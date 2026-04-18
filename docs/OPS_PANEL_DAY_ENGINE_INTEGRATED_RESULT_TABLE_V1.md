# OPS_PANEL_DAY_ENGINE_INTEGRATED_RESULT_TABLE_V1

## 목적
- 이 표는 최종 front-facing table이다.
- panel multiaxis verdict를 primary source로 두고, panel status와 kernel-log family, suspected-cause ranking만 한 줄에서 빠르게 읽게 한다.
- GPVS internal/external/evidence detail은 evidence pack에 남기고, 이 표에서는 다시 노출하지 않는다.

## 입력
- `_share/panel_day_engine_panel_multiaxis_verdict_v1.csv`
- `_share/panel_day_engine_gpvs_evidence_pack_v1.csv`
- `_share/panel_day_engine_cause_candidate_heuristics_v1.csv`

## 출력
- `_share/panel_day_engine_integrated_result_table_v1.csv`
- `_share/panel_day_engine_integrated_result_summary_v1.csv`

## 컬럼 원칙
- `패널고장여부_ko`, `사건유형_ko`, `최종고장양상_ko`:
  current panel multiaxis verdict를 그대로 따른다.
- `커널로그_원인군_ko`:
  direct operational interpretation layer로 읽는다.
- `1순위_의심원인_ko`, `2순위_의심원인_ko`, `3순위_의심원인_ko`:
  heuristic cause-candidate layer의 top1/top2/top3를 front-facing display label로만 옮긴다.
  raw heuristic output 자체는 바꾸지 않는다.

## 표시용 원인명
- 아래 여섯 개 label만 integrated table 안에서 표시 친화적으로 바꿔 적는다.
  - `다이오드·서브스트링형 -> 다이오드·국소 회로 이상형`
  - `접속·부분개방형 -> 접촉 끊김 형`
  - `센서·피드백형 -> 장치 측정 이상형`
  - `제어응답형 -> 장치 응답 이상형`
  - `전력변환부형 -> 전력변환부 이상형`
  - `외부계통교란형 -> 외부 전원 흔들림형`
- `부분음영형`, `오염형`, `열화형`, `원인미확정` 는 그대로 둔다.

## 해석 원칙
- panel verdict는 primary다.
- kernel-log는 direct operational interpretation layer다.
- GPVS는 reference layer only이며 raw detail은 evidence pack에 남긴다.
- integrated front-facing table은 GPVS raw evidence를 다시 보여주는 표가 아니다.
- 이 표는 panel status, kernel-log family, suspected-cause ranking만 보여준다.
- raw GPVS evidence가 필요하면 `_share/panel_day_engine_gpvs_evidence_pack_v1.csv` 를 본다.
- raw heuristic label/score/action note가 필요하면 `_share/panel_day_engine_cause_candidate_heuristics_v1.csv` 를 본다.

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
