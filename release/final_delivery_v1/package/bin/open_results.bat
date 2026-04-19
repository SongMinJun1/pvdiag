@echo off
setlocal
set PACKAGE_ROOT=%~dp0..
set SETTINGS_FILE=%PACKAGE_ROOT%\bin\settings.json
if exist "%SETTINGS_FILE%" goto have_settings
set SETTINGS_FILE=%PACKAGE_ROOT%\bin\settings.template.json

:have_settings
for /f "delims=" %%I in ('python -c "import json, pathlib; root = pathlib.Path(r'%PACKAGE_ROOT%'); settings = json.loads(pathlib.Path(r'%SETTINGS_FILE%').read_text(encoding='utf-8')); latest = pathlib.Path(settings.get('output_root', str(root / 'demo_output'))) / 'latest'; print(str(latest))"') do set LATEST_DIR=%%I

if exist "%LATEST_DIR%" (
  start "" "%LATEST_DIR%"
) else (
  echo latest output directory not found: %LATEST_DIR%
  exit /b 1
)
