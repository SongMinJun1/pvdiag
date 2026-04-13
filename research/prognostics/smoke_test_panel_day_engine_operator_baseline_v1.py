#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from pathlib import Path

import pandas as pd

FEATURE_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "overlap_case_class",
    "fate_class",
    "cohort_hint",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "recurring_run_within_60d",
    "future_fault_linked_flag",
    "future_truth_linked_flag",
    "pre_ews_day_count",
    "ews_warning_day_count",
    "pre_alarm_day_count",
    "prefault_B_day_count",
    "pre_alarm_max_run",
    "any_data_bad",
    "data_bad_day_ratio",
    "cond_evt_day_ratio",
    "cond_evt_same_day_early_corroborated_day_ratio",
    "dtw_mid_or_hi_early_day_ratio",
    "hs_mid_or_hi_early_day_ratio",
    "max_recon_error",
    "max_dtw_dist",
    "p95_dtw_dist",
    "max_hs_score",
    "p95_hs_score",
    "min_mid_i_ratio",
]

V0_SCORE_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "electrical_core_score",
    "electrical_core_minus_broadshape_050",
]

LABEL_PACK_V3_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "label_bucket_v3",
    "training_label_v3",
]

COMPLEMENT_RECOMMENDATION_COLS = ["recommended_next_direction", "rationale_ko"]
THRESHOLD_SPLIT_RECOMMENDATION_COLS = ["recommended_split_rule", "recommended_next_direction", "rationale_ko"]
PREVIEW_POLICY_RECOMMENDATION_COLS = ["recommended_policy_name"]
ATTENTION_POLICY_RECOMMENDATION_COLS = [
    "recommended_policy_name",
    "recommended_policy_reason_ko",
    "expected_use_ko",
    "caution_ko",
]
FATE_CASES_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "discovery_fate_class",
]


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert_true(spec is not None and spec.loader is not None, f"failed to load module: {path.name}")
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def feature_row(
    site: str,
    panel_id: str,
    start: str,
    end: str,
    run_day_count: int,
    run_shape_class: str,
    *,
    overlap_case_class: str = "unmatched_to_review",
    recurring: int = 0,
    future_fault: int = 0,
    future_truth: int = 0,
    max_v_drop: float = 0.5,
    min_mid_v_ratio: float = 0.5,
    min_mid_ratio: float = 0.5,
    mean_signal_count: float = 1.5,
    max_signal_count: float = 2.0,
    p95_recon_error: float = 0.05,
    cond_evt_only_day_ratio: float = 0.5,
    ae_mid_or_hi_early_day_ratio: float = 0.3,
) -> dict[str, object]:
    return {
        "site": site,
        "panel_id": panel_id,
        "run_start_date": start,
        "run_end_date": end,
        "run_day_count": run_day_count,
        "run_shape_class": run_shape_class,
        "overlap_case_class": overlap_case_class,
        "fate_class": "",
        "cohort_hint": "unmatched_other",
        "max_v_drop": max_v_drop,
        "min_mid_v_ratio": min_mid_v_ratio,
        "min_mid_ratio": min_mid_ratio,
        "mean_signal_count": mean_signal_count,
        "max_signal_count": max_signal_count,
        "p95_recon_error": p95_recon_error,
        "cond_evt_only_day_ratio": cond_evt_only_day_ratio,
        "ae_mid_or_hi_early_day_ratio": ae_mid_or_hi_early_day_ratio,
        "recurring_run_within_60d": recurring,
        "future_fault_linked_flag": future_fault,
        "future_truth_linked_flag": future_truth,
        "pre_ews_day_count": 0,
        "ews_warning_day_count": 0,
        "pre_alarm_day_count": 0,
        "prefault_B_day_count": 0,
        "pre_alarm_max_run": 0,
        "any_data_bad": 0,
        "data_bad_day_ratio": 0.0,
        "cond_evt_day_ratio": cond_evt_only_day_ratio,
        "cond_evt_same_day_early_corroborated_day_ratio": 0.0,
        "dtw_mid_or_hi_early_day_ratio": 0.0,
        "hs_mid_or_hi_early_day_ratio": 0.0,
        "max_recon_error": p95_recon_error,
        "max_dtw_dist": 0.0,
        "p95_dtw_dist": 0.0,
        "max_hs_score": 0.0,
        "p95_hs_score": 0.0,
        "min_mid_i_ratio": min_mid_ratio,
    }


def score_row(feature: dict[str, object], raw_score: float) -> dict[str, object]:
    return {
        "site": feature["site"],
        "panel_id": feature["panel_id"],
        "run_start_date": feature["run_start_date"],
        "run_end_date": feature["run_end_date"],
        "electrical_core_score": raw_score + 1.0,
        "electrical_core_minus_broadshape_050": raw_score,
    }


def build_fixture_root(root: Path) -> None:
    features = [
        feature_row(
            "alpha",
            "watch.panel",
            "2025-01-01",
            "2025-01-04",
            12,
            "chronic_alert_run",
            recurring=1,
            max_v_drop=0.90,
            min_mid_v_ratio=0.20,
            min_mid_ratio=0.20,
            mean_signal_count=1.0,
            max_signal_count=1.8,
            p95_recon_error=0.01,
            cond_evt_only_day_ratio=0.2,
            ae_mid_or_hi_early_day_ratio=0.1,
        ),
        feature_row(
            "alpha",
            "queue.panel",
            "2025-01-09",
            "2025-01-10",
            2,
            "medium_alert_run",
            max_v_drop=0.75,
            min_mid_v_ratio=0.35,
            min_mid_ratio=0.35,
            mean_signal_count=1.2,
            max_signal_count=1.6,
            p95_recon_error=0.02,
            cond_evt_only_day_ratio=0.4,
            ae_mid_or_hi_early_day_ratio=0.2,
        ),
        feature_row(
            "alpha",
            "recover.panel",
            "2025-01-03",
            "2025-01-04",
            2,
            "short_alert_run",
            max_v_drop=0.45,
            min_mid_v_ratio=0.55,
            min_mid_ratio=0.55,
            mean_signal_count=1.0,
            max_signal_count=1.0,
            p95_recon_error=0.03,
            cond_evt_only_day_ratio=0.3,
            ae_mid_or_hi_early_day_ratio=0.2,
        ),
        feature_row(
            "alpha",
            "hist.panel",
            "2024-12-01",
            "2024-12-01",
            1,
            "short_alert_run",
            max_v_drop=0.10,
            min_mid_v_ratio=0.90,
            min_mid_ratio=0.90,
            mean_signal_count=1.0,
            max_signal_count=1.0,
            p95_recon_error=0.01,
            cond_evt_only_day_ratio=0.1,
            ae_mid_or_hi_early_day_ratio=0.1,
        ),
        feature_row(
            "alpha",
            "hist2.panel",
            "2024-11-20",
            "2024-11-20",
            1,
            "short_alert_run",
            max_v_drop=0.08,
            min_mid_v_ratio=0.92,
            min_mid_ratio=0.92,
            mean_signal_count=1.0,
            max_signal_count=1.0,
            p95_recon_error=0.01,
            cond_evt_only_day_ratio=0.1,
            ae_mid_or_hi_early_day_ratio=0.1,
        ),
        feature_row(
            "beta",
            "beta.pos.train",
            "2024-12-01",
            "2024-12-02",
            2,
            "medium_alert_run",
            max_v_drop=0.85,
            min_mid_v_ratio=0.30,
            min_mid_ratio=0.30,
            mean_signal_count=1.4,
            max_signal_count=1.8,
            p95_recon_error=0.02,
            cond_evt_only_day_ratio=0.2,
            ae_mid_or_hi_early_day_ratio=0.1,
        ),
        feature_row(
            "beta",
            "beta.neg.train",
            "2024-11-01",
            "2024-11-01",
            1,
            "short_alert_run",
            max_v_drop=0.15,
            min_mid_v_ratio=0.88,
            min_mid_ratio=0.88,
            mean_signal_count=1.0,
            max_signal_count=1.0,
            p95_recon_error=0.01,
            cond_evt_only_day_ratio=0.1,
            ae_mid_or_hi_early_day_ratio=0.8,
        ),
        feature_row(
            "beta",
            "beta.hidden.panel",
            "2025-01-01",
            "2025-01-02",
            2,
            "medium_alert_run",
            max_v_drop=0.80,
            min_mid_v_ratio=0.35,
            min_mid_ratio=0.35,
            mean_signal_count=1.3,
            max_signal_count=1.7,
            p95_recon_error=0.02,
            cond_evt_only_day_ratio=0.3,
            ae_mid_or_hi_early_day_ratio=0.1,
        ),
        feature_row(
            "beta",
            "beta.latest.panel",
            "2025-01-10",
            "2025-01-10",
            1,
            "short_alert_run",
            max_v_drop=0.05,
            min_mid_v_ratio=0.95,
            min_mid_ratio=0.95,
            mean_signal_count=1.0,
            max_signal_count=1.0,
            p95_recon_error=0.01,
            cond_evt_only_day_ratio=0.1,
            ae_mid_or_hi_early_day_ratio=0.1,
        ),
    ]
    scores = [
        score_row(features[0], 10.0),
        score_row(features[1], 9.0),
        score_row(features[2], 6.0),
        score_row(features[3], 1.0),
        score_row(features[4], 0.5),
        score_row(features[5], 9.0),
        score_row(features[6], 2.0),
        score_row(features[7], 8.5),
        score_row(features[8], 0.1),
    ]

    label_pack_v3_rows = [
        {
            "site": feature["site"],
            "panel_id": feature["panel_id"],
            "run_start_date": feature["run_start_date"],
            "run_end_date": feature["run_end_date"],
            "label_bucket_v3": "unlabeled_other",
            "training_label_v3": "exclude",
        }
        for feature in features
    ]
    for row in label_pack_v3_rows:
        if row["panel_id"] == "beta.pos.train":
            row["label_bucket_v3"] = "positive_like"
            row["training_label_v3"] = "positive"
        elif row["panel_id"] == "beta.neg.train":
            row["label_bucket_v3"] = "negative_like"
            row["training_label_v3"] = "negative"

    fate_case_rows = [
        {
            "site": "beta",
            "panel_id": "beta.hidden.panel",
            "run_start_date": "2025-01-01",
            "run_end_date": "2025-01-02",
            "discovery_fate_class": "future_fault_linked",
        },
        {
            "site": "beta",
            "panel_id": "beta.latest.panel",
            "run_start_date": "2025-01-10",
            "run_end_date": "2025-01-10",
            "discovery_fate_class": "recurring_monitor_like",
        },
    ]

    write_csv(root / "_share" / "panel_day_engine_run_feature_table_v1.csv", features, FEATURE_COLS)
    write_csv(root / "_share" / "panel_day_engine_run_ranker_v0_scores.csv", scores, V0_SCORE_COLS)
    write_csv(root / "_share" / "panel_day_engine_run_label_pack_v3_intersection.csv", label_pack_v3_rows, LABEL_PACK_V3_COLS)
    write_csv(
        root / "_share" / "panel_day_engine_run_ranker_complement_recommendation_v1.csv",
        [
            {
                "recommended_next_direction": "use_logistic_as_secondary_discovery_lane",
                "rationale_ko": "fixture guardrail allow",
            }
        ],
        COMPLEMENT_RECOMMENDATION_COLS,
    )
    write_csv(
        root / "_share" / "panel_day_engine_operator_secondary_discovery_threshold_split_recommendation_v1.csv",
        [
            {
                "recommended_split_rule": "electrical_only|electrical_core_minus_broadshape_050>=8",
                "recommended_next_direction": "split_secondary_discovery_into_value_vs_monitor",
                "rationale_ko": "fixture split allow",
            }
        ],
        THRESHOLD_SPLIT_RECOMMENDATION_COLS,
    )
    write_csv(
        root / "_share" / "panel_day_engine_operator_discovery_preview_policy_recommendation_v1.csv",
        [
            {
                "recommended_policy_name": "score_threshold|representative_electrical_core_minus_broadshape_050>=8",
            }
        ],
        PREVIEW_POLICY_RECOMMENDATION_COLS,
    )
    write_csv(
        root / "_share" / "panel_day_engine_operator_attention_policy_recommendation_v1.csv",
        [
            {
                "recommended_policy_name": "baseline_plus_discovery_cluster",
                "recommended_policy_reason_ko": "fixture default workflow",
                "expected_use_ko": "fixture workflow",
                "caution_ko": "fixture only",
            }
        ],
        ATTENTION_POLICY_RECOMMENDATION_COLS,
    )
    write_csv(
        root / "_share" / "panel_day_engine_operator_secondary_discovery_fate_cases_v1.csv",
        fate_case_rows,
        FATE_CASES_COLS,
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_path = repo_root / "research/prognostics/build_panel_day_engine_operator_baseline_v1.py"
    build_module = load_module(build_path, "operator_baseline_build")

    assert_true(
        build_module.BUILDER_SEQUENCE
        == [
            "research/prognostics/build_panel_day_engine_operator_run_consolidation_v1.py",
            "research/prognostics/build_panel_day_engine_operator_attention_delta_v1.py",
            "research/prognostics/build_panel_day_engine_operator_digest_v1.py",
            "research/prognostics/build_panel_day_engine_operator_secondary_discovery_v1.py",
            "research/prognostics/build_panel_day_engine_operator_secondary_discovery_cluster_rollup_v1.py",
            "research/prognostics/build_panel_day_engine_operator_attention_plus_discovery_preview_v1.py",
            "research/prognostics/build_panel_day_engine_operator_secondary_discovery_cluster_delta_v1.py",
            "research/prognostics/build_panel_day_engine_operator_unified_digest_v1.py",
        ],
        "orchestrator should keep baseline builders plus discovery preview, cluster delta, and unified digest builders in order",
    )

    with tempfile.TemporaryDirectory(prefix="operator_baseline_order_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        (tmp_root / "_share").mkdir(parents=True, exist_ok=True)
        recorded_calls: list[str] = []
        original_parse_args = build_module.parse_args
        original_run_builder = build_module.run_builder
        original_build_manifest_and_summary = build_module.build_manifest_and_summary

        def fake_run_builder(repo_root_arg: Path, root_arg: Path, script_relative_path: str) -> None:
            recorded_calls.append(script_relative_path)
            share_dir = root_arg / "_share"
            share_dir.mkdir(parents=True, exist_ok=True)
            if script_relative_path == build_module.DIGEST_SCRIPT:
                pd.DataFrame(
                    [
                        {
                            "record_type": "overall",
                            "site": "",
                            "attention_count": 1,
                            "changed_attention_count": 1,
                            "queue_run_count": 1,
                            "watch_now_panel_count": 0,
                            "new_attention_count": 1,
                            "dropped_attention_count": 0,
                            "attention_class_changed_count": 0,
                            "status_or_tier_changed_count": 0,
                            "priority_changed_count": 0,
                            "score_shifted_count": 0,
                            "metadata_changed_count": 0,
                            "generated_at_utc": "2026-01-01T00:00:00Z",
                        }
                    ]
                ).to_csv(share_dir / build_module.DIGEST_SUMMARY_NAME, index=False, encoding="utf-8-sig")
            elif script_relative_path == build_module.SECONDARY_DISCOVERY_SCRIPT:
                pd.DataFrame(
                    [{"record_type": "overall", "site": "", "value_panel_count": 1}]
                ).to_csv(
                    share_dir / build_module.DISCOVERY_VALUE_PANELS_SUMMARY_NAME,
                    index=False,
                    encoding="utf-8-sig",
                )
            elif script_relative_path == build_module.SECONDARY_DISCOVERY_CLUSTER_ROLLUP_SCRIPT:
                pd.DataFrame(
                    [{"record_type": "overall", "site": "", "cluster_count": 1}]
                ).to_csv(
                    share_dir / build_module.DISCOVERY_CLUSTER_ROLLUP_SUMMARY_NAME,
                    index=False,
                    encoding="utf-8-sig",
                )
            elif script_relative_path == build_module.ATTENTION_PLUS_DISCOVERY_PREVIEW_SCRIPT:
                pd.DataFrame(
                    [
                        {
                            "record_type": "overall",
                            "site": "",
                            "cluster_preview_count": 2,
                            "secondary_value_cluster_count": 1,
                            "clusters_with_future_fault_linked_ref_count": 1,
                            "clusters_with_future_truth_linked_ref_count": 0,
                        }
                    ]
                ).to_csv(
                    share_dir / build_module.DISCOVERY_CLUSTER_PREVIEW_SUMMARY_NAME,
                    index=False,
                    encoding="utf-8-sig",
                )
            elif script_relative_path == build_module.SECONDARY_DISCOVERY_CLUSTER_DELTA_SCRIPT:
                pd.DataFrame(
                    [
                        {
                            "record_type": "overall",
                            "site": "",
                            "current_cluster_count": 1,
                            "changed_cluster_count": 1,
                            "new_cluster_count": 1,
                            "dropped_cluster_count": 0,
                            "representative_changed_count": 0,
                            "linked_ref_changed_count": 0,
                        }
                    ]
                ).to_csv(
                    share_dir / build_module.DISCOVERY_CLUSTER_DELTA_SUMMARY_NAME,
                    index=False,
                    encoding="utf-8-sig",
                )
            elif script_relative_path == build_module.UNIFIED_DIGEST_SCRIPT:
                pd.DataFrame(
                    [
                        {
                            "record_type": "overall",
                            "site": "",
                            "digest_count": 2,
                            "queue_run_count": 1,
                            "watch_now_panel_count": 0,
                            "secondary_value_cluster_count": 1,
                            "changed_count": 1,
                            "changed_attention_count": 0,
                            "changed_cluster_count": 1,
                            "changed_queue_run_count": 0,
                            "changed_watch_now_panel_count": 0,
                            "changed_secondary_value_cluster_count": 1,
                            "note_ko": "fixture unified digest",
                        }
                    ]
                ).to_csv(
                    share_dir / build_module.UNIFIED_DIGEST_SUMMARY_NAME,
                    index=False,
                    encoding="utf-8-sig",
                )
                pd.DataFrame(
                    [
                        {
                            "record_type": "overall",
                            "site": "",
                            "workflow_policy_name": "baseline_plus_discovery_cluster",
                            "workflow_item_count": 2,
                            "queue_run_count": 1,
                            "watch_now_panel_count": 0,
                            "secondary_value_cluster_count": 1,
                            "changed_count": 1,
                            "primary_attention_count": 1,
                            "supplemental_discovery_count": 1,
                            "linked_ref_count": 1,
                            "truth_ref_count": 0,
                            "note_ko": "fixture workflow default",
                        }
                    ]
                ).to_csv(
                    share_dir / build_module.WORKFLOW_DEFAULT_SUMMARY_NAME,
                    index=False,
                    encoding="utf-8-sig",
                )

        def fake_build_manifest_and_summary(
            root: Path,
            generated_at_utc: str,
            *,
            digest_summary: pd.DataFrame | None = None,
            discovery_value_panels_summary: pd.DataFrame | None = None,
            discovery_cluster_rollup_summary: pd.DataFrame | None = None,
            discovery_cluster_preview_summary: pd.DataFrame | None = None,
            discovery_cluster_delta_summary: pd.DataFrame | None = None,
            unified_digest_summary: pd.DataFrame | None = None,
            workflow_default_summary: pd.DataFrame | None = None,
        ) -> tuple[pd.DataFrame, pd.DataFrame]:
            manifest_row = {col: 0 for col in build_module.MANIFEST_OUTPUT_COLS}
            manifest_row["generated_at_utc"] = generated_at_utc
            manifest = pd.DataFrame(
                [
                    manifest_row
                ]
            )
            summary = pd.DataFrame(
                [
                    {
                        "record_type": "overall",
                        "site": "",
                        **{col: 0 for col in build_module.SUMMARY_OUTPUT_COLS if col not in {"record_type", "site"}},
                    }
                ],
                columns=build_module.SUMMARY_OUTPUT_COLS,
            )
            return manifest.loc[:, build_module.MANIFEST_OUTPUT_COLS], summary.loc[:, build_module.SUMMARY_OUTPUT_COLS]

        try:
            build_module.parse_args = lambda: SimpleNamespace(root=tmp_root)
            build_module.run_builder = fake_run_builder
            build_module.build_manifest_and_summary = fake_build_manifest_and_summary
            build_module.main()
        finally:
            build_module.parse_args = original_parse_args
            build_module.run_builder = original_run_builder
            build_module.build_manifest_and_summary = original_build_manifest_and_summary

        assert_true(
            recorded_calls == build_module.BUILDER_SEQUENCE,
            f"orchestrator should call builders in order, got: {recorded_calls}",
        )

    official_paths = [
        repo_root / "_share" / "panel_day_engine_operator_baseline_manifest_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_baseline_summary_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_attention_now_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_attention_now_v1_previous.csv",
        repo_root / "_share" / "panel_day_engine_operator_attention_delta_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_attention_delta_summary_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_digest_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_digest_summary_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_secondary_discovery_cluster_rollup_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_secondary_discovery_cluster_rollup_v1_previous.csv",
        repo_root / "_share" / "panel_day_engine_operator_secondary_discovery_cluster_delta_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_secondary_discovery_cluster_delta_summary_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_attention_plus_discovery_cluster_preview_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_attention_plus_discovery_cluster_preview_summary_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_unified_digest_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_unified_digest_summary_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_workflow_default_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_workflow_default_summary_v1.csv",
    ]
    official_bytes = {path: path.read_bytes() for path in official_paths if path.exists()}

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/prognostics/build_panel_day_engine_operator_baseline_v1.py",
            "research/prognostics/smoke_test_panel_day_engine_operator_baseline_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="operator_baseline_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        build_result = run(
            [
                sys.executable,
                "research/prognostics/build_panel_day_engine_operator_baseline_v1.py",
                "--root",
                str(tmp_root),
            ],
            repo_root,
        )
        assert_true(build_result.returncode == 0, build_result.stderr)

        share_dir = tmp_root / "_share"
        manifest_path = share_dir / "panel_day_engine_operator_baseline_manifest_v1.csv"
        summary_path = share_dir / "panel_day_engine_operator_baseline_summary_v1.csv"
        previous_snapshot_path = share_dir / "panel_day_engine_operator_attention_now_v1_previous.csv"
        cluster_current_path = share_dir / "panel_day_engine_operator_secondary_discovery_cluster_rollup_v1.csv"
        cluster_previous_path = share_dir / "panel_day_engine_operator_secondary_discovery_cluster_rollup_v1_previous.csv"

        assert_true(manifest_path.exists(), "baseline manifest should be generated")
        assert_true(summary_path.exists(), "baseline summary should be generated")
        assert_true(previous_snapshot_path.exists(), "first-run bootstrap should still write previous snapshot")
        assert_true(cluster_previous_path.exists(), "cluster delta bootstrap should still write previous cluster snapshot")

        manifest = pd.read_csv(manifest_path, encoding="utf-8-sig")
        summary = pd.read_csv(summary_path, encoding="utf-8-sig")
        attention_now = pd.read_csv(share_dir / "panel_day_engine_operator_attention_now_v1.csv", encoding="utf-8-sig")
        attention_delta = pd.read_csv(share_dir / "panel_day_engine_operator_attention_delta_v1.csv", encoding="utf-8-sig")
        delta_summary = pd.read_csv(share_dir / "panel_day_engine_operator_attention_delta_summary_v1.csv", encoding="utf-8-sig")
        digest = pd.read_csv(share_dir / "panel_day_engine_operator_digest_v1.csv", encoding="utf-8-sig")
        digest_summary = pd.read_csv(share_dir / "panel_day_engine_operator_digest_summary_v1.csv", encoding="utf-8-sig")
        discovery_value_panels_summary = pd.read_csv(
            share_dir / "panel_day_engine_operator_secondary_discovery_value_panels_summary_v1.csv",
            encoding="utf-8-sig",
        )
        discovery_cluster_rollup_summary = pd.read_csv(
            share_dir / "panel_day_engine_operator_secondary_discovery_cluster_rollup_summary_v1.csv",
            encoding="utf-8-sig",
        )
        discovery_cluster_preview_summary = pd.read_csv(
            share_dir / "panel_day_engine_operator_attention_plus_discovery_cluster_preview_summary_v1.csv",
            encoding="utf-8-sig",
        )
        discovery_cluster_delta_summary = pd.read_csv(
            share_dir / "panel_day_engine_operator_secondary_discovery_cluster_delta_summary_v1.csv",
            encoding="utf-8-sig",
        )
        unified_digest = pd.read_csv(share_dir / "panel_day_engine_operator_unified_digest_v1.csv", encoding="utf-8-sig")
        unified_digest_summary = pd.read_csv(
            share_dir / "panel_day_engine_operator_unified_digest_summary_v1.csv",
            encoding="utf-8-sig",
        )
        workflow_default_summary = pd.read_csv(
            share_dir / "panel_day_engine_operator_workflow_default_summary_v1.csv",
            encoding="utf-8-sig",
        )

        assert_true(len(manifest) == 1, "manifest should emit one row")
        manifest_row = manifest.iloc[0]
        overall_summary = summary.loc[summary["record_type"].astype(str).eq("overall")].iloc[0]
        overall_delta = delta_summary.loc[delta_summary["record_type"].astype(str).eq("overall")].iloc[0]
        overall_digest = digest_summary.loc[digest_summary["record_type"].astype(str).eq("overall")].iloc[0]

        assert_true(bool(str(manifest_row["generated_at_utc"]).strip()), "manifest should include generated_at_utc")
        assert_true(int(manifest_row["attention_count"]) == 2, "manifest attention_count mismatch")
        assert_true(int(manifest_row["queue_count"]) == 1, "manifest queue_count mismatch")
        assert_true(int(manifest_row["backlog_count"]) == 2, "manifest backlog_count mismatch")
        assert_true(int(manifest_row["watchlist_count"]) == 1, "manifest watchlist_count mismatch")
        assert_true(int(manifest_row["watch_now_count"]) == 1, "manifest watch_now_count mismatch")
        assert_true(int(manifest_row["watch_review_count"]) == 0, "manifest watch_review_count mismatch")
        assert_true(int(manifest_row["attention_delta_count"]) == 2, "manifest attention_delta_count mismatch")
        assert_true(int(manifest_row["new_attention_count"]) == 2, "manifest new_attention_count mismatch")
        assert_true(int(manifest_row["dropped_attention_count"]) == 0, "manifest dropped_attention_count mismatch")
        assert_true(int(manifest_row["total_changed_count"]) == 2, "manifest total_changed_count mismatch")
        assert_true(int(manifest_row["digest_attention_count"]) == 2, "manifest digest_attention_count mismatch")
        assert_true(
            int(manifest_row["digest_changed_attention_count"]) == 2,
            "manifest digest_changed_attention_count mismatch",
        )
        assert_true(int(manifest_row["digest_queue_run_count"]) == 1, "manifest digest_queue_run_count mismatch")
        assert_true(
            int(manifest_row["digest_watch_now_panel_count"]) == 1,
            "manifest digest_watch_now_panel_count mismatch",
        )
        discovery_value_overall = discovery_value_panels_summary.loc[
            discovery_value_panels_summary["record_type"].astype(str).eq("overall")
        ].iloc[0]
        discovery_cluster_overall = discovery_cluster_rollup_summary.loc[
            discovery_cluster_rollup_summary["record_type"].astype(str).eq("overall")
        ].iloc[0]
        cluster_preview_overall = discovery_cluster_preview_summary.loc[
            discovery_cluster_preview_summary["record_type"].astype(str).eq("overall")
        ].iloc[0]
        cluster_delta_overall = discovery_cluster_delta_summary.loc[
            discovery_cluster_delta_summary["record_type"].astype(str).eq("overall")
        ].iloc[0]
        unified_digest_overall = unified_digest_summary.loc[
            unified_digest_summary["record_type"].astype(str).eq("overall")
        ].iloc[0]
        workflow_default_overall = workflow_default_summary.loc[
            workflow_default_summary["record_type"].astype(str).eq("overall")
        ].iloc[0]
        assert_true(
            int(manifest_row["discovery_value_panel_count"]) == int(discovery_value_overall["value_panel_count"]),
            "manifest discovery_value_panel_count mismatch",
        )
        assert_true(
            int(manifest_row["discovery_cluster_count"]) == int(discovery_cluster_overall["cluster_count"]),
            "manifest discovery_cluster_count mismatch",
        )
        assert_true(
            int(manifest_row["cluster_preview_count"]) == int(cluster_preview_overall["cluster_preview_count"]),
            "manifest cluster_preview_count mismatch",
        )
        assert_true(
            int(manifest_row["cluster_preview_secondary_value_cluster_count"])
            == int(cluster_preview_overall["secondary_value_cluster_count"]),
            "manifest cluster_preview_secondary_value_cluster_count mismatch",
        )
        assert_true(
            int(manifest_row["cluster_preview_future_fault_linked_ref_count"])
            == int(cluster_preview_overall["clusters_with_future_fault_linked_ref_count"]),
            "manifest cluster_preview_future_fault_linked_ref_count mismatch",
        )
        assert_true(
            int(manifest_row["cluster_preview_future_truth_linked_ref_count"])
            == int(cluster_preview_overall["clusters_with_future_truth_linked_ref_count"]),
            "manifest cluster_preview_future_truth_linked_ref_count mismatch",
        )
        assert_true(
            int(manifest_row["cluster_delta_current_count"]) == int(cluster_delta_overall["current_cluster_count"]),
            "manifest cluster_delta_current_count mismatch",
        )
        assert_true(
            int(manifest_row["cluster_delta_changed_count"]) == int(cluster_delta_overall["changed_cluster_count"]),
            "manifest cluster_delta_changed_count mismatch",
        )
        assert_true(
            int(manifest_row["cluster_delta_new_count"]) == int(cluster_delta_overall["new_cluster_count"]),
            "manifest cluster_delta_new_count mismatch",
        )
        assert_true(
            int(manifest_row["cluster_delta_dropped_count"]) == int(cluster_delta_overall["dropped_cluster_count"]),
            "manifest cluster_delta_dropped_count mismatch",
        )
        assert_true(
            int(manifest_row["cluster_delta_representative_changed_count"])
            == int(cluster_delta_overall["representative_changed_count"]),
            "manifest cluster_delta_representative_changed_count mismatch",
        )
        assert_true(
            int(manifest_row["cluster_delta_linked_ref_changed_count"])
            == int(cluster_delta_overall["linked_ref_changed_count"]),
            "manifest cluster_delta_linked_ref_changed_count mismatch",
        )
        assert_true(
            int(manifest_row["unified_digest_count"]) == int(unified_digest_overall["digest_count"]),
            "manifest unified_digest_count mismatch",
        )
        assert_true(
            int(manifest_row["unified_digest_queue_run_count"]) == int(unified_digest_overall["queue_run_count"]),
            "manifest unified_digest_queue_run_count mismatch",
        )
        assert_true(
            int(manifest_row["unified_digest_watch_now_panel_count"])
            == int(unified_digest_overall["watch_now_panel_count"]),
            "manifest unified_digest_watch_now_panel_count mismatch",
        )
        assert_true(
            int(manifest_row["unified_digest_secondary_value_cluster_count"])
            == int(unified_digest_overall["secondary_value_cluster_count"]),
            "manifest unified_digest_secondary_value_cluster_count mismatch",
        )
        assert_true(
            int(manifest_row["unified_digest_changed_count"]) == int(unified_digest_overall["changed_count"]),
            "manifest unified_digest_changed_count mismatch",
        )
        assert_true(
            int(manifest_row["unified_digest_changed_attention_count"])
            == int(unified_digest_overall["changed_attention_count"]),
            "manifest unified_digest_changed_attention_count mismatch",
        )
        assert_true(
            int(manifest_row["unified_digest_changed_cluster_count"])
            == int(unified_digest_overall["changed_cluster_count"]),
            "manifest unified_digest_changed_cluster_count mismatch",
        )
        assert_true(
            int(manifest_row["workflow_default_item_count"]) == int(workflow_default_overall["workflow_item_count"]),
            "manifest workflow_default_item_count mismatch",
        )
        assert_true(
            int(manifest_row["workflow_default_queue_run_count"]) == int(workflow_default_overall["queue_run_count"]),
            "manifest workflow_default_queue_run_count mismatch",
        )
        assert_true(
            int(manifest_row["workflow_default_watch_now_panel_count"])
            == int(workflow_default_overall["watch_now_panel_count"]),
            "manifest workflow_default_watch_now_panel_count mismatch",
        )
        assert_true(
            int(manifest_row["workflow_default_secondary_value_cluster_count"])
            == int(workflow_default_overall["secondary_value_cluster_count"]),
            "manifest workflow_default_secondary_value_cluster_count mismatch",
        )
        assert_true(
            int(manifest_row["workflow_default_changed_count"]) == int(workflow_default_overall["changed_count"]),
            "manifest workflow_default_changed_count mismatch",
        )
        assert_true(
            int(manifest_row["workflow_default_primary_attention_count"])
            == int(workflow_default_overall["primary_attention_count"]),
            "manifest workflow_default_primary_attention_count mismatch",
        )
        assert_true(
            int(manifest_row["workflow_default_supplemental_discovery_count"])
            == int(workflow_default_overall["supplemental_discovery_count"]),
            "manifest workflow_default_supplemental_discovery_count mismatch",
        )
        assert_true(
            int(manifest_row["workflow_default_linked_ref_count"])
            == int(workflow_default_overall["linked_ref_count"]),
            "manifest workflow_default_linked_ref_count mismatch",
        )
        assert_true(
            int(manifest_row["workflow_default_truth_ref_count"])
            == int(workflow_default_overall["truth_ref_count"]),
            "manifest workflow_default_truth_ref_count mismatch",
        )

        assert_true(int(overall_summary["attention_count"]) == 2, "summary attention_count mismatch")
        assert_true(int(overall_summary["queue_count"]) == 1, "summary queue_count mismatch")
        assert_true(int(overall_summary["backlog_count"]) == 2, "summary backlog_count mismatch")
        assert_true(int(overall_summary["watchlist_count"]) == 1, "summary watchlist_count mismatch")
        assert_true(int(overall_summary["watch_now_count"]) == 1, "summary watch_now_count mismatch")
        assert_true(int(overall_summary["watch_review_count"]) == 0, "summary watch_review_count mismatch")
        assert_true(int(overall_summary["new_attention_count"]) == 2, "summary new_attention_count mismatch")
        assert_true(int(overall_summary["dropped_attention_count"]) == 0, "summary dropped_attention_count mismatch")
        assert_true(int(overall_summary["total_changed_count"]) == 2, "summary total_changed_count mismatch")
        assert_true(
            int(overall_summary["digest_changed_attention_count"]) == 2,
            "summary digest_changed_attention_count mismatch",
        )
        assert_true(
            int(overall_summary["digest_queue_run_count"]) == 1,
            "summary digest_queue_run_count mismatch",
        )
        assert_true(
            int(overall_summary["digest_watch_now_panel_count"]) == 1,
            "summary digest_watch_now_panel_count mismatch",
        )
        assert_true(
            int(overall_summary["discovery_value_panel_count"]) == int(discovery_value_overall["value_panel_count"]),
            "summary discovery_value_panel_count mismatch",
        )
        assert_true(
            int(overall_summary["discovery_cluster_count"]) == int(discovery_cluster_overall["cluster_count"]),
            "summary discovery_cluster_count mismatch",
        )
        assert_true(
            int(overall_summary["cluster_preview_count"]) == int(cluster_preview_overall["cluster_preview_count"]),
            "summary cluster_preview_count mismatch",
        )
        assert_true(
            int(overall_summary["cluster_preview_secondary_value_cluster_count"])
            == int(cluster_preview_overall["secondary_value_cluster_count"]),
            "summary cluster_preview_secondary_value_cluster_count mismatch",
        )
        assert_true(
            int(overall_summary["cluster_delta_current_count"]) == int(cluster_delta_overall["current_cluster_count"]),
            "summary cluster_delta_current_count mismatch",
        )
        assert_true(
            int(overall_summary["cluster_delta_changed_count"]) == int(cluster_delta_overall["changed_cluster_count"]),
            "summary cluster_delta_changed_count mismatch",
        )
        assert_true(
            int(overall_summary["cluster_delta_new_count"]) == int(cluster_delta_overall["new_cluster_count"]),
            "summary cluster_delta_new_count mismatch",
        )
        assert_true(
            int(overall_summary["cluster_delta_dropped_count"]) == int(cluster_delta_overall["dropped_cluster_count"]),
            "summary cluster_delta_dropped_count mismatch",
        )
        assert_true(
            int(overall_summary["unified_digest_count"]) == int(unified_digest_overall["digest_count"]),
            "summary unified_digest_count mismatch",
        )
        assert_true(
            int(overall_summary["unified_digest_queue_run_count"]) == int(unified_digest_overall["queue_run_count"]),
            "summary unified_digest_queue_run_count mismatch",
        )
        assert_true(
            int(overall_summary["unified_digest_watch_now_panel_count"])
            == int(unified_digest_overall["watch_now_panel_count"]),
            "summary unified_digest_watch_now_panel_count mismatch",
        )
        assert_true(
            int(overall_summary["unified_digest_secondary_value_cluster_count"])
            == int(unified_digest_overall["secondary_value_cluster_count"]),
            "summary unified_digest_secondary_value_cluster_count mismatch",
        )
        assert_true(
            int(overall_summary["unified_digest_changed_count"]) == int(unified_digest_overall["changed_count"]),
            "summary unified_digest_changed_count mismatch",
        )
        assert_true(
            int(overall_summary["workflow_default_item_count"]) == int(workflow_default_overall["workflow_item_count"]),
            "summary workflow_default_item_count mismatch",
        )
        assert_true(
            int(overall_summary["workflow_default_queue_run_count"])
            == int(workflow_default_overall["queue_run_count"]),
            "summary workflow_default_queue_run_count mismatch",
        )
        assert_true(
            int(overall_summary["workflow_default_watch_now_panel_count"])
            == int(workflow_default_overall["watch_now_panel_count"]),
            "summary workflow_default_watch_now_panel_count mismatch",
        )
        assert_true(
            int(overall_summary["workflow_default_secondary_value_cluster_count"])
            == int(workflow_default_overall["secondary_value_cluster_count"]),
            "summary workflow_default_secondary_value_cluster_count mismatch",
        )
        assert_true(
            int(overall_summary["workflow_default_changed_count"]) == int(workflow_default_overall["changed_count"]),
            "summary workflow_default_changed_count mismatch",
        )

        assert_true(int(overall_delta["current_attention_count"]) == len(attention_now), "delta summary should reflect current attention count")
        assert_true(len(attention_delta) == 2, "bootstrap delta should treat all current attention rows as new")
        assert_true(attention_delta["delta_class"].eq("new_attention").all(), "bootstrap delta rows should all be new_attention")
        assert_true(len(digest) == 2, "digest should include one row per current attention item")
        assert_true(
            int(overall_digest["attention_count"]) == len(digest),
            "digest summary should reflect digest row count",
        )
        assert_true(
            int(overall_digest["changed_attention_count"]) == 2,
            "digest summary changed attention count mismatch",
        )
        assert_true(
            int(overall_digest["queue_run_count"]) == 1,
            "digest summary queue_run_count mismatch",
        )
        assert_true(
            int(overall_digest["watch_now_panel_count"]) == 1,
            "digest summary watch_now_panel_count mismatch",
        )
        assert_true(len(unified_digest) == int(unified_digest_overall["digest_count"]), "unified digest count mismatch")
        assert_true(
            int(unified_digest_overall["queue_run_count"])
            + int(unified_digest_overall["watch_now_panel_count"])
            + int(unified_digest_overall["secondary_value_cluster_count"])
            == len(unified_digest),
            "unified digest class counts should sum to digest_count",
        )
        assert_true(
            int(unified_digest_overall["changed_count"]) <= len(unified_digest),
            "unified digest changed_count should not exceed digest_count",
        )
        assert_true(
            int(workflow_default_overall["workflow_item_count"]) == len(unified_digest),
            "workflow default should preserve unified digest row count",
        )
        for workflow_site_row in workflow_default_summary.loc[
            workflow_default_summary["record_type"].astype(str).eq("site")
        ].itertuples():
            summary_site_row = summary.loc[
                summary["record_type"].astype(str).eq("site")
                & summary["site"].astype(str).eq(workflow_site_row.site)
            ]
            assert_true(not summary_site_row.empty, f"baseline summary missing workflow site row: {workflow_site_row.site}")
            summary_site_row = summary_site_row.iloc[0]
            assert_true(
                int(summary_site_row["workflow_default_item_count"]) == int(workflow_site_row.workflow_item_count),
                f"summary workflow_default_item_count mismatch for {workflow_site_row.site}",
            )
            assert_true(
                int(summary_site_row["workflow_default_queue_run_count"]) == int(workflow_site_row.queue_run_count),
                f"summary workflow_default_queue_run_count mismatch for {workflow_site_row.site}",
            )
            assert_true(
                int(summary_site_row["workflow_default_watch_now_panel_count"])
                == int(workflow_site_row.watch_now_panel_count),
                f"summary workflow_default_watch_now_panel_count mismatch for {workflow_site_row.site}",
            )
            assert_true(
                int(summary_site_row["workflow_default_secondary_value_cluster_count"])
                == int(workflow_site_row.secondary_value_cluster_count),
                f"summary workflow_default_secondary_value_cluster_count mismatch for {workflow_site_row.site}",
            )
            assert_true(
                int(summary_site_row["workflow_default_changed_count"]) == int(workflow_site_row.changed_count),
                f"summary workflow_default_changed_count mismatch for {workflow_site_row.site}",
            )

        previous_snapshot = pd.read_csv(previous_snapshot_path, encoding="utf-8-sig")
        previous_cluster_snapshot = pd.read_csv(cluster_previous_path, encoding="utf-8-sig")
        current_cluster_snapshot = pd.read_csv(cluster_current_path, encoding="utf-8-sig")
        assert_true(previous_snapshot.equals(attention_now), "previous snapshot should match current attention after bootstrap")
        assert_true(
            previous_cluster_snapshot.equals(current_cluster_snapshot),
            "previous cluster snapshot should match current cluster rollup after bootstrap",
        )

    for path, previous_bytes in official_bytes.items():
        assert_true(path.read_bytes() == previous_bytes, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()
