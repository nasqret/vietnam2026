"""Constructive monic normalization of nonzero-leading polynomial prefixes.

Coefficients are canonical residues, in highest-degree-first order.  Monic
means a nonempty canonical prefix whose actual beta decoding at zero is 1.
Normalization records an inverse of the actual source leading coefficient
and the existing pointwise field-scaling graph.  Monicity, preservation of
represented degree and decoded-value uniqueness are conclusions, not parts
of the normalization graph.  Codes outside the annotated prefix are free.

Prime is needed for existence from an arbitrary nonzero leading residue.
Recorded-inverse consequences also hold over composite moduli whenever the
recorded inverse really exists.  The canonical field unit is natural 1,
including in characteristic two; it is not the signed-integer code 2.
"""

from __future__ import annotations

from typing import Any, Callable

from .prime_field_arithmetic_candidate import (
    _and, _call, _intro, _inv, _lt, _mul, _parts, _prime, _public,
)
from .prime_field_polynomial_candidate import _at, _coeff, _equal, _repeat, _scale
from .prime_field_polynomial_degree_candidate import _degree
from .prime_field_tables_candidate import _rewrite_all


def _monic(p: str, b: str, c: str, length: str, tag: str) -> str:
    return _and(
        f"~(({length}) = 0)",
        _coeff(p, b, c, length, tag + "coefficients"),
        _at(b, c, "0", "1", tag + "leading"),
    )


def _normalization(
    p: str, k: str, ab: str, ac: str, bb: str, bc: str, length: str, tag: str,
) -> str:
    a = "pfm_leading_" + tag
    inverse = f"exists {a}. " + _and(
        _at(ab, ac, "0", a, tag + "source"),
        _inv(p, a, k, tag + "inverse"),
    )
    return _and(
        f"~(({length}) = 0)", inverse,
        _scale(p, k, ab, ac, bb, bc, length, tag + "scale"),
    )


def prime_field_polynomial_monic_relation(
    p: str, b: str, c: str, length: str, *, tag: str, variables: tuple[str, ...],
) -> str:
    """A nonempty canonical prefix with actual leading coefficient one."""
    return _public(_monic, (p, b, c, length), tag=tag, variables=variables)


def prime_field_polynomial_monic_normalization_relation(
    p: str, k: str, ab: str, ac: str, bb: str, bc: str, length: str,
    *, tag: str, variables: tuple[str, ...],
) -> str:
    """An actual leading inverse k and coefficient scaling; no result oracle."""
    return _public(
        _normalization, (p, k, ab, ac, bb, bc, length), tag=tag, variables=variables,
    )


def _monic_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    leading = spec(
        "prime_field_polynomial_monic_leading_value",
        f"forall p b c L a. ({_monic('p','b','c','L','monic_value_source')}) -> "
        f"({_at('b','c','0','a','monic_value_entry')}) -> a=1",
        ("beta_at_unique",),
        _intro("p", "b", "c", "L", "a", "h", "ha") + _parts("h", 3)
        + _call("beta_at_unique", "b", "c", "0", "a", "1")
        + ("exact ha", "exact h_right_right"),
        "Every actual decoding of a monic leading coefficient is canonical one.",
    )
    degree = spec(
        "prime_field_polynomial_monic_represented_degree",
        f"forall p b c L d. ({_monic('p','b','c','L','monic_degree_source')}) -> "
        f"L=S d -> ({_degree('p','b','c','L','d','monic_degree_result')})",
        ("succ_ne_zero",),
        _intro("p", "b", "c", "L", "d", "h", "hlen") + _parts("h", 3)
        + ("split", "exact hlen", "split", "exact h_right_left", "exists 1",
           "split", "exact h_right_right", "intro hz")
        + _call("succ_ne_zero", "0") + ("exact hz",),
        "A monic prefix of annotated length S d has represented degree d, also for d=0.",
    )
    body = _intro("p", "b", "c", "B", "C", "L", "he", "h") + _parts("h", 3)
    body += ("split", "exact h_left", "split")
    body += _call("matrix_rank_bounded_prefix_transport", "b", "c", "B", "C", "L", "p")
    body += ("exact he", "exact h_right_left") + _call("he", "0", "1")
    body += _call("one_le_of_ne_zero", "L") + ("exact h_left", "exact h_right_right")
    transport = spec(
        "prime_field_polynomial_monic_transport",
        f"forall p b c B C L. ({_equal('b','c','B','C','L','monic_recode')}) -> "
        f"({_monic('p','b','c','L','monic_old')}) -> ({_monic('p','B','C','L','monic_new')})",
        ("matrix_rank_bounded_prefix_transport", "one_le_of_ne_zero"), body,
        "Actual prefix reencoding preserves monicity, without constraining any outside entry.",
    )
    body = _intro("p", "b", "c", "h") + _parts("h", 3)
    body += _intro("i", "hi") + ("have hi0 : i=0",)
    body += _call("le_zero", "i") + _call("le_of_succ_le_succ", "i", "0") + ("exact hi",)
    body += _rewrite_all("hi0", _at("b", "c", "i", "1", "monic_constant_index"), "i")
    body += ("exact h_right_right",)
    constant = spec(
        "prime_field_polynomial_monic_constant",
        f"forall p b c. ({_monic('p','b','c','1','monic_constant_source')}) -> "
        f"({_repeat('b','c','1','1','monic_constant_value')})",
        ("le_zero", "le_of_succ_le_succ"), body,
        "The entire represented degree-zero monic prefix is the constant one, not an empty prefix.",
    )
    return leading, degree, transport, constant


def _normalization_consequence_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    args = ("p", "k", "ab", "ac", "bb", "bc", "L")
    norm = lambda tag: _normalization(*args, tag)
    body = _intro(*args, "a", "h", "ha") + _parts("h", 3)
    body += ("cases h_right_left", "cases h_right_left_witness", "have he : a=x")
    body += _call("beta_at_unique", "ab", "ac", "0", "a", "x")
    body += ("exact ha", "exact h_right_left_witness_left")
    body += _rewrite_all("he", _inv("p", "a", "k", "normalization_inverse_value"), "a")
    body += ("exact h_right_left_witness_right",)
    inverse = spec(
        "prime_field_polynomial_monic_normalization_inverse",
        f"forall {' '.join(args)} a. ({norm('normalization_inverse_source')}) -> "
        f"({_at('ab','ac','0','a','normalization_inverse_entry')}) -> "
        f"({_inv('p','a','k','normalization_inverse_result')})",
        ("beta_at_unique",), body,
        "The recorded scalar is an actual inverse of every decoding of the source leading coefficient.",
    )
    nonzero = spec(
        "prime_field_polynomial_monic_normalization_scalar_nonzero",
        f"forall {' '.join(args)}. ({_prime('p','normalization_scalar_prime')}) -> "
        f"({norm('normalization_scalar_source')}) -> ~(k=0)",
        ("prime_field_inverse_output_nonzero",),
        _intro(*args, "hp", "h") + _parts("h", 3)
        + ("cases h_right_left", "cases h_right_left_witness", "intro hz")
        + _call("prime_field_inverse_output_nonzero", "p", "x", "k")
        + ("exact hp", "exact h_right_left_witness_right", "exact hz"),
        "Over a prime field the actual normalization scalar is nonzero; zero is never an inverse convention.",
    )
    entry = spec(
        "prime_field_polynomial_monic_normalization_entry",
        f"forall {' '.join(args)} i a r. ({norm('normalization_entry_source')}) -> "
        f"({_lt('i','L','normalization_entry_bound')}) -> "
        f"({_at('ab','ac','i','a','normalization_entry_input')}) -> "
        f"({_at('bb','bc','i','r','normalization_entry_output')}) -> "
        f"({_mul('p','k','a','r','normalization_entry_multiply')})",
        ("prime_field_polynomial_scale_entry",),
        _intro(*args, "i", "a", "r", "h", "hi", "ha", "hr") + _parts("h", 3)
        + _call("prime_field_polynomial_scale_entry", *args, "i", "a", "r")
        + ("exact h_right_right", "exact hi", "exact ha", "exact hr"),
        "Each in-range output coefficient is the actual canonical product by the recorded inverse scalar.",
    )
    bounds = _and(
        _lt("k", "p", "normalization_bound_scalar"),
        _coeff("p", "ab", "ac", "L", "normalization_bound_input"),
        _coeff("p", "bb", "bc", "L", "normalization_bound_output"),
    )
    bounded = spec(
        "prime_field_polynomial_monic_normalization_bounded",
        f"forall {' '.join(args)}. ({norm('normalization_bound_source')}) -> ({bounds})",
        ("prime_field_polynomial_scale_bounded",),
        _intro(*args, "h") + _parts("h", 3)
        + (f"have hs : {_scale(*args,'normalization_bound_scale')}", "exact h_right_right", "cases hs",
           "split", "exact hs_left")
        + _call("prime_field_polynomial_scale_bounded", *args) + ("exact h_right_right",),
        "The recorded scalar and every source and target coefficient are genuinely below the modulus.",
    )
    body = _intro(*args, "h") + (f"have hc : {norm('normalization_leading_copy')}", "exact h")
    body += _parts("hc", 3) + ("cases hc_right_left", "cases hc_right_left_witness",
                               "cases hc_right_left_witness_right")
    body += (f"have hzero : {_lt('0','L','normalization_leading_index')}",)
    body += _call("one_le_of_ne_zero", "L") + ("exact hc_left",)
    body += (f"have hr : exists r. ({_at('bb','bc','0','r','normalization_leading_decoding')})",)
    body += _call("beta_at_exists", "bb", "bc", "0") + ("cases hr",)
    body += (f"have hm : {_mul('p','k','x','x1','normalization_leading_scaled')}",)
    body += _call("prime_field_polynomial_monic_normalization_entry", *args, "0", "x", "x1")
    body += ("exact h", "exact hzero", "exact hc_right_left_witness_left", "exact hr_witness")
    body += (f"have hu : {_mul('p','k','x','1','normalization_leading_unit')}",)
    body += _call("prime_field_multiply_commutative", "p", "x", "k", "1")
    body += ("exact hc_right_left_witness_right_right", "have he : x1=1")
    body += _call("prime_field_multiply_functional", "p", "k", "x", "x1", "1")
    body += ("exact hm", "exact hu")
    body += _rewrite_all("he", _at("bb", "bc", "0", "x1", "normalization_leading_rewrite"), "x1", "hr_witness")
    body += ("exact hr_witness",)
    leading = spec(
        "prime_field_polynomial_monic_normalization_leading",
        f"forall {' '.join(args)}. ({norm('normalization_leading_source')}) -> "
        f"({_at('bb','bc','0','1','normalization_leading_result')})",
        ("one_le_of_ne_zero", "beta_at_exists", "prime_field_polynomial_monic_normalization_entry",
         "prime_field_multiply_commutative", "prime_field_multiply_functional"), body,
        "The actual scaled leading coefficient equals one by the recorded inverse, not by a monic output premise.",
    )
    body = _intro(*args, "h") + (f"have hc : {norm('normalization_monic_copy')}", "exact h")
    body += _parts("hc", 3) + ("split", "exact hc_left", "split")
    body += (f"have hb : {bounds}",) + _call("prime_field_polynomial_monic_normalization_bounded", *args)
    body += ("exact h",) + _parts("hb", 3) + ("exact hb_right_right",)
    body += _call("prime_field_polynomial_monic_normalization_leading", *args) + ("exact h",)
    monic = spec(
        "prime_field_polynomial_monic_normalization_monic",
        f"forall {' '.join(args)}. ({norm('normalization_monic_source')}) -> "
        f"({_monic('p','bb','bc','L','normalization_monic_result')})",
        ("prime_field_polynomial_monic_normalization_bounded",
         "prime_field_polynomial_monic_normalization_leading"), body,
        "Normalization yields a nonempty canonical monic prefix; all three properties are proved.",
    )
    degree = spec(
        "prime_field_polynomial_monic_normalization_represented_degree",
        f"forall {' '.join(args)} d. ({_degree('p','ab','ac','L','d','normalization_degree_input')}) -> "
        f"({norm('normalization_degree_source')}) -> "
        f"({_degree('p','bb','bc','L','d','normalization_degree_result')})",
        ("prime_field_polynomial_monic_represented_degree",
         "prime_field_polynomial_monic_normalization_monic"),
        _intro(*args, "d", "hd", "h") + ("cases hd",)
        + _call("prime_field_polynomial_monic_represented_degree", "p", "bb", "bc", "L", "d")
        + _call("prime_field_polynomial_monic_normalization_monic", *args)
        + ("exact h", "exact hd_left"),
        "Scaling by the actual leading inverse preserves the annotated nonzero represented degree exactly.",
    )
    return inverse, nonzero, entry, bounded, leading, monic, degree


def _normalization_existence(spec: Callable[..., Any]) -> Any:
    args = ("p", "ab", "ac", "L", "d")
    body = _intro(*args, "hp", "hd") + _parts("hd", 3)
    body += ("cases hd_right_right", "cases hd_right_right_witness")
    body += (f"have ha : {_lt('x','p','normalization_exists_bound')}",)
    body += _call("matrix_rank_bounded_prefix_value", "ab", "ac", "L", "p", "0", "x")
    body += ("exact hd_right_left", "rewrite hd_left", "exists d", "simp", "exact hd_right_right_witness_left")
    body += (f"have hi : exists k. ({_inv('p','x','k','normalization_exists_inverse')})",)
    body += _call("prime_field_inverse_exists", "p", "x")
    body += ("exact hp", "exact ha", "exact hd_right_right_witness_right", "cases hi")
    body += (f"have hc : {_inv('p','x','x1','normalization_exists_inverse_copy')}", "exact hi_witness")
    body += _parts("hc", 4)
    body += (f"have hs : exists bb bc. ({_scale('p','x1','ab','ac','bb','bc','L','normalization_exists_scale')})",)
    body += _call("prime_field_polynomial_scale_exists", "p", "x1", "ab", "ac", "L")
    body += ("intro hz",) + _call("prime_nonzero", "p") + ("exact hp", "exact hz",
              "exact hc_right_right_left", "exact hd_right_left", "cases hs", "cases hs_witness",
              "exists x1", "exists x2", "exists x3", "split", "intro hz")
    body += _call("succ_ne_zero", "d")
    body += ("trans L", "symm", "exact hd_left", "exact hz", "split", "exists x", "split",
             "exact hd_right_right_witness_left", "exact hi_witness", "exact hs_witness_witness")
    return spec(
        "prime_field_polynomial_monic_normalization_exists",
        f"forall {' '.join(args)}. ({_prime('p','normalization_exists_prime')}) -> "
        f"({_degree('p','ab','ac','L','d','normalization_exists_input')}) -> exists k bb bc. "
        f"({_normalization('p','k','ab','ac','bb','bc','L','normalization_exists_result')})",
        ("matrix_rank_bounded_prefix_value", "prime_field_inverse_exists",
         "prime_field_polynomial_scale_exists", "prime_nonzero", "succ_ne_zero"), body,
        "Construct an actual inverse and actual scaled beta prefix from a canonical nonzero-leading representation over any prime, including two.",
    )


def _normalization_function_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    args = ("p", "k", "j", "ab", "ac", "bb", "bc", "cb", "cc", "L")
    first = lambda tag: _normalization("p", "k", "ab", "ac", "bb", "bc", "L", tag)
    second = lambda tag: _normalization("p", "j", "ab", "ac", "cb", "cc", "L", tag)
    body = _intro(*args, "hfirst", "hsecond") + _parts("hfirst", 3) + _parts("hsecond", 3)
    body += ("cases hfirst_right_left", "cases hfirst_right_left_witness",
             "cases hsecond_right_left", "cases hsecond_right_left_witness", "have he : x1=x")
    body += _call("beta_at_unique", "ab", "ac", "0", "x1", "x")
    body += ("exact hsecond_right_left_witness_left", "exact hfirst_right_left_witness_left")
    body += _rewrite_all("he", _inv("p", "x1", "j", "normalization_scalar_comparison"), "x1", "hsecond_right_left_witness_right")
    body += _call("prime_field_inverse_functional", "p", "x", "k", "j")
    body += ("exact hfirst_right_left_witness_right", "exact hsecond_right_left_witness_right")
    scalar = spec(
        "prime_field_polynomial_monic_normalization_scalar_functional",
        f"forall {' '.join(args)}. ({first('normalization_scalar_first')}) -> "
        f"({second('normalization_scalar_second')}) -> k=j",
        ("beta_at_unique", "prime_field_inverse_functional"), body,
        "The recorded canonical leading inverse is unique even when the source and target beta encodings are not.",
    )
    body = _intro(*args, "hfirst", "hsecond") + ("have he : j=k",)
    body += _call("prime_field_polynomial_monic_normalization_scalar_functional", "p", "j", "k", "ab", "ac", "cb", "cc", "bb", "bc", "L")
    body += ("exact hsecond", "exact hfirst") + _parts("hfirst", 3) + _parts("hsecond", 3)
    body += _rewrite_all("he", _scale("p", "j", "ab", "ac", "cb", "cc", "L", "normalization_function_scale"), "j", "hsecond_right_right")
    body += _call("prime_field_polynomial_scale_functional", "p", "k", "ab", "ac", "bb", "bc", "cb", "cc", "L")
    body += ("exact hfirst_right_right", "exact hsecond_right_right")
    functional = spec(
        "prime_field_polynomial_monic_normalization_functional",
        f"forall {' '.join(args)}. ({first('normalization_function_first')}) -> "
        f"({second('normalization_function_second')}) -> "
        f"({_equal('bb','bc','cb','cc','L','normalization_function_result')})",
        ("prime_field_polynomial_monic_normalization_scalar_functional",
         "prime_field_polynomial_scale_functional"), body,
        "Two actual normalizations have the same decoded length-L prefix; beta-code equality is deliberately not asserted.",
    )
    body = _intro(*args, "i", "a", "b", "hfirst", "hsecond", "hi", "ha", "hb")
    body += (f"have he : {_equal('bb','bc','cb','cc','L','normalization_value_prefix')}",)
    body += _call("prime_field_polynomial_monic_normalization_functional", *args) + ("exact hfirst", "exact hsecond")
    body += _call("beta_at_unique", "cb", "cc", "i", "a", "b")
    body += _call("he", "i", "a") + ("exact hi", "exact ha", "exact hb")
    value = spec(
        "prime_field_polynomial_monic_normalization_value_functional",
        f"forall {' '.join(args)} i a b. ({first('normalization_value_first')}) -> "
        f"({second('normalization_value_second')}) -> ({_lt('i','L','normalization_value_bound')}) -> "
        f"({_at('bb','bc','i','a','normalization_value_left')}) -> "
        f"({_at('cb','cc','i','b','normalization_value_right')}) -> a=b",
        ("prime_field_polynomial_monic_normalization_functional", "beta_at_unique"), body,
        "Every pair of actual in-range output decodings agrees; no claim is made for indices outside the prefix.",
    )
    transport_args = ("p", "k", "ab", "ac", "bb", "bc", "AB", "AC", "BB", "BC", "L")
    body = _intro(*transport_args, "hin", "hout", "h") + _parts("h", 3)
    body += ("split", "exact h_left", "split", "cases h_right_left", "cases h_right_left_witness",
             "exists x", "split")
    body += _call("hin", "0", "x") + _call("one_le_of_ne_zero", "L")
    body += ("exact h_left", "exact h_right_left_witness_left", "exact h_right_left_witness_right")
    body += _call("prime_field_polynomial_scale_transport", *transport_args)
    body += ("exact hin", "exact hout", "exact h_right_right")
    transport = spec(
        "prime_field_polynomial_monic_normalization_transport",
        f"forall {' '.join(transport_args)}. ({_equal('ab','ac','AB','AC','L','normalization_recode_input')}) -> "
        f"({_equal('bb','bc','BB','BC','L','normalization_recode_output')}) -> "
        f"({_normalization('p','k','ab','ac','bb','bc','L','normalization_recode_old')}) -> "
        f"({_normalization('p','k','AB','AC','BB','BC','L','normalization_recode_new')})",
        ("one_le_of_ne_zero", "prime_field_polynomial_scale_transport"), body,
        "Reencode both actual coefficient prefixes while retaining the same genuine leading inverse and scale relation.",
    )
    return scalar, functional, value, transport


def _normalization_endpoint_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    body = _intro("p", "b", "c", "L", "hp", "h") + _parts("h", 3)
    body += ("split", "exact h_left", "split", "exists 1", "split", "exact h_right_right",
             "split", "intro hz") + _call("succ_ne_zero", "0") + ("exact hz",)
    body += _call("prime_field_multiply_one_left", "p", "1") + ("exact hp",)
    body += _call("prime_two_le", "p") + ("exact hp",)
    body += _call("prime_field_polynomial_scale_one", "p", "b", "c", "L") + ("exact hp", "exact h_right_left")
    fixed = spec(
        "prime_field_polynomial_monic_normalization_fixed",
        f"forall p b c L. ({_prime('p','normalization_fixed_prime')}) -> "
        f"({_monic('p','b','c','L','normalization_fixed_input')}) -> "
        f"({_normalization('p','1','b','c','b','c','L','normalization_fixed_result')})",
        ("succ_ne_zero", "prime_field_multiply_one_left", "prime_two_le", "prime_field_polynomial_scale_one"), body,
        "An already monic prefix normalizes by the actual scalar one using its original beta codes.",
    )
    args = ("p", "k", "ab", "ac", "bb", "bc")
    constant = spec(
        "prime_field_polynomial_monic_normalization_constant",
        f"forall {' '.join(args)}. ({_normalization(*args,'1','normalization_constant_source')}) -> "
        f"({_repeat('bb','bc','1','1','normalization_constant_result')})",
        ("prime_field_polynomial_monic_constant", "prime_field_polynomial_monic_normalization_monic"),
        _intro(*args, "h") + _call("prime_field_polynomial_monic_constant", "p", "bb", "bc")
        + _call("prime_field_polynomial_monic_normalization_monic", *args, "1") + ("exact h",),
        "Every actual normalization of a nonzero constant representation is the constant one.",
    )
    unique = lambda k, bb, bc, tag: (
        "forall j cb cc. "
        f"({_normalization('p','j','ab','ac','cb','cc','L',tag+'comparison')}) -> "
        + _and(f"j=({k})", _equal("cb", "cc", bb, bc, "L", tag + "equal"))
    )
    result = _and(
        _normalization("p", "k", "ab", "ac", "bb", "bc", "L", "normalization_unique_graph"),
        _monic("p", "bb", "bc", "L", "normalization_unique_monic"),
        _degree("p", "bb", "bc", "L", "d", "normalization_unique_degree"),
        unique("k", "bb", "bc", "normalization_unique"),
    )
    body = _intro("p", "ab", "ac", "L", "d", "hp", "hd")
    body += (f"have h : exists k bb bc. ({_normalization('p','k','ab','ac','bb','bc','L','normalization_unique_choice')})",)
    body += _call("prime_field_polynomial_monic_normalization_exists", "p", "ab", "ac", "L", "d")
    body += ("exact hp", "exact hd", "cases h", "cases h_witness", "cases h_witness_witness",
             "exists x", "exists x1", "exists x2", "split", "exact h_witness_witness_witness", "split")
    chosen = ("p", "x", "ab", "ac", "x1", "x2", "L")
    body += _call("prime_field_polynomial_monic_normalization_monic", *chosen)
    body += ("exact h_witness_witness_witness", "split")
    body += _call("prime_field_polynomial_monic_normalization_represented_degree", *chosen, "d")
    body += ("exact hd", "exact h_witness_witness_witness") + _intro("j", "cb", "cc", "hj") + ("split",)
    comparison = ("p", "j", "x", "ab", "ac", "cb", "cc", "x1", "x2", "L")
    body += _call("prime_field_polynomial_monic_normalization_scalar_functional", *comparison)
    body += ("exact hj", "exact h_witness_witness_witness")
    body += _call("prime_field_polynomial_monic_normalization_functional", *comparison)
    body += ("exact hj", "exact h_witness_witness_witness")
    exists_unique = spec(
        "prime_field_polynomial_monic_normalization_exists_unique",
        f"forall p ab ac L d. ({_prime('p','normalization_unique_prime')}) -> "
        f"({_degree('p','ab','ac','L','d','normalization_unique_input')}) -> exists k bb bc. ({result})",
        ("prime_field_polynomial_monic_normalization_exists", "prime_field_polynomial_monic_normalization_monic",
         "prime_field_polynomial_monic_normalization_represented_degree",
         "prime_field_polynomial_monic_normalization_scalar_functional",
         "prime_field_polynomial_monic_normalization_functional"), body,
        "Construct a monic normalization of the same represented degree, with unique inverse scalar and unique decoded coefficient prefix.",
    )
    body = _intro("p", "ab", "ac", "hp", "hd")
    body += (f"have h : exists k bb bc. ({_normalization('p','k','ab','ac','bb','bc','1','normalization_zero_choice')})",)
    body += _call("prime_field_polynomial_monic_normalization_exists", "p", "ab", "ac", "1", "0")
    body += ("exact hp", "exact hd", "cases h", "cases h_witness", "cases h_witness_witness",
             "exists x", "exists x1", "exists x2", "split", "exact h_witness_witness_witness")
    body += _call("prime_field_polynomial_monic_normalization_constant", "p", "x", "ab", "ac", "x1", "x2")
    body += ("exact h_witness_witness_witness",)
    degree_zero = spec(
        "prime_field_polynomial_monic_normalization_degree_zero_exists",
        f"forall p ab ac. ({_prime('p','normalization_zero_prime')}) -> "
        f"({_degree('p','ab','ac','1','0','normalization_zero_input')}) -> exists k bb bc. "
        + _and(_normalization("p", "k", "ab", "ac", "bb", "bc", "1", "normalization_zero_graph"),
               _repeat("bb", "bc", "1", "1", "normalization_zero_output")),
        ("prime_field_polynomial_monic_normalization_exists", "prime_field_polynomial_monic_normalization_constant"), body,
        "Construct the normalized constant-one prefix from every actual nonzero represented constant over a prime field.",
    )
    return fixed, constant, exists_unique, degree_zero


def make_prime_field_polynomial_monic_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        *_monic_rows(spec), *_normalization_consequence_rows(spec),
        _normalization_existence(spec), *_normalization_function_rows(spec),
        *_normalization_endpoint_rows(spec),
    )


__all__ = [
    "prime_field_polynomial_monic_relation",
    "prime_field_polynomial_monic_normalization_relation",
    "make_prime_field_polynomial_monic_candidate_theorems",
]
