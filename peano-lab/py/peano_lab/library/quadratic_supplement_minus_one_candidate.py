"""Constructive first supplementary law for quadratic reciprocity.

Natural-number arithmetic represents ``-1 (mod p)`` by the predecessor ``n``
of an odd prime ``p = S n``.  The already checked predecessor-power bridge
identifies the Euler half power of ``n`` with ``1`` for an even half and ``n``
for an odd half.  The complete bounded Euler criterion then converts those
two congruences into actual residue and nonresidue statements, and the
odd-half/modulo-four bridges give the classical supplementary-law surface.

Every predicate is expanded into the unchanged first-order Peano language.
These specifications are isolated, dependency-curried candidates: they are
neither registered as public theorems nor admitted as closed certificates.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_map_candidate import prime
from .finite_fold_surface import power_relation
from .quadratic_residue_surface import quadratic_residue
from .wilson_pair_order_candidate import _lt_term
from .wilson_pair_product_candidate import _mod_eq_term


def _even(value: str, *, tag: str) -> str:
    return f"exists qsm_even_{tag}. {value} = 2 * qsm_even_{tag}"


def _odd(value: str, *, tag: str) -> str:
    return f"exists qsm_odd_{tag}. {value} = 2 * qsm_odd_{tag} + 1"


def _mod_four_one(value: str, *, tag: str) -> str:
    return f"exists qsm_four_one_{tag}. {value} = 4 * qsm_four_one_{tag} + 1"


def _mod_four_three(value: str, *, tag: str) -> str:
    return (
        f"exists qsm_four_three_{tag}. "
        f"{value} = 4 * qsm_four_three_{tag} + 3"
    )


def _iff(left: str, right: str) -> str:
    return f"((({left}) -> ({right})) /\\ (({right}) -> ({left})))"


def make_quadratic_supplement_minus_one_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the half-parity and exact modulo-four supplementary laws."""

    prime_p = prime("p", tag="qsm_prime")
    odd_p = _odd("p", tag="modulus")
    qres_n = quadratic_residue("p", "n", tag="qsm_predecessor")
    even_h = _even("h", tag="half")
    odd_h = _odd("h", tag="half")
    one_p = _mod_four_one("p", tag="modulus")
    three_p = _mod_four_three("p", tag="modulus")

    half_residue_iff = _iff(qres_n, even_h)
    half_nonresidue_iff = _iff(f"~({qres_n})", odd_h)
    half_classification = (
        f"(({half_residue_iff}) /\\ ({half_nonresidue_iff}))"
    )
    residue_law = _iff(qres_n, one_p)
    nonresidue_law = _iff(f"~({qres_n})", three_p)

    local_variables = ("p", "n", "h", "x")
    local_power = power_relation("n", "h", "x", tag="qsm_power")
    local_mod_one = _mod_eq_term(
        "p", "x", "1", tag="qsm_mod_one", avoid=local_variables
    )
    local_mod_predecessor = _mod_eq_term(
        "p", "x", "n", tag="qsm_mod_predecessor", avoid=local_variables
    )
    local_bound = _lt_term(
        "n", "p", tag="qsm_predecessor_bound", avoid=("p", "n", "h")
    )
    local_euler = (
        f"(({_iff(qres_n, local_mod_one)}) /\\ "
        f"({_iff(f'~({qres_n})', local_mod_predecessor)}))"
    )
    local_sign_bridge = (
        f"((({even_h}) -> ({local_mod_one})) /\\ "
        f"(({odd_h}) -> ({local_mod_predecessor})))"
    )

    qres_x = quadratic_residue("p", "n", tag="qsm_endpoint_predecessor")
    even_x = _even("x", tag="endpoint_half")
    odd_x = _odd("x", tag="endpoint_half")
    local_half_classification = (
        f"(({_iff(qres_x, even_x)}) /\\ "
        f"({_iff(f'~({qres_x})', odd_x)}))"
    )
    local_even_bridge = _iff(even_x, one_p)
    local_odd_bridge = _iff(odd_x, three_p)

    return (
        spec(
            "prime_predecessor_nonzero",
            f"forall p n. p = S n -> ({prime_p}) -> ~(n = 0)",
            (),
            (
                "intro p",
                "intro n",
                "intro hpredecessor",
                "intro hprime",
                "cases hprime",
                "intro hzero",
                "apply hprime_left",
                "rewrite hpredecessor",
                "rewrite hzero",
                "refl",
            ),
            "The predecessor of a prime cannot be zero.",
        ),
        spec(
            "odd_predecessor_double_half",
            "forall p n h. p = S n -> p = 2 * h + 1 -> n = h + h",
            ("mul_comm", "zero_add"),
            (
                "intro p",
                "intro n",
                "intro h",
                "intro hpredecessor",
                "intro hodd",
                "have hdouble : h + h = 2 * h",
                "trans h * 2",
                "simp [zero_add]",
                "specialize mul_comm h",
                "specialize mul_comm 2",
                "apply mul_comm",
                "have hsuccessors : S n = S (2 * h)",
                "trans p",
                "symm",
                "exact hpredecessor",
                "trans 2 * h + 1",
                "exact hodd",
                "simp",
                "have hpredecessors : n = 2 * h",
                "apply PA2",
                "exact hsuccessors",
                "trans 2 * h",
                "exact hpredecessors",
                "symm",
                "exact hdouble",
            ),
            "An odd successor has predecessor equal to twice its odd half.",
        ),
        spec(
            "quadratic_supplement_minus_one_half_parity",
            f"forall p n h. p = S n -> ({prime_p}) -> "
            f"n = h + h -> ({half_classification})",
            (
                "prime_predecessor_nonzero",
                "pow_exists",
                "bounded_euler_criterion_complete",
                "pow_predecessor_parity_mod",
                "parity_cases",
                "zero_add",
            ),
            (
                "intro p",
                "intro n",
                "intro h",
                "intro hpredecessor",
                "intro hprime",
                "intro hdouble",
                "have hnonzero : ~(n = 0)",
                "intro hzero",
                "specialize prime_predecessor_nonzero p",
                "specialize prime_predecessor_nonzero n",
                "apply prime_predecessor_nonzero",
                "exact hpredecessor",
                "exact hprime",
                "exact hzero",
                f"have hbound : {local_bound}",
                "exists 0",
                "trans S n",
                "apply zero_add",
                "symm",
                "exact hpredecessor",
                f"have hpower : exists A. ({power_relation('n', 'h', 'A', tag='qsm_exists_power')})",
                "specialize pow_exists n",
                "specialize pow_exists h",
                "exact pow_exists",
                "cases hpower",
                f"have heuler : {local_euler}",
                "specialize bounded_euler_criterion_complete p",
                "specialize bounded_euler_criterion_complete n",
                "specialize bounded_euler_criterion_complete n",
                "specialize bounded_euler_criterion_complete h",
                "specialize bounded_euler_criterion_complete x",
                "apply bounded_euler_criterion_complete",
                "exact hpredecessor",
                "exact hprime",
                "exact hnonzero",
                "exact hbound",
                "exact hdouble",
                "exact hpower_witness",
                "cases heuler",
                "cases heuler_left",
                "cases heuler_right",
                f"have hsign : {local_sign_bridge}",
                "specialize pow_predecessor_parity_mod p",
                "specialize pow_predecessor_parity_mod n",
                "specialize pow_predecessor_parity_mod h",
                "specialize pow_predecessor_parity_mod x",
                "apply pow_predecessor_parity_mod",
                "exact hpredecessor",
                "exact hpower_witness",
                "cases hsign",
                "split",
                "split",
                "intro hresidue",
                "specialize parity_cases h",
                "cases parity_cases",
                "cases parity_cases_witness",
                "exists x1",
                "exact parity_cases_witness_left",
                "exfalso",
                f"have hnotresidue : ~({qres_n})",
                "intro hresidue_again",
                "apply heuler_right_right",
                "apply hsign_right",
                "exists x1",
                "exact parity_cases_witness_right",
                "exact hresidue_again",
                "apply hnotresidue",
                "exact hresidue",
                "intro heven",
                "apply heuler_left_right",
                "apply hsign_left",
                "exact heven",
                "split",
                "intro hnotresidue",
                "specialize parity_cases h",
                "cases parity_cases",
                "cases parity_cases_witness",
                "exfalso",
                "apply hnotresidue",
                "apply heuler_left_right",
                "apply hsign_left",
                "exists x1",
                "exact parity_cases_witness_left",
                "exists x1",
                "exact parity_cases_witness_right",
                "intro hodd",
                "intro hresidue",
                "apply heuler_right_right",
                "apply hsign_right",
                "exact hodd",
                "exact hresidue",
            ),
            "For an odd prime, its predecessor is a quadratic residue exactly "
            "when the prime's half is even, and a nonresidue exactly when "
            "that half is odd.",
        ),
        spec(
            "quadratic_supplement_minus_one_residue_iff_mod_four_one",
            f"forall p n. p = S n -> ({prime_p}) -> ({odd_p}) -> "
            f"({residue_law})",
            (
                "odd_predecessor_double_half",
                "quadratic_supplement_minus_one_half_parity",
                "odd_half_even_iff_mod4_one",
            ),
            (
                "intro p",
                "intro n",
                "intro hpredecessor",
                "intro hprime",
                "intro hodd",
                "cases hodd",
                "have hdouble : n = x + x",
                "specialize odd_predecessor_double_half p",
                "specialize odd_predecessor_double_half n",
                "specialize odd_predecessor_double_half x",
                "apply odd_predecessor_double_half",
                "exact hpredecessor",
                "exact hodd_witness",
                f"have hclassification : {local_half_classification}",
                "specialize quadratic_supplement_minus_one_half_parity p",
                "specialize quadratic_supplement_minus_one_half_parity n",
                "specialize quadratic_supplement_minus_one_half_parity x",
                "apply quadratic_supplement_minus_one_half_parity",
                "exact hpredecessor",
                "exact hprime",
                "exact hdouble",
                "cases hclassification",
                "cases hclassification_left",
                f"have hmodfour : {local_even_bridge}",
                "specialize odd_half_even_iff_mod4_one p",
                "specialize odd_half_even_iff_mod4_one x",
                "apply odd_half_even_iff_mod4_one",
                "exact hodd_witness",
                "cases hmodfour",
                "split",
                "intro hresidue",
                "apply hmodfour_left",
                "apply hclassification_left_left",
                "exact hresidue",
                "intro hfourone",
                "apply hclassification_left_right",
                "apply hmodfour_right",
                "exact hfourone",
            ),
            "The first supplementary law: minus one is a quadratic residue "
            "modulo an odd prime exactly when that prime is one modulo four.",
        ),
        spec(
            "quadratic_supplement_minus_one_nonresidue_iff_mod_four_three",
            f"forall p n. p = S n -> ({prime_p}) -> ({odd_p}) -> "
            f"({nonresidue_law})",
            (
                "odd_predecessor_double_half",
                "quadratic_supplement_minus_one_half_parity",
                "odd_half_odd_iff_mod4_three",
            ),
            (
                "intro p",
                "intro n",
                "intro hpredecessor",
                "intro hprime",
                "intro hodd",
                "cases hodd",
                "have hdouble : n = x + x",
                "specialize odd_predecessor_double_half p",
                "specialize odd_predecessor_double_half n",
                "specialize odd_predecessor_double_half x",
                "apply odd_predecessor_double_half",
                "exact hpredecessor",
                "exact hodd_witness",
                f"have hclassification : {local_half_classification}",
                "specialize quadratic_supplement_minus_one_half_parity p",
                "specialize quadratic_supplement_minus_one_half_parity n",
                "specialize quadratic_supplement_minus_one_half_parity x",
                "apply quadratic_supplement_minus_one_half_parity",
                "exact hpredecessor",
                "exact hprime",
                "exact hdouble",
                "cases hclassification",
                "cases hclassification_right",
                f"have hmodfour : {local_odd_bridge}",
                "specialize odd_half_odd_iff_mod4_three p",
                "specialize odd_half_odd_iff_mod4_three x",
                "apply odd_half_odd_iff_mod4_three",
                "exact hodd_witness",
                "cases hmodfour",
                "split",
                "intro hnonresidue",
                "apply hmodfour_left",
                "apply hclassification_right_left",
                "exact hnonresidue",
                "intro hfourthree",
                "intro hresidue",
                "apply hclassification_right_right",
                "apply hmodfour_right",
                "exact hfourthree",
                "exact hresidue",
            ),
            "The first supplementary law's complementary branch: minus one "
            "is a nonresidue exactly for odd primes that are three modulo four.",
        ),
        spec(
            "quadratic_supplement_minus_one_complete",
            f"forall p n. p = S n -> ({prime_p}) -> ({odd_p}) -> "
            f"(({residue_law}) /\\ ({nonresidue_law}))",
            (
                "quadratic_supplement_minus_one_residue_iff_mod_four_one",
                "quadratic_supplement_minus_one_nonresidue_iff_mod_four_three",
            ),
            (
                "intro p",
                "intro n",
                "intro hpredecessor",
                "intro hprime",
                "intro hodd",
                "split",
                "specialize quadratic_supplement_minus_one_residue_iff_mod_four_one p",
                "specialize quadratic_supplement_minus_one_residue_iff_mod_four_one n",
                "apply quadratic_supplement_minus_one_residue_iff_mod_four_one",
                "exact hpredecessor",
                "exact hprime",
                "exact hodd",
                "specialize quadratic_supplement_minus_one_nonresidue_iff_mod_four_three p",
                "specialize quadratic_supplement_minus_one_nonresidue_iff_mod_four_three n",
                "apply quadratic_supplement_minus_one_nonresidue_iff_mod_four_three",
                "exact hpredecessor",
                "exact hprime",
                "exact hodd",
            ),
            "Complete constructive first supplementary law, including both "
            "the one-modulo-four residue and three-modulo-four nonresidue cases.",
        ),
    )


__all__ = ["make_quadratic_supplement_minus_one_candidate_theorems"]
