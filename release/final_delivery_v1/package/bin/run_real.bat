@echo off
setlocal
set PACKAGE_ROOT=%~dp0..
set CONFIG_PATH=%PACKAGE_ROOT%\stable_handoff\config\default.yaml
set DEFAULT_OUTPUT_ROOT=%PACKAGE_ROOT%\real_output

where py >nul 2>nul
if %errorlevel%==0 goto have_python
where python >nul 2>nul
if %errorlevel%==0 goto have_python
echo Python 3가 필요합니다. Python을 설치한 뒤 다시 실행하십시오.
exit /b 1

:have_python
set /p INPUT_ROOT=입력 폴더 경로를 입력하십시오:
if "%INPUT_ROOT%"=="" goto invalid_input
if not exist "%INPUT_ROOT%" goto invalid_input

set /p OUTPUT_ROOT=출력 폴더 경로를 입력하십시오(빈칸이면 기본값 사용):
if "%OUTPUT_ROOT%"=="" set OUTPUT_ROOT=%DEFAULT_OUTPUT_ROOT%

where py >nul 2>nul
if %errorlevel%==0 goto run_with_py
python "%PACKAGE_ROOT%\app\run_conalog_infer.py" --input-root "%INPUT_ROOT%" --output-root "%OUTPUT_ROOT%" --config "%CONFIG_PATH%"
if errorlevel 1 exit /b %errorlevel%
if exist "%OUTPUT_ROOT%\output" start "" "%OUTPUT_ROOT%\output"
exit /b 0

:run_with_py
py -3 "%PACKAGE_ROOT%\app\run_conalog_infer.py" --input-root "%INPUT_ROOT%" --output-root "%OUTPUT_ROOT%" --config "%CONFIG_PATH%"
if errorlevel 1 exit /b %errorlevel%
if exist "%OUTPUT_ROOT%\output" start "" "%OUTPUT_ROOT%\output"
exit /b 0

:invalid_input
echo 입력 폴더 경로를 다시 확인하십시오.
exit /b 0
