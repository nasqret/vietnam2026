#!/usr/bin/env python3
"""Copy the exact verified v31 readers into the dedicated faculty stage.

This is a transport/inventory check, not a proof checker or admission gate.
All theorem and definition bytes come from the separate same-live publication.
The existing staging recipe first retains the historical checkpoint routes and
the explicitly staged QR/k3b supplement. This additive overlay never deletes
them, touches the frozen source trees, or performs a remote write.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import os
from pathlib import Path
import tempfile

import build_constructive_completed_lower_hub_v31 as hub
import constructive_completed_lower_publication_v31 as publication


ROOT = hub.ROOT
STAGE = ROOT / "_deploy/proofs"


def _pins(manifest: dict) -> dict:
    pins = manifest.get("files")
    if (type(pins) is not dict or not 1 <= len(pins) <= 20000
            or type(manifest.get("file_count_excluding_manifest")) is not int
            or len(pins) != manifest["file_count_excluding_manifest"]):
        raise hub.DeliveryError("invalid reader inventory")
    for name, item in pins.items():
        if (not publication.safe_relative(name) or type(item) is not dict
                or set(item) != {"bytes", "sha256"}
                or type(item["bytes"]) is not int or not 0 < item["bytes"] <= 64 * 1024 * 1024
                or type(item["sha256"]) is not str or len(item["sha256"]) != 64):
            raise hub.DeliveryError("unsafe reader inventory entry")
    return pins


def source_inventory() -> tuple[dict[str, tuple[Path, dict]], dict]:
    """Verify all actual reader bytes before writing any public-stage bytes."""
    expected = hub.build_files()
    for path, payload in expected.items():
        if hub.read(path, 2 * 1024 * 1024) != payload:
            raise hub.DeliveryError("regenerate the current hub before staging")
    lock = publication.strict_json(expected[hub.LOCK])
    result = {}

    def add(destination: str, source: Path, binding: dict):
        if not publication.safe_relative(destination):
            raise hub.DeliveryError("unsafe staged path")
        raw = hub.read(source)
        if hub.pin(raw) != binding:
            raise hub.DeliveryError("published input differs from its manifest: " + str(source))
        prior = result.get(destination)
        if prior is not None and prior[1] != binding:
            raise hub.DeliveryError("reader packages disagree on a shared public asset: " + destination)
        result[destination] = (source, binding)

    for package in hub.PACKAGES:
        directory = ROOT / "book/_static" / package
        manifest_path = directory / "manifest.json"
        manifest_bytes = hub.read(manifest_path, 2 * 1024 * 1024)
        if hub.pin(manifest_bytes) != lock["reader_manifests"][package]:
            raise hub.DeliveryError("reader manifest changed after hub generation")
        manifest = publication.strict_json(manifest_bytes)
        pins = _pins(manifest)
        actual = set()
        for path in directory.rglob("*"):
            if path.is_symlink():
                raise hub.DeliveryError("linked entry in immutable reader tree")
            if path.is_file():
                actual.add(path.relative_to(directory).as_posix())
            elif not path.is_dir():
                raise hub.DeliveryError("special file in immutable reader tree")
        if actual != set(pins) | {"manifest.json"}:
            raise hub.DeliveryError("immutable reader tree has missing or extra files")
        for name, binding in pins.items():
            # Aggregate reader indexes are internal previews. The public root
            # has the full QR-derived hub, with all63 primary family links.
            if name == "index.html":
                if hub.pin(hub.read(directory / name)) != binding:
                    raise hub.DeliveryError("internal package index changed")
                continue
            destination = "release-v31/publication.json" if name == "publication.json" else name
            add(destination, directory / name, binding)
        short = "historical" if package == publication.HISTORICAL_OUTPUT_NAME else "completed-lower"
        add("release-v31/" + short + "-manifest.json", manifest_path, hub.pin(manifest_bytes))
    atlas = ROOT / "book/_static" / publication.ATLAS_NAME
    actual_atlas = {path.relative_to(atlas).as_posix() for path in atlas.rglob("*") if path.is_file()}
    if actual_atlas != set(hub.ATLAS_FILES):
        raise hub.DeliveryError("current campaign tree is not the exact four-file release")
    for name, binding in lock["atlas"].items():
        add("grand-campaign/" + name, atlas / name, binding)
    add("index.html", hub.HUB, lock["hub"])
    add("release-v31/manifest.json", hub.LOCK, hub.pin(expected[hub.LOCK]))
    record = lock["verification_record"]
    add("release-v31/alpha-v31-completed-lower-receipt-v1.json", ROOT / record["path"],
        {key: record[key] for key in ("bytes", "sha256")})
    return result, lock


def _destination(root: Path, relative: str, *, create: bool) -> Path:
    if not publication.safe_relative(relative):
        raise hub.DeliveryError("unsafe destination path")
    target = root / relative
    parent = root
    for part in Path(relative).parts[:-1]:
        parent /= part
        if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
            raise hub.DeliveryError("unsafe staged directory")
        if create:
            parent.mkdir(mode=0o755, exist_ok=True)
        if not parent.is_dir() or parent.stat().st_uid != os.getuid():
            raise hub.DeliveryError("staged directory has unsafe owner or type")
    if target.is_symlink() or (target.exists() and (not target.is_file() or target.stat().st_uid != os.getuid())):
        raise hub.DeliveryError("refusing to replace an unsafe staged file")
    return target


def _atomic_copy(source: Path, destination: Path, binding: dict) -> None:
    raw = hub.read(source)
    if hub.pin(raw) != binding:
        raise hub.DeliveryError("published source changed during staging")
    descriptor, temporary = tempfile.mkstemp(prefix=".v31-delivery-", dir=destination.parent)
    path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
        path.chmod(0o644)
        os.replace(path, destination)
    finally:
        if path.exists():
            path.unlink()


def _public_bytes(path: Path, binding: dict, *, selector: bytes | None) -> None:
    maximum = binding["bytes"] + (len(selector) if selector else 0)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > maximum:
        raise hub.DeliveryError("staged file has unsafe size or type")
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    if selector and selector in raw:
        if raw.count(selector) != 1:
            raise hub.DeliveryError("duplicate public Lean selector")
        raw = raw.replace(selector, b"", 1)
    if hub.pin(raw) != binding:
        raise hub.DeliveryError("staged file differs from the immutable publication: " + str(path))


def stage(root: Path, *, check: bool = False, api_url: str = "") -> int:
    if (root != STAGE or root.is_symlink() or not root.is_dir()
            or root.parent.is_symlink() or root.parent.parent != ROOT
            or root.stat().st_uid != os.getuid()):
        raise hub.DeliveryError("v31 delivery is limited to the ordinary _deploy/proofs directory")
    inventory, _ = source_inventory()
    from stage_public_lean_selector import _api_url, _overlay
    selector = _overlay(_api_url(api_url))
    # The root index becomes current last. A failed staging operation is not a
    # deployment and is safe to rerun from the unchanged immutable inputs.
    names = sorted(inventory, key=lambda name: (name == "index.html", name))
    for name in names:
        source, binding = inventory[name]
        target = _destination(root, name, create=not check)
        if check:
            _public_bytes(target, binding, selector=selector if target.suffix == ".html" else None)
        else:
            _atomic_copy(source, target, binding)
    # The supplement is deliberately outside the authenticated44-reader map;
    # it is retained by the original explicit PA staging, never invented here.
    return len(inventory)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=STAGE)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--api-url", default="")
    args = parser.parse_args(argv)
    chosen = args.root if args.root.is_absolute() else ROOT / args.root
    count = stage(chosen, check=args.check, api_url=args.api_url)
    print(f"Alpha v31 public byte inventory: PASS ({count} files, no proof admission or remote writes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
