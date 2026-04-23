# conalog Full Runtime Pack V1

이 pack은 `pv_ae/panel_day_engine.py` 본체를 실제로 포함한 최소 실행 pack임.

핵심 원칙은 아래와 같음.

- panel multiaxis verdict는 기존 frozen 산출물에서 primary로 유지함
- 이 pack의 목적은 실제 core engine을 USB/Windows 시연 가능 형태로 함께 가져가는 것임
- GPVS와 heuristic을 새로 과장하지 않음
- 최종 front-facing integrated table schema 자체는 바꾸지 않음
- 결과를 바꾸는 대신 `shadow compare`와 `runtime_chain_dependency_audit_v1`로 현재 live 범위와 blocker를 같이 설명함

이 pack에 들어 있는 핵심 파일은 아래와 같음.

- `package/pv_ae/panel_day_engine.py`
- `package/app/run_full_algorithm_pack.py`
- `package/research/prognostics/build_panel_day_engine_bootstrap_verdict_v1.py`
- `package/research/prognostics/build_panel_day_engine_fault_panel_event_audit_v1.py`
- `package/research/prognostics/build_panel_day_engine_panel_multiaxis_verdict_v1.py`
- `package/research/prognostics/build_panel_day_engine_gpvs_evidence_pack_v1.py`
- `package/research/prognostics/build_panel_day_engine_cause_candidate_heuristics_v1.py`
- `package/research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py`
- `package/research/prognostics/build_panel_day_engine_runtime_final_verdict_v1.py`
- `package/research/prognostics/build_panel_day_engine_runtime_heuristic_v1.py`
- `package/_share/...`
- `package/bin/run_demo.bat`
- `package/bin/run_guided_real.bat`
- `package/bin/run_real.bat`
- `package/bin/run_imported_real.bat`
- `package/bin/stage_recent_120d.ps1`
- `package/bin/snapshot_copy.ps1`
- `package/bin/daily_run.bat`
- `package/bin/incremental_run.bat`
- `package/bin/resolve_python.bat`
- `package/app/import_any_csv_root.py`
- `package/runtime/windows_x64/python/python.exe`
- `package/runtime/windows_x64/runtime_manifest_v1.json`
- `package/artifacts/fault6_fixed_result_table_v1.csv`
- `package/artifacts/fault6_label_and_algorithm_preview_v1.csv`
- `package/artifacts/fault6_fixed_result_provenance_v1.json`
- `package/artifacts/input_baseline_manifest_v1.json`
- `package/artifacts/panel_day_core_baseline_digest_v1.json`
- `package/artifacts/runtime_chain_dependency_audit_v1.json`
- `package/artifacts/runtime_chain_dependency_audit_v1.md`

`fault6_fixed_result_table_v1.csv`는 현재 frozen verdict와 heuristic을 그대로 묶어, integrated table과 동일한 front-facing 표시명으로 다시 적재한 6개 고장 패널 결과표임.
즉, 이 파일은 현재 합의된 고정 결과표를 유지하되, runtime pack 내부에서는 integrated snapshot 자체를 직접 의존하지 않도록 정리한 artifact임.

`fault6_fixed_result_provenance_v1.json`은 위 결과표가 `frozen verdict + frozen heuristic + integrated display-name mapping` 조합으로 생성되었음을 적고, legacy integrated 6행과 exact match인지도 함께 남기는 provenance artifact임.
즉, 지금 pack에서는 integrated snapshot을 직접 자르지 않지만, 결과 자체는 기존 6행과 같다는 근거를 파일로 같이 제공함.

`package/research/prognostics/*`와 `package/_share/*`는 package 내부 live chain용 자산임.
즉, 이제 package는 engine만 들고 가는 것이 아니라 `bootstrap verdict -> fault_event_audit -> final verdict -> GPVS evidence -> heuristic` 경로를 package 안에서 다시 수행할 준비가 되어 있음.

추가로 package는 `_share` truth/support asset을 쓰지 않는 `raw-only strict chain`도 같이 포함함.
이 경로는 `panel_day_core.csv + ae_simple_local_precursor_gate_daily.csv`만 사용해 `runtime audit -> runtime final verdict -> runtime heuristic`를 만들고, `커널로그_원인군_ko` 컬럼명은 유지하되 실제 의미는 `algorithm-derived family`로 해석함.

`fault6_label_and_algorithm_preview_v1.csv`는 위 고정 6개 fault 결과표를 그대로 유지하면서, 아래 두 축을 분리해서 보여주는 preview artifact임.

- `전조날짜` : 전조형 고장으로 해석된 경우의 대표 onset 날짜
- 급작 고장처럼 전조가 채택되지 않은 경우는 `전조없음`으로 표시
- `고장 기준일` : 최종 fault 기준일 또는 runtime trigger 기준일
- `운영 판정` : 이 row가 확정인지, 고위험 관찰인지, 관찰 단계인지를 구분하는 값
- `급락 종결 관측` : final/fault 급락 종결이 실제로 관측됐는지 먼저 보여주는 값
- `점진 저하 누적` : 전조/점진 저하가 누적된 사건으로 읽히는지 먼저 보여주는 값
- `사건 종결 요약` : 확정 row에서만 채워지는 사건 요약(`전조 후 급격 종료`, `전조 후 진행 악화`, `급작 발생`)
- `상위 해석 후보` : 현재 알고리즘이 가장 가깝다고 본 원인 후보 1순위
- `기존 알고리즘 source` : legacy source 태그가 있으면 그대로, 없으면 `미검출`

즉, 이 preview는 전조/고장 시점, 현재 신호 단계, 관측 플래그, 사건 요약, 원인 후보, legacy source를 한 번에 비교해 보는 용도임.

추가로 이제 package는 Windows portable runtime도 같이 포함함.

- embedded Python 3.11.9
- `runtime\windows_x64\python\python.exe`
- win_amd64 wheel이 미리 포함된 `numpy`, `pandas`, `torch`, `tqdm`, `openpyxl`

즉, 현장 Windows PC에서는 wrapper가 위 embedded Python 3.11.9를 먼저 찾고, 없을 때만 시스템 Python을 fallback으로 사용함.

`panel_day_core_baseline_digest_v1.json`은 baseline raw corpus로 이미 산출된 `panel_day_core.csv`의 정규화 reference hash임.
같은 baseline 입력으로 runtime pack을 다시 실행했을 때 engine core output이 유지되는지 `shadow_compare_v1.json`으로 비교함.

`runtime_chain_dependency_audit_v1.json/md`는 왜 아직 full-chain live runtime이 바로 안 되는지 문서로 고정한 감사 리포트임.
핵심 메시지는 아래와 같음.

- 현재 pack은 `engine live + fixed fault artifacts` 모드임
- `verdict <-> fault_event_audit` 사이에 hard cycle이 있어 단방향 runtime chain이 아님
- 따라서 결과를 바꾸지 않는 선에서는 먼저 shadow compare로 baseline 보존을 확인하는 것이 안전함

USB 시연 동선은 아래처럼 단순하게 가져가면 됨.

1. `package\\bin\\run_demo.bat`
   - 현재까지 고정해 둔 fault 예시 결과표 중 최종 preview만 바로 엶
   - `fault6_label_and_algorithm_preview_v1.csv`

2. `package\\bin\\run_demo_ktc_fault2.bat`
   - `ktc_ess`의 고정 2건만 바로 엶
   - `ktc_fault2_label_and_algorithm_preview_v1.csv`

3. `package\\bin\\run_guided_real.bat`
   - 시연용 권장 wrapper임
   - CSV가 들어 있는 상위 폴더만 고르면 됨
   - 출력 폴더는 `package\\showcase_runs\\run_YYYYMMDD_HHMMSS` 형태로 자동 생성함
   - 콘솔에 `[005%]`, `[020%]`, `[040%]`, `[100%]` 식 진행률 문구를 보여줌
   - 실행이 끝나면 `fault_panel_result_current_preview_v1.csv`를 우선해서 열고, 없으면 `fault_panel_result_current_report_v1.md`, 그 다음 `fault_panel_result_master_report_v1.md` 순으로 엶
   - 시연 중 콘솔 창이 바로 닫히지 않도록 마지막에 `pause`를 둠

3. `package\\bin\\run_real.bat`
   - 콘솔에 경로를 직접 치지 않아도 됨
   - Windows 폴더 선택창으로 `data 루트`를 고르면 됨
   - `conalog/raw`, `gangui/raw`, `ktc_ess/raw` 또는 `data/conalog/raw` 구조면 바로 실행함
   - 그 구조가 아니어도 `import_any_csv_root.py`로 CSV를 재귀 수집해 자동 staging 후 실행함
   - 출력 폴더도 선택 가능하며, 취소하면 기본값 `package\\real_output`을 사용함
   - 실행 중 콘솔에 단계별 진행률 문구를 보여줌
   - 실행이 끝나면 `fault_panel_result_current_preview_v1.csv`를 먼저 열고, 없으면 `fault_panel_result_current_report_v1.md`, 그 다음 `fault_panel_result_master_report_v1.md`, 마지막으로 `result` 폴더를 엶
   - 실행 후 `shadow_compare_v1.json`도 함께 남음

4. `package\\bin\\run_imported_real.bat`
   - 표준 site/raw 구조를 기대하지 않고, 임의 CSV 루트 폴더를 바로 선택하는 wrapper임
   - 선택한 폴더 아래 CSV를 재귀 수집한 뒤 `imported_data/<site>/raw`로 staging 하고 실행함
   - 실행 중 콘솔에 단계별 진행률 문구를 보여줌

실행 전 준비는 아래와 같음.

1. 가장 쉬운 경로는 package에 이미 포함된 embedded Python 3.11.9를 그대로 쓰는 것임
2. 시스템 Python이 없어도 wrapper가 `runtime\windows_x64\python\python.exe`를 먼저 사용함
3. 상대방 데이터가 표준 `conalog/raw`, `gangui/raw`, `ktc_ess/raw` 구조면 그대로 연결하면 됨
4. 폴더 구조가 제각각이어도 CSV schema만 같으면 `run_guided_real.bat`, `run_real.bat`, `run_imported_real.bat`가 `import_any_csv_root.py`로 자동 staging 함

직접 CLI로 실행할 때는 아래 명령을 사용하면 됨.

```bash
python package/app/run_full_algorithm_pack.py \
  --data-root "C:\\path\\to\\data_root" \
  --output-root "C:\\path\\to\\result_folder"
```

`data-root/<site>/out`가 이미 있고 그 `panel_day_core.csv`가 raw보다 최신이면, runner는 기본값 `--prefer-existing-site-outs auto`에 따라 그 출력을 자동 재사용하고 engine 재실행을 건너뜀.
즉 baseline 검증이나 재시연에서는 같은 data 루트를 다시 연결해도 훨씬 빠르게 `live_chain`과 current 결과표를 다시 만들 수 있음.

임의 폴더 구조에서 CSV만 재귀 import하고 싶을 때는 아래 helper를 직접 사용할 수도 있음.

```bash
python package/app/import_any_csv_root.py \
  --input-root "C:\\path\\to\\any_csv_root" \
  --output-root "C:\\path\\to\\staged_data" \
  --clear-output
```

이 helper는 `data/<site>/raw`, `<site>/raw`, 또는 최상위 하위 폴더명을 우선 사용해 site 이름을 추정하고 `staged_data/<site>/raw/*.csv` 형태로 정리함.

기존 `data/<site>/out`가 이미 준비된 검증 환경에서는 아래처럼 engine 실행을 생략하고 package live chain만 끝까지 다시 돌릴 수도 있음.

```bash
python package/app/run_full_algorithm_pack.py \
  --data-root "C:\\path\\to\\data_root" \
  --output-root "C:\\path\\to\\result_folder" \
  --reuse-existing-site-outs-root "C:\\path\\to\\data_root"
```

이 옵션은 baseline 검증/QA용임. 즉 `data/<site>/out`를 package runtime workspace로 복사한 뒤 `bootstrap verdict -> fault_event_audit -> final verdict -> GPVS evidence -> heuristic`만 다시 수행함.

출력은 기본적으로 아래처럼 생성됨.

- `sites/conalog/output/panel_day_core.csv`
- `sites/gangui/output/panel_day_core.csv`
- `sites/ktc_ess/output/panel_day_core.csv`
- `result/fault6_fixed_result_table_v1.csv`
- `result/fault6_label_and_algorithm_preview_v1.csv`
- `result/fault_panel_result_current_v1.csv`
- `result/fault_panel_result_current_preview_v1.csv`
- `result/fault_panel_result_current_report_v1.md`
- `result/fault_panel_result_master_report_v1.md`
- `result/fault_panel_result_detailed_report_v1.xlsx`
- `result/fault_panel_result_precursor_report_v1.csv`
- `result/fault_panel_result_raw_only_current_v1.csv`
- `result/fault_panel_result_raw_only_current_preview_v1.csv`
- `result/fault_panel_result_raw_only_current_report_v1.md`
- `result/live_chain_summary_v1.json`
- `result/raw_only_chain_summary_v1.json`
- `result/live_chain/fault_panel_result_live_v1.csv`
- `result/live_chain/fault_panel_result_live_preview_v1.csv`
- `result/live_chain/panel_day_engine_panel_multiaxis_verdict_v1.csv`
- `result/live_chain/panel_day_engine_gpvs_evidence_pack_v1.csv`
- `result/live_chain/panel_day_engine_cause_candidate_heuristics_v1.csv`
- `result/live_chain/live_chain_summary_v1.json`
- `result/raw_only_chain/fault_panel_result_raw_only_v1.csv`
- `result/raw_only_chain/fault_panel_result_raw_only_preview_v1.csv`
- `result/raw_only_chain/panel_day_engine_runtime_fault_event_audit_v1.csv`
- `result/raw_only_chain/panel_day_engine_runtime_final_verdict_v1.csv`
- `result/raw_only_chain/panel_day_engine_runtime_cause_candidate_heuristics_v1.csv`
- `result/raw_only_chain/raw_only_chain_summary_v1.json`
- `run_plan_v1.json` 또는 `run_metadata_v1.json`
- `shadow_compare_v1.json`

`fault_panel_result_current_preview_v1.csv`, `fault_panel_result_raw_only_current_preview_v1.csv`, `fault6_label_and_algorithm_preview_v1.csv`는 모두 `site, panel_id, 전조날짜, 고장 기준일, 운영 판정, 급락 종결 관측, 점진 저하 누적, 사건 종결 요약, 상위 해석 후보, 기존 알고리즘 source` 형식의 preview 표를 제공함.
즉 운영자는 preview 시트만 열어도 전조 onset, 기준일, 현재 신호 단계, 관측 플래그, 사건 요약, 원인 후보, legacy source를 바로 확인할 수 있음.

`fault_panel_result_precursor_report_v1.csv`는 위 preview와 달리 `신호 기준일` 컬럼을 사용함.
이 값은 사람이 확정한 고장일이 아니라, runtime signal 기준으로 이상/고장 신호가 기준선을 넘은 날짜를 뜻함.

운영 방식은 아래처럼 잡는 것이 권장됨.

1. 과거 전체 raw는 `archive_data/<site>/raw` 또는 `archive_data/<site>/raw_all` 아래에 장기 보관함
2. 매일 운영은 최근 120일만 `runtime_data/<site>/raw`로 staging 함
3. 그 뒤 `runtime_data`만 pack에 연결해서 실행함
4. 월 1회 또는 버전 변경 시에만 전체 replay를 다시 수행함

예시 폴더 구조는 아래와 같음.

```text
D:\pvdiag\
  archive_data\
    conalog\raw\...
    gangui\raw\...
    ktc_ess\raw\...
  runtime_data\
    conalog\raw\...
    gangui\raw\...
    ktc_ess\raw\...
  runtime_output\
    latest\
    daily_runs\2026-04-20\
  conalog_full_runtime_v1\
    package\...
```

최근 120일 staging만 별도로 실행할 때는 아래 명령을 사용하면 됨.

```powershell
powershell -ExecutionPolicy Bypass -File package\bin\stage_recent_120d.ps1 `
  -ArchiveRoot "D:\pvdiag\archive_data" `
  -RuntimeRoot "D:\pvdiag\runtime_data" `
  -WindowDays 120
```

Windows 운영에서 staging + 엔진 실행을 한 번에 하려면 아래 wrapper를 사용하면 됨.

```bat
package\bin\daily_run.bat
```

실증에서 MLPE가 5분 단위로 계속 CSV를 적재하는 경우에는, ingest 폴더를 직접 읽지 말고 아래 snapshot 경로를 권장함.

```powershell
powershell -ExecutionPolicy Bypass -File package\bin\snapshot_copy.ps1 `
  -IngestRoot "D:\pvdiag\mlpe_ingest" `
  -SnapshotRoot "D:\pvdiag\runtime_snapshot_data" `
  -StableMinutes 10
```

`StableMinutes` 동안 수정되지 않은 CSV만 snapshot으로 복사하므로, 쓰는 중인 파일을 runner가 바로 읽는 위험을 줄일 수 있음.

실증용 incremental 실행을 한 번에 하려면 아래 wrapper를 사용하면 됨.

```bat
package\bin\incremental_run.bat
```

이 wrapper도 실행 중 콘솔에 단계별 진행률 문구를 보여주고, 끝나면 master report를 우선해서 엶.

즉 운영자 기준으로는 아래 순서만 기억하면 됨.

- 예시 시연: `run_demo.bat`
- 원클릭 시연: `run_guided_real.bat`
- 실제 실행: `run_real.bat`
- 임의 폴더 실행: `run_imported_real.bat`
- 반복 운영: `daily_run.bat`
- MLPE 실증 incremental 실행: `incremental_run.bat`

`run_guided_real.bat`, `run_real.bat`, `run_imported_real.bat`, `daily_run.bat`, `incremental_run.bat`는 실행이 끝나면 `result/fault_panel_result_current_preview_v1.csv`를 가장 먼저 열고, 없으면 `fault_panel_result_current_report_v1.md`, 그 다음 `fault_panel_result_master_report_v1.md`, 마지막으로 `result` 폴더를 엶.
`result/fault_panel_result_raw_only_current_preview_v1.csv`는 자동 오픈 기본값이 아니라 analyst/support용 보조 preview로 남기며, 필요 시 result 폴더 또는 master report 안내를 통해 수동으로 연다.

`result/fault_panel_result_detailed_report_v1.xlsx`는 실행이 끝날 때 자동으로 생성되는 상세 리포트임.
이 파일에는 아래 시트가 포함됨.

- `overview`
- `current_preview`
- `raw_only_preview`
- `raw_only_evidence`
- `precursor_report`
- `raw_only_candidate_scores`
- `raw_only_timeline`
- `raw_only_daily_log`
- `raw_only_cluster`
- `definitions`

즉, 단일 CSV만 보는 것이 아니라 메인표와 함께 전조 있는 패널 전용 precursor report, 패널별 근거요약, 9개 후보 전수 점수표, 날짜별 전체 로그, 신호가 있는 날짜 타임라인, base 군집 흔들림까지 한 번에 확인할 수 있음.

주의:
- `result/fault_panel_result_raw_only_current_*`는 raw-only candidate 전체를 그대로 노출하지 않음.
- 이 current 표는 `운영해석등급_ko=확정`인 strict subset만 보여줌.
- 전체 candidate universe는 `result/raw_only_chain/*`와 상세 리포트의 `raw_only_*` 시트에서 계속 확인 가능함.
- preview 표의 `운영 판정`은 현재 신호 단계이고, `사건 종결 요약`은 확정 row에서만 채워지는 사건 요약임.
- `급락 종결 관측`과 `점진 저하 누적`은 관측 플래그라서, 요약보다 먼저 읽는 것이 안전함.
- precursor report의 `판정 근거`와 `패턴 설명`을 함께 보면 왜 그렇게 판단했는지 더 직접적으로 읽을 수 있음.
- precursor report의 `신호 기준일`은 라벨 고장일이 아니라 signal trigger 기준일임.

주의사항은 분명함.

- 실제로 새 데이터에서 9컬럼 최종 verdict chain 전체를 다시 live recompute하는 pack은 아직 아님
- 다만 이제 package 안에서 bootstrap verdict를 먼저 만들고 live chain을 다시 수행하는 실험 경로까지는 포함함
- 동시에 raw-only strict chain도 별도 산출물로 같이 생성하므로, frozen-support live chain과 raw-only chain의 차이를 같은 실행에서 바로 비교할 수 있음
- raw-only chain의 `커널로그_원인군_ko`는 기존 라벨 fault family가 아니라 algorithm-derived family 의미임
- raw-only chain의 후보 row 수가 fixed fault6보다 커질 수 있으며, 이는 다른 점수/운영 신호와 함께 보는 candidate universe로 해석함
- 따라서 baseline tri-site universe에서는 final verdict/evidence/heuristic exact match 여부를 단계적으로 점검할 수 있음
- 실행 후 `shadow_compare_v1.json`이 생기면, baseline과 같은 입력일 때 engine core output이 reference digest와 같은지 확인할 수 있음
- `runtime_chain_dependency_audit_v1`는 왜 full-chain live runtime이 아직 blocker를 가지는지 설명하는 감사 리포트임
- 전체 `integrated result table` snapshot은 이 pack의 공식 산출물에서 제거하였음
