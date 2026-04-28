#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-107"
DEFAULT_CAPTURE_INPUT = "/private/tmp/mlpe_field_trial_capture_schema_br102_check/mlpe_field_trial_capture_template_v1.csv"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_filled_capture_fixture_br107_check"

CAPTURE_OUTPUT_NAME = "mlpe_field_trial_filled_capture_fixture_v1.csv"
EVIDENCE_MANIFEST_OUTPUT_NAME = "mlpe_field_trial_filled_capture_fixture_evidence_manifest_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_filled_capture_fixture_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_filled_capture_fixture_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_filled_capture_fixture_v1.json"

CAPTURE_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "site",
    "root_id",
    "panel_id",
    "mlpe_device_id",
    "start_ts",
    "end_ts",
    "capture_status",
    "injection_case",
    "planned_fault_family",
    "planned_fault_subtype",
    "affected_scope",
    "injection_mode",
    "injection_strength",
    "expected_signature",
    "planned_panel_local_flag",
    "planned_common_cause_flag",
    "planned_measurement_artifact_flag",
    "mlpe_state",
    "raw_data_path",
    "peer_data_path",
    "weather_data_path",
    "waveform_slice_path",
    "timestamp_quality",
    "communication_quality",
    "final_fault_family",
    "final_fault_subtype",
    "final_truth_confidence",
    "final_label_attached",
    "label_status",
    "operator_promotion_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "reviewer",
    "review_note",
]


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def read_capture_template(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing capture template: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    for col in CAPTURE_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    out = df.reindex(columns=CAPTURE_COLUMNS).copy()
    for col in CAPTURE_COLUMNS:
        out[col] = out[col].map(normalize_text)
    return out


def write_fixture_file(path: Path, row_id: str, kind: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "ts,v,i,p,kind,trial_event_id",
        f"2026-01-01T00:00:00Z,40.0,8.0,320.0,{kind},{row_id}",
        f"2026-01-01T00:05:00Z,39.5,8.1,319.95,{kind},{row_id}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_fixture(capture: pd.DataFrame, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    evidence_rows = []
    evidence_root = output_dir / "fixture_evidence"
    for idx, row in capture.iterrows():
        event_id = row["trial_event_id"] or f"BR107-FIXTURE-{idx + 1:03d}"
        event_dir = evidence_root / event_id
        raw_path = event_dir / "raw.csv"
        peer_path = event_dir / "peer.csv"
        weather_path = event_dir / "weather.csv"
        wave_path = event_dir / "waveform.csv"
        for path, kind in [
            (raw_path, "raw"),
            (peer_path, "peer"),
            (weather_path, "weather"),
            (wave_path, "waveform"),
        ]:
            write_fixture_file(path, event_id, kind)
            evidence_rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "trial_event_id": event_id,
                    "evidence_kind": kind,
                    "evidence_path": str(path),
                    "exists_flag": int(path.exists()),
                }
            )
        out = row.to_dict()
        out.update(
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": event_id,
                "site": "synthetic_site",
                "root_id": f"synthetic_root_{idx % 3 + 1}",
                "panel_id": f"synthetic_panel_{idx + 1:03d}",
                "mlpe_device_id": f"synthetic_mlpe_{idx + 1:03d}",
                "start_ts": "2026-01-01T00:00:00Z",
                "end_ts": "2026-01-01T00:10:00Z",
                "capture_status": "captured",
                "injection_strength": "synthetic_fixture_only",
                "raw_data_path": str(raw_path),
                "peer_data_path": str(peer_path),
                "weather_data_path": str(weather_path),
                "waveform_slice_path": str(wave_path),
                "timestamp_quality": "ok",
                "communication_quality": "ok",
                "final_fault_family": "",
                "final_fault_subtype": "",
                "final_truth_confidence": "",
                "final_label_attached": "0",
                "label_status": "label_pending",
                "operator_promotion_allowed": "0",
                "engine_patch_allowed": "0",
                "threshold_patch_allowed": "0",
                "reviewer": "",
                "review_note": "synthetic fixture only; not field truth",
            }
        )
        rows.append(out)
    return pd.DataFrame(rows).reindex(columns=CAPTURE_COLUMNS), pd.DataFrame(evidence_rows)


def build_summary(capture: pd.DataFrame, evidence: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "owner_branch": OWNER_BRANCH,
                "rows": int(len(capture)),
                "captured_rows": int(capture["capture_status"].eq("captured").sum()),
                "label_pending_rows": int(capture["label_status"].eq("label_pending").sum()),
                "final_label_attached_rows": int(capture["final_label_attached"].astype(str).eq("1").sum()),
                "evidence_rows": int(len(evidence)),
                "evidence_missing_rows": int(evidence["exists_flag"].eq(0).sum()),
                "truth_intake_allowed_sum": 0,
                "threshold_patch_allowed_sum": 0,
                "engine_patch_allowed_sum": 0,
            }
        ]
    )


def write_note(output_dir: Path, summary: pd.DataFrame) -> Path:
    row = summary.iloc[0].to_dict()
    note_path = output_dir / NOTE_OUTPUT_NAME
    lines = [
        "# BR-107 MLPE Field-Trial Filled Capture Fixture",
        "",
        "## Purpose",
        "- Create a synthetic filled-capture fixture to dry-run BR-103 readiness and BR-106 handoff behavior.",
        "- Keep the fixture explicitly separate from field truth labels.",
        "",
        "## Real Result",
        f"- rows: `{row['rows']}`",
        f"- captured rows: `{row['captured_rows']}`",
        f"- label-pending rows: `{row['label_pending_rows']}`",
        f"- final label attached rows: `{row['final_label_attached_rows']}`",
        f"- evidence rows: `{row['evidence_rows']}`",
        f"- evidence missing rows: `{row['evidence_missing_rows']}`",
        f"- truth intake allowed sum: `{row['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{row['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{row['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- Synthetic fixture rows may test plumbing only.",
        "- Synthetic fixture rows are not positive truth labels.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--capture-input", default=DEFAULT_CAPTURE_INPUT)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    capture_input = resolve_path(repo_root, args.capture_input)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    capture_template = read_capture_template(capture_input)
    fixture, evidence = build_fixture(capture_template, output_dir)
    summary = build_summary(fixture, evidence)

    capture_path = output_dir / CAPTURE_OUTPUT_NAME
    evidence_path = output_dir / EVIDENCE_MANIFEST_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    fixture.to_csv(capture_path, index=False, encoding="utf-8-sig")
    evidence.to_csv(evidence_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, summary)

    overall = summary.iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "rows": int(overall["rows"]),
        "captured_rows": int(overall["captured_rows"]),
        "label_pending_rows": int(overall["label_pending_rows"]),
        "final_label_attached_rows": int(overall["final_label_attached_rows"]),
        "evidence_rows": int(overall["evidence_rows"]),
        "evidence_missing_rows": int(overall["evidence_missing_rows"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "outputs": {
            "capture": str(capture_path),
            "evidence_manifest": str(evidence_path),
            "summary": str(summary_path),
            "note": str(note_path),
            "json": str(json_path),
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
