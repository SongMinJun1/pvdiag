#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

FEATURE_TABLE_NAME = "panel_day_engine_run_feature_table_v1.csv"
LABEL_PACK_V2_NAME = "panel_day_engine_run_label_pack_v2.csv"
V0_SCORES_NAME = "panel_day_engine_run_ranker_v0_scores.csv"

CASES_OUTPUT_NAME = "panel_day_engine_run_ranker_reference_gap_cases_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_run_ranker_reference_gap_summary_v1.csv"

KEY_COLS = ["site", "panel_id", "run_start_date", "run_end_date"]
STRING_COLS = ["site", "panel_id", "run_start_date", "run_end_date", "run_shape_class", "cohort_hint"]
FOCUS_SCORE_NAME = "electrical_core_minus_broadshape_050"
LABELED_BUCKETS = {"positive_like", "negative_like"}
GAP_CLASS_ORDER = [
    "positive_top20_global",
    "positive_top50_global_not_top20",
    "positive_below_top50_global",
    "negative_top20_global",
    "negative_top50_global_not_top20",
    "negative_below_top50_global",
]

REQUIRED_FEATURE_TABLE_COLS = [
    *KEY_COLS,
    "run_day_count",
    "run_shape_class",
    "cohort_hint",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
]
REQUIRED_LABEL_PACK_COLS = [*KEY_COLS, "label_bucket_v2"]
REQUIRED_V0_SCORE_COLS = [*KEY_COLS, FOCUS_SCORE_NAME]

CASE_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "label_bucket_v2",
    "gap_class",
    FOCUS_SCORE_NAME,
    "global_score_rank",
    "site_score_rank",
    "run_day_count",
    "run_shape_class",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
    "reference_gap_reason_ko",
]
SUMMARY_COLS = [
    "summary_type",
    "gap_class",
    "run_count",
    "median_score",
    "median_global_score_rank",
    "median_site_score_rank",
    "median_run_day_count",
    "median_max_v_drop",
    "median_min_mid_v_ratio",
    "median_min_mid_ratio",
    "median_cond_evt_only_day_ratio",
    "median_ae_mid_or_hi_early_day_ratio",
    "median_mean_signal_count",
    "median_max_signal_count",
    "median_p95_recon_error",
    "recommended_next_direction",
    "note_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dissect the strengths and limits of the best deterministic run score."
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


def normalize_date(value: object) -> str:
    text = normalize_text(value)
    return text[:10] if len(text) >= 10 else text


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def drop_repeated_header_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    header_mask = pd.Series(True, index=df.index)
    for col in df.columns:
        header_mask &= df[col].map(normalize_text).eq(col)
    return df.loc[~header_mask].reset_index(drop=True)


def normalize_key_cols(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["site"] = out["site"].map(normalize_text)
    out["panel_id"] = out["panel_id"].map(normalize_text)
    out["run_start_date"] = out["run_start_date"].map(normalize_date)
    out["run_end_date"] = out["run_end_date"].map(normalize_date)
    return out


def load_feature_table(root: Path) -> pd.DataFrame:
    path = root / "_share" / FEATURE_TABLE_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_FEATURE_TABLE_COLS, path.name)
    df = normalize_key_cols(df)
    for col in REQUIRED_FEATURE_TABLE_COLS:
        if col in STRING_COLS:
            df[col] = df[col].map(normalize_text)
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.loc[:, REQUIRED_FEATURE_TABLE_COLS].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_label_pack_v2(root: Path) -> pd.DataFrame:
    path = root / "_share" / LABEL_PACK_V2_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_LABEL_PACK_COLS, path.name)
    df = normalize_key_cols(df)
    df["label_bucket_v2"] = df["label_bucket_v2"].map(normalize_text)
    return df.loc[:, REQUIRED_LABEL_PACK_COLS].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_v0_scores(root: Path) -> pd.DataFrame:
    path = root / "_share" / V0_SCORES_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_V0_SCORE_COLS, path.name)
    df = normalize_key_cols(df)
    df[FOCUS_SCORE_NAME] = pd.to_numeric(df[FOCUS_SCORE_NAME], errors="coerce")
    return df.loc[:, REQUIRED_V0_SCORE_COLS].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def build_rank_columns(full_df: pd.DataFrame) -> pd.DataFrame:
    ranked = full_df.sort_values(
        [FOCUS_SCORE_NAME, "run_day_count", "site", "panel_id", "run_start_date", "run_end_date"],
        ascending=[False, False, True, True, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    ranked["global_score_rank"] = range(1, len(ranked) + 1)

    site_ranked = full_df.sort_values(
        ["site", FOCUS_SCORE_NAME, "run_day_count", "panel_id", "run_start_date", "run_end_date"],
        ascending=[True, False, False, True, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    site_ranked["site_score_rank"] = site_ranked.groupby("site", dropna=False).cumcount() + 1

    out = full_df.merge(
        ranked.loc[:, [*KEY_COLS, "global_score_rank"]],
        on=KEY_COLS,
        how="left",
        validate="one_to_one",
    )
    out = out.merge(
        site_ranked.loc[:, [*KEY_COLS, "site_score_rank"]],
        on=KEY_COLS,
        how="left",
        validate="one_to_one",
    )
    return out


def gap_class_for_row(label_bucket: str, global_rank: float) -> str:
    rank_value = int(global_rank)
    if label_bucket == "positive_like":
        if rank_value <= 20:
            return "positive_top20_global"
        if rank_value <= 50:
            return "positive_top50_global_not_top20"
        return "positive_below_top50_global"
    if rank_value <= 20:
        return "negative_top20_global"
    if rank_value <= 50:
        return "negative_top50_global_not_top20"
    return "negative_below_top50_global"


def reference_gap_reason(row: pd.Series) -> str:
    gap_class = normalize_text(row["gap_class"])
    cond_evt_ratio = float(row["cond_evt_only_day_ratio"])
    ae_ratio = float(row["ae_mid_or_hi_early_day_ratio"])
    min_mid_ratio = float(row["min_mid_ratio"])

    if gap_class == "positive_top20_global":
        return "strong positive-like run이어서 deterministic reference가 global top20에 안정적으로 올림"
    if gap_class == "positive_top50_global_not_top20":
        return "fault-like electrical signal은 있지만 top20 핵심 severity보다는 한 단계 약해 20-50위에 머묾"
    if gap_class == "positive_below_top50_global":
        if cond_evt_ratio >= 0.5 and ae_ratio >= 0.5 and min_mid_ratio < 0.8:
            return "fault-like 조짐은 있으나 broadshape 보정 뒤 점수가 충분히 못 올라 global top50 밖으로 밀림"
        return "electrical severity와 early corroboration이 상대적으로 약해 deterministic reference가 top50 밖에 둠"
    if gap_class == "negative_top20_global":
        return "negative-like run인데 electrical severity가 높아 current reference에서 false promotion 위험이 큼"
    if gap_class == "negative_top50_global_not_top20":
        return "negative-like run이 상위권 근처까지는 오르지만 top20 핵심 retrieval까지는 못 간 경계 사례"
    return "negative-like run이라 deterministic reference가 global top50 밖으로 눌러 비교적 안전하게 처리"


def prepare_case_output(root: Path) -> pd.DataFrame:
    feature_df = load_feature_table(root)
    label_df = load_label_pack_v2(root)
    score_df = load_v0_scores(root)

    full_df = feature_df.merge(label_df, on=KEY_COLS, how="left", validate="one_to_one")
    full_df = full_df.merge(score_df, on=KEY_COLS, how="left", validate="one_to_one")
    if full_df[FOCUS_SCORE_NAME].isna().any():
        raise SystemExit("missing deterministic scores in merged run universe")

    ranked_df = build_rank_columns(full_df)
    labeled_df = ranked_df.loc[ranked_df["label_bucket_v2"].isin(LABELED_BUCKETS)].copy()
    labeled_df["gap_class"] = labeled_df.apply(
        lambda row: gap_class_for_row(normalize_text(row["label_bucket_v2"]), float(row["global_score_rank"])),
        axis=1,
    )
    labeled_df["reference_gap_reason_ko"] = labeled_df.apply(reference_gap_reason, axis=1)
    labeled_df["gap_class"] = pd.Categorical(labeled_df["gap_class"], categories=GAP_CLASS_ORDER, ordered=True)

    return labeled_df.sort_values(
        ["gap_class", "global_score_rank", "site", "panel_id", "run_start_date", "run_end_date"],
        ascending=[True, True, True, True, True, True],
        kind="mergesort",
    ).reindex(columns=CASE_COLS).reset_index(drop=True)


def median_or_none(df: pd.DataFrame, col: str) -> float | None:
    if df.empty:
        return None
    value = pd.to_numeric(df[col], errors="coerce").median()
    return None if pd.isna(value) else float(value)


def summarize_gap_class(gap_class: str, subset: pd.DataFrame) -> dict[str, object]:
    note_map = {
        "positive_top20_global": "reference가 strong positive-like run을 상위 retrieval에서 잘 잡는 구간",
        "positive_top50_global_not_top20": "positive-like near-miss 구간으로 rerank/tuning 여지를 볼 수 있는 구간",
        "positive_below_top50_global": "current reference miss가 본격적으로 쌓이는 구간",
        "negative_top20_global": "false promotion risk가 가장 높은 구간",
        "negative_top50_global_not_top20": "경계성 false promotion 후보 구간",
        "negative_below_top50_global": "reference가 negative-like run을 비교적 안전하게 누르는 구간",
    }
    return {
        "summary_type": "gap_class_summary",
        "gap_class": gap_class,
        "run_count": int(len(subset)),
        "median_score": median_or_none(subset, FOCUS_SCORE_NAME),
        "median_global_score_rank": median_or_none(subset, "global_score_rank"),
        "median_site_score_rank": median_or_none(subset, "site_score_rank"),
        "median_run_day_count": median_or_none(subset, "run_day_count"),
        "median_max_v_drop": median_or_none(subset, "max_v_drop"),
        "median_min_mid_v_ratio": median_or_none(subset, "min_mid_v_ratio"),
        "median_min_mid_ratio": median_or_none(subset, "min_mid_ratio"),
        "median_cond_evt_only_day_ratio": median_or_none(subset, "cond_evt_only_day_ratio"),
        "median_ae_mid_or_hi_early_day_ratio": median_or_none(subset, "ae_mid_or_hi_early_day_ratio"),
        "median_mean_signal_count": median_or_none(subset, "mean_signal_count"),
        "median_max_signal_count": median_or_none(subset, "max_signal_count"),
        "median_p95_recon_error": median_or_none(subset, "p95_recon_error"),
        "recommended_next_direction": "",
        "note_ko": note_map[gap_class],
    }


def recommend_next_direction(case_df: pd.DataFrame) -> tuple[str, str]:
    positive_top20 = case_df.loc[case_df["gap_class"].astype(str).eq("positive_top20_global")].copy()
    positive_below50 = case_df.loc[case_df["gap_class"].astype(str).eq("positive_below_top50_global")].copy()
    negative_top20 = case_df.loc[case_df["gap_class"].astype(str).eq("negative_top20_global")].copy()

    if positive_below50.empty:
        return (
            "keep_reference_as_best_current",
            "positive-like miss가 사실상 없어서 current deterministic reference를 best current로 유지하는 해석이 자연스럽다.",
        )

    if not positive_top20.empty and not negative_top20.empty:
        pos_v = median_or_none(positive_top20, "max_v_drop") or 0.0
        neg_v = median_or_none(negative_top20, "max_v_drop") or 0.0
        pos_ratio = median_or_none(positive_top20, "min_mid_v_ratio") or 0.0
        neg_ratio = median_or_none(negative_top20, "min_mid_v_ratio") or 0.0
        pos_signal = median_or_none(positive_top20, "mean_signal_count") or 0.0
        neg_signal = median_or_none(negative_top20, "mean_signal_count") or 0.0
        if abs(pos_v - neg_v) <= max(0.5, pos_v * 0.15) and abs(pos_ratio - neg_ratio) <= 0.08 and abs(pos_signal - neg_signal) <= 0.5:
            return (
                "stop_scorer_search_for_now",
                "negative_top20_global이 positive_top20_global과 너무 비슷해 clean separator가 거의 없어, 추가 scorer search 이득이 작다는 신호로 해석된다.",
            )

    if not positive_top20.empty:
        top20_v = median_or_none(positive_top20, "max_v_drop") or 0.0
        top20_ae = median_or_none(positive_top20, "ae_mid_or_hi_early_day_ratio") or 0.0
        top20_signal = median_or_none(positive_top20, "mean_signal_count") or 0.0
        below50_v = median_or_none(positive_below50, "max_v_drop") or 0.0
        below50_ae = median_or_none(positive_below50, "ae_mid_or_hi_early_day_ratio") or 0.0
        below50_signal = median_or_none(positive_below50, "mean_signal_count") or 0.0
        below50_mid = median_or_none(positive_below50, "min_mid_ratio") or 0.0
        top20_mid = median_or_none(positive_top20, "min_mid_ratio") or 0.0

        weaker_severity = (
            below50_v <= top20_v * 0.7
            and below50_ae <= top20_ae * 0.8
            and below50_signal <= top20_signal * 0.8
        )
        broadshape_heavy_but_fault_like = (
            below50_v >= top20_v * 0.7
            and below50_signal >= top20_signal * 0.7
            and below50_ae >= top20_ae * 0.7
            and below50_mid < top20_mid
        )
        if weaker_severity:
            return (
                "keep_reference_as_best_current",
                "positive_below_top50_global이 top20 positives보다 전반적으로 전기적 severity가 약해 current reference를 best current로 유지하는 해석이 맞다.",
            )
        if broadshape_heavy_but_fault_like:
            return (
                "tune_broadshape_penalty_only",
                "missed positive가 fault-like signal은 있으면서 broadshape-heavy 패턴을 보여 broadshape penalty만 미세조정해 볼 가치가 있다.",
            )

    heterogeneous = (
        len(positive_below50) <= 3
        or positive_below50["site"].nunique() >= 2
        and (
            pd.to_numeric(positive_below50["max_v_drop"], errors="coerce").std(ddof=0) > 2.0
            or pd.to_numeric(positive_below50["ae_mid_or_hi_early_day_ratio"], errors="coerce").std(ddof=0) > 0.2
            or pd.to_numeric(positive_below50["mean_signal_count"], errors="coerce").std(ddof=0) > 1.0
        )
    )
    if heterogeneous:
        return (
            "expand_positive_labels_before_more_modeling",
            "missed positive가 아직 sparse하거나 heterogeneous해서 method search보다 positive label expansion이 먼저라는 신호다.",
        )

    return (
        "keep_reference_as_best_current",
        "current deterministic reference가 아직 가장 해석 가능하고 안정적인 baseline으로 보인다.",
    )


def build_summary(case_df: pd.DataFrame) -> pd.DataFrame:
    rows = [summarize_gap_class(gap_class, case_df.loc[case_df["gap_class"].astype(str).eq(gap_class)].copy()) for gap_class in GAP_CLASS_ORDER]
    recommended_next_direction, recommendation_note = recommend_next_direction(case_df)
    rows.append(
        {
            "summary_type": "overall_recommendation",
            "gap_class": "",
            "run_count": int(len(case_df)),
            "median_score": None,
            "median_global_score_rank": None,
            "median_site_score_rank": None,
            "median_run_day_count": None,
            "median_max_v_drop": None,
            "median_min_mid_v_ratio": None,
            "median_min_mid_ratio": None,
            "median_cond_evt_only_day_ratio": None,
            "median_ae_mid_or_hi_early_day_ratio": None,
            "median_mean_signal_count": None,
            "median_max_signal_count": None,
            "median_p95_recon_error": None,
            "recommended_next_direction": recommended_next_direction,
            "note_ko": recommendation_note,
        }
    )
    return pd.DataFrame(rows, columns=SUMMARY_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    case_df = prepare_case_output(root)
    summary_df = build_summary(case_df)

    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    case_df.to_csv(share_dir / CASES_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
