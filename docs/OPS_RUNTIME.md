# OPS Runtime

## 운영용 1차 구조
- 운영형 진입점은 `research/prognostics/run_site_latest.py`와 `scripts/run_all_sites_latest.sh`다.
- 실행 로그 기준 wrapper는 `scripts/run_all_sites_latest_logged.sh`다.
- 상태 점검 진입점은 `research/prognostics/ops_healthcheck.py`다.
- 이 문서는 연구용 release bundle이 아니라 운영용 1차 실행 구조를 설명한다.
- 각 사이트는 `configs/sites/<site>.yaml`로 관리한다.
- baseline train 구간은 고정하고, `score_end`만 raw 디렉터리 최신 날짜로 자동 확장한다.

## 원칙
- `train_start`, `train_end`: 고정 healthy baseline 구간
- `score_start`: 고정 운영 시작일
- `score_end`: 설정 파일에 넣지 않음. `raw_dir`의 최신 CSV 날짜를 wrapper가 자동 탐지
- 현재 구조는 incremental update가 아니라 전체 score 구간 재산출 방식이다.

## daily operation 방식
1. site 설정 로드
2. `raw_dir`에서 최신 날짜 탐지
3. `panel_day_engine.py` 실행
4. `run_scores_pipeline.py` 실행
5. 운영용 3종 CSV 생성
6. `ops_healthcheck.py`로 latest 상태 확인

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

## 운영용 산출물 3종

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
- `_share/site_event_phenotypes_latest.csv`가 있으면 phenotype 관련 컬럼을 추가로 붙인다.

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

## 설정 파일 필수 항목
- `site`
- `train_start`
- `train_end`
- `score_start`
- `raw_dir`
- `out_dir`
