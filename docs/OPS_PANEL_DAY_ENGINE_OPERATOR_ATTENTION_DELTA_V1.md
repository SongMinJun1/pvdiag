# OPS_PANEL_DAY_ENGINE_OPERATOR_ATTENTION_DELTA_V1

## 목적
- `operator_attention_now_v1` baseline이 이제 queue + watch-now panel dedupe까지 포함한 비교적 안정된 operator artifact가 되었기 때문에, 매 실행마다 전체 attention list를 다시 읽게 하기보다 "무엇이 달라졌는가"만 따로 내보낸다.
- 이 패치는 detector change가 아니라 operator-facing change feed 추가다.

## 왜 delta feed가 필요한가
- 현재 `panel_day_engine_operator_attention_now_v1.csv` 는 이미 "지금 볼 것"을 queue와 watch-now panel 기준으로 많이 압축한 상태다.
- 그래도 operator는 매 실행마다 full list를 처음부터 다시 읽어야 하면 피로가 크다.
- 그래서 current snapshot과 직전 snapshot을 panel key 기준으로 비교해, 새로 등장한 panel, 빠진 panel, 상태/우선순위/score/reference 변화만 따로 보여 준다.

## 왜 panel-level key를 쓰는가
- attention artifact 자체가 이미 `(site, panel_id)` 기준으로 queue/watch dedupe를 끝낸 panel-level view다.
- delta도 같은 panel key를 유지해야 operator가 "같은 panel이 이번엔 어떻게 달라졌는가"를 바로 추적할 수 있다.
- run-level key로 되돌아가면 다시 repeated recurring row noise가 늘어난다.

## 입력과 출력
- 입력
  - `_share/panel_day_engine_operator_attention_now_v1.csv`
  - optional `_share/panel_day_engine_operator_attention_now_v1_previous.csv`
- 출력
  - `_share/panel_day_engine_operator_attention_delta_v1.csv`
  - `_share/panel_day_engine_operator_attention_delta_summary_v1.csv`
  - overwrite `_share/panel_day_engine_operator_attention_now_v1_previous.csv`

## first-run bootstrap
- previous snapshot이 없으면 first-run bootstrap으로 해석한다.
- 이 경우 current attention의 모든 panel을 `new_attention` 으로 내보낸다.
- delta/summary 생성이 끝난 뒤, current attention 파일을 previous snapshot으로 복사해 다음 실행의 baseline으로 쓴다.

## delta_class 해석
- `new_attention`
  - 현재는 있는데 직전 snapshot에는 없던 panel
- `dropped_attention`
  - 직전 snapshot에는 있었지만 현재는 빠진 panel
- `attention_class_changed`
  - `queue_run` 과 `watch_now_panel` 사이 class가 바뀐 경우
- `status_or_tier_changed`
  - `display_status_or_tier` 가 바뀌었거나, 같은 class 안에서 `action_bucket` / `watchlist_bucket` 이 바뀐 경우
- `priority_changed`
  - `priority_band` 가 바뀐 경우
- `score_shifted`
  - `clipped_operator_score` 절대 차이가 1.0 이상인 경우
- `metadata_changed`
  - 위 큰 변화는 없지만 panel overlap / retrospective reference flag만 달라진 경우

delta row는 panel당 최대 1개만 만든다.  
우선순위는:
- `new/dropped`
- `attention_class_changed`
- `status_or_tier_changed`
- `priority_changed`
- `score_shifted`
- `metadata_changed`

즉 더 큰 operator 의미 변화가 있으면 그것을 대표 delta_class로 쓴다.

## 왜 baseline을 이제 freeze해도 되는가
- queue/backlog/watchlist/watch-now panel 정리가 한 차례 끝났고,
- dedupe priority도 `queue > watch_now_panel` 로 고정됐고,
- clipped operator score까지 적용돼 ordering noise도 많이 줄었다.

그래서 이제부터는 method search보다 operator reading cost를 줄이는 쪽이 더 실용적이다.

## snapshot overwrite 순서
- 비교는 항상 "기존 previous snapshot" 기준으로 먼저 수행한다.
- 그 뒤 delta/summary를 성공적으로 쓴 다음에만 previous snapshot을 current로 덮어쓴다.
- 이 순서를 지켜야 `dropped_attention` 같은 변화가 bootstrap 없이 정상적으로 포착된다.

## 해석 팁
- `new_attention` 과 `dropped_attention` 은 operator triage scope 자체가 바뀌었음을 뜻한다.
- `attention_class_changed` 는 active queue vs recurring watch representation이 바뀌었다는 뜻이라 우선적으로 보는 편이 좋다.
- `score_shifted` 는 같은 panel이라도 operator ordering 상 위치가 크게 흔들렸다는 뜻이다.
- `metadata_changed` 는 triage class는 같지만 retrospective reference context가 달라졌다는 뜻으로, 읽기 우선순위는 상대적으로 낮다.
