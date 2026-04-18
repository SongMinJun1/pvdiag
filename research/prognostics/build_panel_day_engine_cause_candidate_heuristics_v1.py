#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]

INTEGRATED_TABLE_NAME = "panel_day_engine_integrated_result_table_v1.csv"
EVIDENCE_PACK_NAME = "panel_day_engine_gpvs_evidence_pack_v1.csv"
VERDICT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
DETAILED_AUDIT_NAME = "panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv"

OUTPUT_MAIN_NAME = "panel_day_engine_cause_candidate_heuristics_v1.csv"
OUTPUT_BREAKDOWN_NAME = "panel_day_engine_cause_candidate_score_breakdown_v1.csv"
OUTPUT_SUMMARY_NAME = "panel_day_engine_cause_candidate_summary_v1.csv"

CANDIDATES = [
    "부분음영형",
    "오염형",
    "열화형",
    "다이오드·서브스트링형",
    "접속·부분개방형",
    "센서·피드백형",
    "제어응답형",
    "외부계통교란형",
    "전력변환부형",
    "원인미확정",
]

TIE_PRIORITY = {
    "접속·부분개방형": 0,
    "다이오드·서브스트링형": 1,
    "부분음영형": 2,
    "오염형": 3,
    "열화형": 4,
    "센서·피드백형": 5,
    "제어응답형": 6,
    "외부계통교란형": 7,
    "전력변환부형": 8,
    "원인미확정": 9,
}

INTEGRATED_REQUIRED_COLS = [
    "site",
    "panel_id",
    "패널고장여부_ko",
    "사건유형_ko",
    "최종고장양상_ko",
    "커널로그_원인군_ko",
    "GPVS_내부참고유형_ko",
    "GPVS_외부참조패턴_ko",
    "GPVS_최종사용권고_ko",
]

EVIDENCE_REQUIRED_COLS = [
    "site",
    "panel_id",
    "사건유형_ko",
    "최종고장양상_ko",
    "커널로그_원인군_ko",
    "GPVS_내부판정_ko",
    "GPVS_외부참조패턴_ko",
    "GPVS_최종사용권고_ko",
]

VERDICT_REQUIRED_COLS = [
    "site",
    "panel_id",
    "패널고장여부_ko",
    "사건유형_ko",
    "최종고장양상_ko",
    "커널로그_원인군_ko",
    "GPVS_내부참고유형_ko",
    "GPVS_외부참조패턴_ko",
]

DETAILED_REQUIRED_COLS = [
    "site",
    "panel_id",
    "gpvs_detailed_top1_fault_type",
]

MAIN_COLS = [
    "site",
    "panel_id",
    "사건유형_ko",
    "최종고장양상_ko",
    "커널로그_원인군_ko",
    "GPVS_내부참고유형_ko",
    "GPVS_외부참조패턴_ko",
    "원인후보_top1_ko",
    "원인후보_top1_score",
    "원인후보_top2_ko",
    "원인후보_top2_score",
    "원인후보_top3_ko",
    "원인후보_top3_score",
    "원인후보_경합상태_ko",
    "원인후보_공동상위후보_csv",
    "원인후보_실증우선확인_ko",
    "원인후보_신뢰도_ko",
    "원인후보_해석메모_ko",
]

BREAKDOWN_COLS = [
    "site",
    "panel_id",
    "candidate_ko",
    "raw_score",
    "support_signal_csv",
    "note_ko",
]

SUMMARY_COLS = [
    "fault_panel_count",
    "unique_top1_candidate_count",
    "top1_부분음영형_count",
    "top1_오염형_count",
    "top1_열화형_count",
    "top1_다이오드·서브스트링형_count",
    "top1_접속·부분개방형_count",
    "top1_센서·피드백형_count",
    "top1_제어응답형_count",
    "top1_외부계통교란형_count",
    "top1_전력변환부형_count",
    "top1_원인미확정_count",
    "단일우세_count",
    "two_way_competition_count",
    "multi_way_competition_count",
    "note_ko",
]

GPVS_EXTERNAL_RULES = {
    "국소 출력 불균형형": {
        "부분음영형": 2,
        "오염형": 1,
        "열화형": 1,
        "다이오드·서브스트링형": 2,
        "접속·부분개방형": 1,
    },
    "장치 응답 이상형": {
        "센서·피드백형": 3,
        "제어응답형": 2,
        "접속·부분개방형": 1,
    },
    "외부 계통 교란형": {
        "외부계통교란형": 4,
    },
    "전력변환부 이상형": {
        "전력변환부형": 4,
    },
    "제어 응답 이상형": {
        "제어응답형": 4,
    },
}

INTERNAL_FAMILY_RULES = {
    "전기적 고장 계열": {
        "다이오드·서브스트링형": 1,
        "접속·부분개방형": 1,
    },
    "개방/장치이상 계열": {
        "접속·부분개방형": 2,
        "센서·피드백형": 1,
        "제어응답형": 1,
    },
    "불확실": {
        "원인미확정": 2,
    },
}

KERNEL_RULES = {
    "다이오드형": {
        "다이오드·서브스트링형": 2,
    },
    "개방/장치이상형": {
        "접속·부분개방형": 2,
        "센서·피드백형": 1,
    },
    "모듈손상형": {
        "열화형": 2,
        "오염형": 1,
        "다이오드·서브스트링형": 1,
    },
}

TEMPORAL_RULES = {
    ("전조형 고장", "진행성 악화"): {
        "열화형": 2,
        "오염형": 1,
        "다이오드·서브스트링형": 1,
    },
    ("전조형 고장", "급격 종료"): {
        "접속·부분개방형": 1,
        "다이오드·서브스트링형": 1,
        "센서·피드백형": 1,
    },
    ("급작 고장", "급작 발생"): {
        "접속·부분개방형": 1,
        "외부계통교란형": 1,
        "다이오드·서브스트링형": 1,
    },
}

USAGE_WEIGHT_RULES = {
    ("핵심참조", "국소 출력 불균형형"): {
        "다이오드·서브스트링형": 1,
        "부분음영형": 1,
    },
    ("보조참조", "장치 응답 이상형"): {
        "센서·피드백형": 1,
        "제어응답형": 1,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a heuristic cause-candidate ranking layer for current fault panels."
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


def read_optional_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def as_key(site: object, panel_id: object) -> tuple[str, str]:
    return normalize_text(site), normalize_text(panel_id)


def validate_unique_keys(df: pd.DataFrame, name: str) -> None:
    if df.empty:
        return
    if df[["site", "panel_id"]].duplicated().any():
        dup = df.loc[df[["site", "panel_id"]].duplicated(keep=False), ["site", "panel_id"]]
        raise SystemExit(f"{name} must be unique by (site, panel_id): {dup.to_dict(orient='records')[:5]}")


def lookup_map(df: pd.DataFrame) -> dict[tuple[str, str], dict[str, str]]:
    lookup: dict[tuple[str, str], dict[str, str]] = {}
    for row in df.to_dict(orient="records"):
        lookup[as_key(row.get("site"), row.get("panel_id"))] = {
            key: normalize_text(value) for key, value in row.items()
        }
    return lookup


def apply_rule_bundle(
    scores: dict[str, int],
    signals: dict[str, list[str]],
    bundle: dict[str, int],
    signal_prefix: str,
) -> None:
    for candidate, value in bundle.items():
        scores[candidate] += int(value)
        signals[candidate].append(f"{signal_prefix}:{candidate}+{int(value)}")


def rank_candidates(scores: dict[str, int]) -> list[tuple[str, int]]:
    return sorted(
        scores.items(),
        key=lambda item: (-item[1], TIE_PRIORITY[item[0]]),
    )


def competition_candidates(top_ranked: list[tuple[str, int]]) -> list[tuple[str, int]]:
    top1_score = top_ranked[0][1]
    return [item for item in top_ranked if item[1] >= top1_score - 1]


def competition_status(competition_ranked: list[tuple[str, int]]) -> str:
    if len(competition_ranked) <= 1:
        return "단일우세"
    if len(competition_ranked) == 2:
        return "2자경합"
    return "다자경합"


def competition_csv(competition_ranked: list[tuple[str, int]]) -> str:
    return ",".join(candidate for candidate, _ in competition_ranked)


def object_particle(text: str) -> str:
    normalized = normalize_text(text)
    if not normalized:
        return "를"
    last_char = normalized[-1]
    code_point = ord(last_char)
    if 0xAC00 <= code_point <= 0xD7A3:
        jongseong = (code_point - 0xAC00) % 28
        return "을" if jongseong else "를"
    return "를"


def action_note(
    top1_name: str,
    competition_ranked: list[tuple[str, int]],
    competition_state: str,
) -> str:
    if competition_state == "단일우세":
        return f"{top1_name} 우선 점검"
    if competition_state == "2자경합":
        cand1, cand2 = [candidate for candidate, _ in competition_ranked[:2]]
        return f"{cand1}과 {cand2}{object_particle(cand2)} 함께 우선 점검"
    if competition_state == "다자경합":
        cand1, cand2, cand3 = [candidate for candidate, _ in competition_ranked[:3]]
        return f"{cand1}, {cand2}, {cand3}을 함께 우선 점검"
    return f"{top1_name} 우선 점검"


def confidence_label(top1_score: int, competition_state: str) -> str:
    if top1_score >= 6 and competition_state == "단일우세":
        return "high"
    if top1_score >= 4 and competition_state != "다자경합":
        return "medium"
    return "low"


def interpretive_note(
    row: dict[str, str],
    top_ranked: list[tuple[str, int]],
    competition_ranked: list[tuple[str, int]],
    competition_state: str,
    confidence: str,
    detailed_row: dict[str, str] | None,
) -> str:
    top1_name, top1_score = top_ranked[0]
    top2_name, top2_score = top_ranked[1]
    sources = []
    if normalize_text(row.get("GPVS_외부참조패턴_ko")):
        sources.append(f"GPVS 외부={normalize_text(row['GPVS_외부참조패턴_ko'])}")
    if normalize_text(row.get("GPVS_내부참고유형_ko")):
        sources.append(f"GPVS 내부={normalize_text(row['GPVS_내부참고유형_ko'])}")
    if normalize_text(row.get("커널로그_원인군_ko")):
        sources.append(f"커널로그={normalize_text(row['커널로그_원인군_ko'])}")
    if normalize_text(row.get("사건유형_ko")) or normalize_text(row.get("최종고장양상_ko")):
        sources.append(
            f"시간양상={normalize_text(row.get('사건유형_ko'))}/{normalize_text(row.get('최종고장양상_ko'))}"
        )
    detail_tail = ""
    if detailed_row is not None and normalize_text(detailed_row.get("gpvs_detailed_top1_fault_type")):
        detail_tail = (
            f" raw detailed audit top1={normalize_text(detailed_row['gpvs_detailed_top1_fault_type'])}는 "
            "score에 직접 가산하지 않고 front-facing GPVS pattern으로만 반영했다."
        )

    source_text = ", ".join(sources)
    competition_text = competition_csv(competition_ranked)
    if confidence == "high":
        return (
            f"{source_text} 신호가 {top1_name} 쪽으로 강하게 겹치고 경합상태는 {competition_state}({competition_text})다."
            f"{detail_tail}"
        )
    if confidence == "medium":
        return (
            f"{source_text} 신호가 {top1_name}에 더 기울지만 경합상태는 {competition_state}({competition_text})라 {top2_name}({top2_score})도 함께 확인해야 한다."
            f"{detail_tail}"
        )
    return (
        f"{source_text} 신호가 {competition_state}({competition_text}) 상태여서 {top1_name}({top1_score})와 {top2_name}({top2_score})를 포함한 공동 점검 후보로 읽어야 하므로 "
        "definitive diagnosis가 아니라 현장 점검 우선순위 좁히기 용도로만 읽는다."
        f"{detail_tail}"
    )


def build_outputs(
    integrated_df: pd.DataFrame,
    evidence_df: pd.DataFrame,
    verdict_df: pd.DataFrame,
    detailed_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    fault_integrated_df = integrated_df.loc[integrated_df["패널고장여부_ko"].map(normalize_text).eq("고장")].copy()
    if len(fault_integrated_df) != 6:
        raise SystemExit(f"{INTEGRATED_TABLE_NAME} current fault panel count must be 6, found {len(fault_integrated_df)}")

    fault_verdict_df = verdict_df.loc[verdict_df["패널고장여부_ko"].map(normalize_text).eq("고장")].copy()
    if len(fault_verdict_df) != 6:
        raise SystemExit(f"{VERDICT_NAME} current fault panel count must be 6, found {len(fault_verdict_df)}")
    if len(evidence_df) != 6:
        raise SystemExit(f"{EVIDENCE_PACK_NAME} current fault panel count must be 6, found {len(evidence_df)}")

    integrated_lookup = lookup_map(fault_integrated_df)
    evidence_lookup = lookup_map(evidence_df)
    verdict_lookup = lookup_map(fault_verdict_df)
    detailed_lookup = lookup_map(detailed_df) if not detailed_df.empty else {}

    fault_keys = set(integrated_lookup)
    if set(evidence_lookup) != fault_keys:
        raise SystemExit("integrated table and evidence pack fault key universe must match exactly")
    if set(verdict_lookup) != fault_keys:
        raise SystemExit("integrated table and verdict fault key universe must match exactly")
    if not detailed_df.empty and set(detailed_lookup) != fault_keys:
        raise SystemExit("optional detailed audit fault key universe must match current fault panels when present")

    main_rows: list[dict[str, object]] = []
    breakdown_rows: list[dict[str, object]] = []

    for site, panel_id in sorted(fault_keys):
        integrated_row = integrated_lookup[(site, panel_id)]
        evidence_row = evidence_lookup[(site, panel_id)]
        verdict_row = verdict_lookup[(site, panel_id)]
        detailed_row = detailed_lookup.get((site, panel_id))

        event_type = normalize_text(integrated_row["사건유형_ko"])
        terminal_pattern = normalize_text(integrated_row["최종고장양상_ko"])
        kernel_family = normalize_text(integrated_row["커널로그_원인군_ko"])
        internal_family = normalize_text(integrated_row["GPVS_내부참고유형_ko"]) or normalize_text(evidence_row["GPVS_내부판정_ko"])
        external_pattern = normalize_text(integrated_row["GPVS_외부참조패턴_ko"]) or normalize_text(evidence_row["GPVS_외부참조패턴_ko"])
        usage_level = normalize_text(integrated_row["GPVS_최종사용권고_ko"]) or normalize_text(evidence_row["GPVS_최종사용권고_ko"])

        if event_type != normalize_text(evidence_row["사건유형_ko"]) or event_type != normalize_text(verdict_row["사건유형_ko"]):
            raise SystemExit(f"fault event type mismatch across inputs for {site}/{panel_id}")
        if terminal_pattern != normalize_text(evidence_row["최종고장양상_ko"]) or terminal_pattern != normalize_text(verdict_row["최종고장양상_ko"]):
            raise SystemExit(f"fault terminal pattern mismatch across inputs for {site}/{panel_id}")
        if kernel_family != normalize_text(evidence_row["커널로그_원인군_ko"]) or kernel_family != normalize_text(verdict_row["커널로그_원인군_ko"]):
            raise SystemExit(f"kernel family mismatch across inputs for {site}/{panel_id}")

        scores = {candidate: 0 for candidate in CANDIDATES}
        signals = {candidate: [] for candidate in CANDIDATES}

        if external_pattern in GPVS_EXTERNAL_RULES:
            apply_rule_bundle(scores, signals, GPVS_EXTERNAL_RULES[external_pattern], f"gpvs_external={external_pattern}")
        if internal_family in INTERNAL_FAMILY_RULES:
            apply_rule_bundle(scores, signals, INTERNAL_FAMILY_RULES[internal_family], f"gpvs_internal={internal_family}")
        if kernel_family in KERNEL_RULES:
            apply_rule_bundle(scores, signals, KERNEL_RULES[kernel_family], f"kernel={kernel_family}")
        temporal_key = (event_type, terminal_pattern)
        if temporal_key in TEMPORAL_RULES:
            apply_rule_bundle(scores, signals, TEMPORAL_RULES[temporal_key], f"temporality={event_type}/{terminal_pattern}")
        usage_key = (usage_level, external_pattern)
        if usage_key in USAGE_WEIGHT_RULES:
            apply_rule_bundle(scores, signals, USAGE_WEIGHT_RULES[usage_key], f"usage={usage_level}|{external_pattern}")

        ranked = rank_candidates(scores)
        top1_name, top1_score = ranked[0]
        top2_name, top2_score = ranked[1]
        top3_name, top3_score = ranked[2]
        competition_ranked = competition_candidates(ranked)
        competition_state = competition_status(competition_ranked)
        competition_names_csv = competition_csv(competition_ranked)
        action_text = action_note(top1_name, competition_ranked, competition_state)
        confidence = confidence_label(top1_score, competition_state)
        memo = interpretive_note(
            integrated_row,
            ranked,
            competition_ranked,
            competition_state,
            confidence,
            detailed_row,
        )

        main_rows.append(
            {
                "site": site,
                "panel_id": panel_id,
                "사건유형_ko": event_type,
                "최종고장양상_ko": terminal_pattern,
                "커널로그_원인군_ko": kernel_family,
                "GPVS_내부참고유형_ko": internal_family,
                "GPVS_외부참조패턴_ko": external_pattern,
                "원인후보_top1_ko": top1_name,
                "원인후보_top1_score": top1_score,
                "원인후보_top2_ko": top2_name,
                "원인후보_top2_score": top2_score,
                "원인후보_top3_ko": top3_name,
                "원인후보_top3_score": top3_score,
                "원인후보_경합상태_ko": competition_state,
                "원인후보_공동상위후보_csv": competition_names_csv,
                "원인후보_실증우선확인_ko": action_text,
                "원인후보_신뢰도_ko": confidence,
                "원인후보_해석메모_ko": memo,
            }
        )

        for candidate, raw_score in ranked:
            signal_text = ", ".join(signals[candidate])
            breakdown_rows.append(
                {
                    "site": site,
                    "panel_id": panel_id,
                    "candidate_ko": candidate,
                    "raw_score": raw_score,
                    "support_signal_csv": signal_text,
                    "note_ko": "가산 규칙 없음" if not signal_text else f"{len(signals[candidate])}개 가산 규칙 합",
                }
            )

    main_df = pd.DataFrame(main_rows).sort_values(["site", "panel_id"]).reset_index(drop=True).reindex(columns=MAIN_COLS)
    breakdown_df = pd.DataFrame(breakdown_rows).sort_values(["site", "panel_id", "raw_score", "candidate_ko"], ascending=[True, True, False, True]).reset_index(drop=True).reindex(columns=BREAKDOWN_COLS)

    top1_counts = main_df["원인후보_top1_ko"].value_counts().to_dict()
    competition_counts = main_df["원인후보_경합상태_ko"].value_counts().to_dict()
    summary_row = {
        "fault_panel_count": len(main_df),
        "unique_top1_candidate_count": int(main_df["원인후보_top1_ko"].nunique()),
        "top1_부분음영형_count": int(top1_counts.get("부분음영형", 0)),
        "top1_오염형_count": int(top1_counts.get("오염형", 0)),
        "top1_열화형_count": int(top1_counts.get("열화형", 0)),
        "top1_다이오드·서브스트링형_count": int(top1_counts.get("다이오드·서브스트링형", 0)),
        "top1_접속·부분개방형_count": int(top1_counts.get("접속·부분개방형", 0)),
        "top1_센서·피드백형_count": int(top1_counts.get("센서·피드백형", 0)),
        "top1_제어응답형_count": int(top1_counts.get("제어응답형", 0)),
        "top1_외부계통교란형_count": int(top1_counts.get("외부계통교란형", 0)),
        "top1_전력변환부형_count": int(top1_counts.get("전력변환부형", 0)),
        "top1_원인미확정_count": int(top1_counts.get("원인미확정", 0)),
        "단일우세_count": int(competition_counts.get("단일우세", 0)),
        "two_way_competition_count": int(competition_counts.get("2자경합", 0)),
        "multi_way_competition_count": int(competition_counts.get("다자경합", 0)),
        "note_ko": (
            "이 표는 heuristic candidate-ranking layer이며 field trial triage용 후보 좁히기 표다. "
            "panel verdict와 GPVS reference, kernel-log, 시간양상을 additive score로만 합산했고 "
            "final root-cause confirmation이나 direct root-cause classifier로 읽으면 안 된다. "
            "경합 row는 단일 확정이 아니라 공동 현장점검 후보로 읽어야 한다."
        ),
    }
    summary_df = pd.DataFrame([summary_row]).reindex(columns=SUMMARY_COLS)
    return main_df, breakdown_df, summary_df


def write_outputs(root: Path, main_df: pd.DataFrame, breakdown_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    main_df.to_csv(share_dir / OUTPUT_MAIN_NAME, index=False, encoding="utf-8-sig")
    breakdown_df.to_csv(share_dir / OUTPUT_BREAKDOWN_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / OUTPUT_SUMMARY_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    share_dir = args.root.resolve() / "_share"

    integrated_df = read_csv(share_dir / INTEGRATED_TABLE_NAME)
    evidence_df = read_csv(share_dir / EVIDENCE_PACK_NAME)
    verdict_df = read_csv(share_dir / VERDICT_NAME)
    detailed_df = read_optional_csv(share_dir / DETAILED_AUDIT_NAME)

    ensure_columns(integrated_df, INTEGRATED_REQUIRED_COLS, INTEGRATED_TABLE_NAME)
    ensure_columns(evidence_df, EVIDENCE_REQUIRED_COLS, EVIDENCE_PACK_NAME)
    ensure_columns(verdict_df, VERDICT_REQUIRED_COLS, VERDICT_NAME)
    if not detailed_df.empty:
        ensure_columns(detailed_df, DETAILED_REQUIRED_COLS, DETAILED_AUDIT_NAME)

    validate_unique_keys(integrated_df, INTEGRATED_TABLE_NAME)
    validate_unique_keys(evidence_df, EVIDENCE_PACK_NAME)
    validate_unique_keys(verdict_df, VERDICT_NAME)
    if not detailed_df.empty:
        validate_unique_keys(detailed_df, DETAILED_AUDIT_NAME)

    main_df, breakdown_df, summary_df = build_outputs(integrated_df, evidence_df, verdict_df, detailed_df)
    write_outputs(args.root.resolve(), main_df, breakdown_df, summary_df)


if __name__ == "__main__":
    main()
