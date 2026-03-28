#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

KEY_COLS = ["site", "panel_id", "strict_trigger_date"]
SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
HOLD_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "review_priority_bucket",
    "priority_score",
    "critical_phenotype_v3",
    "actionability_v3",
    "hold_reason",
    "hold_status",
    "reactivation_condition",
]
SUMMARY_COLS = [
    "record_type",
    "original_batch_count",
    "deferred_hold_count",
    "active_batch_v2_count",
    "deferred_site_count",
    "site",
    "active_batch_v2_count_after_hold",
    "site_handling_recommendation",
]
HOLD_REASON = "deferred_high_actionability_without_field_evidence"
HOLD_STATUS = "on_hold"
REACTIVATION_CONDITION = "field_or_OM_evidence_available"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Formalize a deferred-hold registry and clean active truth review queue without changing score."
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


def drop_embedded_header_rows(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    if any(col not in df.columns for col in cols):
        return df
    header_mask = pd.Series(True, index=df.index)
    for col in cols:
        header_mask &= df[col].map(normalize_text).eq(col)
    if not bool(header_mask.any()):
        return df
    return df.loc[~header_mask].copy()


def dedupe(df: pd.DataFrame, name: str, cols: list[str]) -> pd.DataFrame:
    dupes = df.loc[df.duplicated(subset=cols, keep=False), cols]
    if not dupes.empty:
        raise SystemExit(f"{name} has duplicate rows on {cols}")
    return df


def build_site_summary(
    active_batch_df: pd.DataFrame,
    deferred_hold_df: pd.DataFrame,
    site_manifest_df: pd.DataFrame,
    sites: list[str],
) -> pd.DataFrame:
    site_order = {site: idx for idx, site in enumerate(sites)}
    manifest_sites = (
        site_manifest_df.loc[:, ["site"]]
        .drop_duplicates()
        .assign(_site_rank=lambda df: df["site"].map(lambda value: site_order.get(value, len(site_order))))
        .sort_values(["_site_rank", "site"], ascending=[True, True])
    )

    rows: list[dict[str, object]] = []
    for site in manifest_sites["site"].tolist():
        deferred_count = int(deferred_hold_df["site"].eq(site).sum())
        rows.append(
            {
                "record_type": "site",
                "original_batch_count": pd.NA,
                "deferred_hold_count": deferred_count,
                "active_batch_v2_count": pd.NA,
                "deferred_site_count": pd.NA,
                "site": site,
                "active_batch_v2_count_after_hold": int(active_batch_df["site"].eq(site).sum()),
                "site_handling_recommendation": (
                    "keep_on_hold_until_field_evidence" if deferred_count > 0 else "no_deferred_hold_rows"
                ),
            }
        )

    return pd.DataFrame(rows, columns=SUMMARY_COLS)


def build_outputs(root: Path, sites: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    hold_cases_df = drop_embedded_header_rows(read_csv(root / "_share" / "score_scope_manifest_cases_v1.csv"), KEY_COLS)
    site_manifest_df = drop_embedded_header_rows(read_csv(root / "_share" / "score_scope_manifest_sites_v1.csv"), ["site"])
    batch_df = drop_embedded_header_rows(read_csv(root / "_share" / "truth_review_batch_v1.csv"), KEY_COLS)

    ensure_columns(
        hold_cases_df,
        [
            *KEY_COLS,
            "scope_class",
            "review_priority_bucket",
            "priority_score",
            "critical_phenotype_v3",
            "actionability_v3",
        ],
        "score_scope_manifest_cases_v1.csv",
    )
    ensure_columns(site_manifest_df, ["site", "recommended_site_handling"], "score_scope_manifest_sites_v1.csv")
    ensure_columns(batch_df, KEY_COLS, "truth_review_batch_v1.csv")

    for df in [hold_cases_df, site_manifest_df, batch_df]:
        if "site" in df.columns:
            df["site"] = df["site"].map(normalize_text)
    for df in [hold_cases_df, batch_df]:
        df["panel_id"] = df["panel_id"].map(normalize_text)
        df["strict_trigger_date"] = df["strict_trigger_date"].map(normalize_date)

    hold_cases_df = hold_cases_df.loc[hold_cases_df["site"].isin(sites)].copy()
    site_manifest_df = site_manifest_df.loc[site_manifest_df["site"].isin(sites)].copy()
    batch_df = batch_df.loc[batch_df["site"].isin(sites)].copy()

    if site_manifest_df.empty:
        raise SystemExit("score_scope_manifest_sites_v1.csv produced an empty site manifest")

    for col in ["scope_class", "review_priority_bucket", "critical_phenotype_v3", "actionability_v3"]:
        hold_cases_df[col] = hold_cases_df[col].map(normalize_text)
    hold_cases_df["priority_score"] = pd.to_numeric(hold_cases_df["priority_score"], errors="coerce").fillna(0).astype(int)
    site_manifest_df["recommended_site_handling"] = site_manifest_df["recommended_site_handling"].map(normalize_text)

    eligible_sites = dedupe(
        site_manifest_df.loc[:, ["site", "recommended_site_handling"]],
        "score_scope_manifest_sites_v1.csv",
        ["site"],
    )
    eligible_sites = eligible_sites.loc[
        eligible_sites["recommended_site_handling"].eq("score_with_deferred_note")
    ].copy()

    batch_df = batch_df.copy()
    batch_df["_batch_row_order"] = range(len(batch_df))
    batch_order_df = batch_df.loc[:, [*KEY_COLS, "_batch_row_order"]].copy()

    deferred_hold_df = hold_cases_df.loc[
        hold_cases_df["scope_class"].eq("deferred_unlabeled_high_actionability")
    ].copy()
    deferred_hold_df = deferred_hold_df.merge(eligible_sites.loc[:, ["site"]], on="site", how="inner")
    deferred_hold_df = dedupe(
        deferred_hold_df.loc[
            :, [*KEY_COLS, "review_priority_bucket", "priority_score", "critical_phenotype_v3", "actionability_v3"]
        ],
        "truth_review_deferred_hold_v1 selection",
        KEY_COLS,
    )
    deferred_hold_df = deferred_hold_df.merge(batch_order_df, on=KEY_COLS, how="left")
    deferred_hold_df["hold_reason"] = HOLD_REASON
    deferred_hold_df["hold_status"] = HOLD_STATUS
    deferred_hold_df["reactivation_condition"] = REACTIVATION_CONDITION
    deferred_hold_df = deferred_hold_df.sort_values(
        ["_batch_row_order", "priority_score", "site", "strict_trigger_date", "panel_id"],
        ascending=[True, False, True, True, True],
        na_position="last",
    ).reset_index(drop=True)
    deferred_hold_output = deferred_hold_df.loc[:, HOLD_COLS]

    hold_keys = deferred_hold_output.loc[:, KEY_COLS].drop_duplicates().assign(_deferred_hold_flag=1)
    active_batch_df = batch_df.merge(hold_keys, on=KEY_COLS, how="left")
    active_batch_df = active_batch_df.loc[active_batch_df["_deferred_hold_flag"].fillna(0).eq(0)].copy()
    active_batch_df = active_batch_df.sort_values("_batch_row_order").reset_index(drop=True)
    active_batch_output = active_batch_df.loc[:, [col for col in batch_df.columns if col != "_batch_row_order"]]

    summary_rows = [
        {
            "record_type": "summary",
            "original_batch_count": int(len(batch_df)),
            "deferred_hold_count": int(len(deferred_hold_output)),
            "active_batch_v2_count": int(len(active_batch_output)),
            "deferred_site_count": int(deferred_hold_output["site"].nunique()),
            "site": "",
            "active_batch_v2_count_after_hold": pd.NA,
            "site_handling_recommendation": "",
        }
    ]
    site_summary_df = build_site_summary(active_batch_output, deferred_hold_output, site_manifest_df, sites)
    summary_output = pd.concat([pd.DataFrame(summary_rows, columns=SUMMARY_COLS), site_summary_df], ignore_index=True)

    return deferred_hold_output, active_batch_output, summary_output.loc[:, SUMMARY_COLS]


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    deferred_hold_output, active_batch_output, summary_output = build_outputs(root, list(args.sites))

    out_dir = root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    deferred_hold_output.to_csv(out_dir / "truth_review_deferred_hold_v1.csv", index=False, encoding="utf-8-sig")
    active_batch_output.to_csv(out_dir / "truth_review_active_batch_v2.csv", index=False, encoding="utf-8-sig")
    summary_output.to_csv(out_dir / "truth_review_deferred_summary_v1.csv", index=False, encoding="utf-8-sig")
    print(
        "truth_review_deferred_hold_v1="
        f"{len(deferred_hold_output)} truth_review_active_batch_v2={len(active_batch_output)}"
    )


if __name__ == "__main__":
    main()
