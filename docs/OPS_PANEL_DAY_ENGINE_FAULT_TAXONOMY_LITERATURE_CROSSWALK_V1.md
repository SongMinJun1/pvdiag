# OPS_PANEL_DAY_ENGINE_FAULT_TAXONOMY_LITERATURE_CROSSWALK_V1

## 왜 branch-grounded taxonomy v1만으로는 부족했는가

`fault_taxonomy_v1` 는 현재 branch evidence를 고정하는 데는 충분했습니다.  
하지만 step 3 precursor evaluation으로 넘어가려면 추가로 구분해야 하는 질문이 있습니다.

- literature에서도 precursor-capable로 여겨지는 family인가
- 현재 `panel_day_engine` daily electrical pipeline이 실제로 볼 수 있는 family인가
- step 3 precursor-bearing 성능 분모에 바로 넣어도 되는가

즉 branch evidence만으로는 “현재 branch에서 본 것”은 정리되지만,  
“어떤 family를 precursor-bearing evaluation 대상으로 정당화할 수 있는가”는 아직 부족했습니다.

## 왜 literature crosswalk가 필요한가

PV fault literature는 대체로 다음을 구분합니다.

- electrical characterisation:
  - voltage/current, I-V, power-loss, model-based electrical monitoring
- thermal / IR:
  - hotspot, thermal anomaly localization
- EL / visual:
  - crack, delamination, corrosion, discoloration, hidden structural defects
- inverter / system-level diagnostics:
  - inverter switch, diode, capacitor, sensor fault

현재 branch의 `panel_day_engine` 는 panel-day electrical persistence 위에 서 있으므로,  
step 3에서 평가할 분모는 literature상 precursor-capable이면서도 현재 daily electrical pipeline이 다룰 수 있는 family로 한정해야 합니다.

## eval_bucket_v2 사용법

### 1) precursor_bearing_detectable_now
- step 3 precursor-bearing performance 분모
- precursor onset truth / hit-rate / lead-time 평가 대상

### 2) precursor_capable_but_not_detectable_now
- literature상 precursor-capable이지만
- 현재 panel_day_engine daily electrical pipeline으로 직접 보기 어려운 family
- future modality expansion 후보

### 3) abrupt_or_no_precursor_now
- step 3 precursor-bearing recall 분모에서는 제외
- step 4에서 non-precursor / abrupt detection-classification 성능으로 해석

### 4) non_panel_or_common_cause
- panel-local precursor detector 책임 분모가 아님
- step 4에서 common-cause / inverter-side 계열로 별도 해석

### 5) unknown_needs_review
- branch evidence와 literature를 연결했어도 아직 family 경계가 불안정한 경우
- onset/performance 분모에 넣기 전에 review가 더 필요한 bucket

## explicit rule table 원칙

이번 crosswalk는 hidden heuristic이 아니라 코드 안의 explicit rule table을 사용합니다.

- 입력 taxonomy row를 그대로 유지
- row별로 literature precursor-capable 여부를 명시
- row별 preferred sensor modality를 명시
- row별 eval_bucket_v2를 명시

즉 micro-family를 새로 발명하지 않고, 현재 branch가 이미 지원하는 coarse row 위에만 literature grounding을 덧댑니다.

## representative literature grounding

- PV module failure/degradation review:
  - electrical characterisation, IR, EL/visual modality를 폭넓게 정리
  - cracked cells, delamination, corrosion, hotspot, bypass-diode related shifts가 electrical/IR/EL에서 어떻게 보이는지 요약
  - https://www.mdpi.com/2673-9941/4/1/3
- PV module fault diagnosis review:
  - electrical characteristic based diagnosis와 image processing 기반 diagnosis를 함께 정리
  - step 3의 “detectable now”를 daily electrical pipeline 기준으로 제한해야 함을 뒷받침
  - https://doi.org/10.1016/j.solener.2025.113489
- Visual PV fault diagnosis review:
  - EL, IR, PL이 cracks, delamination, hotspot, discoloration 같은 fault를 visual modality로 다룬다는 점을 정리
  - https://doi.org/10.1016/j.rineng.2024.102622
- Inverter fault diagnosis review:
  - inverter/system-level precursor-like diagnostics는 존재하지만 modality가 panel-local daily electrical과 다름을 보여 줌
  - https://doi.org/10.3390/machines12090631

## 해석 포인트

- progressive local electrical/module-damage family:
  - literature상 precursor-capable이고
  - branch onset truth도 이미 존재하므로
  - `precursor_bearing_detectable_now`
- group_or_inverter_side_like:
  - literature상 diagnostic target은 맞지만
  - modality가 inverter/system-level이므로
  - `non_panel_or_common_cause`
- none_visible / monitor / unexplained:
  - branch 운영 artefact로는 중요하지만
  - literature-grounded precursor-bearing fault family로 바로 쓰기 어렵다

## 이 patch가 바꾸지 않는 것

- detector logic
- canonical truth template contract
- existing scorer/operator pipeline

이 단계는 step 3 precursor evaluation 전에  
“무슨 family를 지금 평가 분모에 넣을 것인가”를 literature와 branch evidence 둘 다로 고정하는 audit layer입니다.
