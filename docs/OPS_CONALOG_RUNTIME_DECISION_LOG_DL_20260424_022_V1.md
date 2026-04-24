<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_022_V1

## Decision
- `report_entry_friction_axis`는 이제 문서 후보가 아니라, 재현 가능한 evidence-only sidecar로 구현한다.
- 이 sidecar는 `panel_day_engine.py`를 바꾸지 않고도 `group_off_date`, `site_event` direct raw row가 report-layer에서 어디서 막히는지 반복적으로 설명할 수 있어야 한다.

## Why
- BR-037, BR-035, BR-039까지 오면서 blocker는 충분히 보였지만, 그 근거가 계속 ad-hoc temp scan에 머물러 있었다.
- 이제는 같은 질문을 다시 할 때마다 임시 조인 스크립트를 새로 쓰기보다, 고정된 sidecar output으로 재현해야 판단이 덜 흔들린다.
- 현재 단계의 목적은 `exact family closure`가 아니라 `structural_blocker`를 안정적으로 설명하는 것이다.

## Lock
- first implementation scope:
  - `group_off_date`
  - `site_event_soft`
  - `site_event_hard`
- first output role:
  - blocker subtype explanation
  - hold/review explanation
  - family-closure 미달 사유 설명
- not allowed:
  - top-level fault label 직접 생성
  - operator headline 직접 승격
  - runtime threshold 직접 조정

## Immediate Follow-up
- 구현 이후에는 같은 방식으로 `recovery_recurrence_axis`를 다음 후보로 본다.
- `report_entry_friction_axis` 결과가 exact family를 닫지 못해도, 그건 실패가 아니라 blocker family의 재현성 확보로 읽는다.
