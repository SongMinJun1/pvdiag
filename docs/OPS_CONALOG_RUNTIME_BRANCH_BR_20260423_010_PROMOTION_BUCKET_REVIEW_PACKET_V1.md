<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_010_PROMOTION_BUCKET_REVIEW_PACKET_V1

## [BR-20260423-010] promotion bucket review packet
- `status`: review_packet_generated
- `branch_type`: B
- `current_gate`: Gate 3
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23

## 1. 이슈 요약
- BR-009에서 `promotion_decision_bucket` shadow column을 runtime audit에 추가했다.
- BR-010은 이 bucket을 사람이 바로 볼 수 있는 review packet으로 재정리한다.
- 이번 브랜치도 production code와 operator-facing verdict를 변경하지 않는다.

## 2. 이번 브랜치의 목적
- `promotion_decision_bucket`이 비어 있지 않은 row를 모두 repo-tracked packet으로 남긴다.
- 실제 수동 검토가 필요한 row와 provenance-only row를 분리한다.
- 다음 구현 논의가 다시 “전부 승격할까?”로 새지 않도록 action queue를 고정한다.

## 3. 산출물
- repo-tracked:
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_010_PROMOTION_BUCKET_PANEL_PACKET_V1.csv`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_010_PROMOTION_BUCKET_SITE_SUMMARY_V1.csv`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_010_PROMOTION_BUCKET_ACTION_QUEUE_V1.csv`
- local validation:
  - `/private/tmp/br010_promotion_bucket_review_packet_v1/br010_review_packet_validation_v1.json`

## 4. 입력 실행
- command:
  - `python release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/br010_promotion_bucket_review_packet_v1 --sites conalog,gangui,ktc_ess --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data`
- source audit:
  - `/private/tmp/br010_promotion_bucket_review_packet_v1/raw_only_chain_workspace/_share/panel_day_engine_runtime_fault_event_audit_v1.csv`
- source audit shape:
  - `766 x 51`

## 5. 핵심 결과
- non-empty bucket rows: `112`
- action queue rows: `37`
- `promote_candidate`: `0`

| bucket | panel_count | action |
|---|---:|---|
| `hold_shadow_only` | 2 | keep shadow until raw/audit support exists |
| `manual_review` | 2 | inspect raw/audit trace before any promotion |
| `backdate_suppression_candidate` | 7 | review G1 degradation backdating suppression |
| `blocked_cluster_risk` | 26 | keep as cluster false-positive counterexample set |
| `audit_provenance_only` | 75 | provenance-only, no action queue |

## 6. Site summary
| bucket | site | panels | roots | avg secondary selected gap | strict common | site event |
|---|---|---:|---:|---:|---:|---:|
| `hold_shadow_only` | `ktc_ess` | 2 | 1 | 115.5 | 2 | 2 |
| `manual_review` | `gangui` | 1 | 1 | 120.0 | 0 | 1 |
| `manual_review` | `ktc_ess` | 1 | 1 | 118.0 | 0 | 1 |
| `backdate_suppression_candidate` | `ktc_ess` | 7 | 3 | 119.1 | 6 | 7 |
| `blocked_cluster_risk` | `gangui` | 26 | 2 | 118.4 | 0 | 0 |
| `audit_provenance_only` | `conalog` | 58 | 5 | 30.6 | 55 | 23 |
| `audit_provenance_only` | `gangui` | 10 | 2 | 117.7 | 8 | 0 |
| `audit_provenance_only` | `ktc_ess` | 7 | 4 | 94.6 | 1 | 7 |

## 7. Action queue 해석
- `hold_shadow_only` 2건은 가장 강해 보였던 `ktc_ess` strict-common 후보지만, DTW-only selected onset이라 운영 승격 금지 상태를 유지한다.
- `manual_review` 2건은 gangui 1건, ktc_ess 1건이다. context는 있지만 승격 기준을 만족하지 않는다.
- `backdate_suppression_candidate` 7건은 current precursor를 없앨지 보는 억제 후보이지, precursor promotion 후보가 아니다.
- `blocked_cluster_risk` 26건은 gangui persistent-secondary-only cluster risk set으로 남긴다.
- `audit_provenance_only` 75건은 event flip 없이 provenance/date 해석만 참고한다.

## 8. 중요한 주의점
- `trigger_only_to_precursor` row의 current `retrospective_onset_date`는 비어 있고 `gap_days=0`일 수 있다.
- 따라서 review packet에서 trigger-only 후보의 시간 간격은 `secondary_window_selected_gap_days`를 기준으로 읽어야 한다.
- operator-facing 사건유형은 이번 packet에서 절대 바꾸지 않는다.

## 9. 검증
- `promote_candidate_count = 0`
- panel packet rows: `112`
- action queue rows: `37`
- site summary rows: `8`
- `python -m py_compile pv_ae/panel_day_engine.py`

## 10. 다음 단계
- 먼저 `action_queue` 37건 중 사람이 볼 우선순위를 유지한다.
- 다음 BR을 연다면 아래 둘 중 하나가 안전하다.
  - `blocked_cluster_risk` 26건의 root-cluster counterexample deep packet
  - `backdate_suppression_candidate` 7건의 before/after suppression shadow simulation
