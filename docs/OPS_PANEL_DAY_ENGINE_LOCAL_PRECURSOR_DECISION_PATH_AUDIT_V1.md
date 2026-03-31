# OPS_PANEL_DAY_ENGINE_LOCAL_PRECURSOR_DECISION_PATH_AUDIT_V1

## 목적

threshold replay와 context suppressor audit 다음 단계에서 필요한 질문은 이것이다.

- persisted output만으로 봤을 때 panel_day_engine local precursor alert가 어떤 decision path를 따라 나타났거나, 나타나지 않았는가

즉 이번 patch는 새 rule을 만들지 않는다.

- current helper alert가 왜 있었는지
- visible signal은 있었는데 왜 ews_warning이 안 켜졌는지
- ews_warning은 있었는데 왜 prefault_B / pre_alarm으로 escalation되지 않았는지
- 아예 persistence가 부족해서 복원이 안 되는지

를 가능한 범위 안에서 분해한다.

## 왜 threshold/suppressor replay 다음에 decision path audit가 맞는가

replay audit는 “덜 보수적인 shadow rule을 쓰면 잡히는가”를 보여준다.

하지만 그 결과만으로는 다음을 구분하기 어렵다.

- 실제 engine path에서 ews 단계가 막힌 것인지
- ews는 있었지만 helper escalation이 약한 것인지
- 아니면 필요한 internal gate가 persistence 되지 않아 복원이 안 되는 것인지

그래서 이제는 replay보다 한 단계 더 engine 의사결정에 가까운 path audit가 필요하다.

## 왜 helper output을 현재 engine alert의 ground truth로 쓰는가

이번 audit에서 현재 engine local precursor alert의 persisted ground truth는 다음 세 가지다.

- `ews_warning_flag`
- `prefault_B_flag`
- `pre_alarm_flag`

이 세 플래그는 이미 helper output과 shadow artifact로 materialize 되어 있다.

따라서 현재 engine이 실제로 “alert를 냈다/안 냈다”는 판단은 이 helper-derived shadow를 기준으로 읽는 것이 맞다.

## 왜 unavailable internal gate는 guessed 하면 안 되는가

`panel_day_engine.py` 안의 일부 조건은 persistence 되어 있지 않다.

대표적으로:

- `cond_mid` 는 `pf40_mid_mean` rolling mean 기반인데 현재 shadow에는 없다
- `pre_ews`
- site-event gating state
- exact `ae_strength` / `dtw_strength` / `hs_strength`

이런 값은 추정으로 채우면 audit가 detector를 발명하는 쪽으로 흘러간다.

그래서 이번 patch는 다음 원칙을 쓴다.

- raw metric으로 proxy 가능한 것은 `proxy` 로만 복원
- 필요한 입력이 truly absent 하면 `unavailable`
- unavailable 을 false 로 강제하지 않음

## proxy와 unavailable의 경계

이번 audit에서:

- `cond_ae_proxy`: persisted `recon_error` 의 site-p90 proxy
- `cond_dtw_proxy`: persisted `dtw_dist` 의 site-p90 proxy
- `cond_hs_proxy`: persisted `hs_score` 의 site-p90 proxy

반면:

- `cond_mid_proxy` 는 rolling mean input이 없어 unavailable 로 둔다

즉 “무엇을 복원할 수 있는가”보다 “무엇을 복원할 수 없는가”를 명확히 보고하는 것이 더 중요하다.

## day_path_state 의미

### `visible_signal_no_ews`

persisted raw signal proxy는 보이지만 `ews_warning_flag` 는 없는 날이다.

이 결과가 많으면 EWS gating 또는 연속성 조건이 너무 보수적일 가능성이 있다.

### `ews_only`

`ews_warning_flag` 는 있지만 shape/distance proxy 추가 증거가 보이지 않는 날이다.

### `ews_plus_shape_or_distance`

`ews_warning_flag` 와 shape/distance proxy가 함께 보이는 날이다.

### `prefault_B_day`

helper `prefault_B` 가 실제로 켜진 날이다.

### `pre_alarm_day`

helper `pre_alarm` 이 실제로 켜진 날이다.

### `no_visible_signal`

적어도 일부 key proxy는 계산 가능했지만 visible signal은 보이지 않는 날이다.

### `unresolved_due_to_unpersisted_inputs`

필요한 proxy 자체를 계산할 수 없어 clean classification이 불가능한 날이다.

## dominant_miss_reason_class 의미

### `no_visible_signal_before_fault`

bounded window 전체에서 visible signal day가 없었다.

### `visible_signal_but_no_ews_warning`

visible signal day는 있었지만 `ews_warning` 은 끝내 나타나지 않았다.

이 경우는 EWS gating retune 후보가 된다.

### `ews_warning_without_alert_escalation`

`ews_warning` 은 있었지만 `prefault_B` / `pre_alarm` 으로 escalation 되지 않았다.

이 경우는 helper escalation retune 후보가 된다.

### `helper_alert_hit`

bounded window 안에서 helper alert 자체가 있었다.

이 경우는 “miss”라기보다 current helper path가 실제로 작동한 케이스다.

### `unresolved_due_to_unpersisted_inputs`

current persistence만으로는 path reconstruction이 부족하다.

이 경우는 retune보다 persistence expansion이 먼저일 수 있다.

## 어떤 결과가 어떤 후속 조치를 정당화하는가

### A) EWS gating retune

- `visible_signal_but_no_ews_warning` 가 반복적으로 많다
- helper alert는 거의 없고, raw visible signal만 쌓인다

### B) prefault_B / pre_alarm escalation retune

- `ews_warning_without_alert_escalation` 가 많이 나온다
- `ews_warning` 은 있었는데 helper escalation이 비어 있다

### C) persistence expansion before any retune

- `unresolved_due_to_unpersisted_inputs` 가 의미 있게 많다
- 또는 핵심 path가 unavailable proxy 때문에 자주 끊긴다

이 경우는 threshold를 먼저 바꾸는 것보다, 먼저 더 많은 engine-native state를 persistence 하는 것이 맞다.
