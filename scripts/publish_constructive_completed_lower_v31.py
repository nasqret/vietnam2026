#!/usr/bin/env python3
"""Fresh Alpha-v31 publication with additive presentation compatibility.

The frozen publisher remains literal historical evidence.  This successor
corrects its aggregate index link and preserves the two exact historical
edition-agnostic graph schemas. It does not change a theorem, proof gate,
receipt, resource limit or historical test.
Every public invocation still requires the original genuine live verifier.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
from html.parser import HTMLParser
import os
from pathlib import Path
import re
import resource
import signal
import stat
from types import FunctionType

import constructive_alpha_v31_publication_process as original
import constructive_completed_lower_publication_v31 as publication
import upgrade_constructive_historical_publication_v31 as historical


ROOT = publication.ROOT
SOURCE = "scripts/publish_constructive_completed_lower_v31.py"
TEST = "scripts/test_publish_constructive_completed_lower_v31.py"
CORRECTION_SCHEMA = "peano-lab-alpha-v31-aggregate-navigation-correction-v1"
# These complete, immutable schemas deliberately impose no current Alpha
# version. Their lack of a v25 constraint is not an incomplete proof record.
# Do not generalize this exception to an arbitrary edition-agnostic schema.
EDITION_AGNOSTIC_SCHEMAS = (
    ("book/_static/pa-proof-explorer/defined/api/graph.schema.json", 1057,
     "0d5313078ef36d47733b1d2dae06778db8a53b7b18e91adab4e92e445eecd559"),
    ("book/_static/bertrand-proof-explorer/defined/api/graph.schema.json", 1136,
     "289a39e7e66690db269f540ca79b2e074add9575bb0f1cdbc9f8a0435f0aa859"),
)
FROZEN_SOURCES = (
    ("scripts/build_constructive_completed_lower_explorer_v31.py", 24547, "d138a6f6f2dba46567b71f514f2aec3d3042449302b80a652d12f57bcb2818fe"),
    ("scripts/constructive_alpha_v31_publication_process.py", 20539, "6cc39f32255b0e36317bd1b9b806d0aa6031e7fcd39ebcab0396df440ed3b828"),
    ("scripts/constructive_completed_lower_publication_v31.py", 28919, "ed6d9453329c637cbc6c50ffa939f3039f72e999c857565e48907e44cc717ba5"),
    ("scripts/upgrade_constructive_historical_publication_v31.py", 38330, "329cfb7060a13c1e73ee4465c216969e21cd95742adc16474c19e6b6578f572d"),
    ("scripts/extend_constructive_completed_lower_campaign_v31.py", 23009, "0f807fa787d91f9459d86e542780886b46f0e662fceba7961873b2150dbb2467"),
    ("scripts/build_peano_library_channels_v31.py", 30953, "078f1beef9d84c98869faa7d770df53f246a4970463c120b2816d9709b8a4d9b"),
    ("scripts/verify_peano_library_channels_v31.py", 30140, "dd894183446c282e33366d063cca4a32e3778c88269cb1e99373eba3524ef357"),
    ("peano-lab/py/tests/test_constructive_completed_lower_explorer_v31.py", 29010, "d93bfbe3871eca9f4265701049379fa63e538abd72441ccae51214b8eeccd4a4"),
    ("peano-lab/py/tests/test_constructive_historical_publication_v31.py", 15147, "da2979c6547e0d3b29c12a2ace8be64270f40203ee9b7084d80aaf6af27296fa"),
    ("peano-lab/py/tests/test_constructive_alpha_v31_publication_process.py", 43555, "dd84a1245043424daf75dbe1b3a4683c9c9126f04ac2b6de25e7326df0cec41e"),
)


class CorrectionError(original.PublicationProcessError):
    """The exact presentation-only correction or its sources changed."""


@dataclass(frozen=True, slots=True)
class SourceBinding:
    root: Path
    pins: tuple[tuple[str, int, str], ...]

    def require_unchanged(self):
        for name, size, digest in self.pins:
            if not publication.safe_relative(name):
                raise CorrectionError("unsafe correction source path")
            publication.read_pinned(self.root / name, size, digest)

    def descriptor(self):
        return {name: {"bytes": size, "sha256": digest} for name, size, digest in self.pins}


def _observe_source(root: Path, name: str) -> tuple[str, int, str]:
    """Bounded import-time observation, followed by the strict pinned reader."""
    if not publication.safe_relative(name):
        raise CorrectionError("unsafe correction source path")
    path = root / name
    for parent in path.parents:
        if parent.is_symlink() or not parent.is_dir():
            raise CorrectionError("unsafe correction source ancestor")
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= original.MAX_FILE_BYTES:
        raise CorrectionError("nonregular or oversized correction source")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if (opened.st_dev, opened.st_ino, opened.st_size) != (before.st_dev, before.st_ino, before.st_size):
            raise CorrectionError("correction source changed while being opened")
        raw = stream.read(before.st_size + 1)
    pin = name, before.st_size, publication.digest(raw)
    publication.read_pinned(path, pin[1], pin[2])
    return pin


def _capture_sources() -> SourceBinding:
    result = SourceBinding(ROOT, (*FROZEN_SOURCES, _observe_source(ROOT, SOURCE), _observe_source(ROOT, TEST)))
    result.require_unchanged()
    return result


# Capture before any long proof run.  Reimporting a cached module cannot bless
# a changed wrapper/test file; every later boundary uses these same bytes.
_SOURCES = _capture_sources()


class _AggregateLink(HTMLParser):
    """Locate the actual header anchor without reserializing protected text."""

    VOID = frozenset("area base br col embed hr img input link meta param source track wbr".split())

    def __init__(self, text: str, old: str):
        super().__init__(convert_charrefs=False)
        self.text, self.old = text, old
        self.offsets = [0, *(match.end() for match in re.finditer("\n", text))]
        self.stack, self.matches = [], []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if len(attrs) != len(attributes):
            raise CorrectionError("duplicate aggregate HTML attribute")
        protected = any(name in {"pre", "code", "script", "style"} for name, _ in self.stack)
        if tag == "a" and not protected and attrs.get("href") == self.old:
            raw = self.get_starttag_text()
            if (not self.stack or self.stack[-1][0] != "nav"
                    or not any(name == "header" and "hero" in old.get("class", "").split() for name, old in self.stack)
                    or raw != '<a href="' + self.old + '">'):
                raise CorrectionError("the aggregate correction is not its exact header navigation")
            line, column = self.getpos()
            self.matches.append(self.offsets[line - 1] + column + len('<a href="'))
        if tag not in self.VOID:
            self.stack.append((tag, attrs))

    def handle_startendtag(self, tag, attrs):
        if tag not in self.VOID:
            raise CorrectionError("unexpected aggregate self-closing element")
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1][0] != tag:
            raise CorrectionError("unbalanced aggregate HTML")
        self.stack.pop()

    def corrected(self) -> bytes:
        self.feed(self.text)
        self.close()
        if self.stack or len(self.matches) != 1:
            raise CorrectionError("the aggregate must have exactly one original navigation anchor")
        start = self.matches[0]
        if self.text[start:start + len(self.old)] != self.old:
            raise CorrectionError("aggregate anchor offset changed")
        return (self.text[:start] + self.text[start + 3:]).encode("utf-8")


def _correct_completed_files(files: dict[str, bytes], *, catalog_sha256: str, sources: SourceBinding) -> dict[str, bytes]:
    """Pure byte correction only: this function cannot issue proof authority."""
    sources.require_unchanged()
    if (type(catalog_sha256) is not str or re.fullmatch(r"[0-9a-f]{64}", catalog_sha256) is None
            or type(files) is not dict or not {"index.html", "manifest.json"} <= files.keys()
            or not 0 < len(files) <= original.MAX_FILES):
        raise CorrectionError("invalid aggregate correction input")
    if any(not publication.safe_relative(name) or type(raw) is not bytes
           or not 0 < len(raw) <= original.MAX_FILE_BYTES for name, raw in files.items()):
        raise CorrectionError("invalid aggregate file bytes or path")
    raw_manifest = files["manifest.json"]
    if len(raw_manifest) > original.MAX_INVENTORY_BYTES:
        raise CorrectionError("aggregate manifest exceeds its original bound")
    manifest = publication.strict_json(raw_manifest)
    if (type(manifest) is not dict or publication.json_bytes(manifest) != raw_manifest
            or manifest.get("schema") != publication.SCHEMA + "-manifest"
            or manifest.get("catalog_sha256") != catalog_sha256
            or manifest.get("first_enrollment_catalog_sha256") != catalog_sha256
            or manifest.get("html_revision") != catalog_sha256[:12]
            or manifest.get("alpha_edition_version") != "v31"
            or manifest.get("alpha_first_enrolled_version") != "v31"
            or "presentation_correction" in manifest
            or type(manifest.get("files")) is not dict
            or type(manifest.get("file_count_excluding_manifest")) is not int
            or manifest["file_count_excluding_manifest"] != len(files) - 1
            or set(manifest["files"]) != set(files) - {"manifest.json"}):
        raise CorrectionError("the original aggregate manifest is not exact current input")
    inventory = {"files": manifest["files"], "file_count": len(files) - 1,
                 "html_count": sum(name.endswith(".html") for name in manifest["files"]),
                 "total_bytes": sum(len(raw) for name, raw in files.items() if name != "manifest.json")}
    original._validate_inventory(inventory)
    for name, pin in manifest["files"].items():
        if original._pin(files[name]) != pin:
            raise CorrectionError("a generated aggregate file differs from its original manifest pin")
    old = "../grand-campaign/?v=" + catalog_sha256[:12]
    index = _AggregateLink(files["index.html"].decode("utf-8"), old).corrected()
    corrected = dict(files)
    corrected["index.html"] = index
    pins = dict(manifest["files"])
    pins["index.html"] = original._pin(index)
    descriptor = sources.descriptor()
    manifest = {**manifest, "files": pins, "presentation_correction": {
        "schema": CORRECTION_SCHEMA, "scope": "one_navigation_href_only_not_proof_evidence",
        "path": "index.html", "old_href": old, "new_href": old[3:],
        "original_manifest": original._pin(raw_manifest), "original_index": original._pin(files["index.html"]),
        "sources": descriptor, "source_binding_sha256": publication.digest(original._canonical(descriptor)),
    }}
    corrected["manifest.json"] = publication.json_bytes(manifest)
    if len(corrected["manifest.json"]) > original.MAX_INVENTORY_BYTES:
        raise CorrectionError("corrected manifest exceeds its unchanged bound")
    sources.require_unchanged()
    return corrected


def _private_namespace(module) -> dict:
    """Keep unchanged function code in new globals, never mutate an old module."""
    namespace = dict(vars(module))
    for name, function in vars(module).items():
        if isinstance(function, FunctionType) and function.__module__ == module.__name__:
            copied = FunctionType(function.__code__, namespace, function.__name__, function.__defaults__, function.__closure__)
            copied.__kwdefaults__ = None if function.__kwdefaults__ is None else dict(function.__kwdefaults__)
            copied.__annotations__ = dict(function.__annotations__)
            namespace[name] = copied
    return namespace


def _compatible_historical_graph_schema(value: dict) -> dict:
    """Pure schema formatting, not a graph verifier or proof authority."""
    if type(value) is not dict:
        raise CorrectionError("historical graph schema must be an object")
    encoded = historical.canonical_bytes(value)
    for path, size, digest in EDITION_AGNOSTIC_SCHEMAS:
        raw = publication.read_pinned(ROOT / path, size, digest)
        if encoded == historical.canonical_bytes(publication.strict_json(raw)):
            return deepcopy(value)
    # The original reviewed v25-to-v31 migration and all its rejection cases
    # remain in force for every input except those two exact literal schemas.
    return historical._refresh_graph_schema(value)


def _historical_namespace(sources: SourceBinding) -> dict:
    sources.require_unchanged()
    namespace = _private_namespace(historical)
    namespace["_refresh_graph_schema"] = _compatible_historical_graph_schema
    return namespace


def _process_namespace(sources: SourceBinding) -> dict:
    """Copy every local function; never patch the frozen module's globals."""
    sources.require_unchanged()
    namespace = _private_namespace(original)
    # Mutable routing dictionaries also belong to this private namespace.
    namespace["OUTPUTS"], namespace["TESTS"] = dict(original.OUTPUTS), dict(original.TESTS)
    originals = dict(namespace)

    def phase_entries(context, phase):
        sources.require_unchanged()
        if phase == "completed":
            from build_constructive_completed_lower_explorer_v31 import build_files_from_live
            entries = _correct_completed_files(build_files_from_live(context), catalog_sha256=context.catalog_sha256, sources=sources).items()
        elif phase == "historical":
            entries = _historical_namespace(sources)["iter_files_from_live"](context)
        else:
            entries = originals["_phase_entries"](context, phase)
        yield from entries
        sources.require_unchanged()

    def guarded(function):
        def call(*args, **kwargs):
            sources.require_unchanged()
            result = function(*args, **kwargs)
            sources.require_unchanged()
            return result
        return call

    namespace["_phase_entries"] = phase_entries
    for name in ("_fork_phase", "_run_phase_tests", "_validate_tree", "_rss_bytes"):
        namespace[name] = guarded(originals[name])
    # The final guarded RSS check remains INSIDE the original transaction's
    # try/rollback.  Never guard a rollback rename or fail after installation.
    return namespace


def _publish_bound(context, check: bool, sources: SourceBinding):
    publication.require_live(context)
    if type(check) is not bool:
        raise CorrectionError("publication check must be an explicit Boolean")
    sources.require_unchanged()
    return _process_namespace(sources)["publish_from_live_context"](context, check)


def publish_from_live_context(context, check: bool):
    """All original fresh-proof and same-live UI gates remain mandatory."""
    return _publish_bound(context, check, _SOURCES)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--create-release", action="store_true", help="create the six additive release artifacts, then publish from the same fresh proof invocation")
    modes.add_argument("--check", action="store_true", help="freshly verify proofs and compare all three existing publication trees")
    args = parser.parse_args(argv)
    from verify_peano_library_channels_v31 import context_from_live_audit, verify_for_publication, proof_audit
    resource.setrlimit(resource.RLIMIT_CPU, proof_audit.CPU_LIMITS)
    jobs = 1 + len(proof_audit.registry()) + sum(len(item.principal_roots) for item in proof_audit.registry())
    signal.alarm(jobs * proof_audit.PARENT_TIMEOUT_SECONDS + 4 * proof_audit.WALL_SECONDS)
    _SOURCES.require_unchanged()
    if args.create_release:
        from build_peano_library_channels_v31 import build_payloads, check_or_write
        payloads, audit = build_payloads()
        _SOURCES.require_unchanged()
        check_or_write(payloads, check=False)
        context = context_from_live_audit(audit)
    else:
        context = verify_for_publication()
    _publish_bound(context, args.check, _SOURCES)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
