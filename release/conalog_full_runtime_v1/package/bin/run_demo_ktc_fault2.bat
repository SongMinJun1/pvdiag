@echo off
chcp 65001 >nul
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PACKAGE_ROOT=%%~fI"

if exist "%PACKAGE_ROOT%\artifacts\ktc_fault2_label_and_algorithm_preview_v1.csv" start "" "%PACKAGE_ROOT%\artifacts\ktc_fault2_label_and_algorithm_preview_v1.csv"
if not exist "%PACKAGE_ROOT%\artifacts\ktc_fault2_label_and_algorithm_preview_v1.csv" (
  echo ktc_fault2_label_and_algorithm_preview_v1.csv를 찾지 못했습니다.
  if "%PVDIAG_NO_PAUSE%"=="" pause
  exit /b 1
)

exit /b 0
