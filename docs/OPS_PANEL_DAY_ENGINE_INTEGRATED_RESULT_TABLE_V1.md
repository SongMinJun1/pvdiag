# OPS_PANEL_DAY_ENGINE_INTEGRATED_RESULT_TABLE_V1

## 목적
- 이 표는 current panel result를 한 줄씩 빠르게 읽기 위한 front-facing unified reading table이다.
- panel multiaxis verdict를 primary source로 두고, kernel-log 직접 해석 층과 GPVS reference 층을 같은 row에서 함께 읽게 한다.
- raw GPVS code/score/rank/margin 증거는 evidence pack에 남기고, 이 표에서는 다시 노출하지 않는다.

## 입력
- `_share/panel_day_engine_panel_multiaxis_verdict_v1.csv`
- `_share/panel_day_engine_gpvs_evidence_pack_v1.csv`

## 출력
- `_share/panel_day_engine_integrated_result_table_v1.csv`
- `_share/panel_day_engine_integrated_result_summary_v1.csv`

## 컬럼 원칙
- `패널고장여부_ko`, `사건유형_ko`, `최종고장양상_ko`:
  current panel multiaxis verdict를 그대로 따른다.
- `커널로그_원인군_ko`:
  direct operational interpretation layer로 읽는다.
- `GPVS_내부참고유형_ko`:
  current front-facing verdict의 internal GPVS interpretation을 재사용한다.
- `GPVS_외부참조패턴_ko`:
  current front-facing verdict의 external GPVS reference pattern을 재사용한다.
- `GPVS_최종사용권고_ko`:
  evidence pack에서 이미 정리된 최종 reference usage tier를 그대로 읽는다.

## 문장형 요약 규칙
- `대표판정요약_ko`:
  fault panel은 사건유형, 최종고장양상, kernel-log 원인군을 한 문장으로 합친다.
- `판정근거요약_ko`:
  fault panel은 kernel-log interpretation과 GPVS usage level을 한 문장으로 합친다.
- non-fault/unresolved panel:
  GPVS wording 없이 현재 상태만 요약하고, GPVS columns는 blank로 둔다.

## 해석 원칙
- panel verdict는 primary다.
- kernel-log는 direct operational interpretation layer다.
- GPVS는 reference layer only다.
- integrated front-facing table은 GPVS raw evidence를 다시 보여주는 표가 아니다.
- raw GPVS evidence가 필요하면 `_share/panel_day_engine_gpvs_evidence_pack_v1.csv` 를 본다.

## 현재 기대값
- total panel count: 25
- fault panel count: 6
- non-fault or unresolved count: 19
- GPVS core reference count: 2
- GPVS auxiliary reference count: 4
- GPVS not-used count: 19

## 검증
- `python -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_integrated_result_table_v1.py research/prognostics/smoke_test_panel_day_engine_integrated_result_table_v1.py`
- `python research/prognostics/build_panel_day_engine_integrated_result_table_v1.py`
- `python research/prognostics/smoke_test_panel_day_engine_integrated_result_table_v1.py`
