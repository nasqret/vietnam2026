#!/usr/bin/env python3
"""Link both public checkpoint generations without rewriting the Alpha DAG.

The earlier 495-file public snapshot remains literal. Only the already staged
atlas HTML receives the new navigation; its campaign and definition JSON keep
their original hashes. This is delivery, never proof checking or admission.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import os
from pathlib import Path
import sys
import tempfile

import stage_public_checkpoint_navigation as previous
from constructive_lower_tier_publication_adapter import LOCAL_CHECKPOINT_DIGEST, strict_json


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "book/_static/constructive-lower-tier-publication"
NAV_LINK = (
    '      <a href="../checkpoints/lower-tier/?v=ac7111ec14ff" data-proof-lower-tier>'
    'Divisor sums and polynomial data</a>\n'
).encode()
NOTICE = (
    '      <p class="notice" data-checkpoint-publication-notice>'
    'This atlas records the unchanged Alpha v30 library. '
    '<a href="../checkpoints/?v=ac7111ec14ff">170 earlier complete HA/Lean-checked theorems</a> '
    'and <a href="../checkpoints/lower-tier/?v=ac7111ec14ff">126 further complete proofs</a> '
    'are public research checkpoints, not Alpha or Stable admissions. The newer chapters '
    'construct divisor sums, signed weighted sums and prime-field coefficient tables with '
    'actual Horner evaluation. Full Möbius inversion and general prime-power fields remain '
    'open. These 296 distinct additional proofs do not change the admission statuses in this map.</p>\n'
).encode()


def expected_atlas() -> bytes:
    base = previous._overlay(previous._source()["index.html"])
    if base.count(previous.NOTICE) != 1 or base.count(previous.NAV_LINK) != 1:
        raise previous.CheckpointNavigationError("previous atlas overlay changed")
    return base.replace(previous.NOTICE, NOTICE).replace(previous.NAV_LINK, previous.NAV_LINK + NAV_LINK)


def stage_lower_tier_navigation(root: Path, *, check: bool = False) -> bool:
    chosen = Path(root)
    if chosen.is_symlink() or not chosen.is_dir():
        raise previous.CheckpointNavigationError("staging must be an ordinary directory")
    destination = chosen.resolve(strict=True)
    for relative in ("grand-campaign", "checkpoints", "checkpoints/lower-tier"):
        directory = destination / relative
        if directory.is_symlink() or not directory.is_dir():
            raise previous.CheckpointNavigationError("checkpoint staging directory is missing or linked")
    if (destination / "grand-campaign").resolve() == previous.ATLAS.resolve():
        raise previous.CheckpointNavigationError("the frozen atlas is not a staging destination")
    sources = previous._source()
    for name in ("campaign.json", "definitions.json"):
        if previous._read(destination / "grand-campaign" / name) != sources[name]:
            raise previous.CheckpointNavigationError("Alpha campaign or definition data changed")
    manifest = strict_json(previous._read(PUBLIC / "manifest.json"))
    for name in ("index.html", "checkpoints.json"):
        payload = previous._read(PUBLIC / name)
        if manifest["files"][name] != {"bytes": len(payload), "sha256": sha256(payload).hexdigest()}:
            raise previous.CheckpointNavigationError("lower-tier publication metadata is stale")
        if previous._read(destination / "checkpoints/lower-tier" / name) != payload:
            raise previous.CheckpointNavigationError("staged lower-tier publication differs from verified source")
    inventory = strict_json(previous._read(PUBLIC / "checkpoints.json"))
    if (inventory["checkpoint_digest"] != LOCAL_CHECKPOINT_DIGEST or inventory["new_theorem_count"] != 126
            or inventory["alpha_admission_performed"] is not False or inventory["stable_admission_performed"] is not False):
        raise previous.CheckpointNavigationError("lower-tier inventory is not the exact non-admitting tranche")
    previous._read(destination / "checkpoints/index.html")
    target = destination / "grand-campaign/index.html"
    original, expected = previous._read(target), expected_atlas()
    if original == expected:
        return False
    if check:
        raise previous.CheckpointNavigationError("lower-tier navigation is missing or stale")
    if original != previous._overlay(sources["index.html"]):
        raise previous.CheckpointNavigationError("refusing unexpected staged atlas HTML")
    with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".lower-tier-nav-", delete=False) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(expected)
            handle.flush()
            os.fchmod(handle.fileno(), 0o644)
            if previous._read(target) != original:
                raise previous.CheckpointNavigationError("atlas changed during navigation assembly")
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        changed = stage_lower_tier_navigation(args.root, check=args.check)
    except (OSError, ValueError) as error:
        print(f"Lower-tier navigation refused: {error}", file=sys.stderr)
        return 1
    print(f"{'Linked' if changed else 'Verified'} 170 + 126 research proofs; Alpha atlas data unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
