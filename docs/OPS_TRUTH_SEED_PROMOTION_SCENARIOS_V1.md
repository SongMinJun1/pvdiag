# OPS_TRUTH_SEED_PROMOTION_SCENARIOS_V1

## 목적
- 현재 ready seed를 한 번에 전부 promote하지 않고
- `safe_same_label_copyback`와 `gate_review_required`로 나눈 뒤
- 각 시나리오가 baseline truth와 metric에 어떤 영향을 주는지 비교하는 preview-only 단계다.

canonical truth 원본은 덮어쓰지 않는다.

## 왜 7 same-label rows가 3 gate rows보다 낮은 위험인가
현재 ready seed 10건은 두 부류로 나뉜다.

- `safe_same_label_copyback`
  - vendor truth에서 manual truth로 provenance만 바뀐다.
  - strict/lenient polarity 자체는 유지된다.
  - 즉 score 구조를 흔들기보다 trust provenance를 강화하는 쪽이다.

- `gate_review_required`
  - strict truth label이 실제로 바뀐다.
  - vendor 기반에서는 `exclude`였던 케이스가 manual positive로 들어오거나,
    strict scoring universe 자체가 달라진다.
  - 이 row들은 conflict가 0이어도 해석 리스크가 남아 있다.

그래서 현재 10건 중 7건은 낮은 operational risk, 3건은 manual gate 확인이 필요한 상태로 본다.

## 시나리오 정의
- `current_canonical`
  - 아무 seed도 적용하지 않은 현재 truth 상태

- `safe_same_label_only`
  - same-label safe rows만 in-memory 적용
  - 현재 가장 권장되는 다음 운영 단계

- `full_ready_rows`
  - ready rows 전체 10건을 in-memory 적용
  - 영향 upper bound를 보는 시나리오

## 왜 `safe_same_label_only`가 preferred next path인가
- manual truth coverage를 늘린다.
- vendor truth 의존을 줄인다.
- strict polarity를 흔들지 않는다.
- reviewer/ops 관점에서 promote 리스크가 가장 낮다.

즉 score 자체보다 provenance를 먼저 올리고 싶은 지금 단계에서 가장 실용적이다.

## 왜 `full_ready_rows`를 blind promote하면 안 되나
- conflict가 0이라는 것은 key collision이 없다는 뜻이지,
  semantic risk가 0이라는 뜻은 아니다.
- gate 3건은 strict scoring universe를 실제로 바꾼다.
- 이 경우 F1, scored rows, vendor/manual split이 달라질 수 있다.

그래서 `full_ready_rows`는 “가능한 전체 영향”을 보는 평가 시나리오이지,
곧바로 promote해도 된다는 뜻은 아니다.

## gate 3건에서 확인해야 할 manual evidence
다음 근거가 있어야 promote 판단이 강해진다.
- field/O&M 로그가 panel issue 또는 group-side issue를 직접 지지하는가
- vendor reply가 단순 likely-positive인지, 실제 현장 정황과 맞는가
- onset/strict_trigger 맥락이 reviewer note와 일관적인가
- same-day group/common-cause 상황 때문에 strict panel truth가 과대 해석된 것은 아닌가

즉 gate row는 “reviewer가 label을 넣었다”보다
“strict scoring change를 감당할 만큼 evidence가 충분한가”를 확인해야 한다.

## 출력 파일
- `_share/truth_seed_promotion_scenarios_summary_v1.csv`
- `_share/truth_seed_safe_apply_rows_v1.csv`
- `_share/truth_seed_gate_review_rows_v1.csv`
- `_share/truth_seed_promotion_changed_cases_v1.csv`

## 파일 사용법

### `truth_seed_safe_apply_rows_v1.csv`
- 낮은 리스크 same-label promote 후보 목록이다.
- next manual promote shortlist로 바로 쓸 수 있다.

### `truth_seed_gate_review_rows_v1.csv`
- strict truth label을 바꾸는 row만 모은다.
- `current_strict_truth_label`, `proposed_strict_truth_label`, `gate_reason`를 같이 봐야 한다.

### `truth_seed_promotion_changed_cases_v1.csv`
- scenario별로 current 대비 truth source/label이 어떻게 달라지는지 보여준다.
- `no_label_change_manualized`는 provenance 강화 케이스다.
- `strict_label_changed_requires_gate`는 promote 전 수동 근거 확인이 필요한 케이스다.

### `truth_seed_promotion_scenarios_summary_v1.csv`
- 세 시나리오를 동일한 평가 축으로 비교한다.
- F1뿐 아니라 `manual_truth_present_count`, `vendor_truth_used_count`를 함께 봐야 한다.

## 운영 권장 순서
1. `truth_seed_safe_apply_rows_v1.csv`로 low-risk 7건을 먼저 검토한다.
2. `truth_seed_gate_review_rows_v1.csv`에서 3건 근거를 별도로 확인한다.
3. `truth_seed_promotion_scenarios_summary_v1.csv`로 safe-only와 full-ready 차이를 비교한다.
4. safe-only promote 여부를 먼저 결정하고, gate 3건은 별도 reviewer sign-off 뒤에만 올린다.
