#!/usr/bin/env python3
"""Validate the foundational-arithmetic knowledge catalog.

The catalog is planning and provenance data, not theorem authority.  This
gate nevertheless keeps it honest: expressible statements must parse as
closed formulas in the production Peano language, and ``checked_existing``
records must agree with the actual replay library by formula and dependency.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
from typing import Any, NoReturn
from urllib.parse import urlparse


CATALOG_FORMAT = "peano-arithmetic-knowledge-catalog"
SOURCE_FORMAT = "peano-arithmetic-source-register"
FORMAT_VERSION = 1
STATUSES = {
    "checked_existing",
    "checked_m20",
    "planned_expressible",
    "blocked_by_language",
}
BASELINE_EXISTING = {
    "zero_add",
    "add_succ_left",
    "add_comm",
    "add_assoc",
    "mul_zero_left",
    "mul_succ_left",
    "mul_comm",
    "mul_add",
    "mul_assoc",
    "one_mul",
    "mul_one",
    "add_mul",
    "succ_ne_zero",
    "succ_injective",
    "le_refl",
    "le_trans",
    "no_succ_add_fixed",
    "drop_add_prefix_from_fixed",
    "antisymm_from_witnesses",
    "le_antisymm",
    "le_total",
    "add_eq_zero_right",
    "mul_eq_zero",
}
IDENTIFIER = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*\Z")
BLOCKER_CODE = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*\Z")


class KnowledgeBaseError(ValueError):
    """The arithmetic catalog violates its checked data contract."""


def _fail(location: str, message: str) -> NoReturn:
    raise KnowledgeBaseError(f"{location}: {message}")


def _object_from_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise KnowledgeBaseError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream, object_pairs_hook=_object_from_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise KnowledgeBaseError(f"{path}: cannot read strict UTF-8 JSON: {exc}") from exc
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
    if any(ord(char) < 32 for char in value):
        _fail(location, "must not contain control characters")
    return value


def _identifier(value: object, location: str) -> str:
    text = _text(value, location)
    if IDENTIFIER.fullmatch(text) is None:
        _fail(location, "must be an ASCII lowercase snake-case identifier")
    return text


def _url(value: object, location: str) -> str:
    text = _text(value, location)
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        _fail(location, "must be an absolute HTTP(S) URL")
    return text


def _string_list(value: object, location: str, *, nonempty: bool) -> list[str]:
    if type(value) is not list or not all(type(item) is str for item in value):
        _fail(location, "must be a list of strings")
    result: list[str] = value
    if nonempty and not result:
        _fail(location, "must not be empty")
    if len(result) != len(set(result)):
        _fail(location, "must not contain duplicates")
    return result


def _validate_sources(register: dict[str, Any], path: Path) -> set[str]:
    location = str(path)
    record = _fields(
        register,
        {"format", "version", "retrieved_at", "reuse_modes", "sources"},
        set(),
        location,
    )
    if record["format"] != SOURCE_FORMAT or record["version"] != FORMAT_VERSION:
        _fail(location, f"expected {SOURCE_FORMAT!r} version {FORMAT_VERSION}")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", _text(record["retrieved_at"], f"{location}.retrieved_at")) is None:
        _fail(f"{location}.retrieved_at", "must use YYYY-MM-DD")

    modes = record["reuse_modes"]
    if type(modes) is not dict or not modes:
        _fail(f"{location}.reuse_modes", "must be a non-empty object")
    for mode, description in modes.items():
        _identifier(mode, f"{location}.reuse_modes key")
        _text(description, f"{location}.reuse_modes.{mode}")

    sources = record["sources"]
    if type(sources) is not list or not sources:
        _fail(f"{location}.sources", "must be a non-empty list")
    seen: set[str] = set()
    folded: set[str] = set()
    for index, raw in enumerate(sources):
        item_location = f"{location}.sources[{index}]"
        source = _fields(
            raw,
            {"id", "title", "kind", "url", "license", "reuse_mode", "notes"},
            {"revision", "license_url", "resources"},
            item_location,
        )
        source_id = _identifier(source["id"], f"{item_location}.id")
        if source_id in seen or source_id.casefold() in folded:
            _fail(f"{item_location}.id", f"duplicate source id {source_id!r}")
        seen.add(source_id)
        folded.add(source_id.casefold())
        for field in ("title", "kind", "license", "notes"):
            _text(source[field], f"{item_location}.{field}")
        _url(source["url"], f"{item_location}.url")
        if "revision" in source:
            _text(source["revision"], f"{item_location}.revision")
        if "license_url" in source:
            _url(source["license_url"], f"{item_location}.license_url")
        mode = _identifier(source["reuse_mode"], f"{item_location}.reuse_mode")
        if mode not in modes:
            _fail(f"{item_location}.reuse_mode", f"unknown reuse mode {mode!r}")
        resources = source.get("resources", [])
        if type(resources) is not list:
            _fail(f"{item_location}.resources", "must be a list")
        labels: set[str] = set()
        for resource_index, raw_resource in enumerate(resources):
            resource_location = f"{item_location}.resources[{resource_index}]"
            resource = _fields(raw_resource, {"label", "url"}, set(), resource_location)
            label = _text(resource["label"], f"{resource_location}.label")
            if label in labels:
                _fail(f"{resource_location}.label", f"duplicate resource label {label!r}")
            labels.add(label)
            _url(resource["url"], f"{resource_location}.url")
    return seen


def _peano_bindings(repository_root: Path):
    python_root = repository_root / "peano-lab" / "py"
    if not python_root.is_dir():
        _fail(str(repository_root), "does not contain peano-lab/py")
    inserted = str(python_root)
    sys.path.insert(0, inserted)
    try:
        from peano_lab.kernel.formulas import parse_formula_with_names
        from peano_lab.library.theorems import get as get_theorem
        from peano_lab.library.theorems import names as theorem_names
    except ImportError as exc:
        raise KnowledgeBaseError(f"cannot import production Peano parser/library: {exc}") from exc
    finally:
        try:
            sys.path.remove(inserted)
        except ValueError:
            pass
    return parse_formula_with_names, get_theorem, theorem_names


def _closed_formula(source: str, location: str, parser):
    try:
        formula, free_names = parser(source)
    except (ValueError, TypeError) as exc:
        raise KnowledgeBaseError(f"{location}: invalid Peano formula: {exc}") from exc
    if free_names:
        _fail(location, "formula is open; free variable(s): " + ", ".join(free_names))
    return formula


def _validate_companion_artifacts(
    value: object,
    location: str,
    source_ids: set[str],
    repository_root: Path,
) -> int:
    if type(value) is not list or not value:
        _fail(location, "must be a non-empty list")
    seen: set[str] = set()
    for index, raw in enumerate(value):
        item_location = f"{location}[{index}]"
        companion = _fields(
            raw,
            {
                "id",
                "title",
                "prover",
                "artifact_path",
                "source",
                "dependency_revision",
                "declarations",
                "allowed_axioms",
                "scope",
            },
            set(),
            item_location,
        )
        companion_id = _identifier(companion["id"], f"{item_location}.id")
        if companion_id in seen:
            _fail(f"{item_location}.id", f"duplicate companion id {companion_id!r}")
        seen.add(companion_id)
        for field in ("title", "prover", "scope"):
            _text(companion[field], f"{item_location}.{field}")

        source_id = _identifier(companion["source"], f"{item_location}.source")
        if source_id not in source_ids:
            _fail(f"{item_location}.source", f"unknown source id {source_id!r}")
        revision = _text(
            companion["dependency_revision"],
            f"{item_location}.dependency_revision",
        )
        if re.fullmatch(r"[0-9a-f]{40}", revision) is None:
            _fail(
                f"{item_location}.dependency_revision",
                "must be a full lowercase Git commit",
            )

        relative_text = _text(
            companion["artifact_path"], f"{item_location}.artifact_path"
        )
        relative = Path(relative_text)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or relative.as_posix() != relative_text
        ):
            _fail(
                f"{item_location}.artifact_path",
                "must be a normalized repository-relative path",
            )
        artifact = repository_root / relative
        if not artifact.is_file():
            _fail(
                f"{item_location}.artifact_path",
                f"missing artifact {relative_text!r}",
            )
        artifact_source = artifact.read_text(encoding="utf-8")

        declarations = _string_list(
            companion["declarations"],
            f"{item_location}.declarations",
            nonempty=True,
        )
        for declaration_index, declaration in enumerate(declarations):
            declaration_location = (
                f"{item_location}.declarations[{declaration_index}]"
            )
            _text(declaration, declaration_location)
            short_name = declaration.rsplit(".", 1)[-1]
            _identifier(short_name, declaration_location)
            if re.search(rf"\btheorem\s+{re.escape(short_name)}\b", artifact_source) is None:
                _fail(
                    declaration_location,
                    f"declaration {declaration!r} is absent from {relative_text}",
                )

        axioms = _string_list(
            companion["allowed_axioms"],
            f"{item_location}.allowed_axioms",
            nonempty=True,
        )
        for axiom_index, axiom in enumerate(axioms):
            _text(axiom, f"{item_location}.allowed_axioms[{axiom_index}]")
    return len(value)


def _validate_catalog(
    catalog: dict[str, Any],
    path: Path,
    source_ids: set[str],
    repository_root: Path,
) -> dict[str, int]:
    location = str(path)
    record = _fields(
        catalog,
        {
            "format",
            "version",
            "title",
            "scope",
            "object_language",
            "expanded_predicate_conventions",
            "statuses",
            "companion_artifacts",
            "domain_order",
            "lemmas",
        },
        set(),
        location,
    )
    if record["format"] != CATALOG_FORMAT or record["version"] != FORMAT_VERSION:
        _fail(location, f"expected {CATALOG_FORMAT!r} version {FORMAT_VERSION}")
    _text(record["title"], f"{location}.title")
    _text(record["scope"], f"{location}.scope")
    if type(record["object_language"]) is not dict:
        _fail(f"{location}.object_language", "must be an object")
    conventions = record["expanded_predicate_conventions"]
    if type(conventions) is not dict or not conventions:
        _fail(f"{location}.expanded_predicate_conventions", "must be a non-empty object")
    for name, expansion in conventions.items():
        _text(name, f"{location}.expanded_predicate_conventions key")
        _text(expansion, f"{location}.expanded_predicate_conventions.{name}")

    statuses = record["statuses"]
    if type(statuses) is not dict or set(statuses) != STATUSES:
        _fail(f"{location}.statuses", "must define exactly " + ", ".join(sorted(STATUSES)))
    for status, description in statuses.items():
        _text(description, f"{location}.statuses.{status}")

    companion_count = _validate_companion_artifacts(
        record["companion_artifacts"],
        f"{location}.companion_artifacts",
        source_ids,
        repository_root,
    )

    domains = _string_list(record["domain_order"], f"{location}.domain_order", nonempty=True)
    for index, domain in enumerate(domains):
        _identifier(domain, f"{location}.domain_order[{index}]")
    domain_set = set(domains)

    lemmas = record["lemmas"]
    if type(lemmas) is not list or not lemmas:
        _fail(f"{location}.lemmas", "must be a non-empty list")
    parser, get_theorem, theorem_names = _peano_bindings(repository_root)
    seen: dict[str, dict[str, Any]] = {}
    folded: set[str] = set()
    checked_claims: set[str] = set()
    status_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    for index, raw in enumerate(lemmas):
        item_location = f"{location}.lemmas[{index}]"
        lemma = _fields(
            raw,
            {
                "id",
                "title",
                "domain",
                "status",
                "dependencies",
                "sources",
                "summary",
                "peano",
                "blocker",
            },
            set(),
            item_location,
        )
        lemma_id = _identifier(lemma["id"], f"{item_location}.id")
        if lemma_id in seen or lemma_id.casefold() in folded:
            _fail(f"{item_location}.id", f"duplicate lemma id {lemma_id!r}")
        _text(lemma["title"], f"{item_location}.title")
        _text(lemma["summary"], f"{item_location}.summary")
        domain = _identifier(lemma["domain"], f"{item_location}.domain")
        if domain not in domain_set:
            _fail(f"{item_location}.domain", f"unknown domain {domain!r}")
        status = _identifier(lemma["status"], f"{item_location}.status")
        if status not in STATUSES:
            _fail(f"{item_location}.status", f"unknown status {status!r}")

        dependencies = _string_list(
            lemma["dependencies"], f"{item_location}.dependencies", nonempty=False
        )
        for dependency_index, dependency in enumerate(dependencies):
            _identifier(dependency, f"{item_location}.dependencies[{dependency_index}]")
            if dependency not in seen:
                _fail(
                    f"{item_location}.dependencies[{dependency_index}]",
                    f"dependency {dependency!r} must name an earlier catalog entry",
                )

        sources = _string_list(lemma["sources"], f"{item_location}.sources", nonempty=True)
        for source_index, source_id in enumerate(sources):
            _identifier(source_id, f"{item_location}.sources[{source_index}]")
            if source_id not in source_ids:
                _fail(
                    f"{item_location}.sources[{source_index}]",
                    f"unknown source id {source_id!r}",
                )

        if status == "blocked_by_language":
            if lemma["peano"] is not None:
                _fail(f"{item_location}.peano", "blocked entries must not claim a Peano statement")
            blocker = _fields(
                lemma["blocker"],
                {"code", "detail", "unblocks_with"},
                set(),
                f"{item_location}.blocker",
            )
            code = _text(blocker["code"], f"{item_location}.blocker.code")
            if BLOCKER_CODE.fullmatch(code) is None:
                _fail(f"{item_location}.blocker.code", "must be an ASCII snake-case code")
            _text(blocker["detail"], f"{item_location}.blocker.detail")
            remedies = _string_list(
                blocker["unblocks_with"],
                f"{item_location}.blocker.unblocks_with",
                nonempty=True,
            )
            for remedy_index, remedy in enumerate(remedies):
                _text(remedy, f"{item_location}.blocker.unblocks_with[{remedy_index}]")
        else:
            if lemma["blocker"] is not None:
                _fail(f"{item_location}.blocker", "expressible entries must have a null blocker")
            peano = _fields(
                lemma["peano"],
                {"statement", "existing_name"},
                set(),
                f"{item_location}.peano",
            )
            statement = _text(peano["statement"], f"{item_location}.peano.statement")
            formula = _closed_formula(statement, f"{item_location}.peano.statement", parser)
            if status == "planned_expressible":
                if peano["existing_name"] is not None:
                    _fail(
                        f"{item_location}.peano.existing_name",
                        "planned entries must not claim an existing runtime theorem",
                    )
            else:
                existing_name = _identifier(
                    peano["existing_name"], f"{item_location}.peano.existing_name"
                )
                if existing_name != lemma_id:
                    _fail(
                        f"{item_location}.peano.existing_name",
                        "checked entry id and runtime name must agree",
                    )
                spec = get_theorem(existing_name)
                if spec is None:
                    _fail(
                        f"{item_location}.peano.existing_name",
                        f"no runtime theorem {existing_name!r}",
                    )
                expected_status = (
                    "checked_existing"
                    if existing_name in BASELINE_EXISTING
                    else "checked_m20"
                )
                if status != expected_status:
                    _fail(
                        f"{item_location}.status",
                        f"runtime theorem {existing_name!r} must be labeled {expected_status!r}",
                    )
                if "peano_lab_library" not in sources:
                    _fail(
                        f"{item_location}.sources",
                        "checked entries must cite peano_lab_library",
                    )
                runtime_formula = _closed_formula(
                    spec.statement,
                    f"runtime theorem {existing_name!r}",
                    parser,
                )
                if formula != runtime_formula:
                    _fail(
                        f"{item_location}.peano.statement",
                        f"does not match runtime theorem {existing_name!r}",
                    )
                if tuple(dependencies) != spec.dependencies:
                    _fail(
                        f"{item_location}.dependencies",
                        f"does not match runtime dependencies {spec.dependencies!r}",
                    )
                checked_claims.add(existing_name)

        seen[lemma_id] = lemma
        folded.add(lemma_id.casefold())
        status_counts[status] += 1
        domain_counts[domain] += 1

    missing_domains = domain_set - set(domain_counts)
    if missing_domains:
        _fail(f"{location}.lemmas", "domains without entries: " + ", ".join(sorted(missing_domains)))
    runtime_names = set(theorem_names())
    if checked_claims != runtime_names:
        missing = runtime_names - checked_claims
        extra = checked_claims - runtime_names
        details: list[str] = []
        if missing:
            details.append("missing runtime theorem(s): " + ", ".join(sorted(missing)))
        if extra:
            details.append("non-runtime checked claim(s): " + ", ".join(sorted(extra)))
        _fail(f"{location}.lemmas", "; ".join(details))
    return {
        "lemmas": len(lemmas),
        "domains": len(domain_counts),
        "companion_artifacts": companion_count,
        **{status: status_counts[status] for status in sorted(STATUSES)},
    }


def validate_files(
    catalog_path: Path,
    source_path: Path,
    *,
    repository_root: Path,
) -> dict[str, int]:
    """Validate both files against the production Peano parser and library."""

    source_ids = _validate_sources(_load_json(source_path), source_path)
    return _validate_catalog(
        _load_json(catalog_path), catalog_path, source_ids, repository_root
    )


def _parser() -> argparse.ArgumentParser:
    repository_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Validate the Peano foundational-arithmetic knowledge catalog."
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=repository_root / "research" / "arithmetic-library" / "catalog.json",
    )
    parser.add_argument(
        "--sources",
        type=Path,
        default=repository_root / "research" / "arithmetic-library" / "source-register.json",
    )
    parser.add_argument("--repository-root", type=Path, default=repository_root)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        counts = validate_files(
            args.catalog,
            args.sources,
            repository_root=args.repository_root.resolve(),
        )
    except KnowledgeBaseError as exc:
        print(f"arithmetic knowledge-base validation failed: {exc}", file=sys.stderr)
        return 1
    print(
        "validated arithmetic knowledge base: "
        f"{counts['lemmas']} lemmas across {counts['domains']} domains "
        f"({counts['checked_existing']} baseline checked, "
        f"{counts['checked_m20']} post-baseline checked, "
        f"{counts['planned_expressible']} planned, "
        f"{counts['blocked_by_language']} language-blocked; "
        f"{counts['companion_artifacts']} checked companion artifact)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
