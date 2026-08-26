"""M4 ordered simplification and its explicit equality certificates."""

from __future__ import annotations

import random
from dataclasses import fields

import pytest

import peano_lab.engine.tactics as tactics_module
from peano_lab.engine.rewrite import (
    PA_SIMP_SET,
    InvalidSimpRule,
    SimpLimitExceeded,
    SimpRule,
    SimpSet,
    simp_decreases,
    simplify_formula,
)
from peano_lab.engine.state import ProofState, start
from peano_lab.engine.tactics import (
    TacticError,
    TacticLimit,
    apply_tactic,
    checked_final,
    simp,
)
from peano_lab.engine.trace import TraceLogger
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Forall, parse_formula
from peano_lab.kernel.proofs import Axiom, EqRefl, EqSubst, ForallElim, ForallIntro, Hyp, Proof
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero


ZERO = Zero()
ONE = Succ(ZERO)
TWO = Succ(ONE)


def _snapshot(state: ProofState) -> tuple[object, ...]:
    return (
        state.goals,
        state.partial,
        state.history,
        state.target,
        dict(state.subst),
    )


def _contains(proof: Proof, constructor: type[Proof]) -> bool:
    if type(proof) is constructor:
        return True
    return any(
        _contains(value, constructor)
        for item in fields(proof)
        if isinstance((value := getattr(proof, item.name)), Proof)
    )


def test_pa_simp_is_ordered_and_returns_kernel_checked_transports() -> None:
    target = parse_formula("S 0 + S 0 = S (S 0)")
    result = simplify_formula(target, PA_SIMP_SET)

    assert [step.rule for step in result.steps] == ["PA4", "PA3"]
    assert result.formula == Eq(TWO, TWO)
    certificate = result.transport_back(EqRefl(TWO))
    assert _contains(certificate, EqSubst)
    assert check((), certificate, target)


def test_pa6_terminates_even_though_its_first_rewrite_grows_the_tree() -> None:
    target = Eq(Mul(ONE, TWO), TWO)
    result = simplify_formula(target, PA_SIMP_SET)

    assert result.steps[0].rule == "PA6"
    assert result.formula.left == result.formula.right
    assert len(result.steps) < 20
    assert check((), result.transport_back(EqRefl(result.formula.left)), target)


def test_random_closed_term_transport_chains_all_kernel_check() -> None:
    randomizer = random.Random(20260727)

    def term(depth: int):
        if depth == 0:
            return ZERO
        choice = randomizer.randrange(5)
        if choice == 0:
            return ZERO
        if choice == 1:
            return Succ(term(depth - 1))
        constructor = Add if choice < 4 else Mul
        return constructor(term(depth - 1), term(depth - 1))

    for _ in range(100):
        value = term(3)
        target = Eq(value, value)
        result = simplify_formula(target, PA_SIMP_SET)
        assert result.formula.left == result.formula.right
        certificate = result.transport_back(EqRefl(result.formula.left))
        assert check((), certificate, target)


def test_documented_order_accepts_all_pa_rules_and_rejects_growth() -> None:
    x, y = Var(1), Var(0)
    assert simp_decreases(Add(Var(0), ZERO), Var(0))
    assert simp_decreases(Add(x, Succ(y)), Succ(Add(x, y)))
    assert simp_decreases(Mul(Var(0), ZERO), ZERO)
    assert simp_decreases(Mul(x, Succ(y)), Add(Mul(x, y), x))
    assert not simp_decreases(Var(0), Succ(Var(0)))


def test_invalid_late_rule_is_rejected_before_any_simplification() -> None:
    bad = SimpRule(
        "grow",
        Forall(Eq(Var(0), Succ(Var(0)))),
        Hyp(0),
    )
    simp_set = PA_SIMP_SET.extend(bad)
    with pytest.raises(InvalidSimpRule, match="not decreasing"):
        simplify_formula(Eq(Add(ONE, ZERO), ONE), simp_set)


def test_optional_resource_limit_is_honest_and_not_a_termination_claim(
    monkeypatch,
) -> None:
    target = Eq(Add(Add(ONE, ZERO), ZERO), ONE)
    with pytest.raises(SimpLimitExceeded, match="1-step resource limit"):
        simplify_formula(target, PA_SIMP_SET, max_steps=1)

    real_simplify = tactics_module.simplify_formula

    def one_step(formula, simp_set):
        return real_simplify(formula, simp_set, max_steps=1)

    monkeypatch.setattr(tactics_module, "simplify_formula", one_step)
    initial = start(target)
    before = _snapshot(initial)
    with pytest.raises(TacticLimit, match="1-step resource limit"):
        simp(initial)
    assert _snapshot(initial) == before


def test_rule_priority_then_term_preorder_is_deterministic() -> None:
    source = TWO
    first = SimpRule("peel", Eq(source, ONE), Hyp(0))
    second = SimpRule("erase", Eq(source, ZERO), Hyp(1))
    target = Eq(source, ZERO)

    peel_first = simplify_formula(target, SimpSet((first, second)))
    erase_first = simplify_formula(target, SimpSet((second, first)))

    assert [step.rule for step in peel_first.steps] == ["peel"]
    assert peel_first.formula == Eq(ONE, ZERO)
    assert [step.rule for step in erase_first.steps] == ["erase"]
    assert erase_first.formula == Eq(ZERO, ZERO)


def test_permutative_rule_rewrites_only_toward_canonical_order() -> None:
    commutativity = SimpRule(
        "add_comm_local",
        Forall(Forall(Eq(Add(Var(1), Var(0)), Add(Var(0), Var(1))))),
        Hyp(0),
    )
    simp_set = SimpSet((commutativity,))
    descending = Eq(Add(Var(1), Var(0)), Add(Var(0), Var(1)))
    ascending = Eq(Add(Var(0), Var(1)), Add(Var(0), Var(1)))

    result = simplify_formula(descending, simp_set)
    assert len(result.steps) == 1
    assert result.formula == ascending
    assert simplify_formula(ascending, simp_set).steps == ()


def test_simp_tactic_closes_a_quantified_axiom_instance_under_binder() -> None:
    target = parse_formula("forall x. x + 0 = x")
    state = apply_tactic(start(target), "simp")
    certificate = checked_final(state, target)

    assert state.is_done()
    assert _contains(certificate, EqSubst)
    assert check((), certificate, target)


@pytest.mark.parametrize(
    "conclusion",
    (
        "S a = S b",
        "a + c = b + c",
        "a * c = b * c",
        "S ((a + c) + b) = S (a + (c + b))",
    ),
)
def test_simp_finishes_normal_forms_with_checked_congruence(
    conclusion: str,
) -> None:
    premise = (
        "(a + c) + b = a + (c + b)"
        if conclusion.startswith("S ((a + c)")
        else "a = b"
    )
    target = parse_formula(f"forall a b c. {premise} -> {conclusion}")
    state = start(target)
    for name in ("a", "b", "c"):
        state = apply_tactic(state, "intro", name)
    state = apply_tactic(state, "intro", "IH")
    state = apply_tactic(state, "simp")

    assert check((), checked_final(state, target), target)


def test_context_rewrite_under_forall_is_capture_safe() -> None:
    target = parse_formula("forall n. n = 0 -> forall x. n + x = 0 + x")
    state = start(target)
    state = apply_tactic(state, "intro", "n")
    state = apply_tactic(state, "intro", "h")
    state = apply_tactic(state, "simp", "[h]")

    assert check((), checked_final(state, target), target)


def test_explicit_reverse_context_rule_has_the_checked_direction() -> None:
    target = parse_formula("forall n. 0 = n -> n = 0")
    state = start(target)
    state = apply_tactic(state, "intro", "n")
    state = apply_tactic(state, "intro", "h")
    state = apply_tactic(state, "simp", "[<- h]")

    assert check((), checked_final(state, target), target)


def test_simp_can_leave_one_certified_normal_form_goal() -> None:
    target = Eq(Add(ONE, ZERO), ZERO)
    state = apply_tactic(start(target), "simp")

    assert state.current().target == Eq(ONE, ZERO)
    assert _contains(state.partial, EqSubst)


def test_closed_tag_must_be_synthesizable_for_later_specialization() -> None:
    theorem = parse_formula("forall x. x + 0 = x")
    # This eta-expanded proof checks when the forall target is supplied, but
    # the pinned bidirectional kernel cannot infer ForallIntro under an elim.
    checked_but_not_synthesizable = ForallIntro(
        ForallElim(Axiom("PA3"), Var(0))
    )
    assert check((), checked_but_not_synthesizable, theorem)
    tagged = SimpSet(
        (
            SimpRule(
                "eta_pa3",
                theorem,
                checked_but_not_synthesizable,
            ),
        )
    )
    state = start(parse_formula("1 + 0 = 1"))
    before = _snapshot(state)

    with pytest.raises(TacticError, match="cannot be synthesized"):
        simp(state, tagged=tagged)
    assert _snapshot(state) == before


def test_simp_failure_is_transactional_and_trace_records_it() -> None:
    target = parse_formula("forall n. (n = S n) -> n = n")
    state = apply_tactic(start(target), "intro", "n")
    state = apply_tactic(state, "intro", "h")
    before = _snapshot(state)
    trace = TraceLogger(session_id="simp-failure")

    with pytest.raises(TacticError, match="not decreasing"):
        apply_tactic(state, "simp", "[h]", trace=trace)

    assert _snapshot(state) == before
    assert trace.records[-1]["status"] == "error"
    assert trace.records[-1]["goals_before"] == trace.records[-1]["goals_after"]


def test_simp_no_progress_and_bad_syntax_are_transactional() -> None:
    state = start(Eq(ONE, ZERO))
    before = _snapshot(state)
    for args, message in (("", "made no progress"), ("h", "syntax")):
        with pytest.raises(TacticError, match=message):
            simp(state, args)
        assert _snapshot(state) == before


def test_add_comm_induction_uses_prior_tagged_lemmas_in_five_steps() -> None:
    # The two antecedents stand for the already-proved ladder lemmas.  Keeping
    # them as hypotheses exercises the current kernel's reusable-proof API;
    # M7's theorem registry can provide the same checked rules by name.
    target = parse_formula(
        "(forall x. 0 + x = x) -> "
        "(forall x y. S x + y = S (x + y)) -> "
        "forall n m. n + m = m + n"
    )
    state = start(target)
    commands = (
        ("intro", "zero_add"),
        ("intro", "add_succ_left"),
        ("induction", "n"),
        ("simp", "[zero_add]"),
        ("simp", "[add_succ_left, IH]"),
    )
    for tactic, args in commands:
        state = apply_tactic(state, tactic, args)

    assert len(commands) == 5
    assert check((), checked_final(state, target), target)
