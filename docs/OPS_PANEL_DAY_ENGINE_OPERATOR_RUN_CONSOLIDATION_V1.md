# OPS_PANEL_DAY_ENGINE_OPERATOR_RUN_CONSOLIDATION_V1

## 목적
- detector gate tweaking은 잠시 멈추고, 이미 생성된 daily local precursor alert를 operator가 실제로 다룰 수 있는 run/episode 단위 artifact로 묶는다.
- 이 단계는 detector change가 아니라, existing run universe를 operator-facing `registry / queue / backlog` 로 재포장하는 레이어다.
- queue/backlog policy 자체는 크게 흔들지 않고, score hygiene audit에서 확인된 outlier ordering 불안정만 줄이기 위해 operator 기본 정렬 score를 clipped score로 승격한다.

## 왜 run-level operator consolidation인가
- 현재 burden의 실전 문제는 daily alert flood다.
- 같은 panel에서 이어지는 daily pre-alarm은 operator 입장에서는 개별 day보다 하나의 ongoing / recovered / recurring episode로 보는 편이 더 자연스럽다.
- 그래서 기존 run feature table을 그대로 쓰고, deterministic v0 score를 붙여 run registry와 queue/backlog를 만든다.

## 왜 registry와 queue를 분리해야 하는가
- registry는 "무슨 run이 있었는가"를 빠짐없이 남기는 전체 장부다.
- queue는 "지금 operator가 바로 봐야 하는가"를 반영한 좁은 작업 목록이다.
- recurring unmatched run, 특히 `P4` 반복 run까지 queue에 남기면 daily flood가 run flood로만 바뀌기 쉽다.
- 따라서 낮은 우선순위 recurring/recovered run은 backlog로 보내고, queue는 현재성 + 우선순위가 높은 run 위주로 유지한다.

## 왜 queue/backlog 2-way split만으로는 부족한가
- queue에서 recurring chronic을 빼는 것은 active flood를 줄이는 데는 효과적이다.
- 하지만 backlog 안에만 남겨 두면, 반복적으로 나타나는 상위 chronic run이 다시 너무 조용해질 수 있다.
- 그래서 active queue를 다시 넓히지 않으면서도, recurring chronic 중 일부를 별도 `watchlist` 로 surface하는 3번째 operator-facing 레이어가 필요하다.

## 기본 score
- registry에는 두 개의 operator-facing ranking score를 함께 남긴다.
  - `raw_operator_score`
    - 기존 `electrical_core_minus_broadshape_050`
  - `clipped_operator_score`
    - operator 기본 정렬 score
- 참고 score:
  - `electrical_core_score`

`raw_operator_score` 는 이전 deterministic ordering을 그대로 보존한다.  
`clipped_operator_score` 는 같은 score formula를 쓰되, score hygiene audit에서 흔들림을 유발한 transformed input extreme을 site-level `p99` 로 upper clipping 한 뒤 robust scaling 한다.

즉 clipping은 detector 판단을 바꾸는 것이 아니라, operator가 보는 run ordering만 조금 더 안정적으로 만드는 보수적 ranking hygiene patch다.

## 왜 clipped_operator_score가 기본값인가
- queue/backlog policy 자체는 이미 대체로 맞았고, 문제는 일부 extreme run이 ordering 상단을 흔드는 점이었다.
- score hygiene audit에서 clipping 후 top-k overlap이 매우 높게 유지되었기 때문에, ordering 안정성을 얻으면서도 실질적인 triage 집합은 거의 유지된다고 볼 수 있었다.
- 그래서 operator 기본 정렬축만 `raw_operator_score` 에서 `clipped_operator_score` 로 바꾼다.

## transformed-input p99 clipping
- clipping 대상은 raw min-ratio 그 자체가 아니라 score에 실제로 들어가는 transformed input 이다.
  - `core_vdrop_input = max_v_drop`
  - `core_midv_input = 1 - min_mid_v_ratio`
  - `core_mid_input = 1 - min_mid_ratio`
  - broadshape penalty 입력:
    - `ae_mid_or_hi_early_day_ratio`
    - `mean_signal_count`
    - `max_signal_count`
    - `p95_recon_error`
- 각 입력을 site 내부 `p99` 로 upper clipping 한 뒤, 기존 scorer audit과 같은 robust scaling을 적용한다.
- 이렇게 하면 `min_mid_ratio` 같은 값이 raw domain에서는 눈에 띄지 않아도 transformed domain에서 과도하게 커지는 경우를 직접 누를 수 있다.

## raw score reference와 score_hygiene_flag
- `raw_operator_score` 는 항상 registry/queue/backlog에 같이 남긴다.
- 그래서 operator는 "원래 raw ordering" 과 "현재 clipped ordering" 을 둘 다 볼 수 있다.
- 추가 필드:
  - `raw_rank_within_site`
  - `clipped_rank_within_site`
  - `rank_shift_abs`
  - `score_hygiene_flag`
  - `score_hygiene_reason_ko`

`score_hygiene_flag` 는 다음 둘 중 하나면 1이다.
- clipping 적용 후 site 내부 rank 이동 폭이 큰 run
- transformed-input / raw score 기준으로 suspicious extreme에 해당하는 run

즉 이 플래그는 "detector 문제" 가 아니라 "ordering hygiene 주의 필요" 를 뜻한다.

## watchlist가 필요한 이유
- watchlist는 queue를 다시 넓히지 않기 위한 장치다.
- membership은 현재 시점 operator-facing 상태만 사용한다.
  - `backlog_flag`
  - `status`
  - `run_shape_class`
  - `priority_band`
  - `overlap_case_class`
- 즉 "반복되고 있는 chronic run인데, backlog 안에서도 비교적 우선순위가 높은가" 만 본다.

future linkage 관련 필드:
- `future_fault_linked_flag`
- `future_truth_linked_flag`

는 watchlist 자격을 정하는 데 쓰지 않는다.  
이 값들은 retrospective reference로만 남겨서, 나중에 watchlist가 실제 hidden value와 얼마나 닿아 있었는지 사후 점검할 때만 본다.

## 왜 watchlist v1만으로는 아직 넓은가
- watchlist v1은 recurring chronic backlog를 다시 드러내는 데는 유용했지만, `P1` 과 `P2` 가 한 층에 섞여 있어 operator 입장에서는 여전히 다소 넓게 느껴질 수 있다.
- 그래서 current-state membership 자체는 그대로 두고, 이미 watchlist에 들어온 run만 `watch_now` 와 `watch_review` 로 다시 나눈다.
- 이 분리는 queue를 다시 넓히지 않으면서, recurring chronic 중에서도 더 자주 볼 대상을 앞쪽으로 모으기 위한 operator-facing tiering layer다.

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
- 이번 패치에서는 queue/backlog membership은 바꾸지 않는다.
- 오직 queue/backlog 내부 정렬만 `clipped_operator_score` 기준으로 바뀐다.

## watchlist 규칙
- watchlist는 backlog의 부분집합이다.
- queue와는 겹치지 않는다.
- bucket:
  - `recurring_watch_p1`
    - backlog 안의 recurring chronic run 중 `P1` 이고 `nuisance_overlap` 이 아닌 경우
  - `recurring_watch_p2`
    - backlog 안의 recurring chronic run 중 `P2` 이고 `nuisance_overlap` 이 아닌 경우
  - `none`
    - 나머지

watchlist 해석:
- `recurring_watch_p1`
  - 반복 chronic 중에서도 site 내부 상대 우선순위가 가장 높은 편이라, active queue는 아니지만 operator가 주기적으로 다시 봐야 하는 대상
- `recurring_watch_p2`
  - P1보다는 약하지만, backlog 속에 묻히기엔 아까운 recurring chronic

즉 watchlist는 detector 승격이 아니라, recurring chronic backlog를 재정렬해 보여 주는 operator-facing surfacing layer다.

## watchlist tier 해석
- watchlist membership은 바꾸지 않는다.
- 이미 `watchlist_flag == 1` 인 run만 대상으로 삼고, 그 안에서 tier만 나눈다.
- `watch_now`
  - `watchlist_bucket == recurring_watch_p1`
  - 즉시 주시할 상위 반복 chronic
- `watch_review`
  - `watchlist_bucket == recurring_watch_p2`
  - 검토용 반복 chronic
- `none`
  - watchlist tier 대상이 아님

즉 `watch_now` 는 "queue로 올리진 않지만 더 자주 볼 tier",  
`watch_review` 는 "backlog 안에서 정기 검토할 tier" 로 이해하면 된다.

## 중요한 점
- 이 패치는 detector logic을 바꾸지 않는다.
- canonical truth contract도 바꾸지 않는다.
- `_share` 산출물만 갱신하여 operator-facing policy layer를 조정한다.
