"""Exact sign-free native quadratic-reciprocity endpoints.

The first two candidates unpack the provenance-preserving two-orientation
Gauss--Eisenstein data package and feed it to the already checked constructive
parity truth tables.  The third packages those two implications under one
quantifier prefix.  Their statements are exactly the public formulas from
``quadratic_residue_surface``: no count, quotient, beta-code, or auxiliary
half variable remains visible.

These candidates are dependency-curried authoring bodies.  They are neither
registered nor admitted; recursive closure, mutation checking, capacity
profiling, and admission remain WMI gates.
"""

from __future__ import annotations

from typing import Any, Callable

from .quadratic_residue_surface import (
    QUADRATIC_RECIPROCITY_COMBINED,
    QUADRATIC_RECIPROCITY_OPPOSITE_CASE,
    QUADRATIC_RECIPROCITY_SAME_CASE,
    quadratic_residue,
)


def _even(term: str, *, tag: str) -> str:
    return f"exists qr_even_{tag}. {term} = 2 * qr_even_{tag}"


def _odd(term: str, *, tag: str) -> str:
    return f"exists qr_odd_{tag}. {term} = 2 * qr_odd_{tag} + 1"


def _mod_two(left: str, right: str, *, tag: str) -> str:
    return (
        f"exists qr_mod_u_{tag} qr_mod_v_{tag}. "
        f"{left} + 2 * qr_mod_u_{tag} = {right} + 2 * qr_mod_v_{tag}"
    )


def _classification(modulus: str, value: str, count: str, *, tag: str) -> str:
    qres = quadratic_residue(modulus, value, tag=f"qr_final_{tag}")
    even = _even(count, tag=f"{tag}_even")
    odd = _odd(count, tag=f"{tag}_odd")
    return (
        f"(((({qres}) -> ({even})) /\\ (({even}) -> ({qres}))) /\\ "
        f"(((~({qres})) -> ({odd})) /\\ (({odd}) -> ~({qres}))))"
    )


def _pair_data_result(half_first: str, half_second: str) -> str:
    first_class = _classification("p", "q", "e", tag="first")
    second_class = _classification("q", "p", "f", tag="second")
    first_mod = _mod_two("e", "Q", tag="first")
    second_mod = _mod_two("f", "U", tag="second")
    return (
        "exists e f Q U. "
        f"((({first_class}) /\\ ({second_class})) /\\ "
        f"((({first_mod}) /\\ ({second_mod})) /\\ "
        f"Q + U = {half_first} * {half_second}))"
    )


def _unpack_pair() -> tuple[str, ...]:
    root = "hdata_witness_witness_witness_witness"
    return (
        "cases hdata",
        "cases hdata_witness",
        "cases hdata_witness_witness",
        "cases hdata_witness_witness_witness",
        f"cases {root}",
        f"cases {root}_left",
        f"cases {root}_right",
        f"cases {root}_right_left",
    )


def _apply_endpoint(endpoint: str, case_hypothesis: str) -> tuple[str, ...]:
    """Apply one parity endpoint to the already unpacked shared data."""

    root = "hdata_witness_witness_witness_witness"
    return (
        f"specialize {endpoint} p",
        f"specialize {endpoint} q",
        f"specialize {endpoint} x2",
        f"specialize {endpoint} x3",
        f"specialize {endpoint} x4",
        f"specialize {endpoint} x5",
        f"specialize {endpoint} x",
        f"specialize {endpoint} x1",
        f"apply {endpoint}",
        "exact hpodd_witness",
        "exact hqodd_witness",
        f"exact {root}_left_left",
        f"exact {root}_left_right",
        f"exact {root}_right_left_left",
        f"exact {root}_right_left_right",
        f"exact {root}_right_right",
        f"exact {case_hypothesis}",
    )


def make_quadratic_reciprocity_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the exact same-case, opposite-case, and combined QR bodies."""

    data_result = _pair_data_result("x", "x1")
    common_intros = (
        "intro p", "intro q", "intro hp", "intro hq", "intro hpq",
        "intro hpodd", "intro hqodd",
    )
    construct_data = (
        "cases hpodd", "cases hqodd",
        f"have hdata : {data_result}",
        "specialize distinct_odd_primes_gauss_eisenstein_data_exists p",
        "specialize distinct_odd_primes_gauss_eisenstein_data_exists q",
        "specialize distinct_odd_primes_gauss_eisenstein_data_exists x",
        "specialize distinct_odd_primes_gauss_eisenstein_data_exists x1",
        "apply distinct_odd_primes_gauss_eisenstein_data_exists",
        "exact hpodd_witness", "exact hqodd_witness",
        "exact hp", "exact hq", "exact hpq",
    )

    same_name = "quadratic_reciprocity_same_case"
    opposite_name = "quadratic_reciprocity_opposite_case"

    return (
        spec(
            same_name,
            QUADRATIC_RECIPROCITY_SAME_CASE,
            (
                "distinct_odd_primes_gauss_eisenstein_data_exists",
                "conditional_qres_same_status_from_oriented_gauss_counts",
            ),
            common_intros
            + ("intro hcase",)
            + construct_data
            + _unpack_pair()
            + _apply_endpoint(
                "conditional_qres_same_status_from_oriented_gauss_counts",
                "hcase",
            ),
            "For distinct odd primes, a one-mod-four input makes the two "
            "cross-residue propositions have the same truth status.",
        ),
        spec(
            opposite_name,
            QUADRATIC_RECIPROCITY_OPPOSITE_CASE,
            (
                "distinct_odd_primes_gauss_eisenstein_data_exists",
                "conditional_qres_opposite_status_from_oriented_gauss_counts",
            ),
            common_intros
            + ("intro hcase",)
            + construct_data
            + _unpack_pair()
            + _apply_endpoint(
                "conditional_qres_opposite_status_from_oriented_gauss_counts",
                "hcase",
            ),
            "For distinct three-mod-four odd primes, exactly one cross-residue "
            "proposition holds.",
        ),
        spec(
            "quadratic_reciprocity_combined",
            QUADRATIC_RECIPROCITY_COMBINED,
            (
                "distinct_odd_primes_gauss_eisenstein_data_exists",
                "conditional_qres_same_status_from_oriented_gauss_counts",
                "conditional_qres_opposite_status_from_oriented_gauss_counts",
            ),
            common_intros
            + construct_data
            + _unpack_pair()
            + (
                "split",
                "intro hsame",
            )
            + _apply_endpoint(
                "conditional_qres_same_status_from_oriented_gauss_counts",
                "hsame",
            )
            + (
                "intro hopposite",
            )
            + _apply_endpoint(
                "conditional_qres_opposite_status_from_oriented_gauss_counts",
                "hopposite",
            ),
            "The exact sign-free two-case quadratic-reciprocity endpoint.",
        ),
    )


__all__ = ["make_quadratic_reciprocity_candidate_theorems"]
