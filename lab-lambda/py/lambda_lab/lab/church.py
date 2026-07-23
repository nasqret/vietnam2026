"""Church encodings and scope-safe expansion/decoding helpers."""

from __future__ import annotations

from typing import Dict, FrozenSet, Tuple

from lambda_lab.lab.lc import App, Lam, Term, Var, _bound_index, normalize_checked
from lambda_lab.lab.parser import parse

TRUE_SRC = r"\t f. t"
FALSE_SRC = r"\t f. f"
IF_SRC = r"\b t f. b t f"
AND_SRC = r"\p q. p q p"
OR_SRC = r"\p q. p p q"
NOT_SRC = r"\p. p FALSE TRUE"
NAND_SRC = r"\p q. NOT (AND p q)"
NOR_SRC = r"\p q. NOT (OR p q)"
XOR_SRC = r"\p q. AND (OR p q) (NAND p q)"
XNOR_SRC = r"\p q. NOT (XOR p q)"
IMPLIES_SRC = r"\p q. OR (NOT p) q"
IFF_SRC = XNOR_SRC
PAIR_SRC = r"\a b. \f. f a b"
FST_SRC = r"\p. p TRUE"
SND_SRC = r"\p. p FALSE"
ZERO_SRC = r"\f x. x"
SUCC_SRC = r"\n f x. f (n f x)"
PLUS_SRC = r"\m n f x. m f (n f x)"
MULT_SRC = r"\m n f. m (n f)"
# Eta-long so POW m 0 beta-normalizes to the canonical Church numeral 1.
POW_SRC = r"\m n f x. n m f x"
ISZERO_SRC = r"\n. n (\_. FALSE) TRUE"
PRED_SRC = r"\n f x. n (\g h. h (g f)) (\u. x) (\u. u)"
SUB_SRC = r"\m n. n PRED m"
LEQ_SRC = r"\m n. ISZERO (SUB m n)"
EQ_SRC = r"\m n. AND (LEQ m n) (LEQ n m)"
Y_SRC = r"\f. (\x. f (x x)) (\x. f (x x))"
Z_SRC = r"\f. (\x. f (\v. x x v)) (\x. f (\v. x x v))"
OMEGA_SRC = r"(\x. x x) (\x. x x)"

CONSTANTS: Dict[str, str] = {
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
    "PAIR": PAIR_SRC,
    "FST": FST_SRC,
    "SND": SND_SRC,
    "0": ZERO_SRC,
    "ZERO": ZERO_SRC,
    "SUCC": SUCC_SRC,
    "PRED": PRED_SRC,
    "PLUS": PLUS_SRC,
    "SUB": SUB_SRC,
    "MULT": MULT_SRC,
    "POW": POW_SRC,
    "ISZERO": ISZERO_SRC,
    "LEQ": LEQ_SRC,
    "EQ": EQ_SRC,
    "Y": Y_SRC,
    "Z": Z_SRC,
    "OMEGA": OMEGA_SRC,
    "Ω": OMEGA_SRC,
}


def church_numeral_src(n: int) -> str:
    if n < 0:
        raise ValueError("A Church numeral must be a non-negative integer.")
    body = "x"
    for _ in range(n):
        body = f"f ({body})"
    return rf"\f x. {body}"


def church(n: int) -> Term:
    return parse(church_numeral_src(n))


def expand_named(src: str, *, max_passes: int = 16) -> str:
    """Legacy display helper. Evaluation should use ``expand_term``."""
    import re

    names = sorted(CONSTANTS.keys(), key=len, reverse=True)
    patterns = {n: re.compile(rf"\b{re.escape(n)}\b") for n in names}
    for _ in range(max_passes):
        changed = False
        for name in names:
            if name.isdigit():
                continue
            new_src, count = patterns[name].subn(lambda _m, r=f"({CONSTANTS[name]})": r, src)
            if count > 0 and new_src != src:
                src = new_src
                changed = True
        if not changed:
            break
    return src


def expand_term(
    term: Term,
    *,
    bound: FrozenSet[str] = frozenset(),
    stack: Tuple[str, ...] = (),
) -> Term:
    """Expand only free occurrences of named constants.

    String replacement cannot distinguish a free constant from a binder named
    ``TRUE``. AST traversal can, and also avoids matches inside identifiers.
    """
    if isinstance(term, Var):
        name = term.name
        if name in bound or name not in CONSTANTS or name.isdigit():
            return term
        if name in stack:
            chain = " -> ".join(stack + (name,))
            raise ValueError(f"cyclic Church constant definition: {chain}")
        return expand_term(parse(CONSTANTS[name]), stack=stack + (name,))
    if isinstance(term, Lam):
        return Lam(term.param, expand_term(term.body, bound=bound | {term.param}, stack=stack))
    if isinstance(term, App):
        return App(
            expand_term(term.fn, bound=bound, stack=stack),
            expand_term(term.arg, bound=bound, stack=stack),
        )
    raise TypeError(f"Unknown term: {term!r}")


def expand(name: str) -> Term:
    if name not in CONSTANTS:
        raise KeyError(name)
    return expand_term(parse(CONSTANTS[name]), stack=(name,))


def decode_numeral_nf(t: Term) -> int | None:
    """Decode a beta-normal term using binder identity, safe under shadowing."""
    if not isinstance(t, Lam) or not isinstance(t.body, Lam):
        return None
    binders = (t.param, t.body.param)
    body = t.body.body
    count = 0
    while isinstance(body, App):
        if not isinstance(body.fn, Var) or _bound_index(body.fn.name, binders) != 1:
            break
        count += 1
        body = body.arg
    if isinstance(body, Var) and _bound_index(body.name, binders) == 0:
        return count
    return None


def decode_bool_nf(t: Term) -> bool | None:
    """Decode a beta-normal Church boolean using binder identity."""
    if not isinstance(t, Lam) or not isinstance(t.body, Lam):
        return None
    body = t.body.body
    if not isinstance(body, Var):
        return None
    index = _bound_index(body.name, (t.param, t.body.param))
    if index == 1:
        return True
    if index == 0:
        return False
    return None


def try_decode_numeral(t: Term) -> int | None:
    result = normalize_checked(t, max_steps=500)
    return decode_numeral_nf(result.term) if result.complete else None


def try_decode_bool(t: Term) -> bool | None:
    result = normalize_checked(t, max_steps=500)
    return decode_bool_nf(result.term) if result.complete else None
