# OPS_PANEL_DAY_ENGINE_OPERATOR_PIPELINE_V1

## 목적

이제 operator stack은 `refresh` 와 `QA` 를 따로 실행하는 수준을 넘어서, 한 번에 끝까지 돌리는 operational entrypoint가 필요합니다.  
`operator_pipeline_v1` 는 다음 순서를 고정해서 실행합니다.

1. selected site refresh
2. operator baseline rebuild
3. refresh QA gate
4. final pipeline manifest 기록

이 패치는 packaging/orchestration only 이며 detector 변경이 아닙니다.

## 실행

기본 전체 site:

```bash
python research/prognostics/build_panel_day_engine_operator_pipeline_v1.py
```

선택 site:

```bash
python research/prognostics/build_panel_day_engine_operator_pipeline_v1.py --sites conalog,gangui
```

## 동작 규칙

- 먼저 `operator_refresh_v1` 를 실행합니다.
- refresh manifest 기준 `baseline_built_flag == 1` 일 때만 `operator_refresh_qa_v1` 를 실행합니다.
- baseline 이 안 만들어졌으면 QA는 건너뛰고 final manifest 에 실패 상태를 남깁니다.

## final_pipeline_pass_flag 해석

- `1`
  - requested site refresh 성공
  - baseline rebuild 성공
  - QA 실행됨
  - QA pass
- `0`
  - 위 조건 중 하나라도 만족하지 못한 상태입니다.

스크립트 종료코드도 여기에 맞춥니다.
- pass면 `0`
- 아니면 `1`

## manifest 해석

`_share/panel_day_engine_operator_pipeline_manifest_v1.csv`
- operator pipeline 전체 상태를 한 줄로 요약합니다.
- refresh 결과, QA 결과, 현재 overall attention 규모를 한 곳에서 확인할 수 있습니다.
- QA를 건너뛴 경우에는 `qa_skip_reason` 으로 이유를 바로 확인할 수 있습니다.
- 운영자는 이 파일만 보고도
  - 지금 pipeline이 정상 종료되었는지
  - 배포 보류가 필요한지
  - attention 규모가 어느 정도인지
  를 바로 판단할 수 있습니다.
