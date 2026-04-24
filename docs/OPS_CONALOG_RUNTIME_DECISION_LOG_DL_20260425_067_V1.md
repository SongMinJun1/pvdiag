<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260425_067_V1

## Decision
- Accept BR-085 as the evidence attachment packet for BR-084 reviewed episode truth rows.
- Do not treat evidence-card creation as a truth label.
- Keep threshold replay blocked until the BR-085 review template is intentionally filled and BR-084 is rebuilt with positive/negative replay-ready rows.

## Why
- BR-084 created a safe truth-intake table, but all 16 rows still had `needs_evidence`.
- The next risk is confusion: a reviewer could lose the source case IDs, prove/reject axes, or allowed label contract.
- BR-085 reduces that risk by creating one card per row and one fillable template, while leaving label/evidence fields blank by design.

## Evidence
- BR-085 output root:
  - `/private/tmp/panel_day_engine_episode_truth_evidence_attachment_br085_check`
- Real result:
  - input rows: `16`
  - evidence cards: `16`
  - review input template rows: `16`
  - track counts: `long_gap_backdating_review=6`, `strict_sudden_prior_episode_review=3`, `durable_precursor_review=7`
  - site counts: `ktc_ess=10`, `gangui=3`, `conalog=3`
  - reviewer truth labels assigned: `0`
  - reviewer evidence paths filled: `0`
  - threshold replay ready rows: `0`
  - operator-facing change allowed sum: `0`
  - engine patch allowed sum: `0`
  - threshold patch allowed sum: `0`

## Impact
- No runtime semantics change.
- No `panel_day_engine.py` change.
- No threshold change.
- No operator-facing output change.
- No release artifact regeneration.
- Future reviewed-truth work can now proceed row-by-row without reconstructing source context.

## Next Required Action
- Review evidence cards under:
  - `/private/tmp/panel_day_engine_episode_truth_evidence_attachment_br085_check/panel_day_engine_episode_truth_evidence_cards_v1/`
- Fill:
  - `/private/tmp/panel_day_engine_episode_truth_evidence_attachment_br085_check/panel_day_engine_episode_truth_review_input_template_v1.csv`
- Rebuild BR-084 with the filled template as `--review-input`.
- Open subtype-conditioned threshold replay only after positive and negative replay-ready rows exist.
