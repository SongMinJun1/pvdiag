# OPS_PANEL_DAY_ENGINE_GPVS_DETAILED_TYPE_INFERENCE_AUDIT_V1

## 목적
- 현재 real fault panel 6건에 대해 GPVS detailed fault type top-k 추론 결과를 audit-only 형태로 만든다.
- detector logic 은 바꾸지 않는다.
- main panel verdict table 도 이번 patch 에서는 건드리지 않는다.
- 추가로, 현재 by-type inference 결과가 실제 attach 에 쓸 만큼 믿을 수 있는지 sanity audit 으로 점검한다.

## 왜 별도 audit 인가
- `PVFAULT_labels_day.csv` 는 `pvfault.string1/2` 같은 synthetic-string key 를 쓰므로 real panel UUID 기준 direct bridge source 로 쓰면 안 된다.
- 따라서 real panel detailed-fault 추론은 synthetic id join 이 아니라, repo 안에 있는 GPVS by-type 학습/평가 자산을 다시 써서 만들어야 한다.
- 이 파일은 그 real-panel by-type 추론 path 를 따로 materialize 한 audit pack 이다.
- 특히 현재 실데이터에서는 real fault panel 6건이 모두 `top1 = F4L` 로 collapse 되는 현상이 보여서, attach 전에 sanity check 가 꼭 필요하다.

## 입력
- `_share/panel_day_engine_fault_panel_event_audit_v1.csv`
- `_share/panel_day_engine_panel_multiaxis_verdict_v1.csv`
- `data/gpvs/out/gpvs_window_scores.csv`
- `data/gpvs/out/EXTERNAL_GPVS_BYTYPE_METRICS.csv`
- optional serialized by-type artifact under `data/gpvs` or repo outputs
- `data/<site>/out/panel_day_core.csv`

## 모델 경로
- 먼저 recovered export artifact 를 찾는다.
  - `data/gpvs/out/gpvs_bytype_recovered_model_v1.joblib`
  - `data/gpvs/out/gpvs_bytype_recovered_feature_manifest_v1.json`
- recovered artifact 가 usable 하면 그 estimator 와 feature column 을 그대로 쓴다.
- recovered artifact 가 없거나 load 불가하면 fallback head 를 다시 학습한다.
  - source: `data/gpvs/out/gpvs_window_scores.csv`
  - target: raw `fault_type`
  - class space: training rows 에 실제로 존재하는 raw `fault_type` label 그대로 유지
  - model: deterministic multiclass `LogisticRegression(random_state=42)`
  - feature: `gpvs_window_scores.csv` 안 numeric column 중 real-panel path 에서도 재구성 가능한 raw GPVS axis 만 사용
- row-level `model_source` 는 반드시 다음 셋 중 하나로 남긴다.
  - `recovered_artifact`
  - `fallback_lr`
  - `inference_unavailable`
- 현재 repo 상태에서는 recovered artifact 가 없으면 `fallback_lr` audit 으로 내려간다.

## real-panel feature 재구성
- base universe 는 `_share/panel_day_engine_fault_panel_event_audit_v1.csv` 의 current fault panel 6건이다.
- event reference date priority:
  1. `strict_trigger_date`
  2. `first_final_fault_date`
- real-panel feature vector 는 `panel_day_core.csv` 에서 audited reference date row 를 읽어 만든다.
- 현재 재구성하는 raw axis:
  - `level_drop_raw = max(0, 1 - mid_ratio)`
  - `v_drop_raw = max(0, v_drop)`
  - `hs_raw = hs_score`
  - `dtw_raw = dtw_dist`
  - `ae_raw = recon_error`
- recovered artifact 가 `raw_no_norm_all` 계열을 요구하면, audit path 는 panel-day history에서 가능한 범위의 delta / rolling / degeneracy feature 를 함께 재구성한다.
- real panel 에는 GPVS synthetic `fault_mode` 가 없으므로 `mode_L`, `mode_M` 은 zero-filled audit feature 로 취급한다.
- required feature join path 가 없거나 event-date row 가 없으면 그 panel 은 `추론불가` 로 남긴다.

## 상태값
- `추론성공`
  - top-1 prediction 을 audit-level 로 그대로 제시할 수 있을 때
- `판정유보`
  - repo 안에 explicit production abstain rule 이 없으면, audit 파일 안에서만 투명한 margin rule 로 낮은 확신 케이스를 분리한다
- `추론불가`
  - real-panel feature vector 자체를 만들 수 없을 때

## sanity audit 레이어
- 이 audit 은 "top-k 가 나왔다"에서 멈추지 않고, 그 결과를 attach 해도 되는지 추가로 점검한다.
- 점검 항목은 3개다.
  - label distribution audit: `gpvs_window_scores.csv` 안에서 `fault_type` 학습 분포가 한 라벨로 치우치는지 본다.
  - grouped CV sanity audit: 같은 fallback multiclass LR 를 `source_id` 기준 grouped split 으로 재평가해, macro recall / macro f1 / predicted type 다양성을 본다.
  - real-panel sanity audit: 현재 6개 real fault panel 이 한 detailed type 으로 collapse 하는지, 그리고 그 경우 attach 를 막아야 하는지 본다.
- 현재 실데이터에서는 6개 real fault panel 이 모두 `top1 = F4L` 로 collapse 하므로, 원인이 더 분해되기 전까지는 detailed type 을 audit-only 로 유지해야 한다.

## 출력
- `_share/panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv`
  - one row per fault panel
  - columns:
    - `site`
    - `panel_id`
    - `event_reference_date`
    - `gpvs_detailed_model_source`
    - `gpvs_family_label`
    - `gpvs_detailed_top1_fault_type`
    - `gpvs_detailed_top1_score`
    - `gpvs_detailed_top2_fault_type`
    - `gpvs_detailed_top2_score`
    - `gpvs_detailed_margin`
    - `gpvs_detailed_status_ko`
    - `gpvs_detailed_reason_ko`
- `_share/panel_day_engine_gpvs_detailed_type_inference_summary_v1.csv`
  - columns:
    - `fault_panel_count`
    - `inference_success_count`
    - `abstain_count`
    - `inference_unavailable_count`
    - `note_ko`
- `_share/panel_day_engine_gpvs_detailed_type_label_distribution_v1.csv`
  - columns:
    - `fault_type`
    - `train_window_count`
    - `train_source_count`
- `_share/panel_day_engine_gpvs_detailed_type_cv_summary_v1.csv`
  - per-fold grouped CV row + `summary` row
  - columns:
    - `cv_fold`
    - `macro_recall`
    - `macro_f1`
    - `top1_accuracy`
    - `unique_predicted_fault_type_count`
    - `cv_macro_recall_mean`
    - `cv_macro_f1_mean`
    - `cv_top1_accuracy_mean`
    - `cv_unique_predicted_fault_type_count_mean`
    - `note_ko`
- `_share/panel_day_engine_gpvs_detailed_type_realpanel_sanity_v1.csv`
  - one row per real fault panel
  - columns:
    - `site`
    - `panel_id`
    - `gpvs_family_label`
    - `gpvs_detailed_top1_fault_type`
    - `gpvs_detailed_top1_score`
    - `gpvs_detailed_top2_fault_type`
    - `gpvs_detailed_top2_score`
    - `gpvs_detailed_margin`
    - `family_vs_detail_consistency_ko`
    - `single_type_collapse_flag`
    - `attach_recommendation_ko`

## 해석 주의
- GPVS family result 와 GPVS detailed by-type result 는 다른 layer 다.
- family 가 붙어 있어도 detailed by-type 은 `판정유보` 또는 `추론불가` 일 수 있다.
- 이번 patch 는 audit-only 이므로 production attach rule 을 새로 만들지 않는다.
- recovered artifact 가 생겨도 parity 와 real-panel collapse 가 풀렸는지는 별도로 봐야 한다.
- 현재 실데이터에서는 real-panel top1 이 모두 `F4L` 로 collapse 하므로, collapse 원인이 이해되기 전까지는 detailed type 을 main table 에 attach 하면 안 된다.
- main panel verdict table 변경은 다음 단계에서 별도로 동기화해야 한다.
