<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_026_SIGNAL_SCORE_MAP_TIGHTENING_V1

## Purpose
- Tighten `Gate 2C existing signal -> score axis map` from a loose inventory table into a conservative `projection bundle` contract.
- Keep this branch docs-only so no runtime code, thresholds, row universe, or operator-facing semantics change.
- Make the next algorithm discussion start from `which axis combinations are eligible` rather than `which helper looked persuasive`.

## Findings
| finding | severity | action |
|---|---|---|
| Gate 2C already mapped signals to axes, but it was still easy to read `prefault_B_effective`, `critical_fault`, `v_drop`, or `critical_source` as near-direct promotion clues | medium design ambiguity | add explicit projection-bundle constraints and non-promotion locks |
| `actionability_score` could be over-read as an independent escalation axis unless capped by precursor/hard-evidence/common-cause/ambiguity bundles | medium design ambiguity | lock `actionability ceiling` in Gate 2C |
| common-cause and MLPE ambiguity were described as scores but not yet firmly declared `hold/reroute axes` | medium design ambiguity | lock them as suppressor/hold bundles rather than promotion bundles |

## Fixed In This Branch
- Added `projection bundle tightening` section to `OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md`
  - precursor bundle minimum conditions
  - hard-evidence bundle minimum conditions
  - common-cause hold bundle
  - MLPE ambiguity hold bundle
  - actionability ceiling
  - explanation-only signal usage limits
- Updated `OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
  - set BR-026 as current branch
  - recorded BR-026 as completed docs-only branch
  - set next decision to `counterexample seed expansion` vs `score-to-projection decision log`

## Validation
| check | result |
|---|---|
| code change | no |
| runtime semantics change | no |
| threshold change | no |
| row universe change | no |
| Gate 2C bundle locks added | yes |
| actionability ceiling documented | yes |
| explanation-only non-promotion lock documented | yes |
| operator-facing change | no |

## Decision
- BR-026 is safe to merge as a docs-only design tightening branch.
- This branch does not authorize a new algorithm patch yet.
- Next safe work should use real counterexamples to pressure-test the new bundle rules before any code gating patch.
