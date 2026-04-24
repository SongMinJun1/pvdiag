# OPS Conalog Runtime Gate 2 Signal Role Matrix V1

## 1. 목적
- 본 문서는 `OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md`의 Gate 2 산출물인 `signal role matrix`다.
- 목적은 아래 네 가지다.
  - 각 신호가 `전조용`, `고장 신호용`, `설명용`, `내부 전용` 중 어디에 속하는지 잠근다.
  - 같은 신호를 artifact마다 다른 수준으로 노출할 때 허용 범위를 정한다.
  - operator-facing wording과 analyst-facing wording의 경계를 분명히 한다.
  - Gate 3 precursor 승격 규칙과 Gate 4 hard evidence 경계를 정하기 전, 신호의 역할을 먼저 고정한다.

## 2. 사용 규칙
- 이 문서는 `신호의 역할`을 잠그는 문서다. threshold 자체는 잠그지 않는다.
- Gate 3과 Gate 4가 아직 열려 있어도, Gate 2에서 각 신호의 `주 역할`은 먼저 고정한다.
- operator-facing artifact는 본 문서의 `허용 노출` 규칙을 따른다.
- 같은 신호를 다른 역할로 쓰려면 decision log에서 supersede 해야 한다.

## 3. 상태
- 현재 상태:
  - `working baseline`
- 의미:
  - 즉시 참조 가능한 기준선이지만, Gate 3/4 결정 후 일부 세부 문구는 조정될 수 있다.

## 4. 역할 분류 원칙
### 4.1 역할 축
- `전조용`:
  - hard evidence 이전 단계의 누적 이상을 보는 신호
- `고장 신호용`:
  - hard evidence 또는 그에 준하는 confirm path를 형성하는 신호
- `설명용`:
  - 상태를 직접 올리기보다, 왜 그렇게 읽었는지 설명하는 신호
- `내부 전용`:
  - operator-facing 표에 직접 노출하지 않고 내부 규칙/lineage용으로만 쓰는 신호

### 4.2 노출 원칙
- operator-facing precursor 표에는 `전조용`과 일부 `설명용`만 완곡하게 노출한다.
- raw-only fault signal report에는 `고장 신호용`과 일부 `설명용`을 노출할 수 있다.
- detailed report에는 네 역할 모두 남길 수 있다.
- internal shorthand는 가능하면 direct exposure 대신 완곡한 외부 표현으로 바꾼다.

## 5. Signal Role Matrix
| 신호 | source layer | 주 역할 | 보조 역할 | operator-facing 허용 노출 | 허용 artifact | 이렇게 쓰지 말 것 | 비고 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `pre_ews` | panel_day_engine / runtime merge | 전조용 | 설명용 | 가능 | precursor report, detailed, master guide | hard evidence | EWS 계열 초기 누적 징후 |
| `ews_warning` | panel_day_engine / runtime merge | 전조용 | 설명용 | 가능 | precursor report, detailed, master guide | final 신호 | earliest warning marker 후보 |
| `pre_alarm` | panel_day_engine / runtime merge | 전조용 | 설명용 | 가능 | precursor report, detailed | final/critical 확정 | 규칙 기반 이상 징후를 부드럽게 묶는 표현으로만 노출 |
| `prefault_cond_mid` | panel_day_engine / runtime merge | 전조용 | 내부 전용 | 제한적 | detailed, precursor summary(집계형) | 단독 승격 근거 | 단독 노출보다 aggregate count가 적합 |
| `prefault_cond_ae` | panel_day_engine / runtime merge | 전조용 | 내부 전용 | 제한적 | detailed, precursor summary(집계형) | 원인 확정 | AE 기반 전조 조건 |
| `prefault_cond_dtw` | panel_day_engine / runtime merge | 전조용 | 내부 전용 | 제한적 | detailed, precursor summary(집계형) | root cause | DTW 기반 전조 조건 |
| `prefault_cond_ews` | panel_day_engine / runtime merge | 전조용 | 내부 전용 | 제한적 | detailed, precursor summary(집계형) | final path | EWS 기반 prefault condition |
| `fault_like_day` | panel_day_engine / runtime merge | 전조용과 고장 신호용 사이의 경계 신호 | 설명용 | 직접 노출 비권장 | detailed, aggregated precursor wording, raw-only fault signal explanation | final_fault와 동일 | Gate 3/4 decision log 최우선 항목 |
| `event_A` | panel_day_engine | 내부 전용 | 설명용 | 직접 노출 금지 | detailed only | precursor/fault label | event feature lineage용 |
| `critical_fault` | panel_day_engine | 고장 신호용 | 설명용 | 가능 | raw-only fault signal report, current 설명, detailed | precursor | 외부에는 `강한 고장 신호`로만 노출 |
| `critical_confirmed` | panel_day_engine | 고장 신호용 | 확정 경로 설명 | 가능 | raw-only fault signal report, detailed | 별도 원인군 | 외부에는 `강한 고장 신호 확정` |
| `final_fault` | panel_day_engine | 고장 신호용 | 확정 경로 설명 | 가능 | raw-only fault signal report, current 설명, detailed | 미래 예언 | 외부에는 `최종 고장 신호` |
| `critical_source` | panel_day_engine / runtime summary | 설명용 | 원인 후보 보조 | 제한적 | detailed, raw-only fault signal report, preview의 `기존 알고리즘 source` | 정상/비정상 판정 | `none`은 정상 의미가 아님 |
| `anom_subtype` | panel_day_engine / runtime summary | 설명용 | 사건 해석 보조 | 제한적 | detailed, analyst-facing report, precursor/fault summary(완곡형) | 확정 원인 | degradation/shadow 같은 시간 패턴 근거 |
| `mid_ratio` | panel_day_engine | 설명용 | 분석 feature | 숫자 직접 노출은 분석용에 한정 | detailed, analyst-facing note | 단독 판정 라벨 | 정오 출력비 |
| `mid_v_ratio` | panel_day_engine | 설명용 | 분석 feature | 숫자 직접 노출은 분석용에 한정 | detailed, analyst-facing note | bypass/fault 확정명 | MLPE 해석에 중요 |
| `mid_i_ratio` | panel_day_engine | 설명용 | 분석 feature | 숫자 직접 노출은 분석용에 한정 | detailed, analyst-facing note | 확정 근거 단독 사용 | 전류 전달 이상 해석 보조 |
| `v_drop` | panel_day_engine | 설명용과 고장 신호 보조 | precursor wording 보조 | direct exposure 제한 | detailed, raw-only fault signal explanation, precursor의 완곡 표현 | direct hard-evidence label | operator-facing에는 `상대 전압 이탈 징후` 수준으로만 완곡화 |

## 6. 역할별 해석 지침
### 6.1 precursor 쪽에 남겨도 되는 신호
- `pre_ews`
- `ews_warning`
- `pre_alarm`
- `prefault_cond_mid`
- `prefault_cond_ae`
- `prefault_cond_dtw`
- `prefault_cond_ews`

조건:
- direct field보다는 `누적 전조 축`, `대표 전조 신호`, `규칙징후`처럼 집계/완곡 표현을 우선한다.

### 6.2 precursor에 직접 쓰지 말아야 하는 신호
- `critical_fault`
- `critical_confirmed`
- `final_fault`
- `event_A`

원칙:
- precursor report의 row inclusion이나 operator wording을 이 신호 이름으로 직접 설명하지 않는다.

### 6.3 fault signal report에서 중심이 되는 신호
- `critical_fault`
- `critical_confirmed`
- `final_fault`

원칙:
- `확정 경로`는 이 셋 중 주 경로를 하나 고르고,
- 나머지는 `고장 신호 요약` 또는 보조 근거로만 정리한다.

### 6.4 설명 신호로만 남겨야 하는 항목
- `critical_source`
- `anom_subtype`
- `mid_ratio`
- `mid_v_ratio`
- `mid_i_ratio`
- `v_drop`

원칙:
- 상태 라벨보다 `왜 그렇게 읽었는가`를 설명하는 데 쓴다.
- 원인 확정, 정상 판정, 미래 예언으로 번역하지 않는다.

## 7. artifact별 허용 노출 수준
| artifact | 허용 신호 수준 | 비고 |
| --- | --- | --- |
| `fault_panel_result_precursor_report_v1.csv` | 전조용 + 완곡한 설명용 | hard evidence direct naming 금지 |
| `fault_panel_result_raw_only_fault_signal_report_v1.csv` | 고장 신호용 + 설명용 | raw-only 기반임을 항상 명시 |
| `fault_panel_result_current_*` | 운영 요약용 | internal field direct exposure 최소화 |
| `fault_panel_result_detailed_report_v1.xlsx` | 전부 허용 | analyst-facing lineage 문서 |
| `fault_panel_result_master_report_v1.md` | 안내/정의용 | artifact 읽는 순서와 역할 차이를 설명 |

## 8. 바로 decision log에 올려야 할 항목
- `fault_like_day`를 Gate 3 precursor 승격 쪽에 더 가깝게 둘지, Gate 4 hard evidence 경계 쪽에 더 가깝게 둘지
- `event_A`를 완전히 internal-only로 고정할지
- `v_drop`의 operator-facing 노출 상한을 어디까지 둘지
- `critical_source=none`의 외부 wording을 어떻게 잠글지
- `prefault_cond_*`를 각각 노출할지, aggregate count만 노출할지

## 9. Gate 2 체크리스트
- 같은 신호가 artifact마다 다른 상태 라벨로 쓰이지 않는가
- precursor report에 hard evidence direct naming이 새어 나오지 않는가
- raw-only fault signal report가 raw-only 기반임을 숨기지 않는가
- `critical_source`나 `anom_subtype`가 확정 원인처럼 읽히지 않는가
- numeric feature가 단독 판정명으로 번역되지 않는가

## 10. 근거 source
- [panel_day_engine.py](/Users/b9gc/pvdiag/pv_ae/panel_day_engine.py)
- [runtime_rawonly_chain_common_v1.py](/Users/b9gc/pvdiag/research/prognostics/runtime_rawonly_chain_common_v1.py)
- [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py)

## 11. 다음 연결 문서
- 상위 로드맵:
  - [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- Gate 1 용어 사전:
  - [OPS_CONALOG_RUNTIME_GATE1_GLOSSARY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE1_GLOSSARY_V1.md)
- Gate 2A observability / evidence availability matrix:
  - [OPS_CONALOG_RUNTIME_GATE2A_OBSERVABILITY_EVIDENCE_MATRIX_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2A_OBSERVABILITY_EVIDENCE_MATRIX_V1.md)
- Gate 3 precursor 승격 규칙 초안:
  - [OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md)
- 결정 로그 템플릿:
  - [OPS_CONALOG_RUNTIME_DECISION_LOG_TEMPLATE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_TEMPLATE_V1.md)
- 브랜치/파킹 로트 템플릿:
  - [OPS_CONALOG_RUNTIME_BRANCH_PARKING_LOT_TEMPLATE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_PARKING_LOT_TEMPLATE_V1.md)
