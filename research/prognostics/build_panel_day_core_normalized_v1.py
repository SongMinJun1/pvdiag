#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
KEY_COLS = ["site", "panel_id", "date"]
SAFE_CLASSES = {"provenance_only_duplicate", "evidence_equivalent_duplicate"}
UNRESOLVED_CLASSES = {"numeric_jitter_duplicate", "material_conflict_duplicate"}
PROVENANCE_HINTS = [
    "source",
    "file",
    "path",
    "ingest",
    "export",
    "created",
    "updated",
    "modified",
]
SUMMARY_COLS = [
    "record_type",
    "site",
    "total_raw_row_count",
    "total_normalized_row_count",
    "total_dropped_duplicate_row_count",
    "total_safe_duplicate_group_count",
    "raw_row_count",
    "normalized_row_count",
    "dropped_duplicate_row_count",
    "safe_duplicate_group_count",
    "unique_key_count",
]
DROP_COLS = [
    "site",
    "panel_id",
    "date",
    "duplicate_group_type",
    "kept_row_index",
    "dropped_row_index",
    "kept_provenance_fingerprint",
    "dropped_provenance_fingerprint",
    "normalization_reason",
]
REQUIRED_CORE_COLS = ["panel_id", "date"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize safe normalized panel_day_core sidecars from duplicate-resolution audit outputs."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to project root.",
    )
    parser.add_argument(
        "--sites",
        nargs="*",
        default=SITES,
        help="Sites to normalize. Defaults to the stable known sites.",
    )
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def is_provenance_col(col: str) -> bool:
    lower = col.lower()
    if lower == "date":
        return False
    return any(token in lower for token in PROVENANCE_HINTS)


def load_duplicate_resolution(root: Path) -> pd.DataFrame:
    summary_path = root / "_share" / "panel_day_core_duplicate_resolution_summary_v2.csv"
    groups_path = root / "_share" / "panel_day_core_duplicate_resolution_groups_v2.csv"
    summary_df = read_csv(summary_path)
    groups_df = read_csv(groups_path)
    ensure_columns(groups_df, ["site", "panel_id", "date", "resolution_class"], "panel_day_core_duplicate_resolution_groups_v2.csv")

    if "record_type" in summary_df.columns:
        summary_rows = summary_df.loc[summary_df["record_type"].map(normalize_text).eq("summary")].copy()
        if summary_rows.empty:
            raise SystemExit("panel_day_core_duplicate_resolution_summary_v2.csv missing summary row")
        summary_row = summary_rows.iloc[0]
    else:
        summary_row = summary_df.iloc[0]

    unresolved_count = int(
        pd.to_numeric(summary_row.get("numeric_jitter_duplicate_count", 0), errors="coerce") or 0
    ) + int(
        pd.to_numeric(summary_row.get("material_conflict_duplicate_count", 0), errors="coerce") or 0
    )
    unresolved_groups = groups_df.loc[groups_df["resolution_class"].map(normalize_text).isin(UNRESOLVED_CLASSES)].copy()
    if unresolved_count > 0 or not unresolved_groups.empty:
        counts = unresolved_groups["resolution_class"].map(normalize_text).value_counts().to_dict()
        raise SystemExit(f"unresolved duplicate classes block normalization: {counts}")

    groups_df["site"] = groups_df["site"].map(normalize_text)
    groups_df["panel_id"] = groups_df["panel_id"].map(normalize_text)
    groups_df["date"] = groups_df["date"].map(normalize_text)
    groups_df["resolution_class"] = groups_df["resolution_class"].map(normalize_text)
    return groups_df


def load_site_core(root: Path, site: str) -> tuple[pd.DataFrame, list[str], Path]:
    path = root / "data" / site / "out" / "panel_day_core.csv"
    df = read_csv(path)
    ensure_columns(df, REQUIRED_CORE_COLS, f"{site}/panel_day_core.csv")
    original_cols = list(df.columns)
    df = df.copy()
    df.insert(0, "site", site)
    df["_raw_row_index"] = range(1, len(df) + 1)
    df["_panel_id_key"] = df["panel_id"].map(normalize_text)
    df["_date_key"] = df["date"].map(normalize_text)
    return df, original_cols, path


def count_nonblank_non_provenance(row: pd.Series, non_provenance_cols: list[str]) -> int:
    return sum(1 for col in non_provenance_cols if normalize_text(row.get(col, "")) != "")


def build_provenance_fingerprint(row: pd.Series, provenance_cols: list[str], raw_path: Path) -> str:
    parts: list[str] = []
    for col in provenance_cols:
        value = normalize_text(row.get(col, ""))
        if value == "":
            continue
        parts.append(f"{col}={value}")
    if parts:
        return "|".join(parts)
    return f"{raw_path.as_posix()}#row{int(row['_raw_row_index']):06d}"


def select_representative(
    group_df: pd.DataFrame,
    non_provenance_cols: list[str],
    provenance_cols: list[str],
    raw_path: Path,
) -> tuple[pd.Series, pd.DataFrame]:
    ranked = group_df.copy()
    ranked["_nonblank_non_provenance_count"] = ranked.apply(
        lambda row: count_nonblank_non_provenance(row, non_provenance_cols),
        axis=1,
    )
    if "group_key_base" in ranked.columns:
        ranked["_group_key_present"] = ranked["group_key_base"].map(lambda value: 1 if normalize_text(value) != "" else 0)
    else:
        ranked["_group_key_present"] = 0
    ranked["_provenance_fingerprint"] = ranked.apply(
        lambda row: build_provenance_fingerprint(row, provenance_cols, raw_path),
        axis=1,
    )
    ranked = ranked.sort_values(
        [
            "_nonblank_non_provenance_count",
            "_group_key_present",
            "_provenance_fingerprint",
            "_raw_row_index",
        ],
        ascending=[False, False, True, True],
    ).reset_index(drop=True)
    kept_row = ranked.iloc[0]
    return kept_row, ranked


def ensure_group_coverage(raw_rows: pd.DataFrame, groups_df: pd.DataFrame) -> dict[tuple[str, str, str], str]:
    duplicate_keys = {
        tuple(row)
        for row in raw_rows.loc[raw_rows.duplicated(subset=["site", "_panel_id_key", "_date_key"], keep=False), ["site", "_panel_id_key", "_date_key"]]
        .drop_duplicates()
        .itertuples(index=False, name=None)
    }
    group_lookup = {
        (row.site, row.panel_id, row.date): row.resolution_class
        for row in groups_df.loc[:, ["site", "panel_id", "date", "resolution_class"]].itertuples(index=False)
    }
    missing = sorted(duplicate_keys - set(group_lookup))
    extra = sorted(set(group_lookup) - duplicate_keys)
    if missing:
        raise SystemExit(f"duplicate_resolution_groups_v2 missing duplicate keys from raw data: {missing[:5]}")
    if extra:
        raise SystemExit(f"duplicate_resolution_groups_v2 has stale keys not present in raw data: {extra[:5]}")
    return group_lookup


def normalize_site(
    site_df: pd.DataFrame,
    original_cols: list[str],
    raw_path: Path,
    group_lookup: dict[tuple[str, str, str], str],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:
    provenance_cols = [col for col in original_cols if is_provenance_col(col)]
    non_provenance_cols = [col for col in original_cols if not is_provenance_col(col)]

    keep_rows: list[pd.Series] = []
    drop_rows: list[dict[str, object]] = []
    safe_duplicate_group_count = 0

    grouped = site_df.groupby(["site", "_panel_id_key", "_date_key"], sort=False, dropna=False)
    for group_key, group_df in grouped:
        site, panel_id_key, date_key = group_key
        if len(group_df) == 1:
            keep_rows.append(group_df.iloc[0])
            continue

        resolution_class = group_lookup.get((site, panel_id_key, date_key), "")
        if resolution_class not in SAFE_CLASSES:
            raise SystemExit(f"duplicate key is not safe to normalize: {(site, panel_id_key, date_key, resolution_class)}")

        safe_duplicate_group_count += 1
        kept_row, ranked = select_representative(group_df, non_provenance_cols, provenance_cols, raw_path)
        keep_rows.append(kept_row)
        kept_fingerprint = str(kept_row["_provenance_fingerprint"])
        kept_row_index = int(kept_row["_raw_row_index"])

        for _, dropped_row in ranked.iloc[1:].iterrows():
            drop_rows.append(
                {
                    "site": site,
                    "panel_id": panel_id_key,
                    "date": date_key,
                    "duplicate_group_type": resolution_class,
                    "kept_row_index": kept_row_index,
                    "dropped_row_index": int(dropped_row["_raw_row_index"]),
                    "kept_provenance_fingerprint": kept_fingerprint,
                    "dropped_provenance_fingerprint": str(dropped_row["_provenance_fingerprint"]),
                    "normalization_reason": f"collapsed_safe_duplicate_{resolution_class}",
                }
            )

    normalized_df = pd.DataFrame(keep_rows).sort_values("_raw_row_index").reset_index(drop=True)
    if normalized_df.duplicated(subset=["site", "_panel_id_key", "_date_key"]).any():
        raise SystemExit(f"normalization failed to collapse duplicate keys for site={normalize_text(site_df.iloc[0]['site'])}")

    normalized_output = normalized_df.loc[:, original_cols].copy()
    drop_output = pd.DataFrame(drop_rows, columns=DROP_COLS)
    stats = {
        "raw_row_count": int(len(site_df)),
        "normalized_row_count": int(len(normalized_output)),
        "dropped_duplicate_row_count": int(len(drop_output)),
        "safe_duplicate_group_count": int(safe_duplicate_group_count),
        "unique_key_count": int(normalized_df.loc[:, ["site", "_panel_id_key", "_date_key"]].drop_duplicates().shape[0]),
    }
    return normalized_output, drop_output, stats


def build_outputs(root: Path, sites: list[str]) -> tuple[dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame]:
    groups_df = load_duplicate_resolution(root)
    site_frames: dict[str, pd.DataFrame] = {}
    original_cols_by_site: dict[str, list[str]] = {}
    raw_paths: dict[str, Path] = {}
    for site in sites:
        site_df, original_cols, raw_path = load_site_core(root, site)
        site_frames[site] = site_df
        original_cols_by_site[site] = original_cols
        raw_paths[site] = raw_path

    all_rows = pd.concat(site_frames.values(), ignore_index=True, sort=False) if site_frames else pd.DataFrame()
    group_lookup = ensure_group_coverage(all_rows, groups_df) if not all_rows.empty else {}

    normalized_outputs: dict[str, pd.DataFrame] = {}
    drop_frames: list[pd.DataFrame] = []
    summary_rows: list[dict[str, object]] = []

    total_raw_row_count = 0
    total_normalized_row_count = 0
    total_dropped_duplicate_row_count = 0
    total_safe_duplicate_group_count = 0

    for site in sites:
        normalized_output, drop_output, stats = normalize_site(
            site_frames[site],
            original_cols_by_site[site],
            raw_paths[site],
            group_lookup,
        )
        normalized_outputs[site] = normalized_output
        drop_frames.append(drop_output)
        total_raw_row_count += stats["raw_row_count"]
        total_normalized_row_count += stats["normalized_row_count"]
        total_dropped_duplicate_row_count += stats["dropped_duplicate_row_count"]
        total_safe_duplicate_group_count += stats["safe_duplicate_group_count"]
        summary_rows.append(
            {
                "record_type": "site",
                "site": site,
                "total_raw_row_count": pd.NA,
                "total_normalized_row_count": pd.NA,
                "total_dropped_duplicate_row_count": pd.NA,
                "total_safe_duplicate_group_count": pd.NA,
                "raw_row_count": stats["raw_row_count"],
                "normalized_row_count": stats["normalized_row_count"],
                "dropped_duplicate_row_count": stats["dropped_duplicate_row_count"],
                "safe_duplicate_group_count": stats["safe_duplicate_group_count"],
                "unique_key_count": stats["unique_key_count"],
            }
        )

    summary_rows.insert(
        0,
        {
            "record_type": "summary",
            "site": "",
            "total_raw_row_count": total_raw_row_count,
            "total_normalized_row_count": total_normalized_row_count,
            "total_dropped_duplicate_row_count": total_dropped_duplicate_row_count,
            "total_safe_duplicate_group_count": total_safe_duplicate_group_count,
            "raw_row_count": pd.NA,
            "normalized_row_count": pd.NA,
            "dropped_duplicate_row_count": pd.NA,
            "safe_duplicate_group_count": pd.NA,
            "unique_key_count": pd.NA,
        },
    )

    summary_output = pd.DataFrame(summary_rows, columns=SUMMARY_COLS)
    drop_output = pd.concat(drop_frames, ignore_index=True, sort=False) if drop_frames else pd.DataFrame(columns=DROP_COLS)
    return normalized_outputs, summary_output, drop_output


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    normalized_outputs, summary_output, drop_output = build_outputs(root, list(args.sites))

    out_dir = root / "_share" / "panel_day_core_normalized_v1"
    out_dir.mkdir(parents=True, exist_ok=True)
    for site, site_df in normalized_outputs.items():
        site_df.to_csv(out_dir / f"{site}.csv", index=False, encoding="utf-8-sig")

    share_dir = root / "_share"
    summary_output.to_csv(share_dir / "panel_day_core_normalized_summary_v1.csv", index=False, encoding="utf-8-sig")
    drop_output.to_csv(share_dir / "panel_day_core_normalized_drop_manifest_v1.csv", index=False, encoding="utf-8-sig")
    print(
        "panel_day_core_normalized_summary_v1="
        f"{len(summary_output)} panel_day_core_normalized_drop_manifest_v1={len(drop_output)}"
    )


if __name__ == "__main__":
    main()
