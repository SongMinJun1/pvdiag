#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
UNCHANGED_V2 = {
    "electrical_fault_like",
    "open_or_device_issue_like",
    "group_or_inverter_side_like",
    "shape_only_monitor",
    "weak_critical_candidate",
}
MAINTENANCE_PHENOTYPES = {
    "electrical_fault_like",
    "open_or_device_issue_like",
    "group_or_inverter_side_like",
}
OUTPUT_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "anchor_date",
    "critical_phenotype_v2",
    "critical_phenotype_v3",
    "cluster_guard_flag",
    "same_site_borderline_count_anchor_date",
    "same_site_borderline_rate_anchor_date",
    "same_group_borderline_count_anchor_date",
    "same_group_borderline_rate_anchor_date",
    "days_earlier_than_trigger",
    "onset_confidence",
    "onset_method",
    "parsed_strict_method",
    "singleton_hold_flag",
    "singleton_hold_reason",
    "actionability_v3",
    "vendor_reply_class",
    "vendor_fault_family",
]
SUMMARY_COLS = [
    "site",
    "total_rows",
    "count_maintenance_candidate",
    "count_common_cause_review",
    "count_singleton_review",
    "count_singleton_monitor_hold",
    "count_monitor_only",
    "count_common_cause_borderline",
    "count_singleton_borderline_review",
]
VENDOR_MATRIX_COLS = [
    "site",
    "critical_phenotype_v3",
    "actionability_v3",
    "vendor_reply_class",
    "vendor_fault_family",
    "row_count",
]
V2_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "anchor_date",
    "critical_phenotype_v2",
    "cluster_guard_flag",
]
VENDOR_COLS = ["site", "panel_id", "vendor_reply_class", "vendor_fault_family"]
ONSET_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "days_earlier_than_trigger",
    "onset_confidence",
    "onset_method",
    "reason_summary",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split borderline electrical review into common-cause vs singleton review and emit actionability buckets.")
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
        help="Sites to process. Defaults to the known stable sites.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text


def to_int_flag(value: object) -> int:
    text = normalize_text(value).lower()
    return 1 if text in {"1", "true", "t", "yes", "y"} else 0


def safe_rate(numer: int, denom: int) -> float:
    if denom <= 0:
        return float("nan")
    return round(float(numer / denom), 6)


def fallback_group_key(panel_id: str) -> str:
    parts = normalize_text(panel_id).split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return normalize_text(panel_id)


def parse_strict_method(reason_summary: object) -> str:
    text = normalize_text(reason_summary)
    if not text:
        return ""
    for part in text.split("|"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        if normalize_text(key) == "strict_method":
            return normalize_text(value)
    return ""


def ensure_vendor_df(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=VENDOR_COLS)
    df = read_csv(path)
    missing = [col for col in VENDOR_COLS if col not in df.columns]
    if missing:
        raise SystemExit(f"vendor adjudication input missing columns: {missing}")
    for col in VENDOR_COLS:
        df[col] = df[col].map(normalize_text)
    return df.loc[:, VENDOR_COLS].drop_duplicates(subset=["site", "panel_id"]).copy()


def ensure_onset_df(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=ONSET_COLS + ["parsed_strict_method"])
    df = read_csv(path)
    missing = [col for col in ONSET_COLS if col not in df.columns]
    if missing:
        raise SystemExit(f"panel onset shadow input missing columns: {missing}")
    df = df.loc[:, ONSET_COLS].copy()
    for col in ["site", "panel_id", "strict_trigger_date", "onset_confidence", "onset_method", "reason_summary"]:
        df[col] = df[col].map(normalize_text)
    df["days_earlier_than_trigger"] = pd.to_numeric(df["days_earlier_than_trigger"], errors="coerce")
    df["parsed_strict_method"] = df["reason_summary"].map(parse_strict_method)
    return df.drop_duplicates(subset=["site", "panel_id", "strict_trigger_date"])


def load_core_groups(root: Path, site: str) -> pd.DataFrame:
    path = root / "data" / site / "out" / "panel_day_core.csv"
    df = read_csv(path)
    required = ["date", "panel_id"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{path} missing columns: {missing}")
    df = df.copy()
    df["site"] = site
    df["panel_id"] = df["panel_id"].map(normalize_text)
    df["anchor_date"] = pd.to_datetime(df["date"], errors="coerce").dt.date.astype("string")
    if "group_key_base" in df.columns:
        df["group_key_base"] = df["group_key_base"].map(normalize_text)
    else:
        df["group_key_base"] = ""
    missing_group = df["group_key_base"].eq("")
    df.loc[missing_group, "group_key_base"] = df.loc[missing_group, "panel_id"].map(fallback_group_key)
    return df.loc[:, ["site", "panel_id", "anchor_date", "group_key_base"]].drop_duplicates()


def assign_actionability(phenotype_v3: str) -> str:
    if phenotype_v3 in MAINTENANCE_PHENOTYPES:
        return "maintenance_candidate"
    if phenotype_v3 == "common_cause_borderline":
        return "common_cause_review"
    if phenotype_v3 == "singleton_borderline_review":
        return "singleton_review"
    return "monitor_only"


def build_rows(root: Path, sites: list[str]) -> pd.DataFrame:
    v2_df = read_csv(root / "_share" / "critical_phenotype_shadow_v2_latest.csv")
    missing = [col for col in V2_REQUIRED_COLS if col not in v2_df.columns]
    if missing:
        raise SystemExit(f"critical_phenotype_shadow_v2_latest.csv missing columns: {missing}")
    vendor_df = ensure_vendor_df(root / "_share" / "vendor_reply_adjudication_latest.csv")
    onset_df = ensure_onset_df(root / "_share" / "panel_onset_shadow_latest.csv")

    v2_df = v2_df.copy()
    for col in ["site", "panel_id", "strict_trigger_date", "anchor_date", "critical_phenotype_v2"]:
        v2_df[col] = v2_df[col].map(normalize_text)
    v2_df["cluster_guard_flag"] = v2_df["cluster_guard_flag"].map(to_int_flag)
    v2_df = v2_df.loc[v2_df["site"].isin(sites)].copy()
    if not onset_df.empty:
        v2_df = v2_df.merge(
            onset_df,
            on=["site", "panel_id", "strict_trigger_date"],
            how="left",
        )
    else:
        v2_df["days_earlier_than_trigger"] = float("nan")
        v2_df["onset_confidence"] = ""
        v2_df["onset_method"] = ""
        v2_df["reason_summary"] = ""
        v2_df["parsed_strict_method"] = ""

    vendor_lookup = vendor_df.set_index(["site", "panel_id"], drop=False) if not vendor_df.empty else pd.DataFrame(columns=VENDOR_COLS).set_index(["site", "panel_id"], drop=False)

    rows: list[dict[str, object]] = []
    for site in sites:
        site_df = v2_df.loc[v2_df["site"].eq(site)].copy()
        if site_df.empty:
            continue
        core_groups = load_core_groups(root, site)
        site_totals = core_groups.groupby("anchor_date", dropna=False)["panel_id"].nunique().to_dict()
        group_totals = (
            core_groups.groupby(["anchor_date", "group_key_base"], dropna=False)["panel_id"]
            .nunique()
            .to_dict()
        )

        site_df = site_df.merge(core_groups, on=["site", "panel_id", "anchor_date"], how="left")
        site_df["group_key_base"] = site_df["group_key_base"].fillna("").map(normalize_text)
        missing_group = site_df["group_key_base"].eq("")
        site_df.loc[missing_group, "group_key_base"] = site_df.loc[missing_group, "panel_id"].map(fallback_group_key)

        borderline = site_df.loc[site_df["critical_phenotype_v2"].eq("borderline_electrical_review")].copy()
        site_counts = borderline.groupby("anchor_date", dropna=False).size().to_dict()
        group_counts = borderline.groupby(["anchor_date", "group_key_base"], dropna=False).size().to_dict()

        for row in site_df.itertuples(index=False):
            same_site_count = ""
            same_site_rate = float("nan")
            same_group_count = ""
            same_group_rate = float("nan")
            phenotype_v3 = row.critical_phenotype_v2
            singleton_hold_flag = 0
            singleton_hold_reason = ""

            if row.critical_phenotype_v2 == "borderline_electrical_review":
                same_site_count_int = int(site_counts.get(row.anchor_date, 0))
                same_group_count_int = int(group_counts.get((row.anchor_date, row.group_key_base), 0))
                same_site_total = int(site_totals.get(row.anchor_date, 0))
                same_group_total = int(group_totals.get((row.anchor_date, row.group_key_base), 0))

                same_site_count = same_site_count_int
                same_group_count = same_group_count_int
                same_site_rate = safe_rate(same_site_count_int, same_site_total)
                same_group_rate = safe_rate(same_group_count_int, same_group_total)

                if row.cluster_guard_flag == 1 and (same_site_count_int >= 3 or same_group_count_int >= 2):
                    phenotype_v3 = "common_cause_borderline"
                else:
                    phenotype_v3 = "singleton_borderline_review"

                days_earlier = getattr(row, "days_earlier_than_trigger", float("nan"))
                parsed_strict_method = normalize_text(getattr(row, "parsed_strict_method", ""))
                onset_confidence = normalize_text(getattr(row, "onset_confidence", ""))
                onset_method = normalize_text(getattr(row, "onset_method", ""))
                hold_rule = (
                    phenotype_v3 == "singleton_borderline_review"
                    and int(row.cluster_guard_flag) == 0
                    and parsed_strict_method == "critical_fault_flag"
                    and pd.notna(days_earlier)
                    and float(days_earlier) >= 30.0
                    and onset_confidence == "high"
                    and onset_method == "persistent_5of7"
                )
                if hold_rule:
                    phenotype_v3 = "singleton_monitor_hold"
                    singleton_hold_flag = 1
                    singleton_hold_reason = "isolated_long_horizon_singleton_borderline"
            elif row.critical_phenotype_v2 not in UNCHANGED_V2:
                raise SystemExit(f"unexpected v2 phenotype: {row.critical_phenotype_v2}")

            actionability_v3 = assign_actionability(phenotype_v3)
            vendor_row = None
            if (row.site, row.panel_id) in vendor_lookup.index:
                vendor_row = vendor_lookup.loc[(row.site, row.panel_id)]
                if isinstance(vendor_row, pd.DataFrame):
                    vendor_row = vendor_row.iloc[0]

            vendor_reply_class = normalize_text(getattr(row, "vendor_reply_class", ""))
            vendor_fault_family = normalize_text(getattr(row, "vendor_fault_family", ""))
            if vendor_row is not None:
                vendor_reply_class = normalize_text(vendor_row.get("vendor_reply_class", vendor_reply_class))
                vendor_fault_family = normalize_text(vendor_row.get("vendor_fault_family", vendor_fault_family))

            rows.append(
                {
                    "site": row.site,
                    "panel_id": row.panel_id,
                    "strict_trigger_date": row.strict_trigger_date,
                    "anchor_date": row.anchor_date,
                    "critical_phenotype_v2": row.critical_phenotype_v2,
                    "critical_phenotype_v3": phenotype_v3,
                    "cluster_guard_flag": int(row.cluster_guard_flag),
                    "same_site_borderline_count_anchor_date": same_site_count,
                    "same_site_borderline_rate_anchor_date": same_site_rate,
                    "same_group_borderline_count_anchor_date": same_group_count,
                    "same_group_borderline_rate_anchor_date": same_group_rate,
                    "days_earlier_than_trigger": getattr(row, "days_earlier_than_trigger", float("nan")),
                    "onset_confidence": normalize_text(getattr(row, "onset_confidence", "")),
                    "onset_method": normalize_text(getattr(row, "onset_method", "")),
                    "parsed_strict_method": normalize_text(getattr(row, "parsed_strict_method", "")),
                    "singleton_hold_flag": singleton_hold_flag,
                    "singleton_hold_reason": singleton_hold_reason,
                    "actionability_v3": actionability_v3,
                    "vendor_reply_class": vendor_reply_class,
                    "vendor_fault_family": vendor_fault_family,
                }
            )

    return pd.DataFrame(rows, columns=OUTPUT_COLS)


def build_summary(rows_df: pd.DataFrame, sites: list[str]) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for site in sites:
        subset = rows_df.loc[rows_df["site"].eq(site)]
        records.append(
            {
                "site": site,
                "total_rows": int(len(subset)),
                "count_maintenance_candidate": int(subset["actionability_v3"].eq("maintenance_candidate").sum()),
                "count_common_cause_review": int(subset["actionability_v3"].eq("common_cause_review").sum()),
                "count_singleton_review": int(subset["actionability_v3"].eq("singleton_review").sum()),
                "count_singleton_monitor_hold": int(subset["critical_phenotype_v3"].eq("singleton_monitor_hold").sum()),
                "count_monitor_only": int(subset["actionability_v3"].eq("monitor_only").sum()),
                "count_common_cause_borderline": int(subset["critical_phenotype_v3"].eq("common_cause_borderline").sum()),
                "count_singleton_borderline_review": int(subset["critical_phenotype_v3"].eq("singleton_borderline_review").sum()),
            }
        )
    return pd.DataFrame(records, columns=SUMMARY_COLS)


def build_vendor_matrix(rows_df: pd.DataFrame) -> pd.DataFrame:
    if rows_df.empty:
        return pd.DataFrame(columns=VENDOR_MATRIX_COLS)
    matrix = (
        rows_df.groupby(
            ["site", "critical_phenotype_v3", "actionability_v3", "vendor_reply_class", "vendor_fault_family"],
            dropna=False,
        )
        .size()
        .reset_index(name="row_count")
    )
    return matrix.loc[:, VENDOR_MATRIX_COLS]


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    sites = list(args.sites)
    share_dir = root / "_share"

    rows_df = build_rows(root, sites)
    summary_df = build_summary(rows_df, sites)
    vendor_matrix_df = build_vendor_matrix(rows_df)

    rows_df.to_csv(share_dir / "critical_actionability_shadow_v3_latest.csv", index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / "critical_actionability_shadow_v3_summary.csv", index=False, encoding="utf-8-sig")
    vendor_matrix_df.to_csv(share_dir / "critical_actionability_shadow_v3_vendor_matrix.csv", index=False, encoding="utf-8-sig")

    print(f"critical_actionability_v3_rows={len(rows_df)}")


if __name__ == "__main__":
    main()
