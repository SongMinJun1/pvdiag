#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import pandas as pd

SITES = ["conalog", "sinhyo", "gangui", "ktc_ess"]
SUMMARY_COLS = [
    "site",
    "template_row_count",
    "reviewed_row_count",
    "leadtime_row_count",
    "had_prealert_count",
    "had_strong_event_count",
    "match_count",
    "partial_count",
    "mismatch_count",
    "unknown_count",
    "pending_truth_count",
    "ok_count",
    "truth_before_score_window_count",
    "truth_after_latest_raw_count",
    "missing_our_first_anomaly_count",
    "median_lead_days",
    "mean_lead_days",
]
LEAD_COLS = [
    "site",
    "panel_id",
    "review_group",
    "representative_date",
    "candidate_bucket",
    "our_first_anomaly_date",
    "our_first_anomaly_source",
    "chronology_guard_applied",
    "confidence_level",
    "abstain_flag",
    "abstain_reason",
    "truth_date_used",
    "validation_status",
    "lead_days",
    "had_prealert",
    "had_strong_event",
    "event_before_issue",
    "our_latest_status",
    "actual_issue_type",
    "actual_primary_view",
]
MATCH_COLS = [
    "site",
    "panel_id",
    "review_group",
    "representative_date",
    "candidate_bucket",
    "our_first_anomaly_source",
    "chronology_guard_applied",
    "confidence_level",
    "abstain_flag",
    "abstain_reason",
    "our_primary_view",
    "actual_primary_view",
    "field_match_manual",
    "field_match_auto",
    "field_match_final",
    "actual_issue_type",
    "note",
]


def read_csv_or_empty(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, low_memory=False)
    for col in ["site", "panel_id", "review_group", "our_latest_status"]:
        if col in df.columns:
            df = df[df[col].astype(str) != col]
    return df.reset_index(drop=True)


def fmt_date(value) -> str:
    ts = pd.to_datetime(value, errors="coerce")
    return ts.strftime("%Y-%m-%d") if pd.notna(ts) else ""


def boolish(value) -> bool:
    if pd.isna(value):
        return False
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n", ""}:
        return False
    return bool(pd.to_numeric(pd.Series([value]), errors="coerce").fillna(0).iloc[0])


def normalize_view(value) -> str:
    raw = "" if pd.isna(value) else str(value).strip().lower()
    if raw in {"electrical_like", "pattern_change_like", "unstable_like", "mixed_like"}:
        return raw
    return "unknown"


def normalize_match(value) -> str:
    raw = "" if pd.isna(value) else str(value).strip().lower()
    if raw in {"match", "partial", "mismatch", "unknown"}:
        return raw
    return ""


def truth_date_used(row: pd.Series) -> str:
    started = fmt_date(row.get("issue_started_estimated_date"))
    if started:
        return started
    return fmt_date(row.get("issue_detected_date"))


def is_reviewed(row: pd.Series) -> bool:
    for col in [
        "issue_detected_date",
        "issue_started_estimated_date",
        "actual_issue_type",
        "actual_primary_view",
        "action_taken",
        "field_match_manual",
        "note",
    ]:
        value = row.get(col)
        if pd.notna(value) and str(value).strip():
            return True
    return False


def helper_latest_alerts(root: Path) -> pd.DataFrame:
    frames = []
    for site in SITES:
        path = root / "data" / site / "out" / "latest_alerts_enriched.csv"
        df = read_csv_or_empty(path)
        if df.empty:
            continue
        df = df.copy()
        df["site"] = site
        keep = [
            "site",
            "panel_id",
            "diagnosis_date_online",
            "critical_diag_date",
            "dead_diag_date",
            "final_fault",
        ]
        for col in keep:
            if col not in df.columns:
                df[col] = pd.NA
        frames.append(df[keep])
    if not frames:
        return pd.DataFrame(
            columns=[
                "site",
                "panel_id",
                "diagnosis_date_online",
                "critical_diag_date",
                "dead_diag_date",
                "final_fault",
            ]
        )
    merged = pd.concat(frames, ignore_index=True)
    return merged.drop_duplicates(["site", "panel_id"], keep="last")


def helper_site_windows(root: Path) -> pd.DataFrame:
    rows = []
    for site in SITES:
        score_start = ""
        config_path = root / "configs" / "sites" / f"{site}.yaml"
        if config_path.exists():
            for line in config_path.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("score_start:"):
                    score_start = line.split(":", 1)[1].strip().strip("\"'")
                    break
        latest_date = ""
        summary = read_csv_or_empty(root / "data" / site / "out" / "latest_site_summary.csv")
        if not summary.empty and "latest_date" in summary.columns:
            valid = pd.to_datetime(summary["latest_date"], errors="coerce").dropna()
            if not valid.empty:
                latest_date = valid.max().strftime("%Y-%m-%d")
        rows.append({"site": site, "score_start": score_start, "latest_raw_date": latest_date})
    return pd.DataFrame(rows)


def helper_template_meta(root: Path) -> pd.DataFrame:
    path = root / "_share" / "field_truth_template_meta.csv"
    meta = read_csv_or_empty(path)
    if meta.empty:
        return pd.DataFrame(columns=["site", "panel_id", "review_group", "our_first_anomaly_source", "chronology_guard_applied", "confidence_level", "abstain_flag", "abstain_reason"])
    keep = ["site", "panel_id", "review_group", "our_first_anomaly_source", "chronology_guard_applied", "confidence_level", "abstain_flag", "abstain_reason"]
    for col in keep:
        if col not in meta.columns:
            meta[col] = pd.NA
    return meta[keep].drop_duplicates(["site", "panel_id", "review_group"], keep="last")


def field_match_auto(our_view: str, actual_view: str) -> str:
    if our_view == "unknown" or actual_view == "unknown":
        return "unknown"
    if our_view == actual_view:
        return "match"
    concrete = {"electrical_like", "pattern_change_like", "unstable_like"}
    if (our_view == "mixed_like" and actual_view in concrete) or (actual_view == "mixed_like" and our_view in concrete):
        return "partial"
    return "mismatch"


def had_prealert(row: pd.Series) -> bool:
    truth = pd.to_datetime(row.get("truth_date_used"), errors="coerce")
    first_anomaly = pd.to_datetime(row.get("our_first_anomaly_date"), errors="coerce")
    if pd.isna(truth) or pd.isna(first_anomaly):
        return False
    return first_anomaly < truth


def had_strong_event(row: pd.Series) -> bool:
    truth = pd.to_datetime(row.get("truth_date_used"), errors="coerce")
    if pd.isna(truth):
        return False
    strong_dates = pd.to_datetime(
        pd.Series(
            [
                row.get("diagnosis_date_online"),
                row.get("critical_diag_date"),
                row.get("dead_diag_date"),
            ]
        ),
        errors="coerce",
    ).dropna()
    if not strong_dates.empty and bool((strong_dates < truth).any()):
        return True
    if boolish(row.get("final_fault")):
        rep = pd.to_datetime(row.get("representative_date"), errors="coerce")
        return pd.notna(rep) and rep < truth
    return False


def validation_status(row: pd.Series) -> str:
    truth = pd.to_datetime(row.get("truth_date_used"), errors="coerce")
    if pd.isna(truth):
        return "pending_truth"
    first_anomaly = pd.to_datetime(row.get("our_first_anomaly_date"), errors="coerce")
    if pd.isna(first_anomaly):
        return "missing_our_first_anomaly"
    score_start = pd.to_datetime(row.get("score_start"), errors="coerce")
    latest_raw = pd.to_datetime(row.get("latest_raw_date"), errors="coerce")
    if pd.notna(score_start) and truth < score_start:
        return "truth_before_score_window"
    if pd.notna(latest_raw) and truth > latest_raw:
        return "truth_after_latest_raw"
    return "ok"


def build_outputs(template: pd.DataFrame, meta: pd.DataFrame, helpers: pd.DataFrame, windows: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if template.empty:
        summary = pd.DataFrame(
            [{"site": site, **{c: 0 for c in SUMMARY_COLS if c != "site"}} for site in SITES]
            + [{"site": "overall", **{c: 0 for c in SUMMARY_COLS if c != "site"}}],
            columns=SUMMARY_COLS,
        )
        return summary, pd.DataFrame(columns=LEAD_COLS), pd.DataFrame(columns=MATCH_COLS)

    work = template.copy()
    work = work.merge(meta, on=["site", "panel_id", "review_group"], how="left")
    work = work.merge(helpers, on=["site", "panel_id"], how="left")
    work = work.merge(windows, on="site", how="left")
    work["reviewed"] = work.apply(is_reviewed, axis=1)
    work["our_primary_view"] = work.get("our_primary_view", pd.Series(dtype=object)).apply(normalize_view)
    work["actual_primary_view"] = work.get("actual_primary_view", pd.Series(dtype=object)).apply(normalize_view)
    work["field_match_manual"] = work.get("field_match_manual", pd.Series(dtype=object)).apply(normalize_match)
    work["field_match_auto"] = [
        field_match_auto(our_view=our, actual_view=actual)
        for our, actual in zip(work["our_primary_view"], work["actual_primary_view"])
    ]
    work["field_match_final"] = [
        manual if manual else auto
        for manual, auto in zip(work["field_match_manual"], work["field_match_auto"])
    ]
    work["truth_date_used"] = work.apply(truth_date_used, axis=1)
    work["validation_status"] = work.apply(validation_status, axis=1)
    work["had_prealert"] = work.apply(had_prealert, axis=1)
    work["had_strong_event"] = work.apply(had_strong_event, axis=1)
    raw_lead_days = (
        pd.to_datetime(work["truth_date_used"], errors="coerce")
        - pd.to_datetime(work["our_first_anomaly_date"], errors="coerce")
    ).dt.days
    work["lead_days"] = raw_lead_days.where(work["validation_status"].eq("ok"))
    work["event_before_issue"] = work["lead_days"].apply(
        lambda x: pd.NA if pd.isna(x) else bool(x > 0)
    )

    reviewed = work[work["reviewed"]].copy()
    if reviewed.empty:
        summary_rows = []
        for site in SITES + ["overall"]:
            sub = work if site == "overall" else work[work["site"].astype(str) == site]
            status_counts = sub["validation_status"].value_counts()
            summary_rows.append(
                {
                    "site": site,
                    "template_row_count": int(len(sub)),
                    "reviewed_row_count": 0,
                    "leadtime_row_count": 0,
                    "had_prealert_count": 0,
                    "had_strong_event_count": 0,
                    "match_count": 0,
                    "partial_count": 0,
                    "mismatch_count": 0,
                    "unknown_count": 0,
                    "pending_truth_count": int(status_counts.get("pending_truth", 0)),
                    "ok_count": int(status_counts.get("ok", 0)),
                    "truth_before_score_window_count": int(status_counts.get("truth_before_score_window", 0)),
                    "truth_after_latest_raw_count": int(status_counts.get("truth_after_latest_raw", 0)),
                    "missing_our_first_anomaly_count": int(status_counts.get("missing_our_first_anomaly", 0)),
                    "median_lead_days": pd.NA,
                    "mean_lead_days": pd.NA,
                }
            )
        return pd.DataFrame(summary_rows, columns=SUMMARY_COLS), pd.DataFrame(columns=LEAD_COLS), pd.DataFrame(columns=MATCH_COLS)

    lead_df = reviewed[LEAD_COLS].copy()
    match_df = reviewed[MATCH_COLS].copy()

    summary_rows = []
    for site in SITES + ["overall"]:
        sub_all = work if site == "overall" else work[work["site"].astype(str) == site]
        sub = reviewed if site == "overall" else reviewed[reviewed["site"].astype(str) == site]
        lead_vals = pd.to_numeric(sub["lead_days"], errors="coerce").dropna()
        counts = sub["field_match_final"].value_counts()
        status_counts = sub_all["validation_status"].value_counts()
        summary_rows.append(
            {
                "site": site,
                "template_row_count": int(len(sub_all)),
                "reviewed_row_count": int(len(sub)),
                "leadtime_row_count": int(len(lead_vals)),
                "had_prealert_count": int(sub.get("had_prealert", pd.Series(dtype=bool)).fillna(False).sum()),
                "had_strong_event_count": int(sub.get("had_strong_event", pd.Series(dtype=bool)).fillna(False).sum()),
                "match_count": int(counts.get("match", 0)),
                "partial_count": int(counts.get("partial", 0)),
                "mismatch_count": int(counts.get("mismatch", 0)),
                "unknown_count": int(counts.get("unknown", 0)),
                "pending_truth_count": int(status_counts.get("pending_truth", 0)),
                "ok_count": int(status_counts.get("ok", 0)),
                "truth_before_score_window_count": int(status_counts.get("truth_before_score_window", 0)),
                "truth_after_latest_raw_count": int(status_counts.get("truth_after_latest_raw", 0)),
                "missing_our_first_anomaly_count": int(status_counts.get("missing_our_first_anomaly", 0)),
                "median_lead_days": float(lead_vals.median()) if not lead_vals.empty else pd.NA,
                "mean_lead_days": float(lead_vals.mean()) if not lead_vals.empty else pd.NA,
            }
        )
    summary_df = pd.DataFrame(summary_rows, columns=SUMMARY_COLS)
    return summary_df, lead_df, match_df


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    template = read_csv_or_empty(share_dir / "field_truth_template.csv")
    meta = helper_template_meta(root)
    helpers = helper_latest_alerts(root)
    windows = helper_site_windows(root)
    summary_df, lead_df, match_df = build_outputs(template, meta, helpers, windows)

    summary_path = share_dir / "field_validation_summary.csv"
    lead_path = share_dir / "field_validation_leadtime.csv"
    match_path = share_dir / "field_validation_phenotype_match.csv"

    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
    lead_df.to_csv(lead_path, index=False, encoding="utf-8-sig")
    match_df.to_csv(match_path, index=False, encoding="utf-8-sig")

    print(f"[OK] wrote {summary_path}")
    print(f"[OK] wrote {lead_path}")
    print(f"[OK] wrote {match_path}")
    reviewed_rows = int(summary_df.loc[summary_df["site"] == "overall", "reviewed_row_count"].fillna(0).iloc[0]) if not summary_df.empty else 0
    print(f"[COUNT] reviewed_rows={reviewed_rows}")


if __name__ == "__main__":
    main()
