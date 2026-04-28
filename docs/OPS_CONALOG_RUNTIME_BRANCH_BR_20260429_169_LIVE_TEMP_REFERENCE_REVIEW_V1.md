<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_169_LIVE_TEMP_REFERENCE_REVIEW_V1

## Purpose
- BR-168 closed MLPE output defaults as write-location defaults, not input dependencies.
- BR-169 reviews the broader `p1_live_temp_reference` bucket before any path rewrite.
- The goal is to separate true upstream-evidence inputs from repro strings and detector literals.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not bulk-rewrite `/private/tmp` paths.
- Do not delete or replace evidence pointers without a manifest or explicit-input contract.
- Do not claim diagnosis, truth, threshold, or performance improvement.

## Review Method
- Read the path portability audit rows.
- Filter:
  - `triage_priority = p1_live_temp_reference`
- Emit a dedicated review artifact with:
  - source file,
  - workflow lane,
  - matched temp path,
  - context excerpt,
  - live-reference kind,
  - manifest/explicit-input requirement flag,
  - literal/repro-only flag,
  - rewrite and runtime semantic safety flags.

## Observed Counts
- live temp reference rows: `69`
- requires manifest or explicit input rows: `62`
- literal or repro only rows: `7`
- runtime semantic change allowed rows: `0`
- bulk rewrite allowed rows: `0`

## Kind Split
| live_reference_kind | count | handling |
|---|---:|---|
| `static_upstream_directory_input` | 48 | resolve from manifest or explicit directory input |
| `static_upstream_artifact_input` | 10 | resolve from manifest or explicit artifact input |
| `runtime_result_bundle_input` | 4 | materialize stable result bundle or pass explicit result artifacts |
| `embedded_note_repro_command` | 5 | refresh note/runbook prose when touching the builder |
| `intentional_temp_detection_literal` | 2 | preserve or mark scanner literal if it creates audit noise |

## Workflow Split
| workflow_lane | count |
|---|---:|
| `panel_day_engine_evidence` | 30 |
| `panel_engine_episode_truth` | 14 |
| `panel_engine_common_cause` | 13 |
| `panel_engine_prepatch_scorecard` | 7 |
| `panel_engine_voltage_preserved` | 4 |
| `repo_organization` | 1 |

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_repo_live_temp_reference_review_v1.py \
  research/prognostics/smoke_test_repo_live_temp_reference_review_v1.py

python3 research/prognostics/smoke_test_repo_live_temp_reference_review_v1.py

python3 research/prognostics/build_repo_live_temp_reference_review_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/repo_live_temp_reference_review_br169_check"

python3 research/prognostics/build_repo_path_portability_audit_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/repo_live_temp_reference_review_br169_path_audit_check"

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Output Paths
- `/private/tmp/repo_live_temp_reference_review_br169_check`
- `/private/tmp/repo_live_temp_reference_review_br169_path_audit_check`

## Decision
- The next real cleanup target is the `62` manifest/explicit-input candidates.
- Repro commands and detector literals should not drive algorithm or input-contract changes.
- A safe next branch should pick one workflow lane, likely `panel_engine_episode_truth` or `panel_engine_common_cause`, and introduce a manifest/explicit-input contract instead of rewriting all paths.
