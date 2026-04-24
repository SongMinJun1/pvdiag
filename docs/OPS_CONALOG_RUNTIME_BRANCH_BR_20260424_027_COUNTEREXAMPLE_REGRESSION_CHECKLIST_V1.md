<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_027_COUNTEREXAMPLE_REGRESSION_CHECKLIST_V1

## Purpose
- Turn the existing counterexample seed list into an actual pre-patch regression gate.
- Tie each counterexample bucket to the BR-026 projection-bundle rules so the next algorithm patch cannot skip ambiguous/common-cause hold logic.
- Keep this branch docs-only and leave runtime code, thresholds, row universe, and output schemas unchanged.

## Findings
| finding | severity | action |
|---|---|---|
| `OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md` already had good seed rows, but `regression checklist` was still only a TODO item | medium process gap | create a dedicated checklist doc and link it from Gate 2C + counterexample set |
| after BR-026, bucket names alone were no longer enough; each bucket needed a clear `which bundle is under pressure` rule | medium design gap | add bucket pressure-test matrix and per-bucket checks |
| without a minimum pass rule, algorithm gating could still move forward with weak `MLPE ambiguous` or `common_cause risk` coverage | medium safety gap | add minimum pass rule before algorithm patch |

## Fixed In This Branch
- Added `OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_REGRESSION_CHECKLIST_V1.md`
- Expanded `OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md` with:
  - BR-026 bundle-oriented reading rules
  - regression checklist reference
- Updated `OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md`
  - algorithm gating pre-check now includes the counterexample regression checklist
- Updated `OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
  - set BR-027 as current branch
  - recorded BR-027 as completed docs-only branch

## Validation
| check | result |
|---|---|
| code change | no |
| runtime semantics change | no |
| threshold change | no |
| row universe change | no |
| counterexample regression checklist created | yes |
| Gate 2C linked to checklist | yes |
| active register advanced to BR-027 | yes |
| operator-facing change | no |

## Decision
- BR-027 is safe to merge as a docs-only process hardening branch.
- The next safe work is no longer “invent a new rule”; it is “collect the missing high-value seeds that the checklist now requires,” especially:
  - `장치 응답 이상형` top1 or recovery/rebound MLPE ambiguous rows
  - work/event/group_off direct-overlap common-cause rows
