#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


DEFAULT_SITES = ["conalog", "gangui", "ktc_ess"]
RAW_CANDIDATE_NAME = "ae_simple_fault_candidates.csv"
CROSS_AXIS_NAME = "panel_day_engine_cross_axis_manifest_sync_review_v1.csv"
RAW_AUDIT_NAME = "panel_day_engine_runtime_fault_event_audit_v1.csv"
RAW_HEURISTIC_NAME = "panel_day_engine_runtime_cause_candidate_heuristics_v1.csv"
RAW_FINAL_NAME = "panel_day_engine_runtime_final_verdict_v1.csv"
LIVE_HEURISTIC_NAME = "panel_day_engine_cause_candidate_heuristics_v1.csv"
LIVE_MULTIAXIS_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
GPVS_PACK_NAME = "panel_day_engine_gpvs_evidence_pack_v1.csv"
CURRENT_RESULT_NAMES = [
    "fault_panel_result_current_v1.csv",
    "fault_panel_result_current_preview_v1.csv",
    "fault_panel_result_raw_only_current_v1.csv",
    "fault_panel_result_raw_only_current_preview_v1.csv",
]
PRECURSOR_RESULT_NAME = "fault_panel_result_precursor_report_v1.csv"
RAW_SIGNAL_RESULT_NAME = "fault_panel_result_raw_only_fault_signal_report_v1.csv"
TARGET_TOP1_TERMS = {"제어응답형", "장치 응답 이상형", "전력변환부 이상형"}
DEVICE_RESPONSE_EXTERNAL = "장치 응답 이상형"
SENSOR_FEEDBACK_TOP1 = "센서·피드백형"
LOCAL_SIGNAL_BUCKET = "local_signal_morphology_review"
DETAIL_OUTPUT_NAME = "panel_day_engine_local_morphology_exact_seed_search_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_local_morphology_exact_seed_search_summary_v1.csv"
RAW_BOOL_COLS = [
    "pre_ews",
    "prefault_B",
    "prefault_B_effective",
    "fault_like_day",
    "final_fault",
    "critical_fault",
    "recovered_any",
    "recovered_sustained",
    "re_drop",
    "site_event_soft",
    "site_event_hard",
    "group_off_date",
    "group_off_like",
    "subgroup_common_cause_candidate",
    "prefault_B_common_cause_overlap",
]
DETAIL_COLS = [
    "site",
    "panel_id",
    "source_review_focus_bucket",
    "recovery_bucket",
    "recovery_best_report_lane",
    "synchrony_bucket",
    "synchrony_best_report_lane",
    "anchor_dates",
    "raw_candidate_row_count",
    "raw_signal_row_count",
    "raw_recovery_row_count",
    "same_day_signal_row_count",
    "same_day_recovery_row_count",
    "same_day_re_drop_row_count",
    "same_day_recovered_sustained_row_count",
    "same_day_fault_like_row_count",
    "same_day_final_fault_row_count",
    "same_day_common_cause_row_count",
    "same_day_dates",
    "raw_top1_ko",
    "raw_top1_score",
    "raw_top2_ko",
    "raw_top3_ko",
    "raw_empirical_priority_ko",
    "raw_confidence_ko",
    "live_top1_ko",
    "live_top1_score",
    "live_top2_ko",
    "live_top3_ko",
    "live_external_gpvs_ko",
    "live_confidence_ko",
    "final_external_gpvs_ko",
    "gpvs_pack_external_ko",
    "target_exact_top1_flag",
    "device_response_external_flag",
    "sensor_feedback_top1_flag",
    "recovery_recurrence_flag",
    "exact_same_day_local_morphology_flag",
    "common_cause_exclusion_flag",
    "supportive_seed_candidate_flag",
    "exact_family_candidate_flag",
    "search_status",
    "search_note",
]
SUMMARY_COLS = [
    "search_status",
    "site",
    "panels",
    "exact_family_candidates",
    "supportive_seed_candidates",
    "target_exact_top1_panels",
    "device_response_external_panels",
    "sensor_feedback_top1_panels",
    "same_day_local_morphology_panels",
    "same_day_re_drop_panels",
    "common_cause_excluded_panels",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Search exact-family missing seeds from the local_signal_morphology_review pool, "
            "without promoting common-cause-dominant cases."
        )
    )
    parser.add_argument("--cross-axis-root", type=Path, required=True, help="Root containing cross-axis review CSV.")
    parser.add_argument("--data-root", type=Path, required=True, help="Folder containing <site>/out/ae_simple_fault_candidates.csv.")
    parser.add_argument("--result-root", type=Path, required=True, help="Folder containing runtime result report CSVs.")
    parser.add_argument("--raw-only-share-root", type=Path, required=True, help="Raw-only chain _share root.")
    parser.add_argument("--live-share-root", type=Path, required=False, default=None, help="Optional live-chain _share root.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Folder where seed search CSVs will be written.")
    parser.add_argument("--sites", nargs="*", default=DEFAULT_SITES, help="Sites to scan.")
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def normalize_date_text(value: object) -> str:
    text = normalize_text(value)
    candidate = text[:10] if len(text) >= 10 else text
    return candidate if re.fullmatch(r"\d{4}-\d{2}-\d{2}", candidate) else ""


def to_flag(value: object) -> int:
    text = normalize_text(value).lower()
    if text in {"1", "true", "t", "yes", "y"}:
        return 1
    if text in {"0", "false", "f", "no", "n", ""}:
        return 0
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0 if pd.isna(numeric) else int(float(numeric) > 0)


def read_csv(path: Path, required: bool = True) -> pd.DataFrame:
    if not path.exists():
        if required:
            raise SystemExit(f"missing input: {path}")
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def add_missing_columns(df: pd.DataFrame, cols: list[str], default: object = 0) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        if col not in out.columns:
            out[col] = default
    return out


def join_unique(values: list[str]) -> str:
    return "|".join(sorted({value for value in values if value}))


def read_raw_candidates(data_root: Path, sites: list[str]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for site in sites:
        path = data_root / site / "out" / RAW_CANDIDATE_NAME
        df = read_csv(path)
        df = add_missing_columns(df, RAW_BOOL_COLS, default=0)
        if "date" not in df.columns or "panel_id" not in df.columns:
            raise SystemExit(f"{path} missing required date/panel_id columns")
        df = df.copy()
        df["site"] = site
        df["panel_id"] = df["panel_id"].map(normalize_text)
        df["date"] = df["date"].map(normalize_date_text)
        for col in RAW_BOOL_COLS:
            df[col] = df[col].map(to_flag)
        df["raw_signal_flag"] = df[["pre_ews", "prefault_B", "prefault_B_effective", "fault_like_day", "final_fault", "critical_fault"]].sum(axis=1).gt(0).astype(int)
        df["raw_recovery_flag"] = df[["recovered_any", "recovered_sustained", "re_drop"]].sum(axis=1).gt(0).astype(int)
        df["raw_common_cause_flag"] = df[["site_event_soft", "site_event_hard", "group_off_date", "group_off_like", "subgroup_common_cause_candidate", "prefault_B_common_cause_overlap"]].sum(axis=1).gt(0).astype(int)
        frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def read_keyed(path: Path, cols: list[str]) -> pd.DataFrame:
    df = read_csv(path, required=False)
    if df.empty or "site" not in df.columns or "panel_id" not in df.columns:
        return pd.DataFrame(columns=["site", "panel_id"] + cols)
    out = add_missing_columns(df, cols, default="")
    out["site"] = out["site"].map(normalize_text)
    out["panel_id"] = out["panel_id"].map(normalize_text)
    return out[["site", "panel_id"] + cols].drop_duplicates(["site", "panel_id"], keep="first")


def build_report_date_map(result_root: Path) -> dict[tuple[str, str], set[str]]:
    date_cols = ["고장 기준일", "고장날짜", "전조날짜", "전조 시작일", "신호 기준일", "세부fault_기준일"]
    names = CURRENT_RESULT_NAMES + [PRECURSOR_RESULT_NAME, RAW_SIGNAL_RESULT_NAME]
    out: dict[tuple[str, str], set[str]] = {}
    for name in names:
        df = read_csv(result_root / name, required=False)
        if df.empty or "site" not in df.columns or "panel_id" not in df.columns:
            continue
        for row in df.to_dict(orient="records"):
            key = (normalize_text(row.get("site")), normalize_text(row.get("panel_id")))
            if not key[0] or not key[1]:
                continue
            bucket = out.setdefault(key, set())
            for col in date_cols:
                if col in row:
                    value = normalize_date_text(row.get(col))
                    if value:
                        bucket.add(value)
    return out


def date_set_from_row(row: pd.Series, cols: list[str]) -> set[str]:
    values = set()
    for col in cols:
        if col in row.index:
            value = normalize_date_text(row.get(col))
            if value:
                values.add(value)
    return values


def contains_target_top1(*values: object) -> int:
    texts = {normalize_text(value) for value in values if normalize_text(value)}
    return int(bool(texts & TARGET_TOP1_TERMS))


def contains_text(target: str, *values: object) -> int:
    return int(any(normalize_text(value) == target for value in values))


def classify_row(row: dict[str, object]) -> tuple[str, str]:
    exact_top1 = int(row["target_exact_top1_flag"]) == 1
    same_day_local = int(row["exact_same_day_local_morphology_flag"]) == 1
    device_external = int(row["device_response_external_flag"]) == 1
    recovery = int(row["recovery_recurrence_flag"]) == 1
    sensor_top1 = int(row["sensor_feedback_top1_flag"]) == 1
    raw_top1 = normalize_text(row["raw_top1_ko"])
    live_top1 = normalize_text(row["live_top1_ko"])

    if int(row["common_cause_exclusion_flag"]) == 1:
        return "excluded_common_cause_review", "common-cause bucket leaked into the pool; keep excluded."
    if exact_top1 and same_day_local:
        return "exact_family_candidate", "target top1 and same-day local morphology both exist."
    if device_external and recovery and same_day_local:
        return "supportive_device_response_recovery_seed", "device-response external reference plus local recovery morphology exists, but top1 target is still absent."
    if sensor_top1 and recovery and same_day_local:
        return "sensor_feedback_local_morphology_candidate", "sensor-feedback top1 with same-day local morphology is useful pressure, not target exact closure."
    if not raw_top1 and not live_top1:
        return "no_report_heuristic_match", "local morphology exists but no cause heuristic row is attached."
    if same_day_local:
        return "same_day_local_non_target", "same-day local morphology exists but target top1/device-response condition is absent."
    return "local_morphology_non_exact", "local morphology pool row exists, but exact same-day morphology condition is weak."


def build_detail(args: argparse.Namespace) -> pd.DataFrame:
    sites = [normalize_text(site) for site in args.sites if normalize_text(site)]
    cross_df = read_csv(args.cross_axis_root / CROSS_AXIS_NAME)
    local_df = cross_df.loc[cross_df["review_focus_bucket"].eq(LOCAL_SIGNAL_BUCKET)].copy()
    if local_df.empty:
        return pd.DataFrame(columns=DETAIL_COLS)
    local_df["site"] = local_df["site"].map(normalize_text)
    local_df["panel_id"] = local_df["panel_id"].map(normalize_text)

    raw_candidates = read_raw_candidates(args.data_root, sites)
    raw_audit = read_keyed(
        args.raw_only_share_root / RAW_AUDIT_NAME,
        [
            "strict_trigger_date",
            "first_final_fault_date",
            "retrospective_onset_date",
            "대표critical_source",
            "대표anom_subtype",
            "algorithm_family_ko",
            "detailed_fault_label_ko",
        ],
    )
    raw_heur = read_keyed(
        args.raw_only_share_root / RAW_HEURISTIC_NAME,
        [
            "원인후보_top1_ko",
            "원인후보_top1_score",
            "원인후보_top2_ko",
            "원인후보_top3_ko",
            "원인후보_실증우선확인_ko",
            "원인후보_신뢰도_ko",
            "GPVS_외부참조패턴_ko",
        ],
    )
    raw_final = read_keyed(
        args.raw_only_share_root / RAW_FINAL_NAME,
        ["세부fault_기준일", "운영최초전조발견일", "사건해석상전조시작일", "GPVS_외부참조패턴_ko"],
    )

    live_heur = pd.DataFrame(columns=["site", "panel_id"])
    live_multi = pd.DataFrame(columns=["site", "panel_id"])
    gpvs_pack = pd.DataFrame(columns=["site", "panel_id"])
    if args.live_share_root is not None:
        live_heur = read_keyed(
            args.live_share_root / LIVE_HEURISTIC_NAME,
            [
                "원인후보_top1_ko",
                "원인후보_top1_score",
                "원인후보_top2_ko",
                "원인후보_top3_ko",
                "원인후보_신뢰도_ko",
                "GPVS_외부참조패턴_ko",
            ],
        )
        live_multi = read_keyed(
            args.live_share_root / LIVE_MULTIAXIS_NAME,
            ["GPVS_외부참조패턴_ko", "대표판정_ko", "세부fault_type_label_ko"],
        )
        gpvs_pack = read_keyed(args.live_share_root / GPVS_PACK_NAME, ["GPVS_외부참조패턴_ko"])

    report_date_map = build_report_date_map(args.result_root)

    rows: list[dict[str, object]] = []
    for panel in local_df.to_dict(orient="records"):
        site = normalize_text(panel["site"])
        panel_id = normalize_text(panel["panel_id"])
        key = (site, panel_id)
        panel_raw = raw_candidates.loc[(raw_candidates["site"].eq(site)) & (raw_candidates["panel_id"].eq(panel_id))]
        audit_row = raw_audit.loc[(raw_audit["site"].eq(site)) & (raw_audit["panel_id"].eq(panel_id))]
        raw_heur_row = raw_heur.loc[(raw_heur["site"].eq(site)) & (raw_heur["panel_id"].eq(panel_id))]
        raw_final_row = raw_final.loc[(raw_final["site"].eq(site)) & (raw_final["panel_id"].eq(panel_id))]
        live_heur_row = live_heur.loc[(live_heur["site"].eq(site)) & (live_heur["panel_id"].eq(panel_id))]
        live_multi_row = live_multi.loc[(live_multi["site"].eq(site)) & (live_multi["panel_id"].eq(panel_id))]
        gpvs_pack_row = gpvs_pack.loc[(gpvs_pack["site"].eq(site)) & (gpvs_pack["panel_id"].eq(panel_id))]

        audit_s = audit_row.iloc[0] if not audit_row.empty else pd.Series(dtype=object)
        raw_heur_s = raw_heur_row.iloc[0] if not raw_heur_row.empty else pd.Series(dtype=object)
        raw_final_s = raw_final_row.iloc[0] if not raw_final_row.empty else pd.Series(dtype=object)
        live_heur_s = live_heur_row.iloc[0] if not live_heur_row.empty else pd.Series(dtype=object)
        live_multi_s = live_multi_row.iloc[0] if not live_multi_row.empty else pd.Series(dtype=object)
        gpvs_pack_s = gpvs_pack_row.iloc[0] if not gpvs_pack_row.empty else pd.Series(dtype=object)

        anchor_dates = set(report_date_map.get(key, set()))
        anchor_dates |= date_set_from_row(audit_s, ["strict_trigger_date", "first_final_fault_date", "retrospective_onset_date"])
        anchor_dates |= date_set_from_row(raw_final_s, ["세부fault_기준일", "운영최초전조발견일", "사건해석상전조시작일"])
        same_day_raw = panel_raw.loc[panel_raw["date"].isin(anchor_dates)] if anchor_dates else panel_raw.iloc[0:0]

        raw_top1 = normalize_text(raw_heur_s.get("원인후보_top1_ko", ""))
        raw_top2 = normalize_text(raw_heur_s.get("원인후보_top2_ko", ""))
        raw_top3 = normalize_text(raw_heur_s.get("원인후보_top3_ko", ""))
        live_top1 = normalize_text(live_heur_s.get("원인후보_top1_ko", ""))
        live_top2 = normalize_text(live_heur_s.get("원인후보_top2_ko", ""))
        live_top3 = normalize_text(live_heur_s.get("원인후보_top3_ko", ""))
        live_external = normalize_text(live_heur_s.get("GPVS_외부참조패턴_ko", "")) or normalize_text(live_multi_s.get("GPVS_외부참조패턴_ko", ""))
        gpvs_pack_external = normalize_text(gpvs_pack_s.get("GPVS_외부참조패턴_ko", ""))
        final_external = normalize_text(raw_final_s.get("GPVS_외부참조패턴_ko", ""))

        same_day_signal = int(same_day_raw["raw_signal_flag"].sum())
        same_day_recovery = int(same_day_raw["raw_recovery_flag"].sum())
        same_day_re_drop = int(same_day_raw["re_drop"].sum())
        same_day_sustained = int(same_day_raw["recovered_sustained"].sum())
        same_day_fault_like = int(same_day_raw["fault_like_day"].sum())
        same_day_final = int(same_day_raw["final_fault"].sum())
        same_day_common = int(same_day_raw["raw_common_cause_flag"].sum())
        same_day_dates = sorted(same_day_raw.loc[(same_day_raw["raw_signal_flag"].eq(1)) | (same_day_raw["raw_recovery_flag"].eq(1)), "date"].unique().tolist())

        target_exact_top1 = contains_target_top1(raw_top1, live_top1)
        device_external = contains_text(DEVICE_RESPONSE_EXTERNAL, live_external, final_external, gpvs_pack_external)
        sensor_top1 = contains_text(SENSOR_FEEDBACK_TOP1, raw_top1, live_top1)
        recovery_flag = int(normalize_text(panel.get("recovery_bucket")) in {"re_drop_cycle", "persistent_non_recovery", "sustained_recovery"})
        same_day_local = int((same_day_signal + same_day_recovery + same_day_re_drop + same_day_sustained) > 0)
        common_cause_exclusion = int(normalize_text(panel.get("review_focus_bucket")) != LOCAL_SIGNAL_BUCKET)

        row = {
            "site": site,
            "panel_id": panel_id,
            "source_review_focus_bucket": normalize_text(panel.get("review_focus_bucket")),
            "recovery_bucket": normalize_text(panel.get("recovery_bucket")),
            "recovery_best_report_lane": normalize_text(panel.get("recovery_best_report_lane")),
            "synchrony_bucket": normalize_text(panel.get("synchrony_bucket")),
            "synchrony_best_report_lane": normalize_text(panel.get("synchrony_best_report_lane")),
            "anchor_dates": join_unique(sorted(anchor_dates)),
            "raw_candidate_row_count": int(len(panel_raw)),
            "raw_signal_row_count": int(panel_raw["raw_signal_flag"].sum()) if not panel_raw.empty else 0,
            "raw_recovery_row_count": int(panel_raw["raw_recovery_flag"].sum()) if not panel_raw.empty else 0,
            "same_day_signal_row_count": same_day_signal,
            "same_day_recovery_row_count": same_day_recovery,
            "same_day_re_drop_row_count": same_day_re_drop,
            "same_day_recovered_sustained_row_count": same_day_sustained,
            "same_day_fault_like_row_count": same_day_fault_like,
            "same_day_final_fault_row_count": same_day_final,
            "same_day_common_cause_row_count": same_day_common,
            "same_day_dates": join_unique(same_day_dates),
            "raw_top1_ko": raw_top1,
            "raw_top1_score": raw_heur_s.get("원인후보_top1_score", ""),
            "raw_top2_ko": raw_top2,
            "raw_top3_ko": raw_top3,
            "raw_empirical_priority_ko": normalize_text(raw_heur_s.get("원인후보_실증우선확인_ko", "")),
            "raw_confidence_ko": normalize_text(raw_heur_s.get("원인후보_신뢰도_ko", "")),
            "live_top1_ko": live_top1,
            "live_top1_score": live_heur_s.get("원인후보_top1_score", ""),
            "live_top2_ko": live_top2,
            "live_top3_ko": live_top3,
            "live_external_gpvs_ko": live_external,
            "live_confidence_ko": normalize_text(live_heur_s.get("원인후보_신뢰도_ko", "")),
            "final_external_gpvs_ko": final_external,
            "gpvs_pack_external_ko": gpvs_pack_external,
            "target_exact_top1_flag": target_exact_top1,
            "device_response_external_flag": device_external,
            "sensor_feedback_top1_flag": sensor_top1,
            "recovery_recurrence_flag": recovery_flag,
            "exact_same_day_local_morphology_flag": same_day_local,
            "common_cause_exclusion_flag": common_cause_exclusion,
            "supportive_seed_candidate_flag": int(device_external and recovery_flag and same_day_local and not target_exact_top1),
            "exact_family_candidate_flag": int(target_exact_top1 and same_day_local and not common_cause_exclusion),
        }
        status, note = classify_row(row)
        row["search_status"] = status
        row["search_note"] = note
        rows.append(row)

    return pd.DataFrame(rows, columns=DETAIL_COLS).sort_values(["search_status", "site", "panel_id"], kind="stable")


def summarize(detail_df: pd.DataFrame) -> pd.DataFrame:
    if detail_df.empty:
        return pd.DataFrame(columns=SUMMARY_COLS)
    summary = (
        detail_df.groupby(["search_status", "site"], as_index=False)
        .agg(
            panels=("panel_id", "nunique"),
            exact_family_candidates=("exact_family_candidate_flag", "sum"),
            supportive_seed_candidates=("supportive_seed_candidate_flag", "sum"),
            target_exact_top1_panels=("target_exact_top1_flag", "sum"),
            device_response_external_panels=("device_response_external_flag", "sum"),
            sensor_feedback_top1_panels=("sensor_feedback_top1_flag", "sum"),
            same_day_local_morphology_panels=("exact_same_day_local_morphology_flag", "sum"),
            same_day_re_drop_panels=("same_day_re_drop_row_count", lambda s: int((s > 0).sum())),
            common_cause_excluded_panels=("common_cause_exclusion_flag", "sum"),
        )
    )
    return summary.reindex(columns=SUMMARY_COLS).sort_values(["search_status", "site"], kind="stable")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    detail_df = build_detail(args)
    summary_df = summarize(detail_df)
    detail_df.to_csv(args.output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
