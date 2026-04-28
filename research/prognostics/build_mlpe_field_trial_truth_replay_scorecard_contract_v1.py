#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-139"
DEFAULT_SIDECAR_PACKAGE = "/private/tmp/mlpe_field_trial_sidecar_truth_package_contract_br137_check/mlpe_field_trial_sidecar_truth_package_dry_run_v1.csv"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_truth_replay_scorecard_contract_br139_check"

CONTRACT_OUTPUT_NAME = "mlpe_field_trial_truth_replay_scorecard_contract_v1.csv"
DRY_RUN_OUTPUT_NAME = "mlpe_field_trial_truth_replay_scorecard_dry_run_v1.csv"
METRICS_OUTPUT_NAME = "mlpe_field_trial_truth_replay_scorecard_metrics_v1.csv"
ISSUES_OUTPUT_NAME = "mlpe_field_trial_truth_replay_scorecard_contract_issues_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_truth_replay_scorecard_contract_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_truth_replay_scorecard_contract_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_truth_replay_scorecard_contract_v1.json"

APPROVAL_FIELDS = [
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
]

SIDECAR_PACKAGE_COLUMNS = [
    "trial_event_id",
    "site",
    "root_id",
    "panel_id",
    "event_date",
    "package_group",
    "required_flag",
    "package_group_blocking_flag",
    "sidecar_truth_package_status",
    "sidecar_truth_package_id",
    "sidecar_truth_label",
    "sidecar_fault_family",
    "sidecar_event_type",
    "sidecar_onset_date",
    "sidecar_fault_date",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
]

REPLAY_RESULT_COLUMNS = [
    "trial_event_id",
    "site",
    "root_id",
    "panel_id",
    "detected_flag",
    "alert_date",
    "predicted_fault_family",
    "confidence_score",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
]

CONTRACT_GROUPS = [
    {
        "scorecard_group": "sidecar_truth_ready",
        "required_flag": 1,
        "metric_family": "input_gate",
        "metric_definition": "BR-137 sidecar truth package event has no blocking required package groups.",
        "pass_condition": "sidecar package ready event exists and has no write flags",
        "blocked_status": "blocked_sidecar_truth_absent",
        "claim_boundary": "no replay metric without sidecar truth",
    },
    {
        "scorecard_group": "baseline_result_attached",
        "required_flag": 1,
        "metric_family": "input_gate",
        "metric_definition": "Baseline replay row is attached by trial_event_id.",
        "pass_condition": "baseline result row exists, has no write flags, and contains detection columns",
        "blocked_status": "blocked_baseline_result_missing",
        "claim_boundary": "no before/after comparison without baseline",
    },
    {
        "scorecard_group": "candidate_result_attached",
        "required_flag": 1,
        "metric_family": "input_gate",
        "metric_definition": "Candidate replay row is attached by trial_event_id.",
        "pass_condition": "candidate result row exists, has no write flags, and contains detection columns",
        "blocked_status": "blocked_candidate_result_missing",
        "claim_boundary": "no candidate claim without replay output",
    },
    {
        "scorecard_group": "event_identity_join",
        "required_flag": 1,
        "metric_family": "traceability",
        "metric_definition": "site/root/panel/date identity is stable across truth, baseline, and candidate rows.",
        "pass_condition": "trial_event_id joins and identity fields do not conflict",
        "blocked_status": "blocked_identity_join_not_ready",
        "claim_boundary": "no metric if event identity cannot be traced",
    },
    {
        "scorecard_group": "site_family_support",
        "required_flag": 1,
        "metric_family": "support",
        "metric_definition": "scorecard records support counts by site and fault family.",
        "pass_condition": "site and sidecar_fault_family are non-empty",
        "blocked_status": "blocked_site_family_support_missing",
        "claim_boundary": "no site/family claim without support counts",
    },
    {
        "scorecard_group": "precision_recall_f1_axis",
        "required_flag": 1,
        "metric_family": "classification",
        "metric_definition": "precision, recall, and F1 are computed only with positive and negative support counts.",
        "pass_condition": "positive/negative truth labels and detection flags are available",
        "blocked_status": "blocked_precision_recall_axis_not_computable",
        "claim_boundary": "metrics are descriptive until support gates pass",
    },
    {
        "scorecard_group": "lead_time_axis",
        "required_flag": 1,
        "metric_family": "timing",
        "metric_definition": "lead_days = sidecar_fault_date - alert_date for detected positive events.",
        "pass_condition": "positive detected rows have parseable alert_date and sidecar_fault_date",
        "blocked_status": "blocked_lead_time_axis_not_computable",
        "claim_boundary": "no early-warning claim without lead-time distribution",
    },
    {
        "scorecard_group": "false_alarm_axis",
        "required_flag": 1,
        "metric_family": "operator_load",
        "metric_definition": "false alarms are detected negative-control rows.",
        "pass_condition": "negative-control truth labels are present",
        "blocked_status": "blocked_false_alarm_axis_not_computable",
        "claim_boundary": "no operator-load claim without negative controls",
    },
    {
        "scorecard_group": "confidence_axis",
        "required_flag": 1,
        "metric_family": "confidence",
        "metric_definition": "confidence is recorded for detected baseline/candidate rows.",
        "pass_condition": "confidence_score is parseable when detected_flag=1",
        "blocked_status": "blocked_confidence_axis_not_computable",
        "claim_boundary": "no confidence threshold claim without confidence distribution",
    },
    {
        "scorecard_group": "unsupported_claim_guard",
        "required_flag": 1,
        "metric_family": "claim_guard",
        "metric_definition": "performance improvement claim remains blocked in the contract stage.",
        "pass_condition": "performance_improvement_claim_allowed stays 0",
        "blocked_status": "blocked_unsupported_claim_guard_failed",
        "claim_boundary": "BR-139 defines scorecard metrics but does not approve performance claims",
    },
]

CONTRACT_COLUMNS = [
    "owner_branch",
    "scorecard_group",
    "required_flag",
    "metric_family",
    "metric_definition",
    "pass_condition",
    "blocked_status",
    "claim_boundary",
]

DRY_RUN_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "site",
    "root_id",
    "panel_id",
    "event_date",
    "scorecard_group",
    "required_flag",
    "sidecar_truth_ready_flag",
    "baseline_result_attached_flag",
    "candidate_result_attached_flag",
    "scorecard_group_passed_flag",
    "scorecard_group_blocking_flag",
    "truth_replay_scorecard_status",
    "sidecar_truth_package_id",
    "sidecar_truth_label",
    "truth_positive_flag",
    "sidecar_fault_family",
    "sidecar_event_type",
    "sidecar_onset_date",
    "sidecar_fault_date",
    "baseline_detected_flag",
    "candidate_detected_flag",
    "baseline_alert_date",
    "candidate_alert_date",
    "baseline_predicted_fault_family",
    "candidate_predicted_fault_family",
    "baseline_confidence_score",
    "candidate_confidence_score",
    "baseline_lead_days",
    "candidate_lead_days",
    "performance_improvement_claim_allowed",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
    "scorecard_next_action",
]

METRIC_COLUMNS = [
    "owner_branch",
    "model",
    "metric_scope",
    "scope_key",
    "support_total",
    "positive_support",
    "negative_support",
    "detected_count",
    "true_positive",
    "false_positive",
    "false_negative",
    "true_negative",
    "precision",
    "recall",
    "f1",
    "mean_lead_days",
    "false_alarm_count",
    "mean_confidence",
    "performance_improvement_claim_allowed",
]

ISSUE_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "issue_type",
    "field",
    "observed_value",
    "expected_policy",
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


def float_value(value: object) -> float | None:
    text = normalize_text(value)
    if not text:
        return None
    return float(text)


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def read_csv(path: Path, required_columns: list[str]) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing input: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    for col in required_columns:
        if col not in df.columns:
            df[col] = ""
    out = df.copy()
    for col in out.columns:
        out[col] = out[col].map(normalize_text)
    return out


def approval_violation(row: pd.Series) -> bool:
    return any(int_value(row.get(field, "0")) != 0 for field in APPROVAL_FIELDS)


def build_contract() -> pd.DataFrame:
    rows = [{"owner_branch": OWNER_BRANCH, **group} for group in CONTRACT_GROUPS]
    return pd.DataFrame(rows).reindex(columns=CONTRACT_COLUMNS)


def add_issue(issues: list[dict[str, object]], event_id: str, issue_type: str, field: str, observed: str, expected: str) -> None:
    issues.append(
        {
            "owner_branch": OWNER_BRANCH,
            "trial_event_id": event_id,
            "issue_type": issue_type,
            "field": field,
            "observed_value": observed,
            "expected_policy": expected,
        }
    )


def build_missing_input_rows() -> tuple[pd.DataFrame, pd.DataFrame]:
    dry_run = pd.DataFrame(
        [
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": "",
                "scorecard_group": "contract_input",
                "required_flag": 1,
                "scorecard_group_blocking_flag": 1,
                "truth_replay_scorecard_status": "blocked_missing_sidecar_truth_package",
                "performance_improvement_claim_allowed": 0,
                "scorecard_next_action": "Run BR-138 sidecar truth package first; do not compute replay metrics.",
            }
        ]
    ).reindex(columns=DRY_RUN_COLUMNS, fill_value="")
    issues = pd.DataFrame(
        [
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": "",
                "issue_type": "missing_sidecar_truth_package",
                "field": "sidecar_truth_package",
                "observed_value": "",
                "expected_policy": "BR-138/BR-137 sidecar truth package rows before replay scorecard",
            }
        ]
    ).reindex(columns=ISSUE_COLUMNS)
    return dry_run, issues


def ready_truth_events(sidecar: pd.DataFrame) -> pd.DataFrame:
    rows: list[pd.Series] = []
    for event_id, sub in sidecar[sidecar["trial_event_id"].map(normalize_text).ne("")].groupby("trial_event_id"):
        required = sub[sub["required_flag"].map(int_value).eq(1)]
        ready = len(required) > 0 and int(required["package_group_blocking_flag"].map(int_value).sum()) == 0
        no_write = not any(approval_violation(row) for _, row in sub.iterrows())
        if ready and no_write:
            rows.append(sub.iloc[0])
    if not rows:
        return pd.DataFrame(columns=SIDECAR_PACKAGE_COLUMNS)
    return pd.DataFrame(rows).reset_index(drop=True)


def rows_by_event(df: pd.DataFrame | None) -> dict[str, pd.Series]:
    if df is None or df.empty or "trial_event_id" not in df.columns:
        return {}
    out: dict[str, pd.Series] = {}
    for _, row in df.iterrows():
        event_id = normalize_text(row.get("trial_event_id", ""))
        if event_id and event_id not in out:
            out[event_id] = row
    return out


def parse_date(value: object) -> datetime | None:
    text = normalize_text(value)
    if not text:
        return None
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d")
    except ValueError:
        return None


def truth_positive(row: pd.Series) -> int:
    label = normalize_text(row.get("sidecar_truth_label", "")).lower()
    negative_labels = {"confirmed_no_fault", "negative_control_clean", "no_fault", "normal"}
    return int(label not in negative_labels and label != "")


def lead_days(truth_row: pd.Series, result_row: pd.Series | None) -> int | str:
    if result_row is None or int_value(result_row.get("detected_flag", "0")) != 1:
        return ""
    fault_date = parse_date(truth_row.get("sidecar_fault_date", ""))
    alert_date = parse_date(result_row.get("alert_date", ""))
    if fault_date is None or alert_date is None:
        return ""
    return (fault_date - alert_date).days


def confidence_ok(result_row: pd.Series | None) -> bool:
    if result_row is None:
        return False
    if int_value(result_row.get("detected_flag", "0")) != 1:
        return True
    return float_value(result_row.get("confidence_score", "")) is not None


def identity_join_ok(truth_row: pd.Series, baseline_row: pd.Series | None, candidate_row: pd.Series | None) -> bool:
    for row in [baseline_row, candidate_row]:
        if row is None:
            return False
        for field in ["site", "root_id", "panel_id"]:
            source = normalize_text(truth_row.get(field, ""))
            observed = normalize_text(row.get(field, ""))
            if source and observed and source != observed:
                return False
    return True


def result_ok(row: pd.Series | None) -> bool:
    return row is not None and not approval_violation(row) and normalize_text(row.get("detected_flag", "")) != ""


def group_status(
    group_name: str,
    truth_row: pd.Series,
    baseline_row: pd.Series | None,
    candidate_row: pd.Series | None,
) -> tuple[str, int, int]:
    sidecar_ready = True
    baseline_ok = result_ok(baseline_row)
    candidate_ok = result_ok(candidate_row)
    positive = truth_positive(truth_row)

    if group_name == "sidecar_truth_ready":
        passed = sidecar_ready
    elif group_name == "baseline_result_attached":
        passed = baseline_ok
    elif group_name == "candidate_result_attached":
        passed = candidate_ok
    elif group_name == "event_identity_join":
        passed = identity_join_ok(truth_row, baseline_row, candidate_row)
    elif group_name == "site_family_support":
        passed = bool(normalize_text(truth_row.get("site", "")) and normalize_text(truth_row.get("sidecar_fault_family", "")))
    elif group_name == "precision_recall_f1_axis":
        passed = baseline_ok and candidate_ok and normalize_text(truth_row.get("sidecar_truth_label", "")) != ""
    elif group_name == "lead_time_axis":
        if positive:
            passed = (int_value(baseline_row.get("detected_flag", "0")) != 1 or lead_days(truth_row, baseline_row) != "") and (
                int_value(candidate_row.get("detected_flag", "0")) != 1 or lead_days(truth_row, candidate_row) != ""
            ) if baseline_row is not None and candidate_row is not None else False
        else:
            passed = True
    elif group_name == "false_alarm_axis":
        passed = normalize_text(truth_row.get("sidecar_truth_label", "")) != ""
    elif group_name == "confidence_axis":
        passed = confidence_ok(baseline_row) and confidence_ok(candidate_row)
    elif group_name == "unsupported_claim_guard":
        passed = True
    else:
        passed = False

    if passed:
        return "truth_replay_scorecard_group_passed", 1, 0
    for group in CONTRACT_GROUPS:
        if group["scorecard_group"] == group_name:
            return str(group["blocked_status"]), 0, 1
    return "blocked_unknown_scorecard_group", 0, 1


def next_action(status: str) -> str:
    if status == "truth_replay_scorecard_group_passed":
        return "Use as replay scorecard evidence only; no performance claim is approved here."
    if status == "blocked_baseline_result_missing":
        return "Attach baseline replay result before comparison."
    if status == "blocked_candidate_result_missing":
        return "Attach candidate replay result before comparison."
    if status == "blocked_sidecar_truth_absent":
        return "Run BR-138 sidecar truth package first."
    return "Resolve replay scorecard blocker before threshold/rule selection."


def build_dry_run(
    sidecar: pd.DataFrame,
    baseline: pd.DataFrame | None,
    candidate: pd.DataFrame | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    truth = ready_truth_events(sidecar)
    baseline_by_event = rows_by_event(baseline)
    candidate_by_event = rows_by_event(candidate)
    rows: list[dict[str, object]] = []
    issues: list[dict[str, object]] = []

    for _, truth_row in truth.iterrows():
        event_id = normalize_text(truth_row.get("trial_event_id", ""))
        baseline_row = baseline_by_event.get(event_id)
        candidate_row = candidate_by_event.get(event_id)
        if baseline_row is None:
            add_issue(issues, event_id, "missing_baseline_replay_result", "trial_event_id", event_id, "one baseline replay row")
        elif approval_violation(baseline_row):
            add_issue(issues, event_id, "baseline_write_flag_violation", "approval_fields", "nonzero", "baseline replay write flags remain 0")
        if candidate_row is None:
            add_issue(issues, event_id, "missing_candidate_replay_result", "trial_event_id", event_id, "one candidate replay row")
        elif approval_violation(candidate_row):
            add_issue(issues, event_id, "candidate_write_flag_violation", "approval_fields", "nonzero", "candidate replay write flags remain 0")

        for group in CONTRACT_GROUPS:
            group_name = str(group["scorecard_group"])
            status, passed, blocking = group_status(group_name, truth_row, baseline_row, candidate_row)
            if blocking:
                add_issue(issues, event_id, status, group_name, "not passed", str(group["pass_condition"]))
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "trial_event_id": event_id,
                    "site": normalize_text(truth_row.get("site", "")),
                    "root_id": normalize_text(truth_row.get("root_id", "")),
                    "panel_id": normalize_text(truth_row.get("panel_id", "")),
                    "event_date": normalize_text(truth_row.get("event_date", "")),
                    "scorecard_group": group_name,
                    "required_flag": int(group["required_flag"]),
                    "sidecar_truth_ready_flag": 1,
                    "baseline_result_attached_flag": int(baseline_row is not None),
                    "candidate_result_attached_flag": int(candidate_row is not None),
                    "scorecard_group_passed_flag": passed,
                    "scorecard_group_blocking_flag": blocking,
                    "truth_replay_scorecard_status": status,
                    "sidecar_truth_package_id": normalize_text(truth_row.get("sidecar_truth_package_id", "")),
                    "sidecar_truth_label": normalize_text(truth_row.get("sidecar_truth_label", "")),
                    "truth_positive_flag": truth_positive(truth_row),
                    "sidecar_fault_family": normalize_text(truth_row.get("sidecar_fault_family", "")),
                    "sidecar_event_type": normalize_text(truth_row.get("sidecar_event_type", "")),
                    "sidecar_onset_date": normalize_text(truth_row.get("sidecar_onset_date", "")),
                    "sidecar_fault_date": normalize_text(truth_row.get("sidecar_fault_date", "")),
                    "baseline_detected_flag": int_value(baseline_row.get("detected_flag", "0")) if baseline_row is not None else "",
                    "candidate_detected_flag": int_value(candidate_row.get("detected_flag", "0")) if candidate_row is not None else "",
                    "baseline_alert_date": normalize_text(baseline_row.get("alert_date", "")) if baseline_row is not None else "",
                    "candidate_alert_date": normalize_text(candidate_row.get("alert_date", "")) if candidate_row is not None else "",
                    "baseline_predicted_fault_family": normalize_text(baseline_row.get("predicted_fault_family", "")) if baseline_row is not None else "",
                    "candidate_predicted_fault_family": normalize_text(candidate_row.get("predicted_fault_family", "")) if candidate_row is not None else "",
                    "baseline_confidence_score": normalize_text(baseline_row.get("confidence_score", "")) if baseline_row is not None else "",
                    "candidate_confidence_score": normalize_text(candidate_row.get("confidence_score", "")) if candidate_row is not None else "",
                    "baseline_lead_days": lead_days(truth_row, baseline_row),
                    "candidate_lead_days": lead_days(truth_row, candidate_row),
                    "performance_improvement_claim_allowed": 0,
                    "canonical_truth_write_allowed": 0,
                    "truth_intake_allowed": 0,
                    "threshold_patch_allowed": 0,
                    "engine_patch_allowed": 0,
                    "scorecard_next_action": next_action(status),
                }
            )

    return pd.DataFrame(rows).reindex(columns=DRY_RUN_COLUMNS), pd.DataFrame(issues).reindex(columns=ISSUE_COLUMNS)


def safe_div(num: int | float, den: int | float) -> float | str:
    if den == 0:
        return ""
    return float(num) / float(den)


def model_metric_rows(dry_run: pd.DataFrame, model: str, scope: str, key: str, sub: pd.DataFrame) -> dict[str, object]:
    event_rows = sub.drop_duplicates("trial_event_id")
    detected_col = f"{model}_detected_flag"
    family_col = f"{model}_predicted_fault_family"
    confidence_col = f"{model}_confidence_score"
    lead_col = f"{model}_lead_days"
    tp = fp = fn = tn = detected = 0
    lead_values: list[float] = []
    confidence_values: list[float] = []

    for _, row in event_rows.iterrows():
        positive = int_value(row.get("truth_positive_flag", "0")) == 1
        detected_flag = int_value(row.get(detected_col, "0")) == 1
        family_match = normalize_text(row.get(family_col, "")) == normalize_text(row.get("sidecar_fault_family", ""))
        if detected_flag:
            detected += 1
            conf = float_value(row.get(confidence_col, ""))
            if conf is not None:
                confidence_values.append(conf)
        if positive and detected_flag and family_match:
            tp += 1
            lead = float_value(row.get(lead_col, ""))
            if lead is not None:
                lead_values.append(lead)
        elif positive:
            fn += 1
        elif detected_flag:
            fp += 1
        else:
            tn += 1

    positive_support = tp + fn
    negative_support = fp + tn
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, positive_support)
    f1 = ""
    if isinstance(precision, float) and isinstance(recall, float) and (precision + recall) > 0:
        f1 = (2.0 * precision * recall) / (precision + recall)
    return {
        "owner_branch": OWNER_BRANCH,
        "model": model,
        "metric_scope": scope,
        "scope_key": key,
        "support_total": int(len(event_rows)),
        "positive_support": positive_support,
        "negative_support": negative_support,
        "detected_count": detected,
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "mean_lead_days": sum(lead_values) / len(lead_values) if lead_values else "",
        "false_alarm_count": fp,
        "mean_confidence": sum(confidence_values) / len(confidence_values) if confidence_values else "",
        "performance_improvement_claim_allowed": 0,
    }


def build_metrics(dry_run: pd.DataFrame) -> pd.DataFrame:
    if dry_run.empty:
        return pd.DataFrame(columns=METRIC_COLUMNS)
    passed_events = []
    for event_id, sub in dry_run[dry_run["trial_event_id"].map(normalize_text).ne("")].groupby("trial_event_id"):
        required = sub[sub["required_flag"].map(int_value).eq(1)]
        if len(required) and int(required["scorecard_group_blocking_flag"].map(int_value).sum()) == 0:
            passed_events.append(event_id)
    if not passed_events:
        return pd.DataFrame(columns=METRIC_COLUMNS)
    event_df = dry_run[dry_run["trial_event_id"].isin(passed_events)].drop_duplicates("trial_event_id")
    rows: list[dict[str, object]] = []
    for model in ["baseline", "candidate"]:
        rows.append(model_metric_rows(event_df, model, "overall", "all", event_df))
        for site, sub in event_df.groupby("site", dropna=False):
            rows.append(model_metric_rows(event_df, model, "site", normalize_text(site), sub))
        for family, sub in event_df.groupby("sidecar_fault_family", dropna=False):
            rows.append(model_metric_rows(event_df, model, "fault_family", normalize_text(family), sub))
    return pd.DataFrame(rows).reindex(columns=METRIC_COLUMNS)


def ready_event_count(dry_run: pd.DataFrame) -> int:
    ready = 0
    for _, sub in dry_run[dry_run["trial_event_id"].map(normalize_text).ne("")].groupby("trial_event_id"):
        required = sub[sub["required_flag"].map(int_value).eq(1)]
        if len(required) and int(required["scorecard_group_blocking_flag"].map(int_value).sum()) == 0:
            ready += 1
    return ready


def build_summary(dry_run: pd.DataFrame, metrics: pd.DataFrame, issues: pd.DataFrame, contract: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "summary_key": "all",
            "contract_rows": int(len(contract)),
            "events": int(dry_run["trial_event_id"].map(normalize_text).replace("", pd.NA).dropna().nunique()) if len(dry_run) else 0,
            "truth_replay_scorecard_ready_events": ready_event_count(dry_run),
            "scorecard_rows": int(len(dry_run)),
            "scorecard_passed_rows": int(dry_run["scorecard_group_passed_flag"].map(int_value).sum()) if len(dry_run) else 0,
            "scorecard_blocked_rows": int(dry_run["scorecard_group_blocking_flag"].map(int_value).sum()) if len(dry_run) else 0,
            "metric_rows": int(len(metrics)),
            "issue_rows": int(len(issues)),
            "performance_improvement_claim_allowed_sum": int(dry_run["performance_improvement_claim_allowed"].map(int_value).sum()) if len(dry_run) else 0,
            "canonical_truth_write_allowed_sum": int(dry_run["canonical_truth_write_allowed"].map(int_value).sum()) if len(dry_run) else 0,
            "truth_intake_allowed_sum": int(dry_run["truth_intake_allowed"].map(int_value).sum()) if len(dry_run) else 0,
            "threshold_patch_allowed_sum": int(dry_run["threshold_patch_allowed"].map(int_value).sum()) if len(dry_run) else 0,
            "engine_patch_allowed_sum": int(dry_run["engine_patch_allowed"].map(int_value).sum()) if len(dry_run) else 0,
        }
    ]
    if len(dry_run):
        for status, sub in dry_run.groupby("truth_replay_scorecard_status", dropna=False):
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "summary_scope": "truth_replay_scorecard_status",
                    "summary_key": status,
                    "contract_rows": int(len(contract)),
                    "events": int(sub["trial_event_id"].map(normalize_text).replace("", pd.NA).dropna().nunique()),
                    "truth_replay_scorecard_ready_events": 0,
                    "scorecard_rows": int(len(sub)),
                    "scorecard_passed_rows": int(sub["scorecard_group_passed_flag"].map(int_value).sum()),
                    "scorecard_blocked_rows": int(sub["scorecard_group_blocking_flag"].map(int_value).sum()),
                    "metric_rows": int(len(metrics)),
                    "issue_rows": int(len(issues)),
                    "performance_improvement_claim_allowed_sum": 0,
                    "canonical_truth_write_allowed_sum": 0,
                    "truth_intake_allowed_sum": 0,
                    "threshold_patch_allowed_sum": 0,
                    "engine_patch_allowed_sum": 0,
                }
            )
    return pd.DataFrame(rows)


def write_note(output_dir: Path, summary: pd.DataFrame) -> None:
    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    text = "\n".join(
        [
            "# BR-20260425-139 truth replay scorecard contract",
            "",
            f"- contract rows: `{overall['contract_rows']}`",
            f"- events: `{overall['events']}`",
            f"- truth-replay-scorecard-ready events: `{overall['truth_replay_scorecard_ready_events']}`",
            f"- scorecard rows: `{overall['scorecard_rows']}`",
            f"- scorecard passed rows: `{overall['scorecard_passed_rows']}`",
            f"- scorecard blocked rows: `{overall['scorecard_blocked_rows']}`",
            f"- metric rows: `{overall['metric_rows']}`",
            f"- issue rows: `{overall['issue_rows']}`",
            f"- performance improvement claim allowed sum: `{overall['performance_improvement_claim_allowed_sum']}`",
            f"- canonical truth write allowed sum: `{overall['canonical_truth_write_allowed_sum']}`",
            f"- truth intake allowed sum: `{overall['truth_intake_allowed_sum']}`",
            f"- threshold patch allowed sum: `{overall['threshold_patch_allowed_sum']}`",
            f"- engine patch allowed sum: `{overall['engine_patch_allowed_sum']}`",
            "",
            "This contract defines replay scorecard metrics and remains claim-closed.",
            "It does not approve performance improvement, threshold replay, canonical truth writes, or panel-engine changes.",
            "",
        ]
    )
    (output_dir / NOTE_OUTPUT_NAME).write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the BR-139 truth replay scorecard contract and fail-closed dry run.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--sidecar-package", type=Path, default=Path(DEFAULT_SIDECAR_PACKAGE))
    parser.add_argument("--baseline-replay-input", type=Path, default=None)
    parser.add_argument("--candidate-replay-input", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    sidecar_path = resolve_path(repo_root, args.sidecar_package)
    baseline_path = resolve_path(repo_root, args.baseline_replay_input) if args.baseline_replay_input else None
    candidate_path = resolve_path(repo_root, args.candidate_replay_input) if args.candidate_replay_input else None
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    contract = build_contract()
    if not sidecar_path.exists():
        dry_run, issues = build_missing_input_rows()
    else:
        sidecar = read_csv(sidecar_path, SIDECAR_PACKAGE_COLUMNS)
        baseline = read_csv(baseline_path, REPLAY_RESULT_COLUMNS) if baseline_path and baseline_path.exists() else None
        candidate = read_csv(candidate_path, REPLAY_RESULT_COLUMNS) if candidate_path and candidate_path.exists() else None
        dry_run, issues = build_dry_run(sidecar, baseline, candidate)

    metrics = build_metrics(dry_run)
    summary = build_summary(dry_run, metrics, issues, contract)

    contract.to_csv(output_dir / CONTRACT_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    dry_run.to_csv(output_dir / DRY_RUN_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    metrics.to_csv(output_dir / METRICS_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    issues.to_csv(output_dir / ISSUES_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(output_dir, summary)

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "contract_rows": int(overall["contract_rows"]),
        "events": int(overall["events"]),
        "truth_replay_scorecard_ready_events": int(overall["truth_replay_scorecard_ready_events"]),
        "scorecard_rows": int(overall["scorecard_rows"]),
        "scorecard_passed_rows": int(overall["scorecard_passed_rows"]),
        "scorecard_blocked_rows": int(overall["scorecard_blocked_rows"]),
        "metric_rows": int(overall["metric_rows"]),
        "issue_rows": int(overall["issue_rows"]),
        "performance_improvement_claim_allowed_sum": int(overall["performance_improvement_claim_allowed_sum"]),
        "canonical_truth_write_allowed_sum": int(overall["canonical_truth_write_allowed_sum"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "outputs": {
            "contract": str(output_dir / CONTRACT_OUTPUT_NAME),
            "dry_run": str(output_dir / DRY_RUN_OUTPUT_NAME),
            "metrics": str(output_dir / METRICS_OUTPUT_NAME),
            "issues": str(output_dir / ISSUES_OUTPUT_NAME),
            "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
            "note": str(output_dir / NOTE_OUTPUT_NAME),
            "json": str(output_dir / JSON_OUTPUT_NAME),
        },
    }
    (output_dir / JSON_OUTPUT_NAME).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
