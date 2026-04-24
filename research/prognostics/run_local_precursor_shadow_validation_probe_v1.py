#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

import build_panel_day_engine_local_precursor_shadow_v1 as shadow


GATE_FILENAME = "ae_simple_local_precursor_gate_daily.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a validation-only probe root that resolves duplicate local-precursor gate rows "
            "without modifying the source data root, then run the canonical local-precursor shadow builder."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Source repository root that contains data/<site>/out inputs.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        required=True,
        help="Directory where the probe root, duplicate audit, and run metadata will be written.",
    )
    parser.add_argument(
        "--sites",
        nargs="*",
        default=shadow.SITES,
        help="Sites to include. Defaults to the stable known sites.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Remove an existing output root before rebuilding.",
    )
    return parser.parse_args()


def normalize_key_frame(df: pd.DataFrame, site: str) -> pd.DataFrame:
    df = df.copy()
    for col in shadow.GATE_COLS:
        if col not in df.columns:
            df[col] = pd.NA
    if "site" not in df.columns:
        df["site"] = site
    df["site"] = df["site"].map(shadow.normalize_text)
    df.loc[df["site"].eq(""), "site"] = site
    df["panel_id"] = df["panel_id"].map(shadow.normalize_text)
    df["date"] = df["date"].map(shadow.normalize_date)
    df["_row_order"] = range(len(df))
    return df.loc[df["site"].eq(site), [*shadow.KEY_COLS, *shadow.GATE_COLS, "_row_order"]].copy()


def link_or_copy(src: Path, dst: Path) -> None:
    if dst.exists() or dst.is_symlink():
        if dst.is_dir() and not dst.is_symlink():
            shutil.rmtree(dst)
        else:
            dst.unlink()
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        dst.symlink_to(src, target_is_directory=src.is_dir())
    except OSError:
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)


def collapse_group_max(group: pd.DataFrame) -> pd.Series:
    row = group.nsmallest(1, "_row_order").iloc[0].copy()
    for col in shadow.GATE_COLS:
        numeric = pd.to_numeric(group[col], errors="coerce")
        if numeric.notna().any():
            row[col] = numeric.max()
        else:
            non_empty = [shadow.normalize_text(value) for value in group[col]]
            non_empty = [value for value in non_empty if value != ""]
            row[col] = non_empty[0] if non_empty else pd.NA
    row["_row_order"] = int(group["_row_order"].min())
    return row


def summarize_group(group: pd.DataFrame, duplicate_kind: str) -> dict[str, object]:
    varying_cols = [
        col
        for col in shadow.GATE_COLS
        if len({shadow.normalized_value(value) for value in group[col]}) > 1
    ]
    signal_numeric = pd.to_numeric(group["signal_count"], errors="coerce")
    ews_numeric = pd.to_numeric(group["ews_runlen"], errors="coerce")
    return {
        "site": group["site"].iloc[0],
        "panel_id": group["panel_id"].iloc[0],
        "date": group["date"].iloc[0],
        "duplicate_kind": duplicate_kind,
        "source_rows": int(len(group)),
        "rows_dropped": int(len(group) - 1),
        "varying_columns": "|".join(varying_cols),
        "signal_count_min": int(signal_numeric.min()) if signal_numeric.notna().any() else pd.NA,
        "signal_count_max": int(signal_numeric.max()) if signal_numeric.notna().any() else pd.NA,
        "ews_runlen_min": int(ews_numeric.min()) if ews_numeric.notna().any() else pd.NA,
        "ews_runlen_max": int(ews_numeric.max()) if ews_numeric.notna().any() else pd.NA,
    }


def sanitize_gate_df(df: pd.DataFrame, site: str) -> tuple[pd.DataFrame, dict[str, object], list[dict[str, object]]]:
    normalized = normalize_key_frame(df, site)
    duplicated = normalized.duplicated(subset=shadow.KEY_COLS, keep=False)
    if not duplicated.any():
        return normalized.drop(columns="_row_order"), {
            "site": site,
            "source_rows": int(len(normalized)),
            "output_rows": int(len(normalized)),
            "duplicate_keys": 0,
            "exact_duplicate_keys": 0,
            "conflicting_duplicate_keys": 0,
            "rows_dropped": 0,
            "used_sanitized_copy": 0,
        }, []

    unique_rows = normalized.loc[~duplicated].copy()
    keep_rows: list[pd.Series] = []
    audit_rows: list[dict[str, object]] = []
    exact_duplicate_keys = 0
    conflicting_duplicate_keys = 0

    for _, group in normalized.loc[duplicated].groupby(shadow.KEY_COLS, sort=False, dropna=False):
        normalized_rows = {
            tuple(shadow.normalized_value(group.iloc[idx][col]) for col in shadow.GATE_COLS)
            for idx in range(len(group))
        }
        duplicate_kind = "exact" if len(normalized_rows) == 1 else "conflicting"
        audit_rows.append(summarize_group(group, duplicate_kind))
        if duplicate_kind == "exact":
            exact_duplicate_keys += 1
            keep_rows.append(group.nsmallest(1, "_row_order").iloc[0])
        else:
            conflicting_duplicate_keys += 1
            keep_rows.append(collapse_group_max(group))

    deduped = pd.DataFrame(keep_rows)
    collapsed = pd.concat([unique_rows, deduped], ignore_index=True)
    collapsed = collapsed.sort_values("_row_order", kind="stable").reset_index(drop=True)
    output = collapsed.drop(columns="_row_order")

    summary = {
        "site": site,
        "source_rows": int(len(normalized)),
        "output_rows": int(len(output)),
        "duplicate_keys": int(exact_duplicate_keys + conflicting_duplicate_keys),
        "exact_duplicate_keys": int(exact_duplicate_keys),
        "conflicting_duplicate_keys": int(conflicting_duplicate_keys),
        "rows_dropped": int(len(normalized) - len(output)),
        "used_sanitized_copy": 1,
    }
    return output, summary, audit_rows


def prepare_probe_site(source_root: Path, probe_root: Path, site: str) -> tuple[dict[str, object], list[dict[str, object]]]:
    source_site_dir = source_root / "data" / site
    source_out_dir = source_site_dir / "out"
    if not source_out_dir.exists():
        raise SystemExit(f"missing site out directory: {source_out_dir}")

    target_site_dir = probe_root / "data" / site
    target_out_dir = target_site_dir / "out"
    target_out_dir.mkdir(parents=True, exist_ok=True)

    raw_dir = source_site_dir / "raw"
    if raw_dir.exists():
        link_or_copy(raw_dir, target_site_dir / "raw")

    for item in sorted(source_out_dir.iterdir()):
        if item.name == GATE_FILENAME:
            continue
        link_or_copy(item, target_out_dir / item.name)

    gate_path = source_out_dir / GATE_FILENAME
    if not gate_path.exists():
        return {
            "site": site,
            "source_rows": 0,
            "output_rows": 0,
            "duplicate_keys": 0,
            "exact_duplicate_keys": 0,
            "conflicting_duplicate_keys": 0,
            "rows_dropped": 0,
            "used_sanitized_copy": 0,
        }, []

    gate_df = pd.read_csv(gate_path, low_memory=False, encoding="utf-8-sig")
    sanitized_df, summary, audit_rows = sanitize_gate_df(gate_df, site)
    target_gate_path = target_out_dir / GATE_FILENAME
    if int(summary["used_sanitized_copy"]) == 1:
        sanitized_df.to_csv(target_gate_path, index=False, encoding="utf-8-sig")
    else:
        link_or_copy(gate_path, target_gate_path)
    return summary, audit_rows


def run_shadow_builder(repo_root: Path, probe_root: Path, sites: list[str]) -> subprocess.CompletedProcess[str]:
    build_script = Path(__file__).with_name("build_panel_day_engine_local_precursor_shadow_v1.py")
    cmd = [sys.executable, str(build_script), "--root", str(probe_root), "--sites", *sites]
    return subprocess.run(cmd, cwd=repo_root, text=True, capture_output=True)


def main() -> None:
    args = parse_args()
    source_root = args.root.resolve()
    output_root = args.output_root.resolve()
    probe_root = output_root / "probe_root"

    if output_root.exists():
        if not args.overwrite:
            raise SystemExit(f"output root already exists: {output_root} (pass --overwrite to replace it)")
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    summary_rows: list[dict[str, object]] = []
    audit_rows: list[dict[str, object]] = []
    for site in args.sites:
        site_summary, site_audit_rows = prepare_probe_site(source_root, probe_root, site)
        summary_rows.append(site_summary)
        audit_rows.extend(site_audit_rows)

    summary_df = pd.DataFrame(summary_rows).sort_values("site").reset_index(drop=True)
    summary_path = output_root / "gate_duplicate_resolution_summary_v1.csv"
    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")

    audit_df = pd.DataFrame(audit_rows)
    audit_path = output_root / "gate_duplicate_resolution_key_audit_v1.csv"
    if audit_df.empty:
        audit_df = pd.DataFrame(
            columns=[
                "site",
                "panel_id",
                "date",
                "duplicate_kind",
                "source_rows",
                "rows_dropped",
                "varying_columns",
                "signal_count_min",
                "signal_count_max",
                "ews_runlen_min",
                "ews_runlen_max",
            ]
        )
    audit_df.sort_values(["site", "panel_id", "date"], kind="stable").to_csv(
        audit_path,
        index=False,
        encoding="utf-8-sig",
    )

    build_res = run_shadow_builder(source_root, probe_root, args.sites)
    (output_root / "shadow_builder_stdout.log").write_text(build_res.stdout, encoding="utf-8")
    (output_root / "shadow_builder_stderr.log").write_text(build_res.stderr, encoding="utf-8")
    if build_res.returncode != 0:
        raise SystemExit(
            "local precursor shadow builder failed on probe root:\n"
            f"{build_res.stdout}\n{build_res.stderr}"
        )

    manifest = {
        "source_root": str(source_root),
        "output_root": str(output_root),
        "probe_root": str(probe_root),
        "sites": list(args.sites),
        "summary_csv": str(summary_path),
        "key_audit_csv": str(audit_path),
        "shadow_csv": str(probe_root / "_share" / "panel_day_engine_local_precursor_shadow_v1.csv"),
        "shadow_summary_csv": str(probe_root / "_share" / "panel_day_engine_local_precursor_shadow_summary_v1.csv"),
        "shadow_builder_returncode": int(build_res.returncode),
    }
    (output_root / "validation_probe_manifest_v1.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
