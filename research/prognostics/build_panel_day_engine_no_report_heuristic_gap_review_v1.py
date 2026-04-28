#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import pandas as pd


DEFAULT_SITES = ["conalog", "gangui", "ktc_ess"]
LOCAL_SEARCH_NAME = "panel_day_engine_local_morphology_exact_seed_search_v1.csv"
RAW_CANDIDATE_NAME = "ae_simple_fault_candidates.csv"
RAW_AUDIT_NAME = "panel_day_engine_runtime_fault_event_audit_v1.csv"
RAW_FINAL_NAME = "panel_day_engine_runtime_final_verdict_v1.csv"
RAW_HEURISTIC_NAME = "panel_day_engine_runtime_cause_candidate_heuristics_v1.csv"
CURRENT_RESULT_NAMES = [
    "fault_panel_result_current_v1.csv",
    "fault_panel_result_current_preview_v1.csv",
    "fault_panel_result_raw_only_current_v1.csv",
    "fault_panel_result_raw_only_current_preview_v1.csv",
]
PRECURSOR_RESULT_NAME = "fault_panel_result_precursor_report_v1.csv"
RAW_SIGNAL_RESULT_NAME = "fault_panel_result_raw_only_fault_signal_report_v1.csv"
DETAIL_OUTPUT_NAME = "panel_day_engine_no_report_heuristic_gap_review_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_no_report_heuristic_gap_review_summary_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_no_report_heuristic_gap_review_note_v1.md"
TARGET_STATUS = "no_report_heuristic_match"
RAW_FLAG_COLS = [
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
    "source_search_status",
    "recovery_bucket",
    "synchrony_bucket",
    "anchor_dates",
    "raw_candidate_dates",
    "nearest_raw_candidate_date",
    "nearest_anchor_date",
    "min_abs_gap_days",
    "gap_direction",
    "date_alignment_gap_type",
    "raw_candidate_row_count",
    "raw_signal_row_count",
    "raw_recovery_row_count",
    "raw_pre_ews_row_count",
    "raw_prefault_B_effective_row_count",
    "raw_fault_like_row_count",
    "raw_final_fault_row_count",
    "raw_critical_fault_row_count",
    "raw_re_drop_row_count",
    "raw_common_cause_row_count",
    "signal_basis_type",
    "raw_audit_status_ko",
    "raw_final_status_ko",
    "raw_audit_event_type_ko",
    "raw_audit_anom_subtype",
    "raw_audit_critical_source",
    "raw_heuristic_row_present_flag",
    "current_report_row_present_flag",
    "precursor_report_row_present_flag",
    "raw_signal_report_row_present_flag",
    "any_operator_report_row_present_flag",
    "report_attachment_gap_type",
    "heuristic_attachment_gap_type",
    "judgment_role",
    "engine_patch_candidate_flag",
    "report_patch_candidate_flag",
    "recommended_next_action",
    "review_note",
]
SUMMARY_COLS = [
    "heuristic_attachment_gap_type",
    "report_attachment_gap_type",
    "date_alignment_gap_type",
    "site",
    "panels",
    "engine_patch_candidates",
    "report_patch_candidates",
    "near_anchor_panels",
    "date_displaced_panels",
    "hard_fault_signal_panels",
    "non_fault_status_panels",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Decompose no_report_heuristic_match rows into report-lane, date-alignment, and heuristic-gate causes."
    )
    parser.add_argument("--local-search-root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--raw-only-share-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sites", nargs="*", default=DEFAULT_SITES)
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def normalize_date_text(value: object) -> str:
    text = normalize_text(value)
    candidate = text[:10] if len(text) >= 10 else text
    try:
        date.fromisoformat(candidate)
    except ValueError:
        return ""
    return candidate


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


def add_missing_columns(df: pd.DataFrame, cols: list[str], default: object = "") -> pd.DataFrame:
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
        df = add_missing_columns(df, RAW_FLAG_COLS, default=0)
        df["site"] = site
        df["panel_id"] = df["panel_id"].map(normalize_text)
        df["date"] = df["date"].map(normalize_date_text)
        for col in RAW_FLAG_COLS:
            df[col] = df[col].map(to_flag)
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


def read_report_presence(result_root: Path) -> dict[str, set[tuple[str, str]]]:
    report_files = {
        "current": CURRENT_RESULT_NAMES,
        "precursor": [PRECURSOR_RESULT_NAME],
        "raw_signal": [RAW_SIGNAL_RESULT_NAME],
    }
    out: dict[str, set[tuple[str, str]]] = {name: set() for name in report_files}
    for report_name, names in report_files.items():
        for name in names:
            df = read_csv(result_root / name, required=False)
            if df.empty or "site" not in df.columns or "panel_id" not in df.columns:
                continue
            for row in df[["site", "panel_id"]].drop_duplicates().to_dict(orient="records"):
                site = normalize_text(row["site"])
                panel_id = normalize_text(row["panel_id"])
                if site and panel_id:
                    out[report_name].add((site, panel_id))
    return out


def date_gap(anchor_dates: set[str], raw_dates: set[str]) -> tuple[str, str, int | None, str]:
    if not anchor_dates or not raw_dates:
        return "", "", None, "no_comparable_dates"
    best: tuple[int, str, str, int] | None = None
    for anchor in anchor_dates:
        anchor_date = date.fromisoformat(anchor)
        for raw in raw_dates:
            raw_date = date.fromisoformat(raw)
            gap = (raw_date - anchor_date).days
            item = (abs(gap), anchor, raw, gap)
            if best is None or item < best:
                best = item
    assert best is not None
    _, anchor, raw, gap = best
    if gap == 0:
        direction = "exact"
    elif gap > 0:
        direction = "raw_after_anchor"
    else:
        direction = "raw_before_anchor"
    return raw, anchor, gap, direction


def classify_date_alignment(gap_days: int | None) -> str:
    if gap_days is None:
        return "no_comparable_dates"
    abs_gap = abs(gap_days)
    if abs_gap == 0:
        return "exact_anchor"
    if abs_gap <= 3:
        return "near_anchor_1_3d"
    if abs_gap <= 14:
        return "near_window_4_14d"
    return "date_displaced_gt14d"


def classify_signal_basis(row_counts: dict[str, int]) -> str:
    hard = row_counts["fault_like"] + row_counts["final_fault"] + row_counts["critical_fault"]
    if hard > 0:
        return "hard_fault_signal_present"
    if row_counts["pre_ews"] > 0 and row_counts["recovery"] > 0:
        return "early_warning_plus_recovery"
    if row_counts["pre_ews"] > 0:
        return "early_warning_only"
    if row_counts["recovery"] > 0:
        return "recovery_only"
    return "weak_or_unclassified_raw_signal"


def classify_row(row: dict[str, object]) -> tuple[str, str, str, int, int, str, str]:
    status = normalize_text(row["raw_final_status_ko"]) or normalize_text(row["raw_audit_status_ko"])
    hard_signal = int(row["raw_fault_like_row_count"]) + int(row["raw_final_fault_row_count"]) + int(row["raw_critical_fault_row_count"])
    any_report = int(row["any_operator_report_row_present_flag"])
    date_gap_type = normalize_text(row["date_alignment_gap_type"])
    heur_present = int(row["raw_heuristic_row_present_flag"]) == 1

    if heur_present:
        heuristic_gap = "heuristic_already_attached"
    elif status != "고장":
        heuristic_gap = "expected_absent_non_fault_status_gate"
    elif hard_signal > 0:
        heuristic_gap = "unexpected_missing_for_fault_signal"
    else:
        heuristic_gap = "unexpected_missing_for_fault_status"

    if any_report:
        report_gap = "operator_report_attached_elsewhere"
    elif status != "고장":
        report_gap = "final_verdict_all_rows_only_non_fault"
    else:
        report_gap = "missing_operator_report_for_fault"

    if heuristic_gap.startswith("unexpected"):
        judgment = "potential_engine_or_heuristic_join_bug"
        engine_patch = 1
        report_patch = int(not any_report)
        action = "investigate_engine_or_heuristic_join_before_rule_patch"
    elif date_gap_type == "near_anchor_1_3d":
        judgment = "evidence_only_near_anchor_non_fault_morphology"
        engine_patch = 0
        report_patch = 1
        action = "consider_report_observation_sidecar_not_engine_patch"
    elif date_gap_type == "date_displaced_gt14d":
        judgment = "evidence_only_date_displaced_morphology"
        engine_patch = 0
        report_patch = 0
        action = "keep_as_date_displaced_sidecar_evidence"
    else:
        judgment = "evidence_only_non_fault_morphology"
        engine_patch = 0
        report_patch = 0
        action = "keep_evidence_only_until_fault_status_or_exact_family_changes"

    note = (
        f"status={status or 'blank'}, hard_signal_rows={hard_signal}, "
        f"date_gap_type={date_gap_type}, heuristic_gap={heuristic_gap}, report_gap={report_gap}"
    )
    return heuristic_gap, report_gap, judgment, engine_patch, report_patch, action, note


def build_detail(args: argparse.Namespace) -> pd.DataFrame:
    sites = [normalize_text(site) for site in args.sites if normalize_text(site)]
    local = read_csv(args.local_search_root / LOCAL_SEARCH_NAME)
    local = local.loc[local["search_status"].map(normalize_text).eq(TARGET_STATUS)].copy()
    if local.empty:
        return pd.DataFrame(columns=DETAIL_COLS)
    local["site"] = local["site"].map(normalize_text)
    local["panel_id"] = local["panel_id"].map(normalize_text)

    raw_candidates = read_raw_candidates(args.data_root, sites)
    raw_audit = read_keyed(
        args.raw_only_share_root / RAW_AUDIT_NAME,
        [
            "패널고장여부_ko",
            "사건유형_재판정_ko",
            "대표anom_subtype",
            "대표critical_source",
        ],
    )
    raw_final = read_keyed(args.raw_only_share_root / RAW_FINAL_NAME, ["패널고장여부_ko"])
    raw_heur = read_keyed(args.raw_only_share_root / RAW_HEURISTIC_NAME, ["원인후보_top1_ko"])
    reports = read_report_presence(args.result_root)

    rows: list[dict[str, object]] = []
    for item in local.to_dict(orient="records"):
        site = normalize_text(item["site"])
        panel_id = normalize_text(item["panel_id"])
        key = (site, panel_id)
        panel_raw = raw_candidates.loc[raw_candidates["site"].eq(site) & raw_candidates["panel_id"].eq(panel_id)]
        audit_hit = raw_audit.loc[raw_audit["site"].eq(site) & raw_audit["panel_id"].eq(panel_id)]
        final_hit = raw_final.loc[raw_final["site"].eq(site) & raw_final["panel_id"].eq(panel_id)]
        heur_hit = raw_heur.loc[raw_heur["site"].eq(site) & raw_heur["panel_id"].eq(panel_id)]
        audit = audit_hit.iloc[0] if not audit_hit.empty else pd.Series(dtype=object)
        final = final_hit.iloc[0] if not final_hit.empty else pd.Series(dtype=object)

        anchor_dates = {value for value in normalize_text(item.get("anchor_dates")).split("|") if normalize_date_text(value)}
        raw_dates = set(panel_raw["date"].dropna().map(normalize_date_text).tolist()) if not panel_raw.empty else set()
        nearest_raw, nearest_anchor, signed_gap, direction = date_gap(anchor_dates, raw_dates)
        date_alignment = classify_date_alignment(signed_gap)
        current_present = int(key in reports["current"])
        precursor_present = int(key in reports["precursor"])
        raw_signal_present = int(key in reports["raw_signal"])
        any_report = int(current_present or precursor_present or raw_signal_present)

        row_counts = {
            "signal": int(
                panel_raw[["pre_ews", "prefault_B", "prefault_B_effective", "fault_like_day", "final_fault", "critical_fault"]]
                .sum(axis=1)
                .gt(0)
                .sum()
            )
            if not panel_raw.empty
            else 0,
            "recovery": int(panel_raw[["recovered_any", "recovered_sustained", "re_drop"]].sum(axis=1).gt(0).sum())
            if not panel_raw.empty
            else 0,
            "pre_ews": int(panel_raw["pre_ews"].sum()) if not panel_raw.empty else 0,
            "prefault_B_effective": int(panel_raw["prefault_B_effective"].sum()) if not panel_raw.empty else 0,
            "fault_like": int(panel_raw["fault_like_day"].sum()) if not panel_raw.empty else 0,
            "final_fault": int(panel_raw["final_fault"].sum()) if not panel_raw.empty else 0,
            "critical_fault": int(panel_raw["critical_fault"].sum()) if not panel_raw.empty else 0,
            "re_drop": int(panel_raw["re_drop"].sum()) if not panel_raw.empty else 0,
            "common_cause": int(
                panel_raw[
                    [
                        "site_event_soft",
                        "site_event_hard",
                        "group_off_date",
                        "group_off_like",
                        "subgroup_common_cause_candidate",
                        "prefault_B_common_cause_overlap",
                    ]
                ]
                .sum(axis=1)
                .gt(0)
                .sum()
            )
            if not panel_raw.empty
            else 0,
        }

        row = {
            "site": site,
            "panel_id": panel_id,
            "source_search_status": TARGET_STATUS,
            "recovery_bucket": normalize_text(item.get("recovery_bucket")),
            "synchrony_bucket": normalize_text(item.get("synchrony_bucket")),
            "anchor_dates": join_unique(sorted(anchor_dates)),
            "raw_candidate_dates": join_unique(sorted(raw_dates)),
            "nearest_raw_candidate_date": nearest_raw,
            "nearest_anchor_date": nearest_anchor,
            "min_abs_gap_days": "" if signed_gap is None else abs(signed_gap),
            "gap_direction": direction,
            "date_alignment_gap_type": date_alignment,
            "raw_candidate_row_count": int(len(panel_raw)),
            "raw_signal_row_count": row_counts["signal"],
            "raw_recovery_row_count": row_counts["recovery"],
            "raw_pre_ews_row_count": row_counts["pre_ews"],
            "raw_prefault_B_effective_row_count": row_counts["prefault_B_effective"],
            "raw_fault_like_row_count": row_counts["fault_like"],
            "raw_final_fault_row_count": row_counts["final_fault"],
            "raw_critical_fault_row_count": row_counts["critical_fault"],
            "raw_re_drop_row_count": row_counts["re_drop"],
            "raw_common_cause_row_count": row_counts["common_cause"],
            "signal_basis_type": classify_signal_basis(row_counts),
            "raw_audit_status_ko": normalize_text(audit.get("패널고장여부_ko", "")),
            "raw_final_status_ko": normalize_text(final.get("패널고장여부_ko", "")),
            "raw_audit_event_type_ko": normalize_text(audit.get("사건유형_재판정_ko", "")),
            "raw_audit_anom_subtype": normalize_text(audit.get("대표anom_subtype", "")),
            "raw_audit_critical_source": normalize_text(audit.get("대표critical_source", "")),
            "raw_heuristic_row_present_flag": int(not heur_hit.empty),
            "current_report_row_present_flag": current_present,
            "precursor_report_row_present_flag": precursor_present,
            "raw_signal_report_row_present_flag": raw_signal_present,
            "any_operator_report_row_present_flag": any_report,
        }
        heuristic_gap, report_gap, judgment, engine_patch, report_patch, action, note = classify_row(row)
        row["report_attachment_gap_type"] = report_gap
        row["heuristic_attachment_gap_type"] = heuristic_gap
        row["judgment_role"] = judgment
        row["engine_patch_candidate_flag"] = engine_patch
        row["report_patch_candidate_flag"] = report_patch
        row["recommended_next_action"] = action
        row["review_note"] = note
        rows.append(row)

    return pd.DataFrame(rows, columns=DETAIL_COLS).sort_values(["site", "panel_id"], kind="stable")


def summarize(detail: pd.DataFrame) -> pd.DataFrame:
    if detail.empty:
        return pd.DataFrame(columns=SUMMARY_COLS)
    out = (
        detail.groupby(
            ["heuristic_attachment_gap_type", "report_attachment_gap_type", "date_alignment_gap_type", "site"],
            as_index=False,
        )
        .agg(
            panels=("panel_id", "nunique"),
            engine_patch_candidates=("engine_patch_candidate_flag", "sum"),
            report_patch_candidates=("report_patch_candidate_flag", "sum"),
            near_anchor_panels=("date_alignment_gap_type", lambda s: int(s.eq("near_anchor_1_3d").sum())),
            date_displaced_panels=("date_alignment_gap_type", lambda s: int(s.eq("date_displaced_gt14d").sum())),
            hard_fault_signal_panels=("signal_basis_type", lambda s: int(s.eq("hard_fault_signal_present").sum())),
            non_fault_status_panels=("raw_final_status_ko", lambda s: int(s.ne("고장").sum())),
        )
    )
    return out.reindex(columns=SUMMARY_COLS).sort_values(
        ["heuristic_attachment_gap_type", "site", "date_alignment_gap_type"], kind="stable"
    )


def write_note(output_dir: Path, detail: pd.DataFrame, summary: pd.DataFrame) -> None:
    total = int(detail["panel_id"].nunique()) if not detail.empty else 0
    engine_candidates = int(detail["engine_patch_candidate_flag"].sum()) if not detail.empty else 0
    report_candidates = int(detail["report_patch_candidate_flag"].sum()) if not detail.empty else 0
    heuristic_counts = detail["heuristic_attachment_gap_type"].value_counts().to_dict() if not detail.empty else {}
    date_counts = detail["date_alignment_gap_type"].value_counts().to_dict() if not detail.empty else {}
    lines = [
        "# panel_day_engine_no_report_heuristic_gap_review_v1",
        "",
        "## Summary",
        f"- reviewed_panels: {total}",
        f"- engine_patch_candidate_sum: {engine_candidates}",
        f"- report_patch_candidate_sum: {report_candidates}",
        f"- heuristic_gap_counts: {heuristic_counts}",
        f"- date_alignment_counts: {date_counts}",
        "",
        "## Decision Use",
        "- `engine_patch_candidate_flag=1` means investigate engine or heuristic join before any rule patch.",
        "- `report_patch_candidate_flag=1` means possible observation/report sidecar work, not automatic operator-facing promotion.",
        "- `expected_absent_non_fault_status_gate` means the current heuristic absence is explained by the deterministic fault-status filter.",
    ]
    if not summary.empty:
        header = list(summary.columns)
        lines.extend(["", "## Summary Table", "| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * len(header)) + " |"])
        for row in summary.to_dict(orient="records"):
            lines.append("| " + " | ".join(normalize_text(row.get(col)) for col in header) + " |")
    output_dir.joinpath(NOTE_OUTPUT_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    detail = build_detail(args)
    summary = summarize(detail)
    detail.to_csv(args.output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(args.output_dir, detail, summary)


if __name__ == "__main__":
    main()
