# PV Diagnostics Single-File Delivery Contract V1

## Purpose
`pvdiag_single.py` is the single-file delivery artifact for the PV panel fault and precursor diagnosis algorithm.

The target use case is not to replace the counterpart dashboard. The counterpart system can keep its own dashboard and call this file as the diagnosis engine:

1. Provide raw CSV data in the expected folder structure.
2. Run `pvdiag_single.py`.
3. Read the dashboard-facing CSV outputs under `output_root/result/`.

The full modular package remains the development, verification, and traceability reference. The single file is generated from that package by `tools/build_pvdiag_single_py.py`.

## Runtime Assumptions
- Python 3.10 or newer is required.
- Python 3.11 is recommended.
- Input raw CSV files remain external and are not embedded in the single file.
- External Python packages remain external and are not embedded in the single file.

Recommended package set:

```bash
pip install pandas==2.3.3 numpy==2.3.4 torch==2.9.1 openpyxl==3.1.5 tqdm==4.67.1
```

Required packages:

```text
pandas
numpy
torch
openpyxl
tqdm
```

## Input Contract
The expected input layout is:

```text
data_root/
  ktc_ess/
    raw/
      *.csv
```

For tri-site verification:

```text
data_root/
  conalog/
    raw/
      *.csv
  gangui/
    raw/
      *.csv
  ktc_ess/
    raw/
      *.csv
```

The raw CSV format is assumed to match the existing KTC ESS/conalog format.

## Basic Command
Run KTC ESS only:

```bash
python pvdiag_single.py \
  --data-root "/path/to/data_root" \
  --output-root "/path/to/output_root" \
  --sites ktc_ess
```

Run the baseline tri-site universe:

```bash
python pvdiag_single.py \
  --data-root "/path/to/data_root" \
  --output-root "/path/to/output_root" \
  --sites conalog,gangui,ktc_ess
```

If `--data-root` is omitted, the single file first looks for a `data/` folder next to `pvdiag_single.py`. If that folder is missing and the process is interactive, it asks for a path in the console.

If `--output-root` is omitted, the single file creates:

```text
pvdiag_results/run_YYYYMMDD_HHMMSS/
```

next to `pvdiag_single.py`.

## Dashboard Primary Output
The dashboard should read this file first:

```text
output_root/result/fault_panel_result_current_preview_v1.csv
```

Primary join key:

```text
site + panel_id
```

Core columns:

| Column | Meaning |
| --- | --- |
| `site` | Site name |
| `panel_id` | Panel identifier |
| `전조날짜` | Selected precursor onset date. `전조없음` when absent |
| `고장 기준일` | Fault or runtime trigger reference date |
| `운영 판정` | Operator-facing verdict |
| `급락 종결 관측` | Whether abrupt terminal/drop evidence was observed |
| `점진 저하 누적` | Whether gradual degradation evidence accumulated |
| `사건 종결 요약` | Event summary such as abrupt, progressive, or precursor-to-terminal |
| `상위 해석 후보` | Top interpretation candidate from the algorithm |
| `기존 알고리즘 source` | Legacy or previous-algorithm source tag |

## Support Outputs
These files are generated for review, traceability, or richer dashboard pages:

| Output | Role |
| --- | --- |
| `result/fault_panel_result_current_v1.csv` | Detailed current result table |
| `result/fault_panel_result_precursor_report_v1.csv` | Precursor candidates and evidence |
| `result/fault_panel_result_raw_only_fault_signal_report_v1.csv` | Raw-only fault signal support table |
| `result/fault_panel_result_current_report_v1.md` | Current result explanation |
| `result/fault_panel_result_master_report_v1.md` | Output reading order and run summary |
| `result/fault_panel_result_detailed_report_v1.xlsx` | Detailed analyst workbook |
| `result/live_chain/*` | Frozen-support live-chain internal outputs |
| `result/raw_only_chain/*` | Raw-only strict/support-chain internal outputs |

Dashboard integration should prefer `result/` outputs. `_share` and chain-internal files are support/debug material, not the primary dashboard contract.

## Built-In Single-File Checks
Environment and embedded payload check:

```bash
python pvdiag_single.py --single-self-test
```

List embedded runtime files:

```bash
python pvdiag_single.py --single-list-payload
```

Extract readable source files for review:

```bash
python pvdiag_single.py --single-extract-source /tmp/pvdiag_single_source
```

## Single vs Modular Verification
Dry-run structure check:

```bash
python tools/verify_pvdiag_single_vs_modular.py \
  --mode dry-run \
  --json-out /private/tmp/pvdiag_single_vs_modular_dryrun.json
```

Reuse existing site outputs when `data/<site>/out` exists:

```bash
python tools/verify_pvdiag_single_vs_modular.py \
  --mode reuse-existing-site-outs \
  --data-root data \
  --reuse-existing-site-outs-root data \
  --json-out /private/tmp/pvdiag_single_vs_modular_reuse.json
```

The verifier compares key CSV existence, schema, row count, and byte hash where appropriate. It also checks that the master report and detailed xlsx are generated in full reuse mode.

## Exit And Failure Handling
- Exit `0`: command completed successfully.
- Exit `2`: Python version or required package problem.
- Exit `3`: input data root problem.
- Other nonzero exits usually come from the inner algorithm runner.

The single file writes a run log at:

```text
output_root/pvdiag_single_run.log
```

## Notes
- This document does not change algorithm behavior.
- The source of truth remains the modular package.
- The single file is generated, not hand-maintained.
- Raw data and large site outputs are not bundled into the single file.
