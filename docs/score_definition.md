# Score Definition (SSOT)

본 문서는 `risk_score.py`, `add_transition_rankers.py`, `add_ensemble_rankers.py`의 점수 정의를 코드 기준으로 고정한다.

## 1) `risk_day` 정의

입력 컴포넌트(행 단위):
- `level_drop`: `clip(1 - mid_ratio, 0, 1)` (값 기반, 0~1)
- `ae_rank`: 같은 날짜 내 `recon_error` 퍼센타일 rank (`groupby(date).rank(pct=True)`)
- `dtw_rank`: 같은 날짜 내 `dtw_dist` 퍼센타일 rank
- `hs_rank`: 같은 날짜 내 `hs_score` 퍼센타일 rank
- `sustain_rank`: 같은 날짜 내 `sustain_mins` 퍼센타일 rank (event intensity proxy)
- `low_area_rank`: 같은 날짜 내 `low_area` 퍼센타일 rank (event intensity proxy)
- `vdrop_comp`: `v_ref_ok==True`이고 `v_drop` 유한값일 때 `clip(v_drop, 0, 1)`, 아니면 `NaN`

기본 가중치:
- `level_drop=0.35`, `ae_rank=0.15`, `dtw_rank=0.15`, `hs_rank=0.05`, `sustain_rank=0.10`, `low_area_rank=0.10`, `vdrop_comp=0.10`

결합식(가용성 보정 가중평균):
- 분자: `sum_i (w_i * x_i)` (`NaN`은 0으로 대체해 합산)
- 분모: `sum_i (w_i * 1[x_i is not NaN])`
- `risk_day = clip( 분자 / 분모, 0, 1 )` (분모=0이면 `NaN`)

게이트:
- `data_bad==True`이면 `risk_day=NaN`으로 마스킹.

## 2) `cp_score` / `cp_alarm` 정의 (CUSUM)

입력:
- CUSUM 입력열은 `--cp-input`으로 선택 (`risk_day`, `risk_7d_mean`, `risk_7d_max`), 기본은 `risk_7d_mean`.

사전 집계:
- `risk_7d_mean`: panel별 7일 rolling mean (`min_periods=3`)
- `risk_7d_max`: panel별 7일 rolling max (`min_periods=3`)

CUSUM 수식(패널별):
- 기준선: 각 패널의 입력열 유한값 중 첫 `baseline_n`개(기본 14개)로 `mu`, `sd` 계산 (`sd=max(sd, eps)`).
- 표준화: `z_t = (x_t - mu) / sd`
- 누적: `S_t = max(0, S_{t-1} + (z_t - k))` (기본 `k=0.5`)
- 알람: `cp_alarm_t = (S_t >= h)` (기본 `h=5.0`)
- 출력: `cp_score=S_t`, `cp_alarm` boolean

causal 여부:
- `t` 시점 계산은 `x_t`, 고정 기준선(`mu`, `sd`), 이전 누적치 `S_{t-1}`만 사용한다.
- 즉 CUSUM 자체는 미래값을 참조하지 않는다(패널 초반 `baseline_n` 확보 이후 동작).

## 3) `transition_raw` / `transition_cp` 정의

보조 정의:
- `shape_rank = max(ae_rank, dtw_rank)` (행 단위)
- `cp_pulse = 1` iff `cp_alarm`이 패널 내에서 `0 -> 1`로 바뀌는 날, 그 외 0

누수 방지(핵심):
- panel별 baseline은 `shift(1)` 후 rolling median/MAD로 계산.
- 즉 당일값은 baseline 창에 포함되지 않음.

수식:
- `med_mid_t`, `mad_mid_t`: `mid_ratio`의 과거창(window 기본 30, min-history 기본 10) median/MAD
- `med_shape_t`, `mad_shape_t`: `shape_rank`의 과거창 median/MAD
- `z_mid_drop_t = max(0, (med_mid_t - mid_ratio_t) / (mad_mid_t + eps))`
- `z_shape_rise_t = max(0, (shape_rank_t - med_shape_t) / (mad_shape_t + eps))`
- `transition_raw_t = max(z_mid_drop_t, z_shape_rise_t)`
- `transition_cp_t = max(transition_raw_t, cp_pulse_boost * cp_pulse_t)` (`cp_pulse_boost` 기본 5.0)

참고:
- 보고/비교용으로 `transition_rank_day`, `transition_cp_rank_day`를 같은 날짜 내 퍼센타일 rank로 추가한다.

## 4) `risk_ens` 정의

입력 후보 점수:
- `level_drop`, `ae_rank`, `dtw_rank`, `risk_day`, `cp_alarm`(정수화), `cp_score`

중간 정의:
- `shape_rank = max(ae_rank, dtw_rank)`
- `risk_max4 = max(risk_day, level_drop, ae_rank, dtw_rank)`

최종 결합:
- `risk_ens = clip(0.5 * level_drop + 0.5 * shape_rank, 0, 1)` (가중합)
- (별도 보조) `risk_cp = clip(risk_max4 + cp_alpha * cp_alarm_int, 0, 1)` (`cp_alpha` 기본 0.20)

설계 의도(3문장):
- `risk_ens`는 레벨 저하(`level_drop`)와 형상 이상(`shape_rank`)을 단순 대칭 결합해 과도한 규칙 복잡도를 피한다.
- `risk_max4`/`risk_cp`는 "강한 단일 이상 징후를 놓치지 않는" 보수적 보조 채널로 유지한다.
- 즉 `risk_ens`는 안정적인 기본 우선순위, `risk_cp`는 변화점 신호 반영 보조 우선순위라는 역할 분리를 가진다.

## 5) EWS / `prefault_B`와 `risk_ens` 관계

명확한 결론:
- 현재 구현에서 `risk_ens` 계산식에 EWS 계열(`ews_*`, `ews_warning`)이나 `prefault_B`는 **직접 포함되지 않는다**.
- `risk_ens`는 `level_drop`와 `shape_rank`만 사용한다.
- `risk_cp`도 EWS/`prefault_B`를 직접 사용하지 않고 `cp_alarm`(CUSUM 결과)만 사용한다.

---

## 요약 (10~20줄)

1. `risk_day`는 7개 컴포넌트의 가용성 보정 가중평균이다.  
2. 컴포넌트는 값형(`level_drop`, `vdrop_comp`)과 날짜 내 rank형(`ae/dtw/hs/sustain/low_area`)으로 구성된다.  
3. 기본 가중치는 `0.35/0.15/0.15/0.05/0.10/0.10/0.10`이며 `--weights-json`으로 변경 가능하다.  
4. `data_bad=True` 행은 `risk_day`를 강제로 `NaN` 처리한다.  
5. `cp_score`는 패널별 one-sided CUSUM 누적치다.  
6. CUSUM 입력은 기본 `risk_7d_mean`이고, `risk_day` 또는 `risk_7d_max`로 바꿀 수 있다.  
7. CUSUM은 현재값과 과거에서 정한 기준선/누적치만 써서 계산되므로 자체는 causal하다.  
8. `transition_raw`는 “현재값 vs 과거 baseline”의 양의 변화량만 반영한다.  
9. baseline은 `shift(1)` 뒤 rolling median/MAD라서 당일 정보가 baseline에 섞이지 않는다.  
10. `transition_cp`는 `transition_raw`와 `cp_pulse` 부스트의 최대값이다.  
11. `cp_pulse`는 `cp_alarm`이 0에서 1로 바뀌는 첫날만 1이다.  
12. `risk_ens`는 `0.5*level_drop + 0.5*shape_rank`의 clipped 가중합이다.  
13. `shape_rank`는 `max(ae_rank, dtw_rank)`로 정의된다.  
14. `risk_max4`와 `risk_cp`는 별도 보조 점수이며 `risk_ens` 자체와 식이 다르다.  
15. EWS(`ews_*`)와 `prefault_B`는 현재 `risk_ens` 식에 직접 들어가지 않는다.  
16. 따라서 `risk_ens`는 “어떤 입력을 어떤 수식으로 결합하는지”가 명시된 비블랙박스 점수다.  

