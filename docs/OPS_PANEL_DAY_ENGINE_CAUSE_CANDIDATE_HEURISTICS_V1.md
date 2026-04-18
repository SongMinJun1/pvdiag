# OPS_PANEL_DAY_ENGINE_CAUSE_CANDIDATE_HEURISTICS_V1

## 목적
- 이 산출물은 real fault panel 6건에 대해 원인후보를 좁히는 heuristic candidate-ranking layer다.
- detector logic이나 final verdict를 바꾸지 않고, 현재 front-facing verdict/evidence 위에 field trial용 점검 우선순위 층만 추가한다.
- 이 표는 final root-cause confirmation이 아니라 candidate narrowing을 위한 실험층이다.

## 입력
- `_share/panel_day_engine_integrated_result_table_v1.csv`
- `_share/panel_day_engine_gpvs_evidence_pack_v1.csv`
- `_share/panel_day_engine_panel_multiaxis_verdict_v1.csv`
- `_share/panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv` if present

## 출력
- `_share/panel_day_engine_cause_candidate_heuristics_v1.csv`
- `_share/panel_day_engine_cause_candidate_score_breakdown_v1.csv`
- `_share/panel_day_engine_cause_candidate_summary_v1.csv`

## 해석 원칙
- 이 층은 heuristic candidate-ranking layer다.
- additive scoring만 사용한다.
- score는 verdict, kernel-log, GPVS reference, 시간양상 신호를 투명하게 더한 값이다.
- output은 field trial triage용 후보 좁히기 표이지 definitive diagnosis가 아니다.
- final root-cause confirmation은 별도 현장 점검과 추가 증거가 필요하다.
- V2에서는 `전기적 고장 계열` 과 `다이오드형` 규칙의 diode bias를 한 단계 낮추고, 경합 panel은 공동 점검 후보로 더 명시적으로 노출한다.

## canonical candidate universe
- 부분음영형
- 오염형
- 열화형
- 다이오드·서브스트링형
- 접속·부분개방형
- 센서·피드백형
- 제어응답형
- 외부계통교란형
- 전력변환부형
- 원인미확정

## 점수 규칙
- GPVS external pattern, GPVS internal family, kernel-log family, 사건유형/최종고장양상, GPVS usage tier에서 정해진 가산 규칙만 적용한다.
- 감점은 쓰지 않는다.
- tie는 field-actionable 우선순위로 푼다.
  - `접속·부분개방형 > 다이오드·서브스트링형 > 부분음영형 > 오염형 > 열화형 > 센서·피드백형 > 제어응답형 > 외부계통교란형 > 전력변환부형 > 원인미확정`
- V2 rebalancing:
  - `GPVS_내부참고유형_ko == 전기적 고장 계열` 일 때 `다이오드·서브스트링형` 가산은 `+2 -> +1`
  - `커널로그_원인군_ko == 다이오드형` 일 때 `다이오드·서브스트링형` 가산은 `+3 -> +2`

## 경합 규칙
- top1과 점수 차이가 1점 이내인 후보를 모두 `공동상위후보` 로 묶는다.
- `원인후보_경합상태_ko`
  - `단일우세`: top1 근처 후보가 1개뿐인 경우
  - `2자경합`: top1 근처 후보가 2개인 경우
  - `다자경합`: top1 근처 후보가 3개 이상인 경우
- `원인후보_공동상위후보_csv`:
  공동상위후보를 점수순/tie-priority 순으로 나열한다.
- `원인후보_실증우선확인_ko`:
  현장 trial에서 같이 먼저 열어볼 joint inspection note다. 이 문구는 final diagnosis가 아니라 현재 `공동상위후보` 순서를 그대로 field action wording으로 바꾼 것이다.

## 신뢰도
- `high`: top1 score >= 6 and 경합상태 == 단일우세
- `medium`: top1 score >= 4 and 경합상태 != 다자경합
- `low`: 그 외

## 읽는 법
- `원인후보_top1_ko`:
  현재 점수상 가장 먼저 field check를 걸어볼 후보
- `원인후보_top2_ko`, `원인후보_top3_ko`:
  같이 열어 두어야 할 대안 가설
- `원인후보_경합상태_ko`, `원인후보_공동상위후보_csv`:
  single-label처럼 보이더라도 실제로는 공동 점검 후보인지 드러내는 V2 field
- `원인후보_실증우선확인_ko`:
  현장 team이 먼저 같이 확인할 후보 조합 또는 우선 점검 대상을 한 줄로 적는다. multi-way competition row는 앞의 3개 공동상위후보를 그대로 적고, 이 문구 자체는 final diagnosis가 아니라 field-trial inspection guidance다.
- `원인후보_해석메모_ko`:
  어떤 front-facing 신호가 top candidate를 밀어 올렸는지 요약
- `score_breakdown`:
  panel × candidate long-form 가산 규칙 내역

## 주의
- 이 출력은 direct root-cause classifier가 아니다.
- GPVS는 여전히 reference layer다.
- 이 표는 현장 trial에서 점검 순서를 좁히기 위한 보조층으로만 사용한다.
- 특히 `2자경합` / `다자경합` row는 한 후보를 확정했다는 뜻이 아니라 공동 현장점검 후보를 드러낸 것이다.
- action note는 scoring rule을 다시 바꾸는 문장이 아니라, 현재 경쟁 후보 순서를 그대로 field-trial joint inspection 문장으로 바꾼 것이다.

## 검증
- `python -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_cause_candidate_heuristics_v1.py research/prognostics/smoke_test_panel_day_engine_cause_candidate_heuristics_v1.py`
- `python research/prognostics/build_panel_day_engine_cause_candidate_heuristics_v1.py`
- `python research/prognostics/smoke_test_panel_day_engine_cause_candidate_heuristics_v1.py`
