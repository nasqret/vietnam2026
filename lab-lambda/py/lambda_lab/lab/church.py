"""Kodowania Churcha — pojęciowe stałe i konwersje.

Są to **łańcuchy** źródłowe λ-termów (parsowane na żądanie), zamiast
wstępnie zbudowanego AST — dzięki temu narracja może mówić
„podstawiamy definicję TRUE” i pokazać studentowi dokładnie ten tekst.
"""

from __future__ import annotations

from typing import Dict

from lambda_lab.lab.lc import App, Lam, Term, Var, normalize
from lambda_lab.lab.parser import parse


# Stałe zapisane w **pojęciowy** sposób — z odwołaniem do innych stałych
# po nazwie. Funkcja ``expand_named`` poniżej (i komenda ``church`` w REPL)
# rekurencyjnie podstawia te nazwy aż do ich pełnych λ-postaci. Każda
# stała jest dosłownym wzorem, jaki uczeń zobaczy na tablicy: zamiast
# kilkudziesięciu znaków rachunku λ widzi „NAND p q ≡ NOT (AND p q)”.

# Boole — bazowe -----------------------------------------------------------

TRUE_SRC  = r"\t f. t"
FALSE_SRC = r"\t f. f"
IF_SRC    = r"\b t f. b t f"
AND_SRC   = r"\p q. p q p"
OR_SRC    = r"\p q. p p q"
NOT_SRC   = r"\p. p FALSE TRUE"

# Boole — pochodne (definiowane przez bazowe) ------------------------------

NAND_SRC    = r"\p q. NOT (AND p q)"
NOR_SRC     = r"\p q. NOT (OR p q)"
XOR_SRC     = r"\p q. AND (OR p q) (NAND p q)"
XNOR_SRC    = r"\p q. NOT (XOR p q)"
IMPLIES_SRC = r"\p q. OR (NOT p) q"
IFF_SRC     = XNOR_SRC  # równoważność logiczna = XNOR

# Pary --------------------------------------------------------------------

PAIR_SRC = r"\a b. \f. f a b"
FST_SRC  = r"\p. p TRUE"   # selektor pierwszego = TRUE jako selektor
SND_SRC  = r"\p. p FALSE"  # selektor drugiego  = FALSE jako selektor

# Liczby Peano ------------------------------------------------------------

ZERO_SRC   = r"\f x. x"
SUCC_SRC   = r"\n f x. f (n f x)"
PLUS_SRC   = r"\m n f x. m f (n f x)"
MULT_SRC   = r"\m n f. m (n f)"
POW_SRC    = r"\m n. n m"
ISZERO_SRC = r"\n. n (\_. FALSE) TRUE"

# Poprzednik i odejmowanie.
# PRED — klasyczna konstrukcja Kleene'ego (pary funkcyjne, niełatwa do
# zwinięcia w pojęciowej notacji; trzymamy w surowej postaci).
PRED_SRC = r"\n f x. n (\g h. h (g f)) (\u. x) (\u. u)"
# SUB m n — n-krotnie zastosuj PRED do m. Pojęciowo równoważne PEANO.
SUB_SRC  = r"\m n. n PRED m"
# LEQ m n  ≡  ISZERO (SUB m n)
LEQ_SRC  = r"\m n. ISZERO (SUB m n)"
# EQ m n   ≡  AND (LEQ m n) (LEQ n m)
EQ_SRC   = r"\m n. AND (LEQ m n) (LEQ n m)"

# Rekursja -----------------------------------------------------------------

Y_SRC = r"\f. (\x. f (x x)) (\x. f (x x))"
Z_SRC = r"\f. (\x. f (\v. x x v)) (\x. f (\v. x x v))"

# Wywołanie Ω ---------------------------------------------------------------

OMEGA_SRC = r"(\x. x x) (\x. x x)"


CONSTANTS: Dict[str, str] = {
    # Wartości logiczne i spójniki.
    "TRUE": TRUE_SRC,
    "FALSE": FALSE_SRC,
    "IF": IF_SRC,
    "AND": AND_SRC,
    "OR": OR_SRC,
    "NOT": NOT_SRC,
    "NAND": NAND_SRC,
    "NOR": NOR_SRC,
    "XOR": XOR_SRC,
    "XNOR": XNOR_SRC,
    "IFF": IFF_SRC,
    "IMPLIES": IMPLIES_SRC,
    # Pary.
    "PAIR": PAIR_SRC,
    "FST": FST_SRC,
    "SND": SND_SRC,
    # Liczby naturalne i operacje.
    "0": ZERO_SRC,
    "SUCC": SUCC_SRC,
    "PRED": PRED_SRC,
    "PLUS": PLUS_SRC,
    "SUB":  SUB_SRC,
    "MULT": MULT_SRC,
    "POW":  POW_SRC,
    "ISZERO": ISZERO_SRC,
    "LEQ": LEQ_SRC,
    "EQ":  EQ_SRC,
    # Rekursja i dywergencja.
    "Y": Y_SRC,
    "Z": Z_SRC,
    "OMEGA": OMEGA_SRC,
    "Ω": OMEGA_SRC,
}


def church_numeral_src(n: int) -> str:
    if n < 0:
        from lambda_lab.lab.i18n import t as _t
        raise ValueError(_t("church.numeral_negative"))
    body = "x"
    for _ in range(n):
        body = f"f ({body})"
    return rf"\f x. {body}"


def church(n: int) -> Term:
    """Zbuduj AST liczby Churcha ``n``."""
    return parse(church_numeral_src(n))


def expand_named(src: str, *, max_passes: int = 16) -> str:
    """Rekurencyjnie podstawia każdą nazwę stałej (TRUE, AND, EQ, …) jej
    pełnym λ-ciałem. Działa na poziomie *źródła stringa* — używa granic
    słów (\\b), dzięki czemu „NOR” wewnątrz „XNOR” nie trafia.

    Wielo-przebiegowe: gdy ciało stałej zawiera odwołania do innych nazw
    (np. ``EQ → AND, LEQ → ISZERO, SUB → PRED``), kolejne pasy ujawniają
    następną warstwę aż do fixed point. ``max_passes`` chroni przed
    nieskończoną rekurencją (która i tak nie powinna wystąpić — graf
    zależności w CONSTANTS jest acykliczny).
    """
    import re
    # Sortujemy od najdłuższych nazw — najdłuższe matchują najpierw,
    # więc np. „XNOR” zostanie zamienione przed „NOR”.
    names = sorted(CONSTANTS.keys(), key=len, reverse=True)
    patterns = {n: re.compile(rf"\b{re.escape(n)}\b") for n in names}
    for _ in range(max_passes):
        changed = False
        for name in names:
            if name.isdigit():
                continue
            body = CONSTANTS[name]
            new_src, count = patterns[name].subn(lambda _m, r=f"({body})": r, src)
            if count > 0 and new_src != src:
                src = new_src
                changed = True
        if not changed:
            break
    return src


def expand(name: str) -> Term:
    """Pobierz rozwinięcie stałej (np. ``TRUE`` → λt f. t).

    Jeśli ciało stałej zawiera odwołania do innych nazw (np. ``EQ`` → ``AND, LEQ``),
    rozwija je rekurencyjnie do pełnego λ-termu.
    """
    if name in CONSTANTS:
        return parse(expand_named(CONSTANTS[name]))
    raise KeyError(name)


def try_decode_numeral(t: Term) -> int | None:
    """Spróbuj zdekodować liczbę Churcha ``λf x. f (f (f x))`` → 3.

    Zwraca ``None``, jeżeli term nie jest liczbą Churcha.
    """
    t = normalize(t, max_steps=500)
    if not isinstance(t, Lam):
        return None
    f = t.param
    inner = t.body
    if not isinstance(inner, Lam):
        return None
    x = inner.param
    body = inner.body
    count = 0
    while isinstance(body, App) and isinstance(body.fn, Var) and body.fn.name == f:
        count += 1
        body = body.arg
    if isinstance(body, Var) and body.name == x:
        return count
    return None


def try_decode_bool(t: Term) -> bool | None:
    """Zdekoduj wartość logiczną, o ile term jest Church-booleanem."""
    t = normalize(t, max_steps=200)
    if not isinstance(t, Lam):
        return None
    if not isinstance(t.body, Lam):
        return None
    body = t.body.body
    if isinstance(body, Var):
        if body.name == t.param:
            return True
        if body.name == t.body.param:
            return False
    return None
