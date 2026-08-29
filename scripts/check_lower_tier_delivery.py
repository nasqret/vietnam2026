#!/usr/bin/env python3
"""Read-only staged and optional HTTPS byte checks for the 126-proof delivery.

Proof verification belongs to the fresh HA/Lean build gates. This separately
checks the delivered bytes, all new HTML references and the unchanged older
checkpoint copy. It never submits work to the public on-demand proof service.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import posixpath
import ssl
from time import monotonic
from urllib.parse import quote, unquote, urlsplit
from urllib.request import Request, urlopen

import stage_lower_tier_checkpoint_navigation as navigation
from constructive_lower_tier_publication_adapter import ORIGIN, strict_json


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOTS = (
    ("constructive-bottom-layer-publication", "checkpoints", "f800d3436d7b053a6ba233e2c1014d7a1b8e7eb613ba3d9c36902ca5ede623ab", 495),
    ("constructive-lower-tier-publication", "checkpoints/lower-tier", "a44222194449c465f9e89915ab07e1a93ad74f61e319d502745a1d4b7dbee152", 373),
)
MAX_FILE_BYTES = 32 * 1024 * 1024


def read(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= MAX_FILE_BYTES:
        raise ValueError("missing, linked or oversized delivery input: " + str(path))
    with path.open("rb") as stream:
        payload = stream.read(MAX_FILE_BYTES + 1)
    if len(payload) > MAX_FILE_BYTES:
        raise ValueError("delivery input exceeded its read bound")
    return payload


class Document(HTMLParser):
    def __init__(self, payload: bytes):
        super().__init__(convert_charrefs=True)
        self.references, self.ids = [], set()
        self.feed(payload.decode("utf-8"))
        self.close()

    def handle_starttag(self, tag, pairs):
        attrs = dict(pairs)
        if len(pairs) != len(attrs):
            raise ValueError("duplicate HTML attribute")
        if "id" in attrs:
            if attrs["id"] in self.ids:
                raise ValueError("duplicate HTML id")
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            if key in attrs:
                self.references.append(attrs[key])


def staged(root: Path):
    if root.is_symlink() or not root.is_dir():
        raise ValueError("proof staging must be an ordinary directory")
    root = root.resolve(strict=True)
    total_files = total_bytes = 0
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("symlink in dedicated proof staging")
        if path.is_file():
            total_files += 1
            total_bytes += path.stat().st_size
    payloads, counts = {}, {}
    for source_name, prefix, expected_manifest, count in SNAPSHOTS:
        source = ROOT / "book/_static" / source_name
        manifest_bytes = read(source / "manifest.json")
        if sha256(manifest_bytes).hexdigest() != expected_manifest:
            raise ValueError("frozen public manifest changed")
        manifest = strict_json(manifest_bytes)
        expected = manifest["files"] | {"manifest.json": {"bytes": len(manifest_bytes), "sha256": expected_manifest}}
        if len(expected) != count:
            raise ValueError("unexpected snapshot file count")
        for name, pin in expected.items():
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts or "\\" in name or str(path) != name:
                raise ValueError("unsafe snapshot path")
            original, actual = read(source / name), read(root / prefix / name)
            if pin != {"bytes": len(original), "sha256": sha256(original).hexdigest()} or actual != original:
                raise ValueError("source or staged snapshot bytes differ: " + prefix + "/" + name)
            payloads[prefix + "/" + name] = original
        counts[source_name] = count
    navigation.stage_lower_tier_navigation(root, check=True)
    for relative, source in (("index.html", ROOT / "deploy/proofs/index.html"),
                             ("assets/proofs.css", ROOT / "deploy/proofs/proofs.css")):
        payloads[relative] = read(source)
        if read(root / relative) != payloads[relative]:
            raise ValueError("staged hub or canonical stylesheet differs")
    for name in ("index.html", "campaign.json", "definitions.json"):
        payloads["grand-campaign/" + name] = read(root / "grand-campaign" / name)
    documents, references = {}, 0
    new_prefix = "checkpoints/lower-tier/"
    for name, payload in payloads.items():
        if name.startswith(new_prefix) and name.endswith(".html"):
            documents[name] = Document(payload)
    new_html_count = len(documents)
    for name in tuple(documents):
        for href in documents[name].references:
            parsed = urlsplit(href)
            if parsed.scheme or parsed.netloc:
                continue
            target = posixpath.normpath(posixpath.join(posixpath.dirname("/proofs/" + name), unquote(parsed.path))) if parsed.path else "/proofs/" + name
            if parsed.path.endswith("/"):
                target += "/index.html"
            if not target.startswith("/proofs/"):
                raise ValueError("new local reference escaped proof website")
            relative = target.removeprefix("/proofs/")
            if relative not in payloads:
                payloads[relative] = read(root / relative)
            actual = payloads[relative]
            if parsed.fragment:
                if relative not in documents:
                    documents[relative] = Document(actual)
                document = documents[relative]
                if unquote(parsed.fragment) not in document.ids:
                    raise ValueError("missing target fragment: " + name + " -> " + href)
            references += 1
    routes = strict_json(payloads[new_prefix + "historical-prerequisites.json"])["routes"]
    for route in routes.values():
        if route["standalone_page"]:
            relative = route["public_path"].removeprefix("/proofs/")
            payloads[relative] = read(root / relative)
    report = {"staged_files": total_files, "staged_bytes": total_bytes, "literal_snapshots": counts,
              "new_html_pages": new_html_count, "new_html_local_references": references,
              "alpha_atlas_data_unchanged": True, "alpha_or_stable_admissions": False}
    return report, payloads


def live(payloads: dict[str, bytes]):
    context = ssl.create_default_context()
    deadline = monotonic() + 90
    def fetch(item):
        name, expected = item
        remaining = deadline - monotonic()
        if remaining <= 0:
            raise TimeoutError("HTTPS audit exceeded its 90-second request window")
        url = ORIGIN + "/proofs/" + quote(name, safe="/") + "?v=ac7111ec14ff"
        request = Request(url, headers={"User-Agent": "Peano-proof-delivery-check/1", "Accept-Encoding": "identity"})
        with urlopen(request, context=context, timeout=min(25, remaining)) as response:
            if response.status != 200 or response.geturl() != url:
                raise ValueError("unexpected HTTPS status or redirect: " + name)
            actual = response.read(len(expected) + 1)
        if actual != expected:
            raise ValueError("served bytes differ from exact staging: " + name)
        return len(actual)
    # Four bounded read-only requests; no cookies, credentials or proof jobs.
    with ThreadPoolExecutor(max_workers=4) as executor:
        lengths = tuple(executor.map(fetch, sorted(payloads.items())))
    return {"https_objects_compared": len(lengths), "https_bytes_compared": sum(lengths),
            "tls_certificate_verification": True, "differences": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT / "_deploy/proofs")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    report, payloads = staged(args.root)
    if args.live:
        report.update(live(payloads))
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
