# pvdiag Research Roadmap (SSOT)

이 문서는 “우리가 앞으로 할 일 전부”를 잊지 않기 위한 단일 진실(SSOT)이다.

## Done (이미 확정/완료된 SSOT)
- [x] date/ID SSOT: 파일명 내 YYYY-MM-DD 추출 + panel_id 문자열 통일
- [x] peer baseline 인덱싱 안전화: DF는 원본 라벨, dict key만 str(pid)
- [x] V-drop/critical_like SSOT: post-merge에서만 최종 확정
- [x] peerV fallback 단위 오류 제거(전압은 전압으로)
- [x] no-drop 분기 feature 버그 수정(min/p10/p50/low_area)

## Phase 0: Research Preflight (필수)
- [ ] fault_events.csv 구축(panel_id, onset_date, source, notes)
- [ ] censoring 규칙 정의(고장없음/관측종료)
- [ ] leakage audit 문서화(rolling 과거만, 결과컬럼 제외, 시간 split)
- [ ] 평가 지표 고정
  - Detection: event-based precision/recall, false alarm rate
  - Prognostics: horizon PR-AUC(7/14/30), lead time, calibration, Top-K

## Phase 1: 설명 가능한 출력/문서
- [ ] output 3단 분리: debug / analysis / ops
- [ ] DATA_DICTIONARY.md 작성(정의/의도/해석/주의)
- [ ] 컬럼 alias 정책 확정(mid_ratio->mid_power_ratio 등)

## Phase 2: Baseline & Ablation
- [ ] BL-1: mid_ratio+dead_streak 룰만
- [ ] BL-2: AE-only / DTW-only / HS-only
- [ ] BL-3: supervised baseline(로지스틱/트리)
- [ ] Ablation: -AE/-DTW/-HS/-event/-vdrop/-peer/-EWS/-TemplateB

## Phase 3: EWS 강화(필터 -> 연속 스코어/피처)
- [ ] ews_warning 유지 + ews_score(연속값) 추가
- [ ] 개인 기준선 Δ 기반 지표 포함
- [ ] clear-day / data_bad gating 강화
- [ ] co_drop_frac 포함

## Phase 4: Prognostics
- [ ] risk_day/risk_7d/risk_30d/risk_level 설계(설명 가능한 가중합 v1)
- [ ] Discrete-time hazard: P(fail within H days), H=7/14/30
- [ ] 평가: PR-AUC + lead time + calibration + Top-K

## Phase 5: Generalization / Robustness
- [ ] site hold-out
- [ ] season split
- [ ] coverage/threshold sensitivity sweep

## Phase 6: Paper packaging
- [ ] Fig1 pipeline, Fig2 event, Fig3 vdrop SSOT
- [ ] 성능표 + lead time + calibration + Top-K
