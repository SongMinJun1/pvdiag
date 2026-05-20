# Delivery QA Checklist V1

## Scope
이 checklist는 `conalog_full_runtime_v1/package`를 외부 전달 또는 dashboard 연동 검토용으로 넘기기 전 확인할 항목을 정리한다.

## Send / Include
아래 항목은 전달 package에 포함한다.

| Path | Purpose |
| --- | --- |
| `app/run_full_algorithm_pack.py` | 실제 runtime 실행 entrypoint |
| `app/verify_dashboard_outputs.py` | 실행 후 dashboard-facing output 검증 |
| `app/verify_delivery_package.py` | 전달 package 자체의 데이터/로컬경로 오염 여부 검증 |
| `app/import_any_csv_root.py` | 임의 CSV 폴더 staging helper |
| `pv_ae/panel_day_engine.py` | 핵심 panel-day engine |
| `research/prognostics/*` | package 내부 live/raw-only chain script |
| `requirements.txt` | 외부 Python package 목록 |
| `DASHBOARD_INTEGRATION.md` | dashboard 연동 계약 |
| `EXTERNAL_DELIVERY_GUIDE.md` | 외부 실행 안내 |
| `README.md` | runtime pack overview |
| `bin/*.bat`, `bin/*.ps1` | Windows wrapper/staging script |
| `artifacts/*.csv`, `artifacts/*.json`, `artifacts/*.md` | frozen preview/provenance/reference artifact |

## Exclude By Default
아래 항목은 기본 전달 package에 대용량 원본으로 포함하지 않는다.

| Path / Pattern | Reason |
| --- | --- |
| `data/<site>/raw/*` | 상대 시스템이 raw를 보유함 |
| `data/<site>/out/*` | 재실행 산출물이며 대용량일 수 있음 |
| `/private/tmp/*` | 로컬 검증 임시 산출물 |
| `outputs/*` | 내부 검증/개발 산출물 |
| `.git/*` | source control metadata |

## Pre-Delivery Commands
전달 전 최소 확인 명령은 아래와 같다.

```bash
python -m py_compile pv_ae/panel_day_engine.py
python -m py_compile research/prognostics/build_conalog_full_runtime_pack_v1.py
python research/prognostics/build_conalog_full_runtime_pack_v1.py
python release/conalog_full_runtime_v1/package/app/verify_delivery_package.py \
  --package-root release/conalog_full_runtime_v1/package
python research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Runtime Commands For Receiver
KTC ESS raw만 실행하는 경우:

```bash
python package/app/run_full_algorithm_pack.py \
  --data-root "/path/to/data_root" \
  --output-root "/path/to/output_root" \
  --sites ktc_ess
```

실행 후 output contract 확인:

```bash
python package/app/verify_dashboard_outputs.py \
  --output-root "/path/to/output_root"
```

## Primary Dashboard CSV
대시보드가 우선 읽을 파일:

```text
output_root/result/fault_panel_result_current_preview_v1.csv
```

## Final Checks
- [ ] `DASHBOARD_INTEGRATION.md`가 package 안에 있다.
- [ ] `EXTERNAL_DELIVERY_GUIDE.md`가 package 안에 있다.
- [ ] `app/verify_dashboard_outputs.py --help`가 동작한다.
- [ ] `app/verify_delivery_package.py --package-root package`가 통과한다.
- [ ] `pack_summary_v1.json`에 dashboard/doc/verifier 경로가 기록되어 있다.
- [ ] smoke test가 통과한다.
- [ ] 전달 범위에 raw 대용량 데이터가 섞이지 않았다.
- [ ] dashboard primary output은 `_share`가 아니라 `result/fault_panel_result_current_preview_v1.csv`로 안내되어 있다.
