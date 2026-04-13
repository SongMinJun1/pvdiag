# OPS_PANEL_DAY_ENGINE_OPERATOR_SCORE_HYGIENE_AUDIT_V1

## 목적
- 현재 operator queue policy 자체는 대체로 정리되었고, 다음 질문은 "run ordering score가 소수 extreme run 때문에 흔들리는가"이다.
- 그래서 detector logic이나 queue policy는 건드리지 않고, 현재 operator-facing score의 hygiene와 clipping sensitivity만 따로 감사한다.

## 왜 score stability를 보나
- queue/backlog가 분리된 뒤에도 상단 run ordering이 extreme feature 몇 개에 의해 크게 출렁이면 operator triage 경험은 여전히 불안정하다.
- 특히 `electrical_core_minus_broadshape_050` 는 deterministic score라, 작은 clipping/winsorization만으로 ordering이 안정되면 method change 없이도 operator usability를 개선할 수 있다.

## 왜 site-level clipping인가
- run feature 분포가 site마다 다르므로 global clipping보다 site-level upper clipping이 더 자연스럽다.
- 이번 audit에서는 audited raw feature를 site p99에서 upper winsorize한 뒤, 기존 v0와 같은 score formula를 다시 계산해 rank stability를 본다.

## 무엇을 보나
- suspicious outlier run
  - site p99.5 초과 혹은 site robust_z > 8 인 feature/score를 가진 run
- additive contribution breakdown
  - `electrical_core_score`, `electrical_core_minus_broadshape_050` 를 구성하는 core / broadshape term
- clipping sensitivity
  - raw score vs clipped score ranking의 top20/top50/top100 overlap
  - rank shift가 가장 큰 run 목록

## 해석 가이드
- A) operator-facing clipping 추가를 정당화하는 결과
  - suspicious run 수는 적지만, 그 소수가 top20/top50 ordering을 크게 흔들고
  - site-level clipping 뒤 top-k overlap은 높게 유지되면서도 몇몇 extreme run만 완화될 때
- B) score를 그대로 두는 편이 나은 결과
  - suspicious run이 적고, clipping 후에도 top20/top50/top100 overlap이 거의 1.0 에 가깝고
  - 최대 rank shift도 작을 때
- C) score formula 자체를 다시 봐야 하는 결과
  - clipping만으로도 ordering이 크게 바뀌거나
  - suspicious run이 queue/backlog 상단을 지속적으로 점유하고
  - 어떤 feature 한두 개가 score를 과도하게 지배할 때

## 중요한 점
- 이 audit은 operator-facing ranking stability 점검이다.
- detector logic은 바꾸지 않는다.
- operator queue policy도 바꾸지 않는다.
