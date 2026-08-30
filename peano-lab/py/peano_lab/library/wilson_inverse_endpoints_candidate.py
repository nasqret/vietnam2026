"""Static fixed-endpoint candidates for the native Wilson inverse map.

The beta-coded inverse map uses zero-based indices for the nonzero residues
``1,...,p-1``.  When ``p = S n`` and ``n = S k``, index ``0`` represents
``1`` and index ``k`` represents the predecessor ``n`` of ``p``.  This
isolated source-only layer proves that both entries are fixed and packages
them with the previously classified fixed-point cases.

The contracts intentionally do not assert that the endpoints are distinct.
For ``p = 2`` the witness is ``k = 0`` and the two endpoint facts coincide;
for ``p = 3`` the witness is ``k = 1`` and the endpoints are distinct.  Any
later exactly-two-fixed pairing theorem must state its separate nondegeneracy
premise explicitly.

Every readable relation below expands hygienically to the unchanged
first-order Peano language.  The factory is deliberately absent from the
public theorem registry pending WMI discovery and receipt-pinned admission.
"""

from __future__ import annotations

from typing import Any, Callable

from .wilson_inverse_prefix_candidate import (
    beta_at,
    inverse_index,
    inverse_prefix,
    prime,
    strictly_below,
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


def _binders(
    tag: str,
    variables: tuple[str, ...],
    stems: tuple[str, ...],
) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"wie_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated inverse-endpoint binder captures an argument")
    return names


def _mod_eq(
    modulus: str,
    left: str,
    right: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    """Expand balanced natural congruence without adding a parser symbol."""

    safe_modulus = _identifier(modulus, "modulus")
    checked_avoid = tuple(
        _identifier(variable, "captured-variable guard") for variable in avoid
    )
    left_witness, right_witness = _binders(
        tag,
        checked_avoid,
        ("mod_left", "mod_right"),
    )
    return (
        f"exists {left_witness} {right_witness}. "
        f"({left}) + {safe_modulus} * {left_witness} = "
        f"({right}) + {safe_modulus} * {right_witness}"
    )


def _strictly_below_term(
    left: str,
    right: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    """Expand strict order for the controlled constant terms used here."""

    checked_avoid = tuple(
        _identifier(variable, "captured-variable guard") for variable in avoid
    )
    (gap,) = _binders(tag, checked_avoid, ("strict_gap",))
    return f"exists {gap}. {gap} + S {left} = {right}"


def _beta_at_term(
    code: str,
    scale: str,
    index: str,
    value: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    """Expand ``BetaAt`` for controlled terms such as the zero endpoint."""

    safe_code = _identifier(code, "beta code")
    safe_scale = _identifier(scale, "beta scale")
    checked_avoid = tuple(
        _identifier(variable, "captured-variable guard") for variable in avoid
    )
    height, quotient = _binders(
        tag,
        checked_avoid,
        ("beta_height", "beta_quotient"),
    )
    beta_modulus = f"S ((S ({index})) * {safe_scale})"
    return (
        f"((exists {height}. {height} + S ({value}) = {beta_modulus}) /\\ "
        f"exists {quotient}. {safe_code} = "
        f"{quotient} * {beta_modulus} + ({value}))"
    )


def _inverse_index_term(
    modulus: str,
    bound: str,
    index: str,
    mate: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    """Expand ``InvIdx`` for the controlled zero-endpoint terms."""

    safe_modulus = _identifier(modulus, "inverse modulus")
    safe_bound = _identifier(bound, "inverse bound")
    checked_avoid = tuple(
        _identifier(variable, "captured-variable guard") for variable in avoid
    )
    index_bound = _strictly_below_term(
        index,
        safe_bound,
        tag=f"{tag}_index_bound",
        avoid=checked_avoid,
    )
    mate_bound = _strictly_below_term(
        mate,
        safe_bound,
        tag=f"{tag}_mate_bound",
        avoid=checked_avoid,
    )
    congruence = _mod_eq(
        safe_modulus,
        f"(S {index}) * S {mate}",
        "1",
        tag=f"{tag}_mod",
        avoid=checked_avoid,
    )
    return f"({index_bound}) /\\ (({mate_bound}) /\\ ({congruence}))"


def make_wilson_inverse_endpoints_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered fixed-endpoint candidate tranche."""

    zero_prefix = inverse_prefix(
        "p", "n", "b", "c", "n", tag="zero_prefix"
    )
    zero_bound = _strictly_below_term(
        "0", "n", tag="zero_bound", avoid=("p", "n", "k", "b", "c")
    )
    zero_relation = _inverse_index_term(
        "p",
        "n",
        "0",
        "0",
        tag="zero_relation",
        avoid=("p", "n", "k", "b", "c"),
    )
    zero_mod_refl = _mod_eq(
        "p", "1", "1", tag="zero_refl", avoid=("p",)
    )
    zero_mod = _mod_eq(
        "p", "(S 0) * S 0", "1", tag="zero", avoid=("p",)
    )
    zero_result = _beta_at_term(
        "b",
        "c",
        "0",
        "0",
        tag="zero_result",
        avoid=("p", "n", "k", "b", "c"),
    )

    last_prefix = inverse_prefix(
        "p", "n", "b", "c", "n", tag="last_prefix"
    )
    last_bound = strictly_below("k", "n", tag="last_bound")
    last_relation = inverse_index(
        "p", "n", "k", "k", tag="last_relation"
    )
    predecessor_mod = _mod_eq(
        "p", "n * n", "1", tag="predecessor", avoid=("p", "n")
    )
    last_mod = _mod_eq(
        "p", "(S k) * S k", "1", tag="last", avoid=("p", "k")
    )
    last_result = beta_at("b", "c", "k", "k", tag="last_result")

    exact_prime = prime("p", tag="exact_prime")
    exact_prefix = inverse_prefix(
        "p", "n", "b", "c", "n", tag="exact_prefix"
    )
    exact_zero = _beta_at_term(
        "b",
        "c",
        "0",
        "0",
        tag="exact_zero",
        avoid=("p", "n", "b", "c", "k"),
    )
    exact_last = beta_at("b", "c", "k", "k", tag="exact_last")
    exact_fixed_bound = strictly_below(
        "i", "n", tag="exact_fixed_bound"
    )
    exact_fixed_entry = beta_at(
        "b", "c", "i", "i", tag="exact_fixed_entry"
    )
    exact_fixed_cases = (
        f"forall i. ({exact_fixed_bound}) -> ({exact_fixed_entry}) -> "
            "i = 0 \\/ i = k"
    )

    return (
        spec(
            "inverse_prefix_zero_fixed",
            f"forall p n k b c. p = S n -> n = S k -> ({zero_prefix}) -> "
            f"({zero_result})",
            (
                "mod_eq_refl",
                "one_mul",
                "inverse_prefix_extensional",
            ),
            (
                "intro p",
                "intro n",
                "intro k",
                "intro b",
                "intro c",
                "intro hpn",
                "intro hnk",
                "intro hprefix",
                f"have hzero_bound : {zero_bound}",
                "rewrite hnk",
                "exists k",
                "rewrite PA4",
                "rewrite PA3",
                "refl",
                f"have hzero_refl : {zero_mod_refl}",
                "specialize mod_eq_refl p",
                "specialize mod_eq_refl 1",
                "exact mod_eq_refl",
                f"have hzero_mod : {zero_mod}",
                "specialize one_mul 1",
                "rewrite one_mul",
                "exact hzero_refl",
                f"have hzero_relation : {zero_relation}",
                "split",
                "exact hzero_bound",
                "split",
                "exact hzero_bound",
                "exact hzero_mod",
                "specialize inverse_prefix_extensional p",
                "specialize inverse_prefix_extensional n",
                "specialize inverse_prefix_extensional b",
                "specialize inverse_prefix_extensional c",
                "specialize inverse_prefix_extensional n",
                "specialize inverse_prefix_extensional 0",
                "specialize inverse_prefix_extensional 0",
                "apply inverse_prefix_extensional",
                "exact hpn",
                "exact hprefix",
                "exact hzero_bound",
                "exact hzero_relation",
            ),
            "The zero index, representing residue one, is fixed by the full inverse prefix.",
        ),
        spec(
            "inverse_prefix_last_fixed",
            f"forall p n k b c. p = S n -> n = S k -> ({last_prefix}) -> "
            f"({last_result})",
            (
                "zero_add",
                "predecessor_square_mod_one",
                "inverse_prefix_extensional",
            ),
            (
                "intro p",
                "intro n",
                "intro k",
                "intro b",
                "intro c",
                "intro hpn",
                "intro hnk",
                "intro hprefix",
                f"have hlast_bound : {last_bound}",
                "rewrite hnk",
                "exists 0",
                "specialize zero_add (S k)",
                "exact zero_add",
                f"have hpredecessor_mod : {predecessor_mod}",
                "specialize predecessor_square_mod_one p",
                "specialize predecessor_square_mod_one n",
                "apply predecessor_square_mod_one",
                "exact hpn",
                f"have hlast_mod : {last_mod}",
                "rewrite <- hnk",
                "rewrite <- hnk",
                "exact hpredecessor_mod",
                f"have hlast_relation : {last_relation}",
                "split",
                "exact hlast_bound",
                "split",
                "exact hlast_bound",
                "exact hlast_mod",
                "specialize inverse_prefix_extensional p",
                "specialize inverse_prefix_extensional n",
                "specialize inverse_prefix_extensional b",
                "specialize inverse_prefix_extensional c",
                "specialize inverse_prefix_extensional n",
                "specialize inverse_prefix_extensional k",
                "specialize inverse_prefix_extensional k",
                "apply inverse_prefix_extensional",
                "exact hpn",
                "exact hprefix",
                "exact hlast_bound",
                "exact hlast_relation",
            ),
            "The last index, representing the predecessor of p, is fixed by the full inverse prefix.",
        ),
        spec(
            "prime_inverse_prefix_exact_endpoints",
            f"forall p n b c. p = S n -> ({exact_prime}) -> "
            f"({exact_prefix}) -> exists k. ((n = S k) /\\ "
            f"(({exact_zero}) /\\ (({exact_last}) /\\ ({exact_fixed_cases}))))",
            (
                "prime_is_succ_succ",
                "succ_injective",
                "inverse_prefix_zero_fixed",
                "inverse_prefix_last_fixed",
                "prime_inverse_prefix_fixed_cases",
            ),
            (
                "intro p",
                "intro n",
                "intro b",
                "intro c",
                "intro hpn",
                "intro hp",
                "intro hprefix",
                "have hsucc_shape : forall a d. S a = S d -> a = d",
                "exact succ_injective",
                "have hsucc_fixed : forall a d. S a = S d -> a = d",
                "exact succ_injective",
                "have hprime_shape : exists k. p = S (S k)",
                "specialize prime_is_succ_succ p",
                "apply prime_is_succ_succ",
                "exact hp",
                "cases hprime_shape",
                "have hnk : n = S x",
                "specialize hsucc_shape n",
                "specialize hsucc_shape (S x)",
                "apply hsucc_shape",
                "trans p",
                "symm",
                "exact hpn",
                "exact hprime_shape_witness",
                f"have hzero : {exact_zero}",
                "specialize inverse_prefix_zero_fixed p",
                "specialize inverse_prefix_zero_fixed n",
                "specialize inverse_prefix_zero_fixed x",
                "specialize inverse_prefix_zero_fixed b",
                "specialize inverse_prefix_zero_fixed c",
                "apply inverse_prefix_zero_fixed",
                "exact hpn",
                "exact hnk",
                "exact hprefix",
                f"have hlast : {beta_at('b', 'c', 'x', 'x', tag='exact_last_witness')}",
                "specialize inverse_prefix_last_fixed p",
                "specialize inverse_prefix_last_fixed n",
                "specialize inverse_prefix_last_fixed x",
                "specialize inverse_prefix_last_fixed b",
                "specialize inverse_prefix_last_fixed c",
                "apply inverse_prefix_last_fixed",
                "exact hpn",
                "exact hnk",
                "exact hprefix",
                "exists x",
                "split",
                "exact hnk",
                "split",
                "exact hzero",
                "split",
                "exact hlast",
                "intro i",
                "intro hi",
                "intro hfixed",
                "have hcases : i = 0 \\/ S i = n",
                "specialize prime_inverse_prefix_fixed_cases p",
                "specialize prime_inverse_prefix_fixed_cases n",
                "specialize prime_inverse_prefix_fixed_cases b",
                "specialize prime_inverse_prefix_fixed_cases c",
                "specialize prime_inverse_prefix_fixed_cases i",
                "apply prime_inverse_prefix_fixed_cases",
                "exact hpn",
                "exact hp",
                "exact hprefix",
                "exact hi",
                "exact hfixed",
                "cases hcases",
                "left",
                "exact hcases_left",
                "right",
                "specialize hsucc_fixed i",
                "specialize hsucc_fixed x",
                "apply hsucc_fixed",
                "trans n",
                "exact hcases_right",
                "exact hnk",
            ),
            "A prime inverse prefix has exactly the two endpoint fixed-point cases, allowing coincidence at p=2.",
        ),
    )


__all__ = ["make_wilson_inverse_endpoints_candidate_theorems"]
