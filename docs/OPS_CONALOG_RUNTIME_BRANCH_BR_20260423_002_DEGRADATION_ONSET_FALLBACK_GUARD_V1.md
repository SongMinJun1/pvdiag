<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_002_DEGRADATION_ONSET_FALLBACK_GUARD_V1

## [BR-20260423-002] degradation onset fallback guard
- `status`: shadow-audit
- `branch_type`: B
- `current_gate`: Gate 3
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23
- `target_review_date`: 2026-04-24

## 1. 이슈 요약
- 현재 raw-only retrospective 해석은 `primary/secondary warning`이 없으면 첫 `degradation` row를 `retrospective_onset_date`로 당겨 쓰는 fallback을 가진다.
- 이 fallback은 전조를 일찍 잡는 장점이 있지만, persistence나 common-cause guard가 없어서 onset backdating이 과민해질 위험이 있다.

## 2. 왜 브랜치인가
- onset fallback을 바꾸면 아래가 같이 흔들린다.
  - `전조날짜`
  - `사건유형`
  - `전조형 고장` 해석
  - strict trigger와의 gap 기반 설명
- 즉 단순 helper 수정이 아니라 사건 해석층 전체를 건드리는 일이라, 메인 라인에서 바로 규칙 패치로 가면 위험하다.

## 3. 현재까지의 근거

### 3.1 대표 사례는 plausibility가 있다
- `ktc_ess` 사례 분석 기준:
  - `e089...2.0`
  - `e089...2.3`
- 두 패널은 `2025-05-09`에 `degradation_strong`이 찍히고, `2025-05-16`에 `fault_like_strong`으로 넘어가 `retrospective_onset_date=2025-05-09`, `strict_trigger_date=2025-05-16`이 되었다.
- 이 둘은 실제로 `전조형 고장 / 진행성 악화` 해석이 plausible하게 읽힌다.

### 3.2 하지만 같은 날 눌린 패널이 모두 그렇게 읽히진 않는다
- 비교 패널 `e089...2.1`은 `2025-05-09`에 비슷하게 `degradation_strong`이었지만 `2025-05-16`에 `fault_like_day`가 안 찍혀 `미확정`으로 남았다.
- 즉 첫 degradation row만으로는 later fault progression을 충분히 구분하지 못할 수 있다.

### 3.3 subgroup/common-cause와의 경계가 아직 불안정하다
- `ktc_ess 2025-05-09`는 `site_event=0`인데 두 subgroup에서 `12패널`이 함께 눌린 날이었다.
- 이 날은 site-wide common-cause는 아니지만, panel-local onset으로만 보기에도 애매하다.
- 따라서 onset fallback은 최소한 `subgroup/common-cause shadow evidence`와의 상호작용까지 같이 검토해야 한다.

### 3.4 direct 수정 전 비교표가 필요하다
- 지금까지는 onset fallback의 위험성을 사례 수준으로는 확인했지만,
  - false backdating 빈도
  - guard 적용 시 onset 이동량
  - 사건유형 변화량
  를 표로 정리한 branch-level 비교는 아직 부족하다.

### 3.5 첫 tri-site gap/persistence 비교표 결과
- 2026-04-23 tri-site raw-only audit 기준으로, `onset_method=anom_subtype:degradation` fallback은 `gangui`와 `ktc_ess`에서만 관측됐다.
  - `gangui / 고장`: `10 panels`, median gap `1d`, max gap `7d`, `one-day degrade span=5`, `persistent span>=2=5`, onset-day subgroup `6`
  - `ktc_ess / 고장`: `10 panels`, median gap `270d`, max gap `270d`, `one-day degrade span=9`, `persistent span>=2=1`, onset-day subgroup `7`
- 즉 `gangui` 쪽 fallback은 짧은 gap과 persistence가 섞여 있어 전부 과민 backdating으로 보긴 어렵지만, `ktc_ess` 쪽은 `270일` gap + `one-day degradation` 패널이 다수라서 guard 필요성이 훨씬 강하다.

### 3.6 guard 후보를 G1 vs G2b로 정제해보면
- 이번 branch의 실제 비교 후보는 아래 둘로 좁혔다.
  - `G1_extreme_longgap_one_day`
    - `gap_days >= 30`
    - `degrade_days_between_onset_and_strict <= 1`
  - `G2b_longgap_and_subgroup_one_day`
    - `gap_days >= 7`
    - `degrade_days_between_onset_and_strict <= 1`
    - `onset_day_subgroup_common_cause = 1`
- A/B 결과:
  - `G1`: `7 panels`, 전부 `ktc_ess`, `전조형 고장 -> 급작 고장 candidate 7`, strict proximal overlap `6 / 7`
  - `G2b`: `6 panels`, 전부 `ktc_ess`, `전조형 고장 -> 급작 고장 candidate 6`, strict proximal overlap `4 / 6`
- 둘 다 `gangui`를 추가로 건드리지 않는다는 점은 좋지만, 현재 표본에서는 `G1`이 더 좁으면서도 더 많은 extreme long-gap 사례를 잡는다.

### 3.7 왜 G2(longgap or subgroup one-day)는 제외했는가
- `G2_longgap_or_subgroup_one_day`는 아래 `6`건을 추가로 잡는다.
  - `gangui`의 `gap 0d + subgroup-only` `3건`
  - `ktc_ess`의 `subgroup 없는 long-gap` `3건`
- 이 중 `gangui` `3건`은 이번 branch에서 “짧은 gap plausible 사례”로 보고 보호하려는 묶음이라, 현재 후보 비교에선 제외하는 편이 더 안전하다.
- 따라서 이 branch에서는 `G2`를 직접 후보로 쓰지 않고 `G1`과 `G2b`만 비교 대상으로 유지한다.

### 3.8 G1 shadow audit flag 패치
- 2026-04-23 패치에서는 실제 onset fallback 규칙을 바꾸지 않고, audit 산출물에만 `G1_extreme_longgap_one_day` shadow flag를 추가한다.
- flag 조건은 아래로 고정한다.
  - `onset_method = anom_subtype:degradation`
  - `gap_days >= 30`
  - `degradation_onset_backdate_guard_degrade_days <= 1`
- 이 flag는 “현재라면 `전조형 고장`으로 남지만, fallback 제거 후보로 보면 `급작 고장` 전환 가능성이 있는 사례”를 표시하는 용도다.
- `retrospective_onset_date`, `전조흔적_flag`, `사건유형_재판정_ko`, `최종고장양상_재판정_ko`는 이번 패치에서 변경하지 않는다.
- 근거: G1은 A/B 표에서 `ktc_ess` extreme long-gap 사례 `7건`을 잡고, 보호하려는 `gangui` short-gap 사례를 건드리지 않았다.

## 4. 지금 메인 라인에서 허용되는 것
- 사례 deep dive
- onset vs strict-trigger 간격 분석
- persistence/common-cause guard 후보 비교
- warning/proximal/common-cause와 onset fallback의 관계 메모
- audit 표 / branch note 업데이트

## 5. 지금 메인 라인에서 금지되는 것
- fallback 규칙 즉시 변경
- `panel_day_engine.py` threshold 조정
- current surface의 날짜 의미 변경
- direct operator-facing wording 재정의

## 6. 필요한 추가 근거
- `degradation_strong -> fault_like_strong`로 이어지는 대표 사례 추가
- false backdating처럼 보이는 사례 묶음
- onset fallback guard 후보별 변화량 비교
  - `retrospective_onset_date` 이동
  - `전조형 고장 -> 미확정` 전환 수
  - strict trigger와의 간격 변화
- 첫 tri-site 비교표 기준:
  - `pure persistence`는 `gangui`를 과하게 건드릴 수 있다.
  - 따라서 다음 비교는 `long-gap + one-day fallback` 계열 후보 중심으로 보는 편이 낫다.
- 현재 A/B 기준:
  - `G2`는 `gangui gap 0d subgroup-only`를 같이 잡아 제외
  - `G1` vs `G2b`만 유지
- subgroup/common-cause shadow evidence가 onset 과민을 줄이는지 여부

## 7. 잠정 판단
- onset fallback은 완전히 잘못된 규칙은 아니다.
- 다만 지금 상태로는 과민 backdating 위험이 남아 있고, 특히 subgroup/common-cause 경계가 불안정할 때 더 보수적인 guard가 필요해 보인다.
- 첫 tri-site 표 기준으로는 `pure persistence guard`보다 `long-gap 기반 보수 guard`가 더 유망하다.
- 현재 A/B 후보 중에선 `G1_extreme_longgap_one_day`가 다음 shadow/code patch 후보로 가장 적합해 보인다.
- `G2b`는 subgroup 맥락이 있는 중간 후보로 남겨두되, `G1` 검증 후에도 `7일 subgroup` 사례를 별도로 다뤄야 할 때만 후속 후보로 다시 보는 편이 낫다.
- 따라서 현재 branch의 기본 방향은:
  - **`G1`은 shadow audit flag로 먼저 붙이고, 실제 onset fallback 제거 여부는 fresh tri-site rerun 결과를 본 뒤 결정한다**.

## 8. 복귀 조건
- `G1` shadow audit flag fresh tri-site rerun 완료
- 대표 사례 + false backdating 사례를 같이 묶은 비교표 확보
- guard 적용 시 변화량을 보고 decision log 초안 작성 가능 수준까지 축소

## 9. 관련 문서/결정
- [OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md)
- [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)
- [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md)
- [OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md)
