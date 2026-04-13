# OPS_PANEL_DAY_ENGINE_LOCAL_PRECURSOR_THRESHOLD_REPLAY_V1

## 목적

이 patch는 `panel_day_engine.py` 를 바꾸지 않고, 이미 persistence 된 local precursor shadow 위에서 대안 alert rule을 replay 해서 다음 질문에 답한다.

- 현재 bounded local precursor miss는 더 단순하거나 덜 보수적인 rule로 회복 가능한가
- 그 대가로 nuisance trigger는 얼마나 늘어나는가

즉 이것은 core detector change가 아니라 shadow replay audit이다.

## 왜 shadow replay인가

이번 audit는 engine-native local precursor head를 다시 학습하거나 재구현하지 않는다.

하는 일은 다음뿐이다.

- stable shadow artifact에서 bounded pre-window를 다시 읽는다
- persisted raw signal 기준으로 대안 rule을 계산한다
- positive cohort hit recovery와 nuisance cohort trigger rate를 같은 표에서 비교한다

그래서 결과가 좋아 보여도 곧바로 official behavior가 바뀌는 것은 아니다.

## 왜 hit recovery alone이 충분하지 않은가

positive cohort에서 trigger가 많이 회복돼도, nuisance cohort에서 같은 rule이 과도하게 켜지면 운영상 가치는 낮다.

예를 들어 다음 두 결과는 해석이 다르다.

- positive recovery는 크고 nuisance trigger는 거의 늘지 않음
- positive recovery는 크지만 nuisance trigger도 같이 크게 증가

첫 번째는 threshold/gating retune 후보가 될 수 있지만, 두 번째는 단순 완화가 아니라 persistence 또는 visibility 개선 쪽이 더 먼저일 수 있다.

## 왜 nuisance trigger rate가 중요한가

이번 replay의 nuisance cohort는 `group_side` 와 `false_positive` 다.

즉 다음 케이스들이다.

- local fault가 아닌 common-cause 또는 group-side 문제
- local fault로 보기 어려운 false positive

이 cohort에서 replay rule이 많이 켜지면, local precursor detector를 완화했을 때 운영상 불필요한 trigger가 얼마나 늘어날지를 미리 볼 수 있다.

## 왜 fault_start_source stratification이 중요한가

positive cohort 안에서도 anchor source가 다르다.

- `final_fault_first_true`
- `strict_trigger_fallback`

이 stratification은 replay rule이 어떤 종류의 case를 더 잘 회복하는지 구분해 준다.

예를 들어 replay가 `strict_trigger_fallback` case만 회복한다면, 실제 engine final-fault anchor와 가까운 케이스보다는 governance strict case에 더 민감한 것일 수 있다.

반대로 `final_fault_first_true` case까지 안정적으로 회복하면 core retune 근거가 더 강해진다.

## replay rule 의미

### `current_bounded_alert`

현재 persisted bounded alert head 그대로다.

- `ews_warning`
- `prefault_B`
- `pre_alarm`

이 rule은 비교 baseline 역할을 한다.

### `raw_signal_any_day`

bounded window 안에 raw-signal-positive day가 하루라도 있으면 trigger 한다.

가장 회복력이 크지만 nuisance 증가도 같이 보기 쉽다.

### `raw_signal_2day_persistence`

bounded window 안에 raw-signal-positive day가 2일 이상 있어야 trigger 한다.

`raw_signal_any_day` 보다 보수적이며, 일회성 spike를 줄이는지 보는 용도다.

### `shape_plus_electrical_combo`

같은 날에 다음 두 family가 함께 보여야 한다.

- shape family: `recon_error >= p90` or `dtw_dist >= p90` or `hs_score >= p90`
- electrical family: `mid_v_ratio <= 0.85` or `mid_i_ratio <= 0.85` or `v_drop >= 0.20`

단순 raw signal보다 더 구조적인 조합 rule이 nuisance를 얼마나 줄이는지 보는 용도다.

## 어떤 결과가 core threshold/gating retune을 정당화하는가

다음 결과가 동시에 보이면 core retune 근거가 강해진다.

- positive recovery가 current baseline보다 의미 있게 증가한다
- nuisance trigger rate 증가는 제한적이다
- `final_fault_first_true` positive에서도 trigger recovery가 보인다
- recovered cases가 confound 없는 local-fault 케이스에 집중된다

## 어떤 결과가 persistence/visibility improvement만 정당화하는가

다음 결과라면 core change보다 visibility 개선이 우선이다.

- 단순 replay는 positive recovery를 만들지만 nuisance trigger도 크게 오른다
- replay가 mostly `group_side` 나 `false_positive` 에도 같이 반응한다
- recovery가 raw-signal visibility만 보여주고 alert-level precision은 나빠진다

이 경우 더 먼저 필요한 것은:

- engine state persistence expansion
- suppression / gating visibility 개선
- bounded miss 분해 audit 고도화

## 결론

이 audit는 “더 완화하면 몇 건을 더 잡는가”만 보지 않는다.

핵심은 다음 tradeoff를 같은 표에서 보는 것이다.

- positive local-fault hit recovery
- nuisance triggering cost

그래야 core threshold/gating retune이 진짜 필요한지, 아니면 현재 알고리즘을 더 잘 보이게 만드는 persistence 개선이 먼저인지 판단할 수 있다.
