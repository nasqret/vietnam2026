"""Constructive quadratic-residue half of Euler's criterion.

The first theorem is a reusable congruence/divisibility bridge: for a nonzero
modulus, balanced congruence to zero yields an explicit multiple witness.  The
second theorem combines a square witness, relational power algebra, and the
native Fermat predecessor endpoint to show that a quadratic residue has half
power congruent to one modulo an odd prime.

Every displayed surface expands before parsing to the unchanged first-order
Peano language.  The candidates remain unregistered and dependency-curried;
they are not closed WMI receipts or admissions.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_map_candidate import not_divides, prime
from .finite_fold_surface import power_relation
from .power_algebra_theorems import _power_terms
from .quadratic_residue_surface import quadratic_residue
from .wilson_pair_product_candidate import _mod_eq_term


def make_euler_criterion_residue_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the zero-congruence bridge and residue branch of Euler."""

    zero_mod = _mod_eq_term(
        "p", "a", "0", tag="euler_zero_mod", avoid=("p", "a")
    )
    root_square_zero = _mod_eq_term(
        "p", "x * x", "0", tag="euler_root_square_zero", avoid=("p", "a", "h", "A", "x")
    )
    value_square = _mod_eq_term(
        "p", "a", "x * x", tag="euler_value_square", avoid=("p", "a", "h", "A", "x")
    )
    value_zero = _mod_eq_term(
        "p", "a", "0", tag="euler_value_zero", avoid=("p", "a", "h", "A", "x")
    )

    odd_prime = prime("p", tag="euler_residue_prime")
    nonzero_value = not_divides("p", "a", tag="euler_residue_value")
    residue = quadratic_residue("p", "a", tag="euler_residue")
    half_power = power_relation("a", "h", "A", tag="euler_residue_half")
    result = _mod_eq_term(
        "p", "A", "1", tag="euler_residue_result", avoid=("p", "a", "h", "A")
    )

    root_two = _power_terms("x", "2", "x1", tag="euler_root_two")
    square_half = power_relation("x1", "h", "x2", tag="euler_square_half")
    root_double_half = _power_terms(
        "x", "2 * h", "x3", tag="euler_root_double_half"
    )
    square_value = _mod_eq_term(
        "p", "x1", "a", tag="euler_square_value", avoid=("p", "a", "h", "A", "x", "x1")
    )
    powers_congruent = _mod_eq_term(
        "p", "x2", "A", tag="euler_powers_congruent", avoid=("p", "a", "h", "A", "x", "x1", "x2")
    )
    value_power_back = _mod_eq_term(
        "p", "A", "x2", tag="euler_value_power_back", avoid=("p", "a", "h", "A", "x", "x1", "x2")
    )
    root_half_one = _mod_eq_term(
        "p", "x2", "1", tag="euler_root_half_one", avoid=("p", "a", "h", "A", "x", "x1", "x2")
    )
    root_fermat = _mod_eq_term(
        "p", "x3", "1", tag="euler_root_fermat", avoid=("p", "a", "h", "A", "x", "x1", "x2", "x3")
    )

    return (
        spec(
            "mod_eq_zero_to_dvd_nonzero",
            f"forall p a. ~(p = 0) -> ({zero_mod}) -> exists k. a = p * k",
            (
                "nonzero_is_succ",
                "mod_eq_to_remainder_decomposition",
                "mul_comm",
            ),
            (
                "intro p",
                "intro a",
                "intro hp",
                "intro hmod",
                "have hps : exists n. p = S n",
                "specialize nonzero_is_succ p",
                "apply nonzero_is_succ",
                "exact hp",
                "cases hps",
                "have hbound : exists d. d + S 0 = p",
                "exists x",
                "trans S x",
                "simp",
                "symm",
                "exact hps_witness",
                "have hdecomp : exists q. a = q * p + 0",
                "specialize mod_eq_to_remainder_decomposition p",
                "specialize mod_eq_to_remainder_decomposition a",
                "specialize mod_eq_to_remainder_decomposition 0",
                "apply mod_eq_to_remainder_decomposition",
                "exact hp",
                "exact hbound",
                "exact hmod",
                "cases hdecomp",
                "exists x1",
                "trans x1 * p + 0",
                "exact hdecomp_witness",
                "trans x1 * p",
                "simp",
                "apply mul_comm",
            ),
            "For a nonzero modulus, congruence to zero gives an explicit divisor witness.",
        ),
        spec(
            "quadratic_residue_half_power_mod_one",
            f"forall p h a A. p = 2 * h + 1 -> ({odd_prime}) -> "
            f"({nonzero_value}) -> ({residue}) -> ({half_power}) -> ({result})",
            (
                "mod_eq_zero_to_dvd_nonzero",
                "prime_nonzero",
                "multiple_mul_right",
                "dvd_to_mod_zero",
                "mod_eq_symm",
                "mod_eq_trans",
                "pow_exists",
                "pow_two",
                "pow_mul_exp",
                "fermat_predecessor_exponent_mod_one",
                "pow_mod_congruent",
            ),
            (
                "intro p",
                "intro h",
                "intro a",
                "intro A",
                "intro hshape",
                "intro hp",
                "intro hnonzero",
                "intro hresidue",
                "intro hA",
                "cases hresidue",
                "have hp0 : ~(p = 0)",
                "intro hpzero",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hp",
                "exact hpzero",
                "have hroot_nonzero : ~(exists k. x = p * k)",
                "intro hroot_divides",
                "have hsquare_divides : exists k. x * x = p * k",
                "specialize multiple_mul_right p",
                "specialize multiple_mul_right x",
                "specialize multiple_mul_right x",
                "apply multiple_mul_right",
                "exact hroot_divides",
                f"have hsquare_zero : {root_square_zero}",
                "specialize dvd_to_mod_zero p",
                "specialize dvd_to_mod_zero (x * x)",
                "apply dvd_to_mod_zero",
                "exact hsquare_divides",
                f"have hvalue_square : {value_square}",
                "specialize mod_eq_symm p",
                "specialize mod_eq_symm (x * x)",
                "specialize mod_eq_symm a",
                "apply mod_eq_symm",
                "exact hresidue_witness",
                f"have hvalue_zero : {value_zero}",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans a",
                "specialize mod_eq_trans (x * x)",
                "specialize mod_eq_trans 0",
                "apply mod_eq_trans",
                "exact hvalue_square",
                "exact hsquare_zero",
                "have hvalue_divides : exists k. a = p * k",
                "specialize mod_eq_zero_to_dvd_nonzero p",
                "specialize mod_eq_zero_to_dvd_nonzero a",
                "apply mod_eq_zero_to_dvd_nonzero",
                "exact hp0",
                "exact hvalue_zero",
                "apply hnonzero",
                "exact hvalue_divides",
                f"have hroot_two_exists : exists R. ({_power_terms('x', '2', 'R', tag='euler_root_two_exists')})",
                "specialize pow_exists x",
                "specialize pow_exists 2",
                "exact pow_exists",
                "cases hroot_two_exists",
                f"have hroot_two : {root_two}",
                "exact hroot_two_exists_witness",
                "have hroot_two_eq : x1 = x * x",
                "specialize pow_two x",
                "specialize pow_two 2",
                "specialize pow_two x1",
                "apply pow_two",
                "refl",
                "exact hroot_two",
                f"have hsquare_half_exists : exists R. ({power_relation('x1', 'h', 'R', tag='euler_square_half_exists')})",
                "specialize pow_exists x1",
                "specialize pow_exists h",
                "exact pow_exists",
                "cases hsquare_half_exists",
                f"have hsquare_half : {square_half}",
                "exact hsquare_half_exists_witness",
                f"have hroot_total_exists : exists R. ({_power_terms('x', '2 * h', 'R', tag='euler_root_total_exists')})",
                "specialize pow_exists x",
                "specialize pow_exists (2 * h)",
                "exact pow_exists",
                "cases hroot_total_exists",
                f"have hroot_total : {root_double_half}",
                "exact hroot_total_exists_witness",
                "have hiterated : x2 = x3",
                "specialize pow_mul_exp x",
                "specialize pow_mul_exp 2",
                "specialize pow_mul_exp h",
                "specialize pow_mul_exp (2 * h)",
                "specialize pow_mul_exp x1",
                "specialize pow_mul_exp x2",
                "specialize pow_mul_exp x3",
                "apply pow_mul_exp",
                "refl",
                "exact hroot_two",
                "exact hsquare_half",
                "exact hroot_total",
                "have hpredecessor : p = S (2 * h)",
                "trans 2 * h + 1",
                "exact hshape",
                "simp",
                f"have hfermat : {root_fermat}",
                "specialize fermat_predecessor_exponent_mod_one p",
                "specialize fermat_predecessor_exponent_mod_one (2 * h)",
                "specialize fermat_predecessor_exponent_mod_one x",
                "specialize fermat_predecessor_exponent_mod_one x3",
                "apply fermat_predecessor_exponent_mod_one",
                "exact hpredecessor",
                "exact hp",
                "exact hroot_nonzero",
                "exact hroot_total",
                f"have hsquare_value : {square_value}",
                "rewrite hroot_two_eq",
                "exact hresidue_witness",
                f"have hpowers : {powers_congruent}",
                "specialize pow_mod_congruent p",
                "specialize pow_mod_congruent x1",
                "specialize pow_mod_congruent a",
                "specialize pow_mod_congruent h",
                "specialize pow_mod_congruent x2",
                "specialize pow_mod_congruent A",
                "apply pow_mod_congruent",
                "exact hsquare_value",
                "exact hsquare_half",
                "exact hA",
                f"have hback : {value_power_back}",
                "specialize mod_eq_symm p",
                "specialize mod_eq_symm x2",
                "specialize mod_eq_symm A",
                "apply mod_eq_symm",
                "exact hpowers",
                f"have hhalf_one : {root_half_one}",
                "rewrite hiterated",
                "exact hfermat",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans A",
                "specialize mod_eq_trans x2",
                "specialize mod_eq_trans 1",
                "apply mod_eq_trans",
                "exact hback",
                "exact hhalf_one",
            ),
            "A nonzero quadratic residue has half power one modulo an odd prime.",
        ),
    )


__all__ = ["make_euler_criterion_residue_candidate_theorems"]
