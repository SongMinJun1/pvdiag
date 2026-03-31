# OPS_PANEL_DAY_ENGINE_LOCAL_PRECURSOR_ELIGIBILITY_AUDIT_V1

## 목적
- `panel_day_engine` 의 local precursor head를 평가할 때, 모든 `true_positive` local fault를 같은 분모로 두는 불공정을 줄인다.
- 먼저 local-fault case를 `progressive_local_precursor_expected`, `abrupt_local_precursor_unexpected`, `unknown_local_temporality` 로 나눈 뒤, precursor-eligible subset에서만 hit rate를 다시 계산한다.
- 이 패치는 엔진을 바꾸지 않는다. 이미 persist된 shadow artifact와 cohort audit 결과를 다시 해석하는 audit layer다.

## 왜 필요한가
- 모든 `true_positive` local fault가 precursor를 기대할 수 있는 패턴은 아니다.
- fault 직전 1일 이내에 갑자기 무너지는 case는 local precursor head가 켜지지 않아도 불합리하게 실패로 세면 안 된다.
- 따라서 `progressive` 와 `abrupt` 를 분리하지 않으면 precursor recall이 구조적으로 과소평가될 수 있다.

## 입력과 기준
- `_share/panel_day_engine_local_precursor_shadow_v1.csv`
- `_share/panel_day_engine_local_precursor_cohort_cases_v1.csv`
- `_share/panel_date_reaudit_working.csv`
- optional: `_share/vendor_reply_adjudication_latest.csv`

이 audit는 다음을 그대로 재사용한다.
- positive cohort: `candidate_validity == true_positive`
- bounded inspection window: `[fault_start_date - 30 days, fault_start_date)`
- raw-signal day rule: miss audit와 동일한 p90/electrical criteria

## temporality class 정의

### 1) progressive_local_precursor_expected
- bounded raw-signal day가 2일 이상
- earliest bounded raw-signal lead가 2일 이상

이 경우에만 `precursor_eligible_flag = 1` 이다.

### 2) abrupt_local_precursor_unexpected
- bounded raw-signal day가 1일 이하
- 그리고 첫 strong day가 fault 0~1일 전이거나
- final 1-day pre-fault zone에서 `mid_ratio <= 0.10`, `mid_v_ratio <= 0.10`, `v_drop >= 0.90` 급락이 보이는 경우

### 3) unknown_local_temporality
- progressive 조건도 아니고 abrupt 조건도 아닌 나머지

## 왜 fair denominator 인가
- `true_positive` 전체는 local fault cohort로는 맞지만, precursor head fairness denominator로는 너무 넓다.
- precursor가 기대되는 progressive case만 따로 보면:
  - `precursor_eligible_hit_rate`
  - `ews_warning_eligible_hit_rate`
  - `prefault_B_eligible_hit_rate`
  - `pre_alarm_eligible_hit_rate`
를 더 해석 가능하게 볼 수 있다.

## anchor 처리
- cohort audit가 이미 만든 `fault_start_date`, `fault_start_source` 를 우선 재사용한다.
- 없으면 shadow artifact에서 `strict_trigger_date` 전후 30일 범위의 earliest `final_fault == 1` 을 다시 찾는다.
- 그것도 없으면 `strict_trigger_date` fallback을 쓴다.

## 이 patch가 바꾸지 않는 것
- `pv_ae/panel_day_engine.py` 탐지 로직
- `ews_warning`, `prefault_B`, `pre_alarm` 생성 규칙
- canonical truth contract

## 해석 가이드
- eligible hit rate가 높아지면:
  - 현재 엔진이 progressive local precursor에는 어느 정도 반응하고 있다는 뜻이다.
- eligible hit rate가 여전히 낮고 unknown이 많으면:
  - decision-path audit를 eligible subset에 다시 좁혀 보는 것이 합리적이다.
- abrupt 비중이 높으면:
  - 전체 `true_positive` 분모로 precursor를 재단하는 것이 unfair했다는 뜻이다.

## 무엇이 다음 단계를 정당화하나

### A) decision-path audit를 eligible cases only로 더 좁힐 근거
- `progressive_local_precursor_expected` 가 적지 않게 존재하고
- 그 안에서도 bounded hit가 충분히 낮은 경우

### B) core retune 논의보다 먼저 필요한 것
- `unknown_local_temporality` 가 크고
- persisted signal만으로는 progressive/abrupt 분리가 약한 경우

### C) 이 patch의 한계
- persisted raw signal과 helper outputs만 사용한다.
- `pre_ews`, `site_event_soft/hard`, 일부 내부 gate는 persist되어 있지 않으므로 여기서 새로 추정하지 않는다.
