# OPS Conalog Runtime Decision Log Template V1

## 1. 목적
- 본 문서는 `conalog` MLPE runtime redesign 과정에서 중요한 설계 결정을 기록하기 위한 템플릿이다.
- 같은 논의를 반복하지 않고, 나중에 “왜 이렇게 정했는가”를 설명할 수 있게 하는 것이 목적이다.
- 이 문서는 구현 로그가 아니라 `설계 의사결정 로그`다.

## 2. 언제 기록하는가
- 아래 중 하나에 해당하면 decision log에 남긴다.
  - Gate 통과 조건을 실제로 잠그는 결정
  - precursor / hard evidence 경계를 바꾸는 결정
  - artifact 역할을 바꾸는 결정
  - raw-only / official current 관계를 바꾸는 결정
  - taxonomy / action 연결 정책을 바꾸는 결정
  - 기존 결정을 supersede 하는 결정

## 3. 상태 규칙
- `proposed`
  - 질문은 정의됐지만 아직 채택되지 않은 상태
- `accepted`
  - 현재 메인 라인에서 채택된 상태
- `superseded`
  - 후속 결정이 기존 결정을 대체한 상태
- `rejected`
  - 검토했지만 채택하지 않기로 한 상태
- `parked`
  - 질문은 중요하지만 지금 단계에서 잠그지 않기로 한 상태

## 4. ID 규칙
- 권장 포맷:
  - `DL-YYYYMMDD-001`
  - 예: `DL-20260421-001`
- 브랜치/파킹 로트와 연결할 때는 관련 ID를 함께 기록한다.

## 5. 한 항목 작성 템플릿
```md
## [DL-YYYYMMDD-001] 결정 제목
- `status`: proposed | accepted | superseded | rejected | parked
- `date_first_raised`: YYYY-MM-DD
- `date_decided`: YYYY-MM-DD
- `related_gate`: Gate 0 | Gate 1 | Gate 2 | Gate 2A | Gate 2B | Gate 3 | Gate 4 | Gate 4A | Gate 5 | Gate 6A | Gate 6B | Gate 7
- `owner`: 이름/역할
- `related_branch_ids`: [BR-...]
- `related_parking_ids`: [PL-...]

### 질문
- 이번에 실제로 잠가야 하는 질문을 한 문장으로 적는다.

### 배경
- 왜 이 결정을 지금 내려야 하는지 적는다.
- 어떤 artifact / code path / stakeholder에 영향을 주는지 적는다.

### 선택지
1. 선택지 A
   - 장점:
   - 단점:
2. 선택지 B
   - 장점:
   - 단점:
3. 선택지 C
   - 장점:
   - 단점:

### 최종 결정
- 채택한 선택지를 한 문장 규칙으로 적는다.

### 이유
- 왜 그렇게 정했는지 적는다.
- 가능하면 다음 축을 함께 쓴다.
  - 정의 일관성
  - MLPE 해석 적합성
  - 운영자 해석 가능성
  - false positive / false negative 비용
  - downstream artifact 영향

### 허용 패치
- 이 결정 이후 바로 허용되는 패치를 적는다.

### 금지 패치
- 아직 허용되지 않는 패치를 적는다.

### 필요한 문서 업데이트
- 갱신해야 할 문서를 적는다.

### 필요한 코드 업데이트
- 후속으로 갱신해야 할 코드/스크립트를 적는다.

### 검증 계획
- 어떤 slice / 반례 / smoke / run으로 검증할지 적는다.

### 롤백 트리거
- 무엇이 발생하면 이 결정을 다시 열어야 하는지 적는다.

### 관련 근거
- 회의록 / 상세 문서 / 분석 결과 / artifact 경로를 적는다.
```

## 6. 빠른 요약 표 템플릿
| decision_id | status | related_gate | topic | decision | owner | date_decided |
| --- | --- | --- | --- | --- | --- | --- |
| DL-YYYYMMDD-001 | proposed | Gate 2A | evidence rule | TODO | TODO | YYYY-MM-DD |

## 7. 실제 운영 규칙
- `accepted`가 되기 전까지는 구현 패치를 최소화한다.
- `superseded`가 되면 예전 결정을 지우지 말고 상태만 바꾼다.
- 설계 결정을 바꿨는데 decision log를 안 남기면 문서 부채로 본다.
- 한 decision은 가능하면 한 Gate만 주로 담당하게 한다.

## 8. 첫 사용 권장 항목
- precursor 정의
- hard evidence 정의
- `fault_like_day`의 역할
- `vdrop` 노출 정책
- raw-only fault signal report의 운영자 직접 노출 범위
- official current와 raw-only current의 관계
