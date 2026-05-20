# Quickstart

## 1. demonstration
- `package/bin/run_demo.bat`
- packaged example input 으로 `package/app/run_conalog_infer.py` 를 직접 실행하는 thin wrapper 임
- Python 3 설치는 필요하지만, git 설치는 dry-run/demo 흐름에 필수 아님

## 2. actual input folder 실행
- `package/bin/run_real.bat`
- 실행 시 input_root 를 직접 입력받고, output_root 는 비우면 `package/real_output` 을 기본값으로 사용함
- 내부적으로 `package/app/run_conalog_infer.py` 를 직접 실행하는 thin wrapper 임

## 3. system / dashboard integration
- stable direct CLI 는 `package/app/run_conalog_infer.py`
- demo/real batch wrapper 는 stable CLI 위의 thin wrapper 임
- 문서를 scraping 하지 말고 executable entrypoint 를 직접 호출해야 함
- git executable 이 대상 장비 PATH 에 없어도 stable dry-run 은 계속 수행 가능함

## 운영 원칙
- stable output 을 먼저 읽어야 함
- reference_only 와 triage_only 는 stable default output 과 혼동하면 안 됨
- final front-facing integrated table schema 는 그대로 유지됨
- one-click 과 Streamlit 은 optional foundation utility 이며 이번 hotfix scope 에 포함되지 않음
- demo/real wrapper 는 현재 minimal setup 기준으로 지원하지만, Python 설치 자체는 필요함
