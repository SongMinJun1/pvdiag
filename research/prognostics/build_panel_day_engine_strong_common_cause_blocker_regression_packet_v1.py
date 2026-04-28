#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_JUDGMENT_INPUT = Path(
    "/private/tmp/fault_family_judgment_candidate_packet_check/"
    "panel_day_engine_fault_family_judgment_candidate_packet_v1.csv"
)

DETAIL_OUTPUT_NAME = "panel_day_engine_strong_common_cause_blocker_regression_packet_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_strong_common_cause_blocker_regression_summary_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_strong_common_cause_blocker_regression_note_v1.md"

JUDGMENT_REQUIRED_COLS = [
    "candidate_case_id",
    "site",
    "panel_id",
    "judgment_bucket",
    "candidate_family_label_ko",
    "candidate_family_track",
    "axis_presence_count",
    "duration_gap_axis_flag",
    "continuity_recurrence_axis_flag",
    "spatiality_common_cause_axis_flag",
    "candidate_evidence_axis_count",
    "review_focus_bucket",
    "friction_blocker_types",
    "friction_direct_row_count",
    "friction_group_off_row_count",
    "friction_site_event_row_count",
    "recovery_bucket",
    "re_drop_row_count",
    "recovered_sustained_row_count",
    "synchrony_bucket",
    "common_cause_row_count",
    "site_event_row_count",
    "group_off_row_count",
    "subgroup_common_cause_row_count",
    "max_co_drop_frac",
    "operator_promotion_allowed_flag",
    "engine_patch_candidate_flag",
    "threshold_candidate_role",
]

DETAIL_COLS = [
    "blocker_case_id",
    "source_candidate_case_id",
    "site",
    "panel_id",
    "panel_root_id",
    "common_cause_blocker_type",
    "regression_seed_role",
    "candidate_family_label_ko",
    "candidate_family_track",
    "judgment_bucket",
    "review_focus_bucket",
    "operator_promotion_allowed_flag",
    "engine_patch_candidate_flag",
    "threshold_patch_allowed_flag",
    "panel_local_promotion_blocked_flag",
    "regression_seed_flag",
    "axis_presence_count",
    "duration_gap_axis_flag",
    "continuity_recurrence_axis_flag",
    "spatiality_common_cause_axis_flag",
    "candidate_evidence_axis_count",
    "friction_blocker_types",
    "friction_direct_row_count",
    "friction_group_off_row_count",
    "friction_site_event_row_count",
    "recovery_bucket",
    "re_drop_row_count",
    "recovered_sustained_row_count",
    "synchrony_bucket",
    "common_cause_row_count",
    "site_event_row_count",
    "group_off_row_count",
    "subgroup_common_cause_row_count",
    "max_co_drop_frac",
    "required_next_evidence",
    "review_note",
]

SUMMARY_COLS = [
    "site",
    "common_cause_blocker_type",
    "regression_seed_role",
    "cases",
    "unique_panel_roots",
    "operator_promotion_allowed_sum",
    "engine_patch_candidate_sum",
    "threshold_patch_allowed_sum",
    "panel_local_promotion_blocked_sum",
    "regression_seed_sum",
    "max_co_drop_frac_max",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Package BR-064 strong common-cause hold rows as regression/blocker seeds, "
            "not panel-local promotion candidates."
        )
    )
    parser.add_argument("--judgment-input", type=Path, default=DEFAULT_JUDGMENT_INPUT)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def numeric_value(value: object) -> float:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0.0 if pd.isna(numeric) else float(numeric)


def int_value(value: object) -> int:
    return int(round(numeric_value(value)))


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def require_columns(df: pd.DataFrame, cols: list[str], label: str) -> None:
    missing = [col for col in cols if col not in df.columns]
    if missing:
        raise SystemExit(f"{label} is missing columns: {missing}")


def panel_root_id(panel_id: str) -> str:
    parts = panel_id.split(".")
    if len(parts) >= 3:
        return ".".join(parts[:-1])
    return panel_id


def common_cause_blocker_type(row: pd.Series) -> str:
    synchrony = normalize_text(row.get("synchrony_bucket")).lower()
    blocker = normalize_text(row.get("friction_blocker_types")).lower()
    site_events = numeric_value(row.get("site_event_row_count"))
    group_off = numeric_value(row.get("group_off_row_count"))
    subgroup = numeric_value(row.get("subgroup_common_cause_row_count"))
    common_rows = numeric_value(row.get("common_cause_row_count"))
    co_drop = numeric_value(row.get("max_co_drop_frac"))

    if "group_off" in synchrony or group_off > 0:
        return "group_off_synchrony_blocker"
    if "site_event" in synchrony or site_events > 0 or "site_event" in blocker:
        return "site_event_synchrony_blocker"
    if subgroup > 0:
        return "subgroup_common_cause_blocker"
    if co_drop >= 0.20 or common_rows > 0:
        return "broad_common_cause_blocker"
    return "common_cause_context_blocker"


def required_next_evidence(blocker_type: str) -> str:
    if blocker_type == "group_off_synchrony_blocker":
        return "separate group-off/site-event interval before any individual panel precursor reading"
    if blocker_type == "site_event_synchrony_blocker":
        return "confirm whether the site-event window explains the panel signal before panel-local promotion"
    if blocker_type == "subgroup_common_cause_blocker":
        return "separate subgroup-level common-cause context from exact panel-local morphology"
    if blocker_type == "broad_common_cause_blocker":
        return "review breadth/co-drop context before interpreting panel-local precursor evidence"
    return "collect stronger spatiality evidence before panel-local promotion"


def normalize_judgment(df: pd.DataFrame) -> pd.DataFrame:
    require_columns(df, JUDGMENT_REQUIRED_COLS, "judgment input")
    out = df[JUDGMENT_REQUIRED_COLS].copy()
    for col in out.columns:
        if out[col].dtype == object:
            out[col] = out[col].map(normalize_text)
    return out


def build_detail(judgment: pd.DataFrame) -> pd.DataFrame:
    target = judgment.loc[
        judgment["review_focus_bucket"].map(normalize_text).eq("strong_common_cause_hold_review")
        | judgment["judgment_bucket"].map(normalize_text).eq("block_individual_precursor_common_cause")
    ].copy()
    rows: list[dict[str, object]] = []
    for idx, row in target.sort_values(["site", "panel_id", "candidate_case_id"]).reset_index(drop=True).iterrows():
        panel_id = normalize_text(row["panel_id"])
        blocker_type = common_cause_blocker_type(row)
        rows.append(
            {
                "blocker_case_id": f"BR071-{idx + 1:03d}",
                "source_candidate_case_id": normalize_text(row["candidate_case_id"]),
                "site": normalize_text(row["site"]),
                "panel_id": panel_id,
                "panel_root_id": panel_root_id(panel_id),
                "common_cause_blocker_type": blocker_type,
                "regression_seed_role": "block_panel_local_promotion_regression_seed",
                "candidate_family_label_ko": normalize_text(row["candidate_family_label_ko"]),
                "candidate_family_track": normalize_text(row["candidate_family_track"]),
                "judgment_bucket": normalize_text(row["judgment_bucket"]),
                "review_focus_bucket": normalize_text(row["review_focus_bucket"]),
                "operator_promotion_allowed_flag": 0,
                "engine_patch_candidate_flag": 0,
                "threshold_patch_allowed_flag": 0,
                "panel_local_promotion_blocked_flag": 1,
                "regression_seed_flag": 1,
                "axis_presence_count": int_value(row["axis_presence_count"]),
                "duration_gap_axis_flag": int_value(row["duration_gap_axis_flag"]),
                "continuity_recurrence_axis_flag": int_value(row["continuity_recurrence_axis_flag"]),
                "spatiality_common_cause_axis_flag": int_value(row["spatiality_common_cause_axis_flag"]),
                "candidate_evidence_axis_count": int_value(row["candidate_evidence_axis_count"]),
                "friction_blocker_types": normalize_text(row["friction_blocker_types"]),
                "friction_direct_row_count": int_value(row["friction_direct_row_count"]),
                "friction_group_off_row_count": int_value(row["friction_group_off_row_count"]),
                "friction_site_event_row_count": int_value(row["friction_site_event_row_count"]),
                "recovery_bucket": normalize_text(row["recovery_bucket"]),
                "re_drop_row_count": int_value(row["re_drop_row_count"]),
                "recovered_sustained_row_count": int_value(row["recovered_sustained_row_count"]),
                "synchrony_bucket": normalize_text(row["synchrony_bucket"]),
                "common_cause_row_count": int_value(row["common_cause_row_count"]),
                "site_event_row_count": int_value(row["site_event_row_count"]),
                "group_off_row_count": int_value(row["group_off_row_count"]),
                "subgroup_common_cause_row_count": int_value(row["subgroup_common_cause_row_count"]),
                "max_co_drop_frac": round(numeric_value(row["max_co_drop_frac"]), 6),
                "required_next_evidence": required_next_evidence(blocker_type),
                "review_note": (
                    "Strong common-cause synchrony is retained as blocker/regression material, "
                    "not as panel-local fault-family promotion evidence."
                ),
            }
        )
    return pd.DataFrame(rows).reindex(columns=DETAIL_COLS)


def build_summary(detail: pd.DataFrame) -> pd.DataFrame:
    if detail.empty:
        return pd.DataFrame(columns=SUMMARY_COLS)
    summary = (
        detail.groupby(["site", "common_cause_blocker_type", "regression_seed_role"], dropna=False)
        .agg(
            cases=("blocker_case_id", "nunique"),
            unique_panel_roots=("panel_root_id", "nunique"),
            operator_promotion_allowed_sum=("operator_promotion_allowed_flag", "sum"),
            engine_patch_candidate_sum=("engine_patch_candidate_flag", "sum"),
            threshold_patch_allowed_sum=("threshold_patch_allowed_flag", "sum"),
            panel_local_promotion_blocked_sum=("panel_local_promotion_blocked_flag", "sum"),
            regression_seed_sum=("regression_seed_flag", "sum"),
            max_co_drop_frac_max=("max_co_drop_frac", "max"),
        )
        .reset_index()
    )
    return summary.reindex(columns=SUMMARY_COLS).sort_values(["site", "common_cause_blocker_type"])


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    header = "| " + " | ".join(df.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(df.columns)) + " |"
    rows = [
        "| " + " | ".join(normalize_text(row[col]) for col in df.columns)
        + " |"
        for row in df.to_dict(orient="records")
    ]
    return "\n".join([header, separator] + rows)


def write_note(output_dir: Path, detail: pd.DataFrame, summary: pd.DataFrame) -> None:
    lines = [
        "# panel_day_engine_strong_common_cause_blocker_regression_note_v1",
        "",
        "## Purpose",
        "- Package BR-064 strong common-cause hold rows as blocker/regression seeds.",
        "- Prevent spatial/common-cause evidence from being read as panel-local promotion evidence.",
        "",
        "## Guardrails",
        f"- detail rows: `{len(detail)}`",
        f"- operator promotion allowed sum: `{int(detail['operator_promotion_allowed_flag'].sum()) if len(detail) else 0}`",
        f"- engine patch candidate sum: `{int(detail['engine_patch_candidate_flag'].sum()) if len(detail) else 0}`",
        f"- threshold patch allowed sum: `{int(detail['threshold_patch_allowed_flag'].sum()) if len(detail) else 0}`",
        f"- panel-local promotion blocked sum: `{int(detail['panel_local_promotion_blocked_flag'].sum()) if len(detail) else 0}`",
        "",
        "## Summary",
        dataframe_to_markdown(summary),
        "",
        "## Interpretation",
        "- These rows can pressure-test future algorithm changes.",
        "- They must not become positive panel-local precursor or fault-family threshold examples.",
        "- Any future engine patch should prove these rows remain blocked or explicitly reclassified by new independent evidence.",
    ]
    (output_dir / NOTE_OUTPUT_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    judgment = normalize_judgment(read_csv(args.judgment_input))
    detail = build_detail(judgment)
    summary = build_summary(detail)
    if len(detail) and int(detail["operator_promotion_allowed_flag"].sum()) != 0:
        raise SystemExit("common-cause blocker packet must not allow operator promotion")
    if len(detail) and int(detail["engine_patch_candidate_flag"].sum()) != 0:
        raise SystemExit("common-cause blocker packet must not allow engine patch")
    if len(detail) and int(detail["threshold_patch_allowed_flag"].sum()) != 0:
        raise SystemExit("common-cause blocker packet must not allow threshold patch")
    detail.to_csv(args.output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(args.output_dir, detail, summary)


if __name__ == "__main__":
    main()
