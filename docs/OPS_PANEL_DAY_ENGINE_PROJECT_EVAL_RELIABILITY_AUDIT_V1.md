# OPS PANEL DAY ENGINE PROJECT EVAL RELIABILITY AUDIT V1

## 목적

`build_panel_day_engine_project_eval_reliability_audit_v1.py` 는 `project_eval_matrix_v1` 를 그대로 받아서 각 row가 지금 freeze-ready 한지, 아니면 아직 support가 너무 작아 조심해서 읽어야 하는지를 정리합니다.

## 왜 project_eval_matrix_v1 만으로는 부족한가

project evaluation matrix는 step 1, 2, 3, 4, operator policy proxy를 한 표로 모으는 데는 유용합니다. 하지만 같은 표 안에 있다고 해서 모든 row가 같은 신뢰도로 해석되는 것은 아닙니다. 특히 positive support가 몇 건 안 되는 true case metric은 F1가 좋아 보여도 매우 불안정할 수 있습니다.

그래서 freeze 전에 한 번 더 봐야 할 질문은 다음입니다.

- 이 row는 classifier metric이 맞는가?
- 맞다면 positive support가 충분한가?
- support가 작다면 perfect F1도 우연일 수 있지 않은가?
- proxy metric을 실제 detector 성능처럼 읽고 있지는 않은가?

## 작은 support에서 perfect F1가 왜 위험한가

positive case가 2건, 3건 같은 매우 작은 분모에서는 한 건 차이만으로 recall/precision/F1가 크게 흔들립니다. 이런 row에서 F1=1.0 이 나와도 그것이 곧 freeze-ready default라는 뜻은 아닙니다. 이 audit은 그래서 Wilson confidence interval을 함께 계산하고, support 크기에 따라 `underpowered`, `low_support`, `provisional` 로 나눕니다.

## structural / proxy row는 왜 ordinary classifier처럼 읽으면 안 되는가

- `structural_coverage_metric`
  step 1 taxonomy support, step 2 onset coverage row처럼 구조적 coverage만 보여주는 row입니다. precision/recall/F1 자체가 문제 정의에 맞지 않습니다.

- `retrospective_proxy_metric`
  operator workflow/policy row처럼 미래 linked/truth ref를 proxy label로 쓰는 retrospective metric입니다. retrospective value proxy는 보여주지만, prospective operator default 성능을 직접 보장하지는 않습니다.

즉, 이 두 종류는 ordinary classifier metric과 같은 기준으로 freeze 여부를 단정하면 안 됩니다.

## freeze_recommendation 해석

- `do_not_freeze`
  현재 support가 너무 작거나 해석 안정성이 낮아 project conclusion의 현재 default로 고정하지 않는 편이 안전합니다.

- `freeze_with_caution`
  정보 가치는 있지만 구조적 row이거나 proxy row이거나, 또는 support가 아직 작아서 주석과 caveat를 함께 붙여야 합니다.

- `freeze_as_current_default`
  현재 분기 기준으로는 support가 비교적 충분하고 true case metric으로도 읽을 수 있어, 현 시점 default conclusion으로 고정해 둘 수 있습니다.

이 audit은 detector/scorer를 바꾸지 않습니다. freeze 전에 현재 evaluation matrix를 얼마나 강하게 믿어도 되는지 operationally 정리해 주는 readout입니다.
