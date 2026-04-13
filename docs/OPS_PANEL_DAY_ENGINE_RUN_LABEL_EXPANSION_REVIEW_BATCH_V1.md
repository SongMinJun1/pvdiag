# OPS_PANEL_DAY_ENGINE_RUN_LABEL_EXPANSION_REVIEW_BATCH_V1

## 목적
- `run_label_expansion_audit_v1` 는 후보 풀을 넓게 찾는 데는 좋았지만, 그대로는 사람이 바로 검토하기엔 너무 넓다.
- 이번 `review_batch_v1` 는 그 후보 풀을 작은 수동 검토 배치로 줄여서 다음 scorer iteration 전 라벨 확장을 실제로 진행할 수 있게 만든다.

## 왜 broad candidate pool을 바로 쓰지 않는가
- broad pool은 `P1/P2/P3/P4` 를 모두 담고 있어 review cost가 크다.
- scorer 개선 관점에서는 모든 excluded run을 한 번에 보는 것보다,
  - `P1` 을 먼저 전부 보고
  - `P2` 는 site 균형을 맞추며 좁게 top-up 하고
  - `monitor/common-cause` 는 별도 트랙으로 분리하는 것이 훨씬 실용적이다.

## review track
- `positive_review_batch`
  - `P1` 전부
  - site별 `P2` 상위 5건
  - 남은 `P2` 중 global 상위 20건 top-up
- `monitor_review_batch`
  - monitor 후보 상위 10건
- `common_cause_review_batch`
  - common-cause 후보 전부

즉, positive label expansion을 가장 강하게 밀고, monitor/common-cause는 contamination을 피하기 위해 별도 review lane으로 유지한다.

## 왜 P1과 site-balanced P2가 먼저인가
- `P1` 은 positive gap site를 메우는 후보라 holdout generalization에 가장 직접적으로 기여한다.
- `P2` 는 점수 상위 후보지만, 한 site에 몰리면 label coverage가 다시 불균형해진다.
- 그래서 “site별 top5 + global top-up” 으로,
  - coverage 균형
  - high-score value
두 가지를 같이 잡는다.

## 왜 monitor/common-cause를 따로 떼는가
- `monitor_review_candidate` 는 direct positive/negative promotion보다 recurring burden 확인이 먼저다.
- `common_cause_review_candidate` 는 local fault scorer truth가 아니라 routing/descriptive truth 쪽에 가깝다.
- 그래서 두 집합은 positive promotion 후보와 같은 queue에 섞지 않는다.

## evidence 파일 의미
- `review_evidence_v1` 는 각 selected row에 대해
  - core/broadshape score
  - key electrical feature
  - future linkage reference
  - fate truth reference
  - reaudit overlap truth
를 같이 붙인다.

즉, reviewer가 한 줄만 보고도 “왜 이 run이 배치에 들어왔는지”를 바로 이해하도록 돕는 파일이다.

## 다음 scorer iteration으로 연결하는 방법
1. `positive_review_batch` 를 우선 수동 검토한다.
2. 승격 가능한 run을 positive/negative로 확정한다.
3. `monitor/common-cause` 는 direct train label이 아니라 별도 confirmation 결과로 남긴다.
4. 그렇게 늘어난 labeled pool을 다음 `run_ranker_v3` holdout의 입력으로 쓴다.

`run_ranker_v3` 로 넘어갈 근거는:
- 이 review batch를 반영한 뒤
- site positive gap이 줄고
- holdout top-k positive-minus-negative가 다시 의미 있게 올라갈 때다.
