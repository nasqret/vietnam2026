"""Synthetic and mutation contracts for the tactic-free A2.3c verifier.

No test in this file executes a negative replay.  A compact completed result is
assembled from frozen structural constants; one focused target-identity test
constructs formulas without applying tactics, and CLI tests exercise only the
structural verifier and create-only publication boundary.
"""

from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import replace
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = (
    ROOT
    / "training/peano_hydra/"
    "library_pilot_dependency_vector_negative_replay_verifier.py"
)
CLI_PATH = (
    ROOT
    / "scripts/"
    "verify_peano_hydra_library_pilot_dependency_vector_negative_replay_result.py"
)
ISOLATED_PYTHON = shutil.which("python3.12") or shutil.which("python3.11")


def _load_verifier(name: str = "_a23c_structural_verifier_test"):
    specification = importlib.util.spec_from_file_location(name, MODULE_PATH)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


verifier = _load_verifier()


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _isolated_environment() -> dict[str, str]:
    environment = dict(os.environ)
    for name in (
        "PYTHONCASEOK",
        "PYTHONHOME",
        "PYTHONINSPECT",
        "PYTHONOPTIMIZE",
        "PYTHONPATH",
        "PYTHONSTARTUP",
        "PYTHONUSERBASE",
        "PYTHONWARNINGS",
    ):
        environment.pop(name, None)
    environment["PYTHONHASHSEED"] = "23"
    environment["PYTHONPYCACHEPREFIX"] = verifier.PYCACHE_PREFIX
    return environment


def _isolated_argv(*arguments: str) -> list[str]:
    if ISOLATED_PYTHON is None:
        pytest.skip("Python 3.11+ with -P safe-path support is required")
    return [ISOLATED_PYTHON, "-B", "-P", "-s", "-S", *arguments]


def _environment(schema: dict[str, object]) -> dict[str, object]:
    callables = verifier._expected_callable_receipt(schema)
    replayer = {
        "bytes": verifier.PROTOCOL_SOURCE_FILES[1][1],
        "load_mode": "authenticated-source-bytes-source_to_code-exec",
        "module_name": "_peano_hydra_a23c_independent_negative_replayer",
        "path": verifier.PROTOCOL_SOURCE_FILES[1][0],
        "pycache_prefix": "/proc/peano-hydra-a23c-disabled-pycache",
        "sha256": verifier.PROTOCOL_SOURCE_FILES[1][2],
        "source_loader": "importlib.machinery.SourceFileLoader",
    }
    schema_identity = {
        "artifact_sha256": verifier.PROTOCOL_SOURCE_FILES[0][2],
        "bytes": verifier.PROTOCOL_SOURCE_FILES[0][1],
        "id": verifier.SCHEMA_ID,
        "semantic_sha256": verifier.SCHEMA_SEMANTIC_SHA256,
        "v": 1,
    }
    preimage = {
        "callables": callables,
        "fixed_inputs": deepcopy(schema["fixed_inputs"]),
        "format": (
            "peano-hydra-library-pilot-dependency-vector-negative-replay-"
            "environment-preimage"
        ),
        "implementation_source_root_sha256": (
            "b37836ec81ab2f0af638427a937d92519b5b70579de86d38c9321514692f55c1"
        ),
        "runtime": deepcopy(schema["runtime_binding"]),
        "replayer": replayer,
        "schema": schema_identity,
        "v": 1,
    }
    return {
        "callables": callables,
        "fixed_input_count": 6,
        "implementation_source_count": 39,
        "implementation_source_root_sha256": (
            "b37836ec81ab2f0af638427a937d92519b5b70579de86d38c9321514692f55c1"
        ),
        "preimage": preimage,
        "replayer": replayer,
        "root_sha256": verifier._sha256_json(preimage),
        "runtime": deepcopy(schema["runtime_binding"]),
        "status": "all-execution-bindings-authenticated",
    }


def _synthetic_candidate() -> dict[str, object]:
    _sources, schema, _raw = verifier._authenticate_protocol_sources(ROOT)
    fixed, _evidence = verifier._authenticate_retained_evidence(ROOT, schema)
    tasks = verifier._registered_tasks(schema, fixed["replay_manifest"])
    baselines_expected, retained = verifier._validate_retained_a23b_candidate(
        fixed["a2.3b_candidate"], tasks
    )
    baselines: list[dict[str, object]] = []
    for expected in verifier.EXPECTED_THEOREMS:
        retained_baseline = baselines_expected[expected["name"]]
        body: dict[str, object] = {
            "command_count": retained_baseline["command_count"],
            "dependencies": list(expected["dependencies"]),
            "dependency_count": retained_baseline["dependency_count"],
            "formula_sha256": retained_baseline["formula_sha256"],
            "name": expected["name"],
            "proof_sha256": retained_baseline["proof_sha256"],
            "proof_structure": deepcopy(retained_baseline["proof_structure"]),
            "script_sha256": expected["script_sha256"],
            "status": "full-vector-baseline-kernel-accepted",
            "theorem_index": expected["index"],
        }
        body["record_sha256"] = verifier._record_hash(body)
        baselines.append(body)
    observations = [verifier._expected_observation(task) for task in tasks]
    theorems: list[dict[str, object]] = []
    offset = 0
    for expected, baseline in zip(
        verifier.EXPECTED_THEOREMS, baselines, strict=True
    ):
        count = len(expected["dependencies"])
        selected = observations[offset : offset + count]
        offset += count
        body = {
            **{field: False for field in verifier.GLOBAL_FALSE_FIELDS},
            "baseline": deepcopy(baseline),
            "index": expected["index"],
            "name": expected["name"],
            "negative_observation_count": count,
            "negative_observations": deepcopy(selected),
            "negative_observations_independently_verified": True,
        }
        body["record_sha256"] = verifier._record_hash(body)
        theorems.append(body)
    body: dict[str, object] = {
        **{field: False for field in verifier.GLOBAL_FALSE_FIELDS},
        "aggregate": {
            "full_vector_baseline_count": 3,
            "independent_shared_observation_count": 22,
            "retained_route_row_count": 44,
            "route_rows_per_shared_observation": 2,
            "theorem_count": 3,
        },
        "baseline_records": baselines,
        "baselines": verifier._records_bundle(
            baselines, kind="full-vector-baselines"
        ),
        "campaign_executed": True,
        "environment": _environment(schema),
        "format": verifier.CANDIDATE_FORMAT,
        "id": verifier.CANDIDATE_ID,
        "independence": deepcopy(schema["independence_contract"]),
        "logic_mode": verifier.LOGIC_MODE,
        "negative_observation_records": observations,
        "negative_observations": verifier._records_bundle(
            observations, kind="independent-shared-root-body-negative-replays"
        ),
        "negative_observations_independently_verified": True,
        "predecessors": deepcopy(schema["fixed_inputs"]),
        "result_exists": True,
        "retained_route_join": verifier._expected_retained_join(
            observations, retained
        ),
        "schema": {
            "artifact_sha256": verifier.PROTOCOL_SOURCE_FILES[0][2],
            "bytes": verifier.PROTOCOL_SOURCE_FILES[0][1],
            "id": verifier.SCHEMA_ID,
            "semantic_sha256": verifier.SCHEMA_SEMANTIC_SHA256,
            "v": 1,
        },
        "status": "passed",
        "theorem_count": 3,
        "theorem_records": verifier._records_bundle(theorems, kind="theorems"),
        "theorems": theorems,
        "v": 1,
    }
    preimage = {
        "format": verifier.CANDIDATE_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": 1,
    }
    return {**body, "root_preimage": preimage, "root_sha256": verifier._sha256_json(preimage)}


def _refresh_candidate(value: dict[str, object]) -> None:
    baselines = value["baseline_records"]
    observations = value["negative_observation_records"]
    for record in (*baselines, *observations):
        record["record_sha256"] = verifier._record_hash(record)
    offset = 0
    for theorem, baseline, expected in zip(
        value["theorems"], baselines, verifier.EXPECTED_THEOREMS, strict=True
    ):
        count = len(expected["dependencies"])
        theorem["baseline"] = deepcopy(baseline)
        theorem["negative_observations"] = deepcopy(
            observations[offset : offset + count]
        )
        theorem["negative_observation_count"] = count
        theorem["record_sha256"] = verifier._record_hash(theorem)
        offset += count
    value["baselines"] = verifier._records_bundle(
        baselines, kind="full-vector-baselines"
    )
    value["negative_observations"] = verifier._records_bundle(
        observations, kind="independent-shared-root-body-negative-replays"
    )
    value["theorem_records"] = verifier._records_bundle(
        value["theorems"], kind="theorems"
    )
    join_by_key = {
        (row["name"], row["omitted_dependency"]): row
        for row in value["retained_route_join"]["joins"]
    }
    ordered = []
    for observation in observations:
        row = join_by_key[(observation["name"], observation["omitted_dependency"])]
        row["fresh_observation_record_sha256"] = observation["record_sha256"]
        ordered.append(row)
    value["retained_route_join"]["joins"] = ordered
    join_preimage = {
        "format": verifier.RETAINED_JOIN_PREIMAGE_FORMAT,
        "joins": deepcopy(ordered),
        "v": 1,
    }
    value["retained_route_join"]["preimage"] = join_preimage
    value["retained_route_join"]["root_sha256"] = verifier._sha256_json(
        join_preimage
    )
    body = {
        key: item
        for key, item in value.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    value["root_preimage"] = {
        "format": verifier.CANDIDATE_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": 1,
    }
    value["root_sha256"] = verifier._sha256_json(value["root_preimage"])


def _receipt(candidate: dict[str, object]) -> dict[str, object]:
    raw = verifier.canonical_negative_replay_verification_receipt_bytes(candidate)
    return verifier._construct_verification_receipt(
        candidate,
        candidate_raw=raw,
        repository_root=ROOT,
        require_runtime_boundary=False,
    )


def test_static_verifier_import_policy_is_standard_library_only() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)
    allowed = {
        "__future__",
        "ast",
        "copy",
        "hashlib",
        "json",
        "os",
        "pathlib",
        "re",
        "stat",
        "sys",
        "typing",
    }
    assert set(imports) <= allowed
    assert not any(name.startswith(("peano_lab", "training")) for name in imports)
    assert not {"exec", "eval", "compile_candidate_body", "apply_tactic"} & set(calls)


def test_public_surface_and_claim_split_are_narrow() -> None:
    assert set(verifier.__all__) == {
        "LibraryPilotDependencyVectorNegativeReplayVerificationError",
        "PYCACHE_PREFIX",
        "VERIFICATION_FALSE_FIELDS",
        "VERIFICATION_FORMAT",
        "VERIFICATION_ID",
        "VERIFICATION_RECEIPT_BODY_FIELDS",
        "VERIFICATION_RECEIPT_FIELDS",
        "VERIFICATION_VERSION",
        "canonical_negative_replay_verification_receipt_bytes",
        "load_and_verify_pilot_dependency_vector_negative_replay_result",
        "validate_pilot_dependency_vector_negative_replay_verification_receipt",
        "verify_pilot_dependency_vector_negative_replay_result",
    }
    assert {
        "a2_complete",
        "dependency_necessity_established",
        "dependency_vectors_complete",
        "execution_receipt_bound",
        "kernel_baselines_independently_reexecuted",
        "minimality_claim",
        "negative_observations_independently_verified",
        "negative_replays_independently_reexecuted",
        "route_rejections_independently_verified",
        "tactic_semantics_independently_verified",
        "vector_optimizer_executed",
    }.issubset(verifier.VERIFICATION_FALSE_FIELDS)
    assert {
        "candidate_negative_observations_structurally_verified",
        "producer_independence_source_verified",
        "structural_result_verified",
    }.issubset(verifier.VERIFICATION_RECEIPT_BODY_FIELDS)


def test_frozen_protocol_and_retained_source_evidence_are_exact() -> None:
    protocol, schema, source = verifier._authenticate_protocol_sources(ROOT)
    fixed, retained = verifier._authenticate_retained_evidence(ROOT, schema)
    assert protocol["count"] == 4
    assert protocol["independence_source_scan"] == (
        "no-a2.3b-wrapper-import-or-compile-candidate-body-call"
    )
    assert retained["count"] == 8
    assert set(fixed) == {
        "a2.3b_candidate",
        "a2.3b_collection",
        "a2.3b_execution",
        "a2.3b_producer_git_verification",
        "a2.3b_producer_source_state",
        "a2.3b_verification",
        "replay_manifest",
        "replay_report",
    }
    assert _sha(source) == verifier.PROTOCOL_SOURCE_FILES[1][2]


def test_static_target_hashes_crosscheck_frozen_constructor_without_tactics() -> None:
    py_root = ROOT / "peano-lab/py"
    for path in (str(ROOT), str(py_root)):
        if path not in sys.path:
            sys.path.insert(0, path)
    import training.peano_hydra.library_pilot_dependency_vector_negative_replay as replay

    schema = replay.pilot_dependency_vector_negative_replay_schema(ROOT)
    specs, tasks = replay._registered_specs_and_tasks(schema)
    by_name = {spec.name: spec for spec in specs}
    expected = {
        (name, omitted): target
        for name, omitted, _index, _command, target in verifier.EXPECTED_TASKS
    }
    actual: dict[tuple[str, str], str] = {}
    for task in tasks:
        trial = replace(
            by_name[task.theorem_name], dependencies=task.trial_dependencies
        )
        formula = replay.DEFAULT_NEGATIVE_REPLAY_HOOKS.replay_target(trial)
        raw = replay.DEFAULT_NEGATIVE_REPLAY_HOOKS.encode_formula(formula)
        actual[(task.theorem_name, task.omitted_dependency)] = _sha(raw)
    assert actual == expected


def test_synthetic_completed_result_receives_only_structural_authority() -> None:
    candidate = _synthetic_candidate()
    receipt = _receipt(candidate)
    assert receipt["aggregate"] == {
        "full_vector_baseline_count": 3,
        "negative_observation_count": 22,
        "retained_route_pair_count": 22,
        "retained_route_row_count": 44,
        "theorem_count": 3,
    }
    assert receipt["candidate_negative_observations_structurally_verified"] is True
    assert receipt["producer_independence_source_verified"] is True
    assert receipt["structural_result_verified"] is True
    for field in verifier.VERIFICATION_FALSE_FIELDS:
        assert receipt[field] is False, field
        assert all(theorem[field] is False for theorem in receipt["theorems"])
    assert receipt["verifier"]["tactic_free"] is True
    assert receipt["verifier"]["import_policy"] == (
        "python-standard-library-only-no-peano-or-training-import"
    )


@pytest.mark.parametrize(
    "mutate",
    (
        lambda value: value.__setitem__("a2_complete", True),
        lambda value: value["aggregate"].__setitem__(
            "independent_shared_observation_count", 21
        ),
        lambda value: value["environment"].__setitem__(
            "status", "claimed-without-binding"
        ),
        lambda value: value["independence"].__setitem__(
            "route_specific_assemblers_called", True
        ),
        lambda value: value["baseline_records"][0]["proof_structure"].__setitem__(
            "nodes", 92
        ),
        lambda value: value["negative_observation_records"][0].__setitem__(
            "target_formula_sha256", "0" * 64
        ),
        lambda value: value["negative_observation_records"][0]["failure"].__setitem__(
            "message", "unknown hypothesis 'forged'."
        ),
        lambda value: value["negative_observation_records"][0]["failure"].__setitem__(
            "command_index", 8
        ),
        lambda value: value["retained_route_join"]["joins"][0].__setitem__(
            "route_row_count", 1
        ),
        lambda value: value["theorems"][0].__setitem__(
            "negative_observations_independently_verified", False
        ),
    ),
)
def test_candidate_mutations_are_rejected(mutate) -> None:
    forged = _synthetic_candidate()
    mutate(forged)
    _refresh_candidate(forged)
    with pytest.raises(
        verifier.LibraryPilotDependencyVectorNegativeReplayVerificationError
    ):
        _receipt(forged)


def test_fully_rehashed_observation_reorder_is_rejected() -> None:
    forged = _synthetic_candidate()
    forged["negative_observation_records"][0:2] = reversed(
        forged["negative_observation_records"][0:2]
    )
    _refresh_candidate(forged)
    with pytest.raises(
        verifier.LibraryPilotDependencyVectorNegativeReplayVerificationError,
        match="22-observation",
    ):
        _receipt(forged)


def test_deep_receipt_validator_reconstructs_and_rejects_false_claim() -> None:
    candidate = _synthetic_candidate()
    receipt = _receipt(candidate)
    original_boundary = verifier._require_runtime_import_boundary
    verifier._require_runtime_import_boundary = lambda: None
    try:
        assert verifier.validate_pilot_dependency_vector_negative_replay_verification_receipt(
            receipt,
            candidate=candidate,
            candidate_raw=verifier.canonical_negative_replay_verification_receipt_bytes(
                candidate
            ),
            repository_root=ROOT,
        ) == receipt
        forged = deepcopy(receipt)
        forged["tactic_semantics_independently_verified"] = True
        body = {
            key: item
            for key, item in forged.items()
            if key not in {"root_preimage", "root_sha256"}
        }
        forged["root_preimage"] = {
            "format": verifier.VERIFICATION_ROOT_PREIMAGE_FORMAT,
            "payload": body,
            "v": 1,
        }
        forged["root_sha256"] = verifier._sha256_json(forged["root_preimage"])
        with pytest.raises(
            verifier.LibraryPilotDependencyVectorNegativeReplayVerificationError,
            match="forbidden claim",
        ):
            verifier.validate_pilot_dependency_vector_negative_replay_verification_receipt(
                forged,
                candidate=candidate,
                repository_root=ROOT,
            )
    finally:
        verifier._require_runtime_import_boundary = original_boundary


@pytest.mark.parametrize(
    "raw",
    (
        b'{"x":1,"x":2}\n',
        b'{"x":1.5}\n',
        b'{"x":NaN}\n',
        b'[]\n',
    ),
)
def test_strict_decoder_rejects_ambiguous_json(raw: bytes) -> None:
    with pytest.raises(
        verifier.LibraryPilotDependencyVectorNegativeReplayVerificationError
    ):
        verifier._decode_document(raw, label="synthetic", limit=1_024)


def test_safe_reader_rejects_symlink_and_oversize(tmp_path: Path) -> None:
    target = tmp_path / "target.json"
    target.write_bytes(b"{}\n")
    link = tmp_path / "link.json"
    link.symlink_to(target)
    with pytest.raises(
        verifier.LibraryPilotDependencyVectorNegativeReplayVerificationError,
        match="non-symlink",
    ):
        verifier._safe_file(link, label="synthetic", limit=1_024)
    with pytest.raises(
        verifier.LibraryPilotDependencyVectorNegativeReplayVerificationError,
        match="exceeded",
    ):
        verifier._safe_file(target, label="synthetic", limit=1)


def test_cli_exact_loader_is_create_only_and_tactic_free(tmp_path: Path) -> None:
    candidate = _synthetic_candidate()
    candidate_path = tmp_path / "candidate.json"
    output = tmp_path / "receipt.json"
    candidate_path.write_bytes(
        verifier.canonical_negative_replay_verification_receipt_bytes(candidate)
    )
    completed = subprocess.run(
        _isolated_argv(
            str(CLI_PATH),
            "--candidate",
            str(candidate_path),
            "--output",
            str(output),
            "--repository-root",
            str(ROOT),
        ),
        cwd=ROOT,
        env=_isolated_environment(),
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    assert "no tactic replay or execution binding" in completed.stdout
    receipt = json.loads(output.read_bytes())
    assert output.read_bytes() == verifier.canonical_negative_replay_verification_receipt_bytes(
        receipt
    )
    assert stat.S_IMODE(output.stat().st_mode) == 0o644
    assert receipt["negative_replays_independently_reexecuted"] is False
    assert receipt["execution_receipt_bound"] is False
    second = subprocess.run(
        _isolated_argv(
            str(CLI_PATH),
            "--candidate",
            str(candidate_path),
            "--output",
            str(output),
            "--repository-root",
            str(ROOT),
        ),
        cwd=ROOT,
        env=_isolated_environment(),
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert second.returncode != 0
    assert "create-only" in second.stderr


def test_cli_no_args_has_no_verification_or_write() -> None:
    completed = subprocess.run(
        _isolated_argv(str(CLI_PATH)),
        cwd=ROOT,
        env=_isolated_environment(),
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    assert "no candidate verified and no file written" in completed.stdout


def test_cli_rejects_nonisolated_invocation() -> None:
    completed = subprocess.run(
        [sys.executable, str(CLI_PATH)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert completed.returncode != 0
    assert "requires controlled" in completed.stderr


def test_cli_pin_matches_exact_verifier_source() -> None:
    source = CLI_PATH.read_text(encoding="utf-8")
    assert f"VERIFIER_SOURCE_BYTES = {MODULE_PATH.stat().st_size:_}" in source
    assert _sha(MODULE_PATH.read_bytes()) in source
