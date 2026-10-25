"""Constructed metadata fixtures only; no weights, native engine or framework."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORBIDDEN = {"torch", "transformers", "peft", "mlx", "peano_lab", "safetensors", "tokenizers"}


def guard(event, args):
    if event == "import" and args[0].split(".", 1)[0] in FORBIDDEN:
        raise AssertionError("A pure fixture attempted a framework/native import.")
    if event.startswith("socket.") or event in {"subprocess.Popen", "os.system", "os.exec", "os.posix_spawn"}:
        raise AssertionError("A pure fixture attempted process or network execution.")


sys.addaudithook(guard)
loader = importlib.util.spec_from_file_location("hydra_offline_base_fixture", HERE / "experimental_model.py")
subject = importlib.util.module_from_spec(loader)
sys.modules[loader.name] = subject
loader.loader.exec_module(subject)
REGISTRY = ROOT / "output/hydra-implementation-2026-09-04/p6-source-bundle-06/source/hydra-playground/experimental-models/qwen3-base-v1.json"
registry_raw = REGISTRY.read_bytes()
assert sha256(registry_raw).hexdigest() == subject.REGISTRY_SHA256
SPECS = json.loads(registry_raw)["models"]


def config_for(spec):
    # Public, constructed PEFT settings; not a downloaded real adapter config.
    return {"alpha_pattern": {}, "auto_mapping": None, "base_model_name_or_path": spec["model_id"],
        "bias": "none", "corda_config": None, "eva_config": None, "exclude_modules": None,
        "fan_in_fan_out": False, "inference_mode": True, "init_lora_weights": True,
        "layer_replication": None, "layers_pattern": None, "layers_to_transform": None,
        "loftq_config": {}, "lora_alpha": 32, "lora_bias": False, "lora_dropout": 0.05,
        "megatron_config": None, "megatron_core": "megatron.core", "modules_to_save": None,
        "peft_type": "LORA", "qalora_group_size": 16, "r": 16, "rank_pattern": {},
        "revision": None, "target_modules": list(subject.MODULES), "task_type": "CAUSAL_LM",
        "trainable_token_indices": None, "use_dora": False, "use_qalora": False, "use_rslora": False}


def context_for(key):
    spec = SPECS[key]
    # A fixture identity, not a claim that actual Base files were read here.
    return subject._authenticated_base_record(key, spec,
        {**spec["metadata_files"], **spec["weight_files"]})


class OfflineBaseIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="hydra-base-identity-pure-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name).resolve()
        self.key = "qwen3-1.7b-base"
        self.spec = SPECS[self.key]
        self.base = context_for(self.key)
        self.artifact = {"model": {"model_id": self.spec["model_id"], "revision": self.spec["revision"]},
                         "base": deepcopy(self.base), "token_preflight": {"base": deepcopy(self.base)}}
        self.config = config_for(self.spec)
        self.config["base_model_name_or_path"] = str(self.directory)

    def validate(self, config=None, **changes):
        kwargs = {"adapter_kind": "fresh_decision_pilot", "artifact": self.artifact,
                  "authenticated_base": self.base, "authenticated_base_directory": self.directory}
        kwargs.update(changes)
        return subject.validate_adapter_config_with_base_identity(
            self.config if config is None else config, self.spec, **kwargs)

    def test_matching_complete_identity_accepts_only_in_memory_name_change(self):
        before = subject._canonical({"config": self.config, "base": self.base, "artifact": self.artifact})
        result = self.validate()
        self.assertTrue(result["local_base_name_used"])
        self.assertEqual(result["normalization_fields"], ["base_model_name_or_path"])
        self.assertFalse(result["saved_config_modified"])
        self.assertFalse(result["base_selected_from_adapter_metadata"])
        self.assertNotIn("observed_base_name", result)
        self.assertNotIn("authenticated_base_directory", result)
        self.assertTrue(result["recorded_name_matches_authenticated_directory"])
        self.assertEqual(result["authenticated_base_directory_sha256"],
                         sha256(str(self.directory).encode("utf-8")).hexdigest())
        self.assertNotIn(str(self.directory), json.dumps(result))
        self.assertEqual(result["authenticated_base_identity_sha256"], self.base["base_identity_sha256"])
        self.assertEqual(result["validated_config_canonical_sha256"],
                         sha256(subject._canonical(config_for(self.spec))).hexdigest())
        self.assertEqual(before, subject._canonical({"config": self.config, "base": self.base, "artifact": self.artifact}))

    def test_original_strict_validator_does_not_accept_a_path(self):
        with self.assertRaises(subject.ModelAdmissionError):
            subject.validate_adapter_config(self.config, self.spec)
        with self.assertRaises(subject.ModelAdmissionError):
            self.validate(authenticated_base=None, authenticated_base_directory=None)

    def test_both_context_and_path_are_required(self):
        for changes in ({"authenticated_base": None}, {"authenticated_base_directory": None}):
            with self.subTest(changes=tuple(changes)), self.assertRaises(subject.ModelAdmissionError):
                self.validate(**changes)

    def test_canonical_name_and_historical_defaults_remain_strict(self):
        config = config_for(self.spec)
        for kind in ("fresh_decision_pilot", "historical_retention"):
            result = self.validate(config, adapter_kind=kind,
                                   authenticated_base=None, authenticated_base_directory=None)
            self.assertFalse(result["local_base_name_used"])
            self.assertEqual(result["normalization_fields"], [])
        self.assertFalse(self.validate(config)["local_base_name_used"])

    def test_historical_path_never_uses_the_fresh_identity_exception(self):
        for context in ({}, {"authenticated_base": None, "authenticated_base_directory": None}):
            with self.subTest(context=tuple(context)), self.assertRaises(subject.ModelAdmissionError):
                self.validate(adapter_kind="historical_retention", **context)

    def test_wrong_or_incomplete_actual_base_context_is_rejected(self):
        cases = [context_for("qwen3-4b-base")]
        for field, value in (("revision", "0" * 40), ("base_identity_sha256", "0" * 64),
                             ("model_key", "qwen3-4b-base"), ("model_loaded", 0), ("files", {})):
            changed = deepcopy(self.base)
            changed[field] = value
            cases.append(changed)
        for changed in cases:
            with self.subTest(keys=tuple(changed)), self.assertRaises(subject.ModelAdmissionError):
                self.validate(authenticated_base=changed)

    def test_training_and_token_base_must_both_equal_actual_context(self):
        for which in ("training", "token"):
            changed = deepcopy(self.artifact)
            if which == "training":
                changed["base"] = context_for("qwen3-4b-base")
            else:
                changed["token_preflight"]["base"] = context_for("qwen3-4b-base")
            with self.subTest(which=which), self.assertRaises(subject.ModelAdmissionError):
                self.validate(artifact=changed)
        changed = deepcopy(self.artifact)
        changed["model"]["revision"] = "0" * 40
        with self.assertRaises(subject.ModelAdmissionError):
            self.validate(artifact=changed)

    def test_wrong_path_and_equivalent_spelling_are_not_aliases(self):
        sibling = self.directory / "sibling"
        sibling.mkdir()
        for name in (str(sibling), "relative-base", str(self.directory) + "/.",
                     str(self.directory) + "/", "Qwen/Qwen3-4B-Base"):
            changed = deepcopy(self.config)
            changed["base_model_name_or_path"] = name
            with self.subTest(name=name), self.assertRaises(subject.ModelAdmissionError):
                self.validate(changed)

    def test_supplied_base_directory_cannot_be_a_symlink(self):
        target = self.directory / "real"
        target.mkdir()
        link = self.directory / "linked"
        link.symlink_to(target, target_is_directory=True)
        changed = deepcopy(self.config)
        changed["base_model_name_or_path"] = str(link)
        with self.assertRaises(subject.ModelAdmissionError):
            self.validate(changed, authenticated_base_directory=link)

    def test_path_exception_cannot_hide_any_other_peft_change(self):
        for name, value in (("lora_alpha", 16), ("r", 8), ("lora_dropout", 0.1),
                            ("target_modules", ["q_proj"]), ("modules_to_save", ["lm_head"]),
                            ("use_dora", True), ("revision", "main"), ("new_loader_hook", True)):
            changed = deepcopy(self.config)
            changed[name] = value
            with self.subTest(field=name), self.assertRaises(subject.ModelAdmissionError):
                self.validate(changed)

    def test_explicit_registry_sizes_have_distinct_complete_base_identities(self):
        identities = set()
        for key, spec in SPECS.items():
            base = context_for(key)
            artifact = {"model": {"model_id": spec["model_id"], "revision": spec["revision"]},
                        "base": base, "token_preflight": {"base": base}}
            config = config_for(spec)
            config["base_model_name_or_path"] = str(self.directory)
            result = subject.validate_adapter_config_with_base_identity(config, spec,
                adapter_kind="fresh_decision_pilot", artifact=artifact,
                authenticated_base=base, authenticated_base_directory=self.directory)
            identities.add(result["authenticated_base_identity_sha256"])
        self.assertEqual(len(identities), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
