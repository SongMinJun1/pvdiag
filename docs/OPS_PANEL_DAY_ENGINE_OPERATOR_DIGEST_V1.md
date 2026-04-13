# OPS_PANEL_DAY_ENGINE_OPERATOR_DIGEST_V1

## 목적
- operator baseline과 delta feed가 이제 충분히 안정된 current-state layer가 되었기 때문에, operator가 매번 `attention_now` 와 `attention_delta` 를 따로 열지 않아도 되도록 single digest artifact를 만든다.
- 이 단계도 detector change가 아니라 operator-facing packaging layer다.

## 왜 digest가 필요한가
- baseline builder는 current operator state를 한 번에 다시 만드는 entrypoint다.
- delta feed는 "직전 snapshot 대비 무엇이 달라졌는가"를 따로 보여 준다.
- 하지만 operator 입장에서는 결국:
  - 지금 무엇을 볼지
  - 그 panel이 직전 대비 바뀌었는지
를 한 파일에서 같이 보고 싶다.

그래서 digest는 current attention row를 기준으로 유지하고, 그 위에 latest delta context를 얹는다.

## current row 기준인 이유
- digest는 "지금 볼 것"을 위한 current-state file이다.
- 따라서 row universe는 항상 `_share/panel_day_engine_operator_attention_now_v1.csv` 와 동일하다.
- `dropped_attention` 처럼 현재는 더 이상 attention에 없는 panel은 digest row로 넣지 않는다.

즉 dropped row는 digest summary에서는 count로 보이지만, current digest row 자체에는 등장하지 않는다.

## 입력과 출력
- 입력
  - `_share/panel_day_engine_operator_attention_now_v1.csv`
  - `_share/panel_day_engine_operator_attention_summary_v1.csv`
  - `_share/panel_day_engine_operator_attention_delta_v1.csv`
  - `_share/panel_day_engine_operator_baseline_manifest_v1.csv`
  - `_share/panel_day_engine_operator_baseline_summary_v1.csv`
- 출력
  - `_share/panel_day_engine_operator_digest_v1.csv`
  - `_share/panel_day_engine_operator_digest_summary_v1.csv`

## row 구성
- digest는 current attention row를 그대로 유지한다.
- 여기에 `(site, panel_id)` 로 latest delta row를 붙인다.

추가 필드:
- `changed_since_previous_flag`
  - 해당 panel이 delta file에 등장하면 1
  - 아니면 0
- `latest_delta_class`
  - 현재 panel에 대응하는 최신 delta class
- `latest_delta_reason_ko`
  - delta reason
- `previous_attention_class`
- `previous_status_or_tier`
- `previous_priority_band`
- `previous_clipped_operator_score`
- `clipped_score_delta`
- `baseline_generated_at_utc`

## changed_since_previous_flag 해석
- `1`
  - 현재 attention panel인데, 직전 snapshot 대비 의미 있는 변화가 있었다.
  - 예:
    - `new_attention`
    - `attention_class_changed`
    - `status_or_tier_changed`
    - `priority_changed`
    - `score_shifted`
    - `metadata_changed`
- `0`
  - 현재도 attention에 있지만, 직전 snapshot과 비교해 delta row가 없었다.

## latest_delta_class 해석
- `new_attention`
  - 이번 snapshot에서 새로 올라온 current panel
- `attention_class_changed`
  - queue vs watch-now panel 표현이 바뀐 경우
- `status_or_tier_changed`
  - 현재 state/tier 표현이 바뀐 경우
- `priority_changed`
  - priority band가 바뀐 경우
- `score_shifted`
  - clipped score 차이가 큰 경우
- `metadata_changed`
  - triage class는 같지만 reference metadata가 바뀐 경우
- blank
  - 현재 panel은 unchanged

## baseline이 왜 digest까지 갈 만큼 안정됐는가
- run consolidation, watchlist, watch-now panel, attention_now, attention_delta 순서가 이미 고정됐다.
- current attention row와 delta semantics도 panel-level key로 정리됐다.
- 그래서 이제는 operator reading cost를 줄이기 위한 last-mile packaging을 얹어도 되는 상태다.

## summary
- digest summary는 overall + per-site row를 낸다.
- 여기에는:
  - current attention 수
  - changed / unchanged attention 수
  - queue / watch-now panel 수
  - delta class별 count
  - baseline generated timestamp
가 같이 들어간다.

즉 digest summary는 "지금 보이는 attention 규모" 와 "직전 대비 얼마나 흔들렸는가"를 한 표에서 읽게 하는 용도다.
