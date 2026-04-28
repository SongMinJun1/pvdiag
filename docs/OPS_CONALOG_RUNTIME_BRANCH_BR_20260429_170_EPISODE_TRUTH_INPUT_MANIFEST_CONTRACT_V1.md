<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_170_EPISODE_TRUTH_INPUT_MANIFEST_CONTRACT_V1

## Purpose
- BR-169 split `p1_live_temp_reference` rows into true input candidates and repro/detection literals.
- BR-170 narrows the first follow-up lane to `panel_engine_episode_truth`.
- The goal is to define a manifest/explicit-input contract before changing any existing builder defaults.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not rewrite existing episode-truth builder defaults in this branch.
- Do not delete `/private/tmp` defaults before a manifest resolver or explicit-input path is wired.
- Do not claim diagnosis, truth, threshold, or performance improvement.

## Contract Method
- Reuse the BR-169 live-temp reference review.
- Filter:
  - `workflow_lane = panel_engine_episode_truth`
- Add consumer-level contract fields:
  - consumer script,
  - explicit input flag,
  - upstream stage key,
  - manifest-required flag,
  - literal/repro-only flag,
  - runtime/bulk-rewrite safety flags.

## Observed Counts
- episode-truth reference rows: `14`
- manifest-required rows: `12`
- explicit-input-supported rows: `12`
- literal/repro-only rows: `2`
- runtime semantic change allowed rows: `0`
- bulk rewrite allowed rows: `0`

## Required Consumer Flags
| consumer | flags |
|---|---|
| `build_panel_day_engine_episode_truth_adjudication_worksheet_v1.py` | `--trace-input`, `--index-input` |
| `build_panel_day_engine_episode_truth_conservative_adjudication_v1.py` | `--worksheet-input` |
| `build_panel_day_engine_episode_truth_durable_shape_review_v1.py` | `--br088-input` |
| `build_panel_day_engine_episode_truth_evidence_attachment_v1.py` | `--reviewed-rows-input` |
| `build_panel_day_engine_episode_truth_map_v1.py` | `--shape-input`, `--backlog-input` |
| `build_panel_day_engine_episode_truth_review_packet_v1.py` | `--episode-map-input` |
| `build_panel_day_engine_episode_truth_source_trace_audit_v1.py` | `--index-input`, `--template-input` |
| `build_panel_day_engine_reviewed_episode_truth_rows_v1.py` | `--packet-input`, `--guard-json-input` |

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_episode_truth_input_manifest_contract_v1.py \
  research/prognostics/smoke_test_panel_day_engine_episode_truth_input_manifest_contract_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_episode_truth_input_manifest_contract_v1.py

python3 research/prognostics/build_panel_day_engine_episode_truth_input_manifest_contract_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/panel_day_engine_episode_truth_input_manifest_contract_br170_check"

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Output Paths
- `/private/tmp/panel_day_engine_episode_truth_input_manifest_contract_br170_check`

## Decision
- BR-170 is a contract patch, not an execution rewrite.
- The next safe branch can add an episode-truth manifest resolver or fail-closed explicit-input guard to one consumer group.
- Repro-only rows should be cleaned only when touching generated note prose.
