# OPS Daily Report Automation V1

## 1. 목적
- 본 문서는 conalog one-click foundation 에서 daily report markdown 을 어떻게 생성하고 읽는지 설명한다.
- 이번 단계는 foundation 이며 full production scheduler 를 선언하는 문서가 아니다.

## 2. daily report 에 포함되는 내용
- generated_at
- site summary
- total/fault/non-fault-or-unresolved counts
- conalog fault-family distribution
- GPVS core/auxiliary/not-used counts
- suspected-cause distribution
- 신규 fault panel 목록
- 전일 대비 변화 목록
- 주요 해석 메모
- 실행 오류 요약

## 3. stable vs optional sections
- stable 에 가까운 section
  - site summary
  - panel counts
  - conalog fault-family distribution
  - 주요 해석 메모
  - 실행 오류 요약
- optional 또는 fallback 허용 section
  - GPVS usage summary
  - suspected-cause distribution
  - 신규 fault panel 상세
  - 전일 대비 변화 목록
- optional 입력이 없더라도 report 는 생성되어야 하며, 누락 section 은 note/placeholder 로 남긴다.

## 4. 수동 생성 방법
```bash
python research/prognostics/build_daily_report_v1.py --output-root /tmp/pvdiag_oneclick_dryrun
```

- 기본 출력 경로는 `<output-root>/latest/daily_report_v1.md` 다.
- builder 는 latest 경로를 우선 사용하고, 일부 snapshot/frozen fallback 을 참고할 수 있다.

## 5. one-click 연동
- `app/run_oneclick.py --report on` 이면 one-click flow 마지막에 daily report builder 를 호출한다.
- `--report off` 이면 stable/integrated 산출물만 남기고 report 는 생성하지 않는다.

## 6. 향후 자동화 가능성
- 향후에는 scheduler 또는 batch orchestrator 와 연결할 수 있다.
- 그러나 이번 단계는 foundation 이므로 cron, queue, UI scheduler, alert delivery 를 production 수준으로 묶지 않는다.

## 7. 해석 원칙
- daily report 역시 panel multiaxis verdict 를 primary 로 읽는다.
- conalog 는 direct operational interpretation layer 로 읽는다.
- GPVS 는 reference-only 이고, heuristic 은 triage-only 이다.
- 따라서 report 안의 experimental/reference section 은 stable default section 과 분리해서 읽어야 한다.
