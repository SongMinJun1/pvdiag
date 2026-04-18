#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]

VERDICT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
INTEGRATED_NAME = "panel_day_engine_integrated_result_table_v1.csv"
HEURISTIC_NAME = "panel_day_engine_cause_candidate_heuristics_v1.csv"

OUTPUT_DIR_DEFAULT = REPO_ROOT / "outputs" / "validation"
OUTPUT_CSV_NAME = "fault_validation_report_v1.csv"
OUTPUT_MD_NAME = "fault_validation_report_v1.md"

CSV_COLS = [
    "case_id",
    "case_type",
    "validation_axis_ko",
    "input_scope",
    "expected_output_ko",
    "actual_output_ko",
    "pass_flag",
    "note_ko",
]

VERDICT_REQUIRED_COLS = [
    "site",
    "panel_id",
    "패널고장여부_ko",
    "사건유형_ko",
    "최종고장양상_ko",
    "커널로그_원인군_ko",
]

INTEGRATED_REQUIRED_COLS = [
    "site",
    "panel_id",
    "패널고장여부_ko",
    "사건유형_ko",
    "최종고장양상_ko",
    "커널로그_원인군_ko",
    "1순위_의심원인_ko",
    "2순위_의심원인_ko",
    "3순위_의심원인_ko",
]

HEURISTIC_REQUIRED_COLS = [
    "site",
    "panel_id",
    "원인후보_top1_ko",
    "원인후보_top2_ko",
    "원인후보_top3_ko",
    "원인후보_경합상태_ko",
    "원인후보_공동상위후보_csv",
    "원인후보_실증우선확인_ko",
]

SURROGATE_IDS = [
    "surrogate::부분음영형",
    "surrogate::접촉 끊김형",
    "surrogate::장치 측정 이상형",
    "surrogate::장치 응답 이상형",
    "surrogate::gpvs_attach_on_off_fallback",
    "surrogate::sparse_conalog",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the first official fault validation matrix report from frozen stable outputs."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root. Defaults to the project root.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR_DEFAULT,
        help="Output directory for validation report files.",
    )
    return parser.parse_args(argv)


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


def as_key(site: object, panel_id: object) -> tuple[str, str]:
    return normalize_text(site), normalize_text(panel_id)


def lookup_map(df: pd.DataFrame) -> dict[tuple[str, str], dict[str, str]]:
    records: dict[tuple[str, str], dict[str, str]] = {}
    for row in df.to_dict(orient="records"):
        records[as_key(row.get("site"), row.get("panel_id"))] = {
            key: normalize_text(value) for key, value in row.items()
        }
    return records


def object_particle(text: str) -> str:
    normalized = normalize_text(text)
    if not normalized:
        return "를"
    last_char = normalized[-1]
    code_point = ord(last_char)
    if 0xAC00 <= code_point <= 0xD7A3:
        jongseong = (code_point - 0xAC00) % 28
        return "을" if jongseong else "를"
    return "를"


def expected_competition_state(competition_csv: str) -> str:
    names = [name for name in normalize_text(competition_csv).split(",") if name]
    if len(names) <= 1:
        return "단일우세"
    if len(names) == 2:
        return "2자경합"
    return "다자경합"


def expected_action_note(top1_name: str, competition_state: str, competition_csv: str) -> str:
    names = [name for name in normalize_text(competition_csv).split(",") if name]
    if competition_state == "단일우세":
        return f"{top1_name} 우선 점검"
    if competition_state == "2자경합" and len(names) >= 2:
        cand1, cand2 = names[:2]
        return f"{cand1}과 {cand2}{object_particle(cand2)} 함께 우선 점검"
    if competition_state == "다자경합" and len(names) >= 3:
        cand1, cand2, cand3 = names[:3]
        return f"{cand1}, {cand2}, {cand3}을 함께 우선 점검"
    return f"{top1_name} 우선 점검"


def run(cmd: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def build_core_rows(
    verdict_df: pd.DataFrame,
    integrated_df: pd.DataFrame,
    heuristic_df: pd.DataFrame,
) -> list[dict[str, object]]:
    fault_verdict_df = verdict_df.loc[verdict_df["패널고장여부_ko"].map(normalize_text).eq("고장")].copy()
    fault_integrated_df = integrated_df.loc[integrated_df["패널고장여부_ko"].map(normalize_text).eq("고장")].copy()
    if len(fault_verdict_df) != 6:
        raise SystemExit(f"{VERDICT_NAME} current fault panel count must be 6, found {len(fault_verdict_df)}")
    if len(fault_integrated_df) != 6:
        raise SystemExit(f"{INTEGRATED_NAME} current fault panel count must be 6, found {len(fault_integrated_df)}")
    if len(heuristic_df) != 6:
        raise SystemExit(f"{HEURISTIC_NAME} current fault panel count must be 6, found {len(heuristic_df)}")

    verdict_lookup = lookup_map(fault_verdict_df)
    integrated_lookup = lookup_map(fault_integrated_df)
    heuristic_lookup = lookup_map(heuristic_df)

    if set(verdict_lookup) != set(integrated_lookup):
        raise SystemExit("fault key universe mismatch between verdict and integrated outputs")
    if set(verdict_lookup) != set(heuristic_lookup):
        raise SystemExit("fault key universe mismatch between verdict and heuristic outputs")

    rows: list[dict[str, object]] = []
    for key in sorted(verdict_lookup):
        site, panel_id = key
        verdict_row = verdict_lookup[key]
        integrated_row = integrated_lookup[key]
        heuristic_row = heuristic_lookup[key]
        scope = f"frozen_fault_snapshot::{site}/{panel_id}"

        expected_fault_status = normalize_text(verdict_row["패널고장여부_ko"])
        actual_fault_status = normalize_text(integrated_row["패널고장여부_ko"])
        rows.append(
            {
                "case_id": f"core::{panel_id}::패널고장여부",
                "case_type": "core_fault_status",
                "validation_axis_ko": "패널고장여부",
                "input_scope": scope,
                "expected_output_ko": expected_fault_status,
                "actual_output_ko": actual_fault_status,
                "pass_flag": int(expected_fault_status == actual_fault_status),
                "note_ko": "field truth replay가 아니라 frozen panel multiaxis verdict와 final integrated table 간 consistency check 임",
            }
        )

        expected_event_type = normalize_text(verdict_row["사건유형_ko"])
        actual_event_type = normalize_text(integrated_row["사건유형_ko"])
        rows.append(
            {
                "case_id": f"core::{panel_id}::사건유형",
                "case_type": "core_event_type",
                "validation_axis_ko": "사건유형",
                "input_scope": scope,
                "expected_output_ko": expected_event_type,
                "actual_output_ko": actual_event_type,
                "pass_flag": int(expected_event_type == actual_event_type),
                "note_ko": "panel multiaxis verdict primary 축의 event type alignment check 임",
            }
        )

        expected_terminal = normalize_text(verdict_row["최종고장양상_ko"])
        actual_terminal = normalize_text(integrated_row["최종고장양상_ko"])
        rows.append(
            {
                "case_id": f"core::{panel_id}::최종고장양상",
                "case_type": "core_terminal_pattern",
                "validation_axis_ko": "최종고장양상",
                "input_scope": scope,
                "expected_output_ko": expected_terminal,
                "actual_output_ko": actual_terminal,
                "pass_flag": int(expected_terminal == actual_terminal),
                "note_ko": "terminal failure pattern snapshot consistency check 임",
            }
        )

        expected_conalog = normalize_text(verdict_row["커널로그_원인군_ko"])
        actual_conalog = normalize_text(integrated_row["커널로그_원인군_ko"])
        rows.append(
            {
                "case_id": f"core::{panel_id}::conalog원인군",
                "case_type": "core_conalog_family",
                "validation_axis_ko": "conalog 원인군",
                "input_scope": scope,
                "expected_output_ko": expected_conalog,
                "actual_output_ko": actual_conalog,
                "pass_flag": int(expected_conalog == actual_conalog),
                "note_ko": "conalog는 direct operational interpretation layer라는 current frozen rule의 direct consistency check 임",
            }
        )

        expected_competition = expected_competition_state(heuristic_row["원인후보_공동상위후보_csv"])
        actual_competition = normalize_text(heuristic_row["원인후보_경합상태_ko"])
        rows.append(
            {
                "case_id": f"core::{panel_id}::heuristic경합상태",
                "case_type": "core_heuristic_competition",
                "validation_axis_ko": "heuristic competition type",
                "input_scope": scope,
                "expected_output_ko": expected_competition,
                "actual_output_ko": actual_competition,
                "pass_flag": int(expected_competition == actual_competition),
                "note_ko": "heuristic candidate competition type consistency check 임",
            }
        )

        expected_note = expected_action_note(
            normalize_text(heuristic_row["원인후보_top1_ko"]),
            actual_competition,
            normalize_text(heuristic_row["원인후보_공동상위후보_csv"]),
        )
        actual_note = normalize_text(heuristic_row["원인후보_실증우선확인_ko"])
        rows.append(
            {
                "case_id": f"core::{panel_id}::heuristic실증메모",
                "case_type": "core_heuristic_action_note",
                "validation_axis_ko": "heuristic action-note wording alignment",
                "input_scope": scope,
                "expected_output_ko": expected_note,
                "actual_output_ko": actual_note,
                "pass_flag": int(expected_note == actual_note),
                "note_ko": "heuristic action-note wording alignment check 임. final diagnosis가 아니라 triage wording consistency를 점검함",
            }
        )
    return rows


def build_surrogate_rows(
    root: Path,
    integrated_df: pd.DataFrame,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    fault_integrated_df = integrated_df.loc[integrated_df["패널고장여부_ko"].map(normalize_text).eq("고장")].copy()
    label_values = {
        normalize_text(value)
        for value in fault_integrated_df[
            ["1순위_의심원인_ko", "2순위_의심원인_ko", "3순위_의심원인_ko"]
        ].stack().tolist()
        if normalize_text(value)
    }

    for label in ["부분음영형", "접촉 끊김 형", "장치 측정 이상형", "장치 응답 이상형"]:
        rows.append(
            {
                "case_id": f"surrogate::{label.replace(' ', '')}",
                "case_type": "surrogate_display_lane",
                "validation_axis_ko": f"{label} surrogate",
                "input_scope": "synthetic_label_registry",
                "expected_output_ko": f"{label} surrogate lane registered",
                "actual_output_ko": "registered_in_current_fault_output" if label in label_values else "not_observed_in_current_fault_output",
                "pass_flag": int(label in label_values),
                "note_ko": "synthetic/skeleton surrogate row이며 current front-facing suspected-cause lane 등록 여부만 점검함",
            }
        )

    with tempfile.TemporaryDirectory(prefix="pvdiag_validation_gpvs_fallback_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        on_result = run(
            [
                "python",
                "app/run_backfill.py",
                "--dry-run",
                "--site",
                "conalog",
                "--start-date",
                "2024-01-01",
                "--end-date",
                "2024-01-07",
                "--input-root",
                ".",
                "--output-root",
                str(tmp_root / "on"),
                "--gpvs-attach",
                "on",
                "--report",
                "off",
                "--mode",
                "operational",
            ],
            cwd=root,
        )
        off_result = run(
            [
                "python",
                "app/run_backfill.py",
                "--dry-run",
                "--site",
                "conalog",
                "--start-date",
                "2024-01-01",
                "--end-date",
                "2024-01-07",
                "--input-root",
                ".",
                "--output-root",
                str(tmp_root / "off"),
                "--gpvs-attach",
                "off",
                "--report",
                "off",
                "--mode",
                "operational",
            ],
            cwd=root,
        )
        if on_result.returncode != 0 or off_result.returncode != 0:
            raise SystemExit("backfill gpvs attach on/off dry-run fallback check failed")
        on_run_dir = next(path for path in (tmp_root / "on").iterdir() if path.is_dir())
        off_run_dir = next(path for path in (tmp_root / "off").iterdir() if path.is_dir())
        on_df = pd.read_csv(on_run_dir / "panel_result_v1.csv", low_memory=False, encoding="utf-8-sig")
        off_df = pd.read_csv(off_run_dir / "panel_result_v1.csv", low_memory=False, encoding="utf-8-sig")
        top_cols = ["1순위_의심원인_ko", "2순위_의심원인_ko", "3순위_의심원인_ko"]
        on_normalized = on_df[top_cols].apply(lambda column: column.map(normalize_text))
        off_normalized = off_df[top_cols].apply(lambda column: column.map(normalize_text))
        on_has_signal = on_normalized.ne("").any().any()
        off_blank = off_normalized.eq("").all().all()
        rows.append(
            {
                "case_id": "surrogate::gpvs_attach_on_off_fallback",
                "case_type": "surrogate_gpvs_attach_fallback",
                "validation_axis_ko": "GPVS attach on/off fallback test",
                "input_scope": "backfill_dry_run_contract",
                "expected_output_ko": "attach on에서는 preview signal 유지, attach off에서는 GPVS-derived suspected cause blank 유지",
                "actual_output_ko": f"on_preview_populated={int(on_has_signal)}, off_preview_blank={int(off_blank)}",
                "pass_flag": int(on_has_signal and off_blank),
                "note_ko": "synthetic contract surrogate row이며 detector replay가 아니라 backfill foundation fallback behavior를 점검함",
            }
        )

    sparse_df = integrated_df.loc[
        integrated_df["커널로그_원인군_ko"].map(normalize_text).eq("불충분")
    ].copy()
    sparse_blank = True
    if not sparse_df.empty:
        sparse_normalized = sparse_df[
            ["1순위_의심원인_ko", "2순위_의심원인_ko", "3순위_의심원인_ko"]
        ].apply(lambda column: column.map(normalize_text))
        sparse_blank = sparse_normalized.eq("").all().all()
    rows.append(
        {
            "case_id": "surrogate::sparse_conalog",
            "case_type": "surrogate_sparse_conalog",
            "validation_axis_ko": "sparse conalog test",
            "input_scope": "frozen_integrated_snapshot",
            "expected_output_ko": "sparse conalog rows는 conservative하게 유지되고 suspected cause는 blank 처리",
            "actual_output_ko": f"sparse_row_count={len(sparse_df)}, suspected_cause_blank={int(bool(sparse_blank))}",
            "pass_flag": int(len(sparse_df) > 0 and sparse_blank),
            "note_ko": "synthetic/skeleton surrogate row이며 sparse conalog handling guardrail만 점검함",
        }
    )

    return rows


def build_report_md(report_df: pd.DataFrame) -> str:
    total_count = len(report_df)
    pass_count = int(report_df["pass_flag"].sum())
    fail_df = report_df.loc[report_df["pass_flag"].astype(int).ne(1)].copy()
    core_df = report_df.loc[report_df["case_type"].astype(str).str.startswith("core_")].copy()
    surrogate_df = report_df.loc[report_df["case_type"].astype(str).str.startswith("surrogate_")].copy()
    skip_count = 0
    core_panel_ids = sorted(
        {
            part
            for case_id in core_df["case_id"].astype(str).tolist()
            for part in [case_id.split("::")[1] if "::" in case_id else ""]
            if part
        }
    )
    surrogate_matrix_rows = surrogate_df[
        ["case_id", "validation_axis_ko", "expected_output_ko", "actual_output_ko", "pass_flag"]
    ].copy()
    lines = [
        "# Fault Validation Report V1",
        "",
        "## 1. 보고 목적",
        "- 본 보고서는 current frozen fault logic에 대한 첫 공식 field-trial validation matrix 요약임.",
        "- core 6건은 frozen snapshot consistency check로 읽었으며, surrogate rows는 synthetic/contract registration check로 구성하였음.",
        "- 본 단계는 validation framework first 단계이며 full historical evaluation이나 metric optimization을 수행한 보고서는 아님.",
        "",
        "## 2. 요약",
        f"- total cases: {total_count}",
        f"- pass cases: {pass_count}",
        f"- fail cases: {len(fail_df)}",
        f"- skip cases: {skip_count}",
        f"- core fault panels: {len(core_panel_ids)}",
        f"- surrogate rows: {len(surrogate_df)}",
        "",
        "## 3. Core 6 Cases",
        f"- {', '.join(core_panel_ids)}",
        "",
        "## 4. Case Type Summary",
    ]
    case_type_counts = report_df["case_type"].value_counts().to_dict()
    for case_type, count in sorted(case_type_counts.items()):
        lines.append(f"- {case_type}: {count}")
    lines.extend(["", "## 5. Surrogate Coverage Matrix", "", "| case_id | validation_axis_ko | expected_output_ko | actual_output_ko | pass_flag |", "|---|---|---|---|---|"])
    for row in surrogate_matrix_rows.to_dict(orient="records"):
        lines.append(
            f"| {row['case_id']} | {row['validation_axis_ko']} | {row['expected_output_ko']} | {row['actual_output_ko']} | {int(row['pass_flag'])} |"
        )
    lines.extend(["", "## 6. Passes / Fails / Skips"])
    lines.append(f"- passes: {pass_count}")
    lines.append(f"- fails: {len(fail_df)}")
    lines.append(f"- skips: {skip_count}")
    lines.extend(["", "## 7. Failed Cases"])
    if fail_df.empty:
        lines.append("- 없음")
    else:
        for row in fail_df.to_dict(orient="records"):
            lines.append(
                f"- `{row['case_id']}`: expected=`{row['expected_output_ko']}`, actual=`{row['actual_output_ko']}`"
            )
    lines.extend(
        [
            "",
            "## 8. Known Limitations",
            "- 본 단계는 framework validation 우선 단계이므로 measured field performance 자체를 확정한 문서는 아님.",
            "- surrogate rows는 framework placeholder 또는 contract check row이며 final measured performance로 읽으면 안 됨.",
            "- conalog는 direct operational interpretation layer로, GPVS는 reference-only로, heuristic은 triage-only로 유지하였음.",
            "",
            "## 9. Preview",
            "",
            "| case_id | case_type | validation_axis_ko | expected_output_ko | actual_output_ko | pass_flag |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in report_df.head(20).to_dict(orient="records"):
        lines.append(
            f"| {row['case_id']} | {row['case_type']} | {row['validation_axis_ko']} | {row['expected_output_ko']} | {row['actual_output_ko']} | {int(row['pass_flag'])} |"
        )
    return "\n".join(lines) + "\n"


def write_outputs(report_df: pd.DataFrame, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / OUTPUT_CSV_NAME
    md_path = output_dir / OUTPUT_MD_NAME
    report_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    md_path.write_text(build_report_md(report_df), encoding="utf-8")
    return csv_path, md_path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    share_dir = root / "_share"

    verdict_df = read_csv(share_dir / VERDICT_NAME)
    integrated_df = read_csv(share_dir / INTEGRATED_NAME)
    heuristic_df = read_csv(share_dir / HEURISTIC_NAME)

    ensure_columns(verdict_df, VERDICT_REQUIRED_COLS, VERDICT_NAME)
    ensure_columns(integrated_df, INTEGRATED_REQUIRED_COLS, INTEGRATED_NAME)
    ensure_columns(heuristic_df, HEURISTIC_REQUIRED_COLS, HEURISTIC_NAME)

    rows = build_core_rows(verdict_df, integrated_df, heuristic_df)
    rows.extend(build_surrogate_rows(root, integrated_df))
    report_df = pd.DataFrame(rows).reindex(columns=CSV_COLS)
    csv_path, md_path = write_outputs(report_df, args.output_dir.resolve())
    print(f"[OK] wrote {csv_path}")
    print(f"[OK] wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
