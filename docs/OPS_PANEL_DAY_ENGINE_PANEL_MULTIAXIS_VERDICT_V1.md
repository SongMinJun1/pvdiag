# OPS_PANEL_DAY_ENGINE_PANEL_MULTIAXIS_VERDICT_V1

## 목적
- 현재 저장 산출물만으로 panel-level 대표 verdict 표를 만든다.
- 축은 다음 셋이다.
  - 우리 메인 알고리즘 사건 성격 축
  - 커널로그 증상 축
  - GPVS 참고 축
- detector logic 은 바꾸지 않고 packaging/audit 표만 추가한다.

## 입력
- `_share/panel_day_engine_operator_workflow_default_v1.csv`
- `_share/panel_day_engine_abrupt6_symptom_map_v1.csv`
- `_share/panel_day_engine_precursor_onset_truth_v1.csv`
- `_share/panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv`
- `_share/panel_day_engine_kernellog_project_mapping_v1.csv`
- `_share/panel_day_engine_gpv7_perf_summary_v1.csv`
- `_share/panel_day_engine_project_final_decision_pack_v1.csv`
- `data/gpvs/out/*` 등 현재 repo 안 GPVS stored artifact

## Base Universe
- main panel table 은 workflow row 만으로 만들지 않는다.
- unique panel union 은 아래 4개를 dedupe 해서 만든다.
  - workflow panel row
    - `queue_run`, `watch_now_panel`
  - abrupt positive row
    - `_share/panel_day_engine_abrupt6_symptom_map_v1.csv`
  - precursor positive row
    - `preferred_precursor_onset_date` 가 있는 onset truth
  - common-cause positive row
    - `non_panel_or_common_cause` 이고 current/breadth/combined marker evidence 가 있는 descriptive retrofit row
- `secondary_value_cluster` 는 main panel table 에 넣지 않는다.
- cluster 는 별도 보조 파일에만 넣는다.

## Panel-Level 구조
- main table 은 `site + panel_id` 기준으로 정확히 한 줄만 가진다.
- 먼저 panel별 membership flag 를 만든다.
  - `has_급작고장`
  - `has_전조형고장`
  - `has_공통원인이벤트`
  - `has_반복이상`
- 그 다음 대표 verdict 를 우선순위로 고른다.
  1. `급작 고장`
  2. `전조형 고장`
  3. `공통원인 이벤트`
  4. `반복 이상`
  5. `불충분`
- 같은 panel 이 여러 positive universe 에 동시에 속할 수 있으므로, multi-membership 자체는 별도 사건보조표에 남긴다.

## 사건이력 / 대표판정
- `사건이력_ko` 는 아래 고정 순서로 붙인다.
  - `전조형 고장`
  - `급작 고장`
  - `공통원인 이벤트`
  - `반복 이상`
- separator 는 `+` 이다.
- 예:
  - `전조형 고장+급작 고장`
  - `공통원인 이벤트`
  - `반복 이상`

## 패널고장여부 축
- `has_급작고장 == 1` 또는 `has_전조형고장 == 1` 이면 `고장`
- 아니고 `has_공통원인이벤트 == 1` 이면 `비고장`
- 아니면 `미확정`

## 커널로그 축
- abrupt6 direct row 가 있으면 stored symptom map 을 최우선으로 사용한다.
  - `다이오드형` -> `전압 변화형`
  - `개방/장치이상형` -> `전압 변화형`
  - `모듈손상형` -> `출력 저하형`
- 그 외에는 대표판정 기준 nearest symptom axis 만 붙인다.
  - `전조형 고장` -> `출력 저하형`
  - `공통원인 이벤트` -> `패턴 이상형`
  - `반복 이상` -> `불안정형`
  - `불충분` -> `불충분`
- abrupt6 direct row 가 없으면 `커널로그_원인군_ko` 는 `불충분` 으로 남긴다.

## GPVS 축
- panel-level direct GPVS verdict 가 현재 stored artifact 에서 recover 될 때만 붙인다.
- recover 되지 않으면:
  - `GPVS_참고유형_ko = 미부착`
  - `GPVS_근거_ko = 현재 저장 산출물에는 패널별 GPVS 직접 판정이 없음`
- panel-level stored join 이 없는데 GPVS type 을 억지로 발명하면 안 된다.

## 운영 위치
- workflow row 가 `queue_run` 이면 `바로 확인`
- workflow row 가 `watch_now_panel` 이면 `경과 관찰`
- workflow row 가 없는 backfill panel 이면 `현재 workflow 미포함`
- cluster supplement row 는 `추가 발견 후보`

## 출력
- `_share/panel_day_engine_panel_multiaxis_verdict_v1.csv`
  - unique panel 대표 verdict 본표
  - columns:
    - `site`
    - `panel_id`
    - `대표판정_ko`
    - `사건이력_ko`
    - `전조형이력_flag`
    - `급작고장이력_flag`
    - `공통원인이력_flag`
    - `반복이상이력_flag`
    - `패널고장여부_ko`
    - `커널로그_증상명_ko`
    - `커널로그_원인군_ko`
    - `GPVS_참고유형_ko`
    - `GPVS_근거_ko`
    - `운영위치_ko`
    - `판정주의_ko`
- `_share/panel_day_engine_panel_multiaxis_event_supplement_v1.csv`
  - panel x event membership 보조표
  - multi-membership 보존용
- `_share/panel_day_engine_panel_multiaxis_cluster_supplement_v1.csv`
  - cluster 보조표
  - `대표판정_ko = 공통원인 이벤트`
- `_share/panel_day_engine_panel_multiaxis_verdict_summary_v1.csv`
  - membership count / representative count / panel fault status / attach count 요약

## Hard Check
- main panel verdict table 은 `(site, panel_id)` 기준 unique 해야 한다.
- membership guardrail:
  - `급작고장이력_flag == 1` 인 panel 수 = `6`
  - `전조형이력_flag == 1` 인 panel 수 = `2`
  - `공통원인이력_flag == 1` 인 panel 수 = `4`
- main panel verdict table 안에는 cluster row 가 있으면 안 된다.
- workflow 에 discovery cluster 가 있으면 cluster supplement row 가 반드시 있어야 한다.
- `대표판정_ko = 불충분` 인 row 는 네 membership flag 가 모두 `0` 일 때만 허용한다.

## Smoke Test 기준
- builder / smoke script 가 compile 되어야 한다.
- main table 이 unique by panel 이어야 한다.
- event supplement 가 multi-membership 을 보존해야 한다.
- abrupt / precursor / common membership count 가 현재 규칙대로 나와야 한다.
- GPVS panel-level absence path 가 clean 하게 동작해야 한다.
- official outputs 는 smoke 중 바뀌면 안 된다.
