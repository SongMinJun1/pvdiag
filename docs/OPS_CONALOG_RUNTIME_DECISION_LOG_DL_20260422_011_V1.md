<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_011_V1

## 빠른 요약
| decision_id | status | related_gate | topic | decision | owner | date_decided |
| --- | --- | --- | --- | --- | --- | --- |
| DL-20260422-011 | accepted | Gate 7 | stable/runtime mapping note spec promotion | `mapping note`는 overview note로 유지하고, 별도 `mapping spec`을 normative boundary/mapping contract로 승격한다 | Codex + 사용자 합의 | 2026-04-22 |

## [DL-20260422-011] stable/runtime mapping spec promotion lock
- `status`: accepted
- `date_first_raised`: 2026-04-22
- `date_decided`: 2026-04-22
- `related_gate`: Gate 7
- `owner`: Codex + 사용자 합의
- `related_branch_ids`: []
- `related_parking_ids`: []

### 질문
- `OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md` 를 정식 spec으로 승격할지, 아니면 note로만 유지할지.

### 배경
- [DL-20260422-002](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md) 는 stable/handoff contract와 runtime redesign contract를 별도 계약으로 잠갔다.
- 이후 [OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md) 가 boundary/mapping note 역할을 해 왔고, [DL-20260422-010](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_010_V1.md) 으로 final_delivery 문서군도 이 note의 상세를 복제하지 않는 방향으로 정리됐다.
- 현재는 경계와 최소 대응 관계가 꽤 안정되어, “언제 같은 뜻으로 읽으면 안 되는가”를 normative하게 잠그는 별도 spec이 있어도 되는 단계다.

### 선택지
1. 선택지 A. note만 유지하고 별도 spec은 만들지 않는다
   - 장점:
     - 문서 수가 늘지 않는다.
   - 단점:
     - overview와 normative boundary가 한 문서에 섞여 있어 향후 drift가 생기기 쉽다.
2. 선택지 B. note는 overview로 유지하고, 별도 `mapping spec`을 만들어 normative boundary/mapping contract를 잠근다
   - 장점:
     - 읽기 쉬운 note와 규범 spec의 역할이 분리된다.
     - future build/release/final_delivery 동기화 시 어떤 문서가 우선인지 명확해진다.
   - 단점:
     - 관리해야 할 문서가 하나 늘어난다.
3. 선택지 C. note를 바로 spec으로 rename/대체한다
   - 장점:
     - 단일 문서로 보일 수 있다.
   - 단점:
     - 기존 note를 참조하는 링크가 깨질 수 있다.
     - overview와 normative 내용을 한 문서에 다시 섞게 된다.

### 최종 결정
- 선택지 B를 채택한다.
- 규칙은 아래와 같다.
  1. `OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md` 는 reader-friendly overview note로 유지한다.
  2. 새 `OPS_CONALOG_STABLE_RUNTIME_MAPPING_SPEC_V1.md` 를 normative boundary/mapping contract로 추가한다.
  3. 향후 build/release/final_delivery/stable 문서군과 runtime redesign 문서군의 경계/대응 관계를 잠글 때는 spec을 우선 참조하고, note는 설명용 overview로 둔다.
  4. stable six-field contract 자체나 runtime artifact semantics 자체는 각각 원래 문서가 canonical source이며, spec은 그 둘을 합친 새 계약을 만들지 않는다.

### 이유
- boundary maturity:
  - 이제 stable/runtime 경계는 반복적으로 같은 결론으로 수렴했다.
- 문서 역할 분리:
  - overview note와 normative spec을 분리하면 이후 drift와 오독이 줄어든다.
- 링크 안정성:
  - 기존 note를 유지하면 기존 참조 링크를 깨지 않고도 spec을 도입할 수 있다.

### 허용 패치
- 새 mapping spec 문서 추가
- note 문서에 `overview`, spec 문서에 `normative` 역할을 명시하는 패치
- Gate 7, 상위 로드맵, cross-gate audit에서 pending item을 `spec 승격 완료` 기준으로 갱신하는 패치

### 금지 패치
- stable contract 문서나 runtime contract 문서를 mapping spec으로 대체하는 패치
- mapping spec에서 stable/runtime 개별 계약을 새로운 단일 통합 계약처럼 선언하는 패치
- 기존 note를 rename/삭제해서 참조 링크를 깨뜨리는 패치

### 필요한 문서 업데이트
- [OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md)
- [OPS_CONALOG_STABLE_RUNTIME_MAPPING_SPEC_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_STABLE_RUNTIME_MAPPING_SPEC_V1.md)
- [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)
- [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- [OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md)

### 필요한 코드 업데이트
- 없음

### 검증 계획
- 문서 검증:
  - note/spec 역할이 분리되어 있는지 확인
  - 상위 로드맵과 cross-gate audit의 pending item이 spec 승격 완료 기준으로 갱신됐는지 확인
- 실행 검증:
  - `python -m py_compile pv_ae/panel_day_engine.py`
  - conalog 1회 실행

### 롤백 트리거
- spec이 note보다 더 큰 drift를 만들고, 실제로는 overview 문서만으로 충분하다고 판단되는 경우
- spec이 stable/runtime 개별 canonical source보다 더 강한 단일 계약처럼 오해되는 경우

### 남겨둔 보류 질문
- 없음

### 관련 근거
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_010_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_010_V1.md)
- [OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md)
