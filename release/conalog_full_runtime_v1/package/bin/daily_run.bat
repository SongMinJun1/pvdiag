@echo off
chcp 65001 >nul
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PACKAGE_ROOT=%%~fI"
set "STAGING_PS1=%PACKAGE_ROOT%\bin\stage_recent_120d.ps1"
set "APP_PATH=%PACKAGE_ROOT%\app\run_full_algorithm_pack.py"
call "%PACKAGE_ROOT%\bin\resolve_python.bat"
if errorlevel 1 exit /b %errorlevel%

set /p ARCHIVE_ROOT=archive_data 루트 경로를 입력하십시오 ^(예: D:\pvdiag\archive_data^):
if "%ARCHIVE_ROOT%"=="" (
    echo archive_data 루트 경로를 다시 확인하십시오.
  exit /b 0
)
if not exist "%ARCHIVE_ROOT%" (
  echo archive_data 루트 경로를 다시 확인하십시오.
  exit /b 0
)

set /p RUNTIME_ROOT=runtime_data 경로를 입력하십시오 [기본값: %PACKAGE_ROOT%\..\runtime_data]:
if "%RUNTIME_ROOT%"=="" set "RUNTIME_ROOT=%PACKAGE_ROOT%\..\runtime_data"

set /p OUTPUT_ROOT=출력 폴더 경로를 입력하십시오 [기본값: %PACKAGE_ROOT%\..\runtime_output\daily_run]:
if "%OUTPUT_ROOT%"=="" set "OUTPUT_ROOT=%PACKAGE_ROOT%\..\runtime_output\daily_run"

echo [010%%] 최근 120일 raw staging 경로를 준비했습니다.

powershell -ExecutionPolicy Bypass -File "%STAGING_PS1%" -ArchiveRoot "%ARCHIVE_ROOT%" -RuntimeRoot "%RUNTIME_ROOT%" -WindowDays 120
if errorlevel 1 exit /b %errorlevel%

echo [040%%] 학습/추론 및 결과표 생성을 시작합니다.

%PYTHON_CMD% "%APP_PATH%" --data-root "%RUNTIME_ROOT%" --output-root "%OUTPUT_ROOT%"
if errorlevel 1 exit /b %errorlevel%

echo [100%%] 실행 완료. 결과 리포트를 엽니다.

if exist "%OUTPUT_ROOT%\result\fault_panel_result_current_preview_v1.csv" (
  start "" "%OUTPUT_ROOT%\result\fault_panel_result_current_preview_v1.csv"
) else if exist "%OUTPUT_ROOT%\result\fault_panel_result_current_report_v1.md" (
  start "" "%OUTPUT_ROOT%\result\fault_panel_result_current_report_v1.md"
) else if exist "%OUTPUT_ROOT%\result\fault_panel_result_master_report_v1.md" (
  start "" "%OUTPUT_ROOT%\result\fault_panel_result_master_report_v1.md"
) else if exist "%OUTPUT_ROOT%\result" (
  start "" "%OUTPUT_ROOT%\result"
)
exit /b 0
