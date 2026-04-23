# OPS Conalog Runtime Gate 1 Glossary V1

## 1. 목적
- 본 문서는 `OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md`의 Gate 1 산출물인 `용어 사전`이다.
- 목적은 아래 세 가지다.
  - 같은 단어를 문서/코드/report에서 같은 뜻으로만 쓰게 한다.
  - operator-facing wording과 internal wording의 경계를 분명히 한다.
  - artifact 이름만 봐도 공식성/역할/출처를 유추할 수 있게 한다.

## 2. 사용 규칙
- 이 문서는 `용어를 잠그는 문서`다. 구현 세부 규칙은 별도 Gate 문서에서 다룬다.
- 같은 용어를 다른 뜻으로 쓰려면 먼저 decision log에서 supersede 해야 한다.
- operator-facing report는 본 문서의 `허용 표현`만 쓴다.
- internal code field는 유지할 수 있지만, 외부 노출 명칭은 이 문서 기준을 따른다.

## 3. 상태
- 현재 상태:
  - `working baseline`
- 의미:
  - Gate 1 초안으로 즉시 참조 가능하지만, 이후 decision log에 따라 refine될 수 있다.

## 4. 핵심 용어 사전
| 용어 | 잠긴 정의 | 이렇게 읽지 말 것 | 허용 노출 위치 | 비고 |
| --- | --- | --- | --- | --- |
| `MLPE` | 본 프로젝트의 전역 해석 가정인 모듈 단위 power electronics 환경 | site별 on/off feature flag | 모든 상위 설계 문서 | `MLPE 있음/없음`을 project 내부 분기 변수처럼 쓰지 않음 |
| `official current` | frozen-support live chain 기준의 운영 공식 current 결과 | raw-only 후보 우주 | `fault_panel_result_current_*` | 외부 설명의 기준점 |
| `live chain` | frozen-support asset을 참조하는 공식 current 생성 체인 | raw-only candidate 생성 체인 | master report, pack 설명 | `official current`의 upstream |
| `raw-only candidate` | panel_day_core와 precursor gate 위에서 계산한 더 넓은 후보 우주 | 공식 current | detailed report, 내부 분석 | 분석/보조 판단용 |
| `raw-only current` | raw-only candidate 중 strict current subset | official current | `fault_panel_result_raw_only_current_*` | candidate 우주의 일부 |
| `raw-only fault signal report` | raw-only candidate 우주에서 고장 신호가 이미 보인 패널 모음 | analyst/support artifact | `fault_panel_result_raw_only_fault_signal_report_v1.csv` | raw-only 후보 우주의 고장 신호 보조표 |
| `precursor` | hard evidence 이전 단계의 다축 누적 이상 | 확정 fault 자체 | 상위 설계, 평가 정의 | 구체 승격 규칙은 Gate 3에서 잠금 |
| `precursor candidate` | precursor 규칙을 만족했지만 아직 공식 current/확정은 아닌 운영 추적 대상 | 공식 fault row | precursor report | 추적 대상이지 확정 아님 |
| `고위험 관찰` | 즉시 확정 신호는 없지만 precursor 누적이 강한 상태 | 확정 | preview/report 표시 | precursor와 완전 동일어는 아님 |
| `hard evidence` | `final_fault`, `critical_fault`, `critical_confirmed` 같은 확정 계열 강신호 | root cause 확정명 | 설계 문서, 내부 설명 | operator-facing에선 `고장 신호`로 순화 가능 |
| `고장 신호` | operator-facing에서 hard evidence를 풀어 쓴 표현 | 원인 확정 | raw-only fault signal report, current 설명 | `hard evidence`의 외부 노출 표현 |
| `확정` | 운영해석등급 상 최종 고장 신호 또는 강한 고장 신호가 존재하는 상태 | 원인 확정 | preview/report | 상태 등급이지 cause label이 아님 |
| `final_fault` | 최종 확정 계열 신호를 뜻하는 internal field | 미래 예언 | 내부 코드/상세 로그 | 외부 표에는 그대로 쓰지 않음 |
| `critical_fault` | 강한 고장 신호 계열의 internal field | precursor | 내부 코드/상세 로그 | 외부 표엔 `강한 고장 신호`로만 순화 |
| `critical_confirmed` | strong evidence가 confirm된 internal field | 별도 원인군 | 내부 코드/상세 로그 | precedence는 Gate 4에서 잠금 |
| `fault_like_day` | hard evidence 이전 단계의 fault-like 관측일을 뜻하는 중간 신호 | final_fault와 동일 | 내부 코드/상세 로그 | 정확한 역할은 Gate 2에서 잠금 |
| `사건유형` | 시간 전개 관점의 event class | 원인명 | report/detailed | 예: `전조형 고장`, `급작 고장` |
| `최종고장양상` | 사건의 종결 패턴 해석 | 미래에 반드시 그렇게 될 예언 | report/detailed | 예: `진행성 악화`, `급격 종료` |
| `원인 후보` | 관측 신호를 바탕으로 점수화된 ranked candidate | 확정 root cause | preview/report/detailed | `상위 해석 후보`는 top1 표현 |
| `상위 해석 후보` | 현재 시점 top1 candidate를 사람에게 읽기 쉽게 노출한 값 | 확정 원인 | preview/report | top1 confidence와 분리 가능 |
| `기존 알고리즘 source` | legacy rule/source tag를 보여주는 보조 정보 | 정상/비정상 판정 | preview/report | `미검출`은 정상 뜻이 아님 |
| `고장 기준일` | 판단 기준으로 삼은 날짜 | 항상 실제 고장 확정일 | preview/report | 실제 의미는 source에 따라 다를 수 있음 |
| `신호 기준일` | 신호를 대표하는 날짜 | 항상 fault date | signal/fault signal report | current/fault 문맥 분리 필요 |
| `모니터링 권고` | precursor candidate에 대한 다음 확인 행동 메모 | 현장 출동 확정 | precursor report | 운영 메모 성격 |
| `현장 점검 권고` | 고장 신호 동반 패널에 대한 첫 현장 액션 우선순위 | 원인 확정 | raw-only fault signal report | action-first 표현 |

## 5. 절대 혼용하면 안 되는 쌍
| 혼동 금지 쌍 | 이유 |
| --- | --- |
| `official current` vs `raw-only current` | 공식성과 후보 우주가 다름 |
| `precursor` vs `hard evidence` | 시간축과 강도축이 다름 |
| `사건유형` vs `원인 후보` | event semantics와 cause hypothesis는 다름 |
| `최종고장양상` vs 미래 예언 | terminal pattern은 현재 해석이지 예언이 아님 |
| `상위 해석 후보` vs 확정 원인 | ranked candidate를 확정으로 오해하면 안 됨 |
| `기존 알고리즘 source=미검출` vs 정상 | legacy tag 부재일 뿐 상태 정상 의미가 아님 |

## 6. operator-facing 허용 표현
### 6.1 권장 표현
- `전조 후보`
- `고위험 관찰`
- `고장 신호`
- `강한 고장 신호`
- `최종 고장 신호`
- `확정 경로`
- `상위 해석 후보`
- `모니터링 권고`
- `현장 점검 권고`

### 6.2 가급적 피할 표현
- `critical/final`
- `hard evidence`
- `truth`
- `root cause`
- `source=none 이므로 정상`

## 7. internal -> external 매핑
| internal field / 개념 | external wording |
| --- | --- |
| `critical_fault` | `강한 고장 신호` |
| `critical_confirmed` | `강한 고장 신호 확정` |
| `final_fault` | `최종 고장 신호` |
| `hard evidence` | `고장 신호` |
| `top1 candidate` | `상위 해석 후보` |
| `legacy source none` | `기존 알고리즘 source=미검출` |

## 8. artifact 역할 매핑표
| artifact | 공식성 | audience | 한 줄 정의 |
| --- | --- | --- | --- |
| `fault_panel_result_current_*` | 공식 | 운영자 | frozen-support live chain 기준 current 결과 |
| `fault_panel_result_precursor_report_v1.csv` | 보조 | 운영자/분석가 | 고장 신호 없는 precursor candidate 표 |
| `fault_panel_result_raw_only_current_*` | 보조 | 분석가 | raw-only candidate 중 strict current subset |
| `fault_panel_result_raw_only_fault_signal_report_v1.csv` | 보조 | 분석가/운영 보조 | raw-only 후보 우주에서 고장 신호가 이미 보인 패널 표 |
| `fault_panel_result_detailed_report_v1.xlsx` | 분석용 | 분석가 | lineage와 evidence를 모두 보는 상세 리포트 |
| `fault_panel_result_master_report_v1.md` | 안내용 | 운영자/분석가 | 전체 artifact를 어떤 순서로 읽을지 설명하는 안내 문서 |

## 9. Gate 1 체크리스트
- 같은 용어가 문서/코드/report에서 같은 뜻으로 쓰이는가
- `official current`와 `raw-only`가 artifact 이름만으로 구분되는가
- operator-facing 표에 internal shorthand가 새어 나오지 않는가
- `상위 해석 후보`가 확정 원인처럼 읽히지 않는가
- `고장 기준일`이 fault date로 과해석되지 않게 가이드가 있는가

## 10. 바로 decision log에 올려야 할 항목
- precursor 정의
- hard evidence 정의
- `fault_like_day`의 역할
- `vdrop` 노출 정책
- `고위험 관찰`과 `precursor candidate`의 관계
- raw-only fault signal report의 운영자 직접 노출 범위

## 11. 다음 연결 문서
- 상위 로드맵:
  - [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- Gate 2 signal role matrix:
  - [OPS_CONALOG_RUNTIME_GATE2_SIGNAL_ROLE_MATRIX_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2_SIGNAL_ROLE_MATRIX_V1.md)
- decision log template:
  - [OPS_CONALOG_RUNTIME_DECISION_LOG_TEMPLATE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_TEMPLATE_V1.md)
- branch / parking-lot template:
  - [OPS_CONALOG_RUNTIME_BRANCH_PARKING_LOT_TEMPLATE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_PARKING_LOT_TEMPLATE_V1.md)
