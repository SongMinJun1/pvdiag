# runtime_chain_dependency_audit_v1

## 목적
현재 conalog full runtime pack이 어디까지 live이고, full-chain runtime으로 가려면 어떤 blocker가 남는지 고정 설명으로 남긴다.

## 현재 상태
- `runtime_live_full_chain_ready_flag`: `False`
- `current_pack_mode_ko`: `engine_live_plus_fixed_fault_artifacts`

## Hard Cycle
- verdict node: `build_panel_day_engine_panel_multiaxis_verdict_v1.py`
- fault-event-audit node: `build_panel_day_engine_fault_panel_event_audit_v1.py`
- impact: 현재 구조 그대로는 verdict와 fault_event_audit가 서로를 선행 입력으로 요구하므로, integrated snapshot 없이 단방향 live runtime chain을 바로 만들 수 없다.

### verdict가 직접 요구하는 fault_event_audit 축
- `panel_day_engine_fault_panel_event_audit_v1.csv`
- `사건유형_재판정_ko`
- `최종고장양상_재판정_ko`
- `재판정_근거_ko`

### fault_event_audit가 다시 요구하는 verdict 축
- `panel_day_engine_panel_multiaxis_verdict_v1.csv`
- `패널고장여부_ko`
- `사건유형_ko`
- `최종고장양상_ko`
- `전조흔적_flag`
- `순수급작_flag`
- `전조평가셋편입_flag`
- `급작평가셋편입_flag`

## Runtime에 필요한 레이어
- `pv_ae/panel_day_engine.py`
- `build_panel_day_engine_panel_multiaxis_verdict_v1.py`
- `build_panel_day_engine_gpvs_evidence_pack_v1.py`
- `build_panel_day_engine_cause_candidate_heuristics_v1.py`

## verdict 필수 share 입력
- `panel_day_engine_operator_workflow_default_v1.csv`
- `panel_day_engine_abrupt6_symptom_map_v1.csv`
- `panel_day_engine_kernellog_project_mapping_v1.csv`
- `panel_day_engine_gpv7_perf_summary_v1.csv`
- `panel_day_engine_project_final_decision_pack_v1.csv`
- `panel_day_engine_precursor_onset_truth_v1.csv`
- `panel_day_engine_non_precursor_performance_cases_v1.csv`
- `panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv`
- `panel_day_engine_gpvs_panel_attach_inventory_v1.csv`
- `panel_day_engine_gpvs_panel_attach_feasibility_v1.csv`
- `panel_day_engine_gpvs_panel_attach_candidates_v1.csv`
- `panel_day_engine_precursor_abrupt_consistency_cases_v1.csv`
- `panel_day_engine_precursor_abrupt_consistency_summary_v1.csv`
- `panel_day_engine_precursor_abrupt_consistency_recommendation_v1.csv`
- `panel_day_engine_c42997_1_1_forensic_summary_v1.csv`
- `panel_day_engine_fault_panel_event_audit_v1.csv`
- `panel_day_engine_detailed_fault_bridge_audit_v1.csv`
- `panel_day_engine_detailed_fault_bridge_summary_v1.csv`
- `panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv`
- `panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv`
- `panel_day_engine_gpvs_detailed_type_realpanel_sanity_v1.csv`
- `panel_day_engine_gpvs_mlpe_panel_agreement_v1.csv`
- `panel_day_engine_gpvs_canonical_dictionary_v1.csv`
- `panel_day_engine_gpvs_mlpe_fault_matching_table_v1.csv`
- `panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv`

## GPVS evidence 필수 입력
- `panel_day_engine_panel_multiaxis_verdict_v1.csv`
- `panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv`
- `panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv`
- `panel_day_engine_gpvs_mlpe_fault_matching_table_v1.csv`
- `panel_day_engine_gpvs_mlpe_fault_matching_summary_v1.csv`

## heuristic 필수 입력
- `panel_day_engine_gpvs_evidence_pack_v1.csv`
- `panel_day_engine_panel_multiaxis_verdict_v1.csv`

## fault_event_audit 필수 입력
- `panel_day_engine_panel_multiaxis_verdict_v1.csv`
- `panel_day_engine_abrupt6_symptom_map_v1.csv`
- `panel_day_engine_precursor_onset_truth_v1.csv`
- `panel_date_reaudit_working.csv`
- `vendor_reply_adjudication_latest.csv (optional)`
- `data/<site>/out/panel_day_core.csv`
- `data/<site>/out/ae_simple_local_precursor_gate_daily.csv`

## 권장 다음 단계
- runtime chain에서는 fault_event_audit를 validation-only로 분리하고, 별도 shadow-compare 경로에서 기존 frozen chain 결과와 diff를 먼저 점검하는 것이 안전하다.
