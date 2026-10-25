"""Reversible website selection, separate from the sealed comparison selector."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import model_selection as original

APP = Path(__file__).resolve().parent
NEWEST_ID = "wmi-c6-long-vanilla11"
DEFAULT_MODEL_ID = NEWEST_ID
DEFAULT_SEARCH_MODE = "portfolio"
PROMOTION_EVIDENCE_SHA = "408c8a9f0ee89710fa9390dba5796bb0af0bf2ff83883dd44deb3d6a3e4b65e7"
MODEL_IDS = (*original.MODEL_IDS, NEWEST_ID)
PROVIDER_ROOT = APP.parent / "output/hydra-wmi-integration-2026-10-21/newest-wmi"
MANIFEST_SHA = "6c97ad8ebdc9d0b1098b7dc446a628ddafa486c7c1f7cee16489796c426418d6"
CACHE_ROOT = PROVIDER_ROOT.parent / "performance-v2"
CACHE_RUNTIME_SHA = "6d53161ee2a74d89f90fef69508cc36635282bcb5a60c68d24948819b1b1ae9b"
CACHE_MANIFEST_SHA = "ce66ef169b31c6801b948c59eb701f1147ea3792b6b526bc0cb5a1631a5814e2"


def cached_runtime():
    entry = CACHE_ROOT / "cached_policy_runtime.py"
    manifest = CACHE_ROOT / "CACHED_POLICY_RUNTIME_MANIFEST.json"
    for path, expected in ((entry, CACHE_RUNTIME_SHA), (manifest, CACHE_MANIFEST_SHA)):
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 256 * 1024:
            raise ValueError("The reviewed tokenizer runtime is unavailable.")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("The reviewed tokenizer runtime changed.")
    name = "hydra_deployed_cached_length_v1"
    if name in sys.modules:
        module = sys.modules[name]
        if Path(module.__file__).resolve() != entry:
            raise ValueError("Foreign cached tokenizer runtime.")
        return module
    spec = importlib.util.spec_from_file_location(name, entry)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def resolve_model_id(requested=None):
    selected = DEFAULT_MODEL_ID if requested is None else requested
    if type(selected) is not str or selected not in MODEL_IDS:
        raise ValueError("Select one of the installed Hydra models.")
    return selected


def newest_provider():
    manifest_path = PROVIDER_ROOT / "PROVIDER_MANIFEST.json"
    if manifest_path.is_symlink() or not manifest_path.is_file() or manifest_path.stat().st_size > 16384:
        raise ValueError("The newest WMI provider manifest is unavailable.")
    raw = manifest_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA:
        raise ValueError("The newest WMI provider manifest changed.")
    manifest = json.loads(raw)
    if manifest["selection_id"] != NEWEST_ID:
        raise ValueError("The newest WMI provider identity differs.")
    for record in manifest["files"]:
        path = Path(record["path"])
        if path.parent != PROVIDER_ROOT or path.is_symlink() or not path.is_file() or path.stat().st_size > 256 * 1024:
            raise ValueError("Invalid installed WMI provider source.")
        raw = path.read_bytes()
        if len(raw) != record["bytes"] or hashlib.sha256(raw).hexdigest() != record["sha256"]:
            raise ValueError("Installed WMI provider changed: " + path.name)
    entry = Path(manifest["entrypoint"]["path"])
    name = "hydra_deployed_wmi_long11"
    if name in sys.modules:
        module = sys.modules[name]
        if Path(module.__file__).resolve() != entry:
            raise ValueError("Foreign cached WMI provider.")
        return module
    spec = importlib.util.spec_from_file_location(name, entry)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def metadata_status(requested=None):
    selected = resolve_model_id(requested)
    if selected == NEWEST_ID:
        try:
            result = newest_provider().metadata_status()
        except (OSError, ValueError, KeyError, ImportError) as error:
            result = {"available": False, "name": "WMI C6 long vanilla11", "detail": str(error)[:512]}
    else:
        result = original.metadata_status(selected)
    try:
        cached_runtime()._bindings()
    except (OSError, ValueError, KeyError, ImportError) as error:
        result = {**result, "available": False, "detail": str(error)[:512]}
    if selected == NEWEST_ID and result.get("available"):
        result.update(
            quality_status="promoted after the completed local paired comparison; limited development evidence",
            promotion_evidence_sha256=PROMOTION_EVIDENCE_SHA,
            local_comparison={"primary_positive_proofs": 4, "primary_positive_total": 8,
                              "regression_positive_proofs": 0, "regression_positive_total": 4,
                              "historical_positive_proofs": 0, "false_controls_accepted": 0,
                              "false_controls_total": 6, "held_out_benchmark": False},
            detail="Default: WMI long11, step 16384. Fresh local comparison: 4/12 positive proofs versus 0/12 for the old adapter; no false controls accepted (6 each). Small selected development panel, not unseen accuracy.")
    return {**result, "selection_id": selected, "default_selection_id": DEFAULT_MODEL_ID,
            "is_default": selected == DEFAULT_MODEL_ID, "selectable_models": list(MODEL_IDS),
            "sequential_tokenizer_length_policy": "hydra-immutable-tokenizer-length-v1",
            "automatic_fallback": False}


def create_policy(model_id, capabilities, emit_progress, **case_limits):
    selected = resolve_model_id(model_id)
    if selected == NEWEST_ID:
        policy = newest_provider().NewestWMIModelPolicy(capabilities, emit_progress, **case_limits)
    else:
        policy = original.create_policy(selected, capabilities, emit_progress, **case_limits)
    return cached_runtime().wrap_policy(policy)
