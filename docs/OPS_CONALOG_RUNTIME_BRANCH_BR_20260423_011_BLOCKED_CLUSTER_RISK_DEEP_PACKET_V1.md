<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_011_BLOCKED_CLUSTER_RISK_DEEP_PACKET_V1

## [BR-20260423-011] blocked cluster risk deep packet
- `status`: deep_packet_generated
- `branch_type`: B
- `current_gate`: Gate 3
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23

## 1. 이슈 요약
- BR-010 action queue에서 `blocked_cluster_risk`는 26건이다.
- 26건 모두 `gangui`이고, 2개 `panel_root`에 집중되어 있다.
- 이번 브랜치는 이 26건을 다시 쪼개 “승격 후보”가 아니라 “군집성 false-positive 반례 set”으로 유지해야 하는 근거를 고정한다.
- production code, runtime verdict, operator-facing 사건 의미는 변경하지 않는다.

## 2. 입력 산출물
- source packet:
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_010_PROMOTION_BUCKET_PANEL_PACKET_V1.csv`
- source bucket:
  - `promotion_decision_bucket = blocked_cluster_risk`
- source row count:
  - `26`

## 3. 새 산출물
- repo-tracked:
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_011_BLOCKED_CLUSTER_PANEL_PACKET_V1.csv`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_011_BLOCKED_CLUSTER_ROOT_SUMMARY_V1.csv`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_011_BLOCKED_CLUSTER_MARKER_SUMMARY_V1.csv`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_011_BLOCKED_CLUSTER_DATE_PAIR_SUMMARY_V1.csv`
- local validation:
  - `/private/tmp/br011_blocked_cluster_deep_packet_v1/br011_blocked_cluster_validation_summary_v1.json`

## 4. 핵심 결과
- blocked cluster rows: `26`
- site distribution: `gangui = 26`
- root distribution:
  - `bf1a912f-6cf0-4f12-8e97-9d9d86576511 = 19`
  - `4fd0c566-e25e-4d51-96ca-57cc46940593 = 7`
- selected secondary onset date range: `2025-07-14` to `2025-07-21`
- strict trigger date range: `2025-11-11` to `2025-11-17`
- secondary selected gap range: `115` to `120` days
- `site_event_history_flag`: `0 / 26`
- `subgroup_common_cause_history_flag`: `0 / 26`
- `strict_trigger_proximal_common_cause_flag`: `0 / 26`
- `promotion_candidate_allowed`: `0 / 26`
- `operator_facing_change_allowed`: `0 / 26`

## 5. Root summary
| site | panel_root | panels | selected onset span | strict trigger span | selected gap mean | marker mix | decision |
|---|---|---:|---|---|---:|---|---|
| `gangui` | `bf1a912f-6cf0-4f12-8e97-9d9d86576511` | 19 | `2025-07-14` to `2025-07-21` | `2025-11-11` to `2025-11-13` | 118.105 | `prealarm_cond_hs_mid_or_hi:9; prealarm_cond_ae_mid_or_hi:7; prealarm_cond_dtw_mid_or_hi:3` | `blocked_counterexample_hold` |
| `gangui` | `4fd0c566-e25e-4d51-96ca-57cc46940593` | 7 | `2025-07-14` to `2025-07-20` | `2025-11-11` to `2025-11-17` | 119.286 | `prealarm_cond_ae_mid_or_hi:3; prealarm_cond_hs_mid_or_hi:3; prefault_cond_ae:1` | `blocked_counterexample_hold` |

## 6. Marker summary
| selected marker | panels | roots | gap range | site/subgroup/strict-proximal support |
|---|---:|---:|---|---|
| `prealarm_cond_hs_mid_or_hi` | 12 | 2 | `115` to `120` | `0 / 12` |
| `prealarm_cond_ae_mid_or_hi` | 10 | 2 | `116` to `120` | `0 / 10` |
| `prealarm_cond_dtw_mid_or_hi` | 3 | 1 | `119` to `120` | `0 / 3` |
| `prefault_cond_ae` | 1 | 1 | `120` to `120` | `0 / 1` |

## 7. 판단
- 이 set은 “고장 직전 공통 원인”이 아니라 “7월 중순 secondary marker가 같은 root cluster에서 오래 남아 있던 패턴”에 가깝다.
- strict trigger는 11월 중순으로 모여 있지만, selected secondary onset은 115~120일 전이다.
- `site_event_history_flag`, `subgroup_common_cause_history_flag`, `strict_trigger_proximal_common_cause_flag`가 모두 0이라서 현 단계에서 operator-facing 전조 승격 근거가 없다.
- 따라서 `blocked_cluster_risk` 26건은 `blocked_counterexample_hold`로 유지한다.

## 8. Decision lock
- `persistent_secondary_only`는 독립 승격 근거가 아니다.
- 같은 site/root에 대량으로 몰린 secondary-only 패턴은 먼저 false-positive cluster 반례로 취급한다.
- 이 set은 `manual_review`로 올리지 않는다. 수동 검토 대상은 BR-010의 `manual_review=2`, `hold_shadow_only=2`, `backdate_suppression_candidate=7` 쪽이 우선이다.
- 이 branch는 suppression patch 또는 promotion patch의 근거가 아니다.

## 9. 검증
- pre-change reproduction command:
  - `python -c "import pandas as pd; df=pd.read_csv('docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_010_PROMOTION_BUCKET_PANEL_PACKET_V1.csv'); print(df[df.promotion_decision_bucket.eq('blocked_cluster_risk')].shape)"`
- post-change validation commands:
  - `python -m py_compile pv_ae/panel_day_engine.py`
  - `git diff --check`
  - `python release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/br011_conalog_smoke_v1 --sites conalog --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data`
- row count invariant:
  - `panel packet rows = 26`
  - `root summary rows = 2`
  - `marker summary rows = 4`
  - `date pair summary rows = 12`
- blocking invariant:
  - `promotion_candidate_allowed_count = 0`
  - `operator_facing_change_allowed_count = 0`
- validation artifact:
  - `/private/tmp/br011_blocked_cluster_deep_packet_v1/br011_blocked_cluster_validation_summary_v1.json`
- conalog smoke artifact:
  - `/private/tmp/br011_conalog_smoke_v1/result/fault_panel_result_master_report_v1.md`

## 10. 다음 단계
- `blocked_cluster_risk`는 hard hold로 닫는다.
- 다음 안전한 BR은 `backdate_suppression_candidate` 7건의 G1 suppression shadow simulation이다.
- 이때도 먼저 before/after audit-only diff를 만들고, production runtime verdict 변경은 별도 승인을 받은 뒤에만 진행한다.
