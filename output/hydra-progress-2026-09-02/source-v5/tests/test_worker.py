"""Small real-kernel regression tests; no model, network or GPU work."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
import worker


def native_request(theorem, tactics):
    request = worker.json_bytes({"theorem": theorem, "tactics": tactics})
    process = subprocess.run([sys.executable, "-I", "-B", str(APP / "worker.py"), "--mode", "replay"],
                             input=request, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             timeout=48, check=False, cwd=str(APP))
    if len(process.stdout) > worker.MAX_RESULT_BYTES or len(process.stderr) > 65536:
        raise AssertionError("Bounded manual worker produced excessive output.")
    events = [json.loads(line) for line in process.stdout.splitlines()]
    return process, events


class RequestTests(unittest.TestCase):
    def test_search_modes_preserve_the_model_default_and_reject_unknown_modes(self):
        request = {"theorem": "0 = 0", "max_model_calls": 8, "beam_width": 1}
        self.assertEqual(worker.validate_request("search", request)["search_mode"], "model")
        for mode in ("model", "heuristic", "symbolic", "hybrid"):
            self.assertEqual(worker.validate_request("search", {**request, "search_mode": mode})["search_mode"], mode)
        for mode in (None, True, "shell", "../worker.py"):
            with self.assertRaises(ValueError):
                worker.validate_request("search", {**request, "search_mode": mode})

    def test_multiline_formula_normalizes_only_whitespace_after_raw_bound(self):
        value = worker.validate_request("replay", {"theorem": "forall n.\r\n\tn = n", "tactics": []})
        self.assertEqual(value["theorem"], "forall n.  n = n")
        for text in ("0 = 0\x00", "0 = 0\u202e", "0 = 0\u2028", "0 = 0\u200b"):
            with self.subTest(text=repr(text)), self.assertRaises(ValueError):
                worker.validate_request("replay", {"theorem": text, "tactics": []})
        with self.assertRaises(ValueError):
            worker.validate_request("replay", {"theorem": "0 = 0" + "\r\n" * 2048, "tactics": []})

    def test_tactics_and_request_fields_are_bounded(self):
        for tactics in (["refl\nrefl"], ["refl\trefl"], ["x" * 513], ["refl"] * 161):
            with self.subTest(tactics=repr(tactics)[:60]), self.assertRaises(ValueError):
                worker.validate_request("replay", {"theorem": "0 = 0", "tactics": tactics})
        with self.assertRaises(ValueError):
            worker.validate_request("replay", {"theorem": "0 = 0", "tactics": [], "source": "/tmp"})
        for calls, beam in ((True, 1), (8, True), (9, 4), (16, 2)):
            with self.subTest(calls=calls, beam=beam), self.assertRaises(ValueError):
                worker.validate_request("search", {"theorem": "0 = 0", "max_model_calls": calls, "beam_width": beam})

    def test_advanced_profiles_are_explicit_and_cannot_change_model_only_search(self):
        request = {"theorem": "0 = 0", "max_model_calls": 32, "beam_width": 8,
                   "search_mode": "hybrid", "search_profile": "deep"}
        normalized = worker.validate_request("search", request)
        self.assertEqual(normalized, request)
        self.assertEqual(worker.resource_limits("search", normalized)["wall_seconds"], 330)
        self.assertEqual(worker.solver_limits(normalized)["solver_seconds"], 5)
        for changes in ({"search_mode": "model"}, {"search_profile": True},
                        {"search_profile": "unbounded"}, {"max_model_calls": 128},
                        {"beam_width": 16}, {"wall_seconds": 10000}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                worker.validate_request("search", {**request, **changes})
        research = worker.validate_request("search", {**request, "search_profile": "research",
                                                       "max_model_calls": 128})
        self.assertEqual(worker.resource_limits("search", research)["wall_seconds"], 660)
        self.assertEqual(worker.solver_limits(research)["wall_seconds"], 18)

    def test_json_rejects_ambiguity_and_excess(self):
        for raw in (b'{"theorem":"0=0","theorem":"0=1"}', b'{"x":NaN}', b'[]', b'"text"',
                    b"{" * 1000, b" " * (worker.MAX_BODY_BYTES + 1)):
            with self.subTest(raw=raw[:60]), self.assertRaises(ValueError):
                worker.decode_json(raw)


class NativeReplayTests(unittest.TestCase):
    def test_heuristic_search_is_real_native_work_without_loading_a_model(self):
        request = worker.json_bytes({"theorem": "forall n m. n = m -> m = n",
                                    "max_model_calls": 8, "beam_width": 1, "search_mode": "heuristic"})
        process = subprocess.run([sys.executable, "-I", "-B", str(APP / "worker.py"), "--mode", "search"],
            input=request, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, cwd=str(APP))
        events = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(process.returncode, 0, (events, process.stderr.decode()))
        result = events[-1]["result"]
        self.assertEqual(result["kind"], "heuristic")
        self.assertTrue(result["kernel_checked"])
        self.assertEqual(result["search"]["model_calls"], 0)
        self.assertFalse(result["search"]["model_loaded"])
        self.assertEqual(result["search"]["vampire_calls"], 0)
        self.assertEqual(result["proof_sources"], {"heuristic": len(result["commands"])})

    def test_all_supplied_examples_use_the_real_preserved_kernel(self):
        examples = json.loads((APP / "examples.json").read_bytes())["examples"]
        self.assertEqual(len(examples), 5)
        for example in examples:
            with self.subTest(example=example["id"]):
                process, events = native_request(example["theorem"], example["tactics"])
                self.assertEqual(process.returncode, 0, (events, process.stderr.decode("utf-8", "replace")))
                self.assertEqual(len(events), 1)
                result = events[0]["result"]
                self.assertEqual(result["kind"], "manual")
                self.assertFalse(result["model_used"])
                self.assertEqual(result["commands"], example["tactics"])
                transitions = [row for row in result["trace"] if "tactic" in row]
                self.assertEqual(len(transitions), len(example["tactics"]))
                for left, right in zip(transitions, transitions[1:]):
                    self.assertEqual(left["goals_after"], right["goals_before"])
                if example["provenance"] == "negative":
                    self.assertEqual(result["status"], "open")
                    self.assertFalse(result["kernel_checked"])
                    self.assertTrue(result["goals"])
                    self.assertEqual(result["trace"], [])
                    self.assertEqual(result["mode"], "initial-state")
                else:
                    self.assertEqual(result["status"], "proved")
                    self.assertTrue(result["kernel_checked"])
                    self.assertGreater(result["proof_nodes"], 0)
                    self.assertEqual(result["goals"], [])
                    self.assertTrue(result["trace"][-1]["qed"])
                    self.assertEqual(transitions[-1]["goals_after"], [])

    def test_prefix_is_open_and_failed_tactic_does_not_change_the_goal(self):
        process, events = native_request("forall n m. n = m -> m = n", ["intro n", "intro m", "intro h"])
        self.assertEqual(process.returncode, 0, events)
        result = events[0]["result"]
        self.assertEqual(result["status"], "open")
        self.assertFalse(result["kernel_checked"])
        self.assertEqual(result["trace"][-2]["goals_after"], result["goals"])
        process, events = native_request("0 = 1", ["refl"])
        self.assertEqual(process.returncode, 0, events)
        result = events[0]["result"]
        self.assertFalse(result["kernel_checked"])
        self.assertEqual(result["status"], "tactic_error")
        self.assertEqual(result["trace"][0]["goals_before"], result["trace"][0]["goals_after"])
        self.assertTrue(result["trace"][0]["error"])

    def test_unbounded_automation_is_not_a_manual_capability(self):
        process, events = native_request("0 = 0", ["auto"])
        self.assertEqual(process.returncode, 0, events)
        result = events[0]["result"]
        self.assertFalse(result["kernel_checked"])
        self.assertEqual(result["status"], "tactic_error")
        self.assertIn("not available", result["error"])

    def test_protocol_rejects_large_numerals_before_proof_work(self):
        process, events = native_request("65 = 65", [])
        self.assertEqual(process.returncode, 2)
        self.assertEqual(events[0]["type"], "error")
        self.assertIn("numeral", events[0]["error"]["message"].lower())


if __name__ == "__main__":
    unittest.main()
