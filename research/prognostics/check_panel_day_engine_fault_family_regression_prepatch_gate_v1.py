#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_PACKET_INPUT = Path(
    "/private/tmp/fault_family_regression_pressure_packet_check/panel_day_engine_fault_family_regression_pressure_packet_v1.csv"
)
DETAIL_OUTPUT_NAME = "panel_day_engine_fault_family_regression_prepatch_gate_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_fault_family_regression_prepatch_gate_summary_v1.csv"
REQUIRED_BUCKET_MIN_COUNTS = {
    "non_target_hard_same_day_fault_family_seed": 5,
    "sensor_feedback_hard_same_day_ambiguity_pressure": 6,
}
REQUIRED_COUNTEREXAMPLE_BUCKETS = {
    "fault_family_boundary_pressure",
    "mlpe_ambiguous",
}
REQUIRED_COLS = [
    "packet_case_id",
    "site",
    "panel_id",
    "packet_bucket",
    "counterexample_bucket",
    "source_closure_class",
    "evidence_grade",
    "raw_top1_ko",
    "same_day_fault_like_row_count",
    "same_day_final_fault_row_count",
    "same_day_common_cause_row_count",
    "target_exact_closure_candidate_flag",
    "operator_promotion_allowed_flag",
    "engine_patch_candidate_flag",
    "expected_reading",
    "prohibited_overgeneralization",
    "regression_assertion",
]
DETAIL_COLS = [
    "gate_id",
    "severity",
    "pass_flag",
    "status",
    "observed_value",
    "requirement",
    "remediation",
]
SUMMARY_COLS = [
    "overall_status",
    "packet_rows",
    "required_gate_count",
    "failed_required_gate_count",
    "passed_required_gate_count",
    "warn_gate_count",
    "target_exact_closure_candidate_sum",
    "operator_promotion_allowed_sum",
    "engine_patch_candidate_sum",
    "required_bucket_min_counts",
    "observed_bucket_counts",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Gate BR-058 fault-family regression pressure packet before any panel engine "
            "algorithm patch discussion."
        )
    )
    parser.add_argument("--packet-input", type=Path, default=DEFAULT_PACKET_INPUT)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--allow-fail",
        action="store_true",
        help="Write gate outputs but return success even when required gates fail.",
    )
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def to_flag(value: object) -> int:
    text = normalize_text(value).lower()
    if text in {"1", "true", "t", "yes", "y"}:
        return 1
    if text in {"0", "false", "f", "no", "n", ""}:
        return 0
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0 if pd.isna(numeric) else int(float(numeric) > 0)


def to_int(value: object) -> int:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0 if pd.isna(numeric) else int(numeric)


def read_packet(path: Path) -> tuple[pd.DataFrame, list[str]]:
    if not path.exists():
        return pd.DataFrame(), REQUIRED_COLS[:]
    df = pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
    missing = [col for col in REQUIRED_COLS if col not in df.columns]
    out = df.copy()
    for col in REQUIRED_COLS:
        if col not in out.columns:
            out[col] = ""
    flag_cols = [
        "target_exact_closure_candidate_flag",
        "operator_promotion_allowed_flag",
        "engine_patch_candidate_flag",
    ]
    int_cols = [
        "same_day_fault_like_row_count",
        "same_day_final_fault_row_count",
        "same_day_common_cause_row_count",
    ]
    for col in REQUIRED_COLS:
        if col in flag_cols:
            out[col] = out[col].map(to_flag)
        elif col in int_cols:
            out[col] = out[col].map(to_int)
        else:
            out[col] = out[col].map(normalize_text)
    return out[REQUIRED_COLS], missing


def gate_row(
    gate_id: str,
    passed: bool,
    observed_value: object,
    requirement: str,
    remediation: str,
    severity: str = "required",
) -> dict[str, object]:
    if passed:
        status = "pass"
        pass_flag = 1
    elif severity == "required":
        status = "fail"
        pass_flag = 0
    else:
        status = "warn"
        pass_flag = 1
    return {
        "gate_id": gate_id,
        "severity": severity,
        "pass_flag": pass_flag,
        "status": status,
        "observed_value": normalize_text(observed_value),
        "requirement": requirement,
        "remediation": remediation,
    }


def build_detail(packet: pd.DataFrame, missing_cols: list[str], packet_exists: bool) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    row_count = len(packet)
    bucket_counts = packet["packet_bucket"].value_counts().sort_index().to_dict() if not packet.empty else {}
    counterexample_buckets = set(packet["counterexample_bucket"]) if not packet.empty else set()
    case_ids = packet["packet_case_id"].map(normalize_text).tolist() if not packet.empty else []
    target_sum = int(packet["target_exact_closure_candidate_flag"].sum()) if not packet.empty else 0
    promotion_sum = int(packet["operator_promotion_allowed_flag"].sum()) if not packet.empty else 0
    engine_sum = int(packet["engine_patch_candidate_flag"].sum()) if not packet.empty else 0
    hard_rows = int(packet["same_day_final_fault_row_count"].sum()) if not packet.empty else 0
    common_cause_rows = int(packet["same_day_common_cause_row_count"].sum()) if not packet.empty else 0

    rows.append(
        gate_row(
            "G01_packet_exists_and_non_empty",
            packet_exists and row_count > 0,
            f"exists={packet_exists}, rows={row_count}",
            "BR-058 packet must exist and contain rows.",
            "Run build_panel_day_engine_fault_family_regression_pressure_packet_v1.py first.",
        )
    )
    rows.append(
        gate_row(
            "G02_required_columns_present",
            not missing_cols,
            "|".join(missing_cols),
            "Packet must contain the required regression gate columns.",
            "Regenerate the packet with the current BR-058 builder.",
        )
    )
    for bucket, minimum in REQUIRED_BUCKET_MIN_COUNTS.items():
        observed = int(bucket_counts.get(bucket, 0))
        rows.append(
            gate_row(
                f"G03_bucket_min_count__{bucket}",
                observed >= minimum,
                observed,
                f"`{bucket}` must have at least {minimum} cases.",
                "Do not proceed to algorithm gating if the pressure bucket shrank.",
            )
        )
    rows.append(
        gate_row(
            "G04_counterexample_buckets_present",
            REQUIRED_COUNTEREXAMPLE_BUCKETS.issubset(counterexample_buckets),
            "|".join(sorted(counterexample_buckets)),
            "`fault_family_boundary_pressure` and `mlpe_ambiguous` buckets must both be present.",
            "Rebuild or re-curate the packet before any threshold discussion.",
        )
    )
    rows.append(
        gate_row(
            "G05_no_target_exact_closure_in_packet",
            target_sum == 0,
            target_sum,
            "Packet rows must not be target exact-family closure candidates.",
            "Separate target exact closure evidence into a different decision path.",
        )
    )
    rows.append(
        gate_row(
            "G06_no_operator_promotion_in_packet",
            promotion_sum == 0,
            promotion_sum,
            "Packet rows must not be direct operator promotion candidates.",
            "Keep packet rows as regression/counterexample pressure only.",
        )
    )
    rows.append(
        gate_row(
            "G07_no_engine_patch_candidate_in_packet",
            engine_sum == 0,
            engine_sum,
            "Packet rows must not be direct engine patch candidates.",
            "Open a separate safety-gated engine patch only with stronger evidence.",
        )
    )
    rows.append(
        gate_row(
            "G08_same_day_final_fault_context_present",
            hard_rows >= row_count and row_count > 0,
            hard_rows,
            "Every packet row should carry same-day final fault pressure context.",
            "Review packet input if rows without hard same-day pressure were included.",
        )
    )
    rows.append(
        gate_row(
            "G09_common_cause_not_the_packet_basis",
            common_cause_rows == 0,
            common_cause_rows,
            "This packet is fault-family/MLPE pressure, not common-cause pressure.",
            "Move common-cause rows into the common-cause counterexample path.",
        )
    )
    rows.append(
        gate_row(
            "G10_packet_case_ids_unique",
            len(case_ids) == len(set(case_ids)) and all(case_ids),
            f"ids={len(case_ids)}, unique={len(set(case_ids))}",
            "Packet case IDs must be non-empty and unique.",
            "Regenerate packet case IDs with the BR-058 builder.",
        )
    )
    text_required_cols = ["expected_reading", "prohibited_overgeneralization", "regression_assertion"]
    empty_text_count = 0
    for col in text_required_cols:
        empty_text_count += int(packet[col].map(normalize_text).eq("").sum()) if col in packet.columns else row_count
    rows.append(
        gate_row(
            "G11_regression_text_fields_present",
            empty_text_count == 0 and row_count > 0,
            empty_text_count,
            "Expected reading, prohibited overgeneralization, and assertion must be populated.",
            "Do not use rows as regression pressure without explicit interpretation text.",
        )
    )
    return pd.DataFrame(rows, columns=DETAIL_COLS)


def build_summary(detail: pd.DataFrame, packet: pd.DataFrame) -> pd.DataFrame:
    required = detail.loc[detail["severity"] == "required"].copy()
    failed_required = required.loc[required["status"] == "fail"]
    warn_rows = detail.loc[detail["status"] == "warn"]
    row = {
        "overall_status": "pass" if failed_required.empty else "fail",
        "packet_rows": len(packet),
        "required_gate_count": len(required),
        "failed_required_gate_count": len(failed_required),
        "passed_required_gate_count": int(required["pass_flag"].sum()) if not required.empty else 0,
        "warn_gate_count": len(warn_rows),
        "target_exact_closure_candidate_sum": int(packet["target_exact_closure_candidate_flag"].sum()) if not packet.empty else 0,
        "operator_promotion_allowed_sum": int(packet["operator_promotion_allowed_flag"].sum()) if not packet.empty else 0,
        "engine_patch_candidate_sum": int(packet["engine_patch_candidate_flag"].sum()) if not packet.empty else 0,
        "required_bucket_min_counts": str(REQUIRED_BUCKET_MIN_COUNTS),
        "observed_bucket_counts": str(packet["packet_bucket"].value_counts().sort_index().to_dict()) if not packet.empty else "{}",
    }
    return pd.DataFrame([row], columns=SUMMARY_COLS)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    packet_exists = args.packet_input.exists()
    packet, missing_cols = read_packet(args.packet_input)
    detail = build_detail(packet, missing_cols, packet_exists)
    summary = build_summary(detail, packet)
    detail.to_csv(args.output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    if summary.iloc[0]["overall_status"] != "pass" and not args.allow_fail:
        raise SystemExit("fault-family regression prepatch gate failed")


if __name__ == "__main__":
    main()
