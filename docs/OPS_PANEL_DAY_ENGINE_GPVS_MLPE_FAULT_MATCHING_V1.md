# OPS_PANEL_DAY_ENGINE_GPVS_MLPE_FAULT_MATCHING_V1

## 목적
- GPVS scenario output을 MLPE 공식 problem-type 집합과 어떻게 연결해 읽을지 front-facing matching table로 고정한다.
- detector logic과 main verdict는 바꾸지 않는다.
- 이번 산출물은 GPVS를 direct root-cause classifier로 승격하는 문서가 아니라, reference layer 운영 규칙을 명시하는 문서다.

## 입력
- `_share/panel_day_engine_panel_multiaxis_verdict_v1.csv`
- `_share/panel_day_engine_gpvs_mlpe_panel_agreement_v1.csv`
- `_share/panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv`
- `_share/panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv`

## front-facing schema 단순화 대응
- current front-facing verdict table 은 low-level GPVS code/scenario 를 직접 노출하지 않는 simplified schema 를 쓸 수 있다.
- 그래서 fault matching 은 `GPVS_세부fault_code`, `GPVS_시나리오명_ko` 같은 옛 field 를 main verdict table 에서 필수로 요구하지 않는다.
- canonical GPVS code 가 front-facing verdict 에 없으면 `_share/panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv` 같은 audit/provenance artifact 에서 resolve 한다.
- 즉, low-level GPVS field 는 audit/provenance artifact 에만 남아 있어도 matching conclusion 과 support count 를 유지할 수 있어야 한다.

## canonical code 정규화
- front-facing matching에서는 `F2M`, `F4L` 같은 mode suffix를 제거한다.
- 즉:
  - `F0L/F0M -> F0`
  - `F1L/F1M -> F1`
  - ...
  - `F7L/F7M -> F7`
- L/M은 내부 scenario provenance로는 남지만, matching 표의 외부 설명에서는 제거한다.

## 출력
- `_share/panel_day_engine_gpvs_canonical_dictionary_v1.csv`
  - F0~F7 canonical dictionary
- `_share/panel_day_engine_gpvs_mlpe_fault_matching_table_v1.csv`
  - MLPE official fault ↔ GPVS canonical code matching table
- `_share/panel_day_engine_gpvs_mlpe_fault_matching_summary_v1.csv`
  - one-row policy summary
- `_share/panel_day_engine_gpvs_mlpe_fault_matching_note_v1.md`
  - 운영 원칙 설명

## 현재 운영 정책
- `F0`: baseline
- `F4`: core_reference
- `F5`: core_reference_candidate
- `F2`: auxiliary_reference
- `F3`: confounder_only
- `F1/F6/F7`: reserved_system_level

## 해석 원칙
- GPVS는 현재 direct root-cause classifier가 아니라 reference layer다.
- `F4/F5`는 MLPE 패널·어레이 불균형 해석에 가장 유용한 code로 살린다.
- `F2`는 direct root-cause가 아니라 제어·계측 이상 힌트로만 남긴다.
- `F3`는 교란 플래그로만 유지한다.
- `F1/F6/F7`은 시스템/통합 결과표 후보축으로만 보류한다.
- 따라서 front-facing matching 표에서도 human-readable physical root-cause naming을 과도하게 붙이지 않는다.
