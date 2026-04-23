<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_007_KTC_STRICT_COMMON_REVIEW_V1

## [BR-20260423-007] KTC strict-common review
- `status`: review_packet_generated
- `branch_type`: B
- `current_gate`: Gate 3
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23

## 1. 이슈 요약
- BR-006에서 `review_supported_context` 4건을 daily slice로 좁혔다.
- 그중 `ktc_ess` 2건은 `strict_common_cause + site_event_history` 조합을 가진 가장 강한 후보처럼 보인다.
- 하지만 두 건 모두 selected onset marker가 `prealarm_cond_dtw_mid_or_hi`이고, retained daily slice에서 `signal_count`, `pre_ews`, `ews_warning`, `pre_alarm`이 모두 0이다.

## 2. 이번 브랜치의 목적
- production code는 수정하지 않는다.
- `retrospective_onset_date`, `사건유형`, `최종고장양상`, final verdict는 변경하지 않는다.
- KTC strict-common 2건을 promotion 후보가 아니라 `hold_shadow_only` 수동 검토 대상으로 고정한다.

## 3. 산출물
- repo-tracked:
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_007_KTC_STRICT_COMMON_PANEL_PACKET_V1.csv`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_007_KTC_STRICT_COMMON_DAILY_SLICE_V1.csv`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_007_KTC_STRICT_COMMON_DECISION_SUMMARY_V1.csv`
- local 상세 packet:
  - `/private/tmp/br007_ktc_strict_common_review_packet/br007_ktc_strict_common_panel_packet_v1.csv`
  - `/private/tmp/br007_ktc_strict_common_review_packet/br007_ktc_strict_common_daily_slice_v1.csv`
  - `/private/tmp/br007_ktc_strict_common_review_packet/br007_ktc_strict_common_decision_summary_v1.csv`
  - `/private/tmp/br007_ktc_strict_common_review_packet/br007_ktc_strict_common_review_note_v1.md`

## 4. 핵심 결과
- 대상 패널: `2`
- 자동 승격 후보: `0`
- `hold_shadow_only`: `2`
- retained daily slice `signal_count_sum = 0`: `2`
- selected marker가 `prealarm_cond_dtw_mid_or_hi`: `2`
- fault-like terminal evidence: `2`

## 5. Panel summary
| site | panel_id | selected_onset | strict_trigger | selected_marker | qualified_secondary_count | too_early_secondary_count | signal_count_sum | dtw_days | fault_like_days | decision |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---|
| `ktc_ess` | `10305b40-b67e-40d1-9cd1-271b6642a3d9.2.14` | `2025-06-28` | `2025-10-26` | `prealarm_cond_dtw_mid_or_hi` | 89 | 408 | 0 | 6 | 1 | `hold_shadow_only` |
| `ktc_ess` | `10305b40-b67e-40d1-9cd1-271b6642a3d9.2.17` | `2025-07-07` | `2025-10-26` | `prealarm_cond_dtw_mid_or_hi` | 43 | 428 | 0 | 4 | 1 | `hold_shadow_only` |

## 6. 보수 판단
- 두 패널은 지금까지 본 `trigger_only_to_precursor` 중 가장 강한 축에 속한다.
- 그래도 자동 승격은 금지한다.
- 이유:
  - selected onset이 DTW prealarm에 의존한다.
  - retained daily slice의 `signal_count`, `pre_ews`, `ews_warning`, `pre_alarm`이 모두 0이다.
  - `too_early_secondary_count`가 408, 428로 매우 커서, secondary-window pruning 의존도가 크다.
  - terminal fault-like evidence는 있지만, onset 승격의 독립 근거로는 아직 부족하다.

## 7. 다음 단계
- operator-facing promotion rule을 만들기 전에 selected onset 주변 raw/audit trace를 직접 확인한다.
- 향후 승격 규칙은 `strict_common_cause + DTW prealarm`만으로는 부족하며, 최소한 더 강한 raw evidence 또는 재현 가능한 terminal progression guard가 필요하다.
