#!/usr/bin/env python3
"""Hide public on-demand Lean controls without changing any proof page.

Preserve the checked layout stage and replace only its public selector asset.
The original local selector, backend, proof evidence and historical manifests
remain unchanged. The output is a separately checked presentation layer.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import signal
import sys
from tempfile import TemporaryDirectory
import time

from stage_proof_explorer_layout import (
    CPU_LIMITS, MAX_RSS, WALL_SECONDS, canonical, inventory, ordinary, pin, read, require,
)

ROOT = Path(__file__).resolve().parents[1]
BASE_MANIFEST = "presentation/layout-v1.json"
BASE_SHA256 = "14238ef05845f5a97c130814b93e1b65619c88ce7ca9c59cd2e825b4b9efca3f"
POLICY_MANIFEST = "presentation/lean-policy-v1.json"
PUBLIC_SELECTOR = "assets/lean-selector.js"
DISABLED_SELECTOR = "deploy/proofs/lean-selector-disabled.js"
LOCAL_SELECTOR = "book/_static/lean-selector/lean-selector.js"
CONTROLS = (
    "scripts/stage_public_proof_policy.py", DISABLED_SELECTOR, LOCAL_SELECTOR,
    "scripts/stage_proof_explorer_layout.py", "scripts/proof_explorer_layout.py",
    "scripts/constructive_alpha_v34_publication_process.py",
)


def validate_base(base, files, accepted_sha256):
    raw = read(base / BASE_MANIFEST)
    require(sha256(raw).hexdigest() == accepted_sha256, "unaccepted layout manifest")
    layout = json.loads(raw)
    require(layout.get("schema") == "peano-proof-explorer-layout-v1"
        and layout.get("presentation_only") is True
        and layout.get("proof_bytes_changed") is False
        and layout.get("original_assets_changed") is False
        and layout.get("alpha_admission_performed") is False
        and layout.get("stable_admission_performed") is False,
        "base is not the checked presentation-only layout")
    require(POLICY_MANIFEST not in files, "base already has a public Lean policy")
    require(files.get(PUBLIC_SELECTOR) == pin(read(ROOT / LOCAL_SELECTOR)),
        "base selector differs from the unchanged canonical local implementation")
    # The accepted layout manifest binds the entire preserved v34 inventory.
    # Undo its recorded HTML-only changes in the hash inventory, not on disk.
    original = {name: value for name, value in files.items() if name != BASE_MANIFEST}
    for name, change in layout["changed_files"].items():
        require(name.endswith(".html") and original.get(name) == change["after"],
            "base layout page differs: " + name)
        original[name] = change["before"]
    require(len(original) == layout["base_file_count"]
        and sha256(canonical(original)).hexdigest() == layout["base_inventory_sha256"],
        "base proof or asset inventory changed")
    return layout, pin(raw)


def stage(base, output, *, check=False, accepted_sha256=BASE_SHA256):
    base, output = Path(base).absolute(), Path(output).absolute()
    require(base != output and base not in output.parents and output not in base.parents,
        "public policy output must be separate from its preserved base")
    require(not output.is_symlink(), "linked public policy destination")
    ordinary(output.parent, directory=True)
    if not check:
        require(not output.exists(), "public policy output already exists; use --check")
    files = inventory(base)
    layout, base_pin = validate_base(base, files, accepted_sha256)
    replacement = read(ROOT / DISABLED_SELECTOR)
    require(len(replacement) <= 4096, "inactive public selector exceeds its size bound")
    controls = {name: pin(read(ROOT / name)) for name in CONTROLS}
    pages = []
    for name in files:
        if name.endswith(".html") and b'/proofs/assets/lean-selector.js' in read(base / name):
            pages.append(name)
    require(bool(pages), "base has no public selector consumers")
    families = sorted({name.split("/", 1)[0] for name in pages})
    require(set(families) <= set(layout["families"]), "unreviewed public selector family")
    changes = {PUBLIC_SELECTOR: {"before": files[PUBLIC_SELECTOR], "after": pin(replacement)}}
    record = dict(schema="peano-proof-public-lean-policy-v1", presentation_only=True,
        public_on_demand_builds=False, local_builder_changed=False,
        runtime_services_changed=False, generated_lean_live_links=False,
        proof_bytes_changed=False, html_bytes_changed=False,
        alpha_admission_performed=False, stable_admission_performed=False,
        base_manifest={"path": BASE_MANIFEST, **base_pin},
        base_inventory_sha256=sha256(canonical(files)).hexdigest(), base_file_count=len(files),
        selector_page_count=len(pages), families=families,
        changed_files=changes, controls=controls)
    manifest_bytes = canonical(record)

    def verify(directory):
        actual = inventory(directory)
        require(set(actual) == set(files) | {POLICY_MANIFEST}, "unexpected policy output files")
        for name, before in files.items():
            require(actual[name] == changes.get(name, {}).get("after", before),
                "public policy changed an unexpected byte: " + name)
        require(read(directory / POLICY_MANIFEST) == manifest_bytes, "public policy manifest differs")

    def rebind():
        require(inventory(base) == files, "preserved layout base changed during staging")
        require(all(pin(read(ROOT / name)) == value for name, value in controls.items()),
            "public policy controls changed during staging")

    if check:
        verify(output)
        rebind()
    else:
        with TemporaryDirectory(prefix=".public-proof-policy-", dir=output.parent) as temporary:
            candidate = Path(temporary) / "files"
            candidate.mkdir(mode=0o755)
            for name, before in files.items():
                raw = read(base / name)
                require(pin(raw) == before, "base changed before copying")
                destination = candidate / name
                destination.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
                with destination.open("xb") as stream:
                    stream.write(replacement if name == PUBLIC_SELECTOR else raw)
                destination.chmod(0o644)
                source = ROOT / DISABLED_SELECTOR if name == PUBLIC_SELECTOR else base / name
                info = ordinary(source)
                os.utime(destination, ns=(info.st_atime_ns, info.st_mtime_ns))
            destination = candidate / POLICY_MANIFEST
            with destination.open("xb") as stream:
                stream.write(manifest_bytes)
            destination.chmod(0o644)
            # New public directories must remain traversable even when the
            # operator's umask is restrictive; change only this new candidate.
            for directory in (candidate, *(path for path in candidate.rglob("*") if path.is_dir())):
                directory.chmod(0o755)
            verify(candidate)
            rebind()
            require(not output.exists() and not output.is_symlink(), "policy destination appeared")
            from constructive_alpha_v34_publication_process import _rename_new
            _rename_new(candidate, output)
    return dict(files=len(files) + 1, changed_files=1, html_bytes_changed=False,
        selector_pages=len(pages), family_count=len(families),
        public_on_demand_builds=False, check_only=check,
        manifest_sha256=sha256(manifest_bytes).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=ROOT / "_deploy/proofs-layout-v1")
    parser.add_argument("--output", type=Path, default=ROOT / "_deploy/proofs-public-v1")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU, CPU_LIMITS)
    signal.alarm(WALL_SECONDS)
    started = time.monotonic()
    result = stage(args.base, args.output, check=args.check)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss = int(rss if sys.platform == "darwin" else rss * 1024)
    require(0 < rss <= MAX_RSS and time.monotonic() - started < WALL_SECONDS,
        "public policy staging resource limit exceeded")
    print(json.dumps(dict(result, seconds=time.monotonic() - started, peak_rss_bytes=rss), sort_keys=True))


if __name__ == "__main__":
    main()
