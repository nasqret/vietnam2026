#!/usr/bin/env python3
"""Byte-exact v33 faculty staging; never a proof/admission authority.

The genuine live release must exist first. Its registered reader bytes are
combined with the already validated old public tree in a NEW, dedicated stage.
Historical routes are retained. Nothing remote is changed by this script.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import resource
import signal
import stat
import sys
from tempfile import TemporaryDirectory
import time

import constructive_research_publication_v33 as publication
import stage_constructive_g009_publication as legacy
import stage_public_lean_selector as selector
import stage_constructive_research_publication_v32 as previous


ROOT = Path(__file__).resolve().parents[1]
PARENT_STAGE = ROOT / "_deploy/proofs-v32"
STAGE = ROOT / "_deploy/proofs-v33"
CPU_LIMITS, WALL_SECONDS, MAX_RSS = (170, 175), 180, 1536 * 1024 * 1024
MAX_FILE, MAX_FILES = 64 * 1024 * 1024, 20000
ATLAS_FILES = ("campaign.json", "definitions.json", "dag-audit.json", "index.html")
SCHEMA = "peano-lab-alpha-v33-public-delivery-v1"

# Register only the actual completed live publication. Pins identify delivery
# bytes; they are not success flags and cannot replace proof verification.
REGISTRATION = {
    "atlas": {
        "campaign.json": {
            "bytes": 736201,
            "sha256": "a4cce950e1402dd32129241c39e287142a91c52f91646e9ba44fba4bac06755f"
        },
        "dag-audit.json": {
            "bytes": 8466,
            "sha256": "d85f1afe5311efc6f09d05ecb69ce768540333abf91d74d07110bd0e1d8e4b84"
        },
        "definitions.json": {
            "bytes": 1489692,
            "sha256": "7210608913bdb601c055684090bd667704ae66d46be3a71d07818e092de5c15d"
        },
        "index.html": {
            "bytes": 774916,
            "sha256": "f5fa8a047f510a3971f64d280f2980752b2d1613d8e72ea09ed8af59e81ce7ec"
        }
    },
    "catalog": {
        "bytes": 946819,
        "sha256": "6be052da195a295edce02f4b1955cd9e3dd71d7acefb9ac5794277eda7ef40cc"
    },
    "channels": {
        "bytes": 9638,
        "sha256": "d10d87694f813b86451bcccdde4dcd68e5d6fe73795b9610d98bea4f3e5de6bc"
    },
    "readers": {
        "completed": {
            "bytes": 368852,
            "sha256": "769bd7b5938b5a46961b4794e6c7460ef6564306deb30fcbab378ac92f76660d"
        },
        "historical": {
            "bytes": 1780999,
            "sha256": "fc2040db768deac43a23c420e4da9069e26f2853e391e7dd890ff91900d91735"
        },
        "polynomial": {
            "bytes": 64446,
            "sha256": "c73a62e85d0907f71f1ed5cab32f5115cc8d4452ff615c06d168545b47dc6bda"
        },
        "research": {
            "bytes": 100746,
            "sha256": "ac763c90cc1098d73ed3e8d6ceae1c07de68468d3484fb79114d482e9a82fa58"
        }
    },
    "receipt": {
        "bytes": 55856,
        "sha256": "cea85e5c595a021061fb50997df7ad489c8905ab563695209dadc8235f6762cb"
    }
}


class DeliveryError(ValueError):
    """A registered byte identity, route, boundary or safe destination failed."""


@dataclass(frozen=True, slots=True)
class File:
    pin: dict
    source: Path | None = None
    content: bytes | None = None
    current: bool = False


def _pin(raw):
    return {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}


def _valid_pin(value):
    if (type(value) is not dict or set(value) != {"bytes", "sha256"}
            or type(value["bytes"]) is not int or not 0 < value["bytes"] <= MAX_FILE
            or type(value["sha256"]) is not str or re.fullmatch(r"[0-9a-f]{64}", value["sha256"]) is None):
        raise DeliveryError("invalid bounded literal delivery identity")


def require_registration():
    value = REGISTRATION
    expected = {"catalog", "channels", "receipt", "readers", "atlas"}
    if type(value) is not dict or set(value) != expected:
        raise DeliveryError("the actual completed v33 publication is not registered for delivery")
    for name in ("catalog", "channels", "receipt"):
        _valid_pin(value[name])
    if type(value["readers"]) is not dict or set(value["readers"]) != {"polynomial", "research", "completed", "historical"}:
        raise DeliveryError("all four exact v33 reader trees are required")
    if type(value["atlas"]) is not dict or set(value["atlas"]) != set(ATLAS_FILES):
        raise DeliveryError("all four exact current atlas files are required")
    for pin in (*value["readers"].values(), *value["atlas"].values()):
        _valid_pin(pin)
    return value


def _read(path, pin=None):
    raw = legacy._read(Path(path), MAX_FILE if pin is None else pin["bytes"], base=ROOT, owned=True)
    if pin is not None and _pin(raw) != pin:
        raise DeliveryError("registered delivery bytes changed: " + str(path))
    return raw


def _bytes(item):
    if type(item) is not File:
        raise DeliveryError("foreign delivery record")
    _valid_pin(item.pin)
    if item.content is not None:
        if item.source is not None or type(item.content) is not bytes or _pin(item.content) != item.pin:
            raise DeliveryError("changed inline delivery bytes")
        return item.content
    if not isinstance(item.source, Path):
        raise DeliveryError("delivery record lacks an ordinary exact source")
    return _read(item.source, item.pin)


def _inline(raw, *, current=True):
    return File(_pin(raw), content=raw, current=current)


def _tree(base):
    base = Path(base)
    legacy._ordinary_ancestors(base / "index.html", base, owned=True)
    info = base.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
        raise DeliveryError("staging input is not an owned ordinary directory")
    result = set()
    for path in base.rglob("*"):
        info = path.lstat()
        if stat.S_ISDIR(info.st_mode):
            continue
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise DeliveryError("staging tree contains an unsafe filesystem entry")
        name = path.relative_to(base).as_posix()
        if not publication.safe_relative(name) or len(result) >= MAX_FILES:
            raise DeliveryError("unsafe or oversized staging file inventory")
        result.add(name)
    return result


def _selector_bytes(name, raw, insertion):
    matched, markers = selector._candidate(Path(name), Path(name))
    if not matched:
        return raw
    if not any(marker in raw for marker in markers):
        raise DeliveryError("current theorem page lacks its original supported proof panel: " + name)
    marker = b"/proofs/assets/lean-selector.js"
    if marker in raw:
        if raw.count(marker) != 1 or insertion not in raw:
            raise DeliveryError("stale or duplicate current Lean selector")
        return raw
    closing = selector.CLOSING_HEAD.search(raw)
    if closing is None:
        raise DeliveryError("current theorem page lacks a closing head")
    return raw[:closing.start()] + insertion + raw[closing.start():]


def _public_atlas_html(raw, revision):
    """Relocate only the initial home anchor; keep every atlas script literal.

    The verified reader supports both its local package layout and /proofs/.
    Its runtime already chooses the public home on the faculty pathname. The
    initial HTML anchor must also resolve before JavaScript runs.
    """
    if (type(raw) is not bytes or type(revision) is not str
            or re.fullmatch(r"[0-9a-f]{12}", revision) is None):
        raise DeliveryError("invalid exact public atlas relocation")
    before = ('<a href="../constructive-research-explorer-v33/index.html?v='
              + revision + '" data-proof-home>').encode()
    after = ('<a href="../index.html?v=' + revision + '" data-proof-home>').encode()
    if raw.count(before) != 1 or after in raw:
        raise DeliveryError("the exact atlas home anchor is missing or ambiguous")
    return raw.replace(before, after, 1)


def source_inventory(*, api_url=""):
    """Validate sources read-only; this cannot grant theorem membership."""
    registration = require_registration()
    from build_constructive_research_hub_v33 import render_public_hub
    input_pins, input_trees = {}, {}

    def read(path, pin=None):
        raw = _read(path, pin)
        observed = _pin(raw)
        if path in input_pins and input_pins[path] != observed:
            raise DeliveryError("an input changed while the source inventory was built")
        input_pins[path] = observed
        return raw

    def tree(path):
        names = _tree(path)
        input_trees[path] = names
        return names
    # Preserve the existing validated publication, including historical routes.
    previous.stage(check=True, api_url=api_url)
    parent = {}
    for name in sorted(tree(PARENT_STAGE)):
        raw = read(PARENT_STAGE / name)
        parent[name] = File(_pin(raw), source=PARENT_STAGE / name)
    overlay = {}
    catalog_path = ROOT / "artifacts/peano-library/alpha/catalog-v33.json"
    catalog_raw = read(catalog_path, registration["catalog"])
    catalog = publication.strict_json(catalog_raw)["metadata"]
    channels_raw = read(ROOT / "artifacts/peano-library/channels-v33.json", registration["channels"])
    channels = publication.strict_json(channels_raw)
    revision = registration["catalog"]["sha256"][:12]
    if (catalog["checked_use_count"] != 4092 or catalog["stable_count"] != 432
            or channels["default_channel"] != "stable"
            or channels["channels"]["alpha"]["artifact_sha256"] != registration["catalog"]["sha256"]):
        raise DeliveryError("current registered delivery has the wrong release boundary")
    insertion = selector._overlay(selector._api_url(api_url))
    families = []

    def add(name, raw, *, source=None):
        if not publication.safe_relative(name):
            raise DeliveryError("unsafe registered public destination")
        item = _inline(raw) if source is None else File(_pin(raw), source=source, current=True)
        if name in overlay and overlay[name].pin != item.pin:
            raise DeliveryError("current reader packages disagree on shared bytes: " + name)
        overlay[name] = item

    for phase in ("polynomial", "research", "completed", "historical"):
        directory = ROOT / "book/_static" / publication.OUTPUT_NAMES[phase]
        raw = read(directory / "manifest.json", registration["readers"][phase])
        manifest = publication.strict_json(raw)
        if (manifest.get("schema") != publication.SCHEMA + "-manifest"
                or manifest.get("phase") != phase or manifest.get("alpha_edition_version") != "v33"
                or manifest.get("catalog_sha256") != registration["catalog"]["sha256"]
                or manifest.get("alpha_edition_checked_use_count") != 4092
                or manifest.get("stable_edition_count") != 432):
            raise DeliveryError("reader manifest is not the registered current v33 projection")
        files = manifest.get("files")
        if type(files) is not dict or len(files) != manifest.get("file_count_excluding_manifest"):
            raise DeliveryError("invalid current reader file count")
        if tree(directory) != set(files) | {"manifest.json"}:
            raise DeliveryError("current reader has extra or missing files")
        families.extend(row["slug"] for row in manifest["families"])
        add("release-v33/" + phase + "-manifest.json", raw, source=directory / "manifest.json")
        for name, pin in files.items():
            _valid_pin(pin)
            payload = read(directory / name, pin)
            if name == "index.html":
                continue
            destination = "release-v33/" + phase + "-publication.json" if name == "publication.json" else name
            delivered = _selector_bytes(destination, payload, insertion) if name.endswith(".html") else payload
            add(destination, delivered, source=directory / name if delivered == payload else None)
    if len(families) != 66 or len(set(families)) != 66:
        raise DeliveryError("the current release must retain exactly66 proof families")
    atlas = ROOT / "book/_static" / publication.OUTPUT_NAMES["atlas"]
    if tree(atlas) != set(ATLAS_FILES):
        raise DeliveryError("current atlas is not the exact four-file tree")
    for name, pin in registration["atlas"].items():
        raw = read(atlas / name, pin)
        if name == "index.html":
            add("grand-campaign/" + name, _public_atlas_html(raw, revision))
        else:
            add("grand-campaign/" + name, raw, source=atlas / name)
    for name, expected in publication.ASSET_DIGESTS.items():
        if overlay["assets/" + name].pin["sha256"] != expected:
            raise DeliveryError("the original QR asset changed")
    for name in ("lean-selector.js", "lean-selector.css"):
        add("assets/" + name, read(selector.SOURCE / name))
    parent_hub = read(PARENT_STAGE / "index.html", {"bytes": 85047,
        "sha256": "307611d61cf2deabd021f50f920f305368aadfc040f7ceb0e78c66806ed20a36"})
    add("index.html", render_public_hub(parent_hub, revision))
    receipt_path = ROOT / "research/arithmetic-library/artifacts/alpha-v33-research-receipt-v1.json"
    add("release-v33/alpha-v33-research-receipt-v1.json", read(receipt_path, registration["receipt"]), source=receipt_path)
    merged = {**parent, **overlay}
    record = {"schema": SCHEMA, "delivery_metadata_only": True,
        "alpha_admission_performed": False, "stable_admission_performed": False,
        "alpha_version": "v33", "checked_use_count": 4092, "stable_count": 432,
        "catalog_sha256": registration["catalog"]["sha256"], "edition_identity_sha256": catalog["edition_identity_sha256"],
        "family_count": 66, "new_family_count": 1, "new_theorem_count": 121,
        "G009_multiplicative_closure": "proved", "G091_general_prime_power_fields": "open",
        "literal_inputs": registration, "source_hub_preserved": "_deploy/proofs-v32/index.html",
        "current_files": {name: item.pin for name, item in sorted(overlay.items())},
        "retained_historical_file_count": len(set(parent) - set(overlay))}
    raw = publication.json_bytes(record)
    if len(raw) > 4 * 1024 * 1024:
        raise DeliveryError("current delivery record exceeds its metadata budget")
    merged["release-v33/manifest.json"] = _inline(raw)
    if len(merged) > MAX_FILES:
        raise DeliveryError("combined public tree exceeds the original file ceiling")
    return merged, record, (input_pins, input_trees)


def check_links(files):
    """Check current pages against the complete retained public namespace."""
    identifiers, count, fragments = {}, 0, 0
    for name, item in sorted(files.items()):
        if not item.current or not name.endswith(".html"):
            continue
        document = legacy._HTML(_bytes(item))
        identifiers[name] = document.ids
        for _tag, _field, href in document.links:
            resolved = legacy._link_target(name, href)
            if resolved is None:
                continue
            target, fragment = resolved
            if target not in files:
                raise DeliveryError("missing literal public target: " + name + " -> " + target)
            count += 1
            if fragment:
                if not target.endswith(".html"):
                    raise DeliveryError("a fragment targets a non-HTML public artifact")
                if target not in identifiers:
                    identifiers[target] = legacy._HTML(_bytes(files[target])).ids
                if fragment not in identifiers[target]:
                    raise DeliveryError("missing exact public fragment: " + name + " -> " + target + "#" + fragment)
                fragments += 1
    return {"local_links": count, "local_fragments": fragments}


def _verify_tree(directory, files):
    if _tree(directory) != set(files):
        raise DeliveryError("the dedicated stage has missing or extra files")
    for name, item in files.items():
        _read(directory / name, item.pin)


def _rebind_inputs(binding):
    pins, trees = binding
    for path, pin in pins.items():
        _read(path, pin)
    for path, names in trees.items():
        if _tree(path) != names:
            raise DeliveryError("an input tree gained or lost a file during staging")


def _rss_bytes():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    value = int(value if sys.platform == "darwin" else value * 1024)
    if not 0 < value <= MAX_RSS:
        raise DeliveryError("delivery exceeded the unchanged original RSS ceiling")
    return value


def _stage_source_paths():
    """Bind the full nested staging implementation through the final copy."""
    return (Path(__file__), ROOT / "scripts/build_constructive_research_hub_v33.py",
        ROOT / "scripts/stage_public_lean_selector.py", ROOT / "scripts/stage_constructive_g009_publication.py",
        ROOT / "scripts/stage_completed_lower_publication_v31.py",
        ROOT / "scripts/build_constructive_completed_lower_hub_v31.py",
        ROOT / "scripts/constructive_completed_lower_publication_v31.py",
        ROOT / "scripts/peano_catalog_shards.py",
        ROOT / "scripts/constructive_research_publication_v33.py",
        ROOT / "scripts/constructive_alpha_v33_publication_process.py",
        ROOT / "scripts/constructive_research_publication_v32.py",
        ROOT / "scripts/constructive_alpha_v32_publication_process.py",
        ROOT / "scripts/stage_constructive_research_publication_v32.py",
        ROOT / "scripts/build_constructive_research_hub_v32.py")


def stage(*, check=False, api_url=""):
    if type(check) is not bool:
        raise DeliveryError("check must be a literal Boolean")
    started = time.monotonic()
    registration = publication.json_bytes(require_registration())
    source_pins = {path: _pin(_read(path)) for path in _stage_source_paths()}
    files, record, input_binding = source_inventory(api_url=api_url)
    links = check_links(files)

    def final_source_check():
        # Every source is rehashed before any new stage becomes visible.
        for item in files.values():
            _bytes(item)
        _rebind_inputs(input_binding)
        for path, pin in source_pins.items():
            _read(path, pin)
        if publication.json_bytes(require_registration()) != registration:
            raise DeliveryError("delivery registration changed during staging")
        peak = _rss_bytes()
        if time.monotonic() - started >= WALL_SECONDS:
            raise DeliveryError("delivery exceeded the unchanged original resource limits")
        return peak

    if check:
        _verify_tree(STAGE, files)
        peak = final_source_check()
    else:
        if STAGE.exists() or STAGE.is_symlink():
            raise DeliveryError("refusing to replace an existing v33 stage; use --check")
        legacy._ordinary_ancestors(STAGE, ROOT, owned=True)
        from constructive_alpha_v33_publication_process import _rename_new
        with TemporaryDirectory(prefix=".v33-delivery-", dir=STAGE.parent) as temporary:
            private = Path(temporary) / "files"
            private.mkdir(mode=0o755)
            for name in sorted(files, key=lambda value: (value == "index.html", value)):
                destination = private / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open("xb") as stream:
                    stream.write(_bytes(files[name]))
            _verify_tree(private, files)
            peak = final_source_check()
            _rename_new(private, STAGE)
    return {"schema": SCHEMA, "check_only": check, "delivery_metadata_only": True,
        "files": len(files), "source_bytes": sum(item.pin["bytes"] for item in files.values()),
        "family_count": 66, "alpha_checked_use_count": 4092, "stable_count": 432,
        "catalog_sha256": record["catalog_sha256"], "peak_rss_bytes": peak,
        "seconds": time.monotonic() - started, **links}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--api-url", default="")
    args = parser.parse_args(argv)
    resource.setrlimit(resource.RLIMIT_CPU, CPU_LIMITS)
    signal.alarm(WALL_SECONDS)
    print(json.dumps(stage(check=args.check, api_url=args.api_url), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
