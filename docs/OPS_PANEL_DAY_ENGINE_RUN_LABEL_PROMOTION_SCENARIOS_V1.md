# OPS_PANEL_DAY_ENGINE_RUN_LABEL_PROMOTION_SCENARIOS_V1

## 목적

`run_label_pack_v2` 이후에도 holdout 개선 폭이 작다면, 다음 병목은 대개 모델 구조보다 라벨 부족이다.  
하지만 실제 adjudication은 느리고 비용이 크기 때문에, 곧바로 대규모 신규 truth를 만들기보다 review batch에서 작은 weak-label promotion 시나리오를 먼저 시험해 보는 것이 현실적인 다음 단계다.

이번 audit은 detector를 바꾸지 않고 다음 질문만 본다.

- P1만 약하게 positive로 승격하면 holdout이 좋아지는가
- `watch_now` reference가 붙은 review run까지 포함하면 더 좋아지는가
- site-balanced P2 보강이 site coverage를 넓히는 데 도움이 되는가

## 왜 이 시나리오들인가

### P1

P1은 `run_label_expansion_review_batch_v1`에서 이미 가장 우선순위가 높은 후보다.  
site positive gap이 있는 곳의 상위 unlabeled run이 포함되어 있어, 가장 보수적인 weak-label promotion 시작점으로 적절하다.

### watch_now linked

`watch_now_panel_ref_flag == 1`인 positive review run은 operator attention과 겹친다.  
즉, scorer 학습 관점뿐 아니라 운영 burden 관점에서도 중요도가 높아, small weak-label promotion 후보로 가치가 있다.

### site-balanced P2

단순 global 상위 score만 따라가면 label coverage가 특정 site에 치우칠 수 있다.  
site-balanced P2는 scorer가 site gap 때문에 불안정해지는지 먼저 보는 작은 보강 실험이다.

## 시나리오 정의

- `p1_only`
  - positive review batch의 `P1` 전부를 weak positive로 승격
- `p1_plus_watchnow_ref`
  - `P1` 전부
  - plus `watch_now_panel_ref_flag == 1`
- `p1_plus_site_balanced_p2`
  - `P1` 전부
  - plus site별 상위 `P2` 2건
- `p1_plus_watchnow_ref_plus_site_balanced`
  - `P1` 전부
  - plus `watch_now` linked positive review run 전부
  - plus 아직 선택되지 않은 남은 `P2` 중 site별 1건

승격된 run은 training에서만 `positive`로 바꾸고, 평가 grouping은 기존 `label_bucket_v2`를 그대로 유지한다.  
즉 이것은 truth rewrite가 아니라 weak-label scenario test다.

## 평가 방법

- online-safe feature set은 `run_ranker_v2_holdout_audit`와 동일
- fold family도 동일
  - leave-one-site-out
  - time_holdout_70_30
- 비교 score
  - scenario logistic
  - `electrical_core_score`
  - `electrical_core_minus_broadshape_050`

핵심 지표는 `top10/20 positive_like - negative_like`이고, summary는 `logistic_v2_holdout` 대비 delta를 기록한다.

## 해석 가이드

### v3로 넘어갈 수 있는 경우

아래가 동시에 보이면 `run_ranker_v3` 후보로 볼 수 있다.

- LOSO `top20_positive_minus_negative`가 `v2 logistic` 대비 일관되게 개선
- time holdout도 악화되지 않음
- best electrical reference와 비교해도 손해가 크지 않음

### 아직 label expansion이 더 필요한 경우

다음이면 weak-label promotion만으로는 부족하다고 해석한다.

- P1만 올려도 개선이 거의 없음
- watch_now/site-balanced 보강을 해도 LOSO 개선이 미미함
- time holdout이 쉽게 흔들림

이 경우 다음 단계는 `run_label_expansion_review_batch_v1` 기반 추가 adjudication이다.
