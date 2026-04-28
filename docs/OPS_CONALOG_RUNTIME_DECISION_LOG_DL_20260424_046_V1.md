<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_046_V1

## Decision
- Accept BR-064 `fault_family_judgment_candidate_packet` as the required review layer before proposing fault-family-specific threshold changes.
- Keep this layer audit-only:
  - `operator_promotion_allowed_flag = 0`
  - `engine_patch_candidate_flag = 0`

## Why
- BR-063 proved that small direct engine cleanup can be rehearsed safely, but it did not prove any new semantic threshold.
- Fault families have different evidence shapes:
  - degradation/soiling/shadow needs duration and continuity.
  - open-connection and partial-open patterns may need recurrence and shape similarity.
  - diode/substring patterns need VI-shape evidence.
  - sensor/feedback rows must remain ambiguity/QA pressure unless panel-local evidence separates them.
  - external/common-cause rows must be handled before individual precursor promotion.
- Therefore a single threshold cannot be safely promoted until axes are separated by family.

## Evidence
- BR-064 real packet:
  - `/private/tmp/fault_family_judgment_candidate_packet_check`
- Packet result:
  - detail rows: `209`
  - criteria rows: `17`
  - common-cause block/hold rows: `176`
  - regression pressure rows: `11`
  - local morphology family-shape review rows: `10`
  - weak context hold rows: `12`
  - operator promotion allowed sum: `0`
  - engine patch candidate sum: `0`

## Impact
- No runtime output semantics change.
- No `panel_day_engine.py` patch is authorized by this decision.
- Next direct algorithm patch remains blocked until candidate family-shape rows are reviewed and then passed through the BR-060/061/062 gate pattern.

## Next Required Action
- Inspect BR-064 `local_morphology_family_candidate_review` rows first.
- For each candidate, try to assign or reject a family-shape hypothesis using at least two axes before thresholding.
- Keep common-cause and sensor-feedback rows out of direct individual panel precursor promotion.
