#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TEMPLATE = REPO_ROOT / "templates/daily_report_template.md"
LATEST_DIRNAME = "latest"

LATEST_FILES = {
    "panel_result": "conalog_panel_result_v1.csv",
    "site_summary": "conalog_site_summary_v1.csv",
    "metadata": "conalog_run_metadata_v1.json",
    "runtime_log": "runtime_log_v1.jsonl",
    "failure_log": "failure_log_v1.jsonl",
    "reference_sidecar": "conalog_reference_sidecar_v1.csv",
    "gpvs_evidence_pack": "gpvs_evidence_pack_v1.csv",
    "cause_candidate_heuristics": "cause_candidate_heuristics_v1.csv",
    "daily_report": "daily_report_v1.md",
}

FALLBACK_FILES = {
    "gpvs_evidence_pack": REPO_ROOT / "_share/panel_day_engine_gpvs_evidence_pack_v1.csv",
    "gpvs_evidence_summary": REPO_ROOT / "_share/panel_day_engine_gpvs_evidence_summary_v1.csv",
    "cause_candidate_heuristics": REPO_ROOT / "_share/panel_day_engine_cause_candidate_heuristics_v1.csv",
    "cause_candidate_summary": REPO_ROOT / "_share/panel_day_engine_cause_candidate_summary_v1.csv",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the conalog daily report foundation markdown under output-root/latest.")
    parser.add_argument("--output-root", type=Path, required=True, help="Operation output root directory.")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, help="Markdown template path.")
    return parser.parse_args(argv)


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def latest_dir(output_root: Path) -> Path:
    return output_root / LATEST_DIRNAME


def read_optional_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def read_optional_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl_messages(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({"message_ko": f"invalid jsonl line: {line}"})
    return rows


def format_bullets(items: list[str], empty_text: str) -> str:
    clean_items = [item for item in items if normalize_text(item)]
    if not clean_items:
        return f"- {empty_text}"
    return "\n".join(f"- {item}" for item in clean_items)


def choose_frame(latest_path: Path, fallback_path: Path | None = None) -> tuple[pd.DataFrame | None, str]:
    latest_df = read_optional_csv(latest_path)
    if latest_df is not None:
        return latest_df, "latest"
    if fallback_path is not None:
        fallback_df = read_optional_csv(fallback_path)
        if fallback_df is not None:
            return fallback_df, "frozen_fallback"
    return None, "missing"


def site_summary_text(site_summary_df: pd.DataFrame | None, source_label: str) -> str:
    if site_summary_df is None or site_summary_df.empty:
        return "- site summary 입력이 없어 section을 placeholder로 둠"
    rows = []
    for row in site_summary_df.to_dict(orient="records"):
        rows.append(
            f"{normalize_text(row.get('site'))}: total={normalize_text(row.get('total_panel_count'))}, "
            f"fault={normalize_text(row.get('fault_panel_count'))}, "
            f"non_fault_or_unresolved={normalize_text(row.get('non_fault_or_unresolved_count'))}"
        )
    if source_label != "latest":
        rows.append(f"site summary source={source_label}")
    return format_bullets(rows, "site summary 없음")


def count_summary(
    site_summary_df: pd.DataFrame | None,
    panel_result_df: pd.DataFrame | None,
) -> tuple[str, str, str]:
    if site_summary_df is not None and not site_summary_df.empty:
        def summed_count(column: str) -> str | None:
            if column not in site_summary_df.columns:
                return None
            values = pd.to_numeric(site_summary_df[column], errors="coerce")
            if not values.notna().any():
                return None
            return str(int(values.fillna(0).sum()))

        total = summed_count("total_panel_count")
        fault = summed_count("fault_panel_count")
        non_fault = summed_count("non_fault_or_unresolved_count")
        if total is not None and fault is not None and non_fault is not None:
            return total, fault, non_fault
    if panel_result_df is not None and not panel_result_df.empty:
        total = len(panel_result_df)
        fault = int(panel_result_df["패널고장여부_ko"].map(normalize_text).eq("고장").sum())
        return str(total), str(fault), str(total - fault)
    if site_summary_df is not None and not site_summary_df.empty:
        row = site_summary_df.iloc[0]
        return (
            normalize_text(row.get("total_panel_count", "")),
            normalize_text(row.get("fault_panel_count", "")),
            normalize_text(row.get("non_fault_or_unresolved_count", "")),
        )
    return "미확인", "미확인", "미확인"


def conalog_distribution_text(panel_result_df: pd.DataFrame | None, source_label: str) -> str:
    source_df = panel_result_df
    family_col = "conalog_원인군_ko"
    if source_df is None or source_df.empty or family_col not in source_df.columns:
        return "- conalog fault-family distribution 입력이 없어 section을 placeholder로 둠"
    counts = source_df[family_col].map(normalize_text).replace("", "미기재").value_counts().to_dict()
    rows = [f"{name}: {count}" for name, count in counts.items()]
    rows.append(f"source={source_label if source_label else 'latest_or_fallback'}")
    return format_bullets(rows, "conalog family 분포 없음")


def gpvs_usage_text(gpvs_summary_df: pd.DataFrame | None) -> str:
    if gpvs_summary_df is not None and not gpvs_summary_df.empty:
        row = gpvs_summary_df.iloc[0]
        return format_bullets(
            [
                f"core reference={normalize_text(row.get('core_reference_count', ''))}",
                f"auxiliary reference={normalize_text(row.get('auxiliary_reference_count', ''))}",
                f"not recommended={normalize_text(row.get('not_recommended_count', ''))}",
                "source=frozen GPVS evidence summary",
            ],
            "GPVS usage summary 없음",
        )
    return "- GPVS usage summary 입력이 없어 section을 placeholder로 둠"


def suspected_cause_text(heuristic_df: pd.DataFrame | None, cause_summary_df: pd.DataFrame | None) -> str:
    if heuristic_df is not None and not heuristic_df.empty and "원인후보_top1_ko" in heuristic_df.columns:
        counts = (
            heuristic_df["원인후보_top1_ko"]
            .map(normalize_text)
            .loc[lambda s: s.ne("")]
            .value_counts()
            .to_dict()
        )
        if counts:
            return format_bullets([f"{name}: {count}" for name, count in counts.items()], "suspected-cause 분포 없음")
    if cause_summary_df is not None and not cause_summary_df.empty:
        row = cause_summary_df.iloc[0]
        rows = []
        for column in cause_summary_df.columns:
            if column.startswith("top1_") and column.endswith("_count"):
                value = normalize_text(row.get(column, ""))
                if value not in {"", "0"}:
                    label = column.removeprefix("top1_").removesuffix("_count")
                    rows.append(f"{label}: {value}")
        if rows:
            rows.append("source=frozen cause candidate summary")
            return format_bullets(rows, "suspected-cause 분포 없음")
    return "- suspected-cause distribution 입력이 없어 section을 placeholder로 둠"


def new_fault_panels_text(panel_result_df: pd.DataFrame | None) -> str:
    source_df = panel_result_df
    if source_df is None or source_df.empty:
        return "- 신규 fault panel 입력이 없어 placeholder 로 둠"
    if "패널고장여부_ko" not in source_df.columns:
        return "- fault status 컬럼이 없어 신규 fault panel 목록을 만들지 못함"
    fault_df = source_df.loc[source_df["패널고장여부_ko"].map(normalize_text).eq("고장")].copy()
    if fault_df.empty:
        return "- 없음 또는 stable foundation output 기준 신규 고장 미확인"
    rows = []
    for row in fault_df.to_dict(orient="records"):
        site = normalize_text(row.get("site"))
        panel_id = normalize_text(row.get("panel_id"))
        event_type = normalize_text(row.get("사건유형_ko"))
        terminal = normalize_text(row.get("최종고장양상_ko"))
        family = normalize_text(row.get("conalog_원인군_ko"))
        rows.append(f"{site}/{panel_id}: {event_type} / {terminal} / {family}")
    return format_bullets(rows, "신규 fault panel 없음")


def interpretation_notes(
    metadata: dict[str, object] | None,
    has_reference_sidecar: bool,
    panel_source: str,
) -> str:
    rows = [
        "panel multiaxis verdict 를 primary 로 읽어야 함",
        "conalog 는 direct operational interpretation layer 임",
        "GPVS 는 reference-only 임",
        "heuristic 은 triage-only 임",
    ]
    if metadata is not None:
        runtime_mode = normalize_text(metadata.get("runtime_mode", ""))
        run_status = normalize_text(metadata.get("run_status_ko", ""))
        if runtime_mode:
            rows.append(f"runtime mode={runtime_mode}")
        if run_status:
            rows.append(f"runtime status={run_status}")
    rows.append(f"panel result source={panel_source}")
    rows.append(
        "reference sidecar 사용 가능"
        if has_reference_sidecar
        else "reference sidecar 는 현재 latest 경로에 없거나 stable-only 실행이었음"
    )
    return format_bullets(rows, "주요 해석 메모 없음")


def error_summary_text(failure_rows: list[dict[str, object]]) -> str:
    if not failure_rows:
        return "- 실행 오류 없음"
    rows = []
    for row in failure_rows[-5:]:
        message = normalize_text(row.get("message_ko", "")) or normalize_text(row.get("message", ""))
        stage = normalize_text(row.get("stage", ""))
        rows.append(f"{stage}: {message}" if stage else message)
    return format_bullets(rows, "실행 오류 없음")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    output_root = args.output_root.expanduser()
    latest_root = latest_dir(output_root)
    latest_root.mkdir(parents=True, exist_ok=True)

    panel_result_df, panel_source = choose_frame(latest_root / LATEST_FILES["panel_result"])
    site_summary_df, site_summary_source = choose_frame(latest_root / LATEST_FILES["site_summary"])
    heuristic_df, heuristic_source = choose_frame(
        latest_root / LATEST_FILES["cause_candidate_heuristics"],
        FALLBACK_FILES["cause_candidate_heuristics"],
    )
    gpvs_summary_df = read_optional_csv(FALLBACK_FILES["gpvs_evidence_summary"])
    cause_summary_df = read_optional_csv(FALLBACK_FILES["cause_candidate_summary"])
    metadata = read_optional_json(latest_root / LATEST_FILES["metadata"])
    failure_rows = read_jsonl_messages(latest_root / LATEST_FILES["failure_log"])
    has_reference_sidecar = (latest_root / LATEST_FILES["reference_sidecar"]).exists()

    total_panel_count, fault_panel_count, non_fault_or_unresolved_count = count_summary(
        site_summary_df,
        panel_result_df,
    )

    context = {
        "generated_at": now_utc(),
        "site_summary": site_summary_text(site_summary_df, site_summary_source),
        "total_panel_count": total_panel_count,
        "fault_panel_count": fault_panel_count,
        "non_fault_or_unresolved_count": non_fault_or_unresolved_count,
        "conalog_fault_family_distribution": conalog_distribution_text(panel_result_df, panel_source),
        "gpvs_usage_summary": gpvs_usage_text(gpvs_summary_df),
        "suspected_cause_distribution": suspected_cause_text(heuristic_df, cause_summary_df),
        "new_fault_panel_list": new_fault_panels_text(panel_result_df),
        "day_over_day_changes": "- 전일 baseline 비교 입력이 현재 foundation 경로에는 없어 placeholder 로 둠",
        "interpretation_notes": interpretation_notes(metadata, has_reference_sidecar, panel_source if panel_source else heuristic_source),
        "error_summary": error_summary_text(failure_rows),
    }

    template_text = args.template.read_text(encoding="utf-8")
    report_text = template_text.format(**context)
    (latest_root / LATEST_FILES["daily_report"]).write_text(report_text, encoding="utf-8")


if __name__ == "__main__":
    main()
