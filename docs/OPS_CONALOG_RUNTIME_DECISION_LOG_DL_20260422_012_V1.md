<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_012_V1

## 빠른 요약
| decision_id | status | related_gate | topic | decision | owner | date_decided |
| --- | --- | --- | --- | --- | --- | --- |
| DL-20260422-012 | accepted | Gate 2C / Gate 7 | `prefault_B_effective` attention-grade scope lock | `prefault_B_effective`는 local precursor eligibility와 explanation/additive precursor evidence에는 사용하되, 아직 `고위험 관찰` 단독 attention-grade trigger로는 사용하지 않는다 | Codex + 사용자 합의 | 2026-04-22 |

## [DL-20260422-012] `prefault_B_effective` attention-grade scope lock
- `status`: accepted
- `date_first_raised`: 2026-04-22
- `date_decided`: 2026-04-22
- `related_gate`: Gate 2C / Gate 7
- `owner`: Codex + 사용자 합의
- `related_branch_ids`: []
- `related_parking_ids`: []

### 질문
- `prefault_B_effective_days`를 runtime redesign에서 어디까지 사용할 것인가.
- 특히 operator-facing `운영해석등급_ko`의 `고위험 관찰` 단독 승격 트리거로 바로 올릴 것인가.

### 배경
- [ONEPAGER.md](/Users/b9gc/pvdiag/ONEPAGER.md) 와 [OPS_PANEL_DAY_ENGINE_LOCAL_PRECURSOR_GATE_PERSISTENCE_V1.md](/Users/b9gc/pvdiag/docs/OPS_PANEL_DAY_ENGINE_LOCAL_PRECURSOR_GATE_PERSISTENCE_V1.md) 기준으로 `prefault_B`는 raw helper로 보존하고, `prefault_B_effective = prefault_B & ~common_cause_overlap`를 operator-facing precursor eligibility에 우선 사용하게 됐다.
- 현재 코드 [runtime_rawonly_chain_common_v1.py](/Users/b9gc/pvdiag/research/prognostics/runtime_rawonly_chain_common_v1.py)는 `first_secondary_warning`, `local_precursor_any_flag`, `alert_pattern`에서 `prefault_B_effective`를 우선 사용한다.
- 반면 [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py)의 `report_attention_grade()`는 아직 `prefault_B_effective_days`를 직접 등급 트리거로 쓰지 않는다.
- 현재 확인된 분포는 `conalog` 쪽 local precursor helper에서만 충분히 읽혔고, `gangui`, `ktc_ess`는 아직 같은 수준의 regenerated evidence가 모이지 않았다.

### 선택지
1. 선택지 A. `prefault_B_effective_days`를 즉시 `고위험 관찰` 단독 트리거로 올린다
   - 장점:
     - Option B 전조 누적이 긴 패널을 더 공격적으로 승격할 수 있다.
   - 단점:
     - tri-site 기준이 아직 얕다.
     - `pre_ews`, `ews_warning`, `pre_alarm`과 달리 helper-derived 신호를 바로 operator grade threshold에 넣게 된다.
     - common-cause overlap을 분리한 직후라, direct promotion이 너무 빠를 수 있다.
2. 선택지 B. `prefault_B_effective`는 local precursor eligibility와 explanation/additive evidence에는 사용하되, `운영해석등급_ko` 단독 트리거로는 아직 올리지 않는다
   - 장점:
     - 현재 코드/문서와 정합적이다.
     - raw helper 보존 + effective eligibility + operator grade 보수성을 함께 유지한다.
     - 이후 tri-site seed와 common-cause direct overlap 사례가 더 쌓이면 별도 decision으로 올릴 수 있다.
   - 단점:
     - Option B 강신호가 길게 누적돼도 현재 attention grade에는 직접 반영되지 않는다.
3. 선택지 C. `prefault_B_effective`를 explanation에서도 빼고 eligibility에만 제한한다
   - 장점:
     - operator-facing 해석이 가장 보수적이다.
   - 단점:
     - 이미 확보한 signal을 설명에서 잃는다.
     - why/how 추적성이 약해진다.

### 최종 결정
- 선택지 B를 채택한다.
- 규칙은 아래와 같다.
  1. `prefault_B`는 raw helper로 계속 보존한다.
  2. `prefault_B_effective`는 operator-facing precursor eligibility와 local precursor shadow gating에는 사용한다.
  3. `prefault_B_effective_days`는 precursor report, detailed definitions, reason/signal explanation에서 additive evidence로 사용한다.
  4. 하지만 `prefault_B_effective_days`만으로 `운영해석등급_ko = 고위험 관찰`을 직접 올리지는 않는다.
  5. 향후 attention-grade direct trigger로 올리려면 tri-site regenerated evidence, common-cause direct-overlap seed, 별도 threshold justification이 추가로 필요하다.

### 이유
- 신호 성격:
  - `prefault_B_effective`는 raw helper를 common-cause gate로 정제한 신호이지, 현 시점의 primary warning canonical trigger는 아니다.
- 근거 깊이:
  - 현재는 `conalog` 쪽 분포와 일부 runtime surface 반영은 확인됐지만, tri-site regenerated evidence와 official-current direct overlap 근거는 충분히 쌓이지 않았다.
- 역할 분리:
  - eligibility / explanation에는 올리되, operator grade direct trigger는 더 보수적으로 두는 것이 현재 설계 원칙과 맞다.

### 허용 패치
- `prefault_B_effective_days`를 precursor explanation, score-map additive evidence, analyst/support glossary에 반영하는 패치
- `prefault_B_common_cause_overlap`를 suppressor/common-cause risk 설명 축에 반영하는 패치
- 이후 tri-site evidence가 쌓였을 때 별도 DL로 attention-grade threshold를 검토하는 패치

### 금지 패치
- 별도 decision 없이 `report_attention_grade()`에 `prefault_B_effective_days >= N` 같은 단독 승격 규칙을 바로 넣는 패치
- `prefault_B_effective`를 `final_fault`, `critical_fault`, `fault_like_day`와 동급 hard trigger처럼 취급하는 패치
- common-cause overlap evidence가 여전히 얕은 상태에서 `Option B 유효 일수`만 보고 operator-facing 등급을 공격적으로 올리는 패치

### 필요한 문서 업데이트
- [OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md)
- [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)
- [ONEPAGER.md](/Users/b9gc/pvdiag/ONEPAGER.md)

### 필요한 코드 업데이트
- 없음
- 현재 [report_attention_grade()](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py:1731)는 이미 본 결정을 따른다.

### 검증 계획
- 문서 검증:
  - Gate 2C / Gate 7 / ONEPAGER가 본 결정을 모순 없이 참조하는지 확인
- 코드 검증:
  - `report_attention_grade()`가 여전히 `prefault_B_effective_days`를 직접 threshold에 쓰지 않는지 확인
- 실행 검증:
  - `python -m py_compile pv_ae/panel_day_engine.py`
  - conalog 1회 실행

### 롤백 트리거
- tri-site regenerated evidence에서 `prefault_B_effective`가 `고위험 관찰` direct trigger로 들어가야 한다는 근거가 반복적으로 확인되는 경우
- 현재 보수적 정책 때문에 long-lead precursor가 지속적으로 과소평가된다는 반례가 누적되는 경우

### 남겨둔 보류 질문
- 향후 `prefault_B_effective_days`를 `precursor_score`의 내부 additive axis로 더 강하게 반영할지
- 그때 direct threshold를 둘지, `pre_ews` / `ews_warning`와 결합형 규칙으로 둘지

### 관련 근거
- [ONEPAGER.md](/Users/b9gc/pvdiag/ONEPAGER.md)
- [OPS_PANEL_DAY_ENGINE_LOCAL_PRECURSOR_GATE_PERSISTENCE_V1.md](/Users/b9gc/pvdiag/docs/OPS_PANEL_DAY_ENGINE_LOCAL_PRECURSOR_GATE_PERSISTENCE_V1.md)
- [OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md)
- [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)
- [runtime_rawonly_chain_common_v1.py](/Users/b9gc/pvdiag/research/prognostics/runtime_rawonly_chain_common_v1.py)
- [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py)
