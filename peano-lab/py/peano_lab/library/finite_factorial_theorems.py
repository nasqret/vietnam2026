"""Isolated checked theorem data for relational native factorials.

``Factorial(n,z)`` is only an untrusted authoring abbreviation here.  Every
exported theorem statement expands it to a beta-coded consecutive ``Range``
starting at one together with the already checked exact ``Product`` relation.
The module deliberately exports a theorem-spec factory and does not mutate the
public theorem registry.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at, product_relation, range_relation


def factorial_relation(length: str, result: str, *, tag: str) -> str:
    """Expand ``Factorial(length,result)`` into the conservative PA surface."""

    code = f"ff_b_{tag}"
    scale = f"ff_c_{tag}"
    start_marker = f"ff_start_{tag}"
    range_prefix = range_relation(
        code, scale, start_marker, length, tag=f"{tag}_range"
    )
    # The generic Range helper deliberately accepts identifiers only.  This
    # module owns the fresh marker and substitutes the numeral before parsing;
    # the resulting checked statement therefore contains literal ``1 + i``.
    if range_prefix.count(start_marker) != 2:
        raise AssertionError("unexpected consecutive-Range expansion")
    range_prefix = range_prefix.replace(start_marker, "1")
    product = product_relation(code, scale, length, result, tag=f"{tag}_product")
    return f"exists {code} {scale}. (({range_prefix}) /\\ ({product}))"


_FACTORIAL_EXISTS_REL = factorial_relation("n", "z", tag="exists")
FACTORIAL_EXISTS = f"forall n. exists z. ({_FACTORIAL_EXISTS_REL})"

_FACTORIAL_FUNCTIONAL_LEFT = factorial_relation("n", "z", tag="functional_l")
_FACTORIAL_FUNCTIONAL_RIGHT = factorial_relation("n", "w", tag="functional_r")
FACTORIAL_FUNCTIONAL = (
    f"forall n z w. ({_FACTORIAL_FUNCTIONAL_LEFT}) -> "
    f"({_FACTORIAL_FUNCTIONAL_RIGHT}) -> z = w"
)

_FACTORIAL_ZERO_REL = factorial_relation("n", "z", tag="zero")
FACTORIAL_ZERO = (
    f"forall n z. n = 0 -> ({_FACTORIAL_ZERO_REL}) -> z = 1"
)

_FACTORIAL_SUCCESSOR_REL = factorial_relation("sn", "z", tag="successor")
_FACTORIAL_PREDECESSOR_REL = factorial_relation("n", "r", tag="predecessor")
FACTORIAL_SUCCESSOR_DECOMPOSE = (
    f"forall n sn z. sn = S n -> ({_FACTORIAL_SUCCESSOR_REL}) -> "
    f"exists r. ({_FACTORIAL_PREDECESSOR_REL}) /\\ z = r * S n"
)


def make_finite_factorial_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered, unregistered factorial tranche."""

    transported_product = product_relation(
        "x2", "x3", "n", "z", tag="factorial_transport"
    )
    transported_entries = (
        "forall i p. (exists h. h + S i = n) -> "
        f"({beta_at('x', 'x1', 'i', 'p', tag='factorial_transport_l')}) -> "
        f"({beta_at('x2', 'x3', 'i', 'p', tag='factorial_transport_r')})"
    )
    successor_factor = beta_at(
        "x", "x1", "n", "p", tag="factorial_succ_factor"
    )
    successor_prefix = product_relation(
        "x", "x1", "n", "r", tag="factorial_succ_prefix"
    )
    successor_decomposition = (
        f"exists p r. ({successor_factor}) /\\ "
        f"(({successor_prefix}) /\\ z = r * p)"
    )

    return (
        spec(
            "factorial_exists",
            FACTORIAL_EXISTS,
            ("beta_range_exists", "beta_product_exists"),
            (
                "intro n",
                "have hrange : exists b c. (forall i. "
                "(exists h. h + S i = n) -> "
                "((exists h. h + S (1 + i) = S ((S i) * c)) /\\ "
                "exists q. b = q * S ((S i) * c) + (1 + i)))",
                "specialize beta_range_exists 1",
                "specialize beta_range_exists n",
                "exact beta_range_exists",
                "cases hrange",
                "cases hrange_witness",
                "specialize beta_product_exists x",
                "specialize beta_product_exists x1",
                "specialize beta_product_exists n",
                "cases beta_product_exists",
                "cases beta_product_exists_witness",
                "cases beta_product_exists_witness_witness",
                "exists x2",
                "exists x",
                "exists x1",
                "split",
                "exact hrange_witness_witness",
                "exists x3",
                "exists x4",
                "exact beta_product_exists_witness_witness_witness",
            ),
            "Every natural has a beta-coded relational factorial value.",
        ),
        spec(
            "factorial_functional",
            FACTORIAL_FUNCTIONAL,
            (
                "beta_range_transport_entry",
                "beta_product_transport_prefix",
                "beta_product_functional",
            ),
            (
                "intro n",
                "intro z",
                "intro w",
                "intro hz",
                "intro hw",
                "cases hz",
                "cases hz_witness",
                "cases hz_witness_witness",
                "cases hw",
                "cases hw_witness",
                "cases hw_witness_witness",
                f"have htransport : {transported_product}",
                "specialize beta_product_transport_prefix x",
                "specialize beta_product_transport_prefix x1",
                "specialize beta_product_transport_prefix x2",
                "specialize beta_product_transport_prefix x3",
                "specialize beta_product_transport_prefix n",
                "specialize beta_product_transport_prefix z",
                "apply beta_product_transport_prefix",
                "exact hz_witness_witness_right",
                "intro i",
                "intro p",
                "intro hi",
                "intro hp",
                "specialize beta_range_transport_entry x",
                "specialize beta_range_transport_entry x1",
                "specialize beta_range_transport_entry x2",
                "specialize beta_range_transport_entry x3",
                "specialize beta_range_transport_entry 1",
                "specialize beta_range_transport_entry n",
                f"have hentries : {transported_entries}",
                "apply beta_range_transport_entry",
                "exact hz_witness_witness_left",
                "exact hw_witness_witness_left",
                "specialize hentries i",
                "specialize hentries p",
                "apply hentries",
                "exact hi",
                "exact hp",
                "cases htransport",
                "cases htransport_witness",
                "cases hw_witness_witness_right",
                "cases hw_witness_witness_right_witness",
                "specialize beta_product_functional x2",
                "specialize beta_product_functional x3",
                "specialize beta_product_functional n",
                "specialize beta_product_functional z",
                "specialize beta_product_functional x4",
                "specialize beta_product_functional x5",
                "specialize beta_product_functional w",
                "specialize beta_product_functional x6",
                "specialize beta_product_functional x7",
                "apply beta_product_functional",
                "exact htransport_witness_witness",
                "exact hw_witness_witness_right_witness_witness",
            ),
            "The beta-coded relational factorial has a unique value.",
        ),
        spec(
            "factorial_zero",
            FACTORIAL_ZERO,
            ("beta_product_zero",),
            (
                "intro n",
                "intro z",
                "intro hn",
                "intro hfactorial",
                "rewrite hn at hfactorial",
                "rewrite hn at hfactorial",
                "rewrite hn at hfactorial",
                "rewrite hn at hfactorial",
                "cases hfactorial",
                "cases hfactorial_witness",
                "cases hfactorial_witness_witness",
                "specialize beta_product_zero x",
                "specialize beta_product_zero x1",
                "specialize beta_product_zero z",
                "apply beta_product_zero",
                "exact hfactorial_witness_witness_right",
            ),
            "The relational factorial of zero is one.",
        ),
        spec(
            "factorial_succ_decompose",
            FACTORIAL_SUCCESSOR_DECOMPOSE,
            (
                "beta_product_succ_decompose",
                "beta_range_entry_eq",
                "le_refl",
                "le_succ",
                "add_succ_left",
                "zero_add",
            ),
            (
                "intro n",
                "intro sn",
                "intro z",
                "intro hsn",
                "intro hfactorial",
                "rewrite hsn at hfactorial",
                "rewrite hsn at hfactorial",
                "rewrite hsn at hfactorial",
                "rewrite hsn at hfactorial",
                "cases hfactorial",
                "cases hfactorial_witness",
                "cases hfactorial_witness_witness",
                f"have hdecomp : {successor_decomposition}",
                "specialize beta_product_succ_decompose x",
                "specialize beta_product_succ_decompose x1",
                "specialize beta_product_succ_decompose n",
                "specialize beta_product_succ_decompose z",
                "apply beta_product_succ_decompose",
                "exact hfactorial_witness_witness_right",
                "cases hdecomp",
                "cases hdecomp_witness",
                "cases hdecomp_witness_witness",
                "cases hdecomp_witness_witness_right",
                "have hp : x2 = 1 + n",
                "specialize beta_range_entry_eq x",
                "specialize beta_range_entry_eq x1",
                "specialize beta_range_entry_eq 1",
                "specialize beta_range_entry_eq (S n)",
                "specialize beta_range_entry_eq n",
                "specialize beta_range_entry_eq x2",
                "apply beta_range_entry_eq",
                "exact hfactorial_witness_witness_left",
                "specialize le_refl (S n)",
                "exact le_refl",
                "exact hdecomp_witness_witness_left",
                "exists x3",
                "split",
                "exists x",
                "exists x1",
                "split",
                "intro i",
                "intro hi",
                "specialize hfactorial_witness_witness_left i",
                "apply hfactorial_witness_witness_left",
                "specialize le_succ (S i)",
                "specialize le_succ n",
                "apply le_succ",
                "exact hi",
                "exact hdecomp_witness_witness_right_left",
                "trans x3 * x2",
                "exact hdecomp_witness_witness_right_right",
                "rewrite hp",
                "congr",
                "refl",
                "specialize add_succ_left 0",
                "specialize add_succ_left n",
                "trans S (0 + n)",
                "exact add_succ_left",
                "congr",
                "apply zero_add",
            ),
            "A successor factorial is its predecessor factorial times the successor.",
        ),
    )


__all__ = [
    "FACTORIAL_EXISTS",
    "FACTORIAL_FUNCTIONAL",
    "FACTORIAL_SUCCESSOR_DECOMPOSE",
    "FACTORIAL_ZERO",
    "factorial_relation",
    "make_finite_factorial_theorems",
]
