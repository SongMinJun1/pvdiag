<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_031_CURATED_SEED_PROMOTION_AND_GAP_RESCAN_V1

## Purpose
- Execute both safe evidence tasks after BR-030 in one docs-only branch.
  - Promote selected BR-028 provisional shortlist rows into actual curated counterexample rows
  - Re-scan the still-missing exact families with a widened search window

## Scope
- source roots:
  - `/private/tmp/conalog_mlpe_seed_expand_check`
- touched docs:
  - [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md)
  - [OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md)

## Result
### 1. provisional shortlist -> actual curated rows
- 아래 row를 curated counterexample rows로 편입했다.
  - `MLP-007` `conalog c42997a6-...1.1`
  - `MLP-008` `gangui bf1a912f-...0.7`
  - `MLP-009` `ktc_ess 70ad2d87-...1.4`
  - `CCR-007` `gangui 4fd0c566-...3.6 @ 2025-11-23`
  - `CCR-008` `gangui 4fd0c566-...4.15 @ 2025-11-23`
  - `CCR-009` `ktc_ess 10305b40-...1.12 @ 2025-10-26`
  - `CCR-010` `ktc_ess ed5e3367-...0.14 @ 2025-10-26`

### 2. exact missing-family re-scan
- `제어응답형 top1`
  - runtime heuristics: `0`
  - live-chain heuristics: `0`
- report-row 날짜 기준 same-day overlap
  - `precursor@onset`: `0`
  - `current@onset`: `0`
  - `current@fault`: `0`

### 3. widened near-window overlap
- `±7일` widened re-scan에서는 `9건`의 near-window overlap을 찾았다.
- 구성:
  - `precursor_onset` near-window: `8건`
  - `current_fault` near-window: `1건`
- 대표 예시:
  - `ktc_ess / 10305...2.12`: `current_fault` `2025-08-16` vs `site_event_soft` `2025-08-11`, gap `5일`
  - `gangui / 4fd0...4.26`: `precursor_onset` `2025-12-09` vs `group_off_date` `2025-12-04/03/02`, gap `5~7일`
  - `gangui / bf1a...1.0`: `precursor_onset` `2025-11-18` vs `group_off_date` `2025-11-23/24`, gap `5~6일`

## Reading
- BR-031은 두 사실을 동시에 고정한다.
  - curated seed set은 더 강해졌다
  - exact same-day target family는 아직 비어 있다
- 따라서 next patch에서 `near-window overlap`을 `same-day exact family`처럼 취급하면 안 된다.

## Next Safe Step
- 다음 안전 작업은 아래 둘 중 하나다.
  1. `near-window overlap backlog`를 별도 provisional family로 둘지 결정
  2. `제어응답형 top1`, `official/current same-day direct overlap` exact family를 계속 추가 수집
