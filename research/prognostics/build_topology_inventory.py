#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

TOPOLOGY_COLS = ["site", "panel_id", "string_id", "mppt_id", "inverter_id", "note"]
INVENTORY_COLS = ["site", "panel_id"]
COVERAGE_COLS = [
    "site",
    "total_panels",
    "matched_panels",
    "coverage_rate",
    "string_coverage_rate",
    "mppt_coverage_rate",
    "inverter_coverage_rate",
]
MISSING_COLS = ["site", "panel_id", "missing_string", "missing_mppt", "missing_inverter"]
DUPLICATE_COLS = [
    "panel_id",
    "row_count",
    "sites_seen",
    "string_ids_seen",
    "mppt_ids_seen",
    "inverter_ids_seen",
    "inventory_sites_seen",
    "duplicate_flag",
    "conflict_flag",
    "site_mismatch_flag",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build topology input QA and coverage sidecars.")
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


def join_distinct(values: pd.Series) -> str:
    cleaned = sorted({str(value).strip() for value in values if str(value).strip()})
    return "|".join(cleaned)


def safe_rate(numer: pd.Series, denom: pd.Series) -> pd.Series:
    numer = pd.to_numeric(numer, errors="coerce").fillna(0)
    denom = pd.to_numeric(denom, errors="coerce").fillna(0)
    return (numer / denom.where(denom != 0, pd.NA)).fillna(0.0)


def load_panel_inventory(root: Path) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for path in sorted((root / "data").glob("*/out/latest_panel_status.csv")):
        df = read_csv(path)
        if "panel_id" not in df.columns:
            raise SystemExit(f"{path} missing panel_id")
        site_name = path.parents[1].name
        if "site" not in df.columns:
            df = df.assign(site=site_name)
        subset = df[["site", "panel_id"]].copy()
        subset["site"] = normalized_text(subset["site"])
        subset["panel_id"] = normalized_text(subset["panel_id"])
        subset = subset.loc[subset["site"].ne("") & subset["panel_id"].ne("")].copy()
        rows.append(subset)

    if not rows:
        raise SystemExit(f"no latest_panel_status.csv files found under {root / 'data'}")

    inventory = pd.concat(rows, ignore_index=True)
    inventory = inventory.drop_duplicates(INVENTORY_COLS, keep="last")
    inventory = inventory.sort_values(INVENTORY_COLS, kind="stable").reset_index(drop=True)
    return inventory


def load_topology(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=TOPOLOGY_COLS)

    topology = ensure_columns(read_csv(path), TOPOLOGY_COLS, str(path))
    topology = topology[TOPOLOGY_COLS].copy()
    for col in TOPOLOGY_COLS:
        topology[col] = normalized_text(topology[col])
    topology = topology.loc[topology["panel_id"].ne("")].copy()
    return topology.reset_index(drop=True)


def build_panel_topology_flags(topology: pd.DataFrame) -> pd.DataFrame:
    if topology.empty:
        return pd.DataFrame(
            columns=[
                "site",
                "panel_id",
                "matched_panel",
                "has_string",
                "has_mppt",
                "has_inverter",
            ]
        )

    flags = topology.assign(
        matched_panel=1,
        has_string=topology["string_id"].ne("").astype(int),
        has_mppt=topology["mppt_id"].ne("").astype(int),
        has_inverter=topology["inverter_id"].ne("").astype(int),
    )
    flags = (
        flags.groupby(["site", "panel_id"], dropna=False)
        .agg(
            matched_panel=("matched_panel", "max"),
            has_string=("has_string", "max"),
            has_mppt=("has_mppt", "max"),
            has_inverter=("has_inverter", "max"),
        )
        .reset_index()
    )
    return flags


def build_coverage(inventory: pd.DataFrame, topology: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    flags = build_panel_topology_flags(topology)
    merged = inventory.merge(flags, on=["site", "panel_id"], how="left")
    for col in ["matched_panel", "has_string", "has_mppt", "has_inverter"]:
        merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(0).astype(int)

    coverage = (
        merged.groupby("site", dropna=False)
        .agg(
            total_panels=("panel_id", "size"),
            matched_panels=("matched_panel", "sum"),
            string_matched_panels=("has_string", "sum"),
            mppt_matched_panels=("has_mppt", "sum"),
            inverter_matched_panels=("has_inverter", "sum"),
        )
        .reset_index()
    )
    coverage["coverage_rate"] = safe_rate(coverage["matched_panels"], coverage["total_panels"])
    coverage["string_coverage_rate"] = safe_rate(coverage["string_matched_panels"], coverage["total_panels"])
    coverage["mppt_coverage_rate"] = safe_rate(coverage["mppt_matched_panels"], coverage["total_panels"])
    coverage["inverter_coverage_rate"] = safe_rate(coverage["inverter_matched_panels"], coverage["total_panels"])
    coverage = coverage[COVERAGE_COLS].copy()

    missing = merged.loc[
        (merged["has_string"] == 0) | (merged["has_mppt"] == 0) | (merged["has_inverter"] == 0),
        ["site", "panel_id", "has_string", "has_mppt", "has_inverter"],
    ].copy()
    missing["missing_string"] = (1 - missing["has_string"]).astype(int)
    missing["missing_mppt"] = (1 - missing["has_mppt"]).astype(int)
    missing["missing_inverter"] = (1 - missing["has_inverter"]).astype(int)
    missing = missing[MISSING_COLS].sort_values(["site", "panel_id"], kind="stable").reset_index(drop=True)

    return coverage, missing


def build_duplicates(topology: pd.DataFrame, inventory: pd.DataFrame) -> pd.DataFrame:
    if topology.empty:
        return pd.DataFrame(columns=DUPLICATE_COLS)

    inventory_sites = (
        inventory.groupby("panel_id", dropna=False)["site"]
        .agg(join_distinct)
        .rename("inventory_sites_seen")
        .reset_index()
    )

    grouped = (
        topology.groupby("panel_id", dropna=False)
        .agg(
            row_count=("panel_id", "size"),
            sites_seen=("site", join_distinct),
            string_ids_seen=("string_id", join_distinct),
            mppt_ids_seen=("mppt_id", join_distinct),
            inverter_ids_seen=("inverter_id", join_distinct),
        )
        .reset_index()
    )
    grouped = grouped.merge(inventory_sites, on="panel_id", how="left")
    grouped["inventory_sites_seen"] = normalized_text(grouped["inventory_sites_seen"])
    grouped["duplicate_flag"] = grouped["row_count"].gt(1).astype(int)
    grouped["conflict_flag"] = (
        grouped[["sites_seen", "string_ids_seen", "mppt_ids_seen", "inverter_ids_seen"]]
        .apply(
            lambda row: int(
                any("|" in str(value) for value in row)
            ),
            axis=1,
        )
    )
    grouped["site_mismatch_flag"] = grouped.apply(
        lambda row: int(
            bool(str(row["inventory_sites_seen"]).strip())
            and bool(str(row["sites_seen"]).strip())
            and str(row["inventory_sites_seen"]).strip() != str(row["sites_seen"]).strip()
        ),
        axis=1,
    )
    grouped = grouped.loc[
        (grouped["duplicate_flag"] == 1)
        | (grouped["conflict_flag"] == 1)
        | (grouped["site_mismatch_flag"] == 1)
    ].copy()
    if grouped.empty:
        return pd.DataFrame(columns=DUPLICATE_COLS)
    grouped = grouped[DUPLICATE_COLS].sort_values(["panel_id"], kind="stable").reset_index(drop=True)
    return grouped


def build_topology_inventory(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    inventory = load_panel_inventory(root)
    topology = load_topology(root / "data" / "manual" / "site_topology.csv")
    coverage, missing = build_coverage(inventory, topology)
    duplicates = build_duplicates(topology, inventory)
    return coverage, missing, duplicates


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    coverage, missing, duplicates = build_topology_inventory(root)

    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    coverage.to_csv(share_dir / "site_topology_coverage.csv", index=False, encoding="utf-8-sig")
    missing.to_csv(share_dir / "site_topology_missing.csv", index=False, encoding="utf-8-sig")
    duplicates.to_csv(share_dir / "site_topology_duplicates.csv", index=False, encoding="utf-8-sig")

    print(
        "built topology inventory QA: "
        f"sites={len(coverage)}, missing_rows={len(missing)}, duplicate_rows={len(duplicates)}"
    )


if __name__ == "__main__":
    main()
