<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_180_PANEL_DAY_EVIDENCE_INPUT_MANIFEST_CONTRACT_V1

## Purpose
- Continue after BR-179 closed the episode-truth manifest-resolution lane.
- Target the next BR-169 workflow lane: `panel_day_engine_evidence`.
- Build a contract table before changing any evidence-builder temp defaults.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not rewrite or delete `/private/tmp` evidence defaults in this branch.
- Do not change runtime diagnosis semantics, truth labels, threshold tuning, replay eligibility, or operator-facing outputs.
- Do not treat note/repro strings or scanner literals as executable input contracts.

## Review Method
- Reuse the BR-169 live-temp reference review.
- Filter:
  - `workflow_lane = panel_day_engine_evidence`
- Add consumer-level contract fields:
  - consumer script,
  - explicit input flag,
  - upstream stage key,
  - default path,
  - reference shape,
  - live-reference kind,
  - manifest/explicit-input requirement flag,
  - literal/repro-only flag,
  - runtime/bulk-rewrite safety flags.

## Observed Counts
- evidence reference rows: `30`
- manifest-required rows: `26`
- explicit-input-supported rows: `26`
- literal/repro-only rows: `4`
- unmapped required rows: `0`
- runtime semantic change allowed rows: `0`
- bulk rewrite allowed rows: `0`

## Kind Split
| live_reference_kind | count | handling |
|---|---:|---|
| `static_upstream_directory_input` | `20` | resolve from manifest or explicit directory input |
| `static_upstream_artifact_input` | `6` | resolve from manifest or explicit artifact input |
| `embedded_note_repro_command` | `3` | refresh note/runbook prose only when touching the builder |
| `intentional_temp_detection_literal` | `1` | preserve or mark scanner literal if it creates audit noise |

## Consumer Split
| consumer | rows |
|---|---:|
| `build_panel_day_engine_subtype_truth_expansion_backlog_v1.py` | `6` |
| `build_panel_day_engine_direction_assumption_audit_v1.py` | `5` |
| `build_panel_day_engine_exact_family_closure_readiness_review_v1.py` | `3` |
| `build_panel_day_engine_fault_family_judgment_candidate_packet_v1.py` | `2` |
| `build_panel_day_engine_physical_evidence_request_packet_v1.py` | `2` |
| `build_panel_day_engine_subtype_threshold_replay_pilot_v1.py` | `2` |
| other single-row evidence consumers | `10` |

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_evidence_input_manifest_contract_v1.py \
  research/prognostics/smoke_test_panel_day_engine_evidence_input_manifest_contract_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_evidence_input_manifest_contract_v1.py

python3 research/prognostics/build_panel_day_engine_evidence_input_manifest_contract_v1.py \
  --repo-root "$(pwd)" \
  --output-dir /private/tmp/panel_day_engine_evidence_input_manifest_contract_br180_check

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Output Paths
- `/private/tmp/panel_day_engine_evidence_input_manifest_contract_br180_check/panel_day_engine_evidence_input_manifest_contract_v1.csv`
- `/private/tmp/panel_day_engine_evidence_input_manifest_contract_br180_check/panel_day_engine_evidence_input_manifest_contract_summary_v1.csv`
- `/private/tmp/panel_day_engine_evidence_input_manifest_contract_br180_check/panel_day_engine_evidence_input_manifest_contract_note_v1.md`
- `/private/tmp/panel_day_engine_evidence_input_manifest_contract_br180_check/panel_day_engine_evidence_input_manifest_contract_v1.json`

## Decision
- BR-180 is a contract patch, not an execution rewrite.
- The next safe branch should pick one high-impact evidence consumer and add a manifest resolver or fail-closed explicit-input path.
- Highest practical first candidates are:
  - `build_panel_day_engine_subtype_truth_expansion_backlog_v1.py`
  - `build_panel_day_engine_direction_assumption_audit_v1.py`
- Literal/repro and scanner-literal rows stay outside execution patches.
