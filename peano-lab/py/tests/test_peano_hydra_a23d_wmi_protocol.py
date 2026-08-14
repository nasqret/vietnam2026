"""No-network tests for the bounded Hydra A2.3d Cut-liveness protocol."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
for source_root in (ROOT / "peano-lab/py", ROOT):
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))

from training.peano_hydra import (  # noqa: E402
    library_pilot_dependency_vector_cut_liveness as producer,
)
from training.peano_hydra import (  # noqa: E402
    library_pilot_dependency_vector_cut_liveness_verifier as verifier,
)


RUNNER_PATH = ROOT / "scripts/run_peano_hydra_a23d_cut_liveness_wmi.py"
SOURCE_STATE = ROOT / "scripts/build_peano_hydra_a23d_cut_liveness_source_state.py"
SUBMIT = ROOT / "scripts/submit_wmi_hydra_a23d_cut_liveness.sh"
COLLECT = ROOT / "scripts/collect_wmi_hydra_a23d_cut_liveness.sh"
SBATCH = ROOT / "slurm/peano_wmi_hydra_a23d_cut_liveness.sbatch"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


WMI = _load(RUNNER_PATH, "_test_peano_hydra_a23d_wmi")


def _canonical(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


@pytest.fixture(scope="module")
def scientific_documents():
    candidate = producer.build_candidate_dependency_vector_cut_liveness(ROOT)
    candidate_raw = producer.canonical_document_bytes(candidate)
    receipt = verifier.verify_dependency_vector_cut_liveness(candidate, ROOT)
    receipt_raw = verifier.canonical_verification_bytes(receipt)
    source_body = {"format": WMI.FORMAT_SOURCE_STATE, "v": 1}
    source_preimage = {
        "format": WMI.FORMAT_SOURCE_STATE_ROOT,
        "payload": source_body,
        "v": 1,
    }
    source_state = {
        **source_body,
        "root_preimage": source_preimage,
        "root_sha256": WMI._compact_sha256(source_preimage),
    }
    return candidate, candidate_raw, receipt, receipt_raw, source_state


def _install_fake_ssh(tmp_path: Path) -> tuple[Path, Path]:
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    log = tmp_path / "ssh-argv.bin"
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text(
        """#!/bin/bash
set -eu
: "${WMI_TEST_SSH_LOG:?}"
{
  printf '%s\\0' "$#"
  printf '%s\\0' "$@"
} >> "$WMI_TEST_SSH_LOG"
cat > /dev/null
""",
        encoding="utf-8",
    )
    fake_ssh.chmod(0o755)
    return fake_bin, log


def _fake_ssh_calls(log: Path) -> list[list[str]]:
    fields = log.read_bytes().split(b"\0")
    assert fields.pop() == b""
    calls: list[list[str]] = []
    cursor = 0
    while cursor < len(fields):
        count = int(fields[cursor].decode("ascii"))
        cursor += 1
        call = [
            field.decode("utf-8")
            for field in fields[cursor : cursor + count]
        ]
        assert len(call) == count
        calls.append(call)
        cursor += count
    return calls


def _clean_protocol_repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repository"
    repository.mkdir()
    protocol_sources = {
        *WMI.INFRASTRUCTURE_SOURCES,
        *(path for path, _digest in WMI.FROZEN_PRODUCER_SOURCES),
    }
    for relative in sorted(protocol_sources):
        destination = repository / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    for argv in (
        ("init", "-q"),
        ("config", "user.email", "hydra-test@example.invalid"),
        ("config", "user.name", "Hydra Test"),
        ("add", "."),
        ("commit", "-q", "-m", "fixture"),
    ):
        subprocess.run(
            ["git", *argv],
            cwd=repository,
            check=True,
            capture_output=True,
        )
    return repository


def test_protocol_constants_bind_one_root_transform_and_runtime() -> None:
    assert WMI.EXPECTED_ROOT == (256, "odd_add_odd")
    assert WMI.EXPECTED_INPUT_VECTOR == (
        "mul_add",
        "add_succ_left",
        "add_assoc",
        "add_comm",
    )
    assert WMI.EXPECTED_DERIVED_VECTOR == ("mul_add", "add_comm")
    assert WMI.EXPECTED_CANDIDATE_BYTES == 74_579
    assert WMI.EXPECTED_CANDIDATE_SHA256 == (
        "a9077a7b272930477b93c48baef8b14fe0e443627c52177efa863ed0c18375e0"
    )
    assert WMI.EXPECTED_CANDIDATE_ROOT == (
        "fd0497da5ea0c12ecb14fa168637ea6d54006ce9b9295010e879df37f5dcd835"
    )
    assert WMI.EXPECTED_VERIFIER_BYTES == 12_737
    assert WMI.EXPECTED_VERIFIER_SHA256 == (
        "8f6531d3a0544a6d308ebd0abf7e41ed2436984758e76e66797ff1023e0a2821"
    )
    assert WMI.EXPECTED_VERIFIER_ROOT == (
        "b3c253674f488eeed1e5a14e4be6632b0fe6ed946cf611ee0b3fde66f79acad7"
    )
    assert WMI.FORMAT_VERIFIER.endswith("independent-verification-v1")
    assert WMI.EXPECTED_RESOURCES == {
        "partition": "cpu_idle",
        "nodes": 1,
        "ntasks": 1,
        "cpus_per_task": 1,
        "memory_mib": 4096,
        "time_limit": "00:15:00",
        "time_limit_seconds": 900,
    }
    assert WMI.PRODUCER_TIMEOUT_SECONDS == 60
    assert WMI.VERIFIER_TIMEOUT_SECONDS == 90
    assert WMI.PINNED_WMI_PYTHON.endswith("/bin/python")
    runner = RUNNER_PATH.read_text(encoding="utf-8")
    assert "3.12.12" in runner
    assert "sys.flags.no_user_site != 1" in runner
    assert "sys.flags.optimize != 0" in runner


def test_runner_and_source_generator_share_exact_six_file_vector() -> None:
    generator = _load(SOURCE_STATE, "_test_a23d_source_state_vector")
    assert WMI.FROZEN_PRODUCER_SOURCES == tuple(
        (path.as_posix(), digest)
        for path, digest in generator.FROZEN_PROTOCOL_SOURCES
    )
    assert len(WMI.FROZEN_PRODUCER_SOURCES) == 6


def test_runner_deeply_consumes_external_clean_git_receipts(
    tmp_path: Path,
) -> None:
    generator = _load(SOURCE_STATE, "_test_a23d_source_state_receipt")
    repository = tmp_path / "clean-repository"
    repository.mkdir()
    for relative in (
        *(Path(path) for path, _digest in WMI.FROZEN_PRODUCER_SOURCES),
        Path(WMI.SOURCE_STATE_GENERATOR),
    ):
        destination = repository / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    for argv in (
        ("init", "-q"),
        ("config", "user.email", "hydra-test@example.invalid"),
        ("config", "user.name", "Hydra Test"),
        ("add", "."),
        ("commit", "-q", "-m", "fixture"),
    ):
        subprocess.run(
            ["git", *argv], cwd=repository, check=True, capture_output=True
        )
    state, receipt, _envelope = generator.build_cut_liveness_evidence(repository)
    source_raw = generator.canonical_document_bytes(state)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    tree = subprocess.run(
        ["git", "rev-parse", "HEAD^{tree}"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    WMI._validate_source_state_document(
        state,
        raw=source_raw,
        source_root=repository,
        commit=commit,
        tree=tree,
    )
    WMI._validate_git_receipt_document(
        receipt,
        source_root=repository,
        source_state=state,
        source_state_raw=source_raw,
        commit=commit,
        tree=tree,
    )


def test_candidate_consumer_binds_exact_proof_producing_result(
    scientific_documents,
) -> None:
    candidate, raw, _receipt, _receipt_raw, source_state = scientific_documents
    accepted, record = WMI._validate_candidate_document(
        candidate,
        raw=raw,
        filename="candidate.json",
        source_state=source_state,
    )
    assert accepted == candidate
    assert record == {
        "artifact_bytes": 74_579,
        "artifact_sha256": WMI.EXPECTED_CANDIDATE_SHA256,
        "derived_direct_dependencies": ["mul_add", "add_comm"],
        "path": "candidate.json",
        "root_sha256": WMI.EXPECTED_CANDIDATE_ROOT,
        "source_state_root_sha256": source_state["root_sha256"],
        "theorem_index": 256,
        "theorem_name": "odd_add_odd",
    }

    for mutation in ("vector", "artifact", "authority", "kernel"):
        forged = deepcopy(candidate)
        if mutation == "vector":
            forged["theorem"]["derived_direct_vector"]["dependencies"] = [
                "mul_add"
            ]
        elif mutation == "artifact":
            forged["theorem"]["candidate_artifact"]["artifact_sha256"] = "0" * 64
        elif mutation == "authority":
            forged["optimized_best_known"] = True
        else:
            forged["theorem"]["candidate_artifact"][
                "empty_context_kernel_checked"
            ] = False
        with pytest.raises(WMI.A23DWMIError):
            WMI._validate_candidate_document(
                forged,
                raw=_canonical(forged),
                filename="forged.json",
                source_state=source_state,
            )


def test_verifier_consumer_binds_independent_transform_and_false_claims(
    scientific_documents,
) -> None:
    candidate, candidate_raw, receipt, receipt_raw, source_state = (
        scientific_documents
    )
    source_raw = _canonical(source_state)
    assert len(receipt_raw) == WMI.EXPECTED_VERIFIER_BYTES
    WMI._validate_verifier_receipt(
        receipt,
        candidate=candidate,
        candidate_raw=candidate_raw,
        source_state=source_state,
        source_state_raw=source_raw,
        source_root=ROOT,
    )
    for mutation in ("false-claim", "vector", "proof", "candidate"):
        forged = deepcopy(receipt)
        if mutation == "false-claim":
            forged["optimized_vector_independently_audited"] = True
        elif mutation == "vector":
            forged["theorem"]["derived_direct_dependencies"] = ["mul_add"]
        elif mutation == "proof":
            forged["theorem"]["output_proof_term_sha256"] = "0" * 64
        else:
            forged["candidate_root_sha256"] = "0" * 64
        with pytest.raises(WMI.A23DWMIError):
            WMI._validate_verifier_receipt(
                forged,
                candidate=candidate,
                candidate_raw=candidate_raw,
                source_state=source_state,
                source_state_raw=source_raw,
                source_root=ROOT,
            )


def _file_evidence(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    return {
        "bytes": len(raw),
        "path": path.name,
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _process_fixture(
    *, role: str, argv: list[str], run_root: Path, timeout: int
) -> dict[str, object]:
    return {
        "argv": argv,
        "duration_seconds_millis": 1,
        "environment": WMI._isolated_environment(0),
        "finished_at": "2026-08-14T00:00:01+00:00",
        "hash_seed": 0,
        "output_limit_reached": False,
        "returncode": 0,
        "role": role,
        "started_at": "2026-08-14T00:00:00+00:00",
        "stderr": _file_evidence(run_root / f"{role}.stderr.log"),
        "stdout": _file_evidence(run_root / f"{role}.stdout.log"),
        "timed_out": False,
        "timeout_seconds": timeout,
    }


def _execution_fixture(
    tmp_path: Path, scientific_documents
) -> tuple[dict[str, object], dict[str, object], Path, Path, Path]:
    candidate, candidate_raw, receipt, receipt_raw, source_state = (
        scientific_documents
    )
    source_root = ROOT
    input_root = tmp_path / "inputs"
    run_root = tmp_path / "run"
    input_root.mkdir()
    run_root.mkdir()
    source_raw = _canonical(source_state)
    inputs = {
        "cut-liveness-source-state.json": source_raw,
        "cut-liveness-git-verification-receipt.json": _canonical(
            {"fixture": "git-receipt"}
        ),
        "wmi-infrastructure-manifest.json": _canonical(
            {"fixture": "infrastructure"}
        ),
    }
    for name, raw in inputs.items():
        (input_root / name).write_bytes(raw)

    candidate_paths = (
        run_root / WMI.CANDIDATE_FILENAME,
        run_root / WMI.SECOND_PRODUCER_FILENAME,
    )
    for path in candidate_paths:
        path.write_bytes(candidate_raw)
    verifier_path = run_root / WMI.VERIFIER_RECEIPT_FILENAME
    verifier_path.write_bytes(receipt_raw)
    for index in range(2):
        (run_root / f"producer-{index}.stdout.log").write_bytes(candidate_raw)
        (run_root / f"producer-{index}.stderr.log").write_bytes(b"")
    (run_root / "independent-verifier.stdout.log").write_bytes(receipt_raw)
    (run_root / "independent-verifier.stderr.log").write_bytes(b"")

    commit = "1" * 40
    tree = "2" * 40
    snapshot = "3" * 64
    sync_timestamp = "2026-08-14T00:00:00Z"
    provenance_sha = "4" * 64
    submission = {
        "git_commit": commit,
        "git_receipt_sha256": hashlib.sha256(
            inputs["cut-liveness-git-verification-receipt.json"]
        ).hexdigest(),
        "git_tree": tree,
        "infrastructure_sha256": hashlib.sha256(
            inputs["wmi-infrastructure-manifest.json"]
        ).hexdigest(),
        "provenance_sha256": provenance_sha,
        "snapshot_sha256": snapshot,
        "source_state_sha256": hashlib.sha256(source_raw).hexdigest(),
        "sync_timestamp": sync_timestamp,
    }
    runtime = {
        "dont_write_bytecode": True,
        "executable": WMI.PINNED_WMI_PYTHON,
        "implementation": "CPython",
        "machine": "x86_64",
        "no_site": True,
        "optimize": 0,
        "pycache_prefix": WMI.DISABLED_PYCACHE_PREFIX,
        "python_version": "3.12.12",
        "safe_path": True,
        "user_site_disabled": True,
    }
    producer_argv = [
        WMI.PINNED_WMI_PYTHON,
        "-B",
        "-P",
        "-s",
        "-S",
        "scripts/build_peano_hydra_library_pilot_dependency_vector_cut_liveness.py",
        "--build",
        "--repository-root",
        str(source_root),
    ]
    verifier_argv = [
        WMI.PINNED_WMI_PYTHON,
        "-B",
        "-P",
        "-s",
        "-S",
        WMI.VERIFIER_CLI_PATH,
        "--verify",
        str(candidate_paths[0]),
        "--repository-root",
        str(source_root),
    ]
    processes = [
        _process_fixture(
            role="producer-0",
            argv=producer_argv,
            run_root=run_root,
            timeout=WMI.PRODUCER_TIMEOUT_SECONDS,
        ),
        _process_fixture(
            role="producer-1",
            argv=producer_argv,
            run_root=run_root,
            timeout=WMI.PRODUCER_TIMEOUT_SECONDS,
        ),
        _process_fixture(
            role="independent-verifier",
            argv=verifier_argv,
            run_root=run_root,
            timeout=WMI.VERIFIER_TIMEOUT_SECONDS,
        ),
    ]
    _accepted, candidate_record = WMI._validate_candidate_document(
        candidate,
        raw=candidate_raw,
        filename=candidate_paths[0].name,
        source_state=source_state,
    )
    evidence = {
        "candidate": {**candidate_record, "execution_bound": True},
        "evidence_boundary": {
            "bounded_one_root_cut_liveness_execution_complete": True,
            "construction_direct_vector_execution_bound": True,
            "dependency_necessity_established": False,
            "derived_direct_vector_independently_reproduced": True,
            "global_comparison_complete": False,
            "logical_minimality_established": False,
            "optimized_best_known": False,
            "optimized_vector_independently_audited": False,
            "public_graph_applied": False,
            "publication_applied": False,
            "route_rejections_independently_verified": False,
            "shared_kernel_with_producer": True,
        },
        "producer_byte_identical": True,
        "producer_hash_seeds": [0, 0],
        "producer_run_count": 2,
        "verifier": {
            "artifact_bytes": len(receipt_raw),
            "artifact_sha256": hashlib.sha256(receipt_raw).hexdigest(),
            "hash_seed": 0,
            "path": verifier_path.name,
            "root_sha256": receipt["root_sha256"],
            "status": "passed",
        },
    }
    body = {
        "authority_claims": WMI._authority_claims(),
        "classification": (
            "two-producer-byte-identity-and-independent-cut-liveness-verification"
        ),
        "error": None,
        "evidence": evidence,
        "finished_at": "2026-08-14T00:00:02+00:00",
        "format": WMI.FORMAT_EXECUTION,
        "job_id": "123",
        "processes": processes,
        "requested_resources": WMI.EXPECTED_RESOURCES,
        "runtime": runtime,
        "source": {
            "git_commit": commit,
            "git_receipt": _file_evidence(
                input_root / "cut-liveness-git-verification-receipt.json"
            ),
            "git_tree": tree,
            "infrastructure_manifest": _file_evidence(
                input_root / "wmi-infrastructure-manifest.json"
            ),
            "provenance": {
                "git_commit": commit,
                "git_dirty": False,
                "sha256": provenance_sha,
                "sync_timestamp": sync_timestamp,
            },
            "snapshot_sha256": snapshot,
            "source_state": _file_evidence(
                input_root / "cut-liveness-source-state.json"
            ),
        },
        "started_at": "2026-08-14T00:00:00+00:00",
        "status": "passed",
        "v": 1,
    }
    return WMI._receipt_with_root(body), submission, run_root, source_root, input_root


def test_execution_consumer_recomputes_live_files_and_rejects_rerooted_forgery(
    tmp_path: Path, scientific_documents
) -> None:
    receipt, submission, run_root, source_root, input_root = _execution_fixture(
        tmp_path, scientific_documents
    )
    WMI._validate_execution_receipt(
        receipt,
        job_id="123",
        run_root=run_root,
        source_root=source_root,
        input_root=input_root,
        submission=submission,
    )
    mutations = []
    authority = deepcopy(receipt)
    authority["authority_claims"]["proof_authority"] = True
    mutations.append(authority)
    seed = deepcopy(receipt)
    seed["processes"][1]["hash_seed"] = 1
    mutations.append(seed)
    boundary = deepcopy(receipt)
    boundary["evidence"]["evidence_boundary"][
        "optimized_vector_independently_audited"
    ] = True
    mutations.append(boundary)
    for forged in mutations:
        body = {
            key: value
            for key, value in forged.items()
            if key not in {"root_preimage", "root_sha256"}
        }
        rerooted = WMI._receipt_with_root(body)
        with pytest.raises(WMI.A23DWMIError):
            WMI._validate_execution_receipt(
                rerooted,
                job_id="123",
                run_root=run_root,
                source_root=source_root,
                input_root=input_root,
                submission=submission,
            )


def test_fresh_process_environment_and_nonzero_exit_are_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    observed: dict[str, object] = {}

    class FakePopen:
        pid = 999_999

        def __init__(self, argv, **kwargs):
            observed["argv"] = argv
            observed["env"] = kwargs["env"]
            observed["start_new_session"] = kwargs["start_new_session"]
            stdout_read, stdout_write = os.pipe()
            stderr_read, stderr_write = os.pipe()
            os.close(stdout_write)
            os.close(stderr_write)
            self.stdout = os.fdopen(stdout_read, "rb")
            self.stderr = os.fdopen(stderr_read, "rb")

        def wait(self, timeout=None):
            return 7

    monkeypatch.setattr(WMI.subprocess, "Popen", FakePopen)
    record = WMI._run_process(
        role="producer-0",
        argv=["/reviewed/python", "-B", "-P", "-s", "-S", "producer.py"],
        cwd=tmp_path,
        run_root=tmp_path,
        hash_seed=0,
        timeout_seconds=3,
    )
    assert observed["env"] == WMI._isolated_environment(0)
    assert observed["start_new_session"] is True
    assert "PYTHONPATH" not in observed["env"]
    assert record["returncode"] == 7
    assert WMI._process_outcome(record) == "unknown"


def test_child_output_limit_kills_and_classifies_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(WMI, "MAX_LOG_BYTES", 1024)
    record = WMI._run_process(
        role="bounded-child",
        argv=[
            sys.executable,
            "-S",
            "-c",
            "import os\nwhile True:\n os.write(1, b'x' * 4096)",
        ],
        cwd=tmp_path,
        run_root=tmp_path,
        hash_seed=0,
        timeout_seconds=3,
    )
    assert record["stdout"]["bytes"] <= 1024
    assert record["stderr"]["bytes"] <= 1024
    assert record["output_limit_reached"] is True
    assert WMI._process_outcome(record) == "unknown"


def test_child_timeout_kills_process_group_and_classifies_unknown(
    tmp_path: Path,
) -> None:
    record = WMI._run_process(
        role="timed-child",
        argv=[sys.executable, "-S", "-c", "import time; time.sleep(30)"],
        cwd=tmp_path,
        run_root=tmp_path,
        hash_seed=0,
        timeout_seconds=0.05,
    )
    assert record["timed_out"] is True
    assert record["returncode"] != 0
    assert WMI._process_outcome(record) == "unknown"


def test_create_only_publication_refuses_existing_or_link(tmp_path: Path) -> None:
    output = tmp_path / "receipt.json"
    value = WMI._receipt_with_root(
        {"format": "fixture-receipt", "status": "unknown", "v": 1}
    )
    WMI._publish_create_only(output, value)
    assert output.read_bytes() == _canonical(value)
    with pytest.raises(WMI.A23DWMIError, match="existing|replace"):
        WMI._publish_create_only(output, value)
    link = tmp_path / "linked.json"
    link.symlink_to(output)
    with pytest.raises(WMI.A23DWMIError):
        WMI._publish_create_only(link, value)


def test_create_only_detects_stage_swap_and_preserves_foreign_inode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "receipt.json"
    attacker_bytes = b"not-our-staged-inode\n"
    real_link = WMI.os.link

    def swapped_link(source, target, *, follow_symlinks):
        staged = Path(source)
        staged.unlink()
        staged.write_bytes(attacker_bytes)
        real_link(staged, target, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(WMI.os, "link", swapped_link)
    value = WMI._receipt_with_root(
        {"format": "fixture-receipt", "status": "unknown", "v": 1}
    )
    with pytest.raises(WMI.A23DWMIError, match="identity"):
        WMI._publish_create_only(output, value)
    assert output.read_bytes() == attacker_bytes


def test_runner_read_rejects_same_byte_path_inode_substitution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "input.bin"
    original = b"authenticated-input\n"
    target.write_bytes(original)
    displaced = tmp_path / "displaced.bin"
    real_read = WMI.os.read
    swapped = False

    def swap_after_read(descriptor: int, count: int) -> bytes:
        nonlocal swapped
        chunk = real_read(descriptor, count)
        if chunk and not swapped:
            swapped = True
            target.rename(displaced)
            target.write_bytes(original)
        return chunk

    monkeypatch.setattr(WMI.os, "read", swap_after_read)
    with pytest.raises(WMI.A23DWMIError, match="changed"):
        WMI._read_stable_file(target, limit=1024, allow_empty=False)
    assert target.read_bytes() == original


def test_scheduler_resource_and_missing_evidence_fail_closed() -> None:
    base = {
        "allocated_cpus": 1,
        "derived_exit_code": "0:0",
        "elapsed_raw_seconds": 12,
        "exit_code": "0:0",
        "requested_memory": "4096M",
        "state": "COMPLETED",
    }
    assert WMI._collection_status(
        accounting=base,
        execution={"status": "passed"},
        stdout_exists=True,
        stderr_exists=True,
    ) == (
        "passed",
        "completed-dual-producer-and-independent-cut-liveness-verification",
    )
    for changed in (
        {**base, "state": "TIMEOUT"},
        {**base, "requested_memory": "8192M"},
    ):
        assert WMI._collection_status(
            accounting=changed,
            execution={"status": "passed"},
            stdout_exists=True,
            stderr_exists=True,
        )[0] == "unknown"
    assert WMI._collection_status(
        accounting=base,
        execution=None,
        stdout_exists=True,
        stderr_exists=True,
    )[0] == "unknown"
    assert WMI._collection_status(
        accounting=base,
        execution={"status": "passed"},
        stdout_exists=False,
        stderr_exists=True,
    )[0] == "unknown"


def test_collection_rejects_links_and_malformed_json(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    missing_record, missing_error = WMI._collection_optional_record(
        missing, limit=1024
    )
    assert missing_record == {"exists": False, "path": "missing.json"}
    assert missing_error is None
    target = tmp_path / "target.json"
    target.write_text("{}\n", encoding="utf-8")
    linked = tmp_path / "linked.json"
    linked.symlink_to(target)
    linked_record, linked_error = WMI._collection_optional_record(
        linked, limit=1024
    )
    assert linked_record["read_status"] == "rejected-without-following"
    assert linked_record["exists"] is None
    assert linked_error is not None
    malformed = tmp_path / "malformed.json"
    malformed.write_text('{"duplicate":1,"duplicate":2}\n', encoding="utf-8")
    with pytest.raises(WMI.A23DWMIError):
        WMI._strict_json(malformed, limit=1024)


@pytest.mark.parametrize("relative", ("/etc/passwd", "../escape", "a/../escape"))
def test_source_evidence_paths_cannot_escape_snapshot(
    tmp_path: Path, relative: str
) -> None:
    with pytest.raises(WMI.A23DWMIError, match="unsafe"):
        WMI._source_file(tmp_path, relative)


def test_infrastructure_manifest_binds_every_live_protocol_source() -> None:
    missing = [
        relative
        for relative in WMI.INFRASTRUCTURE_SOURCES
        if not (ROOT / relative).is_file()
    ]
    assert missing == []
    assert len(WMI.INFRASTRUCTURE_SOURCES) == len(set(WMI.INFRASTRUCTURE_SOURCES))
    manifest = WMI._infrastructure_manifest(
        repository_root=ROOT,
        commit="1" * 40,
        tree="2" * 40,
    )
    assert tuple(row["path"] for row in manifest["files"]) == (
        WMI.INFRASTRUCTURE_SOURCES
    )
    WMI._validate_infrastructure_manifest(
        manifest,
        source_root=ROOT,
        commit="1" * 40,
        tree="2" * 40,
    )
    forged = deepcopy(manifest)
    forged["files"][0]["sha256"] = "0" * 64
    with pytest.raises(WMI.A23DWMIError, match="source drifted"):
        WMI._validate_infrastructure_manifest(
            forged,
            source_root=ROOT,
            commit="1" * 40,
            tree="2" * 40,
        )


def test_shell_protocol_is_content_addressed_bounded_and_isolated() -> None:
    submit = SUBMIT.read_text(encoding="utf-8")
    collect = COLLECT.read_text(encoding="utf-8")
    sbatch = SBATCH.read_text(encoding="utf-8")
    runner = RUNNER_PATH.read_text(encoding="utf-8")
    generator = SOURCE_STATE.read_text(encoding="utf-8")
    assert 'stage="$(cd "$stage" && pwd -P)"' in submit
    assert "ssh_command=(ssh -o BatchMode=yes -o ConnectTimeout=15)" in submit
    assert "ssh_command=(ssh -o BatchMode=yes -o ConnectTimeout=15)" in collect
    assert 'ssh_command+=(-J "$ssh_jump")' in submit
    assert 'ssh_command+=(-J "$ssh_jump")' in collect
    assert 'git -C "$repo_root" archive --format=tar HEAD' in submit
    assert "sbatch --hold --parsable" in submit
    assert 'scontrol release "$held_job"' in submit
    assert "set -o noclobber" in submit
    assert "--partition=cpu_idle" in submit
    assert "--mem=4096M" in submit
    assert "--time=00:15:00" in submit
    assert "#SBATCH --cpus-per-task=1" in sbatch
    assert "#SBATCH --job-name=peano-hydra-a23d-cut" in sbatch
    assert "#SBATCH --gres" not in sbatch
    assert "env -i" in sbatch and "env -i" in collect
    assert 'chmod a-w "$collection"' in collect
    assert "-B -P -s -S" in sbatch and "-B -P -s -S" in collect
    assert "sys.flags.no_user_site" in sbatch
    assert "sys.flags.optimize" in sbatch
    assert WMI.CANDIDATE_FILENAME in runner
    assert WMI.SECOND_PRODUCER_FILENAME in runner
    assert "PEANO-HYDRA-A23D-WMI-CUT-LIVENESS" in submit
    assert '"producer_hash_seeds": [0, 0]' in runner
    assert '"derived_direct_vector_independently_reproduced": True' in runner
    assert '"route_rejections_independently_verified": False' in runner
    assert '"optimized_vector_independently_audited": False' in runner
    joined = "\n".join((submit, collect, sbatch, runner, generator))
    for forbidden in (
        "library_pilot_dependency_vector_audit.py",
        "library_pilot_dependency_vector_negative_replay.py",
        "hydra-a23a",
        "PEANO_A23A",
        "range(384)",
    ):
        assert forbidden not in joined


@pytest.mark.parametrize(
    ("script", "argv"),
    (
        (SUBMIT, ["--test-only"]),
        (COLLECT, ["--test-only", "--job-id", "1"]),
    ),
)
def test_hostile_jump_is_rejected_before_network(
    script: Path, argv: list[str]
) -> None:
    environment = {
        **os.environ,
        "WMI_SSH_JUMP": "-oProxyCommand=hostile",
        "WMI_SSH_TARGET": "wmicluster",
    }
    completed = subprocess.run(
        ["bash", str(script), *argv],
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 2
    assert "invalid WMI_SSH_JUMP" in completed.stderr


@pytest.mark.parametrize(
    ("script", "expected_call_count"), ((SUBMIT, 2), (COLLECT, 1))
)
@pytest.mark.parametrize("ssh_jump", (None, "", "jump.example"))
def test_bash32_direct_and_jump_argv_are_exact_without_network(
    tmp_path: Path,
    script: Path,
    expected_call_count: int,
    ssh_jump: str | None,
) -> None:
    fake_bin, ssh_log = _install_fake_ssh(tmp_path)
    environment = {
        **os.environ,
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        "PYTHONDONTWRITEBYTECODE": "1",
        "WMI_SSH_TARGET": "worker.example",
        "WMI_TEST_SSH_LOG": str(ssh_log),
    }
    if ssh_jump is None:
        environment.pop("WMI_SSH_JUMP", None)
    else:
        environment["WMI_SSH_JUMP"] = ssh_jump
    if script == SUBMIT:
        repository = _clean_protocol_repository(tmp_path)
        script_under_test = repository / script.relative_to(ROOT)
        argv = ["--test-only"]
    else:
        repository = ROOT
        script_under_test = script
        argv = ["--test-only", "--job-id", "1"]
    completed = subprocess.run(
        ["/bin/bash", str(script_under_test), *argv],
        cwd=repository,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    calls = _fake_ssh_calls(ssh_log)
    assert len(calls) == expected_call_count
    expected_prefix = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=15"]
    if ssh_jump:
        expected_prefix.extend(("-J", ssh_jump))
    expected_prefix.append("worker.example")
    for call in calls:
        assert call[: len(expected_prefix)] == expected_prefix
        assert len(call) == len(expected_prefix) + 1


@pytest.mark.parametrize("script", (SUBMIT, COLLECT, SBATCH))
def test_shell_sources_parse_without_contacting_wmi(script: Path) -> None:
    subprocess.run(
        ["bash", "-n", str(script)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        timeout=10,
    )
