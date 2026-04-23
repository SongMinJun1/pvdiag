#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.prognostics import build_panel_day_engine_panel_multiaxis_verdict_v1 as verdict_mod

OUTPUT_NAME = "panel_day_engine_bootstrap_verdict_v1.csv"
OUTPUT_SUMMARY_NAME = "panel_day_engine_bootstrap_verdict_summary_v1.csv"
ALIAS_NAME = verdict_mod.VERDICT_OUTPUT_NAME

BOOTSTRAP_COLS = [
    "site",
    "panel_id",
    "패널고장여부_ko",
    "사건유형_ko",
    "최종고장양상_ko",
    "전조흔적_flag",
    "순수급작_flag",
    "전조평가셋편입_flag",
    "급작평가셋편입_flag",
]

SUMMARY_COLS = [
    "전체_패널수",
    "고장_패널수",
    "비고장_패널수",
    "미확정_패널수",
    "사건해석_전조형_패널수",
    "사건해석_급작_패널수",
    "전조평가셋_편입패널수",
    "급작평가셋_편입패널수",
    "note_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a minimal bootstrap verdict file for runtime chain bootstrapping. "
            "This omits fault_event_audit dependency and only materializes the fields that "
            "fault_event_audit requires as upstream input."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root. Defaults to the project root.",
    )
    parser.add_argument(
        "--write-panel-verdict-alias",
        action="store_true",
        help=(
            "Also write the bootstrap output to _share/panel_day_engine_panel_multiaxis_verdict_v1.csv "
            "so that fault_event_audit can consume it in a workspace-only chain."
        ),
    )
    return parser.parse_args()


def load_frames(root: Path) -> dict[str, pd.DataFrame]:
    share_dir = root / "_share"
    frames = {
        "workflow": verdict_mod.read_csv(share_dir / verdict_mod.WORKFLOW_DEFAULT_NAME),
        "abrupt6": verdict_mod.read_csv(share_dir / verdict_mod.ABRUPT6_SYMPTOM_MAP_NAME),
        "final_pack": verdict_mod.read_csv(share_dir / verdict_mod.FINAL_DECISION_PACK_NAME),
        "precursor_truth": verdict_mod.read_csv(share_dir / verdict_mod.PRECURSOR_ONSET_TRUTH_NAME),
        "non_precursor_perf": verdict_mod.read_csv(share_dir / verdict_mod.NON_PRECURSOR_PERFORMANCE_CASES_NAME),
        "common_cause": verdict_mod.read_csv(share_dir / verdict_mod.COMMON_CAUSE_RETROFIT_NAME),
        "consistency_cases": verdict_mod.read_csv(share_dir / verdict_mod.PRECURSOR_ABRUPT_CONSISTENCY_CASES_NAME),
        "consistency_summary": verdict_mod.read_csv(share_dir / verdict_mod.PRECURSOR_ABRUPT_CONSISTENCY_SUMMARY_NAME),
        "consistency_recommendation": verdict_mod.read_csv(share_dir / verdict_mod.PRECURSOR_ABRUPT_CONSISTENCY_RECOMMENDATION_NAME),
        "forensic_summary": verdict_mod.read_csv(share_dir / verdict_mod.FORENSIC_SUMMARY_NAME),
    }
    return verdict_mod.normalize_frames(frames)


def build_rows(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    workflow_panel_df = verdict_mod.build_workflow_panel_df(frames["workflow"])
    workflow_by_key = verdict_mod.workflow_lookup(workflow_panel_df)
    abrupt_by_key = verdict_mod.abrupt_lookup(frames["abrupt6"])
    same_event_overlap_keys = verdict_mod.load_same_event_overlap_keys(frames)
    forensic_rule_case = verdict_mod.load_forensic_rule_case(frames)
    forensic_rule_key = (verdict_mod.FORENSIC_RULE_SITE, verdict_mod.FORENSIC_RULE_PANEL_ID)

    workflow_keys = set(workflow_by_key.keys())
    abrupt_keys = set(abrupt_by_key.keys())
    pure_abrupt_keys = abrupt_keys - same_event_overlap_keys - {forensic_rule_key}
    precursor_keys = verdict_mod.build_precursor_positive_keys(frames["precursor_truth"])
    precursor_eval_keys = precursor_keys
    abrupt_eval_keys = verdict_mod.build_abrupt_eval_keys(frames["non_precursor_perf"])
    common_keys = verdict_mod.build_common_cause_positive_keys(frames["common_cause"])
    workflow_watch_keys = {
        (verdict_mod.normalize_text(row["site"]), verdict_mod.normalize_text(row["display_entity_id"]))
        for row in workflow_panel_df.loc[
            workflow_panel_df["preview_attention_class"].eq("watch_now_panel")
        ].to_dict(orient="records")
    }
    panel_keys = set().union(workflow_keys, abrupt_keys, precursor_keys, common_keys)

    rows: list[dict[str, object]] = []
    for site, panel_id in sorted(panel_keys):
        key = (site, panel_id)
        flags = {
            "has_전조형고장": int(key in precursor_keys),
            "has_급작고장": int(key in pure_abrupt_keys),
            "has_공통원인이벤트": int(key in common_keys),
            "has_반복이상": int(key in workflow_watch_keys),
        }
        is_same_event_overlap = key in same_event_overlap_keys
        active_forensic_rule_case = forensic_rule_case if key == forensic_rule_key else None
        event_type, terminal_pattern = verdict_mod.event_type_and_terminal_pattern(
            flags,
            is_same_event_overlap=is_same_event_overlap,
            forensic_rule_case=active_forensic_rule_case,
            fault_audit_row=None,
        )
        interpretation = verdict_mod.interpretation_layer_fields(
            flags,
            event_type,
            precursor_eval_flag=int(key in precursor_eval_keys),
            abrupt_eval_flag=int(key in abrupt_eval_keys),
            is_same_event_overlap=is_same_event_overlap,
            forensic_rule_case=active_forensic_rule_case,
            fault_audit_row=None,
        )
        rows.append(
            {
                "site": site,
                "panel_id": panel_id,
                "패널고장여부_ko": verdict_mod.panel_fault_status_from_event_type(event_type),
                "사건유형_ko": event_type,
                "최종고장양상_ko": terminal_pattern,
                "전조흔적_flag": int(interpretation["전조흔적_flag"]),
                "순수급작_flag": int(interpretation["순수급작_flag"]),
                "전조평가셋편입_flag": int(interpretation["전조평가셋편입_flag"]),
                "급작평가셋편입_flag": int(interpretation["급작평가셋편입_flag"]),
            }
        )

    bootstrap_df = pd.DataFrame(rows).reindex(columns=BOOTSTRAP_COLS)
    if bootstrap_df.empty:
        raise SystemExit("bootstrap verdict must not be empty")
    return bootstrap_df


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    status = df["패널고장여부_ko"].map(verdict_mod.normalize_text)
    event = df["사건유형_ko"].map(verdict_mod.normalize_text)
    row = {
        "전체_패널수": int(len(df)),
        "고장_패널수": int(status.eq("고장").sum()),
        "비고장_패널수": int(status.eq("비고장").sum()),
        "미확정_패널수": int(status.eq("미확정").sum()),
        "사건해석_전조형_패널수": int(event.eq("전조형 고장").sum()),
        "사건해석_급작_패널수": int(event.eq("급작 고장").sum()),
        "전조평가셋_편입패널수": int(pd.to_numeric(df["전조평가셋편입_flag"], errors="coerce").fillna(0).sum()),
        "급작평가셋_편입패널수": int(pd.to_numeric(df["급작평가셋편입_flag"], errors="coerce").fillna(0).sum()),
        "note_ko": (
            "이 파일은 runtime chain bootstrapping용 최소 verdict다. "
            "fault_event_audit가 요구하는 현재표 사건유형/최종고장양상/평가셋 편입 상태만 먼저 만든다. "
            "공식 final verdict를 대체하지 않으며, workspace-only bootstrap 입력으로만 사용한다."
        ),
    }
    return pd.DataFrame([row]).reindex(columns=SUMMARY_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    frames = load_frames(root)
    bootstrap_df = build_rows(frames)
    summary_df = build_summary(bootstrap_df)

    bootstrap_path = share_dir / OUTPUT_NAME
    summary_path = share_dir / OUTPUT_SUMMARY_NAME
    bootstrap_df.to_csv(bootstrap_path, index=False, encoding="utf-8-sig")
    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")

    if args.write_panel_verdict_alias:
        bootstrap_df.to_csv(share_dir / ALIAS_NAME, index=False, encoding="utf-8-sig")

    print(f"[OK] wrote bootstrap verdict: {bootstrap_path}")
    if args.write_panel_verdict_alias:
        print(f"[OK] wrote bootstrap verdict alias: {share_dir / ALIAS_NAME}")


if __name__ == "__main__":
    main()
