#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.prognostics.evaluate_full_algorithm_f1_v3 import (
    REAUDIT_REQUIRED_COLS,
    VENDOR_REQUIRED_COLS,
    dedupe,
    ensure_columns,
    hybrid_truth_label,
    normalize_date,
    normalize_text,
    parse_reason_summary,
    read_csv,
    resolve_truth_source,
    safe_metric,
    source_split_mask,
)

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
KEY_COLS = ["site", "panel_id", "strict_trigger_date"]
TRUTH_MODES = ("strict", "lenient")
SOURCE_SPLITS = ("overall", "manual_truth", "vendor_truth")
SCENARIOS = ("baseline_v3", "same_group_group_like_shadow")
ACTIONABILITY_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "actionability_v3",
]
ONSET_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "days_earlier_than_trigger",
    "onset_confidence",
    "onset_method",
    "reason_summary",
]
SUMMARY_COLS = [
    "scenario",
    "truth_mode",
    "source_split",
    "tp",
    "fp",
    "fn",
    "tn",
    "precision",
    "recall",
    "f1",
    "excluded_rows",
    "scored_rows",
    "promoted_case_count",
]
SELECTED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "current_actionability_v3",
    "shadow_actionability_v3",
    "strict_method",
    "shadow_frac",
    "group_off_frac",
    "recovery_reset",
    "days_earlier_than_trigger",
    "onset_confidence",
    "onset_method",
    "mid_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "v_drop",
    "coverage_mid",
    "strict_day_group_like_flag",
    "same_group_zero_like_count",
    "same_site_zero_like_count",
    "vendor_reply_class",
    "vendor_fault_family",
    "note",
]
ERROR_COLS = [
    "scenario",
    "truth_mode",
    "source_split",
    "site",
    "panel_id",
    "strict_trigger_date",
    "truth_source",
    "truth_label",
    "current_actionability_v3",
    "shadow_actionability_v3",
    "final_prediction_label",
    "error_type",
    "strict_method",
    "shadow_frac",
    "group_off_frac",
    "recovery_reset",
    "same_group_zero_like_count",
    "same_site_zero_like_count",
    "vendor_reply_class",
    "vendor_fault_family",
    "note",
]
CORE_FEATURE_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
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
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate a truth-independent same-group maintenance proxy shadow across the full strict-case universe."
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
        help="Sites to inspect. Defaults to the known stable sites.",
    )
    return parser.parse_args()


def coalesce_text(left: object, right: object) -> str:
    left_text = normalize_text(left)
    if left_text:
        return left_text
    return normalize_text(right)


def to_bool(value: object) -> bool:
    return normalize_text(value).lower() in {"1", "true", "t", "yes", "y"}


def to_float(value: object) -> float | None:
    text = normalize_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def fallback_group_key(panel_id: object) -> str:
    parts = normalize_text(panel_id).split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return normalize_text(panel_id)


def maintenance_prediction_label(current_actionability_v3: object, shadow_actionability_v3: object) -> str:
    current_value = normalize_text(current_actionability_v3)
    shadow_value = normalize_text(shadow_actionability_v3)
    if current_value == "maintenance_candidate" or shadow_value == "maintenance_candidate_shadow":
        return "positive"
    return "negative"


def load_core_site(root: Path, site: str) -> pd.DataFrame:
    path = root / "data" / site / "out" / "panel_day_core.csv"
    df = read_csv(path)
    if "panel_id" not in df.columns or "date" not in df.columns:
        raise SystemExit(f"panel_day_core.csv missing key columns for site={site}")

    df["site"] = site
    df["panel_id"] = df["panel_id"].map(normalize_text)
    df["strict_trigger_date"] = df["date"].map(normalize_date)
    df = df.drop_duplicates(subset=KEY_COLS, keep="first").copy()

    numeric_cols = ["mid_ratio", "last_ratio", "mid_v_ratio", "mid_i_ratio", "v_drop", "coverage_mid"]
    for col in numeric_cols:
        if col not in df.columns:
            df[col] = float("nan")
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["v_ref_ok", "shadow_like", "group_off_like"]:
        if col not in df.columns:
            df[col] = False
        else:
            df[col] = df[col].map(to_bool)

    if "group_key_base" not in df.columns:
        df["group_key_base"] = ""
    df["group_key_base"] = df["group_key_base"].map(normalize_text)
    missing_group = df["group_key_base"].eq("")
    df.loc[missing_group, "group_key_base"] = df.loc[missing_group, "panel_id"].map(fallback_group_key)
    df["fallback_group_proxy"] = df["group_key_base"]

    df["strict_day_zero_like_flag"] = (
        df["mid_ratio"].le(0.10)
        & df["mid_i_ratio"].le(0.10)
        & df["coverage_mid"].ge(0.50)
    ).fillna(False)

    same_site = df.groupby("strict_trigger_date", dropna=False)["strict_day_zero_like_flag"].sum().to_dict()
    same_group = (
        df.groupby(["strict_trigger_date", "fallback_group_proxy"], dropna=False)["strict_day_zero_like_flag"]
        .sum()
        .to_dict()
    )
    df["same_site_zero_like_count"] = df["strict_trigger_date"].map(lambda key: int(same_site.get(key, 0)))
    df["same_group_zero_like_count"] = df.apply(
        lambda row: int(same_group.get((row["strict_trigger_date"], row["fallback_group_proxy"]), 0)),
        axis=1,
    )

    core_unique = df.loc[:, CORE_FEATURE_COLS].copy()
    if core_unique.duplicated(subset=KEY_COLS).any():
        raise SystemExit(f"panel_day_core.csv has duplicate strict-day rows for site={site}")
    return core_unique


def load_core_all(root: Path, sites: list[str]) -> pd.DataFrame:
    frames = [load_core_site(root, site) for site in sites]
    if not frames:
        return pd.DataFrame(columns=CORE_FEATURE_COLS)
    return pd.concat(frames, ignore_index=True)


def build_joined(root: Path, sites: list[str]) -> pd.DataFrame:
    reaudit_df = read_csv(root / "_share" / "panel_date_reaudit_working.csv")
    vendor_df = read_csv(root / "_share" / "vendor_reply_adjudication_latest.csv")
    actionability_df = read_csv(root / "_share" / "critical_actionability_shadow_v3_latest.csv")
    onset_df = read_csv(root / "_share" / "panel_onset_shadow_latest.csv")

    ensure_columns(reaudit_df, REAUDIT_REQUIRED_COLS, "panel_date_reaudit_working.csv")
    ensure_columns(vendor_df, VENDOR_REQUIRED_COLS, "vendor_reply_adjudication_latest.csv")
    ensure_columns(actionability_df, ACTIONABILITY_REQUIRED_COLS, "critical_actionability_shadow_v3_latest.csv")
    ensure_columns(onset_df, ONSET_REQUIRED_COLS, "panel_onset_shadow_latest.csv")

    if "days_earlier_than_trigger" not in reaudit_df.columns:
        reaudit_df["days_earlier_than_trigger"] = float("nan")
    if "onset_method" not in reaudit_df.columns:
        reaudit_df["onset_method"] = ""

    for df in [reaudit_df, vendor_df, actionability_df, onset_df]:
        for col in ["site", "panel_id"]:
            df[col] = df[col].map(normalize_text)
        df["strict_trigger_date"] = df["strict_trigger_date"].map(normalize_date)

    for col in [
        "candidate_validity",
        "onset_confidence",
        "reason_summary",
        "review_priority",
        "vendor_reply_class",
        "vendor_fault_family",
        "note",
    ]:
        reaudit_df[col] = reaudit_df[col].map(normalize_text)
    for col in ["vendor_reply_class", "vendor_fault_family", "vendor_note"]:
        vendor_df[col] = vendor_df[col].map(normalize_text)
    actionability_df["actionability_v3"] = actionability_df["actionability_v3"].map(normalize_text)
    for col in ["onset_confidence", "onset_method", "reason_summary"]:
        onset_df[col] = onset_df[col].map(normalize_text)
    onset_df["days_earlier_than_trigger"] = pd.to_numeric(onset_df["days_earlier_than_trigger"], errors="coerce")

    vendor_unique = dedupe(
        vendor_df.loc[:, VENDOR_REQUIRED_COLS],
        "vendor_reply_adjudication_latest.csv",
        KEY_COLS,
    ).rename(
        columns={
            "vendor_reply_class": "vendor_reply_class_vendor",
            "vendor_fault_family": "vendor_fault_family_vendor",
            "vendor_note": "vendor_note_vendor",
        }
    )
    actionability_unique = dedupe(
        actionability_df.loc[:, ACTIONABILITY_REQUIRED_COLS],
        "critical_actionability_shadow_v3_latest.csv",
        KEY_COLS,
    ).rename(columns={"actionability_v3": "current_actionability_v3"})
    onset_unique = dedupe(
        onset_df.loc[:, ONSET_REQUIRED_COLS],
        "panel_onset_shadow_latest.csv",
        KEY_COLS,
    ).rename(
        columns={
            "days_earlier_than_trigger": "days_earlier_than_trigger_onset",
            "onset_confidence": "onset_confidence_onset",
            "onset_method": "onset_method_onset",
            "reason_summary": "reason_summary_onset",
        }
    )

    joined = reaudit_df.merge(vendor_unique, on=KEY_COLS, how="left")
    joined = joined.merge(actionability_unique, on=KEY_COLS, how="left")
    joined = joined.merge(onset_unique, on=KEY_COLS, how="left")

    joined["vendor_reply_class"] = joined.apply(
        lambda row: coalesce_text(row["vendor_reply_class"], row.get("vendor_reply_class_vendor", "")),
        axis=1,
    )
    joined["vendor_fault_family"] = joined.apply(
        lambda row: coalesce_text(row["vendor_fault_family"], row.get("vendor_fault_family_vendor", "")),
        axis=1,
    )
    joined["note"] = joined.apply(
        lambda row: coalesce_text(row["note"], row.get("vendor_note_vendor", "")),
        axis=1,
    )
    joined["current_actionability_v3"] = joined["current_actionability_v3"].fillna("").map(normalize_text)
    joined["days_earlier_than_trigger"] = joined["days_earlier_than_trigger_onset"].where(
        joined["days_earlier_than_trigger_onset"].notna(),
        pd.to_numeric(joined["days_earlier_than_trigger"], errors="coerce"),
    )
    joined["onset_confidence"] = joined.apply(
        lambda row: coalesce_text(row.get("onset_confidence_onset", ""), row.get("onset_confidence", "")),
        axis=1,
    )
    joined["onset_method"] = joined.apply(
        lambda row: coalesce_text(row.get("onset_method_onset", ""), row.get("onset_method", "")),
        axis=1,
    )
    joined["reason_summary_eval"] = joined.apply(
        lambda row: coalesce_text(row.get("reason_summary_onset", ""), row.get("reason_summary", "")),
        axis=1,
    )

    parsed = joined["reason_summary_eval"].apply(parse_reason_summary).apply(pd.Series).rename(
        columns={
            "parsed_strict_method": "strict_method",
            "parsed_shadow_frac": "shadow_frac",
            "parsed_group_off_frac": "group_off_frac",
            "parsed_recovery_reset": "recovery_reset",
        }
    )
    joined = pd.concat([joined, parsed], axis=1)

    core_all = load_core_all(root, sites)
    joined = joined.merge(core_all, on=KEY_COLS, how="left")
    joined["fallback_group_proxy"] = joined["fallback_group_proxy"].fillna("")
    missing_group = joined["fallback_group_proxy"].eq("")
    joined.loc[missing_group, "fallback_group_proxy"] = joined.loc[missing_group, "panel_id"].map(fallback_group_key)

    joined["strict_method"] = joined["strict_method"].fillna("").map(normalize_text)
    joined["recovery_reset"] = joined["recovery_reset"].fillna("").map(normalize_text)
    joined["shadow_frac"] = pd.to_numeric(joined["shadow_frac"], errors="coerce")
    joined["group_off_frac"] = pd.to_numeric(joined["group_off_frac"], errors="coerce")
    joined["same_group_zero_like_count"] = pd.to_numeric(
        joined["same_group_zero_like_count"], errors="coerce"
    ).fillna(0).astype(int)
    joined["same_site_zero_like_count"] = pd.to_numeric(
        joined["same_site_zero_like_count"], errors="coerce"
    ).fillna(0).astype(int)

    joined["clean_confirmed_flag"] = (
        joined["strict_method"].eq("confirmed_fault_flag")
        & joined["shadow_frac"].eq(0)
        & joined["group_off_frac"].eq(0)
        & joined["recovery_reset"].eq("no")
    ).fillna(False)
    joined["strict_day_group_like_flag"] = (
        pd.to_numeric(joined["mid_ratio"], errors="coerce").le(0.10)
        & pd.to_numeric(joined["mid_i_ratio"], errors="coerce").le(0.10)
        & pd.to_numeric(joined["mid_v_ratio"], errors="coerce").ge(1.05)
    ).fillna(False)
    joined["onset_recent_flag"] = pd.to_numeric(joined["days_earlier_than_trigger"], errors="coerce").le(7).fillna(False)
    joined["truth_source"] = joined.apply(
        lambda row: resolve_truth_source(row["candidate_validity"], row["vendor_reply_class"]),
        axis=1,
    )
    joined["proxy_selected_flag"] = (
        joined["current_actionability_v3"].ne("maintenance_candidate")
        & joined["clean_confirmed_flag"]
        & joined["strict_day_group_like_flag"]
        & joined["same_group_zero_like_count"].ge(2)
    )
    joined["shadow_actionability_v3"] = joined["proxy_selected_flag"].map(
        lambda flag: "maintenance_candidate_shadow" if bool(flag) else ""
    )
    return joined


def evaluate(joined: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary_rows: list[dict[str, object]] = []
    error_rows: list[dict[str, object]] = []

    selected_df = joined.loc[joined["proxy_selected_flag"]].copy()
    selected_df = selected_df.loc[:, SELECTED_COLS] if not selected_df.empty else pd.DataFrame(columns=SELECTED_COLS)

    for scenario in SCENARIOS:
        scenario_df = joined.copy()
        if scenario == "baseline_v3":
            scenario_df["shadow_actionability_v3"] = ""
        promoted_case_count = int(scenario_df["shadow_actionability_v3"].eq("maintenance_candidate_shadow").sum())
        scenario_df["final_prediction_label"] = scenario_df.apply(
            lambda row: maintenance_prediction_label(row["current_actionability_v3"], row["shadow_actionability_v3"]),
            axis=1,
        )

        for truth_mode in TRUTH_MODES:
            base = scenario_df.copy()
            base["truth_label"] = base.apply(
                lambda row: hybrid_truth_label(row["candidate_validity"], row["vendor_reply_class"], truth_mode),
                axis=1,
            )
            for source_split in SOURCE_SPLITS:
                subset = base.loc[source_split_mask(base, source_split)].copy()
                excluded_rows = int(subset["truth_label"].eq("exclude").sum())
                scored = subset.loc[subset["truth_label"].ne("exclude")].copy()
                scored_rows = len(scored)

                tp = int(((scored["truth_label"] == "positive") & (scored["final_prediction_label"] == "positive")).sum())
                fp = int(((scored["truth_label"] == "negative") & (scored["final_prediction_label"] == "positive")).sum())
                fn = int(((scored["truth_label"] == "positive") & (scored["final_prediction_label"] == "negative")).sum())
                tn = int(((scored["truth_label"] == "negative") & (scored["final_prediction_label"] == "negative")).sum())
                precision = safe_metric(tp, tp + fp)
                recall = safe_metric(tp, tp + fn)
                f1 = safe_metric(2 * precision * recall, precision + recall) if (precision + recall) > 0 else 0.0
                summary_rows.append(
                    {
                        "scenario": scenario,
                        "truth_mode": truth_mode,
                        "source_split": source_split,
                        "tp": tp,
                        "fp": fp,
                        "fn": fn,
                        "tn": tn,
                        "precision": precision,
                        "recall": recall,
                        "f1": f1,
                        "excluded_rows": excluded_rows,
                        "scored_rows": scored_rows,
                        "promoted_case_count": promoted_case_count,
                    }
                )

                errors = scored.loc[
                    scored["truth_label"].ne(scored["final_prediction_label"]),
                    [
                        "site",
                        "panel_id",
                        "strict_trigger_date",
                        "truth_source",
                        "truth_label",
                        "current_actionability_v3",
                        "shadow_actionability_v3",
                        "final_prediction_label",
                        "strict_method",
                        "shadow_frac",
                        "group_off_frac",
                        "recovery_reset",
                        "same_group_zero_like_count",
                        "same_site_zero_like_count",
                        "vendor_reply_class",
                        "vendor_fault_family",
                        "note",
                    ],
                ].copy()
                errors["error_type"] = errors["final_prediction_label"].map(
                    lambda label: "fp" if label == "positive" else "fn"
                )
                errors.insert(0, "source_split", source_split)
                errors.insert(0, "truth_mode", truth_mode)
                errors.insert(0, "scenario", scenario)
                error_rows.extend(errors.to_dict(orient="records"))

    summary_df = pd.DataFrame(summary_rows, columns=SUMMARY_COLS)
    error_df = pd.DataFrame(error_rows, columns=ERROR_COLS)
    return summary_df, selected_df, error_df


def main() -> None:
    args = parse_args()
    joined = build_joined(args.root.resolve(), list(args.sites))
    summary_df, selected_df, error_df = evaluate(joined)

    out_dir = args.root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(out_dir / "maintenance_proxy_shadow_f1_summary_v1.csv", index=False, encoding="utf-8-sig")
    selected_df.to_csv(out_dir / "maintenance_proxy_shadow_selected_cases_v1.csv", index=False, encoding="utf-8-sig")
    error_df.to_csv(out_dir / "maintenance_proxy_shadow_case_errors_v1.csv", index=False, encoding="utf-8-sig")
    print(f"maintenance_proxy_shadow_eval_rows_v1={len(joined)}")


if __name__ == "__main__":
    main()
