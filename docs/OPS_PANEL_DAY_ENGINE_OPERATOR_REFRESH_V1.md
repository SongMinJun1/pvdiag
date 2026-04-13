# OPS_PANEL_DAY_ENGINE_OPERATOR_REFRESH_V1

## 목적

`operator_baseline_v1` 는 operator artifact packaging 문제를 풀었지만, 실제 운영에서는 먼저 site 재실행이 필요합니다.  
`operator_refresh_v1` 는 이 앞단을 묶어서 다음 순서로 한 번에 갱신합니다.

1. 요청한 site 재실행
2. 모든 site 성공 시 operator baseline 재빌드
3. refresh manifest / site 결과 기록

이 패치는 detector 변경이 아니라 operator-facing orchestration 추가입니다.

## 실행

기본 전체 site:

```bash
python research/prognostics/build_panel_day_engine_operator_refresh_v1.py
```

선택 site만 재실행:

```bash
python research/prognostics/build_panel_day_engine_operator_refresh_v1.py --sites conalog,gangui
```

## 동작 규칙

- site runner는 요청 순서대로 모두 실행합니다.
- 하나라도 실패하면 baseline builder는 실행하지 않습니다.
- 부분 실패 상태에서도 `site_results` 와 `manifest` 는 남겨서 어떤 site에서 멈췄는지 바로 볼 수 있게 합니다.
- baseline 은 site refresh가 모두 끝난 뒤 마지막에만 실행합니다.

이 순서를 고정한 이유는 partial site 결과를 baseline에 섞지 않기 위해서입니다.

## 산출물 해석

`_share/panel_day_engine_operator_refresh_site_results_v1.csv`
- site별 실행 로그입니다.
- `success_flag`, `return_code`, `error_message` 로 실패 지점을 바로 확인합니다.

`_share/panel_day_engine_operator_refresh_manifest_v1.csv`
- 이번 refresh 전체 결과를 한 줄로 요약합니다.
- `baseline_built_flag=1` 이면 requested site 전부 성공 후 baseline까지 진행된 상태입니다.
- `baseline_built_flag=0` 이면 site 단계에서 partial failure가 있었고 baseline은 의도적으로 건너뛴 상태입니다.
