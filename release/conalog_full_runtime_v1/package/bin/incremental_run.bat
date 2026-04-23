@echo off
chcp 65001 >nul
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PACKAGE_ROOT=%%~fI"
set "APP_PATH=%PACKAGE_ROOT%\app\run_full_algorithm_pack.py"
set "IMPORT_APP=%PACKAGE_ROOT%\app\import_any_csv_root.py"
set "DEFAULT_SNAPSHOT_ROOT=%PACKAGE_ROOT%\..\runtime_snapshot_data"
set "DEFAULT_OUTPUT=%PACKAGE_ROOT%\..\runtime_output\incremental_run"

call "%PACKAGE_ROOT%\bin\resolve_python.bat"
if errorlevel 1 goto FAIL

where powershell >nul 2>nul
if errorlevel 1 (
  echo Windows PowerShell을 찾을 수 없습니다.
  goto FAIL
)

set "INGEST_ROOT="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $dialog = New-Object System.Windows.Forms.FolderBrowserDialog; $dialog.Description='MLPE ingest 루트 폴더를 선택하십시오 (conalog\raw, gangui\raw, ktc_ess\raw 포함)'; if ($dialog.ShowDialog() -eq 'OK') { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output $dialog.SelectedPath }"`) do set "INGEST_ROOT=%%I"

if "%INGEST_ROOT%"=="" (
  echo 입력 폴더 경로를 다시 확인하십시오.
  goto CANCEL
)

set "SNAPSHOT_ROOT="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $dialog = New-Object System.Windows.Forms.FolderBrowserDialog; $dialog.Description='snapshot 루트 폴더를 선택하십시오 (취소 시 기본값 사용)'; if ($dialog.ShowDialog() -eq 'OK') { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output $dialog.SelectedPath }"`) do set "SNAPSHOT_ROOT=%%I"
if "%SNAPSHOT_ROOT%"=="" set "SNAPSHOT_ROOT=%DEFAULT_SNAPSHOT_ROOT%"

set "OUTPUT_ROOT="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $dialog = New-Object System.Windows.Forms.FolderBrowserDialog; $dialog.Description='출력 폴더를 선택하십시오 (취소 시 기본값 사용)'; if ($dialog.ShowDialog() -eq 'OK') { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output $dialog.SelectedPath }"`) do set "OUTPUT_ROOT=%%I"
if "%OUTPUT_ROOT%"=="" set "OUTPUT_ROOT=%DEFAULT_OUTPUT%"

set /p STABLE_MINUTES=안정화 대기 분을 입력하십시오 [기본값: 10]: 
if "%STABLE_MINUTES%"=="" set "STABLE_MINUTES=10"

set "IMPORT_ENV=%SNAPSHOT_ROOT%\import_env.bat"
set "IMPORT_MANIFEST=%SNAPSHOT_ROOT%\import_any_csv_manifest_v1.json"

echo [010%%] snapshot 경로와 출력 경로를 준비했습니다.
echo [020%%] 안정화된 CSV만 snapshot으로 가져옵니다.

%PYTHON_CMD% "%IMPORT_APP%" --input-root "%INGEST_ROOT%" --output-root "%SNAPSHOT_ROOT%" --clear-output --stable-minutes %STABLE_MINUTES% --manifest-path "%IMPORT_MANIFEST%" --env-bat-path "%IMPORT_ENV%"
if errorlevel 1 goto FAIL

call "%IMPORT_ENV%"
if errorlevel 1 goto FAIL

echo [040%%] 학습/추론 및 결과표 생성을 시작합니다.

%PYTHON_CMD% "%APP_PATH%" --data-root "%IMPORTED_DATA_ROOT%" --output-root "%OUTPUT_ROOT%" --sites "%IMPORTED_SITES%"
if errorlevel 1 goto FAIL

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
goto SUCCESS

:CANCEL
echo 작업이 취소되었습니다.
if "%PVDIAG_NO_PAUSE%"=="" pause
exit /b 0

:FAIL
set "EXIT_CODE=%ERRORLEVEL%"
if "%EXIT_CODE%"=="" set "EXIT_CODE=1"
echo 실행이 중단되었습니다. 위 메시지를 확인하십시오.
if "%PVDIAG_NO_PAUSE%"=="" pause
exit /b %EXIT_CODE%

:SUCCESS
if "%PVDIAG_NO_PAUSE%"=="" pause
exit /b 0
