"""Focused tests for the result-independent Hydra A2.3a verifier.

No test builds a production layered certificate.  Compact hand-written kernel
artifacts exercise the independent codec/checker/measurement boundary, while
static import checks keep the producer and optimizer out of the verifier TCB.
"""

from __future__ import annotations

import ast
import base64
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from peano_lab.kernel.artifact_codec import (  # noqa: E402
    encode_artifact_bounded,
    encode_formula,
    encode_proof,
)
from peano_lab.kernel.formulas import Eq  # noqa: E402
from peano_lab.kernel.proofs import Cut, EqRefl, Hyp  # noqa: E402
from peano_lab.kernel.terms import Succ, Zero  # noqa: E402
import training.peano_hydra.library_optimizer_comparison_verifier as verifier  # noqa: E402


MODULE_PATH = (
    ROOT
    / "training"
    / "peano_hydra"
    / "library_optimizer_comparison_verifier.py"
)
CLI_PATH = (
    ROOT
    / "scripts"
    / "verify_peano_hydra_library_optimizer_comparison_pilot.py"
)
FORBIDDEN_IMPORT_PREFIXES = (
    "peano_lab.engine",
    "peano_lab.library",
    "peano_lab.tactics",
    "training.peano_hydra.library_optimizer_comparison_pilot",
    "training.peano_hydra.library_replay_pack",
)
ALLOWED_PEANO_IMPORT_PREFIX = "peano_lab.kernel"
ISOLATED_PYTHON = shutil.which("python3.12") or (
    sys.executable if getattr(sys.flags, "safe_path", None) is not None else None
)


def _isolated_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment["PYTHONPYCACHEPREFIX"] = verifier.PYCACHE_PREFIX
    return environment


def _isolated_argv(*arguments: str) -> list[str]:
    if ISOLATED_PYTHON is None:
        pytest.skip("the controlled verifier requires CPython with -P support")
    return [ISOLATED_PYTHON, "-B", "-P", "-s", "-S", *arguments]


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _artifact(*, cut: bool = False, valid: bool = True, fuel: int = 40):
    zero = Zero()
    target = Eq(zero, zero if valid else Succ(zero))
    proposition = Eq(zero, zero)
    proof = (
        Cut(proposition, proposition, EqRefl(zero), Hyp(0))
        if cut
        else EqRefl(zero)
    )
    raw = encode_artifact_bounded(fuel, target, proof, max_bytes=10_000)
    return raw, target, proof


def _observation(
    candidate_id: str,
    order: int,
    *,
    artifact_bytes: int,
    proof_nodes: int,
    proof_depth: int,
    cut_nodes: int,
) -> dict[str, object]:
    return {
        "artifact_sha256": _sha(candidate_id.encode("ascii")),
        "candidate_id": candidate_id,
        "candidate_kind_order": order,
        "metrics": {
            "artifact_bytes": artifact_bytes,
            "proof_nodes": proof_nodes,
            "proof_depth": proof_depth,
            "cut_nodes": cut_nodes,
        },
    }


def _comparison(observations: tuple[dict[str, object], ...]) -> dict[str, object]:
    frontier = verifier._componentwise_nondominated(observations)
    frontier_set = set(frontier)
    representative = verifier._select_representative(
        tuple(
            row for row in observations if row["candidate_id"] in frontier_set
        )
    )
    return {
        "axes_in_componentwise_order": list(verifier.COMPARISON_AXES),
        "candidate_universe_complete": True,
        "candidate_universe_ids_in_order": [
            item[0] for item in verifier.CANDIDATE_KINDS
        ],
        "claim": "bounded-three-candidate-pilot-only",
        "global_best_claim": False,
        "minimality_claim": False,
        "nondominated_candidate_ids_in_input_order": list(frontier),
        "representative_candidate_id": representative,
        "representative_tie_break": list(verifier.REPRESENTATIVE_TIE_BREAK),
    }


def _producer_source_state() -> dict[str, object]:
    files = [
        {"bytes": size, "path": path.as_posix(), "sha256": digest}
        for path, size, digest in verifier.PRODUCER_SOURCE_FILES
    ]
    body = {
        "commit_sha1": "1" * 40,
        "files": files,
        "format": verifier.PRODUCER_SOURCE_STATE_FORMAT,
        "git_verified": False,
        "tree_sha1": "2" * 40,
        "v": 1,
    }
    preimage = {
        "format": verifier.PRODUCER_SOURCE_STATE_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": 1,
    }
    return {
        **body,
        "root_preimage": preimage,
        "root_sha256": verifier._sha256_json(
            preimage, limit=verifier.MAX_SCHEMA_BYTES
        ),
    }


def test_public_surface_is_narrow_and_has_no_optimizer_entrypoint() -> None:
    assert set(verifier.__all__) == {
        "LibraryOptimizerComparisonVerificationError",
        "VERIFICATION_FALSE_FIELDS",
        "VERIFICATION_RECEIPT_BODY_FIELDS",
        "VERIFICATION_RECEIPT_FIELDS",
        "canonical_verification_receipt_bytes",
        "load_and_verify_optimizer_comparison_pilot",
        "validate_optimizer_comparison_verification_receipt",
        "verify_optimizer_comparison_pilot",
    }
    assert not any(
        fragment in name
        for name in verifier.__all__
        for fragment in ("compile", "build", "publish", "best", "minimal", "admit")
    )


def test_static_import_policy_excludes_producer_optimizer_engine_and_library() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    assert not any(
        name.startswith(prefix)
        for name in imported
        for prefix in FORBIDDEN_IMPORT_PREFIXES
    )
    peano_imports = [name for name in imported if name.startswith("peano_lab")]
    assert peano_imports
    assert all(name.startswith(ALLOWED_PEANO_IMPORT_PREFIX) for name in peano_imports)


def test_exact_cli_loader_keeps_fresh_runtime_stdlib_and_kernel_only() -> None:
    code = r'''
import builtins
import importlib.util
import sys
specification = importlib.util.spec_from_file_location(
    "_fresh_a23a_verifier_cli", sys.argv[1]
)
if specification is None or specification.loader is None:
    raise SystemExit("cannot load exact verifier CLI")
module = importlib.util.module_from_spec(specification)
sys.modules[specification.name] = module
original_import = builtins.__import__
def guarded_import(name, *args, **kwargs):
    if name == "peano_lab" or name.startswith("peano_lab."):
        active = sys.modules[specification.name]
        if getattr(active, "_INITIALIZERS_PREFLIGHTED", False) is not True:
            raise SystemExit("peano_lab import occurred before initializer preflight")
    return original_import(name, *args, **kwargs)
builtins.__import__ = guarded_import
try:
    specification.loader.exec_module(module)
finally:
    builtins.__import__ = original_import
if module._INITIALIZERS_PREFLIGHTED is not True:
    raise SystemExit("kernel initializer preflight was not retained")
if module._CACHE_POLICY_PREFLIGHTED is not True:
    raise SystemExit("bytecode cache preflight was not retained")
if sys.path[-1] != str(module.PY_ROOT):
    raise SystemExit("Peano root was not appended after standard-library paths")
for standard in ("argparse", "dataclasses", "hashlib", "json", "pathlib"):
    loaded = sys.modules.get(standard)
    origin = getattr(loaded, "__file__", None)
    if isinstance(origin, str) and str(module.ROOT) in origin:
        raise SystemExit(f"stdlib module was shadowed: {standard} -> {origin}")
forbidden = [
    name for name in sys.modules
    if name.startswith("peano_lab.engine")
    or name.startswith("peano_lab.library")
    or name.startswith("peano_lab.tactics")
    or name.startswith("training.peano_hydra")
]
if forbidden:
    raise SystemExit(repr(sorted(forbidden)))
'''
    completed = subprocess.run(
        _isolated_argv("-c", code, str(CLI_PATH)),
        cwd=ROOT,
        env=_isolated_environment(),
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_runtime_boundary_fails_closed_on_forbidden_preload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "peano_lab.engine.synthetic_contaminant", object())
    with pytest.raises(
        verifier.LibraryOptimizerComparisonVerificationError,
        match="contaminated",
    ):
        verifier._require_runtime_import_boundary()


def test_cli_initializer_preflight_rejects_drift_before_import(
    tmp_path: Path,
) -> None:
    fake_py_root = tmp_path / "py"
    (fake_py_root / "peano_lab" / "kernel").mkdir(parents=True)
    first = (ROOT / "peano-lab/py/peano_lab/__init__.py").read_bytes()
    second = (ROOT / "peano-lab/py/peano_lab/kernel/__init__.py").read_bytes()
    (fake_py_root / "peano_lab/__init__.py").write_bytes(first)
    # Preserve the exact byte count so a size-only check would accept it.
    (fake_py_root / "peano_lab/kernel/__init__.py").write_bytes(
        bytes([second[0] ^ 1]) + second[1:]
    )
    code = r'''
import importlib.util
from pathlib import Path
import sys
specification = importlib.util.spec_from_file_location("_drift_test_cli", sys.argv[1])
if specification is None or specification.loader is None:
    raise SystemExit("cannot load exact verifier CLI")
module = importlib.util.module_from_spec(specification)
specification.loader.exec_module(module)
module.PY_ROOT = Path(sys.argv[2])
module._INITIALIZERS_PREFLIGHTED = False
try:
    module._preflight_kernel_initializers()
except RuntimeError as exc:
    if "hash drifted" not in str(exc):
        raise
else:
    raise SystemExit("mutated kernel initializer passed preflight")
'''
    completed = subprocess.run(
        _isolated_argv("-c", code, str(CLI_PATH), str(fake_py_root)),
        cwd=ROOT,
        env=_isolated_environment(),
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_cli_kernel_source_preflight_rejects_symlink_ancestor(
    tmp_path: Path,
) -> None:
    fake_py_root = tmp_path / "py"
    fake_py_root.mkdir()
    (fake_py_root / "peano_lab").symlink_to(
        ROOT / "peano-lab/py/peano_lab", target_is_directory=True
    )
    code = r'''
import importlib.util
from pathlib import Path
import sys
specification = importlib.util.spec_from_file_location("_ancestor_test_cli", sys.argv[1])
if specification is None or specification.loader is None:
    raise SystemExit("cannot load exact verifier CLI")
module = importlib.util.module_from_spec(specification)
specification.loader.exec_module(module)
module.PY_ROOT = Path(sys.argv[2])
module._INITIALIZERS_PREFLIGHTED = False
try:
    module._preflight_kernel_sources()
except RuntimeError as exc:
    if "ancestor contains a symlink" not in str(exc):
        raise
else:
    raise SystemExit("symlinked kernel ancestor passed preflight")
'''
    completed = subprocess.run(
        _isolated_argv("-c", code, str(CLI_PATH), str(fake_py_root)),
        cwd=ROOT,
        env=_isolated_environment(),
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_fixed_pycache_prefix_ignores_valid_adjacent_malicious_pyc(
    tmp_path: Path,
) -> None:
    source = tmp_path / "cache_victim.py"
    marker = tmp_path / "malicious-bytecode-executed"
    malicious = f"open({str(marker)!r}, 'w').write('x')\n".encode("utf-8")
    source.write_bytes(malicious)
    original_mtime_ns = source.stat().st_mtime_ns
    compile_code = r'''
import importlib.util
import py_compile
import sys
cache = importlib.util.cache_from_source(sys.argv[1])
py_compile.compile(sys.argv[1], cfile=cache, doraise=True)
print(cache)
'''
    compile_environment = dict(os.environ)
    compile_environment.pop("PYTHONPATH", None)
    compile_environment.pop("PYTHONPYCACHEPREFIX", None)
    compiled = subprocess.run(
        _isolated_argv("-c", compile_code, str(source)),
        cwd=ROOT,
        env=compile_environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert compiled.returncode == 0, compiled.stderr or compiled.stdout
    cache = Path(compiled.stdout.strip())
    assert cache.is_file()
    benign = b"pass" + b" " * (len(malicious) - 5) + b"\n"
    assert len(benign) == len(malicious)
    source.write_bytes(benign)
    os.utime(source, ns=(original_mtime_ns, original_mtime_ns))

    command = "import sys; sys.path.append(sys.argv[1]); import cache_victim"
    control_environment = dict(os.environ)
    control_environment.pop("PYTHONPATH", None)
    control_environment.pop("PYTHONPYCACHEPREFIX", None)
    control = subprocess.run(
        _isolated_argv("-c", command, str(tmp_path)),
        cwd=ROOT,
        env=control_environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert control.returncode == 0, control.stderr or control.stdout
    assert marker.is_file(), "control import did not prove the crafted pyc was valid"
    marker.unlink()

    protected = subprocess.run(
        _isolated_argv("-c", command, str(tmp_path)),
        cwd=ROOT,
        env=_isolated_environment(),
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert protected.returncode == 0, protected.stderr or protected.stdout
    assert not marker.exists(), "fixed pycache prefix executed adjacent bytecode"


def test_frozen_schema_upstream_producer_and_kernel_pins_load() -> None:
    fixed = verifier._load_fixed_inputs(ROOT)
    assert fixed["schema_artifact_sha256"] == verifier.PRODUCER_SOURCE_FILES[0][2]
    assert len(fixed["kernel_sources"]) == 8
    assert [row["path"] for row in fixed["kernel_sources"][:2]] == [
        "peano-lab/py/peano_lab/__init__.py",
        "peano-lab/py/peano_lab/kernel/__init__.py",
    ]
    assert fixed["audit"]["root_sha256"] == verifier.AUDIT_ROOT_SHA256
    assert fixed["rebuild"]["root_sha256"] == verifier.REBUILD_ROOT_SHA256
    assert (
        fixed["manifest"]["replay_root_sha256"] == verifier.REPLAY_ROOT_SHA256
    )


def test_producer_source_state_is_exact_and_explicitly_not_git_verified() -> None:
    state = _producer_source_state()
    assert verifier._validate_producer_source_state(state, root=ROOT) == state
    for mutate in (
        lambda value: value.__setitem__("git_verified", True),
        lambda value: value["files"][0].__setitem__("sha256", "0" * 64),
        lambda value: value["files"].reverse(),
        lambda value: value.__setitem__("root_sha256", "0" * 64),
    ):
        changed = deepcopy(state)
        mutate(changed)
        with pytest.raises(verifier.LibraryOptimizerComparisonVerificationError):
            verifier._validate_producer_source_state(changed, root=ROOT)


def test_independent_artifact_inspection_checks_codec_kernel_hashes_and_metrics() -> None:
    raw, target, proof = _artifact(cut=True, fuel=77)
    decoded_target, observed = verifier._inspect_artifact(
        raw,
        label="synthetic cut",
        expected_artifact_sha256=_sha(raw),
        expected_fuel=77,
        expected_formula_sha256=_sha(encode_formula(target)),
        expected_proof_sha256=_sha(encode_proof(proof)),
    )
    assert decoded_target == target
    assert observed == {
        "artifact_sha256": _sha(raw),
        "formula_sha256": _sha(encode_formula(target)),
        "fuel": 77,
        "kernel_accepted": True,
        "kernel_context": "empty",
        "metrics": {
            "artifact_bytes": len(raw),
            "cut_nodes": 1,
            "proof_depth": 2,
            "proof_nodes": 3,
        },
        "proof_term_sha256": _sha(encode_proof(proof)),
    }


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("expected_artifact_sha256", "0" * 64),
        ("expected_fuel", 41),
        ("expected_formula_sha256", "1" * 64),
        ("expected_proof_sha256", "2" * 64),
    ),
)
def test_artifact_inspector_rejects_identity_mutations(field: str, replacement: object) -> None:
    raw, target, proof = _artifact(fuel=40)
    arguments = {
        "expected_artifact_sha256": _sha(raw),
        "expected_fuel": 40,
        "expected_formula_sha256": _sha(encode_formula(target)),
        "expected_proof_sha256": _sha(encode_proof(proof)),
    }
    arguments[field] = replacement
    with pytest.raises(verifier.LibraryOptimizerComparisonVerificationError):
        verifier._inspect_artifact(raw, label="mutated", **arguments)


def test_artifact_inspector_rejects_noncanonical_and_kernel_invalid_artifacts() -> None:
    raw, _target, _proof = _artifact()
    with pytest.raises(verifier.LibraryOptimizerComparisonVerificationError):
        verifier._inspect_artifact(raw + b" ", label="noncanonical")
    invalid_raw, _invalid_target, _invalid_proof = _artifact(valid=False)
    with pytest.raises(
        verifier.LibraryOptimizerComparisonVerificationError,
        match="kernel rejected",
    ):
        verifier._inspect_artifact(invalid_raw, label="invalid proof")


def test_compact_synthetic_nine_artifact_matrix_all_checks_from_empty_context() -> None:
    accepted = []
    for theorem_index in range(3):
        for candidate_index in range(3):
            cut = candidate_index == 2
            fuel = 100 + theorem_index * 3 + candidate_index
            raw, target, proof = _artifact(cut=cut, fuel=fuel)
            _decoded, observation = verifier._inspect_artifact(
                raw,
                label=f"t{theorem_index}:c{candidate_index}",
                expected_artifact_sha256=_sha(raw),
                expected_fuel=fuel,
                expected_formula_sha256=_sha(encode_formula(target)),
                expected_proof_sha256=_sha(encode_proof(proof)),
            )
            accepted.append(observation["kernel_accepted"])
    assert accepted == [True] * 9


def test_frontier_and_seven_field_tie_break_are_independently_recomputed() -> None:
    observations = (
        _observation(
            "retained-replay",
            0,
            artifact_bytes=100,
            proof_nodes=10,
            proof_depth=5,
            cut_nodes=2,
        ),
        _observation(
            "a2.2-direct-cut-rebuild",
            1,
            artifact_bytes=90,
            proof_nodes=10,
            proof_depth=5,
            cut_nodes=2,
        ),
        _observation(
            "layered-closure",
            2,
            artifact_bytes=80,
            proof_nodes=12,
            proof_depth=4,
            cut_nodes=1,
        ),
    )
    comparison = _comparison(observations)
    frontier, representative = verifier._verify_comparison(
        comparison, artifacts=observations
    )
    assert frontier == ("a2.2-direct-cut-rebuild", "layered-closure")
    assert representative == "a2.2-direct-cut-rebuild"
    assert comparison["representative_tie_break"] == list(
        verifier.REPRESENTATIVE_TIE_BREAK
    )
    for key, replacement in (
        ("nondominated_candidate_ids_in_input_order", ["retained-replay"]),
        ("representative_candidate_id", "layered-closure"),
        ("global_best_claim", True),
        ("minimality_claim", True),
    ):
        changed = deepcopy(comparison)
        changed[key] = replacement
        with pytest.raises(verifier.LibraryOptimizerComparisonVerificationError):
            verifier._verify_comparison(changed, artifacts=observations)


def test_surface_hashes_counts_and_basis_are_exact() -> None:
    dependencies = ("a", "b")
    closure = ("a", "b", "c")
    surface = {
        "direct_dependencies": list(dependencies),
        "direct_dependencies_lf_sha256": verifier._lf_hash(dependencies),
        "direct_dependency_count": 2,
        "surface_basis": verifier.SURFACE_BASES["retained-replay"],
        "transitive_closure_count": 3,
        "transitive_closure_dependencies_in_replay_order": list(closure),
        "transitive_closure_lf_sha256": verifier._lf_hash(closure),
    }
    verifier._verify_surface(
        surface,
        candidate_id="retained-replay",
        dependencies=dependencies,
        closure=closure,
    )
    for key in (
        "direct_dependency_count",
        "direct_dependencies_lf_sha256",
        "surface_basis",
        "transitive_closure_lf_sha256",
    ):
        changed = deepcopy(surface)
        changed[key] = 0 if key.endswith("count") else "wrong"
        with pytest.raises(verifier.LibraryOptimizerComparisonVerificationError):
            verifier._verify_surface(
                changed,
                candidate_id="retained-replay",
                dependencies=dependencies,
                closure=closure,
            )


def test_layered_graph_diagnostics_are_checked_without_importing_compiler() -> None:
    replay_rows = {
        "a": {"declared_dependencies": [], "index": 0},
        "b": {"declared_dependencies": ["a"], "index": 1},
        "root": {"declared_dependencies": ["b"], "index": 2},
    }
    node_names = ("a", "b", "root")
    body_sources = [
        {
            "body_certificate_sha256": str(index) * 64,
            "dependencies": list(replay_rows[name]["declared_dependencies"]),
            "identity_metrics_comparable": False,
            "index": index,
            "name": name,
            "source_identity_metrics_transportable": False,
        }
        for index, name in enumerate(node_names)
    ]
    # Make the first digest lowercase hex too ("0" * 64 is valid).
    bundle = {
        "body_sources": body_sources,
        "compiler_result_type": "LayeredReplayCandidate",
        "dependency_edge_count": 2,
        "layer_count": 3,
        "layers": [[0], [1], [2]],
        "maximum_package_formula_depth": 1,
        "node_count": 3,
        "node_names_in_replay_order": list(node_names),
        "node_names_lf_sha256": verifier._lf_hash(node_names),
        "package_formula_occurrences": 3,
    }
    verifier._verify_layered_bundle(
        bundle,
        root_name="root",
        layered_closure=("a", "b"),
        replay_rows=replay_rows,
        overrides={},
    )
    changed = deepcopy(bundle)
    changed["layers"] = [[0, 1], [2]]
    with pytest.raises(verifier.LibraryOptimizerComparisonVerificationError):
        verifier._verify_layered_bundle(
            changed,
            root_name="root",
            layered_closure=("a", "b"),
            replay_rows=replay_rows,
            overrides={},
        )


def test_artifact_row_rejects_metric_hash_fuel_and_kernel_claim_mutations() -> None:
    raw, target, proof = _artifact(fuel=40)
    dependencies: tuple[str, ...] = ()
    closure: tuple[str, ...] = ()
    source = {
        "artifact_path": "certificates/example.pl2",
        "manifest_record_index": 0,
        "manifest_root_sha256": verifier.REPLAY_MANIFEST_ROOT_SHA256,
    }
    surface = {
        "direct_dependencies": [],
        "direct_dependencies_lf_sha256": verifier._lf_hash(dependencies),
        "direct_dependency_count": 0,
        "surface_basis": verifier.SURFACE_BASES["retained-replay"],
        "transitive_closure_count": 0,
        "transitive_closure_dependencies_in_replay_order": [],
        "transitive_closure_lf_sha256": verifier._lf_hash(closure),
    }
    _decoded, observed = verifier._inspect_artifact(raw, label="fixture")
    row = {
        "artifact_sha256": observed["artifact_sha256"],
        "candidate_id": "retained-replay",
        "candidate_kind_order": 0,
        "certificate_representation": "peano-lab-v2",
        "fuel": observed["fuel"],
        "formula_sha256": observed["formula_sha256"],
        "kernel_accepted": True,
        "kernel_context": "empty",
        "logic_mode": "intuitionistic",
        "metrics": observed["metrics"],
        "proof_term_sha256": observed["proof_term_sha256"],
        "source": source,
        "surface": surface,
    }
    verifier._verify_artifact_row(
        row,
        candidate_id="retained-replay",
        kind_order=0,
        raw=raw,
        expected_artifact_sha256=_sha(raw),
        expected_fuel=40,
        expected_formula_sha256=_sha(encode_formula(target)),
        expected_proof_sha256=_sha(encode_proof(proof)),
        expected_source=source,
        dependencies=dependencies,
        closure=closure,
        label="fixture",
    )
    for mutation in (
        lambda value: value["metrics"].__setitem__("proof_nodes", 99),
        lambda value: value.__setitem__("fuel", 41),
        lambda value: value.__setitem__("artifact_sha256", "0" * 64),
        lambda value: value.__setitem__("kernel_accepted", False),
    ):
        changed = deepcopy(row)
        mutation(changed)
        with pytest.raises(verifier.LibraryOptimizerComparisonVerificationError):
            verifier._verify_artifact_row(
                changed,
                candidate_id="retained-replay",
                kind_order=0,
                raw=raw,
                expected_artifact_sha256=_sha(raw),
                expected_fuel=40,
                expected_formula_sha256=_sha(encode_formula(target)),
                expected_proof_sha256=_sha(encode_proof(proof)),
                expected_source=source,
                dependencies=dependencies,
                closure=closure,
                label="fixture",
            )


def test_strict_json_rejects_duplicate_float_noncanonical_and_cycles(tmp_path: Path) -> None:
    with pytest.raises(verifier.LibraryOptimizerComparisonVerificationError):
        verifier._decode_document(b'{"x":1,"x":2}\n', "duplicate", limit=100)
    with pytest.raises(verifier.LibraryOptimizerComparisonVerificationError):
        verifier._decode_document(b'{"x":1.0}\n', "float", limit=100)
    value = {"b": 1, "a": [True, None]}
    canonical = verifier.canonical_verification_receipt_bytes(value)
    assert canonical == b'{\n  "a": [\n    true,\n    null\n  ],\n  "b": 1\n}\n'
    noncanonical = tmp_path / "noncanonical.json"
    noncanonical.write_bytes(json.dumps(value).encode("utf-8"))
    with pytest.raises(verifier.LibraryOptimizerComparisonVerificationError):
        verifier.load_and_verify_optimizer_comparison_pilot(
            noncanonical, noncanonical, repository_root=ROOT
        )
    cyclic: list[object] = []
    cyclic.append(cyclic)
    with pytest.raises(verifier.LibraryOptimizerComparisonVerificationError):
        verifier.canonical_verification_receipt_bytes(cyclic)


def test_base64_is_canonical_and_bounded() -> None:
    raw, _target, _proof = _artifact()
    encoded = base64.b64encode(raw).decode("ascii")
    assert verifier._decode_base64(encoded, label="fixture") == raw
    with pytest.raises(verifier.LibraryOptimizerComparisonVerificationError):
        verifier._decode_base64(encoded + "\n", label="fixture")


def test_cli_has_no_default_write_and_output_is_create_only(tmp_path: Path) -> None:
    completed = subprocess.run(
        _isolated_argv(str(CLI_PATH)),
        cwd=ROOT,
        env=_isolated_environment(),
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0
    assert "no verification or retained write" in completed.stdout
    incomplete = subprocess.run(
        _isolated_argv(str(CLI_PATH), "--candidate", "missing.json"),
        cwd=ROOT,
        env=_isolated_environment(),
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert incomplete.returncode == 2
    destination = tmp_path / "receipt.json"
    raw = verifier.canonical_verification_receipt_bytes({"ok": True})
    publish_code = r'''
import importlib.util
from pathlib import Path
import sys
specification = importlib.util.spec_from_file_location("_publish_test_cli", sys.argv[1])
if specification is None or specification.loader is None:
    raise SystemExit("cannot load verifier CLI")
module = importlib.util.module_from_spec(specification)
specification.loader.exec_module(module)
destination = Path(sys.argv[2])
raw = module.canonical_verification_receipt_bytes({"ok": True})
module._publish_create_only(destination, raw)
try:
    module._publish_create_only(destination, raw)
except module.LibraryOptimizerComparisonVerificationError as exc:
    if "already exists" not in str(exc):
        raise
else:
    raise SystemExit("create-only publication accepted replacement")
'''
    published = subprocess.run(
        _isolated_argv("-c", publish_code, str(CLI_PATH), str(destination)),
        cwd=ROOT,
        env=_isolated_environment(),
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert published.returncode == 0, published.stderr or published.stdout
    assert destination.read_bytes() == raw


def _synthetic_verification_receipt() -> dict[str, object]:
    theorem_rows = []
    identities = []
    for index, name in verifier.EXPECTED_THEOREMS:
        row = {
            "artifacts": [],
            "candidate_record_sha256": "a" * 64,
            "index": index,
            "name": name,
            "nondominated_candidate_ids_in_input_order": ["retained-replay"],
            "representative_candidate_id": "retained-replay",
        }
        row["record_sha256"] = verifier._record_hash(row)
        theorem_rows.append(row)
        identities.append(
            {"index": index, "name": name, "record_sha256": row["record_sha256"]}
        )
    records_preimage = {
        "format": verifier.VERIFICATION_RECORDS_PREIMAGE_FORMAT,
        "records": identities,
        "v": 1,
    }
    body = {
        field: False for field in verifier.VERIFICATION_FALSE_FIELDS
    }
    body.update(
        {
            "aggregate": {
                "candidate_artifact_count": 9,
                "kernel_accepted_artifact_count": 9,
                "nondominated_members_total": 3,
                "pilot_theorem_count": 3,
                "representative_counts": {
                    "a2.2-direct-cut-rebuild": 0,
                    "layered-closure": 0,
                    "retained-replay": 3,
                },
            },
            "candidate": {
                "artifact_bytes": 100,
                "artifact_sha256": "b" * 64,
                "root_sha256": "c" * 64,
                "theorem_record_root_sha256": "d" * 64,
            },
            "candidate_status": "candidate",
            "format": verifier.VERIFICATION_FORMAT,
            "id": verifier.VERIFICATION_ID,
            "kernel_artifacts_verified": True,
            "logic_mode": "intuitionistic",
            "producer_source_state": {
                "artifact_bytes": 10,
                "artifact_sha256": "e" * 64,
                "root_sha256": "f" * 64,
                "semantic_sha256": "0" * 64,
            },
            "producer_source_state_sha256": "0" * 64,
            "status": "passed",
            "theorem_count": 3,
            "theorem_records": {
                "count": 3,
                "preimage": records_preimage,
                "root_sha256": verifier._sha256_json(records_preimage),
            },
            "v": 1,
            "verifier": {
                "bytecode_write_disabled": True,
                "import_policy": "stdlib-and-peano-kernel-only",
                "kernel_sources": [],
                "load_mode": "direct-source-module-without-training-package-init",
                "path": "training/peano_hydra/library_optimizer_comparison_verifier.py",
                "pycache_prefix": verifier.PYCACHE_PREFIX,
                "safe_path": True,
                "sha256": "1" * 64,
                "site_import_disabled": True,
                "source_loader_preflight": (
                    "pathfinder-sourcefileloader-exact-origin"
                ),
                "stdlib_precedes_peano_root": True,
                "user_site_disabled": True,
            },
        }
    )
    assert set(body) == set(verifier.VERIFICATION_RECEIPT_BODY_FIELDS)
    preimage = {
        "format": verifier.VERIFICATION_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": 1,
    }
    return {
        **body,
        "root_preimage": preimage,
        "root_sha256": verifier._sha256_json(preimage),
        "theorems": theorem_rows,
    }


def test_deep_receipt_validator_rejects_status_false_flag_and_reroot_forgery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = _synthetic_verification_receipt()
    monkeypatch.setattr(
        verifier,
        "verify_optimizer_comparison_pilot",
        lambda *args, **kwargs: deepcopy(receipt),
    )
    assert (
        verifier.validate_optimizer_comparison_verification_receipt(
            receipt,
            candidate={},
            producer_source_state={},
            repository_root=ROOT,
        )
        == receipt
    )
    changed = deepcopy(receipt)
    changed["status"] = "candidate"
    with pytest.raises(verifier.LibraryOptimizerComparisonVerificationError):
        verifier.validate_optimizer_comparison_verification_receipt(
            changed, candidate={}, producer_source_state={}, repository_root=ROOT
        )
    changed = deepcopy(receipt)
    changed["evaluation_eligible"] = True
    with pytest.raises(verifier.LibraryOptimizerComparisonVerificationError):
        verifier.validate_optimizer_comparison_verification_receipt(
            changed, candidate={}, producer_source_state={}, repository_root=ROOT
        )
    # Recompute the public root around a forged candidate hash.  The envelope
    # is internally self-consistent, but exact independent reconstruction must
    # still reject it.
    changed = deepcopy(receipt)
    changed["candidate"]["artifact_sha256"] = "9" * 64
    body = {
        key: changed[key] for key in verifier.VERIFICATION_RECEIPT_BODY_FIELDS
    }
    changed["root_preimage"] = {
        "format": verifier.VERIFICATION_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": 1,
    }
    changed["root_sha256"] = verifier._sha256_json(changed["root_preimage"])
    with pytest.raises(
        verifier.LibraryOptimizerComparisonVerificationError,
        match="reconstruction",
    ):
        verifier.validate_optimizer_comparison_verification_receipt(
            changed, candidate={}, producer_source_state={}, repository_root=ROOT
        )
