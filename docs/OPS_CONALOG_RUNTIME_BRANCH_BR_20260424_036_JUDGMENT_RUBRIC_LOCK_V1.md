<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_036_JUDGMENT_RUBRIC_LOCK_V1

## Purpose
- BR-033, BR-034, BR-035에서 쌓인 evidence를 같은 급으로 읽지 않도록 `judgment rubric`을 잠근다.
- 목적은 `근거 존재`와 `family closure`를 분리하고, 다음 exact-seed search와 algorithm gating 논의가 같은 언어를 쓰게 만드는 것이다.

## Scope
- upstream evidence:
  - BR-033 near-window backlog assessment
  - BR-034 exact seed deep scan
  - BR-035 exact seed blocker anatomy
- affected docs:
  - counterexample regression checklist
  - counterexample set
  - Gate 7 implementation order lock
  - active branch register

## Judgment Role Table
| role | minimum condition | allowed use | prohibited reading | current exemplar |
| --- | --- | --- | --- | --- |
| `exact_family_closure` | report-layer row + artifact-date coincidence or direct family identity | missing family closure, exact precedent | helper/additive-only score를 closure로 확대 | currently missing for `제어응답형 top1` and official/current direct common-cause overlap |
| `supportive_hint` | score or explanation axis contributes, but top1/direct overlap still absent | ranking/explanation/support | top1 closure, exact precedent, rule patch justification | BR-034 `control_score > 0` on 4 panels |
| `candidate_reservoir` | raw-daily exact/direct rows exist and can seed deeper search | blocker search input, pressure-test seed source | report-layer exact family closure | BR-035 same-day direct raw rows `101 rows / 49 panels` |
| `non_closing_backlog` | repeated/near-window pattern exists, but flag family/slice/sign alignment is not stable | backlog tracking, future promotion test | provisional family closure, exact family substitute | BR-033 near-window backlog `5 report rows / 4 roots` |
| `structural_blocker` | family is absent because row-universe, lane-entry, or date-alignment fails | patch-target selection, blocker split | evidence absence, signal absence | BR-035 current lane `71일` gap case and row-universe mismatch |

## Test Usage Tag
- `curated pressure-test seed`는 role이 아니라 usage tag다.
- 따라서 어떤 row가 curated seed가 되더라도 아래 둘을 같이 적어야 한다.
  - underlying `judgment role`
  - 그 row가 pressure-test하는 hold/reroute bundle
- curated seed는 exact-family closure를 자동으로 의미하지 않는다.

## Reading Rules
### 1. exact family를 부를 수 있는 경우
- report-layer row가 실제로 존재한다.
- artifact-date coincidence 또는 동일 family identity가 직접 성립한다.
- helper/additive-only evidence가 아니라, closure 주장과 직접 연결되는 lane evidence가 있다.

### 2. exact family를 부르면 안 되는 경우
- `control_score > 0`만 있다.
- raw-daily same-day row만 있다.
- `±7일` near-window overlap만 있다.
- curated seed로는 편입됐지만 underlying role이 closure가 아니다.

### 3. patch relevance 순서
1. `exact_family_closure`
2. `structural_blocker`
3. `candidate_reservoir`
4. `non_closing_backlog`
5. `supportive_hint`

- 위 순서는 “중요도”가 아니라 “patch discussion eligibility” 순서다.
- 즉 `supportive_hint`가 많아도 `exact_family_closure`보다 앞서서 rule patch를 정당화하지 못한다.

## Consequence
- 다음 Gate 7 evidence turn부터는 새 결과를 적을 때 최소 아래 세 칸을 같이 적는다.
  - `judgment role`
  - `allowed use`
  - `still missing`
- 이 rubric이 없으면 아래 오독이 다시 발생한다.
  - `supportive_hint -> exact_family_closure`
  - `candidate_reservoir -> report-layer exact family`
  - `non_closing_backlog -> provisional family`
  - `curated seed -> exact closure`

## Next Safe Step
1. BR-035 blocker search를 계속하되, 새 사례를 먼저 `judgment role`로 분류한다.
2. `group_off_date -> current/report-lane entry` blocker와 `site_event -> report-date coincidence` blocker를 각각 role-tagged 사례로 모은다.
3. control-family는 `supportive_hint`를 넘는 native evidence가 생길 때만 exact-family reopen을 검토한다.
