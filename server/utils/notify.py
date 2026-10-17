"""Cross-platform desktop system notifications."""

import os
import sys
import shutil
import subprocess

class NotificationManager:
    """Sends native desktop notifications on download completion."""

    @staticmethod
    def notify(title: str, message: str):
        try:
            if sys.platform.startswith("linux"):
                if shutil.which("notify-send"):
                    subprocess.Popen(
                        ["notify-send", "-a", "Video Downloader", title, message],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
            elif sys.platform == "darwin":
                if shutil.which("osascript"):
                    script = f'display notification "{message}" with title "{title}"'
                    subprocess.Popen(
                        ["osascript", "-e", script],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
            elif sys.platform == "win32":
                # PowerShell toast/balloon notification
                ps_cmd = (
                    f'[reflection.assembly]::loadwithpartialname("System.Windows.Forms");'
                    f'$notify = new-object system.windows.forms.notifyicon;'
                    f'$notify.icon = [system.drawing.systemicons]::information;'
                    f'$notify.visible = $true;'
                    f'$notify.showballoontip(5000, "{title}", "{message}", [system.windows.forms.tooltipicon]::None)'
                )
                subprocess.Popen(
                    ["powershell", "-WindowStyle", "Hidden", "-Command", ps_cmd],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except Exception:
            pass
