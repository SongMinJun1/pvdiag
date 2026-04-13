# OPS_PANEL_DAY_ENGINE_PROJECT_CURRENT_DATA_FREEZE_PACK_V1

## 목적
- 현재 시점에는 더 이상 fault case 를 추가 수집할 수 없다는 hard constraint 아래에서, 프로젝트 전체에 대해 “지금 무엇을 얼릴 수 있는가” 를 bounded form 으로 정리한다.
- 이전 truth acquisition backlog 가 “추가로 무엇을 모아야 하는가” 를 보여줬다면, 이번 freeze pack 은 “추가 수집이 막힌 상태에서 지금 어떤 결론만 허용되는가” 를 정리한다.

## 왜 필요한가
- reliability / support-gap / truth expansion / acquisition backlog 까지 오면, 정상적인 다음 단계는 더 많은 truth/data 를 모으는 것이다.
- 하지만 그 경로가 현재 막혀 있으면, collection planning 만 반복해도 실제 writing/reporting decision 에는 도움이 되지 않는다.
- 그래서 지금은 수집 확대가 불가능하다는 제약을 전제로:
  - 지금 바로 freeze 가능한 것
  - caution 과 함께만 쓸 수 있는 것
  - exploratory 로만 남겨야 하는 것
  - operator/workflow proxy 로만 정당화되는 것을 분리해야 한다.

## current_data_decision 해석
- `freeze_as_current_default`
  - 현재 data 범위 안에서 기본 결론으로 둘 수 있다.
- `freeze_with_caution`
  - 현재 data 에서만 유효한 bounded claim 으로 유지하고, caution note 를 항상 함께 붙여야 한다.
- `exploratory_only`
  - informative 하더라도 현재는 안정적 성능 결론으로 upgrade 하면 안 된다.
- `workflow_proxy_only`
  - detector/scorer 일반화 성능이 아니라 operator workflow / packaging / QA / pipeline proxy 정당화로만 써야 한다.

## allowed_claim_strength 해석
- `operational_default_claim`
  - 현재 data 범위에서 default conclusion 으로 채택 가능
- `bounded_current_data_claim`
  - 현재 data 범위에 한정된 주장은 가능
- `exploratory_claim_only`
  - exploratory observation 으로만 사용
- `workflow_claim_only`
  - operator/workflow proxy claim 으로만 사용

## 핵심 해석
- step1 taxonomy, step2 onset truth:
  - 구조적 coverage/reference 이므로 classifier 성능 claim 이 아니라 bounded current-data claim 으로만 유지한다.
  - 이 scope들은 `current_best_target_name` 을 classifier-style best target 으로 읽으면 안 되고, `coverage_only` 같은 중립 label 로만 해석해야 한다.
- step3 precursor performance:
  - informative 하지만 underpowered 이고 acquisition 도 현재 막혀 있으므로 exploratory claim 으로만 남긴다.
  - benchmark reset 이후 precursor benchmark support는 3이고, old support 2 benchmark wording은 obsolete 다.
- step4 abrupt/no-precursor:
  - benchmark reset 이후 전조형 benchmark support는 3이고 순수 급작 benchmark support도 3이다.
  - `c42997a6-5881-47e7-9035-7de8a2673b54.1.1` 은 사건 해석상 `전조형 고장 / 급격 종료` 이며 precursor benchmark 에 포함되고 pure abrupt benchmark 에서는 제외한다.
  - 따라서 pure abrupt positive support 는 현재 3건이고, step4 abrupt scope 는 stale support 6이나 old precursor support 2 기준으로 읽으면 안 된다.
  - 현재 current-data boundary 에서는 pure abrupt scope 도 exploratory 로만 남겨야 한다.
- step4 common-cause routing:
  - descriptive / exploratory 수준으로 남겨야 한다.
- operator_policy_proxy:
  - retrospective proxy best target 과 현재 chosen operational workflow 를 구분해서 읽어야 한다.
  - 예를 들어 retrospective proxy 성능상 best target 이 하나 있어도, 실제 operational workflow 는 policy recommendation 파일이 고른 다른 workflow 일 수 있다.
  - workflow default 는 packaging/QA/pipeline validation 과 policy recommendation 으로 운영상 사용할 수 있지만, 이를 detector algorithm 성능 결론으로 과장하면 안 된다.

## writing/reporting 에서의 사용법
- 논문/보고서/발표에서 새 truth collection 없이 지금 당장 쓸 수 있는 claim boundary 를 이 pack 기준으로 정한다.
- 특히:
  - step3 는 stable detector performance 로 쓰지 않는다.
  - step4 abrupt 는 pure abrupt support 3 기준으로만 읽고, 현재는 exploratory 로 남긴다.
  - benchmark reporting 에서는 precursor benchmark support 3과 pure abrupt benchmark support 3을 직접 쓴다.
  - common-cause 는 descriptive routing 으로만 쓴다.
  - operator workflow default 는 operator/workflow proxy claim 으로만 쓴다.
  - structural scope는 “현재 best target” 이 있다고 쓰지 말고, coverage/reference scope라고만 써야 한다.
  - operator scope는 “retrospective proxy best target” 과 “chosen operational workflow” 를 같은 뜻으로 쓰지 말아야 한다.

## 주의
- 이 문서는 detector/scorer 변경안이 아니다.
- current-data-limited writing / reporting / freeze governance 문서다.
