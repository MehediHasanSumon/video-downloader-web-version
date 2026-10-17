#!/usr/bin/env bash
# ====================================================================
#  Universal Media Downloader Pro - Web GUI Launcher (Linux & macOS)
# ====================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

OS_TYPE="$(uname -s)"
if [ "$OS_TYPE" = "Darwin" ]; then
    OS_NAME="macOS"
else
    OS_NAME="Linux"
fi

echo -e "${CYAN}===================================================${NC}"
echo -e "${BOLD}  Video Downloader Pro - Web GUI ($OS_NAME Launcher) ${NC}"
echo -e "${CYAN}===================================================${NC}"
echo ""

# 1. Check Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}[ERROR] Python 3 is not installed or not available in PATH.${NC}"
    exit 1
fi

# 2. Check Virtual Environment
if [ -f "server/venv/bin/activate" ]; then
    source server/venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "../venv/bin/activate" ]; then
    echo -e "${CYAN}[INFO]${NC} Using shared workspace virtual environment..."
    source ../venv/bin/activate
else
    echo -e "${CYAN}[INFO]${NC} Creating virtual environment in server/venv..."
    python3 -m venv server/venv
    source server/venv/bin/activate
fi

# 3. Check Python dependencies
if ! python3 -c "import yt_dlp; import fastapi; import uvicorn" >/dev/null 2>&1; then
    echo -e "${CYAN}[INFO]${NC} Installing dependencies from server/requirements.txt..."
    pip install -r server/requirements.txt
fi

# 4. Check FFmpeg
if [ -d "$SCRIPT_DIR/server/ffmpeg/bin" ]; then
    export PATH="$SCRIPT_DIR/server/ffmpeg/bin:$PATH"
elif [ -d "$SCRIPT_DIR/ffmpeg/bin" ]; then
    export PATH="$SCRIPT_DIR/ffmpeg/bin:$PATH"
elif [ -d "$SCRIPT_DIR/../ffmpeg/bin" ]; then
    export PATH="$SCRIPT_DIR/../ffmpeg/bin:$PATH"
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
    if [ -f "server/setup_ffmpeg.py" ]; then
        python3 server/setup_ffmpeg.py
        if [ -d "$SCRIPT_DIR/server/ffmpeg/bin" ]; then
            export PATH="$SCRIPT_DIR/server/ffmpeg/bin:$PATH"
        fi
    fi
fi

# 5. Check if frontend pre-built dist exists; if missing and npm is available, build it
if [ ! -d "frontend/dist" ] && [ -f "frontend/package.json" ]; then
    if command -v npm >/dev/null 2>&1; then
        echo -e "${CYAN}[INFO]${NC} Building frontend React application..."
        (cd frontend && npm install && npm run build)
    fi
fi

python3 server/main.py "$@"
