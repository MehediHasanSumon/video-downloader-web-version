@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title Video Downloader Pro - Backend Server
cd /d "%~dp0"

echo ===================================================
echo   Video Downloader Pro - Backend Server (Windows)
echo ===================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH.
    pause
    exit /b 1
)

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist "..\venv\Scripts\activate.bat" (
    call ..\venv\Scripts\activate.bat
) else (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
)

python -c "import yt_dlp; import fastapi; import uvicorn" >nul 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Installing requirements...
    pip install -r requirements.txt
)

if exist "%~dp0ffmpeg\bin" (
    set "PATH=%~dp0ffmpeg\bin;%PATH%"
) else if exist "%~dp0..\ffmpeg\bin" (
    set "PATH=%~dp0..\ffmpeg\bin;%PATH%"
)

where ffmpeg >nul 2>nul
if %errorlevel% neq 0 (
    if exist "setup_ffmpeg.py" (
        python setup_ffmpeg.py
        if exist "%~dp0ffmpeg\bin" set "PATH=%~dp0ffmpeg\bin;%PATH%"
    )
)

python main.py %*
pause
