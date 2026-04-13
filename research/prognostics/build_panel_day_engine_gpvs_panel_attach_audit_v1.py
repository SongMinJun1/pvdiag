#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

PANEL_VERDICT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
INVENTORY_OUTPUT_NAME = "panel_day_engine_gpvs_panel_attach_inventory_v1.csv"
FEASIBILITY_OUTPUT_NAME = "panel_day_engine_gpvs_panel_attach_feasibility_v1.csv"
CANDIDATES_OUTPUT_NAME = "panel_day_engine_gpvs_panel_attach_candidates_v1.csv"

SEARCH_ROOTS = ("_share", "data", "docs")
SEARCH_TOKENS = ("gpv", "gpvs")
SEARCH_SUFFIXES = {".csv", ".tsv", ".parquet", ".json", ".md", ".txt", ".zip"}

INVENTORY_COLS = [
    "경로",
    "존재여부",
    "파일종류_ko",
    "granularity_ko",
    "panel_id_컬럼존재_flag",
    "site_컬럼존재_flag",
    "유형_컬럼존재_flag",
    "점수_컬럼존재_flag",
    "panel_attach_candidate_flag",
    "current_panel_count",
    "candidate_panel_count",
    "overlap_panel_count",
    "overlap_rate",
    "attachability_note_ko",
    "note_ko",
]

FEASIBILITY_COLS = [
    "GPVS_패널별_직접판정_가능여부",
    "근거_ko",
    "최선_후보_파일",
    "overlap_panel_count",
    "overlap_rate",
    "다음권장조치_ko",
]

CANDIDATE_COLS = [
    "site",
    "panel_id",
    "GPVS_참고유형_ko",
    "source_path",
    "source_key_ko",
    "비고_ko",
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
        description="Audit whether GPVS-based panel-level direct verdicts can be attached from current stored artifacts."
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


def read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
    if suffix == ".tsv":
        return pd.read_csv(path, sep="\t", low_memory=False, encoding="utf-8-sig")
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix == ".json":
        return pd.read_json(path)
    raise ValueError(f"unsupported table suffix: {suffix}")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def relative_str(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def file_type_ko(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".csv", ".tsv", ".parquet", ".json"}:
        return "테이블"
    if suffix in {".md", ".txt"}:
        return "문서"
    if suffix == ".zip":
        return "압축파일"
    return "기타"


def find_column(df: pd.DataFrame, candidates: list[str]) -> str:
    lowered = {column.lower(): column for column in df.columns}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return ""


def has_matching_column(df: pd.DataFrame, tokens: list[str]) -> bool:
    lowered = [column.lower() for column in df.columns]
    for column in lowered:
        if any(token in column for token in tokens):
            return True
    return False


def select_type_column(df: pd.DataFrame) -> str:
    lowered = {column.lower(): column for column in df.columns}
    for candidate in TYPE_COL_PRIORITY:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return ""


def classify_granularity(path: Path, df: pd.DataFrame | None) -> str:
    lower_path = str(path).lower()
    if df is None:
        if "bytype" in lower_path or "fault_family" in lower_path:
            return "유형수준"
        if "summary" in lower_path or "metrics" in lower_path or "onepage" in lower_path:
            return "집계수준"
        return "불명확"

    panel_col = find_column(df, ["panel_id", "display_entity_id"])
    if panel_col:
        return "패널수준"
    lowered_cols = [column.lower() for column in df.columns]
    if any(token in lowered_cols for token in ["sample_id", "source_id", "window_idx", "strict_trigger_date"]):
        return "에피소드수준"
    if select_type_column(df):
        return "유형수준"
    if has_matching_column(df, ["score", "auc", "ap", "precision", "recall", "f1"]):
        return "집계수준"
    return "불명확"


def search_gpvs_files(root: Path) -> list[Path]:
    paths: set[Path] = set()
    for base_name in SEARCH_ROOTS:
        base = root / base_name
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            rel = relative_str(path, root).lower()
            if not any(token in rel for token in SEARCH_TOKENS):
                continue
            if path.suffix.lower() not in SEARCH_SUFFIXES:
                continue
            paths.add(path)
    return sorted(paths)


def build_key_set(df: pd.DataFrame, site_col: str, panel_col: str) -> set[tuple[str, str]]:
    valid = df.loc[df[panel_col].map(normalize_text).ne("")].copy()
    if not site_col:
        return set()
    return set(zip(valid[site_col], valid[panel_col]))


def build_panel_only_set(df: pd.DataFrame, panel_col: str) -> set[str]:
    valid = df.loc[df[panel_col].map(normalize_text).ne("")].copy()
    return set(valid[panel_col].tolist())


def attachability_stats(
    candidate_df: pd.DataFrame,
    site_col: str,
    panel_col: str,
    panel_df: pd.DataFrame,
) -> tuple[int, int, float, str, str]:
    current_panel_count = len(panel_df)
    panel_keys = set(zip(panel_df["site"], panel_df["panel_id"]))
    panel_only_unique = panel_df["panel_id"].nunique() == len(panel_df)

    if site_col:
        candidate_keys = build_key_set(candidate_df, site_col, panel_col)
        overlap = panel_keys & candidate_keys
        note = "site+panel_id direct match 가능" if overlap else "site+panel_id key는 있으나 현재 panel table과 겹치지 않음"
        return len(candidate_keys), len(overlap), round(len(overlap) / current_panel_count, 4), note, "site+panel_id"

    candidate_panel_only = build_panel_only_set(candidate_df, panel_col)
    overlap_only = {panel_id for _, panel_id in panel_keys if panel_id in candidate_panel_only}
    if panel_only_unique:
        note = "panel_id 단독 매칭 가능" if overlap_only else "panel_id key는 있으나 현재 panel table과 겹치지 않음"
        return len(candidate_panel_only), len(overlap_only), round(len(overlap_only) / current_panel_count, 4), note, "panel_id"

    return len(candidate_panel_only), 0, 0.0, "panel_id 단독 매칭이 모호해 attach 불가", "panel_id"


def analyze_path(path: Path, root: Path, panel_df: pd.DataFrame) -> dict[str, object]:
    rel = relative_str(path, root)
    row: dict[str, object] = {
        "경로": rel,
        "존재여부": 1,
        "파일종류_ko": file_type_ko(path),
        "granularity_ko": "불명확",
        "panel_id_컬럼존재_flag": 0,
        "site_컬럼존재_flag": 0,
        "유형_컬럼존재_flag": 0,
        "점수_컬럼존재_flag": 0,
        "panel_attach_candidate_flag": 0,
        "current_panel_count": "",
        "candidate_panel_count": "",
        "overlap_panel_count": "",
        "overlap_rate": "",
        "attachability_note_ko": "",
        "note_ko": "",
    }

    table_df: pd.DataFrame | None = None
    if path.suffix.lower() in {".csv", ".tsv", ".parquet", ".json"}:
        try:
            table_df = normalize_df(read_table(path))
        except Exception as exc:  # pragma: no cover - defensive
            row["note_ko"] = f"테이블 읽기 실패: {exc}"
            row["granularity_ko"] = classify_granularity(path, None)
            return row

    row["granularity_ko"] = classify_granularity(path, table_df)

    if table_df is None:
        lower_path = rel.lower()
        if path.suffix.lower() == ".md":
            row["note_ko"] = "문서형 요약 파일이라 panel direct attach source 아님"
        elif path.suffix.lower() == ".zip":
            row["note_ko"] = "압축 보관본이라 직접 컬럼 검사 없이 inventory에만 포함"
        else:
            row["note_ko"] = "비테이블 파일이라 direct attach source 아님"
        if "onepage" in lower_path or "summary" in lower_path:
            row["attachability_note_ko"] = "유형/집계 설명용 문서"
        return row

    panel_col = find_column(table_df, ["panel_id", "display_entity_id"])
    site_col = find_column(table_df, ["site"])
    type_col = select_type_column(table_df)
    score_flag = has_matching_column(table_df, ["score", "auc", "ap", "precision", "recall", "f1"])

    row["panel_id_컬럼존재_flag"] = int(bool(panel_col))
    row["site_컬럼존재_flag"] = int(bool(site_col))
    row["유형_컬럼존재_flag"] = int(bool(type_col))
    row["점수_컬럼존재_flag"] = int(score_flag)

    candidate_flag = bool(panel_col and type_col)
    row["panel_attach_candidate_flag"] = int(candidate_flag)

    if candidate_flag:
        candidate_panel_count, overlap_count, overlap_rate, attach_note, key_kind = attachability_stats(
            table_df, site_col, panel_col, panel_df
        )
        row["current_panel_count"] = len(panel_df)
        row["candidate_panel_count"] = candidate_panel_count
        row["overlap_panel_count"] = overlap_count
        row["overlap_rate"] = overlap_rate
        row["attachability_note_ko"] = attach_note
        if overlap_count > 0:
            row["note_ko"] = f"{key_kind}로 current panel table과 연결 가능한 panel-level GPVS reference file"
        else:
            row["note_ko"] = f"{key_kind}는 있으나 current panel table과 겹치지 않는 panel-level GPVS reference file"
    else:
        if panel_col and not type_col:
            row["attachability_note_ko"] = "panel key는 있지만 유형 label이 없어 direct verdict attach source로는 부족"
        elif type_col and not panel_col:
            row["attachability_note_ko"] = "유형 label은 있지만 panel key가 없어 type-level/aggregate 해석만 가능"
        else:
            row["attachability_note_ko"] = "panel key와 유형 label이 모두 부족"
        row["note_ko"] = "current panel table에 직접 붙일 최소 key/label 요건을 충족하지 못함"

    return row


def choose_best_candidate(inventory_df: pd.DataFrame) -> pd.Series | None:
    candidates = inventory_df.loc[
        (inventory_df["panel_attach_candidate_flag"] == 1)
        & pd.to_numeric(inventory_df["overlap_panel_count"], errors="coerce").fillna(0).gt(0)
    ].copy()
    if candidates.empty:
        return None
    candidates["_overlap"] = pd.to_numeric(candidates["overlap_panel_count"], errors="coerce").fillna(0)
    candidates["_rate"] = pd.to_numeric(candidates["overlap_rate"], errors="coerce").fillna(0.0)
    candidates = candidates.sort_values(
        by=["_overlap", "_rate", "site_컬럼존재_flag", "경로"],
        ascending=[False, False, False, True],
    )
    return candidates.iloc[0]


def source_key_kind(candidate_df: pd.DataFrame, panel_df: pd.DataFrame) -> tuple[str, str, str]:
    panel_col = find_column(candidate_df, ["panel_id", "display_entity_id"])
    site_col = find_column(candidate_df, ["site"])
    if panel_col and site_col:
        return panel_col, site_col, "site+panel_id"
    if panel_col and panel_df["panel_id"].nunique() == len(panel_df):
        return panel_col, "", "panel_id"
    raise SystemExit("best candidate no longer has a recoverable panel key")


def map_reference_type(value: object) -> str:
    text = normalize_text(value)
    if not text:
        return "불명확"
    return TYPE_LABEL_MAP.get(text, text)


def build_candidate_rows(root: Path, panel_df: pd.DataFrame, best_candidate_path: Path | None) -> pd.DataFrame:
    if best_candidate_path is None:
        return pd.DataFrame(columns=CANDIDATE_COLS)

    candidate_df = normalize_df(read_table(best_candidate_path))
    panel_col, site_col, key_kind = source_key_kind(candidate_df, panel_df)
    type_col = select_type_column(candidate_df)
    if not type_col:
        return pd.DataFrame(columns=CANDIDATE_COLS)

    working = candidate_df.loc[candidate_df[panel_col].ne("")].copy()
    if site_col:
        working = working.loc[working[site_col].ne("")].copy()
        working = working.drop_duplicates(subset=[site_col, panel_col], keep="first")
        merged = panel_df.merge(
            working,
            left_on=["site", "panel_id"],
            right_on=[site_col, panel_col],
            how="inner",
            suffixes=("", "_src"),
        )
    else:
        working = working.drop_duplicates(subset=[panel_col], keep="first")
        merged = panel_df.merge(working, left_on="panel_id", right_on=panel_col, how="inner", suffixes=("", "_src"))

    rows: list[dict[str, object]] = []
    for row in merged.itertuples(index=False):
        note_parts: list[str] = []
        prediction_source = normalize_text(getattr(row, "prediction_source", ""))
        fallback_rule = normalize_text(getattr(row, "fallback_rule_used", ""))
        error_type = normalize_text(getattr(row, "error_type", ""))
        vendor_fault_family = normalize_text(getattr(row, "vendor_fault_family", ""))
        if prediction_source:
            note_parts.append(f"prediction_source={prediction_source}")
        if fallback_rule:
            note_parts.append(f"fallback_rule={fallback_rule}")
        if error_type:
            note_parts.append(f"error_type={error_type}")
        if vendor_fault_family:
            note_parts.append(f"vendor_fault_family={vendor_fault_family}")

        rows.append(
            {
                "site": row.site,
                "panel_id": row.panel_id,
                "GPVS_참고유형_ko": map_reference_type(getattr(row, type_col)),
                "source_path": relative_str(best_candidate_path, root),
                "source_key_ko": key_kind,
                "비고_ko": ", ".join(note_parts) if note_parts else "stored panel-level GPVS reference row",
            }
        )

    return pd.DataFrame(rows, columns=CANDIDATE_COLS).sort_values(["site", "panel_id"]).reset_index(drop=True)


def build_feasibility_row(best_candidate: pd.Series | None, current_panel_count: int) -> dict[str, object]:
    if best_candidate is None:
        return {
            "GPVS_패널별_직접판정_가능여부": "불가",
            "근거_ko": "현재 저장 산출물에서는 panel key 없이 유형수준/집계수준으로만 남아 있는 GPVS 파일만 확인되거나, panel key가 있어도 현재 panel table과 겹치지 않는다.",
            "최선_후보_파일": "",
            "overlap_panel_count": 0,
            "overlap_rate": 0.0,
            "다음권장조치_ko": "panel-level verdict table 에서는 GPVS를 계속 미부착으로 두고, 현재 저장 산출물에서는 type-level 또는 aggregate reference 해석만 사용한다.",
        }

    overlap_count = int(pd.to_numeric(best_candidate["overlap_panel_count"], errors="coerce"))
    overlap_rate = float(pd.to_numeric(best_candidate["overlap_rate"], errors="coerce"))
    candidate_count = int(pd.to_numeric(best_candidate["candidate_panel_count"], errors="coerce"))
    return {
        "GPVS_패널별_직접판정_가능여부": "가능",
        "근거_ko": (
            f"{best_candidate['경로']} 에 site/panel_id와 GPVS family type이 함께 저장돼 있어 "
            f"current panel table {current_panel_count}개 중 {overlap_count}개 panel에 direct attach가 가능하다. "
            f"다만 candidate panel {candidate_count}개 전체가 current panel universe를 덮는 것은 아니므로 부분 attach로 읽어야 한다."
        ),
        "최선_후보_파일": best_candidate["경로"],
        "overlap_panel_count": overlap_count,
        "overlap_rate": overlap_rate,
        "다음권장조치_ko": "겹치는 panel에는 GPVS reference type을 보조축으로 붙이고, 겹치지 않는 panel은 미부착으로 유지한다. type-level/aggregate GPVS summary는 계속 별도 해석용으로만 둔다.",
    }


def write_csv(df: pd.DataFrame, path: Path, columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"

    panel_path = share_dir / PANEL_VERDICT_NAME
    panel_df = normalize_df(read_table(panel_path))
    ensure_columns(panel_df, ["site", "panel_id"], PANEL_VERDICT_NAME)
    panel_df = panel_df.loc[panel_df["site"].ne("") & panel_df["panel_id"].ne("")].drop_duplicates(
        subset=["site", "panel_id"]
    )

    inventory_rows = [analyze_path(path, root, panel_df) for path in search_gpvs_files(root)]
    inventory_df = pd.DataFrame(inventory_rows, columns=INVENTORY_COLS).sort_values(["panel_attach_candidate_flag", "경로"], ascending=[False, True]).reset_index(drop=True)

    best_candidate = choose_best_candidate(inventory_df)
    best_candidate_path = root / best_candidate["경로"] if best_candidate is not None else None

    candidate_df = build_candidate_rows(root, panel_df, best_candidate_path)
    feasibility_df = pd.DataFrame([build_feasibility_row(best_candidate, len(panel_df))], columns=FEASIBILITY_COLS)

    write_csv(inventory_df, share_dir / INVENTORY_OUTPUT_NAME, INVENTORY_COLS)
    write_csv(feasibility_df, share_dir / FEASIBILITY_OUTPUT_NAME, FEASIBILITY_COLS)
    write_csv(candidate_df, share_dir / CANDIDATES_OUTPUT_NAME, CANDIDATE_COLS)


if __name__ == "__main__":
    main()
