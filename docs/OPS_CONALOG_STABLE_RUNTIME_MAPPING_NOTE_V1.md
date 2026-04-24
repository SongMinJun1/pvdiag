# OPS Conalog Stable Runtime Mapping Note V1

## 1. 목적
- 본 문서는 `stable/handoff contract`와 `runtime redesign / hybrid artifact contract`를 같은 층으로 오해하지 않도록, 두 경로의 대응 관계를 정리하는 boundary/mapping note다.
- 이 문서는 새로운 계약을 만드는 문서가 아니라, 이미 존재하는 두 계약을 어떻게 병렬로 읽어야 하는지 설명하는 중간 문서다.
- [DL-20260422-002](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md) 가 `선택지 B`를 채택한 이후에는, 본 문서를 stable/handoff와 runtime redesign 사이의 기본 boundary/mapping note로 사용한다.
- [DL-20260422-010](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_010_V1.md) 기준으로, `release/final_delivery_v1/*` 문서군에는 본 note의 상세 mapping을 복제하지 않고 boundary note만 최소 반영한다.
- [DL-20260422-011](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_011_V1.md) 이후에는, 본 문서는 reader-friendly overview note로 유지하고, normative boundary/mapping 규칙은 [OPS_CONALOG_STABLE_RUNTIME_MAPPING_SPEC_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_STABLE_RUNTIME_MAPPING_SPEC_V1.md) 를 우선 참조한다.

## 2. 전제
- stable/handoff 경로의 대표 entrypoint는 [app/run_conalog_infer.py](/Users/b9gc/pvdiag/app/run_conalog_infer.py) 다.
- runtime redesign / hybrid artifact 경로의 대표 entrypoint는 [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py) 다.
- 두 경로는 모두 같은 프로젝트 안에 있지만, 같은 출력 계약을 직접 공유한다고 가정하지 않는다.

## 3. 두 경로의 역할 요약
| 경로 | 대표 entrypoint | 대표 산출물 | 주 독자 | 목적 |
| --- | --- | --- | --- | --- |
| stable/handoff | [run_conalog_infer.py](/Users/b9gc/pvdiag/app/run_conalog_infer.py) | `conalog_panel_result_v1.csv`, `conalog_run_metadata_v1.json` | 외부 handoff consumer, stable runtime consumer | 좁고 고정된 stable contract 전달 |
| runtime redesign / hybrid | [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py) | `fault_panel_result_current_v1.csv`, `fault_panel_result_precursor_report_v1.csv`, `fault_panel_result_raw_only_fault_signal_report_v1.csv`, `fault_panel_result_master_report_v1.md`, `fault_panel_result_detailed_report_v1.xlsx` | 운영자, 분석가, 내부 triage 사용자 | MLPE runtime/hybrid artifact를 분리해 읽는 내부 운영/분석 계약 |

## 4. 왜 둘을 같은 계약으로 읽으면 안 되는가
- stable/handoff 경로는 `site`, `panel_id`, `패널고장여부_ko`, `사건유형_ko`, `최종고장양상_ko`, `conalog_원인군_ko`를 stable six-field contract로 직접 반환한다.  
  근거: [app/run_conalog_infer.py](/Users/b9gc/pvdiag/app/run_conalog_infer.py), [OPS_CONALOG_HANDOFF_PACK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_HANDOFF_PACK_V1.md)
- runtime redesign 경로는 `official current`, `precursor`, `raw-only current`, `raw-only fault signal report`, `master/detailed`를 artifact별로 분리한다.  
  근거: [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py), [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- stable/handoff 문서군은 direct operational interpretation을 설명하지만, runtime redesign 문서군은 operator-facing headline과 analyst-facing explanation을 다시 분리한다.
- 따라서 같은 용어가 두 경로에 모두 등장하더라도, 자동으로 같은 headline policy나 같은 artifact policy를 공유한다고 보면 안 된다.

## 5. 대응 관계
### 5.1 상태 축
| stable/handoff | runtime redesign 대응 축 | 비고 |
| --- | --- | --- |
| `패널고장여부_ko` | `state_axis.operational_state` | 가장 가까운 대응 축 |
| `사건유형_ko` | `temporal_axis.event_type` | stable path에선 direct output, redesign path에선 event semantics 축 |
| `최종고장양상_ko` | `temporal_axis.terminal_pattern` | stable path에선 direct output, redesign path에선 event semantics 축 |
| `conalog_원인군_ko` | `cause_axis.operational_category` 또는 `problem_class` 일부 | 완전 1:1 대응으로 보지 않음 |

### 5.2 artifact 축
| stable/handoff artifact | runtime redesign에서 가장 가까운 참고 artifact | 주의 |
| --- | --- | --- |
| `conalog_panel_result_v1.csv` | `fault_panel_result_current_v1.csv` | 비슷한 현재 결과처럼 보여도 계약이 같다고 가정하지 않음 |
| stable metadata | `fault_panel_result_master_report_v1.md`, detailed definitions | redesign 쪽은 안내/설명 레이어가 더 많음 |
| stable reference sidecar | detailed / raw-only / heuristic explanation artifacts | direct root-cause output이 아님 |

## 6. 읽는 법
### 6.1 stable/handoff 문서를 읽을 때
- stable external contract 문서로 읽는다.
- `사건유형_ko`, `최종고장양상_ko`가 direct output field로 등장해도, 그것을 자동으로 runtime redesign의 operator headline 정책과 동일시하지 않는다.
- stable path를 runtime redesign wording 규칙으로 즉시 교정하려고 하지 않는다.

### 6.2 runtime redesign 문서를 읽을 때
- MLPE runtime/hybrid artifact redesign 문서로 읽는다.
- `event_type`, `terminal_pattern`은 event semantics 축으로 먼저 읽고, operator-facing headline에서는 제한적으로만 다룬다.
- `raw-only fault signal report`는 analyst/support artifact로 읽는다.

## 7. 현재 채택된 boundary 읽기
- `DL-20260422-002` 채택 이후에는 아래를 기본 가정으로 둔다.
  1. stable/handoff 문서군은 stable external contract 문서다.
  2. runtime redesign 문서군은 internal MLPE runtime/hybrid redesign 문서다.
  3. 두 문서군은 같은 용어를 공유할 수 있지만, 같은 artifact policy를 공유한다고 자동으로 가정하지 않는다.
  4. 두 문서군을 연결할 때는 본 문서나 후속 정식 mapping spec을 먼저 참조한다.

## 8. 지금 바로 해도 되는 패치
- stable 문서에 `runtime redesign 문서와 동일 계약이 아님`을 설명하는 경계 문구 추가
- runtime redesign 문서에서 stable path를 참조할 때 `별도 contract`라고 명시
- Gate 1 glossary에서 stable/runtime를 같은 노출 정책으로 읽히지 않게 설명 보강

## 9. 지금 하면 안 되는 패치
- stable/handoff 문서를 runtime redesign semantics에 맞춰 바로 재작성
- `사건유형_ko`, `최종고장양상_ko`의 stable path 의미를 runtime redesign gate 문서만으로 덮어쓰기
- stable output과 runtime artifact를 하나의 schema/policy로 합치는 패치

## 10. 후속 결정 필요 항목
- stable path와 runtime redesign path의 용어를 공용 glossary 하나로 유지할지
- 별도 `stable-runtime mapping spec`을 정식 문서로 승격할지
- stable path에도 runtime redesign의 operator-facing headline 정책 일부를 가져올지

## 11. 관련 문서
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md)
- [OPS_CONALOG_HANDOFF_PACK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_HANDOFF_PACK_V1.md)
- [OPS_CONALOG_RULEBASE_VS_HYBRID_ENGINE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RULEBASE_VS_HYBRID_ENGINE_V1.md)
- [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
