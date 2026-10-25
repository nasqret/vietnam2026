"""Pure staged portability/admission checks; no fits or native/model imports."""
from decimal import Context, ROUND_DOWN, localcontext
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = next(parent for parent in HERE.parents if (parent/"hydra-playground").is_dir())
APP = HERE/"staged/hydra-playground"


def load(name,path):
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ranker = load("portable_ranker_fixture",APP/"branch_ranker.py")
with mock.patch.dict(sys.modules,{"branch_ranker":ranker}):
    exporter = load("portable_exporter_fixture",APP/"export_decisions.py")
sys.path.insert(0,str(ROOT/"hydra-playground/training-v5"))
data = load("hydra_training_v5.portable_admission_fixture",APP/"training-v5/hydra_training_v5/decision_data.py")
legacy = load("legacy_ranker_fixture",ROOT/"output/hydra-implementation-2026-09-04/p6-source-bundle-02/source/hydra-playground/branch_ranker.py")


class PortableEncodingTests(unittest.TestCase):
    def test_encoding_does_not_consult_libm_or_ambient_decimal_context(self):
        goals = ["n : ℕ, h : n + n = 2 * n ⊢ ∃ q. n * (n + 1) = 2 * q"]
        expected = ranker.canonical(ranker.extract_features(goals,depth=7))
        with mock.patch.object(ranker.math,"log1p",side_effect=AssertionError("libm is forbidden")), \
             localcontext(Context(prec=6,rounding=ROUND_DOWN)):
            self.assertEqual(ranker.canonical(ranker.extract_features(goals,depth=7)),expected)
            self.assertGreater(ranker.portable_log1p(12),0)
        self.assertEqual(ranker.portable_scaled(0,65536),0.0)
        self.assertEqual(ranker.portable_scaled(65536,65536),1.0)
        self.assertEqual(ranker.portable_scaled(65537,65536),1.0)

    def test_legacy_features_and_fitted_artifact_keep_their_original_behavior(self):
        path = ROOT/"output/hydra-implementation-2026-09-04/ranker-v1-02.json"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        old_model = legacy.load_ranker(path,expected_sha256=digest)
        model = ranker.load_ranker(path,expected_sha256=digest)
        self.assertEqual(model.feature_schema,ranker.LEGACY_FEATURE_SCHEMA)
        goals = ("⊢ 0 = 0","n : ℕ ⊢ ∃ q. n * (n + 1) = 2 * q")
        self.assertEqual(ranker.extract_features(goals,depth=9,feature_schema=ranker.LEGACY_FEATURE_SCHEMA),
                         legacy.extract_features(goals,depth=9))
        self.assertEqual(model.callback(all_goals=goals,depth=9),old_model.callback(all_goals=goals,depth=9))

    def test_v1_rows_cannot_be_silently_fitted_as_v2(self):
        row = {"schema":ranker.DISTANCE_SCHEMA,"feature_schema":ranker.FEATURE_SCHEMA,
            "id":"fixture","split":"train","censored":False,"verified_continuation":True,
            "remaining_steps":7,"features":ranker.extract_features(["⊢ 0 = 0"])}
        self.assertEqual(len(ranker._training_rows([row])),1)
        for changed in ({"schema":"hydra-branch-distance-v1"},{"feature_schema":ranker.LEGACY_FEATURE_SCHEMA}):
            with self.assertRaises(ValueError):ranker._training_rows([{**row,**changed}])

    def test_mismatch_preserves_both_complete_manifests_and_remains_rejected(self):
        expected = {"schema":"fixture","files":{"ranker-train.jsonl":{"bytes":5,"sha256":"a"*64,"rows":1}}}
        regenerated = {"schema":"fixture","files":{"ranker-train.jsonl":{"bytes":6,"sha256":"b"*64,"rows":1}}}
        expected_raw = exporter.canonical(expected)+b"\n"
        regenerated_raw = exporter.canonical(regenerated)+b"\n"
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(data,"_exporter",return_value=exporter):
            out = Path(temporary)/"failure"
            data.retain_manifest_mismatch(expected_raw,regenerated_raw,expected,regenerated,failure_output=out)
            self.assertEqual((out/"expected-manifest.json").read_bytes(),expected_raw)
            self.assertEqual((out/"regenerated-manifest.json").read_bytes(),regenerated_raw)
            difference = json.loads((out/"diff.json").read_bytes())
            self.assertFalse(difference["admitted"])
            self.assertEqual(difference["different_top_level_fields"],["files"])
            self.assertEqual(set(difference["file_differences"]),{"ranker-train.jsonl"})
            with self.assertRaises(FileExistsError):
                data.retain_manifest_mismatch(expected_raw,regenerated_raw,expected,regenerated,failure_output=out)


if __name__ == "__main__":unittest.main()
