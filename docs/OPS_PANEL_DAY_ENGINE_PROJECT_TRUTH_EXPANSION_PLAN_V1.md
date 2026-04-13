# OPS_PANEL_DAY_ENGINE_PROJECT_TRUTH_EXPANSION_PLAN_V1

## 목적
- `project_eval_reliability_v1` 와 `project_eval_support_gap_v1` 에서 드러난 약한 평가 scope를 실제 다음 액션으로 번역한다.
- freeze 판단과 truth/data expansion 판단을 한 표에서 섞지 않고, "무엇을 더 모아야 하는가" 와 "지금 무엇을 얼릴 수 있는가" 를 분리해 보여준다.

## 왜 필요한가
- reliability audit는 어떤 row가 `underpowered`, `low_support`, `proxy_only`, `structural_only` 인지 알려주지만, 그 다음에 실제로 어떤 데이터를 더 모아야 하는지는 직접 말해주지 않는다.
- support-gap audit는 "얼마나 더 필요한가" 와 "current artifacts 만으로 가능한가" 를 보여주지만, 여전히 팀이 다음 스프린트에서 무엇을 수집해야 하는지까지는 정리하지 않는다.
- 그래서 이번 산출물은 support gap을 `collect_new_precursor_truth_cases`, `collect_new_common_cause_truth_cases`, `collect_new_abrupt_truth_cases`, `workflow_validation_not_truth` 같은 실제 action class로 바꿔 준다.

## 출력물

### 1) `panel_day_engine_project_truth_expansion_plan_v1.csv`
- support-gap row마다 현재 support, 추가 필요량, current artifact candidate pool, 새 truth/data 필요 여부를 함께 적는다.
- `expansion_action_class` 로 다음 액션을 정한다.
- `priority_rank` 는 작은 숫자가 더 높은 우선순위다.

### 2) `panel_day_engine_project_truth_expansion_plan_summary_v1.csv`
- action class 단위로 몇 개 target이 걸려 있는지, support 5/10 까지 얼마나 더 필요한지, 실제로 새 truth/data 가 필요한 row가 몇 개인지 요약한다.

### 3) `panel_day_engine_project_freeze_plan_v1.csv`
- 기존 `project_eval_freeze_candidates_v1.csv` 를 현재 default decision 관점으로 다시 쓴다.
- expansion plan이 "무엇을 더 모을까" 라면, freeze plan은 "지금 어떤 결론을 얼릴까" 를 말한다.

## action class 해석
- `no_action_structural`
  - step1 taxonomy, step2 onset coverage 처럼 classifier metric이 아닌 구조적 coverage row다.
  - 새 truth 수집보다 문서/coverage 유지가 우선이다.
- `collect_new_precursor_truth_cases`
  - step3 precursor-bearing scope의 positive support를 늘리기 위한 새 fault-case truth와 onset corroboration 수집이다.
- `collect_new_common_cause_truth_cases`
  - step4 common-cause routing scope를 위해 새 group-side / common-cause site event truth를 늘린다.
- `collect_new_abrupt_truth_cases`
  - step4 abrupt/no-precursor scope를 위해 새 panel-level abrupt anchor truth를 늘린다.
- `workflow_validation_not_truth`
  - operator policy proxy는 retrospective proxy metric 이므로 truth label 추가보다 실제 workflow observation, shadow review, reviewer load 검증이 더 중요하다.

## requires_new_truth_or_data_flag 해석
- `1`
  - current artifact candidate pool이 0이고, 아직 `freeze_as_current_default` 가 아닌 row다.
  - 즉 현재 산출물만 재정리해서는 해결되지 않고 genuinely new truth/data expansion이 필요하다.
- `0`
  - current artifact pool이 남아 있거나, structural/proxy row라 truth expansion 문제가 아니거나, 이미 freeze 기본값으로 볼 수 있는 경우다.

## freeze plan 읽는 법
- `freeze_as_current_default`
  - 현재 support/reliability 기준으로 기본 결론으로 채택 가능하다.
- `freeze_with_caution`
  - 현재 결론은 유지하되, support나 validation 한계를 함께 명시해야 한다.
- `do_not_freeze`
  - 아직 결론을 얼리지 말고 truth/data expansion 또는 validation을 먼저 해야 한다.

## 주의
- 이 문서는 detector/scorer 변경안이 아니다.
- truth/data expansion 우선순위를 정리하는 운영/연구 planning 산출물이다.
