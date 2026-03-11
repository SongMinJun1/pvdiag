# OPS Handoff

## 목적
- 이 번들은 `pvdiag` 운영용 1차 배포물이다.
- 연구용 실험 스크립트, 외부 검증, 보고서 문서와 분리된 최소 운영 구성만 담는다.
- 번들 기준 포함 파일은 코어 엔진, latest rerun wrapper, healthcheck, launchd 설치 스크립트, 사이트 설정, 운영 문서로 제한한다.

## bundle 포함 기준
- core / pipeline
  - `pv_ae/panel_day_engine.py`
  - `research/prognostics/risk_score.py`
  - `research/prognostics/add_transition_scores.py`
  - `research/prognostics/add_ensemble_scores.py`
  - `research/prognostics/run_scores_pipeline.py`
  - `research/prognostics/run_panel_day_site.py`
  - `research/prognostics/run_site_latest.py`
  - `research/prognostics/ops_healthcheck.py`
- ops scripts
  - `scripts/run_all_sites_latest.sh`
  - `scripts/run_all_sites_latest_logged.sh`
  - `scripts/install_ops_launchd.sh`
  - `scripts/uninstall_ops_launchd.sh`
- configs / docs
  - `configs/sites/*.yaml`
  - `docs/OPS_RUNTIME.md`
  - `docs/OPS_HANDOFF.md`
  - `docs/OPS_SCHEDULE.md`
  - `docs/OPS_DAILY_CHECKLIST.md`
  - `docs/DATA_DICTIONARY.md`
  - `requirements.txt`

## daily operation 순서
1. launchd 또는 수동으로 latest rerun을 실행한다.
2. `_ops_runtime_logs/latest.status`를 확인한다.
3. `python research/prognostics/ops_healthcheck.py`를 실행한다.
4. `data/<site>/out/latest_alerts_enriched.csv`를 우선 확인한다.

## phenotype publish
- daily run이 끝나면 `_share/site_event_phenotypes_latest.csv` 기반 phenotype 결과를 site 운영 파일로 publish한다.
- 추가 운영 산출물
  - `latest_event_phenotypes.csv`
  - `latest_alerts_enriched.csv`
  - `latest_panel_status_enriched.csv`
  - `latest_site_phenotype_summary.csv`
- `electrical`, `shape`, `instability`, `compound`는 exact fault class가 아니라 phenotype 태그다.

## 수동 재실행 방법
### 단일 사이트
```bash
python research/prognostics/run_site_latest.py --site kernelog1
```

### 전체 사이트
```bash
bash scripts/run_all_sites_latest_logged.sh
```

## dry-run 방법
```bash
python research/prognostics/run_site_latest.py --site kernelog1 --dry-run
```

## kickstart 방법
```bash
launchctl kickstart -k gui/$(id -u)/pvdiag.run_all_sites_latest
```

## 실행 원칙
- train 구간은 사이트 설정 파일에 고정한다.
- score 구간은 train 다음 날부터 최신 raw 날짜까지 자동 확장한다.
- 현재 구조는 incremental scoring이 아니라 전체 구간 재산출 방식이다.

## 운영 산출물
### 기본 latest 3종
- `latest_panel_status.csv`
- `latest_alerts.csv`
- `latest_site_summary.csv`

### phenotype enriched 4종
- `latest_event_phenotypes.csv`
- `latest_alerts_enriched.csv`
- `latest_panel_status_enriched.csv`
- `latest_site_phenotype_summary.csv`

## failure 대응
- 먼저 `--dry-run`으로 범위와 입력 경로를 확인한다.
- `_ops_runtime_logs/latest.status`에서 `exit_code`를 확인한다.
- `python research/prognostics/ops_healthcheck.py`로 전체 상태를 다시 본다.
- `latest_alerts_enriched.csv`가 생성됐는지 확인한다.
- 한 사이트 실패 시 해당 사이트부터 다시 단독 실행한다.
- launchd로 돌고 있었다면 `latest.log` 마지막 줄과 `launchctl print gui/$(id -u)/pvdiag.run_all_sites_latest`를 확인한다.

## 운영/연구 분리
- 이 번들은 운영용 wrapper와 최소 코어만 포함한다.
- `docs/reports`, `docs/internal`, `docs/archive`, `research/support`, GPVS/TECNALIA 실험 파일, `_share`, `data`는 bundle에 넣지 않는다.
