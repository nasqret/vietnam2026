"""Shared raw-ANSI helpers for the browser webport modules.

Mirrors the helper idiom of the browser driver (``py/driver.py``): colours
are raw ANSI escape strings, ``NL = "\\r\\n"``, and multi-line output is a
single string of rows joined with ``NL``. Adds a small box renderer used to
approximate the desktop Rich panels with pure stdlib box-drawing characters.
"""

from __future__ import annotations

import re
from typing import Callable, List, Optional, Sequence

RESET = "\x1b[0m"


def _c(s: str, code: str) -> str:
    return f"\x1b[{code}m{s}{RESET}"


def bold(s: str) -> str: return _c(s, "1")
def dim(s: str) -> str: return _c(s, "2")
def green(s: str) -> str: return _c(s, "92")
def cyan(s: str) -> str: return _c(s, "96")
def yellow(s: str) -> str: return _c(s, "93")
def magenta(s: str) -> str: return _c(s, "95")
def red(s: str) -> str: return _c(s, "91")
def blue(s: str) -> str: return _c(s, "94")


NL = "\r\n"

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def lines(*rows: str) -> str:
    return NL.join(rows)


def strip_ansi(s: str) -> str:
    return _ANSI_RE.sub("", s)


def _wide(ch: str) -> bool:
    """True for characters xterm.js renders as two cells (emoji, CJK)."""
    cp = ord(ch)
    return (
        0x1F300 <= cp <= 0x1FAFF
        or 0x2E80 <= cp <= 0xA4CF
        or 0xAC00 <= cp <= 0xD7A3
        or 0xF900 <= cp <= 0xFAFF
        or 0xFE30 <= cp <= 0xFE4F
        or 0xFF00 <= cp <= 0xFF60
        or 0xFFE0 <= cp <= 0xFFE6
    )


def display_width(s: str) -> int:
    return sum(2 if _wide(ch) else 1 for ch in strip_ansi(s))


def box(
    content: Sequence[str],
    *,
    title: str = "",
    border_fn: Optional[Callable[[str], str]] = None,
    pad_x: int = 1,
    pad_y: int = 0,
) -> List[str]:
    """Draw a rounded box (Rich-panel lookalike) around already-styled lines.

    ``content`` lines may contain ANSI escapes; alignment uses the visible
    display width. Returns the list of rendered rows.
    """
    bf = border_fn or (lambda s: s)
    body = [""] * pad_y + list(content) + [""] * pad_y
    inner = max([display_width(row) for row in body] + [display_width(title)] + [1])
    width = inner + 2 * pad_x
    if title:
        tw = display_width(title)
        left = max((width - tw - 2) // 2, 0)
        right = max(width - tw - 2 - left, 0)
        top = bf("╭" + "─" * left) + " " + title + " " + bf("─" * right + "╮")
    else:
        top = bf("╭" + "─" * width + "╮")
    rows = [top]
    for row in body:
        fill = " " * (inner - display_width(row))
        rows.append(bf("│") + " " * pad_x + row + fill + " " * pad_x + bf("│"))
    rows.append(bf("╰" + "─" * width + "╯"))
    return rows
