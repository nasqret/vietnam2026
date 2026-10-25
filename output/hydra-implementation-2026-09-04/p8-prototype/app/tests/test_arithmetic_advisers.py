from dataclasses import replace
import sys
import unittest

from p8_test_support import (AUTHORITY, CAPS, Clock, Eq, Exists, Forall, Add, Mul, Succ, Var, Zero,
                             execution, identity, state)
from adviser_protocol import (AdviserSession, ProtocolError, RESPONSE_SCHEMA, canonical_json,
                              read_json)
from adviser_polynomials import (PolynomialOps, focus_problem, reconstruct, validate_problem)
from smt_bridge import SmtAdvisor, coefficient_problem
from sympy_bridge import SympyAdvisor


def witness_evidence(poly, *, multipliers=None, factorization=None):
    return {"kind": "polynomial_witness", "witness": poly,
            "multipliers": [] if multipliers is None else multipliers, "factorization": factorization}


class FakeTransport:
    def __init__(self, backend, evidence, *, status="completed", response_status="candidate", mutate=None):
        self.identity = identity(backend)
        self.evidence, self.status, self.response_status, self.mutate = evidence, status, response_status, mutate
        self.calls = 0

    def __call__(self, lease):
        self.calls += 1
        req = lease.request
        response = {"schema": RESPONSE_SCHEMA, "backend": req.backend,
            "identity": self.identity, "input_sha256": req.input_sha256,
            "context_sha256": req.context_sha256, "kernel_checked": False,
            "status": self.response_status, "evidence": self.evidence}
        if self.mutate:
            self.mutate(response)
        return {**execution(req, status=self.status, exit_code=0 if self.status == "completed" else -9),
                "stdout": canonical_json(response), "stderr": b"", "available": True,
                "termination": {"reason": "fixture_only"}}


class ArithmeticDataTests(unittest.TestCase):
    def quotient_state(self):
        # (a + 1) * w = a*a + a, so the parameter-dependent witness is a.
        a, w, one = Var(1), Var(0), Succ(Zero())
        return state(Exists(Eq(Mul(Add(a, one), w), Add(Mul(a, a), a))))

    def test_variable_divisor_proposes_only_native_commands(self):
        problem = focus_problem(self.quotient_state(), "sympy")
        self.assertEqual(problem.payload["divisor"], [[[0], 1], [[1], 1]])
        self.assertEqual(problem.payload["numerator"], [[[1], 1], [[2], 1]])
        evidence = witness_evidence([[[1], 1]], factorization={"unit": 1,
            "factors": [{"polynomial": [[[1], 1]], "power": 1}]})
        self.assertEqual(reconstruct(problem, evidence, "sympy"), ("exists (a)", "ring"))

    def test_negative_sampled_and_wrong_scope_witnesses_fail(self):
        problem = focus_problem(self.quotient_state(), "sympy")
        for value in ([[[0], -1]], [[[0], 7]], [[[1, 0], 1]], [[[1], True]], [[[1], 1.0]]):
            with self.subTest(value=value), self.assertRaises(ProtocolError):
                reconstruct(problem, witness_evidence(value), "sympy")

    def test_bad_factorization_is_rejected_even_with_correct_quotient(self):
        problem = focus_problem(self.quotient_state(), "sympy")
        bad = witness_evidence([[[1], 1]], factorization={"unit": 1,
            "factors": [{"polynomial": [[[0], 1]], "power": 1}]})
        with self.assertRaisesRegex(ProtocolError, "Factorization"):
            reconstruct(problem, bad, "sympy")

    def test_smt_rejects_nonlinear_quantified_and_variable_divisor_fragments(self):
        with self.assertRaises(ProtocolError):
            focus_problem(self.quotient_state(), "cvc5")
        for target in (Eq(Mul(Var(0), Var(0)), Var(0)), Forall(Eq(Var(0), Var(0)))):
            with self.assertRaises(ProtocolError):
                focus_problem(state(target), "cvc5")
        nonlinear_context = (("H", Eq(Mul(Var(0), Var(0)), Var(0))),)
        with self.assertRaises(ProtocolError):
            focus_problem(state(context=nonlinear_context), "cvc5")

    def test_affine_template_matches_every_parameter_coefficient(self):
        a, w = Var(1), Var(0)
        problem = focus_problem(state(Exists(Eq(Add(w, a), Add(a, Add(a, a))))), "cvc5")
        constraints = coefficient_problem(problem.payload)
        self.assertEqual(constraints["parameter_lower_bounds"], [0])
        self.assertEqual(constraints["witness_coefficient_bounds"], [0, 64])
        self.assertEqual([row["target"] for row in constraints["rows"]], [0, 2])
        commands = reconstruct(problem, witness_evidence([[[1], 2]]), "cvc5")
        self.assertTrue(commands[0].startswith("exists ("))
        self.assertEqual(commands[-1], "ring")
        with self.assertRaises(ProtocolError):
            reconstruct(problem, witness_evidence([[[0], 2]]), "cvc5")

    def test_renamed_reordered_parameter_scope_is_not_captured(self):
        # Index 0 is witness; after opening, index 1 is b and index 2 is a.
        target = Exists(Eq(Add(Var(0), Var(1)), Add(Var(2), Var(1))))
        problem = focus_problem(state(target, variables=("b", "alpha")), "cvc5")
        commands = reconstruct(problem, witness_evidence([[[0, 1], 1]]), "cvc5")
        self.assertEqual(commands, ("exists (alpha)", "ring"))

    def test_local_equality_combination_reconstructs_a_bounded_rewrite_macro(self):
        a, b, one = Var(0), Var(1), Succ(Zero())
        value = state(Eq(Add(a, one), Add(b, one)), variables=("a", "b"), context=(("H", Eq(a, b)),))
        problem = focus_problem(value, "cvc5")
        evidence = {"kind": "polynomial_combination", "witness": None,
                    "multipliers": [[[[0, 0], 1]]], "factorization": None}
        commands = reconstruct(problem, evidence, "cvc5")
        self.assertIn("rewrite H", commands)
        self.assertLessEqual(len(commands), 8)
        self.assertTrue(all(len(command.encode()) <= 512 for command in commands))
        bad = {**evidence, "multipliers": [[[[0, 0], 2]]]}
        with self.assertRaises(ProtocolError):
            reconstruct(problem, bad, "cvc5")

    def test_shadowed_names_select_only_the_newest_native_binding(self):
        value = state(context=(("H", Eq(Var(0), Zero())), ("H", Eq(Var(0), Succ(Zero())))))
        problem = focus_problem(value, "sympy")
        self.assertEqual(len(problem.hypotheses), 1)
        self.assertEqual(problem.payload["hypotheses"][0]["right"], [])

    def test_no_negative_integer_domain_or_unbounded_data(self):
        problem = focus_problem(state(), "cvc5")
        bad = {**problem.payload, "natural_lower_bounds": [-1]}
        with self.assertRaises(ProtocolError):
            validate_problem(bad, "cvc5")
        with self.assertRaises(ProtocolError):
            PolynomialOps(1).read([[[9], 1]])
        with self.assertRaises(ProtocolError):
            PolynomialOps(1).read([[[1], 1], [[1], 2]])


class AdviceBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.session = AdviserSession(deadline=400, clock=self.clock)
        self.value = state(Exists(Eq(Var(0), Var(1))))
        self.evidence = witness_evidence([[[1], 1]])

    def advisor(self, transport, *, caps=CAPS):
        cls = SympyAdvisor if transport.identity["backend"] == "sympy" else SmtAdvisor
        return cls(self.session, transport, capabilities=caps, authority_identity=AUTHORITY)

    def test_each_fake_transport_is_a_counted_untrusted_suggestion_not_a_proof(self):
        for backend in ("sympy", "cvc5"):
            transport = FakeTransport(backend, self.evidence)
            result = self.advisor(transport).advise(self.value)
            self.assertEqual(result["status"], "advisory_candidate")
            self.assertFalse(result["kernel_checked"])
            self.assertEqual(result["solver"]["invocations"], 1)
            self.assertEqual(result["suggestions"][0]["commands"], ["exists (a)", "ring"])
        self.assertEqual(self.session.report()["actual_launches"], 2)

    def test_unsat_template_is_no_candidate_and_never_closes(self):
        transport = FakeTransport("cvc5", None, response_status="no_candidate")
        result = self.advisor(transport).advise(self.value)
        self.assertEqual(result["status"], "no_candidate")
        self.assertEqual(result["suggestions"], [])
        self.assertEqual(result["solver"]["invocations"], 1)

    def test_resource_and_transport_stops_override_apparent_valid_evidence(self):
        for status in ("timeout", "cancelled", "failed", "resource_limit", "output_limit"):
            transport = FakeTransport("sympy", self.evidence, status=status)
            result = self.advisor(transport).advise(self.value)
            self.assertEqual(result["status"], status)
            self.assertEqual(result["suggestions"], [])
            self.assertEqual(result["solver"]["invocations"], 1)

    def test_changed_context_or_disallowed_surface_command_is_rejected(self):
        transport = FakeTransport("sympy", self.evidence, mutate=lambda row: row.update(context_sha256="0" * 64))
        self.assertEqual(self.advisor(transport).advise(self.value)["status"], "unsupported_evidence")
        transport = FakeTransport("sympy", self.evidence)
        limited = replace(CAPS, allowed_commands=frozenset({"exists"}))
        self.assertEqual(self.advisor(transport, caps=limited).advise(self.value)["suggestions"], [])

    def test_unsupported_export_never_launches_or_silently_falls_back(self):
        transport = FakeTransport("cvc5", self.evidence)
        advisor = self.advisor(transport)
        result = advisor.advise(state(Forall(Eq(Var(0), Var(0)))))
        self.assertEqual(result["status"], "unsupported")
        self.assertEqual(transport.calls, 0)
        self.assertEqual(self.session.report()["requests"], 0)
        self.assertEqual(advisor.report()["advice_requests"], 1)

    def test_missing_actual_accounting_is_not_reported_as_zero(self):
        class BrokenTransport(FakeTransport):
            def __call__(self, lease):
                row = super().__call__(lease)
                del row["elapsed_seconds"]
                return row
        advisor = self.advisor(BrokenTransport("sympy", self.evidence))
        result = advisor.advise(self.value)
        self.assertEqual(result["status"], "infrastructure_error")
        self.assertIsNone(result["solver"]["invocations"])
        self.assertIsNone(advisor.report()["actual_invocations"])

    def test_no_real_backend_was_imported_by_these_tests(self):
        self.assertNotIn("sympy", sys.modules)
        self.assertNotIn("cvc5", sys.modules)


if __name__ == "__main__":
    unittest.main()
