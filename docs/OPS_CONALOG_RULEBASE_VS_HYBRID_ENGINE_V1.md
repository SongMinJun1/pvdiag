# OPS Conalog Rulebase Vs Hybrid Engine V1

## 1. 비교 목적
- 본 문서는 대외 설명 관점에서 conalog rulebase 알고리즘과 현재 hybrid engine의 차이를 직접 비교하기 위한 문서다.
- 여기서 conalog rulebase는 stable handoff pack과 stable runtime/latest output으로 전달되는 직접 운영 판독 경로를 뜻한다.
- 여기서 hybrid engine은 panel multiaxis verdict, conalog, GPVS reference layer, heuristic triage layer, integrated table, validation/coverage/runtime foundation까지 포함한 현재 전체 운영 스택을 뜻한다.
- 외부 공개 freeze 기준은 여전히 `project-main-freeze-v9` 로 두어야 하며, 본 문서는 그 이후 내부 foundation 정리 내용을 대외 설명용으로 재구성한 문서다.

## 1A. 문서 경계
- 본 문서는 `stable/handoff conalog rulebase`와 `현재 hybrid engine`을 비교하는 문서다.
- runtime redesign gate 문서의 artifact/operator semantics 정책을 stable conalog contract에 그대로 덮어쓰는 문서가 아니다.
- stable/handoff contract와 runtime redesign contract의 경계는 [OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md), [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md) 를 따른다.

## 2. 입력 데이터 범위 차이
- conalog rulebase 경로는 외부 handoff 계약 관점에서 입력 범위를 좁게 유지한다. 현재 stable handoff pack은 `site`, `panel_id` 중심의 입력과 고정 config를 받아 stable output만 반환하도록 설계되어 있다.
- 현재 hybrid engine은 같은 운영 입력 위에 panel multiaxis verdict, conalog interpretation, GPVS evidence pack, heuristic candidate summary, validation framework, coverage/performance report 같은 내부 보조층을 함께 읽는다.
- 따라서 conalog rulebase는 전달 계약과 운영 해석의 단순성을 우선하고, hybrid engine은 설명 보강과 triage 보조를 위해 더 넓은 내부 자산을 함께 사용한다.

## 3. 탐지/판정 구조 차이
- conalog rulebase는 stable default output 기준으로 `패널고장여부_ko`, `사건유형_ko`, `최종고장양상_ko`, `conalog_원인군_ko` 를 직접 반환하는 운영 판독 경로다.
- 현재 hybrid engine의 primary 역시 panel multiaxis verdict 이지만, 그 위에 conalog 해석층을 붙이고, 필요 시 GPVS reference layer와 heuristic triage layer를 분리해서 함께 읽는다.
- 다시 말해 conalog rulebase는 운영자가 바로 읽는 직접 판독 경로이고, hybrid engine은 primary 판정층 위에 reference/triage/explanation 층을 추가한 다층 구조다.

## 4. 설명 가능성 차이
- conalog rulebase의 장점은 설명 경로가 짧고 안정적이라는 점이다. 외부 전달 시 stable six-field contract만으로도 현재 패널 상태와 conalog 원인군을 바로 설명할 수 있다.
- hybrid engine의 장점은 설명량이 더 많다는 점이다. integrated table, GPVS evidence pack, cause candidate heuristic, validation/coverage/runtime foundation까지 이어서 보여줄 수 있다.
- 다만 hybrid engine은 layer를 섞어 읽으면 과장 해석 위험이 커진다. 특히 GPVS와 heuristic은 non-primary 층이므로, 설명 가능성은 높아지지만 동시에 레이어 구분이 필수다.

## 5. conalog와 GPVS 사용 위치
- conalog는 두 경로 모두에서 direct operational interpretation layer다.
- conalog rulebase에서는 conalog가 stable default output의 핵심 필드로 직접 노출된다.
- hybrid engine에서는 conalog가 panel multiaxis verdict 위에 붙는 직접 운영 해석층으로 유지되며, GPVS는 여기에 직접 경쟁하지 않는다.
- GPVS는 current evidence summary 기준 `compatibility_reference_only_flag=1`, `core_reference_count=2`, `auxiliary_reference_count=4` 이며 reference-only 층으로만 사용한다.
- GPVS는 외부 실험 시나리오와 닮은 reference pattern을 제공하지만, conalog를 대체하는 직접 판독층이 아니다.

## 6. root-cause 확정 가능 여부
- 현재 conalog rulebase도 자동 root-cause 확정기로 읽으면 안 된다.
- 현재 hybrid engine도 자동 root-cause 확정기로 읽으면 안 된다.
- panel multiaxis verdict가 primary 이고 conalog가 direct operational interpretation layer 이지만, 이것이 곧 최종 물리 root-cause 확정을 뜻하지는 않는다.
- GPVS는 reference-only 이므로 direct root-cause classifier가 아니며, heuristic은 triage-only 이므로 최종 진단기로 승격하면 안 된다.

## 7. 현장 triage 지원 차이
- conalog rulebase는 현장 운영 전달에 유리하다. stable handoff pack, runtime latest output, one-click foundation을 통해 비개발자도 현재 결과를 비교적 단순하게 읽을 수 있다.
- hybrid engine은 현장 triage 보강에 유리하다. integrated table과 heuristic ranking은 후보 축소와 설명 보강에 도움을 준다.
- 다만 hybrid engine의 triage 지원은 어디까지나 보조 기능이다. cause candidate heuristic summary에서도 명시하듯이 이 층은 triage-only 이며, current frozen artifacts에는 official ranking metric이 없다.

## 8. 현재 결론
- 현재 운영 전달의 기본값은 conalog rulebase 경로가 아니라, panel multiaxis verdict를 primary 로 두고 conalog를 direct operational interpretation layer 로 읽는 stable stack 이다.
- 외부 handoff 관점에서는 stable conalog pack과 runtime/latest output을 우선 전달하는 것이 맞다.
- 내부 운영/분석 관점에서는 hybrid engine이 더 풍부한 설명과 triage 보조를 제공한다.
- 그러나 GPVS는 reference-only 이고 heuristic은 triage-only 이므로, hybrid engine을 “자동 root-cause 확정 엔진”으로 소개하면 안 된다.

## 비교 표
| 항목 | conalog rulebase 알고리즘 | 현재 hybrid engine |
| --- | --- | --- |
| 입력 범위 | stable handoff 계약 기준의 축소된 운영 입력을 사용함 | 운영 입력 위에 panel multiaxis verdict, GPVS evidence, heuristic, validation/coverage/runtime foundation까지 함께 읽음 |
| primary output | stable six-field conalog output을 반환함 | panel multiaxis verdict를 primary 로 유지한 채 integrated table과 보조 문서를 함께 생성함 |
| conalog 사용 위치 | direct operational interpretation layer 로 직접 출력됨 | direct operational interpretation layer 로 동일하게 유지됨 |
| GPVS 사용 위치 | stable default output에는 포함하지 않음 | reference-only layer 로만 사용함 |
| heuristic 사용 위치 | stable default output에는 포함하지 않음 | triage-only suspected-cause narrowing 층으로만 사용함 |
| direct root-cause 가능 여부 | 자동 root-cause 확정기로 읽으면 안 됨 | 자동 root-cause 확정기로 읽으면 안 됨 |
| 실시간/준실시간 운용성 | stable handoff pack, runtime once/poll feasibility, one-click foundation과 연결 가능함 | runtime readiness foundation과 one-click foundation이 있으나 production streaming SLA는 아직 없음 |
| 전달 패키지 형태 | `delivery/conalog_handoff_v1/` 기준 stable pack으로 전달 가능함 | 연구/운영 문서, evidence pack, integrated table, validation/coverage/runtime foundation을 포함한 내부 전체 스택임 |
