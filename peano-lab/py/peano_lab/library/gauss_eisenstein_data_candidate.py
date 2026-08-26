"""Construct the complete native Gauss--Eisenstein reciprocity data.

The first candidate packages one orientation of Gauss's lemma together with
the exact Eisenstein quotient prefix.  Its public witness keeps only the
division codes, the sign count, and the quotient sum; the canonical half
range and the signed/magnitude codes are constructed and eliminated inside
the proof.

The second candidate applies that constructor in both prime orientations and
joins the two quotient sums with the exact lattice/Fubini identity.  Its final
contract exposes only ``e, f, Q, U``: the two complete Gauss classifications,
the two modulo-two count/sum congruences, and ``Q + U = h * k``.  All surface
relations expand to unchanged first-order PA.  These candidates are isolated,
unregistered, unadmitted, and intended only for dependency-curried body
replay on the laptop.
"""

from __future__ import annotations

from typing import Any, Callable

from .eisenstein_rectangle_count_candidate import (
    eisenstein_rectangle_row_count_prefix,
)
from .eisenstein_scaled_division_candidate import scaled_successor_prefix
from .finite_division_prefix_candidate import division_prefix
from .finite_fold_surface import bit_count, sum_relation
from .finite_sum_pointwise_mod_candidate import _mod_eq
from .gauss_sign_bridge import _even, _odd
from .gauss_signed_prefix_candidate import (
    half_range,
    not_divides,
    prime,
    signed_half_prefix,
)
from .quadratic_residue_surface import quadratic_residue


def _classification(modulus: str, value: str, count: str, *, tag: str) -> str:
    qres = quadratic_residue(modulus, value, tag=f"{tag}_qres")
    even_count = _even(count, tag=f"{tag}_even")
    odd_count = _odd(count, tag=f"{tag}_odd")
    residue_iff_even = (
        f"((({qres}) -> ({even_count})) /\\ (({even_count}) -> ({qres})))"
    )
    nonresidue_iff_odd = (
        f"((~({qres}) -> ({odd_count})) /\\ (({odd_count}) -> ~({qres})))"
    )
    return f"(({residue_iff_even}) /\\ ({nonresidue_iff_odd}))"


def make_gauss_eisenstein_data_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build one-orientation data and the complete two-prime package."""

    prime_p = prime("p", tag="ged_orientation_prime")
    nondivisor = not_divides("p", "a", tag="ged_orientation_nondivisor")
    odd_a = _odd("a", tag="ged_orientation_odd")
    orientation_scaled = scaled_successor_prefix(
        "a", "tb", "tc", "h", tag="ged_orientation_scaled"
    )
    orientation_division = division_prefix(
        "p", "tb", "tc", "qb", "qc", "rb", "rc", "h",
        tag="ged_orientation_division",
    )
    orientation_sum = sum_relation(
        "qb", "qc", "h", "Q", tag="ged_orientation_sum"
    )
    orientation_classification = _classification(
        "p", "a", "e", tag="ged_orientation_classification"
    )
    orientation_mod = _mod_eq(
        "2", "e", "Q", tag="ged_orientation_count_mod_sum"
    )
    orientation_result = (
        "exists tb tc qb qc rb rc e Q. "
        f"(({orientation_scaled}) /\\ "
        f"(({orientation_division}) /\\ "
        f"(({orientation_sum}) /\\ "
        f"(({orientation_classification}) /\\ ({orientation_mod})))))"
    )

    orientation_script = (
        "intro p", "intro h", "intro a", "intro hpodd", "intro haodd",
        "intro hprime", "intro hnotdiv",
        "have hhalf_exists : exists b c. "
        f"({half_range('b', 'c', 'h', tag='ged_orientation_half_exists')})",
        "specialize beta_range_exists 1", "specialize beta_range_exists h",
        "exact beta_range_exists",
        "cases hhalf_exists", "cases hhalf_exists_witness",
        "have hgauss : exists e. ((exists mb mc sb sc. "
        f"(({signed_half_prefix('p', 'h', 'a', 'x', 'x1', 'mb', 'mc', 'sb', 'sc', 'h', tag='ged_orientation_hidden_signed')}) /\\ "
        f"({bit_count('sb', 'sc', 'h', 'e', tag='ged_orientation_hidden_count')}))) /\\ "
        f"({_classification('p', 'a', 'e', tag='ged_orientation_hidden_classification')}))",
        "specialize arbitrary_gauss_lemma_complete p",
        "specialize arbitrary_gauss_lemma_complete h",
        "specialize arbitrary_gauss_lemma_complete a",
        "specialize arbitrary_gauss_lemma_complete x",
        "specialize arbitrary_gauss_lemma_complete x1",
        "apply arbitrary_gauss_lemma_complete",
        "exact hpodd", "exact hprime", "exact hnotdiv",
        "exact hhalf_exists_witness_witness",
        "cases hgauss", "cases hgauss_witness",
        "cases hgauss_witness_left", "cases hgauss_witness_left_witness",
        "cases hgauss_witness_left_witness_witness",
        "cases hgauss_witness_left_witness_witness_witness",
        "cases hgauss_witness_left_witness_witness_witness_witness",
        "have hquotient : exists tb tc qb qc rb rc Q. "
        f"(({scaled_successor_prefix('a', 'tb', 'tc', 'h', tag='ged_orientation_hidden_scaled')}) /\\ "
        f"(({division_prefix('p', 'tb', 'tc', 'qb', 'qc', 'rb', 'rc', 'h', tag='ged_orientation_hidden_division')}) /\\ "
        f"({sum_relation('qb', 'qc', 'h', 'Q', tag='ged_orientation_hidden_sum')})))",
        "specialize prime_scaled_half_quotient_sum_exists p",
        "specialize prime_scaled_half_quotient_sum_exists h",
        "specialize prime_scaled_half_quotient_sum_exists a",
        "specialize prime_scaled_half_quotient_sum_exists x",
        "specialize prime_scaled_half_quotient_sum_exists x1",
        "apply prime_scaled_half_quotient_sum_exists",
        "exact hpodd", "exact hprime", "exact hhalf_exists_witness_witness",
        "cases hquotient", "cases hquotient_witness",
        "cases hquotient_witness_witness",
        "cases hquotient_witness_witness_witness",
        "cases hquotient_witness_witness_witness_witness",
        "cases hquotient_witness_witness_witness_witness_witness",
        "cases hquotient_witness_witness_witness_witness_witness_witness",
        "cases hquotient_witness_witness_witness_witness_witness_witness_witness",
        "cases hquotient_witness_witness_witness_witness_witness_witness_witness_right",
        f"have hquotient_mod_count : {_mod_eq('2', 'x13', 'x2', tag='ged_orientation_hidden_quotient_mod_count')}",
        "specialize gauss_eisenstein_sign_count_mod_quotient_sum p",
        "specialize gauss_eisenstein_sign_count_mod_quotient_sum h",
        "specialize gauss_eisenstein_sign_count_mod_quotient_sum a",
        "specialize gauss_eisenstein_sign_count_mod_quotient_sum x",
        "specialize gauss_eisenstein_sign_count_mod_quotient_sum x1",
        "specialize gauss_eisenstein_sign_count_mod_quotient_sum x7",
        "specialize gauss_eisenstein_sign_count_mod_quotient_sum x8",
        "specialize gauss_eisenstein_sign_count_mod_quotient_sum x9",
        "specialize gauss_eisenstein_sign_count_mod_quotient_sum x10",
        "specialize gauss_eisenstein_sign_count_mod_quotient_sum x11",
        "specialize gauss_eisenstein_sign_count_mod_quotient_sum x12",
        "specialize gauss_eisenstein_sign_count_mod_quotient_sum x3",
        "specialize gauss_eisenstein_sign_count_mod_quotient_sum x4",
        "specialize gauss_eisenstein_sign_count_mod_quotient_sum x5",
        "specialize gauss_eisenstein_sign_count_mod_quotient_sum x6",
        "specialize gauss_eisenstein_sign_count_mod_quotient_sum x13",
        "specialize gauss_eisenstein_sign_count_mod_quotient_sum x2",
        "apply gauss_eisenstein_sign_count_mod_quotient_sum",
        "exact hpodd", "exact haodd", "exact hprime", "exact hnotdiv",
        "exact hhalf_exists_witness_witness",
        "exact hquotient_witness_witness_witness_witness_witness_witness_witness_left",
        "exact hquotient_witness_witness_witness_witness_witness_witness_witness_right_left",
        "exact hgauss_witness_left_witness_witness_witness_witness_left",
        "exact hgauss_witness_left_witness_witness_witness_witness_right",
        "exact hquotient_witness_witness_witness_witness_witness_witness_witness_right_right",
        f"have hcount_mod_quotient : {_mod_eq('2', 'x2', 'x13', tag='ged_orientation_hidden_count_mod_quotient')}",
        "specialize mod_eq_symm 2", "specialize mod_eq_symm x13",
        "specialize mod_eq_symm x2", "apply mod_eq_symm",
        "exact hquotient_mod_count",
        "exists x7", "exists x8", "exists x9", "exists x10",
        "exists x11", "exists x12", "exists x2", "exists x13",
        "split",
        "exact hquotient_witness_witness_witness_witness_witness_witness_witness_left",
        "split",
        "exact hquotient_witness_witness_witness_witness_witness_witness_witness_right_left",
        "split",
        "exact hquotient_witness_witness_witness_witness_witness_witness_witness_right_right",
        "split", "exact hgauss_witness_right", "exact hcount_mod_quotient",
    )

    prime_first = prime("p", tag="ged_pair_prime_p")
    prime_second = prime("q", tag="ged_pair_prime_q")
    first_nondivisor = not_divides("p", "q", tag="ged_pair_p_not_q")
    second_nondivisor = not_divides("q", "p", tag="ged_pair_q_not_p")
    first_classification = _classification(
        "p", "q", "e", tag="ged_pair_first_classification"
    )
    second_classification = _classification(
        "q", "p", "f", tag="ged_pair_second_classification"
    )
    first_mod = _mod_eq("2", "e", "Q", tag="ged_pair_first_mod")
    second_mod = _mod_eq("2", "f", "U", tag="ged_pair_second_mod")
    pair_result = (
        "exists e f Q U. "
        f"((({first_classification}) /\\ ({second_classification})) /\\ "
        f"((({first_mod}) /\\ ({second_mod})) /\\ Q + U = h * k))"
    )

    pair_script = (
        "intro p", "intro q", "intro h", "intro k", "intro hpodd",
        "intro hqodd", "intro hp", "intro hq", "intro hpq",
        f"have hmutual : (({first_nondivisor}) /\\ ({second_nondivisor}))",
        "specialize distinct_primes_mutually_nondivisible p",
        "specialize distinct_primes_mutually_nondivisible q",
        "apply distinct_primes_mutually_nondivisible",
        "exact hp", "exact hq", "exact hpq", "cases hmutual",
        f"have hq_odd : {_odd('q', tag='ged_pair_q_odd')}",
        "exists k", "exact hqodd",
        f"have hp_odd : {_odd('p', tag='ged_pair_p_odd')}",
        "exists h", "exact hpodd",
        "have hfirst : exists tb tc qb qc rb rc e Q. "
        f"(({scaled_successor_prefix('q', 'tb', 'tc', 'h', tag='ged_pair_first_scaled')}) /\\ "
        f"(({division_prefix('p', 'tb', 'tc', 'qb', 'qc', 'rb', 'rc', 'h', tag='ged_pair_first_division')}) /\\ "
        f"(({sum_relation('qb', 'qc', 'h', 'Q', tag='ged_pair_first_sum')}) /\\ "
        f"(({_classification('p', 'q', 'e', tag='ged_pair_first_hidden_classification')}) /\\ "
        f"({_mod_eq('2', 'e', 'Q', tag='ged_pair_first_hidden_mod')})))))",
        "specialize odd_prime_gauss_eisenstein_orientation_data_exists p",
        "specialize odd_prime_gauss_eisenstein_orientation_data_exists h",
        "specialize odd_prime_gauss_eisenstein_orientation_data_exists q",
        "apply odd_prime_gauss_eisenstein_orientation_data_exists",
        "exact hpodd", "exact hq_odd", "exact hp", "exact hmutual_left",
        "cases hfirst", "cases hfirst_witness", "cases hfirst_witness_witness",
        "cases hfirst_witness_witness_witness",
        "cases hfirst_witness_witness_witness_witness",
        "cases hfirst_witness_witness_witness_witness_witness",
        "cases hfirst_witness_witness_witness_witness_witness_witness",
        "cases hfirst_witness_witness_witness_witness_witness_witness_witness",
        "cases hfirst_witness_witness_witness_witness_witness_witness_witness_witness",
        "cases hfirst_witness_witness_witness_witness_witness_witness_witness_witness_right",
        "cases hfirst_witness_witness_witness_witness_witness_witness_witness_witness_right_right",
        "cases hfirst_witness_witness_witness_witness_witness_witness_witness_witness_right_right_right",
        "have hsecond : exists tb tc qb qc rb rc e Q. "
        f"(({scaled_successor_prefix('p', 'tb', 'tc', 'k', tag='ged_pair_second_scaled')}) /\\ "
        f"(({division_prefix('q', 'tb', 'tc', 'qb', 'qc', 'rb', 'rc', 'k', tag='ged_pair_second_division')}) /\\ "
        f"(({sum_relation('qb', 'qc', 'k', 'Q', tag='ged_pair_second_sum')}) /\\ "
        f"(({_classification('q', 'p', 'e', tag='ged_pair_second_hidden_classification')}) /\\ "
        f"({_mod_eq('2', 'e', 'Q', tag='ged_pair_second_hidden_mod')})))))",
        "specialize odd_prime_gauss_eisenstein_orientation_data_exists q",
        "specialize odd_prime_gauss_eisenstein_orientation_data_exists k",
        "specialize odd_prime_gauss_eisenstein_orientation_data_exists p",
        "apply odd_prime_gauss_eisenstein_orientation_data_exists",
        "exact hqodd", "exact hp_odd", "exact hq", "exact hmutual_right",
        "cases hsecond", "cases hsecond_witness", "cases hsecond_witness_witness",
        "cases hsecond_witness_witness_witness",
        "cases hsecond_witness_witness_witness_witness",
        "cases hsecond_witness_witness_witness_witness_witness",
        "cases hsecond_witness_witness_witness_witness_witness_witness",
        "cases hsecond_witness_witness_witness_witness_witness_witness_witness",
        "cases hsecond_witness_witness_witness_witness_witness_witness_witness_witness",
        "cases hsecond_witness_witness_witness_witness_witness_witness_witness_witness_right",
        "cases hsecond_witness_witness_witness_witness_witness_witness_witness_witness_right_right",
        "cases hsecond_witness_witness_witness_witness_witness_witness_witness_witness_right_right_right",
        "have hqp : ~(q = p)", "intro hqp_eq", "apply hpq", "symm",
        "exact hqp_eq",
        "have hfirst_rectangle : exists cb cc total. "
        f"(({eisenstein_rectangle_row_count_prefix('p', 'q', 'k', 'cb', 'cc', 'h', tag='ged_pair_first_rectangle')}) /\\ "
        f"({sum_relation('cb', 'cc', 'h', 'total', tag='ged_pair_first_rectangle_sum')}))",
        "specialize distinct_odd_prime_half_rectangle_total_exists p",
        "specialize distinct_odd_prime_half_rectangle_total_exists q",
        "specialize distinct_odd_prime_half_rectangle_total_exists h",
        "specialize distinct_odd_prime_half_rectangle_total_exists k",
        "apply distinct_odd_prime_half_rectangle_total_exists",
        "exact hpodd", "exact hqodd", "exact hp", "exact hq", "exact hpq",
        "cases hfirst_rectangle", "cases hfirst_rectangle_witness",
        "cases hfirst_rectangle_witness_witness",
        "cases hfirst_rectangle_witness_witness_witness",
        "have hsecond_rectangle : exists cb cc total. "
        f"(({eisenstein_rectangle_row_count_prefix('q', 'p', 'h', 'cb', 'cc', 'k', tag='ged_pair_second_rectangle')}) /\\ "
        f"({sum_relation('cb', 'cc', 'k', 'total', tag='ged_pair_second_rectangle_sum')}))",
        "specialize distinct_odd_prime_half_rectangle_total_exists q",
        "specialize distinct_odd_prime_half_rectangle_total_exists p",
        "specialize distinct_odd_prime_half_rectangle_total_exists k",
        "specialize distinct_odd_prime_half_rectangle_total_exists h",
        "apply distinct_odd_prime_half_rectangle_total_exists",
        "exact hqodd", "exact hpodd", "exact hq", "exact hp", "exact hqp",
        "cases hsecond_rectangle", "cases hsecond_rectangle_witness",
        "cases hsecond_rectangle_witness_witness",
        "cases hsecond_rectangle_witness_witness_witness",
        "have hsum_identity : x7 + x15 = h * k",
        "specialize distinct_odd_prime_eisenstein_quotient_sum_identity p",
        "specialize distinct_odd_prime_eisenstein_quotient_sum_identity q",
        "specialize distinct_odd_prime_eisenstein_quotient_sum_identity h",
        "specialize distinct_odd_prime_eisenstein_quotient_sum_identity k",
        "specialize distinct_odd_prime_eisenstein_quotient_sum_identity x",
        "specialize distinct_odd_prime_eisenstein_quotient_sum_identity x1",
        "specialize distinct_odd_prime_eisenstein_quotient_sum_identity x2",
        "specialize distinct_odd_prime_eisenstein_quotient_sum_identity x3",
        "specialize distinct_odd_prime_eisenstein_quotient_sum_identity x4",
        "specialize distinct_odd_prime_eisenstein_quotient_sum_identity x5",
        "specialize distinct_odd_prime_eisenstein_quotient_sum_identity x8",
        "specialize distinct_odd_prime_eisenstein_quotient_sum_identity x9",
        "specialize distinct_odd_prime_eisenstein_quotient_sum_identity x10",
        "specialize distinct_odd_prime_eisenstein_quotient_sum_identity x11",
        "specialize distinct_odd_prime_eisenstein_quotient_sum_identity x12",
        "specialize distinct_odd_prime_eisenstein_quotient_sum_identity x13",
        "specialize distinct_odd_prime_eisenstein_quotient_sum_identity x16",
        "specialize distinct_odd_prime_eisenstein_quotient_sum_identity x17",
        "specialize distinct_odd_prime_eisenstein_quotient_sum_identity x19",
        "specialize distinct_odd_prime_eisenstein_quotient_sum_identity x20",
        "specialize distinct_odd_prime_eisenstein_quotient_sum_identity x7",
        "specialize distinct_odd_prime_eisenstein_quotient_sum_identity x15",
        "apply distinct_odd_prime_eisenstein_quotient_sum_identity",
        "exact hpodd", "exact hqodd", "exact hp", "exact hq", "exact hpq",
        "exact hfirst_witness_witness_witness_witness_witness_witness_witness_witness_left",
        "exact hfirst_witness_witness_witness_witness_witness_witness_witness_witness_right_left",
        "exact hsecond_witness_witness_witness_witness_witness_witness_witness_witness_left",
        "exact hsecond_witness_witness_witness_witness_witness_witness_witness_witness_right_left",
        "exact hfirst_rectangle_witness_witness_witness_left",
        "exact hsecond_rectangle_witness_witness_witness_left",
        "exact hfirst_witness_witness_witness_witness_witness_witness_witness_witness_right_right_left",
        "exact hsecond_witness_witness_witness_witness_witness_witness_witness_witness_right_right_left",
        "exists x6", "exists x14", "exists x7", "exists x15",
        "split", "split",
        "exact hfirst_witness_witness_witness_witness_witness_witness_witness_witness_right_right_right_left",
        "exact hsecond_witness_witness_witness_witness_witness_witness_witness_witness_right_right_right_left",
        "split", "split",
        "exact hfirst_witness_witness_witness_witness_witness_witness_witness_witness_right_right_right_right",
        "exact hsecond_witness_witness_witness_witness_witness_witness_witness_witness_right_right_right_right",
        "exact hsum_identity",
    )

    return (
        spec(
            "odd_prime_gauss_eisenstein_orientation_data_exists",
            "forall p h a. p = 2 * h + 1 -> "
            f"({odd_a}) -> ({prime_p}) -> ({nondivisor}) -> "
            f"({orientation_result})",
            (
                "beta_range_exists",
                "arbitrary_gauss_lemma_complete",
                "prime_scaled_half_quotient_sum_exists",
                "gauss_eisenstein_sign_count_mod_quotient_sum",
                "mod_eq_symm",
            ),
            orientation_script,
            "One odd prime orientation has complete Gauss classification and "
            "a congruent exact Eisenstein quotient sum.",
        ),
        spec(
            "distinct_odd_primes_gauss_eisenstein_data_exists",
            "forall p q h k. p = 2 * h + 1 -> q = 2 * k + 1 -> "
            f"({prime_first}) -> ({prime_second}) -> ~(p = q) -> "
            f"({pair_result})",
            (
                "distinct_primes_mutually_nondivisible",
                "odd_prime_gauss_eisenstein_orientation_data_exists",
                "distinct_odd_prime_half_rectangle_total_exists",
                "distinct_odd_prime_eisenstein_quotient_sum_identity",
            ),
            pair_script,
            "Distinct odd primes admit both Gauss classification counts, their "
            "mod-two quotient sums, and the exact Eisenstein sum identity.",
        ),
    )


__all__ = ["make_gauss_eisenstein_data_candidate_theorems"]
