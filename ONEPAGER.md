# PV Fault Early-Warning & Diagnosis — ONEPAGER (Conalog)

## 한 줄 정의
- 본 시스템은 5분 V/I 기반으로 패널 상태를 계산해 **운영용 전조 shortlist(Top-N)** 와 **확정 진단 라벨(final/confirmed)** 을 분리 산출한다.

## 출력 체계 분리 (운영 vs 평가)
- 운영 출력(실시간/준실시간): Top-N shortlist 생성용 점수/순위
  - 예: `risk_day`, `transition_rank_day`, `transition_cp_rank_day`, `ae_rank`
  - 목적: 점검 우선순위 결정
- 논문 평가 지표(오프라인 평가): leadtime/경보 집중도/리스트 다양성/event table
  - 예: onset 기준 리드타임, alert concentration(집중도), list diversity(다양성)
  - 목적: 모델 비교 및 보고

### 순위 비교 지표 공통 적용 원칙
- leadtime, 경보 집중도(alert concentration), 리스트 다양성(list diversity)은 **순위 비교 지표**다.
- 이 지표들은 특정 랭킹 하나에만 종속되지 않으며 `risk_day`, `level_drop`, `ae_rank`, `transition_rank_day` 등 어떤 순위에도 동일하게 적용한다.
- `transition`은 후보 순위 중 하나이며, 코어 진단/전조 헤드와 분리된 `postproc` 순위다.

## 컬럼 출처(Provenance) 레전드
| provenance | 의미 |
|---|---|
| `engine` | `pv_ae/panel_day_engine.py` 본 파이프라인이 직접 계산/출력 |
| `postproc` | risk/transition/ensemble 후처리 스크립트가 추가 계산 |
| `eval(manual)` | 운영 출력이 아닌 평가/라벨링 문맥에서 수동 또는 별도 평가 파이프라인이 정의 |

## 라벨/날짜 정의 SSOT (3분리)
| 구분 | 컬럼/개념 | 정의 | provenance |
|---|---|---|---|
| 현상 시작일 | `onset_date` | 고장 현상이 시작된 날짜. **시스템 기본 출력 컬럼이 아니라 평가용 라벨** | `eval(manual)` |
| 온라인 진단일 | `diagnosis_date_online` | 온라인 최초 확정일. Commit C에서 `min(dead_diag_date, critical_diag_date)`로 고정 | `engine` |
| 구간 라벨 | `retrospective_segment_label` | 사후적으로 구간 전체를 마킹하는 라벨 집합(`confirmed_fault`, `critical_fault`, `final_fault`) | `engine` |

### diagnosis_date_online 계산 규칙 (Commit C SSOT)
- `dead_diag_on_day = (state_dead_eff == True) and (dead_streak >= dead_days)`
- `dead_diag_date = panel_id별 dead_diag_on_day가 처음 True인 date`
- `critical_diag_on_day = (critical_like_eff == True) and (critical_streak >= critical_days)`
- `critical_diag_date = panel_id별 critical_diag_on_day가 처음 True인 date`
- `diagnosis_date_online = min(dead_diag_date, critical_diag_date)`

## confirmed_fault / final_fault 해석
- `confirmed_fault`는 dead 규칙 기반의 **segment 라벨**일 수 있다.
- 즉, `confirmed_fault=True` 구간의 모든 날짜가 동일하게 마킹될 수 있으며, 최초 확정 시점은 별도 컬럼(`dead_diag_date`)로 분리해 해석한다.
- `final_fault`는 최종 확정 라벨이며, `diagnosis_date_online`과 동일 개념이 아니다.

## critical 계층 SSOT
| 계층 | 대표 컬럼 | 설명 |
|---|---|---|
| raw evidence | `critical_like_raw`, `critical_like_suspect_raw` | `v_drop` 기반 hit 증거 (게이트 적용 전/기초 증거) |
| effective | `critical_like_eff` | trust(`v_ref_ok`) + gate(`data_bad`, `group_off`) 적용 후 운영 사용 라벨 |
| decision | `critical_confirmed`, `critical_suspect`, `final_fault` | 연속일/안정성 기준을 적용한 최종 의사결정 |

## rank_day 해석 주의
- `*_rank_day`는 **같은 날짜의 다른 패널과 비교한 횡단면 순위**다.
- 이는 시간축 미래 누수는 아니지만, panel-only strict online(패널 단독 과거만 사용) 지표와는 다르다.
- 따라서 운영/논문에서 `rank_day`는 "동일 날짜 내 상대 우선순위"로 명시한다.

## 핵심 컬럼(설명용 Core)
| canonical | 의미 |
|---|---|
| `midday_ratio` | 정오 출력비(패널/peer) |
| `level_drop` | 상태 저하량(1-midday_ratio) |
| `coverage_midday` | 정오 데이터 품질 |
| `peer_midday_frac` | 사이트가 살아있었는지(정오 peer 발전 수준) |
| `ae_rank` | 모양 이상(날짜 내 순위/분위) |
| `transition_rank` | 최근 변화(전이) 이상(날짜 내 순위/분위) |
| `transition_cp_rank` | 전이 + change-point 보강 순위 |
| `dead_streak` | dead 연속일수 |
| `final_fault` | 확정고장 플래그 |

## Conalog 결과 요약(현재 확보 데이터 기준)

### 사건 정의(onset vs diagnosis)
| panel_id | onset_date | diagnosis_date | delay_days |
|---|---:|---:|---:|
| 7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0 | 2025-12-18 | 2026-01-06 | 19 |
| c42997a6-5881-47e7-9035-7de8a2673b54.1.1 | 2025-03-20 | 2025-04-03 | 14 |

### 전조 리드타임(Top-K=20, onset 기준)
> 값 = onset보다 **몇 일 먼저** Top-K에 진입했는지 (빈칸=진입 못함)
| panel_id | onset | ae_rank | level_drop | risk_day | transition_cp | transition |
|---|---:|---:|---:|---:|---:|---:|
| 7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0 | 2025-12-18 | 98.0 | nan | nan | 98.0 | 98.0 |
| c42997a6-5881-47e7-9035-7de8a2673b54.1.1 | 2025-03-20 | 19.0 | 19.0 | 15.0 | nan | nan |

### 경보 집중도/리스트 다양성(보조 평가 지표)
- max_share_days: 1개 패널이 Top-K를 점령한 최대 비율(높을수록 고착)
- effective_panels: 회전/다양성(높을수록 좋음)
- 이 지표는 실제 인력/비용을 추정하는 것이 아니라, Top‑N 리스트가 특정 패널에 과도하게 고착되는지(반복 경보) 정도를 정량화한 보조 평가 지표다.
| ranker | max_share_days | effective_panels | top20_pick_share |
|---|---:|---:|---:|
| transition_rank_day | 0.1909385113268608 | 257.9486971674029 | 0.1427184466019417 |
| transition_cp_rank_day | 0.2131661442006269 | 260.3049139232088 | 0.141692789968652 |
| level_drop | 0.774294670846395 | 53.70710493260288 | 0.5186520376175549 |
