# OPS_PANEL_DAY_ENGINE_GPVS_DETAILED_TYPE_INFERENCE_V1

## 목적
- real fault panel 6건에 대해 GPVS family 축과 별도로 GPVS detailed fault type(F1~F7)를 붙인다.
- synthetic `PVFAULT_labels_day.csv` panel id bridge가 아니라, repo 안에 남아 있는 GPVS by-type 학습/평가 산출물을 그대로 읽어 real panel event date에 재적용한다.
- detector logic 은 바꾸지 않고 inference/audit packaging 만 추가한다.

## 입력
- `_share/panel_day_engine_fault_panel_event_audit_v1.csv`
- `_share/panel_day_engine_panel_multiaxis_verdict_v1.csv`
- `data/gpvs/out/EXTERNAL_GPVS_ENSEMBLE2_BYTYPE_METRICS.csv`
- `data/gpvs/out/EXTERNAL_GPVS_BYTYPE_METRICS.csv`
- `data/gpvs/out/EXTERNAL_GPVS_METRICS.csv`
- `data/<site>/out/panel_day_core.csv`
- optional serialized by-type artifact
  - `data/gpvs/out/*BYTYPE*.joblib`
  - `data/gpvs/out/*BYTYPE*.pkl`
  - `_share/**/*BYTYPE*.joblib`
  - `_share/**/*BYTYPE*.pkl`

## 핵심 규칙
- base universe 는 `_share/panel_day_engine_fault_panel_event_audit_v1.csv` 의 `패널고장여부_ko=고장` 대응 panel 6건이다.
- event reference date priority:
  1. `strict_trigger_date`
  2. `first_final_fault_date`
  3. 둘 다 없으면 `추론불가`
- serialized by-type model artifact 가 있으면 우선 사용한다.
- serialized artifact 가 없으면 stored by-type metrics 에서 frozen head 를 다시 구성한다.
  - 우선순위:
    - `EXTERNAL_GPVS_ENSEMBLE2_BYTYPE_METRICS.csv`
    - `EXTERNAL_GPVS_BYTYPE_METRICS.csv`
- real panel event row 는 `panel_day_core.csv` 에서 같은 `panel_id + event_reference_date` exact row 를 읽는다.
- raw axis 는 real panel day row에서 다시 구성한다.
  - `level_drop_raw = clip(1 - mid_ratio, lower=0)`
  - `v_drop_raw = clip(v_drop, lower=0)`
  - `dtw_raw = dtw_dist`
  - `hs_raw = hs_score`
  - `ae_raw = recon_error`
- baseline 은 같은 panel 의 event date 이전 row 만 쓴다.
- baseline 대비 robust z-score 를 만든 뒤 stored by-type score head 를 그대로 적용한다.
- abstain rule 도 새 threshold 를 만들지 않고 stored `threshold_fpr1` 를 그대로 따른다.

## 상태값
- `부착`
  - top-1 code score 가 stored by-type threshold 를 넘는다.
- `판정유보`
  - top-1 code 는 있으나 stored by-type threshold 를 못 넘는다.
- `추론불가`
  - exact event row 없음 / pre-event baseline 부족 / usable score 없음

## 출력
- `_share/panel_day_engine_gpvs_detailed_type_inference_v1.csv`
  - one row per fault panel
  - columns:
    - `site`
    - `panel_id`
    - `event_reference_date`
    - `gpvs_family_label`
    - `gpvs_detailed_fault_code`
    - `gpvs_detailed_fault_score`
    - `gpvs_detailed_fault_rank2_code`
    - `gpvs_detailed_fault_margin`
    - `gpvs_detailed_fault_status_ko`
    - `gpvs_detailed_fault_reason_ko`
- `_share/panel_day_engine_gpvs_detailed_type_summary_v1.csv`
  - one summary row
  - columns:
    - `고장패널수`
    - `세부fault_부착수`
    - `세부fault_판정유보수`
    - `세부fault_추론불가수`
    - `note_ko`

## panel_multiaxis 연결
- 본 inference 축은 `_share/panel_day_engine_panel_multiaxis_verdict_v1.csv` 에 아래 column 으로 추가된다.
  - `GPVS_세부fault_code`
  - `GPVS_세부fault_score`
  - `GPVS_세부fault_rank2_code`
  - `GPVS_세부fault_margin`
  - `GPVS_세부fault_status_ko`
  - `GPVS_세부fault_근거_ko`
- 이것은 기존 GPVS family 축(`GPVS_참고유형_ko`)을 덮어쓰지 않는다.
- 이것은 기존 PVFAULT exact-date bridge 축(`세부fault_*`)과도 다른 별도 축이다.

## 해석 주의
- GPVS family uncertainty 와 GPVS detailed type uncertainty 는 다른 문제다.
- 따라서 family 가 이미 부착돼 있어도 detailed type 은 `판정유보` 나 `추론불가` 일 수 있다.
- 반대로 family 가 미부착이어도 real event row 기준 by-type inference 가 가능하면 GPVS detailed type 은 부착될 수 있다.
- 중요한 점은 이 축이 synthetic `PVFAULT_labels_day.csv` panel id mismatch 문제를 우회하기 위한 bridge 가 아니라, real panel event 에 대해 learned GPVS by-type path 를 다시 적용한 결과라는 점이다.
