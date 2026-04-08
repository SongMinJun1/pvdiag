# OPS PANEL DAY ENGINE PROJECT EVAL SUPPORT GAP AUDIT V1

## 목적

`build_panel_day_engine_project_eval_support_gap_audit_v1.py` 는 reliability audit 다음 단계로, 현재 underpowered / low-support / caution-level row들이 얼마나 더 많은 positive support를 필요로 하는지 정량화합니다. 그리고 그 support를 current artifacts만 재조합해서 채울 수 있는지, 아니면 genuinely new truth/data expansion이 필요한지도 함께 표시합니다.

## 왜 reliability audit만으로는 부족한가

reliability audit은 각 row를 `underpowered`, `low_support`, `provisional`, `proxy_only`, `structural_only` 로 나눠 줍니다. 하지만 여기서 바로 “그래서 다음에 무엇을 해야 하는가?” 가 나오지는 않습니다. support gap audit은 그 다음 질문에 답합니다.

- support 5까지 가려면 몇 건이 더 필요한가
- support 10까지 가려면 몇 건이 더 필요한가
- 그 추가 support가 현재 artifacts 안에 잠재적으로 남아 있는가
- 아니면 새로운 truth/data 확장이 없으면 더는 못 가는가

## 왜 freeze 전 support-gap 분석이 필요한가

small-support row는 F1가 좋아 보여도 쉽게 흔들립니다. reliability audit이 “지금은 freeze하지 말자”를 말해 준다면, support-gap audit은 “그 상태를 current artifacts로 풀 수 있는지”를 말해 줍니다. 즉 freeze decision 전에 필요한 후속 액션을 구체화하는 단계입니다.

## scope별 current-artifact candidate pool

### step3_precursor_performance

current artifact pool은:

- `panel_day_engine_local_precursor_eligibility_cases_v1.csv` 에서 `precursor_eligible_flag == 1`
- 하지만 아직 `panel_day_engine_precursor_onset_truth_v1.csv` 에 `(site, panel_id, fault_start_date)` 로 들어오지 않은 case

입니다. 이는 새 raw data 없이도 precursor-bearing support를 보강할 가능성이 있는 후보를 뜻합니다.

### step4_abrupt_no_precursor

current artifact pool은:

- `panel_date_reaudit_working.csv` 에서 abrupt bucket으로 해석 가능한 re-audit case
- 하지만 현재 `panel_day_engine_non_precursor_performance_cases_v1.csv` 의 positive abrupt case로는 아직 집계되지 않은 row

입니다. 이 풀이 비어 있으면, current artifacts만으로는 abrupt support를 더 늘리기 어렵다는 뜻입니다.

### step4_common_cause_routing

current artifact pool은:

- `panel_date_reaudit_working.csv` 의 group-side / common-cause 성격 row
- 하지만 아직 `panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv` 의 positive common-cause case로는 집계되지 않은 row

입니다.

## 왜 어떤 scope는 current artifacts로 개선이 불가능할 수 있는가

candidate pool이 0이거나, pool을 모두 더해도 support 5 / 10에 도달하지 못할 수 있습니다. 이런 경우는 current branch 산출물 재조합만으로는 support gap이 닫히지 않는다는 뜻입니다. 그때는:

- 새 truth labeling
- 새 field confirmation
- 새 branch data expansion

중 하나가 필요합니다.

## 왜 operator proxy row는 다르게 다루는가

`operator_policy_proxy` 는 retrospective proxy metric이지 true classifier support 문제가 아닙니다. 따라서 support gap을 “positive case 몇 건 더 모으면 해결된다” 식으로 해석하면 오해가 생깁니다. 이 row는 pool count를 비워 두고, 별도 workflow/load validation이 더 중요하다는 note를 남깁니다.
