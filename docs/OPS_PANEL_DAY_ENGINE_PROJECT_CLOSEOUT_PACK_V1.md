# OPS_PANEL_DAY_ENGINE_PROJECT_CLOSEOUT_PACK_V1

## 목적
- 이미 완료된 final decision / handoff / internal-share summary를 사람이 바로 넘겨볼 수 있는 closeout index로 묶는다.
- 이 단계는 새 알고리즘이나 새 평가지표를 만드는 일이 아니라, 프로젝트 종료 시점의 읽는 순서와 사용 범위를 고정하는 packaging/documentation 단계다.

## 왜 지금 closeout pack 이 필요한가
- final decision pack 까지 오면 scope별 사용 범위와 overclaim 금지선은 이미 정리돼 있다.
- handoff pack 과 clean internal-share pack 까지 만들어지면, 다음 필요는 "이제 무엇을 먼저 읽고 어디를 기준 문서로 삼을지"를 한 번 더 정리하는 closeout index다.
- 그래서 closeout pack 은 metric table 추가가 아니라, 사람이 프로젝트를 다시 열 때 바로 들어갈 entrance 문서와 artifact index를 제공한다.

## 입력과 원칙
- 다음 승인 산출물만 재사용한다.
  - `panel_day_engine_project_final_decision_pack_v1.csv`
  - `panel_day_engine_project_final_decision_summary_v1.csv`
  - `panel_day_engine_project_final_do_and_dont_v1.csv`
  - `panel_day_engine_project_handoff_summary_v1.csv`
  - `panel_day_engine_project_current_data_freeze_pack_v1.csv`
  - `panel_day_engine_internal_share_clean_summary_v1.csv`
  - `panel_day_engine_abrupt6_symptom_map_v1.csv`
  - `panel_day_engine_kernellog_project_mapping_v1.csv`
  - `panel_day_engine_gpv7_perf_summary_v1.csv`
  - `panel_day_engine_project_progress_snapshot_v1.csv`
  - `panel_day_engine_operator_attention_policy_recommendation_v1.csv`
  - `panel_day_engine_operator_release_gate_manifest_v1.csv`
  - `panel_day_engine_operator_pipeline_manifest_v1.csv`
- detector logic, truth template, 기존 research/prognostics 파일은 바꾸지 않는다.
- seed-panel case flow 를 새로 끌어오지 않는다.

## 출력물
- `_share/panel_day_engine_project_closeout_pack_v1.md`
  - 사람이 읽는 최종 closeout 문서
  - 정확히 여섯 섹션만 가진다.
- `_share/panel_day_engine_project_artifact_index_v1.csv`
  - 어떤 산출물이 어디 있고 왜 읽는지 정리한 index
- `_share/panel_day_engine_project_status_snapshot_v1.csv`
  - branch, HEAD, chosen workflow, release/pipeline 상태, 현재 데이터 한계, 최종 권장 사용 범위를 한 줄씩 정리한 snapshot

## Markdown 구성
- closeout markdown 은 정확히 다음 섹션만 둔다.
  - `1. 지금 확정된 결론`
  - `2. 운영 기본값`
  - `3. 조심해서만 말해야 하는 것`
  - `4. 아직 탐색적으로만 남겨야 하는 것`
  - `5. 가장 먼저 볼 산출물`
  - `6. 프로젝트를 다시 열면 어디서 시작할지`

## 문서에 반드시 들어갈 내용
- 전조형 성능은 표본이 작아 탐색적이라는 점
- 급작 고장은 bounded current-data 수준으로는 사용 가능하다는 점
- common-cause / 같이 흔들리는 이상은 탐색적이라는 점
- chosen operational workflow 가 `baseline_plus_discovery_cluster` 라는 점
- release gate / pipeline pass 상태
- 현재는 추가 fault case 수집이 불가능하다는 점

## Artifact Index 원칙
- index 는 최소한 아래 산출물을 포함한다.
  - `panel_day_engine_project_final_decision_pack_v1.csv`
  - `panel_day_engine_project_final_do_and_dont_v1.csv`
  - `panel_day_engine_project_handoff_pack_v1.md`
  - `panel_day_engine_internal_share_clean_pack_v1.md`
  - `panel_day_engine_abrupt6_symptom_map_v1.csv`
  - `panel_day_engine_kernellog_project_mapping_v1.csv`
  - `panel_day_engine_gpv7_perf_summary_v1.csv`
  - `panel_day_engine_project_progress_snapshot_v1.csv`
  - `panel_day_engine_operator_pipeline_manifest_v1.csv`
  - `panel_day_engine_operator_release_gate_manifest_v1.csv`
- 각 row 는 `용도`, `지금 읽는 목적`, `비고`를 짧게 적는다.

## Status Snapshot 원칙
- status snapshot 은 최소한 다음 항목을 가진다.
  - `현재_브랜치`
  - `현재_HEAD_커밋`
  - `완료된_로드맵_최대단계`
  - `선택된_운영_workflow`
  - `release_gate_통과여부`
  - `pipeline_통과여부`
  - `현재_데이터_한계`
  - `최종_권장_사용_범위`
- git 정보는 subprocess git command 로 읽는다.

## 사용법
- 내부 인수인계:
  - 먼저 `panel_day_engine_project_closeout_pack_v1.md` 를 읽는다.
  - 그 다음 `panel_day_engine_project_status_snapshot_v1.csv` 로 현재 branch / HEAD / workflow / pass 상태를 확인한다.
  - 필요한 세부는 `panel_day_engine_project_artifact_index_v1.csv` 를 보고 해당 산출물로 바로 이동한다.
- 발표/보고:
  - closeout markdown 3, 4, 5 섹션을 claim boundary 체크리스트로 쓴다.
  - workflow 사용 가능 상태를 detector 일반 성능 고정으로 바꾸어 말하지 않는다.

## Smoke Test 기준
- 새 builder / smoke script 가 compile 되어야 한다.
- markdown 여섯 섹션이 모두 생성돼야 한다.
- artifact index 필수 row 가 생성돼야 한다.
- status snapshot 필수 row 가 생성돼야 한다.
- official outputs 는 smoke 중 바뀌지 않아야 한다.

## 주의
- 이 문서는 프로젝트 종료 시점의 closeout index 이다.
- 새 알고리즘, 새 truth, 새 detector 평가를 추가하지 않는다.
