<!-- markdownlint-disable MD013 -->

# OPS Conalog Stable Runtime Mapping Spec V1

## 1. 문서 역할
- 본 문서는 `stable/handoff contract`와 `runtime redesign / hybrid artifact contract` 사이의 normative boundary/mapping contract다.
- 개요/배경 설명은 [OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md)에 남기고, 본 문서는 무엇을 같은 것으로 보면 안 되는지, 무엇이 대응되며 무엇은 대응되지 않는지를 규범적으로 잠근다.

## 2. 비목표
- stable six-field contract를 runtime redesign contract로 대체하지 않는다.
- runtime redesign artifact semantics를 stable contract로 축소하지 않는다.
- 둘을 합친 새로운 단일 output contract를 만들지 않는다.

## 3. canonical source 우선순위
1. stable/handoff contract 자체:
   - stable entrypoint/code 및 stable handoff 문서가 canonical source다.
2. runtime redesign / hybrid artifact contract 자체:
   - runtime pack README와 runtime decision/gate 문서군이 canonical source다.
3. 본 spec:
   - 위 두 문서군 사이의 boundary와 최소 대응 관계를 잠그는 secondary spec이다.

## 4. 경계 규칙
1. stable/handoff와 runtime redesign은 별도 계약이다.
2. 같은 용어가 양쪽에 등장해도, 자동으로 같은 headline policy / artifact policy를 공유한다고 가정하지 않는다.
3. stable direct field(`사건유형_ko`, `최종고장양상_ko`)는 stable contract에서 direct output일 수 있지만, runtime redesign operator-facing artifact에서는 direct headline field가 아니다.
4. runtime redesign의 `official current / precursor / raw-only / master / detailed` artifact 분리는 stable contract에 자동 전파되지 않는다.
5. final_delivery 문서군은 stable 우선 문서이며, runtime redesign artifact semantics의 canonical source가 아니다.

## 5. field-level mapping
### 5.1 direct 대응
| stable/handoff | runtime redesign 대응 축 | mapping class | 비고 |
| --- | --- | --- | --- |
| `패널고장여부_ko` | `state_axis.operational_state` | approximate | 가장 가까운 현재 상태 축 |
| `conalog_원인군_ko` | `cause_axis.operational_category` 일부 | approximate | 완전 1:1 보장 안 함 |

### 5.2 event semantics 대응
| stable/handoff | runtime redesign 대응 축 | mapping class | 비고 |
| --- | --- | --- | --- |
| `사건유형_ko` | `temporal_axis.event_type` | semantic | stable direct output, runtime에선 event semantics 축 |
| `최종고장양상_ko` | `temporal_axis.terminal_pattern` | semantic | stable direct output, runtime에선 event semantics 축 |

### 5.3 no-direct-mapping
| stable/handoff에 없는 축 | runtime redesign 축 | 비고 |
| --- | --- | --- |
| artifact officiality split | `source_layer / officiality` | stable contract에는 current/precursor/raw-only 분리가 없음 |
| audience split | operator-facing vs analyst-facing | runtime redesign에서만 강하게 분리 |
| `raw_only_fault_signal_report` | analyst/support artifact | stable contract 직접 대응 없음 |
| `master_report` / `detailed_report` | guide / lineage layer | stable metadata와 동일시 금지 |

## 6. artifact-level mapping
| stable/handoff artifact | runtime redesign에서 가장 가까운 artifact | mapping class | 금지 가정 |
| --- | --- | --- | --- |
| `conalog_panel_result_v1.csv` | `fault_panel_result_current_v1.csv` | approximate | 둘을 같은 schema/policy로 간주 금지 |
| stable metadata | `fault_panel_result_master_report_v1.md` | loose | master report를 stable metadata 대체물로 간주 금지 |
| stable examples/reference sidecar | detailed / raw-only / heuristic artifacts | loose | direct root-cause output으로 과독해 금지 |

## 7. operator-facing 규칙
1. stable contract에서 direct field인 `사건유형_ko`, `최종고장양상_ko`는 runtime redesign operator-facing artifact에 direct headline으로 이식하지 않는다.
2. runtime redesign operator-facing artifact는 `operational_state` 중심으로 읽는다.
3. runtime redesign에서 허용되는 `사건 종결 요약` 같은 softened summary는 stable contract에 자동 반영되지 않는다.

## 8. final_delivery 규칙
1. `release/final_delivery_v1/*` 문서군은 stable direct CLI / stable integrated schema 설명을 우선한다.
2. runtime redesign artifact semantics는 final_delivery 문서군에 상세 복제하지 않는다.
3. final_delivery 문서군에는 boundary note만 최소 반영한다.

## 9. 변경 관리
- stable/runtime 경계 정책이 바뀌면 먼저 decision log를 작성한다.
- 그다음 note와 spec을 함께 갱신한다.
- 개별 stable 문서 또는 runtime 문서의 세부 semantics 변경은 각 canonical source를 먼저 바꾸고, 필요할 때만 본 spec을 후행 수정한다.

## 10. 관련 문서
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_010_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_010_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_011_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_011_V1.md)
- [OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md)
- [OPS_CONALOG_HANDOFF_PACK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_HANDOFF_PACK_V1.md)
- [OPS_CONALOG_RULEBASE_VS_HYBRID_ENGINE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RULEBASE_VS_HYBRID_ENGINE_V1.md)
- [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
