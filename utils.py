import sys
import termios
import tty
from typing import Self


class NoEcho:
    def enable(self) -> Self:
        self.fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd)
        tty.setcbreak(self.fd)  # no echo, no enter-newline
        return self

    def disable(self) -> None:
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

    def __enter__(self) -> Self:
        return self.enable()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.disable()
