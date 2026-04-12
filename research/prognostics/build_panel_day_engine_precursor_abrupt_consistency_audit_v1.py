#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

PRECURSOR_TRUTH_NAME = "panel_day_engine_precursor_onset_truth_v1.csv"
NON_PRECURSOR_CASES_NAME = "panel_day_engine_non_precursor_performance_cases_v1.csv"
ABRUPT6_NAME = "panel_day_engine_abrupt6_symptom_map_v1.csv"
MULTIAXIS_VERDICT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
EVENT_SUPPLEMENT_NAME = "panel_day_engine_panel_multiaxis_event_supplement_v1.csv"
REAUDIT_NAME = "panel_date_reaudit_working.csv"

CASES_OUTPUT_NAME = "panel_day_engine_precursor_abrupt_consistency_cases_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_precursor_abrupt_consistency_summary_v1.csv"
RECOMMENDATION_OUTPUT_NAME = "panel_day_engine_precursor_abrupt_consistency_recommendation_v1.csv"

CASE_COLS = [
    "site",
    "panel_id",
    "precursor_onset_date",
    "precursor_fault_date",
    "abrupt_anchor_date",
    "abrupt_fault_date",
    "lead_days_from_precursor_to_abrupt_fault",
    "same_event_flag",
    "distinct_event_flag",
    "consistency_judgment_ko",
    "reasoning_ko",
]

SUMMARY_COLS = [
    "overlap_panel_count",
    "same_event_count",
    "distinct_event_count",
    "ambiguous_count",
    "current_unique_fault_panel_count",
    "current_precursor_event_count",
    "current_abrupt_event_count",
    "corrected_precursor_led_fault_count",
    "corrected_pure_abrupt_fault_count",
    "note_ko",
]

RECOMMENDATION_COLS = [
    "recommended_next_handling",
    "rationale_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit whether overlap precursor/abrupt panels represent the same fault events or distinct events."
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
    df = pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
    for column in df.columns:
        if df[column].dtype == object:
            df[column] = df[column].map(normalize_text)
    return df


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def first_existing_column(df: pd.DataFrame, candidates: list[str], frame_name: str) -> str:
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    raise SystemExit(f"{frame_name} missing any of columns: {candidates}")


def parse_date(value: object) -> pd.Timestamp | pd.NaT:
    text = normalize_text(value)
    if not text:
        return pd.NaT
    return pd.to_datetime(text, errors="coerce")


def format_date(value: pd.Timestamp | pd.NaT) -> str:
    if pd.isna(value):
        return ""
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def days_between(start: pd.Timestamp | pd.NaT, end: pd.Timestamp | pd.NaT) -> int | None:
    if pd.isna(start) or pd.isna(end):
        return None
    return int((pd.Timestamp(end) - pd.Timestamp(start)).days)


def first_valid_date(values: list[object]) -> pd.Timestamp | pd.NaT:
    parsed = [parse_date(value) for value in values]
    valid = [value for value in parsed if not pd.isna(value)]
    if not valid:
        return pd.NaT
    return min(valid)


def load_inputs(root: Path) -> dict[str, pd.DataFrame]:
    share = root / "_share"
    frames = {
        "precursor": read_csv(share / PRECURSOR_TRUTH_NAME),
        "non_precursor": read_csv(share / NON_PRECURSOR_CASES_NAME),
        "abrupt6": read_csv(share / ABRUPT6_NAME),
        "verdict": read_csv(share / MULTIAXIS_VERDICT_NAME),
        "event": read_csv(share / EVENT_SUPPLEMENT_NAME),
        "reaudit": read_csv(share / REAUDIT_NAME),
    }
    ensure_columns(
        frames["precursor"],
        [
            "site",
            "fault_start_date",
            "selected_episode_end_date",
            "preferred_precursor_onset_date",
        ],
        PRECURSOR_TRUTH_NAME,
    )
    ensure_columns(
        frames["non_precursor"],
        [
            "site",
            "panel_id",
            "anchor_date",
            "first_confirmed_fault_date",
            "first_critical_fault_date",
            "first_final_fault_date",
        ],
        NON_PRECURSOR_CASES_NAME,
    )
    ensure_columns(frames["abrupt6"], ["site", "panel_id", "고장시점"], ABRUPT6_NAME)
    ensure_columns(
        frames["verdict"],
        ["site", "panel_id", "패널고장여부_ko", "전조형이력_flag", "급작고장이력_flag"],
        MULTIAXIS_VERDICT_NAME,
    )
    ensure_columns(frames["event"], ["site", "panel_id", "사건유형_ko"], EVENT_SUPPLEMENT_NAME)
    ensure_columns(
        frames["reaudit"],
        ["site", "panel_id", "strict_trigger_date", "first_warning_date", "retrospective_onset_date"],
        REAUDIT_NAME,
    )
    return frames


def build_overlap_df(precursor_df: pd.DataFrame, abrupt_df: pd.DataFrame) -> pd.DataFrame:
    panel_col = first_existing_column(
        precursor_df,
        ["panel_id", "display_entity_id", "entity_id", "panel_entity_id"],
        PRECURSOR_TRUTH_NAME,
    )
    positive_precursor_df = precursor_df.loc[precursor_df["preferred_precursor_onset_date"].ne("")].copy()
    positive_precursor_df = positive_precursor_df.rename(columns={panel_col: "panel_id"})
    overlap_df = positive_precursor_df.merge(abrupt_df, on=["site", "panel_id"], how="inner")
    overlap_df = overlap_df.drop_duplicates(subset=["site", "panel_id"]).copy()
    if len(overlap_df) != 2:
        raise SystemExit(f"expected overlap panel count 2, found {len(overlap_df)}")
    return overlap_df


def load_panel_core_by_site(root: Path, site: str) -> pd.DataFrame:
    path = root / "data" / site / "out" / "panel_day_core.csv"
    if not path.exists():
        raise SystemExit(f"missing panel_day_core for site {site}: {path}")
    df = pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
    for column in df.columns:
        if df[column].dtype == object:
            df[column] = df[column].map(normalize_text)
    ensure_columns(
        df,
        ["date", "panel_id", "confirmed_fault", "critical_fault", "final_fault"],
        f"data/{site}/out/panel_day_core.csv",
    )
    return df


def hard_fault_start_date(panel_core_df: pd.DataFrame, panel_id: str) -> pd.Timestamp | pd.NaT:
    panel_df = panel_core_df.loc[panel_core_df["panel_id"].eq(panel_id)].copy()
    if panel_df.empty:
        return pd.NaT
    hard_mask = (
        panel_df["confirmed_fault"].fillna(False).astype(bool)
        | panel_df["critical_fault"].fillna(False).astype(bool)
        | panel_df["final_fault"].fillna(False).astype(bool)
    )
    hard_df = panel_df.loc[hard_mask].copy()
    if hard_df.empty:
        return pd.NaT
    hard_df["date"] = pd.to_datetime(hard_df["date"], errors="coerce")
    hard_df = hard_df.dropna(subset=["date"]).sort_values("date")
    if hard_df.empty:
        return pd.NaT
    return pd.Timestamp(hard_df.iloc[0]["date"])


def select_first_row(df: pd.DataFrame, site: str, panel_id: str) -> dict[str, object]:
    matches = df.loc[df["site"].eq(site) & df["panel_id"].eq(panel_id)].copy()
    if matches.empty:
        return {}
    return matches.iloc[0].to_dict()


def build_case_row(
    overlap_row: dict[str, object],
    non_precursor_row: dict[str, object],
    verdict_row: dict[str, object],
    event_df: pd.DataFrame,
    reaudit_row: dict[str, object],
    panel_core_df: pd.DataFrame,
) -> dict[str, object]:
    site = normalize_text(overlap_row["site"])
    panel_id = normalize_text(overlap_row["panel_id"])

    precursor_onset_date = parse_date(overlap_row.get("preferred_precursor_onset_date", ""))
    precursor_fault_date = parse_date(overlap_row.get("fault_start_date", ""))
    selected_episode_end_date = parse_date(overlap_row.get("selected_episode_end_date", ""))

    abrupt_anchor_date = first_valid_date(
        [
            non_precursor_row.get("anchor_date", ""),
            reaudit_row.get("strict_trigger_date", ""),
            overlap_row.get("고장시점", ""),
        ]
    )
    abrupt_fault_date = first_valid_date(
        [
            non_precursor_row.get("first_final_fault_date", ""),
            non_precursor_row.get("first_critical_fault_date", ""),
            non_precursor_row.get("first_confirmed_fault_date", ""),
            hard_fault_start_date(panel_core_df, panel_id),
            overlap_row.get("고장시점", ""),
        ]
    )

    lead_days = days_between(precursor_onset_date, abrupt_fault_date)
    fault_gap_days = days_between(precursor_fault_date, abrupt_fault_date)
    episode_end_gap_days = days_between(selected_episode_end_date, abrupt_fault_date)

    overlap_event_types = set(
        event_df.loc[event_df["site"].eq(site) & event_df["panel_id"].eq(panel_id), "사건유형_ko"].tolist()
    )
    if not {"전조형 고장", "급작 고장"}.issubset(overlap_event_types):
        raise SystemExit(f"{EVENT_SUPPLEMENT_NAME} missing overlap event rows for {(site, panel_id)}")
    if normalize_text(verdict_row.get("패널고장여부_ko", "")) != "고장":
        raise SystemExit(f"{MULTIAXIS_VERDICT_NAME} must keep overlap panel as fault: {(site, panel_id)}")

    same_event_flag = 0
    distinct_event_flag = 0
    consistency_judgment = "불충분"

    onset_before_abrupt = lead_days is not None and lead_days >= 0
    fault_dates_close = fault_gap_days is not None and 0 <= fault_gap_days <= 7
    episode_continuity_ok = episode_end_gap_days is None or 0 <= episode_end_gap_days <= 7
    fault_dates_far = fault_gap_days is not None and abs(fault_gap_days) > 30
    episode_far = episode_end_gap_days is not None and abs(episode_end_gap_days) > 30
    onset_after_abrupt = lead_days is not None and lead_days < 0

    if onset_before_abrupt and fault_dates_close and episode_continuity_ok:
        same_event_flag = 1
        consistency_judgment = "같은 사건"
    elif onset_after_abrupt or fault_dates_far or episode_far:
        distinct_event_flag = 1
        consistency_judgment = "별도 사건"

    reasoning_parts = [
        f"precursor_onset={format_date(precursor_onset_date)}",
        f"precursor_fault={format_date(precursor_fault_date)}",
        f"abrupt_anchor={format_date(abrupt_anchor_date)}",
        f"abrupt_fault={format_date(abrupt_fault_date)}",
    ]
    if lead_days is not None:
        reasoning_parts.append(f"onset_to_abrupt_fault={lead_days}일")
    if fault_gap_days is not None:
        reasoning_parts.append(f"fault_date_gap={fault_gap_days}일")
    if episode_end_gap_days is not None:
        reasoning_parts.append(f"selected_episode_end_to_abrupt_fault={episode_end_gap_days}일")

    first_warning_date = format_date(parse_date(reaudit_row.get("first_warning_date", "")))
    retrospective_onset_date = format_date(parse_date(reaudit_row.get("retrospective_onset_date", "")))
    if first_warning_date:
        reasoning_parts.append(f"reaudit_first_warning={first_warning_date}")
    if retrospective_onset_date:
        reasoning_parts.append(f"reaudit_retrospective_onset={retrospective_onset_date}")

    if same_event_flag:
        reasoning_parts.append(
            "precursor onset이 abrupt fault보다 먼저 나오고 precursor fault_start_date와 abrupt fault date가 같은/가까운 날짜라 한 evolving fault episode로 읽는 편이 안전하다."
        )
    elif distinct_event_flag:
        reasoning_parts.append(
            "precursor fault date와 abrupt fault date가 크게 벌어져 있어 같은 fault episode로 보기 어렵다."
        )
    else:
        reasoning_parts.append(
            "timing은 일부 이어지지만 같은 episode라고 단정할 만큼 가깝지도, 별도 사건이라고 단정할 만큼 멀지도 않아 stored artifact만으로는 불충분하다."
        )

    return {
        "site": site,
        "panel_id": panel_id,
        "precursor_onset_date": format_date(precursor_onset_date),
        "precursor_fault_date": format_date(precursor_fault_date),
        "abrupt_anchor_date": format_date(abrupt_anchor_date),
        "abrupt_fault_date": format_date(abrupt_fault_date),
        "lead_days_from_precursor_to_abrupt_fault": lead_days if lead_days is not None else "",
        "same_event_flag": same_event_flag,
        "distinct_event_flag": distinct_event_flag,
        "consistency_judgment_ko": consistency_judgment,
        "reasoning_ko": "; ".join(part for part in reasoning_parts if part),
    }


def build_outputs(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    frames = load_inputs(root)
    overlap_df = build_overlap_df(frames["precursor"], frames["abrupt6"])

    verdict_df = frames["verdict"]
    event_df = frames["event"]
    current_unique_fault_panel_count = int(verdict_df["패널고장여부_ko"].eq("고장").sum())
    current_precursor_event_count = int(pd.to_numeric(verdict_df["전조형이력_flag"], errors="coerce").fillna(0).sum())
    current_abrupt_event_count = int(pd.to_numeric(verdict_df["급작고장이력_flag"], errors="coerce").fillna(0).sum())
    pure_precursor_panel_count = int(
        (
            pd.to_numeric(verdict_df["전조형이력_flag"], errors="coerce").fillna(0).eq(1)
            & pd.to_numeric(verdict_df["급작고장이력_flag"], errors="coerce").fillna(0).eq(0)
        ).sum()
    )

    case_rows: list[dict[str, object]] = []
    panel_core_cache: dict[str, pd.DataFrame] = {}
    for overlap_row in overlap_df.to_dict(orient="records"):
        site = normalize_text(overlap_row["site"])
        panel_id = normalize_text(overlap_row["panel_id"])
        if site not in panel_core_cache:
            panel_core_cache[site] = load_panel_core_by_site(root, site)
        case_rows.append(
            build_case_row(
                overlap_row=overlap_row,
                non_precursor_row=select_first_row(frames["non_precursor"], site, panel_id),
                verdict_row=select_first_row(frames["verdict"], site, panel_id),
                event_df=event_df,
                reaudit_row=select_first_row(frames["reaudit"], site, panel_id),
                panel_core_df=panel_core_cache[site],
            )
        )

    cases_df = pd.DataFrame(case_rows).reindex(columns=CASE_COLS)
    same_event_count = int(pd.to_numeric(cases_df["same_event_flag"], errors="coerce").fillna(0).sum())
    distinct_event_count = int(pd.to_numeric(cases_df["distinct_event_flag"], errors="coerce").fillna(0).sum())
    ambiguous_count = int(len(cases_df) - same_event_count - distinct_event_count)
    corrected_precursor_led_fault_count = pure_precursor_panel_count + same_event_count
    corrected_pure_abrupt_fault_count = current_abrupt_event_count - same_event_count

    summary_df = pd.DataFrame(
        [
            {
                "overlap_panel_count": int(len(cases_df)),
                "same_event_count": same_event_count,
                "distinct_event_count": distinct_event_count,
                "ambiguous_count": ambiguous_count,
                "current_unique_fault_panel_count": current_unique_fault_panel_count,
                "current_precursor_event_count": current_precursor_event_count,
                "current_abrupt_event_count": current_abrupt_event_count,
                "corrected_precursor_led_fault_count": corrected_precursor_led_fault_count,
                "corrected_pure_abrupt_fault_count": corrected_pure_abrupt_fault_count,
                "note_ko": (
                    "전조형/급작 overlap panel만 따로 떼어 event-level consistency를 봤다. "
                    "current panel table의 고유 고장패널수는 그대로 두고, overlap이 같은 사건이면 precursor-led fault with abrupt ending으로 읽는 해석만 제안한다."
                ),
            }
        ]
    ).reindex(columns=SUMMARY_COLS)

    if same_event_count == len(cases_df):
        recommended_next_handling = "relabel_overlap_as_precursor_led_faults"
        rationale = (
            "overlap 2건 모두 precursor onset이 abrupt fault보다 앞서고 fault/episode 날짜가 이어져 같은 사건으로 읽는 편이 더 자연스럽다."
        )
    elif distinct_event_count == len(cases_df):
        recommended_next_handling = "keep_abrupt6_as_is"
        rationale = "overlap 전부가 별도 사건으로 보여 abrupt6 count를 그대로 유지하는 편이 안전하다."
    else:
        recommended_next_handling = "keep_overlap_as_ambiguous_until_manual_review"
        rationale = "overlap 중 일부만 같은 사건으로 보여 event count freeze 전에는 manual review를 더 거치는 편이 안전하다."

    recommendation_df = pd.DataFrame(
        [
            {
                "recommended_next_handling": recommended_next_handling,
                "rationale_ko": rationale,
            }
        ]
    ).reindex(columns=RECOMMENDATION_COLS)

    return cases_df, summary_df, recommendation_df


def write_outputs(
    root: Path,
    cases_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    recommendation_df: pd.DataFrame,
) -> None:
    share = root / "_share"
    share.mkdir(parents=True, exist_ok=True)
    cases_df.to_csv(share / CASES_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    recommendation_df.to_csv(share / RECOMMENDATION_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    cases_df, summary_df, recommendation_df = build_outputs(root)
    write_outputs(root, cases_df, summary_df, recommendation_df)


if __name__ == "__main__":
    main()
