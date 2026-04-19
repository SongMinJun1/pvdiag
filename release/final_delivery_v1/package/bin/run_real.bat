@echo off
setlocal
set PACKAGE_ROOT=%~dp0..
set TEMPLATE_FILE=%PACKAGE_ROOT%\bin\settings.template.json
set SETTINGS_FILE=%PACKAGE_ROOT%\bin\settings.json
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

if not exist "%SETTINGS_FILE%" copy "%TEMPLATE_FILE%" "%SETTINGS_FILE%" >nul

call %PYTHON_CMD% -c "import json, pathlib, subprocess, sys; root = pathlib.Path(r'%PACKAGE_ROOT%'); settings_path = pathlib.Path(r'%SETTINGS_FILE%'); settings = json.loads(settings_path.read_text(encoding='utf-8')); input_root = str(settings.get('input_root', '')).strip(); output_root = str(settings.get('output_root', '')).strip(); config_path = str(settings.get('config', str(root / 'config' / 'runtime.yaml'))).strip(); placeholder_input = input_root in {'', 'C:/conalog/input'}; placeholder_output = output_root in {'', 'C:/conalog/output'}; missing_input = (not placeholder_input) and (not pathlib.Path(input_root).exists()); invalid = placeholder_input or placeholder_output or missing_input; print('먼저 settings.json의 input_root/output_root를 실제 경로로 수정하십시오.') if invalid else None; subprocess.Popen(['notepad', str(settings_path)]) if invalid else None; cmd = [sys.executable, str(root / 'app' / 'run_oneclick.py'), '--input-root', input_root, '--output-root', output_root, '--config', config_path, '--include-experimental', str(settings.get('include_experimental', 'off')), '--report', str(settings.get('report', 'on'))]; raise SystemExit(0 if invalid else subprocess.call(cmd))"
if errorlevel 1 exit /b %errorlevel%
