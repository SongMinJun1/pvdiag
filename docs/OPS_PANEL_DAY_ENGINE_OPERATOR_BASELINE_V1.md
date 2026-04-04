# OPS_PANEL_DAY_ENGINE_OPERATOR_BASELINE_V1

## 목적
- operator layer가 이제 `run consolidation -> attention_now -> attention_delta -> digest` 순서로 비교적 안정된 baseline을 갖추었기 때문에, 전체 operator-facing artifact를 한 번에 다시 만드는 entrypoint를 고정한다.
- 이 단계는 detector change가 아니라 packaging/orchestration layer다.

## 왜 이제 orchestrate할 수 있는가
- daily flood를 run/episode 단위로 접었고,
- queue / backlog / watchlist / watch_now panel / attention_now 구조가 정리됐고,
- attention delta까지 붙어서 operator가 "무엇이 바뀌었는가"를 별도로 읽을 수 있게 됐다.
- 그리고 digest까지 붙어서 "지금 볼 것 + 직전 대비 변화"를 한 파일에서 읽을 수 있게 됐다.

즉 method search용 실험 artifact가 아니라, current operator baseline을 재생성하는 고정 순서를 둘 만한 시점이 됐다.

## baseline builder가 하는 일
`build_panel_day_engine_operator_baseline_v1.py` 는 아래 세 builder를 순서대로 실행한다.

1. `research/prognostics/build_panel_day_engine_operator_run_consolidation_v1.py`
2. `research/prognostics/build_panel_day_engine_operator_attention_delta_v1.py`
3. `research/prognostics/build_panel_day_engine_operator_digest_v1.py`

이 순서가 필요한 이유:
- attention delta는 current attention artifact를 입력으로 쓰기 때문에,
- run consolidation이 먼저 attention baseline을 다시 만든 뒤,
- 그 다음 delta가 previous snapshot과 비교해야 한다.
- digest는 current attention row에 latest delta context를 붙여 읽기 때문에,
  delta가 먼저 끝난 뒤에만 정상적으로 생성할 수 있다.

digest builder는 baseline manifest/summary를 입력으로도 읽기 때문에, baseline orchestrator는
1. run consolidation + attention delta 실행
2. provisional baseline manifest/summary 기록
3. digest 실행
4. digest-aware final baseline manifest/summary로 overwrite
순서로 동작한다.

## 재생성되는 산출물
baseline builder 자체는 기존 operator outputs를 다시 생성한다.

주요 하위 산출물:
- run consolidation 계열
  - `panel_day_engine_operator_run_registry_v1.csv`
  - `panel_day_engine_operator_run_queue_v1.csv`
  - `panel_day_engine_operator_run_backlog_v1.csv`
  - `panel_day_engine_operator_run_watchlist_v1.csv`
  - `panel_day_engine_operator_attention_now_v1.csv`
- attention delta 계열
  - `panel_day_engine_operator_attention_delta_v1.csv`
  - `panel_day_engine_operator_attention_delta_summary_v1.csv`
  - `panel_day_engine_operator_attention_now_v1_previous.csv`
- digest 계열
  - `panel_day_engine_operator_digest_v1.csv`
  - `panel_day_engine_operator_digest_summary_v1.csv`

그리고 baseline builder는 추가로:
- `_share/panel_day_engine_operator_baseline_manifest_v1.csv`
- `_share/panel_day_engine_operator_baseline_summary_v1.csv`
를 쓴다.

## manifest와 summary의 역할
### manifest
- baseline 실행 1회를 대표하는 단일 row artifact다.
- `generated_at_utc` 와 함께:
  - attention count
  - queue/backlog/watchlist/watch_now/watch_review count
  - delta row count
  - new/dropped/total changed count
  - digest attention count
  - digest changed attention count
  - digest queue/watch split
를 한 줄에서 본다.

즉 "이번 baseline run이 어떤 규모의 operator state를 만들었는가"를 빠르게 남기는 실행 manifest다.

### summary
- overall + per-site row를 함께 가진 비교용 summary다.
- site별로:
  - attention count
  - queue/backlog/watchlist/watch_now/watch_review count
  - new/dropped/total changed count
  - digest changed attention count
  - digest queue/watch split
를 한 표에서 보게 한다.

즉 manifest가 run-level 실행 기록이라면, summary는 site별 운영 부하를 읽는 테이블이다.

## first-run bootstrap
- delta previous snapshot이 없더라도 baseline builder는 실패하지 않는다.
- 이 경우 attention delta builder가 first-run bootstrap으로 동작해서:
  - current attention 전체를 `new_attention` 으로 기록하고,
  - comparison이 끝난 뒤 `panel_day_engine_operator_attention_now_v1_previous.csv` 를 current snapshot으로 쓴다.

그래서 baseline builder는 "이전 snapshot이 아직 없는 첫 실행"에도 안정적으로 진입점 역할을 한다.

## detector change가 아닌 이유
- 이 builder는 detector logic이나 scoring rule을 바꾸지 않는다.
- 이미 있는 operator-facing builders를 순서대로 실행하고, 결과를 다시 읽어 manifest/summary로 묶어 주는 packaging layer일 뿐이다.
