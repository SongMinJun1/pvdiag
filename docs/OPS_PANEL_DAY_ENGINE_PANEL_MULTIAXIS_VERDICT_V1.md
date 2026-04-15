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
- `_share/panel_day_engine_non_precursor_performance_cases_v1.csv`
- `_share/panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv`
- `_share/panel_day_engine_precursor_abrupt_consistency_cases_v1.csv`
- `_share/panel_day_engine_precursor_abrupt_consistency_summary_v1.csv`
- `_share/panel_day_engine_precursor_abrupt_consistency_recommendation_v1.csv`
- `_share/panel_day_engine_c42997_1_1_forensic_summary_v1.csv`
- `_share/panel_day_engine_fault_panel_event_audit_v1.csv`
- `_share/panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv`
- `_share/panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv`
- `_share/panel_day_engine_gpvs_detailed_type_realpanel_sanity_v1.csv`
- `_share/panel_day_engine_detailed_fault_bridge_audit_v1.csv`
- `_share/panel_day_engine_detailed_fault_bridge_summary_v1.csv`
- `_share/panel_day_engine_kernellog_project_mapping_v1.csv`
- `_share/panel_day_engine_gpv7_perf_summary_v1.csv`
- `_share/panel_day_engine_project_final_decision_pack_v1.csv`
- `_share/panel_day_engine_gpvs_panel_attach_inventory_v1.csv`
- `_share/panel_day_engine_gpvs_panel_attach_feasibility_v1.csv`
- `_share/panel_day_engine_gpvs_panel_attach_candidates_v1.csv`

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
- 그 다음 사건유형과 최종고장양상을 함께 정한다.
  1. fault panel event audit explicit rule
    - `패널고장여부_ko = 고장` row 는 `_share/panel_day_engine_fault_panel_event_audit_v1.csv` 를 최우선으로 쓴다.
    - 즉 fault panel 의 `사건유형_ko`, `사건유형_해석_ko`, `순수급작_flag`, `최종고장양상_ko` 는 이 audit 결과와 동기화한다.
    - same-day fallback onset 도 여기서 다시 판단한다.
      - `retrospective_onset_date == strict_trigger_date`
      - `onset_method == strict_trigger_fallback`
      - `onset_confidence != high`
      - abrupt positive evidence 존재
      - 이면 `급작 고장` 으로 유지한다.
  2. single-panel forensic explicit rule
    - target panel 은 `c42997a6-5881-47e7-9035-7de8a2673b54.1.1`
    - single-panel forensic summary 는 fault panel event audit 이 c429 row 를 읽는 근거 파일이다.
    - 이때 continuity wording 이 아니라 stored field 인 `earliest_onset_date=2025-01-20`, `strong_trigger_date=2025-03-21` 를 기준으로 본다.
    - `사건유형_결정_ko = 전조형 고장`
    - `최종고장양상_결정_ko = 급격 종료`
  3. pure abrupt panel
    - `사건유형_ko = 급작 고장`
    - `최종고장양상_ko = 급작 발생`
  4. pure precursor panel
    - `사건유형_ko = 전조형 고장`
    - `최종고장양상_ko = 진행성 악화`
  5. `공통원인 이벤트`
    - `최종고장양상_ko = 해당없음`
  6. `반복 이상`
    - `최종고장양상_ko = 해당없음`
  7. `불충분`
    - `최종고장양상_ko = 불충분`
- 핵심은 event type 과 terminal failure pattern 을 분리해서 읽는 것이다.
- precursor 가 확인된 사건은 panel 에 abrupt marker 가 있어도 event class 자체를 `급작 고장` 으로 두지 않는다.
- 다만 same-day fallback onset 은 real precursor evidence 로 보지 않으므로 abrupt rule 에서 자동 탈락시키지 않는다.
- `c42997a6-5881-47e7-9035-7de8a2673b54.1.1` 은 single-panel forensic explicit rule 기준으로 `전조형 고장` 이고, benchmark reset 이후 strict precursor eval set 에도 포함된다.
- multi-membership 자체는 별도 사건보조표에 남기되, overlap same-event panel 은 두 개의 독립 fault event 로 세지지 않는다.

## 해석층 vs 평가셋
- `사건유형_ko` 는 downstream output 에 바로 쓰는 현재 주판정 label 이다.
- `사건유형_해석_ko` 는 사람이 읽기 쉽게 붙이는 해석층이다.
- 둘은 같은 뜻일 수도 있지만, 항상 같아야 하는 것은 아니다.
- 특히 `c42997a6-5881-47e7-9035-7de8a2673b54.1.1` 은:
  - `사건유형_ko = 전조형 고장`
  - `사건유형_해석_ko = 전조형 고장`
  - `판정주의_ko` 에도 onset/trigger rule date 를 함께 적어, 왜 이렇게 읽었는지 바로 보이게 한다.
- 평가셋 편입은 별도 benchmark truth 파일에서 다시 계산한다.
  - `전조평가셋편입_flag = 1` iff `_share/panel_day_engine_precursor_onset_truth_v1.csv` 에 panel row 가 존재
  - `급작평가셋편입_flag = 1` iff `_share/panel_day_engine_non_precursor_performance_cases_v1.csv` 에서 `eval_bucket_v2 == abrupt_or_no_precursor_now`
- 즉 사건 해석과 평가셋 편입은 개념상 분리하되, 현재 reset benchmark에서는 c429 도 precursor eval set 에 포함된다.

## onset 날짜 3종
- 본표는 fault panel에 대해 onset 날짜도 세 층으로 나눠 보여 준다.
  - `운영최초전조발견일`
    - 운영상 첫 precursor marker가 잡힌 날짜
  - `운영최초전조마커`
    - 그 날짜를 만든 marker 이름
  - `사건해석상전조시작일`
    - re-audit / forensic에서 사건 해석상 본 onset
  - `benchmark전조시작일`
    - precursor benchmark anchor로 쓰는 onset
- 이 셋은 같은 뜻이 아니다.
- `c42997a6-5881-47e7-9035-7de8a2673b54.1.1` 은:
  - `운영최초전조발견일 = 2025-02-20`
  - `운영최초전조마커 = first_cond_evt`
  - `사건해석상전조시작일 = 2025-01-20`
  - `benchmark전조시작일 = 2025-03-18`
  로 분리해서 읽는다.
- 즉 이 row는 전조형 고장으로 해석되지만, 운영상 최초 detection 과 benchmark onset은 더 늦을 수 있다.

## 추가 flag 의미
- `전조흔적_flag`
  - strong trigger 이전 precursor-like evidence 가 있으면 `1`
- `순수급작_flag`
  - corrected pure abrupt set 에 속할 때만 `1`
- `전조평가셋편입_flag`
  - `_share/panel_day_engine_precursor_onset_truth_v1.csv` 에 panel row 가 있을 때만 `1`
- `급작평가셋편입_flag`
  - `_share/panel_day_engine_non_precursor_performance_cases_v1.csv` 에서 `eval_bucket_v2 == abrupt_or_no_precursor_now` 일 때만 `1`
- `해석대평가차이_ko`
  - 사람이 읽는 해석과 current evaluation-set inclusion 이 어긋나는 경우 그 이유를 짧게 적는다

## 사건이력 / 대표판정
- `사건이력_ko` 는 아래 고정 순서로 붙인다.
  - `전조형 고장`
  - `급작 고장`
  - `공통원인 이벤트`
  - `반복 이상`
- separator 는 `+` 이다.
- 예:
  - `전조형 고장(급격 종료)`
  - `전조형 고장`
  - `전조형 고장`
  - `공통원인 이벤트`
  - `반복 이상`
- overlap same-event panel 은 `전조형 고장+급작 고장` 처럼 두 개의 fault event 로 쓰지 않는다.
- 사건이력은 fault panel event audit 의 최종 사건유형/최종고장양상 조합을 따른다.
  - `전조형 고장`
  - `전조형 고장(급격 종료)`
  - `급작 고장`
- single-panel forensic explicit rule row 는 `전조형 고장(급격 종료)` 로 남고, same-event overlap 2건은 corrected audit 결과에 따라 `전조형 고장` 으로 남을 수 있다.
- `대표판정_ko` 는 reader-facing 대표 label이고, 현재 reconciliation 이후에는 `사건유형_ko` 와 같은 사건 축을 가리킨다.
- `사건유형_ko` 와 `사건유형_해석_ko` 는 필요하면 달라질 수 있지만, `c42997...1.1` 은 이번 explicit rule 반영 이후 둘 다 `전조형 고장` 으로 맞춘다.
- 이 row 는 fault panel 이고 explicit rule 기준으로 `전조형 고장` 이며, 현재 synced benchmark 기준으로 `전조평가셋편입_flag = 1`, `급작평가셋편입_flag = 0` 으로 읽는다.

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
  - `고장유형 보류` -> `전압 변화형`
  - `공통원인 이벤트` -> `패턴 이상형`
  - `반복 이상` -> `불안정형`
  - `불충분` -> `불충분`
- abrupt6 direct row 가 없으면 `커널로그_원인군_ko` 는 `불충분` 으로 남긴다.

## GPVS 축
- GPVS 는 현재 프로젝트에서 모든 visible panel 에 붙는 일반 참고축이 아니다.
- GPVS 는 `fault-family reference axis` 이고, 현재는 `패널고장여부_ko = 고장` 인 panel 에만 적용한다.
- 따라서 비고장 / 공통원인 이벤트 / 반복 이상 / 불충분 panel 은 GPVS target 이 아니다.
- panel-level GPVS direct attach 가능 여부는 별도 attach audit 결과를 그대로 따른다.
- `GPVS_적용대상_ko = 적용대상` 인 row 에만 아래 규칙을 쓴다.
  - feasibility 가 `가능` 이면:
  - `_share/panel_day_engine_gpvs_panel_attach_candidates_v1.csv` 를 `site + panel_id` 로 join 한다.
  - 겹치는 panel 에만 `GPVS_참고유형_ko` 를 붙인다.
  - `GPVS_근거_ko` 는 `source_path | source_key_ko | 비고_ko` 조합으로 짧게 남긴다.
  - `GPVS_부착상태_ko = 부착`
  - `GPVS_후보파일_ko = source_path`
  - feasibility 가 `불가` 이거나 panel 이 unmatched 면:
  - `GPVS_부착상태_ko = 미부착`
  - `GPVS_참고유형_ko = 미부착`
  - `GPVS_근거_ko = 현재 저장 산출물에는 패널별 GPVS 직접 판정이 없음`
  - `GPVS_후보파일_ko` 는 feasibility 의 `최선_후보_파일` 을 유지한다.
  - `GPVS_미부착사유_ko` 는 row-by-row 로 가장 구체적인 이유를 남긴다.
    - `GPVS 패널수준 후보 파일은 있으나 이 패널 key가 없음`
    - `GPVS 결과는 있으나 패널수준 key가 없음`
    - `패널수준 GPVS 산출물 없음`
- GPVS 는 여전히 reference axis 이고, 메인 사건 성격 판정축이 아니다.
- current panel universe 와 겹치지 않는 panel 에까지 GPVS type 을 억지로 붙이면 안 된다.
- 그래서 본표는 GPVS가 붙은 panel 과 안 붙은 panel 을 같이 두되, 안 붙은 경우도 왜 안 붙는지 한 줄씩 투명하게 남긴다.

## GPVS 세부 fault 추론 축
- GPVS family 축과 별도로 recovered GPVS by-type artifact 기반 세부 fault 축을 추가한다.
- authoritative source 는 아래 3개다.
  - `_share/panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv`
  - `_share/panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv`
  - `_share/panel_day_engine_gpvs_detailed_type_realpanel_sanity_v1.csv`
- attach guard 는 다음을 모두 만족할 때만 통과한다.
  - rebuild summary 에서 `current_recovered_attachable_flag = 1`
  - audit row 의 `gpvs_detailed_model_source = recovered_artifact`
  - sanity row 의 `attach_recommendation_ko = attach_ok`
- synthetic `PVFAULT_labels_day.csv` panel id bridge 는 이 축의 direct source 로 쓰지 않는다.
- 따라서 기존 `세부fault_*` exact-date bridge 축과도 다른 별도 축으로 읽어야 한다.
- 본표에는 아래 컬럼을 둔다.
  - `GPVS_세부fault_code`
  - `GPVS_세부fault_score`
  - `GPVS_세부fault_rank2_code`
  - `GPVS_세부fault_rank2_score`
  - `GPVS_세부fault_margin`
  - `GPVS_세부fault_부착상태_ko`
  - `GPVS_세부fault_근거_ko`
  - `GPVS_세부fault_판정주의_ko`
- 고장 panel:
  - guard 통과 시 `부착`
  - guard 미충족 시 `판정유보`
- 비고장/미확정 panel:
  - `비대상`
- `GPVS_참고유형_ko` 와 `GPVS_세부fault_code` 는 같은 뜻이 아니다.
- family uncertainty 가 자동으로 detailed type attachment 를 막지 않는다.
  - 예: `10305...2.12` 는 `GPVS_참고유형_ko = 불확실` 이어도 recovered by-type attach guard 를 통과하면 `GPVS_세부fault_code = F4L` 을 함께 가질 수 있다.
- 이 축이 현재 main verdict 의 공식 detailed-fault attachment source 다.

## 세부 fault code 축
- 세부 fault type exact-date bridge 는 과거 audit-only 시도였고, 현재는 retired path 로 본다.
- source 는 `PVFAULT_labels_day.csv` 의 `fault_type_max` 였지만 synthetic-string keyed 한계 때문에 real panel official attachment source 로 채택하지 않았다.
- 따라서 이 축은 bridge provenance 보존용/보조 audit 용으로만 읽고, main summary 나 공식 detailed-fault claim source 로 쓰지 않는다.
- 본표에는 아래 컬럼을 추가한다.
  - `세부fault_type_code`
  - `세부fault_type_label_ko`
  - `세부fault_부착상태_ko`
  - `세부fault_근거파일_ko`
  - `세부fault_기준일`
  - `세부fault_보류사유_ko`
- `세부fault_부착상태_ko`
  - 고장 panel: `부착` 또는 `보류`
  - 비고장/미확정 panel: `비대상`
- label 은 raw code prefix 로만 읽는다.
  - `F1* -> GPVS Fault1`
  - `F2* -> GPVS Fault2`
  - ...
  - `F7* -> GPVS Fault7`
  - 그 외는 raw code 그대로 둔다.
- 이 label 은 code readability 용일 뿐, 물리 의미를 새로 해석해 붙이지 않는다.
- 정리하면:
  - `GPVS_참고유형_ko` = family axis
  - `GPVS_세부fault_code` = 공식 detailed-fault axis
  - `세부fault_type_code` = retired exact-date bridge audit residue

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
    - `사건유형_ko`
    - `사건유형_해석_ko`
    - `최종고장양상_ko`
    - `대표판정_ko`
    - `사건이력_ko`
    - `전조흔적_flag`
    - `순수급작_flag`
    - `전조평가셋편입_flag`
    - `급작평가셋편입_flag`
    - `해석대평가차이_ko`
    - `운영최초전조발견일`
    - `운영최초전조마커`
    - `사건해석상전조시작일`
    - `benchmark전조시작일`
    - `전조형이력_flag`
    - `급작고장이력_flag`
    - `공통원인이력_flag`
    - `반복이상이력_flag`
    - `패널고장여부_ko`
    - `GPVS_적용대상_ko`
    - `커널로그_증상명_ko`
    - `커널로그_원인군_ko`
    - `GPVS_부착상태_ko`
    - `GPVS_참고유형_ko`
    - `GPVS_근거_ko`
    - `GPVS_미부착사유_ko`
    - `GPVS_후보파일_ko`
    - `GPVS_세부fault_code`
    - `GPVS_세부fault_score`
    - `GPVS_세부fault_rank2_code`
    - `GPVS_세부fault_margin`
    - `GPVS_세부fault_status_ko`
    - `GPVS_세부fault_근거_ko`
    - `세부fault_type_code`
    - `세부fault_type_label_ko`
    - `세부fault_부착상태_ko`
    - `세부fault_근거파일_ko`
    - `세부fault_기준일`
    - `세부fault_보류사유_ko`
    - `운영위치_ko`
    - `판정주의_ko`
- `_share/panel_day_engine_panel_multiaxis_event_supplement_v1.csv`
  - panel x event membership 보조표
  - multi-membership 보존용
- `_share/panel_day_engine_panel_multiaxis_cluster_supplement_v1.csv`
  - cluster 보조표
  - `대표판정_ko = 공통원인 이벤트`
  - GPVS 는 cluster-level artifact 가 아직 없으므로 계속 `미부착`
- `_share/panel_day_engine_panel_multiaxis_verdict_summary_v1.csv`
  - 사건 수 / 고유 고장 패널 수 / 대표판정 수 / GPVS 적용대상/부착 count 요약
  - 핵심 row 예:
    - `고유_고장패널수`
    - `사건해석_전조형_패널수`
    - `사건해석_급작_패널수`
    - `사건해석_전조형_급격종료_패널수`
    - `사건해석_전조형_진행성악화_패널수`
    - `전조흔적_패널수`
    - `순수급작_패널수`
    - `엄격전조평가셋_패널수`
    - `순수급작평가셋_패널수`
    - `해석과평가셋불일치_패널수`
    - `GPVS_세부fault_부착수`
    - `GPVS_세부fault_판정유보수`
    - `GPVS_세부fault_추론불가수`
    - `대표판정_전조형수`
    - `대표판정_급작수`
    - `대표판정_고장유형보류수`
- GPVS 관련해서도 세 축을 섞지 않는다.
  - `GPVS_참고유형_ko`
    - family reference
  - `GPVS_세부fault_*`
    - learned GPVS by-type inference result
  - `세부fault_*`
    - PVFAULT exact-date bridge result

## Hard Check
- main panel verdict table 은 `(site, panel_id)` 기준 unique 해야 한다.
- panel count 와 evaluation-set count 는 분리해서 본다.
  - `고유_고장패널수 = 패널고장여부_ko == 고장`
  - `사건해석_전조형_패널수 = 사건유형_ko == 전조형 고장`
  - `사건해석_급작_패널수 = 사건유형_ko == 급작 고장`
  - `사건해석_전조형_급격종료_패널수 = 사건유형_ko == 전조형 고장` 이고 `최종고장양상_ko == 급격 종료`
  - `사건해석_전조형_진행성악화_패널수 = 사건유형_ko == 전조형 고장` 이고 `최종고장양상_ko == 진행성 악화`
  - `전조흔적_패널수 = 전조흔적_flag == 1`
  - `순수급작_패널수 = 순수급작_flag == 1`
  - `엄격전조평가셋_패널수 = 전조평가셋편입_flag == 1`
  - `순수급작평가셋_패널수 = 급작평가셋편입_flag == 1`
  - `해석과평가셋불일치_패널수 = 해석대평가차이_ko 비공란`
- current real-data guardrail:
  - `고유_고장패널수 = 6`
  - `사건해석_전조형_패널수 = 3`
  - `사건해석_급작_패널수 = 3`
  - `사건해석_전조형_급격종료_패널수 = 1`
  - `사건해석_전조형_진행성악화_패널수 = 2`
  - `전조흔적_패널수 = 3`
  - `엄격전조평가셋_패널수 = 3`
  - `순수급작평가셋_패널수 = 3`
  - `해석과평가셋불일치_패널수 = 0`
  - `공통원인이력_flag == 1` 인 panel 수 = `4`
- `c42997...1.1` 은 정확히 1행이어야 하고:
  - `사건유형_ko = 전조형 고장`
  - `사건유형_해석_ko = 전조형 고장`
  - `전조흔적_flag = 1`
  - `순수급작_flag = 0`
  - `전조평가셋편입_flag = 1`
  - `급작평가셋편입_flag = 0`
- overlap same-event panel 은 계속:
  - `사건유형_해석_ko = 전조형 고장`
  - `최종고장양상_ko = 진행성 악화`
  - `전조평가셋편입_flag = 1`
  - `급작평가셋편입_flag = 0`
- main panel verdict table 안에는 cluster row 가 있으면 안 된다.
- workflow 에 discovery cluster 가 있으면 cluster supplement row 가 반드시 있어야 한다.
- `GPVS_적용대상_ko = 적용대상` row 는 모두 `패널고장여부_ko = 고장` 이어야 한다.
- `GPVS_부착상태_ko = 부착/미부착` row 는 모두 `GPVS_적용대상_ko = 적용대상` 이어야 한다.
- `GPVS_부착상태_ko = 비대상` row 는 `GPVS_참고유형_ko = 비대상`, `GPVS_미부착사유_ko = 고장 패널이 아니어서 GPVS 적용 대상 아님`, `GPVS_후보파일_ko blank` 이어야 한다.
- GPVS attach feasibility 가 `가능` 이더라도 main panel table 의 `GPVS_부착수` 는 `고장 panel` 에 대한 direct-match 수로만 계산한다.
- cluster supplement 는 계속 `GPVS_참고유형_ko = 미부착`, `GPVS_근거_ko = 현재 저장 산출물에는 패널별 GPVS 직접 판정이 없음` 이어야 한다.
- `대표판정_ko = 불충분` 인 row 는 네 membership flag 가 모두 `0` 일 때만 허용한다.

## Smoke Test 기준
- builder / smoke script 가 compile 되어야 한다.
- main table 이 unique by panel 이어야 한다.
- event supplement 가 multi-membership 을 보존해야 한다.
- overlap same-event panel 은 `사건유형_ko = 전조형 고장`, `최종고장양상_ko = 진행성 악화`, `사건이력_ko = 전조형 고장` 으로 읽혀야 한다.
- `c42997a6-5881-47e7-9035-7de8a2673b54.1.1` 은 `사건유형_ko = 전조형 고장`, `사건유형_해석_ko = 전조형 고장`, `패널고장여부_ko = 고장`, `최종고장양상_ko = 급격 종료` 로 읽혀야 한다.
- c429 row 는 `전조흔적_flag = 1`, `순수급작_flag = 0`, `전조평가셋편입_flag = 1`, `급작평가셋편입_flag = 0` 이어야 한다.
- 사건 수와 패널 수 summary 가 final row 기준으로 분리 계산되어야 한다.
- 해석층과 evaluation-set inclusion summary 도 final row 기준으로 계산되어야 한다.
- abrupt / precursor / common membership count 가 현재 규칙대로 나와야 한다.
- fault panel 에 대해서만 GPVS attachable panel 은 candidates file 기준으로 실제 부착돼야 한다.
- non-fault/common-cause/repeating/unresolved row 는 `GPVS_부착상태_ko = 비대상` 이어야 한다.
- fault row 는 `GPVS_세부fault_status_ko ∈ {부착, 판정유보, 추론불가}` 여야 한다.
- non-fault row 는 `GPVS_세부fault_*` column 을 blank 로 둬야 한다.
- unmatched panel 은 허용된 미부착 사유 셋 중 하나를 가져야 한다.
- cluster row 는 계속 미부착이어야 한다.
- official outputs 는 smoke 중 바뀌면 안 된다.
