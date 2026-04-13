# OPS_PANEL_DAY_ENGINE_BRANCH_INVENTORY_AND_FAULT_TAXONOMY_V1

## 왜 지금 full branch inventory가 필요한가

현재 branch는 detector, scorer, operator, label truth, packaging artifact가 많이 쌓여 있습니다.  
다음 phase에서 다시 detector/scorer를 바꾸기 전에:

- 지금 무엇이 실제 baseline인지
- 어떤 파일이 exploratory audit인지
- 어떤 레이어가 다음 단계에서 계속 살아남는지

를 먼저 inventory로 고정할 필요가 있습니다.

## 왜 fault taxonomy가 onset / performance 평가보다 먼저 와야 하나

지금 project evidence를 보면 같은 electrical family 안에서도:

- progressive local precursor expected
- abrupt local precursor unexpected
- unknown temporality

가 섞여 있습니다.

즉 fault type과 temporality를 분리하지 않으면:
- precursor onset labeling
- precursor performance
- non-precursor fault detection/classification performance

를 한 분모에서 섞어 평가하게 됩니다.

그래서 taxonomy를 먼저 정의하고 `recommended_eval_bucket` 으로 다음 단계를 나누는 것이 필요합니다.

## recommended_eval_bucket 사용법

### precursor_bearing
- precursor onset labeling 대상
- precursor lead / hit-rate / top-k evaluation 대상

### abrupt_or_no_precursor
- precursor recall 분모에서는 분리
- non-precursor fault detection / classification performance 쪽에서 해석

### unknown_needs_review
- onset 정의가 아직 불안정하거나
- monitor / unexplained / common-cause처럼 따로 해석이 필요한 bucket
- 다음 review 후 precursor/non-precursor 쪽으로 재배치

## 이 patch가 하는 일

- branch inventory 생성
  - 각 relevant file을 layer/class/purpose 기준으로 정리
- method layer status 생성
  - detector / scorer / operator / label_truth / evaluation / packaging 현상태를 한 표로 정리
- fault taxonomy 생성
  - 현재 branch terminology와 generated evidence만으로 지지되는 coarse family/pattern bucket만 사용

이 단계는 detector logic 변경이 아니라,
다음 onset/performance design 전에 branch 상태와 fault bucket definition을 고정하는 audit layer입니다.
