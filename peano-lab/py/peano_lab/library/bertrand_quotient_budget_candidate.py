"""Subtraction-free quotient/complement budgets for the Bertrand B6 route.

For the canonical division equation ``2*n = 3*q + r``, the intended
complement is represented relationally by ``q+c = n``.  In fact, naturalness
of ``r`` already forces the stronger budget ``2*n <= 6*c``; the canonical
bound ``r < 3`` is preserved separately as part of the DivRem record.

All order, division, ceiling, and floor-square notation is expanded before
parsing.  This module is an isolated candidate factory and adds no kernel
constant or registered theorem.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.kernel.terms import parse_term_with_names

from .bertrand_ceil_sqrt_candidate import (
    ceil_div_six_relation,
    floor_sqrt_relation,
)


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


def _binder(tag: str, avoid: tuple[str, ...], stem: str) -> str:
    name = f"bqb_{stem}_{_identifier(tag, 'binder tag')}"
    if name in avoid:
        raise ValueError("generated Bertrand quotient-budget binder captures an argument")
    return name


def witness_le(left: str, right: str, *, tag: str) -> str:
    """Expand witness order ``left <= right`` for compound native terms."""

    variables = _term_names((left, "lower term"), (right, "upper term"))
    gap = _binder(tag, variables, "le_gap")
    return f"exists {gap}. {gap} + ({left}) = ({right})"


def double_triple_divrem_relation(
    dividend: str,
    quotient: str,
    remainder: str,
    *,
    tag: str,
) -> str:
    """Expand ``2*n = 3*q+r`` together with the strict bound ``r<3``."""

    variables = _term_names(
        (dividend, "division dividend"),
        (quotient, "division quotient"),
        (remainder, "division remainder"),
    )
    gap = _binder(tag, variables, "remainder_gap")
    return (
        f"((2 * ({dividend}) = 3 * ({quotient}) + ({remainder})) /\\ "
        f"exists {gap}. {gap} + S ({remainder}) = 3)"
    )


def quotient_complement_budget_relation(
    dividend: str,
    quotient: str,
    complement: str,
    *,
    tag: str,
) -> str:
    """Expand ``q+c=n`` and the B6 budget ``2*n <= 6*c``."""

    variables = _term_names(
        (dividend, "budget dividend"),
        (quotient, "budget quotient"),
        (complement, "budget complement"),
    )
    gap = _binder(tag, variables, "budget_gap")
    return (
        f"((({quotient}) + ({complement}) = ({dividend})) /\\ "
        f"exists {gap}. {gap} + 2 * ({dividend}) = 6 * ({complement}))"
    )


def make_bertrand_quotient_budget_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the next dependency-closed B6 quotient-budget tranche."""

    ceil_upper = ceil_div_six_relation("x", "e", tag="upper_source")

    strong_budget = quotient_complement_budget_relation(
        "n", "q", "c", tag="strong_result"
    )
    canonical_source = double_triple_divrem_relation(
        "n", "q", "r", tag="canonical_source"
    )
    canonical_base = quotient_complement_budget_relation(
        "n", "q", "c", tag="canonical_base"
    )
    canonical_result = quotient_complement_budget_relation(
        "n", "q", "c", tag="canonical_result"
    )

    bridge_floor = floor_sqrt_relation(
        "2 * n", "s", tag="complement_bridge_floor"
    )
    bridge_ceil = ceil_div_six_relation(
        "s * s", "e", tag="complement_bridge_ceil"
    )
    bridge_ec = witness_le("e", "c", tag="complement_bridge_ec")
    bridge_sum = witness_le("q + e", "n", tag="complement_bridge_sum")

    division_floor = floor_sqrt_relation(
        "2 * n", "s", tag="division_bridge_floor"
    )
    division_ceil = ceil_div_six_relation(
        "s * s", "e", tag="division_bridge_ceil"
    )
    division_source = double_triple_divrem_relation(
        "n", "q", "r", tag="division_bridge_source"
    )
    division_data = quotient_complement_budget_relation(
        "n", "q", "c", tag="division_bridge_data"
    )
    division_result = quotient_complement_budget_relation(
        "n", "q", "c", tag="division_bridge_result"
    )
    division_ec = witness_le("e", "c", tag="division_bridge_ec")
    division_sum = witness_le("q + e", "n", tag="division_bridge_sum")

    return (
        spec(
            "mul_le_cancel_left_nonzero",
            "forall c a b. ~(c = 0) -> "
            "(exists k. k + c * a = c * b) -> exists k. k + a = b",
            ("add_comm", "factor_difference", "mul_left_cancel_nonzero", "mul_add"),
            (
                "intro c",
                "intro a",
                "intro b",
                "intro hc",
                "intro hle",
                "cases hle",
                "have heq : c * b = c * a + x",
                "trans x + c * a",
                "symm",
                "exact hle_witness",
                "apply add_comm",
                "have hfactor : exists w. x = c * w",
                "specialize factor_difference c",
                "specialize factor_difference b",
                "specialize factor_difference a",
                "specialize factor_difference x",
                "apply factor_difference",
                "exact heq",
                "cases hfactor",
                "exists x1",
                "specialize mul_left_cancel_nonzero c",
                "specialize mul_left_cancel_nonzero (x1 + a)",
                "specialize mul_left_cancel_nonzero b",
                "apply mul_left_cancel_nonzero",
                "exact hc",
                "trans c * x1 + c * a",
                "apply mul_add",
                "rewrite <- hfactor_witness",
                "exact hle_witness",
            ),
            "Witness order cancels a common nonzero left multiplier.",
        ),
        spec(
            "three_mul_eq_two_mul_add_self",
            "forall a. 3 * a = 2 * a + a",
            ("mul_comm",),
            (
                "intro a",
                "trans a * 3",
                "apply mul_comm",
                "rewrite PA6",
                "congr",
                "apply mul_comm",
                "refl",
            ),
            "Left multiplication by three is twice the input plus the input.",
        ),
        spec(
            "ceil_div_six_le_of_upper",
            "forall x e c. "
            f"({ceil_upper}) -> (exists k. k + x = 6 * c) -> "
            "exists k. k + e = c",
            (
                "le_or_lt",
                "add_le_add_right",
                "mul_le_mul_left",
                "lt_of_lt_of_le",
                "lt_irrefl_expanded",
            ),
            (
                "intro x",
                "intro e",
                "intro c",
                "intro he",
                "intro hxc",
                "cases he",
                "specialize le_or_lt e",
                "specialize le_or_lt c",
                "cases le_or_lt",
                "exact le_or_lt_left",
                "exfalso",
                "have hx6 : exists k. k + (x + 6) = 6 * c + 6",
                "specialize add_le_add_right x",
                "specialize add_le_add_right (6 * c)",
                "specialize add_le_add_right 6",
                "apply add_le_add_right",
                "exact hxc",
                "have hscaled : exists k. k + 6 * S c = 6 * e",
                "apply mul_le_mul_left",
                "exact le_or_lt_right",
                "have hsucc : 6 * S c = 6 * c + 6",
                "apply PA6",
                "rewrite hsucc at hscaled",
                "have hfirst : exists k. k + S (6 * e) = 6 * c + 6",
                "specialize lt_of_lt_of_le (6 * e)",
                "specialize lt_of_lt_of_le (x + 6)",
                "specialize lt_of_lt_of_le (6 * c + 6)",
                "apply lt_of_lt_of_le",
                "exact he_right",
                "exact hx6",
                "have hloop : exists k. k + S (6 * e) = 6 * e",
                "specialize lt_of_lt_of_le (6 * e)",
                "specialize lt_of_lt_of_le (6 * c + 6)",
                "specialize lt_of_lt_of_le (6 * e)",
                "apply lt_of_lt_of_le",
                "exact hfirst",
                "exact hscaled",
                "specialize lt_irrefl_expanded (6 * e)",
                "apply lt_irrefl_expanded",
                "exact hloop",
            ),
            "Any six-multiple upper bound also bounds the ceiling quotient.",
        ),
        spec(
            "double_triple_remainder_complement_budget",
            "forall n q r. 2 * n = 3 * q + r -> "
            f"exists c. ({strong_budget})",
            (
                "mul_le_mul_right",
                "le_add_right",
                "le_trans",
                "succ_ne_zero",
                "mul_le_cancel_left_nonzero",
                "add_comm",
                "mul_add",
                "three_mul_eq_two_mul_add_self",
                "add_assoc",
                "add_left_cancel",
                "add_le_add_right",
                "mul_le_mul_left",
                "mul_assoc",
            ),
            (
                "intro n",
                "intro q",
                "intro r",
                "intro hdiv",
                "have hcoeff : exists k. k + 2 = 3",
                "exists 1",
                "norm_num",
                "have h23 : exists k. k + 2 * q = 3 * q",
                "specialize mul_le_mul_right 2",
                "specialize mul_le_mul_right 3",
                "specialize mul_le_mul_right q",
                "apply mul_le_mul_right",
                "exact hcoeff",
                "have h3r : exists k. k + 3 * q = 3 * q + r",
                "apply le_add_right",
                "have hpre : exists k. k + 2 * q = 3 * q + r",
                "specialize le_trans (2 * q)",
                "specialize le_trans (3 * q)",
                "specialize le_trans (3 * q + r)",
                "apply le_trans",
                "exact h23",
                "exact h3r",
                "have h2n : exists k. k + 2 * q = 2 * n",
                "rewrite hdiv",
                "exact hpre",
                "have htwo0 : ~(2 = 0)",
                "intro hzero",
                "specialize succ_ne_zero 1",
                "apply succ_ne_zero",
                "exact hzero",
                "have hqn : exists k. k + q = n",
                "specialize mul_le_cancel_left_nonzero 2",
                "specialize mul_le_cancel_left_nonzero q",
                "specialize mul_le_cancel_left_nonzero n",
                "apply mul_le_cancel_left_nonzero",
                "exact htwo0",
                "exact h2n",
                "cases hqn",
                "have hcomp : q + x = n",
                "trans x + q",
                "apply add_comm",
                "exact hqn_witness",
                "have hbalance : 2 * q + 2 * x = 3 * q + r",
                "trans 2 * (q + x)",
                "symm",
                "apply mul_add",
                "rewrite hcomp",
                "exact hdiv",
                "have hthreeq : 3 * q = 2 * q + q",
                "apply three_mul_eq_two_mul_add_self",
                "have hbalance2 : 2 * q + 2 * x = 2 * q + (q + r)",
                "trans 3 * q + r",
                "exact hbalance",
                "rewrite hthreeq",
                "apply add_assoc",
                "have hreduce : 2 * x = q + r",
                "specialize add_left_cancel (2 * q)",
                "specialize add_left_cancel (2 * x)",
                "specialize add_left_cancel (q + r)",
                "apply add_left_cancel",
                "exact hbalance2",
                "have hq2c : exists k. k + q = 2 * x",
                "exists r",
                "trans q + r",
                "apply add_comm",
                "symm",
                "exact hreduce",
                "have hplus : exists k. k + (q + x) = 2 * x + x",
                "specialize add_le_add_right q",
                "specialize add_le_add_right (2 * x)",
                "specialize add_le_add_right x",
                "apply add_le_add_right",
                "exact hq2c",
                "have hthreex : 3 * x = 2 * x + x",
                "apply three_mul_eq_two_mul_add_self",
                "have hn3c : exists k. k + n = 3 * x",
                "rewrite <- hcomp",
                "rewrite hthreex",
                "exact hplus",
                "have hscaled : exists k. k + 2 * n = 2 * (3 * x)",
                "apply mul_le_mul_left",
                "exact hn3c",
                "have hfactor : 2 * (3 * x) = 6 * x",
                "trans (2 * 3) * x",
                "symm",
                "apply mul_assoc",
                "congr",
                "norm_num",
                "refl",
                "exists x",
                "split",
                "exact hcomp",
                "rewrite hfactor at hscaled",
                "exact hscaled",
            ),
            "The equation 2*n=3*q+r constructively yields q+c=n and 2*n<=6*c.",
        ),
        spec(
            "canonical_double_triple_remainder_complement_budget",
            "forall n q r. "
            f"({canonical_source}) -> exists c. "
            f"(({canonical_result}) /\\ "
            "exists bqb_remainder_gap_canonical_preserved. "
            "bqb_remainder_gap_canonical_preserved + S r = 3)",
            ("double_triple_remainder_complement_budget",),
            (
                "intro n",
                "intro q",
                "intro r",
                "intro hcanonical",
                "cases hcanonical",
                f"have hbase : exists c. ({canonical_base})",
                "specialize double_triple_remainder_complement_budget n",
                "specialize double_triple_remainder_complement_budget q",
                "specialize double_triple_remainder_complement_budget r",
                "apply double_triple_remainder_complement_budget",
                "exact hcanonical_left",
                "cases hbase",
                "exists x",
                "split",
                "exact hbase_witness",
                "exact hcanonical_right",
            ),
            "Canonical remainder data yields and preserves the complement budget.",
        ),
        spec(
            "floor_ceil_complement_budget",
            "forall n q s e c. "
            f"({bridge_floor}) -> ({bridge_ceil}) -> q + c = n -> "
            "(exists k. k + 2 * n = 6 * c) -> "
            f"(({bridge_ec}) /\\ ({bridge_sum}))",
            ("le_trans", "ceil_div_six_le_of_upper", "add_le_add_left"),
            (
                "intro n",
                "intro q",
                "intro s",
                "intro e",
                "intro c",
                "intro hfloor",
                "intro hceil",
                "intro hcomp",
                "intro hbudget",
                "cases hfloor",
                "have hsquare : exists k. k + s * s = 6 * c",
                "specialize le_trans (s * s)",
                "specialize le_trans (2 * n)",
                "specialize le_trans (6 * c)",
                "apply le_trans",
                "exact hfloor_left",
                "exact hbudget",
                "have hec : exists k. k + e = c",
                "specialize ceil_div_six_le_of_upper (s * s)",
                "specialize ceil_div_six_le_of_upper e",
                "specialize ceil_div_six_le_of_upper c",
                "apply ceil_div_six_le_of_upper",
                "exact hceil",
                "exact hsquare",
                "have hsum : exists k. k + (q + e) = q + c",
                "specialize add_le_add_left e",
                "specialize add_le_add_left c",
                "specialize add_le_add_left q",
                "apply add_le_add_left",
                "exact hec",
                "split",
                "exact hec",
                "rewrite <- hcomp",
                "exact hsum",
            ),
            "Floor-square and ceiling budgets imply e<=c and q+e<=n.",
        ),
        spec(
            "floor_ceil_division_budget",
            "forall n q r s e. "
            f"({division_floor}) -> ({division_ceil}) -> "
            f"({division_source}) -> exists c. "
            f"((({division_result}) /\\ "
            f"(({division_ec}) /\\ ({division_sum}))) /\\ "
            "exists bqb_remainder_gap_division_bridge_preserved. "
            "bqb_remainder_gap_division_bridge_preserved + S r = 3)",
            (
                "canonical_double_triple_remainder_complement_budget",
                "floor_ceil_complement_budget",
            ),
            (
                "intro n",
                "intro q",
                "intro r",
                "intro s",
                "intro e",
                "intro hfloor",
                "intro hceil",
                "intro hcanonical",
                f"have hdata : exists c. (({division_data}) /\\ "
                "exists bqb_remainder_gap_division_bridge_data. "
                "bqb_remainder_gap_division_bridge_data + S r = 3)",
                "specialize canonical_double_triple_remainder_complement_budget n",
                "specialize canonical_double_triple_remainder_complement_budget q",
                "specialize canonical_double_triple_remainder_complement_budget r",
                "apply canonical_double_triple_remainder_complement_budget",
                "exact hcanonical",
                "cases hdata",
                "cases hdata_witness",
                "cases hdata_witness_left",
                "have hbridge : (exists k. k + e = x) /\\ "
                "exists k. k + (q + e) = n",
                "specialize floor_ceil_complement_budget n",
                "specialize floor_ceil_complement_budget q",
                "specialize floor_ceil_complement_budget s",
                "specialize floor_ceil_complement_budget e",
                "specialize floor_ceil_complement_budget x",
                "apply floor_ceil_complement_budget",
                "exact hfloor",
                "exact hceil",
                "exact hdata_witness_left_left",
                "exact hdata_witness_left_right",
                "exists x",
                "split",
                "split",
                "exact hdata_witness_left",
                "exact hbridge",
                "exact hdata_witness_right",
            ),
            "Raw canonical division data closes both B6 quotient-budget inequalities.",
        ),
    )


__all__ = [
    "double_triple_divrem_relation",
    "make_bertrand_quotient_budget_candidate_theorems",
    "quotient_complement_budget_relation",
    "witness_le",
]
