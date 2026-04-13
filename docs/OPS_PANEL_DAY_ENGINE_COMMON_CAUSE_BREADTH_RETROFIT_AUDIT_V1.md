# OPS_PANEL_DAY_ENGINE_COMMON_CAUSE_BREADTH_RETROFIT_AUDIT_V1

## 목적
- breadth-marker audit에서 동률로 남은 common-cause candidate 중, 가장 덜 넓고 가장 보수적인 후보를 고른다.
- detector logic은 바꾸지 않고, descriptive routing marker candidate를 고르기 위한 prevalence/parsimony retrofit audit이다.

## 왜 첫 breadth audit만으로는 부족했나

직전 audit은:

- positive capture
- contamination

을 기준으로 breadth rule을 비교했다.

하지만 여러 rule이 동시에:

- `4/4 capture`
- `0 contamination`

을 만족하면, labeled set만으로는 어떤 rule이 실제 운영에서 덜 넓고 덜 부담스러운지 알기 어렵다.

즉 첫 audit은 “쓸 수 있는 후보가 있는가”를 보여줬고,  
이번 retrofit audit은 “그중 가장 좁고 단순한 후보가 무엇인가”를 정하는 단계다.

## 왜 tied candidate는 prevalence/parsimony 비교가 필요한가

동률 후보라도 운영 의미는 다르다.

- `same_day` 는 보수적이고 해석이 단순하다.
- `plusminus_3d` / `plusminus_7d` 는 더 넓게 켜질 수 있다.
- `final_fault` 단일 source는 해석이 단순하다.
- `any_breadth` 는 coverage는 넓지만 prevalence도 넓어질 수 있다.

그래서 retrofit audit은 candidate별로:

- 전체 site/day에서 얼마나 자주 켜지는지
- episode가 얼마나 길어지는지
- source/window/threshold가 얼마나 단순한지

를 함께 본다.

## 왜 narrower same-day / single-source candidate가 선호될 수 있나

동일한 capture와 동일한 contamination이면:

- 덜 자주 켜지고
- 더 짧게 켜지고
- 해석이 더 단순한

candidate가 더 안전하다.

특히 common-cause bucket이 아직 descriptive에 가깝다면,

- `final_fault` only
- `same_day`
- 가능한 한 높은 threshold

쪽이 retrofit candidate로 더 적합하다.

즉 “잘 잡는가”보다  
“불필요하게 넓지 않은가”가 tie-break의 핵심이다.

## 추천 규칙 선택 기준

후보는 먼저 다음 tied set으로 제한한다.

- `positive_capture_rate == 1.0`
- `contamination_score == 0.0`

그 다음 우선순위는:

1. positive capture 최대
2. contamination 최소
3. `triggered_site_day_rate` 최소
4. source complexity 최소
5. window complexity 최소
6. threshold 최대

즉 least-broad viable candidate를 고르는 방식이다.

## 어떤 결과가 breadth rule 추가를 정당화하나

다음이면 정당화된다.

- tied candidate 중 하나가 prevalence가 눈에 띄게 낮음
- same-day / single-source처럼 더 단순함
- labeled overlap 성능은 유지됨

이 경우 해당 rule은 detector 승격이 아니라,
우선 descriptive routing marker candidate 또는 review aid로 추가할 근거가 된다.

## 어떤 결과면 descriptive-only를 유지해야 하나

다음이면 유지가 타당하다.

- tied candidate끼리 prevalence 차이가 거의 없음
- narrower candidate도 충분히 넓게 켜짐
- candidate 해석이 여전히 ambiguous함

이 경우 `non_panel_or_common_cause` 는 아직 descriptive-only bucket으로 두는 편이 더 안전하다.
