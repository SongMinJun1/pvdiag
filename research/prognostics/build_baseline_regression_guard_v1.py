#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import pandas as pd

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
OVERALL_FIELDS = [
    "strict_maintenance_f1",
    "strict_operational_f1",
    "lenient_maintenance_f1",
    "lenient_operational_f1",
    "official_scored_count",
    "manual_scored_count",
    "vendor_scored_count",
    "deferred_hold_count",
    "active_review_queue_count",
    "precursor_global_recommendation",
    "freeze_recommendation",
]
SITE_FIELDS = [
    "official_scored_count",
    "manual_scored_count",
    "vendor_scored_count",
    "deferred_hold_count",
    "precursor_site_recommendation",
    "site_status",
]
REQUIRED_DECISION_KEYS = [
    "official_baseline_status",
    "active_truth_review_queue",
    "deferred_high_actionability_rows",
    "global_precursor_addon",
    "conalog_precursor_note",
    "next_workstream_recommendation",
]
DIFF_COLS = ["diff_scope", "diff_key", "site", "frozen_value", "current_value", "severity"]
SITE_OUTPUT_COLS = ["site", "frozen_site_status", "current_site_status", "site_diff_count", "site_guard_status"]
SUMMARY_COLS = [
    "guard_status",
    "overall_diff_count",
    "site_diff_count",
    "decision_diff_count",
    "total_diff_count",
    *[item for field in OVERALL_FIELDS for item in (f"frozen_{field}", f"current_{field}")],
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Guard the frozen baseline against unintended drift while future workstreams run."
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
        help="Sites to include. Defaults to the stable known sites.",
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


def drop_embedded_header_rows(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    if any(col not in df.columns for col in cols):
        return df
    header_mask = pd.Series(True, index=df.index)
    for col in cols:
        header_mask &= df[col].map(normalize_text).eq(col)
    if not bool(header_mask.any()):
        return df
    return df.loc[~header_mask].copy()


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def load_freeze_module() -> object:
    module_path = Path(__file__).resolve().with_name("build_baseline_freeze_pack_v1.py")
    spec = importlib.util.spec_from_file_location("baseline_freeze_pack_v1_module", module_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"unable to load freeze module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_overall_value(field: str, value: object) -> object:
    if field.endswith("_f1"):
        numeric = pd.to_numeric(value, errors="coerce")
        return 0.0 if pd.isna(numeric) else round(float(numeric), 6)
    if field.endswith("_count"):
        numeric = pd.to_numeric(value, errors="coerce")
        return 0 if pd.isna(numeric) else int(numeric)
    return normalize_text(value)


def canonical_site_value(field: str, value: object) -> object:
    if field.endswith("_count"):
        numeric = pd.to_numeric(value, errors="coerce")
        return 0 if pd.isna(numeric) else int(numeric)
    return normalize_text(value)


def canonical_decision_value(field: str, value: object) -> object:
    return normalize_text(value)


def format_value(field: str, value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if field.endswith("_f1"):
            return f"{value:.6f}"
        if value.is_integer():
            return str(int(value))
        return f"{value:.6f}"
    return str(value)


def is_warn_recommendation(field: str, decision_key: str | None = None) -> bool:
    if field in {"precursor_global_recommendation", "precursor_site_recommendation"}:
        return True
    if decision_key in {"global_precursor_addon", "conalog_precursor_note", "next_workstream_recommendation"}:
        return True
    if decision_key is not None and field == "decision_reason":
        return True
    return False


def stable_site_order(sites: list[str], site_values: list[str]) -> list[str]:
    site_rank = {site: idx for idx, site in enumerate(sites)}
    return sorted(set(site_values), key=lambda value: (site_rank.get(value, len(site_rank)), value))


def get_summary_row(df: pd.DataFrame, name: str) -> pd.Series:
    if df.empty:
        raise SystemExit(f"{name} is empty")
    return df.iloc[0]


def build_current_live_state(root: Path, sites: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    freeze_module = load_freeze_module()
    return freeze_module.build_outputs(root, list(sites))


def compare_overall(
    frozen_summary_row: pd.Series,
    current_summary_row: pd.Series,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for field in OVERALL_FIELDS:
        frozen_value = canonical_overall_value(field, frozen_summary_row.get(field, ""))
        current_value = canonical_overall_value(field, current_summary_row.get(field, ""))
        if frozen_value != current_value:
            rows.append(
                {
                    "diff_scope": "overall",
                    "diff_key": field,
                    "site": "",
                    "frozen_value": format_value(field, frozen_value),
                    "current_value": format_value(field, current_value),
                    "severity": "warn" if is_warn_recommendation(field) else "error",
                }
            )
    return rows


def compare_sites(
    frozen_sites_df: pd.DataFrame,
    current_sites_df: pd.DataFrame,
    sites: list[str],
) -> tuple[list[dict[str, str]], pd.DataFrame]:
    frozen_by_site = frozen_sites_df.set_index("site", drop=False)
    current_by_site = current_sites_df.set_index("site", drop=False)
    site_list = stable_site_order(
        sites,
        frozen_sites_df["site"].map(normalize_text).tolist() + current_sites_df["site"].map(normalize_text).tolist(),
    )

    diffs: list[dict[str, str]] = []
    site_rows: list[dict[str, object]] = []
    for site in site_list:
        frozen_row = frozen_by_site.loc[site] if site in frozen_by_site.index else pd.Series(dtype=object)
        current_row = current_by_site.loc[site] if site in current_by_site.index else pd.Series(dtype=object)

        site_diff_count = 0
        for field in SITE_FIELDS:
            frozen_value = canonical_site_value(field, frozen_row.get(field, ""))
            current_value = canonical_site_value(field, current_row.get(field, ""))
            if frozen_value != current_value:
                diffs.append(
                    {
                        "diff_scope": "site",
                        "diff_key": field,
                        "site": site,
                        "frozen_value": format_value(field, frozen_value),
                        "current_value": format_value(field, current_value),
                        "severity": "warn" if is_warn_recommendation(field) else "error",
                    }
                )
                site_diff_count += 1

        site_rows.append(
            {
                "site": site,
                "frozen_site_status": normalize_text(frozen_row.get("site_status", "")),
                "current_site_status": normalize_text(current_row.get("site_status", "")),
                "site_diff_count": site_diff_count,
                "site_guard_status": "preserved" if site_diff_count == 0 else "drift_detected",
            }
        )

    return diffs, pd.DataFrame(site_rows, columns=SITE_OUTPUT_COLS)


def compare_decisions(
    frozen_decisions_df: pd.DataFrame,
    current_decisions_df: pd.DataFrame,
) -> list[dict[str, str]]:
    frozen_by_key = frozen_decisions_df.set_index("decision_key", drop=False)
    current_by_key = current_decisions_df.set_index("decision_key", drop=False)

    diffs: list[dict[str, str]] = []
    for decision_key in REQUIRED_DECISION_KEYS:
        frozen_row = frozen_by_key.loc[decision_key] if decision_key in frozen_by_key.index else pd.Series(dtype=object)
        current_row = current_by_key.loc[decision_key] if decision_key in current_by_key.index else pd.Series(dtype=object)
        for field in ["decision_status", "decision_reason", "supporting_value"]:
            frozen_value = canonical_decision_value(field, frozen_row.get(field, ""))
            current_value = canonical_decision_value(field, current_row.get(field, ""))
            if frozen_value != current_value:
                diffs.append(
                    {
                        "diff_scope": "decision",
                        "diff_key": f"{decision_key}.{field}",
                        "site": "",
                        "frozen_value": format_value(field, frozen_value),
                        "current_value": format_value(field, current_value),
                        "severity": "warn" if is_warn_recommendation(field, decision_key=decision_key) else "error",
                    }
                )
    return diffs


def build_summary_output(
    frozen_summary_row: pd.Series,
    current_summary_row: pd.Series,
    diff_df: pd.DataFrame,
) -> pd.DataFrame:
    overall_diff_count = int(diff_df["diff_scope"].eq("overall").sum()) if not diff_df.empty else 0
    site_diff_count = int(diff_df["diff_scope"].eq("site").sum()) if not diff_df.empty else 0
    decision_diff_count = int(diff_df["diff_scope"].eq("decision").sum()) if not diff_df.empty else 0
    total_diff_count = int(len(diff_df))
    row: dict[str, object] = {
        "guard_status": "frozen_baseline_preserved" if total_diff_count == 0 else "drift_detected",
        "overall_diff_count": overall_diff_count,
        "site_diff_count": site_diff_count,
        "decision_diff_count": decision_diff_count,
        "total_diff_count": total_diff_count,
    }
    for field in OVERALL_FIELDS:
        frozen_value = canonical_overall_value(field, frozen_summary_row.get(field, ""))
        current_value = canonical_overall_value(field, current_summary_row.get(field, ""))
        row[f"frozen_{field}"] = format_value(field, frozen_value)
        row[f"current_{field}"] = format_value(field, current_value)
    return pd.DataFrame([row], columns=SUMMARY_COLS)


def build_outputs(root: Path, sites: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    frozen_summary_df = drop_embedded_header_rows(read_csv(root / "_share" / "baseline_freeze_summary_v1.csv"), ["strict_maintenance_f1"])
    frozen_sites_df = drop_embedded_header_rows(read_csv(root / "_share" / "baseline_freeze_sites_v1.csv"), ["site"])
    frozen_decisions_df = drop_embedded_header_rows(read_csv(root / "_share" / "baseline_freeze_decisions_v1.csv"), ["decision_key"])

    ensure_columns(frozen_summary_df, OVERALL_FIELDS, "baseline_freeze_summary_v1.csv")
    ensure_columns(frozen_sites_df, ["site", *SITE_FIELDS], "baseline_freeze_sites_v1.csv")
    ensure_columns(frozen_decisions_df, ["decision_key", "decision_status", "decision_reason", "supporting_value"], "baseline_freeze_decisions_v1.csv")

    current_summary_df, current_sites_df, current_decisions_df = build_current_live_state(root, sites)
    ensure_columns(current_summary_df, OVERALL_FIELDS, "current live baseline summary")
    ensure_columns(current_sites_df, ["site", *SITE_FIELDS], "current live baseline sites")
    ensure_columns(current_decisions_df, ["decision_key", "decision_status", "decision_reason", "supporting_value"], "current live baseline decisions")

    frozen_summary_row = get_summary_row(frozen_summary_df, "baseline_freeze_summary_v1.csv")
    current_summary_row = get_summary_row(current_summary_df, "current live baseline summary")

    overall_diffs = compare_overall(frozen_summary_row, current_summary_row)
    site_diffs, site_output = compare_sites(frozen_sites_df, current_sites_df, sites)
    decision_diffs = compare_decisions(frozen_decisions_df, current_decisions_df)

    diff_df = pd.DataFrame(overall_diffs + site_diffs + decision_diffs, columns=DIFF_COLS)
    summary_output = build_summary_output(frozen_summary_row, current_summary_row, diff_df)
    return summary_output, site_output, diff_df


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    summary_output, site_output, diff_output = build_outputs(root, list(args.sites))

    out_dir = root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_output.to_csv(out_dir / "baseline_regression_guard_summary_v1.csv", index=False, encoding="utf-8-sig")
    site_output.to_csv(out_dir / "baseline_regression_guard_sites_v1.csv", index=False, encoding="utf-8-sig")
    diff_output.to_csv(out_dir / "baseline_regression_guard_diffs_v1.csv", index=False, encoding="utf-8-sig")
    print(
        f"baseline_regression_guard_summary_v1=1 baseline_regression_guard_sites_v1={len(site_output)} "
        f"baseline_regression_guard_diffs_v1={len(diff_output)}"
    )


if __name__ == "__main__":
    main()
