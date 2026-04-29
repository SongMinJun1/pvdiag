#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


REVIEW_NAME = "panel_day_engine_episode_truth_durable_shape_review_v1.csv"
MIXED_INPUT_NAME = "panel_day_engine_episode_truth_review_input_mixed_v1.csv"
SUMMARY_NAME = "panel_day_engine_episode_truth_durable_shape_review_summary_v1.csv"
JSON_NAME = "panel_day_engine_episode_truth_durable_shape_review_v1.json"


BR088_COLUMNS = [
    "adjudication_row_id",
    "conservative_decision",
    "decision_confidence",
    "reviewer_truth_label",
    "reviewer_evidence_path",
    "reviewer_notes",
    "br084_expected_review_status",
    "br084_expected_truth_role",
    "threshold_replay_input_allowed_candidate",
    "positive_replay_candidate",
    "negative_replay_candidate",
    "defer_reason",
    "worksheet_row_id",
    "reviewed_truth_row_id",
    "review_packet_id",
    "review_priority",
    "review_track",
    "episode_truth_bucket",
    "site",
    "panel_id",
    "family_key",
    "subtype_key",
    "episode_anchor_date",
    "strict_trigger_date",
    "gap_days",
    "signal_day_count",
    "common_cause_flag_sum",
    "strict_trigger_proximal_common_cause_flag",
    "source_reference_count",
    "trace_ready_all",
    "source_gap_days_min",
    "source_gap_days_max",
    "source_episode_classes",
    "source_precursor_promotion_decisions",
    "source_shadow_reasons",
    "source_references",
    "evidence_card_path",
    "evidence_card_exists",
    "must_prove_axes",
    "must_reject_axes",
    "candidate_reading",
    "default_review_disposition",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

CORE_COLUMNS = [
    "date",
    "panel_id",
    "event_A",
    "is_ae_abn",
    "is_ae_strong",
    "fault_like_day",
    "critical_fault",
    "final_fault",
    "re_drop",
    "degraded_candidate",
    "subgroup_common_cause_candidate",
    "data_bad",
    "mid_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "dtw_dist",
    "co_drop_frac",
    "anom_level",
    "ae_strength",
    "anom_subtype",
]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_card(root: Path, name: str) -> str:
    path = root / "cards" / f"{name}.md"
    path.parent.mkdir(exist_ok=True)
    path.write_text(f"# {name}\n", encoding="utf-8")
    return str(path)


def br088_row(
    root: Path,
    idx: int,
    decision: str,
    site: str,
    panel_id: str,
    label: str = "",
    evidence_path: str = "",
    notes: str = "",
) -> dict[str, object]:
    return {
        "adjudication_row_id": f"BR088-CADJ-{idx:03d}",
        "conservative_decision": decision,
        "decision_confidence": "fixture",
        "reviewer_truth_label": label,
        "reviewer_evidence_path": evidence_path,
        "reviewer_notes": notes,
        "br084_expected_review_status": "reviewed_negative" if label else "needs_evidence",
        "br084_expected_truth_role": "negative_counterexample" if label else "unassigned",
        "threshold_replay_input_allowed_candidate": 1 if label else 0,
        "positive_replay_candidate": 0,
        "negative_replay_candidate": 1 if label else 0,
        "defer_reason": "" if label else "fixture durable hold",
        "worksheet_row_id": f"BR087-ADJ-{idx:03d}",
        "reviewed_truth_row_id": f"BR084-RTR-{idx:03d}",
        "review_packet_id": f"BR082-EPR-{idx:03d}",
        "review_priority": "P1",
        "review_track": "durable_precursor_review" if not label else "long_gap_backdating_review",
        "episode_truth_bucket": "fixture_bucket",
        "site": site,
        "panel_id": panel_id,
        "family_key": "fixture_family",
        "subtype_key": "fixture_subtype",
        "episode_anchor_date": "2025-01-01",
        "strict_trigger_date": "2025-01-20",
        "gap_days": 19,
        "signal_day_count": 0,
        "common_cause_flag_sum": 0,
        "strict_trigger_proximal_common_cause_flag": 0,
        "source_reference_count": 1,
        "trace_ready_all": 1,
        "source_gap_days_min": 19,
        "source_gap_days_max": 19,
        "source_episode_classes": "intermittent_precursor_candidate",
        "source_precursor_promotion_decisions": "manual_review_candidate",
        "source_shadow_reasons": "fixture reason",
        "source_references": f"fixture:{idx}",
        "evidence_card_path": evidence_path or write_card(root, f"card-{idx}"),
        "evidence_card_exists": 1,
        "must_prove_axes": "fixture prove",
        "must_reject_axes": "fixture reject",
        "candidate_reading": "fixture candidate",
        "default_review_disposition": "manual_review_no_promotion_yet",
        "operator_facing_change_allowed": 0,
        "engine_patch_allowed": 0,
        "threshold_patch_allowed": 0,
        "notes": "",
    }


def core_row(date: str, panel_id: str, strong: bool) -> dict[str, object]:
    return {
        "date": date,
        "panel_id": panel_id,
        "event_A": strong,
        "is_ae_abn": strong,
        "is_ae_strong": strong,
        "fault_like_day": date == "2025-01-20",
        "critical_fault": False,
        "final_fault": date == "2025-01-20",
        "re_drop": False,
        "degraded_candidate": False,
        "subgroup_common_cause_candidate": False,
        "data_bad": False,
        "mid_ratio": 0.64 if strong else 1.0,
        "mid_v_ratio": 0.65 if strong else 1.0,
        "mid_i_ratio": 0.98 if strong else 1.0,
        "dtw_dist": 12.0 if strong else 0.2,
        "co_drop_frac": 0.0,
        "anom_level": "fault_like" if date == "2025-01-20" else "normal",
        "ae_strength": "high" if strong else "low",
        "anom_subtype": "fault_like_weak" if date == "2025-01-20" else "normal",
    }


def write_fixtures(root: Path) -> tuple[Path, Path]:
    data_root = root / "data"
    site_dir = data_root / "alpha" / "out"
    site_dir.mkdir(parents=True)
    dates = pd.date_range("2025-01-01", "2025-01-20", freq="D").strftime("%Y-%m-%d").tolist()
    core_rows = [core_row(date, "panel-pos", True) for date in dates]
    core_rows += [core_row(date, "panel-hold", False) for date in dates]
    pd.DataFrame(core_rows).reindex(columns=CORE_COLUMNS).to_csv(
        site_dir / "panel_day_core.csv",
        index=False,
        encoding="utf-8-sig",
    )

    neg_card = write_card(root, "negative-card")
    rows = [
        br088_row(
            root,
            1,
            "fill_conservative_negative_long_gap_backdating",
            "alpha",
            "panel-neg",
            label="episode_only_or_backdating",
            evidence_path=neg_card,
            notes="fixture negative",
        ),
        br088_row(root, 2, "defer_positive_or_hold_review", "alpha", "panel-pos"),
        br088_row(root, 3, "defer_positive_or_hold_review", "alpha", "panel-hold"),
    ]
    br088_path = root / "br088.csv"
    pd.DataFrame(rows).reindex(columns=BR088_COLUMNS).to_csv(br088_path, index=False, encoding="utf-8-sig")
    return br088_path, data_root


def run_builder(
    repo_root: Path,
    br088_path: Path | None,
    data_root: Path,
    output_dir: Path,
    input_manifest: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        "research/prognostics/build_panel_day_engine_episode_truth_durable_shape_review_v1.py",
        "--repo-root",
        str(repo_root),
        "--data-root",
        str(data_root),
        "--output-dir",
        str(output_dir),
    ]
    if br088_path is not None:
        cmd.extend(["--br088-input", str(br088_path)])
    if input_manifest is not None:
        cmd.extend(["--input-manifest", str(input_manifest)])
    return run(cmd, cwd=repo_root)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        br088_path, data_root = write_fixtures(root)
        out_dir = root / "out"
        proc = run_builder(repo_root, br088_path, data_root, out_dir)
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)

        review = pd.read_csv(out_dir / REVIEW_NAME, encoding="utf-8-sig")
        mixed = pd.read_csv(out_dir / MIXED_INPUT_NAME, encoding="utf-8-sig")
        summary = pd.read_csv(out_dir / SUMMARY_NAME, encoding="utf-8-sig")
        payload = json.loads((out_dir / JSON_NAME).read_text(encoding="utf-8"))

        assert_true(len(review) == 3, f"expected 3 review rows, got {len(review)}")
        assert_true(len(mixed) == 3, f"expected 3 mixed input rows, got {len(mixed)}")
        assert_true(int(review["positive_replay_candidate"].sum()) == 1, "expected one positive seed")
        assert_true(int(review["negative_replay_candidate"].sum()) == 1, "expected one carried negative")
        assert_true(int(review["threshold_tuning_approved"].sum()) == 0, "must not approve tuning")
        labels = set(mixed["reviewer_truth_label"].fillna(""))
        assert_true("real_precursor" in labels, "missing real precursor label")
        assert_true("episode_only_or_backdating" in labels, "missing carried negative label")
        assert_true("" in labels, "hold row should remain blank")
        assert_true(payload["positive_replay_candidate_rows"] == 1, "json positive count mismatch")
        assert_true(payload["negative_replay_candidate_rows"] == 1, "json negative count mismatch")
        assert_true(payload["threshold_tuning_approved"] == 0, "json must block tuning")
        assert_true(payload["br088_input_source"] == "explicit_cli", "explicit BR-088 input should win")
        assert_true(int(summary["threshold_tuning_approved_sum"].sum()) == 0, "summary must block tuning")

        manifest_path = root / "episode_truth_durable_shape_inputs.json"
        manifest_path.write_text(
            json.dumps({"inputs": {"br088_input": str(br088_path)}}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        manifest_out = root / "manifest_out"
        manifest_proc = run_builder(repo_root, None, data_root, manifest_out, manifest_path)
        assert_true(manifest_proc.returncode == 0, manifest_proc.stderr or manifest_proc.stdout)
        manifest_payload = json.loads((manifest_out / JSON_NAME).read_text(encoding="utf-8"))
        assert_true(manifest_payload["review_rows"] == 3, "manifest run review row count mismatch")
        assert_true(manifest_payload["input_manifest"] == str(manifest_path), "manifest path should be recorded")
        assert_true(manifest_payload["br088_input_source"] == "input_manifest", "BR-088 should resolve from manifest")

        bad_manifest_path = root / "bad_episode_truth_durable_shape_inputs.json"
        bad_manifest_path.write_text(
            json.dumps(
                {"inputs": {"br088_input": str(root / "missing_br088.csv")}},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        override_out = root / "override_out"
        override_proc = run_builder(repo_root, br088_path, data_root, override_out, bad_manifest_path)
        assert_true(override_proc.returncode == 0, override_proc.stderr or override_proc.stdout)
        override_payload = json.loads((override_out / JSON_NAME).read_text(encoding="utf-8"))
        assert_true(override_payload["br088_input_source"] == "explicit_cli", "BR-088 CLI override should win")

        missing_key_manifest_path = root / "missing_key_episode_truth_durable_shape_inputs.json"
        missing_key_manifest_path.write_text(
            json.dumps({"inputs": {}}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        missing_key_proc = run_builder(repo_root, None, data_root, root / "missing_key_out", missing_key_manifest_path)
        assert_true(missing_key_proc.returncode != 0, missing_key_proc.stdout)
        assert_true("missing `br088_input`" in missing_key_proc.stderr, missing_key_proc.stderr)

        unsafe = pd.read_csv(br088_path, encoding="utf-8-sig")
        unsafe["engine_patch_allowed"] = 0
        unsafe.loc[0, "engine_patch_allowed"] = 1
        unsafe_path = root / "unsafe_br088.csv"
        unsafe.to_csv(unsafe_path, index=False, encoding="utf-8-sig")
        unsafe_proc = run_builder(repo_root, unsafe_path, data_root, root / "unsafe_out")
        assert_true(unsafe_proc.returncode != 0, "engine patch authorization should fail")

    print("smoke ok: panel_day_engine_episode_truth_durable_shape_review_v1")


if __name__ == "__main__":
    main()
