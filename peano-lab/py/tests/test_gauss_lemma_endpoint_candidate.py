"""Focused native-body audit for the constructive Gauss endpoint."""

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
from peano_lab.library.finite_pointwise_mul_recode_candidate import (
    make_finite_pointwise_mul_recode_candidate_theorems,
)
from peano_lab.library.gauss_lemma_endpoint_candidate import (
    make_gauss_lemma_endpoint_candidate_theorems,
)
from peano_lab.library.gauss_magnitude_permutation_candidate import (
    make_gauss_magnitude_permutation_candidate_theorems,
)
from peano_lab.library.gauss_product_composition_candidate import (
    make_gauss_product_composition_candidate_theorems,
)
from peano_lab.library.gauss_sign_factor_recode_candidate import (
    make_gauss_sign_factor_recode_candidate_theorems,
)
from peano_lab.library.gauss_signed_prefix_candidate import (
    make_gauss_signed_prefix_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAME = "gauss_lemma_power_congruence_exists"

EXPECTED_DEPENDENCIES = (
    "gauss_half_range_signed_prefix_exists",
    "gauss_signed_half_bit_count_exists",
    "gauss_signed_half_magnitude_range",
    "gauss_signed_half_magnitude_injective",
    "gauss_signed_half_predecessor_recode_exists",
    "beta_product_exists",
    "beta_sign_factor_product_power_exists",
    "beta_pointwise_mul_product_exists",
    "pow_exists",
    "gauss_signed_products_cancel_mod",
)

EXPECTED_STATEMENT_SHA256 = (
    "f70e66bfbec7655df990fbfbdb0eaddd941526e33c9cddac620147533ae482ad"
)

EXPECTED_BODY_METRICS = (258, 83, 256, 257, 2)

_DEPENDENCY_FACTORIES = (
    make_gauss_signed_prefix_candidate_theorems,
    make_gauss_magnitude_permutation_candidate_theorems,
    make_gauss_sign_factor_recode_candidate_theorems,
    make_finite_pointwise_mul_recode_candidate_theorems,
    make_gauss_product_composition_candidate_theorems,
)

_BODY_DEADLINE_SECONDS = 60


def _candidate_spec() -> TheoremSpec:
    (candidate,) = make_gauss_lemma_endpoint_candidate_theorems(TheoremSpec)
    return candidate


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"Gauss endpoint body replay exceeded {seconds}s")

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
def _body_receipt():
    item = _candidate_spec()
    core = _explicit_dependency_core()
    formula = _closed_formula(item.statement)
    target = formula
    for dependency_name in reversed(item.dependencies):
        target = Imp(_closed_formula(core[dependency_name].statement), target)

    started = perf_counter()
    with _body_deadline(_BODY_DEADLINE_SECONDS):
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
    return (
        nodes,
        depth,
        objects,
        edges,
        reused,
        len(item.script),
        perf_counter() - started,
    )


def test_gauss_endpoint_contract_is_exact_closed_native_and_isolated() -> None:
    first = _candidate_spec()
    second = _candidate_spec()
    assert second == first
    assert first.name == EXPECTED_NAME
    assert first.dependencies == EXPECTED_DEPENDENCIES
    assert sha256(first.statement.encode()).hexdigest() == EXPECTED_STATEMENT_SHA256
    assert first.name not in _specs_by_name()

    formula, free_names = parse_formula_with_names(first.statement)
    assert not free_names
    assert formula == parse_formula(first.statement)
    assert formula == _closed_formula(first.statement)

    forbidden_surface_tokens = (
        "BetaAt(",
        "BitCount(",
        "HalfRange(",
        "Pow(",
        "Prime(",
        "Product(",
        "SignedHalfPrefix(",
        "%",
        "^",
        "∣",
        "≡",
    )
    assert all(token not in first.statement for token in forbidden_surface_tokens)
    assert "gle_double_half_base" not in first.statement


def test_gauss_endpoint_hides_codes_beneath_the_e_a_r_interface() -> None:
    statement = _candidate_spec().statement
    outer = statement.index("exists e A R.")
    hidden = statement.index("exists mb mc sb sc.", outer)

    assert statement.startswith("forall p h a b c. p = 2 * h + 1 ->")
    assert outer < hidden
    assert statement.count("exists e A R.") == 1
    assert statement.count("exists mb mc sb sc.") == 1
    assert "S ((2 * h))" in statement
    assert "A + p * gle_left_lemma_endpoint_result" in statement
    assert "R + p * gle_right_lemma_endpoint_result" in statement


def test_gauss_endpoint_dependency_curried_body_is_constructive_and_bounded() -> None:
    nodes, depth, objects, edges, reused, commands, elapsed = _body_receipt()
    assert (nodes, depth, objects, edges, reused) == EXPECTED_BODY_METRICS
    assert commands == 193
    assert elapsed < _BODY_DEADLINE_SECONDS

    print(
        "GAUSS ENDPOINT BODY RECEIPT "
        f"name={EXPECTED_NAME} nodes={nodes} depth={depth} "
        f"objects={objects} edges={edges} reused={reused} "
        f"commands={commands} elapsed={elapsed:.3f}s",
        flush=True,
    )

