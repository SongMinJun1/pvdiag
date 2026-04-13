# OPS_PANEL_DAY_ENGINE_PROJECT_TRUTH_ACQUISITION_BACKLOG_V1

## 목적
- `project_truth_expansion_plan_v1` 의 방향성은 유지하되, target-level row를 그대로 더할 때 생기는 과대계산을 제거한다.
- 다음 수집 스프린트에서 실제로 몇 개의 `fault_case`, `panel_case`, `site_event`, `workflow_observation` 이 필요한지 unique collection unit 기준으로 보여준다.

## 왜 필요한가
- 기존 truth expansion plan은 각 eval target마다 필요한 방향을 잘 보여주지만, 같은 scope 안의 여러 target이 동일한 underlying support를 공유할 수 있다.
- 그래서 step3 marker 6개를 row 단위로 더하면 `+18` 같은 숫자가 나오더라도, 실제로는 `+3 precursor-bearing fault_case` 로 여섯 target을 함께 보강할 수 있다.
- step4 common-cause도 마찬가지로 target 3개가 같은 `site_event` support를 공유할 수 있으므로, unique acquisition backlog로 접어야 실제 수집 계획이 된다.

## collection unit 해석
- `fault_case`
  - precursor-bearing truth 확장 단위다.
  - 하나의 새 precursor-bearing fault case가 여러 precursor marker target을 동시에 보강할 수 있다.
- `panel_case`
  - abrupt/no-precursor anchor truth 확장 단위다.
  - 여러 abrupt hit target이 같은 panel-level abrupt case를 함께 본다.
- `site_event`
  - common-cause / group-side truth 확장 단위다.
  - 여러 routing target이 같은 site-level event support를 공유한다.
- `workflow_observation`
  - operator proxy scope용이다.
  - truth label acquisition이 아니라 shadow review, triage latency, reviewer load 같은 운영 관찰 backlog다.
- `none`
  - step1 taxonomy, step2 onset coverage처럼 structural/documentation 유지용 scope다.

## 출력물

### 1) `panel_day_engine_project_truth_acquisition_backlog_v1.csv`
- scope당 한 줄만 만든다.
- `current_positive_support_unique` 는 그 scope의 target들이 공유하는 underlying support를 보수적으로 `min(current_positive_support)` 로 잡는다.
- `additional_units_needed_for_5` / `10` 도 scope 단위로 한 번만 계산한다.

### 2) `panel_day_engine_project_truth_acquisition_backlog_summary_v1.csv`
- `collection_unit` 와 `expansion_action_class` 조합별로 몇 scope가 걸려 있는지, unique support가 얼마나 있는지, 실제로 몇 unit이 더 필요한지 요약한다.

### 3) `panel_day_engine_project_truth_acquisition_notes_v1.csv`
- 왜 target-level 합산이 과대계산인지, 왜 unique-unit backlog가 더 좋은지 scope별로 짧게 설명한다.
- 예시:
  - step3 marker 6개는 `+18` different cases가 아니라 `+3 fault_case`
  - step4 common-cause 3개 target은 `+3` different events가 아니라 `+1 site_event`

## freeze_status_ko 읽는 법
- `freeze_as_current_default`
  - 해당 scope는 현재 기본 결론으로 채택 가능하다.
- `freeze_with_caution`
  - 결론은 유지하되, support/validation 한계를 함께 써야 한다.
- `do_not_freeze`
  - 새 truth/data expansion 또는 validation이 먼저 필요하다.

## 실무 해석
- 이 backlog는 detector/scorer 변경안이 아니다.
- 다음 real-world collection effort에서 무엇을 몇 단위 더 모아야 하는지 보여주는 acquisition planning 산출물이다.
- 따라서 target row 개수보다, deduplicated unique collection unit 수를 우선해서 읽어야 한다.
