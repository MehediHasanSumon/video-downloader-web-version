"""Application logging configuration and log viewer."""

import os
import re
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box
from core.config import LOG_FILE

class AppLogger:
    """Manages rotating application logging to disk and debug streams."""

    _instance: Optional[logging.Logger] = None

    @classmethod
    def get_logger(cls) -> logging.Logger:
        if cls._instance is None:
            logger = logging.getLogger("media_downloader")
            logger.setLevel(logging.DEBUG)
            if not logger.handlers:
                handler = RotatingFileHandler(
                    LOG_FILE,
                    maxBytes=3 * 1024 * 1024,
                    backupCount=3,
                    encoding="utf-8",
                )
                handler.setLevel(logging.DEBUG)
                formatter = logging.Formatter(
                    "[%(asctime)s] [%(levelname)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
                handler.setFormatter(formatter)
                logger.addHandler(handler)
            cls._instance = logger
        return cls._instance


class YtDlpLogger:
    """Custom logger routing yt-dlp internal messages to the rotating file logger."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.errors: List[str] = []

    def debug(self, msg: str):
        if msg.startswith("[debug] "):
            self.logger.debug(msg)

    def info(self, msg: str):
        self.logger.info(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        clean_msg = re.sub(r'\x1b\[[0-9;]*m', '', str(msg)).strip()
        if clean_msg:
            self.errors.append(clean_msg)
        self.logger.error(msg)


def view_recent_logs(console: Console, lines: int = 25, max_lines: Optional[int] = None):
    """Displays recent log entries from the log file in a clean Rich panel."""
    if max_lines is not None:
        lines = max_lines
    if not os.path.isfile(LOG_FILE):
        console.print(f"  [dim yellow]No log file found at {LOG_FILE}[/dim yellow]\n")
        return

    try:
        with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()

        recent = all_lines[-lines:] if len(all_lines) > lines else all_lines
        log_text = "".join(recent).strip()

        body = Text.from_ansi(log_text) if log_text else Text.from_markup("[dim]Log file is currently empty[/dim]")

        panel = Panel(
            body,
            title=f"[bold #27d2ed] Recent Logs ({os.path.basename(LOG_FILE)}) [/bold #27d2ed]",
            subtitle=f"[dim]Showing last {len(recent)} entries • Location: {LOG_FILE}[/dim]",
            border_style="#27d2ed",
            box=box.ROUNDED,
            padding=(1, 2),
        )
        console.print()
        console.print(panel)
        console.print()
    except Exception as e:
        console.print(f"  [bold red]Could not read log file: {e}[/bold red]\n")
