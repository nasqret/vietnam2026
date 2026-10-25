"""Synthetic launch contract tests; all scheduler/SSH paths are replaced.

Fixture approvals are NOT human consent and fixture token/proof records are
NOT native or model evidence. They exist only in temporary test directories.
"""
import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).absolute().parents[3]
HELPER = ROOT / "training/peano_hydra/frontier_pilot_launch.py"


def _module():
    spec = importlib.util.spec_from_file_location("_frontier_launch_fixture", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def gate(tmp_path, monkeypatch):
    module = _module()
    scratch = tmp_path / "scratch"
    root = scratch / module.REMOTE_PARENT / module.REMOTE_CHILD
    root.mkdir(parents=True)
    monkeypatch.setattr(module, "ROOT", root)
    monkeypatch.setattr(module.safe, "ROOT", root)
    monkeypatch.setenv("SCRATCH", str(scratch))
    monkeypatch.setenv("USER", "synthetic")
    for name in tuple(os.environ):
        if name.startswith(("SLURM_", "SBATCH_", "PEANO_JOB_", "PEANO_HYDRA_")):
            monkeypatch.delenv(name, raising=False)

    def put(name, value):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = value if isinstance(value, bytes) else module.canonical(value) + b"\n"
        path.write_bytes(raw)
        return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

    def seal(value, field):
        value[field] = module.digest({key: item for key, item in value.items() if key != field})
        return value

    commit = "a" * 40
    put(".peano-source-provenance.tsv", (commit + "\tfalse\t2026-08-30T00:00:00Z\n").encode())
    sources = {}
    for name in sorted(module.REQUIRED_SOURCES | {"peano-lab/py/synthetic.py"}):
        raw = ((ROOT / name).read_bytes() if name.endswith("requirements-helios.lock")
               else ("# SYNTHETIC TEST SOURCE, NEVER EXECUTED: " + name + "\n").encode())
        sources[name] = put(name, raw)
    payloads = {}

    def payload(name, value):
        record = put(name, value)
        payloads[name] = record
        return record

    pins = dict(module.PINS, native_source_manifest_sha256="b" * 64, lineage_proposal_sha256="c" * 64)
    ready_file = payload(module.INPUTS["candidate_readiness"], {
        "synthetic_not_native_evidence": True,
        "source_manifest_sha256": pins["native_source_manifest_sha256"],
        "lineage_proposal_sha256": pins["lineage_proposal_sha256"],
    })
    pins["candidate_readiness_sha256"] = ready_file["sha256"]
    scope = [{"component_id": "synthetic", "split": "train", "diagnostic": False}]
    review = seal({
        "schema": "peano-hydra-scaling-lineage-review-v1", "decision": "accept",
        "asserted_human_review": True, "reviewer_reference": "SYNTHETIC TEST; NOT HUMAN AUTHORIZATION",
        "proposal_sha256": pins["lineage_proposal_sha256"], "scope": scope,
        "acknowledgments": {key: True for key in module.ACKNOWLEDGMENTS},
    }, "review_sha256")
    review_file = payload(module.INPUTS["lineage_review"], review)
    native_files = {name: payload(module.ADMITTED + "/source/" + name, b"synthetic native bytes; NOT a proof\n")
                    for name in ("epoch.json", "manifest.json", "sft.jsonl", "preferences.jsonl", "discovery.jsonl")}
    admitted = seal({
        "schema": "peano-hydra-frontier-model-data-admission-v1", "status": "review-accepted-native-source",
        "run_id": module.RUN_ID, "human_review_asserted": True, "model_data_admitted": True,
        "review_sha256": review["review_sha256"], "candidate_readiness_sha256": ready_file["sha256"],
        "source_manifest_sha256": pins["native_source_manifest_sha256"],
        "proposal_sha256": pins["lineage_proposal_sha256"], "scope": scope,
        "files": {"lineage-review.json": review_file, "candidate-readiness.json": ready_file},
        "source_files": native_files,
        "counts": {"candidate_projected_split_rows": {"train": 12772, "dev": 2096, "test": 0, "quarantine": 0},
                   "candidate_projected_rows": 14868, "native_routes": 1152, "native_transition_rows": 15264},
    }, "admission_sha256")
    admitted_file = payload(module.INPUTS["training_admission"], admitted)
    prep_files = {name: payload(module.PREPARATION + "/" + name, b"synthetic preparation; NOT training data\n")
                  for name in ("config.toml", "train.jsonl", "dev.jsonl", "quarantine.jsonl", "preferences.jsonl", "discovery.jsonl")}
    # Real preparation JSONL descriptors additionally carry row counts.
    prep_files["train.jsonl"] = dict(prep_files["train.jsonl"], rows=12772)
    prep_file = payload(module.INPUTS["preparation_manifest"], {
        "run_id": module.RUN_ID, "model": module.MODEL, "epoch_sha256": pins["epoch_sha256"],
        "training": {"adapter_output_dir": module.ADAPTER_OUTPUT},
        "curriculum_identity": {"review_admission": {"admission_file_sha256": admitted_file["sha256"]}},
        "files": prep_files,
    })
    payload(module.INPUTS["preparation_preflight"], {
        "preparation_manifest_sha256": prep_file["sha256"], "training_rows": 12772,
        "development_rows": 2096, "expected_optimizer_steps": 1597, "run_id": module.RUN_ID,
        "adapter_output_dir": module.ADAPTER_OUTPUT, "model_trained": False, "cuda_initialized": False,
    })
    summaries, exposures = {}, {}
    for split, rows, total, maximum, supervised in (("train", 12772, 6977592, 682, 14), ("dev", 2096, 1156032, 678, 5)):
        summaries[split] = {"rows": rows, "total": total, "maximum": maximum, "sum_squared": total * maximum,
                            "supervised_maximum": supervised}
        exposures[split] = seal({"format": "peano-policy-token-exposure", "v": 1, "rows": rows, "role": split,
                                 "max_length": 4096, "sequence": {"total": total, "maximum": maximum, "sum_squared": total * maximum},
                                 "supervision": {"maximum": supervised}}, "record_sha256")
    token_record = {
        "schema": "peano-hydra-frontier-production-token-preflight-v1", "status": "passed",
        "preparation_manifest_sha256": prep_file["sha256"], "tokenizer_file_sha256": pins["tokenizer_json_sha256"],
        "configured_max_length": 4096, "model_weights_loaded": False, "splits": summaries, "token_exposure": exposures,
        "review_sha256": review["review_sha256"], "admission": {"admission_file_sha256": admitted_file["sha256"]},
        "preparation_bytes": sum(v["bytes"] for k, v in payloads.items() if k.startswith(module.PREPARATION + "/")),
        "preparation_byte_cap": 64 * 1024**2,
    }
    token_sources = {name: sources[name]["sha256"] for name in module.TOKEN_PREFLIGHT_SOURCES}
    process_path = module.INPUTS["token_preflight"] + ".process.json"
    process_file = payload(process_path, {
        "schema": "peano-hydra-frontier-token-process-v1", "passed": True, "sources_unchanged": True,
        "source_files": token_sources,
        "process": {"reason": "exited", "returncode": 0, "observed_descendant_count": 0,
                    "stdout": module.canonical(token_record).decode() + "\n"},
    })
    token_record.update(process_receipt={"file": Path(process_path).name, "sha256": process_file["sha256"]},
                        execution_source_files=token_sources)
    payload(module.INPUTS["token_preflight"], token_record)
    payload(module.INPUTS["evaluation_request"], {"benchmark_review": {"synthetic_never_executed": True}})
    old_file = payload(module.INPUTS["baseline_adapter_manifest"], {
        "model": module.MODEL, "adapter": {"sha256": pins["baseline_adapter_sha256"]},
        "tokenizer": {"sha256": pins["baseline_tokenizer_sha256"]},
    })
    pins["baseline_adapter_manifest_sha256"] = old_file["sha256"]
    monkeypatch.setattr(module, "PINS", {key: pins[key] for key in module.PINS})
    request = {
        "schema": module.REQUEST_SCHEMA, "status": "ready-for-explicit-resource-approval",
        "profile": module.PROFILE, "run_id": module.RUN_ID, "source_commit": commit,
        "source_files": sources, "payloads": payloads, "payloads_sha256": module.digest(payloads),
        "inputs": deepcopy(module.INPUTS), "review_sha256": review["review_sha256"], "pins": pins,
        "model": deepcopy(module.MODEL), "training": deepcopy(module.TRAINING), "evaluation": deepcopy(module.EVALUATION),
        "reservations": deepcopy(module.RESERVATIONS), "maximum_aggregate_gpu_seconds": 9000,
        "maximum_concurrent_gpus": 1, "automatic_retry": False, "resume": False, "refunds": False,
        "runtime_dependencies": deepcopy(module.RUNTIME), "transfer_authorized": False, "gpu_execution_authorized": False,
    }
    value = SimpleNamespace(module=module, root=root, commit=commit, request=request, payloads=payloads,
                            put=put, payload=payload, seal=seal, calls=[], scheduled={}, released=[],
                            fail_submit=None, snapshot_overrides={}, running=False)

    def resign():
        request["payloads_sha256"] = module.digest(payloads)
        request_file = put(module.REQUEST, request)
        approval = {"schema": module.APPROVAL_SCHEMA, "profile": module.PROFILE, "run_id": module.RUN_ID,
                    "approved": True, "approval_reference": "SYNTHETIC TEST ONLY; NOT USER APPROVAL",
                    "request_file_sha256": request_file["sha256"]}
        value.approval = approval
        value.sha = put(module.APPROVAL, approval)["sha256"]
        return value.sha

    value.resign = resign
    resign()

    def scheduler(arguments, environment=None):
        assert environment is None
        value.calls.append(list(arguments))
        if arguments[0] == "squeue":
            return "".join(f"{job}|{root}|{module.JOB_NAMES[stage]}|PENDING\n" for stage, job in value.scheduled.items())
        if arguments[0] == "sacct":
            if "--format=JobIDRaw,State,ExitCode" in arguments:
                return value.scheduled["train"] + "|COMPLETED|0:0\n"
            return "".join(f"{job}|{module.JOB_NAMES[stage]}|{root}|\n" for stage, job in value.scheduled.items())
        if arguments[0] == "sbatch":
            stage = next(stage for stage in module.STAGES if module.JOBS[stage] in arguments)
            identity = module._identity(value.approval, request, value.sha)
            state = module.load_ledger(identity)
            assert state["gpu_seconds"] == 9000
            assert state["phase"] == ("reserve" if stage == "train" else "train-accepted")
            if value.fail_submit == stage:
                raise ValueError("synthetic ambiguous scheduler response")
            job = str(41001 + len(value.scheduled))
            value.scheduled[stage] = job
            return job + "\n"
        if arguments[:4] == ["scontrol", "-o", "show", "job"]:
            job = arguments[-1]
            stage = next(stage for stage, recorded in value.scheduled.items() if recorded == job)
            fields = {"JobId": job, "JobName": module.JOB_NAMES[stage], "WorkDir": str(root),
                      "JobState": "RUNNING" if value.running else "PENDING",
                      "Reason": "None" if value.running else "JobHeldUser", "Priority": "1" if value.running else "0",
                      "Dependency": "(null)" if stage == "train" else "afterok:" + value.scheduled["train"] + "(unfulfilled)",
                      "Requeue": "0", "Account": module.ACCOUNT, "Partition": module.PARTITION,
                      "TimeLimit": module.WALL[stage], "NumNodes": "1", "NumCPUs": "8",
                      "ReqTRES": "billing=1,cpu=8,mem=64G,node=1,gres/gpu=1"}
            if value.running:
                fields["Dependency"] = "(null)"
            fields.update(value.snapshot_overrides)
            return " ".join(key + "=" + item for key, item in fields.items()) + "\n"
        if arguments[:2] == ["scontrol", "release"]:
            identity = module._identity(value.approval, request, value.sha)
            assert module.load_ledger(identity)["phase"] in ("release-authorized", "evaluate-released")
            value.released.append(arguments[-1])
            return ""
        pytest.fail("unexpected external operation: " + repr(arguments))

    monkeypatch.setattr(module, "run", scheduler)
    return value


def test_new_gate_is_python36_compatible_and_shells_parse():
    ast.parse(HELPER.read_text(), feature_version=6)
    for name in ("scripts/helios_hydra_frontier.sh", "scripts/run_peano_hydra_frontier.sh",
                 "slurm/peano_hydra_frontier_train.sbatch", "slurm/peano_hydra_frontier_evaluate.sbatch"):
        subprocess.run(["bash", "-n", str(ROOT / name)], check=True, timeout=5)


def test_genuine_metadata_paths_are_not_needed_by_module_import():
    code = "import runpy,sys; runpy.run_path(sys.argv[1]); assert not {'torch','transformers','peft','tokenizers'} & set(sys.modules)"
    subprocess.run([sys.executable, "-I", "-B", "-c", code, str(HELPER)], check=True, timeout=5)


def test_launcher_output_matches_real_trainer_config_for_the_frozen_v28_epoch():
    """Real config construction; only the two epoch metadata fields are a stub."""
    from training.peano_hydra import frontier_pilot_launch as launch, posttrain
    epoch = SimpleNamespace(version="v28", epoch_sha256=launch.PINS["epoch_sha256"])
    raw, config = posttrain._config(epoch, output=ROOT / launch.PREPARATION, run_id=launch.RUN_ID,
                                   authority_profile="peano-authority-primitive-v1")
    assert config.run.output_dir == launch.ADAPTER_OUTPUT
    assert "/qwen3-1.7b-authority-primitive-v28-f64b5f100c9c-frontier-v1" in config.run.output_dir
    assert ('output_dir = "' + launch.ADAPTER_OUTPUT + '"').encode() in raw


def test_synthetic_request_validation_does_not_call_scheduler(gate):
    gate.module.validate_metadata(gate.sha)
    assert gate.calls == []


def test_generated_draft_never_supplies_approval_or_placeholder_identities(gate):
    draft = gate.module.request_template()
    assert draft["status"] == "draft-missing-prerequisites"
    assert draft["source_commit"] is None and draft["review_sha256"] is None
    assert all(draft["pins"][key] is None for key in gate.module.CANDIDATE_PIN_FIELDS)
    with pytest.raises(ValueError, match="draft"):
        gate.module.validate_request(draft)
    assert gate.calls == []


@pytest.mark.parametrize("key,value", [
    ("status", "draft-missing-prerequisites"), ("review_sha256", None),
    ("maximum_aggregate_gpu_seconds", 9001), ("maximum_concurrent_gpus", True),
    ("automatic_retry", True), ("resume", True), ("refunds", True), ("gpu_execution_authorized", True),
])
def test_draft_and_changed_fixed_scope_fail_before_external_calls(gate, key, value):
    gate.request[key] = value
    gate.resign()
    with pytest.raises((ValueError, TypeError)):
        gate.module.launch(gate.sha, submit=True, expected_commit=gate.commit)
    assert not gate.calls
    assert not (gate.root / gate.module.LEDGER).exists()


@pytest.mark.parametrize("input_name", [
    "lineage_review", "training_admission", "preparation_manifest", "preparation_preflight",
    "token_preflight", "evaluation_request", "baseline_adapter_manifest",
])
def test_missing_prerequisite_never_reaches_scheduler(gate, input_name):
    (gate.root / gate.module.INPUTS[input_name]).unlink()
    with pytest.raises((ValueError, OSError)):
        gate.module.launch(gate.sha, submit=True, expected_commit=gate.commit)
    assert gate.calls == []


@pytest.mark.parametrize("input_name,field,value", [
    ("lineage_review", "decision", "reject"),
    ("lineage_review", "asserted_human_review", False),
    ("training_admission", "model_data_admitted", False),
    ("token_preflight", "status", "diagnostic-fit-passed"),
    ("token_preflight", "model_weights_loaded", True),
    ("token_preflight", "preparation_manifest_sha256", "f" * 64),
    ("evaluation_request", "benchmark_review", None),
])
def test_rehashed_but_invalid_admission_still_fails(gate, input_name, field, value):
    path = gate.module.INPUTS[input_name]
    record = json.loads((gate.root / path).read_text())
    record[field] = value
    if input_name == "lineage_review":
        gate.seal(record, "review_sha256")
    if input_name == "training_admission":
        gate.seal(record, "admission_sha256")
    gate.payload(path, record)
    gate.resign()
    with pytest.raises(ValueError):
        gate.module.launch(gate.sha, submit=True, expected_commit=gate.commit)
    assert gate.calls == []


def test_separate_raw_approval_is_required(gate):
    gate.approval["approved"] = False
    sha = gate.put(gate.module.APPROVAL, gate.approval)["sha256"]
    with pytest.raises(ValueError, match="explicit resource approval"):
        gate.module.launch(sha, submit=True, expected_commit=gate.commit)
    assert gate.calls == []


def test_unknown_source_or_payload_leaf_is_rejected(gate):
    gate.put("scripts/extra-unapproved.py", b"unapproved\n")
    with pytest.raises(ValueError, match="unapproved leaves"):
        gate.module.validate_metadata(gate.sha)
    assert gate.calls == []


def test_two_jobs_are_fully_reserved_held_and_released_in_dependency_order(gate):
    result = gate.module.launch(gate.sha, submit=True, expected_commit=gate.commit)
    assert result["jobs"] == {"train": "41001", "evaluate": "41002"}
    assert result["reserved_gpu_seconds"] == 9000
    assert gate.released == ["41002", "41001"]
    submissions = [call for call in gate.calls if call[0] == "sbatch"]
    assert len(submissions) == 2
    assert "--hold" in submissions[0] and "--hold" in submissions[1]
    assert "--dependency=afterok:41001" in submissions[1]
    assert "--time=02:00:00" in submissions[0] and "--time=00:30:00" in submissions[1]
    assert all("--no-requeue" in call and "--gres=gpu:1" in call for call in submissions)
    identity = gate.module._identity(gate.approval, gate.request, gate.sha)
    assert gate.module.load_ledger(identity)["phase"] == "train-released"
    before = list(gate.calls)
    with pytest.raises(ValueError, match="already opened/charged"):
        gate.module.launch(gate.sha, submit=True, expected_commit=gate.commit)
    assert gate.calls == before


@pytest.mark.parametrize("stage,expected_jobs", [("train", {}), ("evaluate", {"train": "41001"})])
def test_ambiguous_submission_never_retries_or_releases_and_keeps_full_charge(gate, stage, expected_jobs):
    gate.fail_submit = stage
    with pytest.raises(ValueError, match="ambiguous"):
        gate.module.launch(gate.sha, submit=True, expected_commit=gate.commit)
    identity = gate.module._identity(gate.approval, gate.request, gate.sha)
    state = gate.module.load_ledger(identity)
    assert state["gpu_seconds"] == 9000 and state["jobs"] == expected_jobs
    assert gate.released == []
    before = list(gate.calls)
    with pytest.raises(ValueError, match="already opened/charged"):
        gate.module.launch(gate.sha, submit=True, expected_commit=gate.commit)
    assert gate.calls == before


@pytest.mark.parametrize("field,value", [
    ("TimeLimit", "03:00:00"), ("NumCPUs", "16"), ("Requeue", "1"),
    ("ReqTRES", "cpu=8,mem=64G,node=1,gres/gpu=2"), ("Account", "other-account"),
    ("Dependency", "(null),afterany:999"), ("WorkDir", "/tmp/foreign"),
])
def test_controller_mismatch_keeps_both_jobs_held(gate, field, value):
    gate.snapshot_overrides[field] = value
    with pytest.raises(ValueError):
        gate.module.launch(gate.sha, submit=True, expected_commit=gate.commit)
    assert gate.scheduled == {"train": "41001", "evaluate": "41002"}
    assert gate.released == []


def test_scheduled_gate_requires_exact_recorded_job_and_current_resources(gate, monkeypatch):
    gate.module.launch(gate.sha, submit=True, expected_commit=gate.commit)
    gate.running = True
    monkeypatch.setenv("SLURM_JOB_ID", "41002")
    monkeypatch.setenv("SLURM_SUBMIT_DIR", str(gate.root))
    monkeypatch.setenv("PEANO_JOB_SCRIPT", gate.module.JOBS["evaluate"])
    monkeypatch.setenv("PEANO_HYDRA_PROFILE", gate.module.PROFILE)
    assert gate.module.check_job_reservation(gate.sha, "evaluate")["job_id"] == "41002"
    gate.snapshot_overrides["TimeLimit"] = "01:00:00"
    with pytest.raises(ValueError, match="resources"):
        gate.module.check_job_reservation(gate.sha, "evaluate")
    gate.snapshot_overrides.clear()
    monkeypatch.setenv("SLURM_RESTART_COUNT", "1")
    with pytest.raises(ValueError, match="restart"):
        gate.module.check_job_reservation(gate.sha, "evaluate")


def test_missing_real_approval_stops_shell_before_ssh(tmp_path):
    fakebin = tmp_path / "bin"
    fakebin.mkdir()
    marker = tmp_path / "SSH_WAS_CALLED"
    ssh = fakebin / "ssh"
    ssh.write_text("#!/bin/sh\n: > " + str(marker) + "\nexit 97\n")
    ssh.chmod(0o700)
    env = {key: value for key, value in os.environ.items() if not key.startswith(("SLURM_", "SBATCH_"))}
    env["PATH"] = str(fakebin) + os.pathsep + os.environ["PATH"]
    result = subprocess.run(["bash", str(ROOT / "scripts/helios_hydra_frontier.sh"),
                             "--approval-sha256", "0" * 64, "--test-only"],
                            env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert not marker.exists()


def test_token_preflight_rejects_unadmitted_candidate_before_backend_import(tmp_path):
    script = ROOT / "scripts/preflight_peano_hydra_frontier_tokens.py"
    spec = importlib.util.spec_from_file_location("_frontier_token_fixture", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    preparation = tmp_path / "unadmitted" / "preparation"
    preparation.mkdir(parents=True)
    raw = b'{"synthetic_not_admitted":true}\n'
    (preparation / "manifest.json").write_bytes(raw)
    args = SimpleNamespace(preparation_dir=preparation, expected_preparation_manifest_sha256=hashlib.sha256(raw).hexdigest(),
                           expected_review_sha256="0" * 64, tokenizer_root=tmp_path / "never-read",
                           tokenizer_site=tmp_path / "never-imported")
    before = set(sys.modules)
    with pytest.raises((ValueError, OSError)):
        module.worker(args)
    assert not {"tokenizers", "torch", "transformers", "peft"} & (set(sys.modules) - before)


def test_direct_scheduled_trainer_cannot_skip_semantic_benchmark_check(monkeypatch):
    script = ROOT / "scripts/execute_peano_hydra_frontier_train.py"
    spec = importlib.util.spec_from_file_location("_frontier_train_fixture", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    from training.peano_hydra import frontier_pilot_launch as gate, posttrain
    calls, trained = [], []
    monkeypatch.setattr(sys, "argv", [str(script), "--approval-sha256", "a" * 64])
    monkeypatch.setattr(gate, "check_job_reservation", lambda sha, stage: {"evaluation_request_sha256": "b" * 64})
    monkeypatch.setattr(posttrain, "execute", lambda *args: trained.append(args))

    def reject_semantics(arguments, **kwargs):
        calls.append(arguments)
        assert "--check" in arguments and "--expected-request-sha256" in arguments and "b" * 64 in arguments
        raise subprocess.CalledProcessError(2, arguments)

    monkeypatch.setattr(module.subprocess, "run", reject_semantics)
    with pytest.raises(subprocess.CalledProcessError):
        module.main()
    assert len(calls) == 1 and not trained
