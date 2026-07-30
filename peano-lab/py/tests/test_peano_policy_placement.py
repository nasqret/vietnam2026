from __future__ import annotations

import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from training.peano_policy.placement import (
    RuntimePlacementError,
    resolve_runtime_placement,
)
import training.peano_policy.generate as generation


class _Backend:
    def __init__(self, **values: bool) -> None:
        self._values = values

    def is_available(self) -> bool:
        return self._values.get("available", False)

    def is_built(self) -> bool:
        return self._values.get("built", False)

    def is_bf16_supported(self) -> bool:
        return self._values.get("bf16", False)


class _MpsRuntime:
    @staticmethod
    def synchronize() -> None:
        return None


class _FakeTorch:
    bfloat16 = "torch.bfloat16"
    float16 = "torch.float16"
    float32 = "torch.float32"

    def __init__(
        self,
        *,
        cuda: bool = False,
        cuda_bf16: bool = False,
        mps: bool = False,
        mps_bf16: bool = True,
    ) -> None:
        self.cuda = _Backend(available=cuda, bf16=cuda_bf16)
        self.backends = type(
            "Backends", (), {"mps": _Backend(built=mps, available=mps)}
        )()
        self.mps = _MpsRuntime()
        self._mps_bf16 = mps_bf16

    def ones(self, count: int, *, device: str, dtype: str | None = None) -> list[int]:
        assert count == 1
        if device != "mps":
            raise AssertionError(device)
        if dtype == self.bfloat16 and not self._mps_bf16:
            raise RuntimeError("unsupported")
        return [1]

    @staticmethod
    def device(name: str) -> str:
        return f"device:{name}"


def test_auto_preserves_cuda_bfloat16_precedence() -> None:
    torch = _FakeTorch(cuda=True, cuda_bf16=True, mps=True)

    placement = resolve_runtime_placement(torch)

    assert (placement.device, placement.dtype) == ("cuda", "bfloat16")
    assert placement.dtype_object(torch) == torch.bfloat16
    assert placement.device_object(torch) == "device:cuda"


def test_auto_selects_probed_mps_bfloat16() -> None:
    placement = resolve_runtime_placement(_FakeTorch(mps=True))

    assert (placement.device, placement.dtype) == ("mps", "bfloat16")
    record = placement.to_record()
    assert record["accelerator"] is True
    assert record["capabilities"]["mps_allocation_succeeded"] is True
    json.dumps(record, allow_nan=False)


def test_auto_uses_mps_float16_when_bfloat16_probe_fails() -> None:
    placement = resolve_runtime_placement(
        _FakeTorch(mps=True, mps_bf16=False)
    )

    assert (placement.device, placement.dtype) == ("mps", "float16")
    assert placement.dtype_reason == "auto-mps-float16-fallback"


def test_auto_cpu_is_safe_float32() -> None:
    placement = resolve_runtime_placement(_FakeTorch())

    assert (placement.device, placement.dtype) == ("cpu", "float32")
    assert placement.accelerator is False


@pytest.mark.parametrize(
    ("device", "dtype", "message"),
    [
        ("cuda", "auto", "CUDA was requested"),
        ("mps", "auto", "MPS was requested"),
        ("cpu", "float16", "CPU float16"),
    ],
)
def test_explicit_unsupported_placement_fails_closed(
    device: str, dtype: str, message: str
) -> None:
    with pytest.raises(RuntimePlacementError, match=message):
        resolve_runtime_placement(_FakeTorch(), device=device, dtype=dtype)


def test_explicit_mps_bfloat16_does_not_silently_fallback() -> None:
    with pytest.raises(RuntimePlacementError, match="MPS BF16"):
        resolve_runtime_placement(
            _FakeTorch(mps=True, mps_bf16=False),
            device="mps",
            dtype="bfloat16",
        )


def test_unknown_choice_is_rejected_before_backend_selection() -> None:
    with pytest.raises(RuntimePlacementError, match="device must be one of"):
        resolve_runtime_placement(_FakeTorch(), device="metal")


def test_adapter_loader_threads_resolved_placement_and_offline_cache(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    revision = "a" * 40
    manifest = {
        "v": generation.MANIFEST_VERSION,
        "prompt_version": "test-prompt",
        "prompt_contract_sha256": "contract",
        "base_model": {
            "id": "unit/base",
            "requested_revision": revision,
            "resolved_snapshot_hash": revision,
        },
        "tokenizer": {
            "resolved_snapshot_hash": revision,
            "artifacts": {},
        },
        "adapter": {},
    }
    (tmp_path / "training-manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    monkeypatch.setattr(generation, "_require_diagnostic_mode", lambda *a, **k: None)
    monkeypatch.setattr(
        generation,
        "attested_training_environment",
        lambda value: SimpleNamespace(prompt_version="test-prompt"),
    )
    monkeypatch.setattr(generation, "prompt_contract_sha256", lambda value: "contract")
    monkeypatch.setattr(generation, "require_safetensors_adapter", lambda value: None)
    monkeypatch.setattr(
        generation,
        "verify_artifact_directory",
        lambda *args: tmp_path,
    )

    calls: dict[str, object] = {}

    class Placement:
        device = "mps"

        @staticmethod
        def dtype_object(torch_module):
            assert torch_module is fake_torch
            return "torch.bfloat16"

        @staticmethod
        def device_object(torch_module):
            assert torch_module is fake_torch
            return "mps-device"

    class Model:
        device = "cpu"
        dtype = "torch.bfloat16"

        def eval(self):
            calls["eval"] = True

        def to(self, device):
            calls["to"] = device
            self.device = device
            return self

    model = Model()
    fake_torch = SimpleNamespace(
        manual_seed=lambda seed: calls.setdefault("torch_seed", seed),
        cuda=SimpleNamespace(
            is_available=lambda: False,
            manual_seed_all=lambda seed: calls.setdefault("cuda_seed", seed),
        ),
        mps=SimpleNamespace(
            manual_seed=lambda seed: calls.setdefault("mps_seed", seed)
        ),
    )

    class AutoModel:
        @staticmethod
        def from_pretrained(model_id, **kwargs):
            calls["model_id"] = model_id
            calls["model_options"] = kwargs
            return object()

    class AutoTokenizer:
        @staticmethod
        def from_pretrained(path, **kwargs):
            calls["tokenizer"] = (path, kwargs)
            return object()

    class PeftModel:
        @staticmethod
        def from_pretrained(base, path):
            calls["peft"] = (base, path)
            return model

    monkeypatch.setattr(
        generation,
        "resolve_runtime_placement",
        lambda module, **kwargs: (
            calls.update(placement=(module, kwargs)) or Placement()
        ),
    )
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setitem(sys.modules, "peft", SimpleNamespace(PeftModel=PeftModel))
    monkeypatch.setitem(
        sys.modules,
        "transformers",
        SimpleNamespace(
            AutoModelForCausalLM=AutoModel,
            AutoTokenizer=AutoTokenizer,
            set_seed=lambda seed: calls.setdefault("transformers_seed", seed),
        ),
    )

    cache = tmp_path / "cache"
    loaded, _, _ = generation.load_adapter(
        tmp_path,
        seed=19,
        device="mps",
        dtype="bfloat16",
        local_files_only=True,
        cache_dir=cache,
    )

    assert loaded is model
    assert calls["placement"] == (
        fake_torch,
        {"device": "mps", "dtype": "bfloat16"},
    )
    assert calls["mps_seed"] == 19
    assert calls["to"] == "mps-device"
    assert model.peano_runtime_placement.__class__ is Placement
    assert calls["model_options"] == {
        "revision": revision,
        "torch_dtype": "torch.bfloat16",
        "attn_implementation": "sdpa",
        "low_cpu_mem_usage": True,
        "trust_remote_code": False,
        "use_safetensors": True,
        "local_files_only": True,
        "cache_dir": cache,
    }
