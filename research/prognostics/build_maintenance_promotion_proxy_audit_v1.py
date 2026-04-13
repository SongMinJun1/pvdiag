#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
KEY_COLS = ["site", "panel_id", "strict_trigger_date"]
PROMOTION_SET_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "promotion_hypothesis",
    "in_strict_backed_shadow",
    "in_full_candidate_shadow",
    "vendor_fault_family",
    "note",
]
AUDIT_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "gap_bucket",
    "promotion_hypothesis",
    "prediction_source",
    "critical_phenotype_v3",
    "actionability_v3",
    "derived_actionability_v3",
    "final_actionability_v3",
    "parsed_strict_method",
    "parsed_shadow_frac",
    "parsed_group_off_frac",
    "parsed_recovery_reset",
    "days_earlier_than_trigger",
    "onset_confidence",
    "onset_method",
    "note",
]
ACTIONABILITY_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "anchor_date",
    "critical_phenotype_v2",
    "critical_phenotype_v3",
    "cluster_guard_flag",
    "same_site_borderline_count_anchor_date",
    "same_group_borderline_count_anchor_date",
]
V2_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "valid_days",
    "evidence_days",
    "evidence_ratio",
    "mid_ratio_win_median",
    "mid_v_ratio_win_median",
    "mid_i_ratio_win_median",
    "v_drop_win_median",
    "coverage_mid_win_median",
    "shape_support_flag",
]
CASES_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "target_proxy_tier",
    "gap_bucket",
    "promotion_hypothesis",
    "prediction_source",
    "anchor_date",
    "critical_phenotype_v2",
    "critical_phenotype_v3",
    "current_critical_phenotype_v3",
    "parsed_strict_method",
    "parsed_shadow_frac",
    "parsed_group_off_frac",
    "parsed_recovery_reset",
    "days_earlier_than_trigger",
    "onset_confidence",
    "onset_method",
    "cluster_guard_flag",
    "same_site_borderline_count_anchor_date",
    "same_group_borderline_count_anchor_date",
    "valid_days",
    "evidence_days",
    "evidence_ratio",
    "mid_ratio_win_median",
    "mid_v_ratio_win_median",
    "mid_i_ratio_win_median",
    "v_drop_win_median",
    "coverage_mid_win_median",
    "mid_ratio",
    "last_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "v_drop",
    "v_ref_ok",
    "coverage_mid",
    "shadow_like",
    "group_off_like",
    "fallback_group_proxy",
    "same_group_zero_like_count",
    "same_site_zero_like_count",
    "strict_day_zero_like_flag",
    "strict_day_open_like_flag",
    "strict_day_group_like_flag",
    "strict_day_electrical_like_flag",
    "onset_recent_flag",
    "onset_long_horizon_flag",
    "clean_confirmed_flag",
    "note",
]
SUMMARY_COLS = [
    "total_candidate_cases",
    "strict_backed_candidate_count",
    "lenient_only_candidate_count",
    "median_days_earlier_strict_backed",
    "median_days_earlier_lenient_only",
    "count_onset_recent_strict_backed",
    "count_onset_recent_lenient_only",
    "count_open_like_strict_backed",
    "count_open_like_lenient_only",
    "count_group_collapse_strict_backed",
    "count_group_collapse_lenient_only",
]
RULES_COLS = [
    "proxy_rule_id",
    "proxy_rule_description",
    "selected_case_count",
    "strict_backed_hit_count",
    "lenient_only_hit_count",
    "precision_for_strict_backed",
    "recall_for_strict_backed",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit truth-independent promotion proxies for maintenance-shadow candidates without changing official outputs."
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
        help="Sites to inspect. Defaults to the stable known sites.",
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


def to_float(value: object) -> float | None:
    text = normalize_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def to_int_flag(value: object) -> int:
    text = normalize_text(value).lower()
    return 1 if text in {"1", "true", "t", "yes", "y"} else 0


def to_bool(value: object) -> bool:
    text = normalize_text(value).lower()
    return text in {"1", "true", "t", "yes", "y"}


def safe_metric(numer: int | float, denom: int | float) -> float:
    if denom <= 0:
        return 0.0
    return round(float(numer / denom), 6)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def fallback_group_key(panel_id: object) -> str:
    parts = normalize_text(panel_id).split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return normalize_text(panel_id)


def load_core_site(root: Path, site: str) -> pd.DataFrame:
    path = root / "data" / site / "out" / "panel_day_core.csv"
    df = read_csv(path)
    df["site"] = site
    for col in ["panel_id", "date"]:
        df[col] = df[col].map(normalize_text)
    df["strict_trigger_date"] = df["date"].map(normalize_date)

    numeric_defaults = [
        "mid_ratio",
        "last_ratio",
        "mid_v_ratio",
        "mid_i_ratio",
        "v_drop",
        "coverage_mid",
    ]
    for col in numeric_defaults:
        if col not in df.columns:
            df[col] = float("nan")
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    bool_defaults = ["v_ref_ok", "shadow_like", "group_off_like"]
    for col in bool_defaults:
        if col not in df.columns:
            df[col] = False
        else:
            df[col] = df[col].map(to_bool)

    if "group_key_base" not in df.columns:
        df["group_key_base"] = ""
    df["group_key_base"] = df["group_key_base"].map(normalize_text)
    missing_group = df["group_key_base"].eq("")
    df.loc[missing_group, "group_key_base"] = df.loc[missing_group, "panel_id"].map(fallback_group_key)

    df["strict_day_zero_like_flag"] = (
        df["mid_ratio"].le(0.10)
        & df["mid_i_ratio"].le(0.10)
        & df["coverage_mid"].ge(0.50)
    ).fillna(False)

    site_zero_counts = df.groupby("strict_trigger_date", dropna=False)["strict_day_zero_like_flag"].sum().to_dict()
    group_zero_counts = (
        df.groupby(["strict_trigger_date", "group_key_base"], dropna=False)["strict_day_zero_like_flag"]
        .sum()
        .to_dict()
    )
    df["same_site_zero_like_count"] = df["strict_trigger_date"].map(lambda key: int(site_zero_counts.get(key, 0)))
    df["same_group_zero_like_count"] = df.apply(
        lambda row: int(group_zero_counts.get((row["strict_trigger_date"], row["group_key_base"]), 0)),
        axis=1,
    )

    cols = [
        "site",
        "panel_id",
        "strict_trigger_date",
        "group_key_base",
        "mid_ratio",
        "last_ratio",
        "mid_v_ratio",
        "mid_i_ratio",
        "v_drop",
        "v_ref_ok",
        "coverage_mid",
        "shadow_like",
        "group_off_like",
        "same_group_zero_like_count",
        "same_site_zero_like_count",
    ]
    return df.loc[:, cols].drop_duplicates(subset=KEY_COLS)


def load_all_core(root: Path, sites: list[str]) -> pd.DataFrame:
    frames = [load_core_site(root, site) for site in sites]
    if not frames:
        return pd.DataFrame(columns=KEY_COLS)
    return pd.concat(frames, ignore_index=True)


def build_target_proxy_tier(row: pd.Series) -> str:
    if int(row["in_strict_backed_shadow"]) == 1:
        return "strict_backed_candidate"
    if int(row["in_full_candidate_shadow"]) == 1:
        return "lenient_only_candidate"
    return ""


def rule_rows(cases_df: pd.DataFrame) -> pd.DataFrame:
    rules = [
        (
            "recent_clean_confirmed",
            "clean_confirmed_flag == 1 and onset_recent_flag == 1",
            cases_df["clean_confirmed_flag"].eq(1) & cases_df["onset_recent_flag"].eq(1),
        ),
        (
            "long_horizon_clean_confirmed",
            "clean_confirmed_flag == 1 and onset_long_horizon_flag == 1",
            cases_df["clean_confirmed_flag"].eq(1) & cases_df["onset_long_horizon_flag"].eq(1),
        ),
        (
            "strict_day_open_like",
            "strict_day_open_like_flag == 1",
            cases_df["strict_day_open_like_flag"].eq(1),
        ),
        (
            "strict_day_group_collapse",
            "same_group_zero_like_count >= 2 or same_site_zero_like_count >= 3",
            cases_df["same_group_zero_like_count"].ge(2) | cases_df["same_site_zero_like_count"].ge(3),
        ),
        (
            "electrical_like_clean",
            "clean_confirmed_flag == 1 and strict_day_electrical_like_flag == 1",
            cases_df["clean_confirmed_flag"].eq(1) & cases_df["strict_day_electrical_like_flag"].eq(1),
        ),
    ]
    total_strict_backed = int(cases_df["target_proxy_tier"].eq("strict_backed_candidate").sum())
    rows: list[dict[str, object]] = []
    for rule_id, description, mask in rules:
        selected = cases_df.loc[mask].copy()
        strict_hits = int(selected["target_proxy_tier"].eq("strict_backed_candidate").sum())
        lenient_hits = int(selected["target_proxy_tier"].eq("lenient_only_candidate").sum())
        rows.append(
            {
                "proxy_rule_id": rule_id,
                "proxy_rule_description": description,
                "selected_case_count": int(len(selected)),
                "strict_backed_hit_count": strict_hits,
                "lenient_only_hit_count": lenient_hits,
                "precision_for_strict_backed": safe_metric(strict_hits, len(selected)),
                "recall_for_strict_backed": safe_metric(strict_hits, total_strict_backed),
            }
        )
    return pd.DataFrame(rows, columns=RULES_COLS)


def build_summary(cases_df: pd.DataFrame) -> pd.DataFrame:
    strict_backed = cases_df.loc[cases_df["target_proxy_tier"].eq("strict_backed_candidate")]
    lenient_only = cases_df.loc[cases_df["target_proxy_tier"].eq("lenient_only_candidate")]
    row = {
        "total_candidate_cases": int(len(cases_df)),
        "strict_backed_candidate_count": int(len(strict_backed)),
        "lenient_only_candidate_count": int(len(lenient_only)),
        "median_days_earlier_strict_backed": float(strict_backed["days_earlier_than_trigger"].median())
        if not strict_backed.empty
        else float("nan"),
        "median_days_earlier_lenient_only": float(lenient_only["days_earlier_than_trigger"].median())
        if not lenient_only.empty
        else float("nan"),
        "count_onset_recent_strict_backed": int(strict_backed["onset_recent_flag"].sum()) if not strict_backed.empty else 0,
        "count_onset_recent_lenient_only": int(lenient_only["onset_recent_flag"].sum()) if not lenient_only.empty else 0,
        "count_open_like_strict_backed": int(strict_backed["strict_day_open_like_flag"].sum()) if not strict_backed.empty else 0,
        "count_open_like_lenient_only": int(lenient_only["strict_day_open_like_flag"].sum()) if not lenient_only.empty else 0,
        "count_group_collapse_strict_backed": int(
            ((strict_backed["same_group_zero_like_count"] >= 2) | (strict_backed["same_site_zero_like_count"] >= 3)).sum()
        )
        if not strict_backed.empty
        else 0,
        "count_group_collapse_lenient_only": int(
            ((lenient_only["same_group_zero_like_count"] >= 2) | (lenient_only["same_site_zero_like_count"] >= 3)).sum()
        )
        if not lenient_only.empty
        else 0,
    }
    return pd.DataFrame([row], columns=SUMMARY_COLS)


def build_cases(root: Path, sites: list[str]) -> pd.DataFrame:
    promotion_df = read_csv(root / "_share" / "maintenance_shadow_promotion_sets_v1.csv")
    audit_df = read_csv(root / "_share" / "maintenance_gap_audit_cases_v1.csv")
    actionability_df = read_csv(root / "_share" / "critical_actionability_shadow_v3_latest.csv")
    v2_df = read_csv(root / "_share" / "critical_phenotype_shadow_v2_latest.csv")

    ensure_columns(promotion_df, PROMOTION_SET_REQUIRED_COLS, "maintenance_shadow_promotion_sets_v1.csv")
    ensure_columns(audit_df, AUDIT_REQUIRED_COLS, "maintenance_gap_audit_cases_v1.csv")
    ensure_columns(actionability_df, ACTIONABILITY_REQUIRED_COLS, "critical_actionability_shadow_v3_latest.csv")
    ensure_columns(v2_df, V2_REQUIRED_COLS, "critical_phenotype_shadow_v2_latest.csv")

    for df in [promotion_df, audit_df, actionability_df, v2_df]:
        for col in ["site", "panel_id"]:
            df[col] = df[col].map(normalize_text)
        df["strict_trigger_date"] = df["strict_trigger_date"].map(normalize_date)

    promotion_df = promotion_df.loc[
        promotion_df["promotion_hypothesis"].map(normalize_text).eq("candidate_for_maintenance_shadow")
    ].copy()
    promotion_df["in_strict_backed_shadow"] = promotion_df["in_strict_backed_shadow"].map(to_int_flag)
    promotion_df["in_full_candidate_shadow"] = promotion_df["in_full_candidate_shadow"].map(to_int_flag)
    promotion_df["target_proxy_tier"] = promotion_df.apply(build_target_proxy_tier, axis=1)
    promotion_df = promotion_df.loc[promotion_df["site"].isin(sites)].copy()

    audit_keep = audit_df.loc[:, AUDIT_REQUIRED_COLS].copy()
    for col in [
        "gap_bucket",
        "promotion_hypothesis",
        "prediction_source",
        "critical_phenotype_v3",
        "actionability_v3",
        "derived_actionability_v3",
        "final_actionability_v3",
        "parsed_strict_method",
        "parsed_recovery_reset",
        "onset_confidence",
        "onset_method",
        "note",
    ]:
        audit_keep[col] = audit_keep[col].map(normalize_text)
    audit_keep["parsed_shadow_frac"] = pd.to_numeric(audit_keep["parsed_shadow_frac"], errors="coerce")
    audit_keep["parsed_group_off_frac"] = pd.to_numeric(audit_keep["parsed_group_off_frac"], errors="coerce")
    audit_keep["days_earlier_than_trigger"] = pd.to_numeric(audit_keep["days_earlier_than_trigger"], errors="coerce")

    action_keep = actionability_df.loc[:, ACTIONABILITY_REQUIRED_COLS].copy()
    extra_cols = [
        "anchor_date",
        "cluster_guard_flag",
        "same_site_borderline_count_anchor_date",
        "same_group_borderline_count_anchor_date",
        "critical_phenotype_v2",
        "critical_phenotype_v3",
    ]
    for col in extra_cols:
        if col not in actionability_df.columns:
            actionability_df[col] = ""
    action_keep = actionability_df.loc[:, KEY_COLS + extra_cols].copy().rename(
        columns={"critical_phenotype_v3": "current_critical_phenotype_v3"}
    )
    action_keep["anchor_date"] = action_keep["anchor_date"].map(normalize_text)
    action_keep["critical_phenotype_v2"] = action_keep["critical_phenotype_v2"].map(normalize_text)
    action_keep["current_critical_phenotype_v3"] = action_keep["current_critical_phenotype_v3"].map(normalize_text)
    action_keep["cluster_guard_flag"] = action_keep["cluster_guard_flag"].map(to_int_flag)
    for col in [
        "same_site_borderline_count_anchor_date",
        "same_group_borderline_count_anchor_date",
    ]:
        action_keep[col] = pd.to_numeric(action_keep[col], errors="coerce")

    v2_keep = v2_df.loc[:, KEY_COLS + [c for c in V2_REQUIRED_COLS if c not in KEY_COLS]].copy()
    for col in [
        "valid_days",
        "evidence_days",
        "evidence_ratio",
        "mid_ratio_win_median",
        "mid_v_ratio_win_median",
        "mid_i_ratio_win_median",
        "v_drop_win_median",
        "coverage_mid_win_median",
        "shape_support_flag",
    ]:
        if col in {"valid_days", "evidence_days", "shape_support_flag"}:
            v2_keep[col] = pd.to_numeric(v2_keep[col], errors="coerce")
        else:
            v2_keep[col] = pd.to_numeric(v2_keep[col], errors="coerce")

    core_df = load_all_core(root, sites)

    cases = promotion_df.merge(audit_keep, on=KEY_COLS, how="left", suffixes=("_promotion", "_audit"))
    cases = cases.merge(action_keep, on=KEY_COLS, how="left")
    cases = cases.merge(v2_keep, on=KEY_COLS, how="left")
    cases = cases.merge(core_df, on=KEY_COLS, how="left")

    for col in ["gap_bucket", "promotion_hypothesis", "note"]:
        promotion_col = f"{col}_promotion"
        audit_col = f"{col}_audit"
        cases[col] = cases.apply(
            lambda row: normalize_text(row.get(promotion_col, "")) or normalize_text(row.get(audit_col, "")),
            axis=1,
        )

    cases["fallback_group_proxy"] = cases.apply(
        lambda row: normalize_text(row.get("group_key_base", "")) or fallback_group_key(row["panel_id"]),
        axis=1,
    )
    cases["same_group_zero_like_count"] = pd.to_numeric(cases["same_group_zero_like_count"], errors="coerce").fillna(0).astype(int)
    cases["same_site_zero_like_count"] = pd.to_numeric(cases["same_site_zero_like_count"], errors="coerce").fillna(0).astype(int)

    cases["strict_day_zero_like_flag"] = (
        cases["mid_ratio"].le(0.10)
        & cases["mid_i_ratio"].le(0.10)
        & cases["coverage_mid"].ge(0.50)
    ).fillna(False).astype(int)
    cases["strict_day_open_like_flag"] = (
        cases["mid_ratio"].le(0.10)
        & cases["mid_v_ratio"].le(0.10)
        & cases["v_drop"].ge(0.90)
    ).fillna(False).astype(int)
    cases["strict_day_group_like_flag"] = (
        cases["mid_ratio"].le(0.10)
        & cases["mid_i_ratio"].le(0.10)
        & cases["mid_v_ratio"].ge(1.05)
    ).fillna(False).astype(int)
    cases["strict_day_electrical_like_flag"] = (
        cases["v_ref_ok"].fillna(False).astype(bool)
        & cases["coverage_mid"].ge(0.85)
        & cases["mid_v_ratio"].le(0.72)
        & cases["v_drop"].ge(0.30)
        & cases["mid_i_ratio"].ge(0.90)
    ).fillna(False).astype(int)
    cases["onset_recent_flag"] = cases["days_earlier_than_trigger"].le(7).fillna(False).astype(int)
    cases["onset_long_horizon_flag"] = cases["days_earlier_than_trigger"].ge(30).fillna(False).astype(int)
    cases["clean_confirmed_flag"] = (
        cases["parsed_strict_method"].map(normalize_text).eq("confirmed_fault_flag")
        & cases["parsed_shadow_frac"].eq(0.0)
        & cases["parsed_group_off_frac"].eq(0.0)
        & cases["parsed_recovery_reset"].map(normalize_text).eq("no")
    ).fillna(False).astype(int)
    cases["v_ref_ok"] = cases["v_ref_ok"].fillna(False).astype(int)
    cases["shadow_like"] = cases["shadow_like"].fillna(False).astype(int)
    cases["group_off_like"] = cases["group_off_like"].fillna(False).astype(int)
    cases["cluster_guard_flag"] = cases["cluster_guard_flag"].fillna(0).astype(int)
    cases["shape_support_flag"] = pd.to_numeric(cases["shape_support_flag"], errors="coerce")
    return cases.loc[:, CASES_COLS + ["vendor_fault_family"]].drop(columns=["vendor_fault_family"], errors="ignore")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    sites = list(args.sites)

    cases_df = build_cases(root, sites)
    summary_df = build_summary(cases_df)
    rules_df = rule_rows(cases_df)

    out_dir = root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    cases_df.to_csv(out_dir / "maintenance_promotion_proxy_cases_v1.csv", index=False, encoding="utf-8-sig")
    summary_df.to_csv(out_dir / "maintenance_promotion_proxy_summary_v1.csv", index=False, encoding="utf-8-sig")
    rules_df.to_csv(out_dir / "maintenance_promotion_proxy_rules_v1.csv", index=False, encoding="utf-8-sig")
    print(f"maintenance_promotion_proxy_rows_v1={len(cases_df)}")


if __name__ == "__main__":
    main()
