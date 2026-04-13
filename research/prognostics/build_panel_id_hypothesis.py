#!/usr/bin/env python3
from __future__ import annotations

import argparse
import uuid
from pathlib import Path

import pandas as pd

REQUIRED_SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
LATEST_COLS = [
    "site",
    "panel_id",
    "token0_uuid",
    "token1_group",
    "token2_index",
    "token2_index_int",
    "panel_id_pattern_valid",
    "parse_note",
    "source_inventory",
    "repeated_panel_id_across_sites_flag",
]
SUMMARY_COLS = [
    "site",
    "repo_panel_count",
    "valid_pattern_count",
    "pattern_valid_rate",
    "token0_unique_count",
    "token1_unique_count",
    "token2_min",
    "token2_max",
    "token2_unique_count",
    "malformed_panel_id_rows",
    "token2_non_integer_rows",
    "repeated_panel_id_across_sites_rows",
    "noncontiguous_group_count",
    "topology_row_count_reference",
]
GROUP_STATS_COLS = [
    "site",
    "token0_uuid",
    "token1_group",
    "panel_count",
    "token2_min",
    "token2_max",
    "token2_unique_count",
    "token2_contiguous_flag",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a neutral panel_id hypothesis layer from active inventory.")
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


def safe_rate(numer: int, denom: int) -> float:
    if denom == 0:
        return 0.0
    return round(float(numer) / float(denom), 6)


def load_active_inventory(root: Path) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    missing_paths: list[str] = []

    for site in REQUIRED_SITES:
        path = root / "data" / site / "out" / "latest_panel_status.csv"
        if not path.exists():
            missing_paths.append(str(path))
            continue
        inventory = read_csv(path)
        if "panel_id" not in inventory.columns:
            raise SystemExit(f"{path} missing panel_id")
        if "site" not in inventory.columns:
            inventory = inventory.assign(site=site)
        subset = inventory[["site", "panel_id"]].copy()
        subset["site"] = normalized_text(subset["site"])
        subset["panel_id"] = normalized_text(subset["panel_id"])
        subset = subset.loc[subset["site"].eq(site) & subset["panel_id"].ne("")].copy()
        subset["source_inventory"] = f"data/{site}/out/latest_panel_status.csv"
        rows.append(subset)

    if missing_paths:
        raise SystemExit(f"missing required latest_panel_status.csv files: {missing_paths}")

    active = pd.concat(rows, ignore_index=True)
    active = active.drop_duplicates(["site", "panel_id"], keep="last")
    active = active.sort_values(["site", "panel_id"], kind="stable").reset_index(drop=True)
    return active


def load_topology_reference_counts(root: Path) -> pd.DataFrame:
    path = root / "data" / "manual" / "site_topology.csv"
    if not path.exists():
        return pd.DataFrame(columns=["site", "topology_row_count_reference"])

    topology = read_csv(path)
    if "site" not in topology.columns:
        return pd.DataFrame(columns=["site", "topology_row_count_reference"])

    site_counts = topology.copy()
    site_counts["site"] = normalized_text(site_counts["site"])
    site_counts = site_counts.loc[site_counts["site"].isin(REQUIRED_SITES)].copy()
    site_counts = (
        site_counts.groupby("site", dropna=False)
        .size()
        .rename("topology_row_count_reference")
        .reset_index()
    )
    return site_counts


def parse_panel_id(panel_id: str) -> dict[str, object]:
    parts = str(panel_id).strip().split(".")
    token0 = parts[0] if len(parts) > 0 else ""
    token1 = parts[1] if len(parts) > 1 else ""
    token2 = parts[2] if len(parts) > 2 else ""
    parse_note = ""
    token2_index_int: object = pd.NA

    if len(parts) != 3:
        parse_note = "wrong_segment_count"
    else:
        try:
            uuid.UUID(token0)
            token0_valid = True
        except (ValueError, AttributeError):
            token0_valid = False

        if not token0_valid:
            parse_note = "token0_not_uuid"
        elif not token1.isdigit():
            parse_note = "token1_not_integer_like"
        else:
            try:
                token2_index_int = int(token2)
            except ValueError:
                parse_note = "token2_not_integer"

    return {
        "token0_uuid": token0,
        "token1_group": token1,
        "token2_index": token2,
        "token2_index_int": token2_index_int,
        "panel_id_pattern_valid": int(parse_note == ""),
        "parse_note": parse_note,
    }


def append_parse_note(existing: str, extra: str) -> str:
    existing_clean = str(existing).strip()
    extra_clean = str(extra).strip()
    if not existing_clean:
        return extra_clean
    if not extra_clean:
        return existing_clean
    return f"{existing_clean}|{extra_clean}"


def build_latest(inventory: pd.DataFrame) -> pd.DataFrame:
    parsed = inventory["panel_id"].map(parse_panel_id).apply(pd.Series)
    latest = pd.concat([inventory.reset_index(drop=True), parsed.reset_index(drop=True)], axis=1)

    repeated_panel_ids = (
        latest.groupby("panel_id", dropna=False)["site"]
        .nunique()
        .rename("site_count")
        .reset_index()
    )
    repeated_panel_ids = repeated_panel_ids.loc[repeated_panel_ids["site_count"].gt(1), ["panel_id"]].copy()
    repeated_panel_ids["repeated_panel_id_across_sites_flag"] = 1

    latest = latest.merge(repeated_panel_ids, on="panel_id", how="left")
    latest["repeated_panel_id_across_sites_flag"] = (
        pd.to_numeric(latest["repeated_panel_id_across_sites_flag"], errors="coerce").fillna(0).astype(int)
    )
    latest["parse_note"] = latest.apply(
        lambda row: append_parse_note(
            row["parse_note"],
            "repeated_panel_id_across_sites" if int(row["repeated_panel_id_across_sites_flag"]) == 1 else "",
        ),
        axis=1,
    )
    latest["token2_index_int"] = pd.to_numeric(latest["token2_index_int"], errors="coerce").astype("Int64")
    latest = latest[LATEST_COLS].copy()
    latest = latest.sort_values(["site", "panel_id"], kind="stable").reset_index(drop=True)
    return latest


def contiguous_flag(token_values: pd.Series) -> int:
    cleaned = pd.to_numeric(token_values, errors="coerce").dropna().astype(int)
    if cleaned.empty:
        return 0
    unique_values = sorted(cleaned.unique().tolist())
    expected_values = list(range(unique_values[0], unique_values[-1] + 1))
    return int(unique_values == expected_values)


def build_group_stats(latest: pd.DataFrame) -> pd.DataFrame:
    valid = latest.loc[latest["panel_id_pattern_valid"].eq(1)].copy()
    if valid.empty:
        return pd.DataFrame(columns=GROUP_STATS_COLS)

    grouped = (
        valid.groupby(["site", "token0_uuid", "token1_group"], dropna=False)
        .agg(
            panel_count=("panel_id", "size"),
            token2_min=("token2_index_int", "min"),
            token2_max=("token2_index_int", "max"),
            token2_unique_count=("token2_index_int", "nunique"),
            token2_contiguous_flag=("token2_index_int", contiguous_flag),
        )
        .reset_index()
    )
    grouped["token2_min"] = pd.to_numeric(grouped["token2_min"], errors="coerce").astype("Int64")
    grouped["token2_max"] = pd.to_numeric(grouped["token2_max"], errors="coerce").astype("Int64")
    grouped["token2_unique_count"] = pd.to_numeric(grouped["token2_unique_count"], errors="coerce").fillna(0).astype(int)
    grouped["token2_contiguous_flag"] = pd.to_numeric(grouped["token2_contiguous_flag"], errors="coerce").fillna(0).astype(int)
    grouped = grouped[GROUP_STATS_COLS].copy()
    grouped = grouped.sort_values(["site", "token0_uuid", "token1_group"], kind="stable").reset_index(drop=True)
    return grouped


def build_summary(latest: pd.DataFrame, group_stats: pd.DataFrame, topology_reference: pd.DataFrame) -> pd.DataFrame:
    topology_lookup = topology_reference.set_index("site").to_dict("index") if not topology_reference.empty else {}
    rows: list[dict[str, object]] = []

    for site in REQUIRED_SITES:
        site_df = latest.loc[latest["site"].eq(site)].copy()
        valid_df = site_df.loc[site_df["panel_id_pattern_valid"].eq(1)].copy()
        site_groups = group_stats.loc[group_stats["site"].eq(site)].copy()
        token2_numeric = pd.to_numeric(valid_df["token2_index_int"], errors="coerce").dropna().astype(int)

        rows.append(
            {
                "site": site,
                "repo_panel_count": int(len(site_df)),
                "valid_pattern_count": int(len(valid_df)),
                "pattern_valid_rate": safe_rate(int(len(valid_df)), int(len(site_df))),
                "token0_unique_count": int(valid_df["token0_uuid"].nunique(dropna=True)),
                "token1_unique_count": int(valid_df["token1_group"].nunique(dropna=True)),
                "token2_min": int(token2_numeric.min()) if not token2_numeric.empty else pd.NA,
                "token2_max": int(token2_numeric.max()) if not token2_numeric.empty else pd.NA,
                "token2_unique_count": int(token2_numeric.nunique()) if not token2_numeric.empty else 0,
                "malformed_panel_id_rows": int(
                    site_df["parse_note"].str.contains(
                        "wrong_segment_count|token0_not_uuid|token1_not_integer_like",
                        regex=True,
                        na=False,
                    ).sum()
                ),
                "token2_non_integer_rows": int(site_df["parse_note"].str.contains("token2_not_integer", regex=False, na=False).sum()),
                "repeated_panel_id_across_sites_rows": int(site_df["repeated_panel_id_across_sites_flag"].sum()),
                "noncontiguous_group_count": int(site_groups["token2_contiguous_flag"].eq(0).sum()) if not site_groups.empty else 0,
                "topology_row_count_reference": topology_lookup.get(site, {}).get("topology_row_count_reference", pd.NA),
            }
        )

    summary = pd.DataFrame(rows)
    summary["token2_min"] = pd.to_numeric(summary["token2_min"], errors="coerce").astype("Int64")
    summary["token2_max"] = pd.to_numeric(summary["token2_max"], errors="coerce").astype("Int64")
    summary = summary[SUMMARY_COLS].copy()
    return summary


def build_panel_id_hypothesis(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    inventory = load_active_inventory(root)
    latest = build_latest(inventory)
    group_stats = build_group_stats(latest)
    topology_reference = load_topology_reference_counts(root)
    summary = build_summary(latest, group_stats, topology_reference)
    return latest, summary, group_stats


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    latest, summary, group_stats = build_panel_id_hypothesis(root)

    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    latest.to_csv(share_dir / "site_panel_id_hypothesis_latest.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(share_dir / "site_panel_id_hypothesis_summary.csv", index=False, encoding="utf-8-sig")
    group_stats.to_csv(share_dir / "site_panel_id_group_stats.csv", index=False, encoding="utf-8-sig")

    malformed_rows = int(latest["panel_id_pattern_valid"].eq(0).sum())
    noncontiguous_groups = int(group_stats["token2_contiguous_flag"].eq(0).sum()) if not group_stats.empty else 0
    print(
        "built panel_id hypothesis: "
        f"rows={len(latest)}, malformed_rows={malformed_rows}, noncontiguous_groups={noncontiguous_groups}"
    )


if __name__ == "__main__":
    main()
