<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_032_NEAR_WINDOW_BACKLOG_DOC_SYNC_V1

## Purpose
- BR-031 이후 문서 체인을 다시 검토해 `same-day exact missing family`와 widened `±7일 near-window backlog`가 patch gate 문서에서 섞여 읽히지 않도록 정리한다.
- 이번 단계는 docs-only sync 이며, runtime rule / threshold / row universe / operator-facing semantics는 건드리지 않는다.

## Review Finding
- BR-031 note와 active register에는 `near-window backlog`가 이미 기록돼 있다.
- 하지만 regression checklist와 Gate 7 implementation order는 아직 `exact same-day family` 수집 우선순위만 중심으로 남아 있어, 다음 알고리즘 턴에서 `near-window overlap`을 `exact family closure`처럼 읽을 여지가 있었다.

## Applied Sync
- `counterexample regression checklist`
  - `near-window backlog`를 `same-day exact family closure`로 읽지 말아야 한다는 금지 문구 추가
  - current collection priority를 `same-day exact`와 `near-window backlog`로 분리
- `Gate 7 implementation order`
  - BR-031 이후 남은 조건에 `near-window backlog` 분류 필요를 추가
  - algorithm gating patch 선행 조건에 backlog 해석 잠금 필요를 추가
  - 현재 우선순위를 BR-031 이후 상태에 맞게 갱신
- `counterexample set`
  - common-cause 수집 과제를 `same-day exact`와 `near-window backlog 분류 결정`으로 분리

## Locked Reading
- BR-031 widened `±7일 near-window overlap backlog`는 실제로 존재한다.
- 그러나 이는 아직 `same-day exact missing family closure`가 아니다.
- 따라서 다음 알고리즘 패치에서 near-window backlog를 common-cause overlap family의 exact precedent로 바로 대체하면 안 된다.

## Next Safe Step
1. `near-window overlap backlog`를 separate provisional family로 둘지 결정
2. 동시에 `제어응답형 top1`, `official/current direct overlap` 같은 `same-day exact` missing family search를 계속 유지
3. 그 뒤에 algorithm gating patch를 다시 검토
