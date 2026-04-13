# OPS_PANEL_DAY_ENGINE_PRECURSOR_PERFORMANCE_AUDIT_V1

## 목적
- `eval_bucket_v2 == precursor_bearing_detectable_now` 인 fault case만 대상으로 precursor performance를 다시 잰다.
- 기준 anchor는 `preferred_precursor_onset_date` 이다.
- 이 단계는 detector logic을 바꾸지 않고, 새 taxonomy와 onset truth를 evaluation layer에 연결하는 audit이다.
- benchmark reset 이후에는 precursor benchmark positive support 3을 직접 받아서 step3 성능을 다시 계산한다.

## 왜 detectable-now precursor-bearing case만 쓰는가
- literature crosswalk 이후에도 모든 family가 현재 `panel_day_engine` daily electrical pipeline의 책임 분모는 아니다.
- step 3은:
  - precursor-capable이고
  - current pipeline이 실제로 감지 가능하며
  - branch에서 onset truth까지 확보된
  case만 대상으로 해야 해석이 흔들리지 않는다.
- 그래서 이번 audit는 `eval_bucket_v2 == precursor_bearing_detectable_now` 만 사용한다.

## benchmark reset 이후 기준
- precursor benchmark positive는 audited event semantics에서 다시 고정한 3 panel이다.
- `7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0`
- `70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4`
- `c42997a6-5881-47e7-9035-7de8a2673b54.1.1`
- 따라서 old support 2 precursor benchmark wording은 obsolete 다.
- `c42997a6-5881-47e7-9035-7de8a2673b54.1.1` 은 precursor benchmark 에 포함되고 pure abrupt benchmark 에는 들어가지 않는다.

## 왜 preferred onset truth가 anchor인가
- `first_pre_alarm` 같은 downstream marker만 anchor로 쓰면 전조 episode의 실제 시작보다 항상 늦은 기준을 쓰게 된다.
- 이번 branch는 이미 `preferred_precursor_onset_date` 를:
  - alarm-backed episode start
  - corroborated/signal-backed episode start
  - evt-only episode start
  중 하나로 정리했다.
- 따라서 marker 비교 기준은 “fault 전 알람이 언제 떴는가”가 아니라 “truth로 본 precursor onset을 얼마나 빨리/정확히 잡았는가”가 되어야 한다.

## onset 날짜를 섞지 않는 원칙
- 이 step3 audit의 benchmark metric은 계속 `benchmark_precursor_onset_date` 를 anchor로 쓴다.
- 하지만 cases output에는 아래 세 날짜를 함께 실어 혼선을 막는다.
  - `operational_first_precursor_detected_date`
  - `interpretive_precursor_onset_date`
  - `benchmark_precursor_onset_date`
- 여기서 benchmark metric 자체는 바꾸지 않는다.
- 즉 숫자는 그대로 두고, 사람이 읽을 때 operational detection 과 interpretive onset 을 benchmark onset 과 섞지 않게 만든다.
- `c42997a6-5881-47e7-9035-7de8a2673b54.1.1` 은:
  - operational detection = `2025-02-20`
  - interpretive onset = `2025-01-20`
  - benchmark onset = `2025-03-18`
  로 분리해서 읽는다.

## 왜 pre_alarm-only 평가는 불충분한가
- `pre_alarm` 는 운영적으로 강한 marker지만, precursor detection chain에서 가장 뒤에 있다.
- `pre_alarm` 만 보면:
  - 앞선 `cond_evt`
  - corroborated cond_evt
  - signal_count>=2
  - `pre_ews`
  신호가 이미 onset에 더 가깝게 나타났는지를 놓치게 된다.
- 그래서 이번 audit는 marker별로:
  - available rate
  - lead to fault
  - preferred onset 대비 capture gap
  를 함께 본다.

## onset capture class 해석
- `exact_or_earlier`
  - marker가 preferred onset과 같거나 더 이른 시점에 존재
- `within_3d_late`
  - preferred onset보다 1~3일 늦음
- `within_7d_late`
  - 4~7일 늦음
- `late_over_7d`
  - 8일 이상 늦음
- `missing`
  - 해당 marker가 case window에서 없었음

## step 4와의 연결
- 이번 step 3 결과는 precursor-bearing detectable-now bucket 안에서만 marker 품질을 비교한다.
- step 4에서는:
  - `abrupt_or_no_precursor_now`
  - `non_panel_or_common_cause`
  bucket을 따로 분리해서
  - non-precursor fault detection/classification
  - common-cause/system-level detection
  성능을 별도로 해석한다.

즉 이번 파일은 “현재 pipeline이 precursor-bearing 분모에서 무엇을 얼마나 빨리 잡는가”를 먼저 고정하는 용도다.
