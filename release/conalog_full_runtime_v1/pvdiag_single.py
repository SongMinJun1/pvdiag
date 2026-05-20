#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path


GENERATED_BY = "tools/build_pvdiag_single_py.py"
GENERATED_AT_UTC = '2026-05-20T11:12:15.575055+00:00'
PAYLOAD_MODE = "source_text"
PAYLOAD_TEXT_SHA256 = '8a8445e538962b8aa3dfa07f3e54562f6a2cac811c78770279041b5a8420b8ac'
PAYLOAD_TEXT_BYTES = 753998
PAYLOAD_FILE_COUNT = 52
PAYLOAD_STRUCTURE_NOTE = (
    "This generated file embeds the modular pvdiag runtime as source-text payload. "
    "Use --single-list-payload to inspect module roles or --single-extract-source DIR "
    "to unpack readable sources."
)

PAYLOAD_FILE_INDEX = [
    {
        "path": "release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py",
        "role": "entry_runner",
        "bytes": 165072,
        "lines": 3508,
        "sha256": "b93a7de63810f7eb99bd2b6cca58c859bb1010f68c3fc4953eae11972942d9f4"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/pv_ae/panel_day_engine.py",
        "role": "core_engine",
        "bytes": 136553,
        "lines": 3277,
        "sha256": "30a20253b897d94d81e1675173334152543d09be7ba49fbef06cbb8552845a80"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/research/__init__.py",
        "role": "package_marker",
        "bytes": 0,
        "lines": 0,
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/research/prognostics/__init__.py",
        "role": "package_marker",
        "bytes": 0,
        "lines": 0,
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_bootstrap_verdict_v1.py",
        "role": "live_bootstrap_builder",
        "bytes": 8771,
        "lines": 201,
        "sha256": "d282379e50de994a571fdd47d929796cb55e88f709974f0b019bd93bb10e707e"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_cause_candidate_heuristics_v1.py",
        "role": "live_heuristic_builder",
        "bytes": 21623,
        "lines": 564,
        "sha256": "86de483fc576f7d10424f0dcac6f5fce24eb864a4ec765833e728119c88035d7"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_fault_panel_event_audit_v1.py",
        "role": "live_audit_builder",
        "bytes": 24531,
        "lines": 559,
        "sha256": "2573004b9450e21faaf944ad5e11d24ccdc66a82d03b04496a6a58778f5d838e"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_gpvs_evidence_pack_v1.py",
        "role": "live_gpvs_builder",
        "bytes": 31022,
        "lines": 714,
        "sha256": "2864b9dc1b6151b88f3205564e9b758192484d727a06550694a925ce140a1972"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_panel_multiaxis_verdict_v1.py",
        "role": "live_verdict_builder",
        "bytes": 119192,
        "lines": 2268,
        "sha256": "47d9a00a9cfdbe1b471eb93d4c0c8674de0116fca112fff5d9366a03efd6f1e7"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py",
        "role": "raw_only_audit_builder",
        "bytes": 11148,
        "lines": 237,
        "sha256": "9db0559f8232ade4a74ac673da7d189ae64e64d472376beace717ba1487a17de"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_final_verdict_v1.py",
        "role": "raw_only_verdict_builder",
        "bytes": 8601,
        "lines": 191,
        "sha256": "d23f1a31463f8367d09d23d1c6973d67448b966e89a30f3785e7403ed7dcaccb"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_heuristic_v1.py",
        "role": "raw_only_heuristic_builder",
        "bytes": 10250,
        "lines": 286,
        "sha256": "7d34a45aa9eb216a0f6e24516f83c8d4a5c225f9eddfe774ee4d991678df8103"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/research/prognostics/heuristic_display_registry_v1.py",
        "role": "display_label_registry",
        "bytes": 3223,
        "lines": 67,
        "sha256": "5ce767d422b02db6781954e05ced907c802f53df661c7f30d0b15a357ebe19ba"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/research/prognostics/runtime_rawonly_chain_common_v1.py",
        "role": "raw_only_shared_utils",
        "bytes": 46428,
        "lines": 1109,
        "sha256": "d3fbf8fcf2a6d3b1a5f0674f3406c09f607b48a01d3bbb5aca73fad62f4f1ae1"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/artifacts/fault6_fixed_result_provenance_v1.json",
        "role": "runtime_reference_artifact",
        "bytes": 1293,
        "lines": 21,
        "sha256": "174cf698b8c9ad7df916b4c3bfb6bd2b590611556def18e05a990bd5626b6d15"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/artifacts/fault6_fixed_result_table_v1.csv",
        "role": "runtime_reference_artifact",
        "bytes": 1341,
        "lines": 7,
        "sha256": "93eb336dfdbba36159e802726e9e94d98f782b74ef2e62b5cea46f4a22f93581"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/artifacts/fault6_label_and_algorithm_preview_v1.csv",
        "role": "runtime_reference_artifact",
        "bytes": 1125,
        "lines": 7,
        "sha256": "58e321a5bfcd7bf62e398aecde38701a533c5a64cbef2d18935b57bc4a39e20a"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/artifacts/input_baseline_manifest_v1.json",
        "role": "runtime_reference_artifact",
        "bytes": 2236,
        "lines": 65,
        "sha256": "8f6e69e526de55fb976e0fd9ecb5c1304816c3d3d48a7f8ef758989d6914ee2c"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/artifacts/ktc_fault2_label_and_algorithm_preview_v1.csv",
        "role": "runtime_reference_artifact",
        "bytes": 468,
        "lines": 3,
        "sha256": "c2bc0f2619ae9f58d57ae2142d7f040ffa5594c0f23e2623dfb0c4bc3c03d3af"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/artifacts/panel_day_core_baseline_digest_v1.json",
        "role": "runtime_reference_artifact",
        "bytes": 2864,
        "lines": 99,
        "sha256": "6b45552c16ce97b5ace20435e5dc811ed47074be5fd27111010cc915e7b3dcdf"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/artifacts/runtime_chain_dependency_audit_v1.json",
        "role": "runtime_reference_artifact",
        "bytes": 4238,
        "lines": 84,
        "sha256": "00766bb59ecaacf8c087b44a02fe33d40fb6c7cdd068e0a91ec53fa858aa2c9d"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/artifacts/runtime_chain_dependency_audit_v1.md",
        "role": "runtime_reference_artifact",
        "bytes": 3941,
        "lines": 85,
        "sha256": "8ee23ae291b499ffc4821d00a82cccceeae92b6d944da90bc3f0b010445008e0"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_date_reaudit_working.csv",
        "role": "frozen_share_input",
        "bytes": 33763,
        "lines": 115,
        "sha256": "5013dcf4281e1656452e3850735f03111aaeba1455766244c2532af2cc14ef9d"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_abrupt6_symptom_map_v1.csv",
        "role": "frozen_share_input",
        "bytes": 6743,
        "lines": 7,
        "sha256": "adc23e272b3b0507a3fc9eed41128d794605cd3faca396a2f703341c3eca2919"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_c42997_1_1_forensic_summary_v1.csv",
        "role": "frozen_share_input",
        "bytes": 2620,
        "lines": 2,
        "sha256": "6bc8496d57b2cc9717db1e2475c0a2c4d13558ecc94d093fc798c81f7f7dc4bb"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv",
        "role": "frozen_share_input",
        "bytes": 3153,
        "lines": 13,
        "sha256": "95faf00e62c5c997d8747f8534bf7c70277e0242aea8274ec0621faa3bd9ad83"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_detailed_fault_bridge_audit_v1.csv",
        "role": "frozen_share_input",
        "bytes": 684,
        "lines": 7,
        "sha256": "b486d90fb12f9ab7d2946e3d8ed7d7f6a841e145345c3d5b25e1bb123093a5b7"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_detailed_fault_bridge_summary_v1.csv",
        "role": "frozen_share_input",
        "bytes": 381,
        "lines": 2,
        "sha256": "74e5f22468c8c8675ed34c2bc86fa225f1a5b92d7efeeb3d0b62eb87a36b08d5"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_fault_panel_event_audit_v1.csv",
        "role": "frozen_share_input",
        "bytes": 4372,
        "lines": 7,
        "sha256": "103ce7549fb21433d14fe5cd0a949d2007ff3ffe16afb3ab28f28b82d8b0d047"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpv7_perf_summary_v1.csv",
        "role": "frozen_share_input",
        "bytes": 2365,
        "lines": 8,
        "sha256": "dc38bb9eb2d942db91b2924a9db7d170030eabc77699aec7731e112c1b93f49e"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv",
        "role": "frozen_share_input",
        "bytes": 583,
        "lines": 2,
        "sha256": "fc0483c0b5584bb3adf831053d4a85fab3a31e62a9868fdf177b0a2e9ad5eaec"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpvs_canonical_dictionary_v1.csv",
        "role": "frozen_share_input",
        "bytes": 1898,
        "lines": 9,
        "sha256": "a5d33bc1d714e2c4cc2f4b6d580174927ec47f1afa2f0d090765fa9d9c434e58"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv",
        "role": "frozen_share_input",
        "bytes": 1774,
        "lines": 7,
        "sha256": "59ba93a644e339a71ef8ea32e7511a116e4b8204cbf292864a986af5ed8e9371"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpvs_detailed_type_realpanel_sanity_v1.csv",
        "role": "frozen_share_input",
        "bytes": 1856,
        "lines": 7,
        "sha256": "bb14a77c79870e6a497b5780540c3e393f1347574e18b9fd0fce94ee09ad21d8"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpvs_evidence_pack_v1.csv",
        "role": "frozen_share_input",
        "bytes": 10516,
        "lines": 7,
        "sha256": "cf0bef62109dde191db4fff981367303dcf3daa4b73afdec2b5a5f336d07bac7"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv",
        "role": "frozen_share_input",
        "bytes": 743,
        "lines": 2,
        "sha256": "70940e6858166bd8a4d9f0f3741e44bed753c0c073f5ca8093b9383647261b1e"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpvs_mlpe_fault_matching_summary_v1.csv",
        "role": "frozen_share_input",
        "bytes": 406,
        "lines": 2,
        "sha256": "59615635e7a22218026a3785fbc841e157763835f182f86ba0c6ec3ea1f83e15"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpvs_mlpe_fault_matching_table_v1.csv",
        "role": "frozen_share_input",
        "bytes": 2369,
        "lines": 10,
        "sha256": "793daf84cd5926d5c2cc13553e4cf1393948ac74382717ef9d6ace530831f345"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpvs_mlpe_panel_agreement_v1.csv",
        "role": "frozen_share_input",
        "bytes": 2281,
        "lines": 7,
        "sha256": "3772deb00b45f2eedae04aee1ac097719d37a17a93ef8380a432267af5f02279"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpvs_panel_attach_candidates_v1.csv",
        "role": "frozen_share_input",
        "bytes": 3405,
        "lines": 13,
        "sha256": "164a017a461a9d422da72f22e2eca4074a40f0b8f41b14053fea2747ef9abd25"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpvs_panel_attach_feasibility_v1.csv",
        "role": "frozen_share_input",
        "bytes": 701,
        "lines": 2,
        "sha256": "5ae50335455718a82408f37fb0577d34e65f258353305dcc895403fc0bf60213"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpvs_panel_attach_inventory_v1.csv",
        "role": "frozen_share_input",
        "bytes": 11433,
        "lines": 53,
        "sha256": "f36125c3b98480f23c029f2a6f1ff8432b653b3209191ac7137db4433fb14f49"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_kernellog_project_mapping_v1.csv",
        "role": "frozen_share_input",
        "bytes": 1622,
        "lines": 6,
        "sha256": "04d816865eef263b2691a7e5d3726a811764cbdde0aaac548e1c31d84fc0c4b5"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_non_precursor_performance_cases_v1.csv",
        "role": "frozen_share_input",
        "bytes": 3673,
        "lines": 8,
        "sha256": "bc7396d7fac075691477edb5e2a6934dd35f5c006749ad86fa7bb142b8fbf588"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_operator_workflow_default_v1.csv",
        "role": "frozen_share_input",
        "bytes": 7704,
        "lines": 24,
        "sha256": "b535662d24c124d6833bb6517625a763e2b682c1f79506ab021aaa8869a4724f"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_panel_multiaxis_verdict_v1.csv",
        "role": "frozen_share_input",
        "bytes": 22626,
        "lines": 26,
        "sha256": "a043a9cf85bd2aaf02efc36cc8fe13dc1edeac060aaf5e938ed3352539f8d3b1"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_precursor_abrupt_consistency_cases_v1.csv",
        "role": "frozen_share_input",
        "bytes": 1366,
        "lines": 3,
        "sha256": "693771f5963bbafbc062bfaa3f34c75c6dabbe0293a9b64a669c6101bf9b4bc3"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_precursor_abrupt_consistency_recommendation_v1.csv",
        "role": "frozen_share_input",
        "bytes": 239,
        "lines": 2,
        "sha256": "a5f5d4279472b9cf169dcd1d7943dcba71322b0ecf1f299abd88a9c7e1ee621d"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_precursor_abrupt_consistency_summary_v1.csv",
        "role": "frozen_share_input",
        "bytes": 522,
        "lines": 2,
        "sha256": "7948911e08de78b1978b982e6ed2865ebcd639fd8223df0e7b70b233c78564a5"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_precursor_onset_truth_v1.csv",
        "role": "frozen_share_input",
        "bytes": 2060,
        "lines": 4,
        "sha256": "5d19ea4cc44382378a8c57ddd5311215e33a94c17e3500fa8994d3f3f850bc0c"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_project_final_decision_pack_v1.csv",
        "role": "frozen_share_input",
        "bytes": 7454,
        "lines": 7,
        "sha256": "462144cf3895c12c67a95daf59fb82001148945c59da6ab99423514c13ec83b3"
    },
    {
        "path": "release/conalog_full_runtime_v1/package/_share/vendor_reply_adjudication_latest.csv",
        "role": "frozen_share_input",
        "bytes": 5683,
        "lines": 15,
        "sha256": "b61270a7536486a669592824c7d7737a73e65bd6fc7828f413bab062b5c1635c"
    }
]

EMBEDDED_TEXT_FILES: dict[str, str] = {}
EMBEDDED_FILE_SHA256: dict[str, str] = {}

REQUIRED_MODULES = {
    "pandas": "pandas",
    "numpy": "numpy",
    "torch": "torch",
    "openpyxl": "openpyxl",
    "tqdm": "tqdm",
}
RECOMMENDED_PACKAGE_VERSIONS = {
    "pandas": "2.3.3",
    "numpy": "2.3.4",
    "torch": "2.9.1",
    "openpyxl": "3.1.5",
    "tqdm": "4.67.1",
}
MIN_PYTHON_VERSION = (3, 10)


def script_dir() -> Path:
    try:
        return Path(__file__).resolve().parent
    except NameError:
        return Path.cwd()


def parse_args(argv: list[str] | None = None) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description=(
            "Run the PV panel fault/precursor diagnosis algorithm from one generated Python file. "
            "External packages and input CSV data are expected separately."
        )
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=None,
        help="Input data root. If omitted, ./data next to this file is used when present.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="Output root. If omitted, pvdiag_results/run_YYYYMMDD_HHMMSS is created next to this file.",
    )
    parser.add_argument("--single-self-test", action="store_true", help="Extract payload and verify the embedded runner without running the algorithm.")
    parser.add_argument("--single-list-payload", action="store_true", help="Print the embedded module/artifact structure and exit.")
    parser.add_argument("--single-extract-source", type=Path, default=None, help="Extract the embedded readable source tree to DIR and exit.")
    parser.add_argument("--single-keep-runtime", action="store_true", help="Keep the extracted temporary runtime folder for debugging.")
    return parser.parse_known_args(argv)


def missing_dependencies() -> list[str]:
    missing: list[str] = []
    for module_name, package_name in REQUIRED_MODULES.items():
        if importlib.util.find_spec(module_name) is None:
            missing.append(package_name)
    return missing


def package_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for module_name in REQUIRED_MODULES:
        if importlib.util.find_spec(module_name) is None:
            continue
        module = __import__(module_name)
        versions[module_name] = str(getattr(module, "__version__", "unknown"))
    return versions


def print_environment_summary() -> None:
    print(
        "[pvdiag_single] environment:",
        f"python={sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        f"executable={sys.executable}",
    )
    versions = package_versions()
    if versions:
        print("[pvdiag_single] installed package versions:")
        for module_name, version in versions.items():
            recommended = RECOMMENDED_PACKAGE_VERSIONS.get(module_name, "")
            suffix = f" (recommended {recommended})" if recommended and version != recommended else ""
            print(f"  - {module_name}=={version}{suffix}")


def python_version_supported() -> bool:
    return sys.version_info >= MIN_PYTHON_VERSION


def print_python_version_help() -> None:
    required = ".".join(str(part) for part in MIN_PYTHON_VERSION)
    current = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"[pvdiag_single] Python {required}+ is required. Current Python is {current}.")
    print("[pvdiag_single] recommended: Python 3.11 with pandas/numpy/torch/openpyxl/tqdm installed.")


def print_dependency_help(missing: list[str]) -> None:
    print("[pvdiag_single] missing required Python packages:")
    for package in missing:
        print(f"  - {package}")
    print("[pvdiag_single] install example:")
    print("  pip install pandas==2.3.3 numpy==2.3.4 torch==2.9.1 openpyxl==3.1.5 tqdm==4.67.1")
    print("[pvdiag_single] after installing packages, run the same command again.")


def print_data_root_help(output_root: Path) -> None:
    print("[pvdiag_single] how to provide input data:")
    print("  1. run with --data-root /path/to/data")
    print("  2. or place a data/ folder next to pvdiag_single.py")
    print("[pvdiag_single] output/log directory:")
    print(f"  {output_root}")


def resolve_data_root(value: Path | None, output_root: Path) -> Path | None:
    if value is not None:
        return value.expanduser().resolve()
    sibling_data = script_dir() / "data"
    if sibling_data.exists():
        return sibling_data.resolve()
    if not sys.stdin.isatty():
        print("[pvdiag_single] data-root was not provided and sibling data/ was not found.")
        print(f"[pvdiag_single] looked for: {sibling_data}")
        print_data_root_help(output_root)
        return None
    try:
        typed = input("[pvdiag_single] Input data-root folder path: ").strip()
    except EOFError:
        print("[pvdiag_single] data-root was not provided and interactive input is unavailable.")
        print(f"[pvdiag_single] looked for: {sibling_data}")
        print_data_root_help(output_root)
        return None
    if not typed:
        print("[pvdiag_single] data-root is required.")
        print_data_root_help(output_root)
        return None
    return Path(typed).expanduser().resolve()


def resolve_output_root(value: Path | None) -> Path:
    if value is not None:
        output_root = value.expanduser().resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_root = script_dir() / "pvdiag_results" / f"run_{stamp}"
    output_root.mkdir(parents=True, exist_ok=True)
    return output_root


def single_source_path() -> Path:
    try:
        return Path(__file__).resolve()
    except NameError:
        return Path(sys.argv[0]).resolve()


def load_embedded_payload_from_source() -> tuple[dict[str, str], dict[str, str]]:
    source = single_source_path()
    try:
        source_lines = source.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise SystemExit(f"could not read generated single-file source: {source}") from exc

    start_prefix = "# pvdiag_payload_file "
    line_prefix = "#|"
    payload: dict[str, str] = {}
    hashes: dict[str, str] = {}
    current_meta: dict[str, object] | None = None
    current_lines: list[str] = []

    for line_no, line in enumerate(source_lines, start=1):
        if line.startswith(start_prefix):
            if current_meta is not None:
                raise SystemExit(f"nested embedded payload block at line {line_no}")
            try:
                current_meta = json.loads(line[len(start_prefix):])
            except json.JSONDecodeError as exc:
                raise SystemExit(f"invalid embedded payload metadata at line {line_no}") from exc
            current_lines = []
            continue
        if line == "# pvdiag_payload_end":
            if current_meta is None:
                raise SystemExit(f"embedded payload end without start at line {line_no}")
            path = str(current_meta.get("path", ""))
            if not path:
                raise SystemExit(f"embedded payload metadata missing path before line {line_no}")
            text = "\n".join(current_lines)
            if bool(current_meta.get("endswith_newline", False)):
                text += "\n"
            payload[path] = text
            hashes[path] = str(current_meta.get("sha256", ""))
            current_meta = None
            current_lines = []
            continue
        if current_meta is not None:
            if not line.startswith(line_prefix):
                raise SystemExit(f"embedded payload source line missing '#|' prefix at line {line_no}")
            current_lines.append(line[len(line_prefix):])

    if current_meta is not None:
        raise SystemExit("unterminated embedded payload block")
    if not payload:
        raise SystemExit("generated single-file source does not contain readable embedded payload blocks")
    return payload, hashes


def embedded_payload_bytes() -> bytes:
    return b"".join(
        path.encode("utf-8") + b"\0" + text.encode("utf-8") + b"\0"
        for path, text in sorted(EMBEDDED_TEXT_FILES.items())
    )


def verify_embedded_payload() -> None:
    if len(EMBEDDED_TEXT_FILES) != PAYLOAD_FILE_COUNT:
        raise SystemExit(
            f"embedded payload file-count mismatch: expected {PAYLOAD_FILE_COUNT}, got {len(EMBEDDED_TEXT_FILES)}"
        )
    payload_data = embedded_payload_bytes()
    if len(payload_data) != PAYLOAD_TEXT_BYTES:
        raise SystemExit(
            f"embedded payload byte mismatch: expected {PAYLOAD_TEXT_BYTES}, got {len(payload_data)}"
        )
    digest = hashlib.sha256(payload_data).hexdigest()
    if digest != PAYLOAD_TEXT_SHA256:
        raise SystemExit(f"embedded payload sha256 mismatch: expected {PAYLOAD_TEXT_SHA256}, got {digest}")
    for path, text in EMBEDDED_TEXT_FILES.items():
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        expected = EMBEDDED_FILE_SHA256.get(path)
        if expected != digest:
            raise SystemExit(f"embedded file sha256 mismatch: {path}")


def safe_target(runtime_root: Path, embedded_path: str) -> Path:
    target = (runtime_root / embedded_path).resolve()
    runtime_root_resolved = runtime_root.resolve()
    if target != runtime_root_resolved and not str(target).startswith(str(runtime_root_resolved) + os.sep):
        raise SystemExit(f"unsafe embedded path: {embedded_path}")
    return target


def extract_embedded_files(runtime_root: Path) -> None:
    verify_embedded_payload()
    runtime_root.mkdir(parents=True, exist_ok=True)
    for embedded_path, text in EMBEDDED_TEXT_FILES.items():
        target = safe_target(runtime_root, embedded_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")


def print_payload_index() -> None:
    verify_embedded_payload()
    print("[pvdiag_single] payload structure")
    print(f"[pvdiag_single] note: {PAYLOAD_STRUCTURE_NOTE}")
    print(f"[pvdiag_single] files: {PAYLOAD_FILE_COUNT}, bytes: {PAYLOAD_TEXT_BYTES}")
    for row in PAYLOAD_FILE_INDEX:
        print(
            "[pvdiag_single] "
            f"{row['role']:<34} "
            f"{row['bytes']:>8} bytes "
            f"{row['sha256'][:12]} "
            f"{row['path']}"
        )
    print("[pvdiag_single] readable source extraction:")
    print("  python pvdiag_single.py --single-extract-source /tmp/pvdiag_single_source")


def extract_source_tree(destination: Path) -> None:
    target_root = destination.expanduser().resolve()
    if target_root.exists() and not target_root.is_dir():
        raise SystemExit(f"source extraction target is not a directory: {target_root}")
    extract_embedded_files(target_root)
    runner = target_root / "release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py"
    engine = target_root / "release/conalog_full_runtime_v1/package/pv_ae/panel_day_engine.py"
    print("[pvdiag_single] source extraction ok")
    print(f"[pvdiag_single] extracted files: {PAYLOAD_FILE_COUNT}")
    print(f"[pvdiag_single] source root: {target_root}")
    print(f"[pvdiag_single] runner: {runner}")
    print(f"[pvdiag_single] core engine: {engine}")


def inner_runner(runtime_root: Path) -> Path:
    path = runtime_root / "release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py"
    if not path.exists():
        raise SystemExit(f"embedded runner not found after extraction: {path}")
    return path


def run_command(cmd: list[str], output_root: Path) -> int:
    log_path = output_root / "pvdiag_single_run.log"
    print("[pvdiag_single] command:", flush=True)
    print(" ".join(str(part) for part in cmd), flush=True)
    print(f"[pvdiag_single] log: {log_path}", flush=True)
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.Popen(
            cmd,
            cwd=Path.cwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end="", flush=True)
            log.write(line)
        return proc.wait()


def main(argv: list[str] | None = None) -> int:
    args, passthrough = parse_args(argv)
    if args.single_list_payload:
        print_payload_index()
        return 0
    if args.single_extract_source is not None:
        extract_source_tree(args.single_extract_source)
        return 0

    cleanup_runtime = not args.single_keep_runtime
    temp_obj = None
    if cleanup_runtime:
        temp_obj = tempfile.TemporaryDirectory(prefix="pvdiag_single_runtime_")
        runtime_root = Path(temp_obj.name)
    else:
        runtime_root = Path(tempfile.mkdtemp(prefix="pvdiag_single_runtime_keep_"))

    try:
        extract_embedded_files(runtime_root)
        runner = inner_runner(runtime_root)
        if args.single_self_test:
            print("[pvdiag_single] self-test ok")
            print(f"[pvdiag_single] generated_at_utc: {GENERATED_AT_UTC}")
            print(f"[pvdiag_single] payload_mode: {PAYLOAD_MODE}")
            print(f"[pvdiag_single] payload_files: {PAYLOAD_FILE_COUNT}")
            print(f"[pvdiag_single] payload_text_bytes: {PAYLOAD_TEXT_BYTES}")
            print(f"[pvdiag_single] payload_structure_note: {PAYLOAD_STRUCTURE_NOTE}")
            print(f"[pvdiag_single] runtime_root: {runtime_root}")
            print(f"[pvdiag_single] runner: {runner}")
            print_environment_summary()
            return 0

        if not python_version_supported():
            print_python_version_help()
            if args.single_keep_runtime:
                print(f"[pvdiag_single] kept runtime: {runtime_root}")
            return 2

        missing = missing_dependencies()
        if missing:
            print_dependency_help(missing)
            if args.single_keep_runtime:
                print(f"[pvdiag_single] kept runtime: {runtime_root}")
            return 2

        output_root = resolve_output_root(args.output_root)
        data_root = resolve_data_root(args.data_root, output_root)
        if data_root is None:
            if args.single_keep_runtime:
                print(f"[pvdiag_single] kept runtime: {runtime_root}")
            return 3
        if not data_root.exists():
            print(f"[pvdiag_single] data-root does not exist: {data_root}")
            print_data_root_help(output_root)
            if args.single_keep_runtime:
                print(f"[pvdiag_single] kept runtime: {runtime_root}")
            return 3

        cmd = [
            sys.executable,
            str(runner),
            "--data-root",
            str(data_root),
            "--output-root",
            str(output_root),
            *passthrough,
        ]

        code = run_command(cmd, output_root)
        if code != 0:
            print(f"[pvdiag_single] failed with exit code {code}")
            print(f"[pvdiag_single] log: {output_root / 'pvdiag_single_run.log'}")
            if args.single_keep_runtime:
                print(f"[pvdiag_single] kept runtime: {runtime_root}")
            return code

        print("[pvdiag_single] completed successfully")
        print(f"[pvdiag_single] result root: {output_root}")
        print(f"[pvdiag_single] master report: {output_root / 'result' / 'fault_panel_result_master_report_v1.md'}")
        print(f"[pvdiag_single] detailed xlsx: {output_root / 'result' / 'fault_panel_result_detailed_report_v1.xlsx'}")
        return 0
    finally:
        if temp_obj is not None:
            temp_obj.cleanup()
        elif cleanup_runtime and runtime_root.exists():
            shutil.rmtree(runtime_root, ignore_errors=True)


# region Embedded readable source payload (auto-generated; collapse this block in VS Code)
# The lines below are original payload files, stored as readable comments.
# Each '#|' line becomes one source line when pvdiag_single.py restores the runtime.
# Use --single-list-payload to inspect roles or --single-extract-source DIR to unpack normal files.
# -----------------------------------------------------------------------------
# region payload: entry_runner
# pvdiag_payload_file {"bytes": 165072, "endswith_newline": true, "lines": 3508, "path": "release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py", "role": "entry_runner", "sha256": "b93a7de63810f7eb99bd2b6cca58c859bb1010f68c3fc4953eae11972942d9f4"}
#|#!/usr/bin/env python3
#|from __future__ import annotations
#|
#|import argparse
#|import hashlib
#|import json
#|import re
#|import shutil
#|import subprocess
#|import sys
#|from datetime import datetime, timezone
#|from pathlib import Path
#|
#|import pandas as pd
#|
#|PACKAGE_ROOT = Path(__file__).resolve().parents[1]
#|if str(PACKAGE_ROOT) not in sys.path:
#|    sys.path.insert(0, str(PACKAGE_ROOT))
#|from research.prognostics.heuristic_display_registry_v1 import (
#|    DISPLAY_HEURISTIC_NAME_MAP,
#|    HEURISTIC_DISPLAY_NOTE_MAP,
#|    display_heuristic_name as shared_display_heuristic_name,
#|    display_heuristic_note as shared_display_heuristic_note,
#|)
#|
#|DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
#|DEFAULT_SITES = ["conalog", "gangui", "ktc_ess"]
#|CORE_DIGEST_COLUMNS = [
#|    "date",
#|    "panel_id",
#|    "confirmed_fault",
#|    "critical_fault",
#|    "critical_source",
#|    "final_fault",
#|    "anom_level",
#|    "anom_subtype",
#|]
#|LIVE_FAULT_COMPARE_COLS = [
#|    "site",
#|    "panel_id",
#|    "패널고장여부_ko",
#|    "사건유형_ko",
#|    "최종고장양상_ko",
#|    "커널로그_원인군_ko",
#|    "1순위_의심원인_ko",
#|    "2순위_의심원인_ko",
#|    "3순위_의심원인_ko",
#|]
#|LIVE_FAULT_OUTPUT_COLS = [
#|    *LIVE_FAULT_COMPARE_COLS,
#|    "전조날짜",
#|    "고장날짜",
#|]
#|LIVE_PREVIEW_OUTPUT_COLS = [
#|    "site",
#|    "panel_id",
#|    "패널고장여부_ko",
#|    "사건유형_ko",
#|    "최종고장양상_ko",
#|    "전조날짜",
#|    "고장날짜",
#|    "라벨된 fault",
#|    "1순위_의심원인_ko",
#|    "2순위_의심원인_ko",
#|    "3순위_의심원인_ko",
#|    "커널로그 기존 알고리즘",
#|]
#|USER_PREVIEW_OUTPUT_COLS = [
#|    "site",
#|    "panel_id",
#|    "전조날짜",
#|    "고장 기준일",
#|    "운영 판정",
#|    "급락 종결 관측",
#|    "점진 저하 누적",
#|    "사건 종결 요약",
#|    "상위 해석 후보",
#|    "기존 알고리즘 source",
#|]
#|SIGNAL_PREVIEW_OUTPUT_COLS = [
#|    "site",
#|    "panel_id",
#|    "전조날짜",
#|    "신호 기준일",
#|    "운영 판정",
#|    "급락 종결 관측",
#|    "점진 저하 누적",
#|    "사건 종결 요약",
#|    "상위 해석 후보",
#|    "기존 알고리즘 source",
#|]
#|PRECURSOR_REPORT_OUTPUT_COLS = [
#|    "site",
#|    "panel_id",
#|    "운영 판정",
#|    "판정 근거",
#|    "전조날짜",
#|    "전조 축",
#|    "대표 전조 신호",
#|    "전조 요약",
#|    "상위 해석 후보",
#|    "기존 알고리즘 source",
#|    "패턴 설명",
#|    "모니터링 권고",
#|    "공통원인 위험",
#|    "권고 검토 레인",
#|    "EWS 전조 일수",
#|    "pre_alarm 일수",
#|    "pre_ews 일수",
#|    "Option B 유효 일수",
#|    "공통원인 겹침 일수",
#|    "AE 전조 조건 일수",
#|    "DTW 전조 조건 일수",
#|]
#|FAULT_SIGNAL_REPORT_OUTPUT_COLS = [
#|    "site",
#|    "group root",
#|    "subgroup base",
#|    "subgroup cluster",
#|    "panel_id",
#|    "동일 subgroup row 수",
#|    "동일 cluster row 수",
#|    "운영 판정",
#|    "확정 경로",
#|    "고장 신호 요약",
#|    "전조 시작일",
#|    "신호 기준일",
#|    "사건유형",
#|    "사건 종결 요약",
#|    "근접 공통원인",
#|    "상위 해석 후보",
#|    "기존 알고리즘 source",
#|    "패턴 설명",
#|    "현장 점검 권고",
#|]
#|ROOT_LIVE_FAULT_NAME = "fault_panel_result_current_v1.csv"
#|ROOT_LIVE_PREVIEW_NAME = "fault_panel_result_current_preview_v1.csv"
#|ROOT_LIVE_SUMMARY_NAME = "live_chain_summary_v1.json"
#|ROOT_LIVE_REPORT_NAME = "fault_panel_result_current_report_v1.md"
#|ROOT_RAWONLY_FAULT_NAME = "fault_panel_result_raw_only_current_v1.csv"
#|ROOT_RAWONLY_PREVIEW_NAME = "fault_panel_result_raw_only_current_preview_v1.csv"
#|ROOT_RAWONLY_SUMMARY_NAME = "raw_only_chain_summary_v1.json"
#|ROOT_RAWONLY_REPORT_NAME = "fault_panel_result_raw_only_current_report_v1.md"
#|ROOT_MASTER_REPORT_NAME = "fault_panel_result_master_report_v1.md"
#|ROOT_DETAILED_REPORT_NAME = "fault_panel_result_detailed_report_v1.xlsx"
#|ROOT_PRECURSOR_REPORT_NAME = "fault_panel_result_precursor_report_v1.csv"
#|ROOT_FAULT_SIGNAL_REPORT_NAME = "fault_panel_result_raw_only_fault_signal_report_v1.csv"
#|RAW_ONLY_STRICT_CURRENT_GRADES = {"확정"}
#|FAULT_SIGNAL_CLUSTER_GAP_DAYS = 3
#|MAIL_BUCKET_ALGORITHM_MAP = {
#|    ("conalog", "7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0"): "panel-bypass",
#|    ("conalog", "c42997a6-5881-47e7-9035-7de8a2673b54.1.1"): "disconnection",
#|    ("gangui", "bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7"): "panel-bypass",
#|    ("gangui", "bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16"): "panel-bypass",
#|    ("ktc_ess", "10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12"): "panel-bypass",
#|    ("ktc_ess", "70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4"): "panel-bypass",
#|}
#|
#|
#|def parse_args() -> argparse.Namespace:
#|    parser = argparse.ArgumentParser(
#|        description=(
#|            "Run the real panel_day_engine.py for the packaged baseline sites under a data root, "
#|            "export the fixed fault result artifacts, and write a shadow-compare report for engine core outputs."
#|        )
#|    )
#|    parser.add_argument(
#|        "--data-root",
#|        type=Path,
#|        required=True,
#|        help="Folder containing site/raw subdirectories such as data-root/conalog/raw.",
#|    )
#|    parser.add_argument(
#|        "--output-root",
#|        type=Path,
#|        required=True,
#|        help="Folder where site-wise engine outputs and fixed result tables will be written.",
#|    )
#|    parser.add_argument(
#|        "--sites",
#|        default=",".join(DEFAULT_SITES),
#|        help="Comma-separated site list. Defaults to conalog,gangui,ktc_ess.",
#|    )
#|    parser.add_argument(
#|        "--train-days",
#|        type=int,
#|        default=60,
#|        help="Maximum number of early days to reserve for training window proposal.",
#|    )
#|    parser.add_argument("--pattern", default="*.csv", help="Filename pattern for raw daily CSVs.")
#|    parser.add_argument("--epochs", type=int, default=40, help="Engine epochs. Defaults to panel_day_engine.py default.")
#|    parser.add_argument("--latent", type=int, default=16, help="Engine latent size. Defaults to panel_day_engine.py default.")
#|    parser.add_argument("--device", default="cpu", help="Torch device to pass through to panel_day_engine.py.")
#|    parser.add_argument(
#|        "--prefer-existing-site-outs",
#|        choices=["auto", "on", "off"],
#|        default="auto",
#|        help=(
#|            "Whether to automatically reuse data-root/<site>/out when available. "
#|            "Defaults to auto."
#|        ),
#|    )
#|    parser.add_argument(
#|        "--reuse-existing-site-outs-root",
#|        type=Path,
#|        default=None,
#|        help=(
#|            "Optional root containing precomputed data/<site>/out trees. "
#|            "When provided, the runner copies those outputs into the runtime workspace and skips engine execution."
#|        ),
#|    )
#|    parser.add_argument(
#|        "--run-live-chain",
#|        choices=["on", "off"],
#|        default="on",
#|        help="After engine execution, run the packaged bootstrap verdict -> audit -> final verdict live chain. Defaults to on.",
#|    )
#|    parser.add_argument(
#|        "--run-raw-only-chain",
#|        choices=["on", "off"],
#|        default="on",
#|        help="After engine execution, run the packaged raw-only audit -> verdict -> heuristic chain. Defaults to on.",
#|    )
#|    parser.add_argument("--dry-run", action="store_true", help="Validate paths and emit the execution plan without running the engine.")
#|    return parser.parse_args()
#|
#|
#|def package_root() -> Path:
#|    return Path(__file__).resolve().parents[1]
#|
#|
#|def engine_path() -> Path:
#|    return package_root() / "pv_ae" / "panel_day_engine.py"
#|
#|
#|def fixed_fault6_table_path() -> Path:
#|    return package_root() / "artifacts" / "fault6_fixed_result_table_v1.csv"
#|
#|
#|def fixed_fault6_preview_path() -> Path:
#|    return package_root() / "artifacts" / "fault6_label_and_algorithm_preview_v1.csv"
#|
#|
#|def baseline_manifest_path() -> Path:
#|    return package_root() / "artifacts" / "input_baseline_manifest_v1.json"
#|
#|
#|def baseline_core_digest_path() -> Path:
#|    return package_root() / "artifacts" / "panel_day_core_baseline_digest_v1.json"
#|
#|
#|def fault6_provenance_path() -> Path:
#|    return package_root() / "artifacts" / "fault6_fixed_result_provenance_v1.json"
#|
#|
#|def dependency_audit_json_path() -> Path:
#|    return package_root() / "artifacts" / "runtime_chain_dependency_audit_v1.json"
#|
#|
#|def dependency_audit_md_path() -> Path:
#|    return package_root() / "artifacts" / "runtime_chain_dependency_audit_v1.md"
#|
#|
#|def packaged_share_root() -> Path:
#|    return package_root() / "_share"
#|
#|
#|def packaged_pipeline_root() -> Path:
#|    return package_root() / "research" / "prognostics"
#|
#|
#|def packaged_script_path(name: str) -> Path:
#|    return packaged_pipeline_root() / name
#|
#|
#|def extract_date_from_name(path: Path) -> pd.Timestamp:
#|    match = DATE_RE.search(path.name)
#|    if not match:
#|        return pd.NaT
#|    return pd.to_datetime(match.group(1), errors="coerce").normalize()
#|
#|
#|def normalize_sites(raw_sites: str) -> list[str]:
#|    sites = [token.strip() for token in str(raw_sites).split(",") if token.strip()]
#|    if not sites:
#|        raise SystemExit("at least one site must be provided")
#|    return sites
#|
#|
#|def scan_site_files(data_root: Path, site: str, pattern: str) -> tuple[pd.Timestamp, pd.Timestamp, list[Path]]:
#|    raw_dir = data_root / site / "raw"
#|    if not raw_dir.exists():
#|        raise SystemExit(f"missing raw dir for site={site}: {raw_dir}")
#|    files = sorted(path for path in raw_dir.glob(pattern) if path.is_file() and path.suffix.lower() == ".csv")
#|    if not files:
#|        raise SystemExit(f"raw csv not found for site={site}: {raw_dir}")
#|    valid_dates = [value for value in (extract_date_from_name(path) for path in files) if pd.notna(value)]
#|    if not valid_dates:
#|        raise SystemExit(f"no YYYY-MM-DD found in filenames for site={site}: {raw_dir}")
#|    return min(valid_dates), max(valid_dates), files
#|
#|
#|def propose_windows(min_date: pd.Timestamp, max_date: pd.Timestamp, train_days: int) -> dict[str, str]:
#|    span_days = int((max_date - min_date).days)
#|    proposed = min(int(train_days) - 1, max(14, int(span_days * 0.30)))
#|    if proposed < 1:
#|        proposed = 1
#|
#|    train_start = min_date
#|    train_end = min_date + pd.Timedelta(days=proposed)
#|    if train_end >= max_date:
#|        train_end = max_date - pd.Timedelta(days=1)
#|    if train_end < min_date:
#|        raise SystemExit("date span too short to propose train/eval windows")
#|
#|    eval_start = train_end + pd.Timedelta(days=1)
#|    eval_end = max_date
#|    if eval_start > eval_end:
#|        raise SystemExit("date span too short to propose eval window")
#|
#|    return {
#|        "train_start": str(train_start.date()),
#|        "train_end": str(train_end.date()),
#|        "eval_start": str(eval_start.date()),
#|        "eval_end": str(eval_end.date()),
#|        "input_date_min": str(min_date.date()),
#|        "input_date_max": str(max_date.date()),
#|    }
#|
#|
#|def site_manifest(files: list[Path]) -> dict[str, object]:
#|    date_tokens = [match.group(1) for path in files if (match := DATE_RE.search(path.name))]
#|    return {
#|        "file_count": int(len(files)),
#|        "total_bytes": int(sum(path.stat().st_size for path in files)),
#|        "first_filenames": [path.name for path in files[:5]],
#|        "last_filenames": [path.name for path in files[-5:]],
#|        "min_date": min(date_tokens) if date_tokens else "",
#|        "max_date": max(date_tokens) if date_tokens else "",
#|    }
#|
#|
#|def build_site_plan(args: argparse.Namespace, site: str) -> tuple[dict[str, object], list[str]]:
#|    data_root = args.data_root.expanduser().resolve()
#|    output_root = args.output_root.expanduser().resolve()
#|    site_output_dir = output_root / "sites" / site / "output"
#|    site_log_dir = output_root / "sites" / site / "log"
#|    site_output_dir.mkdir(parents=True, exist_ok=True)
#|    site_log_dir.mkdir(parents=True, exist_ok=True)
#|
#|    min_date, max_date, files = scan_site_files(data_root, site, args.pattern)
#|    windows = propose_windows(min_date, max_date, args.train_days)
#|    cmd = [
#|        sys.executable,
#|        str(engine_path()),
#|        "--site",
#|        site,
#|        "--data-root",
#|        str(data_root),
#|        "--out-dir",
#|        str(site_output_dir),
#|        "--log-dir",
#|        str(site_log_dir),
#|        "--pattern",
#|        args.pattern,
#|        "--train-start",
#|        windows["train_start"],
#|        "--train-end",
#|        windows["train_end"],
#|        "--eval-start",
#|        windows["eval_start"],
#|        "--eval-end",
#|        windows["eval_end"],
#|        "--epochs",
#|        str(args.epochs),
#|        "--latent",
#|        str(args.latent),
#|        "--device",
#|        args.device,
#|    ]
#|    plan = {
#|        "site": site,
#|        "raw_dir": str(data_root / site / "raw"),
#|        "output_dir": str(site_output_dir),
#|        "log_dir": str(site_log_dir),
#|        "windows": windows,
#|        "file_manifest": site_manifest(files),
#|        "command": cmd,
#|    }
#|    return plan, cmd
#|
#|
#|def write_json(path: Path, payload: dict[str, object]) -> None:
#|    path.parent.mkdir(parents=True, exist_ok=True)
#|    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
#|
#|
#|def write_text(path: Path, text: str) -> None:
#|    path.parent.mkdir(parents=True, exist_ok=True)
#|    path.write_text(text, encoding="utf-8")
#|
#|
#|def emit_progress(percent: int, message: str) -> None:
#|    safe_percent = max(0, min(100, int(percent)))
#|    print(f"[{safe_percent:03d}%] {message}", flush=True)
#|
#|
#|def load_baseline_manifest() -> dict[str, object]:
#|    path = baseline_manifest_path()
#|    if not path.exists():
#|        raise SystemExit(f"missing packaged baseline manifest: {path}")
#|    return json.loads(path.read_text(encoding="utf-8"))
#|
#|
#|def compare_to_baseline(site_plans: list[dict[str, object]]) -> dict[str, object]:
#|    baseline = load_baseline_manifest()
#|    comparison: dict[str, object] = {"all_sites_match": True, "sites": {}}
#|    baseline_sites = baseline.get("sites", {})
#|    for plan in site_plans:
#|        site = str(plan["site"])
#|        actual = plan["file_manifest"]
#|        expected = baseline_sites.get(site, {})
#|        site_match = True
#|        diffs: list[str] = []
#|        for key in ["file_count", "total_bytes", "min_date", "max_date"]:
#|            if actual.get(key) != expected.get(key):
#|                site_match = False
#|                diffs.append(f"{key}: expected={expected.get(key)} actual={actual.get(key)}")
#|        comparison["sites"][site] = {
#|            "match": site_match,
#|            "expected": expected,
#|            "actual": actual,
#|            "diffs": diffs,
#|        }
#|        if not site_match:
#|            comparison["all_sites_match"] = False
#|    comparison["note_ko"] = (
#|        "all_sites_match=1 이면 packaged fixed result table을 만든 baseline raw corpus와 현재 입력의 경량 fingerprint가 일치한다. "
#|        "일치하지 않으면 engine은 실행될 수 있어도 fixed result table exact replay 보장은 약해진다."
#|    )
#|    return comparison
#|
#|
#|def copy_fixed_results(output_root: Path) -> dict[str, str]:
#|    output_dir = output_root / "result"
#|    output_dir.mkdir(parents=True, exist_ok=True)
#|    fault6_dest = output_dir / "fault6_fixed_result_table_v1.csv"
#|    preview_dest = output_dir / "fault6_label_and_algorithm_preview_v1.csv"
#|    shutil.copy2(fixed_fault6_table_path(), fault6_dest)
#|    if fixed_fault6_preview_path().exists():
#|        preview_df = pd.read_csv(fixed_fault6_preview_path(), encoding="utf-8-sig", low_memory=False)
#|        to_user_preview_schema(preview_df).to_csv(preview_dest, index=False, encoding="utf-8-sig")
#|    return {
#|        "fault6_fixed_result_table_v1": str(fault6_dest),
#|        "fault6_label_and_algorithm_preview_v1": str(preview_dest),
#|    }
#|
#|
#|def copy_tree(source: Path, target: Path) -> None:
#|    if not source.exists():
#|        raise SystemExit(f"missing source tree: {source}")
#|    target.parent.mkdir(parents=True, exist_ok=True)
#|    shutil.copytree(source, target, dirs_exist_ok=True)
#|
#|
#|def copy_existing_site_outs(reuse_root: Path, output_root: Path, sites: list[str]) -> dict[str, str]:
#|    copied: dict[str, str] = {}
#|    for site in sites:
#|        source = reuse_root / site / "out"
#|        target = output_root / "sites" / site / "output"
#|        if not source.exists():
#|            raise SystemExit(f"missing precomputed out dir for site={site}: {source}")
#|        if target.exists():
#|            shutil.rmtree(target)
#|        copy_tree(source, target)
#|        copied[site] = str(target)
#|    return copied
#|
#|
#|def site_outs_available(root: Path, sites: list[str]) -> bool:
#|    for site in sites:
#|        if not (root / site / "out" / "panel_day_core.csv").exists():
#|            return False
#|    return True
#|
#|
#|def raw_latest_mtime(root: Path, site: str) -> float | None:
#|    raw_dir = root / site / "raw"
#|    if not raw_dir.exists():
#|        return None
#|    mtimes = [path.stat().st_mtime for path in raw_dir.glob("*.csv") if path.is_file()]
#|    return max(mtimes) if mtimes else None
#|
#|
#|def site_outs_freshness(root: Path, sites: list[str]) -> dict[str, object]:
#|    site_entries: dict[str, object] = {}
#|    all_fresh = True
#|    for site in sites:
#|        out_path = root / site / "out" / "panel_day_core.csv"
#|        raw_mtime = raw_latest_mtime(root, site)
#|        out_exists = out_path.exists()
#|        out_mtime = out_path.stat().st_mtime if out_exists else None
#|        fresh = bool(out_exists and raw_mtime is not None and out_mtime is not None and out_mtime >= raw_mtime)
#|        site_entries[site] = {
#|            "panel_day_core_exists": out_exists,
#|            "raw_latest_mtime": raw_mtime,
#|            "panel_day_core_mtime": out_mtime,
#|            "fresh_enough": fresh,
#|        }
#|        if not fresh:
#|            all_fresh = False
#|    return {"all_fresh": all_fresh, "sites": site_entries}
#|
#|
#|def resolve_reuse_existing_site_outs_root(
#|    data_root: Path,
#|    explicit_reuse_root: Path | None,
#|    prefer_existing_site_outs: str,
#|    sites: list[str],
#|) -> tuple[Path | None, str, dict[str, object]]:
#|    if explicit_reuse_root is not None:
#|        return explicit_reuse_root, "explicit", {"mode": "explicit", "sites": {}}
#|
#|    if prefer_existing_site_outs == "off":
#|        return None, "disabled", {"mode": "disabled", "sites": {}}
#|
#|    if site_outs_available(data_root, sites):
#|        freshness = site_outs_freshness(data_root, sites)
#|        if freshness["all_fresh"]:
#|            return data_root, "auto_fresh" if prefer_existing_site_outs == "auto" else "forced_fresh", freshness
#|        if prefer_existing_site_outs == "on":
#|            raise SystemExit(
#|                "prefer-existing-site-outs=on 이지만 data-root/<site>/out 가 raw보다 오래되었음"
#|            )
#|        return None, "auto_stale_out", freshness
#|
#|    if prefer_existing_site_outs == "on":
#|        raise SystemExit(
#|            f"prefer-existing-site-outs=on 이지만 data-root 아래 precomputed out를 찾지 못함: {data_root}"
#|        )
#|
#|    return None, "not_available", {"mode": "not_available", "sites": {}}
#|
#|
#|def normalize_text(value: object) -> str:
#|    if value is None:
#|        return ""
#|    if isinstance(value, float) and pd.isna(value):
#|        return ""
#|    text = str(value).strip()
#|    if text.lower() == "nan":
#|        return ""
#|    return text
#|
#|
#|def truthy_mask(series: pd.Series) -> pd.Series:
#|    lowered = series.astype(str).str.strip().str.lower()
#|    return lowered.isin({"1", "true", "t", "yes"})
#|
#|
#|def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
#|    missing = [column for column in required if column not in df.columns]
#|    if missing:
#|        raise SystemExit(f"{name} missing columns: {missing}")
#|
#|
#|def row_key(site: object, panel_id: object) -> tuple[str, str]:
#|    return normalize_text(site), normalize_text(panel_id)
#|
#|
#|def display_heuristic_name(raw_label: object) -> str:
#|    return shared_display_heuristic_name(raw_label)
#|
#|
#|def display_heuristic_note(raw_label: object) -> str:
#|    return shared_display_heuristic_note(raw_label)
#|
#|
#|def choose_display_precursor_date(
#|    event_type_ko: object,
#|    interpreted_onset_date: object,
#|    first_warning_date: object,
#|) -> str:
#|    if normalize_text(event_type_ko) != "전조형 고장":
#|        return ""
#|    onset_date = normalize_text(interpreted_onset_date)
#|    if onset_date:
#|        return onset_date
#|    return normalize_text(first_warning_date)
#|
#|
#|def choose_display_fault_date(
#|    fault_date: object,
#|    strict_trigger_date: object,
#|    first_final_fault_date: object,
#|) -> str:
#|    for candidate in [fault_date, strict_trigger_date, first_final_fault_date]:
#|        text = normalize_text(candidate)
#|        if text:
#|            return text
#|    return ""
#|
#|
#|def display_preview_precursor_date(value: object) -> str:
#|    text = normalize_text(value)
#|    return text if text else "전조없음"
#|
#|
#|def display_signal_grade(row: pd.Series) -> str:
#|    grade = normalize_text(row.get("운영해석등급_ko"))
#|    if not grade:
#|        grade = normalize_text(row.get("운영 판정"))
#|    if not grade:
#|        grade = normalize_text(row.get("현재상태"))
#|    if grade:
#|        if grade in {"고장 신호 포착", "고장 확정"}:
#|            return "확정"
#|        if grade == "강한 이상징후":
#|            return "고위험 관찰"
#|        if grade == "이상징후":
#|            return "관찰"
#|        return grade
#|    if normalize_text(row.get("패널고장여부_ko")) == "고장":
#|        return "확정"
#|    return ""
#|
#|
#|def display_existing_algorithm_source(value: object) -> str:
#|    text = normalize_text(value)
#|    if not text:
#|        return "미검출"
#|    if text.lower() == "none":
#|        return "미검출"
#|    if text == "기존 알고리즘 미검출":
#|        return "미검출"
#|    return text
#|
#|
#|def as_int(value: object) -> int:
#|    try:
#|        parsed = int(float(value))
#|    except (TypeError, ValueError):
#|        return 0
#|    return parsed
#|
#|
#|def is_truthy_scalar(value: object) -> bool:
#|    text = normalize_text(value).lower()
#|    return text in {"1", "true", "t", "yes", "y"}
#|
#|
#|def event_summary_from_labels(event_type: object, terminal_pattern: object) -> str:
#|    event = normalize_text(event_type)
#|    terminal = normalize_text(terminal_pattern)
#|    mapping = {
#|        ("전조형 고장", "급격 종료"): "전조 후 급격 종료",
#|        ("전조형 고장", "진행성 악화"): "전조 후 진행 악화",
#|        ("급작 고장", "급작 발생"): "급작 발생",
#|    }
#|    return mapping.get((event, terminal), "")
#|
#|
#|def event_display_fields(record: pd.Series | dict[str, object]) -> dict[str, str]:
#|    existing_abrupt = normalize_text(record.get("급락 종결 관측"))
#|    existing_progressive = normalize_text(record.get("점진 저하 누적"))
#|    existing_summary = normalize_text(record.get("사건 종결 요약"))
#|    if existing_abrupt or existing_progressive or existing_summary:
#|        return {
#|            "급락 종결 관측": existing_abrupt or "없음",
#|            "점진 저하 누적": existing_progressive or "없음",
#|            "사건 종결 요약": existing_summary,
#|        }
#|
#|    event_type = normalize_text(record.get("사건유형_ko")) or normalize_text(record.get("사건 해석"))
#|    terminal_pattern = normalize_text(record.get("최종고장양상_ko")) or normalize_text(
#|        record.get("최종고장양상")
#|    )
#|    precursor_date = display_preview_precursor_date(record.get("전조날짜"))
#|    grade = normalize_text(record.get("운영해석등급_ko")) or normalize_text(record.get("운영 판정"))
#|    if not grade and isinstance(record, pd.Series):
#|        grade = display_signal_grade(record)
#|
#|    abrupt_observed = (
#|        terminal_pattern in {"급격 종료", "급작 발생"}
#|        or as_int(record.get("final_days")) > 0
#|        or is_truthy_scalar(record.get("대표final_fault"))
#|        or is_truthy_scalar(record.get("final_fault"))
#|    )
#|    progressive_observed = (
#|        terminal_pattern == "진행성 악화"
#|        or event_type == "전조형 고장"
#|        or "degradation" in normalize_text(record.get("anom_subtypes_csv")).lower()
#|        or "degradation" in normalize_text(record.get("대표anom_subtype")).lower()
#|        or as_int(record.get("ews_warning_days")) > 0
#|        or as_int(record.get("pre_alarm_days")) > 0
#|        or as_int(record.get("pre_ews_days")) > 0
#|        or as_int(record.get("prefault_cond_ae_days")) > 0
#|        or as_int(record.get("prefault_cond_dtw_days")) > 0
#|        or precursor_date != "전조없음"
#|    )
#|
#|    summary = ""
#|    if grade == "확정" or normalize_text(record.get("패널고장여부_ko")) == "고장":
#|        summary = event_summary_from_labels(event_type, terminal_pattern)
#|        if not summary:
#|            if abrupt_observed and progressive_observed and precursor_date != "전조없음":
#|                summary = "전조 후 급격 종료"
#|            elif progressive_observed and precursor_date != "전조없음":
#|                summary = "전조 후 진행 악화"
#|            elif abrupt_observed:
#|                summary = "급작 발생" if precursor_date == "전조없음" else "급격 종료 관측"
#|
#|    return {
#|        "급락 종결 관측": "있음" if abrupt_observed else "없음",
#|        "점진 저하 누적": "있음" if progressive_observed else "없음",
#|        "사건 종결 요약": summary,
#|    }
#|
#|
#|def has_precursor_signal(record: dict[str, object] | pd.Series) -> bool:
#|    if normalize_text(record.get("전조날짜")):
#|        return True
#|    for field in [
#|        "ews_warning_days",
#|        "pre_alarm_days",
#|        "pre_ews_days",
#|        "prefault_cond_ae_days",
#|        "prefault_cond_dtw_days",
#|        "prefault_cond_ews_days",
#|    ]:
#|        if as_int(record.get(field)) > 0:
#|            return True
#|    return False
#|
#|
#|def has_hard_fault_evidence(record: dict[str, object] | pd.Series) -> bool:
#|    return any(
#|        [
#|            as_int(record.get("final_days")) > 0,
#|            as_int(record.get("critical_days")) > 0,
#|            as_int(record.get("critical_confirmed_days")) > 0,
#|            is_truthy_scalar(record.get("final_fault")),
#|            is_truthy_scalar(record.get("critical_fault")),
#|            is_truthy_scalar(record.get("critical_confirmed")),
#|            is_truthy_scalar(record.get("대표final_fault")),
#|            is_truthy_scalar(record.get("대표critical_fault")),
#|            is_truthy_scalar(record.get("대표critical_confirmed")),
#|        ]
#|    )
#|
#|
#|def as_float(value: object) -> float | None:
#|    try:
#|        parsed = float(value)
#|    except (TypeError, ValueError):
#|        return None
#|    if pd.isna(parsed):
#|        return None
#|    return parsed
#|
#|
#|def format_ratio(value: object, digits: int = 2) -> str:
#|    parsed = as_float(value)
#|    if parsed is None:
#|        return ""
#|    return f"{parsed:.{digits}f}"
#|
#|
#|def representative_signal_row(panel_core: pd.DataFrame) -> pd.Series:
#|    panel_df = panel_core.sort_values("date").copy()
#|    if panel_df.empty:
#|        return pd.Series(dtype=object)
#|    subtype_mask = panel_df.get("anom_subtype", pd.Series(dtype=object)).astype(str).str.contains(
#|        "degradation|fault_like|shadow_like|critical|confirmed_fault",
#|        case=False,
#|        na=False,
#|    )
#|    signal_mask = (
#|        truthy_mask(panel_df["final_fault"])
#|        | truthy_mask(panel_df["critical_fault"])
#|        | truthy_mask(panel_df["fault_like_day"])
#|        | truthy_mask(panel_df.get("event_A", pd.Series(False, index=panel_df.index)))
#|        | subtype_mask
#|    )
#|    focus_df = panel_df.loc[signal_mask].copy()
#|    if focus_df.empty:
#|        focus_df = panel_df.copy()
#|    if "mid_ratio" in focus_df.columns and focus_df["mid_ratio"].notna().any():
#|        return focus_df.sort_values(["mid_ratio", "date"], ascending=[True, True]).iloc[0]
#|    if "dtw_dist" in focus_df.columns and focus_df["dtw_dist"].notna().any():
#|        return focus_df.sort_values(["dtw_dist", "date"], ascending=[False, True]).iloc[0]
#|    return focus_df.iloc[0]
#|
#|
#|def signal_grade_explainer(evidence_row: dict[str, object]) -> str:
#|    text = normalize_text(evidence_row.get("운영해석등급_ko"))
#|    final_days = int(evidence_row.get("final_days", 0) or 0)
#|    critical_days = int(evidence_row.get("critical_days", 0) or 0)
#|    critical_confirmed_days = int(evidence_row.get("critical_confirmed_days", 0) or 0)
#|    ews_warning_days = int(evidence_row.get("ews_warning_days", 0) or 0)
#|    pre_alarm_days = int(evidence_row.get("pre_alarm_days", 0) or 0)
#|    pre_ews_days = int(evidence_row.get("pre_ews_days", 0) or 0)
#|    prefault_cond_ae_days = int(evidence_row.get("prefault_cond_ae_days", 0) or 0)
#|    prefault_cond_dtw_days = int(evidence_row.get("prefault_cond_dtw_days", 0) or 0)
#|    critical_sources = normalize_text(evidence_row.get("critical_sources_csv"))
#|    if text == "확정":
#|        signal_labels: list[str] = []
#|        if final_days > 0:
#|            signal_labels.append("최종 고장 신호")
#|        if critical_confirmed_days > 0:
#|            signal_labels.append("강한 고장 신호 확정")
#|        elif critical_days > 0:
#|            signal_labels.append("강한 고장 신호")
#|        if "vdrop" in critical_sources:
#|            signal_labels.append("vdrop 전기 신호")
#|        signal_summary = " / ".join(signal_labels) if signal_labels else "확정 신호"
#|        return (
#|            f"다음 확정 신호가 관측돼 확정({final_days + critical_days + critical_confirmed_days}일): "
#|            f"{signal_summary}. 원인명은 후보 단계"
#|        )
#|    if text == "고위험 관찰":
#|        return (
#|            f"EWS({ews_warning_days}일)·pre_alarm({pre_alarm_days}일)·pre_ews({pre_ews_days}일)"
#|            f"와 AE/DTW 전조 조건(ae={prefault_cond_ae_days}, dtw={prefault_cond_dtw_days})이 누적돼 강한 이상징후로 분류"
#|        )
#|    if text == "관찰":
#|        return "약한 전조 신호만 보여 계속 관찰이 필요한 상태로 분류"
#|    if normalize_text(evidence_row.get("패널고장여부_ko")) == "고장":
#|        return "고정 결과표 기준 fault. 원인명은 후보 단계"
#|    return ""
#|
#|
#|def pattern_explainer(
#|    evidence_row: dict[str, object], *, soften_hard_language: bool = False
#|) -> str:
#|    mid_v_ratio = as_float(evidence_row.get("대표mid_v_ratio"))
#|    mid_i_ratio = as_float(evidence_row.get("대표mid_i_ratio"))
#|    mid_ratio = as_float(evidence_row.get("대표mid_ratio"))
#|    recon_error = as_float(evidence_row.get("대표recon_error"))
#|    dtw_dist = as_float(evidence_row.get("대표dtw_dist"))
#|    hs_score = as_float(evidence_row.get("대표hs_score"))
#|    critical_source = normalize_text(evidence_row.get("대표critical_source"))
#|    anom_subtype = normalize_text(evidence_row.get("대표anom_subtype"))
#|    final_flag = normalize_text(evidence_row.get("대표final_fault")) == "True"
#|    critical_flag = normalize_text(evidence_row.get("대표critical_fault")) == "True"
#|    event_flag = normalize_text(evidence_row.get("대표event_A")) == "True"
#|
#|    reasons: list[str] = []
#|    if "vdrop" in critical_source:
#|        if soften_hard_language:
#|            reasons.append("상대 전압 이탈 징후가 반복 관측됨")
#|        else:
#|            reasons.append("전압강하형 전기 신호가 직접 관측됨")
#|    if mid_v_ratio is not None and mid_i_ratio is not None:
#|        if mid_v_ratio >= 0.9 and mid_i_ratio <= 0.4:
#|            if soften_hard_language:
#|                reasons.append(
#|                    f"전압 대비 전류 저하 징후가 나타남(mid_v={mid_v_ratio:.2f}, mid_i={mid_i_ratio:.2f})"
#|                )
#|            else:
#|                reasons.append(
#|                    f"전압은 비교적 유지되지만 전류가 크게 낮아짐(mid_v={mid_v_ratio:.2f}, mid_i={mid_i_ratio:.2f})"
#|                )
#|        elif mid_v_ratio <= 0.8 and mid_i_ratio <= 0.8:
#|            if soften_hard_language:
#|                reasons.append(
#|                    f"전압과 전류가 함께 낮아지는 징후가 이어짐(mid_v={mid_v_ratio:.2f}, mid_i={mid_i_ratio:.2f})"
#|                )
#|            else:
#|                reasons.append(
#|                    f"전압과 전류가 함께 낮아짐(mid_v={mid_v_ratio:.2f}, mid_i={mid_i_ratio:.2f})"
#|                )
#|        elif mid_i_ratio <= 0.4:
#|            if soften_hard_language:
#|                reasons.append(f"전류 저하 징후가 두드러짐(mid_i={mid_i_ratio:.2f})")
#|            else:
#|                reasons.append(f"전류가 크게 낮아진 패턴(mid_i={mid_i_ratio:.2f})")
#|    if mid_ratio is not None:
#|        if mid_ratio <= 0.1:
#|            reasons.append(f"중간 출력이 거의 0에 가까움(mid_ratio={mid_ratio:.2f})")
#|        elif mid_ratio <= 0.5:
#|            reasons.append(f"중간 출력이 뚜렷하게 낮아짐(mid_ratio={mid_ratio:.2f})")
#|    if final_flag:
#|        reasons.append("급락 종결 패턴이 직접 관측됨")
#|    elif critical_flag:
#|        reasons.append("critical fault 신호가 직접 나타남")
#|    elif event_flag:
#|        reasons.append("이상 이벤트(event_A)가 반복적으로 나타남")
#|    if "degradation" in anom_subtype:
#|        reasons.append("degradation subtype이 반복돼 점진적 저하 경향이 보임")
#|    if recon_error is not None and recon_error >= 0.05:
#|        reasons.append(f"정상 곡선 대비 복원 오차가 큼(recon={recon_error:.3f})")
#|    if dtw_dist is not None and dtw_dist >= 20:
#|        reasons.append(f"기준 곡선과 형태 차이가 큼(dtw={dtw_dist:.1f})")
#|    if hs_score is not None and hs_score >= 0.3:
#|        reasons.append(f"시계열 흔들림이 큼(hs={hs_score:.3f})")
#|    if not reasons:
#|        reasons.append("대표 관측일의 곡선/출력 변화가 정상 패턴과 다르게 나타남")
#|    return " / ".join(reasons[:3])
#|
#|
#|def to_user_preview_schema(df: pd.DataFrame) -> pd.DataFrame:
#|    if df is None or df.empty:
#|        return pd.DataFrame(columns=USER_PREVIEW_OUTPUT_COLS)
#|
#|    def pick_text(row: pd.Series, *columns: str) -> str:
#|        for column in columns:
#|            if column in row.index:
#|                text = normalize_text(row.get(column))
#|                if text:
#|                    return text
#|        return ""
#|
#|    def pick_algorithm_source(row: pd.Series) -> str:
#|        source = pick_text(
#|            row,
#|            "기존 알고리즘 source",
#|            "커널로그 기존 알고리즘 판정",
#|            "커널로그 기존 알고리즘",
#|            "critical_source",
#|        )
#|        if not source:
#|            source = MAIL_BUCKET_ALGORITHM_MAP.get(
#|                (normalize_text(row.get("site")), normalize_text(row.get("panel_id"))),
#|                "",
#|            )
#|        return display_existing_algorithm_source(source)
#|
#|    rows: list[dict[str, str]] = []
#|    for _, row in df.fillna("").iterrows():
#|        event_fields = event_display_fields(row)
#|        rows.append(
#|            {
#|                "site": normalize_text(row.get("site")),
#|                "panel_id": normalize_text(row.get("panel_id")),
#|                "전조날짜": display_preview_precursor_date(row.get("전조날짜")),
#|                "고장 기준일": pick_text(row, "고장 기준일", "고장날짜", "신호 기준일"),
#|                "운영 판정": display_signal_grade(row),
#|                **event_fields,
#|                "상위 해석 후보": pick_text(
#|                    row,
#|                    "상위 해석 후보",
#|                    "원인 추정",
#|                    "알고리즘 해석 원인",
#|                    "원인",
#|                    "1순위_의심원인_ko",
#|                ),
#|                "기존 알고리즘 source": pick_algorithm_source(row),
#|            }
#|        )
#|    return pd.DataFrame(rows).reindex(columns=USER_PREVIEW_OUTPUT_COLS)
#|
#|
#|def to_signal_preview_schema(df: pd.DataFrame) -> pd.DataFrame:
#|    if df is None or df.empty:
#|        return pd.DataFrame(columns=SIGNAL_PREVIEW_OUTPUT_COLS)
#|
#|    def pick_text(row: pd.Series, *columns: str) -> str:
#|        for column in columns:
#|            if column in row.index:
#|                text = normalize_text(row.get(column))
#|                if text:
#|                    return text
#|        return ""
#|
#|    def pick_algorithm_source(row: pd.Series) -> str:
#|        source = pick_text(
#|            row,
#|            "기존 알고리즘 source",
#|            "커널로그 기존 알고리즘 판정",
#|            "커널로그 기존 알고리즘",
#|            "critical_source",
#|        )
#|        if not source:
#|            source = MAIL_BUCKET_ALGORITHM_MAP.get(
#|                (normalize_text(row.get("site")), normalize_text(row.get("panel_id"))),
#|                "",
#|            )
#|        return display_existing_algorithm_source(source)
#|
#|    rows: list[dict[str, str]] = []
#|    for _, row in df.fillna("").iterrows():
#|        event_fields = event_display_fields(row)
#|        rows.append(
#|            {
#|                "site": normalize_text(row.get("site")),
#|                "panel_id": normalize_text(row.get("panel_id")),
#|                "전조날짜": display_preview_precursor_date(row.get("전조날짜")),
#|                "신호 기준일": pick_text(row, "신호 기준일", "고장날짜", "고장 기준일"),
#|                "운영 판정": display_signal_grade(row),
#|                **event_fields,
#|                "상위 해석 후보": pick_text(
#|                    row,
#|                    "상위 해석 후보",
#|                    "원인 추정",
#|                    "알고리즘 해석 원인",
#|                    "원인",
#|                    "1순위_의심원인_ko",
#|                ),
#|                "기존 알고리즘 source": pick_algorithm_source(row),
#|            }
#|        )
#|    return pd.DataFrame(rows).reindex(columns=SIGNAL_PREVIEW_OUTPUT_COLS)
#|
#|
#|def load_raw_only_common_module():
#|    package = package_root()
#|    if str(package) not in sys.path:
#|        sys.path.insert(0, str(package))
#|    from research.prognostics import runtime_rawonly_chain_common_v1 as raw_only_common_mod
#|
#|    return raw_only_common_mod
#|
#|
#|def load_runtime_heuristic_module():
#|    package = package_root()
#|    if str(package) not in sys.path:
#|        sys.path.insert(0, str(package))
#|    from research.prognostics import (
#|        build_panel_day_engine_runtime_heuristic_v1 as runtime_heuristic_mod,
#|    )
#|
#|    return runtime_heuristic_mod
#|
#|
#|def packaged_live_chain_support() -> dict[str, object]:
#|    required_scripts = [
#|        "build_panel_day_engine_bootstrap_verdict_v1.py",
#|        "build_panel_day_engine_fault_panel_event_audit_v1.py",
#|        "build_panel_day_engine_panel_multiaxis_verdict_v1.py",
#|        "build_panel_day_engine_gpvs_evidence_pack_v1.py",
#|        "build_panel_day_engine_cause_candidate_heuristics_v1.py",
#|    ]
#|    required_share_inputs = [
#|        "panel_day_engine_operator_workflow_default_v1.csv",
#|        "panel_day_engine_abrupt6_symptom_map_v1.csv",
#|        "panel_day_engine_kernellog_project_mapping_v1.csv",
#|        "panel_day_engine_gpv7_perf_summary_v1.csv",
#|        "panel_day_engine_project_final_decision_pack_v1.csv",
#|        "panel_day_engine_precursor_onset_truth_v1.csv",
#|        "panel_day_engine_non_precursor_performance_cases_v1.csv",
#|        "panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv",
#|        "panel_day_engine_gpvs_panel_attach_inventory_v1.csv",
#|        "panel_day_engine_gpvs_panel_attach_feasibility_v1.csv",
#|        "panel_day_engine_gpvs_panel_attach_candidates_v1.csv",
#|        "panel_day_engine_precursor_abrupt_consistency_cases_v1.csv",
#|        "panel_day_engine_precursor_abrupt_consistency_summary_v1.csv",
#|        "panel_day_engine_precursor_abrupt_consistency_recommendation_v1.csv",
#|        "panel_day_engine_c42997_1_1_forensic_summary_v1.csv",
#|        "panel_day_engine_fault_panel_event_audit_v1.csv",
#|        "panel_day_engine_detailed_fault_bridge_audit_v1.csv",
#|        "panel_day_engine_detailed_fault_bridge_summary_v1.csv",
#|        "panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv",
#|        "panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv",
#|        "panel_day_engine_gpvs_detailed_type_realpanel_sanity_v1.csv",
#|        "panel_day_engine_gpvs_mlpe_panel_agreement_v1.csv",
#|        "panel_day_engine_gpvs_canonical_dictionary_v1.csv",
#|        "panel_day_engine_gpvs_mlpe_fault_matching_table_v1.csv",
#|        "panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv",
#|        "panel_day_engine_gpvs_mlpe_fault_matching_summary_v1.csv",
#|        "panel_day_engine_gpvs_evidence_pack_v1.csv",
#|        "panel_day_engine_panel_multiaxis_verdict_v1.csv",
#|        "panel_date_reaudit_working.csv",
#|    ]
#|    missing_scripts = [name for name in required_scripts if not packaged_script_path(name).exists()]
#|    missing_share = [name for name in required_share_inputs if not (packaged_share_root() / name).exists()]
#|    supported = not missing_scripts and not missing_share
#|    return {
#|        "supported": supported,
#|        "required_scripts": required_scripts,
#|        "required_share_inputs": required_share_inputs,
#|        "missing_scripts": missing_scripts,
#|        "missing_share_inputs": missing_share,
#|        "note_ko": (
#|            "live chain은 package 내부에 복사된 bootstrap/audit/verdict/evidence/heuristic 스크립트와 "
#|            "frozen share 입력을 사용해 workspace-only로 재계산한다."
#|        ),
#|    }
#|
#|
#|def packaged_raw_only_chain_support() -> dict[str, object]:
#|    required_scripts = [
#|        "runtime_rawonly_chain_common_v1.py",
#|        "build_panel_day_engine_runtime_fault_event_audit_v1.py",
#|        "build_panel_day_engine_runtime_final_verdict_v1.py",
#|        "build_panel_day_engine_runtime_heuristic_v1.py",
#|    ]
#|    missing_scripts = [name for name in required_scripts if not packaged_script_path(name).exists()]
#|    return {
#|        "supported": not missing_scripts,
#|        "required_scripts": required_scripts,
#|        "missing_scripts": missing_scripts,
#|        "note_ko": (
#|            "raw-only chain은 package 내부에 복사된 runtime audit/verdict/heuristic 스크립트만 사용한다. "
#|            "frozen share truth/support asset은 참조하지 않는다."
#|        ),
#|    }
#|
#|
#|def normalize_core_digest_frame(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
#|    ensure_columns(df, CORE_DIGEST_COLUMNS, source_name)
#|    digest_df = df.loc[:, CORE_DIGEST_COLUMNS].copy()
#|    digest_df["date"] = pd.to_datetime(digest_df["date"], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
#|    for column in CORE_DIGEST_COLUMNS:
#|        if column == "date":
#|            continue
#|        digest_df[column] = digest_df[column].map(normalize_text)
#|    digest_df["panel_id"] = digest_df["panel_id"].astype(str)
#|    return digest_df.sort_values(["panel_id", "date"]).reset_index(drop=True)
#|
#|
#|def build_core_digest_payload(df: pd.DataFrame, source_name: str) -> dict[str, object]:
#|    digest_df = normalize_core_digest_frame(df, source_name)
#|    joined_rows = "\n".join(
#|        "|".join(normalize_text(value) for value in row)
#|        for row in digest_df.itertuples(index=False, name=None)
#|    )
#|    return {
#|        "columns": CORE_DIGEST_COLUMNS,
#|        "row_count": int(len(digest_df)),
#|        "digest_sha256": hashlib.sha256(joined_rows.encode("utf-8")).hexdigest(),
#|        "critical_source_counts": {
#|            key: int(value)
#|            for key, value in digest_df["critical_source"].value_counts(dropna=False).sort_index().items()
#|        },
#|        "anom_level_counts": {
#|            key: int(value)
#|            for key, value in digest_df["anom_level"].value_counts(dropna=False).sort_index().items()
#|        },
#|        "confirmed_fault_true_count": int(truthy_mask(digest_df["confirmed_fault"]).sum()),
#|        "critical_fault_true_count": int(truthy_mask(digest_df["critical_fault"]).sum()),
#|        "final_fault_true_count": int(truthy_mask(digest_df["final_fault"]).sum()),
#|    }
#|
#|
#|def load_core_baseline_digest() -> dict[str, object]:
#|    path = baseline_core_digest_path()
#|    if not path.exists():
#|        raise SystemExit(f"missing packaged core baseline digest: {path}")
#|    return json.loads(path.read_text(encoding="utf-8"))
#|
#|
#|def compare_single_site_digest(expected: dict[str, object], actual: dict[str, object]) -> list[str]:
#|    diffs: list[str] = []
#|    for key in [
#|        "row_count",
#|        "digest_sha256",
#|        "confirmed_fault_true_count",
#|        "critical_fault_true_count",
#|        "final_fault_true_count",
#|    ]:
#|        if expected.get(key) != actual.get(key):
#|            diffs.append(f"{key}: expected={expected.get(key)} actual={actual.get(key)}")
#|    if expected.get("columns") != actual.get("columns"):
#|        diffs.append("columns: expected reference columns differ from actual columns")
#|    if expected.get("critical_source_counts") != actual.get("critical_source_counts"):
#|        diffs.append("critical_source_counts: expected reference counts differ from actual counts")
#|    if expected.get("anom_level_counts") != actual.get("anom_level_counts"):
#|        diffs.append("anom_level_counts: expected reference counts differ from actual counts")
#|    return diffs
#|
#|
#|def load_panel_day_core_from_workspace(workspace_root: Path, site: str) -> pd.DataFrame:
#|    path = workspace_root / "data" / site / "out" / "panel_day_core.csv"
#|    if not path.exists():
#|        raise SystemExit(f"missing workspace panel_day_core: {path}")
#|    df = pd.read_csv(path, low_memory=False)
#|    ensure_columns(
#|        df,
#|        ["panel_id", "date", "final_fault", "critical_fault", "fault_like_day", "critical_source"],
#|        path.name,
#|    )
#|    df["panel_id"] = df["panel_id"].astype(str)
#|    df["date"] = pd.to_datetime(df["date"], errors="coerce")
#|    return df
#|
#|
#|def representative_algorithm_fields(site: str, core_df: pd.DataFrame, panel_id: str) -> dict[str, str]:
#|    mapped = MAIL_BUCKET_ALGORITHM_MAP.get((normalize_text(site), normalize_text(panel_id)), "")
#|    if mapped:
#|        return {"커널로그 기존 알고리즘": mapped}
#|    panel_df = core_df.loc[core_df["panel_id"].eq(str(panel_id))].copy().sort_values("date")
#|    if panel_df.empty:
#|        return {"커널로그 기존 알고리즘": ""}
#|
#|    final_days = panel_df.loc[truthy_mask(panel_df["final_fault"])]
#|    critical_days = panel_df.loc[truthy_mask(panel_df["critical_fault"])]
#|    fault_like_days = panel_df.loc[truthy_mask(panel_df["fault_like_day"])]
#|
#|    if not final_days.empty:
#|        representative = final_days.iloc[0]
#|    elif not critical_days.empty:
#|        representative = critical_days.iloc[0]
#|    elif not fault_like_days.empty:
#|        representative = fault_like_days.iloc[0]
#|    else:
#|        representative = panel_df.iloc[-1]
#|
#|    return {"커널로그 기존 알고리즘": normalize_text(representative.get("critical_source"))}
#|
#|
#|def build_live_fault_table(workspace_root: Path) -> pd.DataFrame:
#|    verdict_path = workspace_root / "_share" / "panel_day_engine_panel_multiaxis_verdict_v1.csv"
#|    heuristic_path = workspace_root / "_share" / "panel_day_engine_cause_candidate_heuristics_v1.csv"
#|    audit_path = workspace_root / "_share" / "panel_day_engine_fault_panel_event_audit_v1.csv"
#|    verdict_df = pd.read_csv(verdict_path, encoding="utf-8-sig", low_memory=False)
#|    heuristic_df = pd.read_csv(heuristic_path, encoding="utf-8-sig", low_memory=False)
#|    audit_df = pd.read_csv(audit_path, encoding="utf-8-sig", low_memory=False)
#|    ensure_columns(
#|        verdict_df,
#|        ["site", "panel_id", "패널고장여부_ko", "사건유형_ko", "최종고장양상_ko", "커널로그_원인군_ko"],
#|        verdict_path.name,
#|    )
#|    ensure_columns(
#|        heuristic_df,
#|        ["site", "panel_id", "원인후보_top1_ko", "원인후보_top2_ko", "원인후보_top3_ko"],
#|        heuristic_path.name,
#|    )
#|    ensure_columns(
#|        audit_df,
#|        [
#|            "site",
#|            "panel_id",
#|            "earliest_warning_date",
#|            "strict_trigger_date",
#|            "first_final_fault_date",
#|        ],
#|        audit_path.name,
#|    )
#|
#|    heuristic_lookup = {
#|        row_key(row["site"], row["panel_id"]): row
#|        for row in heuristic_df.to_dict(orient="records")
#|    }
#|    audit_lookup = {
#|        row_key(row["site"], row["panel_id"]): row
#|        for row in audit_df.to_dict(orient="records")
#|    }
#|    rows: list[dict[str, str]] = []
#|    for row in verdict_df.loc[verdict_df["패널고장여부_ko"].map(normalize_text).eq("고장")].to_dict(orient="records"):
#|        key = row_key(row["site"], row["panel_id"])
#|        heuristic_row = heuristic_lookup.get(key)
#|        if heuristic_row is None:
#|            raise SystemExit(f"missing heuristic row for fault panel: {key}")
#|        audit_row = audit_lookup.get(key, {})
#|        rows.append(
#|            {
#|                "site": normalize_text(row["site"]),
#|                "panel_id": normalize_text(row["panel_id"]),
#|                "패널고장여부_ko": normalize_text(row["패널고장여부_ko"]),
#|                "사건유형_ko": normalize_text(row["사건유형_ko"]),
#|                "최종고장양상_ko": normalize_text(row["최종고장양상_ko"]),
#|                "커널로그_원인군_ko": normalize_text(row["커널로그_원인군_ko"]),
#|                "1순위_의심원인_ko": display_heuristic_name(heuristic_row["원인후보_top1_ko"]),
#|                "2순위_의심원인_ko": display_heuristic_name(heuristic_row["원인후보_top2_ko"]),
#|                "3순위_의심원인_ko": display_heuristic_name(heuristic_row["원인후보_top3_ko"]),
#|                "전조날짜": choose_display_precursor_date(
#|                    event_type_ko=row.get("사건유형_ko"),
#|                    interpreted_onset_date=row.get("사건해석상전조시작일"),
#|                    first_warning_date=audit_row.get("earliest_warning_date"),
#|                ),
#|                "고장날짜": choose_display_fault_date(
#|                    fault_date=row.get("세부fault_기준일"),
#|                    strict_trigger_date=audit_row.get("strict_trigger_date"),
#|                    first_final_fault_date=audit_row.get("first_final_fault_date"),
#|                ),
#|            }
#|        )
#|    return (
#|        pd.DataFrame(rows)
#|        .reindex(columns=LIVE_FAULT_OUTPUT_COLS)
#|        .sort_values(["site", "panel_id"], ascending=[True, True])
#|        .reset_index(drop=True)
#|    )
#|
#|
#|def build_live_fault_preview(workspace_root: Path, fault_df: pd.DataFrame) -> pd.DataFrame:
#|    per_site_core = {
#|        site: load_panel_day_core_from_workspace(workspace_root, site)
#|        for site in sorted(fault_df["site"].astype(str).unique())
#|    }
#|    rows: list[dict[str, str]] = []
#|    for _, row in fault_df.iterrows():
#|        site = normalize_text(row["site"])
#|        panel_id = normalize_text(row["panel_id"])
#|        rows.append(
#|            {
#|                "site": site,
#|                "panel_id": panel_id,
#|                "패널고장여부_ko": normalize_text(row["패널고장여부_ko"]),
#|                "사건유형_ko": normalize_text(row["사건유형_ko"]),
#|                "최종고장양상_ko": normalize_text(row["최종고장양상_ko"]),
#|                "전조날짜": normalize_text(row.get("전조날짜")),
#|                "고장날짜": normalize_text(row.get("고장날짜")),
#|                "라벨된 fault": normalize_text(row["커널로그_원인군_ko"]),
#|                "1순위_의심원인_ko": normalize_text(row["1순위_의심원인_ko"]),
#|                "2순위_의심원인_ko": normalize_text(row["2순위_의심원인_ko"]),
#|                "3순위_의심원인_ko": normalize_text(row["3순위_의심원인_ko"]),
#|                **representative_algorithm_fields(site, per_site_core[site], panel_id),
#|            }
#|        )
#|    return pd.DataFrame(rows).reindex(columns=LIVE_PREVIEW_OUTPUT_COLS)
#|
#|
#|def compare_live_fault_to_fixed(live_fault_df: pd.DataFrame) -> dict[str, object]:
#|    fixed_path = fixed_fault6_table_path()
#|    if not fixed_path.exists():
#|        return {
#|            "fixed_reference_available": False,
#|            "exact_match": False,
#|            "diff_columns": [],
#|        }
#|    fixed_df = pd.read_csv(fixed_path, encoding="utf-8-sig", low_memory=False).sort_values(["site", "panel_id"]).reset_index(drop=True)
#|    live_df = live_fault_df.sort_values(["site", "panel_id"]).reset_index(drop=True)
#|    diff_columns: list[str] = []
#|    if len(fixed_df) != len(live_df):
#|        diff_columns.append("__row_count__")
#|    else:
#|        for column in LIVE_FAULT_OUTPUT_COLS:
#|            if column not in LIVE_FAULT_COMPARE_COLS:
#|                continue
#|            left = fixed_df[column].fillna("").astype(str)
#|            right = live_df[column].fillna("").astype(str)
#|            if not left.equals(right):
#|                diff_columns.append(column)
#|    return {
#|        "fixed_reference_available": True,
#|        "exact_match": not diff_columns,
#|        "diff_columns": diff_columns,
#|        "fixed_row_count": int(len(fixed_df)),
#|        "live_row_count": int(len(live_df)),
#|    }
#|
#|
#|def publish_live_chain_outputs(output_root: Path, result_dir: Path, summary_path: Path) -> dict[str, str]:
#|    root_result_dir = output_root / "result"
#|    root_result_dir.mkdir(parents=True, exist_ok=True)
#|
#|    mapping = {
#|        result_dir / "fault_panel_result_live_v1.csv": root_result_dir / ROOT_LIVE_FAULT_NAME,
#|        result_dir / "fault_panel_result_live_preview_v1.csv": root_result_dir / ROOT_LIVE_PREVIEW_NAME,
#|    }
#|    published: dict[str, str] = {}
#|    for source, target in mapping.items():
#|        if not source.exists():
#|            raise SystemExit(f"missing live chain output for publish step: {source}")
#|        shutil.copy2(source, target)
#|        published[target.name] = str(target)
#|    return published
#|
#|
#|def publish_raw_only_chain_outputs(output_root: Path, result_dir: Path) -> dict[str, str]:
#|    root_result_dir = output_root / "result"
#|    root_result_dir.mkdir(parents=True, exist_ok=True)
#|    mapping = {
#|        result_dir / "fault_panel_result_raw_only_v1.csv": root_result_dir / ROOT_RAWONLY_FAULT_NAME,
#|        result_dir / "fault_panel_result_raw_only_preview_v1.csv": root_result_dir / ROOT_RAWONLY_PREVIEW_NAME,
#|    }
#|    published: dict[str, str] = {}
#|    for source, target in mapping.items():
#|        if not source.exists():
#|            raise SystemExit(f"missing raw-only chain output for publish step: {source}")
#|        shutil.copy2(source, target)
#|        published[target.name] = str(target)
#|    return published
#|
#|
#|def build_strict_raw_only_current_outputs(
#|    raw_only_chain_result: dict[str, object],
#|    evidence_df: pd.DataFrame,
#|) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
#|    candidate_fault_path = Path(
#|        str(raw_only_chain_result.get("generated_outputs", {}).get("fault_panel_result_raw_only_v1", ""))
#|    )
#|    candidate_preview_path = Path(
#|        str(raw_only_chain_result.get("generated_outputs", {}).get("fault_panel_result_raw_only_preview_v1", ""))
#|    )
#|    if not candidate_fault_path.exists() or not candidate_preview_path.exists():
#|        raise SystemExit("missing candidate raw-only outputs for strict current publish")
#|
#|    candidate_fault_df = pd.read_csv(candidate_fault_path, encoding="utf-8-sig", low_memory=False)
#|    candidate_preview_df = pd.read_csv(candidate_preview_path, encoding="utf-8-sig", low_memory=False)
#|    strict_keys = {
#|        row_key(row["site"], row["panel_id"])
#|        for row in evidence_df.to_dict(orient="records")
#|        if normalize_text(row.get("운영해석등급_ko")) in RAW_ONLY_STRICT_CURRENT_GRADES
#|    }
#|    if strict_keys:
#|        strict_fault_df = candidate_fault_df.loc[
#|            candidate_fault_df.apply(lambda row: row_key(row["site"], row["panel_id"]) in strict_keys, axis=1)
#|        ].copy()
#|        strict_preview_df = candidate_preview_df.loc[
#|            candidate_preview_df.apply(lambda row: row_key(row["site"], row["panel_id"]) in strict_keys, axis=1)
#|        ].copy()
#|    else:
#|        strict_fault_df = candidate_fault_df.iloc[0:0].copy()
#|        strict_preview_df = candidate_preview_df.iloc[0:0].copy()
#|
#|    strict_fault_df = strict_fault_df.sort_values(["site", "panel_id"]).reset_index(drop=True)
#|    strict_preview_df = strict_preview_df.sort_values(["site", "panel_id"]).reset_index(drop=True)
#|    date_lookup = {
#|        row_key(row["site"], row["panel_id"]): {
#|            "전조날짜": normalize_text(row.get("전조날짜")),
#|            "고장날짜": normalize_text(row.get("고장날짜")),
#|        }
#|        for row in evidence_df.to_dict(orient="records")
#|    }
#|    for df in [strict_fault_df, strict_preview_df]:
#|        if df.empty:
#|            continue
#|        df["전조날짜"] = df.apply(
#|            lambda row: date_lookup.get(row_key(row["site"], row["panel_id"]), {}).get("전조날짜", ""),
#|            axis=1,
#|        )
#|        df["고장날짜"] = df.apply(
#|            lambda row: date_lookup.get(row_key(row["site"], row["panel_id"]), {}).get("고장날짜", ""),
#|            axis=1,
#|        )
#|        ordered_cols = [column for column in df.columns if column not in {"전조날짜", "고장날짜"}]
#|        insert_at = ordered_cols.index("최종고장양상_ko") + 1 if "최종고장양상_ko" in ordered_cols else len(ordered_cols)
#|        ordered_cols[insert_at:insert_at] = ["전조날짜", "고장날짜"]
#|        df = df.reindex(columns=ordered_cols)
#|        if df is strict_fault_df:
#|            strict_fault_df = df
#|        else:
#|            strict_preview_df = df
#|    meta = {
#|        "publish_policy_ko": "raw_only current는 운영해석등급_ko=확정 strict subset만 노출",
#|        "strict_grade_csv": ",".join(sorted(RAW_ONLY_STRICT_CURRENT_GRADES)),
#|        "candidate_row_count": int(len(candidate_fault_df)),
#|        "published_current_row_count": int(len(strict_fault_df)),
#|        "dropped_candidate_row_count": int(len(candidate_fault_df) - len(strict_fault_df)),
#|    }
#|    return strict_fault_df, strict_preview_df, meta
#|
#|
#|def publish_raw_only_current_outputs(
#|    output_root: Path,
#|    strict_fault_df: pd.DataFrame,
#|    strict_preview_df: pd.DataFrame,
#|) -> dict[str, str]:
#|    root_result_dir = output_root / "result"
#|    root_result_dir.mkdir(parents=True, exist_ok=True)
#|    fault_path = root_result_dir / ROOT_RAWONLY_FAULT_NAME
#|    preview_path = root_result_dir / ROOT_RAWONLY_PREVIEW_NAME
#|    strict_fault_df.to_csv(fault_path, index=False, encoding="utf-8-sig")
#|    strict_preview_df.to_csv(preview_path, index=False, encoding="utf-8-sig")
#|    return {
#|        ROOT_RAWONLY_FAULT_NAME: str(fault_path),
#|        ROOT_RAWONLY_PREVIEW_NAME: str(preview_path),
#|    }
#|
#|
#|def markdown_table_from_df(df: pd.DataFrame) -> str:
#|    if df.empty:
#|        return "_empty_"
#|    safe_df = df.fillna("").astype(str)
#|    headers = safe_df.columns.tolist()
#|    lines = [
#|        "| " + " | ".join(headers) + " |",
#|        "| " + " | ".join(["---"] * len(headers)) + " |",
#|    ]
#|    for row in safe_df.itertuples(index=False, name=None):
#|        lines.append("| " + " | ".join(str(value) for value in row) + " |")
#|    return "\n".join(lines)
#|
#|
#|def truncate_report_df(df: pd.DataFrame, limit: int = 20) -> pd.DataFrame:
#|    if df.empty or len(df) <= limit:
#|        return df
#|    return df.head(limit).copy()
#|
#|
#|def build_live_report_markdown(
#|    sites: list[str],
#|    baseline_comparison: dict[str, object],
#|    compare: dict[str, object],
#|    published_outputs: dict[str, str],
#|    live_preview_df: pd.DataFrame,
#|) -> str:
#|    site_lines = "\n".join(f"- `{site}`" for site in sites)
#|    baseline_site_lines = []
#|    for site in sites:
#|        site_entry = baseline_comparison.get("sites", {}).get(site, {})
#|        baseline_site_lines.append(
#|            f"- `{site}`: `match={site_entry.get('match')}`"
#|        )
#|    baseline_block = "\n".join(baseline_site_lines)
#|    output_lines = "\n".join(
#|        f"- `{name}`: `{path}`" for name, path in sorted(published_outputs.items())
#|    )
#|    return (
#|        "# fault_panel_result_current_report_v1\n\n"
#|        "## 목적\n"
#|        "현재 runtime 실행에서 운영자가 바로 확인할 `운영 공식 current` 결과를 한 곳에 모아 보여준다.\n\n"
#|        "## 실행 대상 site\n"
#|        f"{site_lines}\n\n"
#|        "## baseline 입력 비교\n"
#|        f"- `all_sites_match`: `{baseline_comparison.get('all_sites_match')}`\n"
#|        f"{baseline_block}\n\n"
#|        "## live chain 상태\n"
#|        f"- `fixed_fault_reference_exact_match`: `{compare.get('exact_match')}`\n"
#|        f"- `baseline_input_all_sites_match`: `{compare.get('baseline_input_all_sites_match')}`\n"
#|        f"- `diff_columns`: `{compare.get('diff_columns', [])}`\n\n"
#|        "## 읽는 법\n"
#|        "- 이 report는 `official current` 설명용 문서다.\n"
#|        "- `fault_panel_result_current_preview_v1.csv`와 함께 현재 운영 공식 결과를 먼저 읽는 기본 문서다.\n"
#|        "- `raw-only` 보조표나 analyst artifact를 대신하지 않는다.\n"
#|        "- `fault_panel_result_master_report_v1.md`는 artifact 안내와 fallback 설명용 문서이며, 이 report를 대체하지 않는다.\n\n"
#|        "## 주요 산출물\n"
#|        f"{output_lines}\n\n"
#|        "## 현재 preview 표\n"
#|        f"{markdown_table_from_df(live_preview_df)}\n"
#|    )
#|
#|
#|def build_raw_only_report_markdown(
#|    sites: list[str],
#|    compare: dict[str, object],
#|    published_outputs: dict[str, str],
#|    live_preview_df: pd.DataFrame,
#|    publish_meta: dict[str, object] | None = None,
#|) -> str:
#|    site_lines = "\n".join(f"- `{site}`" for site in sites)
#|    output_lines = "\n".join(
#|        f"- `{name}`: `{path}`" for name, path in sorted(published_outputs.items())
#|    )
#|    publish_meta = publish_meta or {}
#|    return (
#|        "# fault_panel_result_raw_only_current_report_v1\n\n"
#|        "## 목적\n"
#|        "raw-only algorithm candidate chain 중 운영 strict current로 승격된 현재 결과를 `분석용/운영 보조표`로 확인한다.\n\n"
#|        "## 실행 대상 site\n"
#|        f"{site_lines}\n\n"
#|        "## raw-only vs fixed reference 비교\n"
#|        f"- `status_ko`: `{compare.get('status_ko')}`\n"
#|        f"- `reference_available`: `{compare.get('reference_available')}`\n"
#|        f"- `row_key_match`: `{compare.get('row_key_match')}`\n"
#|        f"- `decision_columns_match`: `{compare.get('decision_columns_match')}`\n"
#|        f"- `overlap_decision_columns_match`: `{compare.get('overlap_decision_columns_match')}`\n"
#|        f"- `exact_match`: `{compare.get('exact_match')}`\n"
#|        f"- `reference_row_count`: `{compare.get('reference_row_count')}`\n"
#|        f"- `candidate_row_count`: `{compare.get('candidate_row_count')}`\n"
#|        f"- `matched_row_key_count`: `{compare.get('matched_row_key_count')}`\n"
#|        f"- `diff_columns`: `{compare.get('diff_columns', [])}`\n\n"
#|        f"- `overlap_diff_columns`: `{compare.get('overlap_diff_columns', [])}`\n\n"
#|        "## current 출력 정책\n"
#|        f"- `publish_policy_ko`: `{publish_meta.get('publish_policy_ko', '')}`\n"
#|        f"- `strict_grade_csv`: `{publish_meta.get('strict_grade_csv', '')}`\n"
#|        f"- `published_current_row_count`: `{publish_meta.get('published_current_row_count', '')}`\n"
#|        f"- `candidate_row_count`: `{publish_meta.get('candidate_row_count', '')}`\n"
#|        f"- `dropped_candidate_row_count`: `{publish_meta.get('dropped_candidate_row_count', '')}`\n\n"
#|        "## 주의\n"
#|        "- `커널로그_원인군_ko` 컬럼명은 유지하지만, 이 report에서는 raw-only algorithm-derived family 의미다.\n"
#|        "- 이 chain은 frozen truth/support asset을 참조하지 않는다.\n\n"
#|        "- 이 report는 `official current report`가 아니며, 운영 공식 결과를 대체하지 않는다.\n"
#|        "- 운영자 기본 진입점은 `fault_panel_result_current_*` 계열이고, 이 report는 analyst/support 확인용이다.\n\n"
#|        "- preview 표의 `사건 종결 요약`은 관측 플래그를 먼저 본 뒤, 확정 row에서만 채워지는 요약이다.\n\n"
#|        "- `result/raw_only_chain/*`에는 전체 candidate가 남고, `result/fault_panel_result_raw_only_current_*`는 strict current subset만 노출한다.\n\n"
#|        "## 주요 산출물\n"
#|        f"{output_lines}\n\n"
#|        "## 현재 preview 표\n"
#|        f"{markdown_table_from_df(truncate_report_df(live_preview_df))}\n"
#|    )
#|
#|
#|def build_master_report_markdown(
#|    sites: list[str],
#|    baseline_comparison: dict[str, object],
#|    live_chain_result: dict[str, object],
#|    raw_only_chain_result: dict[str, object],
#|    live_preview_df: pd.DataFrame,
#|    raw_only_preview_df: pd.DataFrame,
#|    precursor_report_df: pd.DataFrame | None = None,
#|    fault_signal_report_df: pd.DataFrame | None = None,
#|    detailed_report_path: Path | None = None,
#|    precursor_report_path: Path | None = None,
#|    fault_signal_report_path: Path | None = None,
#|) -> str:
#|    site_lines = "\n".join(f"- `{site}`" for site in sites)
#|    baseline_site_lines = []
#|    for site in sites:
#|        site_entry = baseline_comparison.get("sites", {}).get(site, {})
#|        baseline_site_lines.append(f"- `{site}`: `match={site_entry.get('match')}`")
#|    baseline_block = "\n".join(baseline_site_lines)
#|    live_compare = live_chain_result.get("fixed_fault_reference_compare", {})
#|    raw_only_compare = raw_only_chain_result.get("fixed_fault_reference_compare", {})
#|    primary_output_lines = []
#|    analyst_output_lines = []
#|    for name, path in sorted(live_chain_result.get("published_outputs", {}).items()):
#|        primary_output_lines.append(f"- `live::{name}`: `{path}`")
#|    for name, path in sorted(raw_only_chain_result.get("published_outputs", {}).items()):
#|        analyst_output_lines.append(f"- `raw_only::{name}`: `{path}`")
#|    primary_output_block = "\n".join(primary_output_lines) if primary_output_lines else "_none_"
#|    analyst_output_block = "\n".join(analyst_output_lines) if analyst_output_lines else "_none_"
#|    precursor_report_df = precursor_report_df if precursor_report_df is not None else pd.DataFrame()
#|    fault_signal_report_df = fault_signal_report_df if fault_signal_report_df is not None else pd.DataFrame()
#|    precursor_keys = set(
#|        zip(
#|            precursor_report_df.get("site", pd.Series(dtype=object)).astype(str),
#|            precursor_report_df.get("panel_id", pd.Series(dtype=object)).astype(str),
#|        )
#|    )
#|    fault_signal_keys = set(
#|        zip(
#|            fault_signal_report_df.get("site", pd.Series(dtype=object)).astype(str),
#|            fault_signal_report_df.get("panel_id", pd.Series(dtype=object)).astype(str),
#|        )
#|    )
#|    overlap_row_count = len(precursor_keys & fault_signal_keys)
#|    fault_signal_subgroup_summary = pd.DataFrame(
#|        columns=["site", "group root", "subgroup base", "row_count"]
#|    )
#|    fault_signal_cluster_summary = pd.DataFrame(
#|        columns=[
#|            "site",
#|            "group root",
#|            "subgroup base",
#|            "subgroup cluster",
#|            "row_count",
#|            "min_signal_date",
#|            "max_signal_date",
#|        ]
#|    )
#|    if fault_signal_report_df is not None and not fault_signal_report_df.empty:
#|        working = fault_signal_report_df.copy()
#|        working["group root"] = working["group root"].map(normalize_text)
#|        working["subgroup base"] = working["subgroup base"].map(normalize_text)
#|        working["subgroup cluster"] = working["subgroup cluster"].map(normalize_text)
#|        working["신호 기준일_dt"] = pd.to_datetime(working["신호 기준일"], errors="coerce")
#|        working = working.loc[working["subgroup base"].ne("")].copy()
#|        if not working.empty:
#|            fault_signal_subgroup_summary = (
#|                working.groupby(["site", "group root", "subgroup base"], dropna=False)
#|                .size()
#|                .rename("row_count")
#|                .reset_index()
#|                .sort_values(
#|                    ["row_count", "site", "group root", "subgroup base"],
#|                    ascending=[False, True, True, True],
#|                )
#|                .reset_index(drop=True)
#|            )
#|            fault_signal_cluster_summary = (
#|                working.groupby(
#|                    ["site", "group root", "subgroup base", "subgroup cluster"], dropna=False
#|                )
#|                .agg(
#|                    row_count=("panel_id", "size"),
#|                    min_signal_date=("신호 기준일_dt", "min"),
#|                    max_signal_date=("신호 기준일_dt", "max"),
#|                )
#|                .reset_index()
#|                .sort_values(
#|                    ["row_count", "site", "group root", "subgroup base", "subgroup cluster"],
#|                    ascending=[False, True, True, True, True],
#|                )
#|                .reset_index(drop=True)
#|            )
#|            for column in ["min_signal_date", "max_signal_date"]:
#|                fault_signal_cluster_summary[column] = pd.to_datetime(
#|                    fault_signal_cluster_summary[column], errors="coerce"
#|                ).dt.strftime("%Y-%m-%d")
#|    fault_signal_unique_group_root_count = (
#|        int(len(fault_signal_subgroup_summary[["site", "group root"]].drop_duplicates()))
#|        if not fault_signal_subgroup_summary.empty
#|        else 0
#|    )
#|    fault_signal_unique_subgroup_base_count = (
#|        int(len(fault_signal_subgroup_summary[["site", "subgroup base"]].drop_duplicates()))
#|        if not fault_signal_subgroup_summary.empty
#|        else 0
#|    )
#|    fault_signal_unique_subgroup_cluster_count = (
#|        int(len(fault_signal_cluster_summary[["site", "subgroup cluster"]].drop_duplicates()))
#|        if not fault_signal_cluster_summary.empty
#|        else 0
#|    )
#|    fault_signal_top_subgroup_block = (
#|        markdown_table_from_df(fault_signal_subgroup_summary.head(10))
#|        if not fault_signal_subgroup_summary.empty
#|        else "_none_"
#|    )
#|    fault_signal_top_cluster_block = (
#|        markdown_table_from_df(fault_signal_cluster_summary.head(10))
#|        if not fault_signal_cluster_summary.empty
#|        else "_none_"
#|    )
#|    detailed_report_block = (
#|        f"- `fault_panel_result_detailed_report_v1.xlsx`: `{detailed_report_path}`\n\n"
#|        if detailed_report_path is not None
#|        else ""
#|    )
#|    precursor_report_block = (
#|        f"- `fault_panel_result_precursor_report_v1.csv`: `{precursor_report_path}`\n\n"
#|        if precursor_report_path is not None
#|        else ""
#|    )
#|    fault_signal_report_block = (
#|        f"- `{ROOT_FAULT_SIGNAL_REPORT_NAME}`: `{fault_signal_report_path}`\n\n"
#|        if fault_signal_report_path is not None
#|        else ""
#|    )
#|    return (
#|        "# fault_panel_result_master_report_v1\n\n"
#|        "## 목적\n"
#|        "frozen-support live chain과 raw-only algorithm candidate chain을 비교하고, 어떤 artifact를 어떤 순서로 읽을지 안내한다.\n\n"
#|        "## 실행 대상 site\n"
#|        f"{site_lines}\n\n"
#|        "## baseline 입력 비교\n"
#|        f"- `all_sites_match`: `{baseline_comparison.get('all_sites_match')}`\n"
#|        f"{baseline_block}\n\n"
#|        "## frozen-support live chain 요약\n"
#|        f"- `status_ko`: `{live_chain_result.get('status_ko')}`\n"
#|        f"- `fixed_fault_reference_exact_match`: `{live_compare.get('exact_match')}`\n"
#|        f"- `baseline_input_all_sites_match`: `{live_compare.get('baseline_input_all_sites_match')}`\n"
#|        f"- `diff_columns`: `{live_compare.get('diff_columns', [])}`\n\n"
#|        "## raw-only algorithm candidate chain 요약\n"
#|        f"- `status_ko`: `{raw_only_compare.get('status_ko')}`\n"
#|        f"- `reference_available`: `{raw_only_compare.get('reference_available')}`\n"
#|        f"- `overlap_decision_columns_match`: `{raw_only_compare.get('overlap_decision_columns_match')}`\n"
#|        f"- `reference_row_count`: `{raw_only_compare.get('reference_row_count')}`\n"
#|        f"- `candidate_row_count`: `{raw_only_compare.get('candidate_row_count')}`\n"
#|        f"- `published_current_row_count`: `{raw_only_chain_result.get('publish_meta', {}).get('published_current_row_count', '')}`\n"
#|        f"- `matched_row_key_count`: `{raw_only_compare.get('matched_row_key_count')}`\n"
#|        f"- `overlap_diff_columns`: `{raw_only_compare.get('overlap_diff_columns', [])}`\n\n"
#|        "## report split 요약\n"
#|        f"- `precursor_candidate_row_count`: `{len(precursor_report_df)}`\n"
#|        f"- `raw_only_fault_signal_row_count`: `{len(fault_signal_report_df)}`\n"
#|        f"- `raw_only_fault_signal_unique_group_root_count`: `{fault_signal_unique_group_root_count}`\n"
#|        f"- `raw_only_fault_signal_unique_subgroup_base_count`: `{fault_signal_unique_subgroup_base_count}`\n"
#|        f"- `raw_only_fault_signal_unique_subgroup_cluster_count`: `{fault_signal_unique_subgroup_cluster_count}`\n"
#|        f"- `report_row_overlap_count`: `{overlap_row_count}`\n\n"
#|        "## 먼저 보는 법\n"
#|        "- `fault_panel_result_current_*`: frozen-support live chain 기준의 공식 current 결과를 먼저 확인한다. current preview/current report가 있으면 그쪽이 공식 current 설명의 주 문서다.\n"
#|        "- `fault_panel_result_precursor_report_v1.csv`: 아직 고장 신호는 없지만 추적 가치가 있는 precursor candidate를 본다.\n"
#|        "- raw-only artifact는 operator 기본 읽기 순서가 아니라 아래 `analyst/support 추가 자료` 섹션에서 필요 시 확인한다.\n\n"
#|        "## 해석 가이드\n"
#|        "- 이 문서는 공식 current 설명 문서를 대체하지 않는 안내/fallback 문서다. current preview/current report가 있으면 그쪽을 먼저 읽는다.\n"
#|        "- `fault_panel_result_current_*`는 frozen-support live chain 기준 결과다.\n"
#|        "- `fault_panel_result_raw_only_current_*`는 raw-only candidate 중 strict current subset만 보여준다.\n"
#|        "- `fault_panel_result_precursor_report_v1.csv`는 고장 신호가 아직 없는 precursor candidate만 보여준다.\n"
#|        f"- `{ROOT_FAULT_SIGNAL_REPORT_NAME}`는 raw-only candidate 우주에서 고장 신호가 이미 관측된 panel만 모은 analyst/support 보조표다.\n"
#|        "- raw-only chain의 `커널로그_원인군_ko`는 기존 라벨 family가 아니라 algorithm-derived family 의미다.\n"
#|        "- preview 표의 `운영 판정`은 현재 신호 단계, `상위 해석 후보`는 가장 가까운 원인 후보를 뜻한다.\n"
#|        "- `급락 종결 관측`과 `점진 저하 누적`은 관측 축이고, `사건 종결 요약`은 확정 row에서만 채워지는 사건 요약이다.\n"
#|        "- `고장 기준일`은 확정 고장일만 뜻하는 칼럼이 아니라 판단 기준으로 삼은 날짜다.\n"
#|        "- `기존 알고리즘 source`의 `미검출`은 legacy source 태그가 없다는 뜻이다.\n"
#|        "- precursor report와 raw-only fault signal report는 row가 중복되지 않게 분리해 읽어야 한다.\n"
#|        "- raw-only fault signal report의 row 수는 `panel_id` 기준 count이고, 같은 `subgroup base` 아래 여러 panel이 함께 잡히면 여러 row로 보일 수 있다.\n"
#|        f"- `subgroup cluster`는 같은 subgroup base 안에서 `신호 기준일` 간격이 `{FAULT_SIGNAL_CLUSTER_GAP_DAYS}`일 이하인 row를 하나의 보조 cluster로 묶은 analyst/support 휴리스틱이다.\n"
#|        "- 운영자는 기본적으로 current -> precursor 순서로 읽고, raw-only artifact는 analyst/support 추가 자료가 필요할 때만 연다.\n"
#|        "- 전체 candidate universe는 `result/raw_only_chain/*`와 detailed report 안에 그대로 남는다.\n\n"
#|        "## 컬럼 읽는 법\n"
#|        "- precursor report의 `전조 축`은 EWS/AE/DTW/규칙징후 중 어떤 축이 전조로 묶였는지 보여준다.\n"
#|        "- precursor report의 `대표 전조 신호`는 전조 후보를 만든 누적 신호를 짧게 풀어쓴 요약이다.\n"
#|        "- precursor report의 `모니터링 권고`는 다음 수집 주기에 무엇을 먼저 확인할지 알려주는 운영 메모다.\n"
#|        "- precursor report의 `공통원인 위험`과 `권고 검토 레인`은 panel-local precursor로 읽기 전에 공통 외란 가능성을 얼마나 먼저 볼지 정리한 보조 값이다.\n"
#|        "- raw-only fault signal report의 `group root`는 넓은 family root, `subgroup base`는 common-cause 검토에 더 가까운 하위 묶음이다.\n"
#|        "- raw-only fault signal report의 `동일 subgroup row 수`는 같은 subgroup base 아래 함께 잡힌 panel row 수다.\n"
#|        "- raw-only fault signal report의 `subgroup cluster`와 `동일 cluster row 수`는 `사건 수`를 직접 뜻하지 않고, 같은 subgroup base 안에서 가까운 날짜 row를 묶어 읽기 쉽게 만든 보조 값이다.\n"
#|        "- raw-only fault signal report의 `확정 경로`는 주 경로 하나만 보여주고, `고장 신호 요약`은 일수와 보조 근거를 덧붙인다.\n"
#|        "- raw-only fault signal report의 `근접 공통원인`은 strict_trigger 기준 ±3일 안의 common-cause만 적고, warning-anchor 기준 common-cause는 audit 전용으로 남긴다.\n"
#|        "- raw-only fault signal report의 `현장 점검 권고`는 첫 현장 액션의 우선순위를 짧게 적은 값이다.\n\n"
#|        "## 주요 산출물\n"
#|        f"{primary_output_block}\n\n"
#|        "## analyst/support 추가 자료\n"
#|        f"{analyst_output_block}\n\n"
#|        "## 상세 리포트\n"
#|        f"{detailed_report_block}"
#|        "## 전조 리포트\n"
#|        f"{precursor_report_block}"
#|        "## raw-only 고장 신호 리포트\n"
#|        f"{fault_signal_report_block}"
#|        "## raw-only 고장 신호 subgroup base 요약 (앞 10행)\n"
#|        f"{fault_signal_top_subgroup_block}\n\n"
#|        "## raw-only 고장 신호 subgroup cluster 요약 (앞 10행)\n"
#|        f"{fault_signal_top_cluster_block}\n\n"
#|        "## current preview 표\n"
#|        f"{markdown_table_from_df(truncate_report_df(live_preview_df))}\n\n"
#|        "## precursor 후보 표 (앞 20행)\n"
#|        f"{markdown_table_from_df(truncate_report_df(precursor_report_df, limit=20))}\n\n"
#|        "## analyst/support 참고 메모\n"
#|        f"- `{ROOT_FAULT_SIGNAL_REPORT_NAME}`와 `fault_panel_result_raw_only_current_*`는 master report에서 경로만 안내하는 보조 artifact다.\n"
#|        "- raw-only preview/fault signal row는 operator 기본 읽기 흐름에 직접 전개하지 않는다.\n"
#|        f"- raw-only strict current preview row count: `{len(raw_only_preview_df)}`\n"
#|        f"- raw-only fault signal row count: `{len(fault_signal_report_df)}`\n"
#|    )
#|
#|
#|def panel_group_root(panel_id: object) -> str:
#|    text = normalize_text(panel_id)
#|    tokens = text.split(".")
#|    if len(tokens) >= 3:
#|        return ".".join(tokens[:-2])
#|    return text
#|
#|
#|def panel_subgroup_base(panel_id: object) -> str:
#|    text = normalize_text(panel_id)
#|    tokens = text.split(".")
#|    if len(tokens) >= 2:
#|        return ".".join(tokens[:-1])
#|    return text
#|
#|
#|def attach_fault_signal_cluster_columns(df: pd.DataFrame) -> pd.DataFrame:
#|    if df is None or df.empty:
#|        working = df.copy() if df is not None else pd.DataFrame()
#|        if "subgroup cluster" not in working.columns:
#|            working["subgroup cluster"] = pd.Series(dtype=object)
#|        if "동일 cluster row 수" not in working.columns:
#|            working["동일 cluster row 수"] = pd.Series(dtype=int)
#|        return working
#|
#|    working = df.copy()
#|    working["신호 기준일_dt"] = pd.to_datetime(working["신호 기준일"], errors="coerce")
#|    cluster_key_by_index: dict[int, str] = {}
#|    cluster_size_by_index: dict[int, int] = {}
#|
#|    for (_, subgroup_base), subgroup_rows in working.groupby(
#|        ["site", "subgroup base"], sort=False, dropna=False
#|    ):
#|        subgroup_rows = subgroup_rows.sort_values(
#|            ["신호 기준일_dt", "panel_id"], ascending=[True, True]
#|        ).copy()
#|        cluster_ids: list[int] = []
#|        cluster_id = 0
#|        prev_date = None
#|        for _, subgroup_row in subgroup_rows.iterrows():
#|            current_date = subgroup_row.get("신호 기준일_dt")
#|            if pd.isna(current_date):
#|                cluster_id += 1
#|            elif prev_date is None or (current_date - prev_date).days > FAULT_SIGNAL_CLUSTER_GAP_DAYS:
#|                cluster_id += 1
#|                prev_date = current_date
#|            else:
#|                prev_date = current_date
#|            cluster_ids.append(cluster_id)
#|        subgroup_rows["cluster_id"] = cluster_ids
#|
#|        cluster_meta = (
#|            subgroup_rows.groupby("cluster_id", dropna=False)
#|            .agg(
#|                cluster_rows=("panel_id", "size"),
#|                start_date=("신호 기준일_dt", "min"),
#|                end_date=("신호 기준일_dt", "max"),
#|            )
#|            .reset_index()
#|        )
#|        label_map: dict[int, str] = {}
#|        size_map: dict[int, int] = {}
#|        for cluster_row in cluster_meta.to_dict(orient="records"):
#|            cid = int(cluster_row["cluster_id"])
#|            start_date = cluster_row.get("start_date")
#|            end_date = cluster_row.get("end_date")
#|            if pd.notna(start_date) and pd.notna(end_date):
#|                start_text = pd.Timestamp(start_date).strftime("%Y-%m-%d")
#|                end_text = pd.Timestamp(end_date).strftime("%Y-%m-%d")
#|                if start_text == end_text:
#|                    label = f"{normalize_text(subgroup_base)} @ {start_text}"
#|                else:
#|                    label = f"{normalize_text(subgroup_base)} @ {start_text}~{end_text}"
#|            else:
#|                label = f"{normalize_text(subgroup_base)} @ undated#{cid}"
#|            label_map[cid] = label
#|            size_map[cid] = int(cluster_row.get("cluster_rows", 0) or 0)
#|
#|        subgroup_rows["subgroup cluster"] = subgroup_rows["cluster_id"].map(label_map)
#|        subgroup_rows["동일 cluster row 수"] = subgroup_rows["cluster_id"].map(size_map)
#|        cluster_key_by_index.update(subgroup_rows["subgroup cluster"].to_dict())
#|        cluster_size_by_index.update(subgroup_rows["동일 cluster row 수"].to_dict())
#|
#|    working["subgroup cluster"] = working.index.map(cluster_key_by_index.get)
#|    working["동일 cluster row 수"] = working.index.map(cluster_size_by_index.get)
#|    return working.drop(columns=["신호 기준일_dt"], errors="ignore")
#|
#|
#|def bool_count(df: pd.DataFrame, column: str) -> int:
#|    if column not in df.columns or df.empty:
#|        return 0
#|    return int(truthy_mask(df[column]).sum())
#|
#|
#|def unique_csv(series: pd.Series) -> str:
#|    values = sorted({normalize_text(value) for value in series if normalize_text(value)})
#|    return ",".join(values)
#|
#|
#|def load_gate_from_workspace(workspace_root: Path, site: str) -> pd.DataFrame:
#|    path = workspace_root / "data" / site / "out" / "ae_simple_local_precursor_gate_daily.csv"
#|    if not path.exists():
#|        raise SystemExit(f"missing workspace precursor gate output: {path}")
#|    df = pd.read_csv(path, low_memory=False)
#|    ensure_columns(df, ["panel_id", "date"], path.name)
#|    df["panel_id"] = df["panel_id"].astype(str)
#|    df["date"] = pd.to_datetime(df["date"], errors="coerce")
#|    return df
#|
#|
#|def report_attention_grade(evidence_row: dict[str, object]) -> str:
#|    final_days = int(evidence_row.get("final_days", 0) or 0)
#|    critical_days = int(evidence_row.get("critical_days", 0) or 0)
#|    critical_confirmed_days = int(evidence_row.get("critical_confirmed_days", 0) or 0)
#|    fault_like_days = int(evidence_row.get("fault_like_days", 0) or 0)
#|    ews_warning_days = int(evidence_row.get("ews_warning_days", 0) or 0)
#|    pre_alarm_days = int(evidence_row.get("pre_alarm_days", 0) or 0)
#|    pre_ews_days = int(evidence_row.get("pre_ews_days", 0) or 0)
#|    prefault_cond_ae_days = int(evidence_row.get("prefault_cond_ae_days", 0) or 0)
#|    prefault_cond_dtw_days = int(evidence_row.get("prefault_cond_dtw_days", 0) or 0)
#|    critical_sources = normalize_text(evidence_row.get("critical_sources_csv"))
#|
#|    if final_days > 0 or critical_days > 0 or critical_confirmed_days > 0:
#|        return "확정"
#|    if (
#|        "vdrop" in critical_sources
#|        or ews_warning_days >= 15
#|        or pre_alarm_days >= 10
#|        or pre_ews_days >= 50
#|        or prefault_cond_ae_days >= 120
#|        or prefault_cond_dtw_days >= 120
#|        or fault_like_days >= 2
#|    ):
#|        return "고위험 관찰"
#|    return "관찰"
#|
#|
#|def report_reason_text(evidence_row: dict[str, object]) -> str:
#|    grade = normalize_text(evidence_row.get("운영해석등급_ko"))
#|    top1 = normalize_text(evidence_row.get("1순위_의심원인_ko"))
#|    final_days = int(evidence_row.get("final_days", 0) or 0)
#|    critical_days = int(evidence_row.get("critical_days", 0) or 0)
#|    critical_confirmed_days = int(evidence_row.get("critical_confirmed_days", 0) or 0)
#|    ews_warning_days = int(evidence_row.get("ews_warning_days", 0) or 0)
#|    pre_ews_days = int(evidence_row.get("pre_ews_days", 0) or 0)
#|    prefault_B_effective_days = int(evidence_row.get("prefault_B_effective_days", 0) or 0)
#|    prefault_B_common_cause_overlap_days = int(evidence_row.get("prefault_B_common_cause_overlap_days", 0) or 0)
#|    prefault_cond_ae_days = int(evidence_row.get("prefault_cond_ae_days", 0) or 0)
#|    prefault_cond_dtw_days = int(evidence_row.get("prefault_cond_dtw_days", 0) or 0)
#|    critical_sources = normalize_text(evidence_row.get("critical_sources_csv"))
#|    subtypes = normalize_text(evidence_row.get("anom_subtypes_csv"))
#|    subgroup_candidate_count = int(evidence_row.get("subgroup_candidate_panel_count", 0) or 0)
#|
#|    if grade == "확정":
#|        signal_labels: list[str] = []
#|        if final_days > 0:
#|            signal_labels.append("최종 고장 신호")
#|        if critical_confirmed_days > 0:
#|            signal_labels.append("강한 고장 신호 확정")
#|        elif critical_days > 0:
#|            signal_labels.append("강한 고장 신호")
#|        if "vdrop" in critical_sources:
#|            signal_labels.append("vdrop 전기 신호")
#|        signal_summary = " / ".join(signal_labels) if signal_labels else "확정 신호"
#|        return f"{signal_summary}가 나타나 고장 신호가 뚜렷하게 포착됨"
#|
#|    reasons: list[str] = []
#|    if "degradation" in subtypes:
#|        reasons.append("degradation subtype 반복")
#|    if ews_warning_days > 0 or pre_ews_days > 0:
#|        reasons.append(f"EWS 전조 누적(ews={ews_warning_days}, pre_ews={pre_ews_days})")
#|    if prefault_B_effective_days > 0:
#|        reasons.append(f"Option B 유효 전조 누적({prefault_B_effective_days}일)")
#|    if prefault_cond_ae_days > 0 or prefault_cond_dtw_days > 0:
#|        reasons.append(
#|            f"AE/DTW 전조 조건 누적(ae={prefault_cond_ae_days}, dtw={prefault_cond_dtw_days})"
#|        )
#|    if prefault_B_common_cause_overlap_days > 0:
#|        reasons.append(f"공통원인 겹침 option B({prefault_B_common_cause_overlap_days}일)는 별도 분리")
#|    if subgroup_candidate_count >= 3:
#|        reasons.append(f"동일 subgroup 동시 흔들림({subgroup_candidate_count} panels)")
#|    if top1:
#|        reasons.append(f"가장 가까운 후보는 {top1}")
#|    if not reasons:
#|        reasons.append("약한 이상 신호만 있어 관찰 대상으로 해석")
#|    return " / ".join(reasons)
#|
#|
#|def report_precursor_axes_text(evidence_row: dict[str, object]) -> str:
#|    axes: list[str] = []
#|    ews_warning_days = int(evidence_row.get("ews_warning_days", 0) or 0)
#|    pre_alarm_days = int(evidence_row.get("pre_alarm_days", 0) or 0)
#|    pre_ews_days = int(evidence_row.get("pre_ews_days", 0) or 0)
#|    prefault_cond_ae_days = int(evidence_row.get("prefault_cond_ae_days", 0) or 0)
#|    prefault_cond_dtw_days = int(evidence_row.get("prefault_cond_dtw_days", 0) or 0)
#|    event_A_days = int(evidence_row.get("event_A_days", 0) or 0)
#|    fault_like_days = int(evidence_row.get("fault_like_days", 0) or 0)
#|    final_days = int(evidence_row.get("final_days", 0) or 0)
#|    critical_days = int(evidence_row.get("critical_days", 0) or 0)
#|    critical_sources = normalize_text(evidence_row.get("critical_sources_csv"))
#|    subtypes = normalize_text(evidence_row.get("anom_subtypes_csv"))
#|
#|    if ews_warning_days > 0 or pre_ews_days > 0:
#|        axes.append("EWS")
#|    if prefault_cond_ae_days > 0 or event_A_days > 0 or "degradation" in subtypes:
#|        axes.append("AE")
#|    if prefault_cond_dtw_days > 0:
#|        axes.append("DTW")
#|    if (
#|        pre_alarm_days > 0
#|        or fault_like_days > 0
#|        or final_days > 0
#|        or critical_days > 0
#|        or "vdrop" in critical_sources
#|    ):
#|        axes.append("규칙징후")
#|    return "+".join(axes)
#|
#|
#|def report_precursor_signal_text(evidence_row: dict[str, object]) -> str:
#|    signals: list[str] = []
#|    ews_warning_days = int(evidence_row.get("ews_warning_days", 0) or 0)
#|    pre_alarm_days = int(evidence_row.get("pre_alarm_days", 0) or 0)
#|    pre_ews_days = int(evidence_row.get("pre_ews_days", 0) or 0)
#|    prefault_B_effective_days = int(evidence_row.get("prefault_B_effective_days", 0) or 0)
#|    prefault_B_common_cause_overlap_days = int(evidence_row.get("prefault_B_common_cause_overlap_days", 0) or 0)
#|    prefault_cond_ae_days = int(evidence_row.get("prefault_cond_ae_days", 0) or 0)
#|    prefault_cond_dtw_days = int(evidence_row.get("prefault_cond_dtw_days", 0) or 0)
#|    critical_sources = normalize_text(evidence_row.get("critical_sources_csv"))
#|    subtypes = normalize_text(evidence_row.get("anom_subtypes_csv"))
#|
#|    if ews_warning_days > 0 or pre_ews_days > 0:
#|        signals.append(f"EWS 전조 누적(ews={ews_warning_days}, pre_ews={pre_ews_days})")
#|    if prefault_B_effective_days > 0:
#|        signals.append(f"Option B 유효 누적({prefault_B_effective_days}일)")
#|    if prefault_cond_ae_days > 0:
#|        signals.append(f"AE 전조 조건 누적({prefault_cond_ae_days}일)")
#|    if prefault_cond_dtw_days > 0:
#|        signals.append(f"DTW 전조 조건 누적({prefault_cond_dtw_days}일)")
#|    if pre_alarm_days > 0:
#|        signals.append(f"pre_alarm 누적({pre_alarm_days}일)")
#|    if "vdrop" in critical_sources:
#|        signals.append("상대 전압 이탈 징후")
#|    if "degradation" in subtypes:
#|        signals.append("degradation subtype 반복")
#|    if prefault_B_common_cause_overlap_days > 0:
#|        signals.append(f"공통원인 겹침 option B({prefault_B_common_cause_overlap_days}일)")
#|    return " / ".join(signals)
#|
#|
#|def precursor_common_cause_risk_text(evidence_row: dict[str, object]) -> str:
#|    prefault_B_common_cause_overlap_days = int(
#|        evidence_row.get("prefault_B_common_cause_overlap_days", 0) or 0
#|    )
#|    subgroup_candidate_count = int(evidence_row.get("subgroup_candidate_panel_count", 0) or 0)
#|    if prefault_B_common_cause_overlap_days > 0 and subgroup_candidate_count >= 3:
#|        return "높음"
#|    if prefault_B_common_cause_overlap_days > 0 or subgroup_candidate_count >= 3:
#|        return "중간"
#|    return "낮음"
#|
#|
#|def precursor_review_lane_text(evidence_row: dict[str, object]) -> str:
#|    risk = precursor_common_cause_risk_text(evidence_row)
#|    grade = normalize_text(evidence_row.get("운영해석등급_ko"))
#|    if risk == "높음":
#|        return "공통원인 검토"
#|    if risk == "중간":
#|        return "공통원인 우선 확인"
#|    if grade == "고위험 관찰":
#|        return "단일 패널 우선 추적"
#|    return "일반 모니터링"
#|
#|
#|def precursor_monitoring_action_text(evidence_row: dict[str, object]) -> str:
#|    grade = normalize_text(evidence_row.get("운영해석등급_ko"))
#|    top1 = normalize_text(evidence_row.get("1순위_의심원인_ko"))
#|    axes = report_precursor_axes_text(evidence_row)
#|    prefault_B_effective_days = int(evidence_row.get("prefault_B_effective_days", 0) or 0)
#|    prefault_B_common_cause_overlap_days = int(evidence_row.get("prefault_B_common_cause_overlap_days", 0) or 0)
#|    subgroup_candidate_count = int(evidence_row.get("subgroup_candidate_panel_count", 0) or 0)
#|    if prefault_B_common_cause_overlap_days > 0 and subgroup_candidate_count >= 3:
#|        return "site_event/group_off 및 동일 subgroup 동시 흔들림을 먼저 재확인"
#|    if prefault_B_common_cause_overlap_days > 0 and prefault_B_effective_days == 0:
#|        return "site_event/group_off 공통원인 여부를 먼저 재확인"
#|    if subgroup_candidate_count >= 3 and prefault_B_effective_days == 0:
#|        return "동일 subgroup 동시 흔들림과 공통 외란 여부를 먼저 재확인"
#|    if "오염" in top1:
#|        return "세척 전후 추세 비교와 추가 관찰 권고"
#|    if "음영" in top1:
#|        return "인접 음영 구조와 시간대별 반복 여부 재확인 권고"
#|    if "접촉" in top1 or "끊김" in top1:
#|        return "다음 수집 주기 재확인 후 접속부 점검 여부 판단"
#|    if grade == "고위험 관찰":
#|        return "가까운 주기 재확인과 현장 비교 점검 권고"
#|    if axes:
#|        return f"{axes} 축 모니터링 유지"
#|    return "지속 모니터링 유지"
#|
#|
#|def strict_trigger_common_cause_text(evidence_row: dict[str, object]) -> str:
#|    if bool(evidence_row.get("strict_trigger_proximal_common_cause_flag")):
#|        return "strict_trigger 근처 공통원인 흔들림 동반"
#|    return ""
#|
#|
#|def fault_signal_path_text(evidence_row: dict[str, object]) -> str:
#|    final_days = int(evidence_row.get("final_days", 0) or 0)
#|    critical_days = int(evidence_row.get("critical_days", 0) or 0)
#|    critical_confirmed_days = int(evidence_row.get("critical_confirmed_days", 0) or 0)
#|    critical_sources = normalize_text(evidence_row.get("critical_sources_csv"))
#|    if final_days > 0:
#|        return "최종 고장 신호 경로"
#|    if critical_confirmed_days > 0:
#|        return "강한 고장 신호 확정 경로"
#|    if critical_days > 0:
#|        return "vdrop 강신호 경로" if "vdrop" in critical_sources else "강한 고장 신호 경로"
#|    return "고장 신호 관측"
#|
#|
#|def fault_signal_summary_text(evidence_row: dict[str, object]) -> str:
#|    final_days = int(evidence_row.get("final_days", 0) or 0)
#|    critical_days = int(evidence_row.get("critical_days", 0) or 0)
#|    critical_confirmed_days = int(evidence_row.get("critical_confirmed_days", 0) or 0)
#|    critical_sources = normalize_text(evidence_row.get("critical_sources_csv"))
#|    parts: list[str] = []
#|    if final_days > 0:
#|        parts.append(f"최종 고장 신호 {final_days}일")
#|        if critical_confirmed_days > 0:
#|            parts.append("강한 고장 신호 확정이 함께 관측됨")
#|        elif critical_days > 0:
#|            parts.append("강한 고장 신호가 함께 관측됨")
#|    elif critical_confirmed_days > 0:
#|        parts.append(f"강한 고장 신호 확정 {critical_confirmed_days}일")
#|    elif critical_days > 0:
#|        parts.append(f"강한 고장 신호 {critical_days}일")
#|    if "vdrop" in critical_sources:
#|        parts.append("vdrop 전기 신호 동반")
#|    if bool(evidence_row.get("strict_trigger_proximal_common_cause_flag")):
#|        parts.append("strict_trigger 근처 공통원인 흔들림 동반")
#|    return " / ".join(parts) if parts else "고장 신호 관측"
#|
#|
#|def fault_signal_action_text(evidence_row: dict[str, object]) -> str:
#|    top1 = normalize_text(evidence_row.get("1순위_의심원인_ko"))
#|    if bool(evidence_row.get("strict_trigger_proximal_common_cause_flag")):
#|        return "패널 국소 고장 신호와 함께 strict_trigger 근처 공통원인 여부도 동시 확인"
#|    if "다이오드" in top1 or "국소 회로" in top1:
#|        return "현장 점검 후 다이오드·국소 회로 이상 여부 우선 확인"
#|    if "접촉" in top1 or "끊김" in top1 or "개방" in top1:
#|        return "배선·접속부 우선 점검"
#|    if "측정" in top1 or "응답" in top1:
#|        return "MLPE/계측값과 접속 상태 동시 점검"
#|    if "외부 전원" in top1:
#|        return "패널 국소 이상보다 외부 전원/공통 원인 먼저 확인"
#|    return "현장 점검과 최근 작업 이력 확인 권고"
#|
#|
#|def build_precursor_report_df(evidence_df: pd.DataFrame) -> pd.DataFrame:
#|    if evidence_df is None or evidence_df.empty:
#|        return pd.DataFrame(columns=PRECURSOR_REPORT_OUTPUT_COLS)
#|
#|    rows: list[dict[str, object]] = []
#|    for _, row in evidence_df.fillna("").iterrows():
#|        precursor_date = normalize_text(row.get("전조날짜"))
#|        evidence_row = row.to_dict()
#|        if not precursor_date or not has_precursor_signal(evidence_row) or has_hard_fault_evidence(evidence_row):
#|            continue
#|        rows.append(
#|            {
#|                "site": normalize_text(row.get("site")),
#|                "panel_id": normalize_text(row.get("panel_id")),
#|                "운영 판정": normalize_text(row.get("운영해석등급_ko")) or "전조 후보",
#|                "판정 근거": report_reason_text(evidence_row),
#|                "전조날짜": precursor_date,
#|                "전조 축": report_precursor_axes_text(evidence_row),
#|                "대표 전조 신호": report_precursor_signal_text(evidence_row),
#|                "전조 요약": normalize_text(row.get("근거요약_ko")),
#|                "상위 해석 후보": normalize_text(row.get("1순위_의심원인_ko")),
#|                "기존 알고리즘 source": display_existing_algorithm_source(
#|                    row.get("커널로그 기존 알고리즘")
#|                ),
#|                "패턴 설명": pattern_explainer(evidence_row, soften_hard_language=True),
#|                "모니터링 권고": precursor_monitoring_action_text(evidence_row),
#|                "공통원인 위험": precursor_common_cause_risk_text(evidence_row),
#|                "권고 검토 레인": precursor_review_lane_text(evidence_row),
#|                "EWS 전조 일수": int(row.get("ews_warning_days", 0) or 0),
#|                "pre_alarm 일수": int(row.get("pre_alarm_days", 0) or 0),
#|                "pre_ews 일수": int(row.get("pre_ews_days", 0) or 0),
#|                "Option B 유효 일수": int(row.get("prefault_B_effective_days", 0) or 0),
#|                "공통원인 겹침 일수": int(row.get("prefault_B_common_cause_overlap_days", 0) or 0),
#|                "AE 전조 조건 일수": int(row.get("prefault_cond_ae_days", 0) or 0),
#|                "DTW 전조 조건 일수": int(row.get("prefault_cond_dtw_days", 0) or 0),
#|            }
#|        )
#|    return (
#|        pd.DataFrame(rows)
#|        .reindex(columns=PRECURSOR_REPORT_OUTPUT_COLS)
#|        .sort_values(["site", "panel_id"], ascending=[True, True])
#|        .reset_index(drop=True)
#|    )
#|
#|
#|def build_fault_signal_report_df(evidence_df: pd.DataFrame) -> pd.DataFrame:
#|    if evidence_df is None or evidence_df.empty:
#|        return pd.DataFrame(columns=FAULT_SIGNAL_REPORT_OUTPUT_COLS)
#|
#|    rows: list[dict[str, object]] = []
#|    for _, row in evidence_df.fillna("").iterrows():
#|        evidence_row = row.to_dict()
#|        if not has_hard_fault_evidence(evidence_row):
#|            continue
#|        event_fields = event_display_fields(evidence_row)
#|        rows.append(
#|            {
#|                "site": normalize_text(row.get("site")),
#|                "group root": normalize_text(row.get("group_root")),
#|                "subgroup base": normalize_text(row.get("subgroup_base")),
#|                "panel_id": normalize_text(row.get("panel_id")),
#|                "동일 subgroup row 수": int(row.get("subgroup_candidate_panel_count", 0) or 0),
#|                "운영 판정": normalize_text(row.get("운영해석등급_ko")) or display_signal_grade(row),
#|                "확정 경로": fault_signal_path_text(evidence_row),
#|                "고장 신호 요약": fault_signal_summary_text(evidence_row),
#|                "전조 시작일": normalize_text(row.get("전조날짜")),
#|                "신호 기준일": normalize_text(row.get("고장날짜")),
#|                "사건유형": normalize_text(row.get("사건유형_ko")),
#|                "사건 종결 요약": event_fields.get("사건 종결 요약", ""),
#|                "근접 공통원인": strict_trigger_common_cause_text(evidence_row),
#|                "상위 해석 후보": normalize_text(row.get("1순위_의심원인_ko")),
#|                "기존 알고리즘 source": display_existing_algorithm_source(
#|                    row.get("커널로그 기존 알고리즘")
#|                ),
#|                "패턴 설명": pattern_explainer(evidence_row),
#|                "현장 점검 권고": fault_signal_action_text(evidence_row),
#|            }
#|        )
#|    working = pd.DataFrame(rows)
#|    working = attach_fault_signal_cluster_columns(working)
#|    working = (
#|        working.reindex(columns=FAULT_SIGNAL_REPORT_OUTPUT_COLS)
#|        .sort_values(["site", "subgroup base", "신호 기준일", "panel_id"], ascending=[True, True, True, True])
#|        .reset_index(drop=True)
#|    )
#|    if "동일 cluster row 수" in working.columns:
#|        working["동일 cluster row 수"] = working["동일 cluster row 수"].fillna(0).astype(int)
#|    return working
#|
#|
#|def nonempty_sheet_df(df: pd.DataFrame, note: str) -> pd.DataFrame:
#|    if not df.empty:
#|        return df
#|    return pd.DataFrame([{"note": note}])
#|
#|
#|def signal_label_text(record: dict[str, object]) -> str:
#|    labels: list[str] = []
#|    if bool(record.get("event_A")):
#|        labels.append("event_A")
#|    if bool(record.get("v_drop")):
#|        labels.append("v_drop")
#|    if bool(record.get("critical_fault")):
#|        labels.append("critical_fault")
#|    if bool(record.get("critical_suspect")):
#|        labels.append("critical_suspect")
#|    if bool(record.get("critical_confirmed")):
#|        labels.append("critical_confirmed")
#|    if bool(record.get("fault_like_day")):
#|        labels.append("fault_like")
#|    if bool(record.get("final_fault")):
#|        labels.append("final_fault")
#|    if bool(record.get("ews_warning")):
#|        labels.append("ews_warning")
#|    if bool(record.get("pre_alarm")):
#|        labels.append("pre_alarm")
#|    if bool(record.get("pre_ews")):
#|        labels.append("pre_ews")
#|    if bool(record.get("site_event_soft")):
#|        labels.append("site_event_soft")
#|    if bool(record.get("site_event_hard")):
#|        labels.append("site_event_hard")
#|    if bool(record.get("group_off_date")):
#|        labels.append("group_off")
#|    if bool(record.get("prefault_B")):
#|        labels.append("prefault_B")
#|    if bool(record.get("prefault_B_effective")):
#|        labels.append("prefault_B_effective")
#|    if bool(record.get("prefault_B_common_cause_overlap")):
#|        labels.append("prefault_B_common_cause_overlap")
#|    if bool(record.get("prefault_cond_mid")):
#|        labels.append("prefault_mid")
#|    if bool(record.get("prefault_cond_ae")):
#|        labels.append("prefault_ae")
#|    if bool(record.get("prefault_cond_dtw")):
#|        labels.append("prefault_dtw")
#|    if bool(record.get("prefault_cond_ews")):
#|        labels.append("prefault_ews")
#|    subtype = normalize_text(record.get("anom_subtype"))
#|    if subtype:
#|        labels.append(f"subtype:{subtype}")
#|    return ",".join(labels)
#|
#|
#|def auto_fit_workbook_columns(path: Path) -> None:
#|    try:
#|        from openpyxl import load_workbook
#|        from openpyxl.utils import get_column_letter
#|    except ModuleNotFoundError as exc:
#|        raise SystemExit(
#|            "openpyxl is required to generate fault_panel_result_detailed_report_v1.xlsx"
#|        ) from exc
#|
#|    workbook = load_workbook(path)
#|    for worksheet in workbook.worksheets:
#|        if worksheet.max_row >= 2:
#|            worksheet.freeze_panes = "A2"
#|            worksheet.auto_filter.ref = worksheet.dimensions
#|        for column_cells in worksheet.columns:
#|            column_letter = get_column_letter(column_cells[0].column)
#|            max_len = max(
#|                len(str(cell.value)) if cell.value is not None else 0
#|                for cell in column_cells
#|            )
#|            worksheet.column_dimensions[column_letter].width = min(max(max_len + 2, 10), 60)
#|    workbook.save(path)
#|
#|
#|def build_detailed_report_frames(
#|    output_root: Path,
#|    sites: list[str],
#|    baseline_comparison: dict[str, object],
#|    live_chain_result: dict[str, object],
#|    raw_only_chain_result: dict[str, object],
#|    live_preview_df: pd.DataFrame,
#|    raw_only_preview_df: pd.DataFrame,
#|) -> dict[str, pd.DataFrame]:
#|    overview_df = pd.DataFrame(
#|        [
#|            {"section": "sites", "key": "sites_csv", "value": ",".join(sites)},
#|            {
#|                "section": "baseline",
#|                "key": "all_sites_match",
#|                "value": str(baseline_comparison.get("all_sites_match")),
#|            },
#|            {
#|                "section": "live_chain",
#|                "key": "status_ko",
#|                "value": normalize_text(live_chain_result.get("status_ko")),
#|            },
#|            {
#|                "section": "live_chain",
#|                "key": "fixed_fault_reference_exact_match",
#|                "value": str(
#|                    live_chain_result.get("fixed_fault_reference_compare", {}).get("exact_match")
#|                ),
#|            },
#|            {
#|                "section": "raw_only_chain",
#|                "key": "status_ko",
#|                "value": normalize_text(raw_only_chain_result.get("status_ko")),
#|            },
#|            {
#|                "section": "raw_only_chain",
#|                "key": "compare_status_ko",
#|                "value": normalize_text(
#|                    raw_only_chain_result.get("fixed_fault_reference_compare", {}).get("status_ko")
#|                ),
#|            },
#|            {
#|                "section": "raw_only_chain",
#|                "key": "candidate_row_count",
#|                "value": str(
#|                    raw_only_chain_result.get("fixed_fault_reference_compare", {}).get(
#|                        "candidate_row_count"
#|                    )
#|                ),
#|            },
#|            {
#|                "section": "raw_only_chain",
#|                "key": "reference_row_count",
#|                "value": str(
#|                    raw_only_chain_result.get("fixed_fault_reference_compare", {}).get(
#|                        "reference_row_count"
#|                    )
#|                ),
#|            },
#|            {
#|                "section": "notes",
#|                "key": "attention_grade_note_ko",
#|                "value": (
#|                    "운영해석등급_ko는 상세 리포트용 보조 등급이다. core verdict를 바꾸지 않고 "
#|                    "확정/고위험 관찰/관찰을 사람이 읽기 쉽게 정리한다."
#|                ),
#|            },
#|        ]
#|    )
#|
#|    frames: dict[str, pd.DataFrame] = {
#|        "overview": overview_df,
#|        "current_preview": nonempty_sheet_df(
#|            live_preview_df.copy(),
#|            "live current preview not available",
#|        ),
#|        "raw_only_preview": nonempty_sheet_df(
#|            raw_only_preview_df.copy(),
#|            "raw-only preview not available",
#|        ),
#|    }
#|
#|    if not raw_only_chain_result.get("requested") or normalize_text(raw_only_chain_result.get("status_ko")) != "completed":
#|        frames["raw_only_evidence"] = pd.DataFrame(
#|            [{"note": "raw-only chain not completed; detailed evidence unavailable"}]
#|        )
#|        frames["raw_only_candidate_scores"] = pd.DataFrame(
#|            [{"note": "raw-only chain not completed; candidate score matrix unavailable"}]
#|        )
#|        frames["raw_only_timeline"] = pd.DataFrame(
#|            [{"note": "raw-only chain not completed; timeline unavailable"}]
#|        )
#|        frames["raw_only_daily_log"] = pd.DataFrame(
#|            [{"note": "raw-only chain not completed; all-date log unavailable"}]
#|        )
#|        frames["raw_only_cluster"] = pd.DataFrame(
#|            [{"note": "raw-only chain not completed; cluster summary unavailable"}]
#|        )
#|        frames["precursor_report"] = pd.DataFrame(columns=PRECURSOR_REPORT_OUTPUT_COLS)
#|        frames["fault_signal_report"] = pd.DataFrame(columns=FAULT_SIGNAL_REPORT_OUTPUT_COLS)
#|        frames["definitions"] = pd.DataFrame(
#|            [
#|                {
#|                    "항목": "확정",
#|                    "설명": "최종 고장 신호 또는 강한 고장 신호가 관측된 상태",
#|                },
#|                {
#|                    "항목": "고위험 관찰",
#|                    "설명": "즉시 확정에 쓰는 신호는 없지만 EWS/AE/DTW 전조가 강하게 누적",
#|                },
#|                {"항목": "관찰", "설명": "약한 이상 또는 간헐 이상으로 계속 관찰 필요"},
#|            ]
#|        )
#|        return frames
#|
#|    workspace_root = Path(str(raw_only_chain_result["workspace_root"]))
#|    raw_only_common = load_raw_only_common_module()
#|    runtime_heuristic = load_runtime_heuristic_module()
#|    audit_path = workspace_root / "_share" / raw_only_common.RUNTIME_AUDIT_OUTPUT_NAME
#|    heuristic_path = workspace_root / "_share" / raw_only_common.RUNTIME_HEURISTIC_OUTPUT_NAME
#|    verdict_path = workspace_root / "_share" / raw_only_common.RUNTIME_VERDICT_OUTPUT_NAME
#|    audit_df = pd.read_csv(audit_path, encoding="utf-8-sig", low_memory=False)
#|    heuristic_df = pd.read_csv(heuristic_path, encoding="utf-8-sig", low_memory=False)
#|    verdict_df = pd.read_csv(verdict_path, encoding="utf-8-sig", low_memory=False)
#|    audit_df["site"] = audit_df["site"].astype(str)
#|    audit_df["panel_id"] = audit_df["panel_id"].astype(str)
#|    heuristic_df["site"] = heuristic_df["site"].astype(str)
#|    heuristic_df["panel_id"] = heuristic_df["panel_id"].astype(str)
#|    verdict_df["site"] = verdict_df["site"].astype(str)
#|    verdict_df["panel_id"] = verdict_df["panel_id"].astype(str)
#|
#|    audit_lookup = {
#|        row_key(row["site"], row["panel_id"]): row for row in audit_df.to_dict(orient="records")
#|    }
#|    heuristic_lookup = {
#|        row_key(row["site"], row["panel_id"]): row for row in heuristic_df.to_dict(orient="records")
#|    }
#|    verdict_lookup = {
#|        row_key(row["site"], row["panel_id"]): row for row in verdict_df.to_dict(orient="records")
#|    }
#|
#|    per_site_core = {site: load_panel_day_core_from_workspace(workspace_root, site) for site in sites}
#|    per_site_gate = {site: load_gate_from_workspace(workspace_root, site) for site in sites}
#|    preview_with_group_keys = raw_only_preview_df.copy()
#|    if not preview_with_group_keys.empty:
#|        preview_with_group_keys["group_root"] = preview_with_group_keys["panel_id"].map(
#|            panel_group_root
#|        )
#|        preview_with_group_keys["subgroup_base"] = preview_with_group_keys["panel_id"].map(
#|            panel_subgroup_base
#|        )
#|    group_root_counts = (
#|        preview_with_group_keys.groupby(["site", "group_root"]).size().to_dict()
#|        if not preview_with_group_keys.empty
#|        else {}
#|    )
#|    subgroup_counts = (
#|        preview_with_group_keys.groupby(["site", "subgroup_base"]).size().to_dict()
#|        if not preview_with_group_keys.empty
#|        else {}
#|    )
#|
#|    evidence_rows: list[dict[str, object]] = []
#|    candidate_score_rows: list[dict[str, object]] = []
#|    timeline_rows: list[dict[str, object]] = []
#|    all_date_rows: list[dict[str, object]] = []
#|    for _, preview_row in raw_only_preview_df.iterrows():
#|        site = normalize_text(preview_row.get("site"))
#|        panel_id = normalize_text(preview_row.get("panel_id"))
#|        group_root = panel_group_root(panel_id)
#|        subgroup_base = panel_subgroup_base(panel_id)
#|        base = group_root
#|        key = row_key(site, panel_id)
#|        audit_row = audit_lookup.get(key, {})
#|        heuristic_row = heuristic_lookup.get(key, {})
#|        verdict_row = verdict_lookup.get(key, {})
#|        merged_for_scores = dict(verdict_row)
#|        merged_for_scores.update(audit_row)
#|        score_map, score_notes = runtime_heuristic.score_row(merged_for_scores)
#|        ranked_candidates = runtime_heuristic.choose_ranked_candidates(score_map)
#|        top_score = ranked_candidates[0][1] if ranked_candidates else 0
#|        panel_core = per_site_core[site].loc[per_site_core[site]["panel_id"].eq(panel_id)].copy()
#|        panel_gate = per_site_gate[site].loc[per_site_gate[site]["panel_id"].eq(panel_id)].copy()
#|        representative = representative_signal_row(panel_core)
#|
#|        evidence_row: dict[str, object] = {
#|            "site": site,
#|            "panel_id": panel_id,
#|            "base": group_root,
#|            "group_root": group_root,
#|            "subgroup_base": subgroup_base,
#|            "base_candidate_panel_count": int(group_root_counts.get((site, group_root), 0)),
#|            "subgroup_candidate_panel_count": int(subgroup_counts.get((site, subgroup_base), 0)),
#|            "패널고장여부_ko": normalize_text(preview_row.get("패널고장여부_ko")),
#|            "사건유형_ko": normalize_text(preview_row.get("사건유형_ko")),
#|            "최종고장양상_ko": normalize_text(preview_row.get("최종고장양상_ko")),
#|            "라벨된 fault": normalize_text(preview_row.get("라벨된 fault")),
#|            "1순위_의심원인_ko": normalize_text(preview_row.get("1순위_의심원인_ko")),
#|            "2순위_의심원인_ko": normalize_text(preview_row.get("2순위_의심원인_ko")),
#|            "3순위_의심원인_ko": normalize_text(preview_row.get("3순위_의심원인_ko")),
#|            "커널로그 기존 알고리즘": normalize_text(preview_row.get("커널로그 기존 알고리즘")),
#|            "final_days": bool_count(panel_core, "final_fault"),
#|            "critical_days": bool_count(panel_core, "critical_fault"),
#|            "fault_like_days": bool_count(panel_core, "fault_like_day"),
#|            "event_A_days": bool_count(panel_core, "event_A"),
#|            "ews_warning_days": bool_count(panel_gate, "ews_warning"),
#|            "pre_alarm_days": bool_count(panel_gate, "pre_alarm"),
#|            "pre_ews_days": bool_count(panel_gate, "pre_ews"),
#|            "critical_confirmed_days": bool_count(panel_core, "critical_confirmed"),
#|            "prefault_B_days": bool_count(panel_gate, "prefault_B"),
#|            "prefault_B_effective_days": bool_count(panel_gate, "prefault_B_effective"),
#|            "prefault_B_common_cause_overlap_days": bool_count(panel_gate, "prefault_B_common_cause_overlap"),
#|            "prefault_cond_mid_days": bool_count(panel_gate, "prefault_cond_mid"),
#|            "prefault_cond_ae_days": bool_count(panel_gate, "prefault_cond_ae"),
#|            "prefault_cond_dtw_days": bool_count(panel_gate, "prefault_cond_dtw"),
#|            "prefault_cond_ews_days": bool_count(panel_gate, "prefault_cond_ews"),
#|            "critical_sources_csv": unique_csv(panel_core.get("critical_source", pd.Series(dtype=object))),
#|            "anom_subtypes_csv": unique_csv(panel_core.get("anom_subtype", pd.Series(dtype=object))),
#|            "원인후보_top1_score": heuristic_row.get("원인후보_top1_score", ""),
#|            "원인후보_top2_score": heuristic_row.get("원인후보_top2_score", ""),
#|            "원인후보_top3_score": heuristic_row.get("원인후보_top3_score", ""),
#|            "원인후보_경합상태_ko": normalize_text(heuristic_row.get("원인후보_경합상태_ko")),
#|            "원인후보_공동상위후보_csv": normalize_text(heuristic_row.get("원인후보_공동상위후보_csv")),
#|            "원인후보_실증우선확인_ko": normalize_text(heuristic_row.get("원인후보_실증우선확인_ko")),
#|            "원인후보_신뢰도_ko": normalize_text(heuristic_row.get("원인후보_신뢰도_ko")),
#|            "원인후보_해석메모_ko": normalize_text(heuristic_row.get("원인후보_해석메모_ko")),
#|            "사건이력_ko": normalize_text(verdict_row.get("사건이력_ko")),
#|            "대표판정_ko": normalize_text(verdict_row.get("대표판정_ko")),
#|            "운영최초전조발견일": normalize_text(verdict_row.get("운영최초전조발견일")),
#|            "사건해석상전조시작일": normalize_text(verdict_row.get("사건해석상전조시작일")),
#|            "세부fault_기준일": normalize_text(verdict_row.get("세부fault_기준일")),
#|            "판정주의_ko": normalize_text(verdict_row.get("판정주의_ko")),
#|            "strict_trigger_proximal_common_cause_flag": int(
#|                audit_row.get("strict_trigger_proximal_common_cause_flag", 0) or 0
#|            ),
#|            "warning_proximal_common_cause_flag": int(
#|                audit_row.get("warning_proximal_common_cause_flag", 0) or 0
#|            ),
#|            "대표critical_source": normalize_text(representative.get("critical_source")),
#|            "대표anom_subtype": normalize_text(representative.get("anom_subtype")),
#|            "대표mid_ratio": representative.get("mid_ratio", ""),
#|            "대표mid_v_ratio": representative.get("mid_v_ratio", ""),
#|            "대표mid_i_ratio": representative.get("mid_i_ratio", ""),
#|            "대표recon_error": representative.get("recon_error", ""),
#|            "대표dtw_dist": representative.get("dtw_dist", ""),
#|            "대표hs_score": representative.get("hs_score", ""),
#|            "대표event_A": normalize_text(representative.get("event_A")),
#|            "대표critical_fault": normalize_text(representative.get("critical_fault")),
#|            "대표critical_confirmed": normalize_text(representative.get("critical_confirmed")),
#|            "대표final_fault": normalize_text(representative.get("final_fault")),
#|        }
#|        evidence_row["전조날짜"] = choose_display_precursor_date(
#|            event_type_ko=preview_row.get("사건유형_ko"),
#|            interpreted_onset_date=verdict_row.get("사건해석상전조시작일"),
#|            first_warning_date=audit_row.get("earliest_warning_date"),
#|        )
#|        evidence_row["고장날짜"] = choose_display_fault_date(
#|            fault_date=verdict_row.get("세부fault_기준일"),
#|            strict_trigger_date=audit_row.get("strict_trigger_date"),
#|            first_final_fault_date=audit_row.get("first_final_fault_date"),
#|        )
#|        evidence_row["운영해석등급_ko"] = report_attention_grade(evidence_row)
#|        evidence_row["근거요약_ko"] = report_reason_text(evidence_row)
#|        evidence_rows.append(evidence_row)
#|        for rank_idx, (candidate, score) in enumerate(ranked_candidates, start=1):
#|            candidate_score_rows.append(
#|                {
#|                    "site": site,
#|                    "panel_id": panel_id,
#|                    "base": base,
#|                    "운영해석등급_ko": evidence_row["운영해석등급_ko"],
#|                    "패널고장여부_ko": evidence_row["패널고장여부_ko"],
#|                    "사건유형_ko": evidence_row["사건유형_ko"],
#|                    "최종고장양상_ko": evidence_row["최종고장양상_ko"],
#|                    "라벨된 fault": evidence_row["라벨된 fault"],
#|                    "후보순위": rank_idx,
#|                    "후보canonical_ko": candidate,
#|                    "후보표시명_ko": display_heuristic_name(candidate),
#|                    "후보점수": score,
#|                    "top1_flag": rank_idx == 1,
#|                    "공동상위_flag": bool(score == top_score and top_score > 0),
#|                    "원인후보_경합상태_ko": normalize_text(heuristic_row.get("원인후보_경합상태_ko")),
#|                    "원인후보_신뢰도_ko": normalize_text(heuristic_row.get("원인후보_신뢰도_ko")),
#|                    "커널로그 기존 알고리즘": evidence_row["커널로그 기존 알고리즘"],
#|                    "critical_sources_csv": evidence_row["critical_sources_csv"],
#|                    "anom_subtypes_csv": evidence_row["anom_subtypes_csv"],
#|                    "점수근거메모_ko": ", ".join(score_notes),
#|                    "후보해석메모_ko": normalize_text(heuristic_row.get("원인후보_해석메모_ko")),
#|                }
#|            )
#|
#|        core_cols = [
#|            "date",
#|            "recon_error",
#|            "dtw_dist",
#|            "hs_score",
#|            "mid_ratio",
#|            "mid_peer",
#|            "mid_v_ratio",
#|            "mid_i_ratio",
#|            "last_ratio",
#|            "last_peer",
#|            "event_A",
#|            "v_drop",
#|            "critical_fault",
#|            "critical_suspect",
#|            "critical_confirmed",
#|            "group_off_like",
#|            "fault_like_day",
#|            "final_fault",
#|            "critical_source",
#|            "anom_level",
#|            "anom_subtype",
#|        ]
#|        gate_cols = [
#|            "date",
#|            "ews_warning",
#|            "pre_alarm",
#|            "pre_ews",
#|            "site_event_soft",
#|            "site_event_hard",
#|            "group_off_date",
#|            "prefault_B",
#|            "prefault_B_effective",
#|            "prefault_B_common_cause_overlap",
#|            "prefault_cond_mid",
#|            "prefault_cond_ae",
#|            "prefault_cond_dtw",
#|            "prefault_cond_ews",
#|        ]
#|        merged = panel_core.loc[:, [c for c in core_cols if c in panel_core.columns]].merge(
#|            panel_gate.loc[:, [c for c in gate_cols if c in panel_gate.columns]],
#|            on="date",
#|            how="outer",
#|        )
#|        signal_cols = [
#|            "event_A",
#|            "critical_fault",
#|            "critical_suspect",
#|            "critical_confirmed",
#|            "group_off_like",
#|            "fault_like_day",
#|            "final_fault",
#|            "ews_warning",
#|            "pre_alarm",
#|            "pre_ews",
#|            "site_event_soft",
#|            "site_event_hard",
#|            "group_off_date",
#|            "prefault_B",
#|            "prefault_B_effective",
#|            "prefault_B_common_cause_overlap",
#|            "prefault_cond_mid",
#|            "prefault_cond_ae",
#|            "prefault_cond_dtw",
#|            "prefault_cond_ews",
#|        ]
#|        available_signal_cols = [column for column in signal_cols if column in merged.columns]
#|        signal_mask = merged[available_signal_cols].fillna(False).astype(bool).any(axis=1)
#|        subtype_mask = merged.get("anom_subtype", pd.Series(dtype=object)).astype(str).str.contains(
#|            "degradation|fault_like|shadow_like|critical",
#|            case=False,
#|            na=False,
#|        )
#|        merged = merged.sort_values("date").reset_index(drop=True)
#|        merged["신호있는날_flag"] = (signal_mask | subtype_mask).reset_index(drop=True)
#|        for record in merged.to_dict(orient="records"):
#|            all_date_rows.append(
#|                {
#|                    "site": site,
#|                    "panel_id": panel_id,
#|                    "base": base,
#|                    "운영해석등급_ko": evidence_row["운영해석등급_ko"],
#|                    "1순위_의심원인_ko": evidence_row["1순위_의심원인_ko"],
#|                    "date": pd.to_datetime(record.get("date"), errors="coerce"),
#|                    "신호있는날_flag": bool(record.get("신호있는날_flag")),
#|                    "관찰포인트_csv": signal_label_text(record),
#|                    "recon_error": record.get("recon_error"),
#|                    "dtw_dist": record.get("dtw_dist"),
#|                    "hs_score": record.get("hs_score"),
#|                    "mid_ratio": record.get("mid_ratio"),
#|                    "mid_peer": record.get("mid_peer"),
#|                    "mid_v_ratio": record.get("mid_v_ratio"),
#|                    "mid_i_ratio": record.get("mid_i_ratio"),
#|                    "last_ratio": record.get("last_ratio"),
#|                    "last_peer": record.get("last_peer"),
#|                    "event_A": record.get("event_A"),
#|                    "v_drop": record.get("v_drop"),
#|                    "critical_fault": record.get("critical_fault"),
#|                    "critical_suspect": record.get("critical_suspect"),
#|                    "critical_confirmed": record.get("critical_confirmed"),
#|                    "fault_like_day": record.get("fault_like_day"),
#|                    "final_fault": record.get("final_fault"),
#|                    "ews_warning": record.get("ews_warning"),
#|                    "pre_alarm": record.get("pre_alarm"),
#|                    "pre_ews": record.get("pre_ews"),
#|                    "site_event_soft": record.get("site_event_soft"),
#|                    "site_event_hard": record.get("site_event_hard"),
#|                    "group_off_date": record.get("group_off_date"),
#|                    "prefault_B": record.get("prefault_B"),
#|                    "prefault_B_effective": record.get("prefault_B_effective"),
#|                    "prefault_B_common_cause_overlap": record.get("prefault_B_common_cause_overlap"),
#|                    "prefault_cond_mid": record.get("prefault_cond_mid"),
#|                    "prefault_cond_ae": record.get("prefault_cond_ae"),
#|                    "prefault_cond_dtw": record.get("prefault_cond_dtw"),
#|                    "prefault_cond_ews": record.get("prefault_cond_ews"),
#|                    "critical_source": normalize_text(record.get("critical_source")),
#|                    "anom_level": normalize_text(record.get("anom_level")),
#|                    "anom_subtype": normalize_text(record.get("anom_subtype")),
#|                }
#|            )
#|        for record in merged.loc[merged["신호있는날_flag"]].to_dict(orient="records"):
#|            timeline_rows.append(
#|                {
#|                    "site": site,
#|                    "panel_id": panel_id,
#|                    "base": base,
#|                    "운영해석등급_ko": evidence_row["운영해석등급_ko"],
#|                    "1순위_의심원인_ko": evidence_row["1순위_의심원인_ko"],
#|                    "date": pd.to_datetime(record.get("date"), errors="coerce"),
#|                    "recon_error": record.get("recon_error"),
#|                    "dtw_dist": record.get("dtw_dist"),
#|                    "hs_score": record.get("hs_score"),
#|                    "mid_ratio": record.get("mid_ratio"),
#|                    "mid_peer": record.get("mid_peer"),
#|                    "mid_v_ratio": record.get("mid_v_ratio"),
#|                    "mid_i_ratio": record.get("mid_i_ratio"),
#|                    "last_ratio": record.get("last_ratio"),
#|                    "last_peer": record.get("last_peer"),
#|                    "event_A": record.get("event_A"),
#|                    "v_drop": record.get("v_drop"),
#|                    "critical_fault": record.get("critical_fault"),
#|                    "critical_suspect": record.get("critical_suspect"),
#|                    "critical_confirmed": record.get("critical_confirmed"),
#|                    "fault_like_day": record.get("fault_like_day"),
#|                    "final_fault": record.get("final_fault"),
#|                    "ews_warning": record.get("ews_warning"),
#|                    "pre_alarm": record.get("pre_alarm"),
#|                    "pre_ews": record.get("pre_ews"),
#|                    "site_event_soft": record.get("site_event_soft"),
#|                    "site_event_hard": record.get("site_event_hard"),
#|                    "group_off_date": record.get("group_off_date"),
#|                    "prefault_B": record.get("prefault_B"),
#|                    "prefault_B_effective": record.get("prefault_B_effective"),
#|                    "prefault_B_common_cause_overlap": record.get("prefault_B_common_cause_overlap"),
#|                    "prefault_cond_mid": record.get("prefault_cond_mid"),
#|                    "prefault_cond_ae": record.get("prefault_cond_ae"),
#|                    "prefault_cond_dtw": record.get("prefault_cond_dtw"),
#|                    "prefault_cond_ews": record.get("prefault_cond_ews"),
#|                    "critical_source": normalize_text(record.get("critical_source")),
#|                    "anom_level": normalize_text(record.get("anom_level")),
#|                    "anom_subtype": normalize_text(record.get("anom_subtype")),
#|                }
#|            )
#|
#|    evidence_df = pd.DataFrame(evidence_rows).sort_values(["site", "base", "panel_id"]).reset_index(drop=True)
#|    cluster_df = (
#|        evidence_df.groupby(["site", "base"], dropna=False)
#|        .agg(
#|            candidate_panels=("panel_id", "nunique"),
#|            확정_panel_count=("운영해석등급_ko", lambda s: int((s == "확정").sum())),
#|            고위험관찰_panel_count=("운영해석등급_ko", lambda s: int((s == "고위험 관찰").sum())),
#|            관찰_panel_count=("운영해석등급_ko", lambda s: int((s == "관찰").sum())),
#|            final_days_total=("final_days", "sum"),
#|            critical_days_total=("critical_days", "sum"),
#|            fault_like_days_total=("fault_like_days", "sum"),
#|            event_A_days_total=("event_A_days", "sum"),
#|            ews_warning_total=("ews_warning_days", "sum"),
#|            pre_ews_total=("pre_ews_days", "sum"),
#|            top1_candidates_csv=("1순위_의심원인_ko", lambda s: ",".join(sorted({normalize_text(v) for v in s if normalize_text(v)}))),
#|            labeled_fault_csv=("라벨된 fault", lambda s: ",".join(sorted({normalize_text(v) for v in s if normalize_text(v)}))),
#|        )
#|        .reset_index()
#|    )
#|    if not cluster_df.empty:
#|        cluster_df["군집해석_ko"] = cluster_df.apply(
#|            lambda row: (
#|                "군집 내 hard fault 포함"
#|                if int(row["확정_panel_count"]) > 0
#|                else "여러 패널이 함께 흔들려 공통 원인 가능성"
#|                if int(row["candidate_panels"]) >= 3
#|                else "소수 패널 관찰"
#|            ),
#|            axis=1,
#|        )
#|
#|    heuristic_definition_rows = [
#|        {
#|            "항목": "1/2/3순위_의심원인_ko",
#|            "설명": "한국어 표시용 heuristic candidate 라벨이며, internal code를 대신하지 않는다. 라벨은 엔지니어 친화적으로 유지하고 쉬운 설명은 definitions에서 별도로 붙인다",
#|        },
#|        *[
#|            {
#|                "항목": display_name,
#|                "설명": display_heuristic_note(display_name),
#|            }
#|            for display_name in DISPLAY_HEURISTIC_NAME_MAP.values()
#|        ],
#|    ]
#|
#|    definitions_df = pd.DataFrame(
#|        [
#|            {
#|                "항목": "definitions 시트",
#|                "설명": "상세 리포트 안에서 artifact 역할과 주요 컬럼 뜻을 짧게 설명하는 analyst/support glossary로, 읽기 순서나 auto-open 정책을 대신하지 않는다",
#|            },
#|            {
#|                "항목": "detailed report",
#|                "설명": "여러 row universe와 lineage를 함께 담는 analyst primary 문서로, current/master report를 대체하지 않는다",
#|            },
#|            {
#|                "항목": "official current",
#|                "설명": "frozen-support live chain 기준의 운영 공식 결과 묶음으로, detailed definitions에서는 역할과 공식성 차이만 짧게 설명한다",
#|            },
#|            {
#|                "항목": "raw_only current",
#|                "설명": "raw-only candidate 우주에서 strict current subset만 따로 보여주는 analyst/support 추가 자료로, official current를 대체하지 않는다",
#|            },
#|            {
#|                "항목": "운영해석등급_ko",
#|                "설명": "상세 리포트용 보조 등급으로 core verdict를 바꾸지 않고 사람이 읽기 쉽게 정리한 값",
#|            },
#|            {
#|                "항목": "확정",
#|                "설명": "최종 고장 신호 또는 강한 고장 신호가 존재하는 패널",
#|            },
#|            {
#|                "항목": "고위험 관찰",
#|                "설명": "즉시 확정에 쓰는 신호는 없지만 EWS, prefault_cond_ae/dtw/ews, fault_like 누적이 강한 패널",
#|            },
#|            {
#|                "항목": "관찰",
#|                "설명": "약한 이상 또는 간헐 이상으로 추가 추적이 필요한 패널",
#|            },
#|            {
#|                "항목": "precursor_report",
#|                "설명": "고장 신호가 아직 없는 precursor candidate만 따로 정리한 watchlist 성격의 보조표로, current artifact를 대체하지 않는다",
#|            },
#|            {
#|                "항목": "fault_signal_report",
#|                "설명": "raw-only candidate 우주에서 고장 신호가 이미 관측된 패널만 따로 정리한 analyst/support 보조표로, operator 기본 읽기 순서에는 직접 포함되지 않는다",
#|            },
#|            {
#|                "항목": "전조 축",
#|                "설명": "EWS/AE/DTW/규칙징후 중 어떤 축이 precursor candidate를 만들었는지 보여주는 묶음",
#|            },
#|            {
#|                "항목": "규칙징후",
#|                "설명": "pre_alarm, fault_like, 상대 전압 이탈 같은 규칙 기반 이상 징후를 완곡하게 묶은 표현",
#|            },
#|            {
#|                "항목": "Option B 유효 일수",
#|                "설명": "prefault_B 중 site_event/group_off 공통원인 겹침을 제외하고 실제 precursor 승격 설명에 반영한 일수",
#|            },
#|            {
#|                "항목": "공통원인 겹침 일수",
#|                "설명": "prefault_B가 켜졌지만 site_event/group_off와 직접 겹쳐 operator-facing precursor 승격에서는 별도 분리한 일수",
#|            },
#|            {
#|                "항목": "대표 전조 신호",
#|                "설명": "전조 표에서 누적된 핵심 신호를 짧게 요약한 값",
#|            },
#|            {
#|                "항목": "모니터링 권고",
#|                "설명": "precursor candidate에 대해 다음 수집 주기에서 무엇을 먼저 볼지 안내하는 운영 메모",
#|            },
#|            {
#|                "항목": "공통원인 위험",
#|                "설명": "site_event/group_off 겹침과 동일 subgroup 동시 흔들림을 바탕으로 panel-local precursor 해석을 얼마나 보수적으로 볼지 적은 보조 라벨",
#|            },
#|            {
#|                "항목": "권고 검토 레인",
#|                "설명": "일반 모니터링, 단일 패널 우선 추적, 공통원인 검토 중 다음 확인 방향을 짧게 정리한 값",
#|            },
#|            {
#|                "항목": "근접 공통원인",
#|                "설명": "raw-only 고장 신호 표에서 strict_trigger 기준 ±3일 안에 common-cause 이력이 같이 있으면 채우는 analyst/support 보조 값",
#|            },
#|            {
#|                "항목": "group root",
#|                "설명": "panel_id에서 마지막 두 서브인덱스를 제외한 넓은 family root로, 같은 상위 군집인지 보기 위한 값",
#|            },
#|            {
#|                "항목": "subgroup base",
#|                "설명": "panel_id에서 마지막 서브인덱스 하나만 제외한 하위 묶음으로, runtime common-cause 검토 단위에 더 가까운 값",
#|            },
#|            {
#|                "항목": "동일 subgroup row 수",
#|                "설명": "같은 raw-only current/fault-signal 우주에서 동일 subgroup base 아래 함께 잡힌 panel row 수로, row 수와 독립 사건 수를 혼동하지 않도록 돕는 값",
#|            },
#|            {
#|                "항목": "subgroup cluster",
#|                "설명": f"같은 subgroup base 안에서 신호 기준일 간격이 {FAULT_SIGNAL_CLUSTER_GAP_DAYS}일 이하인 row를 하나의 보조 cluster로 묶어 읽기 쉽게 만든 값",
#|            },
#|            {
#|                "항목": "동일 cluster row 수",
#|                "설명": "같은 subgroup cluster 안에 함께 들어간 panel row 수로, 대략적인 사건 뭉치를 읽기 쉽게 보조하는 값",
#|            },
#|            {
#|                "항목": "확정 경로",
#|                "설명": "raw-only 고장 신호 표에서 주된 고장 신호 경로 하나만 표시한 값",
#|            },
#|            {
#|                "항목": "고장 신호 요약",
#|                "설명": "고장 신호 지속 일수와 vdrop 같은 보조 근거를 함께 적은 요약",
#|            },
#|            {
#|                "항목": "현장 점검 권고",
#|                "설명": "raw-only 고장 신호 표에서 첫 현장 액션 우선순위를 짧게 적은 값",
#|            },
#|            {
#|                "항목": "strict_trigger_proximal_common_cause_flag",
#|                "설명": "raw-only audit에서 strict_trigger 기준 ±3일 안의 common-cause 이력을 잡는 내부 analyst flag",
#|            },
#|            {
#|                "항목": "warning_proximal_common_cause_flag",
#|                "설명": "raw-only audit에서 earliest_warning 기준 ±3일 안의 common-cause 이력을 잡는 내부 analyst flag로, 현재는 audit 전용",
#|            },
#|            {
#|                "항목": "raw_only_chain 주의",
#|                "설명": "raw-only candidate chain은 current/frozen 공식 결과보다 넓은 후보 우주를 보여주며, official current를 대체하지 않는다",
#|            },
#|            *heuristic_definition_rows,
#|        ]
#|    )
#|
#|    frames["raw_only_evidence"] = nonempty_sheet_df(
#|        evidence_df,
#|        "raw-only evidence rows unavailable",
#|    )
#|    frames["raw_only_candidate_scores"] = nonempty_sheet_df(
#|        pd.DataFrame(candidate_score_rows).sort_values(["site", "base", "panel_id", "후보순위"]).reset_index(drop=True),
#|        "raw-only candidate score matrix unavailable",
#|    )
#|    frames["raw_only_timeline"] = nonempty_sheet_df(
#|        pd.DataFrame(timeline_rows).sort_values(["site", "panel_id", "date"]).reset_index(drop=True),
#|        "raw-only timeline rows unavailable",
#|    )
#|    frames["raw_only_daily_log"] = nonempty_sheet_df(
#|        pd.DataFrame(all_date_rows).sort_values(["site", "panel_id", "date"]).reset_index(drop=True),
#|        "raw-only all-date log unavailable",
#|    )
#|    frames["raw_only_cluster"] = nonempty_sheet_df(
#|        cluster_df,
#|        "raw-only cluster summary unavailable",
#|    )
#|    frames["precursor_report"] = build_precursor_report_df(evidence_df)
#|    frames["fault_signal_report"] = build_fault_signal_report_df(evidence_df)
#|    frames["definitions"] = definitions_df
#|    return frames
#|
#|
#|def write_detailed_report_xlsx(path: Path, frames: dict[str, pd.DataFrame]) -> None:
#|    path.parent.mkdir(parents=True, exist_ok=True)
#|    with pd.ExcelWriter(path, engine="openpyxl") as writer:
#|        for sheet_name, df in frames.items():
#|            df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
#|    auto_fit_workbook_columns(path)
#|
#|
#|def stage_live_chain_workspace(output_root: Path, sites: list[str]) -> Path:
#|    workspace_root = output_root / "live_chain_workspace"
#|    if workspace_root.exists():
#|        shutil.rmtree(workspace_root)
#|    copy_tree(packaged_share_root(), workspace_root / "_share")
#|    for site in sites:
#|        copy_tree(output_root / "sites" / site / "output", workspace_root / "data" / site / "out")
#|    return workspace_root
#|
#|
#|def stage_raw_only_chain_workspace(output_root: Path, sites: list[str]) -> Path:
#|    workspace_root = output_root / "raw_only_chain_workspace"
#|    if workspace_root.exists():
#|        shutil.rmtree(workspace_root)
#|    for site in sites:
#|        copy_tree(output_root / "sites" / site / "output", workspace_root / "data" / site / "out")
#|    return workspace_root
#|
#|
#|def run_live_chain(output_root: Path, sites: list[str], baseline_comparison: dict[str, object]) -> dict[str, object]:
#|    support = packaged_live_chain_support()
#|    result_dir = output_root / "result" / "live_chain"
#|    result_dir.mkdir(parents=True, exist_ok=True)
#|    payload: dict[str, object] = {
#|        "requested": True,
#|        "supported": bool(support["supported"]),
#|        "support": support,
#|        "workspace_root": "",
#|        "result_dir": str(result_dir),
#|        "status_ko": "",
#|        "generated_outputs": {},
#|        "fixed_fault_reference_compare": {},
#|        "note_ko": (
#|            "live chain은 package 내부의 bootstrap verdict -> fault_event_audit -> final verdict -> gpvs evidence -> heuristic "
#|            "경로를 workspace-only로 수행한다."
#|        ),
#|    }
#|    if not support["supported"]:
#|        payload["status_ko"] = "packaged live chain assets missing"
#|        return payload
#|    if sorted(sites) != sorted(DEFAULT_SITES):
#|        payload["status_ko"] = "current live chain supports baseline tri-site universe only"
#|        return payload
#|
#|    workspace_root = stage_live_chain_workspace(output_root, sites)
#|    payload["workspace_root"] = str(workspace_root)
#|    commands = [
#|        [sys.executable, str(packaged_script_path("build_panel_day_engine_bootstrap_verdict_v1.py")), "--root", str(workspace_root), "--write-panel-verdict-alias"],
#|        [sys.executable, str(packaged_script_path("build_panel_day_engine_fault_panel_event_audit_v1.py")), "--root", str(workspace_root)],
#|        [sys.executable, str(packaged_script_path("build_panel_day_engine_panel_multiaxis_verdict_v1.py")), "--root", str(workspace_root)],
#|        [sys.executable, str(packaged_script_path("build_panel_day_engine_gpvs_evidence_pack_v1.py")), "--root", str(workspace_root)],
#|        [sys.executable, str(packaged_script_path("build_panel_day_engine_cause_candidate_heuristics_v1.py")), "--root", str(workspace_root)],
#|    ]
#|    for cmd in commands:
#|        subprocess.run(cmd, cwd=package_root(), check=True)
#|
#|    live_fault_df = build_live_fault_table(workspace_root)
#|    live_preview_df = build_live_fault_preview(workspace_root, live_fault_df)
#|    live_fault_path = result_dir / "fault_panel_result_live_v1.csv"
#|    live_preview_path = result_dir / "fault_panel_result_live_preview_v1.csv"
#|    live_fault_df.to_csv(live_fault_path, index=False, encoding="utf-8-sig")
#|    live_preview_df.to_csv(live_preview_path, index=False, encoding="utf-8-sig")
#|
#|    generated = {
#|        "bootstrap_verdict": str(workspace_root / "_share" / "panel_day_engine_bootstrap_verdict_v1.csv"),
#|        "fault_event_audit": str(workspace_root / "_share" / "panel_day_engine_fault_panel_event_audit_v1.csv"),
#|        "final_verdict": str(workspace_root / "_share" / "panel_day_engine_panel_multiaxis_verdict_v1.csv"),
#|        "gpvs_evidence": str(workspace_root / "_share" / "panel_day_engine_gpvs_evidence_pack_v1.csv"),
#|        "heuristic": str(workspace_root / "_share" / "panel_day_engine_cause_candidate_heuristics_v1.csv"),
#|        "fault_panel_result_live_v1": str(live_fault_path),
#|        "fault_panel_result_live_preview_v1": str(live_preview_path),
#|    }
#|    for name, source in [
#|        ("panel_day_engine_bootstrap_verdict_v1.csv", workspace_root / "_share" / "panel_day_engine_bootstrap_verdict_v1.csv"),
#|        ("panel_day_engine_fault_panel_event_audit_v1.csv", workspace_root / "_share" / "panel_day_engine_fault_panel_event_audit_v1.csv"),
#|        ("panel_day_engine_panel_multiaxis_verdict_v1.csv", workspace_root / "_share" / "panel_day_engine_panel_multiaxis_verdict_v1.csv"),
#|        ("panel_day_engine_gpvs_evidence_pack_v1.csv", workspace_root / "_share" / "panel_day_engine_gpvs_evidence_pack_v1.csv"),
#|        ("panel_day_engine_cause_candidate_heuristics_v1.csv", workspace_root / "_share" / "panel_day_engine_cause_candidate_heuristics_v1.csv"),
#|    ]:
#|        target = result_dir / name
#|        shutil.copy2(source, target)
#|        generated[name] = str(target)
#|
#|    compare = compare_live_fault_to_fixed(live_fault_df)
#|    compare["baseline_input_all_sites_match"] = bool(baseline_comparison.get("all_sites_match", False))
#|    payload["generated_outputs"] = generated
#|    payload["fixed_fault_reference_compare"] = compare
#|    payload["status_ko"] = "completed"
#|    summary_path = result_dir / "live_chain_summary_v1.json"
#|    write_json(summary_path, payload)
#|    payload["summary_path"] = str(summary_path)
#|    payload["published_outputs"] = publish_live_chain_outputs(output_root, result_dir, summary_path)
#|    write_json(summary_path, payload)
#|    root_summary_path = output_root / "result" / ROOT_LIVE_SUMMARY_NAME
#|    shutil.copy2(summary_path, root_summary_path)
#|    payload["published_outputs"][ROOT_LIVE_SUMMARY_NAME] = str(root_summary_path)
#|    root_report_path = output_root / "result" / ROOT_LIVE_REPORT_NAME
#|    write_text(
#|        root_report_path,
#|        build_live_report_markdown(
#|            sites=sites,
#|            baseline_comparison=baseline_comparison,
#|            compare=compare,
#|            published_outputs=payload["published_outputs"],
#|            live_preview_df=live_preview_df,
#|        ),
#|    )
#|    payload["published_outputs"][ROOT_LIVE_REPORT_NAME] = str(root_report_path)
#|    write_json(summary_path, payload)
#|    shutil.copy2(summary_path, root_summary_path)
#|    return payload
#|
#|
#|def run_raw_only_chain(output_root: Path, sites: list[str]) -> dict[str, object]:
#|    support = packaged_raw_only_chain_support()
#|    result_dir = output_root / "result" / "raw_only_chain"
#|    result_dir.mkdir(parents=True, exist_ok=True)
#|    payload: dict[str, object] = {
#|        "requested": True,
#|        "supported": bool(support["supported"]),
#|        "support": support,
#|        "workspace_root": "",
#|        "result_dir": str(result_dir),
#|        "status_ko": "",
#|        "generated_outputs": {},
#|        "fixed_fault_reference_compare": {},
#|        "note_ko": (
#|            "raw-only chain은 panel_day_core와 precursor gate만 사용해 audit -> final verdict -> heuristic를 다시 계산한다. "
#|            "커널로그_원인군_ko는 algorithm-derived family 의미로 해석해야 한다."
#|        ),
#|    }
#|    if not support["supported"]:
#|        payload["status_ko"] = "packaged raw-only chain assets missing"
#|        return payload
#|
#|    workspace_root = stage_raw_only_chain_workspace(output_root, sites)
#|    payload["workspace_root"] = str(workspace_root)
#|    commands = [
#|        [sys.executable, str(packaged_script_path("build_panel_day_engine_runtime_fault_event_audit_v1.py")), "--root", str(workspace_root)],
#|        [sys.executable, str(packaged_script_path("build_panel_day_engine_runtime_final_verdict_v1.py")), "--root", str(workspace_root)],
#|        [sys.executable, str(packaged_script_path("build_panel_day_engine_runtime_heuristic_v1.py")), "--root", str(workspace_root)],
#|    ]
#|    for cmd in commands:
#|        subprocess.run(cmd, cwd=package_root(), check=True)
#|
#|    raw_only_common = load_raw_only_common_module()
#|    raw_only_fault_df = raw_only_common.build_fault_table_from_outputs(
#|        workspace_root=workspace_root,
#|        verdict_name=raw_only_common.RUNTIME_VERDICT_OUTPUT_NAME,
#|        heuristic_name=raw_only_common.RUNTIME_HEURISTIC_OUTPUT_NAME,
#|    )
#|    raw_only_preview_df = raw_only_common.build_fault_preview(workspace_root, raw_only_fault_df)
#|    raw_only_fault_path = result_dir / "fault_panel_result_raw_only_v1.csv"
#|    raw_only_preview_path = result_dir / "fault_panel_result_raw_only_preview_v1.csv"
#|    raw_only_fault_df.to_csv(raw_only_fault_path, index=False, encoding="utf-8-sig")
#|    raw_only_preview_df.to_csv(raw_only_preview_path, index=False, encoding="utf-8-sig")
#|
#|    generated = {
#|        "runtime_audit": str(workspace_root / "_share" / raw_only_common.RUNTIME_AUDIT_OUTPUT_NAME),
#|        "runtime_verdict": str(workspace_root / "_share" / raw_only_common.RUNTIME_VERDICT_OUTPUT_NAME),
#|        "runtime_heuristic": str(workspace_root / "_share" / raw_only_common.RUNTIME_HEURISTIC_OUTPUT_NAME),
#|        "fault_panel_result_raw_only_v1": str(raw_only_fault_path),
#|        "fault_panel_result_raw_only_preview_v1": str(raw_only_preview_path),
#|    }
#|    for name, source in [
#|        (raw_only_common.RUNTIME_AUDIT_OUTPUT_NAME, workspace_root / "_share" / raw_only_common.RUNTIME_AUDIT_OUTPUT_NAME),
#|        (raw_only_common.RUNTIME_VERDICT_OUTPUT_NAME, workspace_root / "_share" / raw_only_common.RUNTIME_VERDICT_OUTPUT_NAME),
#|        (raw_only_common.RUNTIME_HEURISTIC_OUTPUT_NAME, workspace_root / "_share" / raw_only_common.RUNTIME_HEURISTIC_OUTPUT_NAME),
#|    ]:
#|        target = result_dir / name
#|        shutil.copy2(source, target)
#|        generated[name] = str(target)
#|
#|    compare = raw_only_common.compare_fault_table_to_reference(raw_only_fault_df, fixed_fault6_table_path())
#|    payload["generated_outputs"] = generated
#|    payload["fixed_fault_reference_compare"] = compare
#|    payload["status_ko"] = "completed"
#|    summary_path = result_dir / "raw_only_chain_summary_v1.json"
#|    write_json(summary_path, payload)
#|    payload["summary_path"] = str(summary_path)
#|    return payload
#|
#|
#|def build_shadow_compare_report(
#|    output_root: Path,
#|    site_plans: list[dict[str, object]],
#|    baseline_comparison: dict[str, object],
#|) -> dict[str, object]:
#|    reference = load_core_baseline_digest()
#|    report: dict[str, object] = {
#|        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
#|        "reference_path": str(baseline_core_digest_path()),
#|        "note_ko": (
#|            "이 shadow compare는 동일 baseline raw corpus로 runtime pack을 다시 실행했을 때 "
#|            "panel_day_core.csv가 reference digest와 같은지 점검한다. "
#|            "현재는 full-chain verdict/evidence/heuristic live compare가 아니라 engine core compare만 수행한다."
#|        ),
#|        "sites": {},
#|        "compared_site_count": 0,
#|        "matched_site_count": 0,
#|        "all_compared_sites_match": True,
#|    }
#|    reference_sites = reference.get("sites", {})
#|
#|    for plan in site_plans:
#|        site = str(plan["site"])
#|        site_entry: dict[str, object] = {
#|            "baseline_input_match": bool(baseline_comparison["sites"].get(site, {}).get("match", False)),
#|            "compared": False,
#|            "match": None,
#|            "skipped_reason": "",
#|            "expected": {},
#|            "actual": {},
#|            "diffs": [],
#|        }
#|        expected = reference_sites.get(site)
#|        if not expected:
#|            site_entry["skipped_reason"] = "missing_packaged_reference_digest"
#|            report["sites"][site] = site_entry
#|            continue
#|        if not site_entry["baseline_input_match"]:
#|            site_entry["skipped_reason"] = "input_manifest_mismatch"
#|            site_entry["expected"] = expected
#|            report["sites"][site] = site_entry
#|            continue
#|
#|        core_path = output_root / "sites" / site / "output" / "panel_day_core.csv"
#|        if not core_path.exists():
#|            site_entry["skipped_reason"] = "missing_generated_panel_day_core"
#|            site_entry["expected"] = expected
#|            report["sites"][site] = site_entry
#|            continue
#|
#|        actual_df = pd.read_csv(core_path, low_memory=False)
#|        actual_digest = build_core_digest_payload(actual_df, core_path.name)
#|        diffs = compare_single_site_digest(expected, actual_digest)
#|        site_entry.update(
#|            {
#|                "compared": True,
#|                "match": not diffs,
#|                "expected": expected,
#|                "actual": actual_digest,
#|                "diffs": diffs,
#|            }
#|        )
#|        report["sites"][site] = site_entry
#|        report["compared_site_count"] += 1
#|        if not diffs:
#|            report["matched_site_count"] += 1
#|        else:
#|            report["all_compared_sites_match"] = False
#|
#|    if report["compared_site_count"] == 0:
#|        report["all_compared_sites_match"] = False
#|    return report
#|
#|
#|def main() -> None:
#|    args = parse_args()
#|    if not engine_path().exists():
#|        raise SystemExit(f"missing packaged engine: {engine_path()}")
#|
#|    emit_progress(1, "실행 준비를 시작합니다.")
#|    data_root = args.data_root.expanduser().resolve()
#|    output_root = args.output_root.expanduser().resolve()
#|    output_root.mkdir(parents=True, exist_ok=True)
#|    reuse_existing_site_outs_root = (
#|        args.reuse_existing_site_outs_root.expanduser().resolve()
#|        if args.reuse_existing_site_outs_root is not None
#|        else None
#|    )
#|
#|    sites = normalize_sites(args.sites)
#|    effective_reuse_existing_site_outs_root, reuse_decision, reuse_freshness = resolve_reuse_existing_site_outs_root(
#|        data_root=data_root,
#|        explicit_reuse_root=reuse_existing_site_outs_root,
#|        prefer_existing_site_outs=args.prefer_existing_site_outs,
#|        sites=sites,
#|    )
#|    site_plans: list[dict[str, object]] = []
#|    commands: list[list[str]] = []
#|    for site in sites:
#|        plan, cmd = build_site_plan(args, site)
#|        site_plans.append(plan)
#|        commands.append(cmd)
#|
#|    emit_progress(8, "입력 CSV 구조와 실행 계획을 점검했습니다.")
#|    fixed_outputs = copy_fixed_results(output_root)
#|    baseline_comparison = compare_to_baseline(site_plans)
#|    live_chain_support = packaged_live_chain_support()
#|    raw_only_chain_support = packaged_raw_only_chain_support()
#|    live_chain_plan = {
#|        "requested": args.run_live_chain == "on",
#|        "supported": bool(live_chain_support["supported"]),
#|        "support": live_chain_support,
#|        "status_ko": "",
#|    }
#|    if not live_chain_plan["requested"]:
#|        live_chain_plan["status_ko"] = "disabled by option"
#|    elif sorted(sites) != sorted(DEFAULT_SITES):
#|        live_chain_plan["status_ko"] = "current live chain supports baseline tri-site universe only"
#|    elif not live_chain_plan["supported"]:
#|        live_chain_plan["status_ko"] = "packaged live chain assets missing"
#|    else:
#|        live_chain_plan["status_ko"] = (
#|            "will run after precomputed out reuse"
#|            if effective_reuse_existing_site_outs_root is not None
#|            else "will run after engine execution"
#|        )
#|    raw_only_chain_plan = {
#|        "requested": args.run_raw_only_chain == "on",
#|        "supported": bool(raw_only_chain_support["supported"]),
#|        "support": raw_only_chain_support,
#|        "status_ko": "",
#|    }
#|    if not raw_only_chain_plan["requested"]:
#|        raw_only_chain_plan["status_ko"] = "disabled by option"
#|    elif not raw_only_chain_plan["supported"]:
#|        raw_only_chain_plan["status_ko"] = "packaged raw-only chain assets missing"
#|    else:
#|        raw_only_chain_plan["status_ko"] = (
#|            "will run after precomputed out reuse"
#|            if effective_reuse_existing_site_outs_root is not None
#|            else "will run after engine execution"
#|        )
#|
#|    plan = {
#|        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
#|        "package_root": str(package_root()),
#|        "engine_path": str(engine_path()),
#|        "data_root": str(data_root),
#|        "output_root": str(output_root),
#|        "reuse_existing_site_outs_root": str(reuse_existing_site_outs_root) if reuse_existing_site_outs_root else "",
#|        "effective_reuse_existing_site_outs_root": (
#|            str(effective_reuse_existing_site_outs_root)
#|            if effective_reuse_existing_site_outs_root
#|            else ""
#|        ),
#|        "prefer_existing_site_outs": args.prefer_existing_site_outs,
#|        "reuse_decision_ko": reuse_decision,
#|        "reuse_freshness": reuse_freshness,
#|        "execution_mode_ko": (
#|            "auto_reuse_existing_site_outs"
#|            if effective_reuse_existing_site_outs_root is not None and reuse_decision == "auto_fresh"
#|            else "reuse_precomputed_site_outs"
#|            if effective_reuse_existing_site_outs_root is not None
#|            else "run_engine_then_live_chain"
#|        ),
#|        "sites": sites,
#|        "site_plans": site_plans,
#|        "fixed_outputs": fixed_outputs,
#|        "baseline_comparison": baseline_comparison,
#|        "live_chain": live_chain_plan,
#|        "raw_only_chain": raw_only_chain_plan,
#|        "shadow_compare_reference_path": str(baseline_core_digest_path()),
#|        "fault6_provenance_path": str(fault6_provenance_path()),
#|        "dependency_audit_json_path": str(dependency_audit_json_path()),
#|        "dependency_audit_md_path": str(dependency_audit_md_path()),
#|        "shadow_compare_report_path": str(output_root / "shadow_compare_v1.json"),
#|        "dry_run": bool(args.dry_run),
#|        "note_ko": (
#|            "이 pack은 conalog/gangui/ktc_ess baseline sites에 대해 실제 panel_day_engine.py 를 실행하고, "
#|            "현재 frozen fault 결과표도 함께 export 한다. "
#|            "fault6 결과표 provenance도 함께 남겨, 이 표가 frozen verdict+heuristic direct assembly인지 확인할 수 있다. "
#|            "추가로 baseline core output shadow compare 경로를 남겨, same baseline 입력일 때 engine core output이 유지되는지도 점검한다."
#|        ),
#|    }
#|
#|    if args.dry_run:
#|        write_json(output_root / "run_plan_v1.json", plan)
#|        emit_progress(100, "dry-run 계획 파일 생성을 완료했습니다.")
#|        print(f"[OK] dry-run plan written: {output_root / 'run_plan_v1.json'}")
#|        return
#|
#|    reused_site_outs: dict[str, str] = {}
#|    if effective_reuse_existing_site_outs_root is not None:
#|        emit_progress(15, "기존 site out 산출물을 재사용합니다.")
#|        reused_site_outs = copy_existing_site_outs(effective_reuse_existing_site_outs_root, output_root, sites)
#|    else:
#|        site_count = max(1, len(commands))
#|        for idx, cmd in enumerate(commands, start=1):
#|            site_name = str(site_plans[idx - 1]["site"])
#|            start_pct = 15 + int((idx - 1) * 45 / site_count)
#|            done_pct = 15 + int(idx * 45 / site_count)
#|            emit_progress(start_pct, f"메인 엔진 실행 시작: {site_name}")
#|            subprocess.run(cmd, check=True)
#|            emit_progress(done_pct, f"메인 엔진 실행 완료: {site_name}")
#|
#|    emit_progress(65, "engine core 결과를 shadow compare 기준으로 점검합니다.")
#|    shadow_compare = build_shadow_compare_report(output_root, site_plans, baseline_comparison)
#|    write_json(output_root / "shadow_compare_v1.json", shadow_compare)
#|    live_chain_result = {"requested": False, "status_ko": "not requested"}
#|    if args.run_live_chain == "on":
#|        emit_progress(75, "live chain 결과표를 생성합니다.")
#|        live_chain_result = run_live_chain(output_root, sites, baseline_comparison)
#|    raw_only_chain_result = {"requested": False, "status_ko": "not requested"}
#|    if args.run_raw_only_chain == "on":
#|        emit_progress(88, "raw-only candidate chain 결과를 생성합니다.")
#|        raw_only_chain_result = run_raw_only_chain(output_root, sites)
#|
#|    master_report_path = output_root / "result" / ROOT_MASTER_REPORT_NAME
#|    detailed_report_path = output_root / "result" / ROOT_DETAILED_REPORT_NAME
#|    precursor_report_path = output_root / "result" / ROOT_PRECURSOR_REPORT_NAME
#|    fault_signal_report_path = output_root / "result" / ROOT_FAULT_SIGNAL_REPORT_NAME
#|    live_preview_path = output_root / "result" / ROOT_LIVE_PREVIEW_NAME
#|    live_preview_df = pd.read_csv(live_preview_path, encoding="utf-8-sig", low_memory=False) if live_preview_path.exists() else pd.DataFrame()
#|    raw_only_candidate_preview_path = output_root / "result" / "raw_only_chain" / "fault_panel_result_raw_only_preview_v1.csv"
#|    raw_only_candidate_preview_df = (
#|        pd.read_csv(raw_only_candidate_preview_path, encoding="utf-8-sig", low_memory=False)
#|        if raw_only_candidate_preview_path.exists()
#|        else pd.DataFrame()
#|    )
#|    detailed_frames = build_detailed_report_frames(
#|        output_root=output_root,
#|        sites=sites,
#|        baseline_comparison=baseline_comparison,
#|        live_chain_result=live_chain_result,
#|        raw_only_chain_result=raw_only_chain_result,
#|        live_preview_df=live_preview_df,
#|        raw_only_preview_df=raw_only_candidate_preview_df,
#|    )
#|    raw_only_current_preview_df = raw_only_candidate_preview_df.copy()
#|    if raw_only_chain_result.get("requested") and normalize_text(raw_only_chain_result.get("status_ko")) == "completed":
#|        strict_fault_df, strict_preview_df, publish_meta = build_strict_raw_only_current_outputs(
#|            raw_only_chain_result=raw_only_chain_result,
#|            evidence_df=detailed_frames["raw_only_evidence"],
#|        )
#|        raw_only_chain_result["publish_meta"] = publish_meta
#|        raw_only_chain_result["published_outputs"] = publish_raw_only_current_outputs(
#|            output_root,
#|            strict_fault_df,
#|            strict_preview_df,
#|        )
#|        root_summary_path = output_root / "result" / ROOT_RAWONLY_SUMMARY_NAME
#|        raw_only_chain_result["published_outputs"][ROOT_RAWONLY_SUMMARY_NAME] = str(root_summary_path)
#|        root_report_path = output_root / "result" / ROOT_RAWONLY_REPORT_NAME
#|        write_text(
#|            root_report_path,
#|            build_raw_only_report_markdown(
#|                sites=sites,
#|                compare=raw_only_chain_result.get("fixed_fault_reference_compare", {}),
#|                published_outputs=raw_only_chain_result["published_outputs"],
#|                live_preview_df=to_user_preview_schema(strict_preview_df),
#|                publish_meta=publish_meta,
#|            ),
#|        )
#|        raw_only_chain_result["published_outputs"][ROOT_RAWONLY_REPORT_NAME] = str(root_report_path)
#|        raw_only_current_preview_df = strict_preview_df.copy()
#|        summary_path = Path(str(raw_only_chain_result.get("summary_path", "")))
#|        if summary_path.exists():
#|            write_json(summary_path, raw_only_chain_result)
#|            shutil.copy2(summary_path, root_summary_path)
#|    live_preview_display_df = to_user_preview_schema(live_preview_df)
#|    raw_only_current_preview_display_df = to_user_preview_schema(raw_only_current_preview_df)
#|    detailed_frames["current_preview"] = nonempty_sheet_df(
#|        live_preview_display_df.copy(),
#|        "live current preview not available",
#|    )
#|    detailed_frames["raw_only_preview"] = nonempty_sheet_df(
#|        raw_only_current_preview_display_df.copy(),
#|        "raw-only preview not available",
#|    )
#|    precursor_report_df = detailed_frames.get(
#|        "precursor_report",
#|        pd.DataFrame(columns=PRECURSOR_REPORT_OUTPUT_COLS),
#|    )
#|    fault_signal_report_df = detailed_frames.get(
#|        "fault_signal_report",
#|        pd.DataFrame(columns=FAULT_SIGNAL_REPORT_OUTPUT_COLS),
#|    )
#|    precursor_report_df.to_csv(precursor_report_path, index=False, encoding="utf-8-sig")
#|    fault_signal_report_df.to_csv(fault_signal_report_path, index=False, encoding="utf-8-sig")
#|    write_detailed_report_xlsx(
#|        detailed_report_path,
#|        detailed_frames,
#|    )
#|    write_text(
#|        master_report_path,
#|        build_master_report_markdown(
#|            sites=sites,
#|            baseline_comparison=baseline_comparison,
#|            live_chain_result=live_chain_result,
#|            raw_only_chain_result=raw_only_chain_result,
#|            live_preview_df=live_preview_display_df,
#|            raw_only_preview_df=raw_only_current_preview_display_df,
#|            precursor_report_df=precursor_report_df,
#|            fault_signal_report_df=fault_signal_report_df,
#|            detailed_report_path=detailed_report_path,
#|            precursor_report_path=precursor_report_path,
#|            fault_signal_report_path=fault_signal_report_path,
#|        ),
#|    )
#|    if live_preview_path.exists():
#|        live_preview_display_df.to_csv(live_preview_path, index=False, encoding="utf-8-sig")
#|    raw_only_current_preview_path = output_root / "result" / ROOT_RAWONLY_PREVIEW_NAME
#|    if raw_only_current_preview_path.exists():
#|        raw_only_current_preview_display_df.to_csv(
#|            raw_only_current_preview_path,
#|            index=False,
#|            encoding="utf-8-sig",
#|        )
#|
#|    metadata = {
#|        **plan,
#|        "dry_run": False,
#|        "reused_site_outs": reused_site_outs,
#|        "shadow_compare": shadow_compare,
#|        "live_chain": live_chain_result,
#|        "raw_only_chain": raw_only_chain_result,
#|        "detailed_report_path": str(detailed_report_path),
#|        "precursor_report_path": str(precursor_report_path),
#|        "fault_signal_report_path": str(fault_signal_report_path),
#|        "master_report_path": str(master_report_path),
#|    }
#|    write_json(output_root / "run_metadata_v1.json", metadata)
#|    emit_progress(100, "실행 완료. 결과 리포트를 열 수 있습니다.")
#|    print(f"[OK] result dir: {output_root / 'result'}")
#|    print(f"[OK] shadow compare: {output_root / 'shadow_compare_v1.json'}")
#|    print(f"[OK] detailed report: {detailed_report_path}")
#|    print(f"[OK] precursor report: {precursor_report_path}")
#|    print(f"[OK] raw-only fault signal report: {fault_signal_report_path}")
#|    print(f"[OK] master report: {master_report_path}")
#|    if live_chain_result.get("requested"):
#|        print(f"[OK] live chain status: {live_chain_result.get('status_ko')}")
#|    if raw_only_chain_result.get("requested"):
#|        print(f"[OK] raw-only chain status: {raw_only_chain_result.get('status_ko')}")
#|    for site in sites:
#|        print(f"[OK] site output: {output_root / 'sites' / site / 'output' / 'panel_day_core.csv'}")
#|
#|
#|if __name__ == "__main__":
#|    main()
# pvdiag_payload_end
# endregion
# region payload: core_engine
# pvdiag_payload_file {"bytes": 136553, "endswith_newline": true, "lines": 3277, "path": "release/conalog_full_runtime_v1/package/pv_ae/panel_day_engine.py", "role": "core_engine", "sha256": "30a20253b897d94d81e1675173334152543d09be7ba49fbef06cbb8552845a80"}
#|# ====== panel_day_engine.py: AE + 최소 룰 기반 버전 ======
#|import argparse
#|import json
#|import pathlib
#|import re
#|from typing import Dict, Any, Tuple, List
#|
#|import numpy as np
#|import pandas as pd
#|import torch
#|import torch.nn as nn
#|import torch.optim as optim
#|from tqdm import tqdm
#|
#|
#|# ========= 유틸 =========
#|
#|# ======== Filename date helper (SSOT) ========
#|_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
#|
#|def extract_date_from_filename(fname: str) -> pd.Timestamp:
#|    """Extract first YYYY-MM-DD from filename and return normalized Timestamp.
#|    Returns pd.NaT when not found / parse fails.
#|    """
#|    m = _DATE_RE.search(str(fname))
#|    if not m:
#|        return pd.NaT
#|    return pd.to_datetime(m.group(1), errors="coerce").normalize()
#|
#|
#|def find_col(df: pd.DataFrame, *names: str) -> str:
#|    """CSV 컬럼 이름이 조금씩 달라도 비슷한 걸 찾아주는 헬퍼."""
#|    low = {c.lower(): c for c in df.columns}
#|    for n in names:
#|        if n.lower() in low:
#|            return low[n.lower()]
#|    base = names[0].lower().replace(" ", "").replace("_", "")
#|    for c in df.columns:
#|        if base in c.lower().replace(" ", "").replace("_", ""):
#|            return c
#|    raise KeyError(f"column not found: {names}")
#|
#|
#|def to_fixed_length(ts: pd.Series, target_len: int = 96) -> np.ndarray:
#|    """1일 시계열을 0~1 구간에서 선형보간 → 길이 target_len 벡터."""
#|    if len(ts) == 0:
#|        return np.zeros(target_len, dtype=float)
#|    x = np.linspace(0, 1, num=len(ts))
#|    y = ts.values.astype(float)
#|    xi = np.linspace(0, 1, num=target_len)
#|    yi = np.interp(xi, x, y)
#|    yi = np.nan_to_num(yi, nan=0.0, posinf=0.0, neginf=0.0)
#|    return yi
#|
#|
#|def estimate_interval_minutes(dt_index: pd.DatetimeIndex) -> float:
#|    """Robustly estimate sampling interval (minutes) from timestamp diffs.
#|
#|    - Uses median of positive diffs (seconds) to avoid outliers.
#|    - Fallback to 5.0 when estimation fails.
#|    """
#|    try:
#|        if dt_index is None or len(dt_index) < 3:
#|            return 5.0
#|        diffs = dt_index.to_series().diff().dt.total_seconds().to_numpy()
#|        diffs = diffs[np.isfinite(diffs) & (diffs > 0)]
#|        if len(diffs) == 0:
#|            return 5.0
#|        med_sec = float(np.median(diffs))
#|        if not np.isfinite(med_sec) or med_sec <= 0:
#|            return 5.0
#|        return med_sec / 60.0
#|    except Exception:
#|        return 5.0
#|
#|
#|# ==== nanmean_or: np.nanmean with empty-slice guard ====
#|def nanmean_or(arr: np.ndarray | list, default: float = np.nan) -> float:
#|    """np.nanmean with an explicit empty-slice guard.
#|
#|    Returns `default` when there are no finite values.
#|    """
#|    a = np.asarray(arr, dtype=float)
#|    a = a[np.isfinite(a)]
#|    if a.size == 0:
#|        return float(default)
#|    return float(np.mean(a))
#|
#|
#|# ======== Panel group key helper ========
#|def panel_group_key(pid: str) -> str:
#|    """Best-effort grouping key from panel_id.
#|
#|    Many of our panel_id values look like:
#|      <uuid>.<string>.<panel>
#|    For peer baselines, we should compare within the same <uuid>.<string> group to
#|    avoid false V-drop signals caused by different string designs/MPPT voltages.
#|
#|    If the format is not like that, fall back to the first token.
#|    """
#|    s = str(pid)
#|    parts = s.split(".")
#|    if len(parts) >= 3:
#|        return parts[0] + "." + parts[1]
#|    if len(parts) == 2:
#|        return parts[0]
#|    return s
#|
#|
#|def _normalize_name_key(text: Any) -> str:
#|    s = str(text).strip().lower()
#|    s = re.sub(r"\d+", "", s)
#|    s = re.sub(r"[^a-z0-9]+", "", s)
#|    return s
#|
#|
#|def _panel_name_key_for_pmax(panel_id: Any) -> str:
#|    token = str(panel_id).split(".")[-1]
#|    k = _normalize_name_key(token)
#|    if k:
#|        return k
#|    return _normalize_name_key(panel_id)
#|
#|
#|def _resolve_col_by_normalized_key(df: pd.DataFrame, candidates: List[str]) -> str:
#|    cols = { _normalize_name_key(c): c for c in df.columns }
#|    for cand in candidates:
#|        k = _normalize_name_key(cand)
#|        if k in cols:
#|            return cols[k]
#|    for ck, c in cols.items():
#|        for cand in candidates:
#|            if _normalize_name_key(cand) in ck:
#|                return c
#|    raise KeyError(f"required column not found. candidates={candidates}, columns={list(df.columns)}")
#|
#|
#|def _parse_numeric_series(s: pd.Series) -> pd.Series:
#|    return pd.to_numeric(
#|        s.astype(str).str.replace(",", ".", regex=False).str.extract(r"([-+]?\d*\.?\d+)")[0],
#|        errors="coerce",
#|    )
#|
#|
#|def _load_pmax_name_map(pmax_info_csv: str) -> Dict[str, float]:
#|    p = pathlib.Path(pmax_info_csv).expanduser().resolve()
#|    if not p.exists():
#|        raise RuntimeError(f"--pmax-info-csv not found: {p}")
#|    try:
#|        info = pd.read_csv(p, sep=";", encoding="utf-8-sig")
#|    except Exception:
#|        info = pd.read_csv(p, sep=";")
#|
#|    c_name = _resolve_col_by_normalized_key(info, ["Name"])
#|    c_pmax = _resolve_col_by_normalized_key(
#|        info,
#|        [
#|            "PV MODULE Maximum Power STC(Pmax)",
#|            "Maximum Power STC(Pmax)",
#|            "Pmax",
#|        ],
#|    )
#|
#|    work = pd.DataFrame(
#|        {
#|            "name_key": info[c_name].map(_normalize_name_key),
#|            "pmax": _parse_numeric_series(info[c_pmax]),
#|        }
#|    )
#|    work = work[work["name_key"].astype(str).str.len() > 0].copy()
#|    work = work[np.isfinite(work["pmax"]) & (work["pmax"] > 0)].copy()
#|    if work.empty:
#|        raise RuntimeError(f"no valid Pmax rows found in {p}")
#|
#|    # Duplicate key guard: conflicting Pmax values for same normalized name are ambiguous.
#|    dup = (
#|        work.groupby("name_key")["pmax"]
#|        .agg(lambda s: int(pd.Series(np.round(s.to_numpy(dtype=float), 6)).nunique()))
#|        .reset_index(name="nuniq")
#|    )
#|    bad_dup = dup[dup["nuniq"] > 1]
#|    if not bad_dup.empty:
#|        keys = bad_dup["name_key"].astype(str).tolist()
#|        raise RuntimeError(f"conflicting Pmax values for normalized Name keys: {keys}")
#|
#|    return work.groupby("name_key", sort=False)["pmax"].first().astype(float).to_dict()
#|
#|
#|def _collect_panel_ids_from_files(files: List[pathlib.Path]) -> List[str]:
#|    panel_ids: set[str] = set()
#|    for fp in files:
#|        try:
#|            try:
#|                df = pd.read_csv(fp, encoding="utf-8-sig")
#|            except Exception:
#|                df = pd.read_csv(fp)
#|            c_id = find_col(df, "map_id", "panel_id", "id")
#|            panel_ids.update(df[c_id].dropna().astype(str).unique().tolist())
#|        except Exception as e:
#|            raise RuntimeError(f"failed to collect panel_id from {fp}: {e}")
#|    return sorted(panel_ids)
#|
#|
#|def _build_panel_pmax_map_for_panels(pmax_info_csv: str, panel_ids: List[str]) -> Dict[str, float]:
#|    name_map = _load_pmax_name_map(pmax_info_csv)
#|    panel_map: Dict[str, float] = {}
#|    missing: list[tuple[str, str]] = []
#|    for pid in panel_ids:
#|        k = _panel_name_key_for_pmax(pid)
#|        if k not in name_map:
#|            missing.append((str(pid), k))
#|            continue
#|        panel_map[str(pid)] = float(name_map[k])
#|    if missing:
#|        msg_lines = ["Pmax mapping failed for panel_ids (panel_id -> normalized_key):"]
#|        msg_lines.extend([f"- {pid} -> {k}" for pid, k in missing])
#|        raise RuntimeError("\n".join(msg_lines))
#|    return panel_map
#|
#|
#|def _resolve_panel_column(columns: List[Any], panel_id: str) -> Any | None:
#|    target = str(panel_id)
#|    for c in columns:
#|        if str(c) == target:
#|            return c
#|    return None
#|
#|
#|def _build_peer_series(
#|    p_tbl: pd.DataFrame,
#|    group_cols: Dict[str, List[Any]],
#|    mode: str = "median",
#|    quantile: float = 0.80,
#|    ref_panel: str = "",
#|) -> Dict[str, pd.Series]:
#|    peer_by_group: Dict[str, pd.Series] = {}
#|    mode_s = str(mode).strip().lower()
#|    q = float(quantile)
#|    if not np.isfinite(q):
#|        q = 0.80
#|    q = min(1.0, max(0.0, q))
#|
#|    ref_col = _resolve_panel_column(list(p_tbl.columns), str(ref_panel)) if ref_panel else None
#|    ref_series = p_tbl[ref_col].astype(float) if ref_col is not None else pd.Series(np.nan, index=p_tbl.index)
#|
#|    for gk, gcols in group_cols.items():
#|        sub = p_tbl[gcols]
#|        if mode_s == "median":
#|            peer_by_group[gk] = sub.median(axis=1)
#|            continue
#|        q_series = sub.quantile(q, axis=1, interpolation="linear")
#|        if mode_s == "quantile":
#|            peer_by_group[gk] = q_series
#|            continue
#|        if mode_s == "ref":
#|            # Ref panel missing at timestamp -> quantile fallback.
#|            s = ref_series.reindex(sub.index)
#|            peer_by_group[gk] = s.where(s.notna(), q_series)
#|            continue
#|        raise RuntimeError(f"unsupported peer-mode: {mode}")
#|    return peer_by_group
#|
#|
#|def compute_run_streak(panel_ids, flags) -> list[int]:
#|    """Compute consecutive true-run length per panel in row order."""
#|    streaks: list[int] = []
#|    current_panel = None
#|    cnt = 0
#|    for pid, flag in zip(panel_ids, flags):
#|        if pid != current_panel:
#|            current_panel = pid
#|            cnt = 0
#|        if flag:
#|            cnt += 1
#|        else:
#|            cnt = 0
#|        streaks.append(cnt)
#|    return streaks
#|
#|
#|def _safe_report_write(df: pd.DataFrame, path: pathlib.Path, label: str, **kwargs) -> bool:
#|    """Best-effort CSV writer for report outputs."""
#|    try:
#|        df.to_csv(path, **kwargs)
#|        return True
#|    except Exception as e:
#|        print(f"[WARN] failed to write {label}: {e}")
#|        return False
#|
#|
#|_EV_DEFAULTS: dict[str, Any] = {
#|    "drop_time": "",
#|    "sustain_mins": 0,
#|    "recovered": False,
#|    "last_ratio": np.nan,
#|    "last_peer": np.nan,
#|    "mid_ratio": np.nan,
#|    "mid_peer": np.nan,
#|    "mid_v_ratio": np.nan,
#|    "mid_i_ratio": np.nan,
#|    "coverage": np.nan,
#|    "co_drop_frac": np.nan,
#|    "recovered_any": False,
#|    "recovered_sustained": False,
#|    "re_drop": False,
#|    "coverage_mid": np.nan,
#|    "seg_count": 0,
#|    "total_low_mins": 0,
#|    "min_ratio": np.nan,
#|    "p10_ratio": np.nan,
#|    "p50_ratio": np.nan,
#|    "low_area": np.nan,
#|}
#|
#|
#|def _extract_event_values(ev: dict[str, Any]) -> dict[str, Any]:
#|    vals: dict[str, Any] = {}
#|    for key, default in _EV_DEFAULTS.items():
#|        raw = ev.get(key, default)
#|        if isinstance(default, bool):
#|            vals[key] = bool(raw)
#|        elif isinstance(default, int):
#|            vals[key] = int(raw)
#|        elif isinstance(default, float):
#|            vals[key] = float(raw)
#|        else:
#|            vals[key] = raw
#|    return vals
#|
#|# ======== 1D k-means (k=2) and train-only vbin builder ========
#|
#|def kmeans_1d_2(x: np.ndarray, iters: int = 20) -> tuple[float, float, float]:
#|    """Simple 1D k-means for k=2 without sklearn.
#|
#|    Returns (c0, c1, split) where split is midpoint between centroids.
#|    Assumes x is finite and len(x) >= 2.
#|    """
#|    x = np.asarray(x, dtype=float)
#|    x = x[np.isfinite(x)]
#|    if len(x) < 2:
#|        m = float(np.nanmedian(x)) if len(x) else 0.0
#|        return m, m, m
#|
#|    # init: 25th and 75th percentiles
#|    c0 = float(np.quantile(x, 0.25))
#|    c1 = float(np.quantile(x, 0.75))
#|    if not np.isfinite(c0):
#|        c0 = float(np.nanmin(x))
#|    if not np.isfinite(c1):
#|        c1 = float(np.nanmax(x))
#|    if c0 == c1:
#|        c1 = c0 + 1e-6
#|
#|    for _ in range(int(iters)):
#|        d0 = np.abs(x - c0)
#|        d1 = np.abs(x - c1)
#|        m0 = x[d0 <= d1]
#|        m1 = x[d0 > d1]
#|        if len(m0) > 0:
#|            c0_new = float(np.mean(m0))
#|        else:
#|            c0_new = c0
#|        if len(m1) > 0:
#|            c1_new = float(np.mean(m1))
#|        else:
#|            c1_new = c1
#|        # convergence
#|        if abs(c0_new - c0) < 1e-6 and abs(c1_new - c1) < 1e-6:
#|            c0, c1 = c0_new, c1_new
#|            break
#|        c0, c1 = c0_new, c1_new
#|
#|    # order centroids
#|    if c0 > c1:
#|        c0, c1 = c1, c0
#|    split = 0.5 * (c0 + c1)
#|    return float(c0), float(c1), float(split)
#|
#|
#|def build_vbin_map_from_train(
#|    train_files: list[pathlib.Path],
#|    critical_peer_min: float,
#|    mid_peer_alive_thr: float,
#|    mid_ratio_dead_thr: float,
#|    coverage_min: float,
#|    panel_pmax_map: Dict[str, float] | None = None,
#|    peer_mode: str = "median",
#|    peer_quantile: float = 0.80,
#|    peer_ref_panel: str = "",
#|) -> tuple[dict[str, int], dict[str, any]]:
#|    """Build a stable per-panel voltage-bin map from TRAIN period only.
#|
#|    Purpose:
#|    - Some group_key contain mixed string designs / MPPT voltages.
#|    - v_ref_span becomes large and v_ref_ok blocks v_drop.
#|    - We split group_key into sub-groups (vbin=0/1) based on panel-level typical mid_v_ratio.
#|
#|    Rules:
#|    - Use TRAIN files only (no leakage).
#|    - Exclude data_bad and dead-like rows when estimating panel typical mid_v_ratio.
#|    - Assign vbin per base group_key using 1D k-means (k=2) on panel medians.
#|    - If group is unimodal (small separation), do not split.
#|
#|    Returns:
#|      vbin_map: panel_id(str) -> 0 or 1
#|      diag: diagnostics dict for logging
#|    """
#|    # Collect mid_v_ratio observations for each panel across train days
#|    # NOTE (Gangui finding): `mid_peer` can be consistently around ~0.4 on clear days
#|    # depending on daylight/mid-window definition. If we gate too hard (e.g., 0.5),
#|    # vbin training observations become empty and vbin_map degenerates to n=0.
#|    # We therefore use a slightly more permissive peer gate ONLY for building vbin_map.
#|    vbin_peer_min = min(float(mid_peer_alive_thr), 0.35)
#|    obs: dict[str, list[float]] = {}
#|    obs_gk: dict[str, str] = {}
#|
#|    for p in train_files:
#|        try:
#|            ev_map = compute_event_features(
#|                p,
#|                panel_pmax_map=panel_pmax_map,
#|                peer_mode=peer_mode,
#|                peer_quantile=peer_quantile,
#|                peer_ref_panel=peer_ref_panel,
#|            )
#|        except Exception:
#|            continue
#|        for pid, ev in ev_map.items():
#|            pid_s = str(pid)
#|            mv = ev.get("mid_v_ratio", np.nan)
#|            mp = ev.get("mid_peer", np.nan)
#|            mr = ev.get("mid_ratio", np.nan)
#|            cov = ev.get("coverage_mid", ev.get("coverage", np.nan))
#|
#|            # train-time quality gates
#|            if not np.isfinite(mv) or not np.isfinite(mp) or not np.isfinite(mr):
#|                continue
#|            if float(mp) < float(vbin_peer_min):
#|                continue
#|            if float(cov) < float(coverage_min):
#|                continue
#|            # exclude dead-like
#|            if float(mr) <= float(mid_ratio_dead_thr):
#|                continue
#|
#|            gk = panel_group_key(pid_s)
#|            obs.setdefault(pid_s, []).append(float(mv))
#|            obs_gk[pid_s] = gk
#|
#|    # Panel-level typical mid_v_ratio (median)
#|    panel_med: dict[str, float] = {}
#|    for pid_s, lst in obs.items():
#|        arr = np.asarray(lst, dtype=float)
#|        arr = arr[np.isfinite(arr)]
#|        if len(arr) == 0:
#|            continue
#|        panel_med[pid_s] = float(np.median(arr))
#|
#|    # Group panels by base group_key
#|    by_gk: dict[str, list[tuple[str, float]]] = {}
#|    for pid_s, mv_med in panel_med.items():
#|        gk = obs_gk.get(pid_s) or panel_group_key(pid_s)
#|        by_gk.setdefault(gk, []).append((pid_s, float(mv_med)))
#|
#|    vbin_map: dict[str, int] = {}
#|    diag: dict[str, any] = {
#|        "groups_total": int(len(by_gk)),
#|        "groups_split": 0,
#|        "groups_unsplit": 0,
#|        "panels_assigned": 0,
#|        "rule": "train-only panel_median mid_v_ratio; kmeans1d k=2; split only if separation is meaningful",
#|        "groups": {},
#|    }
#|
#|    # Heuristic thresholds
#|    # - We normally require >=2 panels per bin to avoid unstable references.
#|    # - However, for small groups (n=3~5) with *very* strong separation, we allow 1 panel in the smaller bin.
#|    #   This is specifically to avoid permanent legacy fallback when a group_key has only 3~5 panels.
#|    min_panels_to_split = 4
#|    min_sep = 0.18        # typical separation threshold
#|    min_sep_strong = 0.30 # strong separation threshold (allow split even when group is small)
#|    min_bin_size = 2      # normal requirement
#|    min_bin_size_small = 1  # allowed only when sep is strong and group is small
#|
#|    for gk, pairs in by_gk.items():
#|        pairs = [(pid_s, mv) for (pid_s, mv) in pairs if np.isfinite(mv)]
#|        if len(pairs) < 2:
#|            for pid_s, _mv in pairs:
#|                vbin_map[pid_s] = 0
#|            diag["groups"][gk] = {"n": len(pairs), "split": False, "reason": "too_few_panels"}
#|            diag["groups_unsplit"] += 1
#|            continue
#|
#|        xs = np.asarray([mv for (_pid_s, mv) in pairs], dtype=float)
#|        xs = xs[np.isfinite(xs)]
#|        if len(xs) < 2:
#|            for pid_s, _mv in pairs:
#|                vbin_map[pid_s] = 0
#|            diag["groups"][gk] = {"n": len(pairs), "split": False, "reason": "no_finite"}
#|            diag["groups_unsplit"] += 1
#|            continue
#|
#|        c0, c1, split = kmeans_1d_2(xs)
#|        sep = float(abs(c1 - c0))
#|
#|        # Split decision:
#|        # - Normal case: enough panels AND meaningful separation
#|        # - Strong-sep case: even if group is small, split when sep is very large
#|        do_split = (
#|            ((len(pairs) >= int(min_panels_to_split)) and (sep >= float(min_sep)))
#|            or ((sep >= float(min_sep_strong)) and (len(pairs) >= 3))
#|        )
#|
#|        if not do_split:
#|            for pid_s, _mv in pairs:
#|                vbin_map[pid_s] = 0
#|            diag["groups"][gk] = {
#|                "n": len(pairs),
#|                "split": False,
#|                "reason": "unimodal_or_small",
#|                "c0": c0,
#|                "c1": c1,
#|                "sep": sep,
#|                "split_at": split,
#|            }
#|            diag["groups_unsplit"] += 1
#|            continue
#|
#|        # Bin-size safety:
#|        # - default: require >=2 panels per bin
#|        # - small group + strong separation: allow 1 panel in the smaller bin
#|        b0 = int(sum(1 for (_pid_s, mv) in pairs if float(mv) <= float(split)))
#|        b1 = int(sum(1 for (_pid_s, mv) in pairs if float(mv) > float(split)))
#|
#|        eff_min_bin = int(min_bin_size)
#|        if (len(pairs) <= 5) and (sep >= float(min_sep_strong)):
#|            eff_min_bin = int(min_bin_size_small)
#|
#|        if (b0 < eff_min_bin) or (b1 < eff_min_bin):
#|            for pid_s, _mv in pairs:
#|                vbin_map[pid_s] = 0
#|            diag["groups"][gk] = {
#|                "n": len(pairs),
#|                "split": False,
#|                "reason": "tiny_bin",
#|                "c0": c0,
#|                "c1": c1,
#|                "sep": sep,
#|                "split_at": split,
#|                "bin0": b0,
#|                "bin1": b1,
#|                "eff_min_bin": eff_min_bin,
#|            }
#|            diag["groups_unsplit"] += 1
#|            continue
#|
#|        # Assign bins by split point
#|        for pid_s, mv in pairs:
#|            vbin_map[pid_s] = 0 if float(mv) <= float(split) else 1
#|
#|        diag["groups"][gk] = {
#|            "n": len(pairs),
#|            "split": True,
#|            "c0": c0,
#|            "c1": c1,
#|            "sep": sep,
#|            "split_at": split,
#|            "bin0": int(sum(1 for (_pid_s, mv) in pairs if float(mv) <= float(split))),
#|            "bin1": int(sum(1 for (_pid_s, mv) in pairs if float(mv) > float(split))),
#|        }
#|        diag["groups_split"] += 1
#|
#|    diag["panels_assigned"] = int(len(vbin_map))
#|    return vbin_map, diag
#|
#|
#|def mark_run_segments(
#|    df: pd.DataFrame,
#|    key_col: str,
#|    date_col: str,
#|    cond_col: str,
#|    min_len: int,
#|    out_col: str,
#|) -> pd.DataFrame:
#|    """Mark whole consecutive-true segments when run length >= min_len."""
#|    df[out_col] = False
#|    if min_len <= 1:
#|        df[out_col] = df[cond_col].fillna(False).astype(bool)
#|        return df
#|
#|    df = df.sort_values([key_col, date_col]).copy()
#|    for pid, g in df.groupby(key_col, sort=False):
#|        idxs = g.index.to_list()
#|        flags = g[cond_col].fillna(False).astype(bool).to_list()
#|
#|        start = None
#|        run_len = 0
#|        for k, flag in enumerate(flags + [False]):  # sentinel
#|            if flag:
#|                if start is None:
#|                    start = k
#|                    run_len = 1
#|                else:
#|                    run_len += 1
#|            else:
#|                if start is not None and run_len >= int(min_len):
#|                    seg_idxs = idxs[start : start + run_len]
#|                    df.loc[seg_idxs, out_col] = True
#|                start = None
#|                run_len = 0
#|    return df
#|
#|
#|def compute_vdrop_labels(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
#|    """Single SSOT for critical-like labels.
#|
#|    Output columns (defined exactly once here):
#|      - critical_like_raw / critical_like_suspect_raw
#|      - critical_like_eff / critical_like / critical_like_suspect / critical_like_suspect_eff
#|      - critical_like_legacy / critical_source / vdrop_trust
#|    """
#|    out = df.copy()
#|    args = params["args"]
#|    tuning_level = str(params.get("tuning_level", "p2")).lower().strip()
#|
#|    def _bool_col(name: str) -> pd.Series:
#|        if name not in out.columns:
#|            return pd.Series(False, index=out.index)
#|        s = pd.to_numeric(out[name], errors="coerce").fillna(0.0)
#|        return s.ne(0)
#|
#|    def _num_col(name: str) -> pd.Series:
#|        if name in out.columns:
#|            return pd.to_numeric(out[name], errors="coerce")
#|        return pd.Series(np.nan, index=out.index, dtype=float)
#|
#|    v_ref_ok = _bool_col("v_ref_ok")
#|    data_bad = _bool_col("data_bad")
#|    group_off_like = _bool_col("group_off_like")
#|    mid_peer_ok = _num_col("mid_peer") >= float(args.mid_peer_alive_thr)
#|
#|    # V-drop hit evidence (trust-agnostic): preserve legacy guard set used in existing vdrop_condition_post.
#|    v_drop = _num_col("v_drop")
#|    mid_i = _num_col("mid_i_ratio")
#|    mid_r = _num_col("mid_ratio")
#|    vdrop_hit_any = (
#|        v_drop.notna()
#|        & np.isfinite(v_drop.to_numpy(dtype=float))
#|        & (v_drop >= float(args.v_drop_thr))
#|        & mid_i.notna()
#|        & (mid_i >= float(args.mid_i_ratio_healthy_thr))
#|        & mid_r.notna()
#|        & (mid_r >= float(args.critical_mid_ratio_min))
#|        & (mid_r <= float(args.critical_mid_ratio_max))
#|    )
#|
#|    out["critical_like_raw"] = (vdrop_hit_any & v_ref_ok).astype(int)
#|    out["critical_like_suspect_raw"] = (vdrop_hit_any & (~v_ref_ok)).astype(int)
#|
#|    # Legacy fallback semantics are preserved for p2 only.
#|    legacy_hit = pd.Series(False, index=out.index)
#|    if tuning_level == "p2":
#|        use_vdrop = v_ref_ok & np.isfinite(v_drop.to_numpy(dtype=float))
#|        cov_mid = _num_col("coverage_mid").fillna(0.0)
#|        mid_v = _num_col("mid_v_ratio")
#|        legacy_hit = (
#|            (~data_bad)
#|            & mid_peer_ok
#|            & (~use_vdrop)
#|            & (cov_mid >= float(args.coverage_min))
#|            & mid_v.notna()
#|            & (mid_v <= float(args.mid_v_ratio_critical_thr))
#|            & (mid_i >= float(args.mid_i_ratio_healthy_thr))
#|            & (mid_r >= float(args.critical_mid_ratio_min))
#|            & (mid_r <= float(args.critical_mid_ratio_max))
#|        )
#|    out["critical_like_legacy"] = legacy_hit.astype(int)
#|
#|    # Effective labels (after quality + group-off gates) are defined once here.
#|    eff_vdrop = (
#|        (out["critical_like_raw"].astype(int) == 1)
#|        & (~data_bad)
#|        & mid_peer_ok
#|        & (~group_off_like)
#|    )
#|    eff_legacy = (
#|        legacy_hit.astype(bool)
#|        & (~group_off_like)
#|    )
#|    out["critical_like_eff"] = (eff_vdrop | eff_legacy).astype(bool)
#|    out["critical_like"] = out["critical_like_eff"].astype(bool)
#|
#|    out["critical_like_suspect"] = (
#|        (out["critical_like_suspect_raw"].astype(int) == 1)
#|        & (~data_bad)
#|        & mid_peer_ok
#|        & (~group_off_like)
#|        & (~out["critical_like_eff"].astype(bool))
#|    ).astype(bool)
#|    out["critical_like_suspect_eff"] = out["critical_like_suspect"].astype(bool)
#|
#|    out["vdrop_trust"] = v_ref_ok.astype(int)
#|
#|    # Source is set once: legacy > vdrop > vdrop_suspect precedence.
#|    out["critical_source"] = "none"
#|    out.loc[out["critical_like_suspect"].astype(bool), "critical_source"] = "vdrop_suspect"
#|    out.loc[out["critical_like_eff"].astype(bool) & (~legacy_hit.astype(bool)), "critical_source"] = "vdrop"
#|    out.loc[legacy_hit.astype(bool) & out["critical_like_eff"].astype(bool), "critical_source"] = "legacy"
#|
#|    return out
#|
#|
#|def _max_run_by_panel(df: pd.DataFrame, flag_col: str) -> pd.DataFrame:
#|    """Compute max consecutive-day run length per panel for a boolean/int flag."""
#|    tmp = df[["panel_id", "date", flag_col]].copy()
#|    tmp[flag_col] = pd.to_numeric(tmp[flag_col], errors="coerce").fillna(0).astype(int)
#|    tmp = tmp.sort_values(["panel_id", "date"])
#|
#|    runs = []
#|    for pid, g in tmp.groupby("panel_id", sort=False):
#|        vals = g[flag_col].to_numpy(dtype=int)
#|        best = 0
#|        cur = 0
#|        for v in vals:
#|            if v == 1:
#|                cur += 1
#|                if cur > best:
#|                    best = cur
#|            else:
#|                cur = 0
#|        runs.append((pid, int(best)))
#|    return pd.DataFrame(runs, columns=["panel_id", f"{flag_col}_max_run"]).sort_values(
#|        f"{flag_col}_max_run", ascending=False
#|    )
#|
#|# ======== DTW & Hampel Score Helpers =========
#|
#|def dtw_distance(curve: np.ndarray, ref: np.ndarray, band: int | None = None) -> float:
#|    """
#|    Compute Dynamic Time Warping (DTW) distance between two 1D arrays.
#|    - Truncate to min(len(curve), len(ref))
#|    - Use squared difference as cost
#|    - NaNs treated as 0.0
#|    - O(N^2) baseline; if `band` is provided, apply Sakoe–Chiba constraint to speed up.
#|
#|    Parameters
#|    ----------
#|    curve, ref : np.ndarray
#|        1D arrays.
#|    band : int | None
#|        If not None, only compute cells where |i-j| <= band.
#|        Use a small band (e.g., 8~16 for length 96) to reduce compute.
#|    """
#|    a = np.nan_to_num(curve, nan=0.0, posinf=0.0, neginf=0.0)
#|    b = np.nan_to_num(ref, nan=0.0, posinf=0.0, neginf=0.0)
#|    n = min(len(a), len(b))
#|    a = a[:n]
#|    b = b[:n]
#|
#|    # If band is None, default to full DTW.
#|    if band is None:
#|        band = n  # effectively unconstrained
#|    else:
#|        band = int(max(0, band))
#|
#|    INF = 1e30
#|    D = np.full((n, n), INF, dtype=float)
#|
#|    # Initialize start
#|    D[0, 0] = (a[0] - b[0]) ** 2
#|
#|    # Initialize first column/row within band
#|    for i in range(1, n):
#|        if i <= band:
#|            D[i, 0] = D[i - 1, 0] + (a[i] - b[0]) ** 2
#|    for j in range(1, n):
#|        if j <= band:
#|            D[0, j] = D[0, j - 1] + (a[0] - b[j]) ** 2
#|
#|    # Main DP with band constraint
#|    for i in range(1, n):
#|        j_start = max(1, i - band)
#|        j_end = min(n - 1, i + band)
#|        for j in range(j_start, j_end + 1):
#|            cost = (a[i] - b[j]) ** 2
#|            D[i, j] = cost + min(D[i - 1, j], D[i, j - 1], D[i - 1, j - 1])
#|
#|    return float(D[n - 1, n - 1])
#|
#|def compute_hs(curve: np.ndarray) -> float:
#|    """
#|    Compute a Hampel-like turbulence score for a 1D array.
#|    - NaNs/infs replaced with 0.0
#|    - Uses median/MAD, fallback to std if MAD too small, else 0.0
#|    - Returns fraction of |z| >= 2.5
#|    """
#|    x = np.nan_to_num(curve, nan=0.0, posinf=0.0, neginf=0.0)
#|    med = np.median(x)
#|    mad = np.median(np.abs(x - med))
#|    scale = mad if mad >= 1e-6 else np.std(x)
#|    if scale < 1e-6:
#|        return 0.0
#|    z = (x - med) / scale
#|    return float(np.mean(np.abs(z) >= 2.5))
#|
#|
#|# ========= 하루 power ratio 곡선 (AE용) =========
#|
#|def load_day_curves(
#|    csv_path: pathlib.Path,
#|    daylight_frac: float = 0.10,
#|    peer_eps: float = 1e-6,
#|    use_log_ratio: bool = False,
#|    panel_pmax_map: Dict[str, float] | None = None,
#|    peer_mode: str = "median",
#|    peer_quantile: float = 0.80,
#|    peer_ref_panel: str = "",
#|) -> Dict[str, np.ndarray]:
#|    """
#|    - P = V * I (or Pnorm = P/Pmax when panel_pmax_map is provided)
#|    - peer median P 기준으로 P_ratio = P / peerP
#|    - peerP가 max의 daylight_frac 이상인 구간만 사용
#|    - 각 패널 곡선을 길이 96으로 보간
#|    """
#|    try:
#|        df = pd.read_csv(csv_path, encoding="utf-8-sig")
#|    except Exception:
#|        df = pd.read_csv(csv_path)
#|
#|    c_dt = find_col(df, "date_time", "datetime", "timestamp", "time")
#|    c_id = find_col(df, "map_id", "panel_id", "id")
#|    c_v = find_col(df, "v_in (v)", "v_in", "vin", "input_voltage")
#|    c_i = find_col(df, "i_out (a)", "i_out", "i", "current")
#|
#|    df["_dt"] = pd.to_datetime(df[c_dt], errors="coerce")
#|    df = df.dropna(subset=["_dt"]).sort_values("_dt")
#|
#|    v = pd.to_numeric(df[c_v], errors="coerce")
#|    i = pd.to_numeric(df[c_i], errors="coerce")
#|    df["p_calc"] = (v * i).astype(float).clip(lower=0)
#|
#|    P = df.pivot_table(index="_dt", columns=c_id, values="p_calc")
#|    if panel_pmax_map:
#|        pmax_vec = pd.Series(
#|            {
#|                col: float(panel_pmax_map.get(str(col), np.nan))
#|                for col in P.columns
#|            }
#|        )
#|        if pmax_vec.isna().any():
#|            missing = [str(c) for c in P.columns if not np.isfinite(float(pmax_vec.get(c, np.nan)))]
#|            raise RuntimeError(f"Pmax missing for panels in {csv_path.name}: {missing}")
#|        P = P.divide(pmax_vec, axis=1)
#|
#|    # Site-level peer (for daylight detection)
#|    peerP_site = P.median(axis=1)
#|    if len(peerP_site) == 0 or np.nanmax(peerP_site.values) <= 0:
#|        return {}
#|
#|    # Daylight mask based on site-level peer
#|    mask = peerP_site >= float(np.nanmax(peerP_site.values)) * daylight_frac
#|    P_use = P.loc[mask]
#|
#|    # Build per-group peer medians to avoid false anomalies from heterogeneous strings
#|    # IMPORTANT: keep original column labels for safe DataFrame indexing (do not index by str(...) blindly).
#|    group_cols: Dict[str, List[Any]] = {}
#|    for pid in P_use.columns:
#|        pid_s = str(pid)
#|        group_cols.setdefault(panel_group_key(pid_s), []).append(pid)
#|    peerP_group = _build_peer_series(
#|        P_use,
#|        group_cols,
#|        mode=peer_mode,
#|        quantile=peer_quantile,
#|        ref_panel=peer_ref_panel,
#|    )
#|
#|    curves: Dict[str, np.ndarray] = {}
#|    for pid in P_use.columns:
#|        pid_s = str(pid)
#|        s = P_use[pid].astype(float)
#|        if s.notna().sum() < 10:
#|            continue
#|        gk = panel_group_key(pid_s)
#|        peer_use = peerP_group.get(gk)
#|        if peer_use is None or len(peer_use) == 0:
#|            continue
#|        peer_aligned = peer_use.reindex(s.index, method="nearest")
#|
#|        # Robust ratio: avoid division blow-up when peer baseline is tiny.
#|        # Optionally use log-stabilized ratio for heavy-tailed / low-irradiance robustness.
#|        peer_aligned_v = pd.to_numeric(peer_aligned, errors="coerce").astype(float)
#|        s_v = pd.to_numeric(s, errors="coerce").astype(float)
#|
#|        if use_log_ratio:
#|            # log1p ratio proxy: log(P+1) - log(peer+1)
#|            ratio_vals = (np.log1p(s_v.clip(lower=0.0)) - np.log1p(peer_aligned_v.clip(lower=0.0)))
#|        else:
#|            safe_peer = peer_aligned_v.where(peer_aligned_v >= float(peer_eps), np.nan)
#|            with np.errstate(divide="ignore", invalid="ignore"):
#|                ratio_vals = s_v / safe_peer
#|
#|        ratio = pd.Series(
#|            np.nan_to_num(ratio_vals.to_numpy(), nan=0.0, posinf=0.0, neginf=0.0),
#|            index=s.index,
#|        )
#|        curves[pid_s] = to_fixed_length(ratio, 96)
#|    return curves
#|
#|
#|# ========= 하루 이벤트 feature (룰용) =========
#|
#|def compute_event_features(
#|    csv_path: pathlib.Path,
#|    drop_thr: float = 0.90,
#|    sustain_thr: float = 0.80,
#|    last_minutes: int = 60,
#|    recovered_consec: int = 3,
#|    recovered_sustain_mins: int = 15,
#|    co_drop_thr: float = 0.15,
#|    daylight_event_thr: float = 0.2,
#|    peer_eps: float = 1e-6,
#|    panel_pmax_map: Dict[str, float] | None = None,
#|    peer_mode: str = "median",
#|    peer_quantile: float = 0.80,
#|    peer_ref_panel: str = "",
#|) -> Dict[str, Dict[str, Any]]:
#|    """
#|    패널별로:
#|      - drop_time: P_ratio가 sustain_thr 이하로 가장 길게 유지된 구간의 시작 시각 (daylight 안에서)
#|      - sustain_mins: drop 이후 P_ratio <= sustain_thr 인 연속 구간 최장 길이 (분)
#|      - recovered: drop 이후 P_ratio >= drop_thr 가 연속 recovered_consec 샘플 이상 유지되면 True
#|      - last_ratio: 마지막 last_minutes 동안 P_ratio 평균
#|      - last_peer: 마지막 last_minutes 동안 peerP_frac 평균
#|      - mid_ratio: 11시~15시 사이 daylight 구간에서 P_ratio 평균
#|      - mid_peer: 11시~15시 사이 daylight 구간에서 peerP_frac 평균
#|      - co_drop_frac: 최장 저하구간 동안 sustain_thr 이하에 들어간 패널 비율의 평균 (공간 동시성 지표)
#|      - NOTE: event daylight threshold is `daylight_event_thr` (default 0.2) and ratio uses `peer_eps` guard.
#|    """
#|    try:
#|        df = pd.read_csv(csv_path, encoding="utf-8-sig")
#|    except Exception:
#|        df = pd.read_csv(csv_path)
#|
#|    c_dt = find_col(df, "date_time", "datetime", "timestamp", "time")
#|    c_id = find_col(df, "map_id", "panel_id", "id")
#|    c_v = find_col(df, "v_in (v)", "v_in", "vin", "input_voltage")
#|    c_i = find_col(df, "i_out (a)", "i_out", "i", "current")
#|
#|    df["_dt"] = pd.to_datetime(df[c_dt], errors="coerce")
#|    df = df.dropna(subset=["_dt"]).sort_values("_dt")
#|
#|    V = df.pivot_table(index="_dt", columns=c_id, values=c_v)
#|    I = df.pivot_table(index="_dt", columns=c_id, values=c_i)
#|    V = V.apply(pd.to_numeric, errors="coerce").clip(lower=0)
#|    I = I.apply(pd.to_numeric, errors="coerce").clip(lower=0)
#|    P = (V * I).clip(lower=0)
#|    if panel_pmax_map:
#|        pmax_vec = pd.Series(
#|            {
#|                col: float(panel_pmax_map.get(str(col), np.nan))
#|                for col in P.columns
#|            }
#|        )
#|        if pmax_vec.isna().any():
#|            missing = [str(c) for c in P.columns if not np.isfinite(float(pmax_vec.get(c, np.nan)))]
#|            raise RuntimeError(f"Pmax missing for panels in {csv_path.name}: {missing}")
#|        P = P.divide(pmax_vec, axis=1)
#|
#|    # Site-level peer (for daylight/midday gating)
#|    peerP_site = P.median(axis=1)
#|    peerV_site = V.median(axis=1)
#|    peerI_site = I.median(axis=1)
#|    if len(peerP_site) == 0 or np.nanmax(peerP_site.values) <= 0:
#|        return {}
#|
#|    # Build per-group peer baselines (uuid.string) for ratio features
#|    # IMPORTANT: keep original column labels for safe DataFrame indexing.
#|    group_cols: Dict[str, List[Any]] = {}
#|    for pid in P.columns:
#|        pid_s = str(pid)
#|        group_cols.setdefault(panel_group_key(pid_s), []).append(pid)
#|    peerP_by_group: Dict[str, pd.Series] = {}
#|    peerV_by_group: Dict[str, pd.Series] = {}
#|    peerI_by_group: Dict[str, pd.Series] = {}
#|
#|    peerP_by_group = _build_peer_series(
#|        P,
#|        group_cols,
#|        mode=peer_mode,
#|        quantile=peer_quantile,
#|        ref_panel=peer_ref_panel,
#|    )
#|    for gk, gcols in group_cols.items():
#|        peerV_by_group[gk] = V[gcols].median(axis=1)
#|        peerI_by_group[gk] = I[gcols].median(axis=1)
#|
#|    # Fallbacks (degenerate guards)
#|    for gk in list(peerP_by_group.keys()):
#|        if len(peerP_by_group[gk]) == 0 or np.nanmax(peerP_by_group[gk].values) <= 0:
#|            peerP_by_group[gk] = peerP_site.copy()
#|        if len(peerV_by_group[gk]) == 0 or np.nanmax(peerV_by_group[gk].values) <= 0:
#|            # DO NOT fallback to power baseline (unit mismatch). Use site-level V median if available.
#|            if len(peerV_site) > 0 and np.nanmax(peerV_site.values) > 0:
#|                peerV_by_group[gk] = peerV_site.copy()
#|            else:
#|                peerV_by_group[gk] = pd.Series(np.nan, index=peerP_site.index)
#|        if len(peerI_by_group[gk]) == 0 or np.nanmax(peerI_by_group[gk].values) <= 0:
#|            # Prefer site-level I median; fallback to 1.0 only when everything is missing.
#|            if len(peerI_site) > 0 and np.nanmax(peerI_site.values) > 0:
#|                peerI_by_group[gk] = peerI_site.copy()
#|            else:
#|                peerI_by_group[gk] = pd.Series(1.0, index=peerP_site.index)
#|
#|    # Robust interval estimation (minutes)
#|    interval_min = estimate_interval_minutes(P.index)
#|    if not np.isfinite(interval_min) or interval_min <= 0:
#|        interval_min = 5.0
#|
#|    # Normalize site-level peer power to [0,1] for daylight and mid-window gating.
#|    # NOTE: peerP_site can have NaNs at timestamps where all panels are missing.
#|    # If we later take a mean over a slice that is all-NaN, np.nanmean returns NaN,
#|    # which then propagates to mid_peer/last_peer and breaks gates downstream.
#|    peerP_frac = peerP_site / float(np.nanmax(peerP_site.values))
#|    peerP_frac = peerP_frac.astype(float)
#|    peerP_frac_arr = np.nan_to_num(peerP_frac.to_numpy(), nan=0.0, posinf=0.0, neginf=0.0)
#|    # daylight (event): peerP_frac >= daylight_event_thr
#|    daylight_thr = float(daylight_event_thr)
#|    daylight_mask = peerP_frac_arr >= daylight_thr
#|
#|    daylight_mask_np = np.asarray(daylight_mask, dtype=bool)
#|
#|    times = P.index.to_numpy()
#|    times_idx = P.index
#|
#|    # midday mask: daylight and hour in [11,15)
#|    mid_mask = np.array([
#|        (pf >= daylight_thr) and (11 <= ts.hour < 15)
#|        for pf, ts in zip(peerP_frac_arr, times_idx)
#|    ])
#|
#|    # Site-level ratio table only for spatial concurrence (co-drop) diagnostics
#|    with np.errstate(divide="ignore", invalid="ignore"):
#|        R_tbl_site = P.div(peerP_site, axis=0)
#|
#|    out: Dict[str, Dict[str, Any]] = {}
#|
#|    for pid in P.columns:
#|        pid_s = str(pid)
#|        gk = panel_group_key(pid_s)
#|        peerP = peerP_by_group.get(gk, peerP_site)
#|        peerV = peerV_by_group.get(gk, peerV_site)
#|        peerI = peerI_by_group.get(gk, peerI_site)
#|        p = P[pid].astype(float).to_numpy()
#|        if np.sum(np.isfinite(p)) < 5:
#|            continue
#|
#|        # coverage: daylight 구간 중 실제 측정이 있는 비율
#|        valid_day = np.isfinite(p) & daylight_mask_np
#|        daylight_count = int(daylight_mask_np.sum())
#|        if daylight_count > 0:
#|            coverage = float(valid_day.sum() / daylight_count)
#|        else:
#|            coverage = 0.0
#|
#|        # coverage within mid-window (11~15) to avoid "noon holes" masking issues
#|        if int(np.sum(mid_mask)) > 0:
#|            valid_mid = np.isfinite(p) & mid_mask
#|            coverage_mid = float(np.sum(valid_mid) / int(np.sum(mid_mask)))
#|        else:
#|            coverage_mid = float(coverage)
#|
#|        # EVENT ratio with peer-eps gating (SSOT): peer < eps -> NaN (avoid 0/0, x/0 blow-ups)
#|        peer_arr = pd.to_numeric(peerP, errors="coerce").astype(float).to_numpy()
#|        safe_peer = np.where(peer_arr >= float(peer_eps), peer_arr, np.nan)
#|        with np.errstate(divide="ignore", invalid="ignore"):
#|            r = p / safe_peer
#|        # Keep NaNs here; downstream masks/np.isfinite() will exclude invalid points deterministically.
#|
#|        # V/I ratio arrays (panel vs *group* peer)
#|        v_arr = V[pid].astype(float).to_numpy()
#|        i_arr = I[pid].astype(float).to_numpy()
#|        with np.errstate(divide="ignore", invalid="ignore"):
#|            vr = v_arr / peerV.to_numpy()
#|            ir = i_arr / peerI.to_numpy()
#|        vr = np.nan_to_num(vr, nan=0.0, posinf=0.0, neginf=0.0)
#|        ir = np.nan_to_num(ir, nan=0.0, posinf=0.0, neginf=0.0)
#|
#|        # daylight-masked versions
#|        vr_day = vr.copy()
#|        ir_day = ir.copy()
#|        vr_day[~daylight_mask_np] = np.nan
#|        ir_day[~daylight_mask_np] = np.nan
#|
#|        # Spatial concurrence helper series for this panel/day
#|        # Fraction of panels that are also <= sustain_thr at each timestamp (within daylight)
#|        # NOTE: Uses median peer baseline; if a large fraction drops together, it's more likely environmental.
#|        with np.errstate(invalid="ignore"):
#|            co_series = (R_tbl_site <= sustain_thr).mean(axis=1).to_numpy(dtype=float)
#|            co_series = np.nan_to_num(co_series, nan=0.0, posinf=0.0, neginf=0.0)
#|        co_series_day = co_series.copy()
#|        co_series_day[~daylight_mask_np] = np.nan
#|
#|        # daylight 부분만 고려
#|        r_day = r.copy()
#|        r_day[~daylight_mask_np] = np.nan
#|
#|        # longest low segment: P_ratio <= sustain_thr within daylight
#|        cond = np.isfinite(r_day) & (r_day <= sustain_thr)
#|
#|        # Feature expansion: segment counts / total low minutes / quantiles / low-area
#|        r_day_f = r_day.copy()
#|        valid_mask = np.isfinite(r_day_f)
#|
#|        if np.any(valid_mask):
#|            min_ratio = float(np.nanmin(r_day_f))
#|            p10_ratio = float(np.nanpercentile(r_day_f[valid_mask], 10))
#|            p50_ratio = float(np.nanpercentile(r_day_f[valid_mask], 50))
#|        else:
#|            min_ratio = 0.0
#|            p10_ratio = 0.0
#|            p50_ratio = 0.0
#|
#|        # total low minutes
#|        total_low_pts = int(np.sum(cond))
#|        total_low_mins = int(round(total_low_pts * float(interval_min)))
#|
#|        # low area: sum(thr - ratio) where ratio < thr
#|        low_area = float(np.nansum(np.maximum(0.0, float(sustain_thr) - np.nan_to_num(r_day_f, nan=np.nan))))
#|
#|        # segment count: number of low segments
#|        seg_count = 0
#|        prev = False
#|        for flag in cond:
#|            if flag and (not prev):
#|                seg_count += 1
#|            prev = bool(flag)
#|
#|        # compute mid_ratio and mid_peer_val (+ NEW: mid_v_ratio, mid_i_ratio)
#|        if np.any(mid_mask):
#|            mid_ratio = nanmean_or(r[mid_mask], default=np.nan)
#|            mid_peer_val = float(np.mean(peerP_frac_arr[mid_mask])) if np.any(mid_mask) else float(np.mean(peerP_frac_arr))
#|            mid_v_ratio = nanmean_or(vr[mid_mask], default=np.nan)
#|            mid_i_ratio = nanmean_or(ir[mid_mask], default=np.nan)
#|        else:
#|            mid_ratio = nanmean_or(r_day, default=np.nan)
#|            mid_peer_val = float(np.mean(peerP_frac_arr))
#|            mid_v_ratio = nanmean_or(vr_day, default=np.nan)
#|            mid_i_ratio = nanmean_or(ir_day, default=np.nan)
#|
#|        if not np.any(cond):
#|            # no meaningful low segment
#|            out[pid_s] = {
#|                "drop_time": "",
#|                "sustain_mins": 0,
#|                "recovered": False,
#|                "last_ratio": nanmean_or(r_day, default=np.nan),
#|                "last_peer": float(np.mean(peerP_frac_arr)),
#|                "mid_ratio": float(mid_ratio),
#|                "mid_peer": float(mid_peer_val),
#|                "mid_v_ratio": float(mid_v_ratio) if 'mid_v_ratio' in locals() else nanmean_or(vr_day, default=np.nan),
#|                "mid_i_ratio": float(mid_i_ratio) if 'mid_i_ratio' in locals() else nanmean_or(ir_day, default=np.nan),
#|                "coverage": float(coverage),
#|                "co_drop_frac": 0.0,
#|                "recovered_any": False,
#|                "recovered_sustained": False,
#|                "re_drop": False,
#|                "coverage_mid": float(coverage_mid),
#|                "seg_count": int(seg_count),
#|                "total_low_mins": int(total_low_mins),
#|                "min_ratio": float(min_ratio),
#|                "p10_ratio": float(p10_ratio),
#|                "p50_ratio": float(p50_ratio),
#|                "low_area": float(low_area),
#|            }
#|            continue
#|
#|        # find longest consecutive True segment in cond
#|        max_len = 0
#|        best_start = None
#|        best_end = None
#|        current_start = None
#|        current_len = 0
#|
#|        for idx, flag in enumerate(cond):
#|            if flag:
#|                if current_start is None:
#|                    current_start = idx
#|                    current_len = 1
#|                else:
#|                    current_len += 1
#|                if current_len > max_len:
#|                    max_len = current_len
#|                    best_start = current_start
#|                    best_end = idx
#|            else:
#|                current_start = None
#|                current_len = 0
#|
#|        drop_idx = best_start
#|        if drop_idx is None:
#|            # fallback: treat as no drop
#|            out[pid_s] = {
#|                "drop_time": "",
#|                "sustain_mins": 0,
#|                "recovered": False,
#|                "last_ratio": nanmean_or(r_day, default=np.nan),
#|                "last_peer": float(np.mean(peerP_frac_arr)),
#|                "mid_ratio": float(mid_ratio),
#|                "mid_peer": float(mid_peer_val),
#|                "mid_v_ratio": float(mid_v_ratio) if 'mid_v_ratio' in locals() else nanmean_or(vr_day, default=np.nan),
#|                "mid_i_ratio": float(mid_i_ratio) if 'mid_i_ratio' in locals() else nanmean_or(ir_day, default=np.nan),
#|                "coverage": float(coverage),
#|                "co_drop_frac": 0.0,
#|                "recovered_any": False,
#|                "recovered_sustained": False,
#|                "re_drop": False,
#|                "coverage_mid": float(coverage_mid),
#|                "seg_count": int(seg_count),
#|                "total_low_mins": int(total_low_mins),
#|                "min_ratio": float(min_ratio),
#|                "p10_ratio": float(p10_ratio),
#|                "p50_ratio": float(p50_ratio),
#|                "low_area": float(low_area),
#|            }
#|            continue
#|
#|        # Spatial concurrence score for the chosen (longest) low segment
#|        # Average fraction of panels that are also low during this segment
#|        if best_end is not None and best_start is not None:
#|            seg = co_series_day[best_start : best_end + 1]
#|            co_drop_frac = nanmean_or(seg, default=0.0)
#|        else:
#|            co_drop_frac = 0.0
#|
#|        drop_time = pd.Timestamp(times[drop_idx]).isoformat()
#|        sustain_mins = int(round(max_len * float(interval_min)))
#|
#|        # recovered definitions
#|        # recovered_any: any post-segment ratio >= drop_thr
#|        # recovered_sustained: post-segment ratio >= drop_thr sustained for recovered_sustain_mins
#|        # re_drop: after sustained recovery, drops again to sustain_thr or below
#|        recovered_any = False
#|        recovered_sustained = False
#|        re_drop = False
#|
#|        if best_end is not None and best_end + 1 < len(r):
#|            tail = r[best_end + 1 :]
#|            tail_ok = np.isfinite(tail) & (tail >= float(drop_thr))
#|            recovered_any = bool(np.any(tail_ok))
#|
#|            # sustain requirement in points (time-based)
#|            sustain_pts = int(max(1, np.ceil(float(recovered_sustain_mins) / float(interval_min))))
#|
#|            # longest consecutive True run
#|            run = 0
#|            best_run = 0
#|            for flag in tail_ok:
#|                if flag:
#|                    run += 1
#|                    best_run = max(best_run, run)
#|                else:
#|                    run = 0
#|
#|            recovered_sustained = bool(best_run >= sustain_pts)
#|
#|            # re_drop: only meaningful after sustained recovery
#|            if recovered_sustained:
#|                # find first index where sustained recovery starts
#|                run = 0
#|                start_idx = None
#|                for k, flag in enumerate(tail_ok):
#|                    if flag:
#|                        run += 1
#|                        if run >= sustain_pts:
#|                            start_idx = k - sustain_pts + 1
#|                            break
#|                    else:
#|                        run = 0
#|
#|                if start_idx is not None:
#|                    after_rec = tail[start_idx + sustain_pts :]
#|                    after_low = np.isfinite(after_rec) & (after_rec <= float(sustain_thr))
#|                    re_drop = bool(np.any(after_low))
#|
#|        # backward-compatible alias (old field)
#|        recovered = bool(recovered_sustained)
#|
#|        # 마지막 last_minutes 동안 평균
#|        if len(times) > 0:
#|            last_dt = pd.Timestamp(times[-1])
#|            start_last = last_dt - pd.Timedelta(minutes=last_minutes)
#|            last_mask = (times >= np.datetime64(start_last)) & (times <= np.datetime64(last_dt))
#|        else:
#|            last_mask = np.zeros_like(r, dtype=bool)
#|
#|        if np.any(last_mask):
#|            last_ratio = nanmean_or(r[last_mask], default=np.nan)
#|            last_peer = float(np.mean(peerP_frac_arr[last_mask])) if np.any(last_mask) else float(np.mean(peerP_frac_arr))
#|        else:
#|            last_ratio = nanmean_or(r_day, default=np.nan)
#|            last_peer = float(np.mean(peerP_frac_arr))
#|
#|        out[pid_s] = {
#|            "drop_time": drop_time,
#|            "sustain_mins": sustain_mins,
#|            "recovered": bool(recovered),
#|            "last_ratio": last_ratio,
#|            "last_peer": last_peer,
#|            "mid_ratio": float(mid_ratio),
#|            "mid_peer": float(mid_peer_val),
#|            "mid_v_ratio": float(mid_v_ratio),
#|            "mid_i_ratio": float(mid_i_ratio),
#|            "coverage": float(coverage),
#|            "co_drop_frac": float(co_drop_frac),
#|            "recovered_any": bool(recovered_any),
#|            "recovered_sustained": bool(recovered_sustained),
#|            "re_drop": bool(re_drop),
#|            "coverage_mid": float(coverage_mid),
#|            "seg_count": int(seg_count),
#|            "total_low_mins": int(total_low_mins),
#|            "min_ratio": float(min_ratio),
#|            "p10_ratio": float(p10_ratio),
#|            "p50_ratio": float(p50_ratio),
#|            "low_area": float(low_area),
#|        }
#|
#|    return out
#|
#|
#|# ========= Autoencoder =========
#|
#|class AE(nn.Module):
#|    def __init__(self, dim: int = 96, latent: int = 16):
#|        super().__init__()
#|        self.encoder = nn.Sequential(
#|            nn.Linear(dim, 64),
#|            nn.ReLU(),
#|            nn.Linear(64, latent),
#|        )
#|        self.decoder = nn.Sequential(
#|            nn.Linear(latent, 64),
#|            nn.ReLU(),
#|            nn.Linear(64, dim),
#|        )
#|
#|    def forward(self, x: torch.Tensor) -> torch.Tensor:
#|        z = self.encoder(x)
#|        out = self.decoder(z)
#|        return out
#|
#|
#|def train_ae(train_mat: np.ndarray, latent: int, epochs: int, device: str) -> Tuple[AE, np.ndarray]:
#|    x = torch.tensor(train_mat, dtype=torch.float32)
#|    model = AE(dim=train_mat.shape[1], latent=latent).to(device)
#|    opt = optim.Adam(model.parameters(), lr=1e-3)
#|    loss_fn = nn.MSELoss()
#|
#|    ds = torch.utils.data.TensorDataset(x)
#|    loader = torch.utils.data.DataLoader(ds, batch_size=64, shuffle=True)
#|
#|    model.train()
#|    for _ in range(epochs):
#|        for (batch,) in loader:
#|            batch = batch.to(device)
#|            opt.zero_grad()
#|            rec = model(batch)
#|            loss = loss_fn(rec, batch)
#|            loss.backward()
#|            opt.step()
#|
#|    model.eval()
#|    with torch.no_grad():
#|        rec = model(x.to(device)).cpu().numpy()
#|    train_err = ((train_mat - rec) ** 2).mean(axis=1)
#|    return model, train_err
#|
#|
#|# ========= CLI =========
#|
#|def parse_args():
#|    ap = argparse.ArgumentParser()
#|    ap.add_argument("--dir", required=False,
#|                    help="Input directory containing daily CSVs. Prefer --site for portable runs.")
#|    ap.add_argument("--site", default=None,
#|                    help="Site key to use data/<site>/raw as input (portable, recommended).")
#|    ap.add_argument("--data-root", default=None,
#|                    help="Project data root. Defaults to <project_root>/data if omitted.")
#|    ap.add_argument("--out-dir", default=None,
#|                    help="Output directory. Defaults to data/<site>/out (or <dir>/out).")
#|    ap.add_argument("--log-dir", default=None,
#|                    help="Log directory. Defaults to data/<site>/log (or <dir>/log).")
#|    ap.add_argument("--pattern", default="*.csv")
#|    ap.add_argument("--train-start", required=True)
#|    ap.add_argument("--train-end", required=True)
#|    ap.add_argument("--eval-start", required=True)
#|    ap.add_argument("--eval-end", required=True)
#|    ap.add_argument("--epochs", type=int, default=40)
#|    ap.add_argument("--latent", type=int, default=16)
#|    ap.add_argument("--contam", type=float, default=0.10)
#|    ap.add_argument("--recon-mult", type=float, default=1.0)
#|    ap.add_argument("--device", default="cpu")
#|    ap.add_argument("--seed", type=int, default=42,
#|                    help="Random seed for reproducible training/eval (default 42).")
#|    # 튜닝 단계 스위치 (엄격 진행)
#|    ap.add_argument(
#|        "--tuning-level",
#|        choices=["p0", "p1", "p2"],
#|        default="p2",
#|        help=(
#|            "Tuning stage switch. p0=baseline(dead/confirmed only), p1=+group_off_like gate, p2=full (critical/shadow/EWS/etc)."
#|        ),
#|    )
#|
#|    # 룰 파라미터
#|    ap.add_argument("--sustain-mins", type=int, default=40)
#|    ap.add_argument("--drop-thr", type=float, default=0.90)
#|    ap.add_argument("--sustain-thr", type=float, default=0.80)
#|    ap.add_argument("--last-ratio-thr", type=float, default=0.80)
#|    ap.add_argument("--last-peer-thr", type=float, default=0.40)
#|
#|    # 추가 룰 파라미터
#|    ap.add_argument("--event-sustain-mins", type=int, default=15)
#|    ap.add_argument("--mid-peer-alive-thr", type=float, default=0.5)
#|    ap.add_argument("--mid-ratio-dead-thr", type=float, default=0.2)
#|
#|    # critical-like (V-drop) parameters (for bypass-diode-short-like patterns)
#|    # NOTE: In real systems, V-drop levels are not always exactly ~33%.
#|    # We therefore prefer a *relative* drop vs per-(date, group_key) peer V reference.
#|    ap.add_argument(
#|        "--v-drop-thr",
#|        type=float,
#|        default=0.20,
#|        help="Critical-like V-drop threshold expressed as v_drop = 1 - mid_v_ratio/v_ref (default 0.20).",
#|    )
#|    ap.add_argument(
#|        "--v-ref-min",
#|        type=float,
#|        default=0.30,
#|        help="Minimum v_ref (group median mid_v_ratio) required to evaluate v_drop (default 0.30).",
#|    )
#|    ap.add_argument(
#|        "--v-ref-vspan-max",
#|        type=float,
#|        default=0.12,
#|        help="Maximum allowed v_ref span (p90-p10 of mid_v_ratio within (date,group_key)) to trust v_ref/v_drop (default 0.12).",
#|    )
#|    ap.add_argument(
#|        "--v-ref-min-n",
#|        type=int,
#|        default=6,
#|        help="Minimum number of reference panels within (date, group_key) required to trust v_ref/v_drop (default 6).",
#|    )
#|
#|    # Backward-compat (legacy): keep old absolute threshold; not used when v_drop is available.
#|    ap.add_argument(
#|        "--mid-v-ratio-critical-thr",
#|        type=float,
#|        default=0.75,
#|        help="(Legacy) Absolute critical-like threshold for mid_v_ratio. Prefer --v-drop-thr.",
#|    )
#|    ap.add_argument(
#|        "--mid-i-ratio-healthy-thr",
#|        type=float,
#|        default=0.85,
#|        help="Healthy-ish current threshold for mid_i_ratio when labeling V-drop critical-like (default 0.85).",
#|    )
#|    ap.add_argument(
#|        "--critical_mid_ratio_min",
#|        type=float,
#|        default=0.40,
#|        help="Minimum mid_ratio required to treat V-drop as critical-like (exclude near-dead/off cases). Default 0.40.",
#|    )
#|    ap.add_argument(
#|        "--critical_mid_ratio_max",
#|        type=float,
#|        default=0.95,
#|        help="Maximum mid_ratio allowed for critical-like (exclude fully-normal days). Default 0.95.",
#|    )
#|    ap.add_argument(
#|        "--critical-days",
#|        type=int,
#|        default=5,
#|        help="Number of consecutive critical-like days to confirm critical_fault (default 5).",
#|    )
#|
#|    # critical 2-stage split (confirmed vs suspect)
#|    ap.add_argument("--critical-peer-min", type=float, default=0.6,
#|                    help="Only evaluate critical stability on days with mid_peer >= this value (default 0.6).")
#|    ap.add_argument("--critical-vspan-max", type=float, default=0.12,
#|                    help="Max allowed v_span (p90-p10 of mid_v_ratio) for confirmed critical panels (default 0.12).")
#|    ap.add_argument("--critical-min-days", type=int, default=5,
#|                    help="Minimum number of critical-like days for confirmed critical panels (default 5).")
#|
#|    # shadow-like refinement parameters
#|    ap.add_argument("--shadow-seg-min", type=int, default=2,
#|                    help="Minimum number of low segments (seg_count) for shadow_like refinement (default 2).")
#|    ap.add_argument("--shadow-min-ratio-floor", type=float, default=0.30,
#|                    help="Minimum min_ratio floor to keep shadow_like from capturing near-dead patterns (default 0.30).")
#|    ap.add_argument("--dead-days", type=int, default=2)
#|    ap.add_argument("--coverage-min", type=float, default=0.5)
#|
#|    ap.add_argument("--ews-quantile", type=float, default=0.9,
#|                    help="전체 사이트 분포에서 EWS 롤링 지표 상위 분위수 (기본 0.9)")
#|    ap.add_argument("--ews-k-sigma", type=float, default=1.0,
#|                    help="월별 베이스라인(mean + k*sigma) 보정 시 사용할 k 값 (기본 1.0)")
#|    ap.add_argument("--dtw-band", type=int, default=12,
#|                    help="DTW Sakoe–Chiba band width (None/<=0 means unconstrained). Default 12 for length-96 curves.")
#|    ap.add_argument("--recovered-consec", type=int, default=3,
#|                    help="Recovered 판단 시 drop_thr 이상을 연속으로 만족해야 하는 최소 샘플 수 (기본 3).")
#|    ap.add_argument("--shadow-co-drop-thr", type=float, default=0.15,
#|                    help="shadow_like 정제 시 co_drop_frac(공간 동시성) 최소 임계값 (기본 0.15).")
#|    ap.add_argument("--recovered-sustain-mins", type=int, default=15,
#|                    help="Recovered_sustained 판단을 위한 최소 유지 시간(분). interval 기반으로 points로 변환.")
#|    ap.add_argument("--peer-eps", type=float, default=1e-6,
#|                    help="ratio 계산 시 peer baseline이 이 값보다 작으면 제외(division blow-up 방지).")
#|    ap.add_argument("--daylight-event-thr", type=float, default=0.2,
#|                    help="Event/daylight gate threshold on peerP_frac for compute_event_features (default 0.2; site override allowed).")
#|    ap.add_argument("--use-log-ratio", action="store_true",
#|                    help="AE 입력 ratio를 log1p(P)-log1p(peer)로 안정화하여 사용.")
#|    ap.add_argument("--pmax-info-csv", default="",
#|                    help="Optional TECNALIA module info CSV(semicolon-separated). When set, power axis uses Pnorm=P/Pmax(panel).")
#|    ap.add_argument("--peer-mode", choices=["median", "quantile", "ref"], default="median",
#|                    help="Peer baseline mode for ratio features: median(legacy), quantile, ref.")
#|    ap.add_argument("--peer-quantile", type=float, default=0.80,
#|                    help="Peer quantile used when --peer-mode quantile/ref fallback (default 0.80).")
#|    ap.add_argument("--peer-ref-panel", default="",
#|                    help="Reference panel_id when --peer-mode ref. Missing timestamps fall back to peer-quantile.")
#|
#|    # group/string-level OFF-like detection (protect against mislabeling string events as panel faults)
#|    ap.add_argument("--group-off-min-panels", type=int, default=10,
#|                    help="(Group-level) If >= this many panels in the SAME group_key are simultaneously dead-like (state_dead) on a day, consider group-off candidate.")
#|    ap.add_argument("--group-off-min-frac", type=float, default=0.50,
#|                    help="(Group-level) Minimum dead-like fraction within group_key to consider group-off candidate.")
#|    ap.add_argument("--group-off-max-frac", type=float, default=1.00,
#|                    help="(Group-level) Maximum dead-like fraction within group_key (set high; site-wide protection is handled elsewhere).")
#|    ap.add_argument("--group-off-jaccard", type=float, default=0.80,
#|                    help="Jaccard similarity threshold between consecutive days' dead-like panel sets to confirm a persistent group-off event.")
#|    ap.add_argument("--group-off-allow-single-day", action="store_true",
#|                    help="If set, allow single-day group-off labeling even without consecutive-day set stability.")
#|    return ap.parse_args()
#|
#|
#|def _setup_paths(args, seed: int):
#|    """Resolve input/output/log paths and split train/eval files by filename date."""
#|    # ---- Portable path resolution (project-root relative) ----
#|    script_path = pathlib.Path(__file__).resolve()
#|    project_root = script_path.parents[1]  # pvdiag/
#|
#|    # Determine data root
#|    if args.data_root is not None:
#|        data_root = pathlib.Path(args.data_root).expanduser().resolve()
#|    else:
#|        data_root = (project_root / "data").resolve()
#|
#|    # Determine input directory
#|    if args.site:
#|        site = str(args.site).strip()
#|        data_dir = (data_root / site / "raw").resolve()
#|    elif args.dir:
#|        data_dir = pathlib.Path(args.dir).expanduser().resolve()
#|        site = None
#|    else:
#|        raise RuntimeError("Must provide either --site <name> or --dir <path>.")
#|
#|    # Determine output/log directories
#|    if args.out_dir is not None:
#|        out_dir = pathlib.Path(args.out_dir).expanduser().resolve()
#|    else:
#|        out_dir = ((data_root / site / "out") if site else (data_dir / "out")).resolve()
#|
#|    if args.log_dir is not None:
#|        log_dir = pathlib.Path(args.log_dir).expanduser().resolve()
#|    else:
#|        log_dir = ((data_root / site / "log") if site else (data_dir / "log")).resolve()
#|
#|    out_dir.mkdir(parents=True, exist_ok=True)
#|    log_dir.mkdir(parents=True, exist_ok=True)
#|
#|    # Record run configuration for reproducibility
#|    import sys
#|    from datetime import datetime
#|    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
#|    run_info_path = log_dir / f"run_{run_ts}.json"
#|    try:
#|        run_info = {
#|            "timestamp": run_ts,
#|            "cwd": str(pathlib.Path.cwd()),
#|            "script": str(script_path),
#|            "project_root": str(project_root),
#|            "data_root": str(data_root),
#|            "site": site,
#|            "data_dir": str(data_dir),
#|            "out_dir": str(out_dir),
#|            "log_dir": str(log_dir),
#|            "argv": sys.argv,
#|            "python": sys.version,
#|            "seed": seed,
#|        }
#|        run_info_path.write_text(json.dumps(run_info, ensure_ascii=False, indent=2), encoding="utf-8")
#|        print(f"[OK] wrote run config: {run_info_path}")
#|    except Exception as e:
#|        print(f"[WARN] failed to write run config: {e}")
#|
#|    if not data_dir.exists():
#|        raise RuntimeError(f"input directory not found: {data_dir}")
#|
#|    def in_range(p: pathlib.Path, s: str, e: str) -> bool:
#|        """Filename date filter.
#|        - Extracts first occurrence of YYYY-MM-DD anywhere in the filename.
#|        - Compares as dates to avoid lexicographic corner cases.
#|        """
#|        d = extract_date_from_filename(p.name)
#|        if pd.isna(d):
#|            return False
#|        sdt = pd.to_datetime(s, errors="coerce").normalize()
#|        edt = pd.to_datetime(e, errors="coerce").normalize()
#|        if pd.isna(sdt) or pd.isna(edt):
#|            return False
#|        return (d >= sdt) and (d <= edt)
#|
#|    files = sorted(
#|        p for p in data_dir.glob(args.pattern)
#|        if p.is_file() and p.suffix.lower() == ".csv"
#|    )
#|
#|    print(f"[INFO] input_dir = {data_dir}")
#|    print(f"[INFO] out_dir   = {out_dir}")
#|    print(f"[INFO] log_dir   = {log_dir}")
#|
#|    train_files = [p for p in files if in_range(p, args.train_start, args.train_end)]
#|    eval_files = [p for p in files if in_range(p, args.eval_start, args.eval_end)]
#|
#|    # Diagnostics: show detected date range in filenames
#|    try:
#|        import re
#|        ds = []
#|        for p in files:
#|            m = re.search(r"(\d{4}-\d{2}-\d{2})", p.name)
#|            if m:
#|                d = pd.to_datetime(m.group(1), errors="coerce")
#|                if pd.notna(d):
#|                    ds.append(d)
#|        if ds:
#|            print(f"[INFO] detected file date range: {min(ds).date()} ~ {max(ds).date()} (n={len(ds)})")
#|    except Exception:
#|        pass
#|
#|    if not train_files:
#|        raise RuntimeError(
#|            f"no training files in range: {args.train_start} ~ {args.train_end} (pattern={args.pattern})"
#|        )
#|    if not eval_files:
#|        raise RuntimeError(
#|            f"no eval files in range: {args.eval_start} ~ {args.eval_end} (pattern={args.pattern})"
#|        )
#|
#|    return data_dir, out_dir, log_dir, site, train_files, eval_files
#|
#|
#|def _detect_group_off(out: pd.DataFrame, args) -> pd.DataFrame:
#|    # ---- Group-off / string-off like event detection (group_key-level) ----
#|    # What we observed in Gangui:
#|    # - Only ~10~15% of site panels are dead-like on those days,
#|    # - but within specific group_key (string-like groups), dead_frac can be 50~80%.
#|    # Site-level detection is too coarse; it can over-gate unrelated panels.
#|    #
#|    # New behavior:
#|    # - Detect OFF-like events per (date, group_key)
#|    # - Mark only those panels in the affected group_key as group_off_like
#|    # - Keep group_off_date as a convenience (any group-off group on that date)
#|    out["group_off_group"] = False  # row-level: panel belongs to a group_key flagged as OFF-like on that date
#|
#|    flagged_pairs: set[tuple[pd.Timestamp, str]] = set()
#|
#|    # For each group_key, track previous day's dead-set to compute Jaccard stability
#|    prev_dead_set_by_gk: Dict[str, set] = {}
#|    prev_date_by_gk: Dict[str, pd.Timestamp] = {}
#|    prev_candidate_by_gk: Dict[str, bool] = {}
#|
#|    # Iterate by date then by group_key
#|    for d in sorted(out["date"].dropna().unique()):
#|        gd = out[out["date"] == d]
#|        for gk, gg in gd.groupby("group_key"):
#|            # dead-like set within good data only (within this group)
#|            dead_set = set(
#|                gg.loc[(~gg["data_bad"].astype(bool)) & (gg["state_dead"].astype(bool)), "panel_id"].astype(str).tolist()
#|            )
#|            n_dead = len(dead_set)
#|            n_total = int(gg["panel_id"].nunique())
#|            frac = (n_dead / n_total) if n_total > 0 else 0.0
#|
#|            # Candidate definition is applied per-group now.
#|            candidate = (
#|                (n_dead >= int(args.group_off_min_panels))
#|                & (frac >= float(args.group_off_min_frac))
#|                & (frac <= float(args.group_off_max_frac))
#|            )
#|
#|            confirmed_today = False
#|
#|            # Allow single-day labeling when explicitly enabled
#|            if candidate and bool(args.group_off_allow_single_day):
#|                confirmed_today = True
#|
#|            # Consecutive-day stability check (Jaccard)
#|            if candidate and prev_candidate_by_gk.get(gk, False):
#|                prev_dead = prev_dead_set_by_gk.get(gk)
#|                if prev_dead is not None:
#|                    inter = len(dead_set & prev_dead)
#|                    union = len(dead_set | prev_dead)
#|                    jacc = (inter / union) if union > 0 else 0.0
#|                    if jacc >= float(args.group_off_jaccard):
#|                        confirmed_today = True
#|                        # also mark previous day as group-off for this group_key
#|                        prev_d = prev_date_by_gk.get(gk)
#|                        if prev_d is not None:
#|                            flagged_pairs.add((prev_d, gk))
#|
#|            if confirmed_today:
#|                flagged_pairs.add((d, gk))
#|
#|            # update trackers
#|            prev_dead_set_by_gk[gk] = dead_set
#|            prev_date_by_gk[gk] = d
#|            prev_candidate_by_gk[gk] = bool(candidate)
#|
#|    if flagged_pairs:
#|        # row-level membership in flagged (date, group_key)
#|        pair_series = list(zip(out["date"], out["group_key"]))
#|        out["group_off_group"] = [((dd, ggk) in flagged_pairs) for (dd, ggk) in pair_series]
#|
#|    # convenience flag: any group-off group exists on that date
#|    group_dates = {dd for (dd, _gk) in flagged_pairs}
#|    out["group_off_date"] = out["date"].isin(group_dates)
#|
#|    # group_off_like is now precise: only dead-like panels in the flagged group_key
#|    out["group_off_like"] = (
#|        out["group_off_group"].astype(bool)
#|        & (~out["data_bad"].astype(bool))
#|        & out["state_dead"].astype(bool)
#|    )
#|    # --- P1/P2 safety: group_off_like must never contribute to V-drop/critical signals ---
#|    # Rationale: group/string OFF events can produce apparent V-drop rows and confuse downstream checks.
#|    # We keep group_off_like as its own category and mask V-drop-related fields on those rows.
#|    go_mask = out["group_off_like"].fillna(False).astype(bool)
#|    if go_mask.any():
#|        out.loc[go_mask, "v_drop"] = np.nan
#|        out.loc[go_mask, "v_ref_ok"] = False
#|        # keep ops visibility: treat as no usable reference for these rows
#|        if "no_ref" in out.columns:
#|            out.loc[go_mask, "no_ref"] = True
#|    return out
#|
#|
#|def _compute_ews(out: pd.DataFrame, args) -> pd.DataFrame:
#|    q = float(args.ews_quantile)
#|    k_sigma = float(args.ews_k_sigma)
#|
#|    out["ews_month"] = out["date"].dt.month
#|
#|    # Pre-allocate causal baseline columns (for transparency/debugging)
#|    out["mid_base_mean"] = np.nan
#|    out["mid_base_std"] = np.nan
#|    out["dtw_base_mean"] = np.nan
#|    out["dtw_base_std"] = np.nan
#|    out["hs_base_mean"] = np.nan
#|    out["hs_base_std"] = np.nan
#|
#|    # Causal conditions (filled date-by-date)
#|    cond_var = pd.Series(False, index=out.index)
#|    cond_dtw = pd.Series(False, index=out.index)
#|    cond_hs = pd.Series(False, index=out.index)
#|
#|    # eventA 빈도: 최근 7일 중 절반 이상 event_A 발생 (행 단위로 바로 계산 가능)
#|    cond_evt = out["ews_eventA_freq_7d"] >= 0.5
#|
#|    # Date-by-date causal thresholds/baselines
#|    for d in sorted(out["date"].dropna().unique()):
#|        mask_d = out["date"] == d
#|        past = out.loc[out["date"] < d]
#|
#|        # If no past, leave conditions as False for this date
#|        if past.empty:
#|            continue
#|
#|        # Global (site-wide) thresholds from past only
#|        def _past_thr(series: pd.Series, qq: float) -> float:
#|            vals = series.to_numpy()
#|            if np.isfinite(vals).any():
#|                return float(np.nanquantile(vals, qq))
#|            return np.nan
#|
#|        var_thr = _past_thr(past["ews_mid_var_7d"], q)
#|        dtw_thr = _past_thr(past["ews_dtw_mean_7d"], q)
#|        hs_thr = _past_thr(past["ews_hs_mean_7d"], q)
#|
#|        # Panel×Month baseline from past only
#|        base = (
#|            past.groupby(["panel_id", "ews_month"])[
#|                ["ews_mid_var_7d", "ews_dtw_mean_7d", "ews_hs_mean_7d"]
#|            ]
#|            .agg(["mean", "std"])
#|        )
#|
#|        # Helper to fetch baseline stats for current rows
#|        def _get_base(metric: str, stat: str) -> pd.Series:
#|            s = base[(metric, stat)]
#|            # align by (panel_id, ews_month)
#|            key = list(zip(out.loc[mask_d, "panel_id"], out.loc[mask_d, "ews_month"]))
#|            return pd.Series([s.get(k, np.nan) for k in key], index=out.index[mask_d])
#|
#|        # Fill baseline columns for this date (debug visibility)
#|        out.loc[mask_d, "mid_base_mean"] = _get_base("ews_mid_var_7d", "mean")
#|        out.loc[mask_d, "mid_base_std"] = _get_base("ews_mid_var_7d", "std")
#|        out.loc[mask_d, "dtw_base_mean"] = _get_base("ews_dtw_mean_7d", "mean")
#|        out.loc[mask_d, "dtw_base_std"] = _get_base("ews_dtw_mean_7d", "std")
#|        out.loc[mask_d, "hs_base_mean"] = _get_base("ews_hs_mean_7d", "mean")
#|        out.loc[mask_d, "hs_base_std"] = _get_base("ews_hs_mean_7d", "std")
#|
#|        # Apply both gates (global quantile + seasonal baseline) using past-only statistics
#|        if np.isfinite(var_thr) and var_thr > 0:
#|            cv = out.loc[mask_d, "ews_mid_var_7d"] >= var_thr
#|        else:
#|            cv = pd.Series(False, index=out.index[mask_d])
#|        mid_thr_base = out.loc[mask_d, "mid_base_mean"] + k_sigma * out.loc[mask_d, "mid_base_std"].fillna(0.0)
#|        cv = cv & out.loc[mask_d, "mid_base_mean"].notna() & (out.loc[mask_d, "ews_mid_var_7d"] >= mid_thr_base)
#|        cond_var.loc[mask_d] = cv.fillna(False)
#|
#|        if np.isfinite(dtw_thr) and dtw_thr > 0:
#|            cd = out.loc[mask_d, "ews_dtw_mean_7d"] >= dtw_thr
#|        else:
#|            cd = pd.Series(False, index=out.index[mask_d])
#|        dtw_thr_base = out.loc[mask_d, "dtw_base_mean"] + k_sigma * out.loc[mask_d, "dtw_base_std"].fillna(0.0)
#|        cd = cd & out.loc[mask_d, "dtw_base_mean"].notna() & (out.loc[mask_d, "ews_dtw_mean_7d"] >= dtw_thr_base)
#|        cond_dtw.loc[mask_d] = cd.fillna(False)
#|
#|        if np.isfinite(hs_thr) and hs_thr > 0:
#|            ch = out.loc[mask_d, "ews_hs_mean_7d"] >= hs_thr
#|        else:
#|            ch = pd.Series(False, index=out.index[mask_d])
#|        hs_thr_base = out.loc[mask_d, "hs_base_mean"] + k_sigma * out.loc[mask_d, "hs_base_std"].fillna(0.0)
#|        ch = ch & out.loc[mask_d, "hs_base_mean"].notna() & (out.loc[mask_d, "ews_hs_mean_7d"] >= hs_thr_base)
#|        cond_hs.loc[mask_d] = ch.fillna(False)
#|
#|    out["cond_var"] = cond_var.astype(bool)
#|    out["cond_evt"] = cond_evt.astype(bool)
#|    out["cond_dtw"] = cond_dtw.astype(bool)
#|    out["cond_hs"] = cond_hs.astype(bool)
#|
#|    # 패널-날짜별로 high 신호 개수 계산 (4개 중 2개 이상)
#|    signal_count = (
#|        cond_var.astype(int)
#|        + cond_evt.astype(int)
#|        + cond_dtw.astype(int)
#|        + cond_hs.astype(int)
#|    )
#|    out["signal_count"] = signal_count.astype(int)
#|
#|    # data_bad가 아니고, high 신호가 2개 이상인 날을 "잠정 전조 신호"로 본다.
#|    pre_ews = (~out["data_bad"]) & (signal_count >= 2)
#|    out["pre_ews"] = pre_ews.astype(bool)
#|
#|    # 4) 연속성 조건: 같은 패널에서 5일 이상 연속 pre_ews가 유지되면 EWS 경고로 확정 (방안 C)
#|    out["ews_runlen"] = compute_run_streak(out["panel_id"], pre_ews)
#|
#|    out["ews_warning"] = False
#|    out.loc[pre_ews & (out["ews_runlen"] >= 5), "ews_warning"] = True
#|
#|    # 이미 고장 확정(final_fault)인 날은 EWS 경고는 별도로 끈다
#|    out.loc[out["final_fault"], "ews_warning"] = False
#|    return out
#|
#|
#|def _compute_site_events(out: pd.DataFrame) -> pd.DataFrame:
#|    # ===== Site event day (soft/hard) + reason =====
#|    # Goal: protect ops from site-wide irradiance/weather/comm events.
#|    # Uses only per-day aggregates available in `out`.
#|    def _site_event_reason_for_day(g: pd.DataFrame) -> tuple[bool, bool, str]:
#|        reasons = []
#|
#|        # 1) peer energy collapse proxy (mid_peer very low)
#|        mid_peer_med = float(np.nanmedian(g["mid_peer"].to_numpy())) if len(g) else np.nan
#|        if np.isfinite(mid_peer_med) and mid_peer_med < 0.35:
#|            reasons.append("peer_peak_low")
#|
#|        # 2) widespread low concurrence proxy
#|        co_med = float(np.nanmedian(g["co_drop_frac"].fillna(0.0).to_numpy())) if len(g) else 0.0
#|        if np.isfinite(co_med) and co_med >= 0.45:
#|            reasons.append("co_drop_surge")
#|
#|        # 3) degraded surge
#|        deg_frac = float(np.mean(g["degraded_candidate"].fillna(False).to_numpy(dtype=bool))) if len(g) else 0.0
#|        if deg_frac >= 0.35:
#|            reasons.append("degraded_ratio_surge")
#|
#|        # 4) shadow-like surge
#|        sh_frac = float(np.mean(g["shadow_like"].fillna(False).to_numpy(dtype=bool))) if len(g) else 0.0
#|        if sh_frac >= 0.35:
#|            reasons.append("shadow_like_surge")
#|
#|        soft = len(reasons) > 0
#|
#|        # hard condition: peer collapse OR extreme concurrence OR extreme surge
#|        hard = False
#|        if ("peer_peak_low" in reasons) or (co_med >= 0.60) or (deg_frac >= 0.60):
#|            hard = True
#|
#|        return soft, hard, ";".join(reasons)
#|
#|    # compute day-wise flags (pandas groupby.apply FutureWarning-safe)
#|    def _day_flags_apply(df: pd.DataFrame) -> pd.DataFrame:
#|        try:
#|            # pandas newer versions
#|            return df.groupby("date", group_keys=False).apply(
#|                lambda g: pd.Series(
#|                    _site_event_reason_for_day(g),
#|                    index=["site_event_soft", "site_event_hard", "site_event_reason"],
#|                ),
#|                include_groups=False,
#|            )
#|        except TypeError:
#|            # pandas older versions (no include_groups)
#|            return df.groupby("date", group_keys=False).apply(
#|                lambda g: pd.Series(
#|                    _site_event_reason_for_day(g),
#|                    index=["site_event_soft", "site_event_hard", "site_event_reason"],
#|                )
#|            )
#|
#|    day_flags = _day_flags_apply(out)
#|    out = out.merge(day_flags, left_on="date", right_index=True, how="left")
#|    out["site_event_soft"] = out["site_event_soft"].fillna(False).astype(bool)
#|    out["site_event_hard"] = out["site_event_hard"].fillna(False).astype(bool)
#|    out["site_event_reason"] = out["site_event_reason"].fillna("").astype(str)
#|    return out
#|
#|
#|def main():
#|    args = parse_args()
#|
#|    # ---- Reproducibility ----
#|    seed = int(getattr(args, "seed", 42))
#|    np.random.seed(seed)
#|    try:
#|        import random
#|        random.seed(seed)
#|    except Exception:
#|        pass
#|    try:
#|        torch.manual_seed(seed)
#|        if torch.cuda.is_available():
#|            torch.cuda.manual_seed_all(seed)
#|        # Best-effort determinism (may have perf impact)
#|        torch.backends.cudnn.deterministic = True
#|        torch.backends.cudnn.benchmark = False
#|    except Exception:
#|        pass
#|
#|    data_dir, out_dir, log_dir, site, train_files, eval_files = _setup_paths(args, seed)
#|
#|    peer_mode = str(getattr(args, "peer_mode", "median")).strip().lower()
#|    peer_quantile = float(getattr(args, "peer_quantile", 0.80))
#|    peer_ref_panel = str(getattr(args, "peer_ref_panel", "")).strip()
#|    pmax_info_csv = str(getattr(args, "pmax_info_csv", "")).strip()
#|    if not np.isfinite(peer_quantile):
#|        raise RuntimeError(f"invalid --peer-quantile: {peer_quantile}")
#|    if peer_quantile < 0.0 or peer_quantile > 1.0:
#|        raise RuntimeError(f"--peer-quantile must be in [0,1], got {peer_quantile}")
#|
#|    panel_pmax_map: Dict[str, float] = {}
#|    panel_ids_seen: List[str] = []
#|    if pmax_info_csv or peer_mode == "ref":
#|        panel_ids_seen = _collect_panel_ids_from_files(train_files + eval_files)
#|        if peer_mode == "ref":
#|            if not peer_ref_panel:
#|                raise RuntimeError("--peer-mode ref requires --peer-ref-panel <panel_id>")
#|            if peer_ref_panel not in set(panel_ids_seen):
#|                raise RuntimeError(f"--peer-ref-panel not found in train/eval period: {peer_ref_panel}")
#|        if pmax_info_csv:
#|            panel_pmax_map = _build_panel_pmax_map_for_panels(pmax_info_csv, panel_ids_seen)
#|            print(f"[INFO] Pmax normalization enabled: mapped {len(panel_pmax_map)} panels from {pmax_info_csv}")
#|
#|    # ===== Build train-only voltage-bin map (vbin) for stable group references =====
#|    # This prevents mixed-string designs from inflating v_ref_span and forcing legacy critical.
#|    vbin_map: dict[str, int] = {}
#|    vbin_diag: dict[str, any] = {}
#|    try:
#|        vbin_map, vbin_diag = build_vbin_map_from_train(
#|            train_files=train_files,
#|            critical_peer_min=float(args.critical_peer_min),
#|            mid_peer_alive_thr=float(args.mid_peer_alive_thr),
#|            mid_ratio_dead_thr=float(args.mid_ratio_dead_thr),
#|            coverage_min=float(args.coverage_min),
#|            panel_pmax_map=panel_pmax_map,
#|            peer_mode=peer_mode,
#|            peer_quantile=peer_quantile,
#|            peer_ref_panel=peer_ref_panel,
#|        )
#|        # Persist for reproducibility
#|        (log_dir / "vbin_map.json").write_text(
#|            json.dumps(vbin_map, ensure_ascii=False, indent=2), encoding="utf-8"
#|        )
#|        (log_dir / "vbin_diag.json").write_text(
#|            json.dumps(vbin_diag, ensure_ascii=False, indent=2), encoding="utf-8"
#|        )
#|        print(f"[OK] wrote vbin_map.json (n={len(vbin_map)}) and vbin_diag.json")
#|    except Exception as e:
#|        print(f"[WARN] failed to build vbin_map (will run without vbin split): {e}")
#|        vbin_map = {}
#|
#|    # ===== AE 학습 (정상 기간) =====
#|    X_train: List[np.ndarray] = []
#|    train_index: List[Tuple[str, str]] = []
#|    train_curves_by_pid: Dict[str, List[np.ndarray]] = {}
#|
#|    for p in tqdm(train_files, desc="train-curves"):
#|        curves = load_day_curves(
#|            p,
#|            peer_eps=float(args.peer_eps),
#|            use_log_ratio=bool(args.use_log_ratio),
#|            panel_pmax_map=panel_pmax_map,
#|            peer_mode=peer_mode,
#|            peer_quantile=peer_quantile,
#|            peer_ref_panel=peer_ref_panel,
#|        )
#|        fname = p.name
#|        for pid, curve in curves.items():
#|            X_train.append(curve)
#|            train_index.append((fname, pid))
#|            train_curves_by_pid.setdefault(pid, []).append(curve)
#|
#|    if not X_train:
#|        raise RuntimeError("no training curves")
#|
#|    X_train_mat = np.vstack(X_train)
#|    # Compute global and per-panel reference curves
#|    global_ref_curve = np.median(X_train_mat, axis=0)
#|    panel_ref: Dict[str, np.ndarray] = {}
#|    for pid, lst in train_curves_by_pid.items():
#|        panel_ref[pid] = np.median(np.vstack(lst), axis=0)
#|
#|    device = args.device
#|
#|    model, train_err = train_ae(X_train_mat, args.latent, args.epochs, device)
#|    ae_thr_ae = float(np.quantile(train_err, 1.0 - args.contam))
#|
#|    # ===== 평가 (고장 후보 기간) =====
#|    rows = []
#|    with torch.no_grad():
#|        for p in tqdm(eval_files, desc="eval"):
#|            csv_path = p
#|            fname = p.name
#|
#|            # 이벤트 feature 계산
#|            ev_map = compute_event_features(
#|                csv_path,
#|                drop_thr=args.drop_thr,
#|                sustain_thr=args.sustain_thr,
#|                recovered_consec=int(args.recovered_consec),
#|                recovered_sustain_mins=int(args.recovered_sustain_mins),
#|                co_drop_thr=float(args.shadow_co_drop_thr),
#|                daylight_event_thr=float(getattr(args, "daylight_event_thr", 0.2)),
#|                peer_eps=float(args.peer_eps),
#|                panel_pmax_map=panel_pmax_map,
#|                peer_mode=peer_mode,
#|                peer_quantile=peer_quantile,
#|                peer_ref_panel=peer_ref_panel,
#|            )
#|
#|            curves = load_day_curves(
#|                csv_path,
#|                peer_eps=float(args.peer_eps),
#|                use_log_ratio=bool(args.use_log_ratio),
#|                panel_pmax_map=panel_pmax_map,
#|                peer_mode=peer_mode,
#|                peer_quantile=peer_quantile,
#|                peer_ref_panel=peer_ref_panel,
#|            )
#|            for pid, curve in curves.items():
#|                x = torch.tensor(curve[None, :], dtype=torch.float32).to(device)
#|                rec = model(x).cpu().numpy()[0]
#|                recon_err = float(np.mean((curve - rec) ** 2))
#|
#|                ev = ev_map.get(str(pid), {})
#|                ev_vals = _extract_event_values(ev)
#|
#|                is_ae_abn = recon_err >= ae_thr_ae
#|                is_ae_strong = recon_err >= (args.recon_mult * ae_thr_ae)
#|
#|                # --- DTW & HS ---
#|                ref_curve = panel_ref.get(pid, global_ref_curve)
#|                band = int(args.dtw_band)
#|                dtw = float(dtw_distance(curve, ref_curve, band=None if band <= 0 else band))
#|                hs = float(compute_hs(curve))
#|
#|                # --- V-drop reference & labels are computed AFTER dataframe-level v_ref merge ---
#|
#|                # (Remove per-row cache to avoid duplicate computation / label overwrite.)
#|
#|                group_key = panel_group_key(pid)
#|
#|                vbin = vbin_map.get(pid, 0)
#|
#|                group_key_ref = f"{group_key}.v{vbin}"
#|
#|
#|                # Placeholders (computed post-merge)
#|                v_ref = np.nan
#|                v_ref_span = np.nan
#|                n_ref = np.nan
#|                n_total = np.nan
#|                v_ref_ok = False
#|                v_drop = np.nan
#|
#|
#|                # Assemble output row with required fields
#|                rows.append(
#|                    {
#|                        "date": extract_date_from_filename(fname),
#|                        "panel_id": str(pid),
#|                        "v_ref_ok": v_ref_ok,
#|                        "v_drop": v_drop,
#|                        "v_ref": v_ref,
#|                        "v_ref_span": v_ref_span,
#|                        "n_ref": n_ref,
#|                        "n_total": n_total,
#|                        "group_key_ref": group_key_ref,
#|                        "recon_error": recon_err,
#|                        "ae_thr_used": ae_thr_ae,
#|                        "drop_time": ev_vals["drop_time"],
#|                        "sustain_mins": ev_vals["sustain_mins"],
#|                        "recovered": ev_vals["recovered"],
#|                        "last_ratio": ev_vals["last_ratio"],
#|                        "last_peer": ev_vals["last_peer"],
#|                        "mid_ratio": ev_vals["mid_ratio"],
#|                        "mid_peer": ev_vals["mid_peer"],
#|                        "mid_v_ratio": ev_vals["mid_v_ratio"],
#|                        "mid_i_ratio": ev_vals["mid_i_ratio"],
#|                        "coverage": ev_vals["coverage"],
#|                        "co_drop_frac": ev_vals["co_drop_frac"],
#|                        "is_ae_abn": bool(is_ae_abn),
#|                        "is_ae_strong": bool(is_ae_strong),
#|                        "source_csv": fname,
#|                        "dtw_dist": dtw,
#|                        "hs_score": hs,
#|                        "recovered_any": ev_vals["recovered_any"],
#|                        "recovered_sustained": ev_vals["recovered_sustained"],
#|                        "re_drop": ev_vals["re_drop"],
#|                        "coverage_mid": ev_vals["coverage_mid"],
#|                        "seg_count": ev_vals["seg_count"],
#|                        "total_low_mins": ev_vals["total_low_mins"],
#|                        "min_ratio": ev_vals["min_ratio"],
#|                        "p10_ratio": ev_vals["p10_ratio"],
#|                        "p50_ratio": ev_vals["p50_ratio"],
#|                        "low_area": ev_vals["low_area"],
#|                    }
#|                )
#|
#|    out = pd.DataFrame(rows)
#|    # Normalize date to midnight to avoid merge key mismatches
#|    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.normalize()
#|    out["drop_time"] = pd.to_datetime(out["drop_time"], errors="coerce")
#|
#|    cov_min = float(args.coverage_min)
#|    tuning_level = str(getattr(args, "tuning_level", "p2")).lower().strip()
#|    if tuning_level not in {"p0", "p1", "p2"}:
#|        tuning_level = "p2"
#|    print(f"[INFO] tuning_level = {tuning_level}")
#|    print(f"[INFO] daylight_event_thr = {float(getattr(args, 'daylight_event_thr', 0.2))}")
#|    print("[INFO] segment-labeling: confirmed_fault/critical_fault now mark whole sustained segments (not only tail days)")
#|
#|    # rule-based flags
#|    out["event_A"] = out["drop_time"].notna() & (out["sustain_mins"] >= int(args.event_sustain_mins))
#|    out["data_bad"] = (out["coverage"] < cov_min) | (out["coverage_mid"].fillna(0.0) < cov_min)
#|
#|    # ---- Group-aware V reference and relative V-drop (for critical_like) ----
#|    # Goal: derive a per-(date, group_key) voltage reference from good rows, then compute
#|    #       v_drop = 1 - (mid_v_ratio / v_ref).
#|    # Key requirement: NEVER crash when v_ref is unavailable. Always keep `v_ref` column.
#|
#|    # Base group_key (string-like) from panel_id
#|    out["group_key_base"] = out["panel_id"].astype(str).map(panel_group_key)
#|
#|    # vbin-aware group_key: split base group when train-only medians show mixed voltage levels.
#|    # IMPORTANT: vbin is fixed from TRAIN only to avoid leakage and day-to-day instability.
#|    if isinstance(vbin_map, dict) and len(vbin_map) > 0:
#|        vb = out["panel_id"].astype(str).map(lambda s: vbin_map.get(str(s), 0)).astype(int)
#|        out["vbin"] = vb
#|        out["group_key"] = out["group_key_base"].astype(str) + ".v" + vb.astype(str)
#|    else:
#|        out["vbin"] = 0
#|        out["group_key"] = out["group_key_base"].astype(str)
#|
#|    # A안 적용: v_ref(전압 참조)는 vbin까지 포함한 group_key 단위로 계산한다.
#|    # 이유: base group_key_ref(=uuid.string) 안에 서로 다른 설계/MPPT 전압 스트링이 섞이면
#|    #       v_ref_span이 폭발하고 v_ref_ok가 막혀 v_drop 판정이 불안정해진다.
#|    # 따라서 v_ref를 (date, group_key=vbin 포함) 기준으로 산출/적용하여 혼선을 제거한다.
#|    out["group_key_ref"] = out["group_key"].astype(str)
#|
#|    # Ensure n_total is always available for downstream v_ref_ok logic and for CSV outputs.
#|    # n_total = number of unique panels per (date, group_key). Always recompute from the raw rows
#|    # so it is never missing even when v_ref is unavailable.
#|    out["n_total"] = out.groupby(["date", "group_key"])["panel_id"].transform("nunique").astype(float)
#|
#|    # If this script is re-run in an interactive environment, or if the dataframe is
#|    # processed twice by accident, prior merge artifacts can remain and cause pandas
#|    # suffixes (_x/_y), which then breaks downstream v_ref_span selection and can leave
#|    # v_drop as all-NaN. Clean them up before recomputing.
#|    _merge_artifact_cols = [
#|        c for c in out.columns
#|        if (
#|            c.startswith("v_ref_tmp")
#|            or c.startswith("v_p10_grp")
#|            or c.startswith("v_p90_grp")
#|            or c.startswith("v_ref_span_grp")
#|        )
#|    ]
#|    if _merge_artifact_cols:
#|        out = out.drop(columns=_merge_artifact_cols)
#|
#|    # Always materialize columns up-front to avoid KeyError in any branch.
#|    # IMPORTANT: v_ref/v_drop must preserve NaN when unusable.
#|    # Setting v_drop=0.0 on missing v_ref hides data-quality issues and can cause unintended fallback behaviour.
#|    out["v_ref"] = pd.to_numeric(out.get("v_ref", np.nan), errors="coerce")
#|    out["v_drop"] = np.nan
#|    out["v_ref_span"] = np.nan  # group-level span only (avoid merge collisions)
#|    out["n_ref"] = np.nan
#|    out["no_ref"] = False
#|
#|    # Convenience flag: whether v_ref is usable for v_drop evaluation.
#|    # NOTE: v_ref_ok MUST be recomputed after v_ref is derived (merge step below).
#|    out["v_ref_ok"] = out["v_ref"].notna() & (out["v_ref"] >= float(args.v_ref_min))
#|
#|    if tuning_level == "p2":
#|        # For building v_ref only, we must not over-gate by mid_peer.
#|        # Gangui finding: clear-day mid_peer can sit around ~0.4 depending on daylight/mid-window definition.
#|        # Use a slightly more permissive peer threshold ONLY for v_ref computation (no leakage; still uses eval-day rows).
#|        vref_peer_min = min(float(args.mid_peer_alive_thr), 0.35)
#|        # Exclude near-dead/off panels from V reference computation.
#|        # Otherwise a panel/string OFF event can leak into v_ref and distort v_drop.
#|        dead_like_tmp = (
#|            (~out["data_bad"].astype(bool))
#|            & (out["mid_peer"] >= float(vref_peer_min))
#|            & (out["mid_ratio"] <= float(args.mid_ratio_dead_thr))
#|        )
#|
#|        base_mask = (
#|            (~out["data_bad"].astype(bool))
#|            & (out["mid_peer"] >= float(vref_peer_min))
#|            & (np.isfinite(out["mid_v_ratio"]))
#|            & (~dead_like_tmp)
#|        )
#|
#|        if base_mask.any():
#|            # Robust healthy-cluster v_ref: use upper cluster to avoid low-V contamination
#|            def _vref_robust_stats(x: pd.Series) -> pd.Series:
#|                xx = pd.to_numeric(x, errors="coerce").astype(float)
#|                xx = xx[np.isfinite(xx)]
#|                if len(xx) == 0:
#|                    return pd.Series({"v_ref_tmp": np.nan, "v_p10_grp": np.nan, "v_p90_grp": np.nan, "n_ref": 0})
#|
#|                # Use the upper cluster as the reference (protect against low-V fault contamination)
#|                # Keep it simple and deterministic: filter by an upper quantile then take median.
#|                q = float(np.nanquantile(xx, 0.60))
#|                xh = xx[xx >= q]
#|                if len(xh) < 2:
#|                    xh = xx  # fallback when too few remain
#|
#|                return pd.Series({
#|                    "v_ref_tmp": float(np.nanmedian(xh)),
#|                    "v_p10_grp": float(np.nanquantile(xh, 0.10)) if len(xh) > 0 else np.nan,
#|                    "v_p90_grp": float(np.nanquantile(xh, 0.90)) if len(xh) > 0 else np.nan,
#|                    "n_ref": int(len(xh)),
#|                })
#|
#|            # NOTE: pandas groupby.apply with `as_index=False` can produce length/index
#|            # mismatches when the applied function returns a Series. Use groupby.apply
#|            # (without as_index=False) and reset_index safely.
#|            v_ref_tbl = (
#|                out.loc[base_mask]
#|                .groupby(["date", "group_key_ref"])
#|                .apply(lambda g: _vref_robust_stats(g["mid_v_ratio"]))
#|                .reset_index()
#|            )
#|            v_ref_tbl["v_ref_span_grp"] = v_ref_tbl["v_p90_grp"] - v_ref_tbl["v_p10_grp"]
#|            # dtype guards (avoid object columns after apply)
#|            for c in ["v_ref_tmp", "v_p10_grp", "v_p90_grp", "v_ref_span_grp", "n_ref"]:
#|                if c in v_ref_tbl.columns:
#|                    v_ref_tbl[c] = pd.to_numeric(v_ref_tbl[c], errors="coerce")
#|
#|            # Normalize date for safe merge (guard against time components)
#|            v_ref_tbl["date"] = pd.to_datetime(v_ref_tbl["date"], errors="coerce").dt.normalize()
#|
#|            # Persist v_ref table for debugging/ops visibility
#|            try:
#|                v_ref_tbl.to_csv(log_dir / "v_ref_tbl.csv", index=False)
#|                print(f"[OK] wrote v_ref_tbl.csv (n={len(v_ref_tbl)})")
#|                print("[DBG] v_ref_tbl rows by date (top 10):")
#|                print(v_ref_tbl.groupby(v_ref_tbl["date"].dt.date).size().sort_values(ascending=False).head(10).to_string())
#|            except Exception as e:
#|                print(f"[WARN] failed to write v_ref_tbl.csv: {e}")
#|
#|            # Merge with a TEMP column name to avoid pandas suffix traps.
#|            if len(v_ref_tbl) > 0:
#|                # Extra guard: normalize out["date"] before merge (in case other code paths modified it)
#|                out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.normalize()
#|                out = out.merge(v_ref_tbl, on=["date", "group_key_ref"], how="left")
#|
#|                # Recover v_ref_tmp even if pandas added suffixes.
#|                if "v_ref_tmp" not in out.columns:
#|                    for cand in ["v_ref_tmp_y", "v_ref_tmp_x"]:
#|                        if cand in out.columns:
#|                            out["v_ref_tmp"] = out[cand]
#|                            break
#|
#|                # Choose the best available span column by non-null count.
#|                span_candidates = [c for c in out.columns if c.startswith("v_ref_span_grp")]
#|                span_col = None
#|                if span_candidates:
#|                    nn = {c: int(pd.to_numeric(out[c], errors="coerce").notna().sum()) for c in span_candidates}
#|                    span_col = max(nn, key=nn.get)
#|
#|                # Capture n_ref column name (may be suffixed after merges)
#|                nref_col = None
#|                for cand in ["n_ref", "n_ref_y", "n_ref_x"]:
#|                    if cand in out.columns:
#|                        nref_col = cand
#|                        break
#|
#|                if "v_ref_tmp" in out.columns:
#|                    # Stable, non-suffixed outputs
#|                    out["v_ref"] = pd.to_numeric(out["v_ref_tmp"], errors="coerce")
#|                    out["n_ref"] = pd.to_numeric(out[nref_col], errors="coerce") if nref_col is not None else np.nan
#|                    # Keep n_total stable: recompute from rows (do not trust merge artifacts).
#|                    out["n_total"] = out.groupby(["date", "group_key"])["panel_id"].transform("nunique").astype(float)
#|
#|                    if span_col is not None:
#|                        out["v_ref_span"] = pd.to_numeric(out[span_col], errors="coerce")
#|                    else:
#|                        out["v_ref_span"] = np.nan
#|
#|                    # v_ref_ok: usable v_ref AND stable group span AND enough reference panels
#|                    v_ref_min_n = int(getattr(args, "v_ref_min_n", 6))
#|                    span_ok = out["v_ref_span"].notna() & (out["v_ref_span"] <= float(args.v_ref_vspan_max))
#|
#|                    # Adaptive min-N based on reference-bin availability within (date, group_key_ref)
#|                    # (i.e., how many v1 panels exist to form a stable voltage reference).
#|                    v_ref_min_n = int(getattr(args, "v_ref_min_n", 6))
#|                    required_n = out["n_total"].apply(lambda x: max(2, min(v_ref_min_n, int(x))) if pd.notna(x) else v_ref_min_n)
#|                    n_ok = out["n_ref"].notna() & (out["n_ref"] >= required_n)
#|                    out["v_ref_ok"] = out["v_ref"].notna() & (out["v_ref"] >= float(args.v_ref_min)) & span_ok & n_ok
#|
#|                    # no_ref: reference not available or too small (ops visibility)
#|                    out["no_ref"] = out["v_ref"].isna() | (~n_ok)
#|
#|                    # Drop merge helper columns (including any suffixed variants)
#|                    drop_cols = []
#|                    for c in [
#|                        "v_ref_tmp", "v_ref_tmp_x", "v_ref_tmp_y",
#|                        "v_p10_grp", "v_p10_grp_x", "v_p10_grp_y",
#|                        "v_p90_grp", "v_p90_grp_x", "v_p90_grp_y",
#|                        "n_ref_x", "n_ref_y",
#|                        "v_ref_span_grp", "v_ref_span_grp_x", "v_ref_span_grp_y",
#|                    ]:
#|                        # Keep stable output columns `n_ref` and `n_total`; drop only temporary/suffixed merge helpers.
#|                        if c in out.columns and c not in {"n_ref", "n_total"}:
#|                            drop_cols.append(c)
#|                    if drop_cols:
#|                        out = out.drop(columns=drop_cols)
#|
#|                    # Compute relative V-drop using group reference.
#|                    # Keep NaN when v_ref is missing/unusable; do NOT default to 0.0.
#|                    out["v_drop"] = np.nan
#|
#|                    # Ensure numeric dtypes (avoid silent all-False masks when objects sneak in)
#|                    out["mid_v_ratio"] = pd.to_numeric(out["mid_v_ratio"], errors="coerce")
#|                    out["v_ref"] = pd.to_numeric(out["v_ref"], errors="coerce")
#|
#|                    drop_mask = (
#|                        out["v_ref"].notna()
#|                        & out["mid_v_ratio"].notna()
#|                        & np.isfinite(out["mid_v_ratio"].to_numpy(dtype=float))
#|                        & np.isfinite(out["v_ref"].to_numpy(dtype=float))
#|                        & (out["v_ref"] > 0)
#|                    )
#|                    out.loc[drop_mask, "v_drop"] = 1.0 - (
#|                        out.loc[drop_mask, "mid_v_ratio"].astype(float)
#|                        / out.loc[drop_mask, "v_ref"].astype(float)
#|                    )
#|                    # Safety: n_total must never be missing.
#|                    out["n_total"] = out.groupby(["date", "group_key"])["panel_id"].transform("nunique").astype(float)
#|
#|    out["state_dead"] = (
#|        (~out["data_bad"])
#|        & (out["mid_peer"] >= float(args.mid_peer_alive_thr))
#|        & (out["mid_ratio"] <= float(args.mid_ratio_dead_thr))
#|    )
#|
#|    # ---- Stage gating (p0/p1/p2) ----
#|    # p0: dead/confirmed only (no group_off gate, no critical/shadow/EWS)
#|    # p1: +group_off_like gate (still no critical/shadow/EWS)
#|    # p2: full (critical_like + group_off_like + downstream refinement)
#|
#|    # ---- Ops visibility: why a row is low-trust (suspect) ----
#|    # Derived from FINAL (post-merge) trust-gate components.
#|    if "vdrop_trust_reason" not in out.columns:
#|        out["vdrop_trust_reason"] = ""
#|
#|    try:
#|        v_ref_min_n = int(getattr(args, "v_ref_min_n", 6))
#|        v_ref_min = float(getattr(args, "v_ref_min", 0.30))
#|        v_ref_vspan_max = float(getattr(args, "v_ref_vspan_max", 0.12))
#|
#|        n_ref_s = pd.to_numeric(out.get("n_ref", np.nan), errors="coerce")
#|        v_ref_s = pd.to_numeric(out.get("v_ref", np.nan), errors="coerce")
#|        vspan_s = pd.to_numeric(out.get("v_ref_span", np.nan), errors="coerce")
#|
#|        # Match the adaptive required_n logic used in v_ref_ok computation.
#|        required_n = n_ref_s.apply(
#|            lambda x: (max(2, min(v_ref_min_n, int(x))) if pd.notna(x) else v_ref_min_n)
#|        )
#|
#|        low_vref = v_ref_s.isna() | (~np.isfinite(v_ref_s.to_numpy(dtype=float))) | (v_ref_s < v_ref_min)
#|        high_vspan = vspan_s.isna() | (~np.isfinite(vspan_s.to_numpy(dtype=float))) | (vspan_s > v_ref_vspan_max)
#|        low_nref = n_ref_s.isna() | (~np.isfinite(n_ref_s.to_numpy(dtype=float))) | (n_ref_s < required_n)
#|
#|        # Build reason strings (order-stable)
#|        r = np.where(low_vref, "low_v_ref", "")
#|        r = np.where(high_vspan, np.where(r != "", r + "+high_vspan", "high_vspan"), r)
#|        r = np.where(low_nref, np.where(r != "", r + "+low_n_ref", "low_n_ref"), r)
#|
#|        # Only keep reason when FINAL trust is low (suspect); else keep blank.
#|        out["vdrop_trust_reason"] = np.where(out["v_ref_ok"].fillna(False).astype(bool), "", r)
#|    except Exception as _e:
#|        # Never fail the pipeline due to a diagnostics column.
#|        out["vdrop_trust_reason"] = ""
#|
#|    # critical labels are finalized after group_off_like is known.
#|
#|    out["group_off_date"] = False
#|    out["group_off_like"] = False
#|    out["group_off_group"] = False
#|
#|    if tuning_level in {"p1", "p2"}:
#|        out = _detect_group_off(out, args)
#|
#|    # Effective dead for panel-fault confirmation
#|    # p0: no group_off gating
#|    # p1/p2: exclude group_off_like days
#|    if tuning_level == "p0":
#|        out["state_dead_eff"] = out["state_dead"].astype(bool)
#|    else:
#|        out["state_dead_eff"] = out["state_dead"].astype(bool) & (~out["group_off_like"].astype(bool))
#|
#|    # Final critical labels (SSOT): define once after group_off_like is known.
#|    out = compute_vdrop_labels(
#|        out,
#|        {
#|            "args": args,
#|            "tuning_level": tuning_level,
#|        },
#|    )
#|
#|    # dead streak and confirmed fault (always computed)
#|    out = out.sort_values(["panel_id", "date"])
#|    out["dead_streak"] = compute_run_streak(out["panel_id"], out["state_dead_eff"])
#|    # Mark whole dead-like segments when they reach the minimum length (ops-friendly)
#|    out = mark_run_segments(out, key_col="panel_id", date_col="date", cond_col="state_dead_eff", min_len=int(args.dead_days), out_col="confirmed_fault")
#|
#|    # ---- Critical-like (V-drop sustained run) ----
#|    out["crit_streak"] = 0
#|    out["critical_fault"] = False
#|
#|    if tuning_level == "p2":
#|        # ---- Critical-like streak ----
#|        out["crit_streak"] = compute_run_streak(out["panel_id"], out["critical_like_eff"])
#|        # Mark whole critical-like segments when they reach the minimum length (ops-friendly)
#|        out = mark_run_segments(out, key_col="panel_id", date_col="date", cond_col="critical_like_eff", min_len=int(args.critical_days), out_col="critical_fault")
#|
#|    # ===== critical 2-stage split (confirmed vs suspect) =====
#|    # Compute after `critical_fault` is available.
#|    out["critical_confirmed"] = False
#|    out["critical_suspect"] = False
#|    # Ops-friendly stage label (none/like/suspect/confirmed)
#|    out["critical_stage"] = "none"
#|
#|    if tuning_level == "p2":
#|        crit_rows = out[(out["critical_fault"] == True) & (out["mid_peer"] >= float(args.critical_peer_min))].copy()
#|        if len(crit_rows) > 0:
#|            g = (crit_rows.groupby("panel_id")
#|                         .agg(days=("date", "nunique"),
#|                              v_p10=("mid_v_ratio", lambda x: x.quantile(0.10)),
#|                              v_p90=("mid_v_ratio", lambda x: x.quantile(0.90)))
#|                         .reset_index())
#|            g["v_span"] = g["v_p90"] - g["v_p10"]
#|
#|            confirmed_panels = set(
#|                g[(g["days"] >= int(args.critical_min_days)) & (g["v_span"] <= float(args.critical_vspan_max))]["panel_id"].astype(str).tolist()
#|            )
#|            suspect_panels = set(
#|                g[(g["days"] >= int(args.critical_min_days)) & (g["v_span"] > float(args.critical_vspan_max))]["panel_id"].astype(str).tolist()
#|            )
#|
#|            out.loc[out["panel_id"].astype(str).isin(confirmed_panels) & (out["critical_fault"] == True), "critical_confirmed"] = True
#|            out.loc[out["panel_id"].astype(str).isin(suspect_panels) & (out["critical_fault"] == True), "critical_suspect"] = True
#|            # Stage labeling priority: confirmed > suspect > like
#|            out.loc[out["critical_like_eff"].astype(bool), "critical_stage"] = "like"
#|            out.loc[out["critical_suspect"].astype(bool), "critical_stage"] = "suspect"
#|            out.loc[out["critical_confirmed"].astype(bool), "critical_stage"] = "confirmed"
#|
#|    # final_fault
#|    if tuning_level == "p2":
#|        # Final fault should only use CONFIRMED critical (V/I-decomposed and stability-checked).
#|        # Anything else stays as critical_like / critical_suspect for downstream review.
#|        out["final_fault"] = out["confirmed_fault"] | out["critical_confirmed"]
#|    else:
#|        out["final_fault"] = out["confirmed_fault"]
#|
#|    # ---- Online diagnosis dates (panel-wise first confirmed day) ----
#|    # Keep date normalization explicit before first-true day extraction.
#|    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.normalize()
#|
#|    dead_days_thr = int(args.dead_days)
#|    critical_days_thr = int(args.critical_days)
#|
#|    out["dead_diag_on_day"] = (
#|        out["state_dead_eff"].fillna(False).astype(bool)
#|        & (pd.to_numeric(out["dead_streak"], errors="coerce").fillna(0) >= dead_days_thr)
#|    )
#|    dead_diag_first = (
#|        out.loc[out["dead_diag_on_day"], ["panel_id", "date"]]
#|        .groupby("panel_id", sort=False)["date"]
#|        .min()
#|    )
#|    out["dead_diag_date"] = out["panel_id"].map(dead_diag_first)
#|
#|    if tuning_level == "p2":
#|        out["critical_diag_on_day"] = (
#|            out["critical_like_eff"].fillna(False).astype(bool)
#|            & (pd.to_numeric(out["crit_streak"], errors="coerce").fillna(0) >= critical_days_thr)
#|        )
#|        critical_diag_first = (
#|            out.loc[out["critical_diag_on_day"], ["panel_id", "date"]]
#|            .groupby("panel_id", sort=False)["date"]
#|            .min()
#|        )
#|        out["critical_diag_date"] = out["panel_id"].map(critical_diag_first)
#|    else:
#|        out["critical_diag_on_day"] = False
#|        out["critical_diag_date"] = pd.NaT
#|        critical_diag_first = pd.Series(dtype="datetime64[ns]")
#|
#|    out["diagnosis_date_online"] = pd.concat(
#|        [
#|            pd.to_datetime(out["dead_diag_date"], errors="coerce"),
#|            pd.to_datetime(out["critical_diag_date"], errors="coerce"),
#|        ],
#|        axis=1,
#|    ).min(axis=1)
#|
#|    final_fault_first = (
#|        out.loc[out["final_fault"].fillna(False).astype(bool), ["panel_id", "date"]]
#|        .groupby("panel_id", sort=False)["date"]
#|        .min()
#|    )
#|    panel_diag = pd.DataFrame({"panel_id": out["panel_id"].astype(str).drop_duplicates()})
#|    panel_diag["dead_diag_date"] = panel_diag["panel_id"].map(dead_diag_first)
#|    panel_diag["critical_diag_date"] = panel_diag["panel_id"].map(critical_diag_first)
#|    panel_diag["diagnosis_date_online"] = pd.concat(
#|        [
#|            pd.to_datetime(panel_diag["dead_diag_date"], errors="coerce"),
#|            pd.to_datetime(panel_diag["critical_diag_date"], errors="coerce"),
#|        ],
#|        axis=1,
#|    ).min(axis=1)
#|    panel_diag["final_fault_first_date"] = panel_diag["panel_id"].map(final_fault_first)
#|    panel_diag["dead_days"] = dead_days_thr
#|    panel_diag["critical_days"] = critical_days_thr
#|    panel_diag["tuning_level"] = tuning_level
#|    panel_diag_path = out_dir / "panel_diagnosis_summary.csv"
#|    panel_diag.to_csv(panel_diag_path, index=False, encoding="utf-8-sig")
#|    print(f"[OK] wrote output: {panel_diag_path} (n={len(panel_diag)})")
#|
#|    # Sanity checks for critical label consistency after single-pass SSOT assignment.
#|    try:
#|        bad_overlap = int(
#|            (
#|                out["critical_like_raw"].astype(bool)
#|                & out["critical_like_suspect_raw"].astype(bool)
#|            ).sum()
#|        )
#|        if bad_overlap > 0:
#|            raise AssertionError(
#|                f"critical raw overlap detected (n={bad_overlap}); raw and suspect_raw must be exclusive"
#|            )
#|
#|        # Legacy path may legitimately bypass v_ref_ok; trust check applies to non-legacy rows only.
#|        leak_nonlegacy = int(
#|            (
#|                out["critical_like_eff"].astype(bool)
#|                & (~out["v_ref_ok"].fillna(False).astype(bool))
#|                & (~out["critical_like_legacy"].astype(bool))
#|            ).sum()
#|        )
#|        if leak_nonlegacy > 0:
#|            raise AssertionError(
#|                f"non-legacy critical leak detected with v_ref_ok==0 (n={leak_nonlegacy})"
#|            )
#|        print(f"[CHK] critical_raw_overlap = {bad_overlap}, nonlegacy_vref_leak = {leak_nonlegacy}")
#|    except Exception as _e:
#|        raise
#|
#|    # ---- Reports: confirmed vs suspect (after final critical labels are fixed) ----
#|    try:
#|        if tuning_level == "p2":
#|            rep_confirm = _max_run_by_panel(out, "critical_like")
#|            rep_suspect = _max_run_by_panel(out, "critical_like_suspect")
#|
#|            def _attach_ctx(df_run: pd.DataFrame, flag_col: str) -> pd.DataFrame:
#|                top_pids = df_run.loc[df_run[f"{flag_col}_max_run"] > 0, "panel_id"].astype(str).tolist()
#|                if not top_pids:
#|                    return df_run
#|                sub = out[out["panel_id"].astype(str).isin(top_pids)].copy()
#|                sub = sub.sort_values(["panel_id", "date"])
#|                ctx = (
#|                    sub.groupby("panel_id")
#|                    .tail(1)[
#|                        [
#|                            "panel_id",
#|                            "group_key_ref",
#|                            "n_ref",
#|                            "n_total",
#|                            "v_ref_span",
#|                            "mid_peer",
#|                            "mid_ratio",
#|                            "mid_v_ratio",
#|                            "v_drop",
#|                        ]
#|                    ]
#|                    .copy()
#|                )
#|                return df_run.merge(ctx, on="panel_id", how="left")
#|
#|            rep_confirm_ctx = _attach_ctx(rep_confirm, "critical_like")
#|            rep_suspect_ctx = _attach_ctx(rep_suspect, "critical_like_suspect")
#|
#|            ok_critical_reports = True
#|            ok_critical_reports &= _safe_report_write(
#|                rep_confirm_ctx,
#|                log_dir / "report_critical_confirmed_runs.csv",
#|                "report_critical_confirmed_runs(log)",
#|                index=False,
#|            )
#|            ok_critical_reports &= _safe_report_write(
#|                rep_suspect_ctx,
#|                log_dir / "report_critical_suspect_runs.csv",
#|                "report_critical_suspect_runs(log)",
#|                index=False,
#|            )
#|            ok_critical_reports &= _safe_report_write(
#|                rep_confirm_ctx,
#|                out_dir / "report_critical_confirmed_runs.csv",
#|                "report_critical_confirmed_runs(out)",
#|                index=False,
#|            )
#|            ok_critical_reports &= _safe_report_write(
#|                rep_suspect_ctx,
#|                out_dir / "report_critical_suspect_runs.csv",
#|                "report_critical_suspect_runs(out)",
#|                index=False,
#|            )
#|            if ok_critical_reports:
#|                print("[OK] wrote reports: report_critical_confirmed_runs.csv / report_critical_suspect_runs.csv")
#|
#|            print("\n[TOP] critical_like confirmed max_run (TOP40)")
#|            print(rep_confirm.head(40).to_string(index=False))
#|            print("\n[TOP] critical_like SUSPECT max_run (TOP40)")
#|            print(rep_suspect.head(40).to_string(index=False))
#|    except Exception as _e:
#|        print(f"[WARN] critical report generation failed: {_e}")
#|
#|    # helper flags for daily fault-like events and degraded candidates
#|    fault_sustain = 90            # minutes of sustained low ratio to consider the day fault-like
#|    fault_last_ratio_thr = 0.10   # if last_ratio <= 0.1, treated as nearly dead at end of day
#|    degraded_upper = 0.60         # upper bound for degraded mid_ratio (0.2 ~ 0.6)
#|
#|    out["fault_like_day"] = (
#|        (~out["data_bad"])
#|        & out["event_A"]
#|        & (out["sustain_mins"] >= fault_sustain)
#|        & (out["last_ratio"] <= fault_last_ratio_thr)
#|        & (out["mid_peer"] >= float(args.mid_peer_alive_thr))
#|    )
#|
#|    out["degraded_candidate"] = (
#|        (~out["data_bad"])
#|        & (~out["state_dead"])
#|        & (out["mid_peer"] >= float(args.mid_peer_alive_thr))
#|        & (out["mid_ratio"] > float(args.mid_ratio_dead_thr))
#|        & (out["mid_ratio"] <= degraded_upper)
#|    )
#|
#|    # shadow-like events (basic): degraded days that recovered at least once
#|    # NOTE: refined later using HS/DTW strengths to better match transient cloud/shading behaviour.
#|    out["shadow_like_basic"] = (
#|        (~out["data_bad"])
#|        & out["degraded_candidate"]
#|        & out["recovered_sustained"]
#|    )
#|
#|    # Refined shadow-like: require spatial concurrence OR segmented behaviour, and avoid near-dead patterns
#|    out["shadow_like"] = (
#|        out["shadow_like_basic"]
#|        & (
#|            (out["co_drop_frac"].fillna(0.0) >= float(args.shadow_co_drop_thr))
#|            | (out["seg_count"].fillna(0).astype(int) >= int(args.shadow_seg_min))
#|        )
#|        & (out["min_ratio"].fillna(1.0) >= float(args.shadow_min_ratio_floor))
#|    )
#|
#|    # Guard: group/string OFF events should not contaminate other event categories
#|    if "group_off_like" in out.columns:
#|        mask_go = out["group_off_like"].fillna(False).astype(bool)
#|        if mask_go.any():
#|            for col in ["fault_like_day", "degraded_candidate", "shadow_like_basic", "shadow_like"]:
#|                if col in out.columns:
#|                    out.loc[mask_go, col] = False
#|
#|    # textual anomaly level for easier downstream use
#|    out["anom_level"] = "normal"
#|    out.loc[out["degraded_candidate"], "anom_level"] = "degraded_or_shadow"
#|    out.loc[out["shadow_like"], "anom_level"] = "shadow_like"
#|    out.loc[out["fault_like_day"], "anom_level"] = "fault_like"
#|    out.loc[out["group_off_like"], "anom_level"] = "group_off_like"
#|    out.loc[out["final_fault"], "anom_level"] = "confirmed_fault"
#|
#|    # Layer 2: AE 기반 강도 / 서브타입 태깅
#|    # 날짜별 AE 재구성오차 분위수 (0~1)
#|    out["recon_rank_day"] = out.groupby("date")["recon_error"].rank(pct=True)
#|
#|    # AE 강도 수준
#|    out["ae_strength"] = "low"
#|    out.loc[out["recon_rank_day"] >= 0.7, "ae_strength"] = "mid"
#|    out.loc[out["recon_rank_day"] >= 0.9, "ae_strength"] = "high"
#|    # is_ae_strong=True인 경우는 무조건 high로 승격
#|    out.loc[out["is_ae_strong"], "ae_strength"] = "high"
#|
#|    # 이상 서브타입 태그
#|    out["anom_subtype"] = "normal"
#|    out.loc[out["group_off_like"], "anom_subtype"] = "group_off_event"
#|
#|    # shadow-like: 음영/날씨성 이벤트를 AE 강도 기준으로 세분화
#|    out.loc[out["shadow_like"] & (~out["is_ae_strong"]), "anom_subtype"] = "shadow_like_mild"
#|    out.loc[out["shadow_like"] & out["is_ae_strong"], "anom_subtype"] = "shadow_like_strong"
#|
#|    # 열화 후보: shadow_like로 이미 태깅된 패널은 제외하고, AE 강도로 구분
#|    out.loc[
#|        out["degraded_candidate"] & (~out["shadow_like"]) & (~out["is_ae_strong"]),
#|        "anom_subtype",
#|    ] = "degradation_mild"
#|    out.loc[
#|        out["degraded_candidate"] & (~out["shadow_like"]) & out["is_ae_strong"],
#|        "anom_subtype",
#|    ] = "degradation_strong"
#|
#|    # 하루 고장 패턴: fault-like day
#|    out.loc[
#|        out["fault_like_day"] & (~out["is_ae_strong"]),
#|        "anom_subtype",
#|    ] = "fault_like_weak"
#|    out.loc[
#|        out["fault_like_day"] & out["is_ae_strong"],
#|        "anom_subtype",
#|    ] = "fault_like_strong"
#|
#|    # 최종 confirmed fault는 항상 confirmed_fault로 override
#|    out.loc[out["confirmed_fault"], "anom_subtype"] = "confirmed_fault"
#|    out.loc[(out["critical_fault"]) & (~out["confirmed_fault"]), "anom_subtype"] = "critical_fault_vdrop"
#|
#|    # Layer 3: EWS(전조) 지표 – 4종 (mid_var, eventA_freq, dtw_mean, hs_mean)
#|    # 패널별 날짜 순으로 정렬 후 롤링 통계 계산
#|    out = out.sort_values(["panel_id", "date"])
#|    grp = out.groupby("panel_id", group_keys=False)
#|
#|    # 1) 기본 롤링 지표 4개
#|    out["ews_mid_var_7d"] = grp["mid_ratio"].transform(
#|        lambda s: s.rolling(window=7, min_periods=3).var()
#|    )
#|    out["ews_eventA_freq_7d"] = grp["event_A"].transform(
#|        lambda s: s.rolling(window=7, min_periods=3).mean()
#|    )
#|    out["ews_dtw_mean_7d"] = grp["dtw_dist"].transform(
#|        lambda s: s.rolling(window=7, min_periods=3).mean()
#|    )
#|    out["ews_hs_mean_7d"] = grp["hs_score"].transform(
#|        lambda s: s.rolling(window=7, min_periods=3).mean()
#|    )
#|
#|    # 2) 운영(인과성) 관점: 전역 임계값과 월별 베이스라인은 "과거 데이터"로만 산정
#|    #    - 날짜 d에서의 판단은 date < d 구간의 분포/베이스라인만 사용 (미래 데이터 누수 방지)
#|
#|    # ==== EXPORT: Save main output CSV with n_total defensively included ====
#|    # Ensure n_total is exported for ops/debug (number of panels per (date, group_key))
#|    if "n_total" not in out.columns:
#|        out["n_total"] = out.groupby(["date", "group_key"])["panel_id"].transform("nunique").astype(float)
#|
#|    # Define output columns (OUT_COLS): insert n_total after n_ref if present, else near v_ref-related cols
#|    OUT_COLS = [
#|        "date", "panel_id",
#|        "recon_error", "ae_thr_used",
#|        "drop_time", "sustain_mins", "recovered",
#|        "last_ratio", "last_peer",
#|        "mid_ratio", "mid_peer", "mid_v_ratio", "mid_i_ratio",
#|        "coverage", "co_drop_frac",
#|        "is_ae_abn", "is_ae_strong", "source_csv",
#|        "dtw_dist", "hs_score", "recovered_any", "recovered_sustained", "re_drop",
#|        "coverage_mid", "seg_count", "total_low_mins", "min_ratio", "p10_ratio", "p50_ratio", "low_area",
#|        "event_A", "data_bad",
#|        "group_key_base", "vbin", "group_key",
#|        "v_ref", "v_ref_span", "v_ref_ok", "n_ref",  # v_ref-related section
#|        # n_total will be inserted after n_ref or after v_ref-related cols below
#|        "no_ref", "v_drop",
#|        "state_dead", "state_dead_eff", "dead_streak", "confirmed_fault",
#|        "dead_diag_on_day", "dead_diag_date",
#|        "critical_like", "critical_like_eff", "crit_streak", "critical_fault", "critical_source",
#|        "critical_diag_on_day", "critical_diag_date", "diagnosis_date_online",
#|        "critical_confirmed", "critical_suspect", "final_fault",
#|        "group_off_date", "group_off_like", "group_off_group",
#|        "base_day_panel_count", "base_day_degraded_panel_count", "subgroup_common_cause_candidate",
#|        "fault_like_day", "degraded_candidate", "shadow_like_basic", "shadow_like",
#|        "anom_level", "recon_rank_day", "ae_strength", "anom_subtype",
#|        "ews_mid_var_7d", "ews_eventA_freq_7d", "ews_dtw_mean_7d", "ews_hs_mean_7d"
#|    ]
#|    # Insert n_total after n_ref if present, else after v_ref_ok, v_ref_span, or v_ref
#|    if "n_total" not in OUT_COLS:
#|        try:
#|            idx = OUT_COLS.index("n_ref") + 1
#|        except ValueError:
#|            # Try after v_ref_ok or v_ref_span or v_ref
#|            for key in ["v_ref_ok", "v_ref_span", "v_ref"]:
#|                if key in OUT_COLS:
#|                    idx = OUT_COLS.index(key) + 1
#|                    break
#|            else:
#|                idx = len(OUT_COLS)
#|        OUT_COLS.insert(idx, "n_total")
#|
#|    # Final save is performed once at the end of main().
#|
#|    out = _compute_ews(out, args)
#|    out = _compute_site_events(out)
#|
#|    # Gate: site event day should not produce EWS/prefault escalation.
#|    out.loc[out["site_event_soft"], "ews_warning"] = False
#|    out.loc[out["site_event_hard"], "ews_warning"] = False
#|    # Gate: group/string-level OFF events should not escalate into EWS/prefault
#|    out.loc[out["group_off_date"].astype(bool), "ews_warning"] = False
#|
#|    # ---- DTW/HS ranking and subtype refinement ----
#|    # 1) Add daily DTW and HS ranks
#|    out["dtw_rank_day"] = out.groupby("date")["dtw_dist"].rank(pct=True)
#|    out["hs_rank_day"] = out.groupby("date")["hs_score"].rank(pct=True)
#|
#|    # 2) Add categorical strengths
#|    out["dtw_strength"] = "low"
#|    out.loc[out["dtw_rank_day"] >= 0.7, "dtw_strength"] = "mid"
#|    out.loc[out["dtw_rank_day"] >= 0.9, "dtw_strength"] = "high"
#|    out["hs_strength"] = "low"
#|    out.loc[out["hs_rank_day"] >= 0.7, "hs_strength"] = "mid"
#|    out.loc[out["hs_rank_day"] >= 0.9, "hs_strength"] = "high"
#|
#|    # Refine shadow-like using HS/DTW strengths to better capture transient cloud/shading
#|    # - require turbulence (HS mid/high)
#|    # - avoid cases where the panel is strongly off its own reference (DTW high)
#|    # - require spatial concurrence (co_drop_frac >= co_drop_thr)
#|    out["shadow_like"] = (
#|        out["shadow_like_basic"].astype(bool)
#|        & out["hs_strength"].isin(["mid", "high"])
#|        & (~out["dtw_strength"].isin(["high"]))
#|        & (out["co_drop_frac"].fillna(0.0) >= float(args.shadow_co_drop_thr))
#|    )
#|
#|    # Update anom_level after refining shadow_like
#|    # (keep confirmed_fault highest priority)
#|    out.loc[out["shadow_like"], "anom_level"] = "shadow_like"
#|    out.loc[out["shadow_like_basic"] & (~out["shadow_like"]), "anom_level"] = "degraded_or_shadow"
#|    out.loc[out["final_fault"], "anom_level"] = "confirmed_fault"
#|
#|    # 3) Refine anom_subtype using DTW/HS
#|    # For shadow-like days
#|    out.loc[out["shadow_like"] & (out["hs_strength"] != "high"), "anom_subtype"] = "shadow_like_mild"
#|    out.loc[
#|        out["shadow_like"] & (out["hs_strength"] == "high") & (out["dtw_strength"].isin(["mid", "high"])),
#|        "anom_subtype"
#|    ] = "shadow_like_strong"
#|
#|    # For degraded candidates (excluding shadow_like and confirmed faults)
#|    mask_deg = out["degraded_candidate"] & (~out["shadow_like"]) & (~out["final_fault"])
#|    out.loc[
#|        mask_deg & (out["hs_strength"] == "low") & (out["dtw_strength"].isin(["low", "mid"])),
#|        "anom_subtype"
#|    ] = "degradation_steady"
#|    out.loc[
#|        mask_deg & (out["dtw_strength"] == "high"),
#|        "anom_subtype"
#|    ] = "degradation_strong"
#|
#|    # For fault-like days not yet final_fault
#|    mask_fault_like = out["fault_like_day"] & (~out["final_fault"])
#|
#|    # 기본값은 fault_like_weak으로 태깅
#|    out.loc[mask_fault_like, "anom_subtype"] = "fault_like_weak"
#|
#|    # DTW가 강하게 틀어지고, HS 난류가 너무 높지 않은 경우를 strong으로 승격
#|    out.loc[
#|        mask_fault_like
#|        & (out["dtw_strength"] == "high")
#|        & (out["hs_strength"].isin(["low", "mid"])),
#|        "anom_subtype"
#|    ] = "fault_like_strong"
#|
#|    # 4) Confirmed faults always override
#|    out.loc[out["final_fault"], "anom_subtype"] = "confirmed_fault"
#|
#|    # 최종 저장 전에는 다시 날짜+패널 기준 정렬
#|    out = out.sort_values(["date", "panel_id"])
#|
#|    # ===== Layer 4: 1.1-style pre-fault template engine (Option B, 엔진 1.0) =====
#|    # 최근 40일 기준으로 패널별 요약 지표를 만들고,
#|    # 1.1 패널에서 관찰된 패턴과 비슷한 경우를 "전조 후보"로 본다.
#|
#|    # 패널-날짜 순으로 한 번 더 정렬하고 그룹 생성
#|    out = out.sort_values(["panel_id", "date"])
#|    grp_pf = out.groupby("panel_id", group_keys=False)
#|
#|    # AE/DTW/HS mid 이상 여부를 0/1 플래그로 변환
#|    out["ae_mid_flag"] = out["ae_strength"].isin(["mid", "high"]).astype(float)
#|    out["dtw_mid_flag"] = out["dtw_strength"].isin(["mid", "high"]).astype(float)
#|
#|    # 최근 40일 롤링 윈도우 (일 데이터 기준), 최소 20일 이상 관측이 있을 때만 유효
#|    window = 40
#|    min_periods = 20
#|
#|    out["pf40_mid_mean"] = grp_pf["mid_ratio"].transform(
#|        lambda s: s.rolling(window=window, min_periods=min_periods).mean()
#|    )
#|    out["pf40_ae_ratio"] = grp_pf["ae_mid_flag"].transform(
#|        lambda s: s.rolling(window=window, min_periods=min_periods).mean()
#|    )
#|    out["pf40_dtw_ratio"] = grp_pf["dtw_mid_flag"].transform(
#|        lambda s: s.rolling(window=window, min_periods=min_periods).mean()
#|    )
#|    out["pf40_ews_ratio"] = grp_pf["ews_warning"].transform(
#|        lambda s: s.rolling(window=window, min_periods=min_periods).mean()
#|    )
#|
#|    # Option B 템플릿 임계값 (1.1 pre-fault 윈도우를 기준으로 잡은 보수적 구간)
#|    mid_low = 0.5      # 평균 mid_ratio가 너무 낮지도(완전 dead) 너무 높지도(완전 정상) 않은 구간
#|    mid_high = 0.9
#|    pf_ae_ratio_thr = 0.7    # 최근 40일 중 AE mid/high 비율
#|    pf_dtw_ratio_thr = 0.7   # 최근 40일 중 DTW mid/high 비율
#|    pf_ews_ratio_thr = 0.05  # 최근 40일 중 EWS_warning 비율 (대략 40일 중 2일 이상)
#|
#|    cond_mid = (out["pf40_mid_mean"] >= mid_low) & (out["pf40_mid_mean"] <= mid_high)
#|    cond_ae = out["pf40_ae_ratio"] >= pf_ae_ratio_thr
#|    cond_dtw = out["pf40_dtw_ratio"] >= pf_dtw_ratio_thr
#|    cond_ews = out["pf40_ews_ratio"] >= pf_ews_ratio_thr
#|    out["prefault_cond_mid"] = cond_mid.astype(bool)
#|    out["prefault_cond_ae"] = cond_ae.astype(bool)
#|    out["prefault_cond_dtw"] = cond_dtw.astype(bool)
#|    out["prefault_cond_ews"] = cond_ews.astype(bool)
#|
#|    # 실제 전조 엔진 플래그 (b안):
#|    # - 데이터 품질이 나쁘지 않고(data_bad=False)
#|    # - 아직 최종 고장(final_fault)이 아닌 상태에서
#|    # - 위 네 조건을 동시에 만족하면 해당 날짜-패널을 "전조 후보"로 표시
#|    out["prefault_B"] = (
#|        (~out["data_bad"]) & (~out["final_fault"]) &
#|        out["prefault_cond_mid"] & out["prefault_cond_ae"] & out["prefault_cond_dtw"] & out["prefault_cond_ews"]
#|    )
#|    out["base_day_panel_count"] = (
#|        out.groupby(["date", "group_key_base"])["panel_id"].transform("nunique").fillna(0).astype(int)
#|    )
#|    out["base_day_degraded_panel_count"] = (
#|        out.groupby(["date", "group_key_base"])["degraded_candidate"]
#|        .transform(lambda s: s.astype(bool).sum())
#|        .fillna(0)
#|        .astype(int)
#|    )
#|    out["subgroup_common_cause_candidate"] = (
#|        out["degraded_candidate"].astype(bool)
#|        & (~out["site_event_soft"].astype(bool))
#|        & (~out["site_event_hard"].astype(bool))
#|        & (~out["group_off_date"].astype(bool))
#|        & (~out["group_off_like"].astype(bool))
#|        & out["base_day_degraded_panel_count"].ge(3)
#|    )
#|    prefault_common_cause_overlap = (
#|        out["prefault_B"].astype(bool)
#|        & (
#|            out["site_event_soft"].astype(bool)
#|            | out["site_event_hard"].astype(bool)
#|            | out["group_off_date"].astype(bool)
#|            | out["group_off_like"].astype(bool)
#|        )
#|    )
#|    out["prefault_B_common_cause_overlap"] = prefault_common_cause_overlap
#|    out["prefault_B_effective"] = out["prefault_B"].astype(bool) & (~prefault_common_cause_overlap)
#|
#|    # ===== Helper reports: daily summaries & candidate lists =====
#|    # 1) 날짜별 anom_level 요약 테이블
#|    try:
#|        daily_level = (
#|            out.pivot_table(
#|                index="date",
#|                columns="anom_level",
#|                values="panel_id",
#|                aggfunc="count",
#|                fill_value=0,
#|            )
#|            .reset_index()
#|        )
#|        daily_level_path = out_dir / "ae_simple_daily_anom_level.csv"
#|        _safe_report_write(
#|            daily_level,
#|            daily_level_path,
#|            "daily anom_level summary",
#|            index=False,
#|            encoding="utf-8-sig",
#|        )
#|    except Exception as e:
#|        print("[WARN] failed to write daily anom_level summary:", e)
#|
#|    # 2) 날짜별 anom_subtype 요약 테이블
#|    try:
#|        daily_subtype = (
#|            out.pivot_table(
#|                index="date",
#|                columns="anom_subtype",
#|                values="panel_id",
#|                aggfunc="count",
#|                fill_value=0,
#|            )
#|            .reset_index()
#|        )
#|        daily_subtype_path = out_dir / "ae_simple_daily_anom_subtype.csv"
#|        _safe_report_write(
#|            daily_subtype,
#|            daily_subtype_path,
#|            "daily anom_subtype summary",
#|            index=False,
#|            encoding="utf-8-sig",
#|        )
#|    except Exception as e:
#|        print("[WARN] failed to write daily anom_subtype summary:", e)
#|
#|    # 3) 고장/후보 패널 리스트 (final_fault / fault_like_day / degraded_candidate)
#|    try:
#|        mask_candidates = (
#|            out["final_fault"].astype(bool)
#|            | out["fault_like_day"].astype(bool)
#|            | out["degraded_candidate"].astype(bool)
#|        )
#|        fault_candidates = out.loc[mask_candidates].copy()
#|        candidates_path = out_dir / "ae_simple_fault_candidates.csv"
#|        _safe_report_write(
#|            fault_candidates,
#|            candidates_path,
#|            "fault candidate list",
#|            index=False,
#|            encoding="utf-8-sig",
#|        )
#|    except Exception as e:
#|        print("[WARN] failed to write fault candidate list:", e)
#|
#|    # 4) EWS 경고 패널 리스트
#|    try:
#|        ews_list = out[out["ews_warning"].astype(bool)].copy()
#|        ews_path = out_dir / "ae_simple_ews_warnings.csv"
#|        _safe_report_write(
#|            ews_list,
#|            ews_path,
#|            "EWS warning list",
#|            index=False,
#|            encoding="utf-8-sig",
#|        )
#|    except Exception as e:
#|        print("[WARN] failed to write EWS warning list:", e)
#|
#|    # 5) 전조 엔진(Option B) 알람 리스트 – 날짜·패널 단위
#|    # canonical 이름은 option_b를 명시해 의미를 드러내고,
#|    # 기존 template-B 파일명은 backward-compatible alias로 유지한다.
#|    try:
#|        prefault_list = out[out["prefault_B"].astype(bool)].copy()
#|        pf_path = out_dir / "ae_simple_prefault_option_b_daily.csv"
#|        pf_legacy_path = out_dir / "ae_simple_prefault_B_daily.csv"
#|        _safe_report_write(
#|            prefault_list,
#|            pf_path,
#|            "pre-fault option-b list",
#|            index=False,
#|            encoding="utf-8-sig",
#|        )
#|        _safe_report_write(
#|            prefault_list,
#|            pf_legacy_path,
#|            "legacy pre-fault template-B alias",
#|            index=False,
#|            encoding="utf-8-sig",
#|        )
#|    except Exception as e:
#|        print("[WARN] failed to write pre-fault option-b list:", e)
#|
#|    # B안 pre-alarm 플래그: 이미 고장 확정된 날은 제외하고,
#|    # EWS 경고 + (AE/DTW/HS 중 하나 이상 mid 이상) 인 날만 전조 후보로 간주
#|    out["prealarm_cond_ae_mid_or_hi"] = out["ae_strength"].isin(["mid", "high"]).astype(bool)
#|    out["prealarm_cond_dtw_mid_or_hi"] = out["dtw_strength"].isin(["mid", "high"]).astype(bool)
#|    out["prealarm_cond_hs_mid_or_hi"] = out["hs_strength"].isin(["mid", "high"]).astype(bool)
#|    out["pre_alarm"] = (
#|        (~out["final_fault"].astype(bool))
#|        & out["ews_warning"].astype(bool)
#|        & (
#|            out["prealarm_cond_ae_mid_or_hi"]
#|            | out["prealarm_cond_dtw_mid_or_hi"]
#|            | out["prealarm_cond_hs_mid_or_hi"]
#|        )
#|    )
#|
#|    # 6) local precursor gate states helper sidecar
#|    try:
#|        gate_daily = out.loc[
#|            :,
#|            [
#|                "panel_id",
#|                "date",
#|                "data_bad",
#|                "cond_var",
#|                "cond_evt",
#|                "cond_dtw",
#|                "cond_hs",
#|                "pre_ews",
#|                "signal_count",
#|                "ews_runlen",
#|                "ews_warning",
#|                "site_event_soft",
#|                "site_event_hard",
#|                "group_off_date",
#|                "base_day_panel_count",
#|                "base_day_degraded_panel_count",
#|                "subgroup_common_cause_candidate",
#|                "prefault_B",
#|                "prefault_B_common_cause_overlap",
#|                "prefault_B_effective",
#|                "pre_alarm",
#|                "prefault_cond_mid",
#|                "prefault_cond_ae",
#|                "prefault_cond_dtw",
#|                "prefault_cond_ews",
#|                "prealarm_cond_ae_mid_or_hi",
#|                "prealarm_cond_dtw_mid_or_hi",
#|                "prealarm_cond_hs_mid_or_hi",
#|            ],
#|        ].copy()
#|        gate_daily.insert(0, "site", site)
#|        gate_path = out_dir / "ae_simple_local_precursor_gate_daily.csv"
#|        _safe_report_write(
#|            gate_daily,
#|            gate_path,
#|            "local precursor gate daily",
#|            index=False,
#|            encoding="utf-8-sig",
#|        )
#|    except Exception as e:
#|        print("[WARN] failed to write local precursor gate daily:", e)
#|
#|    # 7) 패널별 전조/만성 이상 요약 (전조 엔진 1.0, B안 로직)
#|    try:
#|
#|        # 패널별 집계: 기간, 고장 여부, EWS/전조 일수 등
#|        grp_panel = out.groupby("panel_id")
#|        panel_summary = grp_panel.agg(
#|            first_date=("date", "min"),
#|            last_date=("date", "max"),
#|            has_fault=("final_fault", "any"),
#|            n_fault_days=("final_fault", "sum"),
#|            any_ews=("ews_warning", "any"),
#|            n_ews_days=("ews_warning", "sum"),
#|            any_pre_alarm=("pre_alarm", "any"),
#|            n_pre_alarm_days=("pre_alarm", "sum"),
#|        )
#|
#|        # 패널별 최초 고장일과 최초 전조일
#|        fault_start = (
#|            out[out["final_fault"].astype(bool)]
#|            .groupby("panel_id")["date"]
#|            .min()
#|            .rename("fault_start_date")
#|        )
#|        pre_alarm_start = (
#|            out[out["pre_alarm"].astype(bool)]
#|            .groupby("panel_id")["date"]
#|            .min()
#|            .rename("pre_alarm_start")
#|        )
#|
#|        panel_summary = panel_summary.join(fault_start, how="left").join(pre_alarm_start, how="left")
#|
#|        # 전조 알람 리드타임 (일 단위)
#|        panel_summary["lead_days"] = (
#|            panel_summary["fault_start_date"] - panel_summary["pre_alarm_start"]
#|        ).dt.days
#|
#|        # 패턴 분류 함수: 전조 vs 만성 vs 기타
#|        def _classify_alarm_pattern(row):
#|            # 전조 후보 자체가 없는 패널
#|            if not row["any_pre_alarm"]:
#|                return "no_pre_alarm"
#|
#|            # 실제 고장 패널: 전조 리드타임이 3일 이상이면 전조 후보로 간주
#|            if row["has_fault"]:
#|                if pd.notna(row["lead_days"]) and row["lead_days"] >= 3:
#|                    return "pre_fault_candidate"  # 고장 전에 전조가 선행
#|                else:
#|                    return "near_or_post_fault"  # 고장 직전/직후만 튄 케이스
#|
#|            # 아직 고장은 아니지만, 전조 알람이 장기간 누적된 만성 이상 패널
#|            span_days = (row["last_date"] - row["first_date"]).days
#|            if (row["n_pre_alarm_days"] >= 20) and (span_days >= 60):
#|                return "chronic_abnormal"  # 장기간 만성 이상 패턴
#|
#|            # 나머지: 단기 이상 / 일시적 이상
#|            return "short_abnormal"
#|
#|        panel_summary["alarm_pattern"] = panel_summary.apply(_classify_alarm_pattern, axis=1)
#|
#|        # 패널 요약 리포트 저장
#|        panel_alarm_path = out_dir / "ae_simple_panel_alarms.csv"
#|        _safe_report_write(
#|            panel_summary,
#|            panel_alarm_path,
#|            "panel alarm summary",
#|            index=True,
#|            encoding="utf-8-sig",
#|        )
#|    except Exception as e:
#|        print("[WARN] failed to write panel alarm summary:", e)
#|
#|    out_path = out_dir / "panel_day_core.csv"
#|    out.to_csv(
#|        out_path,
#|        index=False,
#|        encoding="utf-8-sig",
#|        columns=[c for c in OUT_COLS if c in out.columns],
#|    )
#|
#|    meta = {
#|        "args": vars(args),
#|        "ae_threshold_global": ae_thr_ae,
#|        "train_files": [p.name for p in train_files],
#|        "eval_files": [p.name for p in eval_files],
#|    }
#|    meta["tuning_level"] = tuning_level
#|    suffix = "" if tuning_level == "p2" else f"_{tuning_level}"
#|    meta_path = out_dir / f"ae_simple_meta{suffix}.json"
#|    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
#|
#|    print("[OK] wrote", out_path)
#|    print("[OK] tuning_level =", tuning_level)
#|    print("[OK] ae_threshold_global =", ae_thr_ae)
#|
#|
#|if __name__ == "__main__":
#|    main()
#|# __write_probe__
#|
#|# __write_probe__
# pvdiag_payload_end
# endregion
# region payload: package_marker
# pvdiag_payload_file {"bytes": 0, "endswith_newline": false, "lines": 0, "path": "release/conalog_full_runtime_v1/package/research/__init__.py", "role": "package_marker", "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}
# pvdiag_payload_end
# endregion
# region payload: package_marker
# pvdiag_payload_file {"bytes": 0, "endswith_newline": false, "lines": 0, "path": "release/conalog_full_runtime_v1/package/research/prognostics/__init__.py", "role": "package_marker", "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}
# pvdiag_payload_end
# endregion
# region payload: live_bootstrap_builder
# pvdiag_payload_file {"bytes": 8771, "endswith_newline": true, "lines": 201, "path": "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_bootstrap_verdict_v1.py", "role": "live_bootstrap_builder", "sha256": "d282379e50de994a571fdd47d929796cb55e88f709974f0b019bd93bb10e707e"}
#|#!/usr/bin/env python3
#|from __future__ import annotations
#|
#|import argparse
#|import sys
#|from pathlib import Path
#|
#|import pandas as pd
#|
#|REPO_ROOT = Path(__file__).resolve().parents[2]
#|if str(REPO_ROOT) not in sys.path:
#|    sys.path.insert(0, str(REPO_ROOT))
#|
#|from research.prognostics import build_panel_day_engine_panel_multiaxis_verdict_v1 as verdict_mod
#|
#|OUTPUT_NAME = "panel_day_engine_bootstrap_verdict_v1.csv"
#|OUTPUT_SUMMARY_NAME = "panel_day_engine_bootstrap_verdict_summary_v1.csv"
#|ALIAS_NAME = verdict_mod.VERDICT_OUTPUT_NAME
#|
#|BOOTSTRAP_COLS = [
#|    "site",
#|    "panel_id",
#|    "패널고장여부_ko",
#|    "사건유형_ko",
#|    "최종고장양상_ko",
#|    "전조흔적_flag",
#|    "순수급작_flag",
#|    "전조평가셋편입_flag",
#|    "급작평가셋편입_flag",
#|]
#|
#|SUMMARY_COLS = [
#|    "전체_패널수",
#|    "고장_패널수",
#|    "비고장_패널수",
#|    "미확정_패널수",
#|    "사건해석_전조형_패널수",
#|    "사건해석_급작_패널수",
#|    "전조평가셋_편입패널수",
#|    "급작평가셋_편입패널수",
#|    "note_ko",
#|]
#|
#|
#|def parse_args() -> argparse.Namespace:
#|    parser = argparse.ArgumentParser(
#|        description=(
#|            "Build a minimal bootstrap verdict file for runtime chain bootstrapping. "
#|            "This omits fault_event_audit dependency and only materializes the fields that "
#|            "fault_event_audit requires as upstream input."
#|        )
#|    )
#|    parser.add_argument(
#|        "--root",
#|        type=Path,
#|        default=REPO_ROOT,
#|        help="Repository root. Defaults to the project root.",
#|    )
#|    parser.add_argument(
#|        "--write-panel-verdict-alias",
#|        action="store_true",
#|        help=(
#|            "Also write the bootstrap output to _share/panel_day_engine_panel_multiaxis_verdict_v1.csv "
#|            "so that fault_event_audit can consume it in a workspace-only chain."
#|        ),
#|    )
#|    return parser.parse_args()
#|
#|
#|def load_frames(root: Path) -> dict[str, pd.DataFrame]:
#|    share_dir = root / "_share"
#|    frames = {
#|        "workflow": verdict_mod.read_csv(share_dir / verdict_mod.WORKFLOW_DEFAULT_NAME),
#|        "abrupt6": verdict_mod.read_csv(share_dir / verdict_mod.ABRUPT6_SYMPTOM_MAP_NAME),
#|        "final_pack": verdict_mod.read_csv(share_dir / verdict_mod.FINAL_DECISION_PACK_NAME),
#|        "precursor_truth": verdict_mod.read_csv(share_dir / verdict_mod.PRECURSOR_ONSET_TRUTH_NAME),
#|        "non_precursor_perf": verdict_mod.read_csv(share_dir / verdict_mod.NON_PRECURSOR_PERFORMANCE_CASES_NAME),
#|        "common_cause": verdict_mod.read_csv(share_dir / verdict_mod.COMMON_CAUSE_RETROFIT_NAME),
#|        "consistency_cases": verdict_mod.read_csv(share_dir / verdict_mod.PRECURSOR_ABRUPT_CONSISTENCY_CASES_NAME),
#|        "consistency_summary": verdict_mod.read_csv(share_dir / verdict_mod.PRECURSOR_ABRUPT_CONSISTENCY_SUMMARY_NAME),
#|        "consistency_recommendation": verdict_mod.read_csv(share_dir / verdict_mod.PRECURSOR_ABRUPT_CONSISTENCY_RECOMMENDATION_NAME),
#|        "forensic_summary": verdict_mod.read_csv(share_dir / verdict_mod.FORENSIC_SUMMARY_NAME),
#|    }
#|    return verdict_mod.normalize_frames(frames)
#|
#|
#|def build_rows(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
#|    workflow_panel_df = verdict_mod.build_workflow_panel_df(frames["workflow"])
#|    workflow_by_key = verdict_mod.workflow_lookup(workflow_panel_df)
#|    abrupt_by_key = verdict_mod.abrupt_lookup(frames["abrupt6"])
#|    same_event_overlap_keys = verdict_mod.load_same_event_overlap_keys(frames)
#|    forensic_rule_case = verdict_mod.load_forensic_rule_case(frames)
#|    forensic_rule_key = (verdict_mod.FORENSIC_RULE_SITE, verdict_mod.FORENSIC_RULE_PANEL_ID)
#|
#|    workflow_keys = set(workflow_by_key.keys())
#|    abrupt_keys = set(abrupt_by_key.keys())
#|    pure_abrupt_keys = abrupt_keys - same_event_overlap_keys - {forensic_rule_key}
#|    precursor_keys = verdict_mod.build_precursor_positive_keys(frames["precursor_truth"])
#|    precursor_eval_keys = precursor_keys
#|    abrupt_eval_keys = verdict_mod.build_abrupt_eval_keys(frames["non_precursor_perf"])
#|    common_keys = verdict_mod.build_common_cause_positive_keys(frames["common_cause"])
#|    workflow_watch_keys = {
#|        (verdict_mod.normalize_text(row["site"]), verdict_mod.normalize_text(row["display_entity_id"]))
#|        for row in workflow_panel_df.loc[
#|            workflow_panel_df["preview_attention_class"].eq("watch_now_panel")
#|        ].to_dict(orient="records")
#|    }
#|    panel_keys = set().union(workflow_keys, abrupt_keys, precursor_keys, common_keys)
#|
#|    rows: list[dict[str, object]] = []
#|    for site, panel_id in sorted(panel_keys):
#|        key = (site, panel_id)
#|        flags = {
#|            "has_전조형고장": int(key in precursor_keys),
#|            "has_급작고장": int(key in pure_abrupt_keys),
#|            "has_공통원인이벤트": int(key in common_keys),
#|            "has_반복이상": int(key in workflow_watch_keys),
#|        }
#|        is_same_event_overlap = key in same_event_overlap_keys
#|        active_forensic_rule_case = forensic_rule_case if key == forensic_rule_key else None
#|        event_type, terminal_pattern = verdict_mod.event_type_and_terminal_pattern(
#|            flags,
#|            is_same_event_overlap=is_same_event_overlap,
#|            forensic_rule_case=active_forensic_rule_case,
#|            fault_audit_row=None,
#|        )
#|        interpretation = verdict_mod.interpretation_layer_fields(
#|            flags,
#|            event_type,
#|            precursor_eval_flag=int(key in precursor_eval_keys),
#|            abrupt_eval_flag=int(key in abrupt_eval_keys),
#|            is_same_event_overlap=is_same_event_overlap,
#|            forensic_rule_case=active_forensic_rule_case,
#|            fault_audit_row=None,
#|        )
#|        rows.append(
#|            {
#|                "site": site,
#|                "panel_id": panel_id,
#|                "패널고장여부_ko": verdict_mod.panel_fault_status_from_event_type(event_type),
#|                "사건유형_ko": event_type,
#|                "최종고장양상_ko": terminal_pattern,
#|                "전조흔적_flag": int(interpretation["전조흔적_flag"]),
#|                "순수급작_flag": int(interpretation["순수급작_flag"]),
#|                "전조평가셋편입_flag": int(interpretation["전조평가셋편입_flag"]),
#|                "급작평가셋편입_flag": int(interpretation["급작평가셋편입_flag"]),
#|            }
#|        )
#|
#|    bootstrap_df = pd.DataFrame(rows).reindex(columns=BOOTSTRAP_COLS)
#|    if bootstrap_df.empty:
#|        raise SystemExit("bootstrap verdict must not be empty")
#|    return bootstrap_df
#|
#|
#|def build_summary(df: pd.DataFrame) -> pd.DataFrame:
#|    status = df["패널고장여부_ko"].map(verdict_mod.normalize_text)
#|    event = df["사건유형_ko"].map(verdict_mod.normalize_text)
#|    row = {
#|        "전체_패널수": int(len(df)),
#|        "고장_패널수": int(status.eq("고장").sum()),
#|        "비고장_패널수": int(status.eq("비고장").sum()),
#|        "미확정_패널수": int(status.eq("미확정").sum()),
#|        "사건해석_전조형_패널수": int(event.eq("전조형 고장").sum()),
#|        "사건해석_급작_패널수": int(event.eq("급작 고장").sum()),
#|        "전조평가셋_편입패널수": int(pd.to_numeric(df["전조평가셋편입_flag"], errors="coerce").fillna(0).sum()),
#|        "급작평가셋_편입패널수": int(pd.to_numeric(df["급작평가셋편입_flag"], errors="coerce").fillna(0).sum()),
#|        "note_ko": (
#|            "이 파일은 runtime chain bootstrapping용 최소 verdict다. "
#|            "fault_event_audit가 요구하는 현재표 사건유형/최종고장양상/평가셋 편입 상태만 먼저 만든다. "
#|            "공식 final verdict를 대체하지 않으며, workspace-only bootstrap 입력으로만 사용한다."
#|        ),
#|    }
#|    return pd.DataFrame([row]).reindex(columns=SUMMARY_COLS)
#|
#|
#|def main() -> None:
#|    args = parse_args()
#|    root = args.root.resolve()
#|    share_dir = root / "_share"
#|    share_dir.mkdir(parents=True, exist_ok=True)
#|
#|    frames = load_frames(root)
#|    bootstrap_df = build_rows(frames)
#|    summary_df = build_summary(bootstrap_df)
#|
#|    bootstrap_path = share_dir / OUTPUT_NAME
#|    summary_path = share_dir / OUTPUT_SUMMARY_NAME
#|    bootstrap_df.to_csv(bootstrap_path, index=False, encoding="utf-8-sig")
#|    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
#|
#|    if args.write_panel_verdict_alias:
#|        bootstrap_df.to_csv(share_dir / ALIAS_NAME, index=False, encoding="utf-8-sig")
#|
#|    print(f"[OK] wrote bootstrap verdict: {bootstrap_path}")
#|    if args.write_panel_verdict_alias:
#|        print(f"[OK] wrote bootstrap verdict alias: {share_dir / ALIAS_NAME}")
#|
#|
#|if __name__ == "__main__":
#|    main()
# pvdiag_payload_end
# endregion
# region payload: live_heuristic_builder
# pvdiag_payload_file {"bytes": 21623, "endswith_newline": true, "lines": 564, "path": "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_cause_candidate_heuristics_v1.py", "role": "live_heuristic_builder", "sha256": "86de483fc576f7d10424f0dcac6f5fce24eb864a4ec765833e728119c88035d7"}
#|#!/usr/bin/env python3
#|from __future__ import annotations
#|
#|import argparse
#|from pathlib import Path
#|
#|import pandas as pd
#|
#|
#|REPO_ROOT = Path(__file__).resolve().parents[2]
#|
#|EVIDENCE_PACK_NAME = "panel_day_engine_gpvs_evidence_pack_v1.csv"
#|VERDICT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
#|DETAILED_AUDIT_NAME = "panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv"
#|
#|OUTPUT_MAIN_NAME = "panel_day_engine_cause_candidate_heuristics_v1.csv"
#|OUTPUT_BREAKDOWN_NAME = "panel_day_engine_cause_candidate_score_breakdown_v1.csv"
#|OUTPUT_SUMMARY_NAME = "panel_day_engine_cause_candidate_summary_v1.csv"
#|
#|CANDIDATES = [
#|    "부분음영형",
#|    "오염형",
#|    "열화형",
#|    "다이오드·서브스트링형",
#|    "접속·부분개방형",
#|    "센서·피드백형",
#|    "제어응답형",
#|    "외부계통교란형",
#|    "전력변환부형",
#|    "원인미확정",
#|]
#|
#|TIE_PRIORITY = {
#|    "접속·부분개방형": 0,
#|    "다이오드·서브스트링형": 1,
#|    "부분음영형": 2,
#|    "오염형": 3,
#|    "열화형": 4,
#|    "센서·피드백형": 5,
#|    "제어응답형": 6,
#|    "외부계통교란형": 7,
#|    "전력변환부형": 8,
#|    "원인미확정": 9,
#|}
#|
#|EVIDENCE_REQUIRED_COLS = [
#|    "site",
#|    "panel_id",
#|    "사건유형_ko",
#|    "최종고장양상_ko",
#|    "커널로그_원인군_ko",
#|    "GPVS_내부판정_ko",
#|    "GPVS_외부참조패턴_ko",
#|    "GPVS_최종사용권고_ko",
#|]
#|
#|VERDICT_REQUIRED_COLS = [
#|    "site",
#|    "panel_id",
#|    "패널고장여부_ko",
#|    "사건유형_ko",
#|    "최종고장양상_ko",
#|    "커널로그_원인군_ko",
#|    "GPVS_내부참고유형_ko",
#|    "GPVS_외부참조패턴_ko",
#|]
#|
#|DETAILED_REQUIRED_COLS = [
#|    "site",
#|    "panel_id",
#|    "gpvs_detailed_top1_fault_type",
#|]
#|
#|MAIN_COLS = [
#|    "site",
#|    "panel_id",
#|    "사건유형_ko",
#|    "최종고장양상_ko",
#|    "커널로그_원인군_ko",
#|    "GPVS_내부참고유형_ko",
#|    "GPVS_외부참조패턴_ko",
#|    "원인후보_top1_ko",
#|    "원인후보_top1_score",
#|    "원인후보_top2_ko",
#|    "원인후보_top2_score",
#|    "원인후보_top3_ko",
#|    "원인후보_top3_score",
#|    "원인후보_경합상태_ko",
#|    "원인후보_공동상위후보_csv",
#|    "원인후보_실증우선확인_ko",
#|    "원인후보_신뢰도_ko",
#|    "원인후보_해석메모_ko",
#|]
#|
#|BREAKDOWN_COLS = [
#|    "site",
#|    "panel_id",
#|    "candidate_ko",
#|    "raw_score",
#|    "support_signal_csv",
#|    "note_ko",
#|]
#|
#|SUMMARY_COLS = [
#|    "fault_panel_count",
#|    "unique_top1_candidate_count",
#|    "top1_부분음영형_count",
#|    "top1_오염형_count",
#|    "top1_열화형_count",
#|    "top1_다이오드·서브스트링형_count",
#|    "top1_접속·부분개방형_count",
#|    "top1_센서·피드백형_count",
#|    "top1_제어응답형_count",
#|    "top1_외부계통교란형_count",
#|    "top1_전력변환부형_count",
#|    "top1_원인미확정_count",
#|    "단일우세_count",
#|    "two_way_competition_count",
#|    "multi_way_competition_count",
#|    "note_ko",
#|]
#|
#|GPVS_EXTERNAL_RULES = {
#|    "국소 출력 불균형형": {
#|        "부분음영형": 2,
#|        "오염형": 1,
#|        "열화형": 1,
#|        "다이오드·서브스트링형": 2,
#|        "접속·부분개방형": 1,
#|    },
#|    "장치 응답 이상형": {
#|        "센서·피드백형": 3,
#|        "제어응답형": 2,
#|        "접속·부분개방형": 1,
#|    },
#|    "외부 계통 교란형": {
#|        "외부계통교란형": 4,
#|    },
#|    "전력변환부 이상형": {
#|        "전력변환부형": 4,
#|    },
#|    "제어 응답 이상형": {
#|        "제어응답형": 4,
#|    },
#|}
#|
#|INTERNAL_FAMILY_RULES = {
#|    "전기적 고장 계열": {
#|        "다이오드·서브스트링형": 1,
#|        "접속·부분개방형": 1,
#|    },
#|    "개방/장치이상 계열": {
#|        "접속·부분개방형": 2,
#|        "센서·피드백형": 1,
#|        "제어응답형": 1,
#|    },
#|    "불확실": {
#|        "원인미확정": 2,
#|    },
#|}
#|
#|KERNEL_RULES = {
#|    "다이오드형": {
#|        "다이오드·서브스트링형": 2,
#|    },
#|    "개방/장치이상형": {
#|        "접속·부분개방형": 2,
#|        "센서·피드백형": 1,
#|    },
#|    "모듈손상형": {
#|        "열화형": 2,
#|        "오염형": 1,
#|        "다이오드·서브스트링형": 1,
#|    },
#|}
#|
#|TEMPORAL_RULES = {
#|    ("전조형 고장", "진행성 악화"): {
#|        "열화형": 2,
#|        "오염형": 1,
#|        "다이오드·서브스트링형": 1,
#|    },
#|    ("전조형 고장", "급격 종료"): {
#|        "접속·부분개방형": 1,
#|        "다이오드·서브스트링형": 1,
#|        "센서·피드백형": 1,
#|    },
#|    ("급작 고장", "급작 발생"): {
#|        "접속·부분개방형": 1,
#|        "외부계통교란형": 1,
#|        "다이오드·서브스트링형": 1,
#|    },
#|}
#|
#|USAGE_WEIGHT_RULES = {
#|    ("핵심참조", "국소 출력 불균형형"): {
#|        "다이오드·서브스트링형": 1,
#|        "부분음영형": 1,
#|    },
#|    ("보조참조", "장치 응답 이상형"): {
#|        "센서·피드백형": 1,
#|        "제어응답형": 1,
#|    },
#|}
#|
#|
#|def parse_args() -> argparse.Namespace:
#|    parser = argparse.ArgumentParser(
#|        description="Build a heuristic cause-candidate ranking layer for current fault panels."
#|    )
#|    parser.add_argument(
#|        "--root",
#|        type=Path,
#|        default=REPO_ROOT,
#|        help="Repository root. Defaults to the project root.",
#|    )
#|    return parser.parse_args()
#|
#|
#|def normalize_text(value: object) -> str:
#|    if pd.isna(value):
#|        return ""
#|    text = str(value).strip()
#|    return "" if text.lower() == "nan" else text
#|
#|
#|def read_csv(path: Path) -> pd.DataFrame:
#|    if not path.exists():
#|        raise SystemExit(f"missing input: {path}")
#|    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
#|
#|
#|def read_optional_csv(path: Path) -> pd.DataFrame:
#|    if not path.exists():
#|        return pd.DataFrame()
#|    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
#|
#|
#|def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
#|    missing = [column for column in required if column not in df.columns]
#|    if missing:
#|        raise SystemExit(f"{name} missing columns: {missing}")
#|
#|
#|def as_key(site: object, panel_id: object) -> tuple[str, str]:
#|    return normalize_text(site), normalize_text(panel_id)
#|
#|
#|def validate_unique_keys(df: pd.DataFrame, name: str) -> None:
#|    if df.empty:
#|        return
#|    if df[["site", "panel_id"]].duplicated().any():
#|        dup = df.loc[df[["site", "panel_id"]].duplicated(keep=False), ["site", "panel_id"]]
#|        raise SystemExit(f"{name} must be unique by (site, panel_id): {dup.to_dict(orient='records')[:5]}")
#|
#|
#|def lookup_map(df: pd.DataFrame) -> dict[tuple[str, str], dict[str, str]]:
#|    lookup: dict[tuple[str, str], dict[str, str]] = {}
#|    for row in df.to_dict(orient="records"):
#|        lookup[as_key(row.get("site"), row.get("panel_id"))] = {
#|            key: normalize_text(value) for key, value in row.items()
#|        }
#|    return lookup
#|
#|
#|def apply_rule_bundle(
#|    scores: dict[str, int],
#|    signals: dict[str, list[str]],
#|    bundle: dict[str, int],
#|    signal_prefix: str,
#|) -> None:
#|    for candidate, value in bundle.items():
#|        scores[candidate] += int(value)
#|        signals[candidate].append(f"{signal_prefix}:{candidate}+{int(value)}")
#|
#|
#|def rank_candidates(scores: dict[str, int]) -> list[tuple[str, int]]:
#|    return sorted(
#|        scores.items(),
#|        key=lambda item: (-item[1], TIE_PRIORITY[item[0]]),
#|    )
#|
#|
#|def competition_candidates(top_ranked: list[tuple[str, int]]) -> list[tuple[str, int]]:
#|    top1_score = top_ranked[0][1]
#|    return [item for item in top_ranked if item[1] >= top1_score - 1]
#|
#|
#|def competition_status(competition_ranked: list[tuple[str, int]]) -> str:
#|    if len(competition_ranked) <= 1:
#|        return "단일우세"
#|    if len(competition_ranked) == 2:
#|        return "2자경합"
#|    return "다자경합"
#|
#|
#|def competition_csv(competition_ranked: list[tuple[str, int]]) -> str:
#|    return ",".join(candidate for candidate, _ in competition_ranked)
#|
#|
#|def object_particle(text: str) -> str:
#|    normalized = normalize_text(text)
#|    if not normalized:
#|        return "를"
#|    last_char = normalized[-1]
#|    code_point = ord(last_char)
#|    if 0xAC00 <= code_point <= 0xD7A3:
#|        jongseong = (code_point - 0xAC00) % 28
#|        return "을" if jongseong else "를"
#|    return "를"
#|
#|
#|def action_note(
#|    top1_name: str,
#|    competition_ranked: list[tuple[str, int]],
#|    competition_state: str,
#|) -> str:
#|    if competition_state == "단일우세":
#|        return f"{top1_name} 우선 점검"
#|    if competition_state == "2자경합":
#|        cand1, cand2 = [candidate for candidate, _ in competition_ranked[:2]]
#|        return f"{cand1}과 {cand2}{object_particle(cand2)} 함께 우선 점검"
#|    if competition_state == "다자경합":
#|        cand1, cand2, cand3 = [candidate for candidate, _ in competition_ranked[:3]]
#|        return f"{cand1}, {cand2}, {cand3}을 함께 우선 점검"
#|    return f"{top1_name} 우선 점검"
#|
#|
#|def confidence_label(top1_score: int, competition_state: str) -> str:
#|    if top1_score >= 6 and competition_state == "단일우세":
#|        return "high"
#|    if top1_score >= 4 and competition_state != "다자경합":
#|        return "medium"
#|    return "low"
#|
#|
#|def interpretive_note(
#|    row: dict[str, str],
#|    top_ranked: list[tuple[str, int]],
#|    competition_ranked: list[tuple[str, int]],
#|    competition_state: str,
#|    confidence: str,
#|    detailed_row: dict[str, str] | None,
#|) -> str:
#|    top1_name, top1_score = top_ranked[0]
#|    top2_name, top2_score = top_ranked[1]
#|    sources = []
#|    if normalize_text(row.get("GPVS_외부참조패턴_ko")):
#|        sources.append(f"GPVS 외부={normalize_text(row['GPVS_외부참조패턴_ko'])}")
#|    if normalize_text(row.get("GPVS_내부참고유형_ko")):
#|        sources.append(f"GPVS 내부={normalize_text(row['GPVS_내부참고유형_ko'])}")
#|    if normalize_text(row.get("커널로그_원인군_ko")):
#|        sources.append(f"커널로그={normalize_text(row['커널로그_원인군_ko'])}")
#|    if normalize_text(row.get("사건유형_ko")) or normalize_text(row.get("최종고장양상_ko")):
#|        sources.append(
#|            f"시간양상={normalize_text(row.get('사건유형_ko'))}/{normalize_text(row.get('최종고장양상_ko'))}"
#|        )
#|    detail_tail = ""
#|    if detailed_row is not None and normalize_text(detailed_row.get("gpvs_detailed_top1_fault_type")):
#|        detail_tail = (
#|            f" raw detailed audit top1={normalize_text(detailed_row['gpvs_detailed_top1_fault_type'])}는 "
#|            "score에 직접 가산하지 않고 front-facing GPVS pattern으로만 반영했다."
#|        )
#|
#|    source_text = ", ".join(sources)
#|    competition_text = competition_csv(competition_ranked)
#|    if confidence == "high":
#|        return (
#|            f"{source_text} 신호가 {top1_name} 쪽으로 강하게 겹치고 경합상태는 {competition_state}({competition_text})다."
#|            f"{detail_tail}"
#|        )
#|    if confidence == "medium":
#|        return (
#|            f"{source_text} 신호가 {top1_name}에 더 기울지만 경합상태는 {competition_state}({competition_text})라 {top2_name}({top2_score})도 함께 확인해야 한다."
#|            f"{detail_tail}"
#|        )
#|    return (
#|        f"{source_text} 신호가 {competition_state}({competition_text}) 상태여서 {top1_name}({top1_score})와 {top2_name}({top2_score})를 포함한 공동 점검 후보로 읽어야 하므로 "
#|        "definitive diagnosis가 아니라 현장 점검 우선순위 좁히기 용도로만 읽는다."
#|        f"{detail_tail}"
#|    )
#|
#|
#|def build_outputs(
#|    evidence_df: pd.DataFrame,
#|    verdict_df: pd.DataFrame,
#|    detailed_df: pd.DataFrame,
#|) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
#|    fault_verdict_df = verdict_df.loc[verdict_df["패널고장여부_ko"].map(normalize_text).eq("고장")].copy()
#|    if len(fault_verdict_df) != 6:
#|        raise SystemExit(f"{VERDICT_NAME} current fault panel count must be 6, found {len(fault_verdict_df)}")
#|    if len(evidence_df) != 6:
#|        raise SystemExit(f"{EVIDENCE_PACK_NAME} current fault panel count must be 6, found {len(evidence_df)}")
#|
#|    evidence_lookup = lookup_map(evidence_df)
#|    verdict_lookup = lookup_map(fault_verdict_df)
#|    detailed_lookup = lookup_map(detailed_df) if not detailed_df.empty else {}
#|
#|    fault_keys = set(verdict_lookup)
#|    if set(evidence_lookup) != fault_keys:
#|        raise SystemExit("verdict and evidence pack fault key universe must match exactly")
#|    if not detailed_df.empty and set(detailed_lookup) != fault_keys:
#|        raise SystemExit("optional detailed audit fault key universe must match current fault panels when present")
#|
#|    main_rows: list[dict[str, object]] = []
#|    breakdown_rows: list[dict[str, object]] = []
#|
#|    for site, panel_id in sorted(fault_keys):
#|        evidence_row = evidence_lookup[(site, panel_id)]
#|        verdict_row = verdict_lookup[(site, panel_id)]
#|        detailed_row = detailed_lookup.get((site, panel_id))
#|
#|        event_type = normalize_text(verdict_row["사건유형_ko"])
#|        terminal_pattern = normalize_text(verdict_row["최종고장양상_ko"])
#|        kernel_family = normalize_text(verdict_row["커널로그_원인군_ko"])
#|        internal_family = normalize_text(verdict_row["GPVS_내부참고유형_ko"]) or normalize_text(evidence_row["GPVS_내부판정_ko"])
#|        external_pattern = normalize_text(verdict_row["GPVS_외부참조패턴_ko"]) or normalize_text(evidence_row["GPVS_외부참조패턴_ko"])
#|        usage_level = normalize_text(evidence_row["GPVS_최종사용권고_ko"])
#|
#|        if event_type != normalize_text(evidence_row["사건유형_ko"]):
#|            raise SystemExit(f"fault event type mismatch across verdict/evidence for {site}/{panel_id}")
#|        if terminal_pattern != normalize_text(evidence_row["최종고장양상_ko"]):
#|            raise SystemExit(f"fault terminal pattern mismatch across verdict/evidence for {site}/{panel_id}")
#|        if kernel_family != normalize_text(evidence_row["커널로그_원인군_ko"]):
#|            raise SystemExit(f"kernel family mismatch across verdict/evidence for {site}/{panel_id}")
#|
#|        scores = {candidate: 0 for candidate in CANDIDATES}
#|        signals = {candidate: [] for candidate in CANDIDATES}
#|
#|        if external_pattern in GPVS_EXTERNAL_RULES:
#|            apply_rule_bundle(scores, signals, GPVS_EXTERNAL_RULES[external_pattern], f"gpvs_external={external_pattern}")
#|        if internal_family in INTERNAL_FAMILY_RULES:
#|            apply_rule_bundle(scores, signals, INTERNAL_FAMILY_RULES[internal_family], f"gpvs_internal={internal_family}")
#|        if kernel_family in KERNEL_RULES:
#|            apply_rule_bundle(scores, signals, KERNEL_RULES[kernel_family], f"kernel={kernel_family}")
#|        temporal_key = (event_type, terminal_pattern)
#|        if temporal_key in TEMPORAL_RULES:
#|            apply_rule_bundle(scores, signals, TEMPORAL_RULES[temporal_key], f"temporality={event_type}/{terminal_pattern}")
#|        usage_key = (usage_level, external_pattern)
#|        if usage_key in USAGE_WEIGHT_RULES:
#|            apply_rule_bundle(scores, signals, USAGE_WEIGHT_RULES[usage_key], f"usage={usage_level}|{external_pattern}")
#|
#|        ranked = rank_candidates(scores)
#|        top1_name, top1_score = ranked[0]
#|        top2_name, top2_score = ranked[1]
#|        top3_name, top3_score = ranked[2]
#|        competition_ranked = competition_candidates(ranked)
#|        competition_state = competition_status(competition_ranked)
#|        competition_names_csv = competition_csv(competition_ranked)
#|        action_text = action_note(top1_name, competition_ranked, competition_state)
#|        confidence = confidence_label(top1_score, competition_state)
#|        memo = interpretive_note(
#|            {
#|                **verdict_row,
#|                "GPVS_내부참고유형_ko": internal_family,
#|                "GPVS_외부참조패턴_ko": external_pattern,
#|            },
#|            ranked,
#|            competition_ranked,
#|            competition_state,
#|            confidence,
#|            detailed_row,
#|        )
#|
#|        main_rows.append(
#|            {
#|                "site": site,
#|                "panel_id": panel_id,
#|                "사건유형_ko": event_type,
#|                "최종고장양상_ko": terminal_pattern,
#|                "커널로그_원인군_ko": kernel_family,
#|                "GPVS_내부참고유형_ko": internal_family,
#|                "GPVS_외부참조패턴_ko": external_pattern,
#|                "원인후보_top1_ko": top1_name,
#|                "원인후보_top1_score": top1_score,
#|                "원인후보_top2_ko": top2_name,
#|                "원인후보_top2_score": top2_score,
#|                "원인후보_top3_ko": top3_name,
#|                "원인후보_top3_score": top3_score,
#|                "원인후보_경합상태_ko": competition_state,
#|                "원인후보_공동상위후보_csv": competition_names_csv,
#|                "원인후보_실증우선확인_ko": action_text,
#|                "원인후보_신뢰도_ko": confidence,
#|                "원인후보_해석메모_ko": memo,
#|            }
#|        )
#|
#|        for candidate, raw_score in ranked:
#|            signal_text = ", ".join(signals[candidate])
#|            breakdown_rows.append(
#|                {
#|                    "site": site,
#|                    "panel_id": panel_id,
#|                    "candidate_ko": candidate,
#|                    "raw_score": raw_score,
#|                    "support_signal_csv": signal_text,
#|                    "note_ko": "가산 규칙 없음" if not signal_text else f"{len(signals[candidate])}개 가산 규칙 합",
#|                }
#|            )
#|
#|    main_df = pd.DataFrame(main_rows).sort_values(["site", "panel_id"]).reset_index(drop=True).reindex(columns=MAIN_COLS)
#|    breakdown_df = pd.DataFrame(breakdown_rows).sort_values(["site", "panel_id", "raw_score", "candidate_ko"], ascending=[True, True, False, True]).reset_index(drop=True).reindex(columns=BREAKDOWN_COLS)
#|
#|    top1_counts = main_df["원인후보_top1_ko"].value_counts().to_dict()
#|    competition_counts = main_df["원인후보_경합상태_ko"].value_counts().to_dict()
#|    summary_row = {
#|        "fault_panel_count": len(main_df),
#|        "unique_top1_candidate_count": int(main_df["원인후보_top1_ko"].nunique()),
#|        "top1_부분음영형_count": int(top1_counts.get("부분음영형", 0)),
#|        "top1_오염형_count": int(top1_counts.get("오염형", 0)),
#|        "top1_열화형_count": int(top1_counts.get("열화형", 0)),
#|        "top1_다이오드·서브스트링형_count": int(top1_counts.get("다이오드·서브스트링형", 0)),
#|        "top1_접속·부분개방형_count": int(top1_counts.get("접속·부분개방형", 0)),
#|        "top1_센서·피드백형_count": int(top1_counts.get("센서·피드백형", 0)),
#|        "top1_제어응답형_count": int(top1_counts.get("제어응답형", 0)),
#|        "top1_외부계통교란형_count": int(top1_counts.get("외부계통교란형", 0)),
#|        "top1_전력변환부형_count": int(top1_counts.get("전력변환부형", 0)),
#|        "top1_원인미확정_count": int(top1_counts.get("원인미확정", 0)),
#|        "단일우세_count": int(competition_counts.get("단일우세", 0)),
#|        "two_way_competition_count": int(competition_counts.get("2자경합", 0)),
#|        "multi_way_competition_count": int(competition_counts.get("다자경합", 0)),
#|        "note_ko": (
#|            "이 표는 heuristic candidate-ranking layer이며 field trial triage용 후보 좁히기 표다. "
#|            "panel verdict와 GPVS reference, kernel-log, 시간양상을 additive score로만 합산했고 "
#|            "final root-cause confirmation이나 direct root-cause classifier로 읽으면 안 된다. "
#|            "경합 row는 단일 확정이 아니라 공동 현장점검 후보로 읽어야 한다."
#|        ),
#|    }
#|    summary_df = pd.DataFrame([summary_row]).reindex(columns=SUMMARY_COLS)
#|    return main_df, breakdown_df, summary_df
#|
#|
#|def write_outputs(root: Path, main_df: pd.DataFrame, breakdown_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
#|    share_dir = root / "_share"
#|    share_dir.mkdir(parents=True, exist_ok=True)
#|    main_df.to_csv(share_dir / OUTPUT_MAIN_NAME, index=False, encoding="utf-8-sig")
#|    breakdown_df.to_csv(share_dir / OUTPUT_BREAKDOWN_NAME, index=False, encoding="utf-8-sig")
#|    summary_df.to_csv(share_dir / OUTPUT_SUMMARY_NAME, index=False, encoding="utf-8-sig")
#|
#|
#|def main() -> None:
#|    args = parse_args()
#|    share_dir = args.root.resolve() / "_share"
#|
#|    evidence_df = read_csv(share_dir / EVIDENCE_PACK_NAME)
#|    verdict_df = read_csv(share_dir / VERDICT_NAME)
#|    detailed_df = read_optional_csv(share_dir / DETAILED_AUDIT_NAME)
#|
#|    ensure_columns(evidence_df, EVIDENCE_REQUIRED_COLS, EVIDENCE_PACK_NAME)
#|    ensure_columns(verdict_df, VERDICT_REQUIRED_COLS, VERDICT_NAME)
#|    if not detailed_df.empty:
#|        ensure_columns(detailed_df, DETAILED_REQUIRED_COLS, DETAILED_AUDIT_NAME)
#|
#|    validate_unique_keys(evidence_df, EVIDENCE_PACK_NAME)
#|    validate_unique_keys(verdict_df, VERDICT_NAME)
#|    if not detailed_df.empty:
#|        validate_unique_keys(detailed_df, DETAILED_AUDIT_NAME)
#|
#|    main_df, breakdown_df, summary_df = build_outputs(evidence_df, verdict_df, detailed_df)
#|    write_outputs(args.root.resolve(), main_df, breakdown_df, summary_df)
#|
#|
#|if __name__ == "__main__":
#|    main()
# pvdiag_payload_end
# endregion
# region payload: live_audit_builder
# pvdiag_payload_file {"bytes": 24531, "endswith_newline": true, "lines": 559, "path": "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_fault_panel_event_audit_v1.py", "role": "live_audit_builder", "sha256": "2573004b9450e21faaf944ad5e11d24ccdc66a82d03b04496a6a58778f5d838e"}
#|#!/usr/bin/env python3
#|from __future__ import annotations
#|
#|import argparse
#|from dataclasses import dataclass
#|from pathlib import Path
#|
#|import pandas as pd
#|from pandas.errors import EmptyDataError
#|
#|
#|PANEL_VERDICT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
#|ABRUPT6_NAME = "panel_day_engine_abrupt6_symptom_map_v1.csv"
#|PRECURSOR_TRUTH_NAME = "panel_day_engine_precursor_onset_truth_v1.csv"
#|REAUDIT_NAME = "panel_date_reaudit_working.csv"
#|VENDOR_ADJUDICATION_NAME = "vendor_reply_adjudication_latest.csv"
#|
#|AUDIT_OUTPUT = "_share/panel_day_engine_fault_panel_event_audit_v1.csv"
#|SUMMARY_OUTPUT = "_share/panel_day_engine_fault_panel_event_audit_summary_v1.csv"
#|NOTE_OUTPUT = "_share/panel_day_engine_fault_panel_event_audit_note_v1.md"
#|
#|TARGET_SITE = "conalog"
#|TARGET_PANEL_ID = "c42997a6-5881-47e7-9035-7de8a2673b54.1.1"
#|
#|AUDIT_COLS = [
#|    "site",
#|    "panel_id",
#|    "현재표_사건유형_ko",
#|    "현재표_최종고장양상_ko",
#|    "earliest_warning_date",
#|    "retrospective_onset_date",
#|    "strict_trigger_date",
#|    "first_final_fault_date",
#|    "dead_diag_date",
#|    "onset_confidence",
#|    "onset_method",
#|    "전조흔적_flag",
#|    "순수급작_flag",
#|    "전조평가셋편입_flag",
#|    "급작평가셋편입_flag",
#|    "사건유형_재판정_ko",
#|    "최종고장양상_재판정_ko",
#|    "재판정_근거_ko",
#|    "현재표_보정필요여부_flag",
#|]
#|
#|SUMMARY_COLS = [
#|    "고유_고장패널수",
#|    "사건유형_재판정_전조형수",
#|    "사건유형_재판정_급작수",
#|    "사건유형_재판정_보류수",
#|    "최종고장양상_급격종료수",
#|    "전조흔적_패널수",
#|    "순수급작_패널수",
#|    "전조평가셋편입_패널수",
#|    "급작평가셋편입_패널수",
#|    "해석과평가셋불일치_패널수",
#|    "현재표_보정필요_패널수",
#|    "note_ko",
#|]
#|
#|
#|@dataclass(frozen=True)
#|class EventRedecision:
#|    event_type_ko: str
#|    terminal_pattern_ko: str
#|    event_rule_ko: str
#|    terminal_rule_ko: str
#|    abrupt_positive_flag: int
#|
#|
#|def repo_root() -> Path:
#|    return Path(__file__).resolve().parents[2]
#|
#|
#|def parse_args() -> argparse.Namespace:
#|    parser = argparse.ArgumentParser(
#|        description="Audit all current fault panels with explicit stored-field event rules."
#|    )
#|    parser.add_argument(
#|        "--root",
#|        type=Path,
#|        default=repo_root(),
#|        help="Repository root. Defaults to the current repo root.",
#|    )
#|    return parser.parse_args()
#|
#|
#|def ensure_parent(path: Path) -> None:
#|    path.parent.mkdir(parents=True, exist_ok=True)
#|
#|
#|def write_csv(df: pd.DataFrame, path: Path) -> None:
#|    ensure_parent(path)
#|    df.to_csv(path, index=False, encoding="utf-8-sig")
#|
#|
#|def write_text(text: str, path: Path) -> None:
#|    ensure_parent(path)
#|    path.write_text(text, encoding="utf-8-sig")
#|
#|
#|def read_csv(path: Path, required: bool = True) -> pd.DataFrame:
#|    if not path.exists():
#|        if required:
#|            raise FileNotFoundError(f"Required input is missing: {path}")
#|        return pd.DataFrame()
#|    try:
#|        return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
#|    except EmptyDataError:
#|        return pd.DataFrame()
#|    except UnicodeError:
#|        return pd.read_csv(path, low_memory=False)
#|
#|
#|def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
#|    missing = [column for column in required if column not in df.columns]
#|    if missing:
#|        raise SystemExit(f"{name} missing columns: {missing}")
#|
#|
#|def normalize_text(value: object) -> str:
#|    if pd.isna(value):
#|        return ""
#|    text = str(value).strip()
#|    return "" if text.lower() == "nan" else text
#|
#|
#|def to_timestamp(value: object) -> pd.Timestamp | None:
#|    if pd.isna(value):
#|        return None
#|    ts = pd.to_datetime(value, errors="coerce")
#|    if pd.isna(ts):
#|        return None
#|    return ts
#|
#|
#|def format_date(value: object) -> str:
#|    ts = to_timestamp(value)
#|    return "" if ts is None else ts.strftime("%Y-%m-%d")
#|
#|
#|def exact_panel_rows(df: pd.DataFrame, panel_id: str, site: str | None = None) -> pd.DataFrame:
#|    if df.empty:
#|        return df.copy()
#|    panel_cols = [col for col in df.columns if col.lower() in {"panel_id", "display_entity_id", "entity_id"}]
#|    if not panel_cols:
#|        return df.iloc[0:0].copy()
#|    mask = pd.Series(False, index=df.index)
#|    for col in panel_cols:
#|        mask = mask | df[col].astype(str).eq(panel_id)
#|    result = df.loc[mask].copy()
#|    if site is not None and "site" in result.columns:
#|        result = result.loc[result["site"].astype(str).eq(site)].copy()
#|    return result
#|
#|
#|def earliest_true_date(df: pd.DataFrame, column: str, date_column: str = "date") -> pd.Timestamp | None:
#|    if df.empty or column not in df.columns or date_column not in df.columns:
#|        return None
#|    working = df.loc[df[column].fillna(False).astype(bool), date_column]
#|    if working.empty:
#|        return None
#|    value = pd.to_datetime(working, errors="coerce").min()
#|    return None if pd.isna(value) else value
#|
#|
#|def repeated_core_date(core_df: pd.DataFrame, column: str) -> pd.Timestamp | None:
#|    if core_df.empty or column not in core_df.columns:
#|        return None
#|    value = pd.to_datetime(core_df[column], errors="coerce").dropna()
#|    if value.empty:
#|        return None
#|    return value.iloc[0]
#|
#|
#|def build_precursor_eval_keys(precursor_truth_df: pd.DataFrame) -> set[tuple[str, str]]:
#|    panel_cols = [col for col in ("panel_id", "display_entity_id", "entity_id") if col in precursor_truth_df.columns]
#|    if not panel_cols:
#|        raise SystemExit(f"{PRECURSOR_TRUTH_NAME} missing panel id column")
#|    positive_df = precursor_truth_df.loc[
#|        precursor_truth_df["preferred_precursor_onset_date"].map(normalize_text).ne("")
#|    ].copy()
#|    keys: set[tuple[str, str]] = set()
#|    for row in positive_df.to_dict(orient="records"):
#|        site = normalize_text(row.get("site"))
#|        for panel_col in panel_cols:
#|            panel_id = normalize_text(row.get(panel_col))
#|            if site and panel_id:
#|                keys.add((site, panel_id))
#|                break
#|    return keys
#|
#|
#|def build_abrupt_keys(abrupt_df: pd.DataFrame) -> set[tuple[str, str]]:
#|    return {
#|        (normalize_text(row["site"]), normalize_text(row["panel_id"]))
#|        for row in abrupt_df.to_dict(orient="records")
#|        if normalize_text(row["site"]) and normalize_text(row["panel_id"])
#|    }
#|
#|
#|def earliest_warning_date(reaudit_row: pd.Series, gate_df: pd.DataFrame) -> pd.Timestamp | None:
#|    candidates = [
#|        to_timestamp(reaudit_row.get("first_warning_date")),
#|        earliest_true_date(gate_df, "ews_warning"),
#|    ]
#|    parsed = [value for value in candidates if value is not None]
#|    if not parsed:
#|        return None
#|    return min(parsed)
#|
#|
#|def abrupt_positive_evidence_exists(
#|    key: tuple[str, str],
#|    abrupt_keys: set[tuple[str, str]],
#|    core_df: pd.DataFrame,
#|) -> int:
#|    if key in abrupt_keys:
#|        return 1
#|    if earliest_true_date(core_df, "final_fault") is not None:
#|        return 1
#|    if earliest_true_date(core_df, "critical_fault") is not None:
#|        return 1
#|    return 0
#|
#|
#|def determine_event_redecision(
#|    reaudit_row: pd.Series,
#|    abrupt_positive_flag: int,
#|    first_final_fault_date: pd.Timestamp | None,
#|    dead_diag_date: pd.Timestamp | None,
#|) -> EventRedecision:
#|    retrospective_onset = to_timestamp(reaudit_row.get("retrospective_onset_date"))
#|    strict_trigger = to_timestamp(reaudit_row.get("strict_trigger_date"))
#|    onset_confidence = normalize_text(reaudit_row.get("onset_confidence"))
#|    onset_method = normalize_text(reaudit_row.get("onset_method"))
#|
#|    precursor_rule = (
#|        retrospective_onset is not None
#|        and strict_trigger is not None
#|        and retrospective_onset < strict_trigger
#|        and onset_confidence == "high"
#|        and onset_method == "persistent_5of7"
#|    )
#|    abrupt_rule = abrupt_positive_flag == 1 and (
#|        retrospective_onset is None
#|        or (
#|            retrospective_onset is not None
#|            and strict_trigger is not None
#|            and retrospective_onset == strict_trigger
#|            and onset_method == "strict_trigger_fallback"
#|            and onset_confidence != "high"
#|        )
#|    )
#|
#|    if precursor_rule:
#|        event_type = "전조형 고장"
#|        event_rule = (
#|            "retrospective_onset_date 비공란, strict_trigger_date 비공란, "
#|            "retrospective_onset_date < strict_trigger_date, onset_confidence=high, "
#|            "onset_method=persistent_5of7 이 모두 성립"
#|        )
#|    elif abrupt_rule:
#|        event_type = "급작 고장"
#|        event_rule = (
#|            "abrupt positive evidence 가 있고, retrospective_onset_date 가 공란이거나 "
#|            "retrospective_onset_date == strict_trigger_date 이면서 onset_method=strict_trigger_fallback, "
#|            "onset_confidence != high 인 same-day fallback onset 이라 급작 고장으로 둠"
#|        )
#|    else:
#|        event_type = "고장유형 보류"
#|        event_rule = "전조형 고장 규칙과 급작 고장 규칙을 모두 만족하지 않음"
#|
#|    abrupt_ending = (
#|        first_final_fault_date is not None
#|        and strict_trigger is not None
#|        and first_final_fault_date == strict_trigger
#|        and dead_diag_date is not None
#|        and dead_diag_date <= strict_trigger + pd.Timedelta(days=1)
#|    )
#|    if abrupt_ending:
#|        terminal_pattern = "급격 종료"
#|        terminal_rule = "first_final_fault_date == strict_trigger_date 이고 dead_diag_date <= strict_trigger_date + 1 day"
#|    elif event_type == "급작 고장":
#|        terminal_pattern = "급작 발생"
#|        terminal_rule = "급격 종료 규칙은 아니지만 사건유형_재판정_ko == 급작 고장 이라 급작 발생으로 둠"
#|    elif event_type == "전조형 고장":
#|        terminal_pattern = "진행성 악화"
#|        terminal_rule = "사건유형_재판정_ko == 전조형 고장 이고 급격 종료 규칙은 아니므로 진행성 악화로 둠"
#|    else:
#|        terminal_pattern = "불충분"
#|        terminal_rule = "stored field 만으로 terminal failure pattern 을 더 좁히기 어려워 불충분으로 둠"
#|
#|    return EventRedecision(
#|        event_type_ko=event_type,
#|        terminal_pattern_ko=terminal_pattern,
#|        event_rule_ko=event_rule,
#|        terminal_rule_ko=terminal_rule,
#|        abrupt_positive_flag=abrupt_positive_flag,
#|    )
#|
#|
#|def load_site_frame(root: Path, site: str, filename: str) -> pd.DataFrame:
#|    return read_csv(root / "data" / site / "out" / filename, required=True)
#|
#|
#|def load_optional_vendor_row(vendor_df: pd.DataFrame, site: str, panel_id: str) -> pd.Series | None:
#|    if vendor_df.empty:
#|        return None
#|    row_df = exact_panel_rows(vendor_df, panel_id, site=site)
#|    if row_df.empty:
#|        return None
#|    return row_df.iloc[0]
#|
#|
#|def build_audit(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, str]:
#|    share_dir = root / "_share"
#|    verdict_df = read_csv(share_dir / PANEL_VERDICT_NAME)
#|    abrupt_df = read_csv(share_dir / ABRUPT6_NAME)
#|    precursor_truth_df = read_csv(share_dir / PRECURSOR_TRUTH_NAME)
#|    reaudit_df = read_csv(share_dir / REAUDIT_NAME)
#|    vendor_df = read_csv(share_dir / VENDOR_ADJUDICATION_NAME, required=False)
#|
#|    ensure_columns(
#|        verdict_df,
#|        [
#|            "site",
#|            "panel_id",
#|            "패널고장여부_ko",
#|            "사건유형_ko",
#|            "최종고장양상_ko",
#|            "전조흔적_flag",
#|            "순수급작_flag",
#|            "전조평가셋편입_flag",
#|            "급작평가셋편입_flag",
#|        ],
#|        PANEL_VERDICT_NAME,
#|    )
#|    ensure_columns(abrupt_df, ["site", "panel_id"], ABRUPT6_NAME)
#|    ensure_columns(
#|        precursor_truth_df,
#|        ["site", "preferred_precursor_onset_date"],
#|        PRECURSOR_TRUTH_NAME,
#|    )
#|    ensure_columns(
#|        reaudit_df,
#|        ["site", "panel_id", "retrospective_onset_date", "strict_trigger_date", "onset_confidence", "onset_method"],
#|        REAUDIT_NAME,
#|    )
#|
#|    fault_df = verdict_df.loc[verdict_df["패널고장여부_ko"].eq("고장")].copy()
#|    fault_df = fault_df.sort_values(["site", "panel_id"]).drop_duplicates(subset=["site", "panel_id"], keep="first")
#|    if len(fault_df) != 6:
#|        raise SystemExit(f"expected current fault panel count to be 6, found {len(fault_df)}")
#|
#|    abrupt_keys = build_abrupt_keys(abrupt_df)
#|    precursor_eval_keys = build_precursor_eval_keys(precursor_truth_df)
#|
#|    site_cache: dict[tuple[str, str], pd.DataFrame] = {}
#|    audit_rows: list[dict[str, object]] = []
#|    explicit_precursor_rule_hits = 0
#|
#|    for row in fault_df.to_dict(orient="records"):
#|        site = normalize_text(row["site"])
#|        panel_id = normalize_text(row["panel_id"])
#|        key = (site, panel_id)
#|
#|        core_df = site_cache.setdefault((site, "core"), load_site_frame(root, site, "panel_day_core.csv"))
#|        gate_df = site_cache.setdefault((site, "gate"), load_site_frame(root, site, "ae_simple_local_precursor_gate_daily.csv"))
#|
#|        core_panel_df = exact_panel_rows(core_df, panel_id, site=site)
#|        gate_panel_df = exact_panel_rows(gate_df, panel_id, site=site)
#|        reaudit_panel_df = exact_panel_rows(reaudit_df, panel_id, site=site)
#|        if reaudit_panel_df.empty:
#|            raise SystemExit(f"missing reaudit row for fault panel {site}/{panel_id}")
#|        reaudit_row = reaudit_panel_df.iloc[0]
#|
#|        earliest_warning = earliest_warning_date(reaudit_row, gate_panel_df)
#|        retrospective_onset = to_timestamp(reaudit_row.get("retrospective_onset_date"))
#|        strict_trigger = to_timestamp(reaudit_row.get("strict_trigger_date"))
#|        first_final_fault_date = earliest_true_date(core_panel_df, "final_fault")
#|        dead_diag_date = repeated_core_date(core_panel_df, "dead_diag_date")
#|        abrupt_positive_flag = abrupt_positive_evidence_exists(key, abrupt_keys, core_panel_df)
#|        redecision = determine_event_redecision(
#|            reaudit_row=reaudit_row,
#|            abrupt_positive_flag=abrupt_positive_flag,
#|            first_final_fault_date=first_final_fault_date,
#|            dead_diag_date=dead_diag_date,
#|        )
#|
#|        current_event = normalize_text(row["사건유형_ko"])
#|        current_terminal = normalize_text(row["최종고장양상_ko"])
#|        needs_correction = int(
#|            current_event != redecision.event_type_ko
#|            or current_terminal != redecision.terminal_pattern_ko
#|        )
#|
#|        vendor_row = load_optional_vendor_row(vendor_df, site, panel_id)
#|        vendor_hint_parts: list[str] = []
#|        if vendor_row is not None:
#|            for column in ("vendor_fault_family", "vendor_reply_class"):
#|                value = normalize_text(vendor_row.get(column))
#|                if value:
#|                    vendor_hint_parts.append(f"{column}={value}")
#|
#|        reason_parts = [
#|            redecision.event_rule_ko,
#|            redecision.terminal_rule_ko,
#|            f"abrupt_positive_evidence_flag={abrupt_positive_flag}",
#|        ]
#|        if key in precursor_eval_keys:
#|            reason_parts.append("strict precursor truth positive 포함")
#|        if vendor_hint_parts:
#|            reason_parts.append(", ".join(vendor_hint_parts))
#|
#|        precursor_rule_hit = int(redecision.event_type_ko == "전조형 고장")
#|        explicit_precursor_rule_hits += precursor_rule_hit
#|
#|        audit_rows.append(
#|            {
#|                "site": site,
#|                "panel_id": panel_id,
#|                "현재표_사건유형_ko": current_event,
#|                "현재표_최종고장양상_ko": current_terminal,
#|                "earliest_warning_date": format_date(earliest_warning),
#|                "retrospective_onset_date": format_date(retrospective_onset),
#|                "strict_trigger_date": format_date(strict_trigger),
#|                "first_final_fault_date": format_date(first_final_fault_date),
#|                "dead_diag_date": format_date(dead_diag_date),
#|                "onset_confidence": normalize_text(reaudit_row.get("onset_confidence")),
#|                "onset_method": normalize_text(reaudit_row.get("onset_method")),
#|                "전조흔적_flag": int(pd.to_numeric(pd.Series([row["전조흔적_flag"]]), errors="coerce").fillna(0).iloc[0]),
#|                "순수급작_flag": int(pd.to_numeric(pd.Series([row["순수급작_flag"]]), errors="coerce").fillna(0).iloc[0]),
#|                "전조평가셋편입_flag": int(pd.to_numeric(pd.Series([row["전조평가셋편입_flag"]]), errors="coerce").fillna(0).iloc[0]),
#|                "급작평가셋편입_flag": int(pd.to_numeric(pd.Series([row["급작평가셋편입_flag"]]), errors="coerce").fillna(0).iloc[0]),
#|                "사건유형_재판정_ko": redecision.event_type_ko,
#|                "최종고장양상_재판정_ko": redecision.terminal_pattern_ko,
#|                "재판정_근거_ko": "; ".join(part for part in reason_parts if part),
#|                "현재표_보정필요여부_flag": needs_correction,
#|            }
#|        )
#|
#|    audit_df = pd.DataFrame(audit_rows).reindex(columns=AUDIT_COLS)
#|    if audit_df[["site", "panel_id"]].duplicated().any():
#|        raise SystemExit("fault panel audit output must be unique by (site, panel_id)")
#|    if len(audit_df) != 6:
#|        raise SystemExit(f"fault panel audit output must contain exactly 6 rows, found {len(audit_df)}")
#|
#|    c429_df = audit_df.loc[audit_df["site"].eq(TARGET_SITE) & audit_df["panel_id"].eq(TARGET_PANEL_ID)].copy()
#|    if len(c429_df) != 1:
#|        raise SystemExit("c42997...1.1 must appear exactly once in fault panel event audit")
#|    if normalize_text(c429_df.iloc[0]["사건유형_재판정_ko"]) != "전조형 고장":
#|        raise SystemExit("c42997...1.1 must re-evaluate to 전조형 고장 under explicit rule")
#|
#|    precursor_rule_mask = (
#|        audit_df["retrospective_onset_date"].map(normalize_text).ne("")
#|        & audit_df["strict_trigger_date"].map(normalize_text).ne("")
#|        & (
#|            pd.to_datetime(audit_df["retrospective_onset_date"], errors="coerce")
#|            < pd.to_datetime(audit_df["strict_trigger_date"], errors="coerce")
#|        )
#|        & audit_df["onset_confidence"].eq("high")
#|        & audit_df["onset_method"].eq("persistent_5of7")
#|    )
#|    if audit_df.loc[precursor_rule_mask, "사건유형_재판정_ko"].ne("전조형 고장").any():
#|        raise SystemExit("any fault panel meeting the explicit precursor rule must re-evaluate to 전조형 고장")
#|    if explicit_precursor_rule_hits != int(precursor_rule_mask.sum()):
#|        raise SystemExit("explicit precursor rule hit count mismatch")
#|
#|    mismatch_mask = (
#|        (audit_df["사건유형_재판정_ko"].eq("전조형 고장") & audit_df["전조평가셋편입_flag"].eq(0))
#|        | (audit_df["사건유형_재판정_ko"].eq("급작 고장") & audit_df["급작평가셋편입_flag"].eq(0))
#|    )
#|
#|    summary_row = {
#|        "고유_고장패널수": int(len(audit_df)),
#|        "사건유형_재판정_전조형수": int(audit_df["사건유형_재판정_ko"].eq("전조형 고장").sum()),
#|        "사건유형_재판정_급작수": int(audit_df["사건유형_재판정_ko"].eq("급작 고장").sum()),
#|        "사건유형_재판정_보류수": int(audit_df["사건유형_재판정_ko"].eq("고장유형 보류").sum()),
#|        "최종고장양상_급격종료수": int(audit_df["최종고장양상_재판정_ko"].eq("급격 종료").sum()),
#|        "전조흔적_패널수": int(pd.to_numeric(audit_df["전조흔적_flag"], errors="coerce").fillna(0).sum()),
#|        "순수급작_패널수": int(pd.to_numeric(audit_df["순수급작_flag"], errors="coerce").fillna(0).sum()),
#|        "전조평가셋편입_패널수": int(pd.to_numeric(audit_df["전조평가셋편입_flag"], errors="coerce").fillna(0).sum()),
#|        "급작평가셋편입_패널수": int(pd.to_numeric(audit_df["급작평가셋편입_flag"], errors="coerce").fillna(0).sum()),
#|        "해석과평가셋불일치_패널수": int(mismatch_mask.sum()),
#|        "현재표_보정필요_패널수": int(pd.to_numeric(audit_df["현재표_보정필요여부_flag"], errors="coerce").fillna(0).sum()),
#|        "note_ko": (
#|            f"current fault panel {len(audit_df)}건에 explicit stored-field rule 을 적용했다. "
#|            f"재판정 결과 전조형 {int(audit_df['사건유형_재판정_ko'].eq('전조형 고장').sum())}건, "
#|            f"급작 {int(audit_df['사건유형_재판정_ko'].eq('급작 고장').sum())}건, "
#|            f"보류 {int(audit_df['사건유형_재판정_ko'].eq('고장유형 보류').sum())}건이다. "
#|            f"사건 해석상 전조형 패널은 {int(audit_df['사건유형_재판정_ko'].eq('전조형 고장').sum())}건이지만, "
#|            f"strict precursor eval set 편입은 {int(pd.to_numeric(audit_df['전조평가셋편입_flag'], errors='coerce').fillna(0).sum())}건이다. "
#|            f"재판정과 evaluation-set inclusion 이 어긋나는 fault panel 은 {int(mismatch_mask.sum())}건이고, 이 표를 downstream event-semantics authoritative source 로 쓴다."
#|        ),
#|    }
#|    summary_df = pd.DataFrame([summary_row]).reindex(columns=SUMMARY_COLS)
#|
#|    mismatch_df = audit_df.loc[mismatch_mask, ["site", "panel_id", "사건유형_재판정_ko"]].copy()
#|    correction_df = audit_df.loc[audit_df["현재표_보정필요여부_flag"].eq(1), ["site", "panel_id", "현재표_사건유형_ko", "사건유형_재판정_ko", "현재표_최종고장양상_ko", "최종고장양상_재판정_ko"]].copy()
#|    pure_abrupt_df = audit_df.loc[audit_df["사건유형_재판정_ko"].eq("급작 고장"), ["site", "panel_id"]].copy()
#|
#|    mismatch_lines = [
#|        f"- {row.site} / {row.panel_id} / 재판정={row.사건유형_재판정_ko}"
#|        for row in mismatch_df.itertuples(index=False)
#|    ] or ["- 없음"]
#|    correction_lines = [
#|        f"- {row.site} / {row.panel_id} / 현재표={row.현재표_사건유형_ko}·{row.현재표_최종고장양상_ko} -> 재판정={row.사건유형_재판정_ko}·{row.최종고장양상_재판정_ko}"
#|        for row in correction_df.itertuples(index=False)
#|    ] or ["- 없음"]
#|    pure_abrupt_lines = [
#|        f"- {row.site} / {row.panel_id}"
#|        for row in pure_abrupt_df.itertuples(index=False)
#|    ] or ["- 없음"]
#|
#|    note = "\n".join(
#|        [
#|            "## 1. 전체 고장 패널 전수 결과",
#|            f"- 현재 고장 패널 {len(audit_df)}건을 explicit stored-field rule 로 다시 봤다.",
#|            f"- 재판정 결과는 전조형 고장 {summary_row['사건유형_재판정_전조형수']}건, 급작 고장 {summary_row['사건유형_재판정_급작수']}건, 고장유형 보류 {summary_row['사건유형_재판정_보류수']}건이다.",
#|            "- 이 audit 표는 downstream 사건유형/최종고장양상 reconciliation 에서 authoritative source 로 쓴다.",
#|            f"- 현재표 보정 필요 패널은 {summary_row['현재표_보정필요_패널수']}건이다.",
#|            "",
#|            "## 2. 순수 급작 패널 수",
#|            f"- strict rule 재판정 기준 순수 급작 패널 수는 {summary_row['사건유형_재판정_급작수']}건이다.",
#|            *pure_abrupt_lines,
#|            "",
#|            "## 3. 전조흔적은 있지만 평가셋에 안 들어간 패널",
#|            f"- 사건 해석상 전조형 패널은 {summary_row['사건유형_재판정_전조형수']}건이지만, strict precursor eval set 편입은 {summary_row['전조평가셋편입_패널수']}건이다.",
#|            f"- 따라서 해석과 evaluation-set inclusion 이 어긋나는 고장 패널은 {summary_row['해석과평가셋불일치_패널수']}건이다.",
#|            *mismatch_lines,
#|            "",
#|            "## 4. 지금 바로 고쳐야 하는 패널",
#|            *correction_lines,
#|            "",
#|        ]
#|    )
#|    return audit_df, summary_df, note
#|
#|
#|def write_outputs(root: Path, audit_df: pd.DataFrame, summary_df: pd.DataFrame, note: str) -> None:
#|    write_csv(audit_df, root / AUDIT_OUTPUT)
#|    write_csv(summary_df, root / SUMMARY_OUTPUT)
#|    write_text(note, root / NOTE_OUTPUT)
#|
#|
#|def main() -> None:
#|    args = parse_args()
#|    root = args.root.resolve()
#|    audit_df, summary_df, note = build_audit(root)
#|    write_outputs(root, audit_df, summary_df, note)
#|    print(f"Wrote {AUDIT_OUTPUT}")
#|    print(f"Wrote {SUMMARY_OUTPUT}")
#|    print(f"Wrote {NOTE_OUTPUT}")
#|
#|
#|if __name__ == "__main__":
#|    main()
# pvdiag_payload_end
# endregion
# region payload: live_gpvs_builder
# pvdiag_payload_file {"bytes": 31022, "endswith_newline": true, "lines": 714, "path": "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_gpvs_evidence_pack_v1.py", "role": "live_gpvs_builder", "sha256": "2864b9dc1b6151b88f3205564e9b758192484d727a06550694a925ce140a1972"}
#|#!/usr/bin/env python3
#|from __future__ import annotations
#|
#|import argparse
#|import re
#|from pathlib import Path
#|
#|import pandas as pd
#|
#|
#|REPO_ROOT = Path(__file__).resolve().parents[2]
#|
#|VERDICT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
#|FAMILY_EVAL_NAME = "gpvs_fault_family_eval_cases.csv"
#|ATTACH_CANDIDATES_NAME = "panel_day_engine_gpvs_panel_attach_candidates_v1.csv"
#|DETAILED_AUDIT_NAME = "panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv"
#|DETAILED_SANITY_NAME = "panel_day_engine_gpvs_detailed_type_realpanel_sanity_v1.csv"
#|BYTYPE_PROVENANCE_SUMMARY_NAME = "panel_day_engine_gpvs_bytype_provenance_summary_v1.csv"
#|BYTYPE_REBUILD_SUMMARY_NAME = "panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv"
#|MLPE_PANEL_AGREEMENT_NAME = "panel_day_engine_gpvs_mlpe_panel_agreement_v1.csv"
#|MLPE_COMPATIBILITY_SUMMARY_NAME = "panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv"
#|MLPE_MATCHING_TABLE_NAME = "panel_day_engine_gpvs_mlpe_fault_matching_table_v1.csv"
#|MLPE_MATCHING_SUMMARY_NAME = "panel_day_engine_gpvs_mlpe_fault_matching_summary_v1.csv"
#|CANONICAL_DICTIONARY_NAME = "panel_day_engine_gpvs_canonical_dictionary_v1.csv"
#|
#|OUTPUT_PACK_NAME = "panel_day_engine_gpvs_evidence_pack_v1.csv"
#|OUTPUT_SUMMARY_NAME = "panel_day_engine_gpvs_evidence_summary_v1.csv"
#|OUTPUT_NOTE_NAME = "panel_day_engine_gpvs_evidence_note_v1.md"
#|
#|PACK_COLS = [
#|    "site",
#|    "panel_id",
#|    "사건유형_ko",
#|    "최종고장양상_ko",
#|    "커널로그_원인군_ko",
#|    "GPVS_내부판정_ko",
#|    "GPVS_내부판정근거_ko",
#|    "GPVS_외부참조패턴_ko",
#|    "GPVS_외부참조근거_ko",
#|    "GPVS_호환성판정_ko",
#|    "GPVS_호환성근거_ko",
#|    "GPVS_매칭정책_ko",
#|    "GPVS_매칭근거_ko",
#|    "GPVS_최종사용권고_ko",
#|    "GPVS_권고사유_ko",
#|]
#|
#|SUMMARY_COLS = [
#|    "fault_panel_count",
#|    "internal_evidence_available_count",
#|    "external_evidence_available_count",
#|    "compatibility_reference_only_flag",
#|    "core_reference_count",
#|    "core_reference_candidate_count",
#|    "auxiliary_reference_count",
#|    "confounder_flag_count",
#|    "reserved_system_count",
#|    "not_recommended_count",
#|    "final_operational_rule_ko",
#|    "note_ko",
#|]
#|
#|VERDICT_REQUIRED_COLS = [
#|    "site",
#|    "panel_id",
#|    "사건유형_ko",
#|    "최종고장양상_ko",
#|    "커널로그_원인군_ko",
#|    "패널고장여부_ko",
#|]
#|DETAILED_REQUIRED_COLS = [
#|    "site",
#|    "panel_id",
#|    "gpvs_detailed_model_source",
#|    "gpvs_detailed_top1_fault_type",
#|    "gpvs_detailed_top1_score",
#|    "gpvs_detailed_top2_fault_type",
#|    "gpvs_detailed_top2_score",
#|    "gpvs_detailed_margin",
#|]
#|COMPATIBILITY_SUMMARY_REQUIRED_COLS = ["fault_panel_count", "final_recommendation_ko", "note_ko"]
#|MATCHING_SUMMARY_REQUIRED_COLS = [
#|    "canonical_code_count",
#|    "core_reference_count",
#|    "auxiliary_reference_count",
#|    "confounder_count",
#|    "reserved_system_count",
#|    "final_matching_policy_ko",
#|    "note_ko",
#|]
#|
#|INTERNAL_COL_CANDIDATES = ["GPVS_내부참고유형_ko", "GPVS_참고유형_ko"]
#|EXTERNAL_PATTERN_COL_CANDIDATES = ["GPVS_외부참조패턴_ko", "GPVS_외부참조시나리오명_ko"]
#|
#|DEFAULT_CANONICAL_DICTIONARY = {
#|    "F0": {
#|        "current_usage_tier_ko": "baseline",
#|        "mlpe_reference_name_ko": "정상 기준선",
#|        "usage_rule_ko": "비고장 기준선과 drift 비교에만 사용",
#|        "note_ko": "fault명이 아니라 baseline reference로만 노출",
#|    },
#|    "F1": {
#|        "current_usage_tier_ko": "reserved_system_level",
#|        "mlpe_reference_name_ko": "인버터 전력변환부 시스템 시나리오",
#|        "usage_rule_ko": "MLPE direct fault명이 아니라 통합 결과표 후보축으로만 보류",
#|        "note_ko": "system-level reserve code",
#|    },
#|    "F2": {
#|        "current_usage_tier_ko": "auxiliary_reference",
#|        "mlpe_reference_name_ko": "제어/계측 이상 보조 힌트",
#|        "usage_rule_ko": "direct root-cause가 아니라 제어·계측 이상 힌트로만 사용",
#|        "note_ko": "control/measurement hint only",
#|    },
#|    "F3": {
#|        "current_usage_tier_ko": "confounder_only",
#|        "mlpe_reference_name_ko": "계통 교란 플래그",
#|        "usage_rule_ko": "fault label이 아니라 confounder flag로만 사용",
#|        "note_ko": "disturbance flag only",
#|    },
#|    "F4": {
#|        "current_usage_tier_ko": "core_reference",
#|        "mlpe_reference_name_ko": "패널·어레이 mismatch 핵심 참조",
#|        "usage_rule_ko": "MLPE 패널·어레이 불균형 해석의 핵심 reference로 사용",
#|        "note_ko": "panel/array imbalance reference",
#|    },
#|    "F5": {
#|        "current_usage_tier_ko": "core_reference_candidate",
#|        "mlpe_reference_name_ko": "부분 개방회로 계열 핵심 참조 후보",
#|        "usage_rule_ko": "케이블 접점불량(단선) 가설의 핵심 reference candidate로 유지",
#|        "note_ko": "candidate until real-panel evidence grows",
#|    },
#|    "F6": {
#|        "current_usage_tier_ko": "reserved_system_level",
#|        "mlpe_reference_name_ko": "제어기 gain 이상 시스템 시나리오",
#|        "usage_rule_ko": "MLPE direct fault명이 아니라 통합 결과표 후보축으로만 보류",
#|        "note_ko": "system-level reserve code",
#|    },
#|    "F7": {
#|        "current_usage_tier_ko": "reserved_system_level",
#|        "mlpe_reference_name_ko": "제어기 시정수 이상 시스템 시나리오",
#|        "usage_rule_ko": "MLPE direct fault명이 아니라 통합 결과표 후보축으로만 보류",
#|        "note_ko": "system-level reserve code",
#|    },
#|}
#|
#|DEFAULT_EXTERNAL_PATTERN_BY_CODE = {
#|    "F0": "정상 기준선",
#|    "F1": "전력변환 이상형",
#|    "F2": "장치 응답 이상형",
#|    "F3": "계통 교란형",
#|    "F4": "국소 출력 불균형형",
#|    "F5": "부분 개방·접속 이상형",
#|    "F6": "제어기 gain 이상형",
#|    "F7": "제어기 시정수 이상형",
#|}
#|
#|TIER_TO_POLICY = {
#|    "baseline": "기준선",
#|    "core_reference": "핵심참조",
#|    "core_reference_candidate": "핵심참조후보",
#|    "auxiliary_reference": "보조참조",
#|    "confounder_only": "교란플래그",
#|    "reserved_system_level": "시스템보류",
#|}
#|
#|MATCHING_REASON_BY_CODE = {
#|    "F0": "F0는 비고장 기준선과 drift 비교 기준으로만 사용한다",
#|    "F1": "F1은 현재 패널 단독표보다 시스템/통합 결과표 후보축으로만 보류한다",
#|    "F2": "F2는 장치 응답 이상 힌트로만 사용하고 direct root-cause로 읽지 않는다",
#|    "F3": "F3는 외부 계통 교란 플래그로만 남긴다",
#|    "F4": "F4는 패널·어레이 불균형 해석에 가장 유용한 핵심 reference code다",
#|    "F5": "F5는 부분 개방·접속 약화 계열과 가장 가까운 핵심참조후보다",
#|    "F6": "F6은 현재 패널 단독표보다 시스템/통합 결과표 후보축으로만 보류한다",
#|    "F7": "F7은 현재 패널 단독표보다 시스템/통합 결과표 후보축으로만 보류한다",
#|}
#|
#|
#|def parse_args() -> argparse.Namespace:
#|    parser = argparse.ArgumentParser(
#|        description="Aggregate current GPVS evidence layers for the real fault panels."
#|    )
#|    parser.add_argument(
#|        "--root",
#|        type=Path,
#|        default=REPO_ROOT,
#|        help="Repository root. Defaults to project root.",
#|    )
#|    return parser.parse_args()
#|
#|
#|def normalize_text(value: object) -> str:
#|    if pd.isna(value):
#|        return ""
#|    text = str(value).strip()
#|    return "" if text.lower() == "nan" else text
#|
#|
#|def read_csv(path: Path) -> pd.DataFrame:
#|    if not path.exists():
#|        raise SystemExit(f"missing input: {path}")
#|    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
#|
#|
#|def read_optional_csv(path: Path) -> pd.DataFrame:
#|    if not path.exists():
#|        return pd.DataFrame()
#|    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
#|
#|
#|def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
#|    missing = [column for column in required if column not in df.columns]
#|    if missing:
#|        raise SystemExit(f"{name} missing columns: {missing}")
#|
#|
#|def canonicalize_gpvs_code(value: object) -> str:
#|    text = normalize_text(value)
#|    match = re.match(r"^(F[0-7])", text)
#|    return match.group(1) if match else ""
#|
#|
#|def as_key(site: object, panel_id: object) -> tuple[str, str]:
#|    return normalize_text(site), normalize_text(panel_id)
#|
#|
#|def lookup_map(df: pd.DataFrame) -> dict[tuple[str, str], dict[str, object]]:
#|    if df.empty or "site" not in df.columns or "panel_id" not in df.columns:
#|        return {}
#|    records: dict[tuple[str, str], dict[str, object]] = {}
#|    for row in df.to_dict(orient="records"):
#|        records[as_key(row.get("site"), row.get("panel_id"))] = row
#|    return records
#|
#|
#|def first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str:
#|    for candidate in candidates:
#|        if candidate in df.columns:
#|            return candidate
#|    return ""
#|
#|
#|def first_row_text(row: dict[str, object], candidates: list[str]) -> str:
#|    for candidate in candidates:
#|        text = normalize_text(row.get(candidate))
#|        if text:
#|            return text
#|    return ""
#|
#|
#|def fmt_score(value: object) -> str:
#|    text = normalize_text(value)
#|    if not text:
#|        return ""
#|    try:
#|        return f"{float(text):.3f}"
#|    except ValueError:
#|        return text
#|
#|
#|def build_canonical_dictionary_map(df: pd.DataFrame) -> dict[str, dict[str, str]]:
#|    canonical_map = {
#|        code: payload.copy()
#|        for code, payload in DEFAULT_CANONICAL_DICTIONARY.items()
#|    }
#|    if df.empty or "canonical_gpvs_code" not in df.columns:
#|        return canonical_map
#|    for row in df.to_dict(orient="records"):
#|        code = normalize_text(row.get("canonical_gpvs_code"))
#|        if not code:
#|            continue
#|        payload = canonical_map.setdefault(code, {})
#|        for field in ["current_usage_tier_ko", "mlpe_reference_name_ko", "usage_rule_ko", "note_ko"]:
#|            text = normalize_text(row.get(field))
#|            if text:
#|                payload[field] = text
#|    return canonical_map
#|
#|
#|def build_matching_table_map(df: pd.DataFrame) -> dict[str, list[dict[str, object]]]:
#|    table_map: dict[str, list[dict[str, object]]] = {}
#|    if df.empty or "canonical_gpvs_code" not in df.columns:
#|        return table_map
#|    for row in df.to_dict(orient="records"):
#|        code = normalize_text(row.get("canonical_gpvs_code"))
#|        if not code:
#|            continue
#|        table_map.setdefault(code, []).append(row)
#|    return table_map
#|
#|
#|def build_internal_evidence(
#|    family_row: dict[str, object] | None,
#|    attach_row: dict[str, object] | None,
#|) -> str:
#|    if family_row:
#|        parts = []
#|        source = normalize_text(family_row.get("prediction_source"))
#|        fallback = normalize_text(family_row.get("fallback_rule_used"))
#|        error_type = normalize_text(family_row.get("error_type"))
#|        pred_family = normalize_text(family_row.get("pred_fault_family"))
#|        vendor_family = normalize_text(family_row.get("vendor_fault_family"))
#|        if source:
#|            parts.append(f"family evaluator source={source}")
#|        if fallback:
#|            parts.append(f"fallback={fallback}")
#|        if error_type:
#|            parts.append(f"error={error_type}")
#|        if pred_family:
#|            parts.append(f"pred={pred_family}")
#|        if vendor_family:
#|            parts.append(f"vendor={vendor_family}")
#|        return ", ".join(parts) if parts else "family evaluator row 확인됨"
#|    if attach_row:
#|        source_key = normalize_text(attach_row.get("source_key_ko"))
#|        note = normalize_text(attach_row.get("비고_ko"))
#|        parts = []
#|        if source_key:
#|            parts.append(f"attach candidate key={source_key}")
#|        if note:
#|            parts.append(note)
#|        return ", ".join(parts) if parts else "attach candidate row 확인됨"
#|    return "근거 파일 미확인"
#|
#|
#|def build_external_pattern(
#|    verdict_row: dict[str, object],
#|    canonical_code: str,
#|    canonical_map: dict[str, dict[str, str]],
#|) -> str:
#|    pattern = first_row_text(verdict_row, EXTERNAL_PATTERN_COL_CANDIDATES)
#|    if pattern:
#|        return pattern
#|    if canonical_code in DEFAULT_EXTERNAL_PATTERN_BY_CODE:
#|        return DEFAULT_EXTERNAL_PATTERN_BY_CODE[canonical_code]
#|    return normalize_text(canonical_map.get(canonical_code, {}).get("mlpe_reference_name_ko"))
#|
#|
#|def build_external_evidence(
#|    detailed_row: dict[str, object] | None,
#|    sanity_row: dict[str, object] | None,
#|) -> str:
#|    if not detailed_row:
#|        return "근거 파일 미확인"
#|    parts = []
#|    model_source = normalize_text(detailed_row.get("gpvs_detailed_model_source"))
#|    top1 = normalize_text(detailed_row.get("gpvs_detailed_top1_fault_type"))
#|    top1_score = fmt_score(detailed_row.get("gpvs_detailed_top1_score"))
#|    top2 = normalize_text(detailed_row.get("gpvs_detailed_top2_fault_type"))
#|    top2_score = fmt_score(detailed_row.get("gpvs_detailed_top2_score"))
#|    margin = fmt_score(detailed_row.get("gpvs_detailed_margin"))
#|    status = normalize_text(detailed_row.get("gpvs_detailed_status_ko"))
#|    reason = normalize_text(detailed_row.get("gpvs_detailed_reason_ko"))
#|    if model_source:
#|        parts.append(f"by-type source={model_source}")
#|    if top1:
#|        parts.append(f"top1={top1}({top1_score})")
#|    if top2:
#|        parts.append(f"top2={top2}({top2_score})")
#|    if margin:
#|        parts.append(f"margin={margin}")
#|    if status:
#|        parts.append(f"status={status}")
#|    if reason:
#|        parts.append(f"reason={reason}")
#|    if sanity_row:
#|        attach_recommendation = normalize_text(sanity_row.get("attach_recommendation_ko"))
#|        consistency = normalize_text(sanity_row.get("family_vs_detail_consistency_ko"))
#|        if attach_recommendation:
#|            parts.append(f"sanity={attach_recommendation}")
#|        if consistency:
#|            parts.append(f"consistency={consistency}")
#|    return ", ".join(parts) if parts else "근거 파일 미확인"
#|
#|
#|def map_usefulness_to_compatibility(
#|    usefulness: str,
#|    summary_final_recommendation: str,
#|) -> str:
#|    if usefulness == "비권장":
#|        return "직접 판정축 사용 비권장"
#|    if usefulness in {"참고가능", "주의참고"}:
#|        return "조건부 참고 가능"
#|    if summary_final_recommendation in {
#|        "참고축으로만 사용",
#|        "조건부 참고 가능",
#|        "직접 판정축 사용 비권장",
#|        "비교곤란",
#|    }:
#|        return summary_final_recommendation
#|    return "비교곤란"
#|
#|
#|def build_compatibility_evidence(
#|    agreement_row: dict[str, object] | None,
#|    compatibility_summary_row: dict[str, object],
#|) -> str:
#|    parts = []
#|    if agreement_row:
#|        family_alignment = normalize_text(agreement_row.get("family_vs_kernellog_alignment_ko"))
#|        scenario_alignment = normalize_text(agreement_row.get("scenario_vs_kernellog_alignment_ko"))
#|        shift = normalize_text(agreement_row.get("feature_shift_bucket_ko"))
#|        usefulness = normalize_text(agreement_row.get("overall_gpvs_reference_usefulness_ko"))
#|        trust_note = normalize_text(agreement_row.get("overall_gpvs_trust_note_ko"))
#|        if family_alignment:
#|            parts.append(f"family_alignment={family_alignment}")
#|        if scenario_alignment:
#|            parts.append(f"scenario_alignment={scenario_alignment}")
#|        if shift:
#|            parts.append(f"feature_shift={shift}")
#|        if usefulness:
#|            parts.append(f"panel_usefulness={usefulness}")
#|        if trust_note:
#|            parts.append(trust_note)
#|    summary_final = normalize_text(compatibility_summary_row.get("final_recommendation_ko"))
#|    summary_note = normalize_text(compatibility_summary_row.get("note_ko"))
#|    strong_shift_count = normalize_text(compatibility_summary_row.get("strong_shift_panel_count"))
#|    scenario_conflict_count = normalize_text(compatibility_summary_row.get("scenario_conflict_count"))
#|    if summary_final:
#|        parts.append(f"summary={summary_final}")
#|    if strong_shift_count:
#|        parts.append(f"strong_shift_panel_count={strong_shift_count}")
#|    if scenario_conflict_count:
#|        parts.append(f"scenario_conflict_count={scenario_conflict_count}")
#|    if summary_note:
#|        parts.append(summary_note)
#|    return "; ".join(part for part in parts if part) or "호환성 근거 미확인"
#|
#|
#|def build_matching_policy(canonical_code: str, canonical_map: dict[str, dict[str, str]]) -> str:
#|    if not canonical_code:
#|        return "비권장"
#|    usage_tier = normalize_text(canonical_map.get(canonical_code, {}).get("current_usage_tier_ko"))
#|    return TIER_TO_POLICY.get(usage_tier, "비권장")
#|
#|
#|def build_matching_evidence(
#|    canonical_code: str,
#|    canonical_map: dict[str, dict[str, str]],
#|    matching_table_map: dict[str, list[dict[str, object]]],
#|) -> str:
#|    if not canonical_code:
#|        return "canonical GPVS code 미확인"
#|    rule = normalize_text(canonical_map.get(canonical_code, {}).get("usage_rule_ko"))
#|    note = normalize_text(canonical_map.get(canonical_code, {}).get("note_ko"))
#|    parts = [MATCHING_REASON_BY_CODE.get(canonical_code, "canonical matching rule 미정의")]
#|    if rule:
#|        parts.append(rule)
#|    if note:
#|        parts.append(note)
#|    rows = matching_table_map.get(canonical_code, [])
#|    if rows:
#|        compact = []
#|        for row in rows:
#|            official_fault = normalize_text(row.get("mlpe_official_fault_ko"))
#|            role = normalize_text(row.get("match_role_ko"))
#|            if official_fault and role:
#|                compact.append(f"{official_fault}:{role}")
#|        if compact:
#|            parts.append("matching=" + " / ".join(compact))
#|    return "; ".join(part for part in parts if part)
#|
#|
#|def combine_final_recommendation(
#|    matching_policy: str,
#|    compatibility_judgment: str,
#|    has_internal_evidence: bool,
#|    has_external_evidence: bool,
#|) -> str:
#|    if not has_internal_evidence or not has_external_evidence:
#|        return "비권장"
#|    if matching_policy == "비권장":
#|        return "비권장"
#|    if matching_policy in {
#|        "핵심참조",
#|        "핵심참조후보",
#|        "보조참조",
#|        "교란플래그",
#|        "시스템보류",
#|        "기준선",
#|    }:
#|        return matching_policy
#|    return "비권장"
#|
#|
#|def build_recommendation_reason(
#|    final_recommendation: str,
#|    compatibility_judgment: str,
#|    matching_policy: str,
#|    external_pattern: str,
#|    canonical_code: str,
#|) -> str:
#|    pattern_or_code = external_pattern or canonical_code or "GPVS reference"
#|    if final_recommendation == "핵심참조":
#|        return f"{pattern_or_code}는 direct root-cause가 아니라 reference-only 핵심참조로만 사용한다."
#|    if final_recommendation == "핵심참조후보":
#|        return f"{pattern_or_code}는 direct root-cause가 아니라 reference-only 핵심참조후보로만 사용한다."
#|    if final_recommendation == "보조참조":
#|        return f"{pattern_or_code}는 직접 root-cause 판정에는 쓰지 말고 보조참조로만 사용한다."
#|    if final_recommendation == "교란플래그":
#|        return f"{pattern_or_code}는 고장명보다 교란 신호를 표시하는 용도로만 쓰는 것이 안전하다."
#|    if final_recommendation == "시스템보류":
#|        return f"{pattern_or_code}는 현재 패널 단독표보다 시스템/통합 결과표 후보축으로만 보류한다."
#|    if final_recommendation == "기준선":
#|        return f"{pattern_or_code}는 fault명이 아니라 비교 기준선으로만 사용한다."
#|    if matching_policy == "비권장":
#|        return f"{pattern_or_code}는 matching policy 자체가 비권장이라 direct root-cause로도 reference로도 쓰지 않는다."
#|    return f"{pattern_or_code}는 required evidence가 부족하거나 unusable 상태라 비권장으로 둔다."
#|
#|
#|def main() -> None:
#|    args = parse_args()
#|    share_dir = args.root / "_share"
#|
#|    verdict_df = read_csv(share_dir / VERDICT_NAME)
#|    ensure_columns(verdict_df, VERDICT_REQUIRED_COLS, VERDICT_NAME)
#|    detailed_df = read_csv(share_dir / DETAILED_AUDIT_NAME)
#|    ensure_columns(detailed_df, DETAILED_REQUIRED_COLS, DETAILED_AUDIT_NAME)
#|    compatibility_summary_df = read_csv(share_dir / MLPE_COMPATIBILITY_SUMMARY_NAME)
#|    ensure_columns(
#|        compatibility_summary_df,
#|        COMPATIBILITY_SUMMARY_REQUIRED_COLS,
#|        MLPE_COMPATIBILITY_SUMMARY_NAME,
#|    )
#|    matching_table_df = read_csv(share_dir / MLPE_MATCHING_TABLE_NAME)
#|    matching_summary_df = read_csv(share_dir / MLPE_MATCHING_SUMMARY_NAME)
#|    ensure_columns(
#|        matching_summary_df,
#|        MATCHING_SUMMARY_REQUIRED_COLS,
#|        MLPE_MATCHING_SUMMARY_NAME,
#|    )
#|
#|    family_eval_df = read_optional_csv(share_dir / FAMILY_EVAL_NAME)
#|    attach_candidates_df = read_optional_csv(share_dir / ATTACH_CANDIDATES_NAME)
#|    detailed_sanity_df = read_optional_csv(share_dir / DETAILED_SANITY_NAME)
#|    provenance_summary_df = read_optional_csv(share_dir / BYTYPE_PROVENANCE_SUMMARY_NAME)
#|    rebuild_summary_df = read_optional_csv(share_dir / BYTYPE_REBUILD_SUMMARY_NAME)
#|    panel_agreement_df = read_optional_csv(share_dir / MLPE_PANEL_AGREEMENT_NAME)
#|    canonical_dictionary_df = read_optional_csv(share_dir / CANONICAL_DICTIONARY_NAME)
#|
#|    internal_col = first_existing_column(verdict_df, INTERNAL_COL_CANDIDATES)
#|    external_col = first_existing_column(verdict_df, EXTERNAL_PATTERN_COL_CANDIDATES)
#|
#|    fault_df = verdict_df[verdict_df["패널고장여부_ko"].map(normalize_text) == "고장"].copy()
#|    if fault_df.empty:
#|        raise SystemExit("no current fault panels found in verdict table")
#|
#|    family_eval_map = lookup_map(family_eval_df)
#|    attach_candidates_map = lookup_map(attach_candidates_df)
#|    detailed_map = lookup_map(detailed_df)
#|    detailed_sanity_map = lookup_map(detailed_sanity_df)
#|    panel_agreement_map = lookup_map(panel_agreement_df)
#|
#|    compatibility_summary_row = compatibility_summary_df.iloc[0].to_dict()
#|    matching_summary_row = matching_summary_df.iloc[0].to_dict()
#|    provenance_summary_row = provenance_summary_df.iloc[0].to_dict() if not provenance_summary_df.empty else {}
#|    rebuild_summary_row = rebuild_summary_df.iloc[0].to_dict() if not rebuild_summary_df.empty else {}
#|
#|    canonical_map = build_canonical_dictionary_map(canonical_dictionary_df)
#|    matching_table_map = build_matching_table_map(matching_table_df)
#|
#|    pack_rows: list[dict[str, object]] = []
#|    for row in fault_df.to_dict(orient="records"):
#|        key = as_key(row.get("site"), row.get("panel_id"))
#|        detailed_row = detailed_map.get(key)
#|        family_row = family_eval_map.get(key)
#|        attach_row = attach_candidates_map.get(key)
#|        agreement_row = panel_agreement_map.get(key)
#|        sanity_row = detailed_sanity_map.get(key)
#|
#|        canonical_code = canonicalize_gpvs_code(
#|            (detailed_row or {}).get("gpvs_detailed_top1_fault_type")
#|        )
#|        internal_verdict = normalize_text(row.get(internal_col)) if internal_col else ""
#|        external_pattern = normalize_text(row.get(external_col)) if external_col else ""
#|        external_pattern = external_pattern or build_external_pattern(row, canonical_code, canonical_map)
#|
#|        usefulness = normalize_text((agreement_row or {}).get("overall_gpvs_reference_usefulness_ko"))
#|        compatibility_judgment = map_usefulness_to_compatibility(
#|            usefulness,
#|            normalize_text(compatibility_summary_row.get("final_recommendation_ko")),
#|        )
#|        matching_policy = build_matching_policy(canonical_code, canonical_map)
#|        internal_evidence = build_internal_evidence(family_row, attach_row)
#|        external_evidence = build_external_evidence(detailed_row, sanity_row)
#|        final_recommendation = combine_final_recommendation(
#|            matching_policy,
#|            compatibility_judgment,
#|            internal_evidence != "근거 파일 미확인",
#|            external_evidence != "근거 파일 미확인",
#|        )
#|
#|        pack_rows.append(
#|            {
#|                "site": normalize_text(row.get("site")),
#|                "panel_id": normalize_text(row.get("panel_id")),
#|                "사건유형_ko": normalize_text(row.get("사건유형_ko")),
#|                "최종고장양상_ko": normalize_text(row.get("최종고장양상_ko")),
#|                "커널로그_원인군_ko": normalize_text(row.get("커널로그_원인군_ko")),
#|                "GPVS_내부판정_ko": internal_verdict,
#|                "GPVS_내부판정근거_ko": internal_evidence,
#|                "GPVS_외부참조패턴_ko": external_pattern,
#|                "GPVS_외부참조근거_ko": external_evidence,
#|                "GPVS_호환성판정_ko": compatibility_judgment,
#|                "GPVS_호환성근거_ko": build_compatibility_evidence(
#|                    agreement_row,
#|                    compatibility_summary_row,
#|                ),
#|                "GPVS_매칭정책_ko": matching_policy,
#|                "GPVS_매칭근거_ko": build_matching_evidence(
#|                    canonical_code,
#|                    canonical_map,
#|                    matching_table_map,
#|                ),
#|                "GPVS_최종사용권고_ko": final_recommendation,
#|                "GPVS_권고사유_ko": build_recommendation_reason(
#|                    final_recommendation,
#|                    compatibility_judgment,
#|                    matching_policy,
#|                    external_pattern,
#|                    canonical_code,
#|                ),
#|            }
#|        )
#|
#|    pack_df = pd.DataFrame(pack_rows).reindex(columns=PACK_COLS)
#|
#|    summary_row = {
#|        "fault_panel_count": len(pack_df),
#|        "internal_evidence_available_count": int(
#|            (pack_df["GPVS_내부판정근거_ko"] != "근거 파일 미확인").sum()
#|        ),
#|        "external_evidence_available_count": int(
#|            (pack_df["GPVS_외부참조근거_ko"] != "근거 파일 미확인").sum()
#|        ),
#|        "compatibility_reference_only_flag": int(
#|            normalize_text(compatibility_summary_row.get("final_recommendation_ko")) == "참고축으로만 사용"
#|        ),
#|        "core_reference_count": int((pack_df["GPVS_최종사용권고_ko"] == "핵심참조").sum()),
#|        "core_reference_candidate_count": int(
#|            (pack_df["GPVS_최종사용권고_ko"] == "핵심참조후보").sum()
#|        ),
#|        "auxiliary_reference_count": int((pack_df["GPVS_최종사용권고_ko"] == "보조참조").sum()),
#|        "confounder_flag_count": int((pack_df["GPVS_최종사용권고_ko"] == "교란플래그").sum()),
#|        "reserved_system_count": int((pack_df["GPVS_최종사용권고_ko"] == "시스템보류").sum()),
#|        "not_recommended_count": int((pack_df["GPVS_최종사용권고_ko"] == "비권장").sum()),
#|        "final_operational_rule_ko": "GPVS는 direct root-cause classifier가 아니라 reference layer로만 사용",
#|        "note_ko": (
#|            f"compatibility={normalize_text(compatibility_summary_row.get('final_recommendation_ko'))}, "
#|            f"matching_policy={normalize_text(matching_summary_row.get('final_matching_policy_ko'))}, "
#|            f"provenance={normalize_text(provenance_summary_row.get('provenance_status')) or '미기록'}, "
#|            f"rebuild_attachable={normalize_text(rebuild_summary_row.get('current_recovered_attachable_flag')) or '미기록'}"
#|        ),
#|    }
#|    summary_df = pd.DataFrame([summary_row]).reindex(columns=SUMMARY_COLS)
#|
#|    current_code_counts = {
#|        code: int(
#|            (
#|                detailed_df["gpvs_detailed_top1_fault_type"]
#|                .map(canonicalize_gpvs_code)
#|                == code
#|            ).sum()
#|        )
#|        for code in sorted(canonical_map)
#|    }
#|    note_lines = [
#|        "# 1. GPVS 내부판정 근거",
#|        f"- 현재 fault panel {len(pack_df)}건 중 내부판정 근거가 확인된 패널은 {summary_row['internal_evidence_available_count']}건입니다.",
#|        "- 내부판정은 family evaluator row가 있으면 prediction_source / fallback_rule / pred_fault_family / vendor_fault_family를 우선 근거로 쓰고, 없으면 attach candidate trace를 보조 근거로 씁니다.",
#|        "- GPVS 내부판정과 외부참조는 서로 다른 레이어입니다.",
#|        "",
#|        "# 2. GPVS 외부참조 근거",
#|        f"- 외부참조 근거가 확인된 패널은 {summary_row['external_evidence_available_count']}건입니다.",
#|        f"- by-type provenance={normalize_text(provenance_summary_row.get('provenance_status')) or '미기록'}, rebuild_attachable={normalize_text(rebuild_summary_row.get('current_recovered_attachable_flag')) or '미기록'} 입니다.",
#|        "- 외부참조는 recovered by-type inference의 top1/top2 score와 margin을 요약한 근거 사례이며 direct root-cause 판정값이 아닙니다.",
#|        "",
#|        "# 3. GPVS↔MLPE 호환성 근거",
#|        f"- compatibility summary는 `{normalize_text(compatibility_summary_row.get('final_recommendation_ko'))}` 입니다.",
#|        f"- summary note: {normalize_text(compatibility_summary_row.get('note_ko'))}",
#|        "- reference-only 는 unusable 을 뜻하지 않습니다.",
#|        "- auxiliary-reference row 는 direct root-cause 사용을 금지한 채 보조참조로는 계속 사용할 수 있습니다.",
#|        "- 호환성 audit 결과에 따라 GPVS는 reference layer로만 사용합니다.",
#|        "",
#|        "# 4. GPVS↔MLPE matching 근거",
#|        f"- matching summary는 `{normalize_text(matching_summary_row.get('final_matching_policy_ko'))}` 입니다.",
#|        "- matching 정책에 따라 F0/F4/F5/F2/F3/F1/F6/F7의 사용 등급이 갈립니다.",
#|        "- 현재 real fault panel support는 "
#|        + ", ".join(
#|            f"{code}={count}"
#|            for code, count in current_code_counts.items()
#|            if count > 0
#|        )
#|        + " 입니다.",
#|        "",
#|        "# 5. 현재 운영 원칙",
#|        "- GPVS 내부판정과 외부참조는 서로 다른 레이어다.",
#|        "- 외부참조는 근거 사례이지 direct root-cause 판정값이 아니다.",
#|        "- 호환성 audit 결과에 따라 GPVS는 reference layer로만 사용한다.",
#|        "- matching 정책에 따라 F0/F4/F5/F2/F3/F1/F6/F7의 사용 등급이 갈린다.",
#|        "- GPVS는 direct root-cause classifier가 아니라 reference layer로만 사용한다.",
#|    ]
#|
#|    output_pack_path = share_dir / OUTPUT_PACK_NAME
#|    output_summary_path = share_dir / OUTPUT_SUMMARY_NAME
#|    output_note_path = share_dir / OUTPUT_NOTE_NAME
#|    output_pack_path.parent.mkdir(parents=True, exist_ok=True)
#|
#|    pack_df.to_csv(output_pack_path, index=False, encoding="utf-8-sig")
#|    summary_df.to_csv(output_summary_path, index=False, encoding="utf-8-sig")
#|    output_note_path.write_text("\n".join(note_lines).strip() + "\n", encoding="utf-8")
#|
#|
#|if __name__ == "__main__":
#|    main()
# pvdiag_payload_end
# endregion
# region payload: live_verdict_builder
# pvdiag_payload_file {"bytes": 119192, "endswith_newline": true, "lines": 2268, "path": "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_panel_multiaxis_verdict_v1.py", "role": "live_verdict_builder", "sha256": "47d9a00a9cfdbe1b471eb93d4c0c8674de0116fca112fff5d9366a03efd6f1e7"}
#|#!/usr/bin/env python3
#|from __future__ import annotations
#|
#|import argparse
#|from pathlib import Path
#|
#|import pandas as pd
#|
#|WORKFLOW_DEFAULT_NAME = "panel_day_engine_operator_workflow_default_v1.csv"
#|ABRUPT6_SYMPTOM_MAP_NAME = "panel_day_engine_abrupt6_symptom_map_v1.csv"
#|KERNELLOG_PROJECT_MAPPING_NAME = "panel_day_engine_kernellog_project_mapping_v1.csv"
#|GPV7_PERF_SUMMARY_NAME = "panel_day_engine_gpv7_perf_summary_v1.csv"
#|FINAL_DECISION_PACK_NAME = "panel_day_engine_project_final_decision_pack_v1.csv"
#|PRECURSOR_ONSET_TRUTH_NAME = "panel_day_engine_precursor_onset_truth_v1.csv"
#|NON_PRECURSOR_PERFORMANCE_CASES_NAME = "panel_day_engine_non_precursor_performance_cases_v1.csv"
#|COMMON_CAUSE_RETROFIT_NAME = "panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv"
#|GPVS_ATTACH_INVENTORY_NAME = "panel_day_engine_gpvs_panel_attach_inventory_v1.csv"
#|GPVS_ATTACH_FEASIBILITY_NAME = "panel_day_engine_gpvs_panel_attach_feasibility_v1.csv"
#|GPVS_ATTACH_CANDIDATES_NAME = "panel_day_engine_gpvs_panel_attach_candidates_v1.csv"
#|PRECURSOR_ABRUPT_CONSISTENCY_CASES_NAME = "panel_day_engine_precursor_abrupt_consistency_cases_v1.csv"
#|PRECURSOR_ABRUPT_CONSISTENCY_SUMMARY_NAME = "panel_day_engine_precursor_abrupt_consistency_summary_v1.csv"
#|PRECURSOR_ABRUPT_CONSISTENCY_RECOMMENDATION_NAME = "panel_day_engine_precursor_abrupt_consistency_recommendation_v1.csv"
#|FORENSIC_SUMMARY_NAME = "panel_day_engine_c42997_1_1_forensic_summary_v1.csv"
#|FAULT_PANEL_EVENT_AUDIT_NAME = "panel_day_engine_fault_panel_event_audit_v1.csv"
#|DETAILED_FAULT_BRIDGE_AUDIT_NAME = "panel_day_engine_detailed_fault_bridge_audit_v1.csv"
#|DETAILED_FAULT_BRIDGE_SUMMARY_NAME = "panel_day_engine_detailed_fault_bridge_summary_v1.csv"
#|GPVS_BYTYPE_REBUILD_SUMMARY_NAME = "panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv"
#|GPVS_DETAILED_TYPE_INFERENCE_AUDIT_NAME = "panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv"
#|GPVS_DETAILED_TYPE_REALPANEL_SANITY_NAME = "panel_day_engine_gpvs_detailed_type_realpanel_sanity_v1.csv"
#|GPVS_MLPE_PANEL_AGREEMENT_NAME = "panel_day_engine_gpvs_mlpe_panel_agreement_v1.csv"
#|GPVS_CANONICAL_DICTIONARY_NAME = "panel_day_engine_gpvs_canonical_dictionary_v1.csv"
#|GPVS_MLPE_FAULT_MATCHING_TABLE_NAME = "panel_day_engine_gpvs_mlpe_fault_matching_table_v1.csv"
#|GPVS_MLPE_COMPATIBILITY_SUMMARY_NAME = "panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv"
#|
#|VERDICT_OUTPUT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
#|EVENT_SUPPLEMENT_OUTPUT_NAME = "panel_day_engine_panel_multiaxis_event_supplement_v1.csv"
#|CLUSTER_SUPPLEMENT_OUTPUT_NAME = "panel_day_engine_panel_multiaxis_cluster_supplement_v1.csv"
#|SUMMARY_OUTPUT_NAME = "panel_day_engine_panel_multiaxis_verdict_summary_v1.csv"
#|
#|VERDICT_COLS = [
#|    "site",
#|    "panel_id",
#|    "사건유형_ko",
#|    "사건유형_해석_ko",
#|    "최종고장양상_ko",
#|    "대표판정_ko",
#|    "사건이력_ko",
#|    "전조흔적_flag",
#|    "순수급작_flag",
#|    "전조평가셋편입_flag",
#|    "급작평가셋편입_flag",
#|    "해석대평가차이_ko",
#|    "운영최초전조발견일",
#|    "운영최초전조마커",
#|    "사건해석상전조시작일",
#|    "benchmark전조시작일",
#|    "전조형이력_flag",
#|    "급작고장이력_flag",
#|    "공통원인이력_flag",
#|    "반복이상이력_flag",
#|    "패널고장여부_ko",
#|    "GPVS_적용대상_ko",
#|    "커널로그_증상명_ko",
#|    "커널로그_원인군_ko",
#|    "GPVS_부착상태_ko",
#|    "GPVS_내부참고유형_ko",
#|    "GPVS_외부참조패턴_ko",
#|    "GPVS_참조사용등급_ko",
#|    "GPVS_참조설명_ko",
#|    "세부fault_type_code",
#|    "세부fault_type_label_ko",
#|    "세부fault_부착상태_ko",
#|    "세부fault_근거파일_ko",
#|    "세부fault_기준일",
#|    "세부fault_보류사유_ko",
#|    "운영위치_ko",
#|    "판정주의_ko",
#|]
#|
#|EVENT_SUPPLEMENT_COLS = [
#|    "site",
#|    "panel_id",
#|    "사건유형_ko",
#|    "사건우선순위",
#|    "대표판정여부_flag",
#|    "운영위치_ko",
#|    "비고_ko",
#|]
#|
#|CLUSTER_COLS = [
#|    "site",
#|    "cluster_id",
#|    "대표판정_ko",
#|    "커널로그_증상명_ko",
#|    "GPVS_참고유형_ko",
#|    "GPVS_근거_ko",
#|    "운영위치_ko",
#|    "판정주의_ko",
#|]
#|
#|SUMMARY_COLS = [
#|    "전체_패널수",
#|    "고유_고장패널수",
#|    "사건해석_전조형_패널수",
#|    "사건해석_급작_패널수",
#|    "사건해석_전조형_급격종료_패널수",
#|    "사건해석_전조형_진행성악화_패널수",
#|    "전조흔적_패널수",
#|    "엄격전조평가셋_패널수",
#|    "순수급작평가셋_패널수",
#|    "해석과평가셋불일치_패널수",
#|    "공통원인이력_패널수",
#|    "반복이상이력_패널수",
#|    "대표판정_급작수",
#|    "대표판정_전조형수",
#|    "대표판정_공통원인수",
#|    "대표판정_반복이상수",
#|    "대표판정_고장유형보류수",
#|    "대표판정_불충분수",
#|    "고장_패널수",
#|    "비고장_패널수",
#|    "미확정_패널수",
#|    "커널로그_증상명_부착수",
#|    "커널로그_원인군_부착수",
#|    "GPVS_적용대상_패널수",
#|    "GPVS_부착수",
#|    "GPVS_미부착수",
#|    "GPVS_비대상수",
#|    "GPVS_미부착_패널key없음수",
#|    "GPVS_미부착_key부족수",
#|    "GPVS_미부착_산출물없음수",
#|    "GPVS_세부fault_부착수",
#|    "GPVS_세부fault_판정유보수",
#|    "GPVS_세부fault_추론불가수",
#|    "GPVS_세부fault_부착패널수",
#|    "GPVS_세부fault_판정유보패널수",
#|    "GPVS_세부fault_비대상패널수",
#|    "GPVS_세부fault_F2M_패널수",
#|    "GPVS_세부fault_F4L_패널수",
#|    "사건보조행수",
#|    "클러스터_보조행수",
#|    "note_ko",
#|]
#|
#|PANEL_LEVEL_PREVIEW_CLASSES = {"queue_run", "watch_now_panel"}
#|CLUSTER_PREVIEW_CLASS = "secondary_value_cluster"
#|GPVS_ABSENCE_REASON = "현재 저장 산출물에는 패널별 GPVS 직접 판정이 없음"
#|GPVS_NON_TARGET_REASON = "고장 패널이 아니어서 GPVS 적용 대상 아님"
#|GPVS_SCENARIO_WARNING = "외부 GPVS 실험 시나리오 설명이며 실제 패널의 물리 root cause를 직접 뜻하지 않음"
#|GPVS_REFERENCE_ONLY_NOTE = "GPVS는 direct root-cause classifier가 아니라 reference layer로만 사용"
#|GPVS_FRONT_PATTERN_NAME_MAP = {
#|    "F0": "정상 기준형",
#|    "F1": "전력변환부 이상형",
#|    "F2": "장치 응답 이상형",
#|    "F3": "외부 계통 교란형",
#|    "F4": "국소 출력 불균형형",
#|    "F5": "부분 개방·접속 이상형",
#|    "F6": "제어 응답 이상형",
#|    "F7": "제어 응답 이상형",
#|}
#|GPVS_FRONT_DESCRIPTION_MAP = {
#|    "F0": "비고장 기준 패턴으로, 다른 패널/구간의 변화량을 비교하는 기준선",
#|    "F1": "인버터 전력변환부 이상과 유사한 패턴",
#|    "F2": "센서/피드백 오류로 장치 응답이 어긋나는 패턴으로, 패널 물리 파손보다 장치 응답 이상 힌트로 해석",
#|    "F3": "외부 계통 변동이나 순간 저전압과 유사한 교란 이벤트 패턴",
#|    "F4": "일부 패널의 출력 균형이 깨지는 패턴으로, 부분 음영뿐 아니라 오염·열화·다이오드/접속 이상 등과 유사하게 보일 수 있음",
#|    "F5": "일부 연결부가 끊기거나 약해진 것처럼 보이는 패턴으로, 커넥터 이탈·접점 불량·부분 단선과 더 잘 이어짐",
#|    "F6": "제어 응답 또는 제어 파라미터 이상과 유사한 패턴",
#|    "F7": "제어 응답 또는 제어 파라미터 이상과 유사한 패턴",
#|}
#|GPVS_REFERENCE_GRADE_MAP = {
#|    "참고가능": "참고가능",
#|    "주의참고": "주의참고",
#|    "비권장": "비권장",
#|}
#|
#|GPVS_SCENARIO_FAMILY_MAP = {
#|    "F0": {
#|        "family": "정상 기준",
#|        "name": "정상 운전 시나리오",
#|        "description": "fault를 넣지 않은 기준 실험 상태",
#|    },
#|    "F1": {
#|        "family": "인버터/전력변환부 이상",
#|        "name": "인버터 전력소자 이상 시나리오",
#|        "description": "인버터 내부 IGBT 등 전력소자 고장으로 전력변환 경로 자체가 깨지는 상황",
#|    },
#|    "F2": {
#|        "family": "제어·계측 이상",
#|        "name": "제어 피드백 센서 이상 시나리오",
#|        "description": "전류/전압 피드백 센서 이상으로 제어기가 실제 상태를 잘못 읽어 MPPT 또는 인버터 제어가 어긋나는 상황",
#|    },
#|    "F3": {
#|        "family": "계통 이상",
#|        "name": "계통 전압 이상 시나리오",
#|        "description": "외부 계통 측 간헐적 전압 sag 등으로 운전 안정성이 흔들리는 상황",
#|    },
#|    "F4": {
#|        "family": "PV 어레이 이상",
#|        "name": "PV 어레이 mismatch(부분 음영) 시나리오",
#|        "description": "일부 패널이 부분 음영을 받아 어레이 내 전압·전류 균형이 깨지는 상황",
#|    },
#|    "F5": {
#|        "family": "PV 어레이 이상",
#|        "name": "PV 어레이 mismatch(부분 개방회로) 시나리오",
#|        "description": "PV 어레이 일부에 open-circuit 성격 이상이 생겨 어레이 균형이 깨지는 상황",
#|    },
#|    "F6": {
#|        "family": "제어기 이상",
#|        "name": "부스트 컨버터 PI gain 이상 시나리오",
#|        "description": "PI 제어기의 gain 설정 이상으로 제어 응답이 비정상화되는 상황",
#|    },
#|    "F7": {
#|        "family": "제어기 이상",
#|        "name": "부스트 컨버터 PI 시정수 이상 시나리오",
#|        "description": "PI 제어기의 time constant 이상으로 응답 속도와 안정화 과정이 비정상화되는 상황",
#|    },
#|}
#|
#|GPVS_SCENARIO_MODE_MAP = {
#|    "L": "제한출력 운전(IPPT)",
#|    "M": "최대전력점 추종 운전(MPPT)",
#|}
#|
#|EVENT_HISTORY_ORDER = [
#|    "전조형 고장",
#|    "급작 고장",
#|    "고장유형 보류",
#|    "공통원인 이벤트",
#|    "반복 이상",
#|]
#|
#|EVENT_PRIORITY = {
#|    "급작 고장": 1,
#|    "전조형 고장": 2,
#|    "고장유형 보류": 3,
#|    "공통원인 이벤트": 4,
#|    "반복 이상": 5,
#|}
#|
#|SPECIFIC_TO_BROAD_SYMPTOM = {
#|    "다이오드형": "전압 변화형",
#|    "개방/장치이상형": "전압 변화형",
#|    "모듈손상형": "출력 저하형",
#|    "출력저하형": "출력 저하형",
#|    "전압변화형": "전압 변화형",
#|    "복합형": "복합형",
#|    "불충분": "불충분",
#|}
#|
#|SCOPE_BY_EVENT_TYPE = {
#|    "전조형 고장": "step3_precursor_performance",
#|    "급작 고장": "step4_abrupt_no_precursor",
#|    "공통원인 이벤트": "step4_common_cause_routing",
#|}
#|
#|REQUIRED_FORENSIC_SUMMARY_COLS = [
#|    "site",
#|    "panel_id",
#|    "현재_재감사라벨_ko",
#|    "earliest_warning_date",
#|    "earliest_onset_date",
#|    "strong_trigger_date",
#|    "전조흔적_시작일",
#|    "강한트리거일",
#|    "사건유형_결정규칙_ko",
#|    "최종고장양상_결정규칙_ko",
#|    "사건유형_결정_ko",
#|    "최종고장양상_결정_ko",
#|    "사건시간양상_판정_ko",
#|    "현재표_보정필요여부_flag",
#|]
#|
#|FORENSIC_RULE_SITE = "conalog"
#|FORENSIC_RULE_PANEL_ID = "c42997a6-5881-47e7-9035-7de8a2673b54.1.1"
#|FORENSIC_RULE_ONSET_DATE = "2025-01-20"
#|FORENSIC_RULE_TRIGGER_DATE = "2025-03-21"
#|FORENSIC_RULE_EVENT_TYPE = "전조형 고장"
#|FORENSIC_RULE_TERMINAL_PATTERN = "급격 종료"
#|FORENSIC_RULE_REASON = "stored-field rule 기준 retrospective_onset_date<strict_trigger_date, onset_confidence=high, onset_method=persistent_5of7 이라 전조형 고장으로 읽고 최종고장양상은 급격 종료로 둔다"
#|
#|EXPECTED_FINAL_SCOPES = {
#|    "step3_precursor_performance",
#|    "step4_abrupt_no_precursor",
#|    "step4_common_cause_routing",
#|}
#|
#|
#|def parse_args() -> argparse.Namespace:
#|    parser = argparse.ArgumentParser(
#|        description="Build a panel-level representative multi-axis verdict table with separate event-history and cluster supplements."
#|    )
#|    parser.add_argument(
#|        "--root",
#|        type=Path,
#|        default=Path(__file__).resolve().parents[2],
#|        help="Repository root. Defaults to the project root.",
#|    )
#|    return parser.parse_args()
#|
#|
#|def normalize_text(value: object) -> str:
#|    if pd.isna(value):
#|        return ""
#|    text = str(value).strip()
#|    return "" if text.lower() == "nan" else text
#|
#|
#|def read_csv(path: Path) -> pd.DataFrame:
#|    if not path.exists():
#|        raise SystemExit(f"missing input: {path}")
#|    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
#|
#|
#|def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
#|    missing = [column for column in required if column not in df.columns]
#|    if missing:
#|        raise SystemExit(f"{name} missing columns: {missing}")
#|
#|
#|def normalize_frames(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
#|    normalized: dict[str, pd.DataFrame] = {}
#|    for key, value in frames.items():
#|        df = value.copy()
#|        for column in df.columns:
#|            if df[column].dtype == object:
#|                df[column] = df[column].map(normalize_text)
#|        normalized[key] = df
#|    return normalized
#|
#|
#|def first_existing_column(df: pd.DataFrame, candidates: list[str], frame_name: str) -> str:
#|    for candidate in candidates:
#|        if candidate in df.columns:
#|            return candidate
#|    raise SystemExit(f"{frame_name} missing any of columns: {candidates}")
#|
#|
#|def to_numeric_flag(series: pd.Series) -> pd.Series:
#|    return pd.to_numeric(series, errors="coerce").fillna(0)
#|
#|
#|def gpvs_scenario_fields(gpvs_detailed_code: object) -> dict[str, str]:
#|    code = normalize_text(gpvs_detailed_code)
#|    blank = {
#|        "GPVS_시나리오_family_ko": "",
#|        "GPVS_시나리오명_ko": "",
#|        "GPVS_시나리오_고장상황설명_ko": "",
#|        "GPVS_운전모드_ko": "",
#|        "GPVS_해석주의_ko": "",
#|    }
#|    if not code:
#|        return blank
#|
#|    prefix = code[:2] if len(code) >= 2 else ""
#|    suffix = code[-1] if len(code) >= 1 else ""
#|    scenario_meta = GPVS_SCENARIO_FAMILY_MAP.get(prefix)
#|    if scenario_meta is None:
#|        return {
#|            "GPVS_시나리오_family_ko": "",
#|            "GPVS_시나리오명_ko": f"외부 GPVS 시나리오 {code}",
#|            "GPVS_시나리오_고장상황설명_ko": "공식 GPVS 시나리오 map에 직접 등록되지 않은 코드",
#|            "GPVS_운전모드_ko": GPVS_SCENARIO_MODE_MAP.get(suffix, ""),
#|            "GPVS_해석주의_ko": GPVS_SCENARIO_WARNING,
#|        }
#|    return {
#|        "GPVS_시나리오_family_ko": scenario_meta["family"],
#|        "GPVS_시나리오명_ko": scenario_meta["name"],
#|        "GPVS_시나리오_고장상황설명_ko": scenario_meta["description"],
#|        "GPVS_운전모드_ko": GPVS_SCENARIO_MODE_MAP.get(suffix, ""),
#|        "GPVS_해석주의_ko": GPVS_SCENARIO_WARNING,
#|    }
#|
#|
#|def canonical_gpvs_code(gpvs_detailed_code: object) -> str:
#|    code = normalize_text(gpvs_detailed_code).upper()
#|    if len(code) < 2 or not code.startswith("F"):
#|        return ""
#|    canonical = code[:2]
#|    return canonical if canonical in GPVS_FRONT_PATTERN_NAME_MAP else ""
#|
#|
#|def gpvs_front_facing_fields(
#|    *,
#|    panel_fault_status: str,
#|    gpvs_type: str,
#|    gpvs_detailed_code: str,
#|    panel_agreement_row: dict[str, str] | None,
#|) -> dict[str, str]:
#|    blank = {
#|        "GPVS_내부참고유형_ko": "",
#|        "GPVS_외부참조패턴_ko": "",
#|        "GPVS_참조사용등급_ko": "",
#|        "GPVS_참조설명_ko": "",
#|    }
#|    if panel_fault_status != "고장":
#|        return blank
#|
#|    canonical_code = canonical_gpvs_code(gpvs_detailed_code)
#|    internal_type = normalize_text(gpvs_type)
#|    usefulness = ""
#|    if panel_agreement_row is not None:
#|        usefulness = GPVS_REFERENCE_GRADE_MAP.get(
#|            normalize_text(panel_agreement_row.get("overall_gpvs_reference_usefulness_ko", "")),
#|            "",
#|        )
#|
#|    return {
#|        "GPVS_내부참고유형_ko": "" if internal_type in {"", "미부착", "비대상"} else internal_type,
#|        "GPVS_외부참조패턴_ko": GPVS_FRONT_PATTERN_NAME_MAP.get(canonical_code, ""),
#|        "GPVS_참조사용등급_ko": usefulness,
#|        "GPVS_참조설명_ko": GPVS_FRONT_DESCRIPTION_MAP.get(canonical_code, ""),
#|    }
#|
#|
#|def load_inputs(root: Path) -> dict[str, pd.DataFrame]:
#|    share_dir = root / "_share"
#|    frames = {
#|        "workflow": read_csv(share_dir / WORKFLOW_DEFAULT_NAME),
#|        "abrupt6": read_csv(share_dir / ABRUPT6_SYMPTOM_MAP_NAME),
#|        "kernel_map": read_csv(share_dir / KERNELLOG_PROJECT_MAPPING_NAME),
#|        "gpv7": read_csv(share_dir / GPV7_PERF_SUMMARY_NAME),
#|        "final_pack": read_csv(share_dir / FINAL_DECISION_PACK_NAME),
#|        "precursor_truth": read_csv(share_dir / PRECURSOR_ONSET_TRUTH_NAME),
#|        "non_precursor_perf": read_csv(share_dir / NON_PRECURSOR_PERFORMANCE_CASES_NAME),
#|        "common_cause": read_csv(share_dir / COMMON_CAUSE_RETROFIT_NAME),
#|        "gpvs_attach_inventory": read_csv(share_dir / GPVS_ATTACH_INVENTORY_NAME),
#|        "gpvs_attach_feasibility": read_csv(share_dir / GPVS_ATTACH_FEASIBILITY_NAME),
#|        "gpvs_attach_candidates": read_csv(share_dir / GPVS_ATTACH_CANDIDATES_NAME),
#|        "consistency_cases": read_csv(share_dir / PRECURSOR_ABRUPT_CONSISTENCY_CASES_NAME),
#|        "consistency_summary": read_csv(share_dir / PRECURSOR_ABRUPT_CONSISTENCY_SUMMARY_NAME),
#|        "consistency_recommendation": read_csv(share_dir / PRECURSOR_ABRUPT_CONSISTENCY_RECOMMENDATION_NAME),
#|        "forensic_summary": read_csv(share_dir / FORENSIC_SUMMARY_NAME),
#|        "fault_event_audit": read_csv(share_dir / FAULT_PANEL_EVENT_AUDIT_NAME),
#|        "detailed_fault_bridge_audit": read_csv(share_dir / DETAILED_FAULT_BRIDGE_AUDIT_NAME),
#|        "detailed_fault_bridge_summary": read_csv(share_dir / DETAILED_FAULT_BRIDGE_SUMMARY_NAME),
#|        "gpvs_bytype_rebuild_summary": read_csv(share_dir / GPVS_BYTYPE_REBUILD_SUMMARY_NAME),
#|        "gpvs_detailed_type_audit": read_csv(share_dir / GPVS_DETAILED_TYPE_INFERENCE_AUDIT_NAME),
#|        "gpvs_detailed_type_realpanel_sanity": read_csv(share_dir / GPVS_DETAILED_TYPE_REALPANEL_SANITY_NAME),
#|        "gpvs_mlpe_panel_agreement": read_csv(share_dir / GPVS_MLPE_PANEL_AGREEMENT_NAME),
#|        "gpvs_canonical_dictionary": read_csv(share_dir / GPVS_CANONICAL_DICTIONARY_NAME),
#|        "gpvs_mlpe_fault_matching": read_csv(share_dir / GPVS_MLPE_FAULT_MATCHING_TABLE_NAME),
#|        "gpvs_mlpe_compatibility_summary": read_csv(share_dir / GPVS_MLPE_COMPATIBILITY_SUMMARY_NAME),
#|    }
#|
#|    ensure_columns(
#|        frames["workflow"],
#|        [
#|            "preview_attention_class",
#|            "site",
#|            "display_entity_id",
#|            "display_shape_or_cluster_kind",
#|            "display_status_or_tier",
#|            "display_score",
#|            "workflow_reason_ko",
#|        ],
#|        WORKFLOW_DEFAULT_NAME,
#|    )
#|    ensure_columns(
#|        frames["abrupt6"],
#|        [
#|            "site",
#|            "panel_id",
#|            "고장시점",
#|            "사건유형_ko",
#|            "최종고장양상_ko",
#|            "순수급작_flag",
#|            "증상명_ko",
#|            "세부근거_ko",
#|            "source_field_ko",
#|            "비고_ko",
#|        ],
#|        ABRUPT6_SYMPTOM_MAP_NAME,
#|    )
#|    ensure_columns(
#|        frames["kernel_map"],
#|        ["커널로그_증상명", "주_프로젝트분류", "보조_프로젝트분류", "설명_ko", "주의_ko"],
#|        KERNELLOG_PROJECT_MAPPING_NAME,
#|    )
#|    ensure_columns(
#|        frames["gpv7"],
#|        ["고장유형_번호", "고장유형_설명_ko", "성능요약_ko", "수치_ko", "source_ref_ko"],
#|        GPV7_PERF_SUMMARY_NAME,
#|    )
#|    ensure_columns(
#|        frames["final_pack"],
#|        ["eval_scope", "current_data_decision", "final_usage_decision", "final_reason_ko"],
#|        FINAL_DECISION_PACK_NAME,
#|    )
#|    ensure_columns(
#|        frames["precursor_truth"],
#|        [
#|            "site",
#|            "panel_id",
#|            "preferred_precursor_onset_date",
#|            "operational_first_precursor_detected_date",
#|            "operational_first_precursor_marker_name",
#|            "interpretive_precursor_onset_date",
#|            "benchmark_precursor_onset_date",
#|        ],
#|        PRECURSOR_ONSET_TRUTH_NAME,
#|    )
#|    ensure_columns(
#|        frames["non_precursor_perf"],
#|        ["eval_bucket_v2", "site", "panel_id"],
#|        NON_PRECURSOR_PERFORMANCE_CASES_NAME,
#|    )
#|    ensure_columns(
#|        frames["common_cause"],
#|        [
#|            "eval_bucket_v2",
#|            "site",
#|            "panel_id",
#|            "current_marker_only_flag",
#|            "breadth_marker_only_flag",
#|            "combined_marker_flag",
#|        ],
#|        COMMON_CAUSE_RETROFIT_NAME,
#|    )
#|    ensure_columns(
#|        frames["gpvs_attach_inventory"],
#|        [
#|            "경로",
#|            "존재여부",
#|            "granularity_ko",
#|            "panel_id_컬럼존재_flag",
#|            "site_컬럼존재_flag",
#|            "panel_attach_candidate_flag",
#|            "attachability_note_ko",
#|            "note_ko",
#|        ],
#|        GPVS_ATTACH_INVENTORY_NAME,
#|    )
#|    ensure_columns(
#|        frames["gpvs_attach_feasibility"],
#|        [
#|            "GPVS_패널별_직접판정_가능여부",
#|            "근거_ko",
#|            "최선_후보_파일",
#|            "overlap_panel_count",
#|            "overlap_rate",
#|            "다음권장조치_ko",
#|        ],
#|        GPVS_ATTACH_FEASIBILITY_NAME,
#|    )
#|    ensure_columns(
#|        frames["gpvs_attach_candidates"],
#|        ["site", "panel_id", "GPVS_참고유형_ko", "source_path", "source_key_ko", "비고_ko"],
#|        GPVS_ATTACH_CANDIDATES_NAME,
#|    )
#|    ensure_columns(
#|        frames["consistency_cases"],
#|        ["site", "panel_id", "same_event_flag", "distinct_event_flag", "consistency_judgment_ko"],
#|        PRECURSOR_ABRUPT_CONSISTENCY_CASES_NAME,
#|    )
#|    ensure_columns(
#|        frames["consistency_summary"],
#|        ["overlap_panel_count", "same_event_count", "corrected_pure_abrupt_fault_count"],
#|        PRECURSOR_ABRUPT_CONSISTENCY_SUMMARY_NAME,
#|    )
#|    ensure_columns(
#|        frames["consistency_recommendation"],
#|        ["recommended_next_handling", "rationale_ko"],
#|        PRECURSOR_ABRUPT_CONSISTENCY_RECOMMENDATION_NAME,
#|    )
#|    ensure_columns(frames["forensic_summary"], REQUIRED_FORENSIC_SUMMARY_COLS, FORENSIC_SUMMARY_NAME)
#|    ensure_columns(
#|        frames["fault_event_audit"],
#|        [
#|            "site",
#|            "panel_id",
#|            "현재표_사건유형_ko",
#|            "현재표_최종고장양상_ko",
#|            "전조흔적_flag",
#|            "순수급작_flag",
#|            "전조평가셋편입_flag",
#|            "급작평가셋편입_flag",
#|            "사건유형_재판정_ko",
#|            "최종고장양상_재판정_ko",
#|            "재판정_근거_ko",
#|            "현재표_보정필요여부_flag",
#|        ],
#|        FAULT_PANEL_EVENT_AUDIT_NAME,
#|    )
#|    ensure_columns(
#|        frames["detailed_fault_bridge_audit"],
#|        [
#|            "site",
#|            "panel_id",
#|            "reference_date",
#|            "exact_match_file_count",
#|            "matched_files_csv",
#|            "matched_fault_type_values_csv",
#|            "consensus_fault_type_code",
#|            "attachable_flag",
#|            "attach_reason_ko",
#|        ],
#|        DETAILED_FAULT_BRIDGE_AUDIT_NAME,
#|    )
#|    ensure_columns(
#|        frames["detailed_fault_bridge_summary"],
#|        [
#|            "고장패널수",
#|            "세부fault_부착수",
#|            "세부fault_보류수",
#|            "exact_date_match_패널수",
#|            "exact_date_conflict_패널수",
#|            "exact_date_miss_패널수",
#|            "note_ko",
#|        ],
#|        DETAILED_FAULT_BRIDGE_SUMMARY_NAME,
#|    )
#|    ensure_columns(
#|        frames["gpvs_bytype_rebuild_summary"],
#|        [
#|            "recovered_model_exported_flag",
#|            "recovered_feature_manifest_exported_flag",
#|            "recovered_model_source_ko",
#|            "parity_overall_status_ko",
#|            "current_recovered_attachable_flag",
#|            "note_ko",
#|        ],
#|        GPVS_BYTYPE_REBUILD_SUMMARY_NAME,
#|    )
#|    ensure_columns(
#|        frames["gpvs_detailed_type_audit"],
#|        [
#|            "site",
#|            "panel_id",
#|            "event_reference_date",
#|            "gpvs_detailed_model_source",
#|            "gpvs_family_label",
#|            "gpvs_detailed_top1_fault_type",
#|            "gpvs_detailed_top1_score",
#|            "gpvs_detailed_top2_fault_type",
#|            "gpvs_detailed_top2_score",
#|            "gpvs_detailed_margin",
#|            "gpvs_detailed_status_ko",
#|            "gpvs_detailed_reason_ko",
#|        ],
#|        GPVS_DETAILED_TYPE_INFERENCE_AUDIT_NAME,
#|    )
#|    ensure_columns(
#|        frames["gpvs_detailed_type_realpanel_sanity"],
#|        [
#|            "site",
#|            "panel_id",
#|            "gpvs_family_label",
#|            "gpvs_detailed_top1_fault_type",
#|            "single_type_collapse_flag",
#|            "attach_recommendation_ko",
#|        ],
#|        GPVS_DETAILED_TYPE_REALPANEL_SANITY_NAME,
#|    )
#|    ensure_columns(
#|        frames["gpvs_mlpe_panel_agreement"],
#|        [
#|            "site",
#|            "panel_id",
#|            "overall_gpvs_reference_usefulness_ko",
#|            "overall_gpvs_trust_note_ko",
#|        ],
#|        GPVS_MLPE_PANEL_AGREEMENT_NAME,
#|    )
#|    ensure_columns(
#|        frames["gpvs_canonical_dictionary"],
#|        [
#|            "canonical_gpvs_code",
#|            "current_usage_tier_ko",
#|            "mlpe_reference_name_ko",
#|            "usage_rule_ko",
#|            "note_ko",
#|        ],
#|        GPVS_CANONICAL_DICTIONARY_NAME,
#|    )
#|    ensure_columns(
#|        frames["gpvs_mlpe_fault_matching"],
#|        [
#|            "mlpe_official_fault_ko",
#|            "canonical_gpvs_code",
#|            "match_strength_ko",
#|            "match_role_ko",
#|            "recommendation_ko",
#|        ],
#|        GPVS_MLPE_FAULT_MATCHING_TABLE_NAME,
#|    )
#|    ensure_columns(
#|        frames["gpvs_mlpe_compatibility_summary"],
#|        [
#|            "fault_panel_count",
#|            "final_recommendation_ko",
#|            "note_ko",
#|        ],
#|        GPVS_MLPE_COMPATIBILITY_SUMMARY_NAME,
#|    )
#|    return normalize_frames(frames)
#|
#|
#|def validate_inputs(root: Path, frames: dict[str, pd.DataFrame]) -> None:
#|    workflow_df = frames["workflow"]
#|    kernel_map_df = frames["kernel_map"]
#|    final_pack_df = frames["final_pack"]
#|
#|    preview_values = set(workflow_df["preview_attention_class"].tolist())
#|    if not PANEL_LEVEL_PREVIEW_CLASSES.issubset(preview_values):
#|        missing = sorted(PANEL_LEVEL_PREVIEW_CLASSES - preview_values)
#|        raise SystemExit(f"{WORKFLOW_DEFAULT_NAME} missing queue/watch rows: {missing}")
#|
#|    required_kernel_symptoms = {"출력 저하형", "전압 변화형", "패턴 이상형", "불안정형", "복합형"}
#|    missing_symptoms = required_kernel_symptoms - set(kernel_map_df["커널로그_증상명"].tolist())
#|    if missing_symptoms:
#|        raise SystemExit(f"{KERNELLOG_PROJECT_MAPPING_NAME} missing required symptom rows: {sorted(missing_symptoms)}")
#|
#|    final_scopes = set(final_pack_df["eval_scope"].tolist())
#|    missing_scopes = EXPECTED_FINAL_SCOPES - final_scopes
#|    if missing_scopes:
#|        raise SystemExit(f"{FINAL_DECISION_PACK_NAME} missing required scopes: {sorted(missing_scopes)}")
#|
#|    feasibility_df = frames["gpvs_attach_feasibility"]
#|    if len(feasibility_df) != 1:
#|        raise SystemExit(f"{GPVS_ATTACH_FEASIBILITY_NAME} must contain exactly one row, found {len(feasibility_df)}")
#|    feasibility_value = normalize_text(feasibility_df.iloc[0]["GPVS_패널별_직접판정_가능여부"])
#|    if feasibility_value not in {"가능", "불가"}:
#|        raise SystemExit(
#|            f"{GPVS_ATTACH_FEASIBILITY_NAME} has invalid GPVS_패널별_직접판정_가능여부: {feasibility_value}"
#|        )
#|    overlap_value = pd.to_numeric(feasibility_df.iloc[0]["overlap_panel_count"], errors="coerce")
#|    if pd.isna(overlap_value):
#|        raise SystemExit(f"{GPVS_ATTACH_FEASIBILITY_NAME} overlap_panel_count must be numeric")
#|    candidates_df = frames["gpvs_attach_candidates"]
#|    if feasibility_value == "가능" and candidates_df.empty:
#|        raise SystemExit(f"{GPVS_ATTACH_CANDIDATES_NAME} is empty despite feasibility=가능")
#|    if feasibility_value == "불가" and not candidates_df.empty:
#|        raise SystemExit(f"{GPVS_ATTACH_CANDIDATES_NAME} must be empty when feasibility=불가")
#|    if not candidates_df.empty and candidates_df.duplicated(subset=["site", "panel_id"]).any():
#|        dup = candidates_df.loc[candidates_df.duplicated(subset=["site", "panel_id"], keep=False), ["site", "panel_id"]]
#|        raise SystemExit(f"{GPVS_ATTACH_CANDIDATES_NAME} must be unique by (site, panel_id): {dup.to_dict(orient='records')[:5]}")
#|    if frames["gpvs_attach_inventory"].empty:
#|        raise SystemExit(f"{GPVS_ATTACH_INVENTORY_NAME} must not be empty")
#|    if len(frames["detailed_fault_bridge_summary"]) != 1:
#|        raise SystemExit(
#|            f"{DETAILED_FAULT_BRIDGE_SUMMARY_NAME} must contain exactly one row, found {len(frames['detailed_fault_bridge_summary'])}"
#|        )
#|    if len(frames["gpvs_bytype_rebuild_summary"]) != 1:
#|        raise SystemExit(
#|            f"{GPVS_BYTYPE_REBUILD_SUMMARY_NAME} must contain exactly one row, found {len(frames['gpvs_bytype_rebuild_summary'])}"
#|        )
#|    if len(frames["gpvs_mlpe_compatibility_summary"]) != 1:
#|        raise SystemExit(
#|            f"{GPVS_MLPE_COMPATIBILITY_SUMMARY_NAME} must contain exactly one row, found {len(frames['gpvs_mlpe_compatibility_summary'])}"
#|        )
#|    compatibility_recommendation = normalize_text(
#|        frames["gpvs_mlpe_compatibility_summary"].iloc[0]["final_recommendation_ko"]
#|    )
#|    if compatibility_recommendation != "참고축으로만 사용":
#|        raise SystemExit(
#|            f"{GPVS_MLPE_COMPATIBILITY_SUMMARY_NAME} final_recommendation_ko must be 참고축으로만 사용, got {compatibility_recommendation or '<blank>'}"
#|        )
#|    canonical_codes = {
#|        normalize_text(value)
#|        for value in frames["gpvs_canonical_dictionary"]["canonical_gpvs_code"].tolist()
#|        if normalize_text(value)
#|    }
#|    missing_canonical_codes = sorted(set(GPVS_FRONT_PATTERN_NAME_MAP) - canonical_codes)
#|    if missing_canonical_codes:
#|        raise SystemExit(
#|            f"{GPVS_CANONICAL_DICTIONARY_NAME} missing canonical codes required by front-facing GPVS map: {missing_canonical_codes}"
#|        )
#|
#|
#|def load_same_event_overlap_keys(frames: dict[str, pd.DataFrame]) -> set[tuple[str, str]]:
#|    recommendation_df = frames["consistency_recommendation"]
#|    if len(recommendation_df) != 1:
#|        raise SystemExit(
#|            f"{PRECURSOR_ABRUPT_CONSISTENCY_RECOMMENDATION_NAME} must contain exactly one row, found {len(recommendation_df)}"
#|        )
#|    recommendation = normalize_text(recommendation_df.iloc[0]["recommended_next_handling"])
#|    if recommendation != "relabel_overlap_as_precursor_led_faults":
#|        raise SystemExit(
#|            "precursor/abrupt consistency recommendation must be relabel_overlap_as_precursor_led_faults for panel verdict reconciliation; "
#|            f"got {recommendation or '<blank>'}"
#|        )
#|
#|    cases_df = frames["consistency_cases"]
#|    same_event_df = cases_df.loc[pd.to_numeric(cases_df["same_event_flag"], errors="coerce").fillna(0).eq(1)].copy()
#|    overlap_keys = {
#|        (normalize_text(row["site"]), normalize_text(row["panel_id"]))
#|        for row in same_event_df.to_dict(orient="records")
#|        if normalize_text(row["site"]) and normalize_text(row["panel_id"])
#|    }
#|    summary_row = frames["consistency_summary"].iloc[0].to_dict()
#|    expected_overlap = int(pd.to_numeric(summary_row["overlap_panel_count"], errors="raise"))
#|    expected_same = int(pd.to_numeric(summary_row["same_event_count"], errors="raise"))
#|    corrected_pure_abrupt = int(pd.to_numeric(summary_row["corrected_pure_abrupt_fault_count"], errors="raise"))
#|    if expected_overlap != expected_same:
#|        raise SystemExit(
#|            f"{PRECURSOR_ABRUPT_CONSISTENCY_SUMMARY_NAME} must keep overlap_panel_count == same_event_count for this reconciliation"
#|        )
#|    if len(overlap_keys) != expected_same:
#|        raise SystemExit(
#|            f"same-event overlap count mismatch between cases and summary: cases={len(overlap_keys)}, summary={expected_same}"
#|        )
#|    if len(overlap_keys) != 2:
#|        raise SystemExit(f"expected current same-event overlap panel count to be 2, found {len(overlap_keys)}")
#|    if corrected_pure_abrupt != 4:
#|        raise SystemExit(f"expected corrected pure abrupt fault count to be 4, found {corrected_pure_abrupt}")
#|    return overlap_keys
#|
#|
#|def load_forensic_rule_case(frames: dict[str, pd.DataFrame]) -> dict[str, str]:
#|    forensic_df = frames["forensic_summary"].copy()
#|    target_df = forensic_df.loc[
#|        forensic_df["site"].eq(FORENSIC_RULE_SITE)
#|        & forensic_df["panel_id"].eq(FORENSIC_RULE_PANEL_ID)
#|    ].copy()
#|    if len(target_df) != 1:
#|        raise SystemExit(
#|            f"{FORENSIC_SUMMARY_NAME} must contain exactly one target row for {FORENSIC_RULE_SITE}/{FORENSIC_RULE_PANEL_ID}, found {len(target_df)}"
#|        )
#|    row = {key: normalize_text(value) for key, value in target_df.iloc[0].to_dict().items()}
#|    onset_date = normalize_text(row.get("earliest_onset_date")) or normalize_text(row.get("전조흔적_시작일"))
#|    trigger_date = normalize_text(row.get("strong_trigger_date")) or normalize_text(row.get("강한트리거일"))
#|    if onset_date != FORENSIC_RULE_ONSET_DATE or trigger_date != FORENSIC_RULE_TRIGGER_DATE:
#|        raise SystemExit(
#|            f"{FORENSIC_SUMMARY_NAME} guard failed: expected onset/trigger {FORENSIC_RULE_ONSET_DATE}/{FORENSIC_RULE_TRIGGER_DATE}, got {onset_date}/{trigger_date}"
#|        )
#|    row["__forensic_onset_date"] = onset_date
#|    row["__forensic_trigger_date"] = trigger_date
#|    return row
#|
#|
#|def fault_event_audit_lookup(frames: dict[str, pd.DataFrame]) -> dict[tuple[str, str], dict[str, str]]:
#|    audit_df = frames["fault_event_audit"].copy()
#|    if audit_df.empty:
#|        raise SystemExit(f"{FAULT_PANEL_EVENT_AUDIT_NAME} must not be empty")
#|    if audit_df[["site", "panel_id"]].duplicated().any():
#|        dup = audit_df.loc[audit_df[["site", "panel_id"]].duplicated(keep=False), ["site", "panel_id"]]
#|        raise SystemExit(f"{FAULT_PANEL_EVENT_AUDIT_NAME} must be unique by (site, panel_id): {dup.to_dict(orient='records')[:5]}")
#|
#|    lookup: dict[tuple[str, str], dict[str, str]] = {}
#|    for row in audit_df.to_dict(orient="records"):
#|        site = normalize_text(row["site"])
#|        panel_id = normalize_text(row["panel_id"])
#|        if site and panel_id:
#|            lookup[(site, panel_id)] = {key: normalize_text(value) for key, value in row.items()}
#|    if len(lookup) != 6:
#|        raise SystemExit(f"{FAULT_PANEL_EVENT_AUDIT_NAME} must contain current fault panel 6 rows, found {len(lookup)}")
#|    if (FORENSIC_RULE_SITE, FORENSIC_RULE_PANEL_ID) not in lookup:
#|        raise SystemExit(f"{FAULT_PANEL_EVENT_AUDIT_NAME} must contain forensic target panel row")
#|    return lookup
#|
#|
#|def abrupt_lookup(abrupt_df: pd.DataFrame) -> dict[tuple[str, str], dict[str, object]]:
#|    return {
#|        (normalize_text(row["site"]), normalize_text(row["panel_id"])): row
#|        for row in abrupt_df.to_dict(orient="records")
#|    }
#|
#|
#|def final_pack_lookup(final_pack_df: pd.DataFrame) -> dict[str, dict[str, object]]:
#|    return {
#|        normalize_text(row["eval_scope"]): row
#|        for row in final_pack_df.to_dict(orient="records")
#|    }
#|
#|
#|def build_workflow_panel_df(workflow_df: pd.DataFrame) -> pd.DataFrame:
#|    panel_df = workflow_df.loc[workflow_df["preview_attention_class"].isin(PANEL_LEVEL_PREVIEW_CLASSES)].copy()
#|    panel_df = panel_df.sort_values(["site", "display_entity_id", "display_score"], ascending=[True, True, False])
#|    return panel_df.drop_duplicates(subset=["site", "display_entity_id"], keep="first")
#|
#|
#|def build_cluster_df(workflow_df: pd.DataFrame) -> pd.DataFrame:
#|    cluster_df = workflow_df.loc[workflow_df["preview_attention_class"].eq(CLUSTER_PREVIEW_CLASS)].copy()
#|    if cluster_df.empty:
#|        return cluster_df
#|    cluster_df = cluster_df.sort_values(["site", "display_entity_id", "display_score"], ascending=[True, True, False])
#|    return cluster_df.drop_duplicates(subset=["site", "display_entity_id"], keep="first")
#|
#|
#|def panel_key_set(df: pd.DataFrame, site_col: str, panel_col: str) -> set[tuple[str, str]]:
#|    keys: set[tuple[str, str]] = set()
#|    for row in df.to_dict(orient="records"):
#|        site = normalize_text(row[site_col])
#|        panel_id = normalize_text(row[panel_col])
#|        if site and panel_id:
#|            keys.add((site, panel_id))
#|    return keys
#|
#|
#|def build_precursor_positive_keys(precursor_df: pd.DataFrame) -> set[tuple[str, str]]:
#|    panel_col = first_existing_column(
#|        precursor_df,
#|        ["panel_id", "display_entity_id", "entity_id", "panel_entity_id"],
#|        PRECURSOR_ONSET_TRUTH_NAME,
#|    )
#|    positive_df = precursor_df.loc[precursor_df["preferred_precursor_onset_date"].ne("")].copy()
#|    keys = panel_key_set(positive_df, "site", panel_col)
#|    if not keys:
#|        raise SystemExit(f"{PRECURSOR_ONSET_TRUTH_NAME} has no precursor-positive rows with preferred_precursor_onset_date")
#|    return keys
#|
#|
#|def precursor_truth_lookup(precursor_df: pd.DataFrame) -> dict[tuple[str, str], dict[str, str]]:
#|    panel_col = first_existing_column(
#|        precursor_df,
#|        ["panel_id", "display_entity_id", "entity_id", "panel_entity_id"],
#|        PRECURSOR_ONSET_TRUTH_NAME,
#|    )
#|    positive_df = precursor_df.loc[precursor_df["preferred_precursor_onset_date"].ne("")].copy()
#|    if positive_df[["site", panel_col]].duplicated().any():
#|        dup = positive_df.loc[positive_df[["site", panel_col]].duplicated(keep=False), ["site", panel_col]]
#|        raise SystemExit(f"{PRECURSOR_ONSET_TRUTH_NAME} must be unique by (site, panel_id): {dup.to_dict(orient='records')[:5]}")
#|    lookup: dict[tuple[str, str], dict[str, str]] = {}
#|    for row in positive_df.to_dict(orient="records"):
#|        key = (normalize_text(row["site"]), normalize_text(row[panel_col]))
#|        lookup[key] = {column: normalize_text(value) for column, value in row.items()}
#|    return lookup
#|
#|
#|def build_abrupt_eval_keys(non_precursor_df: pd.DataFrame) -> set[tuple[str, str]]:
#|    positive_df = non_precursor_df.loc[
#|        non_precursor_df["eval_bucket_v2"].eq("abrupt_or_no_precursor_now")
#|    ].copy()
#|    keys = panel_key_set(positive_df, "site", "panel_id")
#|    if not keys:
#|        raise SystemExit(
#|            f"{NON_PRECURSOR_PERFORMANCE_CASES_NAME} has no abrupt_or_no_precursor_now rows"
#|        )
#|    return keys
#|
#|
#|def build_common_cause_positive_keys(common_df: pd.DataFrame) -> set[tuple[str, str]]:
#|    marker_mask = (
#|        to_numeric_flag(common_df["current_marker_only_flag"]).eq(1)
#|        | to_numeric_flag(common_df["breadth_marker_only_flag"]).eq(1)
#|        | to_numeric_flag(common_df["combined_marker_flag"]).eq(1)
#|    )
#|    positive_df = common_df.loc[common_df["eval_bucket_v2"].eq("non_panel_or_common_cause") & marker_mask].copy()
#|    keys = panel_key_set(positive_df, "site", "panel_id")
#|    if not keys:
#|        raise SystemExit(
#|            f"{COMMON_CAUSE_RETROFIT_NAME} has no non_panel_or_common_cause positive rows with current/breadth/combined marker evidence"
#|        )
#|    return keys
#|
#|
#|def workflow_lookup(workflow_panel_df: pd.DataFrame) -> dict[tuple[str, str], dict[str, object]]:
#|    return {
#|        (normalize_text(row["site"]), normalize_text(row["display_entity_id"])): row
#|        for row in workflow_panel_df.to_dict(orient="records")
#|    }
#|
#|
#|def current_data_scope_note(
#|    event_type: str,
#|    terminal_pattern: str,
#|    final_pack_by_scope: dict[str, dict[str, object]],
#|) -> str:
#|    if event_type == "전조형 고장" and terminal_pattern == "급격 종료":
#|        return "이 panel은 전조형 사건 한 건이 마지막에 급격 종료로 끝난 것으로 읽는다. event type과 terminal failure pattern은 분리해서 해석해야 한다."
#|    scope = SCOPE_BY_EVENT_TYPE.get(event_type, "")
#|    if scope:
#|        final_row = final_pack_by_scope.get(scope, {})
#|        final_usage = normalize_text(final_row.get("final_usage_decision", ""))
#|        if final_usage == "bounded_reporting_use":
#|            return f"{event_type} 축은 current closeout 기준 bounded current-data 수준으로만 읽는다."
#|        if final_usage == "exploratory_only":
#|            return f"{event_type} 축은 current closeout 기준 exploratory 범위로만 읽는다."
#|    if event_type == "반복 이상":
#|        return "반복 이상은 chronic monitor/반복 lane 해석이며 stable fault classifier claim이 아니다."
#|    if event_type == "불충분":
#|        return "현재 stored positive universe와 직접 연결되지 않아 사건 성격을 보수적으로 유지한다."
#|    return "현재 저장 산출물만으로는 사건 성격 판정 근거가 제한적이다."
#|
#|
#|def event_type_and_terminal_pattern(
#|    flags: dict[str, int],
#|    *,
#|    is_same_event_overlap: bool,
#|    forensic_rule_case: dict[str, str] | None,
#|    fault_audit_row: dict[str, str] | None,
#|) -> tuple[str, str]:
#|    if fault_audit_row is not None:
#|        return (
#|            normalize_text(fault_audit_row["사건유형_재판정_ko"]) or "불충분",
#|            normalize_text(fault_audit_row["최종고장양상_재판정_ko"]) or "불충분",
#|        )
#|    if forensic_rule_case is not None:
#|        return (
#|            normalize_text(forensic_rule_case["사건유형_결정_ko"]) or "불충분",
#|            normalize_text(forensic_rule_case["최종고장양상_결정_ko"]) or "불충분",
#|        )
#|    if is_same_event_overlap:
#|        return ("전조형 고장", "급격 종료")
#|    if flags["has_급작고장"]:
#|        return ("급작 고장", "급작 발생")
#|    if flags["has_전조형고장"]:
#|        return ("전조형 고장", "진행성 악화")
#|    if flags["has_공통원인이벤트"]:
#|        return ("공통원인 이벤트", "해당없음")
#|    if flags["has_반복이상"]:
#|        return ("반복 이상", "해당없음")
#|    return ("불충분", "불충분")
#|
#|
#|def panel_fault_status_from_event_type(event_type: str) -> str:
#|    if event_type in {"전조형 고장", "급작 고장", "고장유형 보류"}:
#|        return "고장"
#|    if event_type == "공통원인 이벤트":
#|        return "비고장"
#|    return "미확정"
#|
#|
#|def gpvs_applicability_from_fault_status(panel_fault_status: str) -> str:
#|    return "적용대상" if panel_fault_status == "고장" else "비대상"
#|
#|
#|def event_history_text(
#|    flags: dict[str, int],
#|    *,
#|    is_same_event_overlap: bool,
#|    forensic_rule_case: dict[str, str] | None,
#|    fault_audit_row: dict[str, str] | None,
#|) -> str:
#|    if fault_audit_row is not None:
#|        event_type = normalize_text(fault_audit_row["사건유형_재판정_ko"])
#|        terminal_pattern = normalize_text(fault_audit_row["최종고장양상_재판정_ko"])
#|        if event_type == "급작 고장" and terminal_pattern == "급작 발생":
#|            return event_type
#|        if event_type == "전조형 고장" and terminal_pattern == "진행성 악화":
#|            return event_type
#|        if event_type and terminal_pattern and terminal_pattern not in {"불충분", "해당없음"}:
#|            return f"{event_type}({terminal_pattern})"
#|        return event_type
#|    if forensic_rule_case is not None:
#|        event_type = normalize_text(forensic_rule_case["사건유형_결정_ko"])
#|        terminal_pattern = normalize_text(forensic_rule_case["최종고장양상_결정_ko"])
#|        if event_type and terminal_pattern and terminal_pattern != "불충분":
#|            return f"{event_type}({terminal_pattern})"
#|        return event_type
#|    members: list[str] = []
#|    if flags["has_전조형고장"]:
#|        if is_same_event_overlap:
#|            members.append("전조형 고장(급격 종료)")
#|        else:
#|            members.append("전조형 고장")
#|    if flags["has_급작고장"]:
#|        members.append("급작 고장")
#|    if flags["has_공통원인이벤트"]:
#|        members.append("공통원인 이벤트")
#|    if flags["has_반복이상"]:
#|        members.append("반복 이상")
#|    return "+".join(members)
#|
#|
#|def interpretation_layer_fields(
#|    flags: dict[str, int],
#|    event_type: str,
#|    *,
#|    precursor_eval_flag: int,
#|    abrupt_eval_flag: int,
#|    is_same_event_overlap: bool,
#|    forensic_rule_case: dict[str, str] | None,
#|    fault_audit_row: dict[str, str] | None,
#|) -> dict[str, object]:
#|    def mismatch_text_for(event_type_ko: str, precursor_flag: int, abrupt_flag: int) -> str:
#|        if event_type_ko == "전조형 고장" and precursor_flag == 0:
#|            return "explicit rule상 전조형 고장이지만 현재 strict precursor evaluation set에는 아직 미편입"
#|        if event_type_ko == "급작 고장" and abrupt_flag == 0:
#|            return "explicit rule상 급작 고장이지만 현재 pure abrupt evaluation set에는 아직 미편입"
#|        return ""
#|
#|    if fault_audit_row is not None:
#|        event_type_ko = normalize_text(fault_audit_row["사건유형_재판정_ko"]) or event_type
#|        return {
#|            "사건유형_해석_ko": event_type_ko,
#|            "전조흔적_flag": int(pd.to_numeric(pd.Series([fault_audit_row["전조흔적_flag"]]), errors="coerce").fillna(0).iloc[0]),
#|            "순수급작_flag": int(pd.to_numeric(pd.Series([fault_audit_row["순수급작_flag"]]), errors="coerce").fillna(0).iloc[0]),
#|            "전조평가셋편입_flag": precursor_eval_flag,
#|            "급작평가셋편입_flag": abrupt_eval_flag,
#|            "해석대평가차이_ko": mismatch_text_for(event_type_ko, precursor_eval_flag, abrupt_eval_flag),
#|        }
#|    if is_same_event_overlap:
#|        return {
#|            "사건유형_해석_ko": "전조형 고장",
#|            "전조흔적_flag": 1,
#|            "순수급작_flag": 0,
#|            "전조평가셋편입_flag": precursor_eval_flag,
#|            "급작평가셋편입_flag": abrupt_eval_flag,
#|            "해석대평가차이_ko": mismatch_text_for("전조형 고장", precursor_eval_flag, abrupt_eval_flag),
#|        }
#|    if forensic_rule_case is not None:
#|        event_type_ko = normalize_text(forensic_rule_case["사건유형_결정_ko"]) or event_type
#|        return {
#|            "사건유형_해석_ko": event_type_ko,
#|            "전조흔적_flag": 1,
#|            "순수급작_flag": 0,
#|            "전조평가셋편입_flag": precursor_eval_flag,
#|            "급작평가셋편입_flag": abrupt_eval_flag,
#|            "해석대평가차이_ko": mismatch_text_for(event_type_ko, precursor_eval_flag, abrupt_eval_flag),
#|        }
#|    if flags["has_급작고장"]:
#|        return {
#|            "사건유형_해석_ko": "급작 고장",
#|            "전조흔적_flag": 0,
#|            "순수급작_flag": 1,
#|            "전조평가셋편입_flag": precursor_eval_flag,
#|            "급작평가셋편입_flag": abrupt_eval_flag,
#|            "해석대평가차이_ko": mismatch_text_for("급작 고장", precursor_eval_flag, abrupt_eval_flag),
#|        }
#|    if flags["has_전조형고장"]:
#|        return {
#|            "사건유형_해석_ko": "전조형 고장",
#|            "전조흔적_flag": 1,
#|            "순수급작_flag": 0,
#|            "전조평가셋편입_flag": precursor_eval_flag,
#|            "급작평가셋편입_flag": abrupt_eval_flag,
#|            "해석대평가차이_ko": mismatch_text_for("전조형 고장", precursor_eval_flag, abrupt_eval_flag),
#|        }
#|    return {
#|        "사건유형_해석_ko": event_type,
#|        "전조흔적_flag": 0,
#|        "순수급작_flag": 0,
#|        "전조평가셋편입_flag": precursor_eval_flag,
#|        "급작평가셋편입_flag": abrupt_eval_flag,
#|        "해석대평가차이_ko": mismatch_text_for(event_type, precursor_eval_flag, abrupt_eval_flag),
#|    }
#|
#|
#|def map_kernel_axis(
#|    event_type: str,
#|    abrupt_row: dict[str, object] | None,
#|) -> tuple[str, str, str]:
#|    if abrupt_row is not None:
#|        specific = normalize_text(abrupt_row["증상명_ko"]) or "불충분"
#|        broad = SPECIFIC_TO_BROAD_SYMPTOM.get(specific, "불충분")
#|        note = (
#|            f"커널로그 원인군은 abrupt6 symptom map의 `{specific}` 를 연결했다."
#|            if specific != "불충분"
#|            else "abrupt6 direct map가 있지만 stored symptom name이 불충분하다."
#|        )
#|        return broad, specific, note
#|
#|    if event_type == "전조형 고장":
#|        return "출력 저하형", "불충분", "전조형 representative verdict라 nearest symptom 축으로 출력 저하형만 부착했다."
#|    if event_type == "공통원인 이벤트":
#|        return "패턴 이상형", "불충분", "공통원인 representative verdict라 nearest symptom 축으로 패턴 이상형만 부착했다."
#|    if event_type == "반복 이상":
#|        return "불안정형", "불충분", "watch_now_panel 반복 lane이라 nearest symptom 축으로 불안정형만 부착했다."
#|    return "불충분", "불충분", "현재 stored field로 커널로그 증상축을 더 붙이기 어렵다."
#|
#|
#|def map_operating_location(workflow_row: dict[str, object] | None) -> str:
#|    if workflow_row is None:
#|        return "현재 workflow 미포함"
#|    preview_class = normalize_text(workflow_row["preview_attention_class"])
#|    if preview_class == "queue_run":
#|        return "바로 확인"
#|    if preview_class == "watch_now_panel":
#|        return "경과 관찰"
#|    return "현재 workflow 미포함"
#|
#|
#|def recover_gpvs_panel_level_reference_from_audit(
#|    feasibility_df: pd.DataFrame,
#|    candidates_df: pd.DataFrame,
#|    panel_keys: set[tuple[str, str]],
#|) -> tuple[dict[tuple[str, str], dict[str, str]], dict[str, str], int]:
#|    feasibility_row = feasibility_df.iloc[0]
#|    feasibility_value = normalize_text(feasibility_row["GPVS_패널별_직접판정_가능여부"])
#|    overlap_expected = int(pd.to_numeric(feasibility_row["overlap_panel_count"], errors="raise"))
#|    best_source = normalize_text(feasibility_row["최선_후보_파일"])
#|    feasibility_reason = normalize_text(feasibility_row["근거_ko"])
#|
#|    if feasibility_value == "불가":
#|        return (
#|            {},
#|            {
#|                "feasibility": feasibility_value,
#|                "best_source": best_source,
#|                "feasibility_reason": feasibility_reason,
#|            },
#|            0,
#|        )
#|
#|    gpvs_lookup: dict[tuple[str, str], dict[str, str]] = {}
#|    for row in candidates_df.to_dict(orient="records"):
#|        key = (normalize_text(row["site"]), normalize_text(row["panel_id"]))
#|        if key not in panel_keys:
#|            continue
#|        source_path = normalize_text(row["source_path"])
#|        source_key = normalize_text(row["source_key_ko"])
#|        note = normalize_text(row["비고_ko"])
#|        reason_parts = [part for part in [source_path, source_key, note] if part]
#|        gpvs_lookup[key] = {
#|            "GPVS_참고유형_ko": normalize_text(row["GPVS_참고유형_ko"]) or "미부착",
#|            "GPVS_근거_ko": " | ".join(reason_parts) if reason_parts else GPVS_ABSENCE_REASON,
#|            "GPVS_후보파일_ko": source_path,
#|        }
#|
#|    return (
#|        gpvs_lookup,
#|        {
#|            "feasibility": feasibility_value,
#|            "best_source": best_source,
#|            "feasibility_reason": feasibility_reason,
#|        },
#|        overlap_expected,
#|    )
#|
#|
#|def gpvs_unattached_reason(
#|    inventory_df: pd.DataFrame,
#|    feasibility_meta: dict[str, str],
#|) -> str:
#|    feasibility_value = normalize_text(feasibility_meta.get("feasibility", ""))
#|    best_source = normalize_text(feasibility_meta.get("best_source", ""))
#|    inventory = inventory_df.copy()
#|    inventory["panel_attach_candidate_flag"] = to_numeric_flag(inventory["panel_attach_candidate_flag"])
#|
#|    if feasibility_value == "가능" and (
#|        best_source
#|        or inventory["panel_attach_candidate_flag"].eq(1).any()
#|    ):
#|        return "GPVS 패널수준 후보 파일은 있으나 이 패널 key가 없음"
#|
#|    key_poor_mask = inventory["panel_attach_candidate_flag"].eq(0) & inventory["granularity_ko"].isin(["유형수준", "집계수준"])
#|    if key_poor_mask.any():
#|        return "GPVS 결과는 있으나 패널수준 key가 없음"
#|
#|    return "패널수준 GPVS 산출물 없음"
#|
#|
#|def detailed_fault_type_label(code: str) -> str:
#|    normalized = normalize_text(code)
#|    if len(normalized) >= 2 and normalized[0] == "F" and normalized[1].isdigit():
#|        family_idx = normalized[1]
#|        if family_idx in {"1", "2", "3", "4", "5", "6", "7"}:
#|            return f"GPVS Fault{family_idx}"
#|    return normalized
#|
#|
#|def detailed_fault_bridge_lookup(
#|    audit_df: pd.DataFrame,
#|    summary_df: pd.DataFrame,
#|) -> tuple[dict[tuple[str, str], dict[str, str]], dict[str, int | str]]:
#|    if audit_df[["site", "panel_id"]].duplicated().any():
#|        dup = audit_df.loc[audit_df[["site", "panel_id"]].duplicated(keep=False), ["site", "panel_id"]]
#|        raise SystemExit(
#|            f"{DETAILED_FAULT_BRIDGE_AUDIT_NAME} must be unique by (site, panel_id): {dup.to_dict(orient='records')[:5]}"
#|        )
#|    lookup: dict[tuple[str, str], dict[str, str]] = {}
#|    for row in audit_df.to_dict(orient="records"):
#|        key = (normalize_text(row["site"]), normalize_text(row["panel_id"]))
#|        lookup[key] = {column: normalize_text(value) for column, value in row.items()}
#|    if len(lookup) != 6:
#|        raise SystemExit(f"{DETAILED_FAULT_BRIDGE_AUDIT_NAME} must contain current fault panel 6 rows, found {len(lookup)}")
#|
#|    summary_row = summary_df.iloc[0]
#|    meta = {
#|        "fault_panel_count": int(pd.to_numeric(summary_row["고장패널수"], errors="raise")),
#|        "attached_count": int(pd.to_numeric(summary_row["세부fault_부착수"], errors="raise")),
#|        "held_count": int(pd.to_numeric(summary_row["세부fault_보류수"], errors="raise")),
#|        "exact_match_count": int(pd.to_numeric(summary_row["exact_date_match_패널수"], errors="raise")),
#|        "conflict_count": int(pd.to_numeric(summary_row["exact_date_conflict_패널수"], errors="raise")),
#|        "miss_count": int(pd.to_numeric(summary_row["exact_date_miss_패널수"], errors="raise")),
#|        "note_ko": normalize_text(summary_row["note_ko"]),
#|    }
#|    if meta["fault_panel_count"] != 6:
#|        raise SystemExit(f"{DETAILED_FAULT_BRIDGE_SUMMARY_NAME} 고장패널수 must be 6, found {meta['fault_panel_count']}")
#|    return lookup, meta
#|
#|
#|def gpvs_detailed_type_attachment_lookup(
#|    audit_df: pd.DataFrame,
#|    sanity_df: pd.DataFrame,
#|    rebuild_summary_df: pd.DataFrame,
#|) -> tuple[dict[tuple[str, str], dict[str, str]], dict[str, int | str]]:
#|    if audit_df[["site", "panel_id"]].duplicated().any():
#|        dup = audit_df.loc[audit_df[["site", "panel_id"]].duplicated(keep=False), ["site", "panel_id"]]
#|        raise SystemExit(
#|            f"{GPVS_DETAILED_TYPE_INFERENCE_AUDIT_NAME} must be unique by (site, panel_id): {dup.to_dict(orient='records')[:5]}"
#|        )
#|    if sanity_df[["site", "panel_id"]].duplicated().any():
#|        dup = sanity_df.loc[sanity_df[["site", "panel_id"]].duplicated(keep=False), ["site", "panel_id"]]
#|        raise SystemExit(
#|            f"{GPVS_DETAILED_TYPE_REALPANEL_SANITY_NAME} must be unique by (site, panel_id): {dup.to_dict(orient='records')[:5]}"
#|        )
#|
#|    audit_lookup: dict[tuple[str, str], dict[str, str]] = {}
#|    for row in audit_df.to_dict(orient="records"):
#|        key = (normalize_text(row["site"]), normalize_text(row["panel_id"]))
#|        audit_lookup[key] = {column: normalize_text(value) for column, value in row.items()}
#|    sanity_lookup: dict[tuple[str, str], dict[str, str]] = {}
#|    for row in sanity_df.to_dict(orient="records"):
#|        key = (normalize_text(row["site"]), normalize_text(row["panel_id"]))
#|        sanity_lookup[key] = {column: normalize_text(value) for column, value in row.items()}
#|
#|    if len(audit_lookup) != 6:
#|        raise SystemExit(f"{GPVS_DETAILED_TYPE_INFERENCE_AUDIT_NAME} must contain current fault panel 6 rows, found {len(audit_lookup)}")
#|    if len(sanity_lookup) != 6:
#|        raise SystemExit(f"{GPVS_DETAILED_TYPE_REALPANEL_SANITY_NAME} must contain current fault panel 6 rows, found {len(sanity_lookup)}")
#|
#|    summary_row = rebuild_summary_df.iloc[0]
#|    attachable_flag = int(pd.to_numeric(summary_row["current_recovered_attachable_flag"], errors="raise"))
#|    recovered_exported_flag = int(pd.to_numeric(summary_row["recovered_model_exported_flag"], errors="raise"))
#|    parity_status = normalize_text(summary_row["parity_overall_status_ko"])
#|    note_ko = normalize_text(summary_row["note_ko"])
#|
#|    lookup: dict[tuple[str, str], dict[str, str]] = {}
#|    attached_expected = 0
#|    deferred_expected = 0
#|    for key, audit_row in audit_lookup.items():
#|        sanity_row = sanity_lookup.get(key)
#|        attach_recommendation = normalize_text((sanity_row or {}).get("attach_recommendation_ko", ""))
#|        model_source = normalize_text(audit_row.get("gpvs_detailed_model_source", ""))
#|        guard_ok = (
#|            attachable_flag == 1
#|            and model_source == "recovered_artifact"
#|            and attach_recommendation == "attach_ok"
#|        )
#|        merged = dict(audit_row)
#|        merged["attach_recommendation_ko"] = attach_recommendation
#|        merged["__guard_ok"] = "1" if guard_ok else "0"
#|        lookup[key] = merged
#|        if guard_ok:
#|            attached_expected += 1
#|        else:
#|            deferred_expected += 1
#|
#|    return lookup, {
#|        "fault_panel_count": 6,
#|        "attached_count": attached_expected,
#|        "deferred_count": deferred_expected,
#|        "recovered_exported_flag": recovered_exported_flag,
#|        "attachable_flag": attachable_flag,
#|        "parity_status_ko": parity_status,
#|        "note_ko": note_ko,
#|    }
#|
#|
#|def gpvs_reference_front_lookup(
#|    panel_agreement_df: pd.DataFrame,
#|) -> dict[tuple[str, str], dict[str, str]]:
#|    if panel_agreement_df[["site", "panel_id"]].duplicated().any():
#|        dup = panel_agreement_df.loc[
#|            panel_agreement_df[["site", "panel_id"]].duplicated(keep=False),
#|            ["site", "panel_id"],
#|        ]
#|        raise SystemExit(
#|            f"{GPVS_MLPE_PANEL_AGREEMENT_NAME} must be unique by (site, panel_id): {dup.to_dict(orient='records')[:5]}"
#|        )
#|    lookup: dict[tuple[str, str], dict[str, str]] = {}
#|    for row in panel_agreement_df.to_dict(orient="records"):
#|        key = (normalize_text(row["site"]), normalize_text(row["panel_id"]))
#|        lookup[key] = {column: normalize_text(value) for column, value in row.items()}
#|    return lookup
#|
#|
#|def build_outputs(
#|    root: Path,
#|    frames: dict[str, pd.DataFrame],
#|) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, int | str], dict[str, str]]:
#|    workflow_panel_df = build_workflow_panel_df(frames["workflow"])
#|    cluster_df = build_cluster_df(frames["workflow"])
#|    workflow_by_key = workflow_lookup(workflow_panel_df)
#|    abrupt_by_key = abrupt_lookup(frames["abrupt6"])
#|    final_pack_by_scope = final_pack_lookup(frames["final_pack"])
#|    same_event_overlap_keys = load_same_event_overlap_keys(frames)
#|    forensic_rule_case = load_forensic_rule_case(frames)
#|    fault_audit_by_key = fault_event_audit_lookup(frames)
#|    detailed_fault_by_key, detailed_fault_meta = detailed_fault_bridge_lookup(
#|        frames["detailed_fault_bridge_audit"],
#|        frames["detailed_fault_bridge_summary"],
#|    )
#|    gpvs_detailed_type_by_key, gpvs_detailed_type_meta = gpvs_detailed_type_attachment_lookup(
#|        frames["gpvs_detailed_type_audit"],
#|        frames["gpvs_detailed_type_realpanel_sanity"],
#|        frames["gpvs_bytype_rebuild_summary"],
#|    )
#|    gpvs_reference_front_by_key = gpvs_reference_front_lookup(frames["gpvs_mlpe_panel_agreement"])
#|    precursor_truth_by_key = precursor_truth_lookup(frames["precursor_truth"])
#|    forensic_rule_key = (FORENSIC_RULE_SITE, FORENSIC_RULE_PANEL_ID)
#|
#|    workflow_keys = set(workflow_by_key.keys())
#|    abrupt_keys = set(abrupt_by_key.keys())
#|    pure_abrupt_keys = abrupt_keys - same_event_overlap_keys - {forensic_rule_key}
#|    precursor_keys = build_precursor_positive_keys(frames["precursor_truth"])
#|    precursor_eval_keys = precursor_keys
#|    abrupt_eval_keys = build_abrupt_eval_keys(frames["non_precursor_perf"])
#|    common_keys = build_common_cause_positive_keys(frames["common_cause"])
#|    workflow_watch_keys = {
#|        (normalize_text(row["site"]), normalize_text(row["display_entity_id"]))
#|        for row in workflow_panel_df.loc[workflow_panel_df["preview_attention_class"].eq("watch_now_panel")].to_dict(orient="records")
#|    }
#|    panel_keys = set().union(workflow_keys, abrupt_keys, precursor_keys, common_keys)
#|    if not same_event_overlap_keys.issubset(abrupt_keys):
#|        raise SystemExit("same-event overlap panels must be included in abrupt symptom map universe")
#|    if not same_event_overlap_keys.issubset(precursor_keys):
#|        raise SystemExit("same-event overlap panels must be included in precursor-positive universe")
#|    if forensic_rule_key not in abrupt_keys:
#|        raise SystemExit("forensic target panel must remain in abrupt symptom map universe")
#|
#|    gpvs_by_key, gpvs_feasibility_meta, gpvs_expected_attach_count = recover_gpvs_panel_level_reference_from_audit(
#|        frames["gpvs_attach_feasibility"],
#|        frames["gpvs_attach_candidates"],
#|        panel_keys,
#|    )
#|    gpvs_default_unattached_reason = gpvs_unattached_reason(
#|        frames["gpvs_attach_inventory"],
#|        gpvs_feasibility_meta,
#|    )
#|    gpvs_best_source = normalize_text(gpvs_feasibility_meta.get("best_source", ""))
#|    gpvs_expected_attach_count_applicable = 0
#|
#|    panel_rows: list[dict[str, object]] = []
#|    event_rows: list[dict[str, object]] = []
#|
#|    for site, panel_id in sorted(panel_keys):
#|        key = (site, panel_id)
#|        workflow_row = workflow_by_key.get(key)
#|        abrupt_row = abrupt_by_key.get(key)
#|        precursor_truth_row = precursor_truth_by_key.get(key)
#|        is_same_event_overlap = key in same_event_overlap_keys
#|        active_forensic_rule_case = forensic_rule_case if key == forensic_rule_key else None
#|        active_fault_audit_row = fault_audit_by_key.get(key)
#|        precursor_eval_flag = int(key in precursor_eval_keys)
#|        abrupt_eval_flag = int(key in abrupt_eval_keys)
#|        flags = {
#|            "has_전조형고장": int(key in precursor_keys),
#|            "has_급작고장": int(key in pure_abrupt_keys),
#|            "has_공통원인이벤트": int(key in common_keys),
#|            "has_반복이상": int(key in workflow_watch_keys),
#|        }
#|
#|        event_type, terminal_pattern = event_type_and_terminal_pattern(
#|            flags,
#|            is_same_event_overlap=is_same_event_overlap,
#|            forensic_rule_case=active_forensic_rule_case,
#|            fault_audit_row=active_fault_audit_row,
#|        )
#|        representative_verdict = event_type
#|        history = event_history_text(
#|            flags,
#|            is_same_event_overlap=is_same_event_overlap,
#|            forensic_rule_case=active_forensic_rule_case,
#|            fault_audit_row=active_fault_audit_row,
#|        )
#|        interpretation = interpretation_layer_fields(
#|            flags,
#|            event_type,
#|            precursor_eval_flag=precursor_eval_flag,
#|            abrupt_eval_flag=abrupt_eval_flag,
#|            is_same_event_overlap=is_same_event_overlap,
#|            forensic_rule_case=active_forensic_rule_case,
#|            fault_audit_row=active_fault_audit_row,
#|        )
#|        operational_first_precursor_detected_date = ""
#|        operational_first_precursor_marker_name = ""
#|        interpretive_precursor_onset_date = ""
#|        benchmark_precursor_onset_date = ""
#|        if precursor_truth_row is not None and panel_fault_status_from_event_type(event_type) == "고장":
#|            operational_first_precursor_detected_date = normalize_text(
#|                precursor_truth_row.get("operational_first_precursor_detected_date", "")
#|            )
#|            operational_first_precursor_marker_name = normalize_text(
#|                precursor_truth_row.get("operational_first_precursor_marker_name", "")
#|            )
#|            interpretive_precursor_onset_date = normalize_text(
#|                precursor_truth_row.get("interpretive_precursor_onset_date", "")
#|            )
#|            benchmark_precursor_onset_date = (
#|                normalize_text(precursor_truth_row.get("benchmark_precursor_onset_date", ""))
#|                or normalize_text(precursor_truth_row.get("preferred_precursor_onset_date", ""))
#|            )
#|        panel_fault_status = panel_fault_status_from_event_type(event_type)
#|        gpvs_applicability = gpvs_applicability_from_fault_status(panel_fault_status)
#|        kernel_symptom, kernel_cause_group, kernel_note = map_kernel_axis(event_type, abrupt_row)
#|
#|        gpvs_row = gpvs_by_key.get(key)
#|        if gpvs_applicability == "비대상":
#|            gpvs_attach_status = "비대상"
#|            gpvs_type = "비대상"
#|            gpvs_reason = ""
#|            gpvs_unattached_note = GPVS_NON_TARGET_REASON
#|            gpvs_candidate_file = ""
#|        else:
#|            if gpvs_row is None:
#|                gpvs_attach_status = "미부착"
#|                gpvs_type = "미부착"
#|                gpvs_reason = GPVS_ABSENCE_REASON
#|                gpvs_unattached_note = gpvs_default_unattached_reason
#|                gpvs_candidate_file = gpvs_best_source
#|            else:
#|                gpvs_attach_status = "부착"
#|                gpvs_type = normalize_text(gpvs_row["GPVS_참고유형_ko"]) or "미부착"
#|                gpvs_reason = normalize_text(gpvs_row["GPVS_근거_ko"]) or GPVS_ABSENCE_REASON
#|                gpvs_unattached_note = ""
#|                gpvs_candidate_file = normalize_text(gpvs_row.get("GPVS_후보파일_ko", "")) or gpvs_best_source
#|                gpvs_expected_attach_count_applicable += 1
#|
#|        detailed_fault_row = detailed_fault_by_key.get(key)
#|        if panel_fault_status == "고장":
#|            if detailed_fault_row is None:
#|                raise SystemExit(f"{DETAILED_FAULT_BRIDGE_AUDIT_NAME} missing fault panel row for {site}/{panel_id}")
#|            detailed_attachable = int(
#|                pd.to_numeric(pd.Series([detailed_fault_row["attachable_flag"]]), errors="coerce").fillna(0).iloc[0]
#|            )
#|            detailed_reference_date = normalize_text(detailed_fault_row["reference_date"])
#|            detailed_files = normalize_text(detailed_fault_row["matched_files_csv"])
#|            detailed_code = normalize_text(detailed_fault_row["consensus_fault_type_code"])
#|            detailed_reason = normalize_text(detailed_fault_row["attach_reason_ko"])
#|            if detailed_attachable == 1 and detailed_code:
#|                detailed_status = "부착"
#|                detailed_label = detailed_fault_type_label(detailed_code)
#|                detailed_hold_reason = ""
#|            else:
#|                detailed_status = "보류"
#|                detailed_code = ""
#|                detailed_label = ""
#|                detailed_hold_reason = detailed_reason
#|        else:
#|            detailed_status = "비대상"
#|            detailed_code = ""
#|            detailed_label = ""
#|            detailed_files = ""
#|            detailed_reference_date = ""
#|            detailed_hold_reason = ""
#|
#|        gpvs_detailed_row = gpvs_detailed_type_by_key.get(key)
#|        if panel_fault_status == "고장":
#|            attach_guard_ok = gpvs_detailed_row is not None and normalize_text(gpvs_detailed_row.get("__guard_ok")) == "1"
#|            if attach_guard_ok:
#|                gpvs_detailed_code = normalize_text(gpvs_detailed_row["gpvs_detailed_top1_fault_type"])
#|                gpvs_detailed_score = normalize_text(gpvs_detailed_row["gpvs_detailed_top1_score"])
#|                gpvs_detailed_rank2 = normalize_text(gpvs_detailed_row["gpvs_detailed_top2_fault_type"])
#|                gpvs_detailed_rank2_score = normalize_text(gpvs_detailed_row["gpvs_detailed_top2_score"])
#|                gpvs_detailed_margin = normalize_text(gpvs_detailed_row["gpvs_detailed_margin"])
#|                gpvs_detailed_attach_status = "부착"
#|                gpvs_detailed_reason = "recovered_artifact by-type inference"
#|                gpvs_detailed_caution = "family와 detailed type은 별도 축"
#|            else:
#|                gpvs_detailed_code = ""
#|                gpvs_detailed_score = ""
#|                gpvs_detailed_rank2 = ""
#|                gpvs_detailed_rank2_score = ""
#|                gpvs_detailed_margin = ""
#|                gpvs_detailed_attach_status = "판정유보"
#|                gpvs_detailed_reason = "attach guard 미충족"
#|                gpvs_detailed_caution = ""
#|            gpvs_detailed_status = gpvs_detailed_attach_status
#|        else:
#|            gpvs_detailed_code = ""
#|            gpvs_detailed_score = ""
#|            gpvs_detailed_rank2 = ""
#|            gpvs_detailed_rank2_score = ""
#|            gpvs_detailed_margin = ""
#|            gpvs_detailed_status = "비대상"
#|            gpvs_detailed_attach_status = "비대상"
#|            gpvs_detailed_reason = ""
#|            gpvs_detailed_caution = ""
#|
#|        universe_parts: list[str] = []
#|        if flags["has_전조형고장"]:
#|            universe_parts.append("precursor onset truth positive universe 포함")
#|        if flags["has_급작고장"]:
#|            universe_parts.append("abrupt6 positive universe 포함")
#|        if flags["has_공통원인이벤트"]:
#|            universe_parts.append("common-cause descriptive positive universe 포함")
#|        if flags["has_반복이상"]:
#|            universe_parts.append("workflow watch_now_panel 포함")
#|        if active_forensic_rule_case is not None:
#|            universe_parts.append("single-panel forensic explicit rule 적용")
#|        if active_fault_audit_row is not None:
#|            universe_parts.append("fault panel event audit explicit rule 적용")
#|        if workflow_row is None:
#|            universe_parts.append("현재 workflow default row에는 아직 없음")
#|        if not universe_parts:
#|            universe_parts.append("workflow current row 기반 fallback verdict")
#|
#|        caution_parts = [
#|            current_data_scope_note(event_type, terminal_pattern, final_pack_by_scope),
#|            kernel_note,
#|            f"사건유형={event_type}, 최종고장양상={terminal_pattern}",
#|            f"사건이력={history}" if history else "사건이력 없음",
#|            "; ".join(universe_parts),
#|        ]
#|        if gpvs_attach_status == "미부착":
#|            caution_parts.append(gpvs_unattached_note or GPVS_ABSENCE_REASON)
#|        if gpvs_attach_status == "비대상":
#|            caution_parts.append(GPVS_NON_TARGET_REASON)
#|        if detailed_status == "부착":
#|            caution_parts.append(f"세부fault_type={detailed_label} ({detailed_code}) exact-date consensus 부착")
#|        elif detailed_status == "보류":
#|            caution_parts.append(f"세부fault_type 보류={detailed_hold_reason or 'unknown'}")
#|        if gpvs_detailed_attach_status == "부착":
#|            gpvs_detailed_score_part = f", score={gpvs_detailed_score}" if gpvs_detailed_score else ""
#|            gpvs_detailed_margin_part = f", margin={gpvs_detailed_margin}" if gpvs_detailed_margin else ""
#|            caution_parts.append(
#|                f"GPVS learned by-type 세부fault={gpvs_detailed_code}{gpvs_detailed_score_part}{gpvs_detailed_margin_part}"
#|            )
#|        elif gpvs_detailed_attach_status == "판정유보":
#|            caution_parts.append(f"GPVS learned by-type 세부fault 판정유보={gpvs_detailed_reason or 'unknown'}")
#|        if active_fault_audit_row is not None:
#|            caution_parts.append(
#|                f"fault panel event audit 재판정={normalize_text(active_fault_audit_row['사건유형_재판정_ko'])}/{normalize_text(active_fault_audit_row['최종고장양상_재판정_ko'])}"
#|            )
#|            caution_parts.append(normalize_text(active_fault_audit_row["재판정_근거_ko"]))
#|        if active_forensic_rule_case is not None:
#|            caution_parts.append(
#|                f"explicit stored-field rule onset={normalize_text(active_forensic_rule_case.get('__forensic_onset_date')) or FORENSIC_RULE_ONSET_DATE}, "
#|                f"trigger={normalize_text(active_forensic_rule_case.get('__forensic_trigger_date')) or FORENSIC_RULE_TRIGGER_DATE}"
#|            )
#|            caution_parts.append(FORENSIC_RULE_REASON)
#|            caution_parts.append(
#|                f"현재 재감사 family hint={forensic_rule_case['현재_재감사라벨_ko']}"
#|            )
#|        onset_split_parts = []
#|        if operational_first_precursor_detected_date:
#|            onset_split_parts.append(
#|                f"운영상 최초 전조 발견={operational_first_precursor_detected_date}"
#|                + (f" ({operational_first_precursor_marker_name})" if operational_first_precursor_marker_name else "")
#|            )
#|        if interpretive_precursor_onset_date:
#|            onset_split_parts.append(f"사건 해석상 전조 시작={interpretive_precursor_onset_date}")
#|        if benchmark_precursor_onset_date:
#|            onset_split_parts.append(f"benchmark 전조 시작={benchmark_precursor_onset_date}")
#|        if onset_split_parts:
#|            caution_parts.append(" / ".join(onset_split_parts))
#|        if normalize_text(interpretation["해석대평가차이_ko"]):
#|            caution_parts.append(normalize_text(interpretation["해석대평가차이_ko"]))
#|        gpvs_scenario_info = gpvs_scenario_fields(gpvs_detailed_code)
#|        gpvs_reference_front_row = gpvs_reference_front_by_key.get(key)
#|        if panel_fault_status == "고장" and gpvs_reference_front_row is None:
#|            raise SystemExit(f"{GPVS_MLPE_PANEL_AGREEMENT_NAME} missing fault panel row for {site}/{panel_id}")
#|        gpvs_front_fields = gpvs_front_facing_fields(
#|            panel_fault_status=panel_fault_status,
#|            gpvs_type=gpvs_type,
#|            gpvs_detailed_code=gpvs_detailed_code,
#|            panel_agreement_row=gpvs_reference_front_row,
#|        )
#|
#|        panel_rows.append(
#|            {
#|                "site": site,
#|                "panel_id": panel_id,
#|                "사건유형_ko": event_type,
#|                "사건유형_해석_ko": interpretation["사건유형_해석_ko"],
#|                "최종고장양상_ko": terminal_pattern,
#|                "대표판정_ko": representative_verdict,
#|                "사건이력_ko": history,
#|                "전조흔적_flag": interpretation["전조흔적_flag"],
#|                "순수급작_flag": interpretation["순수급작_flag"],
#|                "전조평가셋편입_flag": interpretation["전조평가셋편입_flag"],
#|                "급작평가셋편입_flag": interpretation["급작평가셋편입_flag"],
#|                "해석대평가차이_ko": interpretation["해석대평가차이_ko"],
#|                "운영최초전조발견일": operational_first_precursor_detected_date,
#|                "운영최초전조마커": operational_first_precursor_marker_name,
#|                "사건해석상전조시작일": interpretive_precursor_onset_date,
#|                "benchmark전조시작일": benchmark_precursor_onset_date,
#|                "전조형이력_flag": flags["has_전조형고장"],
#|                "급작고장이력_flag": flags["has_급작고장"],
#|                "공통원인이력_flag": flags["has_공통원인이벤트"],
#|                "반복이상이력_flag": flags["has_반복이상"],
#|                "패널고장여부_ko": panel_fault_status,
#|                "GPVS_적용대상_ko": gpvs_applicability,
#|                "커널로그_증상명_ko": kernel_symptom,
#|                "커널로그_원인군_ko": kernel_cause_group,
#|                "GPVS_부착상태_ko": gpvs_attach_status,
#|                "GPVS_내부참고유형_ko": gpvs_front_fields["GPVS_내부참고유형_ko"],
#|                "GPVS_외부참조패턴_ko": gpvs_front_fields["GPVS_외부참조패턴_ko"],
#|                "GPVS_참조사용등급_ko": gpvs_front_fields["GPVS_참조사용등급_ko"],
#|                "GPVS_참조설명_ko": gpvs_front_fields["GPVS_참조설명_ko"],
#|                "GPVS_참고유형_ko": gpvs_type,
#|                "GPVS_근거_ko": gpvs_reason,
#|                "GPVS_미부착사유_ko": gpvs_unattached_note,
#|                "GPVS_후보파일_ko": gpvs_candidate_file,
#|                "GPVS_세부fault_code": gpvs_detailed_code,
#|                "GPVS_세부fault_score": gpvs_detailed_score,
#|                "GPVS_세부fault_rank2_code": gpvs_detailed_rank2,
#|                "GPVS_세부fault_rank2_score": gpvs_detailed_rank2_score,
#|                "GPVS_세부fault_margin": gpvs_detailed_margin,
#|                "GPVS_세부fault_status_ko": gpvs_detailed_status,
#|                "GPVS_세부fault_부착상태_ko": gpvs_detailed_attach_status,
#|                "GPVS_세부fault_근거_ko": gpvs_detailed_reason,
#|                "GPVS_세부fault_판정주의_ko": gpvs_detailed_caution,
#|                "GPVS_시나리오_family_ko": gpvs_scenario_info["GPVS_시나리오_family_ko"],
#|                "GPVS_시나리오명_ko": gpvs_scenario_info["GPVS_시나리오명_ko"],
#|                "GPVS_시나리오_고장상황설명_ko": gpvs_scenario_info["GPVS_시나리오_고장상황설명_ko"],
#|                "GPVS_운전모드_ko": gpvs_scenario_info["GPVS_운전모드_ko"],
#|                "GPVS_해석주의_ko": gpvs_scenario_info["GPVS_해석주의_ko"],
#|                "세부fault_type_code": detailed_code,
#|                "세부fault_type_label_ko": detailed_label,
#|                "세부fault_부착상태_ko": detailed_status,
#|                "세부fault_근거파일_ko": detailed_files,
#|                "세부fault_기준일": detailed_reference_date,
#|                "세부fault_보류사유_ko": detailed_hold_reason,
#|                "운영위치_ko": map_operating_location(workflow_row),
#|                "판정주의_ko": " ".join(part for part in caution_parts if part),
#|            }
#|        )
#|
#|        event_members: list[tuple[str, str]] = []
#|        if active_fault_audit_row is not None:
#|            event_members.append(
#|                (
#|                    normalize_text(active_fault_audit_row["사건유형_재판정_ko"]) or event_type,
#|                    "fault panel event audit explicit stored-field rule 기준 대표사건",
#|                )
#|            )
#|        elif active_forensic_rule_case is not None:
#|            event_members.append(
#|                (
#|                    normalize_text(active_forensic_rule_case["사건유형_결정_ko"]) or event_type,
#|                    "single-panel forensic explicit stored-field rule 기준 대표사건",
#|                )
#|            )
#|        elif flags["has_전조형고장"]:
#|            if is_same_event_overlap:
#|                event_members.append(("전조형 고장", "같은 사건 audit 기준 최종고장양상=급격 종료"))
#|            else:
#|                event_members.append(("전조형 고장", "stored precursor positive universe 포함"))
#|        if flags["has_급작고장"]:
#|            event_members.append(("급작 고장", "stored pure abrupt positive universe 포함"))
#|        if flags["has_공통원인이벤트"]:
#|            event_members.append(("공통원인 이벤트", "stored common-cause positive universe 포함"))
#|        if flags["has_반복이상"]:
#|            event_members.append(("반복 이상", "workflow watch_now_panel 포함"))
#|
#|        deduped_event_members: list[tuple[str, str]] = []
#|        seen_event_names: set[str] = set()
#|        for event_name, event_note in event_members:
#|            if event_name in seen_event_names:
#|                continue
#|            seen_event_names.add(event_name)
#|            deduped_event_members.append((event_name, event_note))
#|
#|        for event_name, event_note in deduped_event_members:
#|            if not history:
#|                break
#|            event_rows.append(
#|                {
#|                    "site": site,
#|                    "panel_id": panel_id,
#|                    "사건유형_ko": event_name,
#|                    "사건우선순위": EVENT_PRIORITY[event_name],
#|                    "대표판정여부_flag": int(event_name == representative_verdict),
#|                    "운영위치_ko": map_operating_location(workflow_row),
#|                    "비고_ko": (
#|                        "대표판정과 동일"
#|                        if event_name == representative_verdict
#|                        else f"대표판정은 `{representative_verdict}` 이고 이 row는 사건이력 보존용"
#|                    ),
#|                }
#|            )
#|            if event_note:
#|                event_rows[-1]["비고_ko"] = (
#|                    f"{event_rows[-1]['비고_ko']}; {event_note}"
#|                    if normalize_text(event_rows[-1]["비고_ko"])
#|                    else event_note
#|                )
#|
#|    cluster_rows: list[dict[str, str]] = []
#|    for row in cluster_df.to_dict(orient="records"):
#|        cluster_rows.append(
#|            {
#|                "site": normalize_text(row["site"]),
#|                "cluster_id": normalize_text(row["display_entity_id"]),
#|                "대표판정_ko": "공통원인 이벤트",
#|                "커널로그_증상명_ko": "패턴 이상형",
#|                "GPVS_참고유형_ko": "미부착",
#|                "GPVS_근거_ko": GPVS_ABSENCE_REASON,
#|                "운영위치_ko": "추가 발견 후보",
#|                "판정주의_ko": "secondary discovery cluster 보조 row이며 panel-level 개별 verdict로 확장하지 않는다. "
#|                + GPVS_ABSENCE_REASON,
#|            }
#|        )
#|
#|    verdict_internal_df = pd.DataFrame(panel_rows)
#|    verdict_df = verdict_internal_df.reindex(columns=VERDICT_COLS)
#|    event_supplement_df = pd.DataFrame(event_rows).reindex(columns=EVENT_SUPPLEMENT_COLS)
#|    cluster_supplement_df = pd.DataFrame(cluster_rows).reindex(columns=CLUSTER_COLS)
#|
#|    if verdict_df.empty:
#|        raise SystemExit("panel-level representative verdict table is empty")
#|
#|    metrics = {
#|        "workflow_panel_count": len(workflow_keys),
#|        "workflow_cluster_count": len(cluster_df),
#|        "abrupt_fault6_total": len(abrupt_keys),
#|        "pure_abrupt_expected": len(pure_abrupt_keys),
#|        "same_event_overlap_expected": len(same_event_overlap_keys),
#|        "forensic_rule_expected": 1,
#|        "fault_audit_expected": len(fault_audit_by_key),
#|        "precursor_expected": len(precursor_keys),
#|        "precursor_eval_expected": len(precursor_eval_keys),
#|        "abrupt_eval_expected": len(abrupt_eval_keys),
#|        "common_expected": len(common_keys),
#|        "gpvs_expected_attach_count": gpvs_expected_attach_count_applicable,
#|        "gpvs_detailed_attached_expected": int(gpvs_detailed_type_meta["attached_count"]),
#|        "gpvs_detailed_deferred_expected": int(gpvs_detailed_type_meta["deferred_count"]),
#|        "gpvs_detailed_impossible_expected": 0,
#|        "gpvs_detailed_note": str(gpvs_detailed_type_meta["note_ko"]),
#|        "detailed_fault_attached_expected": int(detailed_fault_meta["attached_count"]),
#|        "detailed_fault_held_expected": int(detailed_fault_meta["held_count"]),
#|        "detailed_fault_exact_match_expected": int(detailed_fault_meta["exact_match_count"]),
#|        "detailed_fault_conflict_expected": int(detailed_fault_meta["conflict_count"]),
#|        "detailed_fault_miss_expected": int(detailed_fault_meta["miss_count"]),
#|        "detailed_fault_note": str(detailed_fault_meta["note_ko"]),
#|    }
#|    return verdict_df, verdict_internal_df, event_supplement_df, cluster_supplement_df, metrics, gpvs_feasibility_meta
#|
#|
#|def compute_final_row_counts(verdict_df: pd.DataFrame) -> dict[str, int]:
#|    abrupt_flags = to_numeric_flag(verdict_df["급작고장이력_flag"]).astype(int)
#|    precursor_flags = to_numeric_flag(verdict_df["전조형이력_flag"]).astype(int)
#|    common_flags = to_numeric_flag(verdict_df["공통원인이력_flag"]).astype(int)
#|    repeat_flags = to_numeric_flag(verdict_df["반복이상이력_flag"]).astype(int)
#|    precursor_trace_flags = to_numeric_flag(verdict_df["전조흔적_flag"]).astype(int)
#|    pure_abrupt_flags = to_numeric_flag(verdict_df["순수급작_flag"]).astype(int)
#|    precursor_eval_flags = to_numeric_flag(verdict_df["전조평가셋편입_flag"]).astype(int)
#|    abrupt_eval_flags = to_numeric_flag(verdict_df["급작평가셋편입_flag"]).astype(int)
#|    event_type_counts = verdict_df["사건유형_ko"].value_counts().to_dict()
#|    panel_fault_counts = verdict_df["패널고장여부_ko"].value_counts().to_dict()
#|    interpretation_eval_mismatch_count = int(verdict_df["해석대평가차이_ko"].map(normalize_text).ne("").sum())
#|
#|    abrupt_ending_mask = verdict_df["최종고장양상_ko"].eq("급격 종료") & verdict_df["사건유형_ko"].eq("전조형 고장")
#|    progressive_precursor_mask = verdict_df["사건유형_ko"].eq("전조형 고장") & verdict_df["최종고장양상_ko"].eq("진행성 악화")
#|    interpreted_precursor_mask = verdict_df["사건유형_ko"].eq("전조형 고장")
#|    interpreted_abrupt_mask = verdict_df["사건유형_ko"].eq("급작 고장")
#|
#|    return {
#|        "전체_패널수": int(len(verdict_df)),
#|        "고유_고장패널수": int(verdict_df["패널고장여부_ko"].eq("고장").sum()),
#|        "사건해석_전조형_패널수": int(interpreted_precursor_mask.sum()),
#|        "사건해석_급작_패널수": int(interpreted_abrupt_mask.sum()),
#|        "사건해석_전조형_급격종료_패널수": int(abrupt_ending_mask.sum()),
#|        "사건해석_전조형_진행성악화_패널수": int(progressive_precursor_mask.sum()),
#|        "전조흔적_패널수": int(precursor_trace_flags.sum()),
#|        "엄격전조평가셋_패널수": int(precursor_eval_flags.sum()),
#|        "순수급작평가셋_패널수": int(abrupt_eval_flags.sum()),
#|        "해석과평가셋불일치_패널수": interpretation_eval_mismatch_count,
#|        "공통원인이력_패널수": int(common_flags.sum()),
#|        "반복이상이력_패널수": int(repeat_flags.sum()),
#|        "대표판정_급작수": int(event_type_counts.get("급작 고장", 0)),
#|        "대표판정_전조형수": int(event_type_counts.get("전조형 고장", 0)),
#|        "대표판정_공통원인수": int(event_type_counts.get("공통원인 이벤트", 0)),
#|        "대표판정_반복이상수": int(event_type_counts.get("반복 이상", 0)),
#|        "대표판정_고장유형보류수": int(event_type_counts.get("고장유형 보류", 0)),
#|        "대표판정_불충분수": int(event_type_counts.get("불충분", 0)),
#|        "고장_패널수": int(panel_fault_counts.get("고장", 0)),
#|        "비고장_패널수": int(panel_fault_counts.get("비고장", 0)),
#|        "미확정_패널수": int(panel_fault_counts.get("미확정", 0)),
#|    }
#|
#|
#|def validate_real_coverage(
#|    verdict_df: pd.DataFrame,
#|    event_supplement_df: pd.DataFrame,
#|    cluster_supplement_df: pd.DataFrame,
#|    metrics: dict[str, int],
#|) -> None:
#|    if verdict_df["panel_id"].eq("").any():
#|        raise SystemExit("main panel verdict table must not contain blank panel_id rows")
#|    if verdict_df.duplicated(subset=["site", "panel_id"]).any():
#|        dup = verdict_df.loc[verdict_df.duplicated(subset=["site", "panel_id"], keep=False), ["site", "panel_id"]]
#|        raise SystemExit(f"main panel verdict table must be unique by (site, panel_id): {dup.to_dict(orient='records')[:5]}")
#|
#|    counts = compute_final_row_counts(verdict_df)
#|    interpreted_abrupt_membership = counts["사건해석_급작_패널수"]
#|    interpreted_precursor_membership = counts["사건해석_전조형_패널수"]
#|    common_membership = counts["공통원인이력_패널수"]
#|    gpvs_attached = int(verdict_df["GPVS_부착상태_ko"].eq("부착").sum())
#|    gpvs_detailed_attached = int(verdict_df["GPVS_세부fault_부착상태_ko"].eq("부착").sum())
#|    gpvs_detailed_deferred = int(verdict_df["GPVS_세부fault_부착상태_ko"].eq("판정유보").sum())
#|    gpvs_detailed_nontarget = int(verdict_df["GPVS_세부fault_부착상태_ko"].eq("비대상").sum())
#|    detailed_fault_attached = int(verdict_df["세부fault_부착상태_ko"].eq("부착").sum())
#|    detailed_fault_held = int(verdict_df["세부fault_부착상태_ko"].eq("보류").sum())
#|    detailed_fault_nontarget = int(verdict_df["세부fault_부착상태_ko"].eq("비대상").sum())
#|
#|    if counts["고유_고장패널수"] != 6:
#|        raise SystemExit(f"고유_고장패널수 must be 6, found {counts['고유_고장패널수']}")
#|    if interpreted_precursor_membership != 3:
#|        raise SystemExit(f"사건해석_전조형_패널수 must be 3, found {interpreted_precursor_membership}")
#|    if interpreted_abrupt_membership != 3:
#|        raise SystemExit(f"사건해석_급작_패널수 must be 3, found {interpreted_abrupt_membership}")
#|    if counts["사건해석_전조형_급격종료_패널수"] != 1:
#|        raise SystemExit(f"사건해석_전조형_급격종료_패널수 must be 1, found {counts['사건해석_전조형_급격종료_패널수']}")
#|    if counts["사건해석_전조형_진행성악화_패널수"] != 2:
#|        raise SystemExit(f"사건해석_전조형_진행성악화_패널수 must be 2, found {counts['사건해석_전조형_진행성악화_패널수']}")
#|    if counts["전조흔적_패널수"] != 3:
#|        raise SystemExit(f"전조흔적_패널수 must be 3, found {counts['전조흔적_패널수']}")
#|    if counts["엄격전조평가셋_패널수"] != 3:
#|        raise SystemExit(f"엄격전조평가셋_패널수 must be 3, found {counts['엄격전조평가셋_패널수']}")
#|    if counts["순수급작평가셋_패널수"] != 3:
#|        raise SystemExit(f"순수급작평가셋_패널수 must be 3, found {counts['순수급작평가셋_패널수']}")
#|    if counts["해석과평가셋불일치_패널수"] != 0:
#|        raise SystemExit(f"해석과평가셋불일치_패널수 must be 0, found {counts['해석과평가셋불일치_패널수']}")
#|    if common_membership != 4:
#|        raise SystemExit(f"panels with 공통원인이력_flag must be 4, found {common_membership}")
#|    if gpvs_attached != int(metrics["gpvs_expected_attach_count"]):
#|        raise SystemExit(
#|            f"GPVS attached row count must equal applicable direct-match count {metrics['gpvs_expected_attach_count']}, found {gpvs_attached}"
#|        )
#|    if gpvs_detailed_attached != int(metrics["gpvs_detailed_attached_expected"]):
#|        raise SystemExit(
#|            f"GPVS detailed attached row count must equal inference summary {metrics['gpvs_detailed_attached_expected']}, found {gpvs_detailed_attached}"
#|        )
#|    if gpvs_detailed_deferred != int(metrics["gpvs_detailed_deferred_expected"]):
#|        raise SystemExit(
#|            f"GPVS detailed deferred row count must equal inference summary {metrics['gpvs_detailed_deferred_expected']}, found {gpvs_detailed_deferred}"
#|        )
#|    if gpvs_detailed_nontarget != int(len(verdict_df) - counts["고유_고장패널수"]):
#|        raise SystemExit("GPVS detailed non-target row count must equal non-fault/non-uncertain panel count")
#|    if detailed_fault_attached != int(metrics["detailed_fault_attached_expected"]):
#|        raise SystemExit(
#|            f"세부fault attached row count must equal audit summary {metrics['detailed_fault_attached_expected']}, found {detailed_fault_attached}"
#|        )
#|    if detailed_fault_held != int(metrics["detailed_fault_held_expected"]):
#|        raise SystemExit(
#|            f"세부fault held row count must equal audit summary {metrics['detailed_fault_held_expected']}, found {detailed_fault_held}"
#|        )
#|    if detailed_fault_nontarget != int(len(verdict_df) - counts["고유_고장패널수"]):
#|        raise SystemExit("세부fault non-target row count must equal non-fault/non-uncertain panel count")
#|    if verdict_df.loc[verdict_df["GPVS_적용대상_ko"].eq("적용대상"), "패널고장여부_ko"].ne("고장").any():
#|        raise SystemExit("GPVS applicable rows must be fault panels only")
#|    if verdict_df.loc[verdict_df["패널고장여부_ko"].eq("고장"), "GPVS_적용대상_ko"].ne("적용대상").any():
#|        raise SystemExit("fault panels must be marked GPVS_적용대상_ko=적용대상")
#|    if verdict_df.loc[verdict_df["GPVS_부착상태_ko"].eq("부착"), "GPVS_적용대상_ko"].ne("적용대상").any():
#|        raise SystemExit("GPVS attached rows must be GPVS_적용대상_ko=적용대상")
#|    if verdict_df.loc[verdict_df["GPVS_부착상태_ko"].eq("미부착"), "GPVS_적용대상_ko"].ne("적용대상").any():
#|        raise SystemExit("GPVS unattached rows must be GPVS_적용대상_ko=적용대상")
#|    if verdict_df.loc[verdict_df["GPVS_부착상태_ko"].eq("부착"), "GPVS_참고유형_ko"].eq("미부착").any():
#|        raise SystemExit("GPVS attached rows must not keep GPVS_참고유형_ko=미부착")
#|    if verdict_df.loc[verdict_df["GPVS_부착상태_ko"].eq("미부착"), "GPVS_참고유형_ko"].ne("미부착").any():
#|        raise SystemExit("GPVS unattached rows must keep GPVS_참고유형_ko=미부착")
#|    if verdict_df.loc[verdict_df["GPVS_부착상태_ko"].eq("비대상"), "GPVS_참고유형_ko"].ne("비대상").any():
#|        raise SystemExit("GPVS non-target rows must keep GPVS_참고유형_ko=비대상")
#|    if verdict_df.loc[verdict_df["GPVS_부착상태_ko"].eq("비대상"), "GPVS_후보파일_ko"].map(normalize_text).ne("").any():
#|        raise SystemExit("GPVS non-target rows must keep GPVS_후보파일_ko blank")
#|    if verdict_df.loc[verdict_df["GPVS_부착상태_ko"].eq("비대상"), "GPVS_미부착사유_ko"].ne(GPVS_NON_TARGET_REASON).any():
#|        raise SystemExit(f"GPVS non-target rows must keep GPVS_미부착사유_ko={GPVS_NON_TARGET_REASON}")
#|    fault_gpvs_detailed = verdict_df.loc[verdict_df["패널고장여부_ko"].eq("고장")].copy()
#|    if fault_gpvs_detailed["GPVS_세부fault_부착상태_ko"].isin(["부착", "판정유보"]).ne(True).any():
#|        raise SystemExit("fault rows must keep GPVS_세부fault_부착상태_ko in {부착, 판정유보}")
#|    if verdict_df.loc[verdict_df["패널고장여부_ko"].ne("고장"), "GPVS_세부fault_부착상태_ko"].map(normalize_text).ne("비대상").any():
#|        raise SystemExit("non-fault rows must keep GPVS_세부fault_부착상태_ko=비대상")
#|    if verdict_df["GPVS_세부fault_status_ko"].map(normalize_text).ne(verdict_df["GPVS_세부fault_부착상태_ko"].map(normalize_text)).any():
#|        raise SystemExit("GPVS_세부fault_status_ko and GPVS_세부fault_부착상태_ko must stay synchronized")
#|    if verdict_df.loc[verdict_df["GPVS_세부fault_부착상태_ko"].eq("부착"), "GPVS_세부fault_code"].map(normalize_text).eq("").any():
#|        raise SystemExit("GPVS detailed attached rows must keep non-empty GPVS_세부fault_code")
#|    if verdict_df.loc[verdict_df["GPVS_세부fault_부착상태_ko"].eq("판정유보"), "GPVS_세부fault_code"].map(normalize_text).ne("").any():
#|        raise SystemExit("GPVS detailed deferred rows must keep empty GPVS_세부fault_code")
#|    if verdict_df.loc[verdict_df["GPVS_세부fault_부착상태_ko"].eq("부착"), "GPVS_세부fault_rank2_score"].map(normalize_text).eq("").any():
#|        raise SystemExit("GPVS detailed attached rows must keep non-empty GPVS_세부fault_rank2_score")
#|    if verdict_df.loc[verdict_df["GPVS_세부fault_부착상태_ko"].eq("부착"), "GPVS_세부fault_판정주의_ko"].map(normalize_text).ne("family와 detailed type은 별도 축").any():
#|        raise SystemExit("GPVS detailed attached rows must keep the separation caution note")
#|    if verdict_df.loc[verdict_df["GPVS_세부fault_부착상태_ko"].isin(["부착", "판정유보"]), "GPVS_세부fault_근거_ko"].map(normalize_text).eq("").any():
#|        raise SystemExit("fault rows with GPVS detailed inference status must keep non-empty GPVS_세부fault_근거_ko")
#|    gpvs_detailed_nontarget_subset = verdict_df.loc[
#|        verdict_df["패널고장여부_ko"].ne("고장"),
#|        [
#|            "GPVS_세부fault_code",
#|            "GPVS_세부fault_score",
#|            "GPVS_세부fault_rank2_code",
#|            "GPVS_세부fault_rank2_score",
#|            "GPVS_세부fault_margin",
#|            "GPVS_세부fault_근거_ko",
#|            "GPVS_세부fault_판정주의_ko",
#|        ],
#|    ].copy()
#|    if not gpvs_detailed_nontarget_subset.empty:
#|        gpvs_detailed_nontarget_subset = gpvs_detailed_nontarget_subset.apply(lambda column: column.map(normalize_text))
#|    if gpvs_detailed_nontarget_subset.ne("").any().any():
#|        raise SystemExit("non-fault rows must keep GPVS detailed inference columns blank")
#|    if verdict_df.loc[verdict_df["GPVS_세부fault_code"].map(normalize_text).ne(""), "GPVS_해석주의_ko"].map(normalize_text).ne(GPVS_SCENARIO_WARNING).any():
#|        raise SystemExit("rows with GPVS_세부fault_code must keep GPVS_해석주의_ko warning text")
#|    attached_scenario_subset = verdict_df.loc[
#|        verdict_df["GPVS_세부fault_code"].map(normalize_text).ne(""),
#|        [
#|            "GPVS_시나리오_family_ko",
#|            "GPVS_시나리오명_ko",
#|            "GPVS_시나리오_고장상황설명_ko",
#|            "GPVS_운전모드_ko",
#|            "GPVS_해석주의_ko",
#|        ],
#|    ].copy()
#|    if attached_scenario_subset.apply(lambda column: column.map(normalize_text)).eq("").any().any():
#|        raise SystemExit("rows with GPVS_세부fault_code must keep non-empty GPVS scenario semantics columns")
#|    gpvs_scenario_nontarget_subset = verdict_df.loc[
#|        verdict_df["GPVS_세부fault_code"].map(normalize_text).eq(""),
#|        [
#|            "GPVS_시나리오_family_ko",
#|            "GPVS_시나리오명_ko",
#|            "GPVS_시나리오_고장상황설명_ko",
#|            "GPVS_운전모드_ko",
#|            "GPVS_해석주의_ko",
#|        ],
#|    ].copy()
#|    if not gpvs_scenario_nontarget_subset.empty:
#|        gpvs_scenario_nontarget_subset = gpvs_scenario_nontarget_subset.apply(lambda column: column.map(normalize_text))
#|    if gpvs_scenario_nontarget_subset.ne("").any().any():
#|        raise SystemExit("rows without GPVS_세부fault_code must keep GPVS scenario semantics columns blank")
#|    front_facing_columns = [
#|        "GPVS_내부참고유형_ko",
#|        "GPVS_외부참조패턴_ko",
#|        "GPVS_참조사용등급_ko",
#|        "GPVS_참조설명_ko",
#|    ]
#|    front_non_fault_subset = verdict_df.loc[
#|        verdict_df["패널고장여부_ko"].ne("고장"),
#|        front_facing_columns,
#|    ].copy()
#|    if not front_non_fault_subset.empty:
#|        front_non_fault_subset = front_non_fault_subset.apply(lambda column: column.map(normalize_text))
#|    if front_non_fault_subset.ne("").any().any():
#|        raise SystemExit("non-fault/unresolved rows must keep front-facing GPVS columns blank")
#|    front_facing_series = verdict_df[front_facing_columns].fillna("").astype(str).stack()
#|    front_facing_text = "\n".join(front_facing_series.tolist())
#|    for forbidden_token in ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "IPPT", "MPPT", "제한출력 운전", "최대전력점 추종"]:
#|        if forbidden_token in front_facing_text:
#|            raise SystemExit(f"front-facing GPVS columns must not expose raw code/mode token: {forbidden_token}")
#|    if verdict_df.loc[verdict_df["패널고장여부_ko"].eq("고장"), "세부fault_부착상태_ko"].isin(["부착", "보류"]).ne(True).any():
#|        raise SystemExit("fault rows must keep 세부fault_부착상태_ko in {부착, 보류}")
#|    if verdict_df.loc[verdict_df["패널고장여부_ko"].ne("고장"), "세부fault_부착상태_ko"].ne("비대상").any():
#|        raise SystemExit("non-fault rows must keep 세부fault_부착상태_ko=비대상")
#|    if verdict_df.loc[verdict_df["세부fault_부착상태_ko"].eq("부착"), "세부fault_type_code"].map(normalize_text).eq("").any():
#|        raise SystemExit("세부fault attached rows must keep non-empty 세부fault_type_code")
#|    if verdict_df.loc[verdict_df["세부fault_부착상태_ko"].eq("부착"), "세부fault_type_label_ko"].map(normalize_text).eq("").any():
#|        raise SystemExit("세부fault attached rows must keep non-empty 세부fault_type_label_ko")
#|    if verdict_df.loc[verdict_df["세부fault_부착상태_ko"].eq("보류"), "세부fault_보류사유_ko"].map(normalize_text).eq("").any():
#|        raise SystemExit("세부fault held rows must keep non-empty 세부fault_보류사유_ko")
#|    detailed_nontarget_subset = verdict_df.loc[
#|        verdict_df["세부fault_부착상태_ko"].eq("비대상"),
#|        ["세부fault_type_code", "세부fault_type_label_ko", "세부fault_근거파일_ko", "세부fault_기준일", "세부fault_보류사유_ko"],
#|    ].copy()
#|    if not detailed_nontarget_subset.empty:
#|        detailed_nontarget_subset = detailed_nontarget_subset.apply(lambda column: column.map(normalize_text))
#|    if detailed_nontarget_subset.ne("").any().any():
#|        raise SystemExit("세부fault non-target rows must keep detailed-fault columns blank")
#|
#|    forensic_df = verdict_df.loc[
#|        verdict_df["site"].eq(FORENSIC_RULE_SITE) & verdict_df["panel_id"].eq(FORENSIC_RULE_PANEL_ID)
#|    ].copy()
#|    if len(forensic_df) != 1:
#|        raise SystemExit("forensic target panel must appear exactly once in main panel verdict table")
#|    forensic_row = forensic_df.iloc[0]
#|    if normalize_text(forensic_row["사건유형_ko"]) != FORENSIC_RULE_EVENT_TYPE:
#|        raise SystemExit(f"forensic target panel must be marked 사건유형_ko={FORENSIC_RULE_EVENT_TYPE}")
#|    if normalize_text(forensic_row["사건유형_해석_ko"]) != FORENSIC_RULE_EVENT_TYPE:
#|        raise SystemExit(f"forensic target panel must be marked 사건유형_해석_ko={FORENSIC_RULE_EVENT_TYPE}")
#|    if normalize_text(forensic_row["패널고장여부_ko"]) != "고장":
#|        raise SystemExit("forensic target panel must stay 패널고장여부_ko=고장")
#|    if normalize_text(forensic_row["최종고장양상_ko"]) != FORENSIC_RULE_TERMINAL_PATTERN:
#|        raise SystemExit(f"forensic target panel must keep 최종고장양상_ko={FORENSIC_RULE_TERMINAL_PATTERN}")
#|    if normalize_text(forensic_row["GPVS_적용대상_ko"]) != "적용대상":
#|        raise SystemExit("forensic target panel must remain GPVS applicable")
#|    if int(pd.to_numeric(forensic_row["전조흔적_flag"], errors="coerce")) != 1:
#|        raise SystemExit("forensic target panel must keep 전조흔적_flag=1")
#|    if int(pd.to_numeric(forensic_row["순수급작_flag"], errors="coerce")) != 0:
#|        raise SystemExit("forensic target panel must keep 순수급작_flag=0")
#|    if int(pd.to_numeric(forensic_row["전조평가셋편입_flag"], errors="coerce")) != 1:
#|        raise SystemExit("forensic target panel must keep 전조평가셋편입_flag=1")
#|    if int(pd.to_numeric(forensic_row["급작평가셋편입_flag"], errors="coerce")) != 0:
#|        raise SystemExit("forensic target panel must keep 급작평가셋편입_flag=0")
#|    if normalize_text(forensic_row["해석대평가차이_ko"]) != "":
#|        raise SystemExit("forensic target panel should not expose interpretation/evaluation mismatch text after benchmark sync")
#|    if FORENSIC_RULE_ONSET_DATE not in normalize_text(forensic_row["판정주의_ko"]) or FORENSIC_RULE_TRIGGER_DATE not in normalize_text(forensic_row["판정주의_ko"]):
#|        raise SystemExit("forensic target panel note must mention onset/trigger dates")
#|    if normalize_text(forensic_row["GPVS_세부fault_code"]) != "F2M":
#|        raise SystemExit("forensic target panel must keep GPVS_세부fault_code=F2M after recovered-artifact attachment")
#|    if normalize_text(forensic_row["GPVS_세부fault_부착상태_ko"]) != "부착":
#|        raise SystemExit("forensic target panel must keep GPVS_세부fault_부착상태_ko=부착")
#|    if normalize_text(forensic_row["GPVS_시나리오_family_ko"]) != "제어·계측 이상":
#|        raise SystemExit("forensic target panel must expose GPVS_시나리오_family_ko=제어·계측 이상")
#|    if normalize_text(forensic_row["GPVS_시나리오명_ko"]) != "제어 피드백 센서 이상 시나리오":
#|        raise SystemExit("forensic target panel must expose F2M scenario name")
#|    if normalize_text(forensic_row["GPVS_운전모드_ko"]) != "최대전력점 추종 운전(MPPT)":
#|        raise SystemExit("forensic target panel must expose F2M mode=MPPT")
#|    if normalize_text(forensic_row["GPVS_해석주의_ko"]) != GPVS_SCENARIO_WARNING:
#|        raise SystemExit("forensic target panel must keep GPVS scenario warning text")
#|    if normalize_text(forensic_row["GPVS_내부참고유형_ko"]) != normalize_text(forensic_row["GPVS_참고유형_ko"]):
#|        raise SystemExit("forensic target panel must surface internal GPVS interpretation in GPVS_내부참고유형_ko")
#|    if normalize_text(forensic_row["GPVS_외부참조패턴_ko"]) != "장치 응답 이상형":
#|        raise SystemExit("forensic target panel must expose GPVS_외부참조패턴_ko=장치 응답 이상형")
#|    if normalize_text(forensic_row["GPVS_참조사용등급_ko"]) != "비권장":
#|        raise SystemExit("forensic target panel must expose GPVS_참조사용등급_ko=비권장")
#|    if "센서/피드백 오류로 장치 응답이 어긋나는 패턴" not in normalize_text(forensic_row["GPVS_참조설명_ko"]):
#|        raise SystemExit("forensic target panel must expose human-readable GPVS reference description for F2")
#|
#|    special_10305_df = verdict_df.loc[
#|        verdict_df["site"].eq("ktc_ess") & verdict_df["panel_id"].eq("10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12")
#|    ].copy()
#|    if len(special_10305_df) > 1:
#|        raise SystemExit("10305 real fault panel must appear at most once in main panel verdict table")
#|    if len(special_10305_df) == 1:
#|        special_10305_row = special_10305_df.iloc[0]
#|        if normalize_text(special_10305_row["GPVS_참고유형_ko"]) != "불확실":
#|            raise SystemExit("10305 row must keep GPVS_참고유형_ko=불확실")
#|        if normalize_text(special_10305_row["GPVS_세부fault_code"]) != "F4L":
#|            raise SystemExit("10305 row must keep GPVS_세부fault_code=F4L")
#|        if normalize_text(special_10305_row["GPVS_시나리오_family_ko"]) != "PV 어레이 이상":
#|            raise SystemExit("10305 row must expose GPVS_시나리오_family_ko=PV 어레이 이상")
#|        if normalize_text(special_10305_row["GPVS_시나리오명_ko"]) != "PV 어레이 mismatch(부분 음영) 시나리오":
#|            raise SystemExit("10305 row must expose F4L scenario name")
#|        if normalize_text(special_10305_row["GPVS_운전모드_ko"]) != "제한출력 운전(IPPT)":
#|            raise SystemExit("10305 row must expose F4L mode=IPPT")
#|        if normalize_text(special_10305_row["GPVS_내부참고유형_ko"]) != "불확실":
#|            raise SystemExit("10305 row must surface GPVS_내부참고유형_ko=불확실")
#|        if normalize_text(special_10305_row["GPVS_외부참조패턴_ko"]) != "국소 출력 불균형형":
#|            raise SystemExit("10305 row must expose GPVS_외부참조패턴_ko=국소 출력 불균형형")
#|        if normalize_text(special_10305_row["GPVS_참조사용등급_ko"]) != "주의참고":
#|            raise SystemExit("10305 row must expose GPVS_참조사용등급_ko=주의참고")
#|        if "일부 패널의 출력 균형이 깨지는 패턴" not in normalize_text(special_10305_row["GPVS_참조설명_ko"]):
#|            raise SystemExit("10305 row must expose human-readable GPVS reference description for F4")
#|
#|    overlap_rows = verdict_df.loc[
#|        verdict_df["전조평가셋편입_flag"].pipe(to_numeric_flag).eq(1)
#|        & verdict_df["사건유형_ko"].eq("전조형 고장")
#|        & verdict_df["최종고장양상_ko"].eq("진행성 악화")
#|    ].copy()
#|    if len(overlap_rows) != metrics["same_event_overlap_expected"]:
#|        raise SystemExit(
#|            f"same-event overlap rows must stay {metrics['same_event_overlap_expected']}, found {len(overlap_rows)}"
#|        )
#|    if overlap_rows["사건유형_ko"].map(normalize_text).ne("전조형 고장").any():
#|        raise SystemExit("same-event overlap rows must keep 사건유형_ko=전조형 고장")
#|    if overlap_rows["사건유형_해석_ko"].map(normalize_text).ne("전조형 고장").any():
#|        raise SystemExit("same-event overlap rows must keep 사건유형_해석_ko=전조형 고장")
#|    if overlap_rows["최종고장양상_ko"].map(normalize_text).ne("진행성 악화").any():
#|        raise SystemExit("same-event overlap rows must keep 최종고장양상_ko=진행성 악화 after corrected rule sync")
#|    if to_numeric_flag(overlap_rows["전조흔적_flag"]).ne(1).any():
#|        raise SystemExit("same-event overlap rows must keep 전조흔적_flag=1")
#|    if to_numeric_flag(overlap_rows["순수급작_flag"]).ne(0).any():
#|        raise SystemExit("same-event overlap rows must keep 순수급작_flag=0")
#|    if to_numeric_flag(overlap_rows["전조평가셋편입_flag"]).ne(1).any():
#|        raise SystemExit("same-event overlap rows must keep 전조평가셋편입_flag=1")
#|    if to_numeric_flag(overlap_rows["급작평가셋편입_flag"]).ne(0).any():
#|        raise SystemExit("same-event overlap rows must keep 급작평가셋편입_flag=0")
#|
#|    if metrics["workflow_cluster_count"] > 0 and len(cluster_supplement_df) <= 0:
#|        raise SystemExit("cluster supplement check failed: workflow has discovery clusters but supplement is empty")
#|    if cluster_supplement_df["GPVS_참고유형_ko"].ne("미부착").any():
#|        raise SystemExit("cluster supplement must stay GPVS_참고유형_ko=미부착")
#|    if cluster_supplement_df["GPVS_근거_ko"].ne(GPVS_ABSENCE_REASON).any():
#|        raise SystemExit(f"cluster supplement must stay GPVS_근거_ko={GPVS_ABSENCE_REASON}")
#|
#|    insufficient_rows = verdict_df.loc[
#|        verdict_df["사건유형_ko"].eq("불충분"),
#|        ["site", "panel_id", "전조형이력_flag", "급작고장이력_flag", "공통원인이력_flag", "반복이상이력_flag"],
#|    ]
#|    for row in insufficient_rows.to_dict(orient="records"):
#|        if any(int(row[column]) == 1 for column in ["전조형이력_flag", "급작고장이력_flag", "공통원인이력_flag", "반복이상이력_flag"]):
#|            raise SystemExit(f"insufficient representative row violates membership guardrail: {row}")
#|
#|    if event_supplement_df.empty and (interpreted_abrupt_membership + interpreted_precursor_membership + common_membership) > 0:
#|        raise SystemExit("event supplement is empty despite event memberships in the main panel table")
#|
#|
#|def build_summary(
#|    verdict_df: pd.DataFrame,
#|    event_supplement_df: pd.DataFrame,
#|    cluster_supplement_df: pd.DataFrame,
#|    metrics: dict[str, int],
#|    gpvs_feasibility_meta: dict[str, str],
#|) -> pd.DataFrame:
#|    counts = compute_final_row_counts(verdict_df)
#|    symptom_attached = int(verdict_df["커널로그_증상명_ko"].ne("불충분").sum())
#|    cause_group_attached = int(verdict_df["커널로그_원인군_ko"].ne("불충분").sum())
#|    gpvs_applicable = int(verdict_df["GPVS_적용대상_ko"].eq("적용대상").sum())
#|    gpvs_attached = int(verdict_df["GPVS_부착상태_ko"].eq("부착").sum())
#|    gpvs_unattached = int(verdict_df["GPVS_부착상태_ko"].eq("미부착").sum())
#|    gpvs_non_target = int(verdict_df["GPVS_부착상태_ko"].eq("비대상").sum())
#|    gpvs_detailed_attached = int(verdict_df["GPVS_세부fault_부착상태_ko"].eq("부착").sum())
#|    gpvs_detailed_deferred = int(verdict_df["GPVS_세부fault_부착상태_ko"].eq("판정유보").sum())
#|    gpvs_detailed_nontarget = int(verdict_df["GPVS_세부fault_부착상태_ko"].eq("비대상").sum())
#|    gpvs_detailed_f2m = int(verdict_df["GPVS_세부fault_code"].eq("F2M").sum())
#|    gpvs_detailed_f4l = int(verdict_df["GPVS_세부fault_code"].eq("F4L").sum())
#|    detailed_fault_attached = int(verdict_df["세부fault_부착상태_ko"].eq("부착").sum())
#|    detailed_fault_held = int(verdict_df["세부fault_부착상태_ko"].eq("보류").sum())
#|    detailed_fault_non_target = int(verdict_df["세부fault_부착상태_ko"].eq("비대상").sum())
#|    gpvs_reason_counts = (
#|        verdict_df.loc[verdict_df["GPVS_부착상태_ko"].eq("미부착"), "GPVS_미부착사유_ko"].value_counts().to_dict()
#|    )
#|    best_source = normalize_text(gpvs_feasibility_meta.get("best_source", ""))
#|    if gpvs_unattached > 0:
#|        gpvs_note = (
#|            f"GPVS는 reference axis로만 붙이고, 현재 final row 기준 적용대상 fault panel {gpvs_applicable}개 중 {gpvs_attached}개에만 부분 부착했다."
#|        )
#|    else:
#|        gpvs_note = (
#|            f"GPVS는 reference axis로만 붙이고, 현재 final row 기준 적용대상 fault panel {gpvs_applicable}개에는 모두 부착했다."
#|        )
#|    if best_source:
#|        gpvs_note += f" 최선 후보 파일은 {best_source} 다."
#|    gpvs_note += " 다만 GPVS는 현재 fault-family reference axis 이므로 고장 패널에만 적용하고, 비고장/반복/불충분 panel은 비대상으로 둔다."
#|
#|    row = {
#|        **counts,
#|        "커널로그_증상명_부착수": symptom_attached,
#|        "커널로그_원인군_부착수": cause_group_attached,
#|        "GPVS_적용대상_패널수": gpvs_applicable,
#|        "GPVS_부착수": gpvs_attached,
#|        "GPVS_미부착수": gpvs_unattached,
#|        "GPVS_비대상수": gpvs_non_target,
#|        "GPVS_미부착_패널key없음수": int(gpvs_reason_counts.get("GPVS 패널수준 후보 파일은 있으나 이 패널 key가 없음", 0)),
#|        "GPVS_미부착_key부족수": int(gpvs_reason_counts.get("GPVS 결과는 있으나 패널수준 key가 없음", 0)),
#|        "GPVS_미부착_산출물없음수": int(gpvs_reason_counts.get("패널수준 GPVS 산출물 없음", 0)),
#|        "GPVS_세부fault_부착수": gpvs_detailed_attached,
#|        "GPVS_세부fault_판정유보수": gpvs_detailed_deferred,
#|        "GPVS_세부fault_추론불가수": 0,
#|        "GPVS_세부fault_부착패널수": gpvs_detailed_attached,
#|        "GPVS_세부fault_판정유보패널수": gpvs_detailed_deferred,
#|        "GPVS_세부fault_비대상패널수": gpvs_detailed_nontarget,
#|        "GPVS_세부fault_F2M_패널수": gpvs_detailed_f2m,
#|        "GPVS_세부fault_F4L_패널수": gpvs_detailed_f4l,
#|        "사건보조행수": int(len(event_supplement_df)),
#|        "클러스터_보조행수": int(len(cluster_supplement_df)),
#|        "note_ko": (
#|            f"main panel table은 unique panel 대표 verdict 표이고 workflow panel {metrics['workflow_panel_count']}건을 기준으로 fault6 rows {metrics['abrupt_fault6_total']}건, 사건 해석상 전조형 3건, 사건 해석상 급작 3건, 엄격 전조 평가셋 3건, 순수 급작 평가셋 3건을 분리해서 적는다. "
#|            f"fault panel event audit {metrics['fault_audit_expected']}건을 authoritative fault-event source로 읽어 사건유형/최종고장양상/순수급작 flag를 동기화했다. "
#|            f"same-event overlap {metrics['same_event_overlap_expected']}건은 전조형 고장으로 읽고, c42997 row 는 전조형 고장/급격 종료로 읽으며 엄격 전조 평가셋에는 포함하고 순수 급작 평가셋에서는 제외한다. "
#|            f"single-panel forensic explicit rule {metrics['forensic_rule_expected']}건은 c42997 row 설명 근거로 유지하고, same-day fallback onset abrupt row 는 급작 고장으로 다시 허용한다. "
#|            "이제 전조평가셋편입_flag 는 precursor onset truth membership으로, 급작평가셋편입_flag 는 non-precursor abrupt performance case membership으로 다시 계산한다. "
#|            "사건유형_해석_ko 와 평가셋 편입 flag를 분리해, 사건 해석과 evaluation-set inclusion을 같은 뜻으로 읽지 않게 한다. "
#|            "또한 운영상 최초 전조 발견일, 사건 해석상 전조 시작일, benchmark 전조 시작일을 분리해 onset date 의미를 섞지 않게 한다. "
#|            "event type과 terminal failure pattern은 분리해서 읽는다. "
#|            f"GPVS 세부 fault는 learned GPVS by-type inference 결과를 recovered GPVS by-type artifact parity 일치 이후 real panel event date에 다시 적용해 현재 부착 {gpvs_detailed_attached}건 / 판정유보 {gpvs_detailed_deferred}건 / 비대상 {gpvs_detailed_nontarget}건이다. "
#|            f"현재 code 분포는 F2M {gpvs_detailed_f2m}건, F4L {gpvs_detailed_f4l}건이다. "
#|            "GPVS family label 과 GPVS detailed fault code 는 별도 축이며, family 불확실이더라도 recovered by-type inference attach guard를 통과하면 detailed type은 부착할 수 있다. "
#|            "GPVS detailed fault code는 외부 GPVS 실험 시나리오 참조축이므로 F2M/F4L을 실제 패널 물리 root cause 이름으로 직접 번역하면 안 된다. "
#|            "공식 detailed-fault attachment source 는 recovered GPVS by-type inference 이고, 과거 PVFAULT exact-date bridge 경로는 audit-only 실패 경로로 retire 했다. "
#|            "이 세부 fault 축은 GPVS family reference 와 별개로 읽는다. "
#|            f"사건이력 보조표는 panel이 여러 사건군에 속하거나 전조형 고장이 급격 종료로 끝난 경우를 함께 남긴다. {gpvs_note} unmatched panel은 row-by-row 미부착 사유를 함께 남긴다."
#|        ),
#|    }
#|    return pd.DataFrame([row]).reindex(columns=SUMMARY_COLS)
#|
#|
#|def write_outputs(
#|    root: Path,
#|    verdict_df: pd.DataFrame,
#|    event_supplement_df: pd.DataFrame,
#|    cluster_supplement_df: pd.DataFrame,
#|    summary_df: pd.DataFrame,
#|) -> None:
#|    share_dir = root / "_share"
#|    share_dir.mkdir(parents=True, exist_ok=True)
#|    verdict_df.to_csv(share_dir / VERDICT_OUTPUT_NAME, index=False, encoding="utf-8-sig")
#|    event_supplement_df.to_csv(share_dir / EVENT_SUPPLEMENT_OUTPUT_NAME, index=False, encoding="utf-8-sig")
#|    cluster_supplement_df.to_csv(share_dir / CLUSTER_SUPPLEMENT_OUTPUT_NAME, index=False, encoding="utf-8-sig")
#|    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
#|
#|
#|def main() -> None:
#|    args = parse_args()
#|    root = args.root.resolve()
#|    frames = load_inputs(root)
#|    validate_inputs(root, frames)
#|    verdict_df, verdict_internal_df, event_supplement_df, cluster_supplement_df, metrics, gpvs_feasibility_meta = build_outputs(root, frames)
#|    validate_real_coverage(verdict_internal_df, event_supplement_df, cluster_supplement_df, metrics)
#|    summary_df = build_summary(verdict_internal_df, event_supplement_df, cluster_supplement_df, metrics, gpvs_feasibility_meta)
#|    write_outputs(root, verdict_df, event_supplement_df, cluster_supplement_df, summary_df)
#|
#|
#|if __name__ == "__main__":
#|    main()
# pvdiag_payload_end
# endregion
# region payload: raw_only_audit_builder
# pvdiag_payload_file {"bytes": 11148, "endswith_newline": true, "lines": 237, "path": "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py", "role": "raw_only_audit_builder", "sha256": "9db0559f8232ade4a74ac673da7d189ae64e64d472376beace717ba1487a17de"}
#|#!/usr/bin/env python3
#|from __future__ import annotations
#|
#|import argparse
#|import sys
#|from pathlib import Path
#|
#|import pandas as pd
#|
#|
#|REPO_ROOT = Path(__file__).resolve().parents[2]
#|if str(REPO_ROOT) not in sys.path:
#|    sys.path.insert(0, str(REPO_ROOT))
#|
#|from research.prognostics import runtime_rawonly_chain_common_v1 as common
#|
#|
#|AUDIT_COLS = [
#|    "site",
#|    "panel_id",
#|    "현재표_사건유형_ko",
#|    "현재표_최종고장양상_ko",
#|    "earliest_warning_date",
#|    "retrospective_onset_date",
#|    "strict_trigger_date",
#|    "first_final_fault_date",
#|    "dead_diag_date",
#|    "onset_confidence",
#|    "onset_method",
#|    "전조흔적_flag",
#|    "순수급작_flag",
#|    "전조평가셋편입_flag",
#|    "급작평가셋편입_flag",
#|    "사건유형_재판정_ko",
#|    "최종고장양상_재판정_ko",
#|    "재판정_근거_ko",
#|    "현재표_보정필요여부_flag",
#|    "패널고장여부_ko",
#|    "대표critical_source",
#|    "대표anom_level",
#|    "대표anom_subtype",
#|    "algorithm_family_ko",
#|    "algorithm_symptom_ko",
#|    "detailed_fault_code",
#|    "detailed_fault_label_ko",
#|    "gap_days",
#|    "degradation_onset_backdate_guard_flag",
#|    "degradation_onset_backdate_guard_name",
#|    "degradation_onset_backdate_guard_reason",
#|    "degradation_onset_backdate_guard_degrade_days",
#|    "secondary_window_candidate_flag",
#|    "secondary_window_selected_onset_date",
#|    "secondary_window_selected_marker",
#|    "secondary_window_selected_gap_days",
#|    "secondary_window_qualified_count",
#|    "secondary_window_too_early_count",
#|    "secondary_window_change_class",
#|    "secondary_window_review_tier",
#|    "secondary_window_reason",
#|    "common_cause_anchor_date",
#|    "common_cause_anchor_kind",
#|    "site_event_history_flag",
#|    "subgroup_common_cause_history_flag",
#|    "common_cause_history_flag",
#|    "strict_trigger_proximal_common_cause_flag",
#|    "warning_proximal_common_cause_flag",
#|    "trigger_proximal_common_cause_flag",
#|]
#|SUMMARY_COLS = [
#|    "전체_패널수",
#|    "고장_패널수",
#|    "비고장_패널수",
#|    "미확정_패널수",
#|    "전조형_고장수",
#|    "급작_고장수",
#|    "전조평가셋_패널수",
#|    "급작평가셋_패널수",
#|    "algorithm_family_다이오드형_패널수",
#|    "algorithm_family_개방장치이상형_패널수",
#|    "algorithm_family_모듈손상형_패널수",
#|    "algorithm_family_불충분_패널수",
#|    "secondary_window_candidate_패널수",
#|    "secondary_window_trigger_only_to_precursor_패널수",
#|    "secondary_window_review_required_패널수",
#|    "note_ko",
#|]
#|
#|
#|def parse_args() -> argparse.Namespace:
#|    parser = argparse.ArgumentParser(
#|        description=(
#|            "Build a raw-only runtime fault-event audit from panel_day_core and "
#|            "ae_simple_local_precursor_gate_daily without frozen truth/support assets."
#|        )
#|    )
#|    parser.add_argument(
#|        "--root",
#|        type=Path,
#|        default=REPO_ROOT,
#|        help="Workspace root containing data/<site>/out.",
#|    )
#|    return parser.parse_args()
#|
#|
#|def build_rows(root: Path) -> pd.DataFrame:
#|    rows: list[dict[str, object]] = []
#|    for site in common.discover_sites(root):
#|        core_df, gate_df = common.load_site_outputs(root, site)
#|        for panel_id in common.panel_keys(core_df, gate_df):
#|            metrics = common.compute_panel_metrics(site, panel_id, core_df, gate_df)
#|            rows.append(
#|                {
#|                    "site": metrics.site,
#|                    "panel_id": metrics.panel_id,
#|                    "현재표_사건유형_ko": metrics.사건유형_재판정_ko,
#|                    "현재표_최종고장양상_ko": metrics.최종고장양상_재판정_ko,
#|                    "earliest_warning_date": metrics.earliest_warning_date,
#|                    "retrospective_onset_date": metrics.retrospective_onset_date,
#|                    "strict_trigger_date": metrics.strict_trigger_date,
#|                    "first_final_fault_date": metrics.first_final_fault_date,
#|                    "dead_diag_date": metrics.dead_diag_date,
#|                    "onset_confidence": metrics.onset_confidence,
#|                    "onset_method": metrics.onset_method,
#|                    "전조흔적_flag": metrics.전조흔적_flag,
#|                    "순수급작_flag": metrics.순수급작_flag,
#|                    "전조평가셋편입_flag": metrics.전조평가셋편입_flag,
#|                    "급작평가셋편입_flag": metrics.급작평가셋편입_flag,
#|                    "사건유형_재판정_ko": metrics.사건유형_재판정_ko,
#|                    "최종고장양상_재판정_ko": metrics.최종고장양상_재판정_ko,
#|                    "재판정_근거_ko": metrics.재판정_근거_ko,
#|                    "현재표_보정필요여부_flag": metrics.현재표_보정필요여부_flag,
#|                    "패널고장여부_ko": metrics.패널고장여부_ko,
#|                    "대표critical_source": metrics.대표critical_source,
#|                    "대표anom_level": metrics.대표anom_level,
#|                    "대표anom_subtype": metrics.대표anom_subtype,
#|                    "algorithm_family_ko": metrics.algorithm_family_ko,
#|                    "algorithm_symptom_ko": metrics.algorithm_symptom_ko,
#|                    "detailed_fault_code": metrics.detailed_fault_code,
#|                    "detailed_fault_label_ko": metrics.detailed_fault_label_ko,
#|                    "gap_days": metrics.gap_days,
#|                    "degradation_onset_backdate_guard_flag": int(
#|                        metrics.degradation_onset_backdate_guard_flag
#|                    ),
#|                    "degradation_onset_backdate_guard_name": (
#|                        metrics.degradation_onset_backdate_guard_name
#|                    ),
#|                    "degradation_onset_backdate_guard_reason": (
#|                        metrics.degradation_onset_backdate_guard_reason
#|                    ),
#|                    "degradation_onset_backdate_guard_degrade_days": (
#|                        metrics.degradation_onset_backdate_guard_degrade_days
#|                    ),
#|                    "secondary_window_candidate_flag": int(metrics.secondary_window_candidate_flag),
#|                    "secondary_window_selected_onset_date": (
#|                        metrics.secondary_window_selected_onset_date
#|                    ),
#|                    "secondary_window_selected_marker": metrics.secondary_window_selected_marker,
#|                    "secondary_window_selected_gap_days": metrics.secondary_window_selected_gap_days,
#|                    "secondary_window_qualified_count": metrics.secondary_window_qualified_count,
#|                    "secondary_window_too_early_count": metrics.secondary_window_too_early_count,
#|                    "secondary_window_change_class": metrics.secondary_window_change_class,
#|                    "secondary_window_review_tier": metrics.secondary_window_review_tier,
#|                    "secondary_window_reason": metrics.secondary_window_reason,
#|                    "common_cause_anchor_date": metrics.common_cause_anchor_date,
#|                    "common_cause_anchor_kind": metrics.common_cause_anchor_kind,
#|                    "site_event_history_flag": int(metrics.has_site_event),
#|                    "subgroup_common_cause_history_flag": int(metrics.has_subgroup_common_cause),
#|                    "common_cause_history_flag": int(metrics.has_common_cause_history),
#|                    "strict_trigger_proximal_common_cause_flag": int(
#|                        metrics.has_strict_trigger_proximal_common_cause
#|                    ),
#|                    "warning_proximal_common_cause_flag": int(
#|                        metrics.has_warning_proximal_common_cause
#|                    ),
#|                    "trigger_proximal_common_cause_flag": int(metrics.has_trigger_proximal_common_cause),
#|                }
#|            )
#|    if not rows:
#|        raise SystemExit("runtime fault-event audit must not be empty")
#|    return pd.DataFrame(rows).reindex(columns=AUDIT_COLS).sort_values(["site", "panel_id"]).reset_index(drop=True)
#|
#|
#|def build_summary(df: pd.DataFrame) -> pd.DataFrame:
#|    row = {
#|        "전체_패널수": int(len(df)),
#|        "고장_패널수": int(df["패널고장여부_ko"].map(common.normalize_text).eq("고장").sum()),
#|        "비고장_패널수": int(df["패널고장여부_ko"].map(common.normalize_text).eq("비고장").sum()),
#|        "미확정_패널수": int(df["패널고장여부_ko"].map(common.normalize_text).eq("미확정").sum()),
#|        "전조형_고장수": int(df["사건유형_재판정_ko"].map(common.normalize_text).eq("전조형 고장").sum()),
#|        "급작_고장수": int(df["사건유형_재판정_ko"].map(common.normalize_text).eq("급작 고장").sum()),
#|        "전조평가셋_패널수": int(pd.to_numeric(df["전조평가셋편입_flag"], errors="coerce").fillna(0).sum()),
#|        "급작평가셋_패널수": int(pd.to_numeric(df["급작평가셋편입_flag"], errors="coerce").fillna(0).sum()),
#|        "algorithm_family_다이오드형_패널수": int(df["algorithm_family_ko"].map(common.normalize_text).eq("다이오드형").sum()),
#|        "algorithm_family_개방장치이상형_패널수": int(df["algorithm_family_ko"].map(common.normalize_text).eq("개방/장치이상형").sum()),
#|        "algorithm_family_모듈손상형_패널수": int(df["algorithm_family_ko"].map(common.normalize_text).eq("모듈손상형").sum()),
#|        "algorithm_family_불충분_패널수": int(df["algorithm_family_ko"].map(common.normalize_text).eq("불충분").sum()),
#|        "secondary_window_candidate_패널수": int(
#|            pd.to_numeric(df["secondary_window_candidate_flag"], errors="coerce").fillna(0).sum()
#|        ),
#|        "secondary_window_trigger_only_to_precursor_패널수": int(
#|            df["secondary_window_change_class"]
#|            .map(common.normalize_text)
#|            .eq("trigger_only_to_precursor")
#|            .sum()
#|        ),
#|        "secondary_window_review_required_패널수": int(
#|            df["secondary_window_review_tier"]
#|            .map(common.normalize_text)
#|            .str.startswith("review_")
#|            .sum()
#|        ),
#|        "note_ko": (
#|            "이 runtime audit는 raw-only 경로다. panel_day_core와 precursor gate만 사용하며, "
#|            "수동 truth/adjudication/frozen audit snapshot은 참조하지 않는다."
#|        ),
#|    }
#|    return pd.DataFrame([row]).reindex(columns=SUMMARY_COLS)
#|
#|
#|def main() -> None:
#|    args = parse_args()
#|    root = args.root.resolve()
#|    share_dir = root / "_share"
#|    share_dir.mkdir(parents=True, exist_ok=True)
#|
#|    audit_df = build_rows(root)
#|    summary_df = build_summary(audit_df)
#|
#|    audit_path = share_dir / common.RUNTIME_AUDIT_OUTPUT_NAME
#|    summary_path = share_dir / common.RUNTIME_AUDIT_SUMMARY_NAME
#|    audit_df.to_csv(audit_path, index=False, encoding="utf-8-sig")
#|    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
#|    print(f"[OK] wrote runtime raw-only audit: {audit_path}")
#|
#|
#|if __name__ == "__main__":
#|    main()
# pvdiag_payload_end
# endregion
# region payload: raw_only_verdict_builder
# pvdiag_payload_file {"bytes": 8601, "endswith_newline": true, "lines": 191, "path": "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_final_verdict_v1.py", "role": "raw_only_verdict_builder", "sha256": "d23f1a31463f8367d09d23d1c6973d67448b966e89a30f3785e7403ed7dcaccb"}
#|#!/usr/bin/env python3
#|from __future__ import annotations
#|
#|import argparse
#|import sys
#|from pathlib import Path
#|
#|import pandas as pd
#|
#|
#|REPO_ROOT = Path(__file__).resolve().parents[2]
#|if str(REPO_ROOT) not in sys.path:
#|    sys.path.insert(0, str(REPO_ROOT))
#|
#|from research.prognostics import runtime_rawonly_chain_common_v1 as common
#|
#|
#|VERDICT_COLS = [
#|    "site",
#|    "panel_id",
#|    "사건유형_ko",
#|    "사건유형_해석_ko",
#|    "최종고장양상_ko",
#|    "대표판정_ko",
#|    "사건이력_ko",
#|    "전조흔적_flag",
#|    "순수급작_flag",
#|    "전조평가셋편입_flag",
#|    "급작평가셋편입_flag",
#|    "해석대평가차이_ko",
#|    "운영최초전조발견일",
#|    "운영최초전조마커",
#|    "사건해석상전조시작일",
#|    "benchmark전조시작일",
#|    "전조형이력_flag",
#|    "급작고장이력_flag",
#|    "공통원인이력_flag",
#|    "반복이상이력_flag",
#|    "패널고장여부_ko",
#|    "GPVS_적용대상_ko",
#|    "커널로그_증상명_ko",
#|    "커널로그_원인군_ko",
#|    "GPVS_부착상태_ko",
#|    "GPVS_내부참고유형_ko",
#|    "GPVS_외부참조패턴_ko",
#|    "GPVS_참조사용등급_ko",
#|    "GPVS_참조설명_ko",
#|    "세부fault_type_code",
#|    "세부fault_type_label_ko",
#|    "세부fault_부착상태_ko",
#|    "세부fault_근거파일_ko",
#|    "세부fault_기준일",
#|    "세부fault_보류사유_ko",
#|    "운영위치_ko",
#|    "판정주의_ko",
#|]
#|SUMMARY_COLS = [
#|    "전체_패널수",
#|    "고장_패널수",
#|    "비고장_패널수",
#|    "미확정_패널수",
#|    "전조형_고장수",
#|    "급작_고장수",
#|    "커널로그_원인군_다이오드형_패널수",
#|    "커널로그_원인군_개방장치이상형_패널수",
#|    "커널로그_원인군_모듈손상형_패널수",
#|    "커널로그_원인군_불충분_패널수",
#|    "note_ko",
#|]
#|
#|
#|def parse_args() -> argparse.Namespace:
#|    parser = argparse.ArgumentParser(
#|        description=(
#|            "Build a raw-only runtime final verdict. Column names are preserved where practical, "
#|            "but 커널로그_원인군_ko is algorithm-derived from panel_day_core/gate."
#|        )
#|    )
#|    parser.add_argument(
#|        "--root",
#|        type=Path,
#|        default=REPO_ROOT,
#|        help="Workspace root containing _share runtime audit and data/<site>/out.",
#|    )
#|    return parser.parse_args()
#|
#|
#|def build_rows(audit_df: pd.DataFrame) -> pd.DataFrame:
#|    rows: list[dict[str, object]] = []
#|    for row in audit_df.to_dict(orient="records"):
#|        status = common.normalize_text(row.get("패널고장여부_ko"))
#|        event_type = common.normalize_text(row.get("사건유형_재판정_ko"))
#|        terminal = common.normalize_text(row.get("최종고장양상_재판정_ko"))
#|        family = common.normalize_text(row.get("algorithm_family_ko"))
#|        if status == "고장":
#|            representative = event_type or "고장"
#|            event_history = event_type or "고장"
#|        elif status == "미확정":
#|            representative = "미확정"
#|            event_history = "반복 이상"
#|        else:
#|            representative = "비고장"
#|            event_history = "비고장"
#|        rows.append(
#|            {
#|                "site": common.normalize_text(row.get("site")),
#|                "panel_id": common.normalize_text(row.get("panel_id")),
#|                "사건유형_ko": event_type,
#|                "사건유형_해석_ko": event_type,
#|                "최종고장양상_ko": terminal,
#|                "대표판정_ko": representative,
#|                "사건이력_ko": event_history,
#|                "전조흔적_flag": int(row.get("전조흔적_flag") or 0),
#|                "순수급작_flag": int(row.get("순수급작_flag") or 0),
#|                "전조평가셋편입_flag": int(row.get("전조평가셋편입_flag") or 0),
#|                "급작평가셋편입_flag": int(row.get("급작평가셋편입_flag") or 0),
#|                "해석대평가차이_ko": "",
#|                "운영최초전조발견일": common.normalize_text(row.get("earliest_warning_date")),
#|                "운영최초전조마커": common.normalize_text(row.get("onset_method")),
#|                "사건해석상전조시작일": common.normalize_text(row.get("retrospective_onset_date")),
#|                "benchmark전조시작일": "",
#|                "전조형이력_flag": int(event_type == "전조형 고장"),
#|                "급작고장이력_flag": int(event_type == "급작 고장"),
#|                "공통원인이력_flag": int(row.get("common_cause_history_flag") or 0),
#|                "반복이상이력_flag": int(status == "미확정"),
#|                "패널고장여부_ko": status,
#|                "GPVS_적용대상_ko": "raw-only 미사용",
#|                "커널로그_증상명_ko": common.normalize_text(row.get("algorithm_symptom_ko")),
#|                "커널로그_원인군_ko": family,
#|                "GPVS_부착상태_ko": "raw-only 미사용",
#|                "GPVS_내부참고유형_ko": "",
#|                "GPVS_외부참조패턴_ko": "",
#|                "GPVS_참조사용등급_ko": "",
#|                "GPVS_참조설명_ko": "raw-only strict chain에서는 GPVS reference를 사용하지 않음",
#|                "세부fault_type_code": common.normalize_text(row.get("detailed_fault_code")),
#|                "세부fault_type_label_ko": common.normalize_text(row.get("detailed_fault_label_ko")),
#|                "세부fault_부착상태_ko": "algorithm-derived" if family else "",
#|                "세부fault_근거파일_ko": "panel_day_core.csv + ae_simple_local_precursor_gate_daily.csv" if family else "",
#|                "세부fault_기준일": common.normalize_text(row.get("strict_trigger_date")) or common.normalize_text(row.get("first_final_fault_date")),
#|                "세부fault_보류사유_ko": "" if family and family != "불충분" else "raw-only family confidence limited",
#|                "운영위치_ko": "raw-only runtime",
#|                "판정주의_ko": (
#|                    "커널로그_원인군_ko 컬럼명은 유지하지만, 의미는 raw-only algorithm-derived family로 해석해야 한다. "
#|                    "수동 truth/frozen label을 참조하지 않는다."
#|                ),
#|            }
#|        )
#|    return pd.DataFrame(rows).reindex(columns=VERDICT_COLS).sort_values(["site", "panel_id"]).reset_index(drop=True)
#|
#|
#|def build_summary(df: pd.DataFrame) -> pd.DataFrame:
#|    families = df["커널로그_원인군_ko"].map(common.normalize_text)
#|    row = {
#|        "전체_패널수": int(len(df)),
#|        "고장_패널수": int(df["패널고장여부_ko"].map(common.normalize_text).eq("고장").sum()),
#|        "비고장_패널수": int(df["패널고장여부_ko"].map(common.normalize_text).eq("비고장").sum()),
#|        "미확정_패널수": int(df["패널고장여부_ko"].map(common.normalize_text).eq("미확정").sum()),
#|        "전조형_고장수": int(df["사건유형_ko"].map(common.normalize_text).eq("전조형 고장").sum()),
#|        "급작_고장수": int(df["사건유형_ko"].map(common.normalize_text).eq("급작 고장").sum()),
#|        "커널로그_원인군_다이오드형_패널수": int(families.eq("다이오드형").sum()),
#|        "커널로그_원인군_개방장치이상형_패널수": int(families.eq("개방/장치이상형").sum()),
#|        "커널로그_원인군_모듈손상형_패널수": int(families.eq("모듈손상형").sum()),
#|        "커널로그_원인군_불충분_패널수": int(families.eq("불충분").sum()),
#|        "note_ko": (
#|            "runtime final verdict는 raw-only strict chain용이다. "
#|            "커널로그_원인군_ko는 algorithm-derived family이며, 기존 frozen label field와 의미가 다를 수 있다."
#|        ),
#|    }
#|    return pd.DataFrame([row]).reindex(columns=SUMMARY_COLS)
#|
#|
#|def main() -> None:
#|    args = parse_args()
#|    root = args.root.resolve()
#|    share_dir = root / "_share"
#|    audit_path = share_dir / common.RUNTIME_AUDIT_OUTPUT_NAME
#|    audit_df = common.read_csv(audit_path)
#|    summary_dir = share_dir
#|
#|    verdict_df = build_rows(audit_df)
#|    summary_df = build_summary(verdict_df)
#|
#|    verdict_path = summary_dir / common.RUNTIME_VERDICT_OUTPUT_NAME
#|    summary_path = summary_dir / common.RUNTIME_VERDICT_SUMMARY_NAME
#|    verdict_df.to_csv(verdict_path, index=False, encoding="utf-8-sig")
#|    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
#|    print(f"[OK] wrote runtime raw-only verdict: {verdict_path}")
#|
#|
#|if __name__ == "__main__":
#|    main()
# pvdiag_payload_end
# endregion
# region payload: raw_only_heuristic_builder
# pvdiag_payload_file {"bytes": 10250, "endswith_newline": true, "lines": 286, "path": "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_heuristic_v1.py", "role": "raw_only_heuristic_builder", "sha256": "7d34a45aa9eb216a0f6e24516f83c8d4a5c225f9eddfe774ee4d991678df8103"}
#|#!/usr/bin/env python3
#|from __future__ import annotations
#|
#|import argparse
#|import sys
#|from pathlib import Path
#|
#|import pandas as pd
#|
#|
#|REPO_ROOT = Path(__file__).resolve().parents[2]
#|if str(REPO_ROOT) not in sys.path:
#|    sys.path.insert(0, str(REPO_ROOT))
#|
#|from research.prognostics import runtime_rawonly_chain_common_v1 as common
#|
#|
#|CANDIDATES = [
#|    "부분음영형",
#|    "오염형",
#|    "열화형",
#|    "다이오드·서브스트링형",
#|    "접속·부분개방형",
#|    "센서·피드백형",
#|    "제어응답형",
#|    "외부계통교란형",
#|    "전력변환부형",
#|    "원인미확정",
#|]
#|TIE_PRIORITY = {
#|    "다이오드·서브스트링형": 0,
#|    "접속·부분개방형": 1,
#|    "열화형": 2,
#|    "부분음영형": 3,
#|    "오염형": 4,
#|    "센서·피드백형": 5,
#|    "제어응답형": 6,
#|    "외부계통교란형": 7,
#|    "전력변환부형": 8,
#|    "원인미확정": 9,
#|}
#|MAIN_COLS = [
#|    "site",
#|    "panel_id",
#|    "사건유형_ko",
#|    "최종고장양상_ko",
#|    "커널로그_원인군_ko",
#|    "GPVS_내부참고유형_ko",
#|    "GPVS_외부참조패턴_ko",
#|    "원인후보_top1_ko",
#|    "원인후보_top1_score",
#|    "원인후보_top2_ko",
#|    "원인후보_top2_score",
#|    "원인후보_top3_ko",
#|    "원인후보_top3_score",
#|    "원인후보_경합상태_ko",
#|    "원인후보_공동상위후보_csv",
#|    "원인후보_실증우선확인_ko",
#|    "원인후보_신뢰도_ko",
#|    "원인후보_해석메모_ko",
#|]
#|SUMMARY_COLS = [
#|    "fault_panel_count",
#|    "top1_다이오드서브스트링형_count",
#|    "top1_접속부분개방형_count",
#|    "top1_열화형_count",
#|    "top1_부분음영형_count",
#|    "top1_센서피드백형_count",
#|    "top1_원인미확정_count",
#|    "note_ko",
#|]
#|
#|FAMILY_BASE_RULES = {
#|    "다이오드형": {
#|        "다이오드·서브스트링형": 5,
#|        "접속·부분개방형": 2,
#|        "부분음영형": 1,
#|    },
#|    "개방/장치이상형": {
#|        "센서·피드백형": 4,
#|        "접속·부분개방형": 3,
#|        "제어응답형": 2,
#|    },
#|    "모듈손상형": {
#|        "열화형": 5,
#|        "부분음영형": 2,
#|        "오염형": 2,
#|        "다이오드·서브스트링형": 1,
#|    },
#|    "불충분": {
#|        "원인미확정": 4,
#|    },
#|}
#|TEMPORAL_RULES = {
#|    ("전조형 고장", "진행성 악화"): {
#|        "열화형": 2,
#|        "오염형": 1,
#|    },
#|    ("전조형 고장", "급격 종료"): {
#|        "접속·부분개방형": 1,
#|        "다이오드·서브스트링형": 1,
#|    },
#|    ("급작 고장", "급작 발생"): {
#|        "접속·부분개방형": 1,
#|        "센서·피드백형": 1,
#|        "다이오드·서브스트링형": 1,
#|    },
#|}
#|SOURCE_RULES = {
#|    "vdrop": {"다이오드·서브스트링형": 2},
#|    "vdrop_suspect": {"다이오드·서브스트링형": 1},
#|    "legacy": {"접속·부분개방형": 2},
#|    "none": {"센서·피드백형": 1},
#|}
#|SUBTYPE_RULES = {
#|    "degradation": {"열화형": 2, "오염형": 1},
#|    "shadow": {"부분음영형": 2},
#|    "critical_fault_vdrop": {"다이오드·서브스트링형": 2},
#|    "confirmed_fault": {"다이오드·서브스트링형": 1},
#|}
#|
#|
#|def parse_args() -> argparse.Namespace:
#|    parser = argparse.ArgumentParser(
#|        description="Build a raw-only runtime cause-candidate heuristic from runtime final verdict."
#|    )
#|    parser.add_argument(
#|        "--root",
#|        type=Path,
#|        default=REPO_ROOT,
#|        help="Workspace root containing runtime verdict and audit outputs.",
#|    )
#|    return parser.parse_args()
#|
#|
#|def score_row(row: dict[str, object]) -> tuple[dict[str, int], list[str]]:
#|    scores = {candidate: 0 for candidate in CANDIDATES}
#|    notes: list[str] = []
#|    family = common.normalize_text(row.get("커널로그_원인군_ko"))
#|    event_type = common.normalize_text(row.get("사건유형_ko"))
#|    terminal = common.normalize_text(row.get("최종고장양상_ko"))
#|    source = common.normalize_text(row.get("대표critical_source"))
#|    subtype = common.normalize_text(row.get("대표anom_subtype"))
#|
#|    for candidate, weight in FAMILY_BASE_RULES.get(family, {"원인미확정": 2}).items():
#|        scores[candidate] += weight
#|    notes.append(f"family={family or 'blank'}")
#|
#|    for candidate, weight in TEMPORAL_RULES.get((event_type, terminal), {}).items():
#|        scores[candidate] += weight
#|    if event_type or terminal:
#|        notes.append(f"temporal={event_type}/{terminal}")
#|
#|    for candidate, weight in SOURCE_RULES.get(source, {}).items():
#|        scores[candidate] += weight
#|    if source:
#|        notes.append(f"critical_source={source}")
#|
#|    lowered_subtype = subtype.lower()
#|    for token, rule in SUBTYPE_RULES.items():
#|        if token in lowered_subtype:
#|            for candidate, weight in rule.items():
#|                scores[candidate] += weight
#|            notes.append(f"anom_subtype~={token}")
#|
#|    if max(scores.values()) <= 0:
#|        scores["원인미확정"] = 1
#|    return scores, notes
#|
#|
#|def choose_ranked_candidates(scores: dict[str, int]) -> list[tuple[str, int]]:
#|    return sorted(scores.items(), key=lambda item: (-item[1], TIE_PRIORITY[item[0]], item[0]))
#|
#|
#|def competition_state(top_scores: list[int]) -> tuple[str, str]:
#|    if len(top_scores) < 2:
#|        return "단일우세", ""
#|    max_score = top_scores[0]
#|    tied = [idx for idx, score in enumerate(top_scores) if score == max_score]
#|    if len(tied) == 1:
#|        return "단일우세", ""
#|    if len(tied) == 2:
#|        return "2강경합", "top1_tie"
#|    return "다자경합", "multi_tie"
#|
#|
#|def confidence_label(top1: int, top2: int) -> str:
#|    gap = top1 - top2
#|    if top1 >= 6 and gap >= 2:
#|        return "높음"
#|    if top1 >= 4 and gap >= 1:
#|        return "중간"
#|    return "보통"
#|
#|
#|def build_outputs(verdict_df: pd.DataFrame, audit_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
#|    audit_lookup = {
#|        (common.normalize_text(row["site"]), common.normalize_text(row["panel_id"])): row
#|        for row in audit_df.to_dict(orient="records")
#|    }
#|    rows: list[dict[str, object]] = []
#|    summary_counts = {key: 0 for key in [
#|        "다이오드·서브스트링형",
#|        "접속·부분개방형",
#|        "열화형",
#|        "부분음영형",
#|        "센서·피드백형",
#|        "원인미확정",
#|    ]}
#|    fault_count = 0
#|
#|    for row in verdict_df.to_dict(orient="records"):
#|        if common.normalize_text(row.get("패널고장여부_ko")) != "고장":
#|            continue
#|        fault_count += 1
#|        key = (common.normalize_text(row["site"]), common.normalize_text(row["panel_id"]))
#|        merged = dict(row)
#|        merged.update(audit_lookup.get(key, {}))
#|        scores, notes = score_row(merged)
#|        ranked = choose_ranked_candidates(scores)
#|        top3 = ranked[:3]
#|        top_scores = [score for _, score in top3]
#|        competition, tie_note = competition_state(top_scores)
#|        top1, top2, top3_item = top3
#|        summary_counts[top1[0]] = summary_counts.get(top1[0], 0) + 1
#|        notes_text = ", ".join(notes + ([tie_note] if tie_note else []))
#|        rows.append(
#|            {
#|                "site": key[0],
#|                "panel_id": key[1],
#|                "사건유형_ko": common.normalize_text(row.get("사건유형_ko")),
#|                "최종고장양상_ko": common.normalize_text(row.get("최종고장양상_ko")),
#|                "커널로그_원인군_ko": common.normalize_text(row.get("커널로그_원인군_ko")),
#|                "GPVS_내부참고유형_ko": "",
#|                "GPVS_외부참조패턴_ko": "",
#|                "원인후보_top1_ko": top1[0],
#|                "원인후보_top1_score": top1[1],
#|                "원인후보_top2_ko": top2[0],
#|                "원인후보_top2_score": top2[1],
#|                "원인후보_top3_ko": top3_item[0],
#|                "원인후보_top3_score": top3_item[1],
#|                "원인후보_경합상태_ko": competition,
#|                "원인후보_공동상위후보_csv": ",".join(candidate for candidate, score in top3 if score == top1[1]),
#|                "원인후보_실증우선확인_ko": common.display_heuristic_name(top1[0]),
#|                "원인후보_신뢰도_ko": confidence_label(top1[1], top2[1]),
#|                "원인후보_해석메모_ko": notes_text,
#|            }
#|        )
#|
#|    main_df = pd.DataFrame(rows).reindex(columns=MAIN_COLS).sort_values(["site", "panel_id"]).reset_index(drop=True)
#|    summary_df = pd.DataFrame(
#|        [
#|            {
#|                "fault_panel_count": fault_count,
#|                "top1_다이오드서브스트링형_count": int(summary_counts.get("다이오드·서브스트링형", 0)),
#|                "top1_접속부분개방형_count": int(summary_counts.get("접속·부분개방형", 0)),
#|                "top1_열화형_count": int(summary_counts.get("열화형", 0)),
#|                "top1_부분음영형_count": int(summary_counts.get("부분음영형", 0)),
#|                "top1_센서피드백형_count": int(summary_counts.get("센서·피드백형", 0)),
#|                "top1_원인미확정_count": int(summary_counts.get("원인미확정", 0)),
#|                "note_ko": (
#|                    "이 runtime heuristic는 raw-only strict chain용 deterministic triage 규칙이다. "
#|                    "family/event/source/subtype만 사용하며 GPVS/frozen label은 사용하지 않는다."
#|                ),
#|            }
#|        ]
#|    ).reindex(columns=SUMMARY_COLS)
#|    return main_df, summary_df
#|
#|
#|def main() -> None:
#|    args = parse_args()
#|    root = args.root.resolve()
#|    share_dir = root / "_share"
#|    verdict_df = common.read_csv(share_dir / common.RUNTIME_VERDICT_OUTPUT_NAME)
#|    audit_df = common.read_csv(share_dir / common.RUNTIME_AUDIT_OUTPUT_NAME)
#|    main_df, summary_df = build_outputs(verdict_df, audit_df)
#|    output_path = share_dir / common.RUNTIME_HEURISTIC_OUTPUT_NAME
#|    summary_path = share_dir / common.RUNTIME_HEURISTIC_SUMMARY_NAME
#|    main_df.to_csv(output_path, index=False, encoding="utf-8-sig")
#|    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
#|    print(f"[OK] wrote runtime raw-only heuristic: {output_path}")
#|
#|
#|if __name__ == "__main__":
#|    main()
# pvdiag_payload_end
# endregion
# region payload: display_label_registry
# pvdiag_payload_file {"bytes": 3223, "endswith_newline": true, "lines": 67, "path": "release/conalog_full_runtime_v1/package/research/prognostics/heuristic_display_registry_v1.py", "role": "display_label_registry", "sha256": "5ce767d422b02db6781954e05ced907c802f53df661c7f30d0b15a357ebe19ba"}
#|#!/usr/bin/env python3
#|from __future__ import annotations
#|
#|import math
#|
#|
#|# `_ko` fields are Korean display labels. Keep them operator/engineer-readable,
#|# and prefer precise field-facing terminology over overly softened wording.
#|# This registry intentionally covers only remapped heuristic-family labels and
#|# their short glossary notes. Longer report/README prose stays outside.
#|DISPLAY_HEURISTIC_NAME_MAP = {
#|    "다이오드·서브스트링형": "다이오드·서브스트링 이상형",
#|    "접속·부분개방형": "접속 불량·부분 개방형",
#|    "센서·피드백형": "센서·계측 피드백 이상형",
#|    "제어응답형": "제어 응답 이상형",
#|    "전력변환부형": "전력변환부 이상형",
#|    "외부계통교란형": "외부 계통 교란형",
#|}
#|
#|HEURISTIC_DISPLAY_NOTE_MAP = {
#|    "다이오드·서브스트링 이상형": "서브스트링 단위 전류 불균형이나 바이패스 다이오드 이상처럼 국소 회로 문제를 우선 의심하는 라벨",
#|    "접속 불량·부분 개방형": "커넥터, 접속부, 배선 일부 개방처럼 접촉 저항 증가나 단속성 단선을 우선 의심하는 라벨",
#|    "센서·계측 피드백 이상형": "센서값, 계측 피드백, 측정 체인 이상 때문에 전기적 이상처럼 보일 수 있는 경우를 가리키는 라벨",
#|    "제어 응답 이상형": "MLPE나 제어기가 패널 상태 변화에 비정상적으로 응답하거나 추종이 흔들리는 경우를 가리키는 라벨",
#|    "전력변환부 이상형": "인버터, 전력변환부, 내부 전력 전자 회로 영향 가능성을 우선 두는 라벨",
#|    "외부 계통 교란형": "계통 전압 변동, 외부 전원 품질 저하, 공통 외란처럼 패널 외부 요인 가능성을 우선 두는 라벨",
#|}
#|
#|LEGACY_HEURISTIC_DISPLAY_NAME_MAP = {
#|    "다이오드·국소 회로 이상형": "다이오드·서브스트링 이상형",
#|    "접촉 끊김 형": "접속 불량·부분 개방형",
#|    "장치 측정 이상형": "센서·계측 피드백 이상형",
#|    "외부 전원 흔들림형": "외부 계통 교란형",
#|}
#|
#|LEGACY_HEURISTIC_DISPLAY_NAMES = frozenset(LEGACY_HEURISTIC_DISPLAY_NAME_MAP)
#|
#|
#|def normalize_display_text(value: object) -> str:
#|    if value is None:
#|        return ""
#|    if isinstance(value, float) and math.isnan(value):
#|        return ""
#|    text = str(value).strip()
#|    return "" if text.lower() == "nan" else text
#|
#|
#|def display_heuristic_name(raw_label: object) -> str:
#|    normalized = normalize_display_text(raw_label)
#|    if not normalized:
#|        return ""
#|    if normalized in DISPLAY_HEURISTIC_NAME_MAP:
#|        return DISPLAY_HEURISTIC_NAME_MAP[normalized]
#|    if normalized in HEURISTIC_DISPLAY_NOTE_MAP:
#|        return normalized
#|    if normalized in LEGACY_HEURISTIC_DISPLAY_NAME_MAP:
#|        return LEGACY_HEURISTIC_DISPLAY_NAME_MAP[normalized]
#|    return normalized
#|
#|
#|def display_heuristic_note(raw_label: object) -> str:
#|    normalized = display_heuristic_name(raw_label)
#|    return HEURISTIC_DISPLAY_NOTE_MAP.get(normalized, "")
#|
#|
#|def contains_legacy_heuristic_display_name(value: object) -> bool:
#|    return normalize_display_text(value) in LEGACY_HEURISTIC_DISPLAY_NAMES
# pvdiag_payload_end
# endregion
# region payload: raw_only_shared_utils
# pvdiag_payload_file {"bytes": 46428, "endswith_newline": true, "lines": 1109, "path": "release/conalog_full_runtime_v1/package/research/prognostics/runtime_rawonly_chain_common_v1.py", "role": "raw_only_shared_utils", "sha256": "d3fbf8fcf2a6d3b1a5f0674f3406c09f607b48a01d3bbb5aca73fad62f4f1ae1"}
#|#!/usr/bin/env python3
#|from __future__ import annotations
#|
#|from dataclasses import dataclass
#|from pathlib import Path
#|
#|import pandas as pd
#|
#|if __package__ in {None, ""}:
#|    import sys
#|
#|    REPO_ROOT = Path(__file__).resolve().parents[2]
#|    if str(REPO_ROOT) not in sys.path:
#|        sys.path.insert(0, str(REPO_ROOT))
#|    from research.prognostics.heuristic_display_registry_v1 import (
#|        DISPLAY_HEURISTIC_NAME_MAP,
#|        HEURISTIC_DISPLAY_NOTE_MAP,
#|        display_heuristic_name as shared_display_heuristic_name,
#|        display_heuristic_note as shared_display_heuristic_note,
#|    )
#|else:
#|    from .heuristic_display_registry_v1 import (
#|        DISPLAY_HEURISTIC_NAME_MAP,
#|        HEURISTIC_DISPLAY_NOTE_MAP,
#|        display_heuristic_name as shared_display_heuristic_name,
#|        display_heuristic_note as shared_display_heuristic_note,
#|    )
#|
#|
#|RUNTIME_AUDIT_OUTPUT_NAME = "panel_day_engine_runtime_fault_event_audit_v1.csv"
#|RUNTIME_AUDIT_SUMMARY_NAME = "panel_day_engine_runtime_fault_event_audit_summary_v1.csv"
#|RUNTIME_VERDICT_OUTPUT_NAME = "panel_day_engine_runtime_final_verdict_v1.csv"
#|RUNTIME_VERDICT_SUMMARY_NAME = "panel_day_engine_runtime_final_verdict_summary_v1.csv"
#|RUNTIME_HEURISTIC_OUTPUT_NAME = "panel_day_engine_runtime_cause_candidate_heuristics_v1.csv"
#|RUNTIME_HEURISTIC_SUMMARY_NAME = "panel_day_engine_runtime_cause_candidate_summary_v1.csv"
#|
#|RUNTIME_DECISION_COMPARE_COLS = [
#|    "site",
#|    "panel_id",
#|    "패널고장여부_ko",
#|    "사건유형_ko",
#|    "최종고장양상_ko",
#|    "커널로그_원인군_ko",
#|    "1순위_의심원인_ko",
#|    "2순위_의심원인_ko",
#|    "3순위_의심원인_ko",
#|]
#|RUNTIME_FAULT_OUTPUT_COLS = [
#|    *RUNTIME_DECISION_COMPARE_COLS,
#|    "전조날짜",
#|    "고장날짜",
#|]
#|RUNTIME_PREVIEW_OUTPUT_COLS = [
#|    "site",
#|    "panel_id",
#|    "패널고장여부_ko",
#|    "사건유형_ko",
#|    "최종고장양상_ko",
#|    "전조날짜",
#|    "고장날짜",
#|    "커널로그_원인군_ko",
#|    "1순위_의심원인_ko",
#|    "2순위_의심원인_ko",
#|    "3순위_의심원인_ko",
#|    "커널로그 기존 알고리즘",
#|]
#|
#|PRIMARY_WARNING_COLS = [
#|    "ews_warning",
#|    "pre_alarm",
#|]
#|SECONDARY_WARNING_COLS = [
#|    "pre_ews",
#|    "prefault_cond_mid",
#|    "prefault_cond_ae",
#|    "prefault_cond_dtw",
#|    "prefault_cond_ews",
#|    "prealarm_cond_ae_mid_or_hi",
#|    "prealarm_cond_dtw_mid_or_hi",
#|    "prealarm_cond_hs_mid_or_hi",
#|]
#|ALL_WARNING_COLS = PRIMARY_WARNING_COLS + SECONDARY_WARNING_COLS
#|PRIMARY_WARNING_MAX_GAP_DAYS = 120
#|SECONDARY_WARNING_MIN_GAP_DAYS = 7
#|SECONDARY_WARNING_MAX_GAP_DAYS = 120
#|PREFERRED_PREFAULT_B_WARNING_COLS = ["prefault_B_effective", "prefault_B"]
#|PROXIMAL_COMMON_CAUSE_WINDOW_DAYS = 3
#|DEGRADATION_ONSET_BACKDATE_GUARD_NAME = "G1_extreme_longgap_one_day"
#|DEGRADATION_ONSET_BACKDATE_GUARD_MIN_GAP_DAYS = 30
#|DEGRADATION_ONSET_BACKDATE_GUARD_MAX_DEGRADE_DAYS = 1
#|
#|
#|@dataclass(frozen=True)
#|class PanelRuntimeMetrics:
#|    site: str
#|    panel_id: str
#|    earliest_warning_date: str
#|    earliest_warning_marker: str
#|    retrospective_onset_date: str
#|    strict_trigger_date: str
#|    first_final_fault_date: str
#|    dead_diag_date: str
#|    onset_confidence: str
#|    onset_method: str
#|    패널고장여부_ko: str
#|    전조흔적_flag: int
#|    순수급작_flag: int
#|    전조평가셋편입_flag: int
#|    급작평가셋편입_flag: int
#|    사건유형_재판정_ko: str
#|    최종고장양상_재판정_ko: str
#|    재판정_근거_ko: str
#|    현재표_보정필요여부_flag: int
#|    대표critical_source: str
#|    대표anom_level: str
#|    대표anom_subtype: str
#|    algorithm_family_ko: str
#|    algorithm_symptom_ko: str
#|    detailed_fault_code: str
#|    detailed_fault_label_ko: str
#|    gap_days: int
#|    degradation_onset_backdate_guard_flag: bool
#|    degradation_onset_backdate_guard_name: str
#|    degradation_onset_backdate_guard_reason: str
#|    degradation_onset_backdate_guard_degrade_days: int
#|    secondary_window_candidate_flag: bool
#|    secondary_window_selected_onset_date: str
#|    secondary_window_selected_marker: str
#|    secondary_window_selected_gap_days: int
#|    secondary_window_qualified_count: int
#|    secondary_window_too_early_count: int
#|    secondary_window_change_class: str
#|    secondary_window_review_tier: str
#|    secondary_window_reason: str
#|    common_cause_anchor_date: str
#|    common_cause_anchor_kind: str
#|    has_final_fault: bool
#|    has_critical_fault: bool
#|    has_fault_like: bool
#|    has_degradation: bool
#|    has_shadow: bool
#|    has_vdrop: bool
#|    has_site_event: bool
#|    has_group_off: bool
#|    has_subgroup_common_cause: bool
#|    has_common_cause_history: bool
#|    has_strict_trigger_proximal_common_cause: bool
#|    has_warning_proximal_common_cause: bool
#|    has_trigger_proximal_common_cause: bool
#|
#|
#|def normalize_text(value: object) -> str:
#|    if value is None:
#|        return ""
#|    if isinstance(value, float) and pd.isna(value):
#|        return ""
#|    text = str(value).strip()
#|    return "" if text.lower() == "nan" else text
#|
#|
#|def truthy_mask(series: pd.Series) -> pd.Series:
#|    lowered = series.astype(str).str.strip().str.lower()
#|    return lowered.isin({"1", "true", "t", "yes"})
#|
#|
#|def read_csv(path: Path, required: bool = True) -> pd.DataFrame:
#|    if not path.exists():
#|        if required:
#|            raise SystemExit(f"missing input: {path}")
#|        return pd.DataFrame()
#|    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
#|
#|
#|def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
#|    missing = [column for column in required if column not in df.columns]
#|    if missing:
#|        raise SystemExit(f"{name} missing columns: {missing}")
#|
#|
#|def to_timestamp(value: object) -> pd.Timestamp | None:
#|    if pd.isna(value):
#|        return None
#|    ts = pd.to_datetime(value, errors="coerce")
#|    if pd.isna(ts):
#|        return None
#|    return ts.normalize()
#|
#|
#|def format_date(value: object) -> str:
#|    ts = to_timestamp(value)
#|    return "" if ts is None else ts.strftime("%Y-%m-%d")
#|
#|
#|def min_ts(values: list[pd.Timestamp | None]) -> pd.Timestamp | None:
#|    parsed = [value for value in values if value is not None]
#|    return min(parsed) if parsed else None
#|
#|
#|def first_true_date(df: pd.DataFrame, column: str) -> pd.Timestamp | None:
#|    if df.empty or column not in df.columns or "date" not in df.columns:
#|        return None
#|    working = df.loc[truthy_mask(df[column]), "date"]
#|    if working.empty:
#|        return None
#|    ts = pd.to_datetime(working, errors="coerce").dropna()
#|    return None if ts.empty else ts.min().normalize()
#|
#|
#|def true_date_set(df: pd.DataFrame, columns: list[str]) -> set[pd.Timestamp]:
#|    if df.empty or "date" not in df.columns:
#|        return set()
#|    dates: set[pd.Timestamp] = set()
#|    for column in columns:
#|        if column not in df.columns:
#|            continue
#|        working = pd.to_datetime(df.loc[truthy_mask(df[column]), "date"], errors="coerce").dropna()
#|        dates.update(pd.Timestamp(ts).normalize() for ts in working.tolist())
#|    return dates
#|
#|
#|def first_true_marker(df: pd.DataFrame, columns: list[str]) -> tuple[pd.Timestamp | None, str]:
#|    candidates: list[tuple[pd.Timestamp, str]] = []
#|    for column in columns:
#|        ts = first_true_date(df, column)
#|        if ts is not None:
#|            candidates.append((ts, column))
#|    if not candidates:
#|        return None, ""
#|    candidates.sort(key=lambda item: (item[0], item[1]))
#|    return candidates[0]
#|
#|
#|def true_marker_candidates(df: pd.DataFrame, columns: list[str]) -> list[tuple[pd.Timestamp, str]]:
#|    candidates: list[tuple[pd.Timestamp, str]] = []
#|    if df.empty or "date" not in df.columns:
#|        return candidates
#|    for column in dict.fromkeys(columns):
#|        if column not in df.columns:
#|            continue
#|        dates = pd.to_datetime(df.loc[truthy_mask(df[column]), "date"], errors="coerce").dropna()
#|        candidates.extend((pd.Timestamp(ts).normalize(), column) for ts in dates.tolist())
#|    candidates.sort(key=lambda item: (item[0], item[1]))
#|    return candidates
#|
#|
#|def first_true_marker_in_gap_window(
#|    df: pd.DataFrame,
#|    columns: list[str],
#|    strict_trigger: pd.Timestamp | None,
#|    min_gap_days: int,
#|    max_gap_days: int,
#|) -> tuple[pd.Timestamp | None, str, int, int, int]:
#|    if strict_trigger is None:
#|        return None, "", 0, 0, 0
#|
#|    qualified: list[tuple[pd.Timestamp, str, int]] = []
#|    too_early_count = 0
#|    for ts, marker in true_marker_candidates(df, columns):
#|        if ts >= strict_trigger:
#|            continue
#|        gap_days = int((strict_trigger - ts).days)
#|        if min_gap_days <= gap_days <= max_gap_days:
#|            qualified.append((ts, marker, gap_days))
#|        elif gap_days > max_gap_days:
#|            too_early_count += 1
#|
#|    if not qualified:
#|        return None, "", 0, 0, too_early_count
#|    qualified.sort(key=lambda item: (item[0], item[1]))
#|    selected_ts, selected_marker, selected_gap = qualified[0]
#|    return selected_ts, selected_marker, selected_gap, len(qualified), too_early_count
#|
#|
#|def resolve_secondary_warning_cols(df: pd.DataFrame) -> list[str]:
#|    prefault_col = next(
#|        (column for column in PREFERRED_PREFAULT_B_WARNING_COLS if column in df.columns),
#|        "prefault_B",
#|    )
#|    return list(dict.fromkeys(["pre_ews", prefault_col, *SECONDARY_WARNING_COLS]))
#|
#|
#|def discover_sites(root: Path) -> list[str]:
#|    data_root = root / "data"
#|    if not data_root.exists():
#|        raise SystemExit(f"missing data root: {data_root}")
#|    sites = sorted(
#|        path.name
#|        for path in data_root.iterdir()
#|        if path.is_dir() and (path / "out" / "panel_day_core.csv").exists()
#|    )
#|    if not sites:
#|        raise SystemExit(f"no site outputs found under: {data_root}")
#|    return sites
#|
#|
#|def load_site_outputs(root: Path, site: str) -> tuple[pd.DataFrame, pd.DataFrame]:
#|    out_dir = root / "data" / site / "out"
#|    core_path = out_dir / "panel_day_core.csv"
#|    gate_path = out_dir / "ae_simple_local_precursor_gate_daily.csv"
#|    core_df = read_csv(core_path)
#|    ensure_columns(
#|        core_df,
#|        [
#|            "date",
#|            "panel_id",
#|            "critical_source",
#|            "final_fault",
#|            "critical_fault",
#|            "fault_like_day",
#|            "anom_level",
#|            "anom_subtype",
#|        ],
#|        core_path.name,
#|    )
#|    core_df["date"] = pd.to_datetime(core_df["date"], errors="coerce")
#|    core_df["panel_id"] = core_df["panel_id"].astype(str)
#|    gate_df = read_csv(gate_path, required=False)
#|    if not gate_df.empty:
#|        ensure_columns(gate_df, ["date", "panel_id"], gate_path.name)
#|        gate_df["date"] = pd.to_datetime(gate_df["date"], errors="coerce")
#|        gate_df["panel_id"] = gate_df["panel_id"].astype(str)
#|    return core_df, gate_df
#|
#|
#|def panel_keys(core_df: pd.DataFrame, gate_df: pd.DataFrame) -> list[str]:
#|    keys = set(core_df["panel_id"].astype(str).tolist())
#|    if not gate_df.empty and "panel_id" in gate_df.columns:
#|        keys.update(gate_df["panel_id"].astype(str).tolist())
#|    return sorted(key for key in keys if normalize_text(key))
#|
#|
#|def representative_row(panel_core: pd.DataFrame) -> pd.Series:
#|    final_rows = panel_core.loc[truthy_mask(panel_core["final_fault"])]
#|    critical_rows = panel_core.loc[truthy_mask(panel_core["critical_fault"])]
#|    fault_like_rows = panel_core.loc[truthy_mask(panel_core["fault_like_day"])]
#|    if not final_rows.empty:
#|        return final_rows.sort_values("date").iloc[0]
#|    if not critical_rows.empty:
#|        return critical_rows.sort_values("date").iloc[0]
#|    if not fault_like_rows.empty:
#|        return fault_like_rows.sort_values("date").iloc[0]
#|    return panel_core.sort_values("date").iloc[-1]
#|
#|
#|def has_subgroup_common_cause_history(
#|    panel_core: pd.DataFrame,
#|    panel_gate: pd.DataFrame,
#|    core_df: pd.DataFrame,
#|) -> bool:
#|    if "subgroup_common_cause_candidate" in panel_core.columns:
#|        return first_true_date(panel_core, "subgroup_common_cause_candidate") is not None
#|    required_core = {"date", "panel_id", "group_key_base", "degraded_candidate"}
#|    if panel_core.empty or not required_core.issubset(core_df.columns):
#|        return False
#|
#|    working = panel_core.loc[:, ["date", "panel_id", "group_key_base", "degraded_candidate"]].copy()
#|    working["degraded_candidate"] = truthy_mask(working["degraded_candidate"])
#|    working = working.loc[working["degraded_candidate"]].copy()
#|    if working.empty:
#|        return False
#|
#|    same_base_counts = (
#|        core_df.loc[:, ["date", "group_key_base", "degraded_candidate"]]
#|        .assign(degraded_candidate=lambda df: truthy_mask(df["degraded_candidate"]))
#|        .loc[lambda df: df["degraded_candidate"]]
#|        .groupby(["date", "group_key_base"], dropna=False)
#|        .size()
#|        .rename("base_day_degraded_panel_count")
#|        .reset_index()
#|    )
#|    working = working.merge(same_base_counts, on=["date", "group_key_base"], how="left")
#|
#|    if not panel_gate.empty:
#|        gate_flags = panel_gate.loc[:, ["date", "panel_id"]].copy()
#|        for col in ["site_event_soft", "site_event_hard", "group_off_date", "group_off_like"]:
#|            gate_flags[col] = truthy_mask(panel_gate[col]) if col in panel_gate.columns else False
#|        working = working.merge(gate_flags, on=["date", "panel_id"], how="left")
#|    else:
#|        for col in ["site_event_soft", "site_event_hard", "group_off_date", "group_off_like"]:
#|            working[col] = False
#|
#|    for col in ["site_event_soft", "site_event_hard", "group_off_date", "group_off_like"]:
#|        working[col] = working[col].fillna(False).astype(bool)
#|    working["base_day_degraded_panel_count"] = pd.to_numeric(
#|        working["base_day_degraded_panel_count"], errors="coerce"
#|    ).fillna(0)
#|
#|    candidate = (
#|        working["base_day_degraded_panel_count"].ge(3)
#|        & (~working["site_event_soft"])
#|        & (~working["site_event_hard"])
#|        & (~working["group_off_date"])
#|        & (~working["group_off_like"])
#|    )
#|    return bool(candidate.any())
#|
#|
#|def subgroup_common_cause_date_set(
#|    panel_core: pd.DataFrame,
#|    panel_gate: pd.DataFrame,
#|    core_df: pd.DataFrame,
#|) -> set[pd.Timestamp]:
#|    if "subgroup_common_cause_candidate" in panel_core.columns:
#|        return true_date_set(panel_core, ["subgroup_common_cause_candidate"])
#|    required_core = {"date", "panel_id", "group_key_base", "degraded_candidate"}
#|    if panel_core.empty or not required_core.issubset(core_df.columns):
#|        return set()
#|
#|    working = panel_core.loc[:, ["date", "panel_id", "group_key_base", "degraded_candidate"]].copy()
#|    working["degraded_candidate"] = truthy_mask(working["degraded_candidate"])
#|    working = working.loc[working["degraded_candidate"]].copy()
#|    if working.empty:
#|        return set()
#|
#|    same_base_counts = (
#|        core_df.loc[:, ["date", "group_key_base", "degraded_candidate"]]
#|        .assign(degraded_candidate=lambda df: truthy_mask(df["degraded_candidate"]))
#|        .loc[lambda df: df["degraded_candidate"]]
#|        .groupby(["date", "group_key_base"], dropna=False)
#|        .size()
#|        .rename("base_day_degraded_panel_count")
#|        .reset_index()
#|    )
#|    working = working.merge(same_base_counts, on=["date", "group_key_base"], how="left")
#|
#|    if not panel_gate.empty:
#|        gate_flags = panel_gate.loc[:, ["date", "panel_id"]].copy()
#|        for col in ["site_event_soft", "site_event_hard", "group_off_date", "group_off_like"]:
#|            gate_flags[col] = truthy_mask(panel_gate[col]) if col in panel_gate.columns else False
#|        working = working.merge(gate_flags, on=["date", "panel_id"], how="left")
#|    else:
#|        for col in ["site_event_soft", "site_event_hard", "group_off_date", "group_off_like"]:
#|            working[col] = False
#|
#|    for col in ["site_event_soft", "site_event_hard", "group_off_date", "group_off_like"]:
#|        working[col] = working[col].fillna(False).astype(bool)
#|    working["base_day_degraded_panel_count"] = pd.to_numeric(
#|        working["base_day_degraded_panel_count"], errors="coerce"
#|    ).fillna(0)
#|
#|    candidate = (
#|        working["base_day_degraded_panel_count"].ge(3)
#|        & (~working["site_event_soft"])
#|        & (~working["site_event_hard"])
#|        & (~working["group_off_date"])
#|        & (~working["group_off_like"])
#|    )
#|    return {
#|        pd.Timestamp(ts).normalize()
#|        for ts in pd.to_datetime(working.loc[candidate, "date"], errors="coerce").dropna().tolist()
#|    }
#|
#|
#|def panel_abnormal_date_set(panel_core: pd.DataFrame, panel_gate: pd.DataFrame) -> set[pd.Timestamp]:
#|    core_dates = true_date_set(
#|        panel_core,
#|        [
#|            "degraded_candidate",
#|            "fault_like_day",
#|            "critical_fault",
#|            "final_fault",
#|            "shadow_like",
#|            "group_off_like",
#|        ],
#|    )
#|    gate_dates = true_date_set(
#|        panel_gate,
#|        [
#|            "ews_warning",
#|            "pre_alarm",
#|            "pre_ews",
#|            "prefault_B",
#|            "prefault_B_effective",
#|            "prefault_B_common_cause_overlap",
#|        ],
#|    )
#|    return core_dates | gate_dates
#|
#|
#|def count_degradation_days_between(
#|    panel_core: pd.DataFrame,
#|    onset: pd.Timestamp | None,
#|    strict_trigger: pd.Timestamp | None,
#|) -> int:
#|    if onset is None or strict_trigger is None or panel_core.empty or "date" not in panel_core.columns:
#|        return 0
#|
#|    dates = pd.to_datetime(panel_core["date"], errors="coerce")
#|    window_mask = dates.notna() & dates.ge(onset) & dates.le(strict_trigger)
#|    if not window_mask.any():
#|        return 0
#|
#|    degrade_mask = pd.Series(False, index=panel_core.index)
#|    if "degraded_candidate" in panel_core.columns:
#|        degrade_mask = truthy_mask(panel_core["degraded_candidate"])
#|    subtype_mask = pd.Series(False, index=panel_core.index)
#|    if "anom_subtype" in panel_core.columns:
#|        subtype_mask = panel_core["anom_subtype"].astype(str).str.contains("degradation", case=False, na=False)
#|
#|    matched_dates = dates.loc[window_mask & (degrade_mask | subtype_mask)].dt.normalize().dropna()
#|    return int(matched_dates.nunique())
#|
#|
#|def first_available_anchor(
#|    strict_trigger: pd.Timestamp | None,
#|    earliest_warning: pd.Timestamp | None,
#|    retrospective_onset: pd.Timestamp | None,
#|) -> tuple[pd.Timestamp | None, str]:
#|    if strict_trigger is not None:
#|        return strict_trigger, "strict_trigger"
#|    if earliest_warning is not None:
#|        return earliest_warning, "earliest_warning"
#|    if retrospective_onset is not None:
#|        return retrospective_onset, "retrospective_onset"
#|    return None, ""
#|
#|
#|def choose_algorithm_family(
#|    representative_source: str,
#|    representative_subtype: str,
#|    event_type_ko: str,
#|    has_final_fault: bool,
#|    has_critical_fault: bool,
#|    has_degradation: bool,
#|    has_shadow: bool,
#|) -> tuple[str, str, str, str]:
#|    if event_type_ko != "전조형 고장" and event_type_ko != "급작 고장":
#|        return "", "", "", ""
#|
#|    if has_degradation and event_type_ko == "전조형 고장" and not has_final_fault:
#|        return ("모듈손상형", "출력 저하형", "RAW_MODULE_PROGRESSIVE", "알고리즘상 진행성 열화 계열")
#|    if representative_source == "legacy":
#|        return ("개방/장치이상형", "전압 변화형", "RAW_OPEN_LEGACY", "알고리즘상 legacy/open 계열")
#|    if representative_source == "none" and has_final_fault and not has_critical_fault:
#|        return ("개방/장치이상형", "전압 변화형", "RAW_OPEN_NOCRIT", "확정고장이지만 vdrop/critical 증거가 약한 계열")
#|    if representative_source in {"vdrop", "vdrop_suspect"} or "vdrop" in representative_subtype:
#|        return ("다이오드형", "전압 변화형", "RAW_DIODE_VDROP", "알고리즘상 vdrop 계열")
#|    if has_shadow and event_type_ko == "전조형 고장":
#|        return ("모듈손상형", "출력 저하형", "RAW_MODULE_SHADOW", "그림자/열화 진행 계열")
#|    return ("불충분", "불충분", "RAW_UNCERTAIN", "raw-only family 신뢰도가 충분치 않음")
#|
#|
#|def compute_panel_metrics(
#|    site: str,
#|    panel_id: str,
#|    core_df: pd.DataFrame,
#|    gate_df: pd.DataFrame,
#|) -> PanelRuntimeMetrics:
#|    panel_core = core_df.loc[core_df["panel_id"].eq(panel_id)].copy().sort_values("date")
#|    if panel_core.empty:
#|        raise SystemExit(f"panel core rows must not be empty: {(site, panel_id)}")
#|    panel_gate = gate_df.loc[gate_df["panel_id"].eq(panel_id)].copy().sort_values("date") if not gate_df.empty else pd.DataFrame()
#|
#|    first_final_fault = first_true_date(panel_core, "final_fault")
#|    first_critical_fault = first_true_date(panel_core, "critical_fault")
#|    first_fault_like = first_true_date(panel_core, "fault_like_day")
#|    strict_trigger = min_ts([first_critical_fault, first_final_fault, first_fault_like])
#|    first_primary_warning, first_primary_marker = first_true_marker(panel_gate, PRIMARY_WARNING_COLS)
#|    first_secondary_warning, first_secondary_marker = first_true_marker(
#|        panel_gate,
#|        resolve_secondary_warning_cols(panel_gate),
#|    )
#|    (
#|        secondary_window_onset,
#|        secondary_window_marker,
#|        secondary_window_gap_days,
#|        secondary_window_qualified_count,
#|        secondary_window_too_early_count,
#|    ) = first_true_marker_in_gap_window(
#|        panel_gate,
#|        resolve_secondary_warning_cols(panel_gate),
#|        strict_trigger,
#|        SECONDARY_WARNING_MIN_GAP_DAYS,
#|        SECONDARY_WARNING_MAX_GAP_DAYS,
#|    )
#|
#|    has_degradation = panel_core["anom_subtype"].astype(str).str.contains("degradation", case=False, na=False).any()
#|    has_shadow = panel_core["anom_subtype"].astype(str).str.contains("shadow", case=False, na=False).any()
#|    representative = representative_row(panel_core)
#|    representative_source = normalize_text(representative.get("critical_source"))
#|    representative_level = normalize_text(representative.get("anom_level"))
#|    representative_subtype = normalize_text(representative.get("anom_subtype"))
#|    has_vdrop = representative_source in {"vdrop", "vdrop_suspect"} or "vdrop" in representative_subtype
#|    abnormal_dates = panel_abnormal_date_set(panel_core, panel_gate)
#|    site_event_dates = true_date_set(panel_gate, ["site_event_soft", "site_event_hard"])
#|    site_event_overlap_dates = abnormal_dates & site_event_dates
#|    group_off_overlap_dates = abnormal_dates & true_date_set(panel_gate, ["group_off_date", "group_off_like"])
#|    has_group_off = (
#|        (not panel_gate.empty and first_true_date(panel_gate, "group_off_date") is not None)
#|        or panel_core["anom_level"].astype(str).str.contains("group_off", case=False, na=False).any()
#|    )
#|    subgroup_common_cause_dates = subgroup_common_cause_date_set(panel_core, panel_gate, core_df)
#|    has_site_event = bool(site_event_overlap_dates)
#|    has_subgroup_common_cause = bool(subgroup_common_cause_dates)
#|    common_cause_dates = site_event_overlap_dates | group_off_overlap_dates | subgroup_common_cause_dates
#|    has_common_cause_history = bool(common_cause_dates)
#|
#|    earliest_warning = first_primary_warning
#|    earliest_marker = first_primary_marker
#|    if earliest_warning is None:
#|        earliest_warning = first_secondary_warning
#|        earliest_marker = first_secondary_marker
#|
#|    retrospective_onset = None
#|    primary_gap_days = (strict_trigger - first_primary_warning).days if (
#|        strict_trigger is not None and first_primary_warning is not None
#|    ) else None
#|    secondary_gap_days = (strict_trigger - first_secondary_warning).days if (
#|        strict_trigger is not None and first_secondary_warning is not None
#|    ) else None
#|    primary_warning_accepted = (
#|        first_primary_warning is not None
#|        and strict_trigger is not None
#|        and first_primary_warning < strict_trigger
#|        and primary_gap_days is not None
#|        and primary_gap_days <= PRIMARY_WARNING_MAX_GAP_DAYS
#|    )
#|    if strict_trigger is not None:
#|        if primary_warning_accepted:
#|            retrospective_onset = first_primary_warning
#|        elif (
#|            first_secondary_warning is not None
#|            and first_secondary_warning < strict_trigger
#|            and secondary_gap_days is not None
#|            and SECONDARY_WARNING_MIN_GAP_DAYS <= secondary_gap_days <= SECONDARY_WARNING_MAX_GAP_DAYS
#|        ):
#|            retrospective_onset = first_secondary_warning
#|        elif has_degradation:
#|            degradation_rows = panel_core.loc[
#|                panel_core["anom_subtype"].astype(str).str.contains("degradation", case=False, na=False)
#|            ]
#|            if not degradation_rows.empty:
#|                degradation_ts = to_timestamp(degradation_rows.iloc[0]["date"])
#|                if degradation_ts is not None and degradation_ts <= strict_trigger:
#|                    retrospective_onset = degradation_ts
#|                    earliest_marker = "anom_subtype:degradation"
#|
#|    has_final = first_final_fault is not None
#|    has_critical = first_critical_fault is not None
#|    has_fault_like = first_fault_like is not None
#|
#|    if has_final or has_critical or has_fault_like:
#|        fault_status = "고장"
#|    elif earliest_warning is not None:
#|        fault_status = "미확정"
#|    else:
#|        fault_status = "비고장"
#|
#|    gap_days = 0
#|    if retrospective_onset is not None and strict_trigger is not None:
#|        gap_days = max(int((strict_trigger - retrospective_onset).days), 0)
#|
#|    degradation_guard_degrade_days = count_degradation_days_between(
#|        panel_core,
#|        retrospective_onset,
#|        strict_trigger,
#|    )
#|    degradation_guard_flag = (
#|        earliest_marker == "anom_subtype:degradation"
#|        and gap_days >= DEGRADATION_ONSET_BACKDATE_GUARD_MIN_GAP_DAYS
#|        and degradation_guard_degrade_days <= DEGRADATION_ONSET_BACKDATE_GUARD_MAX_DEGRADE_DAYS
#|    )
#|    degradation_guard_reason = ""
#|    if degradation_guard_flag:
#|        degradation_guard_reason = (
#|            f"{DEGRADATION_ONSET_BACKDATE_GUARD_NAME}: "
#|            f"onset_method=anom_subtype:degradation, gap_days>="
#|            f"{DEGRADATION_ONSET_BACKDATE_GUARD_MIN_GAP_DAYS}, "
#|            f"degrade_days_between_onset_and_strict<="
#|            f"{DEGRADATION_ONSET_BACKDATE_GUARD_MAX_DEGRADE_DAYS}"
#|        )
#|
#|    common_cause_anchor_ts, common_cause_anchor_kind = first_available_anchor(
#|        strict_trigger,
#|        earliest_warning,
#|        retrospective_onset,
#|    )
#|    has_strict_trigger_proximal_common_cause = False
#|    has_warning_proximal_common_cause = False
#|    has_trigger_proximal_common_cause = False
#|    if common_cause_dates:
#|        if strict_trigger is not None:
#|            has_strict_trigger_proximal_common_cause = any(
#|                abs(int((date - strict_trigger).days)) <= PROXIMAL_COMMON_CAUSE_WINDOW_DAYS
#|                for date in common_cause_dates
#|            )
#|        elif earliest_warning is not None:
#|            has_warning_proximal_common_cause = any(
#|                abs(int((date - earliest_warning).days)) <= PROXIMAL_COMMON_CAUSE_WINDOW_DAYS
#|                for date in common_cause_dates
#|            )
#|        elif common_cause_anchor_ts is not None:
#|            has_trigger_proximal_common_cause = any(
#|                abs(int((date - common_cause_anchor_ts).days)) <= PROXIMAL_COMMON_CAUSE_WINDOW_DAYS
#|                for date in common_cause_dates
#|            )
#|    has_trigger_proximal_common_cause = (
#|        has_trigger_proximal_common_cause
#|        or has_strict_trigger_proximal_common_cause
#|        or has_warning_proximal_common_cause
#|    )
#|
#|    precursor_flag = int(fault_status == "고장" and retrospective_onset is not None)
#|    abrupt_flag = int(fault_status == "고장" and not precursor_flag)
#|    precursor_eval_flag = precursor_flag
#|    abrupt_eval_flag = abrupt_flag
#|
#|    if fault_status != "고장":
#|        event_type = ""
#|        terminal_pattern = ""
#|        onset_confidence = ""
#|        onset_method = ""
#|        current_needs_correction = 0
#|    elif precursor_flag:
#|        event_type = "전조형 고장"
#|        if has_degradation or not has_final or (has_vdrop and gap_days >= 7):
#|            terminal_pattern = "진행성 악화"
#|        else:
#|            terminal_pattern = "급격 종료"
#|        if gap_days >= 14:
#|            onset_confidence = "high"
#|        elif gap_days >= 3:
#|            onset_confidence = "medium"
#|        else:
#|            onset_confidence = "low"
#|        onset_method = earliest_marker or "runtime_precursor_gate"
#|        current_needs_correction = 1
#|    else:
#|        event_type = "급작 고장"
#|        terminal_pattern = "급작 발생"
#|        onset_confidence = "low"
#|        onset_method = "runtime_trigger_only"
#|        current_needs_correction = 0
#|
#|    secondary_window_candidate_flag = (
#|        strict_trigger is not None
#|        and not primary_warning_accepted
#|        and secondary_window_onset is not None
#|        and (
#|            format_date(secondary_window_onset) != format_date(retrospective_onset)
#|            or secondary_window_marker != onset_method
#|            or onset_method == "runtime_trigger_only"
#|        )
#|    )
#|    secondary_window_change_class = ""
#|    if secondary_window_candidate_flag:
#|        selected_onset_date = format_date(secondary_window_onset)
#|        current_onset_date = format_date(retrospective_onset)
#|        if (
#|            event_type == "전조형 고장"
#|            and selected_onset_date == current_onset_date
#|            and secondary_window_marker != onset_method
#|        ):
#|            secondary_window_change_class = "method_provenance_only_primary_marker_mismatch"
#|        elif onset_method == "anom_subtype:degradation":
#|            secondary_window_change_class = (
#|                "g1_degradation_fallback_replaced_by_secondary"
#|                if degradation_guard_flag
#|                else "degradation_fallback_replaced_by_secondary"
#|            )
#|        elif onset_method == "runtime_trigger_only" and fault_status == "고장":
#|            secondary_window_change_class = "trigger_only_to_precursor"
#|        elif event_type == "전조형 고장" and selected_onset_date != current_onset_date:
#|            secondary_window_change_class = "onset_date_shift_without_event_flip"
#|        else:
#|            secondary_window_change_class = "secondary_window_candidate"
#|
#|    secondary_window_review_tier = ""
#|    if secondary_window_change_class == "trigger_only_to_precursor":
#|        if (
#|            has_strict_trigger_proximal_common_cause
#|            or has_site_event
#|            or has_subgroup_common_cause
#|        ):
#|            secondary_window_review_tier = "review_supported_context"
#|        elif secondary_window_qualified_count >= 30:
#|            secondary_window_review_tier = "review_persistent_secondary_only"
#|        else:
#|            secondary_window_review_tier = "review_sparse_secondary_only"
#|    elif secondary_window_change_class == "method_provenance_only_primary_marker_mismatch":
#|        secondary_window_review_tier = "audit_provenance_only"
#|    elif secondary_window_change_class:
#|        secondary_window_review_tier = "audit_no_event_flip"
#|
#|    secondary_window_reason = ""
#|    if secondary_window_candidate_flag:
#|        secondary_window_reason = (
#|            "BR004_secondary_warning_window_shadow: "
#|            f"first_secondary_gap_days={secondary_gap_days if secondary_gap_days is not None else ''}, "
#|            f"selected_gap_days={secondary_window_gap_days}, "
#|            f"qualified_secondary_count={secondary_window_qualified_count}, "
#|            f"too_early_secondary_count={secondary_window_too_early_count}, "
#|            f"change_class={secondary_window_change_class}, "
#|            f"review_tier={secondary_window_review_tier}"
#|        )
#|
#|    algorithm_family, algorithm_symptom, detailed_code, detailed_label = choose_algorithm_family(
#|        representative_source=representative_source,
#|        representative_subtype=representative_subtype,
#|        event_type_ko=event_type,
#|        has_final_fault=has_final,
#|        has_critical_fault=has_critical,
#|        has_degradation=has_degradation,
#|        has_shadow=has_shadow,
#|    )
#|
#|    evidence_bits: list[str] = []
#|    if earliest_marker:
#|        evidence_bits.append(f"warning={earliest_marker}")
#|    if representative_source:
#|        evidence_bits.append(f"critical_source={representative_source}")
#|    if representative_subtype:
#|        evidence_bits.append(f"anom_subtype={representative_subtype}")
#|    if gap_days:
#|        evidence_bits.append(f"precursor_gap_days={gap_days}")
#|    if has_site_event:
#|        evidence_bits.append("site_event_signal=1")
#|    if has_group_off:
#|        evidence_bits.append("group_off_signal=1")
#|    if has_subgroup_common_cause:
#|        evidence_bits.append("subgroup_common_cause=1")
#|
#|    return PanelRuntimeMetrics(
#|        site=site,
#|        panel_id=panel_id,
#|        earliest_warning_date=format_date(earliest_warning),
#|        earliest_warning_marker=earliest_marker,
#|        retrospective_onset_date=format_date(retrospective_onset),
#|        strict_trigger_date=format_date(strict_trigger),
#|        first_final_fault_date=format_date(first_final_fault),
#|        dead_diag_date=format_date(first_true_date(panel_gate, "group_off_date")),
#|        onset_confidence=onset_confidence,
#|        onset_method=onset_method,
#|        패널고장여부_ko=fault_status,
#|        전조흔적_flag=precursor_flag,
#|        순수급작_flag=abrupt_flag,
#|        전조평가셋편입_flag=precursor_eval_flag,
#|        급작평가셋편입_flag=abrupt_eval_flag,
#|        사건유형_재판정_ko=event_type,
#|        최종고장양상_재판정_ko=terminal_pattern,
#|        재판정_근거_ko="; ".join(evidence_bits),
#|        현재표_보정필요여부_flag=current_needs_correction,
#|        대표critical_source=representative_source,
#|        대표anom_level=representative_level,
#|        대표anom_subtype=representative_subtype,
#|        algorithm_family_ko=algorithm_family,
#|        algorithm_symptom_ko=algorithm_symptom,
#|        detailed_fault_code=detailed_code,
#|        detailed_fault_label_ko=detailed_label,
#|        gap_days=gap_days,
#|        degradation_onset_backdate_guard_flag=degradation_guard_flag,
#|        degradation_onset_backdate_guard_name=(
#|            DEGRADATION_ONSET_BACKDATE_GUARD_NAME if degradation_guard_flag else ""
#|        ),
#|        degradation_onset_backdate_guard_reason=degradation_guard_reason,
#|        degradation_onset_backdate_guard_degrade_days=degradation_guard_degrade_days,
#|        secondary_window_candidate_flag=secondary_window_candidate_flag,
#|        secondary_window_selected_onset_date=(
#|            format_date(secondary_window_onset) if secondary_window_candidate_flag else ""
#|        ),
#|        secondary_window_selected_marker=secondary_window_marker if secondary_window_candidate_flag else "",
#|        secondary_window_selected_gap_days=(
#|            secondary_window_gap_days if secondary_window_candidate_flag else 0
#|        ),
#|        secondary_window_qualified_count=secondary_window_qualified_count,
#|        secondary_window_too_early_count=secondary_window_too_early_count,
#|        secondary_window_change_class=secondary_window_change_class,
#|        secondary_window_review_tier=secondary_window_review_tier,
#|        secondary_window_reason=secondary_window_reason,
#|        common_cause_anchor_date=format_date(common_cause_anchor_ts),
#|        common_cause_anchor_kind=common_cause_anchor_kind,
#|        has_final_fault=has_final,
#|        has_critical_fault=has_critical,
#|        has_fault_like=has_fault_like,
#|        has_degradation=has_degradation,
#|        has_shadow=has_shadow,
#|        has_vdrop=has_vdrop,
#|        has_site_event=has_site_event,
#|        has_group_off=has_group_off,
#|        has_subgroup_common_cause=has_subgroup_common_cause,
#|        has_common_cause_history=has_common_cause_history,
#|        has_strict_trigger_proximal_common_cause=has_strict_trigger_proximal_common_cause,
#|        has_warning_proximal_common_cause=has_warning_proximal_common_cause,
#|        has_trigger_proximal_common_cause=has_trigger_proximal_common_cause,
#|    )
#|
#|
#|def display_heuristic_name(value: object) -> str:
#|    return shared_display_heuristic_name(value)
#|
#|
#|def display_heuristic_note(value: object) -> str:
#|    return shared_display_heuristic_note(value)
#|
#|
#|def display_family_name(value: object) -> str:
#|    text = normalize_text(value)
#|    if text == "불충분":
#|        return ""
#|    return text
#|
#|
#|def choose_display_precursor_date(
#|    event_type_ko: object,
#|    interpreted_onset_date: object,
#|    first_warning_date: object,
#|) -> str:
#|    if normalize_text(event_type_ko) != "전조형 고장":
#|        return ""
#|    onset_date = normalize_text(interpreted_onset_date)
#|    if onset_date:
#|        return onset_date
#|    return normalize_text(first_warning_date)
#|
#|
#|def choose_display_fault_date(
#|    fault_date: object,
#|    strict_trigger_date: object,
#|    first_final_fault_date: object,
#|) -> str:
#|    for candidate in [fault_date, strict_trigger_date, first_final_fault_date]:
#|        text = normalize_text(candidate)
#|        if text:
#|            return text
#|    return ""
#|
#|
#|def load_runtime_core_from_workspace(workspace_root: Path, site: str) -> pd.DataFrame:
#|    core_path = workspace_root / "data" / site / "out" / "panel_day_core.csv"
#|    core_df = read_csv(core_path)
#|    ensure_columns(
#|        core_df,
#|        ["panel_id", "date", "final_fault", "critical_fault", "fault_like_day", "critical_source"],
#|        core_path.name,
#|    )
#|    core_df["panel_id"] = core_df["panel_id"].astype(str)
#|    core_df["date"] = pd.to_datetime(core_df["date"], errors="coerce")
#|    return core_df
#|
#|
#|def representative_algorithm_fields(core_df: pd.DataFrame, panel_id: str) -> dict[str, str]:
#|    panel_df = core_df.loc[core_df["panel_id"].eq(str(panel_id))].copy().sort_values("date")
#|    if panel_df.empty:
#|        return {"커널로그 기존 알고리즘": ""}
#|    representative = representative_row(panel_df)
#|    return {"커널로그 기존 알고리즘": normalize_text(representative.get("critical_source"))}
#|
#|
#|def build_fault_table_from_outputs(
#|    workspace_root: Path,
#|    verdict_name: str,
#|    heuristic_name: str,
#|) -> pd.DataFrame:
#|    verdict_path = workspace_root / "_share" / verdict_name
#|    heuristic_path = workspace_root / "_share" / heuristic_name
#|    audit_path = workspace_root / "_share" / RUNTIME_AUDIT_OUTPUT_NAME
#|    verdict_df = read_csv(verdict_path)
#|    heuristic_df = read_csv(heuristic_path)
#|    audit_df = read_csv(audit_path)
#|    ensure_columns(
#|        verdict_df,
#|        ["site", "panel_id", "패널고장여부_ko", "사건유형_ko", "최종고장양상_ko", "커널로그_원인군_ko"],
#|        verdict_path.name,
#|    )
#|    ensure_columns(
#|        heuristic_df,
#|        ["site", "panel_id", "원인후보_top1_ko", "원인후보_top2_ko", "원인후보_top3_ko"],
#|        heuristic_path.name,
#|    )
#|    ensure_columns(
#|        audit_df,
#|        ["site", "panel_id", "earliest_warning_date", "strict_trigger_date", "first_final_fault_date"],
#|        audit_path.name,
#|    )
#|    heuristic_lookup = {
#|        (normalize_text(row["site"]), normalize_text(row["panel_id"])): row
#|        for row in heuristic_df.to_dict(orient="records")
#|    }
#|    audit_lookup = {
#|        (normalize_text(row["site"]), normalize_text(row["panel_id"])): row
#|        for row in audit_df.to_dict(orient="records")
#|    }
#|    rows: list[dict[str, str]] = []
#|    fault_rows = verdict_df.loc[verdict_df["패널고장여부_ko"].map(normalize_text).eq("고장")].copy()
#|    for row in fault_rows.to_dict(orient="records"):
#|        key = (normalize_text(row["site"]), normalize_text(row["panel_id"]))
#|        heuristic_row = heuristic_lookup.get(key)
#|        if heuristic_row is None:
#|            raise SystemExit(f"missing heuristic row for runtime fault panel: {key}")
#|        audit_row = audit_lookup.get(key, {})
#|        rows.append(
#|            {
#|                "site": key[0],
#|                "panel_id": key[1],
#|                "패널고장여부_ko": normalize_text(row["패널고장여부_ko"]),
#|                "사건유형_ko": normalize_text(row["사건유형_ko"]),
#|                "최종고장양상_ko": normalize_text(row["최종고장양상_ko"]),
#|                "커널로그_원인군_ko": display_family_name(row["커널로그_원인군_ko"]),
#|                "1순위_의심원인_ko": display_heuristic_name(heuristic_row["원인후보_top1_ko"]),
#|                "2순위_의심원인_ko": display_heuristic_name(heuristic_row["원인후보_top2_ko"]),
#|                "3순위_의심원인_ko": display_heuristic_name(heuristic_row["원인후보_top3_ko"]),
#|                "전조날짜": choose_display_precursor_date(
#|                    event_type_ko=row.get("사건유형_ko"),
#|                    interpreted_onset_date=row.get("사건해석상전조시작일"),
#|                    first_warning_date=audit_row.get("earliest_warning_date"),
#|                ),
#|                "고장날짜": choose_display_fault_date(
#|                    fault_date=row.get("세부fault_기준일"),
#|                    strict_trigger_date=audit_row.get("strict_trigger_date"),
#|                    first_final_fault_date=audit_row.get("first_final_fault_date"),
#|                ),
#|            }
#|        )
#|    return pd.DataFrame(rows).reindex(columns=RUNTIME_FAULT_OUTPUT_COLS).sort_values(["site", "panel_id"]).reset_index(drop=True)
#|
#|
#|def build_fault_preview(workspace_root: Path, fault_df: pd.DataFrame) -> pd.DataFrame:
#|    per_site_core = {
#|        site: load_runtime_core_from_workspace(workspace_root, site)
#|        for site in sorted(fault_df["site"].astype(str).unique())
#|    }
#|    rows: list[dict[str, str]] = []
#|    for _, row in fault_df.iterrows():
#|        site = normalize_text(row["site"])
#|        panel_id = normalize_text(row["panel_id"])
#|        rows.append(
#|            {
#|                "site": site,
#|                "panel_id": panel_id,
#|                "패널고장여부_ko": normalize_text(row["패널고장여부_ko"]),
#|                "사건유형_ko": normalize_text(row["사건유형_ko"]),
#|                "최종고장양상_ko": normalize_text(row["최종고장양상_ko"]),
#|                "전조날짜": normalize_text(row.get("전조날짜")),
#|                "고장날짜": normalize_text(row.get("고장날짜")),
#|                "커널로그_원인군_ko": display_family_name(row["커널로그_원인군_ko"]),
#|                "1순위_의심원인_ko": normalize_text(row["1순위_의심원인_ko"]),
#|                "2순위_의심원인_ko": normalize_text(row["2순위_의심원인_ko"]),
#|                "3순위_의심원인_ko": normalize_text(row["3순위_의심원인_ko"]),
#|                **representative_algorithm_fields(per_site_core[site], panel_id),
#|            }
#|        )
#|    return pd.DataFrame(rows).reindex(columns=RUNTIME_PREVIEW_OUTPUT_COLS)
#|
#|
#|def compare_fault_table_to_reference(fault_df: pd.DataFrame, reference_path: Path) -> dict[str, object]:
#|    payload = {
#|        "reference_path": str(reference_path),
#|        "reference_available": reference_path.exists(),
#|        "exact_match": False,
#|        "row_key_match": False,
#|        "decision_columns_match": False,
#|        "overlap_decision_columns_match": False,
#|        "overlap_exact_match": False,
#|        "reference_row_count": 0,
#|        "candidate_row_count": int(len(fault_df)),
#|        "matched_row_key_count": 0,
#|        "diff_columns": [],
#|        "overlap_diff_columns": [],
#|    }
#|    if not reference_path.exists():
#|        return payload
#|    reference_df = read_csv(reference_path).sort_values(["site", "panel_id"]).reset_index(drop=True)
#|    candidate_df = fault_df.sort_values(["site", "panel_id"]).reset_index(drop=True)
#|    reference_keys = list(zip(reference_df["site"].astype(str), reference_df["panel_id"].astype(str)))
#|    candidate_keys = list(zip(candidate_df["site"].astype(str), candidate_df["panel_id"].astype(str)))
#|    payload["reference_row_count"] = int(len(reference_df))
#|    payload["candidate_row_count"] = int(len(candidate_df))
#|    payload["row_key_match"] = reference_keys == candidate_keys
#|    payload["matched_row_key_count"] = int(len(set(reference_keys) & set(candidate_keys)))
#|    diff_columns: list[str] = []
#|    if len(reference_df) != len(candidate_df):
#|        diff_columns.append("__row_count__")
#|    else:
#|        for column in RUNTIME_DECISION_COMPARE_COLS:
#|            if column not in reference_df.columns:
#|                diff_columns.append(f"missing_reference:{column}")
#|                continue
#|            left = reference_df[column].fillna("").astype(str)
#|            right = candidate_df[column].fillna("").astype(str)
#|            if not left.equals(right):
#|                diff_columns.append(column)
#|    payload["diff_columns"] = diff_columns
#|    payload["exact_match"] = not diff_columns and payload["row_key_match"]
#|    decision_columns = ["패널고장여부_ko", "사건유형_ko", "최종고장양상_ko"]
#|    payload["decision_columns_match"] = payload["row_key_match"] and not any(
#|        column in diff_columns for column in decision_columns
#|    )
#|    overlap = reference_df.merge(candidate_df, on=["site", "panel_id"], how="inner", suffixes=("_reference", "_candidate"))
#|    overlap_diff_columns: list[str] = []
#|    if not overlap.empty:
#|        for column in RUNTIME_DECISION_COMPARE_COLS[2:]:
#|            left = overlap[f"{column}_reference"].fillna("").astype(str)
#|            right = overlap[f"{column}_candidate"].fillna("").astype(str)
#|            if not left.equals(right):
#|                overlap_diff_columns.append(column)
#|    payload["overlap_diff_columns"] = overlap_diff_columns
#|    payload["overlap_exact_match"] = payload["matched_row_key_count"] == payload["reference_row_count"] and not overlap_diff_columns
#|    payload["overlap_decision_columns_match"] = payload["matched_row_key_count"] == payload["reference_row_count"] and not any(
#|        column in overlap_diff_columns for column in decision_columns
#|    )
#|    if payload["exact_match"]:
#|        payload["status_ko"] = "fixed fault reference exact match"
#|    elif payload["overlap_decision_columns_match"]:
#|        payload["status_ko"] = "overlap decision columns preserved and raw-only candidate universe expanded by design"
#|    elif payload["matched_row_key_count"] > 0:
#|        payload["status_ko"] = "overlap exists but decision drift detected"
#|    else:
#|        payload["status_ko"] = "no overlapping fixed reference keys"
#|    return payload
# pvdiag_payload_end
# endregion
# region payload: runtime_reference_artifact
# pvdiag_payload_file {"bytes": 1293, "endswith_newline": false, "lines": 21, "path": "release/conalog_full_runtime_v1/package/artifacts/fault6_fixed_result_provenance_v1.json", "role": "runtime_reference_artifact", "sha256": "174cf698b8c9ad7df916b4c3bfb6bd2b590611556def18e05a990bd5626b6d15"}
#|{
#|  "generated_at_utc": "2026-05-20T06:51:16Z",
#|  "source_chain_ko": "frozen verdict plus frozen heuristic with integrated display-name mapping",
#|  "verdict_source_path": "_share/panel_day_engine_panel_multiaxis_verdict_v1.csv",
#|  "heuristic_source_path": "_share/panel_day_engine_cause_candidate_heuristics_v1.csv",
#|  "legacy_integrated_source_path": "_share/panel_day_engine_integrated_result_table_v1.csv",
#|  "fault_row_count": 6,
#|  "display_name_map": {
#|    "다이오드·서브스트링형": "다이오드·서브스트링 이상형",
#|    "접속·부분개방형": "접속 불량·부분 개방형",
#|    "센서·피드백형": "센서·계측 피드백 이상형",
#|    "제어응답형": "제어 응답 이상형",
#|    "전력변환부형": "전력변환부 이상형",
#|    "외부계통교란형": "외부 계통 교란형"
#|  },
#|  "legacy_integrated_exact_match": true,
#|  "legacy_integrated_diff_columns": [],
#|  "note_ko": "이 provenance는 runtime pack의 fault6 고정 결과표가 더 이상 integrated snapshot을 직접 절단하지 않고, frozen verdict와 frozen heuristic를 현재 integrated builder와 동일한 표시명 매핑으로 다시 조합해 만든 것임을 설명한다.",
#|  "legacy_fault_row_count": 6,
#|  "legacy_integrated_compare_status_ko": "exact match"
#|}
# pvdiag_payload_end
# endregion
# region payload: runtime_reference_artifact
# pvdiag_payload_file {"bytes": 1341, "endswith_newline": true, "lines": 7, "path": "release/conalog_full_runtime_v1/package/artifacts/fault6_fixed_result_table_v1.csv", "role": "runtime_reference_artifact", "sha256": "93eb336dfdbba36159e802726e9e94d98f782b74ef2e62b5cea46f4a22f93581"}
#|﻿site,panel_id,패널고장여부_ko,사건유형_ko,최종고장양상_ko,커널로그_원인군_ko,1순위_의심원인_ko,2순위_의심원인_ko,3순위_의심원인_ko
#|conalog,7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0,고장,전조형 고장,진행성 악화,다이오드형,다이오드·서브스트링 이상형,부분음영형,열화형
#|conalog,c42997a6-5881-47e7-9035-7de8a2673b54.1.1,고장,전조형 고장,급격 종료,개방/장치이상형,센서·계측 피드백 이상형,접속 불량·부분 개방형,제어 응답 이상형
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7,고장,급작 고장,급작 발생,다이오드형,다이오드·서브스트링 이상형,센서·계측 피드백 이상형,접속 불량·부분 개방형
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16,고장,급작 고장,급작 발생,다이오드형,다이오드·서브스트링 이상형,센서·계측 피드백 이상형,접속 불량·부분 개방형
#|ktc_ess,10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12,고장,급작 고장,급작 발생,다이오드형,다이오드·서브스트링 이상형,부분음영형,접속 불량·부분 개방형
#|ktc_ess,70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4,고장,전조형 고장,진행성 악화,모듈손상형,열화형,센서·계측 피드백 이상형,다이오드·서브스트링 이상형
# pvdiag_payload_end
# endregion
# region payload: runtime_reference_artifact
# pvdiag_payload_file {"bytes": 1125, "endswith_newline": true, "lines": 7, "path": "release/conalog_full_runtime_v1/package/artifacts/fault6_label_and_algorithm_preview_v1.csv", "role": "runtime_reference_artifact", "sha256": "58e321a5bfcd7bf62e398aecde38701a533c5a64cbef2d18935b57bc4a39e20a"}
#|﻿site,panel_id,전조날짜,고장 기준일,운영 판정,급락 종결 관측,점진 저하 누적,사건 종결 요약,상위 해석 후보,기존 알고리즘 source
#|conalog,7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0,2024-11-06,2024-11-26,확정,없음,있음,전조 후 진행 악화,다이오드·서브스트링 이상형,panel-bypass
#|conalog,c42997a6-5881-47e7-9035-7de8a2673b54.1.1,2025-01-20,2025-03-21,확정,있음,있음,전조 후 급격 종료,센서·계측 피드백 이상형,disconnection
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7,전조없음,2025-06-08,확정,있음,없음,급작 발생,다이오드·서브스트링 이상형,panel-bypass
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16,전조없음,2025-06-08,확정,있음,없음,급작 발생,다이오드·서브스트링 이상형,panel-bypass
#|ktc_ess,10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12,전조없음,2025-08-16,확정,있음,없음,급작 발생,다이오드·서브스트링 이상형,미검출
#|ktc_ess,70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4,2025-01-25,2025-02-02,확정,없음,있음,전조 후 진행 악화,열화형,미검출
# pvdiag_payload_end
# endregion
# region payload: runtime_reference_artifact
# pvdiag_payload_file {"bytes": 2236, "endswith_newline": false, "lines": 65, "path": "release/conalog_full_runtime_v1/package/artifacts/input_baseline_manifest_v1.json", "role": "runtime_reference_artifact", "sha256": "8f6e69e526de55fb976e0fd9ecb5c1304816c3d3d48a7f8ef758989d6914ee2c"}
#|{
#|  "sites": {
#|    "conalog": {
#|      "file_count": 536,
#|      "total_bytes": 3831367301,
#|      "first_filenames": [
#|        "2024-09-06-커널로그1호-5m.csv",
#|        "2024-09-07-커널로그1호-5m.csv",
#|        "2024-09-08-커널로그1호-5m.csv",
#|        "2024-09-09-커널로그1호-5m.csv",
#|        "2024-09-10-커널로그1호-5m.csv"
#|      ],
#|      "last_filenames": [
#|        "ae_simple_ews_warnings.csv",
#|        "ae_simple_fault_candidates.csv",
#|        "ae_simple_panel_alarms.csv",
#|        "ae_simple_prefault_B_daily.csv",
#|        "ae_simple_scores.csv"
#|      ],
#|      "min_date": "2024-09-06",
#|      "max_date": "2026-02-18"
#|    },
#|    "gangui": {
#|      "file_count": 325,
#|      "total_bytes": 1551009589,
#|      "first_filenames": [
#|        "2025-04-08-극동대학교 강의동-5m.csv",
#|        "2025-04-09-극동대학교 강의동-5m.csv",
#|        "2025-04-10-극동대학교 강의동-5m.csv",
#|        "2025-04-11-극동대학교 강의동-5m.csv",
#|        "2025-04-12-극동대학교 강의동-5m.csv"
#|      ],
#|      "last_filenames": [
#|        "ae_simple_ews_warnings.csv",
#|        "ae_simple_fault_candidates.csv",
#|        "ae_simple_panel_alarms.csv",
#|        "ae_simple_prefault_B_daily.csv",
#|        "ae_simple_scores.csv"
#|      ],
#|      "min_date": "2025-04-08",
#|      "max_date": "2026-02-19"
#|    },
#|    "ktc_ess": {
#|      "file_count": 541,
#|      "total_bytes": 2101249399,
#|      "first_filenames": [
#|        "2024-08-13-KTC ESS시험동 옥상-5m.csv",
#|        "2024-08-14-KTC ESS시험동 옥상-5m.csv",
#|        "2024-08-15-KTC ESS시험동 옥상-5m.csv",
#|        "2024-08-16-KTC ESS시험동 옥상-5m.csv",
#|        "2024-08-17-KTC ESS시험동 옥상-5m.csv"
#|      ],
#|      "last_filenames": [
#|        "ae_simple_ews_warnings.csv",
#|        "ae_simple_fault_candidates.csv",
#|        "ae_simple_panel_alarms.csv",
#|        "ae_simple_prefault_B_daily.csv",
#|        "ae_simple_scores.csv"
#|      ],
#|      "min_date": "2024-08-13",
#|      "max_date": "2026-02-19"
#|    }
#|  },
#|  "note_ko": "이 manifest는 고정 fault6 결과표가 만들어진 현재 baseline raw corpus의 경량 fingerprint다. target 환경에서 파일 수/총용량/날짜 범위를 비교해 exact replay 여부를 점검한다."
#|}
# pvdiag_payload_end
# endregion
# region payload: runtime_reference_artifact
# pvdiag_payload_file {"bytes": 468, "endswith_newline": true, "lines": 3, "path": "release/conalog_full_runtime_v1/package/artifacts/ktc_fault2_label_and_algorithm_preview_v1.csv", "role": "runtime_reference_artifact", "sha256": "c2bc0f2619ae9f58d57ae2142d7f040ffa5594c0f23e2623dfb0c4bc3c03d3af"}
#|﻿site,panel_id,전조날짜,고장 기준일,운영 판정,급락 종결 관측,점진 저하 누적,사건 종결 요약,상위 해석 후보,기존 알고리즘 source
#|ktc_ess,10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12,전조없음,2025-08-16,확정,있음,없음,급작 발생,다이오드·서브스트링 이상형,미검출
#|ktc_ess,70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4,2025-01-25,2025-02-02,확정,없음,있음,전조 후 진행 악화,열화형,미검출
# pvdiag_payload_end
# endregion
# region payload: runtime_reference_artifact
# pvdiag_payload_file {"bytes": 2864, "endswith_newline": false, "lines": 99, "path": "release/conalog_full_runtime_v1/package/artifacts/panel_day_core_baseline_digest_v1.json", "role": "runtime_reference_artifact", "sha256": "6b45552c16ce97b5ace20435e5dc811ed47074be5fd27111010cc915e7b3dcdf"}
#|{
#|  "generated_at_utc": "2026-05-20T06:51:16Z",
#|  "sites": {
#|    "conalog": {
#|      "columns": [
#|        "date",
#|        "panel_id",
#|        "confirmed_fault",
#|        "critical_fault",
#|        "critical_source",
#|        "final_fault",
#|        "anom_level",
#|        "anom_subtype"
#|      ],
#|      "row_count": 155723,
#|      "digest_sha256": "f8a5640a480d098bf791f21936345ff5c990470be27418be02eec9a00cbb9309",
#|      "critical_source_counts": {
#|        "legacy": 69,
#|        "none": 155323,
#|        "vdrop": 295,
#|        "vdrop_suspect": 36
#|      },
#|      "anom_level_counts": {
#|        "confirmed_fault": 504,
#|        "degraded_or_shadow": 58,
#|        "fault_like": 46,
#|        "normal": 155096,
#|        "shadow_like": 19
#|      },
#|      "confirmed_fault_true_count": 428,
#|      "critical_fault_true_count": 76,
#|      "final_fault_true_count": 504,
#|      "source_path": "data/conalog/out/panel_day_core.csv"
#|    },
#|    "gangui": {
#|      "columns": [
#|        "date",
#|        "panel_id",
#|        "confirmed_fault",
#|        "critical_fault",
#|        "critical_source",
#|        "final_fault",
#|        "anom_level",
#|        "anom_subtype"
#|      ],
#|      "row_count": 57608,
#|      "digest_sha256": "fb0837562dc01943a6bf3aa22b9467635f4cd50bef276954b05ac213eac4123d",
#|      "critical_source_counts": {
#|        "legacy": 393,
#|        "none": 56528,
#|        "vdrop": 664,
#|        "vdrop_suspect": 23
#|      },
#|      "anom_level_counts": {
#|        "confirmed_fault": 664,
#|        "degraded_or_shadow": 74,
#|        "fault_like": 65,
#|        "group_off_like": 91,
#|        "normal": 56710,
#|        "shadow_like": 4
#|      },
#|      "confirmed_fault_true_count": 255,
#|      "critical_fault_true_count": 616,
#|      "final_fault_true_count": 664,
#|      "source_path": "data/gangui/out/panel_day_core.csv"
#|    },
#|    "ktc_ess": {
#|      "columns": [
#|        "date",
#|        "panel_id",
#|        "confirmed_fault",
#|        "critical_fault",
#|        "critical_source",
#|        "final_fault",
#|        "anom_level",
#|        "anom_subtype"
#|      ],
#|      "row_count": 86688,
#|      "digest_sha256": "e7e3a6a335122ad36f820984953086dd35b4bbfb2d113bef96fa996a756acab5",
#|      "critical_source_counts": {
#|        "legacy": 2,
#|        "none": 86379,
#|        "vdrop": 307
#|      },
#|      "anom_level_counts": {
#|        "confirmed_fault": 122,
#|        "degraded_or_shadow": 231,
#|        "fault_like": 31,
#|        "normal": 86297,
#|        "shadow_like": 7
#|      },
#|      "confirmed_fault_true_count": 0,
#|      "critical_fault_true_count": 191,
#|      "final_fault_true_count": 122,
#|      "source_path": "data/ktc_ess/out/panel_day_core.csv"
#|    }
#|  },
#|  "note_ko": "이 digest는 baseline raw corpus에서 이미 산출된 panel_day_core.csv의 정규화 hash/reference다. runtime pack이 동일 baseline 입력으로 재실행될 때 engine core output이 같은지 shadow compare할 때 사용한다."
#|}
# pvdiag_payload_end
# endregion
# region payload: runtime_reference_artifact
# pvdiag_payload_file {"bytes": 4238, "endswith_newline": false, "lines": 84, "path": "release/conalog_full_runtime_v1/package/artifacts/runtime_chain_dependency_audit_v1.json", "role": "runtime_reference_artifact", "sha256": "00766bb59ecaacf8c087b44a02fe33d40fb6c7cdd068e0a91ec53fa858aa2c9d"}
#|{
#|  "generated_at_utc": "2026-05-20T06:51:20Z",
#|  "runtime_live_full_chain_ready_flag": false,
#|  "current_pack_mode_ko": "engine_live_plus_fixed_fault_artifacts",
#|  "hard_cycle": {
#|    "verified_flag": true,
#|    "nodes": [
#|      "build_panel_day_engine_panel_multiaxis_verdict_v1.py",
#|      "build_panel_day_engine_fault_panel_event_audit_v1.py"
#|    ],
#|    "verdict_requires": [
#|      "panel_day_engine_fault_panel_event_audit_v1.csv",
#|      "사건유형_재판정_ko",
#|      "최종고장양상_재판정_ko",
#|      "재판정_근거_ko"
#|    ],
#|    "fault_event_audit_requires": [
#|      "panel_day_engine_panel_multiaxis_verdict_v1.csv",
#|      "패널고장여부_ko",
#|      "사건유형_ko",
#|      "최종고장양상_ko",
#|      "전조흔적_flag",
#|      "순수급작_flag",
#|      "전조평가셋편입_flag",
#|      "급작평가셋편입_flag"
#|    ],
#|    "impact_ko": "현재 구조 그대로는 verdict와 fault_event_audit가 서로를 선행 입력으로 요구하므로, integrated snapshot 없이 단방향 live runtime chain을 바로 만들 수 없다."
#|  },
#|  "required_runtime_layers": [
#|    "pv_ae/panel_day_engine.py",
#|    "build_panel_day_engine_panel_multiaxis_verdict_v1.py",
#|    "build_panel_day_engine_gpvs_evidence_pack_v1.py",
#|    "build_panel_day_engine_cause_candidate_heuristics_v1.py"
#|  ],
#|  "required_verdict_share_inputs": [
#|    "panel_day_engine_operator_workflow_default_v1.csv",
#|    "panel_day_engine_abrupt6_symptom_map_v1.csv",
#|    "panel_day_engine_kernellog_project_mapping_v1.csv",
#|    "panel_day_engine_gpv7_perf_summary_v1.csv",
#|    "panel_day_engine_project_final_decision_pack_v1.csv",
#|    "panel_day_engine_precursor_onset_truth_v1.csv",
#|    "panel_day_engine_non_precursor_performance_cases_v1.csv",
#|    "panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv",
#|    "panel_day_engine_gpvs_panel_attach_inventory_v1.csv",
#|    "panel_day_engine_gpvs_panel_attach_feasibility_v1.csv",
#|    "panel_day_engine_gpvs_panel_attach_candidates_v1.csv",
#|    "panel_day_engine_precursor_abrupt_consistency_cases_v1.csv",
#|    "panel_day_engine_precursor_abrupt_consistency_summary_v1.csv",
#|    "panel_day_engine_precursor_abrupt_consistency_recommendation_v1.csv",
#|    "panel_day_engine_c42997_1_1_forensic_summary_v1.csv",
#|    "panel_day_engine_fault_panel_event_audit_v1.csv",
#|    "panel_day_engine_detailed_fault_bridge_audit_v1.csv",
#|    "panel_day_engine_detailed_fault_bridge_summary_v1.csv",
#|    "panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv",
#|    "panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv",
#|    "panel_day_engine_gpvs_detailed_type_realpanel_sanity_v1.csv",
#|    "panel_day_engine_gpvs_mlpe_panel_agreement_v1.csv",
#|    "panel_day_engine_gpvs_canonical_dictionary_v1.csv",
#|    "panel_day_engine_gpvs_mlpe_fault_matching_table_v1.csv",
#|    "panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv"
#|  ],
#|  "required_gpvs_evidence_inputs": [
#|    "panel_day_engine_panel_multiaxis_verdict_v1.csv",
#|    "panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv",
#|    "panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv",
#|    "panel_day_engine_gpvs_mlpe_fault_matching_table_v1.csv",
#|    "panel_day_engine_gpvs_mlpe_fault_matching_summary_v1.csv"
#|  ],
#|  "required_heuristic_inputs": [
#|    "panel_day_engine_gpvs_evidence_pack_v1.csv",
#|    "panel_day_engine_panel_multiaxis_verdict_v1.csv"
#|  ],
#|  "required_fault_event_audit_inputs": [
#|    "panel_day_engine_panel_multiaxis_verdict_v1.csv",
#|    "panel_day_engine_abrupt6_symptom_map_v1.csv",
#|    "panel_day_engine_precursor_onset_truth_v1.csv",
#|    "panel_date_reaudit_working.csv",
#|    "vendor_reply_adjudication_latest.csv (optional)",
#|    "data/<site>/out/panel_day_core.csv",
#|    "data/<site>/out/ae_simple_local_precursor_gate_daily.csv"
#|  ],
#|  "recommended_next_step_ko": "runtime chain에서는 fault_event_audit를 validation-only로 분리하고, 별도 shadow-compare 경로에서 기존 frozen chain 결과와 diff를 먼저 점검하는 것이 안전하다.",
#|  "note_ko": "이 audit는 현재 repo 기준의 full-chain live runtime blocker를 문서화한 것이다. pack 자체의 공식 결과표 의미는 바꾸지 않고, 왜 아직 fixed fault artifact를 함께 들고 가는지 설명한다."
#|}
# pvdiag_payload_end
# endregion
# region payload: runtime_reference_artifact
# pvdiag_payload_file {"bytes": 3941, "endswith_newline": true, "lines": 85, "path": "release/conalog_full_runtime_v1/package/artifacts/runtime_chain_dependency_audit_v1.md", "role": "runtime_reference_artifact", "sha256": "8ee23ae291b499ffc4821d00a82cccceeae92b6d944da90bc3f0b010445008e0"}
#|# runtime_chain_dependency_audit_v1
#|
#|## 목적
#|현재 conalog full runtime pack이 어디까지 live이고, full-chain runtime으로 가려면 어떤 blocker가 남는지 고정 설명으로 남긴다.
#|
#|## 현재 상태
#|- `runtime_live_full_chain_ready_flag`: `False`
#|- `current_pack_mode_ko`: `engine_live_plus_fixed_fault_artifacts`
#|
#|## Hard Cycle
#|- verdict node: `build_panel_day_engine_panel_multiaxis_verdict_v1.py`
#|- fault-event-audit node: `build_panel_day_engine_fault_panel_event_audit_v1.py`
#|- impact: 현재 구조 그대로는 verdict와 fault_event_audit가 서로를 선행 입력으로 요구하므로, integrated snapshot 없이 단방향 live runtime chain을 바로 만들 수 없다.
#|
#|### verdict가 직접 요구하는 fault_event_audit 축
#|- `panel_day_engine_fault_panel_event_audit_v1.csv`
#|- `사건유형_재판정_ko`
#|- `최종고장양상_재판정_ko`
#|- `재판정_근거_ko`
#|
#|### fault_event_audit가 다시 요구하는 verdict 축
#|- `panel_day_engine_panel_multiaxis_verdict_v1.csv`
#|- `패널고장여부_ko`
#|- `사건유형_ko`
#|- `최종고장양상_ko`
#|- `전조흔적_flag`
#|- `순수급작_flag`
#|- `전조평가셋편입_flag`
#|- `급작평가셋편입_flag`
#|
#|## Runtime에 필요한 레이어
#|- `pv_ae/panel_day_engine.py`
#|- `build_panel_day_engine_panel_multiaxis_verdict_v1.py`
#|- `build_panel_day_engine_gpvs_evidence_pack_v1.py`
#|- `build_panel_day_engine_cause_candidate_heuristics_v1.py`
#|
#|## verdict 필수 share 입력
#|- `panel_day_engine_operator_workflow_default_v1.csv`
#|- `panel_day_engine_abrupt6_symptom_map_v1.csv`
#|- `panel_day_engine_kernellog_project_mapping_v1.csv`
#|- `panel_day_engine_gpv7_perf_summary_v1.csv`
#|- `panel_day_engine_project_final_decision_pack_v1.csv`
#|- `panel_day_engine_precursor_onset_truth_v1.csv`
#|- `panel_day_engine_non_precursor_performance_cases_v1.csv`
#|- `panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv`
#|- `panel_day_engine_gpvs_panel_attach_inventory_v1.csv`
#|- `panel_day_engine_gpvs_panel_attach_feasibility_v1.csv`
#|- `panel_day_engine_gpvs_panel_attach_candidates_v1.csv`
#|- `panel_day_engine_precursor_abrupt_consistency_cases_v1.csv`
#|- `panel_day_engine_precursor_abrupt_consistency_summary_v1.csv`
#|- `panel_day_engine_precursor_abrupt_consistency_recommendation_v1.csv`
#|- `panel_day_engine_c42997_1_1_forensic_summary_v1.csv`
#|- `panel_day_engine_fault_panel_event_audit_v1.csv`
#|- `panel_day_engine_detailed_fault_bridge_audit_v1.csv`
#|- `panel_day_engine_detailed_fault_bridge_summary_v1.csv`
#|- `panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv`
#|- `panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv`
#|- `panel_day_engine_gpvs_detailed_type_realpanel_sanity_v1.csv`
#|- `panel_day_engine_gpvs_mlpe_panel_agreement_v1.csv`
#|- `panel_day_engine_gpvs_canonical_dictionary_v1.csv`
#|- `panel_day_engine_gpvs_mlpe_fault_matching_table_v1.csv`
#|- `panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv`
#|
#|## GPVS evidence 필수 입력
#|- `panel_day_engine_panel_multiaxis_verdict_v1.csv`
#|- `panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv`
#|- `panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv`
#|- `panel_day_engine_gpvs_mlpe_fault_matching_table_v1.csv`
#|- `panel_day_engine_gpvs_mlpe_fault_matching_summary_v1.csv`
#|
#|## heuristic 필수 입력
#|- `panel_day_engine_gpvs_evidence_pack_v1.csv`
#|- `panel_day_engine_panel_multiaxis_verdict_v1.csv`
#|
#|## fault_event_audit 필수 입력
#|- `panel_day_engine_panel_multiaxis_verdict_v1.csv`
#|- `panel_day_engine_abrupt6_symptom_map_v1.csv`
#|- `panel_day_engine_precursor_onset_truth_v1.csv`
#|- `panel_date_reaudit_working.csv`
#|- `vendor_reply_adjudication_latest.csv (optional)`
#|- `data/<site>/out/panel_day_core.csv`
#|- `data/<site>/out/ae_simple_local_precursor_gate_daily.csv`
#|
#|## 권장 다음 단계
#|- runtime chain에서는 fault_event_audit를 validation-only로 분리하고, 별도 shadow-compare 경로에서 기존 frozen chain 결과와 diff를 먼저 점검하는 것이 안전하다.
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 33763, "endswith_newline": true, "lines": 115, "path": "release/conalog_full_runtime_v1/package/_share/panel_date_reaudit_working.csv", "role": "frozen_share_input", "sha256": "5013dcf4281e1656452e3850735f03111aaeba1455766244c2532af2cc14ef9d"}
#|﻿site,panel_id,strict_trigger_date,first_warning_date,retrospective_onset_date,days_earlier_than_trigger,onset_confidence,onset_method,reason_summary,vendor_reply_class,vendor_fault_family,field_confirmed_flag,dispute_type,vendor_note,review_priority,reaudited_earliest_visible_date,reaudited_first_warning_date,field_estimated_start_date,date_judgement,failure_mode_judgement,candidate_validity,review_confidence,note
#|conalog,7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0,2024-11-26,2024-11-06,2024-11-06,20,high,persistent_5of7,strict_method=critical_fault_flag|window_start=2024-09-27|first_warning=2024-11-06|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,vendor_pattern_positive,diode_like,0.0,agree_group_issue,"입력전압 27 수준, 다른 패널 43 대비 30~40% 낮음",P1,,,,,,true_positive,,초기 seed: vendor_pattern_positive / diode_like
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.15,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,field_confirmed_positive,group_or_inverter_side_like,1.0,agree_positive,"커넥터 불량으로 인버터 하나 내려감, 현장 조치 후 복구",P1,,,,,,group_side,,초기 seed: 동일 그룹 다수 0 → 인버터/커넥터 문제
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.16,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,field_confirmed_positive,group_or_inverter_side_like,1.0,agree_positive,"커넥터 불량으로 인버터 하나 내려감, 현장 조치 후 복구",P1,,,,,,group_side,,초기 seed: 동일 그룹 다수 0 → 인버터/커넥터 문제
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.17,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,field_confirmed_positive,group_or_inverter_side_like,1.0,agree_positive,"커넥터 불량으로 인버터 하나 내려감, 현장 조치 후 복구",P1,,,,,,group_side,,초기 seed: 동일 그룹 다수 0 → 인버터/커넥터 문제
#|conalog,45dfa600-79b7-428e-95d3-22345a068986.1.0,2024-12-29,2024-11-27,2024-12-29,0,medium,strict_trigger_fallback,strict_method=critical_fault_flag|window_start=2024-10-30|first_warning=2024-11-27|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,vendor_rejected,none_visible,0.0,ours_positive_vendor_rejected,이상으로 보이는 것이 전혀 없어 왜 후보인지 모르겠다고 답변,P1,,,,,,false_positive,,assistant_seed: vendor_rejected / none_visible / monitor_only
#|conalog,45dfa600-79b7-428e-95d3-22345a068986.1.1,2025-01-19,2024-11-20,2024-12-23,27,high,persistent_5of7,strict_method=critical_fault_flag|window_start=2024-11-20|first_warning=2024-11-20|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,vendor_rejected,none_visible,0.0,ours_positive_vendor_rejected,이상으로 보이는 것이 전혀 없어 왜 후보인지 모르겠다고 답변,P1,,,,,,false_positive,,assistant_seed: vendor_rejected / none_visible / monitor_only
#|conalog,d15b9e13-4117-49ae-a78f-7ace013e48de.0.0,2025-02-19,2025-01-01,2025-02-19,0,medium,strict_trigger_fallback,strict_method=critical_fault_flag|window_start=2024-12-21|first_warning=2025-01-01|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,vendor_rejected,none_visible,0.0,ours_positive_vendor_rejected,이상으로 보이는 것이 전혀 없어 왜 후보인지 모르겠다고 답변,P1,,,,,,false_positive,,assistant_seed: vendor_rejected / none_visible / monitor_only
#|conalog,c42997a6-5881-47e7-9035-7de8a2673b54.1.1,2025-03-21,2025-01-20,2025-01-20,60,high,persistent_5of7,strict_method=confirmed_fault_flag|window_start=2025-01-20|first_warning=2025-01-20|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,vendor_likely_positive,open_or_device_issue_like,0.0,agree_positive,"전압 0, 패널이나 장비 문제로 볼 수 있는 상태, 현장확인 안됨",P1,,,,,,needs_more_info,,assistant_seed: 전압 0/장비 문제 가능성은 있으나 현장확인 부족 → 추가 확인 필요
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7,2025-06-08,2025-06-08,2025-06-08,0,medium,strict_trigger_fallback,strict_method=critical_fault_flag|window_start=2025-04-09|first_warning=2025-06-08|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,vendor_pattern_positive,diode_like,0.0,agree_group_issue,다이오드 손상으로 파악하는 경우,P1,,,,,,true_positive,,초기 seed: vendor_pattern_positive / diode_like
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16,2025-06-08,2025-06-07,2025-06-08,0,medium,strict_trigger_fallback,strict_method=critical_fault_flag|window_start=2025-04-09|first_warning=2025-06-07|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,vendor_pattern_positive,diode_like,0.0,agree_group_issue,다이오드 손상으로 파악하는 경우,P1,,,,,,true_positive,,초기 seed: vendor_pattern_positive / diode_like
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.9,2025-10-27,2025-08-28,2025-08-28,60,high,persistent_5of7,strict_method=critical_fault_flag|window_start=2025-08-28|first_warning=2025-08-28|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,vendor_rejected,none_visible,0.0,ours_positive_vendor_rejected,이상으로 보이는 것이 전혀 없어 왜 후보인지 모르겠다고 답변,P1,,,,,,false_positive,,assistant_seed: vendor_rejected / none_visible / singleton_monitor_hold
#|gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.4.15,2025-11-11,2025-09-13,2025-11-11,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2025-09-12|first_warning=2025-09-13|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,vendor_likely_positive,group_or_inverter_side_like,0.0,agree_positive,"여러 장비가 0, 인버터 관련 작업 추정, O&M 정보 없음",P1,,,,,,group_side,,assistant_seed: 다수 장비 0 / group_or_inverter_side_like → 그룹·인버터 측 문제
#|ktc_ess,70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4,2025-02-02,2024-12-25,2025-01-25,8,high,persistent_5of7,strict_method=critical_fault_flag|window_start=2024-12-04|first_warning=2024-12-25|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,vendor_likely_positive,module_damage_like,0.0,agree_positive,모듈 손상된 것 같으나 현장확인 안함,P1,,,,,,true_positive,,assistant_seed: vendor_likely_positive / module_damage_like / maintenance_candidate
#|ktc_ess,10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12,2025-08-16,2025-08-12,2025-08-16,0,medium,strict_trigger_fallback,strict_method=critical_fault_flag|window_start=2025-06-17|first_warning=2025-08-12|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,vendor_pattern_positive,diode_like,0.0,agree_group_issue,다이오드 손상으로 파악하는 경우,P1,,,,,,true_positive,,초기 seed: vendor diode_like → 패널 문제 가능
#|conalog,21ca22d1-a6fb-40cd-805c-cd3dcfcbb4ff.0.0,2024-12-06,2024-11-11,2024-11-11,25,high,persistent_5of7,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-11-11|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P2,,,,,,,,
#|conalog,c42997a6-5881-47e7-9035-7de8a2673b54.0.0,2025-04-26,2025-02-25,2025-02-25,60,high,persistent_5of7,strict_method=critical_fault_flag|window_start=2025-02-25|first_warning=2025-02-25|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P2,,,,,,,,
#|conalog,c42997a6-5881-47e7-9035-7de8a2673b54.2.0,2025-05-28,2025-03-29,2025-03-29,60,high,persistent_5of7,strict_method=critical_fault_flag|window_start=2025-03-29|first_warning=2025-03-29|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P2,,,,,,,,
#|gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.4.11,2025-11-11,2025-09-12,2025-09-20,52,high,persistent_5of7,strict_method=critical_fault_flag|window_start=2025-09-12|first_warning=2025-09-12|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P2,,,,,,,,
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.1.2,2025-11-11,2025-09-12,2025-09-12,60,high,persistent_5of7,strict_method=confirmed_fault_flag|window_start=2025-09-12|first_warning=2025-09-12|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P2,,,,,,,,
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.11,2025-11-11,2025-09-12,2025-09-20,52,high,persistent_5of7,strict_method=confirmed_fault_flag|window_start=2025-09-12|first_warning=2025-09-12|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P2,,,,,,,,
#|gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.0.15,2025-11-17,2025-09-18,2025-09-18,60,high,persistent_5of7,strict_method=critical_fault_flag|window_start=2025-09-18|first_warning=2025-09-18|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P2,,,,,,,,
#|conalog,21ca22d1-a6fb-40cd-805c-cd3dcfcbb4ff.0.1,2024-12-06,2024-11-14,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-11-14|recovery_reset=yes|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,21ca22d1-a6fb-40cd-805c-cd3dcfcbb4ff.0.2,2024-12-06,2024-11-11,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-11-11|recovery_reset=yes|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,21ca22d1-a6fb-40cd-805c-cd3dcfcbb4ff.0.3,2024-12-06,2024-11-13,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-11-13|recovery_reset=yes|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,21ca22d1-a6fb-40cd-805c-cd3dcfcbb4ff.0.4,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,21ca22d1-a6fb-40cd-805c-cd3dcfcbb4ff.1.0,2024-12-06,2024-11-09,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-11-09|recovery_reset=yes|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,21ca22d1-a6fb-40cd-805c-cd3dcfcbb4ff.1.1,2024-12-06,2024-11-09,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-11-09|recovery_reset=yes|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,21ca22d1-a6fb-40cd-805c-cd3dcfcbb4ff.1.2,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,21ca22d1-a6fb-40cd-805c-cd3dcfcbb4ff.1.3,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,21ca22d1-a6fb-40cd-805c-cd3dcfcbb4ff.1.4,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,21ca22d1-a6fb-40cd-805c-cd3dcfcbb4ff.2.0,2024-12-06,2024-11-09,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-11-09|recovery_reset=yes|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,21ca22d1-a6fb-40cd-805c-cd3dcfcbb4ff.2.1,2024-12-06,2024-11-09,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-11-09|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,21ca22d1-a6fb-40cd-805c-cd3dcfcbb4ff.2.2,2024-12-06,2024-11-09,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-11-09|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,21ca22d1-a6fb-40cd-805c-cd3dcfcbb4ff.2.3,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,21ca22d1-a6fb-40cd-805c-cd3dcfcbb4ff.2.4,2024-12-06,2024-11-09,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-11-09|recovery_reset=yes|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,7f7dd654-2760-4eb2-a197-3ebb72b85cda.1.0,2024-12-06,2024-11-09,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-11-09|recovery_reset=yes|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,7f7dd654-2760-4eb2-a197-3ebb72b85cda.1.1,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,7f7dd654-2760-4eb2-a197-3ebb72b85cda.1.2,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,7f7dd654-2760-4eb2-a197-3ebb72b85cda.1.3,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,7f7dd654-2760-4eb2-a197-3ebb72b85cda.1.5,2024-12-06,2024-11-09,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-11-09|recovery_reset=yes|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.0.10,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.0.11,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.0.12,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.0.13,2024-12-06,2024-12-06,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-06|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.0.14,2024-12-06,2024-11-06,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-11-06|recovery_reset=yes|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.0.15,2024-12-06,2024-12-06,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-06|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.0.16,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.0.17,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.0.18,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.1.10,2024-12-06,2024-11-09,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-11-09|recovery_reset=yes|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.1.11,2024-12-06,2024-11-06,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-11-06|recovery_reset=yes|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.1.12,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.1.13,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.1.14,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.1.15,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.1.16,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.1.17,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.1.18,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.2.10,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.2.11,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.2.12,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.2.13,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.2.14,2024-12-06,2024-12-06,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-06|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.2.15,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.2.16,2024-12-06,2024-12-06,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-06|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.2.17,2024-12-06,2024-12-06,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-06|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,a481180a-e538-42e2-b1aa-95f251c531bc.2.18,2024-12-06,2024-12-06,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-06|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.11,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.12,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.13,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.14,2024-12-06,2024-11-13,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-11-13|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.18,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.2.10,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.2.11,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.2.12,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.2.13,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.2.14,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.2.15,2024-12-06,2024-12-06,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-06|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.2.16,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.2.17,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.2.9,2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|conalog,c42997a6-5881-47e7-9035-7de8a2673b54.1.0,2025-01-11,2025-01-04,2025-01-04,7,high,persistent_5of7,strict_method=critical_fault_flag|window_start=2024-11-12|first_warning=2025-01-04|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.4.17,2025-06-08,2025-06-07,2025-06-08,0,medium,strict_trigger_fallback,strict_method=critical_fault_flag|window_start=2025-04-09|first_warning=2025-06-07|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.2.10,2025-06-10,2025-06-07,2025-06-10,0,medium,strict_trigger_fallback,strict_method=critical_fault_flag|window_start=2025-04-11|first_warning=2025-06-07|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.3.4,2025-11-11,2025-11-11,2025-11-11,0,medium,strict_trigger_fallback,strict_method=critical_fault_flag|window_start=2025-09-12|first_warning=2025-11-11|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.3.5,2025-11-11,2025-11-11,2025-11-11,0,medium,strict_trigger_fallback,strict_method=critical_fault_flag|window_start=2025-09-12|first_warning=2025-11-11|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.4.10,2025-11-11,2025-11-03,2025-11-11,0,medium,strict_trigger_fallback,strict_method=critical_fault_flag|window_start=2025-09-12|first_warning=2025-11-03|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.4.13,2025-11-11,2025-09-16,2025-11-11,0,medium,strict_trigger_fallback,strict_method=critical_fault_flag|window_start=2025-09-12|first_warning=2025-09-16|recovery_reset=yes|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.4.2,2025-11-11,2025-10-18,2025-11-11,0,medium,strict_trigger_fallback,strict_method=critical_fault_flag|window_start=2025-09-12|first_warning=2025-10-18|recovery_reset=yes|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.1.3,2025-11-11,2025-11-11,2025-11-11,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2025-09-12|first_warning=2025-11-11|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.1.4,2025-11-11,2025-09-12,2025-11-11,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2025-09-12|first_warning=2025-09-12|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.1.5,2025-11-11,2025-11-11,2025-11-11,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2025-09-12|first_warning=2025-11-11|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.1.6,2025-11-11,2025-09-14,2025-11-11,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2025-09-12|first_warning=2025-09-14|recovery_reset=yes|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.1.7,2025-11-11,2025-09-12,2025-11-11,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2025-09-12|first_warning=2025-09-12|recovery_reset=yes|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.1.8,2025-11-11,2025-11-11,2025-11-11,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2025-09-12|first_warning=2025-11-11|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.1.9,2025-11-11,2025-11-11,2025-11-11,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2025-09-12|first_warning=2025-11-11|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.10,2025-11-11,2025-11-11,2025-11-11,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2025-09-12|first_warning=2025-11-11|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.12,2025-11-11,2025-09-20,2025-11-11,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2025-09-12|first_warning=2025-09-20|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.3,2025-11-11,2025-11-11,2025-11-11,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2025-09-12|first_warning=2025-11-11|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.9,2025-11-11,2025-11-11,2025-11-11,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2025-09-12|first_warning=2025-11-11|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.3.0,2025-11-12,2025-11-12,2025-11-12,0,medium,strict_trigger_fallback,strict_method=critical_fault_flag|window_start=2025-09-13|first_warning=2025-11-12|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.3.1,2025-11-12,2025-09-13,2025-11-12,0,medium,strict_trigger_fallback,strict_method=critical_fault_flag|window_start=2025-09-13|first_warning=2025-09-13|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.3.6,2025-11-12,2025-11-11,2025-11-12,0,medium,strict_trigger_fallback,strict_method=critical_fault_flag|window_start=2025-09-13|first_warning=2025-11-11|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.0,2025-11-12,2025-11-11,2025-11-12,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2025-09-13|first_warning=2025-11-11|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.1,2025-11-12,2025-11-11,2025-11-12,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2025-09-13|first_warning=2025-11-11|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.7,2025-11-12,2025-11-12,2025-11-12,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2025-09-13|first_warning=2025-11-12|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.4.22,2025-11-13,2025-11-11,2025-11-13,0,medium,strict_trigger_fallback,strict_method=critical_fault_flag|window_start=2025-09-14|first_warning=2025-11-11|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.4.3,2025-11-13,2025-11-11,2025-11-13,0,medium,strict_trigger_fallback,strict_method=critical_fault_flag|window_start=2025-09-14|first_warning=2025-11-11|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.2,2025-11-13,2025-11-11,2025-11-13,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2025-09-14|first_warning=2025-11-11|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.6,2025-11-16,,2025-11-16,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2025-09-17|first_warning=none|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.0.17,2025-11-17,2025-11-12,2025-11-17,0,medium,strict_trigger_fallback,strict_method=critical_fault_flag|window_start=2025-09-18|first_warning=2025-11-12|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.5,2025-11-17,2025-11-13,2025-11-17,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2025-09-18|first_warning=2025-11-13|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.4,2025-11-30,2025-11-29,2025-11-30,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2025-10-01|first_warning=2025-11-29|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.1.1,2025-12-07,2025-10-15,2025-12-07,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2025-10-08|first_warning=2025-10-15|recovery_reset=yes|shadow_frac=0.0|group_off_frac=0.0,,,,,,P3,,,,,,,,
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 6743, "endswith_newline": true, "lines": 7, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_abrupt6_symptom_map_v1.csv", "role": "frozen_share_input", "sha256": "adc23e272b3b0507a3fc9eed41128d794605cd3faca396a2f703341c3eca2919"}
#|﻿site,panel_id,고장시점,사건유형_ko,최종고장양상_ko,순수급작_flag,사건유형_판정주의_ko,증상명_ko,세부근거_ko,source_field_ko,비고_ko
#|conalog,7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0,2024-11-26,전조형 고장,진행성 악화,0,"retrospective_onset_date 비공란, strict_trigger_date 비공란, retrospective_onset_date < strict_trigger_date, onset_confidence=high, onset_method=persistent_5of7 이 모두 성립; 사건유형_재판정_ko == 전조형 고장 이고 급격 종료 규칙은 아니므로 진행성 악화로 둠; abrupt_positive_evidence_flag=1; strict precursor truth positive 포함; vendor_fault_family=diode_like, vendor_reply_class=vendor_pattern_positive",다이오드형,vendor_fault_family=diode_like,vendor_fault_family,selection_rule=strict_abrupt_evidence_plus_truth_backfill; selection_source=reaudit_accepted_truth_backfill; anchor_source=; candidate_validity=true_positive; vendor_reply_class=vendor_pattern_positive; eligibility_fault_start_date=2024-11-26; fault_event_type=전조형 고장; fault_terminal_pattern=진행성 악화; strict_precursor_eval_included=1; pure_abrupt_eval_included=0; event_semantics=precursor_led_fault_progressive; family_composition_check=ok
#|conalog,c42997a6-5881-47e7-9035-7de8a2673b54.1.1,2025-03-21,전조형 고장,급격 종료,0,"retrospective_onset_date 비공란, strict_trigger_date 비공란, retrospective_onset_date < strict_trigger_date, onset_confidence=high, onset_method=persistent_5of7 이 모두 성립; first_final_fault_date == strict_trigger_date 이고 dead_diag_date <= strict_trigger_date + 1 day; abrupt_positive_evidence_flag=1; vendor_fault_family=open_or_device_issue_like, vendor_reply_class=vendor_likely_positive",개방/장치이상형,vendor_fault_family=open_or_device_issue_like,vendor_fault_family,selection_rule=strict_abrupt_evidence_plus_truth_backfill; selection_source=reaudit_accepted_truth_backfill; anchor_source=; candidate_validity=needs_more_info; vendor_reply_class=vendor_likely_positive; fault_event_type=전조형 고장; fault_terminal_pattern=급격 종료; strict_precursor_eval_included=0; pure_abrupt_eval_included=0; event_semantics=precursor_led_fault_with_abrupt_ending; family_composition_check=ok
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7,2025-06-08,급작 고장,급작 발생,1,"abrupt positive evidence 가 있고, retrospective_onset_date 가 공란이거나 retrospective_onset_date == strict_trigger_date 이면서 onset_method=strict_trigger_fallback, onset_confidence != high 인 same-day fallback onset 이라 급작 고장으로 둠; 급격 종료 규칙은 아니지만 사건유형_재판정_ko == 급작 고장 이라 급작 발생으로 둠; abrupt_positive_evidence_flag=1; vendor_fault_family=diode_like, vendor_reply_class=vendor_pattern_positive",다이오드형,vendor_fault_family=diode_like,vendor_fault_family,selection_rule=strict_abrupt_evidence_plus_truth_backfill; selection_source=non_precursor_abrupt_evidence; anchor_source=fault_start_date; candidate_validity=true_positive; vendor_reply_class=vendor_pattern_positive; evidence=critical_fault_hit_by_anchor_flag; eligibility_fault_start_date=2025-06-08; fault_event_type=급작 고장; fault_terminal_pattern=급작 발생; strict_precursor_eval_included=0; pure_abrupt_eval_included=1; event_semantics=pure_abrupt_fault; family_composition_check=ok
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16,2025-06-08,급작 고장,급작 발생,1,"abrupt positive evidence 가 있고, retrospective_onset_date 가 공란이거나 retrospective_onset_date == strict_trigger_date 이면서 onset_method=strict_trigger_fallback, onset_confidence != high 인 same-day fallback onset 이라 급작 고장으로 둠; 급격 종료 규칙은 아니지만 사건유형_재판정_ko == 급작 고장 이라 급작 발생으로 둠; abrupt_positive_evidence_flag=1; vendor_fault_family=diode_like, vendor_reply_class=vendor_pattern_positive",다이오드형,vendor_fault_family=diode_like,vendor_fault_family,"selection_rule=strict_abrupt_evidence_plus_truth_backfill; selection_source=non_precursor_abrupt_evidence; anchor_source=fault_start_date; candidate_validity=true_positive; vendor_reply_class=vendor_pattern_positive; evidence=final_fault_hit_by_anchor_flag,critical_fault_hit_by_anchor_flag; eligibility_fault_start_date=2025-06-08; fault_event_type=급작 고장; fault_terminal_pattern=급작 발생; strict_precursor_eval_included=0; pure_abrupt_eval_included=1; event_semantics=pure_abrupt_fault; family_composition_check=ok"
#|ktc_ess,70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4,2025-02-02,전조형 고장,진행성 악화,0,"retrospective_onset_date 비공란, strict_trigger_date 비공란, retrospective_onset_date < strict_trigger_date, onset_confidence=high, onset_method=persistent_5of7 이 모두 성립; 사건유형_재판정_ko == 전조형 고장 이고 급격 종료 규칙은 아니므로 진행성 악화로 둠; abrupt_positive_evidence_flag=1; strict precursor truth positive 포함; vendor_fault_family=module_damage_like, vendor_reply_class=vendor_likely_positive",모듈손상형,vendor_fault_family=module_damage_like,vendor_fault_family,selection_rule=strict_abrupt_evidence_plus_truth_backfill; selection_source=reaudit_accepted_truth_backfill; anchor_source=; candidate_validity=true_positive; vendor_reply_class=vendor_likely_positive; eligibility_fault_start_date=2025-02-02; fault_event_type=전조형 고장; fault_terminal_pattern=진행성 악화; strict_precursor_eval_included=1; pure_abrupt_eval_included=0; event_semantics=precursor_led_fault_progressive; family_composition_check=ok
#|ktc_ess,10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12,2025-08-16,급작 고장,급작 발생,1,"abrupt positive evidence 가 있고, retrospective_onset_date 가 공란이거나 retrospective_onset_date == strict_trigger_date 이면서 onset_method=strict_trigger_fallback, onset_confidence != high 인 same-day fallback onset 이라 급작 고장으로 둠; 급격 종료 규칙은 아니지만 사건유형_재판정_ko == 급작 고장 이라 급작 발생으로 둠; abrupt_positive_evidence_flag=1; vendor_fault_family=diode_like, vendor_reply_class=vendor_pattern_positive",다이오드형,vendor_fault_family=diode_like,vendor_fault_family,selection_rule=strict_abrupt_evidence_plus_truth_backfill; selection_source=reaudit_accepted_truth_backfill; anchor_source=; candidate_validity=true_positive; vendor_reply_class=vendor_pattern_positive; eligibility_fault_start_date=2025-08-16; fault_event_type=급작 고장; fault_terminal_pattern=급작 발생; strict_precursor_eval_included=0; pure_abrupt_eval_included=1; event_semantics=pure_abrupt_fault; family_composition_check=ok
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 2620, "endswith_newline": true, "lines": 2, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_c42997_1_1_forensic_summary_v1.csv", "role": "frozen_share_input", "sha256": "6bc8496d57b2cc9717db1e2475c0a2c4d13558ecc94d093fc798c81f7f7dc4bb"}
#|﻿site,panel_id,원래_커널로그라벨_ko,원래라벨_근거파일_ko,현재_재감사라벨_ko,현재_재감사_근거파일_ko,현재_패널표_사건유형_ko,현재_패널표_커널로그증상명_ko,현재_패널표_커널로그원인군_ko,현재_패널표_GPVS참고유형_ko,전조흔적_시작일,강한트리거일,선행기간_일,earliest_warning_date,earliest_onset_date,strong_trigger_date,days_between_onset_and_trigger,pretrigger_window_day_count,ae_active_days_pretrigger,dtw_active_days_pretrigger,hs_active_days_pretrigger,cond_evt_days_pretrigger,pre_alarm_days_pretrigger,final_fault_days_pretrigger,longest_consecutive_active_run_days,longest_consecutive_cond_evt_run_days,last_gap_before_trigger_days,continuity_judgment_ko,event_recommendation_ko,사건유형_결정규칙_ko,최종고장양상_결정규칙_ko,사건유형_결정_ko,최종고장양상_결정_ko,사건시간양상_판정_ko,확정도_판정_ko,현재표_보정필요여부_flag,핵심판정_한줄요약_ko,다음보정권고_ko
#|conalog,c42997a6-5881-47e7-9035-7de8a2673b54.1.1,compound / electrical,"_share/partner_review_pack_send/return_sheet_send.csv (our_phenotype, our_dominant_family)",개방/장치이상형 (open_or_device_issue_like),_share/panel_date_reaudit_working.csv / _share/vendor_reply_adjudication_latest.csv,전조형 고장,전압 변화형,개방/장치이상형,개방/장치이상 계열,2025-01-16,2025-03-21,64,2025-01-16,2025-01-20,2025-03-21,60,64,64,54,9,38,2,0,64,27,0,동일사건_연속가능성_높음,전조형고장으로상향,"retrospective_onset_date 비공란, strict_trigger_date 비공란, retrospective_onset_date < strict_trigger_date, onset_confidence=high, onset_method=persistent_5of7 이 모두 성립해 전조형 고장으로 결정",first_final_fault_date == strict_trigger_date 이고 dead_diag_date <= strict_trigger_date + 1 day 라 급격 종료로 결정,전조형 고장,급격 종료,전조흔적있음_순수급작보류,보류,0,원래 stored kernel wording은 `compound / electrical` 이고 현재 재감사는 `개방/장치이상형 (open_or_device_issue_like)` 이다. explicit stored-field rule 기준 사건유형은 `전조형 고장` 이고 최종고장양상은 `급격 종료` 이다. 현재 downstream authoritative row는 `전조형 고장` / `급격 종료` 이다.,"사건유형은 `전조형 고장`, 최종고장양상은 `급격 종료` 으로 읽고, evaluation-set 편입 여부와는 별도로 관리한다. 이 forensic pack은 그 설명 근거를 남긴다. (pretrigger 64일 동안 AE 64일, DTW 54일, cond_evt 38일, 마지막 gap 0일)"
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 3153, "endswith_newline": true, "lines": 13, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv", "role": "frozen_share_input", "sha256": "95faf00e62c5c997d8747f8534bf7c70277e0242aea8274ec0621faa3bd9ad83"}
#|﻿eval_bucket_v2,site,panel_id,anchor_date,truth_case_id,current_marker_only_flag,breadth_marker_only_flag,combined_marker_flag,explanation_mode_class,retrofit_reason_ko
#|abrupt_or_no_precursor_now,gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7,2025-06-08,eligibility|gangui|bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7|2025-06-08,0,0,0,neither,current/breadth 모두로도 설명되지 않아 descriptive review가 더 필요함
#|abrupt_or_no_precursor_now,gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16,2025-06-08,eligibility|gangui|bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16|2025-06-08,0,0,0,neither,current/breadth 모두로도 설명되지 않아 descriptive review가 더 필요함
#|abrupt_or_no_precursor_now,conalog,45dfa600-79b7-428e-95d3-22345a068986.1.0,2024-12-29,reaudit|conalog|45dfa600-79b7-428e-95d3-22345a068986.1.0|2024-12-29,0,0,0,neither,current/breadth 모두로도 설명되지 않아 descriptive review가 더 필요함
#|abrupt_or_no_precursor_now,conalog,45dfa600-79b7-428e-95d3-22345a068986.1.1,2025-01-19,reaudit|conalog|45dfa600-79b7-428e-95d3-22345a068986.1.1|2025-01-19,0,0,0,neither,current/breadth 모두로도 설명되지 않아 descriptive review가 더 필요함
#|abrupt_or_no_precursor_now,conalog,d15b9e13-4117-49ae-a78f-7ace013e48de.0.0,2025-02-19,reaudit|conalog|d15b9e13-4117-49ae-a78f-7ace013e48de.0.0|2025-02-19,0,0,0,neither,current/breadth 모두로도 설명되지 않아 descriptive review가 더 필요함
#|abrupt_or_no_precursor_now,gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.9,2025-10-27,reaudit|gangui|bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.9|2025-10-27,0,0,0,neither,current/breadth 모두로도 설명되지 않아 descriptive review가 더 필요함
#|non_panel_or_common_cause,conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.15,2024-12-06,reaudit|conalog|d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.15|2024-12-06,0,1,1,breadth_only,선택된 breadth marker가 새로 설명을 추가한 case
#|non_panel_or_common_cause,conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.16,2024-12-06,reaudit|conalog|d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.16|2024-12-06,0,1,1,breadth_only,선택된 breadth marker가 새로 설명을 추가한 case
#|non_panel_or_common_cause,conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.17,2024-12-06,reaudit|conalog|d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.17|2024-12-06,0,1,1,breadth_only,선택된 breadth marker가 새로 설명을 추가한 case
#|non_panel_or_common_cause,gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.4.15,2025-11-11,reaudit|gangui|4fd0c566-e25e-4d51-96ca-57cc46940593.4.15|2025-11-11,0,1,1,breadth_only,선택된 breadth marker가 새로 설명을 추가한 case
#|precursor_bearing_detectable_now,conalog,7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0,2024-11-26,onset|conalog|7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0|2024-11-26,0,0,0,neither,current/breadth 모두로도 설명되지 않아 descriptive review가 더 필요함
#|precursor_bearing_detectable_now,ktc_ess,70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4,2025-02-02,onset|ktc_ess|70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4|2025-02-02,0,0,0,neither,current/breadth 모두로도 설명되지 않아 descriptive review가 더 필요함
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 684, "endswith_newline": true, "lines": 7, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_detailed_fault_bridge_audit_v1.csv", "role": "frozen_share_input", "sha256": "b486d90fb12f9ab7d2946e3d8ed7d7f6a841e145345c3d5b25e1bb123093a5b7"}
#|﻿site,panel_id,reference_date,exact_match_file_count,matched_files_csv,matched_fault_type_values_csv,consensus_fault_type_code,attachable_flag,attach_reason_ko
#|conalog,7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0,2024-11-26,0,,,,0,no_exact_date_match
#|conalog,c42997a6-5881-47e7-9035-7de8a2673b54.1.1,2025-03-21,0,,,,0,no_exact_date_match
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7,2025-06-08,0,,,,0,no_exact_date_match
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16,2025-06-08,0,,,,0,no_exact_date_match
#|ktc_ess,10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12,2025-08-16,0,,,,0,no_exact_date_match
#|ktc_ess,70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4,2025-02-02,0,,,,0,no_exact_date_match
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 381, "endswith_newline": true, "lines": 2, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_detailed_fault_bridge_summary_v1.csv", "role": "frozen_share_input", "sha256": "74e5f22468c8c8675ed34c2bc86fa225f1a5b92d7efeeb3d0b62eb87a36b08d5"}
#|﻿고장패널수,세부fault_부착수,세부fault_보류수,exact_date_match_패널수,exact_date_conflict_패널수,exact_date_miss_패널수,note_ko
#|6,0,6,0,0,6,"세부 fault type은 PVFAULT_labels_day.csv exact-date consensus로만 붙인다. nearest-date heuristic은 쓰지 않고, file 간 conflict가 나면 보류한다. 이 축은 GPVS family attachment와 별개다."
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 4372, "endswith_newline": true, "lines": 7, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_fault_panel_event_audit_v1.csv", "role": "frozen_share_input", "sha256": "103ce7549fb21433d14fe5cd0a949d2007ff3ffe16afb3ab28f28b82d8b0d047"}
#|﻿site,panel_id,현재표_사건유형_ko,현재표_최종고장양상_ko,earliest_warning_date,retrospective_onset_date,strict_trigger_date,first_final_fault_date,dead_diag_date,onset_confidence,onset_method,전조흔적_flag,순수급작_flag,전조평가셋편입_flag,급작평가셋편입_flag,사건유형_재판정_ko,최종고장양상_재판정_ko,재판정_근거_ko,현재표_보정필요여부_flag
#|conalog,7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0,전조형 고장,진행성 악화,2024-11-06,2024-11-06,2024-11-26,2024-11-26,2025-12-19,high,persistent_5of7,1,0,1,0,전조형 고장,진행성 악화,"retrospective_onset_date 비공란, strict_trigger_date 비공란, retrospective_onset_date < strict_trigger_date, onset_confidence=high, onset_method=persistent_5of7 이 모두 성립; 사건유형_재판정_ko == 전조형 고장 이고 급격 종료 규칙은 아니므로 진행성 악화로 둠; abrupt_positive_evidence_flag=1; strict precursor truth positive 포함; vendor_fault_family=diode_like, vendor_reply_class=vendor_pattern_positive",0
#|conalog,c42997a6-5881-47e7-9035-7de8a2673b54.1.1,전조형 고장,급격 종료,2025-01-16,2025-01-20,2025-03-21,2025-03-21,2025-03-22,high,persistent_5of7,1,0,1,0,전조형 고장,급격 종료,"retrospective_onset_date 비공란, strict_trigger_date 비공란, retrospective_onset_date < strict_trigger_date, onset_confidence=high, onset_method=persistent_5of7 이 모두 성립; first_final_fault_date == strict_trigger_date 이고 dead_diag_date <= strict_trigger_date + 1 day; abrupt_positive_evidence_flag=1; strict precursor truth positive 포함; vendor_fault_family=open_or_device_issue_like, vendor_reply_class=vendor_likely_positive",0
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7,급작 고장,급작 발생,2025-06-08,2025-06-08,2025-06-08,,,medium,strict_trigger_fallback,0,1,0,1,급작 고장,급작 발생,"abrupt positive evidence 가 있고, retrospective_onset_date 가 공란이거나 retrospective_onset_date == strict_trigger_date 이면서 onset_method=strict_trigger_fallback, onset_confidence != high 인 same-day fallback onset 이라 급작 고장으로 둠; 급격 종료 규칙은 아니지만 사건유형_재판정_ko == 급작 고장 이라 급작 발생으로 둠; abrupt_positive_evidence_flag=1; vendor_fault_family=diode_like, vendor_reply_class=vendor_pattern_positive",0
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16,급작 고장,급작 발생,2025-06-07,2025-06-08,2025-06-08,2025-06-08,,medium,strict_trigger_fallback,0,1,0,1,급작 고장,급작 발생,"abrupt positive evidence 가 있고, retrospective_onset_date 가 공란이거나 retrospective_onset_date == strict_trigger_date 이면서 onset_method=strict_trigger_fallback, onset_confidence != high 인 same-day fallback onset 이라 급작 고장으로 둠; 급격 종료 규칙은 아니지만 사건유형_재판정_ko == 급작 고장 이라 급작 발생으로 둠; abrupt_positive_evidence_flag=1; vendor_fault_family=diode_like, vendor_reply_class=vendor_pattern_positive",0
#|ktc_ess,10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12,급작 고장,급작 발생,2024-12-14,2025-08-16,2025-08-16,2025-08-16,,medium,strict_trigger_fallback,0,1,0,1,급작 고장,급작 발생,"abrupt positive evidence 가 있고, retrospective_onset_date 가 공란이거나 retrospective_onset_date == strict_trigger_date 이면서 onset_method=strict_trigger_fallback, onset_confidence != high 인 same-day fallback onset 이라 급작 고장으로 둠; 급격 종료 규칙은 아니지만 사건유형_재판정_ko == 급작 고장 이라 급작 발생으로 둠; abrupt_positive_evidence_flag=1; vendor_fault_family=diode_like, vendor_reply_class=vendor_pattern_positive",0
#|ktc_ess,70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4,전조형 고장,진행성 악화,2024-12-25,2025-01-25,2025-02-02,,,high,persistent_5of7,1,0,1,0,전조형 고장,진행성 악화,"retrospective_onset_date 비공란, strict_trigger_date 비공란, retrospective_onset_date < strict_trigger_date, onset_confidence=high, onset_method=persistent_5of7 이 모두 성립; 사건유형_재판정_ko == 전조형 고장 이고 급격 종료 규칙은 아니므로 진행성 악화로 둠; abrupt_positive_evidence_flag=1; strict precursor truth positive 포함; vendor_fault_family=module_damage_like, vendor_reply_class=vendor_likely_positive",0
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 2365, "endswith_newline": true, "lines": 8, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpv7_perf_summary_v1.csv", "role": "frozen_share_input", "sha256": "dc38bb9eb2d942db91b2924a9db7d170030eabc77699aec7731e112c1b93f49e"}
#|﻿고장유형_번호,고장유형_설명_ko,성능요약_ko,수치_ko,source_ref_ko
#|1,GPVS Fault1,F1M / dtw_like representative row from EXTERNAL_GPVS_BYTYPE_METRICS.csv,"auc=0.9080, ap=0.9383, precision_fpr1=0.9886, recall_fpr1=0.7970, f1_fpr1=0.8825, detect_rate_post=1.0000","data/gpvs/out/EXTERNAL_GPVS_BYTYPE_METRICS.csv (fault_type,sid,score,auc,ap,precision_fpr1,recall_fpr1,f1_fpr1,detect_rate_post)"
#|2,GPVS Fault2,F2L / level_drop_like representative row from EXTERNAL_GPVS_BYTYPE_METRICS.csv,"auc=0.5677, ap=0.5367, precision_fpr1=0.6875, recall_fpr1=0.0199, f1_fpr1=0.0386, detect_rate_post=1.0000","data/gpvs/out/EXTERNAL_GPVS_BYTYPE_METRICS.csv (fault_type,sid,score,auc,ap,precision_fpr1,recall_fpr1,f1_fpr1,detect_rate_post)"
#|3,GPVS Fault3,F3L / ae_like representative row from EXTERNAL_GPVS_BYTYPE_METRICS.csv,"auc=0.5708, ap=0.6209, precision_fpr1=0.9184, recall_fpr1=0.1117, f1_fpr1=0.1991, detect_rate_post=1.0000","data/gpvs/out/EXTERNAL_GPVS_BYTYPE_METRICS.csv (fault_type,sid,score,auc,ap,precision_fpr1,recall_fpr1,f1_fpr1,detect_rate_post)"
#|4,GPVS Fault4,F4M / dtw_like representative row from EXTERNAL_GPVS_BYTYPE_METRICS.csv,"auc=0.5290, ap=0.5279, precision_fpr1=0.5455, recall_fpr1=0.0107, f1_fpr1=0.0209, detect_rate_post=1.0000","data/gpvs/out/EXTERNAL_GPVS_BYTYPE_METRICS.csv (fault_type,sid,score,auc,ap,precision_fpr1,recall_fpr1,f1_fpr1,detect_rate_post)"
#|5,GPVS Fault5,F5L / dtw_like representative row from EXTERNAL_GPVS_BYTYPE_METRICS.csv,"auc=0.9749, ap=0.9332, precision_fpr1=0.8276, recall_fpr1=0.0430, f1_fpr1=0.0818, detect_rate_post=1.0000","data/gpvs/out/EXTERNAL_GPVS_BYTYPE_METRICS.csv (fault_type,sid,score,auc,ap,precision_fpr1,recall_fpr1,f1_fpr1,detect_rate_post)"
#|6,GPVS Fault6,F6L / hs_like representative row from EXTERNAL_GPVS_BYTYPE_METRICS.csv,"auc=0.5240, ap=0.5233, precision_fpr1=0.5000, recall_fpr1=0.0089, f1_fpr1=0.0175, detect_rate_post=1.0000","data/gpvs/out/EXTERNAL_GPVS_BYTYPE_METRICS.csv (fault_type,sid,score,auc,ap,precision_fpr1,recall_fpr1,f1_fpr1,detect_rate_post)"
#|7,GPVS Fault7,F7M / ae_like representative row from EXTERNAL_GPVS_BYTYPE_METRICS.csv,"auc=0.5541, ap=0.5458, precision_fpr1=0.6429, recall_fpr1=0.0160, f1_fpr1=0.0312, detect_rate_post=1.0000","data/gpvs/out/EXTERNAL_GPVS_BYTYPE_METRICS.csv (fault_type,sid,score,auc,ap,precision_fpr1,recall_fpr1,f1_fpr1,detect_rate_post)"
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 583, "endswith_newline": true, "lines": 2, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv", "role": "frozen_share_input", "sha256": "fc0483c0b5584bb3adf831053d4a85fab3a31e62a9868fdf177b0a2e9ad5eaec"}
#|﻿recovered_model_exported_flag,recovered_feature_manifest_exported_flag,recovered_model_source_ko,parity_overall_status_ko,current_recovered_attachable_flag,note_ko
#|1,1,gpvs_train_supervised selected primary path reuse,일치,1,"recovered export 는 gpvs_train_supervised selected primary path를 재사용해 만든 multiclass by-type artifact 다. recovered_model_used_flag=1, parity_overall_status_ko=일치, realpanel_collapse_flag=0, current_recovered_attachable_flag=1. do_not_attach 결론은 parity 와 real-panel collapse 둘 다 풀리기 전까지 유지해야 한다."
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 1898, "endswith_newline": true, "lines": 9, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpvs_canonical_dictionary_v1.csv", "role": "frozen_share_input", "sha256": "a5d33bc1d714e2c4cc2f4b6d580174927ec47f1afa2f0d090765fa9d9c434e58"}
#|﻿canonical_gpvs_code,current_usage_tier_ko,mlpe_reference_family_ko,mlpe_reference_name_ko,usage_rule_ko,current_real_fault_support_count,note_ko
#|F0,baseline,정상 기준,정상 기준선,비고장 기준선과 drift 비교에만 사용,0,front-facing matching에서는 fault명이 아니라 baseline reference로만 노출
#|F1,reserved_system_level,시스템/전력변환,인버터 전력변환부 시스템 시나리오,MLPE direct fault명이 아니라 통합 결과표 후보축으로만 보류,0,current panel set direct support가 없어 system-level reserve로만 유지
#|F2,auxiliary_reference,제어·계측 힌트,제어/계측 이상 보조 힌트,direct root-cause가 아니라 제어·계측 이상 힌트로만 사용,4,real fault support 4건; panel agreement useful/caution/notrec=0/0/4
#|F3,confounder_only,계통 교란,계통 교란 플래그,fault label이 아니라 confounder flag로만 사용,0,real-panel direct support가 없어 confounder-only로 유지
#|F4,core_reference,패널·어레이 불균형,패널·어레이 mismatch 핵심 참조,MLPE 패널·어레이 불균형 해석의 핵심 reference로 사용,2,real fault support 2건; panel agreement useful/caution/notrec=0/2/0
#|F5,core_reference_candidate,패널·어레이 불균형,부분 개방회로 계열 핵심 참조 후보,케이블 접점불량(단선) 가설의 핵심 reference candidate로 유지,0,current panel set direct support는 약하지만 semantics상 살려둘 가치가 큼
#|F6,reserved_system_level,제어기/시스템,제어기 gain 이상 시스템 시나리오,MLPE direct fault명이 아니라 통합 결과표 후보축으로만 보류,0,system-level reserve code로만 유지
#|F7,reserved_system_level,제어기/시스템,제어기 시정수 이상 시스템 시나리오,MLPE direct fault명이 아니라 통합 결과표 후보축으로만 보류,0,system-level reserve code로만 유지
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 1774, "endswith_newline": true, "lines": 7, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv", "role": "frozen_share_input", "sha256": "59ba93a644e339a71ef8ea32e7511a116e4b8204cbf292864a986af5ed8e9371"}
#|﻿site,panel_id,event_reference_date,gpvs_detailed_model_source,gpvs_family_label,gpvs_detailed_top1_fault_type,gpvs_detailed_top1_score,gpvs_detailed_top2_fault_type,gpvs_detailed_top2_score,gpvs_detailed_margin,gpvs_detailed_status_ko,gpvs_detailed_reason_ko
#|conalog,7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0,2024-11-26,recovered_artifact,전기적 고장 계열,F4L,0.7663980163772397,F2M,0.2312023817819903,0.5351956345952494,추론성공,model_source=recovered_artifact; top1=F4L:0.766398; top2=F2M:0.231202
#|conalog,c42997a6-5881-47e7-9035-7de8a2673b54.1.1,2025-03-21,recovered_artifact,개방/장치이상 계열,F2M,0.9999684297851251,F4L,3.0448819189008488e-05,0.9999379809659361,추론성공,model_source=recovered_artifact; top1=F2M:0.999968; top2=F4L:3.04488e-05
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7,2025-06-08,recovered_artifact,전기적 고장 계열,F2M,0.9983614102233517,F4L,0.0016307804894536396,0.996730629733898,추론성공,model_source=recovered_artifact; top1=F2M:0.998361; top2=F4L:0.00163078
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16,2025-06-08,recovered_artifact,전기적 고장 계열,F2M,0.9909254812518792,F4L,0.009071427150722886,0.9818540541011563,추론성공,model_source=recovered_artifact; top1=F2M:0.990925; top2=F4L:0.00907143
#|ktc_ess,10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12,2025-08-16,recovered_artifact,불확실,F4L,0.8217373274556089,F2M,0.1167798589533898,0.7049574685022191,추론성공,model_source=recovered_artifact; top1=F4L:0.821737; top2=F2M:0.11678
#|ktc_ess,70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4,2025-02-02,recovered_artifact,전기적 고장 계열,F2M,0.9632018904449849,F4L,0.036321501823062846,0.9268803886219221,추론성공,model_source=recovered_artifact; top1=F2M:0.963202; top2=F4L:0.0363215
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 1856, "endswith_newline": true, "lines": 7, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpvs_detailed_type_realpanel_sanity_v1.csv", "role": "frozen_share_input", "sha256": "bb14a77c79870e6a497b5780540c3e393f1347574e18b9fd0fce94ee09ad21d8"}
#|﻿site,panel_id,gpvs_family_label,gpvs_detailed_top1_fault_type,gpvs_detailed_top1_score,gpvs_detailed_top2_fault_type,gpvs_detailed_top2_score,gpvs_detailed_margin,family_vs_detail_consistency_ko,single_type_collapse_flag,attach_recommendation_ko
#|conalog,7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0,전기적 고장 계열,F4L,0.7663980163772397,F2M,0.2312023817819903,0.5351956345952494,broad GPVS family 와 fine detailed type 사이 직접 충돌 근거는 현재 audit 자산에서 확인되지 않음,0,attach_ok
#|conalog,c42997a6-5881-47e7-9035-7de8a2673b54.1.1,개방/장치이상 계열,F2M,0.9999684297851251,F4L,3.0448819189008488e-05,0.9999379809659361,broad GPVS family 와 fine detailed type 사이 직접 충돌 근거는 현재 audit 자산에서 확인되지 않음,0,attach_ok
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7,전기적 고장 계열,F2M,0.9983614102233517,F4L,0.0016307804894536396,0.996730629733898,broad GPVS family 와 fine detailed type 사이 직접 충돌 근거는 현재 audit 자산에서 확인되지 않음,0,attach_ok
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16,전기적 고장 계열,F2M,0.9909254812518792,F4L,0.009071427150722886,0.9818540541011563,broad GPVS family 와 fine detailed type 사이 직접 충돌 근거는 현재 audit 자산에서 확인되지 않음,0,attach_ok
#|ktc_ess,10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12,불확실,F4L,0.8217373274556089,F2M,0.1167798589533898,0.7049574685022191,broad GPVS family 와 fine detailed type 사이 직접 충돌 근거는 현재 audit 자산에서 확인되지 않음,0,attach_ok
#|ktc_ess,70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4,전기적 고장 계열,F2M,0.9632018904449849,F4L,0.036321501823062846,0.9268803886219221,broad GPVS family 와 fine detailed type 사이 직접 충돌 근거는 현재 audit 자산에서 확인되지 않음,0,attach_ok
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 10516, "endswith_newline": true, "lines": 7, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpvs_evidence_pack_v1.csv", "role": "frozen_share_input", "sha256": "cf0bef62109dde191db4fff981367303dcf3daa4b73afdec2b5a5f336d07bac7"}
#|﻿site,panel_id,사건유형_ko,최종고장양상_ko,커널로그_원인군_ko,GPVS_내부판정_ko,GPVS_내부판정근거_ko,GPVS_외부참조패턴_ko,GPVS_외부참조근거_ko,GPVS_호환성판정_ko,GPVS_호환성근거_ko,GPVS_매칭정책_ko,GPVS_매칭근거_ko,GPVS_최종사용권고_ko,GPVS_권고사유_ko
#|conalog,7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0,전조형 고장,진행성 악화,다이오드형,전기적 고장 계열,"family evaluator source=critical_phenotype_v3, fallback=resolved_by_critical_phenotype_v3, error=correct, pred=electrical_fault_like, vendor=diode_like",국소 출력 불균형형,"by-type source=recovered_artifact, top1=F4L(0.766), top2=F2M(0.231), margin=0.535, status=추론성공, reason=model_source=recovered_artifact; top1=F4L:0.766398; top2=F2M:0.231202, sanity=attach_ok, consistency=broad GPVS family 와 fine detailed type 사이 직접 충돌 근거는 현재 audit 자산에서 확인되지 않음",조건부 참고 가능,"family_alignment=일치; scenario_alignment=부분일치; feature_shift=strong_shift; panel_usefulness=주의참고; feature schema는 맞지만 training 대비 분포 이동이 커서 GPVS는 reference-only로만 읽는 편이 안전함; summary=참고축으로만 사용; strong_shift_panel_count=6; scenario_conflict_count=4; schema_match_ratio=1.000, strong_shift_panel_count=6, scenario_conflict_count=4. GPVS original scenario space and MLPE official problem-type space are not identical. 따라서 GPVS는 direct root-cause classifier가 아니라 reference layer로만 읽는 것이 안전하다.",핵심참조,F4는 패널·어레이 불균형 해석에 가장 유용한 핵심 reference code다; MLPE 패널·어레이 불균형 해석의 핵심 reference로 사용; real fault support 2건; panel agreement useful/caution/notrec=0/2/0; matching=정션박스 손상:핵심참조 / 모듈 경년 열화:보조참조,핵심참조,국소 출력 불균형형는 direct root-cause가 아니라 reference-only 핵심참조로만 사용한다.
#|conalog,c42997a6-5881-47e7-9035-7de8a2673b54.1.1,전조형 고장,급격 종료,개방/장치이상형,개방/장치이상 계열,"family evaluator source=strict_day_core_fallback, fallback=legacy_open_device, error=correct, pred=open_or_device_issue_like, vendor=open_or_device_issue_like",장치 응답 이상형,"by-type source=recovered_artifact, top1=F2M(1.000), top2=F4L(0.000), margin=1.000, status=추론성공, reason=model_source=recovered_artifact; top1=F2M:0.999968; top2=F4L:3.04488e-05, sanity=attach_ok, consistency=broad GPVS family 와 fine detailed type 사이 직접 충돌 근거는 현재 audit 자산에서 확인되지 않음",직접 판정축 사용 비권장,"family_alignment=일치; scenario_alignment=불일치; feature_shift=strong_shift; panel_usefulness=비권장; 외부 GPVS scenario/family 방향성이 current kernel-log 원인군과 직접 충돌해 direct trust를 주기 어려움; summary=참고축으로만 사용; strong_shift_panel_count=6; scenario_conflict_count=4; schema_match_ratio=1.000, strong_shift_panel_count=6, scenario_conflict_count=4. GPVS original scenario space and MLPE official problem-type space are not identical. 따라서 GPVS는 direct root-cause classifier가 아니라 reference layer로만 읽는 것이 안전하다.",보조참조,F2는 장치 응답 이상 힌트로만 사용하고 direct root-cause로 읽지 않는다; direct root-cause가 아니라 제어·계측 이상 힌트로만 사용; real fault support 4건; panel agreement useful/caution/notrec=0/0/4; matching=인버터/스트링 동작 불량:보조참조,보조참조,장치 응답 이상형는 직접 root-cause 판정에는 쓰지 말고 보조참조로만 사용한다.
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7,급작 고장,급작 발생,다이오드형,전기적 고장 계열,"family evaluator source=critical_phenotype_v3, fallback=resolved_by_critical_phenotype_v3, error=correct, pred=electrical_fault_like, vendor=diode_like",장치 응답 이상형,"by-type source=recovered_artifact, top1=F2M(0.998), top2=F4L(0.002), margin=0.997, status=추론성공, reason=model_source=recovered_artifact; top1=F2M:0.998361; top2=F4L:0.00163078, sanity=attach_ok, consistency=broad GPVS family 와 fine detailed type 사이 직접 충돌 근거는 현재 audit 자산에서 확인되지 않음",직접 판정축 사용 비권장,"family_alignment=일치; scenario_alignment=불일치; feature_shift=strong_shift; panel_usefulness=비권장; 외부 GPVS scenario/family 방향성이 current kernel-log 원인군과 직접 충돌해 direct trust를 주기 어려움; summary=참고축으로만 사용; strong_shift_panel_count=6; scenario_conflict_count=4; schema_match_ratio=1.000, strong_shift_panel_count=6, scenario_conflict_count=4. GPVS original scenario space and MLPE official problem-type space are not identical. 따라서 GPVS는 direct root-cause classifier가 아니라 reference layer로만 읽는 것이 안전하다.",보조참조,F2는 장치 응답 이상 힌트로만 사용하고 direct root-cause로 읽지 않는다; direct root-cause가 아니라 제어·계측 이상 힌트로만 사용; real fault support 4건; panel agreement useful/caution/notrec=0/0/4; matching=인버터/스트링 동작 불량:보조참조,보조참조,장치 응답 이상형는 직접 root-cause 판정에는 쓰지 말고 보조참조로만 사용한다.
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16,급작 고장,급작 발생,다이오드형,전기적 고장 계열,"family evaluator source=critical_phenotype_v3, fallback=resolved_by_critical_phenotype_v3, error=correct, pred=electrical_fault_like, vendor=diode_like",장치 응답 이상형,"by-type source=recovered_artifact, top1=F2M(0.991), top2=F4L(0.009), margin=0.982, status=추론성공, reason=model_source=recovered_artifact; top1=F2M:0.990925; top2=F4L:0.00907143, sanity=attach_ok, consistency=broad GPVS family 와 fine detailed type 사이 직접 충돌 근거는 현재 audit 자산에서 확인되지 않음",직접 판정축 사용 비권장,"family_alignment=일치; scenario_alignment=불일치; feature_shift=strong_shift; panel_usefulness=비권장; 외부 GPVS scenario/family 방향성이 current kernel-log 원인군과 직접 충돌해 direct trust를 주기 어려움; summary=참고축으로만 사용; strong_shift_panel_count=6; scenario_conflict_count=4; schema_match_ratio=1.000, strong_shift_panel_count=6, scenario_conflict_count=4. GPVS original scenario space and MLPE official problem-type space are not identical. 따라서 GPVS는 direct root-cause classifier가 아니라 reference layer로만 읽는 것이 안전하다.",보조참조,F2는 장치 응답 이상 힌트로만 사용하고 direct root-cause로 읽지 않는다; direct root-cause가 아니라 제어·계측 이상 힌트로만 사용; real fault support 4건; panel agreement useful/caution/notrec=0/0/4; matching=인버터/스트링 동작 불량:보조참조,보조참조,장치 응답 이상형는 직접 root-cause 판정에는 쓰지 말고 보조참조로만 사용한다.
#|ktc_ess,10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12,급작 고장,급작 발생,다이오드형,불확실,"family evaluator source=critical_phenotype_v3, fallback=resolved_by_critical_phenotype_v3, error=abstain_uncertain, pred=uncertain, vendor=diode_like",국소 출력 불균형형,"by-type source=recovered_artifact, top1=F4L(0.822), top2=F2M(0.117), margin=0.705, status=추론성공, reason=model_source=recovered_artifact; top1=F4L:0.821737; top2=F2M:0.11678, sanity=attach_ok, consistency=broad GPVS family 와 fine detailed type 사이 직접 충돌 근거는 현재 audit 자산에서 확인되지 않음",조건부 참고 가능,"family_alignment=비교곤란; scenario_alignment=부분일치; feature_shift=strong_shift; panel_usefulness=주의참고; feature schema는 맞지만 training 대비 분포 이동이 커서 GPVS는 reference-only로만 읽는 편이 안전함; summary=참고축으로만 사용; strong_shift_panel_count=6; scenario_conflict_count=4; schema_match_ratio=1.000, strong_shift_panel_count=6, scenario_conflict_count=4. GPVS original scenario space and MLPE official problem-type space are not identical. 따라서 GPVS는 direct root-cause classifier가 아니라 reference layer로만 읽는 것이 안전하다.",핵심참조,F4는 패널·어레이 불균형 해석에 가장 유용한 핵심 reference code다; MLPE 패널·어레이 불균형 해석의 핵심 reference로 사용; real fault support 2건; panel agreement useful/caution/notrec=0/2/0; matching=정션박스 손상:핵심참조 / 모듈 경년 열화:보조참조,핵심참조,국소 출력 불균형형는 direct root-cause가 아니라 reference-only 핵심참조로만 사용한다.
#|ktc_ess,70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4,전조형 고장,진행성 악화,모듈손상형,전기적 고장 계열,"family evaluator source=critical_phenotype_v3, fallback=resolved_by_critical_phenotype_v3, error=correct, pred=electrical_fault_like, vendor=module_damage_like",장치 응답 이상형,"by-type source=recovered_artifact, top1=F2M(0.963), top2=F4L(0.036), margin=0.927, status=추론성공, reason=model_source=recovered_artifact; top1=F2M:0.963202; top2=F4L:0.0363215, sanity=attach_ok, consistency=broad GPVS family 와 fine detailed type 사이 직접 충돌 근거는 현재 audit 자산에서 확인되지 않음",직접 판정축 사용 비권장,"family_alignment=부분일치; scenario_alignment=불일치; feature_shift=strong_shift; panel_usefulness=비권장; 외부 GPVS scenario/family 방향성이 current kernel-log 원인군과 직접 충돌해 direct trust를 주기 어려움; summary=참고축으로만 사용; strong_shift_panel_count=6; scenario_conflict_count=4; schema_match_ratio=1.000, strong_shift_panel_count=6, scenario_conflict_count=4. GPVS original scenario space and MLPE official problem-type space are not identical. 따라서 GPVS는 direct root-cause classifier가 아니라 reference layer로만 읽는 것이 안전하다.",보조참조,F2는 장치 응답 이상 힌트로만 사용하고 direct root-cause로 읽지 않는다; direct root-cause가 아니라 제어·계측 이상 힌트로만 사용; real fault support 4건; panel agreement useful/caution/notrec=0/0/4; matching=인버터/스트링 동작 불량:보조참조,보조참조,장치 응답 이상형는 직접 root-cause 판정에는 쓰지 말고 보조참조로만 사용한다.
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 743, "endswith_newline": true, "lines": 2, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv", "role": "frozen_share_input", "sha256": "70940e6858166bd8a4d9f0f3741e44bed753c0c073f5ca8093b9383647261b1e"}
#|﻿fault_panel_count,recovered_model_present_flag,feature_schema_match_ratio,strong_shift_panel_count,mild_shift_panel_count,family_alignment_count,family_partial_alignment_count,family_conflict_count,scenario_alignment_count,scenario_partial_alignment_count,scenario_conflict_count,gpvs_reference_useful_count,gpvs_reference_caution_count,gpvs_reference_not_recommended_count,final_recommendation_ko,note_ko
#|6,1,1.0,6,0,4,1,0,0,2,4,0,2,4,참고축으로만 사용,"schema_match_ratio=1.000, strong_shift_panel_count=6, scenario_conflict_count=4. GPVS original scenario space and MLPE official problem-type space are not identical. 따라서 GPVS는 direct root-cause classifier가 아니라 reference layer로만 읽는 것이 안전하다."
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 406, "endswith_newline": true, "lines": 2, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpvs_mlpe_fault_matching_summary_v1.csv", "role": "frozen_share_input", "sha256": "59615635e7a22218026a3785fbc841e157763835f182f86ba0c6ec3ea1f83e15"}
#|﻿canonical_code_count,core_reference_count,auxiliary_reference_count,confounder_count,reserved_system_count,final_matching_policy_ko,note_ko
#|8,3,1,1,3,"F0/F4/F5 core, F2 auxiliary, F3 confounder, F1/F6/F7 reserved",compatibility final recommendation=참고축으로만 사용. 따라서 이 matching table은 direct root-cause classifier가 아니라 reference-layer 운영 규칙으로만 사용한다.
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 2369, "endswith_newline": true, "lines": 10, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpvs_mlpe_fault_matching_table_v1.csv", "role": "frozen_share_input", "sha256": "793daf84cd5926d5c2cc13553e4cf1393948ac74382717ef9d6ace530831f345"}
#|﻿mlpe_official_fault_ko,canonical_gpvs_code,match_strength_ko,match_role_ko,evidence_basis_ko,current_real_fault_support_count,recommendation_ko
#|정션박스 손상,F4,강,핵심참조,"F4는 PV 어레이 mismatch 계열이며 current real fault panel support=2건, scenario partial alignment=2건으로 panel/array imbalance 해석에 가장 직접적이다",2,reference layer에서 우선 확인하되 direct root-cause로 단정하지 않음
#|케이블 접점불량(단선),F5,강,핵심참조,F5는 부분 개방회로 시나리오라 케이블 접점불량(단선)과 가장 가깝지만 current real fault panel support=0건이라 아직 candidate 성격이 크다,0,core reference candidate로 유지하고 현 패널셋 direct evidence가 쌓일 때까지 조건부 사용
#|모듈 경년 열화,F4,중,보조참조,F4는 출력 불균형 방향을 포착하므로 경년 열화의 결과적 mismatch와 겹칠 수 있으나 one-to-one는 아니다; current support=2건,2,조건부 reference로만 사용
#|모듈 내 누전 추적,,없음,비권장,current GPVS canonical code space에는 누전 추적을 직접 가리키는 row-level match가 없다,0,GPVS direct matching 사용 비권장
#|인버터/스트링 동작 불량,F2,약,보조참조,F2 current support=4건이 있지만 scenario conflict=4건이라 direct fault명보다 제어·계측 이상 힌트로만 읽어야 한다,4,제어·계측 이상 힌트로만 사용
#|인버터/스트링 동작 불량,F3,약,교란플래그,F3는 계통 교란 confounder code이며 current support=0건으로 fault classifier보다 disturbance flag 성격이 강하다,0,교란 플래그로만 유지
#|인버터/스트링 동작 불량,F1,약,시스템보류,F1는 인버터/전력변환부 system-level scenario이며 current support=0건이라 MLPE panel verdict direct mapping을 보류한다,0,통합 결과표 후보축으로만 보류
#|인버터/스트링 동작 불량,F6,약,시스템보류,F6는 제어기 gain 이상 system-level scenario이며 current support=0건이라 MLPE panel verdict direct mapping을 보류한다,0,통합 결과표 후보축으로만 보류
#|인버터/스트링 동작 불량,F7,약,시스템보류,F7는 제어기 시정수 이상 system-level scenario이며 current support=0건이라 MLPE panel verdict direct mapping을 보류한다,0,통합 결과표 후보축으로만 보류
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 2281, "endswith_newline": true, "lines": 7, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpvs_mlpe_panel_agreement_v1.csv", "role": "frozen_share_input", "sha256": "3772deb00b45f2eedae04aee1ac097719d37a17a93ef8380a432267af5f02279"}
#|﻿site,panel_id,사건유형_ko,최종고장양상_ko,커널로그_원인군_ko,GPVS_참고유형_ko,GPVS_외부참조시나리오명_ko,family_vs_kernellog_alignment_ko,scenario_vs_kernellog_alignment_ko,feature_shift_bucket_ko,overall_gpvs_reference_usefulness_ko,overall_gpvs_trust_note_ko
#|conalog,7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0,전조형 고장,진행성 악화,다이오드형,전기적 고장 계열,PV 어레이 mismatch(부분 음영) 시나리오,일치,부분일치,strong_shift,주의참고,feature schema는 맞지만 training 대비 분포 이동이 커서 GPVS는 reference-only로만 읽는 편이 안전함
#|conalog,c42997a6-5881-47e7-9035-7de8a2673b54.1.1,전조형 고장,급격 종료,개방/장치이상형,개방/장치이상 계열,제어 피드백 센서 이상 시나리오,일치,불일치,strong_shift,비권장,외부 GPVS scenario/family 방향성이 current kernel-log 원인군과 직접 충돌해 direct trust를 주기 어려움
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7,급작 고장,급작 발생,다이오드형,전기적 고장 계열,제어 피드백 센서 이상 시나리오,일치,불일치,strong_shift,비권장,외부 GPVS scenario/family 방향성이 current kernel-log 원인군과 직접 충돌해 direct trust를 주기 어려움
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16,급작 고장,급작 발생,다이오드형,전기적 고장 계열,제어 피드백 센서 이상 시나리오,일치,불일치,strong_shift,비권장,외부 GPVS scenario/family 방향성이 current kernel-log 원인군과 직접 충돌해 direct trust를 주기 어려움
#|ktc_ess,10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12,급작 고장,급작 발생,다이오드형,불확실,PV 어레이 mismatch(부분 음영) 시나리오,비교곤란,부분일치,strong_shift,주의참고,feature schema는 맞지만 training 대비 분포 이동이 커서 GPVS는 reference-only로만 읽는 편이 안전함
#|ktc_ess,70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4,전조형 고장,진행성 악화,모듈손상형,전기적 고장 계열,제어 피드백 센서 이상 시나리오,부분일치,불일치,strong_shift,비권장,외부 GPVS scenario/family 방향성이 current kernel-log 원인군과 직접 충돌해 direct trust를 주기 어려움
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 3405, "endswith_newline": true, "lines": 13, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpvs_panel_attach_candidates_v1.csv", "role": "frozen_share_input", "sha256": "164a017a461a9d422da72f22e2eca4074a40f0b8f41b14053fea2747ef9abd25"}
#|﻿site,panel_id,GPVS_참고유형_ko,source_path,source_key_ko,비고_ko
#|conalog,45dfa600-79b7-428e-95d3-22345a068986.1.0,무가시형 계열,_share/gpvs_fault_family_eval_cases.csv,site+panel_id,"prediction_source=critical_phenotype_v3, fallback_rule=resolved_by_critical_phenotype_v3, error_type=correct, vendor_fault_family=none_visible"
#|conalog,7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0,전기적 고장 계열,_share/gpvs_fault_family_eval_cases.csv,site+panel_id,"prediction_source=critical_phenotype_v3, fallback_rule=resolved_by_critical_phenotype_v3, error_type=correct, vendor_fault_family=diode_like"
#|conalog,c42997a6-5881-47e7-9035-7de8a2673b54.1.1,개방/장치이상 계열,_share/gpvs_fault_family_eval_cases.csv,site+panel_id,"prediction_source=strict_day_core_fallback, fallback_rule=legacy_open_device, error_type=correct, vendor_fault_family=open_or_device_issue_like"
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.15,공통원인/인버터측 계열,_share/gpvs_fault_family_eval_cases.csv,site+panel_id,"prediction_source=strict_day_core_fallback, fallback_rule=same_day_group_collapse, error_type=correct, vendor_fault_family=group_or_inverter_side_like"
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.16,공통원인/인버터측 계열,_share/gpvs_fault_family_eval_cases.csv,site+panel_id,"prediction_source=strict_day_core_fallback, fallback_rule=same_day_group_collapse, error_type=correct, vendor_fault_family=group_or_inverter_side_like"
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.17,공통원인/인버터측 계열,_share/gpvs_fault_family_eval_cases.csv,site+panel_id,"prediction_source=strict_day_core_fallback, fallback_rule=same_day_group_collapse, error_type=correct, vendor_fault_family=group_or_inverter_side_like"
#|gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.4.15,공통원인/인버터측 계열,_share/gpvs_fault_family_eval_cases.csv,site+panel_id,"prediction_source=strict_day_core_fallback, fallback_rule=collapse_overrides_open_device, error_type=correct, vendor_fault_family=group_or_inverter_side_like"
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7,전기적 고장 계열,_share/gpvs_fault_family_eval_cases.csv,site+panel_id,"prediction_source=critical_phenotype_v3, fallback_rule=resolved_by_critical_phenotype_v3, error_type=correct, vendor_fault_family=diode_like"
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.9,불확실,_share/gpvs_fault_family_eval_cases.csv,site+panel_id,"prediction_source=critical_phenotype_v3, fallback_rule=resolved_by_critical_phenotype_v3, error_type=abstain_uncertain, vendor_fault_family=none_visible"
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16,전기적 고장 계열,_share/gpvs_fault_family_eval_cases.csv,site+panel_id,"prediction_source=critical_phenotype_v3, fallback_rule=resolved_by_critical_phenotype_v3, error_type=correct, vendor_fault_family=diode_like"
#|ktc_ess,10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12,불확실,_share/gpvs_fault_family_eval_cases.csv,site+panel_id,"prediction_source=critical_phenotype_v3, fallback_rule=resolved_by_critical_phenotype_v3, error_type=abstain_uncertain, vendor_fault_family=diode_like"
#|ktc_ess,70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4,전기적 고장 계열,_share/gpvs_fault_family_eval_cases.csv,site+panel_id,"prediction_source=critical_phenotype_v3, fallback_rule=resolved_by_critical_phenotype_v3, error_type=correct, vendor_fault_family=module_damage_like"
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 701, "endswith_newline": true, "lines": 2, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpvs_panel_attach_feasibility_v1.csv", "role": "frozen_share_input", "sha256": "5ae50335455718a82408f37fb0577d34e65f258353305dcc895403fc0bf60213"}
#|﻿GPVS_패널별_직접판정_가능여부,근거_ko,최선_후보_파일,overlap_panel_count,overlap_rate,다음권장조치_ko
#|가능,_share/gpvs_fault_family_eval_cases.csv 에 site/panel_id와 GPVS family type이 함께 저장돼 있어 current panel table 25개 중 12개 panel에 direct attach가 가능하다. 다만 candidate panel 14개 전체가 current panel universe를 덮는 것은 아니므로 부분 attach로 읽어야 한다.,_share/gpvs_fault_family_eval_cases.csv,12,0.48,"겹치는 panel에는 GPVS reference type을 보조축으로 붙이고, 겹치지 않는 panel은 미부착으로 유지한다. type-level/aggregate GPVS summary는 계속 별도 해석용으로만 둔다."
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 11433, "endswith_newline": true, "lines": 53, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_gpvs_panel_attach_inventory_v1.csv", "role": "frozen_share_input", "sha256": "f36125c3b98480f23c029f2a6f1ff8432b653b3209191ac7137db4433fb14f49"}
#|﻿경로,존재여부,파일종류_ko,granularity_ko,panel_id_컬럼존재_flag,site_컬럼존재_flag,유형_컬럼존재_flag,점수_컬럼존재_flag,panel_attach_candidate_flag,current_panel_count,candidate_panel_count,overlap_panel_count,overlap_rate,attachability_note_ko,note_ko
#|_share/gpvs_fault_family_eval_cases.csv,1,테이블,패널수준,1,1,1,0,1,25,14,12,0.48,site+panel_id direct match 가능,site+panel_id로 current panel table과 연결 가능한 panel-level GPVS reference file
#|_share/external_gpvs_20260304_215400.zip,1,압축파일,불명확,0,0,0,0,0,,,,,,압축 보관본이라 직접 컬럼 검사 없이 inventory에만 포함
#|_share/external_gpvs_20260304_215400/EXTERNAL_GPVS_METRICS.csv,1,테이블,집계수준,0,0,0,1,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|_share/external_gpvs_20260304_215400/EXTERNAL_GPVS_ONEPAGE.md,1,문서,집계수준,0,0,0,0,0,,,,,유형/집계 설명용 문서,문서형 요약 파일이라 panel direct attach source 아님
#|_share/external_gpvs_20260304_215400/gpvs_window_scores.csv,1,테이블,에피소드수준,0,0,1,0,0,,,,,유형 label은 있지만 panel key가 없어 type-level/aggregate 해석만 가능,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|_share/final_all_20260304_215400/external_gpvs_20260304_215400.zip,1,압축파일,불명확,0,0,0,0,0,,,,,,압축 보관본이라 직접 컬럼 검사 없이 inventory에만 포함
#|_share/gpvs_fault_family_confusion.csv,1,테이블,유형수준,0,0,1,0,0,,,,,유형 label은 있지만 panel key가 없어 type-level/aggregate 해석만 가능,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|_share/gpvs_fault_family_f1_summary.csv,1,테이블,유형수준,0,0,1,1,0,,,,,유형 label은 있지만 panel key가 없어 type-level/aggregate 해석만 가능,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|_share/panel_day_engine_gpv7_perf_summary_v1.csv,1,테이블,불명확,0,0,0,0,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|_share/panel_day_engine_gpvs_panel_attach_candidates_v1.csv,1,테이블,패널수준,1,1,0,0,0,,,,,panel key는 있지만 유형 label이 없어 direct verdict attach source로는 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|_share/panel_day_engine_gpvs_panel_attach_feasibility_v1.csv,1,테이블,집계수준,0,0,0,1,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|_share/panel_day_engine_gpvs_panel_attach_inventory_v1.csv,1,테이블,집계수준,0,0,0,1,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/_download/GPVS_Faults/n76t439f65-1/CSV_Files.zip,1,압축파일,불명확,0,0,0,0,0,,,,,,압축 보관본이라 직접 컬럼 검사 없이 inventory에만 포함
#|data/gpvs/_download/GPVS_Faults/n76t439f65-1/CSV_Files/F0L.csv,1,테이블,불명확,0,0,0,0,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/_download/GPVS_Faults/n76t439f65-1/CSV_Files/F0M.csv,1,테이블,불명확,0,0,0,0,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/_download/GPVS_Faults/n76t439f65-1/CSV_Files/F1L.csv,1,테이블,불명확,0,0,0,0,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/_download/GPVS_Faults/n76t439f65-1/CSV_Files/F1M.csv,1,테이블,불명확,0,0,0,0,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/_download/GPVS_Faults/n76t439f65-1/CSV_Files/F2L.csv,1,테이블,불명확,0,0,0,0,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/_download/GPVS_Faults/n76t439f65-1/CSV_Files/F2M.csv,1,테이블,불명확,0,0,0,0,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/_download/GPVS_Faults/n76t439f65-1/CSV_Files/F3L.csv,1,테이블,불명확,0,0,0,0,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/_download/GPVS_Faults/n76t439f65-1/CSV_Files/F3M.csv,1,테이블,불명확,0,0,0,0,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/_download/GPVS_Faults/n76t439f65-1/CSV_Files/F4L.csv,1,테이블,불명확,0,0,0,0,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/_download/GPVS_Faults/n76t439f65-1/CSV_Files/F4M.csv,1,테이블,불명확,0,0,0,0,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/_download/GPVS_Faults/n76t439f65-1/CSV_Files/F5L.csv,1,테이블,불명확,0,0,0,0,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/_download/GPVS_Faults/n76t439f65-1/CSV_Files/F5M.csv,1,테이블,불명확,0,0,0,0,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/_download/GPVS_Faults/n76t439f65-1/CSV_Files/F6L.csv,1,테이블,불명확,0,0,0,0,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/_download/GPVS_Faults/n76t439f65-1/CSV_Files/F6M.csv,1,테이블,불명확,0,0,0,0,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/_download/GPVS_Faults/n76t439f65-1/CSV_Files/F7L.csv,1,테이블,불명확,0,0,0,0,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/_download/GPVS_Faults/n76t439f65-1/CSV_Files/F7M.csv,1,테이블,불명확,0,0,0,0,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/out/EXTERNAL_GPVS_BYTYPE_METRICS.csv,1,테이블,유형수준,0,0,1,1,0,,,,,유형 label은 있지만 panel key가 없어 type-level/aggregate 해석만 가능,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/out/EXTERNAL_GPVS_BYTYPE_ONEPAGE.md,1,문서,유형수준,0,0,0,0,0,,,,,유형/집계 설명용 문서,문서형 요약 파일이라 panel direct attach source 아님
#|data/gpvs/out/EXTERNAL_GPVS_ENSEMBLE2_BYTYPE_METRICS.csv,1,테이블,유형수준,0,0,1,1,0,,,,,유형 label은 있지만 panel key가 없어 type-level/aggregate 해석만 가능,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/out/EXTERNAL_GPVS_ENSEMBLE2_METRICS.csv,1,테이블,집계수준,0,0,0,1,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/out/EXTERNAL_GPVS_ENSEMBLE2_ONEPAGE.md,1,문서,집계수준,0,0,0,0,0,,,,,유형/집계 설명용 문서,문서형 요약 파일이라 panel direct attach source 아님
#|data/gpvs/out/EXTERNAL_GPVS_ENSEMBLE3_BYTYPE_METRICS.csv,1,테이블,유형수준,0,0,1,1,0,,,,,유형 label은 있지만 panel key가 없어 type-level/aggregate 해석만 가능,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/out/EXTERNAL_GPVS_ENSEMBLE3_METRICS.csv,1,테이블,집계수준,0,0,0,1,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/out/EXTERNAL_GPVS_ENSEMBLE3_ONEPAGE.md,1,문서,집계수준,0,0,0,0,0,,,,,유형/집계 설명용 문서,문서형 요약 파일이라 panel direct attach source 아님
#|data/gpvs/out/EXTERNAL_GPVS_ENSEMBLE_BYTYPE_METRICS.csv,1,테이블,유형수준,0,0,1,1,0,,,,,유형 label은 있지만 panel key가 없어 type-level/aggregate 해석만 가능,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/out/EXTERNAL_GPVS_ENSEMBLE_METRICS.csv,1,테이블,집계수준,0,0,0,1,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/out/EXTERNAL_GPVS_ENSEMBLE_ONEPAGE.md,1,문서,집계수준,0,0,0,0,0,,,,,유형/집계 설명용 문서,문서형 요약 파일이라 panel direct attach source 아님
#|data/gpvs/out/EXTERNAL_GPVS_METRICS.csv,1,테이블,집계수준,0,0,0,1,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/out/EXTERNAL_GPVS_ONEPAGE.md,1,문서,집계수준,0,0,0,0,0,,,,,유형/집계 설명용 문서,문서형 요약 파일이라 panel direct attach source 아님
#|data/gpvs/out/EXTERNAL_GPVS_SUPERVISED2_METRICS.csv,1,테이블,집계수준,0,0,0,1,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/out/EXTERNAL_GPVS_SUPERVISED2_ONEPAGE.md,1,문서,집계수준,0,0,0,0,0,,,,,유형/집계 설명용 문서,문서형 요약 파일이라 panel direct attach source 아님
#|data/gpvs/out/EXTERNAL_GPVS_SUPERVISED3_METRICS.csv,1,테이블,집계수준,0,0,0,1,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/out/EXTERNAL_GPVS_SUPERVISED3_ONEPAGE.md,1,문서,집계수준,0,0,0,0,0,,,,,유형/집계 설명용 문서,문서형 요약 파일이라 panel direct attach source 아님
#|data/gpvs/out/EXTERNAL_GPVS_SUPERVISED_METRICS.csv,1,테이블,집계수준,0,0,0,1,0,,,,,panel key와 유형 label이 모두 부족,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|data/gpvs/out/EXTERNAL_GPVS_SUPERVISED_ONEPAGE.md,1,문서,집계수준,0,0,0,0,0,,,,,유형/집계 설명용 문서,문서형 요약 파일이라 panel direct attach source 아님
#|data/gpvs/out/gpvs_window_scores.csv,1,테이블,에피소드수준,0,0,1,0,0,,,,,유형 label은 있지만 panel key가 없어 type-level/aggregate 해석만 가능,current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함
#|docs/OPS_GPVS_FAULT_FAMILY_F1.md,1,문서,유형수준,0,0,0,0,0,,,,,,문서형 요약 파일이라 panel direct attach source 아님
#|docs/OPS_PANEL_DAY_ENGINE_GPVS_PANEL_ATTACH_AUDIT_V1.md,1,문서,불명확,0,0,0,0,0,,,,,,문서형 요약 파일이라 panel direct attach source 아님
#|docs/reports/gpvs_final_summary.md,1,문서,집계수준,0,0,0,0,0,,,,,유형/집계 설명용 문서,문서형 요약 파일이라 panel direct attach source 아님
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 1622, "endswith_newline": true, "lines": 6, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_kernellog_project_mapping_v1.csv", "role": "frozen_share_input", "sha256": "04d816865eef263b2691a7e5d3726a811764cbdde0aaac548e1c31d84fc0c4b5"}
#|﻿커널로그_증상명,주_프로젝트분류,보조_프로젝트분류,설명_ko,주의_ko
#|출력 저하형,전조형 고장,급작 고장,출력이 서서히 눌리거나 회복 없이 약해지는 증상은 전조형 고장 쪽 해석이 기본이다. 다만 anchor 근처 급락이면 급작 고장 보조 해석이 붙는다.,출력만 보고 물리 root-cause를 단정하지 말고 전압/전류 및 fault anchor 문맥을 함께 본다.
#|전압 변화형,급작 고장,전조형 고장,전압 collapse나 급격한 전압 변화는 abrupt anchor와 더 잘 맞는다. 다만 반복적으로 누적되면 전조형 해석 보조가 가능하다.,전압 변화만으로 diode/open/device를 확정하지 말고 same-day collapse 범위와 현장 note를 같이 본다.
#|패턴 이상형,같이 흔들리는 이상,오경보,여러 패널이 같은 날 비슷하게 흔들리면 site/context 쪽 패턴 이상으로 읽는 편이 안전하다.,패턴 이상형은 confusion matrix가 아니라 해석 매핑이다. panel-local fault와 직접 동일시하면 안 된다.
#|불안정형,반복 이상,오경보,짧게 반복되거나 들쑥날쑥한 이상은 반복 이상/monitor lane 쪽으로 우선 해석한다.,반복된다고 바로 고장으로 승격하지 말고 output-normal monitor 문맥과 함께 본다.
#|복합형,급작 고장,같이 흔들리는 이상,"출력 저하와 전압 변화, breadth 신호가 겹치면 복합형으로 보고 abrupt와 common-cause 가능성을 함께 남긴다.",복합형은 해석 보류용 분류다. unsupported 물리 root-cause 명칭으로 과장하지 않는다.
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 3673, "endswith_newline": true, "lines": 8, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_non_precursor_performance_cases_v1.csv", "role": "frozen_share_input", "sha256": "bc7396d7fac075691477edb5e2a6934dd35f5c006749ad86fa7bb142b8fbf588"}
#|﻿eval_bucket_v2,site,panel_id,anchor_date,anchor_source,vendor_fault_family,truth_case_id,candidate_validity,vendor_reply_class,first_confirmed_fault_date,confirmed_fault_available_flag,confirmed_fault_lead_days_to_fault_start,confirmed_fault_hit_by_anchor_flag,confirmed_fault_hit_within_3d_after_flag,confirmed_fault_hit_within_7d_after_flag,first_critical_fault_date,critical_fault_available_flag,critical_fault_lead_days_to_fault_start,critical_fault_hit_by_anchor_flag,critical_fault_hit_within_3d_after_flag,critical_fault_hit_within_7d_after_flag,first_final_fault_date,final_fault_available_flag,final_fault_lead_days_to_fault_start,final_fault_hit_by_anchor_flag,final_fault_hit_within_3d_after_flag,final_fault_hit_within_7d_after_flag,abrupt_eval_reason_ko,any_group_off_like_flag,any_shadow_like_flag,any_common_cause_like_flag,any_local_precursor_alert_flag,any_final_fault_flag,route_eval_reason_ko,descriptive_only_reason_ko
#|abrupt_or_no_precursor_now,gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7,2025-06-08,fault_panel_event_audit.strict_trigger_date,diode_like,fault_event_audit|gangui|bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7|2025-06-08,true_positive,vendor_pattern_positive,,0,,0,0,0,2025-06-08,1,0.0,1,0,0,,0,,0,0,0,anchor 전후 7일 내 hard fault marker가 약해 abrupt bucket에서도 late/miss 성격이 큼,0,0,0,0,0,,
#|abrupt_or_no_precursor_now,gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16,2025-06-08,fault_panel_event_audit.strict_trigger_date,diode_like,fault_event_audit|gangui|bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16|2025-06-08,true_positive,vendor_pattern_positive,,0,,0,0,0,2025-06-08,1,0.0,1,0,0,2025-06-08,1,0.0,1,0,0,anchor 시점까지 final_fault가 이미 확인되어 abrupt detection by-anchor hit로 해석,0,0,0,0,0,,
#|abrupt_or_no_precursor_now,ktc_ess,10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12,2025-08-16,fault_panel_event_audit.strict_trigger_date,diode_like,fault_event_audit|ktc_ess|10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12|2025-08-16,true_positive,vendor_pattern_positive,,0,,0,0,0,2025-08-16,1,0.0,1,0,0,2025-08-16,1,0.0,1,0,0,anchor 시점까지 final_fault가 이미 확인되어 abrupt detection by-anchor hit로 해석,0,0,0,0,0,,
#|non_panel_or_common_cause,conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.15,2024-12-06,strict_trigger_date,group_or_inverter_side_like,reaudit|conalog|d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.15|2024-12-06,group_side,field_confirmed_positive,,0,,0,0,0,,0,,0,0,0,,0,,0,0,0,,0,0,0,0,1,review truth는 group/inverter 쪽이지만 현재 panel-day routing evidence는 약함,
#|non_panel_or_common_cause,conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.16,2024-12-06,strict_trigger_date,group_or_inverter_side_like,reaudit|conalog|d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.16|2024-12-06,group_side,field_confirmed_positive,,0,,0,0,0,,0,,0,0,0,,0,,0,0,0,,0,0,0,0,1,review truth는 group/inverter 쪽이지만 현재 panel-day routing evidence는 약함,
#|non_panel_or_common_cause,conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.17,2024-12-06,strict_trigger_date,group_or_inverter_side_like,reaudit|conalog|d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.17|2024-12-06,group_side,field_confirmed_positive,,0,,0,0,0,,0,,0,0,0,,0,,0,0,0,,0,0,0,0,1,review truth는 group/inverter 쪽이지만 현재 panel-day routing evidence는 약함,
#|non_panel_or_common_cause,gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.4.15,2025-11-11,strict_trigger_date,group_or_inverter_side_like,reaudit|gangui|4fd0c566-e25e-4d51-96ca-57cc46940593.4.15|2025-11-11,group_side,vendor_likely_positive,,0,,0,0,0,,0,,0,0,0,,0,,0,0,0,,0,0,0,0,1,review truth는 group/inverter 쪽이지만 현재 panel-day routing evidence는 약함,
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 7704, "endswith_newline": true, "lines": 24, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_operator_workflow_default_v1.csv", "role": "frozen_share_input", "sha256": "b535662d24c124d6833bb6517625a763e2b682c1f79506ab021aaa8869a4724f"}
#|﻿preview_attention_class,site,display_entity_id,display_start_date,display_end_date,display_span_or_day_count,display_shape_or_cluster_kind,display_status_or_tier,display_score,linked_ref_flag,truth_ref_flag,cluster_panel_count,changed_since_previous_flag,latest_delta_source,latest_delta_class,latest_delta_reason_ko,digest_reason_ko,workflow_policy_name,workflow_role,workflow_priority_class,workflow_reason_ko
#|queue_run,ktc_ess,10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12,2026-02-11,2026-02-11,1,short_alert_run,ongoing_run,9.244065985713108,0,0,1,0,none,,,current queue_run item이며 직전 snapshot 대비 변화 없음,baseline_plus_discovery_cluster,primary_attention,queue_priority,기본 queue attention
#|queue_run,gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7,2026-02-18,2026-02-19,2,short_alert_run,ongoing_run,8.548559738206253,1,0,1,0,none,,,current queue_run item이며 직전 snapshot 대비 변화 없음,baseline_plus_discovery_cluster,primary_attention,queue_priority,기본 queue attention
#|queue_run,conalog,c42997a6-5881-47e7-9035-7de8a2673b54.0.1,2026-02-15,2026-02-18,4,medium_alert_run,ongoing_run,5.766138592917966,0,0,1,0,none,,,current queue_run item이며 직전 snapshot 대비 변화 없음,baseline_plus_discovery_cluster,primary_attention,queue_priority,기본 queue attention
#|queue_run,gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.1.12,2026-02-07,2026-02-19,13,chronic_alert_run,ongoing_run,5.7198876111621075,0,0,1,0,none,,,current queue_run item이며 직전 snapshot 대비 변화 없음,baseline_plus_discovery_cluster,primary_attention,queue_priority,기본 queue attention
#|queue_run,sinhyo,43269809-c7ab-4f87-b228-095e2785c744.1.4,2026-02-12,2026-02-16,5,medium_alert_run,ongoing_run,4.933262216137523,0,0,1,0,none,,,current queue_run item이며 직전 snapshot 대비 변화 없음,baseline_plus_discovery_cluster,primary_attention,queue_priority,기본 queue attention
#|queue_run,sinhyo,43269809-c7ab-4f87-b228-095e2785c744.1.5,2026-02-12,2026-02-16,5,medium_alert_run,ongoing_run,4.210022250819412,0,0,1,0,none,,,current queue_run item이며 직전 snapshot 대비 변화 없음,baseline_plus_discovery_cluster,primary_attention,queue_priority,기본 queue attention
#|queue_run,gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.5.4,2026-02-15,2026-02-19,5,medium_alert_run,ongoing_run,2.887934761625337,0,0,1,0,none,,,current queue_run item이며 직전 snapshot 대비 변화 없음,baseline_plus_discovery_cluster,primary_attention,queue_priority,기본 queue attention
#|watch_now_panel,ktc_ess,70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4,2025-04-14,2025-04-30,17,chronic_alert_run,watch_now,12.635115877851456,1,0,1,0,none,,,current watch_now_panel item이며 직전 snapshot 대비 변화 없음,baseline_plus_discovery_cluster,primary_attention,watch_priority,기본 watch attention
#|watch_now_panel,gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.9,2025-11-08,2025-11-18,11,chronic_alert_run,watch_now,11.698734151421789,0,0,1,0,none,,,current watch_now_panel item이며 직전 snapshot 대비 변화 없음,baseline_plus_discovery_cluster,primary_attention,watch_priority,기본 watch attention
#|watch_now_panel,conalog,c42997a6-5881-47e7-9035-7de8a2673b54.0.0,2025-01-23,2025-02-07,16,chronic_alert_run,watch_now,9.342491414600548,0,0,1,0,none,,,current watch_now_panel item이며 직전 snapshot 대비 변화 없음,baseline_plus_discovery_cluster,primary_attention,watch_priority,기본 watch attention
#|watch_now_panel,conalog,45dfa600-79b7-428e-95d3-22345a068986.2.0,2025-03-26,2025-04-11,17,chronic_alert_run,watch_now,7.353862945147238,0,0,1,0,none,,,current watch_now_panel item이며 직전 snapshot 대비 변화 없음,baseline_plus_discovery_cluster,primary_attention,watch_priority,기본 watch attention
#|watch_now_panel,sinhyo,af126597-828b-4ed4-8d9c-3e32bf5c6e9e.4.4,2026-01-05,2026-01-14,10,chronic_alert_run,watch_now,7.147061861675349,0,0,1,0,none,,,current watch_now_panel item이며 직전 snapshot 대비 변화 없음,baseline_plus_discovery_cluster,primary_attention,watch_priority,기본 watch attention
#|watch_now_panel,conalog,45dfa600-79b7-428e-95d3-22345a068986.1.0,2025-12-05,2025-12-15,11,chronic_alert_run,watch_now,7.02242340604254,0,0,1,0,none,,,current watch_now_panel item이며 직전 snapshot 대비 변화 없음,baseline_plus_discovery_cluster,primary_attention,watch_priority,기본 watch attention
#|watch_now_panel,sinhyo,af126597-828b-4ed4-8d9c-3e32bf5c6e9e.4.5,2025-01-05,2025-01-15,11,chronic_alert_run,watch_now,6.491273929736413,0,0,1,0,none,,,current watch_now_panel item이며 직전 snapshot 대비 변화 없음,baseline_plus_discovery_cluster,primary_attention,watch_priority,기본 watch attention
#|watch_now_panel,conalog,c42997a6-5881-47e7-9035-7de8a2673b54.2.0,2025-04-07,2025-04-21,15,chronic_alert_run,watch_now,6.391990839009163,0,0,1,0,none,,,current watch_now_panel item이며 직전 snapshot 대비 변화 없음,baseline_plus_discovery_cluster,primary_attention,watch_priority,기본 watch attention
#|watch_now_panel,ktc_ess,e089076c-92c1-4365-8641-2182b4f274e6.0.1,2025-08-16,2025-08-27,12,chronic_alert_run,watch_now,3.825935361375034,0,0,1,0,none,,,current watch_now_panel item이며 직전 snapshot 대비 변화 없음,baseline_plus_discovery_cluster,primary_attention,watch_priority,기본 watch attention
#|watch_now_panel,ktc_ess,e089076c-92c1-4365-8641-2182b4f274e6.0.2,2025-08-16,2025-08-27,12,chronic_alert_run,watch_now,3.717724120789715,0,0,1,0,none,,,current watch_now_panel item이며 직전 snapshot 대비 변화 없음,baseline_plus_discovery_cluster,primary_attention,watch_priority,기본 watch attention
#|watch_now_panel,ktc_ess,e089076c-92c1-4365-8641-2182b4f274e6.0.5,2025-08-16,2025-08-27,12,chronic_alert_run,watch_now,3.680275111862274,0,0,1,0,none,,,current watch_now_panel item이며 직전 snapshot 대비 변화 없음,baseline_plus_discovery_cluster,primary_attention,watch_priority,기본 watch attention
#|secondary_value_cluster,conalog,conalog_cluster_002,2025-12-23,2025-12-23,1,discovery_cluster,secondary_discovery_cluster,17.282790522027085,1,0,1,0,none,,,current secondary_value_cluster item이며 직전 snapshot 대비 변화 없음,baseline_plus_discovery_cluster,supplemental_discovery,discovery_priority,기본 workflow에 포함된 discovery cluster
#|secondary_value_cluster,conalog,conalog_cluster_001,2025-05-09,2025-05-09,1,discovery_cluster,secondary_discovery_cluster,17.28279030010019,1,0,1,0,none,,,current secondary_value_cluster item이며 직전 snapshot 대비 변화 없음,baseline_plus_discovery_cluster,supplemental_discovery,discovery_priority,기본 workflow에 포함된 discovery cluster
#|secondary_value_cluster,gangui,gangui_cluster_003,2025-11-17,2025-11-27,11,discovery_cluster,secondary_discovery_cluster,17.203361664330053,1,0,8,0,none,,,current secondary_value_cluster item이며 직전 snapshot 대비 변화 없음,baseline_plus_discovery_cluster,supplemental_discovery,discovery_priority,기본 workflow에 포함된 discovery cluster
#|secondary_value_cluster,gangui,gangui_cluster_002,2025-07-16,2025-07-17,2,discovery_cluster,secondary_discovery_cluster,12.918087686819952,1,0,1,0,none,,,current secondary_value_cluster item이며 직전 snapshot 대비 변화 없음,baseline_plus_discovery_cluster,supplemental_discovery,discovery_priority,기본 workflow에 포함된 discovery cluster
#|secondary_value_cluster,gangui,gangui_cluster_001,2025-06-22,2025-06-24,3,discovery_cluster,secondary_discovery_cluster,10.185707247243844,1,0,1,0,none,,,current secondary_value_cluster item이며 직전 snapshot 대비 변화 없음,baseline_plus_discovery_cluster,supplemental_discovery,discovery_priority,기본 workflow에 포함된 discovery cluster
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 22626, "endswith_newline": true, "lines": 26, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_panel_multiaxis_verdict_v1.csv", "role": "frozen_share_input", "sha256": "a043a9cf85bd2aaf02efc36cc8fe13dc1edeac060aaf5e938ed3352539f8d3b1"}
#|﻿site,panel_id,사건유형_ko,사건유형_해석_ko,최종고장양상_ko,대표판정_ko,사건이력_ko,전조흔적_flag,순수급작_flag,전조평가셋편입_flag,급작평가셋편입_flag,해석대평가차이_ko,운영최초전조발견일,운영최초전조마커,사건해석상전조시작일,benchmark전조시작일,전조형이력_flag,급작고장이력_flag,공통원인이력_flag,반복이상이력_flag,패널고장여부_ko,GPVS_적용대상_ko,커널로그_증상명_ko,커널로그_원인군_ko,GPVS_부착상태_ko,GPVS_내부참고유형_ko,GPVS_외부참조패턴_ko,GPVS_참조사용등급_ko,GPVS_참조설명_ko,세부fault_type_code,세부fault_type_label_ko,세부fault_부착상태_ko,세부fault_근거파일_ko,세부fault_기준일,세부fault_보류사유_ko,운영위치_ko,판정주의_ko
#|conalog,45dfa600-79b7-428e-95d3-22345a068986.1.0,반복 이상,반복 이상,해당없음,반복 이상,반복 이상,0,0,0,0,,,,,,0,0,0,1,미확정,비대상,불안정형,불충분,비대상,,,,,,,비대상,,,,경과 관찰,"반복 이상은 chronic monitor/반복 lane 해석이며 stable fault classifier claim이 아니다. watch_now_panel 반복 lane이라 nearest symptom 축으로 불안정형만 부착했다. 사건유형=반복 이상, 최종고장양상=해당없음 사건이력=반복 이상 workflow watch_now_panel 포함 고장 패널이 아니어서 GPVS 적용 대상 아님"
#|conalog,45dfa600-79b7-428e-95d3-22345a068986.2.0,반복 이상,반복 이상,해당없음,반복 이상,반복 이상,0,0,0,0,,,,,,0,0,0,1,미확정,비대상,불안정형,불충분,비대상,,,,,,,비대상,,,,경과 관찰,"반복 이상은 chronic monitor/반복 lane 해석이며 stable fault classifier claim이 아니다. watch_now_panel 반복 lane이라 nearest symptom 축으로 불안정형만 부착했다. 사건유형=반복 이상, 최종고장양상=해당없음 사건이력=반복 이상 workflow watch_now_panel 포함 고장 패널이 아니어서 GPVS 적용 대상 아님"
#|conalog,7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0,전조형 고장,전조형 고장,진행성 악화,전조형 고장,전조형 고장,1,0,1,0,,2024-11-08,first_cond_evt,2024-11-06,2024-11-08,1,0,0,0,고장,적용대상,전압 변화형,다이오드형,부착,전기적 고장 계열,국소 출력 불균형형,주의참고,"일부 패널의 출력 균형이 깨지는 패턴으로, 부분 음영뿐 아니라 오염·열화·다이오드/접속 이상 등과 유사하게 보일 수 있음",,,보류,,2024-11-26,no_exact_date_match,현재 workflow 미포함,"전조형 고장 축은 current closeout 기준 exploratory 범위로만 읽는다. 커널로그 원인군은 abrupt6 symptom map의 `다이오드형` 를 연결했다. 사건유형=전조형 고장, 최종고장양상=진행성 악화 사건이력=전조형 고장 precursor onset truth positive universe 포함; fault panel event audit explicit rule 적용; 현재 workflow default row에는 아직 없음 세부fault_type 보류=no_exact_date_match GPVS learned by-type 세부fault=F4L, score=0.7663980163772397, margin=0.5351956345952494 fault panel event audit 재판정=전조형 고장/진행성 악화 retrospective_onset_date 비공란, strict_trigger_date 비공란, retrospective_onset_date < strict_trigger_date, onset_confidence=high, onset_method=persistent_5of7 이 모두 성립; 사건유형_재판정_ko == 전조형 고장 이고 급격 종료 규칙은 아니므로 진행성 악화로 둠; abrupt_positive_evidence_flag=1; strict precursor truth positive 포함; vendor_fault_family=diode_like, vendor_reply_class=vendor_pattern_positive 운영상 최초 전조 발견=2024-11-08 (first_cond_evt) / 사건 해석상 전조 시작=2024-11-06 / benchmark 전조 시작=2024-11-08"
#|conalog,c42997a6-5881-47e7-9035-7de8a2673b54.0.0,반복 이상,반복 이상,해당없음,반복 이상,반복 이상,0,0,0,0,,,,,,0,0,0,1,미확정,비대상,불안정형,불충분,비대상,,,,,,,비대상,,,,경과 관찰,"반복 이상은 chronic monitor/반복 lane 해석이며 stable fault classifier claim이 아니다. watch_now_panel 반복 lane이라 nearest symptom 축으로 불안정형만 부착했다. 사건유형=반복 이상, 최종고장양상=해당없음 사건이력=반복 이상 workflow watch_now_panel 포함 고장 패널이 아니어서 GPVS 적용 대상 아님"
#|conalog,c42997a6-5881-47e7-9035-7de8a2673b54.0.1,불충분,불충분,불충분,불충분,,0,0,0,0,,,,,,0,0,0,0,미확정,비대상,불충분,불충분,비대상,,,,,,,비대상,,,,바로 확인,"현재 stored positive universe와 직접 연결되지 않아 사건 성격을 보수적으로 유지한다. 현재 stored field로 커널로그 증상축을 더 붙이기 어렵다. 사건유형=불충분, 최종고장양상=불충분 사건이력 없음 workflow current row 기반 fallback verdict 고장 패널이 아니어서 GPVS 적용 대상 아님"
#|conalog,c42997a6-5881-47e7-9035-7de8a2673b54.1.1,전조형 고장,전조형 고장,급격 종료,전조형 고장,전조형 고장(급격 종료),1,0,1,0,,2025-02-20,first_cond_evt,2025-01-20,2025-03-18,1,0,0,0,고장,적용대상,전압 변화형,개방/장치이상형,부착,개방/장치이상 계열,장치 응답 이상형,비권장,"센서/피드백 오류로 장치 응답이 어긋나는 패턴으로, 패널 물리 파손보다 장치 응답 이상 힌트로 해석",,,보류,,2025-03-21,no_exact_date_match,현재 workflow 미포함,"이 panel은 전조형 사건 한 건이 마지막에 급격 종료로 끝난 것으로 읽는다. event type과 terminal failure pattern은 분리해서 해석해야 한다. 커널로그 원인군은 abrupt6 symptom map의 `개방/장치이상형` 를 연결했다. 사건유형=전조형 고장, 최종고장양상=급격 종료 사건이력=전조형 고장(급격 종료) precursor onset truth positive universe 포함; single-panel forensic explicit rule 적용; fault panel event audit explicit rule 적용; 현재 workflow default row에는 아직 없음 세부fault_type 보류=no_exact_date_match GPVS learned by-type 세부fault=F2M, score=0.9999684297851252, margin=0.999937980965936 fault panel event audit 재판정=전조형 고장/급격 종료 retrospective_onset_date 비공란, strict_trigger_date 비공란, retrospective_onset_date < strict_trigger_date, onset_confidence=high, onset_method=persistent_5of7 이 모두 성립; first_final_fault_date == strict_trigger_date 이고 dead_diag_date <= strict_trigger_date + 1 day; abrupt_positive_evidence_flag=1; strict precursor truth positive 포함; vendor_fault_family=open_or_device_issue_like, vendor_reply_class=vendor_likely_positive explicit stored-field rule onset=2025-01-20, trigger=2025-03-21 stored-field rule 기준 retrospective_onset_date<strict_trigger_date, onset_confidence=high, onset_method=persistent_5of7 이라 전조형 고장으로 읽고 최종고장양상은 급격 종료로 둔다 현재 재감사 family hint=개방/장치이상형 (open_or_device_issue_like) 운영상 최초 전조 발견=2025-02-20 (first_cond_evt) / 사건 해석상 전조 시작=2025-01-20 / benchmark 전조 시작=2025-03-18"
#|conalog,c42997a6-5881-47e7-9035-7de8a2673b54.2.0,반복 이상,반복 이상,해당없음,반복 이상,반복 이상,0,0,0,0,,,,,,0,0,0,1,미확정,비대상,불안정형,불충분,비대상,,,,,,,비대상,,,,경과 관찰,"반복 이상은 chronic monitor/반복 lane 해석이며 stable fault classifier claim이 아니다. watch_now_panel 반복 lane이라 nearest symptom 축으로 불안정형만 부착했다. 사건유형=반복 이상, 최종고장양상=해당없음 사건이력=반복 이상 workflow watch_now_panel 포함 고장 패널이 아니어서 GPVS 적용 대상 아님"
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.15,공통원인 이벤트,공통원인 이벤트,해당없음,공통원인 이벤트,공통원인 이벤트,0,0,0,0,,,,,,0,0,1,0,비고장,비대상,패턴 이상형,불충분,비대상,,,,,,,비대상,,,,현재 workflow 미포함,"공통원인 이벤트 축은 current closeout 기준 exploratory 범위로만 읽는다. 공통원인 representative verdict라 nearest symptom 축으로 패턴 이상형만 부착했다. 사건유형=공통원인 이벤트, 최종고장양상=해당없음 사건이력=공통원인 이벤트 common-cause descriptive positive universe 포함; 현재 workflow default row에는 아직 없음 고장 패널이 아니어서 GPVS 적용 대상 아님"
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.16,공통원인 이벤트,공통원인 이벤트,해당없음,공통원인 이벤트,공통원인 이벤트,0,0,0,0,,,,,,0,0,1,0,비고장,비대상,패턴 이상형,불충분,비대상,,,,,,,비대상,,,,현재 workflow 미포함,"공통원인 이벤트 축은 current closeout 기준 exploratory 범위로만 읽는다. 공통원인 representative verdict라 nearest symptom 축으로 패턴 이상형만 부착했다. 사건유형=공통원인 이벤트, 최종고장양상=해당없음 사건이력=공통원인 이벤트 common-cause descriptive positive universe 포함; 현재 workflow default row에는 아직 없음 고장 패널이 아니어서 GPVS 적용 대상 아님"
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.17,공통원인 이벤트,공통원인 이벤트,해당없음,공통원인 이벤트,공통원인 이벤트,0,0,0,0,,,,,,0,0,1,0,비고장,비대상,패턴 이상형,불충분,비대상,,,,,,,비대상,,,,현재 workflow 미포함,"공통원인 이벤트 축은 current closeout 기준 exploratory 범위로만 읽는다. 공통원인 representative verdict라 nearest symptom 축으로 패턴 이상형만 부착했다. 사건유형=공통원인 이벤트, 최종고장양상=해당없음 사건이력=공통원인 이벤트 common-cause descriptive positive universe 포함; 현재 workflow default row에는 아직 없음 고장 패널이 아니어서 GPVS 적용 대상 아님"
#|gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.1.12,불충분,불충분,불충분,불충분,,0,0,0,0,,,,,,0,0,0,0,미확정,비대상,불충분,불충분,비대상,,,,,,,비대상,,,,바로 확인,"현재 stored positive universe와 직접 연결되지 않아 사건 성격을 보수적으로 유지한다. 현재 stored field로 커널로그 증상축을 더 붙이기 어렵다. 사건유형=불충분, 최종고장양상=불충분 사건이력 없음 workflow current row 기반 fallback verdict 고장 패널이 아니어서 GPVS 적용 대상 아님"
#|gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.4.15,공통원인 이벤트,공통원인 이벤트,해당없음,공통원인 이벤트,공통원인 이벤트,0,0,0,0,,,,,,0,0,1,0,비고장,비대상,패턴 이상형,불충분,비대상,,,,,,,비대상,,,,현재 workflow 미포함,"공통원인 이벤트 축은 current closeout 기준 exploratory 범위로만 읽는다. 공통원인 representative verdict라 nearest symptom 축으로 패턴 이상형만 부착했다. 사건유형=공통원인 이벤트, 최종고장양상=해당없음 사건이력=공통원인 이벤트 common-cause descriptive positive universe 포함; 현재 workflow default row에는 아직 없음 고장 패널이 아니어서 GPVS 적용 대상 아님"
#|gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.5.4,불충분,불충분,불충분,불충분,,0,0,0,0,,,,,,0,0,0,0,미확정,비대상,불충분,불충분,비대상,,,,,,,비대상,,,,바로 확인,"현재 stored positive universe와 직접 연결되지 않아 사건 성격을 보수적으로 유지한다. 현재 stored field로 커널로그 증상축을 더 붙이기 어렵다. 사건유형=불충분, 최종고장양상=불충분 사건이력 없음 workflow current row 기반 fallback verdict 고장 패널이 아니어서 GPVS 적용 대상 아님"
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7,급작 고장,급작 고장,급작 발생,급작 고장,급작 고장,0,1,0,1,,,,,,0,1,0,0,고장,적용대상,전압 변화형,다이오드형,부착,전기적 고장 계열,장치 응답 이상형,비권장,"센서/피드백 오류로 장치 응답이 어긋나는 패턴으로, 패널 물리 파손보다 장치 응답 이상 힌트로 해석",,,보류,,2025-06-08,no_exact_date_match,바로 확인,"급작 고장 축은 current closeout 기준 exploratory 범위로만 읽는다. 커널로그 원인군은 abrupt6 symptom map의 `다이오드형` 를 연결했다. 사건유형=급작 고장, 최종고장양상=급작 발생 사건이력=급작 고장 abrupt6 positive universe 포함; fault panel event audit explicit rule 적용 세부fault_type 보류=no_exact_date_match GPVS learned by-type 세부fault=F2M, score=0.9983614102233516, margin=0.996730629733898 fault panel event audit 재판정=급작 고장/급작 발생 abrupt positive evidence 가 있고, retrospective_onset_date 가 공란이거나 retrospective_onset_date == strict_trigger_date 이면서 onset_method=strict_trigger_fallback, onset_confidence != high 인 same-day fallback onset 이라 급작 고장으로 둠; 급격 종료 규칙은 아니지만 사건유형_재판정_ko == 급작 고장 이라 급작 발생으로 둠; abrupt_positive_evidence_flag=1; vendor_fault_family=diode_like, vendor_reply_class=vendor_pattern_positive"
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.9,반복 이상,반복 이상,해당없음,반복 이상,반복 이상,0,0,0,0,,,,,,0,0,0,1,미확정,비대상,불안정형,불충분,비대상,,,,,,,비대상,,,,경과 관찰,"반복 이상은 chronic monitor/반복 lane 해석이며 stable fault classifier claim이 아니다. watch_now_panel 반복 lane이라 nearest symptom 축으로 불안정형만 부착했다. 사건유형=반복 이상, 최종고장양상=해당없음 사건이력=반복 이상 workflow watch_now_panel 포함 고장 패널이 아니어서 GPVS 적용 대상 아님"
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16,급작 고장,급작 고장,급작 발생,급작 고장,급작 고장,0,1,0,1,,,,,,0,1,0,0,고장,적용대상,전압 변화형,다이오드형,부착,전기적 고장 계열,장치 응답 이상형,비권장,"센서/피드백 오류로 장치 응답이 어긋나는 패턴으로, 패널 물리 파손보다 장치 응답 이상 힌트로 해석",,,보류,,2025-06-08,no_exact_date_match,현재 workflow 미포함,"급작 고장 축은 current closeout 기준 exploratory 범위로만 읽는다. 커널로그 원인군은 abrupt6 symptom map의 `다이오드형` 를 연결했다. 사건유형=급작 고장, 최종고장양상=급작 발생 사건이력=급작 고장 abrupt6 positive universe 포함; fault panel event audit explicit rule 적용; 현재 workflow default row에는 아직 없음 세부fault_type 보류=no_exact_date_match GPVS learned by-type 세부fault=F2M, score=0.9909254812518792, margin=0.9818540541011564 fault panel event audit 재판정=급작 고장/급작 발생 abrupt positive evidence 가 있고, retrospective_onset_date 가 공란이거나 retrospective_onset_date == strict_trigger_date 이면서 onset_method=strict_trigger_fallback, onset_confidence != high 인 same-day fallback onset 이라 급작 고장으로 둠; 급격 종료 규칙은 아니지만 사건유형_재판정_ko == 급작 고장 이라 급작 발생으로 둠; abrupt_positive_evidence_flag=1; vendor_fault_family=diode_like, vendor_reply_class=vendor_pattern_positive"
#|ktc_ess,10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12,급작 고장,급작 고장,급작 발생,급작 고장,급작 고장,0,1,0,1,,,,,,0,1,0,0,고장,적용대상,전압 변화형,다이오드형,부착,불확실,국소 출력 불균형형,주의참고,"일부 패널의 출력 균형이 깨지는 패턴으로, 부분 음영뿐 아니라 오염·열화·다이오드/접속 이상 등과 유사하게 보일 수 있음",,,보류,,2025-08-16,no_exact_date_match,바로 확인,"급작 고장 축은 current closeout 기준 exploratory 범위로만 읽는다. 커널로그 원인군은 abrupt6 symptom map의 `다이오드형` 를 연결했다. 사건유형=급작 고장, 최종고장양상=급작 발생 사건이력=급작 고장 abrupt6 positive universe 포함; fault panel event audit explicit rule 적용 세부fault_type 보류=no_exact_date_match GPVS learned by-type 세부fault=F4L, score=0.8217373274556089, margin=0.7049574685022191 fault panel event audit 재판정=급작 고장/급작 발생 abrupt positive evidence 가 있고, retrospective_onset_date 가 공란이거나 retrospective_onset_date == strict_trigger_date 이면서 onset_method=strict_trigger_fallback, onset_confidence != high 인 same-day fallback onset 이라 급작 고장으로 둠; 급격 종료 규칙은 아니지만 사건유형_재판정_ko == 급작 고장 이라 급작 발생으로 둠; abrupt_positive_evidence_flag=1; vendor_fault_family=diode_like, vendor_reply_class=vendor_pattern_positive"
#|ktc_ess,70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4,전조형 고장,전조형 고장,진행성 악화,전조형 고장,전조형 고장,1,0,1,0,,2025-01-27,first_cond_evt,2025-01-25,2025-01-27,1,0,0,1,고장,적용대상,출력 저하형,모듈손상형,부착,전기적 고장 계열,장치 응답 이상형,비권장,"센서/피드백 오류로 장치 응답이 어긋나는 패턴으로, 패널 물리 파손보다 장치 응답 이상 힌트로 해석",,,보류,,2025-02-02,no_exact_date_match,경과 관찰,"전조형 고장 축은 current closeout 기준 exploratory 범위로만 읽는다. 커널로그 원인군은 abrupt6 symptom map의 `모듈손상형` 를 연결했다. 사건유형=전조형 고장, 최종고장양상=진행성 악화 사건이력=전조형 고장 precursor onset truth positive universe 포함; workflow watch_now_panel 포함; fault panel event audit explicit rule 적용 세부fault_type 보류=no_exact_date_match GPVS learned by-type 세부fault=F2M, score=0.9632018904449848, margin=0.926880388621922 fault panel event audit 재판정=전조형 고장/진행성 악화 retrospective_onset_date 비공란, strict_trigger_date 비공란, retrospective_onset_date < strict_trigger_date, onset_confidence=high, onset_method=persistent_5of7 이 모두 성립; 사건유형_재판정_ko == 전조형 고장 이고 급격 종료 규칙은 아니므로 진행성 악화로 둠; abrupt_positive_evidence_flag=1; strict precursor truth positive 포함; vendor_fault_family=module_damage_like, vendor_reply_class=vendor_likely_positive 운영상 최초 전조 발견=2025-01-27 (first_cond_evt) / 사건 해석상 전조 시작=2025-01-25 / benchmark 전조 시작=2025-01-27"
#|ktc_ess,e089076c-92c1-4365-8641-2182b4f274e6.0.1,반복 이상,반복 이상,해당없음,반복 이상,반복 이상,0,0,0,0,,,,,,0,0,0,1,미확정,비대상,불안정형,불충분,비대상,,,,,,,비대상,,,,경과 관찰,"반복 이상은 chronic monitor/반복 lane 해석이며 stable fault classifier claim이 아니다. watch_now_panel 반복 lane이라 nearest symptom 축으로 불안정형만 부착했다. 사건유형=반복 이상, 최종고장양상=해당없음 사건이력=반복 이상 workflow watch_now_panel 포함 고장 패널이 아니어서 GPVS 적용 대상 아님"
#|ktc_ess,e089076c-92c1-4365-8641-2182b4f274e6.0.2,반복 이상,반복 이상,해당없음,반복 이상,반복 이상,0,0,0,0,,,,,,0,0,0,1,미확정,비대상,불안정형,불충분,비대상,,,,,,,비대상,,,,경과 관찰,"반복 이상은 chronic monitor/반복 lane 해석이며 stable fault classifier claim이 아니다. watch_now_panel 반복 lane이라 nearest symptom 축으로 불안정형만 부착했다. 사건유형=반복 이상, 최종고장양상=해당없음 사건이력=반복 이상 workflow watch_now_panel 포함 고장 패널이 아니어서 GPVS 적용 대상 아님"
#|ktc_ess,e089076c-92c1-4365-8641-2182b4f274e6.0.5,반복 이상,반복 이상,해당없음,반복 이상,반복 이상,0,0,0,0,,,,,,0,0,0,1,미확정,비대상,불안정형,불충분,비대상,,,,,,,비대상,,,,경과 관찰,"반복 이상은 chronic monitor/반복 lane 해석이며 stable fault classifier claim이 아니다. watch_now_panel 반복 lane이라 nearest symptom 축으로 불안정형만 부착했다. 사건유형=반복 이상, 최종고장양상=해당없음 사건이력=반복 이상 workflow watch_now_panel 포함 고장 패널이 아니어서 GPVS 적용 대상 아님"
#|sinhyo,43269809-c7ab-4f87-b228-095e2785c744.1.4,불충분,불충분,불충분,불충분,,0,0,0,0,,,,,,0,0,0,0,미확정,비대상,불충분,불충분,비대상,,,,,,,비대상,,,,바로 확인,"현재 stored positive universe와 직접 연결되지 않아 사건 성격을 보수적으로 유지한다. 현재 stored field로 커널로그 증상축을 더 붙이기 어렵다. 사건유형=불충분, 최종고장양상=불충분 사건이력 없음 workflow current row 기반 fallback verdict 고장 패널이 아니어서 GPVS 적용 대상 아님"
#|sinhyo,43269809-c7ab-4f87-b228-095e2785c744.1.5,불충분,불충분,불충분,불충분,,0,0,0,0,,,,,,0,0,0,0,미확정,비대상,불충분,불충분,비대상,,,,,,,비대상,,,,바로 확인,"현재 stored positive universe와 직접 연결되지 않아 사건 성격을 보수적으로 유지한다. 현재 stored field로 커널로그 증상축을 더 붙이기 어렵다. 사건유형=불충분, 최종고장양상=불충분 사건이력 없음 workflow current row 기반 fallback verdict 고장 패널이 아니어서 GPVS 적용 대상 아님"
#|sinhyo,af126597-828b-4ed4-8d9c-3e32bf5c6e9e.4.4,반복 이상,반복 이상,해당없음,반복 이상,반복 이상,0,0,0,0,,,,,,0,0,0,1,미확정,비대상,불안정형,불충분,비대상,,,,,,,비대상,,,,경과 관찰,"반복 이상은 chronic monitor/반복 lane 해석이며 stable fault classifier claim이 아니다. watch_now_panel 반복 lane이라 nearest symptom 축으로 불안정형만 부착했다. 사건유형=반복 이상, 최종고장양상=해당없음 사건이력=반복 이상 workflow watch_now_panel 포함 고장 패널이 아니어서 GPVS 적용 대상 아님"
#|sinhyo,af126597-828b-4ed4-8d9c-3e32bf5c6e9e.4.5,반복 이상,반복 이상,해당없음,반복 이상,반복 이상,0,0,0,0,,,,,,0,0,0,1,미확정,비대상,불안정형,불충분,비대상,,,,,,,비대상,,,,경과 관찰,"반복 이상은 chronic monitor/반복 lane 해석이며 stable fault classifier claim이 아니다. watch_now_panel 반복 lane이라 nearest symptom 축으로 불안정형만 부착했다. 사건유형=반복 이상, 최종고장양상=해당없음 사건이력=반복 이상 workflow watch_now_panel 포함 고장 패널이 아니어서 GPVS 적용 대상 아님"
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 1366, "endswith_newline": true, "lines": 3, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_precursor_abrupt_consistency_cases_v1.csv", "role": "frozen_share_input", "sha256": "693771f5963bbafbc062bfaa3f34c75c6dabbe0293a9b64a669c6101bf9b4bc3"}
#|﻿site,panel_id,precursor_onset_date,precursor_fault_date,abrupt_anchor_date,abrupt_fault_date,lead_days_from_precursor_to_abrupt_fault,same_event_flag,distinct_event_flag,consistency_judgment_ko,reasoning_ko
#|conalog,7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0,2024-11-08,2024-11-26,2024-11-26,2024-11-26,18,1,0,같은 사건,precursor_onset=2024-11-08; precursor_fault=2024-11-26; abrupt_anchor=2024-11-26; abrupt_fault=2024-11-26; onset_to_abrupt_fault=18일; fault_date_gap=0일; selected_episode_end_to_abrupt_fault=1일; reaudit_first_warning=2024-11-06; reaudit_retrospective_onset=2024-11-06; precursor onset이 abrupt fault보다 먼저 나오고 precursor fault_start_date와 abrupt fault date가 같은/가까운 날짜라 한 evolving fault episode로 읽는 편이 안전하다.
#|ktc_ess,70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4,2025-01-27,2025-02-02,2025-02-02,2025-02-02,6,1,0,같은 사건,precursor_onset=2025-01-27; precursor_fault=2025-02-02; abrupt_anchor=2025-02-02; abrupt_fault=2025-02-02; onset_to_abrupt_fault=6일; fault_date_gap=0일; selected_episode_end_to_abrupt_fault=1일; reaudit_first_warning=2024-12-25; reaudit_retrospective_onset=2025-01-25; precursor onset이 abrupt fault보다 먼저 나오고 precursor fault_start_date와 abrupt fault date가 같은/가까운 날짜라 한 evolving fault episode로 읽는 편이 안전하다.
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 239, "endswith_newline": true, "lines": 2, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_precursor_abrupt_consistency_recommendation_v1.csv", "role": "frozen_share_input", "sha256": "a5f5d4279472b9cf169dcd1d7943dcba71322b0ecf1f299abd88a9c7e1ee621d"}
#|﻿recommended_next_handling,rationale_ko
#|relabel_overlap_as_precursor_led_faults,overlap 2건 모두 precursor onset이 abrupt fault보다 앞서고 fault/episode 날짜가 이어져 같은 사건으로 읽는 편이 더 자연스럽다.
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 522, "endswith_newline": true, "lines": 2, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_precursor_abrupt_consistency_summary_v1.csv", "role": "frozen_share_input", "sha256": "7948911e08de78b1978b982e6ed2865ebcd639fd8223df0e7b70b233c78564a5"}
#|﻿overlap_panel_count,same_event_count,distinct_event_count,ambiguous_count,current_unique_fault_panel_count,current_precursor_event_count,current_abrupt_event_count,corrected_precursor_led_fault_count,corrected_pure_abrupt_fault_count,note_ko
#|2,2,0,0,6,2,6,2,4,"전조형/급작 overlap panel만 따로 떼어 event-level consistency를 봤다. current panel table의 고유 고장패널수는 그대로 두고, overlap이 같은 사건이면 precursor-led fault with abrupt ending으로 읽는 해석만 제안한다."
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 2060, "endswith_newline": true, "lines": 4, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_precursor_onset_truth_v1.csv", "role": "frozen_share_input", "sha256": "5d19ea4cc44382378a8c57ddd5311215e33a94c17e3500fa8994d3f3f850bc0c"}
#|﻿site,panel_id,fault_start_date,vendor_fault_family,temporality_class,bounded_window_start,first_cond_evt_date,first_cond_evt_corroborated_date,first_signalcount2_date,first_pre_ews_date,first_ews_warning_date,first_pre_alarm_date,selected_episode_start_date,selected_episode_end_date,selected_episode_day_count,preferred_precursor_onset_date,preferred_onset_stage,preferred_onset_confidence,lead_days_from_preferred_onset_to_fault_start,onset_reason_ko,operational_first_precursor_detected_date,operational_first_precursor_marker_name,operational_lead_days_to_fault_start,interpretive_precursor_onset_date,interpretive_lead_days_to_fault_start,benchmark_precursor_onset_date,benchmark_lead_days_to_fault_start
#|conalog,7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0,2024-11-26,diode_like,progressive_local_precursor_expected,2024-10-27,2024-11-08,2024-11-09,2024-11-09,,,,2024-11-08,2024-11-25,18,2024-11-08,episode_start_before_corroborated_signal,medium,18,선택된 cond_evt episode 내부에 corroborated cond_evt 또는 signal_count>=2가 있어 episode 시작을 중간 신뢰 onset으로 채택,2024-11-08,first_cond_evt,18,2024-11-06,20,2024-11-08,18
#|conalog,c42997a6-5881-47e7-9035-7de8a2673b54.1.1,2025-03-21,open_or_device_issue_like,progressive_local_precursor_expected,2025-02-19,2025-02-20,2025-02-20,2025-02-20,2025-02-20,,,2025-03-18,2025-03-18,1,2025-03-18,episode_start_before_corroborated_signal,medium,3,선택된 cond_evt episode 내부에 corroborated cond_evt 또는 signal_count>=2가 있어 episode 시작을 중간 신뢰 onset으로 채택,2025-02-20,first_cond_evt,29,2025-01-20,60,2025-03-18,3
#|ktc_ess,70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4,2025-02-02,module_damage_like,progressive_local_precursor_expected,2025-01-03,2025-01-27,2025-01-27,2025-01-27,2025-01-27,2025-01-31,2025-01-31,2025-01-27,2025-02-01,6,2025-01-27,episode_start_before_alarm,strong,6,선택된 cond_evt episode 내부에 pre_alarm 또는 ews_warning가 있어 episode 시작을 강한 onset truth로 채택,2025-01-27,first_cond_evt,6,2025-01-25,8,2025-01-27,6
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 7454, "endswith_newline": true, "lines": 7, "path": "release/conalog_full_runtime_v1/package/_share/panel_day_engine_project_final_decision_pack_v1.csv", "role": "frozen_share_input", "sha256": "462144cf3895c12c67a95daf59fb82001148945c59da6ab99423514c13ec83b3"}
#|﻿eval_scope,current_data_decision,allowed_claim_strength,current_best_target_name,current_best_metric_kind,current_best_f1,current_best_positive_support,chosen_operational_workflow_name,release_gate_pass_flag,pipeline_pass_flag,final_usage_decision,final_reason_ko
#|step1_taxonomy,freeze_with_caution,bounded_current_data_claim,coverage_only,structural_coverage_metric,,3.0,,1,1,bounded_reporting_use,현재는 추가 fault case 수집이 불가능하므로 step1_taxonomy 는 structural coverage/reference scope로만 유지한다. current data decision 은 freeze_with_caution 이고 final usage 는 bounded_reporting_use 다. 이 판단은 operator workflow handoff 상태와 별개로 structural scope 자체의 reporting boundary 를 정한 것이다. classifier target 이나 detector performance default 로 승격하면 안 된다. step1_taxonomy 는 structural coverage/reference scope라 classifier target selection scope가 아니다. current_best_target_name 은 coverage_only 로만 표기하고 bounded current-data claim으로만 유지한다. 이 scope는 coverage/support row만 있어 ordinary classifier target을 추천하지 않는다. 구조적 coverage 해석만 caution 수준으로 유지한다.
#|step2_onset_truth,freeze_with_caution,bounded_current_data_claim,coverage_only,structural_coverage_metric,,3.0,,1,1,bounded_reporting_use,현재는 추가 fault case 수집이 불가능하므로 step2_onset_truth 는 structural coverage/reference scope로만 유지한다. current data decision 은 freeze_with_caution 이고 final usage 는 bounded_reporting_use 다. 이 판단은 operator workflow handoff 상태와 별개로 structural scope 자체의 reporting boundary 를 정한 것이다. classifier target 이나 detector performance default 로 승격하면 안 된다. step2_onset_truth 는 structural coverage/reference scope라 classifier target selection scope가 아니다. current_best_target_name 은 coverage_only 로만 표기하고 bounded current-data claim으로만 유지한다. 이 scope는 coverage/support row만 있어 ordinary classifier target을 추천하지 않는다. 구조적 coverage 해석만 caution 수준으로 유지한다.
#|step3_precursor_performance,exploratory_only,exploratory_claim_only,first_cond_evt,true_case_metric,1.0,3.0,,1,1,exploratory_only,"현재는 추가 fault case 수집이 불가능하고 benchmark reset 이후 precursor benchmark support는 3개이며 c42997a6-5881-47e7-9035-7de8a2673b54.1.1 도 여기에 포함되므로, step3 precursor scope는 positive support=3.0 기준 exploratory only 로 유지한다. 현재 best row는 first_cond_evt (f1=1.0, positive_support=3.0) 이지만 stable default 결론으로 쓰면 안 된다. old precursor support 2 wording은 obsolete 다. step3 precursor scope의 현재 최상위 target은 first_cond_evt (f1=1.0, positive_support=3.0) 이다. benchmark reset 이후 precursor benchmark support는 3건이며, c42997a6-5881-47e7-9035-7de8a2673b54.1.1 은 전조형 고장/급격 종료로 해석되면서 precursor benchmark에 포함된다. 따라서 step3 positive support는 3.0건으로 유지하고 current data에서는 exploratory 수준으로만 읽는다. precursor unique benchmark는 현재 3 fault_case 기준으로 +2면 support 5, +7이면 support 10이다. old precursor support 2 wording은 obsolete 다. 현재 scope freeze 상태는 do_not_freeze 다. precursor-bearing scope는 current artifacts만으로 부족해 새 fault_case truth와 onset corroboration 확장이 우선이다."
#|step4_abrupt_no_precursor,exploratory_only,exploratory_claim_only,final_fault_hit_by_anchor,true_case_metric,0.5714285714285715,3.0,,1,1,exploratory_only,"현재는 추가 fault case 수집이 불가능하고 benchmark reset 이후 precursor benchmark support는 3개, 순수 급작 benchmark support는 3개다. c42997a6-5881-47e7-9035-7de8a2673b54.1.1 은 전조형 고장/급격 종료로 해석되며 precursor benchmark에는 포함되고 pure abrupt benchmark에서는 제외된다. step4 pure abrupt/no-precursor scope는 positive support=3.0 기준 exploratory only 로 유지한다. 현재 best row는 final_fault_hit_by_anchor (f1=0.5714285714285715, positive_support=3.0) 이지만 pure abrupt support가 작아 stable default 결론으로 쓰면 안 된다. step4 pure abrupt/no-precursor scope의 현재 최상위 target은 final_fault_hit_by_anchor (f1=0.5714285714285715, positive_support=3.0) 이다. benchmark reset 이후 precursor benchmark support는 3건이고, 사건 해석상 급작 고장 패널은 3개다. 순수 급작 benchmark support는 3건이며, c42997a6-5881-47e7-9035-7de8a2673b54.1.1 은 precursor benchmark에 포함되고 pure abrupt benchmark에서는 제외된다. 따라서 현재 pure abrupt support는 3.0건이고 current data에서는 exploratory 수준으로만 유지해야 한다. pure abrupt unique backlog는 현재 3 panel_case 기준으로 +2면 support 5, +7이면 support 10이다. old benchmark split wording은 obsolete 다. 현재 scope freeze 상태는 do_not_freeze 다. abrupt/no-precursor scope는 panel_case anchor truth를 더 늘려 low-support 상태를 줄여야 한다."
#|step4_common_cause_routing,exploratory_only,exploratory_claim_only,breadth_marker_only,true_case_metric,1.0,4.0,,1,1,exploratory_only,"현재는 추가 fault case 수집이 불가능하고 positive support 확대도 막혀 있으므로 step4_common_cause_routing 는 exploratory only 로 유지한다. 현재 best row는 breadth_marker_only (f1=1.0, positive_support=4.0) 이지만 stable default 결론으로 쓰면 안 된다. 이 판단은 operator workflow handoff 상태와 별개로 algorithmic evaluation scope 의 freeze boundary 를 정한 것이다. step4_common_cause_routing 의 현재 최상위 target은 breadth_marker_only (f1=1.0, positive_support=4.0) 이지만, 현재 data만으로는 exploratory 수준에 머물러야 한다. step4 common-cause의 3개 routing target은 같은 site_event support를 공유하므로 target-level 합 3건을 그대로 더하면 과대계산이다. unique backlog는 현재 4 site_event 기준으로 +1면 support 5, +6이면 support 10이다. 현재 scope freeze 상태는 do_not_freeze 다. common-cause scope는 새 site_event truth와 routing evidence 확장이 필요하다."
#|operator_policy_proxy,workflow_proxy_only,workflow_claim_only,baseline_plus_discovery_narrow,retrospective_proxy_metric,0.5499999999999999,11.0,baseline_plus_discovery_cluster,1,1,workflow_only,"현재는 추가 fault case 수집이 불가능하므로 operator scope는 detector 성능 freeze가 아니라 workflow handoff 로 읽어야 한다. current data decision 은 workflow_proxy_only 이고 final usage 는 workflow_only 다. chosen operational workflow 는 baseline_plus_discovery_cluster 이며 release gate pass=1, pipeline pass=1 기준으로 사용할 수 있다. queue/watch baseline에 discovery cluster를 side-by-side로 붙인 기본 operator workflow. 선택 이유는 cluster preview가 baseline 대비 linked proxy +5를 유지하면서 total=23, extra=5, max_single_site_share=0.304로 panel view보다 operator load와 site skew를 더 잘 억제한다.. 다만 cluster view는 panel-level 세부 문맥을 압축하므로 analyst drill-down이 필요할 때는 panel preview를 함께 봐야 한다. retrospective proxy best target (baseline_plus_discovery_narrow) 과 chosen workflow 를 같은 뜻으로 쓰면 안 된다."
# pvdiag_payload_end
# endregion
# region payload: frozen_share_input
# pvdiag_payload_file {"bytes": 5683, "endswith_newline": true, "lines": 15, "path": "release/conalog_full_runtime_v1/package/_share/vendor_reply_adjudication_latest.csv", "role": "frozen_share_input", "sha256": "b61270a7536486a669592824c7d7737a73e65bd6fc7828f413bab062b5c1635c"}
#|﻿site,panel_id,vendor_reply_class,vendor_fault_family,field_confirmed_flag,adjudication_weight,vendor_note,strict_trigger_date,first_warning_date,retrospective_onset_date,days_earlier_than_trigger,onset_confidence,onset_method,reason_summary,panel_found_in_ours,dispute_type
#|conalog,7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0,vendor_pattern_positive,diode_like,0,0.7,"입력전압 27 수준, 다른 패널 43 대비 30~40% 낮음",2024-11-26,2024-11-06,2024-11-06,20,high,persistent_5of7,strict_method=critical_fault_flag|window_start=2024-09-27|first_warning=2024-11-06|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,1,agree_group_issue
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16,vendor_pattern_positive,diode_like,0,0.7,다이오드 손상으로 파악하는 경우,2025-06-08,2025-06-07,2025-06-08,0,medium,strict_trigger_fallback,strict_method=critical_fault_flag|window_start=2025-04-09|first_warning=2025-06-07|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,1,agree_group_issue
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7,vendor_pattern_positive,diode_like,0,0.7,다이오드 손상으로 파악하는 경우,2025-06-08,2025-06-08,2025-06-08,0,medium,strict_trigger_fallback,strict_method=critical_fault_flag|window_start=2025-04-09|first_warning=2025-06-08|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,1,agree_group_issue
#|ktc_ess,10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12,vendor_pattern_positive,diode_like,0,0.7,다이오드 손상으로 파악하는 경우,2025-08-16,2025-08-12,2025-08-16,0,medium,strict_trigger_fallback,strict_method=critical_fault_flag|window_start=2025-06-17|first_warning=2025-08-12|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,1,agree_group_issue
#|conalog,c42997a6-5881-47e7-9035-7de8a2673b54.1.1,vendor_likely_positive,open_or_device_issue_like,0,0.5,"전압 0, 패널이나 장비 문제로 볼 수 있는 상태, 현장확인 안됨",2025-03-21,2025-01-20,2025-01-20,60,high,persistent_5of7,strict_method=confirmed_fault_flag|window_start=2025-01-20|first_warning=2025-01-20|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,1,agree_positive
#|ktc_ess,70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4,vendor_likely_positive,module_damage_like,0,0.5,모듈 손상된 것 같으나 현장확인 안함,2025-02-02,2024-12-25,2025-01-25,8,high,persistent_5of7,strict_method=critical_fault_flag|window_start=2024-12-04|first_warning=2024-12-25|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,1,agree_positive
#|gangui,4fd0c566-e25e-4d51-96ca-57cc46940593.4.15,vendor_likely_positive,group_or_inverter_side_like,0,0.5,"여러 장비가 0, 인버터 관련 작업 추정, O&M 정보 없음",2025-11-11,2025-09-13,2025-11-11,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2025-09-12|first_warning=2025-09-13|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,1,agree_positive
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.17,field_confirmed_positive,group_or_inverter_side_like,1,1.0,"커넥터 불량으로 인버터 하나 내려감, 현장 조치 후 복구",2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,1,agree_positive
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.16,field_confirmed_positive,group_or_inverter_side_like,1,1.0,"커넥터 불량으로 인버터 하나 내려감, 현장 조치 후 복구",2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,1,agree_positive
#|conalog,d0a55fe4-4fb3-4dd3-8c11-d1144442db27.1.15,field_confirmed_positive,group_or_inverter_side_like,1,1.0,"커넥터 불량으로 인버터 하나 내려감, 현장 조치 후 복구",2024-12-06,2024-12-05,2024-12-06,0,medium,strict_trigger_fallback,strict_method=confirmed_fault_flag|window_start=2024-10-07|first_warning=2024-12-05|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,1,agree_positive
#|conalog,45dfa600-79b7-428e-95d3-22345a068986.1.1,vendor_rejected,none_visible,0,0.6,이상으로 보이는 것이 전혀 없어 왜 후보인지 모르겠다고 답변,2025-01-19,2024-11-20,2024-12-23,27,high,persistent_5of7,strict_method=critical_fault_flag|window_start=2024-11-20|first_warning=2024-11-20|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,1,ours_positive_vendor_rejected
#|conalog,d15b9e13-4117-49ae-a78f-7ace013e48de.0.0,vendor_rejected,none_visible,0,0.6,이상으로 보이는 것이 전혀 없어 왜 후보인지 모르겠다고 답변,2025-02-19,2025-01-01,2025-02-19,0,medium,strict_trigger_fallback,strict_method=critical_fault_flag|window_start=2024-12-21|first_warning=2025-01-01|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,1,ours_positive_vendor_rejected
#|conalog,45dfa600-79b7-428e-95d3-22345a068986.1.0,vendor_rejected,none_visible,0,0.6,이상으로 보이는 것이 전혀 없어 왜 후보인지 모르겠다고 답변,2024-12-29,2024-11-27,2024-12-29,0,medium,strict_trigger_fallback,strict_method=critical_fault_flag|window_start=2024-10-30|first_warning=2024-11-27|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,1,ours_positive_vendor_rejected
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.9,vendor_rejected,none_visible,0,0.6,이상으로 보이는 것이 전혀 없어 왜 후보인지 모르겠다고 답변,2025-10-27,2025-08-28,2025-08-28,60,high,persistent_5of7,strict_method=critical_fault_flag|window_start=2025-08-28|first_warning=2025-08-28|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0,1,ours_positive_vendor_rejected
# pvdiag_payload_end
# endregion
# endregion


EMBEDDED_TEXT_FILES, EMBEDDED_FILE_SHA256 = load_embedded_payload_from_source()


if __name__ == "__main__":
    raise SystemExit(main())
