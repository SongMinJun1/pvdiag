# OPS Conalog MLPE Runtime Redesign V1

## 1. 목적
- 본 문서는 `conalog` MLPE 기반 PV 진단/리포트 파이프라인의 원본 설계 정리 문서다.
- 이번 문서는 `release/` package 산출물 설명이 아니라, 원본 repo 기준의 상위 설계 원칙을 정리하는 목적이다.
- 특히 아래 세 가지를 분리해 정리한다.
  - MLPE 환경을 전제로 한 신호/사건 해석 원칙
  - 전조, 고장 신호, 원인 분류, 정비 액션을 분리하는 리포트 구조
  - 원본 source tree 와 release package 의 책임 경계

## 2. 범위
- 포함 범위:
  - MLPE 기반 PV 모듈 단위 신호 해석
  - precursor 탐지
  - hard fault evidence 탐지
  - 사건유형/최종고장양상 해석
  - 원인 후보 분류
  - 발전 손실 보고서
  - 정비/운영 액션 연결
  - 원격 차단과 연계되는 운영 해석 축
- 제외 범위:
  - ESS / 배터리 / PCS-배터리 리플 진단
  - 저장 예측 / 저장 최적화
  - 배터리 화재 가설 검증
  - PV 외 자산까지 포함하는 통합 에너지 최적화

## 3. 기본 전제
- 본 알고리즘은 MLPE 환경을 전제로 한다.
- 따라서 `MLPE 있음/없음`은 site-level feature flag 가 아니라 전역 해석 가정이다.
- 해석의 기본 단위는 스트링이 아니라 모듈 단위이며, peer-relative signal 이 중심이다.
- MLPE 환경에서는 패널 전기 거동이 DCDC/제어 개입을 거쳐 보일 수 있으므로, 전압/전류/출력 조합을 스트링형 직관으로 단순 번역하면 안 된다.
- 이번 단계의 운영 목적은 단순 탐지보다 아래에 더 가깝다.
  - 발전 손실 설명
  - 고장/음영/오염/비패널 원인 구분
  - 현장 정비 판단 지원
  - 필요 시 자동/원격 차단과 연결되는 안전 판단 지원

## 4. 회의록에서 확인된 상위 요구
- 회의록은 현재 시스템의 주요 산출물이 `발전 손실 보고서`이며, 여기서 고장 모듈, 현재 발전량, 음영 상태 등을 함께 설명해야 한다고 밝힌다.
- 회의록은 MLPE 환경에서 모듈 하나 문제가 전체 스트링을 같이 죽이는 구조가 아니라, 모듈 단위로 분리해서 해석해야 함을 전제로 둔다.
- 회의록은 `전압, 전류, 온도, 위치, 시계열`을 함께 보고 더 세밀한 고장 유형 분류가 가능해야 함을 시사한다.
- 회의록은 `조기 이상 신호 기반 자동 차단`을 이번 과제의 핵심 차별점으로 설명한다.
- 회의록은 `이게 고장인지, 음영인지, 완전한 고장인지`를 교차검증하는 알고리즘 방향을 명시한다.
- 회의록은 `상대값 진단`을 핵심 철학으로 제시한다.
- 회의록은 초기 보고서가 `현재 손실`, `해결 가능한 부분`, `해결 불가능한 부분`을 나눠 제시해야 한다는 운영 관점을 준다.

## 5. 해석 철학
- 단일 신호 하나로 사건을 설명하지 않는다.
- 전조와 확정 신호를 같은 뜻으로 쓰지 않는다.
- 사건유형(event type)과 최종고장양상(terminal pattern)을 분리해서 읽는다.
- 탐지(detection)와 재검증(revalidation)을 분리한다.
- 상대값 진단을 기본으로 하고, 절대값 threshold 는 보조로만 사용한다.
- MLPE 환경에서는 `전압 유지 + 전류 저하`, `전압강하 + 전류 유지`, `출력만 붕괴`, `간헐 회복/재발` 같은 패턴 조합을 더 중시한다.
- report layer 는 upstream canonical field 를 설명하는 역할을 해야지, 과도하게 재추론하는 역할을 맡아서는 안 된다.

## 6. 전체 파이프라인 층위
### 6.1 원시 신호층
- 입력:
  - 모듈 단위 전압/전류/출력 시계열
  - peer-relative normalization 결과
  - coverage / group-off / site event 관련 상태
- 주요 필드:
  - `mid_ratio`
  - `mid_v_ratio`
  - `mid_i_ratio`
  - `v_drop`
  - `state_dead`
  - `critical_like`
  - `pre_ews`
  - `ews_warning`

### 6.2 hard evidence 층
- 목적:
  - 안전/확정 fault 쪽의 강한 신호를 정의
- 주요 필드:
  - `confirmed_fault`
  - `critical_fault`
  - `critical_confirmed`
  - `final_fault`
- 해석 원칙:
  - `critical_fault` 는 전압강하형 sustained strong evidence 축이다.
  - `final_fault` 는 dead-like confirmed 또는 confirmed critical 을 포함하는 최종 확정 축이다.
  - 이 둘은 전조와 동일 개념이 아니다.

### 6.3 precursor 층
- 목적:
  - hard evidence 이전 단계의 다축 누적 이상을 추적
- 주요 필드:
  - `pre_ews`
  - `pre_alarm`
  - `prefault_cond_ae`
  - `prefault_cond_dtw`
  - `prefault_cond_ews`
- 해석 원칙:
  - hard evidence 가 없는 상태에서 multi-axis / multi-day 누적이 있을 때만 precursor 로 승격한다.
  - same-day fallback onset 은 약한 증거로만 취급한다.

### 6.4 사건 해석층
- 목적:
  - 신호를 panel/event 수준의 시간 해석으로 올림
- 주요 필드:
  - `사건유형_ko`
  - `최종고장양상_ko`
  - `earliest_warning_date`
  - `strict_trigger_date`
  - `first_final_fault_date`
- 해석 원칙:
  - precursor 가 확인된 사건은 abrupt ending 이 있어도 event class 자체를 pure abrupt 로 보지 않는다.
  - `전조형 고장 / 급격 종료`와 같은 조합은 허용한다.

### 6.5 원인 후보층
- 목적:
  - 관측 신호와 사건 해석을 바탕으로 원인 family 와 후보를 부여
- 주요 필드:
  - `커널로그_원인군_ko`
  - `1순위_의심원인_ko`
  - `2순위_의심원인_ko`
  - `3순위_의심원인_ko`
- 해석 원칙:
  - 원인 후보는 탐지 결과와 별도 축이다.
  - 원인 후보는 direct root-cause 확정명이 아니라 ranked candidate 로 읽어야 한다.

### 6.6 리포트/액션층
- 목적:
  - 운영자/분석가가 행동 가능한 형태로 요약
- 필요한 출력:
  - precursor candidate report
  - fault signal report
  - maintenance action report

## 7. 현재 구조의 핵심 문제
- precursor report 가 아래를 한 줄에 섞어 보여준다.
  - precursor 누적
  - hard fault evidence
  - 사건 종결 요약
  - 원인 후보
- `critical/final` 같은 internal wording 이 report 로 새어 나왔다.
- `전조`와 `확정 경로`가 같은 문맥에서 읽혀 해석 혼선이 생긴다.
- live/raw-only/report build 층에서 helper 와 schema 가 중복 구현돼 drift 위험이 있다.
- release packaging 층이 research/source 층과 나란히 살아 있어, source of truth 가 흐려질 수 있다.

## 8. 목표 리포트 구조
### 8.1 precursor_candidates
- 의미:
  - 아직 hard evidence 는 없지만 precursor 누적이 강한 패널
- 포함 조건:
  - `final_fault`, `critical_fault`, `critical_confirmed` 미동반
  - multi-axis precursor evidence 존재
- 대표 컬럼:
  - `운영 판정`
  - `전조 시작일`
  - `전조 축`
  - `대표 전조 신호`
  - `상위 해석 후보`
  - `모니터링 권고`

### 8.2 fault_signal_cases
- 의미:
  - hard evidence 가 이미 관측된 패널
- 포함 조건:
  - `final_fault` 또는 `critical_fault` 또는 `critical_confirmed`
- 대표 컬럼:
  - `확정 경로`
  - `hard evidence 요약`
  - `사건유형`
  - `사건 종결 요약`
  - `상위 해석 후보`
  - `현장 점검 권고`

### 8.3 maintenance_action_report
- 의미:
  - 운영자가 실제로 무엇을 해야 하는지 보여주는 action-facing report
- 대표 컬럼:
  - `문제 대분류`
  - `운영 분류`
  - `상세 후보`
  - `해결 가능 여부`
  - `권고 조치`
  - `출동 전 준비 항목`
  - `추가 확인 필요 데이터`

## 9. 분류 체계 목표
### 9.1 대분류
- `전압강하형`
- `전류단절형`
- `출력붕괴형`
- `간헐응답형`
- `비패널/공통원인형`

### 9.2 운영 분류
- `음영 가능성`
- `오염 가능성`
- `다이오드·서브스트링 이상`
- `접속 불량/부분 개방`
- `센서/계측 이상`
- `MLPE 제어응답 이상`
- `외부 계통/공통원인`
- `설치 초기 불량 가능성`
- `노화/열화 가능성`

### 9.3 상세 후보
- 현행 `1/2/3순위_의심원인_ko` 를 유지
- 단, report 에서는 `상세 후보` 또는 `우선 점검 후보`로 명명

## 10. MLPE 환경에서의 해석 규칙
- `mid_v_ratio` 가 유지되고 `mid_i_ratio` 만 크게 낮아지면:
  - 전류 전달 문제
  - 부분 개방
  - 접속 불량
  - 측정/제어 개입
  - MLPE 응답 이상
  를 우선 고려한다.
- `v_drop` 와 `mid_i_ratio 유지` 조합은:
  - bypass / diode / 서브스트링 계열을 우선 고려한다.
- `mid_ratio` 만 붕괴하고 회복/재발이 반복되면:
  - 간헐 fault
  - 제어응답형
  - 외부 이벤트 연동 가능성
  을 함께 본다.
- group-off / site-event / common-cause 는 panel-local fault 와 다른 bucket 으로 분리한다.

## 11. 운영 프로파일
- `MLPE 있음/없음`은 profile 이 아니라 전역 가정이다.
- 별도 profile 로 관리할 것은 아래다.
  - `RSD/RSP 사용 가능 여부`
  - `원격 차단 가능 여부`
  - `차단 단위`
    - 모듈 / 스트링 / 사이트
  - `외부 센서 연동 여부`
  - `상시 음영 구역 여부`
  - `운영 작업 이벤트 반영 여부`
  - `통신 안정성/지연`
- 이 정보는 `site_profile`보다 `control_profile` 또는 `operational_profile` 이름이 더 적합하다.

## 12. 액션 연결 목표
- `세척 권고`
- `음영 구조 개선 검토`
- `배선/접속부 점검`
- `다이오드/모듈 교체 검토`
- `MLPE/옵티마이저 점검`
- `센서/계측 재교정`
- `모니터링 지속`
- `현장 출동 필요`
- `원격 차단 연계 검토`
- `추가 데이터 확보 필요`

## 13. 코드 구조 원칙
- source of truth 는 원본 repo 의 `pv_ae/`, `research/prognostics/`, `docs/`다.
- `release/` package 는 배포 artifact 이며, source of truth 가 아니다.
- report schema 와 설명문 helper 는 build/runtime 에 중복 구현하지 않는다.
- `run_full_algorithm_pack.py` 의 책임은 최소 아래 네 모듈로 분해하는 것이 바람직하다.
  - execution/orchestration
  - semantic schema/helper
  - report rendering
  - explanation wording
- `runtime_rawonly_chain_common_v1.py` 는 event semantics 공용 계층의 seed 로 유지/확장하는 것이 좋다.

## 14. 우선순위
### P0
- precursor 와 hard fault evidence 를 report 상에서 완전히 분리
- precursor report 에서 hard evidence 동반 row 제거
- `fault_signal_cases` report 신설
- `확정 경로` 표시 추가
- 기본 action recommendation 추가

### P1
- MLPE-aware taxonomy 확장
- 운영 분류/상세 후보/조치 권고 연결
- operational/control profile 도입
- 차단용 판단과 정비용 판단 score 분리

### P2
- report schema 공용화
- build/runtime helper 중복 제거
- `run_full_algorithm_pack.py` 모듈 분리
- 평가 체계 분리
  - precursor detection
  - hard evidence detection
  - cause classification
  - action usefulness

## 15. P0 상세 설계
### 15.1 목적
- P0의 목적은 알고리즘 core 를 다시 짜는 것이 아니라, 현재 source/release report layer 가 섞어 보여 주는 의미를 분리하는 것이다.
- 즉 `전조 후보`와 `hard fault evidence 동반 사례`를 서로 다른 artifact 로 분리하고, 운영자가 각 표를 읽을 때 질문이 섞이지 않게 만드는 것이 우선이다.
- 이번 단계에서는 다음 세 가지를 달성한다.
  - precursor report 의 의미를 `hard evidence 없는 precursor candidate` 로 좁힌다.
  - hard evidence 동반 사례를 별도 `fault_signal_cases` report 로 분리한다.
  - master report 가 두 표의 목적 차이를 먼저 설명하게 만든다.

### 15.2 P0에서 직접 만지는 source of truth
- `research/prognostics/runtime_rawonly_chain_common_v1.py`
  - 사건유형/최종고장양상/event summary 와 관련된 canonical event semantics 레이어
- `research/prognostics/build_conalog_full_runtime_pack_v1.py`
  - pack build 및 artifact/schema 기대치 문서화 레이어
- `research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py`
  - root result artifact 의 존재/컬럼/schema 검증 레이어
- `docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md`
  - 본 상세 설계 문서
- release package 안의 대응 파일은 P0 source 변경 이후 regenerate 대상이지 source of truth 가 아니다.

### 15.3 P0에서 당장 건드리지 않는 것
- `pv_ae/panel_day_engine.py` 내부의 hard evidence / precursor signal 생성 규칙
- event audit 의 fundamental labeling rule
- fault family / cause candidate heuristic 의 점수 체계
- one-click `build_daily_report_v1.py` markdown foundation
- ESS/배터리/PCS 관련 scope

### 15.4 artifact 구조 변경
#### 유지되는 artifact
- `fault_panel_result_precursor_report_v1.csv`
  - 이름은 유지하되 의미를 좁힌다.
- `fault_panel_result_master_report_v1.md`
  - 유지하되 precursor/fault-signal 두 표를 구분 설명한다.

#### 새로 추가되는 artifact
- `fault_panel_result_raw_only_fault_signal_report_v1.csv`
  - `final_fault`, `critical_fault`, `critical_confirmed` 가 관측된 panel 을 별도로 모은다.

#### P0에서 의미가 바뀌는 artifact
- `fault_panel_result_precursor_report_v1.csv`
  - 기존: precursor + hard evidence + 사건 종결 요약 + 원인 후보가 섞인 혼합표
  - 변경 후: hard evidence 미동반 precursor candidate 전용표

### 15.5 row 분기 규칙
#### precursor report 포함 조건
- `전조날짜`가 존재
- 그리고 아래 세 hard evidence 축이 모두 false
  - `final_fault`
  - `critical_fault`
  - `critical_confirmed`
- 그리고 precursor evidence 가 실제로 존재
  - 예: `ews_warning_days`, `pre_ews_days`, `pre_alarm_days`, `prefault_cond_ae_days`, `prefault_cond_dtw_days` 중 하나 이상

#### fault signal report 포함 조건
- 아래 중 하나라도 true
  - `final_fault`
  - `critical_fault`
  - `critical_confirmed`
- precursor 흔적이 같이 있더라도 precursor report 로 보내지 않는다.
- precursor 흔적은 fault signal report 안의 보조 정보로만 유지한다.

### 15.6 precursor report 목표 컬럼
- `site`
- `panel_id`
- `운영 판정`
  - P0에서는 `전조 후보` 또는 빈칸 수준으로 낮춘다.
- `판정 근거`
  - precursor signal 누적 중심 설명만 허용한다.
- `전조날짜`
- `전조 축`
- `대표 전조 신호`
- `전조 요약`
- `상위 해석 후보`
- `기존 알고리즘 source`
- `패턴 설명`
- `모니터링 권고`

#### precursor report 에서 제거/비노출할 항목
- `신호 기준일`
- `급락 종결 관측`
- `점진 저하 누적`
- `사건 종결 요약`
- hard evidence 경로를 직접 드러내는 요약 문구

### 15.7 fault signal report 목표 컬럼
- `site`
- `panel_id`
- `운영 판정`
- `확정 경로`
  - 예: `dead-like confirmed`, `critical_confirmed`, `vdrop hard signal 동반`
- `hard evidence 요약`
  - `final_fault`, `critical_fault`, `critical_confirmed`, `critical_source` 기반
- `전조 시작일`
  - precursor 가 있었던 경우에만 보조로 유지
- `신호 기준일`
- `사건유형`
- `사건 종결 요약`
- `상위 해석 후보`
- `기존 알고리즘 source`
- `패턴 설명`
- `현장 점검 권고`

### 15.8 master report 변경점
- master report 는 표를 보여주기 전에 먼저 아래를 설명해야 한다.
  - precursor report 는 `hard evidence 없는 precursor candidate` 표다.
  - fault signal report 는 `hard evidence 관측 사례` 표다.
  - 두 표는 목적이 다르며 row 가 중복되지 않는다.
- 기존 precursor report 설명에서 `critical/final` shortcut 을 직접 쓰는 문장은 제거한다.
- `current preview` 와 `raw-only current preview` 가 strict subset 임을 지금보다 더 선명하게 적는다.

### 15.9 source 코드 touchpoint별 구현 방향
#### `release/.../run_full_algorithm_pack.py` 에 대응되는 source 측 책임
- 현재 구현상 사람-facing precursor report builder 는 packaged runner 안에 실려 있다.
- source 기준 P0는 아래 함수 책임을 바꾸는 방향으로 간다.
  - `build_precursor_report_df(evidence_df)`
    - hard evidence 동반 row exclusion 로직 추가
    - precursor-only 컬럼 schema 로 축소
  - 신규 `build_raw_only_fault_signal_report_df(evidence_df)` 또는 동등한 raw-only fault signal builder
    - `fault_panel_result_raw_only_fault_signal_report_v1.csv` 생성 책임
  - `build_master_report_markdown(...)`
    - 두 표의 목적 차이를 먼저 설명
- 단, 실제 편집은 packaged copy 가 아니라 source generation 경로에서 먼저 정의하고, release 쪽은 regenerate 대상으로 본다.

#### smoke test 변경 방향
- `research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py`
  - `fault_panel_result_raw_only_fault_signal_report_v1.csv` 존재 검사 추가
  - precursor report required columns 를 precursor-only schema 로 변경
  - fault signal report required columns 새로 추가
  - precursor report 가 empty 가 아니면서 hard evidence 설명 컬럼을 요구하지 않도록 수정

### 15.10 naming 원칙
- `critical/final` 같은 internal shorthand 는 operator-facing column/value 에 직접 쓰지 않는다.
- operator-facing wording 은 아래 수준으로만 노출한다.
  - `강한 고장 신호`
  - `최종 고장 신호`
  - `확정 경로`
  - `hard evidence 요약`
- internal field 명은 유지해도 되지만, artifact 설명문에서는 그대로 노출하지 않는다.

## 16. 왜 기존 P0/P1/P2만으로는 부족했는가
- 기존 `P0 / P1 / P2`는 구현 백로그로서는 유효하지만, 의사결정 로드맵으로는 부족했다.
- 즉, `무엇을 먼저 바꿀지`는 적혀 있었지만 `무엇이 먼저 확정되어야 다음 패치를 해도 되는지`가 빠져 있었다.
- 그 결과 다음과 같은 문제가 반복될 수 있다.
  - report/schema 패치가 먼저 들어가는데, precursor 정의가 나중에 바뀌어 표 이름과 의미가 다시 흔들린다.
  - raw-only 와 official current 역할이 아직 안 잠겼는데 artifact 이름을 고정해 버린다.
  - MLPE 해석 규칙이 아직 안 잠겼는데 전기적 설명 문구를 먼저 최종화한다.
  - action recommendation 을 붙이는데, 정작 고장/음영/오염/제어응답 taxonomy 가 덜 잠겨 있다.
- 따라서 앞으로는 `구현 우선순위`와 별도로 `의사결정 게이트`가 있어야 한다.
- 본 문서의 이후 장은 바로 그 의사결정 게이트를 정의한다.

## 17. Decision-First Roadmap V2
### 17.1 원칙
- 어떤 단계에서든 `정의가 먼저, 패치가 나중`이다.
- 정의가 잠기지 않은 상태에서는 표현층 패치만 허용한다.
- 코어 판정에 영향을 주는 수정은 반드시 그 위 단계의 결정 게이트를 통과한 뒤에만 한다.
- release artifact 정리는 마지막 단계이며, source of truth 는 원본 repo 문서와 source code 다.

### 17.2 단계 개요
1. 범위 고정
2. 용어/역할 고정
3. 신호 분류 체계 고정
4. precursor 승격 규칙 고정
5. hard evidence 경계 고정
6. 출력 정책 고정
7. action/taxonomy 고정
8. 구현 순서 확정
9. 코드 패치
10. 평가/문서/배포 정리

주의:
- 위 순서는 메인 라인 개요일 뿐이고, 실제론 완전한 선형 흐름이 아니다.
- 특히 Gate 6A survey에서 새 축이나 lane 충돌이 발견되면 Gate 3~5를 다시 열 수 있다.
- 이 교차 게이트 허점은 별도 감사 문서 [OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md) 에 정리한다.

### 17.3 Gate 0. 범위 고정
#### 목적
- 이번 작업이 어디까지 다루는지 먼저 고정한다.

#### 이번 프로젝트에서 잠그는 범위
- 포함:
  - MLPE 기반 PV 모듈 진단
  - precursor 탐지
  - hard evidence 탐지
  - 사건 해석
  - 원인 후보 분류
  - 발전 손실 리포트
  - 정비 액션 연결
  - 원격 차단과 연결되는 운영 해석
- 제외:
  - ESS / 배터리 / PCS-배터리 연동 해석
  - 저장 예측 / 저장 최적화
  - 화재 확산/배터리 위험도 모델
  - PV 외 자산 통합 최적화

#### 산출물
- 범위 선언문
- 제외 대상 명시 목록
- 이번 라운드에서 건드리지 않을 코드/문서 목록

#### 통과 조건
- `MLPE PV runtime redesign` 범위가 팀 내에서 같은 뜻으로 읽힌다.
- 배터리/ESS 관련 이슈가 후속 트랙으로 분리된다.

### 17.4 Gate 1. 용어와 역할 고정
#### 목적
- 같은 단어를 다른 뜻으로 쓰는 상황을 끝낸다.

#### 반드시 고정해야 할 용어
- `precursor`
- `precursor candidate`
- `hard evidence`
- `확정`
- `official current`
- `raw-only candidate`
- `raw-only current`
- `raw-only fault signal report`
- `사건유형`
- `최종고장양상`
- `원인 후보`

#### 각 용어의 목표 정의
- `precursor`:
  - hard evidence 이전 단계의 다축 누적 이상
- `precursor candidate`:
  - precursor 규칙을 만족했지만 아직 공식 current/확정은 아닌 운영 추적 대상
- `hard evidence`:
  - `final_fault`, `critical_fault`, `critical_confirmed`처럼 확정 계열 해석에 직접 쓰는 신호
- `official current`:
  - frozen-support live chain 기준으로 외부에 먼저 보여줄 운영 공식 결과
- `raw-only candidate`:
  - panel_day_core 와 precursor gate 위에서 계산한 더 넓은 후보 우주
- `raw-only current`:
  - raw-only candidate 중 strict current subset
- `raw-only fault signal report`:
  - raw-only 후보 우주에서 고장 신호가 이미 관측된 패널 모음

#### 이 단계에서 하면 안 되는 것
- threshold 수정
- precursor 승격 로직 수정
- report 파일명 대규모 변경

#### 산출물
- 용어 사전
- artifact 역할 매핑표

#### 통과 조건
- 같은 용어를 문서/코드/reports에서 같은 뜻으로만 쓴다.
- `raw-only fault signal report`가 official current가 아니라는 점이 문서상 확정된다.

### 17.5 Gate 2. 신호 분류 체계 고정
#### 목적
- 각 신호가 어떤 계층의 신호인지 먼저 분류한다.

#### 분류해야 할 신호군
- precursor 축:
  - `pre_ews`
  - `ews_warning`
  - `pre_alarm`
  - `prefault_cond_mid`
  - `prefault_cond_ae`
  - `prefault_cond_dtw`
  - `prefault_cond_ews`
- hard evidence 축:
  - `critical_fault`
  - `critical_confirmed`
  - `final_fault`
- 중간 해석 축:
  - `fault_like_day`
  - `event_A`
  - `critical_source`
  - `anom_subtype`
- 설명용 축:
  - `mid_ratio`
  - `mid_v_ratio`
  - `mid_i_ratio`
  - `v_drop`

#### 이 단계에서 답해야 하는 질문
- `fault_like_day`는 precursor 강화 신호인가, hard-evidence 전단계인가?
- `vdrop`는 hard evidence 자체인가, hard-evidence-adjacent clue 인가?
- `critical_source`는 사용자 표에 직접 노출 가능한가, 내부 보조정보로만 둘 것인가?
- `event_A`는 전조 신호로 쓸지, 패턴 설명용으로만 쓸지?

#### 산출물
- signal role matrix
- allowed exposure table

#### 통과 조건
- 각 신호가 `precursor`, `hard evidence`, `context`, `explanation only` 중 어디에 속하는지 결정된다.

### 17.6 Gate 3. precursor 승격 규칙 고정
#### 목적
- 무엇을 precursor로 부를지 알고리즘적으로 잠근다.

#### 반드시 결정할 항목
- precursor 최소 조건
  - 몇 개 축 이상 동시 만족이 필요한가
  - 몇 일 이상 지속되어야 하는가
- precursor 제외 조건
  - hard evidence 동반 시 precursor 표에서 제외할지
  - same-day trigger only case 를 precursor로 볼지
- MLPE 해석 보정
  - `전압 유지 + 전류 저하`를 precursor로 언제 볼지
  - `상대 전압 이탈 징후`를 precursor 문맥에 언제 허용할지

#### 권장 산출물
- truth table
- pseudocode
- representative examples
  - precursor 인정 사례
  - precursor 비인정 사례
  - precursor였다가 hard evidence로 승격된 사례

#### 통과 조건
- 임의 행 하나를 놓고도 “왜 precursor인가/아닌가”를 규칙으로 설명할 수 있다.
- report wording이 아니라 algorithm rule로 설명 가능해야 한다.

### 17.7 Gate 4. hard evidence 경계 고정
#### 목적
- 어떤 신호가 공식적으로 `고장 신호`인지 잠근다.

#### 반드시 결정할 항목
- `final_fault`의 의미
- `critical_fault`의 의미
- `critical_confirmed`의 의미
- `fault_like_day`가 hard evidence에 포함되는지 여부
- `vdrop`가 단독으로 hard evidence인지 여부
- `final + critical_confirmed` 중복 시 1건으로 볼지 2건으로 볼지

#### 산출물
- hard evidence boundary note
- canonical precedence rule
  - 예: `final_fault > critical_confirmed > critical_fault > fault_like`

#### 통과 조건
- `확정 경로`를 한 줄로 정할 수 있다.
- 같은 사건을 두 번 말하지 않도록 precedence가 정해진다.

### 17.8 Gate 5. 출력 정책 고정
#### 목적
- 어떤 표를 누구에게 보여줄지 잠근다.

#### 반드시 결정할 artifact
- `fault_panel_result_current_*`
- `fault_panel_result_raw_only_current_*`
- `fault_panel_result_precursor_report_v1.csv`
- `fault_panel_result_raw_only_fault_signal_report_v1.csv`
- detailed report
- master report

#### 각 artifact 에 대해 고정해야 할 것
- audience
  - 운영자 / 분석가 / 내부 검증
- source
  - live / raw-only / combined
- allowed wording
- 금지 wording
- row universe
- 공식성 수준

#### 예시 정책
- official current:
  - 운영 공식 결과
- precursor report:
  - 운영 추적용 보조표
- raw-only fault signal report:
  - 분석/운영 보조용 candidate evidence 표
- detailed report:
  - 분석가용 전체 로그

#### 통과 조건
- artifact 이름만 보고도 `공식/보조/분석용` 구분이 된다.
- master report에서 이 순서를 그대로 설명할 수 있다.

### 17.9 Gate 6. taxonomy와 action 정책 고정
#### 목적
- 분류와 액션을 너무 빨리 한 줄 taxonomy로 접지 않고, 먼저 축을 조사한 뒤 순서를 정해 연결한다.

#### 1단계: inventory / survey
- 먼저 아래 축을 분리 조사한다.
  - cause axis
  - electrical phenotype axis
  - temporal axis
  - scope / locus axis
  - safety / control axis
  - actionability axis
  - confidence / evidence axis
- 이 단계에서는 `음영/오염/고장` 같은 단일 taxonomy로 바로 잠그지 않는다.

#### 2단계: policy lock
- survey가 끝난 뒤 아래를 잠근다.
- 문제 대분류
- 운영 분류
- 현상 축
- 범위 축
- action lane
- 상세 후보 노출 정책

#### 그 다음 연결할 것
- `모니터링 권고`
- `현장 점검 권고`
- `세척 권고`
- `구조 확인 권고`
- `원격 차단 연계 검토`

#### 통과 조건
- action recommendation 이 taxonomy를 거슬러 임의로 나오지 않는다.
- 동일한 top1 후보에 대해 추천 액션이 지나치게 흔들리지 않는다.
- taxonomy가 원인/현상/범위/행동/안전 축을 무리하게 한 줄로 압축하지 않는다.

### 17.10 Gate 7. 구현 순서 고정
#### 목적
- 이제서야 실제 패치 순서를 잠근다.

#### 상세 문서
- [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)

#### 현재 잠긴 구현 순서 요약
1. Gate 5 checklist 작성
2. runtime pack surface wording / guide / definitions patch
3. stable/handoff boundary note 최소 패치 범위 결정
4. precursor / hard evidence 반례 세트 작성
5. algorithm gating patch 검토
6. taxonomy/action patch
7. build/release/smoke sync

#### 이 단계 전까지 보류해야 하는 패치
- precursor 승격 threshold 조정
- hard evidence precedence 수정
- one-click 리포트 전체 재설계
- final delivery pack wording 최종화

#### 통과 조건
- “지금 왜 이 패치를 하는가”가 바로 위 게이트 문서 또는 decision log로 설명된다.

## 18. 패치 순서 규율
### 18.1 지금 허용되는 패치
- artifact 설명문 정정
- 가이드 문구 추가
- 이름이 역할을 더 정확히 드러내도록 하는 경미한 schema 수정
- definitions/README/ops 문서 보강

### 18.2 지금 보류해야 하는 패치
- precursor 승격 규칙 변경
- hard evidence 판정 규칙 변경
- MLPE 해석 threshold 수정
- cause heuristic 점수 재조정
- evaluation label 재정의

### 18.3 언제 보류 해제되는가
- Gate 1~5가 잠긴 뒤
- 최소한 용어, signal role, precursor rule, hard evidence boundary, output policy가 문서화된 뒤

## 19. 앞으로 모든 패치 전에 체크할 질문
- 이 패치는 용어를 바꾸는가, 규칙을 바꾸는가?
- 규칙을 바꾼다면 그 위 게이트가 이미 잠겼는가?
- artifact 이름과 row universe가 일치하는가?
- precursor 표에 hard evidence 어휘가 새지 않는가?
- official current와 raw-only 보조표를 혼동하게 만들지 않는가?
- MLPE 해석 문구가 스트링형 직관으로 잘못 번역되고 있지 않은가?
- 이 패치 때문에 paper/one-pager/data dictionary 정의를 같이 바꿔야 하는가?

## 20. 브랜치 관리 원칙
### 20.1 왜 브랜치 관리가 필요한가
- 실제 작업 중에는 메인 로드맵만 따라가지 않는다.
- 아래와 같은 이유로 중간 가지가 자연스럽게 생긴다.
  - 특정 site에서만 보이는 예외 패턴
  - MLPE 해석 충돌
  - report wording 과 algorithm meaning 의 불일치
  - raw-only 와 official current 경계 혼선
  - 성능 회귀 또는 false positive 폭증
  - 회의록/현장 피드백에 따른 새 요구
- 따라서 `메인 로드맵`과 별개로 `브랜치 발생 시 행동 규칙`을 문서로 고정해야 한다.

### 20.2 브랜치의 기본 개념
- `메인 라인`:
  - 현재 통과 중인 Decision Gate를 따라가는 기본 작업 흐름
- `브랜치`:
  - 메인 라인 진행 중 발생한 예외/질문/특수 케이스를 별도로 분석하는 가지
- `파킹 로트`:
  - 지금 당장 풀지 않지만 이후 반드시 다시 볼 항목을 적재하는 공간
- `복귀 지점`:
  - 브랜치 분석을 끝낸 뒤 다시 어느 Gate로 돌아갈지 지정하는 지점

### 20.3 브랜치 유형
#### A. 정의 충돌 브랜치
- 같은 용어가 서로 다른 뜻으로 읽힐 때
- 예:
  - `precursor`와 `high-risk observation`이 혼용됨
  - `fault signal`과 `확정`의 경계가 불분명함

#### B. 신호 역할 충돌 브랜치
- 특정 신호가 precursor인지 hard evidence인지 애매할 때
- 예:
  - `fault_like_day`
  - `vdrop`
  - `event_A`

#### C. 사이트 특수 케이스 브랜치
- 특정 site 또는 특정 장비군에서만 반복되는 패턴이 전체 규칙을 흔들 때
- 예:
  - gangui에서만 나타나는 상시 음영성 패턴
  - ktc_ess에서 보이는 MLPE 제어 응답형 패턴

#### D. 성능/평가 회귀 브랜치
- 규칙 또는 schema 수정 이후 precision/recall/lead-time이 흔들릴 때
- 예:
  - precursor row 수는 줄었는데 실제 중요한 사례가 빠짐
  - raw-only strict subset은 안정적이지만 false positive가 급증

#### E. 리포트/표현 충돌 브랜치
- 로직은 괜찮지만 report wording이 의미를 왜곡할 때
- 예:
  - precursor 표에 hard-evidence 어휘가 샘
  - official current와 raw-only 보조표가 같은 레벨로 읽힘

#### F. 범위 확장 브랜치
- 현재 스코프 밖 요구가 다시 들어올 때
- 예:
  - 배터리/ESS 연계 요구 재등장
  - 원격 차단 제어 로직 상세화 요청

### 20.4 브랜치 트리거
- 아래 조건 중 하나라도 만족하면 메인 라인을 잠시 멈추고 브랜치를 만든다.
  - 현재 단계에서 사용하는 핵심 용어의 뜻이 팀 내에서 두 가지 이상으로 읽힘
  - 특정 신호를 precursor와 hard evidence 양쪽에서 동시에 쓰려는 압력이 생김
  - 특정 site 예외를 일반 규칙에 바로 반영하려는 상황이 발생함
  - 새 패치가 `공식 current`와 `보조 candidate 표`의 역할을 흐리게 만듦
  - report를 바꾸려는데 upstream canonical rule이 아직 안 잠겨 있음
  - 회귀 평가 없이 threshold/heuristic 수정 요구가 들어옴

### 20.5 브랜치별 허용 행동
#### 정의 충돌 브랜치
- 허용:
  - 용어 사전 보강
  - artifact 역할 표 수정
  - examples 추가
- 금지:
  - threshold 수정
  - algorithm logic patch

#### 신호 역할 충돌 브랜치
- 허용:
  - signal role matrix 작성
  - representative 사례 추출
  - 현재 노출 위치 점검
- 금지:
  - 신호를 임의로 precursor/hard evidence에 재배치하는 코드 patch

#### 사이트 특수 케이스 브랜치
- 허용:
  - site-specific evidence 정리
  - 공통규칙과 예외규칙 분리 문서화
  - operational profile 후보 정의
- 금지:
  - 단일 site 사례만 보고 전역 규칙 수정

#### 성능/평가 회귀 브랜치
- 허용:
  - regression report 작성
  - metric slice 비교
  - holdout 사례 검토
- 금지:
  - 원인 미분석 상태에서 heuristic 점수 조정

#### 리포트/표현 충돌 브랜치
- 허용:
  - wording patch
  - 설명문/definitions/master report 수정
  - 파일명/컬럼명 완화
- 금지:
  - 코어 신호 정의 변경

#### 범위 확장 브랜치
- 허용:
  - backlog 분리
  - 후속 트랙 명명
  - out-of-scope 선언 강화
- 금지:
  - 현재 스코프 문서에 즉시 편입

### 20.6 파킹 로트 규칙
- 브랜치에서 바로 풀 수 없는 문제는 `파킹 로트`로 이동한다.
- 파킹 로트 항목에는 최소한 아래가 있어야 한다.
  - 제목
  - 발생 날짜
  - 어느 Gate에서 발생했는지
  - 지금 못 푸는 이유
  - 다시 열 조건
  - owner
- 파킹 로트는 “잊기 위한 보관함”이 아니라 “메인 라인을 흔들지 않기 위한 보류함”이다.

### 20.7 복귀 규칙
- 브랜치는 반드시 특정 Gate로 복귀해야 한다.
- 예:
  - 용어 충돌 브랜치 -> Gate 1로 복귀
  - signal role 충돌 브랜치 -> Gate 2로 복귀
  - precursor 기준 충돌 브랜치 -> Gate 3로 복귀
  - hard evidence 의미 충돌 브랜치 -> Gate 4로 복귀
  - artifact 공식성 혼선 브랜치 -> Gate 5로 복귀
  - taxonomy/action 혼선 브랜치 -> Gate 6로 복귀
- 브랜치에서 바로 코드 patch로 점프하지 않는다.

### 20.8 브랜치 종료 조건
- 브랜치는 아래가 충족되면 닫는다.
  - 질문이 문장으로 다시 정의됨
  - 메인 라인에 영향을 주는 결정 포인트가 명시됨
  - 복귀 Gate가 지정됨
  - 허용/금지 패치 범위가 적힘

### 20.9 메인 라인 보호 규칙
- 브랜치 분석이 길어져도 아래는 메인 라인에 그대로 유지한다.
  - 현재 범위
  - 현재 공식 artifact
  - 현재 source of truth
  - 현재 잠긴 용어 정의
- 브랜치 하나 때문에 전체 로드맵을 매번 다시 쓰지 않는다.
- 메인 라인을 바꾸는 조건은 브랜치 결론이 상위 Gate 정의를 실제로 수정할 때뿐이다.

### 20.10 운영 예시
#### 예시 1. precursor 표에 hard-evidence 어휘가 남아 있는 경우
- 유형:
  - 리포트/표현 충돌 브랜치
- 허용 작업:
  - wording patch
  - definitions 강화
- 복귀:
  - Gate 5 출력 정책 확인 후 메인 라인 복귀

#### 예시 2. `vdrop`를 precursor에 포함할지 hard evidence에 포함할지 애매한 경우
- 유형:
  - 신호 역할 충돌 브랜치
- 허용 작업:
  - signal role matrix 정리
  - 대표 사례 비교
- 복귀:
  - Gate 2 신호 분류 체계

#### 예시 3. 특정 site에서만 precursor가 과도하게 많이 나오는 경우
- 유형:
  - 사이트 특수 케이스 브랜치
- 허용 작업:
  - site-specific evidence 분석
  - operational profile 후보 정의
- 복귀:
  - Gate 3 precursor 승격 규칙 또는 Gate 6 taxonomy 정책

#### 예시 4. raw-only fault signal report를 운영자가 공식 current로 읽는 경우
- 유형:
  - 정의 충돌 + 출력 정책 브랜치
- 허용 작업:
  - artifact naming 조정
  - master report 가이드 강화
- 복귀:
  - Gate 1 용어 정의와 Gate 5 출력 정책

## 21. 브랜치 발생 시 표준 처리 절차
1. 현재 이슈가 메인 라인 문제인지 브랜치 문제인지 먼저 분류한다.
2. 브랜치 유형을 A~F 중 하나로 명시한다.
3. 현재 작업 중인 Gate와 복귀 예정 Gate를 적는다.
4. 허용되는 패치와 금지되는 패치를 적는다.
5. 바로 해결 못 하면 파킹 로트에 넣는다.
6. 브랜치 종료 시 결론을 한 문장 규칙으로 환원한다.
7. 그 규칙이 메인 라인 정의를 바꾸면 해당 Gate 문서를 수정한다.

## 22. 로드맵 사용 규칙
### 22.1 메인 라인 먼저
- 항상 메인 라인의 현재 Gate를 먼저 말한다.
- 브랜치 작업은 메인 라인을 대체하지 않는다.

### 22.2 문서 먼저
- 브랜치에서 결론이 나면 코드보다 먼저 문서 Gate를 수정한다.

### 22.3 패치는 최소 범위
- 브랜치 성격이 표현 문제면 wording만 바꾼다.
- 브랜치 성격이 정의 충돌이면 definition만 바꾼다.
- 브랜치 성격이 규칙 충돌이면 pseudocode와 examples를 먼저 만든다.

### 22.4 브랜치 누적 관리
- 브랜치가 3개 이상 동시에 열리면 메인 라인 진행을 잠시 멈춘다.
- 열린 브랜치가 많다는 것은 상위 Gate가 아직 덜 잠겼다는 뜻이다.

## 23. 현 시점 권고
- 지금까지의 report split / wording patch는 `허용 가능한 표현층 정리`로 본다.
- 하지만 여기서 더 들어가 `알고리즘 규칙`까지 바꾸는 것은 아직 이르다.
- Gate 6 survey로 인해 Gate 3~5 선행 가정에도 허점이 있을 수 있으므로, 추가 알고리즘 패치 전 교차 게이트 감사를 먼저 본다.
- 다음 실질 작업은 아래 순서가 맞다.
  1. Gate 1 용어 사전 확정
  2. Gate 2 signal role matrix 확정
  3. Gate 3 precursor 승격 규칙 초안 확정
  4. Gate 4 hard evidence boundary 확정
  5. Gate 6 survey 결과를 기준으로 교차 게이트 감사 수행
  6. 그 다음에야 알고리즘 패치 착수

## 24. 문서 상태
- 본 문서는 이제 `상위 설계 + 구현 백로그 + 의사결정 로드맵`을 한 문서에 함께 담는다.
- 이후 필요하면 아래 두 문서로 분화할 수 있다.
  - `OPS_CONALOG_MLPE_RUNTIME_DECISION_ROADMAP_V1.md`
  - `OPS_CONALOG_MLPE_RUNTIME_IMPLEMENTATION_BACKLOG_V1.md`
- 하지만 현재 단계에서는 한 문서 안에서 맥락이 끊기지 않는 것이 더 중요하다.

### 24.1 기존 P0 완료 정의
- precursor report row 가 hard evidence 동반 사례를 포함하지 않는다.
- fault signal report 가 별도 csv 로 생성된다.
- master report 가 두 표의 의미 차이를 명시한다.
- smoke test 가 새 artifact 와 schema 를 검증한다.
- source 문서와 smoke test 기대치가 일치한다.

## 25. 검증/수용 기준
- precursor report 와 fault signal report 가 서로 다른 목적의 row 를 혼합하지 않아야 한다.
- `critical/final` 같은 internal shorthand 없이도 운영자가 의미를 읽을 수 있어야 한다.
- MLPE 환경 해석 문구가 스트링형 직관과 충돌하지 않아야 한다.
- 원인 후보는 direct root-cause 확정이 아니라 ranked candidate 임이 명확해야 한다.
- report 에 최소한 다음 질문의 답이 보여야 한다.
  - 지금은 precursor 인가, hard fault evidence 인가
  - 왜 그렇게 봤는가
  - 무엇을 먼저 확인해야 하는가
  - 해결 가능한 문제인가

## 26. 문서 운용 원칙
- 본 문서는 원본 repo 기준 상위 설계 문서다.
- release package 문서는 본 문서의 하위 전달 문서로 본다.
- 이후 구현 변경은 가능하면 본 문서의 범주와 용어를 먼저 맞춘 뒤 code/report 에 반영한다.

## 27. 이해관계자 맵
### 27.1 왜 필요한가
- 같은 artifact라도 누가 읽느냐에 따라 기대하는 답이 다르다.
- 따라서 wording, granularity, action recommendation 은 이해관계자별로 분리 설계해야 한다.

### 27.2 주요 이해관계자
#### 운영자
- 가장 먼저 궁금한 것:
  - 지금 이 패널을 당장 신경 써야 하는가
  - 공식 current 기준으로 문제가 있는가
  - 모니터링만 하면 되는가, 점검이 필요한가
- 선호 artifact:
  - `fault_panel_result_current_*`
  - `fault_panel_result_precursor_report_v1.csv`
- 금지:
  - internal shorthand
  - 후보 우주와 공식 결과의 혼용

#### 분석가
- 가장 먼저 궁금한 것:
  - 왜 그렇게 판정됐는가
  - 어떤 축의 신호가 누적됐는가
  - raw-only 와 live 결과가 왜 다른가
- 선호 artifact:
  - detailed report
  - raw-only candidate outputs
  - raw-only fault signal report

#### 현장 점검자
- 가장 먼저 궁금한 것:
  - 현장에 가면 뭘 먼저 봐야 하는가
  - 접속/오염/음영/MLPE 중 어디부터 의심해야 하는가
- 선호 artifact:
  - `현장 점검 권고`
  - `모니터링 권고`
  - action-facing report

#### 발표/논문/방어 관점
- 가장 먼저 궁금한 것:
  - precursor 정의는 무엇인가
  - hard evidence 경계는 무엇인가
  - 왜 이 평가셋과 metric을 썼는가
- 선호 artifact:
  - decision log
  - signal role matrix
  - evaluation note

### 27.3 이해관계자별 규칙
- 운영자용 표에는 공식성 수준을 반드시 명시한다.
- 분석가용 표에는 internal detail을 유지하되 source layer를 숨기지 않는다.
- 현장 점검자용 표에는 `첫 행동`이 먼저 보여야 한다.
- 발표/논문용 문서에는 threshold보다 정의와 선택 이유가 먼저 보여야 한다.

## 28. 결정 로그(Decision Log)
### 28.1 목적
- 같은 논쟁을 반복하지 않도록, 중요한 설계 결정을 기록한다.

### 28.2 반드시 남겨야 할 결정
- precursor 정의
- hard evidence 경계
- `fault_like_day`의 역할
- `vdrop` 노출 정책
- raw-only vs official current 역할
- artifact naming 정책
- taxonomy/action 연결 정책

### 28.3 decision log 항목 형식
- `decision_id`
- `date`
- `status`
  - proposed / accepted / superseded / rejected
- `topic`
- `decision`
- `reason`
- `alternatives_considered`
- `impact`
  - code / report / evaluation / docs
- `rollback_trigger`
- `related_gate`

### 28.4 운영 규칙
- Gate를 통과하는 순간 핵심 결정을 decision log에 남긴다.
- superseded 된 결정은 지우지 않고 상태만 바꾼다.
- 구현 patch가 decision log 없이 먼저 들어가면 문서 부채로 간주한다.

## 29. 반례 세트와 챌린지 세트
### 29.1 목적
- 잘 되는 사례만으로는 precursor/hard evidence 경계를 방어할 수 없다.
- 애매한 사례를 따로 모아 decision gate의 반례집으로 운영한다.

### 29.2 필요한 세트
#### precursor 반례 세트
- precursor처럼 보이지만 precursor로 올리면 안 되는 사례
- same-day trigger only 사례
- MLPE 제어응답으로 보이지만 hard evidence는 아닌 사례

#### hard evidence 반례 세트
- 강해 보이지만 공식 hard evidence로는 올리면 안 되는 사례
- `vdrop`가 있지만 common-cause 가능성이 큰 사례
- `fault_like_day`가 반복되지만 최종 확정으로 가면 안 되는 사례

#### taxonomy 반례 세트
- 음영 vs 오염 vs 접속불량이 헷갈리는 사례
- MLPE 응답 이상 vs 센서 이상이 헷갈리는 사례

#### site-specific 챌린지 세트
- conalog 특이 사례
- gangui 특이 사례
- ktc_ess 특이 사례

### 29.3 세트 운영 규칙
- 각 Gate는 대표 정례 사례뿐 아니라 반례를 최소 3개 이상 가져야 한다.
- 규칙을 바꿀 때는 반례 세트에서 regression check를 한다.
- 발표/논문 방어시 반례 세트를 근거로 “왜 이 규칙을 과도하게 일반화하지 않았는가”를 설명한다.

### 29.4 현재 문서
- 현재 V1 seed set:
  - [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md)

## 30. 오판 비용 모델
### 30.1 목적
- false positive와 false negative를 동일하게 취급하지 않는다.

### 30.2 비용 축
- `모니터링 false positive`
  - 운영 피로 증가
- `현장 점검 false positive`
  - 출동 비용
- `세척 권고 false positive`
  - 작업 비용
- `원격 차단 false positive`
  - 운영 손실 / 불필요한 제어 개입
- `precursor false negative`
  - 조기 대응 기회 상실
- `hard evidence false negative`
  - 실제 고장 신호 누락

### 30.3 규칙
- precursor는 false positive 허용도가 hard evidence보다 높다.
- 원격 차단 관련 축은 false positive 허용도가 가장 낮다.
- action recommendation은 action cost를 같이 고려해야 한다.

### 30.4 산출물
- cost matrix
- artifact별 허용 위험도
- action별 오판 비용 메모

## 31. 판단 보류 및 미확정 정책
### 31.1 목적
- 애매한 사례를 억지로 precursor나 fault로 밀지 않는다.

### 31.2 필요한 상태
- `비고장`
- `관찰`
- `고위험 관찰`
- `precursor candidate`
- `고장 신호 동반`
- `확정`
- `원인 미확정`
- `판단 보류`

### 31.3 보류가 필요한 상황
- precursor 축과 hard evidence 축이 동시에 애매하게 걸리는 경우
- site-level common cause 가능성이 큰 경우
- data quality / communication 문제로 신호 신뢰도가 낮은 경우
- top1 후보 score 경쟁이 너무 심한 경우

### 31.4 규칙
- `판단 보류`는 실패가 아니라 의도된 상태다.
- 보류된 사례는 파킹 로트가 아니라 별도 review queue로 관리한다.
- `원인 미확정`과 `패널 상태 미확정`을 같은 뜻으로 쓰지 않는다.

## 32. 버전/호환성 정책
### 32.1 목적
- 파일명, 컬럼명, schema가 자주 흔들려 downstream이 깨지는 상황을 막는다.

### 32.2 관리 대상
- root result csv 이름
- preview schema
- detailed report sheet명
- master report key names
- artifact metadata json

### 32.3 규칙
- artifact 이름을 바꿀 땐 source/build/smoke를 같은 턴에 같이 바꾼다.
- deprecate할 이름은 최소 한 라운드 이상 migration note를 남긴다.
- operator-facing 컬럼명 변경은 decision log와 definitions 시트에 함께 반영한다.

### 32.4 권장 산출물
- schema version note
- migration checklist
- deprecated artifact map

## 33. 추적 가능성(Traceability)
### 33.1 목적
- 한 row가 왜 올라왔는지 나중에도 역추적 가능해야 한다.

### 33.2 추적해야 할 것
- 어떤 신호가 있었는가
- 어떤 Gate 정의에 따라 precursor 또는 hard evidence로 분류됐는가
- 어떤 대표 날짜가 선택됐는가
- 어떤 event summary가 붙었는가
- 어떤 top1 후보가 선택됐는가

### 33.3 규칙
- operator-facing 표는 단순화하더라도, detailed report에는 lineage가 남아야 한다.
- row 하나를 잡고 upstream signal까지 되짚을 수 있어야 한다.
- “왜 이 패널이 여기에 있지?”라는 질문에 코드가 아니라 artifact로 답할 수 있어야 한다.

## 34. Slice 기반 검증 정책
### 34.1 목적
- 평균 성능만 보고 의사결정하지 않는다.

### 34.2 필수 slice
- site별
- 계절별
- 상시 음영 구역 vs 비음영 구역
- 작업일 포함 vs 비포함
- MLPE 응답형 의심 사례 vs 일반 사례
- precursor 사례 vs abrupt 사례

### 34.3 규칙
- 메트릭이 좋아도 특정 slice가 무너지면 Gate를 통과시키지 않는다.
- precursor rule 수정 시 lead-time slice를 같이 본다.
- hard evidence rule 수정 시 false positive cost가 높은 slice를 먼저 본다.

## 35. 현장 피드백 흡수 규칙
### 35.1 목적
- 현장 피드백을 단순 메모로 흘리지 않고 구조화한다.

### 35.2 피드백 수준
- 관찰 메모
- 약한 라벨 후보
- 강한 truth 후보
- 정책 변경 요청

### 35.3 규칙
- 현장 코멘트가 바로 알고리즘 truth가 되지 않는다.
- 반복되는 코멘트는 decision log 또는 taxonomy backlog로 승격한다.
- 현장 피드백이 특정 site 특수성인지 전역 규칙 후보인지 분리한다.

## 36. 롤백 규칙
### 36.1 목적
- 잘못된 패치가 들어갔을 때 어디까지 되돌릴지 미리 정한다.

### 36.2 롤백 수준
- wording rollback
- schema rollback
- report split rollback
- rule rollback
- heuristic rollback

### 36.3 규칙
- wording rollback은 즉시 가능
- schema rollback은 build/smoke/source를 함께 맞춰야 함
- rule rollback은 decision log와 evaluation note를 같이 업데이트해야 함
- heuristic rollback은 regression evidence 없이 수행하지 않음

### 36.4 롤백 트리거 예시
- 운영자가 official current와 raw-only 보조표를 반복적으로 혼동
- precursor rule 변경 후 반례 세트에서 다수 실패
- hard evidence 경계 변경 후 false positive cost 급증
- taxonomy/action 변경 후 현장 권고 일관성 붕괴

## 37. 현 시점에서 특히 우선 추가해야 하는 것
- `결정 로그`
- `반례 세트`
- `오판 비용 모델`
- `판단 보류 정책`
- `traceability 메모`

## 38. 다음 권장 작업
1. `existing signal -> multi-axis score map` refinement
2. build/release/smoke sync 범위를 확정하기
3. `MLPE ambiguous`의 장치 응답 이상형 top1 / 회복 재발 seed 추가
4. `common_cause_risk`의 운영 이벤트 / `group_off_event` 연계 seed 추가
5. `official current`와 direct overlap하는 common-cause seed 추가

## 39. 바로 사용할 템플릿
- 교차 게이트 설계 허점 감사:
  - [OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md)
- Gate 1 용어 사전:
  - [OPS_CONALOG_RUNTIME_GATE1_GLOSSARY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE1_GLOSSARY_V1.md)
- Gate 2 signal role matrix:
  - [OPS_CONALOG_RUNTIME_GATE2_SIGNAL_ROLE_MATRIX_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2_SIGNAL_ROLE_MATRIX_V1.md)
- Gate 2A observability / evidence availability matrix:
  - [OPS_CONALOG_RUNTIME_GATE2A_OBSERVABILITY_EVIDENCE_MATRIX_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2A_OBSERVABILITY_EVIDENCE_MATRIX_V1.md)
- Gate 2B canonical multi-axis result model:
  - [OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md)
- Gate 2C existing signal score map:
  - [OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md)
- Gate 3 precursor 승격 규칙 초안:
  - [OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md)
- Gate 4 hard evidence 경계 초안:
  - [OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md)
- Gate 4A event semantics / operator semantics contract:
  - [OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md)
- Gate 5 출력 정책:
  - [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- Gate 5 artifact/schema patch checklist:
  - [OPS_CONALOG_RUNTIME_GATE5_ARTIFACT_SCHEMA_PATCH_CHECKLIST_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_ARTIFACT_SCHEMA_PATCH_CHECKLIST_V1.md)
- Gate 6 taxonomy/action survey:
  - [OPS_CONALOG_RUNTIME_GATE6_TAXONOMY_ACTION_SURVEY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE6_TAXONOMY_ACTION_SURVEY_V1.md)
- Gate 6B taxonomy/action policy lock:
  - [OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1.md)
- Gate 7 구현 순서 고정:
  - [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)
- 결정 로그 템플릿:
  - [OPS_CONALOG_RUNTIME_DECISION_LOG_TEMPLATE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_TEMPLATE_V1.md)
- decision log 1호:
  - [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md)
- decision log 2호:
  - [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md)
- decision log 3호:
  - [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_003_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_003_V1.md)
- decision log 4호:
  - [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_004_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_004_V1.md)
- decision log 5호:
  - [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_005_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_005_V1.md)
- decision log 6호:
  - [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_006_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_006_V1.md)
- decision log 7호:
  - [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_007_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_007_V1.md)
- decision log 8호:
  - [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_008_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_008_V1.md)
- stable-runtime boundary/mapping note:
  - [OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md)
- 반례 세트 V1:
  - [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md)
- existing signal -> multi-axis score map:
  - [OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md)
- 브랜치/파킹 로트 템플릿:
  - [OPS_CONALOG_RUNTIME_BRANCH_PARKING_LOT_TEMPLATE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_PARKING_LOT_TEMPLATE_V1.md)
