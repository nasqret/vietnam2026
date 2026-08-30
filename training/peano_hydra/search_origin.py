"""Authenticate the saved corrective adapter without relabelling its origin.

Preparation freezes original Git bytes and invokes ONE unchanged original
validator in the existing bounded child. It never writes the old source,
preparation or model. Receipt reuse rehashes inputs without native/model work.
All locations are explicit; relocation never searches for replacement inputs.
"""
from __future__ import annotations

from contextlib import ExitStack
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import secrets

from training.peano_hydra import origin_bridge as bridge


IDENTITY_SCHEMA = "peano-hydra-corrected-search-origin-identity-v1"
REFERENCE_SCHEMA = "peano-hydra-corrected-search-origin-reference-v1"
FAILURE_SCHEMA = "peano-hydra-corrected-search-origin-incomplete-v1"
SOURCE_COMMIT = "5a197363745c61156ce86d64a880fd47b5cb90e3"
PREPARATION_RELATIVE = "_deploy/hydra-corrective-v2/preparation"
PREPARATION_SHA256 = "b8e73c7063ce962bb1542c903ae8b441c69d254b2933548d8e89795cf25ca114"
SOURCE_DATA_RELATIVE = "_deploy/hydra-corrective-v2/source"
SOURCE_DATA_MANIFEST_SHA256 = "3e7fccb43804f5272a61282005c961b492ef891dbb37998f1c4a81ee9dfb4ef4"
ADAPTER_MANIFEST_SHA256 = "172a6928710192c5348dcd7b04f71e6d4d3f75dfa1ab0f7f5add601769704a7c"
EPOCH_SHA256 = "a96223a021edc556ed7620a87b4c00e5817ba169af4a1db093fa7a81847e082e"
AUTHORITY_PROFILE = "peano-authority-primitive-v1"
MODEL = {"model_id": "Qwen/Qwen3-1.7B-Base", "revision": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"}
ARTIFACT_SHA256 = {
    "adapter": "4ad0af7b07078a4812ac627b71941d4acec0f4fa9c8fe74723b6606ec2c27310",
    "tokenizer": "2c5206dc7dda009d1a466348530a56c21f68d68057115142b2cd121838cf3f5e",
}
SOURCE_MANIFEST_FILENAME = "source-manifest.json"
RECEIPT_FILENAME = "origin-receipt.json"
REFERENCE_FILENAME = "manifest.json"
WITNESS_RELATIVE = "artifacts/peano-hydra/native-search-repair-2026-08-28/witness-fixture-02"
WITNESS_FILES = {
    "manifest.json": {"bytes": 10335, "sha256": "7a132a61be1d17e6834034d79ff547635b0ff3fb7abbd34e452b9add912e6970"},
    "plan.json": {"bytes": 36122, "sha256": "35688fdcf73aa58806f2edc942b3c184cd3aebd02e343333be4ed8fa20461a12"},
    "coverage.json": {"bytes": 2911, "sha256": "6abb1ae358bd6d6ba2c633a2fcded168e253193a686b33f05f7e0ebc945d6abb"},
    "proofs.json": {"bytes": 34849, "sha256": "a4153527d280ebdb57a56fb683a8bf2c77bbc01644d21ca052ca3cbfed3a09c9"},
    "sft.jsonl": {"bytes": 159864, "sha256": "614d26c768e8115902f8d180fe716c08b35680aee421691b1b40f6862ad227ce"},
}
CLAIMS = {
    "original_inputs_modified": False, "training_performed": False,
    "model_inference_performed": False, "gpu_allocation_authorized": False,
    "remote_transfer_authorized": False, "old_checkpoint_resume_authorized": False,
    "new_training_authorized": False, "engine_equivalence_claimed": False,
    "research_claim_eligible": False,
}
_MANIFEST_FIELDS = {
    "schema", "status", "reference", "locations", "files", "witness_origin",
    "origin_sha256", "claims", "manifest_sha256",
}
_BUNDLE_FILES = {SOURCE_MANIFEST_FILENAME, RECEIPT_FILENAME, REFERENCE_FILENAME}


class SearchOriginError(ValueError):
    def __init__(self, message: str, *, observation: dict | None = None):
        super().__init__(message)
        self.observation = observation


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SearchOriginError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _same(left: object, right: object) -> bool:
    return bridge._canonical(left) == bridge._canonical(right)


def _file(raw: bytes) -> dict:
    return {"bytes": len(raw), "sha256": _sha(raw)}


def witness_origin_record() -> dict:
    """The five independently pinned ancillary inputs, not new teacher data."""
    return json.loads(bridge._canonical({"directory": WITNESS_RELATIVE, "files": WITNESS_FILES}))


def _witness(tree: bridge._Tree) -> dict:
    expected = {WITNESS_RELATIVE + "/" + name for name in WITNESS_FILES}
    _require(tree.inventory(WITNESS_RELATIVE, maximum=5) == expected,
             "frozen witness origin inventory changed")
    for name, descriptor in WITNESS_FILES.items():
        actual, _ = tree.fingerprint(WITNESS_RELATIVE + "/" + name, maximum=descriptor["bytes"])
        _require(_same(bridge._small_identity(actual), descriptor), "frozen witness origin bytes changed")
    tree.assert_unchanged()
    return witness_origin_record()


def _pin_inputs(source: bridge._Tree, adapter: bridge._Tree) -> None:
    for path, expected in (
        (PREPARATION_RELATIVE + "/manifest.json", PREPARATION_SHA256),
        (SOURCE_DATA_RELATIVE + "/manifest.json", SOURCE_DATA_MANIFEST_SHA256),
    ):
        _require(_sha(source.read(path, bridge.MAX_MANIFEST_BYTES)) == expected,
                 "saved corrective preparation/source manifest differs from its fixed pin")
    _require(_sha(adapter.read("manifest.json", bridge.MAX_MANIFEST_BYTES)) == ADAPTER_MANIFEST_SHA256,
             "saved corrective adapter manifest differs from its fixed pin")
    _witness(source)
    source.assert_unchanged()
    adapter.assert_unchanged()


def build_request(source_root: Path, source_manifest: Path, source_manifest_sha256: str,
                  adapter_manifest: Path) -> bridge.OriginRequest:
    """Build only this fixed origin request; perform no native/model work."""
    source_root = bridge._absolute(source_root)
    source_manifest = bridge._absolute(source_manifest)
    _require(source_manifest.name == SOURCE_MANIFEST_FILENAME, "source manifest must use its fixed bundle filename")
    return bridge.OriginRequest(
        source_root=source_root, source_manifest=source_manifest,
        source_manifest_sha256=source_manifest_sha256, source_commit=SOURCE_COMMIT,
        preparation_directory=source_root / PREPARATION_RELATIVE,
        preparation_manifest_sha256=PREPARATION_SHA256,
        adapter_manifest=adapter_manifest, adapter_manifest_sha256=ADAPTER_MANIFEST_SHA256,
        authority_profile=AUTHORITY_PROFILE,
    )


def _check_handle(handle: bridge.AuthenticatedOrigin, request: bridge.OriginRequest) -> dict:
    _require(type(handle) is bridge.AuthenticatedOrigin and handle.request == request,
             "authenticated handle changed the fixed corrective request")
    origin = handle.origin
    for name, expected in (
        ("schema", "peano-hydra-posttrain-adapter-v2"), ("version", "v25"),
        ("run_id", "corrective-v2"), ("training_source_commit", SOURCE_COMMIT),
        ("preparation_manifest_sha256", PREPARATION_SHA256),
        ("adapter_manifest_sha256", ADAPTER_MANIFEST_SHA256),
        ("epoch_sha256", EPOCH_SHA256), ("training_authority_profile", AUTHORITY_PROFILE),
        ("model", MODEL), ("research_claim_eligible", False),
    ):
        _require(name in origin and _same(origin[name], expected), "authenticated corrective origin changed " + name)
    artifacts = origin.get("artifacts")
    _require(type(artifacts) is dict and set(artifacts) == set(ARTIFACT_SHA256), "corrective artifact groups changed")
    for kind, expected in ARTIFACT_SHA256.items():
        _require(type(artifacts[kind]) is dict and artifacts[kind].get("root") == kind
                 and artifacts[kind].get("sha256") == expected, "corrective artifact tree identity changed")
    evidence = origin.get("training_evidence")
    _require(type(evidence) is dict, "corrective training evidence is missing")
    for name, expected in (("actual_optimizer_steps", 1117), ("expected_optimizer_steps", 1117),
                           ("training_rows", 8932), ("development_rows", 744)):
        _require(type(evidence.get(name)) is int and evidence[name] == expected,
                 "corrective training inventory changed")
    bridge._hash(origin.get("origin_sha256"), "authenticated origin SHA")
    return origin


@dataclass(frozen=True, slots=True)
class CorrectedOriginReference:
    request: bridge.OriginRequest
    receipt_path: Path
    receipt_sha256: str

    def __post_init__(self) -> None:
        _require(type(self.request) is bridge.OriginRequest, "reference needs an exact OriginRequest")
        expected = build_request(self.request.source_root, self.request.source_manifest,
                                 self.request.source_manifest_sha256, self.request.adapter_manifest)
        _require(self.request == expected, "reference changed a fixed corrected origin pin or path")
        path = bridge._absolute(self.receipt_path)
        _require(path.name == RECEIPT_FILENAME and path.parent == self.request.source_manifest.parent,
                 "receipt must be the fixed sibling of the source manifest")
        bridge._hash(self.receipt_sha256, "external corrected origin receipt SHA")
        object.__setattr__(self, "receipt_path", path)

    def to_dict(self) -> dict:
        """Portable identity excludes all physical source/model/evidence roots."""
        return {"schema": IDENTITY_SCHEMA, "request": self.request.to_dict(),
                "receipt_sha256": self.receipt_sha256}

    def load(self) -> bridge.AuthenticatedOrigin:
        """Rehash original inputs and witness bytes; never repeat native work."""
        with bridge._Tree(self.request.source_root) as source, bridge._Tree(self.request.adapter_manifest.parent) as adapter:
            _pin_inputs(source, adapter)
            handle = bridge.load_origin_receipt(self.receipt_path,
                expected_receipt_sha256=self.receipt_sha256, request=self.request)
            _check_handle(handle, self.request)
            _pin_inputs(source, adapter)
            return handle


def _explicit_location(value: object) -> Path:
    _require(type(value) is str and Path(value).is_absolute(), "saved locations must be explicit absolute paths")
    path = bridge._absolute(Path(value))
    _require(str(path) == value, "saved location is not canonical")
    return path


def load_reference(manifest_path: Path, expected_manifest_sha256: str, *,
                   source_root: Path | None = None,
                   adapter_manifest: Path | None = None) -> CorrectedOriginReference:
    """Load an externally pinned reference; relocation requires explicit roots."""
    path = bridge._absolute(manifest_path)
    _require(path.name == REFERENCE_FILENAME, "reference must name its fixed manifest.json")
    bridge._hash(expected_manifest_sha256, "external reference manifest SHA")
    with bridge._Tree(path.parent) as tree:
        _require(tree.inventory("", maximum=3) == _BUNDLE_FILES, "reference bundle is incomplete or has extra files")
        raw = tree.read(path.name, bridge.MAX_BUNDLE_MANIFEST_BYTES)
        _require(_sha(raw) == expected_manifest_sha256, "external reference manifest SHA differs")
        record = bridge._decode(raw, bridge.MAX_BUNDLE_MANIFEST_BYTES, "corrected origin reference")
        bridge._keys(record, _MANIFEST_FIELDS, "corrected reference")
        unsigned = dict(record)
        signed = unsigned.pop("manifest_sha256")
        _require(record["schema"] == REFERENCE_SCHEMA and record["status"] == "validated-original-origin"
                 and signed == bridge._digest(unsigned), "reference schema/status/self-hash changed")
        _require(_same(record["claims"], CLAIMS) and _same(record["witness_origin"], witness_origin_record()),
                 "reference changed claims or the frozen witness inventory")
        bridge._keys(record["locations"], {"source_root", "adapter_manifest"}, "reference locations")
        saved_source = _explicit_location(record["locations"]["source_root"])
        saved_adapter = _explicit_location(record["locations"]["adapter_manifest"])
        bridge._keys(record["files"], {SOURCE_MANIFEST_FILENAME, RECEIPT_FILENAME}, "reference payload inventory")
        for name, descriptor in record["files"].items():
            bridge._keys(descriptor, {"bytes", "sha256"}, "reference payload")
            maximum = bridge.MAX_BUNDLE_MANIFEST_BYTES if name == SOURCE_MANIFEST_FILENAME else bridge.MAX_RECEIPT_BYTES
            payload = tree.read(name, maximum)
            _require(_same(_file(payload), descriptor), "reference payload changed from its exact file identity")
        identity = record["reference"]
        bridge._keys(identity, {"schema", "request", "receipt_sha256"}, "portable reference identity")
        _require(identity["schema"] == IDENTITY_SCHEMA, "portable reference schema changed")
        request = build_request(
            saved_source if source_root is None else source_root,
            path.parent / SOURCE_MANIFEST_FILENAME,
            record["files"][SOURCE_MANIFEST_FILENAME]["sha256"],
            saved_adapter if adapter_manifest is None else adapter_manifest,
        )
        reference = CorrectedOriginReference(request, path.parent / RECEIPT_FILENAME,
                                             record["files"][RECEIPT_FILENAME]["sha256"])
        _require(_same(reference.to_dict(), identity), "reference changed original identity or receipt anchor")
        handle = reference.load()
        _require(handle.origin["origin_sha256"] == record["origin_sha256"], "reference changed authenticated origin identity")
        tree.assert_unchanged()
    return reference


def _check_output_parent(parent: bridge._Tree, protected: tuple[bridge._Tree, ...]) -> None:
    protected_ids = {(os.fstat(tree.directory("")).st_dev, os.fstat(tree.directory("")).st_ino)
                     for tree in protected}
    for descriptor in parent._fds:
        info = os.fstat(descriptor)
        _require((info.st_dev, info.st_ino) not in protected_ids,
                 "new evidence cannot be written inside preserved source/preparation/model inputs")
    for tree in (parent, *protected):
        tree.assert_unchanged()


def _write_new(tree: bridge._Tree, name: str, raw: bytes) -> None:
    """Atomic no-replace file publication in one held, freshly owned directory."""
    _require(type(raw) is bytes and len(raw) <= bridge.MAX_RECEIPT_BYTES,
             "origin metadata exceeds its publication bound")
    _require(name in _BUNDLE_FILES | {"failure.json"}, "unexpected origin publication filename")
    tree.assert_unchanged()
    directory = tree.directory("")
    temporary = "." + name + ".partial-" + secrets.token_hex(12)
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
    try:
        own = os.fstat(descriptor)
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(descriptor)
        current = os.stat(temporary, dir_fd=directory, follow_symlinks=False)
        _require((current.st_dev, current.st_ino) == (own.st_dev, own.st_ino), "temporary metadata identity changed")
        os.link(temporary, name, src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False)
    finally:
        current = os.stat(temporary, dir_fd=directory, follow_symlinks=False)
        if (current.st_dev, current.st_ino) == (own.st_dev, own.st_ino):
            os.unlink(temporary, dir_fd=directory)
        os.close(descriptor)
    os.fsync(directory)
    _require(tree.read(name, bridge.MAX_RECEIPT_BYTES) == raw, "published metadata differs from intended bytes")


def prepare_origin(source_root: Path, adapter_manifest: Path, output_directory: Path,
                   python: Path) -> CorrectedOriginReference:
    """Create one fresh reference bundle, with at most one bounded native check.

    The parent directory must already exist. Failure leaves an explicitly
    incomplete new directory and never retries. Only a closed, anchored
    three-file bundle can authorize reuse. Source freezing uses read-only Git subprocesses; authentication
    owns its one native child. Do not nest this orchestration in a supervisor
    that forbids child processes.
    """
    source_root, adapter_manifest = bridge._absolute(source_root), bridge._absolute(adapter_manifest)
    output, python = bridge._absolute(output_directory), bridge._absolute(python)
    _require(adapter_manifest.name == "manifest.json", "adapter must name its exact original manifest.json")
    with ExitStack() as stack:
        source = stack.enter_context(bridge._Tree(source_root))
        adapter = stack.enter_context(bridge._Tree(adapter_manifest.parent))
        parent = stack.enter_context(bridge._Tree(output.parent))
        protected = (source, adapter)
        _check_output_parent(parent, protected)
        _pin_inputs(source, adapter)
        os.mkdir(output.name, mode=0o700, dir_fd=parent.directory(""))
        os.fsync(parent.directory(""))
        tree = stack.enter_context(bridge._Tree(output))
        stage = "freeze-original-source"
        try:
            raw_source = bridge.freeze_origin_sources(source_root, expected_commit=SOURCE_COMMIT)
            _check_output_parent(parent, protected)
            _pin_inputs(source, adapter)
            _write_new(tree, SOURCE_MANIFEST_FILENAME, raw_source)
            request = build_request(source_root, output / SOURCE_MANIFEST_FILENAME, _sha(raw_source), adapter_manifest)
            stage = "authenticate-original-origin"
            handle = bridge.authenticate_origin(request, python=python)
            _require(handle.validation_mode == "fresh-original-validator", "preparation did not run its original validator")
            origin = _check_handle(handle, request)
            _pin_inputs(source, adapter)
            _check_output_parent(parent, protected)
            stage = "publish-reference"
            _write_new(tree, RECEIPT_FILENAME, handle.receipt_bytes)
            reference = CorrectedOriginReference(request, output / RECEIPT_FILENAME, handle.receipt_sha256)
            # A final byte-only pass closes the publication interval without a
            # second native replay or a process-wide/mutation-dependent cache.
            rechecked = reference.load()
            _require(rechecked.origin == origin, "original origin changed before reference publication")
            record = {
                "schema": REFERENCE_SCHEMA, "status": "validated-original-origin",
                "reference": reference.to_dict(),
                "locations": {"source_root": str(source_root), "adapter_manifest": str(adapter_manifest)},
                "files": {SOURCE_MANIFEST_FILENAME: _file(raw_source), RECEIPT_FILENAME: _file(handle.receipt_bytes)},
                "witness_origin": witness_origin_record(), "origin_sha256": origin["origin_sha256"],
                "claims": dict(CLAIMS),
            }
            record["manifest_sha256"] = bridge._digest(record)
            _check_output_parent(parent, protected)
            _pin_inputs(source, adapter)
            _require(tree.inventory("", maximum=2) == {SOURCE_MANIFEST_FILENAME, RECEIPT_FILENAME},
                     "incomplete reference directory acquired unexpected files")
            _write_new(tree, REFERENCE_FILENAME, bridge._canonical(record) + b"\n")
            _require(tree.inventory("", maximum=3) == _BUNDLE_FILES, "successful reference directory has extra files")
            tree.assert_unchanged()
            _check_output_parent(parent, protected)
            return reference
        except Exception as error:
            failure = {"schema": FAILURE_SCHEMA, "status": "incomplete", "stage": stage,
                       "error_type": type(error).__name__, "error": " ".join(str(error).split())[:3000],
                       "source_commit": SOURCE_COMMIT, "adapter_manifest_sha256": ADAPTER_MANIFEST_SHA256,
                       "claims": dict(CLAIMS), "automatic_retry": False,
                       "observation": getattr(error, "observation", None)}
            published = False
            try:
                _check_output_parent(parent, protected)
                tree.assert_unchanged()
                _write_new(tree, "failure.json", bridge._canonical(failure) + b"\n")
                published = True
            except (OSError, ValueError):
                # Never pursue evidence writing through replaced/unsafe paths.
                pass
            raise SearchOriginError("corrected origin preparation incomplete at " + stage,
                observation={"output_directory": str(output), "failure_evidence_published": published,
                             "stage": stage, "automatic_retry": False}) from error


__all__ = [
    "CorrectedOriginReference", "SearchOriginError", "build_request", "load_reference",
    "prepare_origin", "witness_origin_record", "SOURCE_COMMIT", "PREPARATION_RELATIVE",
    "PREPARATION_SHA256", "ADAPTER_MANIFEST_SHA256", "EPOCH_SHA256", "AUTHORITY_PROFILE",
    "MODEL", "ARTIFACT_SHA256", "IDENTITY_SCHEMA", "REFERENCE_SCHEMA", "CLAIMS",
]
