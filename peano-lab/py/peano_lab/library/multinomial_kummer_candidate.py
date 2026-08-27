"""Constructive finite-list multinomial and carry proofs over unchanged HA.

The authoring relations below expand to ordinary first-order arithmetic.
Neither a definition nor a dependency-curried body is an admission receipt.
The multinomial relation uses actual running sums and binomial products; the
carry relation will count actual binary column-carry traces, never valuations
disguised as carry certificates.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from .bertrand_central_binom_valuation_candidate import _power_valuation_term
from .bertrand_choose_foundation_candidate import _choose_relation_term
from .bertrand_legendre_sum_candidate import _power_quotient_prefix_terms
from .fermat_residue_map_candidate import prime
from .finite_fold_surface import _identifier, _product_relation_term
from .finite_sum_theorems import _at, _sum_relation_terms, _sum_trace_body
from .generalized_crt_fold_candidate import _positive_terms
from .kummer_carry_candidate import _add_carry_prefix, _bit_count_term


def _call(name: str, *arguments: str) -> tuple[str, ...]:
    return (*(f"specialize {name} {argument}" for argument in arguments), f"apply {name}")


def _intro(*names: str) -> tuple[str, ...]:
    return tuple(f"intro {name}" for name in names)


def _rewrite_occurrences(formula: str, variable: str, equation: str, hypothesis: str) -> tuple[str, ...]:
    """Emit one ordinary equality transport per literal free-variable occurrence."""

    return (f"rewrite {equation} at {hypothesis}",) * len(re.findall(rf"\b{re.escape(variable)}\b", formula))


def _fresh(tag: str, terms: tuple[str, ...], *roles: str) -> tuple[str, ...]:
    _identifier(tag, "multinomial definition tag")
    names = tuple(f"mkm_{role}_{tag}" for role in roles)
    arguments = set(re.findall(r"[A-Za-z_][A-Za-z_0-9']*", " ".join(terms)))
    if set(names) & arguments or any(f"_{tag}" in argument for argument in arguments):
        raise ValueError("multinomial definition binder captures an argument")
    return names


def _lt(left: str, right: str, *, tag: str) -> str:
    (witness,) = _fresh(tag, (left, right), "lt")
    return f"exists {witness}. {witness} + S ({left}) = ({right})"


def _val(base: str, value: str, exponent: str, *, tag: str) -> str:
    return _power_valuation_term(base, value, exponent, tag=f"mkm_{tag}")


def _product(code: str, scale: str, length: str, value: str, *, tag: str) -> str:
    return _product_relation_term(code, scale, length, value, tag=f"mkm_{tag}", avoid=(code, scale, length, value))


def _sum(code: str, scale: str, length: str, value: str, *, tag: str) -> str:
    return _sum_relation_terms(code, scale, length, value, tag=f"mkm_{tag}")


def _nonzero(code: str, scale: str, length: str, *, tag: str) -> str:
    return _positive_terms(code, scale, length, tag=f"mkm_{tag}", context=(code, scale, length))


def _choose(total: str, selected: str, value: str, *, tag: str) -> str:
    variables = tuple(sorted(set(re.findall(r"[A-Za-z_][A-Za-z_0-9']*", " ".join((total, selected, value)))) - {"S"}))
    return _choose_relation_term(total, selected, value, tag=f"mkm_{tag}", variables=variables)


def _binomial_point(
    code: str, scale: str, sum_code: str, sum_scale: str,
    factor_code: str, factor_scale: str, index: str, *, tag: str,
) -> str:
    value, partial, factor = _fresh(tag, (code, scale, sum_code, sum_scale, factor_code, factor_scale, index), "value", "partial", "factor")
    source = _at(code, scale, index, value, tag=f"mkm_{tag}_source")
    prefix = _at(sum_code, sum_scale, index, partial, tag=f"mkm_{tag}_partial")
    coefficient = _choose(f"{partial} + {value}", partial, factor, tag=f"{tag}_choose")
    stored = _at(factor_code, factor_scale, index, factor, tag=f"mkm_{tag}_factor")
    return f"exists {value} {partial} {factor}. ({source}) /\\ (({prefix}) /\\ (({coefficient}) /\\ ({stored})))"


def _binomial_prefix(
    code: str, scale: str, sum_code: str, sum_scale: str,
    factor_code: str, factor_scale: str, length: str, *, tag: str,
) -> str:
    (index,) = _fresh(tag, (code, scale, sum_code, sum_scale, factor_code, factor_scale, length), "index")
    point = _binomial_point(code, scale, sum_code, sum_scale, factor_code, factor_scale, index, tag=f"{tag}_point")
    return f"forall {index}. ({_lt(index, length, tag=f'{tag}_bound')}) -> ({point})"


def multinomial_binomial_prefix(
    code: str, scale: str, sum_code: str, sum_scale: str,
    factor_code: str, factor_scale: str, length: str, *, tag: str,
) -> str:
    """Actual binomial factors for each decoded part and supplied partial sum."""

    arguments = (code, scale, sum_code, sum_scale, factor_code, factor_scale, length)
    for value in arguments:
        _identifier(value, "multinomial binomial-prefix argument")
    return _binomial_prefix(*arguments, tag=tag)


def _multinomial(code: str, scale: str, length: str, total: str, value: str, *, tag: str) -> str:
    sb, sc, cb, cc = _fresh(tag, (code, scale, length, total, value), "sum_code", "sum_scale", "factor_code", "factor_scale")
    trace = _sum_trace_body(code, scale, length, total, sb, sc, tag=f"mkm_{tag}_trace")
    factors = _binomial_prefix(code, scale, sb, sc, cb, cc, length, tag=f"{tag}_factors")
    product = _product(cb, cc, length, value, tag=f"{tag}_product")
    return f"exists {sb} {sc} {cb} {cc}. ({trace}) /\\ (({factors}) /\\ ({product}))"


def multinomial(code: str, scale: str, length: str, total: str, value: str, *, tag: str) -> str:
    """An actual running-sum trace and its iterated binomial product."""

    arguments = (code, scale, length, total, value)
    for argument in arguments:
        _identifier(argument, "multinomial argument")
    return _multinomial(*arguments, tag=tag)


def _binary_carry(base: str, left: str, right: str, count: str, *, tag: str) -> str:
    codes = _fresh(tag, (base, left, right, count), "lb", "lc", "rb", "rc", "tb", "tc", "cb", "cc")
    lb, lc, rb, rc, tb, tc, cb, cc = codes
    length = f"{left} + {right}"
    lp = _power_quotient_prefix_terms(base, left, lb, lc, length, tag=f"mkm_{tag}_left")
    rp = _power_quotient_prefix_terms(base, right, rb, rc, length, tag=f"mkm_{tag}_right")
    tp = _power_quotient_prefix_terms(base, length, tb, tc, length, tag=f"mkm_{tag}_total")
    arguments = tuple(sorted(set(re.findall(r"[A-Za-z_][A-Za-z_0-9']*", " ".join((base, left, right, count)))) - {"S"}))
    carries = _add_carry_prefix(lb, lc, rb, rc, tb, tc, cb, cc, length, tag=f"mkm_{tag}_carries", variables=arguments + codes)
    total = _bit_count_term(cb, cc, length, count, tag=f"mkm_{tag}_count")
    return f"exists {' '.join(codes)}. ({lp}) /\\ (({rp}) /\\ (({tp}) /\\ (({carries}) /\\ ({total}))))"


def binary_column_carry_count(base: str, left: str, right: str, count: str, *, tag: str) -> str:
    """Actual quotient columns, carry bits, and bit count of a binary addition."""

    for value in (base, left, right, count):
        _identifier(value, "binary carry-count argument")
    return _binary_carry(base, left, right, count, tag=tag)


def _carry_point(
    base: str, code: str, scale: str, sum_code: str, sum_scale: str,
    count_code: str, count_scale: str, index: str, *, tag: str,
) -> str:
    value, partial, count = _fresh(tag, (base, code, scale, sum_code, sum_scale, count_code, count_scale, index), "value", "partial", "count")
    source = _at(code, scale, index, value, tag=f"mkm_{tag}_source")
    prefix = _at(sum_code, sum_scale, index, partial, tag=f"mkm_{tag}_partial")
    stored = _at(count_code, count_scale, index, count, tag=f"mkm_{tag}_stored")
    carries = _binary_carry(base, partial, value, count, tag=f"{tag}_binary")
    return f"exists {value} {partial} {count}. ({source}) /\\ (({prefix}) /\\ (({stored}) /\\ ({carries})))"


def _carry_prefix(
    base: str, code: str, scale: str, sum_code: str, sum_scale: str,
    count_code: str, count_scale: str, length: str, *, tag: str,
) -> str:
    (index,) = _fresh(tag, (base, code, scale, sum_code, sum_scale, count_code, count_scale, length), "index")
    point = _carry_point(base, code, scale, sum_code, sum_scale, count_code, count_scale, index, tag=f"{tag}_point")
    return f"forall {index}. ({_lt(index, length, tag=f'{tag}_bound')}) -> ({point})"


def multinomial_carry_prefix(
    base: str, code: str, scale: str, sum_code: str, sum_scale: str,
    count_code: str, count_scale: str, length: str, *, tag: str,
) -> str:
    """Complete column-carry rows when each decoded part is added to its prefix."""

    arguments = (base, code, scale, sum_code, sum_scale, count_code, count_scale, length)
    for value in arguments:
        _identifier(value, "multinomial carry-prefix argument")
    return _carry_prefix(*arguments, tag=tag)


def _carry_many(base: str, code: str, scale: str, length: str, count: str, *, tag: str) -> str:
    total, sb, sc, cb, cc = _fresh(tag, (base, code, scale, length, count), "total", "sb", "sc", "cb", "cc")
    trace = _sum_trace_body(code, scale, length, total, sb, sc, tag=f"mkm_{tag}_trace")
    rows = _carry_prefix(base, code, scale, sb, sc, cb, cc, length, tag=f"{tag}_rows")
    counted = _sum(cb, cc, length, count, tag=f"{tag}_count")
    return f"exists {total} {sb} {sc} {cb} {cc}. ({trace}) /\\ (({rows}) /\\ ({counted}))"


def carry_count_many(base: str, code: str, scale: str, length: str, count: str, *, tag: str) -> str:
    """Count all witnessed base-p column carries in sequential finite addition.

    This relation contains neither a multinomial coefficient nor a valuation:
    its only data are actual input parts, their running sums, quotient columns,
    zero/one carry bits, and two finite sum traces.
    """

    arguments = (base, code, scale, length, count)
    for value in arguments:
        _identifier(value, "finite carry-count argument")
    return _carry_many(*arguments, tag=tag)


def _valuation_point(
    base: str, code: str, scale: str, value_code: str, value_scale: str,
    index: str, *, tag: str,
) -> str:
    value, exponent = _fresh(tag, (base, code, scale, value_code, value_scale, index), "value", "exponent")
    source = _at(code, scale, index, value, tag=f"mkm_{tag}_source")
    decoded = _at(value_code, value_scale, index, exponent, tag=f"mkm_{tag}_decoded")
    valuation = _val(base, value, exponent, tag=f"{tag}_valuation")
    return f"exists {value} {exponent}. ({source}) /\\ (({decoded}) /\\ ({valuation}))"


def _valuation_prefix(
    base: str, code: str, scale: str, value_code: str, value_scale: str,
    length: str, *, tag: str,
) -> str:
    (index,) = _fresh(tag, (base, code, scale, value_code, value_scale, length), "index")
    point = _valuation_point(base, code, scale, value_code, value_scale, index, tag=f"{tag}_point")
    return f"forall {index}. ({_lt(index, length, tag=f'{tag}_bound')}) -> ({point})"


def beta_valuation_prefix(
    base: str, code: str, scale: str, value_code: str, value_scale: str,
    length: str, *, tag: str,
) -> str:
    """A finite table of canonical bounded valuations of decoded values.

    Zero is allowed in this table because the inherited canonical relation is
    bounded by the value. Product-additivity theorems separately require every
    actual factor to be nonzero; this relation is not an unbounded v_p(0).
    """

    arguments = (base, code, scale, value_code, value_scale, length)
    for value in arguments:
        _identifier(value, "valuation-prefix argument")
    return _valuation_prefix(*arguments, tag=tag)


def make_multinomial_kummer_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """Build the dependency-ordered finite-list multinomial tranche."""

    prefix = lambda length, tag, vb="vb", vc="vc": _valuation_prefix("p", "b", "c", vb, vc, length, tag=tag)
    point = lambda index, tag, vb="vb", vc="vc": _valuation_point("p", "b", "c", vb, vc, index, tag=tag)
    binprefix = lambda length, tag, cb="cb", cc="cc": _binomial_prefix("b", "c", "sb", "sc", cb, cc, length, tag=tag)
    binpoint = lambda index, tag, cb="cb", cc="cc": _binomial_point("b", "c", "sb", "sc", cb, cc, index, tag=tag)
    return (
        spec(
            "beta_valuation_prefix_empty",
            f"forall p b c vb vc. {prefix('0', 'empty')}",
            ("lt_not_le", "zero_le"),
            (*_intro("p", "b", "c", "vb", "vc", "i", "hi"), "exfalso",
             *_call("lt_not_le", "i", "0"), "exact hi", *_call("zero_le", "i")),
            "Every empty decoded list has an empty bounded-valuation table.",
        ),
        spec(
            "beta_valuation_prefix_drop_last",
            f"forall p b c vb vc l. ({prefix('S l', 'drop_source')}) -> ({prefix('l', 'drop_target')})",
            ("le_succ",),
            (*_intro("p", "b", "c", "vb", "vc", "l", "h", "i", "hi"),
             "specialize h i", "apply h", *_call("le_succ", "(S i)", "l"), "exact hi"),
            "A finite valuation table restricts to its predecessor prefix.",
        ),
        spec(
            "beta_valuation_prefix_last",
            f"forall p b c vb vc l a e. ({prefix('S l', 'last_source')}) -> "
            f"({_at('b', 'c', 'l', 'a', tag='mkm_last_a')}) -> "
            f"({_at('vb', 'vc', 'l', 'e', tag='mkm_last_e')}) -> ({_val('p', 'a', 'e', tag='last_result')})",
            ("le_refl", "beta_at_unique"),
            (*_intro("p", "b", "c", "vb", "vc", "l", "a", "e", "h", "ha", "he"),
             f"have hpoint : {point('l', 'last_point')}", "specialize h l", "apply h",
             *_call("le_refl", "(S l)"), "cases hpoint", "cases hpoint_witness",
             "cases hpoint_witness_witness", "cases hpoint_witness_witness_right",
             "have hvalue : x = a", *_call("beta_at_unique", "b", "c", "l", "x", "a"),
             "exact hpoint_witness_witness_left", "exact ha",
             "have hexponent : x1 = e", *_call("beta_at_unique", "vb", "vc", "l", "x1", "e"),
             "exact hpoint_witness_witness_right_left", "exact he",
             *_rewrite_occurrences(_val('p', 'x', 'x1', tag='last_transport'), 'x', 'hvalue', 'hpoint_witness_witness_right_right'),
             *_rewrite_occurrences(_val('p', 'x', 'x1', tag='last_transport'), 'x1', 'hexponent', 'hpoint_witness_witness_right_right'),
             "exact hpoint_witness_witness_right_right"),
            "Each actual last table entry has the exact canonical valuation of its actual decoded factor.",
        ),
        spec(
            "beta_valuation_prefix_extend",
            f"forall p b c vb vc l a e. ({prefix('l', 'extend_source')}) -> "
            f"({_at('b', 'c', 'l', 'a', tag='mkm_extend_a')}) -> "
            f"({_val('p', 'a', 'e', tag='extend_val')}) -> exists wb wc. "
            f"({prefix('S l', 'extend_target', 'wb', 'wc')})",
            ("beta_prefix_extend", "le_of_succ_le_succ", "le_eq_or_lt"),
            (*_intro("p", "b", "c", "vb", "vc", "l", "a", "e", "h", "ha", "he"),
             "have hext : exists wb wc. "
             f"({_at('wb', 'wc', 'l', 'e', tag='mkm_extend_last')}) /\\ "
             f"forall i q. ({_lt('i', 'l', tag='extend_bound')}) -> "
             f"({_at('vb', 'vc', 'i', 'q', tag='mkm_extend_old')}) -> "
             f"({_at('wb', 'wc', 'i', 'q', tag='mkm_extend_new')})",
             *_call("beta_prefix_extend", "l", "vb", "vc", "e"),
             "cases hext", "cases hext_witness", "cases hext_witness_witness",
             "exists x", "exists x1", "intro i", "intro hi",
             "have hsplit : i = l \\/ exists k. k + S i = l",
             *_call("le_eq_or_lt", "i", "l"), *_call("le_of_succ_le_succ", "i", "l"), "exact hi",
             "cases hsplit", "exists a", "exists e", "split",
             "rewrite hsplit_left", "rewrite hsplit_left", "exact ha", "split",
             "rewrite hsplit_left", "rewrite hsplit_left", "exact hext_witness_witness_left", "exact he",
             f"have hpoint : {point('i', 'extend_point')}", "specialize h i", "apply h", "exact hsplit_right",
             "cases hpoint", "cases hpoint_witness", "cases hpoint_witness_witness",
             "cases hpoint_witness_witness_right", "exists x2", "exists x3", "split",
             "exact hpoint_witness_witness_left", "split",
             "specialize hext_witness_witness_right i", "specialize hext_witness_witness_right x3",
             "apply hext_witness_witness_right", "exact hsplit_right",
             "exact hpoint_witness_witness_right_left", "exact hpoint_witness_witness_right_right"),
            "Append an actual valuation and recode the complete finite table with all prior entries preserved.",
        ),
        spec(
            "beta_valuation_prefix_exists",
            f"forall p b c l. exists vb vc. ({prefix('l', 'exists_result')})",
            ("beta_valuation_prefix_empty", "beta_at_exists", "power_valuation_exists", "beta_valuation_prefix_extend"),
            (*_intro("p", "b", "c"), "induction l", "exists 0", "exists 0",
             *_call("beta_valuation_prefix_empty", "p", "b", "c", "0", "0"),
             f"have hprefix : exists vb vc. ({prefix('l', 'exists_prefix')})", "apply IH",
             "cases hprefix", "cases hprefix_witness",
             f"have hvalue : exists a. {_at('b', 'c', 'l', 'a', tag='mkm_exists_value')}",
             *_call("beta_at_exists", "b", "c", "l"), "cases hvalue",
             f"have hval : exists e. {_val('p', 'x2', 'e', tag='exists_val')}",
             *_call("power_valuation_exists", "p", "x2"), "cases hval",
             *_call("beta_valuation_prefix_extend", "p", "b", "c", "x", "x1", "l", "x2", "x3"),
             "exact hprefix_witness_witness", "exact hvalue_witness", "exact hval_witness"),
            "Every finite decoded list has a genuinely constructed finite table of bounded power valuations.",
        ),
        spec(
            "beta_prime_product_valuation_eq_sum",
            "forall p b c vb vc l z e g. "
            f"({prime('p', tag='mkm_product_prime')}) -> ({_nonzero('b', 'c', 'l', tag='product_nonzero')}) -> "
            f"({prefix('l', 'product_valuations')}) -> ({_product('b', 'c', 'l', 'z', tag='product_value')}) -> "
            f"({_sum('vb', 'vc', 'l', 'e', tag='product_sum')}) -> ({_val('p', 'z', 'g', tag='product_val')}) -> g = e",
            ("beta_sum_zero", "beta_product_zero", "prime_power_valuation_one_zero",
             "beta_product_succ_decompose", "beta_sum_succ_decompose",
             "crt_positive_moduli_prefix_drop_last", "beta_valuation_prefix_drop_last",
             "power_valuation_exists", "beta_valuation_prefix_last",
             "crt_positive_moduli_prefix_product_nonzero", "crt_positive_moduli_prefix_last_nonzero",
             "prime_power_valuation_mul"),
            (*_intro("p", "b", "c", "vb", "vc"), "induction l",
             *_intro("z", "e", "g", "hp", "hn", "hv", "hprod", "hsum", "hg"),
             "have hezero : e = 0", *_call("beta_sum_zero", "vb", "vc", "e"), "exact hsum",
             "rewrite hezero", *_call("prime_power_valuation_one_zero", "p", "z", "g"),
             *_call("beta_product_zero", "b", "c", "z"), "exact hprod", "exact hp", "exact hg",
             *_intro("z", "e", "g", "hp", "hn", "hv", "hprod", "hsum", "hg"),
             "have hprodpart : exists a w. "
             f"({_at('b', 'c', 'l', 'a', tag='mkm_product_last')}) /\\ "
             f"(({_product('b', 'c', 'l', 'w', tag='product_before')}) /\\ z = w * a)",
             *_call("beta_product_succ_decompose", "b", "c", "l", "z"), "exact hprod",
             "cases hprodpart", "cases hprodpart_witness", "cases hprodpart_witness_witness",
             "cases hprodpart_witness_witness_right",
             "have hsumpart : exists v E. "
             f"({_at('vb', 'vc', 'l', 'v', tag='mkm_product_last_exponent')}) /\\ "
             f"(({_sum('vb', 'vc', 'l', 'E', tag='product_sum_before')}) /\\ e = E + v)",
             *_call("beta_sum_succ_decompose", "vb", "vc", "l", "e"), "exact hsum",
             "cases hsumpart", "cases hsumpart_witness", "cases hsumpart_witness_witness",
             "cases hsumpart_witness_witness_right",
             f"have hnprev : {_nonzero('b', 'c', 'l', tag='product_previous_nonzero')}",
             *_call("crt_positive_moduli_prefix_drop_last", "b", "c", "l"), "exact hn",
             f"have hvprev : {prefix('l', 'product_previous_values')}",
             *_call("beta_valuation_prefix_drop_last", "p", "b", "c", "vb", "vc", "l"), "exact hv",
             f"have hprevious : exists v. {_val('p', 'x1', 'v', tag='product_previous_val')}",
             *_call("power_valuation_exists", "p", "x1"), "cases hprevious",
             "have hprevious_value : x4 = x3", "specialize IH x1", "specialize IH x3", "specialize IH x4", "apply IH",
             "exact hp", "exact hnprev", "exact hvprev", "exact hprodpart_witness_witness_right_left",
             "exact hsumpart_witness_witness_right_left", "exact hprevious_witness",
             *_rewrite_occurrences(_val('p', 'x1', 'x4', tag='product_previous_transport'), 'x4', 'hprevious_value', 'hprevious_witness'),
             f"have hlast : {_val('p', 'x', 'x2', tag='product_last_val')}",
             *_call("beta_valuation_prefix_last", "p", "b", "c", "vb", "vc", "l", "x", "x2"),
             "exact hv", "exact hprodpart_witness_witness_left", "exact hsumpart_witness_witness_left",
             *_rewrite_occurrences(_val('p', 'z', 'g', tag='product_transport'), 'z', 'hprodpart_witness_witness_right_right', 'hg'),
             "trans x3 + x2", *_call("prime_power_valuation_mul", "p", "x1", "x", "x3", "x2", "g"), "exact hp",
             "intro hzero",
             *_call("crt_positive_moduli_prefix_product_nonzero", "b", "c", "l", "x1"),
             "exact hnprev", "exact hprodpart_witness_witness_right_left", "exact hzero",
             "intro hzero",
             *_call("crt_positive_moduli_prefix_last_nonzero", "b", "c", "l", "x"),
             "exact hn", "exact hprodpart_witness_witness_left", "exact hzero",
             "exact hprevious_witness", "exact hlast", "exact hg",
             "symm", "exact hsumpart_witness_witness_right_right"),
            "For a prime and any nonzero finite factor list, the exact product valuation equals the finite sum of its actual factor valuations.",
        ),
        spec(
            "beta_prime_product_valuation_from_sum",
            "forall p b c vb vc l z e. "
            f"({prime('p', tag='mkm_construct_prime')}) -> ({_nonzero('b', 'c', 'l', tag='construct_nonzero')}) -> "
            f"({prefix('l', 'construct_valuations')}) -> ({_product('b', 'c', 'l', 'z', tag='construct_product')}) -> "
            f"({_sum('vb', 'vc', 'l', 'e', tag='construct_sum')}) -> ({_val('p', 'z', 'e', tag='construct_val')})",
            ("power_valuation_exists", "beta_prime_product_valuation_eq_sum"),
            (*_intro("p", "b", "c", "vb", "vc", "l", "z", "e", "hp", "hn", "hv", "hz", "he"),
             f"have hactual : exists g. {_val('p', 'z', 'g', tag='construct_actual')}",
             *_call("power_valuation_exists", "p", "z"), "cases hactual",
             "have heq : x = e", *_call("beta_prime_product_valuation_eq_sum", "p", "b", "c", "vb", "vc", "l", "z", "e", "x"),
             "exact hp", "exact hn", "exact hv", "exact hz", "exact he", "exact hactual_witness",
             *_rewrite_occurrences(_val('p', 'z', 'x', tag='construct_transport'), 'x', 'heq', 'hactual_witness'),
             "exact hactual_witness"),
            "A real finite sum of factor valuations constructs the exact valuation of their nonzero product.",
        ),
        spec(
            "multinomial_binomial_prefix_empty",
            f"forall b c sb sc cb cc. {binprefix('0', 'binempty')}",
            ("lt_not_le", "zero_le"),
            (*_intro("b", "c", "sb", "sc", "cb", "cc", "i", "hi"), "exfalso",
             *_call("lt_not_le", "i", "0"), "exact hi", *_call("zero_le", "i")),
            "The empty multinomial factor prefix requires no binomial entries.",
        ),
        spec(
            "multinomial_binomial_prefix_drop_last",
            f"forall b c sb sc cb cc l. ({binprefix('S l', 'bindrop_source')}) -> ({binprefix('l', 'bindrop_target')})",
            ("le_succ",),
            (*_intro("b", "c", "sb", "sc", "cb", "cc", "l", "h", "i", "hi"),
             "specialize h i", "apply h", *_call("le_succ", "(S i)", "l"), "exact hi"),
            "A complete binomial factor table restricts to the predecessor prefix.",
        ),
        spec(
            "multinomial_binomial_prefix_extend",
            f"forall b c sb sc cb cc l a u C. ({binprefix('l', 'binextend_source')}) -> "
            f"({_at('b', 'c', 'l', 'a', tag='mkm_binextend_a')}) -> "
            f"({_at('sb', 'sc', 'l', 'u', tag='mkm_binextend_u')}) -> "
            f"({_choose('u + a', 'u', 'C', tag='binextend_choose')}) -> exists nb nc. "
            f"({binprefix('S l', 'binextend_target', 'nb', 'nc')})",
            ("beta_prefix_extend", "le_eq_or_lt", "le_of_succ_le_succ"),
            (*_intro("b", "c", "sb", "sc", "cb", "cc", "l", "a", "u", "C", "h", "ha", "hu", "hC"),
             "have hext : exists nb nc. "
             f"({_at('nb', 'nc', 'l', 'C', tag='mkm_binextend_last')}) /\\ "
             f"forall i q. ({_lt('i', 'l', tag='binextend_bound')}) -> "
             f"({_at('cb', 'cc', 'i', 'q', tag='mkm_binextend_old')}) -> "
             f"({_at('nb', 'nc', 'i', 'q', tag='mkm_binextend_new')})",
             *_call("beta_prefix_extend", "l", "cb", "cc", "C"),
             "cases hext", "cases hext_witness", "cases hext_witness_witness",
             "exists x", "exists x1", "intro i", "intro hi",
             "have hsplit : i = l \\/ exists k. k + S i = l",
             *_call("le_eq_or_lt", "i", "l"), *_call("le_of_succ_le_succ", "i", "l"), "exact hi",
             "cases hsplit", "exists a", "exists u", "exists C", "split",
             "rewrite hsplit_left", "rewrite hsplit_left", "exact ha", "split",
             "rewrite hsplit_left", "rewrite hsplit_left", "exact hu", "split", "exact hC",
             "rewrite hsplit_left", "rewrite hsplit_left", "exact hext_witness_witness_left",
             f"have hpoint : {binpoint('i', 'binextend_point')}", "specialize h i", "apply h", "exact hsplit_right",
             "cases hpoint", "cases hpoint_witness", "cases hpoint_witness_witness",
             "cases hpoint_witness_witness_witness", "cases hpoint_witness_witness_witness_right",
             "cases hpoint_witness_witness_witness_right_right",
             "exists x2", "exists x3", "exists x4", "split", "exact hpoint_witness_witness_witness_left",
             "split", "exact hpoint_witness_witness_witness_right_left", "split", "exact hpoint_witness_witness_witness_right_right_left",
             "specialize hext_witness_witness_right i", "specialize hext_witness_witness_right x4",
             "apply hext_witness_witness_right", "exact hsplit_right", "exact hpoint_witness_witness_witness_right_right_right"),
            "Append one actual binomial factor while preserving every previously coded factor.",
        ),
        spec(
            "multinomial_binomial_prefix_exists",
            f"forall b c sb sc l. exists cb cc. ({binprefix('l', 'binexists_target')})",
            ("multinomial_binomial_prefix_empty", "beta_at_exists", "choose_exists", "multinomial_binomial_prefix_extend"),
            (*_intro("b", "c", "sb", "sc"), "induction l", "exists 0", "exists 0",
             *_call("multinomial_binomial_prefix_empty", "b", "c", "sb", "sc", "0", "0"),
             f"have hprefix : exists cb cc. {binprefix('l', 'binexists_prefix')}", "apply IH",
             "cases hprefix", "cases hprefix_witness",
             f"have hpart : exists a. {_at('b', 'c', 'l', 'a', tag='mkm_binexists_part')}",
             *_call("beta_at_exists", "b", "c", "l"), "cases hpart",
             f"have hpartial : exists u. {_at('sb', 'sc', 'l', 'u', tag='mkm_binexists_partial')}",
             *_call("beta_at_exists", "sb", "sc", "l"), "cases hpartial",
             f"have hchoose : exists C. {_choose('x3 + x2', 'x3', 'C', tag='binexists_choose')}",
             *_call("choose_exists", "(x3 + x2)", "x3"), "cases hchoose",
             *_call("multinomial_binomial_prefix_extend", "b", "c", "sb", "sc", "x", "x1", "l", "x2", "x3", "x4"),
             "exact hprefix_witness_witness", "exact hpart_witness", "exact hpartial_witness", "exact hchoose_witness"),
            "Construct all actual binomial factors for any finite decoded part and partial-sum tables.",
        ),
        spec(
            "multinomial_binomial_prefix_nonzero",
            f"forall b c sb sc cb cc l. ({binprefix('l', 'binpositive_source')}) -> ({_nonzero('cb', 'cc', 'l', tag='binpositive_target')})",
            ("beta_at_unique", "choose_positive", "le_add_right"),
            (*_intro("b", "c", "sb", "sc", "cb", "cc", "l", "h", "i", "C", "hi", "hC", "hzero"),
             f"have hpoint : {binpoint('i', 'binpositive_point')}", "specialize h i", "apply h", "exact hi",
             "cases hpoint", "cases hpoint_witness", "cases hpoint_witness_witness",
             "cases hpoint_witness_witness_witness", "cases hpoint_witness_witness_witness_right",
             "cases hpoint_witness_witness_witness_right_right",
             "have hfactor : x2 = C", *_call("beta_at_unique", "cb", "cc", "i", "x2", "C"),
             "exact hpoint_witness_witness_witness_right_right_right", "exact hC",
             "have hpositive : exists q. x2 = S q", *_call("choose_positive", "(x1 + x)", "x1", "x2"),
             *_call("le_add_right", "x1", "x"), "exact hpoint_witness_witness_witness_right_right_left", "cases hpositive",
             "have hsucc : S x3 = 0", "trans x2", "symm", "exact hpositive_witness",
             "trans C", "exact hfactor", "exact hzero", "apply PA1", "exact hsucc"),
            "Every actual multinomial binomial factor is strictly nonzero, including zero-valued input parts.",
        ),
        spec(
            "multinomial_exists_of_sum",
            f"forall b c l n. ({_sum('b', 'c', 'l', 'n', tag='exists_sum')}) -> exists z. ({_multinomial('b', 'c', 'l', 'n', 'z', tag='exists_multinomial')})",
            ("multinomial_binomial_prefix_exists", "beta_product_exists"),
            (*_intro("b", "c", "l", "n", "hsum"), "cases hsum", "cases hsum_witness",
             f"have hfactors : exists cb cc. {_binomial_prefix('b', 'c', 'x', 'x1', 'cb', 'cc', 'l', tag='exists_factors')}",
             *_call("multinomial_binomial_prefix_exists", "b", "c", "x", "x1", "l"),
             "cases hfactors", "cases hfactors_witness",
             f"have hproduct : exists z. {_product('x2', 'x3', 'l', 'z', tag='exists_product')}",
             *_call("beta_product_exists", "x2", "x3", "l"), "cases hproduct",
             "exists x4", "exists x", "exists x1", "exists x2", "exists x3", "split",
             "exact hsum_witness_witness", "split", "exact hfactors_witness_witness", "exact hproduct_witness"),
            "An actual finite sum of parts has an actual iterated-binomial multinomial coefficient.",
        ),
        spec(
            "multinomial_exists",
            f"forall b c l. exists n z. ({_multinomial('b', 'c', 'l', 'n', 'z', tag='total_multinomial')})",
            ("beta_sum_exists", "multinomial_exists_of_sum"),
            (*_intro("b", "c", "l"), f"have hsum : exists n. {_sum('b', 'c', 'l', 'n', tag='total_sum')}",
             *_call("beta_sum_exists", "b", "c", "l"), "cases hsum",
             f"have hcoefficient : exists z. {_multinomial('b', 'c', 'l', 'x', 'z', tag='total_coefficient')}",
             *_call("multinomial_exists_of_sum", "b", "c", "l", "x"), "exact hsum_witness", "cases hcoefficient",
             "exists x", "exists x1", "exact hcoefficient_witness"),
            "Every finite natural part list, including the empty list, has a witnessed total and multinomial coefficient.",
        ),
        spec(
            "multinomial_nonzero",
            f"forall b c l n z. ({_multinomial('b', 'c', 'l', 'n', 'z', tag='nonzero_multinomial')}) -> ~(z = 0)",
            ("multinomial_binomial_prefix_nonzero", "crt_positive_moduli_prefix_product_nonzero"),
            (*_intro("b", "c", "l", "n", "z", "h", "hzero"), "cases h", "cases h_witness", "cases h_witness_witness",
             "cases h_witness_witness_witness", "cases h_witness_witness_witness_witness",
             "cases h_witness_witness_witness_witness_right",
             *_call("crt_positive_moduli_prefix_product_nonzero", "x2", "x3", "l", "z"),
             *_call("multinomial_binomial_prefix_nonzero", "b", "c", "x", "x1", "x2", "x3", "l"),
             "exact h_witness_witness_witness_witness_right_left", "exact h_witness_witness_witness_witness_right_right", "exact hzero"),
            "An actual multinomial coefficient is always nonzero; no undefined zero valuation is used in Kummer's theorem.",
        ),
        spec(
            "multinomial_valuations_give_carry_prefix",
            "forall p b c sb sc cb cc vb vc l. "
            f"({prime('p', tag='mkm_rows_prime')}) -> ({binprefix('l', 'rows_binomial')}) -> "
            f"({_valuation_prefix('p', 'cb', 'cc', 'vb', 'vc', 'l', tag='rows_valuations')}) -> "
            f"({_carry_prefix('p', 'b', 'c', 'sb', 'sc', 'vb', 'vc', 'l', tag='rows_carries')})",
            ("beta_at_unique", "kummer_binomial_carry_bit_count"),
            (*_intro("p", "b", "c", "sb", "sc", "cb", "cc", "vb", "vc", "l", "hp", "hbin", "hval", "i", "hi"),
             f"have hpoint : {binpoint('i', 'rows_binpoint')}", "specialize hbin i", "apply hbin", "exact hi",
             "cases hpoint", "cases hpoint_witness", "cases hpoint_witness_witness",
             "cases hpoint_witness_witness_witness", "cases hpoint_witness_witness_witness_right",
             "cases hpoint_witness_witness_witness_right_right",
             f"have hvalue : {_valuation_point('p', 'cb', 'cc', 'vb', 'vc', 'i', tag='rows_valpoint')}",
             "specialize hval i", "apply hval", "exact hi",
             "cases hvalue", "cases hvalue_witness", "cases hvalue_witness_witness", "cases hvalue_witness_witness_right",
             "have hfactor : x3 = x2", *_call("beta_at_unique", "cb", "cc", "i", "x3", "x2"),
             "exact hvalue_witness_witness_left", "exact hpoint_witness_witness_witness_right_right_right",
             *_rewrite_occurrences(_val('p', 'x3', 'x4', tag='rows_transport'), 'x3', 'hfactor', 'hvalue_witness_witness_right_right'),
             "exists x", "exists x1", "exists x4", "split", "exact hpoint_witness_witness_witness_left",
             "split", "exact hpoint_witness_witness_witness_right_left", "split", "exact hvalue_witness_witness_right_left",
             *_call("kummer_binomial_carry_bit_count", "p", "x1", "x", "x2", "x4"),
             "exact hp", "exact hpoint_witness_witness_witness_right_right_left", "exact hvalue_witness_witness_right_right"),
            "Apply the actual checked binary Kummer proof to every decoded addition row; the resulting certificate contains real quotient columns and carry bits.",
        ),
        spec(
            "multinomial_kummer_carry_valuation",
            "forall p b c l n z. "
            f"({prime('p', tag='mkm_final_prime')}) -> ({_multinomial('b', 'c', 'l', 'n', 'z', tag='final_multinomial')}) -> "
            f"exists e. ({_val('p', 'z', 'e', tag='final_valuation')}) /\\ ({_carry_many('p', 'b', 'c', 'l', 'e', tag='final_carries')})",
            ("beta_valuation_prefix_exists", "beta_sum_exists", "beta_prime_product_valuation_from_sum",
             "multinomial_binomial_prefix_nonzero", "multinomial_valuations_give_carry_prefix"),
            (*_intro("p", "b", "c", "l", "n", "z", "hp", "h"),
             "cases h", "cases h_witness", "cases h_witness_witness", "cases h_witness_witness_witness",
             "cases h_witness_witness_witness_witness", "cases h_witness_witness_witness_witness_right",
             f"have hv : exists vb vc. {_valuation_prefix('p', 'x2', 'x3', 'vb', 'vc', 'l', tag='final_table')}",
             *_call("beta_valuation_prefix_exists", "p", "x2", "x3", "l"), "cases hv", "cases hv_witness",
             f"have hcount : exists e. {_sum('x4', 'x5', 'l', 'e', tag='final_count')}",
             *_call("beta_sum_exists", "x4", "x5", "l"), "cases hcount", "exists x6", "split",
             *_call("beta_prime_product_valuation_from_sum", "p", "x2", "x3", "x4", "x5", "l", "z", "x6"), "exact hp",
             *_call("multinomial_binomial_prefix_nonzero", "b", "c", "x", "x1", "x2", "x3", "l"),
             "exact h_witness_witness_witness_witness_right_left", "exact hv_witness_witness",
             "exact h_witness_witness_witness_witness_right_right", "exact hcount_witness",
             "exists n", "exists x", "exists x1", "exists x4", "exists x5", "split",
             "exact h_witness_witness_witness_witness_left", "split",
             *_call("multinomial_valuations_give_carry_prefix", "p", "b", "c", "x", "x1", "x2", "x3", "x4", "x5", "l"),
             "exact hp", "exact h_witness_witness_witness_witness_right_left", "exact hv_witness_witness", "exact hcount_witness"),
            "For every prime and every finite natural part list, an actual multinomial coefficient has a constructed exact valuation equal to all witnessed column carries; the empty list and zero parts are included.",
        ),
        spec(
            "multinomial_empty_values",
            f"forall b c n z. ({_multinomial('b', 'c', '0', 'n', 'z', tag='empty_values')}) -> n = 0 /\\ z = 1",
            ("beta_sum_zero", "beta_product_zero"),
            (*_intro("b", "c", "n", "z", "h"),
             "cases h", "cases h_witness", "cases h_witness_witness", "cases h_witness_witness_witness",
             "cases h_witness_witness_witness_witness", "cases h_witness_witness_witness_witness_right",
             "split", *_call("beta_sum_zero", "b", "c", "n"), "exists x", "exists x1",
             "exact h_witness_witness_witness_witness_left",
             *_call("beta_product_zero", "x2", "x3", "z"), "exact h_witness_witness_witness_witness_right_right"),
            "The empty multinomial has exactly total zero and coefficient one.",
        ),
        spec(
            "multinomial_empty_carry_count",
            f"forall p b c e. ({_carry_many('p', 'b', 'c', '0', 'e', tag='empty_carries')}) -> e = 0",
            ("beta_sum_zero",),
            (*_intro("p", "b", "c", "e", "h"),
             "cases h", "cases h_witness", "cases h_witness_witness", "cases h_witness_witness_witness",
             "cases h_witness_witness_witness_witness", "cases h_witness_witness_witness_witness_witness",
             "cases h_witness_witness_witness_witness_witness_right",
             *_call("beta_sum_zero", "x3", "x4", "e"), "exact h_witness_witness_witness_witness_witness_right_right"),
            "An actual empty finite addition has exactly zero column carries, with no prime-base assumption needed.",
        ),
    )


__all__ = ["beta_valuation_prefix", "multinomial_binomial_prefix", "multinomial", "binary_column_carry_count", "multinomial_carry_prefix", "carry_count_many", "make_multinomial_kummer_candidate_theorems"]
