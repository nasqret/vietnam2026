"""Finite prime-power quotient sums for the Bertrand campaign.

``PowerQuotPrefix(p,n,b,c,l)`` and ``LegendreSum(p,n,e)`` are authoring
notation only.  They expand respectively to a beta-coded prefix of the
quotients

``n / p, n / p^2, ..., n / p^l``

and its exact relational sum.  Exponentiation, division, beta decoding, and
finite summation are all expanded to the unchanged first-order Peano
language before parsing.  The explicit Legendre stopping bound is ``n``.

This module is deliberately isolated and unregistered.  Its theorem bodies
must replay against their exact dependencies and their closed certificates
must be accepted by the independent kernel before any Alpha enrollment.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_power_valuation_candidate import _power_terms
from .fermat_residue_map_candidate import prime
from .finite_fold_surface import beta_at, sum_relation


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


def _lt_terms(left: str, right: str, *, tag: str) -> str:
    return f"exists bls_gap_{tag}. bls_gap_{tag} + S ({left}) = ({right})"


def _divrem_terms(
    value: str,
    divisor: str,
    quotient: str,
    remainder: str,
    *,
    tag: str,
) -> str:
    return (
        f"({value} = {divisor} * {quotient} + {remainder} /\\ "
        f"exists bls_remainder_gap_{tag}. "
        f"bls_remainder_gap_{tag} + S ({remainder}) = {divisor})"
    )


def _power_term_binders(tag: str) -> set[str]:
    """Names bound by the frozen private ``_power_terms`` expansion."""

    power_tag = f"bls_{tag}_power"
    names = {
        f"bpvi_{stem}_{power_tag}"
        for stem in (
            "b",
            "c",
            "i",
            "repeat_gap",
            "u",
            "v",
            "j",
            "factor",
            "partial",
            "successor",
            "product_gap",
        )
    }
    for suffix in ("repeat", "start", "terminal", "factor", "partial", "successor"):
        names.add(f"bpvi_h_{power_tag}_{suffix}")
        names.add(f"bpvi_q_{power_tag}_{suffix}")
    return names


def _prefix_binders(tag: str) -> set[str]:
    """All binders introduced by ``_power_quotient_prefix_terms``."""

    names = {
        f"bls_index_{tag}",
        f"bls_power_{tag}",
        f"bls_quotient_{tag}",
        f"bls_remainder_{tag}",
        f"bls_gap_{tag}_bound",
        f"bls_remainder_gap_{tag}_division",
        f"ff_h_bls_{tag}_quotient_entry",
        f"ff_q_bls_{tag}_quotient_entry",
    }
    names.update(_power_term_binders(tag))
    return names


def _assert_prefix_hygiene(variables: tuple[str, ...], tag: str) -> None:
    if _prefix_binders(tag) & set(variables):
        raise ValueError("generated power-quotient binder captures an argument")


def _power_quotient_prefix_terms(
    base: str,
    value: str,
    code: str,
    scale: str,
    length_term: str,
    *,
    tag: str,
) -> str:
    index = f"bls_index_{tag}"
    power = f"bls_power_{tag}"
    quotient = f"bls_quotient_{tag}"
    remainder = f"bls_remainder_{tag}"
    bound = _lt_terms(index, length_term, tag=f"{tag}_bound")
    powered = _power_terms(
        base,
        f"S {index}",
        power,
        tag=f"bls_{tag}_power",
    )
    decoded = beta_at(
        code,
        scale,
        index,
        quotient,
        tag=f"bls_{tag}_quotient_entry",
    )
    division = _divrem_terms(
        value,
        power,
        quotient,
        remainder,
        tag=f"{tag}_division",
    )
    return (
        f"forall {index}. ({bound}) -> exists {power} {quotient} {remainder}. "
        f"(({powered}) /\\ (({decoded}) /\\ ({division})))"
    )


def power_quotient_prefix(
    base: str,
    value: str,
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand the first ``length`` quotients by positive powers of ``base``."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (base, "power base"),
            (value, "dividend"),
            (code, "quotient code"),
            (scale, "quotient scale"),
            (length, "prefix length"),
        )
    )
    safe_tag = _identifier(tag, "binder tag")
    _assert_prefix_hygiene(variables, safe_tag)
    return _power_quotient_prefix_terms(
        base,
        value,
        code,
        scale,
        length,
        tag=safe_tag,
    )


def legendre_sum(base: str, value: str, result: str, *, tag: str) -> str:
    """Expand the finite sum of ``floor(value / base^(i+1))`` for ``i<value``."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (base, "power base"),
            (value, "dividend and stopping bound"),
            (result, "sum result"),
        )
    )
    safe_tag = _identifier(tag, "binder tag")
    code = f"bls_code_{safe_tag}"
    scale = f"bls_scale_{safe_tag}"
    if {code, scale} & set(variables):
        raise ValueError("generated Legendre-sum binder captures an argument")
    _assert_prefix_hygiene(variables + (code, scale), f"{safe_tag}_prefix")
    prefix = _power_quotient_prefix_terms(
        base,
        value,
        code,
        scale,
        value,
        tag=f"{safe_tag}_prefix",
    )
    total = sum_relation(code, scale, value, result, tag=f"bls_{safe_tag}_sum")
    return f"exists {code} {scale}. (({prefix}) /\\ ({total}))"


def make_bertrand_legendre_sum_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the first dependency-ordered Legendre-sum tranche."""

    prime_p = prime("p", tag="bls_prime")

    prefix = power_quotient_prefix("p", "n", "b", "c", "l", tag="bls_exists")
    successor_prefix = _power_quotient_prefix_terms(
        "p", "n", "z", "d", "S l", tag="bls_exists_successor"
    )
    previous_prefix = power_quotient_prefix(
        "p", "n", "b", "c", "l", tag="bls_exists_previous"
    )

    last_power = _power_terms("p", "S l", "D", tag="bls_exists_last_power")
    last_division = _divrem_terms(
        "n", "D", "q", "r", tag="bls_exists_last_division"
    )
    last_extension = (
        "exists z d. "
        f"(({beta_at('z', 'd', 'l', 'x3', tag='bls_exists_extension_last')}) /\\ "
        "forall i a. (exists h. h + S i = l) -> "
        f"({beta_at('x', 'x1', 'i', 'a', tag='bls_exists_extension_old')}) -> "
        f"({beta_at('z', 'd', 'i', 'a', tag='bls_exists_extension_new')}))"
    )
    old_entry = (
        "exists D q r. "
        f"(({_power_terms('p', 'S i', 'D', tag='bls_exists_old_power')}) /\\ "
        f"(({beta_at('x', 'x1', 'i', 'q', tag='bls_exists_old_entry')}) /\\ "
        f"({_divrem_terms('n', 'D', 'q', 'r', tag='bls_exists_old_division')})))"
    )

    source_prefix = power_quotient_prefix(
        "p", "n", "b", "c", "l", tag="bls_transport_source"
    )
    target_prefix = power_quotient_prefix(
        "p", "n", "z", "d", "l", tag="bls_transport_target"
    )
    source_entry = beta_at("b", "c", "i", "q", tag="bls_transport_given")
    target_entry = beta_at("z", "d", "i", "q", tag="bls_transport_result")
    source_data = (
        "exists D u r. "
        f"(({_power_terms('p', 'S i', 'D', tag='bls_transport_source_power')}) /\\ "
        f"(({beta_at('b', 'c', 'i', 'u', tag='bls_transport_source_stored')}) /\\ "
        f"({_divrem_terms('n', 'D', 'u', 'r', tag='bls_transport_source_division')})))"
    )
    target_data = (
        "exists E v s. "
        f"(({_power_terms('p', 'S i', 'E', tag='bls_transport_target_power')}) /\\ "
        f"(({beta_at('z', 'd', 'i', 'v', tag='bls_transport_target_stored')}) /\\ "
        f"({_divrem_terms('n', 'E', 'v', 's', tag='bls_transport_target_division')})))"
    )

    total = legendre_sum("p", "n", "e", tag="bls_total")
    functional_left = legendre_sum("p", "n", "e", tag="bls_functional_left")
    functional_right = legendre_sum("p", "n", "f", tag="bls_functional_right")
    zero_total = legendre_sum("p", "n", "e", tag="bls_zero")

    transported_sum = sum_relation(
        "x2", "x3", "n", "e", tag="bls_functional_transported"
    )
    functional_pointwise = (
        "forall i a. "
        f"({_lt_terms('i', 'n', tag='bls_functional_bound')}) -> "
        f"({beta_at('x', 'x1', 'i', 'a', tag='bls_functional_source_entry')}) -> "
        f"({beta_at('x2', 'x3', 'i', 'a', tag='bls_functional_target_entry')})"
    )

    return (
        spec(
            "prime_power_quotient_prefix_exists",
            f"forall p n l. ({prime_p}) -> exists b c. ({prefix})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "pow_exists",
                "prime_nonzero",
                "one_le_of_ne_zero",
                "pow_nonzero_of_one_le",
                "division_remainder_exists",
                "beta_prefix_extend",
                "finite_lt_succ_eq_or_lt",
            ),
            (
                "intro p",
                "intro n",
                "induction l",
                "intro hp",
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
                "intro hp",
                f"have hprevious : exists b c. ({previous_prefix})",
                "apply IH",
                "exact hp",
                "cases hprevious",
                "cases hprevious_witness",
                f"have hpower : exists D. ({last_power})",
                "specialize pow_exists p",
                "specialize pow_exists (S l)",
                "exact pow_exists",
                "cases hpower",
                "have hp0 : ~(p = 0)",
                "intro hpzero",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hp",
                "exact hpzero",
                "have hp1 : exists k. k + 1 = p",
                "specialize one_le_of_ne_zero p",
                "apply one_le_of_ne_zero",
                "exact hp0",
                "have hD0 : ~(x2 = 0)",
                "intro hzero",
                "specialize pow_nonzero_of_one_le p",
                "specialize pow_nonzero_of_one_le (S l)",
                "specialize pow_nonzero_of_one_le x2",
                "apply pow_nonzero_of_one_le",
                "exact hp1",
                "exact hpower_witness",
                "exact hzero",
                f"have hdivision : exists q r. ({_divrem_terms('n', 'x2', 'q', 'r', tag='bls_exists_division_witness')})",
                "specialize division_remainder_exists x2",
                "specialize division_remainder_exists n",
                "apply division_remainder_exists",
                "exact hD0",
                "cases hdivision",
                "cases hdivision_witness",
                f"have hextension : {last_extension}",
                "specialize beta_prefix_extend l",
                "specialize beta_prefix_extend x",
                "specialize beta_prefix_extend x1",
                "specialize beta_prefix_extend x3",
                "exact beta_prefix_extend",
                "cases hextension",
                "cases hextension_witness",
                "cases hextension_witness_witness",
                "exists x5",
                "exists x6",
                "intro i",
                "intro hi",
                "have hsplit : i = l \\/ exists gap. gap + S i = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                "cases hsplit",
                "exists x2",
                "exists x3",
                "exists x4",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "split",
                "exact hpower_witness",
                "split",
                "exact hextension_witness_witness_left",
                "exact hdivision_witness_witness",
                f"have hold : {old_entry}",
                "specialize hprevious_witness_witness i",
                "apply hprevious_witness_witness",
                "exact hsplit_right",
                "cases hold",
                "cases hold_witness",
                "cases hold_witness_witness",
                "cases hold_witness_witness_witness",
                "cases hold_witness_witness_witness_right",
                "exists x7",
                "exists x8",
                "exists x9",
                "split",
                "exact hold_witness_witness_witness_left",
                "split",
                "specialize hextension_witness_witness_right i",
                "specialize hextension_witness_witness_right x8",
                "apply hextension_witness_witness_right",
                "exact hsplit_right",
                "exact hold_witness_witness_witness_right_left",
                "exact hold_witness_witness_witness_right_right",
            ),
            "Every prime-power quotient prefix has a finite beta code.",
        ),
        spec(
            "power_quotient_prefix_transport",
            "forall p n b c z d l. "
            f"({source_prefix}) -> ({target_prefix}) -> forall i q. "
            f"({_lt_terms('i', 'l', tag='bls_transport_bound')}) -> "
            f"({source_entry}) -> ({target_entry})",
            ("beta_at_unique", "pow_functional", "division_remainder_unique"),
            (
                "intro p",
                "intro n",
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro l",
                "intro hsource",
                "intro htarget",
                "intro i",
                "intro q",
                "intro hi",
                "intro hq",
                f"have hs : {source_data}",
                "specialize hsource i",
                "apply hsource",
                "exact hi",
                f"have ht : {target_data}",
                "specialize htarget i",
                "apply htarget",
                "exact hi",
                "cases hs",
                "cases hs_witness",
                "cases hs_witness_witness",
                "cases hs_witness_witness_witness",
                "cases hs_witness_witness_witness_right",
                "cases hs_witness_witness_witness_right_right",
                "cases ht",
                "cases ht_witness",
                "cases ht_witness_witness",
                "cases ht_witness_witness_witness",
                "cases ht_witness_witness_witness_right",
                "cases ht_witness_witness_witness_right_right",
                "have hD : x = x3",
                "specialize pow_functional p",
                "specialize pow_functional (S i)",
                "specialize pow_functional x",
                "specialize pow_functional x3",
                "apply pow_functional",
                "exact hs_witness_witness_witness_left",
                "exact ht_witness_witness_witness_left",
                "rewrite <- hD at ht_witness_witness_witness_right_right_left",
                "rewrite <- hD at ht_witness_witness_witness_right_right_right",
                "have hquotients : x1 = x4",
                "specialize division_remainder_unique x",
                "specialize division_remainder_unique n",
                "specialize division_remainder_unique x1",
                "specialize division_remainder_unique x2",
                "specialize division_remainder_unique x4",
                "specialize division_remainder_unique x5",
                "have hdivision_unique : x1 = x4 /\\ x2 = x5",
                "apply division_remainder_unique",
                "exact hs_witness_witness_witness_right_right_left",
                "exact hs_witness_witness_witness_right_right_right",
                "exact ht_witness_witness_witness_right_right_left",
                "exact ht_witness_witness_witness_right_right_right",
                "cases hdivision_unique",
                "exact hdivision_unique_left",
                "have hstored : x1 = q",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique i",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique q",
                "apply beta_at_unique",
                "exact hs_witness_witness_witness_right_left",
                "exact hq",
                "rewrite <- hstored",
                "rewrite hquotients",
                "rewrite <- hstored",
                "rewrite hquotients",
                "exact ht_witness_witness_witness_right_left",
            ),
            "Equivalent power-quotient prefixes transport decoded quotients pointwise.",
        ),
        spec(
            "prime_legendre_sum_exists",
            f"forall p n. ({prime_p}) -> exists e. ({total})",
            ("prime_power_quotient_prefix_exists", "beta_sum_exists"),
            (
                "intro p",
                "intro n",
                "intro hp",
                "have hprefix : exists b c. "
                f"({power_quotient_prefix('p', 'n', 'b', 'c', 'n', tag='bls_total_witness')})",
                "specialize prime_power_quotient_prefix_exists p",
                "specialize prime_power_quotient_prefix_exists n",
                "specialize prime_power_quotient_prefix_exists n",
                "apply prime_power_quotient_prefix_exists",
                "exact hp",
                "cases hprefix",
                "cases hprefix_witness",
                "have hsum : exists e. "
                f"({sum_relation('x', 'x1', 'n', 'e', tag='bls_total_sum_witness')})",
                "specialize beta_sum_exists x",
                "specialize beta_sum_exists x1",
                "specialize beta_sum_exists n",
                "exact beta_sum_exists",
                "cases hsum",
                "exists x2",
                "exists x",
                "exists x1",
                "split",
                "exact hprefix_witness_witness",
                "exact hsum_witness",
            ),
            "Every prime and natural input have a finite relational Legendre sum.",
        ),
        spec(
            "legendre_sum_functional",
            f"forall p n e f. ({functional_left}) -> ({functional_right}) -> e = f",
            (
                "power_quotient_prefix_transport",
                "beta_sum_transport_prefix",
                "beta_sum_functional",
            ),
            (
                "intro p",
                "intro n",
                "intro e",
                "intro f",
                "intro he",
                "intro hf",
                "cases he",
                "cases he_witness",
                "cases he_witness_witness",
                "cases hf",
                "cases hf_witness",
                "cases hf_witness_witness",
                f"have htransported : {transported_sum}",
                "specialize beta_sum_transport_prefix x",
                "specialize beta_sum_transport_prefix x1",
                "specialize beta_sum_transport_prefix x2",
                "specialize beta_sum_transport_prefix x3",
                "specialize beta_sum_transport_prefix n",
                "specialize beta_sum_transport_prefix e",
                "apply beta_sum_transport_prefix",
                "exact he_witness_witness_right",
                f"have hpointwise : {functional_pointwise}",
                "specialize power_quotient_prefix_transport p",
                "specialize power_quotient_prefix_transport n",
                "specialize power_quotient_prefix_transport x",
                "specialize power_quotient_prefix_transport x1",
                "specialize power_quotient_prefix_transport x2",
                "specialize power_quotient_prefix_transport x3",
                "specialize power_quotient_prefix_transport n",
                "apply power_quotient_prefix_transport",
                "exact he_witness_witness_left",
                "exact hf_witness_witness_left",
                "intro i",
                "intro a",
                "intro hi",
                "intro ha",
                "specialize hpointwise i",
                "specialize hpointwise a",
                "apply hpointwise",
                "exact hi",
                "exact ha",
                "specialize beta_sum_functional x2",
                "specialize beta_sum_functional x3",
                "specialize beta_sum_functional n",
                "specialize beta_sum_functional e",
                "specialize beta_sum_functional f",
                "apply beta_sum_functional",
                "exact htransported",
                "exact hf_witness_witness_right",
            ),
            "The finite relational Legendre sum has a unique value.",
        ),
        spec(
            "legendre_sum_zero",
            f"forall p n e. n = 0 -> ({zero_total}) -> e = 0",
            ("beta_sum_zero",),
            (
                "intro p",
                "intro n",
                "intro e",
                "intro hn",
                "intro hsum",
                "cases hsum",
                "cases hsum_witness",
                "cases hsum_witness_witness",
                "specialize beta_sum_zero x",
                "specialize beta_sum_zero x1",
                "specialize beta_sum_zero e",
                "apply beta_sum_zero",
                "rewrite hn at hsum_witness_witness_right",
                "rewrite hn at hsum_witness_witness_right",
                "rewrite hn at hsum_witness_witness_right",
                "exact hsum_witness_witness_right",
            ),
            "The finite Legendre sum at zero is zero.",
        ),
    )


__all__ = [
    "legendre_sum",
    "make_bertrand_legendre_sum_candidate_theorems",
    "power_quotient_prefix",
]
