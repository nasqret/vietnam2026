"""No-network contract tests for the bounded Hydra A2.3a WMI protocol."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from argparse import Namespace
from pathlib import Path
import shutil
import subprocess
import sys
import py_compile

import pytest


ROOT = Path(__file__).resolve().parents[3]
RUNNER_PATH = ROOT / "scripts" / "run_peano_hydra_a23a_wmi.py"
SUBMIT = ROOT / "scripts" / "submit_wmi_hydra_a23a_pilot.sh"
COLLECT = ROOT / "scripts" / "collect_wmi_hydra_a23a_pilot.sh"
SBATCH = ROOT / "slurm" / "peano_wmi_hydra_a23a_pilot.sbatch"


def _load_runner():
    spec = importlib.util.spec_from_file_location("peano_hydra_a23a_wmi", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


WMI = _load_runner()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def test_a23a_infrastructure_manifest_is_exact_rooted_and_live() -> None:
    manifest = WMI._infrastructure_manifest(
        repository_root=ROOT,
        commit="1" * 40,
        tree="2" * 40,
    )
    assert manifest["format"] == WMI.FORMAT_INFRASTRUCTURE
    assert manifest["git_commit"] == "1" * 40
    assert tuple(row["path"] for row in manifest["files"]) == WMI.INFRASTRUCTURE_SOURCES
    assert manifest["root_preimage"]["payload"] == {
        key: value
        for key, value in manifest.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    WMI._validate_infrastructure_manifest(
        manifest,
        source_root=ROOT,
        commit="1" * 40,
        tree="2" * 40,
    )
    mutated = deepcopy(manifest)
    mutated["files"][0]["sha256"] = "0" * 64
    with pytest.raises(WMI.A23AWMIError, match="source drifted"):
        WMI._validate_infrastructure_manifest(
            mutated,
            source_root=ROOT,
            commit="1" * 40,
            tree="2" * 40,
        )


def test_bounded_readers_reject_final_and_ancestor_symlinks(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    payload = real / "payload.json"
    payload.write_bytes(b"{}\n")
    final_link = tmp_path / "payload-link"
    final_link.symlink_to(payload)
    ancestor_link = tmp_path / "linked-parent"
    ancestor_link.symlink_to(real, target_is_directory=True)
    with pytest.raises(WMI.A23AWMIError):
        WMI._read_stable_file(final_link, limit=10)
    with pytest.raises(WMI.A23AWMIError, match="ancestor"):
        WMI._read_stable_file(ancestor_link / "payload.json", limit=10)
    assert WMI._read_stable_file(payload, limit=10) == b"{}\n"
    assert WMI._optional_file_record(
        tmp_path / "missing-run" / "execution-receipt.json", limit=100
    ) == {"exists": False, "path": "execution-receipt.json"}
    with pytest.raises(WMI.A23AWMIError, match="unsafe ancestor"):
        WMI._optional_file_record(
            ancestor_link / "missing-execution-receipt.json", limit=100
        )


def test_fresh_process_environment_is_exact_and_nonzero_is_unknown(
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
    assert record["environment"] == WMI._isolated_environment(0)
    assert "PYTHONPATH" not in observed["env"]
    assert record["returncode"] == 7
    assert WMI._process_outcome(record) == "unknown"


def test_child_output_is_hard_bounded_during_execution(
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
    assert record["returncode"] != 0
    assert WMI._process_outcome(record) == "unknown"


def test_fixed_pycache_prefix_ignores_adjacent_unchecked_pyc(tmp_path: Path) -> None:
    module = tmp_path / "adjacent_cache_probe.py"
    module.write_text("VALUE = 'reviewed-source'\n", encoding="utf-8")
    malicious = tmp_path / "malicious_cache_probe.py"
    malicious.write_text("VALUE = 'unreviewed-pyc'\n", encoding="utf-8")
    cache = tmp_path / "__pycache__" / (
        f"adjacent_cache_probe.{sys.implementation.cache_tag}.pyc"
    )
    cache.parent.mkdir()
    py_compile.compile(
        str(malicious),
        cfile=str(cache),
        doraise=True,
        invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH,
    )
    malicious.unlink()
    probe = (
        "import sys; "
        f"sys.path.append({str(tmp_path)!r}); "
        "import adjacent_cache_probe; print(adjacent_cache_probe.VALUE)"
    )
    adjacent_env = WMI._isolated_environment(0)
    adjacent_env.pop("PYTHONPYCACHEPREFIX")
    unprotected = subprocess.run(
        [sys.executable, "-B", "-s", "-S", "-c", probe],
        env=adjacent_env,
        check=True,
        capture_output=True,
        text=True,
    )
    assert unprotected.stdout.strip() == "unreviewed-pyc"
    protected = subprocess.run(
        [sys.executable, "-B", "-s", "-S", "-c", probe],
        env=WMI._isolated_environment(0),
        check=True,
        capture_output=True,
        text=True,
    )
    assert protected.stdout.strip() == "reviewed-source"
    assert WMI._isolated_environment(0)["PYTHONPYCACHEPREFIX"] == (
        "/proc/peano-hydra-a23a-disabled-pycache"
    )


def test_worker_deeply_consumes_external_source_and_git_receipts(
    tmp_path: Path,
) -> None:
    generator_path = ROOT / WMI.SOURCE_STATE_GENERATOR
    spec = importlib.util.spec_from_file_location("a23a_source_state_for_wmi", generator_path)
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = generator
    spec.loader.exec_module(generator)

    repo = tmp_path / "clean-repo"
    repo.mkdir()
    paths = [
        *(Path(path) for path, _digest in WMI.FROZEN_PRODUCER_SOURCES),
        Path(WMI.SOURCE_STATE_GENERATOR),
    ]
    for relative in paths:
        destination = repo / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    for argv in (
        ["git", "init", "-q"],
        ["git", "config", "user.email", "wmi-test@example.invalid"],
        ["git", "config", "user.name", "WMI Test"],
        ["git", "add", "."],
        ["git", "commit", "-q", "-m", "fixture"],
    ):
        subprocess.run(argv, cwd=repo, check=True, capture_output=True)
    state, receipt, _envelope = generator.build_producer_evidence(repo)
    state_raw = generator.canonical_document_bytes(state)
    WMI._validate_source_state_document(
        state,
        raw=state_raw,
        source_root=repo,
        commit=state["commit_sha1"],
        tree=state["tree_sha1"],
    )
    WMI._validate_git_receipt_document(
        receipt,
        source_root=repo,
        source_state=state,
        source_state_raw=state_raw,
        commit=state["commit_sha1"],
        tree=state["tree_sha1"],
    )
    rerooted = deepcopy(receipt)
    rerooted["commands"][0]["stdout_sha256"] = "0" * 64
    body = {
        key: value
        for key, value in rerooted.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    preimage = {"format": WMI.FORMAT_GIT_RECEIPT_ROOT, "payload": body, "v": 1}
    rerooted["root_preimage"] = preimage
    rerooted["root_sha256"] = WMI._compact_sha256(preimage)
    with pytest.raises(WMI.A23AWMIError, match="version command"):
        WMI._validate_git_receipt_document(
            rerooted,
            source_root=repo,
            source_state=state,
            source_state_raw=state_raw,
            commit=state["commit_sha1"],
            tree=state["tree_sha1"],
        )


def test_submission_and_deposit_records_are_exactly_cross_bound(tmp_path: Path) -> None:
    digests = [character * 64 for character in "123456"]
    row = "\t".join(
        (
            "2026-08-10T10:00:00+00:00",
            "123",
            digests[0],
            "a" * 40,
            "b" * 40,
            digests[1],
            digests[2],
            digests[3],
            digests[4],
            "2026-08-10T09:59:00Z",
            "cpu_idle",
            "1",
            "1",
            "4096",
            "00:15:00",
            digests[5],
        )
    ) + "\n"
    submission_path = tmp_path / "submission.tsv"
    submission_path.write_text(row, encoding="ascii")
    submission = WMI._parse_submission_record(submission_path, "123")
    deposit_path = tmp_path / "deposit.tsv"
    deposit_path.write_text(
        "\t".join(
            (
                digests[0],
                "123456",
                "a" * 40,
                "b" * 40,
                digests[1],
                digests[2],
                digests[3],
                digests[4],
                "2026-08-10T09:59:00Z",
            )
        )
        + "\n",
        encoding="ascii",
    )
    deposit = WMI._parse_deposit_record(deposit_path, submission=submission)
    assert deposit["snapshot_sha256"] == submission["snapshot_sha256"]
    mutated = deposit_path.read_text(encoding="ascii").replace(digests[3], "f" * 64)
    deposit_path.write_text(mutated, encoding="ascii")
    with pytest.raises(WMI.A23AWMIError, match="differs"):
        WMI._parse_deposit_record(deposit_path, submission=submission)


def _unknown_execution_fixture(tmp_path: Path):
    input_root = tmp_path / "inputs"
    source_root = tmp_path / "source"
    run_root = tmp_path / "runs" / "123"
    input_root.mkdir()
    source_root.mkdir()
    run_root.mkdir(parents=True)
    names = (
        "producer-source-state.json",
        "producer-git-verification-receipt.json",
        "wmi-infrastructure-manifest.json",
    )
    records = {}
    for index, name in enumerate(names):
        path = input_root / name
        raw = _canonical({"index": index})
        path.write_bytes(raw)
        records[name] = {
            "bytes": len(raw),
            "path": name,
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    submission = {
        "git_commit": "a" * 40,
        "git_tree": "b" * 40,
        "snapshot_sha256": "1" * 64,
        "source_state_sha256": records[names[0]]["sha256"],
        "git_receipt_sha256": records[names[1]]["sha256"],
        "infrastructure_sha256": records[names[2]]["sha256"],
        "provenance_sha256": "2" * 64,
        "sync_timestamp": "2026-08-10T09:59:00Z",
    }
    payload = {
        "authority_claims": WMI._authority_claims(),
        "classification": "infrastructure-validation-failed",
        "error": {"message": "controlled", "type": "ValueError"},
        "evidence": {},
        "finished_at": "2026-08-10T10:00:01+00:00",
        "format": WMI.FORMAT_EXECUTION,
        "job_id": "123",
        "processes": [],
        "requested_resources": WMI.EXPECTED_RESOURCES,
        "runtime": {
            "dont_write_bytecode": True,
            "executable": WMI.PINNED_WMI_PYTHON,
            "implementation": "CPython",
            "machine": "x86_64",
            "no_site": True,
            "pycache_prefix": WMI.DISABLED_PYCACHE_PREFIX,
            "python_version": "3.12.12",
            "safe_path": True,
        },
        "source": {
            "git_commit": submission["git_commit"],
            "git_receipt": records[names[1]],
            "git_tree": submission["git_tree"],
            "infrastructure_manifest": records[names[2]],
            "provenance": {
                "git_commit": submission["git_commit"],
                "git_dirty": False,
                "sha256": submission["provenance_sha256"],
                "sync_timestamp": "2026-08-10T09:59:00Z",
            },
            "snapshot_sha256": submission["snapshot_sha256"],
            "source_state": records[names[0]],
        },
        "started_at": "2026-08-10T10:00:00+00:00",
        "status": "unknown",
        "v": 1,
    }
    return (
        WMI._receipt_with_root(payload),
        source_root,
        input_root,
        run_root,
        submission,
    )


def test_execution_receipt_requires_exact_root_authority_and_pass_evidence(
    tmp_path: Path,
) -> None:
    receipt, source_root, input_root, run_root, submission = _unknown_execution_fixture(
        tmp_path
    )
    WMI._validate_execution_receipt(
        receipt,
        job_id="123",
        run_root=run_root,
        source_root=source_root,
        input_root=input_root,
        submission=submission,
    )
    rerooted = deepcopy(receipt)
    rerooted["status"] = "passed"
    with pytest.raises(WMI.A23AWMIError, match="root"):
        WMI._validate_execution_receipt(
            rerooted,
            job_id="123",
            run_root=run_root,
            source_root=source_root,
            input_root=input_root,
            submission=submission,
        )


def test_execution_failed_vectors_are_classification_specific(tmp_path: Path) -> None:
    base, source_root, input_root, run_root, submission = _unknown_execution_fixture(
        tmp_path
    )
    source_state_path = input_root / "producer-source-state.json"
    candidate_paths = (
        run_root / "candidate-hashseed-0.json",
        run_root / "candidate-hashseed-1.json",
    )
    candidate_paths[0].write_bytes(_canonical({"candidate": 0}))
    candidate_paths[1].write_bytes(_canonical({"candidate": 1}))
    processes = []
    for seed in (0, 1):
        role = f"producer-{seed}"
        stdout = run_root / f"{role}.stdout.log"
        stderr = run_root / f"{role}.stderr.log"
        stdout.write_bytes(b"")
        stderr.write_bytes(b"")
        processes.append(
            {
                "argv": [
                    WMI.PINNED_WMI_PYTHON,
                    "-B",
                    "-P",
                    "-s",
                    "-S",
                    "scripts/build_peano_hydra_library_optimizer_comparison_pilot.py",
                    "--producer-source-state",
                    str(source_state_path),
                    "--output",
                    str(candidate_paths[seed]),
                ],
                "duration_seconds_millis": 1,
                "environment": WMI._isolated_environment(seed),
                "finished_at": "2026-08-10T10:00:01+00:00",
                "hash_seed": seed,
                "output_limit_reached": False,
                "returncode": 0,
                "role": role,
                "started_at": "2026-08-10T10:00:00+00:00",
                "stderr": {"bytes": 0, "path": stderr.name, "sha256": _sha(stderr)},
                "stdout": {"bytes": 0, "path": stdout.name, "sha256": _sha(stdout)},
                "timed_out": False,
                "timeout_seconds": WMI.PRODUCER_TIMEOUT_SECONDS,
            }
        )
    body = {
        key: value
        for key, value in base.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    body.update(
        {
            "classification": "producer-byte-divergence",
            "error": None,
            "processes": processes,
            "status": "failed",
        }
    )
    divergence = WMI._receipt_with_root(body)
    WMI._validate_execution_receipt(
        divergence,
        job_id="123",
        run_root=run_root,
        source_root=source_root,
        input_root=input_root,
        submission=submission,
    )
    candidate_paths[1].write_bytes(candidate_paths[0].read_bytes())
    with pytest.raises(WMI.A23AWMIError, match="identical"):
        WMI._validate_execution_receipt(
            divergence,
            job_id="123",
            run_root=run_root,
            source_root=source_root,
            input_root=input_root,
            submission=submission,
        )
    body["classification"] = "complete-candidate-contract-mismatch"
    mismatch = WMI._receipt_with_root(body)
    WMI._validate_execution_receipt(
        mismatch,
        job_id="123",
        run_root=run_root,
        source_root=source_root,
        input_root=input_root,
        submission=submission,
    )
    forged = deepcopy(base)
    forged["status"] = "passed"
    forged["classification"] = (
        "two-producer-byte-identity-and-independent-verification"
    )
    forged["error"] = None
    body = {
        key: value
        for key, value in forged.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    forged = WMI._receipt_with_root(body)
    with pytest.raises(WMI.A23AWMIError, match="process vector"):
        WMI._validate_execution_receipt(
            forged,
            job_id="123",
            run_root=run_root,
            source_root=source_root,
            input_root=input_root,
            submission=submission,
        )


def test_verifier_consumer_rejects_status_only_and_wrong_format() -> None:
    with pytest.raises(WMI.A23AWMIError, match="wrong fields"):
        WMI._validate_verifier_receipt(
            {"status": "passed"},
            candidate={},
            candidate_raw=b"{}\n",
            source_state={},
            source_state_raw=b"{}\n",
            source_root=ROOT,
        )
    assert WMI.FORMAT_VERIFIER == (
        "peano-hydra-library-optimizer-comparison-pilot-verification"
    )
    assert _sha(ROOT / WMI.VERIFIER_MODULE_PATH) == WMI.VERIFIER_MODULE_SHA256
    assert _sha(
        ROOT / "scripts/verify_peano_hydra_library_optimizer_comparison_pilot.py"
    ) == WMI.VERIFIER_CLI_SHA256


def test_scheduler_classification_is_exact_and_resource_failures_are_unknown() -> None:
    accounting = {
        "state": "COMPLETED",
        "exit_code": "0:0",
        "derived_exit_code": "0:0",
        "allocated_cpus": 1,
        "requested_memory": "4Gn",
        "elapsed_raw_seconds": 900,
    }
    assert WMI._collection_status(
        accounting=accounting,
        execution={"status": "passed"},
        stdout_exists=True,
        stderr_exists=True,
    ) == ("passed", "completed-and-independently-verified")
    for mutation in (
        {"state": "TIMEOUT"},
        {"allocated_cpus": 2},
        {"requested_memory": "8Gn"},
        {"elapsed_raw_seconds": 901},
    ):
        changed = {**accounting, **mutation}
        assert WMI._collection_status(
            accounting=changed,
            execution={"status": "passed"},
            stdout_exists=True,
            stderr_exists=True,
        )[0] == "unknown"
    assert WMI._collection_status(
        accounting=accounting,
        execution=None,
        stdout_exists=True,
        stderr_exists=True,
    )[0] == "unknown"


def test_collector_roots_rejected_execution_symlink_as_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    remote_root = tmp_path / "remote"
    monkeypatch.setattr(WMI, "WMI_REMOTE_ROOT", remote_root)
    snapshot = "1" * 64
    snapshot_root = remote_root / snapshot
    source_root = snapshot_root / "source"
    input_root = snapshot_root / "inputs"
    run_root = snapshot_root / "runs" / "123"
    logs_root = snapshot_root / "logs"
    collections_root = snapshot_root / "collections"
    for directory in (
        source_root / "slurm",
        input_root,
        run_root,
        logs_root,
        collections_root,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    sbatch = source_root / "slurm" / "peano_wmi_hydra_a23a_pilot.sbatch"
    sbatch.write_bytes(b"#!/bin/sh\n")
    digests = {
        "source": "2" * 64,
        "git": "3" * 64,
        "infrastructure": "4" * 64,
        "provenance": "5" * 64,
        "sbatch": _sha(sbatch),
    }
    submission = collections_root / ".submission-123.fixture.tsv"
    submission.write_text(
        "\t".join(
            (
                "2026-08-10T10:00:00+00:00",
                "123",
                snapshot,
                "a" * 40,
                "b" * 40,
                digests["source"],
                digests["git"],
                digests["infrastructure"],
                digests["provenance"],
                "2026-08-10T09:59:00Z",
                "cpu_idle",
                "1",
                "1",
                "4096",
                "00:15:00",
                digests["sbatch"],
            )
        )
        + "\n",
        encoding="ascii",
    )
    deposit = snapshot_root / "deposit.tsv"
    deposit.write_text(
        "\t".join(
            (
                snapshot,
                "123456",
                "a" * 40,
                "b" * 40,
                digests["source"],
                digests["git"],
                digests["infrastructure"],
                digests["provenance"],
                "2026-08-10T09:59:00Z",
            )
        )
        + "\n",
        encoding="ascii",
    )
    sacct = collections_root / ".sacct-123.fixture.txt"
    sacct.write_text(
        "123|COMPLETED|0:0|0:0|1|1K|4Gn|1|node1\n", encoding="ascii"
    )
    stdout = logs_root / "peano-hydra-a23a-123.out"
    stderr = logs_root / "peano-hydra-a23a-123.err"
    stdout.write_bytes(b"")
    stderr.write_bytes(b"")
    rejected_target = run_root / "untrusted.json"
    rejected_target.write_bytes(b"{}\n")
    execution = run_root / "execution-receipt.json"
    execution.symlink_to(rejected_target)
    output = collections_root / "job-123.json"
    result = WMI._collect(
        Namespace(
            job_id="123",
            submission_record=submission,
            deposit_record=deposit,
            sbatch_file=sbatch,
            source_root=source_root,
            input_root=input_root,
            run_root=run_root,
            sacct_record=sacct,
            execution_receipt=execution,
            stdout=stdout,
            stderr=stderr,
            output=output,
        )
    )
    assert result == 3
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["status"] == "unknown"
    assert receipt["execution_validation"]["status"] == "rejected-as-unknown"
    assert receipt["execution_receipt"]["read_status"] == (
        "rejected-without-following"
    )
    assert receipt["root_sha256"] == WMI._compact_sha256(receipt["root_preimage"])

    oversized = run_root / "oversized.json"
    oversized.write_bytes(b"x" * 11)
    rejected, error = WMI._collection_optional_record(oversized, limit=10)
    assert rejected["read_status"] == "rejected-without-following"
    assert error is not None


def test_wmi_shell_protocol_is_guarded_held_isolated_and_never_run_in_tests() -> None:
    runner = RUNNER_PATH.read_text(encoding="utf-8")
    submit = SUBMIT.read_text(encoding="utf-8")
    collect = COLLECT.read_text(encoding="utf-8")
    sbatch = SBATCH.read_text(encoding="utf-8")
    assert "mode=test-only" in submit
    assert submit.index('stage="$(mktemp -d)"') < submit.index(
        'stage="$(cd "$stage" && pwd -P)"'
    ) < submit.index('source_state="$stage/producer-source-state.json"')
    assert "python_path = str(Path(sys.executable))" in runner
    assert "Path(sys.executable).resolve()" not in runner
    assert "PEANO-HYDRA-A23A-WMI-PILOT" in submit
    assert "requires a clean committed Git worktree" in submit
    assert "producer-source-state.json" in submit
    assert "wmi-infrastructure-manifest.json" in submit
    assert "sbatch --hold --parsable" in submit
    assert submit.index("sbatch --hold --parsable") < submit.index(
        'sync -f "$manifest"'
    ) < submit.index('scontrol release "$held_job"')
    assert 'scancel "$held_job"' in submit
    assert "--test-only" in submit
    assert "submissions.tsv" in collect
    assert "deposit.tsv" in collect
    assert "--submission-record" in collect
    assert "--sbatch-file" in collect
    assert "sacct" in collect
    assert "sha256sum" in collect
    assert "#SBATCH --partition=cpu_idle" in sbatch
    assert "#SBATCH --ntasks=1" in sbatch
    assert "#SBATCH --cpus-per-task=1" in sbatch
    assert "#SBATCH --mem=4096M" in sbatch
    assert "#SBATCH --time=00:15:00" in sbatch
    assert '"$python_path" -B -P -s -S' in sbatch
    assert 'chmod -R a-w "$run_root"' in sbatch
    assert "PYTHONPYCACHEPREFIX=/proc/peano-hydra-a23a-disabled-pycache" in sbatch
    assert "PYTHONPYCACHEPREFIX=/proc/peano-hydra-a23a-disabled-pycache" in collect
    assert "-B -P -s -S" in collect


def test_shell_sources_parse_without_contacting_wmi() -> None:
    for path in (SUBMIT, COLLECT, SBATCH):
        subprocess.run(
            ["bash", "-n", str(path)],
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
