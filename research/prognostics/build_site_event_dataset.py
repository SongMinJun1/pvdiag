#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

EVENT_GROUP_COLS = [
    "site",
    "review_group",
    "representative_date",
    "event_start_date",
    "event_end_date",
    "panel_count",
    "panel_ids",
    "summary",
    "likely_common_issue",
]
META_COLS = [
    "site",
    "panel_id",
    "review_group",
    "our_first_anomaly_source",
    "chronology_guard_applied",
    "confidence_level",
    "abstain_flag",
    "abstain_reason",
]
WEATHER_COLS = [
    "site",
    "date",
    "weather_tag",
    "sun_hours",
    "rain_flag",
    "cloud_flag",
    "weather_confidence",
    "note",
]
DATASET_COLS = [
    "site",
    "review_group",
    "representative_date",
    "event_start_date",
    "event_end_date",
    "panel_count",
    "panel_ids",
    "likely_common_issue",
    "summary",
    "n_alert_history_temporal",
    "n_historical_reconstruction",
    "n_row_evidence_fallback",
    "n_current_review_fallback",
    "n_guard_applied",
    "n_low_confidence",
    "n_medium_confidence",
    "n_high_confidence",
    "n_abstain",
    "event_confidence_level",
    "weather_available",
    "weather_tag",
    "sun_hours",
    "rain_flag",
    "cloud_flag",
    "weather_confidence",
    "weather_confound_flag",
    "weather_note",
]
SOURCE_COUNT_MAP = {
    "alert_history_temporal": "n_alert_history_temporal",
    "historical_reconstruction": "n_historical_reconstruction",
    "row_evidence_fallback": "n_row_evidence_fallback",
    "current_review_fallback": "n_current_review_fallback",
}
CONFIDENCE_COUNT_MAP = {
    "low": "n_low_confidence",
    "medium": "n_medium_confidence",
    "high": "n_high_confidence",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build event-level sidecar dataset with optional manual weather annotations.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to project root.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, expected: list[str], name: str) -> pd.DataFrame:
    missing = [col for col in expected if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")
    return df.copy()


def normalized_text(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def build_weather_template(groups: pd.DataFrame) -> pd.DataFrame:
    template = (
        groups[["site", "representative_date"]]
        .drop_duplicates()
        .rename(columns={"representative_date": "date"})
        .sort_values(["site", "date"], kind="stable")
        .reset_index(drop=True)
    )
    for col in WEATHER_COLS[2:]:
        template[col] = ""
    return template[WEATHER_COLS]


def load_manual_weather(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=WEATHER_COLS)
    weather = ensure_columns(read_csv(path), WEATHER_COLS, str(path))
    weather = weather[WEATHER_COLS].copy()
    weather["site"] = normalized_text(weather["site"])
    weather["date"] = normalized_text(weather["date"])
    return weather


def count_by_group(frame: pd.DataFrame, key_col: str, value_to_col: dict[str, str]) -> pd.DataFrame:
    if frame.empty:
        cols = ["site", "review_group"] + list(value_to_col.values())
        return pd.DataFrame(columns=cols)
    work = frame[[key_col, "site", "review_group"]].copy()
    work[key_col] = normalized_text(frame[key_col])
    grouped = work.groupby(["site", "review_group", key_col], dropna=False).size().unstack(fill_value=0)
    grouped = grouped.rename(columns=value_to_col).reset_index()
    for col in value_to_col.values():
        if col not in grouped.columns:
            grouped[col] = 0
    return grouped[["site", "review_group"] + list(value_to_col.values())]


def aggregate_meta(meta: pd.DataFrame) -> pd.DataFrame:
    base = meta[["site", "review_group"]].drop_duplicates().copy()

    source_counts = count_by_group(meta, "our_first_anomaly_source", SOURCE_COUNT_MAP)
    conf_counts = count_by_group(meta, "confidence_level", CONFIDENCE_COUNT_MAP)

    work = meta.copy()
    work["chronology_guard_applied"] = pd.to_numeric(work["chronology_guard_applied"], errors="coerce").fillna(0).astype(int)
    work["abstain_flag"] = pd.to_numeric(work["abstain_flag"], errors="coerce").fillna(0).astype(int)

    guard_counts = (
        work.groupby(["site", "review_group"], dropna=False)["chronology_guard_applied"]
        .sum()
        .rename("n_guard_applied")
        .reset_index()
    )
    abstain_counts = (
        work.groupby(["site", "review_group"], dropna=False)["abstain_flag"]
        .sum()
        .rename("n_abstain")
        .reset_index()
    )

    aggregated = base.merge(source_counts, on=["site", "review_group"], how="left")
    aggregated = aggregated.merge(conf_counts, on=["site", "review_group"], how="left")
    aggregated = aggregated.merge(guard_counts, on=["site", "review_group"], how="left")
    aggregated = aggregated.merge(abstain_counts, on=["site", "review_group"], how="left")

    count_cols = list(SOURCE_COUNT_MAP.values()) + list(CONFIDENCE_COUNT_MAP.values()) + ["n_guard_applied", "n_abstain"]
    for col in count_cols:
        aggregated[col] = pd.to_numeric(aggregated[col], errors="coerce").fillna(0).astype(int)
    return aggregated


def derive_event_confidence(row: pd.Series) -> str:
    if int(row["n_alert_history_temporal"]) > 0 and int(row["n_guard_applied"]) == 0:
        return "high"
    if int(row["n_row_evidence_fallback"]) > 0 or int(row["n_historical_reconstruction"]) > 0:
        return "medium"
    if int(row["n_abstain"]) == int(row["panel_count"]):
        return "low"
    return "unknown"


def normalize_optional_int(value: object) -> str:
    if pd.isna(value) or value == "":
        return ""
    try:
        as_float = float(value)
    except (TypeError, ValueError):
        return str(value).strip()
    if as_float.is_integer():
        return str(int(as_float))
    return str(as_float)


def derive_weather_confound(row: pd.Series) -> str:
    if int(row["weather_available"]) == 0:
        return ""
    rain_flag = normalize_optional_int(row["rain_flag"])
    cloud_flag = normalize_optional_int(row["cloud_flag"])
    weather_tag = normalized_text(pd.Series([row["weather_tag"]])).iloc[0].lower()
    if rain_flag == "1":
        return "1"
    if weather_tag in {"cloudy", "mixed"} and cloud_flag == "1":
        return "1"
    return "0"


def attach_weather(dataset: pd.DataFrame, manual_weather: pd.DataFrame) -> pd.DataFrame:
    if manual_weather.empty:
        dataset = dataset.copy()
        dataset["weather_available"] = 0
        dataset["weather_tag"] = ""
        dataset["sun_hours"] = ""
        dataset["rain_flag"] = ""
        dataset["cloud_flag"] = ""
        dataset["weather_confidence"] = ""
        dataset["weather_confound_flag"] = ""
        dataset["weather_note"] = ""
        return dataset

    weather = manual_weather.rename(columns={"date": "representative_date", "note": "weather_note"}).copy()
    weather = weather.drop_duplicates(["site", "representative_date"], keep="last")
    merged = dataset.merge(
        weather,
        on=["site", "representative_date"],
        how="left",
    )
    for col in ["weather_tag", "sun_hours", "rain_flag", "cloud_flag", "weather_confidence", "weather_note"]:
        merged[col] = merged[col].fillna("")
    merged["weather_available"] = (
        merged[["weather_tag", "sun_hours", "rain_flag", "cloud_flag", "weather_confidence", "weather_note"]]
        .astype(str)
        .apply(lambda col: col.str.strip())
        .ne("")
        .any(axis=1)
        .astype(int)
    )
    merged["weather_confound_flag"] = merged.apply(derive_weather_confound, axis=1)
    return merged


def build_event_dataset(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    share_dir = root / "_share"
    groups_path = share_dir / "site_event_groups_latest.csv"
    meta_path = share_dir / "field_truth_template_meta.csv"
    manual_weather_path = root / "data" / "manual" / "site_weather_daily.csv"

    groups = ensure_columns(read_csv(groups_path), EVENT_GROUP_COLS, str(groups_path))[EVENT_GROUP_COLS].copy()
    meta = ensure_columns(read_csv(meta_path), META_COLS, str(meta_path))[META_COLS].copy()

    groups["site"] = normalized_text(groups["site"])
    groups["review_group"] = normalized_text(groups["review_group"])
    meta["site"] = normalized_text(meta["site"])
    meta["review_group"] = normalized_text(meta["review_group"])

    weather_template = build_weather_template(groups)
    manual_weather = load_manual_weather(manual_weather_path)

    aggregated_meta = aggregate_meta(meta)
    dataset = groups.merge(aggregated_meta, on=["site", "review_group"], how="left")

    count_cols = list(SOURCE_COUNT_MAP.values()) + list(CONFIDENCE_COUNT_MAP.values()) + ["n_guard_applied", "n_abstain"]
    for col in count_cols:
        dataset[col] = pd.to_numeric(dataset[col], errors="coerce").fillna(0).astype(int)
    dataset["panel_count"] = pd.to_numeric(dataset["panel_count"], errors="coerce").fillna(0).astype(int)

    dataset["event_confidence_level"] = dataset.apply(derive_event_confidence, axis=1)
    dataset = attach_weather(dataset, manual_weather)
    dataset = dataset[DATASET_COLS].copy()
    dataset = dataset.sort_values(["site", "representative_date", "review_group"], kind="stable").reset_index(drop=True)
    return dataset, weather_template


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    dataset, weather_template = build_event_dataset(root)
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = share_dir / "site_event_dataset_latest.csv"
    weather_template_path = share_dir / "site_weather_daily_template.csv"
    dataset.to_csv(dataset_path, index=False, encoding="utf-8-sig")
    weather_template.to_csv(weather_template_path, index=False, encoding="utf-8-sig")

    print(f"site_event_dataset_rows={len(dataset)}")
    print(f"site_weather_template_rows={len(weather_template)}")
    if not dataset.empty:
        print(dataset["event_confidence_level"].value_counts(dropna=False).sort_index().to_string())
        print(dataset["weather_available"].value_counts(dropna=False).sort_index().to_string())


if __name__ == "__main__":
    main()
