# Dashboard Integration Contract V1

## Purpose
- 이 문서는 외부 대시보드 또는 운영 시스템이 본 runtime pack을 호출하고 결과 CSV를 읽는 최소 계약을 정리한다.
- 상대 시스템이 보유한 raw CSV 형식은 기존 KTC ESS/conalog raw 형식과 동일하다는 전제를 둔다.
- 따라서 별도 schema 변환기를 먼저 만들지 않고, raw 폴더를 runtime pack에 연결한 뒤 결과 CSV를 대시보드가 읽는 방식이 기본이다.

## Recommended Integration Flow
1. 상대 시스템은 raw CSV를 `data-root/<site>/raw/*.csv` 형태로 준비한다.
2. runtime pack은 `package/app/run_full_algorithm_pack.py`를 실행한다.
3. 대시보드는 `output-root/result/fault_panel_result_current_preview_v1.csv`를 1차 표시 CSV로 읽는다.
4. 상세 확인이 필요하면 precursor, master report, detailed xlsx를 보조 자료로 읽는다.

## Command
```bash
python package/app/run_full_algorithm_pack.py \
  --data-root "/path/to/data_root" \
  --output-root "/path/to/result_folder" \
  --sites ktc_ess
```

여러 site를 한 번에 실행할 때는 아래처럼 site 목록을 지정한다.

```bash
python package/app/run_full_algorithm_pack.py \
  --data-root "/path/to/data_root" \
  --output-root "/path/to/result_folder" \
  --sites conalog,gangui,ktc_ess
```

## Input Contract
- 기본 구조: `data-root/<site>/raw/*.csv`
- 예: `data-root/ktc_ess/raw/*.csv`
- raw CSV 형식은 기존 KTC ESS/conalog 형식과 동일해야 한다.
- 날짜 구간이 길어질수록 전조, 반복 이벤트, 장기 저하 판단이 안정된다.

## Dashboard Primary Output
대시보드는 우선 아래 파일을 읽는 것을 권장한다.

```text
output-root/result/fault_panel_result_current_preview_v1.csv
```

이 파일은 운영자가 바로 보기 위한 current preview이며, 핵심 컬럼은 아래와 같다.

| Column | Meaning |
| --- | --- |
| `site` | site 이름 |
| `panel_id` | 패널 식별자 |
| `전조날짜` | 전조로 채택된 대표 onset 날짜. 없으면 `전조없음` |
| `고장 기준일` | 고장 또는 runtime trigger 기준일 |
| `운영 판정` | 확정, 고위험 관찰, 관찰 단계 등 운영용 판정 |
| `급락 종결 관측` | 급락/종결성 신호 관측 여부 |
| `점진 저하 누적` | 점진 저하 누적 여부 |
| `사건 종결 요약` | 전조 후 급격 종료, 진행 악화, 급작 발생 등 사건 요약 |
| `상위 해석 후보` | 알고리즘이 가장 가깝게 본 원인 후보 |
| `기존 알고리즘 source` | 기존 알고리즘 또는 legacy source 태그 |

## Support Outputs
대시보드 또는 분석자가 추가로 참고할 수 있는 파일은 아래와 같다.

| Output | Role |
| --- | --- |
| `result/fault_panel_result_current_v1.csv` | current 공식 결과의 상세 CSV |
| `result/fault_panel_result_precursor_report_v1.csv` | 전조 후보와 근거를 더 자세히 보는 CSV |
| `result/fault_panel_result_current_report_v1.md` | current 결과 설명 문서 |
| `result/fault_panel_result_master_report_v1.md` | 전체 artifact와 판독 순서 안내 |
| `result/fault_panel_result_detailed_report_v1.xlsx` | 상세 검토용 xlsx |
| `result/live_chain/*` | frozen-support live chain 내부 산출물 |
| `result/raw_only_chain/*` | raw-only strict/support chain 내부 산출물 |

## Reading Policy
- dashboard 1차 표시는 `fault_panel_result_current_preview_v1.csv`를 기본으로 한다.
- `raw_only_chain`은 support/analyst 확인용으로 먼저 읽는다.
- `live_chain`과 `_share` 내부 파일은 디버깅 또는 검증용이며, dashboard primary contract로 직접 노출하지 않는다.
- `panel_id`와 `site`를 함께 key로 사용한다.
- 같은 raw 형식에서는 별도 입력 변환 없이 실행할 수 있다.

## Dependency Contract
외부 Python 패키지는 별도 설치 전제로 둔다.

- `pandas`
- `numpy`
- `torch`
- `openpyxl`
- `tqdm`

Windows 전달 환경에서는 pack 안의 embedded Python/runtime wrapper를 우선 사용할 수 있다.

## Validation Checklist
전달 전 또는 상대 시스템 연동 전 아래를 확인한다.

1. `package/app/run_full_algorithm_pack.py --dry-run`이 입력 경로를 정상 인식한다.
2. 실행 후 `result/fault_panel_result_current_preview_v1.csv`가 생성된다.
3. preview CSV에 `site`, `panel_id`, `운영 판정`, `상위 해석 후보`가 존재한다.
4. `result/fault_panel_result_detailed_report_v1.xlsx`가 생성된다.
5. 대시보드는 `_share` 또는 site별 engine 내부 output이 아니라 `result/` 아래 공식 artifact를 읽는다.

실행이 끝난 뒤 아래 verifier로 dashboard contract를 한 번에 확인할 수 있다.

```bash
python package/app/verify_dashboard_outputs.py \
  --output-root "/path/to/result_folder"
```

검증이 통과하면 `dashboard_output_check_v1.json`이 생성된다.

## Notes
- 본 문서는 알고리즘 동작을 바꾸지 않는다.
- 본 문서의 목적은 동일 raw 형식을 가진 외부 dashboard가 어떤 entrypoint를 호출하고 어떤 CSV를 읽어야 하는지 고정하는 것이다.
- 실증 raw 날짜가 추가되면 같은 command로 재실행하고, row count와 schema만 다시 확인하면 된다.
