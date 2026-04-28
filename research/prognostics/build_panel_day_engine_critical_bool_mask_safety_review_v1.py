#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd


ENGINE_SOURCE = Path("pv_ae/panel_day_engine.py")
ENGINE_PACKAGE = Path("release/conalog_full_runtime_v1/package/pv_ae/panel_day_engine.py")
DETAIL_OUTPUT_NAME = "panel_day_engine_critical_bool_mask_safety_review_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_critical_bool_mask_safety_review_summary_v1.csv"
OLD_PATTERNS = [
    'out["critical_fault"] == True',
    "out['critical_fault'] == True",
]
NEW_MASK = 'critical_fault_mask = out["critical_fault"].fillna(False).astype(bool)'
DETAIL_COLS = [
    "check_id",
    "pass_flag",
    "source_value",
    "package_value",
    "requirement",
    "interpretation_ko",
]
SUMMARY_COLS = [
    "overall_status",
    "source_package_hash_equal",
    "source_old_bool_equality_count",
    "package_old_bool_equality_count",
    "source_new_mask_count",
    "package_new_mask_count",
    "behavior_change_claim_allowed",
    "next_required_action",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit the panel_day_engine critical_fault boolean-mask cleanup. "
            "This is a safety review, not a performance evaluation."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def read_text(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def sha256_file(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"missing file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_old_patterns(text: str) -> int:
    return sum(text.count(pattern) for pattern in OLD_PATTERNS)


def row(
    check_id: str,
    passed: bool,
    source_value: object,
    package_value: object,
    requirement: str,
    interpretation_ko: str,
) -> dict[str, object]:
    return {
        "check_id": check_id,
        "pass_flag": int(passed),
        "source_value": source_value,
        "package_value": package_value,
        "requirement": requirement,
        "interpretation_ko": interpretation_ko,
    }


def build_review(repo_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    source_path = repo_root / ENGINE_SOURCE
    package_path = repo_root / ENGINE_PACKAGE
    source_text = read_text(source_path)
    package_text = read_text(package_path)
    source_hash = sha256_file(source_path)
    package_hash = sha256_file(package_path)
    source_old_count = count_old_patterns(source_text)
    package_old_count = count_old_patterns(package_text)
    source_new_count = source_text.count(NEW_MASK)
    package_new_count = package_text.count(NEW_MASK)
    detail = pd.DataFrame(
        [
            row(
                "source_package_hash_equal",
                source_hash == package_hash,
                source_hash,
                package_hash,
                "source and package panel_day_engine.py must be byte-identical",
                "source/package mirror drift를 막는다.",
            ),
            row(
                "old_bool_equality_removed",
                source_old_count == 0 and package_old_count == 0,
                source_old_count,
                package_old_count,
                "targeted critical_fault == True comparisons must be removed",
                "pandas bool mask를 명시적으로 재사용하게 한다.",
            ),
            row(
                "new_bool_mask_present_once",
                source_new_count == 1 and package_new_count == 1,
                source_new_count,
                package_new_count,
                "critical_fault_mask must be introduced exactly once in each mirror",
                "동작 변경이 아니라 동일 mask 재사용 cleanup임을 확인한다.",
            ),
        ],
        columns=DETAIL_COLS,
    )
    overall_status = "pass" if int(detail["pass_flag"].sum()) == len(detail) else "fail"
    summary = pd.DataFrame(
        [
            {
                "overall_status": overall_status,
                "source_package_hash_equal": int(source_hash == package_hash),
                "source_old_bool_equality_count": source_old_count,
                "package_old_bool_equality_count": package_old_count,
                "source_new_mask_count": source_new_count,
                "package_new_mask_count": package_new_count,
                "behavior_change_claim_allowed": "no_semantic_change_claim_only",
                "next_required_action": "run_prepatch_runbook_scorecard_and_compare",
            }
        ],
        columns=SUMMARY_COLS,
    )
    return detail, summary


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    detail, summary = build_review(args.repo_root)
    detail.to_csv(args.output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    if summary.iloc[0]["overall_status"] != "pass":
        raise SystemExit("critical bool mask safety review failed")


if __name__ == "__main__":
    main()
