# OPS_PANEL_DAY_ENGINE_RUN_LABEL_PACK_V1

## 목적

`run_ranker_v1` learned scorer는 feature 자체보다 usable label 수가 더 큰 병목이었습니다.  
`run_label_pack_v1` 는 현재 run-level evidence를 한 파일로 묶어, 다음 scorer iteration에서 바로 positive / negative / excluded split을 재사용할 수 있게 만드는 준비 단계입니다.

이 패치는 detector 변경이 아니라 run-level packaging / audit 추가입니다.

## 출력

- `_share/panel_day_engine_run_label_pack_v1.csv`
- `_share/panel_day_engine_run_label_pack_summary_v1.csv`

base universe는 `panel_day_engine_run_feature_table_v1.csv` 의 one-row-per-run 입니다.

## 핵심 라벨 규칙

`label_bucket`
- `positive_like`
- `nuisance_like`
- `monitor_like`
- `unlabeled_other`

우선순위:
1. `eligible_local` 또는 future fault/truth linkage
2. `nuisance_alert` 또는 `isolated_unexplained`
3. `recurring_monitor_like` 또는 `recurring_chronic_monitor_like`
4. 그 외 `unlabeled_other`

`training_label`
- `positive_like -> positive`
- `nuisance_like -> negative`
- `monitor_like -> excluded`
- `unlabeled_other -> excluded`

## 왜 monitor_like를 직접 학습에서 빼는가

`monitor_like` 는 nuisance와도 다르고, true positive와도 다릅니다.  
반복 chronic monitor형은 ranking에서는 참고가 되지만, 바로 positive/negative binary target으로 넣으면 scorer가 operator monitoring pattern과 fault precursor pattern을 섞어 학습할 위험이 있습니다.

그래서 v1 label pack에서는:
- descriptive bucket으로는 유지하고
- direct supervised training에서는 `excluded` 로 둡니다.

## 왜 이것이 v2 전 단계인가

다음 `run_ranker_v2` 에서는 feature 추가보다 먼저 label coverage와 provenance가 안정적이어야 합니다.  
이 label pack이 유용해지려면:

- `positive` / `negative` usable row 수가 의미 있게 늘고
- label source provenance가 일관되고
- holdout에서 v0 reference보다 나은 top-k yield를 재현해야 합니다.

그때 `run_ranker_v2 holdout` 으로 넘어갈 근거가 생깁니다.
