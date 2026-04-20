@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PACKAGE_ROOT=%%~fI"

if exist "%PACKAGE_ROOT%\artifacts\fault6_label_and_algorithm_preview_v1.csv" start "" "%PACKAGE_ROOT%\artifacts\fault6_label_and_algorithm_preview_v1.csv"
if exist "%PACKAGE_ROOT%\artifacts\fault6_fixed_result_table_v1.csv" start "" "%PACKAGE_ROOT%\artifacts\fault6_fixed_result_table_v1.csv"
if exist "%PACKAGE_ROOT%\..\README.md" start "" "%PACKAGE_ROOT%\..\README.md"

exit /b 0
