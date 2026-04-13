# OPS_PANEL_DAY_ENGINE_OPERATOR_PIPELINE_IDEMPOTENCE_AUDIT_V1

## 목적

operator stack의 packaging이 완성되었다고 해서 곧바로 operationally stable 하다고 볼 수는 없습니다.  
같은 입력으로 pipeline을 연속 두 번 돌렸을 때, 두 번째 실행에서 spurious change가 없어야 비로소 steady-state 운영 entrypoint라고 말할 수 있습니다.

`operator_pipeline_idempotence_audit_v1` 는 이 성질을 점검하는 non-core operator-facing audit입니다.  
detector/scorer 변경이 아니라, 현재 packaging/orchestration layer가 back-to-back rerun에서 안정적인지 보는 운영 감사입니다.

## 실행

기본 전체 site:

```bash
python research/prognostics/build_panel_day_engine_operator_pipeline_idempotence_audit_v1.py
```

선택 site:

```bash
python research/prognostics/build_panel_day_engine_operator_pipeline_idempotence_audit_v1.py --sites conalog,gangui
```

## 입력 / 출력

입력:
- existing pipeline entrypoint
  - `research/prognostics/build_panel_day_engine_operator_pipeline_v1.py`
- 각 run 뒤에 읽는 current artifacts
  - `_share/panel_day_engine_operator_pipeline_manifest_v1.csv`
  - `_share/panel_day_engine_operator_refresh_qa_summary_v1.csv`
  - `_share/panel_day_engine_operator_baseline_manifest_v1.csv`

출력:
- `_share/panel_day_engine_operator_pipeline_idempotence_report_v1.csv`
- `_share/panel_day_engine_operator_pipeline_idempotence_summary_v1.csv`

## 어떻게 검사하는가

1. 같은 site set으로 pipeline을 연속 두 번 실행합니다.
2. 첫 번째 실행 직후 pipeline manifest / QA summary / baseline manifest를 snapshot 합니다.
3. 같은 입력으로 두 번째 실행을 다시 돌리고 동일 artifact를 다시 snapshot 합니다.
4. 아래 성질을 비교합니다.

핵심 hard check:
- first run pipeline pass 여부
- second run pipeline pass 여부
- second run `overall_changed_count == 0`
- second run `overall_cluster_delta_changed_count == 0`
- second run `overall_unified_digest_changed_count == 0`
- second run `overall_workflow_default_changed_count == 0`
- first vs second attention / queue / cluster preview / discovery cluster / workflow default count 일치
- first vs second QA pass flag 일치

추가 info check:
- watch_now / watch_review / backlog / unified digest count 등 steady count가 유지되는지 참고용으로 함께 남깁니다.

## 왜 second-run zero-change가 핵심인가

- 첫 번째 run은 이전 snapshot 상태에 따라 delta가 생길 수 있습니다.
- 하지만 입력이 바뀌지 않은 상태에서 바로 이어지는 두 번째 run이라면,
  - attention delta가 더 이상 새 변화를 만들지 않아야 하고,
  - discovery cluster delta도 더 이상 changed/new/dropped를 만들지 않아야 하며,
  - unified digest와 workflow default도 spurious changed count가 0이어야 합니다.

즉 second run zero-change는 "현재 operator stack이 steady-state에서 스스로 요동치지 않는다"는 가장 중요한 운영 성질입니다.

## idempotence 실패가 뜻하는 것

- second run changed count가 남아 있으면:
  - snapshot update 순서가 불안정하거나
  - packaging layer가 rerun마다 같은 현재 상태를 다르게 해석하거나
  - operator-facing delta/workflow view가 steady-state에서 불필요한 change를 만들고 있을 수 있습니다.

- first vs second stable count가 어긋나면:
  - 입력이 실제로 안 바뀌었는데도 현재-state packaging 결과가 흔들리고 있다는 뜻입니다.

이 경우 운영자는 pipeline을 "반복 실행해도 같은 현재 상태를 재현하는 entrypoint"로 신뢰하기 어렵습니다.

## summary 해석

`panel_day_engine_operator_pipeline_idempotence_summary_v1.csv` 는 한 줄로 다음을 보여 줍니다.

- audit 시작/종료 시각
- hard fail 개수 / hard pass 개수
- first / second run pipeline pass flag
- second run changed count
- second run cluster delta changed count
- second run unified digest changed count
- second run workflow default changed count
- 최종 `idempotence_pass_flag`

`idempotence_pass_flag = 1` 은 hard check가 모두 통과했다는 뜻입니다.  
즉 동일 입력 back-to-back second run에서 steady-state가 확인된 상태입니다.

## detector change가 아닌 이유

- 이 audit은 detector logic이나 scoring rule을 바꾸지 않습니다.
- 기존 pipeline entrypoint를 두 번 실행하고, 이미 생성되는 manifest/summary를 비교해 steady-state 성질을 점검할 뿐입니다.
- 즉 연구/모델 변경이 아니라 operator packaging의 operational stability audit입니다.
