"""Profile admission and component limits must agree across worker and search."""
from pathlib import Path
import sys
import unittest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
from search_settings import native_limits, profile, public_profiles
import worker
worker.load_kernel()
from hybrid_search import HybridLimits
from hybrid_runtime import bounded_records


class ProfileTests(unittest.TestCase):
    def test_every_advertised_combination_fits_the_actual_engine_and_worker(self):
        for name, settings in public_profiles().items():
            for calls in settings["model_calls"]:
                for beam in settings["beams"]:
                    for mode in ("heuristic", "symbolic", "hybrid"):
                        with self.subTest(profile=name, calls=calls, beam=beam, mode=mode):
                            selected = native_limits({"search_mode": mode, "search_profile": name,
                                                      "max_model_calls": calls, "beam_width": beam})
                            HybridLimits(**selected)
                            self.assertEqual(selected["max_model_calls"], calls if mode == "hybrid" else 0)
                            self.assertEqual(selected["max_vampire_calls"] > 0, mode != "heuristic")
                            self.assertLess(selected["wall_seconds"] + settings["vampire"]["wall_seconds"],
                                            settings["worker"]["wall_seconds"])
                            self.assertLessEqual(selected["max_depth"], 160)

    def test_returned_metadata_cannot_mutate_runtime_policy(self):
        selected = profile("research")
        selected["search"]["max_tactic_attempts"] = 10**12
        selected["model_calls"].append(9999)
        self.assertEqual(profile("research")["search"]["max_tactic_attempts"], 40000)
        self.assertNotIn(9999, profile("research")["model_calls"])

    def test_optional_diagnostics_are_truncated_without_rewriting_records(self):
        records = [{"attempt": 1, "text": "é" * 20}, {"attempt": 2, "text": "x" * 300}]
        kept, omitted = bounded_records(records, 100)
        self.assertEqual(kept, records[:1])
        self.assertEqual(omitted, 1)
        self.assertEqual(len(records), 2)


if __name__ == "__main__":
    unittest.main()
