#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

TIER_ORDER = [
    "schema_default",
    "relaxed_group_share",
    "precursor_like_medium",
    "precursor_like_broad",
]
TIER_SPECS = {
    "schema_default": {
        "min_group_panels": 2,
        "min_group_share": 0.50,
        "require_group_share": True,
        "min_groups": 2,
        "min_site_panels": 5,
        "min_site_share": 0.10,
    },
    "relaxed_group_share": {
        "min_group_panels": 2,
        "min_group_share": 0.25,
        "require_group_share": True,
        "min_groups": 2,
        "min_site_panels": 5,
        "min_site_share": 0.10,
    },
    "precursor_like_medium": {
        "min_group_panels": 2,
        "min_group_share": 0.0,
        "require_group_share": False,
        "min_groups": 2,
        "min_site_panels": 5,
        "min_site_share": 0.0,
    },
    "precursor_like_broad": {
        "min_group_panels": 2,
        "min_group_share": 0.0,
        "require_group_share": False,
        "min_groups": 3,
        "min_site_panels": 10,
        "min_site_share": 0.0,
    },
}
REQUIRED_COLS = [
    "site",
    "panel_id",
    "date",
    "coverage_ok_flag",
    "mid_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "group_proxy_value",
]
SUMMARY_COLS = [
    "record_type",
    "tier_id",
    "site",
    "candidate_day_count",
    "precursor_overlap_count",
    "precursor_overlap_precision",
    "conalog_candidate_day_count",
    "ktc_ess_candidate_day_count",
    "fail_no_qualifying_groups_count",
    "fail_insufficient_group_count_count",
    "fail_insufficient_site_panels_count",
    "fail_insufficient_site_share_count",
    "fail_insufficient_group_share_count",
]
COMPARISON_COLS = [
    "tier_id",
    "site",
    "date",
    "pass_flag",
    "fail_reason_code",
    "precursor_candidate_flag",
    "precursor_tier_ids_seen",
    "total_panel_count",
    "total_zero_like_panel_count",
    "total_group_like_zero_like_panel_count",
    "qualifying_group_count",
    "max_group_cluster_size",
    "total_panels_in_qualifying_groups",
    "site_affected_share",
    "max_group_like_share",
]
DAY_COLS = [
    "site",
    "date",
    "precursor_candidate_flag",
    "precursor_tier_ids_seen",
    "total_panel_count",
    "total_zero_like_panel_count",
    "total_group_like_zero_like_panel_count",
    "raw_max_group_like_share",
    "schema_default_pass_flag",
    "schema_default_fail_reason_code",
    "relaxed_group_share_pass_flag",
    "relaxed_group_share_fail_reason_code",
    "precursor_like_medium_pass_flag",
    "precursor_like_medium_fail_reason_code",
    "precursor_like_broad_pass_flag",
    "precursor_like_broad_fail_reason_code",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit why common_cause_incident_registry_v1 yields zero real incidents before changing thresholds."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to project root.",
    )
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text


def normalize_date(value: object) -> str:
    text = normalize_text(value)
    return text[:10] if len(text) >= 10 else text


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def to_int_flag(value: object) -> int:
    text = normalize_text(value).lower()
    if text in {"1", "true", "t", "yes", "y"}:
        return 1
    if text in {"0", "false", "f", "no", "n", ""}:
        return 0
    try:
        return 1 if float(text) > 0 else 0
    except ValueError:
        return 0


def safe_div(numer: int | float, denom: int | float) -> float:
    if denom <= 0:
        return 0.0
    return round(float(numer / denom), 6)


def join_sorted(values: list[object]) -> str:
    normalized = sorted({normalize_text(value) for value in values if normalize_text(value) != ""})
    return "|".join(normalized)


def load_matrix(root: Path) -> pd.DataFrame:
    path = root / "_share" / "panel_day_evidence_matrix_v1.csv"
    df = read_csv(path)
    ensure_columns(df, REQUIRED_COLS, "panel_day_evidence_matrix_v1.csv")

    df = df.copy()
    df["site"] = df["site"].map(normalize_text)
    df["panel_id"] = df["panel_id"].map(normalize_text)
    df["date"] = df["date"].map(normalize_date)
    df["group_proxy_value"] = df["group_proxy_value"].map(normalize_text)
    df["coverage_ok_flag"] = df["coverage_ok_flag"].map(to_int_flag).astype(int)
    for col in ["mid_ratio", "mid_v_ratio", "mid_i_ratio"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["zero_like_flag"] = (
        df["coverage_ok_flag"].eq(1)
        & df["mid_ratio"].le(0.10)
        & df["mid_i_ratio"].le(0.10)
    ).fillna(False).astype(int)
    df["group_like_zero_like_flag"] = (
        df["zero_like_flag"].eq(1)
        & df["mid_v_ratio"].ge(1.05)
    ).fillna(False).astype(int)
    return df


def build_base_evidence(matrix_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    group_day = matrix_df.groupby(["site", "date", "group_proxy_value"], as_index=False).agg(
        group_panel_count=("panel_id", "size"),
        zero_like_panel_count=("zero_like_flag", "sum"),
        group_like_zero_like_panel_count=("group_like_zero_like_flag", "sum"),
    )
    group_day["group_like_zero_like_share"] = group_day.apply(
        lambda row: safe_div(row["group_like_zero_like_panel_count"], row["group_panel_count"]),
        axis=1,
    )

    site_day = matrix_df.groupby(["site", "date"], as_index=False).agg(
        total_panel_count=("panel_id", "size"),
        total_zero_like_panel_count=("zero_like_flag", "sum"),
        total_group_like_zero_like_panel_count=("group_like_zero_like_flag", "sum"),
    )
    raw_group_metrics = group_day.groupby(["site", "date"], as_index=False).agg(
        raw_max_group_like_share=("group_like_zero_like_share", "max"),
    )
    site_day = site_day.merge(raw_group_metrics, on=["site", "date"], how="left")
    site_day["raw_max_group_like_share"] = pd.to_numeric(site_day["raw_max_group_like_share"], errors="coerce").fillna(0.0)
    return site_day, group_day


def load_precursor_context(root: Path) -> pd.DataFrame:
    path = root / "_share" / "common_cause_precursor_candidate_days_v1.csv"
    if not path.exists():
        return pd.DataFrame(columns=["site", "date", "precursor_candidate_flag", "precursor_tier_ids_seen"])

    df = read_csv(path)
    ensure_columns(df, ["tier_id", "site", "date"], "common_cause_precursor_candidate_days_v1.csv")
    df = df.copy()
    df["tier_id"] = df["tier_id"].map(normalize_text)
    df["site"] = df["site"].map(normalize_text)
    df["date"] = df["date"].map(normalize_date)
    return df.groupby(["site", "date"], as_index=False).agg(
        precursor_candidate_flag=("tier_id", lambda values: 1 if len(list(values)) > 0 else 0),
        precursor_tier_ids_seen=("tier_id", lambda values: join_sorted(list(values))),
    )


def determine_fail_reason(
    row: pd.Series,
    require_group_share: bool,
) -> str:
    if int(row["pass_flag"]) == 1:
        return "pass"
    if int(row["total_group_like_zero_like_panel_count"]) == 0:
        return "no_signal"
    if int(row["qualifying_group_count"]) == 0:
        if require_group_share and int(row["_size_only_group_count"]) > 0:
            return "insufficient_group_share"
        return "no_qualifying_groups"
    if int(row["qualifying_group_count"]) < int(row["_min_groups"]):
        if int(row["total_panels_in_qualifying_groups"]) >= int(row["_min_site_panels"]) and float(row["site_affected_share"]) < float(row["_min_site_share"]):
            return "insufficient_site_share"
        if int(row["total_panels_in_qualifying_groups"]) < int(row["_min_site_panels"]) and float(row["site_affected_share"]) >= float(row["_min_site_share"]):
            return "insufficient_site_panels"
        return "insufficient_group_count"
    if int(row["total_panels_in_qualifying_groups"]) < int(row["_min_site_panels"]):
        return "insufficient_site_panels"
    if float(row["site_affected_share"]) < float(row["_min_site_share"]):
        return "insufficient_site_share"
    return "no_qualifying_groups"


def evaluate_tier(
    site_day_base: pd.DataFrame,
    group_day: pd.DataFrame,
    precursor_context: pd.DataFrame,
    tier_id: str,
) -> pd.DataFrame:
    spec = TIER_SPECS[tier_id]
    qualifying_mask = group_day["group_like_zero_like_panel_count"].ge(spec["min_group_panels"])
    if spec["require_group_share"]:
        qualifying_mask &= group_day["group_like_zero_like_share"].ge(spec["min_group_share"])

    size_only_day = (
        group_day.loc[group_day["group_like_zero_like_panel_count"].ge(spec["min_group_panels"])]
        .groupby(["site", "date"], as_index=False)
        .agg(_size_only_group_count=("group_proxy_value", "size"))
    )

    qualifying_group_day = group_day.loc[qualifying_mask].copy()
    qualifying_day = qualifying_group_day.groupby(["site", "date"], as_index=False).agg(
        qualifying_group_count=("group_proxy_value", "size"),
        max_group_cluster_size=("group_like_zero_like_panel_count", "max"),
        total_panels_in_qualifying_groups=("group_like_zero_like_panel_count", "sum"),
        max_group_like_share=("group_like_zero_like_share", "max"),
    )

    tier_df = site_day_base.merge(qualifying_day, on=["site", "date"], how="left")
    tier_df = tier_df.merge(size_only_day, on=["site", "date"], how="left")
    tier_df = tier_df.merge(precursor_context, on=["site", "date"], how="left")
    for col in ["qualifying_group_count", "max_group_cluster_size", "total_panels_in_qualifying_groups", "_size_only_group_count"]:
        tier_df[col] = pd.to_numeric(tier_df[col], errors="coerce").fillna(0).astype(int)
    tier_df["max_group_like_share"] = pd.to_numeric(tier_df["max_group_like_share"], errors="coerce").fillna(0.0)
    tier_df["precursor_candidate_flag"] = pd.to_numeric(tier_df["precursor_candidate_flag"], errors="coerce").fillna(0).astype(int)
    tier_df["precursor_tier_ids_seen"] = tier_df["precursor_tier_ids_seen"].map(normalize_text)
    tier_df["site_affected_share"] = tier_df.apply(
        lambda row: safe_div(row["total_panels_in_qualifying_groups"], row["total_panel_count"]),
        axis=1,
    )
    tier_df["_min_groups"] = spec["min_groups"]
    tier_df["_min_site_panels"] = spec["min_site_panels"]
    tier_df["_min_site_share"] = spec["min_site_share"]
    tier_df["pass_flag"] = (
        tier_df["qualifying_group_count"].ge(spec["min_groups"])
        | (
            tier_df["total_panels_in_qualifying_groups"].ge(spec["min_site_panels"])
            & tier_df["site_affected_share"].ge(spec["min_site_share"])
        )
    ).astype(int)
    tier_df["fail_reason_code"] = tier_df.apply(
        lambda row: determine_fail_reason(row, spec["require_group_share"]),
        axis=1,
    )
    tier_df["tier_id"] = tier_id
    return tier_df.loc[:, COMPARISON_COLS].copy()


def build_gate_days_output(comparison_output: pd.DataFrame, site_day_base: pd.DataFrame, precursor_context: pd.DataFrame) -> pd.DataFrame:
    base = site_day_base.merge(precursor_context, on=["site", "date"], how="left")
    base["precursor_candidate_flag"] = pd.to_numeric(base["precursor_candidate_flag"], errors="coerce").fillna(0).astype(int)
    base["precursor_tier_ids_seen"] = base["precursor_tier_ids_seen"].map(normalize_text)

    for tier_id in TIER_ORDER:
        tier_rows = comparison_output.loc[comparison_output["tier_id"].eq(tier_id), ["site", "date", "pass_flag", "fail_reason_code"]].copy()
        tier_rows = tier_rows.rename(
            columns={
                "pass_flag": f"{tier_id}_pass_flag",
                "fail_reason_code": f"{tier_id}_fail_reason_code",
            }
        )
        base = base.merge(tier_rows, on=["site", "date"], how="left")

    return base.loc[:, DAY_COLS].copy()


def build_summary_output(comparison_output: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for tier_id in TIER_ORDER:
        tier_df = comparison_output.loc[comparison_output["tier_id"].eq(tier_id)].copy()
        candidate_day_count = int(tier_df["pass_flag"].sum()) if not tier_df.empty else 0
        precursor_overlap_count = int(
            tier_df.loc[tier_df["pass_flag"].eq(1) & tier_df["precursor_candidate_flag"].eq(1)].shape[0]
        ) if not tier_df.empty else 0
        rows.append(
            {
                "record_type": "summary",
                "tier_id": tier_id,
                "site": "",
                "candidate_day_count": candidate_day_count,
                "precursor_overlap_count": precursor_overlap_count,
                "precursor_overlap_precision": safe_div(precursor_overlap_count, candidate_day_count),
                "conalog_candidate_day_count": int(
                    tier_df.loc[tier_df["site"].eq("conalog") & tier_df["pass_flag"].eq(1)].shape[0]
                ) if not tier_df.empty else 0,
                "ktc_ess_candidate_day_count": int(
                    tier_df.loc[tier_df["site"].eq("ktc_ess") & tier_df["pass_flag"].eq(1)].shape[0]
                ) if not tier_df.empty else 0,
                "fail_no_qualifying_groups_count": int(tier_df["fail_reason_code"].eq("no_qualifying_groups").sum()) if not tier_df.empty else 0,
                "fail_insufficient_group_count_count": int(tier_df["fail_reason_code"].eq("insufficient_group_count").sum()) if not tier_df.empty else 0,
                "fail_insufficient_site_panels_count": int(tier_df["fail_reason_code"].eq("insufficient_site_panels").sum()) if not tier_df.empty else 0,
                "fail_insufficient_site_share_count": int(tier_df["fail_reason_code"].eq("insufficient_site_share").sum()) if not tier_df.empty else 0,
                "fail_insufficient_group_share_count": int(tier_df["fail_reason_code"].eq("insufficient_group_share").sum()) if not tier_df.empty else 0,
            }
        )
        for site in sorted(tier_df["site"].dropna().unique()):
            site_df = tier_df.loc[tier_df["site"].eq(site)].copy()
            rows.append(
                {
                    "record_type": "site",
                    "tier_id": tier_id,
                    "site": site,
                    "candidate_day_count": int(site_df["pass_flag"].sum()),
                    "precursor_overlap_count": int(
                        site_df.loc[site_df["pass_flag"].eq(1) & site_df["precursor_candidate_flag"].eq(1)].shape[0]
                    ),
                    "precursor_overlap_precision": pd.NA,
                    "conalog_candidate_day_count": pd.NA,
                    "ktc_ess_candidate_day_count": pd.NA,
                    "fail_no_qualifying_groups_count": pd.NA,
                    "fail_insufficient_group_count_count": pd.NA,
                    "fail_insufficient_site_panels_count": pd.NA,
                    "fail_insufficient_site_share_count": pd.NA,
                    "fail_insufficient_group_share_count": pd.NA,
                }
            )
    return pd.DataFrame(rows, columns=SUMMARY_COLS)


def build_outputs(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    matrix_df = load_matrix(root)
    site_day_base, group_day = build_base_evidence(matrix_df)
    precursor_context = load_precursor_context(root)
    tier_frames = [evaluate_tier(site_day_base, group_day, precursor_context, tier_id) for tier_id in TIER_ORDER]
    comparison_output = pd.concat(tier_frames, ignore_index=True) if tier_frames else pd.DataFrame(columns=COMPARISON_COLS)
    gate_days_output = build_gate_days_output(comparison_output, site_day_base, precursor_context)
    summary_output = build_summary_output(comparison_output)
    return summary_output, gate_days_output, comparison_output


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    summary_output, gate_days_output, comparison_output = build_outputs(root)

    out_dir = root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_output.to_csv(out_dir / "common_cause_incident_gate_audit_summary_v1.csv", index=False, encoding="utf-8-sig")
    gate_days_output.to_csv(out_dir / "common_cause_incident_gate_days_v1.csv", index=False, encoding="utf-8-sig")
    comparison_output.to_csv(out_dir / "common_cause_incident_gate_comparison_v1.csv", index=False, encoding="utf-8-sig")
    print(
        "common_cause_incident_gate_audit_summary_v1="
        f"{len(summary_output)} common_cause_incident_gate_days_v1={len(gate_days_output)} "
        f"common_cause_incident_gate_comparison_v1={len(comparison_output)}"
    )


if __name__ == "__main__":
    main()
