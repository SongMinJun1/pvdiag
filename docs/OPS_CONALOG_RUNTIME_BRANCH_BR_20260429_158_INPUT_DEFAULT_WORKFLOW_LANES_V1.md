<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_158_INPUT_DEFAULT_WORKFLOW_LANES_V1

## Purpose
- Refine BR-157's `p1_temp_input_default_reference` rows by workflow lane before changing any defaults.
- Keep this as an audit/reporting patch only: no `pv_ae/panel_day_engine.py` behavior change, no production semantic change, and no large data committed.

## Change
- The path portability detail output now includes `workflow_lane`.
- Summary and JSON outputs now include `workflow_lane` counts.
- The smoke test verifies that MLPE field-trial temp defaults are assigned to the `mlpe_field_trial` workflow lane.

## Observed Effect
- Current audit total matches: `1937`.
- `private_tmp`: `1335`.
- `repo_absolute`: `602`.
- `p1_temp_input_default_reference` workflow split:
  - `mlpe_field_trial`: `48`
  - `panel_engine_voltage_preserved`: `5`
  - `panel_engine_common_cause`: `2`
  - `panel_engine_prepatch_scorecard`: `1`

## Interpretation
- The next cleanup target should be the `mlpe_field_trial` lane first.
- The panel-engine evidence rows are smaller and more sensitive, so they should stay behind a separate review after the MLPE field-trial default contract is settled.
- This patch does not remove or rewrite temp defaults; it only makes the cleanup sequence explicit.

## Repro Commands
```bash
git status --short --branch
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_repo_path_portability_audit_v1.py research/prognostics/smoke_test_repo_path_portability_audit_v1.py
python3 research/prognostics/smoke_test_repo_path_portability_audit_v1.py
python3 research/prognostics/build_repo_path_portability_audit_v1.py --repo-root "$(pwd)" --output-dir "${TMPDIR:-/tmp}/pvdiag_repo_path_portability_input_default_lanes_check_v1"
python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
git diff --check
```

## Decision
- Next patch candidate: define the MLPE field-trial input default contract.
- Do not change panel-engine evidence defaults in the same patch.
