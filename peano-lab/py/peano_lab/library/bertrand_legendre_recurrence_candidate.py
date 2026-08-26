"""Constructive finite-sum assembly for Legendre's recurrence.

This isolated tranche turns the pointwise quotient identity from
``bertrand_legendre_successor_candidate`` into the exact relational theorem

``L_p(S n) = L_p(n) + v_p(S n)``.

The five rows deliberately expose the small reusable interfaces needed for
that assembly: dropping a final zero from a beta sum, proving that the final
old quotient is zero, rebuilding an old Legendre prefix at successor length,
constructing a threshold prefix with its exact sum, and finally adding the
three pointwise-related sums.

All notation is expanded before parsing into the unchanged first-order Peano
language.  The proofs are intuitionistic and use no choice principle.  This
module is unregistered pending independent closure and mutation review.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_legendre_sum_candidate import (
    _power_quotient_prefix_terms,
    legendre_sum,
    power_quotient_prefix,
)
from .bertrand_legendre_successor_candidate import _power_valuation_terms
from .bertrand_power_valuation_candidate import _power_terms
from .eisenstein_initial_segment_count_candidate import (
    _successor_prefix,
    eisenstein_initial_segment_prefix,
)
from .fermat_residue_map_candidate import prime
from .finite_fold_surface import beta_at, bit_count, sum_relation
from .finite_sum_theorems import _at, _sum_relation_terms


def _lt(left: str, right: str, *, tag: str) -> str:
    return f"exists blrr_lt_gap_{tag}. blrr_lt_gap_{tag} + S ({left}) = ({right})"


def _le(left: str, right: str, *, tag: str) -> str:
    return f"exists blrr_le_gap_{tag}. blrr_le_gap_{tag} + ({left}) = ({right})"


def _successor_legendre_sum_terms(
    base: str,
    predecessor: str,
    result: str,
    *,
    tag: str,
) -> str:
    """Expand ``LegendreSum(base,S predecessor,result)`` hygienically."""

    code = f"blrr_code_{tag}"
    scale = f"blrr_scale_{tag}"
    length = f"S {predecessor}"
    prefix = _power_quotient_prefix_terms(
        base,
        length,
        code,
        scale,
        length,
        tag=f"{tag}_prefix",
    )
    total = _sum_relation_terms(
        code,
        scale,
        length,
        result,
        tag=f"blrr_{tag}_sum",
    )
    return f"exists {code} {scale}. (({prefix}) /\\ ({total}))"


def make_bertrand_legendre_recurrence_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-topological finite-sum recurrence tranche."""

    successor_sum = _sum_relation_terms(
        "b", "c", "S l", "n", tag="blrr_drop_successor"
    )
    final_zero = _at("b", "c", "l", "0", tag="blrr_drop_zero")
    predecessor_sum = sum_relation(
        "b", "c", "l", "n", tag="blrr_drop_predecessor"
    )
    decomposition = (
        "exists a r. "
        f"({beta_at('b', 'c', 'l', 'a', tag='blrr_drop_decomposition_entry')}) /\\ "
        f"(({sum_relation('b', 'c', 'l', 'r', tag='blrr_drop_decomposition_prefix')}) /\\ "
        "n = r + a)"
    )

    prime_p = prime("p", tag="blrr_tail_prime")
    successor_prefix = _power_quotient_prefix_terms(
        "p", "n", "b", "c", "S n", tag="blrr_tail_prefix"
    )
    tail_zero = _at("b", "c", "n", "0", tag="blrr_tail_zero")

    old_legendre = legendre_sum("p", "n", "e", tag="blrr_extend_old")
    extended_prefix = _power_quotient_prefix_terms(
        "p", "n", "b", "c", "S n", tag="blrr_extend_prefix"
    )
    extended_sum = _sum_relation_terms(
        "b", "c", "S n", "e", tag="blrr_extend_sum"
    )
    extended_result = (
        f"exists b c. (({extended_prefix}) /\\ ({extended_sum}))"
    )

    initial_prefix = eisenstein_initial_segment_prefix(
        "q", "b", "c", "k", tag="blrr_initial_prefix"
    )
    initial_bound = _le("q", "k", tag="blrr_initial_bound")
    initial_sum = sum_relation(
        "b", "c", "k", "q", tag="blrr_initial_sum"
    )
    initial_result = (
        f"exists b c. (({initial_prefix}) /\\ ({initial_sum}))"
    )

    recurrence_prime = prime("p", tag="blrr_recurrence_prime")
    recurrence_valuation = _power_valuation_terms(
        "p", "S n", "f", tag="blrr_recurrence_valuation"
    )
    recurrence_old = legendre_sum(
        "p", "n", "e", tag="blrr_recurrence_old"
    )
    recurrence_new = _successor_legendre_sum_terms(
        "p", "n", "g", tag="recurrence_new"
    )

    return (
        spec(
            "beta_sum_succ_last_zero",
            "forall b c l n. "
            f"({successor_sum}) -> ({final_zero}) -> ({predecessor_sum})",
            ("beta_sum_succ_decompose", "beta_at_unique"),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro n",
                "intro hsum",
                "intro hzero",
                f"have hdecomposition : {decomposition}",
                "specialize beta_sum_succ_decompose b",
                "specialize beta_sum_succ_decompose c",
                "specialize beta_sum_succ_decompose l",
                "specialize beta_sum_succ_decompose n",
                "apply beta_sum_succ_decompose",
                "exact hsum",
                "cases hdecomposition",
                "cases hdecomposition_witness",
                "cases hdecomposition_witness_witness",
                "cases hdecomposition_witness_witness_right",
                "have ha : x = 0",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique l",
                "specialize beta_at_unique x",
                "specialize beta_at_unique 0",
                "apply beta_at_unique",
                "exact hdecomposition_witness_witness_left",
                "exact hzero",
                "have hn : n = x1",
                "trans x1 + x",
                "exact hdecomposition_witness_witness_right_right",
                "rewrite ha",
                "apply PA3",
                "rewrite hn",
                "rewrite hn",
                "exact hdecomposition_witness_witness_right_left",
            ),
            "A successor beta sum with final entry zero is its predecessor sum.",
        ),
        spec(
            "prime_power_quotient_prefix_last_zero",
            "forall p n b c. "
            f"({prime_p}) -> ({successor_prefix}) -> ({tail_zero})",
            (
                "prime_power_quotient_tail_zero",
                "division_remainder_unique",
                "zero_add",
            ),
            (
                "intro p",
                "intro n",
                "intro b",
                "intro c",
                "intro hp",
                "intro hprefix",
                "have hdata : exists D q r. "
                f"(({_power_terms('p', 'S n', 'D', tag='blrr_tail_stored_power')}) /\\ "
                f"(({beta_at('b', 'c', 'n', 'q', tag='blrr_tail_stored_entry')}) /\\ "
                "((n = D * q + r /\\ exists gap. gap + S r = D))))",
                "specialize hprefix n",
                "apply hprefix",
                "exists 0",
                "specialize zero_add (S n)",
                "exact zero_add",
                "cases hdata",
                "cases hdata_witness",
                "cases hdata_witness_witness",
                "cases hdata_witness_witness_witness",
                "cases hdata_witness_witness_witness_right",
                "cases hdata_witness_witness_witness_right_right",
                "have htail : "
                "((n = x * 0 + n /\\ exists gap. gap + S n = x))",
                "specialize prime_power_quotient_tail_zero p",
                "specialize prime_power_quotient_tail_zero n",
                "specialize prime_power_quotient_tail_zero x",
                "apply prime_power_quotient_tail_zero",
                "exact hp",
                "exact hdata_witness_witness_witness_left",
                "cases htail",
                "have hunique : x1 = 0 /\\ x2 = n",
                "specialize division_remainder_unique x",
                "specialize division_remainder_unique n",
                "specialize division_remainder_unique x1",
                "specialize division_remainder_unique x2",
                "specialize division_remainder_unique 0",
                "specialize division_remainder_unique n",
                "apply division_remainder_unique",
                "exact hdata_witness_witness_witness_right_right_left",
                "exact hdata_witness_witness_witness_right_right_right",
                "exact htail_left",
                "exact htail_right",
                "cases hunique",
                "rewrite <- hunique_left",
                "rewrite <- hunique_left",
                "exact hdata_witness_witness_witness_right_left",
            ),
            "The final entry of a length-(n+1) old quotient prefix is zero.",
        ),
        spec(
            "legendre_sum_zero_extended_prefix",
            "forall p n e. "
            f"({prime_p}) -> ({old_legendre}) -> ({extended_result})",
            (
                "prime_power_quotient_prefix_exists",
                "prime_power_quotient_prefix_last_zero",
                "beta_sum_exists",
                "beta_sum_succ_last_zero",
                "le_succ",
                "legendre_sum_functional",
            ),
            (
                "intro p",
                "intro n",
                "intro e",
                "intro hp",
                "intro hlegendre",
                f"have hprefix : exists b c. ({extended_prefix})",
                "specialize prime_power_quotient_prefix_exists p",
                "specialize prime_power_quotient_prefix_exists n",
                "specialize prime_power_quotient_prefix_exists (S n)",
                "apply prime_power_quotient_prefix_exists",
                "exact hp",
                "cases hprefix",
                "cases hprefix_witness",
                "have hzero : "
                + _at("x", "x1", "n", "0", tag="blrr_extend_last_zero"),
                "specialize prime_power_quotient_prefix_last_zero p",
                "specialize prime_power_quotient_prefix_last_zero n",
                "specialize prime_power_quotient_prefix_last_zero x",
                "specialize prime_power_quotient_prefix_last_zero x1",
                "apply prime_power_quotient_prefix_last_zero",
                "exact hp",
                "exact hprefix_witness_witness",
                "have hsuccessor_sum : exists q. "
                + _sum_relation_terms(
                    "x", "x1", "S n", "q", tag="blrr_extend_sum_exists"
                ),
                "specialize beta_sum_exists x",
                "specialize beta_sum_exists x1",
                "specialize beta_sum_exists (S n)",
                "exact beta_sum_exists",
                "cases hsuccessor_sum",
                "have hpredecessor_sum : "
                + sum_relation(
                    "x", "x1", "n", "x2", tag="blrr_extend_predecessor_sum"
                ),
                "specialize beta_sum_succ_last_zero x",
                "specialize beta_sum_succ_last_zero x1",
                "specialize beta_sum_succ_last_zero n",
                "specialize beta_sum_succ_last_zero x2",
                "apply beta_sum_succ_last_zero",
                "exact hsuccessor_sum_witness",
                "exact hzero",
                "have hrestricted : "
                + power_quotient_prefix(
                    "p", "n", "x", "x1", "n", tag="blrr_extend_restricted"
                ),
                "intro i",
                "intro hi",
                "specialize hprefix_witness_witness i",
                "apply hprefix_witness_witness",
                "specialize le_succ (S i)",
                "specialize le_succ n",
                "apply le_succ",
                "exact hi",
                "have hcompeting : "
                + legendre_sum("p", "n", "x2", tag="blrr_extend_competing"),
                "exists x",
                "exists x1",
                "split",
                "exact hrestricted",
                "exact hpredecessor_sum",
                "have heq : e = x2",
                "specialize legendre_sum_functional p",
                "specialize legendre_sum_functional n",
                "specialize legendre_sum_functional e",
                "specialize legendre_sum_functional x2",
                "apply legendre_sum_functional",
                "exact hlegendre",
                "exact hcompeting",
                "exists x",
                "exists x1",
                "split",
                "exact hprefix_witness_witness",
                "rewrite heq",
                "rewrite heq",
                "exact hsuccessor_sum_witness",
            ),
            "An old Legendre sum has a successor-length quotient code ending in zero.",
        ),
        spec(
            "initial_segment_prefix_sum_exists",
            "forall q k. "
            f"({initial_bound}) -> ({initial_result})",
            (
                "eisenstein_initial_segment_prefix_exists",
                "eisenstein_initial_segment_bit_count_exact",
            ),
            (
                "intro q",
                "intro k",
                "intro hbound",
                f"have hprefix : exists b c. ({initial_prefix})",
                "specialize eisenstein_initial_segment_prefix_exists q",
                "specialize eisenstein_initial_segment_prefix_exists k",
                "exact eisenstein_initial_segment_prefix_exists",
                "cases hprefix",
                "cases hprefix_witness",
                "have hcount : "
                + bit_count(
                    "x", "x1", "k", "q", tag="blrr_initial_exact_count"
                ),
                "specialize eisenstein_initial_segment_bit_count_exact q",
                "specialize eisenstein_initial_segment_bit_count_exact x",
                "specialize eisenstein_initial_segment_bit_count_exact x1",
                "specialize eisenstein_initial_segment_bit_count_exact k",
                "apply eisenstein_initial_segment_bit_count_exact",
                "exact hprefix_witness_witness",
                "exact hbound",
                "cases hcount",
                "exists x",
                "exists x1",
                "split",
                "exact hprefix_witness_witness",
                "exact hcount_left",
            ),
            "Every bounded threshold has a beta prefix whose exact sum is the threshold.",
        ),
        spec(
            "prime_legendre_sum_succ",
            "forall p n f e g. "
            f"({recurrence_prime}) -> ({recurrence_valuation}) -> "
            f"({recurrence_old}) -> ({recurrence_new}) -> g = e + f",
            (
                "legendre_sum_zero_extended_prefix",
                "initial_segment_prefix_sum_exists",
                "power_quotient_successor_pointwise_add",
                "beta_sum_pointwise_add",
            ),
            (
                "intro p",
                "intro n",
                "intro f",
                "intro e",
                "intro g",
                "intro hp",
                "intro hvaluation",
                "intro hold",
                "intro hnew",
                "have hvaluation_copy : " + recurrence_valuation,
                "exact hvaluation",
                "cases hvaluation_copy",
                "cases hvaluation_copy_left",
                "have hold_extended : exists b c. "
                f"(({_power_quotient_prefix_terms('p', 'n', 'b', 'c', 'S n', tag='blrr_recurrence_old_extended_prefix')}) /\\ "
                f"({_sum_relation_terms('b', 'c', 'S n', 'e', tag='blrr_recurrence_old_extended_sum')}))",
                "specialize legendre_sum_zero_extended_prefix p",
                "specialize legendre_sum_zero_extended_prefix n",
                "specialize legendre_sum_zero_extended_prefix e",
                "apply legendre_sum_zero_extended_prefix",
                "exact hp",
                "exact hold",
                "cases hold_extended",
                "cases hold_extended_witness",
                "cases hold_extended_witness_witness",
                "cases hnew",
                "cases hnew_witness",
                "cases hnew_witness_witness",
                "have hbits : exists z v. "
                f"(({_successor_prefix('f', 'z', 'v', 'n', tag='blrr_recurrence_bits_prefix')}) /\\ "
                f"({_sum_relation_terms('z', 'v', 'S n', 'f', tag='blrr_recurrence_bits_sum')}))",
                "specialize initial_segment_prefix_sum_exists f",
                "specialize initial_segment_prefix_sum_exists (S n)",
                "apply initial_segment_prefix_sum_exists",
                "exact hvaluation_copy_left_left",
                "cases hbits",
                "cases hbits_witness",
                "cases hbits_witness_witness",
                "have hpointwise : forall i a bit s. "
                f"({_lt('i', 'S n', tag='blrr_recurrence_pointwise_bound')}) -> "
                f"({beta_at('x', 'x1', 'i', 'a', tag='blrr_recurrence_pointwise_old')}) -> "
                f"({beta_at('x4', 'x5', 'i', 'bit', tag='blrr_recurrence_pointwise_bit')}) -> "
                f"({beta_at('x2', 'x3', 'i', 's', tag='blrr_recurrence_pointwise_new')}) -> "
                "s = a + bit",
                "specialize power_quotient_successor_pointwise_add p",
                "specialize power_quotient_successor_pointwise_add n",
                "specialize power_quotient_successor_pointwise_add f",
                "specialize power_quotient_successor_pointwise_add x",
                "specialize power_quotient_successor_pointwise_add x1",
                "specialize power_quotient_successor_pointwise_add x2",
                "specialize power_quotient_successor_pointwise_add x3",
                "specialize power_quotient_successor_pointwise_add x4",
                "specialize power_quotient_successor_pointwise_add x5",
                "apply power_quotient_successor_pointwise_add",
                "exact hp",
                "exact hvaluation",
                "exact hold_extended_witness_witness_left",
                "exact hnew_witness_witness_left",
                "exact hbits_witness_witness_left",
                "symm",
                "specialize beta_sum_pointwise_add x",
                "specialize beta_sum_pointwise_add x1",
                "specialize beta_sum_pointwise_add x4",
                "specialize beta_sum_pointwise_add x5",
                "specialize beta_sum_pointwise_add x2",
                "specialize beta_sum_pointwise_add x3",
                "specialize beta_sum_pointwise_add (S n)",
                "specialize beta_sum_pointwise_add e",
                "specialize beta_sum_pointwise_add f",
                "specialize beta_sum_pointwise_add g",
                "apply beta_sum_pointwise_add",
                "exact hold_extended_witness_witness_right",
                "exact hbits_witness_witness_right",
                "exact hnew_witness_witness_right",
                "exact hpointwise",
            ),
            "Prime Legendre sums satisfy the exact constructive successor recurrence.",
        ),
    )


__all__ = ["make_bertrand_legendre_recurrence_candidate_theorems"]
