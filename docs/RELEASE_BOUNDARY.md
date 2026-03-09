# Release Boundary

이 문서는 현재 배포/공유 경계에서 프로그램, 입력 데이터, 산출물, 레포 포함 범위를 명확히 적기 위한 문서다.

## 프로그램

- core engine: `pv_ae/panel_day_engine.py`
- site runner: `research/prognostics/run_panel_day_site.py`
- post-processing orchestrator: `research/prognostics/run_scores_pipeline.py`
- post-processing steps:
  - `research/prognostics/risk_score.py`
  - `research/prognostics/add_transition_scores.py`
  - `research/prognostics/add_ensemble_scores.py`

## 입력 데이터

- raw site data: `data/<site>/raw/*.csv`
- 엔진 실행 인자: site, train/eval date range, output directory
- post-processing 입력:
  - `panel_day_core.csv` from engine

## 산출물

공식 출력 파일명 계약은 아래 5개다.

- `panel_day_core.csv`
- `panel_diagnosis_summary.csv`
- `panel_day_risk.csv`
- `panel_day_risk_transition.csv`
- `panel_day_risk_ensemble.csv`

그 외 보고용 markdown, PNG, paper-pack 파일은 파생 산출물로 본다.

## 레포에 남길 것

- 프로그램 소스
- 현재형 문서
- 소형 설정/메타데이터
- 재현에 필요한 shell/python entrypoint
- 샘플 수준의 소형 예시 파일(필요할 때만)

## 레포에 남기지 않을 것

- `data/<site>/raw`의 대용량 원천 데이터
- `data/<site>/out`의 대용량 생성 산출물 기본본
- 중간 디버그 CSV, 대용량 로그, 일회성 분석 결과
- 로컬 전용 캐시, 임시 PNG/MD, 개인 실행 산출물
