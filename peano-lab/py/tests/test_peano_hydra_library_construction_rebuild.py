"""Adversarial contracts for the candidate-only Hydra A2.2 rebuild evidence."""

from __future__ import annotations

import base64
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from peano_lab.kernel.artifact_codec import (  # noqa: E402
    decode_artifact,
    encode_artifact,
    encode_formula,
    encode_proof,
)
from peano_lab.kernel.checker import check  # noqa: E402
from peano_lab.kernel.formulas import Eq  # noqa: E402
from peano_lab.kernel.proofs import Cut, EqRefl  # noqa: E402
from peano_lab.kernel.terms import Zero  # noqa: E402
from peano_lab.library.candidate_validation import compile_candidate_body  # noqa: E402
from peano_lab.library.theorems import THEOREMS, TheoremSpec, _closed_formula  # noqa: E402
import training.peano_hydra.library_construction_rebuild as rebuild  # noqa: E402
from training.peano_hydra.library_construction_rebuild_core import (  # noqa: E402
    ConstructionRebuildCoreError,
    DependencyCertificate,
    compile_closed_candidate,
)


CLI_PATH = ROOT / "scripts/build_peano_hydra_library_construction_rebuild.py"
RETAINED = ROOT / "artifacts/peano-hydra/l0-construction-rebuild-candidate-v1.json"
RETAINED_BYTES = 3_106_352
RETAINED_SHA256 = "6176c44a63f791bc27ddd550aa915db6e78c8fbf9f9f0918299f1b3f639fc182"
RETAINED_ROOT_SHA256 = "91ecc6b4bb22f4b46cdfa3fcdd2401dce47d8fef38c15101d221c207fd7793b0"
RETAINED_RECORD_ROOT_SHA256 = (
    "42d718621f91b52bf55a7909751eab695fefd28da2989863de50470d14397ef5"
)
AUDIT = ROOT / "artifacts/peano-hydra/l0-dependency-audit-candidate-v1.json"
REPLAY_ROOT = ROOT / "artifacts/peano-hydra/l0-replay-candidate-v1"
REPLAY_MANIFEST = REPLAY_ROOT / "manifest.json"
REPLAY_CATALOG = REPLAY_ROOT / "catalog.json"
REPLAY_REPORT = ROOT / "artifacts/peano-hydra/l0-replay-candidate-v1-report.json"

EXPECTED = (
    {
        "index": 256,
        "name": "odd_add_odd",
        "omitted": "add_succ_left",
        "candidate": ("mul_add", "add_assoc", "add_comm"),
        "closure_sha256": "a4abec5d9eb955ed95f6eea761c96c3de0166b3df3c64fe8e898d8766ed5c5f2",
        "statement_sha256": "bd3780bb05fa5b37c137f073d0824b16479e754d20ae5a2088784b2161e92376",
        "script_sha256": "4d303cb1b7886cceba15a4d29f198ca16eff7aabca04ca577ae48d06878eed59",
        "formula_sha256": "4d2aa6b4e387657e562641830dab2953890b5493d6e6858b6c36d73b06786c31",
        "proof_sha256": "4067a32d9787024c486b6162a041556a9a07620630d6507920e760eb99f4b996",
        "source_sha256": "0f2e21830809793776988b87d20012d6d7524ad96417115b6966383be28dae55",
        "artifact_sha256": "8064d28bd99adbaa1cde42c7ebd0f94880b345c889d6afc18e4b607749310ecc",
        "artifact_bytes": 13_640,
        "fuel": 2_208,
        "metrics": (274, 31, 6),
    },
    {
        "index": 376,
        "name": "finite_bounded_injective_surjective",
        "omitted": "beta_at_unique",
        "candidate": (
            "finite_surjective_zero",
            "finite_contains_decidable",
            "finite_bounded_last_succ",
            "beta_prefix_swap_last_from_entries",
            "finite_swap_last_bounded",
            "finite_swap_last_injective",
            "finite_bounded_prefix_without_top",
            "finite_injective_prefix_succ",
            "finite_surjective_succ_from_prefix",
            "finite_swap_last_surjective_back",
            "finite_no_top_successor_gate",
            "le_succ",
            "le_refl",
            "lt_irrefl_expanded",
        ),
        "closure_sha256": "a5b1ba200b4fe2f77c86a3b98e4870e05e178e0b21498f303b56a1ad61060363",
        "statement_sha256": "9e0cad653da9de17ab7bbac3cb3bf49bc6d4a1304bda508669943b25fd247257",
        "script_sha256": "6f501cc65ba7d78844c5dd6f42463be97c89b32c6dc2e19d40236a7618315533",
        "formula_sha256": "a0e3d1080e2fdda1b5043ddab641542573ac0d54c85f050c9b1c0f68ca0c7e61",
        "proof_sha256": "3e2b64d254224aa6a13af069c74422d4a00ac85ebe73d0e939afcfa36316b33b",
        "source_sha256": "18e4bd24e78fc5955097d43dd4240718e164cfe6f8a2c1839f3e4b35f6e89f05",
        "artifact_sha256": "623865d90504af44cddca3d76ac4f009be8aa289e80d2785b72b121a52954504",
        "artifact_bytes": 1_870_657,
        "fuel": 330_744,
        "metrics": (41_341, 89, 1_235),
    },
    {
        "index": 379,
        "name": "beta_product_swap_last_invariant",
        "omitted": "le_refl",
        "candidate": (
            "beta_product_replace_balance",
            "beta_product_succ_decompose",
            "beta_at_unique",
            "le_succ",
            "lt_irrefl_expanded",
        ),
        "closure_sha256": "18c328d9374661586958db5e47441f49783a86d158afc0ac066d28f58c5bab37",
        "statement_sha256": "a23f0b2f4451b4e423b9f15132ac02b6a035ce4d06f8eb95d744977109272465",
        "script_sha256": "b84a265093efa741e13cb8ac729dc53ce9baca8710dd51fac2b6c17534e373ed",
        "formula_sha256": "bcb808230bb4f3f4e84416a5371d98f0809220ec499ff67b396d4ec1d717482d",
        "proof_sha256": "8e475f89c515bb4f56c6f0ce8adb64693805b835e80d408442f6e1e4520d0e5c",
        "source_sha256": "898ef3301a30ec69805b61d83791785877e1190e94809a2cec791f67b0f111cd",
        "artifact_sha256": "507940a3e456122fadb3b43d34891a70c91baa87615be80c1fca059e9ebd82df",
        "artifact_bytes": 386_189,
        "fuel": 59_320,
        "metrics": (7_413, 67, 203),
    },
)

PUBLIC_INPUT_HASHES = {
    "peano-lab/py/peano_lab/library/theorems.py": "bfa6fad2c91a774b37c3ee458e9b59d679f7257a1ab4b2bef3f88bbccdb82a2f",
    "artifacts/peano-hydra/l0-replay-candidate-v1/manifest.json": "8b9f9dc8e35e5eb02e43bcffd6aed6280006f4a01c396e43c43c2cbe4cbfb604",
    "artifacts/peano-hydra/l0-replay-candidate-v1/catalog.json": "326ffe660da6e34a3aa12e0aa13096078a0bf20c45c440049aaf5d5bed1f1be7",
    "artifacts/peano-hydra/l0-replay-candidate-v1-report.json": "35f5547978a4d58c5af30c33d253c92af494b94f6d6500a866a13f2fd1fa7f10",
    "artifacts/peano-hydra/l0-dependency-audit-candidate-v1.json": "4b867bb1ce0161e6392f29d9262e035929e5da86b224063546a2a42c17fd9040",
    "artifacts/peano-hydra/library-epoch-metadata-candidate-v1.json": "e719dd526d0aa07e2521fb2e499f2ee6810506d32a912298f11dbac60a2c0289",
    "artifacts/peano-hydra/library-epoch-metadata-candidate-v2.json": "dc6a59ce08397eba698651f6ed4faac0533dec55c13d5a8ca49d863d19d7b72d",
}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _load_cli():
    specification = importlib.util.spec_from_file_location(
        "_test_peano_hydra_construction_rebuild_cli", CLI_PATH
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _script_sha256(script: tuple[str, ...]) -> str:
    return _sha(("\n".join(script) + "\n").encode("utf-8"))


def _transitive_closure(
    direct: tuple[str, ...], table: dict[str, TheoremSpec]
) -> tuple[str, ...]:
    reachable: set[str] = set()
    pending = list(direct)
    while pending:
        name = pending.pop()
        if name in reachable:
            continue
        reachable.add(name)
        pending.extend(table[name].dependencies)
    return tuple(spec.name for spec in THEOREMS if spec.name in reachable)


def _retained_document() -> dict[str, object]:
    raw = RETAINED.read_bytes()
    return rebuild._decode_document(
        raw, "retained A2.2 rebuild", limit=rebuild.MAX_DOCUMENT_BYTES
    )


def _fully_reroot(value: dict[str, object]) -> dict[str, object]:
    """Rehash every public record/root layer after an adversarial mutation."""

    rows = value["theorems"]
    assert type(rows) is list
    for row in rows:
        assert type(row) is dict
        row["record_sha256"] = rebuild._record_hash(row)
    identities = [
        {
            "index": row["index"],
            "name": row["name"],
            "record_sha256": row["record_sha256"],
        }
        for row in rows
    ]
    records_preimage = {
        "format": rebuild.THEOREM_RECORDS_PREIMAGE_FORMAT,
        "records": identities,
        "v": 1,
    }
    value["theorem_records"] = {
        "count": len(rows),
        "preimage": records_preimage,
        "root_sha256": rebuild._sha256_json(records_preimage),
    }
    body = {
        key: item
        for key, item in value.items()
        if key not in {"root_preimage", "root_sha256", "theorems"}
    }
    root_preimage = {
        "format": rebuild.CONSTRUCTION_REBUILD_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": rebuild.CONSTRUCTION_REBUILD_VERSION,
    }
    value["root_preimage"] = root_preimage
    value["root_sha256"] = rebuild._sha256_json(root_preimage)
    return value


def test_schema_is_canonical_pinned_and_has_only_candidate_authority() -> None:
    raw = rebuild.CONSTRUCTION_REBUILD_SCHEMA_PATH.read_bytes()
    assert _sha(raw) == (
        "d1fc09c035e28f96913cdadd63f17c853901fc8dcd2e17df3a094a919612bf9f"
    )
    assert _sha(raw) == rebuild.construction_rebuild_schema_identity()[
        "artifact_sha256"
    ]
    schema = rebuild.construction_rebuild_schema()
    assert raw == rebuild.canonical_document_bytes(
        schema, limit=rebuild.MAX_SCHEMA_BYTES
    )
    identity = rebuild.construction_rebuild_schema_identity()
    assert identity["artifact_sha256"] == _sha(raw)
    assert identity["sha256"] == rebuild.CONSTRUCTION_REBUILD_SCHEMA_SHA256 == (
        "a189ad140f5e7093f11a2f433705d4dafb71d474672e822cf39e45dbeb1ca571"
    )
    assert schema["constants"] == {
        "a2_complete": False,
        "candidate_direct_dependency_edges_across_three_rebuilds": 22,
        "dependency_vectors_complete": False,
        "evaluation_eligible": False,
        "freeze_ready": False,
        "lineage_complete": False,
        "logic_mode": "intuitionistic",
        "minimality_claim": False,
        "optimized_best_known": False,
        "optimized_vector_independently_audited": False,
        "publication_ready": False,
        "publication_union_complete": False,
        "publication_union_verified": False,
        "rebuilt_theorem_count": 3,
        "retained_direct_dependency_edges_across_three_rebuilds": 25,
        "retained_public_graph_edges": 1_038,
        "retrieval_eligible": False,
        "review_complete": False,
        "status": "candidate",
        "training_eligible": False,
    }
    assert tuple(
        (row["index"], row["name"], tuple(row["candidate_dependencies"]))
        for row in schema["required_theorems"]
    ) == tuple(
        (row["index"], row["name"], row["candidate"]) for row in EXPECTED
    )


def test_public_surface_has_no_freeze_publish_or_fast_validation_entrypoint() -> None:
    assert set(rebuild.__all__) == {
        "CONSTRUCTION_REBUILD_SCHEMA_FORMAT",
        "CONSTRUCTION_REBUILD_SCHEMA_ID",
        "CONSTRUCTION_REBUILD_SCHEMA_PATH",
        "CONSTRUCTION_REBUILD_SCHEMA_SHA256",
        "CONSTRUCTION_REBUILD_SCHEMA_VERSION",
        "LibraryConstructionRebuildError",
        "build_candidate_construction_rebuild",
        "canonical_document_bytes",
        "construction_rebuild_schema",
        "construction_rebuild_schema_identity",
        "load_construction_rebuild",
        "validate_construction_rebuild",
    }
    assert not any(
        name in rebuild.__all__
        for name in (
            "freeze",
            "publish",
            "admit",
            "minimal",
            "best_known",
            "optimize",
            "fast_validate",
        )
    )


def test_strict_decoder_rejects_duplicate_floating_and_noncanonical_json() -> None:
    with pytest.raises(rebuild.LibraryConstructionRebuildError, match="duplicate"):
        rebuild._decode_document(b'{"x":1,"x":2}\n', "fixture", limit=100)
    with pytest.raises(rebuild.LibraryConstructionRebuildError, match="floating"):
        rebuild._decode_document(b'{"x":1.5}\n', "fixture", limit=100)
    with pytest.raises(rebuild.LibraryConstructionRebuildError, match="canonical"):
        rebuild._decode_document(b'{"x":1}\n', "fixture", limit=100)


def test_canonical_encoder_rejects_floats_cycles_and_boolean_limits() -> None:
    with pytest.raises(rebuild.LibraryConstructionRebuildError, match="unsupported"):
        rebuild.canonical_document_bytes({"x": 1.5})
    cyclic: list[object] = []
    cyclic.append(cyclic)
    with pytest.raises(rebuild.LibraryConstructionRebuildError, match="cycle"):
        rebuild.canonical_document_bytes(cyclic)
    with pytest.raises(rebuild.LibraryConstructionRebuildError, match="limit"):
        rebuild.canonical_document_bytes({}, limit=True)


def test_small_core_fixture_closes_only_with_exact_checked_dependencies() -> None:
    dependency = TheoremSpec(
        "dependency_fixture",
        "forall n. n = n",
        (),
        ("intro n", "refl"),
        "Fixture dependency.",
    )
    consumer = TheoremSpec(
        "consumer_fixture",
        "forall n. n = n",
        (dependency.name,),
        ("exact dependency_fixture",),
        "Fixture consumer.",
    )
    dependency_body = compile_candidate_body(dependency, core={})
    carrier = DependencyCertificate(
        dependency.name,
        _closed_formula(dependency.statement),
        dependency_body.certificate,
    )
    compiled = compile_closed_candidate(
        consumer,
        core={dependency.name: dependency},
        dependency_certificates={dependency.name: carrier},
    )
    assert check((), compiled.proof, _closed_formula(consumer.statement))

    with pytest.raises(ConstructionRebuildCoreError, match="names differ"):
        compile_closed_candidate(
            consumer,
            core={dependency.name: dependency},
            dependency_certificates={},
        )


def test_retained_public_library_and_all_a21_inputs_are_byte_unchanged() -> None:
    for relative, expected in PUBLIC_INPUT_HASHES.items():
        assert _sha((ROOT / relative).read_bytes()) == expected
    assert len(THEOREMS) == 384
    assert sum(len(spec.dependencies) for spec in THEOREMS) == 1_038


def test_live_selected_sources_have_exact_order_statement_script_and_vectors() -> None:
    for expected in EXPECTED:
        spec = THEOREMS[expected["index"]]
        assert spec.name == expected["name"]
        assert _sha(spec.statement.encode("utf-8")) == expected["statement_sha256"]
        assert _script_sha256(spec.script) == expected["script_sha256"]
        assert expected["omitted"] in spec.dependencies
        assert tuple(
            name for name in spec.dependencies if name != expected["omitted"]
        ) == expected["candidate"]


def test_removed_names_are_only_directly_absent_and_remain_transitively_reachable() -> None:
    table = {spec.name: spec for spec in THEOREMS}
    for expected in EXPECTED:
        closure = _transitive_closure(expected["candidate"], table)
        assert expected["omitted"] not in expected["candidate"]
        assert expected["omitted"] in closure
        assert _sha("".join(f"{name}\n" for name in closure).encode("utf-8")) == (
            expected["closure_sha256"]
        )


def test_fresh_import_does_not_load_candidate_campaign_modules() -> None:
    code = r'''
import sys
import training.peano_hydra.library_construction_rebuild
forbidden = [
    name for name in sys.modules
    if 'quadratic_reciprocity_stack' in name
    or name.rsplit('.', 1)[-1].endswith('_candidate')
]
if forbidden:
    raise SystemExit(repr(sorted(forbidden)))
'''
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        (str(ROOT / "peano-lab" / "py"), str(ROOT))
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_retained_document_is_canonical_and_one_fresh_reconstruction_matches() -> None:
    raw = RETAINED.read_bytes()
    assert len(raw) == RETAINED_BYTES
    assert _sha(raw) == RETAINED_SHA256
    value = rebuild.load_construction_rebuild(RETAINED, repository_root=ROOT)
    assert raw == rebuild.canonical_document_bytes(value)
    assert value == _retained_document()
    assert value["root_sha256"] == RETAINED_ROOT_SHA256
    assert value["theorem_records"]["root_sha256"] == RETAINED_RECORD_ROOT_SHA256


def test_retained_rows_pin_exact_vectors_hashes_metrics_and_empty_context_qeds() -> None:
    value = _retained_document()
    rows = value["theorems"]
    assert [(row["index"], row["name"]) for row in rows] == [
        (row["index"], row["name"]) for row in EXPECTED
    ]
    metric_keys = ("proof_nodes", "proof_depth", "cut_nodes")
    for row, expected in zip(rows, EXPECTED, strict=True):
        rebuilt = row["rebuilt_certificate"]
        assert tuple(row["candidate_direct_dependencies"]) == expected["candidate"]
        assert row["direct_cut_spine"]["dependencies"] == list(expected["candidate"])
        assert row["direct_cut_spine"]["omitted_direct_dependency"] == expected["omitted"]
        assert rebuilt["artifact_bytes"] == expected["artifact_bytes"]
        assert rebuilt["artifact_sha256"] == expected["artifact_sha256"]
        assert rebuilt["fuel"] == expected["fuel"]
        assert rebuilt["formula_sha256"] == expected["formula_sha256"]
        assert rebuilt["proof_term_sha256"] == expected["proof_sha256"]
        assert rebuilt["source_certificate_sha256"] == expected["source_sha256"]
        assert tuple(rebuilt["construction_metrics"][key] for key in metric_keys) == (
            expected["metrics"]
        )
        assert rebuilt["construction_metrics_basis"] == (
            "non-comparable-schedule-dependent-python-object-alias-observation"
        )
        assert rebuilt["identity_metrics_comparable"] is False
        assert rebuilt["identity_metrics_claim"] == (
            "observation-only-schedule-and-assembly-dependent"
        )
        observations = rebuilt["construction_metrics"]
        assert observations["proof_edges"] == (
            observations["distinct_proof_objects"]
            + observations["reused_proof_references"]
            - 1
        )
        assert rebuilt["packed_tree_metrics"] == {
            "cut_nodes": expected["metrics"][2],
            "proof_depth": expected["metrics"][1],
            "proof_nodes": expected["metrics"][0],
        }

        artifact = base64.b64decode(rebuilt["artifact_base64"], validate=True)
        assert len(artifact) == expected["artifact_bytes"]
        assert _sha(artifact) == expected["artifact_sha256"]
        fuel, target, proof = decode_artifact(
            artifact,
            max_bytes=rebuild.MAX_ARTIFACT_BYTES,
            max_nodes=1_000_000,
            max_depth=512,
        )
        original = _closed_formula(THEOREMS[expected["index"]].statement)
        assert fuel == expected["fuel"]
        assert target == original
        assert encode_artifact(fuel, target, proof) == artifact
        assert _sha(encode_formula(target)) == expected["formula_sha256"]
        assert _sha(encode_proof(proof)) == expected["proof_sha256"]
        assert check((), proof, original)


def test_decoded_outer_cut_spines_are_exactly_the_selected_direct_dependencies() -> None:
    """Inspect proof structure rather than trusting the vector sidecar fields."""

    value = _retained_document()
    manifest = json.loads(REPLAY_MANIFEST.read_bytes())
    replay_rows = {row["name"]: row for row in manifest["theorems"]}
    theorem_table = {spec.name: spec for spec in THEOREMS}

    for row, expected in zip(value["theorems"], EXPECTED, strict=True):
        artifact = base64.b64decode(
            row["rebuilt_certificate"]["artifact_base64"], validate=True
        )
        _fuel, target, cursor = decode_artifact(
            artifact,
            max_bytes=rebuild.MAX_ARTIFACT_BYTES,
            max_nodes=1_000_000,
            max_depth=512,
        )
        original_target = _closed_formula(
            theorem_table[expected["name"]].statement
        )
        omitted_target = _closed_formula(
            theorem_table[expected["omitted"]].statement
        )
        assert target == original_target

        observed_names: list[str] = []
        observed_propositions = []
        for dependency_name in expected["candidate"]:
            assert type(cursor) is Cut
            dependency_target = _closed_formula(
                theorem_table[dependency_name].statement
            )
            pinned = replay_rows[dependency_name]
            assert cursor.proposition == dependency_target
            assert cursor.conclusion == original_target
            assert _sha(encode_proof(cursor.lemma)) == pinned["proof_term_sha256"]
            assert check((), cursor.lemma, dependency_target)
            observed_names.append(dependency_name)
            observed_propositions.append(cursor.proposition)
            cursor = cursor.body

        assert type(cursor) is not Cut
        assert tuple(observed_names) == expected["candidate"]
        assert expected["omitted"] not in observed_names
        assert omitted_target not in observed_propositions


def test_retained_rows_join_exact_source_a21_and_replay_records() -> None:
    value = _retained_document()
    audit = json.loads(AUDIT.read_bytes())
    manifest = json.loads(REPLAY_MANIFEST.read_bytes())
    audit_rows = {row["name"]: row for row in audit["theorems"]}
    replay_rows = {row["name"]: row for row in manifest["theorems"]}

    for row, expected in zip(value["theorems"], EXPECTED, strict=True):
        spec = THEOREMS[expected["index"]]
        audited = audit_rows[spec.name]
        replayed = replay_rows[spec.name]
        assert row["original"] == {
            "formula_sha256": replayed["formula_sha256"],
            "script": list(spec.script),
            "script_sha256": replayed["script_sha256"],
            "statement_source": spec.statement,
            "statement_source_sha256": replayed["statement_source_sha256"],
        }
        assert tuple(row["retained_direct_dependencies"]) == spec.dependencies
        assert row["a2_1"]["audit_record_sha256"] == audited["record_sha256"]
        assert row["a2_1"]["requires_certificate_rebuild_before"] is True
        assert row["submitted_certificate"] == {
            "artifact_bytes": replayed["artifact"]["bytes"],
            "artifact_sha256": replayed["artifact"]["sha256"],
            "construction_metrics": replayed["construction_metrics"],
            "construction_metrics_basis": (
                "non-comparable-retained-source-python-object-alias-observation"
            ),
            "identity_metrics_comparable": False,
            "proof_term_sha256": replayed["proof_term_sha256"],
        }
        assert [item["name"] for item in row["direct_cut_spine"]["dependency_artifacts"]] == (
            list(expected["candidate"])
        )
        for receipt in row["direct_cut_spine"]["dependency_artifacts"]:
            dependency = replay_rows[receipt["name"]]
            assert receipt == {
                "artifact_sha256": dependency["artifact"]["sha256"],
                "formula_sha256": dependency["formula_sha256"],
                "index": dependency["index"],
                "name": dependency["name"],
                "proof_term_sha256": dependency["proof_term_sha256"],
            }


def test_retained_claim_boundary_keeps_every_authority_false() -> None:
    value = _retained_document()
    assert value["aggregate"] == {
        "artifact_bytes_delta_total": -49_483,
        "candidate_direct_dependency_edges_across_three_rebuilds": 22,
        "cut_nodes_delta_total": -34,
        "direct_edges_removed_in_candidate_rebuilds": 3,
        "proof_nodes_delta_total": -1_176,
        "rebuilt_theorem_count": 3,
        "retained_direct_dependency_edges_across_three_rebuilds": 25,
        "retained_public_graph_edges": 1_038,
        "transitively_reachable_omitted_names": 3,
    }
    for field in (
        "a2_complete",
        "dependency_vectors_complete",
        "evaluation_eligible",
        "freeze_ready",
        "lineage_complete",
        "minimality_claim",
        "optimized_best_known",
        "optimized_vector_independently_audited",
        "publication_ready",
        "publication_union_complete",
        "publication_union_verified",
        "retrieval_eligible",
        "review_complete",
        "training_eligible",
    ):
        assert value[field] is False
    assert value["status"] == "candidate"
    for row in value["theorems"]:
        assert row["construction_rebuild_complete"] is True
        for field in (
            "a2_complete",
            "dependency_vectors_complete",
            "lineage_complete",
            "minimality_claim",
            "optimized_best_known",
            "optimized_vector_independently_audited",
            "public_graph_applied",
            "publication_union_complete",
            "publication_union_verified",
            "review_complete",
        ):
            assert row[field] is False
        assert row["comparison"]["claim"] == "descriptive-predecessor-delta-only"
        assert row["comparison"]["metric_basis"] == (
            "canonical-artifact-and-intrinsic-proof-tree-only"
        )
        assert set(row["comparison"]["delta_rebuilt_minus_submitted"]) == {
            "artifact_bytes",
            "cut_nodes",
            "proof_depth",
            "proof_nodes",
        }
        assert row["rebuilt_certificate"]["kernel_context"] == "empty"
        assert row["rebuilt_certificate"]["kernel_accepted"] is True


def test_retained_closure_receipts_do_not_make_false_lemma_free_claims() -> None:
    value = _retained_document()
    table = {spec.name: spec for spec in THEOREMS}
    for row, expected in zip(value["theorems"], EXPECTED, strict=True):
        closure = _transitive_closure(expected["candidate"], table)
        assert row["transitive_closure"] == {
            "dependency_count": len(closure),
            "dependencies_in_replay_order": list(closure),
            "lf_sha256": expected["closure_sha256"],
            "omitted_direct_dependency": expected["omitted"],
            "omitted_name_still_reachable": True,
            "source_graph": "retained-1038-edge-replay-manifest",
        }
        assert expected["omitted"] in closure


def test_fully_rerooted_forged_fields_still_fail_exact_reconstruction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    retained = _retained_document()
    monkeypatch.setattr(
        rebuild,
        "_build_candidate_construction_rebuild",
        lambda _root: deepcopy(retained),
    )

    mutators = (
        lambda value: value.__setitem__("publication_ready", True),
        lambda value: value.__setitem__("optimized_best_known", True),
        lambda value: value["theorems"][0].__setitem__("name", "forged"),
        lambda value: value["theorems"][0]["candidate_direct_dependencies"].append(
            "add_succ_left"
        ),
        lambda value: value["theorems"][0]["original"]["script"].append("refl"),
        lambda value: value["theorems"][0]["a2_1"].__setitem__(
            "audit_record_sha256", "0" * 64
        ),
        lambda value: value["theorems"][0]["direct_cut_spine"][
            "dependency_artifacts"
        ][0].__setitem__("proof_term_sha256", "0" * 64),
        lambda value: value["theorems"][0]["rebuilt_certificate"].__setitem__(
            "formula_sha256", "0" * 64
        ),
        lambda value: value["theorems"][0]["rebuilt_certificate"][
            "construction_metrics"
        ].__setitem__("proof_nodes", 1),
        lambda value: value["theorems"][0]["transitive_closure"].__setitem__(
            "omitted_name_still_reachable", False
        ),
    )
    for mutate in mutators:
        forged = deepcopy(retained)
        mutate(forged)
        _fully_reroot(forged)
        with pytest.raises(
            rebuild.LibraryConstructionRebuildError,
            match="fixed-source reconstruction",
        ):
            rebuild.validate_construction_rebuild(forged, repository_root=ROOT)


def test_mutated_embedded_certificate_fails_even_after_all_public_hashes_are_updated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    retained = _retained_document()
    forged = deepcopy(retained)
    certificate = forged["theorems"][0]["rebuilt_certificate"]
    zero = Zero()
    foreign_target = Eq(zero, zero)
    foreign_proof = EqRefl(zero)
    raw = encode_artifact(24, foreign_target, foreign_proof)
    assert check((), foreign_proof, foreign_target)
    assert not check(
        (), foreign_proof, _closed_formula(THEOREMS[EXPECTED[0]["index"]].statement)
    )
    certificate["artifact_base64"] = base64.b64encode(raw).decode("ascii")
    certificate["artifact_bytes"] = len(raw)
    certificate["artifact_sha256"] = _sha(raw)
    certificate["fuel"] = 24
    certificate["formula_sha256"] = _sha(encode_formula(foreign_target))
    certificate["proof_term_sha256"] = _sha(encode_proof(foreign_proof))
    _fully_reroot(forged)
    monkeypatch.setattr(
        rebuild,
        "_build_candidate_construction_rebuild",
        lambda _root: deepcopy(retained),
    )
    with pytest.raises(rebuild.LibraryConstructionRebuildError, match="fixed-source"):
        rebuild.validate_construction_rebuild(forged, repository_root=ROOT)


def test_fixed_loader_rejects_runtime_checker_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(rebuild, "check", lambda *_args: True)
    with pytest.raises(
        rebuild.LibraryConstructionRebuildError,
        match="runtime callable drifted",
    ):
        rebuild._load_fixed_inputs(ROOT)


def test_fixed_loader_independently_rejects_core_source_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = rebuild._safe_file

    def tampered(path: Path, *, label: str, limit: int) -> bytes:
        raw = original(path, label=label, limit=limit)
        if label == "construction-rebuild core":
            return raw + b"\n"
        return raw

    monkeypatch.setattr(rebuild, "_safe_file", tampered)
    with pytest.raises(
        rebuild.LibraryConstructionRebuildError,
        match="construction-rebuild core drifted",
    ):
        rebuild._load_fixed_inputs(ROOT)


def test_cli_publish_is_create_only_atomic_regular_and_exact(tmp_path: Path) -> None:
    cli = _load_cli()
    destination = tmp_path / "rebuild.json"
    raw = b'{"fixture":true}\n'
    cli._publish(destination, raw)

    metadata = destination.lstat()
    assert stat.S_ISREG(metadata.st_mode)
    assert not stat.S_ISLNK(metadata.st_mode)
    assert destination.read_bytes() == raw
    cli._read_exact(destination, raw)
    with pytest.raises(rebuild.LibraryConstructionRebuildError, match="already exists"):
        cli._publish(destination, b"replacement\n")
    assert destination.read_bytes() == raw


def test_cli_publish_race_preserves_foreign_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli = _load_cli()
    destination = tmp_path / "rebuild.json"
    sentinel = b"foreign-writer\n"
    real_link = os.link

    def raced_link(source, target, *, follow_symlinks=False):
        Path(target).write_bytes(sentinel)
        return real_link(source, target, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(cli.os, "link", raced_link)
    with pytest.raises(
        rebuild.LibraryConstructionRebuildError,
        match="cannot publish output document",
    ):
        cli._publish(destination, b"candidate\n")
    assert destination.read_bytes() == sentinel
    assert not tuple(tmp_path.glob(".rebuild.json.*.tmp"))


def test_loader_and_cli_reject_symlinked_file_or_ancestor(tmp_path: Path) -> None:
    cli = _load_cli()
    actual = tmp_path / "actual"
    actual.mkdir()
    target = actual / "rebuild.json"
    target.write_bytes(b"{}\n")
    linked_file = tmp_path / "linked-file.json"
    linked_parent = tmp_path / "linked-parent"
    try:
        linked_file.symlink_to(target)
        linked_parent.symlink_to(actual, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable")

    with pytest.raises(
        rebuild.LibraryConstructionRebuildError,
        match="cannot open|regular file",
    ):
        rebuild.load_construction_rebuild(linked_file, repository_root=ROOT)
    with pytest.raises(
        rebuild.LibraryConstructionRebuildError,
        match="parent contains a link",
    ):
        rebuild.load_construction_rebuild(
            linked_parent / "rebuild.json", repository_root=ROOT
        )
    with pytest.raises(
        rebuild.LibraryConstructionRebuildError,
        match="parent contains a link",
    ):
        cli._read_exact(linked_parent / "rebuild.json", b"{}\n")


def test_loader_and_cli_reject_fifo_without_blocking(tmp_path: Path) -> None:
    if not hasattr(os, "mkfifo") or not hasattr(os, "O_NONBLOCK"):
        pytest.skip("nonblocking FIFOs are unavailable")
    fifo = tmp_path / "rebuild.json"
    os.mkfifo(fifo)
    with pytest.raises(rebuild.LibraryConstructionRebuildError, match="regular file"):
        rebuild.load_construction_rebuild(fifo, repository_root=ROOT)
    cli = _load_cli()
    with pytest.raises(
        rebuild.LibraryConstructionRebuildError,
        match="differs from the deterministic build",
    ):
        cli._read_exact(fifo, b"{}\n")
