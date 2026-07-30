#!/usr/bin/env python3
"""Verify the exact immutable morning diagnostic adapter before publication."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from typing import Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from training.peano_policy.manifest import (  # noqa: E402
    require_safetensors_adapter,
    sha256_json,
    verify_artifact_directory,
)


@dataclass(frozen=True, slots=True)
class AdapterSeal:
    file_sizes: Mapping[str, int]
    top_level_hashes: Mapping[str, str]
    total_bytes: int
    manifest_sha256: str
    adapter_model_sha256: str
    adapter_aggregate_sha256: str
    tokenizer_aggregate_sha256: str
    base_model_id: str
    base_model_revision: str
    base_config_sha256: str
    adapter_tensors: int
    adapter_tensor_names_sha256: str


MORNING_ADAPTER_SEAL = AdapterSeal(
    file_sizes={
        "adapter/README.md": 5_194,
        "adapter/adapter_config.json": 903,
        "adapter/adapter_model.safetensors": 139_512_976,
        "morning-diagnostic.json": 473,
        "morning-reload-probe.json": 718,
        "run-identity.json": 1_429_261,
        "tokenizer/added_tokens.json": 707,
        "tokenizer/chat_template.jinja": 4_116,
        "tokenizer/merges.txt": 1_671_853,
        "tokenizer/special_tokens_map.json": 616,
        "tokenizer/tokenizer.json": 11_422_654,
        "tokenizer/tokenizer_config.json": 5_407,
        "tokenizer/vocab.json": 2_776_833,
        "training-manifest.json": 1_471_010,
    },
    top_level_hashes={
        "morning-diagnostic.json": (
            "d570fdbce29bc0284c9f672573da0abae06335dbdcc0f9afc7b8481a49647f64"
        ),
        "morning-reload-probe.json": (
            "6f745a13c0fceab4aff4ac2292e8b8fdec597c9a96b1b3aae4e1981e0af6937d"
        ),
        "run-identity.json": (
            "ad7c638fca2a6f6913c924ee7ae8345cdfb395730e831ebc8c12b2da25bb50ed"
        ),
        "training-manifest.json": (
            "68d3ba2bfe080d83995bdd59eb3eb516a22d268276f78b17350c262d5ff22302"
        ),
    },
    total_bytes=158_302_721,
    manifest_sha256=(
        "68d3ba2bfe080d83995bdd59eb3eb516a22d268276f78b17350c262d5ff22302"
    ),
    adapter_model_sha256=(
        "817e4f4bf8edb9d47511533c6ef1a9810aa9f0f2353fd4de57af97c82e632324"
    ),
    adapter_aggregate_sha256=(
        "aa588058dae6df8f82bb319b8cd7c107b1b6c6016ab4737b50af701aebaaa4d2"
    ),
    tokenizer_aggregate_sha256=(
        "2c5206dc7dda009d1a466348530a56c21f68d68057115142b2cd121838cf3f5e"
    ),
    base_model_id="Qwen/Qwen3-1.7B-Base",
    base_model_revision="ea980cb0a6c2ae4b936e82123acc929f1cec04c1",
    base_config_sha256=(
        "a325c9f27de176887b8ca7f68d21714247f9c8106e8c120219789338da9a5dcd"
    ),
    adapter_tensors=392,
    adapter_tensor_names_sha256=(
        "db4186653e9c7017cea7d4f7485421842b851aecc96c92cda259e55ba73d8792"
    ),
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _inventory(root: Path) -> tuple[dict[str, int], set[str]]:
    root_status = root.lstat()
    if not stat.S_ISDIR(root_status.st_mode) or root.is_symlink():
        raise ValueError("adapter root must be one plain directory")
    files: dict[str, int] = {}
    directories: set[str] = set()
    for current, directory_names, file_names in os.walk(
        root, topdown=True, followlinks=False
    ):
        current_path = Path(current)
        for name in directory_names:
            path = current_path / name
            status = path.lstat()
            if path.is_symlink() or not stat.S_ISDIR(status.st_mode):
                raise ValueError(f"adapter tree contains an unsafe directory: {path}")
            directories.add(path.relative_to(root).as_posix())
        for name in file_names:
            path = current_path / name
            status = path.lstat()
            if path.is_symlink() or not stat.S_ISREG(status.st_mode):
                raise ValueError(f"adapter tree contains an unsafe file: {path}")
            files[path.relative_to(root).as_posix()] = status.st_size
    return files, directories


def _json_object(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON artifact {path.name}: {exc}") from None
    if type(value) is not dict:
        raise ValueError(f"JSON artifact must be an object: {path.name}")
    return value


def verify_adapter(
    adapter_dir: Path,
    *,
    seal: AdapterSeal = MORNING_ADAPTER_SEAL,
) -> dict[str, object]:
    """Verify structure, bytes, closed-directory manifests, and authority."""

    if adapter_dir.is_symlink():
        raise ValueError("adapter root must not be a symlink")
    root = adapter_dir.resolve(strict=True)
    observed_sizes, observed_directories = _inventory(root)
    expected_names = set(seal.file_sizes)
    if set(observed_sizes) != expected_names:
        missing = sorted(expected_names - set(observed_sizes))
        extra = sorted(set(observed_sizes) - expected_names)
        raise ValueError(f"adapter file tree mismatch; missing={missing}; extra={extra}")
    expected_directories = {
        parent.as_posix()
        for name in expected_names
        for parent in Path(name).parents
        if parent.as_posix() != "."
    }
    if observed_directories != expected_directories:
        raise ValueError("adapter directory tree contains missing or extra entries")
    for name, expected_size in seal.file_sizes.items():
        if observed_sizes[name] != expected_size:
            raise ValueError(
                f"adapter file size mismatch: {name}: "
                f"{observed_sizes[name]} != {expected_size}"
            )
    observed_total = sum(observed_sizes.values())
    if observed_total != seal.total_bytes:
        raise ValueError(
            f"adapter byte total mismatch: {observed_total} != {seal.total_bytes}"
        )

    for name, expected_hash in seal.top_level_hashes.items():
        observed_hash = _sha256_file(root / name)
        if observed_hash != expected_hash:
            raise ValueError(f"adapter artifact hash mismatch: {name}")
    if _sha256_file(root / "training-manifest.json") != seal.manifest_sha256:
        raise ValueError("training manifest seal mismatch")

    manifest = _json_object(root / "training-manifest.json")
    base = manifest.get("base_model")
    adapter = manifest.get("adapter")
    tokenizer = manifest.get("tokenizer")
    diagnostic = manifest.get("diagnostic")
    if not all(type(item) is dict for item in (base, adapter, tokenizer, diagnostic)):
        raise ValueError("training manifest lacks sealed model artifact records")
    assert isinstance(base, dict)
    assert isinstance(adapter, dict)
    assert isinstance(tokenizer, dict)
    assert isinstance(diagnostic, dict)
    if (
        manifest.get("v") != 1
        or base.get("id") != seal.base_model_id
        or base.get("requested_revision") != seal.base_model_revision
        or base.get("resolved_snapshot_hash") != seal.base_model_revision
        or base.get("config_sha256") != seal.base_config_sha256
    ):
        raise ValueError("training manifest base-model identity mismatch")
    tokenizer_artifacts = tokenizer.get("artifacts")
    if type(tokenizer_artifacts) is not dict:
        raise ValueError("training manifest tokenizer artifact record is malformed")
    if (
        adapter.get("sha256") != seal.adapter_aggregate_sha256
        or tokenizer_artifacts.get("sha256") != seal.tokenizer_aggregate_sha256
    ):
        raise ValueError("training manifest artifact aggregate mismatch")
    require_safetensors_adapter(adapter)
    verify_artifact_directory(root, adapter, "adapter")
    verify_artifact_directory(root, tokenizer_artifacts, "tokenizer")
    if (
        adapter.get("files", {}).get("adapter/adapter_model.safetensors")
        != seal.adapter_model_sha256
        or _sha256_file(root / "adapter" / "adapter_model.safetensors")
        != seal.adapter_model_sha256
    ):
        raise ValueError("adapter safetensors identity mismatch")

    diagnostic_core = dict(diagnostic)
    claimed_diagnostic_hash = diagnostic_core.pop("diagnostic_sha256", None)
    tensor_audit = diagnostic.get("adapter_tensor_audit")
    reload_probe = diagnostic.get("reload_probe")
    if (
        diagnostic.get("format") != "peano-policy-v3-morning-diagnostic"
        or diagnostic.get("v") != 1
        or diagnostic.get("status") != "completed-diagnostic-not-production"
        or type(claimed_diagnostic_hash) is not str
        or sha256_json(diagnostic_core) != claimed_diagnostic_hash
        or type(tensor_audit) is not dict
        or tensor_audit.get("sha256") != seal.adapter_model_sha256
        or tensor_audit.get("tensors") != seal.adapter_tensors
        or tensor_audit.get("dtypes") != {"torch.float32": seal.adapter_tensors}
        or tensor_audit.get("tensor_names_sha256")
        != seal.adapter_tensor_names_sha256
        or type(reload_probe) is not dict
        or reload_probe.get("path") != "morning-reload-probe.json"
        or reload_probe.get("sha256")
        != seal.top_level_hashes["morning-reload-probe.json"]
    ):
        raise ValueError("diagnostic authority is incomplete or inconsistent")

    sidecar = _json_object(root / "morning-diagnostic.json")
    sidecar_manifest = sidecar.get("training_manifest")
    if (
        sidecar.get("format") != diagnostic.get("format")
        or sidecar.get("v") != 1
        or sidecar.get("status") != diagnostic.get("status")
        or sidecar.get("diagnostic_sha256") != claimed_diagnostic_hash
        or type(sidecar_manifest) is not dict
        or sidecar_manifest.get("sha256") != seal.manifest_sha256
    ):
        raise ValueError("morning diagnostic sidecar does not bind the manifest")
    probe = _json_object(root / "morning-reload-probe.json")
    if (
        probe.get("format") != "peano-policy-v3-morning-reload-probe"
        or probe.get("v") != 1
        or probe.get("status") != "probe-completed"
        or probe.get("valid_single_tactic") is not True
        or probe.get("exact_match") is not True
        or probe.get("expected_tactic") != probe.get("parsed_tactic")
    ):
        raise ValueError("morning reload probe is not a successful exact probe")

    return {
        "format": "peano-policy-morning-adapter-verification",
        "v": 1,
        "status": "verified",
        "directory": str(root),
        "files": len(observed_sizes),
        "bytes": observed_total,
        "training_manifest_sha256": seal.manifest_sha256,
        "adapter_sha256": seal.adapter_model_sha256,
        "base_model": {
            "id": seal.base_model_id,
            "revision": seal.base_model_revision,
        },
        "diagnostic_status": diagnostic["status"],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("adapter", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        record = verify_adapter(args.adapter)
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(f"adapter verification failed: {exc}") from None
    print(json.dumps(record, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
