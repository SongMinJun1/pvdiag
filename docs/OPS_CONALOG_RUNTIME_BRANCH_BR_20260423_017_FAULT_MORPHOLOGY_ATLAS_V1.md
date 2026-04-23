<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_FAULT_MORPHOLOGY_ATLAS_V1

## [BR-20260423-017] Fault morphology atlas shadow
- `status`: morphology_atlas_shadow_generated
- `branch_type`: A
- `current_gate`: Gate 7
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23

## 1. 이슈 요약
- BR-016은 G1 long-gap one-day degradation backdating 후보 7건 중 strict-proximal support가 있는 6건만 `전조형 고장 -> 급작 고장`으로 좁게 적용했다.
- 다음 질문은 단일 G1 사례가 아니라, 고장 종류별로 어떤 episode 모양이면 전조로 신뢰하고 어떤 모양이면 보류/급작으로 둘지 기준을 세우는 것이다.
- BR-017은 그 기준을 코드에 넣지 않고, raw-only fault panel 145건 위에 fault-family morphology atlas와 threshold candidate shadow를 만든다.

## 2. Scope guard
- 코드와 production verdict는 수정하지 않는다.
- `production_write_allowed` 합계는 `0`이다.
- 모든 판단은 atlas/shadow 전용이며, 다음 BR에서 별도 코드 패치 전까지 운영 의미로 승격하지 않는다.
- 이 branch는 "임계치 확정"이 아니라 "임계치 후보와 반례 구조를 한 장에 모으는 기준판"이다.

## 3. Evidence inputs
- fresh tri-site raw-only run:
  - `/private/tmp/br017_tri_site_v1`
- raw-only audit:
  - `/private/tmp/br017_tri_site_v1/raw_only_chain_workspace/_share/panel_day_engine_runtime_fault_event_audit_v1.csv`
- branch base:
  - `origin/codex/final-delivery-runtime-lfs-base`
  - BR-016 merged base `f0f6157d`

## 4. Atlas output
- fault-family atlas rows: `6`
- threshold candidate rows: `6`
- episode shadow panel rows: `145`
- episode shadow summary rows: `8`
- automatic confirmed precursor candidates under v1 threshold: `0`

## 5. Fault-family morphology v1
| family | promote shape | hold/block shape |
|---|---|---|
| `열화·오염·음영 계열` | degradation/shadow 또는 low-mid 신호가 7~120일 gap 안에서 2~3일 이상 반복 | 1일 단독, 120일 초과 long-gap, 중간 대부분 정상, site/root 동시 흔들림 |
| `다이오드·서브스트링 계열` | 전압은 상대 유지되고 전류/출력이 반복 저하되는 국소 패턴 | site-wide 동시 발생 또는 1일 단독 |
| `접속 불량·부분 개방 계열` | 같은 패널에서 abrupt/open-like episode가 반복 | 전체 site 동시 흔들림, 측정 drift만 있는 경우 |
| `센서·계측 피드백 계열` | 계측 채널 불일치가 장비/센서 맥락과 반복 연결 | 패널 고장으로 바로 승격하지 않음 |
| `전력변환·외부계통 계열` | inverter/grid 공통 episode로 묶어 별도 관리 | 개별 패널 전조로 직접 승격하지 않음 |
| `strict trigger anchored sudden fault` | strict trigger 근처에만 final/fault-like가 집중 | 앞선 1일 단독 신호를 전조 onset으로 backdate하지 않음 |

## 6. Threshold candidates
- duration:
  - promote candidate: degradation/diode는 signal day `>=2`, open-connection은 recurrence `>=2`
  - hold/block: `1` day only
- gap:
  - promote candidate: `7 <= gap_days <= 120`
  - hold/block: onset promotion 기준 `>120`, 특히 one-day degradation
- continuity:
  - promote candidate: 중간 구간에 abnormal recurrence가 있음
  - hold/block: median mid_ratio가 1.0 근처이고 recurrence가 없음
- severity:
  - promote candidate: `mid_ratio < 0.6` 반복 `>=2` 또는 strict 근접 fault-like
  - hold/block: single low day 뒤 회복
- spatiality:
  - promote candidate: site/root 동시성이 낮음
  - hold/block: `site_event_A >= 20`, `subgroup_common_cause = 1`, 또는 `group_event_fraction >= 0.3`
- family-specific:
  - promote candidate: family별 VI shape가 맞음
  - hold/block: family pattern mismatch 또는 isolated event

## 7. Episode shadow summary
| episode_class_shadow | decision | family | panel_count |
|---|---|---|---:|
| `manual_review_episode` | `manual_review` | `개방/장치이상형` | 65 |
| `common_cause_episode_hold` | `block_individual_precursor` | `외부계통·공통원인 계열` | 42 |
| `manual_review_episode` | `manual_review` | `모듈손상형` | 14 |
| `intermittent_precursor_candidate` | `manual_review_candidate` | `접속 불량·부분 개방 계열` | 9 |
| `long_gap_one_day_episode_hold` | `block_precursor_backdating` | `열화·오염·음영 계열 후보 보류` | 6 |
| `sudden_fault_strict_anchor` | `no_precursor_promotion` | `strict trigger anchored sudden fault` | 5 |
| `manual_review_episode` | `manual_review` | `불충분` | 3 |
| `measurement_or_transient_episode` | `hold_episode_only` | `센서·계측 피드백 계열 후보` | 1 |

## 8. G1 correction carried into atlas
- BR-016 적용 후 6개 G1 row는 current output에서 `retrospective_onset_date`가 비어 있다.
- 따라서 BR-017 atlas에서는 G1 row의 episode basis를 current strict date가 아니라 `g1_suppressed_event_shadow_current_onset_date`로 잡는다.
- 이 보정 결과:
  - G1 shadow rows: `7`
  - G1 original episode-basis rows: `7`
  - BR-016 applied long-gap one-day holds: `6`
  - BR-016 hold-review common-cause hold: `1`
- 이 correction은 분석 기준만 고정하며, production semantics에는 쓰지 않는다.

## 9. Evidence outputs
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_FAULT_MORPHOLOGY_ATLAS_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_THRESHOLD_CANDIDATE_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_EPISODE_SHADOW_PANEL_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_EPISODE_SHADOW_SUMMARY_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_G1_LONGGAP_CASES_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_VALIDATION_V1.json`

## 10. Reproduction
- before command:
  - `git status -sb`
- analysis command:
  - `python release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/br017_tri_site_v1 --sites conalog,gangui,ktc_ess --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data`
- validation command:
  - `python -m py_compile pv_ae/panel_day_engine.py`

## 11. Decision
- BR-017 기준으로는 전조 자동승격 후보를 아직 만들지 않는다.
- 다음 패치 후보는 "family별 episode score를 shadow column으로만 추가"하는 것이다.
- 코드 패치 전에는 최소한 duration, gap, continuity, spatiality를 분리해 보고, family마다 임계치를 따로 조정한다.
