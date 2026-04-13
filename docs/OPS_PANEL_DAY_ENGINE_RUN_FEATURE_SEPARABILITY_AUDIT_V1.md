# OPS_PANEL_DAY_ENGINE_RUN_FEATURE_SEPARABILITY_AUDIT_V1

## 왜 day-level gate tweaking이 거의 다 왔다고 보나
- local precursor는 이미 `pre_ews`, `ews_warning`, `pre_alarm` 앞단의 여러 gate replay를 해 봤다.
- 그런데 cond_evt source, same-day corroboration, exact2, seed+carry까지 좁혀도 trade-off가 계속 남는다.
- 즉 "어느 하루를 통과시키느냐"보다 "어떤 run을 더 믿을 만하냐"가 다음 문제처럼 보인다.

## 왜 run-level feature가 다음 타겟인가
- operator burden도 run 단위로 느껴지고,
- hidden positive / recurring chronic / nuisance burden 구분도 run 단위 맥락에서 더 잘 보인다.
- 그래서 현재 helper/core artifact만으로 run-level feature table을 만들고, cohort별 separation signal이 실제로 있는지 본다.

## cohort_hint 의미
- `eligible_local`
  - precursor eligible case window와 겹치는 run
- `nuisance_alert`
  - nuisance_nonlocal alert case window와 겹치는 run
- `future_fault_linked`
  - fate audit에서 future fault/truth linkage로 분류된 run
- `recurring_monitor_like`
  - fate audit에서 recurring chronic monitor형으로 분류된 run
- `isolated_unexplained`
  - fate audit에서 isolated burden으로 남은 run
- `unmatched_other`
  - 위 힌트가 아직 안 붙은 run

## normalized_gap을 어떻게 쓰나
- feature별로 두 cohort의 median 차이를 pooled IQR로 나눈 단순 robust gap score다.
- 값이 클수록 run ranker나 run-level scorer에서 쓸 만한 separation 후보일 가능성이 높다.
- 이건 descriptive audit이지 모델 성능 지표는 아니다.

## 어떤 결과가 다음 결정을 정당화하나
- A) run-level scorer prototype으로 넘어갈 근거
  - `eligible_local vs nuisance_alert`, `future_fault_linked vs recurring_monitor_like` 비교에서 몇 개 feature가 반복적으로 큰 normalized_gap을 보일 때
- B) cond_evt source 재설계를 더 할 근거
  - run-level feature separation이 약하고, 여전히 source/day-level feature만이 설명력을 갖는 경우
- C) detector-side work를 멈추고 operator-facing consolidation으로 가야 할 근거
  - strong candidate feature가 거의 없고, recurring/isolated burden이 run-level에서도 잘 안 갈릴 때

