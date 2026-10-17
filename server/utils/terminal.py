"""Cross-platform terminal handling, key listener, and screen clear."""

import os
import sys
import atexit
import signal

def cleanup_terminal():
    """Guarantees cursor restoration and clean terminal buffer across Linux, macOS, and Windows."""
    try:
        sys.stdout.write("\033[?25h")  # Ensure cursor is visible
        sys.stdout.flush()
    except Exception:
        pass
    if sys.platform != "win32":
        try:
            import termios
            if sys.stdin.isatty():
                termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
        except Exception:
            pass

def clear_terminal():
    """Completely clears the terminal screen and wipes scrollback buffer (prevents empty scroll space)."""
    if sys.platform == "win32":
        os.system("cls")
    else:
        # \033[H: Home cursor (row 1, col 1)
        # \033[2J: Clear visible screen
        # \033[3J: Wipe entire terminal scrollback buffer (GNOME Terminal, xterm, Kitty, Alacritty)
        sys.stdout.write("\033[H\033[2J\033[3J")
        sys.stdout.flush()

atexit.register(cleanup_terminal)

def _sigterm_handler(sig, frame):
    cleanup_terminal()
    sys.exit(0)

try:
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _sigterm_handler)
except Exception:
    pass


def read_key() -> str:
    """
    Reads a single keypress or key event across Windows and Linux/Unix.
    Returns: 'UP', 'DOWN', 'LEFT', 'RIGHT', 'ENTER', 'SPACE', 'CTRL_C', or character string.
    """
    if sys.platform == "win32":
        try:
            import msvcrt
            key = msvcrt.getch()
            if key in (b'\x00', b'\xe0'):
                sub_key = msvcrt.getch()
                if sub_key in (b'H', b'\x48'):
                    return "UP"
                elif sub_key in (b'P', b'\x50'):
                    return "DOWN"
                elif sub_key in (b'K', b'\x4b'):
                    return "LEFT"
                elif sub_key in (b'M', b'\x4d'):
                    return "RIGHT"
                return ""
            elif key == b'\x1b':
                if msvcrt.kbhit():
                    ch2 = msvcrt.getch()
                    if ch2 in (b'[', b'O'):
                        if msvcrt.kbhit():
                            ch3 = msvcrt.getch()
                            if ch3 == b'A':
                                return "UP"
                            elif ch3 == b'B':
                                return "DOWN"
                            elif ch3 == b'C':
                                return "RIGHT"
                            elif ch3 == b'D':
                                return "LEFT"
                return "ESC"
            elif key in (b'\r', b'\n'):
                return "ENTER"
            elif key == b' ':
                return "SPACE"
            elif key == b'\x08':
                return "BACKSPACE"
            elif key == b'\x03':
                return "CTRL_C"
            else:
                return key.decode("utf-8", errors="ignore")
        except Exception:
            return ""
    else:
        try:
            import tty
            import termios
            import select

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = os.read(fd, 1)
                if not ch:
                    return ""
                if ch == b'\x1b':
                    rlist, _, _ = select.select([fd], [], [], 0.05)
                    if rlist:
                        seq = os.read(fd, 8)
                        if not seq:
                            return "ESC"
                        if seq in (b'[', b'O'):
                            rlist2, _, _ = select.select([fd], [], [], 0.05)
                            if rlist2:
                                seq += os.read(fd, 8)
                        if seq.endswith(b'A') and (b'[' in seq or b'O' in seq):
                            return "UP"
                        elif seq.endswith(b'B') and (b'[' in seq or b'O' in seq):
                            return "DOWN"
                        elif seq.endswith(b'C') and (b'[' in seq or b'O' in seq):
                            return "RIGHT"
                        elif seq.endswith(b'D') and (b'[' in seq or b'O' in seq):
                            return "LEFT"
                        return ""
                    return "ESC"
                elif ch in (b'\r', b'\n'):
                    return "ENTER"
                elif ch == b' ':
                    return "SPACE"
                elif ch in (b'\x7f', b'\x08'):
                    return "BACKSPACE"
                elif ch == b'\x03':
                    return "CTRL_C"
                else:
                    return ch.decode("utf-8", errors="ignore")
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception:
            return ""
