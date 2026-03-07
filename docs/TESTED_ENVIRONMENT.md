# Tested Environment

## smoke test success record

- smoke test success date: `2026-03-08`
- python version: `3.11.14`
- numpy: `2.3.4`
- pandas: `2.3.3`
- scipy: `1.17.1`
- matplotlib: `3.10.7`
- torch: `2.9.1`
- tqdm: `4.67.1`

## checks passed

- `python -m py_compile` on release-included Python files: passed
- `bash scripts/build_release_bundle.sh`: passed
- fresh unzip check of `_release_tmp/pvdiag_release.zip`: passed

## scope note

- 이 기록은 현재 로컬 환경에서 수행한 smoke test 기준이다.
- 기록 목적은 release bundle이 최소 수준에서 풀리고(import/compile/build) 재구성되는지 확인하는 것이다.
