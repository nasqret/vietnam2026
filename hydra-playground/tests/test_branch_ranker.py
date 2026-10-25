"""Pure feature/loader contracts; deliberately never fit a ranker here."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(APP))
import branch_ranker as ranker


class BranchRankerTests(unittest.TestCase):
    def test_every_outstanding_goal_changes_features(self):
        one = ranker.extract_features(["⊢ 0 = 0"])
        two = ranker.extract_features(["⊢ 0 = 0","n : ℕ ⊢ ∃ x. n · n = x + x"])
        self.assertGreater(two["goal_count"],one["goal_count"])
        self.assertGreater(two["existential_count"],one["existential_count"])
        self.assertGreater(two["product_count"],one["product_count"])
        self.assertGreater(two["state_bytes"],one["state_bytes"])

    def test_missing_cost_is_not_zero_measurement(self):
        unknown = ranker.extract_features(["⊢ 0 = 0"])
        cost = {"distinct_objects":0,"structural_occurrences":0,"depth":0,
                "exact":{"distinct_objects":True,"structural_occurrences":True,"depth":True}}
        observed = ranker.extract_features(["⊢ 0 = 0"],proof_cost=cost)
        self.assertEqual(unknown["cost_missing"],1)
        self.assertEqual(observed["cost_missing"],0)
        self.assertEqual(observed["objects"],0)
        with self.assertRaises(ranker.RankerError):
            ranker.extract_features(["⊢ 0 = 0"],proof_cost={"depth":4})

    def test_large_state_is_rejected_without_truncation(self):
        for goals in (["⊢ 0 = 0"]*65,["⊢ "+"x"*65536],["not a native goal"]):
            with self.assertRaises(ranker.RankerError):ranker.extract_features(goals)

    def test_fixed_coefficients_callback_is_finite_and_repeatable(self):
        weights = tuple(1.0 if name == "goal_count" else 0.0 for name in ranker.FEATURES)
        model = ranker.BranchRanker(weights,0.0,"a"*64)
        args = {"all_goals":["⊢ 0 = 0","⊢ 1 = 1"],"depth":2}
        self.assertEqual(model.callback(**args),model.callback(**args))
        self.assertGreater(model.callback(**args),model.callback(all_goals=["⊢ 0 = 0"],depth=2))
        self.assertEqual(model.artifact_sha256,"a"*64)

    def test_resource_censored_and_validation_rows_not_fit_inputs(self):
        row = {"schema":ranker.DISTANCE_SCHEMA,"feature_schema":ranker.FEATURE_SCHEMA,"id":"x","split":"train",
               "censored":False,"verified_continuation":True,"remaining_steps":2,
               "features":ranker.extract_features(["⊢ 0 = 0"])}
        self.assertEqual(len(ranker._training_rows([row])),1)
        for field,value in (("censored",True),("split","val"),("verified_continuation",False)):
            changed = {**row,field:value}
            with self.assertRaises(ranker.RankerError):ranker._training_rows([changed])
        with self.assertRaises(ranker.RankerError):ranker._training_rows([row,row])

    def test_loader_requires_pin_schema_and_finite_coefficients(self):
        # Hand-created loader fixture, explicitly not a measured trained model.
        record = {"schema":ranker.SCHEMA,"feature_schema":ranker.FEATURE_SCHEMA,
            "numeric_encoding":ranker.NUMERIC_ENCODING,
            "features":list(ranker.FEATURES),"weights":[0.0]*len(ranker.FEATURES),
            "intercept":1.0,"trained":True,"target":"log1p_observed_checked_continuation_steps",
            "lower_is_better":True}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/"fixture.json"
            raw = ranker.canonical(record);path.write_bytes(raw)
            self.assertEqual(ranker.load_ranker(path,expected_sha256=hashlib.sha256(raw).hexdigest()).intercept,1.0)
            with self.assertRaises(ranker.RankerError):ranker.load_ranker(path,expected_sha256="0"*64)
            record["trained"] = False
            raw = ranker.canonical(record);path.write_bytes(raw)
            with self.assertRaises(ranker.RankerError):ranker.load_ranker(path,expected_sha256=hashlib.sha256(raw).hexdigest())
        with self.assertRaises(ranker.RankerError):
            ranker.BranchRanker(tuple([float("nan")]*len(ranker.FEATURES)),0.0,"a"*64)


if __name__ == "__main__":unittest.main()
