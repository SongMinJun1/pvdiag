# OPS_PANEL_DAY_ENGINE_RUN_RANKER_GAP_AUDIT_V1

## 목적

약한 positive promotion 시나리오를 여러 개 시험한 뒤에는, 다음 질문이 "어떤 시나리오를 더 돌려볼까"가 아니라 "왜 아직 deterministic reference를 못 넘는가"가 된다.  
이번 audit은 그 질문에 답하기 위해 가장 보수적인 실전 후보인 `p1_plus_site_balanced_p2`를 고정하고, learned scorer와 deterministic reference의 top-20 disagreement를 직접 해부한다.

## 왜 parsimonious scenario를 먼저 고정하나

`p1_plus_site_balanced_p2`는 다음 이유로 provisional baseline으로 적절하다.

- `P1`만 쓰는 것보다 label coverage가 조금 넓다
- `watch_now` 전체 확장보다 승격 범위가 더 작고 보수적이다
- site imbalance를 줄이려는 목적이 분명하다

즉, 이 시점의 핵심은 더 많은 promotion scenario를 만드는 것이 아니라, 가장 보수적인 candidate조차 왜 deterministic reference를 못 넘는지를 설명하는 것이다.

## disagreement class 해석

top-20을 기준으로 learned scorer(`logistic_v3_candidate`)와 deterministic reference(`electrical_core_minus_broadshape_050`)를 비교한다.

- `positive_captured_by_reference_not_logistic`
  - reference는 상위권에 올렸지만 learned scorer는 놓친 positive-like run
- `positive_captured_by_logistic_not_reference`
  - learned scorer가 더 먼저 올린 positive-like run
- `negative_promoted_by_logistic_not_reference`
  - learned scorer가 reference보다 더 공격적으로 올린 negative-like run
- `negative_promoted_by_reference_not_logistic`
  - reference가 learned scorer보다 더 공격적으로 올린 negative-like run

이 분해를 통해 "reference가 잡는 고-severity positive를 learned가 억제하는가", 혹은 "learned가 nuisance-like pattern에 과민한가"를 볼 수 있다.

## 왜 추가 promotion보다 gap diagnosis가 먼저인가

weak-label promotion은 이미 아래를 보여 주었다.

- `v2 logistic` 대비 약간의 개선은 가능하다
- 하지만 deterministic reference를 안정적으로 넘지는 못한다

이 상태에서 promotion scenario를 더 늘려도, 문제의 원인이

- site scaling 차이인지
- deterministic severity 신호를 learned model이 죽이는 것인지
- positive label coverage가 아직 부족한 것인지

를 모르면 다음 단계가 계속 흔들린다.

## recommended_next_direction 의미

- `try_site_conditioned_scaling`
  - positive miss가 특정 site에 몰릴 때
  - site별 score scale이나 feature normalization 차이를 먼저 점검
- `try_deterministic_plus_learned_hybrid`
  - reference가 강한 electrical severity positive를 더 잘 잡을 때
  - deterministic severity와 learned rank를 결합한 hybrid가 현실적
- `expand_positive_labels_further`
  - learned scorer가 나쁘다기보다 positive coverage가 아직 너무 얕을 때
  - 다음 단계는 label expansion review/adjudication 확대
- `stop_learned_scorer_for_now`
  - disagreement가 구조적이지 않고 noisy할 때
  - learned scorer 투자를 잠시 멈추고 deterministic/operator layer를 유지

## 산출물

- `panel_day_engine_run_ranker_gap_audit_folds_v1.csv`
  - fold별 method ranking metric
- `panel_day_engine_run_ranker_gap_audit_cases_v1.csv`
  - top-20 disagreement run 개별 사례
- `panel_day_engine_run_ranker_gap_audit_summary_v1.csv`
  - disagreement 요약과 전체 recommended next direction
