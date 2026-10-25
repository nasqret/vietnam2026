"""Bounded immutable JSONL shards; structural integrity, never proof admission.

The caller supplies an independently reviewed binding and an external RAW
manifest SHA. Neither stored ``kernel_checked`` payloads nor this module's
structural receipt authorize training or replace native replay/lineage review.
The original unsharded dataset limits are not imported or changed here.

Publication exclusively creates the destination; its canonical manifest is
the last commit. Failed publication leaves a diagnostic, unadoptable directory.
Readers reject missing manifests, temporary files, extra entries and aliases.
Iteration validates every shard before yielding anything, then rehashes one
bounded shard into memory before yielding any of its original verified bytes.
Callers should exhaust/close iterators promptly to release directory anchors.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
import uuid
from typing import Iterable, Iterator


STORE_SCHEMA = "peano-hydra-scaling-sharded-store-v1"
PROFILE_SCHEMA = "peano-hydra-scaling-shard-profile-v1"
BINDING_SCHEMA = "peano-hydra-scaling-shard-binding-v1"
VALIDATION_SCHEMA = "peano-hydra-scaling-shard-structural-validation-v1"
MANIFEST_NAME = "manifest.json"
SPLITS = ("train", "dev", "test", "quarantine")
MAX_MANIFEST_BYTES = 256 * 1024
MAX_JSON_DEPTH = 32
MAX_JSON_NODES = 16384
MAX_IDENTIFIER_BYTES = 256
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_LABEL = re.compile(r"[a-z][a-z0-9._-]{0,127}\Z")
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:@/-]{0,255}\Z")
_SHARD = re.compile(r"shard-([0-9]{6})\.jsonl\Z")
_DEDUPLICATION = "global-sha256-example-id-and-lineage-single-split-v1"
_MANIFEST_FIELDS = {"schema", "binding", "profile", "shards", "total_rows", "total_bytes", "split_rows",
                    "deduplication", "structural_only", "native_admission_performed", "training_authorized"}
_ROW_FIELDS = {"example_id", "split", "lineage_sha256", "payload"}
_SHARD_FIELDS = {"file", "sha256", "bytes", "rows", "split_rows"}
# Reviewed ceilings; callers may choose tighter limits, never infer an upgrade
# from a saved manifest. The scale profile must be explicitly passed by name.
_CEILINGS = {
    "bounded-small-v1": (64 * 1024, 2 * 1024**2, 2048, 64, 16384, 64 * 1024**2),
    "bounded-scale-100k-v1": (64 * 1024, 8 * 1024**2, 8192, 128, 131072, 512 * 1024**2),
}


class ShardStoreError(ValueError):
    """A structural, identity, publication or resource boundary was violated."""


def _require(value: object, message: str) -> None:
    if not value:
        raise ShardStoreError(message)


def _integer(value: object, maximum: int, label: str, *, minimum: int = 0) -> int:
    _require(type(value) is int and minimum <= value <= maximum, "invalid bounded " + label)
    return value


def _hash(value: object, label: str) -> str:
    _require(type(value) is str and _SHA.fullmatch(value) is not None, "invalid " + label + " SHA256")
    return value


@dataclass(frozen=True)
class StoreBinding:
    row_schema: str
    source_sha256: str
    authority_sha256: str
    lineage_sha256: str

    def __post_init__(self) -> None:
        _require(type(self.row_schema) is str and _LABEL.fullmatch(self.row_schema) is not None,
                 "invalid bound row schema")
        for name in ("source_sha256", "authority_sha256", "lineage_sha256"):
            _hash(getattr(self, name), name)

    def to_dict(self) -> dict:
        return {"schema": BINDING_SCHEMA, **{field.name: getattr(self, field.name) for field in fields(self)}}


@dataclass(frozen=True)
class ShardProfile:
    name: str
    max_row_bytes: int
    max_shard_bytes: int
    max_rows_per_shard: int
    max_shards: int
    max_total_rows: int
    max_total_bytes: int

    def __post_init__(self) -> None:
        _require(type(self.name) is str and self.name in _CEILINGS, "unknown reviewed shard profile")
        limits = tuple(field.name for field in fields(self) if field.name != "name")
        for name, ceiling in zip(limits, _CEILINGS[self.name]):
            _integer(getattr(self, name), ceiling, name, minimum=1)
        _require(self.max_row_bytes <= self.max_shard_bytes <= self.max_total_bytes,
                 "shard byte limits are inconsistent")
        _require(self.max_rows_per_shard <= self.max_total_rows, "shard row limits are inconsistent")

    def to_dict(self) -> dict:
        return {"schema": PROFILE_SCHEMA, **{field.name: getattr(self, field.name) for field in fields(self)}}


DEFAULT_PROFILE = ShardProfile("bounded-small-v1", *_CEILINGS["bounded-small-v1"])
SCALE_100K_V1 = ShardProfile("bounded-scale-100k-v1", *_CEILINGS["bounded-scale-100k-v1"])


def _arguments(binding: StoreBinding, profile: ShardProfile) -> None:
    _require(type(binding) is StoreBinding and type(profile) is ShardProfile, "explicit typed store binding/profile required")
    binding.__post_init__()
    profile.__post_init__()


def _canonical(value: object, maximum: int) -> bytes:
    """Bound standard JSON structure BEFORE allocating its encoded form."""
    pending, nodes, text_bytes = [(value, 0)], 0, 0
    while pending:
        item, depth = pending.pop()
        nodes += 1
        _require(nodes <= MAX_JSON_NODES and depth <= MAX_JSON_DEPTH, "JSON structure exceeds its bound")
        kind = type(item)
        if kind is str:
            _require(len(item) <= maximum, "JSON text exceeds its byte bound")
            try:
                text_bytes += len(item.encode("utf-8"))
            except UnicodeError as error:
                raise ShardStoreError("JSON text must be valid UTF8") from error
            _require(text_bytes <= maximum, "JSON text exceeds its aggregate byte bound")
        elif kind is dict:
            _require(len(item) <= MAX_JSON_NODES - nodes and len(pending) + 2 * len(item) <= MAX_JSON_NODES,
                     "JSON object exceeds its node bound")
            for key, child in item.items():
                _require(type(key) is str, "JSON object keys must be strings")
                pending.extend(((key, depth + 1), (child, depth + 1)))
        elif kind is list:
            _require(len(item) <= MAX_JSON_NODES - nodes and len(pending) + len(item) <= MAX_JSON_NODES,
                     "JSON array exceeds its node bound")
            pending.extend((child, depth + 1) for child in item)
        elif kind is int:
            _require(-(2**63) <= item < 2**63, "JSON integer exceeds signed64 bound")
        elif kind is float:
            _require(math.isfinite(item), "nonfinite JSON number")
        else:
            _require(item is None or kind is bool, "only standard JSON values are accepted")
    try:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (ValueError, TypeError, UnicodeError, RecursionError) as error:
        raise ShardStoreError("invalid bounded JSON value") from error
    _require(len(raw) <= maximum, "canonical JSON exceeds its byte bound")
    return raw


def _decode(raw: bytes, maximum: int) -> dict:
    _require(type(raw) is bytes and 0 < len(raw) <= maximum, "JSON input exceeds its byte bound")
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    def integer(text):
        _require(len(text) <= 20, "JSON integer exceeds its lexical bound")
        value = int(text)
        _require(-(2**63) <= value < 2**63, "JSON integer exceeds signed64 bound")
        return value
    def floating(text):
        _require(len(text) <= 64, "JSON float exceeds its lexical bound")
        value = float(text)
        _require(math.isfinite(value), "nonfinite JSON number")
        return value
    def invalid(_text):
        raise ShardStoreError("nonfinite JSON number")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_int=integer,
                           parse_float=floating, parse_constant=invalid)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ShardStoreError("invalid strict JSON: " + str(error)[:160]) from error
    _require(type(value) is dict, "one JSON object is required")
    _canonical(value, maximum)
    return value


def _manifest_bytes(manifest: dict) -> bytes:
    return _canonical(manifest, MAX_MANIFEST_BYTES - 1) + b"\n"


def manifest_raw_sha256(manifest: dict) -> str:
    """Hash canonical manifest-file bytes (+LF); this is NOT validation."""
    return hashlib.sha256(_manifest_bytes(manifest)).hexdigest()


def _counts() -> dict[str, int]:
    return dict.fromkeys(SPLITS, 0)


def _row(value: object, binding: StoreBinding, profile: ShardProfile) -> bytes:
    _require(type(value) is dict and set(value) == _ROW_FIELDS, "shard row fields differ")
    _require(type(value["example_id"]) is str and _ID.fullmatch(value["example_id"]) is not None,
             "invalid bounded example identity")
    _require(type(value["split"]) is str and value["split"] in SPLITS, "unknown data split")
    _hash(value["lineage_sha256"], "row lineage")
    _require(type(value["payload"]) is dict and value["payload"].get("schema") == binding.row_schema,
             "payload schema differs from the externally bound row schema")
    return _canonical(value, profile.max_row_bytes - 1) + b"\n"


class _IdentityIndex:
    """Only fixed-size hashes/split integers survive a row; never prompts."""
    def __init__(self, maximum: int):
        self.maximum = maximum
        self.examples: set[bytes] = set()
        self.lineages: dict[bytes, int] = {}

    def add(self, row: dict) -> None:
        _require(len(self.examples) < self.maximum, "total rows/identity index exceeds its bound")
        key = hashlib.sha256(row["example_id"].encode("ascii")).digest()
        _require(key not in self.examples, "duplicate example identity across rows/shards/splits")
        lineage, split = bytes.fromhex(row["lineage_sha256"]), SPLITS.index(row["split"])
        previous = self.lineages.setdefault(lineage, split)
        _require(previous == split, "one lineage appears in multiple splits")
        self.examples.add(key)


def _path(path: Path | str) -> Path:
    text = os.fspath(path)
    _require(type(text) is str and 0 < len(text.encode("utf-8")) <= 4096
             and "\\" not in text and not any(ord(char) < 32 or ord(char) == 127 for char in text), "unsafe store path")
    _require(all(part not in (".", "..") for part in text.split("/")), "store path contains traversal/alias components")
    result = Path(text).absolute()
    _require(1 < len(result.parts) <= 64 and result.anchor == "/", "unsafe bounded absolute store path")
    return result


def _signature(info) -> tuple:
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


class _Tree:
    """Keep every ancestor anchored; only the readable leaf is enumerated."""
    def __init__(self, path: Path):
        self.path, self.fds, self.ancestors, self.files = _path(path), [], [], {}
        self.fd = -1
        access = getattr(os, "O_PATH", os.O_RDONLY) if sys.platform == "linux" else os.O_RDONLY
        try:
            current = os.open(self.path.anchor, access | os.O_DIRECTORY | os.O_NOFOLLOW)
            self.fds.append(current)
            for index, part in enumerate(self.path.parts[1:], 1):
                flags = os.O_RDONLY if index == len(self.path.parts) - 1 else access
                child = os.open(part, flags | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current)
                info = os.fstat(child)
                self.fds.append(child)
                self.ancestors.append((current, part, child, (info.st_dev, info.st_ino)))
                current = child
            self.fd = current
            self.assert_unchanged()
        except BaseException:
            self.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()

    def close(self):
        for fd in reversed(self.fds):
            os.close(fd)
        self.fds.clear()
        self.fd = -1

    def assert_unchanged(self):
        for parent, name, fd, expected in self.ancestors:
            named, held = os.stat(name, dir_fd=parent, follow_symlinks=False), os.fstat(fd)
            _require(stat.S_ISDIR(named.st_mode) and named.st_nlink > 0 and held.st_nlink > 0
                     and (named.st_dev, named.st_ino) == (held.st_dev, held.st_ino) == expected,
                     "store root or ancestor identity changed")
        for name, expected in self.files.items():
            _require(_signature(os.stat(name, dir_fd=self.fd, follow_symlinks=False)) == expected,
                     "previously verified store file changed: " + name)

    def inventory(self, profile: ShardProfile, *, manifest: bool) -> set[str]:
        self.assert_unchanged()
        before, names = os.fstat(self.fd), set()
        _require(stat.S_IMODE(before.st_mode) & 0o022 == 0, "store directory is group/world writable")
        with os.scandir(self.fd) as entries:
            for entry in entries:
                _require(len(names) < profile.max_shards + int(manifest), "closed store inventory exceeds its entry bound")
                info = entry.stat(follow_symlinks=False)
                _require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and stat.S_IMODE(info.st_mode) & 0o022 == 0,
                         "store contains a symlink, hardlink, directory or special/writable file")
                if manifest and entry.name == MANIFEST_NAME:
                    maximum = MAX_MANIFEST_BYTES
                else:
                    match = _SHARD.fullmatch(entry.name)
                    _require(match is not None and 1 <= int(match.group(1)) <= profile.max_shards,
                             "unexpected store file or interrupted staging debris")
                    maximum = profile.max_shard_bytes
                _require(info.st_size <= maximum, "store file exceeds its byte bound")
                names.add(entry.name)
        _require(_signature(before) == _signature(os.fstat(self.fd)), "store directory changed during inventory")
        self.assert_unchanged()
        return names

    def open_file(self, name: str, maximum: int, *, expected_size: int | None = None) -> tuple[int, tuple]:
        self.assert_unchanged()
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=self.fd)
        try:
            info = os.fstat(fd)
            _require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= maximum
                     and stat.S_IMODE(info.st_mode) & 0o022 == 0, "unsafe or oversized store file")
            _require(expected_size is None or info.st_size == expected_size, "store file byte count differs")
            signature = _signature(info)
            _require(self.files.get(name, signature) == signature, "store file changed between validation and reread")
            self.check_file(name, fd, signature)
            return fd, signature
        except BaseException:
            os.close(fd)
            raise

    def check_file(self, name: str, fd: int, signature: tuple) -> None:
        _require(_signature(os.fstat(fd)) == _signature(os.stat(name, dir_fd=self.fd, follow_symlinks=False)) == signature,
                 "store file changed during read")

    def read_file(self, name: str, maximum: int, *, expected_size: int | None = None) -> bytes:
        fd, signature = self.open_file(name, maximum, expected_size=expected_size)
        try:
            with os.fdopen(fd, "rb", closefd=False) as stream:
                raw = stream.read(maximum + 1)
            _require(len(raw) == signature[4] and len(raw) <= maximum, "store file changed/grew during read")
            self.check_file(name, fd, signature)
            self.files[name] = signature
            self.assert_unchanged()
            return raw
        finally:
            os.close(fd)


def _split_counts(value: object, maximum: int) -> dict:
    _require(type(value) is dict and set(value) == set(SPLITS), "split count fields differ")
    for count in value.values():
        _integer(count, maximum, "split rows")
    return value


def _manifest(value: dict, binding: StoreBinding, profile: ShardProfile) -> None:
    _require(type(value) is dict and set(value) == _MANIFEST_FIELDS and value["schema"] == STORE_SCHEMA,
             "shard manifest schema/fields differ")
    _require(_canonical(value["binding"], MAX_MANIFEST_BYTES) == _canonical(binding.to_dict(), MAX_MANIFEST_BYTES)
             and _canonical(value["profile"], MAX_MANIFEST_BYTES) == _canonical(profile.to_dict(), MAX_MANIFEST_BYTES),
             "manifest changed its externally supplied source/authority/lineage/schema/profile binding")
    _require(value["structural_only"] is True and value["native_admission_performed"] is False
             and value["training_authorized"] is False and value["deduplication"] == _DEDUPLICATION,
             "structural store cannot attest native admission or training authorization")
    shards = value["shards"]
    _require(type(shards) is list and len(shards) <= profile.max_shards, "manifest shard count exceeds bound")
    total_rows, total_bytes, splits = 0, 0, _counts()
    for index, shard in enumerate(shards, 1):
        _require(type(shard) is dict and set(shard) == _SHARD_FIELDS
                 and shard["file"] == f"shard-{index:06d}.jsonl", "shard inventory/order/fields differ")
        _hash(shard["sha256"], "shard")
        total_rows += _integer(shard["rows"], profile.max_rows_per_shard, "shard rows", minimum=1)
        total_bytes += _integer(shard["bytes"], profile.max_shard_bytes, "shard bytes", minimum=1)
        counts = _split_counts(shard["split_rows"], profile.max_rows_per_shard)
        _require(sum(counts.values()) == shard["rows"], "shard split counts differ")
        for split in SPLITS:
            splits[split] += counts[split]
    _integer(value["total_rows"], profile.max_total_rows, "total rows")
    _integer(value["total_bytes"], profile.max_total_bytes, "total bytes")
    _split_counts(value["split_rows"], profile.max_total_rows)
    _require(value["total_rows"] == total_rows and value["total_bytes"] == total_bytes
             and value["split_rows"] == splits, "manifest aggregate counts differ")


def _stream_rows(stream, binding: StoreBinding, profile: ShardProfile) -> Iterator[tuple[dict, bytes]]:
    while True:
        raw = stream.readline(profile.max_row_bytes + 1)
        if not raw:
            return
        _require(len(raw) <= profile.max_row_bytes and raw.endswith(b"\n"), "oversized or unterminated JSONL row")
        row = _decode(raw[:-1], profile.max_row_bytes - 1)
        _require(_row(row, binding, profile) == raw, "JSONL rows must use exact canonical UTF8 plus LF")
        yield row, raw


def _scan_all(tree: _Tree, manifest: dict, binding: StoreBinding, profile: ShardProfile) -> None:
    identities = _IdentityIndex(profile.max_total_rows)
    for shard in manifest["shards"]:
        name, hasher, count, byte_count, splits = shard["file"], hashlib.sha256(), 0, 0, _counts()
        fd, signature = tree.open_file(name, profile.max_shard_bytes, expected_size=shard["bytes"])
        try:
            with os.fdopen(fd, "rb", closefd=False) as stream:
                for row, raw in _stream_rows(stream, binding, profile):
                    identities.add(row)
                    count += 1
                    byte_count += len(raw)
                    _require(count <= profile.max_rows_per_shard and byte_count <= profile.max_shard_bytes,
                             "shard streaming limits exceeded")
                    splits[row["split"]] += 1
                    hasher.update(raw)
            tree.check_file(name, fd, signature)
            _require(count == shard["rows"] and byte_count == shard["bytes"] and splits == shard["split_rows"]
                     and hasher.hexdigest() == shard["sha256"], "shard raw hash/rows/splits differ")
            tree.files[name] = signature
        finally:
            os.close(fd)
    tree.assert_unchanged()


class _Snapshot:
    def __init__(self, path: Path, binding: StoreBinding, profile: ShardProfile, expected_manifest_sha256: str):
        _arguments(binding, profile)
        _hash(expected_manifest_sha256, "externally pinned RAW manifest")
        self.tree, self.manifest, self.raw = _Tree(path), None, None
        try:
            names = self.tree.inventory(profile, manifest=True)
            _require(MANIFEST_NAME in names, "incomplete store: no committed manifest")
            raw = self.tree.read_file(MANIFEST_NAME, MAX_MANIFEST_BYTES)
            _require(hashlib.sha256(raw).hexdigest() == expected_manifest_sha256, "external RAW manifest SHA differs")
            manifest = _decode(raw, MAX_MANIFEST_BYTES)
            _require(raw == _manifest_bytes(manifest), "manifest is not canonical UTF8 plus LF")
            _manifest(manifest, binding, profile)
            expected = {MANIFEST_NAME} | {shard["file"] for shard in manifest["shards"]}
            _require(names == expected, "closed manifest/shard inventory differs")
            _scan_all(self.tree, manifest, binding, profile)
            _require(self.tree.inventory(profile, manifest=True) == expected, "store inventory changed after validation")
            self.manifest, self.raw = manifest, raw
        except BaseException:
            self.tree.close()
            raise

    def close(self):
        self.tree.close()


def validate_store(path: Path | str, *, binding: StoreBinding, expected_manifest_sha256: str,
                   profile: ShardProfile = DEFAULT_PROFILE) -> dict:
    """Validate all bytes/rows; no payload flag is a native-proof certificate."""
    snapshot = _Snapshot(_path(path), binding, profile, expected_manifest_sha256)
    try:
        snapshot.tree.assert_unchanged()
        return {"schema": VALIDATION_SCHEMA, "status": "structurally-validated",
                "manifest_sha256": hashlib.sha256(snapshot.raw).hexdigest(), "manifest": snapshot.manifest,
                "all_shards_validated": True, "native_admission_performed": False,
                "training_authorized": False, "proof_or_semantic_lineage_verification_performed": False}
    finally:
        snapshot.close()


def iter_rows(path: Path | str, *, binding: StoreBinding, expected_manifest_sha256: str,
              profile: ShardProfile = DEFAULT_PROFILE, split: str | None = None) -> Iterator[dict]:
    """Yield verified snapshot bytes only, after global preflight of ALL splits.

Each shard is fully reread and hashed before its first yield. A caller may
retain yielded rows, but this iterator retains at most one bounded shard and
one decoded row; it never caches a corpus or trusts a saved verified flag.
"""
    _require(split is None or type(split) is str and split in SPLITS, "unknown requested data split")
    snapshot = _Snapshot(_path(path), binding, profile, expected_manifest_sha256)
    try:
        manifest, tree = snapshot.manifest, snapshot.tree
        expected = {MANIFEST_NAME} | {shard["file"] for shard in manifest["shards"]}
        for shard in manifest["shards"]:
            _require(tree.inventory(profile, manifest=True) == expected, "store inventory changed before shard iteration")
            raw = tree.read_file(shard["file"], profile.max_shard_bytes, expected_size=shard["bytes"])
            _require(hashlib.sha256(raw).hexdigest() == shard["sha256"], "shard changed between validation and iteration")
            # The immutable buffer is authenticated before any of its rows can
            # reach a trainer, even if an external writer later changes disk.
            with io.BytesIO(raw) as stream:
                for row, _line in _stream_rows(stream, binding, profile):
                    if split is None or row["split"] == split:
                        yield row
            del raw
            tree.assert_unchanged()
        _require(tree.inventory(profile, manifest=True) == expected, "store inventory changed after iteration")
    finally:
        snapshot.close()


def _write_all(fd: int, raw: bytes) -> None:
    view = memoryview(raw)
    while view:
        size = os.write(fd, view)
        _require(type(size) is int and size > 0, "short/failed store write")
        view = view[size:]


def _new_file(tree: _Tree, name: str) -> int:
    tree.assert_unchanged()
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=tree.fd)
    try:
        info = os.fstat(fd)
        _require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == 0,
                 "new store file is not fresh/single-link")
        _require(_signature(info) == _signature(os.stat(name, dir_fd=tree.fd, follow_symlinks=False)),
                 "new store file was replaced")
        return fd
    except BaseException:
        os.close(fd)
        raise


class _ShardWriter:
    def __init__(self, tree: _Tree, index: int):
        self.tree, self.name = tree, f"shard-{index:06d}.jsonl"
        self.fd = _new_file(tree, self.name)
        self.hasher, self.rows, self.bytes, self.splits = hashlib.sha256(), 0, 0, _counts()
        info = os.fstat(self.fd)
        self.identity = (info.st_dev, info.st_ino)

    def check(self):
        held, named = os.fstat(self.fd), os.stat(self.name, dir_fd=self.tree.fd, follow_symlinks=False)
        _require(stat.S_ISREG(named.st_mode) and held.st_nlink == named.st_nlink == 1
                 and (held.st_dev, held.st_ino) == (named.st_dev, named.st_ino) == self.identity
                 and held.st_size == named.st_size == self.bytes, "shard changed during streaming publication")

    def append(self, row: dict, raw: bytes):
        self.check()
        _write_all(self.fd, raw)
        self.hasher.update(raw)
        self.rows += 1
        self.bytes += len(raw)
        self.splits[row["split"]] += 1
        self.check()

    def finish(self) -> dict:
        self.check()
        os.fsync(self.fd)
        self.tree.assert_unchanged()
        self.check()
        result = {"file": self.name, "sha256": self.hasher.hexdigest(), "bytes": self.bytes,
                  "rows": self.rows, "split_rows": dict(self.splits)}
        self.close()
        return result

    def close(self):
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1


def _publish_manifest(tree: _Tree, manifest: dict, profile: ShardProfile) -> None:
    raw = _manifest_bytes(manifest)
    temporary = ".manifest-" + uuid.uuid4().hex + ".tmp"
    fd = _new_file(tree, temporary)
    try:
        _write_all(fd, raw)
        os.fsync(fd)
        info = os.fstat(fd)
        _require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == len(raw)
                 and _signature(info) == _signature(os.stat(temporary, dir_fd=tree.fd, follow_symlinks=False)),
                 "temporary manifest changed before publication")
        tree.assert_unchanged()
        # Unlike replace/rename, link fails atomically if manifest already
        # exists. An interrupted two-link transaction is rejected by readers.
        os.link(temporary, MANIFEST_NAME, src_dir_fd=tree.fd, dst_dir_fd=tree.fd, follow_symlinks=False)
        named = os.stat(MANIFEST_NAME, dir_fd=tree.fd, follow_symlinks=False)
        staged = os.stat(temporary, dir_fd=tree.fd, follow_symlinks=False)
        _require(stat.S_ISREG(named.st_mode) and named.st_nlink == staged.st_nlink == 2
                 and (named.st_dev, named.st_ino) == (staged.st_dev, staged.st_ino) == (info.st_dev, info.st_ino),
                 "manifest no-replace transaction identity changed")
        os.unlink(temporary, dir_fd=tree.fd)
        os.fsync(tree.fd)
        tree.assert_unchanged()
        _require(tree.inventory(profile, manifest=True) == {MANIFEST_NAME} | {s["file"] for s in manifest["shards"]},
                 "store inventory changed during publication")
        _require(tree.read_file(MANIFEST_NAME, MAX_MANIFEST_BYTES) == raw, "published manifest bytes differ")
    finally:
        os.close(fd)


def publish_store(path: Path | str, rows: Iterable[dict], *, binding: StoreBinding,
                  profile: ShardProfile = DEFAULT_PROFILE) -> dict:
    """Publish a NEW store. Return manifest; use manifest_raw_sha256 for its pin.

No existing directory is adopted, replaced, cleaned, resumed or repaired.
The caller, not this structural writer, must independently verify payloads.
"""
    _arguments(binding, profile)
    path = _path(path)
    iterator = iter(rows)
    with _Tree(path.parent) as parent:
        try:
            os.stat(path.name, dir_fd=parent.fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ShardStoreError("destination already exists; no overwrite/adoption/resume")
        parent.assert_unchanged()
        os.mkdir(path.name, mode=0o700, dir_fd=parent.fd)
        os.fsync(parent.fd)
        made = os.stat(path.name, dir_fd=parent.fd, follow_symlinks=False)
        with _Tree(path) as tree:
            held = os.fstat(tree.fd)
            _require(stat.S_ISDIR(made.st_mode) and (made.st_dev, made.st_ino) == (held.st_dev, held.st_ino),
                     "new store directory was replaced")
            writer, shards, identities = None, [], _IdentityIndex(profile.max_total_rows)
            total_rows, total_bytes, splits = 0, 0, _counts()
            try:
                for row in iterator:
                    raw = _row(row, binding, profile)
                    identities.add(row)
                    _require(total_rows < profile.max_total_rows and total_bytes + len(raw) <= profile.max_total_bytes,
                             "total store rows/bytes exceed profile limits")
                    if writer is not None and (writer.bytes + len(raw) > profile.max_shard_bytes
                                               or writer.rows >= profile.max_rows_per_shard):
                        shards.append(writer.finish())
                        writer = None
                    if writer is None:
                        _require(len(shards) < profile.max_shards, "shard count exceeds profile limit")
                        writer = _ShardWriter(tree, len(shards) + 1)
                    writer.append(row, raw)
                    total_rows += 1
                    total_bytes += len(raw)
                    splits[row["split"]] += 1
                if writer is not None:
                    shards.append(writer.finish())
                    writer = None
            finally:
                if writer is not None:
                    writer.close()
            del identities
            manifest = {"schema": STORE_SCHEMA, "binding": binding.to_dict(), "profile": profile.to_dict(),
                        "shards": shards, "total_rows": total_rows, "total_bytes": total_bytes, "split_rows": splits,
                        "deduplication": _DEDUPLICATION, "structural_only": True,
                        "native_admission_performed": False, "training_authorized": False}
            _manifest(manifest, binding, profile)
            expected = {shard["file"] for shard in shards}
            _require(tree.inventory(profile, manifest=False) == expected, "staging inventory differs before commit")
            _scan_all(tree, manifest, binding, profile)
            _require(tree.inventory(profile, manifest=False) == expected, "staging inventory changed during validation")
            parent.assert_unchanged()
            _publish_manifest(tree, manifest, profile)
            parent.assert_unchanged()
            return manifest


__all__ = ["StoreBinding", "ShardProfile", "ShardStoreError", "DEFAULT_PROFILE", "SCALE_100K_V1", "SPLITS",
           "publish_store", "validate_store", "iter_rows", "manifest_raw_sha256"]
