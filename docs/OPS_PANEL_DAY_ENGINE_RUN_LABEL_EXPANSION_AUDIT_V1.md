# OPS_PANEL_DAY_ENGINE_RUN_LABEL_EXPANSION_AUDIT_V1

## 목적
- `run_label_pack_v2` 와 `run_ranker_v2_holdout` 까지 오면서 scorer는 약간 나아졌지만, 개선 폭은 아직 작다.
- 현재 병목은 model family보다 label scarcity와 site coverage 불균형에 더 가깝다.
- 이번 audit은 `training_label_v2 == exclude` 인 run 중에서 다음 라벨 확장 후보를 우선순위로 정리한다.

## 왜 v2 scorer 개선이 작았는가
- `v2` 는 abrupt timely-hit와 common-cause descriptive 분리로 label quality를 올렸지만, 절대 labeled run 수는 여전히 작다.
- 특히 site별 positive/negative coverage가 균일하지 않다.
- 그래서 scorer가 fold별로 일반화되려면, 다음 단계는 model tweak보다 “어떤 excluded run을 먼저 라벨링할지”를 고르는 일이 된다.

## 입력
- `_share/panel_day_engine_run_feature_table_v1.csv`
- `_share/panel_day_engine_run_label_pack_v2.csv`
- `_share/panel_day_engine_run_ranker_v0_scores.csv`
- `_share/panel_day_engine_run_ranker_v2_holdout_summary.csv`
- `_share/panel_day_engine_operator_run_watchlist_now_panels_v1.csv`
- `_share/panel_day_engine_operator_run_watchlist_review_v1.csv`
- `_share/panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv`

## 출력
- `_share/panel_day_engine_run_label_expansion_candidates_v1.csv`
- `_share/panel_day_engine_run_label_expansion_summary_v1.csv`

## 핵심 원리
- base universe는 `training_label_v2 == exclude` 인 run만 쓴다.
- site별 current coverage를 먼저 본다.
  - `positive_training_count`
  - `negative_training_count`
  - `excluded_training_count`
  - `site_positive_gap_flag`
  - `site_negative_gap_flag`
- 그 위에서 excluded run을 네 클래스로 나눈다.
  - `positive_review_candidate`
  - `monitor_review_candidate`
  - `common_cause_review_candidate`
  - `low_priority_unlabeled`

## candidate_class 의미
### positive_review_candidate
- `label_bucket_v2 == unlabeled_other`
- `run_shape_class` 가 `medium_alert_run` 또는 `chronic_alert_run`
- `electrical_core_minus_broadshape_050` 가 global top 10% 또는 site top 5

즉, 아직 라벨은 없지만 scorer 관점에서 가장 “아깝게 빠져 있는” high-value run이다.

### monitor_review_candidate
- `label_bucket_v2 == monitor_like`
- 반복 chronic / monitor burden은 direct positive/negative로 넣기 전에, monitor truth를 더 분리해서 봐야 한다.

### common_cause_review_candidate
- `label_bucket_v2 == common_cause_like`
- local fault scorer truth가 아니라 routing/descriptive 계열이라 direct positive/negative로 넣지 않고 별도 review한다.

### low_priority_unlabeled
- 나머지 excluded run
- 지금 당장 label expansion을 해도 scorer 개선 기대치가 낮은 집합이다.

## priority band
- `P1`
  - `positive_review_candidate` 이면서 `site_positive_gap_flag == 1`
- `P2`
  - 나머지 `positive_review_candidate`
- `P3`
  - `monitor_review_candidate` 또는 `common_cause_review_candidate`
- `P4`
  - `low_priority_unlabeled`

site gap이 중요한 이유는, 같은 top-score unlabeled run이라도 positive labeled가 비어 있는 site를 먼저 메워야 holdout generalization이 빨리 좋아지기 때문이다.

## 왜 common_cause_like / monitor_like 를 positive_review_candidate 와 분리하는가
- `common_cause_like` 는 routing/descriptive truth에 가깝다.
- `monitor_like` 는 chronic burden/monitor bucket이라 direct positive/negative train label로 바로 승격하면 contamination 위험이 있다.
- 그래서 둘은 가치가 없는 run이 아니라, “다른 종류의 라벨 확장” 후보로 따로 묶는다.

## run_ranker_v3 로 넘어갈 근거
- `P1/P2 positive_review_candidate` 를 추가 라벨링한 뒤
- site positive/negative gap이 줄고
- 그 결과 holdout에서 `logistic_v3` 가 `v2` 대비 top-k positive-minus-negative를 의미 있게 올리면
- 그때 `run_ranker_v3` 를 정식 다음 단계로 볼 수 있다.

반대로:
- P1/P2를 확장해도 holdout이 거의 안 좋아지면
- scorer보다 truth definition이나 label family 재구성이 더 큰 병목일 수 있다.
