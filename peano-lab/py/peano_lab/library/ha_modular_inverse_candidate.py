"""Canonical bounded modular-inverse existence over the checked HA library.

This isolated M1 candidate combines the public, unbounded inverse theorem with
the candidate canonical-remainder interface.  All readable relations expand
immediately to the unchanged first-order language ``{0,S,+,*,=}``; neither
coprimality, strict order, congruence, nor remainder is a kernel primitive.

The theorem remains dependency-curried, unregistered, and unadmitted.  In
particular, it reaches quotient/remainder only through
``canonical_remainder_exists`` rather than invoking division directly.
"""

from __future__ import annotations

from typing import Any, Callable

from .ha_canonical_remainder_candidate import canonical_remainder


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
    names = tuple(f"hmi_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated modular-inverse binder captures an argument")
    return names


def strictly_below(left: str, right: str, *, tag: str) -> str:
    """Expand witness-defined strict order ``left < right``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in ((left, "lower term"), (right, "upper term"))
    )
    (gap,) = _binders(tag, variables, ("gap",))
    return f"exists {gap}. {gap} + S {left} = {right}"


def coprime(left: str, right: str, *, tag: str) -> str:
    """Expand the common-divisor definition of ``Coprime(left,right)``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in ((left, "left operand"), (right, "right operand"))
    )
    divisor, left_factor, right_factor = _binders(
        tag,
        variables,
        ("divisor", "left_factor", "right_factor"),
    )
    return (
        f"forall {divisor}. (exists {left_factor}. "
        f"{left} = {divisor} * {left_factor}) -> "
        f"(exists {right_factor}. {right} = {divisor} * {right_factor}) -> "
        f"{divisor} = 1"
    )


def modular_inverse(
    value: str,
    modulus: str,
    inverse: str,
    *,
    tag: str,
) -> str:
    """Expand balanced congruence ``value * inverse = 1 (mod modulus)``."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (value, "value"),
            (modulus, "modulus"),
            (inverse, "inverse"),
        )
    )
    left_offset, right_offset = _binders(
        tag,
        variables,
        ("left_offset", "right_offset"),
    )
    return (
        f"exists {left_offset} {right_offset}. "
        f"{value} * {inverse} + {modulus} * {left_offset} = "
        f"1 + {modulus} * {right_offset}"
    )


def bounded_modular_inverse(
    value: str,
    modulus: str,
    inverse: str,
    *,
    tag: str,
) -> str:
    """Expand a modular inverse constrained to the canonical interval."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (value, "value"),
            (modulus, "modulus"),
            (inverse, "inverse"),
        )
    )
    value, modulus, inverse = variables
    safe_tag = _identifier(tag, "binder tag")
    bound = strictly_below(inverse, modulus, tag=f"{safe_tag}_bound")
    inverse_relation = modular_inverse(
        value,
        modulus,
        inverse,
        tag=f"{safe_tag}_inverse",
    )
    return f"(({bound}) /\\ ({inverse_relation}))"


def unique_bounded_modular_inverse(
    value: str,
    modulus: str,
    *,
    tag: str,
) -> str:
    """Expand unique existence of a canonical modular inverse."""

    variables = tuple(
        _identifier(item, label)
        for item, label in ((value, "value"), (modulus, "modulus"))
    )
    value, modulus = variables
    safe_tag = _identifier(tag, "binder tag")
    solution, comparison = _binders(
        safe_tag,
        variables,
        ("solution", "comparison"),
    )
    chosen = bounded_modular_inverse(
        value,
        modulus,
        solution,
        tag=f"{safe_tag}_chosen",
    )
    compared = bounded_modular_inverse(
        value,
        modulus,
        comparison,
        tag=f"{safe_tag}_compared",
    )
    return (
        f"exists {solution}. (({chosen}) /\\ forall {comparison}. "
        f"({compared}) -> {comparison} = {solution})"
    )


def make_ha_modular_inverse_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the first canonical modular-inverse existence candidate."""

    coprime_a_m = coprime("a", "m", tag="assumption")
    r_below_m = strictly_below("r", "m", tag="result_bound")
    inverse_ar = modular_inverse("a", "m", "r", tag="result_inverse")
    inverse_az = modular_inverse("a", "m", "z", tag="converse_assumption")
    converse_coprime_a_m = coprime("a", "m", tag="converse_result")
    unique_inverse = unique_bounded_modular_inverse(
        "a", "m", tag="package_result"
    )
    package_coprime_a_m = coprime("a", "m", tag="package_coprime")
    package_exists = bounded_modular_inverse(
        "a", "m", "u", tag="package_exists"
    )

    remainder_z_r = canonical_remainder("m", "x", "r", tag="inverse_witness")
    z_congruent_x3 = "exists u v. x + m * u = x3 + m * v"
    az_congruent_ax3 = (
        "exists u v. (a * x) + m * u = (a * x3) + m * v"
    )
    ax3_congruent_az = (
        "exists u v. (a * x3) + m * u = (a * x) + m * v"
    )
    ax3_congruent_one = (
        "exists u v. (a * x3) + m * u = 1 + m * v"
    )

    return (
        spec(
            "coprime_bounded_mod_inverse",
            f"forall a m. ~(m = 0) -> ({coprime_a_m}) -> "
            f"exists r. ({r_below_m}) /\\ ({inverse_ar})",
            (
                "canonical_remainder_exists",
                "coprime_mod_inverse",
                "mul_comm",
                "remainder_decomposition_to_mod_eq",
                "mod_eq_mul_left",
                "mod_eq_symm",
                "mod_eq_trans",
            ),
            (
                "intro a",
                "intro m",
                "intro hm",
                "intro hcop",
                "have hinv : exists z u v. a * z + m * u = 1 + m * v",
                "specialize coprime_mod_inverse a",
                "specialize coprime_mod_inverse m",
                "apply coprime_mod_inverse",
                "exact hm",
                "exact hcop",
                "cases hinv",
                "cases hinv_witness",
                "cases hinv_witness_witness",
                f"have hrem : exists r. ({remainder_z_r})",
                "specialize canonical_remainder_exists m",
                "specialize canonical_remainder_exists x",
                "apply canonical_remainder_exists",
                "exact hm",
                "cases hrem",
                "cases hrem_witness",
                "cases hrem_witness_left",
                "have hzdecomp : x = x4 * m + x3",
                "trans m * x4 + x3",
                "exact hrem_witness_left_witness",
                "congr",
                "apply mul_comm",
                "refl",
                f"have hzr : {z_congruent_x3}",
                "specialize remainder_decomposition_to_mod_eq m",
                "specialize remainder_decomposition_to_mod_eq x",
                "specialize remainder_decomposition_to_mod_eq x4",
                "specialize remainder_decomposition_to_mod_eq x3",
                "apply remainder_decomposition_to_mod_eq",
                "exact hzdecomp",
                f"have hscaled : {az_congruent_ax3}",
                "specialize mod_eq_mul_left m",
                "specialize mod_eq_mul_left x",
                "specialize mod_eq_mul_left x3",
                "specialize mod_eq_mul_left a",
                "apply mod_eq_mul_left",
                "exact hzr",
                f"have hreverse : {ax3_congruent_az}",
                "specialize mod_eq_symm m",
                "specialize mod_eq_symm (a * x)",
                "specialize mod_eq_symm (a * x3)",
                "apply mod_eq_symm",
                "exact hscaled",
                f"have hfinal : {ax3_congruent_one}",
                "specialize mod_eq_trans m",
                "specialize mod_eq_trans (a * x3)",
                "specialize mod_eq_trans (a * x)",
                "specialize mod_eq_trans 1",
                "apply mod_eq_trans",
                "exact hreverse",
                "exists x1",
                "exists x2",
                "exact hinv_witness_witness_witness",
                "exists x3",
                "split",
                "exact hrem_witness_right",
                "exact hfinal",
            ),
            "Every coprime residue has an inverse in the canonical interval below "
            "a nonzero modulus.",
        ),
        spec(
            "mod_inverse_implies_coprime",
            f"forall a m z. ({inverse_az}) -> ({converse_coprime_a_m})",
            (
                "common_divisor_divides_balanced_result",
                "zero_add",
                "divisor_one",
            ),
            (
                "intro a",
                "intro m",
                "intro z",
                "intro hinv",
                "intro d",
                "intro hda",
                "intro hdm",
                "cases hinv",
                "cases hinv_witness",
                "have hbez : a * z + m * x = 1 + (a * 0 + m * x1)",
                "trans 1 + m * x1",
                "exact hinv_witness_witness",
                "congr",
                "refl",
                "symm",
                "trans 0 + m * x1",
                "congr",
                "apply PA5",
                "refl",
                "apply zero_add",
                "have hdivone : exists w. 1 = d * w",
                "specialize common_divisor_divides_balanced_result d",
                "specialize common_divisor_divides_balanced_result a",
                "specialize common_divisor_divides_balanced_result m",
                "specialize common_divisor_divides_balanced_result 1",
                "specialize common_divisor_divides_balanced_result z",
                "specialize common_divisor_divides_balanced_result x",
                "specialize common_divisor_divides_balanced_result 0",
                "specialize common_divisor_divides_balanced_result x1",
                "apply common_divisor_divides_balanced_result",
                "exact hda",
                "exact hdm",
                "exact hbez",
                "specialize divisor_one d",
                "apply divisor_one",
                "exact hdivone",
            ),
            "Any natural modular inverse forces coprimality, without a nonzero-"
            "modulus side condition.",
        ),
        spec(
            "coprime_iff_unique_bounded_mod_inverse",
            f"forall a m. ~(m = 0) -> (({package_coprime_a_m}) -> "
            f"({unique_inverse})) /\\ (({unique_inverse}) -> "
            f"({package_coprime_a_m}))",
            (
                "coprime_bounded_mod_inverse",
                "bounded_mod_inverse_unique",
                "mod_inverse_implies_coprime",
            ),
            (
                "intro a",
                "intro m",
                "intro hm",
                "split",
                "intro hcop",
                f"have hexists : exists u. ({package_exists})",
                "specialize coprime_bounded_mod_inverse a",
                "specialize coprime_bounded_mod_inverse m",
                "apply coprime_bounded_mod_inverse",
                "exact hm",
                "exact hcop",
                "cases hexists",
                "exists x",
                "split",
                "exact hexists_witness",
                "intro v",
                "intro hv",
                "cases hv",
                "cases hexists_witness",
                "specialize bounded_mod_inverse_unique m",
                "specialize bounded_mod_inverse_unique a",
                "specialize bounded_mod_inverse_unique v",
                "specialize bounded_mod_inverse_unique x",
                "apply bounded_mod_inverse_unique",
                "exact hv_left",
                "exact hexists_witness_left",
                "exact hv_right",
                "exact hexists_witness_right",
                "intro hunique",
                "cases hunique",
                "cases hunique_witness",
                "cases hunique_witness_left",
                "specialize mod_inverse_implies_coprime a",
                "specialize mod_inverse_implies_coprime m",
                "specialize mod_inverse_implies_coprime x",
                "apply mod_inverse_implies_coprime",
                "exact hunique_witness_left_right",
            ),
            "For a nonzero modulus, coprimality is equivalent to unique existence "
            "of a modular inverse in the canonical interval.",
        ),
    )


__all__ = [
    "bounded_modular_inverse",
    "coprime",
    "make_ha_modular_inverse_candidate_theorems",
    "modular_inverse",
    "strictly_below",
    "unique_bounded_modular_inverse",
]
