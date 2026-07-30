#!/usr/bin/env python3
"""Download or offline-verify the one pinned Qwen base-model snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CACHE_ROOT = REPOSITORY_ROOT / ".cache" / "huggingface" / "hub"
MODEL_ID = "Qwen/Qwen3-1.7B-Base"
MODEL_REVISION = "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
MODEL_FILE = "model.safetensors"
MODEL_BYTES = 3_441_185_608
MODEL_SHA256 = "6df85b39330e5a425ee36253d0f894e4387e4f0a15b9c53cb467d668e6b3a841"
CONFIG_FILE = "config.json"
CONFIG_FILE_SHA256 = (
    "1bb33a92c3548fbc68b889b490e810440435253598835bd71dff0396060c12db"
)
GENERATION_CONFIG_FILE = "generation_config.json"
GENERATION_CONFIG_SHA256 = (
    "8c970692323e3ea0e9b8b0a4dca79388d31226e41f83c9fd6014804280ebf6e8"
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _snapshot_path(cache_root: Path) -> Path:
    return (
        cache_root
        / "models--Qwen--Qwen3-1.7B-Base"
        / "snapshots"
        / MODEL_REVISION
    )


def _require_plain_cache_parents(cache_root: Path, *, create: bool) -> None:
    repository = REPOSITORY_ROOT.resolve(strict=True)
    current = repository
    for part in cache_root.relative_to(REPOSITORY_ROOT).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"refusing symlinked model cache path: {current}")
        if not current.exists():
            if not create:
                raise FileNotFoundError(f"model cache is missing: {current}")
            current.mkdir()
        if not current.is_dir():
            raise ValueError(f"model cache component is not a directory: {current}")


def verify_snapshot(snapshot: Path) -> dict[str, object]:
    """Verify the pinned weight bytes and configuration without network I/O."""

    expected = snapshot.resolve(strict=True)
    if expected.name != MODEL_REVISION or not expected.is_dir():
        raise ValueError(f"unexpected model snapshot path: {expected}")
    model = expected / MODEL_FILE
    config = expected / CONFIG_FILE
    generation_config = expected / GENERATION_CONFIG_FILE
    if not model.is_file() or model.stat().st_size != MODEL_BYTES:
        raise ValueError("pinned model.safetensors is missing or has the wrong size")
    if _sha256_file(model) != MODEL_SHA256:
        raise ValueError("pinned model.safetensors failed SHA-256 verification")
    if not config.is_file() or _sha256_file(config) != CONFIG_FILE_SHA256:
        raise ValueError("pinned config.json failed SHA-256 verification")
    if (
        not generation_config.is_file()
        or _sha256_file(generation_config) != GENERATION_CONFIG_SHA256
    ):
        raise ValueError(
            "pinned generation_config.json failed SHA-256 verification"
        )
    try:
        config_record = json.loads(config.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"pinned config.json is invalid: {exc}") from None
    if type(config_record) is not dict or config_record.get("model_type") != "qwen3":
        raise ValueError("pinned config.json does not declare the Qwen3 architecture")
    return {
        "format": "peano-pinned-base-model",
        "v": 1,
        "status": "verified",
        "model_id": MODEL_ID,
        "revision": MODEL_REVISION,
        "snapshot": str(expected),
        "model_bytes": MODEL_BYTES,
        "model_sha256": MODEL_SHA256,
        "config_file_sha256": CONFIG_FILE_SHA256,
        "generation_config_sha256": GENERATION_CONFIG_SHA256,
    }


def prepare_snapshot(*, verify_only: bool) -> dict[str, object]:
    """Download the exact revision, or inspect the expected cache offline."""

    _require_plain_cache_parents(CACHE_ROOT, create=not verify_only)
    expected = _snapshot_path(CACHE_ROOT)
    if verify_only:
        snapshot = expected
    else:
        from huggingface_hub import snapshot_download

        downloaded = Path(
            snapshot_download(
                repo_id=MODEL_ID,
                revision=MODEL_REVISION,
                cache_dir=CACHE_ROOT,
            )
        )
        if downloaded.resolve(strict=True) != expected.resolve(strict=True):
            raise ValueError(
                "Hugging Face resolved a snapshot other than the pinned commit"
            )
        snapshot = downloaded
    record = verify_snapshot(snapshot)
    record["mode"] = "offline-verification" if verify_only else "download"
    return record


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="perform no Hub call; require the exact snapshot in the repo cache",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        record = prepare_snapshot(verify_only=args.verify_only)
    except (FileNotFoundError, ImportError, OSError, ValueError) as exc:
        raise SystemExit(f"pinned base-model preparation failed: {exc}") from None
    print(json.dumps(record, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
