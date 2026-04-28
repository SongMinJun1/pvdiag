<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_MASTER_CONTINUITY_REGISTER_V1

## Purpose
- Preserve the full project continuity so future work does not skip earlier design records.
- Connect what was already written, what we intended to do, what is blocked, and what must happen next.
- This is not a short summary and not a new algorithm proposal.
- This is the current "do not lose the thread" register.

## Read-First Rule
Before answering "where are we", "what is next", or "can we patch `panel_day_engine.py`", read these files together:

| required read base | role |
| --- | --- |
| `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md` | current branch and decision locks |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_FULL_RELATED_DOC_READ_INDEX_V1.csv` | full related-doc read evidence, 495 files |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_PROJECT_DESIGN_CORPUS_V1.csv` | non-BR project design spine |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_ROADMAP_PHASE_INVENTORY_V1.csv` | phase inventory; phase ids are not P0/P1/P2 priorities |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_PRIORITY_GATE_MAP_V1.csv` | P0/P1/P2 priority gates |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_WEAK_AXIS_STRENGTHENING_MATRIX_V1.csv` | weak diagnosis/validation axes |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_DIAGNOSTIC_SKILL_SHADOW_BACKLOG_V1.csv` | diagnostic skill additions; shadow/audit only, not production verdict changes |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_FAULT_FAMILY_EVIDENCE_COVERAGE_MATRIX_V1.csv` | fault-family required/supporting/blocking axes and current diagnostic skill availability |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_127_SOURCE_EVIDENCE_MATERIALIZATION_PREFLIGHT_V1.md` | fail-closed source/evidence materialization precheck before sidecar truth package |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_128_TO_150_EXECUTION_QUEUE_V1.csv` | ordered BR-128..BR-150 pre-label runway queue with open/blocked status |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_129_REAL_CAPTURE_INTAKE_CONTRACT_V1.md` | fail-closed real KTC ESS capture CSV intake contract before BR-130 |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_131_SOURCE_EVIDENCE_RESOLVER_CONTRACT_V1.md` | fail-closed source/evidence resolver contract before BR-132 |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_133_COMMON_CAUSE_CLEARANCE_CONTRACT_V1.md` | fail-closed common-cause clearance contract before BR-134 |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_135_ARTIFACT_MLPE_CONTROL_CLEARANCE_CONTRACT_V1.md` | fail-closed artifact/MLPE-control clearance contract before BR-136 |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_137_SIDECAR_TRUTH_PACKAGE_CONTRACT_V1.md` | fail-closed sidecar truth package contract before BR-138 |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_139_TRUTH_REPLAY_SCORECARD_CONTRACT_V1.md` | fail-closed truth replay scorecard contract before BR-140 |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_143_PANEL_ENGINE_PREPATCH_GATE_REFRESH_V1.md` | fail-closed panel-engine prepatch gate refresh before BR-144 |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_148_PRECHECK_COMMIT_SCOPE_DRY_RUN_AUDIT_V1.md` | dry-run commit-scope audit for the current blocked-state runway |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_149_PRECHECK_BLOCKED_STATE_READINESS_HANDOFF_V1.md` | blocked-state readiness/handoff audit for the current runway |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_150_PRECHECK_PRELABEL_RUNWAY_CHECKPOINT_V1.md` | pre-label runway checkpoint for the current blocked state |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_FULL_RELATED_DOC_READ_SYNTHESIS_V1.md` | full-read interpretation |

## Current Coordinate
| item | current answer |
| --- | --- |
| current branch point | `BR-150-precheck` |
| meaning | pre-label runway checkpoint is complete; official BR-150 and algorithm completion remain blocked until real data/replay/selected-rule/shadow evidence exists |
| full corpus read | `495` files / `41375` lines |
| actual algorithm-complete status | not complete |
| actual current lane | MLPE field-trial truth-intake infrastructure and continuity control |
| current real KTC ESS capture/label/preflight rows | `0` until user supplies real CSV/labels |
| current production patch posture | blocked except separately gated changes |
| current performance-improvement claim posture | blocked until truth-label evaluation |

## Already Built Design Spine
| spine | already written intent | do not forget |
| --- | --- | --- |
| evidence matrix | preserve panel-day evidence rows before grouping | do not filter away row-level evidence before episode/incident work |
| project eval matrix | split structural coverage, true case metrics, and retrospective proxy metrics | do not attach precision/recall/F1 to every row blindly |
| reliability audit | small support can make perfect F1 unstable | do not freeze weak rows as final conclusions |
| support gap audit | quantify support 5/10 and current-artifact feasibility | do not say "need more data" without a support target |
| truth expansion plan | turn weak scopes into action classes | collect precursor fault cases, common-cause site events, abrupt panel cases, or workflow observations as needed |
| truth acquisition backlog | deduplicate target rows into collection units | count `fault_case`, `panel_case`, `site_event`, and `workflow_observation`, not duplicated target rows |
| algorithm role gap pack | split main event-type, kernel-log symptom naming, and GPV reference roles | do not force physical root-cause naming into the main event-type axis |
| project handoff pack | preserve benchmark reset and c429 event/terminal split | do not mix event type with final failure shape |
| MLPE field-trial taxonomy | keep MLPE/control, telemetry artifact, common cause, and panel physical families separate | do not collapse MLPE behavior into panel physical fault |

## Already Built Runtime/BR Spine
| range | already done | status |
| --- | --- | --- |
| BR-001..BR-016 | G1/onset/backdating analysis and one narrow raw-only semantic patch | one intentional runtime semantic change; broad promotion still closed |
| BR-017..BR-024 | morphology, subtype hypotheses, confidence/blocker split, review packets | subtype remains shadow/review only |
| BR-025..BR-039 | stable/runtime boundary, score/projection precedence, evidence/gap rubrics | evidence-first/blocker-first rule locked |
| BR-040..BR-051 | sidecars, manifest roots, role/mirror/builder confusion reduction | reproducible navigation exists |
| BR-052..BR-063 | engine safety, regression gates, result-delta scorecards, no-drift cleanup | direct engine edits are gated |
| BR-064..BR-076 | family judgment, physical evidence requests, common-cause blockers, 3-gate prepatch | threshold/common-cause loosening blocked |
| BR-077..BR-079 | checkpoint, latest handoff, algorithm evolution map | P0/P1/P2 evidence gaps are explicit |
| BR-080..BR-090 | subtype truth, episode truth, conservative adjudication, replay pilot | threshold approval remains 0 |
| BR-091..BR-100 | voltage-preserved acquisition and unlabeled frontier | physical confirmation/truth/threshold approvals remain 0 |
| BR-101..BR-125 | MLPE capture, label, truth gate, reviewer/preflight pipeline | plumbing exists; real rows remain 0 |
| BR-126 | full related-doc read and continuity repair | order-0 diagnostic/family coverage complete |
| BR-127 | source/evidence materialization precheck | fail-closed bridge before sidecar truth package; real rows remain 0 |
| BR-128 | BR-128..BR-150 execution queue | remaining 23 pre-label runway points locked; open/blocked ordering is explicit |
| BR-129 | real capture intake contract | missing real CSV blocks closed; BR-130 remains blocked until user supplies KTC ESS capture bundle |
| BR-131 | source/evidence resolver contract | contract rows 6; missing real rows fail closed; BR-132 remains blocked until BR-130 real intake rows exist |
| BR-133 | common-cause clearance contract | contract rows 6; missing source/evidence rows fail closed; BR-134 remains blocked until BR-132 real source/evidence rows exist |
| BR-135 | artifact/MLPE-control clearance contract | contract rows 7; missing source/evidence and returned telemetry rows fail closed; BR-136 remains blocked until BR-132 rows and telemetry clearance exist |
| BR-137 | sidecar truth package contract | contract rows 8; current materialization candidates 0 so package rows 0; BR-138 remains blocked until clearance rows and sidecar package input exist |
| BR-139 | truth replay scorecard contract | contract rows 10; current sidecar truth events 0 so metrics rows 0; BR-140 remains blocked until sidecar truth rows and baseline/candidate replay outputs exist |
| BR-143 | panel-engine prepatch gate refresh | contract rows 12; current patch candidates 0 so prepatch-ready candidates 0; BR-144 remains blocked until selected rule/replay/shadow/runbook evidence exists |
| BR-148-precheck | commit-scope dry-run audit | dirty files 43; include candidates 43; risk files 0; issue rows 0; no engine source, large data, generated release JSON, or unclassified dirty paths |
| BR-149-precheck | blocked-state readiness/handoff audit | queue rows 23; complete 8; blocked 15; open 0; required docs/builders/smokes missing 0; issue rows 0; handoff-ready 1 |
| BR-150-precheck | pre-label runway checkpoint | checkpoint rows 8; passed 8; issue rows 0; prelabel-ready 1; algorithm/performance claims 0; real data required 1 |

## P0/P1/P2 Priority Gates
`P0/P1/P2` are priority gates, not roadmap phase ids.

| priority | gate family | meaning |
| --- | --- | --- |
| P0 | fault subtype truth | blocks subtype labels and subtype performance claims |
| P0 | episode ground truth | blocks onset/precursor threshold patch |
| P0 | independent physical confirmation | blocks voltage/submodule threshold loosening |
| P0 | official/current common-cause bridge | blocks common-cause semantic loosening |
| P0 | core MLPE injection/counterexample matrix | required before field-trial learning is credible |
| P1 | threshold calibration | follows P0 closure and enough positives/negatives |
| P1 | AE role boundary | blocks AE root-cause claims |
| P1 | MLPE MPPT/rapid-shutdown/degradation emulation | refines taxonomy after P0 cases |
| P2 | monolithic engine maintainability | useful, but must not be mixed with semantic change |
| P2 | compound fault | validates unknown/compound routing after single-family controls |

## Current Weak Axes
| weak axis | current state | intended strengthening |
| --- | --- | --- |
| truth labels and episode truth | real KTC ESS labels are not present yet; sidecar package contract exists with 0 current candidates | intake real CSV/labels through preflight, source trace, sidecar truth |
| common-cause vs panel-local | many candidates are root/site/bulk screened | synchrony, peer breadth, root/site clearance, blocker regression |
| physical/electrical confirmation | raw/voltage support exists but independent confirmation is thin | exact-panel waveform plus inspection/maintenance/field confirmation |
| measurement/communication artifact | schema/checklist and BR-135 clearance contract exist, real cleared rows are pending | timestamp quality, communication status, dropout/stuck/impossible-value checks |
| MLPE control vs panel physical | taxonomy and BR-135 clearance contract exist, real examples pending | optimizer state, injection mode/strength, control counterexamples |
| subtype/threshold calibration | hypotheses and pilot exist, support is thin | family-specific truth, positives/negatives, replay, counterexamples |
| performance claims | scorecard contracts exist but truth replay rows are absent | truth-sidecar replay and site/family stratified metrics |
| handoff/artifact sprawl | 495 related files exist | keep read index, design corpus, register, and synthesis current |

## Diagnostic Skill Additions
The added "skills" are diagnostic evidence axes, not Codex plugins and not immediate detector changes.

They are recorded in:

- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_DIAGNOSTIC_SKILL_SHADOW_BACKLOG_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_FAULT_FAMILY_EVIDENCE_COVERAGE_MATRIX_V1.csv`

Current decision:

| decision | rule |
| --- | --- |
| preserve existing core axes | `AE`, `DTW`, `HS`, `EWS`, and `Rule` are all retained as distinct roles |
| do not replace AE/DTW | AE is normal-pattern departure evidence; DTW is curve-shape distance evidence |
| add only as shadow/audit | CP, episode state, peer synchrony, physical invariant, artifact quality, and evidence vector are not production verdict inputs yet |
| avoid guesswork | each first output must be computed from observed raw/out fields or marked unavailable |
| no destructive use | new flags cannot delete precursor/fault candidates, suppress panel-local rows, or promote subtype labels before truth replay |
| defer label-bound models | shapelets, supervised classifiers, survival/hazard, and direct MLPE telemetry state require field-trial labels or returned telemetry |

## Intended Next Work
These are not optional "nice-to-have" items; they are the continuity path.

| order | intended work | blocked by | output expectation |
| ---: | --- | --- | --- |
| 0 | fault-family evidence coverage matrix plus diagnostic skill shadow backlog | complete for current BR-126 checkpoint; refresh only when taxonomy or returned field-trial evidence changes | for each fault family, define required axes, supporting axes, blocking axes, current gaps, field-trial collection needs, and whether each diagnostic skill is already present, partial, field-trial-required, or label-blocked |
| 1 | materialization precheck package | complete as fail-closed BR-127 contract; real candidate rows still absent | verify source/evidence/reviewer/write-boundary before any sidecar truth package; canonical truth remains untouched |
| 2 | real KTC ESS CSV/capture intake | user has not supplied CSV yet | validate schema, allowed values, timestamps, panel/root/device mapping |
| 3 | evidence resolver for real rows | contract complete; BR-132 still needs BR-130 real intake rows and raw/evidence paths | attach source rows, raw slices, evidence files, and path status |
| 4 | clearance gates | common-cause and artifact/MLPE-control contracts complete; real clearance runs remain blocked | mark panel-local eligibility conservatively |
| 5 | truth sidecar package | contract complete; real clearance rows and reviewer package input remain absent | candidate truth rows remain sidecar, canonical truth untouched |
| 6 | replay/evaluation | contract complete; sidecar truth support and baseline/candidate replay rows absent | baseline vs candidate scorecard, lead time, false alarm, site/family split |
| 7 | threshold/rule shadow candidate | replay evidence | exactly one candidate rule should be shadow-applied first |
| 8 | panel engine prepatch | contract complete as BR-143; still blocked by absent selected rule, replay support, shadow result, and prepatch-ready candidate | only then consider `panel_day_engine.py` behavior patch |
| 9 | fresh rerun/result delta | prepatch pass | prove intended-only drift |
| 10 | release/handoff sync | rerun and docs pass | onepager/data dictionary/release docs aligned |
| 11 | BR-128..BR-150 queue execution | BR-128 queue locked; real-data branches remain blocked until CSV/capture bundle arrives | proceed one branch/gate at a time; open-now contract gates may be built fail-closed |
| 12 | current blocked-state commit-scope audit | complete as BR-148-precheck; official BR-148 still waits for BR-147 | use the file manifest if staging is requested; do not use `git add .` blindly |
| 13 | current blocked-state readiness handoff | complete as BR-149-precheck; official BR-149 still waits for BR-148 | safe to hand off; not safe to patch engine without real data/replay/shadow evidence |
| 14 | current pre-label runway checkpoint | complete as BR-150-precheck; official BR-150 still waits for BR-149 | ready to receive real data/labels safely; not algorithm-complete |

## Explicit Non-Goals Right Now
- Do not tune `panel_day_engine.py` just because the roadmap is clearer.
- Do not call BR-150 a completion point.
- Do not convert sidecar truth into canonical truth without a separate write-boundary branch.
- Do not claim performance improvement without truth-label replay.
- Do not collapse MLPE/control, telemetry artifact, common-cause, and panel physical faults.
- Do not answer roadmap questions from memory alone.

## Current Correction
Earlier BR-126 drafts under-read the project by focusing too narrowly on BR files and then by summarizing too aggressively.
This register corrects that by making the full read index, non-BR design corpus, priority gates, weak axes, and intended next work part of one continuity contract.
