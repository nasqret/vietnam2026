"""Minimal English i18n shim for the browser build of Lambda Lab.

The real ``lambda_lab.lab.i18n`` carries a full PL/EN dictionary plus
filesystem-backed language persistence. In the browser we only need the
handful of message keys that the vendored engine (``parser.py``,
``church.py``) actually looks up, so this shim provides English strings and
a ``str.format`` fallback for anything else. No filesystem access.
"""

from __future__ import annotations

from typing import Any

SUPPORTED = ("en",)
_LANG = "en"

_MESSAGES = {
    # parser.py
    "parser.unexpected_char": "Unexpected character {ch!r} at position {pos}.",
    "parser.expected_kind": "Expected {expected}, but got {got_kind} '{got_text}'.",
    "parser.unexpected_token": "Unexpected token {kind} '{text}'.",
    "parser.lambda_needs_var": "A lambda needs at least one variable name before '.'.",
    "parser.expected_eof": "Unexpected trailing input: '{rest}'.",
    # church.py
    "church.numeral_negative": "A Church numeral must be a non-negative integer.",
}


def t(key: str, **kwargs: Any) -> str:
    msg = _MESSAGES.get(key, key)
    try:
        return msg.format(**kwargs)
    except Exception:
        return msg


def get_lang() -> str:
    return _LANG


def set_lang(lang: str, persist: bool = False) -> bool:  # noqa: ARG001
    return (lang or "").strip().lower() == "en"
