#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

PREDICTION_MODES = ("maintenance", "operational")
SOURCE_SPLITS = ("overall", "vendor_reply_present", "vendor_reply_absent")
TRUTH_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "candidate_validity",
    "review_priority",
    "vendor_reply_class",
    "vendor_fault_family",
    "note",
]
ACTIONABILITY_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "actionability_v3",
]
SUMMARY_COLS = [
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
    "coverage",
]
CONFUSION_COLS = [
    "prediction_mode",
    "source_split",
    "tp",
    "fp",
    "fn",
    "tn",
    "excluded_rows",
    "scored_rows",
    "coverage",
]
ERROR_COLS = [
    "prediction_mode",
    "source_split",
    "site",
    "panel_id",
    "strict_trigger_date",
    "candidate_validity",
    "truth_label",
    "actionability_v3",
    "prediction_label",
    "error_type",
    "review_priority",
    "vendor_reply_class",
    "vendor_fault_family",
    "note",
]
VALID_CANDIDATE_VALIDITY = {
    "true_positive",
    "group_side",
    "false_positive",
    "needs_more_info",
    "",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate full strict-case algorithm F1 on panel_date_reaudit_working.csv."
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


def safe_metric(numer: int | float, denom: int | float) -> float:
    if denom <= 0:
        return 0.0
    return round(float(numer / denom), 6)


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def truth_label(candidate_validity: object) -> str:
    value = normalize_text(candidate_validity)
    if value in {"true_positive", "group_side"}:
        return "positive"
    if value == "false_positive":
        return "negative"
    return "exclude"


def prediction_label(actionability_v3: object, prediction_mode: str) -> str:
    value = normalize_text(actionability_v3)
    if prediction_mode == "maintenance":
        return "positive" if value == "maintenance_candidate" else "negative"
    if prediction_mode == "operational":
        return "positive" if value in {"maintenance_candidate", "common_cause_review", "singleton_review"} else "negative"
    raise ValueError(prediction_mode)


def source_split_mask(df: pd.DataFrame, source_split: str) -> pd.Series:
    vendor_present = df["vendor_reply_class"].map(normalize_text).ne("")
    if source_split == "overall":
        return pd.Series(True, index=df.index)
    if source_split == "vendor_reply_present":
        return vendor_present
    if source_split == "vendor_reply_absent":
        return ~vendor_present
    raise ValueError(source_split)


def build_joined(root: Path) -> pd.DataFrame:
    truth_df = read_csv(root / "_share" / "panel_date_reaudit_working.csv")
    v3_df = read_csv(root / "_share" / "critical_actionability_shadow_v3_latest.csv")

    ensure_columns(truth_df, TRUTH_REQUIRED_COLS, "panel_date_reaudit_working.csv")
    ensure_columns(v3_df, ACTIONABILITY_REQUIRED_COLS, "critical_actionability_shadow_v3_latest.csv")

    for df in [truth_df, v3_df]:
        for col in ["site", "panel_id"]:
            df[col] = df[col].map(normalize_text)
        df["strict_trigger_date"] = df["strict_trigger_date"].map(normalize_date)

    for col in ["candidate_validity", "review_priority", "vendor_reply_class", "vendor_fault_family", "note"]:
        truth_df[col] = truth_df[col].map(normalize_text)
    v3_df["actionability_v3"] = v3_df["actionability_v3"].map(normalize_text)

    invalid_values = sorted(set(truth_df["candidate_validity"]) - VALID_CANDIDATE_VALIDITY)
    if invalid_values:
        raise SystemExit(f"panel_date_reaudit_working.csv has invalid candidate_validity values: {invalid_values}")

    v3_unique = v3_df.loc[:, ACTIONABILITY_REQUIRED_COLS].drop_duplicates(
        subset=["site", "panel_id", "strict_trigger_date"]
    )
    joined = truth_df.merge(
        v3_unique,
        on=["site", "panel_id", "strict_trigger_date"],
        how="left",
    )
    joined["actionability_v3"] = joined["actionability_v3"].fillna("").map(normalize_text)
    joined["prediction_available_flag"] = joined["actionability_v3"].ne("").astype(int)
    return joined


def evaluate(joined: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary_rows: list[dict[str, object]] = []
    confusion_rows: list[dict[str, object]] = []
    error_rows: list[dict[str, object]] = []

    for prediction_mode in PREDICTION_MODES:
        base = joined.copy()
        base["truth_label"] = base["candidate_validity"].map(truth_label)
        base["prediction_label"] = base["actionability_v3"].map(lambda value: prediction_label(value, prediction_mode))

        for source_split in SOURCE_SPLITS:
            subset = base.loc[source_split_mask(base, source_split)].copy()
            excluded_rows = int(subset["truth_label"].eq("exclude").sum())
            scored = subset.loc[subset["truth_label"].ne("exclude")].copy()
            scored_rows = len(scored)
            coverage = safe_metric(int(scored["prediction_available_flag"].sum()), scored_rows)

            tp = int(((scored["truth_label"] == "positive") & (scored["prediction_label"] == "positive")).sum())
            fp = int(((scored["truth_label"] == "negative") & (scored["prediction_label"] == "positive")).sum())
            fn = int(((scored["truth_label"] == "positive") & (scored["prediction_label"] == "negative")).sum())
            tn = int(((scored["truth_label"] == "negative") & (scored["prediction_label"] == "negative")).sum())

            precision = safe_metric(tp, tp + fp)
            recall = safe_metric(tp, tp + fn)
            f1 = safe_metric(2 * precision * recall, precision + recall) if (precision + recall) > 0 else 0.0

            summary_rows.append(
                {
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
                    "scored_rows": scored_rows,
                    "coverage": coverage,
                }
            )
            confusion_rows.append(
                {
                    "prediction_mode": prediction_mode,
                    "source_split": source_split,
                    "tp": tp,
                    "fp": fp,
                    "fn": fn,
                    "tn": tn,
                    "excluded_rows": excluded_rows,
                    "scored_rows": scored_rows,
                    "coverage": coverage,
                }
            )

            errors = scored.loc[
                ((scored["truth_label"] == "positive") & (scored["prediction_label"] == "negative"))
                | ((scored["truth_label"] == "negative") & (scored["prediction_label"] == "positive"))
            ].copy()
            if not errors.empty:
                errors["error_type"] = errors.apply(
                    lambda row: "fn" if row["truth_label"] == "positive" else "fp",
                    axis=1,
                )
                errors["prediction_mode"] = prediction_mode
                errors["source_split"] = source_split
                error_rows.extend(errors.loc[:, ERROR_COLS].to_dict("records"))

    return (
        pd.DataFrame(summary_rows, columns=SUMMARY_COLS),
        pd.DataFrame(confusion_rows, columns=CONFUSION_COLS),
        pd.DataFrame(error_rows, columns=ERROR_COLS),
    )


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"

    joined = build_joined(root)
    summary_df, confusion_df, errors_df = evaluate(joined)

    summary_df.to_csv(share_dir / "full_algorithm_f1_summary.csv", index=False, encoding="utf-8-sig")
    confusion_df.to_csv(share_dir / "full_algorithm_confusion.csv", index=False, encoding="utf-8-sig")
    errors_df.to_csv(share_dir / "full_algorithm_case_errors.csv", index=False, encoding="utf-8-sig")

    print(f"full_algorithm_eval_rows={len(joined)}")


if __name__ == "__main__":
    main()
