# WHAT TO LOOK AT (3분 가이드)

## 0) 먼저 알아둘 핵심 정의
- 2σ 검증은 ‘물리 고장 라벨’이 아니라 ‘지속 저발전(손실) 이벤트’ 약라벨 평가다.
- risk/transition/ensemble은 “진단 라벨”이 아니라 “순위 비교용 점수”다.
- 정의가 필요하면 `docs/DATA_DICTIONARY.md`를 기준으로 보고, `docs/reports/*.md`는 결과 보고서로만 본다.

## 1) 사람이 실제로 봐야 할 파일 TOP5

### 1) `data/kernelog1/out/panel_day_core.csv`
- 패널-날짜 단위의 core 엔진 출력
- 확인 포인트: `mid_ratio`, `state_dead_eff`, `dead_streak`, `critical_like_eff`, `final_fault`, `diagnosis_date_online`

### 2) `data/kernelog1/out/panel_diagnosis_summary.csv`
- 패널별 최초 온라인 진단 요약
- 확인 포인트: `dead_diag_date`, `critical_diag_date`, `diagnosis_date_online`, `final_fault_first_date`

### 3) `data/kernelog1/out/panel_day_risk.csv`
- risk 후처리 결과
- 확인 포인트: `risk_day`, `risk_7d_mean`, `risk_30d_mean`, `cp_score`, `cp_alarm`

### 4) `data/kernelog1/out/panel_day_risk_transition.csv`
- transition 후처리 결과
- 확인 포인트: `transition_raw`, `transition_cp`, `transition_rank_day`, `transition_cp_rank_day`

### 5) `data/kernelog1/out/panel_day_risk_ensemble.csv`
- ensemble 후처리 결과
- 확인 포인트: `risk_ens`, `risk_cp`, `shape_rank`, `risk_max4`

## 2) 3분 확인 순서 (권장)
1. `panel_day_core.csv`에서 패널 1~2개를 골라 `state_dead_eff -> dead_streak -> diagnosis_date_online` 흐름 확인
2. `panel_diagnosis_summary.csv`에서 패널별 최초 날짜 요약 확인
3. `panel_day_risk.csv`에서 risk/cp 기본 축 확인
4. `panel_day_risk_transition.csv`에서 transition 계열 비교
5. `panel_day_risk_ensemble.csv`에서 최종 순위 비교 결과 확인

## 3) 공식 출력 파일명 계약

- `panel_day_core.csv`
- `panel_diagnosis_summary.csv`
- `panel_day_risk.csv`
- `panel_day_risk_transition.csv`
- `panel_day_risk_ensemble.csv`
- 예전 출력 파일명(`ae_simple_*`, `scores_with_risk*`)은 더 이상 기준으로 사용하지 않는다.

## 4) 문서 역할 구분
- `docs/DATA_DICTIONARY.md`: canonical 정의 문서
- `docs/internal/WHAT_TO_LOOK_AT.md`: 내부 빠른 확인 가이드
- `docs/reports/kernelog1_onepager.md`: kernelog1 결과 요약 보고서
