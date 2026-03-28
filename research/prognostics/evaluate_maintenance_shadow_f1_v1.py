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
    LENIENT_VENDOR_NEGATIVE,
    LENIENT_VENDOR_POSITIVE,
    REAUDIT_REQUIRED_COLS,
    STRICT_VENDOR_NEGATIVE,
    STRICT_VENDOR_POSITIVE,
    VENDOR_REQUIRED_COLS,
    dedupe,
    ensure_columns,
    hybrid_truth_label,
    normalize_date,
    normalize_text,
    read_csv,
    resolve_truth_source,
    safe_metric,
    source_split_mask,
)

KEY_COLS = ["site", "panel_id", "strict_trigger_date"]
TRUTH_MODES = ("strict", "lenient")
SOURCE_SPLITS = ("overall", "manual_truth", "vendor_truth")
SCENARIOS = ("baseline_v3", "strict_backed_shadow", "full_candidate_shadow")
ACTIONABILITY_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "actionability_v3",
]
AUDIT_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "gap_bucket",
    "promotion_hypothesis",
    "appears_in_strict",
    "appears_in_lenient",
    "vendor_fault_family",
    "note",
]
SUMMARY_BASELINE_REQUIRED_COLS = [
    "truth_mode",
    "prediction_mode",
    "source_split",
    "f1",
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
    "promoted_strict_backed_count",
    "promoted_lenient_only_count",
]
CASE_CHANGE_COLS = [
    "scenario",
    "site",
    "panel_id",
    "strict_trigger_date",
    "appears_in_strict",
    "appears_in_lenient",
    "gap_bucket",
    "promotion_hypothesis",
    "baseline_actionability_v3",
    "shadow_actionability_v3",
    "promotion_tier",
    "vendor_reply_class",
    "vendor_fault_family",
    "note",
]
PROMOTION_SET_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "gap_bucket",
    "promotion_hypothesis",
    "appears_in_strict",
    "appears_in_lenient",
    "in_strict_backed_shadow",
    "in_full_candidate_shadow",
    "vendor_fault_family",
    "note",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate maintenance-shadow F1 gains using maintenance gap audit candidates without changing official outputs."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to project root.",
    )
    return parser.parse_args()


def coalesce_text(left: object, right: object) -> str:
    left_text = normalize_text(left)
    if left_text:
        return left_text
    return normalize_text(right)


def to_int_flag(value: object) -> int:
    text = normalize_text(value).lower()
    return 1 if text in {"1", "true", "t", "yes", "y"} else 0


def maintenance_prediction_label(actionability: object) -> str:
    value = normalize_text(actionability)
    return "positive" if value in {"maintenance_candidate", "maintenance_candidate_shadow"} else "negative"


def load_joined(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    reaudit_df = read_csv(root / "_share" / "panel_date_reaudit_working.csv")
    vendor_df = read_csv(root / "_share" / "vendor_reply_adjudication_latest.csv")
    actionability_df = read_csv(root / "_share" / "critical_actionability_shadow_v3_latest.csv")
    audit_df = read_csv(root / "_share" / "maintenance_gap_audit_cases_v1.csv")

    ensure_columns(reaudit_df, REAUDIT_REQUIRED_COLS, "panel_date_reaudit_working.csv")
    ensure_columns(vendor_df, VENDOR_REQUIRED_COLS, "vendor_reply_adjudication_latest.csv")
    ensure_columns(actionability_df, ACTIONABILITY_REQUIRED_COLS, "critical_actionability_shadow_v3_latest.csv")
    ensure_columns(audit_df, AUDIT_REQUIRED_COLS, "maintenance_gap_audit_cases_v1.csv")

    optional_summary_path = root / "_share" / "full_algorithm_f1_summary_v3.csv"
    if optional_summary_path.exists():
        summary_df = read_csv(optional_summary_path)
        ensure_columns(summary_df, SUMMARY_BASELINE_REQUIRED_COLS, "full_algorithm_f1_summary_v3.csv")

    for df in [reaudit_df, vendor_df, actionability_df, audit_df]:
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
    for col in [
        "gap_bucket",
        "promotion_hypothesis",
        "vendor_fault_family",
        "note",
    ]:
        audit_df[col] = audit_df[col].map(normalize_text)
    audit_df["appears_in_strict"] = audit_df["appears_in_strict"].map(to_int_flag)
    audit_df["appears_in_lenient"] = audit_df["appears_in_lenient"].map(to_int_flag)

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
    ).rename(columns={"actionability_v3": "baseline_actionability_v3"})

    joined = reaudit_df.merge(vendor_unique, on=KEY_COLS, how="left")
    joined = joined.merge(actionability_unique, on=KEY_COLS, how="left")
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
    joined["baseline_actionability_v3"] = joined["baseline_actionability_v3"].fillna("").map(normalize_text)
    joined["truth_source"] = joined.apply(
        lambda row: resolve_truth_source(row["candidate_validity"], row["vendor_reply_class"]),
        axis=1,
    )
    joined["baseline_prediction_label"] = joined["baseline_actionability_v3"].map(maintenance_prediction_label)
    return joined, audit_df


def candidate_sets(audit_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, set[tuple[str, str, str]]]]:
    candidates = audit_df.loc[
        audit_df["promotion_hypothesis"].eq("candidate_for_maintenance_shadow")
    ].copy()
    candidates["in_strict_backed_shadow"] = candidates["appears_in_strict"].astype(int)
    candidates["in_full_candidate_shadow"] = 1
    scenario_keys = {
        "baseline_v3": set(),
        "strict_backed_shadow": {
            tuple(row) for row in candidates.loc[candidates["appears_in_strict"].eq(1), KEY_COLS].itertuples(index=False, name=None)
        },
        "full_candidate_shadow": {
            tuple(row) for row in candidates.loc[:, KEY_COLS].itertuples(index=False, name=None)
        },
    }
    return candidates, scenario_keys


def evaluate(
    joined: pd.DataFrame,
    candidates: pd.DataFrame,
    scenario_keys: dict[str, set[tuple[str, str, str]]],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary_rows: list[dict[str, object]] = []
    case_change_rows: list[dict[str, object]] = []

    candidate_lookup = candidates.set_index(KEY_COLS, drop=False) if not candidates.empty else None

    for scenario in SCENARIOS:
        promoted_keys = scenario_keys[scenario]
        promoted_case_count = len(promoted_keys)
        promoted_strict_backed_count = len(scenario_keys["strict_backed_shadow"] & promoted_keys)
        promoted_lenient_only_count = promoted_case_count - promoted_strict_backed_count

        scenario_df = joined.copy()
        scenario_df["shadow_actionability_v3"] = scenario_df.apply(
            lambda row: "maintenance_candidate_shadow"
            if tuple(row[col] for col in KEY_COLS) in promoted_keys
            else normalize_text(row["baseline_actionability_v3"]),
            axis=1,
        )
        scenario_df["shadow_prediction_label"] = scenario_df["shadow_actionability_v3"].map(maintenance_prediction_label)

        if promoted_keys:
            promoted_rows = scenario_df.loc[
                scenario_df.apply(lambda row: tuple(row[col] for col in KEY_COLS) in promoted_keys, axis=1)
            ].copy()
            for row in promoted_rows.itertuples(index=False):
                candidate_row = candidate_lookup.loc[(row.site, row.panel_id, row.strict_trigger_date)]
                if isinstance(candidate_row, pd.DataFrame):
                    candidate_row = candidate_row.iloc[0]
                case_change_rows.append(
                    {
                        "scenario": scenario,
                        "site": row.site,
                        "panel_id": row.panel_id,
                        "strict_trigger_date": row.strict_trigger_date,
                        "appears_in_strict": int(candidate_row["appears_in_strict"]),
                        "appears_in_lenient": int(candidate_row["appears_in_lenient"]),
                        "gap_bucket": normalize_text(candidate_row["gap_bucket"]),
                        "promotion_hypothesis": normalize_text(candidate_row["promotion_hypothesis"]),
                        "baseline_actionability_v3": normalize_text(row.baseline_actionability_v3),
                        "shadow_actionability_v3": normalize_text(row.shadow_actionability_v3),
                        "promotion_tier": "strict_backed"
                        if int(candidate_row["appears_in_strict"]) == 1
                        else "lenient_only",
                        "vendor_reply_class": normalize_text(row.vendor_reply_class),
                        "vendor_fault_family": normalize_text(row.vendor_fault_family),
                        "note": normalize_text(row.note),
                    }
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
                tp = int(((scored["truth_label"] == "positive") & (scored["shadow_prediction_label"] == "positive")).sum())
                fp = int(((scored["truth_label"] == "negative") & (scored["shadow_prediction_label"] == "positive")).sum())
                fn = int(((scored["truth_label"] == "positive") & (scored["shadow_prediction_label"] == "negative")).sum())
                tn = int(((scored["truth_label"] == "negative") & (scored["shadow_prediction_label"] == "negative")).sum())
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
                        "promoted_strict_backed_count": promoted_strict_backed_count,
                        "promoted_lenient_only_count": promoted_lenient_only_count,
                    }
                )

    summary_df = pd.DataFrame(summary_rows, columns=SUMMARY_COLS)
    case_change_df = pd.DataFrame(case_change_rows, columns=CASE_CHANGE_COLS)
    promotion_set_df = candidates.loc[:, PROMOTION_SET_COLS].copy() if not candidates.empty else pd.DataFrame(columns=PROMOTION_SET_COLS)
    return summary_df, case_change_df, promotion_set_df


def main() -> None:
    args = parse_args()
    joined, audit_df = load_joined(args.root.resolve())
    candidates, scenario_keys = candidate_sets(audit_df)
    summary_df, case_change_df, promotion_set_df = evaluate(joined, candidates, scenario_keys)

    out_dir = args.root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(out_dir / "maintenance_shadow_f1_summary_v1.csv", index=False, encoding="utf-8-sig")
    case_change_df.to_csv(out_dir / "maintenance_shadow_case_changes_v1.csv", index=False, encoding="utf-8-sig")
    promotion_set_df.to_csv(out_dir / "maintenance_shadow_promotion_sets_v1.csv", index=False, encoding="utf-8-sig")
    print(f"maintenance_shadow_eval_rows_v1={len(joined)}")


if __name__ == "__main__":
    main()
