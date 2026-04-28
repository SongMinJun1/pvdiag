#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


ATTACHMENT_INPUT_NAME = "panel_day_engine_voltage_preserved_independent_confirmation_attachment_v1.csv"

QUEUE_OUTPUT_NAME = "panel_day_engine_voltage_preserved_truth_acquisition_queue_v1.csv"
PANEL_SUMMARY_OUTPUT_NAME = "panel_day_engine_voltage_preserved_truth_acquisition_panel_summary_v1.csv"
SITE_SUMMARY_OUTPUT_NAME = "panel_day_engine_voltage_preserved_truth_acquisition_site_summary_v1.csv"
COLLECTOR_TEMPLATE_OUTPUT_NAME = "panel_day_engine_voltage_preserved_truth_acquisition_collector_template_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_voltage_preserved_truth_acquisition_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_voltage_preserved_truth_acquisition_queue_v1.json"

DEFAULT_ATTACHMENT_DIR = "/private/tmp/panel_day_engine_voltage_preserved_independent_confirmation_br098_check"
DEFAULT_OUTPUT_DIR = "/private/tmp/panel_day_engine_voltage_preserved_truth_acquisition_queue_br099_check"

ATTACHMENT_REQUIRED_COLUMNS = [
    "attachment_row_id",
    "gap_review_row_id",
    "evidence_request_id",
    "site",
    "root_id",
    "panel_group_key",
    "panel_id",
    "request_priority",
    "review_bucket",
    "raw_source_trace_attached",
    "exact_vendor_rows",
    "exact_vendor_positive_or_likely_rows",
    "exact_vendor_rejected_rows",
    "exact_vendor_field_confirmed_rows",
    "same_site_reference_field_confirmed_rows",
    "manual_site_context_rows",
    "manual_site_exact_usable_rows",
    "exact_independent_evidence_rows",
    "independent_confirmation_attached",
    "common_cause_data_clearance_candidate",
    "measurement_artifact_data_clearance_candidate",
    "counterexample_clearance_required",
    "explicit_common_cause_clearance_attached",
    "explicit_measurement_artifact_clearance_attached",
    "explicit_counterexample_clearance_attached",
    "all_required_clearances_attached",
    "truth_intake_ready",
    "positive_truth_candidate_approved",
    "threshold_tuning_approved",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

QUEUE_COLUMNS = [
    "owner_branch",
    "queue_row_id",
    "attachment_row_id",
    "gap_review_row_id",
    "evidence_request_id",
    "site",
    "root_id",
    "panel_group_key",
    "panel_id",
    "review_bucket",
    "acquisition_axis",
    "axis_priority",
    "axis_required_for_truth_intake",
    "current_axis_status",
    "already_satisfied_flag",
    "truth_intake_blocker_flag",
    "evidence_to_collect",
    "accepted_evidence_examples",
    "suggested_collection_source",
    "acceptance_criteria",
    "why_needed",
    "same_site_reference_only_flag",
    "vendor_support_context_flag",
    "counterexample_sensitive_flag",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

PANEL_SUMMARY_COLUMNS = [
    "owner_branch",
    "attachment_row_id",
    "site",
    "panel_id",
    "review_bucket",
    "queue_rows",
    "open_required_axes",
    "independent_confirmation_missing",
    "explicit_clearance_missing",
    "counterexample_clearance_required",
    "same_site_reference_only_flag",
    "vendor_support_context_flag",
    "truth_intake_ready",
    "next_collection_focus",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

SITE_SUMMARY_COLUMNS = [
    "owner_branch",
    "summary_scope",
    "summary_key",
    "panel_rows",
    "queue_rows",
    "open_required_axes",
    "independent_confirmation_open_rows",
    "explicit_clearance_open_rows",
    "counterexample_clearance_open_rows",
    "same_site_reference_only_rows",
    "vendor_support_context_rows",
    "truth_intake_ready_rows",
    "operator_facing_change_allowed_sum",
    "engine_patch_allowed_sum",
    "threshold_patch_allowed_sum",
    "notes",
]

COLLECTOR_TEMPLATE_COLUMNS = [
    "owner_branch",
    "queue_row_id",
    "site",
    "panel_id",
    "acquisition_axis",
    "axis_priority",
    "evidence_to_collect",
    "accepted_evidence_examples",
    "suggested_collection_source",
    "acceptance_criteria",
    "collector_status",
    "collector_evidence_date",
    "collector_evidence_path",
    "collector_note",
    "reviewer",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def numeric_float(value: object) -> float:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0.0 if pd.isna(numeric) else float(numeric)


def numeric_int(value: object) -> int:
    return int(round(numeric_float(value)))


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def read_required_csv(path: Path, required_cols: list[str], name: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing required input {name}: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"{name} missing columns: {missing}")
    return df


def normalize_attachment(df: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = {
        "raw_source_trace_attached",
        "exact_vendor_rows",
        "exact_vendor_positive_or_likely_rows",
        "exact_vendor_rejected_rows",
        "exact_vendor_field_confirmed_rows",
        "same_site_reference_field_confirmed_rows",
        "manual_site_context_rows",
        "manual_site_exact_usable_rows",
        "exact_independent_evidence_rows",
        "independent_confirmation_attached",
        "common_cause_data_clearance_candidate",
        "measurement_artifact_data_clearance_candidate",
        "counterexample_clearance_required",
        "explicit_common_cause_clearance_attached",
        "explicit_measurement_artifact_clearance_attached",
        "explicit_counterexample_clearance_attached",
        "all_required_clearances_attached",
        "truth_intake_ready",
        "positive_truth_candidate_approved",
        "threshold_tuning_approved",
        "operator_facing_change_allowed",
        "engine_patch_allowed",
        "threshold_patch_allowed",
    }
    out = df.copy()
    for col in set(ATTACHMENT_REQUIRED_COLUMNS) - numeric_cols:
        out[col] = out[col].map(normalize_text)
    for col in numeric_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    return out.sort_values(["site", "root_id", "panel_group_key", "panel_id"]).reset_index(drop=True)


def assert_safe_start(attachment_df: pd.DataFrame) -> None:
    for col in [
        "truth_intake_ready",
        "positive_truth_candidate_approved",
        "threshold_tuning_approved",
        "operator_facing_change_allowed",
        "engine_patch_allowed",
        "threshold_patch_allowed",
    ]:
        total = int(pd.to_numeric(attachment_df[col], errors="coerce").fillna(0).sum())
        if total != 0:
            raise ValueError(f"BR-099 must start before truth/engine authorization; {col} sum is {total}")


def independent_priority(row: dict[str, object]) -> str:
    if numeric_int(row["exact_vendor_positive_or_likely_rows"]) > 0:
        return "P0_exact_vendor_supported_physical_confirmation"
    if numeric_int(row["exact_vendor_rejected_rows"]) > 0:
        return "P2_vendor_rejection_overturn_only"
    return "P1_raw_supported_independent_confirmation"


def clearance_priority(axis: str, row: dict[str, object]) -> str:
    if axis == "counterexample_clearance":
        return "P0_counterexample_clearance"
    if normalize_text(row["review_bucket"]) == "blocker_clearance_hold":
        return "P0_blocker_hold_clearance"
    if numeric_int(row["exact_vendor_positive_or_likely_rows"]) > 0:
        return "P1_vendor_supported_clearance"
    return "P2_standard_explicit_clearance"


def independent_collection_source(row: dict[str, object]) -> str:
    if numeric_int(row["exact_vendor_positive_or_likely_rows"]) > 0:
        return "field/O&M/vendor: exact panel IV curve, voltage-current measurement, maintenance, inspection, or repair record"
    if numeric_int(row["exact_vendor_rejected_rows"]) > 0:
        return "field/O&M only if the team intends to overturn vendor rejection or none-visible response"
    return "field/O&M/site operator: exact panel physical or maintenance evidence"


def clearance_collection_source(axis: str, row: dict[str, object]) -> str:
    if axis == "common_cause_clearance":
        return "site operation log, inverter/string work order, group outage log, weather/curtailment context"
    if axis == "measurement_artifact_clearance":
        return "sensor/reference/calibration log, logger status, missing-data audit, raw measurement integrity note"
    return "same-root negative-overlap review, counterexample adjudication note, reviewer sign-off"


def add_queue_row(
    rows: list[dict[str, object]],
    owner_branch: str,
    row_idx: int,
    row: dict[str, object],
    axis: str,
    priority: str,
    satisfied: int,
    evidence_to_collect: str,
    examples: str,
    source: str,
    criteria: str,
    why_needed: str,
) -> None:
    rows.append(
        {
            "owner_branch": owner_branch,
            "queue_row_id": f"BR099-VPTA-{row_idx:03d}",
            "attachment_row_id": normalize_text(row["attachment_row_id"]),
            "gap_review_row_id": normalize_text(row["gap_review_row_id"]),
            "evidence_request_id": normalize_text(row["evidence_request_id"]),
            "site": normalize_text(row["site"]),
            "root_id": normalize_text(row["root_id"]),
            "panel_group_key": normalize_text(row["panel_group_key"]),
            "panel_id": normalize_text(row["panel_id"]),
            "review_bucket": normalize_text(row["review_bucket"]),
            "acquisition_axis": axis,
            "axis_priority": priority,
            "axis_required_for_truth_intake": 1,
            "current_axis_status": "satisfied" if satisfied else "missing",
            "already_satisfied_flag": satisfied,
            "truth_intake_blocker_flag": int(not satisfied),
            "evidence_to_collect": evidence_to_collect,
            "accepted_evidence_examples": examples,
            "suggested_collection_source": source,
            "acceptance_criteria": criteria,
            "why_needed": why_needed,
            "same_site_reference_only_flag": int(
                numeric_int(row["same_site_reference_field_confirmed_rows"]) > 0
                and numeric_int(row["exact_vendor_field_confirmed_rows"]) == 0
            ),
            "vendor_support_context_flag": int(numeric_int(row["exact_vendor_positive_or_likely_rows"]) > 0),
            "counterexample_sensitive_flag": numeric_int(row["counterexample_clearance_required"]),
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Acquisition queue only; collected evidence must be re-attached by BR-098 before truth intake.",
        }
    )


def build_queue(owner_branch: str, attachment_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    row_idx = 1
    for row in attachment_df.to_dict(orient="records"):
        independent_satisfied = numeric_int(row["independent_confirmation_attached"])
        add_queue_row(
            rows,
            owner_branch,
            row_idx,
            row,
            "independent_panel_confirmation",
            independent_priority(row),
            independent_satisfied,
            "exact-panel physical/electrical/inspection/maintenance/repair evidence",
            "IV curve; string/inverter trace; direct voltage-current measurement; maintenance ticket; inspection photo/report; repair record",
            independent_collection_source(row),
            "must match the exact panel_id or include an explicit mapping from field asset ID to panel_id; same-site examples are reference-only",
            "BR-098 shows raw/vendor support is not enough to create confirmed-positive truth.",
        )
        row_idx += 1
        for axis, satisfied, evidence_to_collect, examples, why in [
            (
                "common_cause_clearance",
                numeric_int(row["explicit_common_cause_clearance_attached"]),
                "explicit common-cause clearance",
                "site event log; inverter/string outage log; group-off review; weather/curtailment note",
                "panel-local truth must not absorb site/root/group common-cause motion.",
            ),
            (
                "measurement_artifact_clearance",
                numeric_int(row["explicit_measurement_artifact_clearance_attached"]),
                "explicit measurement-artifact clearance",
                "sensor/reference check; logger status; raw data integrity note; calibration/maintenance note",
                "measurement artifacts must be cleared before raw voltage shape can support truth intake.",
            ),
        ]:
            add_queue_row(
                rows,
                owner_branch,
                row_idx,
                row,
                axis,
                clearance_priority(axis, row),
                satisfied,
                evidence_to_collect,
                examples,
                clearance_collection_source(axis, row),
                "explicit reviewer/evidence clearance must be attached; data-derived no-blocker candidates are not enough",
                why,
            )
            row_idx += 1
        if numeric_int(row["counterexample_clearance_required"]) > 0:
            add_queue_row(
                rows,
                owner_branch,
                row_idx,
                row,
                "counterexample_clearance",
                clearance_priority("counterexample_clearance", row),
                numeric_int(row["explicit_counterexample_clearance_attached"]),
                "explicit same-root counterexample clearance",
                "negative-overlap adjudication; reviewer note; same-root panel comparison; exclusion rationale",
                clearance_collection_source("counterexample_clearance", row),
                "same-root negative-overlap must be explicitly cleared before this target can enter truth intake",
                "counterexample-guarded rows can otherwise turn known negatives into false positives.",
            )
            row_idx += 1
    return pd.DataFrame(rows).reindex(columns=QUEUE_COLUMNS)


def next_collection_focus(group: pd.DataFrame) -> str:
    open_axes = set(group.loc[group["truth_intake_blocker_flag"].eq(1), "acquisition_axis"].map(normalize_text))
    if "counterexample_clearance" in open_axes:
        return "counterexample clearance plus exact-panel physical evidence"
    if "independent_panel_confirmation" in open_axes:
        return "exact-panel physical/maintenance confirmation"
    if open_axes:
        return "explicit blocker clearance"
    return "ready for separate truth-intake review"


def build_panel_summary(owner_branch: str, queue_df: pd.DataFrame, attachment_df: pd.DataFrame) -> pd.DataFrame:
    attachment_lookup = {normalize_text(row["attachment_row_id"]): row for row in attachment_df.to_dict(orient="records")}
    rows: list[dict[str, object]] = []
    for attachment_id, group in queue_df.groupby("attachment_row_id", sort=False):
        source = attachment_lookup[normalize_text(attachment_id)]
        open_required = int(group["truth_intake_blocker_flag"].sum())
        rows.append(
            {
                "owner_branch": owner_branch,
                "attachment_row_id": normalize_text(attachment_id),
                "site": normalize_text(source["site"]),
                "panel_id": normalize_text(source["panel_id"]),
                "review_bucket": normalize_text(source["review_bucket"]),
                "queue_rows": int(len(group)),
                "open_required_axes": open_required,
                "independent_confirmation_missing": int(
                    group.loc[group["acquisition_axis"].eq("independent_panel_confirmation"), "truth_intake_blocker_flag"].sum()
                ),
                "explicit_clearance_missing": int(
                    group.loc[
                        group["acquisition_axis"].isin(["common_cause_clearance", "measurement_artifact_clearance"]),
                        "truth_intake_blocker_flag",
                    ].sum()
                ),
                "counterexample_clearance_required": numeric_int(source["counterexample_clearance_required"]),
                "same_site_reference_only_flag": int(
                    numeric_int(source["same_site_reference_field_confirmed_rows"]) > 0
                    and numeric_int(source["exact_vendor_field_confirmed_rows"]) == 0
                ),
                "vendor_support_context_flag": int(numeric_int(source["exact_vendor_positive_or_likely_rows"]) > 0),
                "truth_intake_ready": int(open_required == 0),
                "next_collection_focus": next_collection_focus(group),
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
                "notes": "Panel summary is for acquisition planning only, not truth approval.",
            }
        )
    return pd.DataFrame(rows).reindex(columns=PANEL_SUMMARY_COLUMNS)


def summarize(owner_branch: str, scope: str, key: str, panel_df: pd.DataFrame, queue_df: pd.DataFrame) -> dict[str, object]:
    if panel_df.empty:
        return {col: 0 for col in SITE_SUMMARY_COLUMNS} | {
            "owner_branch": owner_branch,
            "summary_scope": scope,
            "summary_key": key,
            "notes": "empty",
        }
    attachment_ids = set(panel_df["attachment_row_id"].map(normalize_text))
    sub_queue = queue_df.loc[queue_df["attachment_row_id"].map(normalize_text).isin(attachment_ids)]
    return {
        "owner_branch": owner_branch,
        "summary_scope": scope,
        "summary_key": key,
        "panel_rows": int(len(panel_df)),
        "queue_rows": int(len(sub_queue)),
        "open_required_axes": int(panel_df["open_required_axes"].sum()),
        "independent_confirmation_open_rows": int(panel_df["independent_confirmation_missing"].sum()),
        "explicit_clearance_open_rows": int(panel_df["explicit_clearance_missing"].sum()),
        "counterexample_clearance_open_rows": int(
            sub_queue.loc[sub_queue["acquisition_axis"].eq("counterexample_clearance"), "truth_intake_blocker_flag"].sum()
        ),
        "same_site_reference_only_rows": int(panel_df["same_site_reference_only_flag"].sum()),
        "vendor_support_context_rows": int(panel_df["vendor_support_context_flag"].sum()),
        "truth_intake_ready_rows": int(panel_df["truth_intake_ready"].sum()),
        "operator_facing_change_allowed_sum": int(panel_df["operator_facing_change_allowed"].sum()),
        "engine_patch_allowed_sum": int(panel_df["engine_patch_allowed"].sum()),
        "threshold_patch_allowed_sum": int(panel_df["threshold_patch_allowed"].sum()),
        "notes": "all counts are acquisition-planning counts; truth approval remains separate",
    }


def build_site_summary(owner_branch: str, panel_df: pd.DataFrame, queue_df: pd.DataFrame) -> pd.DataFrame:
    rows = [summarize(owner_branch, "overall", "all", panel_df, queue_df)]
    for site, group in panel_df.groupby("site", sort=True):
        rows.append(summarize(owner_branch, "site", normalize_text(site), group, queue_df))
    for bucket, group in panel_df.groupby("review_bucket", sort=True):
        rows.append(summarize(owner_branch, "review_bucket", normalize_text(bucket), group, queue_df))
    return pd.DataFrame(rows).reindex(columns=SITE_SUMMARY_COLUMNS)


def build_collector_template(owner_branch: str, queue_df: pd.DataFrame) -> pd.DataFrame:
    open_queue = queue_df.loc[queue_df["truth_intake_blocker_flag"].eq(1)].copy()
    rows: list[dict[str, object]] = []
    for row in open_queue.to_dict(orient="records"):
        rows.append(
            {
                "owner_branch": owner_branch,
                "queue_row_id": normalize_text(row["queue_row_id"]),
                "site": normalize_text(row["site"]),
                "panel_id": normalize_text(row["panel_id"]),
                "acquisition_axis": normalize_text(row["acquisition_axis"]),
                "axis_priority": normalize_text(row["axis_priority"]),
                "evidence_to_collect": normalize_text(row["evidence_to_collect"]),
                "accepted_evidence_examples": normalize_text(row["accepted_evidence_examples"]),
                "suggested_collection_source": normalize_text(row["suggested_collection_source"]),
                "acceptance_criteria": normalize_text(row["acceptance_criteria"]),
                "collector_status": "",
                "collector_evidence_date": "",
                "collector_evidence_path": "",
                "collector_note": "",
                "reviewer": "",
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
            }
        )
    return pd.DataFrame(rows).reindex(columns=COLLECTOR_TEMPLATE_COLUMNS)


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_empty_"
    lines = [
        "| " + " | ".join(str(col) for col in df.columns) + " |",
        "| " + " | ".join(["---"] * len(df.columns)) + " |",
    ]
    for row in df.to_dict(orient="records"):
        values = [normalize_text(row.get(col)) for col in df.columns]
        lines.append("| " + " | ".join(value.replace("|", "\\|") for value in values) + " |")
    return "\n".join(lines)


def write_note(path: Path, owner_branch: str, attachment_input: Path, queue_df: pd.DataFrame, site_summary_df: pd.DataFrame) -> None:
    summary_cols = [
        "summary_scope",
        "summary_key",
        "panel_rows",
        "queue_rows",
        "open_required_axes",
        "independent_confirmation_open_rows",
        "explicit_clearance_open_rows",
        "counterexample_clearance_open_rows",
        "same_site_reference_only_rows",
        "vendor_support_context_rows",
        "truth_intake_ready_rows",
        "engine_patch_allowed_sum",
    ]
    lines = [
        "# panel_day_engine_voltage_preserved_truth_acquisition_queue_v1",
        "",
        "## Purpose",
        "- Convert BR-098 missing evidence axes into a collector-facing acquisition queue.",
        "- Keep evidence acquisition separate from truth labels, threshold replay, and engine changes.",
        "- Make same-site references and vendor support useful for prioritization without treating them as confirmation.",
        "",
        "## Inputs",
        f"- BR-098 attachment: `{attachment_input}`",
        "",
        "## Real Result",
        f"- owner_branch: `{owner_branch}`",
        f"- queue rows: `{len(queue_df)}`",
        f"- open required axes: `{int(queue_df['truth_intake_blocker_flag'].sum()) if not queue_df.empty else 0}`",
        f"- independent confirmation queue rows: `{int(queue_df['acquisition_axis'].eq('independent_panel_confirmation').sum()) if not queue_df.empty else 0}`",
        f"- common-cause clearance queue rows: `{int(queue_df['acquisition_axis'].eq('common_cause_clearance').sum()) if not queue_df.empty else 0}`",
        f"- measurement-artifact clearance queue rows: `{int(queue_df['acquisition_axis'].eq('measurement_artifact_clearance').sum()) if not queue_df.empty else 0}`",
        f"- counterexample clearance queue rows: `{int(queue_df['acquisition_axis'].eq('counterexample_clearance').sum()) if not queue_df.empty else 0}`",
        f"- truth intake ready rows: `{int(site_summary_df.loc[site_summary_df['summary_scope'].eq('overall'), 'truth_intake_ready_rows'].iloc[0]) if not site_summary_df.empty else 0}`",
        f"- engine patch allowed sum: `{int(queue_df['engine_patch_allowed'].sum()) if not queue_df.empty else 0}`",
        "",
        "## Summary",
        dataframe_to_markdown(site_summary_df.loc[:, summary_cols] if not site_summary_df.empty else site_summary_df),
        "",
        "## Safety Boundary",
        "- This is an acquisition queue only.",
        "- It does not mark any row as confirmed truth.",
        "- It does not approve threshold replay, operator-facing promotion, or direct `panel_day_engine.py` edits.",
        "- Collected rows must be fed back through BR-098 before a separate truth-intake branch can exist.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(
    path: Path,
    owner_branch: str,
    repo_root: Path,
    output_dir: Path,
    attachment_input: Path,
    queue_df: pd.DataFrame,
    panel_df: pd.DataFrame,
    site_summary_df: pd.DataFrame,
    collector_template_df: pd.DataFrame,
) -> None:
    payload: dict[str, Any] = {
        "owner_branch": owner_branch,
        "repo_root": str(repo_root),
        "output_dir": str(output_dir),
        "attachment_input": str(attachment_input),
        "queue_rows": int(len(queue_df)),
        "panel_summary_rows": int(len(panel_df)),
        "site_summary_rows": int(len(site_summary_df)),
        "collector_template_rows": int(len(collector_template_df)),
        "open_required_axes": int(queue_df["truth_intake_blocker_flag"].sum()) if not queue_df.empty else 0,
        "independent_confirmation_queue_rows": int(queue_df["acquisition_axis"].eq("independent_panel_confirmation").sum())
        if not queue_df.empty
        else 0,
        "common_cause_clearance_queue_rows": int(queue_df["acquisition_axis"].eq("common_cause_clearance").sum())
        if not queue_df.empty
        else 0,
        "measurement_artifact_clearance_queue_rows": int(
            queue_df["acquisition_axis"].eq("measurement_artifact_clearance").sum()
        )
        if not queue_df.empty
        else 0,
        "counterexample_clearance_queue_rows": int(queue_df["acquisition_axis"].eq("counterexample_clearance").sum())
        if not queue_df.empty
        else 0,
        "truth_intake_ready_rows": int(panel_df["truth_intake_ready"].sum()) if not panel_df.empty else 0,
        "operator_facing_change_allowed_sum": int(queue_df["operator_facing_change_allowed"].sum())
        if not queue_df.empty
        else 0,
        "engine_patch_allowed_sum": int(queue_df["engine_patch_allowed"].sum()) if not queue_df.empty else 0,
        "threshold_patch_allowed_sum": int(queue_df["threshold_patch_allowed"].sum()) if not queue_df.empty else 0,
        "recommended_next_branch": "fill_collector_template_then_rerun_br098",
        "outputs": {
            "queue": str(output_dir / QUEUE_OUTPUT_NAME),
            "panel_summary": str(output_dir / PANEL_SUMMARY_OUTPUT_NAME),
            "site_summary": str(output_dir / SITE_SUMMARY_OUTPUT_NAME),
            "collector_template": str(output_dir / COLLECTOR_TEMPLATE_OUTPUT_NAME),
            "note": str(output_dir / NOTE_OUTPUT_NAME),
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a collector-facing acquisition queue from BR-098 voltage-preserved independent-confirmation gaps."
    )
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--attachment-dir", default=DEFAULT_ATTACHMENT_DIR, help="BR-098 attachment output directory.")
    parser.add_argument("--attachment-input", default="", help="Optional direct BR-098 attachment CSV.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory for BR-099 artifacts.")
    parser.add_argument("--owner-branch", default="BR-20260425-099")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    attachment_dir = resolve_path(repo_root, args.attachment_dir)
    attachment_input = (
        resolve_path(repo_root, args.attachment_input)
        if normalize_text(args.attachment_input)
        else attachment_dir / ATTACHMENT_INPUT_NAME
    )
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    attachment_df = normalize_attachment(
        read_required_csv(attachment_input, ATTACHMENT_REQUIRED_COLUMNS, "BR-098 attachment")
    )
    assert_safe_start(attachment_df)

    queue_df = build_queue(args.owner_branch, attachment_df)
    panel_summary_df = build_panel_summary(args.owner_branch, queue_df, attachment_df)
    site_summary_df = build_site_summary(args.owner_branch, panel_summary_df, queue_df)
    collector_template_df = build_collector_template(args.owner_branch, queue_df)

    queue_df.to_csv(output_dir / QUEUE_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    panel_summary_df.to_csv(output_dir / PANEL_SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    site_summary_df.to_csv(output_dir / SITE_SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    collector_template_df.to_csv(output_dir / COLLECTOR_TEMPLATE_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(output_dir / NOTE_OUTPUT_NAME, args.owner_branch, attachment_input, queue_df, site_summary_df)
    write_json(
        output_dir / JSON_OUTPUT_NAME,
        args.owner_branch,
        repo_root,
        output_dir,
        attachment_input,
        queue_df,
        panel_summary_df,
        site_summary_df,
        collector_template_df,
    )

    print(
        json.dumps(
            {
                "owner_branch": args.owner_branch,
                "queue_rows": int(len(queue_df)),
                "panel_summary_rows": int(len(panel_summary_df)),
                "site_summary_rows": int(len(site_summary_df)),
                "collector_template_rows": int(len(collector_template_df)),
                "open_required_axes": int(queue_df["truth_intake_blocker_flag"].sum()) if not queue_df.empty else 0,
                "independent_confirmation_queue_rows": int(
                    queue_df["acquisition_axis"].eq("independent_panel_confirmation").sum()
                )
                if not queue_df.empty
                else 0,
                "common_cause_clearance_queue_rows": int(queue_df["acquisition_axis"].eq("common_cause_clearance").sum())
                if not queue_df.empty
                else 0,
                "measurement_artifact_clearance_queue_rows": int(
                    queue_df["acquisition_axis"].eq("measurement_artifact_clearance").sum()
                )
                if not queue_df.empty
                else 0,
                "counterexample_clearance_queue_rows": int(
                    queue_df["acquisition_axis"].eq("counterexample_clearance").sum()
                )
                if not queue_df.empty
                else 0,
                "truth_intake_ready_rows": int(panel_summary_df["truth_intake_ready"].sum())
                if not panel_summary_df.empty
                else 0,
                "engine_patch_allowed_sum": int(queue_df["engine_patch_allowed"].sum()) if not queue_df.empty else 0,
                "outputs": {
                    "queue": str(output_dir / QUEUE_OUTPUT_NAME),
                    "panel_summary": str(output_dir / PANEL_SUMMARY_OUTPUT_NAME),
                    "site_summary": str(output_dir / SITE_SUMMARY_OUTPUT_NAME),
                    "collector_template": str(output_dir / COLLECTOR_TEMPLATE_OUTPUT_NAME),
                    "note": str(output_dir / NOTE_OUTPUT_NAME),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
