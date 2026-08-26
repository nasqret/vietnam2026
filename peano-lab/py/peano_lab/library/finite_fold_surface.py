"""Conservative β-coded finite-fold surface for native Peano arithmetic.

The functions in this module are untrusted authoring helpers.  They return
fully expanded formula text and are not theorem declarations, parser syntax,
or kernel constants.  User-supplied fragments are restricted to Peano
identifiers; compound terms are assembled only by the audited helpers.

``Sum`` mirrors the checked ``Product`` relation with zero and addition.
``BitCount`` is ``Sum`` plus a proof that every decoded entry is zero or one.
``Range`` and ``Repeat`` describe finite β prefixes.  ``Pow`` existentially
packages a constant ``Repeat`` prefix with the already checked ``Product``
relation, so exponentiation is a relation rather than a new term former.
"""

from __future__ import annotations


_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _identifier(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not (value[0].isalpha() or value[0] == "_")
        or not all(character.isalnum() or character in "_'" for character in value[1:])
        or value in _RESERVED
    ):
        raise ValueError(f"{label} must be a non-reserved Peano identifier")
    return value


def _variables(*labelled: tuple[str, str]) -> tuple[str, ...]:
    return tuple(_identifier(value, label) for value, label in labelled)


def _binders(tag: str, avoid: tuple[str, ...], stems: tuple[str, ...]) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"ff_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(avoid):
        raise ValueError("generated finite-fold binder captures an argument")
    return names


def _beta_at_term(
    code: str,
    scale: str,
    index: str,
    value: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    h, q = _binders(tag, avoid, ("h", "q"))
    # Parenthesize the trusted internal terms even when the common case is a
    # single identifier.  Range uses ``start + i`` as a value; without these
    # parentheses ``S start + i`` would parse as the wrong strict bound.
    modulus = f"S ((S ({index})) * {scale})"
    return (
        f"((exists {h}. {h} + S ({value}) = {modulus}) /\\ "
        f"exists {q}. {code} = {q} * {modulus} + ({value}))"
    )


def _lt(left: str, right: str, *, tag: str, avoid: tuple[str, ...]) -> str:
    (h,) = _binders(tag, avoid, ("lt",))
    return f"exists {h}. {h} + S {left} = {right}"


def beta_at(code: str, scale: str, index: str, value: str, *, tag: str) -> str:
    """Expand the checked ``BetaAt(code,scale,index,value)`` convention."""

    variables = _variables(
        (code, "code"),
        (scale, "scale"),
        (index, "index"),
        (value, "value"),
    )
    return _beta_at_term(code, scale, index, value, tag=tag, avoid=variables)


def _product_relation_term(
    code: str,
    scale: str,
    length_term: str,
    result: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    u, v, i, p, r, s = _binders(
        tag, avoid, ("u", "v", "i", "p", "r", "s")
    )
    bound_names = avoid + (u, v, i, p, r, s)
    start = _beta_at_term(
        u, v, "0", "1", tag=f"{tag}_start", avoid=bound_names
    )
    terminal = _beta_at_term(
        u, v, length_term, result, tag=f"{tag}_terminal", avoid=bound_names
    )
    bound = _lt(i, length_term, tag=f"{tag}_bound", avoid=bound_names)
    factor = _beta_at_term(
        code, scale, i, p, tag=f"{tag}_factor", avoid=bound_names
    )
    partial = _beta_at_term(
        u, v, i, r, tag=f"{tag}_partial", avoid=bound_names
    )
    successor = _beta_at_term(
        u, v, f"S {i}", s, tag=f"{tag}_successor", avoid=bound_names
    )
    return (
        f"exists {u} {v}. (({start}) /\\ (({terminal}) /\\ "
        f"forall {i}. ({bound}) -> exists {p} {r} {s}. "
        f"(({factor}) /\\ (({partial}) /\\ (({successor}) /\\ "
        f"{s} = {r} * {p})))))"
    )


def product_relation(
    code: str,
    scale: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    """Expand the existing checked finite ``Product`` convention exactly."""

    variables = _variables(
        (code, "factor code"),
        (scale, "factor scale"),
        (length, "length"),
        (result, "result"),
    )
    return _product_relation_term(
        code,
        scale,
        length,
        result,
        tag=tag,
        avoid=variables,
    )


def product_successor_relation(
    code: str,
    scale: str,
    predecessor: str,
    result: str,
    *,
    tag: str,
) -> str:
    """Expand ``Product(code, scale, S predecessor, result)`` hygienically.

    ``product_relation`` intentionally accepts identifiers only.  This audited
    companion assembles the one compound length needed by successor
    decomposition arguments without permitting arbitrary term interpolation.
    """

    variables = _variables(
        (code, "factor code"),
        (scale, "factor scale"),
        (predecessor, "length predecessor"),
        (result, "result"),
    )
    return _product_relation_term(
        code,
        scale,
        f"S {predecessor}",
        result,
        tag=tag,
        avoid=variables,
    )


def sum_relation(
    code: str,
    scale: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    """Expand a β-coded prefix-sum trace starting at zero."""

    variables = _variables(
        (code, "summand code"),
        (scale, "summand scale"),
        (length, "length"),
        (result, "result"),
    )
    u, v, i, a, r, s = _binders(
        tag, variables, ("u", "v", "i", "a", "r", "s")
    )
    avoid = variables + (u, v, i, a, r, s)
    start = _beta_at_term(
        u, v, "0", "0", tag=f"{tag}_start", avoid=avoid
    )
    terminal = _beta_at_term(
        u, v, length, result, tag=f"{tag}_terminal", avoid=avoid
    )
    bound = _lt(i, length, tag=f"{tag}_bound", avoid=avoid)
    summand = _beta_at_term(
        code, scale, i, a, tag=f"{tag}_summand", avoid=avoid
    )
    partial = _beta_at_term(
        u, v, i, r, tag=f"{tag}_partial", avoid=avoid
    )
    successor = _beta_at_term(
        u, v, f"S {i}", s, tag=f"{tag}_successor", avoid=avoid
    )
    return (
        f"exists {u} {v}. (({start}) /\\ (({terminal}) /\\ "
        f"forall {i}. ({bound}) -> exists {a} {r} {s}. "
        f"(({summand}) /\\ (({partial}) /\\ (({successor}) /\\ "
        f"{s} = {r} + {a})))))"
    )


def all_bits(code: str, scale: str, length: str, *, tag: str) -> str:
    """Expand the assertion that a decoded prefix contains only zero or one."""

    variables = _variables(
        (code, "bit code"),
        (scale, "bit scale"),
        (length, "length"),
    )
    i, bit = _binders(tag, variables, ("i", "bit"))
    avoid = variables + (i, bit)
    bound = _lt(i, length, tag=f"{tag}_bound", avoid=avoid)
    decoded = _beta_at_term(
        code, scale, i, bit, tag=f"{tag}_decoded", avoid=avoid
    )
    return (
        f"forall {i}. ({bound}) -> exists {bit}. "
        f"(({decoded}) /\\ ({bit} = 0 \\/ {bit} = 1))"
    )


def bit_count(
    code: str,
    scale: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    """Expand a count of ones as ``Sum`` together with ``AllBits``."""

    variables = _variables(
        (code, "bit code"),
        (scale, "bit scale"),
        (length, "length"),
        (result, "count"),
    )
    del variables  # Validation is the purpose; sub-builders perform expansion.
    return (
        f"(({sum_relation(code, scale, length, result, tag=f'{tag}_sum')}) /\\ "
        f"({all_bits(code, scale, length, tag=f'{tag}_bits')}))"
    )


def range_relation(
    code: str,
    scale: str,
    start: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand the β prefix ``start, start+1, ..., start+(length-1)``."""

    variables = _variables(
        (code, "range code"),
        (scale, "range scale"),
        (start, "range start"),
        (length, "range length"),
    )
    (i,) = _binders(tag, variables, ("i",))
    avoid = variables + (i,)
    bound = _lt(i, length, tag=f"{tag}_bound", avoid=avoid)
    decoded = _beta_at_term(
        code,
        scale,
        i,
        f"{start} + {i}",
        tag=f"{tag}_decoded",
        avoid=avoid,
    )
    return f"forall {i}. ({bound}) -> ({decoded})"


def repeat_relation(
    code: str,
    scale: str,
    value: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand a constant β prefix of the requested length."""

    variables = _variables(
        (code, "repeat code"),
        (scale, "repeat scale"),
        (value, "repeated value"),
        (length, "repeat length"),
    )
    (i,) = _binders(tag, variables, ("i",))
    avoid = variables + (i,)
    bound = _lt(i, length, tag=f"{tag}_bound", avoid=avoid)
    decoded = _beta_at_term(
        code, scale, i, value, tag=f"{tag}_decoded", avoid=avoid
    )
    return f"forall {i}. ({bound}) -> ({decoded})"


def power_relation(base: str, exponent: str, result: str, *, tag: str) -> str:
    """Expand ``Pow(base,exponent,result)`` through ``Repeat`` and ``Product``."""

    variables = _variables(
        (base, "power base"),
        (exponent, "power exponent"),
        (result, "power result"),
    )
    code, scale = _binders(tag, variables, ("b", "c"))
    repeated = repeat_relation(
        code, scale, base, exponent, tag=f"{tag}_repeat"
    )
    product = product_relation(
        code, scale, exponent, result, tag=f"{tag}_product"
    )
    return f"exists {code} {scale}. (({repeated}) /\\ ({product}))"


_SUM_EXISTS_REL = sum_relation("b", "c", "l", "n", tag="x")
BETA_SUM_EXISTS = f"forall b c l. exists n. ({_SUM_EXISTS_REL})"

_SUM_LEFT = sum_relation("b", "c", "l", "n", tag="l")
_SUM_RIGHT = sum_relation("b", "c", "l", "m", tag="r")
BETA_SUM_FUNCTIONAL = (
    f"forall b c l n m. ({_SUM_LEFT}) -> ({_SUM_RIGHT}) -> n = m"
)

_BITS_COUNT = bit_count("b", "c", "l", "n", tag="b")
BIT_COUNT_BOUNDED = (
    f"forall b c l n. ({_BITS_COUNT}) -> exists h. h + n = l"
)

_ALL_BITS = all_bits("b", "c", "l", tag="a")
_BIT_COUNT_EXISTS_REL = bit_count("b", "c", "l", "n", tag="b")
BIT_COUNT_EXISTS = (
    f"forall b c l. ({_ALL_BITS}) -> exists n. ({_BIT_COUNT_EXISTS_REL})"
)

_BIT_COUNT_LEFT = bit_count("b", "c", "l", "n", tag="l")
_BIT_COUNT_RIGHT = bit_count("b", "c", "l", "m", tag="r")
BIT_COUNT_FUNCTIONAL = (
    f"forall b c l n m. ({_BIT_COUNT_LEFT}) -> ({_BIT_COUNT_RIGHT}) -> n = m"
)

_RANGE = range_relation("b", "c", "a", "l", tag="r")
RANGE_EXISTS = f"forall a l. exists b c. ({_RANGE})"

_REPEAT = repeat_relation("b", "c", "a", "l", tag="r")
REPEAT_EXISTS = f"forall a l. exists b c. ({_REPEAT})"

_POWER_EXISTS_REL = power_relation("a", "e", "n", tag="x")
POWER_EXISTS = f"forall a e. exists n. ({_POWER_EXISTS_REL})"

_POWER_LEFT = power_relation("a", "e", "n", tag="l")
_POWER_RIGHT = power_relation("a", "e", "m", tag="r")
POWER_FUNCTIONAL = (
    f"forall a e n m. ({_POWER_LEFT}) -> ({_POWER_RIGHT}) -> n = m"
)

_POWER_ZERO = power_relation("a", "e", "n", tag="z")
POWER_ZERO = f"forall a e n. e = 0 -> ({_POWER_ZERO}) -> n = 1"

_POWER_SUCC = power_relation("a", "se", "n", tag="s")
_POWER_PREV = power_relation("a", "e", "r", tag="p")
POWER_SUCCESSOR_DECOMPOSE = (
    f"forall a e se n. se = S e -> ({_POWER_SUCC}) -> "
    f"exists r. ({_POWER_PREV}) /\\ n = r * a"
)


SURFACE_FORMULAS = {
    "beta_sum_exists": BETA_SUM_EXISTS,
    "beta_sum_functional": BETA_SUM_FUNCTIONAL,
    "bit_count_bounded": BIT_COUNT_BOUNDED,
    "bit_count_exists": BIT_COUNT_EXISTS,
    "bit_count_functional": BIT_COUNT_FUNCTIONAL,
    "range_exists": RANGE_EXISTS,
    "repeat_exists": REPEAT_EXISTS,
    "power_exists": POWER_EXISTS,
    "power_functional": POWER_FUNCTIONAL,
    "power_zero": POWER_ZERO,
    "power_successor_decompose": POWER_SUCCESSOR_DECOMPOSE,
}


__all__ = [
    "BETA_SUM_EXISTS",
    "BETA_SUM_FUNCTIONAL",
    "BIT_COUNT_BOUNDED",
    "BIT_COUNT_EXISTS",
    "BIT_COUNT_FUNCTIONAL",
    "POWER_EXISTS",
    "POWER_FUNCTIONAL",
    "POWER_SUCCESSOR_DECOMPOSE",
    "POWER_ZERO",
    "RANGE_EXISTS",
    "REPEAT_EXISTS",
    "SURFACE_FORMULAS",
    "all_bits",
    "beta_at",
    "bit_count",
    "power_relation",
    "product_relation",
    "product_successor_relation",
    "range_relation",
    "repeat_relation",
    "sum_relation",
]
