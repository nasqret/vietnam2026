"""Ordinary HA power-difference certificates for odd-prime LTE.

This is an additive, unsealed authoring module. Powers are the actual historic
beta-coded finite-product graphs, and all subtractions are witnessed natural
balance equations. The arithmetic expansion guide only emits ordinary checked
equality steps; it is not an oracle or a new kernel rule.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from ..kernel.formulas import parse_formula_in_context
from .finite_fold_surface import _identifier
from .gaussian_euclidean_candidate import (
    _commutative_expansion_identity,
    _polynomial_expansion_dependencies,
)
from .ha_generalized_crt_congruence_candidate import _checked_term
from .power_algebra_theorems import _power_terms
from .prime_valuation_support_candidate import _prime, _val
from .signed_integer_division_candidate import _context


def _and(*formulas: str) -> str:
    return formulas[0] if len(formulas) == 1 else f"(({formulas[0]}) /\\ ({_and(*formulas[1:])}))"


def _pow(a: str, n: str, value: str, tag: str) -> str:
    return _power_terms(a, n, value, tag="olte_" + tag)


def _dvd(p: str, value: str, tag: str) -> str:
    return f"exists olte_factor_{tag}. ({value}) = ({p}) * olte_factor_{tag}"


def _coprime(a: str, b: str, tag: str) -> str:
    d = "olte_common_" + tag
    return f"forall {d}. ({_dvd(d, a, tag + 'left')}) -> ({_dvd(d, b, tag + 'right')}) -> {d} = 1"


def _lt(a: str, b: str, tag: str) -> str:
    return f"exists olte_gap_{tag}. olte_gap_{tag} + S ({a}) = ({b})"


def _intro(*names: str) -> tuple[str, ...]:
    return tuple("intro " + name for name in names)


def _call(name: str, *arguments: str) -> tuple[str, ...]:
    return tuple(f"specialize {name} ({argument})" for argument in arguments) + ("apply " + name,)


def _cases(name: str, count: int) -> tuple[str, ...]:
    return tuple("cases " + name + "_witness" * index for index in range(count))


def _parts(name: str, count: int) -> tuple[str, ...]:
    return tuple("cases " + name + "_right" * index for index in range(count - 1))


def _part(name: str, count: int, index: int) -> str:
    return name + "_right" * index + ("_left" if index < count - 1 else "")


def _rewrite(equality: str, variable: str, formula: str, *, at: str | None = None) -> tuple[str, ...]:
    count = len(re.findall(r"(?<![\w'])" + re.escape(variable) + r"(?![\w'])", formula))
    return ("rewrite " + equality + (" at " + at if at else ""),) * count


def _row(spec: Callable[..., Any], name: str, statement: str,
         dependencies: tuple[str, ...], script: tuple[str, ...], summary: str) -> Any:
    used = tuple(dict.fromkeys(
        dependency for dependency in dependencies
        if re.search(r"(?<![\w'])" + re.escape(dependency) + r"(?![\w'])", "\n".join(script))
    ))
    return spec(name, statement, used, script, summary)


def _checked_relation(builder: Callable[..., str], arguments: tuple[str, ...],
                      tag: str, variables: tuple[str, ...]) -> str:
    _identifier(tag, "LTE difference binder tag")
    context = _context(variables)
    if any(value.startswith(("olte_", "pa_")) for value in context):
        raise ValueError("LTE difference context captures a generated binder")
    values = tuple(_checked_term(value, context) for value in arguments)
    formula = builder(*values, tag)
    binders = {
        name for clause in re.findall(r"\b(?:forall|exists)\s+([^.]*)\.", formula)
        for name in clause.split()
    }
    if binders.intersection(context):
        raise ValueError("LTE difference context captures a generated binder")
    parse_formula_in_context(formula, list(context))
    return formula


def _difference_quotient(a: str, b: str, exponent: str, power_a: str, power_b: str,
                         difference: str, quotient: str, tag: str) -> str:
    return _and(
        f"({a}) = ({b}) + ({difference})",
        _pow(a, exponent, power_a, tag + "first"),
        _pow(b, exponent, power_b, tag + "second"),
        f"({power_a}) = ({power_b}) + ({difference}) * ({quotient})",
    )


def power_difference_quotient_relation(
    a: str, b: str, exponent: str, power_a: str, power_b: str,
    difference: str, quotient: str, *, tag: str, variables: tuple[str, ...],
) -> str:
    """Actual powers and their witnessed difference quotient; not a valuation.

    No uniqueness is claimed when the input difference is zero. Neither LTE
    nor prime-divisibility information occurs in this abbreviation.
    """
    return _checked_relation(_difference_quotient,
                             (a, b, exponent, power_a, power_b, difference, quotient),
                             tag, variables)


def _second_order(a: str, b: str, d: str, k: str, A: str, B: str,
                  R: str, T: str, Q: str, C: str, H: str, tag: str) -> str:
    return _and(
        _pow(a, f"S (S ({k}))", A, tag + "A"),
        _pow(b, f"S (S ({k}))", B, tag + "B"),
        _pow(b, f"S ({k})", R, tag + "R"),
        _pow(b, k, T, tag + "T"),
        f"({A}) = ({B}) + ({d}) * ({Q})",
        f"({Q}) = S (S ({k})) * ({R}) + ({d}) * ({C})",
        f"2 * ({C}) = (S (S ({k})) * S ({k})) * ({T}) + ({d}) * ({H})",
    )


def _lifted_difference(p: str, a: str, b: str, n: str, e: str,
                       A: str, B: str, D: str, tag: str) -> str:
    return _and(
        _pow(a, n, A, tag + "A"), _pow(b, n, B, tag + "B"),
        f"({A}) = ({B}) + ({D})", f"~(({D}) = 0)",
        _dvd(p, D, tag + "divides"), "~(" + _dvd(p, B, tag + "unit") + ")",
        _val(p, D, e, "olte_" + tag + "valuation"),
    )


def _tower(p: str, a: str, b: str, k: str, e: str, q: str,
           A: str, B: str, D: str, tag: str) -> str:
    return _and(_pow(p, k, q, tag + "exponent"),
                _lifted_difference(p, a, b, q, f"({e}) + ({k})", A, B, D, tag + "difference"))


def power_difference_second_order_relation(
    a: str, b: str, d: str, k: str, A: str, B: str, R: str, T: str,
    Q: str, C: str, H: str, *, tag: str, variables: tuple[str, ...],
) -> str:
    """Four actual powers and three nonnegative correction balances at k+2.

    This relation does not assert a prime, valuation, nondivisibility or LTE.
    """
    return _checked_relation(_second_order, (a, b, d, k, A, B, R, T, Q, C, H), tag, variables)


def lifted_power_difference_relation(
    p: str, a: str, b: str, n: str, e: str, A: str, B: str, D: str,
    *, tag: str, variables: tuple[str, ...],
) -> str:
    """Actual power outputs and positive p-divisible difference of valuation e.

    This is an output certificate, not an input oracle. Existence is proved by
    the prime and coprime steps and then by their complete iteration.
    """
    return _checked_relation(_lifted_difference, (p, a, b, n, e, A, B, D), tag, variables)


def make_odd_prime_lte_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    rows = []
    scalar = (
        (
            "lte_natural_difference_square", ("a", "b", "d"),
            "a * a = b * b + d * (a + b)",
            "(b + d) * (b + d)", "b * b + d * ((b + d) + b)",
            "The square difference has a genuine nonnegative geometric quotient.",
        ),
        (
            "lte_natural_difference_successor", ("a", "b", "d", "B", "Q"),
            "a * (B + d * Q) = b * B + d * (a * Q + B)",
            "(b + d) * (B + d * Q)", "b * B + d * ((b + d) * Q + B)",
            "A power-difference quotient advances by the actual recurrence a*Q+B.",
        ),
    )
    for name, variables, equation, left, right, summary in scalar:
        rows.append(_row(
            spec, name, f"forall {' '.join(variables)}. a = b + d -> {equation}",
            _polynomial_expansion_dependencies(left, right),
            _intro(*variables, "ha") + _rewrite("ha", "a", equation)
            + _commutative_expansion_identity(left, right), summary,
        ))

    left = "(b + d) * (n * R + d * C) + b * R"
    right = "S n * (b * R) + d * (b * C + (n * R + d * C))"
    rows.append(_row(
        spec, "lte_first_correction_successor",
        "forall a b d n R Q C. a = b + d -> Q = n * R + d * C -> "
        "a * Q + b * R = S n * (b * R) + d * (b * C + Q)",
        _polynomial_expansion_dependencies(left, right),
        _intro("a", "b", "d", "n", "R", "Q", "C", "ha", "hQ")
        + ("rewrite ha", "rewrite hQ", "rewrite hQ")
        + _commutative_expansion_identity(left, right),
        "The first correction term advances by b*C+Q without division or subtraction.",
    ))
    first, middle = "2 * (b * C + Q)", "b * (2 * C) + 2 * Q"
    left = "b * (m * T + d * H) + 2 * (n * (b * T) + d * C)"
    right = "(m + 2 * n) * (b * T) + d * (b * H + 2 * C)"
    rows.append(_row(
        spec, "lte_twice_correction_polynomial",
        "forall b d n m T C Q H. Q = n * (b * T) + d * C -> "
        "2 * C = m * T + d * H -> "
        "2 * (b * C + Q) = (m + 2 * n) * (b * T) + d * (b * H + 2 * C)",
        _polynomial_expansion_dependencies(first, middle)
        + _polynomial_expansion_dependencies(left, right),
        _intro("b", "d", "n", "m", "T", "C", "Q", "H", "hQ", "hC")
        + ("trans " + middle,) + _commutative_expansion_identity(first, middle)
        + ("rewrite hC", "rewrite hQ") + _commutative_expansion_identity(left, right),
        "The doubled correction recurrence has an ordinary polynomial certificate with explicit coefficient carriers.",
    ))
    rows.append(_row(
        spec, "lte_adjacent_coefficient_identity",
        "forall n. S n * n + 2 * S n = S (S n) * S n",
        ("mul_comm", "mul_add"),
        _intro("n") + (
            "trans S n * n + S n * 2", "congr", "refl", "apply mul_comm",
            "trans S n * (n + 2)", "symm", "apply mul_add",
            "trans S n * S (S n)", "congr", "refl", "simp", "apply mul_comm",
        ),
        "Consecutive triangular coefficients advance by exactly twice the next index.",
    ))
    rows.append(_row(
        spec, "lte_twice_correction_successor",
        "forall b d n T C Q H. Q = S n * (b * T) + d * C -> "
        "2 * C = (S n * n) * T + d * H -> "
        "2 * (b * C + Q) = (S (S n) * S n) * (b * T) + d * (b * H + 2 * C)",
        ("lte_twice_correction_polynomial", "lte_adjacent_coefficient_identity"),
        _intro("b", "d", "n", "T", "C", "Q", "H", "hQ", "hC")
        + ("trans (S n * n + 2 * S n) * (b * T) + d * (b * H + 2 * C)",)
        + _call("lte_twice_correction_polynomial", "b", "d", "S n", "S n * n", "T", "C", "Q", "H")
        + ("exact hQ", "exact hC", "have hcoefficient : S n * n + 2 * S n = S (S n) * S n")
        + _call("lte_adjacent_coefficient_identity", "n") + ("rewrite hcoefficient", "refl"),
        "Twice the correction has the exact triangular coefficient and an actual next remainder.",
    ))

    zero = _pow("a", "0", "x", "zero_witness")
    rows.append(_row(
        spec, "lte_power_zero_exact", f"forall a. ({_pow('a', '0', '1', 'zero')})",
        ("pow_exists", "pow_zero"),
        _intro("a") + (f"have hexists : exists x. ({zero})",)
        + _call("pow_exists", "a", "0") + ("cases hexists", "have hx : x = 1")
        + _call("pow_zero", "a", "0", "x") + ("refl", "exact hexists_witness")
        + _rewrite("hx", "x", zero, at="hexists_witness") + ("exact hexists_witness",),
        "Every natural base has an actual beta-coded zeroth power equal to one.",
    ))
    rows.append(_row(
        spec, "lte_power_one_exact", f"forall a. ({_pow('a', '1', 'a', 'one')})",
        ("pow_successor_compose", "lte_power_zero_exact", "one_mul"),
        _intro("a") + _call("pow_successor_compose", "a", "0", "1", "a")
        + _call("lte_power_zero_exact", "a") + ("symm", "apply one_mul"),
        "The relational first power is constructed, not supplied as an oracle.",
    ))
    rows.append(_row(
        spec, "lte_power_two_exact", f"forall a. ({_pow('a', '2', 'a * a', 'two')})",
        ("pow_successor_compose", "lte_power_one_exact"),
        _intro("a") + _call("pow_successor_compose", "a", "1", "a", "(a * a)")
        + _call("lte_power_one_exact", "a") + ("refl",),
        "The relational second power is the actual square, including a zero base.",
    ))
    prefix = "hprefix" + "_witness" * 7
    facts = tuple(_part(prefix, 7, index) for index in range(7))
    old = _second_order("a", "b", "d", "k", "A", "B", "R", "T", "Q", "C", "H", "prefix")
    base_left, base_right = "(b + d) + b", "2 * b + d * 1"
    script = _intro("a", "b", "d") + ("induction k", "intro ha")
    script += tuple("exists " + term for term in ("a * a", "b * b", "b", "1", "a + b", "1", "0"))
    for lemma, argument in (
        ("lte_power_two_exact", "a"), ("lte_power_two_exact", "b"),
        ("lte_power_one_exact", "b"), ("lte_power_zero_exact", "b"),
    ):
        script += ("split",) + _call(lemma, argument)
    script += ("split",) + _call("lte_natural_difference_square", "a", "b", "d") + ("exact ha",)
    script += ("split", "rewrite ha") + _commutative_expansion_identity(base_left, base_right)
    script += ("simp [mul_one]", "intro ha", f"have hprefix : exists A B R T Q C H. ({old})", "apply IH", "exact ha")
    script += _cases("hprefix", 7) + _parts(prefix, 7)
    for name, lower, upper, exponent, successor, low_fact, high_fact in (
        ("hB", "x2", "x1", "S k", "S (S k)", facts[2], facts[1]),
        ("hR", "x3", "x2", "k", "S k", facts[3], facts[2]),
    ):
        script += (f"have {name} : {upper} = b * {lower}", f"trans {lower} * b")
        script += _call("pow_successor_pair_mul", "b", exponent, successor, lower, upper)
        script += ("refl", "exact " + low_fact, "exact " + high_fact, "apply mul_comm")
    script += tuple("exists " + term for term in (
        "a * x", "b * x1", "x1", "x2", "a * x4 + x1", "b * x5 + x4", "b * x6 + 2 * x5",
    ))
    for base, previous, value, fact in (("a", "x", "a * x", facts[0]), ("b", "x1", "b * x1", facts[1])):
        script += ("split",) + _call("pow_successor_compose", base, "S (S k)", previous, value)
        script += ("exact " + fact, "apply mul_comm")
    script += ("split", "exact " + facts[1], "split", "exact " + facts[2])
    script += ("split", "rewrite " + facts[4])
    script += _call("lte_natural_difference_successor", "a", "b", "d", "x1", "x4") + ("exact ha",)
    script += ("split", "rewrite hB", "rewrite hB")
    script += _call("lte_first_correction_successor", "a", "b", "d", "S (S k)", "x2", "x4", "x5")
    script += ("exact ha", "exact " + facts[5], "rewrite hR")
    script += ("have hfirst : x4 = S (S k) * (b * x3) + d * x5", "trans S (S k) * x2 + d * x5", "exact " + facts[5], "rewrite hR", "refl")
    script += _call("lte_twice_correction_successor", "b", "d", "S k", "x3", "x5", "x4", "x6")
    script += ("exact hfirst", "exact " + facts[6])
    rows.append(_row(
        spec, "lte_power_difference_second_order_exists",
        "forall a b d k. a = b + d -> exists A B R T Q C H. ("
        + _second_order("a", "b", "d", "k", "A", "B", "R", "T", "Q", "C", "H", "result") + ")",
        (
            "lte_power_zero_exact", "lte_power_one_exact", "lte_power_two_exact",
            "lte_natural_difference_square", "lte_natural_difference_successor",
            "lte_first_correction_successor", "lte_twice_correction_successor",
            "pow_successor_pair_mul", "pow_successor_compose", "mul_comm", "mul_one",
        ) + _polynomial_expansion_dependencies(base_left, base_right),
        script,
        "Construct the real powers, difference quotient, first correction, and doubled triangular correction at every exponent at least two.",
    ))
    rows.extend(_divisibility_rows(spec))
    rows.extend(_valuation_rows(spec))
    rows.extend(_quotient_rows(spec))
    rows.extend(_lifting_step_rows(spec))
    rows.extend(_iteration_rows(spec))
    rows.extend(_public_lte_rows(spec))
    return tuple(rows)


def _divisibility_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """Actual natural divisibility and power transport, without modular oracles."""
    rows = [
        _row(
            spec, "lte_nondivisor_nonzero",
            f"forall p x. ~({_dvd('p', 'x', 'nonzero')}) -> ~(x = 0)",
            ("multiple_zero",),
            _intro("p", "x", "hnot", "hzero")
            + ("apply hnot", "rewrite hzero") + _call("multiple_zero", "p"),
            "A value not divisible by p is nonzero, for every p including zero.",
        ),
        _row(
            spec, "lte_prime_nondivisor_one",
            f"forall p. ({_prime('p', 'unit_prime')}) -> ~({_dvd('p', '1', 'unit')})",
            ("mul_eq_one_components",),
            _intro("p", "hp", "hdiv")
            + ("cases hdiv", "cases hp", "apply hp_left", "have hcomponents : p = 1 /\\ x = 1")
            + _call("mul_eq_one_components", "p", "x")
            + ("symm", "exact hdiv_witness", "cases hcomponents", "exact hcomponents_left"),
            "An actual prime does not divide one.",
        ),
        _row(
            spec, "lte_nondivisor_product_right",
            f"forall p a b. ~({_dvd('p', 'a * b', 'product')}) -> ~({_dvd('p', 'b', 'right')})",
            ("multiple_mul_left",),
            _intro("p", "a", "b", "hnot", "hdiv") + ("apply hnot",)
            + _call("multiple_mul_left", "p", "b", "a") + ("exact hdiv",),
            "Nondivisibility of a product excludes divisibility of its right factor.",
        ),
        _row(
            spec, "lte_nondivisor_add_multiple",
            f"forall p R D u. ~({_dvd('p', 'R', 'summand')}) -> ({_dvd('p', 'D', 'multiple')}) -> ~({_dvd('p', 'R + D * u', 'sum')})",
            ("balanced_zero_congruence_implies_multiple", "mul_assoc", "zero_add"),
            _intro("p", "R", "D", "u", "hnot", "hD", "hsum")
            + ("cases hD", "cases hsum", "apply hnot")
            + _call("balanced_zero_congruence_implies_multiple", "p", "R")
            + ("exists x * u", "exists x1", "trans R + (p * x) * u", "congr", "refl", "symm", "apply mul_assoc",
               "have hsumcopy : R + (p * x) * u = p * x1", "rewrite hD_witness at hsum_witness", "exact hsum_witness",
               "trans p * x1", "exact hsumcopy", "symm", "apply zero_add"),
            "Adding any actual p-multiple preserves nondivisibility; natural differences are witnessed by balanced equality.",
        ),
        _row(
            spec, "lte_prime_nondivisor_two",
            f"forall p. ({_prime('p', 'odd_prime')}) -> ~(p = 2) -> ~({_dvd('p', '2', 'two')})",
            ("prime_divisor_of_prime_forces_equality", "prime_two"),
            _intro("p", "hp", "hne", "hdiv") + ("apply hne",)
            + _call("prime_divisor_of_prime_forces_equality", "p", "2")
            + ("exact hp", "exact prime_two", "exact hdiv"),
            "Two is a nondivisor unit for every prime explicitly different from two.",
        ),
    ]
    # Induction is over the actual historic power graph, including exponent zero.
    rows.append(_row(
        spec, "lte_nondivisor_power",
        f"forall p b n B. ({_prime('p', 'power_prime')}) -> ~({_dvd('p', 'b', 'power_base')}) -> ({_pow('b', 'n', 'B', 'power_source')}) -> ~({_dvd('p', 'B', 'power_result')})",
        ("pow_zero", "lte_prime_nondivisor_one", "pow_successor_decompose", "prime_nondivisor_mul"),
        _intro("p", "b", "n") + ("induction n",)
        + _intro("B", "hp", "hnot", "hpow", "hdiv")
        + ("have hB : B = 1",) + _call("pow_zero", "b", "0", "B")
        + ("refl", "exact hpow") + _call("lte_prime_nondivisor_one", "p")
        + ("exact hp", "rewrite hB at hdiv", "exact hdiv")
        + _intro("B", "hp", "hnot", "hpow", "hdiv")
        + (f"have hprev : exists r. ({_pow('b', 'n', 'r', 'power_previous')}) /\\ B = r * b",)
        + _call("pow_successor_decompose", "b", "n", "S n", "B")
        + ("refl", "exact hpow", "cases hprev", "cases hprev_witness")
        + _call("prime_nondivisor_mul", "p", "x", "b") + ("exact hp", "intro hfactor")
        + _call("IH", "x") + ("exact hp", "exact hnot", "exact hprev_witness_left", "exact hfactor", "exact hnot",
                                "rewrite hprev_witness_right at hdiv", "exact hdiv"),
        "Every witnessed power of a nondivisor remains a nondivisor of the actual prime, including the zeroth power.",
    ))
    rows.append(_row(
        spec, "lte_prime_divides_correction",
        f"forall p d r T C H. ({_prime('p', 'correction_prime')}) -> ~(p = 2) -> ({_dvd('p', 'd', 'correction_difference')}) -> 2 * C = (p * r) * T + d * H -> ({_dvd('p', 'C', 'correction_result')})",
        ("gauss_coprime_cancel", "prime_not_divides_coprime", "lte_prime_nondivisor_two", "multiple_add", "mul_assoc"),
        _intro("p", "d", "r", "T", "C", "H", "hp", "hne", "hd", "hC")
        + _call("gauss_coprime_cancel", "p", "2", "C")
        + _call("prime_not_divides_coprime", "p", "2") + ("exact hp", "intro hdiv")
        + _call("lte_prime_nondivisor_two", "p") + ("exact hp", "exact hne", "exact hdiv", "rewrite hC")
        + _call("multiple_add", "p", "(p * r) * T", "d * H")
        + ("exists r * T", "apply mul_assoc", "cases hd", "exists x * H", "rewrite hd_witness", "apply mul_assoc"),
        "The doubled second-order remainder is divisible by an odd prime, so its actual correction is divisible too.",
    ))
    left, right = "p * R + d * (p * x)", "p * (R + d * x)"
    rows.append(_row(
        spec, "lte_odd_prime_quotient_unit",
        f"forall p d r R T Q C H. ({_prime('p', 'quotient_prime')}) -> ~(p = 2) -> ({_dvd('p', 'd', 'quotient_difference')}) -> ~({_dvd('p', 'R', 'quotient_base')}) -> Q = p * R + d * C -> 2 * C = (p * r) * T + d * H -> exists u. Q = p * u /\\ ~({_dvd('p', 'u', 'quotient_unit')})",
        ("lte_prime_divides_correction", "lte_nondivisor_add_multiple") + _polynomial_expansion_dependencies(left, right),
        _intro("p", "d", "r", "R", "T", "Q", "C", "H", "hp", "hne", "hd", "hR", "hQ", "hC")
        + (f"have hdiv : {_dvd('p', 'C', 'quotient_correction')}",)
        + _call("lte_prime_divides_correction", "p", "d", "r", "T", "C", "H")
        + ("exact hp", "exact hne", "exact hd", "exact hC", "cases hdiv", "exists R + d * x", "split", "rewrite hQ", "rewrite hdiv_witness")
        + _commutative_expansion_identity(left, right)
        + ("intro hunit",) + _call("lte_nondivisor_add_multiple", "p", "R", "d", "x")
        + ("exact hR", "exact hd", "exact hunit"),
        "The prime-step quotient is exactly p times a genuine p-nondivisible cofactor; no valuation conclusion is assumed.",
    ))
    for name, variable, target in (
        ("lte_power_exponent_eq_transport", "n", "m"),
        ("lte_power_value_eq_transport", "A", "B"),
    ):
        source = _pow("a", "n", "A", name + "source")
        result = _pow("a", "m" if variable == "n" else "n", "B" if variable == "A" else "A", name + "result")
        variables = ("a", "n", "m", "A") if variable == "n" else ("a", "n", "A", "B")
        rows.append(_row(
            spec, name, f"forall {' '.join(variables)}. {variable} = {target} -> ({source}) -> ({result})", (),
            _intro(*variables, "heq", "hpow") + _rewrite("heq", variable, source, at="hpow") + ("exact hpow",),
            "Equality transports one actual relational-power argument without changing the graph or adding a choice principle.",
        ))
    rows.append(_row(
        spec, "lte_power_iteration_construct",
        f"forall a n k m A C. m = n * k -> ({_pow('a', 'n', 'A', 'iteration_base')}) -> ({_pow('A', 'k', 'C', 'iteration_outer')}) -> ({_pow('a', 'm', 'C', 'iteration_result')})",
        ("pow_exists", "pow_mul_exp", "lte_power_value_eq_transport"),
        _intro("a", "n", "k", "m", "A", "C", "hm", "hA", "hC")
        + (f"have hex : exists z. ({_pow('a', 'm', 'z', 'iteration_exists')})",)
        + _call("pow_exists", "a", "m") + ("cases hex",)
        + _call("lte_power_value_eq_transport", "a", "m", "x", "C") + ("symm",)
        + _call("pow_mul_exp", "a", "n", "k", "m", "A", "C", "x")
        + ("exact hm", "exact hA", "exact hC", "exact hex_witness", "exact hex_witness"),
        "Construct a composed power graph from two actual powers and their exact multiplied exponent.",
    ))
    return tuple(rows)


def _valuation_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """Construct maximal valuation graphs from genuine powers and cofactors."""
    cofactor = _and(_pow("p", "e", "P", "self_cofactor"), "p = P * u", "~(u = 0)", "~(" + _dvd("p", "u", "self_unit") + ")")
    facts = tuple(_part("hcofactor_witness_witness", 4, i) for i in range(4))
    left, right = "(x3 * p) * x2", "p * (x3 * x2)"
    rows = [
        _row(
            spec, "lte_prime_self_valuation_value",
            f"forall p e. ({_prime('p', 'self_prime')}) -> ({_val('p', 'p', 'e', 'self_source')}) -> e = 1",
            ("prime_nonzero", "prime_divisor_power_valuation_nonzero", "multiple_refl", "nonzero_is_succ",
             "power_valuation_exact_cofactor", "pow_successor_decompose", "mul_left_cancel_nonzero", "mul_one",
             "mul_eq_one_components", "eq_decidable", "lte_prime_nondivisor_one", "pow_positive_exponent_base_divides")
            + _polynomial_expansion_dependencies(left, right),
            _intro("p", "e", "hp", "hval")
            + ("have hpzero : ~(p = 0)", "intro hz") + _call("prime_nonzero", "p") + ("exact hp", "exact hz",
               "have hene : ~(e = 0)", "intro hezero")
            + _call("prime_divisor_power_valuation_nonzero", "p", "p", "e")
            + ("exact hp", "exact hpzero", "exact hval") + _call("multiple_refl", "p") + ("exact hezero",)
            + ("have hsucc : exists k. e = S k",) + _call("nonzero_is_succ", "e") + ("exact hene", "cases hsucc")
            + (f"have hcofactor : exists P u. ({cofactor})",) + _call("power_valuation_exact_cofactor", "p", "p", "e")
            + ("exact hp", "exact hpzero", "exact hval") + _cases("hcofactor", 2) + _parts("hcofactor_witness_witness", 4)
            + (f"have hprev : exists r. ({_pow('p', 'x', 'r', 'self_previous')}) /\\ x1 = r * p",)
            + _call("pow_successor_decompose", "p", "x", "e", "x1")
            + ("exact hsucc_witness", "exact " + facts[0], "cases hprev", "cases hprev_witness",
               "have hproduct : 1 = x3 * x2")
            + _call("mul_left_cancel_nonzero", "p", "1", "x3 * x2")
            + ("exact hpzero", "trans p", "apply mul_one", "trans x1 * x2", "exact " + facts[1], "rewrite hprev_witness_right")
            + _commutative_expansion_identity(left, right)
            + ("have hcomponents : x3 = 1 /\\ x2 = 1",) + _call("mul_eq_one_components", "x3", "x2")
            + ("symm", "exact hproduct", "cases hcomponents",
               "specialize eq_decidable x", "specialize eq_decidable 0", "cases eq_decidable",
               "trans S x", "exact hsucc_witness", "rewrite eq_decidable_left", "refl", "exfalso")
            + _call("lte_prime_nondivisor_one", "p") + ("exact hp", f"have hdiv : {_dvd('p', 'x3', 'self_previous_divisor')}")
            + _call("pow_positive_exponent_base_divides", "p", "x", "x3")
            + ("exact eq_decidable_right", "exact hprev_witness_left", "rewrite hcomponents_left at hdiv", "exact hdiv"),
            "Every maximal valuation of a prime at itself is exactly one, derived by actual cofactor cancellation.",
        ),
        _row(
            spec, "lte_prime_self_valuation",
            f"forall p. ({_prime('p', 'self_construct_prime')}) -> ({_val('p', 'p', '1', 'self_construct_result')})",
            ("power_valuation_exists", "lte_prime_self_valuation_value", "prime_valuation_exponent_eq_transport"),
            _intro("p", "hp") + (f"have hex : exists e. ({_val('p', 'p', 'e', 'self_construct_exists')})",)
            + _call("power_valuation_exists", "p", "p") + ("cases hex",)
            + _call("prime_valuation_exponent_eq_transport", "p", "p", "x", "1")
            + _call("lte_prime_self_valuation_value", "p", "x")
            + ("exact hp", "exact hex_witness", "exact hex_witness"),
            "Construct the actual bounded maximal valuation graph Val(p,p,1) for an actual prime.",
        ),
        _row(
            spec, "lte_valuation_product_exact",
            f"forall p a b e f. ({_prime('p', 'product_prime')}) -> ~(a = 0) -> ~(b = 0) -> ({_val('p', 'a', 'e', 'product_left')}) -> ({_val('p', 'b', 'f', 'product_right')}) -> ({_val('p', 'a * b', 'e + f', 'product_result')})",
            ("power_valuation_exists", "prime_power_valuation_mul", "prime_valuation_exponent_eq_transport"),
            _intro("p", "a", "b", "e", "f", "hp", "ha", "hb", "hleft", "hright")
            + (f"have hex : exists g. ({_val('p', 'a * b', 'g', 'product_exists')})",)
            + _call("power_valuation_exists", "p", "a * b") + ("cases hex",)
            + _call("prime_valuation_exponent_eq_transport", "p", "a * b", "x", "e + f")
            + _call("prime_power_valuation_mul", "p", "a", "b", "e", "f", "x")
            + ("exact hp", "exact ha", "exact hb", "exact hleft", "exact hright", "exact hex_witness", "exact hex_witness"),
            "Construct the exact sum valuation of a nonzero product instead of requiring its output valuation as an input.",
        ),
        _row(
            spec, "lte_prime_power_valuation_exact",
            f"forall p e P. ({_prime('p', 'prime_power_prime')}) -> ({_pow('p', 'e', 'P', 'prime_power_source')}) -> ({_val('p', 'P', 'e', 'prime_power_result')})",
            ("prime_valuation_exponent_eq_transport", "prime_power_valuation_pow", "prime_nonzero", "lte_prime_self_valuation", "mul_one"),
            _intro("p", "e", "P", "hp", "hpow")
            + _call("prime_valuation_exponent_eq_transport", "p", "P", "e * 1", "e") + ("apply mul_one",)
            + _call("prime_power_valuation_pow", "p", "p", "e", "1", "P")
            + ("exact hp", "intro hz") + _call("prime_nonzero", "p") + ("exact hp", "exact hz")
            + _call("lte_prime_self_valuation", "p") + ("exact hp", "exact hpow"),
            "The actual e-th power of a prime has exactly valuation e, including exponent zero.",
        ),
        _row(
            spec, "lte_valuation_from_exact_cofactor",
            f"forall p e P u X. ({_prime('p', 'cofactor_prime')}) -> ({_pow('p', 'e', 'P', 'cofactor_power')}) -> X = P * u -> ~({_dvd('p', 'u', 'cofactor_unit')}) -> ({_val('p', 'X', 'e', 'cofactor_result')})",
            ("power_valuation_value_eq_transport", "prime_valuation_exponent_eq_transport", "lte_valuation_product_exact",
             "pow_nonzero_of_one_le", "one_le_of_ne_zero", "prime_nonzero", "lte_nondivisor_nonzero",
             "lte_prime_power_valuation_exact", "prime_valuation_zero_of_nondivisor"),
            _intro("p", "e", "P", "u", "X", "hp", "hpow", "hX", "hunit")
            + ("have hu : ~(u = 0)", "intro hz") + _call("lte_nondivisor_nonzero", "p", "u") + ("exact hunit", "exact hz")
            + _call("power_valuation_value_eq_transport", "p", "P * u", "X", "e") + ("symm", "exact hX")
            + _call("prime_valuation_exponent_eq_transport", "p", "P * u", "e + 0", "e") + ("apply PA3",)
            + _call("lte_valuation_product_exact", "p", "P", "u", "e", "0")
            + ("exact hp", "intro hPzero") + _call("pow_nonzero_of_one_le", "p", "e", "P")
            + _call("one_le_of_ne_zero", "p") + ("intro hpzero",) + _call("prime_nonzero", "p")
            + ("exact hp", "exact hpzero", "exact hpow", "exact hPzero", "exact hu")
            + _call("lte_prime_power_valuation_exact", "p", "e", "P") + ("exact hp", "exact hpow")
            + _call("prime_valuation_zero_of_nondivisor", "p", "u") + ("exact hp", "exact hu", "exact hunit"),
            "An actual prime-power times a genuine nondivisor cofactor constructs its precise maximal valuation, including the unit boundary.",
        ),
    ]
    return tuple(rows)


def _quotient_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """The two arithmetic branches: a prime exponent and a nondivisor exponent."""
    prefix = "hsecond" + "_witness" * 7
    facts = tuple(_part(prefix, 7, i) for i in range(7))
    prime_result = _and(
        _pow("a", "p", "A", "prime_step_A"), _pow("b", "p", "B", "prime_step_B"),
        "A = B + d * Q", "Q = p * u", "~(" + _dvd("p", "u", "prime_step_unit") + ")",
    )
    script = _intro("p", "a", "b", "d", "hp", "hne", "ha", "hd", "hb")
    script += ("have hindex : exists k. p = S (S k)",) + _call("prime_is_succ_succ", "p") + ("exact hp", "cases hindex")
    script += ("have hsecond : exists A B R T Q C H. (" + _second_order("a", "b", "d", "x", "A", "B", "R", "T", "Q", "C", "H", "prime_second") + ")",)
    script += _call("lte_power_difference_second_order_exists", "a", "b", "d", "x") + ("exact ha",)
    script += _cases("hsecond", 7) + _parts(prefix, 7)
    script += (f"have hunit : exists u. x5 = p * u /\\ ~({_dvd('p', 'u', 'prime_chosen_unit')})",)
    script += _call("lte_odd_prime_quotient_unit", "p", "d", "S x", "x3", "x4", "x5", "x6", "x7")
    script += ("exact hp", "exact hne", "exact hd", "intro hdivR")
    script += _call("lte_nondivisor_power", "p", "b", "S x", "x3")
    script += ("exact hp", "exact hb", "exact " + facts[2], "exact hdivR",
               "rewrite hindex_witness", "exact " + facts[5], "rewrite hindex_witness", "exact " + facts[6],
               "cases hunit", "cases hunit_witness")
    script += tuple("exists " + value for value in ("x1", "x2", "x5", "x8"))
    for base, value, fact in (("a", "x1", facts[0]), ("b", "x2", facts[1])):
        script += ("split",) + _call("lte_power_exponent_eq_transport", base, "S (S x)", "p", value)
        script += ("symm", "exact hindex_witness", "exact " + fact)
    script += ("split", "exact " + facts[4], "split", "exact hunit_witness_left", "exact hunit_witness_right")
    rows = [_row(
        spec, "lte_odd_prime_power_difference_quotient",
        f"forall p a b d. ({_prime('p', 'prime_step_prime')}) -> ~(p = 2) -> a = b + d -> ({_dvd('p', 'd', 'prime_step_difference')}) -> ~({_dvd('p', 'b', 'prime_step_base')}) -> exists A B Q u. ({prime_result})",
        ("prime_is_succ_succ", "lte_power_difference_second_order_exists", "lte_odd_prime_quotient_unit", "lte_nondivisor_power", "lte_power_exponent_eq_transport"),
        script,
        "Construct the actual p-th powers and their geometric quotient p*u with a genuine p-nondivisible cofactor for every odd prime.",
    )]
    unit_result = _and(
        _pow("a", "n", "A", "unit_step_A"), _pow("b", "n", "B", "unit_step_B"),
        "A = B + d * Q", "~(" + _dvd("p", "Q", "unit_step_quotient") + ")",
    )
    script = _intro("p", "a", "b", "d", "n", "hp", "ha", "hd", "hb", "hn")
    script += ("specialize eq_decidable n", "specialize eq_decidable 1", "cases eq_decidable",
               "exists a", "exists b", "exists 1")
    for base in ("a", "b"):
        script += ("split",) + _call("lte_power_exponent_eq_transport", base, "1", "n", base)
        script += ("symm", "exact eq_decidable_left") + _call("lte_power_one_exact", base)
    script += ("split", "trans b + d", "exact ha", "congr", "refl", "symm", "apply mul_one", "intro hdiv1")
    script += _call("lte_prime_nondivisor_one", "p") + ("exact hp", "exact hdiv1",
               "have hnzero : ~(n = 0)", "intro hz") + _call("lte_nondivisor_nonzero", "p", "n") + ("exact hn", "exact hz")
    script += ("have hfirstindex : exists k. n = S k",) + _call("nonzero_is_succ", "n") + ("exact hnzero", "cases hfirstindex",
               "have hindexzero : ~(x = 0)", "intro hxzero", "apply eq_decidable_right", "trans S x", "exact hfirstindex_witness", "rewrite hxzero", "refl",
               "have hsecondindex : exists k. x = S k")
    script += _call("nonzero_is_succ", "x") + ("exact hindexzero", "cases hsecondindex",
               "have hnindex : n = S (S x1)", "trans S x", "exact hfirstindex_witness", "rewrite hsecondindex_witness", "refl")
    script += ("have hsecond : exists A B R T Q C H. (" + _second_order("a", "b", "d", "x1", "A", "B", "R", "T", "Q", "C", "H", "unit_second") + ")",)
    script += _call("lte_power_difference_second_order_exists", "a", "b", "d", "x1") + ("exact ha",)
    script += _cases("hsecond", 7) + _parts(prefix, 7)
    script += tuple("exists " + value for value in ("x2", "x3", "x6"))
    for base, value, fact in (("a", "x2", facts[0]), ("b", "x3", facts[1])):
        script += ("split",) + _call("lte_power_exponent_eq_transport", base, "S (S x1)", "n", value)
        script += ("symm", "exact hnindex", "exact " + fact)
    script += ("split", "exact " + facts[4], "intro hQdiv",
               "have hfirst : x6 = n * x4 + d * x7", "rewrite hnindex", "exact " + facts[5], "rewrite hfirst at hQdiv")
    script += _call("lte_nondivisor_add_multiple", "p", "n * x4", "d", "x7")
    script += ("intro hproduct",) + _call("prime_nondivisor_mul", "p", "n", "x4")
    script += ("exact hp", "exact hn", "intro hRdiv") + _call("lte_nondivisor_power", "p", "b", "S x1", "x4")
    script += ("exact hp", "exact hb", "exact " + facts[2], "exact hRdiv", "exact hproduct", "exact hd", "exact hQdiv")
    rows.append(_row(
        spec, "lte_coprime_power_difference_quotient",
        f"forall p a b d n. ({_prime('p', 'unit_step_prime')}) -> a = b + d -> ({_dvd('p', 'd', 'unit_step_difference')}) -> ~({_dvd('p', 'b', 'unit_step_base')}) -> ~({_dvd('p', 'n', 'unit_step_exponent')}) -> exists A B Q. ({unit_result})",
        ("eq_decidable", "lte_power_exponent_eq_transport", "lte_power_one_exact", "mul_one", "lte_prime_nondivisor_one",
         "lte_nondivisor_nonzero", "nonzero_is_succ", "lte_power_difference_second_order_exists", "lte_nondivisor_add_multiple",
         "prime_nondivisor_mul", "lte_nondivisor_power"),
        script,
        "For every exponent not divisible by the actual prime, construct real power differences with a nondivisible geometric quotient; exponent one is handled explicitly.",
    ))
    return tuple(rows)


def _lifting_step_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """Close the actual valuation of each constructed power difference."""
    rows = [_row(
        spec, "lte_power_difference_valuation_step",
        f"forall p a b d n A B Q e f g. e + f = g -> ({_prime('p', 'valuation_step_prime')}) -> ~(d = 0) -> ({_dvd('p', 'd', 'valuation_step_divisor')}) -> ~({_dvd('p', 'b', 'valuation_step_base')}) -> ~(Q = 0) -> ({_val('p', 'd', 'e', 'valuation_step_input')}) -> ({_val('p', 'Q', 'f', 'valuation_step_quotient')}) -> ({_pow('a', 'n', 'A', 'valuation_step_A')}) -> ({_pow('b', 'n', 'B', 'valuation_step_B')}) -> A = B + d * Q -> ({_lifted_difference('p', 'a', 'b', 'n', 'g', 'A', 'B', 'd * Q', 'valuation_step_result')})",
        ("mul_ne_zero", "multiple_mul_right", "lte_nondivisor_power", "prime_valuation_exponent_eq_transport", "lte_valuation_product_exact"),
        _intro("p", "a", "b", "d", "n", "A", "B", "Q", "e", "f", "g",
               "hg", "hp", "hdzero", "hd", "hb", "hQzero", "hvd", "hvQ", "hA", "hB", "hbalance")
        + ("split", "exact hA", "split", "exact hB", "split", "exact hbalance", "split", "intro hDzero")
        + _call("mul_ne_zero", "d", "Q") + ("exact hdzero", "exact hQzero", "exact hDzero", "split")
        + _call("multiple_mul_right", "p", "d", "Q") + ("exact hd", "split", "intro hBdiv")
        + _call("lte_nondivisor_power", "p", "b", "n", "B") + ("exact hp", "exact hb", "exact hB", "exact hBdiv")
        + _call("prime_valuation_exponent_eq_transport", "p", "d * Q", "e + f", "g") + ("exact hg",)
        + _call("lte_valuation_product_exact", "p", "d", "Q", "e", "f")
        + ("exact hp", "exact hdzero", "exact hQzero", "exact hvd", "exact hvQ"),
        "Combine real power graphs, a nonzero difference quotient, and its independently constructed valuation into the exact lifted difference.",
    )]
    prime_quotient = _and(
        _pow("a", "p", "A", "lift_prime_A"), _pow("b", "p", "B", "lift_prime_B"),
        "A = B + d * Q", "Q = p * u", "~(" + _dvd("p", "u", "lift_prime_unit") + ")",
    )
    facts = tuple(_part("hquotient" + "_witness" * 4, 5, i) for i in range(5))
    script = _intro("p", "a", "b", "d", "e", "hp", "hne", "ha", "hdzero", "hd", "hb", "hval")
    script += ("have hquotient : exists A B Q u. (" + prime_quotient + ")",)
    script += _call("lte_odd_prime_power_difference_quotient", "p", "a", "b", "d")
    script += ("exact hp", "exact hne", "exact ha", "exact hd", "exact hb")
    script += _cases("hquotient", 4) + _parts("hquotient" + "_witness" * 4, 5)
    script += ("have hQzero : ~(x2 = 0)", "intro hz", "rewrite " + facts[3] + " at hz")
    script += _call("mul_ne_zero", "p", "x3")
    script += ("intro hpzero",) + _call("prime_nonzero", "p") + ("exact hp", "exact hpzero", "intro huzero")
    script += _call("lte_nondivisor_nonzero", "p", "x3") + ("exact " + facts[4], "exact huzero", "exact hz",
               "exists x", "exists x1", "exists d * x2")
    script += _call("lte_power_difference_valuation_step", "p", "a", "b", "d", "p", "x", "x1", "x2", "e", "1", "S e")
    script += ("simp", "exact hp", "exact hdzero", "exact hd", "exact hb", "exact hQzero", "exact hval")
    script += _call("lte_valuation_from_exact_cofactor", "p", "1", "p", "x3", "x2")
    script += ("exact hp",) + _call("lte_power_one_exact", "p")
    script += ("exact " + facts[3], "exact " + facts[4], "exact " + facts[0], "exact " + facts[1], "exact " + facts[2])
    rows.append(_row(
        spec, "lte_odd_prime_power_step",
        f"forall p a b d e. ({_prime('p', 'lift_prime_domain')}) -> ~(p = 2) -> a = b + d -> ~(d = 0) -> ({_dvd('p', 'd', 'lift_prime_difference')}) -> ~({_dvd('p', 'b', 'lift_prime_base')}) -> ({_val('p', 'd', 'e', 'lift_prime_input')}) -> exists A B D. ({_lifted_difference('p', 'a', 'b', 'p', 'S e', 'A', 'B', 'D', 'lift_prime_result')})",
        ("lte_odd_prime_power_difference_quotient", "mul_ne_zero", "prime_nonzero", "lte_nondivisor_nonzero",
         "lte_power_difference_valuation_step", "lte_valuation_from_exact_cofactor", "lte_power_one_exact"),
        script,
        "Raising a genuine nonzero p-divisible difference to an odd-prime exponent increases its exact valuation by one and constructs all power/difference witnesses.",
    ))
    unit_quotient = _and(
        _pow("a", "n", "A", "lift_unit_A"), _pow("b", "n", "B", "lift_unit_B"),
        "A = B + d * Q", "~(" + _dvd("p", "Q", "lift_unit_quotient") + ")",
    )
    facts = tuple(_part("hquotient" + "_witness" * 3, 4, i) for i in range(4))
    script = _intro("p", "a", "b", "d", "n", "e", "hp", "ha", "hdzero", "hd", "hb", "hn", "hval")
    script += ("have hquotient : exists A B Q. (" + unit_quotient + ")",)
    script += _call("lte_coprime_power_difference_quotient", "p", "a", "b", "d", "n")
    script += ("exact hp", "exact ha", "exact hd", "exact hb", "exact hn")
    script += _cases("hquotient", 3) + _parts("hquotient" + "_witness" * 3, 4)
    script += ("have hQzero : ~(x2 = 0)", "intro hz") + _call("lte_nondivisor_nonzero", "p", "x2")
    script += ("exact " + facts[3], "exact hz", "exists x", "exists x1", "exists d * x2")
    script += _call("lte_power_difference_valuation_step", "p", "a", "b", "d", "n", "x", "x1", "x2", "e", "0", "e")
    script += ("apply PA3", "exact hp", "exact hdzero", "exact hd", "exact hb", "exact hQzero", "exact hval")
    script += _call("prime_valuation_zero_of_nondivisor", "p", "x2")
    script += ("exact hp", "exact hQzero", "exact " + facts[3], "exact " + facts[0], "exact " + facts[1], "exact " + facts[2])
    rows.append(_row(
        spec, "lte_coprime_exponent_step",
        f"forall p a b d n e. ({_prime('p', 'lift_unit_domain')}) -> a = b + d -> ~(d = 0) -> ({_dvd('p', 'd', 'lift_unit_difference')}) -> ~({_dvd('p', 'b', 'lift_unit_base')}) -> ~({_dvd('p', 'n', 'lift_unit_exponent')}) -> ({_val('p', 'd', 'e', 'lift_unit_input')}) -> exists A B D. ({_lifted_difference('p', 'a', 'b', 'n', 'e', 'A', 'B', 'D', 'lift_unit_result')})",
        ("lte_coprime_power_difference_quotient", "lte_nondivisor_nonzero", "lte_power_difference_valuation_step", "prime_valuation_zero_of_nondivisor"),
        script,
        "Every exponent not divisible by p preserves the exact valuation of the difference, with actual power/difference witnesses and nonzero guards.",
    ))
    return tuple(rows)


def _iteration_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """Prime-power iteration followed by the actual exponent's unit cofactor."""
    previous = _tower("p", "a", "b", "k", "e", "q", "A", "B", "D", "tower_previous")
    prev_prefix = "hprevious" + "_witness" * 4
    prev = tuple(_part(prev_prefix, 8, i) for i in range(8))
    step_prefix = "hstep" + "_witness" * 3
    step = tuple(_part(step_prefix, 7, i) for i in range(7))
    script = _intro("p", "a", "b", "d", "e") + ("induction k",)
    premises = ("hp", "hne", "ha", "hdzero", "hd", "hb", "hval")
    script += _intro(*premises) + ("exists 1", "exists a", "exists b", "exists d", "split")
    script += _call("lte_power_zero_exact", "p")
    for base in ("a", "b"):
        script += ("split",) + _call("lte_power_one_exact", base)
    script += ("split", "exact ha", "split", "exact hdzero", "split", "exact hd", "split", "exact hb")
    script += _call("prime_valuation_exponent_eq_transport", "p", "d", "e", "e + 0")
    script += ("symm", "apply PA3", "exact hval")
    script += _intro(*premises) + ("have hprevious : exists q A B D. (" + previous + ")", "apply IH")
    script += tuple("exact " + premise for premise in premises)
    script += _cases("hprevious", 4) + _parts(prev_prefix, 8)
    script += ("have hstep : exists A B D. (" + _lifted_difference("p", "x1", "x2", "p", "S (e + k)", "A", "B", "D", "tower_step") + ")",)
    script += _call("lte_odd_prime_power_step", "p", "x1", "x2", "x3", "e + k")
    script += ("exact hp", "exact hne") + tuple("exact " + fact for fact in prev[3:])
    script += _cases("hstep", 3) + _parts(step_prefix, 7)
    script += tuple("exists " + value for value in ("x * p", "x4", "x5", "x6")) + ("split",)
    script += _call("pow_successor_compose", "p", "k", "x", "x * p") + ("exact " + prev[0], "refl")
    for base, old_value, value, old_fact, new_fact in (
        ("a", "x1", "x4", prev[1], step[0]), ("b", "x2", "x5", prev[2], step[1]),
    ):
        script += ("split",) + _call("lte_power_iteration_construct", base, "x", "p", "x * p", old_value, value)
        script += ("refl", "exact " + old_fact, "exact " + new_fact)
    for fact in step[2:6]:
        script += ("split", "exact " + fact)
    script += _call("prime_valuation_exponent_eq_transport", "p", "x6", "S (e + k)", "e + S k")
    script += ("symm", "apply PA4", "exact " + step[6])
    rows = [_row(
        spec, "lte_prime_power_iteration",
        f"forall p a b d e k. ({_prime('p', 'tower_prime')}) -> ~(p = 2) -> a = b + d -> ~(d = 0) -> ({_dvd('p', 'd', 'tower_divisor')}) -> ~({_dvd('p', 'b', 'tower_unit')}) -> ({_val('p', 'd', 'e', 'tower_input')}) -> exists q A B D. ({_tower('p', 'a', 'b', 'k', 'e', 'q', 'A', 'B', 'D', 'tower_result')})",
        ("lte_power_zero_exact", "lte_power_one_exact", "prime_valuation_exponent_eq_transport", "lte_odd_prime_power_step", "pow_successor_compose", "lte_power_iteration_construct"),
        script,
        "Ordinary HA induction constructs every prime-power exponent and its power difference, raising the valuation by exactly the number of prime steps.",
    )]
    cofactor = _and(_pow("p", "k", "P", "general_exponent_power"), "n = P * u", "~(u = 0)", "~(" + _dvd("p", "u", "general_exponent_unit") + ")")
    cofactor_prefix = "hcofactor" + "_witness" * 2
    cof = tuple(_part(cofactor_prefix, 4, i) for i in range(4))
    tower_prefix = "htower" + "_witness" * 4
    tower = tuple(_part(tower_prefix, 8, i) for i in range(8))
    script = _intro("p", "a", "b", "d", "n", "e", "k", "hp", "hne", "ha", "hdzero", "hd", "hb", "hnzero", "hvd", "hvn")
    script += ("have hcofactor : exists P u. (" + cofactor + ")",) + _call("power_valuation_exact_cofactor", "p", "n", "k")
    script += ("exact hp", "exact hnzero", "exact hvn") + _cases("hcofactor", 2) + _parts(cofactor_prefix, 4)
    script += ("have htower : exists q A B D. (" + _tower("p", "a", "b", "k", "e", "q", "A", "B", "D", "general_tower") + ")",)
    script += _call("lte_prime_power_iteration", "p", "a", "b", "d", "e", "k")
    script += ("exact hp", "exact hne", "exact ha", "exact hdzero", "exact hd", "exact hb", "exact hvd")
    script += _cases("htower", 4) + _parts(tower_prefix, 8)
    script += ("have hpower : x2 = x",) + _call("pow_functional", "p", "k", "x2", "x")
    script += ("exact " + tower[0], "exact " + cof[0])
    script += ("have hstep : exists A B D. (" + _lifted_difference("p", "x3", "x4", "x1", "e + k", "A", "B", "D", "general_step") + ")",)
    script += _call("lte_coprime_exponent_step", "p", "x3", "x4", "x5", "x1", "e + k")
    script += ("exact hp",) + tuple("exact " + fact for fact in tower[3:7]) + ("exact " + cof[3], "exact " + tower[7])
    script += _cases("hstep", 3) + _parts(step_prefix, 7)
    script += tuple("exists " + value for value in ("x6", "x7", "x8"))
    for base, old_value, value, old_fact, new_fact in (
        ("a", "x3", "x6", tower[1], step[0]), ("b", "x4", "x7", tower[2], step[1]),
    ):
        script += ("split",) + _call("lte_power_iteration_construct", base, "x2", "x1", "n", old_value, value)
        script += ("rewrite hpower", "exact " + cof[1], "exact " + old_fact, "exact " + new_fact)
    for fact in step[2:6]:
        script += ("split", "exact " + fact)
    script += ("exact " + step[6],)
    rows.append(_row(
        spec, "lte_positive_exponent_exact",
        f"forall p a b d n e k. ({_prime('p', 'general_prime')}) -> ~(p = 2) -> a = b + d -> ~(d = 0) -> ({_dvd('p', 'd', 'general_divisor')}) -> ~({_dvd('p', 'b', 'general_unit')}) -> ~(n = 0) -> ({_val('p', 'd', 'e', 'general_difference_valuation')}) -> ({_val('p', 'n', 'k', 'general_exponent_valuation')}) -> exists A B D. ({_lifted_difference('p', 'a', 'b', 'n', 'e + k', 'A', 'B', 'D', 'general_result')})",
        ("power_valuation_exact_cofactor", "lte_prime_power_iteration", "pow_functional", "lte_coprime_exponent_step", "lte_power_iteration_construct"),
        script,
        "For every positive exponent, strip its actual prime-power valuation, iterate the prime step, and apply the nondivisor cofactor step to construct the full exact LTE valuation.",
    ))
    return tuple(rows)


def _public_lte_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """The exact guarded blueprint endpoint and extensional output interface."""
    rows = [_row(
        spec, "lte_strict_difference_nonzero",
        f"forall x y d. ({_lt('y', 'x', 'strict_difference')}) -> x = y + d -> ~(d = 0)",
        ("lt_irrefl_expanded",),
        _intro("x", "y", "d", "hgt", "hbalance", "hdzero")
        + ("have heq : x = y", "trans y + d", "exact hbalance", "rewrite hdzero", "apply PA3",
           "rewrite heq at hgt") + _call("lt_irrefl_expanded", "y") + ("exact hgt",),
        "A witnessed strictly positive natural difference is nonzero.",
    ), _row(
        spec, "lte_exceeds_two_not_two",
        f"forall p. ({_lt('2', 'p', 'above_two')}) -> ~(p = 2)",
        ("lt_irrefl_expanded",),
        _intro("p", "hgt", "heq") + ("rewrite heq at hgt",)
        + _call("lt_irrefl_expanded", "2") + ("exact hgt",),
        "The exact p>2 guard excludes the binary prime without an implicit case extension.",
    )]
    result = _lifted_difference("p", "x", "y", "n", "a + b", "X", "Y", "D", "public_lte_result")
    rows.append(_row(
        spec, "odd_prime_lifting_the_exponent",
        f"forall p x y d n a b. ({_prime('p', 'public_lte_prime')}) -> ({_lt('2', 'p', 'public_lte_odd')}) -> ({_lt('y', 'x', 'public_lte_order')}) -> ~(y = 0) -> ~(n = 0) -> x = y + d -> ({_dvd('p', 'd', 'public_lte_divisor')}) -> ~({_dvd('p', 'x * y', 'public_lte_units')}) -> ({_val('p', 'd', 'a', 'public_lte_difference_valuation')}) -> ({_val('p', 'n', 'b', 'public_lte_exponent_valuation')}) -> exists X Y D. ({result})",
        ("lte_positive_exponent_exact", "lte_exceeds_two_not_two", "lte_strict_difference_nonzero", "lte_nondivisor_product_right"),
        _intro("p", "x", "y", "d", "n", "a", "b", "hp", "hpgt", "hxy", "hyzero", "hnzero", "hbalance", "hdiv", "hunits", "hvd", "hvn")
        + _call("lte_positive_exponent_exact", "p", "x", "y", "d", "n", "a", "b")
        + ("exact hp", "intro hptwo") + _call("lte_exceeds_two_not_two", "p") + ("exact hpgt", "exact hptwo", "exact hbalance", "intro hdzero")
        + _call("lte_strict_difference_nonzero", "x", "y", "d") + ("exact hxy", "exact hbalance", "exact hdzero", "exact hdiv", "intro hydiv")
        + _call("lte_nondivisor_product_right", "p", "x", "y")
        + ("exact hunits", "exact hydiv", "exact hnzero", "exact hvd", "exact hvn"),
        "Full guarded odd-prime LTE: for p>2, x>y>0, n>0, p|(x-y), and p not dividing xy, construct x^n,y^n and their positive difference of exact valuation v_p(x-y)+v_p(n).",
    ))
    rows.append(_row(
        spec, "lte_power_difference_functional",
        f"forall a b n A B D X Y E. ({_pow('a', 'n', 'A', 'functional_A')}) -> ({_pow('b', 'n', 'B', 'functional_B')}) -> A = B + D -> ({_pow('a', 'n', 'X', 'functional_X')}) -> ({_pow('b', 'n', 'Y', 'functional_Y')}) -> X = Y + E -> D = E",
        ("pow_functional", "add_left_cancel"),
        _intro("a", "b", "n", "A", "B", "D", "X", "Y", "E", "hA", "hB", "hD", "hX", "hY", "hE")
        + ("have hAX : A = X",) + _call("pow_functional", "a", "n", "A", "X")
        + ("exact hA", "exact hX", "have hBY : B = Y") + _call("pow_functional", "b", "n", "B", "Y")
        + ("exact hB", "exact hY") + _call("add_left_cancel", "Y", "D", "E")
        + ("trans X", "symm", "rewrite hAX at hD", "rewrite hBY at hD", "exact hD", "exact hE"),
        "Any two witnesses for the same natural power difference have exactly the same value; no selected representation can change the valuation output.",
    ))
    premise = (
        f"({_prime('p', 'supplied_prime')}) -> ({_lt('2', 'p', 'supplied_odd')}) -> ({_lt('y', 'x', 'supplied_order')}) -> ~(y = 0) -> ~(n = 0) -> x = y + d -> ({_dvd('p', 'd', 'supplied_divisor')}) -> ~({_dvd('p', 'x * y', 'supplied_units')}) -> ({_val('p', 'd', 'a', 'supplied_difference_valuation')}) -> ({_val('p', 'n', 'b', 'supplied_exponent_valuation')})"
    )
    prefix = "hresult" + "_witness" * 3
    facts = tuple(_part(prefix, 7, i) for i in range(7))
    script = _intro("p", "x", "y", "d", "n", "a", "b", "X", "Y", "D", "hp", "hpgt", "hxy", "hyzero", "hnzero", "hbalance", "hdiv", "hunits", "hvd", "hvn", "hX", "hY", "hD")
    script += ("have hresult : exists A B E. (" + _lifted_difference("p", "x", "y", "n", "a + b", "A", "B", "E", "supplied_constructed") + ")",)
    script += _call("odd_prime_lifting_the_exponent", "p", "x", "y", "d", "n", "a", "b")
    script += tuple("exact " + name for name in ("hp", "hpgt", "hxy", "hyzero", "hnzero", "hbalance", "hdiv", "hunits", "hvd", "hvn"))
    script += _cases("hresult", 3) + _parts(prefix, 7)
    # x is already a public argument, so the three existential witnesses are x1,x2,x3.
    script += _call("power_valuation_value_eq_transport", "p", "x3", "D", "a + b")
    script += _call("lte_power_difference_functional", "x", "y", "n", "x1", "x2", "x3", "X", "Y", "D")
    script += ("exact " + facts[0], "exact " + facts[1], "exact " + facts[2], "exact hX", "exact hY", "exact hD", "exact " + facts[6])
    rows.append(_row(
        spec, "odd_prime_lifting_the_exponent_value",
        f"forall p x y d n a b X Y D. {premise} -> ({_pow('x', 'n', 'X', 'supplied_X')}) -> ({_pow('y', 'n', 'Y', 'supplied_Y')}) -> X = Y + D -> ({_val('p', 'D', 'a + b', 'supplied_result')})",
        ("odd_prime_lifting_the_exponent", "power_valuation_value_eq_transport", "lte_power_difference_functional"),
        script,
        "The full LTE valuation holds for every actual supplied power/difference witness, by extensionality of the constructed power graphs.",
    ))
    return tuple(rows)


__all__ = [
    "power_difference_quotient_relation", "power_difference_second_order_relation",
    "lifted_power_difference_relation", "make_odd_prime_lte_candidate_theorems",
]
