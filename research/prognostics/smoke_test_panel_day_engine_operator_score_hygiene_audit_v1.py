#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

KEY_COLS = ["site", "panel_id", "run_start_date", "run_end_date"]
REGISTRY_COLS = [
    *KEY_COLS,
    "run_day_count",
    "run_shape_class",
    "cohort_hint",
    "fate_class",
    "status",
    "action_bucket",
    "overlap_case_class",
    "queue_eligible_flag",
    "backlog_flag",
    "future_fault_linked_flag",
    "future_truth_linked_flag",
    "electrical_core_score",
    "electrical_core_minus_broadshape_050",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
]
QUEUE_BACKLOG_COLS = KEY_COLS
FEATURE_COLS = [*KEY_COLS, "mean_signal_count", "max_signal_count", "p95_recon_error"]
V0_COLS = [*KEY_COLS, "electrical_core_score", "electrical_core_minus_broadshape_050"]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def robust_scale(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    median = float(numeric.median())
    q1 = float(numeric.quantile(0.25))
    q3 = float(numeric.quantile(0.75))
    iqr = q3 - q1
    denom = iqr if abs(iqr) > 1e-9 else 1.0
    return ((numeric.fillna(median) - median) / denom).clip(-5.0, 5.0)


def compute_scores(feature_df: pd.DataFrame) -> pd.DataFrame:
    out = feature_df.copy()
    out["core_vdrop_term"] = robust_scale(out["max_v_drop"])
    out["core_midv_term"] = robust_scale(1.0 - out["min_mid_v_ratio"])
    out["core_mid_term"] = robust_scale(1.0 - out["min_mid_ratio"])
    out["evtonly_bonus_term"] = robust_scale(out["cond_evt_only_day_ratio"])
    broadshape_penalty = (
        robust_scale(out["ae_mid_or_hi_early_day_ratio"])
        + robust_scale(out["mean_signal_count"])
        + robust_scale(out["max_signal_count"])
        + robust_scale(out["p95_recon_error"])
    )
    out["electrical_core_score"] = (
        out["core_vdrop_term"] + out["core_midv_term"] + out["core_mid_term"]
    )
    out["electrical_core_minus_broadshape_050"] = out["electrical_core_score"] - 0.50 * broadshape_penalty
    return out


def make_run(
    site: str,
    panel_id: str,
    date: str,
    rank_seed: float,
    *,
    max_v_drop: float,
    min_mid_v_ratio: float,
    min_mid_ratio: float,
    cond_evt_only_day_ratio: float,
    ae_mid_or_hi_early_day_ratio: float,
    mean_signal_count: float,
    max_signal_count: float,
    p95_recon_error: float,
    status: str = "historical_run",
    action_bucket: str = "historical_archive",
    queue_eligible_flag: int = 0,
    backlog_flag: int = 0,
) -> dict[str, object]:
    return {
        "site": site,
        "panel_id": panel_id,
        "run_start_date": date,
        "run_end_date": date,
        "run_day_count": 1,
        "run_shape_class": "short_alert_run",
        "cohort_hint": "unmatched_other",
        "fate_class": "",
        "status": status,
        "action_bucket": action_bucket,
        "overlap_case_class": "unmatched_to_review",
        "queue_eligible_flag": queue_eligible_flag,
        "backlog_flag": backlog_flag,
        "future_fault_linked_flag": 0,
        "future_truth_linked_flag": 0,
        "electrical_core_score": 0.0,
        "electrical_core_minus_broadshape_050": 0.0,
        "max_v_drop": max_v_drop,
        "min_mid_v_ratio": min_mid_v_ratio,
        "min_mid_ratio": min_mid_ratio,
        "cond_evt_only_day_ratio": cond_evt_only_day_ratio,
        "ae_mid_or_hi_early_day_ratio": ae_mid_or_hi_early_day_ratio,
        "mean_signal_count": mean_signal_count,
        "max_signal_count": max_signal_count,
        "p95_recon_error": p95_recon_error,
        "rank_seed": rank_seed,
    }


def build_fixture_root(tmp_root: Path) -> None:
    rows: list[dict[str, object]] = []
    for idx in range(1, 25):
        rows.append(
            make_run(
                "alpha",
                f"alpha.reg.{idx:02d}",
                f"2025-01-{idx:02d}",
                rank_seed=float(idx),
                max_v_drop=1.20 - idx * 0.02,
                min_mid_v_ratio=0.20 + idx * 0.01,
                min_mid_ratio=0.18 + idx * 0.01,
                cond_evt_only_day_ratio=0.20,
                ae_mid_or_hi_early_day_ratio=0.15,
                mean_signal_count=1.5,
                max_signal_count=2.0,
                p95_recon_error=0.20,
                status="historical_run",
                action_bucket="historical_archive",
            )
        )
    rows.append(
        make_run(
            "alpha",
            "alpha.outlier",
            "2025-01-25",
            rank_seed=25.0,
            max_v_drop=0.95,
            min_mid_v_ratio=0.25,
            min_mid_ratio=0.25,
            cond_evt_only_day_ratio=0.25,
            ae_mid_or_hi_early_day_ratio=8.0,
            mean_signal_count=60.0,
            max_signal_count=75.0,
            p95_recon_error=12.0,
            status="recurring_run",
            action_bucket="recurring_backlog",
            queue_eligible_flag=0,
            backlog_flag=1,
        )
    )
    for idx in range(1, 6):
        rows.append(
            make_run(
                "beta",
                f"beta.reg.{idx:02d}",
                f"2025-02-0{idx}",
                rank_seed=float(idx),
                max_v_drop=0.60 - idx * 0.01,
                min_mid_v_ratio=0.45 + idx * 0.01,
                min_mid_ratio=0.40 + idx * 0.01,
                cond_evt_only_day_ratio=0.18,
                ae_mid_or_hi_early_day_ratio=0.18,
                mean_signal_count=1.8,
                max_signal_count=2.1,
                p95_recon_error=0.22,
                status="ongoing_run" if idx == 1 else "historical_run",
                action_bucket="investigate_now" if idx == 1 else "historical_archive",
                queue_eligible_flag=1 if idx == 1 else 0,
                backlog_flag=0,
            )
        )

    feature_df = pd.DataFrame(rows)
    scored = compute_scores(feature_df)

    registry_rows = []
    feature_rows = []
    v0_rows = []
    queue_rows = []
    backlog_rows = []
    for _, row in scored.iterrows():
        registry_rows.append(
            {
                **{col: row[col] for col in KEY_COLS},
                "run_day_count": row["run_day_count"],
                "run_shape_class": row["run_shape_class"],
                "cohort_hint": row["cohort_hint"],
                "fate_class": row["fate_class"],
                "status": row["status"],
                "action_bucket": row["action_bucket"],
                "overlap_case_class": row["overlap_case_class"],
                "queue_eligible_flag": row["queue_eligible_flag"],
                "backlog_flag": row["backlog_flag"],
                "future_fault_linked_flag": row["future_fault_linked_flag"],
                "future_truth_linked_flag": row["future_truth_linked_flag"],
                "electrical_core_score": row["electrical_core_score"],
                "electrical_core_minus_broadshape_050": row["electrical_core_minus_broadshape_050"],
                "max_v_drop": row["max_v_drop"],
                "min_mid_v_ratio": row["min_mid_v_ratio"],
                "min_mid_ratio": row["min_mid_ratio"],
                "cond_evt_only_day_ratio": row["cond_evt_only_day_ratio"],
                "ae_mid_or_hi_early_day_ratio": row["ae_mid_or_hi_early_day_ratio"],
            }
        )
        feature_rows.append(
            {
                **{col: row[col] for col in KEY_COLS},
                "mean_signal_count": row["mean_signal_count"],
                "max_signal_count": row["max_signal_count"],
                "p95_recon_error": row["p95_recon_error"],
            }
        )
        v0_rows.append(
            {
                **{col: row[col] for col in KEY_COLS},
                "electrical_core_score": row["electrical_core_score"],
                "electrical_core_minus_broadshape_050": row["electrical_core_minus_broadshape_050"],
            }
        )
        if int(row["queue_eligible_flag"]) == 1:
            queue_rows.append({col: row[col] for col in KEY_COLS})
        if int(row["backlog_flag"]) == 1:
            backlog_rows.append({col: row[col] for col in KEY_COLS})

    write_csv(tmp_root / "_share" / "panel_day_engine_operator_run_registry_v1.csv", registry_rows, REGISTRY_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_operator_run_queue_v1.csv", queue_rows, QUEUE_BACKLOG_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_operator_run_backlog_v1.csv", backlog_rows, QUEUE_BACKLOG_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_feature_table_v1.csv", feature_rows, FEATURE_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_ranker_v0_scores.csv", v0_rows, V0_COLS)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="operator_score_hygiene_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        compile_result = run(
            [
                sys.executable,
                "-m",
                "py_compile",
                "research/prognostics/build_panel_day_engine_operator_score_hygiene_audit_v1.py",
                "research/prognostics/smoke_test_panel_day_engine_operator_score_hygiene_audit_v1.py",
            ],
            repo_root,
        )
        assert_true(compile_result.returncode == 0, compile_result.stderr)

        build_result = run(
            [
                sys.executable,
                "research/prognostics/build_panel_day_engine_operator_score_hygiene_audit_v1.py",
                "--root",
                str(tmp_root),
            ],
            repo_root,
        )
        assert_true(build_result.returncode == 0, build_result.stderr)

        share_dir = tmp_root / "_share"
        summary = pd.read_csv(share_dir / "panel_day_engine_operator_score_hygiene_summary_v1.csv")
        outliers = pd.read_csv(share_dir / "panel_day_engine_operator_score_hygiene_outlier_runs_v1.csv")
        clip = pd.read_csv(share_dir / "panel_day_engine_operator_score_clip_sensitivity_v1.csv")

        assert_true(not summary.empty, "summary output should not be empty")
        assert_true(not outliers.empty, "outlier output should not be empty")
        assert_true(not clip.empty, "clip output should not be empty")

        assert_true("alpha.outlier" in set(outliers["panel_id"]), "synthetic outlier should be flagged")
        outlier_row = outliers.loc[outliers["panel_id"] == "alpha.outlier"].iloc[0]
        assert_true(int(outlier_row["suspicious_feature_count"]) >= 1, "outlier should trigger suspicious features")
        assert_true(pd.notna(outlier_row["broadshape_penalty_term"]), "contribution term should be emitted")

        overall_summary = summary.loc[(summary["record_type"] == "scope_summary") & (summary["site"].fillna("") == "")]
        assert_true(len(overall_summary) == 1, "overall summary row missing")
        overall_row = overall_summary.iloc[0]
        assert_true(int(overall_row["suspicious_run_count"]) >= 1, "overall suspicious count should be positive")
        assert_true(int(overall_row["suspicious_backlog_run_count"]) >= 1, "backlog suspicious count should be positive")

        clip_summary = clip.loc[(clip["record_type"] == "summary") & (clip["scope_name"] == "overall")]
        assert_true(len(clip_summary) == 1, "overall clip summary missing")
        clip_row = clip_summary.iloc[0]
        for col in ["top20_overlap_rate", "top50_overlap_rate", "top100_overlap_rate"]:
            overlap = float(clip_row[col])
            assert_true(0.0 <= overlap <= 1.0, f"{col} should be a valid rate")

        largest_shift = clip.loc[clip["record_type"] == "largest_shift"].copy()
        assert_true(not largest_shift.empty, "largest shift table should be populated")
        score_delta = (largest_shift["raw_score"] - largest_shift["clipped_score"]).abs()
        assert_true(score_delta.gt(1e-9).any(), "clipping should change at least one synthetic score")


if __name__ == "__main__":
    main()
