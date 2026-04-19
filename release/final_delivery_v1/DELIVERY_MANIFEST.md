# Delivery Manifest

## 먼저 볼 것
1. `package/stable_handoff/`
2. `package/runtime/`
3. `package/oneclick/`

## 폴더별 의미
- `package/stable_handoff/`: stable handoff docs/config/examples
- `package/runtime/`: runtime guide, failure handling, latency/readiness report, runtime config
- `package/oneclick/`: one-click guide, daily-report guide, template
- `package/docs/`: comparison, GPVS inventory, GPVS mail draft, coverage/performance, integrated table pointer
- `package/examples/`: stable snapshot, reference-only summary, triage-only summary

## 주의
- stable / reference_only / triage_only 구분은 `final_delivery_manifest_v1.csv` 를 기준으로 읽어야 함
