"""Lazy host/custody tests using explicit fake policies; no model imports."""
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cached_policy_runtime as host


class Tokenizer:
    eos_token_id = pad_token_id = 2
    bos_token_id = None
    all_special_ids = [2]
    special_tokens_map = {"eos_token": "eos"}

    def __init__(self):
        self.size = 3
        self.backend_tokenizer = SimpleNamespace(to_str=lambda: json.dumps({"size": self.size}))

    def __len__(self):
        return self.size

    def get_added_vocab(self):
        return {"eos": 2}

    def encode(self, text, **_):
        return [0, 1]


class FakePolicy:
    selection_id = "fixture-model"

    def __init__(self):
        self.policy = None
        self.identity = {"selection_id": self.selection_id}
        self.evaluation_identity = {"use_cache": False}
        self.prepares = 0
        self.finalizations = 0

    def prepare(self):
        if self.policy is None:
            self.prepares += 1
            self.policy = SimpleNamespace(tokenizer=Tokenizer(), backend=object())
        return copy.deepcopy(self.identity)

    def prompt_renderer(self, goals):
        if not hasattr(self.policy.tokenizer, "verify_unchanged"):
            raise AssertionError("Tokenizer was not wrapped before rendering")
        return "literal " + str(goals)

    def provider_factory(self, **limits):
        if not hasattr(self.policy.tokenizer, "verify_unchanged"):
            raise AssertionError("Tokenizer was not wrapped before provider creation")
        return {"limits": limits, "backend": self.policy.backend}

    def new_case(self, **_):
        case = FakePolicy()
        case.policy = self.policy
        return case

    def report(self):
        return {"identity": dict(self.identity), "actual_model_calls": 0, "attempts": []}

    def finalize(self):
        self.finalizations += 1
        return {**self.report(), "original_finalize_called": True}


class HostTests(unittest.TestCase):
    def test_lazy_renderer_and_factory_prepare_once(self):
        original = FakePolicy()
        wrapped = host.wrap_policy(original)
        self.assertEqual(original.prepares, 0)
        self.assertIsNone(wrapped.policy)
        self.assertFalse(wrapped.identity["use_cache"])
        self.assertEqual(wrapped.prompt_renderer(("goal",)), "literal ('goal',)")
        backend = original.policy.backend
        tokenizer = original.policy.tokenizer
        for _ in range(2):
            self.assertIs(wrapped.provider_factory(deadline=123)["backend"], backend)
            self.assertIs(wrapped.policy.tokenizer, tokenizer)
        self.assertEqual(original.prepares, 1)
        self.assertEqual(wrapped.selection_id, "fixture-model")
        self.assertEqual(wrapped.report()["tokenizer_runtime"]["last_verified_custody"]["custody_status"], "verified")

    def test_factory_first_is_also_lazy_and_safe(self):
        wrapped = host.create_policy(FakePolicy)
        self.assertIsNone(wrapped.policy)
        wrapped.provider_factory(deadline=123)
        self.assertEqual(wrapped._original.prepares, 1)

    def test_new_cases_share_only_original_model_and_one_wrapper(self):
        shared = host.wrap_policy(FakePolicy())
        shared.prepare()
        for _ in range(2):
            case = shared.new_case(deadline_monotonic=123)
            self.assertIs(case.policy, shared.policy)
            self.assertIs(case.policy.backend, shared.policy.backend)
            self.assertIs(case.policy.tokenizer, shared.policy.tokenizer)
            result = case.finalize()
            self.assertTrue(result["original_finalize_called"])
            self.assertFalse(result["tokenizer_runtime"]["use_cache"])
            self.assertFalse(result["tokenizer_runtime"]["backend_replaced"])
        self.assertEqual(shared._original.prepares, 1)

    def test_replaced_backend_or_tokenizer_invalidates_finalization(self):
        for field in ("backend", "tokenizer"):
            wrapped = host.wrap_policy(FakePolicy())
            wrapped.prepare()
            setattr(wrapped.policy, field, object())
            with self.assertRaisesRegex(ValueError, "replaced"):
                wrapped.finalize()

    def test_external_tokenizer_change_is_caught_after_original_finalize(self):
        original = FakePolicy()
        original.prepare()
        tokenizer = original.policy.tokenizer
        wrapped = host.wrap_policy(original)
        wrapped.prepare()
        original_finalize = original.finalize
        def mutate_during_finalize():
            tokenizer.size += 1
            return original_finalize()
        original.finalize = mutate_during_finalize
        with self.assertRaisesRegex(ValueError, "changed after"):
            wrapped.finalize()

    def test_source_binding_change_fails_closed(self):
        wrapped = host.wrap_policy(FakePolicy())
        wrapped.prepare()
        different = copy.deepcopy(wrapped._pins)
        different["cached_policy_runtime.py"]["sha256"] = "0" * 64
        with patch.object(host, "_bindings", return_value=different):
            with self.assertRaisesRegex(ValueError, "source changed"):
                wrapped.finalize()

    def test_finalize_without_loading_does_not_load(self):
        original = FakePolicy()
        wrapped = host.wrap_policy(original)
        self.assertTrue(wrapped.finalize()["original_finalize_called"])
        self.assertEqual(original.prepares, 0)
        self.assertIsNone(wrapped.policy)


if __name__ == "__main__":
    unittest.main()
