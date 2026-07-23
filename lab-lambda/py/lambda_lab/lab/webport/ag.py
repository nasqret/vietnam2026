"""Browser port of the desktop ``ag`` command — AlphaGeometry proof replay.

Replays the baked DD+AR demo proofs frozen in ``data_ag.py`` (the desktop
reads them from ``lambda_lab/proofs/alphageometry/*.yaml``).

- ``ag`` lists the available demos.
- ``ag <name>`` replays a proof: problem, ASCII diagram, LM auxiliary
  construction, the DD+AR steps, and the conclusion.

Graceful degradation: the desktop replayer pauses for ENTER between steps;
the browser build is line-oriented, so the whole replay is printed at once
(a one-line notice says so). Everything else follows the desktop rendering:
one panel per step with premises / rule / conclusion / why rows, the
conclusion highlighted.
"""

from __future__ import annotations

from . import _ansi as A
from .data_ag import PROOFS

_RULE_WIDTH = 72
_STEP_KEYS = ("premises", "rule", "conclusion", "why")
_LABEL_W = 10  # len("conclusion")


def _rule_line(title: str) -> str:
    tw = A.display_width(title)
    left = max((_RULE_WIDTH - tw - 2) // 2, 2)
    right = max(_RULE_WIDTH - tw - 2 - left, 2)
    return A.dim("─" * left) + " " + A.bold(A.magenta(title)) + " " + A.dim("─" * right)


def _panel(text: str, title: str, border_fn) -> list[str]:
    return A.box(text.splitlines() or [""], title=title, border_fn=border_fn, pad_x=2)


def _step_panel(i: int, step: dict) -> list[str]:
    rows: list[str] = []
    for key in _STEP_KEYS:
        val = step.get(key)
        if val is None:
            continue
        items = [str(v) for v in val] if isinstance(val, list) else [str(val)]
        style = A.magenta if key == "conclusion" else (lambda s: s)
        rows.append(A.dim(key.ljust(_LABEL_W)) + "  " + style(items[0]))
        rows.extend(" " * (_LABEL_W + 2) + style(item) for item in items[1:])
    return A.box(rows, title=A.bold(f"DD+AR step #{i}"), border_fn=A.dim, pad_x=2)


def _list_demos() -> str:
    width = max(len(name) for name in PROOFS)
    rows = [A.bold(A.magenta("Available demos")) + A.dim(" · AlphaGeometry DD+AR replays")]
    for name in sorted(PROOFS):
        rows.append("  " + A.green(name.ljust(width)) + "  " + A.dim(PROOFS[name]["title"]))
    rows.append("")
    rows.append(A.dim("Replay one with ") + A.yellow("ag <name>") + A.dim(", e.g. ") + A.yellow("ag angle_bisector") + A.dim("."))
    return A.lines(*rows)


def _replay(name: str) -> str:
    data = PROOFS[name]
    rows: list[str] = [_rule_line(data.get("title", name))]
    rows.append(A.dim("(the desktop replayer pauses for ENTER between steps; the browser prints the whole replay)"))
    if "problem" in data:
        rows.extend(_panel(data["problem"], A.bold("Problem"), A.cyan))
    if "diagram" in data:
        rows.extend(_panel(data["diagram"], A.bold("Diagram"), A.dim))
    if "aux" in data:
        aux = data["aux"]
        if isinstance(aux, list):
            aux = "\n".join(aux)
        rows.extend(_panel(aux, A.bold("Auxiliary construction (LM)"), A.yellow))
    for i, step in enumerate(data.get("steps", []), start=1):
        rows.extend(_step_panel(i, step))
    if "conclusion" in data:
        rows.extend(_panel(data["conclusion"], A.bold(A.green("Conclusion")), A.green))
    return A.lines(*rows)


def handle(arg: str, state: dict) -> str:
    """Run ``ag [name]``. Non-interactive; ``state`` is unused."""
    del state
    key = (arg or "").strip()
    if not key:
        return _list_demos()
    if key not in PROOFS:
        return A.yellow(f"Unknown demo: {key}. Available: {', '.join(sorted(PROOFS))}")
    return _replay(key)
