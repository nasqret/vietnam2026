"""Checked content identity for the complete model-v3 theorem ladder.

The public catalog is useful evidence, but it is not proof authority.  This
module first binds the catalog to the exact 247-entry source ladder and then,
on demand, reconstructs every certificate from its authored tactic script.
Each reconstructed certificate is checked by the independent kernel from the
empty context against the theorem's original closed proposition.

Records remain in declaration order.  Consequently prefix ``i`` means exactly
``THEOREMS[:i]``: the current theorem and every later theorem are unavailable.
Individual replay records, full identities, and prefix digests are cached, so
building all prefix environments replays each theorem at most once.

Importing this module is deliberately cheap and does not import Peano Lab.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import TYPE_CHECKING, Collection


if TYPE_CHECKING:  # pragma: no cover - imports used only by static checkers
    from peano_lab.library.theorems import TheoremSpec


LIBRARY_IDENTITY_FORMAT = "peano-model-v3-library-identity"
LIBRARY_IDENTITY_VERSION = 1
CATALOG_SCHEMA = "peano-library-snapshot-v2"
CERTIFICATE_REPRESENTATION = "python-dataclass-repr-with-cut-v2"
EXPECTED_LIBRARY_SIZE = 247
EXPECTED_ORDERED_ROOT_SHA256 = (
    "eb4775dfd181dc5e45bec463a93f14b0ea9d02501c40c5167b7cae77cd4ff432"
)
EXPECTED_SOURCE_SHA256 = (
    "295ca3b65970324e7d2ed51b57dc4510227b0abbc2d35b68a809dbde26aba868"
)
EXPECTED_FULL_IDENTITY_SHA256 = (
    "d173c2f1a32de6a9207fdee1ac77334a77cdebbf84568559eeb6066653d94c63"
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
PUBLIC_LIBRARY_CATALOG = (
    REPOSITORY_ROOT / "artifacts" / "peano-library" / "catalog-v1.json"
)
PUBLIC_LIBRARY_SOURCE = (
    PEANO_PYTHON / "peano_lab" / "library" / "theorems.py"
)

_CATALOG_FIELDS = frozenset(
    {
        "certificate_policy",
        "certificate_representation",
        "ordered_root_sha256",
        "schema",
        "theorem_count",
        "theorem_source",
        "theorem_source_sha256",
        "theorems",
    }
)
_ROW_FIELDS = frozenset(
    {
        "certificate_representation",
        "certificate_sha256",
        "cut_nodes",
        "dependencies",
        "index",
        "layer",
        "name",
        "proof_depth",
        "proof_nodes",
        "script",
        "script_sha256",
        "statement",
        "statement_sha256",
        "summary",
    }
)
_HEX_SHA256 = re.compile(r"[0-9a-f]{64}")


class LibraryIdentityV3Error(RuntimeError):
    """The model-v3 theorem authority could not be independently identified."""


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _json_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _source_spec_record(spec: "TheoremSpec") -> dict[str, object]:
    return {
        "name": spec.name,
        "statement": spec.statement,
        "dependencies": list(spec.dependencies),
        "script": list(spec.script),
        "summary": spec.summary,
    }


@dataclass(frozen=True, slots=True)
class ModelV3LibraryIdentityRecord:
    """One source rung and its independently checked closed certificate."""

    name: str
    statement: str
    dependencies: tuple[str, ...]
    source_spec_sha256: str
    script_sha256: str
    certificate_sha256: str
    proof_nodes: int
    proof_depth: int

    def to_record(self) -> dict[str, object]:
        """Return a fresh canonical-JSON-compatible value."""

        return {
            "name": self.name,
            "statement": self.statement,
            "dependencies": list(self.dependencies),
            "source_spec_sha256": self.source_spec_sha256,
            "script_sha256": self.script_sha256,
            "certificate_sha256": self.certificate_sha256,
            "proof_nodes": self.proof_nodes,
            "proof_depth": self.proof_depth,
        }


@dataclass(frozen=True, slots=True)
class _ValidatedCatalog:
    specifications: tuple["TheoremSpec", ...]
    rows: tuple[dict[str, object], ...]
    catalog_sha256: str
    certificate_policy_sha256: str


def _closed_formula_and_statement(source: str) -> tuple[object, str]:
    from peano_lab.kernel.formulas import parse_formula_with_names, pretty_formula

    formula, free_names = parse_formula_with_names(source)
    if free_names:
        raise LibraryIdentityV3Error(
            "model-v3 theorem statement is not closed; free variable(s): "
            + ", ".join(free_names)
        )
    return formula, pretty_formula(formula, list(free_names))


def _require_sha256(label: str, value: object) -> str:
    if type(value) is not str or _HEX_SHA256.fullmatch(value) is None:
        raise LibraryIdentityV3Error(f"{label} must be a lowercase SHA-256")
    return value


@lru_cache(maxsize=1)
def _validated_catalog() -> _ValidatedCatalog:
    """Bind the v2 catalog to its exact source ladder without replaying it."""

    if str(PEANO_PYTHON) not in sys.path:
        sys.path.insert(0, str(PEANO_PYTHON))
    from peano_lab.library.theorems import THEOREMS

    try:
        raw = PUBLIC_LIBRARY_CATALOG.read_bytes()
        catalog = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LibraryIdentityV3Error("cannot read the model-v3 catalog") from exc
    if type(catalog) is not dict or set(catalog) != _CATALOG_FIELDS:
        raise LibraryIdentityV3Error("model-v3 catalog has invalid top-level fields")
    if catalog.get("schema") != CATALOG_SCHEMA:
        raise LibraryIdentityV3Error("model-v3 catalog has the wrong schema")
    if catalog.get("certificate_representation") != CERTIFICATE_REPRESENTATION:
        raise LibraryIdentityV3Error(
            "model-v3 catalog has the wrong certificate representation"
        )
    policy = catalog.get("certificate_policy")
    if type(policy) is not str or not policy.strip():
        raise LibraryIdentityV3Error("model-v3 catalog has no certificate policy")
    if catalog.get("theorem_source") != (
        "peano-lab/py/peano_lab/library/theorems.py"
    ):
        raise LibraryIdentityV3Error("model-v3 catalog names the wrong source")
    if catalog.get("theorem_count") != EXPECTED_LIBRARY_SIZE:
        raise LibraryIdentityV3Error("model-v3 catalog has the wrong theorem count")
    if len(THEOREMS) != EXPECTED_LIBRARY_SIZE:
        raise LibraryIdentityV3Error(
            f"model-v3 source must contain {EXPECTED_LIBRARY_SIZE} theorems"
        )

    try:
        source_sha256 = hashlib.sha256(PUBLIC_LIBRARY_SOURCE.read_bytes()).hexdigest()
    except OSError as exc:
        raise LibraryIdentityV3Error("cannot read the model-v3 theorem source") from exc
    if (
        source_sha256 != EXPECTED_SOURCE_SHA256
        or catalog.get("theorem_source_sha256") != source_sha256
    ):
        raise LibraryIdentityV3Error("model-v3 theorem source hash is stale")

    rows = catalog.get("theorems")
    if type(rows) is not list or len(rows) != EXPECTED_LIBRARY_SIZE:
        raise LibraryIdentityV3Error("model-v3 catalog theorem rows are malformed")
    ordered_root = _json_sha256(rows)
    if (
        ordered_root != EXPECTED_ORDERED_ROOT_SHA256
        or catalog.get("ordered_root_sha256") != ordered_root
    ):
        raise LibraryIdentityV3Error("model-v3 catalog ordered root is invalid")

    prior_names: set[str] = set()
    validated_rows: list[dict[str, object]] = []
    for index, (row, spec) in enumerate(zip(rows, THEOREMS, strict=True)):
        if type(row) is not dict or set(row) != _ROW_FIELDS:
            raise LibraryIdentityV3Error(
                f"model-v3 catalog row {index} has invalid fields"
            )
        if (
            type(spec.name) is not str
            or not spec.name
            or spec.name in prior_names
        ):
            raise LibraryIdentityV3Error("model-v3 source has invalid theorem names")
        if not all(type(item) is str for item in spec.dependencies):
            raise LibraryIdentityV3Error(
                f"model-v3 theorem {spec.name!r} has malformed dependencies"
            )
        unavailable = set(spec.dependencies).difference(prior_names)
        if unavailable:
            raise LibraryIdentityV3Error(
                f"model-v3 theorem {spec.name!r} has non-prefix dependencies: "
                + ", ".join(sorted(unavailable))
            )
        expected_source = {
            "index": index,
            "name": spec.name,
            "statement": spec.statement,
            "dependencies": list(spec.dependencies),
            "script": list(spec.script),
            "summary": spec.summary,
            "statement_sha256": _text_sha256(spec.statement),
            "script_sha256": _text_sha256("\n".join(spec.script) + "\n"),
            "certificate_representation": CERTIFICATE_REPRESENTATION,
        }
        differing = [
            key for key, expected in expected_source.items() if row.get(key) != expected
        ]
        if differing:
            raise LibraryIdentityV3Error(
                f"model-v3 catalog source mismatch for {spec.name!r}: "
                + ", ".join(differing)
            )
        _require_sha256(
            f"certificate hash for {spec.name!r}", row.get("certificate_sha256")
        )
        if type(row.get("layer")) is not str or not str(row["layer"]).strip():
            raise LibraryIdentityV3Error(
                f"model-v3 catalog layer for {spec.name!r} is malformed"
            )
        for field in ("proof_nodes", "proof_depth"):
            if type(row.get(field)) is not int or row[field] < 1:
                raise LibraryIdentityV3Error(
                    f"model-v3 catalog {field} for {spec.name!r} is malformed"
                )
        if type(row.get("cut_nodes")) is not int or row["cut_nodes"] < 0:
            raise LibraryIdentityV3Error(
                f"model-v3 catalog cut count for {spec.name!r} is malformed"
            )
        prior_names.add(spec.name)
        # The row never escapes this private cached object.
        validated_rows.append(row)

    return _ValidatedCatalog(
        specifications=tuple(THEOREMS),
        rows=tuple(validated_rows),
        catalog_sha256=_json_sha256(catalog),
        certificate_policy_sha256=_text_sha256(policy),
    )


@lru_cache(maxsize=EXPECTED_LIBRARY_SIZE)
def _replay_record(index: int) -> ModelV3LibraryIdentityRecord:
    catalog = _validated_catalog()
    spec = catalog.specifications[index]
    row = catalog.rows[index]

    from peano_lab.engine.state import proof_metrics
    from peano_lab.kernel.checker import check
    from peano_lab.library.theorems import replay

    checked = replay(spec.name)
    if checked.spec != spec:
        raise LibraryIdentityV3Error(
            f"replay returned the wrong source spec for {spec.name!r}"
        )
    formula, statement = _closed_formula_and_statement(spec.statement)
    if checked.formula != formula:
        raise LibraryIdentityV3Error(
            f"replay returned the wrong proposition for {spec.name!r}"
        )
    # This call is intentionally independent of the tactic/library finalizer.
    if not check((), checked.certificate, formula):
        raise LibraryIdentityV3Error(
            f"independent kernel rejected model-v3 theorem {spec.name!r}"
        )
    nodes, depth = proof_metrics(checked.certificate)
    if checked.proof_nodes != nodes:
        raise LibraryIdentityV3Error(
            f"replay reported inconsistent metrics for {spec.name!r}"
        )
    certificate_sha256 = _text_sha256(repr(checked.certificate))
    expected_replay = {
        "certificate_sha256": certificate_sha256,
        "proof_nodes": nodes,
        "proof_depth": depth,
    }
    differing = [
        key for key, expected in expected_replay.items() if row.get(key) != expected
    ]
    if differing:
        raise LibraryIdentityV3Error(
            f"model-v3 catalog replay mismatch for {spec.name!r}: "
            + ", ".join(differing)
        )
    return ModelV3LibraryIdentityRecord(
        name=spec.name,
        statement=statement,
        dependencies=tuple(spec.dependencies),
        source_spec_sha256=_json_sha256(_source_spec_record(spec)),
        script_sha256=_json_sha256(list(spec.script)),
        certificate_sha256=certificate_sha256,
        proof_nodes=nodes,
        proof_depth=depth,
    )


def _prefix_length(value: int) -> int:
    if type(value) is not int or not 0 <= value <= EXPECTED_LIBRARY_SIZE:
        raise ValueError(
            f"prefix length must lie between 0 and {EXPECTED_LIBRARY_SIZE}"
        )
    return value


@lru_cache(maxsize=EXPECTED_LIBRARY_SIZE + 1)
def _prefix_identity(prefix_length: int) -> tuple[ModelV3LibraryIdentityRecord, ...]:
    prefix_length = _prefix_length(prefix_length)
    _validated_catalog()
    return tuple(_replay_record(index) for index in range(prefix_length))


@lru_cache(maxsize=1)
def model_v3_library_identity() -> tuple[ModelV3LibraryIdentityRecord, ...]:
    """Replay and independently kernel-check all 247 source-ordered entries."""

    return _prefix_identity(EXPECTED_LIBRARY_SIZE)


def _identity_document(
    prefix_length: int,
    records: tuple[ModelV3LibraryIdentityRecord, ...],
) -> dict[str, object]:
    prefix_length = _prefix_length(prefix_length)
    catalog = _validated_catalog()
    if len(records) != prefix_length:
        raise LibraryIdentityV3Error("model-v3 identity prefix length is inconsistent")
    return {
        "format": LIBRARY_IDENTITY_FORMAT,
        "v": LIBRARY_IDENTITY_VERSION,
        "catalog": {
            "schema": CATALOG_SCHEMA,
            "catalog_sha256": catalog.catalog_sha256,
            "ordered_root_sha256": EXPECTED_ORDERED_ROOT_SHA256,
            "theorem_source": "peano-lab/py/peano_lab/library/theorems.py",
            "theorem_source_sha256": EXPECTED_SOURCE_SHA256,
            "certificate_representation": CERTIFICATE_REPRESENTATION,
            "certificate_policy_sha256": catalog.certificate_policy_sha256,
        },
        "library_size": EXPECTED_LIBRARY_SIZE,
        "prefix_length": prefix_length,
        "theorems": [record.to_record() for record in records],
    }


def _identity_record(prefix_length: int) -> dict[str, object]:
    prefix_length = _prefix_length(prefix_length)
    return _identity_document(prefix_length, _prefix_identity(prefix_length))


@lru_cache(maxsize=1)
def _catalog_identity() -> tuple[ModelV3LibraryIdentityRecord, ...]:
    """Reconstruct the checked identity fields from the sealed catalog.

    Unlike :func:`model_v3_library_identity`, this does not replay tactic
    scripts or certificates.  The catalog rows are already bound to exact
    theorem source by hard-coded source and ordered-root hashes in
    :func:`_validated_catalog`.  This projection is suitable for loading an
    untrusted inference policy; training/release gates continue to use the
    independent replay path above.
    """

    catalog = _validated_catalog()
    records: list[ModelV3LibraryIdentityRecord] = []
    for spec, row in zip(catalog.specifications, catalog.rows, strict=True):
        _, statement = _closed_formula_and_statement(spec.statement)
        certificate_sha256 = row.get("certificate_sha256")
        proof_nodes = row.get("proof_nodes")
        proof_depth = row.get("proof_depth")
        if (
            type(certificate_sha256) is not str
            or type(proof_nodes) is not int
            or type(proof_depth) is not int
        ):  # pragma: no cover - guaranteed by _validated_catalog
            raise LibraryIdentityV3Error(
                "validated model-v3 catalog lost certificate identity fields"
            )
        records.append(
            ModelV3LibraryIdentityRecord(
                name=spec.name,
                statement=statement,
                dependencies=tuple(spec.dependencies),
                source_spec_sha256=_json_sha256(_source_spec_record(spec)),
                script_sha256=_json_sha256(list(spec.script)),
                certificate_sha256=certificate_sha256,
                proof_nodes=proof_nodes,
                proof_depth=proof_depth,
            )
        )
    return tuple(records)


@lru_cache(maxsize=EXPECTED_LIBRARY_SIZE + 1)
def model_v3_catalog_prefix_sha256(prefix_length: int) -> str:
    """Return a source/catalog-bound prefix digest without replaying proofs."""

    prefix_length = _prefix_length(prefix_length)
    records = _catalog_identity()[:prefix_length]
    digest = _json_sha256(_identity_document(prefix_length, records))
    if (
        prefix_length == EXPECTED_LIBRARY_SIZE
        and digest != EXPECTED_FULL_IDENTITY_SHA256
    ):
        raise LibraryIdentityV3Error(
            "model-v3 catalog projection has the wrong full identity"
        )
    return digest


def model_v3_catalog_full_identity_sha256() -> str:
    """Return the sealed full digest used for latency-sensitive inference."""

    return model_v3_catalog_prefix_sha256(EXPECTED_LIBRARY_SIZE)


def model_v3_library_identity_record() -> dict[str, object]:
    """Return a fresh canonical JSON document for the full checked ladder."""

    return _identity_record(EXPECTED_LIBRARY_SIZE)


@lru_cache(maxsize=1)
def model_v3_full_identity_sha256() -> str:
    """Return the canonical SHA-256 of the full checked identity document."""

    digest = _json_sha256(model_v3_library_identity_record())
    if digest != EXPECTED_FULL_IDENTITY_SHA256:
        raise LibraryIdentityV3Error(
            "checked model-v3 ladder has the wrong full identity"
        )
    return digest


@lru_cache(maxsize=EXPECTED_LIBRARY_SIZE + 1)
def model_v3_prefix_sha256(prefix_length: int) -> str:
    """Return the checked identity digest for exactly ``THEOREMS[:i]``."""

    return _json_sha256(_identity_record(_prefix_length(prefix_length)))


@lru_cache(maxsize=EXPECTED_LIBRARY_SIZE + 1)
def model_v3_prefix_names(prefix_length: int) -> tuple[str, ...]:
    """Return source-ordered theorem names for exactly ``THEOREMS[:i]``."""

    prefix_length = _prefix_length(prefix_length)
    catalog = _validated_catalog()
    return tuple(spec.name for spec in catalog.specifications[:prefix_length])


def model_v3_prefix_index(collection: Collection[str]) -> int:
    """Return ``i`` iff ``collection`` is exactly the name set of prefix ``i``.

    Capability records are sometimes canonicalized independently of declaration
    order, so collection iteration order is intentionally irrelevant. Duplicate
    names remain an error rather than being silently discarded.
    """

    if isinstance(collection, (str, bytes)):
        raise ValueError("a theorem-name collection cannot be text")
    try:
        names = tuple(collection)
    except TypeError as exc:
        raise ValueError("theorem names must be a finite collection") from exc
    if not all(type(name) is str for name in names) or len(names) != len(set(names)):
        raise ValueError("theorem names must be distinct strings")
    prefix_length = _prefix_length(len(names))
    expected = frozenset(model_v3_prefix_names(prefix_length))
    if frozenset(names) != expected:
        raise ValueError("theorem authority is not an exact model-v3 prefix")
    return prefix_length


def clear_model_v3_library_identity_cache() -> None:
    """Clear every immutable model-v3 identity cache (primarily for tests)."""

    model_v3_prefix_names.cache_clear()
    model_v3_prefix_sha256.cache_clear()
    model_v3_full_identity_sha256.cache_clear()
    model_v3_library_identity.cache_clear()
    model_v3_catalog_prefix_sha256.cache_clear()
    _catalog_identity.cache_clear()
    _prefix_identity.cache_clear()
    _replay_record.cache_clear()
    _validated_catalog.cache_clear()


__all__ = [
    "LIBRARY_IDENTITY_FORMAT",
    "LIBRARY_IDENTITY_VERSION",
    "CATALOG_SCHEMA",
    "CERTIFICATE_REPRESENTATION",
    "EXPECTED_LIBRARY_SIZE",
    "EXPECTED_ORDERED_ROOT_SHA256",
    "EXPECTED_SOURCE_SHA256",
    "EXPECTED_FULL_IDENTITY_SHA256",
    "PUBLIC_LIBRARY_CATALOG",
    "PUBLIC_LIBRARY_SOURCE",
    "LibraryIdentityV3Error",
    "ModelV3LibraryIdentityRecord",
    "model_v3_library_identity",
    "model_v3_library_identity_record",
    "model_v3_catalog_prefix_sha256",
    "model_v3_catalog_full_identity_sha256",
    "model_v3_full_identity_sha256",
    "model_v3_prefix_sha256",
    "model_v3_prefix_names",
    "model_v3_prefix_index",
    "clear_model_v3_library_identity_cache",
]
