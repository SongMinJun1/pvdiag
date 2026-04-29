# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_215_PREPATCH_SCORECARD_STATIC_DIRECTORY_CONTRACT_GAP_V1

## Summary
- This patch reviews the prepatch scorecard static directory lane after BR-211 through BR-214.
- It confirms that prepatch scorecard is not contract-closed yet.
- It does not rewrite paths, change runtime behavior, change truth/threshold/engine logic, or modify operator-facing outputs.

## Why This Patch Exists
- BR-211 found 4 prepatch scorecard static directory references.
- BR-212 closed episode-truth and BR-214 closed common-cause.
- Prepatch scorecard needed the same closure check before any code patch or default path rewrite.

## Observed Contract State
- Prepatch directory rows: `4`
- Source files: `3`
- Contract closed rows: `0`
- Contract gap rows: `4`
- Explicit CLI argument rows: `4`
- Input-manifest argument rows: `0`
- Manifest resolver rows: `0`
- Missing check count: `8`
- Runtime semantic change allowed rows: `0`
- Bulk rewrite allowed rows: `0`

## Gap Interpretation
- Gap rows already have explicit per-input CLI flags.
- Gap rows still lack:
  - `--input-manifest`
  - manifest resolver handling
- One compare script maps a single retained default scorecard path to two explicit inputs:
  - `baseline_scorecard_summary`
  - `post_scorecard_summary`

## Scope Boundary
- Changed:
  - `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_215_PREPATCH_SCORECARD_STATIC_DIRECTORY_CONTRACT_GAP_V1.md`
  - `research/prognostics/build_prepatch_scorecard_static_directory_contract_gap_v1.py`
  - `research/prognostics/smoke_test_prepatch_scorecard_static_directory_contract_gap_v1.py`
- Not changed:
  - `pv_ae/panel_day_engine.py`
  - prepatch scorecard/runbook/compare behavior
  - truth, threshold, engine, or operator-facing semantics
  - path portability scanner semantics
  - historical evidence pointers

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_prepatch_scorecard_static_directory_contract_gap_v1.py \
  research/prognostics/smoke_test_prepatch_scorecard_static_directory_contract_gap_v1.py

python3 research/prognostics/smoke_test_prepatch_scorecard_static_directory_contract_gap_v1.py

python3 research/prognostics/build_prepatch_scorecard_static_directory_contract_gap_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/prepatch_scorecard_static_directory_contract_gap_br215_check"

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Expected Result
- `prepatch_directory_rows=4`
- `source_file_count=3`
- `contract_closed_rows=0`
- `contract_gap_rows=4`
- `input_manifest_arg_rows=0`
- `manifest_resolver_rows=0`
- `explicit_cli_arg_rows=4`
- `missing_check_count=8`
- `contract_complete=0`

## Next Decision
- Do not bulk-rewrite prepatch scorecard paths yet.
- Next code patch should add `--input-manifest` and manifest resolver handling to the 4 gap rows.
- Keep runtime semantic and bulk rewrite permission at 0.
