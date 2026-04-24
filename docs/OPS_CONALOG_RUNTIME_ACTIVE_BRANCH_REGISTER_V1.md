<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1

## Purpose
- runtime rule work is split into small branches so evidence does not get mixed with production semantics.
- this register records the current decision path and prevents re-opening the same question without new evidence.

## Current Branch
| branch | status | scope | next decision |
|---|---|---|---|
| `BR-20260424-045` | `repo_wide_cleanup_inventory_built` | broader repo cleanup pressure is now inventoried as six lanes; current evidence line stays intact, but user-priority emphasis moves to cleanup before more expansion | plan `main_dirty_disentangle` next |

## Completed Runtime Branches
| branch | status | key result | operator-facing change |
|---|---|---|---|
| `BR-20260423-002` | `merged_shadow_audit` | G1 extreme long-gap degradation fallback guard marks 7 ktc_ess backdating-suppression candidates | no |
| `BR-20260423-004` | `merged_shadow_audit` | secondary warning window audit exposes 112 candidates and 30 trigger-only-to-precursor review cases | no |
| `BR-20260423-005` | `merged_review_packet` | trigger-only candidates split into 4 supported-context and 26 persistent-secondary-only cluster-risk cases | no |
| `BR-20260423-006` | `merged_review_packet` | supported-context daily slice keeps all 4 as manual review and auto promotion 0 | no |
| `BR-20260423-007` | `merged_review_packet` | ktc_ess strict-common strongest 2 cases remain hold_shadow_only | no |
| `BR-20260423-008` | `merged_decision_contract` | promotion/backdating decision buckets fixed before code shadowing | no |
| `BR-20260423-009` | `shadow_audit_implemented` | audit adds `promotion_decision_bucket` and keeps `promote_candidate=0` | no |
| `BR-20260423-010` | `review_packet_generated` | bucket packet gives 112 non-empty rows and 37 action-queue rows | no |
| `BR-20260423-011` | `deep_packet_generated` | gangui blocked_cluster_risk 26 rows collapse to 2 roots with no site/subgroup/strict-proximal support | no |
| `BR-20260423-012` | `shadow_simulation_generated` | G1 suppression simulation maps ktc_ess 7 rows from current 전조형 고장 to shadow 급작 고장 with no code change | no |
| `BR-20260423-013` | `shadow_audit_implemented` | audit adds 10 G1 suppressed-event shadow columns; final verdict remains byte-equivalent by table value | no |
| `BR-20260423-014` | `semantic_preview_generated` | preview shows 7 ktc_ess rows would change 13 operator-facing columns and 91 cells; no production output written | no |
| `BR-20260423-015` | `apply_ready_sidecar_generated` | strict-proximal support splits G1 preview into 6 apply-ready rows and 1 hold-review row | no |
| `BR-20260423-016` | `semantic_patch_validated` | applies G1 semantics to 6 strict-proximal rows; runtime final verdict changes 6 rows/14 columns/84 cells; cause top ranks unchanged | yes, raw-only candidate runtime semantics only |
| `BR-20260423-017` | `morphology_atlas_shadow_generated` | atlas 6 families, threshold candidates 6 axes, shadow rows 145; G1 6 rows blocked as long-gap one-day episodes | no |
| `BR-20260423-018` | `subtype_hypothesis_roadmap_locked` | locks 17 subtype hypotheses under 6 family buckets; next implementation must be shadow-only subtype evidence columns | no |
| `BR-20260423-019` | `subtype_shadow_columns_validated` | adds 6 subtype hypothesis shadow columns to runtime fault-event audit; 145 populated, production write sum 0, final verdict/heuristic unchanged | no |
| `BR-20260423-020` | `retrospective_subtype_consistency_audit_complete` | reviews prior decision groups under subtype goal; semantic reopen 0, operator-facing rollback 0, shadow follow-up groups 3 | no |
| `BR-20260423-021` | `shape_confidence_blocker_split_validated` | adds 3 shadow columns; old audit common columns, final verdict, and heuristic remain equal to BR-019; shape medium 136, low 9, blocker common_cause 138, backdating_risk 7 | no |
| `BR-20260423-022` | `common_cause_blocker_detail_validated` | adds `group_off_history_flag` and blocker detail; BR-021 common columns/final verdict/heuristic remain equal; site_event 60, strict_trigger_proximal 49, group_off 28, subgroup_common_cause 1, backdating_risk 7 | no |
| `BR-20260423-023` | `blocker_detail_review_packet_generated` | packet rows 77: group_off 28, strict_trigger_proximal 49; priority split P1 cluster false-positive 26, P1 strict-vs-secondary 43, P2 group 2, P2 strict 6 | no |
| `BR-20260423-024` | `patch_gap_review_complete` | fixes BR-023 packet id order to `BR023-001..077`; records remaining gaps: tracked generator missing, site_event 60 not packeted, review priority is triage-only | no |
| `BR-20260424-025` | `boundary_note_sync_complete` | final_delivery docs now state stable/runtime contract separation after PR-79 merge; active register moved from BR-024 packet cleanup to the next Gate 7 safe-lane choice | no |
| `BR-20260424-026` | `signal_score_map_tightened` | Gate 2C now locks projection bundles: precursor/hard-evidence/common-cause/ambiguity/actionability can combine, but single helpers and explanation-only signals cannot jump directly to top-level projection | no |
| `BR-20260424-027` | `counterexample_regression_checklist_added` | counterexample set now has an explicit regression gate: bucket pressure-test matrix, per-bucket checks, and minimum pass rule before algorithm patch | no |
| `BR-20260424-028` | `missing_seed_scan_complete` | scan confirms `제어응답형 top1` and report-row direct common-cause overlap are still absent, but finds live-chain MLPE shortlist 4건 plus raw-daily `group_off` / `co_drop_surge` provisional seed clusters | no |
| `BR-20260424-029` | `provisional_seed_promotion_criteria_locked` | BR-028 provisional shortlist may enter the curated counterexample set only as `hold/reroute pressure-test seed`; this does not close the still-missing exact target families | no |
| `BR-20260424-030` | `score_to_projection_precedence_locked` | projection follows `eligible evidence lane -> hold/reroute cap -> actionability ceiling`; `highest score wins` reading is explicitly rejected | no |
| `BR-20260424-031` | `curated_seed_promotion_and_gap_rescan_complete` | selected provisional shortlist rows are promoted into curated counterexample rows, while exact same-day target families remain absent and widened `±7일` near-window backlog is recorded | no |
| `BR-20260424-032` | `near_window_backlog_doc_sync_complete` | patch-gate docs are synced so `same-day exact` missing families and widened `±7일` near-window backlog are tracked separately before any new algorithm gating discussion | no |
| `BR-20260424-033` | `near_window_backlog_data_assessed_keep_backlog` | widened near-window backlog compresses to `5` report rows / `4` roots with mixed flags, slices, and sign, so it stays non-closing | no |
| `BR-20260424-034` | `exact_seed_deep_scan_supportive_only` | control-like score and raw-only artifact date widening are re-scanned, but both remain supportive only and still do not create exact family closure | no |
| `BR-20260424-035` | `exact_seed_blocker_anatomy_locked` | same-day direct raw rows are re-read as `candidate reservoir`, while missing exact family is attributed to report-lane entry and date-alignment blockers | no |
| `BR-20260424-036` | `judgment_rubric_locked` | new evidence is now classified first as exact closure, supportive hint, candidate reservoir, non-closing backlog, or structural blocker before any patch discussion | no |
| `BR-20260424-037` | `group_off_report_lane_blockers_mapped` | `group_off_date` exact raw rows split into no-entry, precursor-carryover, rawonly-date-displaced, and near-anchor blocker subtypes; only the last remains a plausible near-term inspect target | no |
| `BR-20260424-038` | `patch_direction_rationale_locked` | explicit rationale recorded for staying docs/evidence-first and blocker-first while exact family remains missing and most evidence is still below closure grade | no |
| `BR-20260424-039` | `evidence_axis_opportunity_mapped` | confirms the same blocker-first/evidence-first method can be reused beyond the current exact-family gap and ranks `report_entry_friction`, `recovery_recurrence`, and `common_cause_synchrony` as the strongest first sidecars | no |
| `BR-20260424-040` | `report_entry_friction_axis_sidecar_implemented` | adds a reproducible builder/smoke pair and shows `group_off_date` / `site_event` rows can now be split into current/precursor/rawonly/no-entry blocker families without touching runtime semantics | no |
| `BR-20260424-041` | `recovery_recurrence_axis_sidecar_implemented` | adds a reproducible builder/smoke pair and shows transient/sustained/re-drop/persistent morphology can now be read together with report-lane entry bias across sites | no |
| `BR-20260424-042` | `evidence_execution_order_locked` | locks the next sequence after BR-041 so work is not forgotten: manifest first, `common_cause_synchrony` second, cross-axis review third, exact-family re-search fourth, algorithm gating last | no |
| `BR-20260424-043` | `evidence_manifest_pack_root_implemented` | adds a reproducible manifest builder/smoke pair and a family-organized pack root so base result, blocker scan, opportunity scan, and sidecar artifacts can be read from one index | no |
| `BR-20260424-044` | `remaining_organization_gap_audited` | confirms the current evidence line is organized, while `25` historical BR temp roots, `3` manual-oneoff manifest rows, and `47` wider audit/probe builders remain backlog cleanup targets outside the current blocker path | no |
| `BR-20260424-045` | `repo_wide_cleanup_inventory_built` | inventory confirms the broader cleanup pressure is repo-wide, not evidence-only: main dirty concentration, mirror-surface skew, builder sprawl, archive temp roots, runtime bundle weight, and workspace clutter are now explicit lanes | no |

## Decision Locks
- `trigger_only_to_precursor` is never promoted directly from secondary-window persistence alone.
- `strict_common_cause + site_event_history` is not enough for automatic promotion when retained daily signal is zero.
- `gangui` persistent-secondary cluster cases stay blocked until cluster false-positive risk is resolved.
- BR-002 G1 is a backdating suppression path, not a precursor promotion path.
- Current evidence has `promote_candidate = 0`.
- BR-009 buckets are exclusive: `manual_review=2`, `hold_shadow_only=2`, `blocked_cluster_risk=26`, `backdate_suppression_candidate=7`, `audit_provenance_only=75`.
- BR-010 action queue excludes provenance-only rows: `37` rows remain for review.
- BR-011 closes `blocked_cluster_risk=26` as `blocked_counterexample_hold`: all rows are `gangui`, 2 roots, selected gaps 115-120 days, site/subgroup/strict-proximal support 0.
- BR-012 keeps `backdate_suppression_candidate=7` as shadow-only: if G1 is applied, all 7 become `전조형 고장 -> 급작 고장` simulation rows, but production semantics stay unchanged.
- BR-013 implements the same G1 result as audit shadow columns only: audit common columns equal `true`, final verdict full table equal `true`, G1 shadow rows `7`.
- BR-014 previews operator-facing impact only: 7 ktc_ess rows, 13 columns, 91 cells, production output written `0`; 1 row lacks strict-proximal common-cause support.
- BR-015 reduces first-patch scope to strict-proximal-supported rows only: apply-ready `6`, hold-review `1`, production output written `0`.
- BR-016 applies only those 6 rows and keeps the hold row excluded. Runtime final verdict changes `6` rows, `14` columns, `84` cells; the extra column beyond BR-015 is derived `대표판정_ko`.
- BR-016 blocks unintended cause-candidate rank drift: top1/top2/top3 cause rank drift rows `0`; published strict current output changed rows `0`.
- BR-017 is atlas/shadow only: `production_write_allowed_sum = 0`.
- BR-017 G1 episode basis uses `g1_suppressed_event_shadow_current_onset_date`, because BR-016-applied rows no longer carry current `retrospective_onset_date`.
- BR-017 v1 thresholds produce confirmed precursor candidates `0`; this is a conservative starting point, not a final rule.
- BR-018 locks subtype names as `hypothesis`, not operator-facing final labels.
- BR-018 requires subtype evidence to be defended by at least two axes before any promotion discussion: examples are duration+continuity, recurrence+VI-shape, or spatiality+fast-recovery.
- BR-018 keeps sensor/measurement and external/common-cause subtype paths out of individual panel precursor promotion.
- BR-019 appends subtype hypothesis columns to the audit/evidence layer only; `subtype_production_write_allowed_sum = 0`.
- BR-019 keeps old audit common columns, raw-only final verdict, and raw-only heuristic equal to BR-017.
- BR-019 records subtype shape first and common-cause as a hold reason/tag, so subtype review can proceed without operator-facing promotion.
- BR-020 confirms the subtype goal does not require reopening prior semantic decisions: `semantic_reopen_required_sum = 0`.
- BR-020 marks exactly 3 shadow follow-up groups: secondary-window chain, promotion decision contract extension, and BR-019 confidence/blocker decomposition.
- BR-021 keeps legacy `subtype_confidence_shadow=hold` for 145 subtype rows, while separating shape confidence from blockers: `medium=136`, `low=9`, `common_cause=138`, `backdating_risk=7`.
- BR-021 confirms no semantic drift: BR-019 old audit common columns equal `true`, raw-only final verdict equal `true`, raw-only heuristic equal `true`.
- BR-022 keeps BR-021 old audit common columns equal `true` while splitting blocker details: `site_event=60`, `strict_trigger_proximal=49`, `group_off=28`, `subgroup_common_cause=1`, `backdating_risk=7`.
- BR-023 is packet-only: `group_off=28` and `strict_trigger_proximal=49` are review rows, `subtype_production_write_allowed_sum=0`, and no runtime code changed.
- BR-024 confirms BR-023 packet IDs are review handles only, not semantic ranks; after cleanup the packet opens at `BR023-001` and remains `subtype_production_write_allowed_sum=0`.
- BR-025 applies accepted boundary-note decisions only: final_delivery docs stay stable-first, runtime redesign artifact semantics remain canonical in the runtime pack README/mapping note, and no runtime code or row universe changes.
- BR-026 tightens Gate 2C without touching code: `actionability_score` is capped by eligible evidence lanes, `common_cause_risk_score` and `mlpe_ambiguity_score` stay hold/reroute axes, and explanation-only signals remain non-promoting.
- BR-027 turns counterexamples into an actual patch gate: algorithm changes now need bucket coverage, bundle-specific checks, and minimum pass conditions, not just a loose seed list.
- BR-028 adds evidence about the remaining gaps: the desired `장치 응답 이상형/제어응답형 top1` seed is still missing, official/current direct overlap with common-cause is still missing, but raw-daily provisional seed clusters now exist for curation.
- BR-029 separates `curated seed promotion` from `exact family closure`: provisional MLPE/common-cause shortlist can be used as regression seed only if reproducible identity, direct bundle pressure, two-cue evidence, and prohibited-overgeneralization note are all present.
- BR-030 locks projection precedence: promotion starts from eligible evidence lanes only, common-cause and ambiguity are hold/reroute caps, and actionability cannot outrun the strongest eligible lane.
- BR-031 actually promotes selected BR-028 shortlist rows into curated counterexample rows and confirms the exact same-day target families are still missing, while widened `±7일` near-window overlap backlog now exists.
- BR-032 syncs the patch-gate docs after BR-031: `near-window overlap backlog` can be tracked, but it still cannot be substituted for `same-day exact family closure`.
- BR-033 uses the actual backlog composition to reject immediate family promotion: current near-window backlog compresses to `5` report rows / `4` roots with mixed flag families, mixed slices, and mixed gap direction, so it remains a non-closing backlog.
- BR-034 confirms two more non-closures: `control_score > 0` is still only supportive hint, and expanded raw-only artifact date matching still leaves `same-day direct overlap = 0`.
- BR-035 confirms the next blocker is structural: raw-daily same-day direct rows exist as a reservoir, but report-layer exact family is still blocked by row-universe and date-alignment mismatch.
- BR-036 locks a single judgment rubric over BR-033/034/035 outputs: `supportive_hint`, `candidate_reservoir`, `non_closing_backlog`, and `structural_blocker` are distinct roles, and only `exact_family_closure` can close the still-missing family directly.
- BR-037 shows the `group_off_date` family is not one blocker but four subtypes: `no_report_lane_entry`, `precursor_carryover_without_exact_overlap`, `rawonly_date_displaced`, and `rawonly_near_signal_anchor`; only the last one remains a plausible near-term exact-family inspect target.
- BR-038 locks the rationale for this whole path: exact family is still missing, most evidence is below closure grade, and blocker subtypes are more informative than premature threshold/rule changes, so docs/evidence-first remains the correct patch direction.
- BR-039 confirms the same method can be reused elsewhere: `report_entry_friction`, `recovery_recurrence`, and `common_cause_synchrony` are the strongest evidence-axis expansion candidates already supported by existing raw/audit fields.
- BR-040 turns the first of those candidates into code without touching runtime semantics: `report_entry_friction_axis` is now a reproducible sidecar, not an ad-hoc temp scan, and it keeps `group_off_date` / `site_event` in the evidence/blocker layer only.
- BR-041 turns the second candidate into code without touching runtime semantics: `recovery_recurrence_axis` is now a reproducible sidecar that keeps recovery/re-drop morphology in the evidence layer and explains lane bias by site.
- BR-042 locks the immediate next order so the current work does not drift: before the third axis, evidence layout must be consolidated into one manifest/pack root.
- BR-043 implements that consolidation step: current evidence artifacts are now readable from one manifest/pack root, and future scans should start there instead of re-assembling temp roots by memory.
- BR-044 confirms that there are still broader organization gaps outside the current line, but they belong to archive/registry backlog rather than the immediate blocker path, so the next implementation still remains `common_cause_synchrony_axis`.
- BR-045 widens the lens beyond evidence-only cleanup: the next practical emphasis is now repo-wide cleanup planning, with `main_dirty_disentangle` first, before adding more expansion lanes.

## Next Safe Implementation
- keep `promotion_decision_bucket` as an audit/shadow field only.
- use bucket-specific review packets before proposing any operator-facing event semantic change.
- before any new production semantic patch, keep duration/gap/continuity/spatiality separated by fault-family threshold candidates.
- adjudicate BR-023 `group_off` cluster boundaries and `strict_trigger_proximal` vs secondary-window evidence before any subtype promotion discussion.
- before generating more packet branches, prefer a tracked packet generator or an exact one-shot reproduction script.
- keep `subtype_production_write_allowed = 0` until a fresh tri-site review proves a subtype can be raised without final verdict drift.
- after BR-043, use the evidence manifest/consolidated pack root as the default read base, then implement `common_cause_synchrony_axis`, then do a cross-axis review, then rerun exact same-day missing-family search, and only then reopen algorithm gating.
- after BR-045, keep that runtime evidence order intact, but insert a repo-cleanup prelude on the practical execution lane: first `main_dirty_disentangle`, then `source_release_finaldelivery_mirror_policy`, then `audit_builder_registry`.
