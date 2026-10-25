"""Small offline checks; no framework/model/native execution or setup invocation."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

APP = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("playground_runtime_test_subject", APP / "model_runtime.py")
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


def write_json(path, value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    path.write_bytes(raw)
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


class RuntimeChecks(unittest.TestCase):
    def test_unicode_progress_respects_wire_byte_limit_without_changing_record(self):
        source = {"phase": "proposing", "message": "Model proposal", "goals": ["𐍈" * 512] * 3}
        emitted = []
        runtime._progress(emitted.append, source)
        self.assertEqual(source["goals"], ["𐍈" * 512] * 3)
        self.assertTrue(emitted[0]["preview_omitted_for_byte_limit"])
        wire = json.dumps({"type": "progress", "progress": emitted[0]}, ensure_ascii=False).encode()
        self.assertLess(len(wire), 4096)

    def test_status_never_imports_model_frameworks(self):
        before = set(sys.modules)
        result = runtime.metadata_status()
        self.assertEqual(result["name"], "Mixed adapter · 4-bit local preview")
        self.assertFalse(result["numerical_equivalence_to_training"])
        added = set(sys.modules) - before
        self.assertFalse(any(name.split(".")[0] in {"torch", "mlx", "mlx_lm", "transformers", "tokenizers"}
                             for name in added))

    def test_actual_saved_adapter_header_and_incompatible_mappings(self):
        # Read only the 52 KiB header of the real preserved safetensors file.
        path = runtime.MODEL_ROOT / "adapter/adapter_model.safetensors"
        with path.open("rb") as stream:
            length = struct.unpack("<Q", stream.read(8))[0]
            self.assertLessEqual(length, 256 * 1024)
            header = json.loads(stream.read(length))
        tensors = {name: value for name, value in header.items() if name != "__metadata__"}
        self.assertEqual({item["dtype"] for item in tensors.values()}, {"F32"})
        shapes = {name: tuple(item["shape"]) for name, item in tensors.items()}
        mapping = runtime.peft_mapping(shapes)
        self.assertEqual(len(mapping), 392)
        prefix = "base_model.model.model.layers.27.mlp.down_proj"
        self.assertEqual(mapping[prefix + ".lora_A.weight"], "model.layers.27.mlp.down_proj.lora_a")
        self.assertEqual(mapping[prefix + ".lora_B.weight"], "model.layers.27.mlp.down_proj.lora_b")
        for changed in (dict(list(shapes.items())[1:]), {**shapes, "untrained.lora_A.weight": (16, 2048)},
                        {**shapes, prefix + ".lora_A.weight": (6144, 16)}):
            with self.assertRaises(ValueError):
                runtime.peft_mapping(changed)

    def test_forbidden_high_logits_never_become_candidates_and_ties_are_stable(self):
        import numpy as np
        logits = np.array([[1000.0, -1.0, -1.0, -2.0], [2000.0, -3.0, -3.0, -4.0]])
        active = [((7,), -0.25), ((8,), -0.5)]
        choices = runtime._rank_extensions(logits, active, [[3, 2, 1], [3, 2]], 2, np)
        self.assertEqual(choices[:2], [(-1.25, 0, 1), (-1.25, 0, 2)])
        self.assertFalse(any(token == 0 for _, _, token in choices))
        with self.assertRaises(ValueError):
            runtime._rank_extensions(logits, active, [[4], [2]], 2, np)

    def test_completed_beams_and_cache_parent_indices_remain_separate(self):
        active = [((10,), -1.0), ((11,), -1.0)]
        choices = [(-1.1, 1, 99), (-1.2, 0, 20), (-1.3, 1, 21), (-1.4, 0, 99)]
        live, parents, finished = runtime._advance_beams(active, choices, [], 2, 99)
        self.assertEqual(parents, [0, 1])
        self.assertEqual(live, [((10, 20), -1.2), ((11, 21), -1.3)])
        self.assertEqual(finished, [((11, 99), -0.55)])
        # The below-width EOS is not silently admitted as a better candidate.
        self.assertNotIn((10, 99), [tokens for tokens, _ in finished])

    def test_readiness_requires_actual_zero_exit_and_exact_current_manifest(self):
        with tempfile.TemporaryDirectory(prefix="hydra-runtime-readiness-fixture-") as temporary:
            app = Path(temporary)
            root = app / ".runtime"
            model = root / "model"
            model.mkdir(parents=True)
            helper = app / "setup_model.py"
            helper.write_bytes(b"# explicit offline test fixture, never executed\n")
            helper_pin = {"path": str(helper), **runtime._fingerprint(helper, 1024)}
            manifest = write_json(model / "manifest.json", {"fixture": True})
            invocation = {"schema": "hydra-playground-setup-invocation-v1", "status": "exited", "exit_code": 0,
                          "argv": ["fixture-python", "-I", "-B", str(helper)], "automatic_retry": False,
                          "observed_from": "actual-tool-process-completion", "helper": helper_pin,
                          "model_manifest": manifest}
            with patch.multiple(runtime, APP=app, RUNTIME=root, QUANTIZED=model, READY=root / "model-ready.json"):
                def install(record):
                    invocation_pin = write_json(root / "setup-invocation.json", record)
                    write_json(root / "model-ready.json", {"schema": "hydra-playground-model-ready-v1", "status": "ready",
                        "setup_invocation": invocation_pin, "model_manifest": manifest,
                        "numerical_equivalence_to_training": False, "automatic_training": False})
                install(invocation)
                runtime._readiness()
                for changed in ({**invocation, "exit_code": 2}, {**invocation, "exit_code": False},
                                {**invocation, "observed_from": "inner-file-only"}):
                    install(changed)
                    with self.assertRaises(ValueError):
                        runtime._readiness()
                install(invocation)
                (model / "manifest.json").write_bytes(b"changed\n")
                with self.assertRaises(ValueError):
                    runtime._readiness()

    def test_regular_byte_inputs_do_not_admit_links_or_duplicate_json(self):
        with tempfile.TemporaryDirectory(prefix="hydra-runtime-path-fixture-") as temporary:
            root = Path(temporary)
            path = root / "original"
            path.write_bytes(b"abc")
            first = runtime._fingerprint(path, 8)
            self.assertEqual(first["sha256"], hashlib.sha256(b"abc").hexdigest())
            link = root / "link"
            link.symlink_to(path)
            with self.assertRaises(ValueError):
                runtime._safe_path(root, "link")
            with self.assertRaises(OSError):
                runtime._fingerprint(link, 8)
            with self.assertRaises(ValueError):
                runtime._json(b'{"status":1,"status":2}')


if __name__ == "__main__":
    unittest.main(verbosity=2)
