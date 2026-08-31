"""Actual positive divisor pairs for coprime products, in ordinary HA.

Scratch authoring module: the relation contains only witnessed divisibility and
an actual product equation.  Neither uniqueness, gcd recovery, nor any finite
sum/reindexing result is included in its definition.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.cornacchia_candidate import _gcd
from peano_lab.library.prime_valuation_support_candidate import (
    _and, _call, _cases, _dvd, _intro, _le, _part, _parts, _public,
)
from peano_lab.library.squarefree_decomposition_candidate import _cop


def _pair(m: str, n: str, d: str, a: str, b: str, tag: str) -> str:
    return _and(
        f"~(({a})=0)", f"~(({b})=0)",
        _dvd(a, m, tag + "left"), _dvd(b, n, tag + "right"),
        f"({d})=({a})*({b})",
    )


def divisor_factor_pair_relation(m: str, n: str, d: str, a: str, b: str,
                                 *, tag: str, variables: tuple[str, ...]) -> str:
    """Positive factors a|m, b|n with d=a*b; compound terms are supported."""
    return _public(_pair, (m, n, d, a, b), tag=tag, variables=variables)


def _gcd_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    product = _intro("m", "n", "d", "a", "b", "hd", "hc", "hdiv", "ha", "hb")
    product += (f"have hprod : {_gcd('a*b','m*n','d',tag='cdp_product')}",)
    product += _call("crt_is_gcd_coprime_product", "m", "n", "d", "a", "b", "a*b", "m*n")
    product += ("exact hd", "refl", "refl", "exact hc", "exact ha", "exact hb")
    product += (f"have hself : {_gcd('d','d','m*n',tag='cdp_self')}",)
    product += _call("is_gcd_of_dvd", "d", "m*n") + ("exact hdiv",)
    product += (f"have hswap : {_gcd('d','m*n','d',tag='cdp_swap')}",)
    product += _call("is_gcd_symm", "d", "d", "m*n") + ("exact hself",)
    product += _call("is_gcd_unique", "d", "a*b", "m*n", "d")
    product += ("exact hswap", "exact hprod")

    coordinates = _intro("m", "n", "d", "a", "b", "hc", "hp") + _parts("hp", 5)
    ha, hb, heq = (_part("hp", 5, i) for i in (2, 3, 4))
    coordinates += (f"have hbm : {_cop('b','m','cdp_coordinate_bm')}",)
    coordinates += _call("coprime_symm", "m", "b")
    coordinates += _call("crt_coprime_divisor_pair", "m", "n", "m", "b")
    coordinates += ("exact hc",) + _call("multiple_refl", "m") + ("exact " + hb,)
    coordinates += (f"have han : {_cop('a','n','cdp_coordinate_an')}",)
    coordinates += _call("crt_coprime_divisor_pair", "m", "n", "a", "n")
    coordinates += ("exact hc", "exact " + ha) + _call("multiple_refl", "n")
    coordinates += (f"have hbasea : {_gcd('a','a','m',tag='cdp_coordinate_basea')}",)
    coordinates += _call("is_gcd_of_dvd", "a", "m") + ("exact " + ha,)
    coordinates += (f"have hrestorea : {_gcd('a','d','m',tag='cdp_coordinate_restorea')}",)
    coordinates += _call("crt_is_gcd_coprime_factor_remove", "b", "a", "m", "a", "d")
    coordinates += ("trans a*b", "exact " + heq, "apply mul_comm", "exact hbm", "exact hbasea")
    coordinates += (f"have hbaseb : {_gcd('b','b','n',tag='cdp_coordinate_baseb')}",)
    coordinates += _call("is_gcd_of_dvd", "b", "n") + ("exact " + hb,)
    coordinates += (f"have hrestoreb : {_gcd('b','d','n',tag='cdp_coordinate_restoreb')}",)
    coordinates += _call("crt_is_gcd_coprime_factor_remove", "a", "b", "n", "b", "d")
    coordinates += ("exact " + heq, "exact han", "exact hbaseb", "split")
    coordinates += _call("is_gcd_symm", "a", "d", "m") + ("exact hrestorea",)
    coordinates += _call("is_gcd_symm", "b", "d", "n") + ("exact hrestoreb",)

    unique = _intro("m", "n", "d", "a", "b", "c", "e", "hc", "hp", "hq")
    for key, left, right, hypothesis in (("p", "a", "b", "hp"), ("q", "c", "e", "hq")):
        coords = _and(_gcd(left, 'm', 'd', tag='cdp_unique_' + key + 'left'),
                      _gcd(right, 'n', 'd', tag='cdp_unique_' + key + 'right'))
        unique += (f"have h{key}coords : {coords}",)
        unique += _call("coprime_divisor_factor_pair_coordinates", "m", "n", "d", left, right)
        unique += ("exact hc", "exact " + hypothesis, "cases h" + key + "coords")
    unique += ("split",) + _call("is_gcd_unique", "a", "c", "m", "d")
    unique += ("exact hpcoords_left", "exact hqcoords_left")
    unique += _call("is_gcd_unique", "b", "e", "n", "d")
    unique += ("exact hpcoords_right", "exact hqcoords_right")

    exists = _intro("m", "n", "d", "hd", "hc", "hdiv")
    exists += (f"have ha : exists a. {_gcd('a','m','d',tag='cdp_exists_left')}",)
    exists += _call("canonical_gcd_exists", "m", "d") + ("cases ha",)
    exists += (f"have hb : exists b. {_gcd('b','n','d',tag='cdp_exists_right')}",)
    exists += _call("canonical_gcd_exists", "n", "d") + ("cases hb", "have heq : d=x*x1")
    exists += _call("coprime_divisor_gcd_product", "m", "n", "d", "x", "x1")
    exists += ("exact hd", "exact hc", "exact hdiv", "exact ha_witness", "exact hb_witness",
               "exists x", "exists x1", "split", "intro hzero")
    exists += _call("factor_nonzero_left", "d", "x", "x1")
    exists += ("exact hd", "exact heq", "exact hzero", "split", "intro hzero")
    exists += _call("factor_nonzero_right", "d", "x", "x1")
    exists += ("exact hd", "exact heq", "exact hzero", "split")
    exists += _call("is_gcd_dvd_left", "x", "m", "d") + ("exact ha_witness", "split")
    exists += _call("is_gcd_dvd_left", "x1", "n", "d") + ("exact hb_witness", "exact heq")

    return (
        spec("coprime_divisor_gcd_product",
             f"forall m n d a b. ~(d=0) -> ({_cop('m','n','cdp_product_coprime')}) -> "
             f"({_dvd('d','m*n','cdp_product_divisor')}) -> "
             f"({_gcd('a','m','d',tag='cdp_product_left')}) -> "
             f"({_gcd('b','n','d',tag='cdp_product_right')}) -> d=a*b",
             ("crt_is_gcd_coprime_product", "is_gcd_of_dvd", "is_gcd_symm", "is_gcd_unique"),
             product,
             "The two genuine gcds multiply to the given positive divisor of a coprime product."),
        spec("coprime_divisor_factor_pair_coordinates",
             f"forall m n d a b. ({_cop('m','n','cdp_coordinates_coprime')}) -> "
             f"({_pair('m','n','d','a','b','cdp_coordinates_pair')}) -> "
             f"({_and(_gcd('a','m','d',tag='cdp_coordinates_left'),_gcd('b','n','d',tag='cdp_coordinates_right'))})",
             ("coprime_symm", "crt_coprime_divisor_pair", "multiple_refl", "is_gcd_of_dvd",
              "crt_is_gcd_coprime_factor_remove", "mul_comm", "is_gcd_symm"),
             coordinates,
             "Every actual positive factor pair has its coordinates recovered by the two canonical relational gcds."),
        spec("coprime_divisor_factor_pair_unique",
             f"forall m n d a b c e. ({_cop('m','n','cdp_unique_coprime')}) -> "
             f"({_pair('m','n','d','a','b','cdp_unique_first')}) -> "
             f"({_pair('m','n','d','c','e','cdp_unique_second')}) -> ((a=c) /\\ (b=e))",
             ("coprime_divisor_factor_pair_coordinates", "is_gcd_unique"), unique,
             "The positive-divisor product map is injective on genuine divisor pairs of coprime inputs."),
        spec("coprime_divisor_factor_pair_exists",
             f"forall m n d. ~(d=0) -> ({_cop('m','n','cdp_exists_coprime')}) -> "
             f"({_dvd('d','m*n','cdp_exists_divisor')}) -> exists a b. "
             f"({_pair('m','n','d','a','b','cdp_exists_result')})",
             ("canonical_gcd_exists", "coprime_divisor_gcd_product", "factor_nonzero_left",
              "factor_nonzero_right", "is_gcd_dvd_left"), exists,
             "Canonical gcd existence supplies real positive divisor coordinates, without a factorization or choice oracle."),
    )


def _pair_bounds(m: str, n: str, a: str, b: str, tag: str) -> str:
    return _and(_le(a, m, tag + "left"), _le(b, n, tag + "right"),
                _cop(a, b, tag + "coprime"))


def _product_equation_script(hm: str, hn: str, hd: str,
                             u: str = "x", v: str = "x1") -> tuple[str, ...]:
    """Rearrange only actual witnessed equations; no extra theorem premise."""
    return (
        "rewrite " + hm, "rewrite " + hn, "rewrite " + hd,
        f"trans a*({u}*(b*{v}))", "apply mul_assoc",
        f"trans a*(({u}*b)*{v})", "congr", "refl", "symm", "apply mul_assoc",
        f"trans a*((b*{u})*{v})", "congr", "refl", "congr", "apply mul_comm", "refl",
        f"trans a*(b*({u}*{v}))", "congr", "refl", "apply mul_assoc",
        "symm", "apply mul_assoc",
    )


def _cofactors(m: str, n: str, d: str, a: str, b: str,
               u: str, v: str, tag: str) -> str:
    return _and(
        f"({m})=({a})*({u})", f"({n})=({b})*({v})",
        f"~(({u})=0)", f"~(({v})=0)",
        _le(u, m, tag + "ubound"), _le(v, n, tag + "vbound"),
        _cop(a, b, tag + "ab"), _cop(a, v, tag + "av"),
        _cop(u, b, tag + "ub"), _cop(u, v, tag + "uv"),
        f"({m})*({n})=({d})*(({u})*({v}))",
    )


def _bounded_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    bounds = _intro("m", "n", "d", "a", "b", "hm", "hn", "hc", "hp") + _parts("hp", 5)
    ha, hb = (_part("hp", 5, i) for i in (2, 3))
    bounds += ("split",) + _call("divisor_le_nonzero", "a", "m")
    bounds += ("exact hm", "exact " + ha, "split")
    bounds += _call("divisor_le_nonzero", "b", "n") + ("exact hn", "exact " + hb)
    bounds += _call("crt_coprime_divisor_pair", "m", "n", "a", "b")
    bounds += ("exact hc", "exact " + ha, "exact " + hb)

    final = _and(_pair('m','n','d','a','b','cdp_bounded_exists_pair'),
                 _pair_bounds('m','n','a','b','cdp_bounded_exists_bounds'),
                 f"forall c e. ({_pair('m','n','d','c','e','cdp_bounded_exists_unique')}) -> ((a=c) /\\ (b=e))")
    unique = _intro("m", "n", "d", "hm", "hn", "hd", "hc", "hdiv")
    unique += (f"have hp : exists a b. ({_pair('m','n','d','a','b','cdp_bounded_construct')})",)
    unique += _call("coprime_divisor_factor_pair_exists", "m", "n", "d")
    unique += ("exact hd", "exact hc", "exact hdiv") + _cases("hp", 2)
    unique += ("exists x", "exists x1", "split", "exact hp_witness_witness", "split")
    unique += _call("coprime_divisor_factor_pair_bounds", "m", "n", "d", "x", "x1")
    unique += ("exact hm", "exact hn", "exact hc", "exact hp_witness_witness")
    unique += _intro("c", "e", "hq")
    unique += _call("coprime_divisor_factor_pair_unique", "m", "n", "d", "x", "x1", "c", "e")
    unique += ("exact hc", "exact hp_witness_witness", "exact hq")

    cofactors = _intro("m", "n", "d", "a", "b", "hm", "hn", "hc", "hp") + _parts("hp", 5)
    ha, hb, heq = (_part("hp", 5, i) for i in (2, 3, 4))
    for target, factor, label, hpositive, hdivides in (
            ("m", "a", "u", "hm", ha), ("n", "b", "v", "hn", hb)):
        props = _and(f"{target}={factor}*q", "~(q=0)",
                     _dvd('q',target,'cdp_cofactor_'+label+'divisor'),
                     _le('q',target,'cdp_cofactor_'+label+'bound'),
                     f"forall r. {target}={factor}*r -> r=q")
        cofactors += (f"have h{label} : exists q. ({props})",)
        cofactors += _call("positive_divisor_quotient_exists_unique", target, factor)
        cofactors += ("exact " + hpositive, "exact " + hdivides, "cases h" + label)
        cofactors += _parts("h" + label + "_witness", 5)
    ue, up, ud, ub = (_part("hu_witness", 5, i) for i in (0, 1, 2, 3))
    ve, vp, vd, vb = (_part("hv_witness", 5, i) for i in (0, 1, 2, 3))
    cofactors += ("exists x", "exists x1")
    for hypothesis in (ue, ve, up, vp, ub, vb):
        cofactors += ("split", "exact " + hypothesis)
    for left, right, hleft, hright in (
            ("a", "b", ha, hb), ("a", "x1", ha, vd),
            ("x", "b", ud, hb), ("x", "x1", ud, vd)):
        cofactors += ("split",) + _call("crt_coprime_divisor_pair", "m", "n", left, right)
        cofactors += ("exact hc", "exact " + hleft, "exact " + hright)
    cofactors += _product_equation_script(ue, ve, heq)

    quotient = _intro("m", "n", "d", "a", "b", "u", "v", "q", "hp", "hm", "hn", "hq") + _parts("hp", 5)
    hapos, hbpos, heq = (_part("hp", 5, i) for i in (0, 1, 4))
    quotient += ("have hd : ~(d=0)", "intro hzero") + _call("mul_ne_zero", "a", "b")
    quotient += ("exact " + hapos, "exact " + hbpos, "trans d", "symm", "exact " + heq, "exact hzero")
    quotient += ("have hprod : m*n=d*(u*v)",)
    quotient += _product_equation_script("hm", "hn", heq, "u", "v")
    quotient += _call("mul_left_cancel_nonzero", "d", "q", "u*v")
    quotient += ("exact hd", "trans m*n", "symm", "exact hq", "exact hprod")

    return (
        spec("coprime_divisor_factor_pair_bounds",
             f"forall m n d a b. ~(m=0) -> ~(n=0) -> ({_cop('m','n','cdp_bounds_coprime')}) -> "
             f"({_pair('m','n','d','a','b','cdp_bounds_pair')}) -> "
             f"({_pair_bounds('m','n','a','b','cdp_bounds_result')})",
             ("divisor_le_nonzero", "crt_coprime_divisor_pair"), bounds,
             "For positive inputs each coordinate lies in its actual divisor window, and the coordinates are coprime."),
        spec("coprime_divisor_factor_pair_exists_unique",
             f"forall m n d. ~(m=0) -> ~(n=0) -> ~(d=0) -> ({_cop('m','n','cdp_bounded_coprime')}) -> "
             f"({_dvd('d','m*n','cdp_bounded_divisor')}) -> exists a b. ({final})",
             ("coprime_divisor_factor_pair_exists", "coprime_divisor_factor_pair_bounds",
              "coprime_divisor_factor_pair_unique"), unique,
             "Every positive divisor of a positive coprime product has exactly one bounded positive divisor pair."),
        spec("coprime_divisor_factor_pair_cofactors",
             f"forall m n d a b. ~(m=0) -> ~(n=0) -> ({_cop('m','n','cdp_cofactor_coprime')}) -> "
             f"({_pair('m','n','d','a','b','cdp_cofactor_pair')}) -> exists u v. "
             f"({_cofactors('m','n','d','a','b','u','v','cdp_cofactor_result')})",
             ("positive_divisor_quotient_exists_unique", "crt_coprime_divisor_pair", "mul_assoc", "mul_comm"),
             cofactors,
             "Real positive bounded cofactor witnesses have all cross-input coprimality relations and multiply to the true quotient."),
        spec("divisor_factor_pair_quotient_product",
             f"forall m n d a b u v q. ({_pair('m','n','d','a','b','cdp_quotient_pair')}) -> "
             "m=a*u -> n=b*v -> m*n=d*q -> q=u*v",
             ("mul_ne_zero", "mul_assoc", "mul_comm", "mul_left_cancel_nonzero"), quotient,
             "For any actual positive divisor pair, a supplied product quotient equals the product of the supplied cofactors."),
    )


def make_coprime_divisor_decomposition_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return _gcd_rows(spec) + _bounded_rows(spec)


__all__ = ["divisor_factor_pair_relation", "make_coprime_divisor_decomposition_candidate_theorems"]
