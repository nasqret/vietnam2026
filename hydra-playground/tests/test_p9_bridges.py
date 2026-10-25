"""Pure AST/JSON/fake-transport checks; no tactics, E, egg, or model runs."""
import copy
import unittest

from p8_test_support import (AUTHORITY, Add, Eq, Forall, Mul, Succ, SurfaceCapabilities,
                             Var, Zero, state)
from adviser_protocol import AdviserSession, ProtocolError, RESPONSE_SCHEMA, canonical_json, read_json
from e_bridge import EAdvisor, proof_used_inputs
from egraph_bridge import (EGraphAdvisor, EGraphProblem, cost_estimate, focus_problem,
                          parse_term, reconstruct, sexpr)
from vampire_bridge import UnsupportedProof


CAPS = SurfaceCapabilities(label="p9-pure-tests", allowed_commands=frozenset(
    {"trans", "congr", "ring", "refl", "rewrite", "exact", "apply", "exfalso", "assumption", "symm"}),
    allowed_theorems=frozenset())


def e_output(status="Theorem"):
    return ("% Version: 3.3.6\n% SZS status " + status + "\n% SZS output start CNFRefutation\n"
        "fof(c_0_0,hypothesis,hydra_c0=hydra_c1,file('<stdin>',hydra_h0)).\n"
        "fof(c_0_1,hypothesis,hydra_c1=hydra_c2,file('<stdin>',hydra_h1)).\n"
        "fof(c_0_2,axiom,hydra_zero=hydra_zero,file('<stdin>',hydra_pa6)).\n"
        "fof(c_0_3,negated_conjecture,~(hydra_c0=hydra_c2),inference(assume_negation,[status(cth)],[file('<stdin>',hydra_goal)])).\n"
        "cnf(c_0_4,plain,$false,inference(sr,[status(thm)],[c_0_0,c_0_1,c_0_3])).\n"
        "% SZS output end CNFRefutation\n")


def egg_evidence(before="(* v0 (+ v1 v2))", after="(+ (* v0 v1) (* v0 v2))", path=()):
    return {"schema": "hydra-egg-explanation-v1", "rule_set": "peano-semiring-1",
            "steps": [{"before": before, "after": after, "rule": "distrib-left", "direction": "forward", "path": list(path)}],
            "end": after, "graph_nodes": 18, "iterations": 1}


class FakeRunner:
    def __init__(self, backend, payload, *, status="completed", exit_code=0):
        self.backend, self.payload, self.status, self.exit_code = backend, payload, status, exit_code
        self.calls = 0
        self.identity = {"backend": backend, "version": "0.11.0" if backend == "egg" else "3.3.6",
            "profile": "deep", "policy": "test-pinned-runtime", "package_sha256": "2" * 64,
            "helper_sha256": "3" * 64}

    def __call__(self, lease):
        self.calls += 1
        request = lease.request
        if self.backend == "e":
            raw = self.payload.encode()
        else:
            raw = canonical_json({"schema": RESPONSE_SCHEMA, "backend": "egg", "identity": self.identity,
                "input_sha256": request.input_sha256, "context_sha256": request.context_sha256,
                "kernel_checked": False, **self.payload}, 256 * 1024)
        return {"status": self.status, "executed": True, "available": True, "exit_code": self.exit_code,
                "input_sha256": request.input_sha256, "elapsed_seconds": 0.1, "quiescent": True,
                "identity": self.identity, "stdout": raw, "stderr": b""}


def advisor(kind, runner):
    import time
    session = AdviserSession(deadline=time.monotonic() + 90)
    return kind(session, runner, capabilities=CAPS, authority_identity=AUTHORITY), session


class EDependencyTests(unittest.TestCase):
    def test_only_reachable_inputs_are_advisory(self):
        used, count = proof_used_inputs(e_output(), {"hydra_h0", "hydra_h1", "hydra_pa6", "hydra_goal"})
        self.assertEqual(used, ("hydra_h0", "hydra_h1"))
        self.assertEqual(count, 4)

    def test_partial_missing_parent_duplicate_and_cycle_fail(self):
        original = e_output()
        invalid = (
            original.replace("% SZS output end CNFRefutation", ""),
            original.replace("c_0_0,c_0_1,c_0_3", "absent,c_0_1,c_0_3"),
            original.replace("fof(c_0_2,", "fof(c_0_0,"),
            original.replace("c_0_0,c_0_1,c_0_3", "c_0_4,c_0_1,c_0_3"),
        )
        for value in invalid:
            with self.subTest(value=value[-120:]), self.assertRaises(UnsupportedProof):
                proof_used_inputs(value, {"hydra_h0", "hydra_h1", "hydra_pa6", "hydra_goal"})

    def test_no_unexported_assumption_or_type_axiom(self):
        with self.assertRaises(UnsupportedProof):
            proof_used_inputs(e_output().replace("hydra_h1)", "external_lemma)"), {"hydra_h0", "hydra_h1", "hydra_goal"})
        with self.assertRaises(UnsupportedProof):
            proof_used_inputs(e_output().replace("fof(c_0_0,", "tff(c_0_0,"), {"hydra_h0", "hydra_h1", "hydra_goal"})

    def test_fake_transport_generates_native_chain_but_no_truth_claim(self):
        runner = FakeRunner("e", e_output())
        adviser, session = advisor(EAdvisor, runner)
        native = state(Eq(Var(0), Var(2)), variables=("a", "b", "c"),
                       context=(("H", Eq(Var(0), Var(1))), ("K", Eq(Var(1), Var(2)))))
        result = adviser.advise(native)
        self.assertIn(("rewrite H", "rewrite K", "refl"), result["candidates"])
        self.assertFalse(result["kernel_checked"])
        self.assertEqual(session.report()["actual_launches"], 1)
        self.assertEqual(result["solver"]["helper_launches"], 1)
        self.assertTrue(result["solver"]["backend_execution_confirmed"])

    def test_failed_or_partial_transport_overrules_apparent_theorem(self):
        native = state(Eq(Var(0), Var(2)), variables=("a", "b", "c"),
                       context=(("H", Eq(Var(0), Var(1))), ("K", Eq(Var(1), Var(2)))))
        for status in ("failed", "timeout", "output_limit", "resource_limit", "cancelled"):
            runner = FakeRunner("e", e_output(), status=status, exit_code=-9)
            adviser, session = advisor(EAdvisor, runner)
            result = adviser.advise(native)
            self.assertEqual(result["status"], status)
            self.assertFalse(result["suggestions"])
            self.assertEqual(session.report()["actual_launches"], 1)
            self.assertEqual(adviser.report()["confirmed_backend_executions"], 0)

    def test_positive_status_requires_complete_dag(self):
        runner = FakeRunner("e", "% Version: 3.3.6\n% SZS status Theorem\n")
        adviser, _ = advisor(EAdvisor, runner)
        result = adviser.advise(state())
        self.assertEqual(result["status"], "unsupported_evidence")
        self.assertFalse(result["suggestions"])

    def test_all_three_refutation_statuses_require_same_bound_dag(self):
        for status in ("Theorem", "ContradictoryAxioms", "Unsatisfiable"):
            used, _ = proof_used_inputs(e_output(status), {"hydra_h0", "hydra_h1", "hydra_goal"})
            self.assertEqual(used, ("hydra_h0", "hydra_h1"))


class EGraphExplanationTests(unittest.TestCase):
    def problem(self, *, variables=("a", "b", "c"), before=None, after=None):
        data = egg_evidence()
        return EGraphProblem(parse_term(before or data["steps"][0]["before"], 3),
                             parse_term(after or data["end"], 3), variables)

    def test_named_distribution_reconstructs_three_commands(self):
        candidate = reconstruct(self.problem(), egg_evidence())
        self.assertEqual(candidate["commands"], ["trans ((a * b) + (a * c))", "ring", "refl"])
        self.assertTrue(candidate["complete_explanation_reconstructed"])
        self.assertNotIn("kernel_checked", candidate)

    def test_congruence_reconstructs_successor_path(self):
        before, after = "(s (* v0 (+ v1 v2)))", "(s (+ (* v0 v1) (* v0 v2)))"
        data = egg_evidence(before, after, (0,))
        candidate = reconstruct(self.problem(before=before, after=after), data)
        self.assertEqual(candidate["commands"][1:], ["congr", "ring", "refl"])
        self.assertEqual(candidate["used_rewrites"][0]["path"], [0])

    def test_renamed_eigenvariables_keep_exact_scope(self):
        candidate = reconstruct(self.problem(variables=("m", "n", "q")), egg_evidence())
        self.assertEqual(candidate["commands"][0], "trans ((m * n) + (m * q))")

    def test_false_rule_instance_is_rejected(self):
        data = egg_evidence(after="(+ (* v0 v1) (* v1 v2))")
        with self.assertRaises(ProtocolError):
            reconstruct(self.problem(), data)

    def test_changed_sibling_is_not_congruence(self):
        before = "(+ (* v0 (+ v1 v2)) v2)"
        after = "(+ (+ (* v0 v1) (* v0 v2)) v1)"
        with self.assertRaises(ProtocolError):
            reconstruct(self.problem(before=before, after=after), egg_evidence(before, after, (0,)))

    def test_unknown_rule_scope_and_discontinuous_endpoint(self):
        for key, value in (("rule", "cancel-division"), ("before", "v3"), ("path", [True])):
            data = egg_evidence()
            data["steps"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ProtocolError):
                reconstruct(self.problem(), data)
        data = egg_evidence()
        data["end"] = "z"
        with self.assertRaises(ProtocolError):
            reconstruct(self.problem(), data)

    def test_reverse_rule_remains_valid_only_as_an_exact_instance(self):
        before, after = "v0", "(+ v0 z)"
        data = egg_evidence(before, after)
        data["steps"][0].update(rule="add-zero", direction="backward")
        result = reconstruct(self.problem(before=before, after=after), data)
        self.assertEqual(result["commands"], ["trans (a + 0)", "ring", "refl"])

    def test_boundaries_no_injected_symbol_or_escaped_variable(self):
        for text in ("(/ v0 v1)", "(include secret)", "v2", "(+ v0)", "v0 v1", "(s " * 34 + "z" + ")" * 34):
            with self.subTest(text=text[:30]), self.assertRaises(ProtocolError):
                parse_term(text, 2)
        with self.assertRaises(ProtocolError):
            focus_problem(state(Forall(Eq(Var(0), Var(0)))))

    def test_native_cost_estimates_expansion_work(self):
        factored = parse_term("(* (+ v0 v1) (+ v2 v3))", 4)
        expanded = parse_term("(+ (+ (* v0 v2) (* v0 v3)) (+ (* v1 v2) (* v1 v3)))", 4)
        self.assertLess(cost_estimate(factored)[0], cost_estimate(expanded)[0])

    def test_fake_real_contract_is_advisory_and_counted(self):
        runner = FakeRunner("egg", {"status": "candidate", "evidence": egg_evidence()})
        adviser, session = advisor(EGraphAdvisor, runner)
        native = state(Eq(Mul(Var(0), Add(Var(1), Var(2))), Add(Mul(Var(0), Var(1)), Mul(Var(0), Var(2)))), variables=("a", "b", "c"))
        result = adviser.advise(native)
        self.assertEqual(result["status"], "advisory_candidate")
        self.assertEqual(session.report()["requests"], 1)
        self.assertEqual(session.report()["actual_launches"], 1)
        self.assertFalse(result["kernel_checked"])

    def test_graph_iteration_bounds_and_resource_status(self):
        native = state(Eq(Mul(Var(0), Add(Var(1), Var(2))), Add(Mul(Var(0), Var(1)), Mul(Var(0), Var(2)))), variables=("a", "b", "c"))
        for field, value in (("graph_nodes", 4097), ("iterations", 9), ("iterations", True)):
            data = egg_evidence()
            data[field] = value
            adviser, _ = advisor(EGraphAdvisor, FakeRunner("egg", {"status": "candidate", "evidence": data}))
            self.assertFalse(adviser.advise(native)["suggestions"])
        adviser, _ = advisor(EGraphAdvisor, FakeRunner("egg", {"status": "resource_limit", "reason": "node_limit", "evidence": egg_evidence()}))
        result = adviser.advise(native)
        self.assertEqual(result["status"], "resource_limit")
        self.assertFalse(result["suggestions"])


if __name__ == "__main__":
    unittest.main()
