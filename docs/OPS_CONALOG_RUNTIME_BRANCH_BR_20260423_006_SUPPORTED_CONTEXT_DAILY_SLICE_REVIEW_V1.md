<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_006_SUPPORTED_CONTEXT_DAILY_SLICE_REVIEW_V1

## [BR-20260423-006] supported-context daily slice review
- `status`: review_packet_generated
- `branch_type`: B
- `current_gate`: Gate 3
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23

## 1. 이슈 요약
- BR-005에서 `trigger_only_to_precursor` 후보 30건 중 `review_supported_context` 4건을 우선 수동 검토 대상으로 분리했다.
- 이 4건은 case-level context가 상대적으로 강하지만, operator-facing `전조형 고장`으로 자동 승격하기에는 아직 근거 경계가 불충분하다.
- BR-006은 이 4건의 onset 주변 daily slice를 보존해, 날짜 흐름상 근거가 살아있는지 확인하는 review packet이다.

## 2. 이번 브랜치의 목적
- production code는 수정하지 않는다.
- `retrospective_onset_date`, `사건유형`, `최종고장양상`, final verdict는 변경하지 않는다.
- `review_supported_context` 4건의 daily slice와 panel summary를 repo-tracked evidence로 남긴다.

## 3. 산출물
- repo-tracked:
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_006_SUPPORTED_CONTEXT_DAILY_SLICE_V1.csv`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_006_SUPPORTED_CONTEXT_PANEL_SUMMARY_V1.csv`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_006_SUPPORTED_CONTEXT_DECISION_SUMMARY_V1.csv`
- local 상세 packet:
  - `/private/tmp/br006_supported_context_daily_slice_packet/br006_supported_context_daily_slice_v1.csv`
  - `/private/tmp/br006_supported_context_daily_slice_packet/br006_supported_context_panel_summary_v1.csv`
  - `/private/tmp/br006_supported_context_daily_slice_packet/br006_supported_context_decision_summary_v1.csv`
  - `/private/tmp/br006_supported_context_daily_slice_packet/br006_supported_context_daily_slice_note_v1.md`

## 4. 핵심 결과
- 대상 패널: `4`
- daily slice rows: `53`
- `priority_manual_review`: `4`
- 자동 승격 후보: `0`
- case-level `site_event_history`: `4`
- case-level `strict_common_cause`: `2`
- case-level terminal evidence: `2`
- retained daily slice에서 `signal_count > 0`인 패널: `1`

## 5. Panel summary
| site | panel_id | cf_onset | cf_strict | cf_gap_days | slice_rows | signal_count_sum | signal_nonzero_days | qualified_secondary_count | context_score | strict_common | terminal_evidence | review_priority |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| `gangui` | `bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.9` | `2025-06-29` | `2025-10-27` | 120 | 14 | 21 | 14 | 688 | 5 | false | true | `priority_manual_review` |
| `ktc_ess` | `10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12` | `2025-04-20` | `2025-08-16` | 118 | 14 | 0 | 0 | 43 | 5 | false | true | `priority_manual_review` |
| `ktc_ess` | `10305b40-b67e-40d1-9cd1-271b6642a3d9.2.14` | `2025-06-28` | `2025-10-26` | 120 | 14 | 0 | 0 | 91 | 6 | true | false | `priority_manual_review` |
| `ktc_ess` | `10305b40-b67e-40d1-9cd1-271b6642a3d9.2.17` | `2025-07-07` | `2025-10-26` | 111 | 11 | 0 | 0 | 47 | 6 | true | false | `priority_manual_review` |

## 6. 보수 판단
- 4건 모두 `priority_manual_review`지만, 자동 승격은 `0`건으로 둔다.
- `ktc_ess` 2건은 `strict_common_cause + site_event_history` 조합이라 상대적으로 가장 강한 후보지만, retained daily slice의 `signal_count`가 0이라 raw/audit 해석을 더 확인해야 한다.
- `ktc_ess` 1건은 site-event history와 terminal evidence는 있지만 strict common-cause가 없어 별도 확인이 필요하다.
- `gangui` 1건은 retained daily slice signal이 가장 강하지만, 같은 root cluster의 다수 이웃이 `review_persistent_secondary_only`에 남아 있어 cluster-level false-positive risk가 계속 열린다.

## 7. 다음 단계
- 승격 검토가 필요하면 `site_event_history + strict_common_cause` 조합의 `ktc_ess` 2건부터 raw/audit 상세 확인을 수행한다.
- `gangui` 1건은 같은 root cluster의 26건 persistent-secondary-only 반례와 같이 봐야 한다.
- 이 packet만으로는 `trigger_only_to_precursor`를 operator-facing `전조형 고장`으로 승격하지 않는다.
