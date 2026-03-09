# PV Fault Early-Warning & Diagnosis — ONEPAGER (kernelog1)

> Report notice: 이 문서는 `kernelog1` 결과 요약 보고서다. 컬럼/라벨/출력 계약의 기준 문서는 `docs/DATA_DICTIONARY.md`이며, 현재 core engine 기준 파일은 `pv_ae/panel_day_engine.py`다.

## 한 줄 정의
- 본 시스템은 5분 V/I 기반으로 패널 상태를 계산해 **운영용 전조 shortlist(Top-N)** 와 **확정 진단 라벨(final/confirmed)** 을 분리 산출한다.

## 결과 해석 원칙
- 운영 출력은 `risk_day`, `transition_rank_day`, `transition_cp_rank_day`, `ae_rank` 같은 순위 비교용 점수다.
- 평가 표의 `onset_date`, leadtime, alert concentration, list diversity는 오프라인 비교 지표다.
- 정의와 컬럼 해석은 이 문서가 아니라 `docs/DATA_DICTIONARY.md`를 기준으로 본다.

## kernelog1 결과 요약(현재 확보 데이터 기준)

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
