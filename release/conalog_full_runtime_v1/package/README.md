# PV Diagnostics Runtime Package

이 package는 패널별 raw CSV를 입력으로 받아 PV 패널 고장/전조 진단 결과를 생성하는 실행용 runtime package다.

## Quick Start
```bash
python app/run_full_algorithm_pack.py \
  --data-root "/path/to/data_root" \
  --output-root "/path/to/output_root" \
  --sites ktc_ess
```

실행 후 대시보드가 우선 읽을 결과는 아래 파일이다.

```text
output_root/result/fault_panel_result_current_preview_v1.csv
```

## Verify
실행 결과 검증:

```bash
python app/verify_dashboard_outputs.py \
  --output-root "/path/to/output_root"
```

전달 package 자체 검증:

```bash
python app/verify_delivery_package.py --package-root .
```

## Documents
- `EXTERNAL_DELIVERY_GUIDE.md`: 외부 전달/실행 안내
- `DASHBOARD_INTEGRATION.md`: 대시보드 연동 계약
- `DELIVERY_QA_CHECKLIST.md`: 전달 전 포함/제외/검증 체크리스트
