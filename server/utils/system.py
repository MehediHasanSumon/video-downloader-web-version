"""System utilities, external tools, and file launchers."""

import os
import sys
import shutil
import subprocess
from typing import Optional

class SystemUtils:
    """Manages system paths, external tools, and media file launchers."""

    @staticmethod
    def is_ffmpeg_available() -> bool:
        return shutil.which("ffmpeg") is not None

    @staticmethod
    def open_folder(folder_path: str):
        try:
            abs_path = os.path.abspath(folder_path)
            os.makedirs(abs_path, exist_ok=True)
            if sys.platform == "win32":
                os.startfile(abs_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", abs_path])
            else:
                subprocess.Popen(["xdg-open", abs_path])
        except Exception:
            pass

    @staticmethod
    def play_media(file_path: str):
        try:
            if not os.path.isfile(file_path):
                return
            abs_path = os.path.abspath(file_path)
            if sys.platform == "win32":
                os.startfile(abs_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", abs_path])
            else:
                subprocess.Popen(["xdg-open", abs_path])
        except Exception:
            pass
