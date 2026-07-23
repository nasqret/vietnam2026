"""Browser port of the desktop ``alligators`` command.

Bret Victor's Alligator Eggs rendering of λ-terms, translated from the
desktop Rich renderer (``lambda_lab/lab/alligators.py`` +
``lambda_lab/lab/commands/alligators.py``) into raw ANSI box art:

- **Hungry alligator** (λ-abstraction) = a coloured box titled
  ``🐊 hungry «param»``.
- **Old alligators** (parentheses / application) = a grey (dim) frame
  titled ``🐊 family (application)``.
- **Eggs** (variables) = ``🥚 name``.
- Application stacks function above argument with a ``⇣ feeding ⇣`` arrow,
  exactly like the desktop ``Group`` layout.

Named Church constants are expanded first (scope-safely, via
``church.expand_term``) so ``alligators TRUE`` and ``alligators AND`` show
their λ-structure; integer literals become Church numerals as everywhere
else in the browser build.
"""

from __future__ import annotations

import re

from lambda_lab.lab import church, lc
from lambda_lab.lab.parser import ParseError, parse

from . import _ansi as A

MAX_INPUT = 4_000
MAX_NUMERAL = 24
MAX_NODES = 400

_NEGATIVE_LITERAL = re.compile(r"(?<![\w'])-\d+(?![\w'])", re.UNICODE)
_POSITIVE_LITERAL = re.compile(r"(?<![\w'])\d+(?![\w'])", re.UNICODE)

# Desktop colour cycles (spring_green4/cyan3/dark_orange3/purple3/gold3 and
# bright_white/grey82/bright_yellow/bright_cyan/pink1) mapped onto the
# 8-colour helper idiom of the browser driver.
_GATOR_STYLES = [A.green, A.cyan, A.yellow, A.magenta, A.blue]
_EGG_STYLES = [
    A.bold,
    A.dim,
    lambda s: A.bold(A.yellow(s)),
    lambda s: A.bold(A.cyan(s)),
    lambda s: A.bold(A.magenta(s)),
]

_ARROW = "⇣ feeding ⇣"
_TITLE = "🐊 Alligator Eggs view"
_LEGEND = (
    "🐊 The crocodile says: every green square is a hungry alligator (λ). "
    "An egg (🥚) is a variable. The grey frame is a \"family\" wrapped in a "
    "pair of parentheses."
)


def _expand_numbers(src: str) -> str:
    if _NEGATIVE_LITERAL.search(src):
        raise ValueError("A Church numeral must be non-negative.")

    def repl(match: re.Match[str]) -> str:
        n = int(match.group())
        if n > MAX_NUMERAL:
            raise ValueError(f"numeral {n} is too large for the browser (max {MAX_NUMERAL})")
        return f"({church.church_numeral_src(n)})"

    return _POSITIVE_LITERAL.sub(repl, src)


def _render_lines(t: lc.Term, depth: int = 0) -> list[str]:
    gator = _GATOR_STYLES[depth % len(_GATOR_STYLES)]
    egg = _EGG_STYLES[depth % len(_EGG_STYLES)]

    if isinstance(t, lc.Var):
        return [egg(f"🥚 {t.name}")]

    if isinstance(t, lc.Lam):
        body = _render_lines(t.body, depth + 1)
        return A.box(
            body,
            title=gator(f"🐊 hungry «{t.param}»"),
            border_fn=gator,
            pad_x=2,
        )

    if isinstance(t, lc.App):
        left = _render_lines(t.fn, depth + 1)
        right = _render_lines(t.arg, depth + 1)
        inner = max(A.display_width(row) for row in left + right + [_ARROW])
        pad = " " * max((inner - A.display_width(_ARROW)) // 2, 0)
        content = left + [pad + A.dim(_ARROW)] + right
        return A.box(
            content,
            title=A.dim("🐊 family (application)"),
            border_fn=A.dim,
            pad_x=2,
        )

    raise TypeError(f"Unknown term: {t!r}")


def handle(arg: str, state: dict) -> str:
    """Render ``alligators <term>``. Non-interactive; ``state`` is unused."""
    del state
    src = (arg or "").strip()
    if not src:
        return A.yellow("Usage: alligators <term>")
    if len(src) > MAX_INPUT:
        return A.red(f"Input is too long (max {MAX_INPUT} characters).")
    try:
        term = church.expand_term(parse(_expand_numbers(src)))
    except ParseError as exc:
        return A.red("Parse error: ") + str(exc)
    except ValueError as exc:
        return A.red("Error: ") + str(exc)
    if lc.term_size(term, stop_after=MAX_NODES) > MAX_NODES:
        return A.yellow(
            f"The expanded term has more than {MAX_NODES} AST nodes — "
            "too many alligators to draw in the browser. Try a smaller term."
        )
    try:
        body = _render_lines(term)
    except RecursionError:
        return A.red("The term is too deeply nested for the browser sandbox.")
    panel = A.box(
        body,
        title=A.bold(A.green(_TITLE)),
        border_fn=A.green,
        pad_x=2,
        pad_y=1,
    )
    return A.lines(*panel, A.dim(_LEGEND))
