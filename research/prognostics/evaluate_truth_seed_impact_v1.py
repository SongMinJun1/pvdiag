#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from evaluate_full_algorithm_f1_v3 import (
    ACTIONABILITY_REQUIRED_COLS,
    KEY_COLS,
    PREDICTION_MODES,
    REAUDIT_REQUIRED_COLS,
    SOURCE_SPLITS,
    TRUTH_MODES,
    VALID_CANDIDATE_VALIDITY,
    VENDOR_REQUIRED_COLS,
    coalesce_text,
    dedupe,
    derive_actionability,
    ensure_columns,
    hybrid_truth_label,
    normalize_date,
    normalize_text,
    parse_reason_summary,
    prediction_label,
    read_csv,
    resolve_truth_source,
    safe_metric,
    source_split_mask,
)

METRIC_STATE_COLS = [
    "truth_mode",
    "prediction_mode",
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
    "manual_truth_present_count",
    "vendor_truth_used_count",
]
METRIC_DELTA_COLS = [
    "truth_mode",
    "prediction_mode",
    "source_split",
    "current_f1",
    "proposed_f1",
    "delta_f1",
    "current_scored_rows",
    "proposed_scored_rows",
    "delta_scored_rows",
    "current_manual_truth_present_count",
    "proposed_manual_truth_present_count",
    "delta_manual_truth_present_count",
    "current_vendor_truth_used_count",
    "proposed_vendor_truth_used_count",
    "delta_vendor_truth_used_count",
]
CHANGED_CASE_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "truth_mode",
    "current_truth_source",
    "current_truth_label",
    "proposed_truth_source",
    "proposed_truth_label",
    "candidate_validity_current",
    "candidate_validity_proposed",
    "vendor_reply_class",
    "vendor_fault_family",
    "actionability_v3",
    "change_type",
]
SUMMARY_COLS = [
    "record_type",
    "current_manual_truth_present_count_total",
    "proposed_manual_truth_present_count_total",
    "delta_manual_truth_present_count_total",
    "changed_case_count",
    "changed_case_count_vendor_to_manual_same_label",
    "changed_case_count_vendor_to_manual_label_changed",
    "changed_case_count_excluded_to_manual_scored",
    "truth_mode",
    "prediction_mode",
    "source_split",
    "current_f1",
    "proposed_f1",
    "delta_f1",
    "current_scored_rows",
    "proposed_scored_rows",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare current canonical truth against a proposed copyback sidecar using full_algorithm_f1_v3 logic."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to project root.",
    )
    return parser.parse_args()


def build_joined_for_truth_state(root: Path, truth_path: Path) -> pd.DataFrame:
    truth_df = read_csv(truth_path)
    vendor_df = read_csv(root / "_share" / "vendor_reply_adjudication_latest.csv")
    actionability_df = read_csv(root / "_share" / "critical_actionability_shadow_v3_latest.csv")

    ensure_columns(truth_df, REAUDIT_REQUIRED_COLS, truth_path.name)
    ensure_columns(vendor_df, VENDOR_REQUIRED_COLS, "vendor_reply_adjudication_latest.csv")
    ensure_columns(actionability_df, ACTIONABILITY_REQUIRED_COLS, "critical_actionability_shadow_v3_latest.csv")

    for df in [truth_df, vendor_df, actionability_df]:
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
        truth_df[col] = truth_df[col].map(normalize_text)
    for col in ["vendor_reply_class", "vendor_fault_family", "vendor_note"]:
        vendor_df[col] = vendor_df[col].map(normalize_text)
    actionability_df["actionability_v3"] = actionability_df["actionability_v3"].map(normalize_text)

    invalid_values = sorted(set(truth_df["candidate_validity"]) - VALID_CANDIDATE_VALIDITY)
    if invalid_values:
        raise SystemExit(f"{truth_path.name} has invalid candidate_validity values: {invalid_values}")

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
    )

    joined = truth_df.merge(vendor_unique, on=KEY_COLS, how="left")
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
    joined["actionability_v3"] = joined["actionability_v3"].fillna("").map(normalize_text)
    parsed = joined["reason_summary"].apply(parse_reason_summary).apply(pd.Series)
    joined = pd.concat([joined, parsed], axis=1)
    derived = joined.apply(derive_actionability, axis=1, result_type="expand")
    derived.columns = ["derived_actionability_v3", "prediction_source"]
    joined = pd.concat([joined, derived], axis=1)
    joined["final_actionability_v3"] = joined.apply(
        lambda row: coalesce_text(row["actionability_v3"], row["derived_actionability_v3"]),
        axis=1,
    )
    joined["truth_source"] = joined.apply(
        lambda row: resolve_truth_source(row["candidate_validity"], row["vendor_reply_class"]),
        axis=1,
    )
    return joined


def evaluate_state(joined: pd.DataFrame) -> pd.DataFrame:
    metric_rows: list[dict[str, object]] = []

    for truth_mode in TRUTH_MODES:
        base = joined.copy()
        base["truth_label"] = base.apply(
            lambda row: hybrid_truth_label(row["candidate_validity"], row["vendor_reply_class"], truth_mode),
            axis=1,
        )
        base["manual_truth_present_flag"] = base["truth_source"].eq("manual_truth").astype(int)
        base["vendor_truth_used_flag"] = (
            base["truth_source"].eq("vendor_truth") & base["truth_label"].ne("exclude")
        ).astype(int)

        for prediction_mode in PREDICTION_MODES:
            base["prediction_label"] = base["final_actionability_v3"].map(
                lambda value: prediction_label(value, prediction_mode)
            )

            for source_split in SOURCE_SPLITS:
                subset = base.loc[source_split_mask(base, source_split)].copy()
                excluded_rows = int(subset["truth_label"].eq("exclude").sum())
                scored = subset.loc[subset["truth_label"].ne("exclude")].copy()

                tp = int(((scored["truth_label"] == "positive") & (scored["prediction_label"] == "positive")).sum())
                fp = int(((scored["truth_label"] == "negative") & (scored["prediction_label"] == "positive")).sum())
                fn = int(((scored["truth_label"] == "positive") & (scored["prediction_label"] == "negative")).sum())
                tn = int(((scored["truth_label"] == "negative") & (scored["prediction_label"] == "negative")).sum())

                precision = safe_metric(tp, tp + fp)
                recall = safe_metric(tp, tp + fn)
                f1 = safe_metric(2 * precision * recall, precision + recall) if (precision + recall) > 0 else 0.0

                metric_rows.append(
                    {
                        "truth_mode": truth_mode,
                        "prediction_mode": prediction_mode,
                        "source_split": source_split,
                        "tp": tp,
                        "fp": fp,
                        "fn": fn,
                        "tn": tn,
                        "precision": precision,
                        "recall": recall,
                        "f1": f1,
                        "excluded_rows": excluded_rows,
                        "scored_rows": int(len(scored)),
                        "manual_truth_present_count": int(subset["manual_truth_present_flag"].sum()),
                        "vendor_truth_used_count": int(subset["vendor_truth_used_flag"].sum()),
                    }
                )

    return pd.DataFrame(metric_rows, columns=METRIC_STATE_COLS)


def build_metric_delta(current_metrics: pd.DataFrame, proposed_metrics: pd.DataFrame) -> pd.DataFrame:
    merged = current_metrics.merge(
        proposed_metrics,
        on=["truth_mode", "prediction_mode", "source_split"],
        suffixes=("_current", "_proposed"),
        how="inner",
    )

    delta_rows: list[dict[str, object]] = []
    for _, row in merged.iterrows():
        delta_rows.append(
            {
                "truth_mode": row["truth_mode"],
                "prediction_mode": row["prediction_mode"],
                "source_split": row["source_split"],
                "current_f1": row["f1_current"],
                "proposed_f1": row["f1_proposed"],
                "delta_f1": round(float(row["f1_proposed"] - row["f1_current"]), 6),
                "current_scored_rows": int(row["scored_rows_current"]),
                "proposed_scored_rows": int(row["scored_rows_proposed"]),
                "delta_scored_rows": int(row["scored_rows_proposed"] - row["scored_rows_current"]),
                "current_manual_truth_present_count": int(row["manual_truth_present_count_current"]),
                "proposed_manual_truth_present_count": int(row["manual_truth_present_count_proposed"]),
                "delta_manual_truth_present_count": int(
                    row["manual_truth_present_count_proposed"] - row["manual_truth_present_count_current"]
                ),
                "current_vendor_truth_used_count": int(row["vendor_truth_used_count_current"]),
                "proposed_vendor_truth_used_count": int(row["vendor_truth_used_count_proposed"]),
                "delta_vendor_truth_used_count": int(
                    row["vendor_truth_used_count_proposed"] - row["vendor_truth_used_count_current"]
                ),
            }
        )

    delta_df = pd.DataFrame(delta_rows, columns=METRIC_DELTA_COLS)
    return delta_df.sort_values(["truth_mode", "prediction_mode", "source_split"]).reset_index(drop=True)


def classify_change_type(
    current_truth_source: str,
    current_truth_label: str,
    proposed_truth_source: str,
    proposed_truth_label: str,
) -> str:
    if current_truth_source == "vendor_truth" and proposed_truth_source == "manual_truth":
        if current_truth_label == proposed_truth_label:
            return "vendor_to_manual_same_label"
        return "vendor_to_manual_label_changed"
    if current_truth_label == "exclude" and proposed_truth_source == "manual_truth" and proposed_truth_label in {"positive", "negative"}:
        return "excluded_to_manual_scored"
    raise SystemExit(
        "unhandled changed-case transition: "
        f"current=({current_truth_source},{current_truth_label}) "
        f"proposed=({proposed_truth_source},{proposed_truth_label})"
    )


def build_changed_cases(current_joined: pd.DataFrame, proposed_joined: pd.DataFrame) -> pd.DataFrame:
    current_base = current_joined.loc[
        :,
        [*KEY_COLS, "candidate_validity", "vendor_reply_class", "vendor_fault_family", "actionability_v3"],
    ].rename(columns={"candidate_validity": "candidate_validity_current"})
    proposed_base = proposed_joined.loc[
        :,
        [*KEY_COLS, "candidate_validity"],
    ].rename(columns={"candidate_validity": "candidate_validity_proposed"})

    compare_df = current_base.merge(proposed_base, on=KEY_COLS, how="inner")

    changed_rows: list[dict[str, object]] = []
    for truth_mode in TRUTH_MODES:
        for _, row in compare_df.iterrows():
            current_truth_source = resolve_truth_source(row["candidate_validity_current"], row["vendor_reply_class"])
            proposed_truth_source = resolve_truth_source(row["candidate_validity_proposed"], row["vendor_reply_class"])
            current_truth_label = hybrid_truth_label(
                row["candidate_validity_current"], row["vendor_reply_class"], truth_mode
            )
            proposed_truth_label = hybrid_truth_label(
                row["candidate_validity_proposed"], row["vendor_reply_class"], truth_mode
            )

            if current_truth_source == proposed_truth_source and current_truth_label == proposed_truth_label:
                continue

            changed_rows.append(
                {
                    "site": row["site"],
                    "panel_id": row["panel_id"],
                    "strict_trigger_date": row["strict_trigger_date"],
                    "truth_mode": truth_mode,
                    "current_truth_source": current_truth_source,
                    "current_truth_label": current_truth_label,
                    "proposed_truth_source": proposed_truth_source,
                    "proposed_truth_label": proposed_truth_label,
                    "candidate_validity_current": row["candidate_validity_current"],
                    "candidate_validity_proposed": row["candidate_validity_proposed"],
                    "vendor_reply_class": row["vendor_reply_class"],
                    "vendor_fault_family": row["vendor_fault_family"],
                    "actionability_v3": row["actionability_v3"],
                    "change_type": classify_change_type(
                        current_truth_source=current_truth_source,
                        current_truth_label=current_truth_label,
                        proposed_truth_source=proposed_truth_source,
                        proposed_truth_label=proposed_truth_label,
                    ),
                }
            )

    changed_df = pd.DataFrame(changed_rows, columns=CHANGED_CASE_COLS)
    if changed_df.empty:
        return changed_df
    return changed_df.sort_values(["truth_mode", "site", "strict_trigger_date", "panel_id"]).reset_index(drop=True)


def build_summary(
    current_joined: pd.DataFrame,
    proposed_joined: pd.DataFrame,
    metric_delta_df: pd.DataFrame,
    changed_cases_df: pd.DataFrame,
) -> pd.DataFrame:
    summary_row = {
        "record_type": "summary",
        "current_manual_truth_present_count_total": int(current_joined["truth_source"].eq("manual_truth").sum()),
        "proposed_manual_truth_present_count_total": int(proposed_joined["truth_source"].eq("manual_truth").sum()),
        "delta_manual_truth_present_count_total": int(
            proposed_joined["truth_source"].eq("manual_truth").sum()
            - current_joined["truth_source"].eq("manual_truth").sum()
        ),
        "changed_case_count": int(len(changed_cases_df)),
        "changed_case_count_vendor_to_manual_same_label": int(
            (changed_cases_df["change_type"] == "vendor_to_manual_same_label").sum()
        )
        if not changed_cases_df.empty
        else 0,
        "changed_case_count_vendor_to_manual_label_changed": int(
            (changed_cases_df["change_type"] == "vendor_to_manual_label_changed").sum()
        )
        if not changed_cases_df.empty
        else 0,
        "changed_case_count_excluded_to_manual_scored": int(
            (changed_cases_df["change_type"] == "excluded_to_manual_scored").sum()
        )
        if not changed_cases_df.empty
        else 0,
        "truth_mode": "",
        "prediction_mode": "",
        "source_split": "",
        "current_f1": "",
        "proposed_f1": "",
        "delta_f1": "",
        "current_scored_rows": "",
        "proposed_scored_rows": "",
    }

    metric_rows = [
        {
            "record_type": "metric",
            "current_manual_truth_present_count_total": "",
            "proposed_manual_truth_present_count_total": "",
            "delta_manual_truth_present_count_total": "",
            "changed_case_count": "",
            "changed_case_count_vendor_to_manual_same_label": "",
            "changed_case_count_vendor_to_manual_label_changed": "",
            "changed_case_count_excluded_to_manual_scored": "",
            "truth_mode": row["truth_mode"],
            "prediction_mode": row["prediction_mode"],
            "source_split": row["source_split"],
            "current_f1": row["current_f1"],
            "proposed_f1": row["proposed_f1"],
            "delta_f1": row["delta_f1"],
            "current_scored_rows": row["current_scored_rows"],
            "proposed_scored_rows": row["proposed_scored_rows"],
        }
        for _, row in metric_delta_df.iterrows()
    ]

    return pd.DataFrame([summary_row, *metric_rows], columns=SUMMARY_COLS)


def assert_same_base_universe(current_joined: pd.DataFrame, proposed_joined: pd.DataFrame) -> None:
    current_keys = set(current_joined.loc[:, KEY_COLS].itertuples(index=False, name=None))
    proposed_keys = set(proposed_joined.loc[:, KEY_COLS].itertuples(index=False, name=None))
    if current_keys != proposed_keys:
        raise SystemExit("current and proposed truth states must share the same strict-case base universe")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    current_joined = build_joined_for_truth_state(root=root, truth_path=root / "_share" / "panel_date_reaudit_working.csv")
    proposed_joined = build_joined_for_truth_state(
        root=root,
        truth_path=root / "_share" / "panel_date_reaudit_working_proposed_v1.csv",
    )
    assert_same_base_universe(current_joined=current_joined, proposed_joined=proposed_joined)

    current_metrics = evaluate_state(current_joined)
    proposed_metrics = evaluate_state(proposed_joined)
    metric_delta_df = build_metric_delta(current_metrics=current_metrics, proposed_metrics=proposed_metrics)
    changed_cases_df = build_changed_cases(current_joined=current_joined, proposed_joined=proposed_joined)
    summary_df = build_summary(
        current_joined=current_joined,
        proposed_joined=proposed_joined,
        metric_delta_df=metric_delta_df,
        changed_cases_df=changed_cases_df,
    )

    out_dir = root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(out_dir / "truth_seed_impact_summary_v1.csv", index=False, encoding="utf-8-sig")
    metric_delta_df.to_csv(out_dir / "truth_seed_impact_metric_delta_v1.csv", index=False, encoding="utf-8-sig")
    changed_cases_df.to_csv(out_dir / "truth_seed_impact_changed_cases_v1.csv", index=False, encoding="utf-8-sig")
    print(f"truth_seed_impact_changed_cases_v1={len(changed_cases_df)}")


if __name__ == "__main__":
    main()
