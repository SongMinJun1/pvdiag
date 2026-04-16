# OPS_PANEL_DAY_ENGINE_GPVS_MLPE_COMPATIBILITY_AUDIT_V1

## 목적
- current real fault panel 6건에서 GPVS-derived output이 MLPE 문제공간과 얼마나 호환되는지 audit-only로 점검한다.
- recovered GPVS by-type artifact가 존재하더라도, 그것이 곧 MLPE real panel root-cause classifier라는 뜻은 아님을 수치로 분리한다.
- detector logic, main verdict, benchmark/eval/freeze/final/handoff/closeout semantics는 바꾸지 않는다.

## 왜 필요한가
- GPVS original scenario space and MLPE official problem-type space are not identical.
- 따라서 GPVS detailed code를 실제 패널의 물리 root cause로 자동 번역하면 안 된다.
- 이번 audit은 GPVS를 direct decision axis로 써도 되는지를 보는 것이 아니라, reference layer로 어느 정도까지 믿을 수 있는지를 본다.

## 입력
- `_share/panel_day_engine_panel_multiaxis_verdict_v1.csv`
- `_share/panel_day_engine_fault_panel_event_audit_v1.csv`
- `_share/panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv`
- `_share/panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv`
- `data/gpvs/out/gpvs_bytype_recovered_model_v1.joblib`
- `data/gpvs/out/gpvs_bytype_recovered_feature_manifest_v1.json`
- `data/gpvs/out/gpvs_window_scores.csv`
- optional `_share/gpvs_fault_family_eval_cases.csv`

## 출력
- `_share/panel_day_engine_gpvs_mlpe_feature_compatibility_v1.csv`
  - recovered manifest / training feature schema / real-panel inference schema 비교
- `_share/panel_day_engine_gpvs_mlpe_distribution_shift_v1.csv`
  - real fault panel 6건의 feature distribution shift 요약
- `_share/panel_day_engine_gpvs_mlpe_panel_agreement_v1.csv`
  - kernel-log / GPVS family / GPVS external scenario 간 panel-level directional agreement audit
- `_share/panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv`
  - one-row compatibility summary
- `_share/panel_day_engine_gpvs_mlpe_compatibility_note_v1.md`
  - 한국어 해석 노트

## 핵심 점검 축
- feature/schema compatibility:
  - recovered model manifest feature와 real-panel inference feature가 실제로 맞물리는가
- distribution compatibility:
  - real panel event feature가 GPVS training distribution 내부에 남아 있는가, 아니면 크게 벗어나는가
- semantic compatibility:
  - GPVS internal family / external scenario가 MLPE kernel-log 원인군과 directionally compatible한가

## 해석 원칙
- `일치`는 방향성이 명확히 compatible할 때만 쓴다.
- `부분일치`는 broad reference로는 plausible하지만 one-to-one는 아닐 때만 쓴다.
- `불일치`는 현재 관측축끼리 직접 충돌할 때만 쓴다.
- `비교곤란`은 label space가 다르거나 직접 비교할 근거가 약할 때 쓴다.
- 최종 recommendation이 `참고축으로만 사용` 또는 `직접 판정축 사용 비권장`으로 나오면, GPVS는 MLPE 공식 verdict를 대체하는 classifier가 아니라 reference layer로만 읽어야 한다.

## 중요한 제한
- 이번 audit은 main verdict row를 수정하지 않는다.
- GPVS attached value를 다시 붙이거나 바꾸지 않는다.
- recovered by-type artifact가 있어도 strong distribution shift와 semantic mismatch가 크면 trust를 올려주지 않는다.
- therefore GPVS should not automatically be treated as a direct root-cause classifier.
