"""Tiny synthetic source/input receipts; no actual corpus, models or native QED.

The one worker boundary is mocked. Its saved process schema is checked by the
real stdlib supervisor validator. Source import tests execute only explicitly
authored tiny temporary Python modules, never repository theorem modules.
"""
from __future__ import annotations

import builtins
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
import hashlib
import importlib
import importlib.util
import json
import marshal
import os
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from training.peano_hydra import origin_bridge as bridge
from training.peano_hydra import review_runtime, review_sources


def write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def json_bytes(value):
    return bridge._canonical(value) + b"\n"


def source_manifest(root):
    files = {}
    with bridge._Tree(root) as tree:
        names = set(bridge._epoch_paths("v25"))
        for prefix in bridge.SOURCE_SCOPES:
            names.update(tree.inventory(prefix, maximum=bridge.MAX_SOURCE_FILES, skip_cache=True))
        for name in sorted(names):
            files[name] = tree.fingerprint(name, maximum=1024**2)[0]
    return {"schema": bridge.SOURCE_SCHEMA, "git_commit": "a" * 40,
            "scopes": list(bridge.SOURCE_SCOPES), "epoch_version": "v25", "files": files,
            "files_sha256": bridge._digest(files), "coverage": bridge.SOURCE_COVERAGE}


def process_record(command, limits, payload, stdout, *, reason="exited", returncode=0):
    return {
        "command": list(command), "limits": limits.to_dict(), "stdin_bytes": len(payload), "stdin_sha256": bridge._sha(payload),
        "reason": reason, "returncode": returncode, "stdout": stdout, "stderr": "",
        "output_encoding": "utf-8", "raw_output_base64": None, "output_truncated": False,
        "stdout_bytes": len(stdout.encode()), "stdout_sha256": bridge._sha(stdout.encode()),
        "stderr_bytes": 0, "stderr_sha256": bridge._sha(b""), "observed_descendant_count": 0,
        "resource_measurement": review_runtime.RESOURCE_MEASUREMENT,
        "resources": {"cpu_seconds": 0.01, "wall_seconds": 0.02, "peak_rss_bytes": 4096,
                      "sampled_peak_group_rss_bytes": 4096, "cpu_instructions": None, "energy_joules": None},
    }


@pytest.fixture
def bundle(tmp_path, monkeypatch):
    root, adapter_root, execution = tmp_path / "original", tmp_path / "adapter", tmp_path / "execution"
    for name in bridge.REQUIRED_SOURCE_FILES:
        write(root / name, b"# explicitly synthetic source; no native semantics\n")
    write(root / "training/peano_hydra/probe.py", b"VALUE = 'verified-source'\n")
    for name in bridge._epoch_paths("v25"):
        write(root / name, json_bytes({"meta": {"current_alpha_version": "v25"}} if name == bridge.CAMPAIGN else {}))
    source = source_manifest(root)
    source_path = root / "origin-source.json"
    write(source_path, json_bytes(source))
    for name in bridge.SUPPORT_FILES:
        write(execution / name, b"# explicit mock supervisor/bridge source identity\n")
    monkeypatch.setattr(bridge, "ROOT", execution)
    monkeypatch.setattr(bridge, "__file__", str(execution / bridge.SUPPORT_FILES[0]))
    preparation_path = root / "_deploy/original-preparation"
    source_input = "_deploy/original-source"
    source_fields = {"directory": source_input}
    for name, field in bridge.SOURCE_INPUT_FIELDS.items():
        raw = json_bytes({"synthetic": name}) if not name.endswith(".jsonl") else b""
        write(root / source_input / name, raw)
        source_fields[field] = bridge._sha(raw)
    files = {}
    for name in bridge.PREPARATION_FILES:
        raw = b"{}\n" if name in {"train.jsonl", "dev.jsonl"} else b"# fake config\n" if name == "config.toml" else b""
        write(preparation_path / name, raw)
        files[name] = {"bytes": len(raw), "sha256": bridge._sha(raw)}
        if name.endswith(".jsonl"):
            files[name]["rows"] = int(bool(raw))
    preparation = {"schema": "peano-hydra-posttrain-preparation-v1", "files": files, "source": source_fields}
    preparation_raw = json_bytes(preparation)
    write(preparation_path / "manifest.json", preparation_raw)
    groups = {}
    for kind, payloads in {
        "adapter": {"adapter_config.json": b"{}\n", "adapter_model.safetensors": b"synthetic bytes, never loaded"},
        "tokenizer": {"tokenizer.json": b"{}\n"},
    }.items():
        hashes = {}
        for name, raw in payloads.items():
            write(adapter_root / kind / name, raw)
            hashes[kind + "/" + name] = bridge._sha(raw)
        groups[kind] = {"root": kind, "files": hashes, "sha256": bridge._digest(hashes)}
    adapter = {
        "schema": "peano-hydra-posttrain-adapter-v1", "version": "v25", "run_id": "synthetic-origin",
        "model": {"model_id": "synthetic-test-base", "revision": "b" * 40},
        "epoch_sha256": "c" * 64, "edition_identity_sha256": "d" * 64, "theorem_dag_sha256": "e" * 64,
        "reviewed_definition_dag_sha256": "f" * 64,
        "preparation_manifest_sha256": bridge._sha(preparation_raw),
        "preparation": {"manifest_sha256": bridge._sha(preparation_raw), "files": files},
        "model_trained": True, "research_claim_eligible": False, "alpha_admitted": False, "sealed_benchmark": False,
        "deployment": {"source_sync": {"git_commit": "b" * 40}}, "runtime": {"synthetic": True},
        "job": {"synthetic": True}, "requirements_verification": {"synthetic": True},
        "objective": {"synthetic": True}, "trainer_runtime": {"synthetic": True},
        "finite_gradient_audit": {"synthetic": True}, "adapter_update": {"synthetic": True},
        "metrics": {"expected_optimizer_steps": 1, "actual_optimizer_steps": 1, "training_rows": 1,
                    "development_rows": 1, "train": {"train_loss": 0.5}, "dev": {"eval_loss": 0.6}},
        **groups,
    }
    adapter_raw = json_bytes(adapter)
    write(adapter_root / "manifest.json", adapter_raw)
    request = bridge.OriginRequest(root, source_path, bridge._sha(json_bytes(source)), "a" * 40,
                                   preparation_path, bridge._sha(preparation_raw), adapter_root / "manifest.json",
                                   bridge._sha(adapter_raw))
    return SimpleNamespace(root=root, adapter_root=adapter_root, execution=execution, source=source,
                           preparation=preparation, adapter=adapter, request=request)


@pytest.fixture
def mock_worker(bundle, monkeypatch):
    calls, state = [], {"reason": "exited", "returncode": 0, "mutation": None, "worker_mutation": None}
    monkeypatch.setattr(bridge, "_legacy_origin", lambda *args: pytest.fail("parent invoked native/original validators"))

    def run(command, *, cwd, limits, input_bytes, runtime_library_paths=()):
        calls.append({"command": command, "cwd": cwd, "limits": limits.to_dict(), "payload": input_bytes})
        assert runtime_library_paths == ()
        message = json.loads(input_bytes)
        plan = SimpleNamespace(
            model=bundle.adapter["model"], epoch=SimpleNamespace(**{name: bundle.adapter[name] for name in (
                "epoch_sha256", "edition_identity_sha256", "theorem_dag_sha256", "reviewed_definition_dag_sha256")}),
            preparation_manifest_sha256=bundle.request.preparation_manifest_sha256,
            trained_adapter={"manifest_sha256": bundle.request.adapter_manifest_sha256,
                             "training_evidence": bridge._training_summary(bundle.adapter)},
            authority_profile=bundle.request.authority_profile,
        )
        origin = bridge._origin_record(plan, bundle.adapter, {kind: bundle.adapter[kind] for kind in ("adapter", "tokenizer")})
        worker = {
            "schema": bridge.WORKER_SCHEMA, "status": "validated-original-origin",
            "request_sha256": bridge._digest(message["request"]),
            "source_manifest_sha256": message["request"]["source_manifest_sha256"],
            "inputs_sha256": message["inputs_sha256"], "origin": origin,
            "validation": {"module": "training.peano_hydra.evaluation",
                           "entrypoints": ["build_matched_evaluation_plan", "_verify_trained_artifacts"],
                           "held_out_sha256": "a" * 64,
                           "semantics": "unchanged original validator semantics; no additional corpus, cold-replay or inference claim"},
            "loaded_sources": {"training.peano_hydra.evaluation": {
                "path": "training/peano_hydra/evaluation.py",
                "sha256": bundle.source["files"]["training/peano_hydra/evaluation.py"]["sha256"]}},
            "model_frameworks_imported": False, "model_generation_performed": False, "proof_search_performed": False,
        }
        if state["worker_mutation"]:
            state["worker_mutation"](worker)
        if state["mutation"]:
            state["mutation"]()
        return process_record(command, limits, input_bytes, json_bytes(worker).decode() if state["reason"] == "exited" else "",
                              reason=state["reason"], returncode=state["returncode"])
    monkeypatch.setattr(review_runtime, "run_bounded", run)
    return calls, state


def authenticate(bundle):
    return bridge.authenticate_origin(bundle.request, python=Path("/usr/bin/python3"),
                                      limits=bridge.OriginLimits(cpu_seconds=2, wall_seconds=3))


def save_receipt(bundle, handle, name="receipt.json"):
    path = bundle.root.parent / name
    write(path, handle.receipt_bytes)
    return path


def reseal_worker(record):
    record["process"]["stdout"] = json_bytes(record["worker"]).decode()
    record["process"]["stdout_sha256"] = bridge._sha(record["process"]["stdout"].encode())
    record["process"]["stdout_bytes"] = len(record["process"]["stdout"].encode())


def test_bridge_import_has_no_native_or_model_side_effects(monkeypatch):
    original = builtins.__import__
    def safe(name, *args, **kwargs):
        assert name.partition(".")[0] not in {"peano_lab", "torch", "transformers", "peft", "tokenizers"}
        return original(name, *args, **kwargs)
    with monkeypatch.context() as context:
        context.setattr(builtins, "__import__", safe)
        importlib.reload(bridge)


def test_one_explicit_mock_worker_produces_detached_immutable_origin_without_git(bundle, mock_worker, monkeypatch):
    monkeypatch.setattr(review_sources, "bounded_git", lambda *args, **kwargs: pytest.fail("portable authentication consulted Git"))
    handle = authenticate(bundle)
    calls, _ = mock_worker
    assert len(calls) == 1 and calls[0]["cwd"] == bundle.root
    assert calls[0]["command"][1:5] == ("-I", "-B", "-X", "pycache_prefix=/dev/null")
    assert handle.adapter_directory == bundle.adapter_root / "adapter"
    assert handle.tokenizer_directory == bundle.adapter_root / "tokenizer"
    assert handle.origin["training_authority_profile"] is None
    assert handle.origin["training_source_commit"] == "b" * 40 != bundle.request.source_commit
    original = handle.origin
    original["model"]["model_id"] = "changed detached copy"
    assert handle.origin["model"] == bundle.adapter["model"]
    with pytest.raises(FrozenInstanceError):
        handle.validation_mode = "relabelled"


def test_generic_v4_origin_keeps_its_own_schema_prompt_and_caller_anchor(bundle, mock_worker):
    bundle.preparation.update(schema="peano-hydra-posttrain-preparation-v2", authority_profile=bridge.AUTHORITY_PROFILE)
    prepared_raw = json_bytes(bundle.preparation)
    write(bundle.request.preparation_directory / "manifest.json", prepared_raw)
    bundle.adapter.update(schema="peano-hydra-posttrain-adapter-v2", authority_profile=bridge.AUTHORITY_PROFILE,
                          prompt_contract={"synthetic_prompt_version": 4}, decoder_profile={"synthetic_decoder": True},
                          preparation_manifest_sha256=bridge._sha(prepared_raw))
    bundle.adapter["preparation"]["manifest_sha256"] = bridge._sha(prepared_raw)
    adapter_raw = json_bytes(bundle.adapter)
    write(bundle.request.adapter_manifest, adapter_raw)
    bundle.request = replace(bundle.request, preparation_manifest_sha256=bridge._sha(prepared_raw),
                             adapter_manifest_sha256=bridge._sha(adapter_raw), authority_profile=bridge.AUTHORITY_PROFILE)
    handle = authenticate(bundle)
    assert handle.origin["schema"] == "peano-hydra-posttrain-adapter-v2"
    assert handle.origin["training_authority_profile"] == bridge.AUTHORITY_PROFILE
    assert handle.origin["training_prompt_contract"] == bundle.adapter["prompt_contract"]
    assert handle.origin["adapter_manifest_sha256"] == bundle.request.adapter_manifest_sha256
    assert len(mock_worker[0]) == 1


@pytest.mark.parametrize("profile", [None, bridge.AUTHORITY_PROFILE])
def test_worker_wrapper_calls_unchanged_original_apis_with_original_profile(bundle, monkeypatch, profile):
    import training.peano_hydra as package
    request = replace(bundle.request, authority_profile=profile)
    calls = []
    plan = SimpleNamespace(
        model=bundle.adapter["model"], epoch=SimpleNamespace(**{name: bundle.adapter[name] for name in (
            "epoch_sha256", "edition_identity_sha256", "theorem_dag_sha256", "reviewed_definition_dag_sha256")}),
        preparation_manifest_sha256=request.preparation_manifest_sha256,
        trained_adapter={"manifest_sha256": request.adapter_manifest_sha256,
                         "training_evidence": bridge._training_summary(bundle.adapter)},
        authority_profile=profile, held_out={"synthetic_old_holdout": True},
    )
    def build(*args, **kwargs):
        calls.append((args, kwargs))
        return plan
    def artifacts(value):
        assert value is plan
        calls.append("exact original artifact verifier")
        return bundle.adapter_root / "adapter", bundle.adapter_root / "tokenizer", {
            kind: bundle.adapter[kind] for kind in ("adapter", "tokenizer")}
    monkeypatch.setattr(package, "evaluation", SimpleNamespace(build_matched_evaluation_plan=build,
                       _verify_trained_artifacts=artifacts, _digest=bridge._digest), raising=False)
    origin, summary = bridge._legacy_origin(request, bundle.adapter)
    assert calls == [((request.preparation_directory,), {"trained_adapter": request.adapter_manifest,
        "repository_root": request.source_root, "authority_profile": profile}), "exact original artifact verifier"]
    assert origin["training_authority_profile"] == profile
    assert summary["held_out_sha256"] == bridge._digest(plan.held_out)


def test_external_anchored_cached_load_performs_no_worker_or_original_validator(bundle, mock_worker, monkeypatch):
    handle = authenticate(bundle)
    path = save_receipt(bundle, handle)
    monkeypatch.setattr(review_runtime, "run_bounded", lambda *args, **kwargs: pytest.fail("cached receipt triggered a child"))
    loaded = bridge.load_origin_receipt(path, expected_receipt_sha256=handle.receipt_sha256, request=bundle.request)
    assert loaded.origin == handle.origin and loaded.receipt_bytes == handle.receipt_bytes
    assert loaded.validation_mode == "externally-anchored-byte-recheck-no-replay"


@pytest.mark.parametrize("expected", [None, "", "f" * 64])
def test_cached_receipt_requires_external_raw_sha_before_original_inputs(bundle, mock_worker, monkeypatch, expected):
    handle = authenticate(bundle)
    path = save_receipt(bundle, handle)
    monkeypatch.setattr(bridge, "_check_sources", lambda *args: pytest.fail("bad receipt anchor reached source/input checks"))
    with pytest.raises(bridge.OriginBridgeError):
        bridge.load_origin_receipt(path, expected_receipt_sha256=expected, request=bundle.request)


def test_relocation_preserves_portable_origin_without_using_historical_paths(bundle, mock_worker, monkeypatch):
    handle = authenticate(bundle)
    path = save_receipt(bundle, handle)
    relocated = bundle.root.with_name("relocated-source")
    relocated_adapter = bundle.adapter_root.with_name("relocated-adapter")
    shutil.copytree(bundle.root, relocated)
    shutil.copytree(bundle.adapter_root, relocated_adapter)
    request = replace(bundle.request, source_root=relocated, source_manifest=relocated / bundle.request.source_manifest.name,
                      preparation_directory=relocated / bundle.request.to_dict()["preparation_relative_path"],
                      adapter_manifest=relocated_adapter / "manifest.json")
    assert request.to_dict() == bundle.request.to_dict() and request.locations() != bundle.request.locations()
    bundle.root.rename(bundle.root.with_name("historical-source-no-longer-at-saved-path"))
    bundle.adapter_root.rename(bundle.adapter_root.with_name("historical-adapter-no-longer-at-saved-path"))
    monkeypatch.setattr(review_runtime, "run_bounded", lambda *args, **kwargs: pytest.fail("relocation executed historical command"))
    loaded = bridge.load_origin_receipt(path, expected_receipt_sha256=handle.receipt_sha256, request=request)
    assert loaded.origin == handle.origin
    assert loaded.adapter_directory == relocated_adapter / "adapter"


@pytest.mark.parametrize("change", ["source_commit", "prep-relative", "prep-sha", "adapter-sha", "authority"])
def test_foreign_request_never_reuses_receipt(bundle, mock_worker, change):
    handle = authenticate(bundle)
    path = save_receipt(bundle, handle)
    changes = {
        "source_commit": {"source_commit": "b" * 40},
        "prep-relative": {"preparation_directory": bundle.root / "_deploy/foreign"},
        "prep-sha": {"preparation_manifest_sha256": "a" * 64},
        "adapter-sha": {"adapter_manifest_sha256": "a" * 64},
        "authority": {"authority_profile": bridge.AUTHORITY_PROFILE},
    }[change]
    with pytest.raises((bridge.OriginBridgeError, OSError)):
        bridge.load_origin_receipt(path, expected_receipt_sha256=handle.receipt_sha256, request=replace(bundle.request, **changes))


@pytest.mark.parametrize("name", ["training/peano_hydra/evaluation.py", "peano-lab/py/peano_lab/engine/rewrite.py",
                                  "_deploy/original-preparation/train.jsonl", "_deploy/original-source/sft.jsonl"])
def test_changed_original_source_or_data_rejects_before_child(bundle, mock_worker, name):
    (bundle.root / name).write_bytes(b"changed")
    with pytest.raises(bridge.OriginBridgeError):
        authenticate(bundle)
    assert mock_worker[0] == []


@pytest.mark.parametrize("kind", ["adapter", "tokenizer", "extra", "pickle"])
def test_original_model_artifact_bytes_and_closed_inventory_reject_before_child(bundle, mock_worker, kind):
    if kind in {"adapter", "tokenizer"}:
        name = "adapter/adapter_model.safetensors" if kind == "adapter" else "tokenizer/tokenizer.json"
        (bundle.adapter_root / name).write_bytes(b"mutated")
    else:
        write(bundle.adapter_root / "adapter" / ("foreign.json" if kind == "extra" else "adapter_model.bin"), b"untrusted")
    with pytest.raises(bridge.OriginBridgeError):
        authenticate(bundle)
    assert mock_worker[0] == []


@pytest.mark.parametrize("kind", ["source", "data", "adapter", "support", "root"])
def test_mutation_during_mock_worker_is_rejected_before_handle(bundle, mock_worker, kind):
    _, state = mock_worker
    if kind == "root":
        def change():
            original = bundle.root.with_name("moved-source")
            bundle.root.rename(original)
            shutil.copytree(original, bundle.root)
        state["mutation"] = change
    else:
        path = {"source": bundle.root / "training/peano_hydra/evaluation.py",
                "data": bundle.request.preparation_directory / "train.jsonl",
                "adapter": bundle.adapter_root / "adapter/adapter_model.safetensors",
                "support": bundle.execution / bridge.SUPPORT_FILES[0]}[kind]
        state["mutation"] = lambda: path.write_bytes(b"mutated during bounded child")
    with pytest.raises(bridge.OriginBridgeError):
        authenticate(bundle)
    assert len(mock_worker[0]) == 1


def test_incomplete_worker_never_produces_handle_or_automatic_retry(bundle, mock_worker):
    mock_worker[1].update(reason="cpu_limit", returncode=-24)
    with pytest.raises(bridge.OriginBridgeError, match="did not complete") as error:
        authenticate(bundle)
    assert len(mock_worker[0]) == 1
    assert error.value.observation["process"]["reason"] == "cpu_limit"


@pytest.mark.parametrize("kind", ["counts", "loss", "gradient", "nested-claim", "origin-profile", "loaded-module",
                                  "extra-worker", "generation", "descendant", "boolean-limit", "foreign-argv"])
def test_resealed_receipt_metadata_tampering_still_fails_exact_joins(bundle, mock_worker, kind):
    handle = authenticate(bundle)
    record = json.loads(handle.receipt_bytes)
    origin = record["worker"]["origin"]
    if kind == "counts":
        origin["training_evidence"]["actual_optimizer_steps"] += 1
    elif kind == "loss":
        origin["training_evidence"]["train_metrics"]["train_loss"] = 0.001
    elif kind == "gradient":
        origin["training_evidence"]["finite_gradient_audit_sha256"] = "0" * 64
    elif kind == "nested-claim":
        origin["training_evidence"]["research_claim_eligible"] = True
    elif kind == "origin-profile":
        origin["training_authority_profile"] = bridge.AUTHORITY_PROFILE
    elif kind == "loaded-module":
        item = record["worker"]["loaded_sources"]["training.peano_hydra.evaluation"]
        item["path"] = "peano-lab/py/peano_lab/engine/rewrite.py"
        item["sha256"] = bundle.source["files"][item["path"]]["sha256"]
    elif kind == "extra-worker":
        record["worker"]["inference_authorized"] = True
    elif kind == "generation":
        record["worker"]["model_generation_performed"] = True
    elif kind == "descendant":
        record["process"]["observed_descendant_count"] = 1
    elif kind == "boolean-limit":
        record["limits"]["cpu_seconds"] = True
    elif kind == "foreign-argv":
        record["process"]["command"][-1] = "--execute-models"
    origin["origin_sha256"] = bridge._digest({key: value for key, value in origin.items() if key != "origin_sha256"})
    reseal_worker(record)
    raw = json_bytes(record)
    path = bundle.root.parent / (kind + ".json")
    write(path, raw)
    with pytest.raises(ValueError):
        bridge.load_origin_receipt(path, expected_receipt_sha256=bridge._sha(raw), request=bundle.request)


def test_source_only_loader_ignores_poisoned_bytecode(bundle):
    name = "training/peano_hydra/probe.py"
    source_path = bundle.root / name
    # Deliberately create the ordinary cache location, not the disabled
    # /dev/null prefix used by this bounded test process itself.
    cache = source_path.parent / "__pycache__" / (source_path.stem + "." + sys.implementation.cache_tag + ".pyc")
    info = source_path.stat()
    header = (importlib.util.MAGIC_NUMBER + b"\0" * 4 + (int(info.st_mtime) & 0xffffffff).to_bytes(4, "little")
              + info.st_size.to_bytes(4, "little"))
    poisoned = header + marshal.dumps(compile("VALUE = 'poisoned-bytecode'", str(source_path), "exec"))
    write(cache, poisoned)
    with bridge._Tree(bundle.root) as tree:
        bridge._check_sources(tree, bundle.source)
        finder = bridge._SourceFinder(tree, bundle.source["files"])
        spec = finder.find_spec("training.peano_hydra.probe")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.VALUE == "verified-source"
        assert finder.loaded["training.peano_hydra.probe"]["sha256"] == bundle.source["files"][name]["sha256"]


def test_source_mutation_during_import_is_rejected(bundle):
    name = "training/peano_hydra/probe.py"
    write(bundle.root / name, b"from pathlib import Path\nPath(__file__).write_bytes(b'# changed during import\\n')\n")
    source = source_manifest(bundle.root)
    with bridge._Tree(bundle.root) as tree:
        bridge._check_sources(tree, source)
        finder = bridge._SourceFinder(tree, source["files"])
        spec = finder.find_spec("training.peano_hydra.probe")
        with pytest.raises(bridge.OriginBridgeError, match="identity changed"):
            spec.loader.exec_module(importlib.util.module_from_spec(spec))


@pytest.mark.parametrize("name", ["torch", "transformers", "peft", "tokenizers", "training.foreign", "peano_lab.foreign"])
def test_source_finder_rejects_model_and_unlisted_project_imports(bundle, name):
    with bridge._Tree(bundle.root) as tree:
        finder = bridge._SourceFinder(tree, bundle.source["files"])
        with pytest.raises((bridge.OriginBridgeError, ModuleNotFoundError)):
            finder.find_spec(name)


@pytest.mark.parametrize("name", ["training/__init__.py", "training.py", "scripts/unlisted.py"])
def test_source_bundle_does_not_ignore_new_importable_files(bundle, name):
    write(bundle.root / name, b"raise RuntimeError('unlisted')\n")
    with bridge._Tree(bundle.root) as tree, pytest.raises(bridge.OriginBridgeError):
        bridge._check_sources(tree, bundle.source)


@pytest.mark.parametrize("kind", ["leaf", "ancestor", "hardlink", "fifo", "oversized"])
def test_nofollow_regular_single_link_and_byte_boundaries(tmp_path, kind):
    parent = tmp_path / "parent"
    source = parent / "source.py"
    write(source, b"# bounded\n")
    if kind == "leaf":
        alias = parent / "alias.py"
        alias.symlink_to(source)
        action = lambda: bridge._read(alias, 1024)
    elif kind == "ancestor":
        alias = tmp_path / "alias-parent"
        alias.symlink_to(parent, target_is_directory=True)
        action = lambda: bridge._read(alias / source.name, 1024)
    elif kind == "hardlink":
        os.link(source, parent / "hard.py")
        action = lambda: bridge._read(source, 1024)
    elif kind == "fifo":
        fifo = parent / "fifo"
        os.mkfifo(fifo)
        action = lambda: bridge._read(fifo, 1024)
    else:
        action = lambda: bridge._read(source, 1)
    with pytest.raises((bridge.OriginBridgeError, OSError)):
        action()


def test_replaced_ancestor_is_detected_even_with_identical_leaf_bytes(tmp_path):
    parent = tmp_path / "parent"
    root = parent / "source"
    write(root / "tiny.py", b"VALUE = 1\n")
    with bridge._Tree(root) as tree:
        tree.read("tiny.py", 1024)
        parent.rename(tmp_path / "moved-parent")
        shutil.copytree(tmp_path / "moved-parent", parent)
        with pytest.raises(bridge.OriginBridgeError, match="ancestor"):
            tree.assert_unchanged()


def test_directory_quota_is_rechecked_after_recursive_parent_creation(tmp_path, monkeypatch):
    (tmp_path / "a/b/c").mkdir(parents=True)
    monkeypatch.setattr(bridge, "MAX_DIRECTORIES", 3)
    with bridge._Tree(tmp_path) as tree:
        with pytest.raises(bridge.OriginBridgeError, match="directory inventory"):
            tree.directory("a/b/c")
        assert len(tree.directories) == 3


@pytest.mark.parametrize("raw", [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e999}',
                                 b'{"x":' + b'9' * 65 + b'}', b'{"x":'])
def test_bounded_json_rejects_duplicate_nonfinite_giant_and_truncated_records(raw):
    with pytest.raises(bridge.OriginBridgeError):
        bridge._decode(raw, 1024, "test")


@pytest.mark.parametrize("field,value", [("source_root", Path("/safe/../elsewhere")),
    ("source_manifest_sha256", "unanchored"), ("source_commit", "HEAD"), ("authority_profile", "new-profile"),
    ("preparation_directory", Path("/foreign/preparation")), ("adapter_manifest", Path("/adapter/other.json"))])
def test_requests_reject_unsafe_or_ambiguous_original_identities(bundle, field, value):
    with pytest.raises(bridge.OriginBridgeError):
        replace(bundle.request, **{field: value})


def test_git_manifest_mint_requires_real_expected_blob_and_closed_inventory(bundle, monkeypatch):
    campaign = (bundle.root / bridge.CAMPAIGN).read_bytes()
    rows = b"".join(f'{item["mode"]} blob {item["git_blob"]}\t{name}\0'.encode()
                    for name, item in bundle.source["files"].items())
    calls = []
    def git(root, *args, maximum):
        assert root == bundle.root
        calls.append(args)
        if args[:2] == ("cat-file", "-t"):
            return b"commit\n"
        if args[:2] == ("rev-parse", "--verify"):
            return b"a" * 40 + b"\n"
        if args[:2] == ("cat-file", "blob"):
            return campaign
        assert args[0] == "ls-tree"
        return rows
    monkeypatch.setattr(review_sources, "bounded_git", git)
    frozen = bridge.freeze_origin_sources(bundle.root, expected_commit="a" * 40)
    assert json.loads(frozen) == bundle.source
    assert any(args[0] == "ls-tree" for args in calls)
    (bundle.root / "peano-lab/py/peano_lab/engine/rewrite.py").write_bytes(b"different optimized engine")
    with pytest.raises(bridge.OriginBridgeError, match="Git blob"):
        bridge.freeze_origin_sources(bundle.root, expected_commit="a" * 40)


def test_execution_binding_is_separate_portable_and_drift_sensitive(bundle, mock_worker):
    handle = authenticate(bundle)
    rewrite = "peano-lab/py/peano_lab/engine/rewrite.py"
    write(bundle.execution / rewrite, b"# new bounded engine\n")
    files = {name: bridge._sha((bundle.execution / name).read_bytes()) for name in (bridge.SUPPORT_FILES[0], rewrite)}
    contract = {"primitive_authority": "synthetic-test", "model_calls_per_goal": 8}
    first = bridge.execution_binding(source_root=bundle.execution, source_files=files, contract=contract)
    other = bundle.execution.with_name("portable-execution")
    shutil.copytree(bundle.execution, other)
    assert bridge.execution_binding(source_root=other, source_files=files, contract=contract) == first
    assert str(bundle.execution) not in json.dumps(first)
    assert first["old_checkpoint_resume_allowed"] is False and first["training_origins_relabelled"] is False
    before = handle.origin
    (other / rewrite).write_bytes(b"# separately changed optimized engine\n")
    with pytest.raises(bridge.OriginBridgeError, match="execution source changed"):
        bridge.execution_binding(source_root=other, source_files=files, contract=contract)
    files[rewrite] = bridge._sha((other / rewrite).read_bytes())
    second = bridge.execution_binding(source_root=other, source_files=files, contract=contract)
    assert second["execution_binding_sha256"] != first["execution_binding_sha256"] and handle.origin == before


@pytest.mark.parametrize("values", [{"cpu_seconds": 121}, {"wall_seconds": 181}, {"rss_bytes": 2 * 1024**3},
                                    {"output_bytes": 3 * 1024**2}, {"cpu_seconds": True}, {"wall_seconds": 1}])
def test_origin_resource_defaults_cannot_silently_expand(values):
    with pytest.raises(bridge.OriginBridgeError):
        replace(bridge.ORIGIN_LIMITS, **values).to_dict()
