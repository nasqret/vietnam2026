"""Additive WMI long11 provider; the existing selector and sealed modules stay unchanged."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import time

import wmi_model_runtime as shared
from wmi_candidate_core import Limits, require

HERE = Path(__file__).resolve().parent
MODEL_SELECTION_ID = "wmi-c6-long-vanilla11"
NAME = "WMI C6 long vanilla11 · step 16384 · local 4-bit"
RUN_ID = "wmi-pro6000-c6-long-vanilla-qwen_vanilla-s11"
CHECKPOINT_SHA = "177501bf7b662a210b6cf6887844a282365437c781e53138ad5495f02c620a06"
EXPORT_SHA = "659f71892bacdafc7488d8b683dd8dda051dfa4b054f74ba340db4da59fd07a3"
SELECTED_STEP = 16384
PINS = {
    "receipt.json": {"bytes": 114176, "sha256": "80a8074c0151302496d411d5193df1e038189511c9ab277e7509484eddca58be"},
    "selection.json": {"bytes": 4048, "sha256": "65af30a89ea720163cabedd8b00e39371d3fc7acf5e977ad781f3f777b9cd6a9"},
    "export-receipt.json": {"bytes": 4836, "sha256": "8a5f8ff7a5b57679609eb2334f63a7c4231cb5bfdd246f04143f5a809eb0474e"},
    "export_cpu.py": {"bytes": 6498, "sha256": "3d035052d2b324ae4016c49c0aa7fcf0162c7becec80be0698749cd839b7d7d5"},
    "newest_mlx_loader.py": {"bytes": 20385, "sha256": "093e7d4eaa5c6c1e37397c4736d74818529c47919dc40710864973672b619d03"},
}
CONFIG = {"schema": "hydra-newest-local-config-v1", "selection_id": MODEL_SELECTION_ID,
    "run_id": RUN_ID, "selected_step": SELECTED_STEP, "checkpoint_sha256": CHECKPOINT_SHA,
    "export": {"path": "selected-lora.safetensors", "bytes": 139520392, "sha256": EXPORT_SHA},
    "metadata_files": PINS, "lora_rank": 32, "lora_alpha": 64, "lora_dropout": 0,
    "recurrence_depth": 1, "memory_limit_bytes": 6 * 1024**3,
    "promotion_status": "candidate; fresh matched local results required", "automatic_fallback": False}


def _loader():
    path = HERE / "newest_mlx_loader.py"
    require(shared.trained._fingerprint(path, 256 * 1024) == PINS[path.name], "Standalone loader changed")
    name = "hydra_newest_wmi_mlx_loader"
    if name in sys.modules:
        module = sys.modules[name]
        require(Path(module.__file__).resolve() == path.resolve(), "Foreign cached newest loader")
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _metadata():
    config, config_pin = shared.trained._small(HERE / "provider-config.json")
    require(config == CONFIG, "Newest candidate configuration differs")
    values, pins = {}, {"provider-config.json": config_pin}
    for name, pin in PINS.items():
        actual = shared.trained._fingerprint(HERE / name, 256 * 1024)
        require(actual == pin, "Newest candidate metadata changed: " + name)
        pins[name] = actual
        if name.endswith(".json"):
            values[name] = json.loads((HERE / name).read_text())
    pins[Path(__file__).name] = shared.trained._fingerprint(Path(__file__), 256 * 1024)
    loader = _loader()
    spec = loader.LocalCandidateSpec(export_path=HERE / "selected-lora.safetensors",
        export_bytes=139520392, export_sha256=EXPORT_SHA, checkpoint_sha256=CHECKPOINT_SHA,
        training_receipt_path=HERE / "receipt.json", training_receipt_sha256=PINS["receipt.json"]["sha256"],
        export_receipt_path=HERE / "export-receipt.json", export_receipt_sha256=PINS["export-receipt.json"]["sha256"],
        selection_path=HERE / "selection.json", selection_sha256=PINS["selection.json"]["sha256"],
        exporter_path=HERE / "export_cpu.py", exporter_sha256=PINS["export_cpu.py"]["sha256"],
        selected_step=SELECTED_STEP, run_id=RUN_ID)
    loader.validate_cpu_export_receipt(values["export-receipt.json"], values["selection.json"],
                                      values["receipt.json"], spec, PINS["export_cpu.py"])
    loader.inspect_export_header(spec.export_path, spec.export_bytes)
    return loader, spec, values["receipt.json"], pins


def metadata_status():
    result = {"available": False, "selection_id": MODEL_SELECTION_ID, "name": NAME,
        "model_id": shared.trained.MODEL_ID, "revision": shared.trained.REVISION,
        "training_run_id": RUN_ID, "checkpoint_sha256": CHECKPOINT_SHA,
        "exported_adapter_sha256": EXPORT_SHA, "selected_step": SELECTED_STEP,
        "lora_rank": 32, "lora_alpha": 64, "recurrence_depth": 1,
        "conditioning": "model-v3 full library 247/247", "execution_authority": "current Hydra no imports",
        "loaded": False, "backend": "MLX", "device": "Apple Metal", "memory_limit_bytes": 6 * 1024**3,
        "quantized_preview": True, "numerical_equivalence_to_training": False,
        "automatic_fallback": False, "automatic_retry": False,
        "quality_status": "candidate; fresh matched local results required",
        "export_scope": "CPU serialization with bitwise tensor roundtrip; no inference claim"}
    try:
        base = shared.trained.metadata_status()
        require(base["available"], base["detail"])
        _metadata()
        result.update(available=True,
            detail="Newest locked WMI long11 checkpoint is installed for explicit selection; metadata checks do not load a model.",
            byte_authentication="Every export/base/source byte is rehashed before actual model loading.")
    except (OSError, ValueError, TypeError, KeyError) as error:
        result["detail"] = " ".join(str(error).split())[:512]
    return result


class NewestWMIModelPolicy(shared.WMIModelPolicy):
    selection_id = MODEL_SELECTION_ID
    name = NAME
    adapter_sha = EXPORT_SHA
    selected_step = SELECTED_STEP

    def __init__(self, capabilities, emit_progress=lambda event: None, **limits):
        super().__init__(capabilities, emit_progress, **limits)
        self._extra_pins = None
        self.identity = {"name": NAME, "selection_id": MODEL_SELECTION_ID,
            "checkpoint_sha256": CHECKPOINT_SHA, "exported_adapter_sha256": EXPORT_SHA,
            "selected_step": SELECTED_STEP, "training_run_id": RUN_ID, "used": False,
            "quantized_preview": True, "numerical_equivalence_to_training": False,
            "automatic_retry": False, "automatic_fallback": False,
            "export_scope": "authenticated CPU serialization; no inference score claimed"}
        self.evaluation_identity = copy.deepcopy(self.identity)

    def _prepare(self):
        if self.policy is not None:
            return
        require(not self.load_attempted, "Newest WMI initialization already failed; no reload or fallback")
        self.load_attempted = True
        self.emit({"phase": "authenticating", "message": "Checking newest locked WMI checkpoint and CPU export.", "model_calls": 0})
        loader, spec, training, self._extra_pins = _metadata()
        self._source_pins = {name: shared.trained._fingerprint(shared.APP / name, 256 * 1024)
                             for name in shared.SOURCE_FILES}
        data, evaluation, self._helper_pins = shared._frozen_helpers()
        require({name: pin["sha256"] for name, pin in self._helper_pins.items()}
                == training["identity"]["sources_sha256"], "Newest training helpers differ from authenticated frozen helpers")
        self.emit({"phase": "loading", "message": "Loading WMI long11 step16384 once on the local 4-bit base.", "model_calls": 0})
        policy = loader.load_local_policy(trained=shared.trained, spec=spec, frozen_data=data, frozen_eval=evaluation,
            limits=Limits(max_calls=1), should_stop=lambda: self.deadline is not None and time.monotonic() >= self.deadline)
        require(self.capabilities.allowed_commands == frozenset(policy.environment.capabilities.allowed_commands)
                and not self.capabilities.allowed_theorems and not policy.environment.capabilities.allowed_theorems,
                "Newest WMI and current native authority differ")
        self.policy = policy
        self.identity.update(copy.deepcopy(policy.evaluation_identity), name=NAME, selection_id=MODEL_SELECTION_ID,
            used=False, loaded=True, memory_limit_bytes=6 * 1024**3)
        self.evaluation_identity = copy.deepcopy(self.identity)

    def new_case(self, **kwargs):
        fresh = super().new_case(**kwargs)
        fresh._extra_pins = copy.deepcopy(self._extra_pins)
        return fresh

    def finalize(self):
        result = super().finalize()
        if self._extra_pins is not None:
            for name, pin in self._extra_pins.items():
                require(shared.trained._fingerprint(HERE / name, 256 * 1024) == pin,
                        "Newest provider metadata/source changed during inference: " + name)
        return result


def create_policy(capabilities, emit_progress=lambda event: None):
    return NewestWMIModelPolicy(capabilities, emit_progress)
