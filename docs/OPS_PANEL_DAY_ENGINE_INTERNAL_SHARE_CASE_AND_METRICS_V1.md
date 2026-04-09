# OPS_PANEL_DAY_ENGINE_INTERNAL_SHARE_CASE_AND_METRICS_V1

## 목적
- 내부 공유용으로 바로 쓸 수 있는 두 가지를 한 번에 만든다.
  - AE/DTW 사례 panel 들의 원인 분석, 무가시형 여부, 개선안
  - 전조 감지 최신 성능 요약과 운영 workflow 상태

## 왜 별도 pack 이 필요한가
- 지금 필요한 답은 이론 설명보다도 “이 panel 들은 왜 잡혔나”, “무가시형인가”, “최신 성능을 지금 어떻게 말해야 하나” 에 가깝다.
- 그래서 기존 project evaluation / freeze / workflow 산출물을 다시 묶어, 내부 공유용 사례표 + 한 장 성능표 + 짧은 markdown brief 로 정리한다.

## 사례 판정 로직
- `무가시형_판정` 은 heuristic 이다.
- 기본 원칙:
  - AE/DTW/cond_evt trigger 는 있지만 final fault 일수는 0이고, 전기/output drop proxy 도 약하면 `무가시형_가능성_높음`
  - final fault 일수가 있거나 전기/output drop proxy 가 강하면 `가시형_가능성_있음`
  - 그 사이면 `혼합_또는_불충분`
- 여기서 proxy 는 `mid_ratio`, `mid_v_ratio`, `v_drop`, `recon_error` 의 현재 산출물 값으로만 본다.
- optional retrospective 파일이 있으면 `원인_가설_ko` 문장만 보강하고, detector/scorer 판정을 바꾸지는 않는다.

## 주된 이상유형 추정
- `panel_local_hidden_precursor_like`
  - panel-local hidden precursor 가능성이 높은 경우
- `recurring_monitor_like`
  - 반복 monitor lane 성격이 강한 경우
- `common_cause_or_context_like`
  - 같은 날 site breadth 가 커 공통 원인/문맥성 가능성이 큰 경우
- `output_normal_nuisance_like`
  - trigger 는 있지만 output/electrical proxy 는 거의 정상인 경우
- `unclear`
  - 현재 자료만으로 단정이 어려운 경우

## 최신 성능 표 해석
- `전조형 고장`
  - current freeze pack 이 고른 step3 대표 marker 를 사용한다.
  - 선행시간은 onset/performance summary 에 있는 최신 중앙값/범위를 그대로 쓴다.
  - 표본이 작으므로 탐색적으로만 읽는다.
- `급작 고장`
  - current freeze pack 이 고른 step4 abrupt 대표 기준을 사용한다.
  - 선행시간은 의미가 약하므로 비워 둔다.
- `common-cause routing`
  - step4 common-cause 대표 기준을 사용한다.
  - descriptive / exploratory 용도로만 읽는다.
- `운영 workflow`
  - policy recommendation 이 고른 현재 운영 workflow 를 쓴다.
  - precision/recall/F1 는 이미 retrospective proxy row 로 존재하는 경우에만 넣는다.

## brief markdown 사용법
- `_share/panel_day_engine_internal_share_brief_v1.md` 는 정확히 세 섹션만 둔다.
  - `1. AE/DTW 사례 요약`
  - `2. 최신 성능 한 줄 요약`
  - `3. 지금 당장 말해도 되는 것 / 말하면 안 되는 것`
- 문장 길이는 짧게 유지하고, 내부 공유에서 바로 붙여 넣을 수 있게 이론 설명은 최소화한다.

## 주의
- 이 문서는 detector/scorer 변경안이 아니다.
- internal-share / case review / 최신 성능 설명용 pack 이다.
