# OPS_PANEL_DAY_ENGINE_OPERATOR_ATTENTION_POLICY_AUDIT_V1

## 목적

operator-facing artifact가 여러 층으로 정리되었다고 해서, 곧바로 어떤 view를 기본 workflow로 써야 하는지가 자동으로 정해지는 것은 아닙니다.

이 audit의 목적은 현재 이미 생성되는 네 가지 attention view를 같은 current-state 기준에서 나란히 비교하고,
"운영자가 기본으로 어떤 화면을 읽어야 하는가"를 retrospective value proxy까지 포함해 결정하는 것입니다.

이 패치는 detector/scorer 변경이 아니라, workflow selection용 operator audit입니다.

## 비교 대상

정확히 아래 네 가지 view만 비교합니다.

- `baseline_only`
  - `panel_day_engine_operator_attention_now_v1.csv`
- `baseline_plus_discovery_panel`
  - `panel_day_engine_operator_attention_plus_discovery_preview_v1.csv`
- `baseline_plus_discovery_narrow`
  - `panel_day_engine_operator_attention_plus_discovery_preview_narrow_v1.csv`
- `baseline_plus_discovery_cluster`
  - `panel_day_engine_operator_attention_plus_discovery_cluster_preview_v1.csv`

## 왜 다음 질문이 workflow selection인가

- packaging은 "만들 수 있는가"의 문제입니다.
- workflow selection은 "운영자가 무엇을 기본으로 읽어야 하는가"의 문제입니다.

즉 baseline, discovery preview, cluster preview, unified digest가 다 만들어졌더라도,
default workflow를 정하지 않으면 operator는 여전히 여러 artifact를 병렬로 훑어야 합니다.

이 audit은 그 다음 단계인 default view 선택을 위한 비교표입니다.

## 비교 방식

각 정책 view를 current-row level에서 비교합니다.

공통 비교 항목:
- total item count
- queue run count
- watch_now panel count
- discovery panel count
- discovery cluster count
- site concentration
- retrospective linked reference proxy

여기서 retrospective value proxy는 다음 두 필드를 사용합니다.
- fault linked ref count
- truth linked ref count

그리고
- `fault_or_truth_linked_ref_count`
  - linked 혹은 truth ref가 하나라도 있는 current row 수

를 계산해 baseline 대비 incremental gain을 봅니다.

중요:
- linked_ref / truth_ref count는 retrospective usefulness proxy일 뿐입니다.
- 실제 selection rule이나 detector logic에 future 정보를 넣는 것이 아닙니다.

## 추천 휴리스틱

기본 방향은 세 가지입니다.

- incremental linked gain이 거의 없으면 `baseline_only`
- cluster preview가 panel preview 대비 linked gain을 어느 정도 유지하면서 extra item을 확실히 줄이면 `baseline_plus_discovery_cluster`
- narrow preview가 cluster preview와 거의 비슷한 gain을 더 적은 item으로 주면 `baseline_plus_discovery_narrow`

즉 recall만 보는 것이 아니라,
- 얼마나 더 많은 linked proxy를 주는지
- 그 대가로 몇 줄을 더 읽어야 하는지
- 특정 site로 얼마나 쏠리는지

를 같이 봅니다.

## 추천 결과 해석

- `baseline_only`
  - 추가 discovery layer를 기본 workflow에 넣을 만큼 incremental value가 아직 작다는 뜻입니다.
- `baseline_plus_discovery_panel`
  - recall을 최우선으로 볼 때 유리하지만, operator load와 site skew가 커질 수 있습니다.
- `baseline_plus_discovery_narrow`
  - panel preview보다 줄인 discovery rows를 기본 workflow에 붙이는 선택입니다.
- `baseline_plus_discovery_cluster`
  - discovery signal을 cluster 단위로 압축해, baseline 위에 가장 가벼운 supplemental layer를 붙이는 선택입니다.

## 산출물

- `_share/panel_day_engine_operator_attention_policy_summary_v1.csv`
  - 네 policy view의 current-state 비교표
- `_share/panel_day_engine_operator_attention_policy_recommendation_v1.csv`
  - 기본 workflow 추천 1행

## detector change가 아닌 이유

- 이 audit은 기존 generated artifact만 읽습니다.
- detector rule, scorer, canonical truth template contract는 바꾸지 않습니다.
- 현재 operator-facing view 중 어느 것을 default workflow로 볼지 판단하는 비교 layer입니다.
