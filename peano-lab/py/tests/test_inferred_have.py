"""Short local applications elaborate to ordinary HA and readable Lean proofs."""
from __future__ import annotations

import pytest

from peano_lab.engine.inferred_have import (
    InferredHaveError, MAX_APPLICATION_ARGUMENTS, MAX_APPLICATION_BYTES,
    MAX_APPLICATION_DEPTH, parse_inferred_have,
)
from peano_lab.engine.state import start
from peano_lab.engine.tactics import TacticError, apply_tactic, checked_final
from peano_lab.kernel.formulas import parse_formula
from peano_lab.library.defined_edition import (
    DefinedTheoremSpec, compact_tactic_command, compile_defined_spec,
)
from peano_lab.library.lean_proof_reconstruction import reconstruct_theorem
from peano_lab.library.lean_proof_strand import _local_claims
from peano_lab.library.theorems import TheoremSpec


def run(statement, commands):
    state = start(parse_formula(statement))
    for command in commands:
        pieces = command.split(maxsplit=1)
        state = apply_tactic(state, pieces[0], pieces[1] if len(pieces) == 2 else "")
    return state


EXAMPLES = (
    ("forall n. (forall x. x = x) -> n = n",
     ("intro n", "intro lemma", "have h := lemma n", "exact h")),
    ("forall n. (forall x. x = x) -> (n + n) = (n + n)",
     ("intro n", "intro lemma", "have h := lemma (n + n)", "exact h")),
    ("forall n. (forall x. x = x) -> S n = S n",
     ("intro n", "intro lemma", "have h := lemma (S n)", "exact h")),
    ("forall n. (forall x. x = 0 -> S x = 1) -> n = 0 -> S n = 1",
     ("intro n", "intro lemma", "intro hn", "have h := lemma n hn", "exact h")),
    ("forall n. n = 0 -> n = 0",
     ("intro n", "intro hn", "have h := hn", "exact h")),
    ("(forall x y. x = x -> y = y) -> forall z. z = z",
     ("intro lemma", "intro z", "have self : z = z", "refl",
      "have hpartial := lemma z", "have h := hpartial z self", "exact h")),
    ("(forall x. x = x -> forall y. y = y) -> forall n. n = n",
     ("intro lemma", "intro n", "have hn : n = n", "refl",
      "have h := lemma n hn n", "exact h")),
)


@pytest.mark.parametrize("statement,script", EXAMPLES)
def test_inferred_applications_are_checked_by_unchanged_native_kernel(statement, script):
    state = run(statement, script)
    assert state.is_done()
    checked_final(state, parse_formula(statement))


@pytest.mark.parametrize("statement,script", EXAMPLES)
def test_inferred_applications_translate_to_explicit_lean_terms(statement, script):
    spec = TheoremSpec("readable_application", statement, (), script, "Test application.")
    result = reconstruct_theorem(spec, dependency_references={})
    assert result.status == "translated", result.diagnostics
    assert "have h :=" in result.lean_body
    assert "sorry" not in result.lean_body
    assert "native_decide" not in result.lean_body
    assert result.translated_steps == len(script)


@pytest.mark.parametrize("args", (
    "h := missing n", "h := h n", "n := lemma n", "lemma := lemma n",
    "h := lemma ?", "h := lemma _", "h := lemma unknown",
    "h := lemma n 0", "h := Nat.add_comm n", "h : n = n := lemma n",
    "h := lemma (n", "h := lemma n)", "h := lemma (n); exact lemma",
))
def test_bad_inference_is_transactional_and_does_not_guess(args):
    state = run("forall n. (forall x. x = x) -> n = n", ("intro n", "intro lemma"))
    history, goals, proof = state.history, state.goals, state.partial
    with pytest.raises(TacticError):
        apply_tactic(state, "have", args)
    assert state.history == history and state.goals == goals and state.partial is proof


def test_wrong_proof_argument_cannot_discharge_a_premise():
    state = run("forall n. (n = 0 -> n = 1) -> n = n -> n = 1",
                ("intro n", "intro lemma", "intro hn"))
    with pytest.raises(TacticError, match="exact required premise"):
        apply_tactic(state, "have", "h := lemma hn")


def test_new_hypothesis_is_not_available_to_prove_itself():
    state = run("(0 = 0 -> 0 = 1) -> 0 = 1", ("intro lemma",))
    with pytest.raises(TacticError):
        apply_tactic(state, "have", "h := lemma h")


def test_missing_proof_argument_is_not_searched_for():
    state = run("forall n. (n = 0 -> n = 1) -> n = 0 -> n = 1",
                ("intro n", "intro lemma", "intro hn", "have h := lemma"))
    assert not state.is_done()
    with pytest.raises(TacticError):
        apply_tactic(state, "exact", "h")


@pytest.mark.parametrize("args", (
    "h := f " + "0 " * (MAX_APPLICATION_ARGUMENTS + 1),
    "h := f " + "(" * (MAX_APPLICATION_DEPTH + 1) + "0" + ")" * (MAX_APPLICATION_DEPTH + 1),
    "h := " + "x" * MAX_APPLICATION_BYTES,
))
def test_inferred_application_parser_has_fixed_resource_bounds(args):
    with pytest.raises(InferredHaveError):
        parse_inferred_have(args)


def test_defined_authoring_keeps_inferred_application_without_inventing_a_receipt():
    source = "have h := lemma n hn"
    compacted = compact_tactic_command(source)
    assert compacted.local_name == "h"
    assert compacted.proposition is None
    spec = DefinedTheoremSpec("example", "forall n. n = n", (), (source,), "Example.")
    assert compile_defined_spec(spec).script == (source,)
    claims, count = _local_claims((source, "have explicit : 0 = 0"))
    assert count == 2 and len(claims) == 1
    assert claims[0].name == "explicit" and claims[0].exact_ast_equivalence


def test_existing_typed_have_is_shortened_only_after_exact_application_and_replay():
    spec = TheoremSpec("shorten_claim", "forall n. (n = 0 -> n = 1) -> n = 0 -> n = 1", (),
        ("intro n", "intro lemma", "intro hn", "have h : n = 1", "apply lemma", "exact hn", "exact h"), "Example.")
    result = reconstruct_theorem(spec, dependency_references={})
    assert result.status == "translated" and result.inferred_claims == 1
    assert "have h := lemma hn" in result.lean_body
    assert "have h : " not in result.lean_body
    assert result.translated_steps == len(spec.script)
    original = reconstruct_theorem(spec, dependency_references={}, infer_simple_claims=False)
    assert original.inferred_claims == 0 and "have h :" in original.lean_body
    checked_final(run(spec.statement, spec.script), parse_formula(spec.statement))


def test_non_application_local_argument_remains_a_separate_proved_claim():
    spec = TheoremSpec("keep_claim", "forall n. n = n", (),
        ("intro n", "have h : n = n", "refl", "exact h"), "Example.")
    result = reconstruct_theorem(spec, dependency_references={})
    assert result.status == "translated" and result.inferred_claims == 0
    assert "have h :" in result.lean_body


def test_two_premise_application_is_inferred_without_weakening_the_target():
    spec = TheoremSpec("two_premises", "(0 = 0 -> 1 = 1 -> 2 = 2) -> 2 = 2", (),
        ("intro lemma", "have ha : 0 = 0", "refl", "have hb : 1 = 1", "refl",
         "have h : 2 = 2", "apply lemma", "exact ha", "exact hb", "exact h"), "Example.")
    result = reconstruct_theorem(spec, dependency_references={})
    assert result.status == "translated" and result.inferred_claims == 1
    assert "have h := lemma ha hb" in result.lean_body


def test_shortening_retains_induction_branch_labels_and_scopes():
    spec = TheoremSpec("branch_claims", "0 = 0 -> forall n. 0 = 0", (),
        ("intro lemma", "induction n", "have hz : 0 = 0", "exact lemma", "exact hz",
         "have hs : 0 = 0", "exact lemma", "exact hs"), "Example.")
    result = reconstruct_theorem(spec, dependency_references={})
    assert result.status == "translated", result.diagnostics
    assert result.inferred_claims == 2
    assert "| zero =>\n    have hz := lemma" in result.lean_body
    assert "| succ n IH =>\n    have hs := lemma" in result.lean_body
    checked_final(run(spec.statement, spec.script), parse_formula(spec.statement))


@pytest.mark.parametrize("specialize", ["specialize", "forall_elim"])
def test_typed_specialized_application_becomes_one_inferred_claim(specialize):
    statement = "forall n. (forall x. x = 0 -> S x = 1) -> n = 0 -> S n = 1"
    script = ("intro n", "intro lemma", "intro hn", "have h : S n = 1",
              f"{specialize} lemma n", "apply lemma", "exact hn", "exact h")
    result = reconstruct_theorem(TheoremSpec("specialized_claim", statement, (), script, "Example."), dependency_references={})
    assert result.status == "translated", result.diagnostics
    assert result.inferred_claims == 1 and "have h := lemma n hn" in result.lean_body
    assert f"{specialize} lemma" not in result.lean_body
    checked_final(run(statement, script), parse_formula(statement))
    short = script[:3] + ("have h := lemma n hn", "exact h")
    checked_final(run(statement, short), parse_formula(statement))


def test_specialization_inside_claim_does_not_escape_into_the_continuation():
    statement = "forall n. (forall x. x = x) -> (n = n /\\ S n = S n)"
    script = ("intro n", "intro lemma", "have h : n = n", "specialize lemma n", "exact lemma",
              "split", "exact h", "have second := lemma (S n)", "exact second")
    result = reconstruct_theorem(TheoremSpec("specialization_scope", statement, (), script, "Example."), dependency_references={})
    assert result.status == "translated", result.diagnostics
    assert result.inferred_claims == 1 and "have h := lemma n" in result.lean_body
    assert "have second := lemma (Nat.succ (n))" in result.lean_body
    checked_final(run(statement, script), parse_formula(statement))
