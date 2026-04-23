<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_014_G1_OPERATOR_SEMANTIC_PREVIEW_V1

## [BR-20260423-014] G1 operator-facing semantic preview
- `status`: semantic_preview_generated
- `branch_type`: B
- `current_gate`: Gate 3
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23

## 1. 이슈 요약
- BR-013은 G1 suppressed-event 해석을 runtime audit shadow columns로만 구현했다.
- BR-014는 그 shadow 결과를 operator-facing final verdict column에 적용한다고 가정했을 때의 diff를 preview-only로 만든다.
- production final verdict 파일은 수정하지 않는다.
- 이 브랜치는 승인용 preview이며, 운영 의미 변경 implementation이 아니다.

## 2. 입력 실행
- command:
  - `python release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/br014_tri_site_v1 --sites conalog,gangui,ktc_ess --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data`
- source audit:
  - `/private/tmp/br014_tri_site_v1/raw_only_chain_workspace/_share/panel_day_engine_runtime_fault_event_audit_v1.csv`
- source final verdict:
  - `/private/tmp/br014_tri_site_v1/raw_only_chain_workspace/_share/panel_day_engine_runtime_final_verdict_v1.csv`
- local validation:
  - `/private/tmp/br014_g1_operator_semantic_preview_v1/br014_operator_semantic_preview_validation_v1.json`

## 3. 산출물
- repo-tracked:
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_014_G1_OPERATOR_SEMANTIC_PREVIEW_PANEL_V1.csv`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_014_G1_OPERATOR_SEMANTIC_PREVIEW_DIFF_LONG_V1.csv`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_014_G1_OPERATOR_SEMANTIC_PREVIEW_BY_COLUMN_V1.csv`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_014_G1_OPERATOR_SEMANTIC_PREVIEW_SUMMARY_V1.csv`

## 4. 핵심 결과
- preview panel rows: `7`
- site distribution: `ktc_ess = 7`
- semantic transition:
  - `전조형 고장 -> 급작 고장 = 7`
- changed output columns:
  - `13`
- changed output cells:
  - `91`
- production output written:
  - `0`

## 5. 변경 preview column set
| output column | changed panels |
|---|---:|
| `사건유형_ko` | 7 |
| `사건유형_해석_ko` | 7 |
| `최종고장양상_ko` | 7 |
| `사건이력_ko` | 7 |
| `전조흔적_flag` | 7 |
| `순수급작_flag` | 7 |
| `전조평가셋편입_flag` | 7 |
| `급작평가셋편입_flag` | 7 |
| `운영최초전조발견일` | 7 |
| `운영최초전조마커` | 7 |
| `사건해석상전조시작일` | 7 |
| `전조형이력_flag` | 7 |
| `급작고장이력_flag` | 7 |

## 6. 변하지 않는 중요한 항목
- 이 preview는 production final verdict를 쓰지 않는다.
- `세부fault_기준일`은 preview에서도 strict trigger date와 같아서 변경 cell로 잡히지 않았다.
- `패널고장여부_ko`는 계속 `고장`이다.
- 즉 이 preview는 “고장 제거”가 아니라 “너무 이른 전조 해석 제거 및 strict trigger 기반 급작 anchor로 변경”이다.

## 7. Context overlap
- strict trigger proximal common-cause overlap:
  - `6 / 7`
- site-event history:
  - `7 / 7`
- subgroup common-cause history:
  - `5 / 7`
- remaining caution:
  - `e089076c-92c1-4365-8641-2182b4f274e6.1.9` has `strict_trigger_proximal_common_cause_flag = 0`, even though it is still a G1 candidate.

## 8. 판단
- BR-014 preview는 “운영 변경을 해도 되는가?”를 결정하기 위한 마지막 사람 확인용 표다.
- preview 기준으로 바뀌는 의미는 명확하다.
  - current: `전조형 고장 / 진행성 악화`
  - proposed: `급작 고장 / 급작 발생`
- 단, 7건 모두를 일괄 적용하기 전에 `strict-proximal=0`인 1건은 별도 확인하는 편이 안전하다.

## 9. Decision lock
- BR-014는 preview only다.
- production output, final verdict builder, `panel_day_engine.py`는 변경하지 않는다.
- 다음 BR에서 실제 semantic patch를 만들더라도 처음에는 `apply-ready preview` 또는 `feature flag` 형태로 제한한다.
- operator-facing 변경은 사용자 승인 없이는 merge하지 않는다.

## 10. 검증
- reproduction command:
  - `python release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/br014_tri_site_v1 --sites conalog,gangui,ktc_ess --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data`
- validation command:
  - `python -m py_compile pv_ae/panel_day_engine.py`
- validation command:
  - `git diff --check`
- invariant:
  - `preview_panel_rows = 7`
  - `production_output_written = 0`
  - `changed_output_columns = 13`
  - `changed_output_cells = 91`

## 11. 다음 단계
- reviewer가 BR-014 preview를 승인하면, 다음은 operator-facing semantic patch branch를 만든다.
- 승인하지 않으면 BR-013 audit shadow까지만 유지한다.
- 가장 보수적인 승인안은 `strict-proximal=1`인 6건만 우선 적용하고, 나머지 1건은 hold로 남기는 것이다.
