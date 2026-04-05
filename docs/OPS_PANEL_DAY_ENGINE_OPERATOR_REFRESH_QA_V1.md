# OPS_PANEL_DAY_ENGINE_OPERATOR_REFRESH_QA_V1

## 목적

refresh가 끝났다고 해서 operator stack이 바로 신뢰 가능한 것은 아닙니다.  
site rerun 성공, baseline rebuild 성공, attention/digest/run summary 상호 일치까지 확인되어야 운영자가 현재 산출물을 그대로 받아들일 수 있습니다.

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
- refresh 시간 순서와 duration 유효성

Soft warning:
- `queue_count > 20`
- `attention_count > 50`
- `watch_now_count > 40`
- `backlog_count / max(queue_count, 1) > 500`

soft warning은 운영자가 바로 눈여겨볼 신호지만, detector 또는 refresh 자체 실패로 간주하지는 않습니다.

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
  - baseline/digest/delta 레이어가 쌓이면서 상호 consistency 확인이 필요해졌습니다.
- hard fail vs soft warning 분리:
  - 운영 불가 상태와 단순 규모 이상징후를 구분해 보여 주기 위함입니다.
