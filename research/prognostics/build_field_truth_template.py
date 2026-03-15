#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import pandas as pd

SITES = ["conalog", "sinhyo", "gangui", "ktc_ess"]
TEMPLATE_COLS = [
    "site",
    "panel_id",
    "review_group",
    "representative_date",
    "candidate_bucket",
    "our_first_anomaly_date",
    "our_latest_status",
    "our_primary_view",
    "our_interpretation",
    "issue_detected_date",
    "issue_started_estimated_date",
    "actual_issue_type",
    "actual_primary_view",
    "action_taken",
    "field_match_manual",
    "field_match_auto",
    "note",
]
GROUP_COLS = [
    "site",
    "review_group",
    "representative_date",
    "event_start_date",
    "event_end_date",
    "panel_count",
    "panel_ids",
    "summary",
    "likely_common_issue",
]
SOURCE_COUNT_KEYS = [
    "from_alert_history_temporal",
    "from_historical_reconstruction",
    "from_row_evidence_fallback",
    "from_current_review_fallback",
    "from_representative_guard",
]


def read_csv_or_empty(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, low_memory=False)
    for col in ["site", "panel_id", "snapshot_date", "date", "review_group"]:
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


def our_primary_view(row: pd.Series) -> str:
    phenotype = "" if pd.isna(row.get("phenotype")) else str(row.get("phenotype")).strip().lower()
    dominant = "" if pd.isna(row.get("dominant_family")) else str(row.get("dominant_family")).strip().lower()
    if phenotype == "compound":
        return "mixed_like"
    if dominant == "electrical":
        return "electrical_like"
    if dominant == "shape":
        return "pattern_change_like"
    if dominant == "instability":
        return "unstable_like"
    return "unknown"


def latest_status(row: pd.Series) -> str:
    if boolish(row.get("final_fault")):
        return "final_fault"
    if fmt_date(row.get("dead_diag_date")):
        return "dead"
    if fmt_date(row.get("critical_diag_date")):
        return "critical"
    if fmt_date(row.get("diagnosis_date_online")):
        return "online_diag"
    return "alert"


def candidate_bucket(status: str) -> str:
    if status in {"final_fault", "dead", "critical", "online_diag"}:
        return "event_candidate"
    return "prealert_candidate"


def interpretation(primary_view: str, bucket: str) -> str:
    if primary_view == "electrical_like":
        return "출력이 크게 떨어진 전기 계열 이상 가능성"
    if primary_view == "pattern_change_like":
        return "다른 패널과 비교해 출력 흐름이 달라진 사례"
    if primary_view == "unstable_like":
        return "흔들림/간헐 이상 가능성"
    if primary_view == "mixed_like":
        return "한 가지로 단정하기 어려운 복합 이상 가능성"
    return "해석 정보 부족"


def representative_date_from_evidence(row: pd.Series, initial_fallback_date: str) -> str:
    for col in ["dead_diag_date", "critical_diag_date", "diagnosis_date_online", "phenotype_event_date"]:
        value = fmt_date(row.get(col))
        if value:
            return value
    return initial_fallback_date


def monotonic_first_anomaly(first_anomaly_date: str, rep_date: str) -> str:
    first_ts = pd.to_datetime(first_anomaly_date, errors="coerce")
    rep_ts = pd.to_datetime(rep_date, errors="coerce")
    if pd.notna(rep_ts) and (pd.isna(first_ts) or first_ts > rep_ts):
        return rep_ts.strftime("%Y-%m-%d")
    return first_anomaly_date


def first_alert_history_date(out_dir: Path) -> tuple[dict[str, str], bool]:
    history = read_csv_or_empty(out_dir / "alert_history.csv")
    if history.empty or "snapshot_date" not in history.columns or "panel_id" not in history.columns:
        return {}, False
    history["snapshot_date"] = pd.to_datetime(history["snapshot_date"], errors="coerce")
    history = history.dropna(subset=["snapshot_date"])
    if history.empty:
        return {}, False
    if history["snapshot_date"].dt.normalize().nunique() <= 1:
        return {}, False
    first = (
        history.sort_values(["panel_id", "snapshot_date"], na_position="last")
        .groupby("panel_id", as_index=False)["snapshot_date"]
        .min()
    )
    mapping = {str(row.panel_id): row.snapshot_date.strftime("%Y-%m-%d") for row in first.itertuples(index=False)}
    return mapping, True


def historical_reconstruction_first_anomaly(row: pd.Series) -> str:
    # v1 intentionally does not do resolved-only full historical backfill.
    return ""


def row_evidence_first_anomaly(row: pd.Series) -> str:
    stamps = pd.to_datetime(
        pd.Series(
            [
                row.get("diagnosis_date_online"),
                row.get("critical_diag_date"),
                row.get("dead_diag_date"),
                row.get("phenotype_event_date"),
            ]
        ),
        errors="coerce",
    ).dropna()
    if stamps.empty:
        return ""
    return stamps.min().strftime("%Y-%m-%d")


def current_review_fallback_date(review_date: str) -> str:
    return review_date or ""


def derive_first_anomaly_date(
    panel_id: str,
    row: pd.Series,
    first_history_map: dict[str, str],
    history_available: bool,
    current_review_date: str,
    source_counts: dict[str, int],
) -> str:
    if history_available and panel_id in first_history_map:
        source_counts["from_alert_history_temporal"] += 1
        return first_history_map[panel_id]

    reconstructed = historical_reconstruction_first_anomaly(row)
    if reconstructed:
        source_counts["from_historical_reconstruction"] += 1
        return reconstructed

    row_evidence = row_evidence_first_anomaly(row)
    if row_evidence:
        source_counts["from_row_evidence_fallback"] += 1
        return row_evidence

    review_fallback = current_review_fallback_date(current_review_date)
    if review_fallback:
        source_counts["from_current_review_fallback"] += 1
        return review_fallback

    return ""


def build_template(root: Path) -> tuple[pd.DataFrame, dict[str, int]]:
    rows = []
    source_counts = {key: 0 for key in SOURCE_COUNT_KEYS}
    for site in SITES:
        out_dir = root / "data" / site / "out"
        alerts = read_csv_or_empty(out_dir / "latest_alerts_enriched.csv")
        summary = read_csv_or_empty(out_dir / "latest_site_summary.csv")
        if alerts.empty:
            continue
        latest_date = ""
        if not summary.empty and "latest_date" in summary.columns:
            valid_dates = pd.to_datetime(summary["latest_date"], errors="coerce").dropna()
            if not valid_dates.empty:
                latest_date = valid_dates.max().strftime("%Y-%m-%d")
        first_history_map, history_available = first_alert_history_date(out_dir)

        for row in alerts.itertuples(index=False):
            rec = row._asdict()
            row_series = pd.Series(rec)
            panel_id = str(rec.get("panel_id") or "")
            primary_view = our_primary_view(row_series)
            status = latest_status(row_series)
            bucket = candidate_bucket(status)
            first_anomaly = derive_first_anomaly_date(
                panel_id=panel_id,
                row=row_series,
                first_history_map=first_history_map,
                history_available=history_available,
                current_review_date=latest_date,
                source_counts=source_counts,
            )
            # representative_date is chosen from event/evidence dates first,
            # then falls back to the pre-guard anomaly candidate only if needed.
            rep_date = representative_date_from_evidence(row_series, first_anomaly)
            guarded_first_anomaly = monotonic_first_anomaly(first_anomaly, rep_date)
            if guarded_first_anomaly != first_anomaly:
                source_counts["from_representative_guard"] += 1
            first_anomaly = guarded_first_anomaly
            rows.append(
                {
                    "site": site,
                    "panel_id": panel_id,
                    "review_group": f"{site}:{rep_date}" if rep_date else "",
                    "representative_date": rep_date,
                    "candidate_bucket": bucket,
                    "our_first_anomaly_date": first_anomaly,
                    "our_latest_status": status,
                    "our_primary_view": primary_view,
                    "our_interpretation": interpretation(primary_view, bucket),
                    "issue_detected_date": "",
                    "issue_started_estimated_date": "",
                    "actual_issue_type": "",
                    "actual_primary_view": "",
                    "action_taken": "",
                    "field_match_manual": "",
                    "field_match_auto": "",
                    "note": "",
                }
            )
    template = pd.DataFrame(rows, columns=TEMPLATE_COLS)
    if template.empty:
        return pd.DataFrame(columns=TEMPLATE_COLS), source_counts
    return (
        template.sort_values(
            ["site", "candidate_bucket", "representative_date", "panel_id"],
            ascending=[True, True, True, True],
            na_position="last",
        ).reset_index(drop=True),
        source_counts,
    )


def likely_common_issue(group: pd.DataFrame) -> str:
    views = group["our_primary_view"].fillna("unknown").astype(str)
    if views.empty or views.eq("unknown").all():
        return "unknown"
    counts = views.value_counts()
    top_view = str(counts.index[0])
    top_share = float(counts.iloc[0]) / float(len(group))
    if top_view != "unknown" and top_share >= 0.6:
        return top_view
    return "mixed_like"


def build_event_groups(template: pd.DataFrame) -> pd.DataFrame:
    if template.empty:
        return pd.DataFrame(columns=GROUP_COLS)
    valid = template[template["representative_date"].astype(str).ne("")].copy()
    if valid.empty:
        return pd.DataFrame(columns=GROUP_COLS)
    rows = []
    for (site, review_group, rep_date), group in valid.groupby(["site", "review_group", "representative_date"], dropna=False):
        panel_ids = sorted(group["panel_id"].astype(str).unique().tolist())
        bucket_counts = group["candidate_bucket"].astype(str).value_counts()
        view_counts = group["our_primary_view"].astype(str).value_counts()
        bucket_bits = [f"{k} {v}" for k, v in bucket_counts.items()]
        view_bits = [f"{k} {v}" for k, v in view_counts.items()]
        start_dates = pd.to_datetime(group["our_first_anomaly_date"], errors="coerce").dropna()
        event_start_date = start_dates.min().strftime("%Y-%m-%d") if not start_dates.empty else rep_date
        if pd.notna(pd.to_datetime(rep_date, errors="coerce")) and pd.notna(pd.to_datetime(event_start_date, errors="coerce")):
            if pd.to_datetime(event_start_date, errors="coerce") > pd.to_datetime(rep_date, errors="coerce"):
                event_start_date = rep_date
        rows.append(
            {
                "site": site,
                "review_group": review_group,
                "representative_date": rep_date,
                "event_start_date": event_start_date,
                "event_end_date": rep_date,
                "panel_count": len(panel_ids),
                "panel_ids": "|".join(panel_ids),
                "summary": f"{len(panel_ids)} panels; bucket {', '.join(bucket_bits)}; view {', '.join(view_bits)}",
                "likely_common_issue": likely_common_issue(group),
            }
        )
    return pd.DataFrame(rows, columns=GROUP_COLS).sort_values(
        ["site", "representative_date"], na_position="last"
    ).reset_index(drop=True)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    template, source_counts = build_template(root)
    groups = build_event_groups(template)
    anomaly_after_rep = int(
        (
            pd.to_datetime(template.get("our_first_anomaly_date"), errors="coerce")
            > pd.to_datetime(template.get("representative_date"), errors="coerce")
        ).fillna(False).sum()
    ) if not template.empty else 0
    group_start_after_end = int(
        (
            pd.to_datetime(groups.get("event_start_date"), errors="coerce")
            > pd.to_datetime(groups.get("event_end_date"), errors="coerce")
        ).fillna(False).sum()
    ) if not groups.empty else 0

    csv_path = share_dir / "field_truth_template.csv"
    xlsx_path = share_dir / "field_truth_template.xlsx"
    groups_path = share_dir / "site_event_groups_latest.csv"

    template.to_csv(csv_path, index=False, encoding="utf-8-sig")
    groups.to_csv(groups_path, index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        template.to_excel(writer, sheet_name="field_truth_template", index=False)
        groups.to_excel(writer, sheet_name="site_event_groups", index=False)

    print(f"[OK] wrote {csv_path}")
    print(f"[OK] wrote {xlsx_path}")
    print(f"[OK] wrote {groups_path}")
    print(f"[COUNT] template_rows={len(template)}")
    print(f"[COUNT] event_groups={len(groups)}")
    for key in SOURCE_COUNT_KEYS:
        print(f"[COUNT] {key}={source_counts.get(key, 0)}")
    print(f"[WARNCOUNT] rows_our_first_anomaly_after_representative={anomaly_after_rep}")
    print(f"[WARNCOUNT] groups_event_start_after_event_end={group_start_after_end}")


if __name__ == "__main__":
    main()
