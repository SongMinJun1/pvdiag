<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_053_V1

## Decision
- Accept BR-071 as the regression/blocker packet for BR-064 strong common-cause hold rows.
- Keep all 50 rows as panel-local promotion blockers.
- Keep operator promotion, direct engine patch, and threshold patch authorization at zero.

## Why
- BR-064 identified 50 rows where common-cause spatiality is strong enough to block individual panel-local precursor reading.
- Those rows are not useless.
- They are valuable as regression pressure:
  - future algorithm patches should not promote them accidentally
  - future threshold proposals should prove common-cause spatiality remains separated from panel-local family evidence
- The rows split into two site-specific blocker shapes:
  - `gangui`: group-off synchrony
  - `ktc_ess`: site-event synchrony

## Evidence
- BR-071 output root:
  - `/private/tmp/strong_common_cause_blocker_regression_packet_check`
- Real result:
  - detail rows: `50`
  - unique panel roots: `13`
  - `gangui` group-off synchrony blockers: `20` rows / `5` roots
  - `ktc_ess` site-event synchrony blockers: `30` rows / `8` roots
  - operator promotion allowed sum: `0`
  - engine patch candidate sum: `0`
  - threshold patch allowed sum: `0`

## Impact
- No runtime output changes.
- No `panel_day_engine.py` semantic change.
- No new positive fault-family label.
- Future patch gates now have a concrete common-cause blocker packet to protect.

## Next Required Action
- Use BR-071 rows as regression pressure before any semantic algorithm patch.
- If a future rule wants to reclassify any row, it must add new independent evidence explaining why the common-cause blocker no longer applies.
- Continue exact-family or common-cause seed search without treating these rows as promotion seeds.
