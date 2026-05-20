# PV Diagnostics External Delivery Guide V1

## 전달 목적
본 package는 패널별 raw CSV를 입력으로 받아 PV 패널 고장/전조 진단 결과를 CSV와 리포트로 생성하는 실행용 알고리즘 package다.

상대 시스템이 이미 대시보드를 가지고 있는 경우, 이 package는 UI를 대체하지 않고 아래 역할만 담당한다.

1. raw CSV 폴더를 입력으로 받는다.
2. 알고리즘을 실행한다.
3. 대시보드가 읽을 수 있는 결과 CSV를 생성한다.

## 실행에 필요한 것
- Python 실행 환경
- 입력 raw CSV 폴더
- 아래 Python package
  - `pandas`
  - `numpy`
  - `torch`
  - `openpyxl`
  - `tqdm`

Windows 전달 환경에서는 package 내부의 embedded Python/runtime wrapper를 우선 사용할 수 있다.

## 입력 폴더 구조
기본 입력 구조는 아래와 같다.

```text
data_root/
  ktc_ess/
    raw/
      *.csv
```

여러 site를 동시에 실행할 경우:

```text
data_root/
  conalog/
    raw/
      *.csv
  gangui/
    raw/
      *.csv
  ktc_ess/
    raw/
      *.csv
```

raw CSV 형식은 기존 KTC ESS/conalog 형식과 동일하다는 전제로 실행한다.

## 기본 실행 명령
KTC ESS만 실행하는 경우:

```bash
python package/app/run_full_algorithm_pack.py \
  --data-root "/path/to/data_root" \
  --output-root "/path/to/output_root" \
  --sites ktc_ess
```

세 site를 함께 실행하는 경우:

```bash
python package/app/run_full_algorithm_pack.py \
  --data-root "/path/to/data_root" \
  --output-root "/path/to/output_root" \
  --sites conalog,gangui,ktc_ess
```

## 대시보드가 우선 읽을 CSV
대시보드 1차 표시용 CSV는 아래 파일이다.

```text
output_root/result/fault_panel_result_current_preview_v1.csv
```

주요 컬럼:

| 컬럼 | 의미 |
| --- | --- |
| `site` | site 이름 |
| `panel_id` | 패널 식별자 |
| `전조날짜` | 전조 onset 날짜. 없으면 `전조없음` |
| `고장 기준일` | 고장 또는 runtime trigger 기준일 |
| `운영 판정` | 확정, 고위험 관찰, 관찰 단계 등 운영 판정 |
| `급락 종결 관측` | 급락/종결성 신호 관측 여부 |
| `점진 저하 누적` | 점진 저하 누적 여부 |
| `사건 종결 요약` | 전조 후 급격 종료, 진행 악화, 급작 발생 등 사건 요약 |
| `상위 해석 후보` | 알고리즘의 1순위 원인 후보 |
| `기존 알고리즘 source` | 기존 알고리즘 또는 legacy source 태그 |

## 결과 검증 명령
실행 후 아래 명령으로 dashboard-facing output이 정상 생성됐는지 확인한다.

```bash
python package/app/verify_dashboard_outputs.py \
  --output-root "/path/to/output_root"
```

검증이 통과하면 아래 JSON이 생성된다.

```text
output_root/dashboard_output_check_v1.json
```

## 보조 산출물
상세 분석이 필요한 경우 아래 파일을 함께 확인한다.

| 파일 | 용도 |
| --- | --- |
| `result/fault_panel_result_current_v1.csv` | current 공식 결과 상세 |
| `result/fault_panel_result_precursor_report_v1.csv` | 전조 후보 및 근거 |
| `result/fault_panel_result_current_report_v1.md` | current 결과 설명 |
| `result/fault_panel_result_master_report_v1.md` | 전체 산출물 판독 순서 |
| `result/fault_panel_result_detailed_report_v1.xlsx` | 상세 검토용 xlsx |

## 판독 원칙
- 대시보드는 `result/fault_panel_result_current_preview_v1.csv`를 먼저 읽는다.
- `result/raw_only_chain/*`와 `result/live_chain/*`는 분석/검증용 보조 산출물이다.
- `_share` 내부 파일은 디버깅 및 재현성 확인용이며, 대시보드 primary output으로 직접 쓰지 않는다.
- `site`와 `panel_id`를 함께 key로 사용한다.

## 실증 raw 추가 후 할 일
실증 raw 날짜가 추가되면 같은 명령으로 재실행하고 아래만 다시 확인한다.

1. `fault_panel_result_current_preview_v1.csv` 생성 여부
2. row count
3. schema
4. `dashboard_output_check_v1.json`
5. 주요 fault/event 결과
