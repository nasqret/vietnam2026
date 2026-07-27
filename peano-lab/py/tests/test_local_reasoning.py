"""Focused soundness tests for engine-only ``have``/``suffices`` cuts."""

from __future__ import annotations

from dataclasses import fields, replace

import pytest

import driver
from peano_lab.engine.proof_reduction import (
    LocalHave,
    LocalSuffices,
    compile_local_cuts,
)
from peano_lab.engine.state import ProofState, holes_in, invariants_ok, start
from peano_lab.engine.tactics import (
    InvalidProof,
    TacticError,
    TacticSyntaxError,
    apply_tactic,
    checked_final,
)
from peano_lab.engine.trace import TraceLogger
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Exists, Forall, Imp, Or, parse_formula
from peano_lab.kernel.proofs import (
    EqRefl,
    ExistsElim,
    ForallIntro,
    Hyp,
    ImpIntro,
    OrElim,
    Proof,
)
from peano_lab.kernel.terms import Succ, Var, Zero
from peano_lab.library.theorems import LibraryError
from peano_lab.ui import prove


ZERO = Zero()
ONE = Succ(ZERO)
TRUE = Eq(ZERO, ZERO)
OTHER_TRUE = Eq(ONE, ONE)


def _snapshot(state: ProofState) -> tuple[object, ...]:
    return state.goals, state.partial, state.history, dict(state.subst)


def _contains_local_cut(proof: Proof) -> bool:
    if type(proof) in (LocalHave, LocalSuffices):
        return True
    return any(
        _contains_local_cut(child)
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


def test_have_and_suffices_schedule_matching_holes_without_context_leakage() -> None:
    initial = start(TRUE)

    have_state = apply_tactic(initial, "have", "h : 0 = 0")
    assert invariants_ok(have_state)
    assert type(have_state.partial) is LocalHave
    assert holes_in(have_state.partial) == (
        have_state.partial.proof.id,
        have_state.partial.body.id,
    )
    assert have_state.goals[0].context == ()
    assert have_state.goals[0].target == TRUE
    assert have_state.goals[1].context == (("h", TRUE),)
    assert have_state.goals[1].target == TRUE
    before = _snapshot(have_state)
    with pytest.raises(TacticError, match="unknown hypothesis 'h'"):
        apply_tactic(have_state, "exact", "h")
    assert _snapshot(have_state) == before

    have_state = apply_tactic(have_state, "refl")
    have_state = apply_tactic(have_state, "exact", "h")
    assert check((), checked_final(have_state, TRUE), TRUE)

    suffices_state = apply_tactic(initial, "suffices", "h : 0 = 0")
    assert invariants_ok(suffices_state)
    assert type(suffices_state.partial) is LocalSuffices
    assert holes_in(suffices_state.partial) == (
        suffices_state.partial.body.id,
        suffices_state.partial.proof.id,
    )
    assert suffices_state.goals[0].context == (("h", TRUE),)
    assert suffices_state.goals[0].target == TRUE
    assert suffices_state.goals[1].context == ()
    assert suffices_state.goals[1].target == TRUE

    suffices_state = apply_tactic(suffices_state, "exact", "h")
    before = _snapshot(suffices_state)
    with pytest.raises(TacticError, match="unknown hypothesis 'h'"):
        apply_tactic(suffices_state, "exact", "h")
    assert _snapshot(suffices_state) == before
    suffices_state = apply_tactic(suffices_state, "refl")
    assert check((), checked_final(suffices_state, TRUE), TRUE)


@pytest.mark.parametrize(
    ("tactic", "args", "error_type", "message"),
    [
        ("have", "n : n = n", TacticError, "already in use"),
        ("suffices", "n : n = n", TacticError, "already in use"),
        ("have", "h n = n", TacticSyntaxError, "syntax"),
        ("suffices", "h :", TacticSyntaxError, "syntax"),
        ("have", "h : m = m", TacticError, "unknown term variable"),
        ("suffices", "h : m = m", TacticError, "unknown term variable"),
    ],
)
def test_local_statement_failures_are_final_and_transactional(
    tactic: str,
    args: str,
    error_type: type[TacticError],
    message: str,
) -> None:
    state = apply_tactic(start(parse_formula("forall n. n = n")), "intro", "n")
    before = _snapshot(state)

    with pytest.raises(error_type, match=message):
        apply_tactic(state, tactic, args)

    assert _snapshot(state) == before


@pytest.mark.parametrize(
    ("tactic", "args", "expected_goals"),
    [
        ("have", "h : 0 = 0", ["⊢ 0 = 0", "h : 0 = 0 ⊢ 0 = 0"]),
        ("suffices", "h : 0 = 0", ["h : 0 = 0 ⊢ 0 = 0", "⊢ 0 = 0"]),
    ],
)
def test_local_reasoning_is_undoable_and_has_deterministic_v1_traces(
    tactic: str,
    args: str,
    expected_goals: list[str],
) -> None:
    initial = start(TRUE)
    logger = TraceLogger(session_id=f"local-{tactic}")

    scheduled = apply_tactic(initial, tactic, args, trace=logger)
    assert logger.records[-1]["status"] == "ok"
    assert logger.records[-1]["goals_after"] == expected_goals

    restored = apply_tactic(scheduled, "undo", trace=logger)
    assert restored is initial
    assert logger.records[-1]["status"] == "ok"
    assert logger.records[-1]["goals_after"] == ["⊢ 0 = 0"]

    before = _snapshot(restored)
    with pytest.raises(TacticSyntaxError):
        apply_tactic(restored, tactic, "malformed", trace=logger)
    assert _snapshot(restored) == before
    assert logger.records[-1]["status"] == "error"
    assert logger.records[-1]["goals_after"] == logger.records[-1]["goals_before"]


@pytest.mark.parametrize(
    "raw",
    [
        LocalHave(TRUE, EqRefl(ZERO), Hyp(0)),
        LocalSuffices(TRUE, Hyp(0), EqRefl(ZERO)),
    ],
    ids=("have", "suffices"),
)
def test_raw_local_nodes_have_no_kernel_authority_but_qed_compiles_them(
    raw: Proof,
) -> None:
    assert not check((), raw, TRUE)

    compiled = compile_local_cuts(raw)
    assert compiled == EqRefl(ZERO)
    assert check((), compiled, TRUE)

    closed_state = replace(
        start(TRUE),
        goals=(),
        partial_certificate_with_holes=raw,
    )
    assert checked_final(closed_state, TRUE) == compiled


def test_nested_mixed_local_cuts_are_fully_eliminated_without_scope_leakage() -> None:
    # The outer lemma is itself a suffices cut. In the outer body, the inner
    # suffices body deliberately refers past its own binder to the outer local
    # hypothesis. Both layers must disappear before the kernel is called.
    raw = LocalHave(
        TRUE,
        LocalSuffices(TRUE, Hyp(0), EqRefl(ZERO)),
        LocalSuffices(TRUE, Hyp(1), Hyp(0)),
    )

    compiled = compile_local_cuts(raw)

    assert not _contains_local_cut(compiled)
    assert compiled == EqRefl(ZERO)
    assert check((), compiled, TRUE)


@pytest.mark.parametrize(
    "commands",
    [
        ("have h : 0 = 0; first [exact h | refl]",),
        ("suffices h : 0 = 0; first [exact h | refl]",),
        ("have h : 0 = 0", "all_goals first [exact h | refl]"),
        ("suffices h : 0 = 0", "all_goals first [exact h | refl]"),
        ("have h : 0 = 0", "focus 2 exact h", "focus 1 refl"),
        ("suffices h : 0 = 0", "focus 2 refl", "focus 1 exact h"),
        ("have h : 0 = 0; exact h <|> refl",),
        ("suffices h : 0 = 0; exact h <|> refl",),
    ],
)
def test_local_reasoning_composes_with_surface_tacticals(
    commands: tuple[str, ...],
) -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0")
    for command in commands:
        output = session.run(command)
        assert "Tactic error:" not in output, (command, output)
    assert "No open goals. QED." in session.run("qed")


def test_local_reasoning_is_retained_by_script_export() -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0")
    for command in ("have h : 0 = 0", "refl", "exact h"):
        session.run(command)

    active = session.run("script")
    assert "have h : 0 = 0" in active
    assert "refl" in active
    assert "exact h" in active
    assert "\r\n  qed\r\n" not in active

    assert "No open goals. QED." in session.run("qed")
    retained = session.run("script")
    assert "have h : 0 = 0" in retained
    assert "\r\n  qed\r\n" in retained


def test_local_compiler_failure_rejects_qed_and_keeps_session_alive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0")
    for command in ("have h : 0 = 0", "refl", "exact h"):
        session.run(command)
    owner = prove.get_owner(session.webstate)
    assert owner is not None

    def fail_compilation(_proof: Proof) -> Proof:
        raise LibraryError("planned local compiler failure")

    monkeypatch.setattr(prove, "normalise_cuts", fail_compilation)
    output = session.run("qed")

    assert "QED check failed: proof cut normalization failed" in output
    assert prove.get_owner(session.webstate) is owner


def test_malformed_or_false_local_nodes_cannot_survive_checked_finalization() -> None:
    malformed = LocalHave(object(), EqRefl(ZERO), Hyp(0))  # type: ignore[arg-type]
    malformed_state = replace(
        start(TRUE),
        goals=(),
        partial_certificate_with_holes=malformed,
    )
    with pytest.raises(InvalidProof, match="local-reasoning cut compilation failed"):
        checked_final(malformed_state, TRUE)

    false_cut = LocalHave(TRUE, EqRefl(ONE), Hyp(0))
    false_state = replace(
        start(TRUE),
        goals=(),
        partial_certificate_with_holes=false_cut,
    )
    with pytest.raises(InvalidProof, match="independent kernel rejected"):
        checked_final(false_state, TRUE)


@pytest.mark.parametrize("tactic", ["have", "suffices"])
def test_local_proposition_proofs_do_not_capture_newer_hypotheses(tactic: str) -> None:
    target = Imp(TRUE, Imp(OTHER_TRUE, TRUE))
    state = apply_tactic(start(target), "intro", "a")

    if tactic == "have":
        state = apply_tactic(state, tactic, "h : 0 = 0")
        state = apply_tactic(state, "exact", "a")
        state = apply_tactic(state, "intro", "b")
        state = apply_tactic(state, "exact", "h")
    else:
        state = apply_tactic(state, tactic, "h : 0 = 0")
        state = apply_tactic(state, "intro", "b")
        state = apply_tactic(state, "exact", "h")
        state = apply_tactic(state, "exact", "a")

    certificate = checked_final(state, target)

    assert certificate == ImpIntro(ImpIntro(Hyp(1)))
    assert check((), certificate, target)


@pytest.mark.parametrize("tactic", ["have", "suffices"])
def test_local_term_proofs_are_lifted_below_later_forall_binders(tactic: str) -> None:
    target = Forall(Forall(Eq(Var(1), Var(1))))
    state = apply_tactic(start(target), "intro", "x")

    if tactic == "have":
        state = apply_tactic(state, tactic, "hx : x = x")
        state = apply_tactic(state, "refl")
        state = apply_tactic(state, "intro", "y")
        state = apply_tactic(state, "exact", "hx")
    else:
        state = apply_tactic(state, tactic, "hx : x = x")
        state = apply_tactic(state, "intro", "y")
        state = apply_tactic(state, "exact", "hx")
        state = apply_tactic(state, "refl")

    certificate = checked_final(state, target)

    assert certificate == ForallIntro(ForallIntro(EqRefl(Var(1))))
    assert check((), certificate, target)


@pytest.mark.parametrize("cut", [LocalHave, LocalSuffices], ids=("have", "suffices"))
def test_local_cut_opening_respects_or_and_exists_branch_scopes(cut: type[Proof]) -> None:
    p_or_q = Or(TRUE, OTHER_TRUE)
    or_target = Imp(TRUE, Imp(p_or_q, TRUE))
    or_body = OrElim(Hyp(1), Hyp(1), Hyp(1))
    or_local = (
        LocalHave(TRUE, Hyp(1), or_body)
        if cut is LocalHave
        else LocalSuffices(TRUE, or_body, Hyp(1))
    )
    or_raw = ImpIntro(ImpIntro(or_local))
    or_compiled = compile_local_cuts(or_raw)

    assert or_compiled == ImpIntro(ImpIntro(OrElim(Hyp(0), Hyp(2), Hyp(2))))
    assert check((), or_compiled, or_target)

    # Opening below ExistsElim crosses both its branch hypothesis and its term
    # witness. The inserted x=x proof must therefore become refl(#1).
    exists_reflexive = Exists(Eq(Var(0), Var(0)))
    exists_target = Forall(Imp(exists_reflexive, Eq(Var(0), Var(0))))
    exists_body = ExistsElim(Hyp(1), Hyp(1))
    exists_local = (
        LocalHave(Eq(Var(0), Var(0)), EqRefl(Var(0)), exists_body)
        if cut is LocalHave
        else LocalSuffices(Eq(Var(0), Var(0)), exists_body, EqRefl(Var(0)))
    )
    exists_raw = ForallIntro(ImpIntro(exists_local))
    exists_compiled = compile_local_cuts(exists_raw)

    assert exists_compiled == ForallIntro(
        ImpIntro(ExistsElim(Hyp(0), EqRefl(Var(1))))
    )
    assert check((), exists_compiled, exists_target)
