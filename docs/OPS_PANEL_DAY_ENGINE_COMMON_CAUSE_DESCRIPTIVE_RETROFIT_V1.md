# OPS_PANEL_DAY_ENGINE_COMMON_CAUSE_DESCRIPTIVE_RETROFIT_V1

## 목적
- breadth retrofit candidate를 고른 것만으로 끝내지 않고, 실제 step 4 case set에서 설명력이 얼마나 늘어나는지 확인한다.
- detector logic은 바꾸지 않고, selected breadth rule을 descriptive retrofit으로만 검증한다.

## 왜 candidate selection만으로는 부족했나

직전 retrofit audit은 tied candidate 중:

- 가장 덜 넓고
- 가장 단순하며
- labeled overlap 기준으로 viable한

rule 하나를 골랐다.

하지만 그 결과만으로는 아직 step 4가 실제로 개선됐다고 말하기 어렵다.

남은 질문은:

- 기존 current marker만 썼을 때 설명률이 얼마였는가
- 선택한 breadth marker를 단독으로 쓰면 얼마까지 오르는가
- 둘을 합치면 실제 step 4 positive bucket 설명률이 얼마나 늘어나는가
- 동시에 abrupt / precursor negative contamination은 정말 0으로 유지되는가

이다.

## 왜 이건 detector change가 아니라 descriptive retrofit인가

이번 단계는:

- current marker를 버리거나 바꾸지 않는다
- detector threshold도 바꾸지 않는다
- selected breadth rule을 새로운 official detector로 승격하지 않는다

대신 step 4 interpretation layer에서:

- `current_marker_only`
- `breadth_marker_only`
- `combined_marker`

를 나란히 놓고 “설명률”만 다시 계산한다.

즉 이것은 detection logic patch가 아니라  
evaluation/explanation layer의 descriptive retrofit이다.

## 어떤 결과면 step 4를 “completed v2”라고 부를 수 있나

다음이면 그 표현이 정당화된다.

- `non_panel_or_common_cause` 에서 combined 설명률이 current-only 대비 크게 증가
- 증가분이 breadth-only case에서 안정적으로 발생
- `abrupt_or_no_precursor_now` contamination이 0
- `precursor_bearing_detectable_now` contamination도 0

즉 common-cause bucket의 설명 부족이 breadth descriptive retrofit으로 대부분 메워지고, negative bucket을 건드리지 않으면 step 4 scaffold는 한 단계 닫힌다.

## 어떤 결과면 common-cause를 계속 descriptive-only로 둬야 하나

다음이면 그렇게 두는 편이 안전하다.

- combined increment가 작음
- breadth marker가 positive를 별로 더 설명하지 못함
- negative contamination이 생김
- 또는 `neither` case가 여전히 많아 root cause 설명력이 약함

이 경우 common-cause bucket은 여전히 descriptive review bucket으로만 두는 것이 맞다.

## explanation_mode_class 해석

- `current_only`
  - 기존 routing marker만으로 설명되는 case
- `breadth_only`
  - selected breadth rule이 새 설명을 추가한 case
- `both`
  - current와 breadth가 모두 설명하는 case
- `neither`
  - 아직도 step 4 explanation gap이 남은 case
