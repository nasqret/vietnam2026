"""Pure bridge and real native reconstruction checks; no solver/model launch."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys
import unittest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
import worker
worker.load_kernel()
import vampire_bridge as bridge
import vampire_limits as policy
from peano_lab.engine.state import Goal, MetaVar, start
from peano_lab.engine.tactics import apply_tactic
from peano_lab.kernel.formulas import Eq, parse_formula_with_names
from peano_lab.kernel.terms import Var, Zero
from peano_lab.batch import MODEL_V1_COMMANDS, run_proof
from peano_lab.ui.prove import SurfaceCapabilities


def state_after(theorem, commands=()):
    target, names = parse_formula_with_names(theorem)
    state = start(target, names)
    for command in commands:
        tactic, _, args = command.partition(" ")
        state = apply_tactic(state, tactic, args)
    return state


def fixture_proof(used=("hydra_h0",), *, extra=""):
    """Synthetic dependency fixture, never claimed to be a solver proof."""
    records = [f"fof(f{index},axiom,(hydra_zero = hydra_zero),file(unknown,{name}))."
               for index, name in enumerate(used)]
    parents = ",".join(f"f{index}" for index in range(len(records)))
    records.append(f"fof(final,plain,($false),inference(test_only,[],[{parents}])).")
    return ("% SZS status Theorem for fixture\n% SZS output start Proof for fixture\n"
            + extra + "\n".join(records) + "\n% SZS output end Proof for fixture\n")


def fake_runner(fixture_stdout, **overrides):
    """A test double for transport only; solver claims remain untrusted."""
    def runner(problem):
        return {"available": True, "executed": True, "exit_code": 0, "stdout": fixture_stdout, "stderr": "",
                "status": "completed", "problem_sha256": hashlib.sha256(problem.encode()).hexdigest(), **overrides}
    return runner


class ExportTests(unittest.TestCase):
    def test_scope_and_quantifiers_are_from_the_ast_not_surface_names(self):
        state = state_after("forall a. (forall b. b = a) -> a = a", ("intro quoted'", "intro h"))
        exported = bridge.export_state(state)
        hypothesis = exported.text.splitlines()[1]
        self.assertRegex(hypothesis, r"! \[V0\] : \(V0 = hydra_c0\)")
        self.assertNotIn("quoted'", exported.text)
        self.assertIn("fof(hydra_goal,conjecture,(hydra_c0 = hydra_c0)).", exported.text)
        self.assertEqual(exported.sha256, hashlib.sha256(exported.text.encode()).hexdigest())
        self.assertEqual([item.native_name for item in exported.premises[-6:]], list(bridge.PA_AXIOMS))
        self.assertIn("hydra_pa6", exported.text)
        self.assertNotIn("$int", exported.text)

    def test_order_sugar_is_exported_as_its_native_existential(self):
        exported = bridge.export_state(state_after("forall a b. a <= b -> (a <= b \\/ 0 = 1)"))
        self.assertIn("? [", exported.text)
        self.assertIn("hydra_add", exported.text)
        self.assertNotIn("<=", exported.text)

    def test_unresolved_metavariables_are_not_reinterpreted_as_constants(self):
        state = state_after("0 = 0")
        state = replace(state, goals=(Goal((), Eq(MetaVar(0), Zero()), ()),))
        calls = []
        result = bridge.VampireAdvisor(lambda value: calls.append(value)).advise(state)
        self.assertEqual(result["status"], "unsupported_fragment")
        self.assertEqual(calls, [])
        self.assertEqual(result["solver"]["invocations"], 0)
        self.assertFalse(result["kernel_checked"])

    def test_escaping_rigid_variable_is_rejected(self):
        state = state_after("0 = 0")
        state = replace(state, goals=(Goal((), Eq(Var(1), Zero()), ("n",)),))
        with self.assertRaises(bridge.UnsupportedFragment):
            bridge.export_state(state)


class ProofGraphTests(unittest.TestCase):
    def test_only_refutation_reachable_inputs_are_used(self):
        extra = "fof(unused,axiom,(hydra_zero = hydra_zero),file(unknown,hydra_h1)).\n"
        used, nodes = bridge.proof_used_inputs(fixture_proof(extra=extra), {"hydra_h0", "hydra_h1"})
        self.assertEqual(used, ("hydra_h0",))
        self.assertEqual(nodes, 2)

    def test_actual_recorded_vampire_501_output_parses_without_being_trusted(self):
        path = APP.parent / "output/hydra-hybrid-2026-09-01/vampire-smoke-01.json"
        if not path.is_file():
            self.skipTest("No recorded local solver fixture in this checkout.")
        recorded = json.loads(path.read_bytes())
        self.assertEqual(recorded["exit_code"], 0)
        used, nodes = bridge.proof_used_inputs(recorded["stdout"], {"hyp_0", "goal"})
        self.assertIn("hyp_0", used)
        self.assertEqual(nodes, 8)

    def test_partial_duplicate_missing_and_cyclic_proofs_are_rejected(self):
        good = fixture_proof()
        malformed = [good.replace("% SZS output end Proof for fixture", ""),
                     good.replace("[f0]", "[missing]"),
                     good.replace("[f0]", "[final]"),
                     good.replace("fof(final", "fof(f0"),
                     good.replace("hydra_h0", "unexported_input")]
        for proof in malformed:
            with self.subTest(proof=proof[-150:]), self.assertRaises(bridge.UnsupportedProof):
                bridge.proof_used_inputs(proof, {"hydra_h0"})


class AdviceTests(unittest.TestCase):
    def test_no_runner_or_failed_execution_never_becomes_proof(self):
        state = state_after("forall n m. n = m -> m = n", ("intro n", "intro m", "intro h"))
        self.assertEqual(bridge.VampireAdvisor().advise(state)["solver"]["invocations"], 0)
        for changes in ({"executed": False, "available": False}, {"exit_code": 2},
                        {"status": "timeout"}, {"stdout": "% SZS status Theorem for incomplete\n"}):
            result = bridge.VampireAdvisor(fake_runner(fixture_proof(), **changes)).advise(state)
            self.assertFalse(result["kernel_checked"])
            self.assertEqual(result["suggestions"], [])
            self.assertNotEqual(result["status"], "advisory_theorem")

    def test_actual_timeout_markers_and_szs_resource_stops_keep_bounded_evidence(self):
        state = state_after("0 = 0")
        cases = (("% Time limit reached! \n% Termination reason: Time limit\n", "timeout"),
                 ("% SZS status CPUTimeout for fixture\n", "timeout"),
                 ("% SZS status MemoryOut for fixture\n", "resource_limit"),
                 ("% SZS status ResourceOut for fixture\n", "resource_limit"),
                 ("% SZS status SyntaxError for fixture\n", "solver_error"))
        for stdout, expected in cases:
            with self.subTest(expected=expected, stdout=stdout):
                # The fixed runner classifies these resource markers before
                # returning; an explicit final failed status is authoritative.
                runner_status = "failed" if expected == "solver_error" else expected
                advice = bridge.VampireAdvisor(fake_runner(stdout, exit_code=1, status=runner_status)).advise(state)
                self.assertEqual(advice["status"], expected)
                self.assertEqual(advice["solver"]["exit_code"], 1)
                self.assertEqual(advice["solver"]["invocations"], 1)
                self.assertTrue(advice["solver"]["termination"]["evidence"])
                self.assertNotIn("stdout", advice["solver"])
                self.assertEqual(advice["suggestions"], [])
                self.assertFalse(advice["kernel_checked"])

    def test_resource_flags_or_conflicting_statuses_cannot_authorize_advice(self):
        state = state_after("forall n m. n = m -> m = n", ("intro n", "intro m", "intro h"))
        for change in ({"output_limited": True}, {"status": "resource_limit"}, {"status": "failed"},
                       {"stdout": fixture_proof() + "% SZS status Timeout for fixture\n"}):
            with self.subTest(change=change):
                result = bridge.VampireAdvisor(fake_runner(fixture_proof(), **change)).advise(state)
                self.assertFalse(result["kernel_checked"])
                self.assertEqual(result["suggestions"], [])

    def test_profile_provenance_is_explicit_and_does_not_claim_new_smoke_coverage(self):
        metadata = {"profile": "research", "runtime_policy": policy.RUNTIME_POLICY,
                    "solver_args": policy.solver_args("research"), "limits": policy.solver_limits("research"),
                    "package_smoke": {"profile": "standard", "ready_record_verified": True,
                                      "covers_selected_profile": True}}
        result = bridge.VampireAdvisor(fake_runner("% Time limit reached!\n", exit_code=1, **metadata)).advise(state_after("0 = 0"))
        self.assertEqual(result["status"], "timeout")
        self.assertEqual(result["solver"]["profile"], "research")
        self.assertEqual(result["solver"]["solver_args"], policy.solver_args("research"))
        self.assertFalse(result["solver"]["package_smoke"]["covers_selected_profile"])
        self.assertFalse(result["kernel_checked"])
        metadata["solver_args"] = ["--mode", "portfolio"]
        with self.assertRaises(ValueError):
            bridge.VampireAdvisor(fake_runner(fixture_proof(), **metadata)).advise(state_after("0 = 0"))

    def test_proof_claim_is_advisory_and_native_macro_is_independently_checked(self):
        theorem = "forall n m. n = m -> m = n"
        prefix = ("intro n", "intro m", "intro h")
        result = bridge.VampireAdvisor(fake_runner(fixture_proof())).advise(state_after(theorem, prefix))
        self.assertEqual(result["status"], "advisory_theorem")
        self.assertFalse(result["kernel_checked"])
        self.assertNotIn("stdout", result["solver"])
        self.assertIn(("symm", "exact h"), result["candidates"])
        checked = run_proof(theorem, prefix + ("symm", "exact h"), request_id="vampire-bridge-test",
                            classical=False, on_error="stop",
                            capabilities=SurfaceCapabilities(label="vampire-bridge-test",
                                                             allowed_commands=MODEL_V1_COMMANDS,
                                                             allowed_theorems=frozenset()))
        self.assertTrue(checked.kernel_checked)

    def test_multiple_used_equalities_offer_a_successful_native_rewrite_chain(self):
        theorem = "forall a b c. a = b -> b = c -> S(a) = S(c)"
        prefix = ("intro a", "intro b", "intro c", "intro hab", "intro hbc")
        result = bridge.VampireAdvisor(fake_runner(fixture_proof(("hydra_h0", "hydra_h1")))).advise(state_after(theorem, prefix))
        self.assertTrue(any(len(candidate) == 3 for candidate in result["candidates"]))
        outcomes = [run_proof(theorem, prefix + candidate, request_id="vampire-chain-test",
                              classical=False, on_error="stop",
                              capabilities=SurfaceCapabilities(label="vampire-bridge-test",
                                                               allowed_commands=MODEL_V1_COMMANDS,
                                                               allowed_theorems=frozenset()))
                    for candidate in result["candidates"] if len(candidate) == 3]
        self.assertTrue(any(item.kernel_checked for item in outcomes))

    def test_proof_used_pa1_and_local_negatives_reconstruct_native_contradiction(self):
        cases = (
            ("forall a. S(a) = 0 -> a = 0", ("intro a", "intro h"),
             ("hydra_h0", "hydra_pa1"), ("exfalso", "apply PA1", "assumption")),
            ("forall a. S(a) = 0 -> bot", ("intro a", "intro h"),
             ("hydra_h0", "hydra_pa1"), ("apply PA1", "assumption")),
            ("forall a. (forall z. S(z) = 0 -> bot) -> S(a) = 0 -> a = 0",
             ("intro a", "intro hneg", "intro h"),
             ("hydra_h0", "hydra_h1"), ("exfalso", "apply hneg", "assumption")),
            ("forall a. (a = 0 -> bot) -> a = 0 -> 1 = 0",
             ("intro a", "intro hneg", "intro h"),
             ("hydra_h0", "hydra_h1"), ("exfalso", "apply hneg", "assumption")),
        )
        for theorem, prefix, used, macro in cases:
            with self.subTest(theorem=theorem):
                advice = bridge.VampireAdvisor(fake_runner(fixture_proof(used))).advise(
                    state_after(theorem, prefix), max_candidates=1)
                self.assertEqual(advice["candidates"], (macro,))
                self.assertFalse(advice["kernel_checked"])
                checked = run_proof(theorem, prefix + macro, request_id="vampire-contradiction-test",
                                    classical=False, on_error="stop",
                                    capabilities=SurfaceCapabilities(label="vampire-bridge-test",
                                        allowed_commands=MODEL_V1_COMMANDS, allowed_theorems=frozenset()))
                self.assertTrue(checked.kernel_checked, checked.to_dict(include_trace=False))

    def test_unused_or_shadowed_pa1_does_not_supply_a_contradiction_macro(self):
        unused = "fof(unused,axiom,($false),file(unknown,hydra_pa1)).\n"
        state = state_after("forall a. S(a) = 0 -> a = 0", ("intro a", "intro h"))
        advice = bridge.VampireAdvisor(fake_runner(fixture_proof(("hydra_h0",), extra=unused))).advise(state)
        self.assertTrue(all("apply PA1" not in item for item in advice["candidates"]))
        shadowed = state_after("forall a. 0 = 0 -> S(a) = 0 -> a = 0",
                               ("intro a", "intro PA1", "intro h"))
        advice = bridge.VampireAdvisor(fake_runner(fixture_proof(("hydra_pa1", "hydra_h0")))).advise(shadowed)
        self.assertTrue(all("apply PA1" not in item for item in advice["candidates"]))

    def test_contradictory_axioms_status_requires_a_complete_proof_and_native_reconstruction(self):
        # The live Vampire pilot emitted this status for inconsistent focused
        # premises. The dependency proof here is still a synthetic test fixture.
        theorem = "forall a. S(a) = 0 -> a = 0"
        prefix = ("intro a", "intro h")
        state = state_after(theorem, prefix)
        stdout = fixture_proof(("hydra_h0", "hydra_pa1")).replace(
            "% SZS status Theorem", "% SZS status ContradictoryAxioms", 1)
        advice = bridge.VampireAdvisor(fake_runner(stdout)).advise(state, max_candidates=1)
        self.assertEqual(advice["status"], "advisory_contradiction")
        self.assertEqual(advice["solver"]["szs_status"], "ContradictoryAxioms")
        self.assertTrue(advice["solver"]["advisory_refutation"])
        self.assertFalse(advice["solver"]["advisory_theorem"])
        self.assertFalse(advice["kernel_checked"])
        self.assertEqual(advice["candidates"], (("exfalso", "apply PA1", "assumption"),))
        checked = run_proof(theorem, prefix + advice["candidates"][0],
                            request_id="vampire-contradictory-axioms-test", classical=False, on_error="stop",
                            capabilities=SurfaceCapabilities(label="vampire-bridge-test",
                                allowed_commands=MODEL_V1_COMMANDS, allowed_theorems=frozenset()))
        self.assertTrue(checked.kernel_checked)
        for malformed in ("% SZS status ContradictoryAxioms for fixture\n",
                          stdout.replace("% SZS output end Proof for fixture", ""),
                          stdout.replace("[f0,f1]", "[missing]")):
            with self.subTest(malformed=malformed[-120:]):
                rejected = bridge.VampireAdvisor(fake_runner(malformed)).advise(state)
                self.assertEqual(rejected["status"], "unsupported_proof")
                self.assertEqual(rejected["suggestions"], [])
                self.assertFalse(rejected["kernel_checked"])

    def test_a_forged_theorem_status_cannot_prove_a_false_target(self):
        theorem = "0 = 1"
        for axiom in ("hydra_pa1", "hydra_pa3"):
            with self.subTest(axiom=axiom):
                result = bridge.VampireAdvisor(fake_runner(fixture_proof((axiom,)))).advise(state_after(theorem))
                self.assertFalse(result["kernel_checked"])
                outcomes = [run_proof(theorem, candidate, request_id="vampire-false-test", classical=False,
                                      on_error="stop", capabilities=SurfaceCapabilities(label="vampire-bridge-test",
                                      allowed_commands=MODEL_V1_COMMANDS, allowed_theorems=frozenset()))
                            for candidate in result["candidates"]]
                self.assertTrue(all(not item.kernel_checked for item in outcomes))


if __name__ == "__main__":
    unittest.main()
