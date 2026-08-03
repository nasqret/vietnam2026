#!/usr/bin/env python3
"""Validate the strict-HA definition and representation freeze.

The freeze is planning and audit metadata, not parser, kernel, definition, or
theorem authority.  This verifier therefore resolves every authoritative fact
back to repository sources: file bytes, the live defined-syntax registry, and
the production theorem registry.  Optional API replay uses only the default
intuitionistic checker.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any, NoReturn


FREEZE_SCHEMA = "peano-lab-ha-definition-representation-freeze-v1"
FREEZE_VERSION = 1
HEX_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
HEX_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_]*\Z")
SNAKE_IDENTIFIER = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*\Z")

EXPECTED_CLASSIFICATIONS = {
    "Le": "frozen-compatible",
    "Lt": "frozen-compatible",
    "Dvd": "frozen-compatible",
    "DivRem": "frozen-compatible",
    "IsGCD": "frozen-compatible",
    "Coprime": "frozen-compatible",
    "ModEq": "bridge-required",
    "Prime": "bridge-required",
    "BalancedBezout": "bridge-required",
    "BetaAt": "legacy-late",
    "Product": "legacy-late",
}
EXPECTED_CLASSIFICATION_VOCABULARY = set(EXPECTED_CLASSIFICATIONS.values())
BRIDGE_STATUSES = {
    "required_not_yet_claimed",
    "blocked_until_non_crt_signed_code_freeze",
    "late_after_k3",
    "late_after_k3_and_crt",
    "late_after_k3_k6_and_crt",
}
EXPECTED_OBLIGATION_IDS = {"K3.PAIR", "K3.LIST", "K3.SIGNED", "K6.LIST_PRODUCT"}
EXPECTED_FOUNDATIONAL_ORDER = (
    "primitive_recursive_pair_or_cell_code",
    "explicit_length_canonical_list_code",
    "list_validity_and_functional_decoding",
    "finite_functions_and_list_folds",
    "binary_crt",
    "finite_crt",
    "optional_beta_interoperability",
)
EXPECTED_INTUITIONISTIC_NODES = {
    "Hyp",
    "ImpIntro",
    "ImpElim",
    "Cut",
    "AndIntro",
    "AndElimL",
    "AndElimR",
    "OrIntroL",
    "OrIntroR",
    "OrElim",
    "BotElim",
    "ForallIntro",
    "ForallElim",
    "ExistsIntro",
    "ExistsElim",
    "EqRefl",
    "EqSym",
    "EqTrans",
    "CongS",
    "CongAdd",
    "CongMul",
    "EqSubst",
    "Axiom",
    "Ind",
}
EXPECTED_AXIOMS = {
    "PA1": "forall x. ~(S x = 0)",
    "PA2": "forall x y. S x = S y -> x = y",
    "PA3": "forall x. x + 0 = x",
    "PA4": "forall x y. x + S y = S (x + y)",
    "PA5": "forall x. x * 0 = 0",
    "PA6": "forall x y. x * S y = x * y + x",
}


class FreezeError(ValueError):
    """The freeze violates its executable audit contract."""


def _fail(location: str, message: str) -> NoReturn:
    raise FreezeError(f"{location}: {message}")


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise FreezeError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream, object_pairs_hook=_strict_object)
    except FreezeError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FreezeError(f"{path}: cannot read strict UTF-8 JSON: {exc}") from exc
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


def _string_list(
    value: object,
    location: str,
    *,
    nonempty: bool,
) -> list[str]:
    if type(value) is not list:
        _fail(location, "must be a list")
    result = [_text(item, f"{location}[{index}]") for index, item in enumerate(value)]
    if nonempty and not result:
        _fail(location, "must not be empty")
    if len(result) != len(set(result)):
        _fail(location, "must not contain duplicates")
    return result


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise FreezeError(f"{path}: cannot hash file: {exc}") from exc
    return digest.hexdigest()


def _sha256(value: object, location: str) -> str:
    result = _text(value, location)
    if HEX_SHA256.fullmatch(result) is None:
        _fail(location, "must be a lowercase 64-digit SHA-256")
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


def _verify_file_hash(path: Path, expected: object, location: str) -> None:
    expected_hash = _sha256(expected, location)
    actual_hash = _sha256_file(path)
    if expected_hash != actual_hash:
        _fail(location, f"does not match {path}: expected {actual_hash}")


def _load_authorities(repository_root: Path):
    python_root = repository_root / "peano-lab" / "py"
    inserted = str(python_root)
    sys.path.insert(0, inserted)
    try:
        from peano_lab.library import defined_syntax
        from peano_lab.library import theorems
    except ImportError as exc:
        raise FreezeError(f"cannot import Peano Lab authorities: {exc}") from exc
    finally:
        try:
            sys.path.remove(inserted)
        except ValueError:
            pass
    public_names = [spec.name for spec in theorems.THEOREMS]
    if len(public_names) != len(set(public_names)):
        _fail("peano_lab.library.theorems.THEOREMS", "contains duplicate names")
    return defined_syntax, theorems, set(public_names)


def _validate_baseline(
    root: Path,
    raw: object,
    location: str,
    defined_syntax: Any,
) -> None:
    baseline = _fields(
        raw,
        {
            "repository_commit",
            "repository_branch",
            "controlling_spec_path",
            "controlling_spec_sha256",
            "defined_syntax_registry_id",
            "defined_syntax_registry_version",
            "defined_syntax_registry_sha256",
            "defined_syntax_source_sha256",
            "definition_inventory_path",
            "definition_inventory_sha256",
        },
        set(),
        location,
    )
    commit = _text(baseline["repository_commit"], f"{location}.repository_commit")
    if HEX_COMMIT.fullmatch(commit) is None:
        _fail(f"{location}.repository_commit", "must be a lowercase 40-digit commit")
    _text(baseline["repository_branch"], f"{location}.repository_branch")

    specification = _repository_file(
        root, baseline["controlling_spec_path"], f"{location}.controlling_spec_path"
    )
    if specification.name != "ha-number-theory-formalization-campaign-blueprint.md":
        _fail(
            f"{location}.controlling_spec_path",
            "must name the frozen in-repository campaign blueprint",
        )
    _verify_file_hash(
        specification,
        baseline["controlling_spec_sha256"],
        f"{location}.controlling_spec_sha256",
    )

    if baseline["defined_syntax_registry_id"] != defined_syntax.DEFINED_SYNTAX_REGISTRY_ID:
        _fail(f"{location}.defined_syntax_registry_id", "does not match live registry")
    if (
        type(baseline["defined_syntax_registry_version"]) is not int
        or baseline["defined_syntax_registry_version"]
        != defined_syntax.DEFINED_SYNTAX_VERSION
    ):
        _fail(f"{location}.defined_syntax_registry_version", "does not match live registry")
    registry_hash = _sha256(
        baseline["defined_syntax_registry_sha256"],
        f"{location}.defined_syntax_registry_sha256",
    )
    if registry_hash != defined_syntax.DEFINED_SYNTAX_REGISTRY_SHA256:
        _fail(f"{location}.defined_syntax_registry_sha256", "does not match live registry")

    source = root / "peano-lab" / "py" / "peano_lab" / "library" / "defined_syntax.py"
    _verify_file_hash(
        source,
        baseline["defined_syntax_source_sha256"],
        f"{location}.defined_syntax_source_sha256",
    )
    inventory = _repository_file(
        root,
        baseline["definition_inventory_path"],
        f"{location}.definition_inventory_path",
    )
    _verify_file_hash(
        inventory,
        baseline["definition_inventory_sha256"],
        f"{location}.definition_inventory_sha256",
    )


def _validate_kernel(root: Path, raw: object, location: str) -> None:
    kernel = _fields(
        raw,
        {
            "classification",
            "object_theory",
            "sorts",
            "term_constructors",
            "formula_constructors",
            "variable_representation",
            "campaign_checker_entrypoint",
            "campaign_checker_dne_policy",
            "separate_classical_entrypoint",
            "classical_only_certificate_node",
            "intuitionistic_certificate_nodes",
            "arithmetic_axioms",
            "induction",
            "cut",
            "definition_nodes_in_kernel",
            "sources",
        },
        set(),
        location,
    )
    expected_scalars = {
        "classification": "frozen-compatible",
        "object_theory": "first-order intuitionistic arithmetic",
        "variable_representation": "de_bruijn_indices",
        "campaign_checker_entrypoint": "peano_lab.kernel.checker.check",
        "campaign_checker_dne_policy": "reject",
        "separate_classical_entrypoint": "peano_lab.kernel.checker.check_classical",
        "classical_only_certificate_node": "DNE",
    }
    for field, expected in expected_scalars.items():
        if kernel[field] != expected:
            _fail(f"{location}.{field}", f"must equal {expected!r}")
    if kernel["definition_nodes_in_kernel"] is not False:
        _fail(f"{location}.definition_nodes_in_kernel", "must be false")
    if _string_list(kernel["sorts"], f"{location}.sorts", nonempty=True) != [
        "natural_number"
    ]:
        _fail(f"{location}.sorts", "must contain only natural_number")
    if _string_list(
        kernel["term_constructors"], f"{location}.term_constructors", nonempty=True
    ) != ["Var", "Zero", "Succ", "Add", "Mul"]:
        _fail(f"{location}.term_constructors", "does not match the kernel term grammar")
    if _string_list(
        kernel["formula_constructors"],
        f"{location}.formula_constructors",
        nonempty=True,
    ) != ["Eq", "Bot", "Imp", "And", "Or", "Forall", "Exists"]:
        _fail(
            f"{location}.formula_constructors",
            "does not match the kernel formula grammar",
        )
    nodes = _string_list(
        kernel["intuitionistic_certificate_nodes"],
        f"{location}.intuitionistic_certificate_nodes",
        nonempty=True,
    )
    if set(nodes) != EXPECTED_INTUITIONISTIC_NODES:
        _fail(
            f"{location}.intuitionistic_certificate_nodes",
            "does not match the constructive proof-node set",
        )
    if kernel["arithmetic_axioms"] != EXPECTED_AXIOMS:
        _fail(f"{location}.arithmetic_axioms", "must list PA1-PA6 exactly")
    _text(kernel["induction"], f"{location}.induction")
    _text(kernel["cut"], f"{location}.cut")

    sources = kernel["sources"]
    if type(sources) is not list or not sources:
        _fail(f"{location}.sources", "must be a non-empty list")
    seen_paths: set[str] = set()
    for index, raw_source in enumerate(sources):
        item_location = f"{location}.sources[{index}]"
        source = _fields(raw_source, {"path"}, {"sha256"}, item_location)
        path_text = _text(source["path"], f"{item_location}.path")
        if path_text in seen_paths:
            _fail(f"{item_location}.path", "duplicates an earlier kernel source")
        seen_paths.add(path_text)
        path = _repository_file(root, path_text, f"{item_location}.path")
        if "sha256" in source:
            _verify_file_hash(path, source["sha256"], f"{item_location}.sha256")


def _validate_definition_boundary(root: Path, raw: object, location: str) -> None:
    boundary = _fields(
        raw,
        {
            "surface_parser",
            "expansion_contract",
            "ordinary_parser_accepts_definition_calls",
            "kernel_accepts_definition_calls",
            "macro_receipt_implies_api_theorem",
            "api_authority",
            "sources",
        },
        set(),
        location,
    )
    if boundary["surface_parser"] != "peano_lab.library.defined_syntax":
        _fail(f"{location}.surface_parser", "does not name defined_syntax")
    for field in ("expansion_contract", "api_authority"):
        _text(boundary[field], f"{location}.{field}")
    for field in (
        "ordinary_parser_accepts_definition_calls",
        "kernel_accepts_definition_calls",
        "macro_receipt_implies_api_theorem",
    ):
        if boundary[field] is not False:
            _fail(f"{location}.{field}", "must be false")
    for index, raw_path in enumerate(
        _string_list(boundary["sources"], f"{location}.sources", nonempty=True)
    ):
        _repository_file(root, raw_path, f"{location}.sources[{index}]")


def _validate_bridge(
    raw: object,
    location: str,
    public_names: set[str],
) -> str:
    bridge = _fields(
        raw,
        {"proposed_name", "status", "statement_shape"},
        {"available_components"},
        location,
    )
    name = _text(bridge["proposed_name"], f"{location}.proposed_name")
    if SNAKE_IDENTIFIER.fullmatch(name) is None:
        _fail(f"{location}.proposed_name", "must be a lowercase snake-case theorem name")
    status = _text(bridge["status"], f"{location}.status")
    if status not in BRIDGE_STATUSES:
        _fail(f"{location}.status", f"unknown bridge status {status!r}")
    _text(bridge["statement_shape"], f"{location}.statement_shape")
    if "available_components" in bridge:
        components = _string_list(
            bridge["available_components"],
            f"{location}.available_components",
            nonempty=True,
        )
        for component in components:
            if component not in public_names:
                _fail(
                    f"{location}.available_components",
                    f"{component!r} is absent from the public theorem registry",
                )
    return status


def _validate_definitions(
    raw: object,
    location: str,
    defined_syntax: Any,
    public_names: set[str],
) -> tuple[set[str], set[str], int]:
    if type(raw) is not list or not raw:
        _fail(location, "must be a non-empty list")
    primary = {definition.name: definition for definition in defined_syntax.DEFINITIONS}
    adjacent = {
        definition.name: definition for definition in defined_syntax.ADJACENT_DEFINITIONS
    }
    manifest_names: set[str] = set()
    stable_ids: set[str] = set()
    cited_api: set[str] = set()
    api_rows = 0

    for index, raw_definition in enumerate(raw):
        item_location = f"{location}[{index}]"
        definition = _fields(
            raw_definition,
            {
                "stable_id",
                "name",
                "parameters",
                "registry_class",
                "campaign_classification",
                "exact_expanded_template",
                "template_source_sha256",
                "conceptual_dependencies",
                "reason",
                "sources",
                "proved_api",
                "required_bridge_theorems",
            },
            set(),
            item_location,
        )
        name = _text(definition["name"], f"{item_location}.name")
        if IDENTIFIER.fullmatch(name) is None:
            _fail(f"{item_location}.name", "must be a Peano definition identifier")
        if name in manifest_names:
            _fail(f"{item_location}.name", f"duplicate definition {name!r}")
        manifest_names.add(name)

        registry_class = _text(
            definition["registry_class"], f"{item_location}.registry_class"
        )
        if registry_class == "primary":
            registry = primary
        elif registry_class == "adjacent":
            registry = adjacent
        else:
            _fail(f"{item_location}.registry_class", "must be primary or adjacent")
        if name not in registry:
            other = "adjacent" if registry_class == "primary" else "primary"
            _fail(
                f"{item_location}.registry_class",
                f"{name!r} is not in the live {registry_class} registry (check {other})",
            )
        runtime = registry[name]

        stable_id = _text(definition["stable_id"], f"{item_location}.stable_id")
        if stable_id in stable_ids:
            _fail(f"{item_location}.stable_id", f"duplicate stable id {stable_id!r}")
        stable_ids.add(stable_id)
        if stable_id != runtime.stable_id:
            _fail(f"{item_location}.stable_id", "does not match the live registry")

        parameters = _string_list(
            definition["parameters"], f"{item_location}.parameters", nonempty=True
        )
        if tuple(parameters) != runtime.parameters:
            _fail(
                f"{item_location}.parameters",
                f"does not match live parameter order {runtime.parameters!r}",
            )
        template = _text(
            definition["exact_expanded_template"],
            f"{item_location}.exact_expanded_template",
        )
        if template != runtime.template_source:
            _fail(
                f"{item_location}.exact_expanded_template",
                "does not exactly match the live registry template",
            )
        template_hash = _sha256(
            definition["template_source_sha256"],
            f"{item_location}.template_source_sha256",
        )
        expected_template_hash = _sha256_text(runtime.template_source)
        if template_hash != expected_template_hash:
            _fail(
                f"{item_location}.template_source_sha256",
                f"does not match exact template bytes: expected {expected_template_hash}",
            )
        dependencies = _string_list(
            definition["conceptual_dependencies"],
            f"{item_location}.conceptual_dependencies",
            nonempty=False,
        )
        if tuple(dependencies) != runtime.conceptual_dependencies:
            _fail(
                f"{item_location}.conceptual_dependencies",
                f"does not match live dependency order {runtime.conceptual_dependencies!r}",
            )

        classification = _text(
            definition["campaign_classification"],
            f"{item_location}.campaign_classification",
        )
        expected_classification = EXPECTED_CLASSIFICATIONS.get(name)
        if expected_classification is None:
            _fail(f"{item_location}.name", "is not selected by freeze v1")
        if classification != expected_classification:
            _fail(
                f"{item_location}.campaign_classification",
                f"must remain {expected_classification!r} in freeze v1",
            )
        _text(definition["reason"], f"{item_location}.reason")
        _string_list(definition["sources"], f"{item_location}.sources", nonempty=True)

        api = definition["proved_api"]
        if type(api) is not list or not api:
            _fail(f"{item_location}.proved_api", "must be a non-empty list")
        local_api: set[str] = set()
        for api_index, raw_api in enumerate(api):
            api_location = f"{item_location}.proved_api[{api_index}]"
            api_item = _fields(raw_api, {"name", "status"}, set(), api_location)
            theorem_name = _text(api_item["name"], f"{api_location}.name")
            if theorem_name in local_api:
                _fail(f"{api_location}.name", "duplicates an API citation for this definition")
            local_api.add(theorem_name)
            if api_item["status"] != "public_checked":
                _fail(f"{api_location}.status", "must equal 'public_checked'")
            if theorem_name not in public_names:
                _fail(
                    f"{api_location}.name",
                    f"{theorem_name!r} is absent from the public theorem registry",
                )
            cited_api.add(theorem_name)
            api_rows += 1

        bridges = definition["required_bridge_theorems"]
        if type(bridges) is not list:
            _fail(f"{item_location}.required_bridge_theorems", "must be a list")
        bridge_names: set[str] = set()
        bridge_statuses: list[str] = []
        for bridge_index, raw_bridge in enumerate(bridges):
            bridge_location = f"{item_location}.required_bridge_theorems[{bridge_index}]"
            status = _validate_bridge(raw_bridge, bridge_location, public_names)
            bridge_name = raw_bridge["proposed_name"]
            if bridge_name in bridge_names:
                _fail(f"{bridge_location}.proposed_name", "duplicates an earlier bridge")
            bridge_names.add(bridge_name)
            bridge_statuses.append(status)
        if classification == "frozen-compatible" and bridges:
            _fail(
                f"{item_location}.required_bridge_theorems",
                "frozen-compatible definitions may not claim an outstanding bridge",
            )
        if classification in {"bridge-required", "legacy-late"} and not bridges:
            _fail(
                f"{item_location}.required_bridge_theorems",
                f"{classification} requires at least one explicit bridge obligation",
            )
        if classification == "legacy-late" and any(
            not status.startswith("late_after_") for status in bridge_statuses
        ):
            _fail(
                f"{item_location}.required_bridge_theorems",
                "legacy-late bridges must remain explicitly late",
            )

    expected_names = set(EXPECTED_CLASSIFICATIONS)
    if manifest_names != expected_names:
        missing = sorted(expected_names - manifest_names)
        extra = sorted(manifest_names - expected_names)
        _fail(location, f"freeze-v1 selection mismatch; missing={missing}, extra={extra}")
    return cited_api, manifest_names, api_rows


def _validate_k3_quarantine(raw: object, location: str) -> None:
    quarantine = _fields(
        raw,
        {
            "policy",
            "forbidden_foundational_relations",
            "forbidden_foundational_theorem_families",
            "allowed_uses_before_k3_release",
            "required_foundational_order",
        },
        set(),
        location,
    )
    policy = _text(quarantine["policy"], f"{location}.policy").casefold()
    if "independent of crt" not in policy:
        _fail(f"{location}.policy", "must make K3 independence from CRT explicit")
    forbidden = _string_list(
        quarantine["forbidden_foundational_relations"],
        f"{location}.forbidden_foundational_relations",
        nonempty=True,
    )
    if set(forbidden) != {"BetaAt", "Product"}:
        _fail(
            f"{location}.forbidden_foundational_relations",
            "must quarantine exactly BetaAt and Product",
        )
    forbidden_families = _string_list(
        quarantine["forbidden_foundational_theorem_families"],
        f"{location}.forbidden_foundational_theorem_families",
        nonempty=True,
    )
    folded_families = " ".join(forbidden_families).casefold()
    if "beta" not in folded_families or "crt" not in folded_families:
        _fail(
            f"{location}.forbidden_foundational_theorem_families",
            "must explicitly quarantine beta and CRT theorem families",
        )
    _string_list(
        quarantine["allowed_uses_before_k3_release"],
        f"{location}.allowed_uses_before_k3_release",
        nonempty=True,
    )
    order = tuple(
        _string_list(
            quarantine["required_foundational_order"],
            f"{location}.required_foundational_order",
            nonempty=True,
        )
    )
    if order != EXPECTED_FOUNDATIONAL_ORDER:
        _fail(
            f"{location}.required_foundational_order",
            "must put non-CRT pair/list/folds before CRT and beta interoperability",
        )


def _validate_obligations(raw: object, location: str) -> int:
    if type(raw) is not list or not raw:
        _fail(location, "must be a non-empty list")
    identifiers: set[str] = set()
    for index, raw_obligation in enumerate(raw):
        item_location = f"{location}[{index}]"
        obligation = _fields(
            raw_obligation, {"id", "status", "requirement"}, set(), item_location
        )
        identifier = _text(obligation["id"], f"{item_location}.id")
        if identifier in identifiers:
            _fail(f"{item_location}.id", f"duplicate obligation {identifier!r}")
        identifiers.add(identifier)
        _text(obligation["status"], f"{item_location}.status")
        requirement = _text(obligation["requirement"], f"{item_location}.requirement")
        if identifier.startswith("K3.") and "beta prefix" in requirement.casefold():
            _fail(
                f"{item_location}.requirement",
                "K3 may not make beta coding foundational",
            )
    if identifiers != EXPECTED_OBLIGATION_IDS:
        _fail(location, "must contain the four freeze-v1 representation obligations")
    return len(identifiers)


def _validate_validation_receipt(
    raw: object,
    location: str,
    *,
    distinct_api_count: int,
    api_rows: int,
) -> None:
    validation = _fields(
        raw,
        {
            "json_parse_command",
            "runtime_comparison",
            "theorem_name_comparison",
            "selected_api_replay",
            "full_library_replay_not_performed_in_this_freeze_audit",
        },
        set(),
        location,
    )
    for field in ("json_parse_command", "runtime_comparison", "theorem_name_comparison"):
        _text(validation[field], f"{location}.{field}")
    replay = _fields(
        validation["selected_api_replay"],
        {"date", "checker", "scope", "result"},
        set(),
        f"{location}.selected_api_replay",
    )
    _text(replay["date"], f"{location}.selected_api_replay.date")
    if replay["checker"] != "peano_lab.kernel.checker.check":
        _fail(
            f"{location}.selected_api_replay.checker",
            "must name the default intuitionistic checker",
        )
    expected_scope = (
        f"{distinct_api_count} distinct theorem names referenced by the "
        f"{api_rows} proved_api rows"
    )
    if replay["scope"] != expected_scope:
        _fail(
            f"{location}.selected_api_replay.scope",
            f"must equal {expected_scope!r}",
        )
    if replay["result"] != "pass":
        _fail(f"{location}.selected_api_replay.result", "must equal 'pass'")
    if validation["full_library_replay_not_performed_in_this_freeze_audit"] is not True:
        _fail(
            f"{location}.full_library_replay_not_performed_in_this_freeze_audit",
            "must remain true unless the freeze and validator are versioned together",
        )


def _replay_api(theorems: Any, names: set[str]) -> None:
    from peano_lab.kernel.checker import check

    for name in sorted(names):
        try:
            checked = theorems.replay(name)
        except Exception as exc:
            raise FreezeError(f"proved_api.{name}: public replay failed: {exc}") from exc
        if not check((), checked.certificate, checked.formula):
            _fail(
                f"proved_api.{name}",
                "default intuitionistic checker rejected the replayed certificate",
            )


def validate_freeze(
    repository_root: Path,
    freeze_path: Path,
    *,
    replay_proved_api: bool = False,
) -> dict[str, int]:
    """Validate ``freeze_path`` and return a non-authoritative summary."""

    repository_root = repository_root.resolve()
    freeze = _load_json(freeze_path)
    location = str(freeze_path)
    record = _fields(
        freeze,
        {
            "schema",
            "version",
            "freeze_date",
            "title",
            "authority",
            "baseline",
            "classification_vocabulary",
            "kernel",
            "definition_boundary",
            "definitions",
            "k3_quarantine",
            "next_representation_obligations",
            "validation",
        },
        set(),
        location,
    )
    if record["schema"] != FREEZE_SCHEMA or record["version"] != FREEZE_VERSION:
        _fail(location, f"expected {FREEZE_SCHEMA!r} version {FREEZE_VERSION}")
    _text(record["freeze_date"], f"{location}.freeze_date")
    _text(record["title"], f"{location}.title")
    authority = _text(record["authority"], f"{location}.authority").casefold()
    if "grants no" not in authority or "theorem authority" not in authority:
        _fail(f"{location}.authority", "must disclaim theorem authority explicitly")

    vocabulary = record["classification_vocabulary"]
    if type(vocabulary) is not dict or set(vocabulary) != EXPECTED_CLASSIFICATION_VOCABULARY:
        _fail(
            f"{location}.classification_vocabulary",
            "must define exactly frozen-compatible, bridge-required, and legacy-late",
        )
    for name, description in vocabulary.items():
        _text(description, f"{location}.classification_vocabulary.{name}")

    defined_syntax, theorems, public_names = _load_authorities(repository_root)
    _validate_baseline(
        repository_root, record["baseline"], f"{location}.baseline", defined_syntax
    )
    _validate_kernel(repository_root, record["kernel"], f"{location}.kernel")
    _validate_definition_boundary(
        repository_root,
        record["definition_boundary"],
        f"{location}.definition_boundary",
    )
    cited_api, definition_names, api_rows = _validate_definitions(
        record["definitions"],
        f"{location}.definitions",
        defined_syntax,
        public_names,
    )

    # The central anti-circularity invariant is checked redundantly: both the
    # per-definition classification and the explicit K3 quarantine must agree.
    if not {"BetaAt", "Product"}.issubset(definition_names):
        _fail(f"{location}.definitions", "must include both legacy-late relations")
    _validate_k3_quarantine(
        record["k3_quarantine"], f"{location}.k3_quarantine"
    )
    obligation_count = _validate_obligations(
        record["next_representation_obligations"],
        f"{location}.next_representation_obligations",
    )
    _validate_validation_receipt(
        record["validation"],
        f"{location}.validation",
        distinct_api_count=len(cited_api),
        api_rows=api_rows,
    )
    if replay_proved_api:
        _replay_api(theorems, cited_api)

    return {
        "definitions": len(definition_names),
        "proved_api_rows": api_rows,
        "distinct_public_theorems": len(cited_api),
        "representation_obligations": obligation_count,
        "replayed_public_theorems": len(cited_api) if replay_proved_api else 0,
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
        "--freeze",
        type=Path,
        default=default_root
        / "research"
        / "arithmetic-library"
        / "ha-definition-representation-freeze-v1.json",
        help="definition-freeze JSON path",
    )
    parser.add_argument(
        "--replay-proved-api",
        action="store_true",
        help="also replay every distinct proved_api theorem through checker.check",
    )
    args = parser.parse_args(argv)
    try:
        summary = validate_freeze(
            args.repository_root,
            args.freeze,
            replay_proved_api=args.replay_proved_api,
        )
    except FreezeError as exc:
        print(f"HA definition freeze validation failed: {exc}", file=sys.stderr)
        return 1
    replay_note = (
        f", {summary['replayed_public_theorems']} replayed"
        if args.replay_proved_api
        else ""
    )
    print(
        "HA definition freeze validation passed: "
        f"{summary['definitions']} definitions, "
        f"{summary['proved_api_rows']} API rows, "
        f"{summary['distinct_public_theorems']} public theorems, "
        f"{summary['representation_obligations']} representation obligations"
        f"{replay_note}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
