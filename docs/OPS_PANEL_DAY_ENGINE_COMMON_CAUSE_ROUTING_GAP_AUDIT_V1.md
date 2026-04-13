# OPS_PANEL_DAY_ENGINE_COMMON_CAUSE_ROUTING_GAP_AUDIT_V1

## 목적
- `eval_bucket_v2 == non_panel_or_common_cause` case가 왜 현재 routing marker로 설명되지 않는지 분해한다.
- detector logic은 바꾸지 않고, breadth와 timing 관점에서 현재 common-cause bucket의 약점을 진단한다.

## 왜 non_panel_or_common_cause가 step 4의 약점이었나

이 bucket은 panel-local precursor 성능 문제가 아니다.  
핵심 질문은:

- 실제로 group/common-cause 패턴이 있었는데 현재 marker가 못 잡은 것인가
- 아니면 truth case 자체가 local-fault-like에 더 가까운 것인가
- 혹은 marker는 있었지만 anchor와 timing이 어긋난 것인가

기존 step 4에서는 `group_off_like`, `shadow_like` 만으로 이 질문을 충분히 분해하지 못했다.

## 왜 current marker가 부족할 수 있나

현재 branch의 common-cause routing marker는 비교적 좁다.

- `group_off_like`
- `shadow_like`

하지만 현장/재감사 truth는 다음 같은 상황을 포함할 수 있다.

- 여러 패널이 동시에 final fault 또는 pre-alarm breadth를 보이지만 marker 정의에는 안 걸리는 경우
- marker는 있으나 anchor ±3일 안이 아니라 ±7일 바깥쪽에서만 나타나는 경우
- 실제로는 local fault-like case인데 group-side truth로 남아 있는 경우

그래서 marker 존재 여부만 보는 대신 site breadth와 anchor 정렬을 같이 봐야 한다.

## 왜 breadth와 timing misalignment를 함께 보나

이번 audit은 각 case에 대해 anchor ±7일 window를 보고:

- site-level breadth
  - `final_fault_panel_fraction`
  - `pre_alarm_panel_fraction`
  - `ews_warning_panel_fraction`
  - `group_off_like_panel_fraction`
  - `shadow_like_panel_fraction`
- current marker diagnostics
  - `any_group_off_like_flag`
  - `any_shadow_like_flag`
  - `any_common_cause_like_flag`
- anchor 인접성
  - marker가 ±3일 안에는 없고 ±7일 안에만 있는지

를 함께 계산한다.

이렇게 해야:

- breadth는 넓지만 current marker는 없는 case
- marker는 있지만 timing이 어긋난 case
- 사실상 local fault-like인 case
- signal 자체가 너무 약한 case

를 분리할 수 있다.

## routing_gap_class 해석

- `breadth_without_current_marker`
  - site breadth는 충분히 넓은데 `group_off_like` / `shadow_like`가 없어 marker 재정의 후보
- `local_fault_like_not_common_cause_like`
  - breadth도 좁고 marker도 없어 common-cause보다 local fault-like 또는 truth reassignment 후보
- `current_marker_present_but_misaligned_window`
  - marker는 있는데 anchor ±3일과 어긋나 있어 window 정의 또는 anchor 정의 재검토 후보
- `weak_or_sparse_signal`
  - breadth와 marker가 모두 약해 현재 branch에서는 강한 해석이 어려움
- `unclear`
  - 위 규칙으로 깔끔히 분류되지 않는 잔여 case

## 어떤 결과가 다음 행동을 정당화하나

### A) routing marker 재정의

다음이 반복되면 정당화된다.

- `breadth_without_current_marker` 비중이 높음
- `max_final_fault_panel_fraction` 또는 `max_pre_alarm_panel_fraction` 이 의미 있게 큼
- 현장/common-cause truth는 강한데 current marker hit는 거의 없음

이 경우 breadth 기반 common-cause marker 또는 richer routing feature가 필요하다.

### B) 일부 truth case 재배치

다음이 반복되면 정당화된다.

- `local_fault_like_not_common_cause_like` 비중이 높음
- breadth도 좁고 marker도 없음
- case-level final fault/pre-alarm이 사실상 단일 panel 수준에 머묾

이 경우 일부 case는 non-panel/common-cause bucket에서 빼는 것이 더 타당하다.

### C) 당분간 descriptive bucket 유지

다음이면 정당화된다.

- `weak_or_sparse_signal` 과 `unclear` 가 대부분
- breadth/marker 어느 쪽도 일관되지 않음
- 현재 branch evidence만으로 재정의/재배치가 불안정함

이 경우 이 bucket은 아직 공식 성능 분모보다 descriptive review bucket으로 두는 편이 안전하다.
