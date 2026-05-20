# OPS Field Validation

## 목적

현장 회신이 들어오면 운영 latest review universe 기준으로 전조 리드타임과 phenotype 수준 일치도를 바로 계산할 수 있게 준비한다.

이 단계는 exact fault class 검증이 아니다. 비교 단위는 아래 canonical primary view다.

- `electrical_like`
- `pattern_change_like`
- `unstable_like`
- `mixed_like`
- `unknown`

## 실증 전 준비 체크리스트

이 섹션은 ktc_ess 실증 CSV와 이벤트 기록이 오기 전에 준비해야 할 항목을 잠근다.
목적은 현장 요청 문구를 복잡하게 만들지 않으면서, 내부 검증축은 빠뜨리지 않는 것이다.

### 범위 잠금

- [ ] 외부 요청서는 이벤트 기록만 요구한다.
  - 최소 필드: `event_id`, `fault_type`, `panel_id`, `start_time`, `end_time`, `severity_or_condition`, `intentional_or_observed`, `operator_note`
- [ ] ktc_ess CSV 형식은 기존과 같다고 보고, `panel_id`와 이벤트 시간 범위로 내부 분석 구간을 추출한다.
- [ ] 외부 요청서에는 내부 분석용 root/group, conalog 상태, MLPE 상태 같은 별도 개념을 요구하지 않는다.
- [ ] field label이 들어오기 전에는 cause candidate를 확정 진단으로 승격하지 않는다.
- [ ] 실증 전 패치는 shadow/evidence/report 레이어까지만 허용하고, production verdict 의미 변경은 보류한다.

### 라벨 레이어 구분

현재 문서에는 두 종류의 라벨 레이어가 함께 존재한다.
둘을 섞으면 실증 데이터가 들어왔을 때 평가 단위가 흔들리므로 아래처럼 분리한다.

| 레이어 | 용도 | 현재 상태 | 핵심 키 |
| --- | --- | --- | --- |
| `field_truth_template` | 운영 후보 패널 단위 리뷰와 leadtime/phenotype 비교 | 구현됨 | `site`, `panel_id`, `review_group`, `representative_date` |
| `field_event_label` | 실증에서 주입/관측한 이벤트 단위 비교 | 준비 필요 | `event_id`, `fault_type`, `panel_id`, `start_time`, `end_time` |

정책:
- `build_field_truth_template.py`와 `evaluate_field_truth.py`는 현재 `field_truth_template` 레이어만 다룬다.
- `field_event_label`은 별도 template/compare artifact로 구현해야 한다.
- `field_event_label`을 추가하더라도 기존 `field_truth_template` 컬럼을 억지로 바꾸지 않는다.
- 최종 비교 리포트에서만 두 레이어를 나란히 읽는다.

### 실증 fault / 이상 / 반례 universe

| 우선순위 | 이벤트 조건 | 알고리즘을 흔드는 지점 | 내부 확인 축 |
| --- | --- | --- | --- |
| P0 | 한 패널 부분 음영 | panel-local 저하와 공통 저하 분리 | localness, V/I/P signature, recovery |
| P0 | 한 패널 균일 커버 또는 오염 | 부분 음영과 균일 저하 분리 | sustained low, P drop shape, peer contrast |
| P0 | 케이블 단선 / 부분개방 / 완전개방 | 급작 고장과 회복 이벤트 확인 | abruptness, open-like V/I pattern, recovery |
| P0 | 커넥터/접속부 이상 유사 이벤트 | 전조형 접촉 불안정과 급작 종료 구분 | recurrence, intermittency, terminal pattern |
| P0 | RSD 이벤트 | 장비 상태 전환을 고장으로 오인하지 않는지 확인 | simultaneous drop, control-event negative case |
| P0 | 통신 끊김 / 값 멈춤 / 값 반복 | 데이터 이상을 물리 고장으로 승격하지 않는지 확인 | stale score, timestamp/data-quality gate |
| P0 | 여러 패널 동시 저하 | 개별 패널 고장과 공통 원인 분리 | common-cause score, site/group simultaneity |
| P1 | 다이오드 / 서브스트링 손실 유사 | 음영/개방과 V/I 형태로 구분 | V/I ratio pattern, substring-like signature |
| P1 | 패널 파손 / 국소 모듈 손상 유사 | 국소 손상 후보를 다이오드/열화와 분리 | persistent local loss, recovery absence |
| P1 | BSTR/MPPT/전력변환부 이상 | 패널 물리 문제와 제어 응답 문제 분리 | plateau/clipping, response instability |
| P2 | 장기 열화 / PID 유사 | 단발 episode와 장기 진행성 분리 | duration, recurrence, trend slope |
| P2 | 복합 상황 | 단일 원인 강제 대신 복합/경합으로 남기는지 확인 | top-k competition, overclaim guard |

### 실증 전 내부 구현 준비

- [ ] fault signature dictionary를 만든다.
  - 각 이벤트 조건별 기대되는 P/V/I, 지속성, 회복성, 동시성, 데이터 품질 패턴을 정의한다.
- [ ] shadow V/I/P signature feature extractor를 만든다.
  - production verdict는 바꾸지 않고, 이벤트 단위 특징만 별도 산출한다.
- [ ] shadow fault candidate scorer를 만든다.
  - top1/top3 후보, 경합 여부, 원인미확정 사유를 별도 산출한다.
- [ ] field event label compare report를 만든다.
  - `event_id`, `fault_type`, `panel_id`, `start_time`, `end_time` 기준으로 알고리즘 산출물과 매칭한다.
- [ ] 평가 지표를 잠근다.
  - `detection_hit`
  - `timing_error`
  - `scope_hit`
  - `top1_hit`
  - `top3_hit`
  - `false_positive_guard`
  - `false_reason`
- [ ] single-file delivery와 release pack에 어떤 검증 산출물을 포함할지 따로 결정한다.

### 실증 전 금지 항목

- [ ] field label 없이 원인 후보를 확정 고장명으로 노출하지 않는다.
- [ ] shadow score만으로 precursor threshold나 hard evidence precedence를 바꾸지 않는다.
- [ ] RSD, 통신 이상, 동시 저하 같은 반례를 확인하기 전에는 급작 고장 rule을 공격적으로 넓히지 않는다.
- [ ] 외부 요청 문서에 내부 분석자의 불확실성이나 포맷 우려를 섞지 않는다.

## 생성 절차

1. 최신 운영 출력이 생성된 뒤 template를 만든다.

```bash
python research/prognostics/build_field_truth_template.py
```

truth가 이미 입력된 기존 template가 있으면 기본적으로 overwrite를 막는다.

의도적으로 덮어써야 할 때만 아래처럼 실행한다.

```bash
python research/prognostics/build_field_truth_template.py --force-overwrite-truth
```

생성 파일:

- `_share/field_truth_template.csv`
- `_share/field_truth_template.xlsx`
- `_share/field_truth_template_meta.csv`
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

`field_truth_template.csv`와 `field_truth_template.xlsx` 첫 시트는 사람이 직접 수정하는 canonical truth template다.

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

## field_truth_template_meta.csv machine metadata columns

`field_truth_template_meta.csv`는 machine-generated sidecar다. 사람이 truth를 입력하는 템플릿이 아니라 provenance / confidence / abstain metadata를 따로 보관하는 용도다.

- `site`
- `panel_id`
- `review_group`
- `our_first_anomaly_source`
- `chronology_guard_applied`
- `confidence_level`
- `abstain_flag`
- `abstain_reason`

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

### 5. provenance / confidence / abstain

`our_first_anomaly_source`는 아래 canonical enum 중 하나다.

- `alert_history_temporal`
- `historical_reconstruction`
- `row_evidence_fallback`
- `current_review_fallback`

`chronology_guard_applied`는 chronology guard가 `our_first_anomaly_date`를 실제로 채우거나 수정했으면 `1`, 아니면 `0`이다.

confidence / abstain 규칙:

- `alert_history_temporal` and no guard -> `confidence_level=high`, `abstain_flag=0`
- `historical_reconstruction` and no guard -> `confidence_level=medium`, `abstain_flag=0`
- `row_evidence_fallback` and no guard -> `confidence_level=medium`, `abstain_flag=0`
- `current_review_fallback` -> `confidence_level=low`, `abstain_flag=1`, `abstain_reason=weak_temporal_evidence`
- guard가 적용되면 confidence를 한 단계 낮춘다
- `current_review_fallback`에 guard가 같이 적용돼도 `low` / abstain 유지
- `abstain_flag=0`이면 `abstain_reason`는 빈 값이다

이 provenance-aware confidence를 두는 이유는, 일부 row가 strong temporal history가 아니라 fallback evidence에 의존하기 때문이다.

### 6. sequencing 메모

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

leadtime / phenotype detail output에는 아래 provenance-aware 컬럼이 sidecar에서 join되어 같이 복사된다.

- `our_first_anomaly_source`
- `chronology_guard_applied`
- `confidence_level`
- `abstain_flag`
- `abstain_reason`

## no-truth 동작

- `field_validation_summary.csv`는 항상 생성된다
- truth가 비어 있으면 site별 `reviewed_row_count=0`
- 이 경우 summary의 status count는 `pending_truth` 위주로 채워진다
- `field_validation_leadtime.csv`는 header-only
- `field_validation_phenotype_match.csv`는 header-only

## overwrite-safe workflow

1. `build_field_truth_template.py`로 template를 만든다
2. 현장에서 truth를 입력한다
3. truth 입력 이후에는 기본적으로 build를 다시 돌리지 않는다
4. 정말로 template를 새로 덮어써야 할 때만 `--force-overwrite-truth`를 명시한다

즉 truth entry 이후의 일반 경로는 `evaluate_field_truth.py` 재실행이지 build 재실행이 아니다. canonical human-edit template는 그대로 두고, machine provenance는 sidecar에서 다시 join된다.

## Caveats

- v1은 latest review universe만 본다
- resolved-only historical full backfill은 의도적으로 제외한다
- multi-episode panel에서는 first anomaly 또는 group start가 현재 representative date보다 더 이르게 보일 수 있다
- grouping은 same-date only이며 topology-aware가 아니다
