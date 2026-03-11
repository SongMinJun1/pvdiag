# OPS History

## 왜 latest만으로 부족한가
- `latest_alerts.csv`와 `latest_alerts_enriched.csv`는 오늘 상태만 보여준다.
- 운영자는 전일 대비 신규 경보가 무엇인지, 사라진 경보가 무엇인지, 사이트 단위 추세가 어떤지를 같이 봐야 한다.
- 그래서 latest snapshot 위에 daily history를 누적한다.

## 파일 의미
### `alert_history.csv`
- `snapshot_date`, `site`, `panel_id` 단위의 누적 alert 기록이다.
- 같은 날짜에 같은 panel이 다시 생성되면 upsert처럼 마지막 값으로 덮어쓴다.

### `new_alerts_today.csv`
- 오늘 `latest_alerts_enriched.csv`에는 있고 직전 snapshot에는 없던 panel 목록이다.
- 운영자는 신규 panel이 늘었는지 먼저 본다.

### `resolved_alerts_today.csv`
- 직전 snapshot에는 있었지만 오늘 latest alerts에는 없는 panel 목록이다.
- 마지막으로 보였던 값과 함께 저장한다.

### `site_daily_rollup.csv`
- 날짜별 site 요약이다.
- `alert_count`, `new_alert_count`, `resolved_alert_count`, diagnosis/dead/final fault 수, dominant family count를 한 줄로 본다.

### `_share/ops_daily_rollup_latest.csv`
- 4개 사이트 최신 rollup 한 줄씩만 모은 전역 요약이다.

## 중복 실행 처리
- `alert_history.csv`는 `snapshot_date + site + panel_id` 기준으로 중복 제거한다.
- `site_daily_rollup.csv`는 `snapshot_date + site` 기준으로 중복 제거한다.
- 즉 같은 날짜 rerun을 여러 번 해도 같은 snapshot key는 최신 값으로 유지된다.

## 운영자가 아침에 보는 추천 순서
1. `_ops_runtime_logs/latest.status`
2. `python research/prognostics/ops_healthcheck.py`
3. `data/<site>/out/new_alerts_today.csv`
4. `data/<site>/out/latest_alerts_enriched.csv`
5. `data/<site>/out/resolved_alerts_today.csv`
6. `data/<site>/out/site_daily_rollup.csv`
7. `_share/ops_daily_rollup_latest.csv`

## 해석 주의
- `electrical`, `shape`, `instability`, `compound`는 exact fault class가 아니라 phenotype 태그다.
- 이 history는 운영용 변화 추적용이며, exact F1~F7 fault class 판정용이 아니다.
