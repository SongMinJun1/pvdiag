#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import pandas as pd

SITES = ["kernelog1", "sinhyo", "gangui", "ktc_ess"]
HISTORY_COLS = [
    "snapshot_date",
    "site",
    "panel_id",
    "alert_rule",
    "risk_ens",
    "risk_day",
    "diagnosis_date_online",
    "critical_diag_date",
    "dead_diag_date",
    "final_fault",
    "phenotype",
    "dominant_family",
    "top_score",
    "evidence_strength",
    "phenotype_event_date",
    "run_timestamp",
    "run_exit_code",
]


def read_csv_or_empty(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def parse_status(path: Path) -> tuple[str | pd.NA, float | pd.NA]:
    if not path.exists():
        return pd.NA, pd.NA
    timestamp = pd.NA
    exit_code = pd.NA
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("timestamp="):
            timestamp = line.split("=", 1)[1].strip()
        elif line.startswith("exit_code="):
            try:
                exit_code = float(line.split("=", 1)[1].strip())
            except ValueError:
                exit_code = pd.NA
    return timestamp, exit_code


def first_value(df: pd.DataFrame, col: str):
    if df.empty or col not in df.columns:
        return pd.NA
    val = df.iloc[0][col]
    return val if pd.notna(val) else pd.NA


def latest_event_counts(site: str, out_dir: Path) -> dict[str, int]:
    path = out_dir / "latest_event_phenotypes.csv"
    df = read_csv_or_empty(path)
    if df.empty:
        return {
            "compound_count": 0,
            "unclear_count": 0,
            "dominant_electrical_count": 0,
            "dominant_shape_count": 0,
            "dominant_instability_count": 0,
        }
    return {
        "compound_count": int(df.get("phenotype", pd.Series(dtype=object)).astype(str).eq("compound").sum()),
        "unclear_count": int(df.get("phenotype", pd.Series(dtype=object)).astype(str).eq("unclear").sum()),
        "dominant_electrical_count": int(df.get("dominant_family", pd.Series(dtype=object)).astype(str).eq("electrical").sum()),
        "dominant_shape_count": int(df.get("dominant_family", pd.Series(dtype=object)).astype(str).eq("shape").sum()),
        "dominant_instability_count": int(df.get("dominant_family", pd.Series(dtype=object)).astype(str).eq("instability").sum()),
    }


def ensure_cols(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        if col not in out.columns:
            out[col] = pd.NA
    return out[cols]


def process_site(root: Path, site: str, run_timestamp, run_exit_code) -> pd.DataFrame:
    out_dir = root / "data" / site / "out"
    alerts_path = out_dir / "latest_alerts_enriched.csv"
    status_path = out_dir / "latest_panel_status_enriched.csv"
    summary_path = out_dir / "latest_site_summary.csv"
    history_path = out_dir / "alert_history.csv"
    new_path = out_dir / "new_alerts_today.csv"
    resolved_path = out_dir / "resolved_alerts_today.csv"
    rollup_path = out_dir / "site_daily_rollup.csv"

    alerts = read_csv_or_empty(alerts_path)
    _status = read_csv_or_empty(status_path)
    summary = read_csv_or_empty(summary_path)
    if summary.empty:
        raise FileNotFoundError(summary_path)
    snapshot_date = str(first_value(summary, "latest_date"))

    alerts = alerts.copy()
    alerts["snapshot_date"] = snapshot_date
    alerts["site"] = site
    alerts["run_timestamp"] = run_timestamp
    alerts["run_exit_code"] = run_exit_code
    alerts = ensure_cols(alerts, HISTORY_COLS)

    history = read_csv_or_empty(history_path)
    if not history.empty:
        history = ensure_cols(history, HISTORY_COLS)
        same_snapshot = history["site"].astype(str).eq(site) & history["snapshot_date"].astype(str).eq(snapshot_date)
        history = history.loc[~same_snapshot].copy()
        prev_dates = pd.to_datetime(
            history.loc[history["site"].astype(str).eq(site), "snapshot_date"], errors="coerce"
        ).dropna()
    else:
        prev_dates = pd.Series(dtype="datetime64[ns]")

    prev_snapshot = prev_dates.max().date().isoformat() if not prev_dates.empty else None
    prev_rows = history[(history["site"].astype(str) == site) & (history["snapshot_date"].astype(str) == prev_snapshot)].copy() if prev_snapshot else pd.DataFrame(columns=HISTORY_COLS)

    current_panel_ids = set(alerts.get("panel_id", pd.Series(dtype=object)).astype(str))
    prev_panel_ids = set(prev_rows.get("panel_id", pd.Series(dtype=object)).astype(str))

    new_alerts = alerts[alerts.get("panel_id", pd.Series(dtype=object)).astype(str).isin(current_panel_ids - prev_panel_ids)].copy()
    resolved_alerts = prev_rows[prev_rows.get("panel_id", pd.Series(dtype=object)).astype(str).isin(prev_panel_ids - current_panel_ids)].copy()
    if not resolved_alerts.empty:
        resolved_alerts.insert(len(resolved_alerts.columns), "resolved_on_snapshot_date", snapshot_date)

    updated_history = pd.concat([history, alerts], ignore_index=True)
    updated_history = updated_history.sort_values(["snapshot_date", "site", "panel_id", "run_timestamp"], na_position="last")
    updated_history = updated_history.drop_duplicates(["snapshot_date", "site", "panel_id"], keep="last")
    updated_history.to_csv(history_path, index=False, encoding="utf-8-sig")
    new_alerts.to_csv(new_path, index=False, encoding="utf-8-sig")
    resolved_alerts.to_csv(resolved_path, index=False, encoding="utf-8-sig")

    counts = latest_event_counts(site, out_dir)
    rollup_row = {
        "snapshot_date": snapshot_date,
        "site": site,
        "panel_count": first_value(summary, "panel_count"),
        "alert_count": first_value(summary, "alert_count"),
        "new_alert_count": int(len(new_alerts)),
        "resolved_alert_count": int(len(resolved_alerts)),
        "online_diag_count": first_value(summary, "online_diag_count"),
        "critical_count": first_value(summary, "critical_count"),
        "dead_count": first_value(summary, "dead_count"),
        "final_fault_count": first_value(summary, "final_fault_count"),
        "dominant_electrical_count": counts["dominant_electrical_count"],
        "dominant_shape_count": counts["dominant_shape_count"],
        "dominant_instability_count": counts["dominant_instability_count"],
        "compound_count": counts["compound_count"],
        "unclear_count": counts["unclear_count"],
        "run_exit_code": run_exit_code,
    }
    rollup = read_csv_or_empty(rollup_path)
    if not rollup.empty:
        rollup = rollup.loc[~(
            rollup.get("site", pd.Series(dtype=object)).astype(str).eq(site)
            & rollup.get("snapshot_date", pd.Series(dtype=object)).astype(str).eq(snapshot_date)
        )].copy()
    rollup = pd.concat([rollup, pd.DataFrame([rollup_row])], ignore_index=True)
    rollup = rollup.sort_values(["snapshot_date", "site"], na_position="last")
    rollup = rollup.drop_duplicates(["snapshot_date", "site"], keep="last")
    rollup.to_csv(rollup_path, index=False, encoding="utf-8-sig")

    print(f"[OK] {site}: wrote {history_path.name}, {new_path.name}, {resolved_path.name}, {rollup_path.name}")
    return pd.DataFrame([rollup_row])


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    run_timestamp, run_exit_code = parse_status(root / "_ops_runtime_logs" / "latest.status")
    latest_rows = []
    for site in SITES:
        latest_rows.append(process_site(root, site, run_timestamp, run_exit_code))
    combined = pd.concat(latest_rows, ignore_index=True)
    out_path = root / "_share" / "ops_daily_rollup_latest.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[OK] wrote {out_path}")


if __name__ == "__main__":
    main()
