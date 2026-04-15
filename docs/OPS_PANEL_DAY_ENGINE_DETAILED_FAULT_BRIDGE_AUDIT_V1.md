# OPS_PANEL_DAY_ENGINE_DETAILED_FAULT_BRIDGE_AUDIT_V1

## 목적
- 현재 fault panel 6건에 대해 PVFAULT label 파일의 `fault_type_max` 를 panel-level exact-date rule로 안전하게 붙일 수 있는지 점검한다.
- 이 단계는 detector logic 을 바꾸지 않고, 이미 존재하는 PVFAULT day label 파일만 재사용한다.

## 중요한 구분
- 이 문서는 GPVS family attach 문서가 아니다.
- GPVS family reference 는 기존 `_share/gpvs_fault_family_eval_cases.csv` 계열을 그대로 쓴다.
- 여기서 다루는 `세부 fault type` 은 `PVFAULT_labels_day.csv` 의 `fault_type_max` 이다.
- 즉 family uncertainty 와 detailed fault code attachability 는 서로 다른 축이다.

## 입력
- `_share/panel_day_engine_panel_multiaxis_verdict_v1.csv`
- `_share/panel_day_engine_fault_panel_event_audit_v1.csv`
- `data/pvfault/out/PVFAULT_labels_day.csv`
- `_share/external_pvfault_20260304/PVFAULT_labels_day.csv`
- `_share/external_pvfault_20260304_215400/PVFAULT_labels_day.csv`
- `_share/external_pvfault_fixlabel_20260304_174840/PVFAULT_labels_day.csv`
- `_share/final_validation_20260304_172755/pvfault/PVFAULT_labels_day.csv`

## 기준 universe
- base universe 는 `panel_multiaxis_verdict_v1.csv` 에서 `패널고장여부_ko == 고장` 인 panel 만 쓴다.
- current stored data 기준 기대 count 는 6 이다.

## 기준일 규칙
- panel별 reference date 는 다음 우선순위를 쓴다.
  1. `strict_trigger_date`
  2. `first_final_fault_date`
  3. 둘 다 없으면 unresolved

## 부착 규칙
- exact-date rule 만 허용한다.
- `(panel_id, date == reference_date)` exact match 만 본다.
- nearest-date heuristic 은 쓰지 않는다.
- exact match 가 있고 non-null `fault_type_max` 값이 파일들 사이에서 모두 같으면 attach 가능이다.
- exact match 가 있지만 파일 간 값이 다르면 `conflict` 로 보류한다.
- 어느 파일에도 exact-date match 가 없으면 `no_exact_date_match` 로 보류한다.

## 출력
- `_share/panel_day_engine_detailed_fault_bridge_audit_v1.csv`
  - fault panel 1행당 다음을 남긴다.
    - `site`
    - `panel_id`
    - `reference_date`
    - `exact_match_file_count`
    - `matched_files_csv`
    - `matched_fault_type_values_csv`
    - `consensus_fault_type_code`
    - `attachable_flag`
    - `attach_reason_ko`
- `_share/panel_day_engine_detailed_fault_bridge_summary_v1.csv`
  - 정확히 1행
  - 다음을 포함한다.
    - `고장패널수`
    - `세부fault_부착수`
    - `세부fault_보류수`
    - `exact_date_match_패널수`
    - `exact_date_conflict_패널수`
    - `exact_date_miss_패널수`
    - `note_ko`

## panel multiaxis 연동
- panel multiaxis 는 이 audit 결과를 읽어 다음 컬럼만 추가한다.
  - `세부fault_type_code`
  - `세부fault_type_label_ko`
  - `세부fault_부착상태_ko`
  - `세부fault_근거파일_ko`
  - `세부fault_기준일`
  - `세부fault_보류사유_ko`
- 고장 panel 에서만 `부착` 또는 `보류` 를 쓴다.
- 비고장/미확정 panel 은 `비대상` 이다.

## label 읽는 법
- raw code 는 `세부fault_type_code` 에 그대로 둔다.
- readable label 은 prefix 기반으로만 만든다.
  - `F1* -> GPVS Fault1`
  - `F2* -> GPVS Fault2`
  - ...
  - `F7* -> GPVS Fault7`
- 그 외 코드는 물리 의미를 새로 만들지 않고 raw code 를 label 로 둔다.

## 해석 주의
- 어떤 panel 이 GPVS family 는 불확실해도, PVFAULT exact-date detailed code 는 attach 될 수 있다.
- 반대로 GPVS family 가 붙어 있어도 PVFAULT exact-date consensus 가 없으면 detailed fault type 은 보류될 수 있다.
- 두 축을 한 라벨로 합쳐 읽으면 안 된다.
