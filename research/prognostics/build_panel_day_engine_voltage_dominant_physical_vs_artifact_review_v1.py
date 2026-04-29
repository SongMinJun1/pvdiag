#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_SHAPE_INPUT = Path(
    "/private/tmp/local_morphology_family_shape_review_check/"
    "panel_day_engine_local_morphology_family_shape_review_v1.csv"
)
DEFAULT_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"

DETAIL_OUTPUT_NAME = "panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_voltage_dominant_physical_vs_artifact_review_summary_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_voltage_dominant_physical_vs_artifact_review_note_v1.md"

SHAPE_REQUIRED_COLS = [
    "shape_case_id",
    "source_candidate_case_id",
    "site",
    "panel_id",
    "family_shape_judgment_bucket",
]

DETAIL_COLS = [
    "review_case_id",
    "source_shape_case_id",
    "source_candidate_case_id",
    "site",
    "panel_id",
    "physical_vs_artifact_bucket",
    "candidate_fault_family_label_ko",
    "review_confidence",
    "two_axis_review_ready_flag",
    "operator_promotion_allowed_flag",
    "engine_patch_candidate_flag",
    "target_vdom_signal_days",
    "first_vdom_signal_date",
    "last_vdom_signal_date",
    "vdom_signal_span_days",
    "target_critical_fault_days_on_vdom_signal",
    "target_event_A_days_on_vdom_signal",
    "target_re_drop_days_on_vdom_signal",
    "target_data_bad_days_on_vdom_signal",
    "target_no_ref_days_on_vdom_signal",
    "target_v_ref_ok_days_on_vdom_signal",
    "target_v_ref_ok_rate",
    "target_subgroup_common_cause_days_on_vdom_signal",
    "target_group_off_like_days_on_vdom_signal",
    "target_median_mid_ratio",
    "target_median_mid_v_ratio",
    "target_median_mid_i_ratio",
    "target_median_coverage",
    "target_median_co_drop_frac",
    "target_max_co_drop_frac",
    "peer_observed_dates",
    "peer_median_vdom_frac",
    "peer_max_vdom_frac",
    "peer_broad_vdom_dates_ge_20pct",
    "peer_median_low_v_frac",
    "peer_max_low_v_frac",
    "peer_broad_low_v_dates_ge_20pct",
    "peer_broad_low_mid_dates_ge_20pct",
    "peer_median_mid_ratio_median",
    "peer_median_mid_v_ratio_median",
    "peer_max_co_drop_frac_median",
    "physical_evidence_score",
    "artifact_evidence_score",
    "required_next_evidence",
    "review_note",
]

SUMMARY_COLS = [
    "physical_vs_artifact_bucket",
    "candidate_fault_family_label_ko",
    "site",
    "cases",
    "two_axis_review_ready_sum",
    "operator_promotion_allowed_sum",
    "engine_patch_candidate_sum",
    "target_vdom_signal_days_sum",
    "physical_evidence_score_sum",
    "artifact_evidence_score_sum",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Separate BR-065 voltage-dominant rows into physical-leaning vs "
            "artifact/reference review buckets without changing production semantics."
        )
    )
    parser.add_argument("--input-manifest", default=None)
    parser.add_argument("--shape-input", type=Path, default=DEFAULT_SHAPE_INPUT)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def resolve_path(base_root: Path, path_value: str | Path) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else base_root / path


def load_input_manifest(base_root: Path, value: str | Path | None) -> tuple[Path | None, dict[str, Any]]:
    if value is None or str(value).strip() == "":
        return None, {}
    path = resolve_path(base_root, value)
    if not path.exists():
        raise FileNotFoundError(f"missing input manifest: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"input manifest must be a JSON object: {path}")
    return path, payload


def manifest_path_value(manifest: dict[str, Any], key: str) -> str:
    raw = manifest.get(key)
    if raw is None and isinstance(manifest.get("inputs"), dict):
        raw = manifest["inputs"].get(key)
    if isinstance(raw, dict):
        for field in ["path", "artifact_path", "static_path"]:
            if raw.get(field):
                return str(raw[field])
        return ""
    return "" if raw is None else str(raw)


def cli_flag_provided(flag: str, argv: list[str]) -> bool:
    return any(item == flag or item.startswith(f"{flag}=") for item in argv)


def resolve_chain_input(
    base_root: Path,
    cli_value: str | Path,
    legacy_default: str | Path,
    manifest: dict[str, Any],
    manifest_key: str,
    cli_flag: str,
    explicit_flags: set[str],
) -> tuple[Path, str]:
    if cli_flag in explicit_flags:
        return resolve_path(base_root, cli_value), "explicit_cli"
    if manifest:
        manifest_value = manifest_path_value(manifest, manifest_key)
        if not manifest_value:
            raise KeyError(
                f"panel-day evidence input manifest is missing `{manifest_key}`; "
                f"pass {cli_flag} explicitly or add inputs.{manifest_key}"
            )
        return resolve_path(base_root, manifest_value), "input_manifest"
    return resolve_path(base_root, legacy_default), "legacy_default"


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


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def require_columns(df: pd.DataFrame, cols: list[str], label: str) -> None:
    missing = [col for col in cols if col not in df.columns]
    if missing:
        raise SystemExit(f"{label} is missing columns: {missing}")


def bool_series(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(False, index=df.index)
    return df[col].map(to_flag)


def numeric_series(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(0.0, index=df.index)
    return pd.to_numeric(df[col], errors="coerce")


def rounded(value: float | int) -> float:
    if pd.isna(value):
        return 0.0
    return round(float(value), 6)


def date_span_days(dates: pd.Series) -> int:
    parsed = pd.to_datetime(dates, errors="coerce").dropna()
    if parsed.empty:
        return 0
    return int((parsed.max() - parsed.min()).days) + 1


def normalize_shape_input(df: pd.DataFrame) -> pd.DataFrame:
    require_columns(df, SHAPE_REQUIRED_COLS, "shape input")
    out = df.loc[df["family_shape_judgment_bucket"].map(normalize_text).eq("voltage_dominant_hard_signal_review")].copy()
    out = out[SHAPE_REQUIRED_COLS].copy()
    for col in SHAPE_REQUIRED_COLS:
        out[col] = out[col].map(normalize_text)
    return out.sort_values(["site", "panel_id"]).reset_index(drop=True)


def classify_physical_vs_artifact(metrics: dict[str, object]) -> tuple[str, str, str, int, int, str, str]:
    target_days = int(metrics["target_vdom_signal_days"])
    target_data_bad_days = int(metrics["target_data_bad_days_on_vdom_signal"])
    target_no_ref_days = int(metrics["target_no_ref_days_on_vdom_signal"])
    target_group_off_days = int(metrics["target_group_off_like_days_on_vdom_signal"])
    target_subgroup_days = int(metrics["target_subgroup_common_cause_days_on_vdom_signal"])
    v_ref_ok_rate = float(metrics["target_v_ref_ok_rate"])
    median_coverage = float(metrics["target_median_coverage"])
    critical_days = int(metrics["target_critical_fault_days_on_vdom_signal"])
    event_days = int(metrics["target_event_A_days_on_vdom_signal"])
    peer_median_vdom_frac = float(metrics["peer_median_vdom_frac"])
    peer_max_vdom_frac = float(metrics["peer_max_vdom_frac"])
    peer_median_low_v_frac = float(metrics["peer_median_low_v_frac"])
    peer_max_low_v_frac = float(metrics["peer_max_low_v_frac"])
    peer_broad_vdom_dates = int(metrics["peer_broad_vdom_dates_ge_20pct"])
    peer_broad_low_v_dates = int(metrics["peer_broad_low_v_dates_ge_20pct"])
    target_max_co_drop_frac = float(metrics["target_max_co_drop_frac"])

    artifact_score = 0
    if target_days > 0 and target_data_bad_days / target_days > 0.05:
        artifact_score += 2
    if target_days > 0 and target_no_ref_days / target_days > 0.05:
        artifact_score += 1
    if v_ref_ok_rate < 0.95:
        artifact_score += 1
    if target_group_off_days > 0 or target_subgroup_days > 0:
        artifact_score += 2
    if peer_broad_vdom_dates > 0 or peer_max_vdom_frac >= 0.20:
        artifact_score += 2
    if peer_broad_low_v_dates > 0 or peer_max_low_v_frac >= 0.20:
        artifact_score += 1
    if target_max_co_drop_frac >= 0.40:
        artifact_score += 1

    physical_score = 0
    if target_days >= 30:
        physical_score += 2
    if peer_median_vdom_frac <= 0.05 and peer_broad_vdom_dates == 0:
        physical_score += 2
    if peer_median_low_v_frac <= 0.05 and peer_broad_low_v_dates == 0:
        physical_score += 1
    if target_data_bad_days == 0:
        physical_score += 1
    if v_ref_ok_rate >= 0.95:
        physical_score += 1
    if median_coverage >= 0.80:
        physical_score += 1
    if critical_days >= 5 or event_days >= 10:
        physical_score += 1

    if artifact_score >= 3 and artifact_score >= physical_score:
        return (
            "artifact_or_reference_risk_hold_review",
            "계측·기준·공통원인 artifact 검토",
            "low",
            physical_score,
            artifact_score,
            "inspect reference/channel/common-cause evidence before physical-family reading",
            "Artifact/reference evidence is too strong for a panel-local physical reading.",
        )
    if physical_score >= 6 and artifact_score <= 1:
        return (
            "physical_leaning_voltage_axis_review",
            "접속 불량·부분 개방 계열 검토",
            "medium",
            physical_score,
            artifact_score,
            "collect waveform/IV or maintenance evidence before thresholding",
            "Panel-local voltage-axis pattern dominates while peer/reference artifact evidence is weak.",
        )
    if physical_score >= 6:
        return (
            "physical_leaning_with_artifact_caution_review",
            "접속 불량·부분 개방 계열 검토",
            "low",
            physical_score,
            artifact_score,
            "resolve co-drop/reference/common-cause cautions before thresholding",
            "Physical evidence is strong, but artifact/common-cause caution remains.",
        )
    return (
        "mixed_physical_artifact_hold_review",
        "unassigned_voltage_axis_review",
        "low",
        physical_score,
        artifact_score,
        "collect additional physical and reference evidence before family assignment",
        "Available evidence does not separate physical fault from artifact strongly enough.",
    )


def summarize_target(site_core: pd.DataFrame, shape_row: pd.Series) -> dict[str, object]:
    panel_id = normalize_text(shape_row["panel_id"])
    site_core = site_core.copy()
    site_core["date"] = site_core["date"].map(normalize_text)
    site_core["panel_id"] = site_core["panel_id"].map(normalize_text)
    for col in [
        "mid_ratio",
        "mid_v_ratio",
        "mid_i_ratio",
        "coverage",
        "co_drop_frac",
    ]:
        site_core[col] = numeric_series(site_core, col)

    target_mask = site_core["panel_id"].eq(panel_id)
    signal_mask = (
        bool_series(site_core, "fault_like_day")
        | bool_series(site_core, "final_fault")
        | bool_series(site_core, "critical_fault")
        | bool_series(site_core, "degraded_candidate")
        | bool_series(site_core, "event_A")
        | bool_series(site_core, "re_drop")
    )
    vdom_mask = (site_core["mid_v_ratio"] < 0.75) & (site_core["mid_i_ratio"] >= 0.85)
    target_vdom_signal_mask = target_mask & signal_mask & vdom_mask
    target_rows = site_core.loc[target_vdom_signal_mask].copy()
    dates = set(target_rows["date"])

    base_metrics: dict[str, object] = {
        "source_shape_case_id": normalize_text(shape_row["shape_case_id"]),
        "source_candidate_case_id": normalize_text(shape_row["source_candidate_case_id"]),
        "site": normalize_text(shape_row["site"]),
        "panel_id": panel_id,
        "target_vdom_signal_days": int(len(target_rows)),
        "first_vdom_signal_date": normalize_text(target_rows["date"].min()) if not target_rows.empty else "",
        "last_vdom_signal_date": normalize_text(target_rows["date"].max()) if not target_rows.empty else "",
        "vdom_signal_span_days": date_span_days(target_rows["date"]) if not target_rows.empty else 0,
        "operator_promotion_allowed_flag": 0,
        "engine_patch_candidate_flag": 0,
    }
    if target_rows.empty:
        base_metrics.update(
            {
                "target_critical_fault_days_on_vdom_signal": 0,
                "target_event_A_days_on_vdom_signal": 0,
                "target_re_drop_days_on_vdom_signal": 0,
                "target_data_bad_days_on_vdom_signal": 0,
                "target_no_ref_days_on_vdom_signal": 0,
                "target_v_ref_ok_days_on_vdom_signal": 0,
                "target_v_ref_ok_rate": 0.0,
                "target_subgroup_common_cause_days_on_vdom_signal": 0,
                "target_group_off_like_days_on_vdom_signal": 0,
                "target_median_mid_ratio": 0.0,
                "target_median_mid_v_ratio": 0.0,
                "target_median_mid_i_ratio": 0.0,
                "target_median_coverage": 0.0,
                "target_median_co_drop_frac": 0.0,
                "target_max_co_drop_frac": 0.0,
                "peer_observed_dates": 0,
                "peer_median_vdom_frac": 0.0,
                "peer_max_vdom_frac": 0.0,
                "peer_broad_vdom_dates_ge_20pct": 0,
                "peer_median_low_v_frac": 0.0,
                "peer_max_low_v_frac": 0.0,
                "peer_broad_low_v_dates_ge_20pct": 0,
                "peer_broad_low_mid_dates_ge_20pct": 0,
                "peer_median_mid_ratio_median": 0.0,
                "peer_median_mid_v_ratio_median": 0.0,
                "peer_max_co_drop_frac_median": 0.0,
            }
        )
    else:
        v_ref_ok_days = int(bool_series(target_rows, "v_ref_ok").sum())
        target_days = int(len(target_rows))
        base_metrics.update(
            {
                "target_critical_fault_days_on_vdom_signal": int(bool_series(target_rows, "critical_fault").sum()),
                "target_event_A_days_on_vdom_signal": int(bool_series(target_rows, "event_A").sum()),
                "target_re_drop_days_on_vdom_signal": int(bool_series(target_rows, "re_drop").sum()),
                "target_data_bad_days_on_vdom_signal": int(bool_series(target_rows, "data_bad").sum()),
                "target_no_ref_days_on_vdom_signal": int(bool_series(target_rows, "no_ref").sum()),
                "target_v_ref_ok_days_on_vdom_signal": v_ref_ok_days,
                "target_v_ref_ok_rate": rounded(v_ref_ok_days / max(target_days, 1)),
                "target_subgroup_common_cause_days_on_vdom_signal": int(
                    bool_series(target_rows, "subgroup_common_cause_candidate").sum()
                ),
                "target_group_off_like_days_on_vdom_signal": int(bool_series(target_rows, "group_off_like").sum()),
                "target_median_mid_ratio": rounded(target_rows["mid_ratio"].median()),
                "target_median_mid_v_ratio": rounded(target_rows["mid_v_ratio"].median()),
                "target_median_mid_i_ratio": rounded(target_rows["mid_i_ratio"].median()),
                "target_median_coverage": rounded(target_rows["coverage"].median()),
                "target_median_co_drop_frac": rounded(target_rows["co_drop_frac"].median()),
                "target_max_co_drop_frac": rounded(target_rows["co_drop_frac"].max()),
            }
        )

        peers = site_core.loc[site_core["date"].isin(dates) & ~target_mask].copy()
        if peers.empty:
            peer_by_date = pd.DataFrame()
        else:
            peers["peer_vdom"] = (peers["mid_v_ratio"] < 0.75) & (peers["mid_i_ratio"] >= 0.85)
            peers["peer_low_v"] = peers["mid_v_ratio"] < 0.75
            peers["peer_low_mid"] = peers["mid_ratio"] < 0.75
            peer_by_date = (
                peers.groupby("date", dropna=False)
                .agg(
                    peer_rows=("panel_id", "count"),
                    peer_vdom=("peer_vdom", "sum"),
                    peer_low_v=("peer_low_v", "sum"),
                    peer_low_mid=("peer_low_mid", "sum"),
                    median_peer_mid=("mid_ratio", "median"),
                    median_peer_v=("mid_v_ratio", "median"),
                    max_peer_codrop=("co_drop_frac", "max"),
                )
                .reset_index()
            )
            peer_by_date["peer_vdom_frac"] = peer_by_date["peer_vdom"] / peer_by_date["peer_rows"].clip(lower=1)
            peer_by_date["peer_low_v_frac"] = peer_by_date["peer_low_v"] / peer_by_date["peer_rows"].clip(lower=1)
            peer_by_date["peer_low_mid_frac"] = peer_by_date["peer_low_mid"] / peer_by_date["peer_rows"].clip(lower=1)
        base_metrics.update(
            {
                "peer_observed_dates": int(len(peer_by_date)),
                "peer_median_vdom_frac": rounded(peer_by_date["peer_vdom_frac"].median()) if len(peer_by_date) else 0.0,
                "peer_max_vdom_frac": rounded(peer_by_date["peer_vdom_frac"].max()) if len(peer_by_date) else 0.0,
                "peer_broad_vdom_dates_ge_20pct": int((peer_by_date["peer_vdom_frac"] >= 0.20).sum())
                if len(peer_by_date)
                else 0,
                "peer_median_low_v_frac": rounded(peer_by_date["peer_low_v_frac"].median()) if len(peer_by_date) else 0.0,
                "peer_max_low_v_frac": rounded(peer_by_date["peer_low_v_frac"].max()) if len(peer_by_date) else 0.0,
                "peer_broad_low_v_dates_ge_20pct": int((peer_by_date["peer_low_v_frac"] >= 0.20).sum())
                if len(peer_by_date)
                else 0,
                "peer_broad_low_mid_dates_ge_20pct": int((peer_by_date["peer_low_mid_frac"] >= 0.20).sum())
                if len(peer_by_date)
                else 0,
                "peer_median_mid_ratio_median": rounded(peer_by_date["median_peer_mid"].median())
                if len(peer_by_date)
                else 0.0,
                "peer_median_mid_v_ratio_median": rounded(peer_by_date["median_peer_v"].median())
                if len(peer_by_date)
                else 0.0,
                "peer_max_co_drop_frac_median": rounded(peer_by_date["max_peer_codrop"].median())
                if len(peer_by_date)
                else 0.0,
            }
        )

    bucket, family_label, confidence, physical_score, artifact_score, next_evidence, note = classify_physical_vs_artifact(
        base_metrics
    )
    base_metrics.update(
        {
            "physical_vs_artifact_bucket": bucket,
            "candidate_fault_family_label_ko": family_label,
            "review_confidence": confidence,
            "two_axis_review_ready_flag": 1 if bucket.startswith("physical_leaning") else 0,
            "physical_evidence_score": physical_score,
            "artifact_evidence_score": artifact_score,
            "required_next_evidence": next_evidence,
            "review_note": note,
        }
    )
    return base_metrics


def build_detail(shape_input: pd.DataFrame, data_root: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    site_cache: dict[str, pd.DataFrame] = {}
    for _, shape_row in shape_input.iterrows():
        site = normalize_text(shape_row["site"])
        if site not in site_cache:
            path = data_root / site / "out" / "panel_day_core.csv"
            site_cache[site] = read_csv(path)
            require_columns(site_cache[site], ["date", "panel_id"], f"{site} panel_day_core")
        rows.append(summarize_target(site_cache[site], shape_row))
    if not rows:
        return pd.DataFrame(columns=DETAIL_COLS)
    detail = pd.DataFrame(rows)
    detail = detail.sort_values(["physical_vs_artifact_bucket", "site", "panel_id"], kind="stable").reset_index(drop=True)
    detail["review_case_id"] = [f"BR067-{idx:03d}" for idx in range(1, len(detail) + 1)]
    return detail.reindex(columns=DETAIL_COLS)


def build_summary(detail: pd.DataFrame) -> pd.DataFrame:
    if detail.empty:
        return pd.DataFrame(columns=SUMMARY_COLS)
    summary = (
        detail.groupby(["physical_vs_artifact_bucket", "candidate_fault_family_label_ko", "site"], dropna=False)
        .agg(
            cases=("review_case_id", "nunique"),
            two_axis_review_ready_sum=("two_axis_review_ready_flag", "sum"),
            operator_promotion_allowed_sum=("operator_promotion_allowed_flag", "sum"),
            engine_patch_candidate_sum=("engine_patch_candidate_flag", "sum"),
            target_vdom_signal_days_sum=("target_vdom_signal_days", "sum"),
            physical_evidence_score_sum=("physical_evidence_score", "sum"),
            artifact_evidence_score_sum=("artifact_evidence_score", "sum"),
        )
        .reset_index()
    )
    return summary.reindex(columns=SUMMARY_COLS).sort_values(["physical_vs_artifact_bucket", "site"])


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


def write_note(
    output_dir: Path,
    detail: pd.DataFrame,
    summary: pd.DataFrame,
    input_manifest_path: Path | None = None,
    input_resolution_sources: dict[str, str] | None = None,
) -> None:
    lines = [
        "# panel_day_engine_voltage_dominant_physical_vs_artifact_review_note_v1",
        "",
        "## Purpose",
        "- Review BR-065 voltage-dominant rows for physical-vs-artifact separation.",
        "- Keep this as a review packet only; do not create operator promotion or engine patch candidates.",
        "",
        "## Guardrails",
        f"- detail rows: `{len(detail)}`",
        f"- two-axis review ready rows: `{int(detail['two_axis_review_ready_flag'].sum()) if len(detail) else 0}`",
        f"- operator promotion allowed sum: `{int(detail['operator_promotion_allowed_flag'].sum()) if len(detail) else 0}`",
        f"- engine patch candidate sum: `{int(detail['engine_patch_candidate_flag'].sum()) if len(detail) else 0}`",
        f"- evidence input manifest: `{input_manifest_path if input_manifest_path else 'not provided'}`",
        "",
        "## Summary",
        dataframe_to_markdown(summary),
        "",
        "## Input Resolution Sources",
        *(
            [f"- `{key}`: `{value}`" for key, value in sorted((input_resolution_sources or {}).items())]
            if input_resolution_sources
            else ["- no manifest-wrapped inputs"]
        ),
        "",
        "## Interpretation",
        "- `physical_leaning_voltage_axis_review` means panel-local voltage-axis evidence is stronger than peer/reference artifact evidence.",
        "- It is not a confirmed fault family and not an operator-facing promotion.",
        "- Any later threshold still needs waveform/IV, maintenance, or stronger two-axis physical evidence plus BR-060/061/062 gates.",
    ]
    (output_dir / NOTE_OUTPUT_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    base_root = Path.cwd()
    input_manifest_path, input_manifest = load_input_manifest(base_root, args.input_manifest)
    argv = sys.argv[1:]
    explicit_flags = {
        flag
        for flag in [
            "--shape-input",
        ]
        if cli_flag_provided(flag, argv)
    }
    shape_path, shape_source = resolve_chain_input(
        base_root,
        args.shape_input,
        DEFAULT_SHAPE_INPUT,
        input_manifest,
        "shape_input",
        "--shape-input",
        explicit_flags,
    )
    input_resolution_sources = {
        "shape_input": shape_source,
    }

    shape_input = normalize_shape_input(read_csv(shape_path))
    detail = build_detail(shape_input, args.data_root)
    summary = build_summary(detail)
    if len(detail) and int(detail["operator_promotion_allowed_flag"].sum()) != 0:
        raise SystemExit("voltage-dominant review must not allow operator promotion")
    if len(detail) and int(detail["engine_patch_candidate_flag"].sum()) != 0:
        raise SystemExit("voltage-dominant review must not allow direct engine patch")
    detail.to_csv(args.output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(args.output_dir, detail, summary, input_manifest_path, input_resolution_sources)


if __name__ == "__main__":
    main()
