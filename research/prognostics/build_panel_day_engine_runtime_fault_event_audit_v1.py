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


AUDIT_COLS = [
    "site",
    "panel_id",
    "현재표_사건유형_ko",
    "현재표_최종고장양상_ko",
    "earliest_warning_date",
    "retrospective_onset_date",
    "strict_trigger_date",
    "first_final_fault_date",
    "dead_diag_date",
    "onset_confidence",
    "onset_method",
    "전조흔적_flag",
    "순수급작_flag",
    "전조평가셋편입_flag",
    "급작평가셋편입_flag",
    "사건유형_재판정_ko",
    "최종고장양상_재판정_ko",
    "재판정_근거_ko",
    "현재표_보정필요여부_flag",
    "패널고장여부_ko",
    "대표critical_source",
    "대표anom_level",
    "대표anom_subtype",
    "algorithm_family_ko",
    "algorithm_symptom_ko",
    "detailed_fault_code",
    "detailed_fault_label_ko",
    "gap_days",
    "degradation_onset_backdate_guard_flag",
    "degradation_onset_backdate_guard_name",
    "degradation_onset_backdate_guard_reason",
    "degradation_onset_backdate_guard_degrade_days",
]
SUMMARY_COLS = [
    "전체_패널수",
    "고장_패널수",
    "비고장_패널수",
    "미확정_패널수",
    "전조형_고장수",
    "급작_고장수",
    "전조평가셋_패널수",
    "급작평가셋_패널수",
    "algorithm_family_다이오드형_패널수",
    "algorithm_family_개방장치이상형_패널수",
    "algorithm_family_모듈손상형_패널수",
    "algorithm_family_불충분_패널수",
    "note_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a raw-only runtime fault-event audit from panel_day_core and "
            "ae_simple_local_precursor_gate_daily without frozen truth/support assets."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Workspace root containing data/<site>/out.",
    )
    return parser.parse_args()


def build_rows(root: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for site in common.discover_sites(root):
        core_df, gate_df = common.load_site_outputs(root, site)
        for panel_id in common.panel_keys(core_df, gate_df):
            metrics = common.compute_panel_metrics(site, panel_id, core_df, gate_df)
            rows.append(
                {
                    "site": metrics.site,
                    "panel_id": metrics.panel_id,
                    "현재표_사건유형_ko": metrics.사건유형_재판정_ko,
                    "현재표_최종고장양상_ko": metrics.최종고장양상_재판정_ko,
                    "earliest_warning_date": metrics.earliest_warning_date,
                    "retrospective_onset_date": metrics.retrospective_onset_date,
                    "strict_trigger_date": metrics.strict_trigger_date,
                    "first_final_fault_date": metrics.first_final_fault_date,
                    "dead_diag_date": metrics.dead_diag_date,
                    "onset_confidence": metrics.onset_confidence,
                    "onset_method": metrics.onset_method,
                    "전조흔적_flag": metrics.전조흔적_flag,
                    "순수급작_flag": metrics.순수급작_flag,
                    "전조평가셋편입_flag": metrics.전조평가셋편입_flag,
                    "급작평가셋편입_flag": metrics.급작평가셋편입_flag,
                    "사건유형_재판정_ko": metrics.사건유형_재판정_ko,
                    "최종고장양상_재판정_ko": metrics.최종고장양상_재판정_ko,
                    "재판정_근거_ko": metrics.재판정_근거_ko,
                    "현재표_보정필요여부_flag": metrics.현재표_보정필요여부_flag,
                    "패널고장여부_ko": metrics.패널고장여부_ko,
                    "대표critical_source": metrics.대표critical_source,
                    "대표anom_level": metrics.대표anom_level,
                    "대표anom_subtype": metrics.대표anom_subtype,
                    "algorithm_family_ko": metrics.algorithm_family_ko,
                    "algorithm_symptom_ko": metrics.algorithm_symptom_ko,
                    "detailed_fault_code": metrics.detailed_fault_code,
                    "detailed_fault_label_ko": metrics.detailed_fault_label_ko,
                    "gap_days": metrics.gap_days,
                    "degradation_onset_backdate_guard_flag": int(
                        metrics.degradation_onset_backdate_guard_flag
                    ),
                    "degradation_onset_backdate_guard_name": (
                        metrics.degradation_onset_backdate_guard_name
                    ),
                    "degradation_onset_backdate_guard_reason": (
                        metrics.degradation_onset_backdate_guard_reason
                    ),
                    "degradation_onset_backdate_guard_degrade_days": (
                        metrics.degradation_onset_backdate_guard_degrade_days
                    ),
                }
            )
    if not rows:
        raise SystemExit("runtime fault-event audit must not be empty")
    return pd.DataFrame(rows).reindex(columns=AUDIT_COLS).sort_values(["site", "panel_id"]).reset_index(drop=True)


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    row = {
        "전체_패널수": int(len(df)),
        "고장_패널수": int(df["패널고장여부_ko"].map(common.normalize_text).eq("고장").sum()),
        "비고장_패널수": int(df["패널고장여부_ko"].map(common.normalize_text).eq("비고장").sum()),
        "미확정_패널수": int(df["패널고장여부_ko"].map(common.normalize_text).eq("미확정").sum()),
        "전조형_고장수": int(df["사건유형_재판정_ko"].map(common.normalize_text).eq("전조형 고장").sum()),
        "급작_고장수": int(df["사건유형_재판정_ko"].map(common.normalize_text).eq("급작 고장").sum()),
        "전조평가셋_패널수": int(pd.to_numeric(df["전조평가셋편입_flag"], errors="coerce").fillna(0).sum()),
        "급작평가셋_패널수": int(pd.to_numeric(df["급작평가셋편입_flag"], errors="coerce").fillna(0).sum()),
        "algorithm_family_다이오드형_패널수": int(df["algorithm_family_ko"].map(common.normalize_text).eq("다이오드형").sum()),
        "algorithm_family_개방장치이상형_패널수": int(df["algorithm_family_ko"].map(common.normalize_text).eq("개방/장치이상형").sum()),
        "algorithm_family_모듈손상형_패널수": int(df["algorithm_family_ko"].map(common.normalize_text).eq("모듈손상형").sum()),
        "algorithm_family_불충분_패널수": int(df["algorithm_family_ko"].map(common.normalize_text).eq("불충분").sum()),
        "note_ko": (
            "이 runtime audit는 raw-only 경로다. panel_day_core와 precursor gate만 사용하며, "
            "수동 truth/adjudication/frozen audit snapshot은 참조하지 않는다."
        ),
    }
    return pd.DataFrame([row]).reindex(columns=SUMMARY_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    audit_df = build_rows(root)
    summary_df = build_summary(audit_df)

    audit_path = share_dir / common.RUNTIME_AUDIT_OUTPUT_NAME
    summary_path = share_dir / common.RUNTIME_AUDIT_SUMMARY_NAME
    audit_df.to_csv(audit_path, index=False, encoding="utf-8-sig")
    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
    print(f"[OK] wrote runtime raw-only audit: {audit_path}")


if __name__ == "__main__":
    main()
