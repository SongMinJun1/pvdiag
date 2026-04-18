# OPS Backfill IO Contract V1

## CLI 입력 계약
- `--site`
  - 단일 사이트명 또는 `all`
- `--start-date`
  - 포함 시작일 `YYYY-MM-DD`
- `--end-date`
  - 포함 종료일 `YYYY-MM-DD`
- `--input-root`
  - repo/data 입력 루트
- `--output-root`
  - backfill 결과를 생성할 전용 루트
- `--gpvs-attach`
  - `on|off`
- `--report`
  - `on|off`
- `--mode`
  - `operational|eval`
- `--dry-run`
  - 실제 모델 실행 없이 plan/metadata preview만 생성

## 출력 파일 계약

### `panel_result_v1.csv`
- 최소 컬럼:
  - `site`
  - `panel_id`
  - `target_window_start_date`
  - `target_window_end_date`
  - `패널고장여부_ko`
  - `사건유형_ko`
  - `최종고장양상_ko`
  - `conalog_원인군_ko`
  - `1순위_의심원인_ko`
  - `2순위_의심원인_ko`
  - `3순위_의심원인_ko`
  - `result_source_ko`
  - `note_ko`
- `gpvs-attach=off`이면 suspected-cause 컬럼은 공란일 수 있음.

### `site_day_summary_v1.csv`
- 최소 컬럼:
  - `site`
  - `date`
  - `mode`
  - `gpvs_attach_flag`
  - `report_flag`
  - `candidate_input_file_count`
  - `detected_input_date_min`
  - `detected_input_date_max`
  - `preview_panel_count`
  - `preview_fault_panel_count`
  - `run_status_ko`
  - `note_ko`

### `period_summary_v1.csv`
- 최소 컬럼:
  - `site`
  - `start_date`
  - `end_date`
  - `requested_day_count`
  - `candidate_input_file_count`
  - `preview_panel_count`
  - `preview_fault_panel_count`
  - `gpvs_attach_flag`
  - `report_flag`
  - `mode`
  - `note_ko`

### `cause_candidate_distribution_v1.csv`
- 최소 컬럼:
  - `site`
  - `candidate_ko`
  - `panel_count`
  - `distribution_basis_ko`
  - `note_ko`
- foundation 단계에서는 preview basis만 기록될 수 있음.

### `error_log_v1.csv`
- 최소 컬럼:
  - `logged_at_utc`
  - `level`
  - `site`
  - `stage_ko`
  - `code`
  - `message_ko`

## metadata 계약
- `run_metadata_v1.json`에는 최소한 아래 필드가 있어야 함.
  - `run_id`
  - `generated_at_utc`
  - `git_branch`
  - `git_head`
  - `site_filter`
  - `start_date`
  - `end_date`
  - `gpvs_attach_flag`
  - `report_flag`
  - `mode`
  - `note_ko`

## eval mode 보수 규칙
- `mode=eval` 이더라도 truth source가 없으면 hard fail 하지 않음.
- 해당 사실은 `run_metadata_v1.json`의 `note_ko`와 필요 시 `error_log_v1.csv`에 남김.

## 범위 주의
- 본 계약은 foundation 단계의 IO를 고정하는 문서임.
- detector logic, panel multiaxis verdict의 의미, GPVS evidence 의미는 이 문서에서 다시 정의하지 않음.
