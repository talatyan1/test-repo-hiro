@echo off
chcp 65001 > nul
cd /d %~dp0

echo ============================================================
echo SAFE RUN START
echo ============================================================

if exist kill.switch (
    echo [STOP] kill.switch detected
    pause
    exit /b
)

set "PYTHON_EXE=.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] .venv\Scripts\python.exe not found
    pause
    exit /b
)

echo [INFO] Python:
"%PYTHON_EXE%" --version

echo [INFO] Installing dependencies...
"%PYTHON_EXE%" -m pip install --upgrade pip
"%PYTHON_EXE%" -m pip install gspread google-auth selenium

echo [INFO] Running app.py
"%PYTHON_EXE%" app.py

echo ============================================================
echo SAFE RUN END
echo ============================================================

pause