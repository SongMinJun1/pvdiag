# pvdiag_single.py Quickstart

`pvdiag_single.py`는 교수님 전달용 단일 Python 실행 파일입니다.
원본 알고리즘은 계속 모듈형으로 유지하고, 이 파일은 builder로 생성한 self-extracting runner입니다.
BR-248 이후 내부 payload는 zip/base64가 아니라 UTF-8 source-text로 들어갑니다.

## 준비

필요한 외부 Python 패키지:

```bash
pip install pandas numpy torch openpyxl tqdm
```

입력 데이터는 별도로 준비합니다.
권장 구조:

```text
data/
  conalog/raw/*.csv
  gangui/raw/*.csv
  ktc_ess/raw/*.csv
```

기존에 `data/<site>/out`가 이미 있으면 `--reuse-existing-site-outs-root data`로 빠르게 검증할 수 있습니다.

## 가장 쉬운 실행

`pvdiag_single.py` 옆에 `data/` 폴더가 있으면 아래처럼 실행할 수 있습니다.

```bash
python pvdiag_single.py
```

출력은 자동으로 아래에 생성됩니다.

```text
pvdiag_results/run_YYYYMMDD_HHMMSS/
```

## 전달 파일 만들기

교수님께 보낼 폴더를 만들 때는 repo에서 아래 export helper를 사용합니다.

```bash
python tools/export_pvdiag_single_delivery.py --output-dir /tmp/pvdiag_professor_delivery
```

성공하면 `/tmp/pvdiag_professor_delivery/` 안에는 아래 파일 하나만 있어야 합니다.

```text
pvdiag_single.py
```

quickstart, manifest, checker, runtime pack은 내부 검증용입니다.
교수님께 전달하는 파일은 export된 `pvdiag_single.py` 한 개입니다.
전달 전 내부 체크리스트는 `PVDIAG_SINGLE_DELIVERY_CHECKLIST.md`, checksum snapshot은 `pvdiag_single_delivery_snapshot_v1.json`입니다.

## 명시 실행

```bash
python pvdiag_single.py \
  --data-root /path/to/data \
  --output-root /path/to/pvdiag_result \
  --reuse-existing-site-outs-root /path/to/data
```

`--reuse-existing-site-outs-root`는 이미 생성된 `data/<site>/out`를 재사용하는 검증/시연용 옵션입니다.
새 raw부터 전체 계산하려면 이 옵션을 빼면 됩니다.

## 실행 후 확인할 파일

가장 먼저 볼 파일:

```text
result/fault_panel_result_master_report_v1.md
result/fault_panel_result_detailed_report_v1.xlsx
result/fault_panel_result_precursor_report_v1.csv
result/fault_panel_result_raw_only_fault_signal_report_v1.csv
```

문제가 생기면 로그를 봅니다.

```text
pvdiag_single_run.log
```

## 자가검사

파일이 깨지지 않았는지 알고리즘을 돌리지 않고 확인:

```bash
python pvdiag_single.py --single-self-test
```

repo 안에서 전체 전달 closeout을 다시 확인하려면 아래를 실행합니다.

```bash
python tools/check_pvdiag_single_delivery_closeout.py --export-output-dir /tmp/pvdiag_single_closeout --clean-output-dir
```

## 주의

- `pvdiag_single.py`는 손으로 수정하지 않습니다.
- 재생성은 repo에서 `python tools/build_pvdiag_single_py.py`로 합니다.
- 외부 라이브러리와 입력 CSV는 단일 파일에 포함하지 않습니다.
- Windows embedded runtime은 단일 파일에 포함하지 않습니다.
- zip/base64 payload는 사용하지 않습니다. 내부 파일은 `EMBEDDED_TEXT_FILES` source-text payload로 복원합니다.
- importer helper와 frozen-share live-chain-only builder는 단일 파일 payload에서 제외합니다.
- 기본 실행은 대용량 중복 workspace를 남기지 않도록 `--workspace-retention result-only`를 자동 적용합니다.
- 실패 시 `missing required Python packages`, `data-root was not provided`, `data-root does not exist` 메시지를 먼저 보고, 안내된 `pip install ...` 또는 `--data-root /path/to/data`로 다시 실행합니다.
- generated single file은 source-text JSON chunk container와 11-file essential payload를 사용해 불필요한 line-literal 전개와 sidecar payload를 피합니다.
