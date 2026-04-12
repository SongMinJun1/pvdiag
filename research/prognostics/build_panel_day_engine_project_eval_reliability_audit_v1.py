#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd

EVAL_MATRIX_NAME = "panel_day_engine_project_eval_matrix_v1.csv"
EVAL_SUMMARY_NAME = "panel_day_engine_project_eval_matrix_summary_v1.csv"
EVAL_NOTES_NAME = "panel_day_engine_project_eval_notes_v1.csv"

RELIABILITY_OUTPUT_NAME = "panel_day_engine_project_eval_reliability_v1.csv"
RELIABILITY_SUMMARY_OUTPUT_NAME = "panel_day_engine_project_eval_reliability_summary_v1.csv"
FREEZE_CANDIDATES_OUTPUT_NAME = "panel_day_engine_project_eval_freeze_candidates_v1.csv"

RELIABILITY_COLS = [
    "eval_scope",
    "target_name",
    "metric_kind",
    "positive_support",
    "negative_support",
    "predicted_positive_support",
    "recall",
    "precision",
    "f1",
    "recall_ci_low",
    "recall_ci_high",
    "precision_ci_low",
    "precision_ci_high",
    "reliability_class",
    "freeze_recommendation",
    "reliability_reason_ko",
]

RELIABILITY_SUMMARY_COLS = [
    "eval_scope",
    "target_count",
    "structural_only_count",
    "underpowered_count",
    "low_support_count",
    "provisional_count",
    "proxy_only_count",
    "freeze_as_current_default_count",
    "freeze_with_caution_count",
    "do_not_freeze_count",
    "note_ko",
]

FREEZE_CANDIDATES_COLS = [
    "eval_scope",
    "recommended_target_name",
    "recommended_metric_kind",
    "recommended_f1",
    "recommended_positive_support",
    "recommended_reliability_class",
    "recommended_freeze_recommendation",
    "rationale_ko",
]

FREEZE_RANK = {
    "freeze_as_current_default": 2,
    "freeze_with_caution": 1,
    "do_not_freeze": 0,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit the reliability and freeze-readiness of the integrated project evaluation matrix."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to the project root.",
    )
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def numeric_int(value: object) -> int:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0 if pd.isna(numeric) else int(numeric)


def numeric_float_or_blank(value: object) -> float | None:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return None if pd.isna(numeric) else float(numeric)


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float | None, float | None]:
    if total <= 0:
        return (None, None)
    phat = successes / total
    z2 = z * z
    denom = 1.0 + (z2 / total)
    center = (phat + (z2 / (2.0 * total))) / denom
    margin = (z / denom) * math.sqrt((phat * (1.0 - phat) / total) + (z2 / (4.0 * total * total)))
    return (max(0.0, center - margin), min(1.0, center + margin))


def classify_row(metric_kind: str, positive_support: int) -> tuple[str, str]:
    if metric_kind == "structural_coverage_metric":
        return ("structural_only", "freeze_with_caution")
    if metric_kind == "retrospective_proxy_metric":
        return ("proxy_only", "freeze_with_caution")
    if positive_support < 5:
        return ("underpowered", "do_not_freeze")
    if positive_support < 10:
        return ("low_support", "freeze_with_caution")
    return ("provisional", "freeze_as_current_default")


def reliability_reason(
    *,
    eval_scope: str,
    metric_kind: str,
    reliability_class: str,
    positive_support: int,
    recall: float | None,
    precision: float | None,
    recall_ci_low: float | None,
    recall_ci_high: float | None,
    precision_ci_low: float | None,
    precision_ci_high: float | None,
) -> str:
    if metric_kind == "structural_coverage_metric":
        return "structural coverage row라 classifier metric이 아니며 support 해석만 가능하므로 freeze는 caution 수준이 적절하다."
    if metric_kind == "retrospective_proxy_metric":
        return "retrospective proxy metric이라 workflow 비교에는 유용하지만 prospective default 성능으로 과장할 수 없어 freeze는 caution 수준으로 제한한다."

    if reliability_class == "underpowered":
        reason = (
            f"positive support가 {positive_support}건으로 너무 작아 수치가 좋아도 불안정하다. "
            "작은 support에서는 perfect F1도 쉽게 과장될 수 있어 현재 conclusion freeze는 권하지 않는다."
        )
        if eval_scope == "step4_abrupt_no_precursor":
            reason += " precursor-abrupt same-event overlap 2건은 precursor-led fault with abrupt ending으로 재분류되어 pure abrupt support에서 제외됐고, c42997a6-5881-47e7-9035-7de8a2673b54.1.1 은 precursor-like evidence before trigger 때문에 pure abrupt typing holdout 으로 제외된 상태다."
        return reason
    if reliability_class == "low_support":
        reason = (
            f"positive support가 {positive_support}건으로 아직 작아 interval 해석이 필요하다. "
            "현 시점 기본값으로는 참고 가능하지만 freeze는 caution 수준이 적절하다."
        )
        if eval_scope == "step4_abrupt_no_precursor":
            reason += " 이 support는 overlap precursor-led abrupt ending panel과 c42997a6-5881-47e7-9035-7de8a2673b54.1.1 holdout을 제외한 pure abrupt 기준으로 읽어야 한다."
        return reason
    recall_text = "" if recall is None else f"recall={recall:.3f}"
    precision_text = "" if precision is None else f"precision={precision:.3f}"
    recall_ci_text = "" if recall_ci_low is None else f"recall CI=({recall_ci_low:.3f},{recall_ci_high:.3f})"
    precision_ci_text = "" if precision_ci_low is None else f"precision CI=({precision_ci_low:.3f},{precision_ci_high:.3f})"
    return (
        f"positive support가 {positive_support}건으로 provisional 수준이며 {recall_text} {precision_text} "
        f"{recall_ci_text} {precision_ci_text}를 함께 보고 current default로 freeze할 수 있다."
    ).strip()


def build_reliability_rows(matrix_df: pd.DataFrame, notes_df: pd.DataFrame) -> pd.DataFrame:
    matrix_df = matrix_df.copy()
    matrix_df["eval_scope"] = matrix_df["eval_scope"].map(normalize_text)
    matrix_df["target_name"] = matrix_df["target_name"].map(normalize_text)
    matrix_df["metric_kind"] = matrix_df["metric_kind"].map(normalize_text)

    note_map = {
        normalize_text(row["eval_scope"]): normalize_text(row["caveat_ko"])
        for _, row in notes_df.iterrows()
    }

    rows: list[dict[str, object]] = []
    for row in matrix_df.to_dict(orient="records"):
        metric_kind = normalize_text(row["metric_kind"])
        eval_scope = normalize_text(row["eval_scope"])
        target_name = normalize_text(row["target_name"])

        if metric_kind == "structural_coverage_metric":
            positive_support = numeric_int(row.get("support_positive"))
            negative_support = ""
            predicted_positive_support = ""
            recall = None
            precision = None
            f1 = None
            recall_ci_low = None
            recall_ci_high = None
            precision_ci_low = None
            precision_ci_high = None
        else:
            tp = numeric_int(row.get("tp"))
            fp = numeric_int(row.get("fp"))
            fn = numeric_int(row.get("fn"))
            tn = numeric_int(row.get("tn"))
            positive_support = tp + fn
            negative_support = fp + tn
            predicted_positive_support = tp + fp
            recall = numeric_float_or_blank(row.get("recall"))
            precision = numeric_float_or_blank(row.get("precision"))
            f1 = numeric_float_or_blank(row.get("f1"))
            recall_ci_low, recall_ci_high = wilson_interval(tp, positive_support)
            precision_ci_low, precision_ci_high = wilson_interval(tp, predicted_positive_support)

        reliability_class, freeze_recommendation = classify_row(metric_kind, int(positive_support) if positive_support != "" else 0)
        reason = reliability_reason(
            eval_scope=eval_scope,
            metric_kind=metric_kind,
            reliability_class=reliability_class,
            positive_support=int(positive_support) if positive_support != "" else 0,
            recall=recall,
            precision=precision,
            recall_ci_low=recall_ci_low,
            recall_ci_high=recall_ci_high,
            precision_ci_low=precision_ci_low,
            precision_ci_high=precision_ci_high,
        )
        caveat = note_map.get(eval_scope, "")
        reliability_reason_ko = f"{reason} {caveat}".strip()
        rows.append(
            {
                "eval_scope": eval_scope,
                "target_name": target_name,
                "metric_kind": metric_kind,
                "positive_support": positive_support,
                "negative_support": negative_support,
                "predicted_positive_support": predicted_positive_support,
                "recall": "" if recall is None else recall,
                "precision": "" if precision is None else precision,
                "f1": "" if f1 is None else f1,
                "recall_ci_low": "" if recall_ci_low is None else recall_ci_low,
                "recall_ci_high": "" if recall_ci_high is None else recall_ci_high,
                "precision_ci_low": "" if precision_ci_low is None else precision_ci_low,
                "precision_ci_high": "" if precision_ci_high is None else precision_ci_high,
                "reliability_class": reliability_class,
                "freeze_recommendation": freeze_recommendation,
                "reliability_reason_ko": reliability_reason_ko,
            }
        )
    return pd.DataFrame(rows, columns=RELIABILITY_COLS)


def build_summary_rows(reliability_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for eval_scope, scope_df in reliability_df.groupby("eval_scope", dropna=False):
        eval_scope = normalize_text(eval_scope)
        target_count = int(len(scope_df))
        counts = scope_df["reliability_class"].value_counts().to_dict()
        freeze_counts = scope_df["freeze_recommendation"].value_counts().to_dict()
        structural_only_count = int(counts.get("structural_only", 0))
        underpowered_count = int(counts.get("underpowered", 0))
        low_support_count = int(counts.get("low_support", 0))
        provisional_count = int(counts.get("provisional", 0))
        proxy_only_count = int(counts.get("proxy_only", 0))
        freeze_as_current_default_count = int(freeze_counts.get("freeze_as_current_default", 0))
        freeze_with_caution_count = int(freeze_counts.get("freeze_with_caution", 0))
        do_not_freeze_count = int(freeze_counts.get("do_not_freeze", 0))

        if structural_only_count == target_count:
            note_ko = "이 scope는 structural coverage row만 있어 분류기 freeze 판단이 아니라 support/coverage freeze만 caution 수준으로 본다."
        elif proxy_only_count == target_count:
            note_ko = "이 scope는 retrospective proxy row만 있어 workflow value proxy 해석은 가능하지만 classifier default처럼 freeze하면 안 된다."
        elif do_not_freeze_count == target_count:
            if eval_scope == "step4_abrupt_no_precursor":
                note_ko = "same-event overlap 2건을 precursor-led fault로 재분류하고 c42997a6-5881-47e7-9035-7de8a2673b54.1.1 holdout을 제외한 뒤 pure abrupt support가 3건으로 줄어 현재 scope row들이 underpowered 상태다."
            else:
                note_ko = "현재 scope row들이 모두 underpowered라 freeze를 보류하는 편이 안전하다."
        else:
            note_ko = "support 크기와 Wilson interval을 함께 보고 provisional/low_support row만 current default 후보로 읽어야 한다."

        rows.append(
            {
                "eval_scope": eval_scope,
                "target_count": target_count,
                "structural_only_count": structural_only_count,
                "underpowered_count": underpowered_count,
                "low_support_count": low_support_count,
                "provisional_count": provisional_count,
                "proxy_only_count": proxy_only_count,
                "freeze_as_current_default_count": freeze_as_current_default_count,
                "freeze_with_caution_count": freeze_with_caution_count,
                "do_not_freeze_count": do_not_freeze_count,
                "note_ko": note_ko,
            }
        )
    return pd.DataFrame(rows, columns=RELIABILITY_SUMMARY_COLS)


def build_freeze_candidates(reliability_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for eval_scope, scope_df in reliability_df.groupby("eval_scope", dropna=False):
        eval_scope = normalize_text(eval_scope)
        scope_df = scope_df.copy()
        scope_df["f1_numeric"] = pd.to_numeric(scope_df["f1"], errors="coerce")
        scope_df["positive_support_numeric"] = pd.to_numeric(scope_df["positive_support"], errors="coerce").fillna(0)
        scope_df["freeze_rank"] = scope_df["freeze_recommendation"].map(FREEZE_RANK).fillna(0).astype(int)

        if scope_df["metric_kind"].eq("structural_coverage_metric").all():
            rows.append(
                {
                    "eval_scope": eval_scope,
                    "recommended_target_name": "",
                    "recommended_metric_kind": "structural_coverage_metric",
                    "recommended_f1": "",
                    "recommended_positive_support": "",
                    "recommended_reliability_class": "structural_only",
                    "recommended_freeze_recommendation": "freeze_with_caution",
                    "rationale_ko": "이 scope는 coverage/support row만 있어 ordinary classifier target을 추천하지 않는다. 구조적 coverage 해석만 caution 수준으로 유지한다.",
                }
            )
            continue

        candidate_df = scope_df.loc[scope_df["freeze_recommendation"].ne("do_not_freeze")].copy()
        if candidate_df.empty:
            rows.append(
                {
                    "eval_scope": eval_scope,
                    "recommended_target_name": "",
                    "recommended_metric_kind": "",
                    "recommended_f1": "",
                    "recommended_positive_support": "",
                    "recommended_reliability_class": "",
                    "recommended_freeze_recommendation": "do_not_freeze",
                    "rationale_ko": "현재 scope에는 freeze_recommendation != do_not_freeze 인 row가 없어 freeze 후보를 권하지 않는다.",
                }
            )
            continue

        candidate_df = candidate_df.sort_values(
            ["freeze_rank", "f1_numeric", "positive_support_numeric", "target_name"],
            ascending=[False, False, False, True],
        ).reset_index(drop=True)
        best = candidate_df.iloc[0]
        rows.append(
            {
                "eval_scope": eval_scope,
                "recommended_target_name": normalize_text(best["target_name"]),
                "recommended_metric_kind": normalize_text(best["metric_kind"]),
                "recommended_f1": "" if pd.isna(best["f1_numeric"]) else float(best["f1_numeric"]),
                "recommended_positive_support": int(best["positive_support_numeric"]),
                "recommended_reliability_class": normalize_text(best["reliability_class"]),
                "recommended_freeze_recommendation": normalize_text(best["freeze_recommendation"]),
                "rationale_ko": (
                    f"freeze rank, f1, positive support 순으로 비교했을 때 {normalize_text(best['target_name'])} 가 현재 scope의 최상위 freeze 후보다."
                ),
            }
        )
    return pd.DataFrame(rows, columns=FREEZE_CANDIDATES_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    matrix_df = read_csv(share_dir / EVAL_MATRIX_NAME)
    summary_df = read_csv(share_dir / EVAL_SUMMARY_NAME)
    notes_df = read_csv(share_dir / EVAL_NOTES_NAME)

    ensure_columns(matrix_df, ["eval_scope", "target_name", "metric_kind", "tp", "fp", "fn", "tn", "recall", "precision", "f1", "support_positive"], EVAL_MATRIX_NAME)
    ensure_columns(summary_df, ["eval_scope", "best_target_name", "best_f1"], EVAL_SUMMARY_NAME)
    ensure_columns(notes_df, ["eval_scope", "why_prf_is_valid_or_not", "caveat_ko"], EVAL_NOTES_NAME)

    reliability_df = build_reliability_rows(matrix_df, notes_df)
    reliability_summary_df = build_summary_rows(reliability_df)
    freeze_candidates_df = build_freeze_candidates(reliability_df)

    reliability_df.to_csv(share_dir / RELIABILITY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    reliability_summary_df.to_csv(share_dir / RELIABILITY_SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    freeze_candidates_df.to_csv(share_dir / FREEZE_CANDIDATES_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
