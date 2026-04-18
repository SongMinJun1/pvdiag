# Output Schema

## Stable Default Outputs
- `output/panel_result_v1.csv`
- `output/site_summary_v1.csv`
- `output/run_metadata_v1.json`
- `output/error_log_v1.csv`

## Stable `panel_result_v1.csv` Columns
- `site`
- `panel_id`
- `패널고장여부_ko`
- `사건유형_ko`
- `최종고장양상_ko`
- `conalog_원인군_ko`

## Stable `site_summary_v1.csv` Columns
- `site`
- `total_panel_count`
- `fault_panel_count`
- `non_fault_or_unresolved_count`
- `note_ko`

## Metadata Contract
`run_metadata_v1.json` 은 최소 아래 항목을 포함함.
- `generated_at_utc`
- `git_branch`
- `git_head`
- `config_path`
- `input_root`
- `output_root`
- `include_experimental`
- `dry_run`
- `note_ko`

## Optional Experimental Sidecar
- `output/experimental_reference_result_v1.csv`

이 sidecar 는 아래 성격의 보조 정보만 포함할 수 있음.
- GPVS reference-only field
- heuristic triage-only field

stable default output 과 experimental/reference output 은 반드시 분리해서 읽어야 함.
