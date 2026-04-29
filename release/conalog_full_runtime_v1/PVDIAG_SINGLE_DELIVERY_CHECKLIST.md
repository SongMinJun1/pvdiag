# pvdiag_single.py Delivery Checklist

이 문서는 내부 체크리스트입니다.
교수님께 보낼 파일은 `pvdiag_single.py` 한 개입니다.

## 보내기 전에 확인

- `python tools/export_pvdiag_single_delivery.py --output-dir /tmp/pvdiag_professor_delivery`
- `/tmp/pvdiag_professor_delivery/` 안에 `pvdiag_single.py`만 있는지 확인합니다.
- `python /tmp/pvdiag_professor_delivery/pvdiag_single.py --single-self-test`
- 교수님 전달 폴더 안에서는 `python pvdiag_single.py --single-self-test`로 확인할 수 있습니다.
- checksum은 `release/conalog_full_runtime_v1/pvdiag_single_delivery_snapshot_v1.json`의 `single_file.sha256`과 맞춰 봅니다.

## 교수님 환경 전제

외부 패키지는 별도 설치가 필요합니다.

```bash
pip install pandas numpy torch openpyxl tqdm
```

입력 CSV는 단일 파일에 포함하지 않습니다.
실증 CSV가 준비되면 `--data-root`로 폴더를 지정해서 실행합니다.

## 실행 예시

```bash
python pvdiag_single.py \
  --data-root /path/to/data \
  --output-root /path/to/pvdiag_result
```

이미 `data/<site>/out` 산출물이 있는 시연/검증이면 아래 옵션을 추가할 수 있습니다.

```bash
--reuse-existing-site-outs-root /path/to/data
```

## 결과에서 먼저 볼 파일

```text
result/fault_panel_result_master_report_v1.md
result/fault_panel_result_detailed_report_v1.xlsx
result/fault_panel_result_precursor_report_v1.csv
result/fault_panel_result_raw_only_fault_signal_report_v1.csv
```

## 실패 시 확인

- 패키지 누락: `pandas numpy torch openpyxl tqdm`
- 입력 경로 문제: `--data-root`가 실제 raw CSV 구조를 가리키는지 확인
- 출력 경로 문제: `--output-root`에 쓰기 권한이 있는지 확인
- 실행 로그: `pvdiag_single_run.log`

## 경계

- 이 전달물은 알고리즘 원본을 손으로 한 파일에 합친 것이 아닙니다.
- 원본 모듈 구조는 유지하고, builder/exporter/checker로 generated single file을 검증합니다.
- BR-248 이후 generated single file은 zip/base64 payload를 쓰지 않고 source-text payload를 사용합니다.
- BR-249 이후 단일 파일 payload는 one-file 실행에 필요한 runtime/raw-only 경로 중심으로 정리되어, importer helper와 frozen-share live-chain-only builder는 포함하지 않습니다.
- BR-251 이후 `--single-self-test`는 외부 패키지 없이도 payload 무결성을 확인하고, 실제 실행 실패는 패키지 누락/data-root 문제를 구분해 안내합니다.
- 실증 CSV와 최종 라벨이 들어오기 전까지 truth-label 성능 주장은 하지 않습니다.
