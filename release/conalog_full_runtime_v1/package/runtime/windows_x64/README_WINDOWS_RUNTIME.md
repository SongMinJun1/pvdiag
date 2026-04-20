# Windows Portable Runtime

이 폴더는 `conalog_full_runtime_v1` USB pack이 Windows에서 별도 Python 설치 없이 실행되도록 포함한 portable runtime 자산입니다.

- Embedded Python: `3.11.9`
- Primary packages: `numpy==2.3.4, pandas==2.3.3, tqdm==4.67.1, torch==2.9.1`
- Wrapper는 `runtime\windows_x64\python\python.exe`를 먼저 찾고, 없을 때만 시스템 Python을 찾습니다.
