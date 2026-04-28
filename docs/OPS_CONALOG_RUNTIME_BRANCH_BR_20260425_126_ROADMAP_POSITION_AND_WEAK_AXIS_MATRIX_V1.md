<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_ROADMAP_POSITION_AND_WEAK_AXIS_MATRIX_V1

## Purpose
- Scrape the accumulated roadmap/evidence design rather than relying on memory.
- Confirm the current roadmap position after BR-125.
- Identify weak verification/diagnosis axes and define the method for strengthening each axis.
- Keep this branch documentation/index-only:
  - no `panel_day_engine.py` patch
  - no production rerun
  - no canonical truth write
  - no threshold replay approval
  - no operator-facing verdict change

## Scrape Boundary
The scan used the clean continuation worktree:

| workspace | status | decision |
| --- | --- | --- |
| `/Users/b9gc/pvdiag_worktrees/postmerge_j` | clean before BR-126 scan; `codex/post-merge-base-j` ahead of origin | use for current roadmap/evidence confirmation |
| `/Users/b9gc/pvdiag` | dirty/divergent release/final-delivery working tree | do not mix into this roadmap confirmation |

## Scrape Result
| item | result | interpretation |
| --- | ---: | --- |
| repo files scanned across docs/research/release/pv_ae/app/paper_pack/outputs | `18768` | broad project scan, not a hand-picked subset |
| BR artifact files found in docs | `187` | includes `.md`, `.csv`, and `.json` branch artifacts |
| BR markdown documents found | `125` | every branch from BR-001 through BR-125 has a branch doc |
| BR numbers missing in `BR-001..BR-125` | `0` | roadmap numbering is complete |
| project-level non-BR design corpus rows added | `14` | captures the already-written project eval/reliability/support-gap/truth/acquisition/role/handoff/evidence docs that are not encoded by BR numbering alone |
| relevant `/private/tmp` check roots currently present | `49` | late-stage reproducible check roots remain; older roots may have been cleaned |
| relevant build/smoke/audit scripts matched | `118` | evidence is backed by builders/smokes, not only narrative docs |
| operator-facing change rows in active register | `1` | BR-016 only, limited to raw-only candidate runtime semantics |
| full related docs read after correction | `495` | includes docs, BR artifacts, decision logs, gate docs, project-level design docs, and release/handoff markdowns |

## Project-Level Design Corpus
The BR scrape alone is not enough because several key design documents were already written outside the `BR-*` sequence. Those documents are now indexed in:

- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_PROJECT_DESIGN_CORPUS_V1.csv`

This corpus is part of the roadmap evidence base, not an optional appendix.

The complete read evidence is recorded in:

- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_FULL_RELATED_DOC_READ_INDEX_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_FULL_RELATED_DOC_READ_SUMMARY_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_FULL_RELATED_DOC_READ_SUMMARY_V1.json`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_FULL_RELATED_DOC_READ_SYNTHESIS_V1.md`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_MASTER_CONTINUITY_REGISTER_V1.md`

| corpus area | existing design answer |
| --- | --- |
| project evaluation matrix | structural coverage, true case-level metrics, and retrospective proxy metrics must not be mixed |
| reliability audit | small-support perfect F1 is unstable and must be freeze-gated |
| support-gap audit | weak rows need support 5/10 planning and current-artifact feasibility checks |
| truth expansion plan | support gaps become concrete action classes, not vague "more data" notes |
| truth acquisition backlog | target-level needs must be deduplicated into real collection units |
| algorithm role gap pack | main event-type, kernel-log symptom naming, and GPV reference axes have different jobs |
| project handoff pack | benchmark reset and event/terminal-abrupt split are already documented |
| evidence matrix | panel-day row preservation is the lower-layer evidence contract |

## Roadmap Position
We are not at algorithm-complete. We are at the end of the first field-trial truth-intake safety runway.

Current coordinate:

| coordinate | value |
| --- | --- |
| latest completed design branch | `BR-20260425-125` |
| current confirmation branch | `BR-20260425-126` |
| current lane | MLPE field-trial capture/truth-intake infrastructure |
| real KTC ESS reviewed capture/label/preflight rows | `0` |
| current truth/threshold/engine approval posture | all locked to `0` |
| next allowed implementation | source/evidence materialization precheck package, only after reviewed preflight candidates exist |

The practical reading is:

1. Release/runtime base exists.
2. Evidence and safety rails are substantially stronger than release closeout.
3. The algorithm-evolution map is frozen: subtype truth, episode truth, threshold replay, 3-gate prepatch, then one shadow-applied rule.
4. MLPE field-trial taxonomy/capture/label/truth-gate/preflight plumbing exists.
5. Real labels are still absent, so performance and diagnosis-finality claims remain blocked.

## Phase Inventory
Detailed phase inventory is recorded in:

- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_ROADMAP_PHASE_INVENTORY_V1.csv`

Summary:

| phase | branch range | meaning |
| --- | --- | --- |
| P1 | BR-001..BR-016 | onset guard and first narrow semantic patch |
| P2 | BR-017..BR-024 | morphology, subtype hypotheses, blocker packets |
| P3 | BR-025..BR-039 | evidence rubric and gap classification |
| P4 | BR-040..BR-051 | sidecars, manifests, role/mirror/builder confusion reduction |
| P5 | BR-052..BR-063 | panel-engine safety gates and no-drift validation |
| P6 | BR-064..BR-076 | family judgment, physical evidence, common-cause gates |
| P7 | BR-077..BR-079 | checkpoint, handoff refresh, algorithm-evolution map |
| P8 | BR-080..BR-090 | subtype/episode truth and threshold replay pilot |
| P9 | BR-091..BR-100 | voltage-preserved acquisition and unlabeled frontier |
| P10 | BR-101..BR-125 | MLPE field-trial capture/truth-intake pipeline |
| non-BR corpus | project-level docs | evaluation matrix, reliability, support gap, truth expansion, acquisition backlog, role boundary, handoff, and evidence matrix |

## Weak Axis Matrix
Detailed weak-axis matrix is recorded in:

- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_WEAK_AXIS_STRENGTHENING_MATRIX_V1.csv`

Priority weak axes:

| axis | current weakness | strengthening method |
| --- | --- | --- |
| truth label and episode ground truth | real KTC ESS rows are still 0 | source/evidence materialization precheck, then sidecar truth intake only after all clearances pass |
| common-cause vs panel-local separation | many candidates are root/site/bulk screen material | synchrony, peer breadth, timing clearance, negative controls, and regression blockers |
| physical/electrical confirmation | voltage/raw support exists but independent confirmation is 0 | exact-panel raw slices plus maintenance/inspection or field-measurement confirmation |
| measurement/communication artifact discrimination | schema exists, real artifact-cleared rows do not | timestamp quality, communication status, optimizer state, dropout/stuck/impossible-value checks |
| MLPE control vs panel physical fault | optimizer/control behavior can mimic panel faults | separate MLPE/control labels, injection mode/strength, optimizer state, and controlled MLPE injections |
| subtype granularity and threshold calibration | subtype hypotheses exist, support is thin | morphology atlas plus family-specific replay after enough positives/negatives |
| performance claim and result delta | no accuracy/F1/lead-time claim is supported yet | truth-sidecar baseline vs candidate replay with site-stratified metrics and false-alarm cost |
| handoff/navigation/artifact sprawl | map exists but can become scattered again | active register, phase inventory, weak-axis matrix, latest manifest, and result-only retention |

## Diagnosis Methodology Going Forward
The diagnosis strategy should be hierarchical, not one-threshold-fits-all.

1. First decide whether the row is eligible for panel-local interpretation.
   - common-cause, group-side, measurement artifact, and MLPE/control blockers are checked before panel physical promotion.
2. Then assign fault-family/subtype as a hypothesis.
   - subtype is not a final operator label until enough truth and multi-axis support exist.
3. Then evaluate family-specific evidence.
   - degradation/soiling/shading require duration/repetition.
   - connection/open faults require timing, recurrence, and abrupt/recovery shape.
   - diode/submodule faults require V/I/P morphology.
   - MLPE/control faults require optimizer state and injection/control metadata.
   - telemetry artifacts require timestamp/communication/data-quality clearance.
4. Then replay thresholds against sidecar truth.
   - no threshold update should be accepted without positives, negatives, counterexamples, common-cause blockers, and measurement-artifact blockers.
5. Finally, move production semantics last.
   - run panel-engine safety, family regression, common-cause semantic gate, scorecard compare, and package/source mirror checks before any production patch.

## Decision
- Treat BR-126 as the current roadmap-position confirmation.
- BR-150 should not be read as full algorithm completion.
- BR-150 is better treated as the end of the pre-label field-trial safety runway: taxonomy, capture, truth-intake, materialization, replay, and prepatch gates should be ready.
- The next safe branch is not `panel_day_engine.py` tuning. The next safe branch is a source/evidence materialization precheck package, and it should only activate when reviewed preflight candidates exist.
- Future roadmap answers must read both:
  - the numbered BR register/branch docs
  - the project-level non-BR design corpus
  - the full related-doc read index/synthesis
  - the master continuity register
  before claiming what has or has not been designed.

## Not Allowed From This Branch Alone
- no performance improvement claim
- no new truth label write
- no direct canonical truth materialization
- no threshold loosening
- no common-cause semantic loosening
- no MLPE/control collapse into panel physical fault
- no direct `panel_day_engine.py` behavior patch

## Repro Commands
Before patch:

```bash
git status --short --branch
git worktree list
```

Scrape commands:

```bash
rg --files docs research release pv_ae app paper_pack outputs 2>/dev/null | wc -l
rg --files docs research release pv_ae app paper_pack outputs 2>/dev/null | rg '(BR_|BR-|ROADMAP|GATE|EVIDENCE|HANDOFF|REGISTER|MLPE|TRUTH|VALIDATOR|TAXONOMY|ONEPAGER|data_dictionary|paper_pack|audit|summary|manifest)'
python - <<'PY'
from pathlib import Path
import re
paths = []
for base in ['docs','research/prognostics','release/conalog_full_runtime_v1','release/final_delivery_v1','paper_pack','outputs']:
    p = Path(base)
    if p.exists():
        paths.extend([x for x in p.rglob('*') if x.is_file()])
br_docs = []
for p in paths:
    m = re.search(r'BR_(\d{8})_(\d{3})_', p.name)
    if m:
        br_docs.append((int(m.group(2)), str(p), p.suffix.lower()))
nums = sorted(set(n for n, _, _ in br_docs))
print(len(paths), len(br_docs), len(nums), nums[0], nums[-1], [n for n in range(nums[0], nums[-1] + 1) if n not in nums])
PY
```

After patch:

```bash
git diff --check
python3 -m py_compile pv_ae/panel_day_engine.py
```
