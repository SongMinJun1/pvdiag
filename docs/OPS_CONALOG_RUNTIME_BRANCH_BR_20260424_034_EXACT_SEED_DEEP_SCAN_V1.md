<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_034_EXACT_SEED_DEEP_SCAN_V1

## Purpose
- BR-033 이후 다음 우선순위였던 `same-day exact` missing family를 더 깊게 다시 스캔한다.
- 이번 턴의 초점은 두 가지다.
  1. `제어응답형 top1` family가 정말 비어 있는지
  2. `official/current direct overlap`이 artifact date를 넓히면 생기는지

## Scope
- source root:
  - `/private/tmp/conalog_mlpe_seed_expand_check`
- checked artifacts:
  - live-chain heuristics
  - runtime heuristics
  - live-chain cause candidate score breakdown
  - current / precursor / raw-only result tables
  - `data/<site>/out/ae_simple_local_precursor_gate_daily.csv`

## Result
### 1. control-family deep scan
- live-chain heuristics:
  - `제어응답형 top1 = 0`
- runtime heuristics:
  - `제어응답형 top1 = 0`
- score breakdown:
  - `제어응답형 raw_score > 0` panel은 `4개`
  - 그러나 이 점수는 전부 `gpvs_external`, 일부 `gpvs_internal`, `usage` 보조 가산에서만 왔다.
- 대표 예시:
  - `conalog c42997...1.1`
    - top1 `센서·피드백형 7`
    - top2 `접속·부분개방형 6`
    - top3 `제어응답형 4`
  - `gangui bf1a...0.7`
    - top1 `다이오드·서브스트링형 4`
    - top2 `센서·피드백형 4`
    - control score `3`
  - `ktc_ess 70ad...1.4`
    - top1 `열화형 4`
    - top2 `센서·피드백형 4`
    - control score `3`

### 2. same-day direct overlap expanded scan
- direct common-cause flag:
  - `group_off_date`
  - `site_event_soft`
  - `site_event_hard`
- scanned artifact dates:
  - precursor `전조날짜`
  - current `전조날짜`
  - current `고장날짜`
  - raw-only `전조 시작일`
  - raw-only `신호 기준일`
- result:
  - all `0`

## Reading
- `제어응답형`은 지금도 exact family라기보다 supportive hint 에 머문다.
- same-day direct overlap은 artifact date를 넓혀도 생기지 않는다.
- 따라서 BR-034 이후에도 아래 두 family는 그대로 `missing`이다.
  - `제어응답형 top1`
  - `same-day direct overlap with common-cause`

## Next Safe Step
1. exact seed search를 계속 유지
2. near-window backlog나 supportive score를 exact family closure로 읽지 않기
3. raw-only expanded scan은 evidence widening으로만 쓰고, family closure 근거로는 쓰지 않기
