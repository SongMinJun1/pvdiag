# pvdiag Release Bundle

이 저장소는 PV 패널 일단위 진단/전조 파이프라인을 재현하기 위한 release bundle 기준 트리다.

## 포함된 것

- core engine: `pv_ae/panel_day_engine.py`
- post-processing core:
  - `research/prognostics/risk_score.py`
  - `research/prognostics/add_transition_scores.py`
  - `research/prognostics/add_ensemble_scores.py`
- 실행 entrypoint:
  - `research/prognostics/run_panel_day_site.py`
  - `research/prognostics/run_scores_pipeline.py`
- 평가/사례 분석 스크립트:
  - `research/prognostics/weaklabel_eval_2sigma.py`
  - `research/prognostics/fault_case_study.py`
  - `research/prognostics/plot_case_timeline.py`
  - `research/prognostics/ingest_gpvs_faults.py`
  - `research/prognostics/external_eval_gpvs.py`
- 기준 문서:
  - `docs/DATA_DICTIONARY.md`
  - `docs/score_definition.md`
  - `docs/RELEASE_BOUNDARY.md`
  - `docs/RELEASE_MANIFEST.md`

## 포함되지 않은 것

- 대용량 입력 데이터 `data/**`
- 대용량 생성 산출물 `data/<site>/out/**`
- 내부 계획 문서, refactor 메모, historical 문서
- onepager 성격의 보고서 산출물

## 공식 출력 파일명

- `panel_day_core.csv`
- `panel_diagnosis_summary.csv`
- `panel_day_risk.csv`
- `panel_day_risk_transition.csv`
- `panel_day_risk_ensemble.csv`

## 최소 실행 순서

1. core engine 실행
   - `python research/prognostics/run_panel_day_site.py --site conalog`
2. post-processing 실행
   - `python research/prognostics/run_scores_pipeline.py --site conalog`
3. optional site eval
   - `python research/prognostics/weaklabel_eval_2sigma.py --site conalog`
   - `python research/prognostics/fault_case_study.py --site conalog --case "<panel_id>:<onset_date>"`
4. optional external benchmark
   - `python research/prognostics/ingest_gpvs_faults.py`
   - `python research/prognostics/external_eval_gpvs.py`

## 데이터 준비

이 release bundle에는 실제 `data/<site>/raw/*.csv`가 포함되지 않는다.
실행하려면 사용자가 별도로 site raw data를 준비해야 한다.

## 문서 위치

- 컬럼/라벨/출력 계약: `docs/DATA_DICTIONARY.md`
- risk / transition / ensemble 점수 정의: `docs/score_definition.md`
