<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_020_V1

## Decision
- 현재 Gate 7의 patch 방향은 `algorithm-first`가 아니라 `evidence-role-first -> blocker-split-first -> algorithm-last`로 유지한다.
- 이유는 현재까지 확보된 근거가 `exact_family_closure`보다 아래 급에 더 많이 분포하기 때문이다.
- 따라서 아래 셋은 계속 분리해서 읽는다.
  - `exact_family_closure`
  - `supportive_hint / candidate_reservoir / non_closing_backlog`
  - `structural_blocker`
- 위 분리가 잠기기 전에는 threshold/rule patch를 넣지 않는다.

## Evidence
- BR-033:
  - widened near-window overlap backlog
  - `5 report rows / 4 roots`
  - mixed flag family, mixed slice, mixed sign
  - reading: `non_closing_backlog`
- BR-034:
  - `제어응답형 top1 = 0`
  - `control_score > 0` panels `4`
  - reading: `supportive_hint`
- BR-035:
  - raw-daily same-day direct common-cause rows `101 rows / 49 panels`
  - report-layer exact family still empty
  - reading: `candidate_reservoir + structural_blocker`
- BR-037:
  - `group_off_date` family splits into
    - `no_report_lane_entry`
    - `precursor_carryover_without_exact_overlap`
    - `rawonly_date_displaced`
    - `rawonly_near_signal_anchor`
  - current exact closure `0`

## Reading
- 지금 evidence는 “rule을 바로 바꿀 만큼 exact가 충분하다”보다,
  - `무엇이 exact가 아닌지`
  - `왜 report-layer exact로 못 올라오는지`
  - `어디를 next blocker inspect target으로 삼아야 하는지`
  를 더 잘 설명한다.
- 즉 지금 방향은 보수적이라서 느린 것이 아니라, 현재 evidence의 급에 맞는 순서를 따르는 것이다.

## Consequence
- 다음 patch justification은 아래 둘 중 하나여야 한다.
  1. `exact_family_closure`가 실제로 생김
  2. `structural_blocker`가 충분히 분해돼서 특정 patch target이 명확해짐
- 그 전까지는 docs/evidence-first lane을 유지한다.
