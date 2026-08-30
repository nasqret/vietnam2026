#!/usr/bin/env python3
"""Delivery-only hub for the already verified v31 publication.

This script never grants admission, changes theorem evidence, or reconstructs
proof authority from a receipt. The separate live HA/Lean publication gate
must have produced all three immutable reader trees first. Here their actual
bytes and routes become a reproducible public-delivery inventory.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re

import constructive_completed_lower_publication_v31 as publication
from peano_catalog_shards import verify_catalog_bindings


ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_HUB = ROOT / "deploy/proofs/history/index-v30.html"
HISTORICAL_HUB_SHA256 = "6c4738a077b2cc147ccb4393b1f3c369274b6253553a11f2bfaa5ec9f025be6b"
HUB = ROOT / "deploy/proofs/index.html"
LOCK = ROOT / "deploy/proofs/release-v31.json"
OLD_REVISION = "ac7111ec14ff"
PACKAGES = (publication.HISTORICAL_OUTPUT_NAME, publication.OUTPUT_NAME)
ATLAS_FILES = ("campaign.json", "definitions.json", "dag-audit.json", "index.html")
CURRENT_IDENTITY = "902fa75c2bf4624bb7fc5aca9a6c49b71ff8fa4499f8bdf9ce726cfd4166a5d7"


class DeliveryError(ValueError):
    """The published byte inventory is incomplete, stale, or unsafe."""


def pin(payload: bytes) -> dict:
    return {"bytes": len(payload), "sha256": sha256(payload).hexdigest()}


def read(path: Path, maximum: int = 64 * 1024 * 1024) -> bytes:
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= maximum:
        raise DeliveryError("unsafe or absent delivery input: " + str(path))
    parent = path.parent
    while parent != ROOT:
        if parent == parent.parent or parent.is_symlink() or not parent.is_dir():
            raise DeliveryError("delivery input escaped its ordinary repository tree")
        parent = parent.parent
    with path.open("rb") as stream:
        payload = stream.read(maximum + 1)
    if not 0 < len(payload) <= maximum:
        raise DeliveryError("delivery input exceeded its file budget")
    return payload


def _once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise DeliveryError("historical hub template changed: " + old[:70])
    return source.replace(old, new, 1)


def render_hub(source: str, families: list[dict], revision: str) -> bytes:
    """Pure formatting, not a theorem verifier or admission API."""
    if re.fullmatch(r"[0-9a-f]{12}", revision) is None:
        raise DeliveryError("invalid navigation revision")
    if (type(families) is not list or len(families) != 19
            or {row["slug"]: row["theorem_count"] for row in families} != publication.FAMILY_COUNTS):
        raise DeliveryError("the current hub needs all nineteen exact new families")
    start = source.index('    <section class="frontier-intro" aria-labelledby="lower-tier-heading"')
    end = source.index('    <section class="frontier-intro" aria-labelledby="grand-campaign-heading"', start)
    cards = []
    for row in families:
        goal_links = " · ".join(
            '<a href="grand-campaign/?view=goal&amp;focus=' + escape(goal, quote=True)
            + '&amp;v=' + revision + '">' + escape(goal) + '</a>' for goal in row["goals"])
        cards.append('''      <article class="family-card candidate-card euclidean-card" data-alpha-first="v31">
        <p class="card-kicker">Alpha v31 checked use · ''' + str(row["theorem_count"]) + ''' independently proved theorems</p>
        <h2>''' + escape(row["title"]) + '''</h2>
        <p>''' + escape(row["caveat"]) + '''</p>
        <a class="primary-action" href="''' + escape(row["slug"], quote=True) + '/?v=' + revision + '''">Explore the proof map <span aria-hidden="true">→</span></a>
        <p>Original HA and compiled Lean verification · first admitted v31 · not Stable.</p>
        <p>Campaign connections: ''' + goal_links + '''</p>
      </article>''')
    introduction = '''    <section class="frontier-intro" aria-labelledby="completed-lower-heading" data-current-alpha="v31">
      <p class="eyebrow">Completed lower-layer constructions</p>
      <h2 id="completed-lower-heading">Nineteen chapters, 574 newly admitted proofs.</h2>
      <p>Euler’s theorem for units, prime-order fields, finite signed sums, polynomial data, Dirichlet convolution and full finite Möbius inversion now belong to Alpha v31. All 19 complete dependency bundles passed the original HA kernel and the independently compiled Lean checker; all 52 principal ordinary certificates were checked separately.</p>
      <p class="candidate-disclaimer">Alpha has 3,796 checked-use entries. Stable remains the separate, unchanged 432-theorem library. General finite signed Dirichlet inverse existence is proved. Full G009 still needs multiplicative closure; general prime-power fields in G091 remain open. Historical checkpoint receipts and first-admission records retain their original meaning.</p>
      <p><a href="grand-campaign/?view=goal&amp;focus=G007&amp;v=''' + revision + '''">G007: complete finite Möbius inversion</a> · <a href="grand-campaign/?view=goal&amp;focus=G009&amp;v=''' + revision + '''">G009: inverse criterion and remaining closure</a></p>
    </section>
    <section class="family-grid frontier-grid" aria-label="New Alpha v31 proof families">
''' + "\n".join(cards) + "\n    </section>\n"
    source = source[:start] + introduction + source[end:]
    pattern = r'      <p>Explore twelve mathematical families,.*?</p>'
    summary = ('      <p>Explore twelve mathematical families, sixteen shared tools, eight proof anchors, '
               '372 reviewed conservative definitions with 787 actual expansion arrows, and 12,248 theorem dependencies. '
               'The 120 major goals remain organized by prerequisites and mathematical scale. Alpha v31 has 3,796 '
               'checked-use entries: 432 unchanged Stable theorems and 3,364 additional Alpha-closed theorems. '
               'Its 574 new statements extend every earlier admission without rewriting historical evidence. '
               'Definition arrows, proof dependencies and still-open research goals remain distinct.</p>')
    source, count = re.subn(pattern, summary, source, count=1)
    if count != 1:
        raise DeliveryError("the historical atlas summary changed")
    source = _once(source, "Forty-two constructive proof campaigns, transparently labeled.",
                   "Forty-two established constructive chapters, with their original evidence.")
    source = _once(source, "all 44 Alpha proof families preserve", "these 44 established proof families preserve")
    source = _once(source, "Alpha v30 retains every earlier first-admission record and connects the five completed priority goals",
                   "The current Alpha library retains every earlier first-admission record and connects the completed priority goals")
    history = '''    <section class="frontier-intro" aria-labelledby="publication-history-heading">
      <h2 id="publication-history-heading">Publication history</h2>
      <p>The current library contains 63 proof families. Earlier non-admitting research snapshots remain available as dated evidence, not as the current admission catalogue: <a href="checkpoints/?v=ac7111ec14ff">the 170-proof checkpoint</a> and <a href="checkpoints/lower-tier/?v=ac7111ec14ff">the 126-proof checkpoint</a>.</p>
      <p><a href="release-v31/manifest.json">Exact public-delivery inventory</a> · <a href="release-v31/alpha-v31-completed-lower-receipt-v1.json">Fresh v31 verification record</a></p>
    </section>
'''
    # Only navigation and the CURRENT edition label are advanced. Historical
    # first-enrollment prose and all mathematical caveats remain unchanged.
    source = source.replace(OLD_REVISION, revision).replace("Alpha v30 checked use", "Alpha v31 checked use")
    source = _once(source, "  </main>", history + "  </main>")
    source = _once(source, "</head>", '<meta name="proof-publication-scope" content="alpha-v31-checked-use">\n</head>')
    return source.encode("utf-8")


def build_files() -> dict[Path, bytes]:
    channels = publication.strict_json(read(ROOT / "artifacts/peano-library/channels-v31.json", 8 * 1024 * 1024))
    channel = channels["channels"]["alpha"]
    digest = channel["artifact_sha256"]
    if (channels.get("default_channel") != "stable" or channel.get("theorem_count") != 3796
            or channel.get("checked_use_count") != 3796 or channel.get("edition_identity_sha256") != CURRENT_IDENTITY):
        raise DeliveryError("the existing current release channel is inconsistent")
    verify_catalog_bindings(ROOT / channel["artifact_path"], expected_sha256=digest)
    tree_pins, manifests = {}, {}
    for package in PACKAGES:
        directory = ROOT / "book/_static" / package
        raw = read(directory / "manifest.json", 2 * 1024 * 1024)
        manifest = publication.strict_json(raw)
        if (manifest.get("alpha_edition_version") != "v31" or manifest.get("catalog_sha256") != digest
                or manifest.get("edition_identity_sha256") != CURRENT_IDENTITY
                or manifest.get("html_revision") != digest[:12]):
            raise DeliveryError("the immutable reader belongs to a different current release")
        if type(manifest.get("files")) is not dict or len(manifest["files"]) != manifest.get("file_count_excluding_manifest"):
            raise DeliveryError("reader manifest has an incomplete file inventory")
        tree_pins[package] = pin(raw)
        manifests[package] = manifest
    old, new = (manifests[name] for name in PACKAGES)
    if (len(old["families"]) != 44 or old["theorem_count"] != 3096 or old["checked_use_count"] != 3007
            or old.get("alpha_first_enrolled_version") != "mixed_preserved"
            or "first_enrollment_catalog_sha256" in old
            or new["theorem_count"] != 574 or new["checked_use_count"] != 574
            or new.get("alpha_first_enrolled_version") != "v31"
            or new.get("first_enrollment_catalog_sha256") != digest):
        raise DeliveryError("historical/new family evidence counts or first admissions changed")
    atlas = ROOT / "book/_static" / publication.ATLAS_NAME
    atlas_pins = {name: pin(read(atlas / name, 8 * 1024 * 1024)) for name in ATLAS_FILES}
    campaign = publication.strict_json(read(atlas / "campaign.json", 8 * 1024 * 1024))
    if (campaign["meta"]["current_alpha_version"] != "v31"
            or campaign["meta"]["current_alpha_checked_use_count"] != 3796
            or campaign["ambitious_boundaries"]["alpha_v31_edition"]["catalog_sha256"] != digest):
        raise DeliveryError("the combined atlas differs from the reader release")
    source = read(HISTORICAL_HUB, 256 * 1024)
    if sha256(source).hexdigest() != HISTORICAL_HUB_SHA256:
        raise DeliveryError("the original Quadratic Reciprocity hub template changed")
    hub = render_hub(source.decode("utf-8"), new["families"], digest[:12])
    receipt_path = "research/arithmetic-library/artifacts/alpha-v31-completed-lower-receipt-v1.json"
    lock = {
        "schema": "peano-lab-alpha-v31-public-delivery-v1",
        "purpose": "Byte-exact delivery of an already verified release; not proof or admission authority.",
        "catalog_sha256": digest, "edition_identity_sha256": CURRENT_IDENTITY,
        "alpha_version": "v31", "checked_use_count": 3796, "stable_count": 432,
        "family_count": 63, "new_family_count": 19, "new_theorem_count": 574,
        "historical_hub_sha256": HISTORICAL_HUB_SHA256,
        "hub": pin(hub), "reader_manifests": tree_pins, "atlas": atlas_pins,
        "verification_record": {"path": receipt_path, **pin(read(ROOT / receipt_path, 8 * 1024 * 1024))},
        "G007_finite_signed_mobius_inversion": "proved", "G009_multiplicative_closure": "open",
        "G091_general_prime_power_fields": "open",
    }
    return {HUB: hub, LOCK: publication.json_bytes(lock)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    for path, payload in build_files().items():
        if args.check:
            if read(path, 2 * 1024 * 1024) != payload:
                raise DeliveryError("current delivery hub is stale: " + str(path))
        else:
            if path.is_symlink():
                raise DeliveryError("refusing a linked delivery output")
            path.write_bytes(payload)
    print("Alpha v31 delivery hub: PASS (63 families; 574 new admissions; Stable unchanged)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
