#!/usr/bin/env python3
"""One source-only original-producer metadata worker; never a model loader.

This new caller corrects two call sites, not the preserved 4ae source.  Every
project import compiles a source-manifest-pinned original .py file directly.
No native replay, tokenizer/model framework, network, or child is permitted.
"""
from __future__ import annotations

import hashlib
import importlib.abc
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys

ROOT = Path(__file__).absolute().parents[1]
SOURCE_SHA = "4f4fcbfcd51ff64b9674dfdde383b37337871d93f52792b3f6f9bedec6862665"
INPUTS_SHA = "3df7953c0d405364aef689b5e67b083f5fc744492159643ca5b09e418a06a388"
MODEL_SHA = "cdacbda7777568120029b671374aaf16e994f2da2a54b867a00c81ece086d6ca"
PLAN_SHA = "da26332740d587bdd946b12999fd37de73817115ed3da8983edf5004bd02abf0"
COMMIT = "4aeae795c8cb5bfc622c9943359b5b38446089b9"
TRAINER_SHA = "d6529651c031fce3fe535f7b8b9ccbbb3396125083640184f7125065b9e26725"
EVALUATION_SHA = "1f42a76f0c1127b7edd2ce171c0e238b5846941a40b1c5cd185f676b9dc5bf92"
CLI = "scripts/execute_peano_hydra_retention.py"
MAX_REQUEST = 1024**2
MAX_METADATA = 4 * 1024**2
FORBIDDEN = frozenset({"torch", "transformers", "tokenizers", "peft", "accelerate", "safetensors",
                       "tensorflow", "flax", "jax", "datasets"})
NO_WORK = {"model_weights_loaded": False, "tokenizer_loaded": False, "native_proof_work": False,
           "gpu_allocated": False, "network_work": False, "training_performed": False,
           "original_load_training_artifact_succeeded": False, "automatic_retry": False, "resume": False}


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def decode(raw, maximum):
    require(type(raw) is bytes and 0 < len(raw) <= maximum, "metadata byte bound")
    def pairs(items):
        result = {}
        for name, value in items:
            require(name not in result, "duplicate metadata field")
            result[name] = value
        return result
    def invalid(_):
        raise ValueError("non-finite JSON")
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    require(type(value) is dict, "metadata object required")
    return value


def absolute(value):
    require(type(value) is str and len(value.encode()) <= 4096 and not any(ord(x) < 32 for x in value),
            "bounded explicit path required")
    path = Path(value)
    require(path.is_absolute() and str(path) == value and ".." not in path.parts and len(path.parts) <= 64,
            "noncanonical worker path")
    return path


def read(path, maximum):
    """Stable single-link reads with held no-follow ancestor descriptors."""
    path = absolute(str(path))
    access = getattr(os, "O_PATH", os.O_RDONLY) if sys.platform == "linux" else os.O_RDONLY
    held, ancestry = [], []
    def signature(info):
        return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_nlink)
    try:
        directory = os.open(path.anchor, access | os.O_DIRECTORY | os.O_NOFOLLOW)
        held.append(directory)
        for name in path.parts[1:-1]:
            child = os.open(name, access | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            held.append(child)
            info = os.fstat(child)
            ancestry.append((directory, name, child, (info.st_dev, info.st_ino)))
            directory = child
        fd = os.open(path.name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW, dir_fd=directory)
        held.append(fd)
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 <= before.st_size <= maximum,
                "worker input is not one bounded regular file")
        pieces, total = [], 0
        while True:
            block = os.read(fd, min(1024**2, maximum + 1 - total))
            if not block:
                break
            total += len(block)
            require(total <= maximum, "worker input grew beyond cap")
            pieces.append(block)
        require(total == before.st_size and signature(before) == signature(os.fstat(fd)) ==
                signature(os.stat(path.name, dir_fd=directory, follow_symlinks=False)), "worker file changed while read")
        for parent, name, child, expected in ancestry:
            current, opened = os.stat(name, dir_fd=parent, follow_symlinks=False), os.fstat(child)
            require(stat.S_ISDIR(current.st_mode) and (current.st_dev, current.st_ino) ==
                    (opened.st_dev, opened.st_ino) == expected, "worker input ancestor changed")
        return b"".join(pieces)
    finally:
        for fd in reversed(held):
            os.close(fd)


class SourceLoader(importlib.abc.Loader):
    def __init__(self, finder, relative):
        self.finder, self.relative = finder, relative

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        raw = read(self.finder.root / self.relative, 2 * 1024**2)
        item = self.finder.files[self.relative]
        require(len(raw) == item["bytes"] and sha(raw) == item["sha256"], "original source changed before import")
        self.finder.loaded[module.__name__] = {"path": self.relative, "sha256": item["sha256"]}
        exec(compile(raw, str(self.finder.root / self.relative), "exec", dont_inherit=True), module.__dict__)
        require(read(self.finder.root / self.relative, 2 * 1024**2) == raw, "original source changed during import")


class SourceFinder(importlib.abc.MetaPathFinder):
    def __init__(self, root, files):
        self.root, self.files, self.loaded = root, files, {}

    def find_spec(self, fullname, path=None, target=None):
        first = fullname.split(".")[0]
        require(first not in FORBIDDEN, "metadata admission cannot import a model/tokenizer framework")
        relative = None
        if first in {"training", "scripts"}:
            relative = fullname.replace(".", "/")
        elif first == "peano_lab":
            relative = "peano-lab/py/" + fullname.replace(".", "/")
        if relative is not None:
            for name in (relative + "/__init__.py", relative + ".py"):
                if name in self.files:
                    return importlib.util.spec_from_file_location(fullname, self.root / name,
                        loader=SourceLoader(self, name), submodule_search_locations=
                            [str(self.root / relative)] if name.endswith("/__init__.py") else None)
            if any(name.startswith(relative + "/") for name in self.files):
                spec = importlib.machinery.ModuleSpec(fullname, loader=None, is_package=True)
                spec.submodule_search_locations = [str(self.root / relative)]
                return spec
            raise ModuleNotFoundError("unlisted preserved producer module: " + fullname)
        selected = importlib.machinery.PathFinder.find_spec(fullname, path)
        origin = getattr(selected, "origin", None)
        if origin and Path(origin).is_absolute() and Path(origin).is_relative_to(self.root):
            name = Path(origin).relative_to(self.root).as_posix()
            require(name.endswith(".py") and name in self.files, "unlisted or binary producer import")
            return importlib.util.spec_from_file_location(fullname, origin, loader=SourceLoader(self, name),
                submodule_search_locations=selected.submodule_search_locations)
        return None

    def validate_loaded(self):
        require(0 < len(self.loaded) <= 2048, "original import inventory cap")
        for name, module in tuple(sys.modules.items()):
            first = name.split(".")[0]
            require(first not in FORBIDDEN, "worker imported a forbidden framework")
            path = getattr(module, "__file__", None)
            relevant = first in {"training", "peano_lab", "scripts"}
            if path is not None and Path(path).is_absolute() and Path(path).is_relative_to(self.root):
                relevant = True
            if not relevant:
                continue
            if path is None:
                locations = list(getattr(module, "__path__", ()))
                require(locations and all(Path(value).is_relative_to(self.root) for value in locations),
                        "producer namespace escaped its actual root")
            else:
                item = self.loaded.get(name)
                require(item is not None and Path(path).absolute() == self.root / item["path"]
                        and sha(read(self.root / item["path"], 2 * 1024**2)) == item["sha256"],
                        "original import bypassed source-only bytes")
        return dict(sorted(self.loaded.items()))


def install_audit():
    attempts = []
    forbidden_os = {"os.system", "os.posix_spawn", "os.fork", "os.forkpty", "os.exec", "os.spawn",
                    "os.mkdir", "os.rmdir", "os.remove", "os.rename", "os.link", "os.symlink", "os.chmod", "os.truncate"}
    def reject(event):
        if len(attempts) < 16:
            attempts.append(event)
        raise RuntimeError("metadata admission denies " + event)
    def audit(event, args):
        if event.startswith(("socket.", "subprocess.")) or event in forbidden_os:
            reject(event)
        if event == "import" and args[0].split(".")[0] in FORBIDDEN:
            reject(event + ":" + args[0])
        if event == "ctypes.dlopen" and args and args[0] is not None:
            reject("native-library-load")
        if event == "open":
            mode, flags = args[1], args[2]
            if (type(mode) is str and any(char in mode for char in "wax+")) or (
                type(flags) is int and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)):
                reject("file-write")
    sys.addaudithook(audit)
    return attempts


def run(raw):
    request = decode(raw, MAX_REQUEST)
    require(set(request) == {"schema", "candidate_reference", "locations", "admission_sources", "execution", "limits"}
            and request["schema"] == "peano-hydra-preserved-retention-admission-request-v1"
            and canonical(request) == raw, "exact canonical admission request required")
    ref, locations, execution = request["candidate_reference"], request["locations"], request["execution"]
    expected_producer = {"schema": "peano-hydra-preserved-retention-producer-v1", "source_commit": COMMIT,
        "source_manifest_sha256": SOURCE_SHA, "inputs_sha256": INPUTS_SHA, "training_plan_sha256": PLAN_SHA,
        "trainer_sha256": TRAINER_SHA, "evaluation_source_sha256": EVALUATION_SHA}
    require(ref["schema"] == "peano-hydra-preserved-retention-artifact-reference-v1" and ref["producer"] == expected_producer
            and ref["manifest_sha256"] == MODEL_SHA and ref["admission_receipt_sha256"] is None
            and locations["admission_receipt_path"] is None and execution["source_root"] == str(ROOT)
            and execution["worker"] == str(Path(__file__).absolute()), "worker producer/caller binding changed")
    producer = locations["producer"]
    producer_root = absolute(producer["source_root"])
    source_path, input_path, model_path = (absolute(producer["source_manifest"]), absolute(producer["inputs_path"]),
                                           absolute(locations["manifest_path"]))
    require(producer_root != ROOT and model_path.name == "manifest.json"
            and input_path == producer_root / "_deploy/hydra-retention-pilot-v1/inputs.json", "original producer paths changed")
    require(sys.flags.isolated == 1 and sys.dont_write_bytecode and not any(
        name.split(".")[0] in {"training", "peano_lab", "scripts", *FORBIDDEN} for name in sys.modules),
        "worker did not start in a fresh isolated source namespace")
    source_raw, inputs_raw = read(source_path, 512 * 1024), read(input_path, MAX_METADATA)
    require(sha(source_raw) == SOURCE_SHA and sha(inputs_raw) == INPUTS_SHA, "original source/input external pin changed")
    source = decode(source_raw, 512 * 1024)
    require(source["git_commit"] == COMMIT and type(source["files"]) is dict and 1 <= len(source["files"]) <= 2048,
            "original source manifest changed")
    sources = request["admission_sources"]
    require(type(sources) is dict and 1 <= len(sources) <= 256
            and sources["scripts/authenticate_peano_hydra_retention_saved.py"] == sha(read(Path(__file__).absolute(), 2 * 1024**2)),
            "current corrected caller source pin changed")
    def support():
        for name, expected in sources.items():
            require(type(name) is str and not Path(name).is_absolute() and ".." not in Path(name).parts
                    and sha(read(ROOT / name, 2 * 1024**2)) == expected, "admission support source changed")
    support()
    attempts = install_audit()
    finder = SourceFinder(producer_root, source["files"])
    sys.meta_path.insert(0, finder)
    from training.peano_hydra import origin_bridge as original_bridge
    from training.peano_hydra import retention_training as original_training
    from training.peano_policy import manifest as artifacts
    from scripts import execute_peano_hydra_retention as original_cli
    with original_bridge._Tree(producer_root) as tree:
        original_bridge._check_sources(tree, source)
        original_inputs = original_cli.load_inputs(input_path, INPUTS_SHA)
        require(original_inputs.to_dict() == ref["training_inputs"], "caller changed the genuine producer input identity")
        # Input copies used by a future evaluator are checked by the current
        # caller; the real producer binding below always uses original inputs.
        manifest, manifest_raw = original_training._record(model_path, MODEL_SHA)
        artifacts.require_safetensors_adapter(manifest["adapter"])
        artifact_before = {name: artifacts.artifact_directory_hash(model_path.parent, name)
                           for name in ("adapter", "tokenizer")}
        require(artifact_before == {name: manifest[name] for name in artifact_before}, "saved artifact bytes differ before binding")
        input_before = input_fingerprints(original_bridge, original_inputs)
        plan = original_training.bind_training(original_inputs)
        require(plan.to_dict()["training_plan_sha256"] == PLAN_SHA
                and plan.to_dict()["training_sources"]["training/peano_hydra/retention_training.py"] == TRAINER_SHA
                and plan.to_dict()["training_sources"]["training/peano_hydra/retention_evaluation.py"] == EVALUATION_SHA,
                "genuine historical binding returned a different producer plan")
        original_training._validate_artifact_record(plan, manifest)
        artifacts.require_safetensors_adapter(manifest["adapter"])
        adapter = artifacts.verify_artifact_directory(model_path.parent, manifest["adapter"], "adapter")
        tokenizer = artifacts.verify_artifact_directory(model_path.parent, manifest["tokenizer"], "tokenizer")
        require(adapter == model_path.parent / "adapter" and tokenizer == model_path.parent / "tokenizer",
                "actual original artifact loader paths changed")
        require(original_bridge._read(model_path, MAX_METADATA) == manifest_raw,
                "model manifest changed during historical admission")
        require(original_training.training_sources() == plan.to_dict()["training_sources"],
                "original training implementation changed during historical admission")
        require(input_fingerprints(original_bridge, original_inputs) == input_before
                and read(source_path, 512 * 1024) == source_raw and read(input_path, MAX_METADATA) == inputs_raw,
                "original input bytes changed during historical admission")
        for name, ancestor in (("saved-v25", original_inputs.baseline), ("frontier-v28", original_inputs.frontier)):
            require(ancestor.load().origin == plan.to_dict()["ancestor_origins"][name], "original ancestor bytes changed")
        original_bridge._check_sources(tree, source)
        modules = finder.validate_loaded()
        support()
        require(not attempts, "worker caught a forbidden model/native/network/write/process attempt")
        contract = manifest["common_contract"]
        identity = {"schema": "peano-hydra-preserved-retention-training-identity-v1", "manifest_sha256": MODEL_SHA,
            "training_plan_sha256": PLAN_SHA, "training_inputs": original_inputs.to_dict(),
            "ancestor_origins": plan.to_dict()["ancestor_origins"], "model": manifest["model"],
            "training_authority_profile": contract["authority_profile"], "training_authority": contract["authority"],
            "training_prompt_contract": contract["prompt_contract"], "training_decoder_profile": contract["decoder_profile"],
            "artifacts": {"adapter": manifest["adapter"], "tokenizer": manifest["tokenizer"]},
            "initialization": manifest["initialization"], "job_id": manifest["reservation"]["job_id"],
            "producer": expected_producer,
            "admission_method": "original-bind-and-full-record-validation-plus-explicit-artifact-directories",
            "claim_boundary": "Preserved completed mixed SFT, admitted by corrected original-source metadata calls; no legacy origin or quality claim.",
            **original_training.CLAIMS}
        return {"schema": "peano-hydra-preserved-retention-admission-worker-v1",
            "status": "original-metadata-and-artifact-bytes-validated", "request_sha256": sha(raw),
            "producer": expected_producer, "manifest_sha256": MODEL_SHA, "training_inputs": original_inputs.to_dict(),
            "training_plan": plan.to_dict(), "checked_data": plan.checked_data.to_dict(),
            "evaluation_plan": plan.evaluation_plan, "identity": identity, "loaded_original_modules": modules,
            "checks": {name: True for name in ("original_source_before_after", "original_inputs_before_after",
                "model_bytes_before_after", "manifest_bytes_before_after", "genuine_bind_training",
                "complete_original_record_validation", "explicit_original_directory_verification",
                "original_training_sources_equal_plan", "source_only_original_imports", "no_forbidden_attempts")}, **NO_WORK}


def input_fingerprints(bridge, inputs):
    raw = bridge._read(inputs.directory / "manifest.json", MAX_METADATA)
    require(sha(raw) == inputs.manifest_sha256, "mixed preparation manifest pin changed")
    manifest = decode(raw, MAX_METADATA)
    result = {"manifest.json": sha(raw)}
    with bridge._Tree(inputs.directory) as tree:
        require(tree.inventory("", maximum=32) == {"manifest.json", *manifest["files"]}, "mixed input tree has extra files")
        for name, expected in manifest["files"].items():
            item, _ = tree.fingerprint(name, maximum=bridge.MAX_DATA_BYTES)
            require(item["bytes"] == expected["bytes"] and item["sha256"] == expected["sha256"], "mixed input byte pin changed")
            result[name] = item["sha256"]
        tree.assert_unchanged()
    for label, path, expected in (("config", inputs.config_path, inputs.config_sha256),
                                   ("evaluation-plan", inputs.evaluation_plan_path, inputs.evaluation_plan_sha256)):
        result[label] = sha(bridge._read(path, MAX_METADATA))
        require(result[label] == expected, "original config/evaluation pin changed")
    return result


def main():
    sys.dont_write_bytecode = True
    sys.pycache_prefix = "/dev/null"
    try:
        raw = sys.stdin.buffer.read(MAX_REQUEST + 1)
        result = run(raw)
        output = canonical(result) + b"\n"
        require(len(output) <= MAX_METADATA, "historical admission worker output cap")
        sys.stdout.buffer.write(output)
        sys.stdout.buffer.flush()
        return 0
    except BaseException as error:
        message = " ".join(str(error).split())[:2048]
        sys.stderr.write("preserved-retention-admission: " + type(error).__name__ + ": " + message + "\n")
        sys.stderr.flush()
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
