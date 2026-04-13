# OPS_MAINTENANCE_PROXY_SHADOW_F1_V1

## 목적

`maintenance_shadow_f1_v1`는 audit에서 제안된 후보 집합을 그대로 shadow promotion 했을 때의 이득을 보여줬다. 하지만 그 결과만으로 공식 규칙을 바로 만들 수는 없다. 실제 upstream patch를 검토하려면, full strict-case universe 전체에서 truth-independent proxy를 직접 적용했을 때 어떤 row가 선택되고, maintenance F1이 얼마나 달라지는지 별도로 봐야 한다.

이 문서는 그 shadow-only evaluator를 정의한다.

## 왜 same-group collapse를 본다

직전 proxy audit에서 가장 유망했던 패턴은 다음이었다.

- clean confirmed-fault row
- strict day에서 group-like shape
- 같은 그룹에서 동시 zero-like collapse 존재

반대로 site-level collapse는 strict-backed candidate와 lenient-only candidate를 함께 잡아서 구분력이 약했다. 그래서 이번 shadow evaluator는 site-wide collapse를 진단용으로만 남기고, 실제 promotion trigger는 same-group collapse만 쓴다.

## 왜 여전히 shadow-only인가

이 evaluator는 공식 `actionability_v3`를 바꾸지 않는다.

- `critical_actionability_shadow_v3_latest.csv`를 수정하지 않는다.
- routing/packet output을 수정하지 않는다.
- canonical truth template contract를 수정하지 않는다.

선택된 row는 오직 평가 내부에서만 `maintenance_candidate_shadow`로 본다.

## truth 계약

truth는 `full_algorithm_f1_v3`와 동일한 hybrid truth를 그대로 쓴다.

우선순위:

1. manual truth: `candidate_validity`
2. vendor truth: `vendor_reply_class`
3. 둘 다 없으면 exclude

manual mapping:

- positive: `true_positive`, `group_side`
- negative: `false_positive`
- exclude: `needs_more_info`, blank

vendor strict mapping:

- positive: `field_confirmed_positive`, `vendor_pattern_positive`
- negative: `vendor_rejected`
- exclude: `vendor_likely_positive`, `vendor_no_info`, blank

vendor lenient mapping:

- positive: `field_confirmed_positive`, `vendor_pattern_positive`, `vendor_likely_positive`
- negative: `vendor_rejected`
- exclude: `vendor_no_info`, blank

## proxy 입력

proxy는 algorithm-side fields만 쓴다.

- `panel_onset_shadow_latest.csv`
  - `days_earlier_than_trigger`
  - `onset_confidence`
  - `onset_method`
  - `reason_summary`
- `panel_day_core.csv` strict-day row
  - `mid_ratio`
  - `mid_v_ratio`
  - `mid_i_ratio`
  - `v_drop`
  - `coverage_mid`
  - `group_key_base`

`reason_summary`에서 파싱:

- `strict_method`
- `shadow_frac`
- `group_off_frac`
- `recovery_reset`

## 파생 feature

- `clean_confirmed_flag`
  - `strict_method == confirmed_fault_flag`
  - `shadow_frac == 0`
  - `group_off_frac == 0`
  - `recovery_reset == no`
- `strict_day_group_like_flag`
  - `mid_ratio <= 0.10`
  - `mid_i_ratio <= 0.10`
  - `mid_v_ratio >= 1.05`
- `same_group_zero_like_count`
  - same site, same strict day, same group proxy 내에서
  - `mid_ratio <= 0.10`
  - `mid_i_ratio <= 0.10`
  - `coverage_mid >= 0.50`
- `same_site_zero_like_count`
  - 위 조건의 site-wide count

## shadow promotion rule

공식 prediction이 이미 `maintenance_candidate`인 row는 건드리지 않는다.

그 외 row에 대해 아래가 모두 참이면 shadow promotion 한다.

- `clean_confirmed_flag == 1`
- `strict_day_group_like_flag == 1`
- `same_group_zero_like_count >= 2`

그러면 evaluator 내부에서만:

- `shadow_actionability_v3 = maintenance_candidate_shadow`

중요한 제한:

- `same_site_zero_like_count`는 promotion trigger로 쓰지 않는다.
- vendor label은 scoring truth에는 쓰이지만, proxy rule input으로는 쓰지 않는다.

## scenario

### `baseline_v3`

maintenance positive:

- `maintenance_candidate`

### `same_group_group_like_shadow`

maintenance positive:

- `maintenance_candidate`
- `maintenance_candidate_shadow`

## selected-case count가 중요한 이유

F1이 조금 좋아졌더라도 selected case 수가 너무 많으면 upstream rule로는 위험하다. 반대로 F1 이득이 크더라도 극소수 특정 site에만 걸리면 general rule로 보기 어렵다.

그래서 이 evaluator는 F1만이 아니라 다음도 같이 낸다.

- selected case rows
- promoted_case_count
- scenario별 error cases

## 어떤 결과가 upstream patch를 정당화하나

정당화에 가까운 결과:

- selected-case count가 작고 안정적이다.
- false positive 증가가 없다.
- strict-mode maintenance F1이 의미 있게 오른다.
- 선택된 row가 모두 같은 해석 가능한 algorithm-side pattern을 가진다.

정당화에 부족한 결과:

- site-level collapse 같은 넓은 trigger가 함께 필요하다.
- selected-case count가 커지면서 false positive도 늘어난다.
- strict-backed pattern과 lenient-only pattern이 계속 섞인다.

## 산출물

- `_share/maintenance_proxy_shadow_f1_summary_v1.csv`
- `_share/maintenance_proxy_shadow_selected_cases_v1.csv`
- `_share/maintenance_proxy_shadow_case_errors_v1.csv`
