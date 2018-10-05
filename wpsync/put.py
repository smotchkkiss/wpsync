from crayons import blue, cyan, yellow, red, green, ColoredString


def normal(string, always=False, bold=False):
    return ColoredString('RESET', string, always_color=always, bold=bold)


def title(message):
    print(f'{blue("➙")} {normal(message, bold=True)}')


def step(message):
    print(normal(f'• {message}'))


def error(message):
    print(f'{red("✗")} {red(message, bold=True)}', file=sys.stderr)


def warn(message):
    print(f'{yellow("⚠")} {normal(message)}')


def info(message):
    print(f'{normal("ℹ")} {normal(message)}')


def success(message):
    print(f'{green("✔")} {normal(message, bold=True)}')
