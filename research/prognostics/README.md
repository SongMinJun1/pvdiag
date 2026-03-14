# Prognostics Execution

이 디렉터리의 현재 역할은 `panel_day_engine.py`가 만든 core 출력에 risk, transition, ensemble 후처리를 연결하는 실행 진입 문서를 제공하는 것이다.

## 실행 순서

1. core engine 실행
   - 예: `python research/prognostics/run_panel_day_site.py --site conalog`
   - 또는 `pv_ae/panel_day_engine.py`를 직접 실행
2. post-processing 실행
   - `python research/prognostics/run_scores_pipeline.py --site conalog`

## 공식 출력 파일

- `panel_day_core.csv`
- `panel_diagnosis_summary.csv`
- `panel_day_risk.csv`
- `panel_day_risk_transition.csv`
- `panel_day_risk_ensemble.csv`

## 출력 생성 순서

1. core engine
   - `panel_day_core.csv`
   - `panel_diagnosis_summary.csv`
2. risk postproc
   - `panel_day_risk.csv`
3. transition postproc
   - `panel_day_risk_transition.csv`
4. ensemble postproc
   - `panel_day_risk_ensemble.csv`
