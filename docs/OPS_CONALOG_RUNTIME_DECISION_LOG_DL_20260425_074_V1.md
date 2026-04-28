<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260425_074_V1

## Decision
- Accept BR-092 as an expanded voltage-preserved positive-truth search reservoir.
- Do not promote any BR-092 search hit to positive truth in this branch.
- Do not approve threshold tuning or direct `panel_day_engine.py` edits.
- Use the known negative overlap as a counterexample warning for future voltage-preserved threshold proposals.

## Why
- BR-090 found clean-looking voltage-preserved pilot rules, but only one positive truth seed existed.
- BR-091 confirmed that the 6 deferred durable holds are not the right source for voltage-preserved positives.
- BR-092 therefore searched outside those holds and found:
  - `96` best-per-hard-episode candidate rows
  - `94` new search candidates
  - `86` manual-review-ready rows
  - `1` rediscovered known positive seed
  - `1` known negative counterexample overlap
  - `0` known hold overlap rows
- The positive rediscovery shows the search can find the intended morphology.
- The negative overlap proves the search pattern is not sufficient as a truth label or threshold rule.

## Evidence
- BR-092 output root:
  - `/private/tmp/panel_day_engine_voltage_preserved_positive_search_br092_check`
- Real result:
  - candidate rows: `96`
  - summary rows: `10`
  - new search candidates: `94`
  - manual review ready rows: `86`
  - positive truth candidate approved sum: `0`
  - threshold tuning approved sum: `0`
  - patch authorization sums: `0`
- Candidate tier counts:
  - `strong_b089_like=80`
  - `voltage_preserved_10d=8`
  - `voltage_preserved_2d_review=8`

## Impact
- No runtime semantics change.
- No `panel_day_engine.py` change.
- No threshold change.
- No operator-facing output change.
- No release artifact regeneration.
- The project gains a larger candidate reservoir, but performance/result improvement remains unclaimed until confirmed truth and replay exist.

## Next Required Action
- Build a confirmation packet for `manual_review_ready=1` candidates.
- Deduplicate repeated candidates by panel/root/date family.
- Require independent source or raw/physical confirmation before adding any positive truth rows.
- Re-run BR-090 only after at least 3 independent positive truth rows are confirmed.
- Keep direct engine edits behind the BR-076 3-gate prepatch runbook.
