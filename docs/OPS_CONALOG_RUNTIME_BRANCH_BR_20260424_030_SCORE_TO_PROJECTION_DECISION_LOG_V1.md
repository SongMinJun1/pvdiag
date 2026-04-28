<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_030_SCORE_TO_PROJECTION_DECISION_LOG_V1

## Purpose
- Lock the `score axis -> projection` precedence before any algorithm gating patch.
- Keep this branch docs-only.
- Turn BR-026/027/028/029 into one interpretable gate.

## Scope
- upstream docs:
  - [OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md)
  - [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_REGRESSION_CHECKLIST_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_REGRESSION_CHECKLIST_V1.md)
  - [OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_028_MISSING_SEED_SCAN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_028_MISSING_SEED_SCAN_V1.md)
  - [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_013_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_013_V1.md)
- new decision:
  - [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_014_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_014_V1.md)

## Review Result
### 1. projection은 score rank 문제가 아니라 lane precedence 문제다
- `precursor_score`, `hard_evidence_score`는 promotion lane 후보가 될 수 있다.
- `common_cause_risk_score`, `mlpe_ambiguity_score`는 hold/reroute cap 역할이다.
- `actionability_score`는 마지막 action ceiling 역할이다.

### 2. 따라서 `highest score wins`는 금지한다
- common-cause나 ambiguity가 높을수록 더 강한 promotion이 아니라 더 강한 hold가 자연스럽다.
- actionability가 높아도 evidence lane이 약하면 top-level promotion을 만들면 안 된다.

## Decision
- BR-030은 아래 순서를 잠근다.
  1. eligible evidence lane selection
  2. hold/reroute cap application
  3. actionability ceiling
  4. explanation-only note attachment

## Next Safe Step
- next safe lane은 둘 중 하나다.
  - BR-028 shortlist를 실제 curated counterexample row로 편입
  - exact missing family (`제어응답형 top1`, `official/current direct overlap`) 추가 수집
- algorithm gating patch는 아직 열지 않는다.
