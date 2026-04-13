#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

LATEST_PERF_NAME = "panel_day_engine_latest_perf_internal_share_v1.csv"
ABRUPT6_NAME = "panel_day_engine_abrupt6_symptom_map_v1.csv"
KERNEL_MAPPING_NAME = "panel_day_engine_kernellog_project_mapping_v1.csv"
GPV7_NAME = "panel_day_engine_gpv7_perf_summary_v1.csv"
PROGRESS_NAME = "panel_day_engine_project_progress_snapshot_v1.csv"
FINAL_DECISION_NAME = "panel_day_engine_project_final_decision_pack_v1.csv"
HANDOFF_SUMMARY_NAME = "panel_day_engine_project_handoff_summary_v1.csv"

CLEAN_PACK_OUTPUT_NAME = "panel_day_engine_internal_share_clean_pack_v1.md"
CLEAN_SUMMARY_OUTPUT_NAME = "panel_day_engine_internal_share_clean_summary_v1.csv"

SUMMARY_COLS = [
    "섹션",
    "항목",
    "값_ko",
    "비고_ko",
]

REQUIRED_PERF_ROWS = [
    "전조형 고장",
    "급작 고장",
    "common-cause routing",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a clean Korean internal-share pack from already-approved summary artifacts only."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to the project root.",
    )
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def numeric_float(value: object) -> float | None:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return None
    return float(numeric)


def format_numeric(value: object) -> str:
    numeric = numeric_float(value)
    if numeric is None:
        return ""
    if float(numeric).is_integer():
        return str(int(numeric))
    return f"{numeric:.4f}".rstrip("0").rstrip(".")


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def load_inputs(root: Path) -> dict[str, pd.DataFrame]:
    share_dir = root / "_share"
    frames = {
        "latest_perf": read_csv(share_dir / LATEST_PERF_NAME),
        "abrupt6": read_csv(share_dir / ABRUPT6_NAME),
        "kernel": read_csv(share_dir / KERNEL_MAPPING_NAME),
        "gpv7": read_csv(share_dir / GPV7_NAME),
        "progress": read_csv(share_dir / PROGRESS_NAME),
        "final_decision": read_csv(share_dir / FINAL_DECISION_NAME),
        "handoff": read_csv(share_dir / HANDOFF_SUMMARY_NAME),
    }

    ensure_columns(
        frames["latest_perf"],
        ["구분", "현재_대표기준", "양성_표본수", "재현율", "정밀도", "F1", "선행시간_중앙값_일", "선행시간_범위_일", "현재_판정_ko"],
        LATEST_PERF_NAME,
    )
    ensure_columns(
        frames["abrupt6"],
        ["site", "panel_id", "고장시점", "증상명_ko", "세부근거_ko", "source_field_ko", "비고_ko"],
        ABRUPT6_NAME,
    )
    ensure_columns(
        frames["kernel"],
        ["커널로그_증상명", "주_프로젝트분류", "보조_프로젝트분류", "설명_ko", "주의_ko"],
        KERNEL_MAPPING_NAME,
    )
    ensure_columns(
        frames["gpv7"],
        ["고장유형_번호", "고장유형_설명_ko", "성능요약_ko", "수치_ko", "source_ref_ko"],
        GPV7_NAME,
    )
    ensure_columns(
        frames["progress"],
        ["항목", "현재_완료율_추정", "현재_상태_ko", "근거_ko"],
        PROGRESS_NAME,
    )
    ensure_columns(
        frames["final_decision"],
        ["eval_scope", "current_data_decision", "allowed_claim_strength", "chosen_operational_workflow_name", "final_usage_decision"],
        FINAL_DECISION_NAME,
    )
    ensure_columns(
        frames["handoff"],
        ["eval_scope", "handoff_status_ko", "chosen_operational_workflow_name"],
        HANDOFF_SUMMARY_NAME,
    )

    for df in frames.values():
        for column in df.columns:
            if df[column].dtype == object:
                df[column] = df[column].map(normalize_text)
    return frames


def validate_inputs(frames: dict[str, pd.DataFrame]) -> None:
    perf_rows = set(frames["latest_perf"]["구분"].tolist())
    missing_perf = [row for row in REQUIRED_PERF_ROWS if row not in perf_rows]
    if missing_perf:
        raise SystemExit(f"latest perf rows missing: {missing_perf}")

    if len(frames["abrupt6"]) != 6:
        raise SystemExit(f"abrupt6 symptom map must have exactly 6 rows, got {len(frames['abrupt6'])}")

    progress_items = set(frames["progress"]["항목"].tolist())
    expected_progress = {"연구/알고리즘 큰 줄기", "운영 스택", "내부 공유/정리 문서"}
    if progress_items != expected_progress:
        raise SystemExit(f"progress snapshot rows mismatch: {sorted(progress_items)}")

    handoff_scopes = set(frames["handoff"]["eval_scope"].tolist())
    final_scopes = set(frames["final_decision"]["eval_scope"].tolist())
    expected_scopes = {
        "step1_taxonomy",
        "step2_onset_truth",
        "step3_precursor_performance",
        "step4_abrupt_no_precursor",
        "step4_common_cause_routing",
        "operator_policy_proxy",
    }
    if handoff_scopes != expected_scopes:
        raise SystemExit(f"handoff summary scopes mismatch: {sorted(handoff_scopes)}")
    if final_scopes != expected_scopes:
        raise SystemExit(f"final decision scopes mismatch: {sorted(final_scopes)}")


def perf_lookup(latest_perf_df: pd.DataFrame) -> dict[str, dict[str, object]]:
    return {
        normalize_text(row["구분"]): row
        for row in latest_perf_df.to_dict(orient="records")
    }


def handoff_lookup(handoff_df: pd.DataFrame) -> dict[str, dict[str, object]]:
    return {
        normalize_text(row["eval_scope"]): row
        for row in handoff_df.to_dict(orient="records")
    }


def final_lookup(final_df: pd.DataFrame) -> dict[str, dict[str, object]]:
    return {
        normalize_text(row["eval_scope"]): row
        for row in final_df.to_dict(orient="records")
    }


def perf_summary_value(row: dict[str, object]) -> str:
    bits = [
        f"대표기준={normalize_text(row['현재_대표기준'])}",
        f"표본={format_numeric(row['양성_표본수'])}",
        f"R={format_numeric(row['재현율'])}",
        f"P={format_numeric(row['정밀도'])}",
        f"F1={format_numeric(row['F1'])}",
    ]
    lead_median = normalize_text(row["선행시간_중앙값_일"])
    lead_range = normalize_text(row["선행시간_범위_일"])
    if lead_median:
        bits.append(f"선행중앙={lead_median}일")
    if lead_range:
        bits.append(f"선행범위={lead_range}일")
    return ", ".join(bits)


def build_summary_df(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    latest_perf = perf_lookup(frames["latest_perf"])
    final_by_scope = final_lookup(frames["final_decision"])
    handoff_by_scope = handoff_lookup(frames["handoff"])

    rows: list[dict[str, object]] = []

    perf_item_map = {
        "전조형 고장": "전조형 고장",
        "급작 고장": "급작 고장",
        "common-cause routing": "같이 흔들리는 이상",
    }
    for source_name, display_name in perf_item_map.items():
        row = latest_perf[source_name]
        rows.append(
            {
                "섹션": "최신 성능",
                "항목": display_name,
                "값_ko": perf_summary_value(row),
                "비고_ko": normalize_text(row["현재_판정_ko"]),
            }
        )

    for row in frames["abrupt6"].to_dict(orient="records"):
        rows.append(
            {
                "섹션": "급작 고장 6건",
                "항목": normalize_text(row["panel_id"]),
                "값_ko": f"{normalize_text(row['site'])} / {normalize_text(row['고장시점'])} / {normalize_text(row['증상명_ko'])}",
                "비고_ko": normalize_text(row["세부근거_ko"]),
            }
        )

    for row in frames["kernel"].to_dict(orient="records"):
        rows.append(
            {
                "섹션": "커널로그-프로젝트 매핑",
                "항목": normalize_text(row["커널로그_증상명"]),
                "값_ko": f"주={normalize_text(row['주_프로젝트분류'])}, 보조={normalize_text(row['보조_프로젝트분류'])}",
                "비고_ko": normalize_text(row["주의_ko"]),
            }
        )

    for row in frames["gpv7"].to_dict(orient="records"):
        item = f"{normalize_text(row['고장유형_번호'])}. {normalize_text(row['고장유형_설명_ko'])}"
        metric_text = normalize_text(row["수치_ko"])
        value = normalize_text(row["성능요약_ko"])
        if metric_text:
            value = f"{value} / {metric_text}"
        rows.append(
            {
                "섹션": "GPV 7종",
                "항목": item,
                "값_ko": value,
                "비고_ko": normalize_text(row["source_ref_ko"]),
            }
        )

    for row in frames["progress"].to_dict(orient="records"):
        rows.append(
            {
                "섹션": "진행률",
                "항목": normalize_text(row["항목"]),
                "값_ko": f"{format_numeric(row['현재_완료율_추정'])}% / {normalize_text(row['현재_상태_ko'])}",
                "비고_ko": normalize_text(row["근거_ko"]),
            }
        )

    operator_workflow_name = normalize_text(handoff_by_scope["operator_policy_proxy"]["chosen_operational_workflow_name"])
    operator_status = normalize_text(handoff_by_scope["operator_policy_proxy"]["handoff_status_ko"])
    rows.extend(
        [
            {
                "섹션": "말해도 되는 것 / 말하면 안 되는 것",
                "항목": "급작 고장",
                "값_ko": f"현재는 {normalize_text(handoff_by_scope['step4_abrupt_no_precursor']['handoff_status_ko'])} 수준으로 말할 수 있다.",
                "비고_ko": "bounded current-data 수준으로만 공유",
            },
            {
                "섹션": "말해도 되는 것 / 말하면 안 되는 것",
                "항목": "전조형 고장",
                "값_ko": f"현재는 {normalize_text(handoff_by_scope['step3_precursor_performance']['handoff_status_ko'])} 상태다.",
                "비고_ko": "표본이 작아 안정 성능으로 말하면 안 됨",
            },
            {
                "섹션": "말해도 되는 것 / 말하면 안 되는 것",
                "항목": "같이 흔들리는 이상",
                "값_ko": f"현재는 {normalize_text(handoff_by_scope['step4_common_cause_routing']['handoff_status_ko'])} 상태다.",
                "비고_ko": "descriptive / exploratory 범위만 허용",
            },
            {
                "섹션": "말해도 되는 것 / 말하면 안 되는 것",
                "항목": "운영 workflow",
                "값_ko": f"`{operator_workflow_name}` 는 현재 `{operator_status}` 으로 정리돼 있다.",
                "비고_ko": "운영 workflow choice 이지 detector 일반 성능 claim 아님",
            },
            {
                "섹션": "말해도 되는 것 / 말하면 안 되는 것",
                "항목": "과장 금지",
                "값_ko": "step1/2는 coverage/reference 범위다. detector 일반 성능으로 과장하면 안 된다.",
                "비고_ko": f"final scope 상태: step3={normalize_text(final_by_scope['step3_precursor_performance']['final_usage_decision'])}, step4_common={normalize_text(final_by_scope['step4_common_cause_routing']['final_usage_decision'])}",
            },
        ]
    )
    return pd.DataFrame(rows, columns=SUMMARY_COLS)


def build_clean_pack_md(frames: dict[str, pd.DataFrame]) -> str:
    latest_perf = perf_lookup(frames["latest_perf"])
    handoff_by_scope = handoff_lookup(frames["handoff"])
    operator_workflow_name = normalize_text(handoff_by_scope["operator_policy_proxy"]["chosen_operational_workflow_name"])
    operator_status = normalize_text(handoff_by_scope["operator_policy_proxy"]["handoff_status_ko"])

    section_lines = [
        "## 1. 최신 성능 요약",
        f"- 전조형 고장: {perf_summary_value(latest_perf['전조형 고장'])}. {normalize_text(latest_perf['전조형 고장']['현재_판정_ko'])}",
        f"- 급작 고장: {perf_summary_value(latest_perf['급작 고장'])}. {normalize_text(latest_perf['급작 고장']['현재_판정_ko'])}",
        f"- 같이 흔들리는 이상: {perf_summary_value(latest_perf['common-cause routing'])}. {normalize_text(latest_perf['common-cause routing']['현재_판정_ko'])}",
        "",
        "## 2. 급작 고장 6건 증상 분류",
    ]
    for row in frames["abrupt6"].to_dict(orient="records"):
        section_lines.append(
            f"- {normalize_text(row['site'])} / {normalize_text(row['panel_id'])} / {normalize_text(row['고장시점'])}: {normalize_text(row['증상명_ko'])}. {normalize_text(row['세부근거_ko'])}"
        )

    section_lines.extend(
        [
            "",
            "## 3. 커널로그 분류와 프로젝트 분류 관계",
            "- 커널로그는 증상 축이다.",
            "- 프로젝트는 사건 성격 축이다.",
        ]
    )
    for row in frames["kernel"].to_dict(orient="records"):
        section_lines.append(
            f"- {normalize_text(row['커널로그_증상명'])}: 주={normalize_text(row['주_프로젝트분류'])}, 보조={normalize_text(row['보조_프로젝트분류'])}"
        )

    section_lines.extend(
        [
            "",
            "## 4. GPV 7종 정리",
        ]
    )
    for row in frames["gpv7"].to_dict(orient="records"):
        numeric_text = normalize_text(row["수치_ko"])
        if numeric_text:
            section_lines.append(
                f"- {normalize_text(row['고장유형_번호'])}. {normalize_text(row['고장유형_설명_ko'])}: {normalize_text(row['성능요약_ko'])}. {numeric_text}"
            )
        else:
            section_lines.append(
                f"- {normalize_text(row['고장유형_번호'])}. {normalize_text(row['고장유형_설명_ko'])}: {normalize_text(row['성능요약_ko'])}"
            )

    section_lines.extend(
        [
            "",
            "## 5. 현재 진행률",
        ]
    )
    for row in frames["progress"].to_dict(orient="records"):
        section_lines.append(
            f"- {normalize_text(row['항목'])}: {format_numeric(row['현재_완료율_추정'])}%. {normalize_text(row['현재_상태_ko'])}"
        )

    section_lines.extend(
        [
            "",
            "## 6. 지금 말해도 되는 것 / 말하면 안 되는 것",
            "- 급작 고장은 bounded current-data 수준으로는 말할 수 있다.",
            "- 전조형은 표본이 적어 아직 탐색적이다.",
            "- 같이 흔들리는 이상은 아직 탐색적이다.",
            f"- 운영 workflow `{operator_workflow_name}` 는 현재 `{operator_status}` 으로 사용할 수 있다.",
            "- 다만 이것을 detector 일반 성능으로 과장하면 안 된다.",
        ]
    )
    return "\n".join(section_lines).strip() + "\n"


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"

    frames = load_inputs(root)
    validate_inputs(frames)

    summary_df = build_summary_df(frames)
    clean_pack_md = build_clean_pack_md(frames)

    write_csv(summary_df, share_dir / CLEAN_SUMMARY_OUTPUT_NAME)
    write_text(share_dir / CLEAN_PACK_OUTPUT_NAME, clean_pack_md)

    print(f"wrote {share_dir / CLEAN_PACK_OUTPUT_NAME}")
    print(f"wrote {share_dir / CLEAN_SUMMARY_OUTPUT_NAME}")


if __name__ == "__main__":
    main()
