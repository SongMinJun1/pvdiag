# OPS_PANEL_DAY_ENGINE_LOCAL_PRECURSOR_COHORT_AUDIT_V1

## 목적

이 감사는 `panel_day_engine.py` 안에 이미 존재하는 local precursor head가 실제 local fault cohort에서 fault 전에 얼마나 잡히는지 재는 첫 공정한 cohort test다.

여기서 local precursor head는 새 detector가 아니라, 이미 helper output에 흩어져 있던 기존 엔진 산출물이다.

- `ews_warning`
- `prefault_B`
- `pre_alarm`

이번 v1 해석 패치는 detector를 바꾸지 않는다. 대신 cohort metric을 다음 세 층으로 분리한다.

- any-prior historical alert presence
- bounded precursor hit within a valid 30-day pre-fault window
- stale historical alert far before fault

## 왜 unlimited any-prior matching이 misleading한가

기존 v1은 fault보다 이전이면 얼마나 멀리 떨어져 있어도 hit로 셌다.

이 방식은 아래 같은 문제를 만든다.

- 245일 전 오래된 alert도 precursor hit처럼 보인다
- median lead가 “precursor lead”가 아니라 “historical alert age”를 섞어버린다
- local precursor head가 실제 fault 전조를 잡았는지와 과거에 한 번 켜졌는지를 구분하지 못한다

즉 unlimited any-prior hit는 detector 존재 여부는 보여줘도 precursor metric으로는 과장되기 쉽다.

## 왜 30-day bounded window가 더 해석 가능성이 높은가

이번 패치는 bounded precursor를 다음처럼 제한한다.

- fault보다 엄격히 이전
- fault start 기준 최근 30일 안

이 bounded window는 “fault 직전 precursor behavior”라는 해석이 가능하다.

- 1~3일: 매우 근접한 short-lead precursor
- 4~7일: 짧지만 운영적으로 의미 있는 lead
- 8~30일: 비교적 여유 있는 precursor window

이렇게 나누면 detector가 실제 fault를 앞두고 켜졌는지 더 읽기 쉬워진다.

## stale alert를 왜 따로 분리해야 하는가

stale alert는 다음 조건이다.

- any-prior hit는 있다
- bounded hit는 없다

이 경우의 의미는 “signal head가 과거에 한 번 켜진 적은 있지만, 지금 평가하려는 fault window의 precursor라고 보기 어렵다”에 가깝다.

따라서 stale alert는 버리면 안 되지만, bounded precursor hit와 같은 숫자로 합치면 안 된다.

## fault anchor를 왜 `final_fault` 기준으로 두는가

가능하면 `strict_trigger_date`보다 엔진 내부의 실제 최종 fault anchor가 더 직접적이다.

그래서 규칙은 다음과 같다.

- 우선 shadow artifact에서 `final_fault == True` 인 가장 이른 날짜를 찾는다
- 단, strict case 문맥과 너무 멀어지지 않도록 `strict_trigger_date - 30 days` 이후만 본다
- 그 날짜가 있으면 `fault_start_date`로 사용한다
- 없으면 `strict_trigger_date`로 fallback 한다

이렇게 해야 “엔진이 실제로 fault라고 본 시점”과 “truth/governance strict case 시점”을 최대한 가깝게 맞출 수 있다.

## 이 감사가 답하는 질문

- `true_positive` local fault cohort에서 any-prior alert는 있었는가
- 그 중 최근 30일 bounded precursor는 있었는가
- 어떤 케이스가 stale historical alert만 가지고 있는가
- bounded window 안에서 가장 의미 있는 alert source는 무엇인가
- bounded lead가 1~3일 / 4~7일 / 8~30일 중 어디에 분포하는가

## alert-level precursor와 signal-level precursor의 차이

raw metric 상으로는 이상 신호가 있어도 alert-level precursor가 없을 수 있다.

예를 들어 다음은 모두 가능하다.

- `recon_error`, `dtw_dist`, `hs_score` 는 높았지만 `ews_warning` run length를 못 채움
- `ews_warning` 는 있었지만 `prefault_B` template 조건은 못 채움
- helper output에는 alert가 없지만 raw signal은 분명 움직임

이 경우 의미는 “신호가 없었다”가 아니라 “현재 alert-level head가 그 신호를 precursor로 채택하지 않았다”에 가깝다.

## 이 패치가 detector change가 아닌 이유

이번 수정은 다음을 바꾸지 않는다.

- engine signal 계산
- helper output 생성
- strict cohort 정의
- truth contract

바꾸는 것은 metric interpretation 뿐이다.

- any-prior는 detector historical presence
- bounded는 precursor metric
- stale는 historical-but-not-precursor diagnostic

따라서 이 패치는 detector tuning이 아니라 audit semantics fix다.

## 어떤 결과가 다음 조치를 정당화하는가

다음 중 하나가 보이면 후속 패치 정당성이 높다.

- any-prior는 많은데 bounded는 거의 없다
- stale alert가 많아 bounded recall보다 historical carry-over가 더 크다
- bounded hit가 있어도 lead가 거의 1~3일에만 몰린다
- raw signal은 움직이는데 alert-level bounded hit가 낮다

이 경우 다음 선택지가 열린다.

- core persistence patch: 더 많은 precursor state를 canonical/shadow에 남기기
- threshold retuning audit: `ews_warning`, `prefault_B`, `pre_alarm` 의 bounded precursor behavior를 재검토하기

반대로 bounded hit/lead가 이미 의미 있게 나오면, 먼저 필요한 것은 새 detector보다 evaluation rewiring일 수 있다.
