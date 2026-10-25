"""Pure teacher admission/ledger tests; no framework, model, solver or native run."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import experimental_teacher as teacher


class TeacherContractTests(unittest.TestCase):
    def test_limits_do_not_accept_bool_or_inflated_campaign(self):
        for kwargs in ({"max_calls": True}, {"max_calls": 65}, {"max_generated_tokens": 32769}):
            with self.assertRaises(teacher.TeacherAdmissionError):
                teacher.TeacherLimits(**kwargs)
        self.assertEqual(teacher.TeacherLimits().max_generated_tokens, 32768)

    def test_actual_token_ledger_retains_cancelled_last_token(self):
        counts = []
        stop = [False]
        ledger = teacher.TokenLedger(9, 3, counts.append, lambda: stop[0])
        ledger.observe(1, 10)
        stop[0] = True
        with self.assertRaises(teacher.TeacherCancelled):
            ledger.observe(1, 11)
        self.assertEqual(sum(counts), 2)
        self.assertEqual(ledger.seen, 2)
        with self.assertRaises(teacher.TeacherAdmissionError):
            ledger.observe(1, 10)
        self.assertEqual(sum(counts), 2)

    def test_no_teacher_beam_or_token_overrun_is_hidden(self):
        counts = []
        ledger = teacher.TokenLedger(5, 2, counts.append, None)
        for shape in ((2, 6), (1, 8)):
            with self.assertRaises(teacher.TeacherAdmissionError):
                ledger.observe(*shape)
        self.assertEqual(counts, [])

    def test_only_declared_rope_compatibility_rewrite_is_accepted(self):
        spec = json.loads((HERE / "experimental-models/deepseek-teacher-v1.json").read_bytes())
        config = copy.deepcopy(spec["config"])
        config["rope_scaling"]["rope_type"] = "yarn"
        self.assertTrue(teacher.validate_loaded_config(config, spec))
        for key, value in (("num_hidden_layers", 32), ("num_key_value_heads", 8), ("torch_dtype", "float32")):
            bad = copy.deepcopy(config)
            bad[key] = value
            with self.assertRaises(teacher.TeacherAdmissionError):
                teacher.validate_loaded_config(bad, spec)
        bad = copy.deepcopy(config)
        bad["rope_scaling"]["factor"] = 8
        with self.assertRaises(teacher.TeacherAdmissionError):
            teacher.validate_loaded_config(bad, spec)

    def test_remote_gate_precedes_helper_or_framework_loading(self):
        called = []
        with patch.object(teacher.platform, "system", return_value="Darwin"), \
                patch.object(teacher, "_helpers", side_effect=AssertionError("must not import helper")):
            with self.assertRaises(teacher.TeacherAdmissionError):
                teacher.load_teacher("/does/not/exist", reservation_check=lambda: called.append(True))
        self.assertEqual(called, [])
        with self.assertRaises(teacher.TeacherAdmissionError):
            teacher.TeacherSession(None, None, None, None, {}, None, None, None)

    def test_entire_message_and_template_are_counted_without_truncation(self):
        seen = []
        class Tokenizer:
            def apply_chat_template(self, messages, **kwargs):
                seen.append((messages, kwargs))
                return [100000] + [7] * 4096
        session = object.__new__(teacher.TeacherSession)
        session.tokenizer, session.should_stop = Tokenizer(), None
        text, ids = session.encode_prompt("FULL_CONTEXT_MUST_REMAIN")
        self.assertEqual(len(ids), 4097)
        self.assertIn("FULL_CONTEXT_MUST_REMAIN", text)
        self.assertIn(teacher.PROMPT_VERSION, text)
        self.assertEqual(seen[0][0], [{"role": "user", "content": text}])
        self.assertEqual(seen[0][1], {"tokenize": True, "add_generation_prompt": True})
        # Oversize is left intact for PlannerProvider admission; generation also
        # refuses it before looking for a model/framework/budget object.
        with self.assertRaises(teacher.TeacherAdmissionError):
            session.generate(ids, maximum=1, tracker=SimpleNamespace())

    def test_registry_pin_matches_prepared_primary_metadata(self):
        raw = (HERE / "experimental-models/deepseek-teacher-v1.json").read_bytes()
        self.assertEqual(teacher.sha256(raw).hexdigest(), teacher.REGISTRY_SHA256)
        spec = json.loads(raw)
        self.assertEqual(spec["revision"], teacher.REVISION)
        self.assertEqual(sum(v["bytes"] for v in spec["weight_files"].values()), 13820763130)
        self.assertFalse(spec["teacher_adapters_allowed"])


if __name__ == "__main__":
    unittest.main()
