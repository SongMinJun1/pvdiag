# OPS PANEL DAY ENGINE OPERATOR RELEASE GATE V1

## 목적

`build_panel_day_engine_operator_release_gate_v1.py` 는 현재 operator stack에 대해 하나의 명시적 release/stability gate 엔트리포인트를 제공합니다. 이 gate는 routine refresh용 엔트리포인트가 아니라, 현재 packaging이 실제 운영 release 후보로서 안정적인지 확인하는 최종 점검용입니다.

## 왜 release gate가 필요한가

operator stack은 이미 baseline, discovery preview, cluster delta, unified digest, workflow default까지 packaging되어 있습니다. 하지만 packaging 완료만으로는 운영 release 준비가 끝났다고 보기 어렵습니다. 현재 run이 정상 통과했는지뿐 아니라, 같은 입력으로 연속 실행했을 때 2차 run에서 불필요한 변화가 생기지 않는지도 함께 봐야 release 안정성을 판단할 수 있습니다.

## 왜 idempotence를 여기서만 포함하는가

idempotence audit은 전체 pipeline을 두 번 연속 실행하므로 routine refresh마다 항상 붙이기에는 비용이 큽니다. 대신 release/stability gate에서는 이 비용을 감수하고, 배포 직전 상태가 steady-state인지 확인합니다. 즉:

- routine refresh: 최신 operator outputs 재생성
- release gate: 최신 outputs 재생성 + back-to-back steady-state 검증

## 실행 순서

release gate는 같은 site set에 대해 아래 순서로 동작합니다.

1. `build_panel_day_engine_operator_pipeline_v1.py --sites ...`
2. pipeline manifest의 `final_pipeline_pass_flag == 1` 이고 pipeline command가 성공(exit 0)했을 때만
   `build_panel_day_engine_operator_pipeline_idempotence_audit_v1.py --sites ...`
3. 결과를 `_share/panel_day_engine_operator_release_gate_manifest_v1.csv` 한 줄에 기록

pipeline 단계가 실패하면 idempotence는 생략되고, manifest의 `note_ko` 에 그 이유가 남습니다.

## manifest 해석

출력 파일:

- `_share/panel_day_engine_operator_release_gate_manifest_v1.csv`

주요 필드:

- `pipeline_executed_flag`: release gate가 pipeline entrypoint를 호출했는지
- `pipeline_pass_flag`: pipeline manifest 기준 통과 여부
- `idempotence_executed_flag`: pipeline 성공 후 idempotence audit까지 실행했는지
- `idempotence_pass_flag`: idempotence summary 기준 통과 여부
- `final_release_gate_pass_flag`: 최종 release gate 통과 여부
- `final_recommended_exit_code`: gate 전체 종료 코드 추천값

`final_release_gate_pass_flag = 1` 은 아래를 모두 만족할 때만 참입니다.

- pipeline pass
- idempotence audit executed
- idempotence pass

즉, 현재 operator stack이 "한 번 정상 동작" 하는 것뿐 아니라 "연속 재실행에서도 불필요한 변화 없이 안정적" 이라는 뜻입니다.

## note_ko 해석

대표 상태:

- `operator stack release gate 통과`
- `pipeline 실패로 idempotence 생략`
- `idempotence 미통과로 release 보류`

이 manifest는 detector/scorer를 바꾸지 않습니다. 현재 operator stack의 packaging 결과를 release 관점에서 묶어 보여주는 운영용 gate입니다.
