<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_050_V1

## Decision
- Accept BR-068 as raw waveform proxy support for the 2 BR-067 physical-leaning voltage-axis rows.
- Keep both rows in `raw_waveform_physical_support_review`.
- Keep promotion and direct engine patch authorization at zero.

## Why
- BR-067 showed weak broad peer/reference artifact evidence.
- BR-068 checks the raw daily CSVs directly at timestamp level.
- Both rows show persistent low target voltage relative to peer median while current is preserved:
  - `gangui` raw median voltage ratio `0.632757`, current ratio `1.040984`
  - `ktc_ess` raw median voltage ratio `0.564797`, current ratio `1.044655`
- Both rows have complete raw file coverage for target voltage-dominant signal days.

## Evidence
- BR-068 output root:
  - `/private/tmp/raw_waveform_physical_support_review_check`
- Real result:
  - detail rows: `2`
  - raw waveform physical-support rows: `2`
  - operator promotion allowed sum: `0`
  - engine patch candidate sum: `0`
  - raw active timestamp rows:
    - `gangui`: `14196`
    - `ktc_ess`: `15506`

## Impact
- No runtime output changes.
- No `panel_day_engine.py` semantic change.
- No operator-facing promotion.
- The physical hypothesis is stronger, but still not independently confirmed enough for threshold patching.

## Next Required Action
- Define the physical-confirmation requirement before thresholding:
  - IV/waveform confirmation artifact
  - maintenance/inspection evidence
  - repeated same-panel channel evidence
  - field-confirmed reproducible voltage-axis signature
- Do not convert BR-068 support rows into a family-specific rule until that confirmation layer exists.
