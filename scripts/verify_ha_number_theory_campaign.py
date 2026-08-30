#!/usr/bin/env python3
"""Validate the strict-HA number-theory campaign manifest.

This script validates planning metadata; it does not grant theorem authority.
Public references are checked against both the runtime theorem registry and the
arithmetic catalog. Candidate references are loaded only far enough to inspect
their factory-produced specifications—no candidate is admitted or replayed.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import importlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any, NoReturn


CAMPAIGN_FORMAT = "peano-ha-number-theory-campaign"
FORMAT_VERSION = 1
EXPECTED_LAYER_IDS = tuple(
    [f"K{index}" for index in range(7)]
    + [f"M{index}" for index in range(1, 6)]
)
ALLOWED_STATUSES = {
    "existing_public_core",
    "candidate_seed",
    "new",
    "blocked_on_dependency",
}
THEOREM_EVIDENCE_STATUSES = {
    "public_checked",
    "closed_checked_candidate",
    "body_checked_candidate",
    "planned",
    "blocked_on_dependency",
    "legacy_late_encoding",
}
RECEIPT_FIELDS = {
    "nodes",
    "depth",
    "objects",
    "edges",
    "reused",
    "cuts",
    "certificate_sha256",
}
PUBLIC_CATALOG_STATUSES = {"checked_existing", "checked_m20"}
REQUIRED_GATE_IDS = {
    "manifest_integrity",
    "statement_expansion",
    "candidate_body",
    "dependency_closure",
    "public_admission",
    "generated_integration",
    "heavy_closure",
}
K3_FORBIDDEN_REFERENCE_FRAGMENTS = (
    "beta",
    "crt",
    "chinese_remainder",
    "division",
    "remainder",
)
K3_FORBIDDEN_FOUNDATION_LABEL = "beta, CRT, division, or remainder"
SNAKE_IDENTIFIER = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*\Z")
LAYER_IDENTIFIER = re.compile(r"[KM][0-9]+\Z")
HEX_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
HEX_COMMIT = re.compile(r"[0-9a-f]{40}\Z")


class CampaignError(ValueError):
    """The campaign manifest violates its executable planning contract."""


def _fail(location: str, message: str) -> NoReturn:
    raise CampaignError(f"{location}: {message}")


def _object_from_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise CampaignError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream, object_pairs_hook=_object_from_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CampaignError(f"{path}: cannot read strict UTF-8 JSON: {exc}") from exc
    if type(value) is not dict:
        _fail(str(path), "top-level value must be an object")
    return value


def _fields(
    value: object,
    required: set[str],
    optional: set[str],
    location: str,
) -> dict[str, Any]:
    if type(value) is not dict:
        _fail(location, "must be an object")
    record: dict[str, Any] = value
    missing = required - set(record)
    extra = set(record) - required - optional
    if missing:
        _fail(location, "missing field(s): " + ", ".join(sorted(missing)))
    if extra:
        _fail(location, "unknown field(s): " + ", ".join(sorted(extra)))
    return record


def _text(value: object, location: str) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        _fail(location, "must be non-empty trimmed text")
    if any(ord(character) < 32 for character in value):
        _fail(location, "must not contain control characters")
    return value


def _snake_identifier(value: object, location: str) -> str:
    result = _text(value, location)
    if SNAKE_IDENTIFIER.fullmatch(result) is None:
        _fail(location, "must be a lowercase ASCII snake-case identifier")
    return result


def _string_list(
    value: object,
    location: str,
    *,
    nonempty: bool,
) -> list[str]:
    if type(value) is not list:
        _fail(location, "must be a list")
    result: list[str] = []
    for index, item in enumerate(value):
        result.append(_text(item, f"{location}[{index}]"))
    if nonempty and not result:
        _fail(location, "must not be empty")
    if len(result) != len(set(result)):
        _fail(location, "must not contain duplicates")
    return result


def _repository_file(root: Path, raw_path: object, location: str) -> Path:
    value = _text(raw_path, location)
    posix = PurePosixPath(value)
    if posix.is_absolute() or ".." in posix.parts or "." in posix.parts:
        _fail(location, "must be a normalized repository-relative path")
    resolved = (root / Path(*posix.parts)).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        _fail(location, "escapes the repository root")
    if not resolved.is_file():
        _fail(location, f"does not exist as a file: {value}")
    return resolved


def _public_bindings(repository_root: Path, registry_path: Path):
    expected_registry = (
        repository_root / "peano-lab" / "py" / "peano_lab" / "library" / "theorems.py"
    ).resolve()
    if registry_path.resolve() != expected_registry:
        _fail(
            "authority.public_registry",
            "must name the production peano_lab.library.theorems registry",
        )
    python_root = repository_root / "peano-lab" / "py"
    inserted = str(python_root)
    sys.path.insert(0, inserted)
    try:
        from peano_lab.library.theorems import THEOREMS, TheoremSpec
    except ImportError as exc:
        raise CampaignError(f"cannot import public Peano theorem registry: {exc}") from exc
    finally:
        try:
            sys.path.remove(inserted)
        except ValueError:
            pass
    names = [spec.name for spec in THEOREMS]
    if len(names) != len(set(names)):
        _fail("authority.public_registry", "contains duplicate theorem names")
    return {spec.name: spec for spec in THEOREMS}, TheoremSpec


def _catalog_public_names(catalog_path: Path) -> set[str]:
    catalog = _load_json(catalog_path)
    if catalog.get("format") != "peano-arithmetic-knowledge-catalog":
        _fail(str(catalog_path), "is not the arithmetic knowledge catalog")
    lemmas = catalog.get("lemmas")
    if type(lemmas) is not list:
        _fail(f"{catalog_path}.lemmas", "must be a list")
    names: list[str] = []
    for index, raw in enumerate(lemmas):
        if type(raw) is not dict:
            _fail(f"{catalog_path}.lemmas[{index}]", "must be an object")
        peano = raw.get("peano")
        if not isinstance(peano, dict) or not peano.get("existing_name"):
            continue
        name = _text(
            peano["existing_name"],
            f"{catalog_path}.lemmas[{index}].peano.existing_name",
        )
        status = raw.get("status")
        if status not in PUBLIC_CATALOG_STATUSES:
            _fail(
                f"{catalog_path}.lemmas[{index}].status",
                f"public theorem {name!r} has non-public catalog status {status!r}",
            )
        names.append(name)
    if len(names) != len(set(names)):
        _fail(str(catalog_path), "maps more than one lemma to a public theorem name")
    return set(names)


def _candidate_specs(
    repository_root: Path,
    path: Path,
    factory_name: str,
    theorem_spec: type,
) -> dict[str, Any]:
    python_root = repository_root / "peano-lab" / "py"
    try:
        relative = path.resolve().relative_to(python_root.resolve())
    except ValueError:
        _fail(str(path), "candidate module must live under peano-lab/py")
    if relative.suffix != ".py" or relative.name == "__init__.py":
        _fail(str(path), "candidate module must be a non-package Python source file")
    module_name = ".".join(relative.with_suffix("").parts)
    inserted = str(python_root)
    sys.path.insert(0, inserted)
    try:
        module = importlib.import_module(module_name)
    except (ImportError, RuntimeError, ValueError) as exc:
        raise CampaignError(f"{path}: cannot import candidate module: {exc}") from exc
    finally:
        try:
            sys.path.remove(inserted)
        except ValueError:
            pass
    factory = getattr(module, factory_name, None)
    if not callable(factory):
        _fail(str(path), f"does not expose callable factory {factory_name!r}")
    try:
        specs = factory(theorem_spec)
    except Exception as exc:
        raise CampaignError(
            f"{path}: candidate factory {factory_name!r} failed: {exc}"
        ) from exc
    if type(specs) is not tuple or not all(isinstance(item, theorem_spec) for item in specs):
        _fail(str(path), "candidate factory must return a tuple of TheoremSpec values")
    names = [item.name for item in specs]
    if len(names) != len(set(names)):
        _fail(str(path), "candidate factory returns duplicate theorem names")
    for index, item in enumerate(specs):
        item_location = f"{path}:{factory_name}[{index}]"
        _snake_identifier(item.name, f"{item_location}.name")
        if type(item.dependencies) is not tuple:
            _fail(f"{item_location}.dependencies", "must be a tuple")
        for dependency_index, dependency in enumerate(item.dependencies):
            _snake_identifier(
                dependency,
                f"{item_location}.dependencies[{dependency_index}]",
            )
    return {item.name: item for item in specs}


def _forbidden_k3_dependency_path(
    root_name: str,
    *,
    local_specs: dict[str, Any],
    public_specs: dict[str, Any],
) -> tuple[str, ...] | None:
    """Return a forbidden K3 dependency path reachable from ``root_name``.

    Candidate factories may expose several mutually dependent specifications
    while the manifest names only their intended K3 roots.  Follow the complete
    local factory graph, and continue through public theorem dependencies, so an
    innocuously named wrapper cannot conceal beta/CRT or division/remainder.
    """

    completed: set[str] = set()
    active: set[str] = set()

    def visit(name: str, path: tuple[str, ...]) -> tuple[str, ...] | None:
        folded = name.casefold()
        if any(fragment in folded for fragment in K3_FORBIDDEN_REFERENCE_FRAGMENTS):
            return (*path, name)
        if name in completed:
            return None
        if name in active:
            _fail(
                "K3.candidate_dependencies",
                "candidate dependency cycle: " + " -> ".join((*path, name)),
            )
        spec = local_specs.get(name) or public_specs.get(name)
        if spec is None:
            _fail(
                "K3.candidate_dependencies",
                "cannot classify dependency path: " + " -> ".join((*path, name)),
            )
        next_path = (*path, name)
        # Prefer the shortest explicit violation over an earlier unrelated
        # dependency whose candidate factory was not declared. This makes a
        # direct forbidden edge visible while still failing closed on unknowns
        # when no explicit forbidden edge exists.
        for dependency in spec.dependencies:
            folded_dependency = dependency.casefold()
            if any(
                fragment in folded_dependency
                for fragment in K3_FORBIDDEN_REFERENCE_FRAGMENTS
            ):
                return (*next_path, dependency)
        active.add(name)
        for dependency in spec.dependencies:
            forbidden = visit(dependency, next_path)
            if forbidden is not None:
                return forbidden
        active.remove(name)
        completed.add(name)
        return None

    return visit(root_name, ())


def validate_campaign(repository_root: Path, campaign_path: Path) -> dict[str, int]:
    """Validate ``campaign_path`` and return a small non-authoritative summary."""

    repository_root = repository_root.resolve()
    campaign = _load_json(campaign_path)
    root_location = str(campaign_path)
    record = _fields(
        campaign,
        {
            "format",
            "version",
            "campaign_id",
            "title",
            "source_specification",
            "baseline",
            "authority",
            "status_vocabulary",
            "theorem_evidence",
            "validation_gates",
            "representation_invariants",
            "layers",
        },
        set(),
        root_location,
    )
    if record["format"] != CAMPAIGN_FORMAT or record["version"] != FORMAT_VERSION:
        _fail(root_location, f"expected {CAMPAIGN_FORMAT!r} version {FORMAT_VERSION}")
    _snake_identifier(record["campaign_id"], f"{root_location}.campaign_id")
    _text(record["title"], f"{root_location}.title")

    source = _fields(
        record["source_specification"],
        {"file_name", "path", "sha256", "role"},
        set(),
        f"{root_location}.source_specification",
    )
    if Path(_text(source["file_name"], f"{root_location}.source_specification.file_name")).name != source["file_name"]:
        _fail(
            f"{root_location}.source_specification.file_name",
            "must be a portable base file name",
        )
    source_path = _repository_file(
        repository_root,
        source["path"],
        f"{root_location}.source_specification.path",
    )
    if source_path.name != "ha-number-theory-formalization-campaign-blueprint.md":
        _fail(
            f"{root_location}.source_specification.path",
            "must name the frozen in-repository campaign blueprint",
        )
    source_digest = _text(
        source["sha256"], f"{root_location}.source_specification.sha256"
    )
    if HEX_SHA256.fullmatch(source_digest) is None:
        _fail(f"{root_location}.source_specification.sha256", "must be lowercase SHA-256")
    if sha256(source_path.read_bytes()).hexdigest() != source_digest:
        _fail(
            f"{root_location}.source_specification.sha256",
            "does not match the frozen in-repository campaign blueprint",
        )
    _text(source["role"], f"{root_location}.source_specification.role")

    baseline = _fields(
        record["baseline"],
        {"branch", "commit"},
        set(),
        f"{root_location}.baseline",
    )
    _text(baseline["branch"], f"{root_location}.baseline.branch")
    if HEX_COMMIT.fullmatch(_text(baseline["commit"], f"{root_location}.baseline.commit")) is None:
        _fail(f"{root_location}.baseline.commit", "must be a lowercase 40-digit commit")

    authority = _fields(
        record["authority"],
        {
            "logic",
            "object_language",
            "kernel_entrypoint",
            "public_registry",
            "catalog",
            "candidate_policy",
            "definition_policy",
        },
        set(),
        f"{root_location}.authority",
    )
    for field in (
        "logic",
        "object_language",
        "kernel_entrypoint",
        "candidate_policy",
        "definition_policy",
    ):
        _text(authority[field], f"{root_location}.authority.{field}")
    if authority["logic"] != "first-order intuitionistic arithmetic":
        _fail(f"{root_location}.authority.logic", "must identify strict intuitionistic arithmetic")
    if authority["kernel_entrypoint"] != "peano_lab.kernel.checker.check":
        _fail(
            f"{root_location}.authority.kernel_entrypoint",
            "must use the intuitionistic check entrypoint",
        )
    registry_path = _repository_file(
        repository_root,
        authority["public_registry"],
        f"{root_location}.authority.public_registry",
    )
    catalog_path = _repository_file(
        repository_root,
        authority["catalog"],
        f"{root_location}.authority.catalog",
    )
    public_specs, theorem_spec = _public_bindings(repository_root, registry_path)
    public_names = set(public_specs)
    catalog_names = _catalog_public_names(catalog_path)

    vocabulary = record["status_vocabulary"]
    if type(vocabulary) is not dict or set(vocabulary) != ALLOWED_STATUSES:
        _fail(
            f"{root_location}.status_vocabulary",
            "must define exactly: " + ", ".join(sorted(ALLOWED_STATUSES)),
        )
    for status, description in vocabulary.items():
        _text(description, f"{root_location}.status_vocabulary.{status}")

    evidence = _fields(
        record["theorem_evidence"],
        {
            "status_vocabulary",
            "receipt_kind",
            "determinism_passes",
            "dne_nodes",
            "test_paths",
            "theorems",
        },
        set(),
        f"{root_location}.theorem_evidence",
    )
    evidence_vocabulary = evidence["status_vocabulary"]
    if (
        type(evidence_vocabulary) is not dict
        or set(evidence_vocabulary) != THEOREM_EVIDENCE_STATUSES
    ):
        _fail(
            f"{root_location}.theorem_evidence.status_vocabulary",
            "must define exactly: "
            + ", ".join(sorted(THEOREM_EVIDENCE_STATUSES)),
        )
    for status, description in evidence_vocabulary.items():
        _text(
            description,
            f"{root_location}.theorem_evidence.status_vocabulary.{status}",
        )
    if evidence["receipt_kind"] != "empty_context_intuitionistic_cut_closure":
        _fail(
            f"{root_location}.theorem_evidence.receipt_kind",
            "must identify the empty-context intuitionistic Cut closure receipt",
        )
    if type(evidence["determinism_passes"]) is not int or evidence["determinism_passes"] < 2:
        _fail(
            f"{root_location}.theorem_evidence.determinism_passes",
            "must be an integer of at least two",
        )
    if type(evidence["dne_nodes"]) is not int or evidence["dne_nodes"] != 0:
        _fail(
            f"{root_location}.theorem_evidence.dne_nodes",
            "must be exactly zero for the strict-HA campaign",
        )
    evidence_test_paths = _string_list(
        evidence["test_paths"],
        f"{root_location}.theorem_evidence.test_paths",
        nonempty=True,
    )
    for index, test_path in enumerate(evidence_test_paths):
        _repository_file(
            repository_root,
            test_path,
            f"{root_location}.theorem_evidence.test_paths[{index}]",
        )

    gates = record["validation_gates"]
    if type(gates) is not list or not gates:
        _fail(f"{root_location}.validation_gates", "must be a non-empty list")
    gate_order: dict[str, int] = {}
    for index, raw_gate in enumerate(gates):
        location = f"{root_location}.validation_gates[{index}]"
        gate = _fields(raw_gate, {"id", "order", "scope", "quick_command"}, set(), location)
        gate_id = _snake_identifier(gate["id"], f"{location}.id")
        if gate_id in gate_order:
            _fail(f"{location}.id", f"duplicate gate {gate_id!r}")
        if type(gate["order"]) is not int or gate["order"] != index:
            _fail(f"{location}.order", f"must equal list position {index}")
        gate_order[gate_id] = index
        _text(gate["scope"], f"{location}.scope")
        _text(gate["quick_command"], f"{location}.quick_command")
    if set(gate_order) != REQUIRED_GATE_IDS:
        _fail(
            f"{root_location}.validation_gates",
            "must define exactly the standard campaign gates",
        )

    invariants = _fields(
        record["representation_invariants"],
        {
            "k3_foundational_encoding",
            "k3_forbidden_foundations",
            "legacy_beta_role",
            "canonical_acceptance",
        },
        set(),
        f"{root_location}.representation_invariants",
    )
    _text(
        invariants["k3_foundational_encoding"],
        f"{root_location}.representation_invariants.k3_foundational_encoding",
    )
    forbidden_foundations = _string_list(
        invariants["k3_forbidden_foundations"],
        f"{root_location}.representation_invariants.k3_forbidden_foundations",
        nonempty=True,
    )
    if not {"godel_beta", "binary_crt", "finite_crt"}.issubset(forbidden_foundations):
        _fail(
            f"{root_location}.representation_invariants.k3_forbidden_foundations",
            "must forbid beta coding and both binary and finite CRT",
        )
    _text(
        invariants["legacy_beta_role"],
        f"{root_location}.representation_invariants.legacy_beta_role",
    )
    _string_list(
        invariants["canonical_acceptance"],
        f"{root_location}.representation_invariants.canonical_acceptance",
        nonempty=True,
    )

    layers = record["layers"]
    if type(layers) is not list or not layers:
        _fail(f"{root_location}.layers", "must be a non-empty list")
    layer_records: list[dict[str, Any]] = []
    layer_positions: dict[str, int] = {}
    candidate_cache: dict[tuple[Path, str], dict[str, Any]] = {}
    declared_candidate_specs: dict[str, Any] = {}
    declared_candidate_paths: dict[str, str] = {}
    declared_candidate_factories: dict[str, str] = {}
    candidate_reference_count = 0
    public_reference_count = 0
    for index, raw_layer in enumerate(layers):
        location = f"{root_location}.layers[{index}]"
        layer = _fields(
            raw_layer,
            {
                "id",
                "sequence",
                "release",
                "title",
                "status",
                "depends_on_layers",
                "target",
                "public_theorem_references",
                "candidate_modules",
                "remaining_gap",
                "validation",
            },
            set(),
            location,
        )
        layer_id = _text(layer["id"], f"{location}.id")
        if LAYER_IDENTIFIER.fullmatch(layer_id) is None:
            _fail(f"{location}.id", "must have the form K<number> or M<number>")
        if layer_id in layer_positions:
            _fail(f"{location}.id", f"duplicate layer {layer_id!r}")
        if type(layer["sequence"]) is not int or layer["sequence"] != index:
            _fail(f"{location}.sequence", f"must equal list position {index}")
        layer_positions[layer_id] = index
        _text(layer["release"], f"{location}.release")
        _text(layer["title"], f"{location}.title")
        status = _text(layer["status"], f"{location}.status")
        if status not in ALLOWED_STATUSES:
            _fail(f"{location}.status", f"unknown status {status!r}")
        dependencies = _string_list(
            layer["depends_on_layers"],
            f"{location}.depends_on_layers",
            nonempty=False,
        )
        for dependency in dependencies:
            if dependency not in layer_positions:
                _fail(
                    f"{location}.depends_on_layers",
                    f"dependency {dependency!r} must exist and precede {layer_id}",
                )
        _text(layer["target"], f"{location}.target")
        _text(layer["remaining_gap"], f"{location}.remaining_gap")

        public_references = _string_list(
            layer["public_theorem_references"],
            f"{location}.public_theorem_references",
            nonempty=False,
        )
        public_reference_count += len(public_references)
        for theorem_name in public_references:
            if theorem_name not in public_names:
                _fail(
                    f"{location}.public_theorem_references",
                    f"{theorem_name!r} is absent from the public theorem registry",
                )
            if theorem_name not in catalog_names:
                _fail(
                    f"{location}.public_theorem_references",
                    f"{theorem_name!r} is absent from the checked arithmetic catalog",
                )

        modules = layer["candidate_modules"]
        if type(modules) is not list:
            _fail(f"{location}.candidate_modules", "must be a list")
        candidate_keys: set[tuple[str, str]] = set()
        candidate_structured_references: list[str] = []
        layer_candidate_specs: dict[str, Any] = {}
        declared_candidate_names: list[str] = []
        for module_index, raw_module in enumerate(modules):
            module_location = f"{location}.candidate_modules[{module_index}]"
            module = _fields(
                raw_module,
                {"path", "factory", "theorem_names", "role"},
                set(),
                module_location,
            )
            candidate_path = _repository_file(
                repository_root,
                module["path"],
                f"{module_location}.path",
            )
            factory_name = _snake_identifier(module["factory"], f"{module_location}.factory")
            key = (str(candidate_path), factory_name)
            if key in candidate_keys:
                _fail(module_location, "duplicates a candidate path/factory pair in this layer")
            candidate_keys.add(key)
            theorem_names = _string_list(
                module["theorem_names"],
                f"{module_location}.theorem_names",
                nonempty=True,
            )
            for theorem_name in theorem_names:
                _snake_identifier(theorem_name, f"{module_location}.theorem_names")
            _text(module["role"], f"{module_location}.role")
            cache_key = (candidate_path, factory_name)
            if cache_key not in candidate_cache:
                candidate_cache[cache_key] = _candidate_specs(
                    repository_root,
                    candidate_path,
                    factory_name,
                    theorem_spec,
                )
            available_candidates = candidate_cache[cache_key]
            for candidate_name, candidate_spec in available_candidates.items():
                if candidate_name in layer_candidate_specs:
                    _fail(
                        module_location,
                        f"candidate theorem {candidate_name!r} is produced by more than "
                        "one factory in this layer",
                    )
                layer_candidate_specs[candidate_name] = candidate_spec
            for theorem_name in theorem_names:
                if theorem_name not in available_candidates:
                    _fail(
                        f"{module_location}.theorem_names",
                        f"candidate factory does not produce {theorem_name!r}",
                    )
                if theorem_name in public_names:
                    _fail(
                        f"{module_location}.theorem_names",
                        f"{theorem_name!r} is already public and must not be labeled a candidate",
                    )
                if theorem_name in declared_candidate_specs:
                    _fail(
                        f"{module_location}.theorem_names",
                        f"candidate {theorem_name!r} is declared in more than one layer",
                    )
                declared_candidate_specs[theorem_name] = available_candidates[theorem_name]
                declared_candidate_paths[theorem_name] = str(module["path"])
                declared_candidate_factories[theorem_name] = factory_name
            candidate_reference_count += len(theorem_names)
            declared_candidate_names.extend(theorem_names)
            candidate_structured_references.extend(
                [str(module["path"]), factory_name, *theorem_names]
            )

        validation = _fields(
            layer["validation"],
            {"path", "next_gate", "release_gate"},
            set(),
            f"{location}.validation",
        )
        path = _string_list(
            validation["path"],
            f"{location}.validation.path",
            nonempty=True,
        )
        for gate_id in path:
            if gate_id not in gate_order:
                _fail(f"{location}.validation.path", f"unknown gate {gate_id!r}")
        if [gate_order[gate_id] for gate_id in path] != sorted(
            gate_order[gate_id] for gate_id in path
        ):
            _fail(f"{location}.validation.path", "gates must follow global gate order")
        for field in ("next_gate", "release_gate"):
            gate_id = _text(validation[field], f"{location}.validation.{field}")
            if gate_id not in path:
                _fail(f"{location}.validation.{field}", "must occur in this layer's path")
        if gate_order[validation["next_gate"]] > gate_order[validation["release_gate"]]:
            _fail(
                f"{location}.validation",
                "next_gate must not follow release_gate",
            )

        if status == "existing_public_core" and not public_references:
            _fail(location, "existing_public_core requires public theorem evidence")
        if status == "candidate_seed" and not modules:
            _fail(location, "candidate_seed requires at least one candidate module")
        if status == "new" and (public_references or modules):
            _fail(location, "new status cannot claim aligned public or candidate evidence")

        if layer_id == "K3":
            if any(dependency not in {"K0", "K1", "K2"} for dependency in dependencies):
                _fail(location, "K3 may depend only on K0, K1, and K2")
            structured_references = [*public_references, *candidate_structured_references]
            for reference in structured_references:
                folded = reference.casefold()
                if any(fragment in folded for fragment in K3_FORBIDDEN_REFERENCE_FRAGMENTS):
                    _fail(
                        location,
                        "K3 foundational references may not use "
                        f"{K3_FORBIDDEN_FOUNDATION_LABEL}: {reference!r}",
                    )
            for root_name in (*public_references, *declared_candidate_names):
                forbidden_path = _forbidden_k3_dependency_path(
                    root_name,
                    local_specs=layer_candidate_specs,
                    public_specs=public_specs,
                )
                if forbidden_path is not None:
                    _fail(
                        location,
                        "K3 foundational dependency path may not use "
                        f"{K3_FORBIDDEN_FOUNDATION_LABEL}: "
                        + " -> ".join(forbidden_path),
                    )

        layer_records.append(layer)

    if tuple(layer_positions) != EXPECTED_LAYER_IDS:
        _fail(
            f"{root_location}.layers",
            "must contain K0-K6 followed by M1-M5 exactly once",
        )

    raw_theorem_evidence = evidence["theorems"]
    if type(raw_theorem_evidence) is not list or not raw_theorem_evidence:
        _fail(
            f"{root_location}.theorem_evidence.theorems",
            "must be a non-empty list",
        )
    evidence_names: list[str] = []
    closed_candidate_evidence_names: list[str] = []
    for index, raw_item in enumerate(raw_theorem_evidence):
        location = f"{root_location}.theorem_evidence.theorems[{index}]"
        item = _fields(
            raw_item,
            {
                "name",
                "status",
                "source_module",
                "statement_sha256",
                "receipt",
            },
            set(),
            location,
        )
        name = _snake_identifier(item["name"], f"{location}.name")
        if name in evidence_names:
            _fail(f"{location}.name", f"duplicate theorem evidence for {name!r}")
        evidence_names.append(name)
        status = _text(item["status"], f"{location}.status")
        if status not in THEOREM_EVIDENCE_STATUSES:
            _fail(f"{location}.status", f"unknown theorem evidence status {status!r}")
        if status not in {"public_checked", "closed_checked_candidate"}:
            _fail(
                f"{location}.status",
                "receipt-bearing campaign evidence must be public_checked or "
                "closed_checked_candidate",
            )
        source_path = _repository_file(
            repository_root,
            item["source_module"],
            f"{location}.source_module",
        )
        if status == "public_checked":
            source_factory = f"make_{source_path.stem}_theorems"
            source_key = (source_path, source_factory)
            if source_key not in candidate_cache:
                candidate_cache[source_key] = _candidate_specs(
                    repository_root,
                    source_path,
                    source_factory,
                    theorem_spec,
                )
            source_spec = candidate_cache[source_key].get(name)
            if source_spec is None:
                _fail(
                    f"{location}.source_module",
                    f"its conventional factory {source_factory!r} does not produce "
                    f"{name!r}",
                )
            if name not in public_names:
                _fail(
                    f"{location}.status",
                    f"{name!r} is not in the public theorem registry",
                )
            if name not in catalog_names:
                _fail(
                    f"{location}.status",
                    f"{name!r} is absent from the checked arithmetic catalog",
                )
            if name in declared_candidate_specs:
                _fail(
                    f"{location}.status",
                    f"{name!r} is public and must not also be declared as a candidate",
                )
            spec = public_specs[name]
            if source_spec != spec:
                _fail(
                    f"{location}.source_module",
                    "public specification differs from its isolated source factory",
                )
        else:
            closed_candidate_evidence_names.append(name)
            if name in public_names:
                _fail(
                    f"{location}.status",
                    f"{name!r} is public and cannot remain a closed candidate",
                )
            spec = declared_candidate_specs.get(name)
            if spec is None:
                _fail(
                    f"{location}.name",
                    f"{name!r} is not a declared campaign candidate",
                )
            if str(item["source_module"]) != declared_candidate_paths[name]:
                _fail(
                    f"{location}.source_module",
                    "does not match the candidate module declaration",
                )
            source_factory = declared_candidate_factories[name]
            source_key = (source_path, source_factory)
            source_spec = candidate_cache[source_key].get(name)
            if source_spec is None:
                _fail(
                    f"{location}.source_module",
                    f"its declared factory {source_factory!r} does not produce {name!r}",
                )
            if source_spec != spec:
                _fail(
                    f"{location}.source_module",
                    "declared candidate differs from its evidence source factory",
                )
        statement_digest = _text(
            item["statement_sha256"], f"{location}.statement_sha256"
        )
        if HEX_SHA256.fullmatch(statement_digest) is None:
            _fail(f"{location}.statement_sha256", "must be lowercase SHA-256")
        if sha256(spec.statement.encode()).hexdigest() != statement_digest:
            _fail(
                f"{location}.statement_sha256",
                "does not match the evidence theorem statement",
            )
        receipt = _fields(item["receipt"], RECEIPT_FIELDS, set(), f"{location}.receipt")
        for field in ("nodes", "depth", "objects"):
            if type(receipt[field]) is not int or receipt[field] <= 0:
                _fail(f"{location}.receipt.{field}", "must be a positive integer")
        for field in ("edges", "reused", "cuts"):
            if type(receipt[field]) is not int or receipt[field] < 0:
                _fail(f"{location}.receipt.{field}", "must be a non-negative integer")
        certificate_digest = _text(
            receipt["certificate_sha256"],
            f"{location}.receipt.certificate_sha256",
        )
        if HEX_SHA256.fullmatch(certificate_digest) is None:
            _fail(
                f"{location}.receipt.certificate_sha256",
                "must be lowercase SHA-256",
            )
    if set(closed_candidate_evidence_names) != set(declared_candidate_specs):
        missing = sorted(
            set(declared_candidate_specs) - set(closed_candidate_evidence_names)
        )
        extra = sorted(
            set(closed_candidate_evidence_names) - set(declared_candidate_specs)
        )
        _fail(
            f"{root_location}.theorem_evidence.theorems",
            "closed-candidate evidence must cover every declared candidate exactly "
            f"once; missing={missing}, extra={extra}",
        )
    status_by_layer = {layer["id"]: layer["status"] for layer in layer_records}
    for layer in layer_records:
        if layer["status"] != "blocked_on_dependency":
            continue
        incomplete = [
            dependency
            for dependency in layer["depends_on_layers"]
            if status_by_layer[dependency] != "existing_public_core"
        ]
        if not incomplete:
            _fail(
                f"{root_location}.layers[{layer['sequence']}].status",
                "blocked_on_dependency requires an earlier non-public or blocked dependency",
            )

    return {
        "layers": len(layer_records),
        "public_references": public_reference_count,
        "candidate_references": candidate_reference_count,
        "theorem_evidence": len(evidence_names),
        "validation_gates": len(gate_order),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=default_root,
        help="repository root (default: parent of scripts/)",
    )
    parser.add_argument(
        "--campaign",
        type=Path,
        default=default_root
        / "research"
        / "arithmetic-library"
        / "ha-number-theory-campaign.json",
        help="campaign JSON path",
    )
    args = parser.parse_args(argv)
    try:
        summary = validate_campaign(args.repository_root, args.campaign)
    except CampaignError as exc:
        print(f"HA campaign validation failed: {exc}", file=sys.stderr)
        return 1
    print(
        "HA campaign validation passed: "
        f"{summary['layers']} layers, "
        f"{summary['public_references']} public references, "
        f"{summary['candidate_references']} candidate references, "
        f"{summary['theorem_evidence']} theorem receipts, "
        f"{summary['validation_gates']} gates."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
