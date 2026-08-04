import shutil
import os


COLORS = {
    'red': '31',
    'green': '32',
    'yellow': '33',
    'blue': '34',
    'magenta': '35',
    'cyan': '36',
    'white': '37',
    'bright_red': '91',
    'bright_green': '92',
    'bright_yellow': '93',
    'bright_cyan': '96',
    'bold': '1',
    'dim': '2',
    'reset': '0',
}


def _color(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def red(text: str) -> str:
    return _color(COLORS['red'], text)


def green(text: str) -> str:
    return _color(COLORS['green'], text)


def yellow(text: str) -> str:
    return _color(COLORS['yellow'], text)


def blue(text: str) -> str:
    return _color(COLORS['blue'], text)


def cyan(text: str) -> str:
    return _color(COLORS['cyan'], text)


def magenta(text: str) -> str:
    return _color(COLORS['magenta'], text)


def bold(text: str) -> str:
    return _color(COLORS['bold'], text)


def dim(text: str) -> str:
    return _color(COLORS['dim'], text)


def bright_red(text: str) -> str:
    return _color(COLORS['bright_red'], text)


def bright_green(text: str) -> str:
    return _color(COLORS['bright_green'], text)


def bright_yellow(text: str) -> str:
    return _color(COLORS['bright_yellow'], text)


def print_colored(text, color='white'):
    code = COLORS.get(color, '37')
    print(f"\033[{code}m{text}\033[0m")


def format_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return dim('(empty)')

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    width = shutil.get_terminal_size().columns if hasattr(shutil, 'get_terminal_size') else 120

    def _truncate(text: str, max_w: int) -> str:
        s = str(text)
        return s if len(s) <= max_w else s[:max_w - 3] + '...'

    sep = '  '
    total = sum(col_widths) + len(sep) * (len(headers) - 1)
    if total > width:
        available = width - len(sep) * (len(headers) - 1) - 4
        per_col = max(8, available // len(headers))
        col_widths = [per_col] * len(headers)

    lines = []
    header_line = sep.join(_truncate(cyan(h), w) for h, w in zip(headers, col_widths))
    lines.append(header_line)
    lines.append(dim('─' * min(width, total + 10)))

    for row in rows:
        line = sep.join(_truncate(str(c), w) for c, w in zip(row, col_widths))
        lines.append(line)

    return '\n'.join(lines)


def format_info_card(info: dict) -> str:
    label_width = max(len(k) for k in info.keys()) + 2
    lines = []
    lines.append(bold(blue('  Agent Info')))
    lines.append(dim('  ' + '─' * 30))
    for key, value in info.items():
        label = f'  {key}:'.ljust(label_width)
        lines.append(f'{cyan(label)}{value}')
    return '\n'.join(lines)


def highlight_output(text: str) -> str:
    result = []
    for line in text.split('\n'):
        if line.startswith('[+]'):
            result.append(green(line))
        elif line.startswith('[-]'):
            result.append(red(line))
        elif line.startswith('[!]'):
            result.append(bright_yellow(line))
        elif line.startswith('[*]'):
            result.append(cyan(line))
        else:
            result.append(line)
    return '\n'.join(result)
