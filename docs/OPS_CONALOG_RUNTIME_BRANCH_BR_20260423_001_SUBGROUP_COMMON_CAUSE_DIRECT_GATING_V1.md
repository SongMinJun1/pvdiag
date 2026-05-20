<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_001_SUBGROUP_COMMON_CAUSE_DIRECT_GATING_V1

## [BR-20260423-001] subgroup common-cause direct gating
- `status`: analyzing
- `branch_type`: B
- `current_gate`: Gate 3
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23
- `target_review_date`: 2026-04-24

## 1. 이슈 요약
- 현재 runtime redesign는 `site_event/group_off` 기반 common-cause와 `subgroup_common_cause_candidate` shadow evidence를 함께 다루기 시작했다.
- 그러나 `subgroup common-cause`는 아직 direct gating/onset 보정으로는 올리지 않고, shadow / audit / explanation 축에서만 쓰고 있다.
- 이 branch의 질문은 단순하다.
  - `subgroup common-cause`를 direct gating까지 올릴 만큼 근거가 충분한가
  - 아니면 계속 shadow evidence로만 두어야 하는가

## 2. 왜 브랜치인가
- 이 질문을 메인 라인에서 바로 rule patch로 처리하면 아래 셋이 동시에 흔들린다.
  - precursor eligibility
  - common-cause 해석
  - onset backdating
- 특히 `prefault_B_effective`, `retrospective_onset`, `공통원인이력_flag`가 한 번에 얽혀 있어서, 지금 direct gating으로 점프하면 결과 의미를 잃기 쉽다.

## 3. 현재까지의 근거

### 3.1 shadow evidence는 유효하다
- `subgroup_common_cause_candidate` shadow evidence를 추가한 뒤, broad history 기준 `공통원인이력_flag`가 실제 runtime verdict에 채워지기 시작했다.
- 이전처럼 `0` 고정이던 상태보다는 훨씬 낫다.

### 3.2 broad history는 너무 넓다
- broad `공통원인이력_flag`는 single-site conalog 확인 기준 `196 / 349`까지 올라가 넓은 이력 보존엔 유용하지만, 대표 해석 flag로는 과하다.
- 그래서 broad history와 proximal common-cause를 분리했다.

### 3.3 proximal 분리는 유효하다
- `trigger_proximal_common_cause_flag`: `78 / 349`
- 이 중
  - `strict_trigger_proximal_common_cause_flag`: `64`
  - `warning_proximal_common_cause_flag`: `14`
- 현재 확인 기준으로:
  - `strict`는 고장 패널 쪽에만 붙는다.
  - `warning`은 미확정 꼬리에만 남는다.
- 이 결과 때문에 current surface에는 `strict`만 올리고, `warning`은 audit 전용으로 두고 있다.

### 3.4 direct gating까지 올릴 근거는 아직 부족하다
- 2026-04-23 tri-site(`conalog/gangui/ktc_ess`) 기준으로, 현재 `subgroup_common_cause_candidate`를 가정상 direct suppress에 사용해도 결과는 아래 정도만 변했다.
  - `conalog`: `prefault_B_effective 1077 -> 1077`, `local_precursor_any 2197 -> 2197`, future final-fault coverage `5 -> 5`, official current 근접 overlap `0 / 2`
  - `gangui`: `prefault_B_effective 407 -> 406`, `local_precursor_any 874 -> 874`, future final-fault coverage `5 -> 5`, official current 근접 overlap `0 / 2`
  - `ktc_ess`: `prefault_B_effective 598 -> 562`, `local_precursor_any 1771 -> 1762`, future final-fault coverage `1 -> 1`, official current 근접 overlap `0 / 2`
- 전체 합계로는:
  - `prefault_B_effective` row `37`개 제거
  - `local_precursor_any` row `9`개 제거
  - future final-fault coverage 손실 `0`
  - official current 근접 overlap `0 / 6`
- 즉 이 branch의 첫 tri-site 비교표 기준으로는, subgroup suppress가 `ktc_ess` 쪽 일부 row 정리에는 도움을 주지만, 아직은 `직접 억제해야만 하는 강한 current-side 근거`까지는 보여주지 않았다.
- 반대로 panel-level future fault coverage를 잃지 않았다는 점은 긍정적이지만, 이 표본만으로 바로 direct gating rule을 잠그기엔 여전히 이르다.

### 3.5 첫 비교표만으로는 아직 부족하다
- tri-site raw vs effective 확인 기준에서 `prefault_B_effective`는 panel-level early capture를 끊지 않았고, common-cause 겹침 row만 정리하는 역할에 가깝게 보였다.
- 하지만 `subgroup common-cause`를 direct gating으로 올렸을 때 false positive가 실제로 얼마나 줄고, 어떤 true positive를 같이 잃는지는 아직 branch 수준의 비교표가 더 필요하다.

### 3.6 site-wide와 subgroup common-cause는 성격이 다르다
- `ktc_ess 2025-10-25~27`처럼 `co_drop_surge` 기반 site-wide cluster는 상대적으로 분명하다.
- 반면 `ktc_ess 2025-05-09`처럼 `site_event=0`인데 두 subgroup에서 같이 눌린 날은 subgroup/common-cause 후보로 볼 여지가 있지만, 아직 direct suppress 근거로는 부족하다.

## 4. 지금 메인 라인에서 허용되는 것
- subgroup shadow evidence 유지
- broad / proximal / strict / warning 분리 유지
- `group root / subgroup base / subgroup cluster` 같은 surface 해석 보조값 유지
- `공통원인이력_flag`와 audit common-cause flag를 비교하는 분석 유지
- A/B 비교표 작성

## 5. 지금 메인 라인에서 금지되는 것
- `subgroup_common_cause_candidate`를 direct precursor gating 규칙으로 즉시 승격
- `prefault_B_effective`에 subgroup suppress를 바로 추가
- `retrospective_onset` fallback을 subgroup common-cause와 결합해 즉시 수정
- official current / operator surface를 subgroup common-cause 기준으로 직접 승격/강등

## 6. 필요한 추가 근거
- tri-site 기준 subgroup direct gating 가정 하에서:
  - precursor row 수 변화
  - future final-fault coverage 변화
  - official current 영향
  - false positive 정리량
- 위 첫 비교표에서는 `future final-fault coverage 손실 0`, `official current 근접 overlap 0/6`까지는 확인됐고, 다음엔 실제 false positive 정리량과 site별 편중(`ktc_ess` 집중 여부)을 더 봐야 한다.
- site-wide common-cause와 subgroup common-cause가 실제로 충분히 분리되는지
- subgroup common-cause가 onset backdating 과민을 줄이는지

## 7. 잠정 판단
- `subgroup common-cause`는 shadow / audit / explanation에는 이미 충분히 가치가 있다.
- direct gating으로는 아직 이르다.
- 현재까지의 tri-site 비교표는 “직접 올리면 큰 손실이 날 것 같진 않다”까지는 보여주지만, “지금 바로 direct gating으로 올리는 게 더 낫다”까지는 아직 못 보여준다.
- 따라서 현재 branch의 기본 방향은:
  - **지금은 보이게 만들고, 비교표를 더 쌓고, 마지막에만 gating 여부를 결정한다**.

## 8. 복귀 조건
- subgroup shadow flag 전후 A/B 비교표 1회 이상 확보
- official current / precursor와의 direct overlap 여부 재확인
- direct gating을 올릴지 말지 decision log 초안 작성 가능 수준까지 근거 축소

## 9. 관련 문서/결정
- [OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md)
- [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)
- [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md)
- [OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md)
- [OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md)
