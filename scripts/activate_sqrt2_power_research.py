#!/usr/bin/env python3
"""Faculty-server activation of the exact reviewed additive research payload.

Run only after explicit publication authorization, from a new private upload
directory. Existing proof assets are never deleted or rewritten. Two backed-up
navigation pages are replaced last. This grants no theorem admission.
"""
import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import time

from stage_sqrt2_power_research import (
    ENTRANCES, PARENT_MANIFEST, PARENT_SHA256, RELEASE,
    authenticated_manifest, encode, file_pin, inventory, pin, safe_path,
)

PUBLIC = Path("/home/faculty/bnaskrecki/public_html/proofs")
PRIVATE_PARENT = Path("/home/faculty/bnaskrecki")


def activate(private, expected_manifest):
    if (private.parent != PRIVATE_PARENT or not private.name.startswith(".sqrt2-publication-")
        or private.is_symlink() or not private.is_dir()
        or private.stat().st_uid != os.getuid()):
        raise ValueError("not the operator-owned private upload directory")
    resource.setrlimit(resource.RLIMIT_CPU, (25, 26))
    resource.setrlimit(resource.RLIMIT_AS, (512*1024**2, 512*1024**2))
    signal.alarm(120)
    started = time.monotonic()
    payload = private / "payload"
    raw = safe_path(payload, RELEASE).read_bytes()
    if pin(raw)["sha256"] != expected_manifest:
        raise ValueError("reviewed payload manifest changed")
    manifest = json.loads(raw)
    if (manifest["authority"] != "research_publication_not_library_admission"
        or manifest["new_library_admissions"] != 0
        or manifest["payload_file_count"] != 267):
        raise ValueError("unexpected publication scope")
    files = dict(manifest["files"])
    files[RELEASE] = pin(raw)
    inventory(payload, files)
    parent_raw = safe_path(PUBLIC, PARENT_MANIFEST).read_bytes()
    if pin(parent_raw)["sha256"] != PARENT_SHA256:
        raise ValueError("public parent manifest changed")
    # The public site may retain older immutable releases outside this sealed
    # inventory. Verify all registered parent bytes without deleting extras.
    parent = dict(json.loads(parent_raw)["current_files"])
    parent[PARENT_MANIFEST] = pin(parent_raw)
    if len(parent) != 13798:
        raise ValueError("public parent inventory changed")
    for name, expected in parent.items():
        if file_pin(safe_path(PUBLIC, name)) != expected:
            raise ValueError("public parent bytes changed: " + name)
    additions = set(files)-set(ENTRANCES)
    if additions & set(parent):
        raise ValueError("new namespace collides with old release")
    namespaces = ("sqrt2-power", "research-releases/sqrt2-power-2026-10-01")
    for name in namespaces:
        if safe_path(PUBLIC, name).exists():
            raise ValueError("immutable research namespace already exists")
    rollback = private / "rollback"
    rollback.mkdir(mode=0o700)
    for name in ENTRANCES:
        target = safe_path(rollback, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(safe_path(PUBLIC, name).read_bytes())
        if file_pin(target) != manifest["replaced_navigation"][name]["before"]:
            raise ValueError("rollback copy mismatch")
    for name in namespaces:
        destination = safe_path(PUBLIC, name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        # copytree refuses any existing destination; there is no overwrite or
        # deletion of a previously published immutable namespace.
        shutil.copytree(safe_path(payload, name), destination)
    for name in additions:
        if file_pin(safe_path(PUBLIC, name)) != files[name]:
            raise ValueError("new public bytes mismatch before entrance activation")
    for name in reversed(ENTRANCES):
        destination = safe_path(PUBLIC, name)
        if file_pin(destination) != manifest["replaced_navigation"][name]["before"]:
            raise ValueError("entrance changed concurrently")
        pending = destination.with_name(".sqrt2-power-20261001-index.pending")
        with pending.open("xb") as stream:
            stream.write(safe_path(payload, name).read_bytes())
            stream.flush()
            os.fsync(stream.fileno())
        if file_pin(pending) != files[name]:
            raise ValueError("pending entrance mismatch")
        os.replace(pending, destination)
    current = {**parent, **files}
    for name, expected in current.items():
        if file_pin(safe_path(PUBLIC, name)) != expected:
            raise ValueError("post-activation public bytes mismatch: " + name)
    result = dict(schema="sqrt2-power-faculty-activation-v1", status="passed",
        authority="delivery_observation_not_proof", manifest=pin(raw),
        registered_public_files_verified=len(current), payload_files_verified=len(files),
        preserved_parent_files=len(parent)-len(ENTRANCES),
        changed_navigation=list(ENTRANCES), new_library_admissions=0,
        rollback_directory=str(rollback), wall_seconds=time.monotonic()-started)
    with (private / "activation.json").open("xb") as stream:
        stream.write(encode(result))
    signal.alarm(0)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private", required=True, type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args()
    print(encode(activate(args.private, args.manifest_sha256)).decode(), end="")
