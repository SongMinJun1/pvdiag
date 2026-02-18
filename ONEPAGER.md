# PV Fault Early-Warning & Diagnosis — ONEPAGER (kernelog1)

## 한 줄 정의
- 본 시스템은 5분 V/I로부터 DC power를 만들고, peer(동료 패널 중앙값) 대비 ratio로 정규화한 뒤,
  (1) 상태(Severity), (2) 형태(Shape: AE/DTW), (3) 난류(Turbulence: HS), (4) 전이(Transition) 신호를 생성하여
  **전조(Top‑K 우선순위)** 와 **확정진단(final_fault)** 을 분리 산출한다.

## 출력(Two-head)
- **전조/예측 헤드**: transition_rank(변화), AE rank(모양) 등을 이용해 *점검 우선순위 Top‑K*를 만든다.
- **진단/확정 헤드**: state_dead → dead_streak → final_fault 로 보수적으로 확정고장을 판정한다.

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

## kernelog1 결과 요약(현재 확보 데이터 기준)

### 사건 정의(onset vs diagnosis)
| panel_id | onset_date | diagnosis_date | delay_days |
|---|---:|---:|---:|
| 7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0 | 2025-12-18 | 2026-01-06 | 19 |
| c42997a6-5881-47e7-9035-7de8a2673b54.1.1 | 2025-03-20 | 2025-04-03 | 14 |

### 전조 리드타임(Top‑K=20, onset 기준)
> 값 = onset보다 **몇 일 먼저** Top‑K에 진입했는지 (빈칸=진입 못함)
| panel_id | onset | ae_rank | level_drop | risk_day | transition_cp | transition |
|---|---:|---:|---:|---:|---:|---:|
| 7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0 | 2025-12-18 | 98.0 | nan | nan | 98.0 | 98.0 |
| c42997a6-5881-47e7-9035-7de8a2673b54.1.1 | 2025-03-20 | 19.0 | 19.0 | 15.0 | nan | nan |

### Workload/회전성(오경보 부담 대체 지표)
- max_share_days: 1개 패널이 Top‑K를 점령한 최대 비율(높을수록 고착)
- effective_panels: 회전/다양성(높을수록 좋음)
| ranker | max_share_days | effective_panels | top20_pick_share |
|---|---:|---:|---:|
| transition_rank_day | 0.1909385113268608 | 257.9486971674029 | 0.1427184466019417 |
| transition_cp_rank_day | 0.2131661442006269 | 260.3049139232088 | 0.141692789968652 |
| level_drop | 0.774294670846395 | 53.70710493260288 | 0.5186520376175549 |

## 60초 설명 스크립트(그대로 읽기)
1) 5분 V/I로 P를 만들고, 같은 시각 peer 중앙값으로 나눠 ratio로 정규화한다(날씨 영향 감소).
2) 정오(midday) 구간 ratio 평균으로 상태(Severity)를 만들고, coverage로 품질을 게이트한다.
3) 하루 ratio 곡선(96포인트)에서 AE/DTW/HS로 형태/난류 이상을 점수화한다.
4) 패널 자기 과거 대비 변화(transition)로 ‘최근에 새로 나빠짐’을 전조로 잡아 Top‑K 우선순위를 만든다.
5) 확정고장은 state_dead가 dead_streak로 누적될 때만 보수적으로 final_fault로 확정한다.
