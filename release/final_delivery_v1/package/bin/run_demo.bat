@echo off
setlocal
set PACKAGE_ROOT=%~dp0..
set INPUT_ROOT=%PACKAGE_ROOT%\stable_handoff\examples
set OUTPUT_ROOT=%PACKAGE_ROOT%\demo_output
set CONFIG_PATH=%PACKAGE_ROOT%\config\runtime.yaml
set "PYTHON_CMD="

where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON_CMD=py -3"
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    set "PYTHON_CMD=python"
  ) else (
    echo Python 3가 필요합니다. Python을 설치한 뒤 다시 실행하십시오.
    exit /b 1
  )
)

call %PYTHON_CMD% "%PACKAGE_ROOT%\app\run_oneclick.py" ^
  --input-root "%INPUT_ROOT%" ^
  --output-root "%OUTPUT_ROOT%" ^
  --config "%CONFIG_PATH%" ^
  --include-experimental off ^
  --report on

if errorlevel 1 exit /b %errorlevel%
echo.
echo [OK] results written under %OUTPUT_ROOT%\latest
