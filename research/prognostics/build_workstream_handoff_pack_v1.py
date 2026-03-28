#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
SUMMARY_COLS = [
    "baseline_guard_status",
    "freeze_recommendation",
    "strict_maintenance_f1",
    "strict_operational_f1",
    "lenient_maintenance_f1",
    "lenient_operational_f1",
    "official_scored_count",
    "manual_scored_count",
    "vendor_scored_count",
    "deferred_hold_count",
    "active_review_queue_count",
    "precursor_global_recommendation",
    "next_workstream_recommendation",
]
SITE_COLS = [
    "site",
    "site_status",
    "official_scored_count",
    "manual_scored_count",
    "vendor_scored_count",
    "deferred_hold_count",
    "precursor_site_recommendation",
    "handoff_note_ko",
]
OPEN_THREAD_COLS = [
    "thread_key",
    "thread_status",
    "owner_needed",
    "reactivation_condition",
    "note_ko",
]
REQUIRED_DECISION_KEYS = [
    "official_baseline_status",
    "active_truth_review_queue",
    "deferred_high_actionability_rows",
    "global_precursor_addon",
    "conalog_precursor_note",
    "next_workstream_recommendation",
]
KEY_COLS = ["site", "panel_id", "strict_trigger_date"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bundle the frozen baseline state into a concise workstream handoff pack."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to project root.",
    )
    parser.add_argument(
        "--sites",
        nargs="*",
        default=SITES,
        help="Sites to include. Defaults to the stable known sites.",
    )
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def drop_embedded_header_rows(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    if any(col not in df.columns for col in cols):
        return df
    header_mask = pd.Series(True, index=df.index)
    for col in cols:
        header_mask &= df[col].map(normalize_text).eq(col)
    if not bool(header_mask.any()):
        return df
    return df.loc[~header_mask].copy()


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def dedupe(df: pd.DataFrame, name: str, cols: list[str]) -> pd.DataFrame:
    dupes = df.loc[df.duplicated(subset=cols, keep=False), cols]
    if not dupes.empty:
        raise SystemExit(f"{name} has duplicate rows on {cols}")
    return df


def to_int(value: object) -> int:
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return 0
    return int(numeric)


def to_float(value: object) -> float:
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return 0.0
    return round(float(numeric), 6)


def stable_site_order(sites: list[str], site_values: list[str]) -> list[str]:
    site_rank = {site: idx for idx, site in enumerate(sites)}
    return sorted(set(site_values), key=lambda value: (site_rank.get(value, len(site_rank)), value))


def get_single_row(df: pd.DataFrame, name: str) -> pd.Series:
    if df.empty:
        raise SystemExit(f"{name} is empty")
    return df.iloc[0]


def get_decision_row(decisions_df: pd.DataFrame, decision_key: str) -> pd.Series:
    subset = decisions_df.loc[decisions_df["decision_key"].map(normalize_text).eq(decision_key)].copy()
    if subset.empty:
        raise SystemExit(f"baseline_freeze_decisions_v1.csv missing decision_key={decision_key}")
    return subset.iloc[0]


def build_summary_output(freeze_summary_row: pd.Series, guard_summary_row: pd.Series) -> pd.DataFrame:
    baseline_guard_status = normalize_text(guard_summary_row.get("guard_status", ""))
    active_review_queue_count = to_int(freeze_summary_row.get("active_review_queue_count", 0))
    row = {
        "baseline_guard_status": baseline_guard_status,
        "freeze_recommendation": normalize_text(freeze_summary_row.get("freeze_recommendation", "")),
        "strict_maintenance_f1": to_float(freeze_summary_row.get("strict_maintenance_f1", 0)),
        "strict_operational_f1": to_float(freeze_summary_row.get("strict_operational_f1", 0)),
        "lenient_maintenance_f1": to_float(freeze_summary_row.get("lenient_maintenance_f1", 0)),
        "lenient_operational_f1": to_float(freeze_summary_row.get("lenient_operational_f1", 0)),
        "official_scored_count": to_int(freeze_summary_row.get("official_scored_count", 0)),
        "manual_scored_count": to_int(freeze_summary_row.get("manual_scored_count", 0)),
        "vendor_scored_count": to_int(freeze_summary_row.get("vendor_scored_count", 0)),
        "deferred_hold_count": to_int(freeze_summary_row.get("deferred_hold_count", 0)),
        "active_review_queue_count": active_review_queue_count,
        "precursor_global_recommendation": normalize_text(
            freeze_summary_row.get("precursor_global_recommendation", "")
        ),
        "next_workstream_recommendation": (
            "safe_to_switch_topic"
            if baseline_guard_status == "frozen_baseline_preserved" and active_review_queue_count == 0
            else "finish_current_baseline_first"
        ),
    }
    return pd.DataFrame([row], columns=SUMMARY_COLS)


def build_site_note(row: pd.Series) -> str:
    precursor_site_recommendation = normalize_text(row.get("precursor_site_recommendation", ""))
    deferred_hold_count = to_int(row.get("deferred_hold_count", 0))
    official_scored_count = to_int(row.get("official_scored_count", 0))
    if precursor_site_recommendation == "keep_site_specific_precursor_note":
        return "공식 score는 유지하고 precursor site note만 관찰용으로 넘깁니다."
    if deferred_hold_count > 0:
        return "공식 score는 유지하고 deferred hold 행은 증거 전까지 보류합니다."
    if official_scored_count == 0:
        return "현재 scored row는 없고 안정 상태로만 기록합니다."
    return "공식 score 범위의 안정 사이트로 유지합니다."


def build_site_output(
    freeze_sites_df: pd.DataFrame,
    guard_sites_df: pd.DataFrame,
    precursor_sites_df: pd.DataFrame,
    sites: list[str],
) -> pd.DataFrame:
    freeze_sites = freeze_sites_df.copy()
    guard_sites = guard_sites_df.copy()
    precursor_sites = precursor_sites_df.copy()

    freeze_sites["site"] = freeze_sites["site"].map(normalize_text)
    guard_sites["site"] = guard_sites["site"].map(normalize_text)
    precursor_sites["site"] = precursor_sites["site"].map(normalize_text)

    freeze_sites = dedupe(freeze_sites, "baseline_freeze_sites_v1.csv", ["site"])
    guard_sites = dedupe(guard_sites, "baseline_regression_guard_sites_v1.csv", ["site"])
    precursor_sites = dedupe(precursor_sites, "common_cause_precursor_decision_sites_v1.csv", ["site"])

    merged = freeze_sites.merge(
        guard_sites.loc[:, ["site", "current_site_status", "site_guard_status"]],
        on="site",
        how="left",
    ).merge(
        precursor_sites.loc[:, ["site", "site_recommendation"]],
        on="site",
        how="left",
    )

    merged["site_status"] = merged["site_status"].map(normalize_text)
    merged["current_site_status"] = merged["current_site_status"].map(normalize_text)
    merged["precursor_site_recommendation"] = merged["precursor_site_recommendation"].map(normalize_text)
    merged["site_recommendation"] = merged["site_recommendation"].map(normalize_text)
    merged["site_guard_status"] = merged["site_guard_status"].map(normalize_text)

    missing_precursor = merged["precursor_site_recommendation"].eq("") & merged["site_recommendation"].ne("")
    merged.loc[missing_precursor, "precursor_site_recommendation"] = merged.loc[missing_precursor, "site_recommendation"]

    missing_site_status = merged["site_status"].eq("") & merged["current_site_status"].ne("")
    merged.loc[missing_site_status, "site_status"] = merged.loc[missing_site_status, "current_site_status"]

    for col in ["official_scored_count", "manual_scored_count", "vendor_scored_count", "deferred_hold_count"]:
        merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(0).astype(int)

    merged["handoff_note_ko"] = merged.apply(build_site_note, axis=1)

    site_order = stable_site_order(
        sites,
        freeze_sites["site"].tolist() + guard_sites["site"].tolist() + precursor_sites["site"].tolist(),
    )
    merged["_site_rank"] = merged["site"].map(lambda value: site_order.index(value) if value in site_order else len(site_order))
    merged = merged.sort_values(["_site_rank", "site"], ascending=[True, True]).reset_index(drop=True)
    return merged.loc[:, SITE_COLS]


def build_open_threads(
    deferred_hold_df: pd.DataFrame,
    freeze_summary_row: pd.Series,
    freeze_decisions_df: pd.DataFrame,
    site_output: pd.DataFrame,
    guard_summary_row: pd.Series,
) -> pd.DataFrame:
    deferred_hold_count = int(len(deferred_hold_df))
    deferred_reactivation_condition = "field_or_OM_evidence_available"
    if not deferred_hold_df.empty and "reactivation_condition" in deferred_hold_df.columns:
        candidate = normalize_text(deferred_hold_df.iloc[0]["reactivation_condition"])
        if candidate:
            deferred_reactivation_condition = candidate

    global_precursor_decision = get_decision_row(freeze_decisions_df, "global_precursor_addon")
    global_precursor_status = normalize_text(global_precursor_decision.get("decision_status", ""))
    precursor_global_recommendation = normalize_text(freeze_summary_row.get("precursor_global_recommendation", ""))

    conalog_row = site_output.loc[site_output["site"].map(normalize_text).eq("conalog")].copy()
    conalog_note = ""
    if not conalog_row.empty:
        conalog_note = normalize_text(conalog_row.iloc[0]["handoff_note_ko"])

    guard_status = normalize_text(guard_summary_row.get("guard_status", ""))
    thread_rows = [
        {
            "thread_key": "gangui_deferred_high_actionability",
            "thread_status": "on_hold",
            "owner_needed": "field_or_OM_review",
            "reactivation_condition": deferred_reactivation_condition,
            "note_ko": (
                f"gangui deferred hold {deferred_hold_count}건은 field/O&M evidence 확보 전까지 active review로 되돌리지 않습니다."
            ),
        },
        {
            "thread_key": "conalog_site_specific_precursor_note",
            "thread_status": "observation_only",
            "owner_needed": "analysis_review",
            "reactivation_condition": "repeated_multi_site_evidence",
            "note_ko": (
                "conalog precursor는 site note로만 유지하고 공식 addon으로 승격하지 않습니다."
                if conalog_note
                else "site-specific precursor note는 반복 다중-site 증거 전까지 관찰용으로만 둡니다."
            ),
        },
        {
            "thread_key": "precursor_global_addon",
            "thread_status": "not_adopted",
            "owner_needed": "future_research",
            "reactivation_condition": "precision_and_recall_thresholds_met",
            "note_ko": (
                f"global precursor addon은 {precursor_global_recommendation or global_precursor_status} 상태이며 기준 충족 전까지 채택하지 않습니다."
            ),
        },
        {
            "thread_key": "baseline_regression_guard",
            "thread_status": "active_guard",
            "owner_needed": "any_future_workstream",
            "reactivation_condition": "run_before_reporting_or_topic_switch",
            "note_ko": (
                "향후 보고나 주제 전환 전에는 baseline regression guard를 다시 실행합니다."
                if guard_status == "frozen_baseline_preserved"
                else "baseline drift가 해소될 때까지 regression guard 결과를 먼저 점검합니다."
            ),
        },
    ]
    return pd.DataFrame(thread_rows, columns=OPEN_THREAD_COLS)


def build_outputs(root: Path, sites: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    freeze_summary_df = drop_embedded_header_rows(
        read_csv(root / "_share" / "baseline_freeze_summary_v1.csv"),
        ["strict_maintenance_f1"],
    )
    freeze_sites_df = drop_embedded_header_rows(
        read_csv(root / "_share" / "baseline_freeze_sites_v1.csv"),
        ["site"],
    )
    freeze_decisions_df = drop_embedded_header_rows(
        read_csv(root / "_share" / "baseline_freeze_decisions_v1.csv"),
        ["decision_key"],
    )
    guard_summary_df = drop_embedded_header_rows(
        read_csv(root / "_share" / "baseline_regression_guard_summary_v1.csv"),
        ["guard_status"],
    )
    guard_sites_df = drop_embedded_header_rows(
        read_csv(root / "_share" / "baseline_regression_guard_sites_v1.csv"),
        ["site"],
    )
    deferred_hold_df = drop_embedded_header_rows(
        read_csv(root / "_share" / "truth_review_deferred_hold_v1.csv"),
        KEY_COLS,
    )
    precursor_sites_df = drop_embedded_header_rows(
        read_csv(root / "_share" / "common_cause_precursor_decision_sites_v1.csv"),
        ["site"],
    )

    ensure_columns(freeze_summary_df, SUMMARY_COLS[1:-1], "baseline_freeze_summary_v1.csv")
    ensure_columns(
        freeze_sites_df,
        ["site", "site_status", "official_scored_count", "manual_scored_count", "vendor_scored_count", "deferred_hold_count", "precursor_site_recommendation"],
        "baseline_freeze_sites_v1.csv",
    )
    ensure_columns(
        freeze_decisions_df,
        ["decision_key", "decision_status", "decision_reason", "supporting_value"],
        "baseline_freeze_decisions_v1.csv",
    )
    ensure_columns(
        guard_summary_df,
        ["guard_status"],
        "baseline_regression_guard_summary_v1.csv",
    )
    ensure_columns(
        guard_sites_df,
        ["site", "current_site_status", "site_guard_status"],
        "baseline_regression_guard_sites_v1.csv",
    )
    ensure_columns(
        deferred_hold_df,
        ["site", "panel_id", "strict_trigger_date", "reactivation_condition"],
        "truth_review_deferred_hold_v1.csv",
    )
    ensure_columns(
        precursor_sites_df,
        ["site", "site_recommendation"],
        "common_cause_precursor_decision_sites_v1.csv",
    )

    for decision_key in REQUIRED_DECISION_KEYS:
        get_decision_row(freeze_decisions_df, decision_key)

    freeze_sites_df["site"] = freeze_sites_df["site"].map(normalize_text)
    guard_sites_df["site"] = guard_sites_df["site"].map(normalize_text)
    precursor_sites_df["site"] = precursor_sites_df["site"].map(normalize_text)
    deferred_hold_df["site"] = deferred_hold_df["site"].map(normalize_text)

    selected_sites = set(sites)
    freeze_sites_df = freeze_sites_df.loc[freeze_sites_df["site"].isin(selected_sites)].copy()
    guard_sites_df = guard_sites_df.loc[guard_sites_df["site"].isin(selected_sites)].copy()
    precursor_sites_df = precursor_sites_df.loc[precursor_sites_df["site"].isin(selected_sites)].copy()
    deferred_hold_df = deferred_hold_df.loc[deferred_hold_df["site"].isin(selected_sites)].copy()

    freeze_summary_row = get_single_row(freeze_summary_df, "baseline_freeze_summary_v1.csv")
    guard_summary_row = get_single_row(guard_summary_df, "baseline_regression_guard_summary_v1.csv")

    summary_output = build_summary_output(freeze_summary_row, guard_summary_row)
    site_output = build_site_output(freeze_sites_df, guard_sites_df, precursor_sites_df, sites)
    open_threads_output = build_open_threads(
        deferred_hold_df,
        freeze_summary_row,
        freeze_decisions_df,
        site_output,
        guard_summary_row,
    )
    return summary_output, site_output, open_threads_output


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    summary_output, site_output, open_threads_output = build_outputs(root, list(args.sites))

    out_dir = root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_output.to_csv(out_dir / "workstream_handoff_summary_v1.csv", index=False, encoding="utf-8-sig")
    site_output.to_csv(out_dir / "workstream_handoff_sites_v1.csv", index=False, encoding="utf-8-sig")
    open_threads_output.to_csv(out_dir / "workstream_handoff_open_threads_v1.csv", index=False, encoding="utf-8-sig")
    print(
        "workstream_handoff_summary_v1="
        f"{len(summary_output)} workstream_handoff_sites_v1={len(site_output)} "
        f"workstream_handoff_open_threads_v1={len(open_threads_output)}"
    )


if __name__ == "__main__":
    main()
