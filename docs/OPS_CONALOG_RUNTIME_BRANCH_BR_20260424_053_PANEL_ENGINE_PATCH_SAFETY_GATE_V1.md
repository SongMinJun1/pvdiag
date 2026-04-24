<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_053_PANEL_ENGINE_PATCH_SAFETY_GATE_V1

## Purpose
- `pv_ae/panel_day_engine.py`를 직접 수정하기 전에, 엔진 패치가 반드시 통과해야 하는 최소 안전장치를 코드화한다.
- 이 패치는 runtime algorithm rule patch가 아니다.
- 목적은 다음 단계의 `no_report_heuristic_match` 또는 이후 `panel_day_engine.py` 패치가 문서, shadow/safety evidence, smoke, source/package mirror, 공개 동작 문서 갱신 없이 들어가는 것을 막는 것이다.

## Safety Gate
- script:
  - `research/prognostics/check_panel_day_engine_patch_safety_gate_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_patch_safety_gate_v1.py`

## Gate Contract
- `G00_engine_change_detection`
  - source or packaged panel engine touch 여부를 먼저 판정한다.
- `G01_branch_doc_present`
  - 엔진 변경 시 BR 문서가 있어야 한다.
- `G02_decision_log_present`
  - 엔진 변경 시 별도 decision log가 있어야 한다.
- `G03_shadow_or_safety_builder_present`
  - 엔진 변경 시 재현 가능한 shadow/safety/audit/review builder가 있어야 한다.
- `G04_smoke_test_present`
  - 엔진 변경 시 smoke test가 있어야 한다.
- `G05_active_register_updated`
  - 엔진 변경 시 active branch register가 갱신되어야 한다.
- `G06_gate7_order_updated`
  - 엔진 변경 시 Gate7 order 문서가 갱신 또는 재확인되어야 한다.
- `G07_public_behavior_doc_present`
  - algorithm behavior 변경 가능성이 있으면 `ONEPAGER.md`, `data_dictionary_paper.md`, 또는 `paper_pack/` 문서가 같이 갱신되어야 한다.
- `G08_source_package_sync_present`
  - source engine 변경 시 packaged mirror도 같은 safety packet에 포함되어야 한다.
- `G09_no_large_data_paths`
  - `data/<site>/raw` 또는 `data/<site>/out` 대용량/생성 데이터는 엔진 safety patch에 포함하면 안 된다.
- BR-054 tightened this initial contract:
  - package-only engine changes are also blocked.
  - source/package content equality is checked by SHA-256.
  - deleted files cannot satisfy required evidence gates.
  - docs/builders/smokes must be panel-engine related, not just filename-shaped.

## Current Patch Result
- current patch has no engine code change:
  - `engine_change_detected = 0`
  - `source_engine_changed = 0`
  - `package_engine_changed = 0`
- therefore engine-specific required gates are not applicable in this patch.
- the gate output still verifies that the current patch packet itself is clean.

## Smoke Coverage
- `no_engine` synthetic case:
  - docs/safety-only changes pass.
- `missing` synthetic case:
  - `pv_ae/panel_day_engine.py` only fails.
  - required failures include missing branch doc and missing source/package sync.
- `full` synthetic case:
  - source engine, package engine, branch doc, decision log, register, Gate7, public behavior doc, shadow builder, and smoke test pass together.

## Outputs
- `/private/tmp/panel_engine_patch_safety_gate_check/panel_day_engine_patch_safety_gate_v1.csv`
- `/private/tmp/panel_engine_patch_safety_gate_check/panel_day_engine_patch_safety_gate_summary_v1.csv`

## Decision
- Accept `panel_day_engine_patch_safety_gate_v1` as a pre-engine-change safety gate.
- Do not patch `pv_ae/panel_day_engine.py` until this gate says the proposed packet is complete.
- Keep the next evidence task as `no_report_heuristic_match` decomposition, but run it under this safety discipline.
- Effective gate semantics are tightened by BR-054.

## Repro Command
```bash
python3 research/prognostics/check_panel_day_engine_patch_safety_gate_v1.py --output-dir /private/tmp/panel_engine_patch_safety_gate_check
```
