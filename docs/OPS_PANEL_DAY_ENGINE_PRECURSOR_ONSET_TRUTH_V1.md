# OPS_PANEL_DAY_ENGINE_PRECURSOR_ONSET_TRUTH_V1

## 목적
- detector gate를 더 만지기 전에, precursor-bearing fault에 대해서만 case-level onset truth를 먼저 고정한다.
- 이 산출물은 다음 단계의 `precursor performance`, `lead-time evaluation`, `non-precursor bucket 비교`의 기준선이 된다.

## 왜 taxonomy가 먼저였는가
- onset truth는 모든 fault를 한 번에 정의하면 해석이 흔들린다.
- 먼저 `fault_taxonomy_v1`에서 `precursor_bearing`, `abrupt_or_no_precursor`, `unknown_needs_review`를 나눠 두어야 precursor onset truth의 적용 대상을 좁힐 수 있다.
- 따라서 이번 단계는 taxonomy에서 precursor-bearing으로 다룰 수 있는 local case만 onset truth 대상으로 삼는다.

## 왜 precursor-bearing fault만 대상으로 제한하는가
- abrupt/no-precursor bucket은 onset이 늦거나 없을 수 있으므로 같은 분모에 두면 precursor recall과 lead-time 해석이 왜곡된다.
- unknown bucket은 onset 정의보다 review가 먼저다.
- 그래서 이번 출력은 `_share/panel_day_engine_local_precursor_eligibility_cases_v1.csv` 중 `precursor_eligible_flag == 1` 인 local case만 사용한다.

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
