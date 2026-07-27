"""The shared untrusted proof reducer and its checked-library facade."""

from __future__ import annotations

import pytest

import driver
import peano_lab.engine.proof_reduction as reduction
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Forall
from peano_lab.kernel.proofs import (
    EqRefl,
    ForallIntro,
    Hyp,
    ImpElim,
    ImpIntro,
    Proof,
)
from peano_lab.kernel.terms import Var, Zero
from peano_lab.library.theorems import (
    LibraryError,
    normalise_cuts as library_normalise_cuts,
    replay,
)


def test_engine_reducer_and_library_facade_preserve_capture_safe_results() -> None:
    proposition = Eq(Zero(), Zero())
    argument = EqRefl(Var(0))
    redex = ImpElim(
        ImpIntro(ForallIntro(Hyp(0))),
        argument,
    )
    target = Forall(Eq(Var(1), Var(1)))

    reduced = reduction.normalise_cuts(redex)

    assert reduced == ForallIntro(EqRefl(Var(1)))
    assert library_normalise_cuts(redex) == reduced
    assert check((proposition,), reduced, target)


def test_engine_and_library_facade_reject_malformed_proofs_with_stable_types() -> None:
    with pytest.raises(
        reduction.ProofReductionError,
        match="^cut normalization needs an exact proof certificate$",
    ):
        reduction.normalise_cuts(object())  # type: ignore[arg-type]

    with pytest.raises(
        LibraryError,
        match="^cut normalization needs an exact proof certificate$",
    ):
        library_normalise_cuts(object())  # type: ignore[arg-type]

    with pytest.raises(
        reduction.ProofReductionError,
        match="^unsupported proof node during normalization: Proof$",
    ):
        reduction.normalise_cuts(Proof())

    malformed = ImpElim(ImpIntro(Hyp(0)), Hyp("bad"))  # type: ignore[arg-type]
    with pytest.raises(
        reduction.ProofReductionError,
        match="^malformed proof certificate during cut normalization$",
    ):
        reduction.normalise_cuts(malformed)
    with pytest.raises(
        LibraryError,
        match="^malformed proof certificate during cut normalization$",
    ):
        library_normalise_cuts(malformed)


def test_recursion_exhaustion_maps_at_both_public_boundaries(monkeypatch) -> None:
    def overflow(_proof: Proof) -> Proof:
        raise RecursionError

    monkeypatch.setattr(reduction, "_normalise_forall_cuts", overflow)

    with pytest.raises(
        reduction.ProofReductionError,
        match="^cut normalization exceeded the host recursion limit$",
    ):
        reduction.normalise_cuts(EqRefl(Zero()))

    with pytest.raises(
        LibraryError,
        match="^cut normalization exceeded the host recursion limit$",
    ):
        library_normalise_cuts(EqRefl(Zero()))


def test_ladder_replay_still_reduces_dependencies_to_closed_certificates() -> None:
    replay.cache_clear()

    for name in ("add_comm", "add_mul", "mul_eq_zero"):
        theorem = replay(name)
        assert check((), theorem.certificate, theorem.formula)


def test_live_use_still_compiles_an_introduction_form_before_qed() -> None:
    session = driver.LabSession()
    session.run("pa prove forall n m. n + m = m + n")
    session.run("use add_comm")

    assert "No open goals" in session.run("exact add_comm")
    finished = session.run("qed")

    assert "No open goals. QED." in finished
    assert "Theorem: ∀ x. ∀ y. x + y = y + x" in finished
