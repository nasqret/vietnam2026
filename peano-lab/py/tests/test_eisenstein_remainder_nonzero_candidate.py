"""Focused native-body audit for sound Eisenstein remainder nonvanishing."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from time import perf_counter

import pytest

import peano_lab.library.eisenstein_remainder_nonzero_candidate as remainder_module
from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library.eisenstein_remainder_nonzero_candidate import (
    make_eisenstein_remainder_nonzero_candidate_theorems,
    prime_nondivisor_scaled_remainder_data,
)
from peano_lab.library.gauss_magnitude_coprime_candidate import (
    make_gauss_magnitude_coprime_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "prime_nondivisor_bounded_scaled_remainder_nonzero",
    "distinct_primes_bounded_scaled_remainder_nonzero",
    "distinct_primes_own_odd_half_scaled_remainder_nonzero",
)

EXPECTED_DEPENDENCIES = {
    "prime_nondivisor_bounded_scaled_remainder_nonzero": (
        "euclid_prime_dvd_product",
        "succ_ne_zero",
        "divisor_le_nonzero",
        "lt_not_le",
    ),
    "distinct_primes_bounded_scaled_remainder_nonzero": (
        "prime_divisor_eq_one_or_self",
        "prime_nondivisor_bounded_scaled_remainder_nonzero",
    ),
    "distinct_primes_own_odd_half_scaled_remainder_nonzero": (
        "odd_half_strictly_below_modulus",
        "lt_of_le_of_lt",
        "distinct_primes_bounded_scaled_remainder_nonzero",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "prime_nondivisor_bounded_scaled_remainder_nonzero": (
        "7ade642ca6287eb8e347256ad4bd4f0f06babcfe96a48e0776b71140c074f379"
    ),
    "distinct_primes_bounded_scaled_remainder_nonzero": (
        "b9d3fa2c1b7d5acaaa53093ad518cab3cd91ce39dab6644249049ec01599c4ff"
    ),
    "distinct_primes_own_odd_half_scaled_remainder_nonzero": (
        "23c3775f63a8ccea5e0b25c92b04b7017b43a3fc91f179476a185411a96e4918"
    ),
}

EXPECTED_BODY_METRICS = {
    "prime_nondivisor_bounded_scaled_remainder_nonzero": (47, 21, 47, 46, 0),
    "distinct_primes_bounded_scaled_remainder_nonzero": (45, 24, 45, 44, 0),
    "distinct_primes_own_odd_half_scaled_remainder_nonzero": (
        45,
        28,
        45,
        44,
        0,
    ),
}

EXPECTED_COMMAND_COUNTS = {
    "prime_nondivisor_bounded_scaled_remainder_nonzero": 40,
    "distinct_primes_bounded_scaled_remainder_nonzero": 37,
    "distinct_primes_own_odd_half_scaled_remainder_nonzero": 37,
}

_BODY_DEADLINE_SECONDS = 60


def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_eisenstein_remainder_nonzero_candidate_theorems(TheoremSpec)


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"Eisenstein remainder replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def _explicit_dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for dependency in make_gauss_magnitude_coprime_candidate_theorems(
        TheoremSpec
    ):
        assert dependency.name not in core
        core[dependency.name] = dependency
    return core


@lru_cache(maxsize=1)
def _body_receipts():
    specs = _candidate_specs()
    local = {item.name: item for item in specs}
    core = _explicit_dependency_core()
    rows = []
    started = perf_counter()

    with _body_deadline(_BODY_DEADLINE_SECONDS):
        for item in specs:
            formula = _closed_formula(item.statement)
            target = formula
            for dependency_name in reversed(item.dependencies):
                dependency = local.get(dependency_name) or core[dependency_name]
                target = Imp(_closed_formula(dependency.statement), target)

            state = start(target)
            for dependency_name in item.dependencies:
                state = apply_tactic(state, "intro", dependency_name)
            for command in item.script:
                tactic, arguments = _primitive(command)
                state = apply_tactic(state, tactic, arguments)

            certificate = checked_final(state, target)
            assert check((), certificate, target)
            assert not any(type(node) is DNE for node in _walk(certificate))
            nodes, depth = proof_metrics(certificate)
            objects, edges, reused = proof_identity_metrics(certificate)
            rows.append(
                (
                    item.name,
                    nodes,
                    depth,
                    objects,
                    edges,
                    reused,
                    len(item.script),
                )
            )

    return tuple(rows), perf_counter() - started


def test_eisenstein_remainder_factory_has_exact_isolated_contract() -> None:
    first = _candidate_specs()
    second = _candidate_specs()

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in first)


def test_remainder_helper_is_hygienic_alpha_native_and_exact() -> None:
    data_left = prime_nondivisor_scaled_remainder_data(
        "p", "q", "i", "d", "r", tag="alpha_left"
    )
    data_right = prime_nondivisor_scaled_remainder_data(
        "p", "q", "i", "d", "r", tag="alpha_right"
    )

    assert data_left != data_right
    assert parse_formula(data_left) == parse_formula(data_right)
    _, free_names = parse_formula_with_names(data_left)
    assert set(free_names) == {"p", "q", "i", "d", "r"}
    assert "ern_factor_alpha_left" in data_left
    assert "q = p * ern_factor_alpha_left" in data_left
    assert "ern_lt_gap_alpha_left_index_bound + S (S i) = p" in data_left
    assert "q * S i = p * d + r" in data_left

    with pytest.raises(ValueError, match="Peano identifier"):
        prime_nondivisor_scaled_remainder_data(
            "p + 1", "q", "i", "d", "r", tag="bad"
        )
    with pytest.raises(ValueError, match="captures an argument"):
        prime_nondivisor_scaled_remainder_data(
            "ern_factor_capture", "q", "i", "d", "r", tag="capture"
        )
    with pytest.raises(ValueError, match="binder tag"):
        prime_nondivisor_scaled_remainder_data(
            "p", "q", "i", "d", "r", tag="bad tag"
        )


def test_remainder_contracts_are_closed_expanded_native_and_soundly_bounded() -> None:
    forbidden_surface_tokens = (
        "BetaAt(",
        "DivRem(",
        "Prime(",
        "Product(",
        "%",
        "<",
        "<=",
        "∣",
        "≡",
    )

    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in forbidden_surface_tokens)

    generic, distinct, corrected_half = _candidate_specs()
    assert "exists factor. q = p * factor" in generic.statement
    assert "q * S i = p * d + r" in generic.statement
    assert "remainder_nonzero_index_below_p" in generic.statement
    assert "forall p q i d r." in distinct.statement

    # The corrected wrapper bounds the index by p's own half k.  It neither
    # introduces q's half nor states the false cross-half condition i<h.
    assert corrected_half.statement.startswith(
        "forall p q k i d r. p = 2 * k + 1 ->"
    )
    assert "remainder_nonzero_own_half_bound" in corrected_half.statement
    assert " + S (i) = k" in corrected_half.statement
    assert "q = 2 *" not in corrected_half.statement
    assert "forall p q k h" not in corrected_half.statement

    # Regression: the rejected cross-half wrapper has this concrete model.
    p, k, q, h, i, d, r = 3, 1, 7, 3, 2, 7, 0
    assert p == 2 * k + 1
    assert q == 2 * h + 1
    assert i < h
    assert p != q
    assert q * (i + 1) == p * d + r
    assert r == 0
    assert remainder_module.__doc__ is not None
    assert all(
        witness in remainder_module.__doc__
        for witness in ("p=3", "q=7", "i=2", "i<k")
    )


def test_eisenstein_remainder_bodies_are_constructive_and_bounded() -> None:
    rows, elapsed = _body_receipts()
    assert tuple(row[0] for row in rows) == EXPECTED_NAMES
    assert {row[0]: row[1:6] for row in rows} == EXPECTED_BODY_METRICS
    assert {row[0]: row[6] for row in rows} == EXPECTED_COMMAND_COUNTS
    assert elapsed < _BODY_DEADLINE_SECONDS

    for name, nodes, depth, objects, edges, reused, commands in rows:
        print(
            "EISENSTEIN REMAINDER BODY RECEIPT "
            f"name={name} nodes={nodes} depth={depth} objects={objects} "
            f"edges={edges} reused={reused} commands={commands}",
            flush=True,
        )
