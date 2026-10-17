#!/usr/bin/env bash
# ====================================================================
#  Video Downloader Pro - Server Launcher (Linux & macOS)
# ====================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

echo -e "${CYAN}===================================================${NC}"
echo -e "${BOLD}  Video Downloader Pro - Backend Server Launcher    ${NC}"
echo -e "${CYAN}===================================================${NC}"
echo ""

# 1. Check Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}[ERROR] Python 3 is not installed or not in PATH.${NC}"
    exit 1
fi

# 2. Virtual Environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
else
    echo -e "${CYAN}[INFO]${NC} Creating virtual environment in venv..."
    python3 -m venv venv
    source venv/bin/activate
fi

# 3. Check Python dependencies
if ! python3 -c "import yt_dlp; import fastapi; import uvicorn" >/dev/null 2>&1; then
    echo -e "${CYAN}[INFO]${NC} Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
fi

# 4. Check FFmpeg
if [ -d "$SCRIPT_DIR/ffmpeg/bin" ]; then
    export PATH="$SCRIPT_DIR/ffmpeg/bin:$PATH"
elif [ -d "$SCRIPT_DIR/../ffmpeg/bin" ]; then
    export PATH="$SCRIPT_DIR/../ffmpeg/bin:$PATH"
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
    if [ -f "setup_ffmpeg.py" ]; then
        python3 setup_ffmpeg.py
        if [ -d "$SCRIPT_DIR/ffmpeg/bin" ]; then
            export PATH="$SCRIPT_DIR/ffmpeg/bin:$PATH"
        fi
    fi
fi

python3 main.py "$@"
