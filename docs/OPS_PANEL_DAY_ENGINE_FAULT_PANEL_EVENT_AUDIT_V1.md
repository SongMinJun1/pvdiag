# OPS_PANEL_DAY_ENGINE_FAULT_PANEL_EVENT_AUDIT_V1

## 목적
- 현재 panel multiaxis 본표에서 `패널고장여부_ko = 고장` 인 패널만 다시 모은다.
- single-panel forensic 에서 쓴 explicit stored-field rule 을 전 fault panel 에 똑같이 적용한다.
- 그래서 현재 fault panel 이
  - 진짜 순수 급작인지
  - precursor evidence 가 있는지
  - strict precursor eval set 에 들어간 것인지
  - 해석과 evaluation-set inclusion 이 어긋나는지
  를 한 번에 본다.
- 이 audit 표는 downstream reconciliation 에서 authoritative event-semantics source 로 쓴다.

## 입력
- `_share/panel_day_engine_panel_multiaxis_verdict_v1.csv`
- `_share/panel_day_engine_abrupt6_symptom_map_v1.csv`
- `_share/panel_day_engine_precursor_onset_truth_v1.csv`
- `_share/panel_date_reaudit_working.csv`
- `_share/vendor_reply_adjudication_latest.csv` if exists
- `data/*/out/panel_day_core.csv`
- `data/*/out/ae_simple_local_precursor_gate_daily.csv`

## 출력
- `_share/panel_day_engine_fault_panel_event_audit_v1.csv`
- `_share/panel_day_engine_fault_panel_event_audit_summary_v1.csv`
- `_share/panel_day_engine_fault_panel_event_audit_note_v1.md`

## Base Universe
- base universe 는 현재 panel multiaxis 본표의 `패널고장여부_ko == 고장` row 전부다.
- 현재 stored data 기준 기대 row 수는 `6` 이다.
- 이 audit 은 non-fault panel 을 다시 분류하지 않는다.

## 명시 규칙
### 사건유형_재판정_ko
- `전조형 고장` iff:
  - `retrospective_onset_date` 비공란
  - `strict_trigger_date` 비공란
  - `retrospective_onset_date < strict_trigger_date`
  - `onset_confidence == high`
  - `onset_method == persistent_5of7`
- `급작 고장` iff:
  - abrupt positive evidence 존재
  - 그리고 아래 둘 중 하나
    - `retrospective_onset_date` 공란
    - `retrospective_onset_date == strict_trigger_date`
      - `onset_method == strict_trigger_fallback`
      - `onset_confidence != high`
- 즉 same-day fallback onset 은 pure abrupt 후보에서 자동 탈락시키지 않는다.
- 위 두 규칙을 모두 만족하지 않는 positive fault panel 만 `고장유형 보류` 다.

### 최종고장양상_재판정_ko
- `급격 종료` iff:
  - `first_final_fault_date == strict_trigger_date`
  - `dead_diag_date <= strict_trigger_date + 1 day`
- 그 외:
  - 사건유형 재판정이 `급작 고장` 이면 `급작 발생`
  - 사건유형 재판정이 `전조형 고장` 이면 `진행성 악화`
  - 아니면 `불충분`

## 출력 컬럼 의미
- `현재표_사건유형_ko`, `현재표_최종고장양상_ko`
  - 현재 panel multiaxis 본표가 이미 들고 있는 값이다.
- `전조흔적_flag`, `순수급작_flag`, `전조평가셋편입_flag`, `급작평가셋편입_flag`
  - 현재 stored artifact 가 이미 들고 있는 row-level flag 다.
- `사건유형_재판정_ko`, `최종고장양상_재판정_ko`
  - 이번 audit 이 explicit rule 로 다시 낸 값이다.
- `현재표_보정필요여부_flag`
  - 현재 본표 값과 explicit rule 재판정 값이 다르면 `1` 이다.

## Summary 의미
- `고유_고장패널수`
  - audit 대상 fault panel 수
- `사건유형_재판정_전조형수 / 급작수 / 보류수`
  - explicit rule 기준 재분류 개수
- `최종고장양상_급격종료수`
  - explicit terminal rule 까지 만족한 수
- `해석과평가셋불일치_패널수`
  - explicit rule 해석상 precursor 또는 abrupt 로 읽히지만 현재 strict evaluation-set inclusion flag 와 안 맞는 수
- `현재표_보정필요_패널수`
  - 현재 panel table 값을 바로 고쳐야 할 후보 수
- downstream reconciliation 뒤에는 이 값이 `0` 이 될 수 있다.
  - 그 경우 이 audit 은 pending-fix 탐지기라기보다 authoritative event-semantics source 와 현재 본표가 일치하는지 확인하는 검산표가 된다.
- `사건유형_재판정_전조형수` 와 `전조평가셋편입_패널수` 는 일부러 다를 수 있다.
  - 전자는 사건 해석 count 이고,
  - 후자는 엄격 precursor evaluation-set inclusion count 이다.

## Note 규칙
- note markdown 은 아래 4개 section 을 고정으로 쓴다.
  - `1. 전체 고장 패널 전수 결과`
  - `2. 순수 급작 패널 수`
  - `3. 전조흔적은 있지만 평가셋에 안 들어간 패널`
  - `4. 지금 바로 고쳐야 하는 패널`

## Hard Check
- base fault panel count 는 `6`
- `c42997a6-5881-47e7-9035-7de8a2673b54.1.1` 은 정확히 한 번 나와야 한다.
- 이 panel 은 explicit rule 기준 `전조형 고장` 으로 재판정돼야 한다.
- 다른 fault panel 이라도 precursor explicit rule 을 만족하면 반드시 `전조형 고장` 으로 재판정돼야 한다.
- same-day fallback onset + abrupt positive evidence panel 은 `급작 고장` 으로 재판정돼야 한다.
- non-fault panel 이 audit output 에 들어가면 안 된다.

## 해석 주의
- 이 audit 은 detector 를 바꾸지 않는다.
- 이 audit 은 current fault panel 을 explicit stored-field rule 로 다시 읽는 문서화/감사 단계다.
- 그래서 current visible label 과 strict evaluation-set inclusion 을 같은 뜻으로 읽지 않게 해 준다.
