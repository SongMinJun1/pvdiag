<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_009_PROMOTION_DECISION_BUCKET_SHADOW_V1

## [BR-20260423-009] promotion decision bucket shadow column
- `status`: shadow_audit_implemented
- `branch_type`: B
- `current_gate`: Gate 3
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23

## 1. 이슈 요약
- BR-008에서 promotion/backdating 판단 bucket을 문서로 고정했다.
- BR-009는 이 계약을 runtime audit CSV의 shadow column으로만 추가한다.
- operator-facing `retrospective_onset_date`, `사건유형`, `최종고장양상`, final verdict는 변경하지 않는다.

## 2. 패치 범위
- source copy:
  - `research/prognostics/runtime_rawonly_chain_common_v1.py`
  - `research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py`
- release package copy:
  - `release/conalog_full_runtime_v1/package/research/prognostics/runtime_rawonly_chain_common_v1.py`
  - `release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py`

## 3. 추가 audit columns
- `promotion_decision_bucket`
- `promotion_decision_reason`

## 4. Exclusive bucket 규칙
- `backdate_suppression_candidate`
  - `degradation_onset_backdate_guard_flag = 1`
  - BR-002 G1 path이며 precursor promotion이 아니다.
- `audit_provenance_only`
  - `secondary_window_review_tier in {audit_provenance_only, audit_no_event_flip}`
  - 단, G1 backdate suppression 후보는 위 bucket이 우선한다.
- `blocked_cluster_risk`
  - `secondary_window_change_class = trigger_only_to_precursor`
  - `secondary_window_review_tier = review_persistent_secondary_only`
- `hold_shadow_only`
  - `secondary_window_change_class = trigger_only_to_precursor`
  - `secondary_window_review_tier = review_supported_context`
  - selected marker가 `prealarm_cond_dtw_mid_or_hi`
  - selected onset 근접창의 independent signal count가 `0`
- `manual_review`
  - `trigger_only_to_precursor`이지만 위 blocker에 걸리지 않는 review 후보
- `promote_candidate`
  - 이번 패치에서는 생성하지 않는다.

## 5. 근접창 기준
- 첫 구현 시 `selected onset ~ strict trigger` 전체 구간 signal을 세면 KTC strict-common 2건이 `manual_review`로 남았다.
- BR-006/BR-007의 판단 근거는 selected onset 주변 retained slice였으므로, BR-009는 selected onset 이후 `10일` 근접창만 independent signal 확인에 쓴다.
- 이 조정 후 KTC strict-common 2건은 의도대로 `hold_shadow_only`가 된다.

## 6. 검증 결과
- baseline command:
  - `python release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/br009_head_baseline_check_v1 --sites conalog,gangui,ktc_ess --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data`
- patch command:
  - `python release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/br009_promotion_bucket_shadow_check_v2 --sites conalog,gangui,ktc_ess --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data`
- py_compile:
  - `python -m py_compile research/prognostics/runtime_rawonly_chain_common_v1.py research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py release/conalog_full_runtime_v1/package/research/prognostics/runtime_rawonly_chain_common_v1.py release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py pv_ae/panel_day_engine.py`
- invariant:
  - runtime audit: `766 x 49 -> 766 x 51`
  - runtime audit common columns: unchanged
  - runtime final verdict: `766 x 37 -> 766 x 37`
  - runtime final verdict common columns: unchanged
  - `promote_candidate`: `0`

## 7. Bucket counts
| promotion_decision_bucket | panel_count |
|---|---:|
| `(empty)` | 654 |
| `audit_provenance_only` | 75 |
| `blocked_cluster_risk` | 26 |
| `backdate_suppression_candidate` | 7 |
| `manual_review` | 2 |
| `hold_shadow_only` | 2 |
| `promote_candidate` | 0 |

## 8. BR-008 숫자와의 차이
- BR-008의 `manual_review=4`, `hold_shadow_only=2`는 evidence-set 관점이라 subset overlap이 있었다.
- BR-009의 `promotion_decision_bucket`은 한 row에 하나의 값만 들어가는 exclusive bucket이다.
- 따라서 `hold_shadow_only` 2건은 `manual_review`에서 빠져 `manual_review=2`, `hold_shadow_only=2`가 된다.
- BR-008의 `audit_provenance_only=82` 역시 evidence-set 관점이다.
- BR-009에서는 G1 `backdate_suppression_candidate=7`을 우선 bucket으로 분리하므로 exclusive `audit_provenance_only=75`가 된다.

## 9. 산출물
- validation summary:
  - `/private/tmp/br009_promotion_bucket_shadow_check_v2/br009_validation_summary_v1.json`
- patched runtime audit:
  - `/private/tmp/br009_promotion_bucket_shadow_check_v2/raw_only_chain_workspace/_share/panel_day_engine_runtime_fault_event_audit_v1.csv`
- patched runtime final verdict:
  - `/private/tmp/br009_promotion_bucket_shadow_check_v2/raw_only_chain_workspace/_share/panel_day_engine_runtime_final_verdict_v1.csv`

## 10. 다음 단계
- 이 shadow bucket을 operator-facing event semantics로 쓰지 않는다.
- 다음 BR은 bucket별 reviewer packet을 더 보기 쉽게 만들거나, `blocked_cluster_risk`와 `hold_shadow_only` counterexample table을 묶는 쪽이 안전하다.
