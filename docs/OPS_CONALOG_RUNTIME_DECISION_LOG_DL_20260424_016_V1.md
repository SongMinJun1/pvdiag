<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_016_V1

## Decision
- `제어응답형` raw score가 존재하더라도, 그것만으로 `제어응답형 top1 family`가 확보된 것으로 읽지 않는다.
- `same-day direct overlap`은 official/current/precursor 뿐 아니라 raw-only artifact 날짜까지 넓혀도 `0`이면, 여전히 `missing family`로 둔다.

## Evidence
- BR-034 deep scan 기준:
  - live-chain heuristics에서 `제어응답형 top1 = 0`
  - runtime heuristics에서도 `제어응답형 top1 = 0`
  - live-chain score breakdown에서 `제어응답형 raw_score > 0` panel은 `4개`
    - `conalog c42997...1.1 = 4`
    - `gangui bf1a...0.7 = 3`
    - `gangui bf1a...2.16 = 3`
    - `ktc_ess 70ad...1.4 = 3`
  - 위 점수는 전부 `gpvs_external`, 일부 `gpvs_internal`, `usage` 보조 가산에서만 왔다.
  - same-day direct overlap expanded scan:
    - precursor `전조날짜` vs direct common-cause flag: `0`
    - current `전조날짜` vs direct common-cause flag: `0`
    - current `고장날짜` vs direct common-cause flag: `0`
    - raw-only `전조 시작일` vs direct common-cause flag: `0`
    - raw-only `신호 기준일` vs direct common-cause flag: `0`

## Reading
- 현재 `제어응답형`은 exact family라기보다 `supportive hint` 수준이다.
- current/precursor/raw-only 모든 artifact date를 넓혀도 same-day direct overlap이 없으므로, common-cause exact family도 계속 비어 있다.

## Consequence
- 다음 patch gate에서는 아래를 금지한다.
  - `control_score > 0` 를 `제어응답형 top1 family 확보`로 읽는 것
  - raw-only artifact date expanded scan을 이유로 `same-day direct overlap family 확보`라고 읽는 것
- 다음 안전 작업은 계속 exact seed search다.
