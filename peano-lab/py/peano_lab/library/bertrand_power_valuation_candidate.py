"""Constructive bounded prime-power valuation candidates for Bertrand.

The object language has no exponentiation or valuation symbol.  This module
therefore expands ``p^e | a`` through the already checked relational ``Pow``
surface and ordinary divisibility witnesses.  A bounded valuation is the
greatest exponent, inside an explicit natural bound, whose relational power
divides the value.  The bound makes the construction intuitionistically
finite; no excluded-middle or unbounded minimisation principle is used.

This is an isolated, unregistered authoring layer.  Its theorem bodies must be
curried over their declared dependencies and accepted by the independent
kernel before they can enter Alpha.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_map_candidate import prime
from .finite_fold_surface import power_relation


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


def _variables(*labelled: tuple[str, str]) -> tuple[str, ...]:
    return tuple(_identifier(value, label) for value, label in labelled)


def _binders(tag: str, avoid: tuple[str, ...], stems: tuple[str, ...]) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"bpv_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(avoid):
        raise ValueError("generated power-valuation binder captures an argument")
    return names


def at_most(left: str, right: str, *, tag: str) -> str:
    """Expand the native witness relation ``left <= right``."""

    variables = _variables((left, "lower term"), (right, "upper term"))
    (gap,) = _binders(tag, variables, ("gap",))
    return f"exists {gap}. {gap} + {left} = {right}"


def divides(divisor: str, value: str, *, tag: str) -> str:
    """Expand ``divisor | value`` as an ordinary factor witness."""

    variables = _variables((divisor, "divisor"), (value, "value"))
    (factor,) = _binders(tag, variables, ("factor",))
    return f"exists {factor}. {value} = {divisor} * {factor}"


def power_divides(base: str, exponent: str, value: str, *, tag: str) -> str:
    """Expand ``exists r, Pow(base,exponent,r) and r | value``."""

    variables = _variables(
        (base, "power base"),
        (exponent, "power exponent"),
        (value, "dividend"),
    )
    (result,) = _binders(tag, variables, ("result",))
    power = power_relation(base, exponent, result, tag=f"{tag}_power")
    result_divides = divides(result, value, tag=f"{tag}_divides")
    return f"exists {result}. (({power}) /\\ ({result_divides}))"


def bounded_power_valuation(
    base: str,
    value: str,
    bound: str,
    exponent: str,
    *,
    tag: str,
) -> str:
    """Expand the greatest power-divisor exponent below ``bound``.

    This is deliberately a bounded relation.  A later Bertrand tranche will
    prove that, for prime ``base`` and nonzero ``value``, the canonical bound
    ``value`` also yields the usual unbounded successor-nondivisibility
    characterization.
    """

    variables = _variables(
        (base, "power base"),
        (value, "value"),
        (bound, "exponent bound"),
        (exponent, "valuation exponent"),
    )
    (candidate,) = _binders(tag, variables, ("candidate",))
    exponent_bound = at_most(exponent, bound, tag=f"{tag}_exponent_bound")
    exponent_divides = power_divides(base, exponent, value, tag=f"{tag}_selected")
    candidate_bound = at_most(candidate, bound, tag=f"{tag}_candidate_bound")
    candidate_divides = power_divides(base, candidate, value, tag=f"{tag}_candidate")
    candidate_below = at_most(candidate, exponent, tag=f"{tag}_maximal")
    return (
        f"(({exponent_bound}) /\\ ({exponent_divides})) /\\ "
        f"forall {candidate}. ({candidate_bound}) -> "
        f"({candidate_divides}) -> ({candidate_below})"
    )


def power_valuation(base: str, value: str, exponent: str, *, tag: str) -> str:
    """Use the value itself as the canonical finite exponent bound."""

    return bounded_power_valuation(base, value, value, exponent, tag=tag)


def prime_power_valuation(base: str, value: str, exponent: str, *, tag: str) -> str:
    """Expand the intended nonzero, prime-base valuation domain and graph."""

    _variables(
        (base, "prime base"),
        (value, "nonzero value"),
        (exponent, "valuation exponent"),
    )
    domain = f"(({prime(base, tag=f'{tag}_prime')}) /\\ ~({value} = 0))"
    graph = power_valuation(base, value, exponent, tag=f"{tag}_graph")
    return f"({domain}) /\\ ({graph})"


# The public helpers above accept identifiers only.  Candidate proofs need two
# module-owned compound exponents (``0`` and ``S B``) while inspecting an
# induction boundary.  These private builders mirror the frozen Pow expansion
# and never interpolate caller-provided term text.
def _beta_at_terms(code: str, scale: str, index: str, value: str, *, tag: str) -> str:
    modulus = f"S ((S ({index})) * {scale})"
    return (
        f"((exists bpvi_h_{tag}. bpvi_h_{tag} + S ({value}) = {modulus}) /\\ "
        f"exists bpvi_q_{tag}. {code} = bpvi_q_{tag} * {modulus} + ({value}))"
    )


def _power_terms(base: str, exponent: str, result: str, *, tag: str) -> str:
    code = f"bpvi_b_{tag}"
    scale = f"bpvi_c_{tag}"
    i = f"bpvi_i_{tag}"
    repeat_bound = f"exists bpvi_repeat_gap_{tag}. bpvi_repeat_gap_{tag} + S {i} = {exponent}"
    repeated = (
        f"forall {i}. ({repeat_bound}) -> "
        f"({_beta_at_terms(code, scale, i, base, tag=f'{tag}_repeat')})"
    )
    u = f"bpvi_u_{tag}"
    v = f"bpvi_v_{tag}"
    j = f"bpvi_j_{tag}"
    factor = f"bpvi_factor_{tag}"
    partial = f"bpvi_partial_{tag}"
    successor = f"bpvi_successor_{tag}"
    product_bound = (
        f"exists bpvi_product_gap_{tag}. "
        f"bpvi_product_gap_{tag} + S {j} = {exponent}"
    )
    product = (
        f"exists {u} {v}. "
        f"(({_beta_at_terms(u, v, '0', '1', tag=f'{tag}_start')}) /\\ "
        f"(({_beta_at_terms(u, v, exponent, result, tag=f'{tag}_terminal')}) /\\ "
        f"forall {j}. ({product_bound}) -> "
        f"exists {factor} {partial} {successor}. "
        f"(({_beta_at_terms(code, scale, j, factor, tag=f'{tag}_factor')}) /\\ "
        f"(({_beta_at_terms(u, v, j, partial, tag=f'{tag}_partial')}) /\\ "
        f"(({_beta_at_terms(u, v, f'S {j}', successor, tag=f'{tag}_successor')}) /\\ "
        f"{successor} = {partial} * {factor})))))"
    )
    return f"exists {code} {scale}. (({repeated}) /\\ ({product}))"


def _power_divides_terms(base: str, exponent: str, value: str, *, tag: str) -> str:
    result = f"bpvi_result_{tag}"
    factor = f"bpvi_divisor_factor_{tag}"
    return (
        f"exists {result}. (({_power_terms(base, exponent, result, tag=f'{tag}_power')}) /\\ "
        f"exists {factor}. {value} = {result} * {factor})"
    )


def make_bertrand_power_valuation_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the first dependency-ordered Bertrand valuation tranche."""

    decision_property = power_divides("p", "e", "a", tag="decision")
    zero_property = power_divides("p", "z", "a", tag="zero")

    search_property = power_divides("p", "f", "a", tag="search_property")
    search_boundary = power_divides("p", "B", "a", tag="search_boundary")
    search_selected = power_divides("p", "e", "a", tag="search_selected")
    search_candidate = power_divides("p", "f", "a", tag="search_candidate")
    search_none = (
        "forall f. "
        f"({at_most('f', 'B', tag='search_none_bound')}) -> "
        f"~({search_property})"
    )
    search_maximum = (
        "exists e. (("
        f"{at_most('e', 'B', tag='search_selected_bound')}) /\\ "
        f"({search_selected})) /\\ forall f. "
        f"({at_most('f', 'B', tag='search_candidate_bound')}) -> "
        f"({search_candidate}) -> "
        f"({at_most('f', 'e', tag='search_maximal')})"
    )

    bounded = bounded_power_valuation("p", "a", "B", "e", tag="bounded")
    canonical = power_valuation("p", "a", "e", tag="canonical")
    canonical_left = power_valuation("p", "a", "e", tag="functional_left")
    canonical_right = power_valuation("p", "a", "f", tag="functional_right")
    canonical_property = power_divides("p", "e", "a", tag="projection")
    canonical_candidate = power_divides("p", "f", "a", tag="dominates_candidate")
    prime_canonical = prime_power_valuation("p", "a", "e", tag="prime_canonical")
    prime_canonical_left = prime_power_valuation(
        "p", "a", "e", tag="prime_functional_left"
    )
    prime_canonical_right = prime_power_valuation(
        "p", "a", "f", tag="prime_functional_right"
    )
    prime_p = prime("p", tag="prime_total_domain")

    return (
        spec(
            "power_divides_decidable",
            f"forall p e a. ({decision_property}) \\/ ~({decision_property})",
            ("pow_exists", "multiple_decidable", "pow_functional"),
            (
                "intro p",
                "intro e",
                "intro a",
                f"have hpower : exists r. ({power_relation('p', 'e', 'r', tag='decision_witness')})",
                "specialize pow_exists p",
                "specialize pow_exists e",
                "exact pow_exists",
                "cases hpower",
                "have hdiv : (exists q. a = x * q) \\/ ~(exists q. a = x * q)",
                "specialize multiple_decidable x",
                "specialize multiple_decidable a",
                "exact multiple_decidable",
                "cases hdiv",
                "left",
                "exists x",
                "split",
                "exact hpower_witness",
                "exact hdiv_left",
                "right",
                "intro hother",
                "cases hother",
                "cases hother_witness",
                "have heq : x1 = x",
                "specialize pow_functional p",
                "specialize pow_functional e",
                "specialize pow_functional x1",
                "specialize pow_functional x",
                "apply pow_functional",
                "exact hother_witness_left",
                "exact hpower_witness",
                "apply hdiv_right",
                "rewrite heq at hother_witness_right",
                "exact hother_witness_right",
            ),
            "Divisibility by a relational power is constructively decidable.",
        ),
        spec(
            "power_divides_zero",
            f"forall p a z. z = 0 -> ({zero_property})",
            ("pow_exists", "pow_zero", "one_multiple"),
            (
                "intro p",
                "intro a",
                "intro z",
                "intro hz",
                f"have hpower : exists r. ({power_relation('p', 'z', 'r', tag='zero_witness')})",
                "specialize pow_exists p",
                "specialize pow_exists z",
                "exact pow_exists",
                "cases hpower",
                "have hr : x = 1",
                "specialize pow_zero p",
                "specialize pow_zero z",
                "specialize pow_zero x",
                "apply pow_zero",
                "exact hz",
                "exact hpower_witness",
                "exists x",
                "split",
                "exact hpower_witness",
                "rewrite hr",
                "specialize one_multiple a",
                "exact one_multiple",
            ),
            "The zeroth relational power divides every natural.",
        ),
        spec(
            "bounded_power_valuation_search",
            f"forall B p a. ({search_none}) \\/ ({search_maximum})",
            (
                "power_divides_decidable",
                "le_zero",
                "le_refl",
                "le_eq_or_lt",
                "le_of_succ_le_succ",
                "le_succ",
            ),
            (
                "induction B",
                "intro p",
                "intro a",
                f"have hboundary : ({_power_divides_terms('p', '0', 'a', tag='search_base_boundary')}) \\/ ~({_power_divides_terms('p', '0', 'a', tag='search_base_boundary')})",
                "specialize power_divides_decidable p",
                "specialize power_divides_decidable 0",
                "specialize power_divides_decidable a",
                "exact power_divides_decidable",
                "cases hboundary",
                "right",
                "exists 0",
                "split",
                "split",
                "specialize le_refl 0",
                "exact le_refl",
                "exact hboundary_left",
                "intro f",
                "intro hf",
                "intro hproperty",
                "have hf0 : f = 0",
                "specialize le_zero f",
                "apply le_zero",
                "exact hf",
                "rewrite hf0",
                "specialize le_refl 0",
                "exact le_refl",
                "left",
                "intro f",
                "intro hf",
                "intro hproperty",
                "have hf0 : f = 0",
                "specialize le_zero f",
                "apply le_zero",
                "exact hf",
                "apply hboundary_right",
                "rewrite hf0 at hproperty",
                "rewrite hf0 at hproperty",
                "rewrite hf0 at hproperty",
                "rewrite hf0 at hproperty",
                "exact hproperty",
                "intro p",
                "intro a",
                f"have hboundary : ({_power_divides_terms('p', 'S B', 'a', tag='search_succ_boundary')}) \\/ ~({_power_divides_terms('p', 'S B', 'a', tag='search_succ_boundary')})",
                "specialize power_divides_decidable p",
                "specialize power_divides_decidable (S B)",
                "specialize power_divides_decidable a",
                "exact power_divides_decidable",
                "cases hboundary",
                "right",
                "exists S B",
                "split",
                "split",
                "specialize le_refl (S B)",
                "exact le_refl",
                "exact hboundary_left",
                "intro f",
                "intro hf",
                "intro hproperty",
                "exact hf",
                f"have hprevious : ({search_none}) \\/ ({search_maximum})",
                "specialize IH p",
                "specialize IH a",
                "exact IH",
                "cases hprevious",
                "left",
                "intro f",
                "intro hf",
                "intro hproperty",
                "have hsplit : f = S B \\/ exists h. h + S f = S B",
                "specialize le_eq_or_lt f",
                "specialize le_eq_or_lt (S B)",
                "apply le_eq_or_lt",
                "exact hf",
                "cases hsplit",
                "apply hboundary_right",
                "rewrite hsplit_left at hproperty",
                "rewrite hsplit_left at hproperty",
                "rewrite hsplit_left at hproperty",
                "rewrite hsplit_left at hproperty",
                "exact hproperty",
                "specialize hprevious_left f",
                "apply hprevious_left",
                "specialize le_of_succ_le_succ f",
                "specialize le_of_succ_le_succ B",
                "apply le_of_succ_le_succ",
                "exact hsplit_right",
                "exact hproperty",
                "right",
                "cases hprevious_right",
                "cases hprevious_right_witness",
                "cases hprevious_right_witness_left",
                "exists x",
                "split",
                "split",
                "specialize le_succ x",
                "specialize le_succ B",
                "apply le_succ",
                "exact hprevious_right_witness_left_left",
                "exact hprevious_right_witness_left_right",
                "intro f",
                "intro hf",
                "intro hproperty",
                "have hsplit : f = S B \\/ exists h. h + S f = S B",
                "specialize le_eq_or_lt f",
                "specialize le_eq_or_lt (S B)",
                "apply le_eq_or_lt",
                "exact hf",
                "cases hsplit",
                "exfalso",
                "apply hboundary_right",
                "rewrite hsplit_left at hproperty",
                "rewrite hsplit_left at hproperty",
                "rewrite hsplit_left at hproperty",
                "rewrite hsplit_left at hproperty",
                "exact hproperty",
                "specialize hprevious_right_witness_right f",
                "apply hprevious_right_witness_right",
                "specialize le_of_succ_le_succ f",
                "specialize le_of_succ_le_succ B",
                "apply le_of_succ_le_succ",
                "exact hsplit_right",
                "exact hproperty",
            ),
            "Finite search either excludes every power divisor or returns a greatest exponent.",
        ),
        spec(
            "bounded_power_valuation_exists",
            f"forall p a B. exists e. ({bounded})",
            ("bounded_power_valuation_search", "power_divides_zero", "zero_le"),
            (
                "intro p",
                "intro a",
                "intro B",
                f"have hsearch : ({search_none}) \\/ ({search_maximum})",
                "specialize bounded_power_valuation_search B",
                "specialize bounded_power_valuation_search p",
                "specialize bounded_power_valuation_search a",
                "exact bounded_power_valuation_search",
                "cases hsearch",
                f"have hzero : ({_power_divides_terms('p', '0', 'a', tag='exists_zero')})",
                "specialize power_divides_zero p",
                "specialize power_divides_zero a",
                "specialize power_divides_zero 0",
                "apply power_divides_zero",
                "refl",
                "specialize hsearch_left 0",
                "exfalso",
                "apply hsearch_left",
                "specialize zero_le B",
                "exact zero_le",
                "exact hzero",
                "cases hsearch_right",
                "exists x",
                "exact hsearch_right_witness",
            ),
            "Every explicit exponent bound has a greatest power-divisor exponent.",
        ),
        spec(
            "power_valuation_exists",
            f"forall p a. exists e. ({canonical})",
            ("bounded_power_valuation_exists",),
            (
                "intro p",
                "intro a",
                "specialize bounded_power_valuation_exists p",
                "specialize bounded_power_valuation_exists a",
                "specialize bounded_power_valuation_exists a",
                "exact bounded_power_valuation_exists",
            ),
            "The value itself supplies a canonical finite bound for power valuation.",
        ),
        spec(
            "power_valuation_functional",
            f"forall p a e f. ({canonical_left}) -> ({canonical_right}) -> e = f",
            ("le_antisymm",),
            (
                "intro p",
                "intro a",
                "intro e",
                "intro f",
                "intro he",
                "intro hf",
                "cases he",
                "cases he_left",
                "cases hf",
                "cases hf_left",
                "have hef : e <= f",
                "specialize hf_right e",
                "apply hf_right",
                "exact he_left_left",
                "exact he_left_right",
                "have hfe : f <= e",
                "specialize he_right f",
                "apply he_right",
                "exact hf_left_left",
                "exact hf_left_right",
                "specialize le_antisymm e",
                "specialize le_antisymm f",
                "apply le_antisymm",
                "exact hef",
                "exact hfe",
            ),
            "Canonical bounded power valuations have a unique exponent.",
        ),
        spec(
            "power_valuation_power_divides",
            f"forall p a e. ({canonical}) -> ({canonical_property})",
            (),
            (
                "intro p",
                "intro a",
                "intro e",
                "intro hvaluation",
                "cases hvaluation",
                "cases hvaluation_left",
                "exact hvaluation_left_right",
            ),
            "A valuation exponent has a relational power dividing the value.",
        ),
        spec(
            "power_valuation_dominates",
            f"forall p a e f. ({canonical}) -> "
            f"({at_most('f', 'a', tag='dominates_bound')}) -> "
            f"({canonical_candidate}) -> ({at_most('f', 'e', tag='dominates_result')})",
            (),
            (
                "intro p",
                "intro a",
                "intro e",
                "intro f",
                "intro hvaluation",
                "intro hbound",
                "intro hdivides",
                "cases hvaluation",
                "specialize hvaluation_right f",
                "apply hvaluation_right",
                "exact hbound",
                "exact hdivides",
            ),
            "Every bounded power-divisor exponent lies below the valuation exponent.",
        ),
        spec(
            "prime_power_valuation_exists",
            f"forall p a. ({prime_p}) -> ~(a = 0) -> exists e. ({prime_canonical})",
            ("power_valuation_exists",),
            (
                "intro p",
                "intro a",
                "intro hp",
                "intro ha",
                f"have hvaluation : exists e. ({power_valuation('p', 'a', 'e', tag='prime_total_graph')})",
                "specialize power_valuation_exists p",
                "specialize power_valuation_exists a",
                "exact power_valuation_exists",
                "cases hvaluation",
                "exists x",
                "split",
                "split",
                "exact hp",
                "exact ha",
                "exact hvaluation_witness",
            ),
            "Every nonzero natural has a bounded valuation at each prime base.",
        ),
        spec(
            "prime_power_valuation_functional",
            f"forall p a e f. ({prime_canonical_left}) -> "
            f"({prime_canonical_right}) -> e = f",
            ("power_valuation_functional",),
            (
                "intro p",
                "intro a",
                "intro e",
                "intro f",
                "intro he",
                "intro hf",
                "cases he",
                "cases hf",
                "specialize power_valuation_functional p",
                "specialize power_valuation_functional a",
                "specialize power_valuation_functional e",
                "specialize power_valuation_functional f",
                "apply power_valuation_functional",
                "exact he_right",
                "exact hf_right",
            ),
            "Prime-base nonzero valuations have a unique exponent.",
        ),
    )


__all__ = [
    "at_most",
    "bounded_power_valuation",
    "divides",
    "make_bertrand_power_valuation_candidate_theorems",
    "power_divides",
    "power_valuation",
    "prime_power_valuation",
]
