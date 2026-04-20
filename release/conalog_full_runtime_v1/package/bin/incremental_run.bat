@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PACKAGE_ROOT=%%~fI"
set "APP_PATH=%PACKAGE_ROOT%\app\run_full_algorithm_pack.py"
set "IMPORT_APP=%PACKAGE_ROOT%\app\import_any_csv_root.py"
set "DEFAULT_SNAPSHOT_ROOT=%PACKAGE_ROOT%\..\runtime_snapshot_data"
set "DEFAULT_OUTPUT=%PACKAGE_ROOT%\..\runtime_output\incremental_run"

call "%PACKAGE_ROOT%\bin\resolve_python.bat"
if errorlevel 1 exit /b %errorlevel%

where powershell >nul 2>nul
if errorlevel 1 (
  echo Windows PowerShell을 찾을 수 없습니다.
  exit /b 0
)

set "INGEST_ROOT="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $dialog = New-Object System.Windows.Forms.FolderBrowserDialog; $dialog.Description='MLPE ingest 루트 폴더를 선택하십시오 (conalog\raw, gangui\raw, ktc_ess\raw 포함)'; if ($dialog.ShowDialog() -eq 'OK') { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output $dialog.SelectedPath }"`) do set "INGEST_ROOT=%%I"

if "%INGEST_ROOT%"=="" (
  echo 입력 폴더 경로를 다시 확인하십시오.
  exit /b 0
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

%PYTHON_CMD% "%IMPORT_APP%" --input-root "%INGEST_ROOT%" --output-root "%SNAPSHOT_ROOT%" --clear-output --stable-minutes %STABLE_MINUTES% --manifest-path "%IMPORT_MANIFEST%" --env-bat-path "%IMPORT_ENV%"
if errorlevel 1 exit /b %errorlevel%

call "%IMPORT_ENV%"
if errorlevel 1 exit /b %errorlevel%

%PYTHON_CMD% "%APP_PATH%" --data-root "%IMPORTED_DATA_ROOT%" --output-root "%OUTPUT_ROOT%" --sites "%IMPORTED_SITES%"
if errorlevel 1 exit /b %errorlevel%

if exist "%OUTPUT_ROOT%\result\fault_panel_result_master_report_v1.md" (
  start "" "%OUTPUT_ROOT%\result\fault_panel_result_master_report_v1.md"
) else if exist "%OUTPUT_ROOT%\result\fault_panel_result_current_report_v1.md" (
  start "" "%OUTPUT_ROOT%\result\fault_panel_result_current_report_v1.md"
) else if exist "%OUTPUT_ROOT%\result\fault_panel_result_current_preview_v1.csv" (
  start "" "%OUTPUT_ROOT%\result\fault_panel_result_current_preview_v1.csv"
) else if exist "%OUTPUT_ROOT%\result" (
  start "" "%OUTPUT_ROOT%\result"
)
exit /b 0
