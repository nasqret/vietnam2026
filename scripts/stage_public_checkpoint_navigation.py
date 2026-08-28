#!/usr/bin/env python3
"""Link public research checkpoints from the staged, unchanged Alpha atlas.

Only the staged atlas HTML receives navigation and a scope notice. Its frozen
source, campaign data, definition data and admission statuses stay byte-exact.
This presentation overlay does not verify proofs or grant library membership;
the public checkpoint builder performs the actual HA and Lean checks first.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import os
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "book/_static/constructive-gaussian-campaign"
MAX_BYTES = 16 * 1024 * 1024
REVISION = "ac7111ec14ff"
SOURCE_PINS = {
    "index.html": "1db67dfce7e7c34863732720706e30a8ef41273998af990025ecf975eebc2fe4",
    "campaign.json": "2f0d367c693a51abc3af9fb0dde9e60ee83cbb9e1d51c1c3915b7e6b98f88764",
    "definitions.json": "57c3d1e786d4107eadfa1a1e04c81610fdd060d24ff1eab32ff9c7ed1a4278fd",
}
NAV_ANCHOR = (
    '      <a href="../bertrand-proof-explorer/defined/index.html" '
    'data-proof-bertrand>Bertrand’s Postulate</a>\n'
).encode("utf-8")
NOTICE_ANCHOR = (
    '      <h2 id="campaign-overview-heading">'
    'A mathematical programme, not a theorem certificate</h2>\n'
).encode("utf-8")
NAV_LINK = (
    f'      <a href="../checkpoints/?v={REVISION}" data-proof-checkpoints>'
    'Checked research checkpoints</a>\n'
).encode("utf-8")
NOTICE = (
    '      <p class="notice" data-checkpoint-publication-notice>'
    'This atlas records the unchanged Alpha v30 library. '
    f'<a href="../checkpoints/?v={REVISION}">170 additional complete HA/Lean-checked '
    'theorems</a> are available as public research checkpoints, not Alpha or Stable '
    'admissions. They include Euler’s theorem for units, prime-order fields, '
    'Möbius values and signed finite sums. The full prime-power field and Möbius '
    'inversion goals remain open; publishing these checkpoints does not change '
    'the admission statuses in this map.</p>\n'
).encode("utf-8")


class CheckpointNavigationError(ValueError):
    """The frozen source or dedicated staged navigation is unsafe or stale."""


def _read(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= MAX_BYTES:
        raise CheckpointNavigationError(f"missing, linked or oversized navigation input: {path}")
    with path.open("rb") as handle:
        payload = handle.read(MAX_BYTES + 1)
    if not 0 < len(payload) <= MAX_BYTES:
        raise CheckpointNavigationError(f"navigation input exceeded its read bound: {path}")
    return payload


def _source() -> dict[str, bytes]:
    files = {name: _read(ATLAS / name) for name in SOURCE_PINS}
    if any(sha256(payload).hexdigest() != SOURCE_PINS[name] for name, payload in files.items()):
        raise CheckpointNavigationError("the exact Alpha v30 atlas source changed")
    return files


def _overlay(source: bytes) -> bytes:
    if source.count(NAV_ANCHOR) != 1 or source.count(NOTICE_ANCHOR) != 1:
        raise CheckpointNavigationError("the atlas has no unique reviewed navigation anchors")
    return source.replace(NAV_ANCHOR, NAV_ANCHOR + NAV_LINK).replace(
        NOTICE_ANCHOR, NOTICE_ANCHOR + NOTICE
    )


def stage_public_checkpoint_navigation(root: Path, *, check: bool = False) -> bool:
    """Return whether one staged HTML file changed; never rewrite atlas JSON."""
    chosen = Path(root)
    if chosen.is_symlink() or not chosen.is_dir():
        raise CheckpointNavigationError("proof staging must be an ordinary directory")
    destination = chosen.resolve(strict=True)
    for directory in (destination / "grand-campaign", destination / "checkpoints"):
        if directory.is_symlink() or not directory.is_dir():
            raise CheckpointNavigationError("the staged atlas and checkpoints must be ordinary directories")
    if (destination / "grand-campaign").resolve() == ATLAS.resolve():
        raise CheckpointNavigationError("the frozen source atlas is not a staging destination")

    source = _source()
    _read(destination / "checkpoints/index.html")
    for name in ("campaign.json", "definitions.json"):
        if _read(destination / "grand-campaign" / name) != source[name]:
            raise CheckpointNavigationError("staged Alpha campaign or definition evidence changed")
    target = destination / "grand-campaign/index.html"
    original = _read(target)
    expected = _overlay(source["index.html"])
    if original == expected:
        return False
    if check:
        raise CheckpointNavigationError("the staged checkpoint navigation is missing or stale")
    if original != source["index.html"]:
        raise CheckpointNavigationError("refusing to overwrite unexpected staged atlas HTML")

    # Replacing one private temporary file does not write through a hard link
    # to a historical source, and never leaves partially written public HTML.
    with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".checkpoint-nav-", delete=False) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(expected)
            handle.flush()
            os.fchmod(handle.fileno(), 0o644)
            if _read(target) != original:
                raise CheckpointNavigationError("the staged atlas changed during navigation assembly")
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        changed = stage_public_checkpoint_navigation(args.root, check=args.check)
    except (OSError, CheckpointNavigationError) as error:
        print(f"Checkpoint navigation staging failed: {error}", file=sys.stderr)
        return 1
    print(f"{'Linked' if changed else 'Verified'} public research checkpoints; Alpha atlas data unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
