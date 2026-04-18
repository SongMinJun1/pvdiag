# OPS Fault Validation Matrix V1

## validation purpose
- 본 문서는 current pipeline의 첫 공식 field-trial validation matrix 정의서임.
- detector logic을 다시 정의하지 않고, 현재 frozen front-facing outputs 사이의 consistency와 surrogate pathway registration을 점검하는 목적임.
- panel multiaxis verdict가 primary 임. conalog는 direct operational interpretation layer 임. GPVS는 reference-only 임. cause candidate heuristic은 triage-only 임.

## core validation set
- core validation set은 현재 고장 패널 6건임.
- 본 cycle에서는 full historical evaluation 대신 frozen snapshot consistency check를 우선 수행함.
- 따라서 core rows의 actual_output_ko는 current frozen outputs에서 직접 읽을 수 있으며, measured field performance 자체를 재산정한 값은 아님.

## acceptance axes
- `패널고장여부`
  - panel multiaxis verdict와 final integrated table이 같은 fault status를 유지하는지 점검함.
- `사건유형`
  - primary event type이 frozen panel verdict와 integrated table에서 일관되는지 점검함.
- `최종고장양상`
  - terminal failure pattern이 일관되는지 점검함.
- `conalog 원인군`
  - conalog direct operational interpretation layer가 integrated table에 그대로 반영되는지 점검함.
- `heuristic competition type`
  - 단일우세 / 2자경합 / 다자경합 상태가 공동상위후보 목록과 일치하는지 점검함.
- `heuristic action-note wording alignment`
  - heuristic action note가 competition state와 후보 순서에 맞게 생성되는지 점검함.

## surrogate tests
- `부분음영형 surrogate`
  - front-facing suspected-cause lane으로 등록되어 있는지 점검함.
- `접촉 끊김 형 surrogate`
  - display-friendly label lane으로 등록되어 있는지 점검함.
- `장치 측정 이상형 surrogate`
  - 장치 측정 이상형 display lane이 현재 output에 노출되는지 점검함.
- `장치 응답 이상형 surrogate`
  - 장치 응답 이상형 display lane이 현재 output에 노출되는지 점검함.
- `GPVS attach on/off fallback test`
  - backfill dry-run에서 attach on/off 시 fallback behavior가 계약대로 동작하는지 점검함.
- `sparse conalog test`
  - conalog 정보가 sparse한 row는 conservative하게 유지되고 suspected cause를 blank 처리하는지 점검함.

## 현재 단계의 범위
- validation framework first 단계임.
- surrogate rows는 synthetic/skeleton expected-vs-actual placeholder를 허용하되, report의 `note_ko`에 framework placeholder 성격을 명시해야 함.
- 본 단계는 full historical replay, measured performance optimization, detector retraining 단계가 아님.
