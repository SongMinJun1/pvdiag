#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


REQUIRED_PACKAGE_FILES = [
    "DASHBOARD_INTEGRATION.md",
    "EXTERNAL_DELIVERY_GUIDE.md",
    "DELIVERY_QA_CHECKLIST.md",
    "README.md",
    "requirements.txt",
    "app/run_full_algorithm_pack.py",
    "app/import_any_csv_root.py",
    "app/verify_dashboard_outputs.py",
    "app/verify_delivery_package.py",
    "pv_ae/panel_day_engine.py",
    "runtime/windows_x64/runtime_manifest_v1.json",
]

REQUIRED_SHARE_INPUTS = [
    "_share/panel_day_engine_operator_workflow_default_v1.csv",
    "_share/panel_day_engine_abrupt6_symptom_map_v1.csv",
    "_share/panel_day_engine_kernellog_project_mapping_v1.csv",
    "_share/panel_day_engine_gpv7_perf_summary_v1.csv",
    "_share/panel_day_engine_project_final_decision_pack_v1.csv",
    "_share/panel_day_engine_precursor_onset_truth_v1.csv",
    "_share/panel_day_engine_non_precursor_performance_cases_v1.csv",
    "_share/panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv",
    "_share/panel_day_engine_gpvs_panel_attach_inventory_v1.csv",
    "_share/panel_day_engine_gpvs_panel_attach_feasibility_v1.csv",
    "_share/panel_day_engine_gpvs_panel_attach_candidates_v1.csv",
    "_share/panel_day_engine_precursor_abrupt_consistency_cases_v1.csv",
    "_share/panel_day_engine_precursor_abrupt_consistency_summary_v1.csv",
    "_share/panel_day_engine_precursor_abrupt_consistency_recommendation_v1.csv",
    "_share/panel_day_engine_c42997_1_1_forensic_summary_v1.csv",
    "_share/panel_day_engine_fault_panel_event_audit_v1.csv",
    "_share/panel_day_engine_detailed_fault_bridge_audit_v1.csv",
    "_share/panel_day_engine_detailed_fault_bridge_summary_v1.csv",
    "_share/panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv",
    "_share/panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv",
    "_share/panel_day_engine_gpvs_detailed_type_realpanel_sanity_v1.csv",
    "_share/panel_day_engine_gpvs_mlpe_panel_agreement_v1.csv",
    "_share/panel_day_engine_gpvs_canonical_dictionary_v1.csv",
    "_share/panel_day_engine_gpvs_mlpe_fault_matching_table_v1.csv",
    "_share/panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv",
    "_share/panel_day_engine_gpvs_mlpe_fault_matching_summary_v1.csv",
    "_share/panel_day_engine_gpvs_evidence_pack_v1.csv",
    "_share/panel_day_engine_panel_multiaxis_verdict_v1.csv",
    "_share/panel_date_reaudit_working.csv",
]

REQUIRED_RUNTIME_SENTINELS = [
    "runtime/windows_x64/python/python311.zip",
    "runtime/windows_x64/python/Lib/site-packages/torch/utils/data/__init__.py",
    "runtime/windows_x64/python/Lib/site-packages/torch/utils/data/dataloader.py",
    "runtime/windows_x64/python/Lib/site-packages/torch/utils/data/dataset.py",
    "runtime/windows_x64/python/Lib/site-packages/torch/utils/data/sampler.py",
    "runtime/windows_x64/python/Lib/site-packages/torch/ao/pruning/_experimental/data_sparsifier/__init__.py",
    "runtime/windows_x64/python/Lib/site-packages/torch/distributed/elastic/utils/data/__init__.py",
]

FORBIDDEN_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "data",
    "outputs",
    "raw",
    "out",
}

CONTROLLED_TEXT_PATTERNS = [
    "*.md",
    "*.json",
    "*.py",
    "*.bat",
    "*.ps1",
    "*.txt",
]

LOCAL_PATH_NEEDLES = [
    "/Users/",
    "/private/var/folders/",
    "C:\\Users\\",
]

ALLOW_LOCAL_PATH_DOCS = {
    "DELIVERY_QA_CHECKLIST.md",
    "delivery_package_check_v1.json",
    "app/verify_delivery_package.py",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify that the pvdiag delivery package is portable and data-clean."
    )
    parser.add_argument(
        "--package-root",
        type=Path,
        default=None,
        help="Package root to verify. Defaults to this script's parent package when run from package/app.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional JSON report path. Defaults to <package-root>/delivery_package_check_v1.json.",
    )
    return parser.parse_args()


def infer_package_root() -> Path:
    here = Path(__file__).resolve()
    if here.parent.name == "app":
        return here.parent.parent
    raise SystemExit("please pass --package-root when running from the source tree")


def relative_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def find_forbidden_dirs(package_root: Path) -> list[str]:
    hits: list[str] = []
    for path in package_root.rglob("*"):
        if not path.is_dir():
            continue
        rel_parts = path.relative_to(package_root).parts
        if not rel_parts:
            continue
        if rel_parts[:5] == ("runtime", "windows_x64", "python", "Lib", "site-packages"):
            continue
        if path.name in FORBIDDEN_DIR_NAMES:
            hits.append(relative_path(package_root, path))
    return sorted(hits)


def controlled_text_files(package_root: Path) -> list[Path]:
    files: set[Path] = set()
    controlled_roots = [
        package_root,
        package_root / "app",
        package_root / "pv_ae",
        package_root / "research",
        package_root / "artifacts",
        package_root / "bin",
    ]
    for root in controlled_roots:
        if not root.exists():
            continue
        for pattern in CONTROLLED_TEXT_PATTERNS:
            iterator = root.glob(pattern) if root == package_root else root.rglob(pattern)
            files.update(path for path in iterator if path.is_file())
    runtime_manifest = package_root / "runtime" / "windows_x64" / "runtime_manifest_v1.json"
    if runtime_manifest.exists():
        files.add(runtime_manifest)
    return sorted(files)


def find_local_path_leaks(package_root: Path) -> list[dict[str, object]]:
    leaks: list[dict[str, object]] = []
    for path in controlled_text_files(package_root):
        rel = relative_path(package_root, path)
        if rel in ALLOW_LOCAL_PATH_DOCS or Path(rel).name in ALLOW_LOCAL_PATH_DOCS:
            continue
        if path.stat().st_size > 2_000_000:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for needle in LOCAL_PATH_NEEDLES:
            if needle in text:
                leaks.append({"path": rel, "needle": needle})
    return leaks


def find_large_nonruntime_files(package_root: Path) -> list[dict[str, object]]:
    large_files: list[dict[str, object]] = []
    runtime_prefix = ("runtime", "windows_x64")
    for path in package_root.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(package_root).parts
        if rel_parts[:2] == runtime_prefix:
            continue
        size_bytes = path.stat().st_size
        if size_bytes > 20 * 1024 * 1024:
            large_files.append(
                {
                    "path": relative_path(package_root, path),
                    "size_bytes": int(size_bytes),
                }
            )
    return sorted(large_files, key=lambda item: item["path"])


def find_missing_required_files(package_root: Path) -> list[str]:
    required = REQUIRED_PACKAGE_FILES + REQUIRED_SHARE_INPUTS + REQUIRED_RUNTIME_SENTINELS
    return [rel for rel in required if not (package_root / rel).exists()]


def main() -> None:
    args = parse_args()
    package_root = (args.package_root or infer_package_root()).resolve()
    if not package_root.exists():
        raise SystemExit(f"missing package root: {package_root}")

    missing = find_missing_required_files(package_root)
    forbidden_dirs = find_forbidden_dirs(package_root)
    local_path_leaks = find_local_path_leaks(package_root)
    large_nonruntime_files = find_large_nonruntime_files(package_root)
    pycache_dirs = sorted(
        relative_path(package_root, path)
        for path in package_root.rglob("__pycache__")
        if path.is_dir()
    )

    status = "pass"
    failures: list[str] = []
    if missing:
        status = "fail"
        failures.append("missing_required_files")
    if forbidden_dirs:
        status = "fail"
        failures.append("forbidden_dirs")
    if local_path_leaks:
        status = "fail"
        failures.append("local_path_leaks")
    if large_nonruntime_files:
        status = "fail"
        failures.append("large_nonruntime_files")

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": status,
        "package_root": ".",
        "missing_required_files": missing,
        "forbidden_dirs": forbidden_dirs,
        "local_path_leaks": local_path_leaks,
        "large_nonruntime_files": large_nonruntime_files,
        "pycache_dirs_warning": pycache_dirs,
        "required_share_input_count": len(REQUIRED_SHARE_INPUTS),
        "required_runtime_sentinel_count": len(REQUIRED_RUNTIME_SENTINELS),
        "note_ko": (
            "전달 package에 필수 실행 파일, 대시보드 문서, frozen share 입력, "
            "Windows runtime sentinel 파일이 있는지와 raw/out/data/tmp/local path 흔적이 "
            "섞이지 않았는지 확인한다."
        ),
    }

    json_out = args.json_out or (package_root / "delivery_package_check_v1.json")
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if status != "pass":
        raise SystemExit(f"delivery package verification failed: {failures}; report={json_out}")
    print(f"[OK] delivery package verified: {json_out}")


if __name__ == "__main__":
    main()
