# OPS Conalog Runtime Branch & Parking-Lot Template V1

## 1. 목적
- 본 문서는 메인 로드맵 진행 중 생기는 가지(branch)와 보류 항목(parking lot)을 관리하기 위한 템플릿이다.
- 목적은 메인 라인을 흔들지 않으면서도 중요한 예외와 질문을 잊지 않고 추적하는 것이다.

## 2. 언제 브랜치를 여는가
- 아래 상황이면 브랜치를 연다.
  - 정의 충돌이 생김
  - 신호 역할이 애매함
  - 특정 site 예외가 전역 규칙을 흔듦
  - 성능 회귀가 의심됨
  - report wording이 의미를 왜곡함
  - 스코프 밖 요구가 다시 들어옴

## 3. 브랜치 유형
- `A. 정의 충돌`
- `B. 신호 역할 충돌`
- `C. 사이트 특수 케이스`
- `D. 성능/평가 회귀`
- `E. 리포트/표현 충돌`
- `F. 범위 확장`

## 4. 브랜치 ID 규칙
- 권장 포맷:
  - `BR-YYYYMMDD-001`
  - 예: `BR-20260421-001`

## 5. 파킹 로트 ID 규칙
- 권장 포맷:
  - `PL-YYYYMMDD-001`
  - 예: `PL-20260421-001`

## 6. 브랜치 항목 템플릿
```md
## [BR-YYYYMMDD-001] 브랜치 제목
- `status`: open | analyzing | waiting | resolved | merged_back | converted_to_parking
- `branch_type`: A | B | C | D | E | F
- `current_gate`: Gate 0 | Gate 1 | Gate 2 | Gate 2A | Gate 2B | Gate 3 | Gate 4 | Gate 4A | Gate 5 | Gate 6A | Gate 6B | Gate 7
- `return_gate`: Gate 0 | Gate 1 | Gate 2 | Gate 2A | Gate 2B | Gate 3 | Gate 4 | Gate 4A | Gate 5 | Gate 6A | Gate 6B | Gate 7
- `owner`: 이름/역할
- `created_at`: YYYY-MM-DD
- `target_review_date`: YYYY-MM-DD

### 이슈 요약
- 무엇이 메인 라인을 흔들었는지 적는다.

### 왜 브랜치인가
- 왜 지금 메인 라인에서 바로 결론내면 안 되는지 적는다.

### 허용 작업
- 지금 이 브랜치 안에서 해도 되는 것만 적는다.

### 금지 작업
- 이 브랜치에서 하면 안 되는 패치를 적는다.

### 필요한 추가 근거
- 더 모아야 할 데이터 / artifact / 사례를 적는다.

### 잠정 판단
- 현재까지의 임시 판단을 적는다.

### 복귀 조건
- 무엇이 충족되면 메인 라인으로 돌아갈지 적는다.

### 관련 문서/결정
- decision log ID, 관련 Gate 문서, 관련 artifact를 적는다.
```

## 7. 파킹 로트 항목 템플릿
```md
## [PL-YYYYMMDD-001] 파킹 항목 제목
- `status`: parked | reopened | resolved | dropped
- `source_branch_id`: BR-...
- `related_gate`: Gate 0 | Gate 1 | Gate 2 | Gate 2A | Gate 2B | Gate 3 | Gate 4 | Gate 4A | Gate 5 | Gate 6A | Gate 6B | Gate 7
- `owner`: 이름/역할
- `created_at`: YYYY-MM-DD
- `review_after`: YYYY-MM-DD or 조건

### 보류 이유
- 왜 지금은 풀지 않는지 적는다.

### 현재 위험도
- low | medium | high

### 지금 허용되는 최소 조치
- 지금 당장 할 수 있는 안전 조치를 적는다.

### 다시 열 조건
- 어떤 상황이 오면 다시 꺼내야 하는지 적는다.

### 예상 복귀 지점
- 다시 열면 어느 Gate부터 봐야 하는지 적는다.

### 관련 근거
- 관련 branch / decision / artifact / meeting note를 적는다.
```

## 8. 빠른 요약 표 템플릿
### 8.1 열린 브랜치
| branch_id | status | type | current_gate | return_gate | title | owner |
| --- | --- | --- | --- | --- | --- | --- |
| BR-YYYYMMDD-001 | open | B | Gate 2A | Gate 2A | TODO | TODO |

### 8.2 파킹 로트
| parking_id | status | related_gate | title | risk | review_after | owner |
| --- | --- | --- | --- | --- | --- | --- |
| PL-YYYYMMDD-001 | parked | Gate 6B | TODO | medium | YYYY-MM-DD | TODO |

## 9. 운영 규칙
- 브랜치를 열면 반드시 `return_gate`를 적는다.
- 브랜치에서 바로 코드 패치로 점프하지 않는다.
- 파킹 로트는 브랜치보다 한 단계 더 느린 보류 상태다.
- 브랜치가 3개 이상 동시에 열리면 메인 라인 진행을 잠시 멈추고 상위 Gate를 재점검한다.
- 브랜치가 resolved 되면 decision log에 어떤 결론이 남았는지 연결한다.

## 10. 첫 사용 권장 브랜치
- `vdrop` 역할 충돌 브랜치
- `fault_like_day` 역할 충돌 브랜치
- gangui site 특수 패턴 브랜치
- raw-only vs official current 혼선 브랜치
- precursor false positive 증가 브랜치
