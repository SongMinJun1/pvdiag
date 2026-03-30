# OPS_PANEL_DAY_ENGINE_LOCAL_PRECURSOR_SHADOW_V1

## 목적

이 패치는 `panel_day_engine.py`의 코어 탐지 로직을 바꾸지 않고, 엔진이 이미 계산하고 있는 local precursor head를 `_share`에 안정적으로 관측 가능한 shadow artifact로 고정한다.

white-box 감사 결과의 핵심은 다음이었다.

- local precursor logic 자체는 이미 엔진 안에 있다.
- 문제는 로직 부재가 아니라 persistence / evaluation 분리다.
- `pre_ews`, `ews_warning`, `prefault_B`, `pre_alarm`이 helper output에 흩어져 있어 panel-day 단위 재결합이 어렵다.

따라서 이 패치는 새로운 detector를 추가하는 것이 아니라, 기존 helper output을 panel-day grain으로 다시 묶는 bridge layer다.

## 왜 필요한가

현재 `panel_day_engine.py` 안에는 아래 local precursor head가 있다.

- `pre_ews`
- `ews_warning`
- `prefault_B`
- `pre_alarm`

하지만 canonical `panel_day_core.csv`에는 이들 중 raw/effective precursor head가 그대로 저장되지 않는다. 그래서 downstream audit과 evaluation은 local precursor head 자체가 아니라 다음과 같은 우회 산출물만 보게 된다.

- retrospective onset shadow
- actionability routing
- common-cause precursor audit

즉 현재의 핵심 문제는 precursor logic absence가 아니라 precursor observability gap이다.

## 이 shadow가 하는 일

`panel_day_core.csv`를 base row로 삼고, helper output이 존재할 때만 다음 정보를 안정적으로 결합한다.

- `ews_warning_flag`
- `prefault_B_flag`
- `pre_alarm_flag`
- `local_precursor_any_flag`
- `first_local_precursor_date_per_panel`
- `lead_days_to_final_fault`
- `alert_pattern`

또한 나중 audit을 위해 엔진의 핵심 evidence 컬럼을 함께 고정한다.

- `recon_error`
- `dtw_dist`
- `hs_score`
- `mid_ratio`
- `mid_v_ratio`
- `mid_i_ratio`
- `v_drop`
- `confirmed_fault`
- `critical_fault`
- `final_fault`
- `group_off_like`
- `shadow_like`

## 이 shadow가 답할 수 있는 질문

- 어떤 패널/날짜가 engine-native local precursor head에 포착되었는가
- 어떤 패널이 `ews_warning`만 있었는가, `prefault_B`만 있었는가, `pre_alarm`까지 갔는가
- local precursor가 최종 `final_fault`보다 며칠 먼저 나타났는가
- site별로 local precursor day와 final fault panel의 관계가 어떤가

## 아직 답할 수 없는 것

v1 shadow는 persisted helper output만 사용하므로 다음은 여전히 직접 복원할 수 없다.

- `pre_ews`
- `site_event_soft`
- `site_event_hard`

이 값들이 canonical output에 저장되지 않았기 때문이다. 따라서 v1 shadow는 아래를 완전히 설명하지 못한다.

- 왜 어떤 row가 `ews_warning` 직전 단계에서 멈췄는지
- 어떤 row가 site-event gate 때문에 suppress 되었는지

또한 `pre_alarm`의 full day-level history도 따로 저장되어 있지 않으므로, v1에서는 `ae_simple_panel_alarms.csv`의 `pre_alarm_start`를 panel-day row에 anchoring하는 보수적 복원만 수행한다.

## 왜 이 bridge가 먼저여야 하는가

코어 패치를 바로 시작하면 “기존에 이미 있던 precursor head”와 “새로 넣는 precursor logic”가 섞여 해석이 어려워진다.

반대로 이 shadow를 먼저 만들면 아래가 가능해진다.

- 현재 엔진의 local precursor head를 그대로 관측
- helper output과 canonical core 사이의 persistence gap을 정량화
- 이후 core patch가 필요한지, 아니면 persistence / evaluation rewiring만으로 충분한지 판단

즉 이 shadow는 core detector 변경 전의 가장 안전한 중간 bridge다.
