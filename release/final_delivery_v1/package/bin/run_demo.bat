@echo off
setlocal
set PACKAGE_ROOT=%~dp0..
set INPUT_ROOT=%PACKAGE_ROOT%\stable_handoff\examples
set OUTPUT_ROOT=%PACKAGE_ROOT%\demo_output
set OUTPUT_DIR=%OUTPUT_ROOT%\output
set CONFIG_PATH=%PACKAGE_ROOT%\stable_handoff\config\default.yaml

where py >nul 2>nul
if %errorlevel%==0 goto use_py
where python >nul 2>nul
if %errorlevel%==0 goto use_python
echo Python 3가 필요합니다. Python을 설치한 뒤 다시 실행하십시오.
exit /b 1

:use_py
py -3 "%PACKAGE_ROOT%\app\run_conalog_infer.py" --input-root "%INPUT_ROOT%" --output-root "%OUTPUT_ROOT%" --config "%CONFIG_PATH%"
if errorlevel 1 exit /b %errorlevel%
if exist "%OUTPUT_DIR%" start "" "%OUTPUT_DIR%"
exit /b 0

:use_python
python "%PACKAGE_ROOT%\app\run_conalog_infer.py" --input-root "%INPUT_ROOT%" --output-root "%OUTPUT_ROOT%" --config "%CONFIG_PATH%"
if errorlevel 1 exit /b %errorlevel%
if exist "%OUTPUT_DIR%" start "" "%OUTPUT_DIR%"
exit /b 0
