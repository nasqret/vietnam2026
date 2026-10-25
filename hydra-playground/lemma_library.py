"""Pinned self-contained native certificates, never executable lemma scripts.

Only an explicitly wired ``hydra-certified-lemmas-v1`` surface may use this
resolver. Loading does not modify the existing native catalogue or authority.
Every certificate is checked against its original closed statement by the
unchanged intuitionistic kernel. Dependencies are pinned manifest prerequisites
and exclusion edges; they do not confer proof authority or replace certificate
subtrees. The complete certificate must already be self-contained.

The enclosing worker still owns CPU/RSS/wall supervision. ``should_stop`` is
checked between bounded operations, not inside the recursive native checker.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields
import hashlib
import hmac
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import time
from types import MappingProxyType
import unicodedata

import peano_lab.kernel as kernel_package
from peano_lab.kernel import checker as kernel, formulas as f, proofs as p, terms as t, subst
from certificate_codec import (CodecError, CodecLimits, DEFAULT_LIMITS as CODEC_LIMITS,
                               bounded_json, decode_certificate, formula_identity)


SCHEMA = "hydra-certified-lemma-library-v1"
VERSION = 1
CAPABILITY_PROFILE = "hydra-certified-lemmas-v1"
KERNEL_FILES = MappingProxyType({
    "__init__.py": "e4d6cd30f2468de77d6e02fb71bf84394ff8330d264602bb9398df1ad194bc84",
    "checker.py": "d7dfb9c256214695b9b7c427afb3b22291b9659b15defb16c57751b536a02ebe",
    "formulas.py": "b449bf50c7c8f6a93ff0dea067d9cfb048b3033f4e761e61c71d55e4f9a57645",
    "proofs.py": "1ff7c055e64f784b45f00488b00fe945a57e4d872e520382da779d1d775f28f2",
    "subst.py": "0c685d14aa8494141181b79f25f72699da044526054a80a689e2d5af519226b3",
    "terms.py": "f49313e209a8861918e3aaca38ddfb27f147f824308af699ab5cc1aafbb6dff5",
})
KERNEL_IDENTITY_SHA256 = hashlib.sha256(json.dumps(
    {"logic": "intuitionistic", "files": dict(KERNEL_FILES)}, sort_keys=True,
    separators=(",", ":")).encode()).hexdigest()


class LemmaLibraryError(ValueError):
    """Invalid catalogue, rejected certificate or bounded operation failure."""


class ExcludedLemmaError(LemmaLibraryError):
    """The fixed target/reservation policy disallows this lemma."""


@dataclass(frozen=True, slots=True)
class LibraryLimits:
    max_manifest_bytes: int = 8 * 1024 * 1024
    max_total_bytes: int = 8 * 1024 * 1024
    max_entries: int = 128
    max_dependencies: int = 16
    max_dependency_depth: int = 8
    max_statement_bytes: int = 4096
    max_retrieval_work: int = 50_000

    def __post_init__(self):
        maxima = (8 * 1024 * 1024, 8 * 1024 * 1024, 128, 16, 8, 4096, 50_000)
        for field, maximum in zip(fields(self), maxima):
            value = getattr(self, field.name)
            if type(value) is not int or not 1 <= value <= maximum:
                raise LemmaLibraryError(field.name + " must be a positive integer at most " + str(maximum))


DEFAULT_LIMITS = LibraryLimits()
_LOADER_TOKEN = object()


def _require(condition, message):
    if not condition:
        raise LemmaLibraryError(message)


def _cancel(should_stop):
    if should_stop is not None and should_stop():
        raise LemmaLibraryError("Lemma operation cancelled by caller.")


def _hash(value, label):
    _require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value), "Invalid " + label + " hash.")
    return value


def _name(value, label="lemma"):
    _require(type(value) is str and re.fullmatch(r"[a-z][a-z0-9_]{0,79}", value), "Invalid " + label + " name.")
    return value


def _family(value):
    _require(type(value) is str and re.fullmatch(r"[a-z][a-z0-9_.-]{0,79}", value), "Invalid family label.")
    return value


def _relative_path(value):
    _require(type(value) is str and 0 < len(value) <= 240, "Invalid certificate path.")
    parts = PurePosixPath(value).parts
    _require(parts and value == "/".join(parts) and not value.startswith("/") and len(parts) <= 8,
             "Certificate path must be a canonical relative path.")
    _require(all(part not in {".", ".."} and re.fullmatch(r"[a-zA-Z0-9_][a-zA-Z0-9_.-]{0,79}", part)
                 for part in parts), "Certificate path contains an unsafe component.")
    return parts


def _open_root(directory):
    """Open every absolute directory component without following symlinks."""
    path = Path(directory)
    _require(".." not in path.parts, "A library directory cannot contain '..'.")
    absolute = Path(os.path.abspath(path))
    _require(hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_DIRECTORY"), "This platform lacks safe directory opening.")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    current = os.open(absolute.anchor, flags)
    try:
        for part in absolute.parts[1:]:
            next_fd = os.open(part, flags, dir_fd=current)
            os.close(current); current = next_fd
        return current
    except BaseException:
        os.close(current)
        raise


def _read_at(root_fd, relative, maximum):
    """Read a regular, stable bounded file through an anchored directory FD."""
    parts = _relative_path(relative)
    parent = os.dup(root_fd)
    file_fd = None
    # A FIFO must not block in open() before fstat can reject its file type.
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0)
    try:
        for part in parts[:-1]:
            next_fd = os.open(part, flags | os.O_DIRECTORY, dir_fd=parent)
            os.close(parent); parent = next_fd
        file_fd = os.open(parts[-1], flags, dir_fd=parent)
        before = os.fstat(file_fd)
        _require(stat.S_ISREG(before.st_mode) and 0 < before.st_size <= maximum, "Expected a bounded regular file: " + relative)
        chunks, total = [], 0
        while True:
            block = os.read(file_fd, min(64 * 1024, maximum + 1 - total))
            if not block:
                break
            chunks.append(block); total += len(block)
            _require(total <= maximum, "File exceeded its byte limit while reading.")
        after = os.fstat(file_fd)
        identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        _require(identity(before) == identity(after) and total == before.st_size, "File changed while reading.")
        return b"".join(chunks)
    finally:
        if file_fd is not None:
            os.close(file_fd)
        os.close(parent)


def _verify_kernel_sources(should_stop):
    directory = Path(kernel.__file__).absolute().parent
    for module in (kernel_package, kernel, f, p, t, subst):
        _require(Path(module.__file__).absolute().parent == directory, "Native kernel modules do not share one source directory.")
    root_fd = _open_root(directory)
    try:
        for filename, expected in KERNEL_FILES.items():
            _cancel(should_stop)
            raw = _read_at(root_fd, filename, 256 * 1024)
            _require(hashlib.sha256(raw).hexdigest() == expected, "Original native kernel bytes changed: " + filename)
    finally:
        os.close(root_fd)


def _closed_formula(statement, *, maximum=4096, should_stop=None):
    _require(type(statement) is str and statement and len(statement.encode("utf-8")) <= maximum,
             "Statement must be bounded nonempty text.")
    _require(not any(unicodedata.category(c) in {"Cc", "Cf", "Cs", "Zl", "Zp"} for c in statement),
             "Statement contains control characters.")
    _cancel(should_stop)
    try:
        formula, free_names = f.parse_formula_with_names(statement)
        identity = formula_identity(formula, should_stop=should_stop)
    except (ValueError, TypeError, RecursionError) as error:
        raise LemmaLibraryError("Malformed or oversized native statement.") from error
    _require(not free_names, "Lemma statements must have no free names.")
    # Explicit #indices can bypass the parser's free-name table.
    pending, work = [(formula, 0)], 0
    while pending:
        if work % 64 == 0:
            _cancel(should_stop)
        work += 1
        _require(work <= CODEC_LIMITS.max_graph_occurrences, "Closed-statement inspection limit exceeded.")
        node, binders = pending.pop()
        if type(node) is t.Var:
            _require(node.index < binders, "Lemma statement has an unbound de Bruijn variable.")
        elif type(node) in (f.Forall, f.Exists):
            pending.append((node.body, binders + 1))
        elif type(node) in (t.Add, t.Mul, f.Eq, f.And, f.Or):
            pending.extend(((node.left, binders), (node.right, binders)))
        elif type(node) is f.Imp:
            pending.extend(((node.antecedent, binders), (node.consequent, binders)))
        elif type(node) is t.Succ:
            pending.append((node.term, binders))
        else:
            _require(type(node) in (t.Zero, f.Bot), "Unsupported native statement constructor.")
    return formula, identity


def statement_identity(statement, *, should_stop=None):
    """Closed native AST identity, invariant under binder spelling only."""
    return _closed_formula(statement, should_stop=should_stop)[1]


@dataclass(frozen=True, slots=True)
class Exclusions:
    statement_ids: frozenset[str] = frozenset()
    names: frozenset[str] = frozenset()
    families: frozenset[str] = frozenset()

    def __post_init__(self):
        for name in ("statement_ids", "names", "families"):
            value = getattr(self, name)
            _require(type(value) is frozenset and len(value) <= 1024, "Exclusion sets must be bounded immutable sets.")
        for value in self.statement_ids:
            _hash(value, "reserved statement identity")
        for value in self.names:
            _name(value)
        for value in self.families:
            _family(value)


def make_exclusions(*, statements=(), names=(), families=(), should_stop=None):
    """Trusted caller hook; no evaluation suite is read implicitly."""
    _require(type(statements) in (tuple, list) and len(statements) <= 1024, "Reserved statements must be a bounded sequence.")
    _require(type(names) in (tuple, list, frozenset) and len(names) <= 1024, "Reserved names must be a bounded sequence.")
    _require(type(families) in (tuple, list, frozenset) and len(families) <= 1024, "Reserved families must be a bounded sequence.")
    return Exclusions(frozenset(statement_identity(s, should_stop=should_stop) for s in statements),
                      frozenset(names), frozenset(families))


@dataclass(frozen=True, slots=True)
class CheckedLemma:
    name: str
    statement: str
    formula: f.Formula
    certificate: p.Proof
    family: str
    dependencies: tuple[str, ...]
    statement_id: str
    certificate_sha256: str
    proof_cost: dict

    def metadata(self):
        return {"name": self.name, "statement": self.statement, "family": self.family,
                "dependencies": list(self.dependencies), "statement_id": self.statement_id,
                "certificate_sha256": self.certificate_sha256}


def _features(formula, *, maximum, should_stop):
    """Small constructor/path features; no symbolic proof search or matching."""
    result, pending, work = Counter(), [(formula, "root", 0)], 0
    while pending:
        if work % 64 == 0:
            _cancel(should_stop)
        work += 1
        _require(work <= maximum, "Retrieval feature work limit exceeded.")
        node, parent, depth = pending.pop()
        name = type(node).__name__
        result["symbol:" + name] += 1
        if depth <= 3:
            result["shape:" + parent + ":" + name] += 1
        if type(node) in (f.Forall, f.Exists):
            pending.append((node.body, name, depth + 1))
        elif type(node) in (t.Add, t.Mul, f.Eq, f.And, f.Or):
            pending.extend(((node.left, name + ".left", depth + 1), (node.right, name + ".right", depth + 1)))
        elif type(node) is f.Imp:
            pending.extend(((node.antecedent, name + ".left", depth + 1), (node.consequent, name + ".right", depth + 1)))
        elif type(node) is t.Succ:
            pending.append((node.term, name, depth + 1))
        else:
            _require(type(node) in (t.Var, t.Zero, f.Bot), "Unsupported retrieval formula.")
    return result, work


@dataclass(frozen=True, slots=True, init=False, eq=False, repr=False)
class LemmaLibrary:
    """Immutable verified snapshot with explicit, target-bound resolution."""

    _entries: object
    excluded: object
    manifest_sha256: str
    target_formula: object
    target_sha256: str | None
    capability_label: str | None
    _limits: LibraryLimits
    _should_stop: object
    _features: object
    _verification: object

    def __init__(self, entries, excluded, manifest_sha256, target_formula, target_id, limits, should_stop, verification, *, _token=None):
        _require(_token is _LOADER_TOKEN, "LemmaLibrary snapshots must be produced by load_library.")
        object.__setattr__(self, "_entries", MappingProxyType(dict(entries)))
        object.__setattr__(self, "excluded", MappingProxyType(dict(excluded)))
        object.__setattr__(self, "manifest_sha256", manifest_sha256)
        object.__setattr__(self, "target_formula", target_formula)
        object.__setattr__(self, "target_sha256", target_id)
        binding = json.dumps({"profile": CAPABILITY_PROFILE, "manifest": manifest_sha256,
                              "target": target_id}, sort_keys=True, separators=(",", ":")).encode()
        object.__setattr__(self, "capability_label", CAPABILITY_PROFILE + "-" + hashlib.sha256(binding).hexdigest()
                           if target_id is not None else None)
        object.__setattr__(self, "_limits", limits)
        object.__setattr__(self, "_should_stop", should_stop)
        object.__setattr__(self, "_verification", MappingProxyType(dict(verification)))
        all_features = {}
        remaining = limits.max_retrieval_work
        for name in self.names:
            features, used = _features(self._entries[name].formula, maximum=remaining, should_stop=should_stop)
            all_features[name] = MappingProxyType(dict(features))
            remaining -= used
        object.__setattr__(self, "_features", MappingProxyType(all_features))

    @property
    def target_id(self):
        return self.target_sha256

    @property
    def names(self):
        return tuple(name for name in self._entries if name not in self.excluded) if self.target_id is not None else ()

    @property
    def available_names(self):
        return self.names

    @property
    def verification(self):
        """JSON-safe copy; preload checks are distinct from later native uses."""
        return dict(self._verification)

    def validate_target(self, formula):
        """Accept the original closed AST only; spelling changes are harmless."""
        _cancel(self._should_stop)
        _require(self.target_formula is not None and self.target_sha256 is not None,
                 "An original target is required before lemma use.")
        try:
            actual = formula_identity(formula, should_stop=self._should_stop)
        except CodecError as error:
            raise LemmaLibraryError("Invalid original target formula.") from error
        _require(actual == self.target_sha256 and formula == self.target_formula,
                 "The proof state's original target changed.")
        return True

    def resolve(self, name):
        _cancel(self._should_stop)
        _require(self.target_id is not None, "An original target is required before lemma resolution.")
        _name(name)
        _require(name in self._entries, "Unknown certified lemma: " + name)
        if name in self.excluded:
            raise ExcludedLemmaError("Lemma excluded by the fixed target/reservation policy: " + name)
        return self._entries[name]

    def retrieve(self, goal, *, limit=4):
        """Return at most four deterministic structural/symbol suggestions."""
        _require(self.target_id is not None, "An original target is required before retrieval.")
        _require(type(limit) is int and 1 <= limit <= 4, "Retrieval limit must be 1..4.")
        try:
            formula_identity(goal, should_stop=self._should_stop)  # No proof check.
        except CodecError as error:
            raise LemmaLibraryError("Invalid retrieval formula.") from error
        wanted, _ = _features(goal, maximum=self._limits.max_retrieval_work, should_stop=self._should_stop)
        ranked = []
        for name in self.names:
            _cancel(self._should_stop)
            features = self._features[name]
            score = sum(min(count, wanted.get(feature, 0)) * (3 if feature.startswith("shape:") else 1)
                        for feature, count in features.items())
            if score:
                ranked.append((-score, self._entries[name].proof_cost["distinct_objects"], name))
        ranked.sort()
        return tuple({**self._entries[name].metadata(), "score": -score,
                      "retrieval": "bounded_native_structure_and_symbols_v1"}
                     for score, _, name in ranked[:limit])


def load_library(directory, *, expected_manifest_sha256, exclusions=Exclusions(), target=None,
                 exclusion_hook=None, limits=DEFAULT_LIMITS, codec_limits=CODEC_LIMITS, should_stop=None):
    """Authenticate all entries and check every original statement from scratch.

``target=None`` permits validation only: resolve/retrieve then reject. The
optional trusted hook receives (metadata, native_formula) and must return a
boolean. Metadata is never executable. Exact reserved/target formula payloads
inside certificates are excluded too; general semantic equivalence and
implicit mathematical consequences are deliberately not decided here.
"""
    _require(type(limits) is LibraryLimits and type(codec_limits) is CodecLimits, "Invalid library/codec limits.")
    _require(type(exclusions) is Exclusions, "Expected immutable Exclusions.")
    _require(should_stop is None or callable(should_stop), "should_stop must be callable.")
    _require(exclusion_hook is None or callable(exclusion_hook), "exclusion_hook must be callable.")
    expected = _hash(expected_manifest_sha256, "manifest")
    root_fd = None
    try:
        _cancel(should_stop)
        root_fd = _open_root(directory)
        raw = _read_at(root_fd, "manifest.json", limits.max_manifest_bytes)
        _require(hmac.compare_digest(hashlib.sha256(raw).hexdigest(), expected), "Manifest hash mismatch.")
        manifest = bounded_json(raw, maximum=limits.max_manifest_bytes)
        _require(type(manifest) is dict and set(manifest) == {"schema", "version", "capability_profile", "kernel_identity_sha256", "entries"}, "Invalid manifest fields.")
        _require(manifest["schema"] == SCHEMA and type(manifest["version"]) is int and manifest["version"] == VERSION, "Unsupported manifest version.")
        _require(manifest["capability_profile"] == CAPABILITY_PROFILE and manifest["kernel_identity_sha256"] == KERNEL_IDENTITY_SHA256, "Manifest authority/kernel identity mismatch.")
        rows = manifest["entries"]
        _require(type(rows) is list and 1 <= len(rows) <= limits.max_entries, "Invalid catalogue entry count.")
        _verify_kernel_sources(should_stop)
        target_formula, target_id = _closed_formula(target, should_stop=should_stop) if target is not None else (None, None)
        prepared, depths, paths, total = {}, {}, set(), len(raw)
        for row in rows:
            _cancel(should_stop)
            _require(type(row) is dict and set(row) == {"name", "statement", "statement_sha256", "family", "dependencies", "certificate"}, "Invalid lemma entry fields.")
            name = _name(row["name"]); family = _family(row["family"])
            _require(name not in prepared, "Repeated lemma name.")
            formula, identity = _closed_formula(row["statement"], maximum=limits.max_statement_bytes, should_stop=should_stop)
            _require(hashlib.sha256(row["statement"].encode()).hexdigest() == _hash(row["statement_sha256"], "statement"), "Statement hash mismatch.")
            dependencies = row["dependencies"]
            _require(type(dependencies) is list and len(dependencies) <= limits.max_dependencies, "Invalid dependency list.")
            for dependency in dependencies:
                _name(dependency, "dependency")
                _require(dependency in prepared, "Dependencies must name earlier entries in the pinned manifest.")
            _require(len(set(dependencies)) == len(dependencies), "Repeated dependency name.")
            depth = 1 + max((depths[n] for n in dependencies), default=0)
            _require(depth <= limits.max_dependency_depth, "Manifest dependency depth limit exceeded.")
            descriptor = row["certificate"]
            _require(type(descriptor) is dict and set(descriptor) == {"path", "bytes", "sha256"}, "Invalid certificate descriptor.")
            _relative_path(descriptor["path"])
            _require(descriptor["path"].endswith(".json") and descriptor["path"] != "manifest.json" and descriptor["path"] not in paths,
                     "Certificate paths must be distinct JSON files.")
            _require(type(descriptor["bytes"]) is int and 1 <= descriptor["bytes"] <= codec_limits.max_bytes, "Invalid certificate byte size.")
            _hash(descriptor["sha256"], "certificate")
            total += descriptor["bytes"]
            _require(total <= limits.max_total_bytes, "Total catalogue/certificate byte limit exceeded.")
            prepared[name] = (row, formula, identity); depths[name] = depth; paths.add(descriptor["path"])
        checked, excluded = {}, {}
        certificate_bytes_read, native_check_seconds = 0, 0.0
        for name, (row, formula, identity) in prepared.items():
            _cancel(should_stop)
            descriptor = row["certificate"]
            payload = _read_at(root_fd, descriptor["path"], codec_limits.max_bytes)
            certificate_bytes_read += len(payload)
            _require(len(payload) == descriptor["bytes"], "Certificate byte size differs from its manifest.")
            decoded = decode_certificate(payload, expected_sha256=descriptor["sha256"], limits=codec_limits, should_stop=should_stop)
            _require(decoded.formula == formula, "Certificate formula differs from the exact manifest statement.")
            before_check = time.monotonic()
            accepted = kernel.check((), decoded.certificate, formula)
            native_check_seconds += time.monotonic() - before_check
            _require(accepted is True, "Original intuitionistic kernel rejected lemma: " + name)
            _cancel(should_stop)
            entry = CheckedLemma(name, row["statement"], formula, decoded.certificate, row["family"],
                                 tuple(row["dependencies"]), identity, decoded.sha256, decoded.metrics["proof_cost"])
            reasons = []
            if name in exclusions.names:
                reasons.append("reserved_name")
            if row["family"] in exclusions.families:
                reasons.append("reserved_template_family")
            if decoded.formula_identities & exclusions.statement_ids:
                reasons.append("reserved_statement_or_formula_payload")
            if target_id is not None and target_id in decoded.formula_identities:
                reasons.append("original_target_or_formula_payload")
            if any(dependency in excluded for dependency in entry.dependencies):
                reasons.append("excluded_declared_dependency")
            if exclusion_hook is not None:
                decision = exclusion_hook(entry.metadata(), formula)
                _require(type(decision) is bool, "Exclusion hook must return a boolean.")
                if decision:
                    reasons.append("caller_exclusion_hook")
            checked[name] = entry
            if reasons:
                excluded[name] = tuple(reasons)
        verification = {"certificates_checked": len(checked), "native_kernel_checks": len(checked),
                        "certificate_bytes_read": certificate_bytes_read, "manifest_bytes_read": len(raw),
                        "catalogue_bytes_read": len(raw) + certificate_bytes_read,
                        "kernel_source_files_rehashed": len(KERNEL_FILES),
                        "native_kernel_check_seconds": native_check_seconds,
                        "all_entries_checked_before_return": True, "excluded_entries": len(excluded),
                        "counts_scope": "Catalogue preload only; excludes subsequent use_checked and original-goal final checks."}
        return LemmaLibrary(checked, excluded, expected, target_formula, target_id, limits, should_stop,
                            verification, _token=_LOADER_TOKEN)
    except (CodecError, OSError, UnicodeError, RecursionError) as error:
        raise LemmaLibraryError("Certificate library load failed: " + str(error)) from error
    finally:
        if root_fd is not None:
            os.close(root_fd)


def resolve_lemma(library, name):
    """Explicit UI hook; never falls back to the old executable catalogue."""
    _require(type(library) is LemmaLibrary, "Expected a verified LemmaLibrary snapshot.")
    return library.resolve(name)


__all__ = ["SCHEMA", "VERSION", "CAPABILITY_PROFILE", "KERNEL_FILES", "KERNEL_IDENTITY_SHA256",
           "LemmaLibraryError", "ExcludedLemmaError", "LibraryLimits", "DEFAULT_LIMITS",
           "Exclusions", "make_exclusions", "statement_identity", "CheckedLemma",
           "LemmaLibrary", "load_library", "resolve_lemma"]
