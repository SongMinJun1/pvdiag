# OPS_PANEL_DAY_ENGINE_RUN_RANKER_SITE_CONDITIONED_SCALING_AUDIT_V1

## 목적

`run_ranker_gap_audit_v1` 에서 learned scorer miss가 특정 site 쪽으로 몰리는 패턴이 보여, 다음 weak-label 확대 전에 `site-conditioned scaling` 이 실제로 도움이 되는지 점검한다. 이 패치는 detector logic을 바꾸지 않고, 현재 최선의 weak-label promotion 시나리오(`p1_plus_site_balanced_p2`) 위에서 scaling 방식만 비교하는 non-core audit이다.

## 왜 지금 이 실험이 필요한가

- gap audit은 learned scorer가 deterministic reference보다 낮은 이유가 단순 label scarcity만은 아닐 수 있음을 보여줬다.
- 같은 electrical feature라도 site별 baseline 분포가 달라, global robust scaling만으로는 상대 이상도를 충분히 살리지 못할 수 있다.
- 그래서 추가 라벨 확장으로 바로 가기 전에, feature normalization 방식만 바꿔도 positive-like 회수가 좋아지는지 먼저 확인한다.

## 비교 대상

- `logistic_v3_global_scaling`
  - 기존 global robust scaling baseline
  - training labeled rows만으로 median/IQR을 fit한 뒤 logistic regression 학습
- `logistic_v3_site_conditioned_scaling`
  - fold 안에서 site별 observable distribution을 이용한 exploratory scaling
  - 각 site의 median/IQR을 site 단위로 계산해 같은 site의 run들을 정규화
- `electrical_core_minus_broadshape_050`
  - deterministic reference

## 중요한 해석 주의점

`site-conditioned scaling` 은 method search 단계다. 이 audit에서는 fold의 observable universe 안에서 site별 unsupervised distribution 정보를 사용하므로, 최종 unbiased performance claim으로 쓰기보다는 "site normalization이 learned scorer miss를 줄일 가능성이 있는가"를 보는 탐색용 결과로 해석해야 한다.

## 입력

- `_share/panel_day_engine_run_feature_table_v1.csv`
- `_share/panel_day_engine_run_label_pack_v2.csv`
- `_share/panel_day_engine_run_label_promotion_scenarios_v1.csv`
- `_share/panel_day_engine_run_ranker_v0_scores.csv`
- `_share/panel_day_engine_run_ranker_v3_scenario_holdout_summary_v1.csv`

## 출력

- `_share/panel_day_engine_run_ranker_site_conditioned_scaling_fold_scores_v1.csv`
- `_share/panel_day_engine_run_ranker_site_conditioned_scaling_summary_v1.csv`
- `_share/panel_day_engine_run_ranker_site_conditioned_scaling_cases_v1.csv`

## 방법

1. `run_label_pack_v2` 를 base label로 읽는다.
2. `p1_plus_site_balanced_p2` 시나리오만 weak positive promotion으로 재적용한다.
3. leave-one-site-out, time_holdout_70_30 두 holdout family로 평가한다.
4. 같은 online-safe run features를 써서:
   - global scaling logistic
   - site-conditioned scaling logistic
   - deterministic reference
   를 비교한다.
5. case output에서는 특히 다음 disagreement를 본다.
   - `positive_captured_by_site_scaled_not_global`
   - `positive_captured_by_reference_not_site_scaled`
   - `negative_promoted_by_site_scaled_not_global`

## 어떤 결과가 의미 있는가

### A) `run_ranker_v3_site_scaled` 로 진행할 근거

- leave-one-site-out 에서 `site_conditioned_scaling` 의 `top20 positive-minus-negative` 가 global logistic보다 안정적으로 높다.
- 동시에 negative promotion 증가가 제한적이다.
- case output에서 site-scaled 쪽이 실제 positive-like miss를 되찾는 패턴이 반복된다.

### B) learned scorer를 잠시 접을 근거

- site-conditioned scaling도 deterministic reference보다 못하거나 gain이 거의 없다.
- recovered positive보다 새 negative promotion이 더 많다.
- disagreement가 일관된 site effect보다 노이즈성 false lift에 가깝다.

## 재현

```bash
python -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_run_ranker_site_conditioned_scaling_audit_v1.py \
  research/prognostics/smoke_test_panel_day_engine_run_ranker_site_conditioned_scaling_audit_v1.py

python research/prognostics/build_panel_day_engine_run_ranker_site_conditioned_scaling_audit_v1.py
python research/prognostics/smoke_test_panel_day_engine_run_ranker_site_conditioned_scaling_audit_v1.py
```
