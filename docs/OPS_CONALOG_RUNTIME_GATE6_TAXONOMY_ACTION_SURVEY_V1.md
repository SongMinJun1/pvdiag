# OPS Conalog Runtime Gate 6 Taxonomy and Action Survey V1

## 1. 목적
- 본 문서는 `OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md`의 Gate 6에서 바로 `최종 taxonomy`를 잠그기 전에 필요한 `분류 축 조사 문서`다.
- 목적은 아래 일곱 가지다.
  - 현재 코드, 회의록, 기존 운영 문서에 이미 존재하는 분류 축을 한곳에 모은다.
  - 너무 작은 단일 taxonomy로 섣불리 고정하는 것을 막는다.
  - `원인`, `현상`, `범위`, `시간양상`, `행동 권고`, `안전/차단`, `확신도`를 서로 다른 축으로 분리한다.
  - 현재 runtime family와 기존 phenotype/actionability 문서를 연결한다.
  - 무엇이 이미 있고, 무엇이 빠져 있으며, 무엇이 아직 섞여 있는지 드러낸다.
  - Gate 6를 `6A 조사/구조화`와 `6B 정책 잠금`의 2단계로 재정의한다.
  - 이후 taxonomy/action patch가 어떤 축을 건드리는지 추적 가능하게 만든다.

## 2. 왜 기존 초안이 너무 좁았는가
- 기존 Gate 6 초안은 아래를 너무 빨리 한 줄 taxonomy로 접으려 했다.
  - `음영 / 오염 / 고장 / MLPE 응답 / 점검 권고`
- 하지만 실제 자료를 보면 이미 더 많은 축이 존재한다.
  - 모듈 내부/서브스트링/다이오드/접속 불량
  - 센서/피드백/계측/제어응답
  - 외부 계통/공통원인/그룹 오프
  - 전기 phenotype, shape phenotype, instability phenotype
  - maintenance actionability
  - 원격 차단/안전 차단/외부 센서 연동
  - 설치 초기 불량 vs 운영 중 고장
- 따라서 Gate 6는 `운영 분류 이름표` 하나를 잠그는 단계가 아니라, 먼저 `다축 inventory`를 만드는 단계가 되어야 한다.

## 3. 사용 규칙
- 이 문서는 `조사 문서`다. 아직 최종 정책 잠금 문서는 아니다.
- Gate 6가 열려 있는 동안 허용되는 작업:
  - 현재 분류 축 inventory 정리
  - 축 간 충돌 정리
  - 빠진 범주 식별
  - 후보 taxonomy draft 작성
- Gate 6가 잠기기 전 금지되는 작업:
  - top1 family만으로 모든 운영 액션을 고정
  - 회의록 요구를 반영하지 않은 단일 taxonomy로 report schema 확정
  - safety/차단 축을 maintenance 축에 그대로 덮어쓰기

## 4. 상태
- 현재 상태:
  - `survey draft`
- 의미:
  - 현재 존재하는 분류/행동 축을 넓게 모은 단계이며, 이 다음에 `정책 잠금`이 와야 한다.

## 5. 현재 코드와 문서에 이미 존재하는 분류 축
### 5.1 raw-only runtime cause candidates
현재 heuristic 후보:
- `부분음영형`
- `오염형`
- `열화형`
- `다이오드·서브스트링형`
- `접속·부분개방형`
- `센서·피드백형`
- `제어응답형`
- `외부계통교란형`
- `전력변환부형`
- `원인미확정`

출처:
- [build_panel_day_engine_runtime_heuristic_v1.py](/Users/b9gc/pvdiag/research/prognostics/build_panel_day_engine_runtime_heuristic_v1.py)

### 5.2 operator-facing display name layer
현재 사람이 읽는 이름:
- `다이오드·국소 회로 이상형`
- `접촉 끊김 형`
- `장치 측정 이상형`
- `장치 응답 이상형`
- `전력변환부 이상형`
- `외부 전원 흔들림형`

출처:
- [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py)

### 5.3 phenotype / dominant family 계열
기존 문서와 리포트에는 아래 축도 이미 존재한다.
- phenotype:
  - `compound`
  - `shape`
  - `instability`
  - `unclear`
- dominant family:
  - `electrical`
  - `shape`
  - `instability`

출처:
- [docs/reports/multisite_latest_summary.md](/Users/b9gc/pvdiag/docs/reports/multisite_latest_summary.md)

### 5.4 critical phenotype / actionability 계열
기존 운영 문서에는 아래 축도 있다.
- phenotype:
  - `electrical_fault_like`
  - `open_or_device_issue_like`
  - `group_or_inverter_side_like`
  - `shape_only_monitor`
  - `weak_critical_candidate`
  - `common_cause_borderline`
  - `singleton_borderline_review`
  - `singleton_monitor_hold`
- actionability:
  - `maintenance_candidate`
  - `common_cause_review`
  - `singleton_review`
  - `monitor_only`

출처:
- [OPS_CRITICAL_ACTIONABILITY_V3.md](/Users/b9gc/pvdiag/docs/OPS_CRITICAL_ACTIONABILITY_V3.md)
- [OPS_CRITICAL_PHENOTYPE_SHADOW_V2.md](/Users/b9gc/pvdiag/docs/OPS_CRITICAL_PHENOTYPE_SHADOW_V2.md)

### 5.5 vendor / truth 계열
기존 truth/eval 계열에는 아래 family가 보인다.
- `diode_like`
- `module_damage_like`
- `group_or_inverter_side_like`
- `none_visible`

출처:
- [evaluate_gpvs_fault_family_f1.py](/Users/b9gc/pvdiag/research/prognostics/evaluate_gpvs_fault_family_f1.py)

## 6. 회의록에서 추가로 요구하는 축
회의록을 보면 운영 요구는 단순 `음영/오염/고장`보다 넓다.

### 6.1 원인/유형 축
- 음영
- 오염
- 제품 자체 특성/결함
- 서브스트링/내부 소재/다이오드 고장
- 운영 중 고장 vs 설치 후 발견되는 태생적 불량
- 전압/전류/온도/위치/시계열을 함께 본 유형 분류

### 6.2 액션 축
- 세척
- 음영 구조 개선
- 옵티마이저 추가 조립/구성 변경
- 현장 출동 전 준비 품목 결정
- 자동 차단
- 모듈 단위 차단
- 스트링/접속반 단위 차단
- 사람이 수동 판단하기 전에 시스템이 먼저 차단

### 6.3 안전/제어 축
- RSP/RSD 사용 여부
- 외부 센서 연동
- 모듈 차단 vs 스트링/접속반 차단
- 발전 손실 최소화 vs 화재 안전 우선

### 6.4 범위 축
- 모듈 국소 문제
- 스트링/어레이 영향
- 접속반/그룹 영향
- 외부 센서/외부 화재 영향

## 7. Gate 6에서 실제로 분리해야 하는 축
Gate 6는 하나의 taxonomy가 아니라 아래 축들의 조합으로 봐야 한다.

### 7.1 Cause Axis
질문:
- 무엇이 원인에 가장 가까운가

후보:
- `부분음영형`
- `오염형`
- `열화형`
- `다이오드·서브스트링형`
- `접속·부분개방형`
- `센서·피드백형`
- `제어응답형`
- `전력변환부형`
- `외부계통교란형`
- `설치 초기 불량 가능성`
- `원인미확정`

### 7.2 Electrical Phenotype Axis
질문:
- 전기적으로 어떤 모습인가

후보:
- `전압강하형`
- `전류단절형`
- `출력붕괴형`
- `전압 유지 + 전류 저하형`
- `전압강하 + 전류 유지형`
- `간헐 회복/재발형`
- `dead-like`
- `critical vdrop형`
- `shape-only anomaly`
- `instability-like`

### 7.3 Temporal Axis
질문:
- 시간 전개는 어떤가

후보:
- `전조형 고장`
- `급작 고장`
- `진행성 악화`
- `급격 종료`
- `급작 발생`
- `만성 경보형`
- `short alert run`
- `medium alert run`
- `chronic alert run`

### 7.4 Scope / Locus Axis
질문:
- 문제 범위가 어디까지인가

후보:
- `모듈 국소`
- `서브스트링 국소`
- `MLPE/모듈 장치 국소`
- `스트링/그룹`
- `인버터/전력변환부`
- `외부 계통`
- `공통원인`
- `접속반/차단 범위 확장 필요`

### 7.5 Safety / Control Axis
질문:
- 차단/안전 측면에선 어떤 lane인가

후보:
- `모니터링 우선`
- `현장 점검 우선`
- `원격 차단 연계 검토`
- `모듈 차단 후보`
- `스트링/접속반 차단 후보`
- `외부 센서 확인 필요`
- `화재안전 우선 정책 검토`

### 7.6 Actionability Axis
질문:
- 운영자는 무엇을 해야 하나

후보:
- `monitor_only`
- `singleton_review`
- `common_cause_review`
- `maintenance_candidate`
- `세척 전후 비교`
- `음영 구조 확인`
- `배선/접속부 점검`
- `MLPE/계측 동시 점검`
- `외부 전원/공통원인 우선 확인`
- `최근 작업 이력 확인`

### 7.7 Confidence / Evidence Axis
질문:
- 얼마나 확실한가

후보:
- `원인미확정`
- `보통`
- `중간`
- `높음`
- `공동상위후보`
- `단일우세`
- `2강경합`
- `다자경합`

## 8. 현재 가장 큰 혼선
### 8.1 원인 축과 현상 축이 섞여 있음
- `다이오드·서브스트링형`은 원인에 가깝다.
- `전압강하형`은 현상에 가깝다.
- 둘을 같은 레벨에서 top1으로 경쟁시키면 혼선이 생긴다.

### 8.2 maintenance action과 safety action이 섞여 있음
- `세척 권고`와 `모듈/스트링 차단`은 같은 종류의 액션이 아니다.
- 하나는 maintenance lane, 다른 하나는 safety/control lane이다.

### 8.3 panel-local fault와 common-cause가 섞여 있음
- 회의록은 분명히 모듈 국소와 스트링/접속반/외부 공통원인을 구분하라고 말한다.
- 현재 일부 분류는 이 둘을 한 family 수준에서 경쟁시킨다.

### 8.4 MLPE 특성 축이 단순 cause label에 흡수되고 있음
- `제어응답형`, `센서·피드백형`, `전력변환부형`은 MLPE 환경에선 중요하다.
- 그런데 운영 표면에선 `장치 측정 이상형` 정도로만 보이면 정보가 많이 손실된다.

## 9. Gate 6를 어떻게 다시 정의할 것인가
### 9.1 Gate 6A. Survey / Inventory
먼저 해야 할 것:
- 현재 존재하는 분류 축을 전부 inventory로 모은다.
- 축별로 `원인`, `현상`, `범위`, `행동`, `확신도`, `안전`을 분리한다.
- 누락된 범주와 중복된 범주를 표시한다.

산출물:
- 본 문서
- 축별 example table
- decision log 질문 목록

### 9.2 Gate 6B. Policy Lock
그 다음 해야 할 것:
- operator-facing에 노출할 축을 정한다.
- top-level result object를 몇 축으로 보여줄지 정한다.
- 어떤 액션 축이 maintenance인지 safety인지 나눈다.
- raw-only / official current / precursor / fault signal 각각에 어떤 축까지 노출할지 잠근다.

## 10. 권장 결과 구조
단일 `top1 family`만 보여주는 구조보다 아래처럼 다축 구조가 안전하다.

### 10.1 예시 구조
- `문제 대분류`
  - electrical / shape / instability / common-cause / control
- `운영 분류`
  - 음영 / 오염 / 다이오드 / 접속 / 센서 / MLPE 응답 / 외부 전원
- `현상 축`
  - 전압강하 / 전류단절 / 출력붕괴 / 간헐 회복
- `범위 축`
  - 모듈 / 그룹 / 인버터 / 외부
- `action lane`
  - monitor / maintenance / common-cause review / safety shutdown review
- `상세 후보`
  - top1/top2/top3

### 10.2 왜 이 구조가 좋은가
- 원인과 현상을 혼동하지 않는다.
- safety/control 축을 maintenance 축과 분리할 수 있다.
- 회의록에서 요구한 차단 범위와 현장 조치를 함께 다룰 수 있다.
- 현재 코드에 이미 존재하는 가족군을 버리지 않고 흡수할 수 있다.

## 11. 현재 자료 기준으로 빠져 있는 후보 범주
현재 Gate 6 초안에서 추가 검토가 필요한 범주:
- `설치 초기 불량/제조 편차`
- `제품 자체 특성/결함`
- `그룹/인버터 측 공통원인`
- `접속반/차단 범위 확장 필요`
- `외부 센서/외부 화재 감지 연계`
- `보안/원격 제어 운용 lane`
- `작업일/운영 이벤트 영향`
- `노후/열화 vs 오염의 분리 기준`

## 12. Decision Log에 바로 올릴 질문
- Gate 6의 최상위 축은 `원인`이 되어야 하는가, `문제 대분류`가 되어야 하는가
- maintenance action과 safety action을 같은 report에서 같이 보여줄 것인가
- `제어응답형`과 `센서·피드백형`을 MLPE 전용 별도 lane으로 격상할 것인가
- `공통원인`을 cause family로 둘 것인가, scope axis로 분리할 것인가
- `설치 초기 불량 가능성`은 top-level category인가, investigation note인가
- operator-facing 표에서 몇 개 축까지 노출할 것인가

## 13. Gate 6 체크리스트
- taxonomy가 하나의 단일 축으로 과도하게 압축되지 않았는가
- 원인 / 현상 / 범위 / 행동 / 안전이 분리되어 있는가
- 회의록에서 요구한 차단 범위와 운영 액션이 taxonomy에 흡수되어 있는가
- current 코드의 후보 family를 버리지 않고 흡수할 수 있는가
- action recommendation이 cause family 하나만 보고 임의로 나오지 않는가

## 14. 근거 source
- [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- [build_panel_day_engine_runtime_heuristic_v1.py](/Users/b9gc/pvdiag/research/prognostics/build_panel_day_engine_runtime_heuristic_v1.py)
- [runtime_rawonly_chain_common_v1.py](/Users/b9gc/pvdiag/research/prognostics/runtime_rawonly_chain_common_v1.py)
- [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py)
- [OPS_CRITICAL_ACTIONABILITY_V3.md](/Users/b9gc/pvdiag/docs/OPS_CRITICAL_ACTIONABILITY_V3.md)
- [3사 회의록.md](</Users/b9gc/Documents/1. 현장 시스템과 현재 구축 상태/3사 회의록.md>)

## 15. 다음 연결 문서
- 상위 로드맵:
  - [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- 교차 게이트 설계 허점 감사:
  - [OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md)
- Gate 5 출력 정책 초안:
  - [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- Gate 6B taxonomy/action policy lock:
  - [OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1.md)
- 결정 로그 템플릿:
  - [OPS_CONALOG_RUNTIME_DECISION_LOG_TEMPLATE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_TEMPLATE_V1.md)
- 브랜치/파킹 로트 템플릿:
  - [OPS_CONALOG_RUNTIME_BRANCH_PARKING_LOT_TEMPLATE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_PARKING_LOT_TEMPLATE_V1.md)
