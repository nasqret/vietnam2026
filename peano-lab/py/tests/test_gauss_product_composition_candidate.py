"""Focused native-body audit for the Gauss product cancellation boundary."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from time import perf_counter

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library.finite_pointwise_mul_product_candidate import (
    make_finite_pointwise_mul_product_candidate_theorems,
)
from peano_lab.library.finite_prime_product_coprime_candidate import (
    make_finite_prime_product_coprime_candidate_theorems,
)
from peano_lab.library.gauss_magnitude_coprime_candidate import (
    make_gauss_magnitude_coprime_candidate_theorems,
)
from peano_lab.library.gauss_magnitude_product_candidate import (
    make_gauss_magnitude_product_candidate_theorems,
)
from peano_lab.library.gauss_product_composition_candidate import (
    make_gauss_product_composition_candidate_theorems,
)
from peano_lab.library.gauss_sign_product_candidate import (
    make_gauss_sign_product_candidate_theorems,
)
from peano_lab.library.gauss_signed_pointwise_product_candidate import (
    make_gauss_signed_pointwise_product_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


MAGNITUDE_NAMES = (
    "odd_half_strictly_below_modulus",
    "gauss_magnitude_positive_below_prime",
    "gauss_magnitude_product_coprime",
)

COMPOSITION_NAMES = (
    "prime_half_range_product_coprime",
    "gauss_signed_products_balance_mod",
    "gauss_signed_products_cancel_mod",
)

EXPECTED_DEPENDENCIES = {
    "odd_half_strictly_below_modulus": (
        "mul_succ_left",
        "mul_zero_left",
        "zero_add",
        "add_succ_left",
        "add_assoc",
    ),
    "gauss_magnitude_positive_below_prime": (
        "odd_half_strictly_below_modulus",
        "beta_at_unique",
        "lt_irrefl_expanded",
        "lt_of_le_of_lt",
    ),
    "gauss_magnitude_product_coprime": (
        "gauss_magnitude_positive_below_prime",
        "prime_positive_bounded_product_coprime",
    ),
    "prime_half_range_product_coprime": (
        "beta_half_range_entry_bounds",
        "prime_positive_bounded_product_coprime",
    ),
    "gauss_signed_products_balance_mod": (
        "gauss_signed_pointwise_mul_product_mod",
        "gauss_magnitude_product_eq_half_range",
        "beta_sign_factor_product_power",
        "beta_product_pointwise_mul_exact",
    ),
    "gauss_signed_products_cancel_mod": (
        "gauss_signed_products_balance_mod",
        "prime_half_range_product_coprime",
        "prime_nonzero",
        "mod_eq_cancel_coprime",
        "mul_comm",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "odd_half_strictly_below_modulus": (
        "dcfc161c1e29e2b0ce9d95c2c3cca6c89b40841f0ebe94b51e39428d4df24aba"
    ),
    "gauss_magnitude_positive_below_prime": (
        "31f66c85ac8faa552ea58e117b18aab469985ebab271628806ec7d27a9e87c53"
    ),
    "gauss_magnitude_product_coprime": (
        "1a706f810adad5b7464d21bdcb6a246e9f723f3503b01abcaa286c3b603644a8"
    ),
    "prime_half_range_product_coprime": (
        "c625a47d1b92f0f22d7ea7c94737a938bdfe75d5671f19c8b5176fc7a61fb485"
    ),
    "gauss_signed_products_balance_mod": (
        "dae2bfd87d356ac51201d509ecc7e66c8c6eea295c5cae6e124f428c2b8f55d3"
    ),
    "gauss_signed_products_cancel_mod": (
        "690778d360802afcb1fa12e97f084bc61e4d0dd92c1736664527bc9c928f1174"
    ),
}

EXPECTED_BODY_METRICS = {
    "odd_half_strictly_below_modulus": (45, 20),
    "gauss_magnitude_positive_below_prime": (69, 29),
    "gauss_magnitude_product_coprime": (31, 20),
    "prime_half_range_product_coprime": (41, 28),
    "gauss_signed_products_balance_mod": (148, 70),
    "gauss_signed_products_cancel_mod": (156, 87),
}

_DEPENDENCY_FACTORIES = (
    make_finite_prime_product_coprime_candidate_theorems,
    make_gauss_signed_pointwise_product_candidate_theorems,
    make_gauss_magnitude_product_candidate_theorems,
    make_gauss_sign_product_candidate_theorems,
    make_finite_pointwise_mul_product_candidate_theorems,
)

_BODY_DEADLINE_SECONDS = 60


def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return (
        make_gauss_magnitude_coprime_candidate_theorems(TheoremSpec)
        + make_gauss_product_composition_candidate_theorems(TheoremSpec)
    )


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"Gauss composition body replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def _explicit_dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in _DEPENDENCY_FACTORIES:
        for dependency in factory(TheoremSpec):
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


def test_gauss_product_factories_have_exact_isolated_contracts() -> None:
    magnitude_first = make_gauss_magnitude_coprime_candidate_theorems(TheoremSpec)
    magnitude_second = make_gauss_magnitude_coprime_candidate_theorems(TheoremSpec)
    composition_first = make_gauss_product_composition_candidate_theorems(TheoremSpec)
    composition_second = make_gauss_product_composition_candidate_theorems(TheoremSpec)

    assert magnitude_second == magnitude_first
    assert composition_second == composition_first
    assert tuple(item.name for item in magnitude_first) == MAGNITUDE_NAMES
    assert tuple(item.name for item in composition_first) == COMPOSITION_NAMES

    specs = magnitude_first + composition_first
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in specs
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in specs)


def test_gauss_product_contracts_are_closed_native_pa_expansions() -> None:
    forbidden_surface_tokens = (
        "BetaAt(",
        "BitCount(",
        "Coprime(",
        "HalfRange(",
        "MagnitudeRange(",
        "PointwiseMul(",
        "Pow(",
        "Prime(",
        "Product(",
        "SignFactor(",
        "SignedHalf(",
        "%",
        "^",
        "∣",
        "≡",
    )

    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in forbidden_surface_tokens)


def test_gauss_product_dependency_curried_bodies_are_constructive_and_bounded() -> None:
    rows, elapsed = _body_receipts()
    assert tuple(row[0] for row in rows) == MAGNITUDE_NAMES + COMPOSITION_NAMES
    assert {row[0]: row[1:3] for row in rows} == EXPECTED_BODY_METRICS
    assert elapsed < _BODY_DEADLINE_SECONDS

    for name, nodes, depth, objects, edges, reused, commands in rows:
        print(
            "GAUSS PRODUCT BODY RECEIPT "
            f"name={name} nodes={nodes} depth={depth} objects={objects} "
            f"edges={edges} reused={reused} commands={commands}",
            flush=True,
        )

