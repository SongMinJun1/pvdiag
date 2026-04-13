# OPS_PANEL_DAY_ENGINE_GPVS_PANEL_ATTACH_AUDIT_V1

## 목적
- 현재 저장 산출물만으로 GPVS reference verdict를 panel level에 직접 붙일 수 있는지 확인한다.
- detector logic 은 바꾸지 않는다.
- 결론은 `가능` 또는 `불가` 한 줄로 닫히도록 만든다.

## 왜 이 audit 이 필요한가
- 기존 panel multiaxis verdict 표에서는 GPVS를 보수적으로 `미부착` 으로 뒀다.
- 이유는 panel key가 있는 stored GPVS artifact가 실제로 있는지, 그리고 current panel table과 겹치는지 아직 formal check가 없었기 때문이다.
- panel table 이 먼저 안정화돼야 `site + panel_id` 기준 overlap 을 정확히 볼 수 있으므로, 이 audit 은 panel table 이후 단계로 둔다.

## 입력
- `_share/panel_day_engine_panel_multiaxis_verdict_v1.csv`
- repo 안 GPV/GPVS 관련 stored artifact / doc / output
  - 예: `_share/gpvs_fault_family_eval_cases.csv`
  - 예: `data/gpvs/out/EXTERNAL_GPVS_BYTYPE_METRICS.csv`
  - 예: `data/gpvs/out/gpvs_window_scores.csv`
  - 예: `docs/reports/gpvs_final_summary.md`

## 판정 기준
- panel attach candidate 파일은 최소한 아래를 만족해야 한다.
  - current panel row 와 연결 가능한 panel key 가 있다.
    - 직접 `panel_id`
    - 또는 explicit recoverable equivalent key
  - panel별 GPVS reference type 을 읽을 수 있는 유형 column 이 있다.
- type-level / aggregate-only 파일은 attach candidate 가 아니다.

## 출력
- `_share/panel_day_engine_gpvs_panel_attach_inventory_v1.csv`
  - GPVS 관련 후보 파일 inventory
  - 각 파일에 대해 granularity, key column, type column, score column, attach candidate 여부를 적는다.
  - attach candidate 파일에는 current panel table 과의 overlap 도 같이 적는다.
- `_share/panel_day_engine_gpvs_panel_attach_feasibility_v1.csv`
  - 정확히 1행
  - `가능` 이면 최선 후보 파일과 overlap 을 적는다.
  - `불가` 면 현재 저장 산출물이 유형수준/집계수준 해석만 가능하다고 적는다.
- `_share/panel_day_engine_gpvs_panel_attach_candidates_v1.csv`
  - attach 가능할 때만 matched panel row 를 쓴다.
  - 불가이면 header-only 빈 파일로 둔다.

## 가능 / 불가의 의미
- `가능`
  - stored artifact 중 하나가 panel key 와 GPVS type 을 함께 가지고 있다.
  - current panel verdict table 과 실제 overlap 이 있어서 partial direct attach 가 가능하다.
  - 다만 current panel 전체를 다 덮지 못할 수 있으므로, 미부착 panel 은 그대로 남는다.
- `불가`
  - 현재 저장 산출물은 유형수준 또는 집계수준 reference 로만 읽을 수 있다.
  - panel multiaxis verdict 에서는 GPVS를 계속 `미부착` 으로 두는 것이 맞다.

## Smoke Test 기준
- builder / smoke script 가 compile 되어야 한다.
- inventory row 가 생성돼야 한다.
- attachable synthetic path 와 non-attachable synthetic path 둘 다 확인해야 한다.
- feasibility 1행이 항상 생성돼야 한다.
- smoke 중 official outputs 는 바뀌면 안 된다.
