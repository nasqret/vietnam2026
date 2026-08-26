"""Adversarial and tiny real-process tests for Bertrand Alpha-v3 closure."""

from __future__ import annotations

from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
if str(PEANO_PYTHON) not in sys.path:
    sys.path.insert(0, str(PEANO_PYTHON))


def _load_runner():
    path = REPOSITORY_ROOT / "scripts/run_bertrand_alpha_v3_cold_closure.py"
    spec = importlib.util.spec_from_file_location(
        "run_bertrand_alpha_v3_cold_closure_under_test", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RUNNER = _load_runner()
SBATCH = REPOSITORY_ROOT / "slurm/peano_wmi_bertrand_alpha_v3_closure.sbatch"
SCHEMA = (
    REPOSITORY_ROOT
    / "schemas/peano-bertrand-alpha-v3-cold-closure-v2.schema.json"
)
TINY_TARGET = "prime_interval_exclusion_refutes_witness"
EXPECTED_TINY_RECEIPT = {
    TINY_TARGET: {
        "cuts": 0,
        "dependency_closure_count": 1,
        "dependency_closure_sha256": (
            "9ed62c1c30fc8cdc2e0eca90dfd2e68f83ee2921c18a7af317d3c681fdb088d9"
        ),
        "direct_dependencies": [],
        "dne_objects": 0,
        "proof_dag_sha256": (
            "29818c11d1a2f03af97f15969578c402d7addd470d7ab107c7def6eae1a2911f"
        ),
        "proof_depth": 19,
        "proof_edges": 32,
        "proof_nodes": 33,
        "proof_objects": 33,
        "reused_objects": 0,
        "script_commands": 13,
        "script_sha256": (
            "4df92d763e803078c5dbbbd864536198d23df44aee233e58d9f0f63235fa2eaa"
        ),
        "source_path": (
            "peano-lab/py/peano_lab/library/bertrand_prime_interval_candidate.py"
        ),
        "source_sha256": (
            "6b9263ffd4aa39130ff4cee9ae3f3449e4aadbc544363900f7f2289ffc701a97"
        ),
        "statement_characters": 1_344,
        "statement_sha256": (
            "8e28fa9dd9b0b2b8a1d4c2284e1613368cd4485147890b1bb5bdeeca30b26905"
        ),
    }
}


CONTROLLED_ENVIRONMENT = (
    "PEANO_BERTRAND_LOCAL_COMMIT",
    "PEANO_BERTRAND_LOCAL_DIRTY",
    "PEANO_BERTRAND_PAYLOAD_SHA256",
    "PEANO_BERTRAND_REQUESTED_PARTITION",
    "PEANO_BERTRAND_REQUESTED_NODES",
    "PEANO_BERTRAND_REQUESTED_NTASKS",
    "PEANO_BERTRAND_REQUESTED_CPUS_PER_TASK",
    "PEANO_BERTRAND_REQUESTED_MEMORY_MIB",
    "PEANO_BERTRAND_REQUESTED_TIME_LIMIT",
    "PEANO_BERTRAND_REQUESTED_TIME_LIMIT_SECONDS",
    "PEANO_BERTRAND_ALLOW_LOCAL_DIAGNOSTIC",
    "PEANO_CLUSTER_BACKEND",
    "SLURM_JOB_ID",
    "SLURM_JOB_NAME",
    "SLURM_JOB_PARTITION",
    "SLURM_CLUSTER_NAME",
    "SLURM_JOB_NODELIST",
    "SLURM_SUBMIT_DIR",
    "SLURM_JOB_NUM_NODES",
    "SLURM_NTASKS",
    "SLURM_CPUS_PER_TASK",
    "SLURM_MEM_PER_NODE",
)


def _clear_controlled_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in CONTROLLED_ENVIRONMENT:
        monkeypatch.delenv(name, raising=False)


def _set_local_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_controlled_environment(monkeypatch)
    monkeypatch.setenv("PEANO_BERTRAND_ALLOW_LOCAL_DIAGNOSTIC", "true")
    monkeypatch.setenv("PYTHONHASHSEED", "20260809")


def _set_wmi_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_controlled_environment(monkeypatch)
    values = {
        "PEANO_BERTRAND_LOCAL_COMMIT": "1" * 40,
        "PEANO_BERTRAND_LOCAL_DIRTY": "false",
        "PEANO_BERTRAND_PAYLOAD_SHA256": "2" * 64,
        "PEANO_BERTRAND_REQUESTED_PARTITION": "cpu_idle",
        "PEANO_BERTRAND_REQUESTED_NODES": "1",
        "PEANO_BERTRAND_REQUESTED_NTASKS": "1",
        "PEANO_BERTRAND_REQUESTED_CPUS_PER_TASK": "1",
        "PEANO_BERTRAND_REQUESTED_MEMORY_MIB": "32768",
        "PEANO_BERTRAND_REQUESTED_TIME_LIMIT": "06:00:00",
        "PEANO_BERTRAND_REQUESTED_TIME_LIMIT_SECONDS": "21600",
        "PEANO_CLUSTER_BACKEND": "wmi",
        "SLURM_JOB_ID": "424242",
        "SLURM_JOB_NAME": "peano-bertrand-v3",
        "SLURM_JOB_PARTITION": "cpu_idle",
        "SLURM_CLUSTER_NAME": "wmi",
        "SLURM_JOB_NODELIST": "cpu001",
        "SLURM_SUBMIT_DIR": str(REPOSITORY_ROOT),
        "SLURM_JOB_NUM_NODES": "1",
        "SLURM_NTASKS": "1",
        "SLURM_CPUS_PER_TASK": "1",
        "SLURM_MEM_PER_NODE": "32768",
        "PYTHONHASHSEED": "20260809",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)


def _local_tiny_arguments(report: Path) -> list[str]:
    return [
        "--execution-mode",
        "local-diagnostic",
        "--theorem",
        TINY_TARGET,
        "--report",
        str(report),
    ]


def test_parent_artifacts_target_graph_and_sources_are_exact() -> None:
    assert RUNNER.FORMAT == "peano-bertrand-alpha-v3-cold-closure-v2"
    assert RUNNER.EXPECTED_PASSES == 2
    assert len(RUNNER.TARGET_NAMES) == 21
    parent = RUNNER._parent_receipt()
    assert parent["alpha_v3_runtime"] == {
        "checked_use_count": 570,
        "edge_count": 2_730,
        "enrollment_sha256": (
            "4507736cde37301ecf3369540d6cc686de860b07b101f2afb60f850f86aeebd4"
        ),
        "identity_sha256": (
            "e20eefac839fb2bcd3e696989c091a5f6837de04824f94e1073723851a471a2f"
        ),
        "layer_count": 45,
        "theorem_count": 923,
    }
    assert parent["alpha_v3_artifacts"] == RUNNER.EXPECTED_ALPHA_V3_ARTIFACTS

    local = RUNNER._local_specs()
    public = RUNNER._public_specs()
    assert tuple(local) == RUNNER.TARGET_NAMES
    assert not (set(local) & set(public))
    assert sum(len(item.dependencies) for item in local.values()) == 56
    assert RUNNER._target_graph_sha256(tuple(local.values())) == (
        "9b14ced99d5a138f740ec7c99aca044a61b706e8161fa162c863f41e75f58bca"
    )
    entries = RUNNER.v3.ALPHA_ENTRIES[RUNNER.BERTRAND_START_INDEX :]
    assert RUNNER._target_surface_sha256(entries) == (
        "16f595012facc50bab5a4790d76fc5b4c00583159b70b9178618ab24c3d9b323"
    )
    assert {
        entry.source_module for entry in entries
    } == set(RUNNER.EXPECTED_SOURCE_SHA256)
    for path, expected in RUNNER.EXPECTED_SOURCE_SHA256.items():
        assert sha256((REPOSITORY_ROOT / path).read_bytes()).hexdigest() == expected
    closure = RUNNER._dependency_closure(RUNNER.TARGET_NAMES, local, public)
    assert len(closure) == 159
    assert sha256("\n".join(closure).encode()).hexdigest() == (
        "7db223693e54554c71155fbb0999696242287a5e8e797af84d7bcc2fb1de46a3"
    )


def test_immutable_report_schema_is_bound_and_well_formed() -> None:
    assert RUNNER._report_schema_receipt() == {
        "path": RUNNER.REPORT_SCHEMA_PATH,
        "sha256": (
            "49385ea44ce059b6d3543b3d68f5ae67a3a0155fb8d1f219fed118eba783fa69"
        ),
    }
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert schema["$id"] == schema["title"] == RUNNER.FORMAT
    assert schema["additionalProperties"] is False
    assert schema["$defs"]["result"]["additionalProperties"] is False
    assert schema["$defs"]["declaredUpload"]["properties"]["local_dirty"] == {
        "const": False
    }
    assert schema["$defs"]["localExecution"]["properties"][
        "admission_eligible"
    ] == {"const": False}
    assert schema["$defs"]["wmiExecution"]["properties"][
        "admission_eligible"
    ] == {"const": True}
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.Draft202012Validator.check_schema(schema)


def test_cli_execution_authority_and_declared_provenance_are_fail_closed(
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert RUNNER.main(["--list-theorems"]) == 0
    assert tuple(capsys.readouterr().out.splitlines()) == RUNNER.TARGET_NAMES
    requested = (RUNNER.TARGET_NAMES[-1], RUNNER.TARGET_NAMES[0])
    assert RUNNER._selected(requested) == (
        RUNNER.TARGET_NAMES[0],
        RUNNER.TARGET_NAMES[-1],
    )
    with pytest.raises(RUNNER.ClosureError, match="duplicate"):
        RUNNER._selected((TINY_TARGET, TINY_TARGET))
    with pytest.raises(SystemExit):
        RUNNER._arguments(["--theorem", "not_a_bertrand_theorem"])
    with pytest.raises(RUNNER.ClosureError, match="execution-mode"):
        RUNNER.main(["--report", "unused.json"])

    _set_local_environment(monkeypatch)
    with pytest.raises(RUNNER.ClosureError, match="exactly two"):
        RUNNER.main(
            [
                "--execution-mode",
                "local-diagnostic",
                "--passes",
                "1",
                "--report",
                "unused.json",
            ]
        )
    local_execution = RUNNER._execution_receipt(RUNNER.LOCAL_DIAGNOSTIC_MODE)
    assert local_execution["mode"] == "local-diagnostic"
    assert local_execution["admission_eligible"] is False
    assert local_execution["synthetic"] is False
    assert local_execution["scheduler"] == {"kind": "none"}
    assert RUNNER._requested_resources(RUNNER.LOCAL_DIAGNOSTIC_MODE) is None
    assert RUNNER._source_provenance(RUNNER.LOCAL_DIAGNOSTIC_MODE)[
        "declared_upload"
    ] is None

    monkeypatch.delenv("PEANO_BERTRAND_ALLOW_LOCAL_DIAGNOSTIC")
    with pytest.raises(RUNNER.ClosureError, match="ALLOW_LOCAL_DIAGNOSTIC"):
        RUNNER._execution_receipt(RUNNER.LOCAL_DIAGNOSTIC_MODE)
    monkeypatch.setenv("PEANO_BERTRAND_ALLOW_LOCAL_DIAGNOSTIC", "true")
    monkeypatch.setenv("SLURM_JOB_ID", "7")
    with pytest.raises(RUNNER.ClosureError, match="scheduler identity"):
        RUNNER._execution_receipt(RUNNER.LOCAL_DIAGNOSTIC_MODE)

    _set_wmi_environment(monkeypatch)
    execution = RUNNER._execution_receipt(RUNNER.WMI_SLURM_MODE)
    assert execution["admission_eligible"] is True
    assert execution["scheduler"] == {
        "cluster": "wmi",
        "job_id": "424242",
        "job_name": "peano-bertrand-v3",
        "kind": "slurm",
        "submit_dir_matches_repository": True,
    }
    assert execution["observed_allocation"] == {
        "cpus_per_task": 1,
        "memory_mib": 32768,
        "node_list": "cpu001",
        "nodes": 1,
        "ntasks": 1,
        "partition": "cpu_idle",
    }
    monkeypatch.setattr(
        RUNNER,
        "_observed_repository",
        lambda: {"availability": "payload_without_git"},
    )
    assert RUNNER._source_provenance(RUNNER.WMI_SLURM_MODE) == {
        "declared_upload": {
            "local_commit": "1" * 40,
            "local_dirty": False,
            "payload_sha256": "2" * 64,
        },
        "observed_repository": {"availability": "payload_without_git"},
    }
    monkeypatch.setenv("PEANO_BERTRAND_LOCAL_DIRTY", "true")
    with pytest.raises(RUNNER.ClosureError, match="false for WMI"):
        RUNNER._source_provenance(RUNNER.WMI_SLURM_MODE)
    monkeypatch.setenv("PEANO_BERTRAND_LOCAL_DIRTY", "false")
    monkeypatch.setenv("PEANO_BERTRAND_LOCAL_COMMIT", "not-a-commit")
    with pytest.raises(RUNNER.ClosureError, match="LOCAL_COMMIT"):
        RUNNER._source_provenance(RUNNER.WMI_SLURM_MODE)


def test_resource_profile_and_wmi_entry_are_frozen(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_wmi_environment(monkeypatch)
    assert RUNNER._requested_resources(RUNNER.WMI_SLURM_MODE) == (
        RUNNER.EXPECTED_RESOURCES
    )
    monkeypatch.setenv("PEANO_BERTRAND_REQUESTED_MEMORY_MIB", "65536")
    with pytest.raises(RUNNER.ClosureError, match="resource profile mismatch"):
        RUNNER._requested_resources(RUNNER.WMI_SLURM_MODE)

    text = SBATCH.read_text(encoding="utf-8")
    lines = set(text.splitlines())
    assert {
        "#SBATCH --partition=cpu_idle",
        "#SBATCH --nodes=1",
        "#SBATCH --ntasks=1",
        "#SBATCH --cpus-per-task=1",
        "#SBATCH --mem=32768M",
        "#SBATCH --time=06:00:00",
    } <= lines
    assert "arguments=(--passes 2 --execution-mode wmi-slurm)" in text
    assert "export PYTHONHASHSEED=20260809" in text
    assert "export PEANO_CLUSTER_BACKEND=wmi" in text
    assert "scripts/run_bertrand_alpha_v3_cold_closure.py" in text
    assert "PEANO_BERTRAND_PAYLOAD_SHA256" in text
    assert "PEANO_BERTRAND_LOCAL_COMMIT" in text
    assert "PEANO_BERTRAND_LOCAL_DIRTY" in text
    assert "SLURM_MEM_PER_NODE" in text
    assert "SLURM_JOB_ID" in text
    assert "SLURM_CLUSTER_NAME" in text
    assert "SLURM_JOB_NODELIST" in text
    assert "#SBATCH --output=peano-bertrand-v3-%j.out" in text
    assert "#SBATCH --error=peano-bertrand-v3-%j.err" in text
    assert "#SBATCH --output=logs/" not in text
    assert "#SBATCH --error=logs/" not in text
    assert "closure-v2.schema.json" in text
    assert all(name in text for name in RUNNER.TARGET_NAMES)
    assert "\nsbatch " not in text
    assert "\nsrun " not in text
    subprocess.run(["bash", "-n", str(SBATCH)], check=True)


@pytest.mark.parametrize(
    "name",
    [
        "PEANO_CLUSTER_BACKEND",
        "SLURM_JOB_ID",
        "SLURM_JOB_NAME",
        "SLURM_JOB_PARTITION",
        "SLURM_CLUSTER_NAME",
        "SLURM_JOB_NODELIST",
        "SLURM_SUBMIT_DIR",
        "SLURM_JOB_NUM_NODES",
        "SLURM_NTASKS",
        "SLURM_CPUS_PER_TASK",
        "SLURM_MEM_PER_NODE",
    ],
)
def test_wmi_scheduler_identity_requires_every_observed_field(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    _set_wmi_environment(monkeypatch)
    monkeypatch.delenv(name)
    with pytest.raises(RUNNER.ClosureError):
        RUNNER._execution_receipt(RUNNER.WMI_SLURM_MODE)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("SLURM_JOB_ID", "0"),
        ("SLURM_JOB_NAME", "wrong-job"),
        ("SLURM_JOB_PARTITION", "gpu"),
        ("SLURM_JOB_NUM_NODES", "2"),
        ("SLURM_NTASKS", "2"),
        ("SLURM_CPUS_PER_TASK", "2"),
        ("SLURM_MEM_PER_NODE", "65536"),
    ],
)
def test_wmi_scheduler_identity_rejects_mutated_allocation(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    value: str,
) -> None:
    _set_wmi_environment(monkeypatch)
    monkeypatch.setenv(name, value)
    with pytest.raises(RUNNER.ClosureError):
        RUNNER._execution_receipt(RUNNER.WMI_SLURM_MODE)


def test_local_diagnostic_rejects_claimed_slurm_resources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_local_environment(monkeypatch)
    monkeypatch.setenv("PEANO_BERTRAND_REQUESTED_NODES", "1")
    with pytest.raises(RUNNER.ClosureError, match="cannot claim Slurm"):
        RUNNER._requested_resources(RUNNER.LOCAL_DIAGNOSTIC_MODE)


def test_git_observation_matches_head_and_rejects_dirty_wmi_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "config", "user.name", "Audit"],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(repository),
            "config",
            "user.email",
            "audit@example.invalid",
        ],
        check=True,
    )
    tracked = repository / "tracked.txt"
    tracked.write_text("sealed\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repository), "add", "tracked.txt"], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "commit", "-q", "-m", "seal"],
        check=True,
    )
    head = subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    monkeypatch.setattr(RUNNER, "_repository_root", lambda: repository)
    observed = RUNNER._observed_repository()
    assert observed == {
        "availability": "git",
        "clean": True,
        "head": head,
        "status_entries": 0,
        "status_sha256": sha256(b"").hexdigest(),
        "top_level_matches_repository": True,
    }

    _set_wmi_environment(monkeypatch)
    monkeypatch.setenv("PEANO_BERTRAND_LOCAL_COMMIT", head)
    provenance = RUNNER._source_provenance(RUNNER.WMI_SLURM_MODE)
    assert provenance["declared_upload"]["local_commit"] == head
    assert provenance["observed_repository"]["clean"] is True

    monkeypatch.setenv("PEANO_BERTRAND_LOCAL_COMMIT", "0" * 40)
    with pytest.raises(RUNNER.ClosureError, match="differs from observed"):
        RUNNER._source_provenance(RUNNER.WMI_SLURM_MODE)
    monkeypatch.setenv("PEANO_BERTRAND_LOCAL_COMMIT", head)

    (repository / "untracked.txt").write_text("dirty\n", encoding="utf-8")
    dirty = RUNNER._observed_repository()
    assert dirty["clean"] is False
    assert dirty["status_entries"] == 1
    with pytest.raises(RUNNER.ClosureError, match="worktree is dirty"):
        RUNNER._source_provenance(RUNNER.WMI_SLURM_MODE)


def test_payload_without_git_is_never_mislabeled_as_observed_git(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = tmp_path / "payload"
    payload.mkdir()
    monkeypatch.setattr(RUNNER, "_repository_root", lambda: payload)
    assert RUNNER._observed_repository() == {
        "availability": "payload_without_git"
    }
    _set_wmi_environment(monkeypatch)
    provenance = RUNNER._source_provenance(RUNNER.WMI_SLURM_MODE)
    assert provenance["declared_upload"] == {
        "local_commit": "1" * 40,
        "local_dirty": False,
        "payload_sha256": "2" * 64,
    }
    assert provenance["observed_repository"] == {
        "availability": "payload_without_git"
    }


def test_two_tiny_passes_are_fresh_deterministic_zero_dne_and_atomic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_local_environment(monkeypatch)
    report = tmp_path / "success/receipt.json"
    assert RUNNER.main(
        [
            "--execution-mode",
            "local-diagnostic",
            "--theorem",
            TINY_TARGET,
            "--report",
            str(report),
        ]
    ) == 0
    receipt = json.loads(report.read_text(encoding="utf-8"))
    assert receipt["status"] == "passed"
    assert receipt["passes"] == 2
    assert receipt["deterministic_across_passes"] is True
    assert receipt["admission_eligible"] is False
    assert receipt["execution"]["mode"] == "local-diagnostic"
    assert receipt["execution"]["synthetic"] is False
    assert receipt["execution"]["proof_execution"] == (
        "native-two-fresh-processes"
    )
    assert receipt["execution"]["scheduler"] == {"kind": "none"}
    assert receipt["requested_resources"] is None
    assert receipt["source_provenance"]["declared_upload"] is None
    assert receipt["results"] == EXPECTED_TINY_RECEIPT
    assert receipt["results"][TINY_TARGET]["dne_objects"] == 0
    assert receipt["report_schema"] == RUNNER._report_schema_receipt()
    passes = receipt["cold_passes"]
    payloads = [item["worker_payload"] for item in passes]
    assert [item["pass_index"] for item in payloads] == [1, 2]
    assert payloads[0]["receipt"] == payloads[1]["receipt"]
    assert payloads[0]["receipt"]["results"] == EXPECTED_TINY_RECEIPT
    worker_pids = [item["process"]["pid"] for item in payloads]
    worker_nonces = [item["process"]["process_nonce"] for item in payloads]
    assert len(set(worker_pids)) == len(set(worker_nonces)) == 2
    assert os.getpid() not in worker_pids
    assert all(
        item["process"]["parent_pid"] == os.getpid() for item in payloads
    )
    assert all(
        sha256(RUNNER._canonical_json_bytes(item["worker_payload"])).hexdigest()
        == item["worker_payload_sha256"]
        for item in passes
    )
    assert report.read_bytes().endswith(b"\n")
    assert tuple(report.parent.glob(f".{report.name}.pass-*.json")) == ()
    assert tuple(report.parent.glob(f".{report.name}.*.tmp")) == ()
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.validate(receipt, schema)
    crossed = json.loads(json.dumps(receipt))
    crossed["admission_eligible"] = True
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(crossed, schema)
    synthetic = json.loads(json.dumps(receipt))
    synthetic["execution"]["synthetic"] = True
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(synthetic, schema)

    with pytest.raises(RUNNER.ClosureError, match="overwrite"):
        RUNNER.main(
            [
                "--execution-mode",
                "local-diagnostic",
                "--theorem",
                TINY_TARGET,
                "--report",
                str(report),
            ]
        )


def test_report_writer_rejects_dangling_symlinks_and_link_races(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_local_environment(monkeypatch)
    dangling_target = tmp_path / "redirected.json"
    dangling = tmp_path / "dangling.json"
    dangling.symlink_to(dangling_target)
    with pytest.raises(RUNNER.ClosureError, match="overwrite"):
        RUNNER.main(_local_tiny_arguments(dangling))
    assert not dangling_target.exists()

    existing_target = tmp_path / "existing-target.json"
    existing_target.write_bytes(b"do-not-touch\n")
    existing_link = tmp_path / "existing-link.json"
    existing_link.symlink_to(existing_target)
    with pytest.raises(RUNNER.ClosureError, match="overwrite"):
        RUNNER.main(_local_tiny_arguments(existing_link))
    assert existing_target.read_bytes() == b"do-not-touch\n"

    raced = tmp_path / "raced.json"
    real_link = RUNNER.os.link

    def competing_link(source, destination):
        Path(destination).write_bytes(b"winner\n")
        return real_link(source, destination)

    monkeypatch.setattr(RUNNER.os, "link", competing_link)
    with pytest.raises(RUNNER.ClosureError, match="overwrite"):
        RUNNER._write_report(raced, {"loser": True})
    assert raced.read_bytes() == b"winner\n"
    assert tuple(tmp_path.glob(f".{raced.name}.*.tmp")) == ()

    reserved = tmp_path / "reserved.json"
    reserved_temporary = tmp_path / f".{reserved.name}.{os.getpid()}.tmp"
    reserved_temporary.write_bytes(b"foreign\n")
    with pytest.raises(RUNNER.ClosureError, match="temporary report"):
        RUNNER._write_report(reserved, {"must_not_publish": True})
    assert reserved_temporary.read_bytes() == b"foreign\n"
    assert not reserved.exists()


def test_failure_nondeterminism_reused_process_and_fabricated_dne_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_local_environment(monkeypatch)
    failed_report = tmp_path / "failed.json"
    real_subprocess_run = RUNNER.subprocess.run
    calls = 0

    def failed_worker(command, **kwargs):
        nonlocal calls
        if command and command[0] == "git":
            return real_subprocess_run(command, **kwargs)
        calls += 1
        if calls == 1:
            return real_subprocess_run(command, **kwargs)
        return subprocess.CompletedProcess(command, 9, None, "synthetic failure")

    monkeypatch.setattr(RUNNER.subprocess, "run", failed_worker)
    with pytest.raises(RUNNER.ClosureError, match="exit 9"):
        RUNNER.main(
            _local_tiny_arguments(failed_report)
        )
    assert calls == 2
    assert not failed_report.exists()
    assert tuple(tmp_path.glob(f".{failed_report.name}.pass-*.json")) == ()

    monkeypatch.setattr(RUNNER.subprocess, "run", real_subprocess_run)
    common = RUNNER._deterministic_receipt(
        (TINY_TARGET,),
        RUNNER._parent_receipt(),
        RUNNER._execution_receipt(RUNNER.LOCAL_DIAGNOSTIC_MODE),
        RUNNER._source_provenance(RUNNER.LOCAL_DIAGNOSTIC_MODE),
        RUNNER._requested_resources(RUNNER.LOCAL_DIAGNOSTIC_MODE),
        RUNNER._report_schema_receipt(),
        EXPECTED_TINY_RECEIPT,
    )

    def fake_pass(index: int, receipt: dict[str, object], pid: int):
        payload = {
            "format": RUNNER.WORKER_FORMAT,
            "pass_index": index,
            "process": {
                "parent_pid": os.getpid(),
                "pid": pid,
                "process_nonce": f"{index:032x}",
            },
            "receipt": receipt,
            "schema_version": 2,
            "status": "passed",
        }
        return {
            "worker_payload": payload,
            "worker_payload_sha256": sha256(
                RUNNER._canonical_json_bytes(payload)
            ).hexdigest(),
        }

    nondeterministic = tmp_path / "nondeterministic.json"

    def nondeterministic_worker(
        index, _execution_mode, _selected, _report, _expected
    ):
        receipt = json.loads(json.dumps(common))
        if index == 2:
            receipt["results"][TINY_TARGET]["cuts"] = 1
        return fake_pass(index, receipt, os.getpid() + index)

    monkeypatch.setattr(RUNNER, "_run_worker", nondeterministic_worker)
    with pytest.raises(RUNNER.ClosureError, match="nondeterministic"):
        RUNNER.main(
            _local_tiny_arguments(nondeterministic)
        )
    assert not nondeterministic.exists()

    reused = tmp_path / "reused.json"

    def reused_worker(index, _execution_mode, _selected, _report, _expected):
        return fake_pass(index, common, os.getpid() + 1)

    monkeypatch.setattr(RUNNER, "_run_worker", reused_worker)
    with pytest.raises(RUNNER.ClosureError, match="distinct fresh processes"):
        RUNNER.main(_local_tiny_arguments(reused))
    assert not reused.exists()

    fabricated = json.loads(json.dumps(EXPECTED_TINY_RECEIPT))
    fabricated[TINY_TARGET]["dne_objects"] = 1
    with pytest.raises(RUNNER.ClosureError, match="found DNE"):
        RUNNER._validate_result_receipts(fabricated, (TINY_TARGET,))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("dependency_closure_count", 2),
        ("dependency_closure_sha256", "0" * 64),
        ("direct_dependencies", ["fabricated"]),
        ("dne_objects", 1),
        ("script_commands", 12),
        ("script_sha256", "0" * 64),
        ("source_path", "fabricated.py"),
        ("source_sha256", "0" * 64),
        ("statement_characters", 1),
        ("statement_sha256", "0" * 64),
    ],
)
def test_derivable_worker_receipt_mutations_are_rejected(
    field: str,
    value: object,
) -> None:
    fabricated = json.loads(json.dumps(EXPECTED_TINY_RECEIPT))
    fabricated[TINY_TARGET][field] = value
    with pytest.raises(RUNNER.ClosureError):
        RUNNER._validate_result_receipts(fabricated, (TINY_TARGET,))


@pytest.mark.parametrize("kind", ["artifact", "source", "schema"])
def test_bound_byte_mutations_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    real_sha = RUNNER._sha256_file

    def mutated(path: Path) -> str:
        text = path.as_posix()
        if kind == "artifact" and text.endswith("catalog-v3.json"):
            return "0" * 64
        if kind == "source" and text.endswith(
            "bertrand_prime_interval_candidate.py"
        ):
            return "0" * 64
        if kind == "schema" and text.endswith("closure-v2.schema.json"):
            return "0" * 64
        return real_sha(path)

    monkeypatch.setattr(RUNNER, "_sha256_file", mutated)
    if kind == "artifact":
        with pytest.raises(RUNNER.ClosureError, match="artifact-family"):
            RUNNER._parent_receipt()
    elif kind == "source":
        with pytest.raises(RUNNER.ClosureError, match="source bytes"):
            RUNNER._local_specs()
    else:
        with pytest.raises(RUNNER.ClosureError, match="schema bytes"):
            RUNNER._report_schema_receipt()
