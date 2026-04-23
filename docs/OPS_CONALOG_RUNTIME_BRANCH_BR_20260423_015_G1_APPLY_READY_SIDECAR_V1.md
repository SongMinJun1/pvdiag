<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_015_G1_APPLY_READY_SIDECAR_V1

## [BR-20260423-015] G1 apply-ready sidecar
- `status`: apply_ready_sidecar_generated
- `branch_type`: B
- `current_gate`: Gate 3
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23

## 1. 이슈 요약
- BR-014 preview는 G1 적용 시 operator-facing column `13`개, 총 `91` cell이 바뀐다고 보여줬다.
- 단 7건 중 1건은 `strict_trigger_proximal_common_cause_flag = 0`이다.
- BR-015는 이 1건을 production 후보에서 분리하고, strict-proximal support가 있는 6건만 apply-ready sidecar로 고정한다.
- production final verdict 파일은 수정하지 않는다.

## 2. 입력 실행
- command:
  - `python release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/br015_tri_site_v1 --sites conalog,gangui,ktc_ess --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data`
- source audit:
  - `/private/tmp/br015_tri_site_v1/raw_only_chain_workspace/_share/panel_day_engine_runtime_fault_event_audit_v1.csv`
- source final verdict:
  - `/private/tmp/br015_tri_site_v1/raw_only_chain_workspace/_share/panel_day_engine_runtime_final_verdict_v1.csv`
- local validation:
  - `/private/tmp/br015_g1_apply_ready_sidecar_v1/br015_g1_apply_ready_sidecar_validation_v1.json`

## 3. 산출물
- repo-tracked:
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_015_G1_APPLY_READY_PANEL_SIDECAR_V1.csv`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_015_G1_APPLY_READY_DIFF_LONG_V1.csv`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_015_G1_APPLY_READY_BY_COLUMN_V1.csv`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_015_G1_APPLY_READY_SUMMARY_V1.csv`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_015_G1_HOLD_REVIEW_PANEL_V1.csv`

## 4. 핵심 결과
- G1 shadow total rows: `7`
- apply-ready rows: `6`
- hold-review rows: `1`
- apply-ready site distribution:
  - `ktc_ess = 6`
- hold-review panel:
  - `e089076c-92c1-4365-8641-2182b4f274e6.1.9`
- apply-ready semantic transition:
  - `전조형 고장 -> 급작 고장 = 6`
- apply-ready changed columns:
  - `13`
- apply-ready changed cells:
  - `78`
- production output written:
  - `0`

## 5. Apply-ready 기준
- include:
  - `g1_suppressed_event_shadow_flag = 1`
  - `strict_trigger_proximal_common_cause_flag = 1`
- exclude / hold:
  - `strict_trigger_proximal_common_cause_flag = 0`
- rationale:
  - G1은 backdated degradation onset 억제 후보지만, operator-facing 전환은 더 강한 anchor가 필요하다.
  - strict trigger 근처 common-cause support가 있는 6건만 먼저 적용 후보로 두면, 7건 일괄 변경보다 안전하다.

## 6. 변경 후보 column set
| output column | changed panels |
|---|---:|
| `사건유형_ko` | 6 |
| `사건유형_해석_ko` | 6 |
| `최종고장양상_ko` | 6 |
| `사건이력_ko` | 6 |
| `전조흔적_flag` | 6 |
| `순수급작_flag` | 6 |
| `전조평가셋편입_flag` | 6 |
| `급작평가셋편입_flag` | 6 |
| `운영최초전조발견일` | 6 |
| `운영최초전조마커` | 6 |
| `사건해석상전조시작일` | 6 |
| `전조형이력_flag` | 6 |
| `급작고장이력_flag` | 6 |

## 7. Hold review
- hold panel:
  - `e089076c-92c1-4365-8641-2182b4f274e6.1.9`
- hold reason:
  - `strict_trigger_proximal_common_cause_flag = 0`
- context:
  - gap `75` days
  - site event history `1`
  - subgroup common-cause history `1`
- interpretation:
  - it remains a G1 candidate, but lacks the strict-trigger proximal support used for this safer apply-ready set.

## 8. Decision lock
- BR-015 is sidecar only.
- production final verdict remains unchanged.
- apply-ready rows require explicit user approval before a semantic patch branch.
- hold-review row must not be silently included in the first semantic patch.

## 9. 검증
- validation command:
  - `python -m py_compile pv_ae/panel_day_engine.py`
- validation command:
  - `git diff --check`
- invariant:
  - `g1_shadow_total_rows = 7`
  - `apply_ready_rows = 6`
  - `hold_review_rows = 1`
  - `apply_ready_changed_output_columns = 13`
  - `apply_ready_changed_output_cells = 78`
  - `production_output_written = 0`

## 10. 다음 단계
- If approved: create a separate semantic patch branch for the 6 apply-ready rows only.
- If not approved: keep BR-013 audit shadow and BR-015 sidecar as reviewer evidence only.
- Do not include the hold row until separate evidence review closes it.
