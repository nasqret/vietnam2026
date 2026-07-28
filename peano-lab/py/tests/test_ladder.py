"""M7 theorem ladder: every script ends as a closed checked certificate."""

from __future__ import annotations

from dataclasses import fields, replace

from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Forall, Imp, parse_formula_with_names
from peano_lab.kernel.proofs import Axiom, EqRefl, ForallIntro, Hyp, ImpElim, ImpIntro, Proof
from peano_lab.kernel.terms import Succ, Var, Zero
from peano_lab.library.theorems import (
    THEOREMS,
    get,
    names,
    replay,
    replay_all,
    replay_target,
    _normalise_forall_cuts,
)


EXPECTED_NAMES = (
    "zero_add",
    "add_succ_left",
    "add_comm",
    "add_assoc",
    "mul_zero_left",
    "mul_succ_left",
    "mul_comm",
    "mul_add",
    "mul_assoc",
    "one_mul",
    "mul_one",
    "add_mul",
    "succ_ne_zero",
    "succ_injective",
    "le_refl",
    "le_trans",
    "no_succ_add_fixed",
    "drop_add_prefix_from_fixed",
    "antisymm_from_witnesses",
    "le_antisymm",
    "le_total",
    "add_eq_zero_right",
    "mul_eq_zero",
    "eq_symm",
    "eq_trans",
    "succ_congr",
    "add_congr",
    "mul_congr",
    "add_right_cancel",
    "add_left_cancel",
    "zero_le",
    "le_succ_self",
    "le_zero",
    "add_eq_zero_left",
    "mul_ne_zero",
    "two_large_factors_impossible",
    "prime_two",
    "multiple_zero",
    "one_multiple",
    "multiple_refl",
    "multiple_add",
    "multiple_mul_right",
    "multiple_mul_left",
    "multiple_trans",
    "not_multiple_pointwise",
    "not_multiple_from_pointwise",
    "add_residue",
    "add_residue_lift",
    "square_decomp",
    "square_residue_lift",
    "square_residue_witness",
)


def _mutate_first_pa6(proof: Proof) -> tuple[Proof, bool]:
    if type(proof) is Axiom and proof.name == "PA6":
        return Axiom("PA5"), True
    for item in fields(proof):
        child = getattr(proof, item.name)
        if not isinstance(child, Proof):
            continue
        changed_child, changed = _mutate_first_pa6(child)
        if changed:
            return replace(proof, **{item.name: changed_child}), True
    return proof, False


def test_full_binding_ladder_and_helpers_have_stable_acyclic_order() -> None:
    assert names() == EXPECTED_NAMES
    assert tuple(spec.name for spec in THEOREMS) == EXPECTED_NAMES

    earlier: set[str] = set()
    for spec in THEOREMS:
        formula, free_names = parse_formula_with_names(spec.statement)
        assert not free_names
        assert spec.script
        assert set(spec.dependencies) <= earlier
        found = get(spec.name)
        assert found is spec
        assert replay_target(spec) == replay_target(found)
        assert formula == replay(spec.name).formula
        earlier.add(spec.name)


def test_every_script_replays_and_final_certificate_checks_original_statement() -> None:
    checked = replay_all()

    assert tuple(item.spec.name for item in checked) == EXPECTED_NAMES
    assert all(item.proof_nodes > 0 for item in checked)
    assert all(check((), item.certificate, item.formula) for item in checked)


def test_capstone_is_the_required_zero_product_theorem() -> None:
    capstone = replay("mul_eq_zero")
    expected, names = parse_formula_with_names(
        "forall n m. n * m = 0 -> n = 0 \\/ m = 0"
    )

    assert names == ()
    assert capstone.formula == expected
    assert check((), capstone.certificate, expected)


def test_mutating_a_capstone_arithmetic_leaf_is_rejected() -> None:
    capstone = replay("mul_eq_zero")
    mutation, changed = _mutate_first_pa6(capstone.certificate)

    assert changed
    assert mutation != capstone.certificate
    assert not check((), mutation, capstone.formula)


def test_multi_dependency_cut_does_not_capture_inserted_internal_hypotheses() -> None:
    # This rung uses two dependencies whose own certificates contain local
    # Hyp nodes.  Sequential substitution once corrupted those internal slots.
    theorem = replay("antisymm_from_witnesses")

    assert theorem.spec.dependencies == (
        "add_assoc",
        "drop_add_prefix_from_fixed",
    )
    assert check((), theorem.certificate, theorem.formula)


def test_implication_beta_normalization_avoids_proposition_capture() -> None:
    a = Eq(Zero(), Zero())
    b = Eq(Succ(Zero()), Succ(Zero()))
    redex = ImpElim(ImpIntro(ImpIntro(Hyp(1))), Hyp(0))

    normalized = _normalise_forall_cuts(redex)

    assert normalized == ImpIntro(Hyp(1))
    assert check((a,), normalized, Imp(b, a))


def test_implication_beta_normalization_shifts_terms_below_forall() -> None:
    # The argument mentions ambient x as Var(0). Once inserted below the new
    # y binder it must become Var(1), not be captured as y.
    redex = ImpElim(
        ImpIntro(ForallIntro(Hyp(0))),
        EqRefl(Var(0)),
    )
    target = Forall(Eq(Var(1), Var(1)))

    normalized = _normalise_forall_cuts(redex)

    assert normalized == ForallIntro(EqRefl(Var(1)))
    assert check((), normalized, target)


def test_lookup_is_casefolded_but_unknown_names_do_not_fabricate_entries() -> None:
    assert get(" ADD_COMM ") is get("add_comm")
    assert get("not_a_theorem") is None
    assert get(17) is None  # type: ignore[arg-type]
