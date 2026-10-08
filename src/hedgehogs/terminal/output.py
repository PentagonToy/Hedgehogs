"""Small portable helpers for scientific status output."""

import html
import os
import shutil
import sys
from typing import TextIO

from matplotlib.colors import to_hex, to_rgb

from ..core.environment import _is_jupyter


_TONES = {
    "info": "#0072B2",
    "success": "#009E73",
    "warning": "#E69F00",
    "error": "#D55E00",
    "muted": "#777777",
}


def _supports_colour(stream: TextIO) -> bool:
    return bool(stream.isatty() and "NO_COLOR" not in os.environ and os.environ.get("TERM") != "dumb")


def echo(message: object, *, tone: str | None = None, color: str | None = None, bold: bool = False, file: TextIO | None = None) -> None:
    """Write a status message using semantic or explicit colour when supported."""
    if tone is not None and tone not in _TONES:
        raise ValueError(f"Unknown tone {tone!r}; expected one of {tuple(_TONES)}.")
    selected = color or (_TONES[tone] if tone else None)
    if selected is not None:
        selected = to_hex(selected)
    text = str(message)
    stream = file or sys.stdout
    if _is_jupyter() and file is None:
        from IPython.display import HTML, display
        styles = []
        if selected:
            styles.append(f"color:{selected}")
        if bold:
            styles.append("font-weight:bold")
        display(HTML(f'<span style="{";".join(styles)}">{html.escape(text)}</span>'))
        return
    if selected and _supports_colour(stream):
        red, green, blue = (round(channel * 255) for channel in to_rgb(selected))
        weight = "1;" if bold else ""
        text = f"\033[{weight}38;2;{red};{green};{blue}m{text}\033[0m"
    elif bold and _supports_colour(stream):
        text = f"\033[1m{text}\033[0m"
    print(text, file=stream)


def rule(title: str = "", *, width: int | None = None, file: TextIO | None = None) -> None:
    """Write a compact horizontal separator."""
    stream = file or sys.stdout
    available = width or shutil.get_terminal_size((80, 20)).columns
    label = f" {title} " if title else ""
    remaining = max(0, available - len(label))
    left = remaining // 2
    print("─" * left + label + "─" * (remaining - left), file=stream)
