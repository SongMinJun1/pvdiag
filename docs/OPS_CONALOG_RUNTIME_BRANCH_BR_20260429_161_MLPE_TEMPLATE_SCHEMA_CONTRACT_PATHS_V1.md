<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_161_MLPE_TEMPLATE_SCHEMA_CONTRACT_PATHS_V1

## Purpose
- BR-160 made user-filled MLPE defaults fail closed so stale temp templates cannot be consumed silently.
- BR-161 handles the adjacent, safer category: MLPE templates and schemas that are not user evidence but were still defaulting to volatile temp outputs from prior builders.
- The goal is path portability only. This branch does not approve truth intake, threshold changes, engine patches, or panel-day runtime semantic changes.

## Scope
- Move MLPE field-trial template/schema default inputs to repo-tracked contract artifacts under `research/prognostics/contracts/mlpe_field_trial_v1/`.
- Keep user-filled inputs explicit and guarded by BR-160.
- Do not change `pv_ae/panel_day_engine.py`.
- Do not change current panel verdicts, fault labels, thresholds, or production diagnosis behavior.

## Contract Artifacts
- `research/prognostics/contracts/mlpe_field_trial_v1/capture_schema/mlpe_field_trial_capture_template_v1.csv`
- `research/prognostics/contracts/mlpe_field_trial_v1/capture_schema/mlpe_field_trial_capture_schema_v1.csv`
- `research/prognostics/contracts/mlpe_field_trial_v1/capture_schema/mlpe_field_trial_capture_allowed_values_v1.csv`
- `research/prognostics/contracts/mlpe_field_trial_v1/final_label_intake_schema/mlpe_field_trial_final_label_intake_schema_v1.csv`
- `research/prognostics/contracts/mlpe_field_trial_v1/final_label_intake_schema/mlpe_field_trial_final_label_allowed_values_v1.csv`
- `research/prognostics/contracts/mlpe_field_trial_v1/truth_seed_reviewer_decision_schema/mlpe_field_trial_truth_seed_reviewer_decision_schema_v1.csv`
- `research/prognostics/contracts/mlpe_field_trial_v1/truth_seed_reviewer_decision_schema/mlpe_field_trial_truth_seed_reviewer_decision_allowed_values_v1.csv`

## Default Path Changes
- Capture template defaults now point at the tracked capture template for readiness, filled fixture, operator intake, and partial-capture matrix builders.
- Final-label schema and allowed-value defaults now point at the tracked final-label contract files.
- Truth-seed reviewer decision schema and allowed-value defaults now point at the tracked reviewer-decision contract files.
- Final-label input and truth-seed decision input remain user-filled inputs and still require explicit paths unless a fixture/regression override is intentionally used.

## Evidence
- Before BR-161, the path portability audit classified `10` MLPE rows as `mlpe_template_or_schema_input`.
- After BR-161, the same audit classifies `0` rows as `mlpe_template_or_schema_input`.
- Remaining MLPE dependency-contract rows are intentionally separate categories:
  - `mlpe_user_filled_input = 7`
  - `mlpe_upstream_generated_artifact_input = 27`
  - `mlpe_chain_directory_bundle_input = 4`
- This is the intended split: durable contracts are tracked, user-filled evidence is explicit/guarded, and generated chain artifacts remain a later dependency-resolution lane.

## Validation Commands
```bash
python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_mlpe_field_trial_capture_readiness_packet_v1.py \
  research/prognostics/build_mlpe_field_trial_filled_capture_fixture_v1.py \
  research/prognostics/build_mlpe_field_trial_operator_intake_guide_v1.py \
  research/prognostics/build_mlpe_field_trial_partial_capture_failure_matrix_v1.py \
  research/prognostics/build_mlpe_field_trial_final_label_validator_v1.py \
  research/prognostics/build_mlpe_field_trial_real_label_intake_runbook_v1.py \
  research/prognostics/build_mlpe_field_trial_truth_seed_reviewer_decision_validator_v1.py

python3 research/prognostics/build_mlpe_field_trial_capture_readiness_packet_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/pvdiag_mlpe_contract_default_capture_readiness_check_v1"

python3 research/prognostics/build_mlpe_field_trial_filled_capture_fixture_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/pvdiag_mlpe_contract_default_filled_fixture_check_v1"

python3 research/prognostics/build_mlpe_field_trial_partial_capture_failure_matrix_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/pvdiag_mlpe_contract_default_partial_matrix_check_v1"

python3 research/prognostics/build_mlpe_field_trial_operator_intake_guide_v1.py \
  --repo-root "$(pwd)" \
  --readiness-input "${TMPDIR:-/tmp}/pvdiag_mlpe_contract_default_capture_readiness_check_v1/mlpe_field_trial_capture_readiness_packet_v1.csv" \
  --output-dir "${TMPDIR:-/tmp}/pvdiag_mlpe_contract_default_operator_intake_check_v1"

python3 research/prognostics/build_mlpe_field_trial_real_label_intake_runbook_v1.py \
  --repo-root "$(pwd)" \
  --label-input "${TMPDIR:-/tmp}/pvdiag_mlpe_contract_default_label_schema_check_v1/label_input.csv" \
  --output-dir "${TMPDIR:-/tmp}/pvdiag_mlpe_contract_default_real_label_runbook_check_v1"

python3 research/prognostics/smoke_test_mlpe_field_trial_user_filled_default_guard_v1.py

python3 research/prognostics/build_repo_path_portability_audit_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/pvdiag_mlpe_template_schema_contract_check_v1"
```

## Validation Results
- `py_compile` passed for `pv_ae/panel_day_engine.py` and all touched MLPE builder scripts.
- Capture readiness default run passed with `rows = 14`.
- Filled capture fixture default run passed with `rows = 14` and `evidence_rows = 56`.
- Partial capture matrix default run passed with `scenario_rows = 6`, `expected_rows = 6`, and `evidence_rows = 25`.
- Operator intake default run passed with `rows = 14`, `field_guide_rows = 26`, and all approval sums `0`.
- Final-label validator passed against an explicit one-row fixture with `valid_label_rows = 1`, `truth_gate_candidate_rows = 1`, `issue_rows = 0`, and all approval sums `0`.
- Real-label intake runbook passed against the same explicit fixture with `fixture_mismatch_rows = 0`, `valid_label_rows = 1`, `truth_gate_ready_rows = 1`, `truth_seed_review_candidate_rows = 1`, and all approval sums `0`.
- Truth-seed reviewer decision validator passed against an explicit one-row fixture with `valid_decision_rows = 1`, `future_truth_intake_candidate_rows = 1`, `issue_rows = 0`, and all write/patch approval sums `0`.
- User-filled default guard smoke passed and still guards 7 user-filled scripts.
- Path portability audit passed with `mlpe_template_or_schema_input = 0`.

## Decision
- The default contract-path patch is ready for review.
- This branch is a portability and reproducibility improvement, not a diagnosis-performance improvement claim.
- Next cleanup lane should remain bounded: generated upstream artifact defaults and chain-directory bundle inputs require separate dependency-resolution review before any replacement.
