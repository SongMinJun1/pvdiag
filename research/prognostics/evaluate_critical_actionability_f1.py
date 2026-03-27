#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

TRUTH_MODES = ("strict", "lenient")
PREDICTION_MODES = ("maintenance", "operational_review")
V3_REQUIRED_COLS = ["site", "panel_id", "actionability_v3"]
VENDOR_REQUIRED_COLS = [
    "site",
    "panel_id",
    "vendor_reply_class",
    "vendor_fault_family",
    "vendor_note",
]
SUMMARY_COLS = [
    "truth_mode",
    "prediction_mode",
    "tp",
    "fp",
    "fn",
    "tn",
    "precision",
    "recall",
    "f1",
    "excluded_rows",
]
CONFUSION_COLS = [
    "truth_mode",
    "prediction_mode",
    "tp",
    "fp",
    "fn",
    "tn",
    "excluded_rows",
]
ERROR_COLS = [
    "truth_mode",
    "prediction_mode",
    "site",
    "panel_id",
    "vendor_reply_class",
    "vendor_fault_family",
    "actionability_v3",
    "truth_label",
    "prediction_label",
    "error_type",
    "vendor_note",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate panel-level critical actionability F1 on the vendor-adjudicated critical subset.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to project root.",
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


def safe_metric(numer: int, denom: int) -> float:
    if denom <= 0:
        return 0.0
    return round(float(numer / denom), 6)


def truth_label(vendor_reply_class: str, truth_mode: str) -> str:
    value = normalize_text(vendor_reply_class)
    if truth_mode == "strict":
        if value in {"field_confirmed_positive", "vendor_pattern_positive"}:
            return "positive"
        if value == "vendor_rejected":
            return "negative"
        return "exclude"
    if truth_mode == "lenient":
        if value in {"field_confirmed_positive", "vendor_pattern_positive", "vendor_likely_positive"}:
            return "positive"
        if value == "vendor_rejected":
            return "negative"
        return "exclude"
    raise ValueError(truth_mode)


def prediction_label(actionability_v3: str, prediction_mode: str) -> str:
    value = normalize_text(actionability_v3)
    if prediction_mode == "maintenance":
        return "positive" if value == "maintenance_candidate" else "negative"
    if prediction_mode == "operational_review":
        return "positive" if value in {"maintenance_candidate", "common_cause_review", "singleton_review"} else "negative"
    raise ValueError(prediction_mode)


def build_joined(root: Path) -> pd.DataFrame:
    v3_df = read_csv(root / "_share" / "critical_actionability_shadow_v3_latest.csv")
    vendor_df = read_csv(root / "_share" / "vendor_reply_adjudication_latest.csv")

    missing_v3 = [col for col in V3_REQUIRED_COLS if col not in v3_df.columns]
    if missing_v3:
        raise SystemExit(f"critical_actionability_shadow_v3_latest.csv missing columns: {missing_v3}")
    missing_vendor = [col for col in VENDOR_REQUIRED_COLS if col not in vendor_df.columns]
    if missing_vendor:
        raise SystemExit(f"vendor_reply_adjudication_latest.csv missing columns: {missing_vendor}")

    for df in [v3_df, vendor_df]:
        for col in ["site", "panel_id"]:
            df[col] = df[col].map(normalize_text)
    v3_df["actionability_v3"] = v3_df["actionability_v3"].map(normalize_text)
    vendor_df["vendor_reply_class"] = vendor_df["vendor_reply_class"].map(normalize_text)
    vendor_df["vendor_fault_family"] = vendor_df["vendor_fault_family"].map(normalize_text)
    vendor_df["vendor_note"] = vendor_df["vendor_note"].map(normalize_text)

    joined = vendor_df.merge(
        v3_df.loc[:, ["site", "panel_id", "actionability_v3"]].drop_duplicates(subset=["site", "panel_id"]),
        on=["site", "panel_id"],
        how="left",
    )
    joined["actionability_v3"] = joined["actionability_v3"].fillna("").map(normalize_text)
    return joined


def evaluate(joined: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary_rows: list[dict[str, object]] = []
    confusion_rows: list[dict[str, object]] = []
    error_rows: list[dict[str, object]] = []

    for truth_mode in TRUTH_MODES:
        for prediction_mode in PREDICTION_MODES:
            df = joined.copy()
            df["truth_label"] = df["vendor_reply_class"].map(lambda value: truth_label(value, truth_mode))
            df["prediction_label"] = df["actionability_v3"].map(lambda value: prediction_label(value, prediction_mode))

            included = df.loc[~df["truth_label"].eq("exclude")].copy()
            excluded_rows = int(df["truth_label"].eq("exclude").sum())

            tp = int(((included["truth_label"] == "positive") & (included["prediction_label"] == "positive")).sum())
            fp = int(((included["truth_label"] == "negative") & (included["prediction_label"] == "positive")).sum())
            fn = int(((included["truth_label"] == "positive") & (included["prediction_label"] == "negative")).sum())
            tn = int(((included["truth_label"] == "negative") & (included["prediction_label"] == "negative")).sum())

            precision = safe_metric(tp, tp + fp)
            recall = safe_metric(tp, tp + fn)
            f1 = safe_metric(2 * precision * recall, precision + recall) if (precision + recall) > 0 else 0.0

            summary_rows.append(
                {
                    "truth_mode": truth_mode,
                    "prediction_mode": prediction_mode,
                    "tp": tp,
                    "fp": fp,
                    "fn": fn,
                    "tn": tn,
                    "precision": precision,
                    "recall": recall,
                    "f1": round(f1, 6),
                    "excluded_rows": excluded_rows,
                }
            )
            confusion_rows.append(
                {
                    "truth_mode": truth_mode,
                    "prediction_mode": prediction_mode,
                    "tp": tp,
                    "fp": fp,
                    "fn": fn,
                    "tn": tn,
                    "excluded_rows": excluded_rows,
                }
            )

            errors = included.loc[
                (
                    (included["truth_label"] == "positive") & (included["prediction_label"] == "negative")
                )
                | (
                    (included["truth_label"] == "negative") & (included["prediction_label"] == "positive")
                )
            ].copy()
            if not errors.empty:
                errors["error_type"] = errors.apply(
                    lambda row: "fn" if row["truth_label"] == "positive" else "fp",
                    axis=1,
                )
                errors["truth_mode"] = truth_mode
                errors["prediction_mode"] = prediction_mode
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

    summary_df.to_csv(share_dir / "critical_actionability_f1_summary.csv", index=False, encoding="utf-8-sig")
    confusion_df.to_csv(share_dir / "critical_actionability_confusion.csv", index=False, encoding="utf-8-sig")
    errors_df.to_csv(share_dir / "critical_actionability_case_errors.csv", index=False, encoding="utf-8-sig")

    print(f"critical_actionability_eval_rows={len(joined)}")


if __name__ == "__main__":
    main()
