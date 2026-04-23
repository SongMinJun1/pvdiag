<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_005_TRIGGER_ONLY_TO_PRECURSOR_REVIEW_V1

## [BR-20260423-005] trigger-only to precursor review packet
- `status`: review_packet_generated
- `branch_type`: B
- `current_gate`: Gate 3
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23

## 1. 이슈 요약
- BR-004는 `secondary_window_change_class = trigger_only_to_precursor` 후보 `30`건을 드러냈다.
- 이 후보들은 현재 `급작 고장` 또는 trigger-only 해석이지만, later qualified secondary warning을 onset으로 채택하면 `전조형 고장`으로 이동할 수 있는 사례다.
- 따라서 이 묶음은 operator-facing 규칙으로 바로 승격하면 사건유형을 흔들 수 있다.

## 2. 이번 브랜치의 목적
- production code는 수정하지 않는다.
- `retrospective_onset_date`, `사건유형`, `최종고장양상`, final verdict는 변경하지 않는다.
- BR-004 산출물을 바탕으로 `trigger_only_to_precursor` 후보를 review tier별로 나누고, 어떤 subset이 후속 수동 검토 대상인지 정리한다.

## 3. Review packet 산출물
- repo-tracked 요약:
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_005_TRIGGER_ONLY_DECISION_SUMMARY_V1.csv`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_005_TRIGGER_ONLY_SITE_TIER_SUMMARY_V1.csv`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_005_TRIGGER_ONLY_ROOT_CLUSTER_SUMMARY_V1.csv`
- local 상세 packet:
- `/private/tmp/br005_trigger_only_review_packet/br005_trigger_only_to_precursor_review_packet_v1.csv`
- `/private/tmp/br005_trigger_only_review_packet/br005_trigger_only_to_precursor_decision_summary_v1.csv`
- `/private/tmp/br005_trigger_only_review_packet/br005_trigger_only_to_precursor_site_tier_summary_v1.csv`
- `/private/tmp/br005_trigger_only_review_packet/br005_trigger_only_to_precursor_root_cluster_summary_v1.csv`
- `/private/tmp/br005_trigger_only_review_packet/br005_trigger_only_to_precursor_review_note_v1.md`

## 4. 핵심 결과
- 전체 후보: `30 panels`
- `review_supported_context`: `4 panels`
  - `gangui`: `1`
  - `ktc_ess`: `3`
- `review_persistent_secondary_only`: `26 panels`
  - 전부 `gangui`
- `strict_trigger_proximal_common_cause = true`: `2 panels`
- `site_event_history = true`: `4 panels`
- `subgroup_common_cause_history = true`: `0 panels`

## 5. Site x review tier
| site | review_tier | panel_count | avg_gap_days | avg_qualified_secondary_count | strict_common | site_event | subgroup_common |
|---|---|---:|---:|---:|---:|---:|---:|
| `gangui` | `review_persistent_secondary_only` | 26 | 118.4 | 73.0 | 0 | 0 | 0 |
| `gangui` | `review_supported_context` | 1 | 120.0 | 688.0 | 0 | 1 | 0 |
| `ktc_ess` | `review_supported_context` | 3 | 116.3 | 60.3 | 2 | 3 | 0 |

## 6. Root cluster 요약
| site | panel_root | panel_count | onset_range | strict_range | avg_qualified_secondary_count | review_tiers |
|---|---|---:|---|---|---:|---|
| `gangui` | `bf1a912f-6cf0-4f12-8e97-9d9d86576511` | 20 | `2025-06-29..2025-07-21` | `2025-10-27..2025-11-13` | 94.3 | `review_persistent_secondary_only, review_supported_context` |
| `gangui` | `4fd0c566-e25e-4d51-96ca-57cc46940593` | 7 | `2025-07-14..2025-07-20` | `2025-11-11..2025-11-17` | 100.0 | `review_persistent_secondary_only` |
| `ktc_ess` | `10305b40-b67e-40d1-9cd1-271b6642a3d9` | 3 | `2025-04-20..2025-07-07` | `2025-08-16..2025-10-26` | 60.3 | `review_supported_context` |

## 7. 판단
- `review_supported_context` 4건은 후속 수동 검토 1순위로 둔다.
- 다만 이 4건도 아직 자동 승격 대상은 아니다.
- `review_persistent_secondary_only` 26건은 secondary warning persistence가 강하지만, strict/common-cause/site-event 근거가 약하다.
- 따라서 이 26건은 cluster-level false-positive risk가 해소되기 전까지 operator-facing `전조형 고장` 승격을 금지한다.

## 8. 다음 단계
- `review_supported_context` 4건을 상세 daily slice로 먼저 본다.
- 필요하면 `site_event_history`, `strict_trigger_proximal_common_cause`, terminal evidence를 묶은 더 좁은 promotion 후보를 새 BR로 분리한다.
- `review_persistent_secondary_only`는 counterexample set 또는 false-positive review set으로 유지한다.

## 9. Dirty worktree 운영 원칙
- `/Users/b9gc/pvdiag` main worktree는 기존 미분류 변경이 많으므로 직접 reset/checkout하지 않는다.
- 후속 BR 작업은 clean worktree `/private/tmp/pvdiag_br005_trigger_review`에서 진행한다.
- dirty 상태 백업:
  - `/private/tmp/pvdiag_dirty_status_after_br004_merge_20260423.txt`
  - `/private/tmp/pvdiag_dirty_tracked_diff_after_br004_merge_20260423.patch`
