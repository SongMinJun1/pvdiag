<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_157_TEMP_DEFAULT_PRIORITY_SPLIT_V1

## Purpose
- Refine BR-156's broad temp-default class before changing any builder defaults.
- Keep this as an audit/reporting patch only: no `pv_ae/panel_day_engine.py` behavior change, no production semantic change, and no large data committed.

## Change
- The path portability audit now splits temp-root defaults into:
  - `research_temp_input_artifact_default_reference`
  - `research_temp_directory_default_reference`
  - `research_temp_output_default_reference`
  - `research_temp_cli_default_reference`
- The smoke test now verifies that temp input defaults and temp output defaults are classified separately.

## Observed Effect
- Current audit total matches: `1937`.
- `private_tmp`: `1335`.
- `repo_absolute`: `602`.
- Non-doc temp-root research/prognostics split:
  - `temp_reference_in_research_code`: `69`
  - `research_temp_input_artifact_default_reference`: `53`
  - `embedded_repro_command_temp_reference`: `50`
  - `research_temp_output_default_reference`: `47`
  - `embedded_manifest_temp_artifact_reference`: `12`
  - `research_temp_cli_default_reference`: `10`
  - `test_fixture_temp_reference`: `6`
  - `research_temp_directory_default_reference`: `3`
  - `intentional_temp_path_detection_literal`: `1`
- The generic `research_temp_default_reference` bucket is now `0`.

## Interpretation
- The highest next cleanup class is `p1_temp_input_default_reference`: `56` rows, made of `53` direct input artifacts and `3` directory defaults.
- Output defaults are lower risk because they can usually be regenerated, but they should eventually move to explicit CLI output dirs for reproducibility.
- `p1_live_temp_reference` still has `69` unresolved research-code references and should be inspected after input defaults.

## Repro Commands
```bash
git status --short --branch
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_repo_path_portability_audit_v1.py research/prognostics/smoke_test_repo_path_portability_audit_v1.py
python3 research/prognostics/smoke_test_repo_path_portability_audit_v1.py
python3 research/prognostics/build_repo_path_portability_audit_v1.py --repo-root "$(pwd)" --output-dir "${TMPDIR:-/tmp}/pvdiag_repo_path_portability_temp_default_priority_check_v3"
python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
git diff --check
```

## Decision
- Next patch candidate: inspect `p1_temp_input_default_reference` first.
- Do not change output defaults, embedded repro commands, embedded manifests, or fixtures in bulk.
