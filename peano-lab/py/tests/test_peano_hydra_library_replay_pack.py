"""Adversarial tests for the isolated H1.1 candidate replay pack."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from peano_lab.kernel.artifact_codec import (  # noqa: E402
    encode_artifact,
    encode_formula,
    encode_proof,
)
from peano_lab.kernel.checker import check_classical  # noqa: E402
from peano_lab.kernel.formulas import Bot, Eq, Imp, pretty_formula  # noqa: E402
from peano_lab.kernel.proofs import DNE, EqRefl  # noqa: E402
from peano_lab.kernel.terms import Succ, Zero  # noqa: E402
import training.peano_hydra.library_replay_pack as replay_pack  # noqa: E402


ZERO = Zero()
ATOM = Eq(ZERO, ZERO)
REFL = EqRefl(ZERO)
CLASSICALLY_VALID_DNE = Imp(Imp(Imp(ATOM, Bot()), Bot()), ATOM)
PROFILE_RAW = (ROOT / "training/peano_hydra/semantic-profile-v2.json").read_bytes()
COMMITTED_PACK = ROOT / "artifacts/peano-hydra/l0-replay-candidate-v1"
COMMITTED_REPORT = ROOT / "artifacts/peano-hydra/l0-replay-candidate-v1-report.json"
COMMITTED_MANIFEST_ROOT = (
    "fe6718465fbb5e89154ccfce5c511b51ee296b21568d1759a00dda8a21f8a25d"
)
COMMITTED_REPLAY_ROOT = (
    "88e39a886949e2ef31220397e529871bc907f9cd9311c27dc97710d12ef1e3ba"
)


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _source_metrics(proof) -> dict[str, object]:
    tree = replay_pack.proof_tree_metrics(proof)
    return {
        "cut_nodes": tree["cut_nodes"],
        "distinct_proof_objects": tree["proof_nodes"],
        "proof_depth": tree["proof_depth"],
        "proof_edges": tree["proof_nodes"] - 1,
        "proof_nodes": tree["proof_nodes"],
        "reused_proof_references": 0,
        "source_certificate_representation": (
            replay_pack.SOURCE_CERTIFICATE_REPRESENTATION
        ),
        "source_certificate_sha256": _sha(repr(proof).encode("utf-8")),
    }


def _fixture(
    *,
    statement: str = "0 = 0",
    target=ATOM,
    proof=REFL,
    artifact_target=None,
):
    artifact_target = target if artifact_target is None else artifact_target
    tree = replay_pack.proof_tree_metrics(proof)
    fuel = replay_pack.FUEL_MULTIPLIER * tree["proof_nodes"] + replay_pack.FUEL_OFFSET
    artifact = encode_artifact(fuel, artifact_target, proof)
    artifact_hash = _sha(artifact)
    script = ["refl"]
    statement_hash = _sha(statement.encode("utf-8"))
    source_metrics = _source_metrics(proof)
    catalog_row = {
        "certificate_representation": replay_pack.SOURCE_CERTIFICATE_REPRESENTATION,
        "certificate_sha256": source_metrics["source_certificate_sha256"],
        "cut_nodes": source_metrics["cut_nodes"],
        "dependencies": [],
        "distinct_proof_objects": source_metrics["distinct_proof_objects"],
        "index": 0,
        "layer": "test",
        "name": "zero_reflexive_fixture",
        "proof_depth": source_metrics["proof_depth"],
        "proof_edges": source_metrics["proof_edges"],
        "proof_nodes": source_metrics["proof_nodes"],
        "reused_proof_references": source_metrics["reused_proof_references"],
        "script": script,
        "script_sha256": _sha(b"refl\n"),
        "statement": statement,
        "statement_sha256": statement_hash,
        "summary": "Synthetic replay-pack fixture.",
    }
    sources = [
        {
            "path": "peano-lab/py/peano_lab/library/theorems.py",
            "sha256": "a" * 64,
        }
    ]
    catalog = {
        "certificate_policy": "synthetic test fixture",
        "certificate_representation": replay_pack.SOURCE_CERTIFICATE_REPRESENTATION,
        "ordered_root_sha256": _sha(
            replay_pack.canonical_json_bytes([catalog_row])
        ),
        "schema": replay_pack.CATALOG_SCHEMA,
        "theorem_count": 1,
        "theorem_source_root_sha256": _sha(
            replay_pack.canonical_document_bytes(
                sources, limit=replay_pack.MAX_CATALOG_BYTES
            )
        ),
        "theorem_sources": sources,
        "theorems": [catalog_row],
    }
    catalog_raw = replay_pack.canonical_document_bytes(
        catalog, limit=replay_pack.MAX_CATALOG_BYTES
    )
    catalog_identity, _ = replay_pack._catalog_from_bytes(catalog_raw)
    profile_identity, _ = replay_pack._profile_identity_from_bytes(PROFILE_RAW)
    canonical_statement = pretty_formula(artifact_target, [])
    row = {
        "artifact": {
            "bytes": len(artifact),
            "fuel": fuel,
            "path": (
                "certificates/0000-zero_reflexive_fixture-"
                f"{artifact_hash}.pl2"
            ),
            "sha256": artifact_hash,
        },
        "construction_metrics": source_metrics,
        "declared_dependencies": [],
        "formula_sha256": _sha(encode_formula(artifact_target)),
        "index": 0,
        "layer": "test",
        "name": "zero_reflexive_fixture",
        "packed_tree_metrics": tree,
        "proof_term_sha256": _sha(encode_proof(proof)),
        "script": script,
        "script_sha256": _sha(b"refl\n"),
        "statement_canonical": canonical_statement,
        "statement_canonical_sha256": _sha(canonical_statement.encode("utf-8")),
        "statement_source": statement,
        "statement_source_sha256": statement_hash,
        "summary": "Synthetic replay-pack fixture.",
    }
    body = {
        "aggregate": {
            "artifact_bytes_maximum": len(artifact),
            "artifact_bytes_total": len(artifact),
            "cut_nodes_total": tree["cut_nodes"],
            "proof_depth_maximum": tree["proof_depth"],
            "proof_nodes_maximum": tree["proof_nodes"],
            "proof_nodes_total": tree["proof_nodes"],
        },
        "certificate_representation": replay_pack.CERTIFICATE_REPRESENTATION,
        "evaluation_eligible": False,
        "format": replay_pack.REPLAY_PACK_FORMAT,
        "id": "synthetic-replay-pack",
        "kernel_identity": replay_pack.live_kernel_identity(),
        "logic_mode": replay_pack.LOGIC_MODE,
        "replay_root_sha256": replay_pack.replay_root_sha256([row]),
        "schema": replay_pack.replay_pack_schema_identity(),
        "semantic_profile": profile_identity,
        "source_catalog": catalog_identity,
        "status": replay_pack.PACK_STATUS,
        "theorem_count": 1,
        "theorems": [row],
        "v": replay_pack.REPLAY_PACK_VERSION,
    }
    manifest = replay_pack.with_manifest_root(body)
    return {
        "artifact_files": {row["artifact"]["path"]: artifact},
        "catalog_raw": catalog_raw,
        "manifest": manifest,
        "profile_raw": PROFILE_RAW,
        "schema_raw": replay_pack.canonical_document_bytes(
            replay_pack.replay_pack_schema(), limit=replay_pack.MAX_SCHEMA_BYTES
        ),
    }


def _write_pack(root: Path, fixture: dict[str, object]) -> None:
    root.mkdir()
    (root / replay_pack.CERTIFICATE_DIRECTORY).mkdir()
    (root / replay_pack.SCHEMA_FILE).write_bytes(fixture["schema_raw"])
    (root / replay_pack.CATALOG_FILE).write_bytes(fixture["catalog_raw"])
    (root / replay_pack.PROFILE_FILE).write_bytes(fixture["profile_raw"])
    (root / replay_pack.MANIFEST_FILE).write_bytes(
        replay_pack.canonical_document_bytes(fixture["manifest"])
    )
    for path, raw in fixture["artifact_files"].items():
        (root / path).write_bytes(raw)


def _reroot(manifest: dict[str, object]) -> dict[str, object]:
    body = {
        key: value
        for key, value in manifest.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    return replay_pack.with_manifest_root(body)


def _isolated_cli_prefix(tmp_path: Path, cache_name: str) -> list[str]:
    return [
        sys.executable,
        "-I",
        "-S",
        "-X",
        f"pycache_prefix={tmp_path / cache_name}",
        str(ROOT / "scripts/build_peano_hydra_replay_pack.py"),
    ]


def test_replay_pack_schema_is_pinned_canonical_and_explicitly_candidate_only() -> None:
    schema = replay_pack.replay_pack_schema()
    identity = replay_pack.replay_pack_schema_identity()
    assert identity["sha256"] == replay_pack.REPLAY_PACK_SCHEMA_SHA256
    assert identity["artifact_sha256"] == _sha(
        replay_pack.canonical_document_bytes(schema, limit=replay_pack.MAX_SCHEMA_BYTES)
    )
    assert schema["constants"] == {
        "certificate_representation": "peano-lab-v2",
        "evaluation_eligible": False,
        "logic_mode": "intuitionistic",
        "status": "candidate",
    }
    assert "best-known" not in json.dumps(schema)


def test_synthetic_pack_replays_from_bytes_through_the_independent_kernel(
    tmp_path: Path,
) -> None:
    fixture = _fixture()
    report = replay_pack.verify_replay_pack_files(
        fixture["manifest"],
        schema_raw=fixture["schema_raw"],
        catalog_raw=fixture["catalog_raw"],
        profile_raw=fixture["profile_raw"],
        artifact_files=fixture["artifact_files"],
    )
    assert report["status"] == "passed"
    assert report["kernel_checked_count"] == 1

    root = tmp_path / "pack"
    _write_pack(root, fixture)
    manifest, streamed = replay_pack.load_and_verify_replay_pack(root)
    assert manifest["root_sha256"] == fixture["manifest"]["root_sha256"]
    assert streamed == report


def test_fully_rehashed_invalid_certificate_still_fails_kernel() -> None:
    fixture = _fixture(statement="0 = 1", target=Eq(ZERO, Succ(ZERO)), proof=REFL)
    with pytest.raises(replay_pack.LibraryReplayPackError, match="kernel rejected"):
        replay_pack.verify_replay_pack_files(
            fixture["manifest"],
            schema_raw=fixture["schema_raw"],
            catalog_raw=fixture["catalog_raw"],
            profile_raw=fixture["profile_raw"],
            artifact_files=fixture["artifact_files"],
        )


def test_fully_rehashed_classically_valid_dne_fails_constructive_kernel() -> None:
    proof = DNE(ATOM)
    assert check_classical((), proof, CLASSICALLY_VALID_DNE)
    fixture = _fixture(
        statement=pretty_formula(CLASSICALLY_VALID_DNE, []),
        target=CLASSICALLY_VALID_DNE,
        proof=proof,
    )
    with pytest.raises(replay_pack.LibraryReplayPackError, match="kernel rejected"):
        replay_pack.verify_replay_pack_files(
            fixture["manifest"],
            schema_raw=fixture["schema_raw"],
            catalog_raw=fixture["catalog_raw"],
            profile_raw=fixture["profile_raw"],
            artifact_files=fixture["artifact_files"],
        )


@pytest.mark.parametrize("identity", ["schema", "semantic_profile"])
def test_embedded_versions_reject_bool_integer_aliases(identity: str) -> None:
    fixture = _fixture()
    manifest = deepcopy(fixture["manifest"])
    manifest[identity]["v"] = True
    with pytest.raises(replay_pack.LibraryReplayPackError, match="version"):
        replay_pack.validate_replay_pack_manifest(_reroot(manifest))


def test_catalog_counts_and_indexes_reject_bool_integer_aliases() -> None:
    fixture = _fixture()
    catalog = json.loads(fixture["catalog_raw"])
    catalog["theorem_count"] = True
    with pytest.raises(replay_pack.LibraryReplayPackError, match="root"):
        replay_pack._catalog_from_bytes(
            replay_pack.canonical_document_bytes(
                catalog, limit=replay_pack.MAX_CATALOG_BYTES
            )
        )

    catalog = json.loads(fixture["catalog_raw"])
    catalog["theorems"][0]["index"] = False
    catalog["ordered_root_sha256"] = _sha(
        replay_pack.canonical_json_bytes(catalog["theorems"])
    )
    with pytest.raises(replay_pack.LibraryReplayPackError, match="order"):
        replay_pack._catalog_from_bytes(
            replay_pack.canonical_document_bytes(
                catalog, limit=replay_pack.MAX_CATALOG_BYTES
            )
        )


def test_manifest_counts_and_indexes_reject_bool_integer_aliases() -> None:
    fixture = _fixture()
    manifest = deepcopy(fixture["manifest"])
    manifest["source_catalog"]["theorem_count"] = True
    with pytest.raises(replay_pack.LibraryReplayPackError, match="exact integer"):
        replay_pack.validate_replay_pack_manifest(_reroot(manifest))

    manifest = deepcopy(fixture["manifest"])
    manifest["theorems"][0]["index"] = False
    manifest["replay_root_sha256"] = replay_pack.replay_root_sha256(
        manifest["theorems"]
    )
    with pytest.raises(replay_pack.LibraryReplayPackError, match="order"):
        replay_pack.validate_replay_pack_manifest(_reroot(manifest))


@pytest.mark.parametrize(
    "dependencies",
    [
        ["zero_reflexive_fixture"],
        ["unknown_theorem"],
        ["unknown_theorem", "unknown_theorem"],
    ],
)
def test_manifest_rejects_self_unknown_and_duplicate_dependencies(
    dependencies: list[str],
) -> None:
    fixture = _fixture()
    manifest = deepcopy(fixture["manifest"])
    manifest["theorems"][0]["declared_dependencies"] = dependencies
    with pytest.raises(replay_pack.LibraryReplayPackError, match="order"):
        replay_pack.validate_replay_pack_manifest(_reroot(manifest))


def test_manifest_enforces_artifact_node_limit_before_file_io() -> None:
    fixture = _fixture()
    manifest = deepcopy(fixture["manifest"])
    tree = manifest["theorems"][0]["packed_tree_metrics"]
    tree["proof_nodes"] = replay_pack.MAX_ARTIFACT_NODES + 1
    manifest["theorems"][0]["artifact"]["fuel"] = (
        replay_pack.FUEL_MULTIPLIER * tree["proof_nodes"] + replay_pack.FUEL_OFFSET
    )
    manifest["replay_root_sha256"] = replay_pack.replay_root_sha256(
        manifest["theorems"]
    )
    manifest["aggregate"]["proof_nodes_maximum"] = tree["proof_nodes"]
    manifest["aggregate"]["proof_nodes_total"] = tree["proof_nodes"]
    with pytest.raises(replay_pack.LibraryReplayPackError, match="exceed"):
        replay_pack.validate_replay_pack_manifest(_reroot(manifest))


def test_manifest_enforces_artifact_depth_limit_before_file_io() -> None:
    fixture = _fixture()
    manifest = deepcopy(fixture["manifest"])
    depth = replay_pack.MAX_ARTIFACT_DEPTH + 1
    tree = manifest["theorems"][0]["packed_tree_metrics"]
    construction = manifest["theorems"][0]["construction_metrics"]
    tree["proof_depth"] = depth
    tree["proof_nodes"] = depth
    construction["proof_depth"] = depth
    construction["proof_nodes"] = depth
    manifest["theorems"][0]["artifact"]["fuel"] = (
        replay_pack.FUEL_MULTIPLIER * depth + replay_pack.FUEL_OFFSET
    )
    manifest["aggregate"]["proof_depth_maximum"] = depth
    manifest["aggregate"]["proof_nodes_maximum"] = depth
    manifest["aggregate"]["proof_nodes_total"] = depth
    manifest["replay_root_sha256"] = replay_pack.replay_root_sha256(
        manifest["theorems"]
    )
    with pytest.raises(replay_pack.LibraryReplayPackError, match="exceed"):
        replay_pack.validate_replay_pack_manifest(_reroot(manifest))


def test_forged_kernel_source_identity_fails_even_when_fully_rerooted() -> None:
    fixture = _fixture()
    manifest = deepcopy(fixture["manifest"])
    sources = manifest["kernel_identity"]["sources"]
    sources[0]["sha256"] = "0" * 64
    manifest["kernel_identity"]["source_root_sha256"] = _sha(
        replay_pack.canonical_json_bytes(sources)
    )
    with pytest.raises(replay_pack.LibraryReplayPackError, match="live verifier"):
        replay_pack.validate_replay_pack_manifest(_reroot(manifest))


def test_live_kernel_source_drift_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture()
    live_identity = replay_pack.live_kernel_identity

    def drifted_identity() -> dict[str, object]:
        identity = deepcopy(live_identity())
        identity["sources"][0]["sha256"] = "0" * 64
        identity["source_root_sha256"] = _sha(
            replay_pack.canonical_json_bytes(identity["sources"])
        )
        return identity

    monkeypatch.setattr(replay_pack, "live_kernel_identity", drifted_identity)
    with pytest.raises(replay_pack.LibraryReplayPackError, match="live verifier"):
        replay_pack.validate_replay_pack_manifest(fixture["manifest"])


def test_construction_metrics_cannot_lie_about_reconstructable_tree_shape() -> None:
    fixture = _fixture()
    manifest = deepcopy(fixture["manifest"])
    manifest["theorems"][0]["construction_metrics"]["proof_nodes"] += 1
    with pytest.raises(replay_pack.LibraryReplayPackError, match="structural metrics"):
        replay_pack.validate_replay_pack_manifest(_reroot(manifest))


def test_construction_object_sharing_metrics_obey_dag_invariants() -> None:
    fixture = _fixture()
    manifest = deepcopy(fixture["manifest"])
    manifest["theorems"][0]["construction_metrics"]["proof_edges"] = 1
    manifest["theorems"][0]["construction_metrics"][
        "reused_proof_references"
    ] = 0
    with pytest.raises(replay_pack.LibraryReplayPackError, match="object-sharing"):
        replay_pack.validate_replay_pack_manifest(_reroot(manifest))


def test_fully_rehashed_artifact_target_must_equal_packed_catalog_statement() -> None:
    fixture = _fixture(statement="0 = 0", target=ATOM, artifact_target=Eq(Succ(ZERO), Succ(ZERO)))
    with pytest.raises(replay_pack.LibraryReplayPackError, match="differs from its closed statement"):
        replay_pack.verify_replay_pack_files(
            fixture["manifest"],
            schema_raw=fixture["schema_raw"],
            catalog_raw=fixture["catalog_raw"],
            profile_raw=fixture["profile_raw"],
            artifact_files=fixture["artifact_files"],
        )


def test_missing_extra_or_mutated_artifact_bytes_fail_closed() -> None:
    fixture = _fixture()
    with pytest.raises(replay_pack.LibraryReplayPackError, match="mapping"):
        replay_pack.verify_replay_pack_files(
            fixture["manifest"],
            schema_raw=fixture["schema_raw"],
            catalog_raw=fixture["catalog_raw"],
            profile_raw=fixture["profile_raw"],
            artifact_files={},
        )
    extra = {**fixture["artifact_files"], "certificates/extra.pl2": b"x"}
    with pytest.raises(replay_pack.LibraryReplayPackError, match="mapping"):
        replay_pack.verify_replay_pack_files(
            fixture["manifest"],
            schema_raw=fixture["schema_raw"],
            catalog_raw=fixture["catalog_raw"],
            profile_raw=fixture["profile_raw"],
            artifact_files=extra,
        )
    mutated = dict(fixture["artifact_files"])
    path = next(iter(mutated))
    mutated[path] = mutated[path][:-2] + b"x\n"
    with pytest.raises(replay_pack.LibraryReplayPackError, match="hash"):
        replay_pack.verify_replay_pack_files(
            fixture["manifest"],
            schema_raw=fixture["schema_raw"],
            catalog_raw=fixture["catalog_raw"],
            profile_raw=fixture["profile_raw"],
            artifact_files=mutated,
        )


def test_manifest_semantics_are_checked_before_any_artifact_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture()
    manifest = deepcopy(fixture["manifest"])
    manifest["theorem_count"] = 2
    root = tmp_path / "pack"
    _write_pack(root, {**fixture, "manifest": manifest})
    real_read = replay_pack._read_bounded_regular_file
    artifact_reads = 0

    def counting_read(path: Path, *, label: str, limit: int) -> bytes:
        nonlocal artifact_reads
        if replay_pack.CERTIFICATE_DIRECTORY in path.parts:
            artifact_reads += 1
        return real_read(path, label=label, limit=limit)

    monkeypatch.setattr(replay_pack, "_read_bounded_regular_file", counting_read)
    with pytest.raises(replay_pack.LibraryReplayPackError, match="count|root"):
        replay_pack.load_and_verify_replay_pack(root)
    assert artifact_reads == 0


def test_loader_rejects_extra_files_and_symlinked_roots(tmp_path: Path) -> None:
    fixture = _fixture()
    root = tmp_path / "pack"
    _write_pack(root, fixture)
    (root / "extra").write_text("not committed", encoding="utf-8")
    with pytest.raises(
        replay_pack.LibraryReplayPackError, match="extra|entry limit"
    ):
        replay_pack.load_and_verify_replay_pack(root)

    clean = tmp_path / "clean"
    _write_pack(clean, fixture)
    link = tmp_path / "link"
    try:
        link.symlink_to(clean, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable")
    with pytest.raises(replay_pack.LibraryReplayPackError, match="non-symlink"):
        replay_pack.load_and_verify_replay_pack(link)


def test_cli_rejects_a_manifest_fifo_without_blocking(tmp_path: Path) -> None:
    if not hasattr(replay_pack.os, "mkfifo") or not hasattr(
        replay_pack.os, "O_NONBLOCK"
    ):
        pytest.skip("nonblocking FIFOs are unavailable")
    root = tmp_path / "fifo-pack"
    root.mkdir()
    replay_pack.os.mkfifo(root / replay_pack.MANIFEST_FILE)
    completed = subprocess.run(
        [
            *_isolated_cli_prefix(tmp_path, "fifo-pack-pycache"),
            "--verify",
            "--output",
            str(root),
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode != 0
    assert "regular file" in completed.stderr


def test_directory_enumeration_stops_at_the_declared_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeEntry:
        def __init__(self, name: str) -> None:
            self.name = name

        def is_file(self, *, follow_symlinks: bool) -> bool:
            assert follow_symlinks is False
            return True

        def is_dir(self, *, follow_symlinks: bool) -> bool:
            assert follow_symlinks is False
            return False

    class FakeScan:
        def __init__(self) -> None:
            self.consumed = 0

        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def __iter__(self):
            return self

        def __next__(self) -> FakeEntry:
            self.consumed += 1
            return FakeEntry(f"entry-{self.consumed}")

    scan = FakeScan()
    monkeypatch.setattr(replay_pack.os, "scandir", lambda _path: scan)
    with pytest.raises(replay_pack.LibraryReplayPackError, match="entry limit"):
        replay_pack._bounded_directory_entries(
            Path("unused"), label="synthetic directory", maximum=5
        )
    assert scan.consumed == 6


def test_cli_does_not_resolve_away_a_symlinked_pack_root(tmp_path: Path) -> None:
    fixture = _fixture()
    clean = tmp_path / "clean"
    _write_pack(clean, fixture)
    link = tmp_path / "link"
    try:
        link.symlink_to(clean, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable")
    completed = subprocess.run(
        [
            *_isolated_cli_prefix(tmp_path, "symlink-pack-pycache"),
            "--verify",
            "--output",
            str(link),
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode != 0
    assert "non-symlink directory" in completed.stderr


def test_pack_only_worker_never_imports_living_library_engine_ui_or_training(
    tmp_path: Path,
) -> None:
    fixture = _fixture()
    root = tmp_path / "pack"
    _write_pack(root, fixture)
    module_path = ROOT / "training/peano_hydra/library_replay_pack.py"
    code = r'''
import builtins, importlib.util, pathlib, sys
sys.path.insert(0, sys.argv[1])
blocked = ("peano_lab.library", "peano_lab.engine", "peano_lab.ui", "training", "torch", "transformers")
real_import = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.startswith(blocked):
        raise RuntimeError("forbidden import: " + name)
    return real_import(name, *args, **kwargs)
builtins.__import__ = guarded
spec = importlib.util.spec_from_file_location("isolated_replay", sys.argv[2])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
manifest, report = module.load_and_verify_replay_pack(pathlib.Path(sys.argv[3]))
assert report["kernel_checked_count"] == 1
assert not any(name.startswith(blocked) for name in sys.modules)
print(manifest["root_sha256"])
'''
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            code,
            str(ROOT / "peano-lab/py"),
            str(module_path),
            str(root),
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == fixture["manifest"]["root_sha256"]


def test_public_cli_emits_a_fresh_isolated_worker_receipt(tmp_path: Path) -> None:
    fixture = _fixture()
    root = tmp_path / "pack"
    report_path = tmp_path / "report.json"
    _write_pack(root, fixture)
    completed = subprocess.run(
        [
            *_isolated_cli_prefix(tmp_path, "public-cli-pycache"),
            "--verify",
            "--output",
            str(root),
            "--report",
            str(report_path),
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(report_path.read_bytes())
    assert report["manifest_root_sha256"] == fixture["manifest"]["root_sha256"]
    assert report["worker_isolation"] == {
        "forbidden_import_prefixes": list(
            replay_pack.FORBIDDEN_REPLAY_IMPORT_PREFIXES
        ),
        "forbidden_modules_loaded": [],
        "format": replay_pack.REPLAY_WORKER_ISOLATION_FORMAT,
        "fresh_repo_pycache": True,
        "guard": "meta-path-reject",
        "python_isolated_mode": True,
        "python_no_site": True,
        "v": replay_pack.REPLAY_WORKER_ISOLATION_VERSION,
    }

    raw = report_path.read_bytes()
    assert raw == replay_pack.canonical_document_bytes(
        report, limit=replay_pack.MAX_SCHEMA_BYTES
    )
    assert not list(tmp_path.glob(f".{report_path.name}.*.tmp"))


@pytest.mark.parametrize(
    "relative_report",
    [".", "manifest.json", "nested/report.json"],
)
def test_cli_rejects_report_destinations_that_could_mutate_the_pack(
    tmp_path: Path,
    relative_report: str,
) -> None:
    fixture = _fixture()
    root = tmp_path / "pack"
    _write_pack(root, fixture)
    manifest_before = (root / replay_pack.MANIFEST_FILE).read_bytes()
    report_path = root / relative_report
    completed = subprocess.run(
        [
            *_isolated_cli_prefix(
                tmp_path, f"bad-report-{relative_report.replace('/', '-')}-pycache"
            ),
            "--verify",
            "--output",
            str(root),
            "--report",
            str(report_path),
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode != 0
    assert "outside the replay pack" in completed.stderr
    assert (root / replay_pack.MANIFEST_FILE).read_bytes() == manifest_before
    if relative_report == "nested/report.json":
        assert not report_path.exists()


def test_cli_rejects_report_symlink_resolving_inside_the_pack(tmp_path: Path) -> None:
    fixture = _fixture()
    root = tmp_path / "pack"
    _write_pack(root, fixture)
    manifest_path = root / replay_pack.MANIFEST_FILE
    manifest_before = manifest_path.read_bytes()
    report_link = tmp_path / "report-link.json"
    try:
        report_link.symlink_to(manifest_path)
    except OSError:
        pytest.skip("symlinks are unavailable")
    completed = subprocess.run(
        [
            *_isolated_cli_prefix(tmp_path, "report-link-pycache"),
            "--verify",
            "--output",
            str(root),
            "--report",
            str(report_link),
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode != 0
    assert "outside the replay pack" in completed.stderr
    assert report_link.is_symlink()
    assert manifest_path.read_bytes() == manifest_before


def test_cli_rejects_casefolded_report_alias_inside_the_pack(tmp_path: Path) -> None:
    fixture = _fixture()
    root = tmp_path / "CaseSensitiveSpelling"
    _write_pack(root, fixture)
    manifest_before = (root / replay_pack.MANIFEST_FILE).read_bytes()
    report_path = tmp_path / "casesensitivespelling" / replay_pack.MANIFEST_FILE
    completed = subprocess.run(
        [
            *_isolated_cli_prefix(tmp_path, "casefold-report-pycache"),
            "--verify",
            "--output",
            str(root),
            "--report",
            str(report_path),
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode != 0
    assert "outside the replay pack" in completed.stderr
    assert (root / replay_pack.MANIFEST_FILE).read_bytes() == manifest_before


@pytest.mark.parametrize("prepopulate_cache", [False, True])
def test_cli_requires_a_fresh_explicit_repository_pycache(
    tmp_path: Path,
    prepopulate_cache: bool,
) -> None:
    fixture = _fixture()
    root = tmp_path / "pack"
    _write_pack(root, fixture)
    command = [sys.executable, "-I", "-S"]
    expected_error = "pycache_prefix"
    if prepopulate_cache:
        cache_root = tmp_path / "used-pycache"
        repository_cache = cache_root.joinpath(*ROOT.resolve().parts[1:])
        repository_cache.mkdir(parents=True)
        command.extend(["-X", f"pycache_prefix={cache_root}"])
        expected_error = "fresh repository pycache"
    command.extend(
        [
            str(ROOT / "scripts/build_peano_hydra_replay_pack.py"),
            "--verify",
            "--output",
            str(root),
        ]
    )
    completed = subprocess.run(
        command,
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode != 0
    assert expected_error in completed.stderr


def test_verify_path_configuration_cannot_shadow_the_standard_library(
    tmp_path: Path,
) -> None:
    fake_root = tmp_path / "untrusted-repository"
    fake_root.mkdir()
    (fake_root / "dataclasses.py").write_text(
        "raise RuntimeError('repository shadow module loaded')\n", encoding="utf-8"
    )
    (fake_root / "hashlib.py").write_text(
        "raise RuntimeError('repository shadow module loaded')\n", encoding="utf-8"
    )
    code = r'''
import importlib.util, pathlib, sys
spec = importlib.util.spec_from_file_location("replay_cli", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.ROOT = pathlib.Path(sys.argv[2])
module.PY_ROOT = pathlib.Path(sys.argv[2])
module._configure_verify_paths()
import dataclasses
import hashlib
assert pathlib.Path(dataclasses.__file__).resolve().parent != pathlib.Path(sys.argv[2]).resolve()
assert pathlib.Path(hashlib.__file__).resolve().parent != pathlib.Path(sys.argv[2]).resolve()
'''
    completed = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            "-X",
            f"pycache_prefix={tmp_path / 'stdlib-shadow-pycache'}",
            "-c",
            code,
            str(ROOT / "scripts/build_peano_hydra_replay_pack.py"),
            str(fake_root),
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr


def test_builder_binds_second_live_certificate_to_catalog_repr_hash() -> None:
    from training.peano_hydra import library_replay_pack_builder as builder

    fixture = _fixture()
    catalog_row = json.loads(fixture["catalog_raw"])["theorems"][0]
    catalog_row["certificate_sha256"] = "0" * 64
    artifact = next(iter(fixture["artifact_files"].values()))
    with pytest.raises(builder.LibraryReplayPackBuildError, match="identity drifted"):
        builder._row(
            0,
            catalog_row,
            artifact=artifact,
            formula=ATOM,
            proof=REFL,
        )


def test_manifest_and_replay_roots_are_deterministic() -> None:
    first = _fixture()
    second = _fixture()
    assert replay_pack.canonical_document_bytes(first["manifest"]) == (
        replay_pack.canonical_document_bytes(second["manifest"])
    )
    assert first["artifact_files"] == second["artifact_files"]


def test_committed_384_theorem_pack_replays_in_fresh_isolated_worker(
    tmp_path: Path,
) -> None:
    manifest = json.loads((COMMITTED_PACK / replay_pack.MANIFEST_FILE).read_bytes())
    assert manifest["theorem_count"] == 384
    assert manifest["root_sha256"] == COMMITTED_MANIFEST_ROOT
    assert manifest["replay_root_sha256"] == COMMITTED_REPLAY_ROOT
    generated_report = tmp_path / "full-replay-report.json"
    completed = subprocess.run(
        [
            *_isolated_cli_prefix(tmp_path, "committed-pack-pycache"),
            "--verify",
            "--output",
            str(COMMITTED_PACK),
            "--report",
            str(generated_report),
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert completed.returncode == 0, completed.stderr
    retained_raw = COMMITTED_REPORT.read_bytes()
    generated_raw = generated_report.read_bytes()
    report = json.loads(generated_raw)
    assert generated_raw == replay_pack.canonical_document_bytes(
        report, limit=replay_pack.MAX_SCHEMA_BYTES
    )
    assert generated_raw == retained_raw
    assert report["kernel_checked_count"] == 384
    assert report["manifest_root_sha256"] == COMMITTED_MANIFEST_ROOT
    assert report["replay_root_sha256"] == COMMITTED_REPLAY_ROOT
