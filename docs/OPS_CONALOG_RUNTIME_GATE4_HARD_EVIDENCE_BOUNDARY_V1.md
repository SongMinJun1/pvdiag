# OPS Conalog Runtime Gate 4 Hard Evidence Boundary V1

## 1. 목적
- 본 문서는 `OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md`의 Gate 4 산출물인 `hard evidence boundary` 초안이다.
- 목적은 아래 여섯 가지다.
  - 어떤 신호를 공식적으로 `고장 신호`로 부를지 잠근다.
  - `confirmed dead path`, `critical path`, `fault-like path`를 서로 다른 강도로 정리한다.
  - `final_fault`, `critical_confirmed`, `critical_fault`, `fault_like_day`, `vdrop`의 관계를 분명히 한다.
  - 같은 사건을 두 번 말하지 않도록 precedence를 정한다.
  - operator-facing 표와 analyst-facing 표의 노출 강도를 분리한다.
  - Gate 3 precursor 승격 규칙과 충돌하지 않도록 hard evidence 경계를 먼저 명문화한다.

## 2. 사용 규칙
- 이 문서는 `고장 신호 경계`를 잠그는 문서다.
- 이 문서가 잠기기 전에는 아래 패치를 금지한다.
  - `final_fault`/`critical_fault`/`critical_confirmed` 의미를 바꾸는 코드 patch
  - `fault_like_day`를 hard evidence로 승격하는 patch
  - `vdrop` 단독을 hard evidence로 번역하는 patch
- 이 문서가 잠기기 전에도 허용되는 작업은 아래다.
  - wording patch
  - lineage 확인
  - precedence 정리
  - decision log 등록

## 3. 상태
- 현재 상태:
  - `working draft`
- 의미:
  - 현재 baseline과 권장 경계를 함께 적은 초안이며, Gate 3/5와 함께 refinement될 수 있다.

## 4. 먼저 분리해야 하는 네 가지 질문
### 4.1 질문 A. 지금 강한 전기 신호가 있는가
- 의미:
  - `critical_fault` 또는 그에 가까운 신호가 있는가

### 4.2 질문 B. 지금 confirm된 확정 경로가 있는가
- 의미:
  - `critical_confirmed` 또는 `confirmed_fault`를 통해 `final_fault`로 닫히는가

### 4.3 질문 C. fault-like 흔적만 있는가
- 의미:
  - `fault_like_day`가 있지만, 아직 confirm path는 아닌가

### 4.4 질문 D. 설명 신호만 있는가
- 의미:
  - `vdrop`, `critical_source`, `mid_v_ratio` 등은 보이지만, 그것만으로 hard evidence로 부를 수는 없는가

## 5. 상태 사다리
| 상태 | 의미 | operator-facing 허용 표현 | artifact 기본 위치 |
| --- | --- | --- | --- |
| `설명 신호` | 전기적/시계열 설명 근거가 존재 | 직접 노출 제한 | detailed / analyst note |
| `fault-like 경계 신호` | 뭔가 fault-like 하지만 아직 공식 hard evidence는 아님 | 직접 노출 비권장 | detailed / event semantics 보조 |
| `강한 고장 신호` | sustained critical path가 존재 | `강한 고장 신호` | raw-only fault signal report |
| `강한 고장 신호 확정` | critical path가 confirm됨 | `강한 고장 신호 확정` | raw-only fault signal report |
| `최종 고장 신호` | dead-like path 또는 confirmed critical path로 닫힘 | `최종 고장 신호` | current 설명 / raw-only fault signal report |
| `확정 경로` | 최종적으로 어떤 경로로 확정되었는지 한 줄로 정리한 값 | `확정 경로` | raw-only fault signal report / current 설명 |

## 6. Current Baseline
### 6.1 dead-like path
- `state_dead_eff`:
  - `data_bad` 아님
  - `mid_peer`가 alive threshold 이상
  - `mid_ratio <= dead threshold`
- `confirmed_fault`:
  - `state_dead_eff`가 `dead_days` 이상 이어진 segment

의미:
- dead-like segment가 기준 일수 이상 이어지면 confirm path가 열린다.

### 6.2 critical path
- `critical_like_raw`:
  - `v_drop`가 임계 이상
  - `mid_i_ratio`가 healthy-ish
  - `mid_ratio`가 critical range 안
  - trust-agnostic hit
- `critical_like_eff`:
  - `data_bad` 아님
  - `mid_peer` alive threshold 이상
  - `group_off_like` 아님
- `critical_fault`:
  - `critical_like_eff`가 `critical_days` 이상 이어진 segment

### 6.3 confirmed critical path
- `critical_confirmed`:
  - `critical_fault == True`
  - `mid_peer >= critical_peer_min`
  - panel별 critical days가 `critical_min_days` 이상
  - `mid_v_ratio` span이 `critical_vspan_max` 이하

의미:
- sustained critical path 중에서도 stability check까지 통과한 경우만 confirmed로 본다.

### 6.4 final path
- tuning level `p2`에서
  - `final_fault = confirmed_fault OR critical_confirmed`
- tuning level `p0/p1`에서
  - `final_fault = confirmed_fault`

의미:
- final fault는 dead-like confirm path 또는 confirmed critical path의 합집합이다.

### 6.5 critical_source baseline
- precedence:
  - `legacy`
  - `vdrop`
  - `vdrop_suspect`
  - `none`

의미:
- `critical_source`는 hard evidence 자체가 아니라, critical path의 source tag다.

### 6.6 runtime event semantics baseline
- runtime에서는 `strict_trigger = min(first_critical_fault, first_final_fault, first_fault_like)`
- 그리고 아래 조건이면 `fault_status = 고장`
  - `has_final`
  - `has_critical`
  - `has_fault_like`

주의:
- 이건 event semantics baseline이다.
- operator-facing hard evidence boundary와 1:1로 동일하다고 읽으면 안 된다.

## 7. Gate 4에서 잠그려는 핵심 원칙
### 7.1 `final_fault`는 공식 최상위 hard evidence다
- `final_fault`는 operator-facing에서 `최종 고장 신호`로 읽는다.
- `final_fault`는 미래 예언이 아니라 현재 시점 confirm path 결과다.

### 7.2 `critical_confirmed`는 confirm된 hard evidence다
- `critical_confirmed`는 `강한 고장 신호 확정`이다.
- operator-facing에서는 hard evidence로 볼 수 있다.
- 다만 `final_fault`와 같은 사건을 이중 카운트하면 안 된다.

### 7.3 `critical_fault`는 hard-evidence-adjacent signal이다
- `critical_fault`는 sustained critical path다.
- analyst-facing에선 충분히 중요하지만, operator-facing에선 `강한 고장 신호`로만 제한적으로 노출한다.
- `critical_fault` 단독은 `final_fault`와 같은 수준의 최종 확정이 아니다.

### 7.4 `fault_like_day`는 공식 hard evidence가 아니다
- `fault_like_day`는 경계 신호다.
- event semantics에선 trigger에 들어가더라도, Gate 4 문맥에선 아래를 잠근다.
  - `fault_like_day` 단독으로 operator-facing hard evidence로 승격하지 않는다.
  - `fault_like_day`를 `최종 고장 신호`로 번역하지 않는다.

### 7.5 `vdrop`는 hard evidence 자체가 아니라 critical path의 설명 근거다
- `vdrop`는 중요하다.
- 하지만 `vdrop` 단독은 hard evidence가 아니다.
- `vdrop`는 아래에 더 가깝다.
  - critical path 형성 근거
  - `critical_source` 설명
  - precursor/fault signal wording의 전기적 설명

### 7.6 `critical_source`는 source tag이지 상태 등급이 아니다
- `critical_source=legacy/vdrop/vdrop_suspect/none`는 상태 판정 그 자체가 아니다.
- 외부에는 `기존 알고리즘 source` 또는 설명 문구로만 제한적으로 노출한다.

## 8. Draft Boundary Rule
### 8.1 Tier 0. 설명 신호
- `vdrop`
- `critical_source`
- `mid_ratio`
- `mid_v_ratio`
- `mid_i_ratio`
- `anom_subtype`

원칙:
- 이유 설명용이다.
- 단독 hard evidence로 쓰지 않는다.

### 8.2 Tier 1. fault-like 경계 신호
- `fault_like_day`

원칙:
- fault-like하다는 신호는 되지만 공식 hard evidence는 아니다.
- event semantics나 retrospective trigger 보조에는 쓸 수 있다.
- operator-facing hard evidence label로는 쓰지 않는다.

### 8.3 Tier 2. 강한 고장 신호
- `critical_fault`

원칙:
- sustained critical path다.
- analyst-facing fault signal report에 포함 가능하다.
- operator-facing current 요약에서는 `강한 고장 신호` 수준으로만 제한적으로 노출한다.

### 8.4 Tier 3. confirm된 강한 고장 신호
- `critical_confirmed`

원칙:
- confirm된 critical path다.
- hard evidence로 인정한다.
- 다만 `final_fault`와 precedence를 정해 중복 서술을 피한다.

### 8.5 Tier 4. 최종 고장 신호
- `final_fault`

원칙:
- dead-like confirmed path 또는 confirmed critical path의 최상위 결과다.
- operator-facing에선 가장 우선되는 hard evidence다.

## 9. Canonical Precedence Rule
### 9.1 상태 precedence
`final_fault > critical_confirmed > critical_fault > fault_like_day > explanation-only`

### 9.2 report 서술 precedence
- `확정 경로`:
  - 먼저 `final_fault` 경로를 본다
  - 없으면 `critical_confirmed`
  - 없으면 `critical_fault`
  - `fault_like_day`는 `확정 경로`에 넣지 않는다

### 9.3 같은 사건 중복 금지
- 같은 날짜 구간에서 `final_fault`와 `critical_confirmed`가 함께 보이면
  - `확정 경로`는 1건으로 말한다
  - `critical_confirmed`는 보조 근거로만 남긴다

## 10. 승격 금지 규칙
- `fault_like_day` 단독을 operator-facing hard evidence로 올리지 않는다.
- `vdrop` 단독을 hard evidence로 올리지 않는다.
- `critical_source=legacy`만으로 확정이라고 말하지 않는다.
- `critical_fault`를 자동으로 `final_fault`와 같은 말로 쓰지 않는다.
- `final_fault`와 `critical_confirmed`를 같은 사건에서 두 건으로 세지 않는다.
- `none` source를 정상이라고 번역하지 않는다.

## 11. 꼭 남겨야 하는 구분
### 11.1 `critical_fault` vs `critical_confirmed`
- `critical_fault`:
  - sustained critical path
- `critical_confirmed`:
  - stability check까지 통과한 confirm path

### 11.2 `critical_confirmed` vs `final_fault`
- `critical_confirmed`:
  - confirm된 critical path
- `final_fault`:
  - 최상위 공식 final 결과

### 11.3 `fault_like_day` vs hard evidence
- `fault_like_day`:
  - fault-like 경계 신호
- hard evidence:
  - operator-facing에서 `고장 신호`로 부를 수 있는 신호

### 11.4 `vdrop` vs `critical_source`
- `vdrop`:
  - 전기적 설명 근거
- `critical_source`:
  - critical path의 source tag

## 12. 현재 코드와 이후 코드 패치가 갈라지는 지점
### 12.1 현재 baseline
- runtime event semantics는 `fault_like_day`까지 trigger 축에 포함한다.
- `fault_status=고장`에도 `has_fault_like`가 들어간다.
- panel_day_engine에서 `final_fault`는 `confirmed_fault OR critical_confirmed`다.

### 12.2 이후 패치에서 바꿔야 할 가능성이 높은 지점
- operator-facing hard evidence 정의와 runtime event semantics 정의의 분리 명시
- `fault_like_day`를 status gate에서 얼마나 멀리 둘지 재검토
- `critical_fault`의 operator-facing 노출 수준 재조정
- `확정 경로`를 dead-like path / critical-confirmed path로 더 명시적으로 분기
- raw-only fault signal report의 강도 등급 컬럼 추가

## 13. Decision Log에 바로 올릴 질문
- `fault_like_day`를 runtime event semantics trigger에 계속 둘 것인가
- `critical_fault`를 operator-facing hard evidence로 어느 수준까지 허용할 것인가
- `critical_confirmed`와 `final_fault`를 current preview에서 어떻게 합쳐 말할 것인가
- `confirmed_fault`를 external wording으로 별도 드러낼 것인가
- dead-like path와 critical path를 완전히 별도 경로명으로 둘 것인가

## 14. Gate 4 체크리스트
- `확정 경로`를 한 줄로 정할 수 있는가
- `final_fault`와 `critical_confirmed`를 같은 사건에서 두 번 말하지 않는가
- `fault_like_day`를 hard evidence처럼 보여주지 않는가
- `vdrop`를 상태 등급이 아니라 설명 근거로 유지하는가
- operator-facing current와 analyst-facing raw-only fault signal report의 강도 표현이 섞이지 않는가

## 15. 근거 source
- [panel_day_engine.py](/Users/b9gc/pvdiag/pv_ae/panel_day_engine.py)
- [runtime_rawonly_chain_common_v1.py](/Users/b9gc/pvdiag/research/prognostics/runtime_rawonly_chain_common_v1.py)
- [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py)

## 16. 다음 연결 문서
- 상위 로드맵:
  - [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- Gate 2 signal role matrix:
  - [OPS_CONALOG_RUNTIME_GATE2_SIGNAL_ROLE_MATRIX_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2_SIGNAL_ROLE_MATRIX_V1.md)
- Gate 3 precursor 승격 규칙 초안:
  - [OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md)
- Gate 5 출력 정책 초안:
  - [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- Gate 4A event semantics / operator semantics contract:
  - [OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md)
- 결정 로그 템플릿:
  - [OPS_CONALOG_RUNTIME_DECISION_LOG_TEMPLATE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_TEMPLATE_V1.md)
