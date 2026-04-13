# OPS PANEL DAY ENGINE PROJECT EVAL MATRIX V1

## 목적

`build_panel_day_engine_project_eval_matrix_v1.py` 는 현재까지 완성된 project 평가 조각들을 한 장의 matrix로 모읍니다. 이 matrix는 모든 row에 억지로 precision/recall/F1를 붙이지 않고, 구조적 coverage row, true case metric row, retrospective proxy metric row를 구분해서 보여줍니다.

## 왜 step 1 / step 2는 precision/recall/F1가 아닌가

step 1 taxonomy는 fault family가 어떤 eval bucket으로 정리되어 있는지와 support가 어느 정도인지 보여주는 구조적 coverage 작업입니다. 이는 classifier가 positive/negative를 예측한 결과가 아니므로 precision/recall/F1를 붙이면 의미가 왜곡됩니다.

step 2 onset truth도 마찬가지로 marker coverage와 lead availability를 보는 row입니다. 예를 들어 `first_cond_evt` 나 `preferred_precursor_onset` 이 몇 case에서 정의되었는지를 보는 것이지, negative case를 분류하는 precision task가 아닙니다. 그래서 matrix에서는 `metric_kind = structural_coverage_metric` 으로 분리하고 precision/recall/F1는 비워 둡니다.

## 왜 step 3 / step 4는 true case-level metric인가

step 3은 precursor-bearing detectable-now case를 positive로, abrupt/common-cause case의 pre-anchor window를 negative로 두고 marker hit 여부를 비교합니다. 이 row들은 실제 positive/negative case 구분을 포함하므로 true case-level precision/recall/F1가 의미 있습니다.

step 4A는 pure abrupt/no-precursor case에서 hard fault marker hit가 얼마나 잘 잡히는지 보고, precursor/common-cause case를 negative로 둡니다. benchmark reset 이후 이 matrix의 공식 benchmark 분모는 audited event semantics에서 다시 고정한 precursor 3 / pure abrupt 3 / common-cause 4 입니다. `c42997a6-5881-47e7-9035-7de8a2673b54.1.1` 은 사건 해석상 `전조형 고장 / 급격 종료` 이며 precursor benchmark 에 포함되고 pure abrupt benchmark 에서는 제외됩니다. 그래서 step 4A positive support 는 pure abrupt benchmark 3건으로만 계산합니다. old precursor 2 benchmark wording은 더 이상 이 matrix의 공식 분모가 아닙니다. step 4B는 non-panel/common-cause routing marker가 다른 bucket과 얼마나 구분되는지 보는 row입니다. 둘 다 true case-level yes/no 비교이므로 classifier-style metric을 붙일 수 있습니다.

## 왜 operator policy는 retrospective proxy metric인가

operator policy row는 baseline / discovery panel / narrow / cluster / workflow default 중 어떤 view가 retrospective linked/truth proxy를 더 많이 포함하는지를 panel 단위로 비교합니다. 하지만 이 label은 미래 linkage/truth reference 기반 proxy이므로 prospective operator efficiency를 직접 측정하는 것은 아닙니다.

따라서 operator policy row의 precision/recall/F1는:

- workflow가 retrospective value proxy를 얼마나 많이 품는지 보는 참고 지표
- 실제 review latency, operator load, decision cost를 대체하지는 못하는 지표

로 읽어야 합니다.

## 어떻게 읽어야 하는가

이 matrix는 아래 순서로 읽는 것이 안전합니다.

1. step 1 / step 2: project가 어떤 taxonomy support와 onset coverage를 갖추었는지 확인
2. step 3 / step 4: true case-level precision/recall/F1로 실제 marker discrimination을 확인
3. operator policy: retrospective proxy metric으로 operator-facing view의 보조 가치를 확인

특히 step 4 abrupt/no-precursor 는 "fault가 급격히 끝났는가" 와 "그 event type 자체가 abrupt 인가" 를 구분해서 읽어야 합니다. precursor 가 있으면 event class 는 abrupt 가 아니고, abrupt 는 terminal failure pattern 으로만 남습니다. benchmark reset 이후에는 이 해석을 precursor benchmark 3 / pure abrupt benchmark 3 으로 직접 반영합니다.

즉, 한 row의 수치만 보고 project 전체를 과장 해석하면 안 됩니다. 구조적 coverage, true case metric, retrospective proxy metric은 서로 다른 질문에 답하고 있기 때문입니다.
