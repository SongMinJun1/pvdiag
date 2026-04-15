# OPS_PANEL_DAY_ENGINE_GPVS_BYTYPE_REBUILD_EXPORT_V1

## 목적
- `gpvs_train_supervised.py`의 현재 재현 가능한 training path에서 GPVS by-type recovered artifact 를 export 한다.
- export 된 artifact 로 real-panel detailed-type audit 를 다시 돌릴 수 있게 만든다.
- detector logic 은 바꾸지 않는다.
- main panel verdict table 에는 아직 attach 하지 않는다.

## 기본 원칙
- 현재 provenance audit 결론은 `provenance_incomplete` 이다.
- 따라서 이번 patch 는 “원본 artifact 발견”이 아니라 “기존 training path에서 재현 가능한 recovered artifact export”를 만든다.
- recovered artifact 가 생겨도 parity 와 real-panel collapse 가 풀리기 전까지는 `do_not_attach` 결론을 유지한다.

## 재구성 우선순위
1. `gpvs_train_supervised.py` 안의 import 가능한 함수/클래스를 직접 재사용한다.
2. selected strict primary path 를 그대로 따른다.
   - model: `LogisticRegression`
   - feature_set: `raw_no_norm_all`
   - split reference: `grouped_source`
3. by-type head 는 raw `fault_type` multiclass 로 export 한다.

## export 산출물
- `data/gpvs/out/gpvs_bytype_recovered_model_v1.joblib`
- `data/gpvs/out/gpvs_bytype_recovered_feature_manifest_v1.json`
- `_share/panel_day_engine_gpvs_bytype_rebuild_parity_v1.csv`
- `_share/panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv`

## parity 의미
- `docs/reports/gpvs_final_summary.md` 와는 selected primary path metadata / grouped primary metric parity 를 본다.
- `data/gpvs/out/EXTERNAL_GPVS_BYTYPE_METRICS.csv` 와는 label-space / by-type metric scope parity 를 본다.
- parity 는 다음 중 하나로 요약한다.
  - `일치`
  - `근사일치`
  - `불일치`
  - `비교불가`

## detailed-type audit 연동
- recovered artifact 가 있으면 `build_panel_day_engine_gpvs_detailed_type_inference_audit_v1.py` 가 그것을 우선 사용한다.
- recovered artifact 가 없거나 load 불가면 `fallback_lr` 로 내려간다.
- row-level `model_source` 는 다음 셋 중 하나만 쓴다.
  - `recovered_artifact`
  - `fallback_lr`
  - `inference_unavailable`

## 해석 주의
- recovered artifact 는 provenance recovery 단계다. production attach 승인 단계가 아니다.
- `current_recovered_attachable_flag = 1` 이 되려면:
  - export 성공
  - parity 가 globally `불일치` 가 아님
  - real-panel detailed-type audit 가 더 이상 6건 단일 top1 collapse 가 아님
- 이 셋 중 하나라도 깨지면 attach 하지 않는다.
