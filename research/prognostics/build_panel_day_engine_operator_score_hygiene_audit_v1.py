#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

OPERATOR_REGISTRY_NAME = "panel_day_engine_operator_run_registry_v1.csv"
OPERATOR_QUEUE_NAME = "panel_day_engine_operator_run_queue_v1.csv"
OPERATOR_BACKLOG_NAME = "panel_day_engine_operator_run_backlog_v1.csv"
FEATURE_TABLE_NAME = "panel_day_engine_run_feature_table_v1.csv"
V0_SCORES_NAME = "panel_day_engine_run_ranker_v0_scores.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_operator_score_hygiene_summary_v1.csv"
OUTLIER_OUTPUT_NAME = "panel_day_engine_operator_score_hygiene_outlier_runs_v1.csv"
CLIP_OUTPUT_NAME = "panel_day_engine_operator_score_clip_sensitivity_v1.csv"

KEY_COLS = ["site", "panel_id", "run_start_date", "run_end_date"]
STRING_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_shape_class",
    "status",
    "action_bucket",
    "overlap_case_class",
    "cohort_hint",
    "fate_class",
]
PRIMARY_SCORE = "electrical_core_minus_broadshape_050"
REFERENCE_SCORE = "electrical_core_score"
SCORE_COLS = [REFERENCE_SCORE, PRIMARY_SCORE]
AUDITED_FEATURES = [
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
]
REGISTRY_REQUIRED_COLS = [
    *KEY_COLS,
    "run_day_count",
    "run_shape_class",
    "cohort_hint",
    "fate_class",
    "status",
    "action_bucket",
    "overlap_case_class",
    "queue_eligible_flag",
    "backlog_flag",
    "future_fault_linked_flag",
    "future_truth_linked_flag",
    REFERENCE_SCORE,
    PRIMARY_SCORE,
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
]
FEATURE_REQUIRED_COLS = [*KEY_COLS, "mean_signal_count", "max_signal_count", "p95_recon_error"]
V0_REQUIRED_COLS = [*KEY_COLS, REFERENCE_SCORE, PRIMARY_SCORE]
SUMMARY_OUTPUT_COLS = [
    "record_type",
    "site",
    "feature_name",
    "median_value",
    "iqr_value",
    "p99_value",
    "p99_5_value",
    "total_run_count",
    "suspicious_run_count",
    "suspicious_queue_run_count",
    "suspicious_backlog_run_count",
    "p99_score",
    "p99_5_score",
    "max_score",
    "top20_overlap_rate_after_clipping",
    "top50_overlap_rate_after_clipping",
    "top100_overlap_rate_after_clipping",
]
OUTLIER_OUTPUT_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "status",
    "action_bucket",
    "overlap_case_class",
    REFERENCE_SCORE,
    PRIMARY_SCORE,
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
    "suspicious_feature_count",
    "suspicious_reason_ko",
    "core_vdrop_term",
    "core_midv_term",
    "core_mid_term",
    "broadshape_penalty_term",
    "evtonly_bonus_term",
]
CLIP_OUTPUT_COLS = [
    "record_type",
    "scope_name",
    "site",
    "top20_rank_change_count",
    "top50_rank_change_count",
    "top100_rank_change_count",
    "max_absolute_rank_shift",
    "top20_overlap_rate",
    "top50_overlap_rate",
    "top100_overlap_rate",
    "note",
    "panel_id",
    "run_start_date",
    "raw_score",
    "clipped_score",
    "raw_rank",
    "clipped_rank",
    "rank_shift",
    "shift_reason_ko",
]
EPSILON = 1e-9
TOP_K_VALUES = [20, 50, 100]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit operator-facing score hygiene and clipping sensitivity for run ordering."
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


def normalize_frame(df: pd.DataFrame, string_cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in string_cols:
        normalizer = normalize_date if col in {"run_start_date", "run_end_date"} else normalize_text
        out[col] = out[col].map(normalizer)
    return out


def robust_scale(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.dropna().empty:
        return pd.Series(0.0, index=series.index)
    median = float(numeric.median())
    q1 = float(numeric.quantile(0.25))
    q3 = float(numeric.quantile(0.75))
    iqr = q3 - q1
    denom = iqr if abs(iqr) > EPSILON else 1.0
    return ((numeric.fillna(median) - median) / denom).clip(-5.0, 5.0)


def compute_stats(series: pd.Series) -> dict[str, float | None]:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return {
            "median": None,
            "iqr": None,
            "p99": None,
            "p99_5": None,
            "max": None,
        }
    q1 = float(numeric.quantile(0.25))
    q3 = float(numeric.quantile(0.75))
    return {
        "median": float(numeric.median()),
        "iqr": float(q3 - q1),
        "p99": float(numeric.quantile(0.99)),
        "p99_5": float(numeric.quantile(0.995)),
        "max": float(numeric.max()),
    }


def load_registry(root: Path) -> pd.DataFrame:
    path = root / "_share" / OPERATOR_REGISTRY_NAME
    df = read_csv(path)
    ensure_columns(df, REGISTRY_REQUIRED_COLS, path.name)
    df = drop_repeated_header_rows(df)
    df = normalize_frame(df, STRING_COLS)
    for col in REGISTRY_REQUIRED_COLS:
        if col in STRING_COLS:
            continue
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.loc[:, REGISTRY_REQUIRED_COLS].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_key_file(root: Path, name: str) -> pd.DataFrame:
    path = root / "_share" / name
    df = read_csv(path)
    ensure_columns(df, KEY_COLS, path.name)
    df = drop_repeated_header_rows(df)
    df = normalize_frame(df, KEY_COLS)
    return df.loc[:, KEY_COLS].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_feature_extras(root: Path) -> pd.DataFrame:
    path = root / "_share" / FEATURE_TABLE_NAME
    df = read_csv(path)
    ensure_columns(df, FEATURE_REQUIRED_COLS, path.name)
    df = drop_repeated_header_rows(df)
    df = normalize_frame(df, KEY_COLS)
    for col in FEATURE_REQUIRED_COLS:
        if col in KEY_COLS:
            continue
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.loc[:, FEATURE_REQUIRED_COLS].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_v0_scores(root: Path) -> pd.DataFrame:
    path = root / "_share" / V0_SCORES_NAME
    df = read_csv(path)
    ensure_columns(df, V0_REQUIRED_COLS, path.name)
    df = drop_repeated_header_rows(df)
    df = normalize_frame(df, KEY_COLS)
    for col in SCORE_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.loc[:, V0_REQUIRED_COLS].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def prepare_universe(root: Path) -> tuple[pd.DataFrame, set[tuple[str, str, str, str]], set[tuple[str, str, str, str]]]:
    registry = load_registry(root)
    feature_extras = load_feature_extras(root)
    v0_scores = load_v0_scores(root).rename(
        columns={
            REFERENCE_SCORE: f"{REFERENCE_SCORE}_v0",
            PRIMARY_SCORE: f"{PRIMARY_SCORE}_v0",
        }
    )
    queue_keys_df = load_key_file(root, OPERATOR_QUEUE_NAME)
    backlog_keys_df = load_key_file(root, OPERATOR_BACKLOG_NAME)

    merged = registry.merge(feature_extras, on=KEY_COLS, how="left", validate="one_to_one")
    merged = merged.merge(v0_scores, on=KEY_COLS, how="left", validate="one_to_one")
    for col in [f"{REFERENCE_SCORE}_v0", f"{PRIMARY_SCORE}_v0"]:
        if merged[col].isna().any():
            raise SystemExit(f"missing reference v0 score after merge: {col}")

    for col in SCORE_COLS:
        ref_col = f"{col}_v0"
        diff = (pd.to_numeric(merged[col], errors="coerce") - pd.to_numeric(merged[ref_col], errors="coerce")).abs()
        if diff.fillna(0.0).gt(1e-9).any():
            raise SystemExit(f"registry and v0 score mismatch detected for {col}")
        merged = merged.drop(columns=[ref_col])

    merged["run_key"] = list(zip(merged["site"], merged["panel_id"], merged["run_start_date"], merged["run_end_date"]))
    queue_keys = set(tuple(row) for row in queue_keys_df.itertuples(index=False, name=None))
    backlog_keys = set(tuple(row) for row in backlog_keys_df.itertuples(index=False, name=None))
    merged["queue_file_flag"] = merged["run_key"].isin(queue_keys).astype(int)
    merged["backlog_file_flag"] = merged["run_key"].isin(backlog_keys).astype(int)
    merged["run_start_dt"] = pd.to_datetime(merged["run_start_date"], errors="coerce")
    return merged, queue_keys, backlog_keys


def compute_distribution_rows(df: pd.DataFrame) -> tuple[list[dict[str, object]], dict[tuple[str, str], dict[str, float | None]]]:
    rows: list[dict[str, object]] = []
    stats_map: dict[tuple[str, str], dict[str, float | None]] = {}
    feature_list = [*AUDITED_FEATURES, *SCORE_COLS]
    scopes = [("", df)] + [(site, site_df.copy()) for site, site_df in df.groupby("site", sort=True, dropna=False)]

    for site, scope_df in scopes:
        for feature_name in feature_list:
            stats = compute_stats(scope_df[feature_name])
            stats_map[(site, feature_name)] = stats
            rows.append(
                {
                    "record_type": "distribution",
                    "site": site,
                    "feature_name": feature_name,
                    "median_value": stats["median"],
                    "iqr_value": stats["iqr"],
                    "p99_value": stats["p99"],
                    "p99_5_value": stats["p99_5"],
                    "total_run_count": int(len(scope_df)),
                    "suspicious_run_count": None,
                    "suspicious_queue_run_count": None,
                    "suspicious_backlog_run_count": None,
                    "p99_score": None,
                    "p99_5_score": None,
                    "max_score": None,
                    "top20_overlap_rate_after_clipping": None,
                    "top50_overlap_rate_after_clipping": None,
                    "top100_overlap_rate_after_clipping": None,
                }
            )
    return rows, stats_map


def compute_raw_score_terms(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["core_vdrop_term"] = robust_scale(out["max_v_drop"])
    out["core_midv_term"] = robust_scale(1.0 - out["min_mid_v_ratio"])
    out["core_mid_term"] = robust_scale(1.0 - out["min_mid_ratio"])
    out["evtonly_bonus_term"] = robust_scale(out["cond_evt_only_day_ratio"])
    ae_term = robust_scale(out["ae_mid_or_hi_early_day_ratio"])
    mean_signal_term = robust_scale(out["mean_signal_count"])
    max_signal_term = robust_scale(out["max_signal_count"])
    recon_term = robust_scale(out["p95_recon_error"])
    out["broadshape_penalty_term"] = ae_term + mean_signal_term + max_signal_term + recon_term
    out["reconstructed_core_score"] = out["core_vdrop_term"] + out["core_midv_term"] + out["core_mid_term"]
    out["reconstructed_core_minus_broadshape_050"] = (
        out["reconstructed_core_score"] - 0.50 * out["broadshape_penalty_term"]
    )
    return out


def compute_site_p99_map(df: pd.DataFrame) -> dict[tuple[str, str], float]:
    p99_map: dict[tuple[str, str], float] = {}
    for site, site_df in df.groupby("site", sort=True, dropna=False):
        for feature_name in AUDITED_FEATURES:
            p99_map[(site, feature_name)] = compute_stats(site_df[feature_name])["p99"]
    return p99_map


def compute_clipped_score(df: pd.DataFrame, site_p99_map: dict[tuple[str, str], float]) -> pd.DataFrame:
    clipped = df.copy()
    clipped_feature_names: list[list[str]] = []
    for idx, row in clipped.iterrows():
        changed: list[str] = []
        site = row["site"]
        for feature_name in AUDITED_FEATURES:
            threshold = site_p99_map.get((site, feature_name))
            value = pd.to_numeric(row[feature_name], errors="coerce")
            if pd.notna(value) and threshold is not None and pd.notna(threshold) and value > threshold:
                clipped.at[idx, feature_name] = threshold
                changed.append(feature_name)
        clipped_feature_names.append(changed)
    clipped = compute_raw_score_terms(clipped)
    clipped["electrical_core_minus_broadshape_050_clipped"] = clipped["reconstructed_core_minus_broadshape_050"]
    clipped["clipped_feature_names"] = clipped_feature_names
    return clipped.loc[:, [*KEY_COLS, "electrical_core_minus_broadshape_050_clipped", "clipped_feature_names"]]


def detect_suspicious_runs(df: pd.DataFrame, stats_map: dict[tuple[str, str], dict[str, float | None]]) -> pd.DataFrame:
    suspicious_counts: list[int] = []
    suspicious_reasons: list[str] = []
    suspicious_mask: list[bool] = []
    feature_list = [*AUDITED_FEATURES, *SCORE_COLS]

    for _, row in df.iterrows():
        site = row["site"]
        p99_5_hits: list[str] = []
        robust_hits: list[str] = []
        for feature_name in feature_list:
            stats = stats_map.get((site, feature_name), {})
            value = pd.to_numeric(row[feature_name], errors="coerce")
            if pd.isna(value):
                continue
            p99_5 = stats.get("p99_5")
            if p99_5 is not None and pd.notna(p99_5) and value > float(p99_5):
                p99_5_hits.append(feature_name)
            median = stats.get("median")
            iqr = stats.get("iqr")
            if median is None or iqr is None or pd.isna(median):
                continue
            denom = float(iqr) if iqr is not None and abs(float(iqr)) > EPSILON else EPSILON
            robust_z = (float(value) - float(median)) / denom
            if robust_z > 8.0:
                robust_hits.append(feature_name)

        hit_names = sorted(set([*p99_5_hits, *robust_hits]))
        suspicious = bool(hit_names)
        suspicious_mask.append(suspicious)
        suspicious_counts.append(len(hit_names))
        reasons: list[str] = []
        if p99_5_hits:
            reasons.append(f"site p99.5 초과: {','.join(sorted(set(p99_5_hits)))}")
        if robust_hits:
            reasons.append(f"robust_z 과대: {','.join(sorted(set(robust_hits)))}")
        suspicious_reasons.append("; ".join(reasons))

    out = df.copy()
    out["suspicious_run_flag"] = suspicious_mask
    out["suspicious_feature_count"] = suspicious_counts
    out["suspicious_reason_ko"] = suspicious_reasons
    return out


def rank_scope(scope_df: pd.DataFrame, score_col: str) -> pd.DataFrame:
    ranked = scope_df.sort_values(
        [score_col, "run_day_count", "site", "panel_id", "run_start_date", "run_end_date"],
        ascending=[False, False, True, True, True, True],
        kind="mergesort",
    ).copy()
    ranked["rank"] = range(1, len(ranked) + 1)
    return ranked.loc[:, [*KEY_COLS, "rank"]]


def compute_scope_clip_summary(scope_df: pd.DataFrame, scope_name: str, site: str) -> tuple[dict[str, object], pd.DataFrame]:
    if scope_df.empty:
        return (
            {
                "record_type": "summary",
                "scope_name": scope_name,
                "site": site,
                "top20_rank_change_count": 0,
                "top50_rank_change_count": 0,
                "top100_rank_change_count": 0,
                "max_absolute_rank_shift": 0,
                "top20_overlap_rate": None,
                "top50_overlap_rate": None,
                "top100_overlap_rate": None,
                "note": "empty_scope",
                "panel_id": None,
                "run_start_date": None,
                "raw_score": None,
                "clipped_score": None,
                "raw_rank": None,
                "clipped_rank": None,
                "rank_shift": None,
                "shift_reason_ko": None,
            },
            scope_df,
        )

    raw_ranks = rank_scope(scope_df, PRIMARY_SCORE).rename(columns={"rank": "raw_rank"})
    clipped_ranks = rank_scope(scope_df, "electrical_core_minus_broadshape_050_clipped").rename(columns={"rank": "clipped_rank"})
    ranked = scope_df.merge(raw_ranks, on=KEY_COLS, how="left", validate="one_to_one")
    ranked = ranked.merge(clipped_ranks, on=KEY_COLS, how="left", validate="one_to_one")
    ranked["rank_shift"] = ranked["clipped_rank"] - ranked["raw_rank"]
    ranked["abs_rank_shift"] = ranked["rank_shift"].abs()

    summary: dict[str, object] = {
        "record_type": "summary",
        "scope_name": scope_name,
        "site": site,
        "note": "site_p99 upper clipping on audited raw features",
        "panel_id": None,
        "run_start_date": None,
        "raw_score": None,
        "clipped_score": None,
        "raw_rank": None,
        "clipped_rank": None,
        "rank_shift": None,
        "shift_reason_ko": None,
    }
    for top_k in TOP_K_VALUES:
        denom = min(top_k, len(ranked))
        raw_top = set(ranked.loc[ranked["raw_rank"].le(denom), "run_key"]) if denom else set()
        clipped_top = set(ranked.loc[ranked["clipped_rank"].le(denom), "run_key"]) if denom else set()
        overlap = len(raw_top & clipped_top) / float(denom) if denom else None
        changed = int(
            ranked.loc[
                (ranked[["raw_rank", "clipped_rank"]].min(axis=1) <= denom)
                & ranked["raw_rank"].ne(ranked["clipped_rank"])
            ].shape[0]
        ) if denom else 0
        summary[f"top{top_k}_rank_change_count"] = changed
        summary[f"top{top_k}_overlap_rate"] = overlap
    summary["max_absolute_rank_shift"] = int(ranked["abs_rank_shift"].max()) if not ranked.empty else 0
    return summary, ranked


def build_shift_reason(row: pd.Series) -> str:
    changed = row.get("clipped_feature_names", [])
    if not changed:
        return "clipping 영향 작음"
    return f"p99 clipping 영향: {','.join(changed[:3])}"


def build_clip_sensitivity(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, dict[str, object]]]:
    summary_rows: list[dict[str, object]] = []
    scope_summary_map: dict[str, dict[str, object]] = {}

    overall_summary, overall_ranked = compute_scope_clip_summary(df.copy(), "overall", "")
    summary_rows.append(overall_summary)
    scope_summary_map[""] = overall_summary

    for site, site_df in df.groupby("site", sort=True, dropna=False):
        site_summary, _ = compute_scope_clip_summary(site_df.copy(), site, site)
        summary_rows.append(site_summary)
        scope_summary_map[site] = site_summary

    overall_ranked = overall_ranked.sort_values(
        ["abs_rank_shift", PRIMARY_SCORE, "run_day_count"],
        ascending=[False, False, False],
        kind="mergesort",
    ).copy()
    largest_shift_rows: list[dict[str, object]] = []
    for _, row in overall_ranked.head(20).iterrows():
        largest_shift_rows.append(
            {
                "record_type": "largest_shift",
                "scope_name": "overall",
                "site": row["site"],
                "top20_rank_change_count": None,
                "top50_rank_change_count": None,
                "top100_rank_change_count": None,
                "max_absolute_rank_shift": None,
                "top20_overlap_rate": None,
                "top50_overlap_rate": None,
                "top100_overlap_rate": None,
                "note": None,
                "panel_id": row["panel_id"],
                "run_start_date": row["run_start_date"],
                "raw_score": row[PRIMARY_SCORE],
                "clipped_score": row["electrical_core_minus_broadshape_050_clipped"],
                "raw_rank": int(row["raw_rank"]),
                "clipped_rank": int(row["clipped_rank"]),
                "rank_shift": int(row["rank_shift"]),
                "shift_reason_ko": build_shift_reason(row),
            }
        )
    clip_df = pd.DataFrame([*summary_rows, *largest_shift_rows], columns=CLIP_OUTPUT_COLS)
    return clip_df, scope_summary_map


def build_scope_summary_rows(
    df: pd.DataFrame,
    scope_summary_map: dict[str, dict[str, object]],
    queue_keys: set[tuple[str, str, str, str]],
    backlog_keys: set[tuple[str, str, str, str]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    scopes = [("", df)] + [(site, site_df.copy()) for site, site_df in df.groupby("site", sort=True, dropna=False)]

    for site, scope_df in scopes:
        suspicious = scope_df.loc[scope_df["suspicious_run_flag"]].copy()
        queue_hits = suspicious["run_key"].isin(queue_keys)
        backlog_hits = suspicious["run_key"].isin(backlog_keys)
        score_stats = compute_stats(scope_df[PRIMARY_SCORE])
        clip_summary = scope_summary_map.get(site, {})
        rows.append(
            {
                "record_type": "scope_summary",
                "site": site,
                "feature_name": "",
                "median_value": None,
                "iqr_value": None,
                "p99_value": None,
                "p99_5_value": None,
                "total_run_count": int(len(scope_df)),
                "suspicious_run_count": int(len(suspicious)),
                "suspicious_queue_run_count": int(queue_hits.sum()),
                "suspicious_backlog_run_count": int(backlog_hits.sum()),
                "p99_score": score_stats["p99"],
                "p99_5_score": score_stats["p99_5"],
                "max_score": score_stats["max"],
                "top20_overlap_rate_after_clipping": clip_summary.get("top20_overlap_rate"),
                "top50_overlap_rate_after_clipping": clip_summary.get("top50_overlap_rate"),
                "top100_overlap_rate_after_clipping": clip_summary.get("top100_overlap_rate"),
            }
        )
    return rows


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    universe, queue_keys, backlog_keys = prepare_universe(root)
    distribution_rows, site_stats = compute_distribution_rows(universe)
    universe = compute_raw_score_terms(universe)
    site_p99_map = compute_site_p99_map(universe)
    clipped_scores = compute_clipped_score(universe, site_p99_map)
    universe = universe.merge(clipped_scores, on=KEY_COLS, how="left", validate="one_to_one")
    universe = detect_suspicious_runs(universe, site_stats)

    outliers = universe.loc[universe["suspicious_run_flag"]].copy()
    outliers = outliers.sort_values(
        ["suspicious_feature_count", PRIMARY_SCORE, "run_day_count", "site", "panel_id"],
        ascending=[False, False, False, True, True],
        kind="mergesort",
    )

    clip_sensitivity, scope_summary_map = build_clip_sensitivity(universe)
    scope_summary_rows = build_scope_summary_rows(universe, scope_summary_map, queue_keys, backlog_keys)
    summary = pd.DataFrame([*scope_summary_rows, *distribution_rows], columns=SUMMARY_OUTPUT_COLS)

    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    outliers.loc[:, OUTLIER_OUTPUT_COLS].to_csv(
        share_dir / OUTLIER_OUTPUT_NAME,
        index=False,
        encoding="utf-8-sig",
    )
    clip_sensitivity.to_csv(share_dir / CLIP_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
