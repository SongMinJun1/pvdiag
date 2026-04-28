<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_023_V1

## Decision
- `recovery_recurrence_axis`를 두 번째 evidence-only sidecar로 구현한다.
- 이 축은 `transient / sustained / re-drop / persistent_non_recovery`를 새 fault label이 아니라 `event morphology evidence`로만 설명한다.

## Why
- BR-039에서 이 축은 P1 후보였고, 실제 tri-site raw counts도 충분했다.
  - `recovered_any = 253 / 292 / 304`
  - `recovered_sustained = 141 / 96 / 231`
  - `re_drop = 53 / 25 / 141`
- 이번 실제 sidecar run에서도 site별로 다른 morphology 분포가 드러났다.
  - `conalog`: recovery가 mostly `rawonly_current`
  - `gangui`: `rawonly_current`와 `precursor`가 혼재
  - `ktc_ess`: `none`과 `precursor`에 recovery/re-drop이 많이 남음

## Lock
- first implementation scope:
  - `recovered_any`
  - `recovered_sustained`
  - `re_drop`
  - `sustain_mins`
  - `drop_time`
- first output role:
  - transient vs persistent vs re-drop explanation
  - hold/review explanation
  - site-wise morphology difference explanation
- not allowed:
  - top-level fault taxonomy 직접 변경
  - operator headline 직접 승격
  - runtime threshold 직접 조정

## Immediate Follow-up
- next evidence-axis implementation candidate is `common_cause_synchrony_axis`.
- `recovery_recurrence_axis`는 지금 단계에서 `exact family closure`를 만들기 위한 축이 아니라, morphology evidence와 report-lane 편향을 분해하는 축으로 읽는다.
