#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]

KNOWN_OPERATIONAL_SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")

VERDICT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
HEURISTIC_NAME = "panel_day_engine_cause_candidate_heuristics_v1.csv"

PANEL_RESULT_NAME = "panel_result_v1.csv"
SITE_DAY_SUMMARY_NAME = "site_day_summary_v1.csv"
PERIOD_SUMMARY_NAME = "period_summary_v1.csv"
CAUSE_DISTRIBUTION_NAME = "cause_candidate_distribution_v1.csv"
RUN_METADATA_NAME = "run_metadata_v1.json"
ERROR_LOG_NAME = "error_log_v1.csv"

TRUTH_SOURCE_CANDIDATES = [
    "_share/field_truth_template.csv",
    "_share/field_truth_template.xlsx",
    "_share/episode_truth_template.csv",
    "_share/episode_truth_template_p1.csv",
]

PANEL_RESULT_COLS = [
    "site",
    "panel_id",
    "target_window_start_date",
    "target_window_end_date",
    "패널고장여부_ko",
    "사건유형_ko",
    "최종고장양상_ko",
    "conalog_원인군_ko",
    "1순위_의심원인_ko",
    "2순위_의심원인_ko",
    "3순위_의심원인_ko",
    "result_source_ko",
    "note_ko",
]

SITE_DAY_SUMMARY_COLS = [
    "site",
    "date",
    "mode",
    "gpvs_attach_flag",
    "report_flag",
    "candidate_input_file_count",
    "detected_input_date_min",
    "detected_input_date_max",
    "preview_panel_count",
    "preview_fault_panel_count",
    "run_status_ko",
    "note_ko",
]

PERIOD_SUMMARY_COLS = [
    "site",
    "start_date",
    "end_date",
    "requested_day_count",
    "candidate_input_file_count",
    "preview_panel_count",
    "preview_fault_panel_count",
    "gpvs_attach_flag",
    "report_flag",
    "mode",
    "note_ko",
]

CAUSE_DISTRIBUTION_COLS = [
    "site",
    "candidate_ko",
    "panel_count",
    "distribution_basis_ko",
    "note_ko",
]

ERROR_LOG_COLS = [
    "logged_at_utc",
    "level",
    "site",
    "stage_ko",
    "code",
    "message_ko",
]

VERDICT_REQUIRED_COLS = [
    "site",
    "panel_id",
    "패널고장여부_ko",
    "사건유형_ko",
    "최종고장양상_ko",
    "커널로그_원인군_ko",
]

HEURISTIC_REQUIRED_COLS = [
    "site",
    "panel_id",
    "원인후보_top1_ko",
    "원인후보_top2_ko",
    "원인후보_top3_ko",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a foundation-only historical backfill package from frozen stable panel result layers."
    )
    parser.add_argument("--site", required=True, help='Single site name or "all".')
    parser.add_argument("--start-date", required=True, help="Inclusive start date in YYYY-MM-DD format.")
    parser.add_argument("--end-date", required=True, help="Inclusive end date in YYYY-MM-DD format.")
    parser.add_argument("--input-root", type=Path, required=True, help="Input repository/data root.")
    parser.add_argument("--output-root", type=Path, required=True, help="Destination root for dedicated backfill runs.")
    parser.add_argument("--gpvs-attach", choices=["on", "off"], required=True, help="Whether GPVS-derived fields are projected into preview outputs.")
    parser.add_argument("--report", choices=["on", "off"], required=True, help="Whether downstream report packaging is requested.")
    parser.add_argument("--mode", choices=["operational", "eval"], default="operational", help="Backfill mode. Defaults to operational.")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and emit plan/metadata preview without model execution.")
    return parser.parse_args(argv)


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def parse_iso_date(text: str, label: str) -> pd.Timestamp:
    parsed = pd.to_datetime(text, format="%Y-%m-%d", errors="coerce")
    if pd.isna(parsed):
        raise SystemExit(f"{label} must be YYYY-MM-DD, got {text}")
    return parsed.normalize()


def read_optional_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def git_value(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def discover_operational_sites(input_root: Path) -> list[str]:
    data_dir = input_root / "data"
    if not data_dir.exists():
        return []
    discovered = {
        child.name
        for child in data_dir.iterdir()
        if child.is_dir()
    }
    return [site for site in KNOWN_OPERATIONAL_SITES if site in discovered]


def resolve_selected_sites(site_arg: str, discovered_sites: list[str]) -> list[str]:
    normalized = site_arg.strip()
    if not normalized:
        raise SystemExit("--site must not be blank")
    if normalized == "all":
        return discovered_sites or KNOWN_OPERATIONAL_SITES
    if normalized in KNOWN_OPERATIONAL_SITES:
        return [normalized]
    if normalized in discovered_sites:
        return [normalized]
    raise SystemExit(f"unsupported site filter: {normalized}")


def scan_site_inventory(input_root: Path, site: str) -> dict[str, str | int]:
    site_dir = input_root / "data" / site
    if not site_dir.exists():
        return {
            "site": site,
            "candidate_input_file_count": 0,
            "detected_input_date_min": "",
            "detected_input_date_max": "",
        }

    csv_files: list[Path] = []
    dates: list[pd.Timestamp] = []
    for path in site_dir.rglob("*.csv"):
        if any(part == "out" or part.startswith("out_") for part in path.parts):
            continue
        csv_files.append(path)
        match = DATE_RE.search(path.name)
        if match:
            date = pd.to_datetime(match.group(1), errors="coerce")
            if pd.notna(date):
                dates.append(date.normalize())

    min_date = dates and min(dates).date().isoformat() or ""
    max_date = dates and max(dates).date().isoformat() or ""
    return {
        "site": site,
        "candidate_input_file_count": len(csv_files),
        "detected_input_date_min": min_date,
        "detected_input_date_max": max_date,
    }


def discover_truth_source(input_root: Path) -> str:
    for relative_path in TRUTH_SOURCE_CANDIDATES:
        path = input_root / relative_path
        if path.exists():
            return str(path.resolve())
    return ""


def build_run_id(site_filter: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    site_token = site_filter.replace("/", "_")
    return f"historical_backfill_v1_{timestamp}_{site_token}"


def date_range_days(start_date: pd.Timestamp, end_date: pd.Timestamp) -> list[str]:
    current = start_date
    values: list[str] = []
    while current <= end_date:
        values.append(current.date().isoformat())
        current += timedelta(days=1)
    return values


def build_panel_result_preview(
    verdict_df: pd.DataFrame,
    heuristic_df: pd.DataFrame,
    *,
    selected_sites: list[str],
    start_date: str,
    end_date: str,
    gpvs_attach_flag: str,
    dry_run: bool,
) -> pd.DataFrame:
    if verdict_df.empty:
        return pd.DataFrame(columns=PANEL_RESULT_COLS)

    ensure_columns(verdict_df, VERDICT_REQUIRED_COLS, VERDICT_NAME)
    heuristic_lookup: dict[tuple[str, str], dict[str, str]] = {}
    if not heuristic_df.empty:
        ensure_columns(heuristic_df, HEURISTIC_REQUIRED_COLS, HEURISTIC_NAME)
        for row in heuristic_df.to_dict(orient="records"):
            key = (normalize_text(row["site"]), normalize_text(row["panel_id"]))
            heuristic_lookup[key] = {column: normalize_text(value) for column, value in row.items()}

    filtered_verdict = verdict_df.loc[verdict_df["site"].map(normalize_text).isin(selected_sites)].copy()
    result_source = "stable_snapshot_preview_dry_run" if dry_run else "stable_snapshot_placeholder_run"
    note = (
        "dry-run preview only; historical day-level engine replay는 아직 수행하지 않았음"
        if dry_run
        else "foundation-only placeholder output; historical day-level engine replay는 다음 단계에서 연결 예정임"
    )
    rows: list[dict[str, str]] = []
    for row in filtered_verdict.to_dict(orient="records"):
        key = (normalize_text(row["site"]), normalize_text(row["panel_id"]))
        preview = heuristic_lookup.get(key, {})
        if gpvs_attach_flag == "on":
            top1 = normalize_text(preview.get("원인후보_top1_ko", ""))
            top2 = normalize_text(preview.get("원인후보_top2_ko", ""))
            top3 = normalize_text(preview.get("원인후보_top3_ko", ""))
        else:
            top1 = ""
            top2 = ""
            top3 = ""
        rows.append(
            {
                "site": normalize_text(row["site"]),
                "panel_id": normalize_text(row["panel_id"]),
                "target_window_start_date": start_date,
                "target_window_end_date": end_date,
                "패널고장여부_ko": normalize_text(row["패널고장여부_ko"]),
                "사건유형_ko": normalize_text(row["사건유형_ko"]),
                "최종고장양상_ko": normalize_text(row["최종고장양상_ko"]),
                "conalog_원인군_ko": normalize_text(row["커널로그_원인군_ko"]),
                "1순위_의심원인_ko": top1,
                "2순위_의심원인_ko": top2,
                "3순위_의심원인_ko": top3,
                "result_source_ko": result_source,
                "note_ko": note,
            }
        )
    preview_df = pd.DataFrame(rows).reindex(columns=PANEL_RESULT_COLS)
    return preview_df.sort_values(["site", "panel_id"], ascending=[True, True]).reset_index(drop=True)


def build_site_day_summary(
    *,
    selected_sites: list[str],
    inventory_rows: dict[str, dict[str, str | int]],
    panel_result_df: pd.DataFrame,
    dates: list[str],
    gpvs_attach_flag: str,
    report_flag: str,
    mode: str,
    dry_run: bool,
) -> pd.DataFrame:
    run_status = "dry_run_plan" if dry_run else "foundation_stub"
    note = (
        "요청 구간 day plan 미리보기이며 실제 detector execution은 수행하지 않았음"
        if dry_run
        else "foundation stub 요약이며 실제 historical day replay 연결은 다음 단계에서 수행함"
    )
    panel_counts = panel_result_df.groupby("site").size().to_dict() if not panel_result_df.empty else {}
    fault_counts = (
        panel_result_df.loc[panel_result_df["패널고장여부_ko"].map(normalize_text).eq("고장")]
        .groupby("site")
        .size()
        .to_dict()
        if not panel_result_df.empty
        else {}
    )
    rows: list[dict[str, str | int]] = []
    for site in selected_sites:
        inventory = inventory_rows.get(site, {})
        for date_text in dates:
            rows.append(
                {
                    "site": site,
                    "date": date_text,
                    "mode": mode,
                    "gpvs_attach_flag": gpvs_attach_flag,
                    "report_flag": report_flag,
                    "candidate_input_file_count": int(inventory.get("candidate_input_file_count", 0)),
                    "detected_input_date_min": str(inventory.get("detected_input_date_min", "")),
                    "detected_input_date_max": str(inventory.get("detected_input_date_max", "")),
                    "preview_panel_count": int(panel_counts.get(site, 0)),
                    "preview_fault_panel_count": int(fault_counts.get(site, 0)),
                    "run_status_ko": run_status,
                    "note_ko": note,
                }
            )
    return pd.DataFrame(rows).reindex(columns=SITE_DAY_SUMMARY_COLS)


def build_period_summary(
    *,
    selected_sites: list[str],
    inventory_rows: dict[str, dict[str, str | int]],
    panel_result_df: pd.DataFrame,
    start_date: str,
    end_date: str,
    requested_day_count: int,
    gpvs_attach_flag: str,
    report_flag: str,
    mode: str,
    dry_run: bool,
) -> pd.DataFrame:
    note = (
        "current frozen stable outputs를 preview source로만 읽은 foundation backfill 요약임"
        if dry_run
        else "current frozen stable outputs를 placeholder source로 읽은 foundation backfill 요약임"
    )
    rows: list[dict[str, str | int]] = []
    total_candidate_files = 0
    total_preview_rows = 0
    total_fault_rows = 0
    for site in selected_sites:
        inventory = inventory_rows.get(site, {})
        site_panel_df = panel_result_df.loc[panel_result_df["site"].map(normalize_text).eq(site)].copy()
        preview_panel_count = int(len(site_panel_df))
        preview_fault_count = int(site_panel_df["패널고장여부_ko"].map(normalize_text).eq("고장").sum()) if not site_panel_df.empty else 0
        candidate_count = int(inventory.get("candidate_input_file_count", 0))
        total_candidate_files += candidate_count
        total_preview_rows += preview_panel_count
        total_fault_rows += preview_fault_count
        rows.append(
            {
                "site": site,
                "start_date": start_date,
                "end_date": end_date,
                "requested_day_count": requested_day_count,
                "candidate_input_file_count": candidate_count,
                "preview_panel_count": preview_panel_count,
                "preview_fault_panel_count": preview_fault_count,
                "gpvs_attach_flag": gpvs_attach_flag,
                "report_flag": report_flag,
                "mode": mode,
                "note_ko": note,
            }
        )
    rows.append(
        {
            "site": "all" if len(selected_sites) > 1 else selected_sites[0],
            "start_date": start_date,
            "end_date": end_date,
            "requested_day_count": requested_day_count,
            "candidate_input_file_count": total_candidate_files,
            "preview_panel_count": total_preview_rows,
            "preview_fault_panel_count": total_fault_rows,
            "gpvs_attach_flag": gpvs_attach_flag,
            "report_flag": report_flag,
            "mode": mode,
            "note_ko": "site-level rows를 합산한 run-period summary 임",
        }
    )
    return pd.DataFrame(rows).reindex(columns=PERIOD_SUMMARY_COLS)


def build_cause_candidate_distribution(
    panel_result_df: pd.DataFrame,
    *,
    gpvs_attach_flag: str,
    dry_run: bool,
) -> pd.DataFrame:
    if gpvs_attach_flag != "on":
        return pd.DataFrame(columns=CAUSE_DISTRIBUTION_COLS)

    fault_df = panel_result_df.loc[panel_result_df["패널고장여부_ko"].map(normalize_text).eq("고장")].copy()
    if fault_df.empty:
        return pd.DataFrame(columns=CAUSE_DISTRIBUTION_COLS)

    rows: list[dict[str, str | int]] = []
    note = (
        "dry-run preview 기준 top1 suspected cause 분포이며 historical replay 실결과가 아님"
        if dry_run
        else "foundation placeholder 기준 top1 suspected cause 분포이며 historical replay 실결과가 아님"
    )
    for site, site_df in fault_df.groupby("site", dropna=False):
        counts = site_df["1순위_의심원인_ko"].map(normalize_text).value_counts().to_dict()
        for candidate, count in sorted(counts.items()):
            if not candidate:
                continue
            rows.append(
                {
                    "site": normalize_text(site),
                    "candidate_ko": candidate,
                    "panel_count": int(count),
                    "distribution_basis_ko": "top1_preview",
                    "note_ko": note,
                }
            )
    return pd.DataFrame(rows).reindex(columns=CAUSE_DISTRIBUTION_COLS)


def build_error_log_rows(
    *,
    selected_sites: list[str],
    truth_source_path: str,
    mode: str,
) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    if mode == "eval" and not truth_source_path:
        rows.append(
            {
                "logged_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "level": "warning",
                "site": ",".join(selected_sites),
                "stage_ko": "eval_mode_precheck",
                "code": "truth_source_missing_continue",
                "message_ko": "eval mode 요청이었지만 truth source를 찾지 못해 operational-style outputs로 계속 진행함",
            }
        )
    return pd.DataFrame(rows).reindex(columns=ERROR_LOG_COLS)


def metadata_note(
    *,
    dry_run: bool,
    gpvs_attach_flag: str,
    report_flag: str,
    mode: str,
    truth_source_path: str,
) -> str:
    parts = [
        "historical backfill foundation run으로 detector logic 재정의나 재학습은 수행하지 않았음",
        "panel multiaxis verdict를 primary로, conalog를 direct operational interpretation layer로 유지함",
        "GPVS는 reference-only이며 heuristic은 field-trial triage layer로만 유지함",
    ]
    if dry_run:
        parts.append("dry-run이므로 실제 model execution 없이 run plan/metadata preview와 contract outputs만 생성하였음")
    else:
        parts.append("foundation step이므로 historical day-level replay 대신 stable snapshot placeholder outputs를 생성하였음")
    if gpvs_attach_flag == "off":
        parts.append("GPVS attach off 요청에 따라 suspected-cause projection은 비워 두었음")
    if report_flag == "on":
        parts.append("report on 요청은 metadata에만 반영하였고 one-click/report automation은 이번 단계에 병합하지 않았음")
    if mode == "eval" and not truth_source_path:
        parts.append("truth source 미확인이라 eval hard fail 없이 operational-style outputs로 계속 진행하였음")
    return ". ".join(parts)


def write_csv(path: Path, df: pd.DataFrame, columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def build_outputs(args: argparse.Namespace) -> tuple[Path, dict[str, object]]:
    input_root = args.input_root.resolve()
    output_root = args.output_root.resolve()
    start_date = parse_iso_date(args.start_date, "--start-date")
    end_date = parse_iso_date(args.end_date, "--end-date")
    if end_date < start_date:
        raise SystemExit("--end-date must be on or after --start-date")

    discovered_sites = discover_operational_sites(input_root)
    selected_sites = resolve_selected_sites(args.site, discovered_sites)
    inventory_rows = {
        site: scan_site_inventory(input_root, site)
        for site in selected_sites
    }
    truth_source_path = discover_truth_source(input_root) if args.mode == "eval" else ""

    share_dir = input_root / "_share"
    verdict_df = read_optional_csv(share_dir / VERDICT_NAME)
    heuristic_df = read_optional_csv(share_dir / HEURISTIC_NAME)

    panel_result_df = build_panel_result_preview(
        verdict_df,
        heuristic_df,
        selected_sites=selected_sites,
        start_date=start_date.date().isoformat(),
        end_date=end_date.date().isoformat(),
        gpvs_attach_flag=args.gpvs_attach,
        dry_run=args.dry_run,
    )
    date_values = date_range_days(start_date, end_date)
    site_day_summary_df = build_site_day_summary(
        selected_sites=selected_sites,
        inventory_rows=inventory_rows,
        panel_result_df=panel_result_df,
        dates=date_values,
        gpvs_attach_flag=args.gpvs_attach,
        report_flag=args.report,
        mode=args.mode,
        dry_run=args.dry_run,
    )
    period_summary_df = build_period_summary(
        selected_sites=selected_sites,
        inventory_rows=inventory_rows,
        panel_result_df=panel_result_df,
        start_date=start_date.date().isoformat(),
        end_date=end_date.date().isoformat(),
        requested_day_count=len(date_values),
        gpvs_attach_flag=args.gpvs_attach,
        report_flag=args.report,
        mode=args.mode,
        dry_run=args.dry_run,
    )
    cause_distribution_df = build_cause_candidate_distribution(
        panel_result_df,
        gpvs_attach_flag=args.gpvs_attach,
        dry_run=args.dry_run,
    )
    error_log_df = build_error_log_rows(
        selected_sites=selected_sites,
        truth_source_path=truth_source_path,
        mode=args.mode,
    )

    run_id = build_run_id(args.site)
    run_dir = output_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    write_csv(run_dir / PANEL_RESULT_NAME, panel_result_df, PANEL_RESULT_COLS)
    write_csv(run_dir / SITE_DAY_SUMMARY_NAME, site_day_summary_df, SITE_DAY_SUMMARY_COLS)
    write_csv(run_dir / PERIOD_SUMMARY_NAME, period_summary_df, PERIOD_SUMMARY_COLS)
    write_csv(run_dir / CAUSE_DISTRIBUTION_NAME, cause_distribution_df, CAUSE_DISTRIBUTION_COLS)
    write_csv(run_dir / ERROR_LOG_NAME, error_log_df, ERROR_LOG_COLS)

    metadata = {
        "run_id": run_id,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_branch": git_value(["rev-parse", "--abbrev-ref", "HEAD"]),
        "git_head": git_value(["rev-parse", "HEAD"]),
        "site_filter": args.site,
        "start_date": start_date.date().isoformat(),
        "end_date": end_date.date().isoformat(),
        "gpvs_attach_flag": args.gpvs_attach,
        "report_flag": args.report,
        "mode": args.mode,
        "note_ko": metadata_note(
            dry_run=args.dry_run,
            gpvs_attach_flag=args.gpvs_attach,
            report_flag=args.report,
            mode=args.mode,
            truth_source_path=truth_source_path,
        ),
        "dry_run": bool(args.dry_run),
        "input_root": str(input_root),
        "output_root": str(output_root),
        "run_dir": str(run_dir),
        "selected_sites": selected_sites,
        "discovered_operational_sites": discovered_sites,
        "truth_source_path": truth_source_path,
        "panel_result_row_count": int(len(panel_result_df)),
        "site_day_summary_row_count": int(len(site_day_summary_df)),
        "period_summary_row_count": int(len(period_summary_df)),
        "cause_candidate_distribution_row_count": int(len(cause_distribution_df)),
        "error_log_row_count": int(len(error_log_df)),
        "required_output_files": [
            PANEL_RESULT_NAME,
            SITE_DAY_SUMMARY_NAME,
            PERIOD_SUMMARY_NAME,
            CAUSE_DISTRIBUTION_NAME,
            RUN_METADATA_NAME,
            ERROR_LOG_NAME,
        ],
        "site_inventory_preview": inventory_rows,
    }
    (run_dir / RUN_METADATA_NAME).write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return run_dir, metadata


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_dir, metadata = build_outputs(args)
    print(json.dumps({"run_dir": str(run_dir), "run_id": metadata["run_id"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
