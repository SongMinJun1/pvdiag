#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pickle
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.prognostics.external_eval_gpvs import _baseline_noae_weights


FAULT_PANEL_EVENT_AUDIT_NAME = "panel_day_engine_fault_panel_event_audit_v1.csv"
PANEL_MULTIAXIS_VERDICT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"

OUTPUT_AUDIT_NAME = "panel_day_engine_gpvs_detailed_type_inference_v1.csv"
OUTPUT_SUMMARY_NAME = "panel_day_engine_gpvs_detailed_type_summary_v1.csv"

OVERALL_METRICS_CANDIDATE_NAMES = [
    "EXTERNAL_GPVS_METRICS.csv",
]
BYTYPE_HEAD_CANDIDATE_NAMES = [
    "EXTERNAL_GPVS_ENSEMBLE2_BYTYPE_METRICS.csv",
    "EXTERNAL_GPVS_BYTYPE_METRICS.csv",
]
SERIALIZED_ARTIFACT_PATTERNS = [
    "data/gpvs/out/*BYTYPE*.joblib",
    "data/gpvs/out/*BYTYPE*.pkl",
    "data/gpvs/out/*BYTYPE*.pickle",
    "_share/**/*BYTYPE*.joblib",
    "_share/**/*BYTYPE*.pkl",
    "_share/**/*BYTYPE*.pickle",
]

RAW_SCORE_COLS = [
    "level_drop_raw",
    "v_drop_raw",
    "dtw_raw",
    "hs_raw",
    "ae_raw",
]
NOAE_RAW_COLS = [
    "level_drop_raw",
    "v_drop_raw",
    "dtw_raw",
    "hs_raw",
]
DIRECT_SCORE_MAP = {
    "level_drop_like": "level_drop_raw",
    "v_drop_like": "v_drop_raw",
    "dtw_like": "dtw_raw",
    "hs_like": "hs_raw",
    "ae_like": "ae_raw",
}
SUPPORTED_SCORE_NAMES = set(DIRECT_SCORE_MAP) | {
    "ensemble_raw",
    "ensemble_top2_raw",
    "ensemble_weighted_noae_raw",
}

AUDIT_COLS = [
    "site",
    "panel_id",
    "event_reference_date",
    "gpvs_family_label",
    "gpvs_detailed_fault_code",
    "gpvs_detailed_fault_score",
    "gpvs_detailed_fault_rank2_code",
    "gpvs_detailed_fault_margin",
    "gpvs_detailed_fault_status_ko",
    "gpvs_detailed_fault_reason_ko",
]

SUMMARY_COLS = [
    "고장패널수",
    "세부fault_부착수",
    "세부fault_판정유보수",
    "세부fault_추론불가수",
    "note_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Infer GPVS detailed fault codes (F1~F7) for real fault panels using the stored GPVS by-type path."
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
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    for column in normalized.columns:
        if normalized[column].dtype == object:
            normalized[column] = normalized[column].map(normalize_text)
    return normalized


def relative_str(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def choose_serialized_artifact(root: Path) -> Path | None:
    hits: list[Path] = []
    for pattern in SERIALIZED_ARTIFACT_PATTERNS:
        hits.extend(root.glob(pattern))
    unique_hits = sorted({path.resolve() for path in hits if path.is_file()})
    return Path(unique_hits[0]) if unique_hits else None


def load_serialized_head(path: Path) -> tuple[pd.DataFrame, str] | None:
    suffix = path.suffix.lower()
    try:
        if suffix in {".pkl", ".pickle"}:
            with path.open("rb") as fp:
                payload = pickle.load(fp)
        elif suffix == ".joblib":
            import joblib  # type: ignore

            payload = joblib.load(path)
        else:
            return None
    except Exception:
        return None

    if not isinstance(payload, dict):
        return None
    head_df = payload.get("preferred_head")
    if not isinstance(head_df, pd.DataFrame):
        return None
    required = ["fault_code", "score", "threshold_fpr1"]
    if any(column not in head_df.columns for column in required):
        return None
    return head_df.copy(), f"serialized:{path.name}"


def choose_head_metric_path(root: Path) -> Path:
    for name in BYTYPE_HEAD_CANDIDATE_NAMES:
        path = root / "data" / "gpvs" / "out" / name
        if path.exists():
            return path
    raise SystemExit(
        "missing GPVS by-type metric artifact. expected one of: "
        + ", ".join(f"data/gpvs/out/{name}" for name in BYTYPE_HEAD_CANDIDATE_NAMES)
    )


def load_metric_head(path: Path) -> tuple[pd.DataFrame, str]:
    df = normalize_frame(read_csv(path))
    ensure_columns(df, ["fault_type", "sid", "score", "threshold_fpr1", "ap", "roc_auc"], path.name)
    usable = df.loc[pd.to_numeric(df["sid"], errors="coerce").fillna(0).gt(0)].copy()
    usable["fault_code"] = usable["fault_type"].map(normalize_text).str.extract(r"^(F[1-7])")[0]
    usable = usable.loc[usable["fault_code"].map(normalize_text).ne("")].copy()
    usable = usable.loc[usable["score"].map(normalize_text).isin(SUPPORTED_SCORE_NAMES)].copy()
    if usable.empty:
        raise SystemExit(f"{path.name} does not contain usable by-type rows for F1~F7")
    preferred = (
        usable.sort_values(
            ["fault_code", "ap", "roc_auc", "threshold_fpr1"],
            ascending=[True, False, False, True],
            na_position="last",
        )
        .groupby("fault_code", as_index=False)
        .head(1)
        .reset_index(drop=True)
    )
    if preferred["fault_code"].nunique() < 7:
        missing = sorted({"F1", "F2", "F3", "F4", "F5", "F6", "F7"} - set(preferred["fault_code"]))
        raise SystemExit(f"{path.name} missing preferred rows for fault codes: {missing}")
    return preferred, f"metric:{path.name}"


def load_overall_weights(root: Path) -> tuple[dict[str, float], str]:
    for name in OVERALL_METRICS_CANDIDATE_NAMES:
        path = root / "data" / "gpvs" / "out" / name
        if not path.exists():
            continue
        df = normalize_frame(read_csv(path))
        ensure_columns(df, ["score", "roc_auc"], name)
        return _baseline_noae_weights(df), relative_str(path, root)
    equal_weight = 1.0 / len(NOAE_RAW_COLS)
    return {column: equal_weight for column in NOAE_RAW_COLS}, "equal_weight_fallback"


def build_inputs(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    share_dir = root / "_share"
    fault_df = normalize_frame(read_csv(share_dir / FAULT_PANEL_EVENT_AUDIT_NAME))
    verdict_df = normalize_frame(read_csv(share_dir / PANEL_MULTIAXIS_VERDICT_NAME))
    ensure_columns(
        fault_df,
        [
            "site",
            "panel_id",
            "strict_trigger_date",
            "first_final_fault_date",
        ],
        FAULT_PANEL_EVENT_AUDIT_NAME,
    )
    ensure_columns(
        verdict_df,
        [
            "site",
            "panel_id",
            "패널고장여부_ko",
            "GPVS_참고유형_ko",
        ],
        PANEL_MULTIAXIS_VERDICT_NAME,
    )
    return fault_df, verdict_df


def choose_reference_date(row: pd.Series) -> str:
    strict_trigger = normalize_text(row.get("strict_trigger_date", ""))
    if strict_trigger:
        return strict_trigger
    first_final = normalize_text(row.get("first_final_fault_date", ""))
    if first_final:
        return first_final
    return ""


def map_panel_day_axes(panel_df: pd.DataFrame) -> pd.DataFrame:
    work = panel_df.copy()
    mid_ratio = pd.to_numeric(work.get("mid_ratio"), errors="coerce")
    v_drop = pd.to_numeric(work.get("v_drop"), errors="coerce")
    dtw_dist = pd.to_numeric(work.get("dtw_dist"), errors="coerce")
    hs_score = pd.to_numeric(work.get("hs_score"), errors="coerce")
    recon_error = pd.to_numeric(work.get("recon_error"), errors="coerce")

    work["level_drop_raw"] = (1.0 - mid_ratio).clip(lower=0)
    work["v_drop_raw"] = v_drop.clip(lower=0)
    work["dtw_raw"] = dtw_dist
    work["hs_raw"] = hs_score
    work["ae_raw"] = recon_error
    return work


def robust_z(event_value: float, baseline: pd.Series) -> float:
    vals = pd.to_numeric(baseline, errors="coerce").dropna().to_numpy(dtype=float)
    if len(vals) == 0 or not np.isfinite(event_value):
        return np.nan
    median = float(np.median(vals))
    mad = float(np.median(np.abs(vals - median)))
    if not np.isfinite(mad) or mad <= 1e-12:
        return np.nan
    return float((event_value - median) / (1.4826 * mad))


def compute_panel_event_scores(
    panel_df: pd.DataFrame,
    reference_date: str,
    noae_weights: dict[str, float],
) -> tuple[dict[str, float], str]:
    if panel_df.empty:
        return {}, "panel_day_core row 없음"

    work = map_panel_day_axes(panel_df)
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    ref_ts = pd.to_datetime(reference_date, errors="coerce")
    if pd.isna(ref_ts):
        return {}, "event_reference_date 해석 실패"

    event_rows = work.loc[work["date"].eq(ref_ts)].copy()
    if event_rows.empty:
        return {}, "event_reference_date 와 일치하는 panel_day_core row 없음"
    event_row = event_rows.iloc[0]
    pre_df = work.loc[work["date"].lt(ref_ts)].copy()

    z_scores: dict[str, float] = {}
    raw_scores: dict[str, float] = {}
    for column in RAW_SCORE_COLS:
        event_value = pd.to_numeric(pd.Series([event_row.get(column)]), errors="coerce").iloc[0]
        raw_scores[column] = float(event_value) if pd.notna(event_value) else np.nan
        z_scores[column] = robust_z(float(event_value) if pd.notna(event_value) else np.nan, pre_df[column])

    all_z = np.asarray([z_scores[column] for column in RAW_SCORE_COLS], dtype=float)
    finite_all = all_z[np.isfinite(all_z)]
    noae_z = np.asarray([z_scores[column] for column in NOAE_RAW_COLS], dtype=float)
    finite_noae = noae_z[np.isfinite(noae_z)]

    ensemble_raw = float(np.mean(finite_all)) if len(finite_all) else np.nan
    ensemble_top2_raw = (
        float(np.mean(np.sort(finite_noae)[-min(2, len(finite_noae)) :])) if len(finite_noae) else np.nan
    )
    weight_vec = np.asarray([float(noae_weights.get(column, 0.0)) for column in NOAE_RAW_COLS], dtype=float)
    valid_mask = np.isfinite(noae_z) & np.isfinite(weight_vec) & (weight_vec > 0)
    ensemble_weighted_noae_raw = (
        float(np.average(noae_z[valid_mask], weights=weight_vec[valid_mask])) if valid_mask.any() else np.nan
    )

    score_map = {
        **raw_scores,
        "ensemble_raw": ensemble_raw,
        "ensemble_top2_raw": ensemble_top2_raw,
        "ensemble_weighted_noae_raw": ensemble_weighted_noae_raw,
    }
    if not any(np.isfinite(value) for value in score_map.values()):
        return {}, "pre-event baseline 부족으로 z-score 기반 by-type 추론 불가"
    return score_map, ""


def score_value_for_head(score_name: str, score_map: dict[str, float]) -> float:
    if score_name in DIRECT_SCORE_MAP:
        return score_map.get(DIRECT_SCORE_MAP[score_name], np.nan)
    return score_map.get(score_name, np.nan)


def infer_rows(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    fault_df, verdict_df = build_inputs(root)
    fault_only = fault_df.copy()
    if len(fault_only) != 6:
        raise SystemExit(f"{FAULT_PANEL_EVENT_AUDIT_NAME} must contain exactly 6 current fault panels, found {len(fault_only)}")

    verdict_fault_only = verdict_df.loc[verdict_df["패널고장여부_ko"].eq("고장"), ["site", "panel_id", "GPVS_참고유형_ko"]].copy()
    if len(verdict_fault_only) != 6:
        raise SystemExit(
            f"{PANEL_MULTIAXIS_VERDICT_NAME} must contain exactly 6 fault rows by 패널고장여부_ko==고장, found {len(verdict_fault_only)}"
        )
    if verdict_fault_only.duplicated(subset=["site", "panel_id"]).any():
        raise SystemExit(f"{PANEL_MULTIAXIS_VERDICT_NAME} fault rows must be unique by (site, panel_id)")
    family_by_key = {
        (normalize_text(row["site"]), normalize_text(row["panel_id"])): normalize_text(row["GPVS_참고유형_ko"])
        for row in verdict_fault_only.to_dict(orient="records")
    }

    serialized_path = choose_serialized_artifact(root)
    if serialized_path is not None:
        maybe_loaded = load_serialized_head(serialized_path)
        if maybe_loaded is not None:
            preferred_head, head_source = maybe_loaded
        else:
            preferred_head, head_source = load_metric_head(choose_head_metric_path(root))
    else:
        preferred_head, head_source = load_metric_head(choose_head_metric_path(root))

    noae_weights, weight_source = load_overall_weights(root)

    panel_core_cache: dict[str, pd.DataFrame] = {}
    audit_rows: list[dict[str, object]] = []

    for row in fault_only.to_dict(orient="records"):
        site = normalize_text(row["site"])
        panel_id = normalize_text(row["panel_id"])
        key = (site, panel_id)
        if key not in family_by_key:
            raise SystemExit(f"{PANEL_MULTIAXIS_VERDICT_NAME} missing fault-panel row for {site}/{panel_id}")

        reference_date = choose_reference_date(pd.Series(row))
        gpvs_family_label = family_by_key[key]
        reason_prefix = f"head_source={head_source}; weight_source={weight_source}"

        if not reference_date:
            audit_rows.append(
                {
                    "site": site,
                    "panel_id": panel_id,
                    "event_reference_date": "",
                    "gpvs_family_label": gpvs_family_label,
                    "gpvs_detailed_fault_code": "",
                    "gpvs_detailed_fault_score": "",
                    "gpvs_detailed_fault_rank2_code": "",
                    "gpvs_detailed_fault_margin": "",
                    "gpvs_detailed_fault_status_ko": "추론불가",
                    "gpvs_detailed_fault_reason_ko": f"{reason_prefix}; strict_trigger_date/first_final_fault_date 모두 없음",
                }
            )
            continue

        if site not in panel_core_cache:
            panel_core_path = root / "data" / site / "out" / "panel_day_core.csv"
            panel_core_cache[site] = normalize_frame(read_csv(panel_core_path))
            ensure_columns(
                panel_core_cache[site],
                ["date", "panel_id", "mid_ratio", "v_drop", "dtw_dist", "hs_score", "recon_error"],
                panel_core_path.name,
            )

        panel_df = panel_core_cache[site].loc[panel_core_cache[site]["panel_id"].eq(panel_id)].copy()
        score_map, infer_error = compute_panel_event_scores(panel_df, reference_date, noae_weights)
        if infer_error:
            audit_rows.append(
                {
                    "site": site,
                    "panel_id": panel_id,
                    "event_reference_date": reference_date,
                    "gpvs_family_label": gpvs_family_label,
                    "gpvs_detailed_fault_code": "",
                    "gpvs_detailed_fault_score": "",
                    "gpvs_detailed_fault_rank2_code": "",
                    "gpvs_detailed_fault_margin": "",
                    "gpvs_detailed_fault_status_ko": "추론불가",
                    "gpvs_detailed_fault_reason_ko": f"{reason_prefix}; {infer_error}",
                }
            )
            continue

        candidate_rows: list[dict[str, Any]] = []
        for head_row in preferred_head.to_dict(orient="records"):
            score_name = normalize_text(head_row["score"])
            score_value = score_value_for_head(score_name, score_map)
            threshold = pd.to_numeric(pd.Series([head_row["threshold_fpr1"]]), errors="coerce").iloc[0]
            threshold_ratio = (
                float(score_value / threshold)
                if np.isfinite(score_value) and pd.notna(threshold) and float(threshold) > 0
                else np.nan
            )
            candidate_rows.append(
                {
                    "fault_code": normalize_text(head_row["fault_code"]),
                    "fault_type": normalize_text(head_row.get("fault_type", "")),
                    "score_name": score_name,
                    "score_value": float(score_value) if np.isfinite(score_value) else np.nan,
                    "threshold_fpr1": float(threshold) if pd.notna(threshold) else np.nan,
                    "threshold_ratio": threshold_ratio,
                    "ap": pd.to_numeric(pd.Series([head_row.get("ap")]), errors="coerce").iloc[0],
                    "roc_auc": pd.to_numeric(pd.Series([head_row.get("roc_auc")]), errors="coerce").iloc[0],
                }
            )

        candidates_df = pd.DataFrame(candidate_rows)
        usable = candidates_df.loc[candidates_df["threshold_ratio"].map(np.isfinite)].copy()
        if usable.empty:
            audit_rows.append(
                {
                    "site": site,
                    "panel_id": panel_id,
                    "event_reference_date": reference_date,
                    "gpvs_family_label": gpvs_family_label,
                    "gpvs_detailed_fault_code": "",
                    "gpvs_detailed_fault_score": "",
                    "gpvs_detailed_fault_rank2_code": "",
                    "gpvs_detailed_fault_margin": "",
                    "gpvs_detailed_fault_status_ko": "추론불가",
                    "gpvs_detailed_fault_reason_ko": f"{reason_prefix}; usable fault-code score가 없음",
                }
            )
            continue

        usable = usable.sort_values(
            ["threshold_ratio", "score_value", "ap", "roc_auc", "fault_code"],
            ascending=[False, False, False, False, True],
            na_position="last",
        ).reset_index(drop=True)
        top = usable.iloc[0].to_dict()
        second = usable.iloc[1].to_dict() if len(usable) > 1 else None
        top_ratio = float(top["threshold_ratio"])
        top_score = float(top["score_value"])
        top_threshold = float(top["threshold_fpr1"])
        second_ratio = float(second["threshold_ratio"]) if second is not None else np.nan
        margin = float(top_ratio - second_ratio) if np.isfinite(top_ratio) and np.isfinite(second_ratio) else np.nan

        status = "부착" if top_ratio >= 1.0 else "판정유보"
        reason = (
            f"{reason_prefix}; preferred_score={top['score_name']}; "
            f"score={top_score:.6g}; threshold_fpr1={top_threshold:.6g}; "
            f"threshold_ratio={top_ratio:.6g}"
        )
        if second is not None and np.isfinite(second_ratio):
            reason += f"; rank2={second['fault_code']} ratio={second_ratio:.6g}"
        if status == "판정유보":
            reason += "; stored by-type threshold 미충족"

        audit_rows.append(
            {
                "site": site,
                "panel_id": panel_id,
                "event_reference_date": reference_date,
                "gpvs_family_label": gpvs_family_label,
                "gpvs_detailed_fault_code": normalize_text(top["fault_code"]),
                "gpvs_detailed_fault_score": top_score,
                "gpvs_detailed_fault_rank2_code": normalize_text(second["fault_code"]) if second is not None else "",
                "gpvs_detailed_fault_margin": margin,
                "gpvs_detailed_fault_status_ko": status,
                "gpvs_detailed_fault_reason_ko": reason,
            }
        )

    audit_df = pd.DataFrame(audit_rows).reindex(columns=AUDIT_COLS)
    if len(audit_df) != 6:
        raise SystemExit(f"{OUTPUT_AUDIT_NAME} must contain exactly 6 fault-panel rows, found {len(audit_df)}")
    if audit_df.duplicated(subset=["site", "panel_id"]).any():
        raise SystemExit(f"{OUTPUT_AUDIT_NAME} must be unique by (site, panel_id)")

    attached = int(audit_df["gpvs_detailed_fault_status_ko"].eq("부착").sum())
    deferred = int(audit_df["gpvs_detailed_fault_status_ko"].eq("판정유보").sum())
    impossible = int(audit_df["gpvs_detailed_fault_status_ko"].eq("추론불가").sum())

    summary_df = pd.DataFrame(
        [
            {
                "고장패널수": int(len(audit_df)),
                "세부fault_부착수": attached,
                "세부fault_판정유보수": deferred,
                "세부fault_추론불가수": impossible,
                "note_ko": (
                    "실패 panel bridge 대신 GPVS by-type metric artifact를 frozen head로 읽고, "
                    "real panel event date에서 panel_day_core raw axis(level_drop_raw/v_drop_raw/dtw_raw/hs_raw/ae_raw)를 재구성해 "
                    "threshold_fpr1 기존 규칙으로 부착/판정유보/추론불가를 나눈다. "
                    "synthetic PVFAULT_labels_day panel_id direct bridge는 여기서 쓰지 않는다."
                ),
            }
        ]
    ).reindex(columns=SUMMARY_COLS)
    return audit_df, summary_df


def write_outputs(root: Path, audit_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    audit_df.to_csv(share_dir / OUTPUT_AUDIT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / OUTPUT_SUMMARY_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    audit_df, summary_df = infer_rows(root)
    write_outputs(root, audit_df, summary_df)


if __name__ == "__main__":
    main()
