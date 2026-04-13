#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

TARGET_PANELS = [
    "45dfa600-79b7-428e-95d3-22345a068986.1.1",
    "d15b9e13-4117-49ae-a78f-7ace013e48de.0.0",
    "45dfa600-79b7-428e-95d3-22345a068986.1.0",
    "bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.9",
]

PROJECT_EVAL_MATRIX_NAME = "panel_day_engine_project_eval_matrix_v1.csv"
CURRENT_FREEZE_PACK_NAME = "panel_day_engine_project_current_data_freeze_pack_v1.csv"
CURRENT_CLAIMS_NAME = "panel_day_engine_project_current_data_claims_v1.csv"
PRECURSOR_ONSET_SUMMARY_NAME = "panel_day_engine_precursor_onset_summary_v1.csv"
PRECURSOR_PERFORMANCE_SUMMARY_NAME = "panel_day_engine_precursor_performance_summary_v1.csv"
NON_PRECURSOR_PERFORMANCE_SUMMARY_NAME = "panel_day_engine_non_precursor_performance_summary_v1.csv"
POLICY_RECOMMENDATION_NAME = "panel_day_engine_operator_attention_policy_recommendation_v1.csv"
PIPELINE_MANIFEST_NAME = "panel_day_engine_operator_pipeline_manifest_v1.csv"

OPTIONAL_SECONDARY_DISCOVERY_FATE_NAME = "panel_day_engine_operator_secondary_discovery_fate_cases_v1.csv"
OPTIONAL_LOCAL_SEED_CARRY_FATE_NAME = "panel_day_engine_local_seed_carry_fate_cases_v1.csv"
OPTIONAL_REAUDIT_NAME = "panel_date_reaudit_working.csv"

CASE_REVIEW_OUTPUT_NAME = "panel_day_engine_ae_dtw_case_review_v1.csv"
LATEST_PERF_OUTPUT_NAME = "panel_day_engine_latest_perf_internal_share_v1.csv"
INTERNAL_SHARE_BRIEF_OUTPUT_NAME = "panel_day_engine_internal_share_brief_v1.md"

CASE_REVIEW_COLS = [
    "panel_id",
    "found_flag",
    "site",
    "observed_date_start",
    "observed_date_end",
    "ae_trigger_day_count",
    "dtw_trigger_day_count",
    "hs_trigger_day_count",
    "cond_evt_day_count",
    "pre_alarm_day_count",
    "final_fault_day_count",
    "min_mid_ratio",
    "min_mid_v_ratio",
    "max_v_drop",
    "max_signal_count",
    "max_p95_recon_error",
    "max_site_same_day_pre_alarm_panel_count",
    "max_site_same_day_final_fault_panel_count",
    "무가시형_판정",
    "주된_이상유형_추정",
    "원인_가설_ko",
    "개선안_ko",
    "reason_ko",
]

LATEST_PERF_COLS = [
    "구분",
    "현재_대표기준",
    "양성_표본수",
    "재현율",
    "정밀도",
    "F1",
    "선행시간_중앙값_일",
    "선행시간_범위_일",
    "현재_판정_ko",
]

EXPECTED_FREEZE_SCOPES = [
    "step3_precursor_performance",
    "step4_abrupt_no_precursor",
    "step4_common_cause_routing",
    "operator_policy_proxy",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Produce an internal-share pack with AE/DTW panel case review plus latest precursor-detection metrics."
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


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def read_optional_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def numeric_float_or_blank(value: object) -> float | str:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return "" if pd.isna(numeric) else float(numeric)


def numeric_int(value: object) -> int:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0 if pd.isna(numeric) else int(numeric)


def numeric_min_or_blank(series: pd.Series) -> float | str:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    return "" if numeric.empty else float(numeric.min())


def numeric_max_or_blank(series: pd.Series) -> float | str:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    return "" if numeric.empty else float(numeric.max())


def numeric_quantile_or_blank(series: pd.Series, q: float) -> float | str:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    return "" if numeric.empty else float(numeric.quantile(q))


def flag_series(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(0, index=df.index, dtype="int64")
    raw = df[col]
    numeric = pd.to_numeric(raw, errors="coerce")
    flags = pd.Series(0, index=df.index, dtype="int64")
    numeric_mask = numeric.notna()
    if numeric_mask.any():
        flags.loc[numeric_mask] = numeric.loc[numeric_mask].fillna(0).astype(float).ne(0).astype(int)
    if (~numeric_mask).any():
        text = raw.astype(str).str.strip().str.lower()
        flags.loc[~numeric_mask] = text.loc[~numeric_mask].isin({"1", "true", "t", "yes", "y"}).astype(int)
    return flags


def load_required_share_frames(root: Path) -> dict[str, pd.DataFrame]:
    share_dir = root / "_share"
    frames = {
        "eval_matrix": read_csv(share_dir / PROJECT_EVAL_MATRIX_NAME),
        "freeze_pack": read_csv(share_dir / CURRENT_FREEZE_PACK_NAME),
        "claims": read_csv(share_dir / CURRENT_CLAIMS_NAME),
        "onset_summary": read_csv(share_dir / PRECURSOR_ONSET_SUMMARY_NAME),
        "precursor_perf_summary": read_csv(share_dir / PRECURSOR_PERFORMANCE_SUMMARY_NAME),
        "non_precursor_perf_summary": read_csv(share_dir / NON_PRECURSOR_PERFORMANCE_SUMMARY_NAME),
        "policy": read_csv(share_dir / POLICY_RECOMMENDATION_NAME),
        "pipeline": read_csv(share_dir / PIPELINE_MANIFEST_NAME),
    }

    ensure_columns(
        frames["eval_matrix"],
        ["eval_scope", "target_name", "support_positive", "recall", "precision", "f1", "note_ko"],
        PROJECT_EVAL_MATRIX_NAME,
    )
    ensure_columns(
        frames["freeze_pack"],
        [
            "eval_scope",
            "current_best_target_name",
            "current_best_metric_kind",
            "current_best_f1",
            "current_best_positive_support",
            "current_operational_workflow_name",
            "current_data_decision",
            "allowed_claim_strength",
            "freeze_reason_ko",
        ],
        CURRENT_FREEZE_PACK_NAME,
    )
    ensure_columns(
        frames["claims"],
        ["claim_scope", "claim_text_ko", "claim_strength", "prohibited_overclaim_ko"],
        CURRENT_CLAIMS_NAME,
    )
    ensure_columns(
        frames["onset_summary"],
        ["summary_type", "marker_name", "case_count", "available_case_count", "median_lead_days", "min_lead_days", "max_lead_days"],
        PRECURSOR_ONSET_SUMMARY_NAME,
    )
    ensure_columns(
        frames["precursor_perf_summary"],
        ["marker_name", "case_count", "available_case_count", "median_lead_days", "min_lead_days", "max_lead_days"],
        PRECURSOR_PERFORMANCE_SUMMARY_NAME,
    )
    ensure_columns(
        frames["non_precursor_perf_summary"],
        ["eval_bucket_v2", "case_count", "final_fault_hit_by_anchor_rate", "note_ko"],
        NON_PRECURSOR_PERFORMANCE_SUMMARY_NAME,
    )
    ensure_columns(
        frames["policy"],
        ["recommended_policy_name", "recommended_policy_reason_ko", "expected_use_ko", "caution_ko"],
        POLICY_RECOMMENDATION_NAME,
    )
    ensure_columns(
        frames["pipeline"],
        ["final_pipeline_pass_flag", "note_ko"],
        PIPELINE_MANIFEST_NAME,
    )
    return frames


def load_optional_share_frames(root: Path) -> dict[str, pd.DataFrame | None]:
    share_dir = root / "_share"
    return {
        "secondary_discovery_fate": read_optional_csv(share_dir / OPTIONAL_SECONDARY_DISCOVERY_FATE_NAME),
        "local_seed_carry_fate": read_optional_csv(share_dir / OPTIONAL_LOCAL_SEED_CARRY_FATE_NAME),
        "reaudit": read_optional_csv(share_dir / OPTIONAL_REAUDIT_NAME),
    }


def normalize_frame_text_columns(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    normalized = df.copy()
    for col in cols:
        if col in normalized.columns:
            normalized[col] = normalized[col].map(normalize_text)
    return normalized


def load_site_frames(root: Path) -> dict[str, dict[str, pd.DataFrame | None]]:
    site_frames: dict[str, dict[str, pd.DataFrame | None]] = {}
    for gate_path in sorted(root.glob("data/*/out/ae_simple_local_precursor_gate_daily.csv")):
        site = gate_path.parents[1].name
        core_path = root / "data" / site / "out" / "panel_day_core.csv"
        diag_path = root / "data" / site / "out" / "panel_diagnosis_summary.csv"
        if not core_path.exists():
            continue

        gate_df = read_csv(gate_path)
        core_df = read_csv(core_path)
        diag_df = read_optional_csv(diag_path)

        ensure_columns(gate_df, ["panel_id", "date", "cond_var", "cond_evt", "cond_dtw", "cond_hs", "pre_alarm", "signal_count"], gate_path.name)
        ensure_columns(core_df, ["panel_id", "date", "recon_error", "mid_ratio", "mid_v_ratio", "v_drop", "final_fault"], core_path.name)
        if diag_df is not None:
            ensure_columns(diag_df, ["panel_id"], diag_path.name)

        gate_df = normalize_frame_text_columns(gate_df, ["panel_id", "site", "date"])
        core_df = normalize_frame_text_columns(core_df, ["panel_id", "date", "ae_strength", "anom_subtype"])
        if "site" not in gate_df.columns:
            gate_df["site"] = site
        if diag_df is not None:
            diag_df = normalize_frame_text_columns(diag_df, ["panel_id", "final_fault_first_date", "diagnosis_date_online", "critical_diag_date"])

        pre_alarm_counts = (
            gate_df.loc[flag_series(gate_df, "pre_alarm").eq(1)].groupby("date")["panel_id"].nunique().to_dict()
        )
        final_fault_counts = (
            core_df.loc[flag_series(core_df, "final_fault").eq(1)].groupby("date")["panel_id"].nunique().to_dict()
        )
        site_frames[site] = {
            "gate": gate_df,
            "core": core_df,
            "diag": diag_df,
            "pre_alarm_counts": pre_alarm_counts,
            "final_fault_counts": final_fault_counts,
        }
    return site_frames


def choose_panel_site(site_frames: dict[str, dict[str, pd.DataFrame | None]], panel_id: str) -> str:
    best_site = ""
    best_count = -1
    for site, bundle in site_frames.items():
        gate_df = bundle["gate"]
        core_df = bundle["core"]
        diag_df = bundle["diag"]
        count = int(gate_df["panel_id"].eq(panel_id).sum()) + int(core_df["panel_id"].eq(panel_id).sum())
        if diag_df is not None:
            count += int(diag_df["panel_id"].eq(panel_id).sum())
        if count > best_count:
            best_count = count
            best_site = site
    return best_site if best_count > 0 else ""


def hidden_visibility_label(
    *,
    found_flag: int,
    ae_trigger_day_count: int,
    dtw_trigger_day_count: int,
    cond_evt_day_count: int,
    final_fault_day_count: int,
    min_mid_ratio: float | str,
    min_mid_v_ratio: float | str,
    max_v_drop: float | str,
    max_p95_recon_error: float | str,
) -> str:
    if found_flag != 1:
        return "패널미발견"

    triggered = (ae_trigger_day_count + dtw_trigger_day_count + cond_evt_day_count) > 0
    min_mid_ratio_num = 1.0 if min_mid_ratio == "" else float(min_mid_ratio)
    min_mid_v_ratio_num = 1.0 if min_mid_v_ratio == "" else float(min_mid_v_ratio)
    max_v_drop_num = 0.0 if max_v_drop == "" else float(max_v_drop)
    max_p95_num = 0.0 if max_p95_recon_error == "" else float(max_p95_recon_error)

    mild_proxies = (
        min_mid_ratio_num >= 0.88
        and min_mid_v_ratio_num >= 0.9
        and max_v_drop_num < 0.12
        and max_p95_num < 0.035
    )
    strong_proxies = (
        min_mid_ratio_num < 0.8
        or min_mid_v_ratio_num < 0.8
        or max_v_drop_num >= 0.25
        or max_p95_num >= 0.08
    )

    if triggered and final_fault_day_count == 0 and mild_proxies:
        return "무가시형_가능성_높음"
    if final_fault_day_count > 0 or strong_proxies:
        return "가시형_가능성_있음"
    return "혼합_또는_불충분"


def infer_main_case_type(
    *,
    found_flag: int,
    visibility_label: str,
    ae_trigger_day_count: int,
    dtw_trigger_day_count: int,
    pre_alarm_day_count: int,
    final_fault_day_count: int,
    max_site_same_day_pre_alarm_panel_count: int,
    max_site_same_day_final_fault_panel_count: int,
    reaudit_row: dict[str, object] | None,
    local_seed_rows: list[dict[str, object]],
) -> str:
    if found_flag != 1:
        return "not_found"

    if any("recurring" in normalize_text(row.get("fate_class", "")) for row in local_seed_rows):
        return "recurring_monitor_like"

    if max_site_same_day_pre_alarm_panel_count >= 8 or max_site_same_day_final_fault_panel_count >= 5:
        return "common_cause_or_context_like"

    if visibility_label == "무가시형_가능성_높음":
        return "panel_local_hidden_precursor_like"

    if final_fault_day_count == 0 and pre_alarm_day_count == 0 and (ae_trigger_day_count + dtw_trigger_day_count) <= 3:
        return "output_normal_nuisance_like"

    if pre_alarm_day_count >= 20 or ae_trigger_day_count >= 60 or dtw_trigger_day_count >= 60:
        return "recurring_monitor_like"

    if reaudit_row is not None:
        candidate_validity = normalize_text(reaudit_row.get("candidate_validity"))
        vendor_family = normalize_text(reaudit_row.get("vendor_fault_family"))
        if candidate_validity == "false_positive" or vendor_family == "none_visible":
            return "common_cause_or_context_like"

    return "unclear"


def build_reason_and_action(
    *,
    panel_id: str,
    found_flag: int,
    visibility_label: str,
    main_case_type: str,
    final_fault_day_count: int,
    max_site_same_day_pre_alarm_panel_count: int,
    max_site_same_day_final_fault_panel_count: int,
    reaudit_row: dict[str, object] | None,
    local_seed_rows: list[dict[str, object]],
    secondary_fate_rows: list[dict[str, object]],
) -> tuple[str, str, str]:
    if found_flag != 1:
        return (
            "지정된 panel_id 를 data/*/out 산출물에서 찾지 못했다.",
            "추가 패널 ID 확인 후 동일 검색을 다시 수행",
            "AE/DTW 사례 대상 panel_id 미발견",
        )

    reaudited_none_visible = False
    reaudited_bits: list[str] = []
    if reaudit_row is not None:
        vendor_family = normalize_text(reaudit_row.get("vendor_fault_family"))
        candidate_validity = normalize_text(reaudit_row.get("candidate_validity"))
        vendor_reply_class = normalize_text(reaudit_row.get("vendor_reply_class"))
        note = normalize_text(reaudit_row.get("note"))
        if vendor_family:
            reaudited_bits.append(vendor_family)
        if candidate_validity:
            reaudited_bits.append(candidate_validity)
        if vendor_reply_class:
            reaudited_bits.append(vendor_reply_class)
        if note:
            reaudited_bits.append(note)
        reaudited_none_visible = vendor_family == "none_visible" or candidate_validity == "false_positive"

    if main_case_type == "panel_local_hidden_precursor_like":
        reason = "AE/DTW/cond_evt 는 반복되지만 final fault 와 강한 전기 collapse proxy 는 약해 panel-local hidden precursor 쪽이 더 그럴듯하다."
        action = "hidden precursor 가능 panel은 secondary discovery/value lane 유지"
    elif main_case_type == "recurring_monitor_like":
        reason = "같은 panel 에서 경보 run 이 반복되거나 오래 이어져 monitor lane 성격이 강하다."
        action = "output-normal panel에 대한 monitor lane 분리 유지; AE/DTW 단독 민감도 억제"
    elif main_case_type == "common_cause_or_context_like":
        reason = (
            f"동일 site 의 같은 날 pre_alarm/final_fault 폭이 커서 "
            f"panel-local 단독 이상보다 site/context 영향 가능성이 더 커 보인다 "
            f"(max pre_alarm breadth={max_site_same_day_pre_alarm_panel_count}, max final_fault breadth={max_site_same_day_final_fault_panel_count})."
        )
        action = "site breadth marker와 함께 common-cause 분기; broadshape/recon heavy suppressor 추가 검토"
    elif main_case_type == "output_normal_nuisance_like":
        reason = "AE/DTW 계열 trigger 는 있었지만 출력/전기 drop proxy 가 약해 output-normal nuisance 가능성이 크다."
        action = "AE/DTW 단독 민감도 억제; broadshape/recon heavy suppressor 추가 검토"
    else:
        reason = "전기 proxy, breadth/context, 재감사 문맥이 섞여 현재 자료만으로 한 가지 유형으로 단정하기 어렵다."
        action = "site breadth marker와 함께 common-cause 분기 검토; output-normal panel에 대한 monitor lane 분리 유지"

    if reaudited_none_visible:
        reason += " retrospective re-audit 에서는 vendor_rejected / none_visible / false_positive 쪽 문맥이 있어 현장 가시성은 낮았을 가능성도 같이 남는다."
    elif reaudited_bits:
        reason += f" retrospective re-audit 문맥: {', '.join(reaudited_bits[:3])}."

    if local_seed_rows:
        fate_classes = sorted({normalize_text(row.get('fate_class')) for row in local_seed_rows if normalize_text(row.get('fate_class'))})
        if fate_classes:
            reason += f" local seed carry fate 는 {', '.join(fate_classes)} 로 기록돼 있다."
    elif secondary_fate_rows:
        fate_classes = sorted({normalize_text(row.get('discovery_fate_class')) for row in secondary_fate_rows if normalize_text(row.get('discovery_fate_class'))})
        if fate_classes:
            reason += f" secondary discovery fate 는 {', '.join(fate_classes)} 로 기록돼 있다."

    if visibility_label == "가시형_가능성_있음" and final_fault_day_count > 0:
        action += "; final fault proxy 강도와 breadth를 분리해 panel-local vs context성 재분기"

    reason_ko = "target panel 산출물 탐색 및 heuristic 기반 판정 완료"
    return (reason, action, reason_ko)


def build_case_review(root: Path, optional_frames: dict[str, pd.DataFrame | None]) -> pd.DataFrame:
    site_frames = load_site_frames(root)
    reaudit_df = optional_frames["reaudit"]
    seed_fate_df = optional_frames["local_seed_carry_fate"]
    secondary_fate_df = optional_frames["secondary_discovery_fate"]

    if reaudit_df is not None:
        reaudit_df = normalize_frame_text_columns(reaudit_df, ["panel_id", "vendor_fault_family", "candidate_validity", "vendor_reply_class", "note"])
    if seed_fate_df is not None:
        seed_fate_df = normalize_frame_text_columns(seed_fate_df, ["panel_id", "fate_class", "fate_reason_ko"])
    if secondary_fate_df is not None:
        secondary_fate_df = normalize_frame_text_columns(secondary_fate_df, ["panel_id", "discovery_fate_class", "discovery_fate_reason_ko"])

    rows: list[dict[str, object]] = []
    for panel_id in TARGET_PANELS:
        site = choose_panel_site(site_frames, panel_id)
        if not site:
            rows.append(
                {
                    "panel_id": panel_id,
                    "found_flag": 0,
                    "site": "",
                    "observed_date_start": "",
                    "observed_date_end": "",
                    "ae_trigger_day_count": 0,
                    "dtw_trigger_day_count": 0,
                    "hs_trigger_day_count": 0,
                    "cond_evt_day_count": 0,
                    "pre_alarm_day_count": 0,
                    "final_fault_day_count": 0,
                    "min_mid_ratio": "",
                    "min_mid_v_ratio": "",
                    "max_v_drop": "",
                    "max_signal_count": "",
                    "max_p95_recon_error": "",
                    "max_site_same_day_pre_alarm_panel_count": 0,
                    "max_site_same_day_final_fault_panel_count": 0,
                    "무가시형_판정": "패널미발견",
                    "주된_이상유형_추정": "not_found",
                    "원인_가설_ko": "지정된 panel_id 를 data/*/out 산출물에서 찾지 못했다.",
                    "개선안_ko": "패널 ID 재확인 후 재탐색",
                    "reason_ko": "found_flag=0",
                }
            )
            continue

        bundle = site_frames[site]
        gate_df = bundle["gate"]
        core_df = bundle["core"]
        diag_df = bundle["diag"]
        gate_panel = gate_df.loc[gate_df["panel_id"].eq(panel_id)].copy()
        core_panel = core_df.loc[core_df["panel_id"].eq(panel_id)].copy()
        diag_panel = pd.DataFrame() if diag_df is None else diag_df.loc[diag_df["panel_id"].eq(panel_id)].copy()

        ae_flags = (
            flag_series(gate_panel, "cond_var")
            | flag_series(gate_panel, "prefault_cond_ae")
            | flag_series(gate_panel, "prealarm_cond_ae_mid_or_hi")
        )
        dtw_flags = (
            flag_series(gate_panel, "cond_dtw")
            | flag_series(gate_panel, "prefault_cond_dtw")
            | flag_series(gate_panel, "prealarm_cond_dtw_mid_or_hi")
        )
        hs_flags = flag_series(gate_panel, "cond_hs") | flag_series(gate_panel, "prealarm_cond_hs_mid_or_hi")
        cond_evt_flags = flag_series(gate_panel, "cond_evt")
        pre_alarm_flags = flag_series(gate_panel, "pre_alarm")
        final_fault_flags = flag_series(core_panel, "final_fault")

        active_dates = sorted(
            set(gate_panel.loc[(ae_flags | dtw_flags | hs_flags | cond_evt_flags | pre_alarm_flags).eq(1), "date"])
            | set(core_panel.loc[final_fault_flags.eq(1), "date"])
        )
        if not active_dates:
            active_dates = sorted(set(gate_panel["date"]) | set(core_panel["date"]))

        max_site_same_day_pre_alarm_panel_count = max(
            [int(bundle["pre_alarm_counts"].get(date, 0)) for date in active_dates],
            default=0,
        )
        max_site_same_day_final_fault_panel_count = max(
            [int(bundle["final_fault_counts"].get(date, 0)) for date in active_dates],
            default=0,
        )

        observed_dates = sorted(set(gate_panel["date"]) | set(core_panel["date"]))
        observed_date_start = observed_dates[0] if observed_dates else ""
        observed_date_end = observed_dates[-1] if observed_dates else ""

        ae_trigger_day_count = int(ae_flags.sum())
        dtw_trigger_day_count = int(dtw_flags.sum())
        hs_trigger_day_count = int(hs_flags.sum())
        cond_evt_day_count = int(cond_evt_flags.sum())
        pre_alarm_day_count = int(pre_alarm_flags.sum())
        final_fault_day_count = int(final_fault_flags.sum())
        min_mid_ratio = numeric_min_or_blank(core_panel["mid_ratio"])
        min_mid_v_ratio = numeric_min_or_blank(core_panel["mid_v_ratio"])
        max_v_drop = numeric_max_or_blank(core_panel["v_drop"])
        max_signal_count = numeric_max_or_blank(gate_panel["signal_count"])
        max_p95_recon_error = numeric_quantile_or_blank(core_panel["recon_error"], 0.95)

        reaudit_row = None
        if reaudit_df is not None:
            reaudit_hits = reaudit_df.loc[reaudit_df["panel_id"].eq(panel_id)].copy()
            if not reaudit_hits.empty:
                reaudit_row = reaudit_hits.iloc[0].to_dict()

        local_seed_rows = []
        if seed_fate_df is not None:
            local_seed_rows = seed_fate_df.loc[seed_fate_df["panel_id"].eq(panel_id)].to_dict(orient="records")

        secondary_fate_rows = []
        if secondary_fate_df is not None:
            secondary_fate_rows = secondary_fate_df.loc[secondary_fate_df["panel_id"].eq(panel_id)].to_dict(orient="records")

        visibility_label = hidden_visibility_label(
            found_flag=1,
            ae_trigger_day_count=ae_trigger_day_count,
            dtw_trigger_day_count=dtw_trigger_day_count,
            cond_evt_day_count=cond_evt_day_count,
            final_fault_day_count=final_fault_day_count,
            min_mid_ratio=min_mid_ratio,
            min_mid_v_ratio=min_mid_v_ratio,
            max_v_drop=max_v_drop,
            max_p95_recon_error=max_p95_recon_error,
        )

        main_case_type = infer_main_case_type(
            found_flag=1,
            visibility_label=visibility_label,
            ae_trigger_day_count=ae_trigger_day_count,
            dtw_trigger_day_count=dtw_trigger_day_count,
            pre_alarm_day_count=pre_alarm_day_count,
            final_fault_day_count=final_fault_day_count,
            max_site_same_day_pre_alarm_panel_count=max_site_same_day_pre_alarm_panel_count,
            max_site_same_day_final_fault_panel_count=max_site_same_day_final_fault_panel_count,
            reaudit_row=reaudit_row,
            local_seed_rows=local_seed_rows,
        )
        cause_hypothesis, improvement, reason_ko = build_reason_and_action(
            panel_id=panel_id,
            found_flag=1,
            visibility_label=visibility_label,
            main_case_type=main_case_type,
            final_fault_day_count=final_fault_day_count,
            max_site_same_day_pre_alarm_panel_count=max_site_same_day_pre_alarm_panel_count,
            max_site_same_day_final_fault_panel_count=max_site_same_day_final_fault_panel_count,
            reaudit_row=reaudit_row,
            local_seed_rows=local_seed_rows,
            secondary_fate_rows=secondary_fate_rows,
        )

        if diag_panel is not None and not diag_panel.empty:
            final_fault_first_date = normalize_text(diag_panel.iloc[0].get("final_fault_first_date"))
            if final_fault_first_date:
                cause_hypothesis += f" diagnosis summary 상 첫 final fault date 는 {final_fault_first_date} 다."

        rows.append(
            {
                "panel_id": panel_id,
                "found_flag": 1,
                "site": site,
                "observed_date_start": observed_date_start,
                "observed_date_end": observed_date_end,
                "ae_trigger_day_count": ae_trigger_day_count,
                "dtw_trigger_day_count": dtw_trigger_day_count,
                "hs_trigger_day_count": hs_trigger_day_count,
                "cond_evt_day_count": cond_evt_day_count,
                "pre_alarm_day_count": pre_alarm_day_count,
                "final_fault_day_count": final_fault_day_count,
                "min_mid_ratio": min_mid_ratio,
                "min_mid_v_ratio": min_mid_v_ratio,
                "max_v_drop": max_v_drop,
                "max_signal_count": max_signal_count,
                "max_p95_recon_error": max_p95_recon_error,
                "max_site_same_day_pre_alarm_panel_count": max_site_same_day_pre_alarm_panel_count,
                "max_site_same_day_final_fault_panel_count": max_site_same_day_final_fault_panel_count,
                "무가시형_판정": visibility_label,
                "주된_이상유형_추정": main_case_type,
                "원인_가설_ko": cause_hypothesis,
                "개선안_ko": improvement,
                "reason_ko": reason_ko,
            }
        )

    return pd.DataFrame(rows, columns=CASE_REVIEW_COLS)


def find_eval_row(eval_df: pd.DataFrame, scope: str, target_name: str) -> dict[str, object]:
    matches = eval_df.loc[
        eval_df["eval_scope"].eq(scope)
        & eval_df["target_name"].eq(target_name)
    ].copy()
    if matches.empty:
        raise SystemExit(f"missing eval row for scope={scope}, target={target_name}")
    return matches.iloc[0].to_dict()


def lead_time_from_marker(
    marker_name: str,
    onset_summary_df: pd.DataFrame,
    precursor_perf_df: pd.DataFrame,
) -> tuple[float | str, str]:
    perf_matches = precursor_perf_df.loc[precursor_perf_df["marker_name"].eq(marker_name)].copy()
    if not perf_matches.empty:
        row = perf_matches.iloc[0]
        median = numeric_float_or_blank(row["median_lead_days"])
        min_lead = numeric_float_or_blank(row["min_lead_days"])
        max_lead = numeric_float_or_blank(row["max_lead_days"])
        if median != "" and min_lead != "" and max_lead != "":
            return (median, f"{min_lead:g}~{max_lead:g}")

    onset_matches = onset_summary_df.loc[
        onset_summary_df["summary_type"].eq("onset_marker") & onset_summary_df["marker_name"].eq(marker_name)
    ].copy()
    if onset_matches.empty:
        return ("", "")
    row = onset_matches.iloc[0]
    median = numeric_float_or_blank(row["median_lead_days"])
    min_lead = numeric_float_or_blank(row["min_lead_days"])
    max_lead = numeric_float_or_blank(row["max_lead_days"])
    if median == "" or min_lead == "" or max_lead == "":
        return ("", "")
    return (median, f"{min_lead:g}~{max_lead:g}")


def judgment_for_perf_row(
    *,
    row_kind: str,
    freeze_row: dict[str, object] | None,
    claim_row: dict[str, object] | None,
    policy_row: dict[str, object],
    pipeline_row: dict[str, object],
) -> str:
    if row_kind == "전조형 고장":
        return "표본이 2건이라 최신 수치는 탐색적으로만 읽어야 한다."
    if row_kind == "급작 고장":
        return "현재 데이터 기준에서는 급작 고장 쪽이 가장 상대적으로 안정적이지만 bounded use 로만 본다."
    if row_kind == "common-cause routing":
        return "common-cause routing 은 descriptive/exploratory 수준으로만 유지한다."
    pipeline_pass = numeric_int(pipeline_row["final_pipeline_pass_flag"])
    return (
        f"{normalize_text(policy_row['recommended_policy_name'])} 는 packaging/QA/pipeline 검증을 거쳐 운영용으로는 사용할 수 있다 "
        f"(pipeline pass={pipeline_pass}). detector 일반 성능으로 과장하면 안 된다."
    )


def build_latest_perf_table(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    eval_df = normalize_frame_text_columns(frames["eval_matrix"], ["eval_scope", "target_name", "metric_kind"])
    freeze_df = normalize_frame_text_columns(frames["freeze_pack"], ["eval_scope", "current_best_target_name", "current_operational_workflow_name", "current_data_decision", "allowed_claim_strength"])
    claims_df = normalize_frame_text_columns(frames["claims"], ["claim_scope", "claim_text_ko", "claim_strength"])
    onset_summary_df = normalize_frame_text_columns(frames["onset_summary"], ["summary_type", "marker_name"])
    precursor_perf_df = normalize_frame_text_columns(frames["precursor_perf_summary"], ["marker_name"])
    policy_row = {key: normalize_text(value) for key, value in frames["policy"].iloc[0].to_dict().items()}
    pipeline_row = frames["pipeline"].iloc[0].to_dict()

    freeze_lookup = {normalize_text(row["eval_scope"]): row for row in freeze_df.to_dict(orient="records")}
    claim_lookup = {normalize_text(row["claim_scope"]): row for row in claims_df.to_dict(orient="records")}

    missing_scopes = sorted(set(EXPECTED_FREEZE_SCOPES) - set(freeze_lookup))
    if missing_scopes:
        raise SystemExit(f"freeze pack missing scopes: {missing_scopes}")

    precursor_target = normalize_text(freeze_lookup["step3_precursor_performance"]["current_best_target_name"])
    abrupt_target = normalize_text(freeze_lookup["step4_abrupt_no_precursor"]["current_best_target_name"])
    common_target = normalize_text(freeze_lookup["step4_common_cause_routing"]["current_best_target_name"])
    workflow_name = normalize_text(freeze_lookup["operator_policy_proxy"].get("current_operational_workflow_name")) or normalize_text(policy_row["recommended_policy_name"])

    precursor_eval = find_eval_row(eval_df, "step3_precursor_performance", precursor_target)
    abrupt_eval = find_eval_row(eval_df, "step4_abrupt_no_precursor", abrupt_target)
    common_eval = find_eval_row(eval_df, "step4_common_cause_routing", common_target)
    workflow_eval = find_eval_row(eval_df, "operator_policy_proxy", workflow_name)

    precursor_lead_median, precursor_lead_range = lead_time_from_marker(precursor_target, onset_summary_df, precursor_perf_df)

    rows = [
        {
            "구분": "전조형 고장",
            "현재_대표기준": precursor_target,
            "양성_표본수": numeric_float_or_blank(precursor_eval["support_positive"]),
            "재현율": numeric_float_or_blank(precursor_eval["recall"]),
            "정밀도": numeric_float_or_blank(precursor_eval["precision"]),
            "F1": numeric_float_or_blank(precursor_eval["f1"]),
            "선행시간_중앙값_일": precursor_lead_median,
            "선행시간_범위_일": precursor_lead_range,
            "현재_판정_ko": judgment_for_perf_row(
                row_kind="전조형 고장",
                freeze_row=freeze_lookup["step3_precursor_performance"],
                claim_row=claim_lookup.get("step3_precursor_performance"),
                policy_row=policy_row,
                pipeline_row=pipeline_row,
            ),
        },
        {
            "구분": "급작 고장",
            "현재_대표기준": abrupt_target,
            "양성_표본수": numeric_float_or_blank(abrupt_eval["support_positive"]),
            "재현율": numeric_float_or_blank(abrupt_eval["recall"]),
            "정밀도": numeric_float_or_blank(abrupt_eval["precision"]),
            "F1": numeric_float_or_blank(abrupt_eval["f1"]),
            "선행시간_중앙값_일": "",
            "선행시간_범위_일": "",
            "현재_판정_ko": judgment_for_perf_row(
                row_kind="급작 고장",
                freeze_row=freeze_lookup["step4_abrupt_no_precursor"],
                claim_row=claim_lookup.get("step4_abrupt_no_precursor"),
                policy_row=policy_row,
                pipeline_row=pipeline_row,
            ),
        },
        {
            "구분": "common-cause routing",
            "현재_대표기준": common_target,
            "양성_표본수": numeric_float_or_blank(common_eval["support_positive"]),
            "재현율": numeric_float_or_blank(common_eval["recall"]),
            "정밀도": numeric_float_or_blank(common_eval["precision"]),
            "F1": numeric_float_or_blank(common_eval["f1"]),
            "선행시간_중앙값_일": "",
            "선행시간_범위_일": "",
            "현재_판정_ko": judgment_for_perf_row(
                row_kind="common-cause routing",
                freeze_row=freeze_lookup["step4_common_cause_routing"],
                claim_row=claim_lookup.get("step4_common_cause_routing"),
                policy_row=policy_row,
                pipeline_row=pipeline_row,
            ),
        },
        {
            "구분": "운영 workflow",
            "현재_대표기준": workflow_name,
            "양성_표본수": numeric_float_or_blank(workflow_eval["support_positive"]),
            "재현율": numeric_float_or_blank(workflow_eval["recall"]),
            "정밀도": numeric_float_or_blank(workflow_eval["precision"]),
            "F1": numeric_float_or_blank(workflow_eval["f1"]),
            "선행시간_중앙값_일": "",
            "선행시간_범위_일": "",
            "현재_판정_ko": judgment_for_perf_row(
                row_kind="운영 workflow",
                freeze_row=freeze_lookup["operator_policy_proxy"],
                claim_row=claim_lookup.get("operator_policy_proxy"),
                policy_row=policy_row,
                pipeline_row=pipeline_row,
            ),
        },
    ]
    return pd.DataFrame(rows, columns=LATEST_PERF_COLS)


def build_internal_share_brief(
    case_review_df: pd.DataFrame,
    latest_perf_df: pd.DataFrame,
    frames: dict[str, pd.DataFrame],
) -> str:
    found_df = case_review_df.loc[case_review_df["found_flag"].eq(1)].copy()
    if found_df.empty:
        case_line = "- 지정된 4개 panel 을 current 산출물에서 찾지 못했다. panel ID 재확인이 먼저 필요하다."
    else:
        hidden_counts = found_df["무가시형_판정"].value_counts().to_dict()
        type_counts = found_df["주된_이상유형_추정"].value_counts().to_dict()
        case_line = (
            f"- 이번 대상 {len(found_df)}개 panel 은 모두 current 산출물에서 잡혔고, "
            f"무가시형 판정은 {hidden_counts.get('무가시형_가능성_높음', 0)}건 hidden-high / "
            f"{hidden_counts.get('가시형_가능성_있음', 0)}건 visible-like / "
            f"{hidden_counts.get('혼합_또는_불충분', 0)}건 mixed 였다."
        )
        if type_counts:
            dominant_type = sorted(type_counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
            case_line += f" 현재 사례상 주된 패턴은 {dominant_type} 쪽으로 보인다."

    perf_lookup = {normalize_text(row["구분"]): row for row in latest_perf_df.to_dict(orient="records")}
    precursor_row = perf_lookup["전조형 고장"]
    abrupt_row = perf_lookup["급작 고장"]
    workflow_row = perf_lookup["운영 workflow"]

    perf_line = (
        f"- 전조형은 {normalize_text(precursor_row['현재_대표기준'])} 기준 R/P/F1="
        f"{precursor_row['재현율']}/{precursor_row['정밀도']}/{precursor_row['F1']}, "
        f"중앙 선행 {precursor_row['선행시간_중앙값_일']}일이지만 표본이 작아 탐색적이다. "
        f"급작 고장은 {normalize_text(abrupt_row['현재_대표기준'])} 기준 "
        f"R/P/F1={abrupt_row['재현율']}/{abrupt_row['정밀도']}/{abrupt_row['F1']} 로 "
        f"현재 데이터 기준에서는 가장 상대적으로 안정적이다."
    )

    policy_row = frames["policy"].iloc[0].to_dict()
    workflow_name = normalize_text(policy_row["recommended_policy_name"])
    pipeline_pass = numeric_int(frames["pipeline"].iloc[0]["final_pipeline_pass_flag"])
    governance_line = (
        f"- 말해도 되는 것: operator workflow {workflow_name} 는 packaging/QA/pipeline 검증이 끝나 운영용으로는 사용할 수 있다 "
        f"(pipeline pass={pipeline_pass}). 말하면 안 되는 것: 이 workflow 검증이나 step3 전조형 수치를 detector 일반 성능으로 과장하면 안 된다."
    )

    return "\n".join(
        [
            "## 1. AE/DTW 사례 요약",
            case_line,
            "",
            "## 2. 최신 성능 한 줄 요약",
            perf_line,
            "",
            "## 3. 지금 당장 말해도 되는 것 / 말하면 안 되는 것",
            governance_line,
            "",
        ]
    )


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    required_frames = load_required_share_frames(root)
    optional_frames = load_optional_share_frames(root)
    case_review_df = build_case_review(root, optional_frames)
    latest_perf_df = build_latest_perf_table(required_frames)
    brief_text = build_internal_share_brief(case_review_df, latest_perf_df, required_frames)

    case_review_df.to_csv(share_dir / CASE_REVIEW_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    latest_perf_df.to_csv(share_dir / LATEST_PERF_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    (share_dir / INTERNAL_SHARE_BRIEF_OUTPUT_NAME).write_text(brief_text, encoding="utf-8")


if __name__ == "__main__":
    main()
