"""Adversarial acceptance tests for Hydra's isolated L0 documentation bundle.

The historical proof explorers are deliberately *not* inputs to this bundle.
These tests independently reconstruct the retained 384-row namespace and its
declared dependency graph, then exercise the bundle as a closed five-document
protocol.  Passing this file grants no owner, freeze, training, retrieval, or
evaluation authority.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
PY_ROOT = ROOT / "peano-lab" / "py"
for entry in (ROOT, PY_ROOT):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

import training.peano_hydra.library_documentation_bundle as bundle_module  # noqa: E402
from training.peano_hydra.library_documentation_bundle import (  # noqa: E402
    LibraryDocumentationBundleError,
    build_candidate_documentation_bundle,
    canonical_document_bytes,
    documentation_bundle_schema,
    documentation_bundle_schema_identity,
    load_documentation_bundle,
    validate_documentation_bundle,
)


SCHEMA_SOURCE = (
    ROOT / "training/peano_hydra/library-documentation-bundle-schema-v1.json"
)
ARTIFACT_DIRECTORY = (
    ROOT / "artifacts/peano-hydra/l0-documentation-candidate-v1"
)
REPLAY_MANIFEST = (
    ROOT / "artifacts/peano-hydra/l0-replay-candidate-v1/manifest.json"
)
CLI = ROOT / "scripts/build_peano_hydra_library_documentation_bundle.py"

DOCUMENT_FILES = (
    "schema.json",
    "explicit.json",
    "defined.json",
    "isolation-receipt.json",
    "manifest.json",
)
MANIFEST_MEMBER_FILES = DOCUMENT_FILES[:-1]
FORBIDDEN_THEOREM_FIELDS = {"closure", "dependents", "href", "scope", "tag"}
PA_TAG = re.compile(r"^PA[0-9A-Y]{4}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")

EXPECTED = {
    "changed_local_propositions": 624,
    "changed_statements": 321,
    "declared_dependency_edges": 1_038,
    "defined_local_characters": 25_733,
    "defined_statement_characters": 29_098,
    "definition_count": 40,
    "definition_occurrences": 2_027,
    "dependency_depth_maximum": 21,
    "dependency_level_count": 22,
    "expanded_local_characters": 148_105,
    "expanded_statement_characters": 224_948,
    "explicitly_referenced_dependency_edges": 1_035,
    "foundation_count": 55,
    "implicit_dependency_edges": 3,
    "local_proposition_count": 950,
    "reference_occurrences": 3_989,
    "tactic_head_count": 20,
    "tactic_line_count": 13_862,
    "tactic_text_characters": 399_210,
    "terminal_count": 100,
    "theorem_count": 384,
}

SCHEMA_SEMANTIC_SHA256 = (
    "30236aaaecc41104e7e193476f59a8b764d56fe86c63ca04c1561ad38645832d"
)
FINAL_ARTIFACT_PINS = {
    "schema.json": {
        "bytes": 29_324,
        "sha256": "a442e89ac312302dcee777b5741ca7f2d67e10f6ebcc996b8096fc6061c28a9c",
        "root_sha256": None,
    },
    "explicit.json": {
        "bytes": 6_334_632,
        "sha256": "f1c9f364db0cb7ae7f4c7fe065b1ef48d5522fc49711667479ec3dc4db723936",
        "root_sha256": "b7942fa5a866ff7cd8a38f30c93787ec0abd2948e69710651e4d3578e64377da",
    },
    "defined.json": {
        "bytes": 11_190_180,
        "sha256": "164b34dd0cad555baf2164ee3da114fb60a447bd667112481e7225097dd17cea",
        "root_sha256": "897fd5e4bedb44b63853e428ff5bc2e2c273e30a0c239450e0ec8f93d73fc61f",
    },
    "isolation-receipt.json": {
        "bytes": 3_729,
        "sha256": "8c8a6882d0d5a82552942fc0c3efe5a900244a9cad02c32b24cabe3d86a0eee6",
        "root_sha256": "64bdc2c52bcaf88d26382bbe514be4a442cc876b8df2a353c272587e1516d919",
    },
    "manifest.json": {
        "bytes": 7_930,
        "sha256": "5ded97c27b859cc4725362bc76aba89fac06c5f11843b50529b78050b19348bf",
        "root_sha256": "8f7ef8fcca69bc6f5f8b39c220293b8414a65fd81576c584f78e59da104d46a4",
    },
}

# H1.1b is an additive protocol.  These receipts make accidental resealing of
# the historical 557-row documentation surfaces visible in the same change.
HISTORICAL_ARTIFACTS = {
    "research/arithmetic-library/pa-proof-tags.json": (
        "84d741c7319cd14ac2f42dd3a131ae908f3ca56b421a1a3bb8c78f4e6f2f2052"
    ),
    "book/_static/pa-proof-explorer/manifest.json": (
        "a45a2a85b9fcb418a4117c38d3e5025add873431cb778466ee1a960488c7cd7d"
    ),
    "book/_static/pa-proof-explorer/api/corpus.json": (
        "95df7f7d096c41cc25e49217e4310451477ea5c45bf8624f67f41893693e43e1"
    ),
    "book/_static/pa-proof-explorer/defined/manifest.json": (
        "e2a9177ad57246d7a40609bd7474e0077ef1522334bdfd521e0b4a5c98432c90"
    ),
    "book/_static/pa-proof-explorer/defined/api/corpus.json": (
        "1e5de6a773d5283280909677509420c01afe34a6d4f6fe5dc202114b87b6433d"
    ),
    "training/peano_hydra/library-epoch-metadata-schema-v1.json": (
        "9867378c8802501d2120ad4d94a86378815cf90b003eafc92b164685da61c956"
    ),
    "artifacts/peano-hydra/library-epoch-metadata-candidate-v1.json": (
        "e719dd526d0aa07e2521fb2e499f2ee6810506d32a912298f11dbac60a2c0289"
    ),
    "artifacts/peano-hydra/library-epoch-metadata-candidate-v1-readiness.json": (
        "386be7eb475980a373122d769a496220319d34090463e0a3bc870cfece3e4c25"
    ),
}


def _compact_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha_json(value: object) -> str:
    return sha256(_compact_json_bytes(value)).hexdigest()


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_bytes())
    assert type(value) is dict
    return value


def _walk(value: object):
    yield value
    if type(value) is dict:
        for key, item in value.items():
            yield key
            yield from _walk(item)
    elif type(value) is list:
        for item in value:
            yield from _walk(item)


def _record_preimage(record: dict[str, object]) -> dict[str, object]:
    return {key: item for key, item in record.items() if key != "record_sha256"}


def _assert_record_hash(record: dict[str, object]) -> None:
    assert SHA256.fullmatch(str(record["record_sha256"]))
    assert record["record_sha256"] == _sha_json(_record_preimage(record))


def _assert_candidate_constants(document: dict[str, object]) -> None:
    assert document["status"] == "candidate"
    assert document["logic_mode"] == "intuitionistic"
    assert document["freeze_ready"] is False
    assert document["training_eligible"] is False
    assert document["retrieval_eligible"] is False
    assert document["evaluation_eligible"] is False


def _assert_exact_fields(
    schema: dict[str, object], shape: str, value: dict[str, object]
) -> None:
    assert set(value) == set(schema["object_shapes"][shape]["fields"])


def _literal_theorem_spec(
    *,
    name: str = "same",
    statement: str = "0 = 0",
    dependencies: tuple[str, ...] = (),
    script: tuple[str, ...] = ("refl",),
    summary: str = "The same retained theorem.",
) -> str:
    return (
        f"TheoremSpec({name!r}, {statement!r}, {dependencies!r}, "
        f"{script!r}, {summary!r})\n"
    )


def _reroot_document(document: dict[str, object]) -> dict[str, object]:
    """Recompute a document root after a hostile mutation.

    This helper intentionally trusts the document's own preimage format.  The
    production validator must still compare the fully rerooted value with the
    exact source-derived candidate.
    """

    result = deepcopy(document)
    preimage = result["root_preimage"]
    payload = deepcopy(preimage["payload"])
    body = {
        key: item
        for key, item in result.items()
        if key not in {"root_preimage", "root_sha256", "theorems", "definitions"}
    }
    ordered_key = "ordered_records"
    if "theorems" in result:
        payload.update(body)
        payload[ordered_key] = [
            {
                "index": row["index"],
                "name": row["name"],
                "record_sha256": row["record_sha256"],
            }
            for row in result["theorems"]
        ]
        if "definitions" in result:
            payload["definitions_root_sha256"] = _sha_json(
                [
                    [row["index"], row["id"], row["record_sha256"]]
                    for row in result["definitions"]
                ]
            )
    elif "definitions" in result:
        payload.update(body)
    else:
        payload.update(body)
    result["root_preimage"] = {
        "format": preimage["format"],
        "payload": payload,
        "v": preimage["v"],
    }
    result["root_sha256"] = _sha_json(result["root_preimage"])
    return result


def _rebind_whole_bundle(
    value: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
    """Rebind every downstream receipt after a hostile explicit-row edit."""

    result = deepcopy(value)
    explicit = result["explicit.json"]
    explicit["theorems"] = [
        {**row, "record_sha256": _sha_json(_record_preimage(row))}
        for row in explicit["theorems"]
    ]
    explicit["dependency_receipt"]["ordered_record_root_sha256"] = _sha_json(
        [
            [row["index"], row["name"], row["record_sha256"]]
            for row in explicit["theorems"]
        ]
    )
    explicit = _reroot_document(explicit)
    result["explicit.json"] = explicit

    defined = result["defined.json"]
    defined["explicit_root_sha256"] = explicit["root_sha256"]
    for explicit_row, defined_row in zip(
        explicit["theorems"], defined["theorems"], strict=True
    ):
        defined_row["explicit_record_sha256"] = explicit_row["record_sha256"]
        defined_row["record_sha256"] = _sha_json(_record_preimage(defined_row))
    defined["aggregate"]["ordered_record_root_sha256"] = _sha_json(
        [
            [row["index"], row["name"], row["record_sha256"]]
            for row in defined["theorems"]
        ]
    )
    defined = _reroot_document(defined)
    result["defined.json"] = defined

    isolation = result["isolation-receipt.json"]
    isolation["roots"].update(
        {
            "defined_document_root_sha256": defined["root_sha256"],
            "defined_ordered_record_root_sha256": defined["aggregate"][
                "ordered_record_root_sha256"
            ],
            "dependency_edge_root_sha256": explicit["dependency_receipt"][
                "edge_root_sha256"
            ],
            "dependency_node_root_sha256": explicit["dependency_receipt"][
                "node_root_sha256"
            ],
            "explicit_document_root_sha256": explicit["root_sha256"],
            "explicit_ordered_record_root_sha256": explicit["dependency_receipt"][
                "ordered_record_root_sha256"
            ],
        }
    )
    isolation = _reroot_document(isolation)
    result["isolation-receipt.json"] = isolation

    manifest = result["manifest.json"]
    members = {
        filename: result[filename] for filename in MANIFEST_MEMBER_FILES
    }
    manifest["files"] = [
        {
            "bytes": len(canonical_document_bytes(members[filename])),
            "name": filename,
            "sha256": sha256(
                canonical_document_bytes(members[filename])
            ).hexdigest(),
        }
        for filename in MANIFEST_MEMBER_FILES
    ]
    result["manifest.json"] = _reroot_document(manifest)
    return result


@pytest.fixture(scope="module")
def bundle() -> dict[str, dict[str, object]]:
    built = build_candidate_documentation_bundle()
    assert type(built) is dict
    assert set(built) == set(DOCUMENT_FILES)
    assert all(type(value) is dict for value in built.values())
    return built


@pytest.fixture(scope="module")
def replay() -> dict[str, object]:
    return _load(REPLAY_MANIFEST)


def test_schema_is_canonical_closed_exact_and_candidate_only() -> None:
    schema = documentation_bundle_schema()
    identity = documentation_bundle_schema_identity()
    raw = SCHEMA_SOURCE.read_bytes()
    assert raw == canonical_document_bytes(schema, limit=1_000_000)
    assert identity == {
        "artifact_sha256": sha256(raw).hexdigest(),
        "format": schema["format"],
        "id": schema["id"],
        "sha256": _sha_json(schema),
        "v": schema["v"],
    }
    assert schema["additional_fields_policy"] == (
        "forbidden-at-every-schema-owned-object"
    )
    assert schema["constants"] == {
        "evaluation_eligible": False,
        "freeze_ready": False,
        "logic_mode": "intuitionistic",
        "retrieval_eligible": False,
        "status": "candidate",
        "training_eligible": False,
    }
    assert schema["expected_aggregates"] == EXPECTED
    assert schema["files"] == {
        "defined": "defined.json",
        "explicit": "explicit.json",
        "isolation_receipt": "isolation-receipt.json",
        "manifest": "manifest.json",
        "schema": "schema.json",
    }
    fixed = schema["fixed_inputs"]
    assert fixed["replay_manifest"] == {
        "artifact_path": "artifacts/peano-hydra/l0-replay-candidate-v1/manifest.json",
        "artifact_sha256": bundle_module.REPLAY_MANIFEST_ARTIFACT_SHA256,
        "manifest_root_sha256": bundle_module.REPLAY_MANIFEST_ROOT_SHA256,
        "replay_root_sha256": bundle_module.REPLAY_ROOT_SHA256,
    }
    assert fixed["replay_catalog"]["artifact_sha256"] == (
        bundle_module.CATALOG_ARTIFACT_SHA256
    )
    assert fixed["replay_catalog"]["catalog_sha256"] == (
        bundle_module.CATALOG_SEMANTIC_SHA256
    )
    assert fixed["defined_syntax_registry"]["source_sha256"] == (
        bundle_module.DEFINED_SYNTAX_SOURCE_SHA256
    )
    assert fixed["defined_edition_compactor"]["source_sha256"] == (
        bundle_module.DEFINED_COMPACTOR_SOURCE_SHA256
    )
    shapes = schema["object_shapes"]
    for required in (
        "explicit_document",
        "explicit_theorem",
        "command_line",
        "reference_span",
        "defined_document",
        "defined_theorem",
        "definition",
        "formula_compaction",
        "manifest",
        "isolation_receipt",
    ):
        assert required in shapes
        assert type(shapes[required].get("fields")) is list
        assert len(shapes[required]["fields"]) == len(
            set(shapes[required]["fields"])
        )
    assert "cannot freeze" in schema["claim_boundary"]["authority"]
    assert "no independent kernel replay" in schema["claim_boundary"]["kernel"]


def test_final_schema_and_five_retained_transport_identities_are_hard_pinned(
    bundle: dict[str, dict[str, object]],
) -> None:
    identity = documentation_bundle_schema_identity()
    assert identity["sha256"] == SCHEMA_SEMANTIC_SHA256
    assert identity["artifact_sha256"] == FINAL_ARTIFACT_PINS["schema.json"][
        "sha256"
    ]
    assert bundle_module.SCHEMA_SHA256 == SCHEMA_SEMANTIC_SHA256

    for filename in DOCUMENT_FILES:
        raw = canonical_document_bytes(bundle[filename])
        retained = (ARTIFACT_DIRECTORY / filename).read_bytes()
        expected = FINAL_ARTIFACT_PINS[filename]
        assert len(raw) == len(retained) == expected["bytes"]
        assert sha256(raw).hexdigest() == sha256(retained).hexdigest() == expected[
            "sha256"
        ]
        if expected["root_sha256"] is None:
            assert "root_sha256" not in bundle[filename]
        else:
            assert bundle[filename]["root_sha256"] == expected["root_sha256"]

    # The retained manifest's transport SHA and semantic root are distinct
    # contracts and must never be substituted for one another.
    assert FINAL_ARTIFACT_PINS["manifest.json"]["sha256"] != (
        FINAL_ARTIFACT_PINS["manifest.json"]["root_sha256"]
    )


def test_every_emitted_schema_owned_object_has_the_exact_declared_shape(
    bundle: dict[str, dict[str, object]],
) -> None:
    schema = documentation_bundle_schema()
    explicit = bundle["explicit.json"]
    defined = bundle["defined.json"]
    isolation = bundle["isolation-receipt.json"]
    manifest = bundle["manifest.json"]

    for shape, document in (
        ("explicit_document", explicit),
        ("defined_document", defined),
        ("isolation_receipt", isolation),
        ("manifest", manifest),
    ):
        _assert_exact_fields(schema, shape, document)
        _assert_exact_fields(schema, "root_preimage", document["root_preimage"])
    for kind, document in (
        ("explicit", explicit),
        ("defined", defined),
        ("isolation", isolation),
        ("manifest", manifest),
    ):
        assert set(document["root_preimage"]["payload"]) == set(
            schema["root_preimage_shapes"][kind]
        )

    _assert_exact_fields(schema, "explicit_aggregate", explicit["aggregate"])
    _assert_exact_fields(schema, "dependency_receipt", explicit["dependency_receipt"])
    _assert_exact_fields(schema, "replay_pack_identity", explicit["replay_pack"])
    _assert_exact_fields(schema, "repository_identity", explicit["repository"])
    _assert_exact_fields(
        schema, "source_catalog_identity", explicit["source_catalog"]
    )

    for row in explicit["theorems"]:
        _assert_exact_fields(schema, "explicit_theorem", row)
        _assert_exact_fields(schema, "source_locator", row["source"])
        for line in row["command_lines"]:
            _assert_exact_fields(schema, "command_line", line)
            _assert_exact_fields(schema, "tactic_span", line["tactic"])
            for reference in line["references"]:
                _assert_exact_fields(schema, "reference_span", reference)

    for definition in defined["definitions"]:
        _assert_exact_fields(schema, "definition", definition)
        _assert_exact_fields(schema, "definition_source_locator", definition["source"])
    for row in defined["theorems"]:
        _assert_exact_fields(schema, "defined_theorem", row)
        for use in row["definition_uses"]:
            _assert_exact_fields(schema, "definition_use", use)
        _assert_compaction_shapes(schema, row["statement"])
        for line in row["script"]:
            _assert_exact_fields(schema, "defined_tactic_line", line)
            for part in line["parts"]:
                _assert_exact_fields(
                    schema,
                    "surface_part_definition"
                    if part["kind"] == "definition"
                    else "surface_part_text",
                    part,
                )
            if line["proposition"] is not None:
                _assert_compaction_shapes(schema, line["proposition"])

    _assert_exact_fields(schema, "defined_aggregate", defined["aggregate"])
    _assert_exact_fields(schema, "compactor_identity", defined["compactor"])
    for dependency in defined["compactor"]["runtime_dependencies"]:
        _assert_exact_fields(schema, "runtime_dependency", dependency)
    _assert_exact_fields(schema, "registry_identity", defined["registry"])
    _assert_exact_fields(schema, "replay_pack_identity", defined["replay_pack"])

    _assert_exact_fields(schema, "isolation_checks", isolation["checks"])
    _assert_exact_fields(schema, "isolation_counts", isolation["counts"])
    _assert_exact_fields(schema, "isolation_roots", isolation["roots"])
    _assert_exact_fields(schema, "manifest_aggregate", manifest["aggregate"])
    _assert_exact_fields(schema, "schema_identity", manifest["schema"])
    _assert_exact_fields(schema, "source_bindings", manifest["source_bindings"])
    _assert_exact_fields(
        schema, "compactor_identity", manifest["source_bindings"]["compactor"]
    )
    for dependency in manifest["source_bindings"]["compactor"][
        "runtime_dependencies"
    ]:
        _assert_exact_fields(schema, "runtime_dependency", dependency)
    _assert_exact_fields(
        schema, "registry_identity", manifest["source_bindings"]["registry"]
    )
    _assert_exact_fields(
        schema,
        "source_catalog_identity",
        manifest["source_bindings"]["replay_catalog"],
    )
    _assert_exact_fields(
        schema,
        "replay_pack_identity",
        manifest["source_bindings"]["replay_manifest"],
    )
    _assert_exact_fields(
        schema,
        "repository_identity",
        manifest["source_bindings"]["repository"],
    )
    for receipt in manifest["files"]:
        _assert_exact_fields(schema, "file_receipt", receipt)


def _assert_compaction_shapes(
    schema: dict[str, object], value: dict[str, object]
) -> None:
    _assert_exact_fields(schema, "formula_compaction", value)
    _assert_exact_fields(schema, "compaction_receipt", value["receipt"])
    for use in value["receipt"]["definition_uses"]:
        _assert_exact_fields(schema, "definition_use", use)
    for part in value["parts"]:
        _assert_exact_fields(
            schema,
            "surface_part_definition"
            if part["kind"] == "definition"
            else "surface_part_text",
            part,
        )


def test_two_builds_are_deterministic_and_match_retained_artifacts(
    bundle: dict[str, dict[str, object]],
) -> None:
    second = build_candidate_documentation_bundle()
    assert second == bundle
    for filename in DOCUMENT_FILES:
        first_raw = canonical_document_bytes(bundle[filename])
        second_raw = canonical_document_bytes(second[filename])
        assert first_raw == second_raw
        retained = ARTIFACT_DIRECTORY / filename
        assert retained.is_file()
        assert retained.read_bytes() == first_raw
    assert validate_documentation_bundle(bundle) == bundle


@pytest.mark.parametrize(
    "value",
    (
        {"value": 1.0},
        {"value": float("nan")},
        {"value": 9_007_199_254_740_992},
        {1: "non-text-key"},
    ),
)
def test_canonical_transport_rejects_values_outside_strict_json(value: object) -> None:
    with pytest.raises(LibraryDocumentationBundleError):
        canonical_document_bytes(value)


def test_canonical_transport_rejects_cycles_and_nonexact_limits() -> None:
    cycle: list[object] = []
    cycle.append(cycle)
    with pytest.raises(LibraryDocumentationBundleError):
        canonical_document_bytes(cycle)
    for limit in (True, 1.0, 0, -1):
        with pytest.raises(TypeError):
            canonical_document_bytes({}, limit=limit)


def test_manifest_binds_exact_file_set_bytes_roots_and_source_inputs(
    bundle: dict[str, dict[str, object]],
) -> None:
    manifest = bundle["manifest.json"]
    _assert_candidate_constants(manifest)
    assert [row["name"] for row in manifest["files"]] == list(
        MANIFEST_MEMBER_FILES
    )
    for receipt in manifest["files"]:
        name = receipt["name"]
        raw = canonical_document_bytes(bundle[name])
        assert receipt == {
            "bytes": len(raw),
            "name": name,
            "sha256": sha256(raw).hexdigest(),
        }
    assert manifest["schema"] == documentation_bundle_schema_identity()
    assert manifest["source_bindings"]["replay_manifest"][
        "artifact_sha256"
    ] == bundle_module.REPLAY_MANIFEST_ARTIFACT_SHA256
    assert manifest["source_bindings"]["replay_manifest"][
        "manifest_root_sha256"
    ] == bundle_module.REPLAY_MANIFEST_ROOT_SHA256
    assert manifest["source_bindings"]["replay_manifest"][
        "replay_root_sha256"
    ] == bundle_module.REPLAY_ROOT_SHA256
    assert manifest["aggregate"] == {
        "declared_dependency_edges": EXPECTED["declared_dependency_edges"],
        "definition_count": EXPECTED["definition_count"],
        "theorem_count": EXPECTED["theorem_count"],
    }
    assert manifest["source_bindings"]["compactor"] == bundle["defined.json"][
        "compactor"
    ]
    assert manifest["source_bindings"]["registry"] == bundle["defined.json"][
        "registry"
    ]
    assert manifest["source_bindings"]["replay_manifest"] == bundle["explicit.json"][
        "replay_pack"
    ] == bundle["defined.json"]["replay_pack"]
    assert manifest["source_bindings"]["replay_catalog"] == bundle[
        "explicit.json"
    ]["source_catalog"]
    assert manifest["source_bindings"]["repository"] == bundle["explicit.json"][
        "repository"
    ]
    assert manifest["root_preimage"]["payload"] == {
        key: value
        for key, value in manifest.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    assert manifest["root_sha256"] == _sha_json(manifest["root_preimage"])


def test_explicit_rows_are_an_exact_fresh_zip_not_a_legacy_filter(
    bundle: dict[str, dict[str, object]], replay: dict[str, object]
) -> None:
    from peano_lab.library.theorems import THEOREMS

    explicit = bundle["explicit.json"]
    rows = explicit["theorems"]
    replay_rows = replay["theorems"]
    assert explicit["theorem_count"] == len(rows) == len(replay_rows) == len(
        THEOREMS
    ) == 384
    assert [row["index"] for row in rows] == list(range(384))
    assert [row["name"] for row in rows] == [
        row["name"] for row in replay_rows
    ] == [spec.name for spec in THEOREMS]

    for index, (row, retained, spec) in enumerate(
        zip(rows, replay_rows, THEOREMS, strict=True)
    ):
        _assert_record_hash(row)
        assert row["index"] == index
        assert row["name"] == retained["name"] == spec.name
        assert row["catalog_layer"] == retained["layer"]
        assert row["formula_sha256"] == retained["formula_sha256"]
        assert row["statement_source"] == retained["statement_source"] == spec.statement
        assert row["statement_source_sha256"] == retained[
            "statement_source_sha256"
        ]
        assert row["statement_canonical"] == retained["statement_canonical"]
        assert row["statement_canonical_sha256"] == retained[
            "statement_canonical_sha256"
        ]
        assert row["declared_dependencies"] == retained[
            "declared_dependencies"
        ] == list(spec.dependencies)
        assert row["script_sha256"] == retained["script_sha256"]
        assert row["summary"] == retained["summary"] == spec.summary
        assert row["summary_sha256"] == sha256(spec.summary.encode()).hexdigest()
        assert row["minimality_claim"] is False
        assert not (FORBIDDEN_THEOREM_FIELDS & set(row))
        source = row["source"]
        source_path = Path(source["path"])
        assert not source_path.is_absolute() and ".." not in source_path.parts
        source_bytes = (ROOT / source_path).read_bytes()
        assert source["file_sha256"] == sha256(source_bytes).hexdigest()
        assert source["kind"] in {"declaration", "generated-factory"}
        assert type(source["line"]) is int and 1 <= source["line"] <= len(
            source_bytes.splitlines()
        )


def test_identical_full_literal_duplicate_uses_first_locator_deterministically(
    tmp_path: Path,
) -> None:
    source = tmp_path / "library.py"
    declaration = _literal_theorem_spec()
    raw = (declaration + "\n" + declaration).encode()
    source.write_bytes(raw)
    source_rows = [{"path": source.name, "sha256": sha256(raw).hexdigest()}]

    first = bundle_module._finite_source_locators(
        source_rows, root=tmp_path, theorem_names={"same"}
    )
    second = bundle_module._finite_source_locators(
        source_rows, root=tmp_path, theorem_names={"same"}
    )
    assert first == second == {
        "same": {
            "file_sha256": sha256(raw).hexdigest(),
            "kind": "declaration",
            "line": 1,
            "path": "library.py",
        }
    }


@pytest.mark.parametrize(
    "changed",
    (
        {"statement": "S 0 = S 0"},
        {"dependencies": ("zero_add",)},
        {"script": ("symm", "refl")},
        {"summary": "A conflicting theorem description."},
    ),
    ids=("statement", "dependencies", "script", "summary"),
)
def test_same_name_different_full_literal_payload_fails_closed(
    tmp_path: Path, changed: dict[str, object]
) -> None:
    source = tmp_path / "library.py"
    raw = (_literal_theorem_spec() + _literal_theorem_spec(**changed)).encode()
    source.write_bytes(raw)
    source_rows = [{"path": source.name, "sha256": sha256(raw).hexdigest()}]

    with pytest.raises(
        LibraryDocumentationBundleError,
        match="conflicting pinned source declarations",
    ):
        bundle_module._finite_source_locators(
            source_rows, root=tmp_path, theorem_names={"same"}
        )


def test_builder_has_no_runtime_or_source_dependency_on_legacy_557_surfaces(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import peano_lab.library.defined_edition as defined_edition
    import peano_lab.library.quadratic_reciprocity_stack_runtime as qr_runtime

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("legacy documentation/candidate builder was called")

    monkeypatch.setattr(defined_edition, "defined_library_edition", forbidden)
    monkeypatch.setattr(defined_edition, "build_defined_edition", forbidden)
    monkeypatch.setattr(qr_runtime, "quadratic_reciprocity_stack", forbidden)
    rebuilt = build_candidate_documentation_bundle()
    assert len(rebuilt["explicit.json"]["theorems"]) == 384

    source = Path(bundle_module.__file__).read_text(encoding="utf-8")
    for forbidden_text in (
        "pa-proof-explorer",
        "pa-proof-tags",
        "quadratic_reciprocity_stack",
        "defined_library_edition(",
        "build_defined_edition(",
    ):
        assert forbidden_text not in source


def test_fresh_process_bundle_build_does_not_import_candidate_factories() -> None:
    program = r'''import json
import sys

from training.peano_hydra.library_documentation_bundle import (
    build_candidate_documentation_bundle,
)

built = build_candidate_documentation_bundle()
assert built["explicit.json"]["theorem_count"] == 384
loaded_before_legacy_request = sorted(
    name
    for name in sys.modules
    if name in {
        "peano_lab.library.quadratic_reciprocity_stack",
        "peano_lab.library.quadratic_reciprocity_stack_runtime",
    }
    or (
        name.startswith("peano_lab.library.")
        and name.rsplit(".", 1)[-1].endswith("_candidate")
    )
)
assert loaded_before_legacy_request == []

# Lazy isolation must preserve the old explicitly requested 557-row edition.
from peano_lab.library.defined_edition import defined_library_edition
edition = defined_library_edition()
assert len(edition.records) == 557
assert edition.metrics.theorem_count == 557
assert edition.metrics.public_theorem_count == 240
assert edition.metrics.candidate_theorem_count == 317
print(json.dumps({"loaded_before": loaded_before_legacy_request, "legacy": 557}))
'''
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(PY_ROOT), str(ROOT), environment.get("PYTHONPATH", "")]
    )
    completed = subprocess.run(
        [sys.executable, "-c", program],
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    assert json.loads(completed.stdout) == {"legacy": 557, "loaded_before": []}


@pytest.mark.parametrize(
    "constant",
    (
        "REPLAY_MANIFEST_ARTIFACT_SHA256",
        "CATALOG_ARTIFACT_SHA256",
        "DEFINED_SYNTAX_SOURCE_SHA256",
        "DEFINED_COMPACTOR_SOURCE_SHA256",
    ),
)
def test_builder_rejects_every_representative_stale_fixed_input_pin(
    monkeypatch: pytest.MonkeyPatch, constant: str
) -> None:
    monkeypatch.setattr(bundle_module, constant, "0" * 64)
    with pytest.raises(LibraryDocumentationBundleError, match="drifted"):
        build_candidate_documentation_bundle()


def test_dependency_graph_and_explicit_command_receipts_are_exact(
    bundle: dict[str, dict[str, object]], replay: dict[str, object]
) -> None:
    rows = bundle["explicit.json"]["theorems"]
    retained_by_name = {row["name"]: row for row in replay["theorems"]}
    rank = {row["name"]: index for index, row in enumerate(rows)}
    depths: dict[str, int] = {}
    edge_count = 0
    referenced_edges: set[tuple[str, str]] = set()
    reference_count = 0
    tactic_heads: set[str] = set()
    line_count = 0
    text_characters = 0
    dependents = {row["name"]: [] for row in rows}
    dependency_pairs: list[list[str]] = []
    node_pairs: list[list[object]] = []

    for row in rows:
        name = row["name"]
        dependencies = row["declared_dependencies"]
        node_pairs.append([name, dependencies])
        assert len(dependencies) == len(set(dependencies))
        assert all(dependency in rank and rank[dependency] < rank[name] for dependency in dependencies)
        for dependency in dependencies:
            dependents[dependency].append(name)
            dependency_pairs.append([dependency, name])
        edge_count += len(dependencies)
        depth = 0 if not dependencies else 1 + max(depths[item] for item in dependencies)
        depths[name] = depth
        assert row["dependency_depth"] == depth

        retained_script = retained_by_name[name]["script"]
        lines = row["command_lines"]
        assert len(lines) == len(retained_script)
        for index, (line, text) in enumerate(zip(lines, retained_script, strict=True)):
            assert set(line) == {
                "index", "line", "references", "sha256", "tactic", "text"
            }
            assert line["index"] == index
            assert line["line"] == index + 1
            assert line["text"] == text
            assert line["sha256"] == sha256(text.encode()).hexdigest()
            tactic = line["tactic"]
            assert set(tactic) == {"end", "name", "start"}
            assert type(tactic["start"]) is type(tactic["end"]) is int
            assert 0 <= tactic["start"] < tactic["end"] <= len(text)
            assert text[tactic["start"] : tactic["end"]] == tactic["name"]
            tactic_heads.add(tactic["name"])
            previous_end = 0
            for reference in line["references"]:
                assert set(reference) == {"end", "kind", "name", "start"}
                left, right = reference["start"], reference["end"]
                assert type(left) is type(right) is int
                assert previous_end <= left < right <= len(text)
                previous_end = right
                assert text[left:right] == reference["name"]
                if reference["kind"] == "theorem":
                    assert reference["name"] in dependencies
                    referenced_edges.add((reference["name"], name))
                    reference_count += 1
                else:
                    assert reference["kind"] == "axiom"
                    assert reference["name"] in {f"PA{i}" for i in range(1, 7)}
            line_count += 1
            text_characters += len(text)

    terminals = [name for name, values in dependents.items() if not values]
    assert edge_count == EXPECTED["declared_dependency_edges"]
    assert len(referenced_edges) == EXPECTED[
        "explicitly_referenced_dependency_edges"
    ]
    assert edge_count - len(referenced_edges) == EXPECTED["implicit_dependency_edges"]
    assert reference_count == EXPECTED["reference_occurrences"]
    assert line_count == EXPECTED["tactic_line_count"]
    assert text_characters == EXPECTED["tactic_text_characters"]
    assert len(tactic_heads) == EXPECTED["tactic_head_count"]
    assert max(depths.values()) == EXPECTED["dependency_depth_maximum"]
    assert len(set(depths.values())) == EXPECTED["dependency_level_count"]
    assert sum(not row["declared_dependencies"] for row in rows) == EXPECTED[
        "foundation_count"
    ]
    assert len(terminals) == EXPECTED["terminal_count"]
    assert bundle["explicit.json"]["aggregate"] == {
        "declared_dependency_edges": edge_count,
        "dependency_depth_maximum": max(depths.values()),
        "dependency_level_count": len(set(depths.values())),
        "explicitly_referenced_dependency_edges": len(referenced_edges),
        "foundation_count": sum(not row["declared_dependencies"] for row in rows),
        "implicit_dependency_edges": edge_count - len(referenced_edges),
        "reference_occurrences": reference_count,
        "tactic_head_count": len(tactic_heads),
        "tactic_heads": sorted(tactic_heads),
        "tactic_line_count": line_count,
        "tactic_text_characters": text_characters,
        "terminal_count": len(terminals),
        "theorem_count": len(rows),
    }
    assert bundle["explicit.json"]["dependency_receipt"] == {
        "edge_root_sha256": _sha_json(dependency_pairs),
        "node_root_sha256": _sha_json(node_pairs),
        "orientation": "dependency-to-dependent",
        "ordered_record_root_sha256": _sha_json(
            [
                [row["index"], row["name"], row["record_sha256"]]
                for row in rows
            ]
        ),
    }
    explicit = bundle["explicit.json"]
    assert explicit["root_preimage"]["payload"] == {
        **{
            key: value
            for key, value in explicit.items()
            if key not in {"root_preimage", "root_sha256", "theorems"}
        },
        "ordered_records": [
            {
                "index": row["index"],
                "name": row["name"],
                "record_sha256": row["record_sha256"],
            }
            for row in rows
        ],
    }
    assert explicit["root_sha256"] == _sha_json(explicit["root_preimage"])


def test_defined_rows_freshly_compact_all_and_only_explicit_rows(
    bundle: dict[str, dict[str, object]],
) -> None:
    from peano_lab.library.defined_syntax import (
        ALL_DEFINITIONS,
        DEFINITIONS,
        DEFINED_SYNTAX_REGISTRY_SHA256,
    )

    explicit = bundle["explicit.json"]
    defined = bundle["defined.json"]
    _assert_candidate_constants(explicit)
    _assert_candidate_constants(defined)
    explicit_rows = explicit["theorems"]
    rows = defined["theorems"]
    assert defined["theorem_count"] == len(rows) == len(explicit_rows) == 384
    assert [row["index"] for row in rows] == list(range(384))
    assert [row["name"] for row in rows] == [
        row["name"] for row in explicit_rows
    ]
    assert len(defined["definitions"]) == EXPECTED["definition_count"]
    # The parser registry deliberately binds three adjacent authoring-only
    # definitions too; this retained surface serializes and may use only 40.
    assert len(DEFINITIONS) == 40
    assert len(ALL_DEFINITIONS) == 43
    assert defined["registry"] == {
        "id": "peano-lab.defined-predicates",
        "parser_registry_definition_count": 43,
        "parser_registry_semantic_sha256": DEFINED_SYNTAX_REGISTRY_SHA256,
        "path": "peano-lab/py/peano_lab/library/defined_syntax.py",
        "serialized_definition_count": 40,
        "source_sha256": bundle_module.DEFINED_SYNTAX_SOURCE_SHA256,
        "v": 2,
    }

    definition_ids: list[str] = []
    definition_names: list[str] = []
    for index, definition in enumerate(defined["definitions"]):
        _assert_record_hash(definition)
        assert definition["index"] == index
        assert re.fullmatch(r"PD[0-9]{4}", definition["id"])
        assert definition["id"] not in definition_ids
        assert definition["name"] not in definition_names
        assert all(item in definition_ids for item in definition["conceptual_dependencies"])
        assert definition["expansion_sha256"] == sha256(
            definition["expansion"].encode()
        ).hexdigest()
        source = definition["source"]
        source_path = Path(source["path"])
        assert not source_path.is_absolute() and ".." not in source_path.parts
        source_bytes = (ROOT / source_path).read_bytes()
        assert source["file_sha256"] == sha256(source_bytes).hexdigest()
        assert type(source["line"]) is int and 1 <= source["line"] <= len(
            source_bytes.splitlines()
        )
        definition_ids.append(definition["id"])
        definition_names.append(definition["name"])

    explicit_by_name = {row["name"]: row for row in explicit_rows}
    for row in rows:
        _assert_record_hash(row)
        assert row["minimality_claim"] is False
        assert not (FORBIDDEN_THEOREM_FIELDS & set(row))
        explicit_row = explicit_by_name[row["name"]]
        assert row["explicit_record_sha256"] == explicit_row["record_sha256"]
        assert all(use["definition"] in definition_ids for use in row["definition_uses"])
        statement = row["statement"]
        _assert_formula_compaction(statement, definition_ids, definition_names)
        assert statement["expanded_source"] == explicit_row["statement_source"]
        assert len(row["script"]) == len(explicit_row["command_lines"])
        for line, explicit_line in zip(
            row["script"], explicit_row["command_lines"], strict=True
        ):
            assert line["index"] == explicit_line["index"]
            assert line["line"] == explicit_line["line"]
            assert line["expanded_command"] == explicit_line["text"]
            assert line["expanded_command_sha256"] == explicit_line["sha256"]
            assert line["defined_command_sha256"] == sha256(
                line["defined_command"].encode()
            ).hexdigest()
            assert "".join(part["text"] for part in line["parts"]) == line[
                "defined_command"
            ]
            assert line["tactic"] == explicit_line["tactic"]["name"]
            assert all(
                part.get("definition") in definition_ids
                for part in line["parts"]
                if part["kind"] == "definition"
            )
            assert "tag" not in line and "href" not in line
            if line["proposition"] is not None:
                _assert_formula_compaction(
                    line["proposition"], definition_ids, definition_names
                )
    statement_receipts = [row["statement"]["receipt"] for row in rows]
    local_compactions = [
        line["proposition"]
        for row in rows
        for line in row["script"]
        if line["proposition"] is not None
    ]
    assert sum(bool(item["definition_uses"]) for item in statement_receipts) == (
        EXPECTED["changed_statements"]
    )
    assert len(local_compactions) == EXPECTED["local_proposition_count"]
    assert sum(
        bool(item["receipt"]["definition_uses"]) for item in local_compactions
    ) == EXPECTED["changed_local_propositions"]
    assert sum(len(row["statement"]["expanded_source"]) for row in rows) == (
        EXPECTED["expanded_statement_characters"]
    )
    assert sum(len(row["statement"]["defined_source"]) for row in rows) == (
        EXPECTED["defined_statement_characters"]
    )
    assert sum(len(item["expanded_source"]) for item in local_compactions) == (
        EXPECTED["expanded_local_characters"]
    )
    assert sum(len(item["defined_source"]) for item in local_compactions) == (
        EXPECTED["defined_local_characters"]
    )
    assert sum(
        use["occurrences"] for row in rows for use in row["definition_uses"]
    ) == EXPECTED["definition_occurrences"]
    assert defined["aggregate"] == {
        "changed_local_propositions": EXPECTED["changed_local_propositions"],
        "changed_statements": EXPECTED["changed_statements"],
        "defined_local_characters": EXPECTED["defined_local_characters"],
        "defined_statement_characters": EXPECTED[
            "defined_statement_characters"
        ],
        "definition_count": EXPECTED["definition_count"],
        "definition_occurrences": EXPECTED["definition_occurrences"],
        "expanded_local_characters": EXPECTED["expanded_local_characters"],
        "expanded_statement_characters": EXPECTED[
            "expanded_statement_characters"
        ],
        "local_proposition_count": EXPECTED["local_proposition_count"],
        "ordered_record_root_sha256": _sha_json(
            [
                [row["index"], row["name"], row["record_sha256"]]
                for row in rows
            ]
        ),
        "theorem_count": EXPECTED["theorem_count"],
    }
    assert defined["explicit_root_sha256"] == explicit["root_sha256"]
    assert defined["root_preimage"]["payload"] == {
        **{
            key: value
            for key, value in defined.items()
            if key
            not in {"definitions", "root_preimage", "root_sha256", "theorems"}
        },
        "definitions_root_sha256": _sha_json(
            [
                [row["index"], row["id"], row["record_sha256"]]
                for row in defined["definitions"]
            ]
        ),
        "ordered_records": [
            {
                "index": row["index"],
                "name": row["name"],
                "record_sha256": row["record_sha256"],
            }
            for row in rows
        ],
    }
    assert defined["root_sha256"] == _sha_json(defined["root_preimage"])


def _assert_formula_compaction(
    value: dict[str, object],
    definition_ids: list[str],
    definition_names: list[str],
) -> None:
    from peano_lab.kernel.formulas import parse_formula_with_names, pretty_formula
    from peano_lab.library.defined_syntax import parse_defined_formula_in_context

    assert set(value) == {"defined_source", "expanded_source", "parts", "receipt"}
    assert "".join(part["text"] for part in value["parts"]) == value["defined_source"]
    for part in value["parts"]:
        if part["kind"] == "definition":
            assert set(part) == {"definition", "kind", "text"}
            assert part["definition"] in definition_ids
        else:
            assert part["kind"] == "text" and set(part) == {"kind", "text"}
    receipt = value["receipt"]
    assert receipt["exact_ast_equivalence"] is True
    expanded_formula, free_names = parse_formula_with_names(value["expanded_source"])
    expanded_again = parse_defined_formula_in_context(
        value["defined_source"], list(free_names), expansion_budget=4_000_000
    )
    assert expanded_again == expanded_formula
    assert receipt["free_names"] == list(free_names)
    assert receipt["canonical_expansion_sha256"] == sha256(
        pretty_formula(expanded_again, list(free_names)).encode()
    ).hexdigest()
    assert receipt["expanded_source_sha256"] == sha256(
        value["expanded_source"].encode()
    ).hexdigest()
    assert receipt["defined_source_sha256"] == sha256(
        value["defined_source"].encode()
    ).hexdigest()
    assert receipt["expanded_characters"] == len(value["expanded_source"])
    assert receipt["defined_characters"] == len(value["defined_source"])
    seen: set[str] = set()
    rank = {item: index for index, item in enumerate(definition_ids)}
    for use in receipt["definition_uses"]:
        assert set(use) == {"definition", "name", "occurrences"}
        assert use["definition"] in definition_ids and use["definition"] not in seen
        assert use["name"] == definition_names[rank[use["definition"]]]
        assert type(use["occurrences"]) is int and use["occurrences"] >= 1
        seen.add(use["definition"])
    assert [rank[item["definition"]] for item in receipt["definition_uses"]] == sorted(
        rank[item["definition"]] for item in receipt["definition_uses"]
    )


def test_isolation_receipt_excludes_every_legacy_candidate_and_disallowed_field(
    bundle: dict[str, dict[str, object]],
) -> None:
    from peano_lab.library.quadratic_reciprocity_stack_runtime import (
        quadratic_reciprocity_stack,
    )

    explicit = bundle["explicit.json"]
    defined = bundle["defined.json"]
    isolation = bundle["isolation-receipt.json"]
    _assert_candidate_constants(isolation)
    assert isolation["checks"] == {
        "declared_edges_internal": True,
        "exact_member_names": True,
        "exact_selected_order": True,
        "explicit_defined_order": True,
        "no_disallowed_fields": True,
        "no_duplicate_names": True,
        "no_foreign_names": True,
    }
    assert isolation["counts"] == {
        "definition_records": 40,
        "defined_records": 384,
        "disallowed_fields": 0,
        "duplicate_names": 0,
        "explicit_records": 384,
        "foreign_defined_names": 0,
        "foreign_explicit_names": 0,
        "missing_defined_names": 0,
        "missing_explicit_names": 0,
        "outside_dependency_edges": 0,
        "selected_names": 384,
    }
    selected = {row["name"] for row in explicit["theorems"]}
    selected_order = [row["name"] for row in explicit["theorems"]]
    candidates = {
        spec.name for spec in quadratic_reciprocity_stack().candidate_order
    }
    assert len(candidates) == 317 and candidates.isdisjoint(selected)
    assert candidates.isdisjoint(row["name"] for row in defined["theorems"])
    for document in (explicit, defined, isolation):
        strings = {item for item in _walk(document) if type(item) is str}
        tokens = {
            token
            for item in strings
            for token in re.findall(r"[A-Za-z_][A-Za-z0-9_']*", item)
        }
        assert candidates.isdisjoint(tokens)
        assert not any(PA_TAG.fullmatch(item) for item in tokens)
    for row in [*explicit["theorems"], *defined["theorems"]]:
        assert not (FORBIDDEN_THEOREM_FIELDS & set(row))
    assert isolation["roots"] == {
        "defined_document_root_sha256": defined["root_sha256"],
        "defined_ordered_record_root_sha256": defined["aggregate"][
            "ordered_record_root_sha256"
        ],
        "dependency_edge_root_sha256": explicit["dependency_receipt"][
            "edge_root_sha256"
        ],
        "dependency_node_root_sha256": explicit["dependency_receipt"][
            "node_root_sha256"
        ],
        "explicit_document_root_sha256": explicit["root_sha256"],
        "explicit_ordered_record_root_sha256": explicit["dependency_receipt"][
            "ordered_record_root_sha256"
        ],
        "selected_name_root_sha256": _sha_json(selected_order),
    }
    assert isolation["root_preimage"]["payload"] == {
        key: value
        for key, value in isolation.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    assert isolation["root_sha256"] == _sha_json(isolation["root_preimage"])


@pytest.mark.parametrize(
    "filename, mutation",
    [
        ("explicit.json", lambda doc: doc["theorems"].pop()),
        (
            "explicit.json",
            lambda doc: doc["theorems"].__setitem__(
                slice(0, 2), list(reversed(doc["theorems"][:2]))
            ),
        ),
        ("explicit.json", lambda doc: doc["theorems"][0].update({"tag": "PA0001"})),
        ("explicit.json", lambda doc: doc["theorems"][2].update({"minimality_claim": True})),
        ("explicit.json", lambda doc: doc["theorems"][0].update({"index": True})),
        ("explicit.json", lambda doc: doc.update({"theorem_count": True})),
        ("defined.json", lambda doc: doc["theorems"].append(deepcopy(doc["theorems"][-1]))),
        ("defined.json", lambda doc: doc["theorems"][0].update({"href": "legacy.html"})),
        ("defined.json", lambda doc: doc["definitions"][0].update({"expansion": "forged"})),
        ("isolation-receipt.json", lambda doc: doc["checks"].update({"no_foreign_names": False})),
        ("manifest.json", lambda doc: doc.update({"training_eligible": True})),
        ("manifest.json", lambda doc: doc.update({"independent_owner": {"forged": True}})),
    ],
)
def test_missing_reordered_extra_tagged_and_authority_forged_documents_fail(
    bundle: dict[str, dict[str, object]],
    monkeypatch: pytest.MonkeyPatch,
    filename: str,
    mutation,
) -> None:
    # The unpatched happy path and whole-bundle forgery tests exercise a real
    # pinned rebuild.  Reuse its exact result here so the mutation matrix does
    # not rebuild/compact 384 theorems once per parameter on CI.
    monkeypatch.setattr(
        bundle_module,
        "_build_candidate_documentation_bundle",
        lambda *, repository_root=None: deepcopy(bundle),
    )
    forged = deepcopy(bundle)
    mutation(forged[filename])
    with pytest.raises(LibraryDocumentationBundleError):
        validate_documentation_bundle(forged)


def test_fully_rerooted_record_dependency_line_and_definition_forgeries_fail(
    bundle: dict[str, dict[str, object]], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        bundle_module,
        "_build_candidate_documentation_bundle",
        lambda *, repository_root=None: deepcopy(bundle),
    )
    mutations = (
        ("explicit.json", lambda doc: doc["theorems"][2]["declared_dependencies"].clear()),
        ("explicit.json", lambda doc: doc["theorems"][0]["command_lines"][0].update({"text": "refl"})),
        ("defined.json", lambda doc: doc["theorems"][0]["statement"]["receipt"].update({"exact_ast_equivalence": False})),
        ("defined.json", lambda doc: doc["definitions"][0].update({"source": {"path": "../outside.py", "line": 1, "kind": "declaration", "file_sha256": "0" * 64}})),
    )
    for filename, mutation in mutations:
        forged = deepcopy(bundle)
        document = forged[filename]
        mutation(document)
        for record in document.get("theorems", []):
            record["record_sha256"] = _sha_json(_record_preimage(record))
        for record in document.get("definitions", []):
            record["record_sha256"] = _sha_json(_record_preimage(record))
        forged[filename] = _reroot_document(document)
        with pytest.raises(LibraryDocumentationBundleError):
            validate_documentation_bundle(forged)


def test_fully_rebound_whole_bundle_forgery_still_fails_source_reconstruction(
    bundle: dict[str, dict[str, object]],
) -> None:
    forged = deepcopy(bundle)
    row = forged["explicit.json"]["theorems"][0]
    row["summary"] = "Hostile but internally and transitively re-bound summary."
    row["summary_sha256"] = sha256(row["summary"].encode()).hexdigest()
    forged = _rebind_whole_bundle(forged)

    # Demonstrate that all four document roots and all manifest member bytes
    # have actually been rebound; rejection must come from pinned rebuilding.
    for filename in DOCUMENT_FILES[1:]:
        document = forged[filename]
        assert document["root_sha256"] == _sha_json(document["root_preimage"])
    for receipt in forged["manifest.json"]["files"]:
        raw = canonical_document_bytes(forged[receipt["name"]])
        assert receipt["bytes"] == len(raw)
        assert receipt["sha256"] == sha256(raw).hexdigest()

    with pytest.raises(
        LibraryDocumentationBundleError, match="differs from pinned reconstruction"
    ):
        validate_documentation_bundle(forged)


def test_canonical_loader_rejects_missing_extra_noncanonical_and_hostile_files(
    bundle: dict[str, dict[str, object]], tmp_path: Path
) -> None:
    directory = tmp_path / "bundle"
    directory.mkdir()
    for filename, document in bundle.items():
        (directory / filename).write_bytes(canonical_document_bytes(document))
    assert load_documentation_bundle(directory) == bundle

    explicit = directory / "explicit.json"
    canonical = explicit.read_bytes()
    explicit.write_bytes(_compact_json_bytes(bundle["explicit.json"]))
    with pytest.raises(LibraryDocumentationBundleError):
        load_documentation_bundle(directory)
    explicit.write_bytes(canonical)

    manifest_path = directory / "manifest.json"
    manifest_raw = manifest_path.read_bytes()
    strict_json_attacks = (
        manifest_raw.replace(b"{\n", b'{\n  "format": "duplicate",\n', 1),
        manifest_raw.replace(b'"v": 1', b'"v": 1.0', 1),
        manifest_raw.replace(b'"v": 1', b'"v": NaN', 1),
        b"\xff",
    )
    for attack in strict_json_attacks:
        assert attack != manifest_raw
        manifest_path.write_bytes(attack)
        with pytest.raises(LibraryDocumentationBundleError):
            load_documentation_bundle(directory)
    manifest_path.write_bytes(manifest_raw)

    manifest_path.unlink()
    with pytest.raises(LibraryDocumentationBundleError):
        load_documentation_bundle(directory)
    manifest_path.write_bytes(manifest_raw)

    extra = directory / "legacy.json"
    extra.write_bytes(b"{}\n")
    with pytest.raises(LibraryDocumentationBundleError):
        load_documentation_bundle(directory)
    extra.unlink()

    linked_target = tmp_path / "target.json"
    linked_target.write_bytes((directory / "defined.json").read_bytes())
    (directory / "defined.json").unlink()
    os.mkfifo(directory / "defined.json")
    with pytest.raises(LibraryDocumentationBundleError):
        load_documentation_bundle(directory)
    (directory / "defined.json").unlink()
    (directory / "defined.json").symlink_to(linked_target)
    with pytest.raises(LibraryDocumentationBundleError):
        load_documentation_bundle(directory)

    linked_directory = tmp_path / "linked-directory"
    linked_directory.symlink_to(directory, target_is_directory=True)
    with pytest.raises(LibraryDocumentationBundleError):
        load_documentation_bundle(linked_directory)

    fifo = tmp_path / "bundle-fifo"
    os.mkfifo(fifo)
    with pytest.raises(LibraryDocumentationBundleError):
        load_documentation_bundle(fifo)


def _run_cli(*arguments: object, cwd: Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, str(CLI), *(str(item) for item in arguments)],
        cwd=cwd,
        check=False,
        capture_output=True,
        timeout=120,
    )


def test_cli_has_no_implicit_write_and_explicit_output_is_deterministic_atomic(
    bundle: dict[str, dict[str, object]], tmp_path: Path
) -> None:
    retained_before = {
        path.name: sha256(path.read_bytes()).hexdigest()
        for path in ARTIFACT_DIRECTORY.iterdir()
        if path.is_file()
    }
    default = _run_cli(cwd=tmp_path)
    assert default.returncode == 0, default.stderr.decode("utf-8", "replace")
    assert {
        path.name: sha256(path.read_bytes()).hexdigest()
        for path in ARTIFACT_DIRECTORY.iterdir()
        if path.is_file()
    } == retained_before

    output = tmp_path / "output"
    written = _run_cli("--output-dir", output, cwd=tmp_path)
    assert written.returncode == 0, written.stderr.decode("utf-8", "replace")
    for filename, document in bundle.items():
        assert (output / filename).read_bytes() == canonical_document_bytes(document)
    before = {path.name: path.read_bytes() for path in output.iterdir()}
    checked = _run_cli("--check", "--output-dir", output, cwd=tmp_path)
    assert checked.returncode == 0, checked.stderr.decode("utf-8", "replace")
    assert {path.name: path.read_bytes() for path in output.iterdir()} == before

    (output / "explicit.json").write_bytes(b"stale\n")
    stale = _run_cli("--check", "--output-dir", output, cwd=tmp_path)
    assert stale.returncode != 0
    assert (output / "explicit.json").read_bytes() == b"stale\n"

    target = tmp_path / "target"
    target.mkdir()
    sentinel = target / "sentinel"
    sentinel.write_bytes(b"unchanged\n")
    linked = tmp_path / "linked-output"
    linked.symlink_to(target, target_is_directory=True)
    rejected = _run_cli("--output-dir", linked, cwd=tmp_path)
    assert rejected.returncode != 0
    assert sentinel.read_bytes() == b"unchanged\n"


def test_cli_rejects_symlink_in_an_output_parent_component(tmp_path: Path) -> None:
    real_parent = tmp_path / "real-parent"
    nested_parent = real_parent / "nested"
    nested_parent.mkdir(parents=True)
    sentinel = nested_parent / "sentinel"
    sentinel.write_bytes(b"unchanged\n")
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)

    # The immediate lexical parent looks like a directory under lstat, but an
    # ancestor component is a symlink and resolution changes its path.
    destination = linked_parent / "nested" / "bundle"
    rejected = _run_cli("--output-dir", destination, cwd=tmp_path)
    assert rejected.returncode != 0
    assert b"must not contain symlink components" in rejected.stderr
    assert sentinel.read_bytes() == b"unchanged\n"
    assert not (nested_parent / "bundle").exists()
    assert sorted(path.name for path in nested_parent.iterdir()) == ["sentinel"]


def test_historical_557_explorers_tags_and_metadata_v1_are_immutable() -> None:
    for relative, expected in HISTORICAL_ARTIFACTS.items():
        assert sha256((ROOT / relative).read_bytes()).hexdigest() == expected
    explicit_manifest = _load(
        ROOT / "book/_static/pa-proof-explorer/manifest.json"
    )
    defined_manifest = _load(
        ROOT / "book/_static/pa-proof-explorer/defined/manifest.json"
    )
    assert explicit_manifest["theorem_count"] == 557
    assert explicit_manifest["public_count"] == 240
    assert explicit_manifest["candidate_count"] == 317
    assert explicit_manifest["aggregate_sha256"] == (
        "50c1d143cf6008d3bce737c2e7c0f84fc4ff6eff33978f7690fa22409db3be8b"
    )
    assert defined_manifest["theorem_count"] == 557
    assert defined_manifest["edition_identity_sha256"] == (
        "9b7c7928ddd3e1930fb5eca6e6b6c4b5ce6978633f6f187525d8813c90f3ddd6"
    )
    assert defined_manifest["aggregate_sha256"] == (
        "f77c63e101f8cdf47182160633585a7a522210805d8f239a357fb2fdc94c72a1"
    )
