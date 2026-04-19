# Delivery Manifest

## 먼저 볼 것
1. `package/bin/run_demo.bat`
2. `package/bin/run_real.bat`
3. `package/app/run_conalog_infer.py`
4. `package/app/run_oneclick.py`

## 폴더별 의미
- `package/app/`: executable entrypoint 모음
- `package/bin/`: Windows operator wrapper 와 설정 template
- `package/config/`: runtime config
- `package/stable_handoff/`: stable handoff docs/config/examples
- `package/runtime/`: runtime guide, failure handling, latency/readiness report
- `package/oneclick/`: one-click guide, daily-report guide, template
- `package/docs/`: comparison, GPVS inventory, GPVS mail draft, coverage/performance, integrated table pointer
- `package/examples/`: stable snapshot, reference-only summary, triage-only summary

## 주의
- stable / reference_only / triage_only 구분은 `final_delivery_manifest_v1.csv` 를 기준으로 읽어야 함
- stable default output 과 optional experimental output 은 혼동하면 안 됨
