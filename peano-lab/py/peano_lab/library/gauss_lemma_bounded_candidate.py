"""Constructive bounded Gauss-lemma classification.

This isolated candidate composes the witness-producing Gauss power
congruence, the predecessor-power parity bridge, and the complete bounded
Euler criterion.  For a canonical nonzero representative ``a < p`` at an
odd prime ``p = 2*h+1``, it retains the signed half-range prefix and its
reflection count ``e`` and proves both exact classifications

``QRes(p,a) <-> Even(e)`` and ``~QRes(p,a) <-> Odd(e)``.

All surface relations expand before parsing to unchanged first-order Peano
arithmetic.  The proof is constructive and dependency-curried; this module
is not imported by the public theorem registry and admits nothing.
"""

from __future__ import annotations

from typing import Any, Callable

from .euler_scaled_inverse_candidate import prime
from .fermat_residue_map_candidate import not_divides
from .finite_fold_surface import bit_count, power_relation
from .gauss_lemma_endpoint_candidate import double_half_power_relation
from .gauss_sign_bridge import _even, _odd
from .gauss_signed_prefix_candidate import half_range, signed_half_prefix
from .quadratic_residue_surface import quadratic_residue
from .wilson_pair_order_candidate import _lt_term
from .wilson_pair_product_candidate import _mod_eq_term


def make_gauss_lemma_bounded_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the signed-count residue/nonresidue equivalence endpoint."""

    variables = ("p", "h", "a", "b", "c", "e", "A", "R")
    prime_p = prime("p", tag="glb_prime")
    a_positive = _lt_term("0", "a", tag="glb_a_positive", avoid=variables)
    a_lt_p = _lt_term("a", "p", tag="glb_a_lt_p", avoid=variables)
    nondivisor = not_divides("p", "a", tag="glb_nondivisor")
    canonical_half = half_range("b", "c", "h", tag="glb_half_range")
    qres = quadratic_residue("p", "a", tag="glb_qres")

    signed_prefix = signed_half_prefix(
        "p",
        "h",
        "a",
        "b",
        "c",
        "mb",
        "mc",
        "sb",
        "sc",
        "h",
        tag="glb_signed_prefix",
    )
    signed_count = bit_count("sb", "sc", "h", "e", tag="glb_count")
    hidden_signed_count = (
        "exists mb mc sb sc. "
        f"(({signed_prefix}) /\\ ({signed_count}))"
    )

    multiplier_power = power_relation("a", "h", "A", tag="glb_multiplier_power")
    sign_power = double_half_power_relation("h", "e", "R", tag="glb_sign_power")
    a_mod_r = _mod_eq_term(
        "p", "A", "R", tag="glb_a_mod_r", avoid=variables
    )
    one_mod_predecessor = _mod_eq_term(
        "p", "1", "2 * h", tag="glb_one_mod_predecessor", avoid=variables
    )

    even_e = _even("e", tag="glb_even")
    odd_e = _odd("e", tag="glb_odd")
    residue_iff_even = f"((({qres}) -> ({even_e})) /\\ (({even_e}) -> ({qres})))"
    nonresidue_iff_odd = (
        f"((~({qres}) -> ({odd_e})) /\\ (({odd_e}) -> ~({qres})))"
    )
    conclusion = (
        "exists e. "
        f"(({hidden_signed_count}) /\\ "
        f"(({residue_iff_even}) /\\ ({nonresidue_iff_odd})))"
    )

    gauss_package = (
        "exists e A R. "
        f"(({multiplier_power}) /\\ (({sign_power}) /\\ "
        f"(({hidden_signed_count}) /\\ ({a_mod_r}))))"
    )
    # Formula variants after destructing the Gauss package.  The proof engine
    # names the existential witnesses ``x`` (e), ``x1`` (A), and ``x2`` (R).
    local_even = _even("x", tag="glb_local_even")
    local_odd = _odd("x", tag="glb_local_odd")
    local_a_mod_one = _mod_eq_term(
        "p", "x1", "1", tag="glb_local_a_mod_one", avoid=variables + ("x", "x1", "x2")
    )
    local_a_mod_predecessor = _mod_eq_term(
        "p",
        "x1",
        "2 * h",
        tag="glb_local_a_mod_predecessor",
        avoid=variables + ("x", "x1", "x2"),
    )
    local_r_mod_one = _mod_eq_term(
        "p", "x2", "1", tag="glb_local_r_mod_one", avoid=variables + ("x", "x1", "x2")
    )
    local_r_mod_predecessor = _mod_eq_term(
        "p",
        "x2",
        "2 * h",
        tag="glb_local_r_mod_predecessor",
        avoid=variables + ("x", "x1", "x2"),
    )
    local_one_mod_a = _mod_eq_term(
        "p", "1", "x1", tag="glb_local_one_mod_a", avoid=variables + ("x", "x1", "x2")
    )
    local_one_mod_r = _mod_eq_term(
        "p", "1", "x2", tag="glb_local_one_mod_r", avoid=variables + ("x", "x1", "x2")
    )
    local_euler_complete = (
        f"((((({qres}) -> ({local_a_mod_one})) /\\ "
        f"(({local_a_mod_one}) -> ({qres})))) /\\ "
        f"((~({qres}) -> ({local_a_mod_predecessor})) /\\ "
        f"(({local_a_mod_predecessor}) -> ~({qres}))))"
    )
    local_parity_bridge = (
        f"((({local_even}) -> ({local_r_mod_one})) /\\ "
        f"(({local_odd}) -> ({local_r_mod_predecessor})))"
    )
    return (
        spec(
            "bounded_gauss_lemma_complete",
            "forall p h a b c. p = 2 * h + 1 -> "
            f"({prime_p}) -> ({a_positive}) -> ({a_lt_p}) -> "
            f"({canonical_half}) -> ({conclusion})",
            (
                "lt_irrefl_expanded",
                "bounded_nonzero_not_divides",
                "gauss_lemma_power_congruence_exists",
                "pow_predecessor_parity_mod",
                "bounded_euler_criterion_complete",
                "parity_cases",
                "odd_prime_one_not_mod_predecessor",
                "mod_eq_symm",
                "mod_eq_trans",
                "mul_comm",
                "zero_add",
            ),
            (
                "intro p",
                "intro h",
                "intro a",
                "intro b",
                "intro c",
                "intro hpodd",
                "intro hprime",
                "intro hpositive",
                "intro halt",
                "intro hhalf",
                "have hpsucc : p = S (2 * h)",
                "trans 2 * h + 1",
                "exact hpodd",
                "simp",
                "have hdouble : h + h = 2 * h",
                "trans h * 2",
                "simp [zero_add]",
                "specialize mul_comm h",
                "specialize mul_comm 2",
                "apply mul_comm",
                "have ha0 : ~(a = 0)",
                "intro haeq",
                "specialize lt_irrefl_expanded 0",
                "apply lt_irrefl_expanded",
                "rewrite haeq at hpositive",
                "exact hpositive",
                f"have hnotdiv : {nondivisor}",
                "intro hdiv",
                "specialize bounded_nonzero_not_divides p",
                "specialize bounded_nonzero_not_divides a",
                "apply bounded_nonzero_not_divides",
                "exact ha0",
                "exact halt",
                "exact hdiv",
                f"have hgauss : {gauss_package}",
                "specialize gauss_lemma_power_congruence_exists p",
                "specialize gauss_lemma_power_congruence_exists h",
                "specialize gauss_lemma_power_congruence_exists a",
                "specialize gauss_lemma_power_congruence_exists b",
                "specialize gauss_lemma_power_congruence_exists c",
                "apply gauss_lemma_power_congruence_exists",
                "exact hpodd",
                "exact hprime",
                "exact hnotdiv",
                "exact hhalf",
                "cases hgauss",
                "cases hgauss_witness",
                "cases hgauss_witness_witness",
                "cases hgauss_witness_witness_witness",
                "cases hgauss_witness_witness_witness_right",
                "cases hgauss_witness_witness_witness_right_right",
                f"have heuler : {local_euler_complete}",
                "specialize bounded_euler_criterion_complete p",
                "specialize bounded_euler_criterion_complete a",
                "specialize bounded_euler_criterion_complete (2 * h)",
                "specialize bounded_euler_criterion_complete h",
                "specialize bounded_euler_criterion_complete x1",
                "apply bounded_euler_criterion_complete",
                "exact hpsucc",
                "exact hprime",
                "exact ha0",
                "exact halt",
                "symm",
                "exact hdouble",
                "exact hgauss_witness_witness_witness_left",
                "cases heuler",
                "cases heuler_left",
                "cases heuler_right",
                f"have hbridge : {local_parity_bridge}",
                "specialize pow_predecessor_parity_mod p",
                "specialize pow_predecessor_parity_mod (2 * h)",
                "specialize pow_predecessor_parity_mod x",
                "specialize pow_predecessor_parity_mod x2",
                "apply pow_predecessor_parity_mod",
                "exact hpsucc",
                "exact hgauss_witness_witness_witness_right_left",
                "cases hbridge",
                f"have hseparation : ~({one_mod_predecessor})",
                "intro hcollision",
                "specialize odd_prime_one_not_mod_predecessor p",
                "specialize odd_prime_one_not_mod_predecessor (2 * h)",
                "specialize odd_prime_one_not_mod_predecessor h",
                "apply odd_prime_one_not_mod_predecessor",
                "exact hpsucc",
                "exact hprime",
                "symm",
                "exact hdouble",
                "exact hcollision",
                f"have hqres_even : ({qres}) -> ({local_even})",
                "intro hqres",
                "specialize parity_cases x",
                "cases parity_cases",
                "cases parity_cases_witness",
                "exists x3",
                "exact parity_cases_witness_left",
                "exfalso",
                "apply hseparation",
                f"have hAone : {local_a_mod_one}",
                "apply heuler_left_left",
                "exact hqres",
                f"have honeA : {local_one_mod_a}",
                "specialize mod_eq_symm p",
                "specialize mod_eq_symm x1",
                "specialize mod_eq_symm 1",
                "apply mod_eq_symm",
                "exact hAone",
                f"have honeR : {local_one_mod_r}",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans 1",
                "specialize mod_eq_trans x1",
                "specialize mod_eq_trans x2",
                "apply mod_eq_trans",
                "exact honeA",
                "exact hgauss_witness_witness_witness_right_right_right",
                f"have hRpred : {local_r_mod_predecessor}",
                "apply hbridge_right",
                "exists x3",
                "exact parity_cases_witness_right",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans 1",
                "specialize mod_eq_trans x2",
                "specialize mod_eq_trans (2 * h)",
                "apply mod_eq_trans",
                "exact honeR",
                "exact hRpred",
                f"have heven_qres : ({local_even}) -> ({qres})",
                "intro heven",
                f"have hRone : {local_r_mod_one}",
                "apply hbridge_left",
                "exact heven",
                f"have hAone : {local_a_mod_one}",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans x1",
                "specialize mod_eq_trans x2",
                "specialize mod_eq_trans 1",
                "apply mod_eq_trans",
                "exact hgauss_witness_witness_witness_right_right_right",
                "exact hRone",
                "apply heuler_left_right",
                "exact hAone",
                f"have hnonres_odd : ~({qres}) -> ({local_odd})",
                "intro hnonres",
                "specialize parity_cases x",
                "cases parity_cases",
                "cases parity_cases_witness",
                "exfalso",
                "apply hseparation",
                f"have hRone : {local_r_mod_one}",
                "apply hbridge_left",
                "exists x3",
                "exact parity_cases_witness_left",
                f"have hAone : {local_a_mod_one}",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans x1",
                "specialize mod_eq_trans x2",
                "specialize mod_eq_trans 1",
                "apply mod_eq_trans",
                "exact hgauss_witness_witness_witness_right_right_right",
                "exact hRone",
                f"have honeA : {local_one_mod_a}",
                "specialize mod_eq_symm p",
                "specialize mod_eq_symm x1",
                "specialize mod_eq_symm 1",
                "apply mod_eq_symm",
                "exact hAone",
                f"have hApred : {local_a_mod_predecessor}",
                "apply heuler_right_left",
                "exact hnonres",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans 1",
                "specialize mod_eq_trans x1",
                "specialize mod_eq_trans (2 * h)",
                "apply mod_eq_trans",
                "exact honeA",
                "exact hApred",
                "exists x3",
                "exact parity_cases_witness_right",
                f"have hodd_nonres : ({local_odd}) -> ~({qres})",
                "intro hodd",
                f"have hRpred : {local_r_mod_predecessor}",
                "apply hbridge_right",
                "exact hodd",
                f"have hApred : {local_a_mod_predecessor}",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans x1",
                "specialize mod_eq_trans x2",
                "specialize mod_eq_trans (2 * h)",
                "apply mod_eq_trans",
                "exact hgauss_witness_witness_witness_right_right_right",
                "exact hRpred",
                "intro hqres",
                "apply heuler_right_right",
                "exact hApred",
                "exact hqres",
                "exists x",
                "split",
                "exact hgauss_witness_witness_witness_right_right_left",
                "split",
                "split",
                "exact hqres_even",
                "exact heven_qres",
                "split",
                "exact hnonres_odd",
                "exact hodd_nonres",
            ),
            "A canonical Gauss reflection count is even exactly for residues "
            "and odd exactly for nonresidues.",
        ),
    )


__all__ = ["make_gauss_lemma_bounded_candidate_theorems"]
