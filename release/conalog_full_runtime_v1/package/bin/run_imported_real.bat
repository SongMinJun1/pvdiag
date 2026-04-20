@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PACKAGE_ROOT=%%~fI"
set "APP_PATH=%PACKAGE_ROOT%\app\run_full_algorithm_pack.py"
set "IMPORT_APP=%PACKAGE_ROOT%\app\import_any_csv_root.py"
set "DEFAULT_OUTPUT=%PACKAGE_ROOT%\real_output_imported"

call "%PACKAGE_ROOT%\bin\resolve_python.bat"
if errorlevel 1 exit /b %errorlevel%

where powershell >nul 2>nul
if errorlevel 1 (
  echo Windows PowerShell을 찾을 수 없습니다.
  exit /b 0
)

set "DATA_ROOT="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $dialog = New-Object System.Windows.Forms.FolderBrowserDialog; $dialog.Description='CSV가 들어 있는 임의 루트 폴더를 선택하십시오'; if ($dialog.ShowDialog() -eq 'OK') { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output $dialog.SelectedPath }"`) do set "DATA_ROOT=%%I"

if "%DATA_ROOT%"=="" (
  echo 입력 폴더 경로를 다시 확인하십시오.
  exit /b 0
)

set "OUTPUT_ROOT="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $dialog = New-Object System.Windows.Forms.FolderBrowserDialog; $dialog.Description='출력 폴더를 선택하십시오 (취소 시 기본값 사용)'; if ($dialog.ShowDialog() -eq 'OK') { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output $dialog.SelectedPath }"`) do set "OUTPUT_ROOT=%%I"
if "%OUTPUT_ROOT%"=="" set "OUTPUT_ROOT=%DEFAULT_OUTPUT%"

set "IMPORT_STAGE_ROOT=%OUTPUT_ROOT%\imported_data"
set "IMPORT_ENV=%IMPORT_STAGE_ROOT%\import_env.bat"
set "IMPORT_MANIFEST=%IMPORT_STAGE_ROOT%\import_any_csv_manifest_v1.json"

%PYTHON_CMD% "%IMPORT_APP%" --input-root "%DATA_ROOT%" --output-root "%IMPORT_STAGE_ROOT%" --clear-output --manifest-path "%IMPORT_MANIFEST%" --env-bat-path "%IMPORT_ENV%"
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
