#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


DETAIL_OUTPUT_NAME = "panel_day_engine_episode_truth_manifest_resolution_closure_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_episode_truth_manifest_resolution_closure_summary_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_episode_truth_manifest_resolution_closure_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_episode_truth_manifest_resolution_closure_v1.json"

ACTIVE_REGISTER = "docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md"
BR170_CONTRACT = "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_170_EPISODE_TRUTH_INPUT_MANIFEST_CONTRACT_V1.md"

EXPECTED_CONSUMERS = [
    {
        "branch": "BR-20260429-171",
        "consumer": "build_panel_day_engine_episode_truth_adjudication_worksheet_v1.py",
        "smoke": "smoke_test_panel_day_engine_episode_truth_adjudication_worksheet_v1.py",
        "doc": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_171_EPISODE_TRUTH_WORKSHEET_MANIFEST_RESOLUTION_V1.md",
        "flags": ["--trace-input", "--index-input"],
        "keys": ["trace_input", "index_input"],
    },
    {
        "branch": "BR-20260429-172",
        "consumer": "build_panel_day_engine_episode_truth_conservative_adjudication_v1.py",
        "smoke": "smoke_test_panel_day_engine_episode_truth_conservative_adjudication_v1.py",
        "doc": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_172_EPISODE_TRUTH_CONSERVATIVE_MANIFEST_RESOLUTION_V1.md",
        "flags": ["--worksheet-input"],
        "keys": ["worksheet_input"],
    },
    {
        "branch": "BR-20260429-173",
        "consumer": "build_panel_day_engine_episode_truth_durable_shape_review_v1.py",
        "smoke": "smoke_test_panel_day_engine_episode_truth_durable_shape_review_v1.py",
        "doc": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_173_EPISODE_TRUTH_DURABLE_SHAPE_MANIFEST_RESOLUTION_V1.md",
        "flags": ["--br088-input"],
        "keys": ["br088_input"],
    },
    {
        "branch": "BR-20260429-174",
        "consumer": "build_panel_day_engine_episode_truth_evidence_attachment_v1.py",
        "smoke": "smoke_test_panel_day_engine_episode_truth_evidence_attachment_v1.py",
        "doc": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_174_EPISODE_TRUTH_EVIDENCE_ATTACHMENT_MANIFEST_RESOLUTION_V1.md",
        "flags": ["--reviewed-rows-input"],
        "keys": ["reviewed_rows_input"],
    },
    {
        "branch": "BR-20260429-175",
        "consumer": "build_panel_day_engine_episode_truth_map_v1.py",
        "smoke": "smoke_test_panel_day_engine_episode_truth_map_v1.py",
        "doc": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_175_EPISODE_TRUTH_MAP_MANIFEST_RESOLUTION_V1.md",
        "flags": ["--shape-input", "--backlog-input"],
        "keys": ["shape_input", "backlog_input"],
    },
    {
        "branch": "BR-20260429-176",
        "consumer": "build_panel_day_engine_episode_truth_review_packet_v1.py",
        "smoke": "smoke_test_panel_day_engine_episode_truth_review_packet_v1.py",
        "doc": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_176_EPISODE_TRUTH_REVIEW_PACKET_MANIFEST_RESOLUTION_V1.md",
        "flags": ["--episode-map-input"],
        "keys": ["episode_map_input"],
    },
    {
        "branch": "BR-20260429-177",
        "consumer": "build_panel_day_engine_episode_truth_source_trace_audit_v1.py",
        "smoke": "smoke_test_panel_day_engine_episode_truth_source_trace_audit_v1.py",
        "doc": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_177_EPISODE_TRUTH_SOURCE_TRACE_MANIFEST_RESOLUTION_V1.md",
        "flags": ["--index-input", "--template-input"],
        "keys": ["index_input", "template_input"],
    },
    {
        "branch": "BR-20260429-178",
        "consumer": "build_panel_day_engine_reviewed_episode_truth_rows_v1.py",
        "smoke": "smoke_test_panel_day_engine_reviewed_episode_truth_rows_v1.py",
        "doc": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_178_REVIEWED_EPISODE_TRUTH_ROWS_MANIFEST_RESOLUTION_V1.md",
        "flags": ["--packet-input", "--guard-json-input"],
        "keys": ["packet_input", "guard_json_input"],
    },
]

DETAIL_COLUMNS = [
    "owner_branch",
    "branch",
    "consumer",
    "required_flags",
    "manifest_keys",
    "consumer_exists",
    "smoke_exists",
    "doc_exists",
    "active_register_mentions_branch",
    "br170_contract_mentions_consumer",
    "has_input_manifest_arg",
    "has_manifest_helpers",
    "all_required_flags_present",
    "all_manifest_keys_present",
    "records_resolution_sources",
    "smoke_covers_manifest_path",
    "smoke_covers_explicit_override",
    "smoke_covers_fail_closed",
    "doc_records_non_semantic_boundary",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "closure_status",
    "missing_checks",
]

SUMMARY_COLUMNS = [
    "owner_branch",
    "expected_consumer_count",
    "expected_manifest_key_count",
    "closure_pass_count",
    "closure_fail_count",
    "unresolved_manifest_consumer_count",
    "missing_check_count",
    "operator_facing_change_allowed_sum",
    "engine_patch_allowed_sum",
    "threshold_patch_allowed_sum",
    "closure_complete",
]


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def bool_int(value: bool) -> int:
    return 1 if value else 0


def build_detail(repo_root: Path, owner_branch: str) -> pd.DataFrame:
    active_register_text = read_text(resolve_path(repo_root, ACTIVE_REGISTER))
    br170_contract_text = read_text(resolve_path(repo_root, BR170_CONTRACT))
    rows: list[dict[str, object]] = []

    for spec in EXPECTED_CONSUMERS:
        consumer_path = repo_root / "research/prognostics" / spec["consumer"]
        smoke_path = repo_root / "research/prognostics" / spec["smoke"]
        doc_path = resolve_path(repo_root, spec["doc"])
        consumer_text = read_text(consumer_path)
        smoke_text = read_text(smoke_path)
        doc_text = read_text(doc_path)

        checks = {
            "consumer_exists": consumer_path.exists(),
            "smoke_exists": smoke_path.exists(),
            "doc_exists": doc_path.exists(),
            "active_register_mentions_branch": spec["branch"] in active_register_text,
            "br170_contract_mentions_consumer": spec["consumer"] in br170_contract_text,
            "has_input_manifest_arg": "--input-manifest" in consumer_text,
            "has_manifest_helpers": all(
                token in consumer_text
                for token in ["load_input_manifest", "manifest_path_value", "resolve_chain_input"]
            ),
            "all_required_flags_present": all(flag in consumer_text for flag in spec["flags"]),
            "all_manifest_keys_present": all(key in consumer_text for key in spec["keys"]),
            "records_resolution_sources": all(
                token in consumer_text for token in ["explicit_cli", "input_manifest", "legacy_default"]
            ),
            "smoke_covers_manifest_path": "input_manifest" in smoke_text and "--input-manifest" in smoke_text,
            "smoke_covers_explicit_override": "explicit_cli" in smoke_text,
            "smoke_covers_fail_closed": "missing `" in smoke_text,
            "doc_records_boundary": "Do not edit `pv_ae/panel_day_engine.py`" in doc_text,
        }
        missing = [name for name, passed in checks.items() if not passed]
        closure_status = "closed" if not missing else "needs_followup"
        rows.append(
            {
                "owner_branch": owner_branch,
                "branch": spec["branch"],
                "consumer": spec["consumer"],
                "required_flags": "; ".join(spec["flags"]),
                "manifest_keys": "; ".join(spec["keys"]),
                "consumer_exists": bool_int(checks["consumer_exists"]),
                "smoke_exists": bool_int(checks["smoke_exists"]),
                "doc_exists": bool_int(checks["doc_exists"]),
                "active_register_mentions_branch": bool_int(checks["active_register_mentions_branch"]),
                "br170_contract_mentions_consumer": bool_int(checks["br170_contract_mentions_consumer"]),
                "has_input_manifest_arg": bool_int(checks["has_input_manifest_arg"]),
                "has_manifest_helpers": bool_int(checks["has_manifest_helpers"]),
                "all_required_flags_present": bool_int(checks["all_required_flags_present"]),
                "all_manifest_keys_present": bool_int(checks["all_manifest_keys_present"]),
                "records_resolution_sources": bool_int(checks["records_resolution_sources"]),
                "smoke_covers_manifest_path": bool_int(checks["smoke_covers_manifest_path"]),
                "smoke_covers_explicit_override": bool_int(checks["smoke_covers_explicit_override"]),
                "smoke_covers_fail_closed": bool_int(checks["smoke_covers_fail_closed"]),
                "doc_records_non_semantic_boundary": bool_int(checks["doc_records_boundary"]),
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
                "closure_status": closure_status,
                "missing_checks": "; ".join(missing),
            }
        )
    return pd.DataFrame(rows, columns=DETAIL_COLUMNS)


def build_summary(owner_branch: str, detail_df: pd.DataFrame) -> pd.DataFrame:
    missing_check_count = int(detail_df["missing_checks"].map(lambda value: 0 if str(value) == "" else len(str(value).split("; "))).sum())
    row = {
        "owner_branch": owner_branch,
        "expected_consumer_count": int(len(detail_df)),
        "expected_manifest_key_count": int(detail_df["manifest_keys"].map(lambda value: len(str(value).split("; "))).sum()),
        "closure_pass_count": int(detail_df["closure_status"].eq("closed").sum()),
        "closure_fail_count": int(detail_df["closure_status"].ne("closed").sum()),
        "unresolved_manifest_consumer_count": int(detail_df["closure_status"].ne("closed").sum()),
        "missing_check_count": missing_check_count,
        "operator_facing_change_allowed_sum": int(detail_df["operator_facing_change_allowed"].sum()),
        "engine_patch_allowed_sum": int(detail_df["engine_patch_allowed"].sum()),
        "threshold_patch_allowed_sum": int(detail_df["threshold_patch_allowed"].sum()),
        "closure_complete": int(detail_df["closure_status"].eq("closed").all()),
    }
    return pd.DataFrame([row], columns=SUMMARY_COLUMNS)


def write_note(output_dir: Path, owner_branch: str, detail_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    summary = summary_df.iloc[0].to_dict()
    note = f"""# Panel Day Engine Episode Truth Manifest Resolution Closure V1

## Purpose
- Close the BR-170 episode-truth manifest-resolution lane with a reproducible static audit.
- Verify that every BR-170 manifest-required consumer has `--input-manifest`, explicit CLI precedence, source recording, smoke coverage, and docs/register coverage.
- Keep this closure audit non-semantic: no runtime, threshold, truth-label, or operator-facing behavior change.

## Outputs
- `{output_dir / DETAIL_OUTPUT_NAME}`
- `{output_dir / SUMMARY_OUTPUT_NAME}`
- `{output_dir / JSON_OUTPUT_NAME}`

## Result
- owner_branch: `{owner_branch}`
- expected consumers: `{summary["expected_consumer_count"]}`
- manifest-required inputs: `{summary["expected_manifest_key_count"]}`
- closed consumers: `{summary["closure_pass_count"]}`
- failed consumers: `{summary["closure_fail_count"]}`
- unresolved manifest consumers: `{summary["unresolved_manifest_consumer_count"]}`
- missing checks: `{summary["missing_check_count"]}`
- operator-facing change allowed sum: `{summary["operator_facing_change_allowed_sum"]}`
- engine patch allowed sum: `{summary["engine_patch_allowed_sum"]}`
- threshold patch allowed sum: `{summary["threshold_patch_allowed_sum"]}`
- closure complete: `{summary["closure_complete"]}`

## Reading
- `closure_complete=1` means the BR-170 manifest-required consumer list is covered by static code/docs/smoke checks.
- This does not regenerate upstream episode truth artifacts and does not approve production semantics.
- Future episode-truth consumers should add a row to this audit before relying on `/private/tmp` defaults.

## Repro Command
```bash
python3 research/prognostics/build_panel_day_engine_episode_truth_manifest_resolution_closure_v1.py --repo-root "$(pwd)" --output-dir /private/tmp/panel_day_engine_episode_truth_manifest_resolution_closure_br179_check
```
"""
    (output_dir / NOTE_OUTPUT_NAME).write_text(note, encoding="utf-8")


def build_outputs(repo_root: Path, output_dir: Path, owner_branch: str) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    detail_df = build_detail(repo_root, owner_branch)
    summary_df = build_summary(owner_branch, detail_df)

    detail_df.to_csv(output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(output_dir, owner_branch, detail_df, summary_df)

    summary = summary_df.iloc[0].to_dict()
    payload = {
        "owner_branch": owner_branch,
        "repo_root": str(repo_root),
        "output_dir": str(output_dir),
        "expected_consumer_count": int(summary["expected_consumer_count"]),
        "expected_manifest_key_count": int(summary["expected_manifest_key_count"]),
        "closure_pass_count": int(summary["closure_pass_count"]),
        "closure_fail_count": int(summary["closure_fail_count"]),
        "unresolved_manifest_consumer_count": int(summary["unresolved_manifest_consumer_count"]),
        "missing_check_count": int(summary["missing_check_count"]),
        "operator_facing_change_allowed_sum": int(summary["operator_facing_change_allowed_sum"]),
        "engine_patch_allowed_sum": int(summary["engine_patch_allowed_sum"]),
        "threshold_patch_allowed_sum": int(summary["threshold_patch_allowed_sum"]),
        "closure_complete": int(summary["closure_complete"]),
        "recommended_next_branch": (
            "br170_manifest_resolution_complete_proceed_to_next_cleanup_lane"
            if int(summary["closure_complete"]) == 1
            else "resolve_failed_manifest_consumers_before_next_lane"
        ),
        "failed_consumers": detail_df.loc[
            detail_df["closure_status"].ne("closed"), ["branch", "consumer", "missing_checks"]
        ].to_dict(orient="records"),
        "outputs": {
            "detail": str(output_dir / DETAIL_OUTPUT_NAME),
            "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
            "note": str(output_dir / NOTE_OUTPUT_NAME),
        },
    }
    (output_dir / JSON_OUTPUT_NAME).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/private/tmp/panel_day_engine_episode_truth_manifest_resolution_closure_br179_check"),
    )
    parser.add_argument("--owner-branch", default="BR-20260429-179")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    payload = build_outputs(repo_root, args.output_dir, args.owner_branch)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
