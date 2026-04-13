# OPS_PANEL_DAY_ENGINE_PROJECT_HANDOFF_PACK_V1

## 목적
- handoff pack 을 최신 benchmark reset 과 onset-semantics split 상태에 맞춰 다시 맞춘다.
- 이 문서는 detector logic 을 바꾸지 않고, 이미 확정된 v6 계열 산출물을 사람이 바로 읽을 수 있는 Korean handoff 로 정리한다.

## 이번 동기화에서 바뀌는 기준
- handoff 는 더 이상 오래된 support wording 을 쓰지 않는다.
- 현재 기준 숫자는 다음처럼 읽는다.
  - 사건 해석상 전조형 고장 패널 수 = 3
  - 전조형 benchmark support = 3
  - 순수 급작 benchmark support = 3
  - 공통원인 이벤트 support = 4
- `c42997a6-5881-47e7-9035-7de8a2673b54.1.1` 은 이제 handoff 에서:
  - 사건 해석상 전조형 고장
  - 최종고장양상 = 급격 종료
  - 운영 최초 전조 발견 = 2025-02-20
  - 사건 해석 onset = 2025-01-20
  - benchmark onset = 2025-03-18
  - precursor eval flag = 1
  - abrupt eval flag = 0
  로 분리해서 적는다.

## 입력
- `panel_day_engine_project_final_decision_pack_v1.csv`
- `panel_day_engine_project_current_data_freeze_pack_v1.csv`
- `panel_day_engine_project_eval_matrix_v1.csv`
- `panel_day_engine_project_eval_reliability_v1.csv`
- `panel_day_engine_precursor_onset_truth_v1.csv`
- `panel_day_engine_panel_multiaxis_verdict_v1.csv`
- `panel_day_engine_project_status_snapshot_v1.csv`
- `panel_day_engine_operator_attention_policy_recommendation_v1.csv`
- `panel_day_engine_operator_release_gate_manifest_v1.csv`
- `panel_day_engine_operator_pipeline_manifest_v1.csv`

## 핵심 해석 원칙
- handoff 는 반드시 네 층을 분리해서 쓴다.
  - 사건 해석
  - 운영 최초 전조 발견일
  - benchmark onset
  - 평가셋 편입
- 이 네 개를 한 문장으로 뭉개면 c429 같은 panel 이 다시 모순적으로 읽히므로, handoff markdown 이 직접 분리해서 적는다.
- benchmark reporting 은 reset 이후 benchmark truth 를 기준으로 읽는다.
- panel row 의 evaluation-set inclusion flag 는 benchmark support 숫자와 자동 동치가 아니다.
- handoff metadata 의 branch / HEAD 는 stale text 를 재사용하지 않고, closeout 단계에서 live git 으로 다시 만든 status snapshot 과 현재 git 상태가 일치할 때만 반영한다.

## 출력
- `_share/panel_day_engine_project_handoff_pack_v1.md`
  - 정확히 다섯 섹션만 둔다.
    - `1. 지금 확정된 기준`
    - `2. 운영 기본값`
    - `3. 전조/급작 읽는 법`
    - `4. 조심해서만 말해야 하는 것`
    - `5. 가장 먼저 볼 파일`
- `_share/panel_day_engine_project_handoff_summary_v1.csv`
  - 세로형 metric row 로 적는다.
  - old wide eval-scope schema 로 되돌리지 않는다.
  - 최소 포함 항목:
    - 사건해석_전조형_패널수
    - precursor_benchmark_support
    - 순수급작_benchmark_support
    - common_cause_support
    - GPVS_적용대상_패널수
    - GPVS_부착수
    - GPVS_비대상_패널수
    - chosen_workflow
    - release_gate
    - pipeline_pass

## handoff markdown 에 반드시 들어가야 하는 내용
- 사건 해석상 전조형 고장 패널 수 = 3
- 순수 급작 benchmark support = 3
- 공통원인 이벤트 support = 4
- step3 precursor 와 step4 pure abrupt 는 둘 다 underpowered / exploratory
- 운영 기본 workflow = `baseline_plus_discovery_cluster`
- release gate 통과
- pipeline 통과
- GPVS 는 고장 패널 6개에만 적용하고 현재 6개 모두 부착
- 비고장/미확정 패널 19개는 GPVS 비대상
- c429 는 사건 해석상 전조형 고장 / 최종고장양상 급격 종료
- c429 panel row flag 는 precursor=`1`, abrupt=`0`
- c429 3-date split:
  - 운영 최초 전조 발견 = 2025-02-20
  - 사건 해석 onset = 2025-01-20
  - benchmark onset = 2025-03-18
- markdown 마지막 git context 문장은 refreshed status snapshot 의 branch / HEAD 를 그대로 반영해야 한다.

## 검증 포인트
- markdown 에 3-way onset split 문구가 직접 들어가야 한다.
- summary CSV 는 3/3/4 와 6/6/19 값을 직접 담아야 한다.
- 오래된 wording:
  - 전조 2
  - 급작 6
  - c429 보류
  는 handoff markdown 에 남아 있으면 안 된다.

## 주의
- 이 문서는 detector/scorer 수정 문서가 아니다.
- benchmark reset 과 onset-semantics split 을 handoff 문구에 반영하는 synchronization 문서다.
