#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

PANEL_MULTIAXIS_VERDICT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
FAULT_PANEL_EVENT_AUDIT_NAME = "panel_day_engine_fault_panel_event_audit_v1.csv"

AUDIT_OUTPUT_NAME = "panel_day_engine_detailed_fault_bridge_audit_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_detailed_fault_bridge_summary_v1.csv"

CANDIDATE_RELATIVE_PATHS = [
    Path("data/pvfault/out/PVFAULT_labels_day.csv"),
    Path("_share/external_pvfault_20260304/PVFAULT_labels_day.csv"),
    Path("_share/external_pvfault_20260304_215400/PVFAULT_labels_day.csv"),
    Path("_share/external_pvfault_fixlabel_20260304_174840/PVFAULT_labels_day.csv"),
    Path("_share/final_validation_20260304_172755/pvfault/PVFAULT_labels_day.csv"),
]

AUDIT_COLS = [
    "site",
    "panel_id",
    "reference_date",
    "exact_match_file_count",
    "matched_files_csv",
    "matched_fault_type_values_csv",
    "consensus_fault_type_code",
    "attachable_flag",
    "attach_reason_ko",
]

SUMMARY_COLS = [
    "고장패널수",
    "세부fault_부착수",
    "세부fault_보류수",
    "exact_date_match_패널수",
    "exact_date_conflict_패널수",
    "exact_date_miss_패널수",
    "note_ko",
]

REASON_CONSENSUS = "exact_date_consensus"
REASON_CONFLICT = "exact_date_conflict"
REASON_MISS = "no_exact_date_match"
REASON_UNRESOLVED = "reference_date_unresolved"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit exact-date PVFAULT detailed fault-type attachment candidates for current fault panels."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to the project root.",
    )
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for column in out.columns:
        if out[column].dtype == object:
            out[column] = out[column].map(normalize_text)
    return out


def load_candidate_frames(root: Path) -> list[tuple[str, pd.DataFrame]]:
    loaded: list[tuple[str, pd.DataFrame]] = []
    for rel_path in CANDIDATE_RELATIVE_PATHS:
        path = root / rel_path
        if not path.exists():
            continue
        df = read_csv(path)
        ensure_columns(df, ["date", "panel_id", "fault_type_max"], rel_path.as_posix())
        loaded.append((rel_path.as_posix(), normalize_df(df)))
    if not loaded:
        raise SystemExit("no PVFAULT_labels_day.csv candidate files are available")
    return loaded


def build_reference_lookup(audit_df: pd.DataFrame) -> dict[tuple[str, str], str]:
    ensure_columns(
        audit_df,
        ["site", "panel_id", "strict_trigger_date", "first_final_fault_date"],
        FAULT_PANEL_EVENT_AUDIT_NAME,
    )
    if audit_df[["site", "panel_id"]].duplicated().any():
        dup = audit_df.loc[audit_df[["site", "panel_id"]].duplicated(keep=False), ["site", "panel_id"]]
        raise SystemExit(f"{FAULT_PANEL_EVENT_AUDIT_NAME} must be unique by (site, panel_id): {dup.to_dict(orient='records')[:5]}")
    lookup: dict[tuple[str, str], str] = {}
    for row in audit_df.to_dict(orient="records"):
        key = (normalize_text(row["site"]), normalize_text(row["panel_id"]))
        strict_trigger = normalize_text(row["strict_trigger_date"])
        first_final_fault = normalize_text(row["first_final_fault_date"])
        lookup[key] = strict_trigger or first_final_fault
    return lookup


def collect_fault_panel_rows(verdict_df: pd.DataFrame) -> pd.DataFrame:
    ensure_columns(verdict_df, ["site", "panel_id", "패널고장여부_ko"], PANEL_MULTIAXIS_VERDICT_NAME)
    fault_df = verdict_df.loc[verdict_df["패널고장여부_ko"].map(normalize_text).eq("고장"), ["site", "panel_id"]].copy()
    if fault_df[["site", "panel_id"]].duplicated().any():
        dup = fault_df.loc[fault_df[["site", "panel_id"]].duplicated(keep=False), ["site", "panel_id"]]
        raise SystemExit(f"{PANEL_MULTIAXIS_VERDICT_NAME} fault rows must be unique by (site, panel_id): {dup.to_dict(orient='records')[:5]}")
    if len(fault_df) != 6:
        raise SystemExit(f"fault-panel base universe must be 6 rows, found {len(fault_df)}")
    return fault_df.sort_values(["site", "panel_id"]).reset_index(drop=True)


def evaluate_fault_panel(
    *,
    site: str,
    panel_id: str,
    reference_date: str,
    candidate_frames: list[tuple[str, pd.DataFrame]],
) -> dict[str, object]:
    matched_files: list[str] = []
    matched_values: list[str] = []

    if reference_date:
        for display_path, candidate_df in candidate_frames:
            matched_df = candidate_df.loc[
                candidate_df["panel_id"].map(normalize_text).eq(panel_id)
                & candidate_df["date"].map(normalize_text).eq(reference_date)
            ].copy()
            if matched_df.empty:
                continue
            matched_files.append(display_path)
            matched_values.extend(
                [
                    normalize_text(value)
                    for value in matched_df["fault_type_max"].tolist()
                    if normalize_text(value)
                ]
            )

    unique_values = sorted(set(matched_values))
    exact_match_file_count = len(matched_files)
    if not reference_date:
        reason = REASON_UNRESOLVED
        attachable = 0
        consensus = ""
    elif exact_match_file_count == 0:
        reason = REASON_MISS
        attachable = 0
        consensus = ""
    elif len(unique_values) == 1:
        reason = REASON_CONSENSUS
        attachable = 1
        consensus = unique_values[0]
    else:
        reason = REASON_CONFLICT
        attachable = 0
        consensus = ""

    return {
        "site": site,
        "panel_id": panel_id,
        "reference_date": reference_date,
        "exact_match_file_count": exact_match_file_count,
        "matched_files_csv": "|".join(matched_files),
        "matched_fault_type_values_csv": "|".join(unique_values),
        "consensus_fault_type_code": consensus,
        "attachable_flag": attachable,
        "attach_reason_ko": reason,
    }


def build_outputs(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    share_dir = root / "_share"
    verdict_df = normalize_df(read_csv(share_dir / PANEL_MULTIAXIS_VERDICT_NAME))
    fault_audit_df = normalize_df(read_csv(share_dir / FAULT_PANEL_EVENT_AUDIT_NAME))
    candidate_frames = load_candidate_frames(root)

    fault_panels_df = collect_fault_panel_rows(verdict_df)
    reference_lookup = build_reference_lookup(fault_audit_df)

    rows: list[dict[str, object]] = []
    for row in fault_panels_df.to_dict(orient="records"):
        key = (normalize_text(row["site"]), normalize_text(row["panel_id"]))
        rows.append(
            evaluate_fault_panel(
                site=key[0],
                panel_id=key[1],
                reference_date=reference_lookup.get(key, ""),
                candidate_frames=candidate_frames,
            )
        )

    audit_df = pd.DataFrame(rows).reindex(columns=AUDIT_COLS)
    attached_count = int(pd.to_numeric(audit_df["attachable_flag"], errors="coerce").fillna(0).sum())
    conflict_count = int(audit_df["attach_reason_ko"].eq(REASON_CONFLICT).sum())
    miss_count = int(audit_df["attach_reason_ko"].isin([REASON_MISS, REASON_UNRESOLVED]).sum())
    exact_match_panel_count = int(pd.to_numeric(audit_df["exact_match_file_count"], errors="coerce").fillna(0).gt(0).sum())

    summary_df = pd.DataFrame(
        [
            {
                "고장패널수": int(len(audit_df)),
                "세부fault_부착수": attached_count,
                "세부fault_보류수": int(len(audit_df) - attached_count),
                "exact_date_match_패널수": exact_match_panel_count,
                "exact_date_conflict_패널수": conflict_count,
                "exact_date_miss_패널수": miss_count,
                "note_ko": (
                    "세부 fault type은 PVFAULT_labels_day.csv exact-date consensus로만 붙인다. "
                    "nearest-date heuristic은 쓰지 않고, file 간 conflict가 나면 보류한다. "
                    "이 축은 GPVS family attachment와 별개다."
                ),
            }
        ]
    ).reindex(columns=SUMMARY_COLS)
    return audit_df, summary_df


def write_outputs(root: Path, audit_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    audit_df.to_csv(share_dir / AUDIT_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    audit_df, summary_df = build_outputs(root)
    write_outputs(root, audit_df, summary_df)


if __name__ == "__main__":
    main()
