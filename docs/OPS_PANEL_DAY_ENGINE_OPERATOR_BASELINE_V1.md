# OPS_PANEL_DAY_ENGINE_OPERATOR_BASELINE_V1

## 목적
- operator layer가 이제 `run consolidation -> attention_now -> attention_delta -> digest` 순서로 비교적 안정된 baseline을 갖추었기 때문에, 전체 operator-facing artifact를 한 번에 다시 만드는 entrypoint를 고정한다.
- 여기에 더해 secondary discovery value panel -> cluster rollup -> attention+discovery preview -> cluster delta -> unified digest까지 붙이더라도 baseline attention 자체를 흔들지 않고 side-by-side supplemental layer와 consumer-facing digest view로 packaging할 수 있는 상태가 됐다.
- 이 단계는 detector change가 아니라 packaging/orchestration layer다.

## 왜 이제 orchestrate할 수 있는가
- daily flood를 run/episode 단위로 접었고,
- queue / backlog / watchlist / watch_now panel / attention_now 구조가 정리됐고,
- attention delta까지 붙어서 operator가 "무엇이 바뀌었는가"를 별도로 읽을 수 있게 됐다.
- 그리고 digest까지 붙어서 "지금 볼 것 + 직전 대비 변화"를 한 파일에서 읽을 수 있게 됐다.
- 또 secondary discovery lane은 run-level / panel-level / cluster-level audit을 거치며, baseline 밖 hidden value를 압축된 cluster preview로 보여 줄 만큼 operational utility가 있다는 근거가 생겼다.
- 그리고 cluster preview도 refresh마다 전체를 다시 읽기보다, 무엇이 새로 생기고 사라지고 바뀌었는지를 delta로 읽을 수 있는 상태가 됐다.
- 마지막으로 baseline attention과 secondary discovery cluster preview를 current-state 기준으로 한 파일에서 읽는 unified digest가 생기면서, operator가 여러 preview/delta artifact를 직접 합쳐 보지 않아도 되는 consumer-facing view가 마련됐다.
- 그리고 attention policy audit을 거쳐 `baseline_plus_discovery_cluster` 가 기본 operator workflow로 충분히 안정적이라는 근거가 생겨, unified digest builder가 이 기본 workflow artifact까지 함께 재생성하는 상태가 됐다.

즉 method search용 실험 artifact가 아니라, current operator baseline을 재생성하는 고정 순서를 둘 만한 시점이 됐다.

## baseline builder가 하는 일
`build_panel_day_engine_operator_baseline_v1.py` 는 아래 여덟 builder를 순서대로 실행한다.

1. `research/prognostics/build_panel_day_engine_operator_run_consolidation_v1.py`
2. `research/prognostics/build_panel_day_engine_operator_attention_delta_v1.py`
3. `research/prognostics/build_panel_day_engine_operator_digest_v1.py`
4. `research/prognostics/build_panel_day_engine_operator_secondary_discovery_v1.py`
5. `research/prognostics/build_panel_day_engine_operator_secondary_discovery_cluster_rollup_v1.py`
6. `research/prognostics/build_panel_day_engine_operator_attention_plus_discovery_preview_v1.py`
7. `research/prognostics/build_panel_day_engine_operator_secondary_discovery_cluster_delta_v1.py`
8. `research/prognostics/build_panel_day_engine_operator_unified_digest_v1.py`

이 순서가 필요한 이유:
- attention delta는 current attention artifact를 입력으로 쓰기 때문에,
- run consolidation이 먼저 attention baseline을 다시 만든 뒤,
- 그 다음 delta가 previous snapshot과 비교해야 한다.
- digest는 current attention row에 latest delta context를 붙여 읽기 때문에,
  delta가 먼저 끝난 뒤에만 정상적으로 생성할 수 있다.
- secondary discovery는 current run feature/scores와 complement guardrail을 바탕으로 hidden value lane을 다시 만들고,
- cluster rollup은 그 value panel들을 site-time cluster로 압축하며,
- attention+discovery preview는 baseline attention과 cluster preview를 side-by-side preview로 합치고,
- cluster delta는 current cluster rollup과 previous cluster snapshot을 비교해 operator가 reread 없이 바뀐 cluster만 볼 수 있게 하며,
- unified digest는 맨 마지막에 baseline attention current rows와 secondary discovery cluster preview current rows를 두 delta context와 함께 한 파일로 다시 포장한다.
- unified digest builder는 같은 current-state rows를 바탕으로, 선택된 기본 workflow policy를 반영한 `panel_day_engine_operator_workflow_default_v1.csv` / summary도 함께 기록한다.

digest builder는 baseline manifest/summary를 입력으로도 읽기 때문에, baseline orchestrator는
1. run consolidation + attention delta 실행
2. provisional baseline manifest/summary 기록
3. digest 실행
4. secondary discovery / cluster rollup / preview / cluster delta / unified digest stack 실행
5. digest-aware + discovery-preview-aware + discovery-delta-aware + unified-digest-aware final baseline manifest/summary로 overwrite
   그리고 이 final manifest/summary에는 workflow default summary에서 읽은 운영용 count도 함께 노출한다.
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
- secondary discovery 계열
  - `panel_day_engine_operator_secondary_discovery_v1.csv`
  - `panel_day_engine_operator_secondary_discovery_value_v1.csv`
  - `panel_day_engine_operator_secondary_discovery_value_panels_v1.csv`
  - `panel_day_engine_operator_secondary_discovery_value_panels_summary_v1.csv`
  - `panel_day_engine_operator_secondary_discovery_cluster_rollup_v1.csv`
  - `panel_day_engine_operator_secondary_discovery_cluster_rollup_summary_v1.csv`
- attention+discovery preview 계열
  - `panel_day_engine_operator_attention_plus_discovery_preview_v1.csv`
  - `panel_day_engine_operator_attention_plus_discovery_preview_narrow_v1.csv`
  - `panel_day_engine_operator_attention_plus_discovery_cluster_preview_v1.csv`
  - `panel_day_engine_operator_attention_plus_discovery_cluster_preview_summary_v1.csv`
- discovery cluster delta 계열
  - `panel_day_engine_operator_secondary_discovery_cluster_delta_v1.csv`
  - `panel_day_engine_operator_secondary_discovery_cluster_delta_summary_v1.csv`
  - `panel_day_engine_operator_secondary_discovery_cluster_rollup_v1_previous.csv`
- unified digest 계열
  - `panel_day_engine_operator_unified_digest_v1.csv`
  - `panel_day_engine_operator_unified_digest_summary_v1.csv`
  - `panel_day_engine_operator_workflow_default_v1.csv`
  - `panel_day_engine_operator_workflow_default_summary_v1.csv`

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
  - discovery value panel count
  - discovery cluster count
  - cluster preview count
  - cluster preview linked-ref counts
  - cluster delta current/changed/new/dropped count
  - cluster delta representative-changed / linked-ref-changed count
  - unified digest current count
  - unified digest queue/watch/cluster split
  - unified digest changed attention/cluster count
  - workflow default item count
  - workflow default queue/watch/cluster split
  - workflow default changed / primary attention / supplemental discovery / linked ref count
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
  - discovery value panel count
  - discovery cluster count
  - cluster preview count
  - cluster preview secondary cluster count
  - cluster delta current/changed/new/dropped count
  - unified digest current count
  - unified digest queue/watch/cluster split
  - unified digest changed count
  - workflow default item count
  - workflow default queue/watch/cluster split
  - workflow default changed count
를 한 표에서 보게 한다.

즉 manifest가 run-level 실행 기록이라면, summary는 site별 운영 부하를 읽는 테이블이다.

## 왜 cluster preview, cluster delta, unified digest를 같이 package하는가
- panel-level secondary discovery는 retrospective value가 있었지만, 같은 site에서 비슷한 시점의 hidden value panel이 여러 줄로 보이면서 operator load와 site skew가 남아 있었다.
- cluster rollup은 이 hidden value panel들을 site-time cluster로 접어, baseline attention을 대체하지 않으면서도 "보조로 볼 가치가 있는 묶음"을 더 좁은 형태로 제공한다.
- 그리고 cluster delta는 이 cluster preview를 매 refresh 전체 reread하지 않고도, 무엇이 새로 생기고 사라지고 바뀌었는지를 incremental feed로 볼 수 있게 한다.
- 그리고 unified digest는 baseline attention current rows와 discovery cluster preview current rows를 delta context와 함께 한 파일에서 읽게 해, operator가 primary baseline과 supplemental discovery layer를 별도 파일로 조합하지 않아도 되게 한다.
- 그리고 workflow default는 그 unified digest를 source artifact로 삼아, policy audit이 고른 기본 operator workflow를 current-state 기준 공식 operational view로 고정한다.
- 그래서 baseline orchestration은 이제 primary attention stack뿐 아니라 supplemental discovery cluster preview / cluster delta / unified digest stack도 함께 재생성한다.
- 이번 패치는 그 workflow default를 새로 만드는 것이 아니라, unified digest builder가 이미 재생성한 workflow default summary를 baseline manifest/summary에 같이 노출하는 packaging enrichment다.

중요한 점:
- baseline attention (`queue_run`, `watch_now_panel` 등)은 여전히 primary operator baseline이다.
- discovery cluster preview와 discovery cluster delta는 그 baseline을 대체하지 않고, baseline 바깥 hidden value를 side-by-side로 보여 주는 supplemental preview/delta layer다.
- unified digest 역시 baseline replacement가 아니라, 기존 baseline attention과 supplemental discovery cluster layer를 소비자 관점에서 다시 묶어 보여 주는 current-state view다.
- workflow default 역시 detector/scorer output이 아니라, 위 current-state layer들 위에서 읽기 좋은 기본 operator workflow를 consumer-facing으로 고정한 operational view다.

## first-run bootstrap
- delta previous snapshot이 없더라도 baseline builder는 실패하지 않는다.
- 이 경우 attention delta builder가 first-run bootstrap으로 동작해서:
  - current attention 전체를 `new_attention` 으로 기록하고,
  - comparison이 끝난 뒤 `panel_day_engine_operator_attention_now_v1_previous.csv` 를 current snapshot으로 쓴다.
- cluster previous snapshot이 없더라도 baseline builder는 실패하지 않는다.
- 이 경우 discovery cluster delta builder가 first-run bootstrap으로 동작해서:
  - current discovery cluster 전체를 `new_cluster` 로 기록하고,
  - comparison이 끝난 뒤 `panel_day_engine_operator_secondary_discovery_cluster_rollup_v1_previous.csv` 를 current snapshot으로 쓴다.

그래서 baseline builder는 "이전 snapshot이 아직 없는 첫 실행"에도 안정적으로 진입점 역할을 한다.

## detector change가 아닌 이유
- 이 builder는 detector logic이나 scoring rule을 바꾸지 않는다.
- 이미 있는 operator-facing builders를 순서대로 실행하고, 결과를 다시 읽어 manifest/summary로 묶어 주는 packaging layer일 뿐이다.
- 이번 확장도 baseline attention 규칙을 바꾸는 것이 아니라, 이미 승인된 discovery preview/delta stack, unified digest consumer view, 그리고 workflow default operational view의 count를 baseline manifest/summary에 함께 노출하는 packaging change다.
