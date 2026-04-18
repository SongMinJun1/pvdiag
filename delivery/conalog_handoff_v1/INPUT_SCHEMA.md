# Input Schema

## Expected Input Directory Layout
- `input-root/` 아래에 config 가 가리키는 입력 CSV 가 있어야 함.
- 기본 config 에서는 `input_sample.csv` 를 기대함.

## Minimal Required File Naming Assumptions
- 기본값: `input-root/input_sample.csv`
- 실제 handoff 운영 시에는 `config/default.yaml` 의 `input_csv_name` 으로 제어함.

## Required Columns
- `site`
- `panel_id`

## Notes
- 본 handoff pack 은 conalog naming 만 사용함.
- full research tree 의 내부 feature schema 전체를 handoff 계약으로 노출하지 않음.
- dry-run 은 expected input 이 없어도 path/config 점검과 candidate csv 탐색 계획을 반환할 수 있음.
