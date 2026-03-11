#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ["kernelog1", "sinhyo", "gangui", "ktc_ess"]
DONE_MARKER = "[DONE] all sites completed"


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Check latest ops runtime status and site outputs")
    ap.add_argument("--root", default=".", help="Repository root (default: current directory)")
    return ap.parse_args()


def parse_status(path: Path) -> tuple[bool, float | None]:
    if not path.exists():
        return False, None
    exit_code = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("exit_code="):
            try:
                exit_code = float(line.split("=", 1)[1].strip())
            except ValueError:
                exit_code = None
    return True, exit_code


def log_done(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, ""
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    last_line = lines[-1].strip() if lines else ""
    return DONE_MARKER in last_line, last_line


def first_value(df: pd.DataFrame, col: str):
    if col not in df.columns or df.empty:
        return pd.NA
    value = df.iloc[0][col]
    return value if pd.notna(value) else pd.NA


def health_state(
    status_exists: bool,
    exit_code: float | None,
    summary_exists: bool,
    alerts_exists: bool,
    panel_status_exists: bool,
    done_found: bool,
    final_fault_count,
) -> str:
    if not status_exists or exit_code is None or exit_code != 0 or not summary_exists:
        return "fail"
    if (not done_found) or pd.isna(final_fault_count) or (not alerts_exists) or (not panel_status_exists):
        return "warning"
    return "ok"


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    logs_dir = root / "_ops_runtime_logs"
    status_path = logs_dir / "latest.status"
    log_path = logs_dir / "latest.log"
    out_path = root / "_share" / "ops_healthcheck_latest.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    status_exists, exit_code = parse_status(status_path)
    log_exists = log_path.exists()
    done_found, last_log_line = log_done(log_path)

    rows: list[dict[str, object]] = []
    for site in SITES:
        out_dir = root / "data" / site / "out"
        summary_path = out_dir / "latest_site_summary.csv"
        alerts_path = out_dir / "latest_alerts.csv"
        panel_status_path = out_dir / "latest_panel_status.csv"

        summary_exists = summary_path.exists()
        alerts_exists = alerts_path.exists()
        panel_status_exists = panel_status_path.exists()

        if summary_exists:
            summary_df = pd.read_csv(summary_path)
        else:
            summary_df = pd.DataFrame()

        latest_date = first_value(summary_df, "latest_date")
        panel_count = first_value(summary_df, "panel_count")
        alert_count = first_value(summary_df, "alert_count")
        online_diag_count = first_value(summary_df, "online_diag_count")
        critical_count = first_value(summary_df, "critical_count")
        dead_count = first_value(summary_df, "dead_count")
        final_fault_count = first_value(summary_df, "final_fault_count")

        rows.append(
            {
                "site": site,
                "latest_status_exists": status_exists,
                "latest_status_exit_code": exit_code if exit_code is not None else pd.NA,
                "latest_log_exists": log_exists,
                "latest_log_done_marker": done_found,
                "latest_log_last_line": last_log_line,
                "latest_site_summary_exists": summary_exists,
                "latest_alerts_exists": alerts_exists,
                "latest_panel_status_exists": panel_status_exists,
                "latest_date": latest_date,
                "panel_count": panel_count,
                "alert_count": alert_count,
                "online_diag_count": online_diag_count,
                "critical_count": critical_count,
                "dead_count": dead_count,
                "final_fault_count": final_fault_count,
                "health_state": health_state(
                    status_exists=status_exists,
                    exit_code=exit_code,
                    summary_exists=summary_exists,
                    alerts_exists=alerts_exists,
                    panel_status_exists=panel_status_exists,
                    done_found=done_found,
                    final_fault_count=final_fault_count,
                ),
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False, encoding="utf-8-sig")

    state_order = {"fail": 2, "warning": 1, "ok": 0}
    worst_state = max(df["health_state"].astype(str), key=lambda x: state_order.get(x, -1))
    print(f"[OPS] overall_health={worst_state}")
    print(f"[OPS] latest_status_exists={status_exists} exit_code={exit_code}")
    print(f"[OPS] latest_log_exists={log_exists} done_marker={done_found}")
    for _, row in df.iterrows():
        print(
            "[SITE] "
            f"{row['site']} state={row['health_state']} latest_date={row['latest_date']} "
            f"panel_count={row['panel_count']} alert_count={row['alert_count']} "
            f"online_diag_count={row['online_diag_count']} dead_count={row['dead_count']} "
            f"final_fault_count={row['final_fault_count']}"
        )
    print(f"[OK] wrote {out_path}")


if __name__ == "__main__":
    main()
