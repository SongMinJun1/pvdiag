<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_028_MISSING_SEED_SCAN_V1

## Purpose
- Search the current tri-site runtime artifacts for the two highest-priority missing seed families after BR-027:
  - `MLPE ambiguous`: rows closer to `장치 응답 이상형 / 제어응답형`
  - `common_cause_risk`: work/event/group-off direct-overlap rows
- Keep this branch docs-only.
- Record what was actually found and what still remains missing before any algorithm gating patch.

## Scope
- source scan roots:
  - `/private/tmp/conalog_mlpe_seed_expand_check`
  - `/private/tmp/conalog_counterexample_seed_check`
- checked artifacts:
  - `raw_only_chain_workspace/_share/panel_day_engine_runtime_cause_candidate_heuristics_v1.csv`
  - `result/live_chain/panel_day_engine_cause_candidate_heuristics_v1.csv`
  - `result/fault_panel_result_current_v1.csv`
  - `result/fault_panel_result_precursor_report_v1.csv`
  - `sites/*/output/ae_simple_local_precursor_gate_daily.csv`
  - `sites/*/output/ae_simple_fault_candidates.csv`

## Findings
### 1. MLPE ambiguous: `제어응답형 top1`은 현재 tri-site scan에서 미관측
- `raw_only_chain_workspace/_share/panel_day_engine_runtime_cause_candidate_heuristics_v1.csv` 기준:
  - `원인후보_top1_ko` 분포는 `센서·피드백형 87`, `열화형 25`, `다이오드·서브스트링형 18`, `원인미확정 12`, `접속·부분개방형 3`
  - `제어응답형 top1` 행 수: `0`
- 따라서 `장치 응답 이상형/제어응답형 top1` seed는 여전히 추가 수집 필요 상태다.

### 2. MLPE ambiguous shortlist: live-chain에서 `장치 응답 이상형` 관련 4건 확보
- 아래 4건은 `GPVS_외부참조패턴_ko=장치 응답 이상형`이면서 panel-local 후보와 경합한다.

| site | panel_id | 사건유형_ko | 최종고장양상_ko | top1 | top2 | top3 | 신뢰도 |
|---|---|---|---|---|---|---|---|
| `conalog` | `c42997a6-5881-47e7-9035-7de8a2673b54.1.1` | `전조형 고장` | `급격 종료` | `센서·피드백형` | `접속·부분개방형` | `제어응답형` | `medium` |
| `gangui` | `bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7` | `급작 고장` | `급작 발생` | `다이오드·서브스트링형` | `센서·피드백형` | `접속·부분개방형` | `low` |
| `gangui` | `bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16` | `급작 고장` | `급작 발생` | `다이오드·서브스트링형` | `센서·피드백형` | `접속·부분개방형` | `low` |
| `ktc_ess` | `70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4` | `전조형 고장` | `진행성 악화` | `열화형` | `센서·피드백형` | `다이오드·서브스트링형` | `low` |

### 3. report-row direct overlap: current/precursor row 날짜 기준 `site_event/group_off` 직접 중첩은 미관측
- 아래 조인을 직접 확인했다.
  - precursor report `전조날짜` vs `ae_simple_local_precursor_gate_daily.csv`
  - current report `전조날짜` vs same gate daily
  - current report `고장날짜` vs same gate daily
- 결과:
  - `precursor@onset true hits = 0`
  - `current@onset true hits = 0`
  - `current@fault true hits = 0`
- 따라서 `official current와 동시에 엮이는 common-cause direct overlap`은 이번 tri-site scan에서도 여전히 미관측이다.

### 4. common-cause raw-daily shortlist는 확보됨
#### 4.1 precursor + `group_off` direct overlap shortlist
- `gangui`에서 `group_off_date=true` 이면서 precursor bundle 신호가 강한 raw-daily 후보를 확보했다.
- 대표 예시는 아래와 같다.

| site | panel_id | date | signal_count | note |
|---|---|---|---:|---|
| `gangui` | `4fd0c566-e25e-4d51-96ca-57cc46940593.3.6` | `2025-11-23` | `8` | `pre_ews + prefault_B + prefault_cond_mid/ae/dtw/ews` 동시 존재 |
| `gangui` | `bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7` | `2025-11-23` | `8` | 동일 날짜 `group_off` 중첩, precursor helper 다수 존재 |
| `gangui` | `bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.8` | `2025-12-04` | `8` | 강한 precursor bundle + group hold 동시 존재 |
| `gangui` | `4fd0c566-e25e-4d51-96ca-57cc46940593.4.15` | `2025-11-23` | `6` | 이미 MLPE ambiguous seed set과도 연결 가능한 패널 |

#### 4.2 hard-like + `site_event_reason=co_drop_surge` shortlist
- `ktc_ess`에서 `2025-10-26` 하루에 `site_event_soft=true`, `site_event_reason=co_drop_surge`, `fault_like_day=true`가 동시에 뜬 `20`개 row를 확보했다.
- 모두 `critical_fault=0`, `critical_confirmed=0`, `final_fault=0` 이고, 즉 hard-like 흔적은 있으나 confirm path는 아니다.
- 대표 예시는 아래와 같다.

| site | panel_id | date | reason | anom_subtype | mid_v_ratio | mid_i_ratio |
|---|---|---|---|---|---:|---:|
| `ktc_ess` | `10305b40-b67e-40d1-9cd1-271b6642a3d9.1.12` | `2025-10-26` | `co_drop_surge` | `fault_like_weak` | `1.089995` | `0.000000` |
| `ktc_ess` | `10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12` | `2025-10-26` | `co_drop_surge` | `fault_like_weak` | `1.079213` | `0.000000` |
| `ktc_ess` | `ed5e3367-fbd4-4c8c-be33-c5d1c5e191b7.0.14` | `2025-10-26` | `co_drop_surge` | `fault_like_strong` | `1.158757` | `0.000468` |
| `ktc_ess` | `ed5e3367-fbd4-4c8c-be33-c5d1c5e191b7.0.15` | `2025-10-26` | `co_drop_surge` | `fault_like_strong` | `1.092913` | `0.000000` |

## Decision
- BR-028 is useful because it narrows the next evidence task:
  - `장치 응답 이상형/제어응답형 top1`은 아직 0건이므로 계속 추가 수집 필요
  - 반면 `group_off` 및 `site_event co_drop_surge` raw-daily overlap 후보는 실제 seed source로 사용할 수 있다
- 다음 안전 작업은 code patch가 아니라 아래 둘 중 하나다.
  1. BR-028 shortlist를 curated `counterexample set` 정식 seed로 승격할 기준을 잠그기
  2. `score-to-projection decision log`를 만들어 BR-026/027/028 findings를 하나의 gate로 묶기
