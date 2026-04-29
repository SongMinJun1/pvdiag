#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_PACKET_INPUT = Path(
    "/private/tmp/fault_family_judgment_candidate_packet_check/"
    "panel_day_engine_fault_family_judgment_candidate_packet_v1.csv"
)
DEFAULT_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"

DETAIL_OUTPUT_NAME = "panel_day_engine_local_morphology_family_shape_review_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_local_morphology_family_shape_review_summary_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_local_morphology_family_shape_review_note_v1.md"

PACKET_REQUIRED_COLS = [
    "candidate_case_id",
    "site",
    "panel_id",
    "judgment_bucket",
    "recovery_bucket",
    "synchrony_bucket",
    "max_co_drop_frac",
    "candidate_evidence_axis_count",
]

DETAIL_COLS = [
    "shape_case_id",
    "source_candidate_case_id",
    "site",
    "panel_id",
    "family_shape_judgment_bucket",
    "candidate_family_label_ko",
    "candidate_family_track",
    "shape_confidence",
    "two_axis_review_ready_flag",
    "operator_promotion_allowed_flag",
    "engine_patch_candidate_flag",
    "signal_day_count",
    "first_signal_date",
    "last_signal_date",
    "signal_span_days",
    "fault_like_days",
    "final_fault_days",
    "critical_fault_days",
    "degraded_candidate_days",
    "event_A_days",
    "re_drop_days",
    "recovered_sustained_days",
    "data_bad_days",
    "subgroup_common_cause_days",
    "low_mid_days",
    "severe_low_mid_days",
    "low_i_days",
    "low_v_days",
    "diode_vi_shape_days",
    "voltage_dominant_low_days",
    "both_low_vi_days",
    "median_signal_mid_ratio",
    "median_signal_mid_v_ratio",
    "median_signal_mid_i_ratio",
    "min_signal_mid_ratio",
    "max_signal_co_drop_frac",
    "recovery_bucket",
    "synchrony_bucket",
    "max_co_drop_frac",
    "source_candidate_evidence_axis_count",
    "required_next_evidence",
    "review_note",
]

SUMMARY_COLS = [
    "family_shape_judgment_bucket",
    "candidate_family_label_ko",
    "site",
    "cases",
    "two_axis_review_ready_sum",
    "operator_promotion_allowed_sum",
    "engine_patch_candidate_sum",
    "critical_fault_days_sum",
    "event_A_days_sum",
    "re_drop_days_sum",
    "low_mid_days_sum",
    "voltage_dominant_low_days_sum",
    "diode_vi_shape_days_sum",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Review BR-064 local morphology candidates for family-shape evidence "
            "without changing production semantics."
        )
    )
    parser.add_argument("--input-manifest", default=None)
    parser.add_argument("--packet-input", type=Path, default=DEFAULT_PACKET_INPUT)
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


def to_float(value: object) -> float:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0.0 if pd.isna(numeric) else float(numeric)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def require_columns(df: pd.DataFrame, cols: list[str], label: str) -> None:
    missing = [col for col in cols if col not in df.columns]
    if missing:
        raise SystemExit(f"{label} is missing columns: {missing}")


def normalize_packet(df: pd.DataFrame) -> pd.DataFrame:
    require_columns(df, PACKET_REQUIRED_COLS, "packet input")
    out = df.loc[df["judgment_bucket"].map(normalize_text).eq("local_morphology_family_candidate_review")].copy()
    out = out[PACKET_REQUIRED_COLS].copy()
    for col in ["candidate_case_id", "site", "panel_id", "judgment_bucket", "recovery_bucket", "synchrony_bucket"]:
        out[col] = out[col].map(normalize_text)
    for col in ["max_co_drop_frac", "candidate_evidence_axis_count"]:
        out[col] = out[col].map(to_float)
    return out.sort_values(["site", "panel_id"]).reset_index(drop=True)


def bool_series(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(False, index=df.index)
    return df[col].map(to_flag)


def numeric_series(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(0.0, index=df.index)
    return pd.to_numeric(df[col], errors="coerce")


def date_span_days(dates: pd.Series) -> int:
    parsed = pd.to_datetime(dates, errors="coerce").dropna()
    if parsed.empty:
        return 0
    return int((parsed.max() - parsed.min()).days) + 1


def classify_shape(metrics: dict[str, object]) -> tuple[str, str, str, str, int, str, str]:
    signal_days = int(metrics["signal_day_count"])
    critical_days = int(metrics["critical_fault_days"])
    fault_like_days = int(metrics["fault_like_days"])
    final_days = int(metrics["final_fault_days"])
    degraded_days = int(metrics["degraded_candidate_days"])
    event_days = int(metrics["event_A_days"])
    re_drop_days = int(metrics["re_drop_days"])
    low_mid_days = int(metrics["low_mid_days"])
    severe_days = int(metrics["severe_low_mid_days"])
    diode_days = int(metrics["diode_vi_shape_days"])
    voltage_days = int(metrics["voltage_dominant_low_days"])
    data_bad_days = int(metrics["data_bad_days"])

    hard_days = critical_days + fault_like_days + final_days
    if signal_days <= 0:
        return (
            "no_shape_evidence_hold",
            "unassigned_family_needs_shape_review",
            "unassigned_family_needs_shape_review",
            "low",
            0,
            "collect signal-day evidence before family assignment",
            "No signal days were available for shape review.",
        )
    if voltage_days >= 10 and hard_days >= 5:
        confidence = "medium" if data_bad_days <= max(3, signal_days * 0.2) else "low"
        return (
            "voltage_dominant_hard_signal_review",
            "접속 불량·부분 개방 또는 계측 전압축 이상",
            "open_connection_or_measurement_voltage_axis",
            confidence,
            1,
            "separate partial-open voltage signature from measurement/reference artifact",
            f"Voltage-dominant low pattern has {voltage_days} days and hard signal days {hard_days}.",
        )
    if diode_days >= 2 and hard_days > 0:
        return (
            "diode_substring_shape_review",
            "다이오드·서브스트링 계열",
            "diode_substring",
            "medium",
            1,
            "confirm VI-shape repeatability and exclude site/common-cause context",
            f"VI-shape has {diode_days} high-voltage/low-current days with hard signal context.",
        )
    if low_mid_days >= 10 and (degraded_days >= 2 or event_days >= 10 or critical_days >= 5):
        return (
            "degradation_or_shading_shape_review",
            "열화·오염·음영 계열",
            "degradation_soiling_shadow",
            "medium",
            1,
            "check persistence, time-of-day repeatability, and low site synchrony",
            f"Repeated low-mid morphology has {low_mid_days} days, severe days {severe_days}.",
        )
    if re_drop_days >= 2 and hard_days == 0 and low_mid_days <= 2 and degraded_days <= 1:
        return (
            "recovery_recurrence_only_no_family_shape_hold",
            "unassigned_family_needs_shape_review",
            "unassigned_family_needs_shape_review",
            "low",
            0,
            "keep as recurrence/recovery observation until VI or degradation shape appears",
            f"Re-drop/recovery is recurrent ({re_drop_days} days), but hard/family-shape evidence is absent.",
        )
    if event_days >= 10 and hard_days == 0:
        return (
            "eventA_recovery_shape_weak_review",
            "unassigned_family_needs_shape_review",
            "unassigned_family_needs_shape_review",
            "low",
            0,
            "inspect event_A morphology manually; do not threshold automatically",
            f"event_A is frequent ({event_days} days), but hard/family-shape evidence is still weak.",
        )
    return (
        "weak_family_shape_hold",
        "unassigned_family_needs_shape_review",
        "unassigned_family_needs_shape_review",
        "low",
        0,
        "collect additional shape evidence before thresholding",
        "Available morphology does not meet a family-specific review threshold.",
    )


def summarize_panel(panel_df: pd.DataFrame, packet_row: pd.Series) -> dict[str, object]:
    if panel_df.empty:
        metrics: dict[str, object] = {
            "signal_day_count": 0,
            "first_signal_date": "",
            "last_signal_date": "",
            "signal_span_days": 0,
        }
    else:
        bool_cols = {
            "fault_like_day": bool_series(panel_df, "fault_like_day"),
            "final_fault": bool_series(panel_df, "final_fault"),
            "critical_fault": bool_series(panel_df, "critical_fault"),
            "degraded_candidate": bool_series(panel_df, "degraded_candidate"),
            "event_A": bool_series(panel_df, "event_A"),
            "re_drop": bool_series(panel_df, "re_drop"),
            "recovered_sustained": bool_series(panel_df, "recovered_sustained"),
            "data_bad": bool_series(panel_df, "data_bad"),
            "subgroup_common_cause_candidate": bool_series(panel_df, "subgroup_common_cause_candidate"),
        }
        signal_mask = (
            bool_cols["fault_like_day"]
            | bool_cols["final_fault"]
            | bool_cols["critical_fault"]
            | bool_cols["degraded_candidate"]
            | bool_cols["event_A"]
            | bool_cols["re_drop"]
        )
        signal_df = panel_df.loc[signal_mask].copy()
        for col in ["mid_ratio", "mid_v_ratio", "mid_i_ratio", "co_drop_frac"]:
            signal_df[col] = numeric_series(signal_df, col)

        mid = numeric_series(signal_df, "mid_ratio")
        mid_v = numeric_series(signal_df, "mid_v_ratio")
        mid_i = numeric_series(signal_df, "mid_i_ratio")
        co_drop = numeric_series(signal_df, "co_drop_frac")
        metrics = {
            "signal_day_count": int(signal_mask.sum()),
            "first_signal_date": normalize_text(signal_df["date"].min()) if not signal_df.empty else "",
            "last_signal_date": normalize_text(signal_df["date"].max()) if not signal_df.empty else "",
            "signal_span_days": date_span_days(signal_df["date"]) if not signal_df.empty else 0,
            "fault_like_days": int(bool_cols["fault_like_day"].sum()),
            "final_fault_days": int(bool_cols["final_fault"].sum()),
            "critical_fault_days": int(bool_cols["critical_fault"].sum()),
            "degraded_candidate_days": int(bool_cols["degraded_candidate"].sum()),
            "event_A_days": int(bool_cols["event_A"].sum()),
            "re_drop_days": int(bool_cols["re_drop"].sum()),
            "recovered_sustained_days": int(bool_cols["recovered_sustained"].sum()),
            "data_bad_days": int(bool_cols["data_bad"].sum()),
            "subgroup_common_cause_days": int(bool_cols["subgroup_common_cause_candidate"].sum()),
            "low_mid_days": int((mid < 0.75).sum()),
            "severe_low_mid_days": int((mid < 0.60).sum()),
            "low_i_days": int((mid_i < 0.65).sum()),
            "low_v_days": int((mid_v < 0.75).sum()),
            "diode_vi_shape_days": int(((mid_v >= 0.85) & (mid_i <= 0.65)).sum()),
            "voltage_dominant_low_days": int(((mid_v < 0.75) & (mid_i >= 0.85)).sum()),
            "both_low_vi_days": int(((mid_v < 0.75) & (mid_i < 0.75)).sum()),
            "median_signal_mid_ratio": round(float(mid.median()), 6) if mid.notna().any() else 0.0,
            "median_signal_mid_v_ratio": round(float(mid_v.median()), 6) if mid_v.notna().any() else 0.0,
            "median_signal_mid_i_ratio": round(float(mid_i.median()), 6) if mid_i.notna().any() else 0.0,
            "min_signal_mid_ratio": round(float(mid.min()), 6) if mid.notna().any() else 0.0,
            "max_signal_co_drop_frac": round(float(co_drop.max()), 6) if co_drop.notna().any() else 0.0,
        }
    defaults = [
        "fault_like_days",
        "final_fault_days",
        "critical_fault_days",
        "degraded_candidate_days",
        "event_A_days",
        "re_drop_days",
        "recovered_sustained_days",
        "data_bad_days",
        "subgroup_common_cause_days",
        "low_mid_days",
        "severe_low_mid_days",
        "low_i_days",
        "low_v_days",
        "diode_vi_shape_days",
        "voltage_dominant_low_days",
        "both_low_vi_days",
        "median_signal_mid_ratio",
        "median_signal_mid_v_ratio",
        "median_signal_mid_i_ratio",
        "min_signal_mid_ratio",
        "max_signal_co_drop_frac",
    ]
    for col in defaults:
        metrics.setdefault(col, 0)
    bucket, family_label, family_track, confidence, ready, next_evidence, note = classify_shape(metrics)
    metrics.update(
        {
            "family_shape_judgment_bucket": bucket,
            "candidate_family_label_ko": family_label,
            "candidate_family_track": family_track,
            "shape_confidence": confidence,
            "two_axis_review_ready_flag": ready,
            "operator_promotion_allowed_flag": 0,
            "engine_patch_candidate_flag": 0,
            "required_next_evidence": next_evidence,
            "review_note": note,
            "source_candidate_case_id": normalize_text(packet_row["candidate_case_id"]),
            "site": normalize_text(packet_row["site"]),
            "panel_id": normalize_text(packet_row["panel_id"]),
            "recovery_bucket": normalize_text(packet_row["recovery_bucket"]),
            "synchrony_bucket": normalize_text(packet_row["synchrony_bucket"]),
            "max_co_drop_frac": to_float(packet_row["max_co_drop_frac"]),
            "source_candidate_evidence_axis_count": to_float(packet_row["candidate_evidence_axis_count"]),
        }
    )
    return metrics


def build_detail(packet: pd.DataFrame, data_root: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    site_cache: dict[str, pd.DataFrame] = {}
    for _, packet_row in packet.iterrows():
        site = normalize_text(packet_row["site"])
        if site not in site_cache:
            panel_core = data_root / site / "out" / "panel_day_core.csv"
            site_cache[site] = read_csv(panel_core)
            require_columns(site_cache[site], ["date", "panel_id"], f"{site} panel_day_core")
            site_cache[site]["panel_id"] = site_cache[site]["panel_id"].map(normalize_text)
        panel_id = normalize_text(packet_row["panel_id"])
        panel_df = site_cache[site].loc[site_cache[site]["panel_id"].eq(panel_id)].copy()
        rows.append(summarize_panel(panel_df, packet_row))
    if not rows:
        return pd.DataFrame(columns=DETAIL_COLS)
    detail = pd.DataFrame(rows)
    detail = detail.sort_values(["family_shape_judgment_bucket", "site", "panel_id"], kind="stable").reset_index(drop=True)
    detail["shape_case_id"] = [f"BR065-{idx:03d}" for idx in range(1, len(detail) + 1)]
    return detail.reindex(columns=DETAIL_COLS)


def build_summary(detail: pd.DataFrame) -> pd.DataFrame:
    if detail.empty:
        return pd.DataFrame(columns=SUMMARY_COLS)
    summary = (
        detail.groupby(["family_shape_judgment_bucket", "candidate_family_label_ko", "site"], dropna=False)
        .agg(
            cases=("shape_case_id", "nunique"),
            two_axis_review_ready_sum=("two_axis_review_ready_flag", "sum"),
            operator_promotion_allowed_sum=("operator_promotion_allowed_flag", "sum"),
            engine_patch_candidate_sum=("engine_patch_candidate_flag", "sum"),
            critical_fault_days_sum=("critical_fault_days", "sum"),
            event_A_days_sum=("event_A_days", "sum"),
            re_drop_days_sum=("re_drop_days", "sum"),
            low_mid_days_sum=("low_mid_days", "sum"),
            voltage_dominant_low_days_sum=("voltage_dominant_low_days", "sum"),
            diode_vi_shape_days_sum=("diode_vi_shape_days", "sum"),
        )
        .reset_index()
    )
    return summary.reindex(columns=SUMMARY_COLS).sort_values(["family_shape_judgment_bucket", "site"])


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
        "# panel_day_engine_local_morphology_family_shape_review_note_v1",
        "",
        "## Purpose",
        "- Inspect BR-064 local morphology candidates for family-shape evidence.",
        "- Keep shape review separate from operator promotion and engine patch decisions.",
        "- Do not infer performance improvement from morphology buckets.",
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
        "- `recovery_recurrence_only_no_family_shape_hold` rows have recurrence/recovery evidence but no defensible family shape yet.",
        "- `voltage_dominant_hard_signal_review` rows are useful review candidates, but must separate partial-open physics from measurement/reference artifacts.",
        "- Any later semantic patch still needs BR-060 runbook, BR-061 scorecard, and BR-062 compare.",
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
            "--packet-input",
        ]
        if cli_flag_provided(flag, argv)
    }
    packet_path, packet_source = resolve_chain_input(
        base_root,
        args.packet_input,
        DEFAULT_PACKET_INPUT,
        input_manifest,
        "packet_input",
        "--packet-input",
        explicit_flags,
    )
    input_resolution_sources = {
        "packet_input": packet_source,
    }

    packet = normalize_packet(read_csv(packet_path))
    detail = build_detail(packet, args.data_root)
    summary = build_summary(detail)
    if int(detail["operator_promotion_allowed_flag"].sum()) != 0:
        raise SystemExit("local morphology shape review must not allow operator promotion")
    if int(detail["engine_patch_candidate_flag"].sum()) != 0:
        raise SystemExit("local morphology shape review must not allow direct engine patch")

    detail.to_csv(args.output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(args.output_dir, detail, summary, input_manifest_path, input_resolution_sources)


if __name__ == "__main__":
    main()
