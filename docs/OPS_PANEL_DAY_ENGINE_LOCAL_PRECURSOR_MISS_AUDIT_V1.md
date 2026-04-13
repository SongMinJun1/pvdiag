# OPS_PANEL_DAY_ENGINE_LOCAL_PRECURSOR_MISS_AUDIT_V1

## 목적

이 감사는 bounded local precursor cohort audit 다음 단계다.

이전 audit가 답한 질문은 다음이었다.

- true-positive local fault cohort에서 bounded precursor alert가 실제로 있었는가

이번 audit가 답하는 질문은 그 다음이다.

- bounded precursor alert가 없었던 케이스는 왜 miss였는가

즉 detector를 새로 만드는 문서가 아니라, 이미 persisted 된 local precursor shadow와 raw daily evidence를 이용해 miss 원인을 설명하는 audit이다.

## 왜 bounded miss audit가 바로 다음 질문인가

cohort audit에서 bounded hit rate만 보면 두 해석이 동시에 가능하다.

- 엔진이 볼 만한 precursor signal이 실제로 없었다
- signal은 있었는데 alert head가 그걸 precursor로 채택하지 못했다

이 둘은 다음 조치를 완전히 다르게 만든다.

- signal 자체가 없으면 core logic을 당장 바꾸기 어렵다
- signal은 있는데 alert가 안 켜지면 threshold 또는 gating을 다시 봐야 한다

그래서 bounded miss를 다시 30일 창으로 내려가 설명하는 audit가 필요하다.

## persisted raw signal은 왜 partial window인가

이번 audit는 `_share/panel_day_engine_local_precursor_shadow_v1.csv` 에 저장된 값만 본다.

즉 다음은 볼 수 있다.

- `recon_error`
- `dtw_dist`
- `hs_score`
- `mid_ratio`
- `mid_v_ratio`
- `mid_i_ratio`
- `v_drop`
- `group_off_like`
- `shadow_like`

하지만 다음은 여전히 직접 볼 수 없다.

- `pre_ews`
- `site_event_soft`
- `site_event_hard`
- helper 내부의 미저장 run-length / suppression state

따라서 이번 audit의 의미는 “persisted raw window 기준으로 visible precursor-like evidence가 있었는가”이지, 엔진 내부 state를 완전히 재현한다는 뜻은 아니다.

## raw signal day 정의

miss case별로 fault 직전 30일 window를 보고, 하루라도 아래 조건 중 하나를 만족하면 raw-signal day로 센다.

- `recon_error >= site-specific p90` among non-final-fault rows
- `dtw_dist >= site-specific p90`
- `hs_score >= site-specific p90`
- `mid_v_ratio <= 0.85`
- `mid_i_ratio <= 0.85`
- `v_drop >= 0.20`

여기서 p90은 site별 non-final-fault 분포에서 계산한다.

이렇게 해야 절대값이 아니라 site 맥락 안에서 “평소보다 강한 persisted anomaly였는가”를 볼 수 있다.

## miss_reason_class 의미

### `no_obvious_persisted_signal`

30일 bounded window 안에서 persisted raw precursor-like signal이 뚜렷하지 않은 경우다.

이 경우는 detector miss라기보다, 현재 persistence만으로는 precursor-like evidence가 잘 보이지 않는 쪽에 가깝다.

### `raw_signal_present_but_no_alert`

window 안에 raw precursor-like signal은 있었지만 bounded alert는 없었던 경우다.

이 결과가 늘어나면 다음 검토가 정당화된다.

- alert threshold retuning
- gating logic audit
- helper output persistence expansion

### `confounded_signal_window`

raw signal은 있었지만 같은 window에 `group_off_like` 또는 `shadow_like` confound가 함께 있는 경우다.

이 경우는 단순 miss로 보기 어렵고, confound suppression이 합리적으로 작동했는지 따로 봐야 한다.

### `stale_alert_only`

bounded raw signal은 안 보이는데, cohort audit 상 오래된 any-prior alert만 남아 있는 경우다.

이 경우는 “historical alert presence”는 있지만, 현재 fault window의 precursor라고 보기 어렵다.

## 어떤 결과가 어떤 후속 조치를 정당화하는가

### threshold 또는 gating retuning이 정당화되는 경우

- `raw_signal_present_but_no_alert` 가 반복적으로 나온다
- strongest signal이 fault 전 30일 안에 꾸준히 보인다
- confound 없이도 alert head가 안 켜진다

### persistence expansion이 정당화되는 경우

- `no_obvious_persisted_signal` 이 많지만, 엔진 내부에는 suppression/run-length state가 있을 가능성이 크다
- raw persisted fields만으로는 precursor 여부를 해석하기 어렵다

이 경우는 detector를 바로 바꾸기보다, 먼저 더 많은 engine-native state를 shadow 또는 canonical artifact로 남기는 것이 낫다.

### core logic을 그대로 두는 쪽이 정당화되는 경우

- miss 대부분이 `confounded_signal_window` 다
- 또는 `no_obvious_persisted_signal` 이고 raw window에도 실제로 볼 신호가 거의 없다

이 경우는 현재 core detection이 과도하게 miss라고 단정하기 어렵다.

## 이 문서의 결론

이 patch는 official output을 바꾸지 않는다.

하는 일은 하나다.

- bounded miss cohort를 “raw signal 없음 / raw signal 있지만 alert 없음 / confounded / stale-only” 로 분해해서 다음 변경의 우선순위를 더 정확하게 잡게 만드는 것
