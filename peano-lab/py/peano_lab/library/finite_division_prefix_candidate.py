"""Construct beta-coded quotient and remainder prefixes.

Eisenstein's floor sums require finite quotient sequences, but the native PA
language has neither division functions nor lists.  This isolated candidate
uses the checked relational division theorem and ordinary beta-prefix
extension to encode, for every source position, a quotient and a strictly
bounded remainder.

Every readable relation expands to the unchanged first-order PA language.
The candidates are intentionally unregistered pending recursive WMI review.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at
from .gauss_signed_prefix_candidate import _strictly_below_term


def division_prefix(
    modulus: str,
    source_code: str,
    source_scale: str,
    quotient_code: str,
    quotient_scale: str,
    remainder_code: str,
    remainder_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand a beta-coded quotient/remainder trace over a finite prefix."""

    variables = (
        modulus,
        source_code,
        source_scale,
        quotient_code,
        quotient_scale,
        remainder_code,
        remainder_scale,
        length,
    )
    index = f"fdp_index_{tag}"
    value = f"fdp_value_{tag}"
    quotient = f"fdp_quotient_{tag}"
    remainder = f"fdp_remainder_{tag}"
    owned = variables + (index, value, quotient, remainder)
    index_bound = _strictly_below_term(
        index, length, tag=f"{tag}_index_bound", variables=owned
    )
    remainder_bound = _strictly_below_term(
        remainder, modulus, tag=f"{tag}_remainder_bound", variables=owned
    )
    source = beta_at(
        source_code, source_scale, index, value, tag=f"fdp_{tag}_source"
    )
    quotient_entry = beta_at(
        quotient_code,
        quotient_scale,
        index,
        quotient,
        tag=f"fdp_{tag}_quotient_entry",
    )
    remainder_entry = beta_at(
        remainder_code,
        remainder_scale,
        index,
        remainder,
        tag=f"fdp_{tag}_remainder_entry",
    )
    return (
        f"forall {index}. ({index_bound}) -> exists {value} {quotient} "
        f"{remainder}. ({source}) /\\ (({quotient_entry}) /\\ "
        f"(({remainder_entry}) /\\ ({value} = {modulus} * {quotient} + "
        f"{remainder} /\\ ({remainder_bound}))))"
    )


def make_finite_division_prefix_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build one-step extension and full-prefix existence candidates."""

    prefix = division_prefix(
        "p", "b", "c", "qb", "qc", "rb", "rc", "l", tag="before"
    )
    successor_prefix = division_prefix(
        "p", "b", "c", "z", "d", "u", "v", "S l", tag="after"
    )

    source_last = beta_at("b", "c", "l", "x", tag="fdp_choice_source")
    remainder_last_bound = _strictly_below_term(
        "r",
        "p",
        tag="fdp_choice_remainder_bound",
        variables=("p", "b", "c", "qb", "qc", "rb", "rc", "l", "x", "q", "r"),
    )
    choice = (
        f"exists x q r. ({source_last}) /\\ "
        f"(x = p * q + r /\\ ({remainder_last_bound}))"
    )

    quotient_extension_old_source = beta_at(
        "qb", "qc", "i", "q0", tag="fdp_quotient_extension_old_source"
    )
    quotient_old_bound = _strictly_below_term(
        "i",
        "l",
        tag="fdp_quotient_extension_old_bound",
        variables=("p", "b", "c", "qb", "qc", "rb", "rc", "l", "i", "q0"),
    )
    quotient_extension = (
        f"exists z d. ({beta_at('z', 'd', 'l', 'x1', tag='fdp_quotient_extension_last')}) /\\ "
        f"forall i q0. ({quotient_old_bound}) -> "
        f"({quotient_extension_old_source}) -> "
        f"({beta_at('z', 'd', 'i', 'q0', tag='fdp_quotient_extension_old_target_symbolic')})"
    )
    remainder_old_bound = _strictly_below_term(
        "i",
        "l",
        tag="fdp_remainder_extension_old_bound",
        variables=("p", "b", "c", "qb", "qc", "rb", "rc", "l", "i", "r0"),
    )
    remainder_extension = (
        f"exists u v. ({beta_at('u', 'v', 'l', 'x2', tag='fdp_remainder_extension_last')}) /\\ "
        f"forall i r0. ({remainder_old_bound}) -> "
        f"({beta_at('rb', 'rc', 'i', 'r0', tag='fdp_remainder_extension_old_source')}) -> "
        f"({beta_at('u', 'v', 'i', 'r0', tag='fdp_remainder_extension_old_target')})"
    )

    previous_entry = (
        "exists x q r. "
        f"({beta_at('b', 'c', 'i', 'x', tag='fdp_previous_source')}) /\\ "
        f"(({beta_at('qb', 'qc', 'i', 'q', tag='fdp_previous_quotient')}) /\\ "
        f"(({beta_at('rb', 'rc', 'i', 'r', tag='fdp_previous_remainder')}) /\\ "
        f"(x = p * q + r /\\ "
        f"({_strictly_below_term('r', 'p', tag='fdp_previous_remainder_bound', variables=('p', 'b', 'c', 'qb', 'qc', 'rb', 'rc', 'l', 'i', 'x', 'q', 'r'))}))))"
    )

    existence_result = (
        "exists qb qc rb rc. "
        f"({division_prefix('p', 'b', 'c', 'qb', 'qc', 'rb', 'rc', 'l', tag='exists_result')})"
    )
    previous_existence = (
        "exists qb qc rb rc. "
        f"({division_prefix('p', 'b', 'c', 'qb', 'qc', 'rb', 'rc', 'l', tag='exists_previous')})"
    )
    next_existence = (
        "exists qb qc rb rc. "
        f"({division_prefix('p', 'b', 'c', 'qb', 'qc', 'rb', 'rc', 'S l', tag='exists_next')})"
    )
    decoded_last = beta_at("b", "c", "l", "x", tag="fdp_exists_last_source")
    last_remainder_bound = _strictly_below_term(
        "r",
        "p",
        tag="fdp_exists_last_remainder_bound",
        variables=("p", "b", "c", "l", "x", "q", "r"),
    )
    last_choice = (
        f"exists x q r. ({beta_at('b', 'c', 'l', 'x', tag='fdp_choice_source')}) /\\ "
        f"(x = p * q + r /\\ "
        f"({_strictly_below_term('r', 'p', tag='fdp_choice_remainder_bound', variables=('p', 'b', 'c', 'l', 'x', 'q', 'r'))}))"
    )

    return (
        spec(
            "beta_division_prefix_extend",
            "forall p b c qb qc rb rc l. "
            f"({prefix}) -> ({choice}) -> exists z d u v. ({successor_prefix})",
            ("beta_prefix_extend", "finite_lt_succ_eq_or_lt"),
            (
                "intro p",
                "intro b",
                "intro c",
                "intro qb",
                "intro qc",
                "intro rb",
                "intro rc",
                "intro l",
                "intro hprefix",
                "intro hchoice",
                "cases hchoice",
                "cases hchoice_witness",
                "cases hchoice_witness_witness",
                "cases hchoice_witness_witness_witness",
                "cases hchoice_witness_witness_witness_right",
                f"have hqextend : {quotient_extension}",
                "specialize beta_prefix_extend l",
                "specialize beta_prefix_extend qb",
                "specialize beta_prefix_extend qc",
                "specialize beta_prefix_extend x1",
                "exact beta_prefix_extend",
                "cases hqextend",
                "cases hqextend_witness",
                "cases hqextend_witness_witness",
                f"have hrextend : {remainder_extension}",
                "specialize beta_prefix_extend l",
                "specialize beta_prefix_extend rb",
                "specialize beta_prefix_extend rc",
                "specialize beta_prefix_extend x2",
                "exact beta_prefix_extend",
                "cases hrextend",
                "cases hrextend_witness",
                "cases hrextend_witness_witness",
                "exists x3",
                "exists x4",
                "exists x5",
                "exists x6",
                "intro i",
                "intro hi",
                "have hsplit : i = l \/ exists gap. gap + S i = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                "cases hsplit",
                "exists x",
                "exists x1",
                "exists x2",
                "split",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact hchoice_witness_witness_witness_left",
                "split",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact hqextend_witness_witness_left",
                "split",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact hrextend_witness_witness_left",
                "split",
                "exact hchoice_witness_witness_witness_right_left",
                "exact hchoice_witness_witness_witness_right_right",
                f"have hold : {previous_entry}",
                "specialize hprefix i",
                "apply hprefix",
                "exact hsplit_right",
                "cases hold",
                "cases hold_witness",
                "cases hold_witness_witness",
                "cases hold_witness_witness_witness",
                "cases hold_witness_witness_witness_right",
                "cases hold_witness_witness_witness_right_right",
                "cases hold_witness_witness_witness_right_right_right",
                "exists x7",
                "exists x8",
                "exists x9",
                "split",
                "exact hold_witness_witness_witness_left",
                "split",
                "specialize hqextend_witness_witness_right i",
                "specialize hqextend_witness_witness_right x8",
                "apply hqextend_witness_witness_right",
                "exact hsplit_right",
                "exact hold_witness_witness_witness_right_left",
                "split",
                "specialize hrextend_witness_witness_right i",
                "specialize hrextend_witness_witness_right x9",
                "apply hrextend_witness_witness_right",
                "exact hsplit_right",
                "exact hold_witness_witness_witness_right_right_left",
                "split",
                "exact hold_witness_witness_witness_right_right_right_left",
                "exact hold_witness_witness_witness_right_right_right_right",
            ),
            "Append one quotient/remainder pair while preserving the decoded prefix.",
        ),
        spec(
            "beta_division_prefix_exists",
            "forall p b c l. ~(p = 0) -> " + existence_result,
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "beta_at_exists",
                "division_remainder_exists",
                "beta_division_prefix_extend",
            ),
            (
                "intro p",
                "intro b",
                "intro c",
                "induction l",
                "intro hp0",
                "exists 0",
                "exists 0",
                "exists 0",
                "exists 0",
                "intro i",
                "intro hi",
                "exfalso",
                "cases hi",
                "have hsi : S i = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S i)",
                "apply add_eq_zero_right",
                "exact hi_witness",
                "specialize succ_ne_zero i",
                "apply succ_ne_zero",
                "exact hsi",
                "intro hp0",
                f"have hprevious : {previous_existence}",
                "apply IH",
                "exact hp0",
                "cases hprevious",
                "cases hprevious_witness",
                "cases hprevious_witness_witness",
                "cases hprevious_witness_witness_witness",
                f"have hdecoded : exists x. ({decoded_last})",
                "specialize beta_at_exists b",
                "specialize beta_at_exists c",
                "specialize beta_at_exists l",
                "exact beta_at_exists",
                "cases hdecoded",
                "have hdivision : exists q r. x4 = p * q + r /\\ "
                f"({last_remainder_bound})",
                "specialize division_remainder_exists p",
                "specialize division_remainder_exists x4",
                "apply division_remainder_exists",
                "exact hp0",
                "cases hdivision",
                "cases hdivision_witness",
                f"have hchoice : {last_choice}",
                "exists x4",
                "exists x5",
                "exists x6",
                "split",
                "exact hdecoded_witness",
                "exact hdivision_witness_witness",
                f"have hnext : {next_existence}",
                "specialize beta_division_prefix_extend p",
                "specialize beta_division_prefix_extend b",
                "specialize beta_division_prefix_extend c",
                "specialize beta_division_prefix_extend x",
                "specialize beta_division_prefix_extend x1",
                "specialize beta_division_prefix_extend x2",
                "specialize beta_division_prefix_extend x3",
                "specialize beta_division_prefix_extend l",
                "apply beta_division_prefix_extend",
                "exact hprevious_witness_witness_witness_witness",
                "exact hchoice",
                "exact hnext",
            ),
            "Every finite beta source prefix has beta-coded quotients and bounded remainders for a nonzero modulus.",
        ),
    )


__all__ = [
    "division_prefix",
    "make_finite_division_prefix_candidate_theorems",
]
