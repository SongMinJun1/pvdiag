# OPS_PANEL_DAY_ENGINE_LOCAL_PRECURSOR_GATE_PERSISTENCE_V1

## 목적
- `panel_day_engine` 안에 이미 있는 local precursor logic를 바꾸지 않고, 지금까지 숨겨져 있던 gate state를 helper sidecar로 남긴다.
- canonical `panel_day_core.csv` 계약은 그대로 유지한다.
- 이후 local precursor eligibility / decision-path audit가 "무슨 gate에서 멈췄는지"를 직접 볼 수 있게 만든다.

## 왜 필요한가
- 최근 local precursor eligibility / cohort / miss audit까지 진행한 결과, 문제의 핵심은 local precursor logic의 부재가 아니라 decision path visibility 부족이었다.
- 지금까지는 `_share/panel_day_engine_local_precursor_shadow_v1.csv` 에서 `ews_warning / prefault_B / pre_alarm` 일부만 간접 복원했다.
- 하지만 다음 질문에는 답하기 어려웠다.
  - `data_bad` 가 `pre_ews` 를 막았는가?
  - `signal_count` 를 이루는 `cond_var / cond_evt / cond_dtw / cond_hs` 중 무엇이 실제로 켜졌는가?
  - `pre_ews` 가 실제로 켜졌는가?
  - `ews_warning` 가 연속성(`ews_runlen`) 또는 suppression gate에서 꺼졌는가?
  - `site_event_soft/hard` 나 `group_off_date` suppression 이 활성화됐는가?
  - `prefault_B` 는 어느 조건에서 실패했는가?
  - `pre_alarm` 은 AE/DTW/HS escalation 중 무엇이 부족했는가?

## 무엇을 추가하는가
- site run마다 새 helper sidecar:
  - `data/<site>/out/ae_simple_local_precursor_gate_daily.csv`

이 파일은 panel-day 단위로 아래 state를 남긴다.
- `data_bad`
- `cond_var`
- `cond_evt`
- `cond_dtw`
- `cond_hs`
- `pre_ews`
- `signal_count`
- `ews_runlen`
- `ews_warning`
- `site_event_soft`
- `site_event_hard`
- `group_off_date`
- `prefault_B`
- `pre_alarm`
- `prefault_cond_mid`
- `prefault_cond_ae`
- `prefault_cond_dtw`
- `prefault_cond_ews`
- `prealarm_cond_ae_mid_or_hi`
- `prealarm_cond_dtw_mid_or_hi`
- `prealarm_cond_hs_mid_or_hi`

## 중요한 경계
- `panel_day_core.csv` schema는 바꾸지 않는다.
- official scoring output은 바꾸지 않는다.
- helper sidecar만 추가하고, shadow builder가 이를 읽어 `_share/panel_day_engine_local_precursor_shadow_v1.csv` 에 실어 나른다.

## 왜 helper sidecar가 맞는가
- canonical output 계약은 논문/평가/배포 경계와 맞물려 있다.
- 지금 필요한 것은 detector retune보다 "현재 detector가 어디서 멈췄는지 보이는 것"이다.
- 따라서 먼저 helper sidecar로 visibility를 늘리고, core schema 변경은 뒤로 미루는 것이 안전하다.

## shadow builder 변경점
- 새 helper file이 있으면 exact gate state를 우선 join한다.
- 없으면 기존 `ae_simple_ews_warnings.csv`, canonical `ae_simple_prefault_option_b_daily.csv`(legacy alias `ae_simple_prefault_B_daily.csv` 포함), `ae_simple_panel_alarms.csv` 로 예전 방식의 flag를 유지한다.
- 즉, 과거 site output도 깨지지 않는다.
- `prefault_B`는 raw helper로 유지하고, `prefault_B_common_cause_overlap` / `prefault_B_effective` 를 함께 보존해 downstream에서 common-cause gate를 분리 검토할 수 있게 한다.
- `local_precursor_any_flag`와 `alert_pattern`은 operator-facing precursor eligibility에 가까운 shadow 지표이므로, raw `prefault_B`가 아니라 `prefault_B_effective`를 사용한다.
- 즉, `site_event` / `group_off`와 직접 겹친 `prefault_B` row는 forensic raw helper로는 남지만 local precursor 승격 일수에는 바로 포함하지 않는다.

## 좁은 shadow-join integrity fix
- 이 패치에는 helper gate file join 안정성 보정도 포함된다.
- `ae_simple_local_precursor_gate_daily.csv` 에 `(site, panel_id, date)` exact duplicate row가 있으면 shadow builder는 이를 안전하게 1행으로 접고 계속 진행한다.
- exact duplicate는 non-key gate state가 완전히 같으므로 visibility 복원 관점에서 안전하게 collapse 가능하다.
- 반대로 non-key gate state가 하나라도 다르면 conflicting duplicate로 간주하고 즉시 실패한다.
- 즉, 이 변경은 detector retune이 아니라 shadow visibility restoration/integrity fix다.

## 이 sidecar가 답해주는 질문

### A) did `pre_ews` ever turn on?
- `pre_ews`, `signal_count`

### B) which cond_* pieces fired?
- `cond_var`, `cond_evt`, `cond_dtw`, `cond_hs`, `signal_count`

### C) was `data_bad` blocking `pre_ews`?
- `data_bad`, `signal_count`, `pre_ews`

### D) did `ews_runlen` fail to reach threshold?
- `pre_ews`, `ews_runlen`, `ews_warning`

### E) was site-event suppression active?
- `site_event_soft`, `site_event_hard`, `group_off_date`, `ews_warning`

### F) which prefault/prealarm gate failed?
- `prefault_cond_mid`, `prefault_cond_ae`, `prefault_cond_dtw`, `prefault_cond_ews`
- `prealarm_cond_ae_mid_or_hi`, `prealarm_cond_dtw_mid_or_hi`, `prealarm_cond_hs_mid_or_hi`

## 왜 이 패치가 eligibility audit 다음 단계인가
- eligibility audit는 "어떤 local fault가 precursor를 기대할 수 있는가"를 분리했다.
- 그 다음 자연스러운 질문은 "eligible case에서 왜 alert가 안 떴는가"다.
- 이 질문은 threshold replay만으로는 부족하고, 실제 engine gate path visibility가 필요하다.
