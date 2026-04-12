# OPS_PANEL_DAY_ENGINE_PRECURSOR_ABRUPT_CONSISTENCY_AUDIT_V1

## 목적
- precursor-positive panel 2건이 abrupt-positive set에도 들어가 있는 이유를 event level에서 다시 점검한다.
- 질문은 하나다.
  - 같은 fault event를 precursor로 먼저 보고 나중에 abrupt ending까지 본 것인가
  - 아니면 같은 panel에서 서로 다른 시점의 별도 사건을 본 것인가
- detector logic은 바꾸지 않고 audit 결과만 추가한다.

## 왜 필요한가
- event level에서는 "전조가 있으면 급작이 아니다"가 맞다.
- 다만 panel level에서는 한 panel이 시간차를 두고 여러 사건을 가질 수 있다.
- 그래서 overlap panel 2건이 같은 사건인지 별도 사건인지 정리하지 않으면 event-type count를 freeze할 때 해석이 흔들린다.

## 입력
- `_share/panel_day_engine_precursor_onset_truth_v1.csv`
- `_share/panel_day_engine_non_precursor_performance_cases_v1.csv`
- `_share/panel_day_engine_abrupt6_symptom_map_v1.csv`
- `_share/panel_day_engine_panel_multiaxis_verdict_v1.csv`
- `_share/panel_day_engine_panel_multiaxis_event_supplement_v1.csv`
- `_share/panel_date_reaudit_working.csv`
- `data/*/out/panel_day_core.csv`

## overlap 정의
- precursor positive universe:
  - `preferred_precursor_onset_date` 가 있는 row
- abrupt positive universe:
  - `_share/panel_day_engine_abrupt6_symptom_map_v1.csv`
- 둘의 교집합 panel을 overlap panel로 본다.
- current stored data 기준 expected overlap panel count는 `2`다.

## 판정 로직
- case row마다 다음 날짜를 맞춘다.
  - `precursor_onset_date`
  - `precursor_fault_date`
  - `abrupt_anchor_date`
  - `abrupt_fault_date`
- same event로 보는 최소 조건:
  - precursor onset이 abrupt fault보다 먼저 나온다
  - precursor fault date와 abrupt fault date가 매우 가깝다
  - selected precursor episode end가 abrupt fault 바로 앞에 붙어 있다
- distinct event로 보는 최소 조건:
  - precursor와 abrupt fault date가 크게 벌어진다
  - 또는 onset과 abrupt timing이 역전된다
- 애매하면 `불충분`으로 남긴다.

## 출력
- `_share/panel_day_engine_precursor_abrupt_consistency_cases_v1.csv`
  - overlap panel 1건당 1행
  - same / distinct / ambiguous 판단과 reasoning을 남긴다
- `_share/panel_day_engine_precursor_abrupt_consistency_summary_v1.csv`
  - overlap count
  - same/distinct/ambiguous count
  - current fault/event count
  - corrected precursor-led / pure abrupt count
- `_share/panel_day_engine_precursor_abrupt_consistency_recommendation_v1.csv`
  - 최종 handling 제안 1행

## 해석 원칙
- 같은 사건으로 나오면:
  - event level에서는 precursor-led fault with abrupt ending으로 읽는 편이 자연스럽다
  - 이 경우 abrupt count는 pure abrupt count와 분리해서 읽어야 한다
- 별도 사건으로 나오면:
  - 같은 panel 위의 다른 시점 사건이므로 abrupt6를 그대로 둘 수 있다
- 불충분이면:
  - count를 바로 바꾸지 말고 manual review를 한 번 더 거친다

## smoke test 기준
- builder / smoke script가 compile 되어야 한다
- overlap extraction이 동작해야 한다
- synthetic fixture에서 same-event / distinct-event 둘 다 검증되어야 한다
- recommendation row가 반드시 나와야 한다
- official outputs는 smoke 중 바뀌면 안 된다
