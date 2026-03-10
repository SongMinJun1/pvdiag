# GPVS Final Summary

## 1. 데이터셋 성격
- GPVS-Faults는 Mendeley Data에 공개된 실험 데이터셋이다.
- 각 fault scenario는 실험 중간 시점(midpoint)에서 fault를 주입하는 구조로 해석한다.
- 각 scenario에는 `L`, `M` 두 mode가 존재한다.
- fault scenario는 `F1`부터 `F7`까지 존재하며, `F0`는 healthy reference로 사용한다.

## 2. 평가 원칙
- strict result는 `grouped_source` split을 사용한다.
- optimistic result는 `pooled_random` split을 사용한다.
- 주지표는 `roc_auc`, `ap`다.
- `f1_best`, `f1_fpr1`는 보조 지표로만 본다.
- by-type 분석에서 `degenerate_score = 1`인 행은 score collapse로 간주하고 해석에서 제외한다.

## 3. 최종 채택 결과

### A. strict primary result
- model: `LogisticRegression`
- feature_set: `raw_no_norm_all`
- split: `grouped_source`
- roc_auc: `0.609412`
- ap: `0.382040`
- f1_best: `0.463250`
- f1_fpr1: `0.003544`

### B. strict AP-focused supplementary result
- model: `LogisticRegression`
- feature_set: `mixed_no_norm`
- split: `grouped_source`
- roc_auc: `0.579122`
- ap: `0.424450`
- f1_best: `0.463250`
- f1_fpr1: `0.038018`

### C. optimistic upper bound only
- model: `HistGradientBoostingClassifier_mode_aware`
- split: `pooled_random`
- roc_auc: `0.877929`
- ap: `0.851983`
- 이 결과는 upper bound 참고치이며 최종 claim에는 사용하지 않는다.

## 4. 해석
- supervised 접근은 baseline best single보다 개선된다.
- 다만 `grouped_source` 기준 일반화 성능은 여전히 제한적이다.
- 병목은 mode-specific collapse와 source shift로 해석한다.
- 따라서 GPVS는 현재 결과에서 마감하고, 추가 개선 실험은 더 진행하지 않는다.

## 5. 최종 문장
- overall pooled 성능만 보면 높은 값도 가능하다.
- 그러나 정직한 일반화 기준에서는 `grouped_source` 결과를 메인 결과로 채택한다.
- GPVS는 다축 설계가 외부 fault 라벨에 반응한다는 근거와, supervised 개선 가능성이 존재한다는 점을 확인하는 용도로 사용한다.
