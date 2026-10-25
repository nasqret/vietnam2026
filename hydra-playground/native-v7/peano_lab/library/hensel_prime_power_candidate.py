"""Constructive canonical and iterated simple-root Hensel lifting over HA.

The authoring relations below are hygienic expansions in the unchanged
first-order signature.  Every theorem has an ordinary tactic body; no
polynomial, inverse, correction, power, or choice oracle is admitted here.
Natural-coefficient Horner theorems are explicitly distinguished from any
later signed-coefficient bridge.  This additive module changes no release.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from .finite_fold_surface import _identifier
from .ha_generalized_crt_congruence_candidate import balanced_mod_eq
from .ha_modular_inverse_candidate import coprime
from .polynomial_hensel_candidate import _paired_terms
from .polynomial_horner_candidate import _horner_relation_terms
from .polynomial_taylor_hensel_candidate import _correction_terms
from .power_algebra_theorems import _power_terms


class HenselPrimePowerError(ValueError):
    """A purported conservative Hensel relation is malformed or capturing."""


def _safe(tag: str) -> str:
    try:
        return _identifier(tag, "Hensel prime-power binder tag")
    except ValueError as error:
        raise HenselPrimePowerError(str(error)) from error


def _arguments(*values: str) -> tuple[str, ...]:
    try:
        result = tuple(_identifier(value, "Hensel relation argument") for value in values)
        if len(set(result)) != len(result):
            raise ValueError("Hensel relation arguments must be distinct")
        if any(value.startswith(("hpl_", "ff_", "fs_", "ph_", "hd_", "pa_", "pth_", "hgcrt_", "hmi_")) for value in result):
            raise ValueError("generated Hensel binder captures an argument")
        return result
    except ValueError as error:
        raise HenselPrimePowerError(str(error)) from error


def _variables(*terms: str) -> tuple[str, ...]:
    """The finite parsing context of trusted module-owned term fragments."""

    return tuple(dict.fromkeys(
        word for term in terms for word in re.findall(r"[A-Za-z_][A-Za-z0-9_']*", term)
        if word != "S"
    )) or ("hpl_unused_context",)


def _mod(m: str, a: str, b: str, *, tag: str = "mod") -> str:
    return balanced_mod_eq(m, a, b, tag=f"hpl_{_safe(tag)}", variables=_variables(m, a, b))


def _lt(a: str, b: str, *, tag: str = "bound") -> str:
    return f"exists hpl_gap_{_safe(tag)}. hpl_gap_{_safe(tag)} + S ({a}) = ({b})"


def _pair(b: str, c: str, a: str, l: str, n: str, d: str, *, tag: str = "pair") -> str:
    return _paired_terms(b, c, a, l, n, d, tag=f"hpl_{_safe(tag)}")


def _eval(b: str, c: str, a: str, l: str, n: str, *, tag: str = "eval") -> str:
    return _horner_relation_terms(b, c, a, l, n, tag=f"hpl_{_safe(tag)}")


def _cop(d: str, p: str, *, tag: str = "coprime") -> str:
    return coprime(d, p, tag=f"hpl_{_safe(tag)}")


def _correction(d: str, p: str, q: str, t: str, *, tag: str = "correction") -> str:
    return _correction_terms(d, p, q, t, tag=f"hpl_{_safe(tag)}", context=_variables(d, p, q, t))


def _power(p: str, k: str, m: str, *, tag: str = "power") -> str:
    return _power_terms(p, k, m, tag=f"hpl_{_safe(tag)}")


def _root(b: str, c: str, a: str, l: str, m: str, *, tag: str = "root") -> str:
    n = f"hpl_value_{_safe(tag)}"
    return f"exists {n}. (({_eval(b, c, a, l, n, tag=tag)}) /\\ ({_mod(m, n, '0', tag=tag)}))"


def horner_root_modulo_relation(
    code: str, scale: str, point: str, length: str, modulus: str, *, tag: str,
) -> str:
    """An actual natural-polynomial value is zero modulo its natural modulus."""

    return _root(*_arguments(code, scale, point, length, modulus), tag=_safe(tag))


def _simple(
    b: str, c: str, a: str, l: str, m: str, p: str, *, tag: str = "simple",
) -> str:
    n, d = f"hpl_value_{_safe(tag)}", f"hpl_derivative_{_safe(tag)}"
    return (
        f"exists {n} {d}. (({_pair(b, c, a, l, n, d, tag=tag)}) /\\ "
        f"(({_mod(m, n, '0', tag=tag)}) /\\ ({_cop(d, p, tag=tag)})))"
    )


def simple_horner_root_relation(
    code: str, scale: str, point: str, length: str,
    root_modulus: str, derivative_modulus: str, *, tag: str,
) -> str:
    """A genuine polynomial root with derivative coprime to the lifting base."""

    return _simple(*_arguments(
        code, scale, point, length, root_modulus, derivative_modulus,
    ), tag=_safe(tag))


def _lift(
    b: str, c: str, l: str, m: str, a: str, M: str, r: str, *, tag: str = "lift",
) -> str:
    return (
        f"(({_lt(r, M, tag=tag)}) /\\ "
        f"(({_mod(m, r, a, tag=tag)}) /\\ ({_root(b, c, r, l, M, tag=tag)})))"
    )


def canonical_horner_lift_relation(
    code: str, scale: str, length: str, old_modulus: str,
    source_point: str, new_modulus: str, lift_point: str, *, tag: str,
) -> str:
    """A bounded root at the new modulus in the old residue class."""

    return _lift(*_arguments(
        code, scale, length, old_modulus, source_point, new_modulus, lift_point,
    ), tag=_safe(tag))


def _call(name: str, *arguments: str) -> tuple[str, ...]:
    return (*(f"specialize {name} {argument}" for argument in arguments), f"apply {name}")


def make_hensel_prime_power_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """Return dependency-ordered original-kernel proof candidates, never admission."""

    return (
        spec(
            "hensel_mod_add_zero_cancel",
            f"forall m a q. ({_mod('m', 'a + q', '0')}) -> "
            f"({_mod('m', 'q', '0')}) -> ({_mod('m', 'a', '0')})",
            ("mod_eq_add_cancel_right", "mod_eq_trans", "mod_eq_symm", "zero_add"),
            (
                "intro m", "intro a", "intro q", "intro hsum", "intro hq",
                *_call("mod_eq_add_cancel_right", "m", "a", "0", "q"),
                *_call("mod_eq_trans", "m", "(a + q)", "0", "(0 + q)"),
                "exact hsum", "have heq : 0 + q = q", "apply zero_add", "rewrite heq",
                *_call("mod_eq_symm", "m", "q", "0"), "exact hq",
            ),
            "A known zero-congruent summand can be cancelled without subtraction.",
        ),
        spec(
            "hensel_coprime_mod_transport",
            f"forall p d e. ~(p = 0) -> ({_cop('d', 'p')}) -> "
            f"({_mod('p', 'd', 'e')}) -> ({_cop('e', 'p')})",
            ("coprime_bounded_mod_inverse", "mod_eq_mul_right", "mod_eq_trans", "mod_eq_symm", "mod_inverse_implies_coprime"),
            (
                "intro p", "intro d", "intro e", "intro hp", "intro hcop", "intro hmod",
                f"have hinv : exists u. (({_lt('u', 'p')}) /\\ ({_mod('p', 'd * u', '1')}))",
                *_call("coprime_bounded_mod_inverse", "d", "p"), "exact hp", "exact hcop",
                "cases hinv", "cases hinv_witness",
                *_call("mod_inverse_implies_coprime", "e", "p", "x"),
                *_call("mod_eq_trans", "p", "(e * x)", "(d * x)", "1"),
                *_call("mod_eq_mul_right", "p", "e", "d", "x"),
                *_call("mod_eq_symm", "p", "d", "e"), "exact hmod", "exact hinv_witness_right",
            ),
            "A derivative remains coprime to a nonzero modulus after any genuine congruence transport.",
        ),
        spec(
            "hensel_canonical_residue_exists",
            f"forall m a. ~(m = 0) -> exists r. (({_lt('r', 'm')}) /\\ ({_mod('m', 'a', 'r')}))",
            ("division_remainder_exists", "add_comm"),
            (
                "intro m", "intro a", "intro hm",
                "have hdiv : exists q r. a = m * q + r /\\ S r <= m",
                *_call("division_remainder_exists", "m", "a"), "exact hm",
                "cases hdiv", "cases hdiv_witness", "cases hdiv_witness_witness",
                "exists x1", "split", "exact hdiv_witness_witness_right",
                "exists 0", "exists x", "trans a", "simp",
                "trans m * x + x1", "exact hdiv_witness_witness_left", "apply add_comm",
            ),
            "Every unrestricted natural input has a constructed canonical residue at every nonzero modulus.",
        ),
        spec(
            "hensel_lift_digit_bound",
            f"forall m p a t. ({_lt('a', 'm')}) -> ({_lt('t', 'p')}) -> ({_lt('a + m * t', 'p * m')})",
            ("division_block_upper", "mul_le_mul_left", "lt_of_lt_of_le", "add_comm", "mul_comm"),
            (
                "intro m", "intro p", "intro a", "intro t", "intro ha", "intro ht",
                "have hsum : a + m * t = m * t + a", "apply add_comm", "rewrite hsum",
                "have hproduct : p * m = m * p", "apply mul_comm", "rewrite hproduct",
                *_call("lt_of_lt_of_le", "(m * t + a)", "(m * S t)", "(m * p)"),
                *_call("division_block_upper", "m", "t", "a"), "exact ha",
                *_call("mul_le_mul_left", "(S t)", "p", "m"), "exact ht",
            ),
            "A bounded old representative and bounded correction digit give the exact next-modulus bound.",
        ),
        spec(
            "hensel_canonical_lift_digit_decompose",
            f"forall m p a z. ~(m = 0) -> ({_lt('a', 'm')}) -> ({_lt('z', 'p * m')}) -> "
            f"({_mod('m', 'z', 'a')}) -> exists t. (({_lt('t', 'p')}) /\\ z = a + m * t)",
            ("division_remainder_exists", "canonical_remainder_from_mod", "le_or_lt", "lt_not_le", "le_trans", "mul_le_mul_left", "le_add_right", "mul_comm", "add_comm"),
            (
                "intro m", "intro p", "intro a", "intro z", "intro hm", "intro ha", "intro hz", "intro hmod",
                "have hdiv : exists q r. z = m * q + r /\\ S r <= m",
                *_call("division_remainder_exists", "m", "z"), "exact hm",
                "cases hdiv", "cases hdiv_witness", "cases hdiv_witness_witness",
                "have hr : x1 = a", *_call("canonical_remainder_from_mod", "m", "z", "x", "x1", "a"),
                "exact hdiv_witness_witness_left", "exact hdiv_witness_witness_right", "exact ha", "exact hmod",
                f"have hbound : {_lt('x', 'p')}",
                "specialize le_or_lt p", "specialize le_or_lt x", "cases le_or_lt",
                "exfalso", *_call("lt_not_le", "z", "(p * m)"), "exact hz",
                "have hprod : p * m = m * p", "apply mul_comm", "rewrite hprod",
                *_call("le_trans", "(m * p)", "(m * x)", "z"),
                *_call("mul_le_mul_left", "p", "x", "m"), "exact le_or_lt_left",
                "rewrite hdiv_witness_witness_left", *_call("le_add_right", "(m * x)", "x1"),
                "exact le_or_lt_right", "exists x", "split", "exact hbound",
                "trans m * x + x1", "exact hdiv_witness_witness_left", "rewrite hr", "apply add_comm",
            ),
            "Every canonical next-modulus element in an old residue class has an actual bounded correction digit.",
        ),
        spec(
            "hensel_lift_linear_identity",
            "forall m d q t. m * (q + d * t) = m * q + (m * t) * d",
            ("mul_add", "mul_assoc", "mul_comm"),
            (
                "intro m", "intro d", "intro q", "intro t",
                "trans m * q + m * (d * t)", "apply mul_add", "congr", "refl",
                "trans m * (t * d)", "congr", "refl", "apply mul_comm", "symm", "apply mul_assoc",
            ),
            "The lifted first-order Taylor term factors exactly by the old modulus.",
        ),
        spec(
            "hensel_lift_correction_of_root",
            f"forall b c a l n d m p s q t y. ~(m = 0) -> ({_pair('b', 'c', 'a', 'l', 'n', 'd')}) -> "
            f"({_eval('b', 'c', '(a + m * t)', 'l', 'y')}) -> m = p * s -> n = m * q -> "
            f"({_lt('t', 'p')}) -> ({_mod('p * m', 'y', '0')}) -> ({_correction('d', 'p', 'q', 't')})",
            ("beta_horner_taylor_remainder_exists", "hensel_square_shift_multiple", "multiple_mul_right", "multiple_implies_balanced_zero_congruence", "hensel_mod_add_zero_cancel", "hensel_lift_linear_identity", "mod_eq_unscale_nonzero", "mul_comm"),
            (
                "intro b", "intro c", "intro a", "intro l", "intro n", "intro d", "intro m", "intro p",
                "intro s", "intro q", "intro t", "intro y", "intro hm", "intro hpair", "intro hvalue",
                "intro hfactor", "intro hn", "intro ht", "intro hroot",
                "have htaylor : exists w. y = (n + (m * t) * d) + ((m * t) * (m * t)) * w",
                *_call("beta_horner_taylor_remainder_exists", "b", "c", "a", "(m * t)", "l", "n", "d", "y"),
                "exact hpair", "exact hvalue", "cases htaylor",
                "have hsquare : exists w. (m * t) * (m * t) = (p * m) * w",
                *_call("hensel_square_shift_multiple", "m", "t", "p", "s"), "exact hfactor",
                f"have hquad : {_mod('p * m', '((m * t) * (m * t)) * x', '0')}",
                *_call("multiple_implies_balanced_zero_congruence", "(p * m)", "(((m * t) * (m * t)) * x)"),
                *_call("multiple_mul_right", "(p * m)", "((m * t) * (m * t))", "x"), "exact hsquare",
                f"have hlinear : {_mod('p * m', 'n + (m * t) * d', '0')}",
                *_call("hensel_mod_add_zero_cancel", "(p * m)", "(n + (m * t) * d)", "(((m * t) * (m * t)) * x)"),
                "rewrite <- htaylor_witness", "exact hroot", "exact hquad",
                "split", "exact ht", *_call("mod_eq_unscale_nonzero", "m", "p", "(q + d * t)", "0"), "exact hm",
                "have hproduct : m * p = p * m", "apply mul_comm", "rewrite hproduct", "rewrite hproduct",
                "have hzero : m * 0 = 0", "simp", "rewrite hzero",
                "have hidentity : m * (q + d * t) = n + (m * t) * d",
                "rewrite hn", *_call("hensel_lift_linear_identity", "m", "d", "q", "t"),
                "rewrite hidentity", "exact hlinear",
            ),
            "Every genuine next-modulus root with a bounded digit necessarily satisfies the derivative correction equation.",
        ),
        spec(
            "hensel_canonical_horner_lift_exists_unique",
            f"forall b c a l n d m p s q. ~(p = 0) -> ~(m = 0) -> "
            f"({_pair('b', 'c', 'a', 'l', 'n', 'd')}) -> m = p * s -> n = m * q -> "
            f"({_cop('d', 'p')}) -> ({_lt('a', 'm')}) -> exists r. "
            f"(({_lift('b', 'c', 'l', 'm', 'a', 'p * m', 'r')}) /\\ "
            f"forall z. ({_lift('b', 'c', 'l', 'm', 'a', 'p * m', 'z')}) -> z = r)",
            ("beta_horner_hensel_lift_exists", "hensel_lift_digit_bound", "multiple_implies_balanced_zero_congruence", "hensel_canonical_lift_digit_decompose", "hensel_lift_correction_of_root", "hensel_correction_unique"),
            (
                "intro b", "intro c", "intro a", "intro l", "intro n", "intro d", "intro m", "intro p", "intro s", "intro q",
                "intro hp", "intro hm", "intro hpair", "intro hfactor", "intro hn", "intro hcop", "intro ha",
                f"have hstep : exists t y. (({_correction('d', 'p', 'q', 't')}) /\\ "
                f"(({_eval('b', 'c', '(a + m * t)', 'l', 'y')}) /\\ exists w. y = (p * m) * w))",
                *_call("beta_horner_hensel_lift_exists", "b", "c", "a", "l", "n", "d", "m", "p", "s", "q"),
                "exact hp", "exact hpair", "exact hfactor", "exact hn", "exact hcop",
                "cases hstep", "cases hstep_witness", "cases hstep_witness_witness", "cases hstep_witness_witness_right",
                f"have ht : {_lt('x', 'p')}", "cases hstep_witness_witness_left", "exact hstep_witness_witness_left_left",
                "exists a + m * x", "split", "split",
                *_call("hensel_lift_digit_bound", "m", "p", "a", "x"), "exact ha", "exact ht", "split",
                "exists 0", "exists x", "simp",
                "exists x1", "split", "exact hstep_witness_witness_right_left",
                *_call("multiple_implies_balanced_zero_congruence", "(p * m)", "x1"), "exact hstep_witness_witness_right_right",
                "intro z", "intro hz", "cases hz", "cases hz_right",
                f"have hdigit : exists t. (({_lt('t', 'p')}) /\\ z = a + m * t)",
                *_call("hensel_canonical_lift_digit_decompose", "m", "p", "a", "z"),
                "exact hm", "exact ha", "exact hz_left", "exact hz_right_left",
                "cases hdigit", "cases hdigit_witness", "cases hz_right_right", "cases hz_right_right_witness",
                f"have hcorrection : {_correction('d', 'p', 'q', 'x2')}",
                *_call("hensel_lift_correction_of_root", "b", "c", "a", "l", "n", "d", "m", "p", "s", "q", "x2", "x3"),
                "exact hm", "exact hpair", "rewrite <- hdigit_witness_right", "exact hz_right_right_witness_left",
                "exact hfactor", "exact hn", "exact hdigit_witness_left", "exact hz_right_right_witness_right",
                "have heq : x2 = x", *_call("hensel_correction_unique", "d", "p", "q", "x2", "x"),
                "exact hp", "exact hcop", "exact hcorrection", "exact hstep_witness_witness_left",
                "trans a + m * x2", "exact hdigit_witness_right", "rewrite heq", "refl",
            ),
            "A canonical old simple root has exactly one bounded next-modulus lift among all roots in its old residue class.",
        ),
        spec(
            "beta_horner_simple_canonical_representative",
            f"forall b c a l n d m p s. ~(p = 0) -> ~(m = 0) -> "
            f"({_pair('b', 'c', 'a', 'l', 'n', 'd')}) -> m = p * s -> "
            f"({_mod('m', 'n', '0')}) -> ({_cop('d', 'p')}) -> exists r. "
            f"(({_lt('r', 'm')}) /\\ (({_mod('m', 'r', 'a')}) /\\ ({_simple('b', 'c', 'r', 'l', 'm', 'p')})))",
            ("hensel_canonical_residue_exists", "beta_horner_derivative_value_exists", "beta_horner_derivative_mod_congruence", "mod_eq_trans", "mod_eq_symm", "mod_eq_of_mod_eq_multiple", "hensel_coprime_mod_transport"),
            (
                "intro b", "intro c", "intro a", "intro l", "intro n", "intro d", "intro m", "intro p", "intro s",
                "intro hp", "intro hm", "intro hpair", "intro hfactor", "intro hroot", "intro hcop",
                f"have hresidue : exists r. (({_lt('r', 'm')}) /\\ ({_mod('m', 'a', 'r')}))",
                *_call("hensel_canonical_residue_exists", "m", "a"), "exact hm", "cases hresidue", "cases hresidue_witness",
                f"have hnewpair : exists v e. ({_pair('b', 'c', 'x', 'l', 'v', 'e')})",
                *_call("beta_horner_derivative_value_exists", "b", "c", "x", "l"), "cases hnewpair", "cases hnewpair_witness",
                f"have hboth : ({_mod('m', 'n', 'x1')}) /\\ ({_mod('m', 'd', 'x2')})",
                *_call("beta_horner_derivative_mod_congruence", "b", "c", "m", "a", "x", "l", "n", "d", "x1", "x2"),
                "exact hresidue_witness_right", "exact hpair", "exact hnewpair_witness_witness", "cases hboth",
                "exists x", "split", "exact hresidue_witness_left", "split",
                *_call("mod_eq_symm", "m", "a", "x"), "exact hresidue_witness_right",
                "exists x1", "exists x2", "split", "exact hnewpair_witness_witness", "split",
                *_call("mod_eq_trans", "m", "x1", "n", "0"),
                *_call("mod_eq_symm", "m", "n", "x1"), "exact hboth_left", "exact hroot",
                *_call("hensel_coprime_mod_transport", "p", "d", "x2"), "exact hp", "exact hcop",
                *_call("mod_eq_of_mod_eq_multiple", "p", "m", "d", "x2"), "exists s", "exact hfactor", "exact hboth_right",
            ),
            "An unrestricted natural input can be normalized without losing its exact polynomial root or simple derivative.",
        ),
        spec(
            "beta_horner_simple_root_hensel_lift_exists_unique",
            f"forall b c a l n d m p s. ~(p = 0) -> ~(m = 0) -> "
            f"({_pair('b', 'c', 'a', 'l', 'n', 'd')}) -> m = p * s -> "
            f"({_mod('m', 'n', '0')}) -> ({_cop('d', 'p')}) -> exists r. "
            f"(({_lift('b', 'c', 'l', 'm', 'a', 'p * m', 'r')}) /\\ "
            f"forall z. ({_lift('b', 'c', 'l', 'm', 'a', 'p * m', 'z')}) -> z = r)",
            ("beta_horner_simple_canonical_representative", "mod_eq_zero_to_dvd_nonzero", "hensel_canonical_horner_lift_exists_unique", "mod_eq_trans", "mod_eq_symm"),
            (
                "intro b", "intro c", "intro a", "intro l", "intro n", "intro d", "intro m", "intro p", "intro s",
                "intro hp", "intro hm", "intro hpair", "intro hfactor", "intro hroot", "intro hcop",
                f"have hnormalized : exists r. (({_lt('r', 'm')}) /\\ (({_mod('m', 'r', 'a')}) /\\ ({_simple('b', 'c', 'r', 'l', 'm', 'p')})))",
                *_call("beta_horner_simple_canonical_representative", "b", "c", "a", "l", "n", "d", "m", "p", "s"),
                "exact hp", "exact hm", "exact hpair", "exact hfactor", "exact hroot", "exact hcop",
                "cases hnormalized", "cases hnormalized_witness", "cases hnormalized_witness_right",
                "cases hnormalized_witness_right_right", "cases hnormalized_witness_right_right_witness",
                "cases hnormalized_witness_right_right_witness_witness", "cases hnormalized_witness_right_right_witness_witness_right",
                "have hquotient : exists q. x1 = m * q", *_call("mod_eq_zero_to_dvd_nonzero", "m", "x1"),
                "exact hm", "exact hnormalized_witness_right_right_witness_witness_right_left", "cases hquotient",
                f"have hcanonical : exists r. (({_lift('b', 'c', 'l', 'm', 'x', 'p * m', 'r')}) /\\ forall z. ({_lift('b', 'c', 'l', 'm', 'x', 'p * m', 'z')}) -> z = r)",
                *_call("hensel_canonical_horner_lift_exists_unique", "b", "c", "x", "l", "x1", "x2", "m", "p", "s", "x3"),
                "exact hp", "exact hm", "exact hnormalized_witness_right_right_witness_witness_left", "exact hfactor", "exact hquotient_witness",
                "exact hnormalized_witness_right_right_witness_witness_right_right", "exact hnormalized_witness_left",
                "cases hcanonical", "cases hcanonical_witness", "cases hcanonical_witness_left", "cases hcanonical_witness_left_right",
                "exists x4", "split", "split", "exact hcanonical_witness_left_left", "split",
                *_call("mod_eq_trans", "m", "x4", "x", "a"), "exact hcanonical_witness_left_right_left", "exact hnormalized_witness_right_left",
                "exact hcanonical_witness_left_right_right",
                "intro z", "intro hz", "cases hz", "cases hz_right", "specialize hcanonical_witness_right z", "apply hcanonical_witness_right",
                "split", "exact hz_left", "split", *_call("mod_eq_trans", "m", "z", "a", "x"), "exact hz_right_left",
                *_call("mod_eq_symm", "m", "x", "a"), "exact hnormalized_witness_right_left", "exact hz_right_right",
            ),
            "Every unrestricted natural-polynomial simple root has a unique canonical lift, with no supplied correction or representative bound.",
        ),
    ) + _make_root_transport_theorems(spec) + _make_prime_power_theorems(spec)


def _make_root_transport_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "beta_horner_root_mod_transport",
            f"forall b c a r l m. ({_mod('m', 'a', 'r')}) -> "
            f"({_root('b', 'c', 'a', 'l', 'm')}) -> ({_root('b', 'c', 'r', 'l', 'm')})",
            ("beta_horner_eval_exists", "beta_horner_eval_mod_congruence", "mod_eq_trans", "mod_eq_symm"),
            (
                "intro b", "intro c", "intro a", "intro r", "intro l", "intro m", "intro hmod", "intro hroot",
                "cases hroot", "cases hroot_witness",
                f"have hvalue : exists v. ({_eval('b', 'c', 'r', 'l', 'v')})",
                *_call("beta_horner_eval_exists", "b", "c", "r", "l"), "cases hvalue", "exists x1", "split", "exact hvalue_witness",
                *_call("mod_eq_trans", "m", "x1", "x", "0"),
                *_call("mod_eq_symm", "m", "x", "x1"),
                *_call("beta_horner_eval_mod_congruence", "b", "c", "m", "a", "r", "l", "x", "x1"),
                "exact hmod", "exact hroot_witness_left", "exact hvalue_witness", "exact hroot_witness_right",
            ),
            "An actual polynomial root transports to every congruent natural point.",
        ),
        spec(
            "beta_horner_root_mod_weaken",
            f"forall b c a l m M. (exists q. M = m * q) -> "
            f"({_root('b', 'c', 'a', 'l', 'M')}) -> ({_root('b', 'c', 'a', 'l', 'm')})",
            ("mod_eq_of_mod_eq_multiple",),
            (
                "intro b", "intro c", "intro a", "intro l", "intro m", "intro M", "intro hdiv", "intro hroot",
                "cases hroot", "cases hroot_witness", "exists x", "split", "exact hroot_witness_left",
                *_call("mod_eq_of_mod_eq_multiple", "m", "M", "x", "0"), "exact hdiv", "exact hroot_witness_right",
            ),
            "A witnessed root modulo a multiple is also a root modulo the old divisor.",
        ),
        spec(
            "beta_horner_simple_root_at_congruent_point",
            f"forall b c a r l n d p M. ~(p = 0) -> "
            f"({_pair('b', 'c', 'a', 'l', 'n', 'd')}) -> ({_cop('d', 'p')}) -> "
            f"({_mod('p', 'a', 'r')}) -> ({_root('b', 'c', 'r', 'l', 'M')}) -> "
            f"({_simple('b', 'c', 'r', 'l', 'M', 'p')})",
            ("beta_horner_derivative_value_exists", "beta_horner_derivative_mod_congruence", "beta_horner_derivative_value_projection", "beta_horner_eval_functional", "hensel_coprime_mod_transport"),
            (
                "intro b", "intro c", "intro a", "intro r", "intro l", "intro n", "intro d", "intro p", "intro M",
                "intro hp", "intro hpair", "intro hcop", "intro hmod", "intro hroot",
                f"have hnewpair : exists v e. ({_pair('b', 'c', 'r', 'l', 'v', 'e')})",
                *_call("beta_horner_derivative_value_exists", "b", "c", "r", "l"), "cases hnewpair", "cases hnewpair_witness",
                f"have hboth : ({_mod('p', 'n', 'x')}) /\\ ({_mod('p', 'd', 'x1')})",
                *_call("beta_horner_derivative_mod_congruence", "b", "c", "p", "a", "r", "l", "n", "d", "x", "x1"),
                "exact hmod", "exact hpair", "exact hnewpair_witness_witness", "cases hboth",
                f"have hvalue : {_eval('b', 'c', 'r', 'l', 'x')}",
                *_call("beta_horner_derivative_value_projection", "b", "c", "r", "l", "x", "x1"), "exact hnewpair_witness_witness",
                "cases hroot", "cases hroot_witness", "have heq : x = x2",
                *_call("beta_horner_eval_functional", "b", "c", "r", "l", "x", "x2"), "exact hvalue", "exact hroot_witness_left",
                "exists x", "exists x1", "split", "exact hnewpair_witness_witness", "split",
                "rewrite heq", "exact hroot_witness_right",
                *_call("hensel_coprime_mod_transport", "p", "d", "x1"), "exact hp", "exact hcop", "exact hboth_right",
            ),
            "Every lifted root in a simple residue class has an actual evaluated derivative that remains coprime to the base.",
        ),
        spec(
            "hensel_canonical_horner_root_exists_unique",
            f"forall b c a l m. ~(m = 0) -> ({_root('b', 'c', 'a', 'l', 'm')}) -> "
            f"exists r. (({_lift('b', 'c', 'l', 'm', 'a', 'm', 'r')}) /\\ "
            f"forall z. ({_lift('b', 'c', 'l', 'm', 'a', 'm', 'z')}) -> z = r)",
            ("hensel_canonical_residue_exists", "beta_horner_root_mod_transport", "mod_eq_symm", "mod_eq_trans", "mod_eq_bounded_unique"),
            (
                "intro b", "intro c", "intro a", "intro l", "intro m", "intro hm", "intro hroot",
                f"have hresidue : exists r. (({_lt('r', 'm')}) /\\ ({_mod('m', 'a', 'r')}))",
                *_call("hensel_canonical_residue_exists", "m", "a"), "exact hm", "cases hresidue", "cases hresidue_witness",
                "exists x", "split", "split", "exact hresidue_witness_left", "split",
                *_call("mod_eq_symm", "m", "a", "x"), "exact hresidue_witness_right",
                *_call("beta_horner_root_mod_transport", "b", "c", "a", "x", "l", "m"), "exact hresidue_witness_right", "exact hroot",
                "intro z", "intro hz", "cases hz", "cases hz_right",
                *_call("mod_eq_bounded_unique", "m", "z", "x"), "exact hz_left", "exact hresidue_witness_left",
                *_call("mod_eq_trans", "m", "z", "a", "x"), "exact hz_right_left", "exact hresidue_witness_right",
            ),
            "At iteration zero every unrestricted root has exactly one representative in its own canonical residue interval.",
        ),
        spec(
            "hensel_positive_power_factor",
            f"forall p k m. ~(p = 0) -> ~(k = 0) -> ({_power('p', 'k', 'm')}) -> "
            "~(m = 0) /\\ exists s. m = p * s",
            ("pow_nonzero_of_one_le", "one_le_of_ne_zero", "nonzero_is_succ", "pow_successor_decompose", "mul_comm"),
            (
                "intro p", "intro k", "intro m", "intro hp", "intro hk", "intro hpower", "split", "intro hzero",
                *_call("pow_nonzero_of_one_le", "p", "k", "m"), *_call("one_le_of_ne_zero", "p"), "exact hp", "exact hpower", "exact hzero",
                "have hkpositive : exists e. k = S e", *_call("nonzero_is_succ", "k"), "exact hk", "cases hkpositive",
                f"have hprevious : exists r. ({_power('p', 'x', 'r')}) /\\ m = r * p",
                *_call("pow_successor_decompose", "p", "x", "k", "m"), "exact hkpositive_witness", "exact hpower",
                "cases hprevious", "cases hprevious_witness", "exists x1", "trans x1 * p", "exact hprevious_witness_right", "apply mul_comm",
            ),
            "Every actual positive power of a nonzero base supplies both nonzeroness and an explicit base factor.",
        ),
    )


def _make_prime_power_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "beta_horner_prime_power_hensel_lift_exists_unique",
            f"forall b c a l n d p k m. ~(p = 0) -> ~(k = 0) -> "
            f"({_power('p', 'k', 'm')}) -> ({_pair('b', 'c', 'a', 'l', 'n', 'd')}) -> "
            f"({_mod('m', 'n', '0')}) -> ({_cop('d', 'p')}) -> exists M. "
            f"(({_power('p', 'S k', 'M')}) /\\ exists r. "
            f"(({_lift('b', 'c', 'l', 'm', 'a', 'M', 'r')}) /\\ "
            f"forall z. ({_lift('b', 'c', 'l', 'm', 'a', 'M', 'z')}) -> z = r))",
            ("hensel_positive_power_factor", "pow_successor_compose", "mul_comm", "beta_horner_simple_root_hensel_lift_exists_unique"),
            (
                "intro b", "intro c", "intro a", "intro l", "intro n", "intro d", "intro p", "intro k", "intro m",
                "intro hp", "intro hk", "intro hpower", "intro hpair", "intro hroot", "intro hcop",
                "have hfactor : ~(m = 0) /\\ exists s. m = p * s",
                *_call("hensel_positive_power_factor", "p", "k", "m"), "exact hp", "exact hk", "exact hpower",
                "cases hfactor", "cases hfactor_right", "exists p * m", "split",
                *_call("pow_successor_compose", "p", "k", "m", "(p * m)"), "exact hpower", "apply mul_comm",
                *_call("beta_horner_simple_root_hensel_lift_exists_unique", "b", "c", "a", "l", "n", "d", "m", "p", "x"),
                "exact hp", "exact hfactor_left", "exact hpair", "exact hfactor_right_witness", "exact hroot", "exact hcop",
            ),
            "A positive prime-power-level simple root at an unrestricted input has a unique canonical lift and an actual next-power witness; the theorem even permits every nonzero base.",
        ),
        spec(
            "beta_horner_simple_lift_preserves_simplicity",
            f"forall b c a l n d m p s M r. ~(p = 0) -> "
            f"({_pair('b', 'c', 'a', 'l', 'n', 'd')}) -> ({_cop('d', 'p')}) -> m = p * s -> "
            f"({_lift('b', 'c', 'l', 'm', 'a', 'M', 'r')}) -> ({_simple('b', 'c', 'r', 'l', 'M', 'p')})",
            ("beta_horner_simple_root_at_congruent_point", "mod_eq_of_mod_eq_multiple", "mod_eq_symm"),
            (
                "intro b", "intro c", "intro a", "intro l", "intro n", "intro d", "intro m", "intro p", "intro s", "intro M", "intro r",
                "intro hp", "intro hpair", "intro hcop", "intro hfactor", "intro hlift", "cases hlift", "cases hlift_right",
                *_call("beta_horner_simple_root_at_congruent_point", "b", "c", "a", "r", "l", "n", "d", "p", "M"),
                "exact hp", "exact hpair", "exact hcop",
                *_call("mod_eq_of_mod_eq_multiple", "p", "m", "a", "r"), "exists s", "exact hfactor",
                *_call("mod_eq_symm", "m", "r", "a"), "exact hlift_right_left", "exact hlift_right_right",
            ),
            "Every genuine canonical lift preserves simplicity, with an actual new polynomial/derivative trace rather than a supplied derivative oracle.",
        ),
        spec(
            "beta_horner_hensel_iterated_exists_unique",
            f"forall b c a l n d m p s. ~(p = 0) -> ~(m = 0) -> "
            f"({_pair('b', 'c', 'a', 'l', 'n', 'd')}) -> m = p * s -> "
            f"({_mod('m', 'n', '0')}) -> ({_cop('d', 'p')}) -> forall j q. "
            f"({_power('p', 'j', 'q')}) -> exists r. "
            f"(({_lift('b', 'c', 'l', 'm', 'a', 'm * q', 'r')}) /\\ "
            f"forall z. ({_lift('b', 'c', 'l', 'm', 'a', 'm * q', 'z')}) -> z = r)",
            (
                "pow_zero", "pow_successor_decompose", "pow_nonzero_of_one_le", "one_le_of_ne_zero",
                "mul_ne_zero", "mul_one", "mul_assoc", "mul_comm", "hensel_canonical_horner_root_exists_unique",
                "beta_horner_derivative_value_projection", "beta_horner_simple_lift_preserves_simplicity",
                "beta_horner_simple_root_hensel_lift_exists_unique", "mod_eq_trans", "mod_eq_symm",
                "mod_eq_of_mod_eq_multiple", "hensel_canonical_residue_exists", "beta_horner_root_mod_weaken", "beta_horner_root_mod_transport",
            ),
            (
                "intro b", "intro c", "intro a", "intro l", "intro n", "intro d", "intro m", "intro p", "intro s",
                "intro hp", "intro hm", "intro hpair", "intro hfactor", "intro hroot", "intro hcop", "induction j",
                "intro q", "intro hpower", "have hq : q = 1", *_call("pow_zero", "p", "0", "q"), "refl", "exact hpower",
                "have hM : m * q = m", "rewrite hq", "apply mul_one",
                *("rewrite hM",) * 6,
                *_call("hensel_canonical_horner_root_exists_unique", "b", "c", "a", "l", "m"), "exact hm",
                "exists n", "split", *_call("beta_horner_derivative_value_projection", "b", "c", "a", "l", "n", "d"), "exact hpair", "exact hroot",
                "intro q", "intro hpower",
                f"have hprevious_power : exists u. ({_power('p', 'j', 'u')}) /\\ q = u * p",
                *_call("pow_successor_decompose", "p", "j", "(S j)", "q"), "refl", "exact hpower",
                "cases hprevious_power", "cases hprevious_power_witness",
                "have hx : ~(x = 0)", "intro hzero", *_call("pow_nonzero_of_one_le", "p", "j", "x"),
                *_call("one_le_of_ne_zero", "p"), "exact hp", "exact hprevious_power_witness_left", "exact hzero",
                "have hnonzero : ~(m * x = 0)", "intro hzero", *_call("mul_ne_zero", "m", "x"), "exact hm", "exact hx", "exact hzero",
                "have hcurrent_factor : m * x = p * (s * x)", "rewrite hfactor", "apply mul_assoc",
                "have hM : m * q = p * (m * x)", "rewrite hprevious_power_witness_right",
                "trans (m * x) * p", "symm", "apply mul_assoc", "apply mul_comm",
                *("rewrite hM",) * 6,
                f"have hprevious : exists r. (({_lift('b', 'c', 'l', 'm', 'a', 'm * x', 'r')}) /\\ forall z. ({_lift('b', 'c', 'l', 'm', 'a', 'm * x', 'z')}) -> z = r)",
                "specialize IH x", "apply IH", "exact hprevious_power_witness_left", "cases hprevious", "cases hprevious_witness",
                f"have hsimple : {_simple('b', 'c', 'x1', 'l', 'm * x', 'p')}",
                *_call("beta_horner_simple_lift_preserves_simplicity", "b", "c", "a", "l", "n", "d", "m", "p", "s", "(m * x)", "x1"),
                "exact hp", "exact hpair", "exact hcop", "exact hfactor", "exact hprevious_witness_left",
                "cases hsimple", "cases hsimple_witness", "cases hsimple_witness_witness", "cases hsimple_witness_witness_right",
                f"have hnext : exists r. (({_lift('b', 'c', 'l', 'm * x', 'x1', 'p * (m * x)', 'r')}) /\\ forall z. ({_lift('b', 'c', 'l', 'm * x', 'x1', 'p * (m * x)', 'z')}) -> z = r)",
                *_call("beta_horner_simple_root_hensel_lift_exists_unique", "b", "c", "x1", "l", "x2", "x3", "(m * x)", "p", "(s * x)"),
                "exact hp", "exact hnonzero", "exact hsimple_witness_witness_left", "exact hcurrent_factor",
                "exact hsimple_witness_witness_right_left", "exact hsimple_witness_witness_right_right",
                "cases hnext", "cases hnext_witness", "cases hnext_witness_left", "cases hnext_witness_left_right",
                "cases hprevious_witness_left", "cases hprevious_witness_left_right",
                "exists x4", "split", "split", "exact hnext_witness_left_left", "split",
                *_call("mod_eq_trans", "m", "x4", "x1", "a"),
                *_call("mod_eq_of_mod_eq_multiple", "m", "(m * x)", "x4", "x1"), "exists x", "refl", "exact hnext_witness_left_right_left",
                "exact hprevious_witness_left_right_left", "exact hnext_witness_left_right_right",
                "intro z", "intro hz", "cases hz", "cases hz_right",
                f"have hresidue : exists r. (({_lt('r', 'm * x')}) /\\ ({_mod('m * x', 'z', 'r')}))",
                *_call("hensel_canonical_residue_exists", "(m * x)", "z"), "exact hnonzero", "cases hresidue", "cases hresidue_witness",
                f"have hroot_previous : {_root('b', 'c', 'z', 'l', 'm * x')}",
                *_call("beta_horner_root_mod_weaken", "b", "c", "z", "l", "(m * x)", "(p * (m * x))"),
                "exists p", "apply mul_comm", "exact hz_right_right",
                f"have hroot_representative : {_root('b', 'c', 'x5', 'l', 'm * x')}",
                *_call("beta_horner_root_mod_transport", "b", "c", "z", "x5", "l", "(m * x)"), "exact hresidue_witness_right", "exact hroot_previous",
                "have hsame_previous : x5 = x1", "specialize hprevious_witness_right x5", "apply hprevious_witness_right",
                "split", "exact hresidue_witness_left", "split", *_call("mod_eq_trans", "m", "x5", "z", "a"),
                *_call("mod_eq_of_mod_eq_multiple", "m", "(m * x)", "x5", "z"), "exists x", "refl",
                *_call("mod_eq_symm", "(m * x)", "z", "x5"), "exact hresidue_witness_right",
                "exact hz_right_left", "exact hroot_representative",
                "specialize hnext_witness_right z", "apply hnext_witness_right", "split", "exact hz_left", "split",
                "rewrite <- hsame_previous", "exact hresidue_witness_right", "exact hz_right_right",
            ),
            "HA induction constructs unique canonical simple-root lifts through every finite number of prime-power steps, including iteration zero, and proves uniqueness among all roots in the original residue class.",
        ),
        spec(
            "beta_horner_prime_power_iterated_lifts_exists_unique",
            f"forall b c a l n d p k j m. ~(p = 0) -> ~(k = 0) -> "
            f"({_power('p', 'k', 'm')}) -> ({_pair('b', 'c', 'a', 'l', 'n', 'd')}) -> "
            f"({_mod('m', 'n', '0')}) -> ({_cop('d', 'p')}) -> exists M. "
            f"(({_power('p', 'k + j', 'M')}) /\\ exists r. "
            f"(({_lift('b', 'c', 'l', 'm', 'a', 'M', 'r')}) /\\ "
            f"forall z. ({_lift('b', 'c', 'l', 'm', 'a', 'M', 'z')}) -> z = r))",
            ("hensel_positive_power_factor", "pow_exists", "pow_add", "beta_horner_hensel_iterated_exists_unique"),
            (
                "intro b", "intro c", "intro a", "intro l", "intro n", "intro d", "intro p", "intro k", "intro j", "intro m",
                "intro hp", "intro hk", "intro hpower", "intro hpair", "intro hroot", "intro hcop",
                "have hfactor : ~(m = 0) /\\ exists s. m = p * s",
                *_call("hensel_positive_power_factor", "p", "k", "m"), "exact hp", "exact hk", "exact hpower",
                "cases hfactor", "cases hfactor_right",
                f"have hmultiplier : exists q. ({_power('p', 'j', 'q')})", *_call("pow_exists", "p", "j"), "cases hmultiplier",
                f"have htarget : exists M. ({_power('p', 'k + j', 'M')})", *_call("pow_exists", "p", "(k + j)"), "cases htarget",
                "have hM : x2 = m * x1", *_call("pow_add", "p", "k", "j", "(k + j)", "m", "x1", "x2"),
                "refl", "exact hpower", "exact hmultiplier_witness", "exact htarget_witness",
                f"have hiteration : forall e q. ({_power('p', 'e', 'q')}) -> exists r. (({_lift('b', 'c', 'l', 'm', 'a', 'm * q', 'r')}) /\\ forall z. ({_lift('b', 'c', 'l', 'm', 'a', 'm * q', 'z')}) -> z = r)",
                *_call("beta_horner_hensel_iterated_exists_unique", "b", "c", "a", "l", "n", "d", "m", "p", "x"),
                "exact hp", "exact hfactor_left", "exact hpair", "exact hfactor_right_witness", "exact hroot", "exact hcop",
                "exists x2", "split", "exact htarget_witness", *("rewrite hM",) * 6,
                "specialize hiteration j", "specialize hiteration x1", "apply hiteration", "exact hmultiplier_witness",
            ),
            "From every positive initial prime-power exponent, arbitrary finite further lifting constructs the actual higher power and its unique canonical root while preserving the entire initial residue class.",
        ),
    )


__all__ = [
    "HenselPrimePowerError",
    "canonical_horner_lift_relation",
    "horner_root_modulo_relation",
    "simple_horner_root_relation",
    "make_hensel_prime_power_candidate_theorems",
]
