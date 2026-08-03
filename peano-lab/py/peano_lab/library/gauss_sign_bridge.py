"""Constructive predecessor-sign bridge for Gauss-style arguments.

The module is an isolated theorem-spec factory.  ``Pow``, parity, and modular
congruence are expanded into ordinary first-order PA formulas in every public
contract; no parser or kernel symbol is introduced.  The main invariant is
proved as one conjunction induction, so the even and odd branches share the
same predecessor power certificate.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import power_relation


def _mod_eq(modulus: str, left: str, right: str, *, tag: str) -> str:
    return (
        f"exists gs_u_{tag} gs_v_{tag}. ({left}) + "
        f"{modulus} * gs_u_{tag} = ({right}) + {modulus} * gs_v_{tag}"
    )


def _even(value: str, *, tag: str) -> str:
    return f"exists gs_even_{tag}. {value} = 2 * gs_even_{tag}"


def _odd(value: str, *, tag: str) -> str:
    return f"exists gs_odd_{tag}. {value} = 2 * gs_odd_{tag} + 1"


def make_gauss_sign_bridge_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered predecessor/parity power bridge."""

    square_mod_one = _mod_eq("p", "r * r", "1", tag="square")

    power = power_relation("r", "e", "z", tag="main")
    even_e = _even("e", tag="main")
    odd_e = _odd("e", tag="main")
    even_result = _mod_eq("p", "z", "1", tag="result_even")
    odd_result = _mod_eq("p", "z", "r", tag="result_odd")
    main_statement = (
        f"forall p r e z. p = S r -> ({power}) -> "
        f"((({even_e}) -> ({even_result})) /\\ "
        f"(({odd_e}) -> ({odd_result})))"
    )

    predecessor_power = power_relation("r", "e", "w", tag="predecessor")
    successor_step = (
        f"exists w. ({predecessor_power}) /\\ z = w * r"
    )
    ih_even = _even("e", tag="ih")
    ih_odd = _odd("e", tag="ih")
    ih_even_result = _mod_eq("p", "x", "1", tag="ih_even")
    ih_odd_result = _mod_eq("p", "x", "r", tag="ih_odd")
    induction_invariant = (
        f"((({ih_even}) -> ({ih_even_result})) /\\ "
        f"(({ih_odd}) -> ({ih_odd_result})))"
    )

    return (
        spec(
            "predecessor_square_mod_one",
            f"forall p r. p = S r -> {square_mod_one}",
            (
                "mul_one",
                "mul_succ_left",
                "add_assoc",
                "add_comm",
                "zero_add",
                "add_succ_left",
            ),
            (
                "intro p",
                "intro r",
                "intro hp",
                "exists 1",
                "exists r",
                "rewrite hp",
                "rewrite hp",
                "simp [mul_one, mul_succ_left, add_assoc, add_comm, "
                "zero_add, add_succ_left]",
            ),
            "The predecessor of a successor squares to one modulo that successor.",
        ),
        spec(
            "even_successor_to_odd",
            "forall n. (exists a. S n = 2 * a) -> "
            "exists b. n = 2 * b + 1",
            ("parity_cases", "successor_odd_of_even", "even_not_odd"),
            (
                "intro n",
                "intro hse",
                "specialize parity_cases n",
                "cases parity_cases",
                "cases parity_cases_witness",
                "exfalso",
                "have hso : exists b. S n = 2 * b + 1",
                "specialize successor_odd_of_even n",
                "apply successor_odd_of_even",
                "exists x",
                "exact parity_cases_witness_left",
                "specialize even_not_odd (S n)",
                "apply even_not_odd",
                "exact hse",
                "exact hso",
                "exists x",
                "exact parity_cases_witness_right",
            ),
            "If a successor is even, its predecessor is odd.",
        ),
        spec(
            "odd_successor_to_even",
            "forall n. (exists a. S n = 2 * a + 1) -> "
            "exists b. n = 2 * b",
            ("parity_cases", "successor_even_of_odd", "odd_not_even"),
            (
                "intro n",
                "intro hso",
                "specialize parity_cases n",
                "cases parity_cases",
                "cases parity_cases_witness",
                "exists x",
                "exact parity_cases_witness_left",
                "exfalso",
                "have hse : exists b. S n = 2 * b",
                "specialize successor_even_of_odd n",
                "apply successor_even_of_odd",
                "exists x",
                "exact parity_cases_witness_right",
                "specialize odd_not_even (S n)",
                "apply odd_not_even",
                "exact hso",
                "exact hse",
            ),
            "If a successor is odd, its predecessor is even.",
        ),
        spec(
            "pow_predecessor_parity_mod",
            main_statement,
            (
                "pow_zero",
                "pow_successor_decompose",
                "odd_not_even",
                "even_successor_to_odd",
                "odd_successor_to_even",
                "predecessor_square_mod_one",
                "mod_eq_refl",
                "mod_eq_mul",
                "mod_eq_trans",
                "one_mul",
            ),
            (
                "intro p",
                "intro r",
                "induction e",
                "intro z",
                "intro hp",
                "intro hpow",
                "split",
                "intro he",
                "have hz : z = 1",
                "specialize pow_zero r",
                "specialize pow_zero 0",
                "specialize pow_zero z",
                "apply pow_zero",
                "refl",
                "exact hpow",
                "rewrite hz",
                "specialize mod_eq_refl p",
                "specialize mod_eq_refl 1",
                "exact mod_eq_refl",
                "intro ho",
                "exfalso",
                "specialize odd_not_even 0",
                "apply odd_not_even",
                "exact ho",
                "exists 0",
                "norm_num",
                "intro z",
                "intro hp",
                "intro hpow",
                f"have hstep : {successor_step}",
                "specialize pow_successor_decompose r",
                "specialize pow_successor_decompose e",
                "specialize pow_successor_decompose (S e)",
                "specialize pow_successor_decompose z",
                "apply pow_successor_decompose",
                "refl",
                "exact hpow",
                "cases hstep",
                "cases hstep_witness",
                f"have hinv : {induction_invariant}",
                "specialize IH x",
                "apply IH",
                "exact hp",
                "exact hstep_witness_left",
                "cases hinv",
                "split",
                "intro hse",
                "have heo : exists a. e = 2 * a + 1",
                "specialize even_successor_to_odd e",
                "apply even_successor_to_odd",
                "exact hse",
                "have hwr : exists u v. x + p * u = r + p * v",
                "apply hinv_right",
                "exact heo",
                "have hrr : exists u v. r + p * u = r + p * v",
                "specialize mod_eq_refl p",
                "specialize mod_eq_refl r",
                "exact mod_eq_refl",
                "have hmul : exists u v. (x * r) + p * u = "
                "(r * r) + p * v",
                "specialize mod_eq_mul p",
                "specialize mod_eq_mul x",
                "specialize mod_eq_mul r",
                "specialize mod_eq_mul r",
                "specialize mod_eq_mul r",
                "apply mod_eq_mul",
                "exact hwr",
                "exact hrr",
                "have hsq : exists u v. (r * r) + p * u = 1 + p * v",
                "specialize predecessor_square_mod_one p",
                "specialize predecessor_square_mod_one r",
                "apply predecessor_square_mod_one",
                "exact hp",
                "have hfinal : exists u v. (x * r) + p * u = 1 + p * v",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans (x * r)",
                "specialize mod_eq_trans (r * r)",
                "specialize mod_eq_trans 1",
                "apply mod_eq_trans",
                "exact hmul",
                "exact hsq",
                "rewrite hstep_witness_right",
                "exact hfinal",
                "intro hso",
                "have hee : exists a. e = 2 * a",
                "specialize odd_successor_to_even e",
                "apply odd_successor_to_even",
                "exact hso",
                "have hw1 : exists u v. x + p * u = 1 + p * v",
                "apply hinv_left",
                "exact hee",
                "have hrr : exists u v. r + p * u = r + p * v",
                "specialize mod_eq_refl p",
                "specialize mod_eq_refl r",
                "exact mod_eq_refl",
                "have hmul : exists u v. (x * r) + p * u = "
                "(1 * r) + p * v",
                "specialize mod_eq_mul p",
                "specialize mod_eq_mul x",
                "specialize mod_eq_mul 1",
                "specialize mod_eq_mul r",
                "specialize mod_eq_mul r",
                "apply mod_eq_mul",
                "exact hw1",
                "exact hrr",
                "specialize one_mul r",
                "rewrite one_mul at hmul",
                "rewrite hstep_witness_right",
                "exact hmul",
            ),
            "Powers of the predecessor of p alternate between one and the predecessor modulo p.",
        ),
    )


__all__ = ["make_gauss_sign_bridge_theorems"]
