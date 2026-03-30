#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
KEY_COLS = ["site", "panel_id", "date"]
CORE_OUTPUT_COLS = [
    "site",
    "panel_id",
    "date",
    "recon_error",
    "dtw_dist",
    "hs_score",
    "mid_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "v_drop",
    "confirmed_fault",
    "critical_fault",
    "final_fault",
    "group_off_like",
    "shadow_like",
]
OUTPUT_COLS = CORE_OUTPUT_COLS + [
    "ews_warning_flag",
    "prefault_B_flag",
    "pre_alarm_flag",
    "local_precursor_any_flag",
    "first_local_precursor_date_per_panel",
    "lead_days_to_final_fault",
    "alert_pattern",
]
SUMMARY_COLS = [
    "site",
    "row_count",
    "ews_warning_day_count",
    "prefault_B_day_count",
    "pre_alarm_day_count",
    "local_precursor_any_day_count",
    "panels_with_any_local_precursor_count",
    "final_fault_panel_count",
    "final_fault_panels_with_prior_local_precursor_count",
]
REQUIRED_CORE_COLS = [
    "date",
    "panel_id",
    "recon_error",
    "dtw_dist",
    "hs_score",
    "mid_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "v_drop",
    "confirmed_fault",
    "critical_fault",
    "final_fault",
    "group_off_like",
    "shadow_like",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize a stable shadow artifact for the panel_day_engine local precursor head using existing outputs only."
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


def to_int_flag(value: object) -> int:
    text = normalize_text(value).lower()
    if text in {"1", "true", "t", "yes", "y"}:
        return 1
    if text in {"0", "false", "f", "no", "n", ""}:
        return 0
    try:
        return 1 if float(text) > 0 else 0
    except ValueError:
        return 0


def normalize_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def normalized_value(value: object) -> object:
    text = normalize_text(value)
    if text == "":
        return ""
    try:
        numeric = float(text)
        return round(numeric, 12)
    except ValueError:
        return text


def load_site_core(root: Path, site: str) -> pd.DataFrame:
    path = root / "data" / site / "out" / "panel_day_core.csv"
    df = read_csv(path)
    ensure_columns(df, REQUIRED_CORE_COLS, f"{site}/panel_day_core.csv")

    df = df.copy()
    df["site"] = site
    df["panel_id"] = df["panel_id"].map(normalize_text)
    df["date"] = df["date"].map(normalize_date)
    df["_row_order"] = range(len(df))

    for col in ["recon_error", "dtw_dist", "hs_score", "mid_ratio", "mid_v_ratio", "mid_i_ratio", "v_drop"]:
        df[col] = normalize_numeric(df[col])
    for col in ["confirmed_fault", "critical_fault", "final_fault", "group_off_like", "shadow_like"]:
        df[col] = df[col].map(to_int_flag).astype(int)

    base = df.loc[:, CORE_OUTPUT_COLS + ["_row_order"]].copy()
    duplicated = base.duplicated(subset=KEY_COLS, keep=False)
    if duplicated.any():
        dup_df = base.loc[duplicated].copy()
        compare_cols = [col for col in CORE_OUTPUT_COLS if col not in KEY_COLS]
        problem_keys: list[str] = []
        keep_rows: list[pd.DataFrame] = []
        for key, group in dup_df.groupby(KEY_COLS, sort=False, dropna=False):
            normalized_rows = {
                tuple(normalized_value(group.iloc[idx][col]) for col in compare_cols)
                for idx in range(len(group))
            }
            if len(normalized_rows) > 1:
                problem_keys.append(f"{key[0]}|{key[1]}|{key[2]}")
                continue
            keep_rows.append(group.nsmallest(1, "_row_order"))
        if problem_keys:
            raise SystemExit(
                "panel_day_core has conflicting duplicates on carried local-precursor shadow columns: "
                + ", ".join(problem_keys[:10])
            )
        deduped = pd.concat(keep_rows, ignore_index=True) if keep_rows else pd.DataFrame(columns=base.columns)
        unique_rows = base.loc[~base.duplicated(subset=KEY_COLS, keep=False)].copy()
        base = pd.concat([unique_rows, deduped], ignore_index=True)

    return base.sort_values(KEY_COLS, kind="stable").reset_index(drop=True)


def load_day_flag_helper(path: Path, flag_name: str, site: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=[*KEY_COLS, flag_name])
    df = read_csv(path)
    required = ["date", "panel_id"]
    ensure_columns(df, required, path.name)
    df = df.copy()
    df["site"] = site
    df["panel_id"] = df["panel_id"].map(normalize_text)
    df["date"] = df["date"].map(normalize_date)
    df[flag_name] = 1
    return (
        df.loc[:, [*KEY_COLS, flag_name]]
        .groupby(KEY_COLS, as_index=False)
        .agg(**{flag_name: (flag_name, "max")})
    )


def load_pre_alarm_helper(path: Path, site: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=[*KEY_COLS, "pre_alarm_flag"])
    df = read_csv(path)
    required = ["panel_id", "any_pre_alarm", "pre_alarm_start"]
    ensure_columns(df, required, path.name)
    df = df.copy()
    df["site"] = site
    df["panel_id"] = df["panel_id"].map(normalize_text)
    df["pre_alarm_start"] = df["pre_alarm_start"].map(normalize_date)
    df["any_pre_alarm"] = df["any_pre_alarm"].map(to_int_flag).astype(int)
    df = df.loc[df["any_pre_alarm"].eq(1) & df["pre_alarm_start"].ne("")].copy()
    if df.empty:
        return pd.DataFrame(columns=[*KEY_COLS, "pre_alarm_flag"])
    df["date"] = df["pre_alarm_start"]
    df["pre_alarm_flag"] = 1
    return (
        df.loc[:, [*KEY_COLS, "pre_alarm_flag"]]
        .groupby(KEY_COLS, as_index=False)
        .agg(pre_alarm_flag=("pre_alarm_flag", "max"))
    )


def alert_pattern(row: pd.Series) -> str:
    flags = {
        "ews": int(row["ews_warning_flag"]) == 1,
        "prefault": int(row["prefault_B_flag"]) == 1,
        "pre_alarm": int(row["pre_alarm_flag"]) == 1,
    }
    if not any(flags.values()):
        return "no_local_precursor"
    if flags["ews"] and not flags["prefault"] and not flags["pre_alarm"]:
        return "ews_only"
    if flags["prefault"] and not flags["ews"] and not flags["pre_alarm"]:
        return "prefault_only"
    if flags["pre_alarm"] and not flags["ews"] and not flags["prefault"]:
        return "pre_alarm_only"
    if flags["ews"] and flags["prefault"] and not flags["pre_alarm"]:
        return "ews_and_prefault"
    if flags["ews"] and flags["pre_alarm"] and not flags["prefault"]:
        return "ews_and_pre_alarm"
    if flags["prefault"] and flags["pre_alarm"] and not flags["ews"]:
        return "prefault_and_pre_alarm"
    return "all_three"


def build_site_rows(root: Path, site: str) -> pd.DataFrame:
    base = load_site_core(root, site)
    out_dir = root / "data" / site / "out"

    ews_df = load_day_flag_helper(out_dir / "ae_simple_ews_warnings.csv", "ews_warning_flag", site)
    prefault_df = load_day_flag_helper(out_dir / "ae_simple_prefault_B_daily.csv", "prefault_B_flag", site)
    pre_alarm_df = load_pre_alarm_helper(out_dir / "ae_simple_panel_alarms.csv", site)

    merged = base.merge(ews_df, on=KEY_COLS, how="left")
    merged = merged.merge(prefault_df, on=KEY_COLS, how="left")
    merged = merged.merge(pre_alarm_df, on=KEY_COLS, how="left")

    for col in ["ews_warning_flag", "prefault_B_flag", "pre_alarm_flag"]:
        merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(0).astype(int)

    merged["local_precursor_any_flag"] = (
        merged[["ews_warning_flag", "prefault_B_flag", "pre_alarm_flag"]].max(axis=1).astype(int)
    )

    merged["date_ts"] = pd.to_datetime(merged["date"], errors="coerce")
    first_precursor = (
        merged.loc[merged["local_precursor_any_flag"].eq(1), ["panel_id", "date_ts"]]
        .groupby("panel_id", sort=False)["date_ts"]
        .min()
    )
    first_final_fault = (
        merged.loc[merged["final_fault"].eq(1), ["panel_id", "date_ts"]]
        .groupby("panel_id", sort=False)["date_ts"]
        .min()
    )
    merged["first_local_precursor_date_per_panel"] = (
        merged["panel_id"].map(first_precursor).dt.date.astype("string").fillna("")
    )
    merged["first_final_fault_date_per_panel"] = merged["panel_id"].map(first_final_fault)
    merged["lead_days_to_final_fault"] = pd.NA
    lead_mask = (
        merged["local_precursor_any_flag"].eq(1)
        & merged["first_final_fault_date_per_panel"].notna()
        & merged["date_ts"].notna()
        & merged["first_final_fault_date_per_panel"].ge(merged["date_ts"])
    )
    merged.loc[lead_mask, "lead_days_to_final_fault"] = (
        merged.loc[lead_mask, "first_final_fault_date_per_panel"] - merged.loc[lead_mask, "date_ts"]
    ).dt.days.astype("Int64")

    merged["alert_pattern"] = merged.apply(alert_pattern, axis=1)
    return merged.loc[:, OUTPUT_COLS + ["first_final_fault_date_per_panel"]].copy()


def build_summary(rows_df: pd.DataFrame, sites: list[str]) -> pd.DataFrame:
    summary_rows: list[dict[str, object]] = []
    for site in sites:
        site_df = rows_df.loc[rows_df["site"].eq(site)].copy()
        first_local = (
            site_df.loc[site_df["first_local_precursor_date_per_panel"].ne(""), ["panel_id", "first_local_precursor_date_per_panel"]]
            .drop_duplicates(subset=["panel_id"])
        )
        first_fault = (
            site_df.loc[site_df["first_final_fault_date_per_panel"].notna(), ["panel_id", "first_final_fault_date_per_panel"]]
            .drop_duplicates(subset=["panel_id"])
        )
        prior_precursor = first_fault.merge(first_local, on="panel_id", how="left")
        prior_precursor["first_local_precursor_date_per_panel"] = pd.to_datetime(
            prior_precursor["first_local_precursor_date_per_panel"], errors="coerce"
        )
        prior_count = int(
            (
                prior_precursor["first_local_precursor_date_per_panel"].notna()
                & prior_precursor["first_local_precursor_date_per_panel"].lt(prior_precursor["first_final_fault_date_per_panel"])
            ).sum()
        )
        summary_rows.append(
            {
                "site": site,
                "row_count": int(len(site_df)),
                "ews_warning_day_count": int(site_df["ews_warning_flag"].sum()),
                "prefault_B_day_count": int(site_df["prefault_B_flag"].sum()),
                "pre_alarm_day_count": int(site_df["pre_alarm_flag"].sum()),
                "local_precursor_any_day_count": int(site_df["local_precursor_any_flag"].sum()),
                "panels_with_any_local_precursor_count": int(site_df.loc[site_df["local_precursor_any_flag"].eq(1), "panel_id"].nunique()),
                "final_fault_panel_count": int(site_df.loc[site_df["final_fault"].eq(1), "panel_id"].nunique()),
                "final_fault_panels_with_prior_local_precursor_count": prior_count,
            }
        )
    return pd.DataFrame(summary_rows, columns=SUMMARY_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    frames = [build_site_rows(root, site) for site in args.sites]
    rows_df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=OUTPUT_COLS)
    rows_df = rows_df.sort_values(KEY_COLS, kind="stable").reset_index(drop=True)
    summary_df = build_summary(rows_df, args.sites)

    rows_df.loc[:, OUTPUT_COLS].to_csv(
        share_dir / "panel_day_engine_local_precursor_shadow_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    summary_df.to_csv(
        share_dir / "panel_day_engine_local_precursor_shadow_summary_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )


if __name__ == "__main__":
    main()
