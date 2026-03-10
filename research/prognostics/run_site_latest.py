#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd


DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
DEFAULT_ALERT_TOPN = 20


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Run latest site operation wrapper with fixed train window and auto latest score end")
    ap.add_argument("--site", required=True, help="Site key matching configs/sites/<site>.yaml")
    ap.add_argument("--dry-run", action="store_true", help="Print resolved paths and commands without executing")
    ap.add_argument("--skip-scores", action="store_true", help="Skip run_scores_pipeline.py and build latest views from existing outputs")
    return ap.parse_args()


def load_simple_yaml(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise RuntimeError(f"Invalid yaml line in {path}: {raw_line}")
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    required = ["site", "train_start", "train_end", "score_start", "raw_dir", "out_dir"]
    missing = [k for k in required if k not in data]
    if missing:
        raise RuntimeError(f"Missing required keys in {path}: {missing}")
    return data


def detect_latest_raw_date(raw_dir: Path) -> pd.Timestamp:
    dates: list[pd.Timestamp] = []
    for path in raw_dir.rglob("*.csv"):
        if "/out/" in str(path):
            continue
        m = DATE_RE.search(path.name)
        if not m:
            continue
        dt = pd.to_datetime(m.group(1), errors="coerce")
        if pd.notna(dt):
            dates.append(dt.normalize())
    if not dates:
        raise RuntimeError(f"No YYYY-MM-DD filename found under {raw_dir}")
    return max(dates)


def run_cmd(cmd: list[str], dry_run: bool) -> None:
    print("[RUN]", " ".join(cmd))
    if dry_run:
        return
    subprocess.run(cmd, check=True)


def existing_table(out_dir: Path) -> Path:
    candidates = [
        out_dir / "panel_day_risk_ensemble.csv",
        out_dir / "panel_day_risk_transition.csv",
        out_dir / "panel_day_risk.csv",
        out_dir / "panel_day_core.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(f"No panel-day table found in {out_dir}")


def as_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)
    return pd.to_numeric(series, errors="coerce").fillna(0).ne(0)


def date_present(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(False, index=df.index)
    return pd.to_datetime(df[col], errors="coerce").notna()


def optional_phenotype_table(site: str) -> pd.DataFrame:
    path = Path("_share/site_event_phenotypes_latest.csv")
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    need = {"site", "panel_id", "event_date"}
    if not need.issubset(df.columns):
        return pd.DataFrame()
    df = df[df["site"].astype(str) == site].copy()
    if df.empty:
        return df
    df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce")
    df = df.sort_values(["panel_id", "event_date"]).drop_duplicates("panel_id", keep="last")
    keep = [c for c in ["panel_id", "dominant_family", "phenotype", "top_score", "evidence_strength"] if c in df.columns]
    return df[keep].copy()


def build_latest_outputs(site: str, out_dir: Path, dry_run: bool) -> tuple[Path, Path, Path]:
    status_path = out_dir / "latest_panel_status.csv"
    alerts_path = out_dir / "latest_alerts.csv"
    summary_path = out_dir / "latest_site_summary.csv"
    if dry_run:
        print(f"[INFO] latest source table: {out_dir}/panel_day_risk_ensemble.csv (preferred), fallback to transition/risk/core")
        return status_path, alerts_path, summary_path
    table_path = existing_table(out_dir)
    print(f"[INFO] latest source table: {table_path}")

    df = pd.read_csv(table_path, low_memory=False)
    if "date" not in df.columns or "panel_id" not in df.columns:
        raise RuntimeError(f"{table_path} must contain date and panel_id")
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df = df[df["date"].notna()].copy()
    latest_date = df["date"].max()
    latest = df[df["date"] == latest_date].copy()
    latest.insert(0, "site", site)

    pheno = optional_phenotype_table(site)
    if not pheno.empty:
        latest = latest.merge(pheno, on="panel_id", how="left")

    status_cols = [
        "site",
        "panel_id",
        "date",
        "risk_ens",
        "risk_day",
        "diagnosis_date_online",
        "critical_diag_date",
        "dead_diag_date",
        "final_fault",
        "dominant_family",
        "phenotype",
        "top_score",
        "evidence_strength",
    ]
    latest_status = latest[[c for c in status_cols if c in latest.columns]].copy()

    final_fault = as_bool(latest.get("final_fault", pd.Series(False, index=latest.index)))
    dead_eff = as_bool(latest.get("state_dead_eff", pd.Series(False, index=latest.index)))
    crit_eff = as_bool(latest.get("critical_like_eff", pd.Series(False, index=latest.index)))
    priority_mask = (
        date_present(latest, "diagnosis_date_online")
        | date_present(latest, "critical_diag_date")
        | date_present(latest, "dead_diag_date")
        | final_fault
        | dead_eff
        | crit_eff
    )
    if bool(priority_mask.any()):
        alerts = latest[priority_mask].copy()
        alert_rule = "diagnosis/critical/dead/final-fault priority"
    else:
        sort_col = "risk_ens" if "risk_ens" in latest.columns else ("risk_day" if "risk_day" in latest.columns else None)
        alerts = latest.sort_values(sort_col, ascending=False, na_position="last").head(DEFAULT_ALERT_TOPN).copy() if sort_col else latest.head(0).copy()
        alert_rule = f"top-{DEFAULT_ALERT_TOPN} by {sort_col or 'none'}"
    alerts.insert(1, "alert_rule", alert_rule)
    alert_cols = [
        "site",
        "alert_rule",
        "panel_id",
        "date",
        "risk_ens",
        "risk_day",
        "diagnosis_date_online",
        "critical_diag_date",
        "dead_diag_date",
        "final_fault",
        "dominant_family",
        "phenotype",
    ]
    latest_alerts = alerts[[c for c in alert_cols if c in alerts.columns]].copy()

    site_summary = pd.DataFrame(
        [
            {
                "site": site,
                "latest_date": latest_date.date().isoformat(),
                "panel_count": int(len(latest)),
                "alert_count": int(len(latest_alerts)),
                "online_diag_count": int(date_present(latest, "diagnosis_date_online").sum()),
                "critical_count": int(date_present(latest, "critical_diag_date").sum()) if "critical_diag_date" in latest.columns else int(crit_eff.sum()),
                "dead_count": int(date_present(latest, "dead_diag_date").sum()) if "dead_diag_date" in latest.columns else int(dead_eff.sum()),
                "final_fault_count": int(final_fault.sum()),
            }
        ]
    )

    latest_status.to_csv(status_path, index=False, encoding="utf-8-sig")
    latest_alerts.to_csv(alerts_path, index=False, encoding="utf-8-sig")
    site_summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    print(f"[OK] wrote {status_path}")
    print(f"[OK] wrote {alerts_path}")
    print(f"[OK] wrote {summary_path}")
    return status_path, alerts_path, summary_path


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]
    cfg_path = root / "configs" / "sites" / f"{args.site}.yaml"
    if not cfg_path.exists():
        raise FileNotFoundError(cfg_path)
    cfg = load_simple_yaml(cfg_path)
    raw_dir = (root / cfg["raw_dir"]).resolve()
    out_dir = (root / cfg["out_dir"]).resolve()
    latest_raw_date = detect_latest_raw_date(raw_dir)

    print(f"[INFO] site={cfg['site']}")
    print(f"[INFO] config={cfg_path}")
    print(f"[INFO] raw_dir={raw_dir}")
    print(f"[INFO] out_dir={out_dir}")
    print(f"[INFO] train={cfg['train_start']} .. {cfg['train_end']}")
    print(f"[INFO] score={cfg['score_start']} .. {latest_raw_date.date().isoformat()}")

    engine_cmd = [
        sys.executable,
        str(root / "pv_ae" / "panel_day_engine.py"),
        "--site",
        cfg["site"],
        "--train-start",
        cfg["train_start"],
        "--train-end",
        cfg["train_end"],
        "--eval-start",
        cfg["score_start"],
        "--eval-end",
        latest_raw_date.date().isoformat(),
        "--out-dir",
        str(out_dir),
    ]
    run_cmd(engine_cmd, args.dry_run)

    if not args.skip_scores:
        scores_cmd = [
            sys.executable,
            str(root / "research" / "prognostics" / "run_scores_pipeline.py"),
            "--scores-path",
            str(out_dir / "panel_day_core.csv"),
            "--out-dir",
            str(out_dir),
        ]
        run_cmd(scores_cmd, args.dry_run)
    else:
        print("[INFO] --skip-scores enabled; using existing post-processed outputs if present")

    build_latest_outputs(cfg["site"], out_dir, args.dry_run)


if __name__ == "__main__":
    main()
