# WHAT TO LOOK AT (3분 가이드)

## 0) 먼저 알아둘 핵심 정의
- 2σ 검증은 ‘물리 고장 라벨’이 아니라 ‘지속 저발전(손실) 이벤트’ 약라벨 평가다.
- risk/transition/ensemble은 “진단 라벨”이 아니라 “순위 비교용 점수”다.

## 1) 사람이 실제로 봐야 할 파일 TOP5

### 1) `data/kernelog1/out/ae_simple_scores.csv`
- 이 파일이 답하는 질문:
  - “패널-날짜 단위의 원본 엔진 출력(진단/전조/피처)이 무엇인가?”
- 확인 포인트:
  - `mid_ratio`, `state_dead_eff`, `dead_streak`, `critical_like_eff`, `final_fault`, `diagnosis_date_online`
  - 특정 패널의 날짜 흐름에서 신호가 언제 올라가고 확정되는지

### 2) `data/kernelog1/out/ae_simple_panel_diagnosis.csv`
- 이 파일이 답하는 질문:
  - “패널별 최초 온라인 진단일은 언제인가?”
- 확인 포인트:
  - `dead_diag_date`, `critical_diag_date`, `diagnosis_date_online`, `final_fault_first_date`
  - segment 라벨(`final_fault`)과 온라인 최초 확정일 분리 여부

### 3) `data/kernelog1/out/scores_with_risk_ens.csv`
- 이 파일이 답하는 질문:
  - “순위 비교용 점수(risk/ensemble)는 어떤 순서로 패널을 올리는가?”
- 확인 포인트:
  - `risk_day`, `risk_7d_mean`, `risk_ens`, `risk_cp`, `shape_rank`, `risk_max4`
  - 진단 라벨이 아니라 랭킹 점수임을 전제로 Top-K 관찰

### 4) `data/kernelog1/out/scores_with_risk_transition.csv`
- 이 파일이 답하는 질문:
  - “transition 계열 점수가 risk와 비교해 어떤 후보를 앞당기는가?”
- 확인 포인트:
  - `transition_raw`, `transition_cp`, `transition_rank_day`, `transition_cp_rank_day`
  - transition은 코어 진단 헤드가 아니라 postproc 순위 후보인지

### 5) `docs/score_definition.md`
- 이 파일이 답하는 질문:
  - “risk/cp/transition/ensemble 점수 정의가 블랙박스가 아닌가?”
- 확인 포인트:
  - 점수 입력 컬럼, 결합식, causal 여부, 누수 방지 설명
  - `risk_vdrop_or_7d`, `risk_vdrop_plus_7d` 설계 의도

## 2) 3분 확인 순서 (권장)
1. `ae_simple_scores.csv`에서 패널 1~2개를 골라 `state_dead_eff -> dead_streak -> diagnosis_date_online` 흐름 확인
2. `ae_simple_panel_diagnosis.csv`에서 패널별 최초 날짜 요약 확인
3. `scores_with_risk_ens.csv`에서 같은 날짜의 상위 랭크 후보 확인
4. `scores_with_risk_transition.csv`로 transition 점수와 순위 차이 비교
5. `docs/score_definition.md`로 정의/식/해석을 역참조

## 3) 재현 커맨드 4개 (실행했던 그대로)
```bash
python -m py_compile pv_ae/pv_autoencoder_dayAE.py
git diff --stat -- pv_ae/pv_autoencoder_dayAE.py
rg -n "^def _compute_ews|^def _compute_site_events|out = _compute_ews\\(out, args\\)|out = _compute_site_events\\(out\\)" pv_ae/pv_autoencoder_dayAE.py
rg -n "^_EV_DEFAULTS|^def _extract_event_values|ev_vals = _extract_event_values\\(ev\\)" pv_ae/pv_autoencoder_dayAE.py
```
