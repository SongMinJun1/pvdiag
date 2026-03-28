#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from build_truth_review_copyback_apply_v1 import build_note_merged

KEY_COLS = ["site", "panel_id", "strict_trigger_date"]
SAFE_ROW_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "candidate_validity_proposed",
    "date_judgement_proposed",
    "note_proposed",
    "review_owner",
    "review_status",
    "vendor_reply_class",
    "vendor_fault_family",
    "actionability_v3",
    "apply_path",
]
GATE_ROW_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "candidate_validity_proposed",
    "date_judgement_proposed",
    "note_proposed",
    "review_owner",
    "review_status",
    "vendor_reply_class",
    "vendor_fault_family",
    "actionability_v3",
    "current_strict_truth_label",
    "proposed_strict_truth_label",
    "gate_reason",
    "evidence_summary_ko",
    "review_question_ko",
    "recommended_sources_ko",
]
SUMMARY_COLS = [
    "safe_same_label_case_count",
    "gate_review_case_count",
    "canonical_row_count",
    "safe7_proposed_row_count",
    "current_strict_maintenance_f1",
    "safe7_strict_maintenance_f1",
    "current_strict_operational_f1",
    "safe7_strict_operational_f1",
    "current_lenient_maintenance_f1",
    "safe7_lenient_maintenance_f1",
    "current_lenient_operational_f1",
    "safe7_lenient_operational_f1",
    "summary_recommendation",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Package the preferred safe truth-seed promotion path without overwriting canonical truth."
    )
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


def normalize_date(value: object) -> str:
    text = normalize_text(value)
    return text[:10] if len(text) >= 10 else text


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def ensure_unique(df: pd.DataFrame, name: str) -> pd.DataFrame:
    dupes = df.loc[df.duplicated(subset=KEY_COLS, keep=False), KEY_COLS]
    if not dupes.empty:
        raise SystemExit(f"{name} has duplicate rows on {KEY_COLS}")
    return df


def key_tuple_from_row(row: pd.Series) -> tuple[str, str, str]:
    return (
        normalize_text(row["site"]),
        normalize_text(row["panel_id"]),
        normalize_date(row["strict_trigger_date"]),
    )


def normalize_key_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["site", "panel_id"]:
        df[col] = df[col].map(normalize_text)
    df["strict_trigger_date"] = df["strict_trigger_date"].map(normalize_date)
    return df


def load_safe_rows(root: Path) -> pd.DataFrame:
    safe_df = read_csv(root / "_share" / "truth_seed_safe_apply_rows_v1.csv")
    ensure_columns(
        safe_df,
        [
            *KEY_COLS,
            "candidate_validity_proposed",
            "date_judgement_proposed",
            "note_proposed",
            "review_owner",
            "review_status",
            "vendor_reply_class",
            "vendor_fault_family",
            "actionability_v3",
            "change_class",
        ],
        "truth_seed_safe_apply_rows_v1.csv",
    )
    safe_df = normalize_key_columns(safe_df)
    for col in [
        "candidate_validity_proposed",
        "date_judgement_proposed",
        "note_proposed",
        "review_owner",
        "review_status",
        "vendor_reply_class",
        "vendor_fault_family",
        "actionability_v3",
        "change_class",
    ]:
        safe_df[col] = safe_df[col].map(normalize_text)
    safe_df = ensure_unique(safe_df, "truth_seed_safe_apply_rows_v1.csv")
    safe_df["apply_path"] = "safe_same_label_promotion"
    return safe_df


def load_gate_rows(root: Path) -> pd.DataFrame:
    gate_df = read_csv(root / "_share" / "truth_seed_gate_review_rows_v1.csv")
    ensure_columns(
        gate_df,
        [
            *KEY_COLS,
            "candidate_validity_proposed",
            "date_judgement_proposed",
            "note_proposed",
            "review_owner",
            "review_status",
            "vendor_reply_class",
            "vendor_fault_family",
            "actionability_v3",
            "current_strict_truth_label",
            "proposed_strict_truth_label",
            "gate_reason",
        ],
        "truth_seed_gate_review_rows_v1.csv",
    )
    gate_df = normalize_key_columns(gate_df)
    for col in [
        "candidate_validity_proposed",
        "date_judgement_proposed",
        "note_proposed",
        "review_owner",
        "review_status",
        "vendor_reply_class",
        "vendor_fault_family",
        "actionability_v3",
        "current_strict_truth_label",
        "proposed_strict_truth_label",
        "gate_reason",
    ]:
        gate_df[col] = gate_df[col].map(normalize_text)
    return ensure_unique(gate_df, "truth_seed_gate_review_rows_v1.csv")


def load_evidence_pack(root: Path) -> pd.DataFrame:
    evidence_path = root / "_share" / "truth_review_evidence_pack_v1.csv"
    if not evidence_path.exists():
        return pd.DataFrame(columns=[*KEY_COLS, "evidence_summary_ko", "review_question_ko", "recommended_sources_ko"])
    evidence_df = read_csv(evidence_path)
    ensure_columns(
        evidence_df,
        [*KEY_COLS, "evidence_summary_ko", "review_question_ko", "recommended_sources_ko"],
        "truth_review_evidence_pack_v1.csv",
    )
    evidence_df = normalize_key_columns(evidence_df)
    for col in ["evidence_summary_ko", "review_question_ko", "recommended_sources_ko"]:
        evidence_df[col] = evidence_df[col].map(normalize_text)
    evidence_df = (
        evidence_df.loc[:, [*KEY_COLS, "evidence_summary_ko", "review_question_ko", "recommended_sources_ko"]]
        .drop_duplicates(subset=KEY_COLS)
        .reset_index(drop=True)
    )
    return evidence_df


def build_safe7_proposed(canonical_df: pd.DataFrame, safe_df: pd.DataFrame) -> pd.DataFrame:
    proposed_df = canonical_df.copy()
    key_to_indices: dict[tuple[str, str, str], list[int]] = {}
    for idx, row in proposed_df.loc[:, KEY_COLS].iterrows():
        key_to_indices.setdefault(tuple(row), []).append(idx)

    for _, safe_row in safe_df.iterrows():
        key = key_tuple_from_row(safe_row)
        matched_indices = key_to_indices.get(key, [])
        if not matched_indices:
            raise SystemExit(f"safe row missing from canonical universe: {key}")

        candidate_validity_proposed = normalize_text(safe_row["candidate_validity_proposed"])
        date_judgement_proposed = normalize_text(safe_row["date_judgement_proposed"])
        note_proposed = normalize_text(safe_row["note_proposed"])
        current_note = normalize_text(proposed_df.loc[matched_indices[0], "note"])

        if candidate_validity_proposed:
            proposed_df.loc[matched_indices, "candidate_validity"] = candidate_validity_proposed
        if date_judgement_proposed:
            proposed_df.loc[matched_indices, "date_judgement"] = date_judgement_proposed
        proposed_df.loc[matched_indices, "note"] = build_note_merged(
            note_current=current_note,
            note_proposed=note_proposed,
        )

    return proposed_df


def lookup_metric(metric_df: pd.DataFrame, scenario: str, truth_mode: str, prediction_mode: str) -> float:
    row = metric_df.loc[
        metric_df["scenario"].eq(scenario)
        & metric_df["truth_mode"].eq(truth_mode)
        & metric_df["prediction_mode"].eq(prediction_mode)
        & metric_df["source_split"].eq("overall")
    ]
    if row.empty:
        raise SystemExit(
            f"missing scenario metric for scenario={scenario} truth_mode={truth_mode} prediction_mode={prediction_mode}"
        )
    return float(row.iloc[0]["f1"])


def build_summary(canonical_row_count: int, safe7_proposed_row_count: int, safe_df: pd.DataFrame, gate_df: pd.DataFrame, metric_df: pd.DataFrame) -> pd.DataFrame:
    current_strict_maintenance_f1 = lookup_metric(metric_df, "current_canonical", "strict", "maintenance")
    safe7_strict_maintenance_f1 = lookup_metric(metric_df, "safe_same_label_only", "strict", "maintenance")
    current_strict_operational_f1 = lookup_metric(metric_df, "current_canonical", "strict", "operational")
    safe7_strict_operational_f1 = lookup_metric(metric_df, "safe_same_label_only", "strict", "operational")
    current_lenient_maintenance_f1 = lookup_metric(metric_df, "current_canonical", "lenient", "maintenance")
    safe7_lenient_maintenance_f1 = lookup_metric(metric_df, "safe_same_label_only", "lenient", "maintenance")
    current_lenient_operational_f1 = lookup_metric(metric_df, "current_canonical", "lenient", "operational")
    safe7_lenient_operational_f1 = lookup_metric(metric_df, "safe_same_label_only", "lenient", "operational")

    current_values = [
        current_strict_maintenance_f1,
        current_strict_operational_f1,
        current_lenient_maintenance_f1,
        current_lenient_operational_f1,
    ]
    safe_values = [
        safe7_strict_maintenance_f1,
        safe7_strict_operational_f1,
        safe7_lenient_maintenance_f1,
        safe7_lenient_operational_f1,
    ]
    summary_recommendation = (
        "promote_safe7_now_and_review_gate3"
        if all(safe >= current for current, safe in zip(current_values, safe_values))
        else "hold_all_until_gate_review"
    )

    return pd.DataFrame(
        [
            {
                "safe_same_label_case_count": int(len(safe_df)),
                "gate_review_case_count": int(len(gate_df)),
                "canonical_row_count": int(canonical_row_count),
                "safe7_proposed_row_count": int(safe7_proposed_row_count),
                "current_strict_maintenance_f1": current_strict_maintenance_f1,
                "safe7_strict_maintenance_f1": safe7_strict_maintenance_f1,
                "current_strict_operational_f1": current_strict_operational_f1,
                "safe7_strict_operational_f1": safe7_strict_operational_f1,
                "current_lenient_maintenance_f1": current_lenient_maintenance_f1,
                "safe7_lenient_maintenance_f1": safe7_lenient_maintenance_f1,
                "current_lenient_operational_f1": current_lenient_operational_f1,
                "safe7_lenient_operational_f1": safe7_lenient_operational_f1,
                "summary_recommendation": summary_recommendation,
            }
        ],
        columns=SUMMARY_COLS,
    )


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    canonical_df = read_csv(root / "_share" / "panel_date_reaudit_working.csv")
    canonical_df = normalize_key_columns(canonical_df)
    for col in ["candidate_validity", "date_judgement", "note"]:
        if col not in canonical_df.columns:
            canonical_df[col] = ""
        canonical_df[col] = canonical_df[col].map(normalize_text)
    canonical_df = ensure_unique(canonical_df, "panel_date_reaudit_working.csv")

    safe_df = load_safe_rows(root)
    gate_df = load_gate_rows(root)
    evidence_df = load_evidence_pack(root)
    metric_df = read_csv(root / "_share" / "truth_seed_promotion_scenarios_summary_v1.csv")
    ensure_columns(
        metric_df,
        ["scenario", "truth_mode", "prediction_mode", "source_split", "f1"],
        "truth_seed_promotion_scenarios_summary_v1.csv",
    )
    metric_df = normalize_key_columns(metric_df) if set(KEY_COLS).issubset(metric_df.columns) else metric_df
    for col in ["scenario", "truth_mode", "prediction_mode", "source_split"]:
        metric_df[col] = metric_df[col].map(normalize_text)

    safe7_proposed_df = build_safe7_proposed(canonical_df=canonical_df, safe_df=safe_df)
    safe_copyback_df = safe_df.loc[:, SAFE_ROW_COLS].sort_values(KEY_COLS).reset_index(drop=True)
    gate_packet_df = (
        gate_df.merge(evidence_df, on=KEY_COLS, how="left")
        .fillna("")
        .loc[:, GATE_ROW_COLS]
        .sort_values(KEY_COLS)
        .reset_index(drop=True)
    )
    summary_df = build_summary(
        canonical_row_count=len(canonical_df),
        safe7_proposed_row_count=len(safe7_proposed_df),
        safe_df=safe_df,
        gate_df=gate_df,
        metric_df=metric_df,
    )

    out_dir = root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe7_proposed_df.to_csv(out_dir / "panel_date_reaudit_working_safe7_proposed_v1.csv", index=False, encoding="utf-8-sig")
    safe_copyback_df.to_csv(out_dir / "truth_seed_safe7_copyback_rows_v1.csv", index=False, encoding="utf-8-sig")
    gate_packet_df.to_csv(out_dir / "truth_seed_gate3_review_packet_v1.csv", index=False, encoding="utf-8-sig")
    summary_df.to_csv(out_dir / "truth_seed_safe_promotion_summary_v1.csv", index=False, encoding="utf-8-sig")

    print(f"truth_seed_safe7_copyback_rows_v1={len(safe_copyback_df)}")


if __name__ == "__main__":
    main()
