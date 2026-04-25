<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1

## Purpose
- runtime rule work is split into small branches so evidence does not get mixed with production semantics.
- this register records the current decision path and prevents re-opening the same question without new evidence.

## Current Branch
| branch | status | scope | next decision |
|---|---|---|---|
| `BR-20260425-099` | `voltage_preserved_truth_acquisition_queue_complete` | converts the 14 voltage-preserved requests into 45 collector-facing acquisition rows while keeping truth intake, threshold, and engine approval at 0 | collect exact-panel evidence and explicit clearances, then feed them back through BR-098 before truth intake |

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
| `BR-20260424-046` | `confusion_reduction_lanes_locked` | clarifies that the immediate goal is not git-only branch cleanup but reducing cross-lane confusion among mixed scopes, packaged mirrors, builder entrypoints, archive/current roots, runtime bundle, and workspace clutter | no |
| `BR-20260424-047` | `role_boundary_manifest_implemented` | adds a reproducible role/boundary builder and smoke; current dirty paths classify into 24 manifest roles with `unclassified_dirty_entry_total=0`, so the first confusion-reduction step is now actionable | no |
| `BR-20260424-048` | `mirror_boundary_manifest_implemented` | adds a reproducible source/package mirror boundary builder and smoke; package-facing mirror rows are split into in-sync mirrors, package-only surfaces, and generated artifacts | no |
| `BR-20260424-049` | `active_builder_entrypoint_registry_implemented` | adds a reproducible build/smoke entrypoint registry; 289 entrypoints split into packaged runtime, documented paired, documented unpaired, paired unreferenced, and unpaired review queues | no |
| `BR-20260424-050` | `common_cause_synchrony_axis_sidecar_implemented` | adds a reproducible common-cause synchrony sidecar; 206 tri-site panels split into site-event, group-off, subgroup, co-drop, and weak/local buckets across report lanes | no |
| `BR-20260424-051` | `cross_axis_manifest_sync_review_implemented` | adds a reproducible cross-axis review and refreshes the evidence manifest to include common-cause synchrony; 209 panels split into strong common-cause hold, subgroup/breadth context, local morphology, and weak context buckets | no |
| `BR-20260424-052` | `local_morphology_exact_seed_search_complete` | scans 21 local morphology rows; exact target top1 remains 0, supportive device-response recovery seed 1, sensor-feedback local morphology pressure rows 6, no-report heuristic gap 8 | no |
| `BR-20260424-053` | `panel_engine_patch_safety_gate_complete` | adds a reproducible gate and smoke so future `pv_ae/panel_day_engine.py` changes must include decision docs, shadow/safety evidence, smoke, source/package sync, and public behavior docs when behavior can change | no |
| `BR-20260424-054` | `panel_engine_patch_safety_gate_tightened` | closes BR-053 precision holes: package-only drift fails, source/package hash mismatch fails, deleted evidence cannot satisfy gates, and related active docs/builders/smokes are required | no |
| `BR-20260424-055` | `no_report_heuristic_gap_review_complete` | reviews 8 no-report heuristic rows; all are `미확정` and expected to be absent from fault-only heuristic, with 3 near-anchor observation-sidecar candidates and 5 date-displaced evidence-only rows | no |
| `BR-20260424-056` | `non_fault_morphology_observation_sidecar_complete` | emits sidecar-only evidence for the 3 near-anchor non-fault morphology rows; `operator_promotion_allowed_sum=0`, `engine_patch_candidate_sum=0` | no |
| `BR-20260424-057` | `exact_family_closure_readiness_review_complete` | rereads 21 local morphology rows after BR-056: target exact closure 0, non-target hard same-day fault-family seeds 5, sensor-feedback pressure seeds 6, closed non-fault blockers 8 | no |
| `BR-20260424-058` | `fault_family_regression_pressure_packet_complete` | packages 5 non-target hard same-day family-boundary seeds and 6 sensor-feedback ambiguity pressure seeds as regression/counterexample material only | no |
| `BR-20260424-059` | `fault_family_regression_prepatch_gate_complete` | checks BR-058 packet integrity with 12 required gates; packet rows 11, failed gates 0, target closure/promotion/engine patch sums all 0 | no |
| `BR-20260424-060` | `panel_engine_algorithm_prepatch_runbook_complete` | combined prepatch runbook passes both panel-engine safety and fault-family regression gates; packet rows 11, target closure/promotion/engine patch sums all 0 | no |
| `BR-20260424-061` | `result_delta_scorecard_complete` | result delta scorecard confirms core result delta 0 and blocks accuracy/F1 improvement claims without truth-label evaluation | no |
| `BR-20260424-062` | `result_delta_scorecard_compare_complete` | baseline vs fresh conalog rerun scorecard compare reports changed metric count 0, core result changed flag 0, and performance improvement claim still blocked | no |
| `BR-20260424-063` | `critical_bool_mask_engine_cleanup_complete` | source/package panel engine mirrors use explicit `critical_fault_mask`; safety gate/runbook/scorecard/compare all pass with result delta 0 | no |
| `BR-20260424-064` | `fault_family_judgment_candidate_packet_complete` | packages 209 cross-axis panels into family-judgment buckets: common-cause block/hold 176, regression pressure 11, local morphology family-shape review 10, weak hold 12; promotion/engine patch sums remain 0 | no |
| `BR-20260424-065` | `local_morphology_family_shape_review_complete` | rereads BR-064 local morphology 10 rows against panel-day shape metrics: 8 recovery-only holds, 2 voltage-dominant hard-signal review rows, promotion/engine patch sums remain 0 | no |
| `BR-20260424-066` | `evidence_handoff_index_complete` | adds a single handoff index so a new reviewer can start from status/order/artifact/candidate/shape documents without reconstructing context from memory | no |
| `BR-20260424-067` | `voltage_dominant_physical_vs_artifact_review_complete` | checks the 2 voltage-dominant rows against peer/reference artifact evidence; both are physical-leaning voltage-axis review, but still not confirmed family or engine patch candidates | no |
| `BR-20260424-068` | `raw_waveform_physical_support_review_complete` | raw daily CSV timestamp comparison supports both physical-leaning voltage-axis rows; raw support is stronger evidence but still not an independent physical confirmation or threshold approval | no |
| `BR-20260424-069` | `physical_confirmation_requirements_review_complete` | converts BR-068 raw support into an independent confirmation checklist; both rows have `0/2` required axes met and threshold/promotion/engine patch sums remain 0 | no |
| `BR-20260424-070` | `physical_evidence_request_packet_complete` | emits 2 high-priority exact-panel evidence requests for physical measurement plus maintenance/inspection records; promotion/engine/threshold sums remain 0 | no |
| `BR-20260424-071` | `strong_common_cause_blocker_regression_packet_complete` | turns 50 strong common-cause hold rows into blocker/regression seeds; panel-local promotion blocked sum 50 and promotion/engine/threshold sums remain 0 | no |
| `BR-20260424-072` | `common_cause_exact_seed_search_complete` | rereads 176 external/common-cause candidates: exact closure 0, candidate reservoir 49 panels / 101 raw rows, structural blockers 49, promotion/engine/threshold sums 0 | no |
| `BR-20260424-073` | `common_cause_structural_blocker_review_complete` | splits the 49 structural blockers into no-report 13, precursor-carryover 19, rawonly-displaced 15, and 2 manual trace targets; promotion/engine/threshold sums 0 | no |
| `BR-20260424-074` | `common_cause_manual_trace_review_complete` | traces the 2 manual targets: gangui is raw-only near-anchor trace-only, ktc_ess is post-current 71-day mismatch; official/current bridge and semantic patch sums 0 | no |
| `BR-20260424-075` | `common_cause_semantic_prepatch_gate_complete` | gates BR-071~074 before semantic loosening: overall pass, required failures 0, exact closure 0, raw direct rows 101, expected raw-only context warning 1 | no |
| `BR-20260424-076` | `algorithm_prepatch_runbook_common_cause_gate_complete` | upgrades the combined prepatch runbook from 2 gates to 3 gates by adding BR-075; panel-engine/fault-family/common-cause statuses all pass | no |
| `BR-20260424-077` | `project_completion_checkpoint_complete` | records the post-BR-076 whole-project map: safety gates are stronger, evidence frontier is known, but latest manifest/handoff indexing is stale | no |
| `BR-20260425-078` | `latest_evidence_handoff_manifest_complete` | adds a reproducible latest evidence/handoff manifest for BR-064~077: detail rows 14, primary artifacts present 14, operator/engine/threshold authorization sums 0 | no |
| `BR-20260425-079` | `algorithm_evolution_map_complete` | maps 10 current algorithm layers, 7 evidence gaps, and 6 ordered next actions; P0 gaps 4 and operator/engine/threshold authorization sums 0 | no |
| `BR-20260425-080` | `subtype_truth_expansion_backlog_complete` | maps 17 subtype hypotheses into truth backlog rows; P0 rows 12, current exact truth support 0, operator/engine/threshold authorization sums 0 | no |
| `BR-20260425-081` | `episode_truth_map_complete` | maps 244 episode/truth-review rows; all truth_pending, common-cause/group hold 205, long-gap/backdating hold 12, durable precursor review 7, patch authorization sums 0 | no |
| `BR-20260425-082` | `episode_truth_review_packet_complete` | creates 16 review rows from 22 selected source-lens rows: long-gap/backdating 6, strict-sudden 3, durable precursor 7; reviewer truth labels 0 and patch authorization sums 0 | no |
| `BR-20260425-083` | `direction_assumption_audit_complete` | verifies BR-079~082 counts, sequence, authorization boundaries, G1 bucket precedence, duplicate-lens collapse, and blank reviewer labels; 40/40 checks pass | no |
| `BR-20260425-084` | `reviewed_episode_truth_rows_intake_complete` | builds 16 truth-intake rows from BR-082; all `needs_evidence`, reviewer labels 0, threshold replay ready 0, patch authorization sums 0 | no |
| `BR-20260425-085` | `episode_truth_evidence_attachment_complete` | packages the 16 BR-084 rows into 16 evidence cards plus a blank review-input template; reviewer labels 0, evidence paths 0, threshold replay ready 0 | no |
| `BR-20260425-086` | `episode_truth_source_trace_audit_complete` | resolves 22 source references for 16 review rows; source rows resolved 22, identity matches 22, trace-ready 22, labels 0, replay-ready 0 | no |
| `BR-20260425-087` | `episode_truth_adjudication_worksheet_complete` | compresses source traces into 16 human-adjudication rows; guidance counts 6/3/7, labels 0, replay-ready 0 | no |
| `BR-20260425-088` | `episode_truth_conservative_negative_adjudication_complete` | conservative BR-084 review input fills 6 long-gap backdating negatives and 3 strict-sudden negatives; positives 0, deferred durable 7 | no |
| `BR-20260425-089` | `episode_truth_durable_shape_review_complete` | BR-089 mixed review input yields positive 1, negative 9, deferred 6; threshold tuning approved 0 | no |
| `BR-20260425-090` | `subtype_threshold_replay_pilot_complete` | pilot replay rows 112, summary rows 7; 3 broad rules blocked by hold pressure, 4 strict/voltage rules need more positive truth; threshold tuning approved 0 | no |
| `BR-20260425-091` | `durable_hold_raw_shape_review_complete` | reviews 6 durable holds over 48 selected raw days; no voltage-preserved positives added, 2 current-limited holds separated, threshold tuning approved 0 | no |
| `BR-20260425-092` | `voltage_preserved_positive_search_complete` | searches outside the 6 durable holds; candidate rows 96, manual-review-ready rows 86, known positive seed rows 1, known negative overlap rows 1, threshold approval 0 | no |
| `BR-20260425-093` | `voltage_preserved_confirmation_packet_complete` | compresses 86 voltage-preserved source candidates into 14 panel tasks and 7 root families; counterexample-risk packet rows 3, threshold approval 0 | no |
| `BR-20260425-094` | `runtime_workspace_retention_complete` | adds `--workspace-retention result-only`; fresh tri-site validation kept result artifacts at about 20M and removed about 7.01GiB of duplicate staged workspace data | no |
| `BR-20260425-095` | `voltage_preserved_evidence_request_packet_complete` | emits 14 evidence request rows and 73 checklist rows; raw waveform independent confirmation rows 0, evidence-ready/truth/threshold/engine approval sums 0 | no |
| `BR-20260425-096` | `voltage_preserved_raw_source_attachment_complete` | attaches 86 source-candidate traces and 1698 core daily/raw-file reference rows to all 14 requests; raw refs missing 0, physical confirmation/truth/threshold/engine approval sums 0 | no |
| `BR-20260425-097` | `voltage_preserved_confirmation_gap_review_complete` | review rows 14 split into vendor-supported 5, raw-supported 4, counterexample hold 3, blocker hold 2; vendor exact support 9 but field-confirmed/independent confirmation/truth/threshold/engine approvals all 0 | no |
| `BR-20260425-098` | `voltage_preserved_independent_confirmation_attachment_complete` | attachment rows 14; exact vendor positive/likely target rows 7, exact field-confirmed target rows 0, same-site reference target rows 3, independent confirmation 0, explicit all-clearance 0, truth intake ready 0 | no |
| `BR-20260425-099` | `voltage_preserved_truth_acquisition_queue_complete` | acquisition queue rows 45: independent confirmation 14, common-cause clearance 14, measurement-artifact clearance 14, counterexample clearance 3; collector template rows 45, truth intake ready 0 | no |

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
- BR-046 refines that wording so the target is explicit: the next practical emphasis is confusion reduction by role/boundary disentanglement, not branch cosmetics.
- BR-047 implements the first concrete role/boundary manifest: dirty paths are now read by `role_id`, `role_family`, owner, sync direction, edit policy, commit policy, validation, and cleanup action before any moving or syncing.
- BR-048 implements the second concrete confusion-reduction manifest: source/package mirror pairs are hash-checked separately from package-only surfaces and generated outputs.
- BR-049 implements the third concrete confusion-reduction manifest: build/smoke entrypoints are now read by pair status, package mirror status, doc reference count, and recommended action before adding or editing another script.
- BR-050 implements the third evidence-axis sidecar: common-cause synchrony is now readable by marker family and report lane, while `co_drop_breadth_hint` stays weak context and no runtime semantics change.
- BR-051 aligns the maps: evidence manifest now includes `common_cause_synchrony_axis`, cleanup maps stay separate from evidence-family rows, and cross-axis review gives the next search pool without algorithm gating.
- BR-052 confirms the cleaner local morphology pool still does not close the exact family gap: target top1 rows `0`, exact-family candidates `0`, supportive device-response seed `1`, and no-report heuristic gap `8`.
- BR-053 locks the safety rail before direct engine edits: engine source/package changes must pass the panel-engine safety gate packet before any runtime semantics patch is considered.
- BR-054 tightens that safety rail so source/package drift, content mismatch, deleted evidence, and unrelated filename-only evidence are blocked before any engine patch.
- BR-055 closes the immediate no-report heuristic gap as non-engine-bug evidence: all 8 rows are non-fault status-gated heuristic absences, engine patch candidates `0`.
- BR-056 closes the 3 near-anchor rows as sidecar-only observation evidence: operator promotion `0`, engine patch candidates `0`, exact-family closure still open.
- BR-057 confirms the post-BR-056 pool still has target exact closure `0`, while 11 non-target regression/pressure seeds are useful for future counterexample packets only.
- BR-058 turns those 11 seeds into an executable packet with `target_exact_closure_candidate_sum=0`, `operator_promotion_allowed_sum=0`, and `engine_patch_candidate_sum=0`.
- BR-059 turns BR-058 into a prepatch gate: the real packet passes 12 required gates and blocks shrinkage, promotion, target-closure drift, engine-patch drift, missing interpretation text, and common-cause mixing.
- BR-060 combines BR-054 and BR-059 into one executable prepatch runbook: both gates pass, and a passing runbook remains a review precondition rather than patch approval.
- BR-061 adds the result delta answer layer: core result change is `0`, raw-only candidate context is quantified, and performance improvement remains unclaimed without truth-label evaluation.
- BR-062 adds the before/after compare layer: future post-patch scorecards must be compared against the baseline before any result-change claim.
- BR-063 completes the first direct engine cleanup rehearsal with no result drift: scorecard compare changed metrics `0`.
- BR-064 separates family-judgment candidates before any threshold patch: most rows are common-cause block/hold, the remaining local morphology pool has `10` rows that still need family-shape evidence.
- BR-065 narrows those 10 local morphology rows: 8 remain recovery/recurrence-only holds, while 2 voltage-dominant hard-signal rows need partial-open vs measurement/reference review.
- BR-066 declares the evidence stack `handoff_ready_with_index`: start from BR-066 before opening scattered temp roots or proposing new rules.
- BR-067 checks those 2 rows for artifact/reference risk: both are physical-leaning voltage-axis review, but physical confirmation is still required before thresholding.
- BR-068 adds raw waveform proxy support for those 2 rows: both have complete raw coverage and persistent low-voltage/current-preserved timestamp morphology, but independent confirmation is still required.
- BR-069 confirms the independent confirmation layer is still open: both raw-supported rows have `0/2` required exact-panel axes met, so voltage-axis thresholding remains blocked.
- BR-070 converts the BR-069 gap into 2 high-priority exact-panel evidence requests so the next action is acquisition, not rule tuning.
- BR-071 packages the 50 strong common-cause hold rows as regression blockers so future rules cannot accidentally promote common-cause spatiality as panel-local evidence.
- BR-072 confirms conservative common-cause gating still has forward motion: exact closure is `0`, but `49` panels / `101` raw same-day direct rows are preserved as candidate reservoir plus report-lane/date-alignment structural blockers.
- BR-073 narrows those `49` structural blockers to `2` manual trace targets while keeping `47` rows as lane/date hold context and keeping promotion/engine/threshold sums at `0`.
- BR-074 closes those `2` manual trace targets without semantic loosening: `gangui` is raw-only report trace-only, `ktc_ess` is a post-current 71-day mismatch, and official/current bridge plus semantic patch sums stay `0`.
- BR-075 makes the common-cause boundary executable: BR-071~074 must pass 12 required prepatch gates before semantic loosening is reviewed, and the one raw-only near-anchor bridge remains context-only warning material.
- BR-076 moves BR-075 into the default combined algorithm prepatch runbook: future direct panel-engine algorithm review now expects panel-engine safety, fault-family regression, and common-cause semantic gates all to pass.
- BR-077 locks the current navigation checkpoint: the core safety/evidence lanes are not missing, but the latest evidence/handoff manifest must be refreshed before new scattered scans or algorithm proposals.
- BR-078 completes that refresh: BR-064 through BR-077 are now indexed by branch, evidence layer, judgment role, artifact path, temp-artifact repro command, next action, and patch authorization boundary.
- BR-079 freezes the current algorithm evolution map before code changes: 10 layers, 7 evidence gaps, and 6 ordered next actions; the next safe branch is subtype-truth backlog, not threshold or engine patch.
- BR-080 completes that subtype-truth backlog: 17 subtype rows, 12 P0 rows, exact truth support 0; next safe branch is episode truth map, not threshold or engine patch.
- BR-095 converts BR-093 voltage-preserved candidates into evidence requests only: request rows `14`, checklist rows `73`, raw waveform independent confirmation rows `0`, and truth/threshold/engine approvals all `0`.
- BR-095 keeps the 3 `gangui` same-root negative-overlap rows behind `counterexample_clearance` before any truth rebuild.
- BR-096 closes raw/source traceability for BR-095 rows: `14/14` request rows have raw-source trace attached, `1698/1698` raw file refs found, but independent physical/maintenance confirmation remains `0`.
- BR-097 separates vendor pattern support from field confirmation: exact vendor rows exist for `9/14`, positive/likely vendor support exists for `7/14`, but vendor field-confirmed rows, independent confirmation rows, truth approval, threshold approval, and engine patch approval all remain `0`.
- BR-098 confirms that same-site field-confirmed examples are reference-only when `panel_id` does not match: target rows with same-site references `3`, exact field-confirmed target rows `0`, independent confirmation attached rows `0`, explicit all-clearance rows `0`, truth intake ready rows `0`.
- BR-099 turns the remaining BR-098 blockers into collector-facing work: queue rows `45`, open required axes `45`, collector template rows `45`, and truth/threshold/operator/engine approvals remain `0`.

## Next Safe Implementation
- keep `promotion_decision_bucket` as an audit/shadow field only.
- use bucket-specific review packets before proposing any operator-facing event semantic change.
- before any new production semantic patch, keep duration/gap/continuity/spatiality separated by fault-family threshold candidates.
- adjudicate BR-023 `group_off` cluster boundaries and `strict_trigger_proximal` vs secondary-window evidence before any subtype promotion discussion.
- before generating more packet branches, prefer a tracked packet generator or an exact one-shot reproduction script.
- keep `subtype_production_write_allowed = 0` until a fresh tri-site review proves a subtype can be raised without final verdict drift.
- after BR-043, use the evidence manifest/consolidated pack root as the default read base, then implement `common_cause_synchrony_axis`, then do a cross-axis review, then rerun exact same-day missing-family search, and only then reopen algorithm gating.
- after BR-052, inspect `no_report_heuristic_match` as a report-lane / heuristic attachment gap before reopening any algorithm gating discussion.
- after BR-053, run any future `pv_ae/panel_day_engine.py` patch through `panel_day_engine_patch_safety_gate_v1` before code review or commit.
- after BR-054, treat the tightened pair/hash/deletion/relevance checks as the effective safety gate contract.
- after BR-056, do not patch the engine for no-report heuristic rows or near-anchor non-fault morphology observations; continue exact-family closure search with stronger fault-family evidence.
- after BR-057, keep target exact-family closure open and package the 11 regression/pressure seeds separately before any algorithm gating discussion.
- after BR-058, any future algorithm patch should first run/check the packet as regression pressure and prove it does not convert packet rows into target exact closure or direct operator promotion.
- after BR-059, run `check_panel_day_engine_fault_family_regression_prepatch_gate_v1.py` before any direct panel-engine algorithm patch review.
- after BR-060, use `check_panel_day_engine_algorithm_prepatch_runbook_v1.py` as the default combined prepatch command before direct panel-engine algorithm patch review.
- after BR-061, compare future post-patch outputs against `result_delta_scorecard_v1` before claiming result or performance improvement.
- after BR-062, use `compare_panel_day_engine_result_delta_scorecards_v1.py` for the actual before/after comparison.
- after BR-063, use source/package mirror + safety review + prepatch runbook + scorecard + compare as the minimum direct engine patch pattern.
- after BR-064, inspect `local_morphology_family_candidate_review` rows for family-shape evidence before any fault-family threshold or semantic engine patch.
- after BR-065, inspect only the 2 `voltage_dominant_hard_signal_review` rows before proposing any family-specific threshold; keep the 8 recovery-only rows on hold.
- after BR-066, use the handoff index as the default entry point for continuation; if BR-064/065 cannot be reproduced from it, fix handoff before adding new evidence.
- after BR-067, do not treat physical-leaning voltage-axis rows as confirmed faults; collect physical confirmation evidence first.
- after BR-068, use raw waveform support as stronger review evidence, but require an independent physical-confirmation checklist before thresholding.
- after BR-069, do not propose voltage-axis thresholding until exact-panel direct physical measurement and maintenance/inspection evidence are attached.
- after BR-070, attach exact-panel evidence and rerun BR-069/070 before reopening any voltage-axis threshold proposal.
- after BR-071, run or inspect the strong common-cause blocker packet before any semantic algorithm patch that could affect panel-local promotion.
- after BR-072, use the common-cause exact seed search before loosening common-cause semantics: raw direct rows are search reservoir only until report-layer same-day closure or a scoped structural-blocker patch target is proven.
- after BR-073, inspect the `gangui` rawonly-near-anchor row and the `ktc_ess` 71-day current-date-displaced row before any common-cause semantic loosening; the remaining 47 blockers stay hold/context.
- after BR-074, do not use raw-only near-anchor traces or post-current date-displaced common-cause rows as official/current closure; preserve BR-071~074 as regression/hold evidence for future semantic patches.
- after BR-075, any common-cause semantic patch must run `check_panel_day_engine_common_cause_semantic_prepatch_gate_v1.py` first; passing the gate is a safety precondition, not patch approval.
- after BR-076, use `check_panel_day_engine_algorithm_prepatch_runbook_v1.py` as the default 3-gate prepatch command before direct `panel_day_engine.py` algorithm review.
- after BR-077, use `OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_077_PROJECT_COMPLETION_CHECKPOINT_V1.md` as the current whole-project read map; the next safest branch is a latest evidence/handoff manifest refresh covering BR-064 through BR-076.
- after BR-078, use `/private/tmp/latest_evidence_handoff_manifest_br078_check/panel_day_engine_latest_evidence_handoff_manifest_v1.csv` and `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_078_LATEST_EVIDENCE_HANDOFF_MANIFEST_V1.md` as the current evidence/handoff entry point before new evidence scans or algorithm proposals.
- after BR-079, use `/private/tmp/panel_day_engine_algorithm_evolution_map_br079_check/panel_day_engine_algorithm_evolution_layer_map_v1.csv` and `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_079_ALGORITHM_EVOLUTION_MAP_V1.md` as the current algorithm-evolution map; build subtype-truth backlog before threshold replay or direct engine edits.
- after BR-080, use `/private/tmp/panel_day_engine_subtype_truth_expansion_backlog_br080_check/panel_day_engine_subtype_truth_expansion_backlog_v1.csv` and `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_080_SUBTYPE_TRUTH_EXPANSION_BACKLOG_V1.md` as the current subtype truth backlog; build episode truth map before threshold replay or direct engine edits.
- after BR-081, use `/private/tmp/panel_day_engine_episode_truth_map_br081_check/panel_day_engine_episode_truth_map_v1.csv` and `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_081_EPISODE_TRUTH_MAP_V1.md` as the current episode truth map; build episode truth review packets before threshold replay or direct engine edits.
- after BR-082, use `/private/tmp/panel_day_engine_episode_truth_review_packet_br082_check/panel_day_engine_episode_truth_review_packet_v1.csv` and `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_082_EPISODE_TRUTH_REVIEW_PACKET_V1.md` as the current review packet; attach reviewed truth labels before threshold replay or direct engine edits.
- after BR-083, use `/private/tmp/panel_day_engine_direction_assumption_audit_br083_check/panel_day_engine_direction_assumption_audit_v1.csv` and `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_083_DIRECTION_ASSUMPTION_AUDIT_V1.md` as the current direction guard; if any P0 audit fails, stop before reviewed truth rows, threshold replay, or direct engine edits.
- after BR-084, use `/private/tmp/panel_day_engine_reviewed_episode_truth_rows_br084_check/panel_day_engine_reviewed_episode_truth_rows_v1.csv` and `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_084_REVIEWED_EPISODE_TRUTH_ROWS_V1.md` as the current truth-intake table; threshold replay remains blocked until reviewer labels and evidence paths create positive/negative replay-ready rows.
- after BR-085, use `/private/tmp/panel_day_engine_episode_truth_evidence_attachment_br085_check/panel_day_engine_episode_truth_review_input_template_v1.csv` and `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_085_EPISODE_TRUTH_EVIDENCE_ATTACHMENT_V1.md` as the current evidence attachment packet; fill the template and rebuild BR-084 before any subtype-conditioned threshold replay.
- after BR-086, use `/private/tmp/panel_day_engine_episode_truth_source_trace_audit_br086_check/panel_day_engine_episode_truth_source_trace_audit_v1.csv` and `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_086_EPISODE_TRUTH_SOURCE_TRACE_AUDIT_V1.md` as the current source-trace guard; source trace readiness is not a truth label, so fill BR-085 manually and rebuild BR-084 before threshold replay.
- after BR-087, use `/private/tmp/panel_day_engine_episode_truth_adjudication_worksheet_br087_check/panel_day_engine_episode_truth_adjudication_worksheet_v1.csv` and `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_087_EPISODE_TRUTH_ADJUDICATION_WORKSHEET_V1.md` as the current adjudication worksheet; suggested directions are guidance only, so manually fill a copy of the draft input and rebuild BR-084 before threshold replay.
- after BR-088, use `/private/tmp/panel_day_engine_episode_truth_conservative_adjudication_br088_check/panel_day_engine_episode_truth_review_input_conservative_v1.csv` and `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_088_EPISODE_TRUTH_CONSERVATIVE_ADJUDICATION_V1.md` as the current negative counterexample input; BR-084 now has negative replay-ready rows 9 but positive rows 0, so threshold replay remains blocked until durable positive evidence is attached.
- after BR-089, use `/private/tmp/panel_day_engine_episode_truth_durable_shape_review_br089_check/panel_day_engine_episode_truth_review_input_mixed_v1.csv` and `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_089_EPISODE_TRUTH_DURABLE_SHAPE_REVIEW_V1.md` as the current mixed truth input; pilot replay review is allowed as evidence assessment only, while threshold tuning and direct engine edits remain blocked.
- after BR-090, use `/private/tmp/panel_day_engine_subtype_threshold_replay_pilot_br090_check/panel_day_engine_subtype_threshold_replay_pilot_summary_v1.csv` and `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_090_SUBTYPE_THRESHOLD_REPLAY_PILOT_V1.md` as the current replay evidence; voltage-preserved candidates are evidence-collection targets only, not tuning approval.
- after BR-091, use `/private/tmp/panel_day_engine_durable_hold_raw_shape_review_br091_check/panel_day_engine_durable_hold_raw_shape_review_summary_v1.csv` and `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_091_DURABLE_HOLD_RAW_SHAPE_REVIEW_V1.md` as the current hold-resolution evidence; do not mine the 6 holds for voltage-preserved positives, search elsewhere.
- after BR-092, use `/private/tmp/panel_day_engine_voltage_preserved_positive_search_br092_check/panel_day_engine_voltage_preserved_positive_search_candidates_v1.csv` and `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_092_VOLTAGE_PRESERVED_POSITIVE_SEARCH_V1.md` as the current voltage-preserved candidate reservoir; search hits are not truth labels, and known negative overlap blocks direct thresholding.
- after BR-092, the next safe branch is a confirmation packet for `manual_review_ready=1` candidates, with de-duplication and independent evidence before rebuilding truth rows or rerunning BR-090.
- after BR-093, use `/private/tmp/panel_day_engine_voltage_preserved_confirmation_packet_br093_check/panel_day_engine_voltage_preserved_confirmation_packet_v1.csv` and `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_093_VOLTAGE_PRESERVED_CONFIRMATION_PACKET_V1.md` as the current confirmation worklist; `86` source candidates are compressed to `14` panel tasks and `7` root families.
- after BR-093, attach independent confirmation to P0 packet rows before any positive truth rebuild; same-root known negative overlap family remains counterexample-guarded.
- after BR-094, use `--workspace-retention result-only` for routine runtime pack validation when full staged workspace forensics is not needed; keep `workspace_cleanup_v1.json` as the audit record and rerun with `full` only when staged `sites/` or workspace `data/` copies are explicitly required.
- after BR-095, attach evidence to the request/checklist rows first; do not rebuild confirmed-positive truth or rerun threshold replay until required independent/clearance axes are populated.
- after BR-096, treat raw/source traceability as closed for the 14 voltage-preserved requests; the next bottleneck is independent physical/maintenance evidence plus common-cause, measurement-artifact, and counterexample clearance.
- after BR-097, attach exact-panel physical/maintenance evidence for vendor-supported rows and resolve counterexample/blocker clearances before any truth rebuild, threshold replay, or `panel_day_engine.py` patch.
- after BR-098, fill `panel_day_engine_voltage_preserved_independent_confirmation_input_template_v1.csv` and `panel_day_engine_voltage_preserved_blocker_clearance_input_template_v1.csv` with exact-panel evidence before any confirmed-positive truth intake; same-site references and data-clearance candidates are not enough.
- after BR-099, use `panel_day_engine_voltage_preserved_truth_acquisition_collector_template_v1.csv` as the collection sheet; any collected evidence must be converted back into BR-098 inputs and re-attached before a separate truth-intake gate can be opened.
