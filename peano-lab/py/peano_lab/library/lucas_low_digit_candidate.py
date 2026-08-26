"""Constructive arbitrary-quotient Lucas congruence for one lower digit.

These isolated theorem candidates iterate the independently checked prime-row
Pascal shift.  Every formula expands into unchanged first-order Heyting
arithmetic, and no theorem is enrolled in Alpha or admitted to Stable.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_choose_foundation_candidate import _choose_relation_term
from .fermat_residue_map_candidate import prime


LUCAS_PRIME_BLOCK_ZERO_REASSOCIATION = "lucas_prime_block_zero_reassociation"
LUCAS_PRIME_BLOCK_SUCCESSOR_REASSOCIATION = (
    "lucas_prime_block_successor_reassociation"
)
LUCAS_REPEATED_PRIME_SHIFT_BELOW_BASE = "lucas_repeated_prime_shift_below_base"
LUCAS_LOW_DIGIT_CONGRUENCE = "lucas_low_digit_congruence"
LUCAS_LOW_DIGIT_PRODUCT_CONGRUENCE = "lucas_low_digit_product_congruence"


def _choose(upper: str, lower: str, value: str, *, tag: str) -> str:
    return _choose_relation_term(
        upper,
        lower,
        value,
        tag=f"lucas_low_digit_{tag}",
        variables=("p", "q", "a", "b", "d", "e", "C", "D", "A", "B"),
    )


def _lt(left: str, right: str, *, tag: str) -> str:
    return f"exists lld_gap_{tag}. lld_gap_{tag} + S ({left}) = ({right})"


def _mod(modulus: str, left: str, right: str, *, tag: str) -> str:
    return (
        f"exists lld_left_{tag} lld_right_{tag}. "
        f"({left}) + ({modulus}) * lld_left_{tag} = "
        f"({right}) + ({modulus}) * lld_right_{tag}"
    )


def make_lucas_low_digit_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the full arbitrary-quotient, single-lower-digit Lucas theorem."""

    prime_p = prime("p", tag="lucas_low_digit_prime")
    upper = _choose("p * q + a", "b", "C", tag="repeat_upper")
    lower = _choose("a", "b", "D", tag="repeat_lower")
    low_upper = _choose("p * q + d", "e", "C", tag="low_upper")
    low_lower = _choose("d", "e", "D", tag="low_lower")
    product_upper = _choose("p * q + d", "e", "C", tag="product_upper")
    product_quotient = _choose("q", "0", "A", tag="product_quotient")
    product_digit = _choose("d", "e", "B", tag="product_digit")

    return (
        spec(
            LUCAS_PRIME_BLOCK_ZERO_REASSOCIATION,
            "forall p a. p * 0 + a = a",
            ("zero_add",),
            (
                "intro p",
                "intro a",
                "trans 0 + a",
                "congr",
                "apply PA5",
                "refl",
                "apply zero_add",
            ),
            "The zero prime-block quotient leaves its additive tail unchanged.",
        ),
        spec(
            LUCAS_PRIME_BLOCK_SUCCESSOR_REASSOCIATION,
            "forall p q a. p * S q + a = p + (p * q + a)",
            ("add_comm", "add_assoc"),
            (
                "intro p",
                "intro q",
                "intro a",
                "trans (p * q + p) + a",
                "congr",
                "apply PA6",
                "refl",
                "trans (p + p * q) + a",
                "congr",
                "apply add_comm",
                "refl",
                "apply add_assoc",
            ),
            "A successor prime-block quotient is exactly one prime shift of its predecessor.",
        ),
        spec(
            LUCAS_REPEATED_PRIME_SHIFT_BELOW_BASE,
            f"forall p q a b C D. ({prime_p}) -> "
            f"({_lt('b', 'p', tag='repeat_bound')}) -> "
            f"({upper}) -> ({lower}) -> "
            f"({_mod('p', 'C', 'D', tag='repeat_result')})",
            (
                LUCAS_PRIME_BLOCK_ZERO_REASSOCIATION,
                LUCAS_PRIME_BLOCK_SUCCESSOR_REASSOCIATION,
                "choose_upper_eq_transport",
                "choose_functional",
                "mod_eq_refl",
                "choose_exists",
                "lucas_prime_shift_below_base",
                "mod_eq_trans",
            ),
            (
                "intro p",
                "induction q",
                "intro a",
                "intro b",
                "intro C",
                "intro D",
                "intro hprime",
                "intro hbound",
                "intro hupper",
                "intro hlower",
                f"have hnormalized : {_choose('a', 'b', 'C', tag='repeat_zero_normalized')}",
                "specialize choose_upper_eq_transport (p * 0 + a)",
                "specialize choose_upper_eq_transport a",
                "specialize choose_upper_eq_transport b",
                "specialize choose_upper_eq_transport C",
                "apply choose_upper_eq_transport",
                "apply lucas_prime_block_zero_reassociation",
                "exact hupper",
                "have hequal : C = D",
                "specialize choose_functional a",
                "specialize choose_functional b",
                "specialize choose_functional C",
                "specialize choose_functional D",
                "apply choose_functional",
                "exact hnormalized",
                "exact hlower",
                "rewrite hequal",
                "apply mod_eq_refl",
                "intro a",
                "intro b",
                "intro C",
                "intro D",
                "intro hprime",
                "intro hbound",
                "intro hupper",
                "intro hlower",
                f"have hnormalized : "
                f"{_choose('p + (p * q + a)', 'b', 'C', tag='repeat_successor_normalized')}",
                "specialize choose_upper_eq_transport (p * S q + a)",
                "specialize choose_upper_eq_transport (p + (p * q + a))",
                "specialize choose_upper_eq_transport b",
                "specialize choose_upper_eq_transport C",
                "apply choose_upper_eq_transport",
                "apply lucas_prime_block_successor_reassociation",
                "exact hupper",
                f"have hmiddle : exists D. "
                f"{_choose('p * q + a', 'b', 'D', tag='repeat_middle')}",
                "apply choose_exists",
                "cases hmiddle",
                f"have hshift : {_mod('p', 'C', 'x', tag='repeat_shift')}",
                "specialize lucas_prime_shift_below_base p",
                "specialize lucas_prime_shift_below_base (p * q + a)",
                "specialize lucas_prime_shift_below_base b",
                "specialize lucas_prime_shift_below_base C",
                "specialize lucas_prime_shift_below_base x",
                "apply lucas_prime_shift_below_base",
                "exact hprime",
                "exact hbound",
                "exact hnormalized",
                "exact hmiddle_witness",
                f"have hremaining : {_mod('p', 'x', 'D', tag='repeat_remaining')}",
                "specialize IH a",
                "specialize IH b",
                "specialize IH x",
                "specialize IH D",
                "apply IH",
                "exact hprime",
                "exact hbound",
                "exact hmiddle_witness",
                "exact hlower",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans C",
                "specialize mod_eq_trans x",
                "specialize mod_eq_trans D",
                "apply mod_eq_trans",
                "exact hshift",
                "exact hremaining",
            ),
            "Every below-base binomial column is invariant modulo a prime under an arbitrary number of prime-row shifts.",
        ),
        spec(
            LUCAS_LOW_DIGIT_CONGRUENCE,
            f"forall p q d e C D. ({prime_p}) -> "
            f"({_lt('d', 'p', tag='low_upper_bound')}) -> "
            f"({_lt('e', 'p', tag='low_lower_bound')}) -> "
            f"({low_upper}) -> ({low_lower}) -> "
            f"({_mod('p', 'C', 'D', tag='low_result')})",
            (LUCAS_REPEATED_PRIME_SHIFT_BELOW_BASE,),
            (
                "intro p",
                "intro q",
                "intro d",
                "intro e",
                "intro C",
                "intro D",
                "intro hprime",
                "intro hupper_bound",
                "intro hlower_bound",
                "intro hupper",
                "intro hlower",
                "specialize lucas_repeated_prime_shift_below_base p",
                "specialize lucas_repeated_prime_shift_below_base q",
                "specialize lucas_repeated_prime_shift_below_base d",
                "specialize lucas_repeated_prime_shift_below_base e",
                "specialize lucas_repeated_prime_shift_below_base C",
                "specialize lucas_repeated_prime_shift_below_base D",
                "apply lucas_repeated_prime_shift_below_base",
                "exact hprime",
                "exact hlower_bound",
                "exact hupper",
                "exact hlower",
            ),
            "The exact Lucas congruence holds for every natural upper quotient and every lower index consisting of one base-prime digit.",
        ),
        spec(
            LUCAS_LOW_DIGIT_PRODUCT_CONGRUENCE,
            f"forall p q d e C A B. ({prime_p}) -> "
            f"({_lt('d', 'p', tag='product_upper_bound')}) -> "
            f"({_lt('e', 'p', tag='product_lower_bound')}) -> "
            f"({product_upper}) -> ({product_quotient}) -> "
            f"({product_digit}) -> "
            f"({_mod('p', 'C', 'A * B', tag='product_result')})",
            ("choose_zero", "one_mul", LUCAS_LOW_DIGIT_CONGRUENCE),
            (
                "intro p",
                "intro q",
                "intro d",
                "intro e",
                "intro C",
                "intro A",
                "intro B",
                "intro hprime",
                "intro hupper_bound",
                "intro hlower_bound",
                "intro hupper",
                "intro hquotient",
                "intro hdigit",
                "have hone : A = 1",
                "specialize choose_zero q",
                "specialize choose_zero A",
                "apply choose_zero",
                "exact hquotient",
                "rewrite hone",
                "specialize one_mul B",
                "rewrite one_mul",
                "specialize lucas_low_digit_congruence p",
                "specialize lucas_low_digit_congruence q",
                "specialize lucas_low_digit_congruence d",
                "specialize lucas_low_digit_congruence e",
                "specialize lucas_low_digit_congruence C",
                "specialize lucas_low_digit_congruence B",
                "apply lucas_low_digit_congruence",
                "exact hprime",
                "exact hupper_bound",
                "exact hlower_bound",
                "exact hupper",
                "exact hdigit",
            ),
            "The full quotient-times-digit Lucas product formula is kernel-checked whenever the lower quotient is zero, for unrestricted upper quotient.",
        ),
    )


__all__ = [
    "LUCAS_LOW_DIGIT_CONGRUENCE",
    "LUCAS_LOW_DIGIT_PRODUCT_CONGRUENCE",
    "LUCAS_PRIME_BLOCK_SUCCESSOR_REASSOCIATION",
    "LUCAS_PRIME_BLOCK_ZERO_REASSOCIATION",
    "LUCAS_REPEATED_PRIME_SHIFT_BELOW_BASE",
    "make_lucas_low_digit_candidate_theorems",
]
