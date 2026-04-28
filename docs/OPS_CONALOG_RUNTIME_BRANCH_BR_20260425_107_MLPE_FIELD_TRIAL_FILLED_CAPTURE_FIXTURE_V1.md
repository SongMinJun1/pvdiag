<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_107_MLPE_FIELD_TRIAL_FILLED_CAPTURE_FIXTURE_V1

## Purpose
- Create a synthetic filled-capture fixture so the BR-103 readiness and BR-106 handoff gates can be dry-run before real 실증 labels exist.
- Prove that complete capture metadata/evidence can move rows to adjudication handoff while truth intake remains blocked.
- Keep this branch fixture-only:
  - no new truth labels
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_filled_capture_fixture_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_filled_capture_fixture_v1.py`

## Outputs
- `/private/tmp/mlpe_field_trial_filled_capture_fixture_br107_check/mlpe_field_trial_filled_capture_fixture_v1.csv`
- `/private/tmp/mlpe_field_trial_filled_capture_fixture_br107_check/mlpe_field_trial_filled_capture_fixture_evidence_manifest_v1.csv`
- `/private/tmp/mlpe_field_trial_filled_capture_fixture_br107_check/mlpe_field_trial_filled_capture_fixture_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_filled_capture_fixture_br107_check/readiness/mlpe_field_trial_capture_readiness_packet_v1.csv`
- `/private/tmp/mlpe_field_trial_filled_capture_fixture_br107_check/intake/mlpe_field_trial_operator_intake_checklist_v1.csv`
- `/private/tmp/mlpe_field_trial_filled_capture_fixture_br107_check/guard/mlpe_field_trial_adjudication_handoff_guard_v1.csv`

## Real Result
- synthetic filled capture rows: `14`
- synthetic evidence rows: `56`
- evidence missing rows: `0`
- BR-103 `capture_ready_label_pending` rows: `14`
- BR-104 adjudication-ready rows: `14`
- BR-106 adjudication handoff allowed rows: `14`
- final label attached rows: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

## Interpretation
- The field-trial plumbing works when metadata and evidence paths are complete.
- The current real/planned rows remain blocked, but the synthetic dry-run confirms the gates are not permanently closed.
- The fixture is not field truth; it only verifies schema/readiness/handoff behavior.

## Safety Boundary
- Synthetic fixture rows must never be merged into truth rows.
- `adjudication_handoff_allowed=1` means final human adjudication can begin, not that truth intake is approved.
- `truth_intake_allowed`, `threshold_patch_allowed`, and `engine_patch_allowed` remain `0`.
- `panel_day_engine.py` remains untouched.

## Ordered Next Path
1. Use this fixture as regression proof for the BR-103/104/106 plumbing.
2. When real capture rows arrive, rerun the same sequence on real data.
3. Open truth intake only after final labels are supplied externally.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_filled_capture_fixture_v1.py research/prognostics/smoke_test_mlpe_field_trial_filled_capture_fixture_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_filled_capture_fixture_v1.py
python3 research/prognostics/build_mlpe_field_trial_filled_capture_fixture_v1.py --repo-root "$(pwd)" --capture-input /private/tmp/mlpe_field_trial_capture_schema_br102_check/mlpe_field_trial_capture_template_v1.csv --output-dir /private/tmp/mlpe_field_trial_filled_capture_fixture_br107_check
python3 research/prognostics/build_mlpe_field_trial_capture_readiness_packet_v1.py --repo-root "$(pwd)" --capture-input /private/tmp/mlpe_field_trial_filled_capture_fixture_br107_check/mlpe_field_trial_filled_capture_fixture_v1.csv --output-dir /private/tmp/mlpe_field_trial_filled_capture_fixture_br107_check/readiness
python3 research/prognostics/build_mlpe_field_trial_package_manifest_v1.py --repo-root "$(pwd)" --schema-dir /private/tmp/mlpe_field_trial_capture_schema_br102_check --readiness-dir /private/tmp/mlpe_field_trial_filled_capture_fixture_br107_check/readiness --intake-dir /private/tmp/mlpe_field_trial_filled_capture_fixture_br107_check/intake --output-dir /private/tmp/mlpe_field_trial_filled_capture_fixture_br107_check/manifest
python3 research/prognostics/build_mlpe_field_trial_adjudication_handoff_guard_v1.py --repo-root "$(pwd)" --readiness-input /private/tmp/mlpe_field_trial_filled_capture_fixture_br107_check/readiness/mlpe_field_trial_capture_readiness_packet_v1.csv --manifest-summary-input /private/tmp/mlpe_field_trial_filled_capture_fixture_br107_check/manifest/mlpe_field_trial_package_manifest_summary_v1.csv --output-dir /private/tmp/mlpe_field_trial_filled_capture_fixture_br107_check/guard
```
