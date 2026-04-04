# OPS_PANEL_DAY_ENGINE_OPERATOR_RUN_CONSOLIDATION_V1

## 목적
- detector gate tweaking은 잠시 멈추고, 이미 생성된 daily local precursor alert를 operator가 실제로 다룰 수 있는 run/episode 단위 artifact로 묶는다.
- 이 단계는 detector change가 아니라, existing run universe를 operator-facing `registry / queue / backlog` 로 재포장하는 레이어다.

## 왜 run-level operator consolidation인가
- 현재 burden의 실전 문제는 daily alert flood다.
- 같은 panel에서 이어지는 daily pre-alarm은 operator 입장에서는 개별 day보다 하나의 ongoing / recovered / recurring episode로 보는 편이 더 자연스럽다.
- 그래서 기존 run feature table을 그대로 쓰고, deterministic v0 score를 붙여 run registry와 queue/backlog를 만든다.

## 왜 registry와 queue를 분리해야 하는가
- registry는 "무슨 run이 있었는가"를 빠짐없이 남기는 전체 장부다.
- queue는 "지금 operator가 바로 봐야 하는가"를 반영한 좁은 작업 목록이다.
- recurring unmatched run, 특히 `P4` 반복 run까지 queue에 남기면 daily flood가 run flood로만 바뀌기 쉽다.
- 따라서 낮은 우선순위 recurring/recovered run은 backlog로 보내고, queue는 현재성 + 우선순위가 높은 run 위주로 유지한다.

## 기본 score
- 기본 operator ordering score:
  - `electrical_core_minus_broadshape_050`
- 참고 score:
  - `electrical_core_score`

`electrical_core_minus_broadshape_050` 을 기본값으로 쓰는 이유는, pure electrical severity를 유지하면서도 broadshape 계열 과잉 우선순위를 조금 누르는 가장 보수적인 deterministic score이기 때문이다.

## status 해석
- `ongoing_run`
  - site 최신 run 종료일에 거의 붙어 있는 run. 현재도 이어지고 있을 가능성이 가장 높다.
- `new_run`
  - 시작이 최근 3일 안쪽인 새 episode.
- `recurring_run`
  - 최근 60일 내 재발 정보가 있는 run.
- `recovered_run`
  - 최신 run은 아니지만 최근 7일 안쪽에서 종료된 run.
- `historical_run`
  - 위 네 상태에 해당하지 않는 과거 run.

status는 최근성/재발성을 operator triage용으로 붙인 것이고, detector decision 자체를 바꾸지 않는다.

## priority_band 해석
- site 내부에서 `electrical_core_minus_broadshape_050` 순위 기준으로 밴드를 부여한다.
- `P1`
  - site 상위 5%
- `P2`
  - 다음 15%
- `P3`
  - 다음 30%
- `P4`
  - 나머지

즉 priority는 "지금 당장 볼 가치가 큰 electrical-like run인가"를 site별 상대 순위로 표현한 것이다.

## action_bucket 해석
- `investigate_now`
  - `new_run` 또는 `ongoing_run` 이면서 `P1/P2`
- `monitor_active`
  - `new_run` 또는 `ongoing_run` 이면서 `P3` 이고 `medium/chronic`
- `recurring_backlog`
  - 현재 반복 run이지만 바로 queue에 올릴 정도의 current-state urgency는 아닌 backlog
- `recovered_backlog`
  - 최근 종료된 run으로, queue보다는 follow-up backlog가 적절한 경우
- `historical_archive`
  - 현재 operator queue/backlog 어디에도 올리지 않는 과거 archive

즉 action_bucket은 detector confidence가 아니라 operator action policy를 표현한다.

## operator queue / backlog 규칙
- queue에는 `action_bucket in {investigate_now, monitor_active}` 만 넣는다.
- backlog에는 `action_bucket in {recurring_backlog, recovered_backlog}` 만 넣는다.
- 그래서 `P4 recurring unmatched` run은 registry에는 남지만 queue에서는 빠지고 backlog로 이동한다.

## 중요한 점
- 이 패치는 detector logic을 바꾸지 않는다.
- canonical truth contract도 바꾸지 않는다.
- `_share` 산출물만 추가하여 operator-facing policy layer를 제공한다.
