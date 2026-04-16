# OPS_PANEL_DAY_ENGINE_GPVS_BYTYPE_PROVENANCE_AUDIT_V1

## 목적
- GPVS by-type detailed fault inference의 원본 provenance를 추적한다.
- repo/local output 자산 안에 실제 trained by-type head 가 남아 있는지, 아니면 지금의 `fallback_lr` audit 이 surrogate 인지만 판정한다.
- detector logic 은 바꾸지 않는다.
- main panel verdict table 에 detailed type 을 attach 하지 않는다.

## 왜 필요한가
- provenance audit 이 보는 질문과 detailed-type attachment 질문은 다르다.
- provenance audit 은 먼저 “recoverable by-type head 가 repo/output 자산 안에 있는가”를 본다.
- 동시에 `fallback_lr:gpvs_window_scores.csv` surrogate 가 독립적으로 attach 가능한지는 별도로 본다.
- `gpvs_window_scores.csv` 기준 `fault_type` 별 `train_source_count == 1` 이면, fallback surrogate 는 여전히 강한 제약을 가진다.
- 따라서 recovered artifact 가 있더라도, fallback surrogate 를 그대로 attach 해도 된다는 뜻은 아니다.

## 입력
- `data/gpvs/out/gpvs_window_scores.csv`
- `data/gpvs/out/EXTERNAL_GPVS_BYTYPE_METRICS.csv`
- `research/prognostics/external_eval_gpvs.py`
- `data/gpvs`, `research/prognostics`, `docs` 아래의 repo-local by-type 관련 자산
- optional current audit context:
  - `_share/panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv`
  - `_share/panel_day_engine_gpvs_detailed_type_inference_summary_v1.csv`
  - `_share/panel_day_engine_gpvs_detailed_type_cv_summary_v1.csv`

## 핵심 점검 항목
- serialized by-type model artifact 가 실제로 있는가
- feature manifest / preprocessing manifest 가 있는가
- `external_eval_gpvs.py` 는 model load/training script 인가, 아니면 precomputed score evaluator 인가
- `gpvs_train_supervised.py` 는 학습 결과를 artifact 로 남기는가, 아니면 metrics/onepage 만 쓰는가
- current fallback audit 가 attach 가능한 상태인가

## provenance 상태 분류
- `original_trained_head_recovered`
  - repo/local output 자산 안에서 serialized by-type head 와 feature manifest 를 함께 확인한 경우
- `only_evaluation_assets_present`
  - 평가 스크립트/metrics 는 있으나 recoverable head 는 없는 경우
- `only_synthetic_score_assets_present`
  - synthetic score frame 만 있고 training/evaluation path 도 빈약한 경우
- `provenance_incomplete`
  - training/evaluation 흔적은 있으나 원본 head 복구에 필요한 artifact/manifest 가 부족한 경우

## 출력
- `_share/panel_day_engine_gpvs_bytype_provenance_inventory_v1.csv`
  - artifact inventory + `gpvs_window_scores.csv` fault_type provenance audit
  - 대표 column:
    - `path`
    - `artifact_kind`
    - `exists_flag`
    - `fault_type`
    - `train_window_count`
    - `unique_source_count`
    - `unique_scenario_count`
    - `notes_ko`
- `_share/panel_day_engine_gpvs_bytype_provenance_summary_v1.csv`
  - one-row summary
  - 대표 column:
    - `provenance_status`
    - `serialized_model_found_flag`
    - `feature_manifest_found_flag`
    - `training_script_found_flag`
    - `evaluation_script_found_flag`
    - `external_eval_loads_serialized_model_flag`
    - `external_eval_trains_model_flag`
    - `external_eval_precomputed_scores_only_flag`
    - `current_fallback_lr_attachable_flag`
    - `note_ko`
- `_share/panel_day_engine_gpvs_bytype_provenance_note_v1.md`
  - 현재 자산, 복구 가능 여부, fallback 비부착 이유, 다음 필요 자산을 한국어로 요약

## 해석 원칙
- `PVFAULT_labels_day.csv` synthetic-string key 문제와는 별개로, 이번 audit 은 “원본 GPVS by-type head 자체가 repo에 남아 있는가”를 본다.
- `external_eval_gpvs.py` 가 by-type metrics 를 만든다고 해서 trained by-type head 가 저장돼 있다는 뜻은 아니다.
- current fallback surrogate 는 provenance 와 generalization 이 둘 다 불충분하면 attach 하면 안 된다.
- recovered export artifact 존재 여부와 `current_fallback_lr_attachable_flag` 는 같은 질문이 아니다.
- 즉, recoverable head 가 확인돼도 fallback surrogate 자체는 계속 `attach 불가`로 남을 수 있다.
