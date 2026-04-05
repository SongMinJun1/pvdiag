# OPS_PANEL_DAY_ENGINE_NON_PRECURSOR_PERFORMANCE_AUDIT_V1

## 목적
- precursor-bearing detectable-now 성능을 분리한 뒤, 남은 bucket을 한 분모로 섞지 않고 따로 평가한다.
- 이번 단계는 detector logic을 바꾸지 않고, step 4 evaluation scaffold를 완성하는 audit layer다.

## 왜 step 4는 bucket별로 나눠야 하나

`eval_bucket_v2` 를 만든 이유는 남은 case들이 같은 질문을 답하지 않기 때문이다.

- `abrupt_or_no_precursor_now`
  - panel-local fault일 수는 있지만 precursor를 기대하기 어려운 row
- `non_panel_or_common_cause`
  - panel-local precursor detector의 책임 분모가 아니라 routing/classification 문제
- `unknown_needs_review`
  - 아직 denominator에 넣기 어려운 descriptive bucket

따라서 step 4는 bucket별 metric 정의 자체가 달라야 한다.

## 왜 abrupt/no-precursor는 detection timing 문제인가

abrupt bucket의 핵심 질문은:

- fault start 직전이나 직후 며칠 안에 hard fault marker가 잡히는가

이다.

이 bucket은 precursor lead-time이 아니라:
- `confirmed_fault`
- `critical_fault`
- `final_fault`

가 anchor 근처에 얼마나 빨리 도달하는지로 보는 것이 맞다.

즉 여기서는 “전조를 얼마나 빨리 잡았는가”보다  
“fault 시점 전후에 hard fault로 얼마나 빨리 수렴하는가”가 핵심이다.

## 왜 non-panel/common-cause는 routing/classification 문제인가

`group_or_inverter_side_like` 는 문헌과 branch evidence 모두 panel-local precursor 분모와는 다르다.

여기서 중요한 질문은:
- `group_off_like`
- `shadow_like`
- `common_cause_like`

같은 routing signal이 anchor 주변에서 충분히 보이는가이다.

동시에:
- `ews_warning`
- `pre_alarm`

같은 local precursor alert contamination이 얼마나 섞이는지도 봐야 한다.  
그래야 common-cause/system-level routing layer와 panel-local precursor layer가 얼마나 분리되어 있는지 해석할 수 있다.

## 왜 unknown_needs_review는 descriptive only인가

unknown bucket은 아직 다음 중 하나가 남아 있다.

- temporality 정의 미완성
- family mapping 미완성
- review truth 자체가 불안정

이 상태에서 denominator metric에 넣으면 수치만 늘고 해석은 약해진다.  
그래서 이번 단계에서는 case count와 descriptive reason만 남기고 공식 rate 계산에서는 제외한다.

## 이번 단계가 evaluation scaffold를 어떻게 완성하나

이제 initial evaluation scaffold는 네 층으로 정리된다.

1. `precursor_bearing_detectable_now`
- preferred onset truth 기준 precursor performance / lead-time 평가

2. `abrupt_or_no_precursor_now`
- hard fault detection timing 평가

3. `non_panel_or_common_cause`
- routing/classification 평가

4. `unknown_needs_review`
- descriptive review only

즉 detector를 더 건드리기 전에, 현재 branch에서 무엇을 어떤 metric으로 평가해야 하는지의 초기 프레임을 한 번 닫는 단계다.
