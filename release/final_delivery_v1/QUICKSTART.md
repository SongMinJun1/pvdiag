# Quickstart

## 1. demonstration
- `package/bin/run_demo.bat`
- packaged example input 으로 one-click foundation 을 실행함
- Python 3 설치는 필요하지만, git 설치는 dry-run/demo 흐름에 필수 아님

## 2. actual input folder 실행
- `package/bin/run_real.bat`
- `package/bin/settings.template.json` 또는 `settings.json` 을 이용하여 input-root, output-root, config 를 지정함

## 3. optional GUI
- `package/app/app_streamlit.py`
- foundation GUI 이며 stable output 과 optional experimental output 을 분리해서 보여줌

## 4. system / dashboard integration
- stable direct CLI 는 `package/app/run_conalog_infer.py`
- one-click orchestration 은 `package/app/run_oneclick.py`
- 문서를 scraping 하지 말고 executable entrypoint 를 직접 호출해야 함
- git executable 이 대상 장비 PATH 에 없어도 stable dry-run 은 계속 수행 가능함

## 운영 원칙
- stable output 을 먼저 읽어야 함
- reference_only 와 triage_only 는 stable default output 과 혼동하면 안 됨
- demo/one-click 은 현재 minimal setup 기준으로 지원하지만, Python 설치 자체는 필요함
