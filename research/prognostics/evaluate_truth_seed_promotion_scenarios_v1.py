#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from evaluate_full_algorithm_f1_v3 import (
    ACTIONABILITY_REQUIRED_COLS,
    KEY_COLS,
    REAUDIT_REQUIRED_COLS,
    VALID_CANDIDATE_VALIDITY,
    VENDOR_REQUIRED_COLS,
    coalesce_text,
    dedupe,
    derive_actionability,
    ensure_columns,
    normalize_date,
    normalize_text,
    parse_reason_summary,
)
from evaluate_truth_seed_impact_v1 import evaluate_state

SCENARIOS = ("current_canonical", "safe_same_label_only", "full_ready_rows")
SUMMARY_COLS = [
    "scenario",
    "ready_unique_case_count",
    "safe_same_label_case_count",
    "gate_review_case_count",
    "truth_mode",
    "prediction_mode",
    "source_split",
    "tp",
    "fp",
    "fn",
    "tn",
    "precision",
    "recall",
    "f1",
    "excluded_rows",
    "scored_rows",
    "manual_truth_present_count",
    "vendor_truth_used_count",
]
SAFE_ROW_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "candidate_validity_proposed",
    "date_judgement_proposed",
    "note_proposed",
    "review_owner",
    "review_status",
    "vendor_reply_class",
    "vendor_fault_family",
    "actionability_v3",
    "change_class",
]
GATE_ROW_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "candidate_validity_proposed",
    "date_judgement_proposed",
    "note_proposed",
    "review_owner",
    "review_status",
    "vendor_reply_class",
    "vendor_fault_family",
    "actionability_v3",
    "current_strict_truth_label",
    "proposed_strict_truth_label",
    "gate_reason",
]
CHANGED_CASE_COLS = [
    "scenario",
    "site",
    "panel_id",
    "strict_trigger_date",
    "truth_mode",
    "current_truth_source",
    "current_truth_label",
    "scenario_truth_source",
    "scenario_truth_label",
    "candidate_validity_proposed",
    "vendor_reply_class",
    "vendor_fault_family",
    "actionability_v3",
    "scenario_change_type",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split ready truth seeds into safe vs gate-review rows and evaluate promotion scenarios in memory."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to project root.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def key_tuple_from_row(row: pd.Series) -> tuple[str, str, str]:
    return (
        normalize_text(row["site"]),
        normalize_text(row["panel_id"]),
        normalize_date(row["strict_trigger_date"]),
    )


def ensure_unique(df: pd.DataFrame, name: str, cols: list[str]) -> pd.DataFrame:
    dupes = df.loc[df.duplicated(subset=cols, keep=False), cols]
    if not dupes.empty:
        raise SystemExit(f"{name} has duplicate rows on {cols}")
    return df


def build_joined_for_truth_df(root: Path, truth_df: pd.DataFrame) -> pd.DataFrame:
    vendor_df = read_csv(root / "_share" / "vendor_reply_adjudication_latest.csv")
    actionability_df = read_csv(root / "_share" / "critical_actionability_shadow_v3_latest.csv")

    ensure_columns(truth_df, REAUDIT_REQUIRED_COLS, "scenario_truth_df")
    ensure_columns(vendor_df, VENDOR_REQUIRED_COLS, "vendor_reply_adjudication_latest.csv")
    ensure_columns(actionability_df, ACTIONABILITY_REQUIRED_COLS, "critical_actionability_shadow_v3_latest.csv")

    truth_df = truth_df.copy()
    for df in [truth_df, vendor_df, actionability_df]:
        for col in ["site", "panel_id"]:
            df[col] = df[col].map(normalize_text)
        df["strict_trigger_date"] = df["strict_trigger_date"].map(normalize_date)

    for col in [
        "candidate_validity",
        "onset_confidence",
        "reason_summary",
        "review_priority",
        "vendor_reply_class",
        "vendor_fault_family",
        "note",
    ]:
        truth_df[col] = truth_df[col].map(normalize_text)
    for col in ["vendor_reply_class", "vendor_fault_family", "vendor_note"]:
        vendor_df[col] = vendor_df[col].map(normalize_text)
    actionability_df["actionability_v3"] = actionability_df["actionability_v3"].map(normalize_text)

    invalid_values = sorted(set(truth_df["candidate_validity"]) - VALID_CANDIDATE_VALIDITY)
    if invalid_values:
        raise SystemExit(f"scenario truth has invalid candidate_validity values: {invalid_values}")

    vendor_unique = dedupe(
        vendor_df.loc[:, VENDOR_REQUIRED_COLS],
        "vendor_reply_adjudication_latest.csv",
        KEY_COLS,
    ).rename(
        columns={
            "vendor_reply_class": "vendor_reply_class_vendor",
            "vendor_fault_family": "vendor_fault_family_vendor",
            "vendor_note": "vendor_note_vendor",
        }
    )
    actionability_unique = dedupe(
        actionability_df.loc[:, ACTIONABILITY_REQUIRED_COLS],
        "critical_actionability_shadow_v3_latest.csv",
        KEY_COLS,
    )

    joined = truth_df.merge(vendor_unique, on=KEY_COLS, how="left")
    joined = joined.merge(actionability_unique, on=KEY_COLS, how="left")
    joined["vendor_reply_class"] = joined.apply(
        lambda row: coalesce_text(row["vendor_reply_class"], row.get("vendor_reply_class_vendor", "")),
        axis=1,
    )
    joined["vendor_fault_family"] = joined.apply(
        lambda row: coalesce_text(row["vendor_fault_family"], row.get("vendor_fault_family_vendor", "")),
        axis=1,
    )
    joined["note"] = joined.apply(
        lambda row: coalesce_text(row["note"], row.get("vendor_note_vendor", "")),
        axis=1,
    )
    joined["actionability_v3"] = joined["actionability_v3"].fillna("").map(normalize_text)
    parsed = joined["reason_summary"].apply(parse_reason_summary).apply(pd.Series)
    joined = pd.concat([joined, parsed], axis=1)
    derived = joined.apply(derive_actionability, axis=1, result_type="expand")
    derived.columns = ["derived_actionability_v3", "prediction_source"]
    joined = pd.concat([joined, derived], axis=1)
    joined["final_actionability_v3"] = joined.apply(
        lambda row: coalesce_text(row["actionability_v3"], row["derived_actionability_v3"]),
        axis=1,
    )
    joined["truth_source"] = joined.apply(
        lambda row: "manual_truth" if normalize_text(row["candidate_validity"]) else ("vendor_truth" if normalize_text(row["vendor_reply_class"]) else ""),
        axis=1,
    )
    return joined


def load_ready_rows(root: Path) -> pd.DataFrame:
    copyback_df = read_csv(root / "_share" / "truth_review_copyback_rows_v1.csv")
    required = [
        *KEY_COLS,
        "candidate_validity_proposed",
        "candidate_validity_merged",
        "date_judgement_proposed",
        "date_judgement_merged",
        "note_proposed",
        "note_merged",
        "review_owner",
        "review_status",
        "apply_ready_flag",
    ]
    ensure_columns(copyback_df, required, "truth_review_copyback_rows_v1.csv")

    for col in KEY_COLS:
        normalizer = normalize_date if col == "strict_trigger_date" else normalize_text
        copyback_df[col] = copyback_df[col].map(normalizer)
    for col in [
        "candidate_validity_proposed",
        "candidate_validity_merged",
        "date_judgement_proposed",
        "date_judgement_merged",
        "note_proposed",
        "note_merged",
        "review_owner",
        "review_status",
    ]:
        copyback_df[col] = copyback_df[col].map(normalize_text)
    copyback_df["apply_ready_flag"] = copyback_df["apply_ready_flag"].fillna(0).astype(int)

    ready_df = copyback_df.loc[copyback_df["apply_ready_flag"].eq(1)].copy()
    ready_df = ensure_unique(ready_df, "truth_review_copyback_rows_v1.csv ready rows", KEY_COLS)
    return ready_df.reset_index(drop=True)


def load_changed_case_context(root: Path) -> pd.DataFrame:
    changed_df = read_csv(root / "_share" / "truth_seed_impact_changed_cases_v1.csv")
    ensure_columns(
        changed_df,
        [
            *KEY_COLS,
            "truth_mode",
            "current_truth_label",
            "proposed_truth_label",
            "vendor_reply_class",
            "vendor_fault_family",
            "actionability_v3",
            "change_type",
        ],
        "truth_seed_impact_changed_cases_v1.csv",
    )
    for col in KEY_COLS:
        normalizer = normalize_date if col == "strict_trigger_date" else normalize_text
        changed_df[col] = changed_df[col].map(normalizer)
    for col in [
        "truth_mode",
        "current_truth_label",
        "proposed_truth_label",
        "vendor_reply_class",
        "vendor_fault_family",
        "actionability_v3",
        "change_type",
    ]:
        changed_df[col] = changed_df[col].map(normalize_text)
    return changed_df


def build_ready_context(root: Path, ready_df: pd.DataFrame, changed_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    vendor_df = read_csv(root / "_share" / "vendor_reply_adjudication_latest.csv")
    actionability_df = read_csv(root / "_share" / "critical_actionability_shadow_v3_latest.csv")
    for df in [vendor_df, actionability_df]:
        for col in ["site", "panel_id"]:
            df[col] = df[col].map(normalize_text)
        df["strict_trigger_date"] = df["strict_trigger_date"].map(normalize_date)

    vendor_min = dedupe(
        vendor_df.loc[:, [*KEY_COLS, "vendor_reply_class", "vendor_fault_family"]],
        "vendor_reply_adjudication_latest.csv",
        KEY_COLS,
    )
    action_min = dedupe(
        actionability_df.loc[:, [*KEY_COLS, "actionability_v3"]],
        "critical_actionability_shadow_v3_latest.csv",
        KEY_COLS,
    )
    action_min["actionability_v3"] = action_min["actionability_v3"].map(normalize_text)

    gate_keys = set(
        changed_df.loc[changed_df["change_type"].eq("vendor_to_manual_label_changed"), KEY_COLS].itertuples(index=False, name=None)
    )
    ready_context = ready_df.merge(vendor_min, on=KEY_COLS, how="left")
    ready_context = ready_context.merge(action_min, on=KEY_COLS, how="left")
    for col in ["vendor_reply_class", "vendor_fault_family", "actionability_v3"]:
        ready_context[col] = ready_context[col].fillna("").map(normalize_text)
    ready_context["change_class"] = ready_context.apply(
        lambda row: "gate_review_required" if key_tuple_from_row(row) in gate_keys else "safe_same_label_copyback",
        axis=1,
    )

    strict_change_min = (
        changed_df.loc[changed_df["truth_mode"].eq("strict"), [*KEY_COLS, "current_truth_label", "proposed_truth_label"]]
        .drop_duplicates(subset=KEY_COLS)
        .rename(
            columns={
                "current_truth_label": "current_strict_truth_label",
                "proposed_truth_label": "proposed_strict_truth_label",
            }
        )
    )
    gate_context = (
        ready_context.loc[ready_context["change_class"].eq("gate_review_required")].copy()
        .merge(strict_change_min, on=KEY_COLS, how="left")
    )
    gate_context["current_strict_truth_label"] = gate_context["current_strict_truth_label"].fillna("").map(normalize_text)
    gate_context["proposed_strict_truth_label"] = gate_context["proposed_strict_truth_label"].fillna("").map(normalize_text)
    gate_context["gate_reason"] = gate_context.apply(
        lambda row: (
            f"strict 기준에서 {row['current_strict_truth_label']} -> {row['proposed_strict_truth_label']}로 바뀌므로 "
            "manual evidence 재확인이 필요"
        ),
        axis=1,
    )
    return ready_context, gate_context


def apply_ready_rows(canonical_df: pd.DataFrame, rows_to_apply: pd.DataFrame) -> pd.DataFrame:
    applied_df = canonical_df.copy()
    key_to_index = {tuple(row): idx for idx, row in applied_df.loc[:, KEY_COLS].iterrows()}

    for _, row in rows_to_apply.iterrows():
        key = key_tuple_from_row(row)
        if key not in key_to_index:
            raise SystemExit(f"ready row not found in canonical strict-case universe: {key}")
        idx = key_to_index[key]
        candidate_validity_value = normalize_text(row.get("candidate_validity_merged", "")) or normalize_text(
            row.get("candidate_validity_proposed", "")
        )
        date_judgement_value = normalize_text(row.get("date_judgement_merged", "")) or normalize_text(
            row.get("date_judgement_proposed", "")
        )
        note_value = normalize_text(row.get("note_merged", "")) or normalize_text(row.get("note_proposed", ""))
        if candidate_validity_value:
            applied_df.at[idx, "candidate_validity"] = candidate_validity_value
        if date_judgement_value:
            applied_df.at[idx, "date_judgement"] = date_judgement_value
        if note_value:
            applied_df.at[idx, "note"] = note_value
    return applied_df


def build_changed_cases_output(
    current_joined: pd.DataFrame,
    scenario_joined_map: dict[str, pd.DataFrame],
    ready_context: pd.DataFrame,
    gate_keys: set[tuple[str, str, str]],
) -> pd.DataFrame:
    current_base = current_joined.loc[:, [*KEY_COLS, "candidate_validity", "vendor_reply_class", "vendor_fault_family", "actionability_v3"]].copy()
    current_base = current_base.rename(columns={"candidate_validity": "candidate_validity_current"})
    ready_min = ready_context.loc[
        :,
        [*KEY_COLS, "candidate_validity_proposed", "vendor_reply_class", "vendor_fault_family", "actionability_v3", "change_class"],
    ].copy()
    ready_min = ready_min.rename(
        columns={
            "vendor_reply_class": "vendor_reply_class_ready",
            "vendor_fault_family": "vendor_fault_family_ready",
            "actionability_v3": "actionability_v3_ready",
        }
    )

    changed_rows: list[dict[str, object]] = []
    for scenario in ("safe_same_label_only", "full_ready_rows"):
        scenario_joined = scenario_joined_map[scenario]
        scenario_base = scenario_joined.loc[:, [*KEY_COLS, "candidate_validity"]].copy()
        scenario_base = scenario_base.rename(columns={"candidate_validity": "candidate_validity_scenario"})
        compare_df = current_base.merge(scenario_base, on=KEY_COLS, how="inner")
        compare_df = compare_df.merge(ready_min, on=KEY_COLS, how="left")
        compare_df = compare_df.loc[compare_df["candidate_validity_proposed"].fillna("").ne("")].copy()

        for truth_mode in ("strict", "lenient"):
            for _, row in compare_df.iterrows():
                current_truth_source = "manual_truth" if normalize_text(row["candidate_validity_current"]) else ("vendor_truth" if normalize_text(row["vendor_reply_class"]) else "")
                scenario_truth_source = "manual_truth" if normalize_text(row["candidate_validity_scenario"]) else ("vendor_truth" if normalize_text(row["vendor_reply_class"]) else "")

                from evaluate_full_algorithm_f1_v3 import hybrid_truth_label  # local import keeps module dependency narrow

                current_truth_label = hybrid_truth_label(row["candidate_validity_current"], row["vendor_reply_class"], truth_mode)
                scenario_truth_label = hybrid_truth_label(row["candidate_validity_scenario"], row["vendor_reply_class"], truth_mode)
                if current_truth_source == scenario_truth_source and current_truth_label == scenario_truth_label:
                    continue

                key = (row["site"], row["panel_id"], row["strict_trigger_date"])
                change_type = "strict_label_changed_requires_gate" if key in gate_keys else "no_label_change_manualized"

                changed_rows.append(
                    {
                        "scenario": scenario,
                        "site": row["site"],
                        "panel_id": row["panel_id"],
                        "strict_trigger_date": row["strict_trigger_date"],
                        "truth_mode": truth_mode,
                        "current_truth_source": current_truth_source,
                        "current_truth_label": current_truth_label,
                        "scenario_truth_source": scenario_truth_source,
                        "scenario_truth_label": scenario_truth_label,
                        "candidate_validity_proposed": normalize_text(row["candidate_validity_proposed"]),
                        "vendor_reply_class": coalesce_text(row["vendor_reply_class_ready"], row["vendor_reply_class"]),
                        "vendor_fault_family": coalesce_text(row["vendor_fault_family_ready"], row["vendor_fault_family"]),
                        "actionability_v3": normalize_text(row["actionability_v3_ready"]),
                        "scenario_change_type": change_type,
                    }
                )

    changed_df = pd.DataFrame(changed_rows, columns=CHANGED_CASE_COLS)
    if changed_df.empty:
        return changed_df
    return changed_df.sort_values(["scenario", "truth_mode", "site", "strict_trigger_date", "panel_id"]).reset_index(drop=True)


def build_summary(
    scenario_metrics: dict[str, pd.DataFrame],
    ready_unique_case_count: int,
    safe_same_label_case_count: int,
    gate_review_case_count: int,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for scenario in SCENARIOS:
        metric_df = scenario_metrics[scenario]
        for _, row in metric_df.iterrows():
            rows.append(
                {
                    "scenario": scenario,
                    "ready_unique_case_count": ready_unique_case_count,
                    "safe_same_label_case_count": safe_same_label_case_count,
                    "gate_review_case_count": gate_review_case_count,
                    "truth_mode": row["truth_mode"],
                    "prediction_mode": row["prediction_mode"],
                    "source_split": row["source_split"],
                    "tp": int(row["tp"]),
                    "fp": int(row["fp"]),
                    "fn": int(row["fn"]),
                    "tn": int(row["tn"]),
                    "precision": row["precision"],
                    "recall": row["recall"],
                    "f1": row["f1"],
                    "excluded_rows": int(row["excluded_rows"]),
                    "scored_rows": int(row["scored_rows"]),
                    "manual_truth_present_count": int(row["manual_truth_present_count"]),
                    "vendor_truth_used_count": int(row["vendor_truth_used_count"]),
                }
            )
    return pd.DataFrame(rows, columns=SUMMARY_COLS).sort_values(
        ["scenario", "truth_mode", "prediction_mode", "source_split"]
    ).reset_index(drop=True)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    canonical_df = read_csv(root / "_share" / "panel_date_reaudit_working.csv")
    ensure_columns(canonical_df, REAUDIT_REQUIRED_COLS, "panel_date_reaudit_working.csv")
    for col in ["site", "panel_id"]:
        canonical_df[col] = canonical_df[col].map(normalize_text)
    canonical_df["strict_trigger_date"] = canonical_df["strict_trigger_date"].map(normalize_date)
    for col in ["candidate_validity", "date_judgement", "note", "vendor_reply_class", "vendor_fault_family"]:
        if col in canonical_df.columns:
            canonical_df[col] = canonical_df[col].map(normalize_text)
    canonical_df = ensure_unique(canonical_df, "panel_date_reaudit_working.csv", KEY_COLS)

    ready_df = load_ready_rows(root)
    changed_df = load_changed_case_context(root)
    ready_context, gate_context = build_ready_context(root, ready_df, changed_df)

    gate_keys = set(gate_context.loc[:, KEY_COLS].itertuples(index=False, name=None))
    safe_context = ready_context.loc[~ready_context.apply(key_tuple_from_row, axis=1).isin(gate_keys)].copy()
    safe_context = safe_context.loc[:, SAFE_ROW_COLS].sort_values(KEY_COLS).reset_index(drop=True)
    gate_output_df = gate_context.loc[:, GATE_ROW_COLS].copy().sort_values(KEY_COLS).reset_index(drop=True)

    current_truth_df = canonical_df.copy()
    safe_truth_df = apply_ready_rows(canonical_df, ready_context.loc[ready_context["change_class"].eq("safe_same_label_copyback")])
    full_truth_df = apply_ready_rows(canonical_df, ready_df)

    current_joined = build_joined_for_truth_df(root=root, truth_df=current_truth_df)
    safe_joined = build_joined_for_truth_df(root=root, truth_df=safe_truth_df)
    full_joined = build_joined_for_truth_df(root=root, truth_df=full_truth_df)

    scenario_metrics = {
        "current_canonical": evaluate_state(current_joined),
        "safe_same_label_only": evaluate_state(safe_joined),
        "full_ready_rows": evaluate_state(full_joined),
    }
    summary_df = build_summary(
        scenario_metrics=scenario_metrics,
        ready_unique_case_count=int(len(ready_df)),
        safe_same_label_case_count=int(len(safe_context)),
        gate_review_case_count=int(len(gate_output_df)),
    )
    changed_cases_df = build_changed_cases_output(
        current_joined=current_joined,
        scenario_joined_map={"safe_same_label_only": safe_joined, "full_ready_rows": full_joined},
        ready_context=ready_context,
        gate_keys=gate_keys,
    )

    out_dir = root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(out_dir / "truth_seed_promotion_scenarios_summary_v1.csv", index=False, encoding="utf-8-sig")
    safe_context.to_csv(out_dir / "truth_seed_safe_apply_rows_v1.csv", index=False, encoding="utf-8-sig")
    gate_output_df.to_csv(out_dir / "truth_seed_gate_review_rows_v1.csv", index=False, encoding="utf-8-sig")
    changed_cases_df.to_csv(out_dir / "truth_seed_promotion_changed_cases_v1.csv", index=False, encoding="utf-8-sig")
    print(f"truth_seed_promotion_ready_cases_v1={len(ready_df)}")


if __name__ == "__main__":
    main()
