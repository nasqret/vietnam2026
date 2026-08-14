"""Adversarial acceptance tests for Hydra's selected metadata-v2 join.

Metadata v2 may supersede the candidate v1 reading, but it may not rewrite
that predecessor, import the disjoint research theorem stack, or turn selected
documentation completeness into freeze, training, retrieval, evaluation, or
owner authority.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib.util
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

import training.peano_hydra.library_epoch_metadata_v2 as metadata_module  # noqa: E402
from training.peano_hydra.library_epoch_metadata_v2 import (  # noqa: E402
    LibraryEpochMetadataV2Error,
    build_candidate_epoch_metadata_v2,
    canonical_document_bytes,
    epoch_metadata_v2_schema,
    epoch_metadata_v2_schema_identity,
    load_epoch_metadata_v2,
    readiness_report_v2,
    validate_epoch_metadata_v2,
)


SCHEMA_PATH = ROOT / "training/peano_hydra/library-epoch-metadata-schema-v2.json"
METADATA_PATH = ROOT / "artifacts/peano-hydra/library-epoch-metadata-candidate-v2.json"
READINESS_PATH = ROOT / (
    "artifacts/peano-hydra/library-epoch-metadata-candidate-v2-readiness.json"
)
PREDECESSOR_SCHEMA_PATH = (
    ROOT / "training/peano_hydra/library-epoch-metadata-schema-v1.json"
)
PREDECESSOR_PATH = (
    ROOT / "artifacts/peano-hydra/library-epoch-metadata-candidate-v1.json"
)
PREDECESSOR_READINESS_PATH = ROOT / (
    "artifacts/peano-hydra/library-epoch-metadata-candidate-v1-readiness.json"
)
BUNDLE_PATH = ROOT / "artifacts/peano-hydra/l0-documentation-candidate-v1"
CLI_PATH = ROOT / "scripts/build_peano_hydra_epoch_metadata_v2.py"

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PA_TAG_RE = re.compile(r"^PA[0-9A-Y]{4}$")
FORBIDDEN_ROW_FIELDS = {"closure", "dependents", "href", "scope", "tag"}

PREDECESSOR_PINS = {
    "schema_artifact_sha256": (
        "9867378c8802501d2120ad4d94a86378815cf90b003eafc92b164685da61c956"
    ),
    "schema_sha256": (
        "71995b59d4f5592a08a90dc354a91888f5f1f6f89ec4428be291aea19e76062c"
    ),
    "artifact_sha256": (
        "e719dd526d0aa07e2521fb2e499f2ee6810506d32a912298f11dbac60a2c0289"
    ),
    "root_sha256": (
        "b2f397cec26d5f22bf0806da1f6e219d26bb5e319a503395150d9278efae8279"
    ),
    "readiness_artifact_sha256": (
        "386be7eb475980a373122d769a496220319d34090463e0a3bc870cfece3e4c25"
    ),
}

BUNDLE_PINS = {
    "schema.json": {
        "artifact_sha256": (
            "a442e89ac312302dcee777b5741ca7f2d67e10f6ebcc996b8096fc6061c28a9c"
        ),
        "root_sha256": None,
    },
    "explicit.json": {
        "artifact_sha256": (
            "f1c9f364db0cb7ae7f4c7fe065b1ef48d5522fc49711667479ec3dc4db723936"
        ),
        "root_sha256": (
            "b7942fa5a866ff7cd8a38f30c93787ec0abd2948e69710651e4d3578e64377da"
        ),
    },
    "defined.json": {
        "artifact_sha256": (
            "164b34dd0cad555baf2164ee3da114fb60a447bd667112481e7225097dd17cea"
        ),
        "root_sha256": (
            "897fd5e4bedb44b63853e428ff5bc2e2c273e30a0c239450e0ec8f93d73fc61f"
        ),
    },
    "isolation-receipt.json": {
        "artifact_sha256": (
            "8c8a6882d0d5a82552942fc0c3efe5a900244a9cad02c32b24cabe3d86a0eee6"
        ),
        "root_sha256": (
            "64bdc2c52bcaf88d26382bbe514be4a442cc876b8df2a353c272587e1516d919"
        ),
    },
    "manifest.json": {
        "artifact_sha256": (
            "5ded97c27b859cc4725362bc76aba89fac06c5f11843b50529b78050b19348bf"
        ),
        "root_sha256": (
            "8f7ef8fcca69bc6f5f8b39c220293b8414a65fd81576c584f78e59da104d46a4"
        ),
    },
}

RETAINED_V2_PINS = {
    "schema_artifact_sha256": (
        "27af1e5c1ee0e73cb012db3d8b94cb9a6e1be48d08e8158ad48b8edac399973e"
    ),
    "schema_semantic_sha256": (
        "498dde0a3b4f762197d8c371609dfac2eabf7edcfc37a6d3c5cdf6ca21efb38a"
    ),
    "metadata_artifact_sha256": (
        "dc6a59ce08397eba698651f6ed4faac0533dec55c13d5a8ca49d863d19d7b72d"
    ),
    "metadata_bytes": 3_732_032,
    "metadata_root_sha256": (
        "e0c1d3683e111d7f2883cebbc423694159e82d95471d9375866a81ec596dfb9e"
    ),
    "readiness_artifact_sha256": (
        "f257646d1ba5b51835c8b1718538b4b21c89ea402ba073a9630842708db0206b"
    ),
    "readiness_bytes": 1_891,
    "theorem_record_root_sha256": (
        "22330158f52f049ec920992f51f96a0ab0e9939c3eeb893f533616c17b48e98a"
    ),
}

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


def _record_body(row: dict[str, object]) -> dict[str, object]:
    return {key: item for key, item in row.items() if key != "record_sha256"}


def _reroot(value: dict[str, object]) -> dict[str, object]:
    result = deepcopy(value)
    for row in result["theorems"]:
        row["record_sha256"] = _sha_json(_record_body(row))
    identities = [
        {
            "index": row["index"],
            "name": row["name"],
            "record_sha256": row["record_sha256"],
        }
        for row in result["theorems"]
    ]
    records_preimage = {
        "format": "peano-hydra-library-epoch-theorem-records-preimage",
        "records": identities,
        "v": 2,
    }
    result["theorem_records"] = {
        "count": len(identities),
        "preimage": records_preimage,
        "root_sha256": _sha_json(records_preimage),
    }
    body = {
        key: item
        for key, item in result.items()
        if key not in {"root_preimage", "root_sha256", "theorems"}
    }
    old = result["root_preimage"]
    result["root_preimage"] = {
        "format": old["format"],
        "payload": {
            "body": body,
            "theorem_record_root_sha256": result["theorem_records"][
                "root_sha256"
            ],
        },
        "v": old["v"],
    }
    result["root_sha256"] = _sha_json(result["root_preimage"])
    return result


def _mutated(candidate: dict[str, object], mutation) -> dict[str, object]:
    value = deepcopy(candidate)
    mutation(value)
    return _reroot(value)


def _root_v1_document(value: dict[str, object]) -> dict[str, object]:
    result = deepcopy(value)
    body = {
        key: item
        for key, item in result.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    old = result["root_preimage"]
    result["root_preimage"] = {
        "format": old["format"],
        "payload": body,
        "v": old["v"],
    }
    result["root_sha256"] = _sha_json(result["root_preimage"])
    return result


def _ordered_record_root(rows: list[dict[str, object]]) -> str:
    return _sha_json(
        [[row["index"], row["name"], row["record_sha256"]] for row in rows]
    )


def _reroot_explicit_document(value: dict[str, object]) -> dict[str, object]:
    result = deepcopy(value)
    ordered = _ordered_record_root(result["theorems"])
    result["dependency_receipt"]["ordered_record_root_sha256"] = ordered
    body = {
        key: item
        for key, item in result.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    payload = {
        key: item for key, item in body.items() if key != "theorems"
    } | {
        "ordered_records": [
            {
                "index": row["index"],
                "name": row["name"],
                "record_sha256": row["record_sha256"],
            }
            for row in result["theorems"]
        ]
    }
    result["root_preimage"] = {
        "format": value["root_preimage"]["format"],
        "payload": payload,
        "v": 1,
    }
    result["root_sha256"] = _sha_json(result["root_preimage"])
    return result


def _reroot_defined_document(
    value: dict[str, object], *, explicit_root_sha256: str
) -> dict[str, object]:
    result = deepcopy(value)
    result["explicit_root_sha256"] = explicit_root_sha256
    ordered = _ordered_record_root(result["theorems"])
    result["aggregate"]["ordered_record_root_sha256"] = ordered
    body = {
        key: item
        for key, item in result.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    payload = {
        key: item
        for key, item in body.items()
        if key not in {"definitions", "theorems"}
    } | {
        "definitions_root_sha256": value["root_preimage"]["payload"][
            "definitions_root_sha256"
        ],
        "ordered_records": [
            {
                "index": row["index"],
                "name": row["name"],
                "record_sha256": row["record_sha256"],
            }
            for row in result["theorems"]
        ],
    }
    result["root_preimage"] = {
        "format": value["root_preimage"]["format"],
        "payload": payload,
        "v": 1,
    }
    result["root_sha256"] = _sha_json(result["root_preimage"])
    return result


def _assert_candidate_flags(value: dict[str, object]) -> None:
    assert value["status"] == "candidate"
    assert value["logic_mode"] == "intuitionistic"
    assert value["freeze_ready"] is False
    assert value["training_eligible"] is False
    assert value["retrieval_eligible"] is False
    assert value["evaluation_eligible"] is False


def _assert_exact_fields(
    schema: dict[str, object], shape: str, value: dict[str, object]
) -> None:
    assert set(value) == set(schema["object_shapes"][shape]["fields"])


def _required(schema: dict[str, object], *path: str) -> set[str]:
    value: object = schema
    for key in path:
        assert type(value) is dict and key in value
        value = value[key]
    assert type(value) is dict and type(value.get("required")) is dict
    return set(value["required"])


@pytest.fixture(scope="module")
def candidate() -> dict[str, object]:
    return build_candidate_epoch_metadata_v2()


@pytest.fixture(scope="module")
def predecessor() -> dict[str, object]:
    return _load(PREDECESSOR_PATH)


@pytest.fixture(scope="module")
def bundle_documents() -> dict[str, dict[str, object]]:
    return {
        filename: _load(BUNDLE_PATH / filename)
        for filename in BUNDLE_PINS
    }


def test_schema_is_canonical_closed_pinned_and_candidate_only() -> None:
    schema = epoch_metadata_v2_schema()
    identity = epoch_metadata_v2_schema_identity()
    raw = SCHEMA_PATH.read_bytes()
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
    assert schema["claim_boundary"]["candidate_only"] is True
    assert "absent" in schema["claim_boundary"]["owner_authority"]
    assert "does not imply" in schema["claim_boundary"][
        "selected_api_completeness"
    ]
    predecessor_pins = schema["pins"]["predecessor"]
    assert predecessor_pins == {
        "ledger_artifact_sha256": PREDECESSOR_PINS["artifact_sha256"],
        "ledger_root_sha256": PREDECESSOR_PINS["root_sha256"],
        "readiness_artifact_sha256": PREDECESSOR_PINS[
            "readiness_artifact_sha256"
        ],
        "schema_artifact_sha256": PREDECESSOR_PINS[
            "schema_artifact_sha256"
        ],
        "schema_semantic_sha256": PREDECESSOR_PINS["schema_sha256"],
    }
    selected_pins = schema["pins"]["selected_bundle"]
    assert selected_pins == {
        "defined_artifact_sha256": BUNDLE_PINS["defined.json"][
            "artifact_sha256"
        ],
        "defined_root_sha256": BUNDLE_PINS["defined.json"]["root_sha256"],
        "explicit_artifact_sha256": BUNDLE_PINS["explicit.json"][
            "artifact_sha256"
        ],
        "explicit_root_sha256": BUNDLE_PINS["explicit.json"]["root_sha256"],
        "isolation_artifact_sha256": BUNDLE_PINS["isolation-receipt.json"][
            "artifact_sha256"
        ],
        "isolation_root_sha256": BUNDLE_PINS["isolation-receipt.json"][
            "root_sha256"
        ],
        "manifest_artifact_sha256": BUNDLE_PINS["manifest.json"][
            "artifact_sha256"
        ],
        "manifest_root_sha256": BUNDLE_PINS["manifest.json"]["root_sha256"],
        "schema_artifact_sha256": BUNDLE_PINS["schema.json"][
            "artifact_sha256"
        ],
        "schema_semantic_sha256": "30236aaaecc41104e7e193476f59a8b764d56fe86c63ca04c1561ad38645832d",
    }
    assert _required(schema, "metadata") == {
        "aggregate",
        "documentation_sources",
        "evaluation_eligible",
        "format",
        "freeze_ready",
        "gaps",
        "id",
        "logic_mode",
        "predecessor",
        "replay_pack",
        "repository",
        "retrieval_eligible",
        "root_preimage",
        "root_sha256",
        "schema",
        "status",
        "supersession",
        "theorem_count",
        "theorem_records",
        "theorems",
        "training_eligible",
        "v",
    }


def test_predecessor_bundle_and_historical_artifacts_are_exactly_immutable() -> None:
    assert sha256(PREDECESSOR_SCHEMA_PATH.read_bytes()).hexdigest() == (
        PREDECESSOR_PINS["schema_artifact_sha256"]
    )
    assert _sha_json(_load(PREDECESSOR_SCHEMA_PATH)) == PREDECESSOR_PINS[
        "schema_sha256"
    ]
    assert sha256(PREDECESSOR_PATH.read_bytes()).hexdigest() == PREDECESSOR_PINS[
        "artifact_sha256"
    ]
    assert _load(PREDECESSOR_PATH)["root_sha256"] == PREDECESSOR_PINS[
        "root_sha256"
    ]
    assert sha256(PREDECESSOR_READINESS_PATH.read_bytes()).hexdigest() == (
        PREDECESSOR_PINS["readiness_artifact_sha256"]
    )
    for filename, expected in BUNDLE_PINS.items():
        raw = (BUNDLE_PATH / filename).read_bytes()
        assert sha256(raw).hexdigest() == expected["artifact_sha256"]
        if expected["root_sha256"] is not None:
            assert json.loads(raw)["root_sha256"] == expected["root_sha256"]
    for relative, expected in HISTORICAL_ARTIFACTS.items():
        assert sha256((ROOT / relative).read_bytes()).hexdigest() == expected


def test_retained_v2_schema_metadata_and_readiness_have_exact_frozen_identities(
) -> None:
    schema_raw = SCHEMA_PATH.read_bytes()
    metadata_raw = METADATA_PATH.read_bytes()
    readiness_raw = READINESS_PATH.read_bytes()
    assert sha256(schema_raw).hexdigest() == RETAINED_V2_PINS[
        "schema_artifact_sha256"
    ]
    assert _sha_json(json.loads(schema_raw)) == RETAINED_V2_PINS[
        "schema_semantic_sha256"
    ]
    assert len(metadata_raw) == RETAINED_V2_PINS["metadata_bytes"]
    assert sha256(metadata_raw).hexdigest() == RETAINED_V2_PINS[
        "metadata_artifact_sha256"
    ]
    assert len(readiness_raw) == RETAINED_V2_PINS["readiness_bytes"]
    assert sha256(readiness_raw).hexdigest() == RETAINED_V2_PINS[
        "readiness_artifact_sha256"
    ]
    retained = json.loads(metadata_raw)
    readiness = json.loads(readiness_raw)
    assert metadata_raw == canonical_document_bytes(retained)
    assert retained["root_sha256"] == RETAINED_V2_PINS[
        "metadata_root_sha256"
    ]
    assert retained["theorem_records"]["root_sha256"] == RETAINED_V2_PINS[
        "theorem_record_root_sha256"
    ]
    assert readiness["metadata_artifact_sha256"] == RETAINED_V2_PINS[
        "metadata_artifact_sha256"
    ]
    assert readiness["metadata_root_sha256"] == RETAINED_V2_PINS[
        "metadata_root_sha256"
    ]
    assert readiness["theorem_record_root_sha256"] == RETAINED_V2_PINS[
        "theorem_record_root_sha256"
    ]
    assert readiness_raw == canonical_document_bytes(readiness)


def test_private_combined_builder_runs_one_exact_build_and_matches_public_bytes(
    candidate: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    original = metadata_module._candidate_body
    calls = 0

    def counted(root: Path):
        nonlocal calls
        calls += 1
        return original(root)

    monkeypatch.setattr(metadata_module, "_candidate_body", counted)
    combined_metadata, combined_readiness = (
        metadata_module._build_candidate_epoch_metadata_v2_with_readiness()
    )
    assert calls == 1
    assert canonical_document_bytes(combined_metadata) == canonical_document_bytes(
        candidate
    ) == METADATA_PATH.read_bytes()
    public_readiness = readiness_report_v2(candidate)
    assert calls == 2
    assert canonical_document_bytes(combined_readiness) == canonical_document_bytes(
        public_readiness
    ) == READINESS_PATH.read_bytes()
    for private_name in (
        "_build_candidate_epoch_metadata_v2",
        "_build_candidate_epoch_metadata_v2_with_readiness",
        "_readiness_projection_from_validated_v2",
    ):
        assert private_name not in metadata_module.__all__


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
    with pytest.raises(LibraryEpochMetadataV2Error):
        canonical_document_bytes(value)


def test_canonical_transport_rejects_cycles_and_nonexact_limits() -> None:
    cycle: list[object] = []
    cycle.append(cycle)
    with pytest.raises(LibraryEpochMetadataV2Error):
        canonical_document_bytes(cycle)
    for limit in (True, 1.0, 0, -1):
        with pytest.raises(TypeError):
            canonical_document_bytes({}, limit=limit)


def test_fresh_process_build_imports_no_predecessor_builder_or_disjoint_stack() -> None:
    script = r'''import sys
from training.peano_hydra.library_epoch_metadata_v2 import build_candidate_epoch_metadata_v2
value = build_candidate_epoch_metadata_v2()
assert value["theorem_count"] == 384
loaded = set(sys.modules)
assert "training.peano_hydra.library_epoch_metadata" not in loaded
stack_fragment = "quadratic_reciprocity_" + "stack"
assert not any(stack_fragment in name for name in loaded)
explorer_fragment = "proof_" + "explorer"
assert not any(explorer_fragment in name for name in loaded)
assert not any(
    name.startswith("peano_lab.library.")
    and name.rsplit(".", 1)[-1].endswith("_candidate")
    for name in loaded
)
'''
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join((str(PY_ROOT), str(ROOT)))
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")


def test_v2_source_contains_no_old_corpus_path_or_hash_dependency() -> None:
    source = "\n".join(
        (
            Path(metadata_module.__file__).read_text(encoding="utf-8"),
            CLI_PATH.read_text(encoding="utf-8"),
            SCHEMA_PATH.read_text(encoding="utf-8"),
        )
    )
    forbidden = (
        "pa-proof-explorer",
        "pa-proof-tags",
        *HISTORICAL_ARTIFACTS.values(),
    )
    assert not any(item in source for item in forbidden)


def test_candidate_has_exact_order_preserved_v1_evidence_and_selected_joins(
    candidate: dict[str, object],
    predecessor: dict[str, object],
    bundle_documents: dict[str, dict[str, object]],
) -> None:
    _assert_candidate_flags(candidate)
    rows = candidate["theorems"]
    old_rows = predecessor["theorems"]
    explicit = bundle_documents["explicit.json"]
    defined = bundle_documents["defined.json"]
    explicit_rows = explicit["theorems"]
    defined_rows = defined["theorems"]
    assert candidate["theorem_count"] == len(rows) == 384
    assert [row["index"] for row in rows] == list(range(384))
    assert [row["name"] for row in rows] == [
        row["name"] for row in old_rows
    ] == [row["name"] for row in explicit_rows] == [
        row["name"] for row in defined_rows
    ]
    assert sum(
        len(row["dependencies"]["declared_publication_dependencies"])
        for row in rows
    ) == 1_038

    preserved_keys = (
        "declaration_order",
        "dependencies",
        "explanation",
        "index",
        "layer",
        "lineage",
        "logic",
        "name",
        "optimized_construction",
        "proof",
        "readable_proof",
        "source",
        "statement",
    )
    for row, old, explicit_row, defined_row in zip(
        rows, old_rows, explicit_rows, defined_rows, strict=True
    ):
        for key in preserved_keys:
            assert row[key] == old[key]
        assert row["predecessor"] == {"record_sha256": _sha_json(old)}
        assert row["documentation"]["atlas"] == old["documentation"]["atlas"]
        assert row["documentation"]["vault"] == old["documentation"]["vault"]
        assert row["presentation"] == {
            "authority": "historical-non-authoritative",
            "deployed_defined_page_status": old["documentation"][
                "defined_explorer"
            ]["status"],
            "deployed_explicit_page_status": old["documentation"][
                "explicit_explorer"
            ]["status"],
        }
        assert row["documentation"]["selected_explicit_api"] == {
            "artifact_path": (
                "artifacts/peano-hydra/l0-documentation-candidate-v1/explicit.json"
            ),
            "artifact_sha256": BUNDLE_PINS["explicit.json"]["artifact_sha256"],
            "document_root_sha256": explicit["root_sha256"],
            "record_sha256": explicit_row["record_sha256"],
            "status": "present",
        }
        assert row["documentation"]["selected_defined_api"] == {
            "artifact_path": (
                "artifacts/peano-hydra/l0-documentation-candidate-v1/defined.json"
            ),
            "artifact_sha256": BUNDLE_PINS["defined.json"]["artifact_sha256"],
            "document_root_sha256": defined["root_sha256"],
            "record_sha256": defined_row["record_sha256"],
            "status": "present",
        }
        assert row["definitions"] == {
            "artifact_path": (
                "artifacts/peano-hydra/l0-documentation-candidate-v1/defined.json"
            ),
            "artifact_sha256": BUNDLE_PINS["defined.json"]["artifact_sha256"],
            "definition_use_count": sum(
                use["occurrences"] for use in defined_row["definition_uses"]
            ),
            "definition_use_preimage": {
                "format": (
                    "peano-hydra-library-definition-use-receipt-preimage"
                ),
                "uses": defined_row["definition_uses"],
                "v": 2,
            },
            "definition_use_receipt_sha256": _sha_json(
                {
                    "format": (
                        "peano-hydra-library-definition-use-receipt-preimage"
                    ),
                    "uses": defined_row["definition_uses"],
                    "v": 2,
                }
            ),
            "document_root_sha256": defined["root_sha256"],
            "record_sha256": defined_row["record_sha256"],
            "registry": defined["registry"],
            "status": "present",
        }
        assert row["record_sha256"] == _sha_json(_record_body(row))
        assert not (FORBIDDEN_ROW_FIELDS & set(row))
        assert "explicit_explorer" not in row["documentation"]
        assert "defined_explorer" not in row["documentation"]


@pytest.mark.parametrize(
    "mutate_explicit",
    (
        lambda row: row.update(
            {
                "statement_canonical": "0 = S 0",
                "statement_canonical_sha256": sha256(b"0 = S 0").hexdigest(),
            }
        ),
        lambda row: row.update({"script_sha256": "0" * 64}),
        lambda row: row["source"].update({"line": row["source"]["line"] + 1}),
        lambda row: row.update({"catalog_layer": "forged-layer"}),
        lambda row: row.update(
            {
                "summary": "forged summary",
                "summary_sha256": sha256(b"forged summary").hexdigest(),
            }
        ),
    ),
)
def test_predecessor_selected_cross_join_rejects_semantic_receipt_drift(
    monkeypatch: pytest.MonkeyPatch,
    bundle_documents: dict[str, dict[str, object]],
    mutate_explicit,
) -> None:
    forged = deepcopy(bundle_documents)
    explicit_row = forged["explicit.json"]["theorems"][0]
    mutate_explicit(explicit_row)
    explicit_row["record_sha256"] = _sha_json(_record_body(explicit_row))
    defined_row = forged["defined.json"]["theorems"][0]
    defined_row["explicit_record_sha256"] = explicit_row["record_sha256"]
    defined_row["record_sha256"] = _sha_json(_record_body(defined_row))
    monkeypatch.setattr(metadata_module, "_load_selected_bundle", lambda _root: forged)
    with pytest.raises(LibraryEpochMetadataV2Error):
        build_candidate_epoch_metadata_v2()


@pytest.mark.parametrize("attack", ("id-name", "order", "aggregate"))
def test_definition_uses_bind_registry_name_canonical_order_and_aggregate(
    monkeypatch: pytest.MonkeyPatch,
    bundle_documents: dict[str, dict[str, object]],
    attack: str,
) -> None:
    forged = deepcopy(bundle_documents)
    defined = forged["defined.json"]
    if attack == "id-name":
        defined["theorems"][14]["definition_uses"][0]["name"] = "Lt"
    elif attack == "order":
        defined["theorems"][41]["definition_uses"].reverse()
    else:
        defined["theorems"][14]["definition_uses"][0]["occurrences"] += 1
        defined["aggregate"]["definition_occurrences"] += 1
    for row in defined["theorems"]:
        row["record_sha256"] = _sha_json(_record_body(row))
    monkeypatch.setattr(metadata_module, "_load_selected_bundle", lambda _root: forged)
    with pytest.raises(LibraryEpochMetadataV2Error):
        build_candidate_epoch_metadata_v2()


def test_every_v2_owned_object_has_the_closed_schema_shape(
    candidate: dict[str, object],
) -> None:
    schema = epoch_metadata_v2_schema()
    report = readiness_report_v2(candidate)
    selected = candidate["documentation_sources"]["selected_bundle"]

    for shape, value in (
        ("metadata", candidate),
        ("aggregate", candidate["aggregate"]),
        ("documentation_sources", candidate["documentation_sources"]),
        ("gaps", candidate["gaps"]),
        ("metadata_root_preimage", candidate["root_preimage"]),
        ("metadata_root_payload", candidate["root_preimage"]["payload"]),
        ("metadata_body", candidate["root_preimage"]["payload"]["body"]),
        ("predecessor", candidate["predecessor"]),
        ("predecessor_ledger", candidate["predecessor"]["ledger"]),
        ("predecessor_readiness", candidate["predecessor"]["readiness"]),
        ("predecessor_schema", candidate["predecessor"]["schema"]),
        ("schema_identity", candidate["schema"]),
        ("selected_bundle", selected),
        ("selected_bundle_defined", selected["defined"]),
        ("selected_bundle_explicit", selected["explicit"]),
        ("selected_bundle_rooted_member", selected["isolation"]),
        ("selected_bundle_rooted_member", selected["manifest"]),
        ("selected_bundle_schema", selected["schema"]),
        ("definition_registry", selected["registry"]),
        ("supersession", candidate["supersession"]),
        ("theorem_records", candidate["theorem_records"]),
        ("theorem_records_preimage", candidate["theorem_records"]["preimage"]),
        ("readiness", report),
    ):
        _assert_exact_fields(schema, shape, value)

    for identity, row in zip(
        candidate["theorem_records"]["preimage"]["records"],
        candidate["theorems"],
        strict=True,
    ):
        _assert_exact_fields(schema, "theorem_record_identity", identity)
        _assert_exact_fields(schema, "theorem", row)
        _assert_exact_fields(schema, "row_predecessor", row["predecessor"])
        _assert_exact_fields(schema, "presentation", row["presentation"])
        _assert_exact_fields(
            schema, "theorem_documentation", row["documentation"]
        )
        _assert_exact_fields(
            schema,
            "selected_api_receipt",
            row["documentation"]["selected_explicit_api"],
        )
        _assert_exact_fields(
            schema,
            "selected_api_receipt",
            row["documentation"]["selected_defined_api"],
        )
        _assert_exact_fields(schema, "definition_receipt", row["definitions"])
        _assert_exact_fields(
            schema, "definition_registry", row["definitions"]["registry"]
        )
        _assert_exact_fields(
            schema,
            "definition_use_preimage",
            row["definitions"]["definition_use_preimage"],
        )
        for use in row["definitions"]["definition_use_preimage"]["uses"]:
            _assert_exact_fields(schema, "definition_use", use)


def test_theorem_record_and_metadata_roots_bind_exact_ordered_preimages(
    candidate: dict[str, object],
) -> None:
    identities = [
        {
            "index": row["index"],
            "name": row["name"],
            "record_sha256": row["record_sha256"],
        }
        for row in candidate["theorems"]
    ]
    records_preimage = {
        "format": "peano-hydra-library-epoch-theorem-records-preimage",
        "records": identities,
        "v": 2,
    }
    assert candidate["theorem_records"] == {
        "count": 384,
        "preimage": records_preimage,
        "root_sha256": _sha_json(records_preimage),
    }
    for row in candidate["theorems"]:
        assert row["record_sha256"] == _sha_json(_record_body(row))

    body = {
        key: value
        for key, value in candidate.items()
        if key not in {"root_preimage", "root_sha256", "theorems"}
    }
    assert candidate["root_preimage"] == {
        "format": "peano-hydra-library-epoch-metadata-root-preimage",
        "payload": {
            "body": body,
            "theorem_record_root_sha256": candidate["theorem_records"][
                "root_sha256"
            ],
        },
        "v": 2,
    }
    assert candidate["root_sha256"] == _sha_json(candidate["root_preimage"])


def test_selected_api_is_complete_while_deployed_pages_remain_240_of_384(
    candidate: dict[str, object], predecessor: dict[str, object]
) -> None:
    assert candidate["aggregate"] == {
        "declared_dependency_edges": 1_038,
        "deployed_page_documentation_complete_count": 240,
        "selected_api_documentation_complete_count": 384,
        "source_locator_count": 384,
        "theorem_count": 384,
    }
    gaps = candidate["gaps"]
    assert gaps == {
        "atlas_missing_count": 0,
        "atlas_stale_count": 0,
        "deployed_defined_page_pending_count": 144,
        "deployed_explicit_page_pending_count": 144,
        "human_review_pending_count": 384,
        "lineage_pending_count": 384,
        "optimized_best_known_pending_count": 384,
        "optimized_dependency_vectors_pending_count": 384,
        "publication_union_pending_count": 384,
        "readable_dependency_vectors_unverified_count": 384,
        "selected_defined_api_missing_count": 0,
        "selected_defined_api_stale_count": 0,
        "selected_definition_receipt_missing_count": 0,
        "selected_definition_receipt_stale_count": 0,
        "selected_explicit_api_missing_count": 0,
        "selected_explicit_api_stale_count": 0,
        "source_locator_missing_count": 0,
        "vault_missing_count": 0,
        "vault_stale_count": 0,
    }
    assert sum(
        row["presentation"]["deployed_explicit_page_status"] == "present"
        for row in candidate["theorems"]
    ) == 240
    assert sum(
        row["presentation"]["deployed_defined_page_status"] == "present"
        for row in candidate["theorems"]
    ) == 240
    assert sum(
        row["presentation"]["deployed_explicit_page_status"] == "present"
        and row["presentation"]["deployed_defined_page_status"] == "present"
        for row in candidate["theorems"]
    ) == candidate["aggregate"]["deployed_page_documentation_complete_count"]
    assert predecessor["aggregate"]["documentation_complete_count"] == 240
    for row in candidate["theorems"]:
        assert row["documentation"]["selected_explicit_api"]["status"] == "present"
        assert row["documentation"]["selected_defined_api"]["status"] == "present"
        assert row["definitions"]["status"] == "present"
        assert row["dependencies"]["minimality_claim"] is False
        assert row["dependencies"]["readable_dependencies"] is None
        assert row["dependencies"]["optimized_dependencies"] is None
        assert row["dependencies"]["publication_union"] is None
        assert row["explanation"]["review_status"] == "pending-human-review"
        assert row["lineage"] == {"id": None, "status": "pending"}
        assert row["optimized_construction"]["claim"] == (
            "submitted-not-best-known"
        )


def test_candidate_binds_exact_predecessor_bundle_and_successor_boundary(
    candidate: dict[str, object],
    predecessor: dict[str, object],
    bundle_documents: dict[str, dict[str, object]],
) -> None:
    assert candidate["predecessor"] == {
        "ledger": {
            "artifact_path": (
                "artifacts/peano-hydra/library-epoch-metadata-candidate-v1.json"
            ),
            "artifact_sha256": PREDECESSOR_PINS["artifact_sha256"],
            "id": predecessor["id"],
            "root_sha256": predecessor["root_sha256"],
            "v": 1,
        },
        "readiness": {
            "artifact_path": (
                "artifacts/peano-hydra/library-epoch-metadata-candidate-v1-readiness.json"
            ),
            "artifact_sha256": PREDECESSOR_PINS["readiness_artifact_sha256"],
            "metadata_root_sha256": predecessor["root_sha256"],
            "v": 1,
        },
        "schema": {
            "artifact_path": (
                "training/peano_hydra/library-epoch-metadata-schema-v1.json"
            ),
            "artifact_sha256": PREDECESSOR_PINS["schema_artifact_sha256"],
            "format": "peano-hydra-library-epoch-metadata-schema",
            "id": "peano-hydra-library-epoch-metadata-v1",
            "sha256": PREDECESSOR_PINS["schema_sha256"],
            "v": 1,
        },
    }
    selected = candidate["documentation_sources"]["selected_bundle"]
    assert selected["manifest"]["artifact_sha256"] == BUNDLE_PINS[
        "manifest.json"
    ]["artifact_sha256"]
    assert selected["manifest"]["root_sha256"] == bundle_documents[
        "manifest.json"
    ]["root_sha256"]
    assert selected["explicit"]["artifact_sha256"] == BUNDLE_PINS[
        "explicit.json"
    ]["artifact_sha256"]
    assert selected["defined"]["artifact_sha256"] == BUNDLE_PINS[
        "defined.json"
    ]["artifact_sha256"]
    assert selected["isolation"]["artifact_sha256"] == BUNDLE_PINS[
        "isolation-receipt.json"
    ]["artifact_sha256"]
    assert candidate["supersession"] == {
        "added_receipts": [
            "selected_explicit_api",
            "selected_defined_api",
            "selected_definition_use",
        ],
        "kind": "full-candidate-successor-ledger",
        "predecessor_id": predecessor["id"],
        "preserved_evidence": [
            "replay_pack",
            "repository",
            "theorem_semantics",
            "proofs",
            "source_locators",
            "atlas_receipts",
            "vault_receipts",
            "deployed_page_statuses",
            "unresolved_authority_gaps",
        ],
        "status": "candidate-successor",
    }
    assert candidate["replay_pack"] == predecessor["replay_pack"]
    assert candidate["repository"] == predecessor["repository"]


def test_candidate_contains_no_old_api_corpus_receipts_tags_or_disjoint_names(
    candidate: dict[str, object],
) -> None:
    from peano_lab.library.quadratic_reciprocity_stack_runtime import (
        quadratic_reciprocity_stack,
    )

    candidates = {
        spec.name for spec in quadratic_reciprocity_stack().candidate_order
    }
    assert len(candidates) == 317
    production_source = "\n".join(
        (
            Path(metadata_module.__file__).read_text(encoding="utf-8"),
            CLI_PATH.read_text(encoding="utf-8"),
            SCHEMA_PATH.read_text(encoding="utf-8"),
        )
    )
    production_tokens = set(
        re.findall(r"[A-Za-z_][A-Za-z0-9_']*", production_source)
    )
    assert candidates.isdisjoint(production_tokens)
    strings = {item for item in _walk(candidate) if type(item) is str}
    tokens = {
        token
        for item in strings
        for token in re.findall(r"[A-Za-z_][A-Za-z0-9_']*", item)
    }
    assert candidates.isdisjoint(tokens)
    assert not any(PA_TAG_RE.fullmatch(item) for item in strings)
    assert not any(
        item in strings
        for item in (
            "book/_static/pa-proof-explorer/api/corpus.json",
            "book/_static/pa-proof-explorer/defined/api/corpus.json",
            HISTORICAL_ARTIFACTS[
                "book/_static/pa-proof-explorer/api/corpus.json"
            ],
            HISTORICAL_ARTIFACTS[
                "book/_static/pa-proof-explorer/defined/api/corpus.json"
            ],
        )
    )
    assert not any(
        type(key) is str and key in FORBIDDEN_ROW_FIELDS
        for key in _walk(candidate)
    )


def test_v2_builder_does_not_call_v1_build_or_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import training.peano_hydra.library_epoch_metadata as predecessor_module

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("metadata-v1 live builder/validator was called")

    forbidden_paths = (
        "book/_static/pa-proof-explorer",
        "research/arithmetic-library/pa-proof-tags.json",
    )
    original_os_open = os.open
    original_read_bytes = Path.read_bytes

    def guarded_os_open(path: object, *args: object, **kwargs: object):
        assert not any(item in os.fspath(path) for item in forbidden_paths)
        return original_os_open(path, *args, **kwargs)

    def guarded_read_bytes(path: Path) -> bytes:
        assert not any(item in str(path) for item in forbidden_paths)
        return original_read_bytes(path)

    monkeypatch.setattr(predecessor_module, "build_candidate_epoch_metadata", forbidden)
    monkeypatch.setattr(predecessor_module, "validate_epoch_metadata", forbidden)
    monkeypatch.setattr(os, "open", guarded_os_open)
    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)
    rebuilt = build_candidate_epoch_metadata_v2()
    assert rebuilt["theorem_count"] == 384


def test_schema_source_has_no_duplicate_json_keys() -> None:
    def strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            assert key not in result, f"duplicate schema key: {key!r}"
            result[key] = value
        return result

    decoded = json.loads(
        SCHEMA_PATH.read_text(encoding="utf-8"), object_pairs_hook=strict_object
    )
    assert type(decoded) is dict


@pytest.mark.parametrize(
    "mutation",
    (
        lambda value: value["theorems"].pop(),
        lambda value: value["theorems"].__setitem__(
            slice(0, 2), list(reversed(value["theorems"][:2]))
        ),
        lambda value: value["theorems"][0]["predecessor"].update(
            {"record_sha256": "0" * 64}
        ),
        lambda value: value["theorems"][0]["documentation"][
            "selected_explicit_api"
        ].update({"record_sha256": "0" * 64}),
        lambda value: value["theorems"][0]["definitions"].update(
            {"definition_use_receipt_sha256": "0" * 64}
        ),
        lambda value: value["theorems"][0]["presentation"].update(
            {"authority": "authoritative"}
        ),
        lambda value: value["gaps"].update(
            {"selected_explicit_api_missing_count": 1}
        ),
        lambda value: value.update({"training_eligible": True}),
        lambda value: value.update({"independent_owner": {"forged": True}}),
    ),
)
def test_fully_rerooted_predecessor_bundle_join_and_authority_forgeries_fail(
    candidate: dict[str, object], mutation
) -> None:
    forged = _mutated(candidate, mutation)
    assert forged["root_sha256"] == _sha_json(forged["root_preimage"])
    with pytest.raises(LibraryEpochMetadataV2Error):
        validate_epoch_metadata_v2(forged)


def test_fully_rerooted_alternate_predecessor_cannot_be_substituted(
    candidate: dict[str, object], predecessor: dict[str, object]
) -> None:
    alternate = deepcopy(predecessor)
    alternate["theorems"][0]["statement"]["canonical"] = "0 = S 0"
    alternate["theorems"][0]["statement"]["canonical_sha256"] = sha256(
        b"0 = S 0"
    ).hexdigest()
    alternate = _root_v1_document(alternate)
    alternate_readiness = _load(PREDECESSOR_READINESS_PATH)
    alternate_readiness["metadata_root_sha256"] = alternate["root_sha256"]

    forged = deepcopy(candidate)
    forged["theorems"][0]["statement"] = deepcopy(
        alternate["theorems"][0]["statement"]
    )
    for row, old in zip(
        forged["theorems"], alternate["theorems"], strict=True
    ):
        row["predecessor"]["record_sha256"] = _sha_json(old)
    forged["predecessor"]["ledger"].update(
        {
            "artifact_sha256": sha256(
                canonical_document_bytes(alternate)
            ).hexdigest(),
            "root_sha256": alternate["root_sha256"],
        }
    )
    forged["predecessor"]["readiness"].update(
        {
            "artifact_sha256": sha256(
                canonical_document_bytes(alternate_readiness)
            ).hexdigest(),
            "metadata_root_sha256": alternate["root_sha256"],
        }
    )
    forged = _reroot(forged)
    assert forged["theorems"][0]["predecessor"]["record_sha256"] == _sha_json(
        alternate["theorems"][0]
    )
    assert forged["predecessor"]["ledger"]["root_sha256"] == alternate[
        "root_sha256"
    ]
    assert forged["root_sha256"] == _sha_json(forged["root_preimage"])
    with pytest.raises(LibraryEpochMetadataV2Error):
        validate_epoch_metadata_v2(forged)


def test_fully_rerooted_alternate_selected_bundle_cannot_be_substituted(
    candidate: dict[str, object],
    bundle_documents: dict[str, dict[str, object]],
) -> None:
    explicit = deepcopy(bundle_documents["explicit.json"])
    explicit_row = explicit["theorems"][0]
    explicit_row["summary"] = "forged summary"
    explicit_row["summary_sha256"] = sha256(b"forged summary").hexdigest()
    explicit_row["record_sha256"] = _sha_json(_record_body(explicit_row))
    explicit = _reroot_explicit_document(explicit)

    defined = deepcopy(bundle_documents["defined.json"])
    defined_row = defined["theorems"][0]
    defined_row["explicit_record_sha256"] = explicit_row["record_sha256"]
    defined_row["record_sha256"] = _sha_json(_record_body(defined_row))
    defined = _reroot_defined_document(
        defined, explicit_root_sha256=explicit["root_sha256"]
    )

    isolation = deepcopy(bundle_documents["isolation-receipt.json"])
    isolation["roots"].update(
        {
            "defined_document_root_sha256": defined["root_sha256"],
            "defined_ordered_record_root_sha256": defined["aggregate"][
                "ordered_record_root_sha256"
            ],
            "explicit_document_root_sha256": explicit["root_sha256"],
            "explicit_ordered_record_root_sha256": explicit[
                "dependency_receipt"
            ]["ordered_record_root_sha256"],
        }
    )
    isolation = _root_v1_document(isolation)

    replacements = {
        "explicit.json": explicit,
        "defined.json": defined,
        "isolation-receipt.json": isolation,
    }
    manifest = deepcopy(bundle_documents["manifest.json"])
    for receipt in manifest["files"]:
        if receipt["name"] in replacements:
            raw = canonical_document_bytes(replacements[receipt["name"]])
            receipt.update({"bytes": len(raw), "sha256": sha256(raw).hexdigest()})
    manifest = _root_v1_document(manifest)
    replacements["manifest.json"] = manifest

    forged = deepcopy(candidate)
    selected = forged["documentation_sources"]["selected_bundle"]
    artifact_hashes = {
        name: sha256(canonical_document_bytes(document)).hexdigest()
        for name, document in replacements.items()
    }
    selected["explicit"].update(
        {
            "artifact_sha256": artifact_hashes["explicit.json"],
            "ordered_record_root_sha256": explicit["dependency_receipt"][
                "ordered_record_root_sha256"
            ],
            "root_sha256": explicit["root_sha256"],
        }
    )
    selected["defined"].update(
        {
            "artifact_sha256": artifact_hashes["defined.json"],
            "ordered_record_root_sha256": defined["aggregate"][
                "ordered_record_root_sha256"
            ],
            "root_sha256": defined["root_sha256"],
        }
    )
    selected["isolation"].update(
        {
            "artifact_sha256": artifact_hashes["isolation-receipt.json"],
            "root_sha256": isolation["root_sha256"],
        }
    )
    selected["manifest"].update(
        {
            "artifact_sha256": artifact_hashes["manifest.json"],
            "root_sha256": manifest["root_sha256"],
        }
    )
    for index, row in enumerate(forged["theorems"]):
        row["documentation"]["selected_explicit_api"].update(
            {
                "artifact_sha256": artifact_hashes["explicit.json"],
                "document_root_sha256": explicit["root_sha256"],
                "record_sha256": explicit["theorems"][index]["record_sha256"],
            }
        )
        row["documentation"]["selected_defined_api"].update(
            {
                "artifact_sha256": artifact_hashes["defined.json"],
                "document_root_sha256": defined["root_sha256"],
                "record_sha256": defined["theorems"][index]["record_sha256"],
            }
        )
        row["definitions"].update(
            {
                "artifact_sha256": artifact_hashes["defined.json"],
                "document_root_sha256": defined["root_sha256"],
                "record_sha256": defined["theorems"][index]["record_sha256"],
            }
        )
    forged = _reroot(forged)
    assert forged["documentation_sources"]["selected_bundle"]["manifest"][
        "root_sha256"
    ] == manifest["root_sha256"]
    assert forged["root_sha256"] == _sha_json(forged["root_preimage"])
    with pytest.raises(LibraryEpochMetadataV2Error):
        validate_epoch_metadata_v2(forged)


def test_readiness_revalidates_candidate_and_cannot_upgrade_flags(
    candidate: dict[str, object],
) -> None:
    report = readiness_report_v2(candidate)
    assert report["metadata_root_sha256"] == candidate["root_sha256"]
    assert report["metadata_artifact_sha256"] == sha256(
        canonical_document_bytes(candidate)
    ).hexdigest()
    assert report["status"] == "candidate"
    assert report["freeze_ready"] is False
    assert report["training_eligible"] is False
    assert report["retrieval_eligible"] is False
    assert report["evaluation_eligible"] is False
    for field in (
        "freeze_ready",
        "training_eligible",
        "retrieval_eligible",
        "evaluation_eligible",
    ):
        forged = _mutated(candidate, lambda value, field=field: value.update({field: True}))
        with pytest.raises(LibraryEpochMetadataV2Error):
            readiness_report_v2(forged)


def test_loader_accepts_only_one_canonical_bounded_nofollow_document(
    candidate: dict[str, object], tmp_path: Path
) -> None:
    path = tmp_path / "metadata-v2.json"
    canonical = canonical_document_bytes(candidate)
    path.write_bytes(canonical)
    assert load_epoch_metadata_v2(path) == candidate

    path.write_bytes(_compact_json_bytes(candidate))
    with pytest.raises(LibraryEpochMetadataV2Error):
        load_epoch_metadata_v2(path)

    attacks = (
        canonical.replace(b"{\n", b'{\n  "format": "duplicate",\n', 1),
        canonical.replace(b'"v": 2', b'"v": 2.0', 1),
        canonical.replace(b'"v": 2', b'"v": NaN', 1),
        b"\xff",
    )
    for attack in attacks:
        assert attack != canonical
        path.write_bytes(attack)
        with pytest.raises(LibraryEpochMetadataV2Error):
            load_epoch_metadata_v2(path)

    target = tmp_path / "target.json"
    target.write_bytes(canonical)
    path.unlink()
    path.symlink_to(target)
    with pytest.raises(LibraryEpochMetadataV2Error):
        load_epoch_metadata_v2(path)
    path.unlink()
    os.mkfifo(path)
    with pytest.raises(LibraryEpochMetadataV2Error):
        load_epoch_metadata_v2(path)
    path.unlink()
    path.mkdir()
    with pytest.raises(LibraryEpochMetadataV2Error):
        load_epoch_metadata_v2(path)


def test_loader_rejects_oversize_and_symlinked_ancestor_components(
    candidate: dict[str, object], tmp_path: Path
) -> None:
    oversized = tmp_path / "oversized.json"
    with oversized.open("wb") as stream:
        stream.truncate(metadata_module.MAX_METADATA_BYTES + 1)
    with pytest.raises(LibraryEpochMetadataV2Error):
        load_epoch_metadata_v2(oversized)

    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    target = real_parent / "metadata.json"
    target.write_bytes(canonical_document_bytes(candidate))
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    with pytest.raises(LibraryEpochMetadataV2Error):
        load_epoch_metadata_v2(linked_parent / "metadata.json")


def test_builder_rejects_symlink_repository_root(tmp_path: Path) -> None:
    linked = tmp_path / "repository"
    linked.symlink_to(ROOT, target_is_directory=True)
    with pytest.raises(LibraryEpochMetadataV2Error):
        build_candidate_epoch_metadata_v2(repository_root=linked)


def _run_cli(*arguments: object, cwd: Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, str(CLI_PATH), *(str(item) for item in arguments)],
        cwd=cwd,
        check=False,
        capture_output=True,
        timeout=120,
    )


def _load_cli_module():
    spec = importlib.util.spec_from_file_location("metadata_v2_cli_test", CLI_PATH)
    assert spec is not None and spec.loader is not None
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    return cli


def test_cli_defaults_to_stdout_without_an_implicit_retained_write(
    capfd: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    candidate = _load(METADATA_PATH)
    readiness = _load(READINESS_PATH)
    cli = _load_cli_module()
    monkeypatch.setattr(
        cli,
        "_build_candidate_epoch_metadata_v2_with_readiness",
        lambda **_kwargs: (candidate, readiness),
    )
    retained = (METADATA_PATH, READINESS_PATH)
    before = {
        path: (path.exists(), sha256(path.read_bytes()).hexdigest())
        for path in retained
        if path.exists()
    }
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", [str(CLI_PATH)])
    cli.main()
    captured = capfd.readouterr()
    assert captured.err == ""
    assert captured.out.encode("utf-8") == canonical_document_bytes(candidate)
    for path in retained:
        if path in before:
            assert path.is_file()
            assert sha256(path.read_bytes()).hexdigest() == before[path][1]
        else:
            assert not path.exists()


def test_cli_explicit_outputs_are_atomic_deterministic_and_check_is_read_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    candidate = _load(METADATA_PATH)
    readiness = _load(READINESS_PATH)
    cli = _load_cli_module()
    monkeypatch.setattr(
        cli,
        "_build_candidate_epoch_metadata_v2_with_readiness",
        lambda **_kwargs: (candidate, readiness),
    )
    monkeypatch.chdir(tmp_path)
    output = tmp_path / "metadata.json"
    report = tmp_path / "readiness.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [str(CLI_PATH), "--output", str(output), "--report", str(report)],
    )
    cli.main()
    assert output.read_bytes() == canonical_document_bytes(candidate)
    assert report.read_bytes() == canonical_document_bytes(readiness)
    before = (output.read_bytes(), report.read_bytes())
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(CLI_PATH),
            "--check",
            "--output",
            str(output),
            "--report",
            str(report),
        ],
    )
    cli.main()
    assert (output.read_bytes(), report.read_bytes()) == before

    output.write_bytes(b"stale\n")
    monkeypatch.setattr(
        sys,
        "argv",
        [str(CLI_PATH), "--check", "--output", str(output)],
    )
    with pytest.raises(cli.LibraryEpochMetadataV2Error):
        cli.main()
    assert output.read_bytes() == b"stale\n"
    monkeypatch.setattr(sys, "argv", [str(CLI_PATH), "--check"])
    with pytest.raises(SystemExit):
        cli.main()


def test_cli_rejects_partial_publication_existing_targets_and_symlink_parents(
    tmp_path: Path,
) -> None:
    output = tmp_path / "must-not-appear.json"
    existing_report = tmp_path / "existing-readiness.json"
    existing_report.write_bytes(b"sentinel\n")
    failed = _run_cli(
        "--output", output, "--report", existing_report, cwd=tmp_path
    )
    assert failed.returncode != 0
    assert not output.exists()
    assert existing_report.read_bytes() == b"sentinel\n"

    same = tmp_path / "same.json"
    same.write_bytes(b"same-sentinel\n")
    failed = _run_cli("--output", same, "--report", same, cwd=tmp_path)
    assert failed.returncode != 0
    assert same.read_bytes() == b"same-sentinel\n"

    target = tmp_path / "target.json"
    target.write_bytes(b"target-sentinel\n")
    linked = tmp_path / "linked-output.json"
    linked.symlink_to(target)
    failed = _run_cli("--output", linked, cwd=tmp_path)
    assert failed.returncode != 0
    assert linked.is_symlink()
    assert target.read_bytes() == b"target-sentinel\n"

    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    sentinel = real_parent / "sentinel"
    sentinel.write_bytes(b"unchanged\n")
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    linked_output = linked_parent / "metadata.json"
    failed = _run_cli("--output", linked_output, cwd=tmp_path)
    assert failed.returncode != 0
    assert not (real_parent / "metadata.json").exists()
    assert sentinel.read_bytes() == b"unchanged\n"


def test_cli_publish_primitive_preserves_racing_inode_and_cleans_staging(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    spec = importlib.util.spec_from_file_location("metadata_v2_cli_unit", CLI_PATH)
    assert spec is not None and spec.loader is not None
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    output = tmp_path / "metadata.json"
    report = tmp_path / "readiness.json"
    real_link = os.link
    calls = 0
    racing_identity: tuple[int, int] | None = None

    def racing_link(
        source: object, destination: object, *args: object, **kwargs: object
    ) -> None:
        nonlocal calls, racing_identity
        calls += 1
        if calls == 2:
            destination_path = Path(destination)
            destination_path.write_bytes(b"race-sentinel\n")
            identity = destination_path.lstat()
            racing_identity = (identity.st_dev, identity.st_ino)
        real_link(source, destination, *args, **kwargs)

    monkeypatch.setattr(cli.os, "link", racing_link)
    with pytest.raises(cli.LibraryEpochMetadataV2Error):
        cli._publish_all([(output, b"metadata\n"), (report, b"readiness\n")])
    assert not output.exists()
    assert report.read_bytes() == b"race-sentinel\n"
    identity = report.lstat()
    assert (identity.st_dev, identity.st_ino) == racing_identity
    assert not list(tmp_path.glob(".*.tmp"))
