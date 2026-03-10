# Final Validation Summary

> 현재 종합 요약은 `pv_ae/panel_day_engine.py`와 공식 출력 파일 `panel_day_core.csv`, `panel_diagnosis_summary.csv`, `panel_day_risk.csv`, `panel_day_risk_transition.csv`, `panel_day_risk_ensemble.csv` 기준으로 작성했다.

## 1. kernelog1 내부 검증

### 무엇을 검증했는가
- 내부 운영 데이터 기준으로 `2σ weak label` 평가를 수행했다.
- case study는 대표 패널 2건을 기준으로 onset, online diagnosis, rank-based leadtime을 확인했다.
- online diagnosis와 final fault를 분리해서 해석했다.

### 해석 원칙
- `diagnosis_date_online`은 누적 조건이 처음 충족된 온라인 최초 확정일이다.
- `final_fault`는 retrospective segment label로, 온라인 최초 진단 시점과 같은 의미가 아니다.

### 현재 버전에서 확인한 점
- 두 대표 사례에서 onset 이전 Top-K 진입과 진단 지연을 함께 확인할 수 있었다.
- 한 사례는 `ae_rank / transition` 계열이 긴 조기 신호를 보였고, 다른 사례는 `level_drop`가 직접적으로 반응했다.
- 즉 현재 버전은 전조 shortlist와 보수적인 online diagnosis를 분리해서 운영/평가에 쓸 수 있다.

## 2. TECNALIA 외부 sanity

### 데이터 성격
- Zenodo 공개 TECNALIA PV benchmark 데이터를 사용했다.
- 현재 결과는 subset 5모듈 기준 sanity/외부 반응성 점검이다.

### 무엇을 확인했는가
- ingest 자체가 정상적으로 동작하는지 확인했다.
- 모듈 간 정격 차이가 크므로 Pmax 정규화가 필요하다는 점을 확인했다.
- level-drop 축과 mid-ratio 계열이 fault/reference 구분에서 상대적으로 잘 반응하는지 확인했다.

### 무엇은 못 했는가
- onset 기반 전조 검증은 데이터 구조상 제한이 크다.
- 공개 subset 자체가 작고 모듈 타입 차이가 커서, 운영형 leadtime 검증으로 일반화하기 어렵다.
- 따라서 TECNALIA는 외부 sanity와 축 반응성 확인 용도로만 사용한다.

## 3. GPVS 외부 정량 검증

### 데이터 성격
- GPVS-Faults는 Mendeley Data 공개 실험 데이터다.
- fault는 실험 midpoint에 주입되며, `L/M` mode와 `F1~F7` scenario가 존재한다.

### 평가 원칙
- 주지표는 `ROC AUC`, `AP`다.
- `F1`은 보조 지표로만 사용한다.
- by-type에서 `degenerate_score = 1`인 row는 score collapse로 보고 해석에서 제외한다.
- strict result는 `grouped_source`, optimistic result는 `pooled_random`으로 본다.

### 최종 채택 결과

| tier | model | feature_set | split | roc_auc | ap | f1_best | f1_fpr1 |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| strict primary | LogisticRegression | raw_no_norm_all | grouped_source | 0.609412 | 0.382040 | 0.463250 | 0.003544 |
| strict supplementary | LogisticRegression | mixed_no_norm | grouped_source | 0.579122 | 0.424450 | 0.463250 | 0.038018 |
| optimistic upper bound only | HistGradientBoostingClassifier_mode_aware | pooled_random | pooled_random | 0.877929 | 0.851983 | - | - |

### 해석
- supervised 접근은 baseline single보다 개선되지만, `grouped_source` 일반화는 여전히 제한적이다.
- 따라서 GPVS 최종 주장은 `grouped_source` 결과를 중심으로 한다.
- pooled high score는 upper bound 참고치일 뿐 최종 claim에는 사용하지 않는다.

## 4. multisite latest rerun

| site | raw_first | raw_last | out_first | out_last | core_panels | online_diag_count |
| --- | --- | --- | --- | --- | ---: | ---: |
| kernelog1 | 2024-09-06 | 2026-02-18 | 2025-03-01 | 2026-02-18 | 349 | 4 |
| sinhyo | 2024-10-29 | 2026-02-19 | 2025-07-01 | 2026-02-19 | 117 | 0 |
| gangui | 2025-04-08 | 2026-02-19 | 2025-09-01 | 2026-02-19 | 230 | 39 |
| ktc_ess | 2024-08-13 | 2026-02-19 | 2025-07-01 | 2026-02-19 | 187 | 1 |

### 해석
- `kernelog1`은 내부 검증/사례 검증의 중심 사이트다.
- `sinhyo`는 latest rerun 기준 이벤트가 없다.
- `gangui`는 이벤트 수가 가장 많고 phenotype tagging 적용 범위가 가장 넓다.
- `ktc_ess`는 이벤트 수가 적어 보조 sanity 수준으로 본다.

## 5. gangui 현장 수기 근거

### 남겨둔 정성 근거
- 모듈 출력 저하
- 스트링 단선
- GARD
- BSTR
- 250414 특이사항 모듈

### 해석 원칙
- `모듈 출력 저하`는 electrical 기대 사례지만, 현재 확보 시각은 발생시각이 아니라 발견/기록 시각일 가능성이 있고 latest rerun score 시작일보다 이르다.
- 따라서 weak time anchor로만 남기고 direct temporal validation에는 쓰지 않았다.
- `스트링 단선`, `GARD`, `BSTR`, `250414 특이사항`은 정적 상태 태그 또는 설비 속성으로 보고 subgroup annotation에만 사용했다.
- exact field validation은 수행하지 않았고, 정성 보조 근거로만 사용했다.

## 6. 최종 결론

### 현재 버전이 쓸 만한 것
- `kernelog1` 내부 데이터에서 전조 shortlist와 online diagnosis를 분리해 해석하는 용도
- multisite rerun에서 이벤트 분포와 phenotype 분포를 빠르게 요약하는 용도
- GPVS/TECNALIA 같은 외부 공개 데이터에서 축 반응성과 일반화 한계를 점검하는 용도

### 아직 못 하는 것
- exact fault class 수준의 외부 분류
- 정직한 외부 onset 기반 전조 검증의 강한 주장
- 현장 수기 로그와의 exact temporal validation

### 선을 그어 정리하면
- 전조: 내부 데이터에서는 shortlist/leadtime 해석 가능
- 진단: online diagnosis는 보수적으로 사용 가능하나, retrospective final label과 동일시하면 안 됨
- phenotype: axis-based tagging 수준에서는 유용하지만 exact class 분류는 아님
- 외부 일반화: 반응성 근거와 supervised 개선 가능성은 보였지만, strict generalization 성능은 아직 제한적이다
