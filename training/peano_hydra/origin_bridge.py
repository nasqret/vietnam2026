"""Keep authenticated original training separate from a new execution engine.

Only ``authenticate_origin`` runs original validators, in one explicitly bounded
fresh child. Imports, source-manifest creation, receipt loading, and execution
binding never import the native library, a tokenizer, or a model framework.
An anchored receipt rechecks bytes; it does NOT repeat native verification.

The portable source manifest is minted locally against real caller-pinned Git
objects. A separately staged, .git-free copy can use its externally pinned raw
SHA256. Neither an asserted commit nor a self-resealed receipt is an anchor.
Preparation/source locations remain their original repository-relative paths;
adapter and source-bundle physical locations can change without relabelling an
origin. This module never copies inputs, writes receipts, admits training,
resumes a checkpoint, or establishes historical inference/hardware attestation.
"""
from __future__ import annotations

from contextlib import ExitStack
from dataclasses import dataclass
import hashlib
import importlib.abc
import importlib.machinery
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import resource
import stat
import sys
from typing import Mapping


ROOT = Path(__file__).absolute().parents[2]
SOURCE_SCHEMA = "peano-hydra-origin-source-bundle-v1"
REQUEST_SCHEMA = "peano-hydra-preserved-origin-request-v1"
WORKER_SCHEMA = "peano-hydra-preserved-origin-worker-v1"
RECEIPT_SCHEMA = "peano-hydra-preserved-origin-receipt-v1"
EXECUTION_SCHEMA = "peano-hydra-origin-execution-binding-v1"
AUTHORITY_PROFILE = "peano-authority-primitive-v1"
SOURCE_SCOPES = ("training/peano_hydra", "training/peano_policy", "peano-lab/py/peano_lab", "scripts")
CAMPAIGN = "book/_static/constructive-grand-campaign/campaign.json"
DEFINITIONS = "book/_static/constructive-grand-campaign/definitions.json"
STABLE_CATALOG = "artifacts/peano-library/catalog-v1.json"
SOURCE_COVERAGE = "Complete listed code scopes and five selected epoch artifacts, joined to pinned Git blobs; not whole-repository or runtime attestation"
REQUIRED_SOURCE_FILES = frozenset({
    "training/peano_hydra/__init__.py", "training/peano_hydra/evaluation.py",
    "training/peano_hydra/posttrain.py", "training/peano_hydra/epoch.py",
    "training/peano_policy/__init__.py", "training/peano_policy/manifest.py",
    "peano-lab/py/peano_lab/__init__.py", "peano-lab/py/peano_lab/engine/rewrite.py",
    "peano-lab/py/peano_lab/kernel/checker.py", "scripts/hydra_bounded_exec.py",
})
SUPPORT_FILES = ("training/peano_hydra/origin_bridge.py", "training/peano_hydra/review_runtime.py",
                 "scripts/hydra_bounded_exec.py")
PREPARATION_FILES = frozenset({"config.toml", "train.jsonl", "dev.jsonl", "quarantine.jsonl",
                               "preferences.jsonl", "discovery.jsonl"})
SOURCE_INPUT_FIELDS = {"epoch.json": "epoch_file_sha256", "manifest.json": "manifest_sha256",
                       "sft.jsonl": "sft_sha256", "preferences.jsonl": "preferences_sha256",
                       "discovery.jsonl": "discovery_sha256"}
MAX_SOURCE_FILES = 2048
MAX_SOURCE_ENTRIES = 8192
MAX_DIRECTORIES = 1024
MAX_SOURCE_TOTAL_BYTES = 128 * 1024**2
MAX_SOURCE_FILE_BYTES = 64 * 1024**2
MAX_PYTHON_BYTES = 2 * 1024**2
MAX_MANIFEST_BYTES = 4 * 1024**2
MAX_DATA_BYTES = 64 * 1024**2
MAX_ARTIFACT_BYTES = 512 * 1024**2
MAX_INPUT_TOTAL_BYTES = 512 * 1024**2
MAX_BUNDLE_MANIFEST_BYTES = 512 * 1024
MAX_REQUEST_BYTES = 1024**2
MAX_RECEIPT_BYTES = 4 * 1024**2
MAX_EXECUTION_FILES = 256
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_OID = re.compile(r"[0-9a-f]{40}\Z")
_VERSION = re.compile(r"v[1-9][0-9]{0,3}\Z")
_MODEL_IMPORTS = frozenset({"torch", "transformers", "peft", "tokenizers"})
_UNSAFE_WEIGHTS = frozenset({".bin", ".pkl", ".pickle", ".pt", ".pth"})


class OriginBridgeError(ValueError):
    """A requested origin was not authenticated; observation is never success."""
    def __init__(self, message: str, *, observation: dict | None = None):
        super().__init__(message)
        self.observation = observation


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise OriginBridgeError(message)


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                          allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as error:
        raise OriginBridgeError("bridge evidence is not strict bounded JSON") from error


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _keys(value: object, names: set[str], label: str) -> None:
    _require(type(value) is dict and set(value) == names, f"{label} fields differ")


def _hash(value: object, label: str) -> str:
    _require(type(value) is str and _SHA.fullmatch(value) is not None, f"{label} must be an external SHA256")
    return value


def _integer(value: object, maximum: int, label: str, minimum: int = 0) -> int:
    _require(type(value) is int and minimum <= value <= maximum, f"{label} exceeds its integer bound")
    return value


def _decode(raw: bytes, maximum: int, label: str) -> dict:
    _require(type(raw) is bytes and 0 < len(raw) <= maximum, f"{label} exceeds its byte bound")
    def pairs(items):
        result = {}
        for name, value in items:
            _require(name not in result, f"duplicate {label} JSON field")
            result[name] = value
        return result
    def invalid(value):
        raise OriginBridgeError(f"non-finite {label} JSON")
    def integer(text):
        _require(len(text) <= 64, f"oversized {label} integer")
        return int(text)
    def floating(text):
        _require(len(text) <= 64, f"oversized {label} number")
        value = float(text)
        _require(math.isfinite(value), f"non-finite {label} number")
        return value
    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid, parse_int=integer, parse_float=floating)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise OriginBridgeError(f"invalid {label} JSON") from error
    _require(type(value) is dict, f"{label} must be a JSON object")
    return value


def _relative(value: object) -> str:
    _require(type(value) is str and 0 < len(value.encode("utf-8")) <= 1024,
             "path must be a bounded relative POSIX string")
    parts = value.split("/")
    _require(len(parts) <= 64 and all(part not in {"", ".", ".."} for part in parts)
             and not PurePosixPath(value).is_absolute() and "\\" not in value
             and not any(ord(char) < 32 or ord(char) == 127 for char in value), "unsafe relative path")
    return value


def _absolute(value: Path) -> Path:
    _require(isinstance(value, Path), "location must be an explicit Path")
    path = value.absolute()
    _require(".." not in path.parts and len(path.parts) <= 64 and len(str(path).encode()) <= 4096
             and not any(ord(char) < 32 or ord(char) == 127 for char in str(path)), "unsafe absolute location")
    return path


def _signature(info) -> tuple:
    return (info.st_dev, info.st_ino, info.st_size, info.st_nlink, info.st_mtime_ns, info.st_ctime_ns)


class _Tree:
    """Held no-follow root/ancestor descriptors and stable bounded file reads."""
    def __init__(self, root: Path):
        self.root = _absolute(root)
        self.directories: dict[str, int] = {}
        self.ancestry: list[tuple[int, str, int, tuple[int, int]]] = []
        self.signatures: dict[str, tuple] = {}
        self._fds: list[int] = []
        access = getattr(os, "O_PATH", os.O_RDONLY) if sys.platform == "linux" else os.O_RDONLY
        try:
            descriptor = os.open(self.root.anchor, access | os.O_DIRECTORY | os.O_NOFOLLOW)
            self._fds.append(descriptor)
            for index, part in enumerate(self.root.parts[1:], 1):
                flags = os.O_RDONLY if index == len(self.root.parts) - 1 else access
                child = os.open(part, flags | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
                self._fds.append(child)
                info = os.fstat(child)
                self.ancestry.append((descriptor, part, child, (info.st_dev, info.st_ino)))
                descriptor = child
            if len(self.root.parts) == 1:
                descriptor = os.open(".", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
                self._fds.append(descriptor)
            self.directories[""] = descriptor
        except BaseException:
            self.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        for descriptor in reversed(self._fds):
            os.close(descriptor)
        self._fds.clear()

    def directory(self, relative: str = "") -> int:
        if relative in self.directories:
            return self.directories[relative]
        relative = _relative(relative)
        parent, _, name = relative.rpartition("/")
        parent_fd = self.directory(parent)
        _require(len(self.directories) < MAX_DIRECTORIES, "directory inventory exceeds its bound")
        child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
        self._fds.append(child)
        info = os.fstat(child)
        self.ancestry.append((parent_fd, name, child, (info.st_dev, info.st_ino)))
        self.directories[relative] = child
        return child

    def assert_unchanged(self) -> None:
        for parent, name, child, expected in self.ancestry:
            current = os.stat(name, dir_fd=parent, follow_symlinks=False)
            opened = os.fstat(child)
            _require(stat.S_ISDIR(current.st_mode) and current.st_nlink > 0 and opened.st_nlink > 0
                     and (current.st_dev, current.st_ino) == (opened.st_dev, opened.st_ino) == expected,
                     "root or ancestor directory changed")
        for relative, signature in self.signatures.items():
            parent, _, name = relative.rpartition("/")
            info = os.stat(name, dir_fd=self.directory(parent), follow_symlinks=False)
            _require(stat.S_ISREG(info.st_mode) and _signature(info) == signature,
                     f"input identity changed: {relative}")

    def fingerprint(self, relative: str, *, maximum: int, retain: bool = False) -> tuple[dict, bytes | None]:
        relative = _relative(relative)
        parent, _, name = relative.rpartition("/")
        parent_fd = self.directory(parent)
        descriptor = os.open(name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW, dir_fd=parent_fd)
        chunks, total, sha = [], 0, hashlib.sha256()
        try:
            before = os.fstat(descriptor)
            _require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 <= before.st_size <= maximum,
                     f"not a bounded single-link regular file: {relative}")
            baseline = self.signatures.setdefault(relative, _signature(before))
            _require(baseline == _signature(before), f"input changed before read: {relative}")
            blob = hashlib.sha1(b"blob " + str(before.st_size).encode("ascii") + b"\0")
            while True:
                chunk = os.read(descriptor, min(1024**2, maximum + 1 - total))
                if not chunk:
                    break
                total += len(chunk)
                _require(total <= maximum, "input grew beyond its byte bound")
                sha.update(chunk)
                blob.update(chunk)
                if retain:
                    chunks.append(chunk)
            after = os.fstat(descriptor)
            current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            _require(total == before.st_size and _signature(after) == _signature(current) == baseline,
                     f"input changed while read: {relative}")
            return {"bytes": total, "sha256": sha.hexdigest(), "git_blob": blob.hexdigest(),
                    "mode": "100755" if before.st_mode & 0o111 else "100644"}, b"".join(chunks) if retain else None
        finally:
            os.close(descriptor)

    def read(self, relative: str, maximum: int) -> bytes:
        return self.fingerprint(relative, maximum=maximum, retain=True)[1]

    def inventory(self, relative: str, *, maximum: int, skip_cache: bool = False) -> set[str]:
        result, entries = set(), 0
        def visit(name, depth):
            nonlocal entries
            _require(depth <= 16, "inventory depth exceeds its bound")
            descriptor = self.directory(name)
            with os.scandir(descriptor) as stream:
                for entry in stream:
                    entries += 1
                    _require(entries <= MAX_SOURCE_ENTRIES and len(entry.name.encode()) <= 256,
                             "directory entry inventory exceeds its bound")
                    child = name + "/" + entry.name if name else entry.name
                    info = entry.stat(follow_symlinks=False)
                    _require(not stat.S_ISLNK(info.st_mode), "inventory contains a symlink")
                    if stat.S_ISDIR(info.st_mode):
                        if skip_cache and entry.name == "__pycache__":
                            continue
                        visit(child, depth + 1)
                    else:
                        _require(stat.S_ISREG(info.st_mode), "inventory contains a nonregular entry")
                        result.add(_relative(child))
                        _require(len(result) <= maximum, "file inventory exceeds its bound")
        visit(relative, 0)
        return result


def _read(path: Path, maximum: int) -> bytes:
    path = _absolute(path)
    with _Tree(path.parent) as tree:
        raw = tree.read(path.name, maximum)
        tree.assert_unchanged()
        return raw


def _epoch_paths(version: str) -> tuple[str, ...]:
    _require(type(version) is str and _VERSION.fullmatch(version) is not None, "unsafe frozen edition")
    return (CAMPAIGN, DEFINITIONS, STABLE_CATALOG, f"artifacts/peano-library/channels-{version}.json",
            f"artifacts/peano-library/alpha/catalog-{version}.json")


def _source_record(record: dict) -> dict:
    _keys(record, {"schema", "git_commit", "scopes", "epoch_version", "files", "files_sha256", "coverage"}, "source manifest")
    _require(record["schema"] == SOURCE_SCHEMA and type(record["git_commit"]) is str
             and _OID.fullmatch(record["git_commit"]) is not None
             and record["scopes"] == list(SOURCE_SCOPES) and record["coverage"] == SOURCE_COVERAGE,
             "source manifest contract differs")
    paths = set(_epoch_paths(record["epoch_version"]))
    files = record["files"]
    _require(type(files) is dict and 1 <= len(files) <= MAX_SOURCE_FILES and REQUIRED_SOURCE_FILES <= files.keys()
             and paths <= files.keys() and record["files_sha256"] == _digest(files), "source manifest inventory differs")
    total = 0
    for name, item in files.items():
        name = _relative(name)
        _require(name in paths or any(name.startswith(prefix + "/") for prefix in SOURCE_SCOPES),
                 "source manifest exceeds its declared scopes")
        _keys(item, {"bytes", "sha256", "git_blob", "mode"}, "source file")
        total += _integer(item["bytes"], MAX_PYTHON_BYTES if name.endswith(".py") else MAX_SOURCE_FILE_BYTES, "source bytes")
        _hash(item["sha256"], "source file SHA")
        _require(type(item["git_blob"]) is str and _OID.fullmatch(item["git_blob"]) is not None
                 and item["mode"] in {"100644", "100755"}, "source Git identity differs")
    _require(total <= MAX_SOURCE_TOTAL_BYTES, "source inventory exceeds total byte bound")
    return files


def _check_sources(tree: _Tree, record: dict) -> None:
    files = _source_record(record)
    # The compatible implementation uses a namespace parent. Do not ignore a
    # newly introduced initializer that ordinary imports would execute.
    for name in ("training.py", "training/__init__.py"):
        parent, _, leaf = name.rpartition("/")
        try:
            os.stat(leaf, dir_fd=tree.directory(parent), follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise OriginBridgeError("original training namespace acquired an unlisted initializer")
    for prefix in SOURCE_SCOPES:
        expected = {name for name in files if name.startswith(prefix + "/")}
        _require(tree.inventory(prefix, maximum=MAX_SOURCE_FILES, skip_cache=True) == expected,
                 f"closed source inventory differs: {prefix}")
    for name, expected in files.items():
        actual, _ = tree.fingerprint(name, maximum=expected["bytes"])
        _require(actual == expected, f"source differs from pinned original bytes: {name}")
    tree.assert_unchanged()


def freeze_origin_sources(source_root: Path, *, expected_commit: str) -> bytes:
    """Mint a portable source manifest from real Git objects; never write/copy."""
    from .review_sources import bounded_git
    root = _absolute(source_root)
    _require(type(expected_commit) is str and _OID.fullmatch(expected_commit) is not None, "expected source commit is invalid")
    _require(bounded_git(root, "cat-file", "-t", expected_commit, maximum=32) == b"commit\n",
             "source anchor is not a real Git commit")
    _require(bounded_git(root, "rev-parse", "--verify", "HEAD", maximum=80) == (expected_commit + "\n").encode(),
             "source checkout is not at its explicitly pinned commit")
    campaign = bounded_git(root, "cat-file", "blob", f"{expected_commit}:{CAMPAIGN}", maximum=8 * 1024**2)
    version = _decode(campaign, 8 * 1024**2, "historical campaign").get("meta", {}).get("current_alpha_version")
    epoch_paths = _epoch_paths(version)
    raw = bounded_git(root, "ls-tree", "-r", "-z", expected_commit, "--", *SOURCE_SCOPES, *epoch_paths,
                      maximum=2 * 1024**2)
    _require(raw.endswith(b"\0"), "historical source inventory is incomplete")
    entries = raw[:-1].split(b"\0")
    _require(len(entries) <= MAX_SOURCE_FILES, "historical source inventory exceeds its bound")
    files, total = {}, 0
    with _Tree(root) as tree:
        for entry in entries:
            try:
                metadata, path = entry.split(b"\t", 1)
                mode, kind, blob = metadata.decode("ascii").split()
                name = _relative(path.decode("utf-8"))
            except (ValueError, UnicodeError) as error:
                raise OriginBridgeError("malformed historical source entry") from error
            _require(mode in {"100644", "100755"} and kind == "blob" and _OID.fullmatch(blob) is not None
                     and name not in files, "nonregular or repeated historical source entry")
            maximum = min(MAX_PYTHON_BYTES if name.endswith(".py") else MAX_SOURCE_FILE_BYTES,
                          MAX_SOURCE_TOTAL_BYTES - total)
            actual, _ = tree.fingerprint(name, maximum=maximum)
            _require(actual["git_blob"] == blob and actual["mode"] == mode, f"source differs from real pinned Git blob: {name}")
            files[name] = actual
            total += actual["bytes"]
        record = {"schema": SOURCE_SCHEMA, "git_commit": expected_commit, "scopes": list(SOURCE_SCOPES),
                  "epoch_version": version, "files": dict(sorted(files.items())), "files_sha256": _digest(files),
                  "coverage": SOURCE_COVERAGE}
        _check_sources(tree, record)
    result = _canonical(record) + b"\n"
    _require(len(result) <= MAX_BUNDLE_MANIFEST_BYTES, "portable source manifest exceeds its bound")
    return result


@dataclass(frozen=True, slots=True)
class OriginLimits:
    cpu_seconds: int = 120
    wall_seconds: int = 180
    rss_bytes: int = 1024**3
    output_bytes: int = 2 * 1024**2

    def to_dict(self) -> dict:
        result = {name: getattr(self, name) for name in ("cpu_seconds", "wall_seconds", "rss_bytes", "output_bytes")}
        _limits(result)
        return result


ORIGIN_LIMITS = OriginLimits()


def _limits(value: dict) -> dict:
    _keys(value, {"cpu_seconds", "wall_seconds", "rss_bytes", "output_bytes"}, "origin limits")
    for name, maximum, minimum in (("cpu_seconds", 120, 1), ("wall_seconds", 180, 1),
                                    ("rss_bytes", 1024**3, 128 * 1024**2), ("output_bytes", 2 * 1024**2, 65536)):
        _integer(value[name], maximum, name, minimum)
    _require(value["cpu_seconds"] <= value["wall_seconds"], "inconsistent origin resource reservation")
    return dict(value)


@dataclass(frozen=True, slots=True)
class OriginRequest:
    source_root: Path
    source_manifest: Path
    source_manifest_sha256: str
    source_commit: str
    preparation_directory: Path
    preparation_manifest_sha256: str
    adapter_manifest: Path
    adapter_manifest_sha256: str
    authority_profile: str | None = None

    def __post_init__(self):
        for name in ("source_root", "source_manifest", "preparation_directory", "adapter_manifest"):
            object.__setattr__(self, name, _absolute(getattr(self, name)))
        for name in ("source_manifest_sha256", "preparation_manifest_sha256", "adapter_manifest_sha256"):
            _hash(getattr(self, name), name)
        _require(type(self.source_commit) is str and _OID.fullmatch(self.source_commit) is not None, "origin source commit is invalid")
        _require(self.authority_profile is None or self.authority_profile == AUTHORITY_PROFILE,
                 "bridge supports only original None or V4 authority, without relabelling")
        try:
            relative = self.preparation_directory.relative_to(self.source_root).as_posix()
        except ValueError as error:
            raise OriginBridgeError("preparation must retain its original location under the source bundle") from error
        _relative(relative)
        _require(self.adapter_manifest.name == "manifest.json", "adapter must name its exact original manifest.json")

    def to_dict(self) -> dict:
        """Portable identity: physical source/adapter locations are separate."""
        return {"schema": REQUEST_SCHEMA, "source_manifest_sha256": self.source_manifest_sha256,
                "source_commit": self.source_commit,
                "preparation_relative_path": self.preparation_directory.relative_to(self.source_root).as_posix(),
                "preparation_manifest_sha256": self.preparation_manifest_sha256,
                "adapter_manifest_sha256": self.adapter_manifest_sha256, "authority_profile": self.authority_profile}

    def locations(self) -> dict:
        return {"source_root": str(self.source_root), "source_manifest": str(self.source_manifest),
                "adapter_manifest": str(self.adapter_manifest)}


def _request(identity: dict, locations: dict) -> OriginRequest:
    _keys(identity, {"schema", "source_manifest_sha256", "source_commit", "preparation_relative_path",
                      "preparation_manifest_sha256", "adapter_manifest_sha256", "authority_profile"}, "origin request")
    _keys(locations, {"source_root", "source_manifest", "adapter_manifest"}, "origin locations")
    _require(identity["schema"] == REQUEST_SCHEMA and all(type(value) is str for value in locations.values()),
             "origin request schema/locations differ")
    source_root = Path(locations["source_root"])
    result = OriginRequest(source_root, Path(locations["source_manifest"]), identity["source_manifest_sha256"],
                           identity["source_commit"], source_root / _relative(identity["preparation_relative_path"]),
                           identity["preparation_manifest_sha256"], Path(locations["adapter_manifest"]),
                           identity["adapter_manifest_sha256"], identity["authority_profile"])
    _require(result.to_dict() == identity and result.locations() == locations, "origin locations must be absolute canonical paths")
    return result


def _source_bundle(request: OriginRequest, tree: _Tree) -> tuple[dict, bytes]:
    raw = tree.read(request.source_manifest.name, MAX_BUNDLE_MANIFEST_BYTES)
    _require(_sha(raw) == request.source_manifest_sha256, "external source-bundle SHA differs")
    record = _decode(raw, MAX_BUNDLE_MANIFEST_BYTES, "source bundle")
    _source_record(record)
    _require(record["git_commit"] == request.source_commit, "source bundle changed caller-pinned historical commit")
    return record, raw


def _small_identity(item: dict) -> dict:
    return {"bytes": item["bytes"], "sha256": item["sha256"]}


def _inputs(request: OriginRequest, tree: _Tree, artifacts: _Tree) -> tuple[dict, dict, dict]:
    relative = request.to_dict()["preparation_relative_path"]
    raw = tree.read(relative + "/manifest.json", MAX_MANIFEST_BYTES)
    _require(_sha(raw) == request.preparation_manifest_sha256, "original preparation manifest SHA differs")
    preparation = _decode(raw, MAX_MANIFEST_BYTES, "original preparation")
    expected = preparation.get("files")
    _require(type(expected) is dict and set(expected) == PREPARATION_FILES,
             "preparation must retain its exact closed six-file payload")
    _require(tree.inventory(relative, maximum=7) == {relative + "/" + name for name in PREPARATION_FILES | {"manifest.json"}},
             "original preparation inventory changed")
    result = {"preparation": {"manifest": {"bytes": len(raw), "sha256": _sha(raw)}, "files": {}}, "source": {}, "artifacts": {}}
    total = len(raw)
    for name, descriptor in expected.items():
        _keys(descriptor, {"bytes", "sha256", *({"rows"} if name.endswith(".jsonl") else set())}, "preparation file identity")
        _integer(descriptor["bytes"], MAX_DATA_BYTES, "preparation file bytes")
        _hash(descriptor["sha256"], "preparation payload SHA")
        if name.endswith(".jsonl"):
            _integer(descriptor["rows"], 16384, "prepared rows")
        actual, _ = tree.fingerprint(relative + "/" + name, maximum=MAX_DATA_BYTES)
        _require(_small_identity(actual) == {key: descriptor[key] for key in ("bytes", "sha256")},
                 f"original preparation bytes changed: {name}")
        result["preparation"]["files"][name] = _small_identity(actual)
        total += actual["bytes"]
        _require(total <= MAX_INPUT_TOTAL_BYTES, "original input set exceeds its aggregate byte bound")
    source = preparation.get("source")
    _require(type(source) is dict, "original source binding is missing")
    source_relative = _relative(source.get("directory"))
    _require(tree.inventory(source_relative, maximum=5) == {source_relative + "/" + name for name in SOURCE_INPUT_FIELDS},
             "original source inventory changed")
    result["source"] = {"directory": source_relative, "files": {}}
    for name, field in SOURCE_INPUT_FIELDS.items():
        expected_sha = _hash(source.get(field), "original source payload SHA")
        actual, _ = tree.fingerprint(source_relative + "/" + name, maximum=min(MAX_DATA_BYTES, MAX_INPUT_TOTAL_BYTES - total))
        _require(actual["sha256"] == expected_sha, f"original source bytes changed: {name}")
        result["source"]["files"][name] = _small_identity(actual)
        total += actual["bytes"]
        _require(total <= MAX_INPUT_TOTAL_BYTES, "original input set exceeds its aggregate byte bound")
    adapter_raw = artifacts.read(request.adapter_manifest.name, MAX_MANIFEST_BYTES)
    _require(_sha(adapter_raw) == request.adapter_manifest_sha256, "original adapter manifest SHA differs")
    adapter = _decode(adapter_raw, MAX_MANIFEST_BYTES, "original adapter")
    _require(adapter.get("authority_profile") == request.authority_profile
             and preparation.get("authority_profile") == request.authority_profile
             and (request.authority_profile is not None or "authority_profile" not in adapter and "authority_profile" not in preparation),
             "original training authority was relabelled")
    result["adapter_manifest"] = {"bytes": len(adapter_raw), "sha256": _sha(adapter_raw)}
    total += len(adapter_raw)
    _require(total <= MAX_INPUT_TOTAL_BYTES, "original input set exceeds its aggregate byte bound")
    for kind in ("adapter", "tokenizer"):
        identity = adapter.get(kind)
        _keys(identity, {"root", "sha256", "files"}, "closed model artifact identity")
        files = identity["files"]
        _require(identity["root"] == kind and type(files) is dict and 1 <= len(files) <= 128
                 and identity["sha256"] == _digest(files), "closed artifact group changed")
        for name, digest in files.items():
            _require(_relative(name).startswith(kind + "/"), "artifact file escapes its loader directory")
            _hash(digest, "artifact file SHA")
        _require(artifacts.inventory(kind, maximum=128) == set(files), "closed artifact inventory changed")
        if kind == "adapter":
            _require("adapter/adapter_config.json" in files
                     and sorted(name for name in files if Path(name).suffix.lower() == ".safetensors") == ["adapter/adapter_model.safetensors"]
                     and not any(Path(name).suffix.lower() in _UNSAFE_WEIGHTS for name in files),
                     "adapter must retain exactly safe original safetensors weights")
        result["artifacts"][kind] = {"identity": identity, "files": {}}
        for name, expected_sha in files.items():
            actual, _ = artifacts.fingerprint(name, maximum=min(MAX_ARTIFACT_BYTES, MAX_INPUT_TOTAL_BYTES - total))
            _require(actual["sha256"] == expected_sha, f"closed artifact bytes changed: {name}")
            result["artifacts"][kind]["files"][name] = _small_identity(actual)
            total += actual["bytes"]
            _require(total <= MAX_INPUT_TOTAL_BYTES, "original input set exceeds its aggregate byte bound")
    tree.assert_unchanged()
    artifacts.assert_unchanged()
    return result, preparation, adapter


def _support(tree: _Tree) -> dict:
    return {name: _small_identity(tree.fingerprint(name, maximum=MAX_PYTHON_BYTES)[0]) for name in SUPPORT_FILES}


def _training_summary(adapter: dict) -> dict:
    """Bind saved legacy summary to immutable manifest bytes, not revalidate training.

    The original validators return these unchanged record projections after
    their semantic checks. Reconstructing the projections prevents a resealed
    cached summary from inventing different steps, gradients, losses or source.
    It does not replace those validators or grant trust to an unanchored file.
    """
    metrics = adapter["metrics"]
    _require(type(metrics) is dict, "original training metrics are missing")
    result = {}
    for name in ("expected_optimizer_steps", "actual_optimizer_steps", "training_rows", "development_rows"):
        result[name] = _integer(metrics[name], 16384, "original " + name, 1)
    _require(result["expected_optimizer_steps"] == result["actual_optimizer_steps"], "saved training is incomplete")
    for field, source in (("objective_sha256", "objective"), ("trainer_runtime_sha256", "trainer_runtime"),
                          ("finite_gradient_audit_sha256", "finite_gradient_audit"), ("adapter_update_sha256", "adapter_update")):
        _require(type(adapter[source]) is dict, "original evidence record is missing")
        result[field] = _digest(adapter[source])
    provenance = {name: adapter[name] for name in ("runtime", "deployment", "job", "requirements_verification")}
    _require(all(type(value) is dict for value in provenance.values()), "original execution provenance is missing")
    result["execution_provenance_sha256"] = _digest(provenance)
    for field, name, required in (("train_metrics", "train", "train_loss"), ("development_metrics", "dev", "eval_loss")):
        values = metrics[name]
        _require(type(values) is dict and required in values and 1 <= len(values) <= 128
                 and all(type(key) is str and key and type(value) in {int, float} and math.isfinite(value)
                         for key, value in values.items()), "saved metrics must remain finite non-boolean values")
        result[field] = values
    return result


class _PinnedLoader(importlib.abc.Loader):
    def __init__(self, finder, relative):
        self.finder, self.relative = finder, relative

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        tree = self.finder.tree
        raw = tree.read(self.relative, MAX_PYTHON_BYTES)
        expected = self.finder.files[self.relative]
        _require(len(raw) == expected["bytes"] and _sha(raw) == expected["sha256"], "source changed immediately before import")
        tree.assert_unchanged()
        self.finder.loaded[module.__name__] = {"path": self.relative, "sha256": expected["sha256"]}
        # Compile these verified source bytes directly; never inspect a .pyc.
        exec(compile(raw, str(tree.root / self.relative), "exec", dont_inherit=True), module.__dict__)
        tree.assert_unchanged()


class _SourceFinder(importlib.abc.MetaPathFinder):
    def __init__(self, tree: _Tree, files: dict):
        self.tree, self.files, self.loaded = tree, files, {}

    def find_spec(self, fullname, path=None, target=None):
        first = fullname.partition(".")[0]
        _require(first not in _MODEL_IMPORTS, "origin validation cannot import a model/tokenizer framework")
        relative = None
        if first == "training":
            relative = fullname.replace(".", "/")
        elif first == "peano_lab":
            relative = "peano-lab/py/" + fullname.replace(".", "/")
        elif first == "scripts":
            relative = fullname.replace(".", "/")
        if relative is not None:
            for name in (relative + "/__init__.py", relative + ".py"):
                if name in self.files:
                    return importlib.util.spec_from_file_location(fullname, self.tree.root / name,
                        loader=_PinnedLoader(self, name),
                        submodule_search_locations=[str(self.tree.root / relative)] if name.endswith("/__init__.py") else None)
            if any(name.startswith(relative + "/") for name in self.files):
                spec = importlib.machinery.ModuleSpec(fullname, loader=None, is_package=True)
                spec.submodule_search_locations = [str(self.tree.root / relative)]
                return spec
            raise ModuleNotFoundError(f"unlisted original project module: {fullname}")
        selected = importlib.machinery.PathFinder.find_spec(fullname, path)
        origin = getattr(selected, "origin", None)
        if origin and Path(origin).is_absolute() and Path(origin).is_relative_to(self.tree.root):
            name = Path(origin).relative_to(self.tree.root).as_posix()
            _require(name.endswith(".py") and name in self.files, "unlisted or binary repository import")
            return importlib.util.spec_from_file_location(fullname, origin, loader=_PinnedLoader(self, name),
                submodule_search_locations=selected.submodule_search_locations)
        return None

    def validate_loaded(self) -> dict:
        _require(0 < len(self.loaded) <= MAX_SOURCE_FILES, "original module load inventory exceeds its bound")
        for name, module in tuple(sys.modules.items()):
            first = name.partition(".")[0]
            _require(first not in _MODEL_IMPORTS, "origin verification imported model framework code")
            path = getattr(module, "__file__", None)
            relevant = first in {"training", "peano_lab", "scripts"}
            if path is not None and Path(path).is_absolute() and Path(path).is_relative_to(self.tree.root):
                relevant = True
            if not relevant:
                continue
            if path is None:
                locations = list(getattr(module, "__path__", ()))
                _require(locations and all(Path(value).is_relative_to(self.tree.root) for value in locations),
                         "original package namespace escaped the pinned root")
            else:
                item = self.loaded.get(name)
                _require(item is not None and Path(path).absolute() == self.tree.root / item["path"],
                         "original code bypassed the pinned source-only loader")
        self.tree.assert_unchanged()
        return dict(sorted(self.loaded.items()))


def _origin_record(plan, adapter: dict, artifacts: dict) -> dict:
    result = {
        "kind": "completed-posttraining-origin", "schema": adapter["schema"], "version": adapter["version"],
        "run_id": adapter["run_id"], "model": dict(plan.model), "epoch_sha256": plan.epoch.epoch_sha256,
        "edition_identity_sha256": plan.epoch.edition_identity_sha256,
        "theorem_dag_sha256": plan.epoch.theorem_dag_sha256,
        "reviewed_definition_dag_sha256": plan.epoch.reviewed_definition_dag_sha256,
        "preparation_manifest_sha256": plan.preparation_manifest_sha256,
        "adapter_manifest_sha256": plan.trained_adapter["manifest_sha256"],
        "training_authority_profile": plan.authority_profile,
        "training_prompt_contract": adapter.get("prompt_contract"),
        "training_decoder_profile": adapter.get("decoder_profile"),
        "training_evidence": plan.trained_adapter["training_evidence"],
        "training_source_commit": adapter["deployment"]["source_sync"].get("git_commit"),
        "artifacts": artifacts, "research_claim_eligible": False,
    }
    return {**result, "origin_sha256": _digest(result)}


def _legacy_origin(request: OriginRequest, adapter: dict) -> tuple[dict, dict]:
    """Only called in the explicit fresh worker; no previous-adapter override."""
    from training.peano_hydra import evaluation as original
    plan = original.build_matched_evaluation_plan(
        request.preparation_directory, trained_adapter=request.adapter_manifest,
        repository_root=request.source_root, authority_profile=request.authority_profile,
    )
    _require(plan.preparation_manifest_sha256 == request.preparation_manifest_sha256
             and plan.trained_adapter["manifest_sha256"] == request.adapter_manifest_sha256,
             "original validators returned a different requested origin")
    adapter_directory, tokenizer_directory, artifacts = original._verify_trained_artifacts(plan)
    _require(adapter_directory == request.adapter_manifest.parent / "adapter"
             and tokenizer_directory == request.adapter_manifest.parent / "tokenizer", "original artifact loader paths changed")
    return _origin_record(plan, adapter, artifacts), {
        "module": "training.peano_hydra.evaluation",
        "entrypoints": ["build_matched_evaluation_plan", "_verify_trained_artifacts"],
        "held_out_sha256": original._digest(plan.held_out),
        "semantics": "unchanged original validator semantics; no additional corpus, cold-replay or inference claim",
    }


def _worker(payload: bytes) -> dict:
    _require(not _MODEL_IMPORTS.intersection(name.split(".")[0] for name in sys.modules), "worker must start without model frameworks")
    _require(not any(name == "training" or name.startswith(("training.", "peano_lab")) for name in sys.modules),
             "worker must start without preloaded project modules")
    _require(sys.flags.isolated and sys.dont_write_bytecode and sys.pycache_prefix == "/dev/null"
             and stat.S_ISCHR(os.lstat("/dev/null").st_mode), "worker needs isolated source-only Python startup")
    message = _decode(payload, MAX_REQUEST_BYTES, "origin worker request")
    _keys(message, {"schema", "request", "locations", "limits", "source_manifest", "inputs_sha256", "bridge_support"}, "worker request")
    _require(message["schema"] == WORKER_SCHEMA and payload == _canonical(message), "worker request lost canonical bytes")
    limits = _limits(message["limits"])
    soft, hard = resource.getrlimit(resource.RLIMIT_CPU)
    _require(type(soft) is int and soft == limits["cpu_seconds"] and hard == soft + 1, "worker has no exact inherited CPU reservation")
    request = _request(message["request"], message["locations"])
    with ExitStack() as stack:
        tree = stack.enter_context(_Tree(request.source_root))
        artifacts = stack.enter_context(_Tree(request.adapter_manifest.parent))
        manifest_tree = stack.enter_context(_Tree(request.source_manifest.parent))
        support_tree = stack.enter_context(_Tree(ROOT))
        source, source_raw = _source_bundle(request, manifest_tree)
        _require(source == message["source_manifest"], "worker source manifest differs from parent")
        _check_sources(tree, source)
        inputs, _, adapter = _inputs(request, tree, artifacts)
        _require(_digest(inputs) == message["inputs_sha256"] and _support(support_tree) == message["bridge_support"],
                 "worker inputs or bridge implementation changed")
        finder = _SourceFinder(tree, source["files"])
        original_path, original_meta = list(sys.path), list(sys.meta_path)
        try:
            sys.path[:0] = [str(request.source_root), str(request.source_root / "peano-lab/py"), str(request.source_root / "scripts")]
            sys.meta_path.insert(0, finder)
            # The legacy API performs its original native checks only here.
            origin, validation = _legacy_origin(request, adapter)
            loaded = finder.validate_loaded()
            _check_sources(tree, source)
            after, _, _ = _inputs(request, tree, artifacts)
            _require(after == inputs and _source_bundle(request, manifest_tree)[1] == source_raw
                     and _support(support_tree) == message["bridge_support"], "original inputs changed through validation")
            for pinned in (tree, artifacts, manifest_tree, support_tree):
                pinned.assert_unchanged()
        finally:
            sys.path[:] = original_path
            sys.meta_path[:] = original_meta
    return {"schema": WORKER_SCHEMA, "status": "validated-original-origin",
            "request_sha256": _digest(request.to_dict()), "source_manifest_sha256": request.source_manifest_sha256,
            "inputs_sha256": _digest(inputs), "origin": origin, "validation": validation,
            "loaded_sources": loaded, "model_frameworks_imported": False,
            "model_generation_performed": False, "proof_search_performed": False}


def _command(python: Path, script: Path) -> tuple[str, ...]:
    return (str(_absolute(python)), "-I", "-B", "-X", "pycache_prefix=/dev/null", str(_absolute(script)), "--origin-worker")


@dataclass(frozen=True, slots=True)
class AuthenticatedOrigin:
    request: OriginRequest
    _origin_json: str
    _receipt_bytes: bytes
    validation_mode: str

    @property
    def origin(self) -> dict:
        return json.loads(self._origin_json)

    @property
    def adapter_directory(self) -> Path:
        return self.request.adapter_manifest.parent / "adapter"

    @property
    def tokenizer_directory(self) -> Path:
        return self.request.adapter_manifest.parent / "tokenizer"

    @property
    def receipt_bytes(self) -> bytes:
        return self._receipt_bytes

    @property
    def receipt_sha256(self) -> str:
        return _sha(self._receipt_bytes)


def _validate_receipt(record: dict, request: OriginRequest, source: dict, inputs: dict, adapter: dict,
                      support: dict) -> dict:
    from .review_runtime import ProcessLimits, validate_process_record
    _keys(record, {"schema", "request", "locations", "source_manifest", "inputs", "bridge_support", "limits",
                   "python", "script", "runtime_library_paths", "process", "worker", "claim_boundary"}, "origin receipt")
    _require(record["schema"] == RECEIPT_SCHEMA and record["request"] == request.to_dict()
             and record["source_manifest"] == source and record["inputs"] == inputs and record["bridge_support"] == support,
             "receipt differs from caller-pinned source/input/origin identities")
    # Historical locations are syntax/binding data only; never execute them.
    recorded = _request(record["request"], record["locations"])
    _require(type(record["python"]) is str and type(record["script"]) is str
             and Path(record["script"]).name == "origin_bridge.py", "recorded bridge command differs")
    command = _command(Path(record["python"]), Path(record["script"]))
    limits = ProcessLimits(**_limits(record["limits"]))
    libraries = record["runtime_library_paths"]
    _require(type(libraries) is list and all(type(value) is str for value in libraries), "runtime library declaration differs")
    payload = {"schema": WORKER_SCHEMA, "request": recorded.to_dict(), "locations": recorded.locations(),
               "limits": limits.to_dict(), "source_manifest": source, "inputs_sha256": _digest(inputs), "bridge_support": support}
    validate_process_record(record["process"], command=command, limits=limits, input_bytes=_canonical(payload),
                            success_codes=(0,), runtime_library_paths=tuple(libraries))
    worker = record["worker"]
    _require(record["process"]["stdout"] == (_canonical(worker) + b"\n").decode(), "worker output bytes differ from retained result")
    _keys(worker, {"schema", "status", "request_sha256", "source_manifest_sha256", "inputs_sha256", "origin", "validation",
                   "loaded_sources", "model_frameworks_imported", "model_generation_performed", "proof_search_performed"}, "origin worker result")
    _require(worker["schema"] == WORKER_SCHEMA and worker["status"] == "validated-original-origin"
             and worker["request_sha256"] == _digest(request.to_dict())
             and worker["source_manifest_sha256"] == request.source_manifest_sha256
             and worker["inputs_sha256"] == _digest(inputs)
             and all(worker[name] is False for name in ("model_frameworks_imported", "model_generation_performed", "proof_search_performed")),
             "worker changed its exact request or claims")
    validation = worker["validation"]
    _keys(validation, {"module", "entrypoints", "held_out_sha256", "semantics"}, "legacy validation summary")
    _require(validation["module"] == "training.peano_hydra.evaluation"
             and validation["entrypoints"] == ["build_matched_evaluation_plan", "_verify_trained_artifacts"]
             and validation["semantics"] == "unchanged original validator semantics; no additional corpus, cold-replay or inference claim",
             "original validation API/claims differ")
    _hash(validation["held_out_sha256"], "original held-out evidence SHA")
    loaded = worker["loaded_sources"]
    _require(type(loaded) is dict and 1 <= len(loaded) <= MAX_SOURCE_FILES
             and "training.peano_hydra.evaluation" in loaded, "original module inventory is missing")
    for name, item in loaded.items():
        _require(type(name) is str and 0 < len(name) <= 512
                 and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*", name) is not None,
                 "invalid loaded module name")
        _keys(item, {"path", "sha256"}, "loaded source")
        path = _relative(item["path"])
        _require(path in source["files"] and path.endswith(".py")
                 and item["sha256"] == source["files"][path]["sha256"], "loaded module source differs from pinned inventory")
        module_path = name.replace(".", "/")
        if name == "peano_lab" or name.startswith("peano_lab."):
            module_path = "peano-lab/py/" + module_path
        elif name.split(".")[0] not in {"training", "scripts"}:
            module_path = "scripts/" + module_path
        _require(path in {module_path + ".py", module_path + "/__init__.py"},
                 "loaded module name was rebound to a different source")
    origin = worker["origin"]
    fields = {"kind", "schema", "version", "run_id", "model", "epoch_sha256", "edition_identity_sha256", "theorem_dag_sha256",
              "reviewed_definition_dag_sha256", "preparation_manifest_sha256", "adapter_manifest_sha256",
              "training_authority_profile", "training_prompt_contract", "training_decoder_profile", "training_evidence",
              "training_source_commit", "artifacts", "research_claim_eligible", "origin_sha256"}
    _keys(origin, fields, "original origin")
    expected = {key: adapter[key] for key in ("schema", "version", "run_id", "epoch_sha256", "edition_identity_sha256",
                                               "theorem_dag_sha256", "reviewed_definition_dag_sha256")}
    expected.update({"kind": "completed-posttraining-origin", "model": {key: adapter["model"][key] for key in ("model_id", "revision")},
                     "preparation_manifest_sha256": request.preparation_manifest_sha256,
                     "adapter_manifest_sha256": request.adapter_manifest_sha256, "training_authority_profile": request.authority_profile,
                     "training_prompt_contract": adapter.get("prompt_contract"), "training_decoder_profile": adapter.get("decoder_profile"),
                     "training_source_commit": adapter["deployment"]["source_sync"].get("git_commit"),
                     "artifacts": {kind: inputs["artifacts"][kind]["identity"] for kind in ("adapter", "tokenizer")},
                     "training_evidence": _training_summary(adapter), "research_claim_eligible": False})
    _require(origin == {**expected, "origin_sha256": _digest(expected)} and origin["research_claim_eligible"] is False,
             "original manifest/model/epoch/artifact identity was relabelled")
    _require(type(origin["training_evidence"]) is dict and len(_canonical(origin["training_evidence"])) <= 128 * 1024,
             "saved original training evidence exceeds its bound")
    _require(record["claim_boundary"] == _CLAIM, "bridge claim boundary differs")
    return origin


_CLAIM = "Preserved original training validated by its unchanged frozen implementation; cached reuse needs an external raw receipt anchor and fresh byte checks. No new training, inference, checkpoint reuse, optimized-engine equivalence proof, or hardware attestation."


def authenticate_origin(request: OriginRequest, *, python: Path, limits: OriginLimits = ORIGIN_LIMITS,
                        runtime_library_paths: tuple[str, ...] = ()) -> AuthenticatedOrigin:
    """Explicitly run ONE bounded original-validator child; never retry/fallback."""
    from .review_runtime import ProcessLimits, run_bounded, validate_process_record
    _require(type(request) is OriginRequest, "origin authentication requires an explicit request")
    bound = ProcessLimits(**_limits(limits.to_dict()))
    command = _command(python, Path(__file__).absolute())
    with ExitStack() as stack:
        tree = stack.enter_context(_Tree(request.source_root))
        artifacts = stack.enter_context(_Tree(request.adapter_manifest.parent))
        manifest_tree = stack.enter_context(_Tree(request.source_manifest.parent))
        support_tree = stack.enter_context(_Tree(ROOT))
        source, source_raw = _source_bundle(request, manifest_tree)
        _check_sources(tree, source)
        inputs, _, adapter = _inputs(request, tree, artifacts)
        support = _support(support_tree)
        message = {"schema": WORKER_SCHEMA, "request": request.to_dict(), "locations": request.locations(),
                   "limits": bound.to_dict(), "source_manifest": source, "inputs_sha256": _digest(inputs), "bridge_support": support}
        payload = _canonical(message)
        _require(len(payload) <= MAX_REQUEST_BYTES, "origin worker request exceeds its bound")
        process = run_bounded(command, cwd=request.source_root, limits=bound, input_bytes=payload,
                              runtime_library_paths=runtime_library_paths)
        _check_sources(tree, source)
        after, _, _ = _inputs(request, tree, artifacts)
        _require(after == inputs and _source_bundle(request, manifest_tree)[1] == source_raw
                 and _support(support_tree) == support, "origin inputs changed during bounded validation")
        for pinned in (tree, artifacts, manifest_tree, support_tree):
            pinned.assert_unchanged()
        if process["reason"] != "exited" or process["returncode"] != 0:
            raise OriginBridgeError("bounded origin validation did not complete; no authenticated handle or retry",
                                    observation={"request": request.to_dict(), "process": process})
        validate_process_record(process, command=command, limits=bound, input_bytes=payload,
                                success_codes=(0,), runtime_library_paths=runtime_library_paths)
        worker = _decode(process["stdout"].encode(), bound.output_bytes, "origin worker output")
        record = {"schema": RECEIPT_SCHEMA, "request": request.to_dict(), "locations": request.locations(), "source_manifest": source,
                  "inputs": inputs, "bridge_support": support, "limits": bound.to_dict(), "python": command[0], "script": command[5],
                  "runtime_library_paths": list(runtime_library_paths), "process": process, "worker": worker, "claim_boundary": _CLAIM}
        origin = _validate_receipt(record, request, source, inputs, adapter, support)
        raw = _canonical(record) + b"\n"
        _require(len(raw) <= MAX_RECEIPT_BYTES, "origin receipt exceeds its byte bound")
    return AuthenticatedOrigin(request, _canonical(origin).decode(), raw, "fresh-original-validator")


def load_origin_receipt(path: Path, *, expected_receipt_sha256: str, request: OriginRequest) -> AuthenticatedOrigin:
    """Model/native-free anchored reuse, with full current source/input hashing.

    The expected raw SHA must come from a separately trusted completed check,
    not this file's claims. Historic absolute command strings are only checked
    as saved metadata; the relocated current paths come from ``request``.
    """
    _require(type(request) is OriginRequest, "receipt loading requires an explicit origin request")
    _hash(expected_receipt_sha256, "external origin receipt SHA")
    path = _absolute(path)
    with ExitStack() as stack:
        receipt_tree = stack.enter_context(_Tree(path.parent))
        raw = receipt_tree.read(path.name, MAX_RECEIPT_BYTES)
        _require(_sha(raw) == expected_receipt_sha256, "externally anchored origin receipt SHA differs")
        record = _decode(raw, MAX_RECEIPT_BYTES, "origin receipt")
        tree = stack.enter_context(_Tree(request.source_root))
        artifacts = stack.enter_context(_Tree(request.adapter_manifest.parent))
        manifest_tree = stack.enter_context(_Tree(request.source_manifest.parent))
        support_tree = stack.enter_context(_Tree(ROOT))
        source, source_raw = _source_bundle(request, manifest_tree)
        _check_sources(tree, source)
        inputs, _, adapter = _inputs(request, tree, artifacts)
        support = _support(support_tree)
        origin = _validate_receipt(record, request, source, inputs, adapter, support)
        _require(receipt_tree.read(path.name, MAX_RECEIPT_BYTES) == raw
                 and _source_bundle(request, manifest_tree)[1] == source_raw, "cached receipt/source manifest changed")
        for pinned in (receipt_tree, tree, artifacts, manifest_tree, support_tree):
            pinned.assert_unchanged()
    return AuthenticatedOrigin(request, _canonical(origin).decode(), raw, "externally-anchored-byte-recheck-no-replay")


def execution_binding(*, source_root: Path, source_files: Mapping[str, str], contract: dict) -> dict:
    """Hash a separately caller-validated execution contract and current sources.

    This does not validate theorem authority/search policy semantics, compare
    two engines, change an origin, or accept any old checkpoint. The comparison
    planner must supply its independently validated complete contract.
    """
    _require(type(source_files) is dict and 2 <= len(source_files) <= MAX_EXECUTION_FILES
             and {"training/peano_hydra/origin_bridge.py", "peano-lab/py/peano_lab/engine/rewrite.py"} <= source_files.keys(),
             "execution source inventory must explicitly include bridge and optimized engine")
    _require(type(contract) is dict and 0 < len(_canonical(contract)) <= 128 * 1024, "execution contract exceeds its bound")
    files = {}
    with _Tree(source_root) as tree:
        for name, expected_sha in sorted(source_files.items()):
            _relative(name)
            _hash(expected_sha, "execution source SHA")
            actual, _ = tree.fingerprint(name, maximum=MAX_PYTHON_BYTES)
            _require(actual["sha256"] == expected_sha, "execution source changed from supplied contract")
            files[name] = _small_identity(actual)
        tree.assert_unchanged()
    result = {"schema": EXECUTION_SCHEMA, "source_files": files, "source_files_sha256": _digest(files),
              "contract": json.loads(_canonical(contract)), "contract_sha256": _digest(contract),
              "training_origins_relabelled": False, "old_checkpoint_resume_allowed": False,
              "engine_equivalence_claimed": False}
    return {**result, "execution_binding_sha256": _digest(result)}


if __name__ == "__main__":
    try:
        _require(sys.argv[1:] == ["--origin-worker"], "only the explicit bounded internal worker entrypoint is supported")
        result = _worker(sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1))
        print((_canonical(result) + b"\n").decode(), end="")
    except (OriginBridgeError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"origin-bridge: {error}", file=sys.stderr)
        raise SystemExit(2)
