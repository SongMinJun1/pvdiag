#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.prognostics import runtime_rawonly_chain_common_v1 as common


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
    "다이오드·서브스트링형": 0,
    "접속·부분개방형": 1,
    "열화형": 2,
    "부분음영형": 3,
    "오염형": 4,
    "센서·피드백형": 5,
    "제어응답형": 6,
    "외부계통교란형": 7,
    "전력변환부형": 8,
    "원인미확정": 9,
}
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
SUMMARY_COLS = [
    "fault_panel_count",
    "top1_다이오드서브스트링형_count",
    "top1_접속부분개방형_count",
    "top1_열화형_count",
    "top1_부분음영형_count",
    "top1_센서피드백형_count",
    "top1_원인미확정_count",
    "note_ko",
]

FAMILY_BASE_RULES = {
    "다이오드형": {
        "다이오드·서브스트링형": 5,
        "접속·부분개방형": 2,
        "부분음영형": 1,
    },
    "개방/장치이상형": {
        "센서·피드백형": 4,
        "접속·부분개방형": 3,
        "제어응답형": 2,
    },
    "모듈손상형": {
        "열화형": 5,
        "부분음영형": 2,
        "오염형": 2,
        "다이오드·서브스트링형": 1,
    },
    "불충분": {
        "원인미확정": 4,
    },
}
TEMPORAL_RULES = {
    ("전조형 고장", "진행성 악화"): {
        "열화형": 2,
        "오염형": 1,
    },
    ("전조형 고장", "급격 종료"): {
        "접속·부분개방형": 1,
        "다이오드·서브스트링형": 1,
    },
    ("급작 고장", "급작 발생"): {
        "접속·부분개방형": 1,
        "센서·피드백형": 1,
        "다이오드·서브스트링형": 1,
    },
}
SOURCE_RULES = {
    "vdrop": {"다이오드·서브스트링형": 2},
    "vdrop_suspect": {"다이오드·서브스트링형": 1},
    "legacy": {"접속·부분개방형": 2},
    "none": {"센서·피드백형": 1},
}
SUBTYPE_RULES = {
    "degradation": {"열화형": 2, "오염형": 1},
    "shadow": {"부분음영형": 2},
    "critical_fault_vdrop": {"다이오드·서브스트링형": 2},
    "confirmed_fault": {"다이오드·서브스트링형": 1},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a raw-only runtime cause-candidate heuristic from runtime final verdict."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Workspace root containing runtime verdict and audit outputs.",
    )
    return parser.parse_args()


def score_row(row: dict[str, object]) -> tuple[dict[str, int], list[str]]:
    scores = {candidate: 0 for candidate in CANDIDATES}
    notes: list[str] = []
    family = common.normalize_text(row.get("커널로그_원인군_ko"))
    event_type = common.normalize_text(row.get("사건유형_ko"))
    terminal = common.normalize_text(row.get("최종고장양상_ko"))
    temporal_event_type = event_type
    temporal_terminal = terminal
    if int(row.get("g1_suppressed_event_guard_applied_flag") or 0):
        temporal_event_type = (
            common.normalize_text(row.get("g1_suppressed_event_shadow_current_event_type_ko"))
            or event_type
        )
        temporal_terminal = (
            common.normalize_text(row.get("g1_suppressed_event_shadow_current_final_pattern_ko"))
            or terminal
        )
    source = common.normalize_text(row.get("대표critical_source"))
    subtype = common.normalize_text(row.get("대표anom_subtype"))

    for candidate, weight in FAMILY_BASE_RULES.get(family, {"원인미확정": 2}).items():
        scores[candidate] += weight
    notes.append(f"family={family or 'blank'}")

    for candidate, weight in TEMPORAL_RULES.get((temporal_event_type, temporal_terminal), {}).items():
        scores[candidate] += weight
    if temporal_event_type or temporal_terminal:
        notes.append(f"temporal={temporal_event_type}/{temporal_terminal}")
    if int(row.get("g1_suppressed_event_guard_applied_flag") or 0):
        notes.append("g1_guard_temporal_basis=pre_guard")

    for candidate, weight in SOURCE_RULES.get(source, {}).items():
        scores[candidate] += weight
    if source:
        notes.append(f"critical_source={source}")

    lowered_subtype = subtype.lower()
    for token, rule in SUBTYPE_RULES.items():
        if token in lowered_subtype:
            for candidate, weight in rule.items():
                scores[candidate] += weight
            notes.append(f"anom_subtype~={token}")

    if max(scores.values()) <= 0:
        scores["원인미확정"] = 1
    return scores, notes


def choose_ranked_candidates(scores: dict[str, int]) -> list[tuple[str, int]]:
    return sorted(scores.items(), key=lambda item: (-item[1], TIE_PRIORITY[item[0]], item[0]))


def competition_state(top_scores: list[int]) -> tuple[str, str]:
    if len(top_scores) < 2:
        return "단일우세", ""
    max_score = top_scores[0]
    tied = [idx for idx, score in enumerate(top_scores) if score == max_score]
    if len(tied) == 1:
        return "단일우세", ""
    if len(tied) == 2:
        return "2강경합", "top1_tie"
    return "다자경합", "multi_tie"


def confidence_label(top1: int, top2: int) -> str:
    gap = top1 - top2
    if top1 >= 6 and gap >= 2:
        return "높음"
    if top1 >= 4 and gap >= 1:
        return "중간"
    return "보통"


def build_outputs(verdict_df: pd.DataFrame, audit_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    audit_lookup = {
        (common.normalize_text(row["site"]), common.normalize_text(row["panel_id"])): row
        for row in audit_df.to_dict(orient="records")
    }
    rows: list[dict[str, object]] = []
    summary_counts = {key: 0 for key in [
        "다이오드·서브스트링형",
        "접속·부분개방형",
        "열화형",
        "부분음영형",
        "센서·피드백형",
        "원인미확정",
    ]}
    fault_count = 0

    for row in verdict_df.to_dict(orient="records"):
        if common.normalize_text(row.get("패널고장여부_ko")) != "고장":
            continue
        fault_count += 1
        key = (common.normalize_text(row["site"]), common.normalize_text(row["panel_id"]))
        merged = dict(row)
        merged.update(audit_lookup.get(key, {}))
        scores, notes = score_row(merged)
        ranked = choose_ranked_candidates(scores)
        top3 = ranked[:3]
        top_scores = [score for _, score in top3]
        competition, tie_note = competition_state(top_scores)
        top1, top2, top3_item = top3
        summary_counts[top1[0]] = summary_counts.get(top1[0], 0) + 1
        notes_text = ", ".join(notes + ([tie_note] if tie_note else []))
        rows.append(
            {
                "site": key[0],
                "panel_id": key[1],
                "사건유형_ko": common.normalize_text(row.get("사건유형_ko")),
                "최종고장양상_ko": common.normalize_text(row.get("최종고장양상_ko")),
                "커널로그_원인군_ko": common.normalize_text(row.get("커널로그_원인군_ko")),
                "GPVS_내부참고유형_ko": "",
                "GPVS_외부참조패턴_ko": "",
                "원인후보_top1_ko": top1[0],
                "원인후보_top1_score": top1[1],
                "원인후보_top2_ko": top2[0],
                "원인후보_top2_score": top2[1],
                "원인후보_top3_ko": top3_item[0],
                "원인후보_top3_score": top3_item[1],
                "원인후보_경합상태_ko": competition,
                "원인후보_공동상위후보_csv": ",".join(candidate for candidate, score in top3 if score == top1[1]),
                "원인후보_실증우선확인_ko": common.display_heuristic_name(top1[0]),
                "원인후보_신뢰도_ko": confidence_label(top1[1], top2[1]),
                "원인후보_해석메모_ko": notes_text,
            }
        )

    main_df = pd.DataFrame(rows).reindex(columns=MAIN_COLS).sort_values(["site", "panel_id"]).reset_index(drop=True)
    summary_df = pd.DataFrame(
        [
            {
                "fault_panel_count": fault_count,
                "top1_다이오드서브스트링형_count": int(summary_counts.get("다이오드·서브스트링형", 0)),
                "top1_접속부분개방형_count": int(summary_counts.get("접속·부분개방형", 0)),
                "top1_열화형_count": int(summary_counts.get("열화형", 0)),
                "top1_부분음영형_count": int(summary_counts.get("부분음영형", 0)),
                "top1_센서피드백형_count": int(summary_counts.get("센서·피드백형", 0)),
                "top1_원인미확정_count": int(summary_counts.get("원인미확정", 0)),
                "note_ko": (
                    "이 runtime heuristic는 raw-only strict chain용 deterministic triage 규칙이다. "
                    "family/event/source/subtype만 사용하며 GPVS/frozen label은 사용하지 않는다."
                ),
            }
        ]
    ).reindex(columns=SUMMARY_COLS)
    return main_df, summary_df


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    verdict_df = common.read_csv(share_dir / common.RUNTIME_VERDICT_OUTPUT_NAME)
    audit_df = common.read_csv(share_dir / common.RUNTIME_AUDIT_OUTPUT_NAME)
    main_df, summary_df = build_outputs(verdict_df, audit_df)
    output_path = share_dir / common.RUNTIME_HEURISTIC_OUTPUT_NAME
    summary_path = share_dir / common.RUNTIME_HEURISTIC_SUMMARY_NAME
    main_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
    print(f"[OK] wrote runtime raw-only heuristic: {output_path}")


if __name__ == "__main__":
    main()
