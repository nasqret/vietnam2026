"""Checked constructive bounded prime units for quadratic reciprocity.

The authoring helpers in this module expand immediately to the unchanged
first-order PA language.  They add no ``Prime``, order, inverse, remainder,
or congruence symbol to the parser or kernel.
"""

from __future__ import annotations

from typing import Any, Callable


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


def _binders(
    tag: str,
    variables: tuple[str, ...],
    stems: tuple[str, ...],
) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"qrbu_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated bounded-unit binder captures an argument")
    return names


def prime(value: str, *, tag: str) -> str:
    """Expand primality at one identifier."""

    variable = _identifier(value, "prime candidate")
    left, right = _binders(tag, (variable,), ("factor_left", "factor_right"))
    return (
        f"(~({value} = 1) /\\ forall {left} {right}. "
        f"{value} = {left} * {right} -> {left} = 1 \\/ {right} = 1)"
    )


def strictly_below(left: str, right: str, *, tag: str) -> str:
    """Expand the witness-defined strict order ``left < right``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in ((left, "lower term"), (right, "upper term"))
    )
    (gap,) = _binders(tag, variables, ("gap",))
    return f"exists {gap}. {gap} + S {left} = {right}"


def balanced_inverse(
    modulus: str,
    value: str,
    inverse: str,
    *,
    tag: str,
) -> str:
    """Expand ``value * inverse = 1 (mod modulus)`` constructively."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (modulus, "modulus"),
            (value, "value"),
            (inverse, "inverse"),
        )
    )
    positive, negative = _binders(tag, variables, ("mod_left", "mod_right"))
    return (
        f"exists {positive} {negative}. {value} * {inverse} + "
        f"{modulus} * {positive} = 1 + {modulus} * {negative}"
    )


def bounded_nonzero_inverse(
    modulus: str,
    value: str,
    *,
    tag: str,
) -> str:
    """Expand existence of a nonzero inverse strictly below the modulus."""

    variables = tuple(
        _identifier(item, label)
        for item, label in ((modulus, "modulus"), (value, "value"))
    )
    (inverse,) = _binders(tag, variables, ("inverse",))
    return (
        f"exists {inverse}. (~({inverse} = 0) /\\ "
        f"(({strictly_below(inverse, modulus, tag=f'{tag}_bound')}) /\\ "
        f"({balanced_inverse(modulus, value, inverse, tag=f'{tag}_mod')})))"
    )


def make_qr_bounded_unit_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the checked two-rung bounded prime-unit tranche."""

    prime_p = prime("p", tag="prime_p")
    a_lt_p = strictly_below("a", "p", tag="a_lt_p")
    bounded_inverse = bounded_nonzero_inverse("p", "a", tag="bounded_inverse")

    return (
        spec(
            "prime_is_succ_succ",
            f"forall p. ({prime_p}) -> exists k. p = S (S k)",
            ("prime_nonzero", "nonzero_is_succ"),
            (
                "intro p",
                "intro hp",
                "have hp0 : ~(p = 0)",
                "intro hpzero",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hp",
                "exact hpzero",
                "have hps : exists k. p = S k",
                "specialize nonzero_is_succ p",
                "apply nonzero_is_succ",
                "exact hp0",
                "cases hps",
                "have hx0 : ~(x = 0)",
                "intro hx0",
                "cases hp",
                "apply hp_left",
                "rewrite hps_witness",
                "rewrite hx0",
                "refl",
                "have hxs : exists k. x = S k",
                "specialize nonzero_is_succ x",
                "apply nonzero_is_succ",
                "exact hx0",
                "cases hxs",
                "exists x1",
                "rewrite hps_witness",
                "rewrite hxs_witness",
                "refl",
            ),
            "Every prime natural is the second successor of a natural.",
        ),
        spec(
            "prime_bounded_nonzero_mod_inverse",
            f"forall p a. ({prime_p}) -> ~(a = 0) -> ({a_lt_p}) -> "
            f"({bounded_inverse})",
            (
                "prime_is_succ_succ",
                "prime_nonzero",
                "divisor_le_nonzero",
                "lt_not_le",
                "prime_mod_inverse",
                "division_remainder_exists",
                "mul_comm",
                "remainder_decomposition_to_mod_eq",
                "mod_eq_mul_left",
                "mod_eq_symm",
                "mod_eq_trans",
                "mod_eq_bounded_unique",
                "succ_ne_zero",
            ),
            (
                "intro p",
                "intro a",
                "intro hp",
                "intro ha0",
                "intro hap",
                "have hp0 : ~(p = 0)",
                "intro hpzero",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hp",
                "exact hpzero",
                "have hnotdiv : ~(exists k. a = p * k)",
                "intro hdiv",
                "have hpa : exists t. t + p = a",
                "specialize divisor_le_nonzero p",
                "specialize divisor_le_nonzero a",
                "apply divisor_le_nonzero",
                "exact ha0",
                "exact hdiv",
                "specialize lt_not_le a",
                "specialize lt_not_le p",
                "apply lt_not_le",
                "exact hap",
                "exact hpa",
                "have hinv : exists z u v. a * z + p * u = 1 + p * v",
                "specialize prime_mod_inverse p",
                "specialize prime_mod_inverse a",
                "apply prime_mod_inverse",
                "exact hp",
                "exact hnotdiv",
                "cases hinv",
                "cases hinv_witness",
                "cases hinv_witness_witness",
                "have hdivz : exists q r. x = p * q + r /\\ "
                "exists h. h + S r = p",
                "specialize division_remainder_exists p",
                "specialize division_remainder_exists x",
                "apply division_remainder_exists",
                "exact hp0",
                "cases hdivz",
                "cases hdivz_witness",
                "cases hdivz_witness_witness",
                "have hzdecomp : x = x3 * p + x4",
                "trans p * x3 + x4",
                "exact hdivz_witness_witness_left",
                "congr",
                "apply mul_comm",
                "refl",
                "have hzr : exists u v. x + p * u = x4 + p * v",
                "specialize remainder_decomposition_to_mod_eq p",
                "specialize remainder_decomposition_to_mod_eq x",
                "specialize remainder_decomposition_to_mod_eq x3",
                "specialize remainder_decomposition_to_mod_eq x4",
                "apply remainder_decomposition_to_mod_eq",
                "exact hzdecomp",
                "have hscaled : exists u v. (a * x) + p * u = "
                "(a * x4) + p * v",
                "specialize mod_eq_mul_left p",
                "specialize mod_eq_mul_left x",
                "specialize mod_eq_mul_left x4",
                "specialize mod_eq_mul_left a",
                "apply mod_eq_mul_left",
                "exact hzr",
                "have hrz : exists u v. (a * x4) + p * u = "
                "(a * x) + p * v",
                "specialize mod_eq_symm p",
                "specialize mod_eq_symm (a * x)",
                "specialize mod_eq_symm (a * x4)",
                "apply mod_eq_symm",
                "exact hscaled",
                "have hfinal : exists u v. (a * x4) + p * u = 1 + p * v",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans (a * x4)",
                "specialize mod_eq_trans (a * x)",
                "specialize mod_eq_trans 1",
                "apply mod_eq_trans",
                "exact hrz",
                "exists x1",
                "exists x2",
                "exact hinv_witness_witness_witness",
                "have hp2 : exists k. p = S (S k)",
                "specialize prime_is_succ_succ p",
                "apply prime_is_succ_succ",
                "exact hp",
                "cases hp2",
                "have h0bound : exists h. h + S 0 = p",
                "exists S x5",
                "rewrite hp2_witness",
                "simp",
                "have h1bound : exists h. h + S 1 = p",
                "exists x5",
                "rewrite hp2_witness",
                "simp",
                "have hr0 : ~(x4 = 0)",
                "intro hrzero",
                "have hzeroone : exists u v. 0 + p * u = 1 + p * v",
                "cases hfinal",
                "cases hfinal_witness",
                "exists x6",
                "exists x7",
                "trans (a * x4) + p * x6",
                "congr",
                "symm",
                "trans a * 0",
                "congr",
                "refl",
                "exact hrzero",
                "apply PA5",
                "refl",
                "exact hfinal_witness_witness",
                "have hzeroeqone : 0 = 1",
                "specialize mod_eq_bounded_unique p",
                "specialize mod_eq_bounded_unique 0",
                "specialize mod_eq_bounded_unique 1",
                "apply mod_eq_bounded_unique",
                "exact h0bound",
                "exact h1bound",
                "exact hzeroone",
                "specialize succ_ne_zero 0",
                "apply succ_ne_zero",
                "symm",
                "exact hzeroeqone",
                "exists x4",
                "split",
                "exact hr0",
                "split",
                "exact hdivz_witness_witness_right",
                "exact hfinal",
            ),
            "A nonzero residue below a prime has a nonzero bounded inverse.",
        ),
    )


__all__ = [
    "balanced_inverse",
    "bounded_nonzero_inverse",
    "make_qr_bounded_unit_theorems",
    "prime",
    "strictly_below",
]
