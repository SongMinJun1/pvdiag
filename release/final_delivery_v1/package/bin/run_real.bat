@echo off
setlocal
set PACKAGE_ROOT=%~dp0..
set SETTINGS_FILE=%PACKAGE_ROOT%\bin\settings.json
if not exist "%SETTINGS_FILE%" set SETTINGS_FILE=%PACKAGE_ROOT%\bin\settings.template.json

python -c "import json, pathlib, subprocess, sys; root = pathlib.Path(r'%PACKAGE_ROOT%'); settings_path = pathlib.Path(r'%SETTINGS_FILE%'); settings = json.loads(settings_path.read_text(encoding='utf-8')); cmd = [sys.executable, str(root / 'app' / 'run_oneclick.py'), '--input-root', settings['input_root'], '--output-root', settings['output_root'], '--config', settings.get('config', str(root / 'config' / 'runtime.yaml')), '--include-experimental', settings.get('include_experimental', 'off'), '--report', settings.get('report', 'on')]; raise SystemExit(subprocess.call(cmd))"
