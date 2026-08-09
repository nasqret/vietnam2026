"""Constructive pointwise infrastructure for Legendre's recurrence.

The five rows in this module isolate the arithmetic heart of

``L_p(n+1) = L_p(n) + v_p(n+1)``.

All displayed predicates are authoring notation only.  Division with
remainder, powers, bounded valuations, beta decoding, quotient prefixes, and
threshold prefixes are fully expanded into the unchanged first-order Peano
language before parsing.  The proofs use the constructive carry/no-carry
split of a successor division; they use neither choice nor classical logic.

This module is deliberately unregistered.  Enrollment requires a separate
review of its exact statements, dependency-curried bodies, empty-context
closures, and mutation evidence.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_legendre_sum_candidate import (
    _power_quotient_prefix_terms,
    power_quotient_prefix,
)
from .bertrand_power_valuation_candidate import (
    _power_divides_terms,
    _power_terms,
    power_valuation,
)
from .eisenstein_initial_segment_count_candidate import (
    _successor_prefix,
    eisenstein_initial_segment_choice,
)
from .fermat_residue_map_candidate import prime
from .finite_fold_surface import beta_at


def _lt(left: str, right: str, *, tag: str) -> str:
    return f"exists blsr_lt_gap_{tag}. blsr_lt_gap_{tag} + S ({left}) = ({right})"


def _le(left: str, right: str, *, tag: str) -> str:
    return f"exists blsr_le_gap_{tag}. blsr_le_gap_{tag} + ({left}) = ({right})"


def _divrem(
    divisor: str,
    value: str,
    quotient: str,
    remainder: str,
    *,
    tag: str,
) -> str:
    return (
        f"(({value}) = ({divisor}) * ({quotient}) + ({remainder}) /\\ "
        f"{_lt(remainder, divisor, tag=f'{tag}_bound')})"
    )


def _power_valuation_terms(
    base: str,
    value: str,
    exponent: str,
    *,
    tag: str,
) -> str:
    """Mirror ``PowerVal`` for the one module-owned compound value ``S n``."""

    candidate = f"blsr_candidate_{tag}"
    return (
        f"((({_le(exponent, value, tag=f'{tag}_exponent_bound')}) /\\ "
        f"({_power_divides_terms(base, exponent, value, tag=f'{tag}_selected')})) /\\ "
        f"forall {candidate}. ({_le(candidate, value, tag=f'{tag}_candidate_bound')}) -> "
        f"({_power_divides_terms(base, candidate, value, tag=f'{tag}_candidate')}) -> "
        f"({_le(candidate, exponent, tag=f'{tag}_maximal')}))"
    )


def make_bertrand_legendre_successor_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the first dependency-small Legendre-successor microtranche."""

    old_division = _divrem("d", "n", "q", "r", tag="successor_cases_old")
    new_division = _divrem("d", "S n", "z", "s", tag="successor_cases_new")
    no_carry_bound = _lt("S r", "d", tag="successor_cases_no_carry")

    bit_old_division = _divrem("d", "n", "q", "r", tag="quotient_bit_old")
    bit_new_division = _divrem("d", "S n", "z", "s", tag="quotient_bit_new")
    multiple = "exists k. S n = d * k"

    prime_p = prime("p", tag="legendre_successor_prime")
    valuation = power_valuation(
        "p", "a", "f", tag="legendre_successor_threshold_valuation"
    )
    exponent_bound = _le(
        "S i", "f", tag="legendre_successor_threshold_inside"
    )
    exponent_outside = _lt(
        "f", "S i", tag="legendre_successor_threshold_outside"
    )
    candidate_divides = _power_divides_terms(
        "p", "S i", "a", tag="legendre_successor_threshold_divides"
    )

    decoded_prefix = power_quotient_prefix(
        "p", "n", "b", "c", "l", tag="legendre_successor_projection"
    )
    decoded_bound = _lt("i", "l", tag="legendre_successor_projection_index")
    decoded_entry = beta_at(
        "b", "c", "i", "q", tag="legendre_successor_projection_entry"
    )
    decoded_power = _power_terms(
        "p", "S i", "D", tag="legendre_successor_projection_power"
    )
    decoded_division = _divrem(
        "D", "n", "q", "r", tag="legendre_successor_projection_division"
    )

    old_prefix = _power_quotient_prefix_terms(
        "p", "n", "b", "c", "S n", tag="legendre_successor_pointwise_old"
    )
    new_prefix = _power_quotient_prefix_terms(
        "p", "S n", "d", "e", "S n", tag="legendre_successor_pointwise_new"
    )
    threshold_prefix = _successor_prefix(
        "f", "z", "v", "n", tag="legendre_successor_pointwise_threshold"
    )
    pointwise_valuation = _power_valuation_terms(
        "p", "S n", "f", tag="legendre_successor_pointwise_valuation"
    )
    pointwise_bound = _lt(
        "i", "S n", tag="legendre_successor_pointwise_index"
    )
    old_entry = beta_at(
        "b", "c", "i", "a", tag="legendre_successor_pointwise_old_entry"
    )
    bit_entry = beta_at(
        "z", "v", "i", "bit", tag="legendre_successor_pointwise_bit_entry"
    )
    new_entry = beta_at(
        "d", "e", "i", "s", tag="legendre_successor_pointwise_new_entry"
    )

    return (
        spec(
            "division_remainder_successor_cases",
            "forall d n q r z s. "
            f"({old_division}) -> ({new_division}) -> "
            f"((S r = d /\\ (z = S q /\\ s = 0)) \\/ "
            f"(({no_carry_bound}) /\\ (z = q /\\ s = S r)))",
            ("le_eq_or_lt", "division_remainder_unique"),
            (
                "intro d",
                "intro n",
                "intro q",
                "intro r",
                "intro z",
                "intro s",
                "intro hold",
                "intro hnew",
                "cases hold",
                "cases hnew",
                "have hsplit : S r = d \/ " + no_carry_bound,
                "specialize le_eq_or_lt (S r)",
                "specialize le_eq_or_lt d",
                "apply le_eq_or_lt",
                "exact hold_right",
                "cases hsplit",
                "left",
                "split",
                "exact hsplit_left",
                "have hequation : S n = d * S q + 0",
                "trans S (d * q + r)",
                "congr",
                "exact hold_left",
                "trans d * q + S r",
                "symm",
                "apply PA4",
                "rewrite hsplit_left",
                "rewrite PA3",
                "symm",
                "apply PA6",
                "have hbound : " + _lt("0", "d", tag="successor_cases_carry_zero"),
                "exists r",
                "rewrite PA4",
                "rewrite PA3",
                "exact hsplit_left",
                "have hunique : z = S q /\\ s = 0",
                "specialize division_remainder_unique d",
                "specialize division_remainder_unique (S n)",
                "specialize division_remainder_unique z",
                "specialize division_remainder_unique s",
                "specialize division_remainder_unique (S q)",
                "specialize division_remainder_unique 0",
                "apply division_remainder_unique",
                "exact hnew_left",
                "exact hnew_right",
                "exact hequation",
                "exact hbound",
                "exact hunique",
                "right",
                "split",
                "exact hsplit_right",
                "have hequation : S n = d * q + S r",
                "trans S (d * q + r)",
                "congr",
                "exact hold_left",
                "symm",
                "apply PA4",
                "have hunique : z = q /\\ s = S r",
                "specialize division_remainder_unique d",
                "specialize division_remainder_unique (S n)",
                "specialize division_remainder_unique z",
                "specialize division_remainder_unique s",
                "specialize division_remainder_unique q",
                "specialize division_remainder_unique (S r)",
                "apply division_remainder_unique",
                "exact hnew_left",
                "exact hnew_right",
                "exact hequation",
                "exact hsplit_right",
                "exact hunique",
            ),
            "Successor division has exactly the carry and no-carry quotient cases.",
        ),
        spec(
            "division_successor_quotient_by_bit",
            "forall d n q r z s bit. "
            f"({bit_old_division}) -> ({bit_new_division}) -> "
            f"((bit = 1 /\\ ({multiple})) \\/ "
            f"(bit = 0 /\\ ~({multiple}))) -> z = q + bit",
            (
                "division_remainder_successor_cases",
                "add_eq_zero_right",
                "succ_ne_zero",
                "multiple_has_zero_remainder",
                "division_remainder_unique",
                "zero_remainder_implies_multiple",
            ),
            (
                "intro d",
                "intro n",
                "intro q",
                "intro r",
                "intro z",
                "intro s",
                "intro bit",
                "intro hold",
                "intro hnew",
                "intro hbit",
                "have hcases : ((S r = d /\\ (z = S q /\\ s = 0)) \\/ "
                f"(({_lt('S r', 'd', tag='quotient_bit_cases_no_carry')}) /\\ "
                "(z = q /\\ s = S r)))",
                "specialize division_remainder_successor_cases d",
                "specialize division_remainder_successor_cases n",
                "specialize division_remainder_successor_cases q",
                "specialize division_remainder_successor_cases r",
                "specialize division_remainder_successor_cases z",
                "specialize division_remainder_successor_cases s",
                "apply division_remainder_successor_cases",
                "exact hold",
                "exact hnew",
                "cases hbit",
                "cases hbit_left",
                "cases hcases",
                "cases hcases_left",
                "cases hcases_left_right",
                "rewrite hbit_left_left",
                "rewrite hcases_left_right_left",
                "rewrite PA4",
                "rewrite PA3",
                "refl",
                "cases hcases_right",
                "cases hcases_right_right",
                "have hd0 : ~(d = 0)",
                "intro hd",
                "cases hold",
                "cases hold_right",
                "rewrite hd at hold_right_witness",
                "have hsr0 : S r = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S r)",
                "apply add_eq_zero_right",
                "exact hold_right_witness",
                "specialize succ_ne_zero r",
                "apply succ_ne_zero",
                "exact hsr0",
                "have hzero : exists q0 r0. ((S n = d * q0 + r0 /\\ r0 = 0) /\\ "
                "exists gap. gap + S r0 = d)",
                "specialize multiple_has_zero_remainder d",
                "specialize multiple_has_zero_remainder (S n)",
                "apply multiple_has_zero_remainder",
                "exact hd0",
                "exact hbit_left_right",
                "cases hzero",
                "cases hzero_witness",
                "cases hzero_witness_witness",
                "cases hzero_witness_witness_left",
                "have hunique : z = x /\\ s = x1",
                "cases hnew",
                "specialize division_remainder_unique d",
                "specialize division_remainder_unique (S n)",
                "specialize division_remainder_unique z",
                "specialize division_remainder_unique s",
                "specialize division_remainder_unique x",
                "specialize division_remainder_unique x1",
                "apply division_remainder_unique",
                "exact hnew_left",
                "exact hnew_right",
                "exact hzero_witness_witness_left_left",
                "exact hzero_witness_witness_right",
                "cases hunique",
                "have hs0 : s = 0",
                "trans x1",
                "exact hunique_right",
                "exact hzero_witness_witness_left_right",
                "exfalso",
                "specialize succ_ne_zero r",
                "apply succ_ne_zero",
                "trans s",
                "symm",
                "exact hcases_right_right_right",
                "exact hs0",
                "cases hbit_right",
                "cases hcases",
                "cases hcases_left",
                "cases hcases_left_right",
                "exfalso",
                "apply hbit_right_right",
                "cases hnew",
                "rewrite hcases_left_right_right at hnew_left",
                "specialize zero_remainder_implies_multiple d",
                "specialize zero_remainder_implies_multiple (S n)",
                "specialize zero_remainder_implies_multiple z",
                "apply zero_remainder_implies_multiple",
                "exact hnew_left",
                "cases hcases_right",
                "cases hcases_right_right",
                "rewrite hbit_right_left",
                "rewrite hcases_right_right_left",
                "rewrite PA3",
                "refl",
            ),
            "A divisibility bit is exactly the successor quotient increment.",
        ),
        spec(
            "valuation_threshold_bit_decides_power_divides",
            "forall p a f i bit. "
            f"({prime_p}) -> ~(a = 0) -> ({valuation}) -> "
            f"((bit = 1 /\\ ({exponent_bound})) \\/ "
            f"(bit = 0 /\\ ({exponent_outside}))) -> "
            f"((bit = 1 /\\ ({candidate_divides})) \\/ "
            f"(bit = 0 /\\ ~({candidate_divides})))",
            (
                "power_divides_of_exponent_le_valuation",
                "prime_power_divides_exponent_le_valuation",
                "lt_not_le",
            ),
            (
                "intro p",
                "intro a",
                "intro f",
                "intro i",
                "intro bit",
                "intro hp",
                "intro ha",
                "intro hvaluation",
                "intro hchoice",
                "cases hchoice",
                "cases hchoice_left",
                "left",
                "split",
                "exact hchoice_left_left",
                "specialize power_divides_of_exponent_le_valuation p",
                "specialize power_divides_of_exponent_le_valuation a",
                "specialize power_divides_of_exponent_le_valuation f",
                "specialize power_divides_of_exponent_le_valuation (S i)",
                "apply power_divides_of_exponent_le_valuation",
                "exact hvaluation",
                "exact hchoice_left_right",
                "cases hchoice_right",
                "right",
                "split",
                "exact hchoice_right_left",
                "intro hdivides",
                "have hbound : "
                + _le("S i", "f", tag="legendre_successor_threshold_contradiction"),
                "specialize prime_power_divides_exponent_le_valuation p",
                "specialize prime_power_divides_exponent_le_valuation a",
                "specialize prime_power_divides_exponent_le_valuation f",
                "specialize prime_power_divides_exponent_le_valuation (S i)",
                "apply prime_power_divides_exponent_le_valuation",
                "exact hp",
                "exact ha",
                "exact hvaluation",
                "exact hdivides",
                "specialize lt_not_le f",
                "specialize lt_not_le (S i)",
                "apply lt_not_le",
                "exact hchoice_right_right",
                "exact hbound",
            ),
            "A valuation threshold bit constructively decides the corresponding power divisor.",
        ),
        spec(
            "power_quotient_prefix_decoded_divrem",
            "forall p n b c l i q. "
            f"({decoded_prefix}) -> ({decoded_bound}) -> ({decoded_entry}) -> "
            f"exists D r. (({decoded_power}) /\\ ({decoded_division}))",
            ("beta_at_unique",),
            (
                "intro p",
                "intro n",
                "intro b",
                "intro c",
                "intro l",
                "intro i",
                "intro q",
                "intro hprefix",
                "intro hi",
                "intro hq",
                "have hdata : exists D stored r. "
                f"(({_power_terms('p', 'S i', 'D', tag='legendre_successor_projection_stored_power')}) /\\ "
                f"(({beta_at('b', 'c', 'i', 'stored', tag='legendre_successor_projection_stored_entry')}) /\\ "
                f"({_divrem('D', 'n', 'stored', 'r', tag='legendre_successor_projection_stored_division')})))",
                "specialize hprefix i",
                "apply hprefix",
                "exact hi",
                "cases hdata",
                "cases hdata_witness",
                "cases hdata_witness_witness",
                "cases hdata_witness_witness_witness",
                "cases hdata_witness_witness_witness_right",
                "have hstored : x1 = q",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique i",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique q",
                "apply beta_at_unique",
                "exact hdata_witness_witness_witness_right_left",
                "exact hq",
                "exists x",
                "exists x2",
                "split",
                "exact hdata_witness_witness_witness_left",
                "rewrite <- hstored",
                "exact hdata_witness_witness_witness_right_right",
            ),
            "A decoded quotient-prefix entry exposes its power and canonical division data.",
        ),
        spec(
            "power_quotient_successor_pointwise_add",
            "forall p n f b c d e z v. "
            f"({prime_p}) -> ({pointwise_valuation}) -> "
            f"({old_prefix}) -> ({new_prefix}) -> ({threshold_prefix}) -> "
            "forall i a bit s. "
            f"({pointwise_bound}) -> ({old_entry}) -> ({bit_entry}) -> "
            f"({new_entry}) -> s = a + bit",
            (
                "power_quotient_prefix_decoded_divrem",
                "eisenstein_initial_segment_decoded_choice",
                "valuation_threshold_bit_decides_power_divides",
                "pow_functional",
                "division_successor_quotient_by_bit",
                "succ_ne_zero",
            ),
            (
                "intro p",
                "intro n",
                "intro f",
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "intro z",
                "intro v",
                "intro hp",
                "intro hvaluation",
                "intro holdprefix",
                "intro hnewprefix",
                "intro hthreshold",
                "intro i",
                "intro a",
                "intro bit",
                "intro s",
                "intro hi",
                "intro ha",
                "intro hbit",
                "intro hs",
                "have hold : exists D r. "
                f"(({_power_terms('p', 'S i', 'D', tag='legendre_successor_pointwise_old_power')}) /\\ "
                f"({_divrem('D', 'n', 'a', 'r', tag='legendre_successor_pointwise_old_division')}))",
                "specialize power_quotient_prefix_decoded_divrem p",
                "specialize power_quotient_prefix_decoded_divrem n",
                "specialize power_quotient_prefix_decoded_divrem b",
                "specialize power_quotient_prefix_decoded_divrem c",
                "specialize power_quotient_prefix_decoded_divrem (S n)",
                "specialize power_quotient_prefix_decoded_divrem i",
                "specialize power_quotient_prefix_decoded_divrem a",
                "apply power_quotient_prefix_decoded_divrem",
                "exact holdprefix",
                "exact hi",
                "exact ha",
                "have hnew : exists E t. "
                f"(({_power_terms('p', 'S i', 'E', tag='legendre_successor_pointwise_new_power')}) /\\ "
                f"({_divrem('E', 'S n', 's', 't', tag='legendre_successor_pointwise_new_division')}))",
                "specialize power_quotient_prefix_decoded_divrem p",
                "specialize power_quotient_prefix_decoded_divrem (S n)",
                "specialize power_quotient_prefix_decoded_divrem d",
                "specialize power_quotient_prefix_decoded_divrem e",
                "specialize power_quotient_prefix_decoded_divrem (S n)",
                "specialize power_quotient_prefix_decoded_divrem i",
                "specialize power_quotient_prefix_decoded_divrem s",
                "apply power_quotient_prefix_decoded_divrem",
                "exact hnewprefix",
                "exact hi",
                "exact hs",
                "cases hold",
                "cases hold_witness",
                "cases hold_witness_witness",
                "cases hnew",
                "cases hnew_witness",
                "cases hnew_witness_witness",
                "have hpower : x = x2",
                "specialize pow_functional p",
                "specialize pow_functional (S i)",
                "specialize pow_functional x",
                "specialize pow_functional x2",
                "apply pow_functional",
                "exact hold_witness_witness_left",
                "exact hnew_witness_witness_left",
                "rewrite <- hpower at hnew_witness_witness_right",
                "rewrite <- hpower at hnew_witness_witness_right",
                "have hchoice : "
                + eisenstein_initial_segment_choice(
                    "f", "i", "bit", tag="legendre_successor_pointwise_choice"
                ),
                "specialize eisenstein_initial_segment_decoded_choice f",
                "specialize eisenstein_initial_segment_decoded_choice z",
                "specialize eisenstein_initial_segment_decoded_choice v",
                "specialize eisenstein_initial_segment_decoded_choice (S n)",
                "specialize eisenstein_initial_segment_decoded_choice i",
                "specialize eisenstein_initial_segment_decoded_choice bit",
                "apply eisenstein_initial_segment_decoded_choice",
                "exact hthreshold",
                "exact hi",
                "exact hbit",
                "have hdecision : ((bit = 1 /\\ "
                + _power_divides_terms(
                    "p", "S i", "S n", tag="legendre_successor_pointwise_decision_left"
                )
                + ") \/ (bit = 0 /\\ ~("
                + _power_divides_terms(
                    "p", "S i", "S n", tag="legendre_successor_pointwise_decision_right"
                )
                + ")))",
                "specialize valuation_threshold_bit_decides_power_divides p",
                "specialize valuation_threshold_bit_decides_power_divides (S n)",
                "specialize valuation_threshold_bit_decides_power_divides f",
                "specialize valuation_threshold_bit_decides_power_divides i",
                "specialize valuation_threshold_bit_decides_power_divides bit",
                "apply valuation_threshold_bit_decides_power_divides",
                "exact hp",
                "specialize succ_ne_zero n",
                "exact succ_ne_zero",
                "exact hvaluation",
                "exact hchoice",
                "have hmultiple_bit : ((bit = 1 /\\ exists k. S n = x * k) \/ "
                "(bit = 0 /\\ ~(exists k. S n = x * k)))",
                "cases hdecision",
                "cases hdecision_left",
                "left",
                "split",
                "exact hdecision_left_left",
                "cases hdecision_left_right",
                "cases hdecision_left_right_witness",
                "cases hdecision_left_right_witness_right",
                "have hresult : x4 = x",
                "specialize pow_functional p",
                "specialize pow_functional (S i)",
                "specialize pow_functional x4",
                "specialize pow_functional x",
                "apply pow_functional",
                "exact hdecision_left_right_witness_left",
                "exact hold_witness_witness_left",
                "cases hdecision_left_right_witness_right",
                "exists x5",
                "rewrite <- hresult",
                "exact hdecision_left_right_witness_right_witness",
                "cases hdecision_right",
                "right",
                "split",
                "exact hdecision_right_left",
                "intro hmultiple",
                "apply hdecision_right_right",
                "exists x",
                "split",
                "exact hold_witness_witness_left",
                "exact hmultiple",
                "specialize division_successor_quotient_by_bit x",
                "specialize division_successor_quotient_by_bit n",
                "specialize division_successor_quotient_by_bit a",
                "specialize division_successor_quotient_by_bit x1",
                "specialize division_successor_quotient_by_bit s",
                "specialize division_successor_quotient_by_bit x3",
                "specialize division_successor_quotient_by_bit bit",
                "apply division_successor_quotient_by_bit",
                "exact hold_witness_witness_right",
                "exact hnew_witness_witness_right",
                "exact hmultiple_bit",
            ),
            "Successor prime-power quotients are the old quotients plus their valuation-threshold bits.",
        ),
    )


__all__ = ["make_bertrand_legendre_successor_candidate_theorems"]
