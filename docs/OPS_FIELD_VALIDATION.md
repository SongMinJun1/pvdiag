# OPS Field Validation

## 목적

현장 회신이 들어오면 운영 latest review universe 기준으로 전조 리드타임과 phenotype 수준 일치도를 바로 계산할 수 있게 준비한다.

이 단계는 exact fault class 검증이 아니다. 비교 단위는 아래 canonical primary view다.

- `electrical_like`
- `pattern_change_like`
- `unstable_like`
- `mixed_like`
- `unknown`

## 생성 절차

1. 최신 운영 출력이 생성된 뒤 template를 만든다.

```bash
python research/prognostics/build_field_truth_template.py
```

생성 파일:

- `_share/field_truth_template.csv`
- `_share/field_truth_template.xlsx`
- `_share/site_event_groups_latest.csv`

2. 현장 회신을 `field_truth_template.csv` 또는 xlsx 첫 시트에 입력한다.

3. 회신이 들어오면 비교 스크립트를 실행한다.

```bash
python research/prognostics/evaluate_field_truth.py
```

생성 파일:

- `_share/field_validation_summary.csv`
- `_share/field_validation_leadtime.csv`
- `_share/field_validation_phenotype_match.csv`

회신이 아직 없으면:

- `field_validation_summary.csv`는 `reviewed_row_count=0`
- `field_validation_leadtime.csv`는 header-only
- `field_validation_phenotype_match.csv`는 header-only

## field_truth_template.csv canonical columns

- `site`
- `panel_id`
- `review_group`
- `representative_date`
- `candidate_bucket`
- `our_first_anomaly_date`
- `our_latest_status`
- `our_primary_view`
- `our_interpretation`
- `issue_detected_date`
- `issue_started_estimated_date`
- `actual_issue_type`
- `actual_primary_view`
- `action_taken`
- `field_match_manual`
- `field_match_auto`
- `note`

## site_event_groups_latest.csv canonical columns

- `site`
- `review_group`
- `representative_date`
- `event_start_date`
- `event_end_date`
- `panel_count`
- `panel_ids`
- `summary`
- `likely_common_issue`

## Candidate Universe

candidate universe는 각 사이트의 전체 `latest_alerts_enriched.csv`다.

- `conalog`
- `sinhyo`
- `gangui`
- `ktc_ess`

이 단계에서 추가 top-N 필터는 다시 적용하지 않는다.

## review_group 규칙

형식은 고정이다.

- `site:YYYY-MM-DD`

`representative_date`가 비어 있지 않은 경우 그 날짜를 그대로 사용한다.

## our_latest_status 규칙

우선순위:

- `final_fault`
- `dead`
- `critical`
- `online_diag`
- `alert`

## our_primary_view 규칙

- `phenotype == compound` -> `mixed_like`
- `dominant_family == electrical` -> `electrical_like`
- `dominant_family == shape` -> `pattern_change_like`
- `dominant_family == instability` -> `unstable_like`
- missing -> `unknown`

## our_first_anomaly_date 규칙

`our_first_anomaly_date`는 first alert-worthy date다. 다만 v1에서는 historical evidence와 current review snapshot을 명확히 구분한다.

우선순위:

1. truly temporal한 `alert_history.csv`
2. 현재 validation-prep 경로에 historical reconstruction이 따로 있으면 그것
3. row-level evidence fallback
4. current review snapshot fallback
5. chronology guard

### 1. alert_history.csv 사용 조건

`alert_history.csv`는 아래 조건을 모두 만족할 때만 temporal history로 사용한다.

- `panel_id` 컬럼 존재
- `snapshot_date` 컬럼 존재
- 파싱 가능한 `snapshot_date` 값 존재
- `snapshot_date` 고유값이 2개 이상

즉 latest-snapshot-only `alert_history.csv`는 temporal first-anomaly history로 취급하지 않는다.

### 2. row-level evidence fallback

temporal history를 쓸 수 없으면 아래 row-level evidence date만 사용한다.

- `diagnosis_date_online`
- `critical_diag_date`
- `dead_diag_date`
- `phenotype_event_date`

이 중 가장 이른 날짜를 `our_first_anomaly_date`로 사용한다.

### 3. current review snapshot fallback

row-level evidence도 없으면 current review snapshot date를 마지막 보수적 fallback으로만 사용한다.

- 예: `latest_site_summary.csv`의 `latest_date`

이 날짜는 historical anomaly evidence가 아니다. review 시점 기준으로 candidate row를 비워두지 않기 위한 conservative fallback이다.

### 4. chronology guard

`representative_date`가 있고 `our_first_anomaly_date`가 비어 있거나 더 늦으면 마지막 안전장치로:

- `our_first_anomaly_date = representative_date`

따라서 v1 lead time은 current review fallback만 있었던 row에서는 보수적으로 계산될 수 있다.

### 5. sequencing 메모

v1 sequencing은 아래 순서다.

1. `our_first_anomaly_date` 후보를 temporal / reconstruction / row evidence / current review fallback 순서로 만든다
2. `representative_date`는 dead / critical / online / phenotype event evidence를 먼저 보고, 없을 때만 위 anomaly candidate를 fallback으로 쓴다
3. 마지막에 chronology guard로 `our_first_anomaly_date <= representative_date`를 강제한다

즉 `representative_date`와 chronology guard는 같은 단계가 아니며, guard는 후처리 safety step이다.

## representative_date 규칙

아래 우선순위로 선택한다.

- `dead_diag_date`
- `critical_diag_date`
- `diagnosis_date_online`
- `phenotype_event_date`
- `our_first_anomaly_date`

`final_fault` 자체의 날짜는 만들지 않는다.

## candidate_bucket 규칙

- `event_candidate`
  - `online_diag / critical / dead / final_fault`
- `prealert_candidate`
  - 그 외 `alert`

## likely_common_issue 규칙

`our_primary_view` 기준 canonical enum만 사용한다.

- top view share가 `>= 0.6`이면 그 view 사용
- 모두 `unknown`이면 `unknown`
- 그 외는 `mixed_like`

현재 v1은 same-date only grouping이다.

- group key = `review_group`
- `event_start_date = min(our_first_anomaly_date)` within group, fallback to `representative_date`
- `event_end_date = representative_date`
- `event_start_date`는 `event_end_date`를 넘지 않도록 monotonicity guard를 한 번 더 적용한다

## evaluate_field_truth.py 규칙

### truth_date_used

- `issue_started_estimated_date`가 있으면 우선 사용
- 없으면 `issue_detected_date` 사용

### lead_days

- `lead_days = truth_date_used - our_first_anomaly_date`
- 음수도 그대로 유지한다

### validation_status

- `pending_truth`
- `ok`
- `truth_before_score_window`
- `truth_after_latest_raw`
- `missing_our_first_anomaly`

leadtime 계산 eligibility는 아래 조건을 모두 만족할 때만 `ok`다.

- `truth_date_used` 존재
- `our_first_anomaly_date` 존재
- truth date가 site score window 안에 있음

### had_prealert

- truth date 이전에 alert-level signal이 한 번이라도 있었으면 `True`
- 구현상 `our_first_anomaly_date < truth_date_used`

### had_strong_event

- truth date 이전에 아래 strong signal이 있었으면 `True`
  - `online_diag`
  - `critical`
  - `dead`
  - `final_fault`

### event_before_issue

- `lead_days > 0`

### phenotype comparison

- `actual_issue_type` 자유 텍스트는 phenotype 비교에 사용하지 않는다
- 비교는 `actual_primary_view`만 사용한다

### field_match_auto

- either side blank/unknown -> `unknown`
- equal -> `match`
- one side `mixed_like`, the other concrete -> `partial`
- otherwise -> `mismatch`

### field_match_final

- `field_match_manual`이 비어 있지 않으면 manual 사용
- 아니면 `field_match_auto` 사용

## no-truth 동작

- `field_validation_summary.csv`는 항상 생성된다
- truth가 비어 있으면 site별 `reviewed_row_count=0`
- 이 경우 summary의 status count는 `pending_truth` 위주로 채워진다
- `field_validation_leadtime.csv`는 header-only
- `field_validation_phenotype_match.csv`는 header-only

## Caveats

- v1은 latest review universe만 본다
- resolved-only historical full backfill은 의도적으로 제외한다
- multi-episode panel에서는 first anomaly 또는 group start가 현재 representative date보다 더 이르게 보일 수 있다
- grouping은 same-date only이며 topology-aware가 아니다
