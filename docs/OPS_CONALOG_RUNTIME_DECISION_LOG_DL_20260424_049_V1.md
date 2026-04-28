<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_049_V1

## Decision
- Accept BR-067 as a focused physical-vs-artifact review packet for the 2 BR-065 voltage-dominant rows.
- Keep both rows as `physical_leaning_voltage_axis_review`.
- Keep promotion and direct engine patch authorization at zero.

## Why
- BR-065 narrowed the local morphology pool from 10 rows to 2 voltage-dominant rows.
- BR-067 checks whether those 2 rows are broad peer/reference artifacts or panel-local voltage-axis candidates.
- Both rows show low peer voltage-dominant breadth and no target data-bad days.
- The `ktc_ess` row has 2 `no_ref` days, but its target v-ref ok rate remains `0.981982`, so that caution is not strong enough to overrule the panel-local voltage-axis evidence.

## Evidence
- BR-067 output root:
  - `/private/tmp/voltage_dominant_physical_vs_artifact_review_check`
- Real result:
  - detail rows: `2`
  - physical-leaning voltage-axis review rows: `2`
  - artifact/reference hold rows: `0`
  - two-axis review ready rows: `2`
  - operator promotion allowed sum: `0`
  - engine patch candidate sum: `0`

## Impact
- No runtime output changes.
- No `panel_day_engine.py` semantic change.
- No operator-facing promotion.
- The next question is no longer broad artifact screening; it is physical confirmation strength.

## Next Required Action
- Build or collect physical confirmation evidence for the 2 rows:
  - waveform/IV signature
  - maintenance/inspection history
  - repeated same-panel channel evidence
  - independently reproducible voltage-axis signature
- Do not propose a family-specific threshold until this confirmation layer exists.
