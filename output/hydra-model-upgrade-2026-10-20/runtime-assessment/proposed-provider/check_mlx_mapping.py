"""Pure metadata fixtures for the proposed rank32 conversion; no MLX import."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import struct
import sys
import tempfile

sys.dont_write_bytecode = True
from hydra_mlx_vanilla import LORA_DIMS, rank32_mapping, inspect_export_header
from hydra_torch_candidate import BindingError


def main():
    shapes, header, offset = {}, {}, 0
    for layer in range(28):
        for projection, (input_size, output_size) in LORA_DIMS.items():
            for ab, shape in (("A", (32, input_size)), ("B", (output_size, 32))):
                name = f"base_model.base_model.model.model.layers.{layer}.{projection}.lora_{ab}.default.weight"
                shapes[name] = shape
                size = 4 * shape[0] * shape[1]
                header[name] = {"dtype": "F32", "shape": list(shape), "data_offsets": [offset, offset + size]}
                offset += size
    mapped = rank32_mapping(shapes)
    assert len(mapped) == len(set(mapped.values())) == 392
    source_a = "base_model.base_model.model.model.layers.27.mlp.down_proj.lora_A.default.weight"
    source_b = "base_model.base_model.model.model.layers.0.self_attn.k_proj.lora_B.default.weight"
    assert mapped[source_a] == "model.layers.27.mlp.down_proj.lora_a" and shapes[source_a][::-1] == (6144, 32)
    assert mapped[source_b] == "model.layers.0.self_attn.k_proj.lora_b" and shapes[source_b][::-1] == (32, 1024)
    checks = ["392 exact matrix names, unique targets and asymmetric transpose axes"]

    for bad in ({**shapes, "damping_logits": (12,)},
                {key: value for key, value in shapes.items() if key != source_a},
                {**shapes, source_a: (16, 6144)}):
        try:
            rank32_mapping(bad)
            raise AssertionError("invalid rank/tensor set accepted")
        except BindingError:
            pass
    checks.append("recurrence tensors, missing matrices and wrong rank are refused")

    with tempfile.TemporaryDirectory(prefix="hydra-metadata-fixture-") as temporary:
        path = Path(temporary) / "fixture-only-not-model.safetensors"

        def write_fixture(value):
            raw = json.dumps(value, separators=(",", ":")).encode()
            total = 8 + len(raw) + offset
            with path.open("wb") as stream:
                stream.write(struct.pack("<Q", len(raw)))
                stream.write(raw)
                stream.truncate(total)  # Sparse placeholder; no real weights are generated.
            return total

        size = write_fixture(header)
        assert inspect_export_header(path, size) == mapped
        checks.append("bounded safetensors metadata exactly covers the declared data region")
        for key, value in (("dtype", "BF16"), ("data_offsets", [1, header[source_a]["data_offsets"][1]])):
            bad = copy.deepcopy(header)
            bad[source_a][key] = value
            try:
                inspect_export_header(path, write_fixture(bad))
                raise AssertionError("invalid dtype/span accepted")
            except BindingError:
                pass
        checks.append("wrong dtype and malformed tensor byte spans are refused")
        size = write_fixture(header)
        with path.open("ab") as stream:
            stream.write(b"x")
        try:
            inspect_export_header(path, size + 1)
            raise AssertionError("unlisted trailing byte accepted")
        except BindingError:
            pass
        checks.append("unlisted trailing tensor bytes are refused")

    forbidden = [name for name in sys.modules if name.split(".")[0] in
                 {"mlx", "mlx_lm", "torch", "transformers", "peft", "peano_lab", "training"}]
    assert not forbidden, forbidden
    print(json.dumps({"format": "hydra-local-mlx-mapping-fixtures-v1", "passed": True,
        "checks": checks, "framework_and_native_imports": forbidden,
        "real_model_calls": 0, "native_proof_calls": 0, "numerical_mapping_tested": False}, indent=2))


if __name__ == "__main__":
    main()
