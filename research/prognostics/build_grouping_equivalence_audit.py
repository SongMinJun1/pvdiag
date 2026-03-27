#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

HYPOTHESIS_REQUIRED_COLS = ["site", "panel_id", "token0_uuid", "token1_group"]
LATEST_COLS = [
    "site",
    "panel_id",
    "current_group_key_base",
    "candidate_group_token0",
    "candidate_group_token0_token1",
    "match_token0",
    "match_token0_token1",
]
SUMMARY_COLS = [
    "site",
    "total_panels",
    "current_unique_groups",
    "candidate_token0_unique_groups",
    "candidate_token0_token1_unique_groups",
    "match_rate_token0",
    "match_rate_token0_token1",
    "mismatch_panels_token0",
    "mismatch_panels_token0_token1",
]
MISMATCH_COLS = [
    "site",
    "panel_id",
    "current_group_key_base",
    "candidate_group_token0",
    "candidate_group_token0_token1",
]
GROUPING_SOURCE_FILENAME = "panel_day_risk_ensemble.csv"
GROUPING_SOURCE_COL_CANDIDATES = ["current_group_key_base", "group_key_base"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit grouping equivalence between current group_key_base and panel_id-derived candidates.")
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


def find_group_col(df: pd.DataFrame, path: Path) -> str:
    for candidate in GROUPING_SOURCE_COL_CANDIDATES:
        if candidate in df.columns:
            return candidate
    raise SystemExit(
        f"missing grouping column in {path}; expected one of {GROUPING_SOURCE_COL_CANDIDATES}"
    )


def load_hypothesis(root: Path) -> pd.DataFrame:
    path = root / "_share" / "site_panel_id_hypothesis_latest.csv"
    if not path.exists():
        raise SystemExit(f"missing hypothesis input: {path}")
    hypothesis = read_csv(path)
    missing = [col for col in HYPOTHESIS_REQUIRED_COLS if col not in hypothesis.columns]
    if missing:
        raise SystemExit(f"{path} missing required columns: {missing}")
    subset = hypothesis[HYPOTHESIS_REQUIRED_COLS].copy()
    subset["site"] = normalized_text(subset["site"])
    subset["panel_id"] = normalized_text(subset["panel_id"])
    subset["token0_uuid"] = normalized_text(subset["token0_uuid"])
    subset["token1_group"] = normalized_text(subset["token1_group"])
    subset = subset.loc[subset["site"].ne("") & subset["panel_id"].ne("")].copy()
    subset = subset.drop_duplicates(["site", "panel_id"], keep="last").reset_index(drop=True)
    return subset


def load_current_grouping(root: Path, sites: list[str]) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []

    for site in sorted(sites):
        path = root / "data" / site / "out" / GROUPING_SOURCE_FILENAME
        if not path.exists():
            raise SystemExit(f"missing grouping source file for site={site}: {path}")
        source = read_csv(path)
        if "panel_id" not in source.columns:
            raise SystemExit(f"{path} missing required column: panel_id")
        group_col = find_group_col(source, path)
        if "site" not in source.columns:
            source = source.assign(site=site)
        subset = source[["site", "panel_id", group_col]].copy()
        subset.columns = ["site", "panel_id", "current_group_key_base"]
        subset["site"] = normalized_text(subset["site"])
        subset["panel_id"] = normalized_text(subset["panel_id"])
        subset["current_group_key_base"] = normalized_text(subset["current_group_key_base"])
        subset = subset.loc[subset["site"].eq(site) & subset["panel_id"].ne("")].copy()
        if subset["current_group_key_base"].eq("").all():
            raise SystemExit(f"{path} has blank current grouping values for site={site}")

        per_panel = (
            subset.groupby(["site", "panel_id"], dropna=False)["current_group_key_base"]
            .nunique(dropna=True)
            .reset_index(name="group_count")
        )
        unstable = per_panel.loc[per_panel["group_count"].gt(1)].copy()
        if not unstable.empty:
            sample = unstable.head(10).to_dict("records")
            raise SystemExit(
                f"{path} has multiple current grouping values for some panels; sample={sample}"
            )

        subset = subset.drop_duplicates(["site", "panel_id"], keep="last")
        rows.append(subset)

    current = pd.concat(rows, ignore_index=True)
    current = current.sort_values(["site", "panel_id"], kind="stable").reset_index(drop=True)
    return current


def build_latest(hypothesis: pd.DataFrame, current: pd.DataFrame) -> pd.DataFrame:
    merged = hypothesis.merge(current, on=["site", "panel_id"], how="inner", validate="one_to_one")
    if len(merged) != len(hypothesis):
        missing = hypothesis.merge(current, on=["site", "panel_id"], how="left", indicator=True)
        missing = missing.loc[missing["_merge"].eq("left_only"), ["site", "panel_id"]]
        raise SystemExit(
            "current grouping source is missing rows for some hypothesis panels; "
            f"sample={missing.head(10).to_dict('records')}"
        )

    merged["candidate_group_token0"] = merged["token0_uuid"]
    merged["candidate_group_token0_token1"] = merged.apply(
        lambda row: f"{row['token0_uuid']}.{row['token1_group']}"
        if str(row["token0_uuid"]).strip() and str(row["token1_group"]).strip()
        else "",
        axis=1,
    )
    merged["match_token0"] = merged["current_group_key_base"].eq(merged["candidate_group_token0"]).astype(int)
    merged["match_token0_token1"] = merged["current_group_key_base"].eq(merged["candidate_group_token0_token1"]).astype(int)
    latest = merged[LATEST_COLS].copy()
    latest = latest.sort_values(["site", "panel_id"], kind="stable").reset_index(drop=True)
    return latest


def build_summary(latest: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for site, site_df in latest.groupby("site", sort=True):
        total = int(len(site_df))
        match_token0 = int(site_df["match_token0"].sum())
        match_token0_token1 = int(site_df["match_token0_token1"].sum())
        rows.append(
            {
                "site": site,
                "total_panels": total,
                "current_unique_groups": int(site_df["current_group_key_base"].nunique(dropna=True)),
                "candidate_token0_unique_groups": int(site_df["candidate_group_token0"].replace("", pd.NA).nunique(dropna=True)),
                "candidate_token0_token1_unique_groups": int(site_df["candidate_group_token0_token1"].replace("", pd.NA).nunique(dropna=True)),
                "match_rate_token0": safe_rate(match_token0, total),
                "match_rate_token0_token1": safe_rate(match_token0_token1, total),
                "mismatch_panels_token0": int(total - match_token0),
                "mismatch_panels_token0_token1": int(total - match_token0_token1),
            }
        )
    summary = pd.DataFrame(rows)
    return summary[SUMMARY_COLS].copy()


def build_mismatches(latest: pd.DataFrame) -> pd.DataFrame:
    mismatches = latest.loc[
        latest["match_token0"].eq(0) | latest["match_token0_token1"].eq(0),
        MISMATCH_COLS,
    ].copy()
    mismatches = mismatches.sort_values(["site", "panel_id"], kind="stable").reset_index(drop=True)
    return mismatches


def build_grouping_equivalence_audit(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    hypothesis = load_hypothesis(root)
    current = load_current_grouping(root, hypothesis["site"].dropna().astype(str).unique().tolist())
    latest = build_latest(hypothesis, current)
    summary = build_summary(latest)
    mismatches = build_mismatches(latest)
    return latest, summary, mismatches


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    latest, summary, mismatches = build_grouping_equivalence_audit(root)

    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    latest.to_csv(share_dir / "site_grouping_equivalence_latest.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(share_dir / "site_grouping_equivalence_summary.csv", index=False, encoding="utf-8-sig")
    mismatches.to_csv(share_dir / "site_grouping_mismatches.csv", index=False, encoding="utf-8-sig")

    print(
        "built grouping equivalence audit: "
        f"rows={len(latest)}, mismatch_rows={len(mismatches)}, sites={summary['site'].nunique()}"
    )


if __name__ == "__main__":
    main()
