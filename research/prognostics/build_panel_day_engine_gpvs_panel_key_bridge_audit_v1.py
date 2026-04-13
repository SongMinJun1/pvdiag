#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

PANEL_VERDICT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
ATTACH_CANDIDATES_NAME = "panel_day_engine_gpvs_panel_attach_candidates_v1.csv"
ATTACH_INVENTORY_NAME = "panel_day_engine_gpvs_panel_attach_inventory_v1.csv"
GPVS_EVAL_CASES_NAME = "gpvs_fault_family_eval_cases.csv"

CANDIDATES_OUTPUT_NAME = "panel_day_engine_gpvs_panel_key_bridge_candidates_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_gpvs_panel_key_bridge_summary_v1.csv"
RECOMMENDATION_OUTPUT_NAME = "panel_day_engine_gpvs_panel_key_bridge_recommendation_v1.csv"

CANDIDATE_COLS = [
    "site",
    "panel_id",
    "rule_name",
    "matched_gpvs_row_count",
    "matched_gpvs_panel_ids_csv",
    "matched_gpvs_type_values_csv",
    "unique_attachable_flag",
    "conflict_flag",
    "bridge_reason_ko",
]

SUMMARY_COLS = [
    "rule_name",
    "unmatched_panel_count",
    "unique_attachable_count",
    "conflict_count",
    "contradiction_on_matched_count",
    "safe_attachable_count",
    "note_ko",
]

RECOMMENDATION_COLS = [
    "recommended_action",
    "recommended_rule_name",
    "rationale_ko",
]

RULE_ORDER = [
    "exact_full_key",
    "site_plus_parent_uuid",
    "site_plus_two_level_prefix",
    "site_only_not_allowed",
]

RECOMMENDABLE_RULES = [
    "site_plus_two_level_prefix",
    "site_plus_parent_uuid",
]

TYPE_LABEL_MAP = {
    "electrical_fault_like": "전기적 고장 계열",
    "open_or_device_issue_like": "개방/장치이상 계열",
    "group_or_inverter_side_like": "공통원인/인버터측 계열",
    "none_visible": "무가시형 계열",
    "uncertain": "불확실",
}

TYPE_COL_PRIORITY = [
    "pred_fault_family",
    "fault_family",
    "fault_type",
    "class_label",
    "type",
    "truth_fault_family",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit whether currently unmatched GPVS panel references can be bridged safely by alternate panel keys."
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


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    for column in normalized.columns:
        if normalized[column].dtype == object:
            normalized[column] = normalized[column].map(normalize_text)
    return normalized


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def find_column(df: pd.DataFrame, candidates: list[str], name: str) -> str:
    lowered = {column.lower(): column for column in df.columns}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    raise SystemExit(f"{name} missing any of columns: {candidates}")


def select_type_column(df: pd.DataFrame) -> str:
    lowered = {column.lower(): column for column in df.columns}
    for candidate in TYPE_COL_PRIORITY:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    raise SystemExit(f"{GPVS_EVAL_CASES_NAME} missing any GPVS type column from {TYPE_COL_PRIORITY}")


def parent_uuid(panel_id: str) -> str:
    return panel_id.split(".", 1)[0] if "." in panel_id else panel_id


def two_level_prefix(panel_id: str) -> str:
    return panel_id.rsplit(".", 1)[0] if "." in panel_id else panel_id


def derive_rule_key(site: str, panel_id: str, rule_name: str) -> str:
    if rule_name == "exact_full_key":
        return f"{site}||{panel_id}"
    if rule_name == "site_plus_parent_uuid":
        return f"{site}||{parent_uuid(panel_id)}"
    if rule_name == "site_plus_two_level_prefix":
        return f"{site}||{two_level_prefix(panel_id)}"
    if rule_name == "site_only_not_allowed":
        return site
    raise SystemExit(f"unsupported rule_name: {rule_name}")


def gpvs_type_label(raw_value: object) -> str:
    raw = normalize_text(raw_value)
    if not raw:
        return "불충분"
    return TYPE_LABEL_MAP.get(raw, raw)


def build_gpvs_eval_df(eval_df: pd.DataFrame) -> pd.DataFrame:
    type_col = select_type_column(eval_df)
    enriched = eval_df.copy()
    enriched["site"] = enriched["site"].map(normalize_text)
    enriched["panel_id"] = enriched["panel_id"].map(normalize_text)
    enriched["GPVS_참고유형_ko"] = enriched[type_col].map(gpvs_type_label)
    for rule_name in RULE_ORDER:
        enriched[f"rule_key__{rule_name}"] = [
            derive_rule_key(site, panel_id, rule_name)
            for site, panel_id in zip(enriched["site"], enriched["panel_id"])
        ]
    return enriched


def load_inputs(root: Path) -> dict[str, pd.DataFrame]:
    share = root / "_share"
    frames = {
        "panel_verdict": normalize_df(read_csv(share / PANEL_VERDICT_NAME)),
        "attach_candidates": normalize_df(read_csv(share / ATTACH_CANDIDATES_NAME)),
        "attach_inventory": normalize_df(read_csv(share / ATTACH_INVENTORY_NAME)),
        "gpvs_eval_cases": normalize_df(read_csv(share / GPVS_EVAL_CASES_NAME)),
    }

    ensure_columns(
        frames["panel_verdict"],
        ["site", "panel_id", "GPVS_적용대상_ko", "GPVS_부착상태_ko", "GPVS_참고유형_ko"],
        PANEL_VERDICT_NAME,
    )
    ensure_columns(
        frames["attach_candidates"],
        ["site", "panel_id", "GPVS_참고유형_ko", "source_path", "source_key_ko", "비고_ko"],
        ATTACH_CANDIDATES_NAME,
    )
    ensure_columns(
        frames["attach_inventory"],
        ["경로", "panel_attach_candidate_flag", "granularity_ko", "attachability_note_ko", "note_ko"],
        ATTACH_INVENTORY_NAME,
    )
    ensure_columns(
        frames["gpvs_eval_cases"],
        ["site", "panel_id"],
        GPVS_EVAL_CASES_NAME,
    )
    return frames


def validate_inputs(frames: dict[str, pd.DataFrame]) -> None:
    panel_df = frames["panel_verdict"]
    if panel_df.duplicated(subset=["site", "panel_id"]).any():
        raise SystemExit(f"{PANEL_VERDICT_NAME} must be unique by (site, panel_id)")

    unmatched_df = panel_df.loc[
        panel_df["GPVS_적용대상_ko"].eq("적용대상") & panel_df["GPVS_부착상태_ko"].eq("미부착")
    ].copy()

    matched_df = panel_df.loc[
        panel_df["GPVS_적용대상_ko"].eq("적용대상") & panel_df["GPVS_부착상태_ko"].eq("부착")
    ].copy()
    attach_candidates_df = frames["attach_candidates"]
    merged = matched_df.merge(
        attach_candidates_df[["site", "panel_id", "GPVS_참고유형_ko"]],
        on=["site", "panel_id"],
        how="left",
        suffixes=("_panel", "_candidate"),
    )
    if not merged.empty and merged["GPVS_참고유형_ko_candidate"].map(normalize_text).eq("").any():
        raise SystemExit("currently attached panel rows are missing from attach candidates output")

    inventory_df = frames["attach_inventory"].copy()
    inventory_df["panel_attach_candidate_flag"] = pd.to_numeric(
        inventory_df["panel_attach_candidate_flag"], errors="coerce"
    ).fillna(0)
    gpvs_inventory_row = inventory_df.loc[inventory_df["경로"].eq(f"_share/{GPVS_EVAL_CASES_NAME}")]
    if gpvs_inventory_row.empty:
        raise SystemExit(f"{ATTACH_INVENTORY_NAME} must include _share/{GPVS_EVAL_CASES_NAME}")


def matched_rows_for_rule(
    gpvs_eval_df: pd.DataFrame,
    site: str,
    panel_id: str,
    rule_name: str,
) -> pd.DataFrame:
    rule_key = derive_rule_key(site, panel_id, rule_name)
    return gpvs_eval_df.loc[gpvs_eval_df[f"rule_key__{rule_name}"].eq(rule_key)].copy()


def candidate_reason(rule_name: str, matched_rows: pd.DataFrame, unique_attachable: int, conflict: int) -> str:
    row_count = len(matched_rows)
    if rule_name == "site_only_not_allowed":
        if row_count == 0:
            return "site-only negative control 기준으로도 연결되는 GPVS row가 없다."
        return "site-only는 같은 site 여러 panel/type을 섞을 수 있어 negative control로만 기록한다."

    if row_count == 0:
        return f"{rule_name} 기준 연결되는 GPVS row가 없다."
    if unique_attachable == 1 and conflict == 0:
        return f"{rule_name} 기준 GPVS 1행/1유형으로만 이어져 후보로 볼 수 있다."
    type_values = sorted({value for value in matched_rows["GPVS_참고유형_ko"].tolist() if value})
    if len(type_values) > 1:
        return f"{rule_name} 기준 여러 GPVS 유형({', '.join(type_values)})과 겹쳐 안전하게 붙일 수 없다."
    return f"{rule_name} 기준 여러 GPVS row와 겹쳐 안전하게 붙일 수 없다."


def contradiction_count_on_matched(
    matched_panel_df: pd.DataFrame,
    gpvs_eval_df: pd.DataFrame,
    rule_name: str,
) -> int:
    contradiction_count = 0
    for row in matched_panel_df.to_dict(orient="records"):
        current_type = normalize_text(row["GPVS_참고유형_ko"])
        matched_rows = matched_rows_for_rule(gpvs_eval_df, row["site"], row["panel_id"], rule_name)
        type_values = sorted({value for value in matched_rows["GPVS_참고유형_ko"].tolist() if value})
        if not type_values:
            continue
        if len(type_values) > 1 or current_type not in type_values:
            contradiction_count += 1
    return contradiction_count


def build_outputs(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    panel_df = frames["panel_verdict"].copy()
    unmatched_df = panel_df.loc[
        panel_df["GPVS_적용대상_ko"].eq("적용대상") & panel_df["GPVS_부착상태_ko"].eq("미부착"),
        ["site", "panel_id"],
    ].copy()
    matched_df = panel_df.loc[
        panel_df["GPVS_적용대상_ko"].eq("적용대상") & panel_df["GPVS_부착상태_ko"].eq("부착"),
        ["site", "panel_id", "GPVS_참고유형_ko"],
    ].copy()
    gpvs_eval_df = build_gpvs_eval_df(frames["gpvs_eval_cases"])

    candidate_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    rule_to_safe_count: dict[str, int] = {}

    for rule_name in RULE_ORDER:
        contradiction_count = contradiction_count_on_matched(matched_df, gpvs_eval_df, rule_name)
        unique_attachable_count = 0
        conflict_count = 0
        safe_attachable_count = 0

        for row in unmatched_df.to_dict(orient="records"):
            matched_rows = matched_rows_for_rule(gpvs_eval_df, row["site"], row["panel_id"], rule_name)
            panel_ids = sorted({panel_id for panel_id in matched_rows["panel_id"].tolist() if panel_id})
            type_values = sorted({value for value in matched_rows["GPVS_참고유형_ko"].tolist() if value})
            row_count = len(matched_rows)
            unique_attachable = int(row_count == 1 and len(type_values) == 1)
            conflict_flag = int(row_count > 1 or len(type_values) > 1)
            if unique_attachable:
                unique_attachable_count += 1
            if conflict_flag:
                conflict_count += 1

            if (
                rule_name in RECOMMENDABLE_RULES
                and unique_attachable == 1
                and conflict_flag == 0
                and contradiction_count == 0
            ):
                safe_attachable_count += 1

            candidate_rows.append(
                {
                    "site": row["site"],
                    "panel_id": row["panel_id"],
                    "rule_name": rule_name,
                    "matched_gpvs_row_count": row_count,
                    "matched_gpvs_panel_ids_csv": ",".join(panel_ids),
                    "matched_gpvs_type_values_csv": ",".join(type_values),
                    "unique_attachable_flag": unique_attachable,
                    "conflict_flag": conflict_flag,
                    "bridge_reason_ko": candidate_reason(rule_name, matched_rows, unique_attachable, conflict_flag),
                }
            )

        rule_to_safe_count[rule_name] = safe_attachable_count
        if rule_name == "site_only_not_allowed":
            note = "site-only는 negative control이므로 match가 있어도 추천하지 않는다."
        elif unmatched_df.empty:
            note = "현재 GPVS 적용대상 미부착 fault panel 이 없어 bridge audit 대상이 없다."
        elif contradiction_count > 0:
            note = f"이미 붙은 panel에서 GPVS type 모순이 {contradiction_count}건 생겨 unsafe rule로 본다."
        elif safe_attachable_count > 0:
            note = f"현재 unmatched panel 중 {safe_attachable_count}건은 rule 기준으로 1:1 bridge 후보가 된다."
        else:
            note = "현재 unmatched panel에 대해 안전한 1:1 bridge 후보를 만들지 못했다."

        summary_rows.append(
            {
                "rule_name": rule_name,
                "unmatched_panel_count": len(unmatched_df),
                "unique_attachable_count": unique_attachable_count,
                "conflict_count": conflict_count,
                "contradiction_on_matched_count": contradiction_count,
                "safe_attachable_count": safe_attachable_count,
                "note_ko": note,
            }
        )

    summary_df = pd.DataFrame(summary_rows).reindex(columns=SUMMARY_COLS)
    candidate_df = pd.DataFrame(candidate_rows).reindex(columns=CANDIDATE_COLS)

    chosen_rule = ""
    chosen_safe_count = 0
    for rule_name in RECOMMENDABLE_RULES:
        safe_count = rule_to_safe_count.get(rule_name, 0)
        if safe_count > chosen_safe_count:
            chosen_rule = rule_name
            chosen_safe_count = safe_count

    if unmatched_df.empty:
        recommendation_row = {
            "recommended_action": "keep_exact_match_only",
            "recommended_rule_name": "",
            "rationale_ko": "현재 GPVS 적용대상 미부착 fault panel 이 없어 추가 bridge 검토 없이 exact-match-only 상태를 유지한다.",
        }
    elif chosen_rule:
        recommendation_row = {
            "recommended_action": "use_safe_bridge_rule",
            "recommended_rule_name": chosen_rule,
            "rationale_ko": (
                f"{chosen_rule} 는 현재 unmatched panel 중 {chosen_safe_count}건을 안전한 1:1 bridge 후보로 만들고, "
                "이미 exact-match로 붙은 panel과의 GPVS type 모순도 만들지 않는다."
            ),
        }
    else:
        recommendation_row = {
            "recommended_action": "keep_exact_match_only",
            "recommended_rule_name": "",
            "rationale_ko": (
                "tested alternate key rule들이 unmatched panel에서 conflict를 만들거나, "
                "already-matched panel의 current GPVS type과 모순을 만들어 exact-match-only를 유지해야 한다."
            ),
        }

    recommendation_df = pd.DataFrame([recommendation_row]).reindex(columns=RECOMMENDATION_COLS)
    return candidate_df, summary_df, recommendation_df


def write_outputs(root: Path, candidate_df: pd.DataFrame, summary_df: pd.DataFrame, recommendation_df: pd.DataFrame) -> None:
    share = root / "_share"
    share.mkdir(parents=True, exist_ok=True)
    candidate_df.to_csv(share / CANDIDATES_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    recommendation_df.to_csv(share / RECOMMENDATION_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    frames = load_inputs(root)
    validate_inputs(frames)
    candidate_df, summary_df, recommendation_df = build_outputs(frames)
    write_outputs(root, candidate_df, summary_df, recommendation_df)


if __name__ == "__main__":
    main()
