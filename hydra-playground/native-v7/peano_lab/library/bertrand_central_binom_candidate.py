"""Conservative central-binomial wrappers over relational Choose.

``CentralBinom(n,z)`` is authoring-only notation for ``Choose(n + n,n,z)``.
The helper below expands that notation completely into ordinary first-order
Peano arithmetic before parsing.  This module creates no trusted primitive,
authority enrollment, or checked-use grant.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.kernel.terms import Add, parse_term_in_context, pretty_term
from peano_lab.library.bertrand_choose_foundation_candidate import (
    _choose_relation_term,
    _identifier,
)


CENTRAL_BINOM_EXISTS = "central_binom_exists"
CENTRAL_BINOM_FUNCTIONAL = "central_binom_functional"
CENTRAL_BINOM_POSITIVE = "central_binom_positive"


def _central_binom_relation_term(
    n: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    """Expand ``Choose(n + n,n,value)`` with hygienic private binders."""

    if not isinstance(variables, tuple):
        raise ValueError("central-binomial variables must be a tuple")
    context = [
        _identifier(variable, "central-binomial context variable")
        for variable in variables
    ]
    if len(set(context)) != len(context):
        raise ValueError("central-binomial context variables must be distinct")

    parsed_terms = []
    for source, label in (
        (n, "central-binomial index"),
        (value, "central-binomial value"),
    ):
        if not isinstance(source, str) or not source:
            raise ValueError(f"{label} must be a nonempty Peano term")
        try:
            parsed_terms.append(parse_term_in_context(source, context))
        except ValueError as exc:
            raise ValueError(f"{label} must be a Peano term: {exc}") from None

    index_term, value_term = parsed_terms
    rendered_index = pretty_term(index_term, context).replace("·", "*")
    rendered_value = pretty_term(value_term, context).replace("·", "*")
    doubled_index = pretty_term(Add(index_term, index_term), context).replace(
        "·", "*"
    )
    return _choose_relation_term(
        doubled_index,
        rendered_index,
        rendered_value,
        tag=tag,
        variables=variables,
    )


def make_bertrand_central_binom_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build existence, functionality, and positivity wrappers."""

    exists_relation = _central_binom_relation_term(
        "n",
        "z",
        tag="bcbe_result",
        variables=("n", "z"),
    )
    functional_variables = ("n", "x", "y")
    functional_left = _central_binom_relation_term(
        "n",
        "x",
        tag="bcbf_left",
        variables=functional_variables,
    )
    functional_right = _central_binom_relation_term(
        "n",
        "y",
        tag="bcbf_right",
        variables=functional_variables,
    )
    positive_relation = _central_binom_relation_term(
        "n",
        "z",
        tag="bcbp_source",
        variables=("n", "z"),
    )

    return (
        spec(
            CENTRAL_BINOM_EXISTS,
            f"forall n. exists z. ({exists_relation})",
            ("choose_exists",),
            (
                "intro n",
                "specialize choose_exists (n + n)",
                "specialize choose_exists n",
                "exact choose_exists",
            ),
            "Every row has a relational central-binomial value.",
        ),
        spec(
            CENTRAL_BINOM_FUNCTIONAL,
            "forall n x y. "
            f"({functional_left}) -> ({functional_right}) -> x = y",
            ("choose_functional",),
            (
                "intro n",
                "intro x",
                "intro y",
                "intro hleft",
                "intro hright",
                "specialize choose_functional (n + n)",
                "specialize choose_functional n",
                "specialize choose_functional x",
                "specialize choose_functional y",
                "apply choose_functional",
                "exact hleft",
                "exact hright",
            ),
            "The relational central-binomial value is unique.",
        ),
        spec(
            CENTRAL_BINOM_POSITIVE,
            f"forall n z. ({positive_relation}) -> exists p. z = S p",
            ("choose_positive",),
            (
                "intro n",
                "intro z",
                "intro hcentral",
                "specialize choose_positive (n + n)",
                "specialize choose_positive n",
                "specialize choose_positive z",
                "apply choose_positive",
                "exists n",
                "refl",
                "exact hcentral",
            ),
            "Every relational central-binomial value is a successor.",
        ),
    )


__all__ = ["make_bertrand_central_binom_candidate_theorems"]
