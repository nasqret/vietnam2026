"""P3 local Cut sharing, checked by the unchanged original kernel.

Run in a dedicated process: ``python3 -I -B tests/test_native_sharing.py``.
This suite executes only small authored native certificates/scripts: no proof
search, arithmetic automation, model, solver, server, or remote work. The
immutable original checker is loaded directly, using the byte-identical kernel
data constructors from native-v7. Full scripts also get a fresh native replay.
"""

from dataclasses import fields, replace
import importlib.util
from pathlib import Path
import sys
import unittest


APP = Path(__file__).resolve().parents[1]
NATIVE = APP / "native-v7"
FROZEN = (APP.parent / "_deploy" /
          "hydra-retention-evaluation-recovery-execution-20260831" /
          "peano-lab" / "py" / "peano_lab")
loaded = sys.modules.get("peano_lab")
if loaded is not None and Path(loaded.__file__).resolve().parent != NATIVE / "peano_lab":
    raise RuntimeError("test_native_sharing.py needs an isolated native-v7 process")
sys.path.insert(0, str(NATIVE))

from peano_lab.batch import MODEL_V1_COMMANDS, run_proof
from peano_lab.engine import proof_reduction as reduction
from peano_lab.engine.proof_reduction import LocalHave, LocalSuffices
from peano_lab.engine.state import (
    MetaVar, apply_proof_subst, final_certificate, holes_in, invariants_ok,
    metas_in_proof, proof_identity_metrics, proof_size, replace_hole, start,
)
from peano_lab.engine.tactics import (
    InvalidProof, TacticError, apply_tactic, checked_final,
)
from peano_lab.engine.trace import TraceLogger
from peano_lab.kernel.formulas import (
    And, Eq, Exists, Forall, Imp, Or, parse_formula_with_names,
)
from peano_lab.kernel.proofs import (
    AndIntro, Cut, EqRefl, EqSubst, EqTrans, ExistsElim, ForallElim,
    ForallIntro, Hyp, ImpElim, ImpIntro, Ind, OrElim, Proof,
)
from peano_lab.kernel.subst import shift_formula
from peano_lab.kernel.terms import Succ, Var, Zero
from peano_lab.ui.prove import (
    ProofSession, SurfaceCapabilities, checked_surface_final, run_surface,
)


ZERO = Zero()
ONE = Succ(ZERO)
TRUE = Eq(ZERO, ZERO)
FALSE = Eq(ZERO, ONE)
OTHER = Eq(ONE, ONE)
AUTHORITY = SurfaceCapabilities(
    label="hydra-p3-local-sharing-test",
    allowed_commands=MODEL_V1_COMMANDS,
    allowed_theorems=frozenset(),
)


def local(kind, proposition, lemma, body, conclusion=None):
    if kind is LocalHave:
        return kind(proposition, lemma, body, conclusion=conclusion)
    return kind(proposition, body, lemma, conclusion=conclusion)


def nodes(proof):
    pending = [proof]
    while pending:
        current = pending.pop()
        yield current
        pending.extend(
            child for field in fields(current)
            if isinstance((child := getattr(current, field.name)), Proof)
        )


class NativeSharingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Checking with this separately loaded file is stronger than trusting
        # a new surface's success flag. Its exact AST classes must also match
        # the immutable source, since the checker deliberately uses type().
        original_files = {p.name: p.read_bytes() for p in (FROZEN / "kernel").glob("*.py")}
        working_files = {p.name: p.read_bytes()
                         for p in (NATIVE / "peano_lab" / "kernel").glob("*.py")}
        if not original_files or working_files != original_files:
            raise AssertionError("P3 must not change any kernel source file")
        name = "peano_lab.kernel._p3_unchanged_checker"
        spec = importlib.util.spec_from_file_location(name, FROZEN / "kernel" / "checker.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        cls.original_check = staticmethod(module.check)

    def assert_original_checks(self, proof, target, context=()):
        self.assertTrue(self.original_check(context, proof, target))
        self.assertFalse(any(type(node) in (LocalHave, LocalSuffices) for node in nodes(proof)))

    def test_tactics_annotate_target_without_changing_goal_or_hole_order(self):
        for command, kind in (("have", LocalHave), ("suffices", LocalSuffices)):
            with self.subTest(command=command):
                initial = start(OTHER)
                state = apply_tactic(initial, command, "h : 0=0")
                raw = state.partial
                self.assertIs(type(raw), kind)
                self.assertEqual(raw.conclusion, OTHER)
                self.assertEqual(raw.proposition, TRUE)
                ordered = ((raw.proof.id, raw.body.id) if kind is LocalHave
                           else (raw.body.id, raw.proof.id))
                self.assertEqual(holes_in(raw), ordered)
                self.assertTrue(invariants_ok(state))
                lemma_goal, body_goal = (state.goals if kind is LocalHave
                                         else reversed(state.goals))
                self.assertEqual(lemma_goal.context, ())
                self.assertEqual(body_goal.context, (("h", TRUE),))
                self.assertEqual(body_goal.target, OTHER)
                self.assertIs(apply_tactic(state, "undo"), initial)
                # A local hypothesis must never leak into its own obligation.
                if kind is LocalHave:
                    with self.assertRaises(TacticError):
                        apply_tactic(state, "exact", "h")
                copied = replace_hole(raw, raw.body.id, EqRefl(ONE))
                self.assertEqual(copied.conclusion, OTHER)
                self.assertEqual(initial.target, OTHER)

    def test_annotated_nodes_preserve_one_checked_lemma_child(self):
        lemma = EqRefl(ZERO)
        for kind in (LocalHave, LocalSuffices):
            with self.subTest(kind=kind.__name__):
                raw = local(kind, TRUE, lemma, AndIntro(Hyp(0), Hyp(0)), And(TRUE, TRUE))
                self.assertFalse(self.original_check((), raw, And(TRUE, TRUE)))
                compiled = reduction.compile_local_cuts(raw)
                self.assertEqual(compiled, Cut(TRUE, And(TRUE, TRUE), lemma,
                                               AndIntro(Hyp(0), Hyp(0))))
                self.assertIs(compiled.lemma, lemma)
                self.assert_original_checks(compiled, And(TRUE, TRUE))
                # Already-kernel certificates retain the old identity promise.
                self.assertIs(reduction.compile_local_cuts(compiled), compiled)

    def test_repeated_nontrivial_lemma_stays_shared_instead_of_beta_copied(self):
        lemma = EqRefl(ZERO)
        for _ in range(20):
            lemma = EqTrans(lemma, EqRefl(ZERO))
        target, body = TRUE, Hyp(0)
        for _ in range(15):
            target, body = And(TRUE, target), AndIntro(Hyp(0), body)
        raw = LocalHave(TRUE, lemma, body, conclusion=target)
        compiled = reduction.compile_local_cuts(raw)
        legacy = reduction.compile_local_cuts(replace(raw, conclusion=None))
        self.assert_original_checks(compiled, target)
        self.assert_original_checks(legacy, target)
        self.assertEqual(sum(type(node) is Cut for node in nodes(compiled)), 1)
        self.assertLess(proof_size(compiled) * 5, proof_size(legacy))
        self.assertLess(proof_identity_metrics(compiled)[0] * 5,
                        proof_identity_metrics(legacy)[0])

    def test_legacy_unannotated_constructors_keep_capture_safe_semantics(self):
        raw = LocalHave(TRUE, LocalSuffices(TRUE, Hyp(0), EqRefl(ZERO)),
                        LocalSuffices(TRUE, Hyp(1), Hyp(0)))
        compiled = reduction.compile_local_cuts(raw)
        self.assertEqual(compiled, EqRefl(ZERO))
        self.assert_original_checks(compiled, TRUE)
        # Retained legacy nodes still lift both term and proposition scopes.
        raw = ImpElim(ImpIntro(ForallIntro(LocalHave(
            Eq(Var(1), Var(1)), Hyp(0), Hyp(0)))), EqRefl(Var(0)))
        compiled = reduction.normalise_cuts(raw)
        self.assertEqual(compiled, ForallIntro(EqRefl(Var(1))))
        self.assert_original_checks(compiled, Forall(Eq(Var(1), Var(1))))

    def test_nested_mixed_cuts_and_or_exists_binders_keep_context_indices(self):
        for kind in (LocalHave, LocalSuffices):
            with self.subTest(kind=kind.__name__):
                mixed = local(kind, TRUE, EqRefl(ZERO),
                              LocalSuffices(TRUE, Hyp(1), Hyp(0), conclusion=TRUE), TRUE)
                compiled = reduction.compile_local_cuts(mixed)
                self.assert_original_checks(compiled, TRUE)
                self.assertEqual(sum(type(node) is Cut for node in nodes(compiled)), 2)
                disjunction = Or(TRUE, OTHER)
                or_raw = ImpIntro(ImpIntro(local(
                    kind, TRUE, Hyp(1), OrElim(Hyp(1), Hyp(1), Hyp(1)), TRUE)))
                self.assert_original_checks(reduction.compile_local_cuts(or_raw),
                                            Imp(TRUE, Imp(disjunction, TRUE)))
                x_refl = Eq(Var(0), Var(0))
                exists_raw = ForallIntro(ImpIntro(local(
                    kind, x_refl, EqRefl(Var(0)), ExistsElim(Hyp(1), Hyp(1)), x_refl)))
                self.assert_original_checks(reduction.compile_local_cuts(exists_raw),
                                            Forall(Imp(Exists(x_refl), x_refl)))

    def test_term_opening_transforms_local_annotations_below_binders(self):
        for kind in (LocalHave, LocalSuffices):
            with self.subTest(kind=kind.__name__):
                outer = Eq(Var(1), Var(1))
                raw = ForallIntro(local(kind, outer, EqRefl(Var(1)), Hyp(0), outer))
                opened = reduction._open_term_slot(raw, ONE)
                self.assertEqual(opened.body.proposition, OTHER)
                self.assertEqual(opened.body.conclusion, OTHER)
                compiled = reduction.compile_local_cuts(opened)
                self.assert_original_checks(compiled, Forall(OTHER))
                self.assertEqual(reduction.normalise_cuts(ForallElim(ForallIntro(raw), ONE)),
                                 compiled)
                legacy = replace(raw, body=replace(raw.body, conclusion=None))
                self.assertIsNone(reduction._open_term_slot(legacy, ONE).body.conclusion)
                witness_branch = ExistsElim(Hyp(0), local(
                    kind, outer, EqRefl(Var(1)), Hyp(0), outer))
                opened_branch = reduction._open_term_slot(witness_branch, ONE)
                self.assertEqual(opened_branch.body.conclusion, OTHER)
                self.assert_original_checks(reduction.compile_local_cuts(opened_branch),
                                            OTHER, (Exists(Eq(Var(0), Var(0))),))

    def test_weakening_and_hypothesis_substitution_preserve_annotations(self):
        free = Eq(Var(0), Var(0))
        target = Forall(Eq(Var(1), Var(1)))
        for kind in (LocalHave, LocalSuffices):
            with self.subTest(kind=kind.__name__):
                raw = local(kind, free, Hyp(0), ForallIntro(Hyp(1)), target)
                shifted = reduction._shift_hypotheses(raw, 1)
                self.assertEqual(shifted.proof, Hyp(1))
                self.assertEqual(shifted.body, ForallIntro(Hyp(2)))
                self.assertEqual(shifted.conclusion, target)
                self.assert_original_checks(reduction.compile_local_cuts(shifted),
                                            target, (OTHER, free))
                lifted = reduction._shift_proof_terms(raw, 1)
                self.assertEqual(lifted.proposition, Eq(Var(1), Var(1)))
                self.assertEqual(lifted.conclusion, shift_formula(target, 1))
                self.assert_original_checks(reduction.compile_local_cuts(lifted),
                                            shift_formula(target, 1), (Eq(Var(1), Var(1)),))
                substituted = reduction._open_hypothesis(raw, EqRefl(Var(0)))
                self.assertEqual(substituted.conclusion, target)
                self.assert_original_checks(reduction.compile_local_cuts(substituted), target)

    def test_motive_cutoffs_survive_term_opening_around_local_cuts(self):
        motive = Eq(Var(0), Var(0))
        annotated = LocalHave(TRUE, EqRefl(ZERO), EqRefl(Var(0)),
                              conclusion=Eq(Var(0), Var(0)))
        proof = EqSubst(motive, EqRefl(Var(0)), annotated)
        opened = reduction._open_term_slot(proof, ONE)
        self.assertEqual(opened.motive, motive)
        self.assertEqual(opened.body.conclusion, OTHER)
        self.assert_original_checks(reduction.compile_local_cuts(opened), OTHER)
        # Induction's distinguished motive variable is not the opened ambient
        # parameter. Both its base and step still carry local annotations.
        parametric_motive = Eq(Var(1), Var(1))
        base = LocalHave(TRUE, EqRefl(ZERO), EqRefl(Var(0)),
                         conclusion=Eq(Var(0), Var(0)))
        step = ForallIntro(ImpIntro(LocalSuffices(
            TRUE, EqRefl(Var(1)), EqRefl(ZERO), conclusion=Eq(Var(1), Var(1)))))
        opened_ind = reduction._open_term_slot(Ind(parametric_motive, base, step), ONE)
        self.assertEqual(opened_ind.motive, OTHER)
        self.assert_original_checks(reduction.compile_local_cuts(opened_ind), Forall(OTHER))

    def test_metavariable_substitution_updates_conclusions_without_losing_sharing(self):
        unknown = MetaVar(7001)
        equation = Eq(unknown, unknown)
        child = LocalHave(TRUE, EqRefl(ZERO), EqRefl(unknown), conclusion=equation)
        transformed = apply_proof_subst(AndIntro(child, child), {7001: ONE})
        self.assertIs(transformed.left, transformed.right)
        self.assertEqual(transformed.left.conclusion, OTHER)
        self.assertEqual(metas_in_proof(transformed), ())
        compiled = reduction.compile_local_cuts(transformed)
        self.assertIs(compiled.left, compiled.right)
        self.assert_original_checks(compiled, And(OTHER, OTHER))
        # This also exercises native unification updating an already-recorded
        # target annotation when an existential witness is solved later.
        theorem = "exists x. x=1"
        target, names = parse_formula_with_names(theorem)
        state = start(target, names)
        for command in ("exists ?", "have h : 0=0", "refl", "refl"):
            tactic, _, args = command.partition(" ")
            state = apply_tactic(state, tactic, args)
        certificate = checked_final(state, target)
        cuts = [node for node in nodes(certificate) if type(node) is Cut]
        self.assertEqual(cuts[0].conclusion, Eq(ONE, ONE))
        self.assert_original_checks(certificate, target)

    def test_cut_erasure_copy_retains_local_conclusion(self):
        for kind in (LocalHave, LocalSuffices):
            with self.subTest(kind=kind.__name__):
                inner = Cut(TRUE, TRUE, EqRefl(ZERO), Hyp(0))
                raw = local(kind, TRUE, inner, Hyp(0), TRUE)
                erased = reduction.erase_trusted_cuts(raw)
                self.assertIs(type(erased), kind)
                self.assertEqual(erased.conclusion, TRUE)
                self.assertFalse(any(type(node) is Cut for node in nodes(erased)))
                self.assert_original_checks(reduction.compile_local_cuts(erased), TRUE)

    def test_bad_annotations_lemmas_and_targets_have_no_authority(self):
        for kind in (LocalHave, LocalSuffices):
            with self.subTest(kind=kind.__name__):
                malformed = local(kind, TRUE, EqRefl(ZERO), Hyp(0), object())
                with self.assertRaises(reduction.ProofReductionError):
                    reduction.compile_local_cuts(malformed)
                for raw in (
                    local(kind, TRUE, EqRefl(ZERO), Hyp(0), FALSE),
                    local(kind, FALSE, EqRefl(ZERO), Hyp(0), FALSE),
                    # An unused but false claimed lemma must still be checked.
                    local(kind, FALSE, EqRefl(ZERO), EqRefl(ZERO), TRUE),
                    local(kind, TRUE, EqRefl(ZERO), Hyp(1), TRUE),
                ):
                    compiled = reduction.compile_local_cuts(raw)
                    self.assertFalse(self.original_check((), compiled, raw.conclusion))
                    closed = replace(start(raw.conclusion), goals=(),
                                     partial_certificate_with_holes=raw)
                    with self.assertRaises(InvalidProof):
                        checked_final(closed, raw.conclusion)
                good = reduction.compile_local_cuts(local(kind, TRUE, EqRefl(ZERO), Hyp(0), TRUE))
                self.assertFalse(self.original_check((), good, FALSE))
                forged = replace(start(TRUE), goals=(), partial_certificate_with_holes=good)
                with self.assertRaises(InvalidProof):
                    checked_final(forged, FALSE)

    def test_full_scripts_receive_original_kernel_check_and_fresh_native_replay(self):
        examples = (
            ("forall a b. (a=a /\\ b=b)",
             ("have identity : forall x. x=x", "intro x", "refl", "intro a", "intro b",
              "split", "apply identity", "apply identity")),
            ("forall a b. a=b -> b=a",
             ("suffices symmetry : forall x y. x=y -> y=x", "intro a", "intro b",
              "intro ab", "apply symmetry", "exact ab", "intro x", "intro y",
              "intro xy", "symm", "exact xy")),
            ("forall x y. x=x",
             ("intro x", "have hx : x=x", "refl", "intro y", "exact hx")),
            ("forall x. (exists y. y=y) -> x=x",
             ("intro x", "intro hex", "have hx : x=x", "refl", "cases hex", "exact hx")),
        )
        for index, (theorem, commands) in enumerate(examples):
            with self.subTest(theorem=theorem):
                target, names = parse_formula_with_names(theorem)
                owner = ProofSession(state=start(target, names), original_target=target,
                    original_names=names, target_source=theorem, classical=False,
                    trace=TraceLogger(session_id=f"local-sharing-first-{index}"))
                for command in commands:
                    owner = run_surface(owner, command, capabilities=AUTHORITY)
                self.assertEqual(owner.original_target, target)
                self.assertEqual(owner.state.goals, ())
                self.assertIsNotNone(final_certificate(owner.state))
                certificate = checked_surface_final(owner.state, target)
                self.assert_original_checks(certificate, target)
                self.assertTrue(any(type(node) is Cut for node in nodes(certificate)))
                replay = run_proof(theorem, commands, capabilities=AUTHORITY,
                                   request_id=f"local-sharing-replay-{index}")
                self.assertEqual(replay.status, "proved", replay.error)
                self.assertTrue(replay.kernel_checked)
                self.assertEqual(replay.goals, ())
                self.assertEqual(replay.tactics_applied, len(commands))
                self.assertEqual(replay.proof_nodes, proof_size(certificate))
                self.assertIsNotNone(replay.trace)


if __name__ == "__main__":
    unittest.main()
