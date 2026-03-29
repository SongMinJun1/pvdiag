#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
KEY_COLS = ["site", "panel_id", "date"]
OUTPUT_COLS = [
    "site",
    "panel_id",
    "date",
    "coverage_mid",
    "coverage_ok_flag",
    "mid_ratio",
    "last_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "v_drop",
    "shadow_like_flag",
    "group_off_like_flag",
    "shape_flag",
    "shape_score",
    "instability_flag",
    "instability_score",
    "electrical_like_flag",
    "open_device_like_flag",
    "local_signal_signature",
    "evidence_reason_code",
    "group_proxy_value",
    "group_proxy_source",
    "topology_confidence",
]
SUMMARY_COLS = [
    "site",
    "row_count",
    "electrical_like_count",
    "open_device_like_count",
    "shape_present_count",
    "instability_present_count",
    "group_key_base_count",
    "panel_id_token_proxy_count",
]
REQUIRED_CORE_COLS = [
    "date",
    "panel_id",
    "coverage_mid",
    "mid_ratio",
    "last_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "v_drop",
    "shadow_like",
    "group_off_like",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize panel_day_evidence_matrix_v1 from panel_day_core without changing official outputs."
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
        default=SITES,
        help="Sites to include. Defaults to the stable known sites.",
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


def fallback_group_key(panel_id: object) -> str:
    parts = normalize_text(panel_id).split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return normalize_text(panel_id)


def to_bool(value: object) -> bool:
    text = normalize_text(value).lower()
    if text in {"1", "true", "t", "yes", "y"}:
        return True
    if text in {"0", "false", "f", "no", "n", ""}:
        return False
    try:
        return float(text) > 0
    except ValueError:
        return False


def to_optional_int_flag(value: object) -> object:
    text = normalize_text(value).lower()
    if not text:
        return pd.NA
    if text in {"1", "true", "t", "yes", "y"}:
        return 1
    if text in {"0", "false", "f", "no", "n"}:
        return 0
    try:
        return 1 if float(text) > 0 else 0
    except ValueError:
        return pd.NA


def build_optional_flag(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series([pd.NA] * len(df), index=df.index, dtype="Int64")
    return df[col].map(to_optional_int_flag).astype("Int64")


def build_optional_score(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series([float("nan")] * len(df), index=df.index, dtype="float64")
    return pd.to_numeric(df[col], errors="coerce")


def classify_output_token(value: float | None) -> str:
    if pd.notna(value) and float(value) <= 0.10:
        return "output_zero_like"
    if pd.notna(value) and 0.10 < float(value) <= 0.80:
        return "output_drop"
    return "output_not_low"


def classify_voltage_token(value: float | None) -> str:
    if pd.notna(value) and float(value) <= 0.10:
        return "voltage_zero_like"
    if pd.notna(value) and 0.10 < float(value) <= 0.85:
        return "voltage_drop"
    return "voltage_not_low"


def classify_current_token(value: float | None) -> str:
    if pd.notna(value) and float(value) <= 0.10:
        return "current_zero_like"
    if pd.notna(value) and 0.10 < float(value) <= 0.85:
        return "current_drop"
    return "current_preserved"


def build_signal_signature(row: pd.Series) -> str:
    tokens = [
        classify_output_token(row.get("mid_ratio")),
        classify_voltage_token(row.get("mid_v_ratio")),
        classify_current_token(row.get("mid_i_ratio")),
    ]
    if int(row.get("shadow_like_flag", 0)) == 1:
        tokens.append("shadow_like")
    if int(row.get("group_off_like_flag", 0)) == 1:
        tokens.append("group_off_like")
    if int(row.get("shape_flag_present", 0)) == 1:
        tokens.append("shape_present")
    if int(row.get("instability_flag_present", 0)) == 1:
        tokens.append("instability_present")
    return "+".join(tokens)


def build_evidence_reason_code(row: pd.Series) -> str:
    if int(row.get("open_device_like_flag", 0)) == 1:
        return "EVID_OPEN_DEVICE"
    if int(row.get("electrical_like_flag", 0)) == 1:
        return "EVID_ELECTRICAL"
    if int(row.get("shape_flag_present", 0)) == 1:
        return "EVID_SHAPE_PERSISTENT"
    if int(row.get("instability_flag_present", 0)) == 1:
        return "EVID_INSTABILITY_PERSISTENT"
    return ""


def load_site_core(root: Path, site: str) -> pd.DataFrame:
    path = root / "data" / site / "out" / "panel_day_core.csv"
    df = read_csv(path)
    ensure_columns(df, REQUIRED_CORE_COLS, f"{site}/panel_day_core.csv")

    df = df.copy()
    df["site"] = site
    df["panel_id"] = df["panel_id"].map(normalize_text)
    df["date"] = df["date"].map(normalize_date)
    df["_row_order"] = range(len(df))

    for col in ["coverage_mid", "mid_ratio", "last_ratio", "mid_v_ratio", "mid_i_ratio", "v_drop"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["shadow_like_flag"] = df["shadow_like"].map(to_bool).astype(int)
    df["group_off_like_flag"] = df["group_off_like"].map(to_bool).astype(int)
    df["coverage_ok_flag"] = (df["coverage_mid"].notna() & df["coverage_mid"].ge(0.50)).astype(int)

    if "group_key_base" not in df.columns:
        df["group_key_base"] = ""
    df["group_key_base"] = df["group_key_base"].map(normalize_text)
    has_group_key_base = df["group_key_base"].ne("")
    df["group_proxy_value"] = df["group_key_base"]
    df.loc[~has_group_key_base, "group_proxy_value"] = df.loc[~has_group_key_base, "panel_id"].map(fallback_group_key)
    df["group_proxy_source"] = "group_key_base"
    df.loc[~has_group_key_base, "group_proxy_source"] = "panel_id_token_proxy"
    df["topology_confidence"] = "high"
    df.loc[~has_group_key_base, "topology_confidence"] = "low"

    df["shape_flag"] = build_optional_flag(df, "shape_flag")
    df["shape_score"] = build_optional_score(df, "shape_score")
    df["instability_flag"] = build_optional_flag(df, "instability_flag")
    df["instability_score"] = build_optional_score(df, "instability_score")
    df["shape_flag_present"] = df["shape_flag"].fillna(0).astype("Int64").eq(1).astype(int)
    df["instability_flag_present"] = df["instability_flag"].fillna(0).astype("Int64").eq(1).astype(int)

    electrical_like = (
        df["coverage_ok_flag"].eq(1)
        & df["shadow_like_flag"].eq(0)
        & df["group_off_like_flag"].eq(0)
        & df["mid_v_ratio"].le(0.75)
        & df["v_drop"].ge(0.28)
        & df["mid_i_ratio"].ge(0.85)
    )
    open_device_like = (
        df["coverage_ok_flag"].eq(1)
        & df["shadow_like_flag"].eq(0)
        & df["group_off_like_flag"].eq(0)
        & df["mid_ratio"].le(0.10)
        & df["mid_v_ratio"].le(0.10)
        & df["v_drop"].ge(0.90)
    )
    df["electrical_like_flag"] = electrical_like.fillna(False).astype(int)
    df["open_device_like_flag"] = open_device_like.fillna(False).astype(int)
    df["local_signal_signature"] = df.apply(build_signal_signature, axis=1)
    df["evidence_reason_code"] = df.apply(build_evidence_reason_code, axis=1)

    return df


def ensure_unique_keys(df: pd.DataFrame) -> None:
    duplicate_rows = df.loc[df.duplicated(subset=KEY_COLS, keep=False), KEY_COLS]
    if duplicate_rows.empty:
        return
    sample = duplicate_rows.head(5).to_dict(orient="records")
    raise SystemExit(f"duplicate site/panel/date keys found in panel_day_core inputs: {sample}")


def build_summary_output(matrix_df: pd.DataFrame, sites: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for site in sites:
        site_df = matrix_df.loc[matrix_df["site"].eq(site)].copy()
        rows.append(
            {
                "site": site,
                "row_count": int(len(site_df)),
                "electrical_like_count": int(site_df["electrical_like_flag"].sum()) if not site_df.empty else 0,
                "open_device_like_count": int(site_df["open_device_like_flag"].sum()) if not site_df.empty else 0,
                "shape_present_count": int(site_df["shape_flag"].fillna(0).astype("Int64").sum()) if not site_df.empty else 0,
                "instability_present_count": int(site_df["instability_flag"].fillna(0).astype("Int64").sum()) if not site_df.empty else 0,
                "group_key_base_count": int(site_df["group_proxy_source"].eq("group_key_base").sum()) if not site_df.empty else 0,
                "panel_id_token_proxy_count": int(site_df["group_proxy_source"].eq("panel_id_token_proxy").sum()) if not site_df.empty else 0,
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_COLS)


def build_outputs(root: Path, sites: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    frames = [load_site_core(root, site) for site in sites]
    if frames:
        matrix_df = pd.concat(frames, ignore_index=True, sort=False)
    else:
        matrix_df = pd.DataFrame(columns=OUTPUT_COLS + ["_row_order"])

    ensure_unique_keys(matrix_df)
    site_rank = {site: idx for idx, site in enumerate(sites)}
    matrix_df["_site_rank"] = matrix_df["site"].map(lambda value: site_rank.get(value, len(site_rank)))
    matrix_df = matrix_df.sort_values(["_site_rank", "_row_order"], ascending=[True, True]).reset_index(drop=True)

    matrix_output = matrix_df.loc[:, OUTPUT_COLS].copy()
    summary_output = build_summary_output(matrix_output, sites)
    return matrix_output, summary_output


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    matrix_output, summary_output = build_outputs(root, list(args.sites))

    out_dir = root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    matrix_output.to_csv(out_dir / "panel_day_evidence_matrix_v1.csv", index=False, encoding="utf-8-sig")
    summary_output.to_csv(out_dir / "panel_day_evidence_matrix_summary_v1.csv", index=False, encoding="utf-8-sig")
    print(
        "panel_day_evidence_matrix_v1="
        f"{len(matrix_output)} panel_day_evidence_matrix_summary_v1={len(summary_output)}"
    )


if __name__ == "__main__":
    main()
