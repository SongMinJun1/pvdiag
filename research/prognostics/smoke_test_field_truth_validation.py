#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd

TRUTH_COL = "issue_detected_date"
CANONICAL_TEMPLATE_COLS = [
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


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    share_dir = root / "_share"
    build_script = root / "research" / "prognostics" / "build_field_truth_template.py"
    eval_script = root / "research" / "prognostics" / "evaluate_field_truth.py"

    build_res = run([sys.executable, str(build_script)], root)
    assert_true(build_res.returncode == 0, f"build no-truth smoke failed:\n{build_res.stdout}\n{build_res.stderr}")

    eval_res = run([sys.executable, str(eval_script)], root)
    assert_true(eval_res.returncode == 0, f"evaluate no-truth smoke failed:\n{eval_res.stdout}\n{eval_res.stderr}")

    template_path = share_dir / "field_truth_template.csv"
    meta_path = share_dir / "field_truth_template_meta.csv"
    lead_path = share_dir / "field_validation_leadtime.csv"
    match_path = share_dir / "field_validation_phenotype_match.csv"
    template = pd.read_csv(template_path, low_memory=False)
    meta = pd.read_csv(meta_path, low_memory=False)

    assert_true(
        template.columns.tolist() == CANONICAL_TEMPLATE_COLS,
        f"canonical template columns drifted: {template.columns.tolist()}",
    )

    assert_true(
        meta["our_first_anomaly_source"].fillna("").astype(str).str.strip().ne("").all(),
        "meta contains blank our_first_anomaly_source",
    )

    current_review_rows = meta[meta["our_first_anomaly_source"] == "current_review_fallback"].copy()
    if not current_review_rows.empty:
        assert_true(
            current_review_rows["confidence_level"].fillna("").astype(str).eq("low").all(),
            "current_review_fallback rows must have confidence_level=low",
        )
        assert_true(
            pd.to_numeric(current_review_rows["abstain_flag"], errors="coerce").fillna(0).eq(1).all(),
            "current_review_fallback rows must have abstain_flag=1",
        )

    lead_lines = lead_path.read_text(encoding="utf-8-sig").splitlines()
    match_lines = match_path.read_text(encoding="utf-8-sig").splitlines()
    assert_true(len(lead_lines) == 1, "field_validation_leadtime.csv must be header-only in no-truth state")
    assert_true(len(match_lines) == 1, "field_validation_phenotype_match.csv must be header-only in no-truth state")

    original_bytes = template_path.read_bytes()
    try:
        temp = template.copy()
        assert_true(not temp.empty, "template is unexpectedly empty")
        temp[TRUTH_COL] = temp[TRUTH_COL].astype(object)
        temp.loc[temp.index[0], TRUTH_COL] = "2099-01-01"
        temp.to_csv(template_path, index=False, encoding="utf-8-sig")

        blocked_res = run([sys.executable, str(build_script)], root)
        combined = f"{blocked_res.stdout}\n{blocked_res.stderr}"
        assert_true(blocked_res.returncode != 0, "overwrite protection did not block truth-filled template")
        assert_true(
            "--force-overwrite-truth" in combined,
            "overwrite protection message did not mention --force-overwrite-truth",
        )
    finally:
        template_path.write_bytes(original_bytes)

    print("[OK] build/evaluate no-truth smoke path")
    print("[OK] canonical template columns stable")
    print("[OK] no blank our_first_anomaly_source in meta")
    print(f"[OK] current_review_fallback_rows={len(current_review_rows)}")
    print("[OK] no-truth detail files are header-only")
    print("[OK] overwrite protection blocks truth-filled template without --force-overwrite-truth")


if __name__ == "__main__":
    main()
