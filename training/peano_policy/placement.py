"""Select an inference device and dtype without importing PyTorch globally.

The trained policy loader passes its already-imported ``torch`` module into
``resolve_runtime_placement``.  Keeping this module model-free makes command
line validation and unit tests independent of a multi-gigabyte model load.
Explicit requests fail closed; only ``device=auto`` may fall back to another
backend.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


DEVICE_CHOICES = ("auto", "cuda", "mps", "cpu")
DTYPE_CHOICES = ("auto", "bfloat16", "float16", "float32")
_DTYPE_ATTRIBUTES = {
    "bfloat16": "bfloat16",
    "float16": "float16",
    "float32": "float32",
}


class RuntimePlacementError(ValueError):
    """A requested accelerator or precision is unavailable or unsafe."""


@dataclass(frozen=True, slots=True)
class RuntimePlacement:
    """One validated runtime placement with a JSON-safe audit record."""

    requested_device: str
    requested_dtype: str
    device: str
    dtype: str
    device_reason: str
    dtype_reason: str
    cuda_available: bool
    cuda_bfloat16_supported: bool | None
    mps_built: bool
    mps_reported_available: bool
    mps_allocation_succeeded: bool | None
    mps_bfloat16_supported: bool | None

    @property
    def accelerator(self) -> bool:
        return self.device in {"cuda", "mps"}

    def dtype_object(self, torch_module: Any) -> Any:
        """Return the torch dtype only at the integration boundary."""

        attribute = _DTYPE_ATTRIBUTES[self.dtype]
        try:
            return getattr(torch_module, attribute)
        except AttributeError:
            raise RuntimePlacementError(
                f"PyTorch does not expose the resolved dtype {self.dtype}"
            ) from None

    def device_object(self, torch_module: Any) -> Any:
        """Return a torch device when available, otherwise its safe string."""

        factory = getattr(torch_module, "device", None)
        return factory(self.device) if callable(factory) else self.device

    def to_record(self) -> dict[str, object]:
        """Return detached, JSON-serializable placement provenance."""

        return {
            "requested_device": self.requested_device,
            "requested_dtype": self.requested_dtype,
            "device": self.device,
            "dtype": self.dtype,
            "accelerator": self.accelerator,
            "device_reason": self.device_reason,
            "dtype_reason": self.dtype_reason,
            "capabilities": {
                "cuda_available": self.cuda_available,
                "cuda_bfloat16_supported": self.cuda_bfloat16_supported,
                "mps_built": self.mps_built,
                "mps_reported_available": self.mps_reported_available,
                "mps_allocation_succeeded": self.mps_allocation_succeeded,
                "mps_bfloat16_supported": self.mps_bfloat16_supported,
            },
        }


def _boolean_call(owner: Any, name: str) -> bool:
    method = getattr(owner, name, None)
    if not callable(method):
        return False
    try:
        return bool(method())
    except Exception:
        return False


def _mps_probe(torch_module: Any, *, dtype: Any | None = None) -> bool:
    factory = getattr(torch_module, "ones", None)
    if not callable(factory):
        return False
    options: dict[str, Any] = {"device": "mps"}
    if dtype is not None:
        options["dtype"] = dtype
    try:
        probe = factory(1, **options)
        mps = getattr(torch_module, "mps", None)
        synchronize = getattr(mps, "synchronize", None)
        if callable(synchronize):
            synchronize()
        del probe
        return True
    except Exception:
        return False


def _require_choice(value: object, choices: tuple[str, ...], label: str) -> str:
    if type(value) is not str or value not in choices:
        rendered = ", ".join(choices)
        raise RuntimePlacementError(f"{label} must be one of: {rendered}")
    return value


def resolve_runtime_placement(
    torch_module: Any,
    *,
    device: str = "auto",
    dtype: str = "auto",
) -> RuntimePlacement:
    """Resolve ``auto|cuda|mps|cpu`` and a compatible inference dtype.

    CUDA remains the first automatic choice, preserving the existing WMI
    A100 behavior.  Apple MPS is selected only after a real allocation probe;
    this avoids trusting a build-time flag.  MPS BF16 likewise receives a
    small runtime probe.  CPU defaults to FP32 because CPU FP16 execution is
    incomplete and commonly slower than FP32.
    """

    requested_device = _require_choice(device, DEVICE_CHOICES, "device")
    requested_dtype = _require_choice(dtype, DTYPE_CHOICES, "dtype")

    cuda = getattr(torch_module, "cuda", None)
    cuda_available = _boolean_call(cuda, "is_available")
    cuda_bfloat16 = (
        _boolean_call(cuda, "is_bf16_supported") if cuda_available else None
    )

    backends = getattr(torch_module, "backends", None)
    mps_backend = getattr(backends, "mps", None)
    mps_built = _boolean_call(mps_backend, "is_built")
    mps_reported = _boolean_call(mps_backend, "is_available")
    mps_allocation: bool | None = None
    if mps_built and mps_reported:
        mps_allocation = _mps_probe(torch_module)
    mps_usable = mps_allocation is True

    mps_bfloat16: bool | None = None
    if mps_usable and hasattr(torch_module, "bfloat16"):
        mps_bfloat16 = _mps_probe(
            torch_module,
            dtype=getattr(torch_module, "bfloat16"),
        )

    if requested_device == "auto":
        if cuda_available:
            resolved_device = "cuda"
            device_reason = "auto-preferred-cuda"
        elif mps_usable:
            resolved_device = "mps"
            device_reason = "auto-preferred-mps"
        else:
            resolved_device = "cpu"
            device_reason = "auto-cpu-fallback"
    else:
        resolved_device = requested_device
        device_reason = "explicit-request"
        if resolved_device == "cuda" and not cuda_available:
            raise RuntimePlacementError("CUDA was requested but is unavailable")
        if resolved_device == "mps" and not mps_usable:
            raise RuntimePlacementError(
                "MPS was requested but its availability/allocation probe failed"
            )

    if requested_dtype == "auto":
        if resolved_device == "cuda":
            if cuda_bfloat16:
                resolved_dtype = "bfloat16"
                dtype_reason = "auto-cuda-bfloat16"
            else:
                resolved_dtype = "float16"
                dtype_reason = "auto-cuda-float16-fallback"
        elif resolved_device == "mps":
            if mps_bfloat16:
                resolved_dtype = "bfloat16"
                dtype_reason = "auto-mps-bfloat16"
            else:
                resolved_dtype = "float16"
                dtype_reason = "auto-mps-float16-fallback"
        else:
            resolved_dtype = "float32"
            dtype_reason = "auto-cpu-float32"
    else:
        resolved_dtype = requested_dtype
        dtype_reason = "explicit-request"

    if not hasattr(torch_module, _DTYPE_ATTRIBUTES[resolved_dtype]):
        raise RuntimePlacementError(
            f"PyTorch does not expose the requested dtype {resolved_dtype}"
        )
    if (
        resolved_device == "cuda"
        and resolved_dtype == "bfloat16"
        and not cuda_bfloat16
    ):
        raise RuntimePlacementError(
            "CUDA BF16 was requested but the selected device does not support it"
        )
    if (
        resolved_device == "mps"
        and resolved_dtype == "bfloat16"
        and not mps_bfloat16
    ):
        raise RuntimePlacementError(
            "MPS BF16 was requested but its allocation probe failed"
        )
    if resolved_device == "cpu" and resolved_dtype == "float16":
        raise RuntimePlacementError(
            "CPU float16 is not an admitted inference placement; use float32"
        )

    return RuntimePlacement(
        requested_device=requested_device,
        requested_dtype=requested_dtype,
        device=resolved_device,
        dtype=resolved_dtype,
        device_reason=device_reason,
        dtype_reason=dtype_reason,
        cuda_available=cuda_available,
        cuda_bfloat16_supported=cuda_bfloat16,
        mps_built=mps_built,
        mps_reported_available=mps_reported,
        mps_allocation_succeeded=mps_allocation,
        mps_bfloat16_supported=mps_bfloat16,
    )


__all__ = [
    "DEVICE_CHOICES",
    "DTYPE_CHOICES",
    "RuntimePlacement",
    "RuntimePlacementError",
    "resolve_runtime_placement",
]
