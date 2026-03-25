import os
import select
import sys
import termios
import tty
from typing import Self


class NoEcho:
    instance: "NoEcho | None" = None

    def enable(self) -> Self:
        self.fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd)
        tty.setcbreak(self.fd)  # no echo, no enter-newline
        NoEcho.instance = self
        return self

    def disable(self) -> None:
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)
        NoEcho.instance = None

    def read_key(self, timeout: float = 0.1) -> str | None:
        """Non-blocking key read. Returns single char, 'ESC', or None on timeout."""
        ready, _, _ = select.select([self.fd], [], [], timeout)
        if not ready:
            return None
        data = os.read(self.fd, 1).decode("utf-8", errors="replace")
        if data == "\x1b":
            # Possible escape sequence — drain remaining bytes
            while select.select([self.fd], [], [], 0.02)[0]:
                os.read(self.fd, 1)
            return "ESC"
        return data

    def __enter__(self) -> Self:
        return self.enable()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.disable()
