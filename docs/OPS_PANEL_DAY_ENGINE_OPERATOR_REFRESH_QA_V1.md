# OPS_PANEL_DAY_ENGINE_OPERATOR_REFRESH_QA_V1

## 목적

refresh가 끝났다고 해서 operator stack이 바로 신뢰 가능한 것은 아닙니다.  
site rerun 성공, baseline rebuild 성공, attention/digest/run summary 상호 일치, 그리고 baseline에 함께 packaging된 discovery preview stack, discovery cluster delta stack, unified digest stack, workflow default stack 일관성까지 확인되어야 운영자가 현재 산출물을 그대로 받아들일 수 있습니다.

`operator_refresh_qa_v1` 는 이 마지막 QA gate를 추가하는 operator-facing 점검 레이어입니다.  
detector 변경이 아니라 refresh 이후 결과물 coherence 검사입니다.

## 입력 / 출력

입력:
- `panel_day_engine_operator_refresh_manifest_v1.csv`
- `panel_day_engine_operator_refresh_site_results_v1.csv`
- `panel_day_engine_operator_baseline_manifest_v1.csv`
- `panel_day_engine_operator_baseline_summary_v1.csv`
- `panel_day_engine_operator_attention_summary_v1.csv`
- `panel_day_engine_operator_digest_summary_v1.csv`
- `panel_day_engine_operator_attention_plus_discovery_cluster_preview_v1.csv`
- `panel_day_engine_operator_attention_plus_discovery_cluster_preview_summary_v1.csv`
- `panel_day_engine_operator_secondary_discovery_cluster_delta_v1.csv`
- `panel_day_engine_operator_secondary_discovery_cluster_delta_summary_v1.csv`
- `panel_day_engine_operator_unified_digest_v1.csv`
- `panel_day_engine_operator_unified_digest_summary_v1.csv`
- `panel_day_engine_operator_workflow_default_v1.csv`
- `panel_day_engine_operator_workflow_default_summary_v1.csv`
- `panel_day_engine_operator_run_summary_v1.csv`
- optional watchlist summary

출력:
- `_share/panel_day_engine_operator_refresh_qa_report_v1.csv`
- `_share/panel_day_engine_operator_refresh_qa_summary_v1.csv`

## 체크 종류

Hard fail:
- 필수 입력 파일 존재 여부
- 모든 requested site 성공 여부
- baseline rebuild 여부
- attention / digest / watchlist / site aggregate 간 count consistency
- baseline manifest 와 discovery cluster preview summary 간 count consistency
- baseline manifest 와 discovery cluster delta summary 간 count consistency
- baseline manifest 와 unified digest summary 간 count consistency
- baseline manifest 와 workflow default summary 간 count consistency
- cluster preview overall count = baseline attention + discovery cluster count consistency
- cluster preview per-site sum = cluster preview overall consistency
- cluster delta per-site current/changed/new/dropped sum = cluster delta overall consistency
- unified digest overall count = baseline attention + discovery cluster count consistency
- unified digest per-site digest/queue/watch/cluster/changed sum = unified digest overall consistency
- workflow default overall count = unified digest overall count consistency
- workflow default per-site workflow/queue/watch/cluster/changed sum = workflow default overall consistency
- refresh 시간 순서와 duration 유효성

Soft warning:
- `queue_count > 20`
- `attention_count > 50`
- `watch_now_count > 40`
- `backlog_count / max(queue_count, 1) > 500`
- `cluster_preview_count > 35`
- `secondary_value_cluster_count > 10`
- `unified_digest_count > 30`
- `workflow_default_count > 30`

soft warning은 운영자가 바로 눈여겨볼 신호지만, detector 또는 refresh 자체 실패로 간주하지는 않습니다.

정리:
- hard fail은 refresh 결과물을 운영 기준으로 바로 신뢰하면 안 되는 상태를 뜻합니다.
- soft warn은 규모나 부하가 커졌다는 신호이며, QA gate 자체는 통과할 수 있습니다.

## qa_pass_flag 해석

- `qa_pass_flag = 1`
  - hard fail이 하나도 없다는 뜻입니다.
  - warning은 있을 수 있습니다.
- `qa_pass_flag = 0`
  - 최소 하나 이상의 hard fail이 있어 현재 refresh 산출물을 운영 기준으로 바로 신뢰하면 안 됩니다.

## 사용 이유

- refresh success alone is not enough:
  - site 실행은 성공했는데 summary가 서로 어긋날 수 있습니다.
- operator stack now needs a QA gate:
  - baseline/digest/delta 레이어가 쌓였고, 이제 secondary discovery cluster preview, discovery cluster delta, unified digest, workflow default까지 baseline packaging에 같이 들어오므로 상호 consistency 확인이 필요해졌습니다.
- hard fail vs soft warning 분리:
  - 운영 불가 상태와 단순 규모 이상징후를 구분해 보여 주기 위함입니다.

## 왜 discovery preview, cluster delta, unified digest, workflow default까지 QA에 포함하는가

- baseline orchestrator는 이제 primary attention stack만이 아니라 supplemental discovery cluster preview stack, discovery cluster delta stack, unified digest stack, workflow default stack도 함께 재생성합니다.
- workflow default는 detector/scorer 결과를 새로 만드는 것이 아니라, policy audit을 거쳐 선택된 기본 operator workflow를 unified digest 위에 공식 operational view로 고정한 consumer-facing layer입니다.
- 따라서 QA gate도 baseline manifest가 기록한 discovery preview / cluster delta / unified digest / workflow default count와 실제 summary가 서로 맞는지 검증해야 합니다.
- 이 검사는 detector/scorer 변경이 아니라, refresh 결과 packaging coherence를 점검하는 운영 QA입니다.

정리:
- hard fail
  - preview/delta/unified digest/workflow default 필수 파일 누락
  - baseline manifest 와 preview/delta/unified digest/workflow default summary 불일치
  - preview/delta/unified digest/workflow default per-site 합과 overall 불일치
- soft warn
  - queue/watch_now/attention/cluster preview/unified digest/workflow default 규모 이상치

즉 이 QA는 operator baseline stack과 그 위에 붙은 supplemental discovery preview/delta/unified digest/workflow default stack이 함께 coherent 한지 보는 gate일 뿐, detector/scorer를 바꾸는 로직은 아닙니다.
