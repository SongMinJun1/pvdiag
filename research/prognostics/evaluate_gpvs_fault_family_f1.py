#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ("conalog", "gangui", "ktc_ess", "sinhyo")
TRUTH_LABELS = [
    "electrical_fault_like",
    "open_or_device_issue_like",
    "group_or_inverter_side_like",
    "none_visible",
]
PRED_LABELS_CLOSED = TRUTH_LABELS + ["uncertain"]

VENDOR_REQUIRED_COLS = [
    "site",
    "panel_id",
    "vendor_reply_class",
    "vendor_fault_family",
    "vendor_note",
    "strict_trigger_date",
]
V3_REQUIRED_COLS = [
    "site",
    "panel_id",
    "critical_phenotype_v3",
]
ONSET_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "retrospective_onset_date",
]
CORE_REQUIRED_COLS = [
    "date",
    "panel_id",
    "mid_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "v_drop",
]
EVAL_CASE_COLS = [
    "site",
    "panel_id",
    "truth_fault_family",
    "pred_fault_family",
    "vendor_reply_class",
    "vendor_fault_family",
    "strict_trigger_date",
    "retrospective_onset_date",
    "prediction_source",
    "fallback_group_proxy",
    "same_group_zero_like_count",
    "same_site_zero_like_count",
    "fallback_rule_used",
    "error_type",
    "vendor_note",
]
SUMMARY_COLS = [
    "evaluation_mode",
    "row_type",
    "class_label",
    "macro_f1",
    "weighted_f1",
    "accuracy",
    "coverage",
    "precision",
    "recall",
    "f1",
    "support",
    "scored_rows",
    "eligible_truth_rows",
    "excluded_truth_rows",
    "excluded_uncertain_rows",
]
CONFUSION_COLS = [
    "evaluation_mode",
    "truth_fault_family",
    "pred_fault_family",
    "row_count",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate GPVS-derived fault-family classification on vendor-adjudicated rows."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to project root.",
    )
    parser.add_argument(
        "--sites",
        nargs="*",
        default=list(SITES),
        help="Sites to inspect for panel_day_core fallback. Defaults to conalog/gangui/ktc_ess/sinhyo.",
    )
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text


def normalize_date(value: object) -> str:
    text = normalize_text(value)
    return text[:10] if len(text) >= 10 else text


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def safe_rate(numer: float, denom: float) -> float:
    if denom <= 0:
        return 0.0
    return round(float(numer / denom), 6)


def truth_fault_family(vendor_fault_family: object) -> str:
    value = normalize_text(vendor_fault_family)
    mapping = {
        "diode_like": "electrical_fault_like",
        "module_damage_like": "electrical_fault_like",
        "open_or_device_issue_like": "open_or_device_issue_like",
        "group_or_inverter_side_like": "group_or_inverter_side_like",
        "none_visible": "none_visible",
    }
    return mapping.get(value, "")


def pred_fault_family_from_v3(critical_phenotype_v3: object) -> str:
    value = normalize_text(critical_phenotype_v3)
    mapping = {
        "electrical_fault_like": "electrical_fault_like",
        "open_or_device_issue_like": "open_or_device_issue_like",
        "group_or_inverter_side_like": "group_or_inverter_side_like",
        "common_cause_borderline": "group_or_inverter_side_like",
        "shape_only_monitor": "none_visible",
        "singleton_borderline_review": "uncertain",
        "weak_critical_candidate": "uncertain",
    }
    return mapping.get(value, "uncertain")


def group_proxy_from_panel_id(panel_id: object) -> str:
    value = normalize_text(panel_id)
    parts = value.split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return value


def to_float(value: object) -> float:
    return float(pd.to_numeric(value, errors="coerce"))


def to_int(value: object) -> int:
    coerced = pd.to_numeric(value, errors="coerce")
    if pd.isna(coerced):
        return 0
    return int(coerced)


def coverage_floor_value(row: pd.Series) -> float:
    for col in ["coverage_mid", "coverage"]:
        if col in row.index:
            value = to_float(row.get(col))
            if pd.notna(value):
                return value
    return float("nan")


def is_zero_like_day(row: pd.Series | None) -> bool:
    if row is None:
        return False
    mid_ratio = to_float(row.get("mid_ratio"))
    mid_i_ratio = to_float(row.get("mid_i_ratio"))
    coverage_value = coverage_floor_value(row)
    return (
        pd.notna(mid_ratio)
        and pd.notna(mid_i_ratio)
        and pd.notna(coverage_value)
        and mid_ratio <= 0.10
        and mid_i_ratio <= 0.10
        and coverage_value >= 0.50
    )


def infer_fault_family_from_core(core_row: pd.Series | None) -> tuple[str, str, int, int, str]:
    if core_row is None:
        return ("uncertain", "", 0, 0, "missing_core_row")

    mid_ratio = to_float(core_row.get("mid_ratio"))
    mid_v_ratio = to_float(core_row.get("mid_v_ratio"))
    mid_i_ratio = to_float(core_row.get("mid_i_ratio"))
    v_drop = to_float(core_row.get("v_drop"))
    zero_like = is_zero_like_day(core_row)
    group_proxy = normalize_text(core_row.get("fallback_group_proxy", ""))
    same_group_zero_like_count = to_int(core_row.get("same_group_zero_like_count"))
    same_site_zero_like_count = to_int(core_row.get("same_site_zero_like_count"))
    collapse_evidence = same_group_zero_like_count >= 2 or same_site_zero_like_count >= 3
    open_candidate = (
        pd.notna(mid_ratio)
        and pd.notna(mid_v_ratio)
        and pd.notna(v_drop)
        and mid_ratio <= 0.10
        and mid_v_ratio <= 0.10
        and v_drop >= 0.90
    )

    if zero_like and collapse_evidence:
        return (
            "group_or_inverter_side_like",
            group_proxy,
            same_group_zero_like_count,
            same_site_zero_like_count,
            "same_day_group_collapse",
        )

    if open_candidate and collapse_evidence:
        return (
            "group_or_inverter_side_like",
            group_proxy,
            same_group_zero_like_count,
            same_site_zero_like_count,
            "collapse_overrides_open_device",
        )

    if zero_like:
        return (
            "open_or_device_issue_like",
            group_proxy,
            same_group_zero_like_count,
            same_site_zero_like_count,
            "isolated_zero_like_open_device",
        )

    if open_candidate:
        return (
            "open_or_device_issue_like",
            group_proxy,
            same_group_zero_like_count,
            same_site_zero_like_count,
            "legacy_open_device",
        )

    if pd.notna(mid_ratio) and pd.notna(mid_i_ratio) and pd.notna(mid_v_ratio):
        if mid_ratio <= 0.10 and mid_i_ratio <= 0.10 and mid_v_ratio >= 1.05:
            return (
                "group_or_inverter_side_like",
                group_proxy,
                same_group_zero_like_count,
                same_site_zero_like_count,
                "legacy_group_or_inverter",
            )

    return (
        "uncertain",
        group_proxy,
        same_group_zero_like_count,
        same_site_zero_like_count,
        "legacy_uncertain",
    )


def error_type(truth_label: str, pred_label: str) -> str:
    if not truth_label:
        return "excluded_truth"
    if pred_label == truth_label:
        return "correct"
    if pred_label == "uncertain":
        return "abstain_uncertain"
    return "misclassified"


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def load_core_lookup(root: Path, sites: list[str]) -> dict[tuple[str, str, str], pd.Series]:
    lookup: dict[tuple[str, str, str], pd.Series] = {}
    for site in sites:
        path = root / "data" / site / "out" / "panel_day_core.csv"
        if not path.exists():
            continue
        df = read_csv(path)
        ensure_columns(df, CORE_REQUIRED_COLS, str(path))
        df["site"] = site
        df["panel_id"] = df["panel_id"].map(normalize_text)
        df["date"] = df["date"].map(normalize_date)
        if "group_key_base" in df.columns:
            df["group_key_base"] = df["group_key_base"].map(normalize_text)
        df["fallback_group_proxy"] = df.apply(
            lambda row: normalize_text(row.get("group_key_base", "")) or group_proxy_from_panel_id(row.get("panel_id", "")),
            axis=1,
        )
        for coverage_col in ["coverage_mid", "coverage"]:
            if coverage_col in df.columns:
                df[coverage_col] = pd.to_numeric(df[coverage_col], errors="coerce")
        for metric_col in ["mid_ratio", "mid_v_ratio", "mid_i_ratio", "v_drop"]:
            df[metric_col] = pd.to_numeric(df[metric_col], errors="coerce")
        df["zero_like_day"] = df.apply(is_zero_like_day, axis=1)
        df["same_site_zero_like_count"] = (
            df.groupby(["site", "date"])["zero_like_day"].transform("sum").astype(int)
        )
        df["same_group_zero_like_count"] = (
            df.groupby(["site", "date", "fallback_group_proxy"])["zero_like_day"].transform("sum").astype(int)
        )
        keep_cols = ["site"] + CORE_REQUIRED_COLS + [
            col
            for col in [
                "group_key_base",
                "coverage_mid",
                "coverage",
                "fallback_group_proxy",
                "same_group_zero_like_count",
                "same_site_zero_like_count",
            ]
            if col in df.columns
        ]
        for row in df.loc[:, keep_cols].itertuples(index=False):
            key = (normalize_text(getattr(row, "site")), normalize_text(getattr(row, "panel_id")), normalize_date(getattr(row, "date")))
            if key not in lookup:
                lookup[key] = pd.Series(row._asdict())
    return lookup


def build_eval_cases(root: Path, sites: list[str]) -> pd.DataFrame:
    vendor_df = read_csv(root / "_share" / "vendor_reply_adjudication_latest.csv")
    v3_df = read_csv(root / "_share" / "critical_actionability_shadow_v3_latest.csv")
    onset_df = read_csv(root / "_share" / "panel_onset_shadow_latest.csv")

    ensure_columns(vendor_df, VENDOR_REQUIRED_COLS, "vendor_reply_adjudication_latest.csv")
    ensure_columns(v3_df, V3_REQUIRED_COLS, "critical_actionability_shadow_v3_latest.csv")
    ensure_columns(onset_df, ONSET_REQUIRED_COLS, "panel_onset_shadow_latest.csv")

    for df in [vendor_df, v3_df, onset_df]:
        for col in ["site", "panel_id"]:
            df[col] = df[col].map(normalize_text)

    for col in ["vendor_reply_class", "vendor_fault_family", "vendor_note"]:
        vendor_df[col] = vendor_df[col].map(normalize_text)
    for col in ["strict_trigger_date", "retrospective_onset_date"]:
        if col in vendor_df.columns:
            vendor_df[col] = vendor_df[col].map(normalize_date)
        onset_df[col] = onset_df[col].map(normalize_date)
    if "strict_trigger_date" in v3_df.columns:
        v3_df["strict_trigger_date"] = v3_df["strict_trigger_date"].map(normalize_date)
    v3_df["critical_phenotype_v3"] = v3_df["critical_phenotype_v3"].map(normalize_text)

    v3_lookup = (
        v3_df.loc[:, ["site", "panel_id", "critical_phenotype_v3"]]
        .drop_duplicates(subset=["site", "panel_id"])
        .set_index(["site", "panel_id"])
        .to_dict("index")
    )
    onset_lookup = (
        onset_df.loc[:, ["site", "panel_id", "strict_trigger_date", "retrospective_onset_date"]]
        .drop_duplicates(subset=["site", "panel_id"])
        .set_index(["site", "panel_id"])
        .to_dict("index")
    )
    core_lookup = load_core_lookup(root, sites)

    rows: list[dict[str, object]] = []
    for row in vendor_df.itertuples(index=False):
        key = (row.site, row.panel_id)
        truth_label = truth_fault_family(row.vendor_fault_family)
        onset_row = onset_lookup.get(key)
        strict_trigger_date = normalize_date(getattr(row, "strict_trigger_date", ""))
        retrospective_onset_date = ""
        if onset_row is not None:
            strict_trigger_date = normalize_date(onset_row.get("strict_trigger_date", strict_trigger_date)) or strict_trigger_date
            retrospective_onset_date = normalize_date(onset_row.get("retrospective_onset_date", ""))

        if key in v3_lookup:
            pred_label = pred_fault_family_from_v3(v3_lookup[key].get("critical_phenotype_v3", ""))
            prediction_source = "critical_phenotype_v3"
            fallback_group_proxy = ""
            same_group_zero_like_count = 0
            same_site_zero_like_count = 0
            fallback_rule_used = "resolved_by_critical_phenotype_v3"
        else:
            core_row = core_lookup.get((row.site, row.panel_id, strict_trigger_date))
            (
                pred_label,
                fallback_group_proxy,
                same_group_zero_like_count,
                same_site_zero_like_count,
                fallback_rule_used,
            ) = infer_fault_family_from_core(core_row)
            prediction_source = "strict_day_core_fallback" if core_row is not None else "missing_core_fallback"

        rows.append(
            {
                "site": row.site,
                "panel_id": row.panel_id,
                "truth_fault_family": truth_label,
                "pred_fault_family": pred_label,
                "vendor_reply_class": row.vendor_reply_class,
                "vendor_fault_family": row.vendor_fault_family,
                "strict_trigger_date": strict_trigger_date,
                "retrospective_onset_date": retrospective_onset_date,
                "prediction_source": prediction_source,
                "fallback_group_proxy": fallback_group_proxy,
                "same_group_zero_like_count": same_group_zero_like_count,
                "same_site_zero_like_count": same_site_zero_like_count,
                "fallback_rule_used": fallback_rule_used,
                "error_type": error_type(truth_label, pred_label),
                "vendor_note": row.vendor_note,
            }
        )

    return pd.DataFrame(rows, columns=EVAL_CASE_COLS)


def compute_metrics(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_rows: list[dict[str, object]] = []
    confusion_rows: list[dict[str, object]] = []

    eligible = df.loc[df["truth_fault_family"].ne("")].copy()
    excluded_truth_rows = int(df["truth_fault_family"].eq("").sum())

    for evaluation_mode in ["closed_world", "abstaining"]:
        if evaluation_mode == "closed_world":
            scored = eligible.copy()
            excluded_uncertain_rows = 0
            coverage = 1.0 if len(eligible) > 0 else 0.0
            pred_labels = PRED_LABELS_CLOSED
        else:
            scored = eligible.loc[eligible["pred_fault_family"].ne("uncertain")].copy()
            excluded_uncertain_rows = int(eligible["pred_fault_family"].eq("uncertain").sum())
            coverage = safe_rate(len(scored), len(eligible))
            pred_labels = TRUTH_LABELS

        scored_rows = len(scored)
        per_class_f1: list[float] = []
        weighted_num = 0.0

        for class_label in TRUTH_LABELS:
            tp = int(((scored["truth_fault_family"] == class_label) & (scored["pred_fault_family"] == class_label)).sum())
            fp = int(((scored["truth_fault_family"] != class_label) & (scored["pred_fault_family"] == class_label)).sum())
            fn = int(((scored["truth_fault_family"] == class_label) & (scored["pred_fault_family"] != class_label)).sum())
            support = int((scored["truth_fault_family"] == class_label).sum())

            precision = safe_rate(tp, tp + fp)
            recall = safe_rate(tp, tp + fn)
            f1 = safe_rate(2 * precision * recall, precision + recall) if (precision + recall) > 0 else 0.0

            per_class_f1.append(f1)
            weighted_num += f1 * support
            summary_rows.append(
                {
                    "evaluation_mode": evaluation_mode,
                    "row_type": "class",
                    "class_label": class_label,
                    "macro_f1": "",
                    "weighted_f1": "",
                    "accuracy": "",
                    "coverage": "",
                    "precision": precision,
                    "recall": recall,
                    "f1": f1,
                    "support": support,
                    "scored_rows": scored_rows,
                    "eligible_truth_rows": len(eligible),
                    "excluded_truth_rows": excluded_truth_rows,
                    "excluded_uncertain_rows": excluded_uncertain_rows,
                }
            )

        accuracy = safe_rate(int((scored["truth_fault_family"] == scored["pred_fault_family"]).sum()), scored_rows)
        macro_f1 = round(sum(per_class_f1) / len(TRUTH_LABELS), 6) if TRUTH_LABELS else 0.0
        weighted_f1 = safe_rate(weighted_num, int(scored["truth_fault_family"].isin(TRUTH_LABELS).sum()))
        summary_rows.append(
            {
                "evaluation_mode": evaluation_mode,
                "row_type": "overall",
                "class_label": "",
                "macro_f1": macro_f1,
                "weighted_f1": weighted_f1,
                "accuracy": accuracy,
                "coverage": coverage,
                "precision": "",
                "recall": "",
                "f1": "",
                "support": int(scored["truth_fault_family"].isin(TRUTH_LABELS).sum()),
                "scored_rows": scored_rows,
                "eligible_truth_rows": len(eligible),
                "excluded_truth_rows": excluded_truth_rows,
                "excluded_uncertain_rows": excluded_uncertain_rows,
            }
        )

        for truth_label in TRUTH_LABELS:
            for pred_label in pred_labels:
                confusion_rows.append(
                    {
                        "evaluation_mode": evaluation_mode,
                        "truth_fault_family": truth_label,
                        "pred_fault_family": pred_label,
                        "row_count": int(
                            ((scored["truth_fault_family"] == truth_label) & (scored["pred_fault_family"] == pred_label)).sum()
                        ),
                    }
                )

    return (
        pd.DataFrame(summary_rows, columns=SUMMARY_COLS),
        pd.DataFrame(confusion_rows, columns=CONFUSION_COLS),
    )


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"

    eval_cases_df = build_eval_cases(root, [normalize_text(site) for site in args.sites if normalize_text(site)])
    summary_df, confusion_df = compute_metrics(eval_cases_df)

    eval_cases_df.to_csv(share_dir / "gpvs_fault_family_eval_cases.csv", index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / "gpvs_fault_family_f1_summary.csv", index=False, encoding="utf-8-sig")
    confusion_df.to_csv(share_dir / "gpvs_fault_family_confusion.csv", index=False, encoding="utf-8-sig")

    print(f"gpvs_fault_family_eval_rows={len(eval_cases_df)}")


if __name__ == "__main__":
    main()
