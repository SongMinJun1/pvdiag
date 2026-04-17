# OPS_PANEL_DAY_ENGINE_GPVS_EVIDENCE_PACK_V1

## 목적
- current real fault panel 6건에 대해 GPVS 내부판정, 외부참조, 호환성, matching 정책, 최종 사용권고를 한 표로 묶는다.
- detector logic, main verdict, 기존 audit 결과는 바꾸지 않는다.
- 이번 산출물은 GPVS를 direct root-cause classifier로 승격하는 문서가 아니라, reference layer evidence를 한곳에 모으는 evidence pack이다.

## 입력
- `_share/panel_day_engine_panel_multiaxis_verdict_v1.csv`
- `_share/gpvs_fault_family_eval_cases.csv` if present
- `_share/panel_day_engine_gpvs_panel_attach_candidates_v1.csv` if present
- `_share/panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv`
- `_share/panel_day_engine_gpvs_detailed_type_realpanel_sanity_v1.csv` if present
- `_share/panel_day_engine_gpvs_bytype_provenance_summary_v1.csv`
- `_share/panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv`
- `_share/panel_day_engine_gpvs_mlpe_panel_agreement_v1.csv`
- `_share/panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv`
- `_share/panel_day_engine_gpvs_mlpe_fault_matching_table_v1.csv`
- `_share/panel_day_engine_gpvs_mlpe_fault_matching_summary_v1.csv`
- `_share/panel_day_engine_gpvs_canonical_dictionary_v1.csv` if present

## 출력
- `_share/panel_day_engine_gpvs_evidence_pack_v1.csv`
  - current fault panel 1행당 GPVS evidence를 압축해 적는다.
- `_share/panel_day_engine_gpvs_evidence_summary_v1.csv`
  - one-row 운영 요약.
- `_share/panel_day_engine_gpvs_evidence_note_v1.md`
  - 레이어별 운영 메모.

## 구성 원칙
- `GPVS_내부판정_ko`
  - current verdict의 내부 GPVS 해석값을 우선 사용한다.
- `GPVS_내부판정근거_ko`
  - family evaluator row가 있으면 그것을 우선 요약하고, 없으면 attach candidate trace를 보조 근거로 사용한다.
- `GPVS_외부참조패턴_ko`
  - current verdict의 front-facing pattern명을 우선 사용하고, 없으면 detailed-type top1 canonical code로 fallback resolve 한다.
- `GPVS_외부참조근거_ko`
  - by-type inference의 model source, top1/top2 score, margin을 읽기 쉬운 한 문장으로 압축한다.
- `GPVS_호환성판정_ko`
  - panel-level agreement가 있으면 usefulness를 우선 반영하되, compatibility summary의 최종 결론을 함께 기록한다.
- `GPVS_매칭정책_ko`
  - canonical GPVS↔MLPE matching policy를 그대로 사용한다.
- `GPVS_최종사용권고_ko`
  - compatibility와 matching tier를 보수적으로 합친다.
  - 단, reference-only는 unusable을 뜻하지 않는다.
  - 그래서 `보조참조` row는 direct root-cause 사용을 금지한 채 최종 권고도 `보조참조`로 유지한다.
  - `비권장`은 matching policy 자체가 비권장이거나 required evidence가 비어 있을 때만 사용한다.

## 해석 원칙
- GPVS 내부판정과 외부참조는 서로 다른 레이어다.
- 외부참조는 근거 사례이지 direct root-cause 판정값이 아니다.
- 호환성 audit 결과에 따라 GPVS는 reference layer로만 사용한다.
- auxiliary-reference row도 direct root-cause 판정에는 쓰지 말고 보조참조로만 사용한다.
- matching 정책에 따라 `F0/F4/F5/F2/F3/F1/F6/F7`의 사용 등급이 갈린다.
