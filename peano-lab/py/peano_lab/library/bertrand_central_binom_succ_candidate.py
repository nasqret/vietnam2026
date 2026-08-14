"""Successor support for the relational central-binomial surface.

The first row transports the upper index of an expanded ``Choose`` relation
along an equality.  The second normalizes ``CentralBinom(S n,d)`` through
that transport and applies Pascal recurrence plus odd-row symmetry.  Every
authoring abbreviation expands before parsing; this module adds no trusted
primitive, authority enrollment, or checked-use grant.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.bertrand_central_binom_candidate import (
    _central_binom_relation_term,
)
from peano_lab.library.bertrand_choose_foundation_candidate import (
    _choose_relation_term,
)


CHOOSE_UPPER_EQ_TRANSPORT = "choose_upper_eq_transport"
CENTRAL_BINOM_SUCC_DOUBLE_MIDDLE = "central_binom_succ_double_middle"


def make_bertrand_central_binom_succ_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build upper-index transport and the additive successor law."""

    transport_variables = ("n", "m", "k", "z")
    transport_source = _choose_relation_term(
        "n",
        "k",
        "z",
        tag="bcuet_source",
        variables=transport_variables,
    )
    transport_target = _choose_relation_term(
        "m",
        "k",
        "z",
        tag="bcuet_target",
        variables=transport_variables,
    )
    transport_script = (
        "intro n",
        "intro m",
        "intro k",
        "intro z",
        "intro heq",
        "intro hchoose",
        "rewrite heq at hchoose",
        "rewrite heq at hchoose",
        "rewrite heq at hchoose",
        "rewrite heq at hchoose",
        "rewrite heq at hchoose",
        "rewrite heq at hchoose",
        "rewrite heq at hchoose",
        "rewrite heq at hchoose",
        "rewrite heq at hchoose",
        "exact hchoose",
    )

    successor_variables = ("n", "d")
    successor = _central_binom_relation_term(
        "S n",
        "d",
        tag="bcbsdm_successor",
        variables=successor_variables,
    )
    normalized = _choose_relation_term(
        "S (S (n + n))",
        "S n",
        "d",
        tag="bcbsdm_normalized",
        variables=successor_variables,
    )
    middle_variables = ("n", "d", "m")
    middle = _choose_relation_term(
        "S (n + n)",
        "n",
        "m",
        tag="bcbsdm_middle",
        variables=middle_variables,
    )
    mirror = _choose_relation_term(
        "S (n + n)",
        "S n",
        "r",
        tag="bcbsdm_mirror",
        variables=("n", "d", "m", "r"),
    )
    successor_script = (
        "intro n",
        "intro d",
        "intro hsuccessor",
        "have hupper : S n + S n = S (S (n + n))",
        "trans S (n + S n)",
        "specialize add_succ_left n",
        "specialize add_succ_left (S n)",
        "apply add_succ_left",
        "congr",
        "apply PA4",
        f"have hnormalized : {normalized}",
        "specialize choose_upper_eq_transport (S n + S n)",
        "specialize choose_upper_eq_transport (S (S (n + n)))",
        "specialize choose_upper_eq_transport (S n)",
        "specialize choose_upper_eq_transport d",
        "apply choose_upper_eq_transport",
        "exact hupper",
        "exact hsuccessor",
        f"have hmiddle_exists : exists m. ({middle})",
        "specialize choose_exists (S (n + n))",
        "specialize choose_exists n",
        "exact choose_exists",
        "cases hmiddle_exists",
        f"have hmirror_exists : exists r. ({mirror})",
        "specialize choose_exists (S (n + n))",
        "specialize choose_exists (S n)",
        "exact choose_exists",
        "cases hmirror_exists",
        "have hsym : x = x1",
        "specialize choose_symmetry (S (n + n))",
        "specialize choose_symmetry n",
        "specialize choose_symmetry (S n)",
        "specialize choose_symmetry x",
        "specialize choose_symmetry x1",
        "apply choose_symmetry",
        "apply PA4",
        "exact hmiddle_exists_witness",
        "exact hmirror_exists_witness",
        "have hsum : d = x + x1",
        "specialize choose_succ_succ (S (n + n))",
        "specialize choose_succ_succ n",
        "specialize choose_succ_succ x",
        "specialize choose_succ_succ x1",
        "specialize choose_succ_succ d",
        "apply choose_succ_succ",
        "exact hmiddle_exists_witness",
        "exact hmirror_exists_witness",
        "exact hnormalized",
        "exists x",
        "split",
        "exact hmiddle_exists_witness",
        "trans x + x1",
        "exact hsum",
        "rewrite <- hsym",
        "refl",
    )

    return (
        spec(
            CHOOSE_UPPER_EQ_TRANSPORT,
            "forall n m k z. n = m -> "
            f"({transport_source}) -> ({transport_target})",
            (),
            transport_script,
            "Choose is invariant under equality of its upper index.",
        ),
        spec(
            CENTRAL_BINOM_SUCC_DOUBLE_MIDDLE,
            "forall n d. "
            f"({successor}) -> exists m. (({middle}) /\\ d = m + m)",
            (
                "add_succ_left",
                "choose_exists",
                "choose_symmetry",
                "choose_succ_succ",
                CHOOSE_UPPER_EQ_TRANSPORT,
            ),
            successor_script,
            "A successor central binomial is twice its odd-row middle value.",
        ),
    )


__all__ = ["make_bertrand_central_binom_succ_candidate_theorems"]
