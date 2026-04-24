<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_066_EVIDENCE_HANDOFF_INDEX_V1

## Purpose
- Answer whether the current evidence line is readable enough for another reviewer to continue.
- Provide one handoff entry point after BR-065 so the next worker does not need to reconstruct the path from memory.
- Keep this as documentation only: no runtime verdict, operator-facing output, or `panel_day_engine.py` behavior changes.

## Handoff Verdict
- Current state is `handoff_ready_with_index`.
- Evidence is already reproducible and well separated by branch docs, but the entry points were too distributed across Active Register, Gate7, temp output roots, and per-branch notes.
- BR-066 makes the continuation path explicit:
  - read the branch register for status
  - read the Gate7 lock for allowed order
  - read the evidence manifest for artifact roots
  - read BR-064 and BR-065 for the current fault-family decision frontier
  - run the safety gates before any direct engine patch

## Start Here
| question | first file to open | why |
| --- | --- | --- |
| Where are we now? | `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md` | current branch status, completed BR list, and next safe implementation |
| What order must be followed? | `docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md` | lane order, forbidden shortcuts, and validation sequence |
| Where are the evidence artifacts? | `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_043_EVIDENCE_MANIFEST_PACK_ROOT_V1.md` | single manifest / pack root entry point for scattered evidence outputs |
| What candidate pool matters now? | `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_064_FAULT_FAMILY_JUDGMENT_CANDIDATE_PACKET_V1.md` | 209 cross-axis rows split before thresholding |
| What is the immediate next review target? | `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_065_LOCAL_MORPHOLOGY_FAMILY_SHAPE_REVIEW_V1.md` | 10 local morphology rows narrowed to 2 voltage-dominant hard-signal review rows |
| Can we patch `panel_day_engine.py` now? | `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_060_PANEL_ENGINE_ALGORITHM_PREPATCH_RUNBOOK_V1.md` | direct algorithm patch must pass combined safety and regression gates first |

## Current Evidence Frontier
| layer | current result | continuation rule |
| --- | --- | --- |
| evidence manifest | BR-043 indexes scattered sidecar/temp artifacts from one manifest and pack root | use the manifest before opening raw temp roots manually |
| cross-axis sync | BR-051 gives 209 cross-axis review rows | keep common-cause, local morphology, and weak context separate |
| exact family search | BR-052 keeps target exact closure at `0` | do not claim exact target closure from supportive hints |
| regression pressure | BR-058 packages 11 non-target/sensor-feedback pressure seeds | use as counterexamples only |
| prepatch gate | BR-060 combines panel-engine safety and fault-family regression gates | passing is a review precondition, not patch approval |
| result delta | BR-061/062 separate output change from performance improvement | no accuracy/F1 improvement claim without truth-label evaluation |
| direct engine rehearsal | BR-063 changed `critical_fault` selection style with result delta `0` | use as the minimum pattern for future engine patches |
| fault-family packet | BR-064 splits 209 rows: common-cause hold/block `176`, regression pressure `11`, local morphology `10`, weak hold `12` | threshold work starts from family/axis buckets, not a blended score |
| shape review | BR-065 splits 10 rows: recovery-only hold `8`, voltage-dominant review `2` | inspect only the 2 voltage-dominant rows next |

## Immediate Next Work
- Scope:
  - inspect only the 2 `voltage_dominant_hard_signal_review` rows from BR-065
  - decide whether they look like partial-open/contact/voltage-axis physical fault or measurement/reference/channel artifact
- Required output:
  - a review packet, not an engine patch
  - per-row physical-vs-artifact evidence fields
  - `operator_promotion_allowed_flag = 0`
  - `engine_patch_candidate_flag = 0`
- Not allowed yet:
  - no family-specific threshold patch
  - no direct operator promotion
  - no claim that voltage-dominant morphology is automatically a confirmed fault family

## Repro Sequence For A New Reviewer
```bash
git status --short --branch
python3 research/prognostics/build_panel_day_engine_fault_family_judgment_candidate_packet_v1.py --cross-axis-input /private/tmp/cross_axis_manifest_sync_review_check/panel_day_engine_cross_axis_manifest_sync_review_v1.csv --pressure-input /private/tmp/fault_family_regression_pressure_packet_check/panel_day_engine_fault_family_regression_pressure_packet_v1.csv --threshold-input docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_THRESHOLD_CANDIDATE_V1.csv --subtype-input docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_018_FAULT_SUBTYPE_HYPOTHESIS_MAP_V1.csv --output-dir /private/tmp/fault_family_judgment_candidate_packet_check
python3 research/prognostics/build_panel_day_engine_local_morphology_family_shape_review_v1.py --packet-input /private/tmp/fault_family_judgment_candidate_packet_check/panel_day_engine_fault_family_judgment_candidate_packet_v1.csv --data-root /Users/b9gc/pvdiag/data --output-dir /private/tmp/local_morphology_family_shape_review_check
python3 -m py_compile pv_ae/panel_day_engine.py
```

## Handoff Gaps Still Open
- Some evidence roots are still `/private/tmp` artifacts, not repo-tracked canonical data.
- The evidence manifest exists, but BR-064 and BR-065 are newer than the original BR-043 manifest snapshot and should be read from their own branch docs until a later manifest refresh includes them.
- Release package smoke tests can rewrite absolute paths/timestamps in generated JSONs; those are validation side effects and should not be committed unless the release artifact contract is intentionally regenerated.
- The PR is intentionally draft because the next step is still review-only, not a finished semantic release.

## Decision
- Treat the evidence line as sufficiently organized for continuation after this index.
- The safest next branch is a focused `voltage_dominant_physical_vs_artifact_review`, not a direct `panel_day_engine.py` patch.
- If a future worker cannot reproduce BR-064 and BR-065 from the commands above, stop and fix the handoff/repro layer before adding new judgment rules.
