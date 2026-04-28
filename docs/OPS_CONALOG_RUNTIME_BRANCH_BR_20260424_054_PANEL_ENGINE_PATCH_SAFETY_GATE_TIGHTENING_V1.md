<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_054_PANEL_ENGINE_PATCH_SAFETY_GATE_TIGHTENING_V1

## Purpose
- BR-053 safety gate의 허점을 리뷰하고, 엔진 패치 전에 통과해야 하는 조건을 더 정확하게 조인다.
- 이 패치는 `pv_ae/panel_day_engine.py` 동작 변경이 아니다.
- 목적은 “파일명이 맞아서 통과”하는 gate가 아니라 “source/package/content/evidence가 실제로 맞아서 통과”하는 gate로 바꾸는 것이다.

## Review Findings From BR-053
- package-only engine change가 통과할 수 있었다.
- source/package가 둘 다 changed list에 있어도 실제 내용이 다른지 확인하지 않았다.
- deleted file도 path pattern만 맞으면 evidence로 카운트될 수 있었다.
- BR 문서, decision log, smoke/builder가 현재 panel engine patch와 관련 있는지 본문/경로 기준으로 확인하지 않았다.

## Tightened Gate Changes
- changed path reader now tracks git status:
  - `M`, `A`, `D`, rename-like records are parsed from `git diff --name-status`.
  - newline-only synthetic changed-path files still work and default to modified.
- required evidence is counted only when active and existing:
  - deleted docs/smoke/build/public docs cannot satisfy the gate.
- branch docs, decision logs, builders, smoke tests, and public behavior docs must be panel-engine related:
  - path/content must contain panel-engine terms such as `panel_day_engine`.
- engine mirror rule is now bidirectional:
  - source-only engine change fails.
  - package-only engine change fails.
- source/package content equality is now checked by SHA-256:
  - both engine files must be byte-identical after the patch.

## Updated Required Gates
- `G08_source_package_pair_changed_together`
  - source and packaged panel engine must move together.
- `G09_source_package_content_equal`
  - source and packaged panel engine must be byte-identical.
- `G10_no_deleted_required_evidence`
  - deleted required evidence cannot satisfy a safety gate.
- `G11_no_large_data_paths`
  - data raw/out payloads remain blocked.

## Smoke Coverage Added
- `package_only`:
  - packaged engine plus docs/smoke/shadow still fails without source engine.
- `mismatch`:
  - source and package engine both listed, but divergent content fails.
- `deleted_evidence`:
  - deleted BR doc fails both branch-doc and deleted-evidence gates.
- existing coverage remains:
  - docs/safety-only passes.
  - source-only fails.
  - complete source/package/doc/smoke/shadow packet passes.

## Outputs
- `/private/tmp/panel_engine_patch_safety_gate_check/panel_day_engine_patch_safety_gate_v1.csv`
- `/private/tmp/panel_engine_patch_safety_gate_check/panel_day_engine_patch_safety_gate_summary_v1.csv`

## Decision
- Accept BR-054 as the effective panel-engine safety gate contract.
- BR-053 remains the initial gate introduction, but BR-054 supersedes its weaker mirror/evidence interpretation.
- Do not proceed to any direct `pv_ae/panel_day_engine.py` patch until BR-054 gate semantics pass.

## Repro Command
```bash
python3 research/prognostics/check_panel_day_engine_patch_safety_gate_v1.py --output-dir /private/tmp/panel_engine_patch_safety_gate_check
```
