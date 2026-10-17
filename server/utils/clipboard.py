"""Safe clipboard detection across Linux, Windows, and macOS."""

import sys
import shutil
import subprocess
from typing import Optional

class ClipboardHelper:
    """Reads system clipboard safely across environments."""

    @staticmethod
    def get_clipboard_text() -> Optional[str]:
        # 1. Try Wayland wl-paste on Linux
        if sys.platform.startswith("linux") and shutil.which("wl-paste"):
            try:
                res = subprocess.run(
                    ["wl-paste", "--no-newline"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=0.2,
                )
                if res.returncode == 0 and res.stdout:
                    return res.stdout.strip()
            except Exception:
                pass

        # 2. Try xclip on Linux (X11)
        if sys.platform.startswith("linux") and shutil.which("xclip"):
            try:
                res = subprocess.run(
                    ["xclip", "-selection", "clipboard", "-o"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=0.2,
                )
                if res.returncode == 0 and res.stdout:
                    return res.stdout.strip()
            except Exception:
                pass

        # 3. Try xsel on Linux (X11)
        if sys.platform.startswith("linux") and shutil.which("xsel"):
            try:
                res = subprocess.run(
                    ["xsel", "--clipboard", "--output"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=0.2,
                )
                if res.returncode == 0 and res.stdout:
                    return res.stdout.strip()
            except Exception:
                pass

        # 4. Try macOS pbpaste
        if sys.platform == "darwin" and shutil.which("pbpaste"):
            try:
                res = subprocess.run(
                    ["pbpaste"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=0.2,
                )
                if res.returncode == 0 and res.stdout:
                    return res.stdout.strip()
            except Exception:
                pass

        # 5. Try pyperclip if available
        try:
            import pyperclip
            val = pyperclip.paste()
            if val:
                return val.strip()
        except Exception:
            pass

        # 6. Safe Tkinter fallback with guaranteed resource cleanup
        try:
            import tkinter
            root = tkinter.Tk()
            try:
                root.withdraw()
                text = root.clipboard_get()
                if text:
                    return str(text).strip()
            finally:
                root.destroy()
        except Exception:
            pass

        return None

    @classmethod
    def get_media_url_candidate(cls) -> Optional[str]:
        """Returns clipboard text if it looks like a media link."""
        text = cls.get_clipboard_text()
        if not text:
            return None
        text_lower = text.lower()
        if any(term in text_lower for term in ["youtube.com", "youtu.be", "facebook.com", "fb.watch", "instagram.com", "tiktok.com", "twitter.com", "x.com"]):
            if text.startswith("http://") or text.startswith("https://"):
                return text
            return f"https://{text}"
        return None
