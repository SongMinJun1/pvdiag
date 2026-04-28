<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_156_LIVE_TEMP_REFERENCE_REVIEW_V1

## Purpose
- Refine BR-155's broad `p1_live_temp_reference` bucket before changing any builder defaults.
- Keep this as an audit/reporting patch only: no `pv_ae/panel_day_engine.py` behavior change, no production semantic change, and no large data committed.

## Change
- The path portability audit now classifies non-doc `/private/tmp` references into more specific roles:
  - `research_temp_default_reference`
  - `temp_reference_in_research_code`
  - `embedded_repro_command_temp_reference`
  - `embedded_manifest_temp_artifact_reference`
  - `test_fixture_temp_reference`
  - `intentional_temp_path_detection_literal`
- The smoke test now verifies that research smoke-test fixture literals do not get treated as live cleanup defaults.

## Observed Effect
- Current audit total matches: `1936`.
- `private_tmp`: `1334`.
- `repo_absolute`: `602`.
- Non-doc `/private/tmp` research/prognostics split:
  - `research_temp_default_reference`: `113`
  - `temp_reference_in_research_code`: `69`
  - `embedded_repro_command_temp_reference`: `50`
  - `embedded_manifest_temp_artifact_reference`: `12`
  - `test_fixture_temp_reference`: `5`
  - `intentional_temp_path_detection_literal`: `1`
- Practical cleanup target is now narrowed to `182` active-review rows:
  - `113` explicit temp defaults.
  - `69` unresolved research-code temp references.

## Interpretation
- Do not treat every non-doc `/private/tmp` reference as equally dangerous.
- `research_temp_default_reference` is the highest next cleanup class because deleted `/private/tmp` artifacts can break default script execution.
- `embedded_repro_command_temp_reference` and `embedded_manifest_temp_artifact_reference` should be preserved until those historical manifests are rebuilt with stable artifact paths.
- `test_fixture_temp_reference` and `intentional_temp_path_detection_literal` are not cleanup targets unless they mask a real live default.

## Repro Commands
```bash
git status --short --branch
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_repo_path_portability_audit_v1.py research/prognostics/smoke_test_repo_path_portability_audit_v1.py
python3 research/prognostics/smoke_test_repo_path_portability_audit_v1.py
python3 research/prognostics/build_repo_path_portability_audit_v1.py --repo-root "$(pwd)" --output-dir /private/tmp/pvdiag_repo_path_portability_live_temp_review_check_v2
python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
git diff --check
```

## Decision
- Next patch candidate: inspect the `research_temp_default_reference` class first and decide which scripts should require explicit inputs versus derive stable repo-relative defaults.
- Do not edit historical manifest/repro strings in bulk.
