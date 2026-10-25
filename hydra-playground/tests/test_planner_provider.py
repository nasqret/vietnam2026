"""Strict provider contract tests; callbacks are explicitly NOT model inference."""
from dataclasses import replace
import json
from pathlib import Path
import sys
import unittest

APP = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(APP), str(APP / "native-v7")]

from planner_provider import (
    PlannerBackendError, PlannerBackendIdentity, PlannerProvider,
    render_planner_prompt,
)
from proof_planner import CapabilitySnapshot, PlannerCancelled, PlannerContext
from peano_lab.engine.state import Goal
from peano_lab.kernel.formulas import parse_formula


VALID = '{"v":1,"plans":[{"reason":"Try a primitive closure.","actions":[{"kind":"step","tactic":"refl"}]}]}'


def context():
    target = parse_formula("0=0")
    sibling = Goal((("Hsibling", parse_formula("1=1")),), parse_formula("1=1"))
    return PlannerContext(target, (), (Goal((), target), sibling),
        CapabilitySnapshot("planner-provider-fixture", ("refl",)), "1" * 64,
        failures=("previous tactic failed",),
        remaining={"depth": 32, "tactic_attempts": 64, "model_calls": 4},
        certificate_cost={"distinct_objects": 23, "structural_occurrences": 31})


class ExplicitTestBackend:
    """Exercises callback/counter plumbing only; contains no model or inference."""
    def __init__(self, document=VALID, *, input_tokens=64, output_tokens=24):
        self.identity = PlannerBackendIdentity("pure-contract-fixture", "test-only-no-model",
            "2" * 64, "3" * 64, "unit-fixture", kind="test_double")
        self.calls = self.generated_tokens = 0
        self.encode_calls = self.decode_calls = 0
        self.input_tokens, self.output_tokens, self.document = input_tokens, output_tokens, document
        self.last_prompt = self.last_ids = None
        self.requested_output_cap = None

    def encode_prompt(self, prompt):
        self.encode_calls += 1
        self.last_prompt = prompt
        return tuple(range(self.input_tokens))

    def generate(self, input_ids, *, max_new_tokens, should_stop=None):
        self.calls += 1
        self.last_ids, self.requested_output_cap = input_ids, max_new_tokens
        self.generated_tokens += self.output_tokens
        return tuple(range(self.output_tokens))

    def decode_output(self, output_ids):
        self.decode_calls += 1
        return self.document


def request(provider, ctx=None, **kwargs):
    return provider.propose(ctx or context(), model_calls_remaining=kwargs.pop("model_calls_remaining", 4),
        generated_tokens_remaining=kwargs.pop("generated_tokens_remaining", 2048), **kwargs)


class PlannerProviderTests(unittest.TestCase):
    def test_unconfigured_provider_and_test_double_are_not_model_inference(self):
        unavailable = request(PlannerProvider())
        self.assertEqual(unavailable.status, "unavailable")
        self.assertEqual(unavailable.actual_model_calls, 0)
        self.assertEqual(unavailable.plans, ())
        backend = ExplicitTestBackend()
        with self.assertRaises(PlannerBackendError):
            PlannerProvider(backend)
        provider = PlannerProvider(backend, allow_test_backend=True)
        result = request(provider)
        self.assertEqual(result.status, "proposals")
        self.assertEqual((backend.calls, backend.generated_tokens), (1, 24))
        self.assertEqual((result.backend_calls, result.generated_tokens), (1, 24))
        self.assertEqual((provider.calls, result.actual_model_calls), (0, 0))
        self.assertFalse(result.model_inference)
        self.assertFalse(result.kernel_checked)
        self.assertEqual(result.plans[0].source, "test_backend")
        self.assertEqual(result.plans[0].commands, ("refl",))
        self.assertTrue(provider.report()["test_backend"])

    def test_prompt_contains_full_obligations_and_all_required_metadata(self):
        backend = ExplicitTestBackend()
        ctx = context()
        prompt = render_planner_prompt(ctx, backend.identity)
        self.assertIn("Hsibling", prompt)
        self.assertIn("previous tactic failed", prompt)
        self.assertIn('"structural_occurrences":31', prompt)
        self.assertIn('"model_calls":4', prompt)
        self.assertIn('"provider":', prompt)
        self.assertIn(backend.identity.tokenizer_sha256, prompt)
        self.assertIn('"library_identity":"none"', prompt)
        provider = PlannerProvider(backend, allow_test_backend=True)
        result = request(provider, ctx)
        self.assertEqual(backend.last_prompt, prompt)
        self.assertEqual(backend.last_ids, tuple(range(64)))
        self.assertEqual(result.input_tokens, 64)

    def test_oversize_full_input_is_rejected_without_truncation_or_generation(self):
        backend = ExplicitTestBackend(input_tokens=4097)
        provider = PlannerProvider(backend, allow_test_backend=True)
        result = request(provider)
        self.assertEqual(result.status, "input_rejected")
        self.assertIn("not truncated", result.detail)
        self.assertEqual((backend.calls, backend.encode_calls, backend.decode_calls), (0, 1, 0))
        self.assertEqual(provider.requests, 0)
        self.assertEqual(provider.generated_tokens, 0)
        self.assertIn("Hsibling", backend.last_prompt)

    def test_strict_decoder_rejects_duplicate_keys_malformed_actions_and_trailing_text(self):
        documents = (
            '{"v":1,"v":1,"plans":[]}',
            '{"v":1,"plans":[{"reason":"x","actions":[{"kind":"step","tactic":[]}]}]}',
            '{"v":1,"plans":[{"reason":"x","actions":[{"kind":"invent-rule"}]}]}',
            '{"v":1,"plans":[{"reason":"x","actions":[{"kind":"route","goal":1,"actions":[{"kind":"step","tactic":"refl"}]}]}]}',
            '{"v":1,"plans":[{"reason":"x","actions":[{"kind":"step","tactic":"qed"}]}]}',
            '{"v":NaN,"plans":[]}', VALID + " trailing text", "```json\n" + VALID + "\n```",
            VALID[:-1],
        )
        for document in documents:
            with self.subTest(document=document):
                backend = ExplicitTestBackend(document)
                provider = PlannerProvider(backend, allow_test_backend=True)
                result = request(provider)
                self.assertEqual(result.status, "output_rejected")
                self.assertEqual(result.plans, ())
                self.assertEqual((provider.requests, provider.backend_calls, provider.generated_tokens), (1, 1, 24))
                self.assertEqual(provider.calls, 0)

    def test_two_proposals_are_bounded_and_exact_duplicates_are_not_repeated(self):
        plan = json.loads(VALID)["plans"][0]
        document = json.dumps({"v": 1, "plans": [plan, plan]})
        backend = ExplicitTestBackend(document)
        provider = PlannerProvider(backend, allow_test_backend=True)
        result = request(provider)
        self.assertEqual(result.status, "proposals")
        self.assertEqual(len(result.plans), 1)
        too_many = ExplicitTestBackend(json.dumps({"v": 1, "plans": [plan, plan, plan]}))
        self.assertEqual(request(PlannerProvider(too_many, allow_test_backend=True)).status, "output_rejected")
        one_only = ExplicitTestBackend(document)
        self.assertEqual(request(PlannerProvider(one_only, allow_test_backend=True), max_proposals=1).status,
                         "output_rejected")

    def test_shared_model_and_total_token_budgets_stop_actual_callbacks(self):
        backend = ExplicitTestBackend(output_tokens=512)
        provider = PlannerProvider(backend, allow_test_backend=True)
        self.assertEqual(request(provider, model_calls_remaining=0).status, "limit")
        self.assertEqual(request(provider, generated_tokens_remaining=0).status, "limit")
        self.assertEqual(backend.calls, 0)
        for _ in range(4):
            self.assertEqual(request(provider).status, "proposals")
        self.assertEqual((provider.requests, provider.backend_calls, provider.generated_tokens), (4, 4, 2048))
        self.assertEqual(request(provider).status, "limit")
        self.assertEqual(backend.calls, 4)
        reduced = ExplicitTestBackend(output_tokens=17)
        limited = PlannerProvider(reduced, allow_test_backend=True, max_total_generated_tokens=17)
        self.assertEqual(request(limited, generated_tokens_remaining=20).status, "proposals")
        self.assertEqual(reduced.requested_output_cap, 17)
        self.assertEqual(request(limited).status, "limit")

    def test_unbacked_output_and_counter_violations_cannot_claim_a_proposal(self):
        class NoDecode(ExplicitTestBackend):
            def generate(self, input_ids, **kwargs):
                return (1, 2, 3)
        provider = PlannerProvider(NoDecode(), allow_test_backend=True)
        self.assertEqual(request(provider).status, "output_rejected")
        self.assertEqual(provider.backend_calls, 0)
        for calls, tokens, returned in ((2, 3, 3), (1, 513, 513), (1, 4, 3), (0, 3, 3)):
            class BadCounters(ExplicitTestBackend):
                def generate(self, input_ids, **kwargs):
                    self.calls += calls
                    self.generated_tokens += tokens
                    return tuple(range(returned))
            provider = PlannerProvider(BadCounters(), allow_test_backend=True)
            with self.subTest(calls=calls, tokens=tokens), self.assertRaises(PlannerBackendError):
                request(provider)
            self.assertEqual(provider.backend_calls, calls)
            self.assertEqual(provider.generated_tokens, tokens)

    def test_resource_errors_and_cancellation_preserve_observed_work(self):
        for error_type in (MemoryError, TimeoutError):
            class Failure(ExplicitTestBackend):
                def generate(self, input_ids, **kwargs):
                    self.calls += 1
                    self.generated_tokens += 7
                    raise error_type("intentional contract fixture")
            provider = PlannerProvider(Failure(), allow_test_backend=True)
            with self.subTest(error=error_type), self.assertRaises(error_type):
                request(provider)
            self.assertEqual((provider.backend_calls, provider.generated_tokens), (1, 7))
        backend = ExplicitTestBackend()
        provider = PlannerProvider(backend, allow_test_backend=True)
        with self.assertRaises(PlannerCancelled):
            request(provider, should_stop=lambda: True)
        self.assertEqual(backend.calls, 0)
        stopped = [False]
        class CancelAfterDecode(ExplicitTestBackend):
            def generate(self, input_ids, **kwargs):
                result = super().generate(input_ids, **kwargs)
                stopped[0] = True
                return result
        provider = PlannerProvider(CancelAfterDecode(), allow_test_backend=True)
        with self.assertRaises(PlannerCancelled):
            request(provider, should_stop=lambda: stopped[0])
        self.assertEqual((provider.backend_calls, provider.generated_tokens), (1, 24))

    def test_identity_and_read_only_tokenizer_contract_are_enforced(self):
        backend = ExplicitTestBackend()
        provider = PlannerProvider(backend, allow_test_backend=True)
        backend.identity = replace(backend.identity, runtime_identity="changed")
        with self.assertRaises(PlannerBackendError):
            request(provider)
        class HiddenDecode(ExplicitTestBackend):
            def encode_prompt(self, prompt):
                self.calls += 1
                return super().encode_prompt(prompt)
        provider = PlannerProvider(HiddenDecode(), allow_test_backend=True)
        with self.assertRaises(PlannerBackendError):
            request(provider)
        self.assertEqual(provider.backend_calls, 1)
        self.assertEqual(provider.calls, 0)

    def test_cache_namespace_binds_actual_prompt_provider_and_search_context(self):
        ctx = context()
        provider = PlannerProvider(ExplicitTestBackend(), allow_test_backend=True)
        first = request(provider, ctx)
        changed_budget = request(provider, replace(ctx, remaining={"depth": 31, "tactic_attempts": 64}))
        changed_error = request(provider, replace(ctx, failures=("different failure",)))
        changed_goal = request(provider, replace(ctx, goals=(ctx.goals[0],)))
        self.assertEqual(len({first.cache_identity, changed_budget.cache_identity,
                              changed_error.cache_identity, changed_goal.cache_identity}), 4)
        other_backend = ExplicitTestBackend()
        other_backend.identity = replace(other_backend.identity, runtime_identity="another-runtime")
        other = request(PlannerProvider(other_backend, allow_test_backend=True), ctx)
        self.assertNotEqual(first.cache_identity, other.cache_identity)


if __name__ == "__main__":
    unittest.main()
