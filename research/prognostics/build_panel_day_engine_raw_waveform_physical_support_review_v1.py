#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_REVIEW_INPUT = Path(
    "/private/tmp/voltage_dominant_physical_vs_artifact_review_check/"
    "panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.csv"
)
DEFAULT_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"

DETAIL_OUTPUT_NAME = "panel_day_engine_raw_waveform_physical_support_review_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_raw_waveform_physical_support_review_summary_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_raw_waveform_physical_support_review_note_v1.md"

REVIEW_REQUIRED_COLS = [
    "review_case_id",
    "source_shape_case_id",
    "source_candidate_case_id",
    "site",
    "panel_id",
    "physical_vs_artifact_bucket",
]

DETAIL_COLS = [
    "raw_support_case_id",
    "source_review_case_id",
    "source_shape_case_id",
    "source_candidate_case_id",
    "site",
    "panel_id",
    "raw_waveform_support_bucket",
    "candidate_fault_family_label_ko",
    "support_confidence",
    "operator_promotion_allowed_flag",
    "engine_patch_candidate_flag",
    "target_vdom_signal_days",
    "raw_file_found_days",
    "raw_file_missing_days",
    "raw_target_found_days",
    "raw_active_timestamp_rows",
    "raw_active_days",
    "raw_median_v_ratio",
    "raw_p10_v_ratio",
    "raw_p90_v_ratio",
    "raw_median_i_ratio",
    "raw_p10_i_ratio",
    "raw_p90_i_ratio",
    "raw_median_p_ratio",
    "raw_p10_p_ratio",
    "raw_p90_p_ratio",
    "raw_vlow_iok_timestamp_frac",
    "raw_vlow_iok_days",
    "raw_daily_support_days",
    "raw_daily_support_frac",
    "raw_median_target_v_in",
    "raw_median_peer_v_in",
    "raw_median_target_i_out",
    "raw_median_peer_i_out",
    "raw_median_target_p",
    "raw_median_peer_p",
    "physical_support_score",
    "raw_evidence_limitation_score",
    "required_next_evidence",
    "review_note",
]

SUMMARY_COLS = [
    "raw_waveform_support_bucket",
    "candidate_fault_family_label_ko",
    "site",
    "cases",
    "operator_promotion_allowed_sum",
    "engine_patch_candidate_sum",
    "target_vdom_signal_days_sum",
    "raw_file_found_days_sum",
    "raw_active_timestamp_rows_sum",
    "raw_daily_support_days_sum",
    "physical_support_score_sum",
    "raw_evidence_limitation_score_sum",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Use raw long-format panel CSVs to check whether BR-067 voltage-axis "
            "candidates have waveform-level physical support."
        )
    )
    parser.add_argument("--review-input", type=Path, default=DEFAULT_REVIEW_INPUT)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def to_flag(value: object) -> bool:
    text = normalize_text(value).lower()
    if text in {"1", "true", "t", "yes", "y"}:
        return True
    if text in {"0", "false", "f", "no", "n", ""}:
        return False
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return False if pd.isna(numeric) else bool(float(numeric) > 0)


def numeric_series(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(0.0, index=df.index)
    return pd.to_numeric(df[col], errors="coerce")


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def require_columns(df: pd.DataFrame, cols: list[str], label: str) -> None:
    missing = [col for col in cols if col not in df.columns]
    if missing:
        raise SystemExit(f"{label} is missing columns: {missing}")


def rounded(value: object) -> float:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0.0 if pd.isna(numeric) else round(float(numeric), 6)


def quantile(series: pd.Series, q: float) -> float:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    return 0.0 if clean.empty else round(float(clean.quantile(q)), 6)


def normalize_review_input(df: pd.DataFrame) -> pd.DataFrame:
    require_columns(df, REVIEW_REQUIRED_COLS, "review input")
    out = df.loc[df["physical_vs_artifact_bucket"].map(normalize_text).eq("physical_leaning_voltage_axis_review")].copy()
    out = out[REVIEW_REQUIRED_COLS].copy()
    for col in REVIEW_REQUIRED_COLS:
        out[col] = out[col].map(normalize_text)
    return out.sort_values(["site", "panel_id"]).reset_index(drop=True)


def panel_core_vdom_signal_rows(site_core: pd.DataFrame, panel_id: str) -> pd.DataFrame:
    core = site_core.copy()
    core["panel_id"] = core["panel_id"].map(normalize_text)
    core["date"] = core["date"].map(normalize_text)
    for col in ["mid_v_ratio", "mid_i_ratio"]:
        core[col] = numeric_series(core, col)
    signal_mask = (
        core.get("fault_like_day", pd.Series(False, index=core.index)).map(to_flag)
        | core.get("final_fault", pd.Series(False, index=core.index)).map(to_flag)
        | core.get("critical_fault", pd.Series(False, index=core.index)).map(to_flag)
        | core.get("degraded_candidate", pd.Series(False, index=core.index)).map(to_flag)
        | core.get("event_A", pd.Series(False, index=core.index)).map(to_flag)
        | core.get("re_drop", pd.Series(False, index=core.index)).map(to_flag)
    )
    return core.loc[
        core["panel_id"].eq(panel_id)
        & signal_mask
        & (core["mid_v_ratio"] < 0.75)
        & (core["mid_i_ratio"] >= 0.85)
    ].copy()


def raw_timestamp_ratios(raw_path: Path, panel_id: str) -> pd.DataFrame:
    if not raw_path.exists():
        return pd.DataFrame()
    raw = pd.read_csv(raw_path, low_memory=False, encoding="utf-8-sig")
    require_columns(raw, ["date_time", "map_type", "map_id", "i_out (A)", "v_in (V)", "p (W)"], f"raw file {raw_path}")
    raw = raw.loc[raw["map_type"].map(normalize_text).eq("panel")].copy()
    raw["map_id"] = raw["map_id"].map(normalize_text)
    for col in ["i_out (A)", "v_in (V)", "p (W)"]:
        raw[col] = numeric_series(raw, col)
    target = raw.loc[raw["map_id"].eq(panel_id)].copy()
    if target.empty:
        return pd.DataFrame()
    peers = raw.loc[~raw["map_id"].eq(panel_id)].copy()
    if peers.empty:
        return pd.DataFrame()
    peer = (
        peers.groupby("date_time", dropna=False)
        .agg(
            peer_v_in=("v_in (V)", "median"),
            peer_i_out=("i_out (A)", "median"),
            peer_p=("p (W)", "median"),
            peer_rows=("map_id", "count"),
        )
        .reset_index()
    )
    merged = target.merge(peer, on="date_time", how="left")
    active = merged.loc[
        (merged["peer_v_in"] > 5.0)
        & (merged["peer_i_out"].abs() > 0.05)
        & (merged["peer_p"] > 0.5)
    ].copy()
    if active.empty:
        return pd.DataFrame()
    active["raw_v_ratio"] = active["v_in (V)"] / active["peer_v_in"]
    active["raw_i_ratio"] = active["i_out (A)"] / active["peer_i_out"]
    active["raw_p_ratio"] = active["p (W)"] / active["peer_p"]
    active["raw_vlow_iok"] = (active["raw_v_ratio"] <= 0.75) & (active["raw_i_ratio"] >= 0.85)
    return active[
        [
            "date_time",
            "v_in (V)",
            "i_out (A)",
            "p (W)",
            "peer_v_in",
            "peer_i_out",
            "peer_p",
            "raw_v_ratio",
            "raw_i_ratio",
            "raw_p_ratio",
            "raw_vlow_iok",
        ]
    ].copy()


def classify_support(metrics: dict[str, object]) -> tuple[str, str, str, int, int, str, str]:
    target_days = int(metrics["target_vdom_signal_days"])
    found_days = int(metrics["raw_file_found_days"])
    target_found_days = int(metrics["raw_target_found_days"])
    active_rows = int(metrics["raw_active_timestamp_rows"])
    median_v = float(metrics["raw_median_v_ratio"])
    median_i = float(metrics["raw_median_i_ratio"])
    median_p = float(metrics["raw_median_p_ratio"])
    vlow_iok_frac = float(metrics["raw_vlow_iok_timestamp_frac"])
    daily_support_frac = float(metrics["raw_daily_support_frac"])

    limitation_score = 0
    if target_days <= 0:
        limitation_score += 3
    elif found_days / max(target_days, 1) < 0.80:
        limitation_score += 2
    if target_found_days / max(found_days, 1) < 0.90:
        limitation_score += 2
    if active_rows < 500:
        limitation_score += 2

    support_score = 0
    if found_days / max(target_days, 1) >= 0.95:
        support_score += 2
    if target_found_days / max(found_days, 1) >= 0.95:
        support_score += 1
    if active_rows >= 1000:
        support_score += 1
    if median_v <= 0.75:
        support_score += 2
    if median_i >= 0.85:
        support_score += 2
    if median_p <= 0.85:
        support_score += 1
    if vlow_iok_frac >= 0.50:
        support_score += 2
    if daily_support_frac >= 0.50:
        support_score += 1

    if support_score >= 10 and limitation_score == 0:
        return (
            "raw_waveform_physical_support_review",
            "접속 불량·부분 개방 계열 검토",
            "medium",
            support_score,
            limitation_score,
            "collect independent IV/waveform or maintenance confirmation before thresholding",
            "Raw timestamps support persistent low-voltage / current-preserved panel-local morphology.",
        )
    if support_score >= 8:
        return (
            "raw_waveform_physical_support_with_limitations_review",
            "접속 불량·부분 개방 계열 검토",
            "low",
            support_score,
            limitation_score,
            "resolve raw coverage limitations and collect independent confirmation before thresholding",
            "Raw waveform support is present, but coverage or active-row limitations remain.",
        )
    return (
        "raw_waveform_support_insufficient_hold",
        "unassigned_voltage_axis_review",
        "low",
        support_score,
        limitation_score,
        "collect more raw waveform evidence before physical-family reading",
        "Raw waveform evidence is not strong enough for physical-support review.",
    )


def summarize_review_row(site_core: pd.DataFrame, data_root: Path, review_row: pd.Series) -> dict[str, object]:
    site = normalize_text(review_row["site"])
    panel_id = normalize_text(review_row["panel_id"])
    vdom_rows = panel_core_vdom_signal_rows(site_core, panel_id)
    raw_frames: list[pd.DataFrame] = []
    found_days = 0
    target_found_days = 0
    for _, core_row in vdom_rows.iterrows():
        source_csv = normalize_text(core_row.get("source_csv", ""))
        raw_path = data_root / site / "raw" / source_csv
        if raw_path.exists():
            found_days += 1
        ratios = raw_timestamp_ratios(raw_path, panel_id) if source_csv else pd.DataFrame()
        if not ratios.empty:
            target_found_days += 1
            ratios["date"] = normalize_text(core_row["date"])
            raw_frames.append(ratios)

    if raw_frames:
        raw = pd.concat(raw_frames, ignore_index=True)
        daily = (
            raw.groupby("date", dropna=False)
            .agg(
                daily_median_v_ratio=("raw_v_ratio", "median"),
                daily_median_i_ratio=("raw_i_ratio", "median"),
                daily_vlow_iok_frac=("raw_vlow_iok", "mean"),
            )
            .reset_index()
        )
        daily["daily_support"] = (
            (daily["daily_median_v_ratio"] <= 0.75)
            & (daily["daily_median_i_ratio"] >= 0.85)
            & (daily["daily_vlow_iok_frac"] >= 0.50)
        )
    else:
        raw = pd.DataFrame()
        daily = pd.DataFrame()

    target_days = int(len(vdom_rows))
    metrics: dict[str, object] = {
        "source_review_case_id": normalize_text(review_row["review_case_id"]),
        "source_shape_case_id": normalize_text(review_row["source_shape_case_id"]),
        "source_candidate_case_id": normalize_text(review_row["source_candidate_case_id"]),
        "site": site,
        "panel_id": panel_id,
        "target_vdom_signal_days": target_days,
        "raw_file_found_days": found_days,
        "raw_file_missing_days": max(target_days - found_days, 0),
        "raw_target_found_days": target_found_days,
        "raw_active_timestamp_rows": int(len(raw)),
        "raw_active_days": int(raw["date"].nunique()) if len(raw) else 0,
        "raw_median_v_ratio": rounded(raw["raw_v_ratio"].median()) if len(raw) else 0.0,
        "raw_p10_v_ratio": quantile(raw["raw_v_ratio"], 0.10) if len(raw) else 0.0,
        "raw_p90_v_ratio": quantile(raw["raw_v_ratio"], 0.90) if len(raw) else 0.0,
        "raw_median_i_ratio": rounded(raw["raw_i_ratio"].median()) if len(raw) else 0.0,
        "raw_p10_i_ratio": quantile(raw["raw_i_ratio"], 0.10) if len(raw) else 0.0,
        "raw_p90_i_ratio": quantile(raw["raw_i_ratio"], 0.90) if len(raw) else 0.0,
        "raw_median_p_ratio": rounded(raw["raw_p_ratio"].median()) if len(raw) else 0.0,
        "raw_p10_p_ratio": quantile(raw["raw_p_ratio"], 0.10) if len(raw) else 0.0,
        "raw_p90_p_ratio": quantile(raw["raw_p_ratio"], 0.90) if len(raw) else 0.0,
        "raw_vlow_iok_timestamp_frac": rounded(raw["raw_vlow_iok"].mean()) if len(raw) else 0.0,
        "raw_vlow_iok_days": int(raw.loc[raw["raw_vlow_iok"], "date"].nunique()) if len(raw) else 0,
        "raw_daily_support_days": int(daily["daily_support"].sum()) if len(daily) else 0,
        "raw_daily_support_frac": rounded(daily["daily_support"].mean()) if len(daily) else 0.0,
        "raw_median_target_v_in": rounded(raw["v_in (V)"].median()) if len(raw) else 0.0,
        "raw_median_peer_v_in": rounded(raw["peer_v_in"].median()) if len(raw) else 0.0,
        "raw_median_target_i_out": rounded(raw["i_out (A)"].median()) if len(raw) else 0.0,
        "raw_median_peer_i_out": rounded(raw["peer_i_out"].median()) if len(raw) else 0.0,
        "raw_median_target_p": rounded(raw["p (W)"].median()) if len(raw) else 0.0,
        "raw_median_peer_p": rounded(raw["peer_p"].median()) if len(raw) else 0.0,
        "operator_promotion_allowed_flag": 0,
        "engine_patch_candidate_flag": 0,
    }
    bucket, family_label, confidence, support_score, limitation_score, next_evidence, note = classify_support(metrics)
    metrics.update(
        {
            "raw_waveform_support_bucket": bucket,
            "candidate_fault_family_label_ko": family_label,
            "support_confidence": confidence,
            "physical_support_score": support_score,
            "raw_evidence_limitation_score": limitation_score,
            "required_next_evidence": next_evidence,
            "review_note": note,
        }
    )
    return metrics


def build_detail(review_input: pd.DataFrame, data_root: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    site_cache: dict[str, pd.DataFrame] = {}
    for _, review_row in review_input.iterrows():
        site = normalize_text(review_row["site"])
        if site not in site_cache:
            core_path = data_root / site / "out" / "panel_day_core.csv"
            site_cache[site] = read_csv(core_path)
            require_columns(site_cache[site], ["date", "panel_id", "source_csv"], f"{site} panel_day_core")
        rows.append(summarize_review_row(site_cache[site], data_root, review_row))
    if not rows:
        return pd.DataFrame(columns=DETAIL_COLS)
    detail = pd.DataFrame(rows)
    detail = detail.sort_values(["raw_waveform_support_bucket", "site", "panel_id"], kind="stable").reset_index(drop=True)
    detail["raw_support_case_id"] = [f"BR068-{idx:03d}" for idx in range(1, len(detail) + 1)]
    return detail.reindex(columns=DETAIL_COLS)


def build_summary(detail: pd.DataFrame) -> pd.DataFrame:
    if detail.empty:
        return pd.DataFrame(columns=SUMMARY_COLS)
    summary = (
        detail.groupby(["raw_waveform_support_bucket", "candidate_fault_family_label_ko", "site"], dropna=False)
        .agg(
            cases=("raw_support_case_id", "nunique"),
            operator_promotion_allowed_sum=("operator_promotion_allowed_flag", "sum"),
            engine_patch_candidate_sum=("engine_patch_candidate_flag", "sum"),
            target_vdom_signal_days_sum=("target_vdom_signal_days", "sum"),
            raw_file_found_days_sum=("raw_file_found_days", "sum"),
            raw_active_timestamp_rows_sum=("raw_active_timestamp_rows", "sum"),
            raw_daily_support_days_sum=("raw_daily_support_days", "sum"),
            physical_support_score_sum=("physical_support_score", "sum"),
            raw_evidence_limitation_score_sum=("raw_evidence_limitation_score", "sum"),
        )
        .reset_index()
    )
    return summary.reindex(columns=SUMMARY_COLS).sort_values(["raw_waveform_support_bucket", "site"])


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    header = "| " + " | ".join(df.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(df.columns)) + " |"
    rows = [
        "| " + " | ".join(normalize_text(row[col]) for col in df.columns) + " |"
        for row in df.to_dict(orient="records")
    ]
    return "\n".join([header, separator] + rows)


def write_note(output_dir: Path, detail: pd.DataFrame, summary: pd.DataFrame) -> None:
    lines = [
        "# panel_day_engine_raw_waveform_physical_support_review_note_v1",
        "",
        "## Purpose",
        "- Check BR-067 physical-leaning voltage-axis rows against raw long-format waveform proxies.",
        "- Keep this as support evidence only; it is not a confirmed fault-family threshold.",
        "",
        "## Guardrails",
        f"- detail rows: `{len(detail)}`",
        f"- operator promotion allowed sum: `{int(detail['operator_promotion_allowed_flag'].sum()) if len(detail) else 0}`",
        f"- engine patch candidate sum: `{int(detail['engine_patch_candidate_flag'].sum()) if len(detail) else 0}`",
        "",
        "## Summary",
        dataframe_to_markdown(summary),
        "",
        "## Interpretation",
        "- `raw_waveform_physical_support_review` means raw timestamps support low-voltage / current-preserved morphology.",
        "- This still requires independent IV/waveform, maintenance, or field confirmation before thresholding.",
        "- Any later semantic patch still needs BR-060 runbook, BR-061 scorecard, and BR-062 compare.",
    ]
    (output_dir / NOTE_OUTPUT_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    review_input = normalize_review_input(read_csv(args.review_input))
    detail = build_detail(review_input, args.data_root)
    summary = build_summary(detail)
    if len(detail) and int(detail["operator_promotion_allowed_flag"].sum()) != 0:
        raise SystemExit("raw waveform support review must not allow operator promotion")
    if len(detail) and int(detail["engine_patch_candidate_flag"].sum()) != 0:
        raise SystemExit("raw waveform support review must not allow direct engine patch")
    detail.to_csv(args.output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(args.output_dir, detail, summary)


if __name__ == "__main__":
    main()
