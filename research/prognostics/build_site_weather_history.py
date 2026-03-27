#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ADDRESS_COLS = ["site", "address", "weather_enabled", "note"]
WEATHER_DAILY_COLS = [
    "site",
    "date",
    "weather_tag",
    "sun_hours",
    "rain_flag",
    "cloud_flag",
    "weather_confidence",
    "note",
]
HISTORY_COLS = [
    "site",
    "date",
    "score_window_flag",
    "weather_available",
    "weather_tag",
    "sun_hours",
    "rain_flag",
    "cloud_flag",
    "weather_confidence",
    "weather_source",
    "weather_missing_reason",
    "note",
]
COVERAGE_COLS = [
    "site",
    "score_window_days",
    "weather_available_days",
    "missing_weather_days",
    "coverage_rate",
    "missing_address_flag",
]
REQUEST_COLS = ["site", "address", "date", "reason"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build full score-window site weather history sidecars.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to project root.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def normalized_text(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def ensure_columns(df: pd.DataFrame, expected: list[str], name: str) -> pd.DataFrame:
    missing = [col for col in expected if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")
    return df.copy()


def parse_site_config(path: Path) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip()] = value.strip()
    required = ["site", "train_end", "out_dir"]
    missing = [key for key in required if key not in parsed or not parsed[key]]
    if missing:
        raise SystemExit(f"{path} missing required config keys: {missing}")
    return parsed


def load_site_configs(config_dir: Path) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for path in sorted(config_dir.glob("*.yaml")):
        rows.append(parse_site_config(path))
    if not rows:
        raise SystemExit(f"no site configs found under {config_dir}")
    return pd.DataFrame(rows)


def load_addresses(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=ADDRESS_COLS)
    addresses = ensure_columns(read_csv(path), ADDRESS_COLS, str(path))
    addresses = addresses[ADDRESS_COLS].copy()
    addresses["site"] = normalized_text(addresses["site"])
    addresses["address"] = normalized_text(addresses["address"])
    addresses["weather_enabled"] = normalized_text(addresses["weather_enabled"])
    addresses["note"] = normalized_text(addresses["note"])
    return addresses.drop_duplicates(["site"], keep="last")


def load_manual_weather(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=WEATHER_DAILY_COLS + ["weather_row_has_payload", "weather_source"])
    weather = ensure_columns(read_csv(path), WEATHER_DAILY_COLS, str(path))
    weather = weather[WEATHER_DAILY_COLS].copy()
    weather["site"] = normalized_text(weather["site"])
    weather["date"] = normalized_text(weather["date"])
    for col in ["weather_tag", "sun_hours", "rain_flag", "cloud_flag", "weather_confidence", "note"]:
        weather[col] = weather[col].fillna("")
    weather["weather_row_has_payload"] = (
        weather[["weather_tag", "sun_hours", "rain_flag", "cloud_flag", "weather_confidence", "note"]]
        .astype(str)
        .apply(lambda col: col.str.strip())
        .ne("")
        .any(axis=1)
    )
    weather["weather_source"] = weather.apply(derive_weather_source, axis=1)
    return weather.drop_duplicates(["site", "date"], keep="last")


def derive_weather_source(row: pd.Series) -> str:
    note = str(row.get("note", "") or "").strip().lower()
    if not bool(row.get("weather_row_has_payload", False)):
        return ""
    if "observed_api" in note:
        return "observed_api"
    if "manual_entry" in note or "manual" in note:
        return "manual_entry"
    return "unknown"


def load_latest_raw_dates(configs: pd.DataFrame, root: Path) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for _, row in configs.iterrows():
        summary_path = root / row["out_dir"] / "latest_site_summary.csv"
        summary = read_csv(summary_path)
        if "latest_date" not in summary.columns:
            raise SystemExit(f"{summary_path} missing latest_date")
        latest_date = normalized_text(summary["latest_date"]).iloc[0]
        if not latest_date:
            raise SystemExit(f"{summary_path} has blank latest_date")
        rows.append({"site": row["site"], "latest_date": latest_date})
    return pd.DataFrame(rows)


def build_score_window(configs: pd.DataFrame, latest_dates: pd.DataFrame) -> pd.DataFrame:
    merged = configs.merge(latest_dates, on="site", how="left")
    rows: list[dict[str, str | int]] = []
    for _, row in merged.iterrows():
        start = pd.to_datetime(row["train_end"]) + pd.Timedelta(days=1)
        end = pd.to_datetime(row["latest_date"])
        if pd.isna(start) or pd.isna(end):
            raise SystemExit(f"invalid score window for site={row['site']}")
        if start > end:
            raise SystemExit(f"score window start after end for site={row['site']}: {start.date()} > {end.date()}")
        for day in pd.date_range(start, end, freq="D"):
            rows.append(
                {
                    "site": row["site"],
                    "date": day.strftime("%Y-%m-%d"),
                    "score_window_flag": 1,
                }
            )
    return pd.DataFrame(rows)


def derive_missing_reason(address: str, weather_enabled: str, weather_available: int) -> str:
    if int(weather_available) == 1:
        return ""
    if not address:
        return "missing_address"
    if weather_enabled == "0":
        return "address_disabled"
    return "missing_weather_row"


def build_weather_history(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    config_dir = root / "configs" / "sites"
    share_dir = root / "_share"
    manual_dir = root / "data" / "manual"

    configs = load_site_configs(config_dir)
    latest_dates = load_latest_raw_dates(configs, root)
    score_window = build_score_window(configs, latest_dates)

    addresses = load_addresses(manual_dir / "site_addresses.csv")
    manual_weather = load_manual_weather(manual_dir / "site_weather_daily.csv")

    history = score_window.merge(addresses, on="site", how="left")
    history = history.merge(
        manual_weather,
        on=["site", "date"],
        how="left",
        suffixes=("", "_manual"),
    )

    history["address"] = normalized_text(history["address"])
    history["weather_enabled"] = normalized_text(history["weather_enabled"])
    history["weather_row_has_payload"] = history["weather_row_has_payload"].eq(True)
    history["weather_available"] = history["weather_row_has_payload"].astype(int)

    for col in ["weather_tag", "sun_hours", "rain_flag", "cloud_flag", "weather_confidence", "note", "weather_source"]:
        history[col] = history[col].fillna("")

    history["weather_missing_reason"] = history.apply(
        lambda row: derive_missing_reason(
            address=str(row["address"] or "").strip(),
            weather_enabled=str(row["weather_enabled"] or "").strip(),
            weather_available=int(row["weather_available"]),
        ),
        axis=1,
    )
    history.loc[history["weather_available"] == 0, "weather_source"] = ""

    history_output = history[HISTORY_COLS].copy()
    history_output = history_output.sort_values(["site", "date"], kind="stable").reset_index(drop=True)

    coverage = (
        history.assign(missing_address_flag=history["address"].eq("").astype(int))
        .groupby("site", dropna=False)
        .agg(
            score_window_days=("date", "size"),
            weather_available_days=("weather_available", "sum"),
            missing_address_flag=("missing_address_flag", "max"),
        )
        .reset_index()
    )
    coverage["missing_weather_days"] = coverage["score_window_days"] - coverage["weather_available_days"]
    coverage["coverage_rate"] = (
        coverage["weather_available_days"] / coverage["score_window_days"].where(coverage["score_window_days"] != 0, pd.NA)
    ).fillna(0.0)
    coverage = coverage[COVERAGE_COLS].copy()

    request_template = history.loc[history["weather_available"] == 0, ["site", "address", "date", "weather_missing_reason"]].copy()
    request_template = request_template.rename(columns={"weather_missing_reason": "reason"})
    request_template["address"] = request_template["address"].fillna("")
    request_template = request_template[REQUEST_COLS].sort_values(["site", "date"], kind="stable").reset_index(drop=True)

    share_dir.mkdir(parents=True, exist_ok=True)
    return history_output, coverage, request_template


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    history, coverage, request_template = build_weather_history(root)
    share_dir = root / "_share"
    history_path = share_dir / "site_weather_history_latest.csv"
    coverage_path = share_dir / "site_weather_history_coverage.csv"
    request_path = share_dir / "site_weather_request_template.csv"

    history.to_csv(history_path, index=False, encoding="utf-8-sig")
    coverage.to_csv(coverage_path, index=False, encoding="utf-8-sig")
    request_template.to_csv(request_path, index=False, encoding="utf-8-sig")

    print(f"site_weather_history_rows={len(history)}")
    print(history["site"].value_counts().sort_index().to_string())
    print(coverage.to_string(index=False))


if __name__ == "__main__":
    main()
