#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

KEY_COLS = ["site", "panel_id", "strict_trigger_date"]
READY_STATUS = "ready_for_copyback_preview"
SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
CANONICAL_EDIT_COLS = ["candidate_validity", "date_judgement", "note"]
COPYBACK_ROW_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "candidate_validity_current",
    "candidate_validity_proposed",
    "candidate_validity_merged",
    "date_judgement_current",
    "date_judgement_proposed",
    "date_judgement_merged",
    "note_current",
    "note_proposed",
    "note_merged",
    "review_owner",
    "review_status",
    "conflict_type",
    "apply_ready_flag",
]
CONFLICT_COLS = [
    "conflict_type",
    "site",
    "panel_id",
    "strict_trigger_date",
    "candidate_validity_current",
    "candidate_validity_proposed",
    "date_judgement_current",
    "date_judgement_proposed",
    "note_current",
    "note_proposed",
    "review_owner",
    "review_status",
    "conflict_detail",
]
SUMMARY_COLS = [
    "canonical_row_count",
    "ready_row_count",
    "apply_ready_count",
    "conflict_count",
    "candidate_validity_conflict_count",
    "date_judgement_conflict_count",
    "no_matching_canonical_row_count",
    "untouched_or_nonready_count",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stage reviewer-filled round-1 truth rows into a preview-only canonical truth proposal."
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


def normalize_flag(value: object) -> int:
    if pd.isna(value):
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return 1 if float(value) != 0 else 0
    text = normalize_text(value).lower()
    return 1 if text in {"1", "1.0", "true", "yes", "y"} else 0


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


def build_note_merged(note_current: str, note_proposed: str) -> str:
    if not note_current and note_proposed:
        return note_proposed
    if note_current and not note_proposed:
        return note_current
    if not note_current and not note_proposed:
        return ""
    if note_current == note_proposed:
        return note_current
    return f"{note_current} || review_v1: {note_proposed}"


def build_conflict_result(
    candidate_validity_current: str,
    candidate_validity_proposed: str,
    date_judgement_current: str,
    date_judgement_proposed: str,
) -> tuple[str, str]:
    candidate_conflict = (
        bool(candidate_validity_current)
        and bool(candidate_validity_proposed)
        and candidate_validity_current != candidate_validity_proposed
    )
    date_conflict = bool(date_judgement_current) and bool(date_judgement_proposed) and date_judgement_current != date_judgement_proposed

    details: list[str] = []
    if candidate_conflict:
        details.append(
            "candidate_validity current="
            f"{candidate_validity_current} proposed={candidate_validity_proposed}"
        )
    if date_conflict:
        details.append(
            "date_judgement current="
            f"{date_judgement_current} proposed={date_judgement_proposed}"
        )

    if candidate_conflict:
        return "candidate_validity_conflict", "; ".join(details)
    if date_conflict:
        return "date_judgement_conflict", "; ".join(details)
    return "no_conflict", ""


def build_outputs(root: Path, sites: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    intake_preview_df = read_csv(root / "_share" / "truth_review_intake_preview_v1.csv")
    canonical_df = read_csv(root / "_share" / "panel_date_reaudit_working.csv")

    intake_preview_df = intake_preview_df.loc[intake_preview_df["site"].isin(sites)].copy()
    canonical_df = canonical_df.loc[canonical_df["site"].isin(sites)].copy()

    for col in KEY_COLS:
        normalizer = normalize_date if col == "strict_trigger_date" else normalize_text
        intake_preview_df[col] = intake_preview_df[col].map(normalizer)
        canonical_df[col] = canonical_df[col].map(normalizer)

    for col in [
        "candidate_validity_current",
        "date_judgement_current",
        "note_current",
        "candidate_validity_proposed",
        "date_judgement_proposed",
        "note_proposed",
        "review_owner",
        "review_status",
        "intake_row_status",
    ]:
        if col not in intake_preview_df.columns:
            intake_preview_df[col] = ""
        intake_preview_df[col] = intake_preview_df[col].map(normalize_text)
    if "copyback_ready_flag" not in intake_preview_df.columns:
        intake_preview_df["copyback_ready_flag"] = 0
    intake_preview_df["copyback_ready_flag"] = intake_preview_df["copyback_ready_flag"].map(normalize_flag)

    for col in CANONICAL_EDIT_COLS:
        if col not in canonical_df.columns:
            canonical_df[col] = ""
        canonical_df[col] = canonical_df[col].map(normalize_text)

    canonical_proposed_df = canonical_df.copy()
    canonical_proposed_df["_key"] = list(canonical_proposed_df.loc[:, KEY_COLS].itertuples(index=False, name=None))
    key_to_indices: dict[tuple[str, str, str], list[int]] = {}
    for idx, key in canonical_proposed_df["_key"].items():
        key_to_indices.setdefault(key, []).append(idx)

    ready_df = intake_preview_df.loc[
        intake_preview_df["intake_row_status"].eq(READY_STATUS)
        & intake_preview_df["copyback_ready_flag"].eq(1)
    ].copy()

    copyback_rows: list[dict[str, object]] = []
    conflict_rows: list[dict[str, object]] = []

    for _, ready_row in ready_df.iterrows():
        key = key_tuple_from_row(ready_row)
        matched_indices = key_to_indices.get(key, [])

        candidate_validity_proposed = normalize_text(ready_row["candidate_validity_proposed"])
        date_judgement_proposed = normalize_text(ready_row["date_judgement_proposed"])
        note_proposed = normalize_text(ready_row["note_proposed"])
        review_owner = normalize_text(ready_row["review_owner"])
        review_status = normalize_text(ready_row["review_status"])

        if not matched_indices:
            conflict_rows.append(
                {
                    "conflict_type": "no_matching_canonical_row",
                    "site": key[0],
                    "panel_id": key[1],
                    "strict_trigger_date": key[2],
                    "candidate_validity_current": "",
                    "candidate_validity_proposed": candidate_validity_proposed,
                    "date_judgement_current": "",
                    "date_judgement_proposed": date_judgement_proposed,
                    "note_current": "",
                    "note_proposed": note_proposed,
                    "review_owner": review_owner,
                    "review_status": review_status,
                    "conflict_detail": "ready intake row does not match any canonical strict case",
                }
            )
            continue

        canonical_row = canonical_proposed_df.loc[matched_indices[0]]
        candidate_validity_current = normalize_text(canonical_row["candidate_validity"])
        date_judgement_current = normalize_text(canonical_row["date_judgement"])
        note_current = normalize_text(canonical_row["note"])

        conflict_type, conflict_detail = build_conflict_result(
            candidate_validity_current=candidate_validity_current,
            candidate_validity_proposed=candidate_validity_proposed,
            date_judgement_current=date_judgement_current,
            date_judgement_proposed=date_judgement_proposed,
        )

        candidate_validity_merged = (
            candidate_validity_proposed if candidate_validity_proposed and conflict_type == "no_conflict" else candidate_validity_current
        )
        date_judgement_merged = (
            date_judgement_proposed if date_judgement_proposed and conflict_type == "no_conflict" else date_judgement_current
        )
        note_merged = build_note_merged(note_current=note_current, note_proposed=note_proposed)

        if conflict_type != "no_conflict":
            conflict_rows.append(
                {
                    "conflict_type": conflict_type,
                    "site": key[0],
                    "panel_id": key[1],
                    "strict_trigger_date": key[2],
                    "candidate_validity_current": candidate_validity_current,
                    "candidate_validity_proposed": candidate_validity_proposed,
                    "date_judgement_current": date_judgement_current,
                    "date_judgement_proposed": date_judgement_proposed,
                    "note_current": note_current,
                    "note_proposed": note_proposed,
                    "review_owner": review_owner,
                    "review_status": review_status,
                    "conflict_detail": conflict_detail,
                }
            )
            continue

        copyback_rows.append(
            {
                "site": key[0],
                "panel_id": key[1],
                "strict_trigger_date": key[2],
                "candidate_validity_current": candidate_validity_current,
                "candidate_validity_proposed": candidate_validity_proposed,
                "candidate_validity_merged": candidate_validity_merged,
                "date_judgement_current": date_judgement_current,
                "date_judgement_proposed": date_judgement_proposed,
                "date_judgement_merged": date_judgement_merged,
                "note_current": note_current,
                "note_proposed": note_proposed,
                "note_merged": note_merged,
                "review_owner": review_owner,
                "review_status": review_status,
                "conflict_type": "no_conflict",
                "apply_ready_flag": 1,
            }
        )

        canonical_proposed_df.loc[matched_indices, "candidate_validity"] = candidate_validity_merged
        canonical_proposed_df.loc[matched_indices, "date_judgement"] = date_judgement_merged
        canonical_proposed_df.loc[matched_indices, "note"] = note_merged

    copyback_rows_df = pd.DataFrame(copyback_rows, columns=COPYBACK_ROW_COLS)
    conflicts_df = pd.DataFrame(conflict_rows, columns=CONFLICT_COLS)
    canonical_output_df = canonical_proposed_df.drop(columns="_key")

    summary_row = {
        "canonical_row_count": int(len(canonical_output_df)),
        "ready_row_count": int(len(ready_df)),
        "apply_ready_count": int(len(copyback_rows_df)),
        "conflict_count": int(len(conflicts_df)),
        "candidate_validity_conflict_count": int((conflicts_df["conflict_type"] == "candidate_validity_conflict").sum())
        if not conflicts_df.empty
        else 0,
        "date_judgement_conflict_count": int((conflicts_df["conflict_type"] == "date_judgement_conflict").sum())
        if not conflicts_df.empty
        else 0,
        "no_matching_canonical_row_count": int((conflicts_df["conflict_type"] == "no_matching_canonical_row").sum())
        if not conflicts_df.empty
        else 0,
        "untouched_or_nonready_count": int(len(intake_preview_df) - len(ready_df)),
    }
    summary_df = pd.DataFrame([summary_row], columns=SUMMARY_COLS)
    return summary_df, canonical_output_df, copyback_rows_df, conflicts_df


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    summary_df, canonical_output_df, copyback_rows_df, conflicts_df = build_outputs(root=root, sites=args.sites)

    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(share_dir / "truth_review_copyback_apply_summary_v1.csv", index=False, encoding="utf-8-sig")
    canonical_output_df.to_csv(share_dir / "panel_date_reaudit_working_proposed_v1.csv", index=False, encoding="utf-8-sig")
    copyback_rows_df.to_csv(share_dir / "truth_review_copyback_rows_v1.csv", index=False, encoding="utf-8-sig")
    conflicts_df.to_csv(share_dir / "truth_review_copyback_conflicts_v1.csv", index=False, encoding="utf-8-sig")

    print(f"truth_review_copyback_rows_v1={len(copyback_rows_df)}")


if __name__ == "__main__":
    main()
