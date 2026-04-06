#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import build_panel_day_engine_run_boundary_label_expansion_audit_v1 as boundary_base

RAW_CANDIDATES_NAME = "panel_day_engine_run_boundary_label_expansion_candidates_v1.csv"
RAW_SUMMARY_NAME = "panel_day_engine_run_boundary_label_expansion_summary_v1.csv"
RAW_PROTOTYPES_NAME = "panel_day_engine_run_boundary_label_expansion_prototypes_v1.csv"
REVIEW_BATCH_NAME = "panel_day_engine_run_label_expansion_review_batch_v1.csv"

SUMMARY_OUTPUT_NAME = "panel_day_engine_run_boundary_distance_hygiene_summary_v1.csv"
OUTLIERS_OUTPUT_NAME = "panel_day_engine_run_boundary_distance_hygiene_outliers_v1.csv"
STRATEGY_OUTPUT_NAME = "panel_day_engine_run_boundary_distance_hygiene_strategy_v1.csv"

MODE_NAMES = [
    "raw_boundary",
    "clipped_global_boundary",
    "clipped_site_boundary",
    "boundary_intersection_with_review_batch",
]
ACTIONABLE_CLASSES = {"positive_promotion_candidate", "hard_negative_review_candidate"}
POSITIVE_REVIEW_TRACK = "positive_review_batch"
MIN_SITE_ROWS_FOR_SITE_P99 = 10

RAW_CANDIDATE_REQUIRED_COLS = [
    *boundary_base.KEY_COLS,
    "candidate_class",
    "candidate_priority_band",
    "positive_boundary_distance",
    "hard_negative_distance",
    "boundary_margin",
    "electrical_core_minus_broadshape_050",
    "global_score_rank",
    "site_score_rank",
]
RAW_SUMMARY_REQUIRED_COLS = [
    "record_type",
    "site",
    "excluded_run_count",
    "positive_promotion_candidate_count",
    "hard_negative_review_candidate_count",
]
STORED_PROTOTYPE_REQUIRED_COLS = [
    "prototype_pool_name",
    *boundary_base.KEY_COLS,
]
OUTLIER_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "candidate_class",
    "suspicious_feature_count",
    "suspicious_reason_ko",
    "positive_boundary_distance",
    "hard_negative_distance",
    "boundary_margin",
    *boundary_base.DISTANCE_FEATURE_COLS,
]
SUMMARY_COLS = [
    "mode_name",
    "prototype_pool_positive_count",
    "prototype_pool_hard_negative_count",
    "candidate_universe_count",
    "raw_positive_promotion_candidate_count",
    "raw_hard_negative_review_candidate_count",
    "positive_promotion_candidate_count",
    "hard_negative_review_candidate_count",
    "candidate_count_reduction_vs_raw",
    "top50_overlap_with_raw",
    "top50_overlap_with_review_batch",
    "suspicious_candidate_count",
    "note_ko",
]
STRATEGY_COLS = ["recommended_strategy", "recommended_reason_ko"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Diagnose and stabilize the boundary-distance label expansion method before any v3 scorer step."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to the project root.",
    )
    return parser.parse_args()


def load_existing_raw_candidates(root: Path) -> pd.DataFrame:
    path = root / "_share" / RAW_CANDIDATES_NAME
    df = boundary_base.drop_repeated_header_rows(boundary_base.read_csv(path))
    boundary_base.ensure_columns(df, RAW_CANDIDATE_REQUIRED_COLS, path.name)
    df = boundary_base.normalize_key_cols(df)
    for col in ["candidate_class", "candidate_priority_band"]:
        df[col] = df[col].map(boundary_base.normalize_text)
    numeric_cols = [col for col in RAW_CANDIDATE_REQUIRED_COLS if col not in boundary_base.KEY_COLS and col not in {"candidate_class", "candidate_priority_band"}]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.loc[:, RAW_CANDIDATE_REQUIRED_COLS].drop_duplicates(subset=boundary_base.KEY_COLS, keep="first").reset_index(drop=True)


def load_existing_raw_summary(root: Path) -> pd.DataFrame:
    path = root / "_share" / RAW_SUMMARY_NAME
    df = boundary_base.drop_repeated_header_rows(boundary_base.read_csv(path))
    boundary_base.ensure_columns(df, RAW_SUMMARY_REQUIRED_COLS, path.name)
    df["record_type"] = df["record_type"].map(boundary_base.normalize_text)
    df["site"] = df["site"].map(boundary_base.normalize_text)
    for col in ["excluded_run_count", "positive_promotion_candidate_count", "hard_negative_review_candidate_count"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.loc[:, RAW_SUMMARY_REQUIRED_COLS].reset_index(drop=True)


def load_stored_prototypes(root: Path) -> pd.DataFrame:
    path = root / "_share" / RAW_PROTOTYPES_NAME
    df = boundary_base.drop_repeated_header_rows(boundary_base.read_csv(path))
    boundary_base.ensure_columns(df, STORED_PROTOTYPE_REQUIRED_COLS, path.name)
    df = boundary_base.normalize_key_cols(df)
    df["prototype_pool_name"] = df["prototype_pool_name"].map(boundary_base.normalize_text)
    return df.loc[:, STORED_PROTOTYPE_REQUIRED_COLS].drop_duplicates(subset=["prototype_pool_name", *boundary_base.KEY_COLS], keep="first").reset_index(drop=True)


def positive_review_batch_keys(root: Path) -> set[tuple[str, str, str, str]]:
    review_batch_df = boundary_base.load_review_batch(root)
    positive_df = review_batch_df.loc[review_batch_df["review_track"].eq(POSITIVE_REVIEW_TRACK)].copy()
    return set(boundary_base.make_key_tuple_frame(positive_df))


def reconstruct_raw_mode(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    excluded_df, reference_gap_df, total_scored_run_count = boundary_base.build_joined_universe(root)
    prototype_df = boundary_base.build_prototype_output(reference_gap_df)
    with_distances = boundary_base.compute_boundary_distances(excluded_df, prototype_df)
    classified = boundary_base.classify_candidates(with_distances, total_scored_run_count=total_scored_run_count)
    return classified.reset_index(drop=True), prototype_df.reset_index(drop=True), total_scored_run_count


def clip_at_thresholds(df: pd.DataFrame, thresholds_df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for feature in boundary_base.DISTANCE_FEATURE_COLS:
        out[feature] = pd.to_numeric(out[feature], errors="coerce").astype(float)
    threshold_lookup = thresholds_df.set_index("site")
    global_thresholds = threshold_lookup.loc["__global__"]
    for idx, row in out.iterrows():
        site = boundary_base.normalize_text(row["site"])
        thresholds = threshold_lookup.loc[site] if site in threshold_lookup.index else global_thresholds
        for feature in boundary_base.DISTANCE_FEATURE_COLS:
            value = pd.to_numeric(pd.Series([row[feature]]), errors="coerce").iloc[0]
            cap = pd.to_numeric(pd.Series([thresholds[feature]]), errors="coerce").iloc[0]
            if pd.isna(value) or pd.isna(cap):
                continue
            if value > cap:
                out.at[idx, feature] = cap
    return out


def build_global_clip_thresholds(prototype_df: pd.DataFrame, candidate_df: pd.DataFrame, quantile: float = 0.99) -> pd.DataFrame:
    combined = pd.concat(
        [
            prototype_df.loc[:, ["site", *boundary_base.DISTANCE_FEATURE_COLS]],
            candidate_df.loc[:, ["site", *boundary_base.DISTANCE_FEATURE_COLS]],
        ],
        ignore_index=True,
    )
    numeric = combined.loc[:, boundary_base.DISTANCE_FEATURE_COLS].apply(pd.to_numeric, errors="coerce")
    thresholds = numeric.quantile(quantile)
    row = {"site": "__global__"}
    row.update(thresholds.to_dict())
    return pd.DataFrame([row])


def build_site_clip_thresholds(prototype_df: pd.DataFrame, candidate_df: pd.DataFrame, quantile: float = 0.99) -> pd.DataFrame:
    combined = pd.concat(
        [
            prototype_df.loc[:, ["site", *boundary_base.DISTANCE_FEATURE_COLS]],
            candidate_df.loc[:, ["site", *boundary_base.DISTANCE_FEATURE_COLS]],
        ],
        ignore_index=True,
    )
    numeric_combined = combined.copy()
    for col in boundary_base.DISTANCE_FEATURE_COLS:
        numeric_combined[col] = pd.to_numeric(numeric_combined[col], errors="coerce")

    global_threshold_row = {"site": "__global__"}
    global_threshold_row.update(numeric_combined.loc[:, boundary_base.DISTANCE_FEATURE_COLS].quantile(quantile).to_dict())
    rows = [global_threshold_row]
    for site, site_df in numeric_combined.groupby("site", dropna=False):
        site_name = boundary_base.normalize_text(site)
        if len(site_df) < MIN_SITE_ROWS_FOR_SITE_P99:
            continue
        row = {"site": site_name}
        row.update(site_df.loc[:, boundary_base.DISTANCE_FEATURE_COLS].quantile(quantile).to_dict())
        rows.append(row)
    return pd.DataFrame(rows)


def recompute_mode(
    raw_candidate_df: pd.DataFrame,
    prototype_df: pd.DataFrame,
    total_scored_run_count: int,
    mode_name: str,
) -> pd.DataFrame:
    if mode_name == "raw_boundary":
        return raw_candidate_df.copy()

    if mode_name == "clipped_global_boundary":
        thresholds_df = build_global_clip_thresholds(prototype_df, raw_candidate_df)
        clipped_prototypes = clip_at_thresholds(prototype_df, thresholds_df)
        clipped_candidates = clip_at_thresholds(raw_candidate_df, thresholds_df)
        with_distances = boundary_base.compute_boundary_distances(clipped_candidates, clipped_prototypes)
        return boundary_base.classify_candidates(with_distances, total_scored_run_count=total_scored_run_count)

    if mode_name == "clipped_site_boundary":
        thresholds_df = build_site_clip_thresholds(prototype_df, raw_candidate_df)
        clipped_prototypes = clip_at_thresholds(prototype_df, thresholds_df)
        clipped_candidates = clip_at_thresholds(raw_candidate_df, thresholds_df)
        with_distances = boundary_base.compute_boundary_distances(clipped_candidates, clipped_prototypes)
        return boundary_base.classify_candidates(with_distances, total_scored_run_count=total_scored_run_count)

    raise ValueError(f"unsupported mode: {mode_name}")


def sort_positive_candidates(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.loc[df["candidate_class"].eq("positive_promotion_candidate")].copy()
        .sort_values(
            by=["boundary_margin", "electrical_core_minus_broadshape_050", "site", "panel_id", "run_start_date", "run_end_date"],
            ascending=[False, False, True, True, True, True],
            na_position="last",
        )
        .reset_index(drop=True)
    )


def actionable_key_set(df: pd.DataFrame) -> set[tuple[str, str, str, str]]:
    return set(boundary_base.make_key_tuple_frame(df.loc[df["candidate_class"].isin(ACTIONABLE_CLASSES)].copy()))


def positive_top_keys(df: pd.DataFrame, top_k: int = 50) -> set[tuple[str, str, str, str]]:
    sorted_positive = sort_positive_candidates(df).head(top_k)
    return set(boundary_base.make_key_tuple_frame(sorted_positive))


def detect_suspicious_runs(candidate_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    out = candidate_df.copy().reset_index(drop=True)
    feature_frame = out.loc[:, boundary_base.DISTANCE_FEATURE_COLS].apply(pd.to_numeric, errors="coerce")
    feature_p995 = feature_frame.quantile(0.995)
    medians = feature_frame.median()
    iqr = (feature_frame.quantile(0.75) - feature_frame.quantile(0.25)).replace(0, np.nan).fillna(1.0)
    robust_z = (feature_frame.fillna(medians) - medians) / iqr

    distance_cols = ["positive_boundary_distance", "hard_negative_distance"]
    distance_frame = out.loc[:, distance_cols].apply(pd.to_numeric, errors="coerce")
    distance_p995 = distance_frame.quantile(0.995)

    suspicious_rows: list[dict[str, object]] = []
    suspicious_flags: list[int] = []
    suspicious_counts: list[int] = []
    suspicious_reasons: list[str] = []

    for idx, row in out.iterrows():
        reasons: list[str] = []
        for feature in boundary_base.DISTANCE_FEATURE_COLS:
            value = feature_frame.iloc[idx][feature]
            z_value = robust_z.iloc[idx][feature]
            if not pd.isna(value) and value > feature_p995[feature]:
                reasons.append(f"{feature}가 global p99.5를 초과")
            if not pd.isna(z_value) and abs(float(z_value)) > 8.0:
                reasons.append(f"{feature}의 absolute robust_z가 8을 초과")
        for distance_col in distance_cols:
            value = distance_frame.iloc[idx][distance_col]
            if not pd.isna(value) and value > distance_p995[distance_col]:
                reasons.append(f"{distance_col}가 global p99.5를 초과")

        suspicious_flag = int(len(reasons) > 0)
        suspicious_flags.append(suspicious_flag)
        suspicious_counts.append(len(reasons))
        suspicious_reasons.append("; ".join(reasons))

        if suspicious_flag:
            record = {
                "site": row["site"],
                "panel_id": row["panel_id"],
                "run_start_date": row["run_start_date"],
                "run_end_date": row["run_end_date"],
                "candidate_class": row["candidate_class"],
                "suspicious_feature_count": len(reasons),
                "suspicious_reason_ko": "; ".join(reasons),
                "positive_boundary_distance": row["positive_boundary_distance"],
                "hard_negative_distance": row["hard_negative_distance"],
                "boundary_margin": row["boundary_margin"],
            }
            for feature in boundary_base.DISTANCE_FEATURE_COLS:
                record[feature] = row[feature]
            suspicious_rows.append(record)

    out["suspicious_flag"] = suspicious_flags
    out["suspicious_feature_count"] = suspicious_counts
    out["suspicious_reason_ko"] = suspicious_reasons
    suspicious_df = pd.DataFrame(suspicious_rows).reindex(columns=OUTLIER_COLS)
    return out, suspicious_df


def build_intersection_mode(raw_mode_df: pd.DataFrame, review_batch_positive_keys: set[tuple[str, str, str, str]]) -> pd.DataFrame:
    out = raw_mode_df.copy()
    keys = boundary_base.make_key_tuple_frame(out)
    keep_positive = keys.isin(review_batch_positive_keys) & out["candidate_class"].eq("positive_promotion_candidate")
    out["candidate_class"] = np.where(keep_positive, "positive_promotion_candidate", "low_priority_unlabeled")
    out["candidate_priority_band"] = np.where(keep_positive, out["candidate_priority_band"], "P4")
    return out


def summarize_modes(
    raw_mode_df: pd.DataFrame,
    raw_suspicious_df: pd.DataFrame,
    mode_frames: dict[str, pd.DataFrame],
    mode_suspicious_frames: dict[str, pd.DataFrame],
    stored_raw_candidates: pd.DataFrame,
    stored_raw_summary: pd.DataFrame,
    stored_prototypes: pd.DataFrame,
    prototype_df: pd.DataFrame,
    review_batch_positive_keys: set[tuple[str, str, str, str]],
) -> pd.DataFrame:
    raw_positive_count = int(raw_mode_df["candidate_class"].eq("positive_promotion_candidate").sum())
    raw_hard_negative_count = int(raw_mode_df["candidate_class"].eq("hard_negative_review_candidate").sum())
    raw_actionable_count = raw_positive_count + raw_hard_negative_count
    candidate_universe_count = int(len(raw_mode_df))
    prototype_positive_count = int(prototype_df["prototype_pool_name"].eq("positive_boundary_prototype_pool").sum())
    prototype_hard_negative_count = int(prototype_df["prototype_pool_name"].eq("hard_negative_prototype_pool").sum())

    stored_positive_count = int(stored_raw_candidates["candidate_class"].eq("positive_promotion_candidate").sum())
    stored_hard_negative_count = int(stored_raw_candidates["candidate_class"].eq("hard_negative_review_candidate").sum())
    stored_proto_positive_count = int(stored_prototypes["prototype_pool_name"].eq("positive_boundary_prototype_pool").sum())
    stored_proto_hard_negative_count = int(stored_prototypes["prototype_pool_name"].eq("hard_negative_prototype_pool").sum())
    stored_overall = stored_raw_summary.loc[stored_raw_summary["record_type"].eq("overall")].copy()

    raw_alignment_ok = (
        stored_positive_count == raw_positive_count
        and stored_hard_negative_count == raw_hard_negative_count
        and stored_proto_positive_count == prototype_positive_count
        and stored_proto_hard_negative_count == prototype_hard_negative_count
        and (not stored_overall.empty)
        and int(stored_overall.iloc[0]["excluded_run_count"]) == candidate_universe_count
    )

    raw_top50_keys = positive_top_keys(stored_raw_candidates, top_k=50)
    review_batch_top_keys = review_batch_positive_keys

    rows: list[dict[str, object]] = []
    for mode_name in MODE_NAMES:
        mode_df = mode_frames[mode_name]
        suspicious_df = mode_suspicious_frames[mode_name]
        positive_count = int(mode_df["candidate_class"].eq("positive_promotion_candidate").sum())
        hard_negative_count = int(mode_df["candidate_class"].eq("hard_negative_review_candidate").sum())
        actionable_count = positive_count + hard_negative_count
        mode_top50_keys = positive_top_keys(mode_df, top_k=50)
        mode_actionable_suspicious_count = int(
            suspicious_df.loc[suspicious_df["candidate_class"].isin(ACTIONABLE_CLASSES)].shape[0]
        )

        if mode_name == "raw_boundary":
            note = (
                "raw boundary 재구성 결과"
                + ("가 기존 저장 산출물과 정합" if raw_alignment_ok else "가 기존 저장 산출물과 일부 불일치")
            )
        elif mode_name == "clipped_global_boundary":
            note = "global p99 upper clip 후 재계산한 boundary mode"
        elif mode_name == "clipped_site_boundary":
            note = f"site p99 upper clip 후 재계산한 boundary mode (site 최소행={MIN_SITE_ROWS_FOR_SITE_P99}, 부족 시 global fallback)"
        else:
            note = "raw positive boundary 후보와 positive review batch의 교집합만 남긴 fallback mode"

        rows.append(
            {
                "mode_name": mode_name,
                "prototype_pool_positive_count": prototype_positive_count,
                "prototype_pool_hard_negative_count": prototype_hard_negative_count,
                "candidate_universe_count": candidate_universe_count,
                "raw_positive_promotion_candidate_count": raw_positive_count,
                "raw_hard_negative_review_candidate_count": raw_hard_negative_count,
                "positive_promotion_candidate_count": positive_count,
                "hard_negative_review_candidate_count": hard_negative_count,
                "candidate_count_reduction_vs_raw": raw_actionable_count - actionable_count,
                "top50_overlap_with_raw": len(mode_top50_keys & raw_top50_keys),
                "top50_overlap_with_review_batch": len(mode_top50_keys & review_batch_top_keys),
                "suspicious_candidate_count": mode_actionable_suspicious_count,
                "note_ko": note,
            }
        )

    return pd.DataFrame(rows).reindex(columns=SUMMARY_COLS)


def choose_strategy(summary_df: pd.DataFrame, review_batch_positive_count: int) -> pd.DataFrame:
    summary_by_mode = summary_df.set_index("mode_name")
    raw_row = summary_by_mode.loc["raw_boundary"]
    raw_positive_count = int(raw_row["positive_promotion_candidate_count"])
    raw_suspicious_count = int(raw_row["suspicious_candidate_count"])

    viable_rows: list[pd.Series] = []
    for mode_name in ["clipped_global_boundary", "clipped_site_boundary"]:
        row = summary_by_mode.loc[mode_name]
        positive_count = int(row["positive_promotion_candidate_count"])
        hard_negative_count = int(row["hard_negative_review_candidate_count"])
        suspicious_count = int(row["suspicious_candidate_count"])
        reduction_ratio = 0.0 if raw_positive_count == 0 else float(raw_positive_count - positive_count) / float(raw_positive_count)
        suspicious_reduction = raw_suspicious_count - suspicious_count
        if reduction_ratio >= 0.5 and (hard_negative_count > 0 or suspicious_reduction >= max(2, raw_suspicious_count // 2 if raw_suspicious_count > 0 else 2)):
            viable_rows.append(row)

    if viable_rows:
        viable_rows = sorted(
            viable_rows,
            key=lambda row: (
                int(row["positive_promotion_candidate_count"]),
                int(row["suspicious_candidate_count"]),
                -int(row["hard_negative_review_candidate_count"]),
                0 if row.name == "clipped_global_boundary" else 1,
            ),
        )
        chosen = viable_rows[0]
        strategy = "use_clipped_global_boundary" if chosen.name == "clipped_global_boundary" else "use_clipped_site_boundary"
        reason = (
            f"{chosen.name}가 raw 대비 positive candidate를 {int(chosen['candidate_count_reduction_vs_raw'])}건 줄였고, "
            f"suspicious candidate는 {int(chosen['suspicious_candidate_count'])}건으로 낮춰 salvageable하다고 본다."
        )
        return pd.DataFrame([{"recommended_strategy": strategy, "recommended_reason_ko": reason}], columns=STRATEGY_COLS)

    intersection_row = summary_by_mode.loc["boundary_intersection_with_review_batch"]
    if int(intersection_row["positive_promotion_candidate_count"]) > 0:
        reason = (
            "clipped boundary mode들이 raw 대비 충분히 좁아지지 않거나 suspicious burden을 충분히 줄이지 못해, "
            f"positive review batch와의 교집합 {int(intersection_row['positive_promotion_candidate_count'])}건만 우선 사용하는 편이 더 안정적이다."
        )
        return pd.DataFrame(
            [{"recommended_strategy": "use_boundary_intersection_with_review_batch", "recommended_reason_ko": reason}],
            columns=STRATEGY_COLS,
        )

    reason = (
        "raw/clipped/intersection boundary mode 모두 안정적으로 좁혀지지 않아, "
        f"이미 curated된 positive review batch {review_batch_positive_count}건만 사용하는 것이 더 안전하다."
    )
    return pd.DataFrame([{"recommended_strategy": "use_review_batch_only", "recommended_reason_ko": reason}], columns=STRATEGY_COLS)


def save_outputs(root: Path, summary_df: pd.DataFrame, outliers_df: pd.DataFrame, strategy_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    outliers_df.to_csv(share_dir / OUTLIERS_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    strategy_df.to_csv(share_dir / STRATEGY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    stored_raw_candidates = load_existing_raw_candidates(root)
    stored_raw_summary = load_existing_raw_summary(root)
    stored_prototypes = load_stored_prototypes(root)
    review_batch_positive_keys = positive_review_batch_keys(root)
    review_batch_positive_count = len(review_batch_positive_keys)

    raw_mode_df, prototype_df, total_scored_run_count = reconstruct_raw_mode(root)
    raw_mode_df, raw_outliers_df = detect_suspicious_runs(raw_mode_df)

    clipped_global_df = recompute_mode(raw_mode_df, prototype_df, total_scored_run_count, "clipped_global_boundary")
    clipped_global_df, clipped_global_outliers = detect_suspicious_runs(clipped_global_df)

    clipped_site_df = recompute_mode(raw_mode_df, prototype_df, total_scored_run_count, "clipped_site_boundary")
    clipped_site_df, clipped_site_outliers = detect_suspicious_runs(clipped_site_df)

    intersection_df = build_intersection_mode(raw_mode_df, review_batch_positive_keys)
    intersection_df, intersection_outliers = detect_suspicious_runs(intersection_df)

    mode_frames = {
        "raw_boundary": raw_mode_df,
        "clipped_global_boundary": clipped_global_df,
        "clipped_site_boundary": clipped_site_df,
        "boundary_intersection_with_review_batch": intersection_df,
    }
    mode_suspicious_frames = {
        "raw_boundary": raw_outliers_df,
        "clipped_global_boundary": clipped_global_outliers,
        "clipped_site_boundary": clipped_site_outliers,
        "boundary_intersection_with_review_batch": intersection_outliers,
    }

    summary_df = summarize_modes(
        raw_mode_df=raw_mode_df,
        raw_suspicious_df=raw_outliers_df,
        mode_frames=mode_frames,
        mode_suspicious_frames=mode_suspicious_frames,
        stored_raw_candidates=stored_raw_candidates,
        stored_raw_summary=stored_raw_summary,
        stored_prototypes=stored_prototypes,
        prototype_df=prototype_df,
        review_batch_positive_keys=review_batch_positive_keys,
    )
    strategy_df = choose_strategy(summary_df, review_batch_positive_count=review_batch_positive_count)
    save_outputs(root, summary_df, raw_outliers_df, strategy_df)


if __name__ == "__main__":
    main()
