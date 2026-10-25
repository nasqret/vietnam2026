from dataclasses import replace
import json
import unittest

from p8_test_support import AUTHORITY, CAPS, Clock, Eq, Goal, Var, Zero, execution, identity, request, state
from adviser_protocol import (AdviserSession, BudgetStop, ProtocolError, RESPONSE_SCHEMA,
    canonical_json, checked_response, external_request, read_json, semantic_context)


class JsonTests(unittest.TestCase):
    def test_duplicate_float_and_oversized_values_are_rejected(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":1.5}', b'{"a":NaN}', b'{"a":123456789012345678901}'):
            with self.subTest(raw=raw), self.assertRaises(ProtocolError):
                read_json(raw)
        with self.assertRaises(ProtocolError):
            canonical_json({"x": "a" * 65536})

    def test_cycles_and_unicode_fail_boundedly(self):
        cycle = []
        cycle.append(cycle)
        with self.assertRaises(ProtocolError):
            canonical_json(cycle)
        with self.assertRaises(ProtocolError):
            canonical_json({"x": "\ud800"})


class SemanticContextTests(unittest.TestCase):
    def test_all_goals_order_context_and_original_target_are_bound(self):
        a, z = Var(0), Zero()
        first = Goal((("H", Eq(a, z)),), Eq(a, a), ("a",))
        second = Goal((), Eq(z, a), ("a",))
        original = state(goals=(first, second))
        raw = semantic_context(original, CAPS, authority_identity=AUTHORITY)
        variants = [replace(original, goals=(second, first)),
                    replace(original, goals=(first, replace(second, target=Eq(z, z)))),
                    replace(original, target=Eq(a, z)),
                    replace(original, goals=(replace(first, context=(("J", Eq(a, z)),)), second)),
                    replace(original, subst={7: z})]
        for variant in variants:
            self.assertNotEqual(raw, semantic_context(variant, CAPS, authority_identity=AUTHORITY))
        self.assertNotEqual(raw, semantic_context(original, CAPS, authority_identity="4" * 64))
        limited = replace(CAPS, allowed_commands=frozenset({"refl"}))
        self.assertNotEqual(raw, semantic_context(original, limited, authority_identity=AUTHORITY))

    def test_scoped_binders_and_shadowed_assumptions_are_preserved(self):
        from p8_test_support import Exists
        value = state(Exists(Eq(Var(0), Var(1))), context=(("H", Eq(Var(0), Zero())), ("H", Eq(Zero(), Zero()))))
        parsed = read_json(semantic_context(value, CAPS, authority_identity=AUTHORITY))
        self.assertEqual(len(parsed["goals"][0]["context"]), 2)
        self.assertEqual(parsed["goals"][0]["target"], ["exists", ["eq", ["var", 0], ["var", 1]]])

    def test_escaped_variables_and_unbounded_context_are_rejected(self):
        with self.assertRaises(ProtocolError):
            semantic_context(state(Eq(Var(1), Zero())), CAPS, authority_identity=AUTHORITY)
        many = state(goals=tuple(Goal((), Eq(Var(0), Zero()), ("a",)) for _ in range(33)))
        with self.assertRaises(ProtocolError):
            semantic_context(many, CAPS, authority_identity=AUTHORITY)

    def test_cache_identity_uses_full_context_and_backend_bytes(self):
        first = request()
        second = external_request("sympy", first.data,
            canonical_json({"schema": "hydra-adviser-semantic-context-v1", "test": False}), identity("sympy"))
        self.assertEqual(first.input_sha256, second.input_sha256)
        self.assertNotEqual(first.exact_cache_key, second.exact_cache_key)
        altered = {**identity("sympy"), "version": "different"}
        third = external_request("sympy", first.data, first.context, altered)
        self.assertNotEqual(first.exact_cache_key, third.exact_cache_key)


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.session = AdviserSession(deadline=400, clock=self.clock)

    def test_all_backends_share_one_request_cap_including_failed_and_cached_work(self):
        for index in range(12):
            backend = ("vampire", "sympy", "cvc5")[index % 3]
            req = request(backend)
            with self.session.lease(req) as lease:
                cached = index % 3 == 0
                value = execution(req, status="cache_hit" if cached else "timeout", executed=not cached,
                                  exit_code=None if cached else -9)
                self.clock.value += 0.2
                lease.record_external(value, cache_hit=cached, quiescent=True)
        report = self.session.report()
        self.assertEqual((report["requests"], report["actual_launches"], report["cache_hits"]), (12, 8, 4))
        self.assertEqual(len(report["records"]), 12)
        with self.assertRaisesRegex(BudgetStop, "shared_request_limit"):
            self.session.lease(request("cvc5"))

    def test_wall_and_completion_reserves_refuse_dispatch(self):
        small = AdviserSession(deadline=400, clock=self.clock, max_external_wall=8)
        with self.assertRaisesRegex(BudgetStop, "shared_wall_limit"):
            small.lease(request("cvc5"))
        near = AdviserSession(deadline=120, clock=self.clock)
        with self.assertRaisesRegex(BudgetStop, "deadline_reserve"):
            near.lease(request("vampire"))

    def test_one_live_lease_and_cancellation_are_authoritative(self):
        req = request()
        with self.session.lease(req) as lease:
            with self.assertRaisesRegex(BudgetStop, "external_child_busy"):
                self.session.lease(request("cvc5"))
            lease.record_external(execution(req), quiescent=True)
        stopped = AdviserSession(deadline=400, clock=self.clock, should_stop=lambda: True)
        with self.assertRaisesRegex(BudgetStop, "cancelled"):
            stopped.lease(req)
        self.assertEqual(stopped.report()["actual_launches"], 0)

    def test_unavailable_is_a_real_request_but_not_a_launch(self):
        req = request()
        with self.session.lease(req) as lease:
            self.clock.value += 0.75
            lease.record_external(execution(req, status="unavailable", executed=False, elapsed=0.1, exit_code=None),
                                  quiescent=True)
        report = self.session.report()
        self.assertEqual(report["requests"], 1)
        self.assertEqual(report["actual_launches"], 0)
        self.assertEqual(report["external_wall_seconds"], 0.75)

    def test_missing_accounting_is_unknown_and_blocks_future_children(self):
        req = request()
        with self.assertRaises(ProtocolError):
            with self.session.lease(req) as lease:
                bad = execution(req)
                del bad["elapsed_seconds"]
                lease.record_external(bad, quiescent=True)
        report = self.session.report()
        self.assertIsNone(report["actual_launches"])
        self.assertFalse(report["accounting_complete"])
        with self.assertRaises(BudgetStop):
            self.session.lease(req)

    def test_abandoned_or_unreaped_attempt_cannot_free_the_lease(self):
        with self.session.lease(request()):
            pass
        self.assertIsNone(self.session.report()["actual_launches"])
        self.assertIsNotNone(self.session.report()["active_request"])
        fresh = AdviserSession(deadline=400, clock=self.clock)
        req = request()
        with fresh.lease(req) as lease:
            lease.record_external(execution(req, status="failed", exit_code=None), quiescent=False)
        self.assertEqual(fresh.report()["actual_launches"], 1)
        self.assertEqual(fresh.report()["blocked_reason"], "external_child_not_reaped")

    def test_mismatched_input_and_conflicting_launch_counts_are_not_zero(self):
        for patch in ({"input_sha256": "0" * 64}, {"invocations": 0}):
            session = AdviserSession(deadline=400, clock=self.clock)
            req = request()
            with self.assertRaises(ProtocolError):
                with session.lease(req) as lease:
                    lease.record_external({**execution(req), **patch}, quiescent=True)
            self.assertIsNone(session.report()["actual_launches"])


class ResponseTests(unittest.TestCase):
    def response(self, req):
        return {"schema": RESPONSE_SCHEMA, "backend": req.backend,
            "identity": read_json(req.identity), "input_sha256": req.input_sha256,
            "context_sha256": req.context_sha256, "kernel_checked": False,
            "status": "candidate", "evidence": {"still": "untrusted"}}

    def test_context_version_and_input_binding(self):
        req = request()
        raw = self.response(req)
        run = {**execution(req), "stdout": canonical_json(raw)}
        self.assertEqual(checked_response(req, run)["status"], "candidate")
        for key in ("input_sha256", "context_sha256", "backend", "identity", "kernel_checked"):
            bad = {**raw, key: "mismatch"}
            with self.subTest(key=key), self.assertRaises(ProtocolError):
                checked_response(req, {**run, "stdout": canonical_json(bad)})

    def test_apparent_success_after_resource_or_transport_failure_is_rejected(self):
        req = request()
        raw = canonical_json(self.response(req))
        for status in ("timeout", "cancelled", "failed", "output_limit", "resource_limit", "unavailable"):
            with self.subTest(status=status), self.assertRaises(ProtocolError):
                checked_response(req, {**execution(req, status=status), "stdout": raw})
        with self.assertRaises(ProtocolError):
            checked_response(req, {**execution(req), "quiescent": False, "stdout": raw})


if __name__ == "__main__":
    unittest.main()
