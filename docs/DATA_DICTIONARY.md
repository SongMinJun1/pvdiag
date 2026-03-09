# Data Dictionary (Canonical SSOT)

본 문서는 논문/발표/운영 문맥에서 혼동이 잦은 라벨, 날짜, 순위 해석, 출력 계약을 하나의 기준 문서로 고정한다.
현재 core engine 기준 파일은 `pv_ae/panel_day_engine.py`이며, 공식 출력 계약은 `panel_day_*` 5개 파일을 따른다.

## 1) Provenance 레전드
| provenance | 의미 |
|---|---|
| `engine` | `pv_ae/panel_day_engine.py`에서 직접 계산되어 `panel_day_core.csv`에 출력 |
| `postproc` | `risk_score.py`, `add_transition_scores.py`, `add_ensemble_scores.py`에서 후처리로 추가 |
| `eval(manual)` | 시스템 기본 출력이 아닌 평가 라벨, 수동 정답, 실험 표 생성용 정의 |

## 2) 라벨/날짜 정의
| 컬럼/개념 | 정의 | provenance | 비고 |
|---|---|---|---|
| `onset_date` | 고장 현상 시작일 | `eval(manual)` | 시스템 출력 컬럼이 아닌 평가용 라벨 |
| `dead_diag_on_day` | 해당일 dead 온라인 진단 조건 충족 여부 | `engine` | daily online decision flag |
| `dead_diag_date` | panel별 `dead_diag_on_day` 최초 True 날짜 | `engine` | 최초 dead 진단일 |
| `critical_diag_on_day` | 해당일 critical 온라인 진단 조건 충족 여부 | `engine` | p2에서만 의미 있음 |
| `critical_diag_date` | panel별 `critical_diag_on_day` 최초 True 날짜 | `engine` | 최초 critical 진단일 |
| `diagnosis_date_online` | 온라인 최초 확정일 | `engine` | `min(dead_diag_date, critical_diag_date)` |
| `retrospective_segment_label` | 구간 전체 사후 마킹 라벨 | `engine` | `confirmed_fault`, `critical_fault`, `final_fault` |

관계 요약:
- `onset_date`는 평가 기준점이며, 엔진이 생성하는 기본 출력이 아니다.
- `diagnosis_date_online`은 온라인 규칙이 처음 충족된 날짜다.
- `retrospective labels`는 사후적으로 구간 전체를 채우는 라벨이며, 최초 진단 시점과 동일하지 않을 수 있다.
- 따라서 발표/논문에서는 `onset_date`, `diagnosis_date_online`, `confirmed_fault/final_fault`를 서로 다른 층위로 구분해 써야 한다.

## 3) confirmed_fault / final_fault 해석
| 컬럼 | 정의 | provenance | 해석 주의 |
|---|---|---|---|
| `confirmed_fault` | dead 규칙 기반 확정 라벨 | `engine` | 구간 전체가 마킹될 수 있으며 최초 진단 시점과 동일하지 않을 수 있음 |
| `final_fault` | 최종 확정 라벨 | `engine` | online 최초 확정일은 `diagnosis_date_online`으로 별도 관리 |

해석 규칙:
- `confirmed_fault=True`가 곧 그 날 처음 진단되었다는 뜻은 아니다.
- 최초 dead 확정 시점은 `dead_diag_date`로 본다.
- 최종 온라인 확정 시점은 `diagnosis_date_online`으로 본다.
- `final_fault`는 보고/세그먼트 마킹용 최종 상태이며, retrospective 성격이 섞일 수 있다.

## 4) critical 계층 raw / effective / decision
| 계층 | 컬럼 | 정의 | provenance |
|---|---|---|---|
| raw evidence | `critical_like_raw` | vdrop hit 기초 증거 | `engine` |
| raw evidence | `critical_like_suspect_raw` | suspect 축 기초 증거 | `engine` |
| effective | `critical_like_eff` | trust/gate 반영 후 운영 사용 라벨 | `engine` |
| decision | `critical_confirmed` | 연속일/안정성 기준 충족 | `engine` |
| decision | `critical_suspect` | evidence는 있으나 confirmed 미충족 | `engine` |
| decision | `final_fault` | 최종 확정 라벨 | `engine` |

## 5) rank_day / 횡단면 비교 해석
| 컬럼 예시 | 정의 | provenance | 주의 |
|---|---|---|---|
| `ae_rank`, `recon_rank_day` | 동일 날짜 내 AE 상대 순위 | `engine`/`postproc` | panel-only strict online 아님 |
| `dtw_rank_day`, `hs_rank_day` | 동일 날짜 내 DTW/HS 상대 순위 | `engine` | 횡단면 비교 |
| `transition_rank_day`, `transition_cp_rank_day` | 동일 날짜 내 전이 상대 순위 | `postproc` | 시간 누수는 아니나 횡단면 의존 |

운영/평가 해석:
- `rank_day` 계열은 미래 날짜를 보지 않는다는 뜻이지, 패널 단독 시계열만 쓴다는 뜻은 아니다.
- 같은 날짜 다른 패널과의 비교가 포함되므로 "횡단면 비교 순위"라고 적는 것이 안전하다.
- `risk_day`, `transition_rank_day`, `transition_cp_rank_day`, `ae_rank`는 진단 라벨이 아니라 우선순위 비교용 점수/순위다.

## 6) 운영 출력 vs 평가 지표 구분
- 운영 출력(Top-N shortlist): `risk_day`, `transition_rank_day`, `transition_cp_rank_day`, `ae_rank`
- 논문 평가 지표: `onset_date` 기준 리드타임 표, alert concentration, list diversity, event table
- 원칙: 운영 점수와 평가 라벨(`onset_date`)을 같은 의미로 혼용하지 않는다.
- leadtime, alert concentration, list diversity는 특정 모델 전용이 아닌 순위 비교 지표다.
- `transition`은 후보 순위 중 하나이며, 코어 진단/전조 헤드와 분리된 `postproc` 계층의 순위다.

## 7) 현재 공식 출력 파일명 계약
| 단계 | 파일명 | 역할 |
|---|---|---|
| core engine | `panel_day_core.csv` | 패널-일 단위 core 엔진 출력 |
| diagnosis summary | `panel_diagnosis_summary.csv` | 패널별 최초 온라인 진단 요약 |
| risk postproc | `panel_day_risk.csv` | risk score와 rolling/change-point 추가 |
| transition postproc | `panel_day_risk_transition.csv` | transition 계열 순위 추가 |
| ensemble postproc | `panel_day_risk_ensemble.csv` | ensemble 계열 순위 추가 |

## 8) 컬럼 패밀리 요약
| 패밀리 | 대표 컬럼 | 설명 |
|---|---|---|
| 식별자 | `date`, `panel_id`, `source_csv` | 패널-일 관측 단위 식별 |
| 품질/게이트 | `coverage`, `coverage_mid`, `data_bad`, `n_ref`, `n_total` | 데이터 품질과 신뢰도 게이트 |
| 레벨/요약 | `mid_ratio`, `last_ratio`, `min_ratio`, `p10_ratio`, `p50_ratio`, `low_area` | 레벨 저하와 분포 요약 |
| 이벤트 구조 | `drop_time`, `sustain_mins`, `recovered_any`, `recovered_sustained`, `re_drop`, `co_drop_frac`, `seg_count`, `total_low_mins` | 저하 세그먼트의 시간 구조 |
| shape | `recon_error`, `recon_rank_day`, `ae_strength`, `dtw_dist`, `dtw_rank_day`, `dtw_strength` | 형상 이탈 관련 축 |
| turbulence | `hs_score`, `hs_rank_day`, `hs_strength` | 난류/불안정 관련 축 |
| rule state | `state_dead`, `state_dead_eff`, `dead_streak`, `confirmed_fault`, `final_fault` | dead/confirmed 기반 규칙 상태 |
| vdrop / critical | `mid_v_ratio`, `v_ref`, `v_ref_ok`, `v_drop`, `critical_like_raw`, `critical_like_eff` | 전기축 critical 판단 계층 |
| EWS / prefault | `ews_*`, `ews_warning`, `prefault_B` | 조기경보 및 전조 엔진 |
| postproc rank | `risk_day`, `risk_7d_mean`, `cp_score`, `transition_rank_day`, `transition_cp_rank_day`, `risk_ens` | 후처리 비교용 점수와 순위 |

## 9) alias 정책 초안
- canonical 출력 이름은 파일 단위에서만 고정한다: `panel_day_core`, `panel_diagnosis_summary`, `panel_day_risk`, `panel_day_risk_transition`, `panel_day_risk_ensemble`
- 컬럼 alias는 문서 설명용 별칭과 실제 컬럼명을 구분한다.
- 코드와 CSV 헤더의 SSOT는 실제 컬럼명을 우선한다.
- 발표/논문용 표에서는 설명 alias를 병기할 수 있으나, 원본 CSV 컬럼명을 덮어쓰지 않는다.
- 더 이상 구 파일명(`ae_simple_*`, `scores_with_risk*`)은 canonical alias로 유지하지 않는다.
