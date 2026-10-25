"""Additive lazy host facade; authenticated original model/decoder stay intact.

Deployment selects and constructs its existing original policy, then calls
wrap_policy(policy). No model or framework is loaded on module import/wrapping.
The caller must pin this entrypoint externally before importing it; this facade
then binds its own source and the reviewed immutable-tokenizer wrapper through
each case. This module is not automatically registered with any live route.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WRAPPER_SHA256 = "98ff0d972f053a242066cc9ab26ec9103c70f7c761c605a1aee97c6657cac1e5"
MANIFEST_SHA256 = "800e6a792d08e19360769ca60e366495f0f082060441521a13e4b3cb6177dc46"
POLICY = "hydra-cached-length-host-v1"


def _pin(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 256 * 1024:
        raise ValueError("Unavailable bounded cached-tokenizer runtime source")
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _bindings():
    pins = {name: _pin(HERE / name) for name in
            ("cached_tokenizer_length.py", "TOKENIZER_WRAPPER_MANIFEST.json", "cached_policy_runtime.py")}
    if pins["cached_tokenizer_length.py"]["sha256"] != WRAPPER_SHA256 or pins["TOKENIZER_WRAPPER_MANIFEST.json"]["sha256"] != MANIFEST_SHA256:
        raise ValueError("Reviewed tokenizer wrapper/manifest changed")
    manifest = json.loads((HERE / "TOKENIZER_WRAPPER_MANIFEST.json").read_text())
    if manifest["entrypoint"]["sha256"] != WRAPPER_SHA256 or manifest["actual_cpu_test"]["passed"] is not True:
        raise ValueError("Missing reviewed tokenizer wrapper evidence")
    return pins


def _wrapper_type():
    name = "hydra_immutable_tokenizer_length_v1"
    path = HERE / "cached_tokenizer_length.py"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            sys.modules.pop(name, None)
            raise
    module = sys.modules[name]
    if Path(module.__file__).resolve() != path:
        raise ValueError("Foreign cached tokenizer wrapper module")
    return module.ImmutableTokenizerLength


class CachedLengthPolicy:
    def __init__(self, original, *, _shared=None):
        if isinstance(original, CachedLengthPolicy):
            raise ValueError("Do not wrap a cached policy again")
        self._original = original
        self._pins = _bindings()
        self._context = _shared
        self._last_custody = None

    def _identity(self, identity):
        return {**copy.deepcopy(identity), "tokenizer_length_policy": "hydra-immutable-tokenizer-length-v1",
                "tokenizer_host_policy": POLICY, "tokenizer_runtime_pins": copy.deepcopy(self._pins),
                "numerical_decoder_changed": False, "use_cache": False}

    @property
    def identity(self):
        return self._identity(self._original.identity)

    @property
    def evaluation_identity(self):
        return self._identity(self._original.evaluation_identity)

    @property
    def policy(self):
        return self._original.policy

    def __getattr__(self, name):
        # Preserve counters, selection_id and ordinary read metadata without
        # inheriting the original class or altering any sealed implementation.
        return getattr(self._original, name)

    def _assert_pointers(self):
        if self._context is None or self.policy is None:
            raise ValueError("Cached tokenizer policy has not been prepared")
        if self.policy.backend is not self._context["backend"] or self.policy.tokenizer is not self._context["tokenizer"]:
            raise ValueError("Original decoder or installed immutable tokenizer was replaced")

    def _verify(self):
        if _bindings() != self._pins:
            raise ValueError("Cached policy runtime source changed during the request")
        self._assert_pointers()
        self._last_custody = self._context["tokenizer"].verify_unchanged()
        return copy.deepcopy(self._last_custody)

    def prepare(self):
        if self._context is None:
            # Original prepare owns all source/base/adapter authentication and
            # the existing one-time load. Only wrap after it returns cleanly.
            self._original.prepare()
            if _bindings() != self._pins:
                raise ValueError("Cached runtime source changed during model loading")
            backend = self.policy.backend
            wrapper = _wrapper_type()(self.policy.tokenizer)
            self.policy.tokenizer = wrapper
            self._context = {"backend": backend, "tokenizer": wrapper}
            self._verify()
        else:
            self._assert_pointers()
        return self.identity

    def prompt_renderer(self, goals):
        self.prepare()
        return self._original.prompt_renderer(goals)

    def provider_factory(self, **limits):
        self.prepare()
        return self._original.provider_factory(**limits)

    @property
    def policy_environment(self):
        self.prepare()
        return self._original.policy_environment

    def propose(self, goals_before, *, max_candidates):
        self.prepare()
        return self._original.propose(goals_before, max_candidates=max_candidates)

    def new_case(self, **limits):
        self.prepare()
        self._verify()
        case = self._original.new_case(**limits)
        wrapped = CachedLengthPolicy(case, _shared=self._context)
        wrapped._verify()
        return wrapped

    def report(self):
        value = copy.deepcopy(self._original.report())
        value["identity"] = self.identity
        value["tokenizer_runtime"] = {"policy": POLICY, "source_pins": copy.deepcopy(self._pins),
            "tokenizer": None if self._context is None else self._context["tokenizer"].report(),
            "last_verified_custody": copy.deepcopy(self._last_custody), "backend_replaced": False,
            "use_cache": False}
        return value

    def finalize(self):
        if self._context is not None:
            self._verify()
        elif _bindings() != self._pins:
            raise ValueError("Cached runtime changed before finalization")
        # Existing finalization rehashes the native source, model, adapter and
        # original helper code. Do not replace or weaken that custody gate.
        result = copy.deepcopy(self._original.finalize())
        if self._context is not None:
            self._verify()
        result["identity"] = self.identity
        result["tokenizer_runtime"] = self.report()["tokenizer_runtime"]
        return result


def wrap_policy(original_policy):
    return CachedLengthPolicy(original_policy)


def create_policy(original_factory, *args, **kwargs):
    """Construct through the host's existing authenticated selector, lazily."""
    return wrap_policy(original_factory(*args, **kwargs))
