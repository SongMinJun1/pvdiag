# OPS_PANEL_DAY_ENGINE_PRECURSOR_ONSET_TRUTH_V1

## 목적
- detector gate를 더 만지기 전에, precursor-bearing fault에 대해서만 case-level onset truth를 먼저 고정한다.
- 이 산출물은 다음 단계의 `precursor performance`, `lead-time evaluation`, `non-precursor bucket 비교`의 기준선이 된다.
- benchmark reset 이후에는 이 파일이 audited event semantics에서 재구성한 precursor benchmark truth 의 직접 기준선이 된다.

## 왜 taxonomy가 먼저였는가
- onset truth는 모든 fault를 한 번에 정의하면 해석이 흔들린다.
- 먼저 `fault_taxonomy_v1`에서 `precursor_bearing`, `abrupt_or_no_precursor`, `unknown_needs_review`를 나눠 두어야 precursor onset truth의 적용 대상을 좁힐 수 있다.
- 따라서 이번 단계는 taxonomy에서 precursor-bearing으로 다룰 수 있는 local case만 onset truth 대상으로 삼는다.

## benchmark reset 이후 무엇이 바뀌었는가
- precursor benchmark truth는 audited event semantics를 기준으로 3 panel로 다시 고정한다.
- 현재 precursor benchmark positive는 아래 3 panel이다.
- `7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0`
- `70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4`
- `c42997a6-5881-47e7-9035-7de8a2673b54.1.1`
- 즉, 이전 support 2 benchmark는 더 이상 쓰지 않는다.
- 특히 `c42997a6-5881-47e7-9035-7de8a2673b54.1.1` 은 사건유형 `전조형 고장`, 최종고장양상 `급격 종료`로 해석되며 precursor benchmark에 포함된다.

## onset 날짜는 셋으로 나눠 읽는다
- 이 파일에서 onset 날짜는 이제 한 가지 뜻으로만 읽지 않는다.
- `operational_first_precursor_detected_date`
  - 운영상 실제로 첫 precursor marker가 잡힌 날짜다.
  - 가장 이른 marker 날짜를 그대로 둔다.
- `interpretive_precursor_onset_date`
  - re-audit에서 retrospective하게 본 사건 해석 onset 이다.
  - `panel_date_reaudit_working.csv` 의 `retrospective_onset_date` 를 쓴다.
- `benchmark_precursor_onset_date`
  - step3 benchmark에서 anchor로 쓰는 precursor onset 이다.
  - 현재 `preferred_precursor_onset_date` 와 같은 뜻으로 유지한다.
- 즉 운영 detection onset, 사건 해석 onset, benchmark onset은 서로 다를 수 있다.
- `c42997a6-5881-47e7-9035-7de8a2673b54.1.1` 예시는 아래처럼 읽는다.
  - interpretive onset = `2025-01-20`
  - operational detection = `2025-02-20`
  - benchmark onset = `2025-03-18`

## onset ladder 정의
- bounded window는 `fault_start_date - 30d` 부터 `fault_start_date` 전날까지다.
- ladder marker는 최소한 아래 7개를 기록한다.
- `first_cond_evt`
- `first_cond_evt_corroborated`
- `first_signalcount2`
- `first_pre_ews`
- `first_ews_warning`
- `first_pre_alarm`
- `preferred_precursor_onset`

## 왜 first alarm day 대신 episode start를 쓰는가
- operator나 scorer 관점에서 중요한 것은 “경보가 처음 세게 뜬 날”보다 “fault 전조 episode가 실제로 시작된 시점”이다.
- 이번 로직은 `cond_evt` day를 1일 gap tolerance로 episode로 묶고, fault 직전의 최신 episode를 선택한다.
- 그 episode 안에서 alarm/warning, corroboration, signal_count>=2가 있었는지를 본 뒤, onset 자체는 episode 시작일로 잡는다.
- 이렇게 해야 precursor lead-time이 alarm 시스템의 임계값 설정에 덜 종속된다.

## confidence 해석
- `strong`
- 선택된 episode 안에 `pre_alarm` 또는 `ews_warning` 가 있어 onset을 강하게 지지하는 경우
- `medium`
- alarm은 없지만 `cond_evt_corroborated` 또는 `signal_count>=2` 가 있어 onset을 중간 강도로 지지하는 경우
- `weak`
- cond_evt only episode이거나 detectable episode 자체가 없어 weak truth로만 기록하는 경우

## 다음 단계 연결
- precursor performance evaluation:
- `preferred_precursor_onset_date` 와 ladder marker를 기준으로 “fault 전 얼마 전부터 precursor를 잡았는지”를 측정한다.
- lead-time evaluation:
- `lead_days_from_preferred_onset_to_fault_start` 를 기준으로 precursor-bearing bucket 안에서 lead 분포를 평가한다.
- non-precursor fault detection/classification performance:
- 이번 onset truth 파일에 없는 abrupt/no-precursor bucket은 별도 분모로 두고 detection/classification 평가를 분리한다.

## 해석 원칙
- 이 파일은 detector logic 변경이 아니라 truth/evaluation layer 정의다.
- onset truth가 비어 있는 case는 `no_detectable_precursor_episode` 로 남기고, 억지로 positive onset을 부여하지 않는다.
- benchmark reporting 에서는 이제 이 파일의 support 3을 그대로 precursor benchmark support로 읽는다.
