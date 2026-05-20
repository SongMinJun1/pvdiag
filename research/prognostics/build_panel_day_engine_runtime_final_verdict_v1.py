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


VERDICT_COLS = [
    "site",
    "panel_id",
    "사건유형_ko",
    "사건유형_해석_ko",
    "최종고장양상_ko",
    "대표판정_ko",
    "사건이력_ko",
    "전조흔적_flag",
    "순수급작_flag",
    "전조평가셋편입_flag",
    "급작평가셋편입_flag",
    "해석대평가차이_ko",
    "운영최초전조발견일",
    "운영최초전조마커",
    "사건해석상전조시작일",
    "benchmark전조시작일",
    "전조형이력_flag",
    "급작고장이력_flag",
    "공통원인이력_flag",
    "반복이상이력_flag",
    "패널고장여부_ko",
    "GPVS_적용대상_ko",
    "커널로그_증상명_ko",
    "커널로그_원인군_ko",
    "GPVS_부착상태_ko",
    "GPVS_내부참고유형_ko",
    "GPVS_외부참조패턴_ko",
    "GPVS_참조사용등급_ko",
    "GPVS_참조설명_ko",
    "세부fault_type_code",
    "세부fault_type_label_ko",
    "세부fault_부착상태_ko",
    "세부fault_근거파일_ko",
    "세부fault_기준일",
    "세부fault_보류사유_ko",
    "운영위치_ko",
    "판정주의_ko",
]
SUMMARY_COLS = [
    "전체_패널수",
    "고장_패널수",
    "비고장_패널수",
    "미확정_패널수",
    "전조형_고장수",
    "급작_고장수",
    "커널로그_원인군_다이오드형_패널수",
    "커널로그_원인군_개방장치이상형_패널수",
    "커널로그_원인군_모듈손상형_패널수",
    "커널로그_원인군_불충분_패널수",
    "note_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a raw-only runtime final verdict. Column names are preserved where practical, "
            "but 커널로그_원인군_ko is algorithm-derived from panel_day_core/gate."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Workspace root containing _share runtime audit and data/<site>/out.",
    )
    return parser.parse_args()


def build_rows(audit_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for row in audit_df.to_dict(orient="records"):
        status = common.normalize_text(row.get("패널고장여부_ko"))
        event_type = common.normalize_text(row.get("사건유형_재판정_ko"))
        terminal = common.normalize_text(row.get("최종고장양상_재판정_ko"))
        family = common.normalize_text(row.get("algorithm_family_ko"))
        if status == "고장":
            representative = event_type or "고장"
            event_history = event_type or "고장"
        elif status == "미확정":
            representative = "미확정"
            event_history = "반복 이상"
        else:
            representative = "비고장"
            event_history = "비고장"
        rows.append(
            {
                "site": common.normalize_text(row.get("site")),
                "panel_id": common.normalize_text(row.get("panel_id")),
                "사건유형_ko": event_type,
                "사건유형_해석_ko": event_type,
                "최종고장양상_ko": terminal,
                "대표판정_ko": representative,
                "사건이력_ko": event_history,
                "전조흔적_flag": int(row.get("전조흔적_flag") or 0),
                "순수급작_flag": int(row.get("순수급작_flag") or 0),
                "전조평가셋편입_flag": int(row.get("전조평가셋편입_flag") or 0),
                "급작평가셋편입_flag": int(row.get("급작평가셋편입_flag") or 0),
                "해석대평가차이_ko": "",
                "운영최초전조발견일": common.normalize_text(row.get("earliest_warning_date")),
                "운영최초전조마커": common.normalize_text(row.get("onset_method")),
                "사건해석상전조시작일": common.normalize_text(row.get("retrospective_onset_date")),
                "benchmark전조시작일": "",
                "전조형이력_flag": int(event_type == "전조형 고장"),
                "급작고장이력_flag": int(event_type == "급작 고장"),
                "공통원인이력_flag": int(row.get("common_cause_history_flag") or 0),
                "반복이상이력_flag": int(status == "미확정"),
                "패널고장여부_ko": status,
                "GPVS_적용대상_ko": "raw-only 미사용",
                "커널로그_증상명_ko": common.normalize_text(row.get("algorithm_symptom_ko")),
                "커널로그_원인군_ko": family,
                "GPVS_부착상태_ko": "raw-only 미사용",
                "GPVS_내부참고유형_ko": "",
                "GPVS_외부참조패턴_ko": "",
                "GPVS_참조사용등급_ko": "",
                "GPVS_참조설명_ko": "raw-only strict chain에서는 GPVS reference를 사용하지 않음",
                "세부fault_type_code": common.normalize_text(row.get("detailed_fault_code")),
                "세부fault_type_label_ko": common.normalize_text(row.get("detailed_fault_label_ko")),
                "세부fault_부착상태_ko": "algorithm-derived" if family else "",
                "세부fault_근거파일_ko": "panel_day_core.csv + ae_simple_local_precursor_gate_daily.csv" if family else "",
                "세부fault_기준일": common.normalize_text(row.get("strict_trigger_date")) or common.normalize_text(row.get("first_final_fault_date")),
                "세부fault_보류사유_ko": "" if family and family != "불충분" else "raw-only family confidence limited",
                "운영위치_ko": "raw-only runtime",
                "판정주의_ko": (
                    "커널로그_원인군_ko 컬럼명은 유지하지만, 의미는 raw-only algorithm-derived family로 해석해야 한다. "
                    "수동 truth/frozen label을 참조하지 않는다."
                ),
            }
        )
    return pd.DataFrame(rows).reindex(columns=VERDICT_COLS).sort_values(["site", "panel_id"]).reset_index(drop=True)


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    families = df["커널로그_원인군_ko"].map(common.normalize_text)
    row = {
        "전체_패널수": int(len(df)),
        "고장_패널수": int(df["패널고장여부_ko"].map(common.normalize_text).eq("고장").sum()),
        "비고장_패널수": int(df["패널고장여부_ko"].map(common.normalize_text).eq("비고장").sum()),
        "미확정_패널수": int(df["패널고장여부_ko"].map(common.normalize_text).eq("미확정").sum()),
        "전조형_고장수": int(df["사건유형_ko"].map(common.normalize_text).eq("전조형 고장").sum()),
        "급작_고장수": int(df["사건유형_ko"].map(common.normalize_text).eq("급작 고장").sum()),
        "커널로그_원인군_다이오드형_패널수": int(families.eq("다이오드형").sum()),
        "커널로그_원인군_개방장치이상형_패널수": int(families.eq("개방/장치이상형").sum()),
        "커널로그_원인군_모듈손상형_패널수": int(families.eq("모듈손상형").sum()),
        "커널로그_원인군_불충분_패널수": int(families.eq("불충분").sum()),
        "note_ko": (
            "runtime final verdict는 raw-only strict chain용이다. "
            "커널로그_원인군_ko는 algorithm-derived family이며, 기존 frozen label field와 의미가 다를 수 있다."
        ),
    }
    return pd.DataFrame([row]).reindex(columns=SUMMARY_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    audit_path = share_dir / common.RUNTIME_AUDIT_OUTPUT_NAME
    audit_df = common.read_csv(audit_path)
    summary_dir = share_dir

    verdict_df = build_rows(audit_df)
    summary_df = build_summary(verdict_df)

    verdict_path = summary_dir / common.RUNTIME_VERDICT_OUTPUT_NAME
    summary_path = summary_dir / common.RUNTIME_VERDICT_SUMMARY_NAME
    verdict_df.to_csv(verdict_path, index=False, encoding="utf-8-sig")
    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
    print(f"[OK] wrote runtime raw-only verdict: {verdict_path}")


if __name__ == "__main__":
    main()
