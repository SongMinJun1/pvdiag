@echo off
setlocal
set PACKAGE_ROOT=%~dp0..
set INPUT_ROOT=%PACKAGE_ROOT%\stable_handoff\examples
set OUTPUT_ROOT=%PACKAGE_ROOT%\demo_output
set CONFIG_PATH=%PACKAGE_ROOT%\config\runtime.yaml

python "%PACKAGE_ROOT%\app\run_oneclick.py" ^
  --input-root "%INPUT_ROOT%" ^
  --output-root "%OUTPUT_ROOT%" ^
  --config "%CONFIG_PATH%" ^
  --include-experimental off ^
  --report on

if errorlevel 1 exit /b %errorlevel%
echo.
echo [OK] results written under %OUTPUT_ROOT%\latest
