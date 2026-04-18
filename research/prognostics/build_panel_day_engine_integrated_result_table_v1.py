#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]

VERDICT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
EVIDENCE_PACK_NAME = "panel_day_engine_gpvs_evidence_pack_v1.csv"
HEURISTIC_NAME = "panel_day_engine_cause_candidate_heuristics_v1.csv"

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
HEURISTIC_REQUIRED_COLS = [
    "site",
    "panel_id",
    "원인후보_top1_ko",
    "원인후보_top2_ko",
    "원인후보_top3_ko",
]

TABLE_COLS = [
    "site",
    "panel_id",
    "패널고장여부_ko",
    "사건유형_ko",
    "최종고장양상_ko",
    "커널로그_원인군_ko",
    "1순위_의심원인_ko",
    "2순위_의심원인_ko",
    "3순위_의심원인_ko",
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


def row_key(site: object, panel_id: object) -> tuple[str, str]:
    return normalize_text(site), normalize_text(panel_id)


def validate_unique_keys(df: pd.DataFrame, name: str) -> None:
    if df[["site", "panel_id"]].duplicated().any():
        dup = df.loc[df[["site", "panel_id"]].duplicated(keep=False), ["site", "panel_id"]]
        raise SystemExit(f"{name} must be unique by (site, panel_id): {dup.to_dict(orient='records')[:5]}")


DISPLAY_HEURISTIC_NAME_MAP = {
    "다이오드·서브스트링형": "다이오드·국소 회로 이상형",
    "접속·부분개방형": "접촉 끊김 형",
    "센서·피드백형": "장치 측정 이상형",
    "제어응답형": "장치 응답 이상형",
    "전력변환부형": "전력변환부 이상형",
    "외부계통교란형": "외부 전원 흔들림형",
}


def display_heuristic_name(raw_label: str) -> str:
    normalized = normalize_text(raw_label)
    return DISPLAY_HEURISTIC_NAME_MAP.get(normalized, normalized)


def build_integrated_rows(
    verdict_df: pd.DataFrame,
    heuristic_df: pd.DataFrame,
) -> pd.DataFrame:
    heuristic_lookup = {
        row_key(row["site"], row["panel_id"]): {
            column: normalize_text(value) for column, value in row.items()
        }
        for row in heuristic_df.to_dict(orient="records")
    }
    fault_keys = {
        row_key(row["site"], row["panel_id"])
        for row in verdict_df.loc[verdict_df["패널고장여부_ko"].map(normalize_text).eq("고장")].to_dict(orient="records")
    }
    heuristic_keys = set(heuristic_lookup)
    missing_fault_keys = sorted(fault_keys - heuristic_keys)
    unexpected_heuristic_keys = sorted(heuristic_keys - fault_keys)
    if missing_fault_keys:
        raise SystemExit(f"{HEURISTIC_NAME} missing fault panel rows: {missing_fault_keys[:5]}")
    if unexpected_heuristic_keys:
        raise SystemExit(f"{HEURISTIC_NAME} contains non-fault panel rows: {unexpected_heuristic_keys[:5]}")

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
            heuristic_row = heuristic_lookup[key]
            top1 = display_heuristic_name(heuristic_row["원인후보_top1_ko"])
            top2 = display_heuristic_name(heuristic_row["원인후보_top2_ko"])
            top3 = display_heuristic_name(heuristic_row["원인후보_top3_ko"])
        else:
            top1 = ""
            top2 = ""
            top3 = ""

        rows.append(
            {
                "site": site,
                "panel_id": panel_id,
                "패널고장여부_ko": panel_fault_status,
                "사건유형_ko": event_type,
                "최종고장양상_ko": terminal_pattern,
                "커널로그_원인군_ko": kernel_family,
                "1순위_의심원인_ko": top1,
                "2순위_의심원인_ko": top2,
                "3순위_의심원인_ko": top3,
            }
        )

    integrated_df = pd.DataFrame(rows)
    integrated_df["__fault_sort"] = integrated_df["패널고장여부_ko"].map(lambda value: 0 if normalize_text(value) == "고장" else 1)
    integrated_df = integrated_df.sort_values(["__fault_sort", "site", "panel_id"], ascending=[True, True, True])
    return integrated_df.drop(columns="__fault_sort").reset_index(drop=True).reindex(columns=TABLE_COLS)


def build_summary(table_df: pd.DataFrame, evidence_df: pd.DataFrame) -> pd.DataFrame:
    total_count = int(len(table_df))
    fault_count = int(table_df["패널고장여부_ko"].map(normalize_text).eq("고장").sum())
    non_fault_or_unresolved_count = total_count - fault_count
    gpvs_recommendation = evidence_df["GPVS_최종사용권고_ko"].map(normalize_text)
    core_count = int(gpvs_recommendation.eq("핵심참조").sum())
    auxiliary_count = int(gpvs_recommendation.eq("보조참조").sum())
    gpvs_not_used_count = int(non_fault_or_unresolved_count)

    row = {
        "total_panel_count": total_count,
        "fault_panel_count": fault_count,
        "non_fault_or_unresolved_count": non_fault_or_unresolved_count,
        "gpvs_core_reference_count": core_count,
        "gpvs_auxiliary_reference_count": auxiliary_count,
        "gpvs_not_used_count": gpvs_not_used_count,
        "note_ko": (
            "이 표는 최종 front-facing table이며 panel multiaxis verdict를 primary로 읽는다. "
            "kernel-log 원인군과 heuristic suspected-cause ranking만 남기고, GPVS internal/external/evidence detail은 evidence pack에만 유지한다. "
            "display friendliness를 위해 여섯 개 heuristic label만 표 안에서 표시용으로 바꿔 적고, raw heuristic output은 그대로 둔다."
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
    heuristic_df = read_csv(share_dir / HEURISTIC_NAME)
    ensure_columns(verdict_df, VERDICT_REQUIRED_COLS, VERDICT_NAME)
    ensure_columns(evidence_df, EVIDENCE_REQUIRED_COLS, EVIDENCE_PACK_NAME)
    ensure_columns(heuristic_df, HEURISTIC_REQUIRED_COLS, HEURISTIC_NAME)
    validate_unique_keys(verdict_df, VERDICT_NAME)
    validate_unique_keys(evidence_df, EVIDENCE_PACK_NAME)
    validate_unique_keys(heuristic_df, HEURISTIC_NAME)

    table_df = build_integrated_rows(verdict_df, heuristic_df)
    summary_df = build_summary(table_df, evidence_df)
    write_outputs(root, table_df, summary_df)


if __name__ == "__main__":
    main()
