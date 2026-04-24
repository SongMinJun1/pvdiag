<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_017_V1

## Decision
- raw-daily `same-day direct common-cause row`가 존재하더라도, 그것만으로 `report-layer exact family`가 확보된 것으로 읽지 않는다.
- 앞으로 `same-day exact direct overlap` family 탐색은 `row 존재 여부`보다 `artifact-date coincidence`와 `report-lane entry`를 함께 본다.

## Evidence
- BR-035 blocker anatomy scan 기준:
  - direct common-cause same-day raw-daily rows with signal strength:
    - `101 rows`
    - `49 panels`
  - site split:
    - `gangui = 71`
    - `ktc_ess = 30`
  - top-level artifact presence by panel:
    - `precursor = 19`
    - `rawonly = 16`
    - `none = 13`
    - `current = 1`
  - only `1` current panel exists:
    - `ktc_ess 10305...2.12`
    - nearest current `고장날짜` gap `71일`
- 따라서 current missing family의 핵심 blocker는 `raw-daily row absence`가 아니라 `report-lane entry/date alignment failure`다.

## Reading
- `group_off_date` exact rows는 주로 `rawonly`로 흘러간다.
- `site_event` exact rows는 주로 `precursor` 또는 `none`에 머문다.
- 즉 current/official direct-overlap family는 아직 비어 있지만, 그 이유는 `top-level row universe mismatch`와 `summary date displacement`가 더 크다.

## Consequence
- 다음 exact seed search에서는 아래를 먼저 분리해 본다.
  1. raw-daily exact row가 있지만 report-lane에 안 들어오는 패널
  2. report-lane에는 들어왔지만 summary date가 exact date와 어긋나는 패널
  3. native signal이 부족해 control top1까지 못 올라가는 패널
- 따라서 raw-daily same-day row는 `candidate reservoir`이지, 곧바로 `exact family closure`는 아니다.
