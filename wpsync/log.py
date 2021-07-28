from datetime import datetime
from typing import TextIO, Union
from pathlib import Path
import sys

from crayons import blue, cyan, yellow, red, green, ColoredString


class AbstractLogger:
    """Logger base class
    log levels:
    0: nothing
    1: errors
    2: errors, warnings
    3: errors, warnings, infos
    4: everything"""

    def __init__(self, level: int = 2):
        if level < 0 or level > 4:
            raise ValueError("Level must be between 0 and 4!")
        else:
            self.level = level

    def do_log_title(self) -> bool:
        return self.level > 3

    def do_log_step(self) -> bool:
        return self.level > 3

    def do_log_error(self) -> bool:
        return self.level > 0

    def do_log_warning(self) -> bool:
        return self.level > 1

    def do_log_info(self) -> bool:
        return self.level > 2

    def do_log_success(self) -> bool:
        return self.level > 3

    def title(self, message: str):
        raise NotImplementedError()

    def step(self, message: str):
        raise NotImplementedError()

    def error(self, message: str):
        raise NotImplementedError()

    def warning(self, message: str):
        raise NotImplementedError()

    def info(self, message: str):
        raise NotImplementedError()

    def success(self, message: str):
        raise NotImplementedError()


class TermLogger(AbstractLogger):
    def format(self, string: str, always: bool = False, bold: bool = False):
        return ColoredString("RESET", string, always_color=always, bold=bold)

    def print(self, formatted_string: str, stderr: bool = False):
        if stderr:
            print(formatted_string, file=sys.stderr)
        else:
            print(formatted_string)

    def title(self, message: str):
        if self.do_log_title():
            self.print(f'{blue("➙")} {self.format(message, bold=True)}')

    def step(self, message: str):
        if self.do_log_step():
            self.print(self.format(f"• {message}"))

    def error(self, message: str):
        if self.do_log_error():
            self.print(f'{red("✗")} {red(message, bold=True)}', stderr=True)

    def warning(self, message: str):
        if self.do_log_warning():
            self.print(f'{yellow("⚠")} {self.format(message)}', stderr=True)

    def info(self, message: str):
        if self.do_log_info():
            self.print(f'{self.format("ℹ")} {self.format(message)}')

    def success(self, message: str):
        if self.do_log_success():
            self.print(f'{green("✔")} {self.format(message, bold=True)}')


class FileLogger(AbstractLogger):
    def __init__(self, path: str, level: int = 0):
        super().__init__(level=level)
        self.path = path

    def timestamp(self) -> str:
        return "[" + datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "]"

    def print(self, string: str):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(string + "\n")

    def log(self, message: str):
        self.print(self.timestamp() + " " + message)

    def title(self, message: str):
        if self.do_log_title():
            self.log("-> " + message)

    def step(self, message: str):
        if self.do_log_step():
            self.log(" - " + message)

    def error(self, message: str):
        if self.do_log_error():
            self.log(" x " + message)

    def warning(self, message: str):
        if self.do_log_warning():
            self.log(" ! " + message)

    def info(self, message: str):
        if self.do_log_info():
            self.log(" i " + message)

    def success(self, message: str):
        if self.do_log_success():
            self.log(" + " + message)
