@echo off
if "%PACKAGE_ROOT%"=="" (
  echo PACKAGE_ROOT 환경변수가 비어 있습니다.
  exit /b 1
)

set "PYTHON_CMD=%PACKAGE_ROOT%\runtime\windows_x64\python\python.exe"
if exist "%PYTHON_CMD%" (
  set "PYTHON_RUNTIME_KIND=embedded"
  exit /b 0
)

where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON_CMD=py -3"
  set "PYTHON_RUNTIME_KIND=system_py_launcher"
  exit /b 0
)

where python >nul 2>nul
if errorlevel 1 (
  echo Python 3를 찾지 못했습니다. package\runtime\windows_x64\python\python.exe 또는 시스템 Python 3를 준비하십시오.
  exit /b 1
)

set "PYTHON_CMD=python"
set "PYTHON_RUNTIME_KIND=system_python"
exit /b 0
