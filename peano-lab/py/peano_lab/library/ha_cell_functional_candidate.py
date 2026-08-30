"""Constructive functionality for exact D06 tagged cells.

This ``HA-K3-PAIR-1`` tranche transfers the private exact-D01 pair
injectivity theorem through the single successor tag in RFC D06.  The three
results expose joint, head, and tail functionality while keeping the D06
relation literally expanded in every statement.

The candidates are dependency-curried, unregistered, and unadmitted.  Their
proofs use only PA2 successor injectivity and the private constructive pair
shell/injectivity layer; they use no division, remainder, beta coding, CRT,
classical logic, or DNE.
"""

from __future__ import annotations

from typing import Any, Callable


def _pair_polynomial(left: str, right: str) -> str:
    return f"({left} + {right}) * S ({left} + {right}) + ({right} + {right})"


def make_ha_cell_functional_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the exact D06 joint and projected functionality candidates."""

    pair1 = _pair_polynomial("head1", "tail1")
    pair2 = _pair_polynomial("head2", "tail2")
    premises = (
        f"code = S ({pair1}) -> code = S ({pair2}) -> "
    )

    return (
        spec(
            "cell_functional",
            "forall code head1 tail1 head2 tail2. "
            f"{premises}head1 = head2 /\\ tail1 = tail2",
            ("pair_code_injective",),
            (
                "intro code",
                "intro head1",
                "intro tail1",
                "intro head2",
                "intro tail2",
                "intro hcell1",
                "intro hcell2",
                f"have hpairs : {pair1} = {pair2}",
                "apply PA2",
                "trans code",
                "symm",
                "exact hcell1",
                "exact hcell2",
                f"specialize pair_code_injective {pair1}",
                "specialize pair_code_injective head1",
                "specialize pair_code_injective tail1",
                "specialize pair_code_injective head2",
                "specialize pair_code_injective tail2",
                "apply pair_code_injective",
                "refl",
                "exact hpairs",
            ),
            "Two exact D06 witnesses for one cell code have equal heads and "
            "equal tails constructively.",
        ),
        spec(
            "cell_head_functional",
            "forall code head1 tail1 head2 tail2. "
            f"{premises}head1 = head2",
            ("cell_functional",),
            (
                "intro code",
                "intro head1",
                "intro tail1",
                "intro head2",
                "intro tail2",
                "intro hcell1",
                "intro hcell2",
                "specialize cell_functional code",
                "specialize cell_functional head1",
                "specialize cell_functional tail1",
                "specialize cell_functional head2",
                "specialize cell_functional tail2",
                "have hcomponents : head1 = head2 /\\ tail1 = tail2",
                "apply cell_functional",
                "exact hcell1",
                "exact hcell2",
                "cases hcomponents",
                "exact hcomponents_left",
            ),
            "Project joint exact-D06 functionality to the cell head.",
        ),
        spec(
            "cell_tail_functional",
            "forall code head1 tail1 head2 tail2. "
            f"{premises}tail1 = tail2",
            ("cell_functional",),
            (
                "intro code",
                "intro head1",
                "intro tail1",
                "intro head2",
                "intro tail2",
                "intro hcell1",
                "intro hcell2",
                "specialize cell_functional code",
                "specialize cell_functional head1",
                "specialize cell_functional tail1",
                "specialize cell_functional head2",
                "specialize cell_functional tail2",
                "have hcomponents : head1 = head2 /\\ tail1 = tail2",
                "apply cell_functional",
                "exact hcell1",
                "exact hcell2",
                "cases hcomponents",
                "exact hcomponents_right",
            ),
            "Project joint exact-D06 functionality to the cell tail.",
        ),
    )


__all__ = ["make_ha_cell_functional_candidate_theorems"]
