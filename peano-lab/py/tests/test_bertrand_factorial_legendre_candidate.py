"""Cheap static and dependency-curried audit for factorial/Legendre equality.

This gate deliberately stops before empty-context closure.  It freezes the
expanded statements and dependency surface, then asks the independent kernel
to check each proof body with every declared dependency as an ordinary
hypothesis.
"""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library.bertrand_factorial_legendre_candidate import (
    make_bertrand_factorial_legendre_candidate_theorems,
)
from peano_lab.library.bertrand_factorial_valuation_candidate import (
    make_bertrand_factorial_valuation_candidate_theorems,
)
from peano_lab.library.bertrand_legendre_recurrence_candidate import (
    make_bertrand_legendre_recurrence_candidate_theorems,
)
from peano_lab.library.bertrand_legendre_sum_candidate import (
    make_bertrand_legendre_sum_candidate_theorems,
)
from peano_lab.library.bertrand_power_valuation_candidate import (
    make_bertrand_power_valuation_candidate_theorems,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _specs_by_name,
)


EXPECTED = {
    "factorial_legendre_successor_agreement": {
        "statement": (
            65_959,
            "8bc0d088d9ed0d911a3d0eb9a7ebfb6e1b66069215956b58b1f282dafa412a02",
        ),
        "dependencies": (
            "prime_factorial_valuation_succ",
            "prime_legendre_sum_succ",
        ),
        "body": (2, 45, 54, 29, 54, 53, 0),
    },
    "prime_factorial_valuation_eq_legendre_sum": {
        "statement": (
            25_480,
            "7123646c1dfc92f90c584772c3ee1df5fd6e34ed2b5590c9d66be4e6a2e49b9a",
        ),
        "dependencies": (
            "prime_factorial_valuation_zero",
            "legendre_sum_zero",
            "factorial_valuation_exists",
            "prime_legendre_sum_exists",
            "power_valuation_exists",
            "factorial_legendre_successor_agreement",
        ),
        "body": (6, 69, 84, 33, 84, 83, 0),
    },
}


@lru_cache(maxsize=1)
def _prior_specs() -> tuple[TheoremSpec, ...]:
    """Return only the direct, concrete statement providers for this gate."""

    return (
        *make_bertrand_power_valuation_candidate_theorems(TheoremSpec),
        *make_bertrand_factorial_valuation_candidate_theorems(TheoremSpec),
        *make_bertrand_legendre_sum_candidate_theorems(TheoremSpec),
        *make_bertrand_legendre_recurrence_candidate_theorems(TheoremSpec),
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_factorial_legendre_candidate_theorems(TheoremSpec)


def _local() -> dict[str, TheoremSpec]:
    rows = (*_prior_specs(), *_specs())
    assert len({row.name for row in rows}) == len(rows)
    return {row.name: row for row in rows}


def _available() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _local()


def test_factorial_legendre_factory_is_frozen_hygienic_and_topological() -> None:
    specs = _specs()
    assert tuple(item.name for item in specs) == tuple(EXPECTED)
    assert make_bertrand_factorial_legendre_candidate_theorems(
        TheoremSpec
    ) == specs

    public = _specs_by_name()
    assert not (set(EXPECTED) & set(public))

    local = _local()
    available = set(public) | {item.name for item in _prior_specs()}
    for item in specs:
        expected = EXPECTED[item.name]
        assert local[item.name] is item
        assert item.dependencies == expected["dependencies"]
        assert all(dependency in available for dependency in item.dependencies)
        available.add(item.name)

        length, digest = expected["statement"]
        assert len(item.statement) == length
        assert sha256(item.statement.encode()).hexdigest() == digest
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert all(
            marker not in item.statement
            for marker in (
                "Factorial(",
                "FactorialVal(",
                "LegendreSum(",
                "PowerVal(",
                "PowerQuotPrefix(",
                "Prime(",
                "Pow(",
                "DivRem(",
                "BetaAt(",
                "Sum(",
                "^",
                "%",
                "∣",
                "<=",
            )
        )

    commands = tuple(command for item in specs for command in item.script)
    assert all(
        command.split(maxsplit=1)[0]
        not in {
            "auto",
            "choice",
            "compact_arith",
            "norm_num",
            "ring",
            "simp",
            "use",
        }
        for command in commands
    )
    assert all(
        forbidden not in command
        for command in commands
        for forbidden in ("DNE", "by_contra", "classical", "sorry")
    )


def test_factorial_legendre_bodies_have_exact_kernel_receipts() -> None:
    receipts = replay_candidate_bodies(_specs(), core=_available())
    assert {
        receipt.name: (
            receipt.dependency_count,
            receipt.command_count,
            receipt.proof_nodes,
            receipt.proof_depth,
            receipt.proof_objects,
            receipt.proof_edges,
            receipt.reused_objects,
        )
        for receipt in receipts
    } == {name: expected["body"] for name, expected in EXPECTED.items()}


def test_factorial_legendre_rejects_false_targets_and_every_removed_edge() -> None:
    for item in _specs():
        false_item = replace(item, statement=f"({item.statement}) /\\ false")
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((false_item,), core=_available())

        for dependency in item.dependencies:
            without_edge = replace(
                item,
                dependencies=tuple(
                    candidate
                    for candidate in item.dependencies
                    if candidate != dependency
                ),
            )
            with pytest.raises(CandidateBodyError):
                replay_candidate_bodies((without_edge,), core=_available())
