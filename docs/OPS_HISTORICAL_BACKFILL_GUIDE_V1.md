# OPS Historical Backfill Guide V1

## 목적
- historical backfill은 과거 기간을 지정해 panel 결과 패키지를 다시 생성하기 위한 공식 진입점임.
- 이번 V1은 foundation 단계이며 detector logic을 다시 정의하지 않고, dry-run 중심으로 실행 계약과 출력 구조를 고정하는 단계임.
- panel multiaxis verdict가 primary이며, conalog는 direct operational interpretation layer, GPVS는 reference-only layer, heuristic은 field-trial triage layer로 유지함.

## 기본 진입점
- `python app/run_backfill.py --help`

## 지원 인자
- `--site`: 단일 사이트 또는 `all`
- `--start-date`: 시작일 `YYYY-MM-DD`
- `--end-date`: 종료일 `YYYY-MM-DD`
- `--input-root`: 입력 루트
- `--output-root`: 전용 backfill run 디렉터리를 만들 출력 루트
- `--gpvs-attach`: `on|off`
- `--report`: `on|off`
- `--mode`: `operational|eval`
- `--dry-run`: 실제 모델 실행 없이 plan/metadata preview만 생성

## dry-run 먼저 사용
- 권장 첫 실행:

```bash
python app/run_backfill.py \
  --dry-run \
  --site conalog \
  --start-date 2024-01-01 \
  --end-date 2024-01-07 \
  --input-root . \
  --output-root /tmp/pvdiag_backfill_dryrun \
  --gpvs-attach on \
  --report off \
  --mode operational
```

- dry-run은 인자를 검증하고, candidate input을 탐색하며, 전용 run 디렉터리와 metadata/output contract 파일을 생성함.
- dry-run에서는 실제 detector retrain이나 day-level replay를 수행하지 않음.

## operational vs eval
- `operational`
  - 기본 모드임.
  - 현행 stable result layer를 기준으로 backfill run contract를 생성함.
- `eval`
  - truth source가 있으면 이후 cycle에서 eval branch로 확장할 수 있게 reserved 함.
  - 현재 V1에서는 truth source가 없더라도 hard fail 하지 않고 metadata에 note를 남긴 뒤 operational-style outputs로 계속 진행함.

## 출력 디렉터리 구조
- `output-root/<run_id>/panel_result_v1.csv`
- `output-root/<run_id>/site_day_summary_v1.csv`
- `output-root/<run_id>/period_summary_v1.csv`
- `output-root/<run_id>/cause_candidate_distribution_v1.csv`
- `output-root/<run_id>/run_metadata_v1.json`
- `output-root/<run_id>/error_log_v1.csv`

## conalog 기준 예시
- conalog 단일 사이트 dry-run

```bash
python app/run_backfill.py \
  --dry-run \
  --site conalog \
  --start-date 2025-01-01 \
  --end-date 2025-01-31 \
  --input-root . \
  --output-root /tmp/pvdiag_backfill_conalog \
  --gpvs-attach on \
  --report off
```

- 전체 사이트 dry-run

```bash
python app/run_backfill.py \
  --dry-run \
  --site all \
  --start-date 2025-01-01 \
  --end-date 2025-01-31 \
  --input-root . \
  --output-root /tmp/pvdiag_backfill_all \
  --gpvs-attach off \
  --report off
```

## 현재 단계에서 고정되는 점
- detector logic은 바꾸지 않음.
- current frozen front-facing outputs는 바꾸지 않음.
- report automation과 one-click runtime orchestration은 이번 단계에 병합하지 않음.
