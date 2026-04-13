# OPS_PANEL_DAY_ENGINE_RUN_RANKER_V0_AUDIT

## 목적
- day-level gate tweaking이 거의 소진된 뒤에도 run-level score로 useful run과 nuisance-like run을 더 잘 가를 수 있는지 빠르게 본다.
- detector logic은 바꾸지 않고, 이미 만들어진 `run_feature_table_v1.csv` 위에서 online-safe feature만 써서 v0 prototype을 만든다.

## 왜 run-level score인가
- 같은 패널의 연속 alert는 day 수만 보면 과하게 불리해 보일 수 있다.
- 실제 운영에서는 하루 단위보다 run 단위 prioritization이 더 자연스럽다.
- 그래서 다음 방법 탐색은 "게이트를 더 깎을지"보다 "run을 더 잘 정렬할 수 있는지"가 맞다.
- 하지만 separability만으로는 부족하다. median gap이 커도 실제 상위 몇 개를 뽑았을 때 nuisance가 먼저 쏟아지면 운영 가치는 낮다.
- 그래서 다음 검사는 top-k yield다. 상위 10/20/50/100 run 안에 우리가 원하는 run이 실제로 얼마나 농축되는지 봐야 한다.

## 입력
- `_share/panel_day_engine_run_feature_table_v1.csv`
- `_share/panel_day_engine_run_feature_method_hints_v1.csv`

## 평가 그룹
- `positive_like`: `eligible_local`, `future_fault_linked`
- `nuisance_like`: `nuisance_alert`, `isolated_unexplained`
- `monitor_like`: `recurring_monitor_like`
- `unlabeled_other`: `unmatched_other`

이 그룹은 점수 학습용이 아니라 retrospective evaluation용이다.

## online-safe 원칙
점수 입력에서는 미래 정보와 outcome 라벨을 제외한다.

제외:
- `future_fault_linked_flag`
- `future_truth_linked_flag`
- `recurring_run_within_60d`
- `fate_class`
- `cohort_hint`

## prototype score
모든 component는 전체 run table 기준 median/IQR robust scaling 후 단순 합으로 만든다.

### electrical_core_score
- `+ max_v_drop`
- `+ (1 - min_mid_v_ratio)`
- `+ (1 - min_mid_ratio)`

전기적 비정상 깊이만 보려는 가장 기본형이다.
현재 v0 결과에서는 이 축이 가장 해석 가능했고, evt를 강하게 밀지 않아도 baseline separation이 어느 정도 나온다.

### electrical_evt_score
- `electrical_core_score`
- `+ cond_evt_only_day_ratio`

전기적 이상 + evt-driven persistence가 같이 있는 run이 앞쪽으로 오르는지 본다.
다만 현재 결과에서는 evt가 main axis로 보이기보다 보조 축에 가까워 보인다. evt bonus를 크게 주면 top ranks가 다시 broad nuisance 쪽으로 퍼질 위험이 있다.

### electrical_evt_minus_broadshape_score
- `electrical_core_score`
- `+ cond_evt_only_day_ratio`
- `- ae_mid_or_hi_early_day_ratio`
- `- mean_signal_count`
- `- max_signal_count`
- `- p95_recon_error`

너무 broad한 shape/high-signal/high-AE 성격을 감점해서 nuisance-like chronic run을 아래로 누를 수 있는지 본다.

### weak broadshape penalty family
- `electrical_core_minus_broadshape_025`
- `electrical_core_minus_broadshape_050`
- `electrical_core_minus_broadshape_075`

`electrical_core` 가 가장 promising했기 때문에, 먼저 core를 유지한 채 broadshape penalty를 약하게만 섞어본다. penalty를 너무 세게 주면 hidden positive나 chronic abnormal까지 같이 깎을 수 있어서 0.25 / 0.50 / 0.75 세 단계만 시험한다.

### small evt bonus + weak broadshape penalty family
- `electrical_core_plus_evtonly_minus_broadshape_025`
- `electrical_core_plus_evtonly_minus_broadshape_050`

evt는 main axis로 보기보다 약한 보너스만 주는 쪽이 더 현실적일 수 있어서, `0.25 * evt_only_bonus` 를 고정하고 broadshape penalty만 달리 본다.

### two-stage rerank family
- `two_stage_core50_penalty050`
- `two_stage_core100_penalty050`

여기서는 `electrical_core_score` 를 retrieval axis로 쓴다. 이유는 현재까지 가장 해석 가능하고 positive_like를 완전히 놓치지 않는 축이 core였기 때문이다.

반면 broadshape penalty는 retrieval 축이 아니라 reranking 축으로만 쓴다. single-score에서 penalty를 너무 강하게 넣으면 positive_like까지 같이 깎이는 일이 있었기 때문에, 먼저 core로 후보를 가져오고 shortlist 내부에서만 `electrical_core_minus_broadshape_050` 로 순서를 다듬는다.

shortlist `50` 과 `100` 을 같이 보는 이유는:
- `50`: 더 공격적으로 nuisance를 누를 수 있는지 보기 위함
- `100`: positive 회수는 유지하면서 reordering만으로 상단 yield를 개선할 수 있는지 보기 위함

## 출력
- `_share/panel_day_engine_run_ranker_v0_scores.csv`
- `_share/panel_day_engine_run_ranker_v0_summary.csv`
- `_share/panel_day_engine_run_ranker_v0_topruns.csv`
- `_share/panel_day_engine_run_ranker_v0_topk_yield_summary.csv`
- `_share/panel_day_engine_run_ranker_v0_topk_yield_rows.csv`

## top-k yield 해석
- `positive_like_lift`: top-k 안의 positive_like 비율이 전체 labeled base rate보다 몇 배 높은지 본다.
- `nuisance_like_lift`: top-k 안의 nuisance_like 비율이 base rate보다 몇 배 높은지 본다.
- `precision_minus_nuisance`: 상위 run 안에서 positive_like 비율이 nuisance_like 비율보다 얼마나 더 큰지 본다.

좋은 신호:
- `positive_like_lift > 1`
- `nuisance_like_lift < 1`
- `precision_minus_nuisance > 0`

나쁜 신호:
- 상위 k가 커질수록 nuisance_like가 빠르게 늘어난다.
- `positive_like_lift` 가 1 근처이거나 그보다 낮다.
- `nuisance_like_lift` 가 1 이상으로 유지된다.

## 해석 기준
### A) run_ranker_v1 / learned scorer로 진행
- `positive_like_median` 이 `nuisance_like_median` 보다 안정적으로 높다.
- top 10 / top 20 에서 positive-like 비중이 nuisance-like 보다 유리하다.
- 같은 방향성이 여러 prototype score에서 반복된다.
- top-k yield에서도 `positive_like_lift` 가 의미 있게 높고 `nuisance_like_lift` 가 낮다.
- 특히 `electrical_core` 대비 hybrid variant가 같은 수준의 positive_like 확보를 유지하면서 nuisance_like를 더 낮추면 `run_ranker_v1` 후보로 볼 만하다.
- 또는 two-stage rerank가 `electrical_core` 대비 top-20 / top-50 에서 nuisance를 줄이면서 positive_like retrieval을 유지하면, 다음 단계는 learned scorer보다도 shortlist+rereank 구조를 가진 `run_ranker_v1` prototype이 된다.

### B) detector-side method search 중단 후 operator-facing handling으로 이동
- 세 score 모두 positive vs nuisance separation이 약하다.
- top ranks가 nuisance/monitor run으로 계속 채워진다.
- top-k yield 기준으로도 positive_like 농축이 거의 없고 nuisance가 계속 같이 따라온다.
- feature engineering을 더 해도 online-safe한 정보만으로는 분리가 잘 안 보인다.
