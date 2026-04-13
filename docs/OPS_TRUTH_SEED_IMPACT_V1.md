# OPS_TRUTH_SEED_IMPACT_V1

## 목적
- 현재 canonical truth 상태와
- round-1 seed가 반영된 sidecar canonical proposal 상태를

같은 평가 로직으로 비교해서, seed가 F1 자체를 얼마나 바꾸는지와 manual-truth coverage를 얼마나 늘리는지를 함께 본다.

중요한 점:
- 이 평가는 canonical truth를 덮어쓰지 않는다.
- 이 평가는 "점수만" 보는 단계가 아니다.
- trustworthiness 개선 자체를 1차 결과로 본다.

## 왜 지금 이 평가가 필요한가
- round-1 review batch, intake preview, copyback apply까지 오면서 일부 strict case는 사람이 검토한 seed를 sidecar로 안전하게 준비할 수 있게 됐다.
- 이 시점에는 "이 seed가 점수를 얼마나 바꾸는가?"보다 먼저
  - manual truth가 얼마나 늘어나는가
  - vendor truth 의존이 얼마나 줄어드는가
  - conflict 없이 baseline 신뢰도를 얼마나 올리는가
를 봐야 한다.

즉 seed 10건은 작은 수여도, F1 변화보다 truth provenance 개선을 확인하는 preview로 충분히 의미가 있다.

## 비교 대상
- current: `_share/panel_date_reaudit_working.csv`
- proposed: `_share/panel_date_reaudit_working_proposed_v1.csv`

## 평가 원칙
`evaluate_full_algorithm_f1_v3.py`와 같은 축을 쓴다.
- strict-case base universe
- hybrid truth precedence
- `truth_mode in {strict, lenient}`
- `prediction_mode in {maintenance, operational}`
- `source_split in {overall, manual_truth, vendor_truth}`
- `actionability_v3` prediction source

## 출력 파일
- `_share/truth_seed_impact_summary_v1.csv`
- `_share/truth_seed_impact_metric_delta_v1.csv`
- `_share/truth_seed_impact_changed_cases_v1.csv`

## 해석 포인트

### 1. `delta_f1`만 보면 안 된다
seed 수가 작으면 F1은 거의 안 변할 수 있다.  
그래도 다음이 좋아지면 baseline trustworthiness는 실제로 개선된 것이다.
- `delta_manual_truth_present_count > 0`
- `delta_vendor_truth_used_count < 0`
- changed cases가 conflict-free manual seed로 설명됨

### 2. `delta_manual_truth_present_count`는 1차 결과다
manual truth가 늘었다는 것은:
- vendor-only 판정이 줄고
- 사람이 검토한 근거가 늘고
- 이후 baseline 해석이 더 방어 가능해진다는 뜻이다.

즉 F1이 거의 그대로여도 manual truth 증가 자체가 중요한 outcome이다.

### 3. `delta_vendor_truth_used_count` 감소는 좋은 신호다
conflict가 없다면 vendor truth 의존이 manual truth로 대체되는 것은 바람직하다.
- reviewer 근거가 더 직접적이고
- 추후 dispute 설명이 쉬워지고
- label provenance가 강해진다.

## changed-case audit 읽는 법
`truth_seed_impact_changed_cases_v1.csv`는 current와 proposed 사이에서 truth source 또는 truth label이 바뀐 strict case만 보여준다.

주요 change type:
- `vendor_to_manual_same_label`
  - polarity는 그대로고 provenance만 manual로 강화된 경우
- `vendor_to_manual_label_changed`
  - manual seed가 vendor polarity를 실제로 뒤집는 경우
- `excluded_to_manual_scored`
  - 예전엔 exclude였는데 이제 scored truth로 들어오는 경우

## 언제 현재 sidecar를 수동 promote해도 되는가
다음 조합이면 promote 판단 근거가 생긴다.
- `delta_manual_truth_present_count`가 의미 있게 증가
- `delta_vendor_truth_used_count`가 감소
- `delta_f1`가 크게 악화되지 않음
- changed cases가 reviewer 설명으로 납득 가능
- copyback apply 단계에서 conflict가 없음

이 경우에는 seed expansion을 잠시 멈추고 현재 sidecar를 manual promote하는 쪽이 합리적일 수 있다.

## 언제 나머지 14건 라벨링을 계속해야 하는가
다음이면 seed expansion을 계속하는 편이 낫다.
- `delta_manual_truth_present_count`는 늘었지만 overall trust improvement가 아직 작음
- 여전히 vendor truth 의존이 높음
- changed cases 대부분이 일부 site/bucket에만 몰림
- F1 변동 해석이 불안정하고 score noise가 큼

즉 이번 평가는 "끝내기"보다 "다음 라벨링이 얼마나 가치 있는지"를 판단하는 기준점으로도 쓴다.

## 운영 권장 순서
1. `truth_seed_impact_summary_v1.csv`에서 total delta를 먼저 본다.
2. `truth_seed_impact_metric_delta_v1.csv`에서 `overall`과 `manual_truth` split을 같이 본다.
3. `truth_seed_impact_changed_cases_v1.csv`에서 어떤 strict case가 provenance 변경을 만들었는지 확인한다.
4. 그 다음에만 sidecar promote 또는 추가 라벨링을 결정한다.
