# OPS Handoff

## 목적
- 이 번들은 `pvdiag` 운영용 1차 배포물이다.
- 연구용 실험 스크립트, 외부 검증, 보고서 문서와 분리된 최소 운영 구성만 담는다.

## daily 실행 방법

### 단일 사이트
```bash
python research/prognostics/run_site_latest.py --site kernelog1
```

### 전체 사이트
```bash
bash scripts/run_all_sites_latest.sh
```

## 실행 원칙
- train 구간은 사이트 설정 파일에 고정한다.
- score 구간은 train 다음 날부터 최신 raw 날짜까지 자동 확장한다.
- 현재 구조는 incremental scoring이 아니라 전체 구간 재산출 방식이다.

## 운영 산출물 3종

### `latest_panel_status.csv`
- 최신 날짜 기준 panel 상태 1행씩 정리
- 운영자가 현재 panel 상태를 빠르게 훑는 용도

### `latest_alerts.csv`
- high-priority panel만 추린 운영용 shortlist
- diagnosis / dead / critical 흔적이 있으면 우선 노출하고, 없으면 `risk_ens` 상위 panel을 사용

### `latest_site_summary.csv`
- 사이트 단위 최신 요약
- panel 수, alert 수, diagnosis 수, dead/critical/final fault 수를 한 줄로 정리

## failure 대응
- 먼저 `--dry-run`으로 범위와 입력 경로를 확인한다.
- 한 사이트 실패 시 해당 사이트부터 다시 단독 실행한다.
- 실패 시 `run_site_latest.py`가 출력한 실행 명령과 로그를 확인한다.

## 운영/연구 분리
- 이 번들은 운영용 wrapper와 최소 코어만 포함한다.
- GPVS, TECNALIA, weak-label 평가, case study, 연구 보고서 문서는 포함하지 않는다.
