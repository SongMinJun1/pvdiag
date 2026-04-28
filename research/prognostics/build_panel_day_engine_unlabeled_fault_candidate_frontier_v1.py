#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-100"

DEFAULT_INPUT_DIR = "release/conalog_full_runtime_v1/package/_share"
DEFAULT_OUTPUT_DIR = "/private/tmp/panel_day_engine_unlabeled_fault_candidate_frontier_br100_check"
INPUT_NAME = "panel_date_reaudit_working.csv"

FRONTIER_OUTPUT_NAME = "panel_day_engine_unlabeled_fault_candidate_frontier_v1.csv"
PRIORITY_OUTPUT_NAME = "panel_day_engine_unlabeled_fault_candidate_priority_v1.csv"
SITE_SUMMARY_OUTPUT_NAME = "panel_day_engine_unlabeled_fault_candidate_site_summary_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_unlabeled_fault_candidate_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_unlabeled_fault_candidate_frontier_v1.json"

REQUIRED_COLUMNS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "first_warning_date",
    "retrospective_onset_date",
    "days_earlier_than_trigger",
    "onset_confidence",
    "onset_method",
    "reason_summary",
    "vendor_reply_class",
    "vendor_fault_family",
    "field_confirmed_flag",
    "dispute_type",
    "review_priority",
    "candidate_validity",
    "note",
]

FRONTIER_COLUMNS = [
    "owner_branch",
    "source_row_id",
    "site",
    "root_id",
    "panel_group_key",
    "panel_id",
    "strict_trigger_date",
    "first_warning_date",
    "retrospective_onset_date",
    "days_earlier_than_trigger",
    "onset_confidence",
    "onset_method",
    "review_priority",
    "seed_label_status",
    "candidate_validity",
    "vendor_reply_class",
    "vendor_fault_family",
    "field_confirmed_flag",
    "same_site_trigger_date_panel_count",
    "same_root_trigger_date_panel_count",
    "same_group_trigger_date_panel_count",
    "data_candidate_bucket",
    "data_fault_like_candidate_flag",
    "strong_unlabeled_candidate_flag",
    "trigger_only_bulk_screen_flag",
    "common_cause_screen_flag",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
    "review_priority_bucket",
    "evidence_to_collect",
    "data_only_basis",
    "notes",
]

SITE_SUMMARY_COLUMNS = [
    "owner_branch",
    "summary_scope",
    "summary_key",
    "total_rows",
    "seed_positive_fault_rows",
    "seed_non_panel_or_negative_rows",
    "seed_needs_more_info_rows",
    "unlabeled_rows",
    "unlabeled_persistent_rows",
    "strong_unlabeled_candidate_rows",
    "strong_unlabeled_isolated_rows",
    "strong_unlabeled_common_cause_screen_rows",
    "strong_unlabeled_30d_plus_rows",
    "trigger_only_unlabeled_rows",
    "trigger_only_bulk_screen_rows",
    "common_cause_screen_rows",
    "truth_intake_allowed_sum",
    "engine_patch_allowed_sum",
    "notes",
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


def panel_root(panel_id: str) -> str:
    return panel_id.split(".")[0] if panel_id else ""


def panel_group(panel_id: str) -> str:
    parts = panel_id.split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else panel_id


def read_required_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing required input: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"{path.name} missing columns: {missing}")
    return df


def normalize_input(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in REQUIRED_COLUMNS:
        if col in {"days_earlier_than_trigger", "field_confirmed_flag"}:
            out[col] = pd.to_numeric(out[col], errors="coerce")
        else:
            out[col] = out[col].map(normalize_text)
    out["root_id"] = out["panel_id"].map(panel_root)
    out["panel_group_key"] = out["panel_id"].map(panel_group)
    out["days_earlier_than_trigger"] = out["days_earlier_than_trigger"].fillna(0)
    return out.reset_index(drop=True)


def seed_label_status(row: pd.Series) -> str:
    validity = normalize_text(row.get("candidate_validity"))
    if not validity:
        return "unlabeled_data_candidate"
    if validity == "true_positive":
        return "seed_positive_fault"
    if validity in {"false_positive", "group_side"}:
        return "seed_non_panel_or_negative"
    if validity == "needs_more_info":
        return "seed_needs_more_info"
    return "seed_other_reviewed"


def bucket_unlabeled(row: pd.Series) -> str:
    if row["seed_label_status"] != "unlabeled_data_candidate":
        return f"L_reviewed_{row['seed_label_status']}"

    onset_method = normalize_text(row["onset_method"])
    onset_confidence = normalize_text(row["onset_confidence"])
    days = numeric_float(row["days_earlier_than_trigger"])
    same_site = numeric_int(row["same_site_trigger_date_panel_count"])
    same_root = numeric_int(row["same_root_trigger_date_panel_count"])
    same_group = numeric_int(row["same_group_trigger_date_panel_count"])

    if onset_method == "persistent_5of7" and onset_confidence == "high" and days >= 7:
        return "U1_strong_persistent_lead_review"
    if onset_method == "persistent_5of7":
        return "U2_persistent_short_or_medium_review"
    if onset_method == "strict_trigger_fallback" and (same_group >= 2 or same_root >= 2 or same_site >= 5):
        return "U3_trigger_only_common_cause_screen"
    if onset_method == "strict_trigger_fallback":
        return "U4_trigger_only_singleton_screen"
    return "U5_unclassified_unlabeled_review"


def review_priority_bucket(row: pd.Series) -> str:
    bucket = normalize_text(row["data_candidate_bucket"])
    days = numeric_float(row["days_earlier_than_trigger"])
    if bucket == "U1_strong_persistent_lead_review" and days >= 30:
        return "P0_strong_data_only_fault_like_30d_plus"
    if bucket == "U1_strong_persistent_lead_review":
        return "P1_strong_data_only_fault_like_7d_plus"
    if bucket == "U2_persistent_short_or_medium_review":
        return "P2_persistent_shape_review"
    if bucket == "U3_trigger_only_common_cause_screen":
        return "P3_common_cause_or_group_screen"
    if bucket == "U4_trigger_only_singleton_screen":
        return "P4_trigger_only_low_confidence_screen"
    return "P5_reviewed_or_other"


def evidence_to_collect(row: pd.Series) -> str:
    bucket = normalize_text(row["data_candidate_bucket"])
    if bucket == "U1_strong_persistent_lead_review":
        return (
            "Exact-panel raw curve trace around onset/trigger, independent maintenance or field note, "
            "and explicit common-cause/measurement-artifact clearance."
        )
    if bucket == "U2_persistent_short_or_medium_review":
        return "Raw curve trace and recurrence check before treating this as a panel-local candidate."
    if bucket == "U3_trigger_only_common_cause_screen":
        return "Same site/root/group breadth review first; only keep panel-local candidates after common-cause clearance."
    if bucket == "U4_trigger_only_singleton_screen":
        return "Low-priority strict-trigger-only review; require raw trace shape before escalation."
    if bucket.startswith("L_reviewed_seed_positive_fault"):
        return "Already seed-reviewed positive reference; keep as gold/reference, not new unlabeled evidence."
    return "Reviewed/reference row; no new data-only promotion."


def data_only_basis(row: pd.Series) -> str:
    return (
        f"onset_method={row['onset_method']}; onset_confidence={row['onset_confidence']}; "
        f"lead_days={numeric_float(row['days_earlier_than_trigger']):.0f}; "
        f"same_site_date_n={numeric_int(row['same_site_trigger_date_panel_count'])}; "
        f"same_root_date_n={numeric_int(row['same_root_trigger_date_panel_count'])}; "
        f"same_group_date_n={numeric_int(row['same_group_trigger_date_panel_count'])}"
    )


def build_frontier(df: pd.DataFrame) -> pd.DataFrame:
    out = normalize_input(df)
    out["source_row_id"] = [f"BR100-UFCF-{idx:03d}" for idx in range(1, len(out) + 1)]

    site_counts = out.groupby(["site", "strict_trigger_date"])["panel_id"].transform("count")
    root_counts = out.groupby(["site", "root_id", "strict_trigger_date"])["panel_id"].transform("count")
    group_counts = out.groupby(["site", "panel_group_key", "strict_trigger_date"])["panel_id"].transform("count")
    out["same_site_trigger_date_panel_count"] = site_counts.fillna(0).astype(int)
    out["same_root_trigger_date_panel_count"] = root_counts.fillna(0).astype(int)
    out["same_group_trigger_date_panel_count"] = group_counts.fillna(0).astype(int)

    out["seed_label_status"] = out.apply(seed_label_status, axis=1)
    out["data_candidate_bucket"] = out.apply(bucket_unlabeled, axis=1)
    out["data_fault_like_candidate_flag"] = (out["data_candidate_bucket"] == "U1_strong_persistent_lead_review").astype(int)
    out["strong_unlabeled_candidate_flag"] = out["data_fault_like_candidate_flag"]
    out["trigger_only_bulk_screen_flag"] = (out["data_candidate_bucket"] == "U3_trigger_only_common_cause_screen").astype(int)
    out["common_cause_screen_flag"] = (
        (out["same_group_trigger_date_panel_count"] >= 2)
        | (out["same_root_trigger_date_panel_count"] >= 2)
        | (out["same_site_trigger_date_panel_count"] >= 5)
    ).astype(int)
    out["truth_intake_allowed"] = 0
    out["threshold_patch_allowed"] = 0
    out["engine_patch_allowed"] = 0
    out["review_priority_bucket"] = out.apply(review_priority_bucket, axis=1)
    out["evidence_to_collect"] = out.apply(evidence_to_collect, axis=1)
    out["data_only_basis"] = out.apply(data_only_basis, axis=1)
    out["notes"] = out.apply(
        lambda row: (
            "Data-only candidate frontier only; not a truth label. "
            f"source_note={normalize_text(row.get('note'))}"
        ).strip(),
        axis=1,
    )
    out["owner_branch"] = OWNER_BRANCH

    return out.reindex(columns=FRONTIER_COLUMNS).sort_values(
        ["strong_unlabeled_candidate_flag", "review_priority_bucket", "site", "strict_trigger_date", "panel_id"],
        ascending=[False, True, True, True, True],
    )


def build_priority(frontier: pd.DataFrame) -> pd.DataFrame:
    priority = frontier[frontier["seed_label_status"] == "unlabeled_data_candidate"].copy()
    return priority.sort_values(
        ["review_priority_bucket", "site", "strict_trigger_date", "panel_id"],
        ascending=[True, True, True, True],
    ).reset_index(drop=True)


def summarize(frontier: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    groups: list[tuple[str, str, pd.DataFrame]] = [("overall", "all", frontier)]
    groups.extend(("site", site, sub) for site, sub in frontier.groupby("site", dropna=False))
    for scope, key, sub in groups:
        unlabeled = sub["seed_label_status"].eq("unlabeled_data_candidate")
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "summary_scope": scope,
                "summary_key": key,
                "total_rows": int(len(sub)),
                "seed_positive_fault_rows": int(sub["seed_label_status"].eq("seed_positive_fault").sum()),
                "seed_non_panel_or_negative_rows": int(sub["seed_label_status"].eq("seed_non_panel_or_negative").sum()),
                "seed_needs_more_info_rows": int(sub["seed_label_status"].eq("seed_needs_more_info").sum()),
                "unlabeled_rows": int(unlabeled.sum()),
                "unlabeled_persistent_rows": int((unlabeled & sub["onset_method"].eq("persistent_5of7")).sum()),
                "strong_unlabeled_candidate_rows": int(sub["strong_unlabeled_candidate_flag"].sum()),
                "strong_unlabeled_isolated_rows": int(
                    (sub["strong_unlabeled_candidate_flag"].eq(1) & sub["common_cause_screen_flag"].eq(0)).sum()
                ),
                "strong_unlabeled_common_cause_screen_rows": int(
                    (sub["strong_unlabeled_candidate_flag"].eq(1) & sub["common_cause_screen_flag"].eq(1)).sum()
                ),
                "strong_unlabeled_30d_plus_rows": int(
                    (
                        sub["strong_unlabeled_candidate_flag"].eq(1)
                        & (pd.to_numeric(sub["days_earlier_than_trigger"], errors="coerce").fillna(0) >= 30)
                    ).sum()
                ),
                "trigger_only_unlabeled_rows": int((unlabeled & sub["onset_method"].eq("strict_trigger_fallback")).sum()),
                "trigger_only_bulk_screen_rows": int(sub["trigger_only_bulk_screen_flag"].sum()),
                "common_cause_screen_rows": int(sub["common_cause_screen_flag"].sum()),
                "truth_intake_allowed_sum": int(sub["truth_intake_allowed"].sum()),
                "engine_patch_allowed_sum": int(sub["engine_patch_allowed"].sum()),
                "notes": "Counts are candidate-frontier only; no unlabeled row is promoted to truth.",
            }
        )
    return pd.DataFrame(rows).reindex(columns=SITE_SUMMARY_COLUMNS)


def write_note(output_dir: Path, frontier: pd.DataFrame, priority: pd.DataFrame, summary: pd.DataFrame) -> Path:
    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    bucket_counts = frontier["data_candidate_bucket"].value_counts().sort_index()
    site_table = summary[summary["summary_scope"].eq("site")][
        [
            "summary_key",
            "total_rows",
            "unlabeled_rows",
            "strong_unlabeled_candidate_rows",
            "strong_unlabeled_isolated_rows",
            "strong_unlabeled_common_cause_screen_rows",
            "strong_unlabeled_30d_plus_rows",
            "trigger_only_unlabeled_rows",
            "trigger_only_bulk_screen_rows",
        ]
    ]
    lines = [
        "# BR-100 Unlabeled Fault Candidate Frontier",
        "",
        "## Purpose",
        "- Separate seed-labeled faults from data-only, unlabeled fault-like candidates.",
        "- Keep unlabeled candidates out of truth labels until exact-panel evidence and clearance exist.",
        "- Make the hidden candidate pool visible without changing `panel_day_engine.py` or operator verdicts.",
        "",
        "## Real Result",
        f"- source rows: `{overall['total_rows']}`",
        f"- seed positive fault rows: `{overall['seed_positive_fault_rows']}`",
        f"- seed non-panel/negative rows: `{overall['seed_non_panel_or_negative_rows']}`",
        f"- seed needs-more-info rows: `{overall['seed_needs_more_info_rows']}`",
        f"- unlabeled rows: `{overall['unlabeled_rows']}`",
        f"- unlabeled persistent rows: `{overall['unlabeled_persistent_rows']}`",
        f"- strong unlabeled data-only candidates: `{overall['strong_unlabeled_candidate_rows']}`",
        f"- strong unlabeled isolated candidates: `{overall['strong_unlabeled_isolated_rows']}`",
        f"- strong unlabeled common-cause-screen candidates: `{overall['strong_unlabeled_common_cause_screen_rows']}`",
        f"- strong unlabeled 30d+ lead candidates: `{overall['strong_unlabeled_30d_plus_rows']}`",
        f"- trigger-only unlabeled rows: `{overall['trigger_only_unlabeled_rows']}`",
        f"- trigger-only bulk/common-cause screen rows: `{overall['trigger_only_bulk_screen_rows']}`",
        f"- priority queue rows: `{len(priority)}`",
        "- truth intake allowed sum: `0`",
        "- engine patch allowed sum: `0`",
        "",
        "## Bucket Counts",
    ]
    lines.extend(f"- `{bucket}`: `{int(count)}`" for bucket, count in bucket_counts.items())
    lines.extend(
        [
            "",
            "## Site Split",
            "| site | total_rows | unlabeled_rows | strong_unlabeled_candidate_rows | isolated_strong_rows | common_cause_screen_strong_rows | strong_unlabeled_30d_plus_rows | trigger_only_unlabeled_rows | trigger_only_bulk_screen_rows |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in site_table.to_dict("records"):
        lines.append(
            f"| `{row['summary_key']}` | {row['total_rows']} | {row['unlabeled_rows']} | "
            f"{row['strong_unlabeled_candidate_rows']} | {row['strong_unlabeled_isolated_rows']} | "
            f"{row['strong_unlabeled_common_cause_screen_rows']} | {row['strong_unlabeled_30d_plus_rows']} | "
            f"{row['trigger_only_unlabeled_rows']} | {row['trigger_only_bulk_screen_rows']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "- The labeled fault count is not the full fault universe; it is only the confirmed/seed-reviewed subset.",
            "- BR-100 exposes the hidden frontier: unlabeled rows with strong persistent high-confidence lead are the first data-only review targets.",
            "- Strong data-only does not mean confirmed: common-cause-screen strong rows still need breadth clearance before panel-local interpretation.",
            "- Trigger-only rows are not automatically fault-like; many are bulk/common-cause screens and need breadth clearance before panel-local promotion.",
            "- No row from this branch is a truth label, threshold input, or engine patch approval.",
            "",
            "## Ordered Next Path",
            "1. Manually review `U1_strong_persistent_lead_review` rows first.",
            "2. For each candidate, attach exact-panel raw curve traces and maintenance/inspection evidence if available.",
            "3. Clear common-cause and measurement-artifact alternatives before truth intake.",
            "4. Only after evidence attachment should a separate truth-intake gate consider expanding the confirmed-positive set.",
        ]
    )
    note_path = output_dir / NOTE_OUTPUT_NAME
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--input-dir", default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    input_dir = resolve_path(repo_root, args.input_dir)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source = read_required_csv(input_dir / INPUT_NAME)
    frontier = build_frontier(source)
    priority = build_priority(frontier)
    summary = summarize(frontier)

    frontier_path = output_dir / FRONTIER_OUTPUT_NAME
    priority_path = output_dir / PRIORITY_OUTPUT_NAME
    summary_path = output_dir / SITE_SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    frontier.to_csv(frontier_path, index=False, encoding="utf-8-sig")
    priority.to_csv(priority_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, frontier, priority, summary)

    payload = {
        "owner_branch": OWNER_BRANCH,
        "source_rows": int(len(frontier)),
        "priority_queue_rows": int(len(priority)),
        "unlabeled_rows": int((frontier["seed_label_status"] == "unlabeled_data_candidate").sum()),
        "strong_unlabeled_candidate_rows": int(frontier["strong_unlabeled_candidate_flag"].sum()),
        "strong_unlabeled_isolated_rows": int(
            (frontier["strong_unlabeled_candidate_flag"].eq(1) & frontier["common_cause_screen_flag"].eq(0)).sum()
        ),
        "strong_unlabeled_common_cause_screen_rows": int(
            (frontier["strong_unlabeled_candidate_flag"].eq(1) & frontier["common_cause_screen_flag"].eq(1)).sum()
        ),
        "strong_unlabeled_30d_plus_rows": int(
            (
                frontier["strong_unlabeled_candidate_flag"].eq(1)
                & (pd.to_numeric(frontier["days_earlier_than_trigger"], errors="coerce").fillna(0) >= 30)
            ).sum()
        ),
        "trigger_only_bulk_screen_rows": int(frontier["trigger_only_bulk_screen_flag"].sum()),
        "truth_intake_allowed_sum": int(frontier["truth_intake_allowed"].sum()),
        "engine_patch_allowed_sum": int(frontier["engine_patch_allowed"].sum()),
        "outputs": {
            "frontier": str(frontier_path),
            "priority": str(priority_path),
            "site_summary": str(summary_path),
            "note": str(note_path),
            "json": str(json_path),
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
