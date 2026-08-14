"""No-network tests for the bounded Hydra A2.3c WMI audit protocol."""

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
RUNNER_PATH = ROOT / "scripts" / "run_peano_hydra_a23c_negative_replay_wmi.py"
SOURCE_STATE = ROOT / "scripts" / "build_peano_hydra_a23c_replayer_source_state.py"
SUBMIT = ROOT / "scripts" / "submit_wmi_hydra_a23c_negative_replay.sh"
COLLECT = ROOT / "scripts" / "collect_wmi_hydra_a23c_negative_replay.sh"
SBATCH = ROOT / "slurm" / "peano_wmi_hydra_a23c_negative_replay.sbatch"


def _load_runner():
    spec = importlib.util.spec_from_file_location(
        "_test_peano_hydra_a23c_wmi", RUNNER_PATH
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
        *(path for path, _digest in WMI.FROZEN_REPLAYER_SOURCES),
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


def _candidate_fixture(_source_state: dict[str, object]) -> dict[str, object]:
    observations = [
        {"record_sha256": hashlib.sha256(str(index).encode("ascii")).hexdigest()}
        for index in range(WMI.EXPECTED_INDEPENDENT_OBSERVATION_COUNT)
    ]
    theorems: list[dict[str, object]] = []
    offset = 0
    for index, name in WMI.EXPECTED_ROOTS:
        count = WMI.EXPECTED_DIRECT_COUNTS[name]
        theorem = {
            **{field: False for field in WMI.CANDIDATE_FALSE_FIELDS},
            "baseline": {"status": "full-vector-baseline-kernel-accepted"},
            "index": index,
            "name": name,
            "negative_observation_count": count,
            "negative_observations": observations[offset : offset + count],
            "negative_observations_independently_verified": True,
            "record_sha256": hashlib.sha256(name.encode("ascii")).hexdigest(),
        }
        offset += count
        theorems.append(theorem)
    joins = [
        {
            "fresh_observation_record_sha256": row["record_sha256"],
            "route_row_count": 2,
        }
        for row in observations
    ]
    body: dict[str, object] = {
        **{field: False for field in WMI.CANDIDATE_FALSE_FIELDS},
        "aggregate": {
            "full_vector_baseline_count": WMI.EXPECTED_BASELINE_COUNT,
            "independent_shared_observation_count": (
                WMI.EXPECTED_INDEPENDENT_OBSERVATION_COUNT
            ),
            "retained_route_row_count": WMI.EXPECTED_RETAINED_ROUTE_ROW_COUNT,
            "route_rows_per_shared_observation": 2,
            "theorem_count": len(WMI.EXPECTED_ROOTS),
        },
        "baseline_records": [{}, {}, {}],
        "baselines": {"root_sha256": "2" * 64},
        "campaign_executed": True,
        "environment": {},
        "format": (
            "peano-hydra-library-pilot-dependency-vector-negative-replay"
        ),
        "id": "independent-a2.3c-pilot-vector-negative-replay-v1",
        "independence": {},
        "logic_mode": "intuitionistic",
        "negative_observation_records": observations,
        "negative_observations": {"root_sha256": "3" * 64},
        "negative_observations_independently_verified": True,
        "predecessors": {},
        "result_exists": True,
        "retained_route_join": {
            "fresh_observation_count": (
                WMI.EXPECTED_INDEPENDENT_OBSERVATION_COUNT
            ),
            "joins": joins,
            "preimage": {},
            "retained_route_row_count": WMI.EXPECTED_RETAINED_ROUTE_ROW_COUNT,
            "root_sha256": "1" * 64,
            "route_rows_per_observation": 2,
            "status": "exact-44-route-rows-joined-two-to-one",
        },
        "route_rejections_independently_verified": False,
        "schema": {},
        "status": "passed",
        "theorem_count": len(WMI.EXPECTED_ROOTS),
        "theorem_records": {"root_sha256": "4" * 64},
        "theorems": theorems,
        "v": 1,
    }
    preimage = {
        "format": (
            "peano-hydra-library-pilot-dependency-vector-negative-replay-"
            "root-preimage"
        ),
        "payload": body,
        "v": 1,
    }
    return {
        **body,
        "root_preimage": preimage,
        "root_sha256": WMI._compact_sha256(preimage),
    }


def _verification_fixture(
    candidate: dict[str, object], candidate_raw: bytes
) -> dict[str, object]:
    protocol_rows = []
    for relative, digest in WMI.FROZEN_REPLAYER_SOURCES:
        raw = (ROOT / relative).read_bytes()
        protocol_rows.append(
            {"bytes": len(raw), "path": relative, "sha256": digest}
        )
    protocol_preimage = {
        "format": (
            "peano-hydra-library-pilot-dependency-vector-negative-replay-"
            "verified-protocol-sources-preimage"
        ),
        "sources": protocol_rows,
        "v": 1,
    }
    protocol_sources = {
        "count": 4,
        "independence_source_scan": (
            "no-a2.3b-wrapper-import-or-compile-candidate-body-call"
        ),
        "preimage": protocol_preimage,
        "root_sha256": WMI._compact_sha256(protocol_preimage),
    }

    schema = json.loads(
        (
            ROOT
            / "training/peano_hydra/"
            "library-pilot-dependency-vector-negative-replay-schema-v1.json"
        ).read_bytes()
    )
    retained_rows = [
        {
            "artifact_sha256": identity["artifact_sha256"],
            "bytes": identity["bytes"],
            "label": label,
            "path": identity["path"],
        }
        for label, identity in sorted(schema["fixed_inputs"].items())
    ]
    for label, relative in (
        (
            "a2.3b_producer_source_state",
            "artifacts/peano-hydra/a23b-wmi-vector-audit-220220/inputs/"
            "producer-source-state.json",
        ),
        (
            "a2.3b_producer_git_verification",
            "artifacts/peano-hydra/a23b-wmi-vector-audit-220220/inputs/"
            "producer-git-verification-receipt.json",
        ),
    ):
        raw = (ROOT / relative).read_bytes()
        retained_rows.append(
            {
                "artifact_sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
                "label": label,
                "path": relative,
            }
        )
    retained_preimage = {
        "evidence": retained_rows,
        "format": (
            "peano-hydra-library-pilot-dependency-vector-negative-replay-"
            "verified-retained-evidence-preimage"
        ),
        "v": 1,
    }
    retained_evidence = {
        "count": 8,
        "preimage": retained_preimage,
        "root_sha256": WMI._compact_sha256(retained_preimage),
        "status": (
            "exact-retained-predecessors-and-source-evidence-authenticated"
        ),
    }

    theorem_rows = []
    for index, name in WMI.EXPECTED_ROOTS:
        count = WMI.EXPECTED_DIRECT_COUNTS[name]
        theorem = {
            **{field: False for field in WMI.VERIFIER_FALSE_FIELDS},
            "baseline_record_sha256": hashlib.sha256(
                f"{name}:baseline".encode("ascii")
            ).hexdigest(),
            "index": index,
            "name": name,
            "negative_observation_count": count,
            "negative_observation_records_root_sha256": hashlib.sha256(
                f"{name}:observations".encode("ascii")
            ).hexdigest(),
            "retained_route_pair_count": count,
            "structural_result_verified": True,
        }
        theorem["record_sha256"] = WMI._compact_sha256(theorem)
        theorem_rows.append(theorem)
    theorem_preimage = {
        "format": WMI.FORMAT_VERIFIER_RECORDS,
        "records": [
            {
                "index": row["index"],
                "name": row["name"],
                "record_sha256": row["record_sha256"],
            }
            for row in theorem_rows
        ],
        "v": 1,
    }
    candidate_binding = {
        "artifact_bytes": len(candidate_raw),
        "artifact_sha256": hashlib.sha256(candidate_raw).hexdigest(),
        "baseline_records_root_sha256": candidate["baselines"]["root_sha256"],
        "negative_observation_records_root_sha256": (
            candidate["negative_observations"]["root_sha256"]
        ),
        "retained_route_join_root_sha256": (
            candidate["retained_route_join"]["root_sha256"]
        ),
        "root_sha256": candidate["root_sha256"],
        "theorem_records_root_sha256": (
            candidate["theorem_records"]["root_sha256"]
        ),
    }
    body: dict[str, object] = {
        **{field: False for field in WMI.VERIFIER_FALSE_FIELDS},
        "aggregate": {
            "full_vector_baseline_count": 3,
            "negative_observation_count": 22,
            "retained_route_pair_count": 22,
            "retained_route_row_count": 44,
            "theorem_count": 3,
        },
        "candidate": candidate_binding,
        "candidate_negative_observations_structurally_verified": True,
        "candidate_status": "passed",
        "format": WMI.FORMAT_VERIFIER,
        "id": WMI.VERIFIER_ID,
        "logic_mode": "intuitionistic",
        "predecessor_evidence_authenticated": True,
        "producer_environment_structurally_verified": True,
        "producer_independence_source_verified": True,
        "protocol_sources": protocol_sources,
        "retained_evidence": retained_evidence,
        "source_protocol_authenticated": True,
        "status": "passed",
        "structural_receipts_verified": True,
        "structural_result_verified": True,
        "theorem_count": 3,
        "theorem_records": {
            "count": 3,
            "preimage": theorem_preimage,
            "root_sha256": WMI._compact_sha256(theorem_preimage),
        },
        "theorems": theorem_rows,
        "v": 1,
        "verifier": {
            "bytecode_write_disabled": True,
            "import_policy": (
                "python-standard-library-only-no-peano-or-training-import"
            ),
            "load_mode": "authenticated-source-bytes-source_to_code-exec",
            "module_name": WMI.VERIFIER_MODULE_NAME,
            "path": WMI.VERIFIER_MODULE_PATH,
            "pycache_prefix": WMI.DISABLED_PYCACHE_PREFIX,
            "sha256": WMI.VERIFIER_MODULE_SHA256,
            "source_bytes": WMI.VERIFIER_MODULE_BYTES,
            "tactic_free": True,
        },
    }
    preimage = {"format": WMI.FORMAT_VERIFIER_ROOT, "payload": body, "v": 1}
    return {
        **body,
        "root_preimage": preimage,
        "root_sha256": WMI._compact_sha256(preimage),
    }
def test_protocol_constants_are_exactly_three_twenty_two_and_forty_four() -> None:
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
    assert WMI.EXPECTED_BASELINE_COUNT == 3
    assert WMI.EXPECTED_RETAINED_ROUTE_ROW_COUNT == 44
    assert WMI.EXPECTED_INDEPENDENT_OBSERVATION_COUNT == 22
    assert WMI.MAX_JSON_BYTES == 16_000_000
    assert WMI.FORMAT_VERIFIER == (
        "peano-hydra-library-pilot-dependency-vector-negative-replay-"
        "independent-verification"
    )
    assert WMI.VERIFIER_ID == (
        "independent-a2.3c-pilot-vector-negative-replay-"
        "structural-verification-v1"
    )
    assert WMI.VERIFIER_MODULE_NAME == (
        "_peano_hydra_a23c_tactic_free_structural_verifier"
    )
    verifier_module_raw = (ROOT / WMI.VERIFIER_MODULE_PATH).read_bytes()
    assert len(verifier_module_raw) == WMI.VERIFIER_MODULE_BYTES
    assert hashlib.sha256(verifier_module_raw).hexdigest() == WMI.VERIFIER_MODULE_SHA256
    verifier_cli_raw = (ROOT / WMI.VERIFIER_CLI_PATH).read_bytes()
    assert len(verifier_cli_raw) == WMI.VERIFIER_CLI_BYTES
    assert hashlib.sha256(verifier_cli_raw).hexdigest() == WMI.VERIFIER_CLI_SHA256
    assert {
        "bounded_three_root_vector_audit_complete",
        "execution_receipt_bound",
        "negative_replays_independently_reexecuted",
        "tactic_semantics_independently_verified",
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
        "_test_a23c_source_state_vector", SOURCE_STATE
    )
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = generator
    spec.loader.exec_module(generator)
    assert WMI.FROZEN_REPLAYER_SOURCES == tuple(
        (path.as_posix(), digest)
        for path, digest in generator.FROZEN_REPLAYER_SOURCES
    )


def test_runner_deeply_consumes_external_clean_git_receipts(
    tmp_path: Path,
) -> None:
    spec = importlib.util.spec_from_file_location(
        "_test_a23c_source_state_receipt", SOURCE_STATE
    )
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = generator
    spec.loader.exec_module(generator)

    repository = tmp_path / "clean-repository"
    repository.mkdir()
    for relative in (
        *(Path(path) for path, _digest in WMI.FROZEN_REPLAYER_SOURCES),
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
    state, receipt, _envelope = generator.build_replayer_evidence(repository)
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
        "baseline_record_count": 3,
        "bytes": len(raw),
        "independent_negative_observation_count": 22,
        "negative_observations_independently_verified": True,
        "path": "candidate.json",
        "replayer_observations_execution_bound": False,
        "replayer_source_state_root_sha256": "1" * 64,
        "retained_route_row_count": 44,
        "root_sha256": candidate["root_sha256"],
        "sha256": hashlib.sha256(raw).hexdigest(),
    }

    for mutation in ("count", "join", "authority", "record"):
        forged = deepcopy(candidate)
        if mutation == "count":
            forged["aggregate"]["independent_shared_observation_count"] = 21
        elif mutation == "join":
            forged["retained_route_join"]["retained_route_row_count"] = 43
        elif mutation == "authority":
            forged["proof_authority"] = True
        else:
            forged["theorems"][0]["record_sha256"] = "malformed"
        with pytest.raises(WMI.A23CWMIError):
            WMI._validate_candidate_document(
                forged,
                raw=_canonical(forged),
                filename="forged.json",
                source_state=source_state,
            )


def test_verifier_consumer_enforces_tactic_free_structural_boundary() -> None:
    source_payload = {"format": WMI.FORMAT_SOURCE_STATE, "v": 1}
    source_preimage = {
        "format": WMI.FORMAT_SOURCE_STATE_ROOT,
        "payload": source_payload,
        "v": 1,
    }
    source_state = {
        **source_payload,
        "root_preimage": source_preimage,
        "root_sha256": WMI._compact_sha256(source_preimage),
    }
    source_raw = _canonical(source_state)
    candidate = _candidate_fixture(source_state)
    candidate_raw = _canonical(candidate)
    receipt = _verification_fixture(candidate, candidate_raw)
    WMI._validate_verifier_receipt(
        receipt,
        candidate=candidate,
        candidate_raw=candidate_raw,
        source_state=source_state,
        source_state_raw=source_raw,
        source_root=ROOT,
    )

    for mutation in ("false-claim", "candidate", "retained-path", "theorem"):
        forged = deepcopy(receipt)
        if mutation == "false-claim":
            forged["tactic_semantics_independently_verified"] = True
        elif mutation == "candidate":
            forged["candidate"]["artifact_sha256"] = "0" * 64
        elif mutation == "retained-path":
            forged["retained_evidence"]["preimage"]["evidence"][0][
                "path"
            ] = "/etc/passwd"
        else:
            forged["theorems"][0]["record_sha256"] = "0" * 64
        with pytest.raises(WMI.A23CWMIError):
            WMI._validate_verifier_receipt(
                forged,
                candidate=candidate,
                candidate_raw=candidate_raw,
                source_state=source_state,
                source_state_raw=source_raw,
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
        role="replayer-0",
        argv=["/reviewed/python", "-B", "-P", "-s", "-S", "replayer.py"],
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


def test_child_timeout_kills_process_group_and_classifies_unknown(
    tmp_path: Path,
) -> None:
    record = WMI._run_process(
        role="timed-child",
        argv=[sys.executable, "-S", "-c", "import time; time.sleep(30)"],
        cwd=tmp_path,
        run_root=tmp_path,
        hash_seed=1,
        timeout_seconds=0.05,
    )
    assert record["timed_out"] is True
    assert record["returncode"] != 0
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
    with pytest.raises(WMI.A23CWMIError, match="existing|replace"):
        WMI._publish_create_only(output, value)
    link = tmp_path / "linked.json"
    link.symlink_to(output)
    with pytest.raises(WMI.A23CWMIError):
        WMI._publish_create_only(link, value)


def test_create_only_publication_detects_stage_swap_and_preserves_unowned_name(
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
    with pytest.raises(WMI.A23CWMIError, match="identity"):
        WMI._publish_create_only(output, value)

    assert output.read_bytes() == attacker_bytes


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
        "completed-dual-replayer-and-independent-structural-verification",
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


def test_collection_missing_linked_and_malformed_evidence_cannot_promote(
    tmp_path: Path,
) -> None:
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
    with pytest.raises(WMI.A23CWMIError):
        WMI._strict_json(malformed, limit=1024)

    collector_source = RUNNER_PATH.read_text(encoding="utf-8")
    assert '"status": "rejected-as-unknown"' in collector_source
    assert '"status": "missing-as-unknown"' in collector_source
    assert "_publish_create_only(args.output, _receipt_with_root(payload))" in collector_source


@pytest.mark.parametrize("relative", ("/etc/passwd", "../escape", "a/../escape"))
def test_source_evidence_paths_cannot_escape_snapshot(
    tmp_path: Path, relative: str
) -> None:
    with pytest.raises(WMI.A23CWMIError, match="unsafe"):
        WMI._source_file(tmp_path, relative)


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
    with pytest.raises(WMI.A23CWMIError, match="source drifted"):
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
    assert "#SBATCH --job-name=peano-hydra-a23c-neg" in sbatch
    assert "#SBATCH --gres" not in sbatch
    assert "--gpus" not in submit
    assert "env -i" in sbatch and "env -i" in collect
    assert 'chmod a-w "$collection"' in collect
    assert "-B -P -s -S" in sbatch and "-B -P -s -S" in collect
    assert "sys.flags.no_user_site" in sbatch
    assert "sys.flags.optimize" in sbatch
    assert "l0-pilot-dependency-vector-negative-replay-candidate-v1.json" in runner
    assert "candidate-v1-hashseed-1.json" in runner
    assert "PEANO-HYDRA-A23C-WMI-NEGATIVE-REPLAY" in submit
    assert "replayer_hash_seeds" in runner
    assert "negative_observations_independently_verified" in runner
    assert "replayer_observations_execution_bound" in runner
    assert '"independent_wrapper_implementation": True' in runner
    assert '"shared_engine_with_a2.3b": True' in runner
    assert '"tactic_semantics_independently_verified_by_verifier": False' in runner

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
