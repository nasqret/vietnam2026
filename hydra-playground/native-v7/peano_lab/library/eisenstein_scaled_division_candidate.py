"""Exact scaled half-range division data for Eisenstein floor sums.

The existing Fermat scale surface records multiplication only modulo a
modulus.  Eisenstein's argument instead needs the exact naturals
``a*(1+i)`` before division.  This isolated layer fills that representation
gap constructively:

* a constant beta prefix supplies the factor ``a``;
* pointwise multiplication with the canonical half range constructs an exact
  source prefix ``a,2a,...,h*a``;
* the finite division-prefix candidate supplies quotient and remainder codes;
* the checked finite-sum relation packages the quotient floor sum.

Every helper expands to ordinary first-order PA.  No division, remainder,
floor, list, function, or sum primitive is added to the parser or kernel, and
the candidates remain outside the public registry.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_division_prefix_candidate import division_prefix
from .finite_fold_surface import beta_at, repeat_relation, sum_relation
from .finite_pointwise_mul_product_candidate import pointwise_mul_prefix
from .fermat_residue_product_candidate import prime
from .gauss_signed_prefix_candidate import _beta_at_term, half_range


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


def _binders(
    tag: str,
    variables: tuple[str, ...],
    stems: tuple[str, ...],
) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"esd_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated Eisenstein binder captures an argument")
    return names


def scaled_successor_prefix(
    multiplier: str,
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand exact decoding of ``multiplier*(1+i)`` for ``i < length``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (multiplier, "multiplier"),
            (code, "scaled code"),
            (scale, "scaled scale"),
            (length, "prefix length"),
        )
    )
    index, value, gap = _binders(
        tag, variables, ("index", "value", "gap")
    )
    decoded = beta_at(
        code, scale, index, value, tag=f"esd_{tag}_decoded"
    )
    return (
        f"forall {index} {value}. (exists {gap}. {gap} + S {index} = {length}) -> "
        f"({decoded}) -> {value} = {multiplier} * (1 + {index})"
    )


def make_eisenstein_scaled_division_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build exact scaling, division-prefix, and quotient-sum candidates."""

    canonical_half = half_range(
        "b", "c", "h", tag="eisenstein_scaled_half_range"
    )
    repeated_multiplier = repeat_relation(
        "ab", "ac", "a", "h", tag="eisenstein_scaled_repeat"
    )
    pointwise_scaled = pointwise_mul_prefix(
        "ab",
        "ac",
        "b",
        "c",
        "tb",
        "tc",
        "h",
        tag="eisenstein_scaled_pointwise",
    )
    exact_scaled = scaled_successor_prefix(
        "a", "tb", "tc", "h", tag="eisenstein_scaled_exact"
    )
    canonical_entry = _beta_at_term(
        "b",
        "c",
        "i",
        "1 + i",
        tag="eisenstein_scaled_canonical_entry",
        variables=("a", "b", "c", "ab", "ac", "tb", "tc", "h", "i", "x"),
    )
    repeated_entry = beta_at(
        "ab", "ac", "i", "a", tag="eisenstein_scaled_repeated_entry"
    )

    prime_p = prime("p", tag="eisenstein_division_prime")
    division = division_prefix(
        "p",
        "tb",
        "tc",
        "qb",
        "qc",
        "rb",
        "rc",
        "h",
        tag="eisenstein_division_prefix",
    )
    quotient_sum = sum_relation(
        "qb", "qc", "h", "Q", tag="eisenstein_quotient_sum"
    )

    repeat_exists = (
        "exists ab ac. "
        f"({repeat_relation('ab', 'ac', 'a', 'h', tag='eisenstein_repeat_exists')})"
    )
    pointwise_exists = (
        "exists tb tc. "
        f"({pointwise_mul_prefix('x', 'x1', 'b', 'c', 'tb', 'tc', 'h', tag='eisenstein_pointwise_exists')})"
    )
    local_exact_scaled = scaled_successor_prefix(
        "a", "x2", "x3", "h", tag="eisenstein_local_exact"
    )
    division_exists = (
        "exists qb qc rb rc. "
        f"({division_prefix('p', 'x2', 'x3', 'qb', 'qc', 'rb', 'rc', 'h', tag='eisenstein_division_exists')})"
    )
    division_package = (
        "exists tb tc qb qc rb rc. "
        f"(({exact_scaled}) /\ ({division}))"
    )
    local_division_package = (
        "exists tb tc qb qc rb rc. "
        f"(({scaled_successor_prefix('a', 'tb', 'tc', 'h', tag='eisenstein_local_package_scaled')}) /\ "
        f"({division_prefix('p', 'tb', 'tc', 'qb', 'qc', 'rb', 'rc', 'h', tag='eisenstein_local_package_division')}))"
    )
    local_sum_exists = (
        "exists Q. "
        f"({sum_relation('x2', 'x3', 'h', 'Q', tag='eisenstein_local_sum_exists')})"
    )
    quotient_sum_package = (
        "exists tb tc qb qc rb rc Q. "
        f"(({exact_scaled}) /\ (({division}) /\ ({quotient_sum})))"
    )

    return (
        spec(
            "beta_scaled_successor_prefix_from_pointwise",
            "forall a b c ab ac tb tc h. "
            f"({canonical_half}) -> ({repeated_multiplier}) -> "
            f"({pointwise_scaled}) -> ({exact_scaled})",
            (),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro ab",
                "intro ac",
                "intro tb",
                "intro tc",
                "intro h",
                "intro hhalf",
                "intro hrepeat",
                "intro hpointwise",
                "intro i",
                "intro x",
                "intro hi",
                "intro hx",
                f"have hcanonical : {canonical_entry}",
                "specialize hhalf i",
                "apply hhalf",
                "exact hi",
                f"have hrepeated : {repeated_entry}",
                "specialize hrepeat i",
                "apply hrepeat",
                "exact hi",
                "specialize hpointwise i",
                "specialize hpointwise a",
                "specialize hpointwise (1 + i)",
                "specialize hpointwise x",
                "apply hpointwise",
                "exact hi",
                "exact hrepeated",
                "exact hcanonical",
                "exact hx",
            ),
            "A constant prefix times 1,...,h decodes exactly as a*(1+i).",
        ),
        spec(
            "prime_scaled_half_division_prefix_exists",
            "forall p h a b c. p = 2 * h + 1 -> "
            f"({prime_p}) -> ({canonical_half}) -> ({division_package})",
            (
                "beta_repeat_exists",
                "beta_pointwise_mul_prefix_exists",
                "beta_scaled_successor_prefix_from_pointwise",
                "prime_nonzero",
                "beta_division_prefix_exists",
            ),
            (
                "intro p",
                "intro h",
                "intro a",
                "intro b",
                "intro c",
                "intro hpodd",
                "intro hprime",
                "intro hhalf",
                f"have hrepeat_exists : {repeat_exists}",
                "specialize beta_repeat_exists a",
                "specialize beta_repeat_exists h",
                "exact beta_repeat_exists",
                "cases hrepeat_exists",
                "cases hrepeat_exists_witness",
                f"have hpointwise_exists : {pointwise_exists}",
                "specialize beta_pointwise_mul_prefix_exists x",
                "specialize beta_pointwise_mul_prefix_exists x1",
                "specialize beta_pointwise_mul_prefix_exists b",
                "specialize beta_pointwise_mul_prefix_exists c",
                "specialize beta_pointwise_mul_prefix_exists h",
                "exact beta_pointwise_mul_prefix_exists",
                "cases hpointwise_exists",
                "cases hpointwise_exists_witness",
                f"have hscaled : {local_exact_scaled}",
                "specialize beta_scaled_successor_prefix_from_pointwise a",
                "specialize beta_scaled_successor_prefix_from_pointwise b",
                "specialize beta_scaled_successor_prefix_from_pointwise c",
                "specialize beta_scaled_successor_prefix_from_pointwise x",
                "specialize beta_scaled_successor_prefix_from_pointwise x1",
                "specialize beta_scaled_successor_prefix_from_pointwise x2",
                "specialize beta_scaled_successor_prefix_from_pointwise x3",
                "specialize beta_scaled_successor_prefix_from_pointwise h",
                "apply beta_scaled_successor_prefix_from_pointwise",
                "exact hhalf",
                "exact hrepeat_exists_witness_witness",
                "exact hpointwise_exists_witness_witness",
                "have hp0 : ~(p = 0)",
                "intro hpzero",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hprime",
                "exact hpzero",
                f"have hdivision_exists : {division_exists}",
                "specialize beta_division_prefix_exists p",
                "specialize beta_division_prefix_exists x2",
                "specialize beta_division_prefix_exists x3",
                "specialize beta_division_prefix_exists h",
                "apply beta_division_prefix_exists",
                "exact hp0",
                "cases hdivision_exists",
                "cases hdivision_exists_witness",
                "cases hdivision_exists_witness_witness",
                "cases hdivision_exists_witness_witness_witness",
                "exists x2",
                "exists x3",
                "exists x4",
                "exists x5",
                "exists x6",
                "exists x7",
                "split",
                "exact hscaled",
                "exact hdivision_exists_witness_witness_witness_witness",
            ),
            "An odd-prime half range has exact scaled quotient/remainder codes.",
        ),
        spec(
            "prime_scaled_half_quotient_sum_exists",
            "forall p h a b c. p = 2 * h + 1 -> "
            f"({prime_p}) -> ({canonical_half}) -> ({quotient_sum_package})",
            (
                "prime_scaled_half_division_prefix_exists",
                "beta_sum_exists",
            ),
            (
                "intro p",
                "intro h",
                "intro a",
                "intro b",
                "intro c",
                "intro hpodd",
                "intro hprime",
                "intro hhalf",
                f"have hdivision : {local_division_package}",
                "specialize prime_scaled_half_division_prefix_exists p",
                "specialize prime_scaled_half_division_prefix_exists h",
                "specialize prime_scaled_half_division_prefix_exists a",
                "specialize prime_scaled_half_division_prefix_exists b",
                "specialize prime_scaled_half_division_prefix_exists c",
                "apply prime_scaled_half_division_prefix_exists",
                "exact hpodd",
                "exact hprime",
                "exact hhalf",
                "cases hdivision",
                "cases hdivision_witness",
                "cases hdivision_witness_witness",
                "cases hdivision_witness_witness_witness",
                "cases hdivision_witness_witness_witness_witness",
                "cases hdivision_witness_witness_witness_witness_witness",
                "cases hdivision_witness_witness_witness_witness_witness_witness",
                f"have hsum_exists : {local_sum_exists}",
                "specialize beta_sum_exists x2",
                "specialize beta_sum_exists x3",
                "specialize beta_sum_exists h",
                "exact beta_sum_exists",
                "cases hsum_exists",
                "exists x",
                "exists x1",
                "exists x2",
                "exists x3",
                "exists x4",
                "exists x5",
                "exists x6",
                "split",
                "exact hdivision_witness_witness_witness_witness_witness_witness_left",
                "split",
                "exact hdivision_witness_witness_witness_witness_witness_witness_right",
                "exact hsum_exists_witness",
            ),
            "The quotient code additionally carries its native finite floor sum.",
        ),
    )


__all__ = [
    "make_eisenstein_scaled_division_candidate_theorems",
    "scaled_successor_prefix",
]
