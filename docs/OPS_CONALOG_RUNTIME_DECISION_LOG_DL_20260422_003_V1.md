# OPS Conalog Runtime Decision Log DL-20260422-003 V1

## 빠른 요약
| decision_id | status | related_gate | topic | decision | owner | date_decided |
| --- | --- | --- | --- | --- | --- | --- |
| DL-20260422-003 | accepted | Gate 0 / Gate 7 | minimal stable/handoff boundary note patch scope | stable/handoff 문서군에는 `별도 계약` 경계 문구만 최소 수준으로 넣고, 필드 의미 재정의는 하지 않는다 | Codex + 사용자 | 2026-04-22 |

## [DL-20260422-003] minimal stable/handoff boundary note patch scope
- `status`: accepted
- `date_first_raised`: 2026-04-22
- `date_decided`: 2026-04-22
- `related_gate`: Gate 0 (primary), Gate 7 (dependent)
- `owner`: Codex + 사용자
- `related_branch_ids`: []
- `related_parking_ids`: []

### 질문
- stable/handoff 문서군에 runtime redesign와의 경계 문구를 어디까지 넣을 것인가.

### 배경
- [DL-20260422-002](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md) 에서 stable/handoff contract와 runtime redesign contract를 별도 계약으로 잠갔다.
- 하지만 stable 문서군인 [OPS_CONALOG_HANDOFF_PACK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_HANDOFF_PACK_V1.md), [OPS_CONALOG_RULEBASE_VS_HYBRID_ENGINE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RULEBASE_VS_HYBRID_ENGINE_V1.md) 에는 아직 그 경계가 직접 적혀 있지 않다.
- 이 상태로 두면 runtime redesign 문서만 읽은 사람이 stable 문서도 같은 operator-facing policy를 따른다고 오해할 수 있다.

### 선택지
1. 선택지 A. stable 문서군은 그대로 두고 runtime redesign 문서에서만 경계를 설명한다
   - 장점:
     - stable 문서를 건드리지 않아도 된다.
   - 단점:
     - stable 문서를 단독으로 읽는 사람은 여전히 경계를 모를 수 있다.
2. 선택지 B. stable 문서군에 최소 boundary note만 넣고, 필드 의미나 schema는 바꾸지 않는다
   - 장점:
     - 오해를 줄이면서 stable contract 자체는 건드리지 않는다.
     - runtime redesign semantics를 stable path에 덮어쓰지 않는다.
   - 단점:
     - 문서 길이가 조금 늘어난다.
3. 선택지 C. stable 문서군을 runtime redesign wording에 맞춰 재서술한다
   - 장점:
     - 표면상 용어가 더 통일될 수 있다.
   - 단점:
     - stable contract 의미를 불필요하게 흔들 수 있다.
     - DL-002가 금지한 층 혼합에 가깝다.

### 최종 결정
- `선택지 B`를 채택한다.
- stable/handoff 문서군에는 아래만 허용한다.
  1. `runtime redesign 문서와 동일 계약이 아니다`라는 경계 문구
  2. stable/handoff는 direct output contract, runtime redesign는 내부/hybrid artifact contract라는 설명
  3. 필요 시 [OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md) 링크
- 아래는 허용하지 않는다.
  1. stable six-field contract의 필드 의미 재정의
  2. `사건유형_ko`, `최종고장양상_ko`를 runtime redesign operator headline 정책으로 교정하는 문구
  3. stable output artifact 이름/역할/schema 변경

### 이유
- 정의 일관성:
  - DL-002의 별도 계약 원칙을 가장 보수적으로 반영한다.
- 운영자 해석 가능성:
  - stable 문서를 단독으로 읽어도 runtime redesign와 같은 층이 아니라는 점을 알 수 있다.
- downstream artifact 영향:
  - stable contract와 runtime redesign artifact를 불필요하게 섞지 않는다.

### 허용 패치
- stable 문서 상단 또는 목적 근처에 boundary note 추가
- stable 문서에서 mapping note 참조 링크 추가
- stable path / runtime redesign path 구분을 한두 문장으로 명시

### 금지 패치
- stable 문서의 6개 계약 필드 의미를 runtime redesign semantics에 맞춰 다시 쓰는 패치
- stable 문서에 raw-only / precursor / official current artifact 정책을 직접 끌어오는 패치
- stable artifact/schema 이름 변경

### 필요한 문서 업데이트
- [OPS_CONALOG_HANDOFF_PACK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_HANDOFF_PACK_V1.md)
- [OPS_CONALOG_RULEBASE_VS_HYBRID_ENGINE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RULEBASE_VS_HYBRID_ENGINE_V1.md)
- [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- [OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md)

### 필요한 코드 업데이트
- 없음

### 검증 계획
- stable 문서를 단독으로 읽어도 `runtime redesign와 같은 계약이 아니다`가 드러나는지 확인
- stable 문서의 six-field contract 설명이 변형되지 않았는지 확인
- runtime redesign 문서와 경계가 모순 없이 맞물리는지 확인

### 롤백 트리거
- stable external consumer가 경계 문구 없이 더 단순한 문서를 요구하는 경우
- boundary note가 stable contract 의미를 흐린다는 명확한 피드백이 생기는 경우

### 관련 근거
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md)
- [OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md)
- [OPS_CONALOG_HANDOFF_PACK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_HANDOFF_PACK_V1.md)
- [OPS_CONALOG_RULEBASE_VS_HYBRID_ENGINE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RULEBASE_VS_HYBRID_ENGINE_V1.md)
