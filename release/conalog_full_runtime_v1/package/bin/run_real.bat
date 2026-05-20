@echo off
chcp 65001 >nul
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PACKAGE_ROOT=%%~fI"
set "APP_PATH=%PACKAGE_ROOT%\app\run_full_algorithm_pack.py"
set "IMPORT_APP=%PACKAGE_ROOT%\app\import_any_csv_root.py"
set "DEFAULT_OUTPUT=%PACKAGE_ROOT%\real_output"
call "%PACKAGE_ROOT%\bin\resolve_python.bat"
if errorlevel 1 goto FAIL

where powershell >nul 2>nul
if errorlevel 1 (
  echo Windows PowerShell을 찾을 수 없습니다.
  goto FAIL
)

set "DATA_ROOT="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $dialog = New-Object System.Windows.Forms.FolderBrowserDialog; $dialog.Description='data 루트 폴더를 선택하십시오 (conalog\raw, gangui\raw, ktc_ess\raw 포함)'; if ($dialog.ShowDialog() -eq 'OK') { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output $dialog.SelectedPath }"`) do set "DATA_ROOT=%%I"

if "%DATA_ROOT%"=="" (
  echo 입력 폴더 경로를 다시 확인하십시오.
  goto CANCEL
)

echo [005%%] 입력 폴더 선택 완료: %DATA_ROOT%

set "OUTPUT_ROOT="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $dialog = New-Object System.Windows.Forms.FolderBrowserDialog; $dialog.Description='출력 폴더를 선택하십시오 (취소 시 기본값 사용)'; if ($dialog.ShowDialog() -eq 'OK') { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output $dialog.SelectedPath }"`) do set "OUTPUT_ROOT=%%I"
if "%OUTPUT_ROOT%"=="" set "OUTPUT_ROOT=%DEFAULT_OUTPUT%"

echo [010%%] 결과 폴더 준비 완료: %OUTPUT_ROOT%

set "EFFECTIVE_DATA_ROOT=%DATA_ROOT%"
set "EFFECTIVE_SITES=conalog,gangui,ktc_ess"

if exist "%DATA_ROOT%\conalog\raw" if exist "%DATA_ROOT%\gangui\raw" if exist "%DATA_ROOT%\ktc_ess\raw" goto RUN_ENGINE
if exist "%DATA_ROOT%\data\conalog\raw" if exist "%DATA_ROOT%\data\gangui\raw" if exist "%DATA_ROOT%\data\ktc_ess\raw" (
  set "EFFECTIVE_DATA_ROOT=%DATA_ROOT%\data"
  goto RUN_ENGINE
)

set "IMPORT_STAGE_ROOT=%OUTPUT_ROOT%\imported_data"
set "IMPORT_ENV=%IMPORT_STAGE_ROOT%\import_env.bat"
set "IMPORT_MANIFEST=%IMPORT_STAGE_ROOT%\import_any_csv_manifest_v1.json"

echo [020%%] CSV 구조를 점검하고 자동 staging 여부를 결정합니다.

%PYTHON_CMD% "%IMPORT_APP%" --input-root "%DATA_ROOT%" --output-root "%IMPORT_STAGE_ROOT%" --clear-output --manifest-path "%IMPORT_MANIFEST%" --env-bat-path "%IMPORT_ENV%"
if errorlevel 1 goto FAIL

call "%IMPORT_ENV%"
if errorlevel 1 goto FAIL
set "EFFECTIVE_DATA_ROOT=%IMPORTED_DATA_ROOT%"
set "EFFECTIVE_SITES=%IMPORTED_SITES%"

:RUN_ENGINE
echo [040%%] 학습/추론 및 결과표 생성을 시작합니다.

%PYTHON_CMD% "%APP_PATH%" --data-root "%EFFECTIVE_DATA_ROOT%" --output-root "%OUTPUT_ROOT%" --sites "%EFFECTIVE_SITES%"
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
