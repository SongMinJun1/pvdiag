<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_021_V1

## Decision
- 현재 raw/audit에 이미 있는 재료로 `new evidence axis`를 추가로 만들 수 있다.
- 다만 이 축은 먼저 `evidence-only sidecar`로 시작한다.
- 즉 아래는 아직 새 top-level fault label이나 operator headline 축이 아니다.
  - `report_entry_friction_axis`
  - `recovery_recurrence_axis`
  - `common_cause_synchrony_axis`
  - `observability_continuity_axis`
  - `control_scope_hint_axis`
- 현재 우선순위는 `report_entry_friction_axis`, `recovery_recurrence_axis`, `common_cause_synchrony_axis` 순서다.

## Evidence
- `report_entry_friction_axis`
  - `group_off_date`
    - `gangui 71 rows / 19 panels`
    - BR-037 기준 report-layer exact family 대신 blocker subtype으로 갈라짐
  - `site_event`
    - `ktc_ess 30 rows / 30 panels`
    - presence:
      - `current+rawonly = 1`
      - `precursor = 17`
      - `none = 12`
    - only current case도 nearest gap `71일`
- `recovery_recurrence_axis`
  - tri-site counts:
    - `recovered_any = 253 / 292 / 304`
    - `recovered_sustained = 141 / 96 / 231`
    - `re_drop = 53 / 25 / 141`
- `common_cause_synchrony_axis`
  - raw:
    - `subgroup_common_cause_candidate = 109 / 20 / 152`
  - audit:
    - `common_cause_history_flag = 196`
    - `subgroup_common_cause_history_flag = 71`
    - `strict_trigger_proximal_common_cause_flag = 64`
    - `trigger_proximal_common_cause_flag = 78`
- `observability_continuity_axis`
  - `drop_time_nonnull = 627 / 807 / 391`
  - `seg_count_ge_2 = 317 / 615 / 276`
  - `coverage_mid_lt_0.6 = 1 / 3 / 0`

## Reading
- 지금은 새 fault family를 invent하는 게 아니라, 기존 raw/audit을 더 잘 읽게 만드는 축을 뽑는 단계다.
- 특히 아래 세 축은 즉시성도 높고, 현재 blocker 설명력도 높다.
  - `report_entry_friction_axis`
    - 왜 raw row가 report-layer exact로 못 올라오는지 설명
  - `recovery_recurrence_axis`
    - transient / recovered / re-drop / persistent를 분리
  - `common_cause_synchrony_axis`
    - singleton 해석과 group/site synchrony를 분리

## Consequence
- 다음 새 축 구현은 `evidence-only sidecar`로 간다.
- 새 축은 아래 순서로 승격 여부를 본다.
  1. raw/audit existing fields만으로 재현 가능
  2. exact family를 억지 closure하지 않음
  3. blocker subtype 또는 hold/review 설명력을 실제로 높임
  4. 그 다음에야 score/projection 연결 여부를 검토
