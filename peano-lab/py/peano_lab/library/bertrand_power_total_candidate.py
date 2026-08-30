"""Capacity-normalized relational-power infrastructure for Bertrand B6.

The existing closed power theorems are mathematically suitable for Bertrand,
but several of them each embed the same comparatively large ``pow_exists``
certificate.  This isolated candidate surface exposes that already-proved
totality proposition as an ordinary antecedent instead.  A downstream block
proof can consequently cut ``pow_exists`` once and pass the resulting local
hypothesis to every theorem below.

``PowTotal`` is authoring syntax only::

    forall a e. exists x. Pow(a,e,x)

Every occurrence is expanded through the existing beta-coded finite-product
graph before parsing.  No predicate, proof rule, axiom, or classical
principle is added to the kernel.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import power_relation
from .power_algebra_theorems import _power_terms


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


def power_total_relation(*, tag: str) -> str:
    """Expand ``forall a e. exists x. Pow(a,e,x)`` hygienically."""

    safe_tag = _identifier(tag, "power-total tag")
    base = f"bpt_a_{safe_tag}"
    exponent = f"bpt_e_{safe_tag}"
    result = f"bpt_x_{safe_tag}"
    power = power_relation(
        base,
        exponent,
        result,
        tag=f"bpt_value_{safe_tag}",
    )
    return f"forall {base} {exponent}. exists {result}. ({power})"


def make_bertrand_power_total_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build conditional power laws sharing one explicit totality premise."""

    total_successor = power_total_relation(tag="successor")
    predecessor = power_relation("a", "e", "r", tag="bpt_predecessor")
    successor = _power_terms("a", "S e", "n", tag="bpt_successor")
    successor_witness = _power_terms(
        "a", "S e", "x", tag="bpt_successor_witness"
    )

    total_mul_exp = power_total_relation(tag="mul_exp")
    mul_base = power_relation("a", "e", "x", tag="bpt_mul_base")
    mul_outer = power_relation("x", "f", "y", tag="bpt_mul_outer")
    mul_total = power_relation("a", "p", "z", tag="bpt_mul_total")
    mul_y_prefix = power_relation("x", "f", "r", tag="bpt_mul_y_prefix")
    mul_total_prefix = _power_terms(
        "a", "e * f", "r", tag="bpt_mul_total_prefix"
    )

    total_exponent = power_total_relation(tag="exponent")
    exponent_base_at_least_one = (
        "exists bpt_gap_exponent_base. "
        "bpt_gap_exponent_base + 1 = a"
    )
    exponent_le = (
        "exists bpt_gap_exponent_order. "
        "bpt_gap_exponent_order + e = f"
    )
    exponent_result = (
        "exists bpt_gap_exponent_result. "
        "bpt_gap_exponent_result + x = y"
    )
    exponent_left = power_relation("a", "e", "x", tag="bpt_exp_left")
    exponent_right = power_relation("a", "f", "y", tag="bpt_exp_right")
    # ``cases hef`` exposes the additive gap under deterministic name ``x1``.
    exponent_gap = power_relation("a", "x1", "z", tag="bpt_exp_gap")

    total_seed = power_total_relation(tag="seed")
    two_two_any = _power_terms("2", "2", "x", tag="bpt_seed_two_any")
    two_two = _power_terms("2", "2", "4", tag="bpt_seed_two")
    two_three = _power_terms("2", "3", "8", tag="bpt_seed_three")
    two_four = _power_terms("2", "4", "16", tag="bpt_seed_four")
    two_five = _power_terms("2", "5", "32", tag="bpt_seed_five")
    two_six = _power_terms("2", "6", "64", tag="bpt_seed_six")
    two_seven = _power_terms("2", "7", "128", tag="bpt_seed_seven")

    return (
        spec(
            "pow_successor_compose_from_total",
            "forall a e r n. "
            f"({total_successor}) -> ({predecessor}) -> n = r * a -> "
            f"({successor})",
            ("pow_successor_pair_mul",),
            (
                "intro a",
                "intro e",
                "intro r",
                "intro n",
                "intro htotal",
                "intro hprevious",
                "intro hn",
                f"have hsuccessor : exists x. ({successor_witness})",
                "specialize htotal a",
                "specialize htotal (S e)",
                "exact htotal",
                "cases hsuccessor",
                "have hx : x = r * a",
                "specialize pow_successor_pair_mul a",
                "specialize pow_successor_pair_mul e",
                "specialize pow_successor_pair_mul (S e)",
                "specialize pow_successor_pair_mul r",
                "specialize pow_successor_pair_mul x",
                "apply pow_successor_pair_mul",
                "refl",
                "exact hprevious",
                "exact hsuccessor_witness",
                "have hxn : x = n",
                "trans r * a",
                "exact hx",
                "symm",
                "exact hn",
                "rewrite <- hxn",
                "rewrite <- hxn",
                "exact hsuccessor_witness",
            ),
            "One shared power-totality premise constructs a successor power.",
        ),
        spec(
            "pow_mul_exp_from_total",
            "forall a e f p x y z. "
            f"({total_mul_exp}) -> p = e * f -> ({mul_base}) -> "
            f"({mul_outer}) -> ({mul_total}) -> y = z",
            ("pow_zero", "pow_successor_decompose", "pow_add"),
            (
                "intro a",
                "intro e",
                "induction f",
                "intro p",
                "intro x",
                "intro y",
                "intro z",
                "intro htotal",
                "intro hp",
                "intro hx",
                "intro hy",
                "intro hz",
                "rewrite PA5 at hp",
                "rewrite hp at hz",
                "rewrite hp at hz",
                "rewrite hp at hz",
                "rewrite hp at hz",
                "have hy1 : y = 1",
                "specialize pow_zero x",
                "specialize pow_zero 0",
                "specialize pow_zero y",
                "apply pow_zero",
                "refl",
                "exact hy",
                "have hz1 : z = 1",
                "specialize pow_zero a",
                "specialize pow_zero 0",
                "specialize pow_zero z",
                "apply pow_zero",
                "refl",
                "exact hz",
                "trans 1",
                "exact hy1",
                "symm",
                "exact hz1",
                "intro p",
                "intro x",
                "intro y",
                "intro z",
                "intro htotal",
                "intro hp",
                "intro hx",
                "intro hy",
                "intro hz",
                f"have hy_step : exists r. ({mul_y_prefix}) /\\ y = r * x",
                "specialize pow_successor_decompose x",
                "specialize pow_successor_decompose f",
                "specialize pow_successor_decompose (S f)",
                "specialize pow_successor_decompose y",
                "apply pow_successor_decompose",
                "refl",
                "exact hy",
                "cases hy_step",
                "cases hy_step_witness",
                f"have hqpow : exists r. ({mul_total_prefix})",
                "specialize htotal a",
                "specialize htotal (e * f)",
                "exact htotal",
                "cases hqpow",
                "have hprefix : x1 = x2",
                "specialize IH (e * f)",
                "specialize IH x",
                "specialize IH x1",
                "specialize IH x2",
                "apply IH",
                "exact htotal",
                "refl",
                "exact hx",
                "exact hy_step_witness_left",
                "exact hqpow_witness",
                "have hpsum : p = (e * f) + e",
                "trans e * S f",
                "exact hp",
                "apply PA6",
                "have hproduct : z = x2 * x",
                "specialize pow_add a",
                "specialize pow_add (e * f)",
                "specialize pow_add e",
                "specialize pow_add p",
                "specialize pow_add x2",
                "specialize pow_add x",
                "specialize pow_add z",
                "apply pow_add",
                "exact hpsum",
                "exact hqpow_witness",
                "exact hx",
                "exact hz",
                "trans x1 * x",
                "exact hy_step_witness_right",
                "trans x2 * x",
                "congr",
                "exact hprefix",
                "refl",
                "symm",
                "exact hproduct",
            ),
            "Iterated powers multiply exponents using a supplied totality proof.",
        ),
        spec(
            "pow_exponent_monotone_from_total",
            "forall a e f x y. "
            f"({total_exponent}) -> ({exponent_base_at_least_one}) -> "
            f"({exponent_le}) -> ({exponent_left}) -> ({exponent_right}) -> "
            f"({exponent_result})",
            ("pow_add", "one_le_pow", "le_mul_of_one_le_right", "add_comm"),
            (
                "intro a",
                "intro e",
                "intro f",
                "intro x",
                "intro y",
                "intro htotal",
                "intro ha",
                "intro hef",
                "intro hx",
                "intro hy",
                "cases hef",
                "have hsum : f = e + x1",
                "trans x1 + e",
                "symm",
                "exact hef_witness",
                "specialize add_comm x1",
                "specialize add_comm e",
                "exact add_comm",
                f"have hgap : exists z. ({exponent_gap})",
                "specialize htotal a",
                "specialize htotal x1",
                "exact htotal",
                "cases hgap",
                "have hyfactor : y = x * x2",
                "specialize pow_add a",
                "specialize pow_add e",
                "specialize pow_add x1",
                "specialize pow_add f",
                "specialize pow_add x",
                "specialize pow_add x2",
                "specialize pow_add y",
                "apply pow_add",
                "exact hsum",
                "exact hx",
                "exact hgap_witness",
                "exact hy",
                "have hgap1 : exists k. k + 1 = x2",
                "specialize one_le_pow a",
                "specialize one_le_pow x1",
                "specialize one_le_pow x2",
                "apply one_le_pow",
                "exact ha",
                "exact hgap_witness",
                "rewrite hyfactor",
                "specialize le_mul_of_one_le_right x",
                "specialize le_mul_of_one_le_right x2",
                "apply le_mul_of_one_le_right",
                "exact hgap1",
            ),
            "Exponent monotonicity reuses one supplied power-totality proof.",
        ),
        spec(
            "pow_two_seed_bundle_from_total",
            f"({total_seed}) -> (({two_two}) /\\ ({two_seven}))",
            (
                "pow_successor_compose_from_total",
                "pow_two_base_two_value_four",
            ),
            (
                "intro htotal",
                f"have htwo_exists : exists x. ({two_two_any})",
                "specialize htotal 2",
                "specialize htotal 2",
                "exact htotal",
                "cases htwo_exists",
                "have htwo_value : x = 4",
                "specialize pow_two_base_two_value_four x",
                "apply pow_two_base_two_value_four",
                "exact htwo_exists_witness",
                f"have htwo : {two_two}",
                "rewrite <- htwo_value",
                "rewrite <- htwo_value",
                "exact htwo_exists_witness",
                f"have hthree : {two_three}",
                "specialize pow_successor_compose_from_total 2",
                "specialize pow_successor_compose_from_total 2",
                "specialize pow_successor_compose_from_total 4",
                "specialize pow_successor_compose_from_total 8",
                "apply pow_successor_compose_from_total",
                "exact htotal",
                "exact htwo",
                "norm_num",
                f"have hfour : {two_four}",
                "specialize pow_successor_compose_from_total 2",
                "specialize pow_successor_compose_from_total 3",
                "specialize pow_successor_compose_from_total 8",
                "specialize pow_successor_compose_from_total 16",
                "apply pow_successor_compose_from_total",
                "exact htotal",
                "exact hthree",
                "norm_num",
                f"have hfive : {two_five}",
                "specialize pow_successor_compose_from_total 2",
                "specialize pow_successor_compose_from_total 4",
                "specialize pow_successor_compose_from_total 16",
                "specialize pow_successor_compose_from_total 32",
                "apply pow_successor_compose_from_total",
                "exact htotal",
                "exact hfour",
                "norm_num",
                f"have hsix : {two_six}",
                "specialize pow_successor_compose_from_total 2",
                "specialize pow_successor_compose_from_total 5",
                "specialize pow_successor_compose_from_total 32",
                "specialize pow_successor_compose_from_total 64",
                "apply pow_successor_compose_from_total",
                "exact htotal",
                "exact hfive",
                "symm",
                "rewrite PA6",
                "rewrite PA6",
                "rewrite PA5",
                *("rewrite PA4",) * 32,
                "rewrite PA3",
                *("rewrite PA4",) * 32,
                "rewrite PA3",
                "refl",
                f"have hseven : {two_seven}",
                "specialize pow_successor_compose_from_total 2",
                "specialize pow_successor_compose_from_total 6",
                "specialize pow_successor_compose_from_total 64",
                "specialize pow_successor_compose_from_total 128",
                "apply pow_successor_compose_from_total",
                "exact htotal",
                "exact hsix",
                "symm",
                "rewrite PA6",
                "rewrite PA6",
                "rewrite PA5",
                *("rewrite PA4",) * 64,
                "rewrite PA3",
                *("rewrite PA4",) * 64,
                "rewrite PA3",
                "refl",
                "split",
                "exact htwo",
                "exact hseven",
            ),
            "One totality premise yields the exact seeds 2^2=4 and 2^7=128.",
        ),
    )


__all__ = [
    "make_bertrand_power_total_candidate_theorems",
    "power_total_relation",
]
