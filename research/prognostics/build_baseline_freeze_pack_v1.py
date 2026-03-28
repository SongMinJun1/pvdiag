#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
SUMMARY_COLS = [
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
    "freeze_recommendation",
]
SITE_COLS = [
    "site",
    "official_scored_count",
    "manual_scored_count",
    "vendor_scored_count",
    "deferred_hold_count",
    "precursor_site_recommendation",
    "site_status",
]
DECISION_COLS = ["decision_key", "decision_status", "decision_reason", "supporting_value"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Freeze the current baseline state into a single decision artifact without changing score or truth."
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


def first_nonblank(series: pd.Series) -> object:
    for value in series.tolist():
        if normalize_text(value):
            return value
    if series.dtype.kind in {"f", "i", "u"}:
        return float("nan")
    return ""


def get_summary_row(df: pd.DataFrame, name: str) -> pd.Series:
    if df.empty:
        raise SystemExit(f"{name} is empty")
    if "record_type" in df.columns:
        summary_rows = df.loc[df["record_type"].map(normalize_text).eq("summary")].copy()
        if not summary_rows.empty:
            return summary_rows.iloc[0]
    return df.iloc[0]


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


def extract_f1(summary_df: pd.DataFrame, truth_mode: str, prediction_mode: str) -> float:
    subset = summary_df.loc[
        summary_df["source_split"].map(normalize_text).eq("overall")
        & summary_df["truth_mode"].map(normalize_text).eq(truth_mode)
        & summary_df["prediction_mode"].map(normalize_text).eq(prediction_mode),
        "f1",
    ]
    if subset.empty:
        raise SystemExit(
            f"full_algorithm_f1_summary_v3.csv missing overall row for truth_mode={truth_mode}, "
            f"prediction_mode={prediction_mode}"
        )
    return to_float(subset.iloc[0])


def stable_site_order(sites: list[str], site_values: list[str]) -> list[str]:
    site_order = {site: idx for idx, site in enumerate(sites)}
    return sorted(set(site_values), key=lambda value: (site_order.get(value, len(site_order)), value))


def build_site_output(
    score_scope_sites_df: pd.DataFrame,
    deferred_summary_df: pd.DataFrame,
    precursor_sites_df: pd.DataFrame,
    sites: list[str],
) -> pd.DataFrame:
    deferred_sites = deferred_summary_df.loc[
        deferred_summary_df.get("record_type", "").map(normalize_text).eq("site")
    ].copy()
    precursor_sites = precursor_sites_df.copy()

    for col in ["site"]:
        if col in deferred_sites.columns:
            deferred_sites[col] = deferred_sites[col].map(normalize_text)
        if col in precursor_sites.columns:
            precursor_sites[col] = precursor_sites[col].map(normalize_text)

    if "deferred_hold_count" not in deferred_sites.columns:
        deferred_sites["deferred_hold_count"] = 0
    deferred_sites["deferred_hold_count"] = pd.to_numeric(deferred_sites["deferred_hold_count"], errors="coerce").fillna(0).astype(int)

    if "site_handling_recommendation" not in deferred_sites.columns:
        deferred_sites["site_handling_recommendation"] = ""
    deferred_sites["site_handling_recommendation"] = deferred_sites["site_handling_recommendation"].map(normalize_text)

    if "site_recommendation" not in precursor_sites.columns:
        precursor_sites["site_recommendation"] = ""
    precursor_sites["site_recommendation"] = precursor_sites["site_recommendation"].map(normalize_text)
    if "site_decision_reason" not in precursor_sites.columns:
        precursor_sites["site_decision_reason"] = ""
    precursor_sites["site_decision_reason"] = precursor_sites["site_decision_reason"].map(normalize_text)

    merged = score_scope_sites_df.merge(
        deferred_sites.loc[:, ["site", "deferred_hold_count", "site_handling_recommendation"]],
        on="site",
        how="left",
    ).merge(
        precursor_sites.loc[:, ["site", "site_recommendation", "site_decision_reason"]],
        on="site",
        how="left",
    )

    merged["deferred_hold_count"] = pd.to_numeric(merged["deferred_hold_count"], errors="coerce").fillna(0).astype(int)
    merged["precursor_site_recommendation"] = merged["site_recommendation"].fillna("").map(normalize_text)

    def classify_site_status(row: pd.Series) -> str:
        deferred_hold_count = int(row["deferred_hold_count"])
        precursor_site_recommendation = normalize_text(row["precursor_site_recommendation"])
        if deferred_hold_count > 0 and precursor_site_recommendation == "keep_site_specific_precursor_note":
            return "scored_with_deferred_hold_and_site_note"
        if deferred_hold_count > 0:
            return "scored_with_deferred_hold"
        if precursor_site_recommendation == "keep_site_specific_precursor_note":
            return "scored_with_site_specific_precursor_note"
        return "stable_scored_site"

    merged["site_status"] = merged.apply(classify_site_status, axis=1)

    all_sites = stable_site_order(
        sites,
        score_scope_sites_df["site"].map(normalize_text).tolist()
        + precursor_sites["site"].map(normalize_text).tolist()
        + deferred_sites["site"].map(normalize_text).tolist(),
    )
    merged["_site_rank"] = merged["site"].map(lambda value: all_sites.index(value) if value in all_sites else len(all_sites))
    merged = merged.sort_values(["_site_rank", "site"], ascending=[True, True]).reset_index(drop=True)
    return merged.loc[:, SITE_COLS]


def build_decisions(
    summary_row: pd.Series,
    site_output: pd.DataFrame,
    precursor_summary_row: pd.Series,
    precursor_sites_df: pd.DataFrame,
) -> pd.DataFrame:
    freeze_recommendation = normalize_text(summary_row["freeze_recommendation"])
    active_review_queue_count = to_int(summary_row["active_review_queue_count"])
    deferred_hold_count = to_int(summary_row["deferred_hold_count"])
    precursor_global_recommendation = normalize_text(summary_row["precursor_global_recommendation"])
    precursor_global_reason = normalize_text(precursor_summary_row.get("global_decision_reason", ""))
    primary_tier_used = normalize_text(precursor_summary_row.get("primary_tier_used", ""))

    precursor_sites_df = precursor_sites_df.copy()
    precursor_sites_df["site"] = precursor_sites_df["site"].map(normalize_text)
    precursor_sites_df["site_recommendation"] = precursor_sites_df.get("site_recommendation", "").fillna("").map(normalize_text)
    precursor_sites_df["site_decision_reason"] = precursor_sites_df.get("site_decision_reason", "").fillna("").map(normalize_text)
    conalog_rows = precursor_sites_df.loc[precursor_sites_df["site"].eq("conalog")].copy()
    conalog_recommendation = ""
    conalog_reason = ""
    if not conalog_rows.empty:
        conalog_recommendation = normalize_text(conalog_rows.iloc[0]["site_recommendation"])
        conalog_reason = normalize_text(conalog_rows.iloc[0]["site_decision_reason"])

    decisions = [
        {
            "decision_key": "official_baseline_status",
            "decision_status": "frozen" if freeze_recommendation == "baseline_frozen_ready" else "not_frozen",
            "decision_reason": (
                "The active truth review queue is empty, so the current baseline state can be treated as frozen."
                if freeze_recommendation == "baseline_frozen_ready"
                else "The active truth review queue is still nonempty, so the baseline should not be frozen yet."
            ),
            "supporting_value": freeze_recommendation,
        },
        {
            "decision_key": "active_truth_review_queue",
            "decision_status": "empty" if active_review_queue_count == 0 else "nonempty",
            "decision_reason": (
                "No active truth review rows remain after applying the deferred-hold packaging."
                if active_review_queue_count == 0
                else "Some truth review rows remain active after applying the deferred-hold packaging."
            ),
            "supporting_value": str(active_review_queue_count),
        },
        {
            "decision_key": "deferred_high_actionability_rows",
            "decision_status": "on_hold" if deferred_hold_count > 0 else "none",
            "decision_reason": (
                "Deferred high-actionability rows remain on hold pending stronger field or O&M evidence."
                if deferred_hold_count > 0
                else "No deferred high-actionability rows are currently on hold."
            ),
            "supporting_value": str(deferred_hold_count),
        },
        {
            "decision_key": "global_precursor_addon",
            "decision_status": precursor_global_recommendation,
            "decision_reason": precursor_global_reason,
            "supporting_value": primary_tier_used,
        },
        {
            "decision_key": "conalog_precursor_note",
            "decision_status": "keep" if conalog_recommendation == "keep_site_specific_precursor_note" else "none",
            "decision_reason": (
                conalog_reason
                if conalog_reason
                else "No site-specific precursor note is currently retained for conalog."
            ),
            "supporting_value": conalog_recommendation,
        },
        {
            "decision_key": "next_workstream_recommendation",
            "decision_status": (
                "safe_to_switch_topic" if freeze_recommendation == "baseline_frozen_ready" else "finish_review_first"
            ),
            "decision_reason": (
                "The official baseline, deferred hold registry, and precursor posture are captured in one frozen artifact."
                if freeze_recommendation == "baseline_frozen_ready"
                else "Finish the remaining active truth review queue before switching to another workstream."
            ),
            "supporting_value": freeze_recommendation,
        },
    ]
    return pd.DataFrame(decisions, columns=DECISION_COLS)


def build_outputs(root: Path, sites: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    f1_summary_df = drop_embedded_header_rows(read_csv(root / "_share" / "full_algorithm_f1_summary_v3.csv"), ["truth_mode"])
    score_scope_summary_df = drop_embedded_header_rows(
        read_csv(root / "_share" / "score_scope_manifest_summary_v1.csv"),
        ["record_type"],
    )
    score_scope_sites_df = drop_embedded_header_rows(
        read_csv(root / "_share" / "score_scope_manifest_sites_v1.csv"),
        ["site"],
    )
    deferred_summary_df = drop_embedded_header_rows(
        read_csv(root / "_share" / "truth_review_deferred_summary_v1.csv"),
        ["record_type"],
    )
    precursor_summary_df = drop_embedded_header_rows(
        read_csv(root / "_share" / "common_cause_precursor_decision_summary_v1.csv"),
        ["global_recommendation"],
    )
    precursor_sites_df = drop_embedded_header_rows(
        read_csv(root / "_share" / "common_cause_precursor_decision_sites_v1.csv"),
        ["site"],
    )
    active_review_df = drop_embedded_header_rows(
        read_csv(root / "_share" / "truth_review_active_batch_v2.csv"),
        ["site", "panel_id", "strict_trigger_date"],
    )

    ensure_columns(f1_summary_df, ["truth_mode", "prediction_mode", "source_split", "f1"], "full_algorithm_f1_summary_v3.csv")
    ensure_columns(
        score_scope_summary_df,
        ["official_scored_count", "manual_scored_count", "vendor_scored_count"],
        "score_scope_manifest_summary_v1.csv",
    )
    ensure_columns(
        score_scope_sites_df,
        ["site", "official_scored_count", "manual_scored_count", "vendor_scored_count"],
        "score_scope_manifest_sites_v1.csv",
    )
    ensure_columns(
        deferred_summary_df,
        ["original_batch_count", "deferred_hold_count", "active_batch_v2_count", "deferred_site_count"],
        "truth_review_deferred_summary_v1.csv",
    )
    ensure_columns(
        precursor_summary_df,
        ["global_recommendation"],
        "common_cause_precursor_decision_summary_v1.csv",
    )
    ensure_columns(
        precursor_sites_df,
        ["site", "site_recommendation"],
        "common_cause_precursor_decision_sites_v1.csv",
    )

    for df in [score_scope_sites_df, precursor_sites_df]:
        df["site"] = df["site"].map(normalize_text)
    score_scope_sites_df = score_scope_sites_df.loc[score_scope_sites_df["site"].isin(sites)].copy()
    precursor_sites_df = precursor_sites_df.loc[precursor_sites_df["site"].isin(sites)].copy()

    score_scope_summary_row = get_summary_row(score_scope_summary_df, "score_scope_manifest_summary_v1.csv")
    deferred_summary_row = get_summary_row(deferred_summary_df, "truth_review_deferred_summary_v1.csv")
    precursor_summary_row = get_summary_row(precursor_summary_df, "common_cause_precursor_decision_summary_v1.csv")

    active_review_queue_count = int(len(active_review_df))
    summary_active_queue_count = to_int(deferred_summary_row.get("active_batch_v2_count", 0))
    if active_review_queue_count != summary_active_queue_count:
        raise SystemExit(
            "truth_review_active_batch_v2.csv row count does not match truth_review_deferred_summary_v1.csv: "
            f"rows={active_review_queue_count} summary={summary_active_queue_count}"
        )

    freeze_recommendation = (
        "baseline_frozen_ready" if active_review_queue_count == 0 else "baseline_requires_active_review"
    )
    summary_output = pd.DataFrame(
        [
            {
                "strict_maintenance_f1": extract_f1(f1_summary_df, "strict", "maintenance"),
                "strict_operational_f1": extract_f1(f1_summary_df, "strict", "operational"),
                "lenient_maintenance_f1": extract_f1(f1_summary_df, "lenient", "maintenance"),
                "lenient_operational_f1": extract_f1(f1_summary_df, "lenient", "operational"),
                "official_scored_count": to_int(score_scope_summary_row["official_scored_count"]),
                "manual_scored_count": to_int(score_scope_summary_row["manual_scored_count"]),
                "vendor_scored_count": to_int(score_scope_summary_row["vendor_scored_count"]),
                "deferred_hold_count": to_int(deferred_summary_row["deferred_hold_count"]),
                "active_review_queue_count": active_review_queue_count,
                "precursor_global_recommendation": normalize_text(precursor_summary_row["global_recommendation"]),
                "freeze_recommendation": freeze_recommendation,
            }
        ],
        columns=SUMMARY_COLS,
    )

    site_output = build_site_output(score_scope_sites_df, deferred_summary_df, precursor_sites_df, sites)
    decision_output = build_decisions(summary_output.iloc[0], site_output, precursor_summary_row, precursor_sites_df)
    return summary_output, site_output, decision_output


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    summary_output, site_output, decision_output = build_outputs(root, list(args.sites))

    out_dir = root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_output.to_csv(out_dir / "baseline_freeze_summary_v1.csv", index=False, encoding="utf-8-sig")
    site_output.to_csv(out_dir / "baseline_freeze_sites_v1.csv", index=False, encoding="utf-8-sig")
    decision_output.to_csv(out_dir / "baseline_freeze_decisions_v1.csv", index=False, encoding="utf-8-sig")
    print(
        f"baseline_freeze_summary_v1=1 baseline_freeze_sites_v1={len(site_output)} "
        f"baseline_freeze_decisions_v1={len(decision_output)}"
    )


if __name__ == "__main__":
    main()
