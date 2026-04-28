<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260428_154_RESEARCH_DATA_ROOT_PORTABILITY_V1

## Purpose
- Remove local-machine data-root defaults from research/audit builders.
- Keep this as a portability cleanup only: no panel engine behavior change, no operator-facing semantic change, and no large data committed.

## Change
- Research builders that defaulted to a fixed local checkout data path now derive `data` from the current repository root.
- Handoff/manifest repro command strings now use `--data-root data` instead of a user-specific absolute path.
- Manual/vendor input defaults now resolve to `data/manual/vendor_reply_cases.csv` under the current checkout.

## Observed Effect
- Path portability audit total matches: `1954 -> 1933`.
- `repo_absolute` matches: `624 -> 603`.
- `private_tmp` remains `1330`; those are historical/temp evidence references and need separate triage.

## Repro Commands
```bash
git status --short --branch
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_common_cause_exact_seed_search_v1.py research/prognostics/build_panel_day_engine_common_cause_manual_trace_review_v1.py research/prognostics/build_panel_day_engine_durable_hold_raw_shape_review_v1.py research/prognostics/build_panel_day_engine_episode_truth_durable_shape_review_v1.py research/prognostics/build_panel_day_engine_evidence_manifest_v1.py research/prognostics/build_panel_day_engine_latest_evidence_handoff_manifest_v1.py research/prognostics/build_panel_day_engine_local_morphology_family_shape_review_v1.py research/prognostics/build_panel_day_engine_raw_waveform_physical_support_review_v1.py research/prognostics/build_panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.py research/prognostics/build_panel_day_engine_voltage_preserved_confirmation_gap_review_v1.py research/prognostics/build_panel_day_engine_voltage_preserved_independent_confirmation_attachment_v1.py research/prognostics/build_panel_day_engine_voltage_preserved_positive_search_v1.py research/prognostics/build_panel_day_engine_voltage_preserved_raw_source_attachment_v1.py research/prognostics/check_panel_day_engine_patch_safety_gate_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_common_cause_exact_seed_search_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_common_cause_manual_trace_review_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_durable_hold_raw_shape_review_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_episode_truth_durable_shape_review_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_evidence_manifest_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_latest_evidence_handoff_manifest_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_local_morphology_family_shape_review_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_raw_waveform_physical_support_review_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_voltage_preserved_confirmation_gap_review_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_voltage_preserved_independent_confirmation_attachment_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_voltage_preserved_positive_search_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_voltage_preserved_raw_source_attachment_v1.py
python3 research/prognostics/build_repo_path_portability_audit_v1.py --repo-root "$(pwd)" --output-dir /private/tmp/pvdiag_repo_path_portability_audit_research_data_root_check_v1
python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
git diff --check
```

## Decision
- This patch only removes user-specific data-root assumptions from research/audit helpers.
- Historical docs that cite prior absolute paths are not bulk-rewritten in this branch.
