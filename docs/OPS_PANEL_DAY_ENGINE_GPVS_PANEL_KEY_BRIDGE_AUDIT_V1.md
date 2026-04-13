# OPS_PANEL_DAY_ENGINE_GPVS_PANEL_KEY_BRIDGE_AUDIT_V1

## 목적
- 현재 panel multiaxis 본표에서 GPVS 가 `미부착` 인 panel 들에 대해 alternate key bridge 가 안전한지 확인한다.
- detector logic 은 바꾸지 않고, stored artifact 기준으로만 key bridge 가능 여부를 감사한다.
- 이 단계의 질문은 하나다.
  - exact `(site, panel_id)` 밖으로 나가도 되는가, 아니면 exact-match-only 를 유지해야 하는가.
- 단, 여기서 GPVS 는 모든 visible panel 에 대한 일반 참고축이 아니다.
- 현재 프로젝트에서 GPVS 는 `fault-family reference axis` 이고 `고장 패널` 에만 적용한다.

## 입력
- `_share/panel_day_engine_panel_multiaxis_verdict_v1.csv`
- `_share/panel_day_engine_gpvs_panel_attach_candidates_v1.csv`
- `_share/panel_day_engine_gpvs_panel_attach_inventory_v1.csv`
- `_share/gpvs_fault_family_eval_cases.csv`

## 왜 이 audit 이 필요한가
- 현재 panel multiaxis 본표는 exact `(site, panel_id)` 로 겹치는 panel 에만 GPVS reference 를 붙였다.
- 하지만 이 감사의 base universe 는 `GPVS_적용대상_ko = 적용대상` 이면서 `GPVS_부착상태_ko = 미부착` 인 `fault panel` 뿐이다.
- 비고장 / 공통원인 이벤트 / 반복 이상 / 불충분 panel 은 GPVS target 이 아니므로 bridge 대상에 넣지 않는다.
- 남은 panel 에 대해 suffix 일부만 잘라서 bridge 하면 더 붙일 수 있을 수 있다.
- 하지만 이런 prefix bridge 는 위험하다.
  - 같은 parent UUID 아래 suffix 가 다른 panel 이 서로 다른 GPVS type 을 가질 수 있다.
  - 같은 두 단계 prefix 아래에서도 panel 별 suffix 가 다른 사건일 수 있다.
  - site-only 는 특히 더 위험하다. 같은 site 의 여러 panel/type 을 한 번에 섞어 버릴 수 있다.

## 시험하는 규칙
- `exact_full_key`
  - baseline 확인용이다.
  - 현재 미부착 panel 에서는 원칙적으로 계속 unmatched 여야 한다.
- `site_plus_parent_uuid`
  - 첫 점(`.`) 앞 UUID 까지만 남겨 본다.
- `site_plus_two_level_prefix`
  - 마지막 점 앞 prefix 까지만 남겨 본다.
- `site_only_not_allowed`
  - negative control 이다.
  - 결과를 보더라도 추천하지 않는다.

## 안전성 기준
- `GPVS_적용대상_ko = 적용대상` 인 미부착 fault panel 쪽에서는 다음 둘을 동시에 만족해야 bridge 후보로 본다.
  - `unique_attachable_flag == 1`
  - `conflict_flag == 0`
- 하지만 이것만으로는 부족하다.
- 이미 exact-match 로 붙어 있는 12개 panel 에도 같은 rule 을 거꾸로 적용한다.
- 그 결과가 현재 attached GPVS type 과 모순되면 그 rule 은 unsafe 로 본다.

## 출력
- `_share/panel_day_engine_gpvs_panel_key_bridge_candidates_v1.csv`
  - 미부착 panel x rule 조합 전체 후보표
  - 각 row 에 대해:
    - 몇 개 GPVS row 와 맞는지
    - type 이 하나인지 여러 개인지
    - conflict 가 있는지
    - bridge reason 이 무엇인지
- `_share/panel_day_engine_gpvs_panel_key_bridge_summary_v1.csv`
  - rule 별 요약
  - `unique_attachable_count`, `conflict_count`, `contradiction_on_matched_count`, `safe_attachable_count` 를 같이 본다.
- `_share/panel_day_engine_gpvs_panel_key_bridge_recommendation_v1.csv`
  - 최종 권고 한 줄
  - `use_safe_bridge_rule` 또는 `keep_exact_match_only`

## 해석
- `use_safe_bridge_rule`
  - 일부 `fault panel` 미부착 row 는 stored artifact 만으로도 안전하게 1:1 GPVS bridge 가 가능하다는 뜻이다.
- `keep_exact_match_only`
  - 남은 `fault panel` 들은 exact key 밖으로 나가면 충돌하거나, 이미 붙은 panel type 과 모순된다는 뜻이다.
  - 이 경우 나머지 fault panel 은 계속 `미부착` 으로 두는 것이 맞다.
  - 비고장/non-fault row 는 애초에 GPVS target 이 아니므로 여기서 다루지 않는다.

## Smoke Test 기준
- script compile
- candidate rows emit
- GPVS 비대상 row 는 bridge audit base 에서 제외
- unmatched panel conflict detection works
- already matched panel contradiction detection works
- recommendation row emit
- official outputs unchanged
