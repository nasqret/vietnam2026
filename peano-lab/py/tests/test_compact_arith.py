"""Cost-pinned PA certificates from the compact recurrence planner."""

from __future__ import annotations

from dataclasses import replace

import pytest

import peano_lab.engine.compact_arith as compact_module
from peano_lab.engine.compact_arith import (
    DEFAULT_COMPACT_ARITH_LIMITS,
    CompactArithAssumption,
    CompactArithLimits,
    compact_arith_checked,
    prove_compact_equation,
)
from peano_lab.engine.state import Goal, MetaVar, start
from peano_lab.engine.tactics import TacticError, TacticLimit, apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Forall, Formula, Imp
from peano_lab.kernel.proofs import EqRefl, EqSym, Hyp, Proof
from peano_lab.kernel.terms import Add, Mul, Succ, Term, Var, Zero


ZERO = Zero()
ONE = Succ(ZERO)
TWO = Succ(ONE)


def _parity_terms():
    # Inside the eliminated existential IH, x is newest and n is next.
    x = Var(0)
    n = Var(1)
    successor_n = Succ(n)
    ih = Eq(Add(Mul(n, n), n), Mul(TWO, x))
    first = Eq(
        Add(Mul(successor_n, successor_n), successor_n),
        Add(Add(Add(Mul(n, n), n), successor_n), successor_n),
    )
    full = Eq(
        Add(Mul(successor_n, successor_n), successor_n),
        Mul(TWO, Add(x, successor_n)),
    )
    return ih, first, full


@pytest.mark.parametrize(
    ("equation", "expected_nodes", "strategy"),
    (
        (
            Eq(Add(Mul(ZERO, ZERO), ZERO), Mul(TWO, ZERO)),
            9,
            "right-zero normalization",
        ),
        (
            Eq(
                Add(Succ(Var(0)), Var(1)),
                Succ(Add(Var(0), Var(1))),
            ),
            20,
            "successor-left addition recurrence",
        ),
        (
            Eq(
                Add(Add(Var(2), Var(1)), Succ(Var(0))),
                Add(Add(Var(2), Var(0)), Succ(Var(1))),
            ),
            51,
            "additive offset-swap recurrence",
        ),
        (
            Eq(
                Mul(Succ(Var(0)), Var(1)),
                Add(Mul(Var(0), Var(1)), Var(1)),
            ),
            75,
            "successor-left multiplication recurrence",
        ),
        (
            Eq(
                Add(Add(Mul(TWO, Var(0)), Var(1)), Var(1)),
                Mul(TWO, Add(Var(0), Var(1))),
            ),
            65,
            "doubling recurrence",
        ),
    ),
)
def test_seeded_recurrences_have_exact_small_checked_costs(
    equation: Eq,
    expected_nodes: int,
    strategy: str,
) -> None:
    result = prove_compact_equation(equation, clock=lambda: 0.0)

    assert result.equation == equation
    assert result.proof_nodes == expected_nodes
    assert result.strategy == strategy
    assert result.proof_depth > 0
    assert result.work_units > 0
    assert check((), result.certificate, equation)


def test_parity_successor_leaf_is_the_record_81_node_expansion() -> None:
    _, first, _ = _parity_terms()

    result = prove_compact_equation(first, clock=lambda: 0.0)

    assert result.proof_nodes == 81
    assert result.strategy == "structural add"
    assert check((), result.certificate, first)


@pytest.mark.parametrize(
    ("equation", "expected_nodes", "strategy"),
    (
        (Eq(Add(Var(0), ONE), Succ(Var(0))), 6, "one-successor bridge"),
        (
            Eq(Add(Var(0), TWO), Succ(Succ(Var(0)))),
            10,
            "two-successor bridge",
        ),
        (
            Eq(
                Mul(Var(1), Add(Var(0), ONE)),
                Add(Mul(Var(1), Var(0)), Var(1)),
            ),
            11,
            "multiplication-by-add-one bridge",
        ),
    ),
)
def test_small_successor_bridges_avoid_full_normalization(
    equation: Eq,
    expected_nodes: int,
    strategy: str,
) -> None:
    result = prove_compact_equation(equation, clock=lambda: 0.0)

    assert result.proof_nodes == expected_nodes
    assert result.strategy == strategy
    assert check((), result.certificate, equation)


def test_selected_ih_closes_the_full_parity_step_in_149_nodes() -> None:
    ih, _, full = _parity_terms()
    selected = (CompactArithAssumption("IH_witness", ih, Hyp(0)),)

    result = prove_compact_equation(
        full,
        context=(ih,),
        assumptions=selected,
        clock=lambda: 0.0,
    )

    assert result.proof_nodes == 149
    assert result.strategy == "IH_witness transport then doubling recurrence"
    assert result.used_assumptions == ("IH_witness",)
    assert check((ih,), result.certificate, full)
    mutated = Eq(full.left, Add(full.right, ONE))
    assert not check((ih,), result.certificate, mutated)
    assert not check((ih,), EqSym(result.certificate), full)


def test_only_explicitly_selected_assumptions_are_consulted() -> None:
    equation = Eq(Var(1), Var(0))
    state = apply_tactic(start(Imp(equation, equation)), "intro", "h")
    before = state

    with pytest.raises(TacticError, match="found no proof"):
        compact_arith_checked(state, clock=lambda: 0.0)
    assert state == before

    selected = (CompactArithAssumption("h", equation, Hyp(0)),)
    completed = compact_arith_checked(
        state,
        selected,
        clock=lambda: 0.0,
    )

    assert completed.is_done()
    assert completed.history[-1].tactic == "compact_arith"
    assert completed.history[-1].args == "[h]"
    assert check((), checked_final(completed, state.target), state.target)


def test_oriented_reverse_assumption_is_ordinary_eqsym_evidence() -> None:
    forward = Eq(Var(1), Var(0))
    reverse = Eq(forward.right, forward.left)
    state = apply_tactic(start(Imp(forward, reverse)), "intro", "h")
    selected = (CompactArithAssumption("<- h", reverse, EqSym(Hyp(0))),)

    completed = compact_arith_checked(state, selected, clock=lambda: 0.0)

    assert completed.is_done()
    assert completed.history[-1].args == "[<- h]"
    assert check((), checked_final(completed, state.target), state.target)


def test_equal_cost_assumptions_preserve_the_written_order() -> None:
    equation = Eq(Var(1), Var(0))
    z = CompactArithAssumption("z", equation, Hyp(0))
    a = CompactArithAssumption("a", equation, Hyp(1))

    za = prove_compact_equation(
        equation,
        context=(equation, equation),
        assumptions=(z, a),
        clock=lambda: 0.0,
    )
    az = prove_compact_equation(
        equation,
        context=(equation, equation),
        assumptions=(a, z),
        clock=lambda: 0.0,
    )

    assert za.certificate == Hyp(0)
    assert za.strategy == "selected assumption z"
    assert za.used_assumptions == ("z",)
    assert az.certificate == Hyp(1)
    assert az.strategy == "selected assumption a"
    assert az.used_assumptions == ("a",)


def test_forged_selected_assumption_is_rejected_before_search() -> None:
    equation = Eq(Var(1), Var(0))
    forged = CompactArithAssumption("forged", equation, Hyp(0))

    with pytest.raises(TacticError, match="rejected compact_arith assumption"):
        prove_compact_equation(
            equation,
            context=(),
            assumptions=(forged,),
            clock=lambda: 0.0,
        )


def test_malformed_targets_and_unresolved_metas_are_rejected() -> None:
    with pytest.raises(TacticError, match="needs an equality goal"):
        prove_compact_equation(  # type: ignore[arg-type]
            Imp(Eq(ZERO, ZERO), Eq(ZERO, ZERO)),
            clock=lambda: 0.0,
        )

    unresolved = Eq(Add(MetaVar(7), ONE), Succ(MetaVar(7)))
    with pytest.raises(TacticError, match="needs rigid terms"):
        prove_compact_equation(unresolved, clock=lambda: 0.0)


def test_final_kernel_rejection_happens_before_state_commit(monkeypatch) -> None:
    equation = Eq(Add(Var(0), ONE), Succ(Var(0)))
    state = start(equation, ("n",))
    before = state
    real_check = compact_module.check

    def reject_result(context, proof, target):
        if target == equation:
            return False
        return real_check(context, proof, target)

    monkeypatch.setattr(compact_module, "check", reject_result)

    with pytest.raises(TacticError, match="rejected the generated"):
        compact_arith_checked(state, clock=lambda: 0.0)
    assert state == before


def test_typed_composition_rejects_mismatched_endpoints_before_kernel(monkeypatch) -> None:
    def forbidden_check(*_args, **_kwargs):
        raise AssertionError("composition mismatch reached the kernel")

    monkeypatch.setattr(compact_module, "check", forbidden_check)
    zero_to_one = compact_module._EqualityProof(ZERO, ONE, EqRefl(ZERO))
    two_to_zero = compact_module._EqualityProof(TWO, ZERO, EqRefl(TWO))

    with pytest.raises(TacticError, match="transitivity endpoints do not compose"):
        compact_module._trans(zero_to_one, two_to_zero)

    wrong_body = compact_module._EqualityProof(ONE, ONE, EqRefl(ONE))
    with pytest.raises(TacticError, match="substitution source does not match"):
        compact_module._subst_eq(Eq(Var(0), ZERO), zero_to_one, wrong_body)

    congruence = compact_module._cong_add(
        compact_module._refl(ZERO),
        compact_module._refl(ONE),
    )
    with pytest.raises(TacticError, match="congruence endpoints do not match"):
        compact_module._expect_endpoints(
            congruence,
            Add(ZERO, ZERO),
            Add(ZERO, ZERO),
            "congruence",
        )


def test_result_is_structurally_deterministic() -> None:
    _, first, _ = _parity_terms()

    first_result = prove_compact_equation(first, clock=lambda: 0.0)
    second_result = prove_compact_equation(first, clock=lambda: 0.0)

    assert first_result == second_result


def test_proof_and_time_limits_are_typed_and_deterministic() -> None:
    double = Eq(
        Add(Add(Mul(TWO, Var(0)), Var(1)), Var(1)),
        Mul(TWO, Add(Var(0), Var(1))),
    )
    with pytest.raises(TacticLimit, match="64-proof-node limit"):
        prove_compact_equation(
            double,
            limits=replace(DEFAULT_COMPACT_ARITH_LIMITS, max_proof_nodes=64),
            clock=lambda: 0.0,
        )

    readings = iter((0.0, 2.0))
    with pytest.raises(TacticLimit, match="1-second time limit"):
        prove_compact_equation(
            Eq(ZERO, ZERO),
            limits=replace(DEFAULT_COMPACT_ARITH_LIMITS, max_seconds=1.0),
            clock=lambda: next(readings, 2.0),
        )


def test_annotation_assumption_and_whole_partial_limits_are_enforced() -> None:
    qone = Eq(Add(Var(0), ONE), Succ(Var(0)))
    with pytest.raises(TacticLimit, match="1-annotation-node limit"):
        prove_compact_equation(
            qone,
            limits=replace(
                DEFAULT_COMPACT_ARITH_LIMITS,
                max_annotation_nodes=1,
            ),
            clock=lambda: 0.0,
        )

    equality = Eq(Var(1), Var(0))
    assumptions = (
        CompactArithAssumption("h", equality, Hyp(0)),
        CompactArithAssumption("again", equality, Hyp(0)),
    )
    with pytest.raises(TacticLimit, match="1-selected-assumption limit"):
        prove_compact_equation(
            equality,
            context=(equality,),
            assumptions=assumptions,
            limits=replace(DEFAULT_COMPACT_ARITH_LIMITS, max_assumptions=1),
            clock=lambda: 0.0,
        )

    state = start(qone, ("n",))
    before = state
    with pytest.raises(TacticLimit, match="1-partial-proof-node limit"):
        compact_arith_checked(
            state,
            limits=replace(DEFAULT_COMPACT_ARITH_LIMITS, max_partial_nodes=1),
            clock=lambda: 0.0,
        )
    assert state == before


def test_input_ast_limit_is_aggregate_across_both_equation_sides() -> None:
    def balanced_zeros(leaves: int):
        level = [ZERO] * leaves
        while len(level) > 1:
            following = []
            for index in range(0, len(level), 2):
                if index + 1 == len(level):
                    following.append(level[index])
                else:
                    following.append(Add(level[index], level[index + 1]))
            level = following
        return level[0]

    left = balanced_zeros(80)  # 159 nodes: individually below the 256 cap.
    right = balanced_zeros(80)
    with pytest.raises(TacticLimit, match="256-AST-node limit"):
        prove_compact_equation(Eq(left, right), clock=lambda: 0.0)


def test_malformed_assumption_proof_clock_and_partial_are_typed_failures() -> None:
    equation = Eq(Var(1), Var(0))
    malformed = CompactArithAssumption("bad", equation, Proof())
    with pytest.raises(TacticError, match="malformed proof certificate"):
        prove_compact_equation(
            equation,
            context=(equation,),
            assumptions=(malformed,),
            clock=lambda: 0.0,
        )

    with pytest.raises(TacticError, match="clock must return a finite number"):
        prove_compact_equation(Eq(ZERO, ZERO), clock=lambda: float("nan"))
    with pytest.raises(TacticError, match="clock failed"):
        prove_compact_equation(
            Eq(ZERO, ZERO),
            clock=lambda: (_ for _ in ()).throw(RuntimeError("clock broke")),
        )

    state = start(Eq(ZERO, ZERO))
    malformed_state = replace(state, partial_certificate_with_holes=Proof())
    with pytest.raises(TacticError, match="malformed partial proof certificate"):
        compact_arith_checked(malformed_state, clock=lambda: 0.0)

    missing_child = object.__new__(EqSym)
    malformed = CompactArithAssumption("missing", equation, missing_child)
    with pytest.raises(TacticError, match="malformed proof certificate"):
        prove_compact_equation(
            equation,
            context=(equation,),
            assumptions=(malformed,),
            clock=lambda: 0.0,
        )

    missing_term = object.__new__(Succ)
    with pytest.raises(TacticError, match="malformed input term"):
        prove_compact_equation(Eq(missing_term, ZERO), clock=lambda: 0.0)


def test_shallowly_forged_state_fields_are_typed_failures() -> None:
    state = start(Eq(ZERO, ZERO))
    malformed_states = (
        replace(state, goals=("not a goal",)),
        replace(state, goals=(Goal((), Formula()),)),
        replace(state, history=(object(),)),
        replace(state, target=Formula()),
        replace(state, subst={7: Term()}),
    )

    for malformed in malformed_states:
        with pytest.raises(TacticError, match="valid exact proof state"):
            compact_arith_checked(malformed, clock=lambda: 0.0)  # type: ignore[arg-type]

    missing_fields = object.__new__(compact_module.ProofState)
    with pytest.raises(TacticError, match="valid exact proof state"):
        compact_arith_checked(missing_fields, clock=lambda: 0.0)


def test_outer_deadline_covers_preflight_and_post_replacement(monkeypatch) -> None:
    equation = Eq(Add(Var(0), ONE), Succ(Var(0)))
    state = start(equation, ("n",))
    limits = replace(DEFAULT_COMPACT_ARITH_LIMITS, max_seconds=1.0)

    readings = iter((0.0, 2.0))
    with pytest.raises(TacticLimit, match="1-second time limit"):
        compact_arith_checked(
            state,
            limits=limits,
            clock=lambda: next(readings, 2.0),
        )

    crossed_replacement = False
    real_replace = compact_module.replace_current_hole

    def mark_replacement(*args, **kwargs):
        nonlocal crossed_replacement
        result = real_replace(*args, **kwargs)
        crossed_replacement = True
        return result

    monkeypatch.setattr(compact_module, "replace_current_hole", mark_replacement)
    with pytest.raises(TacticLimit, match="1-second time limit"):
        compact_arith_checked(
            state,
            limits=limits,
            clock=lambda: 2.0 if crossed_replacement else 0.0,
        )
    assert not state.is_done()


def test_recurrence_templates_are_checked_with_empty_context(monkeypatch) -> None:
    assert check(
        (),
        compact_module._ADD_SUCC,
        compact_module._ADD_SUCC_FORMULA,
    )
    real_check = compact_module.check
    template_contexts: list[tuple[Formula, ...]] = []

    def record_template_checks(context, proof, target):
        if type(target) is Forall:
            template_contexts.append(context)
        return real_check(context, proof, target)

    monkeypatch.setattr(compact_module, "check", record_template_checks)
    equations = (
        Eq(
            Add(Add(Var(2), Var(1)), Succ(Var(0))),
            Add(Add(Var(2), Var(0)), Succ(Var(1))),
        ),
        Eq(
            Mul(Succ(Var(0)), Var(1)),
            Add(Mul(Var(0), Var(1)), Var(1)),
        ),
        Eq(
            Add(Add(Mul(TWO, Var(0)), Var(1)), Var(1)),
            Mul(TWO, Add(Var(0), Var(1))),
        ),
    )
    for equation in equations:
        prove_compact_equation(equation, clock=lambda: 0.0)

    assert len(template_contexts) >= 4
    assert all(context == () for context in template_contexts)


def test_every_structural_resource_limit_has_a_typed_failure_path() -> None:
    qone = Eq(Add(Var(0), ONE), Succ(Var(0)))
    for changes, fragment in (
        ({"max_ast_nodes": 3}, "3-AST-node limit"),
        ({"max_ast_depth": 2}, "2-AST-depth limit"),
        ({"max_annotation_depth": 1}, "1-annotation-depth limit"),
        ({"max_work_units": 1}, "1-work-unit limit"),
        ({"max_proof_depth": 1}, "1-proof-depth limit"),
    ):
        with pytest.raises(TacticLimit, match=fragment):
            prove_compact_equation(
                qone,
                limits=replace(DEFAULT_COMPACT_ARITH_LIMITS, **changes),
                clock=lambda: 0.0,
            )

    ih, _, full = _parity_terms()
    selected = (CompactArithAssumption("IH_witness", ih, Hyp(0)),)
    for changes, fragment in (
        ({"max_template_instances": 1}, "1-template-instance limit"),
        ({"max_search_states": 1}, "1-search-state limit"),
        ({"max_candidates": 1}, "1-candidate limit"),
    ):
        with pytest.raises(TacticLimit, match=fragment):
            prove_compact_equation(
                full,
                context=(ih,),
                assumptions=selected,
                limits=replace(DEFAULT_COMPACT_ARITH_LIMITS, **changes),
                clock=lambda: 0.0,
            )

    state = start(qone, ("n",))
    before = state
    with pytest.raises(TacticLimit, match="1-partial-proof-depth limit"):
        compact_arith_checked(
            state,
            limits=replace(DEFAULT_COMPACT_ARITH_LIMITS, max_partial_depth=1),
            clock=lambda: 0.0,
        )
    assert state == before


def test_host_recursion_failure_is_typed_and_transactional(monkeypatch) -> None:
    equation = Eq(Add(Var(0), ONE), Succ(Var(0)))
    state = start(equation, ("n",))
    before = state

    def overflow(_proof):
        raise RecursionError

    monkeypatch.setattr(compact_module, "normalise_cuts", overflow)
    with pytest.raises(TacticLimit, match="host recursion limit"):
        compact_arith_checked(state, clock=lambda: 0.0)
    assert state == before

@pytest.mark.parametrize(
    "kwargs",
    (
        {"max_ast_nodes": 0},
        {"max_assumptions": 0},
        {"max_template_instances": 0},
        {"max_search_states": 0},
        {"max_candidates": 0},
        {"max_annotation_nodes": 0},
        {"max_work_units": True},
        {"max_proof_nodes": 0},
        {"max_partial_depth": 0},
        {"max_seconds": 0},
        {"max_seconds": "slow"},
        {"max_seconds": float("nan")},
    ),
)
def test_limits_reject_invalid_values(kwargs: dict[str, object]) -> None:
    with pytest.raises(
        ValueError,
        match=r"compact_arith (?:integer limits|time limit) must be positive",
    ):
        CompactArithLimits(**kwargs)  # type: ignore[arg-type]
