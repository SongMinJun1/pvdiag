<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_039_EVIDENCE_AXIS_EXPANSION_OPPORTUNITY_MAP_V1

## Purpose
- `group_off blocker split`에서 쓴 방식이 다른 영역에도 통하는지 확인하고, 어떤 새 evidence axis를 먼저 만들면 좋을지 opportunity map으로 정리한다.

## Decision
- answer: `yes`
- 다만 먼저 만들 축은 아래 성격이어야 한다.
  - 기존 raw/audit fields로 재현 가능
  - exact family를 억지로 닫지 않음
  - blocker / hold / review 설명력을 올려줌

## Priority Map
| priority | axis | why now | immediate target |
| --- | --- | --- | --- |
| `P1` | `report_entry_friction_axis` | exact-row reservoir와 report-layer family 사이의 미진입/날짜 어긋남을 직접 설명 | `group_off_date`, `site_event` |
| `P1` | `recovery_recurrence_axis` | transient vs persistent vs re-drop을 exact family와 별도로 설명 가능 | `recovered_any`, `recovered_sustained`, `re_drop`, `sustain_mins`, `drop_time` |
| `P1` | `common_cause_synchrony_axis` | panel-local과 group/site synchrony를 더 잘 분리 | `subgroup_common_cause_candidate`, proximal/common-cause flags |
| `P2` | `observability_continuity_axis` | weak evidence와 weak observability를 분리 | `drop_time`, `seg_count`, `coverage_mid`, `data_bad` |
| `P2` | `control_scope_hint_axis` | control-family exact closure 전에도 evidence-only hint로는 유용 | `mid_v_ratio`, `mid_i_ratio`, `critical_source`, `site_event_reason` |

## Why These Axes Are Viable
### 1. `report_entry_friction_axis`
- already observed:
  - `group_off_date`
    - `gangui 71 rows / 19 panels`
    - BR-037 blocker subtype split 가능
  - `site_event`
    - `ktc_ess 30 rows / 30 panels`
    - `precursor 17`, `none 12`, `current+rawonly 1`
    - only current case has nearest gap `71일`
- reading:
  - 같은 evidence라도 `lane entry failure`, `precursor carry-over`, `date displacement`를 분리해 설명할 수 있다.

### 2. `recovery_recurrence_axis`
- raw counts already exist at scale:
  - `recovered_any = 253 / 292 / 304`
  - `recovered_sustained = 141 / 96 / 231`
  - `re_drop = 53 / 25 / 141`
- reading:
  - 지금은 “강한 신호”만 보고 있지만, 실제로는 `회복`, `지속 회복`, `재드랍`을 분리하면 event morphology가 많이 선명해질 수 있다.

### 3. `common_cause_synchrony_axis`
- raw:
  - `subgroup_common_cause_candidate = 109 / 20 / 152`
- audit:
  - `common_cause_history_flag = 196`
  - `subgroup_common_cause_history_flag = 71`
  - `strict_trigger_proximal_common_cause_flag = 64`
  - `trigger_proximal_common_cause_flag = 78`
- reading:
  - singleton false positive와 synchrony-backed hold를 더 잘 구분할 수 있다.

### 4. `observability_continuity_axis`
- raw support exists:
  - `drop_time_nonnull = 627 / 807 / 391`
  - `seg_count_ge_2 = 317 / 615 / 276`
  - `coverage_mid_lt_0.6 = 1 / 3 / 0`
- reading:
  - exact family 부재가 진짜 signal 부재인지, 관측/continuity 약화 때문인지 나눌 수 있다.

### 5. `control_scope_hint_axis`
- immediate closure는 아니지만 raw materials exist:
  - `mid_v_ratio`, `mid_i_ratio`, `critical_source`, `site_event_reason`
- reading:
  - control-family top1이 아직 비어 있어도, evidence-only hint axis로는 충분히 유용하다.

## What This Does Not Mean
- 새 axis를 만든다고 바로 새 fault label을 만든다는 뜻은 아니다.
- 새 axis를 만든다고 바로 operator-facing top-level projection에 연결한다는 뜻도 아니다.
- first use is:
  - blocker explanation
  - hold/review explanation
  - evidence-grade decomposition

## Recommended Order
1. `report_entry_friction_axis` sidecar
2. `recovery_recurrence_axis` sidecar
3. `common_cause_synchrony_axis` sidecar
4. then only consider `observability_continuity_axis`
5. keep `control_scope_hint_axis` evidence-only until exact family closure appears

## External Summary Artifact
- evidence opportunity count summary:
  - [/private/tmp/evidence_axis_expansion_opportunity_scan/evidence_axis_opportunity_summary_v1.csv](/private/tmp/evidence_axis_expansion_opportunity_scan/evidence_axis_opportunity_summary_v1.csv)
