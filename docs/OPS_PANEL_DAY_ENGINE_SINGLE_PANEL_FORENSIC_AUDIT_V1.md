# OPS_PANEL_DAY_ENGINE_SINGLE_PANEL_FORENSIC_AUDIT_V1

## 목적
- 단일 패널 `conalog / c42997a6-5881-47e7-9035-7de8a2673b54.1.1` 에 대해,
  원래 커널로그 wording, 현재 재감사 라벨, 현재 패널표 라벨, 전조 흔적 시간축을 한 번에 맞춰 보는 forensic pack 이다.
- detector logic 을 바꾸지 않고 stored artifact 만으로 지금 가장 안전한 해석을 남긴다.

## 왜 이 pack 이 필요한가
- 이 패널은 현재 표에서는 `급작 고장 / 전압 변화형 / 개방·장치이상형` 으로 읽히기 쉽다.
- 그런데 재감사 파일에는 `first_warning_date`, `retrospective_onset_date`, `vendor_note=현장확인 안됨` 이 함께 남아 있다.
- 그래서 원래 kernel wording, 재감사 라벨, panel-table label, precursor-like timing 을 분리해서 봐야 오해가 줄어든다.

## 입력과 출력
- 입력:
  - `_share/panel_date_reaudit_working.csv`
  - `_share/vendor_reply_adjudication_latest.csv` if present
  - `_share/full_algorithm_case_errors_v2.csv` if present
  - `_share/panel_day_engine_non_precursor_performance_cases_v1.csv`
  - `_share/panel_day_engine_precursor_onset_truth_v1.csv`
  - `_share/panel_day_engine_panel_multiaxis_verdict_v1.csv`
  - `data/conalog/out/panel_day_core.csv`
  - `data/conalog/out/ae_simple_local_precursor_gate_daily.csv`
  - panel id 가 직접 들어 있는 current repo text/csv artifacts
- 출력:
  - `_share/panel_day_engine_c42997_1_1_forensic_summary_v1.csv`
  - `_share/panel_day_engine_c42997_1_1_forensic_timeline_v1.csv`
  - `_share/panel_day_engine_c42997_1_1_forensic_note_v1.md`

## 판단 원칙
- 원래 커널로그 라벨은 exact panel id 가 들어 있는 stored file 에서 직접 회수될 때만 쓴다.
- 직접 회수되지 않으면 `미확인` 으로 남긴다.
- first warning / retrospective onset 이 strong trigger 보다 충분히 앞서 있으면 `전조흔적있음_순수급작보류` 로 읽는다.
- `현장확인 안됨`, `needs_more_info` 같은 문구가 남아 있으면 확정도는 보수적으로 `보류` 로 둔다.

## 해석 포인트
- 이 pack 은 “원래 라벨이 무엇이었는지”, “현재 재감사가 무엇이라고 읽는지”, “현재 패널표가 왜 더 단정적으로 보이는지” 를 분리해 보여 준다.
- 따라서 pure abrupt, precursor-led, holdout/needs-review 중 어디가 안전한지 문장으로 남길 수 있다.
