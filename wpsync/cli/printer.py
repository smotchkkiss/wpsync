import sys
from crayons import blue, cyan, yellow, red, green, ColoredString


class Printer:
    def __init__(self, quiet):
        self.quiet = quiet

    def format(self, string, always=False, bold=False):
        return ColoredString("RESET", string, always_color=always, bold=bold)

    def print(self, formatted_string, stderr=False):
        if not stderr and not self.quiet:
            print(formatted_string)
        if stderr:
            print(formatted_string, file=sys.stderr)

    def title(self, message):
        self.print(f'{blue("➙")} {self.format(message, bold=True)}')

    def step(self, message):
        self.print(self.format(f"• {message}"))

    def error(self, message):
        self.print(f'{red("✗")} {red(message, bold=True)}', stderr=True)

    def warn(self, message):
        self.print(f'{yellow("⚠")} {self.format(message)}', stderr=True)

    def info(self, message):
        self.print(f'{self.format("ℹ")} {self.format(message)}')

    def success(self, message):
        self.print(f'{green("✔")} {self.format(message, bold=True)}')
