"""Content identity for the complete model-v2 theorem authority.

This module deliberately has no eager Peano Lab imports.  Reading constants or
importing training helpers must not replay forty-five theorem certificates.
The first call to :func:`model_v2_library_identity` loads the public library,
computes the dependency closure of the sealed benchmark targets, replays every
remaining theorem, asks the independent kernel to check the resulting *closed*
certificate again, and freezes the resulting records.

Hash preimages are intentionally explicit:

* ``source_spec_sha256`` hashes the canonical JSON form of all five fields in
  the repository's :class:`TheoremSpec` (including its source statement,
  tactic script, and pedagogical summary);
* ``script_sha256`` hashes the canonical JSON array of exact tactic lines;
* ``certificate_sha256`` hashes the deterministic ``repr`` of the closed proof
  term, matching the public modular-arithmetic validation artifact; and
* the library digest hashes the versioned canonical JSON identity document.

Only the kernel-checked identity is cached.  JSON-shaped accessors always
construct fresh containers, so a caller cannot mutate the cached attestation.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import TYPE_CHECKING


if TYPE_CHECKING:  # pragma: no cover - imports used by static type checkers only
    from peano_lab.library.theorems import TheoremSpec


LIBRARY_IDENTITY_FORMAT = "peano-model-v2-library-identity"
LIBRARY_IDENTITY_VERSION = 1

# These are evaluation targets, not model-v2 premises.  The identity module
# owns the boundary so prompt, dataset, evaluator, and request integrations can
# all consume the same immutable definition without creating an import cycle.
SEALED_LIBRARY_GOALS: tuple[tuple[str, str], ...] = (
    ("le_trans", "forall n m k. n <= m -> m <= k -> n <= k"),
    ("le_antisymm", "forall n m. n <= m -> m <= n -> n = m"),
    ("le_total", "forall n m. n <= m \\/ m <= n"),
    ("mul_eq_zero", "forall n m. n * m = 0 -> n = 0 \\/ m = 0"),
)
SEALED_LIBRARY_NAMES = frozenset(name for name, _ in SEALED_LIBRARY_GOALS)

# The current 247-row catalog is the immutable baseline, not a permanent upper
# bound.  Model-v2 may coexist with a later append-only public ladder, but any
# rewrite/reorder of these baseline rows remains a compatibility failure.
EXPECTED_PUBLIC_LIBRARY_COUNT = 247
EXPECTED_PUBLIC_LIBRARY_PREFIX_SHA256 = (
    "eb4775dfd181dc5e45bec463a93f14b0ea9d02501c40c5167b7cae77cd4ff432"
)
EXPECTED_MODEL_V2_LIBRARY_COUNT = 56
EXPECTED_MODEL_V2_LIBRARY_SHA256 = (
    "3ce83721f4517f2d5f2e734da1fbeae086473c4d1b8abb45d875a52769096439"
)
LIVE_CATALOG_SCHEMA = "peano-library-snapshot-v3"
CERTIFICATE_REPRESENTATION = "python-dataclass-repr-with-cut-v2"
EXPECTED_CERTIFICATE_POLICY_SHA256 = (
    "8e1019a14a523e72e82723e7c7667f79daf25c271fddf487154efeb43701bd57"
)

_LIVE_CATALOG_FIELDS = frozenset(
    {
        "certificate_policy",
        "certificate_representation",
        "ordered_root_sha256",
        "schema",
        "theorem_count",
        "theorem_source_root_sha256",
        "theorem_sources",
        "theorems",
    }
)
_LEGACY_ROW_FIELDS = frozenset(
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
_LIVE_ROW_FIELDS = _LEGACY_ROW_FIELDS | {
    "distinct_proof_objects",
    "proof_edges",
    "reused_proof_references",
}
_SOURCE_FIELDS = frozenset({"path", "sha256"})
_PRIMARY_SOURCE = "peano-lab/py/peano_lab/library/theorems.py"
_SOURCE_DIRECTORY = "peano-lab/py/peano_lab/library/"
_HEX_SHA256 = re.compile(r"[0-9a-f]{64}")

# Model-v2 is a published historical authority.  The public theorem ladder is
# intentionally allowed to grow, but the meaning of an already trained policy
# surface must not grow with it.  Pin the exact old allow-list rather than
# recomputing it from the current dependency graph (which now contains FTA).
MODEL_V2_LIBRARY_NAMES: tuple[str, ...] = (
    "add_assoc", "add_comm", "add_congr", "add_eq_zero_left",
    "add_eq_zero_right", "add_left_cancel", "add_mul", "add_residue",
    "add_residue_lift", "add_right_cancel", "add_succ_left",
    "antisymm_from_witnesses", "drop_add_prefix_from_fixed", "eq_symm",
    "eq_trans", "fourth_power_regroup", "le_refl", "le_succ_self",
    "le_zero", "mod5_fourth_power_one", "mod5_fourth_power_residue_four",
    "mod5_fourth_power_residue_one", "mod5_fourth_power_residue_three",
    "mod5_fourth_power_residue_two", "mod5_nonzero_residue_cases",
    "mod5_residue_complete", "mod5_square_residue_four",
    "mod5_square_residue_one", "mod5_square_residue_three",
    "mod5_square_residue_two", "mul_add", "mul_assoc", "mul_comm",
    "mul_congr", "mul_one", "mul_succ_left", "mul_zero_left",
    "multiple_add", "multiple_mul_left", "multiple_mul_right",
    "multiple_refl", "multiple_trans", "multiple_zero",
    "no_succ_add_fixed", "not_multiple_from_pointwise",
    "not_multiple_pointwise", "one_mul", "one_multiple", "square_decomp",
    "square_residue_lift", "square_residue_witness", "succ_congr",
    "succ_injective", "succ_ne_zero", "zero_add", "zero_le",
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
MOD5_SOURCE_REPORT = (
    REPOSITORY_ROOT
    / "artifacts"
    / "peano-library"
    / "mod5-source-validation-report.json"
)
PUBLIC_LIBRARY_CATALOG = (
    REPOSITORY_ROOT / "artifacts" / "peano-library" / "catalog-v1.json"
)
PUBLIC_LIBRARY_SOURCE = (
    PEANO_PYTHON / "peano_lab" / "library" / "theorems.py"
)


class LibraryIdentityError(RuntimeError):
    """The public theorem authority could not be independently identified."""


def sealed_library_closure(
    specifications: tuple["TheoremSpec", ...],
) -> frozenset[str]:
    """Return benchmark targets and every theorem depending on one of them.

    A descendant would leak a sealed certificate even if its own name and
    statement differ from the benchmark.  Computing this reverse dependency
    closure makes that information-flow boundary explicit and fail-closed.
    """

    names = tuple(spec.name for spec in specifications)
    if len(names) != len(set(names)):
        raise LibraryIdentityError("public theorem library has duplicate names")
    missing = SEALED_LIBRARY_NAMES.difference(names)
    if missing:
        raise LibraryIdentityError(
            "sealed theorem(s) are absent from the public library: "
            + ", ".join(sorted(missing))
        )
    known = frozenset(names)
    for spec in specifications:
        unknown = set(spec.dependencies).difference(known)
        if unknown:
            raise LibraryIdentityError(
                f"public theorem {spec.name!r} has unknown dependencies: "
                + ", ".join(sorted(unknown))
            )

    excluded = set(SEALED_LIBRARY_NAMES)
    changed = True
    while changed:
        changed = False
        for spec in specifications:
            if spec.name not in excluded and excluded.intersection(spec.dependencies):
                excluded.add(spec.name)
                changed = True
    return frozenset(excluded)


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _json_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _snapshot_document_sha256(value: object) -> str:
    text = json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _require_sha256(label: str, value: object) -> str:
    if type(value) is not str or _HEX_SHA256.fullmatch(value) is None:
        raise LibraryIdentityError(f"{label} must be a lowercase SHA-256")
    return value


@dataclass(frozen=True, slots=True)
class LibraryIdentityRecord:
    """One independently replayed theorem in the model-v2 authority."""

    name: str
    statement: str
    dependencies: tuple[str, ...]
    source_spec_sha256: str
    script_sha256: str
    certificate_sha256: str
    proof_nodes: int
    proof_depth: int

    def to_record(self) -> dict[str, object]:
        """Return a fresh canonical-JSON-compatible record."""

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


def _source_spec_record(spec: "TheoremSpec") -> dict[str, object]:
    """Canonical value-level preimage of an exact repository theorem spec."""

    return {
        "name": spec.name,
        "statement": spec.statement,
        "dependencies": list(spec.dependencies),
        "script": list(spec.script),
        "summary": spec.summary,
    }


def _load_mod5_report() -> dict[str, object]:
    try:
        raw = MOD5_SOURCE_REPORT.read_bytes()
        report = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LibraryIdentityError(
            "cannot read the modular-arithmetic source validation report"
        ) from exc
    if type(report) is not dict:
        raise LibraryIdentityError(
            "modular-arithmetic source validation report must be an object"
        )
    return report


def _load_public_catalog() -> dict[str, object]:
    try:
        raw = PUBLIC_LIBRARY_CATALOG.read_bytes()
        catalog = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LibraryIdentityError("cannot read the public library catalog") from exc
    if type(catalog) is not dict:
        raise LibraryIdentityError("public library catalog must be an object")
    return catalog


def _public_catalog_rows(
    catalog: dict[str, object],
    specifications: tuple["TheoremSpec", ...],
) -> dict[str, dict[str, object]]:
    if set(catalog) != _LIVE_CATALOG_FIELDS:
        raise LibraryIdentityError("public library catalog has invalid top-level fields")
    if catalog.get("schema") != LIVE_CATALOG_SCHEMA:
        raise LibraryIdentityError("public library catalog has the wrong schema")
    if catalog.get("certificate_representation") != CERTIFICATE_REPRESENTATION:
        raise LibraryIdentityError(
            "public library catalog has the wrong certificate representation"
        )
    policy = catalog.get("certificate_policy")
    if (
        type(policy) is not str
        or not policy.strip()
        or hashlib.sha256(policy.encode("utf-8")).hexdigest()
        != EXPECTED_CERTIFICATE_POLICY_SHA256
    ):
        raise LibraryIdentityError("public library catalog certificate policy changed")

    sources = catalog.get("theorem_sources")
    if type(sources) is not list or not sources:
        raise LibraryIdentityError("public library catalog theorem sources are malformed")
    source_paths: set[str] = set()
    for index, source in enumerate(sources):
        if type(source) is not dict or set(source) != _SOURCE_FIELDS:
            raise LibraryIdentityError(
                f"public library catalog theorem source {index} is malformed"
            )
        path = source.get("path")
        if (
            type(path) is not str
            or not path.startswith(_SOURCE_DIRECTORY)
            or not path.endswith(".py")
            or Path(path).is_absolute()
            or ".." in Path(path).parts
            or Path(path).as_posix() != path
            or path in source_paths
        ):
            raise LibraryIdentityError(
                f"public library catalog theorem source {index} has an invalid path"
            )
        expected_digest = _require_sha256(
            f"public theorem source hash for {path!r}", source.get("sha256")
        )
        try:
            actual_digest = hashlib.sha256(
                (REPOSITORY_ROOT / path).read_bytes()
            ).hexdigest()
        except OSError as exc:
            raise LibraryIdentityError(
                f"cannot read public theorem source {path!r}"
            ) from exc
        if actual_digest != expected_digest:
            raise LibraryIdentityError(
                f"public theorem source hash for {path!r} is stale"
            )
        source_paths.add(path)
    if sources[0].get("path") != _PRIMARY_SOURCE:
        raise LibraryIdentityError("public library catalog names the wrong primary source")
    source_root = _require_sha256(
        "public theorem source root", catalog.get("theorem_source_root_sha256")
    )
    if source_root != _snapshot_document_sha256(sources):
        raise LibraryIdentityError("public library catalog theorem source root is invalid")

    rows = catalog.get("theorems")
    if (
        type(rows) is not list
        or catalog.get("theorem_count") != len(rows)
        or len(rows) < EXPECTED_PUBLIC_LIBRARY_COUNT
    ):
        raise LibraryIdentityError("public library catalog has invalid metadata")
    if len(specifications) != len(rows):
        raise LibraryIdentityError(
            "public theorem library and catalog have different theorem counts"
        )
    expected_root = _json_sha256(rows)
    if catalog.get("ordered_root_sha256") != expected_root:
        raise LibraryIdentityError("public library catalog ordered root is invalid")

    result: dict[str, dict[str, object]] = {}
    prior_names: set[str] = set()
    for index, (row, spec) in enumerate(zip(rows, specifications, strict=True)):
        if type(row) is not dict or set(row) != _LIVE_ROW_FIELDS:
            raise LibraryIdentityError(
                f"public library catalog row {index} has invalid fields"
            )
        if (
            type(spec.name) is not str
            or not spec.name
            or spec.name in prior_names
        ):
            raise LibraryIdentityError("public theorem library has invalid names")
        if not all(type(item) is str for item in spec.dependencies):
            raise LibraryIdentityError(
                f"public theorem {spec.name!r} has malformed dependencies"
            )
        unavailable = set(spec.dependencies).difference(prior_names)
        if unavailable:
            raise LibraryIdentityError(
                f"public theorem {spec.name!r} has non-prefix dependencies: "
                + ", ".join(sorted(unavailable))
            )
        name = row["name"]
        if name in result:
            raise LibraryIdentityError(f"duplicate public catalog row {name!r}")
        expected_source = {
            "index": index,
            "name": spec.name,
            "statement": spec.statement,
            "dependencies": list(spec.dependencies),
            "script": list(spec.script),
            "summary": spec.summary,
            "statement_sha256": hashlib.sha256(
                spec.statement.encode("utf-8")
            ).hexdigest(),
            "script_sha256": hashlib.sha256(
                ("\n".join(spec.script) + "\n").encode("utf-8")
            ).hexdigest(),
            "certificate_representation": CERTIFICATE_REPRESENTATION,
        }
        for key, expected in expected_source.items():
            if row.get(key) != expected:
                raise LibraryIdentityError(
                    f"public catalog source mismatch for {spec.name!r}: {key}"
                )
        _require_sha256(
            f"public certificate hash for {spec.name!r}",
            row.get("certificate_sha256"),
        )
        if type(row.get("layer")) is not str or not str(row["layer"]).strip():
            raise LibraryIdentityError(
                f"public catalog layer for {spec.name!r} is malformed"
            )
        for field in ("proof_nodes", "proof_depth"):
            if type(row.get(field)) is not int or row[field] < 1:
                raise LibraryIdentityError(
                    f"public catalog {field} for {spec.name!r} is malformed"
                )
        if type(row.get("cut_nodes")) is not int or row["cut_nodes"] < 0:
            raise LibraryIdentityError(
                f"public catalog cut count for {spec.name!r} is malformed"
            )
        for field in (
            "distinct_proof_objects",
            "proof_edges",
            "reused_proof_references",
        ):
            if type(row.get(field)) is not int or row[field] < 0:
                raise LibraryIdentityError(
                    f"public catalog {field} for {spec.name!r} is malformed"
                )
        if row["distinct_proof_objects"] < 1:
            raise LibraryIdentityError(
                f"public catalog distinct object count for {spec.name!r} is malformed"
            )
        result[name] = row
        prior_names.add(spec.name)

    legacy_prefix = [
        {key: row[key] for key in _LEGACY_ROW_FIELDS}
        for row in rows[:EXPECTED_PUBLIC_LIBRARY_COUNT]
    ]
    if _json_sha256(legacy_prefix) != EXPECTED_PUBLIC_LIBRARY_PREFIX_SHA256:
        raise LibraryIdentityError(
            "public library catalog rewrites the frozen 247-row baseline"
        )
    return result


def _mod5_rows(report: dict[str, object]) -> dict[str, dict[str, object]]:
    rows = report.get("lemmas")
    if type(rows) is not list or not rows:
        raise LibraryIdentityError(
            "modular-arithmetic source validation report has no lemma rows"
        )
    result: dict[str, dict[str, object]] = {}
    for row in rows:
        if type(row) is not dict or type(row.get("name")) is not str:
            raise LibraryIdentityError(
                "modular-arithmetic source validation report has a malformed lemma"
            )
        name = row["name"]
        if name in result:
            raise LibraryIdentityError(
                f"duplicate modular-arithmetic validation row {name!r}"
            )
        result[name] = row
    return result


def _canonical_closed_statement(source: str) -> str:
    from peano_lab.kernel.formulas import parse_formula_with_names, pretty_formula

    formula, free_names = parse_formula_with_names(source)
    if free_names:
        raise LibraryIdentityError(
            "model-v2 theorem statement is not closed; free variable(s): "
            + ", ".join(free_names)
        )
    return pretty_formula(formula, list(free_names))


def _validate_mod5_record(
    record: LibraryIdentityRecord,
    row: dict[str, object],
) -> None:
    try:
        artifact_statement = _canonical_closed_statement(str(row["statement"]))
    except (KeyError, ValueError) as exc:
        raise LibraryIdentityError(
            f"source validation row for {record.name!r} is malformed"
        ) from exc
    expected = {
        "statement": artifact_statement,
        "dependencies": tuple(row.get("dependencies", ())),
        "certificate_sha256": row.get("certificate_sha256"),
        "proof_nodes": row.get("proof_nodes"),
        "proof_depth": row.get("proof_depth"),
    }
    actual = {
        "statement": record.statement,
        "dependencies": record.dependencies,
        "certificate_sha256": record.certificate_sha256,
        "proof_nodes": record.proof_nodes,
        "proof_depth": record.proof_depth,
    }
    if actual != expected:
        differing = ", ".join(
            key for key in actual if actual[key] != expected[key]
        )
        raise LibraryIdentityError(
            f"source validation mismatch for {record.name!r}: {differing}"
        )


def _validate_public_catalog_record(
    record: LibraryIdentityRecord,
    row: dict[str, object],
) -> None:
    expected = {
        "certificate_representation": "python-dataclass-repr-with-cut-v2",
        "certificate_sha256": record.certificate_sha256,
        "dependencies": list(record.dependencies),
        "proof_depth": record.proof_depth,
        "proof_nodes": record.proof_nodes,
    }
    differing = [key for key, value in expected.items() if row.get(key) != value]
    if differing:
        raise LibraryIdentityError(
            f"public catalog replay mismatch for {record.name!r}: "
            + ", ".join(differing)
        )


@lru_cache(maxsize=1)
def model_v2_library_identity() -> tuple[LibraryIdentityRecord, ...]:
    """Replay and return the exact 56-theorem model-v2 library identity.

    Results are sorted by theorem name rather than source order.  Source order
    remains committed by each theorem's dependency tuple and source-spec hash.
    """

    if str(PEANO_PYTHON) not in sys.path:
        sys.path.insert(0, str(PEANO_PYTHON))

    from peano_lab.engine.proof_reduction import erase_trusted_cuts
    from peano_lab.engine.state import proof_metrics
    from peano_lab.kernel.checker import check
    from peano_lab.library.theorems import (
        MOD5_THEOREMS,
        THEOREMS,
        normalise_cuts,
        replay,
    )

    names = [spec.name for spec in THEOREMS]
    allowed_names = frozenset(MODEL_V2_LIBRARY_NAMES)
    if len(allowed_names) != EXPECTED_MODEL_V2_LIBRARY_COUNT:
        raise LibraryIdentityError("model-v2 theorem allow-list is malformed")
    missing_allowed = allowed_names.difference(names)
    if missing_allowed:
        raise LibraryIdentityError(
            "model-v2 theorem(s) disappeared from the public library: "
            + ", ".join(sorted(missing_allowed))
        )

    canonical_sealed = {
        name: _canonical_closed_statement(statement)
        for name, statement in SEALED_LIBRARY_GOALS
    }
    specs_by_name = {spec.name: spec for spec in THEOREMS}
    for name, statement in canonical_sealed.items():
        actual = _canonical_closed_statement(specs_by_name[name].statement)
        if actual != statement:
            raise LibraryIdentityError(
                f"sealed theorem {name!r} no longer states its frozen target"
            )
    sealed_statements = frozenset(canonical_sealed.values())
    for spec in THEOREMS:
        if spec.name not in allowed_names:
            continue
        statement = _canonical_closed_statement(spec.statement)
        if statement in sealed_statements:
            raise LibraryIdentityError(
                f"allowed theorem {spec.name!r} aliases a sealed target"
            )
        unavailable = set(spec.dependencies).difference(allowed_names)
        if unavailable:
            raise LibraryIdentityError(
                f"allowed theorem {spec.name!r} depends outside model-v2: "
                + ", ".join(sorted(unavailable))
            )

    mod5_names = {spec.name for spec in MOD5_THEOREMS}
    report = _load_mod5_report()
    report_rows = _mod5_rows(report)
    if set(report_rows) != mod5_names:
        raise LibraryIdentityError(
            "modular-arithmetic source report does not identify the exact import"
        )
    public_rows = _public_catalog_rows(_load_public_catalog(), THEOREMS)

    records: list[LibraryIdentityRecord] = []
    for spec in THEOREMS:
        if spec.name not in allowed_names:
            continue
        checked = replay(spec.name)
        if checked.spec != spec:
            raise LibraryIdentityError(
                f"library replay returned the wrong spec for {spec.name!r}"
            )
        if not check((), checked.certificate, checked.formula):
            raise LibraryIdentityError(
                f"independent kernel rejected model-v2 theorem {spec.name!r}"
            )
        statement = _canonical_closed_statement(spec.statement)
        if checked.formula != _parse_closed_formula(spec.statement):
            raise LibraryIdentityError(
                f"library replay returned the wrong formula for {spec.name!r}"
            )
        cut_nodes, cut_depth = proof_metrics(checked.certificate)
        if checked.proof_nodes != cut_nodes:
            raise LibraryIdentityError(
                f"library replay reported inconsistent metrics for {spec.name!r}"
            )
        # The current 247-theorem ladder deliberately preserves dependency
        # sharing as self-contained Cut nodes.  Validate that representation
        # against the current catalog before deriving the historical model-v2
        # identity below.  This keeps the v3 authority and its checker path
        # completely independent of the compatibility projection.
        current_record = LibraryIdentityRecord(
            name=spec.name,
            statement=statement,
            dependencies=tuple(spec.dependencies),
            source_spec_sha256=_json_sha256(_source_spec_record(spec)),
            script_sha256=_json_sha256(list(spec.script)),
            certificate_sha256=hashlib.sha256(
                repr(checked.certificate).encode("utf-8")
            ).hexdigest(),
            proof_nodes=cut_nodes,
            proof_depth=cut_depth,
        )
        _validate_public_catalog_record(current_record, public_rows[spec.name])

        # Model-v2 was published before Cut sharing existed.  Its content
        # identity commits the fully inlined proof terms produced by the old
        # replay algorithm.  Erasing current Cut nodes and normalising the
        # resulting ordinary implication redexes reconstructs that exact
        # representation.  Dependency-free certificates were *not*
        # normalised by the historical replay and therefore remain unchanged.
        legacy_certificate = checked.certificate
        if spec.dependencies:
            legacy_certificate = normalise_cuts(
                erase_trusted_cuts(checked.certificate)
            )
        if not check((), legacy_certificate, checked.formula):
            raise LibraryIdentityError(
                "independent kernel rejected reconstructed historical "
                f"model-v2 theorem {spec.name!r}"
            )
        nodes, depth = proof_metrics(legacy_certificate)
        record = LibraryIdentityRecord(
            name=spec.name,
            statement=statement,
            dependencies=tuple(spec.dependencies),
            source_spec_sha256=_json_sha256(_source_spec_record(spec)),
            script_sha256=_json_sha256(list(spec.script)),
            certificate_sha256=hashlib.sha256(
                repr(legacy_certificate).encode("utf-8")
            ).hexdigest(),
            proof_nodes=nodes,
            proof_depth=depth,
        )
        if spec.name in mod5_names:
            _validate_mod5_record(record, report_rows[spec.name])
        records.append(record)

    if len(records) != EXPECTED_MODEL_V2_LIBRARY_COUNT:
        raise LibraryIdentityError(
            "model-v2 library must contain exactly "
            f"{EXPECTED_MODEL_V2_LIBRARY_COUNT} theorems, got {len(records)}"
        )
    return tuple(sorted(records, key=lambda item: item.name))


def _parse_closed_formula(source: str) -> object:
    """Parse a closed formula without exporting a kernel type at import time."""

    from peano_lab.kernel.formulas import parse_formula_with_names

    formula, free_names = parse_formula_with_names(source)
    if free_names:
        raise LibraryIdentityError(
            "model-v2 theorem statement is not closed; free variable(s): "
            + ", ".join(free_names)
        )
    return formula


def model_v2_library_identity_record() -> dict[str, object]:
    """Return a fresh versioned JSON identity document."""

    return {
        "format": LIBRARY_IDENTITY_FORMAT,
        "v": LIBRARY_IDENTITY_VERSION,
        "theorems": [
            record.to_record() for record in model_v2_library_identity()
        ],
    }


@lru_cache(maxsize=1)
def model_v2_library_identity_sha256() -> str:
    """Return the canonical JSON SHA-256 of the full identity document."""

    actual = _json_sha256(model_v2_library_identity_record())
    if actual != EXPECTED_MODEL_V2_LIBRARY_SHA256:
        raise LibraryIdentityError(
            "reconstructed model-v2 library identity differs from its "
            "published historical contract"
        )
    return actual


def clear_model_v2_library_identity_cache() -> None:
    """Clear only this module's immutable identity cache (primarily for tests)."""

    model_v2_library_identity_sha256.cache_clear()
    model_v2_library_identity.cache_clear()


__all__ = [
    "LIBRARY_IDENTITY_FORMAT",
    "LIBRARY_IDENTITY_VERSION",
    "EXPECTED_PUBLIC_LIBRARY_COUNT",
    "EXPECTED_PUBLIC_LIBRARY_PREFIX_SHA256",
    "EXPECTED_MODEL_V2_LIBRARY_COUNT",
    "EXPECTED_MODEL_V2_LIBRARY_SHA256",
    "MODEL_V2_LIBRARY_NAMES",
    "PUBLIC_LIBRARY_CATALOG",
    "SEALED_LIBRARY_GOALS",
    "SEALED_LIBRARY_NAMES",
    "LibraryIdentityError",
    "LibraryIdentityRecord",
    "model_v2_library_identity",
    "model_v2_library_identity_record",
    "model_v2_library_identity_sha256",
    "clear_model_v2_library_identity_cache",
    "sealed_library_closure",
]
