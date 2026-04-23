<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_012_G1_SUPPRESSION_SHADOW_SIMULATION_V1

## [BR-20260423-012] G1 suppression shadow simulation
- `status`: shadow_simulation_generated
- `branch_type`: B
- `current_gate`: Gate 3
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23

## 1. 이슈 요약
- BR-011에서 `blocked_cluster_risk` 26건은 `blocked_counterexample_hold`로 닫았다.
- 남은 구현 인접 후보는 `backdate_suppression_candidate` 7건이다.
- 이번 브랜치는 G1 guard가 실제 적용되었다고 가정했을 때의 before/after 의미 변화를 shadow 표로만 기록한다.
- production code, runtime verdict, operator-facing 사건 의미는 변경하지 않는다.

## 2. G1 shadow rule
- candidate name:
  - `G1_extreme_longgap_one_day`
- source bucket:
  - `promotion_decision_bucket = backdate_suppression_candidate`
- shadow condition:
  - `onset_method = anom_subtype:degradation`
  - `gap_days >= 30`
  - `degradation_onset_backdate_guard_flag = 1`
- interpretation:
  - current `retrospective_onset_date` is treated as an extreme long-gap backdated degradation onset.
  - if suppressed, the strict trigger remains as the event anchor.

## 3. 산출물
- repo-tracked:
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_012_G1_SUPPRESSION_SHADOW_PANEL_SIM_V1.csv`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_012_G1_SUPPRESSION_SHADOW_ROOT_SUMMARY_V1.csv`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_012_G1_SUPPRESSION_SHADOW_SUMMARY_V1.csv`
- local validation:
  - `/private/tmp/br012_g1_suppression_shadow_sim_v1/br012_g1_suppression_shadow_validation_v1.json`

## 4. 핵심 결과
- candidate rows: `7`
- site distribution: `ktc_ess = 7`
- root distribution:
  - `ed5e3367-fbd4-4c8c-be33-c5d1c5e191b7 = 4`
  - `10305b40-b67e-40d1-9cd1-271b6642a3d9 = 2`
  - `e089076c-92c1-4365-8641-2182b4f274e6 = 1`
- current event type:
  - `전조형 고장 = 7`
- shadow transition if G1 is applied:
  - `전조형 고장 -> 급작 고장 = 7`
- current gap range:
  - `75` to `270` days
- context overlap:
  - `site_event_history_flag = 7 / 7`
  - `subgroup_common_cause_history_flag = 5 / 7`
  - `strict_trigger_proximal_common_cause_flag = 6 / 7`
- allowed current branch changes:
  - `operator_facing_change_allowed = 0`
  - `code_change_allowed = 0`

## 5. Root summary
| site | panel_root | panels | current onset | strict trigger | gap mean | strict-proximal common cause | shadow transition |
|---|---|---:|---|---|---:|---:|---|
| `ktc_ess` | `ed5e3367-fbd4-4c8c-be33-c5d1c5e191b7` | 4 | `2025-01-29` | `2025-10-26` | 270.0 | 4 / 4 | `전조형 고장 -> 급작 고장` |
| `ktc_ess` | `10305b40-b67e-40d1-9cd1-271b6642a3d9` | 2 | `2025-01-29` | `2025-10-26` | 270.0 | 2 / 2 | `전조형 고장 -> 급작 고장` |
| `ktc_ess` | `e089076c-92c1-4365-8641-2182b4f274e6` | 1 | `2024-11-29` | `2025-02-12` | 75.0 | 0 / 1 | `전조형 고장 -> 급작 고장` |

## 6. 판단
- 이 7건은 “고장 자체를 제거”하는 후보가 아니다.
- G1이 적용되면, 너무 이른 degradation fallback onset을 제거하고 strict trigger date를 사건 anchor로 남기는 해석이 된다.
- 그래서 shadow transition은 `전조형 고장 -> 급작 고장`으로 기록한다.
- 6/7은 strict trigger proximal common-cause support가 있어, 10월 strict event를 남기는 판단은 현재 evidence와 충돌하지 않는다.
- 1건은 strict-proximal support가 없지만 gap이 75일이고 G1 조건에 들어오므로 별도 review note가 필요하다.

## 7. Decision lock
- BR-012는 simulation only다.
- `backdate_suppression_candidate`는 precursor promotion 후보가 아니다.
- 다음 코드 패치가 열린다면 audit/shadow field로 먼저 구현하고, final verdict 변경은 별도 approval 후에만 진행한다.
- G1 implementation proposal의 최소 성공 조건은 아래다.
  - `gangui` short-gap plausible cases remain unchanged.
  - `ktc_ess` 7 candidate rows are still isolated.
  - final verdict common columns remain unchanged in the first shadow pass.

## 8. 검증
- pre-change reproduction command:
  - `python -c "import pandas as pd; df=pd.read_csv('docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_010_PROMOTION_BUCKET_PANEL_PACKET_V1.csv'); print(df[df.promotion_decision_bucket.eq('backdate_suppression_candidate')].shape)"`
- post-change validation commands:
  - `python -m py_compile pv_ae/panel_day_engine.py`
  - `git diff --check`
  - `python release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/br012_conalog_smoke_v1 --sites conalog --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data`
- shadow invariant checks:
  - `candidate_rows = 7`
  - `shadow_precursor_to_sudden_rows = 7`
  - `operator_facing_change_allowed_rows = 0`
  - `code_change_allowed_rows = 0`
- local validation:
  - `/private/tmp/br012_g1_suppression_shadow_sim_v1/br012_g1_suppression_shadow_validation_v1.json`
- conalog smoke artifact:
  - `/private/tmp/br012_conalog_smoke_v1/result/fault_panel_result_master_report_v1.md`

## 9. 다음 단계
- BR-012를 merge한 뒤 다음 안전한 step은 G1을 runtime audit에 “suppressed-event shadow columns”로만 구현하는 것이다.
- 그 다음 fresh tri-site rerun에서 audit/final verdict common-column invariants를 비교한다.
- final operator-facing event semantics는 이 shadow rerun이 안정적일 때만 별도 branch로 논의한다.
