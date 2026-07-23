"""Parser λ-termów: wejście jak ``λx y. x (y z)`` lub ``\\x. x``.

Gramatyka:

    term      := application
    applic    := atom atom*                          (lewo-asocjacyjnie)
    atom      := "(" term ")" | lambda_ | identifier
    lambda_   := ("λ" | "\\") ident ident* "." term

Identyfikator: [A-Za-z_][A-Za-z0-9_']*  (pojedyncze znaki Greckie dozwolone jako aliasy).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Set

from lambda_lab.lab.i18n import t as _t
from lambda_lab.lab.lc import App, Lam, Term, Var


class ParseError(ValueError):
    """Błąd składni wyrażenia λ."""


# ---------------------------------------------------------------------------
# Lekser
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Tok:
    kind: str
    text: str
    pos: int


_LAMBDA_CHARS = ("λ", "\\")
_DOT = "."
_OPEN = "("
_CLOSE = ")"


def _is_ident_start(ch: str) -> bool:
    return ch.isalpha() or ch == "_"


def _is_ident_cont(ch: str) -> bool:
    return ch.isalnum() or ch == "_" or ch == "'"


def tokenize(src: str) -> List[Tok]:
    toks: List[Tok] = []
    i = 0
    n = len(src)
    while i < n:
        ch = src[i]
        if ch.isspace():
            i += 1
            continue
        if ch in _LAMBDA_CHARS:
            toks.append(Tok("LAM", "λ", i))
            i += 1
            continue
        if ch == _DOT:
            toks.append(Tok("DOT", ch, i))
            i += 1
            continue
        if ch == _OPEN:
            toks.append(Tok("LPAREN", ch, i))
            i += 1
            continue
        if ch == _CLOSE:
            toks.append(Tok("RPAREN", ch, i))
            i += 1
            continue
        if _is_ident_start(ch):
            j = i + 1
            while j < n and _is_ident_cont(src[j]):
                j += 1
            toks.append(Tok("IDENT", src[i:j], i))
            i = j
            continue
        raise ParseError(_t("parser.unexpected_char", ch=ch, pos=i))
    toks.append(Tok("EOF", "", n))
    return toks


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class _Parser:
    def __init__(self, toks: List[Tok], *, constants: Optional[Set[str]] = None):
        self.toks = toks
        self.i = 0
        self.constants = constants or set()

    @property
    def cur(self) -> Tok:
        return self.toks[self.i]

    def eat(self, kind: str) -> Tok:
        if self.cur.kind != kind:
            raise ParseError(
                _t("parser.expected_kind",
                   expected=kind, got_kind=self.cur.kind, got_text=self.cur.text)
            )
        tok = self.cur
        self.i += 1
        return tok

    # term := application
    def term(self) -> Term:
        return self.application()

    # application := atom atom*
    def application(self) -> Term:
        out = self.atom()
        while self.cur.kind in ("IDENT", "LPAREN", "LAM"):
            right = self.atom()
            out = App(out, right)
        return out

    # atom := "(" term ")" | lambda_ | IDENT
    def atom(self) -> Term:
        tok = self.cur
        if tok.kind == "LPAREN":
            self.eat("LPAREN")
            node = self.term()
            self.eat("RPAREN")
            return node
        if tok.kind == "LAM":
            return self.lambda_()
        if tok.kind == "IDENT":
            self.eat("IDENT")
            return Var(tok.text)
        raise ParseError(_t("parser.unexpected_token", kind=tok.kind, text=tok.text))

    # lambda_ := "λ" IDENT+ "." term
    def lambda_(self) -> Term:
        self.eat("LAM")
        params: List[str] = []
        if self.cur.kind != "IDENT":
            raise ParseError(_t("parser.lambda_needs_var"))
        while self.cur.kind == "IDENT":
            params.append(self.cur.text)
            self.i += 1
        self.eat("DOT")
        body = self.term()
        for p in reversed(params):
            body = Lam(p, body)
        return body


def parse(src: str, *, constants: Optional[Set[str]] = None) -> Term:
    toks = tokenize(src)
    p = _Parser(toks, constants=constants)
    node = p.term()
    if p.cur.kind != "EOF":
        raise ParseError(_t("parser.expected_eof", rest=p.cur.text))
    return node
