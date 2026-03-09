# data_dictionary_paper (Commit A SSOT)

> Legacy archive 문서. 현재 canonical 문서는 아니며, 최신 기준은 `docs/DATA_DICTIONARY.md`를 따른다.

본 문서는 논문/발표/운영 문맥에서 혼동이 잦은 라벨·날짜·rank 해석을 우선 고정한다.

## 1) Provenance 레전드
| provenance | 의미 |
|---|---|
| `engine` | `pv_ae/pv_autoencoder_dayAE.py`에서 직접 계산되어 `panel_day_core.csv`에 출력 |
| `postproc` | `risk_score.py`, `add_transition_rankers.py`, `add_ensemble_rankers.py`에서 후처리로 추가 |
| `eval(manual)` | 시스템 기본 출력이 아닌 평가 라벨/수동 정답/실험 표 생성용 정의 |

## 2) 라벨/날짜 정의 (3분리)
| 컬럼/개념 | 정의 | provenance | 비고 |
|---|---|---|---|
| `onset_date` | 고장 현상 시작일 | `eval(manual)` | **시스템 출력 컬럼 아님** |
| `dead_diag_on_day` | 해당일 dead 온라인 진단 조건 충족 여부 | `engine` | Commit C에서 추가 예정 |
| `dead_diag_date` | panel별 `dead_diag_on_day` 최초 True 날짜 | `engine` | Commit C에서 추가 예정 |
| `critical_diag_on_day` | 해당일 critical 온라인 진단 조건 충족 여부 | `engine` | p2 + Commit C에서 추가 예정 |
| `critical_diag_date` | panel별 `critical_diag_on_day` 최초 True 날짜 | `engine` | p2 + Commit C에서 추가 예정 |
| `diagnosis_date_online` | 온라인 최초 확정일 | `engine` | `min(dead_diag_date, critical_diag_date)` |
| `retrospective_segment_label` | 구간 전체 사후 마킹 라벨 | `engine` | `confirmed_fault`, `critical_fault`, `final_fault` |

## 3) confirmed/final 해석 고정
| 컬럼 | 정의 | provenance | 해석 주의 |
|---|---|---|---|
| `confirmed_fault` | dead 규칙 기반 확정 라벨(구간 마킹 가능) | `engine` | 최초 진단 시점과 동일하지 않을 수 있음 |
| `final_fault` | 최종 확정 라벨 | `engine` | online 최초 확정일은 `diagnosis_date_online`로 별도 관리 |

## 4) critical SSOT (raw → effective → decision)
| 계층 | 컬럼 | 정의 | provenance |
|---|---|---|---|
| raw evidence | `critical_like_raw` | vdrop hit 기초 증거 | `engine` |
| raw evidence | `critical_like_suspect_raw` | suspect 축 기초 증거 | `engine` |
| effective | `critical_like_eff` | trust/gate 반영 후 운영 사용 | `engine` |
| decision | `critical_confirmed` | 연속일/안정성 기준 충족 | `engine` |
| decision | `critical_suspect` | evidence는 있으나 confirmed 미충족 | `engine` |
| decision | `final_fault` | 최종 확정 라벨 | `engine` |

## 5) rank_day/횡단면 비교 해석
| 컬럼 예시 | 정의 | provenance | 주의 |
|---|---|---|---|
| `ae_rank`, `recon_rank_day` | 동일 날짜 내 AE 상대 순위 | `engine`/`postproc` | panel-only strict online 아님 |
| `dtw_rank_day`, `hs_rank_day` | 동일 날짜 내 DTW/HS 상대 순위 | `engine` | 횡단면 비교 |
| `transition_rank_day`, `transition_cp_rank_day` | 동일 날짜 내 전이 상대 순위 | `postproc` | 시간 누수는 아니나 횡단면 의존 |

## 6) 운영 출력 vs 논문 평가 지표 구분
- 운영 출력(Top-N shortlist): `risk_day`, `transition_rank_day`, `transition_cp_rank_day`, `ae_rank`
- 논문 평가 지표(leadtime/경보 집중도/리스트 다양성): `onset_date` 기준 리드타임 표 + Top-N 리스트의 집중/다양성 비교 표
- 원칙: 운영 점수와 평가 라벨(`onset_date`)을 같은 의미로 혼용하지 않는다.
- 이 지표는 실제 인력/비용을 추정하는 것이 아니라, Top‑N 리스트가 특정 패널에 과도하게 고착되는지(반복 경보) 정도를 정량화한 보조 평가 지표다.

## 7) 순위 비교 프레임 고정
- leadtime, 경보 집중도(alert concentration), 리스트 다양성(list diversity)은 특정 모델 전용이 아닌 **순위 비교 지표**다.
- 따라서 `risk_day`, `level_drop`, `ae_rank`, `transition_rank_day` 등 어떤 순위 열에도 동일한 평가 방식으로 적용한다.
- `transition`은 후보 순위 중 하나이며, 코어 진단/전조 헤드와 분리된 `postproc` 계층의 순위다.
