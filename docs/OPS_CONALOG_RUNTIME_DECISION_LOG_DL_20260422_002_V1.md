# OPS Conalog Runtime Decision Log DL-20260422-002 V1

## 빠른 요약
| decision_id | status | related_gate | topic | decision | owner | date_decided |
| --- | --- | --- | --- | --- | --- | --- |
| DL-20260422-002 | accepted | Gate 0 / Gate 5 / cross-gate audit | stable/handoff contract vs runtime redesign contract boundary | 선택지 B 채택: stable/handoff 문서군과 runtime redesign 문서군을 별도 계약으로 둔다 | Codex + 사용자 | 2026-04-22 |

## [DL-20260422-002] stable/handoff contract vs runtime redesign contract boundary
- `status`: accepted
- `date_first_raised`: 2026-04-22
- `date_decided`: 2026-04-22
- `related_gate`: Gate 0 (primary), Gate 5 / cross-gate audit (dependent)
- `owner`: Codex + 사용자
- `related_branch_ids`: []
- `related_parking_ids`: []

### 질문
- `OPS_CONALOG_HANDOFF_PACK_V1.md`, `OPS_CONALOG_RULEBASE_VS_HYBRID_ENGINE_V1.md` 같은 stable/handoff 문서군과
  runtime redesign / gate 문서군을 같은 계약으로 읽을지, 다른 계약으로 읽을지 지금 시점에 어떻게 잠글 것인가.

### 배경
- stable/handoff 문서군은 conalog stable output 또는 stable handoff contract를 설명한다.
  - 예: `패널고장여부_ko`, `사건유형_ko`, `최종고장양상_ko`, `conalog_원인군_ko`
- runtime redesign 문서군은 MLPE runtime/hybrid artifact를 재설계하는 내부 계약을 설명한다.
  - 예: `official current`, `raw-only`, `precursor report`, `raw-only fault signal report`
- 현재 충돌처럼 보이는 지점은 주로 아래다.
  - stable 문서에서는 `사건유형_ko`, `최종고장양상_ko`가 direct operational output처럼 읽힌다.
  - runtime redesign 문서에서는 `event_type`, `terminal_pattern`을 operator-facing headline에서 밀어내고 `operational_state` 중심 current semantics를 잠근다.
- 이 둘이 실제로 같은 계약인데 문서만 어긋난 것인지, 아니면 애초에 서로 다른 층의 계약인지 먼저 결정하지 않으면 이후 패치가 잘못된 층을 덮어쓸 수 있다.

### 선택지
1. 선택지 A. stable/handoff 문서군과 runtime redesign 문서군을 같은 계약으로 본다
   - 장점:
     - 문서 체계가 단순해진다.
     - 사용자 입장에서 하나의 설명 체계로 읽기 쉽다.
   - 단점:
     - stable handoff contract를 runtime redesign semantics에 맞춰 대규모 재작성해야 할 수 있다.
     - 외부 handoff/stable contract와 내부 hybrid redesign을 섞을 위험이 크다.
     - 기존 stable 문서의 의미를 훼손할 수 있다.
2. 선택지 B. stable/handoff 문서군과 runtime redesign 문서군을 별도 계약으로 둔다
   - 장점:
     - stable external contract와 runtime internal/hybrid contract를 분리해 방어할 수 있다.
     - 문서 층 차이 때문에 보이는 충돌을 억지 패치로 덮어쓰지 않게 된다.
     - DL-001의 official/raw-only/operator semantics lock을 runtime redesign 범위에 한정해 해석할 수 있다.
   - 단점:
     - 경계 문구와 cross-reference 문서가 추가로 필요하다.
     - 같은 용어가 층마다 다르게 보일 수 있으므로 glossary/mapping 문서가 더 중요해진다.
3. 선택지 C. stable/handoff 문서를 runtime redesign의 frozen subset projection으로 재정의한다
   - 장점:
     - 장기적으로는 문서 체계를 한 계열로 정리할 수 있다.
     - stable output과 runtime redesign의 매핑 테이블을 명시적으로 만들 수 있다.
   - 단점:
     - 지금 당장 필요한 설계 판단보다 범위가 커진다.
     - projection/mapping spec, validation, 대외 설명 정책까지 한 번에 다시 잠가야 한다.

### 최종 결정
- `선택지 B`를 채택한다.
- 즉, 현재 프로젝트 문서 체계에서는 아래처럼 읽는다.
  1. stable/handoff 문서군은 `stable external contract / conalog direct output` 층이다.
  2. runtime redesign 문서군은 `MLPE runtime/hybrid artifact redesign` 층이다.
  3. 두 문서군 사이에서 같은 용어를 쓰더라도, 자동으로 같은 operator-facing policy를 공유한다고 가정하지 않는다.
  4. 두 문서군을 연결할 때는 `경계 문구` 또는 `mapping note`가 먼저 있어야 한다.
  5. accepted boundary/mapping basis는 [OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md) 를 따른다.

### 채택 근거
- stable/handoff 경로의 대표 entrypoint인 [run_conalog_infer.py](/Users/b9gc/pvdiag/app/run_conalog_infer.py) 는 stable six-field contract를 직접 반환한다.
- runtime redesign / hybrid 경로의 대표 entrypoint인 [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py) 는 `official current`, `precursor`, `raw-only current`, `raw-only fault signal report`, `master/detailed`를 분리한 다중 artifact 계약을 사용한다.
- 따라서 두 경로는 같은 프로젝트 안에 있지만, 동일한 operator-facing projection contract를 공유한다고 보는 것보다 `별도 계약 + boundary/mapping note`로 읽는 편이 실제 코드와 문서 모두에 더 잘 맞는다.

### 이 결정 이후 허용되는 작업
- stable/handoff 문서군과 runtime redesign 문서군의 경계 문구 초안 작성
- Gate 1 glossary에서 `stable path`와 `runtime redesign path`의 용어 충돌 지점 inventory 정리
- stable 문서와 redesign 문서를 연결하는 `boundary/mapping note` 유지 및 후속 정식 spec 필요 여부 검토
- Gate 5 / Gate 4A / Gate 6B가 runtime redesign 범위임을 더 명확히 적는 정합성 패치

### 지금 당장 금지되는 작업
- 별도 결정 없이 stable/handoff 문서를 runtime redesign semantics에 맞춰 덮어쓰는 패치
- runtime redesign 문서를 stable handoff contract의 공식 operator policy로 승격하는 패치
- `사건유형_ko`, `최종고장양상_ko`의 stable contract 의미를 redesign 논리만으로 재정의하는 패치
- stable output contract와 runtime artifact contract를 같은 schema/policy로 전제하는 패치

### 후속 확인 필요 항목
- stable/handoff 문서군에 `runtime redesign 문서와 동일 계약이 아님`을 어느 수준까지 명시할지
- runtime redesign 문서군에서 stable path를 참조할 때 boundary note를 어디까지 반복 표기할지
- `사건유형_ko`, `최종고장양상_ko`를 stable path에서 direct operational fields로 유지하면서도 runtime redesign gate 문서와 충돌 없이 읽히게 하는 방법
- stable path와 runtime redesign path 사이에 공통 glossary만 공유할지, 별도 mapping spec까지 승격할지

### 이 결정이 잠기면 바로 정리할 문서
- [OPS_CONALOG_HANDOFF_PACK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_HANDOFF_PACK_V1.md)
- [OPS_CONALOG_RULEBASE_VS_HYBRID_ENGINE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RULEBASE_VS_HYBRID_ENGINE_V1.md)
- [OPS_CONALOG_RUNTIME_GATE1_GLOSSARY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE1_GLOSSARY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md)

### 검증 계획
- 문서 검증:
  - stable/handoff 문서군과 runtime redesign 문서군의 역할 정의가 서로 침범하지 않는지 확인
  - Gate 1 glossary가 두 경로를 같은 계약처럼 적지 않는지 확인
- 용어 검증:
  - `사건유형`, `최종고장양상`, `official current`, `raw-only fault signal report`가 층별로 다르게 쓰이는 경우 mapping note가 필요한지 확인
- 구현 영향 검증:
  - 이 결정이 실제 runtime code patch를 바로 요구하는지 여부 확인
  - release/handoff 문서만 바꿔도 되는지, 별도 mapping artifact가 필요한지 판단

### 롤백 트리거
- stable/handoff 문서군과 runtime redesign 문서군이 실제로 동일한 operator contract를 설명한다는 강한 근거가 새로 확보되는 경우
- stable external consumer가 runtime redesign semantics와 동일한 headline policy를 요구하는 경우
- boundary 분리보다 mapping 통합이 유지보수 비용을 더 줄인다는 근거가 생기는 경우

### 남겨둔 보류 질문
- stable/handoff 문서군과 runtime redesign 문서군 사이에 별도 `mapping spec`을 만들 것인가
- stable path의 `사건유형_ko`, `최종고장양상_ko`를 redesign 쪽 `event_type`, `terminal_pattern`과 어떤 수준으로 연결할 것인가
- Gate 1 glossary를 공용 glossary로 유지할지, stable/runtime로 분리할지

### 관련 근거
- [OPS_CONALOG_HANDOFF_PACK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_HANDOFF_PACK_V1.md)
- [OPS_CONALOG_RULEBASE_VS_HYBRID_ENGINE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RULEBASE_VS_HYBRID_ENGINE_V1.md)
- [OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md)
- [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- [OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md)
- [OPS_CONALOG_RUNTIME_GATE1_GLOSSARY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE1_GLOSSARY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1.md)
