"""Static native Fermat endpoints built over the eight-rung residue route.

The predecessor-exponent theorem cancels the exact product of ``1,...,p-1``.
The all-input theorem then performs the constructive prime coprime-or-divides
split.  Both statements use relational powers and balanced congruence, expand
to the unchanged first-order PA language, and remain outside the public
registry pending WMI discovery and receipt-pinned admission.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_map_candidate import not_divides, prime
from .fermat_residue_product_candidate import coprime
from .fermat_scale_product_candidate import product_left_mod
from .finite_fold_surface import power_relation


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


def _identifier_or_one(value: str, label: str) -> str:
    if value == "1":
        return value
    return _identifier(value, label)


def _binders(
    tag: str,
    variables: tuple[str, ...],
    stems: tuple[str, ...],
) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"fep_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated Fermat-endpoint binder captures an argument")
    return names


def balanced_mod(
    modulus: str,
    left: str,
    right: str,
    *,
    tag: str,
) -> str:
    """Expand balanced congruence ``left == right (mod modulus)``."""

    variables = (
        _identifier(modulus, "modulus"),
        _identifier_or_one(left, "left value"),
        _identifier_or_one(right, "right value"),
    )
    left_witness, right_witness = _binders(
        tag,
        variables,
        ("mod_left", "mod_right"),
    )
    return (
        f"exists {left_witness} {right_witness}. "
        f"{left} + {modulus} * {left_witness} = "
        f"{right} + {modulus} * {right_witness}"
    )


def divides(divisor: str, value: str, *, tag: str) -> str:
    """Expand divisibility with a hygienically owned factor."""

    variables = tuple(
        _identifier(item, label)
        for item, label in ((divisor, "divisor"), (value, "dividend"))
    )
    (factor,) = _binders(tag, variables, ("factor",))
    return f"exists {factor}. {value} = {divisor} * {factor}"


def product_pair_mod(
    modulus: str,
    left_first: str,
    left_second: str,
    right_first: str,
    right_second: str,
    *,
    tag: str,
) -> str:
    """Expand congruence between two explicitly factored products."""

    variables = (
        _identifier(modulus, "modulus"),
        _identifier_or_one(left_first, "left first factor"),
        _identifier_or_one(left_second, "left second factor"),
        _identifier_or_one(right_first, "right first factor"),
        _identifier_or_one(right_second, "right second factor"),
    )
    left_witness, right_witness = _binders(
        tag,
        variables,
        ("product_mod_left", "product_mod_right"),
    )
    return (
        f"exists {left_witness} {right_witness}. "
        f"({left_first} * {left_second}) + {modulus} * {left_witness} = "
        f"({right_first} * {right_second}) + {modulus} * {right_witness}"
    )


def make_fermat_endpoint_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the predecessor-exponent and all-input Fermat candidates."""

    predecessor_prime = prime("p", tag="predecessor_prime")
    predecessor_nonzero = not_divides("p", "a", tag="predecessor_multiplier")
    predecessor_power = power_relation("a", "n", "A", tag="predecessor_power")
    predecessor_result = balanced_mod("p", "A", "1", tag="predecessor_result")
    balance = product_left_mod("p", "A", "x", "x", tag="predecessor_balance")
    factor_coprime = coprime("x", "p", tag="predecessor_coprime")
    normalized_balance = product_pair_mod(
        "p", "x", "A", "x", "1", tag="predecessor_normalized"
    )

    all_prime = prime("p", tag="all_prime")
    all_power = power_relation("a", "p", "A", tag="all_power")
    all_result = balanced_mod("p", "A", "a", tag="all_result")
    predecessor_power_at_x = power_relation(
        "a", "x", "r", tag="all_predecessor_power"
    )
    predecessor_mod_at_x1 = balanced_mod(
        "p", "x1", "1", tag="all_predecessor_result"
    )
    scaled_predecessor = product_pair_mod(
        "p", "x1", "a", "1", "a", tag="all_scaled"
    )
    prime_coprime_a = coprime("p", "a", tag="all_coprime")
    prime_divides_a = divides("p", "a", tag="all_divides")

    return (
        spec(
            "fermat_predecessor_exponent_mod_one",
            f"forall p n a A. p = S n -> ({predecessor_prime}) -> "
            f"({predecessor_nonzero}) -> ({predecessor_power}) -> "
            f"({predecessor_result})",
            (
                "factorial_exists",
                "prime_mul_residue_product_balance",
                "prime_range_product_coprime",
                "prime_nonzero",
                "mod_eq_cancel_coprime",
                "mul_comm",
                "mul_one",
            ),
            (
                "intro p",
                "intro n",
                "intro a",
                "intro A",
                "intro hpn",
                "intro hp",
                "intro hnotdiv",
                "intro hA",
                "specialize factorial_exists n",
                "cases factorial_exists",
                "cases factorial_exists_witness",
                "cases factorial_exists_witness_witness",
                "cases factorial_exists_witness_witness_witness",
                f"have hbalance : {balance}",
                "specialize prime_mul_residue_product_balance p",
                "specialize prime_mul_residue_product_balance n",
                "specialize prime_mul_residue_product_balance a",
                "specialize prime_mul_residue_product_balance x1",
                "specialize prime_mul_residue_product_balance x2",
                "specialize prime_mul_residue_product_balance x",
                "specialize prime_mul_residue_product_balance A",
                "apply prime_mul_residue_product_balance",
                "exact hpn",
                "exact hp",
                "exact hnotdiv",
                "exact factorial_exists_witness_witness_witness_left",
                "exact factorial_exists_witness_witness_witness_right",
                "exact hA",
                f"have hcop : {factor_coprime}",
                "specialize prime_range_product_coprime p",
                "specialize prime_range_product_coprime n",
                "specialize prime_range_product_coprime x1",
                "specialize prime_range_product_coprime x2",
                "specialize prime_range_product_coprime x",
                "apply prime_range_product_coprime",
                "exact hpn",
                "exact hp",
                "exact factorial_exists_witness_witness_witness_left",
                "exact factorial_exists_witness_witness_witness_right",
                "have hp0 : ~(p = 0)",
                "intro hpzero",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hp",
                "exact hpzero",
                f"have hscaled : {normalized_balance}",
                "cases hbalance",
                "cases hbalance_witness",
                "exists x3",
                "exists x4",
                "trans (A * x) + p * x3",
                "congr",
                "apply mul_comm",
                "refl",
                "trans x + p * x4",
                "exact hbalance_witness_witness",
                "congr",
                "symm",
                "apply mul_one",
                "refl",
                "specialize mod_eq_cancel_coprime p",
                "specialize mod_eq_cancel_coprime x",
                "specialize mod_eq_cancel_coprime A",
                "specialize mod_eq_cancel_coprime 1",
                "apply mod_eq_cancel_coprime",
                "exact hp0",
                "exact hcop",
                "exact hscaled",
            ),
            "Fermat's theorem for the native predecessor exponent p-1.",
        ),
        spec(
            "fermat_little_all_inputs",
            f"forall p a A. ({all_prime}) -> ({all_power}) -> ({all_result})",
            (
                "prime_nonzero",
                "nonzero_is_succ",
                "pow_successor_decompose",
                "prime_coprime_or_divides",
                "multiple_refl",
                "fermat_predecessor_exponent_mod_one",
                "mod_eq_mul_right",
                "one_mul",
                "multiple_mul_left",
                "add_comm",
            ),
            (
                "intro p",
                "intro a",
                "intro A",
                "intro hp",
                "intro hpow",
                "have hp0 : ~(p = 0)",
                "intro hpzero",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hp",
                "exact hpzero",
                "have hps : exists n. p = S n",
                "specialize nonzero_is_succ p",
                "apply nonzero_is_succ",
                "exact hp0",
                "cases hps",
                f"have hdecomp : exists r. ({predecessor_power_at_x}) /\\ A = r * a",
                "specialize pow_successor_decompose a",
                "specialize pow_successor_decompose x",
                "specialize pow_successor_decompose p",
                "specialize pow_successor_decompose A",
                "apply pow_successor_decompose",
                "exact hps_witness",
                "exact hpow",
                "cases hdecomp",
                "cases hdecomp_witness",
                f"have hsplit : ({prime_coprime_a}) \\/ ({prime_divides_a})",
                "specialize prime_coprime_or_divides p",
                "specialize prime_coprime_or_divides a",
                "apply prime_coprime_or_divides",
                "exact hp",
                "cases hsplit",
                "have hnotdiv : ~(exists k. a = p * k)",
                "intro hdiv",
                "have hpdiv : exists q. p = p * q",
                "specialize multiple_refl p",
                "exact multiple_refl",
                "have hpone : p = 1",
                "specialize hsplit_left p",
                "apply hsplit_left",
                "exact hpdiv",
                "exact hdiv",
                "cases hp",
                "apply hp_left",
                "exact hpone",
                f"have hprev : {predecessor_mod_at_x1}",
                "specialize fermat_predecessor_exponent_mod_one p",
                "specialize fermat_predecessor_exponent_mod_one x",
                "specialize fermat_predecessor_exponent_mod_one a",
                "specialize fermat_predecessor_exponent_mod_one x1",
                "apply fermat_predecessor_exponent_mod_one",
                "exact hps_witness",
                "exact hp",
                "exact hnotdiv",
                "exact hdecomp_witness_left",
                f"have hscaled : {scaled_predecessor}",
                "specialize mod_eq_mul_right p",
                "specialize mod_eq_mul_right x1",
                "specialize mod_eq_mul_right 1",
                "specialize mod_eq_mul_right a",
                "apply mod_eq_mul_right",
                "exact hprev",
                "rewrite hdecomp_witness_right",
                "specialize one_mul a",
                "rewrite one_mul at hscaled",
                "exact hscaled",
                "cases hsplit_right",
                "have hAdiv : exists s. A = p * s",
                "rewrite hdecomp_witness_right",
                "specialize multiple_mul_left p",
                "specialize multiple_mul_left a",
                "specialize multiple_mul_left x1",
                "apply multiple_mul_left",
                "exists x2",
                "exact hsplit_right_witness",
                "cases hAdiv",
                "exists x2",
                "exists x3",
                "rewrite hAdiv_witness",
                "rewrite hsplit_right_witness",
                "specialize add_comm (p * x3)",
                "specialize add_comm (p * x2)",
                "exact add_comm",
            ),
            "Fermat's little theorem for every natural base in relational-power form.",
        ),
    )


__all__ = [
    "balanced_mod",
    "divides",
    "make_fermat_endpoint_candidate_theorems",
    "product_pair_mod",
]
