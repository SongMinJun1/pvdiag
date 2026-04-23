<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_016_G1_SEMANTIC_APPLY_V1

## [BR-20260423-016] G1 semantic apply
- `status`: semantic_patch_validated
- `branch_type`: B
- `current_gate`: Gate 7
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23

## 1. 이슈 요약
- BR-015에서 G1 shadow 후보 `7`건을 `apply-ready 6`건과 `hold-review 1`건으로 분리했다.
- BR-016은 그중 `strict_trigger_proximal_common_cause_flag = 1`인 `6`건만 runtime semantic에 반영한다.
- 제외 행 `e089076c-92c1-4365-8641-2182b4f274e6.1.9`는 G1 후보이지만 strict-trigger 근접 common-cause support가 없어 첫 패치에서 제외한다.

## 2. 적용 규칙
- apply if:
  - `g1_suppressed_event_shadow_flag = 1`
  - `strict_trigger_proximal_common_cause_flag = 1`
- hold if:
  - `g1_suppressed_event_shadow_flag = 1`
  - `strict_trigger_proximal_common_cause_flag = 0`
- applied semantics:
  - `전조형 고장 -> 급작 고장`
  - `진행성 악화 -> 급작 발생`
  - `전조흔적_flag 1 -> 0`
  - `순수급작_flag 0 -> 1`
  - `전조평가셋편입_flag 1 -> 0`
  - `급작평가셋편입_flag 0 -> 1`
  - operator-facing precursor dates/markers are blanked for applied rows.

## 3. Scope guard
- root strict published current table is unchanged:
  - `published_raw_only_current_changed_rows = 0`
- raw-only candidate chain changes only the 6 apply-ready rows:
  - `raw_only_chain_fault_changed_rows = 6`
  - changed columns: `사건유형_ko`, `최종고장양상_ko`
- runtime final verdict changes 6 rows:
  - changed columns: `14`
  - changed cells: `84`
- BR-015 preview listed 13 operator-facing columns. BR-016 also changes `대표판정_ko`, which is a derived consistency column tied to `사건유형_ko`.

## 4. Cause-candidate guard
- First implementation attempt showed downstream cause-candidate rank drift in `2순위_의심원인_ko`.
- BR-016 explicitly prevents that drift:
  - G1-applied rows keep cause-candidate temporal scoring on the pre-guard temporal basis.
  - `heuristic_top_candidate_rank_drift_rows = 0`
- The heuristic table still records the new event/final pattern and a memo note:
  - changed columns: `사건유형_ko`, `최종고장양상_ko`, `원인후보_해석메모_ko`

## 5. Evidence outputs
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_016_G1_SEMANTIC_APPLY_PANEL_STATUS_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_016_G1_SEMANTIC_APPLY_FINAL_VERDICT_DIFF_LONG_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_016_G1_SEMANTIC_APPLY_RAW_ONLY_FAULT_DIFF_LONG_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_016_G1_SEMANTIC_APPLY_HEURISTIC_DIFF_LONG_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_016_G1_SEMANTIC_APPLY_SUMMARY_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_016_G1_SEMANTIC_APPLY_VALIDATION_V1.json`

## 6. Before/after reproduction
- before command:
  - `python release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/br016_baseline_tri_site_v1 --sites conalog,gangui,ktc_ess --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data`
- after command:
  - `python release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/br016_after3_tri_site_v1 --sites conalog,gangui,ktc_ess --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data`
- validation command:
  - `python -m py_compile pv_ae/panel_day_engine.py research/prognostics/runtime_rawonly_chain_common_v1.py research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py research/prognostics/build_panel_day_engine_runtime_heuristic_v1.py release/conalog_full_runtime_v1/package/research/prognostics/runtime_rawonly_chain_common_v1.py release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_heuristic_v1.py`

## 7. Decision
- The 6 strict-proximal-supported G1 rows are safe to apply as a narrow runtime semantic patch.
- The 1 hold-review row remains excluded.
- This branch does not broaden secondary-window precursor promotion.
