#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
CFG_INCIDENT_MIN_GROUP_PANELS = 2
CFG_INCIDENT_MIN_GROUP_SHARE = 0.50
CFG_INCIDENT_MIN_GROUPS = 2
CFG_INCIDENT_MIN_SITE_PANELS = 5
CFG_INCIDENT_MIN_SITE_SHARE = 0.10
CFG_INCIDENT_MERGE_GROUP_OVERLAP_SHARE = 0.50
REQUIRED_COLS = [
    "site",
    "panel_id",
    "date",
    "coverage_ok_flag",
    "mid_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "group_proxy_value",
    "group_proxy_source",
]
INCIDENT_REGISTRY_COLS = [
    "site",
    "incident_id",
    "incident_start_date",
    "incident_end_date",
    "incident_day_count",
    "incident_scope",
    "affected_group_count",
    "affected_panel_count",
    "max_group_like_share",
    "max_site_affected_share",
    "dominant_incident_family",
    "incident_confidence",
    "recommended_action",
    "group_proxy_source_mode",
    "topology_confidence",
    "open_reason_code",
    "close_reason_code",
]
INCIDENT_DAY_COLS = [
    "site",
    "incident_id",
    "date",
    "qualifying_group_count",
    "max_group_cluster_size",
    "total_panels_in_qualifying_groups",
    "site_affected_share",
    "representative_group_proxies",
    "representative_panel_ids",
    "incident_day_reason_code",
]
SUMMARY_COLS = [
    "site",
    "incident_count",
    "incident_day_count",
    "high_confidence_incident_count",
    "medium_confidence_incident_count",
    "group_scope_incident_count",
    "site_scope_incident_count",
    "mixed_scope_incident_count",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize common_cause_incident_registry_v1 from panel_day_evidence_matrix_v1 using evidence aggregation only."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to project root.",
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


def parse_date(value: object) -> pd.Timestamp | pd.NaT:
    text = normalize_date(value)
    if text == "":
        return pd.NaT
    return pd.to_datetime(text, errors="coerce")


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def safe_div(numer: int | float, denom: int | float) -> float:
    if denom <= 0:
        return 0.0
    return round(float(numer / denom), 6)


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


def join_sorted(values: list[object]) -> str:
    normalized = sorted({normalize_text(value) for value in values if normalize_text(value) != ""})
    return "|".join(normalized)


def overlap_share(left: set[str], right: set[str]) -> float:
    union = left | right
    if not union:
        return 0.0
    return safe_div(len(left & right), len(union))


def load_matrix(root: Path) -> pd.DataFrame:
    path = root / "_share" / "panel_day_evidence_matrix_v1.csv"
    df = read_csv(path)
    ensure_columns(df, REQUIRED_COLS, "panel_day_evidence_matrix_v1.csv")

    df = df.copy()
    df["site"] = df["site"].map(normalize_text)
    df["panel_id"] = df["panel_id"].map(normalize_text)
    df["date"] = df["date"].map(normalize_date)
    df["_date_ts"] = df["date"].map(parse_date)
    df["group_proxy_value"] = df["group_proxy_value"].map(normalize_text)
    df["group_proxy_source"] = df["group_proxy_source"].map(normalize_text)
    for col in ["coverage_ok_flag", "mid_ratio", "mid_v_ratio", "mid_i_ratio"]:
        if col == "coverage_ok_flag":
            df[col] = df[col].map(to_int_flag).astype(int)
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["zero_like_flag"] = (
        df["coverage_ok_flag"].eq(1)
        & df["mid_ratio"].le(0.10)
        & df["mid_i_ratio"].le(0.10)
    ).fillna(False).astype(int)
    df["group_like_zero_like_flag"] = (
        df["zero_like_flag"].eq(1)
        & df["mid_v_ratio"].ge(1.05)
    ).fillna(False).astype(int)
    return df


def build_group_day(matrix_df: pd.DataFrame) -> pd.DataFrame:
    group_day = matrix_df.groupby(["site", "date", "group_proxy_value"], as_index=False).agg(
        group_panel_count=("panel_id", "size"),
        zero_like_panel_count=("zero_like_flag", "sum"),
        group_like_zero_like_panel_count=("group_like_zero_like_flag", "sum"),
    )
    group_day["group_like_zero_like_share"] = group_day.apply(
        lambda row: safe_div(row["group_like_zero_like_panel_count"], row["group_panel_count"]),
        axis=1,
    )
    group_day["qualifying_group_flag"] = (
        group_day["group_like_zero_like_panel_count"].ge(CFG_INCIDENT_MIN_GROUP_PANELS)
        & group_day["group_like_zero_like_share"].ge(CFG_INCIDENT_MIN_GROUP_SHARE)
    ).astype(int)
    return group_day


def build_candidate_days(matrix_df: pd.DataFrame, group_day: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    site_day = matrix_df.groupby(["site", "date"], as_index=False).agg(
        total_panel_count=("panel_id", "size"),
        total_zero_like_panel_count=("zero_like_flag", "sum"),
        total_group_like_zero_like_panel_count=("group_like_zero_like_flag", "sum"),
    )

    qualifying_group_day = group_day.loc[group_day["qualifying_group_flag"].eq(1)].copy()
    qualifying_day = qualifying_group_day.groupby(["site", "date"], as_index=False).agg(
        qualifying_group_count=("group_proxy_value", "size"),
        max_group_cluster_size=("group_like_zero_like_panel_count", "max"),
        total_panels_in_qualifying_groups=("group_like_zero_like_panel_count", "sum"),
    )
    qualifying_day["site_affected_share"] = qualifying_day.apply(
        lambda row: safe_div(row["total_panels_in_qualifying_groups"], row["total_panel_count"])
        if "total_panel_count" in row
        else 0.0,
        axis=1,
    )

    candidate_panel_rows = (
        matrix_df.loc[matrix_df["group_like_zero_like_flag"].eq(1)]
        .merge(
            qualifying_group_day.loc[:, ["site", "date", "group_proxy_value"]],
            on=["site", "date", "group_proxy_value"],
            how="inner",
        )
        .copy()
    )
    representative_groups = qualifying_group_day.groupby(["site", "date"], as_index=False).agg(
        representative_group_proxies=("group_proxy_value", lambda values: join_sorted(list(values))),
        _qualifying_group_set=("group_proxy_value", lambda values: sorted({normalize_text(value) for value in values if normalize_text(value) != ""})),
        _max_group_like_share=("group_like_zero_like_share", "max"),
    )
    representative_panels = candidate_panel_rows.groupby(["site", "date"], as_index=False).agg(
        representative_panel_ids=("panel_id", lambda values: join_sorted(list(values))),
        _qualifying_panel_set=("panel_id", lambda values: sorted({normalize_text(value) for value in values if normalize_text(value) != ""})),
        _group_proxy_source_values=("group_proxy_source", lambda values: sorted({normalize_text(value) for value in values if normalize_text(value) != ""})),
    )

    site_day = site_day.merge(qualifying_day, on=["site", "date"], how="left")
    for col in ["qualifying_group_count", "max_group_cluster_size", "total_panels_in_qualifying_groups"]:
        site_day[col] = pd.to_numeric(site_day[col], errors="coerce").fillna(0).astype(int)
    site_day["site_affected_share"] = site_day.apply(
        lambda row: safe_div(row["total_panels_in_qualifying_groups"], row["total_panel_count"]),
        axis=1,
    )
    site_day["incident_candidate_flag"] = (
        site_day["qualifying_group_count"].ge(CFG_INCIDENT_MIN_GROUPS)
        | (
            site_day["total_panels_in_qualifying_groups"].ge(CFG_INCIDENT_MIN_SITE_PANELS)
            & site_day["site_affected_share"].ge(CFG_INCIDENT_MIN_SITE_SHARE)
        )
    ).astype(int)

    candidate_days = site_day.loc[site_day["incident_candidate_flag"].eq(1)].copy()
    candidate_days = candidate_days.merge(representative_groups, on=["site", "date"], how="left")
    candidate_days = candidate_days.merge(representative_panels, on=["site", "date"], how="left")
    candidate_days["incident_day_reason_code"] = candidate_days["qualifying_group_count"].map(
        lambda count: "IOPEN_MULTI_GROUP_COLLAPSE" if int(count) >= CFG_INCIDENT_MIN_GROUPS else "IOPEN_SITE_WIDE_COLLAPSE"
    )
    candidate_days["_date_ts"] = candidate_days["date"].map(parse_date)
    candidate_days["_qualifying_group_set"] = candidate_days["_qualifying_group_set"].map(
        lambda values: set(values) if isinstance(values, list) else set()
    )
    candidate_days["_qualifying_panel_set"] = candidate_days["_qualifying_panel_set"].map(
        lambda values: set(values) if isinstance(values, list) else set()
    )
    candidate_days["_group_proxy_source_values"] = candidate_days["_group_proxy_source_values"].map(
        lambda values: set(values) if isinstance(values, list) else set()
    )
    return candidate_days, qualifying_group_day, candidate_panel_rows


def derive_incident_scope(affected_group_count: int) -> str:
    if affected_group_count == 1:
        return "group"
    if affected_group_count >= 3:
        return "site"
    return "mixed"


def derive_dominant_incident_family(max_group_like_share: float, max_site_affected_share: float, affected_group_count: int) -> str:
    # Prioritize the stronger site-wide condition so the site-wide branch remains reachable.
    if max_site_affected_share >= CFG_INCIDENT_MIN_SITE_SHARE and affected_group_count >= 3:
        return "site_wide_collapse"
    if max_group_like_share >= 0.50:
        return "group_inverter_side"
    return "mixed"


def derive_incident_confidence(affected_group_count: int, max_site_affected_share: float) -> str:
    if affected_group_count >= 3 and max_site_affected_share >= CFG_INCIDENT_MIN_SITE_SHARE:
        return "high"
    if affected_group_count >= 2:
        return "medium"
    return "low"


def derive_group_proxy_source_mode(source_values: set[str]) -> str:
    if source_values == {"group_key_base"}:
        return "group_key_base"
    if source_values == {"panel_id_token_proxy"}:
        return "panel_id_token_proxy"
    return "mixed"


def derive_topology_confidence(group_proxy_source_mode: str) -> str:
    if group_proxy_source_mode == "group_key_base":
        return "high"
    if group_proxy_source_mode == "panel_id_token_proxy":
        return "low"
    return "medium"


def build_incidents(
    candidate_days: pd.DataFrame,
    qualifying_group_day: pd.DataFrame,
    candidate_panel_rows: pd.DataFrame,
    site_max_dates: dict[str, str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if candidate_days.empty:
        return (
            pd.DataFrame(columns=INCIDENT_REGISTRY_COLS),
            pd.DataFrame(columns=INCIDENT_DAY_COLS),
        )

    registry_rows: list[dict[str, object]] = []
    incident_day_rows: list[dict[str, object]] = []

    for site in sorted(candidate_days["site"].dropna().unique()):
        site_days = candidate_days.loc[candidate_days["site"].eq(site)].sort_values(["_date_ts", "date"]).reset_index(drop=True)
        current_indices: list[int] = []
        incident_index = 0

        def finalize(indices: list[int], close_reason_code: str) -> None:
            nonlocal incident_index
            if not indices:
                return
            incident_index += 1
            incident_df = site_days.loc[indices].copy()
            incident_start_date = normalize_text(incident_df.iloc[0]["date"])
            incident_end_date = normalize_text(incident_df.iloc[-1]["date"])
            incident_id = f"{site}.cci.{incident_start_date}.{incident_index:03d}"
            affected_group_set = set().union(*incident_df["_qualifying_group_set"].tolist())
            affected_panel_set = set().union(*incident_df["_qualifying_panel_set"].tolist())
            source_values = set().union(*incident_df["_group_proxy_source_values"].tolist())
            max_group_like_share = (
                qualifying_group_day.loc[
                    qualifying_group_day["site"].eq(site)
                    & qualifying_group_day["date"].isin(incident_df["date"].tolist()),
                    "group_like_zero_like_share",
                ].max()
                if not qualifying_group_day.empty
                else 0.0
            )
            max_group_like_share = float(max_group_like_share) if pd.notna(max_group_like_share) else 0.0
            max_site_affected_share = float(incident_df["site_affected_share"].max()) if not incident_df.empty else 0.0
            affected_group_count = len(affected_group_set)
            affected_panel_count = len(affected_panel_set)
            incident_scope = derive_incident_scope(affected_group_count)
            dominant_incident_family = derive_dominant_incident_family(
                max_group_like_share,
                max_site_affected_share,
                affected_group_count,
            )
            incident_confidence = derive_incident_confidence(affected_group_count, max_site_affected_share)
            recommended_action = "field_check" if incident_confidence == "high" else "common_cause_review"
            group_proxy_source_mode = derive_group_proxy_source_mode(source_values)
            topology_confidence = derive_topology_confidence(group_proxy_source_mode)
            open_reason_code = normalize_text(incident_df.iloc[0]["incident_day_reason_code"])

            registry_rows.append(
                {
                    "site": site,
                    "incident_id": incident_id,
                    "incident_start_date": incident_start_date,
                    "incident_end_date": incident_end_date,
                    "incident_day_count": int(len(incident_df)),
                    "incident_scope": incident_scope,
                    "affected_group_count": int(affected_group_count),
                    "affected_panel_count": int(affected_panel_count),
                    "max_group_like_share": round(max_group_like_share, 6),
                    "max_site_affected_share": round(max_site_affected_share, 6),
                    "dominant_incident_family": dominant_incident_family,
                    "incident_confidence": incident_confidence,
                    "recommended_action": recommended_action,
                    "group_proxy_source_mode": group_proxy_source_mode,
                    "topology_confidence": topology_confidence,
                    "open_reason_code": open_reason_code,
                    "close_reason_code": close_reason_code,
                }
            )

            for _, row in incident_df.iterrows():
                incident_day_rows.append(
                    {
                        "site": site,
                        "incident_id": incident_id,
                        "date": normalize_text(row["date"]),
                        "qualifying_group_count": int(row["qualifying_group_count"]),
                        "max_group_cluster_size": int(row["max_group_cluster_size"]),
                        "total_panels_in_qualifying_groups": int(row["total_panels_in_qualifying_groups"]),
                        "site_affected_share": round(float(row["site_affected_share"]), 6),
                        "representative_group_proxies": normalize_text(row["representative_group_proxies"]),
                        "representative_panel_ids": normalize_text(row["representative_panel_ids"]),
                        "incident_day_reason_code": normalize_text(row["incident_day_reason_code"]),
                    }
                )

        for idx, row in site_days.iterrows():
            if not current_indices:
                current_indices = [idx]
                continue

            prev_row = site_days.loc[current_indices[-1]]
            consecutive = row["_date_ts"] == prev_row["_date_ts"] + pd.Timedelta(days=1)
            share = overlap_share(prev_row["_qualifying_group_set"], row["_qualifying_group_set"]) if consecutive else 0.0
            if consecutive and share >= CFG_INCIDENT_MERGE_GROUP_OVERLAP_SHARE:
                current_indices.append(idx)
                continue

            finalize(current_indices, "ICLOSE_GAP_BREAK")
            current_indices = [idx]

        if current_indices:
            final_end_date = normalize_text(site_days.loc[current_indices[-1], "date"])
            final_close_reason = "ICLOSE_DATA_END" if final_end_date == site_max_dates.get(site, "") else "ICLOSE_GAP_BREAK"
            finalize(current_indices, final_close_reason)

    registry_output = pd.DataFrame(registry_rows, columns=INCIDENT_REGISTRY_COLS)
    incident_days_output = pd.DataFrame(incident_day_rows, columns=INCIDENT_DAY_COLS)
    return registry_output, incident_days_output


def build_summary_output(registry_output: pd.DataFrame, incident_days_output: pd.DataFrame, sites: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for site in sites:
        site_registry = registry_output.loc[registry_output["site"].eq(site)] if not registry_output.empty else registry_output
        site_days = incident_days_output.loc[incident_days_output["site"].eq(site)] if not incident_days_output.empty else incident_days_output
        rows.append(
            {
                "site": site,
                "incident_count": int(len(site_registry)),
                "incident_day_count": int(len(site_days)),
                "high_confidence_incident_count": int(site_registry["incident_confidence"].eq("high").sum()) if not site_registry.empty else 0,
                "medium_confidence_incident_count": int(site_registry["incident_confidence"].eq("medium").sum()) if not site_registry.empty else 0,
                "group_scope_incident_count": int(site_registry["incident_scope"].eq("group").sum()) if not site_registry.empty else 0,
                "site_scope_incident_count": int(site_registry["incident_scope"].eq("site").sum()) if not site_registry.empty else 0,
                "mixed_scope_incident_count": int(site_registry["incident_scope"].eq("mixed").sum()) if not site_registry.empty else 0,
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_COLS)


def build_outputs(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    matrix_df = load_matrix(root)
    sites = list(SITES)
    site_max_dates = {
        site: normalize_text(max_date)
        for site, max_date in matrix_df.groupby("site")["date"].max().items()
    }
    group_day = build_group_day(matrix_df)
    candidate_days, qualifying_group_day, candidate_panel_rows = build_candidate_days(matrix_df, group_day)
    registry_output, incident_days_output = build_incidents(
        candidate_days,
        qualifying_group_day,
        candidate_panel_rows,
        site_max_dates,
    )
    summary_output = build_summary_output(registry_output, incident_days_output, sites)
    return registry_output, incident_days_output, summary_output


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    registry_output, incident_days_output, summary_output = build_outputs(root)

    out_dir = root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    registry_output.to_csv(out_dir / "common_cause_incident_registry_v1.csv", index=False, encoding="utf-8-sig")
    incident_days_output.to_csv(out_dir / "common_cause_incident_days_v1.csv", index=False, encoding="utf-8-sig")
    summary_output.to_csv(out_dir / "common_cause_incident_summary_v1.csv", index=False, encoding="utf-8-sig")
    print(
        "common_cause_incident_registry_v1="
        f"{len(registry_output)} common_cause_incident_days_v1={len(incident_days_output)} "
        f"common_cause_incident_summary_v1={len(summary_output)}"
    )


if __name__ == "__main__":
    main()
