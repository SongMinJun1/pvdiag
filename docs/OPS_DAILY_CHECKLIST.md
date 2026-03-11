# OPS Daily Checklist

## 목적
- 운영자가 아침에 latest rerun이 정상 완료됐는지 빠르게 확인하는 절차다.
- 알고리즘 해석보다 실행 성공 여부와 latest alert 상태 확인에 집중한다.

## 아침 확인 순서
1. `_ops_runtime_logs/latest.status`를 먼저 확인한다.
   - `exit_code=0`인지 본다.
2. healthcheck를 실행한다.
   ```bash
   python research/prognostics/ops_healthcheck.py
   ```
3. 사이트별 `latest_alerts.csv`를 확인한다.
   - `data/<site>/out/latest_alerts.csv`
4. 이상이 있으면 `_ops_runtime_logs/latest.log` 마지막 구간을 확인한다.

## 수동 재실행 방법
### 단일 사이트
```bash
python research/prognostics/run_site_latest.py --site kernelog1
```

### 전체 사이트
```bash
bash scripts/run_all_sites_latest_logged.sh
```

## launchd kickstart
```bash
launchctl kickstart -k gui/$(id -u)/pvdiag.run_all_sites_latest
```

## dry-run 확인
- 실제 재실행 전에 경로와 날짜 범위를 먼저 본다.
```bash
python research/prognostics/run_site_latest.py --site kernelog1 --dry-run
```

## 운영자가 매일 확인할 파일
- `data/<site>/out/latest_panel_status.csv`
- `data/<site>/out/latest_alerts.csv`
- `data/<site>/out/latest_site_summary.csv`

## 운영자 판단 포인트
- `alert_count`가 전일 대비 급증했는지
- `online_diag_count`가 증가했는지
- `dead_count`가 증가했는지
- 특정 사이트의 latest 파일이 누락됐는지
- `_ops_runtime_logs/latest.log` 마지막 줄에 `[DONE] all sites completed`가 있는지

## health state 해석
- `ok`
  - latest status 정상, site summary 존재, log 완료 문구 확인
- `warning`
  - log 완료 문구 누락, `final_fault_count` 누락, 또는 일부 latest 파일 누락
- `fail`
  - `latest.status` 없음
  - `exit_code != 0`
  - `latest_site_summary.csv` 없음
