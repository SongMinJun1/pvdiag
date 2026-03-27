#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

KEY_COLS = ["site", "panel_id", "strict_trigger_date"]
SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
EDITABLE_COLS = ["candidate_validity", "date_judgement", "note", "review_owner", "review_status"]
ALLOWED_CANDIDATE_VALIDITY = {
    "true_positive",
    "group_side",
    "false_positive",
    "needs_more_info",
}
PREVIEW_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "candidate_validity_current",
    "date_judgement_current",
    "note_current",
    "candidate_validity_proposed",
    "date_judgement_proposed",
    "note_proposed",
    "review_owner",
    "review_status",
    "review_priority_bucket",
    "priority_score",
    "recommended_review_action",
    "intake_row_status",
    "copyback_ready_flag",
]
ISSUE_COLS = [
    "issue_type",
    "site",
    "panel_id",
    "strict_trigger_date",
    "candidate_validity_proposed",
    "date_judgement_proposed",
    "note_proposed",
    "review_owner",
    "review_status",
    "issue_detail",
]
SUMMARY_COLS = [
    "round1_expected_count",
    "template_row_count",
    "matched_row_count",
    "copyback_ready_count",
    "untouched_blank_count",
    "incomplete_missing_candidate_validity_count",
    "invalid_candidate_validity_count",
    "duplicate_submission_count",
    "unexpected_key_count",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and preview round-1 truth review intake without modifying the canonical truth file."
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
        help="Sites to include. Defaults to stable known sites.",
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


def key_tuple_from_row(row: pd.Series) -> tuple[str, str, str]:
    return (
        normalize_text(row["site"]),
        normalize_text(row["panel_id"]),
        normalize_date(row["strict_trigger_date"]),
    )


def all_editable_blank(row: pd.Series) -> bool:
    return all(not normalize_text(row[col]) for col in EDITABLE_COLS)


def any_nonblank_other_than_candidate(row: pd.Series) -> bool:
    return any(normalize_text(row[col]) for col in ["date_judgement", "note", "review_owner", "review_status"])


def determine_intake_status(template_row: pd.Series | None, has_duplicate: bool) -> str:
    if has_duplicate:
        return "duplicate_submission"
    if template_row is None or all_editable_blank(template_row):
        return "untouched_blank"

    candidate_validity = normalize_text(template_row["candidate_validity"])
    if candidate_validity in ALLOWED_CANDIDATE_VALIDITY:
        return "ready_for_copyback_preview"
    if not candidate_validity and any_nonblank_other_than_candidate(template_row):
        return "incomplete_missing_candidate_validity"
    if candidate_validity:
        return "invalid_candidate_validity"
    return "untouched_blank"


def build_outputs(root: Path, sites: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    batch_df = read_csv(root / "_share" / "truth_review_batch_v1.csv")
    template_df = read_csv(root / "_share" / "truth_review_copyback_template_v1.csv")
    canonical_df = read_csv(root / "_share" / "panel_date_reaudit_working.csv")

    for df in [batch_df, template_df, canonical_df]:
        for col in KEY_COLS:
            if col not in df.columns:
                raise SystemExit(f"missing required column: {col}")
            if col == "strict_trigger_date":
                df[col] = df[col].map(normalize_date)
            else:
                df[col] = df[col].map(normalize_text)

    batch_df = batch_df.loc[batch_df["site"].isin(sites)].copy()
    if batch_df.empty:
        raise SystemExit("truth_review_batch_v1.csv produced an empty round-1 universe")

    for col in ["review_priority_bucket", "recommended_review_action"]:
        if col not in batch_df.columns:
            raise SystemExit(f"missing required column in truth_review_batch_v1.csv: {col}")
        batch_df[col] = batch_df[col].map(normalize_text)
    if "priority_score" not in batch_df.columns:
        raise SystemExit("missing required column in truth_review_batch_v1.csv: priority_score")
    batch_df["priority_score"] = pd.to_numeric(batch_df["priority_score"], errors="coerce").fillna(0).astype(int)

    batch_df = (
        batch_df.groupby(KEY_COLS, as_index=False)
        .agg(
            review_priority_bucket=("review_priority_bucket", "first"),
            priority_score=("priority_score", "max"),
            recommended_review_action=("recommended_review_action", "first"),
        )
        .sort_values(["priority_score", "site", "strict_trigger_date", "panel_id"], ascending=[False, True, True, True])
        .reset_index(drop=True)
    )

    for col in EDITABLE_COLS:
        if col not in template_df.columns:
            template_df[col] = ""
        template_df[col] = template_df[col].map(normalize_text)
    template_df = template_df.loc[:, [*KEY_COLS, *EDITABLE_COLS]].copy()
    template_df["_template_row_number"] = range(1, len(template_df) + 1)

    for col in ["candidate_validity", "date_judgement", "note"]:
        if col not in canonical_df.columns:
            canonical_df[col] = ""
        canonical_df[col] = canonical_df[col].map(normalize_text)
    canonical_df = (
        canonical_df.loc[:, [*KEY_COLS, "candidate_validity", "date_judgement", "note"]]
        .groupby(KEY_COLS, as_index=False)
        .agg(
            candidate_validity_current=("candidate_validity", "first"),
            date_judgement_current=("date_judgement", "first"),
            note_current=("note", "first"),
        )
    )

    expected_keys = {tuple(row) for row in batch_df.loc[:, KEY_COLS].itertuples(index=False, name=None)}
    template_df["_key"] = list(template_df.loc[:, KEY_COLS].itertuples(index=False, name=None))
    template_df["_key_exists_in_expected"] = template_df["_key"].isin(expected_keys)

    duplicate_key_counts = template_df["_key"].value_counts()
    duplicate_keys = {key for key, count in duplicate_key_counts.items() if count > 1}

    matched_template_df = template_df.loc[template_df["_key_exists_in_expected"]].copy()
    template_group_map = {
        key: group.sort_values("_template_row_number").reset_index(drop=True)
        for key, group in matched_template_df.groupby("_key", sort=False)
    }

    preview_base = batch_df.merge(canonical_df, on=KEY_COLS, how="left")
    for col in ["candidate_validity_current", "date_judgement_current", "note_current"]:
        preview_base[col] = preview_base[col].map(normalize_text)

    preview_rows: list[dict[str, object]] = []
    for _, expected_row in preview_base.iterrows():
        key = key_tuple_from_row(expected_row)
        template_group = template_group_map.get(key)
        representative = template_group.iloc[0] if template_group is not None else None
        intake_row_status = determine_intake_status(representative, key in duplicate_keys)

        preview_rows.append(
            {
                "site": key[0],
                "panel_id": key[1],
                "strict_trigger_date": key[2],
                "candidate_validity_current": normalize_text(expected_row["candidate_validity_current"]),
                "date_judgement_current": normalize_text(expected_row["date_judgement_current"]),
                "note_current": normalize_text(expected_row["note_current"]),
                "candidate_validity_proposed": normalize_text(representative["candidate_validity"]) if representative is not None else "",
                "date_judgement_proposed": normalize_text(representative["date_judgement"]) if representative is not None else "",
                "note_proposed": normalize_text(representative["note"]) if representative is not None else "",
                "review_owner": normalize_text(representative["review_owner"]) if representative is not None else "",
                "review_status": normalize_text(representative["review_status"]) if representative is not None else "",
                "review_priority_bucket": normalize_text(expected_row["review_priority_bucket"]),
                "priority_score": int(expected_row["priority_score"]),
                "recommended_review_action": normalize_text(expected_row["recommended_review_action"]),
                "intake_row_status": intake_row_status,
                "copyback_ready_flag": 1 if intake_row_status == "ready_for_copyback_preview" else 0,
            }
        )
    preview_df = pd.DataFrame(preview_rows, columns=PREVIEW_COLS)

    issue_rows: list[dict[str, object]] = []
    for _, template_row in template_df.sort_values("_template_row_number").iterrows():
        key_exists = bool(template_row["_key_exists_in_expected"])
        key = template_row["_key"]
        candidate_validity = normalize_text(template_row["candidate_validity"])
        date_judgement = normalize_text(template_row["date_judgement"])
        note = normalize_text(template_row["note"])
        review_owner = normalize_text(template_row["review_owner"])
        review_status = normalize_text(template_row["review_status"])

        def append_issue(issue_type: str, detail: str) -> None:
            issue_rows.append(
                {
                    "issue_type": issue_type,
                    "site": key[0],
                    "panel_id": key[1],
                    "strict_trigger_date": key[2],
                    "candidate_validity_proposed": candidate_validity,
                    "date_judgement_proposed": date_judgement,
                    "note_proposed": note,
                    "review_owner": review_owner,
                    "review_status": review_status,
                    "issue_detail": detail,
                }
            )

        if not key_exists:
            append_issue("unexpected_key", "template key is not part of the round-1 review batch")
        if key in duplicate_keys:
            append_issue("duplicate_submission", "template contains multiple rows for the same strict case")
        if key_exists and candidate_validity and candidate_validity not in ALLOWED_CANDIDATE_VALIDITY:
            append_issue("invalid_candidate_validity", "candidate_validity_proposed is outside the allowed set")
        if key_exists and not candidate_validity and any([date_judgement, note, review_owner, review_status]):
            append_issue(
                "incomplete_missing_candidate_validity",
                "reviewer entered supporting fields but left candidate_validity_proposed blank",
            )

    issues_df = pd.DataFrame(issue_rows, columns=ISSUE_COLS)

    summary_df = pd.DataFrame(
        [
            {
                "round1_expected_count": int(len(preview_df)),
                "template_row_count": int(len(template_df)),
                "matched_row_count": int(template_df["_key_exists_in_expected"].sum()),
                "copyback_ready_count": int(preview_df["copyback_ready_flag"].sum()),
                "untouched_blank_count": int(preview_df["intake_row_status"].eq("untouched_blank").sum()),
                "incomplete_missing_candidate_validity_count": int(
                    len(issues_df.loc[issues_df["issue_type"].eq("incomplete_missing_candidate_validity")])
                ),
                "invalid_candidate_validity_count": int(
                    len(issues_df.loc[issues_df["issue_type"].eq("invalid_candidate_validity")])
                ),
                "duplicate_submission_count": int(len(issues_df.loc[issues_df["issue_type"].eq("duplicate_submission")])),
                "unexpected_key_count": int(len(issues_df.loc[issues_df["issue_type"].eq("unexpected_key")])),
            }
        ],
        columns=SUMMARY_COLS,
    )

    return summary_df, preview_df, issues_df


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    summary_df, preview_df, issues_df = build_outputs(root, list(args.sites))

    out_dir = root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(out_dir / "truth_review_intake_summary_v1.csv", index=False, encoding="utf-8-sig")
    preview_df.to_csv(out_dir / "truth_review_intake_preview_v1.csv", index=False, encoding="utf-8-sig")
    issues_df.to_csv(out_dir / "truth_review_intake_issues_v1.csv", index=False, encoding="utf-8-sig")
    print(f"truth_review_intake_preview_v1={len(preview_df)}")


if __name__ == "__main__":
    main()
