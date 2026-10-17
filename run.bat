@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title Video Downloader Pro - Web GUI
cd /d "%~dp0"

echo ===================================================
echo   Video Downloader Pro - Web GUI (Windows)
echo ===================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH.
    pause
    exit /b 1
)

if exist "server\venv\Scripts\activate.bat" (
    call server\venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist "..\venv\Scripts\activate.bat" (
    call ..\venv\Scripts\activate.bat
) else (
    echo [INFO] Creating virtual environment in server\venv...
    python -m venv server\venv
    call server\venv\Scripts\activate.bat
)

python -c "import yt_dlp; import fastapi; import uvicorn" >nul 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Installing requirements from server\requirements.txt...
    pip install -r server\requirements.txt
)

if exist "%~dp0server\ffmpeg\bin" (
    set "PATH=%~dp0server\ffmpeg\bin;%PATH%"
) else if exist "%~dp0ffmpeg\bin" (
    set "PATH=%~dp0ffmpeg\bin;%PATH%"
) else if exist "%~dp0..\ffmpeg\bin" (
    set "PATH=%~dp0..\ffmpeg\bin;%PATH%"
)

where ffmpeg >nul 2>nul
if %errorlevel% neq 0 (
    if exist "server\setup_ffmpeg.py" (
        python server\setup_ffmpeg.py
        if exist "%~dp0server\ffmpeg\bin" set "PATH=%~dp0server\ffmpeg\bin;%PATH%"
    )
)

if not exist "frontend\dist" (
    where npm >nul 2>nul
    if %errorlevel% equ 0 (
        echo [INFO] Building frontend React application...
        pushd frontend
        call npm install
        call npm run build
        popd
    )
)

python server\main.py %*
pause
