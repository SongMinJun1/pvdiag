# OPS_PANEL_DAY_ENGINE_SINGLE_PANEL_FORENSIC_AUDIT_V1

## 목적
- 단일 패널 `conalog / c42997a6-5881-47e7-9035-7de8a2673b54.1.1` 에 대해,
  원래 커널로그 wording, 현재 재감사 라벨, 현재 패널표 라벨, 전조 흔적 시간축을 한 번에 맞춰 보는 forensic pack 이다.
- detector logic 을 바꾸지 않고 stored artifact 만으로 지금 가장 안전한 해석을 남긴다.
- 이번 버전은 continuity 지표를 보조 근거로 남기되, 최종 사건유형은 heuristic 문장이 아니라 explicit stored-field rule 로 결정한다.
- fault-panel event audit downstream row가 이미 맞춰진 뒤에는, 이 pack은 pending-fix detector가 아니라 explanatory/forensic note 로 남는다.

## 왜 이 pack 이 필요한가
- 이 패널은 현재 표에서는 `급작 고장 / 전압 변화형 / 개방·장치이상형` 으로 읽히기 쉽다.
- 그런데 재감사 파일에는 `first_warning_date`, `retrospective_onset_date`, `vendor_note=현장확인 안됨` 이 함께 남아 있다.
- 그래서 원래 kernel wording, 재감사 라벨, panel-table label, precursor-like timing 을 분리해서 봐야 오해가 줄어든다.
- downstream verdict/eval/freeze 를 건드리기 전에, 이 패널 하나에서 continuity 판단이 실제로 어느 정도 강한지 먼저 고립해서 보는 용도다.

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
- 사건유형 결정은 아래 explicit rule 을 그대로 쓴다.
  - `전조형 고장`
    - `retrospective_onset_date` 비공란
    - `strict_trigger_date` 비공란
    - `retrospective_onset_date < strict_trigger_date`
    - `onset_confidence == high`
    - `onset_method == persistent_5of7`
  - `급작 고장`
    - `retrospective_onset_date` 공란
    - `anchor/final/critical hit` 기반 abrupt positive evidence 존재
  - 위 둘이 아니면 positive fault panel 이어도 `고장유형 보류`
- 최종고장양상 결정은 아래 explicit rule 을 쓴다.
  - `급격 종료`
    - `first_final_fault_date == strict_trigger_date`
    - `dead_diag_date <= strict_trigger_date + 1 day`
- `사건시간양상_판정_ko` 는 coarse timing 해석이다.
  - `전조형고장의심`
  - `전조흔적있음_순수급작보류`
  - `순수급작의심`
  - `불충분`
- 이번 버전에서 continuity 는 별도 축으로 다시 본다.
  - `동일사건_연속가능성_높음`
  - `전조흔적은있지만_연속성불충분`
  - `초기경고와_후기트리거_별개가능성`
  - `불충분`
- continuity 에 따라 event recommendation 을 별도로 낸다.
  - `전조형고장으로상향`
  - `고장유형보류유지`
  - `순수급작으로복귀`
  - `추가수동검토필요`
- `현장확인 안됨`, `needs_more_info` 같은 문구가 남아 있으면 확정도는 보수적으로 `보류` 로 둔다.

## 해석 포인트
- summary 는 continuity 지표와 별도로 deterministic decision field 를 함께 낸다.
  - `사건유형_결정규칙_ko`
  - `최종고장양상_결정규칙_ko`
  - `사건유형_결정_ko`
  - `최종고장양상_결정_ko`
- summary 는 다음 continuity 지표를 함께 낸다.
  - `earliest_warning_date`
  - `earliest_onset_date`
  - `strong_trigger_date`
  - `days_between_onset_and_trigger`
  - `pretrigger_window_day_count`
  - `ae_active_days_pretrigger`
  - `dtw_active_days_pretrigger`
  - `hs_active_days_pretrigger`
  - `cond_evt_days_pretrigger`
  - `pre_alarm_days_pretrigger`
  - `final_fault_days_pretrigger`
  - `longest_consecutive_active_run_days`
  - `longest_consecutive_cond_evt_run_days`
  - `last_gap_before_trigger_days`
  - `continuity_judgment_ko`
  - `event_recommendation_ko`
- timeline 은 earliest warning/onset, pretrigger key markers, longest run, 마지막 gap, trigger date 를 compact 하게 남긴다.
- note 는 아래 네 질문에 직접 답한다.
  - 전조흔적이 실제로 있었는가
  - 그 흔적이 2025-03-21과 같은 사건으로 이어졌다고 볼 수 있는가
  - 그래서 현재 이 패널은 전조형/급작/보류 중 무엇으로 두는 게 맞는가
  - 왜 그렇게 판단하는가
- note 에서는 continuity 해석을 보조 설명으로만 쓰고, 최종 사건유형 결정은 explicit stored-field rule 기준이라고 분명히 적는다.
- 이 pack 은 downstream 공식 표를 바로 바꾸지 않는다. 먼저 single-panel evidence 를 정리해, 이후 reconciliation 이 필요한지 판단하는 근거로 쓴다.
- 현재 panel_multiaxis row가 fault-panel event audit 와 이미 일치하면 `현재표_보정필요여부_flag = 0` 이 될 수 있다.
- 이 경우에도 이 pack은 불필요해지는 것이 아니라, 왜 `전조형 고장 / 급격 종료` 로 읽는지가 stored field 기준으로 어떻게 성립하는지 설명하는 forensic 근거 문서로 남는다.
