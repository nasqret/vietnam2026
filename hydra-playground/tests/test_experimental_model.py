"""Pure metadata/shape/boundary tests; no model, tensor allocation, or native proof."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
import experimental_model as subject


def header_for(spec):
    result = {"__metadata__": {"format": "pt"}}
    offset = 0
    for name, shape in subject.expected_lora_shapes(spec).items():
        size = shape[0] * shape[1] * 4
        result[name] = {"dtype": "F32", "shape": list(shape), "data_offsets": [offset, offset + size]}
        offset += size
    return result, offset


def adapter_config(spec):
    return {"alpha_pattern": {}, "auto_mapping": None, "base_model_name_or_path": spec["model_id"],
        "bias": "none", "corda_config": None, "eva_config": None, "exclude_modules": None,
        "fan_in_fan_out": False, "inference_mode": True, "init_lora_weights": True,
        "layer_replication": None, "layers_pattern": None, "layers_to_transform": None,
        "loftq_config": {}, "lora_alpha": 32, "lora_bias": False, "lora_dropout": 0.05,
        "megatron_config": None, "megatron_core": "megatron.core", "modules_to_save": None,
        "peft_type": "LORA", "qalora_group_size": 16, "r": 16, "rank_pattern": {},
        "revision": None, "target_modules": list(subject.MODULES), "task_type": "CAUSAL_LM",
        "trainable_token_indices": None, "use_dora": False, "use_qalora": False, "use_rslora": False}


class ExperimentalModelTests(unittest.TestCase):
    def test_exact_registry_pins_three_architectures_without_frameworks(self):
        before = {name for name in sys.modules if name.split(".")[0] in {"torch", "transformers", "peft", "mlx"}}
        status = subject.metadata_status()
        self.assertEqual(len(status["models"]), 3)
        self.assertFalse(status["available"])
        self.assertFalse(status["model_loaded"])
        self.assertFalse(status["local_mlx_supported"])
        self.assertEqual(subject.model_spec("qwen3-8b-base")["revision"], "49e3418fbbbca6ecbdf9608b4d22e5a407081db4")
        after = {name for name in sys.modules if name.split(".")[0] in {"torch", "transformers", "peft", "mlx"}}
        self.assertEqual(before, after)
        for invalid in ("4B", "qwen3-4b-instruct", "../../model", None):
            with self.assertRaises(subject.ModelAdmissionError):
                subject.model_spec(invalid)

    def test_registry_cannot_be_swapped_by_model_size_string(self):
        original = subject.REGISTRY_PATH.read_bytes()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "registry.json"
            path.write_bytes(original.replace(b'"hidden_size": 2560', b'"hidden_size": 2048'))
            with patch.object(subject, "REGISTRY_PATH", path):
                with self.assertRaisesRegex(subject.ModelAdmissionError, "registry bytes"):
                    subject.registry()

    def test_qwen4b_query_and_output_dimensions_are_not_hidden_square(self):
        shapes = subject.expected_lora_shapes(subject.model_spec("qwen3-4b-base"))
        root = "base_model.model.model.layers.0.self_attn."
        self.assertEqual(shapes[root + "q_proj.lora_A.weight"], (16, 2560))
        self.assertEqual(shapes[root + "q_proj.lora_B.weight"], (4096, 16))
        self.assertEqual(shapes[root + "o_proj.lora_A.weight"], (16, 4096))
        self.assertEqual(shapes[root + "o_proj.lora_B.weight"], (2560, 16))
        self.assertEqual(shapes[root + "k_proj.lora_B.weight"], (1024, 16))
        self.assertEqual(len(shapes), 36 * 14)

    def test_all_three_complete_tensor_populations_and_runtime_names(self):
        for key in ("qwen3-1.7b-base", "qwen3-4b-base", "qwen3-8b-base"):
            with self.subTest(key=key):
                spec = subject.model_spec(key)
                header, payload = header_for(spec)
                report = subject.validate_adapter_header(header, payload, spec)
                self.assertEqual(report["tensors"], spec["config"]["num_hidden_layers"] * 14)
                self.assertLess(payload, subject.MAX_ADAPTER_BYTES)
                self.assertTrue(all(".default.weight" in name for name in subject.expected_lora_shapes(spec, saved=False)))

    def test_cross_size_wrong_shape_dtype_extra_or_missing_matrix_rejected(self):
        spec = subject.model_spec("qwen3-4b-base")
        header, payload = header_for(spec)
        first = next(name for name in header if name != "__metadata__")
        mutations = []
        changed = deepcopy(header); changed[first]["shape"][1] -= 1; mutations.append(changed)
        changed = deepcopy(header); changed[first]["dtype"] = "BF16"; mutations.append(changed)
        changed = deepcopy(header); changed.pop(first); mutations.append(changed)
        changed = deepcopy(header); changed["lm_head.weight"] = changed[first]; mutations.append(changed)
        changed = deepcopy(header); changed[first]["data_offsets"][1] -= 4; mutations.append(changed)
        for altered in mutations:
            with self.assertRaises(subject.ModelAdmissionError):
                subject.validate_adapter_header(altered, payload, spec)
        with self.assertRaises(subject.ModelAdmissionError):
            subject.validate_adapter_header(header, payload, subject.model_spec("qwen3-8b-base"))

    def test_overlapping_payload_not_just_shape_matching_is_rejected(self):
        spec = subject.model_spec("qwen3-1.7b-base")
        header, payload = header_for(spec)
        names = [name for name in header if name != "__metadata__"]
        # Same shape and byte count, but an A matrix aliases a previous A matrix.
        first = names[0]
        other = next(name for name in names[1:] if header[name]["shape"] == header[first]["shape"])
        header[other]["data_offsets"] = header[first]["data_offsets"][:]
        with self.assertRaisesRegex(subject.ModelAdmissionError, "overlapping"):
            subject.validate_adapter_header(header, payload, spec)

    def test_peft_settings_base_path_and_extra_authority_are_explicit(self):
        spec = subject.model_spec("qwen3-4b-base")
        config = adapter_config(spec)
        self.assertTrue(subject.validate_adapter_config(config, spec))
        for key, value in (("r", 8), ("base_model_name_or_path", "Qwen/Qwen3-8B-Base"),
                           ("target_modules", ["q_proj"]), ("use_dora", True), ("modules_to_save", ["lm_head"]),
                           ("revision", "main"), ("auto_mapping", {"library": "arbitrary"})):
            changed = deepcopy(config); changed[key] = value
            with self.assertRaises(subject.ModelAdmissionError):
                subject.validate_adapter_config(changed, spec)
        changed = deepcopy(config); changed["new_loader_hook"] = True
        with self.assertRaises(subject.ModelAdmissionError):
            subject.validate_adapter_config(changed, spec)

    def test_small_header_reader_rejects_truncation_overflow_duplicate_keys(self):
        spec = subject.model_spec("qwen3-1.7b-base")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "adapter.safetensors"
            for content in (b"x" * 7, struct.pack("<Q", 2**63) + b"{}", struct.pack("<Q", 17) + b"{}"):
                path.write_bytes(content)
                with self.assertRaises(subject.ModelAdmissionError):
                    subject.inspect_adapter_header(path, spec)
            raw = b'{"duplicate":1,"duplicate":2}'
            path.write_bytes(struct.pack("<Q", len(raw)) + raw + b"1234")
            with self.assertRaisesRegex(subject.ModelAdmissionError, "Duplicate"):
                subject.inspect_adapter_header(path, spec)

    def test_full_file_authentication_keeps_exact_bytes_and_checks_cancellation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "artifact.json"
            path.write_bytes(b'{"x":1}')
            expected = {"bytes": 7, "sha256": sha256(path.read_bytes()).hexdigest()}
            self.assertEqual(subject._file(path, maximum=7, expected=expected)[0], expected)
            with self.assertRaises(subject.ExperimentalCancelled):
                subject._file(path, maximum=7, should_stop=lambda: True)
            with self.assertRaises(subject.ModelAdmissionError):
                subject._file(path, maximum=6)
            path.write_bytes(b'{"x":2}')
            with self.assertRaises(subject.ModelAdmissionError):
                subject._file(path, maximum=7, expected=expected)

    def test_base_cache_link_is_hashed_and_watched_not_treated_as_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); directory = root / "snapshot"; directory.mkdir()
            blob = root / "blob"; blob.write_bytes(b"known content")
            target = directory / "model.safetensors"; target.symlink_to(blob)
            spec = {"metadata_files": {}, "weight_files": {"model.safetensors": {
                "bytes": len(blob.read_bytes()), "sha256": sha256(blob.read_bytes()).hexdigest()}}}
            _, _, watched = subject._base_files(directory, spec, None)
            subject._unchanged(watched)
            other = root / "other"; other.write_bytes(blob.read_bytes())
            target.unlink(); target.symlink_to(other)
            with self.assertRaisesRegex(subject.ModelAdmissionError, "changed"):
                subject._unchanged(watched)

    def test_counter_tracks_real_observed_slots_before_cancellation(self):
        observed = []
        stop = [False]
        ledger = subject._GenerationLedger(10, 4, 64, observed.append, lambda: stop[0])
        self.assertFalse(ledger.observe(8, 11))
        self.assertFalse(ledger.observe(8, 12))
        stop[0] = True
        with self.assertRaises(subject.ExperimentalCancelled):
            ledger.observe(8, 13)
        self.assertEqual(sum(observed), 12)
        self.assertEqual(ledger.seen, 3)
        with self.assertRaises(subject.ModelAdmissionError):
            ledger.observe(3, 14)

    def test_limits_allocation_and_session_construction_fail_closed(self):
        for kwargs in ({"max_calls": 129}, {"max_calls": True}, {"max_token_slots": 131073}):
            with self.assertRaises(subject.ModelAdmissionError):
                subject.SessionLimits(**kwargs)
        allocation = {"job_id": "12345", "gpus": 1, "cpus": 8, "memory_gib": 64,
                      "seconds": 120, "elapsed_seconds": 1.0}
        self.assertEqual(subject._reservation(allocation)["job_id"], "12345")
        for key, value in (("gpus", 2), ("elapsed_seconds", float("nan")), ("seconds", 7201),
                           ("elapsed_seconds", 111), ("memory_gib", 65)):
            changed = dict(allocation); changed[key] = value
            with self.assertRaises(subject.ModelAdmissionError):
                subject._reservation(changed)
        with self.assertRaises(subject.ModelAdmissionError):
            subject.TorchModelSession(None, None, None, None, {}, None, None, None)

    def test_bad_model_pair_rejected_before_framework_or_weight_load(self):
        before = set(sys.modules)
        with self.assertRaises(subject.ModelAdmissionError):
            subject.load_torch_model("qwen3-4b-base", base_directory="/nonexistent",
                adapter_directory="/not-an-adapter", reservation_check=lambda: {})
        with self.assertRaises(subject.ModelAdmissionError):
            subject.load_torch_model("qwen3-4b-base", base_directory="/nonexistent",
                adapter_kind="invented", reservation_check=lambda: {})
        self.assertFalse(any(name.startswith("torch") for name in set(sys.modules) - before))

    def test_historical_control_needs_exact_declared_manifest_not_schema_guess(self):
        spec = subject.model_spec("qwen3-1.7b-base")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            raw = json.dumps({"schema": "peano-hydra-retention-trained-adapter-v1", "model_trained": True,
                              "resume": False, "automatic_retry": False}).encode()
            (root / "manifest.json").write_bytes(raw)
            with self.assertRaisesRegex(subject.ModelAdmissionError, "exact preserved"):
                subject._adapter(root, sha256(raw).hexdigest(), spec, None, "historical_retention")


if __name__ == "__main__":
    unittest.main()
