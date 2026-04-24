<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1

## 1. 목적
- 본 문서는 `runtime redesign`에서 precursor / hard evidence / artifact exposure 규칙을 바꾸기 전에 반드시 확인해야 하는 반례 세트 V1이다.
- 목적은 아래 다섯 가지다.
  - 잘 되는 사례가 아니라 `헷갈리는 사례`를 기준점으로 고정한다.
  - Gate 3 / Gate 4 / Gate 5 / Gate 6 논의를 실제 패널 사례와 연결한다.
  - `official current`, `precursor`, `raw-only fault signal`이 서로 어떤 반례를 가지는지 문서로 남긴다.
  - 알고리즘 규칙 변경 전에 regression input을 미리 만든다.
  - 발표/논문/운영 방어에서 “왜 과도하게 일반화하지 않았는가”를 설명할 근거를 만든다.

## 2. 이 문서의 역할
- 상위 로드맵:
  - [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- 구현 순서:
  - [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)
- precursor 규칙:
  - [OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md)
- hard evidence 경계:
  - [OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md)
- output policy:
  - [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- taxonomy/action survey:
  - [OPS_CONALOG_RUNTIME_GATE6_TAXONOMY_ACTION_SURVEY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE6_TAXONOMY_ACTION_SURVEY_V1.md)

## 3. 적용 범위
- 대상 artifact:
  - `fault_panel_result_current_v1.csv`
  - `fault_panel_result_precursor_report_v1.csv`
  - `fault_panel_result_raw_only_fault_signal_report_v1.csv`
- 대상 목적:
  - precursor 승격 규칙 검토
  - hard evidence 경계 검토
  - operator-facing vs analyst-facing artifact 노출 검토
- 비대상:
  - stable/handoff six-field contract 재정의
  - safety/control lane 직접 추천 규칙 최종화

## 4. 케이스 기록 스키마
- `case_id`
- `site`
- `panel_id`
- `slice_type`
  - `official_only`
  - `precursor_only`
  - `raw_only_only`
  - `mlpe_ambiguous`
  - `common_cause_risk`
- `present_in_current`
- `present_in_precursor`
- `present_in_raw_only_fault_signal`
- `expected_reading`
- `why_counterexample`
- `prohibited_overgeneralization`
- `follow_up_gate_or_decision`

## 5. 운영 규칙
- algorithm gating patch 전에 아래 다섯 버킷을 모두 확인한다.
  - `official_only`
  - `precursor_only`
  - `raw_only_only`
  - `mlpe_ambiguous`
  - `common_cause_risk`
- 규칙 변경 전후에 적어도 각 버킷 대표 사례 3개 이상을 regression input으로 재확인한다.
- 비어 있는 버킷은 “없다”가 아니라 “아직 수집 전”으로 취급한다.
- 반례 세트에서 흔들리는 규칙은 decision log 없이 바로 코드 패치하지 않는다.

## 6. V1 수집 기준
- 기준 실행:
  - `conalog_dl005_check`
- 기준 artifact:
  - `fault_panel_result_current_v1.csv`
  - `fault_panel_result_precursor_report_v1.csv`
  - `fault_panel_result_raw_only_fault_signal_report_v1.csv`
- 선택 원칙:
  - site를 가능하면 `conalog / gangui / ktc_ess`로 분산한다.
  - 같은 base/group의 반복 사례는 대표 사례와 보조 사례를 나눈다.
  - operator-facing과 analyst/support artifact가 갈라지는 사례를 우선 채택한다.

## 7. V1 Seed Set
### 7.1 official_only
#### 목적
- official current에 바로 올라오지만 precursor-only 나 raw-only-only로 읽으면 안 되는 사례를 모은다.

| case_id | site | panel_id | expected_reading | why_counterexample | prohibited_overgeneralization | follow_up_gate_or_decision |
| --- | --- | --- | --- | --- | --- | --- |
| OFF-001 | conalog | `7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0` | official current의 대표 고장 사례로 읽는다 | stable/current에서는 고장으로 명확하지만 precursor 논의 입력으로 재해석하면 안 된다 | `전조형 고장`이라는 이유로 precursor 세트에 다시 포함하지 말 것 | Gate 5, DL-001 |
| OFF-002 | conalog | `c42997a6-5881-47e7-9035-7de8a2673b54.1.1` | official current의 급격 종료형 current 사례 | official current 확정 사례를 raw-only-only 근거처럼 재설명하면 안 된다 | current artifact를 analyst-support artifact로 낮추지 말 것 | Gate 5, Gate 4A |
| OFF-003 | gangui | `bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7` | 급작 고장 current 사례 | same-day/abrupt 사례를 precursor 부족의 실패 예시로 섞으면 안 된다 | abrupt current 사례를 precursor recall 실패로 일반화하지 말 것 | Gate 3, Gate 4A |
| OFF-004 | gangui | `bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16` | current artifact의 운영 고장 사례 | site 특수 current 사례가 raw-only artifact 필요성의 근거로 오용될 수 있다 | current artifact 존재를 이유로 raw-only direct open을 확대하지 말 것 | DL-004, DL-005 |
| OFF-005 | ktc_ess | `10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12` | official current 현재 고장 사례 | ESS site 사례도 stable current lane으로 먼저 읽혀야 한다 | site 특수성을 이유로 stable/runtime contract 경계를 흐리지 말 것 | DL-002, Gate 5 |
| OFF-006 | ktc_ess | `70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4` | official current 현재 고장 사례 | current artifact에 있는 사례를 raw-only fault signal report 대표 사례로 대신 쓰면 안 된다 | official current와 analyst/support artifact의 대표 사례를 혼용하지 말 것 | DL-001, Gate 5 |

### 7.2 precursor_only
#### 목적
- precursor report에는 남지만 current나 raw-only fault signal로 올리면 과한 사례를 모은다.

| case_id | site | panel_id | expected_reading | why_counterexample | prohibited_overgeneralization | follow_up_gate_or_decision |
| --- | --- | --- | --- | --- | --- | --- |
| PRE-001 | gangui | `4fd0c566-e25e-4d51-96ca-57cc46940593.0.12` | `고위험 관찰`, `열화형` 후보로 읽는다 | EWS/pre_ews/규칙징후가 강해도 official current나 raw-only hard evidence로 바로 승격하면 안 된다 | `상대 전압 이탈 징후`를 hard evidence로 곧장 승격하지 말 것 | Gate 3, Gate 4 |
| PRE-002 | gangui | `4fd0c566-e25e-4d51-96ca-57cc46940593.0.13` | precursor-only 고위험 관찰 | event_A 반복과 dtw 차이가 있어도 current 확정으로 직결되지 않는다 | 이상 이벤트 반복을 곧장 공식 current 승격으로 일반화하지 말 것 | Gate 3, Gate 5 |
| PRE-003 | gangui | `4fd0c566-e25e-4d51-96ca-57cc46940593.4.26` | precursor-only, 다이오드·국소 회로 이상형 후보 | `기존 알고리즘 source=vdrop`가 있어도 raw-only fault signal로 바로 올리면 과하다 | vdrop 흔적을 hard evidence와 동치로 두지 말 것 | Gate 3, Gate 4 |
| PRE-004 | gangui | `bf1a912f-6cf0-4f12-8e97-9d9d86576511.1.0` | precursor-only 관찰/고위험 관찰 | 군집 흔들림이 섞이면 panel-local precursor로 과하게 읽을 수 있다 | group 흔들림을 panel-local precursor로 과대 해석하지 말 것 | Gate 2A, Gate 6A |
| PRE-005 | ktc_ess | `10305b40-b67e-40d1-9cd1-271b6642a3d9.0.17` | `관찰`, `원인미확정` 상태 유지 | 아직 증거가 약한 관찰 상태를 taxonomy 확정으로 밀면 안 된다 | `원인미확정`을 억지 top1 후보로 대체하지 말 것 | Gate 2B, Gate 6B |
| PRE-006 | ktc_ess | `10305b40-b67e-40d1-9cd1-271b6642a3d9.1.12` | precursor-only 관찰 | precursor 누적이 있어도 current/headline 확정 아님 | precursor 누적 일수를 headline 확정 근거로 쓰지 말 것 | Gate 3, Gate 5 |

### 7.3 raw_only_only
#### 목적
- raw-only fault signal report에는 강하게 올라오지만 official current와는 별도 analyst/support artifact로 읽혀야 하는 사례를 모은다.

| case_id | site | panel_id | expected_reading | why_counterexample | prohibited_overgeneralization | follow_up_gate_or_decision |
| --- | --- | --- | --- | --- | --- | --- |
| RAW-001 | conalog | `21ca22d1-a6fb-40cd-805c-cd3dcfcbb4ff.0.0` | raw-only hard evidence 사례, analyst/support 확인용 | `최종 고장 신호 경로`가 강해도 official current 대체물이 아니다 | raw-only fault signal report를 operator headline으로 직접 승격하지 말 것 | DL-001, DL-004 |
| RAW-002 | conalog | `21ca22d1-a6fb-40cd-805c-cd3dcfcbb4ff.0.1` | raw-only hard evidence 사례 | 동일 base 반복 사례는 support evidence 강화용이지 current row universe 확대 근거가 아니다 | 동일 묶음 반복을 official current 확장 근거로 쓰지 말 것 | Gate 5, DL-005 |
| RAW-003 | conalog | `21ca22d1-a6fb-40cd-805c-cd3dcfcbb4ff.0.2` | raw-only hard evidence 사례 | MLPE-like 패턴이 있어도 current artifact와 같은 공식성은 없다 | MLPE 패턴이라는 이유로 raw-only artifact의 공식성을 높이지 말 것 | DL-002, DL-004 |
| RAW-004 | conalog | `21ca22d1-a6fb-40cd-805c-cd3dcfcbb4ff.0.3` | raw-only hard evidence 사례 | `전조 후 급격 종료` 사건 요약은 analyst 설명축이다 | event semantics를 operator-facing headline으로 직접 복사하지 말 것 | Gate 4A, Gate 5 |
| RAW-005 | conalog | `21ca22d1-a6fb-40cd-805c-cd3dcfcbb4ff.0.4` | raw-only hard evidence 사례 | `장치 측정 이상형` 후보는 현장 점검 가이드이지 official cause 확정은 아니다 | 후보 cause를 stable current cause와 혼동하지 말 것 | Gate 6B, DL-002 |
| RAW-006 | conalog | `21ca22d1-a6fb-40cd-805c-cd3dcfcbb4ff.1.0` | raw-only hard evidence 사례 | analyst/support artifact의 반복 사례는 master report 직접 노출 범위를 흔든다 | master report에서 raw-only 링크를 자동 과다 노출하지 말 것 | DL-006 예정 |

### 7.4 mlpe_ambiguous
#### 목적
- MLPE 특성 때문에 `전류 단절`, `장치 측정 이상`, `제어 응답`, `실제 패널 이상`이 섞여 보이는 사례를 모은다.

승인 기준:
- `센서·피드백형` 또는 장치/제어형 후보가 top1이지만
- `접속·부분개방형`, `다이오드·서브스트링형`, `열화형` 같은 panel-local 후보가 같이 상위권에 존재하고
- raw-only hard evidence는 강하지만 official current headline으로는 직접 승격되지 않는 사례를 우선 승인한다.

| case_id | site | panel_id | expected_reading | why_counterexample | prohibited_overgeneralization | follow_up_gate_or_decision |
| --- | --- | --- | --- | --- | --- | --- |
| MLP-001 | conalog | `21ca22d1-a6fb-40cd-805c-cd3dcfcbb4ff.0.0` | MLPE ambiguous, 센서·피드백 우세 but panel-local 경합 | raw-only 기준 top1은 `센서·피드백형`이고 `원인후보_실증우선확인_ko`는 `장치 측정 이상형`이며, top2 `접속·부분개방형`, top3 `다이오드·서브스트링형`이 함께 보여 장치/패널 해석이 섞인다 | 센서·피드백 top1 하나만 보고 패널 자체 고장이나 MLPE 응답 이상으로 단정하지 말 것 | Gate 2C, Gate 6B |
| MLP-002 | conalog | `21ca22d1-a6fb-40cd-805c-cd3dcfcbb4ff.0.3` | MLPE ambiguous, 센서·피드백 우세 but 열화/개방 경합 | top1 `센서·피드백형`, top2 `접속·부분개방형`, top3 `열화형` 조합이고 실증 우선 확인값은 `장치 측정 이상형`이라 제어/장치/패널 노화 해석이 동시에 열린다 | 전압 유지 + 전류 급락 패턴을 장치 문제 하나로만 환원하지 말 것 | Gate 2C, DL-008 |
| MLP-003 | conalog | `7f7dd654-2760-4eb2-a197-3ebb72b85cda.1.0` | MLPE ambiguous, 급격 종료형 device-panel 경합 사례 | top1 `센서·피드백형`, top2 `접속·부분개방형`, top3 `다이오드·서브스트링형`이고 사건은 `급격 종료`로 닫혀 장치/패널 경계가 더 모호하다 | abrupt raw-only hard evidence를 곧바로 operator-facing 장치 확정으로 노출하지 말 것 | Gate 4A, Gate 5 |
| MLP-004 | gangui | `bf1a912f-6cf0-4f12-8e97-9d9d86576511.1.2` | MLPE ambiguous, 급작 발생형 센서·피드백 우세 but panel-local 경합 | top1 `센서·피드백형` score 6에 top2 `접속·부분개방형`, top3 `다이오드·서브스트링형`이 같이 붙고 사건은 `급작 고장 / 급작 발생`으로 닫혀 장치 응답과 패널 국소 이상을 쉽게 혼동한다 | abrupt device-like top1을 곧바로 장치 확정이나 패널 확정으로 단정하지 말 것 | Gate 2C, Gate 4A |
| MLP-005 | conalog | `21ca22d1-a6fb-40cd-805c-cd3dcfcbb4ff.0.1` | MLPE ambiguous, 전조형 고장 뒤 급격 종료형 센서·피드백 경합 | top1 `센서·피드백형`, top2 `접속·부분개방형`, top3 `다이오드·서브스트링형`이고 `전조형 고장 / 급격 종료`로 닫혀 precursor 축과 panel-local 축이 함께 흔들린다 | precursor 흔적이 있다고 장치/패널 중 한쪽으로만 단정하지 말 것 | Gate 2C, Gate 3 |
| MLP-006 | gangui | `4fd0c566-e25e-4d51-96ca-57cc46940593.4.15` | MLPE ambiguous, 진행성 악화형 센서·피드백 vs 열화 경합 | top1 `센서·피드백형`, top2 `접속·부분개방형`, top3 `열화형`이고 `전조형 고장 / 진행성 악화`로 닫혀 장치 응답형과 실제 열화형 해석이 동시에 열린다 | 진행성 악화 패턴을 곧바로 열화형이나 장치 측정형 한쪽으로만 고정하지 말 것 | Gate 2C, Gate 6B |
| MLP-007 | conalog | `c42997a6-5881-47e7-9035-7de8a2673b54.1.1` | MLPE ambiguous, `장치 응답 이상형` 외부참조와 panel-local/control near-miss가 함께 남는 curated seed | live-chain에서 `장치 응답 이상형`이 외부참조로 붙고 top1 `센서·피드백형`, top2 `접속·부분개방형`, top3 `제어응답형`, 신뢰도 `medium`이라 장치/제어/패널 해석이 동시에 열린다 | 외부참조패턴과 top3 `제어응답형`이 있다고 exact `제어응답형 top1`을 확보한 것으로 읽지 말 것 | Gate 2C, DL-013, DL-014 |
| MLP-008 | gangui | `bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7` | MLPE ambiguous, 급작 current 사례에서도 `장치 응답 이상형` 외부참조와 panel-local top1이 충돌하는 curated seed | `장치 응답 이상형` 외부참조가 붙지만 top1은 `다이오드·서브스트링형`, top2는 `센서·피드백형`이라 abrupt current 사례 안에서도 장치/패널 경합이 실제로 존재한다 | 급작 current + 외부참조를 이유로 장치형 확정이나 exact control-family closure로 과대 해석하지 말 것 | Gate 2C, Gate 4A, DL-014 |
| MLP-009 | ktc_ess | `70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4` | MLPE ambiguous, 진행성 악화 current에서도 device-response hint와 열화형 top1이 충돌하는 curated seed | `장치 응답 이상형` 외부참조가 붙지만 top1은 `열화형`, top2는 `센서·피드백형`, top3는 `다이오드·서브스트링형`이라 panel-local 열화와 장치 응답형 해석이 동시에 열린다 | 외부 device-response hint만으로 열화형/장치형 중 하나를 성급히 확정하거나 exact `제어응답형 top1` 발견으로 읽지 말 것 | Gate 2C, DL-013, DL-014 |

필수 추가 수집 과제:
- `센서·피드백형` 외에 `장치 응답 이상형`이 실제 top1으로 뜨는 사례
- MLPE 현장 점검 결과가 남은 사례
- 동일 panel의 회복/재발까지 확인되는 사례

### 7.5 common_cause_risk
#### 목적
- panel-local precursor 또는 hard evidence처럼 보이지만 사실은 group/base/common-cause일 가능성이 큰 사례를 모은다.

승인 기준:
- precursor 근거는 강하지만
- `동일 base 군집 흔들림(N panels)`이 판정 근거에 직접 나타나고
- panel-local보다 group/base/common-cause를 먼저 검토해야 하는 사례를 우선 승인한다.

| case_id | site | panel_id | expected_reading | why_counterexample | prohibited_overgeneralization | follow_up_gate_or_decision |
| --- | --- | --- | --- | --- | --- | --- |
| CCR-001 | gangui | `4fd0c566-e25e-4d51-96ca-57cc46940593.0.12` | common-cause risk, panel-local 고위험 관찰 보류 사례 | precursor 근거가 있지만 판정 근거에 `동일 base 군집 흔들림(19 panels)`이 직접 들어가 panel-local 해석을 눌러야 한다 | 열화형 후보가 보인다고 바로 singleton precursor나 개별 패널 조치로 연결하지 말 것 | Gate 2A, Gate 2C |
| CCR-002 | gangui | `bf1a912f-6cf0-4f12-8e97-9d9d86576511.1.0` | common-cause risk, 대규모 군집 흔들림 우선 사례 | `동일 base 군집 흔들림(26 panels)`이 함께 관측돼 다축 전조가 강해도 panel-local precursor로 과대 해석하면 위험하다 | 다수 군집 흔들림을 개별 패널 조치 우선순위로 번역하지 말 것 | Gate 2A, Gate 6A |
| CCR-003 | ktc_ess | `ed5e3367-fbd4-4c8c-be33-c5d1c5e191b7.0.13` | common-cause risk, site 특수 group 흔들림 사례 | EWS/AE/DTW 누적이 매우 크지만 `동일 base 군집 흔들림(14 panels)`이 함께 있어 원인미확정 또는 common-cause review가 더 적합하다 | 누적 전조 일수만 보고 panel-local 열화로 단정하지 말 것 | Gate 2C, Gate 6B |
| CCR-004 | gangui | `4fd0c566-e25e-4d51-96ca-57cc46940593.4.26` | common-cause risk, panel-local 다이오드형 후보도 군집 흔들림에 눌리는 사례 | `가장 가까운 후보는 다이오드·국소 회로 이상형`이지만 `동일 base 군집 흔들림(19 panels)`이 동시에 들어가 panel-local 다이오드 해석보다 group/base 검토가 먼저여야 한다 | panel-local 전기 후보가 강하다는 이유만으로 singleton hard-evidence 보강 규칙을 바로 강화하지 말 것 | Gate 2C, Gate 4 |
| CCR-005 | ktc_ess | `10305b40-b67e-40d1-9cd1-271b6642a3d9.0.17` | common-cause risk, 관찰 단계 원인미확정 보류 사례 | `운영 판정=관찰` 수준인데도 `동일 base 군집 흔들림(9 panels)`과 AE/DTW 누적이 함께 보여, 초기에 panel-local precursor로 올리기보다 common-cause screening이 먼저다 | 초기 전조 누적만 보고 개별 패널 선조치 대상으로 승격하지 말 것 | Gate 2A, Gate 3 |
| CCR-006 | ktc_ess | `10305b40-b67e-40d1-9cd1-271b6642a3d9.1.16` | common-cause risk, 원인미확정 고위험 관찰 사례 | EWS/AE/DTW가 매우 크고 `동일 base 군집 흔들림(9 panels)`이 직접 들어가 있어, 원인미확정 보류가 panel-local 가설보다 더 적절하다 | 원인미확정 + 다수 군집 흔들림 상태를 억지로 열화형이나 개별 고장형으로 접지 말 것 | Gate 2C, Gate 6B |
| CCR-007 | gangui | `4fd0c566-e25e-4d51-96ca-57cc46940593.3.6` | common-cause risk, `2025-11-23` group-off same-day raw-daily curated seed | `group_off_date=true`와 함께 `fault_like_weak`, `pre_ews`, `prefault_B`, `prefault_cond_mid/ae/dtw/ews`가 같은 날짜에 겹쳐 panel-local precursor처럼 보이지만 common-cause hold가 직접 필요하다 | same-day helper bundle + weak hard-like 흔적을 singleton precursor 승격 근거로 일반화하지 말 것 | Gate 2A, Gate 2C, DL-013, DL-014 |
| CCR-008 | gangui | `4fd0c566-e25e-4d51-96ca-57cc46940593.4.15` | common-cause risk, `2025-11-23` group-off same-day confirm-like tension curated seed | `group_off_date=true`와 같은 날짜에 `fault_like_day=true`, `final_fault=true`, `anom_subtype=confirmed_fault`가 겹쳐 강한 hard-like 흔적도 common-cause hold 아래서 다시 읽어야 함을 보여준다 | group-off 같은-day confirm-like 흔적을 바로 singleton hard-evidence precedent나 stable current 대체 근거로 쓰지 말 것 | Gate 2C, Gate 4, DL-014 |
| CCR-009 | ktc_ess | `10305b40-b67e-40d1-9cd1-271b6642a3d9.1.12` | common-cause risk, `2025-10-26 co_drop_surge` weak hard-like curated seed | `site_event_soft=true`, `site_event_reason=co_drop_surge`, `fault_like_weak`, `mid_i_ratio=0.0`, `critical_confirmed=0`, `final_fault=0`이 겹쳐 site-event와 panel-local hard-like 흔적이 충돌한다 | site-event와 같이 뜬 weak hard-like 하루를 panel-local hard evidence precedent로 확대하지 말 것 | Gate 2C, Gate 4, DL-014 |
| CCR-010 | ktc_ess | `ed5e3367-fbd4-4c8c-be33-c5d1c5e191b7.0.14` | common-cause risk, `2025-10-26 co_drop_surge` strong hard-like curated seed | `site_event_soft=true`, `site_event_reason=co_drop_surge`, `fault_like_strong`, `prefault_cond_dtw=true`, `mid_i_ratio≈0`, `critical_confirmed=0`, `final_fault=0`이라 stronger hard-like 흔적도 common-cause hold 아래서 재검토돼야 함을 보여준다 | strong hard-like + site-event overlap을 confirm-path 강화나 panel-local 단정 근거로 바로 연결하지 말 것 | Gate 2C, Gate 4, DL-014 |

추가 확인 메모:
- `2026-04-24` widened re-scan 기준으로 `same-day` exact overlap은 여전히 `0`이지만, `±7일` near-window에서는 `9건`이 확인됐다.
  - 대표 예시:
    - `ktc_ess / 10305...2.12`: `current_fault` 날짜 `2025-08-16` 기준 `site_event_soft` 날짜 `2025-08-11`과 `5일 차`
    - `gangui / 4fd0...4.26`: `precursor_onset` `2025-12-09` 기준 `group_off_date` `2025-12-04/03/02`와 `5~7일 차`
    - `gangui / bf1a...1.0`: `precursor_onset` `2025-11-18` 기준 `group_off_date` `2025-11-23/24`와 `5~6일 차`
- 따라서 `official current와 동시에 엮이는 common-cause 사례`의 exact same-day family는 아직 빈칸이지만, `near-window overlap backlog`은 별도 추적 가치가 있는 상태로 읽어야 한다.

필수 추가 수집 과제:
- 작업일 / 운영 이벤트 / 통신 흔들림과 직접 겹치는 사례
- `vdrop`나 `fault_like_day`가 반복되지만 common-cause를 더 먼저 의심해야 하는 사례
- precursor/current row와 `group_off_event`가 직접 겹치는 `same-day exact` 사례
- official current와 동시에 엮이는 common-cause `same-day exact` 사례
- `±7일 near-window overlap backlog`를 separate provisional family로 둘지 여부

## 8. 반례 해석 규칙
- `official_only` 사례는 precursor recall 실패의 증거가 아니다.
- `precursor_only` 사례는 hard evidence sensitivity 부족의 증거가 아니다.
- `raw_only_only` 사례는 official current 누락의 증거가 아니라 artifact lane 분리의 증거일 수 있다.
- `mlpe_ambiguous` 사례는 top1 cause를 억지 확정하지 않고 `needs-more-evidence`를 허용한다.
- `common_cause_risk` 사례는 panel-local rule을 바로 강화하는 근거로 쓰지 않는다.

## 9. 이 문서를 쓰는 방법
- Gate 3 규칙 논의:
  - `precursor_only`와 `raw_only_only`를 함께 본다.
- Gate 4 규칙 논의:
  - `raw_only_only`와 `common_cause_risk`를 함께 본다.
- Gate 5/6 operator-facing 노출 논의:
  - `official_only`와 `raw_only_only`를 함께 본다.
- 발표/운영 방어:
  - “왜 이 규칙을 넓히지 않았는가”를 설명할 때 `prohibited_overgeneralization`을 직접 인용한다.

## 10. BR-026 이후 pressure-test 읽기
- BR-026 이후에는 아래 bundle 관점으로 각 bucket을 다시 읽는다.
  - `official_only`: artifact lane separation pressure-test
  - `precursor_only`: precursor bundle minimum-condition pressure-test
  - `raw_only_only`: hard evidence bundle + lane split pressure-test
  - `mlpe_ambiguous`: ambiguity hold bundle pressure-test
  - `common_cause_risk`: common-cause hold bundle pressure-test
- 따라서 bucket을 늘리는 것만으로 충분하지 않고, 각 bucket이 `무엇을 승격시키지 못하게 막는지`까지 함께 적어야 한다.
- 실제 patch turn에서는 [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_REGRESSION_CHECKLIST_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_REGRESSION_CHECKLIST_V1.md) 를 함께 본다.

## 11. BR-028 scan result note
- `장치 응답 이상형/제어응답형 top1`은 현재 tri-site raw-only runtime heuristics scan에서 `0건`이다.
- 대신 live-chain 기준 `장치 응답 이상형` 관련 경합 shortlist `4건`은 확보됐다.
- report-row 날짜 기준 `site_event/group_off` direct overlap은 `0건`이었고, 즉 official/current/precursor row와 직접 겹치는 common-cause seed는 여전히 미관측이다.
- 반면 raw-daily level에서는 아래 provisional source가 확보됐다.
  - `gangui` group-off precursor overlap candidate cluster
  - `ktc_ess 2025-10-26 co_drop_surge` hard-like overlap cluster
- 자세한 scan 결과는 [OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_028_MISSING_SEED_SCAN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_028_MISSING_SEED_SCAN_V1.md) 를 본다.

## 11A. BR-029 promotion rule note
- BR-028에서 찾은 shortlist는 `curated counterexample seed`로 승격될 수 있다.
- 단, 이 승격은 `hold/reroute pressure-test seed` 의미만 가진다.
- 아래는 그대로 분리해 유지한다.
  - `curated seed로는 충분함`
  - `원래 찾던 exact missing family를 찾았음`
- 따라서 아래 사실은 BR-029 이후에도 계속 missing 상태로 읽는다.
  - `제어응답형 top1 = 0`
  - report-row 날짜 기준 `official/current direct overlap = 0`
- 자세한 기준은 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_013_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_013_V1.md) 와 [OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_029_PROVISIONAL_SEED_PROMOTION_CRITERIA_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_029_PROVISIONAL_SEED_PROMOTION_CRITERIA_V1.md) 를 본다.

## 11B. BR-031 curation + exact-gap re-scan note
- BR-031에서는 두 작업을 같이 수행했다.
  - BR-028 provisional shortlist 중 조건을 만족한 row를 actual curated counterexample row로 편입
    - `MLP-007..009`
    - `CCR-007..010`
  - exact missing-family를 widened re-scan으로 다시 확인
- 결과는 아래와 같다.
  - `제어응답형 top1`은 runtime/live-chain 모두 여전히 `0`
  - report-row 날짜 기준 `official/current direct overlap` same-day도 여전히 `0`
  - 대신 `±7일` near-window overlap은 `9건` 확인
- 따라서 BR-031 이후 reading은 아래처럼 분리한다.
  - curated seed set은 더 강해졌다
  - exact missing family closure는 아직 아니다
  - near-window overlap은 새 backlog 축으로 관리할 가치가 있다

## 12. 남은 과제
- `MLPE ambiguous`에서 `장치 응답 이상형` top1 또는 회복/재발까지 확인되는 사례 추가
- `common_cause risk`에서 작업일 / 운영 이벤트 / 통신 흔들림 겹침 사례 추가
- `common_cause risk`에서 precursor/current row와 `group_off_event`가 직접 겹치는 `same-day exact` 사례 추가
- `common_cause risk`에서 official current direct overlap `same-day exact` 사례 추가
- `±7일 near-window overlap backlog`를 separate provisional family로 둘지 문서에서 먼저 결정
- 반례 세트 row를 decision log와 연결하는 `regression checklist`를 실제 patch gate로 사용
- 필요 시 `challenge set`와 `counterexample set`를 분리

## 13. 다음 연결 문서
- 상위 로드맵:
  - [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- Gate 7 구현 순서:
  - [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)
- Gate 3 precursor 승격 규칙:
  - [OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md)
- Gate 4 hard evidence 경계:
  - [OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md)
- Gate 5 출력 정책:
  - [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- regression checklist:
  - [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_REGRESSION_CHECKLIST_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_REGRESSION_CHECKLIST_V1.md)
- BR-028 scan note:
  - [OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_028_MISSING_SEED_SCAN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_028_MISSING_SEED_SCAN_V1.md)
- cross-gate 감사:
  - [OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md)
