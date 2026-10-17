#!/usr/bin/env python3
"""
====================================================================
 Universal Video & Audio Downloader Pro - Web GUI
 Powered by FastAPI, React, yt-dlp, and FFmpeg
 Developed by Md Mehedi Hasan
====================================================================
"""

import sys
import os
import argparse
import webbrowser
import threading
import time
import ctypes

# Enable UTF-8 and ANSI colors / Virtual Terminal Processing on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

    try:
        kernel32 = ctypes.windll.kernel32
        h_stdout = kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        if kernel32.GetConsoleMode(h_stdout, ctypes.byref(mode)):
            kernel32.SetConsoleMode(h_stdout, mode.value | 0x0004)
    except Exception:
        pass

# Ensure server and project root are in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
for p in (SCRIPT_DIR, PROJECT_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

def main():
    parser = argparse.ArgumentParser(description="Video Downloader Web GUI Server")
    parser.add_argument("--host", default="127.0.0.1", help="Web host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="Web port (default: 5000)")
    parser.add_argument("--no-browser", action="store_true", help="Don't auto-open browser")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload on code changes")
    args = parser.parse_args()

    try:
        import uvicorn
        from fastapi import FastAPI
    except ImportError:
        print("\n\033[91m[ERROR] Required packages are missing!\033[0m")
        print("Install them using: pip install -r requirements.txt\n")
        return 1

    url = f"http://{args.host}:{args.port}"
    print(f"\n\033[1;36m╭──────────────────────────────────────────────────────────╮\033[0m")
    print(f"\033[1;36m│\033[0m           \033[1;35mVIDEO DOWNLOADER PRO - WEB GUI\033[0m                 \033[1;36m│\033[0m")
    print(f"\033[1;36m│\033[0m             Developed by Md Mehedi Hasan                 \033[1;36m│\033[0m")
    print(f"\033[1;36m╰──────────────────────────────────────────────────────────╯\033[0m\n")
    print(f"  \033[1;32m➜ Web UI:\033[0m   \033[4;36m{url}\033[0m")
    print(f"  \033[90m➜ Docs:\033[0m     \033[90m{url}/docs\033[0m")
    print(f"  \033[90m➜ Press CTRL+C to stop the server\033[0m\n")

    if not args.no_browser:
        def open_browser():
            time.sleep(1.2)
            try:
                webbrowser.open(url)
            except Exception:
                pass
        threading.Thread(target=open_browser, daemon=True).start()

    try:
        uvicorn.run("app:app", host=args.host, port=args.port, app_dir=SCRIPT_DIR, reload=args.reload, log_level="info")
        return 0
    except KeyboardInterrupt:
        print("\n\033[93mWeb server stopped by user.\033[0m\n")
        return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\033[93mApplication terminated by user.\033[0m\n")
        sys.exit(0)
