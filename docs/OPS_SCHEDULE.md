# OPS Schedule

## 범위
- 이 단계는 macOS `launchd` 기준이다.
- 핵심 알고리즘이 아니라 운영용 wrapper 실행 스케줄만 다룬다.

## install
```bash
bash scripts/install_ops_launchd.sh
```

시간 변경 예시:
```bash
bash scripts/install_ops_launchd.sh --hour 2 --minute 10
```

## uninstall
```bash
bash scripts/uninstall_ops_launchd.sh
```

## 수동 실행

### 단일 사이트
```bash
python research/prognostics/run_site_latest.py --site kernelog1
```

### 전체 사이트
```bash
bash scripts/run_all_sites_latest_logged.sh
```

## dry-run 확인
```bash
python research/prognostics/run_site_latest.py --site kernelog1 --dry-run
```

## log 파일 위치
- `_ops_runtime_logs/`
- 파일 예시
  - `run_all_sites_latest_YYYYMMDD_HHMMSS.log`
  - `latest.log`
  - `latest.status`

## 운영자가 매일 확인할 파일
- `latest_panel_status.csv`
- `latest_alerts.csv`
- `latest_site_summary.csv`
