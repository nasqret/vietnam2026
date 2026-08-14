"""No-network tests for the bounded Hydra A2.3b WMI audit protocol."""

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
RUNNER_PATH = ROOT / "scripts" / "run_peano_hydra_a23b_wmi.py"
SOURCE_STATE = ROOT / "scripts" / "build_peano_hydra_a23b_producer_source_state.py"
SUBMIT = ROOT / "scripts" / "submit_wmi_hydra_a23b_vector_audit.sh"
COLLECT = ROOT / "scripts" / "collect_wmi_hydra_a23b_vector_audit.sh"
SBATCH = ROOT / "slurm" / "peano_wmi_hydra_a23b_vector_audit.sbatch"


def _load_runner():
    spec = importlib.util.spec_from_file_location(
        "_test_peano_hydra_a23b_wmi", RUNNER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


WMI = _load_runner()


def _canonical(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


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


def _shared_digest(name: str, position: int) -> str:
    return hashlib.sha256(f"{name}:{position}".encode("ascii")).hexdigest()


def _candidate_fixture(source_state: dict[str, object]) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    identities: list[dict[str, object]] = []
    for index, name in WMI.EXPECTED_ROOTS:
        count = WMI.EXPECTED_DIRECT_COUNTS[name]
        route_rows: list[dict[str, object]] = []
        for route_name in (
            "readable-direct-closure",
            "proposed-layered-closure-construction",
        ):
            formula_sha = hashlib.sha256(
                f"{name}:formula".encode("ascii")
            ).hexdigest()
            proof_sha = hashlib.sha256(
                f"{name}:{route_name}:proof".encode("ascii")
            ).hexdigest()
            proof_metrics = {
                "cut_nodes": 1,
                "proof_depth": 2,
                "proof_nodes": 3,
            }
            attempts = [
                {
                    "attempt_index": position,
                    "attempted_dependencies": [
                        f"dependency-{item}"
                        for item in range(count)
                        if item != position
                    ],
                    "layered_compiler_invoked": False,
                    "omitted_dependency": f"dependency-{position}",
                    "outcome": "exact-route-rejected",
                    "route": route_name,
                    "route_specific_assembly_reached": False,
                    "shared_root_body_observation_sha256": _shared_digest(
                        name, position
                    ),
                    "terminal_stage": "root-body-regeneration",
                }
                for position in range(count)
            ]
            route_rows.append(
                {
                    "attempts": attempts,
                    "baseline": {
                        "proof": {
                            "formula_sha256": formula_sha,
                            "kernel_accepted": True,
                            "kernel_context": "empty",
                            "logic_mode": "intuitionistic",
                            "metrics": proof_metrics,
                            "proof_term_sha256": proof_sha,
                        },
                        "status": "kernel-accepted-baseline",
                    },
                    "route": route_name,
                    "single_omission_kernel_accepted_count": 0,
                    "single_omission_rejected_count": count,
                    "status": "bounded-route-audit-complete",
                }
            )
        row: dict[str, object] = {
            **{field: False for field in WMI.AUTHORITY_CLAIM_KEYS},
            "bounded_protocol_executed": True,
            "bounded_three_root_vector_audit_complete": False,
            "index": index,
            "name": name,
            "routes": route_rows,
            "shared_body_consistency": {
                "paired_attempt_count": count,
                "status": "shared-root-body-consistent",
            },
            "single_omission_attempt_count": count * 2,
            "single_omission_kernel_accepted_count": 0,
            "single_omission_rejected_count": count * 2,
            "single_omission_terminal_count": count * 2,
            "terminal_route_observations_complete": True,
        }
        row["record_sha256"] = WMI._compact_sha256(row)
        rows.append(row)
        identities.append(
            {
                "index": index,
                "name": name,
                "record_sha256": row["record_sha256"],
            }
        )
    records_preimage = {
        "format": (
            "peano-hydra-library-pilot-dependency-vector-audit-records-preimage"
        ),
        "records": identities,
        "v": 1,
    }
    body: dict[str, object] = {
        **{name: False for name in WMI.AUTHORITY_CLAIM_KEYS},
        "aggregate": {
            "kernel_accepted_baseline_count": 6,
            "pilot_theorem_count": 3,
            "route_count": 2,
            "single_omission_attempt_count": 44,
            "single_omission_kernel_accepted_count": 0,
            "single_omission_rejected_count": 44,
            "single_omission_terminal_count": 44,
        },
        "bounded_protocol_executed": True,
        "bounded_three_root_protocol_frozen": True,
        "bounded_three_root_vector_audit_complete": False,
        "format": "peano-hydra-library-pilot-dependency-vector-audit",
        "id": "authoring-l0-pilot-dependency-vector-audit-candidate-v1",
        "logic_mode": "intuitionistic",
        "producer_git_verified": False,
        "producer_source_state": source_state,
        "producer_source_state_sha256": WMI._compact_sha256(source_state),
        "status": "candidate",
        "terminal_route_observations_complete": True,
        "theorem_count": 3,
        "theorem_records": {
            "count": 3,
            "preimage": records_preimage,
            "root_sha256": WMI._compact_sha256(records_preimage),
        },
        "v": 1,
    }
    preimage = {
        "format":
        "peano-hydra-library-pilot-dependency-vector-audit-root-preimage",
        "payload": body,
        "v": 1,
    }
    return {
        **body,
        "root_preimage": preimage,
        "root_sha256": WMI._compact_sha256(preimage),
        "theorems": rows,
    }


def _verification_fixture(
    candidate: dict[str, object], source_state: dict[str, object]
) -> dict[str, object]:
    candidate_raw = _canonical(candidate)
    source_raw = _canonical(source_state)
    rows: list[dict[str, object]] = []
    identities: list[dict[str, object]] = []
    for (index, name), candidate_row in zip(
        WMI.EXPECTED_ROOTS, candidate["theorems"], strict=True
    ):
        baseline_rows = []
        for candidate_route, route, source in zip(
            candidate_row["routes"],
            (
                "readable-direct-closure",
                "proposed-layered-closure-construction",
            ),
            (
                "fixed-a2.2-embedded-artifact",
                "fixed-a2.3a-embedded-artifact",
            ),
            strict=True,
        ):
            proof = candidate_route["baseline"]["proof"]
            baseline_rows.append(
                {
                    "artifact_sha256": hashlib.sha256(
                        f"{name}:{route}:artifact".encode("ascii")
                    ).hexdigest(),
                    "formula_sha256": proof["formula_sha256"],
                    "fuel": 40,
                    "kernel_accepted": True,
                    "kernel_context": "empty",
                    "metrics": {
                        "artifact_bytes": 100,
                        **proof["metrics"],
                    },
                    "proof_term_sha256": proof["proof_term_sha256"],
                    "route": route,
                    "source": source,
                }
            )
        direct_count = WMI.EXPECTED_DIRECT_COUNTS[name]
        row: dict[str, object] = {
            "baseline_artifacts": baseline_rows,
            "candidate_record_sha256": candidate_row["record_sha256"],
            "index": index,
            "name": name,
            "producer_observation_route_record_count": direct_count * 2,
            "unique_shared_root_body_observation_count": direct_count,
        }
        row["record_sha256"] = WMI._compact_sha256(row)
        rows.append(row)
        identities.append(
            {
                "index": index,
                "name": name,
                "record_sha256": row["record_sha256"],
            }
        )
    records_preimage = {
        "format": WMI.FORMAT_VERIFIER_RECORDS,
        "records": identities,
        "v": 1,
    }
    module_raw = (ROOT / WMI.VERIFIER_MODULE_PATH).read_bytes()
    body: dict[str, object] = {
        **{field: False for field in WMI.VERIFIER_FALSE_FIELDS},
        "aggregate": {
            "baseline_artifact_count": 6,
            "kernel_accepted_baseline_artifact_count": 6,
            "pilot_theorem_count": 3,
            "producer_observation_route_record_count": 44,
            "unique_shared_root_body_observation_count": 22,
        },
        "candidate": {
            "artifact_bytes": len(candidate_raw),
            "artifact_sha256": hashlib.sha256(candidate_raw).hexdigest(),
            "root_sha256": candidate["root_sha256"],
            "theorem_record_root_sha256": candidate["theorem_records"][
                "root_sha256"
            ],
        },
        "candidate_status": "candidate",
        "format": WMI.FORMAT_VERIFIER,
        "id": WMI.VERIFIER_ID,
        "kernel_baseline_artifacts_verified": True,
        "logic_mode": "intuitionistic",
        "producer_observations_structurally_verified": True,
        "producer_source_state": {
            "artifact_bytes": len(source_raw),
            "artifact_sha256": hashlib.sha256(source_raw).hexdigest(),
            "root_sha256": source_state["root_sha256"],
            "semantic_sha256": WMI._compact_sha256(source_state),
        },
        "producer_source_state_sha256": WMI._compact_sha256(source_state),
        "status": "passed",
        "structural_receipts_verified": True,
        "theorem_count": 3,
        "theorem_records": {
            "count": 3,
            "preimage": records_preimage,
            "root_sha256": WMI._compact_sha256(records_preimage),
        },
        "v": 1,
        "verifier": {
            "bytecode_write_disabled": True,
            "import_policy": "stdlib-and-peano-kernel-only",
            "kernel_sources": [
                {"module": module, "path": path, "sha256": digest}
                for module, path, digest in WMI.VERIFIER_KERNEL_SOURCES
            ],
            "load_mode": "direct-source-module-without-training-package-init",
            "path": WMI.VERIFIER_MODULE_PATH,
            "pycache_prefix": WMI.DISABLED_PYCACHE_PREFIX,
            "safe_path": True,
            "sha256": hashlib.sha256(module_raw).hexdigest(),
            "site_import_disabled": True,
            "source_loader_preflight": "pathfinder-sourcefileloader-exact-origin",
            "stdlib_precedes_peano_root": True,
            "user_site_disabled": True,
        },
    }
    preimage = {"format": WMI.FORMAT_VERIFIER_ROOT, "payload": body, "v": 1}
    return {
        **body,
        "root_preimage": preimage,
        "root_sha256": WMI._compact_sha256(preimage),
        "theorems": rows,
    }


def test_protocol_constants_are_exactly_three_six_forty_four_and_twenty_two() -> None:
    assert WMI.EXPECTED_ROOTS == (
        (256, "odd_add_odd"),
        (376, "finite_bounded_injective_surjective"),
        (379, "beta_product_swap_last_invariant"),
    )
    assert WMI.EXPECTED_DIRECT_COUNTS == {
        "odd_add_odd": 3,
        "finite_bounded_injective_surjective": 14,
        "beta_product_swap_last_invariant": 5,
    }
    assert WMI.EXPECTED_BASELINE_COUNT == 6
    assert WMI.EXPECTED_ROUTE_ATTEMPT_COUNT == 44
    assert WMI.EXPECTED_SHARED_OBSERVATION_COUNT == 22
    assert WMI.MAX_JSON_BYTES == 16_000_000
    assert WMI.FORMAT_VERIFIER == (
        "peano-hydra-library-pilot-dependency-vector-audit-verification"
    )
    assert WMI.VERIFIER_ID == (
        "independent-a2.3b-pilot-dependency-vector-audit-verification-v1"
    )
    verifier_module_raw = (ROOT / WMI.VERIFIER_MODULE_PATH).read_bytes()
    assert len(verifier_module_raw) == WMI.VERIFIER_MODULE_BYTES == 109_448
    assert (
        hashlib.sha256(verifier_module_raw).hexdigest()
        == WMI.VERIFIER_MODULE_SHA256
        == "b5f5cf39ea7b12d3ed52ee176ed733b28fa2e9224640e89dac77df87b14dfab1"
    )
    verifier_cli_raw = (ROOT / WMI.VERIFIER_CLI_PATH).read_bytes()
    assert len(verifier_cli_raw) == WMI.VERIFIER_CLI_BYTES == 18_653
    assert (
        hashlib.sha256(verifier_cli_raw).hexdigest()
        == WMI.VERIFIER_CLI_SHA256
        == "ed9e234f5af04e5878e6f4fd23aace512c66c0bc249fc33dd19c1fcbcdb908c2"
    )
    assert {
        "bounded_three_root_vector_audit_complete",
        "negative_observations_independently_verified",
        "producer_git_verified",
        "producer_observations_execution_bound",
        "route_rejections_independently_verified",
    }.issubset(WMI.VERIFIER_FALSE_FIELDS)
    assert WMI.EXPECTED_RESOURCES == {
        "partition": "cpu_idle",
        "nodes": 1,
        "ntasks": 1,
        "cpus_per_task": 1,
        "memory_mib": 4096,
        "time_limit": "00:15:00",
        "time_limit_seconds": 900,
    }
    assert WMI.PINNED_WMI_PYTHON.endswith("/bin/python")
    runner_source = RUNNER_PATH.read_text(encoding="utf-8")
    assert "3.12.12" in runner_source
    assert "sys.flags.no_user_site != 1" in runner_source
    assert "sys.flags.optimize != 0" in runner_source


def test_runner_and_external_generator_share_the_exact_four_file_vector() -> None:
    spec = importlib.util.spec_from_file_location(
        "_test_a23b_source_state_vector", SOURCE_STATE
    )
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = generator
    spec.loader.exec_module(generator)
    assert WMI.FROZEN_PRODUCER_SOURCES == tuple(
        (path.as_posix(), digest)
        for path, digest in generator.FROZEN_PRODUCER_SOURCES
    )


def test_runner_deeply_consumes_external_clean_git_receipts(
    tmp_path: Path,
) -> None:
    spec = importlib.util.spec_from_file_location(
        "_test_a23b_source_state_receipt", SOURCE_STATE
    )
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = generator
    spec.loader.exec_module(generator)

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
    state, receipt, _envelope = generator.build_producer_evidence(repository)
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


def test_candidate_consumer_preserves_shared_negative_evidence_boundary() -> None:
    source_state = {"root_sha256": "1" * 64}
    candidate = _candidate_fixture(source_state)
    raw = _canonical(candidate)
    accepted, record = WMI._validate_candidate_document(
        candidate,
        raw=raw,
        filename="candidate.json",
        source_state=source_state,
    )
    assert accepted == candidate
    assert record == {
        "baseline_artifact_count": 6,
        "bytes": len(raw),
        "negative_observations_independently_verified": False,
        "path": "candidate.json",
        "producer_observations_execution_bound": False,
        "root_sha256": candidate["root_sha256"],
        "route_negative_record_count": 44,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "unique_shared_root_body_observation_count": 22,
    }

    for mutation in ("count", "shared", "authority", "record"):
        forged = deepcopy(candidate)
        if mutation == "count":
            forged["aggregate"]["single_omission_attempt_count"] = 43
        elif mutation == "shared":
            forged["theorems"][0]["routes"][1]["attempts"][0][
                "shared_root_body_observation_sha256"
            ] = "0" * 64
        elif mutation == "authority":
            forged["proof_authority"] = True
        else:
            forged["theorems"][0]["record_sha256"] = "0" * 64
        with pytest.raises(WMI.A23BWMIError):
            WMI._validate_candidate_document(
                forged,
                raw=_canonical(forged),
                filename="forged.json",
                source_state=source_state,
            )


def test_verifier_consumer_enforces_exact_baseline_and_negative_split() -> None:
    assert (ROOT / WMI.VERIFIER_CLI_PATH).is_file()
    source_state = {"root_sha256": "1" * 64}
    candidate = _candidate_fixture(source_state)
    receipt = _verification_fixture(candidate, source_state)
    WMI._validate_verifier_receipt(
        receipt,
        candidate=candidate,
        candidate_raw=_canonical(candidate),
        source_state=source_state,
        source_state_raw=_canonical(source_state),
        source_root=ROOT,
    )
    for mutation in ("false-claim", "baseline", "shared-count", "record"):
        forged = deepcopy(receipt)
        if mutation == "false-claim":
            forged["negative_observations_independently_verified"] = True
        elif mutation == "baseline":
            forged["theorems"][0]["baseline_artifacts"][0][
                "kernel_accepted"
            ] = False
        elif mutation == "shared-count":
            forged["aggregate"][
                "unique_shared_root_body_observation_count"
            ] = 44
        else:
            forged["theorems"][0]["record_sha256"] = "0" * 64
        with pytest.raises(WMI.A23BWMIError):
            WMI._validate_verifier_receipt(
                forged,
                candidate=candidate,
                candidate_raw=_canonical(candidate),
                source_state=source_state,
                source_state_raw=_canonical(source_state),
                source_root=ROOT,
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
    assert record["environment"] == WMI._isolated_environment(0)
    assert "PYTHONPATH" not in observed["env"]
    assert record["returncode"] == 7
    assert WMI._process_outcome(record) == "unknown"


def test_child_output_limit_kills_process_and_classifies_unknown(
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


def test_create_only_receipt_publication_refuses_existing_or_link(
    tmp_path: Path,
) -> None:
    output = tmp_path / "receipt.json"
    value = WMI._receipt_with_root(
        {"format": "fixture-receipt", "status": "unknown", "v": 1}
    )
    WMI._publish_create_only(output, value)
    assert output.read_bytes() == _canonical(value)
    with pytest.raises(WMI.A23BWMIError, match="existing|replace"):
        WMI._publish_create_only(output, value)
    link = tmp_path / "linked.json"
    link.symlink_to(output)
    with pytest.raises(WMI.A23BWMIError):
        WMI._publish_create_only(link, value)


def test_scheduler_resource_and_missing_evidence_fail_closed_as_unknown() -> None:
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
        "completed-dual-producer-and-independent-baselines-verified",
    )
    timed_out = {**base, "state": "TIMEOUT"}
    assert WMI._collection_status(
        accounting=timed_out,
        execution={"status": "passed"},
        stdout_exists=True,
        stderr_exists=True,
    )[0] == "unknown"
    oversized = {**base, "requested_memory": "8192M"}
    assert WMI._collection_status(
        accounting=oversized,
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
    assert WMI._collection_status(
        accounting=base,
        execution={"status": "failed"},
        stdout_exists=True,
        stderr_exists=True,
    ) == ("unknown", "malformed-execution-status")


def test_infrastructure_manifest_binds_every_live_protocol_source() -> None:
    missing = [
        relative
        for relative in WMI.INFRASTRUCTURE_SOURCES
        if not (ROOT / relative).is_file()
    ]
    assert missing == []
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
    with pytest.raises(WMI.A23BWMIError, match="source drifted"):
        WMI._validate_infrastructure_manifest(
            forged,
            source_root=ROOT,
            commit="1" * 40,
            tree="2" * 40,
        )


def test_shell_protocol_is_content_addressed_held_bounded_and_isolated() -> None:
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
    assert '"${ssh_command[@]}" "$ssh_target"' in submit
    assert '"${ssh_command[@]}" "$ssh_target"' in collect
    assert "ssh_route=()" not in submit
    assert "ssh_route=()" not in collect
    assert 'git -C "$repo_root" archive --format=tar HEAD' in submit
    assert 'snapshot_sha256="$(shasum -a 256 "$archive"' in submit
    assert "sbatch --hold --parsable" in submit
    assert 'scontrol release "$held_job"' in submit
    assert "set -o noclobber" in submit
    assert "--partition=cpu_idle" in submit
    assert "--mem=4096M" in submit
    assert "--time=00:15:00" in submit
    assert "#SBATCH --cpus-per-task=1" in sbatch
    assert "env -i" in sbatch and "env -i" in collect
    assert "-B -P -s -S" in sbatch and "-B -P -s -S" in collect
    assert "sys.flags.no_user_site" in sbatch
    assert "sys.flags.optimize" in sbatch
    assert "candidate-hashseed-0.json" in runner
    assert "candidate-hashseed-1.json" in runner
    assert "producer_hash_seeds" in runner
    assert "negative_observations_independently_verified" in runner
    assert "producer_observations_execution_bound" in runner

    joined = "\n".join((submit, collect, sbatch, runner, generator))
    for forbidden in (
        "build_peano_hydra_library_optimizer_comparison_pilot.py",
        "verify_peano_hydra_library_optimizer_comparison_pilot.py",
        "library_optimizer_comparison_verifier.py",
        "hydra-a23a",
        "PEANO_A23A",
    ):
        assert forbidden not in joined
    assert "range(384)" not in runner
    assert "LIBRARY_THEOREM_COUNT" not in runner


@pytest.mark.parametrize(
    ("script", "argv"),
    (
        (SUBMIT, ["--test-only"]),
        (COLLECT, ["--test-only", "--job-id", "1"]),
    ),
)
def test_hostile_jump_is_rejected_before_any_network_call(
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
    ("script", "expected_call_count"),
    ((SUBMIT, 2), (COLLECT, 1)),
)
@pytest.mark.parametrize("ssh_jump", (None, "", "jump.example"))
def test_bash32_direct_and_jump_ssh_argv_are_exact_without_network(
    tmp_path: Path,
    script: Path,
    expected_call_count: int,
    ssh_jump: str | None,
) -> None:
    bash = Path("/bin/bash")
    version = subprocess.run(
        [str(bash), "--version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout
    if sys.platform == "darwin":
        assert "GNU bash, version 3.2." in version

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
        [str(bash), str(script_under_test), *argv],
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
    expected_prefix = [
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=15",
    ]
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
