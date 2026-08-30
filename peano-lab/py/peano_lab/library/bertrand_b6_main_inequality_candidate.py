"""Constructive main-inequality candidates for the Bertrand B6 route.

The first row combines the factorized root threshold, the all-root H/J
envelope, the quotient budget, and the two power-product growth lemmas under
one supplied ``PowTotal`` premise.  The second row discharges that premise
through the already checked relational-power totality theorem.  The final
row preserves the public additive spelling ``n + n`` and transports its
three graph premises to the internal ``2 * n`` spelling by five explicit
checked equality rewrites.

``PowTotal``, ``FloorSqrt``, ``DivRem``, ``Pow``, and ``Le`` are authoring
notation only.  Every occurrence is expanded hygienically into the existing
first-order Peano language before a theorem specification is returned.  The
large-input carrier stays exactly ``16 * 32`` throughout.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.kernel.terms import parse_term_with_names

from .bertrand_ceil_sqrt_candidate import (
    ceil_div_six_relation,
    floor_sqrt_relation,
)
from .bertrand_power_total_candidate import power_total_relation
from .bertrand_quotient_budget_candidate import (
    quotient_complement_budget_relation,
    witness_le,
)
from .power_algebra_theorems import _power_terms


_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _identifier(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not (value[0].isalpha() or value[0] == "_")
        or not all(
            character.isalnum() or character in "_'"
            for character in value[1:]
        )
        or value in _RESERVED
    ):
        raise ValueError(f"{label} must be a non-reserved Peano identifier")
    return value


def _term_names(*labelled: tuple[str, str]) -> tuple[str, ...]:
    names: list[str] = []
    for source, label in labelled:
        if not isinstance(source, str) or not source:
            raise ValueError(f"{label} must be a nonempty Peano term")
        try:
            _term, free_names = parse_term_with_names(source)
        except ValueError as exc:
            raise ValueError(f"{label} must be a Peano term: {exc}") from None
        names.extend(free_names)
    return tuple(dict.fromkeys(names))


def _divrem_three_relation(
    dividend: str,
    quotient: str,
    remainder: str,
    *,
    tag: str,
) -> str:
    """Expand ``DivRem(dividend,3,quotient,remainder)`` hygienically."""

    variables = _term_names(
        (dividend, "division dividend"),
        (quotient, "division quotient"),
        (remainder, "division remainder"),
    )
    gap = f"bmi_remainder_gap_{_identifier(tag, 'binder tag')}"
    if gap in variables:
        raise ValueError(
            "generated Bertrand main-inequality binder captures an argument"
        )
    return (
        f"((({dividend}) = 3 * ({quotient}) + ({remainder})) /\\ "
        f"exists {gap}. {gap} + S ({remainder}) = 3)"
    )


def make_bertrand_b6_main_inequality_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the frozen factorized, thin, and public B6 inequality rows."""

    factorized_total = power_total_relation(tag="b6_main_factorized")
    factorized_threshold = witness_le(
        "16 * 32", "n", tag="b6_main_factorized_threshold"
    )
    factorized_floor = floor_sqrt_relation(
        "2 * n", "s", tag="b6_main_factorized_floor"
    )
    factorized_division = _divrem_three_relation(
        "2 * n",
        "q",
        "r",
        tag="b6_main_factorized_division",
    )
    factorized_a = _power_terms(
        "2 * n", "s", "A", tag="b6_main_factorized_a"
    )
    factorized_b = _power_terms(
        "4", "q", "B", tag="b6_main_factorized_b"
    )
    factorized_f = _power_terms(
        "4", "n", "F", tag="b6_main_factorized_f"
    )
    factorized_result = witness_le(
        "n * A * B", "F", tag="b6_main_factorized_result"
    )

    root_lower = witness_le("32", "s", tag="b6_main_root_lower")
    ceiling = ceil_div_six_relation(
        "s * s", "e", tag="b6_main_ceiling"
    )
    envelope_h = _power_terms(
        "s + 1", "2 * s + 2", "H", tag="b6_main_envelope_h"
    )
    envelope_u = _power_terms(
        "4", "e", "U", tag="b6_main_envelope_u"
    )
    envelope_u_witness = _power_terms(
        "4", "x", "U", tag="b6_main_envelope_u_witness"
    )
    envelope_j = _power_terms(
        "s + 7", "12", "J", tag="b6_main_envelope_j"
    )
    envelope_g = _power_terms(
        "4", "s + 5", "G", tag="b6_main_envelope_g"
    )
    envelope_h_order = witness_le(
        "H", "U", tag="b6_main_envelope_h_order"
    )
    envelope_j_order = witness_le(
        "J", "G", tag="b6_main_envelope_j_order"
    )

    budget_data = quotient_complement_budget_relation(
        "n", "q", "c", tag="b6_main_budget_data"
    )
    budget_ec = witness_le("e", "c", tag="b6_main_budget_ec")
    budget_sum = witness_le("q + e", "n", tag="b6_main_budget_sum")
    budget_ec_witness = witness_le(
        "x", "c", tag="b6_main_budget_ec_witness"
    )
    budget_sum_witness = witness_le(
        "q + x", "n", tag="b6_main_budget_sum_witness"
    )
    budget_remainder_gap = "bmi_remainder_gap_b6_main_budget_preserved"
    budget_result = (
        f"exists c. ((({budget_data}) /\\ "
        f"((({budget_ec_witness}) /\\ ({budget_sum_witness})))) /\\ "
        f"exists {budget_remainder_gap}. {budget_remainder_gap} + S r = 3)"
    )

    h_power = _power_terms(
        "s + 1", "2 * s + 2", "x1", tag="b6_main_h_power"
    )
    u_power = _power_terms(
        "4", "x", "x2", tag="b6_main_u_power"
    )
    j_power = _power_terms(
        "s + 7", "12", "x3", tag="b6_main_j_power"
    )
    g_power = _power_terms(
        "4", "s + 5", "x4", tag="b6_main_g_power"
    )
    h_u_order = witness_le("x1", "x2", tag="b6_main_h_u_order")
    j_g_order = witness_le("x3", "x4", tag="b6_main_j_g_order")
    floor_product_order = witness_le(
        "n * A", "x1", tag="b6_main_floor_product_order"
    )
    floor_to_u_order = witness_le(
        "n * A", "x2", tag="b6_main_floor_to_u_order"
    )
    scaled_floor_order = witness_le(
        "(n * A) * B", "x2 * B", tag="b6_main_scaled_floor_order"
    )
    u_b_order = witness_le(
        "x2 * B", "F", tag="b6_main_u_b_order"
    )

    thin_threshold = witness_le(
        "16 * 32", "n", tag="b6_main_thin_threshold"
    )
    thin_floor = floor_sqrt_relation(
        "2 * n", "s", tag="b6_main_thin_floor"
    )
    thin_division = _divrem_three_relation(
        "2 * n", "q", "r", tag="b6_main_thin_division"
    )
    thin_a = _power_terms("2 * n", "s", "A", tag="b6_main_thin_a")
    thin_b = _power_terms("4", "q", "B", tag="b6_main_thin_b")
    thin_f = _power_terms("4", "n", "F", tag="b6_main_thin_f")
    thin_result = witness_le(
        "n * A * B", "F", tag="b6_main_thin_result"
    )
    thin_total = power_total_relation(tag="b6_main_thin_total")

    public_threshold = witness_le(
        "16 * 32", "n", tag="b6_main_public_threshold"
    )
    public_floor = floor_sqrt_relation(
        "n + n", "s", tag="b6_main_public_floor"
    )
    public_division = _divrem_three_relation(
        "n + n", "q", "r", tag="b6_main_public_division"
    )
    public_a = _power_terms(
        "n + n", "s", "A", tag="b6_main_public_a"
    )
    public_b = _power_terms("4", "q", "B", tag="b6_main_public_b")
    public_f = _power_terms("4", "n", "F", tag="b6_main_public_f")
    public_result = witness_le(
        "n * A * B", "F", tag="b6_main_public_result"
    )

    return (
        spec(
            "bertrand_main_inequality_factorized_from_total",
            "forall n s q r A B F. "
            f"({factorized_total}) -> ({factorized_threshold}) -> "
            f"({factorized_floor}) -> ({factorized_division}) -> "
            f"({factorized_a}) -> ({factorized_b}) -> "
            f"({factorized_f}) -> ({factorized_result})",
            (
                "floor_sqrt_factorized_threshold_thirty_two",
                "ceil_div_six_total",
                "bertrand_hj_envelope_thirty_two",
                "floor_ceil_division_budget",
                "bertrand_floor_power_product_le_h_from_total",
                "bertrand_four_power_product_le_of_sum_from_total",
                "mul_le_mul_right",
                "le_trans",
            ),
            (
                "intro n",
                "intro s",
                "intro q",
                "intro r",
                "intro A",
                "intro B",
                "intro F",
                "intro htotal",
                "intro hthreshold",
                "intro hfloor",
                "intro hdiv",
                "intro hA",
                "intro hB",
                "intro hF",
                f"have hs : {root_lower}",
                "specialize floor_sqrt_factorized_threshold_thirty_two n",
                "specialize floor_sqrt_factorized_threshold_thirty_two s",
                "apply floor_sqrt_factorized_threshold_thirty_two",
                "exact hthreshold",
                "exact hfloor",
                f"have he_exists : exists e. ({ceiling})",
                "specialize ceil_div_six_total (s * s)",
                "exact ceil_div_six_total",
                "cases he_exists",
                f"have hH_exists : exists H. ({envelope_h})",
                "specialize htotal (s + 1)",
                "specialize htotal (2 * s + 2)",
                "exact htotal",
                "cases hH_exists",
                f"have hU_exists : exists U. ({envelope_u_witness})",
                "specialize htotal 4",
                "specialize htotal x",
                "exact htotal",
                "cases hU_exists",
                f"have hJ_exists : exists J. ({envelope_j})",
                "specialize htotal (s + 7)",
                "specialize htotal 12",
                "exact htotal",
                "cases hJ_exists",
                f"have hG_exists : exists G. ({envelope_g})",
                "specialize htotal 4",
                "specialize htotal (s + 5)",
                "exact htotal",
                "cases hG_exists",
                f"have henvelope : (({h_u_order}) /\\ ({j_g_order}))",
                "specialize bertrand_hj_envelope_thirty_two s",
                "specialize bertrand_hj_envelope_thirty_two x",
                "specialize bertrand_hj_envelope_thirty_two x1",
                "specialize bertrand_hj_envelope_thirty_two x2",
                "specialize bertrand_hj_envelope_thirty_two x3",
                "specialize bertrand_hj_envelope_thirty_two x4",
                "apply bertrand_hj_envelope_thirty_two",
                "exact hs",
                "exact he_exists_witness",
                "exact hH_exists_witness",
                "exact hU_exists_witness",
                "exact hJ_exists_witness",
                "exact hG_exists_witness",
                "cases henvelope",
                f"have hbudget : {budget_result}",
                "specialize floor_ceil_division_budget n",
                "specialize floor_ceil_division_budget q",
                "specialize floor_ceil_division_budget r",
                "specialize floor_ceil_division_budget s",
                "specialize floor_ceil_division_budget x",
                "apply floor_ceil_division_budget",
                "exact hfloor",
                "exact he_exists_witness",
                "exact hdiv",
                "cases hbudget",
                "cases hbudget_witness",
                "cases hbudget_witness_left",
                "cases hbudget_witness_left_right",
                f"have hfloor_product : {floor_product_order}",
                "specialize bertrand_floor_power_product_le_h_from_total n",
                "specialize bertrand_floor_power_product_le_h_from_total s",
                "specialize bertrand_floor_power_product_le_h_from_total A",
                "specialize bertrand_floor_power_product_le_h_from_total x1",
                "apply bertrand_floor_power_product_le_h_from_total",
                "exact htotal",
                "exact hfloor",
                "exact hA",
                "exact hH_exists_witness",
                f"have hfloor_to_u : {floor_to_u_order}",
                "specialize le_trans (n * A)",
                "specialize le_trans x1",
                "specialize le_trans x2",
                "apply le_trans",
                "exact hfloor_product",
                "exact henvelope_left",
                f"have hscaled_floor : {scaled_floor_order}",
                "specialize mul_le_mul_right (n * A)",
                "specialize mul_le_mul_right x2",
                "specialize mul_le_mul_right B",
                "apply mul_le_mul_right",
                "exact hfloor_to_u",
                f"have hub : {u_b_order}",
                "specialize bertrand_four_power_product_le_of_sum_from_total q",
                "specialize bertrand_four_power_product_le_of_sum_from_total x",
                "specialize bertrand_four_power_product_le_of_sum_from_total n",
                "specialize bertrand_four_power_product_le_of_sum_from_total B",
                "specialize bertrand_four_power_product_le_of_sum_from_total x2",
                "specialize bertrand_four_power_product_le_of_sum_from_total F",
                "apply bertrand_four_power_product_le_of_sum_from_total",
                "exact htotal",
                "exact hbudget_witness_left_right_right",
                "exact hB",
                "exact hU_exists_witness",
                "exact hF",
                "specialize le_trans ((n * A) * B)",
                "specialize le_trans (x2 * B)",
                "specialize le_trans F",
                "apply le_trans",
                "exact hscaled_floor",
                "exact hub",
            ),
            "The factorized threshold and all-root envelope imply the B6 "
            "power-product inequality under one supplied power-totality premise.",
        ),
        spec(
            "bertrand_main_inequality_factorized",
            "forall n s q r A B F. "
            f"({thin_threshold}) -> ({thin_floor}) -> "
            f"({thin_division}) -> ({thin_a}) -> ({thin_b}) -> "
            f"({thin_f}) -> ({thin_result})",
            (
                "pow_exists",
                "bertrand_main_inequality_factorized_from_total",
            ),
            (
                "intro n",
                "intro s",
                "intro q",
                "intro r",
                "intro A",
                "intro B",
                "intro F",
                "intro hthreshold",
                "intro hfloor",
                "intro hdiv",
                "intro hA",
                "intro hB",
                "intro hF",
                f"have htotal : {thin_total}",
                "intro a",
                "intro e",
                "specialize pow_exists a",
                "specialize pow_exists e",
                "exact pow_exists",
                "specialize bertrand_main_inequality_factorized_from_total n",
                "specialize bertrand_main_inequality_factorized_from_total s",
                "specialize bertrand_main_inequality_factorized_from_total q",
                "specialize bertrand_main_inequality_factorized_from_total r",
                "specialize bertrand_main_inequality_factorized_from_total A",
                "specialize bertrand_main_inequality_factorized_from_total B",
                "specialize bertrand_main_inequality_factorized_from_total F",
                "apply bertrand_main_inequality_factorized_from_total",
                "exact htotal",
                "exact hthreshold",
                "exact hfloor",
                "exact hdiv",
                "exact hA",
                "exact hB",
                "exact hF",
            ),
            "The factorized B6 inequality discharges relational-power "
            "totality exactly once.",
        ),
        spec(
            "bertrand_main_inequality_nat",
            "forall n s q r A B F. "
            f"({public_threshold}) -> ({public_floor}) -> "
            f"({public_division}) -> ({public_a}) -> ({public_b}) -> "
            f"({public_f}) -> ({public_result})",
            (
                "two_mul_eq_add_self",
                "bertrand_main_inequality_factorized",
            ),
            (
                "intro n",
                "intro s",
                "intro q",
                "intro r",
                "intro A",
                "intro B",
                "intro F",
                "intro hthreshold",
                "intro hfloor",
                "intro hdiv",
                "intro hA",
                "intro hB",
                "intro hF",
                "have hdouble : 2 * n = n + n",
                "specialize two_mul_eq_add_self n",
                "exact two_mul_eq_add_self",
                "rewrite <- hdouble at hfloor",
                "rewrite <- hdouble at hfloor",
                "rewrite <- hdouble at hdiv",
                "rewrite <- hdouble at hA",
                "rewrite <- hdouble at hA",
                "specialize bertrand_main_inequality_factorized n",
                "specialize bertrand_main_inequality_factorized s",
                "specialize bertrand_main_inequality_factorized q",
                "specialize bertrand_main_inequality_factorized r",
                "specialize bertrand_main_inequality_factorized A",
                "specialize bertrand_main_inequality_factorized B",
                "specialize bertrand_main_inequality_factorized F",
                "apply bertrand_main_inequality_factorized",
                "exact hthreshold",
                "exact hfloor",
                "exact hdiv",
                "exact hA",
                "exact hB",
                "exact hF",
            ),
            "The public B6 surface retains n+n and reaches the factorized "
            "internal theorem through five checked equality rewrites.",
        ),
    )


__all__ = ["make_bertrand_b6_main_inequality_candidate_theorems"]
