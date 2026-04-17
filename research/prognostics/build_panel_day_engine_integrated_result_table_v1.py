#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]

VERDICT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
EVIDENCE_PACK_NAME = "panel_day_engine_gpvs_evidence_pack_v1.csv"

OUTPUT_TABLE_NAME = "panel_day_engine_integrated_result_table_v1.csv"
OUTPUT_SUMMARY_NAME = "panel_day_engine_integrated_result_summary_v1.csv"

VERDICT_REQUIRED_COLS = [
    "site",
    "panel_id",
    "패널고장여부_ko",
    "사건유형_ko",
    "최종고장양상_ko",
    "커널로그_원인군_ko",
]
EVIDENCE_REQUIRED_COLS = [
    "site",
    "panel_id",
    "GPVS_최종사용권고_ko",
]

INTERNAL_GPVS_COL_CANDIDATES = ["GPVS_내부참고유형_ko", "GPVS_참고유형_ko"]
EXTERNAL_GPVS_COL_CANDIDATES = ["GPVS_외부참조패턴_ko", "GPVS_외부참조시나리오명_ko"]

TABLE_COLS = [
    "site",
    "panel_id",
    "패널고장여부_ko",
    "사건유형_ko",
    "최종고장양상_ko",
    "커널로그_원인군_ko",
    "GPVS_내부참고유형_ko",
    "GPVS_외부참조패턴_ko",
    "GPVS_최종사용권고_ko",
    "대표판정요약_ko",
    "판정근거요약_ko",
]

SUMMARY_COLS = [
    "total_panel_count",
    "fault_panel_count",
    "non_fault_or_unresolved_count",
    "gpvs_core_reference_count",
    "gpvs_auxiliary_reference_count",
    "gpvs_not_used_count",
    "note_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a front-facing integrated panel result table from panel verdict and GPVS evidence outputs."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root. Defaults to the project root.",
    )
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def first_existing_column(df: pd.DataFrame, candidates: list[str], frame_name: str) -> str:
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    raise SystemExit(f"{frame_name} missing any of columns: {candidates}")


def row_key(site: object, panel_id: object) -> tuple[str, str]:
    return normalize_text(site), normalize_text(panel_id)


def validate_unique_keys(df: pd.DataFrame, name: str) -> None:
    if df[["site", "panel_id"]].duplicated().any():
        dup = df.loc[df[["site", "panel_id"]].duplicated(keep=False), ["site", "panel_id"]]
        raise SystemExit(f"{name} must be unique by (site, panel_id): {dup.to_dict(orient='records')[:5]}")


def summarize_fault_row(event_type: str, terminal_pattern: str, kernel_family: str) -> str:
    kernel_text = kernel_family or "불충분"
    return f"{event_type}으로 해석되며 최종고장양상은 {terminal_pattern}이고 커널로그 원인군은 {kernel_text}이다."


def summarize_non_fault_row(panel_fault_status: str, event_type: str) -> str:
    if panel_fault_status == "비고장":
        if event_type == "공통원인 이벤트":
            return "현재는 공통원인 이벤트로 분류되며 개별 패널 고장으로 보지 않는다."
        return "현재는 비고장으로 분류되며 개별 패널 고장으로 해석하지 않는다."
    if event_type == "반복 이상":
        return "현재는 반복 이상으로 관찰 중이며 확정 고장 패널로 보지 않는다."
    if event_type == "불충분":
        return "현재는 미확정 상태로 남아 있어 추가 해석이 필요하다."
    if event_type:
        return f"현재는 {event_type} 상태로 관찰 중이며 추가 확인이 필요하다."
    return "현재는 미확정 상태로 남아 있으며 추가 확인이 필요하다."


def summarize_fault_rationale(kernel_family: str, gpvs_pattern: str, gpvs_recommendation: str) -> str:
    kernel_text = kernel_family or "불충분"
    if gpvs_pattern and gpvs_recommendation:
        return f"커널로그는 {kernel_text}, GPVS는 {gpvs_pattern}을 {gpvs_recommendation}로 제시"
    return f"커널로그는 {kernel_text}로 읽고 GPVS 참조는 현재 비워 둔다"


def build_integrated_rows(
    verdict_df: pd.DataFrame,
    evidence_df: pd.DataFrame,
    internal_gpvs_col: str,
    external_gpvs_col: str,
) -> pd.DataFrame:
    evidence_lookup = {
        row_key(row["site"], row["panel_id"]): {
            column: normalize_text(value) for column, value in row.items()
        }
        for row in evidence_df.to_dict(orient="records")
    }
    fault_keys = {
        row_key(row["site"], row["panel_id"])
        for row in verdict_df.loc[verdict_df["패널고장여부_ko"].map(normalize_text).eq("고장")].to_dict(orient="records")
    }
    evidence_keys = set(evidence_lookup)
    missing_fault_keys = sorted(fault_keys - evidence_keys)
    unexpected_evidence_keys = sorted(evidence_keys - fault_keys)
    if missing_fault_keys:
        raise SystemExit(f"{EVIDENCE_PACK_NAME} missing fault panel rows: {missing_fault_keys[:5]}")
    if unexpected_evidence_keys:
        raise SystemExit(f"{EVIDENCE_PACK_NAME} contains non-fault panel rows: {unexpected_evidence_keys[:5]}")

    rows: list[dict[str, str]] = []
    for row in verdict_df.to_dict(orient="records"):
        site = normalize_text(row["site"])
        panel_id = normalize_text(row["panel_id"])
        panel_fault_status = normalize_text(row["패널고장여부_ko"])
        event_type = normalize_text(row["사건유형_ko"])
        terminal_pattern = normalize_text(row["최종고장양상_ko"])
        kernel_family = normalize_text(row["커널로그_원인군_ko"])
        key = (site, panel_id)

        if panel_fault_status == "고장":
            evidence_row = evidence_lookup[key]
            gpvs_internal = normalize_text(row.get(internal_gpvs_col)) or normalize_text(evidence_row.get("GPVS_내부판정_ko"))
            gpvs_external = normalize_text(row.get(external_gpvs_col)) or normalize_text(evidence_row.get("GPVS_외부참조패턴_ko"))
            gpvs_final = normalize_text(evidence_row.get("GPVS_최종사용권고_ko"))
            if not gpvs_final:
                raise SystemExit(f"{EVIDENCE_PACK_NAME} missing GPVS_최종사용권고_ko for {site}/{panel_id}")
            representative_summary = summarize_fault_row(event_type, terminal_pattern, kernel_family)
            rationale_summary = summarize_fault_rationale(kernel_family, gpvs_external, gpvs_final)
        else:
            gpvs_internal = ""
            gpvs_external = ""
            gpvs_final = ""
            representative_summary = summarize_non_fault_row(panel_fault_status, event_type)
            rationale_summary = ""

        rows.append(
            {
                "site": site,
                "panel_id": panel_id,
                "패널고장여부_ko": panel_fault_status,
                "사건유형_ko": event_type,
                "최종고장양상_ko": terminal_pattern,
                "커널로그_원인군_ko": kernel_family,
                "GPVS_내부참고유형_ko": gpvs_internal,
                "GPVS_외부참조패턴_ko": gpvs_external,
                "GPVS_최종사용권고_ko": gpvs_final,
                "대표판정요약_ko": representative_summary,
                "판정근거요약_ko": rationale_summary,
            }
        )

    integrated_df = pd.DataFrame(rows)
    integrated_df["__fault_sort"] = integrated_df["패널고장여부_ko"].map(lambda value: 0 if normalize_text(value) == "고장" else 1)
    integrated_df = integrated_df.sort_values(["__fault_sort", "site", "panel_id"], ascending=[True, True, True])
    return integrated_df.drop(columns="__fault_sort").reset_index(drop=True).reindex(columns=TABLE_COLS)


def build_summary(table_df: pd.DataFrame) -> pd.DataFrame:
    total_count = int(len(table_df))
    fault_count = int(table_df["패널고장여부_ko"].map(normalize_text).eq("고장").sum())
    non_fault_or_unresolved_count = total_count - fault_count
    gpvs_recommendation = table_df["GPVS_최종사용권고_ko"].map(normalize_text)
    core_count = int(gpvs_recommendation.eq("핵심참조").sum())
    auxiliary_count = int(gpvs_recommendation.eq("보조참조").sum())
    gpvs_not_used_count = int(gpvs_recommendation.isin(["", "비권장"]).sum())

    row = {
        "total_panel_count": total_count,
        "fault_panel_count": fault_count,
        "non_fault_or_unresolved_count": non_fault_or_unresolved_count,
        "gpvs_core_reference_count": core_count,
        "gpvs_auxiliary_reference_count": auxiliary_count,
        "gpvs_not_used_count": gpvs_not_used_count,
        "note_ko": (
            "이 표는 panel multiaxis verdict를 primary로 읽고, kernel-log를 직접 운영 해석 층으로, "
            "GPVS를 reference-only 보조층으로 합친 front-facing unified reading table이다. "
            "raw GPVS evidence/code/score는 evidence pack에만 남기고 여기서는 다시 노출하지 않는다."
        ),
    }
    return pd.DataFrame([row]).reindex(columns=SUMMARY_COLS)


def write_outputs(root: Path, table_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    table_df.to_csv(share_dir / OUTPUT_TABLE_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / OUTPUT_SUMMARY_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"

    verdict_df = read_csv(share_dir / VERDICT_NAME)
    evidence_df = read_csv(share_dir / EVIDENCE_PACK_NAME)
    ensure_columns(verdict_df, VERDICT_REQUIRED_COLS, VERDICT_NAME)
    ensure_columns(evidence_df, EVIDENCE_REQUIRED_COLS, EVIDENCE_PACK_NAME)
    validate_unique_keys(verdict_df, VERDICT_NAME)
    validate_unique_keys(evidence_df, EVIDENCE_PACK_NAME)

    internal_gpvs_col = first_existing_column(verdict_df, INTERNAL_GPVS_COL_CANDIDATES, VERDICT_NAME)
    external_gpvs_col = first_existing_column(verdict_df, EXTERNAL_GPVS_COL_CANDIDATES, VERDICT_NAME)

    table_df = build_integrated_rows(verdict_df, evidence_df, internal_gpvs_col, external_gpvs_col)
    summary_df = build_summary(table_df)
    write_outputs(root, table_df, summary_df)


if __name__ == "__main__":
    main()
