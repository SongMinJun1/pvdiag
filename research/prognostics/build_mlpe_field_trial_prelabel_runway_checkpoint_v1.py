#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-150-precheck"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_prelabel_runway_checkpoint_br150_check"
DEFAULT_QUEUE = "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_128_TO_150_EXECUTION_QUEUE_V1.csv"

CHECKPOINT_OUTPUT_NAME = "mlpe_field_trial_prelabel_runway_checkpoint_v1.csv"
ISSUES_OUTPUT_NAME = "mlpe_field_trial_prelabel_runway_checkpoint_issues_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_prelabel_runway_checkpoint_summary_v1.csv"
NEXT_OUTPUT_NAME = "mlpe_field_trial_prelabel_runway_checkpoint_next_actions_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_prelabel_runway_checkpoint_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_prelabel_runway_checkpoint_v1.json"

EXPECTED_COMPLETE_COUNT = 8
EXPECTED_BLOCKED_COUNT = 15

CHECKPOINTS = [
    {
        "checkpoint_id": "queue_locked",
        "pass_condition": "BR-128..150 queue has 23 contiguous rows and no open branch",
    },
    {
        "checkpoint_id": "contract_spine_complete",
        "pass_condition": "fail-closed contract gates through BR-143 are complete",
    },
    {
        "checkpoint_id": "commit_scope_clean",
        "pass_condition": "BR-148-precheck has no risk files or issue rows",
    },
    {
        "checkpoint_id": "handoff_ready",
        "pass_condition": "BR-149-precheck blocked-state handoff ready flag is 1",
    },
    {
        "checkpoint_id": "semantic_patch_blocked",
        "pass_condition": "BR-144 remains blocked until replay, selected rule, shadow, and prepatch-ready candidate exist",
    },
    {
        "checkpoint_id": "truth_and_patch_writes_locked",
        "pass_condition": "truth, threshold, canonical, and engine patch approval sums remain 0",
    },
    {
        "checkpoint_id": "real_data_boundary_explicit",
        "pass_condition": "next semantic progress requires real KTC ESS capture/labels or replay evidence",
    },
    {
        "checkpoint_id": "algorithm_completion_not_claimed",
        "pass_condition": "prelabel checkpoint does not claim final algorithm completion or performance improvement",
    },
]

CHECKPOINT_COLUMNS = [
    "owner_branch",
    "checkpoint_id",
    "pass_condition",
    "checkpoint_passed_flag",
    "checkpoint_status",
    "observed_value",
    "next_action",
]

ISSUE_COLUMNS = [
    "owner_branch",
    "issue_type",
    "checkpoint_id",
    "observed_value",
    "expected_policy",
]

NEXT_COLUMNS = [
    "owner_branch",
    "next_action_order",
    "action_id",
    "action_type",
    "requires_real_data_flag",
    "safe_without_real_data_flag",
    "action_detail",
]


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def int_value(value: object) -> int:
    text = normalize_text(value)
    if not text:
        return 0
    return int(float(text))


def resolve(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def read_json(path: Path | None) -> dict[str, object]:
    if path is None or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_queue(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    for col in ["branch", "sequence_no", "status", "blocked_by", "operator_facing_change"]:
        if col not in df.columns:
            df[col] = ""
    out = df.copy()
    for col in out.columns:
        out[col] = out[col].map(normalize_text)
    return out


def queue_metrics(queue: pd.DataFrame) -> dict[str, int]:
    seq_ok = 0
    try:
        seq_ok = int([int_value(x) for x in queue["sequence_no"].tolist()] == list(range(1, 24)))
    except Exception:
        seq_ok = 0
    status = queue["status"].map(normalize_text)
    br144 = queue[queue["branch"].eq("BR-20260425-144")]
    br150 = queue[queue["branch"].eq("BR-20260425-150")]
    return {
        "queue_rows": int(len(queue)),
        "sequence_ok": seq_ok,
        "complete_rows": int(status.eq("complete_this_branch").sum()),
        "blocked_rows": int(status.str.startswith("blocked_").sum()),
        "open_rows": int(status.eq("open_now").sum()),
        "br144_blocked": int(not br144.empty and normalize_text(br144.iloc[0].get("status", "")).startswith("blocked_")),
        "br150_official_blocked": int(not br150.empty and normalize_text(br150.iloc[0].get("status", "")).startswith("blocked_")),
    }


def approval_sum(payloads: list[dict[str, object]], field: str) -> int:
    return sum(int_value(payload.get(field, 0)) for payload in payloads)


def pass_fail(condition: bool, status_pass: str, status_fail: str) -> tuple[int, str]:
    return (1, status_pass) if condition else (0, status_fail)


def build_checkpoint(
    queue: pd.DataFrame,
    commit_payload: dict[str, object],
    handoff_payload: dict[str, object],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    q = queue_metrics(queue)
    payloads = [commit_payload, handoff_payload]
    approvals_zero = all(
        approval_sum(payloads, field) == 0
        for field in [
            "engine_patch_allowed_sum",
            "threshold_patch_allowed_sum",
            "truth_intake_allowed_sum",
            "canonical_truth_write_allowed_sum",
        ]
    )
    checks: dict[str, tuple[bool, str, str]] = {
        "queue_locked": (
            q["queue_rows"] == 23 and q["sequence_ok"] == 1 and q["open_rows"] == 0,
            f"rows={q['queue_rows']}; sequence_ok={q['sequence_ok']}; open={q['open_rows']}",
            "Fix queue continuity/open branch state before checkpoint.",
        ),
        "contract_spine_complete": (
            q["complete_rows"] == EXPECTED_COMPLETE_COUNT and q["blocked_rows"] == EXPECTED_BLOCKED_COUNT,
            f"complete={q['complete_rows']}; blocked={q['blocked_rows']}",
            "Expected 8 complete contract/precheck rows and 15 blocked downstream rows.",
        ),
        "commit_scope_clean": (
            int_value(commit_payload.get("commit_scope_ready_flag", 0)) == 1
            and int_value(commit_payload.get("risk_files", 1)) == 0
            and int_value(commit_payload.get("issue_rows", 1)) == 0,
            f"ready={commit_payload.get('commit_scope_ready_flag', '')}; risk={commit_payload.get('risk_files', '')}; issues={commit_payload.get('issue_rows', '')}",
            "Refresh BR-148-precheck until commit scope is clean.",
        ),
        "handoff_ready": (
            int_value(handoff_payload.get("blocked_state_handoff_ready_flag", 0)) == 1
            and int_value(handoff_payload.get("issue_rows", 1)) == 0,
            f"ready={handoff_payload.get('blocked_state_handoff_ready_flag', '')}; issues={handoff_payload.get('issue_rows', '')}",
            "Refresh BR-149-precheck until handoff is ready.",
        ),
        "semantic_patch_blocked": (
            q["br144_blocked"] == 1,
            f"br144_blocked={q['br144_blocked']}",
            "Do not open BR-144 without replay, selected rule, shadow, and prepatch-ready candidate.",
        ),
        "truth_and_patch_writes_locked": (
            approvals_zero,
            "approval_sums=0",
            "All write/patch approval sums must remain 0.",
        ),
        "real_data_boundary_explicit": (
            int_value(handoff_payload.get("real_data_required_to_continue_flag", 0)) == 1,
            f"real_data_required={handoff_payload.get('real_data_required_to_continue_flag', '')}",
            "Record that semantic progress requires real data/replay evidence.",
        ),
        "algorithm_completion_not_claimed": (
            q["br150_official_blocked"] == 1,
            f"br150_official_blocked={q['br150_official_blocked']}",
            "Official BR-150 must remain blocked; this is only a prelabel checkpoint.",
        ),
    }

    rows: list[dict[str, object]] = []
    issues: list[dict[str, object]] = []
    for item in CHECKPOINTS:
        cid = str(item["checkpoint_id"])
        passed, observed, fix_action = checks[cid]
        pass_flag, status = pass_fail(passed, "checkpoint_passed", "checkpoint_blocked")
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "checkpoint_id": cid,
                "pass_condition": item["pass_condition"],
                "checkpoint_passed_flag": pass_flag,
                "checkpoint_status": status,
                "observed_value": observed,
                "next_action": "Keep as prelabel checkpoint evidence only." if passed else fix_action,
            }
        )
        if not passed:
            issues.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "issue_type": status,
                    "checkpoint_id": cid,
                    "observed_value": observed,
                    "expected_policy": item["pass_condition"],
                }
            )
    return pd.DataFrame(rows).reindex(columns=CHECKPOINT_COLUMNS), pd.DataFrame(issues).reindex(columns=ISSUE_COLUMNS)


def build_next_actions() -> pd.DataFrame:
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "next_action_order": 1,
            "action_id": "commit_scope_stage_if_requested",
            "action_type": "repo_bookkeeping",
            "requires_real_data_flag": 0,
            "safe_without_real_data_flag": 1,
            "action_detail": "If requested, stage only the BR-148-precheck include-candidate manifest; do not use git add .",
        },
        {
            "owner_branch": OWNER_BRANCH,
            "next_action_order": 2,
            "action_id": "real_capture_intake",
            "action_type": "field_trial_data",
            "requires_real_data_flag": 1,
            "safe_without_real_data_flag": 0,
            "action_detail": "When KTC ESS capture/labels arrive, resume BR-130 real capture intake.",
        },
        {
            "owner_branch": OWNER_BRANCH,
            "next_action_order": 3,
            "action_id": "semantic_patch_path",
            "action_type": "algorithm_semantics",
            "requires_real_data_flag": 1,
            "safe_without_real_data_flag": 0,
            "action_detail": "Run replay, selected-rule, and shadow gates before any BR-144 panel-engine patch.",
        },
    ]
    return pd.DataFrame(rows).reindex(columns=NEXT_COLUMNS)


def build_summary(checkpoint: pd.DataFrame, issues: pd.DataFrame) -> pd.DataFrame:
    passed = int(checkpoint["checkpoint_passed_flag"].map(int_value).sum()) if len(checkpoint) else 0
    total = int(len(checkpoint))
    ready = int(total == len(CHECKPOINTS) and passed == total and len(issues) == 0)
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "summary_key": "all",
            "checkpoint_rows": total,
            "checkpoint_passed_rows": passed,
            "checkpoint_blocked_rows": int(total - passed),
            "issue_rows": int(len(issues)),
            "prelabel_runway_checkpoint_ready_flag": ready,
            "algorithm_complete_claim_allowed_flag": 0,
            "performance_improvement_claim_allowed_flag": 0,
            "real_data_required_to_continue_flag": 1,
            "safe_to_stage_commit_scope_if_requested_flag": ready,
            "engine_patch_allowed_sum": 0,
            "threshold_patch_allowed_sum": 0,
            "truth_intake_allowed_sum": 0,
            "canonical_truth_write_allowed_sum": 0,
        }
    ]
    for _, row in checkpoint.iterrows():
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "summary_scope": "checkpoint_id",
                "summary_key": row["checkpoint_id"],
                "checkpoint_rows": 1,
                "checkpoint_passed_rows": int_value(row["checkpoint_passed_flag"]),
                "checkpoint_blocked_rows": int(1 - int_value(row["checkpoint_passed_flag"])),
                "issue_rows": int(len(issues[issues["checkpoint_id"].eq(row["checkpoint_id"])])),
                "prelabel_runway_checkpoint_ready_flag": 0,
                "algorithm_complete_claim_allowed_flag": 0,
                "performance_improvement_claim_allowed_flag": 0,
                "real_data_required_to_continue_flag": 1,
                "safe_to_stage_commit_scope_if_requested_flag": 0,
                "engine_patch_allowed_sum": 0,
                "threshold_patch_allowed_sum": 0,
                "truth_intake_allowed_sum": 0,
                "canonical_truth_write_allowed_sum": 0,
            }
        )
    return pd.DataFrame(rows)


def write_note(output_dir: Path, summary: pd.DataFrame) -> None:
    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    text = "\n".join(
        [
            "# BR-20260425-150 precheck prelabel runway checkpoint",
            "",
            f"- checkpoint rows: `{overall['checkpoint_rows']}`",
            f"- checkpoint passed rows: `{overall['checkpoint_passed_rows']}`",
            f"- checkpoint blocked rows: `{overall['checkpoint_blocked_rows']}`",
            f"- issue rows: `{overall['issue_rows']}`",
            f"- prelabel runway checkpoint ready flag: `{overall['prelabel_runway_checkpoint_ready_flag']}`",
            f"- algorithm complete claim allowed flag: `{overall['algorithm_complete_claim_allowed_flag']}`",
            f"- performance improvement claim allowed flag: `{overall['performance_improvement_claim_allowed_flag']}`",
            f"- real data required to continue flag: `{overall['real_data_required_to_continue_flag']}`",
            "",
            "This is a prelabel checkpoint only.",
            "It does not claim algorithm completion, performance improvement, truth intake, threshold approval, or engine patch authorization.",
            "",
        ]
    )
    (output_dir / NOTE_OUTPUT_NAME).write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a prelabel runway checkpoint for the blocked MLPE field-trial runway.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--queue-input", type=Path, default=Path(DEFAULT_QUEUE))
    parser.add_argument("--commit-scope-json", type=Path, required=True)
    parser.add_argument("--handoff-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    queue_path = resolve(repo_root, args.queue_input)
    commit_path = resolve(repo_root, args.commit_scope_json)
    handoff_path = resolve(repo_root, args.handoff_json)
    output_dir = args.output_dir if args.output_dir.is_absolute() else repo_root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    queue = read_queue(queue_path)
    commit_payload = read_json(commit_path)
    handoff_payload = read_json(handoff_path)
    checkpoint, issues = build_checkpoint(queue, commit_payload, handoff_payload)
    summary = build_summary(checkpoint, issues)
    next_actions = build_next_actions()

    checkpoint.to_csv(output_dir / CHECKPOINT_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    issues.to_csv(output_dir / ISSUES_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    next_actions.to_csv(output_dir / NEXT_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(output_dir, summary)

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "checkpoint_rows": int(overall["checkpoint_rows"]),
        "checkpoint_passed_rows": int(overall["checkpoint_passed_rows"]),
        "checkpoint_blocked_rows": int(overall["checkpoint_blocked_rows"]),
        "issue_rows": int(overall["issue_rows"]),
        "prelabel_runway_checkpoint_ready_flag": int(overall["prelabel_runway_checkpoint_ready_flag"]),
        "algorithm_complete_claim_allowed_flag": int(overall["algorithm_complete_claim_allowed_flag"]),
        "performance_improvement_claim_allowed_flag": int(overall["performance_improvement_claim_allowed_flag"]),
        "real_data_required_to_continue_flag": int(overall["real_data_required_to_continue_flag"]),
        "safe_to_stage_commit_scope_if_requested_flag": int(overall["safe_to_stage_commit_scope_if_requested_flag"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "canonical_truth_write_allowed_sum": int(overall["canonical_truth_write_allowed_sum"]),
        "outputs": {
            "checkpoint": str(output_dir / CHECKPOINT_OUTPUT_NAME),
            "issues": str(output_dir / ISSUES_OUTPUT_NAME),
            "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
            "next_actions": str(output_dir / NEXT_OUTPUT_NAME),
            "note": str(output_dir / NOTE_OUTPUT_NAME),
            "json": str(output_dir / JSON_OUTPUT_NAME),
        },
    }
    (output_dir / JSON_OUTPUT_NAME).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
