# OPS Runtime

## 운영용 1차 구조
- 운영형 진입점은 `research/prognostics/run_site_latest.py`와 `scripts/run_all_sites_latest.sh`다.
- 실행 로그 기준 wrapper는 `scripts/run_all_sites_latest_logged.sh`다.
- 상태 점검 진입점은 `research/prognostics/ops_healthcheck.py`다.
- phenotype publish 진입점은 `research/prognostics/publish_site_latest_phenotypes.py`다.
- 이 문서는 연구용 release bundle이 아니라 운영용 1차 실행 구조를 설명한다.
- 각 사이트는 `configs/sites/<site>.yaml`로 관리한다.
- baseline train 구간은 고정하고, `score_end`만 raw 디렉터리 최신 날짜로 자동 확장한다.

## 원칙
- `train_start`, `train_end`: 고정 healthy baseline 구간
- `score_start`: 고정 운영 시작일
- `score_end`: 설정 파일에 넣지 않음. `raw_dir`의 최신 CSV 날짜를 wrapper가 자동 탐지
- 현재 구조는 incremental update가 아니라 전체 score 구간 재산출 방식이다.
- `electrical`, `shape`, `instability`, `compound`는 exact fault class가 아니라 phenotype 태그다.

## daily operation 방식
1. site 설정 로드
2. `raw_dir`에서 최신 날짜 탐지
3. `panel_day_engine.py` 실행
4. `run_scores_pipeline.py` 실행
5. `_share` phenotype 집계 refresh
6. site별 phenotype publish
7. 운영용 latest CSV와 enriched CSV 생성
8. `ops_healthcheck.py`로 latest 상태 확인

## 4개 사이트 실행 예시

```bash
python research/prognostics/run_site_latest.py --site kernelog1 --dry-run
python research/prognostics/run_site_latest.py --site sinhyo
python research/prognostics/run_site_latest.py --site gangui
python research/prognostics/run_site_latest.py --site ktc_ess
```

```bash
bash scripts/run_all_sites_latest_logged.sh
python research/prognostics/ops_healthcheck.py
```

## 운영용 산출물

### 기본 latest 3종
- `latest_panel_status.csv`
- `latest_alerts.csv`
- `latest_site_summary.csv`

### phenotype publish 4종
- `latest_event_phenotypes.csv`
- `latest_alerts_enriched.csv`
- `latest_panel_status_enriched.csv`
- `latest_site_phenotype_summary.csv`

### `latest_panel_status.csv`
- 최신 날짜 기준 panel 상태 1행씩
- 기본 컬럼
  - `site`
  - `panel_id`
  - `date`
  - `risk_ens`
  - `risk_day`
  - `diagnosis_date_online`
  - `critical_diag_date`
  - `dead_diag_date`
  - `final_fault`

### `latest_alerts.csv`
- 운영상 바로 볼 high-priority panel만 추린다.
- 우선순위 규칙
  1. `dead`, `critical`, `diagnosis_date_online`, `final_fault` 흔적이 있는 panel
  2. 그런 panel이 없으면 `risk_ens` 상위 20개

### `latest_site_summary.csv`
- 최신 날짜 기준 사이트 요약
- 컬럼
  - `site`
  - `latest_date`
  - `panel_count`
  - `alert_count`
  - `online_diag_count`
  - `critical_count`
  - `dead_count`
  - `final_fault_count`

### `latest_alerts_enriched.csv`
- 운영자가 우선 확인할 phenotype 부착 shortlist다.
- 추가 컬럼
  - `phenotype`
  - `dominant_family`
  - `top_score`
  - `second_score`
  - `margin_top2`
  - `evidence_strength`
  - `phenotype_event_date`

### `latest_panel_status_enriched.csv`
- panel latest 상태에 phenotype 태그를 패널 기준으로 붙인 전체판이다.
- event가 없는 panel은 phenotype 컬럼이 비어 있을 수 있다.

### `latest_site_phenotype_summary.csv`
- site별 phenotype count와 dominant family count를 한 줄로 요약한다.

## 설정 파일 필수 항목
- `site`
- `train_start`
- `train_end`
- `score_start`
- `raw_dir`
- `out_dir`
