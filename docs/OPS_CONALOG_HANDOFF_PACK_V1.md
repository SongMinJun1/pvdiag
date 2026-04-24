# OPS Conalog Handoff Pack V1

## 목적
- 본 문서는 conalog stable handoff foundation pack의 공식 실행 경로와 stable/reference output 구분을 설명하는 운영 문서임.
- panel multiaxis verdict가 primary 임.
- conalog는 direct operational interpretation layer 임.
- GPVS는 reference-only 임.
- heuristic은 field-trial triage only 임.

## 문서 경계
- 본 문서는 `stable/handoff contract`를 설명하는 문서다.
- runtime redesign / hybrid artifact 정책과 같은 층의 문서가 아니며, operator-facing headline 정책도 자동으로 공유하지 않는다.
- 두 경로를 함께 읽을 때는 [OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md) 를 먼저 참조한다.

## 실행 entrypoint
```bash
python app/run_conalog_infer.py --help
```

## stable mode
- stable mode 는 아래 primary output 만 반환함.
  - `conalog_panel_result_v1.csv`
  - `conalog_run_metadata_v1.json`
- stable CSV 는 아래 6개 계약 컬럼을 사용함.
  - `site`
  - `panel_id`
  - `패널고장여부_ko`
  - `사건유형_ko`
  - `최종고장양상_ko`
  - `conalog_원인군_ko`

## reference mode
- reference mode 는 stable output 을 유지하면서 필요 시 아래 sidecar 를 추가할 수 있음.
  - `conalog_reference_sidecar_v1.csv`
- sidecar 안의 GPVS field 는 reference-only 임.
- sidecar 안의 heuristic field 는 triage-only 임.
- 둘 다 direct root-cause output 이 아님.

## dry-run
- dry-run 은 input/config/path 를 검증하고 run plan metadata 만 생성함.
- full production run binding 없이도 handoff contract 를 미리 점검할 수 있게 하는 목적임.

## stable vs experimental/reference 구분
- stable output 은 외부 handoff 계약으로 사용할 primary conalog-facing output 임.
- GPVS 와 heuristic 은 stable primary output 이 아니라 experimental/reference sidecar 로만 분리해야 함.
- 따라서 research tree 전체를 handoff contract 로 그대로 노출하면 안 됨.
