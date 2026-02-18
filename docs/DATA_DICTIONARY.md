# Data Dictionary (SSOT)
각 컬럼의 정의/의도/해석/주의사항을 여기에 적는다.

## 컬럼 패밀리
1) 식별자: date, panel_id, source_csv
2) 품질/게이트: coverage, coverage_mid, data_bad
3) 레벨/요약: mid_ratio, last_ratio, min/p10/p50, low_area
4) 이벤트 구조: drop_time, sustain_mins, recovered_any/sustained, re_drop, co_drop_frac, seg_count, total_low_mins
5) shape: recon_error + rank/strength, dtw_dist + rank/strength
6) turbulence: hs_score + rank/strength
7) 룰 상태: state_dead, dead_streak, confirmed_fault/final_fault
8) vdrop: mid_v_ratio, v_ref, v_drop, v_ref_ok, critical_like/suspect
9) 전조: ews_* / prefault_B_*

(추가) alias 정책: mid_ratio -> mid_power_ratio, recon_error -> ae_recon_mse 등
