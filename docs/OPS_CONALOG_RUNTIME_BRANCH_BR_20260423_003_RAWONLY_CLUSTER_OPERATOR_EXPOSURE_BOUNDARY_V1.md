<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_003_RAWONLY_CLUSTER_OPERATOR_EXPOSURE_BOUNDARY_V1

## [BR-20260423-003] raw-only cluster/operator exposure boundary
- `status`: analyzing
- `branch_type`: E
- `current_gate`: Gate 5
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23
- `target_review_date`: 2026-04-24

## 1. 이슈 요약
- raw-only fault signal 표면은 처음엔 `row count`만 보여서 `72 rows = 72 incidents`처럼 읽히기 쉬웠다.
- 이후 `group root`, `subgroup base`, `subgroup cluster`까지 보조축을 추가했지만, 여전히 이 값들을 어디까지 operator-facing으로 올릴지 경계가 필요하다.

## 2. 왜 브랜치인가
- report surface wording은 단순 표현 문제가 아니라, 사용자가 무엇을 “사건 수”로 오해하는지와 바로 연결된다.
- 이걸 메인 라인에서 과하게 밀어붙이면 raw-only analyst artifact가 official current처럼 읽힐 위험이 있다.

## 3. 현재까지의 근거

### 3.1 row count만으로는 충분히 헷갈린다
- `conalog` 단일 실행에서 `raw-only fault signal row_count = 72`가 보였고, 이 값은 직관적으로 독립 incident 수처럼 읽히기 쉬웠다.
- 실제로는 clustered panel row가 많이 포함돼 있었다.

### 3.2 group root / subgroup base 분리는 유효하다
- `group root`와 `subgroup base`를 분리한 뒤:
  - `72 rows`
  - `7 group roots`
  - `15 subgroup bases`
  로 읽을 수 있게 되었다.
- 이 단계만으로도 `72건` 과대 해석은 많이 줄었다.

### 3.3 subgroup cluster도 해석에는 도움이 된다
- 추가로 `subgroup cluster`를 넣은 뒤:
  - `72 rows`
  - `15 subgroup bases`
  - `17 subgroup clusters`
  로 보이게 됐다.
- cluster는 “확정 incident count”는 아니지만, analyst/support가 row 수와 사건 뭉치를 분리해서 보는 데는 유용하다.

### 3.4 하지만 cluster를 official incident처럼 부르면 안 된다
- 현재 cluster는 `같은 subgroup base 안에서 신호 기준일 간격이 3일 이하인 row`를 묶은 휴리스틱이다.
- 즉 이것은 사고/장애 incident를 확정하는 canonical rule이 아니라, 읽기 쉬운 보조 요약값이다.

### 3.5 operator-facing까지 올릴지 여부는 아직 열려 있다
- 지금 기준으로는:
  - raw-only fault signal report
  - master report 보조 요약
  - detailed definitions
  까지는 cluster를 보여줘도 괜찮다.
- 하지만 official current/operator headline에까지 올리면 사건 수처럼 과대 해석될 여지가 있다.

## 4. 지금 메인 라인에서 허용되는 것
- `group root / subgroup base / subgroup cluster` 보조축 유지
- master report / definitions 보강
- row 수와 cluster 수를 함께 표기
- analyst/support 보조표에서 cluster 휴리스틱을 설명

## 5. 지금 메인 라인에서 금지되는 것
- cluster를 incident 확정 count처럼 표기
- raw-only fault signal을 official current처럼 승격
- operator-facing current headline에 cluster 휴리스틱을 직접 노출

## 6. 필요한 추가 근거
- cluster 휴리스틱이 실제 analyst reading에 얼마나 도움이 되는지
- cluster를 master report까지만 두는 게 적절한지, 아니면 analyst raw-only 표에만 두는 게 맞는지
- operator 문서에서 cluster까지 보이는 것이 혼선을 줄이는지 늘리는지

## 7. 잠정 판단
- `group root / subgroup base / subgroup cluster` 분리는 메인 라인에서도 유효하다.
- 다만 cluster는 현재 **analyst/support 보조값**으로만 읽어야 안전하다.
- 따라서 이 branch의 기본 방향은:
  - **cluster는 보이되, canonical incident semantics로 승격하지 않는다**.

## 8. 복귀 조건
- cluster 표면의 역할을 `analyst only` 또는 `master report 보조` 중 하나로 더 명확히 잠금
- 필요 시 별도 decision log 또는 Gate 5 보강 문서 작성

## 9. 관련 문서/결정
- [OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md)
- [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_008_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_008_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_009_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_009_V1.md)
