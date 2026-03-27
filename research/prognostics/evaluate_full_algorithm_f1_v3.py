#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

KEY_COLS = ["site", "panel_id", "strict_trigger_date"]
TRUTH_MODES = ("strict", "lenient")
PREDICTION_MODES = ("maintenance", "operational")
SOURCE_SPLITS = ("overall", "manual_truth", "vendor_truth")
REAUDIT_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "candidate_validity",
    "onset_confidence",
    "reason_summary",
    "review_priority",
    "vendor_reply_class",
    "vendor_fault_family",
    "note",
]
VENDOR_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "vendor_reply_class",
    "vendor_fault_family",
    "vendor_note",
]
ACTIONABILITY_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "actionability_v3",
]
SUMMARY_COLS = [
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
    "primary_coverage",
    "effective_coverage",
]
CONFUSION_COLS = [
    "truth_mode",
    "prediction_mode",
    "source_split",
    "tp",
    "fp",
    "fn",
    "tn",
    "excluded_rows",
    "scored_rows",
    "primary_coverage",
    "effective_coverage",
]
ERROR_COLS = [
    "truth_mode",
    "prediction_mode",
    "source_split",
    "site",
    "panel_id",
    "strict_trigger_date",
    "truth_source",
    "truth_label",
    "actionability_v3",
    "derived_actionability_v3",
    "final_actionability_v3",
    "prediction_label",
    "error_type",
    "prediction_source",
    "parsed_strict_method",
    "parsed_shadow_frac",
    "parsed_group_off_frac",
    "parsed_recovery_reset",
    "candidate_validity",
    "vendor_reply_class",
    "vendor_fault_family",
    "review_priority",
    "note",
]
VALID_CANDIDATE_VALIDITY = {
    "true_positive",
    "group_side",
    "false_positive",
    "needs_more_info",
    "",
}
STRICT_VENDOR_POSITIVE = {"field_confirmed_positive", "vendor_pattern_positive"}
STRICT_VENDOR_NEGATIVE = {"vendor_rejected"}
LENIENT_VENDOR_POSITIVE = {
    "field_confirmed_positive",
    "vendor_pattern_positive",
    "vendor_likely_positive",
}
LENIENT_VENDOR_NEGATIVE = {"vendor_rejected"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate full strict-case algorithm F1 with hybrid truth and conservative confirmed-fault fallback."
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


def to_float(value: object) -> float | None:
    text = normalize_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def safe_metric(numer: int | float, denom: int | float) -> float:
    if denom <= 0:
        return 0.0
    return round(float(numer / denom), 6)


def coalesce_text(left: object, right: object) -> str:
    left_text = normalize_text(left)
    if left_text:
        return left_text
    return normalize_text(right)


def dedupe(df: pd.DataFrame, name: str, cols: list[str]) -> pd.DataFrame:
    dupes = df.loc[df.duplicated(subset=cols, keep=False), cols]
    if not dupes.empty:
        raise SystemExit(f"{name} has duplicate rows on {cols}")
    return df


def manual_truth_label(candidate_validity: object) -> str:
    value = normalize_text(candidate_validity)
    if value in {"true_positive", "group_side"}:
        return "positive"
    if value == "false_positive":
        return "negative"
    return "exclude"


def vendor_truth_label(vendor_reply_class: object, truth_mode: str) -> str:
    value = normalize_text(vendor_reply_class)
    if truth_mode == "strict":
        if value in STRICT_VENDOR_POSITIVE:
            return "positive"
        if value in STRICT_VENDOR_NEGATIVE:
            return "negative"
        return "exclude"
    if truth_mode == "lenient":
        if value in LENIENT_VENDOR_POSITIVE:
            return "positive"
        if value in LENIENT_VENDOR_NEGATIVE:
            return "negative"
        return "exclude"
    raise ValueError(truth_mode)


def resolve_truth_source(candidate_validity: object, vendor_reply_class: object) -> str:
    if normalize_text(candidate_validity):
        return "manual_truth"
    if normalize_text(vendor_reply_class):
        return "vendor_truth"
    return ""


def hybrid_truth_label(candidate_validity: object, vendor_reply_class: object, truth_mode: str) -> str:
    truth_source = resolve_truth_source(candidate_validity, vendor_reply_class)
    if truth_source == "manual_truth":
        return manual_truth_label(candidate_validity)
    if truth_source == "vendor_truth":
        return vendor_truth_label(vendor_reply_class, truth_mode)
    return "exclude"


def prediction_label(final_actionability_v3: object, prediction_mode: str) -> str:
    value = normalize_text(final_actionability_v3)
    if prediction_mode == "maintenance":
        return "positive" if value == "maintenance_candidate" else "negative"
    if prediction_mode == "operational":
        return (
            "positive"
            if value in {"maintenance_candidate", "common_cause_review", "singleton_review"}
            else "negative"
        )
    raise ValueError(prediction_mode)


def source_split_mask(df: pd.DataFrame, source_split: str) -> pd.Series:
    if source_split == "overall":
        return pd.Series(True, index=df.index)
    if source_split == "manual_truth":
        return df["truth_source"].eq("manual_truth")
    if source_split == "vendor_truth":
        return df["truth_source"].eq("vendor_truth")
    raise ValueError(source_split)


def parse_reason_summary(reason_summary: object) -> dict[str, object]:
    tokens: dict[str, str] = {}
    text = normalize_text(reason_summary)
    if text:
        for part in text.split("|"):
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            tokens[normalize_text(key)] = normalize_text(value)
    return {
        "parsed_strict_method": tokens.get("strict_method", ""),
        "parsed_shadow_frac": to_float(tokens.get("shadow_frac", "")),
        "parsed_group_off_frac": to_float(tokens.get("group_off_frac", "")),
        "parsed_recovery_reset": tokens.get("recovery_reset", ""),
    }


def derive_actionability(row: pd.Series) -> tuple[str, str]:
    if normalize_text(row["actionability_v3"]):
        return "", "primary_actionability_v3"

    strict_method = normalize_text(row["parsed_strict_method"])
    onset_confidence = normalize_text(row["onset_confidence"])
    recovery_reset = normalize_text(row["parsed_recovery_reset"])
    shadow_frac = row["parsed_shadow_frac"]
    group_off_frac = row["parsed_group_off_frac"]
    shadow_known = shadow_frac is not None
    group_known = group_off_frac is not None
    clean_confirmed = (
        strict_method == "confirmed_fault_flag"
        and onset_confidence in {"high", "medium"}
        and recovery_reset == "no"
        and shadow_known
        and group_known
        and shadow_frac <= 0.20
        and group_off_frac <= 0.20
    )
    confounded_confirmed = (
        strict_method == "confirmed_fault_flag"
        and (
            recovery_reset == "yes"
            or (shadow_known and shadow_frac > 0.20)
            or (group_known and group_off_frac > 0.20)
        )
    )
    if clean_confirmed:
        return "singleton_review", "confirmed_fault_clean"
    if confounded_confirmed:
        return "monitor_only", "confirmed_fault_confounded"
    if strict_method == "critical_fault_flag":
        return "", "unmatched_critical_missing_v3"
    return "", "no_fallback_rule"


def build_joined(root: Path) -> pd.DataFrame:
    reaudit_df = read_csv(root / "_share" / "panel_date_reaudit_working.csv")
    vendor_df = read_csv(root / "_share" / "vendor_reply_adjudication_latest.csv")
    actionability_df = read_csv(root / "_share" / "critical_actionability_shadow_v3_latest.csv")

    ensure_columns(reaudit_df, REAUDIT_REQUIRED_COLS, "panel_date_reaudit_working.csv")
    ensure_columns(vendor_df, VENDOR_REQUIRED_COLS, "vendor_reply_adjudication_latest.csv")
    ensure_columns(actionability_df, ACTIONABILITY_REQUIRED_COLS, "critical_actionability_shadow_v3_latest.csv")

    for df in [reaudit_df, vendor_df, actionability_df]:
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

    invalid_values = sorted(set(reaudit_df["candidate_validity"]) - VALID_CANDIDATE_VALIDITY)
    if invalid_values:
        raise SystemExit(f"panel_date_reaudit_working.csv has invalid candidate_validity values: {invalid_values}")

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
    joined["primary_prediction_available_flag"] = joined["actionability_v3"].ne("").astype(int)
    joined["effective_prediction_available_flag"] = joined["final_actionability_v3"].ne("").astype(int)
    joined["parsed_shadow_frac"] = joined["parsed_shadow_frac"].astype(float)
    joined["parsed_group_off_frac"] = joined["parsed_group_off_frac"].astype(float)
    return joined


def evaluate(joined: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary_rows: list[dict[str, object]] = []
    confusion_rows: list[dict[str, object]] = []
    error_rows: list[dict[str, object]] = []

    for truth_mode in TRUTH_MODES:
        base = joined.copy()
        base["truth_label"] = base.apply(
            lambda row: hybrid_truth_label(row["candidate_validity"], row["vendor_reply_class"], truth_mode),
            axis=1,
        )

        for prediction_mode in PREDICTION_MODES:
            base["prediction_label"] = base["final_actionability_v3"].map(
                lambda value: prediction_label(value, prediction_mode)
            )

            for source_split in SOURCE_SPLITS:
                subset = base.loc[source_split_mask(base, source_split)].copy()
                excluded_rows = int(subset["truth_label"].eq("exclude").sum())
                scored = subset.loc[subset["truth_label"].ne("exclude")].copy()
                scored_rows = len(scored)
                primary_coverage = safe_metric(int(scored["primary_prediction_available_flag"].sum()), scored_rows)
                effective_coverage = safe_metric(int(scored["effective_prediction_available_flag"].sum()), scored_rows)

                tp = int(((scored["truth_label"] == "positive") & (scored["prediction_label"] == "positive")).sum())
                fp = int(((scored["truth_label"] == "negative") & (scored["prediction_label"] == "positive")).sum())
                fn = int(((scored["truth_label"] == "positive") & (scored["prediction_label"] == "negative")).sum())
                tn = int(((scored["truth_label"] == "negative") & (scored["prediction_label"] == "negative")).sum())

                precision = safe_metric(tp, tp + fp)
                recall = safe_metric(tp, tp + fn)
                f1 = safe_metric(2 * precision * recall, precision + recall) if (precision + recall) > 0 else 0.0

                summary_rows.append(
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
                        "scored_rows": scored_rows,
                        "primary_coverage": primary_coverage,
                        "effective_coverage": effective_coverage,
                    }
                )
                confusion_rows.append(
                    {
                        "truth_mode": truth_mode,
                        "prediction_mode": prediction_mode,
                        "source_split": source_split,
                        "tp": tp,
                        "fp": fp,
                        "fn": fn,
                        "tn": tn,
                        "excluded_rows": excluded_rows,
                        "scored_rows": scored_rows,
                        "primary_coverage": primary_coverage,
                        "effective_coverage": effective_coverage,
                    }
                )

                errors = scored.loc[
                    scored["truth_label"].ne(scored["prediction_label"]),
                    [
                        "site",
                        "panel_id",
                        "strict_trigger_date",
                        "truth_source",
                        "truth_label",
                        "actionability_v3",
                        "derived_actionability_v3",
                        "final_actionability_v3",
                        "prediction_label",
                        "prediction_source",
                        "parsed_strict_method",
                        "parsed_shadow_frac",
                        "parsed_group_off_frac",
                        "parsed_recovery_reset",
                        "candidate_validity",
                        "vendor_reply_class",
                        "vendor_fault_family",
                        "review_priority",
                        "note",
                    ],
                ].copy()
                errors["error_type"] = errors.apply(
                    lambda row: "fp" if row["prediction_label"] == "positive" else "fn",
                    axis=1,
                )
                errors.insert(0, "source_split", source_split)
                errors.insert(0, "prediction_mode", prediction_mode)
                errors.insert(0, "truth_mode", truth_mode)
                error_rows.extend(errors.to_dict(orient="records"))

    summary_df = pd.DataFrame(summary_rows, columns=SUMMARY_COLS)
    confusion_df = pd.DataFrame(confusion_rows, columns=CONFUSION_COLS)
    error_df = pd.DataFrame(error_rows, columns=ERROR_COLS)
    return summary_df, confusion_df, error_df


def main() -> None:
    args = parse_args()
    joined = build_joined(args.root)
    summary_df, confusion_df, error_df = evaluate(joined)

    out_dir = args.root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(out_dir / "full_algorithm_f1_summary_v3.csv", index=False, encoding="utf-8-sig")
    confusion_df.to_csv(out_dir / "full_algorithm_confusion_v3.csv", index=False, encoding="utf-8-sig")
    error_df.to_csv(out_dir / "full_algorithm_case_errors_v3.csv", index=False, encoding="utf-8-sig")
    print(f"full_algorithm_eval_rows_v3={len(joined)}")


if __name__ == "__main__":
    main()
