@echo off
REM Blockchain Forensics Backend Quick Start Script for Windows

echo.
echo ============================================
echo Blockchain Forensics Backend - Quick Start
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo [1/5] Checking Python installation...
python --version
REM Check Python version - warn if 3.13+
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo Python version detected: %PYTHON_VER%
echo.
echo NOTE: If you experience Rust compilation errors with python-louvain,
echo you have two options:
echo   A) Use Python 3.11 or 3.12 instead (easier)
echo   B) Use requirements-minimal.txt (skip python-louvain)
echo.
echo OK

echo.
echo [2/5] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists
) else (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)
echo OK

echo.
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo OK

echo.
echo [4/5] Installing dependencies...
REM Upgrade pip, setuptools, and wheel first
python -m pip install --upgrade pip setuptools wheel >nul 2>&1
REM Try normal install first
pip install -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ⚠️  Standard installation failed (likely Rust compilation issue with python-louvain)
    echo.
    echo Retrying with minimal requirements (without python-louvain)...
    pip install -r requirements-minimal.txt
    if %errorlevel% neq 0 (
        echo.
        echo ❌ ERROR: Failed to install dependencies
        echo.
        echo Solutions:
        echo 1. Use Python 3.11 or 3.12 instead of 3.13+
        echo 2. Edit requirements.txt to remove python-louvain
        echo 3. Install Visual C++ Build Tools and Rust
        echo 4. Use Docker: docker build -t forensics-api . ^& docker run -p 8000:8000 forensics-api
        echo.
        echo See INSTALL_TROUBLESHOOTING.md for detailed solutions.
        pause
        exit /b 1
    )
    echo.
    echo ✓ Minimal dependencies installed successfully
    echo   Note: python-louvain not installed (uses NetworkX algorithms instead)
) else (
    echo ✓ All dependencies installed successfully
)
echo OK

echo.
echo [5/5] Starting Backend API Server...
echo.
echo ============================================
echo Backend API is starting...
echo ============================================
echo.
echo API Documentation:   http://localhost:8000/docs
echo Health Check:        http://localhost:8000/api/v1/health
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
