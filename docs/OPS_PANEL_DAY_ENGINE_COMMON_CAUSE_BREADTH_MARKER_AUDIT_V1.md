# OPS_PANEL_DAY_ENGINE_COMMON_CAUSE_BREADTH_MARKER_AUDIT_V1

## 목적
- routing gap audit에서 드러난 `breadth_without_current_marker` 패턴을 실제 candidate rule로 시험한다.
- detector logic은 바꾸지 않고, simple breadth-based routing marker가 `non_panel_or_common_cause` case를 current marker보다 더 잘 설명하는지 본다.

## 왜 routing gap audit 다음 단계가 breadth marker 시험인가

직전 audit에서 `non_panel_or_common_cause` case는:

- `group_off_like`
- `shadow_like`

같은 current routing marker에는 거의 잡히지 않았지만,

- `final_fault_panel_fraction`
- `pre_alarm_panel_fraction`
- `ews_warning_panel_fraction`

의 site breadth는 꽤 크게 나타났다.

즉 현재 공통원인 routing 약점은 “marker가 전혀 없었다”기보다  
“marker 정의가 breadth를 반영하지 못했다”는 쪽에 더 가깝다.

## 왜 current marker만으로는 부족해 보이나

현 truth는 group/inverter/common-cause 쪽인데:

- 같은 날짜 또는 인접 날짜에 여러 panel이 함께 final fault / pre-alarm / warning을 보임
- 하지만 `group_off_like`, `shadow_like` 는 비어 있음

이 패턴이면 current marker는 too narrow일 수 있다.  
따라서 breadth 자체를 routing feature 후보로 올려서:

- positive capture
- contamination

을 함께 봐야 한다.

## 왜 positive capture vs contamination tradeoff가 핵심인가

breadth rule은 쉽게 넓어질 수 있다.  
그래서 common-cause positive를 잘 잡더라도:

- precursor-bearing local fault
- abrupt local / none-visible fault

에도 많이 켜지면 routing marker로는 부적절하다.

이번 audit은 그래서 각 candidate rule마다:

- `positive_capture_rate`
- `precursor_negative_trigger_rate`
- `abrupt_negative_trigger_rate`
- `contamination_score`

를 같이 본다.

즉 “잘 잡는가”와 “엉뚱한 local case에도 켜지는가”를 동시에 확인하는 단계다.

## 시험하는 breadth marker family

다음 네 family를 비교한다.

1. `final_fault` breadth threshold
2. `pre_alarm` breadth threshold
3. `ews_warning` breadth threshold
4. 세 가지 중 하나라도 threshold를 넘는 `any_breadth`

각 family에 대해:

- window
  - `same_day`
  - `plusminus_3d`
  - `plusminus_7d`
- threshold
  - `0.05`
  - `0.10`
  - `0.15`
  - `0.20`

를 sweep 한다.

## 어떤 결과가 breadth marker 추가를 정당화하나

다음이면 정당화된다.

- `positive_capture_rate` 가 current marker보다 뚜렷하게 높음
- contamination이 낮음
- 특히 좁은 window (`same_day` 또는 `±3d`) 와 비교적 높은 threshold에서도 capture가 유지됨

이 경우 breadth-based routing marker를 operator/evaluation layer에 추가할 근거가 생긴다.

## 어떤 결과면 descriptive-only를 유지해야 하나

다음이면 breadth marker 추가 근거가 약하다.

- capture는 오르지만 precursor 또는 abrupt negative contamination이 같이 커짐
- 높은 capture를 위해 너무 넓은 window나 너무 낮은 threshold가 필요함
- 추천 규칙조차 practical contamination 수준을 넘김

이 경우 `non_panel_or_common_cause` 는 당분간 routing denominator보다 descriptive bucket으로 남기는 편이 안전하다.
