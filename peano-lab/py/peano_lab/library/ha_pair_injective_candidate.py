"""Constructive injectivity for the doubled-Cantor pair relation.

This final ``HA-K3-PAIR-1`` tranche turns strict separation of distinct
doubled-triangular shells into literal component injectivity.  The exact D01
relation is expanded in the statement; ``PairCode`` remains documentation
only.  Both candidates are dependency-curried, unregistered, and unadmitted.

The proof stays inside K0--K2 arithmetic.  In particular it uses neither
division nor remainder, beta coding, CRT, classical logic, nor DNE.
"""

from __future__ import annotations

from typing import Any, Callable


def make_ha_pair_injective_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build doubling injectivity and exact D01 pair injectivity."""

    pair1 = "(l1 + r1) * S (l1 + r1) + (r1 + r1)"
    pair2 = "(l2 + r2) * S (l2 + r2) + (r2 + r2)"

    return (
        spec(
            "double_add_injective",
            "forall a b. a + a = b + b -> a = b",
            (
                "mul_left_cancel_nonzero",
                "succ_ne_zero",
                "mul_succ_left",
                "mul_zero_left",
                "zero_add",
            ),
            (
                "intro a",
                "intro b",
                "intro h",
                "have htwoa : 2 * a = a + a",
                "simp [mul_succ_left, mul_zero_left, zero_add]",
                "have htwob : 2 * b = b + b",
                "simp [mul_succ_left, mul_zero_left, zero_add]",
                "have hmul : 2 * a = 2 * b",
                "trans a + a",
                "exact htwoa",
                "trans b + b",
                "exact h",
                "symm",
                "exact htwob",
                "have htwo : ~(2 = 0)",
                "specialize succ_ne_zero 1",
                "exact succ_ne_zero",
                "specialize mul_left_cancel_nonzero 2",
                "specialize mul_left_cancel_nonzero a",
                "specialize mul_left_cancel_nonzero b",
                "apply mul_left_cancel_nonzero",
                "exact htwo",
                "exact hmul",
            ),
            "Doubling by self-addition is injective over naturals.",
        ),
        spec(
            "pair_code_injective",
            f"forall code l1 r1 l2 r2. code = {pair1} -> "
            f"code = {pair2} -> l1 = l2 /\\ r1 = r2",
            (
                "double_add_injective",
                "pair_code_shell_separated",
                "lt_trichotomy",
                "lt_irrefl_expanded",
                "add_left_cancel",
                "add_right_cancel",
            ),
            (
                "intro code",
                "intro l1",
                "intro r1",
                "intro l2",
                "intro r2",
                "intro hpair1",
                "intro hpair2",
                "specialize lt_trichotomy (l1 + r1)",
                "specialize lt_trichotomy (l2 + r2)",
                "cases lt_trichotomy",
                "rewrite <- lt_trichotomy_left at hpair2",
                "rewrite <- lt_trichotomy_left at hpair2",
                "have hdouble : r1 + r1 = r2 + r2",
                "specialize add_left_cancel "
                "((l1 + r1) * S (l1 + r1))",
                "specialize add_left_cancel (r1 + r1)",
                "specialize add_left_cancel (r2 + r2)",
                "apply add_left_cancel",
                "trans code",
                "symm",
                "exact hpair1",
                "exact hpair2",
                "have hright : r1 = r2",
                "specialize double_add_injective r1",
                "specialize double_add_injective r2",
                "apply double_add_injective",
                "exact hdouble",
                "have hleft : l1 = l2",
                "rewrite hright at lt_trichotomy_left",
                "specialize add_right_cancel l1",
                "specialize add_right_cancel l2",
                "specialize add_right_cancel r2",
                "apply add_right_cancel",
                "exact lt_trichotomy_left",
                "split",
                "exact hleft",
                "exact hright",
                "cases lt_trichotomy_right",
                "exfalso",
                "specialize lt_irrefl_expanded code",
                "apply lt_irrefl_expanded",
                "specialize pair_code_shell_separated code",
                "specialize pair_code_shell_separated l1",
                "specialize pair_code_shell_separated r1",
                "specialize pair_code_shell_separated code",
                "specialize pair_code_shell_separated l2",
                "specialize pair_code_shell_separated r2",
                "apply pair_code_shell_separated",
                "exact hpair1",
                "exact hpair2",
                "exact lt_trichotomy_right_left",
                "exfalso",
                "specialize lt_irrefl_expanded code",
                "apply lt_irrefl_expanded",
                "specialize pair_code_shell_separated code",
                "specialize pair_code_shell_separated l2",
                "specialize pair_code_shell_separated r2",
                "specialize pair_code_shell_separated code",
                "specialize pair_code_shell_separated l1",
                "specialize pair_code_shell_separated r1",
                "apply pair_code_shell_separated",
                "exact hpair2",
                "exact hpair1",
                "exact lt_trichotomy_right_right",
            ),
            "The exact D01 doubled-Cantor relation determines both pair "
            "components constructively.",
        ),
    )


__all__ = ["make_ha_pair_injective_candidate_theorems"]
