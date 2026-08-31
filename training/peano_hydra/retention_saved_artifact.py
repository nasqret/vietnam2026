"""Corrected admission of the one preserved, completed retention producer.

The original 4ae loader has an argument-count defect.  It is never patched or
claimed to have succeeded here.  An explicit fresh metadata worker executes
the real original binding and full record validator, then the real original
artifact-directory verifier with its required literal directory arguments.
That receipt remains provisional until separate custody binds the actually
observed final owner exit. Reuse never launches a worker or loads weights.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import sys
import time

from training.peano_hydra import corrective_workflow as files, origin_bridge as bridge
from training.peano_hydra import retention_training as training
from training.peano_hydra import review_runtime as runtime

ROOT = Path(__file__).absolute().parents[2]
WORKER = "scripts/authenticate_peano_hydra_retention_saved.py"
MODULE = "training/peano_hydra/retention_saved_artifact.py"
PRODUCER_COMMIT = "4aeae795c8cb5bfc622c9943359b5b38446089b9"
PRODUCER_SOURCE_SHA = "4f4fcbfcd51ff64b9674dfdde383b37337871d93f52792b3f6f9bedec6862665"
PRODUCER_INPUTS_SHA = "3df7953c0d405364aef689b5e67b083f5fc744492159643ca5b09e418a06a388"
PRODUCER_PLAN_SHA = "da26332740d587bdd946b12999fd37de73817115ed3da8983edf5004bd02abf0"
PRODUCER_TRAINER_SHA = "d6529651c031fce3fe535f7b8b9ccbbb3396125083640184f7125065b9e26725"
PRODUCER_EVALUATION_SHA = "1f42a76f0c1127b7edd2ce171c0e238b5846941a40b1c5cd185f676b9dc5bf92"
MODEL_MANIFEST_SHA = "cdacbda7777568120029b671374aaf16e994f2da2a54b867a00c81ece086d6ca"
TRAINING_JOB = "21456251"
PRODUCER_SCHEMA = "peano-hydra-preserved-retention-producer-v1"
REFERENCE_SCHEMA = "peano-hydra-preserved-retention-artifact-reference-v1"
REQUEST_SCHEMA = "peano-hydra-preserved-retention-admission-request-v1"
WORKER_SCHEMA = "peano-hydra-preserved-retention-admission-worker-v1"
RECEIPT_SCHEMA = "peano-hydra-preserved-retention-admission-v1"
CUSTODY_SCHEMA = "peano-hydra-preserved-retention-admission-custody-v1"
IDENTITY_SCHEMA = "peano-hydra-preserved-retention-training-identity-v1"
LIMITS = {"cpu_seconds": 30, "wall_seconds": 60, "rss_bytes": 2 * 1024**3, "output_bytes": 4 * 1024**2}
OWNER_LIMITS = {"cpu_seconds": 40, "wall_seconds": 90, "rss_bytes": 2 * 1024**3, "output_bytes": 16 * 1024**2}
OWNER_SCHEMA = "peano-hydra-retention-recovery-cpu-owner-v1"
INVOCATION_SCHEMA = "peano-hydra-retention-recovery-cpu-invocation-exit-v1"
OWNER_HELPER = "run-recovery-cpu-preflight-01.py"
SUPERVISOR_SHA = "1be34563858e2deba8e23ea47dc9f5966ffe092c3e0d23fe80a81a411b94af1c"
RECOVERY_CLI = "scripts/execute_peano_hydra_retention_evaluation_recovery.py"
MAX_METADATA = 4 * 1024**2
METHOD = "original-bind-and-full-record-validation-plus-explicit-artifact-directories"
NO_WORK = {"model_weights_loaded": False, "tokenizer_loaded": False, "native_proof_work": False,
           "gpu_allocated": False, "network_work": False, "training_performed": False,
           "original_load_training_artifact_succeeded": False, "automatic_retry": False, "resume": False}
require, canonical, digest = training.require, training.canonical, training.digest


def admission_sources():
    result = training.training_sources()
    result.update({name: hashlib.sha256(bridge._read(ROOT / name, 2 * 1024**2)).hexdigest()
                   for name in (MODULE, WORKER, "scripts/hydra_bounded_exec.py", RECOVERY_CLI,
                       "training/peano_hydra/retention_evaluation_recovery_launch.py",
                       "training/peano_hydra/helios_runtime.py")})
    return dict(sorted(result.items()))


@dataclass(frozen=True, slots=True)
class PreservedProducerReference:
    source_root: Path
    source_manifest: Path
    source_manifest_sha256: str
    inputs_path: Path
    inputs_sha256: str

    def __post_init__(self):
        for name in ("source_root", "source_manifest", "inputs_path"):
            object.__setattr__(self, name, bridge._absolute(Path(getattr(self, name))))
        require(self.source_manifest_sha256 == PRODUCER_SOURCE_SHA and self.inputs_sha256 == PRODUCER_INPUTS_SHA,
                "preserved producer needs the actual original source and inputs pins")
        require(self.inputs_path == self.source_root / training.PACKAGE / "inputs.json",
                "preserved producer inputs must retain their original source-relative location")

    def to_dict(self):
        return {"schema": PRODUCER_SCHEMA, "source_commit": PRODUCER_COMMIT,
                "source_manifest_sha256": self.source_manifest_sha256, "inputs_sha256": self.inputs_sha256,
                "training_plan_sha256": PRODUCER_PLAN_SHA, "trainer_sha256": PRODUCER_TRAINER_SHA,
                "evaluation_source_sha256": PRODUCER_EVALUATION_SHA}

    def locations(self):
        return {"source_root": str(self.source_root), "source_manifest": str(self.source_manifest),
                "inputs_path": str(self.inputs_path)}


@dataclass(frozen=True, slots=True)
class PreservedRetentionArtifactReference:
    manifest_path: Path
    manifest_sha256: str
    inputs: training.TrainingInputReference
    producer: PreservedProducerReference
    admission_receipt_path: Path | None = None
    admission_receipt_sha256: str | None = None

    def __post_init__(self):
        object.__setattr__(self, "manifest_path", bridge._absolute(Path(self.manifest_path)))
        require(type(self.inputs) is training.TrainingInputReference and type(self.producer) is PreservedProducerReference
                and self.manifest_path.name == "manifest.json" and self.manifest_sha256 == MODEL_MANIFEST_SHA,
                "preserved retention requires the actual completed model and explicit typed original inputs")
        require((self.admission_receipt_path is None) == (self.admission_receipt_sha256 is None),
                "an admission receipt needs both its path and external raw pin")
        if self.admission_receipt_path is not None:
            object.__setattr__(self, "admission_receipt_path", bridge._absolute(Path(self.admission_receipt_path)))
            training._sha(self.admission_receipt_sha256, "corrected admission receipt")

    def to_dict(self):
        return {"schema": REFERENCE_SCHEMA, "manifest_sha256": self.manifest_sha256,
                "training_inputs": self.inputs.to_dict(), "producer": self.producer.to_dict(),
                "admission_receipt_sha256": self.admission_receipt_sha256}

    def locations(self):
        return {"manifest_path": str(self.manifest_path), "training_inputs": self.inputs.locations(),
                "producer": self.producer.locations(), "admission_receipt_path":
                    None if self.admission_receipt_path is None else str(self.admission_receipt_path)}

    def protected_paths(self):
        return (self.manifest_path.parent, self.producer.source_root, self.producer.source_manifest.parent,
                *self.inputs.protected_paths(),
                *((self.admission_receipt_path.parent,) if self.admission_receipt_path is not None else ()))

    def load(self):
        return load_preserved_artifact(self)


def reference(record, locations):
    require(type(record) is dict and set(record) == {"schema", "manifest_sha256", "training_inputs", "producer",
            "admission_receipt_sha256"} and record["schema"] == REFERENCE_SCHEMA,
            "wrong preserved retention reference identity")
    require(type(locations) is dict and set(locations) == {"manifest_path", "training_inputs", "producer",
            "admission_receipt_path"}, "wrong preserved retention reference locations")
    require(type(record["producer"]) is dict and set(record["producer"]) == {"schema", "source_commit",
            "source_manifest_sha256", "inputs_sha256", "training_plan_sha256", "trainer_sha256", "evaluation_source_sha256"},
            "wrong preserved producer identity fields")
    where = locations["producer"]
    require(type(where) is dict and set(where) == {"source_root", "source_manifest", "inputs_path"},
            "wrong original producer locations")
    producer = PreservedProducerReference(Path(where["source_root"]), Path(where["source_manifest"]),
        record["producer"]["source_manifest_sha256"], Path(where["inputs_path"]), record["producer"]["inputs_sha256"])
    result = PreservedRetentionArtifactReference(Path(locations["manifest_path"]), record["manifest_sha256"],
        training.input_reference(record["training_inputs"], locations["training_inputs"]), producer,
        None if locations["admission_receipt_path"] is None else Path(locations["admission_receipt_path"]),
        record["admission_receipt_sha256"])
    require(result.to_dict() == record and result.locations() == locations, "preserved reference fields or paths changed")
    return result


def _draft(ref):
    return PreservedRetentionArtifactReference(ref.manifest_path, ref.manifest_sha256, ref.inputs, ref.producer)


def _descriptor(path, maximum=MAX_METADATA):
    path = bridge._absolute(Path(path))
    with bridge._Tree(path.parent) as tree:
        item, _ = tree.fingerprint(path.name, maximum=maximum)
        tree.assert_unchanged()
    return {key: item[key] for key in ("bytes", "sha256")}


def _producer_sources(producer):
    record, raw = training._record(producer.source_manifest, producer.source_manifest_sha256,
                                   bridge.MAX_BUNDLE_MANIFEST_BYTES)
    require(record["git_commit"] == PRODUCER_COMMIT
            and record["files"]["training/peano_hydra/retention_training.py"]["sha256"] == PRODUCER_TRAINER_SHA
            and record["files"]["training/peano_hydra/retention_evaluation.py"]["sha256"] == PRODUCER_EVALUATION_SHA,
            "preserved producer is not the actual original trainer/evaluator")
    with bridge._Tree(producer.source_root) as tree:
        bridge._check_sources(tree, record)
    return record, {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _input_files(inputs):
    manifest, raw = training._record(inputs.directory / "manifest.json", inputs.manifest_sha256)
    result = {"preparation/manifest.json": {"bytes": len(raw), "sha256": inputs.manifest_sha256}}
    with bridge._Tree(inputs.directory) as tree:
        require(tree.inventory("", maximum=32) == {"manifest.json", *manifest["files"]},
                "mixed input tree is not the original closed inventory")
        for name, expected in manifest["files"].items():
            item, _ = tree.fingerprint(name, maximum=bridge.MAX_DATA_BYTES)
            actual = {key: item[key] for key in ("bytes", "sha256")}
            require(actual == {key: expected[key] for key in actual}, "mixed input bytes changed")
            result["preparation/" + name] = actual
        tree.assert_unchanged()
    for name, path, sha in (("config", inputs.config_path, inputs.config_sha256),
                          ("evaluation-plan", inputs.evaluation_plan_path, inputs.evaluation_plan_sha256)):
        item = _descriptor(path)
        require(item["sha256"] == sha, "original configuration/evaluation bytes changed")
        result[name] = item
    return result


def _snapshot(ref):
    source, source_descriptor = _producer_sources(ref.producer)
    inputs, inputs_raw = training._record(ref.producer.inputs_path, ref.producer.inputs_sha256)
    require(inputs["training_input"] == ref.inputs.to_dict(), "current inputs relabel the original producer inputs")
    record, raw = training._record(ref.manifest_path, ref.manifest_sha256)
    require(len(raw) == 191597 and record["training_inputs"] == ref.inputs.to_dict()
            and record["training_plan_sha256"] == PRODUCER_PLAN_SHA
            and record["reservation"]["source_commit"] == PRODUCER_COMMIT
            and record["reservation"]["job_id"] == TRAINING_JOB,
            "saved model does not belong to the actual completed producer")
    # This is byte authentication, not a call to a current-source training plan.
    adapter, tokenizer = training._verified_artifact_directories(ref.manifest_path.parent, record)
    ancestors = {name: origin.load().origin for name, origin in
                 (("saved-v25", ref.inputs.baseline), ("frontier-v28", ref.inputs.frontier))}
    snapshot = {"producer_source_manifest": source_descriptor, "producer_source_files_sha256": source["files_sha256"],
        "producer_inputs": {"bytes": len(inputs_raw), "sha256": ref.producer.inputs_sha256},
        "training_inputs": ref.inputs.to_dict(), "input_files": _input_files(ref.inputs), "ancestor_origins": ancestors,
        "model_manifest": {"bytes": len(raw), "sha256": ref.manifest_sha256},
        "artifacts": {"adapter": record["adapter"], "tokenizer": record["tokenizer"]}}
    require(bridge._read(ref.manifest_path, MAX_METADATA) == raw, "saved model manifest changed during hashing")
    return snapshot, record, adapter, tokenizer


def _training_identity(record, ref):
    contract = record["common_contract"]
    return {"schema": IDENTITY_SCHEMA, "manifest_sha256": ref.manifest_sha256,
        "training_plan_sha256": record["training_plan_sha256"], "training_inputs": ref.inputs.to_dict(),
        "ancestor_origins": record["training_plan"]["ancestor_origins"], "model": record["model"],
        "training_authority_profile": contract["authority_profile"], "training_authority": contract["authority"],
        "training_prompt_contract": contract["prompt_contract"], "training_decoder_profile": contract["decoder_profile"],
        "artifacts": {"adapter": record["adapter"], "tokenizer": record["tokenizer"]},
        "initialization": record["initialization"], "job_id": record["reservation"]["job_id"],
        "producer": ref.producer.to_dict(), "admission_method": METHOD,
        "claim_boundary": "Preserved completed mixed SFT, admitted by corrected original-source metadata calls; no legacy origin or quality claim.",
        **training.CLAIMS}


def _process_limits(value):
    require(type(value) is dict and set(value) == set(LIMITS)
            and all(type(value[key]) is int and 1 <= value[key] <= LIMITS[key] for key in LIMITS)
            and value["rss_bytes"] == LIMITS["rss_bytes"] and value["output_bytes"] == LIMITS["output_bytes"],
            "historical admission process limits escaped its separate metadata envelope")
    return runtime.ProcessLimits(**value)


def _validate_receipt(receipt, ref, snapshot, record, sources):
    require(type(receipt) is dict and set(receipt) == {"schema", "status", "request", "process", "worker_result",
            "before", "after", "whole_call", "claim_boundary", *NO_WORK}
            and receipt["schema"] == RECEIPT_SCHEMA and receipt["status"] == "passed-corrected-historical-admission"
            and all(receipt[key] is False for key in NO_WORK), "corrected historical admission is not a successful exact receipt")
    request = receipt["request"]
    require(type(request) is dict and set(request) == {"schema", "candidate_reference", "locations", "admission_sources",
            "execution", "limits"} and request["schema"] == REQUEST_SCHEMA,
            "historical admission worker request changed")
    saved = reference(request["candidate_reference"], request["locations"])
    require(saved.admission_receipt_sha256 is None and saved.to_dict() == _draft(ref).to_dict()
            and request["admission_sources"] == sources and receipt["before"] == receipt["after"] == snapshot,
            "historical admission receipt changed its source, model or original input bytes")
    execution = request["execution"]
    require(type(execution) is dict and set(execution) == {"source_root", "python", "worker", "runtime_library_paths"},
            "historical admission execution locations changed")
    root = bridge._absolute(Path(execution["source_root"]))
    python = bridge._absolute(Path(execution["python"]))
    require(str(root) == execution["source_root"] and str(python) == execution["python"]
            and execution["worker"] == str(root / WORKER)
            and type(execution["runtime_library_paths"]) is list, "historical admission command is not the recorded source worker")
    command = (str(python), "-I", "-B", str(root / WORKER))
    runtime.validate_process_record(receipt["process"], command=command, limits=_process_limits(request["limits"]),
        input_bytes=canonical(request), success_codes=(0,), runtime_library_paths=tuple(execution["runtime_library_paths"]))
    worker = bridge._decode(receipt["process"]["stdout"].encode(), MAX_METADATA, "historical admission worker")
    require(worker == receipt["worker_result"] and type(worker) is dict and set(worker) == {
            "schema", "status", "request_sha256", "producer", "manifest_sha256", "training_inputs", "training_plan",
            "checked_data", "evaluation_plan", "identity", "loaded_original_modules", "checks", *NO_WORK}
            and worker["schema"] == WORKER_SCHEMA and worker["status"] == "original-metadata-and-artifact-bytes-validated"
            and worker["request_sha256"] == digest(request) and worker["producer"] == ref.producer.to_dict()
            and worker["manifest_sha256"] == ref.manifest_sha256 and worker["training_inputs"] == ref.inputs.to_dict()
            and worker["training_plan"] == record["training_plan"] and worker["identity"] == _training_identity(record, ref)
            and all(worker[key] is False for key in NO_WORK), "worker did not retain the actual original validation result")
    plan = worker["training_plan"]
    require(plan["training_plan_sha256"] == PRODUCER_PLAN_SHA
            and digest({key: value for key, value in plan.items() if key != "training_plan_sha256"}) == PRODUCER_PLAN_SHA
            and plan["ancestor_origins"] == snapshot["ancestor_origins"]
            and plan["training_sources"]["training/peano_hydra/retention_training.py"] == PRODUCER_TRAINER_SHA
            and plan["training_sources"]["training/peano_hydra/retention_evaluation.py"] == PRODUCER_EVALUATION_SHA,
            "worker replaced the historical producer plan with the current evaluator")
    expected_checks = {name: True for name in ("original_source_before_after", "original_inputs_before_after",
        "model_bytes_before_after", "manifest_bytes_before_after", "genuine_bind_training",
        "complete_original_record_validation", "explicit_original_directory_verification",
        "original_training_sources_equal_plan", "source_only_original_imports", "no_forbidden_attempts")}
    require(worker["checks"] == expected_checks, "historical admission omitted an original validation or final byte guard")
    source, _ = training._record(ref.producer.source_manifest, PRODUCER_SOURCE_SHA, bridge.MAX_BUNDLE_MANIFEST_BYTES)
    modules = worker["loaded_original_modules"]
    require(type(modules) is dict and 1 <= len(modules) <= bridge.MAX_SOURCE_FILES,
            "historical worker has no bounded original-module inventory")
    for name, item in modules.items():
        require(type(name) is str and type(item) is dict and set(item) == {"path", "sha256"}
                and item["path"] in source["files"] and item["sha256"] == source["files"][item["path"]]["sha256"],
                "historical worker imported undeclared original bytes")
    for name in ("training.peano_hydra.retention_training", "training.peano_hydra.retention_evaluation",
                 "training.peano_policy.manifest", "scripts.execute_peano_hydra_retention"):
        require(name in modules, "historical worker omitted a required genuine original module")
    whole = receipt["whole_call"]
    require(type(whole) is dict and set(whole) == {"limits", "cpu_seconds", "wall_seconds", "parent_peak_rss_bytes",
        "conservative_combined_peak_rss_bytes", "measurement"} and whole["limits"] == LIMITS
        and whole["measurement"] == "parent and reaped children CPU; conservative sum of parent/worker peak RSS; through final checks",
        "historical admission whole-call accounting changed")
    for key, ceiling in (("cpu_seconds", LIMITS["cpu_seconds"]), ("wall_seconds", LIMITS["wall_seconds"]),
                         ("parent_peak_rss_bytes", LIMITS["rss_bytes"]),
                         ("conservative_combined_peak_rss_bytes", LIMITS["rss_bytes"])):
        require(type(whole[key]) in (int, float) and math.isfinite(whole[key]) and 0 <= whole[key] <= ceiling,
                "historical admission exceeded its whole-call metadata envelope")
    require(whole["cpu_seconds"] >= receipt["process"]["resources"]["cpu_seconds"]
            and whole["wall_seconds"] >= receipt["process"]["resources"]["wall_seconds"]
            and whole["conservative_combined_peak_rss_bytes"] >= max(whole["parent_peak_rss_bytes"],
                receipt["process"]["resources"]["peak_rss_bytes"]), "whole-call accounting omits the actual worker")
    return worker


def _custody_descriptor(value, *, maximum=MAX_METADATA):
    require(type(value) is dict and set(value) == {"path", "bytes", "sha256"}
            and type(value["path"]) is str and str(bridge._absolute(Path(value["path"]))) == value["path"]
            and type(value["bytes"]) is int and 0 < value["bytes"] <= maximum,
            "custody needs an exact bounded actual-file descriptor")
    training._sha(value["sha256"], "custody file")
    return value


def _matches_raw(descriptor, raw):
    _custody_descriptor(descriptor)
    require(len(raw) == descriptor["bytes"] and hashlib.sha256(raw).hexdigest() == descriptor["sha256"],
            "custody changed actual retained receipt bytes")


def _completed_invocation(invocation):
    require(type(invocation) is dict and set(invocation) == {"schema", "status", "mode", "source_commit", "argv",
            "exit_code", "helper", "owner_result", "output", "observed_from", "recorded_at_utc", "automatic_retry"}
            and invocation["schema"] == INVOCATION_SCHEMA and invocation["status"] == "exited"
            and invocation["mode"] == "authenticate-admission" and type(invocation["exit_code"]) is int
            and invocation["exit_code"] == 0 and invocation["automatic_retry"] is False
            and invocation["observed_from"] == "actual-tool-process-completion"
            and type(invocation["recorded_at_utc"]) is str and 20 <= len(invocation["recorded_at_utc"]) <= 40,
            "admission custody requires the externally observed successful owner exit")


def _validate_custody(custody):
    """Only a later custodian can join an actual completed owner invocation.

    A provisional admission retained after a late caller failure is never a
    candidate. The invocation bytes are a separately observed tool result,
    not a return-code constant manufactured by the still-running owner.
    """
    require(type(custody) is dict and set(custody) == {"schema", "status", "admission", "admission_file",
            "owner_result", "owner_result_file", "invocation_json", "invocation_file", "owner_helper",
            "owner_supervisor", "claim_boundary", *NO_WORK}
            and custody["schema"] == CUSTODY_SCHEMA and custody["status"] == "completed-caller-admission"
            and all(custody[key] is False for key in NO_WORK),
            "a bare provisional admission lacks mandatory completed-caller custody")
    require(type(custody["invocation_json"]) is str, "custody must preserve the actual invocation JSON bytes")
    invocation_raw = custody["invocation_json"].encode()
    _matches_raw(custody["invocation_file"], invocation_raw)
    invocation = bridge._decode(invocation_raw, MAX_METADATA, "actual owner invocation")
    _completed_invocation(invocation)
    owner, inner = custody["owner_result"], custody["admission"]
    _matches_raw(custody["owner_result_file"], canonical(owner) + b"\n")
    _matches_raw(custody["admission_file"], canonical(inner) + b"\n")
    helper, supervisor = _custody_descriptor(custody["owner_helper"]), _custody_descriptor(custody["owner_supervisor"])
    require(Path(helper["path"]).name == OWNER_HELPER
            and Path(supervisor["path"]).name == "run-v28-hotspots-supervised-v2.py"
            and supervisor["sha256"] == SUPERVISOR_SHA, "custody changed its reviewed external owner/supervisor")
    require(type(owner) is dict and owner.get("schema") == OWNER_SCHEMA and owner.get("status") == "passed"
            and owner.get("mode") == "authenticate-admission" and owner.get("helper") == helper
            and owner.get("supervisor") == supervisor and owner.get("source_unchanged") is True
            and owner.get("inputs_unchanged") is True and owner.get("source_before") == owner.get("source_after")
            and owner.get("output") == custody["admission_file"] and owner.get("error") is None
            and all(owner.get(key) is False for key in NO_WORK), "admission owner did not complete its actual final byte checks")
    require(type(owner["source_commit"]) is str and bridge._OID.fullmatch(owner["source_commit"])
            and owner["source_commit"] != PRODUCER_COMMIT, "custody relabels the corrected caller as the original producer")
    require(invocation["helper"] == helper and invocation["owner_result"] == custody["owner_result_file"]
            and invocation["output"] == custody["admission_file"] and invocation["source_commit"] == owner["source_commit"]
            and invocation["argv"] == owner["request"]["owner_argv"], "actual owner exit was not for this admission attempt")
    require(owner["admission_sources"] == inner["request"]["admission_sources"],
            "custody owner and historical metadata worker used different current source bytes")
    root = bridge._absolute(Path(inner["request"]["execution"]["source_root"]))
    python = inner["request"]["execution"]["python"]
    input_descriptor = _custody_descriptor(owner["input"])
    inner_path = Path(custody["admission_file"]["path"])
    require(input_descriptor["path"] == str(root / "_deploy/hydra-retention-evaluation-recovery-v1/admission-request.json")
            and inner_path.name == "admission.json" and owner["cli_command"] == [python, "-I", "-B", str(root / RECOVERY_CLI),
                "--authenticate-admission", "--inputs", input_descriptor["path"], "--expected-inputs-sha256",
                input_descriptor["sha256"], "--output", str(inner_path.parent)],
            "custody did not observe the actual unchanged admission CLI invocation")
    request_raw = canonical(owner["request"]) + b"\n"
    _matches_raw(owner["request_file"], request_raw)
    expected_command = [python, "-I", "-B", helper["path"], "--worker", "--request", owner["request_file"]["path"],
                        "--expected-request-sha256", owner["request_file"]["sha256"]]
    process = owner["supervision"]
    require(owner["command"] == expected_command and process["command"] == expected_command
            and process["schema"] == "peano-hydra-v28-hotspot-process-tree-supervision-v2"
            and process["status"] == "process-completed-with-open-gates" and process["reason"] == "exited"
            and type(process["returncode"]) is int and process["returncode"] == 0
            and process["remaining_live_owned_pids"] == [] and process["error"] is None
            and process["limits"]["cpu_seconds"] <= OWNER_LIMITS["cpu_seconds"]
            and process["limits"]["wall_seconds"] <= OWNER_LIMITS["wall_seconds"]
            and process["limits"]["rss_bytes"] == OWNER_LIMITS["rss_bytes"]
            and process["limits"]["output_bytes"] == OWNER_LIMITS["output_bytes"],
            "admission caller lacks actual successful quiescent bounded process completion")
    for name in ("cpu_seconds", "wall_seconds"):
        value = process["limits"][name]
        require(type(value) in (int, float) and math.isfinite(value) and 0.1 <= value <= OWNER_LIMITS[name],
                "custody process has an invalid original supervisor limit")
    cleanup = process["cleanup"]
    require(type(cleanup) is dict and cleanup.get("controller_reaped") is True and cleanup.get("errors") == []
            and cleanup.get("remaining_live_owned_pids") == [] and cleanup.get("remaining_zombie_owned_pids") == [],
            "custody caller did not finish its owned process cleanup")
    guard = owner["worker_guard"]
    _matches_raw(owner["worker_guard_file"], canonical(guard) + b"\n")
    require(guard.get("schema") == "peano-hydra-retention-recovery-cpu-guard-v1" and guard.get("status") == "passed"
            and guard.get("mode") == "authenticate-admission" and guard.get("original_cli_returncode") == 0
            and guard.get("cli_command") == owner["cli_command"] and guard.get("output") == custody["admission_file"]
            and guard.get("request_sha256") == owner["request_file"]["sha256"]
            and guard.get("admission_sources") == owner["admission_sources"] and guard.get("forbidden_attempts") == []
            and guard.get("allowed_subprocess_counts", {}).get("admission_worker") == 1
            and guard.get("cli_sha256") == owner["admission_sources"][RECOVERY_CLI]
            and guard.get("admission_worker_sha256") == owner["admission_sources"][WORKER]
            and all(guard.get(key) is False for key in NO_WORK), "actual admission CLI guard did not finish cleanly")
    stdout = canonical({key: custody["admission_file"][key] for key in ("path", "bytes", "sha256")})
    # The CLI prints json.dumps(sort_keys=True), including ordinary spaces.
    stdout = (json.dumps(json.loads(stdout), sort_keys=True, allow_nan=False) + "\n").encode()
    require(process["logs"]["stdout"] == {"bytes": len(stdout), "sha256": hashlib.sha256(stdout).hexdigest()},
            "actual CLI stdout did not return this exact provisional admission descriptor")
    accounting = owner["accounting"]
    require(type(accounting) is dict and accounting.get("limits") == OWNER_LIMITS
            and accounting.get("cpu_is_exact_aggregate") is False and accounting.get("rss_is_instantaneous_hard_cap") is False
            and accounting.get("whole_process_tree_quiescent") is True,
            "custody changed sampled accounting into a hard or exact resource claim")
    for key, maximum in (("cpu_seconds", OWNER_LIMITS["cpu_seconds"]), ("wall_seconds", OWNER_LIMITS["wall_seconds"]),
                         ("peak_rss_bytes", OWNER_LIMITS["rss_bytes"]), ("retained_bytes", OWNER_LIMITS["output_bytes"])):
        require(type(accounting.get(key)) in (int, float) and math.isfinite(accounting[key]) and 0 <= accounting[key] <= maximum,
                "completed admission owner exceeded its explicit outer envelope")
    require(accounting["cpu_seconds"] >= inner["whole_call"]["cpu_seconds"]
            and accounting["cpu_seconds"] >= process["accounted_cpu_lower_bound_seconds"]
            and accounting["wall_seconds"] >= process["wall_seconds"]
            and accounting["peak_rss_bytes"] >= process["peak_sampled_combined_rss_bytes"],
            "custody omits the admission worker or outer supervision tail")
    return inner


@dataclass(frozen=True, slots=True)
class HistoricalTrainingPlanRecord:
    """Saved producer evidence, deliberately not a current TrainingPlan."""
    _record_json: str
    _evaluation_json: str

    def to_dict(self):
        return json.loads(self._record_json)

    @property
    def evaluation_plan(self):
        return json.loads(self._evaluation_json)


@dataclass(frozen=True, slots=True)
class AuthenticatedPreservedRetentionArtifact:
    identity: dict
    adapter_directory: Path
    tokenizer_directory: Path
    checked_data: object
    manifest: dict
    plan: HistoricalTrainingPlanRecord

    def to_dict(self):
        return json.loads(canonical(self.identity))


def load_preserved_artifact(ref):
    """Rehash an externally pinned completed receipt; never run admission."""
    require(type(ref) is PreservedRetentionArtifactReference and ref.admission_receipt_path is not None
            and ref.admission_receipt_sha256 is not None,
            "a nullable historical admission draft cannot load an evaluation candidate")
    custody, raw = training._record(ref.admission_receipt_path, ref.admission_receipt_sha256)
    receipt = _validate_custody(custody)
    sources = admission_sources()
    snapshot, record, adapter, tokenizer = _snapshot(ref)
    worker = _validate_receipt(receipt, ref, snapshot, record, sources)
    from training.peano_hydra import retention_data
    checked = retention_data.load_preparation(ref.inputs.directory, expected_manifest_sha256=ref.inputs.manifest_sha256)
    evaluation, _ = training._record(ref.inputs.evaluation_plan_path, ref.inputs.evaluation_plan_sha256)
    require(checked.to_dict() == worker["checked_data"] and evaluation == worker["evaluation_plan"],
            "current explicit preparation or pretraining evaluation differs from the original validated bytes")
    after, after_record, _, _ = _snapshot(ref)
    require(after == snapshot and after_record == record and admission_sources() == sources
            and bridge._read(ref.admission_receipt_path, MAX_METADATA) == raw,
            "historical admission support or input bytes changed during receipt loading")
    identity = {**worker["identity"], "admission_receipt_sha256": ref.admission_receipt_sha256,
                "admission_sources": sources}
    return AuthenticatedPreservedRetentionArtifact(identity, adapter, tokenizer, checked, record,
        HistoricalTrainingPlanRecord(canonical(worker["training_plan"]).decode(), canonical(evaluation).decode()))


class _WholeCall:
    def __init__(self):
        self.started = time.monotonic()
        self.parent = resource.getrusage(resource.RUSAGE_SELF)
        self.children = resource.getrusage(resource.RUSAGE_CHILDREN)
        self.process = None

    def measure(self):
        parent, children = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
        cpu = parent.ru_utime + parent.ru_stime - self.parent.ru_utime - self.parent.ru_stime
        child_cpu = children.ru_utime + children.ru_stime - self.children.ru_utime - self.children.ru_stime
        observed = {} if self.process is None else self.process["resources"]
        cpu += max(child_cpu, observed.get("cpu_seconds", 0))
        peak = int(parent.ru_maxrss if sys.platform == "darwin" else parent.ru_maxrss * 1024)
        worker_peak = max(observed.get("peak_rss_bytes", 0), observed.get("sampled_peak_group_rss_bytes") or 0)
        return {"limits": dict(LIMITS), "cpu_seconds": cpu, "wall_seconds": time.monotonic() - self.started,
            "parent_peak_rss_bytes": peak, "conservative_combined_peak_rss_bytes": peak + worker_peak,
            "measurement": "parent and reaped children CPU; conservative sum of parent/worker peak RSS; through final checks"}

    def check(self):
        record = self.measure()
        require(record["cpu_seconds"] < LIMITS["cpu_seconds"] and record["wall_seconds"] < LIMITS["wall_seconds"]
                and record["conservative_combined_peak_rss_bytes"] <= LIMITS["rss_bytes"],
                "historical admission exhausted its separate whole-call metadata envelope")
        return record


def authenticate_admission(ref, output_directory):
    """One fresh attempt; returned inner receipt still needs completed custody."""
    require(type(ref) is PreservedRetentionArtifactReference and ref.admission_receipt_sha256 is None,
            "authentication requires an explicit nullable preserved-model draft")
    output = bridge._absolute(Path(output_directory))
    protected = (*ref.protected_paths(), ROOT / "training", ROOT / "scripts", ROOT / "peano-lab/py")
    files.guard_output(output, protected=protected)
    require(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0),
            "admission cannot replace an existing caller wall-time alarm")
    budget = _WholeCall()
    previous_handler = signal.getsignal(signal.SIGALRM)
    def deadline(*_):
        raise training.RetentionTrainingError("historical admission whole-call wall deadline")
    signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, LIMITS["wall_seconds"])
    parent, created = None, False
    try:
        parent = files.directory(output.parent)
        os.mkdir(output.name, 0o700, dir_fd=parent)
        created = True
        files.write_new(output / "start.json", {"schema": RECEIPT_SCHEMA + "-attempt", "status": "started",
            "candidate_reference": ref.to_dict(), "locations": ref.locations(), "limits": LIMITS, **NO_WORK})
        sources = admission_sources()
        before, record, _, _ = _snapshot(ref)
        measured = budget.check()
        # Reserve only what is left after input/source setup; original limit
        # constructors and all native proof limits are unchanged.
        remaining_cpu = math.floor(LIMITS["cpu_seconds"] - measured["cpu_seconds"])
        remaining_wall = math.floor(LIMITS["wall_seconds"] - measured["wall_seconds"])
        limits = _process_limits({**LIMITS, "cpu_seconds": min(remaining_cpu, remaining_wall), "wall_seconds": remaining_wall})
        from training.peano_hydra.helios_runtime import reviewed_runtime_library_paths
        libraries = reviewed_runtime_library_paths()
        python = str(Path(sys.executable).resolve(strict=True))
        request = {"schema": REQUEST_SCHEMA, "candidate_reference": ref.to_dict(), "locations": ref.locations(),
            "admission_sources": sources, "execution": {"source_root": str(ROOT), "python": python,
                "worker": str(ROOT / WORKER), "runtime_library_paths": list(libraries)}, "limits": limits.to_dict()}
        payload = canonical(request)
        require(len(payload) <= 1024**2, "historical admission request exceeds its bound")
        command = (python, "-I", "-B", str(ROOT / WORKER))
        process = runtime.run_bounded(command, cwd=ref.producer.source_root, limits=limits,
                                      input_bytes=payload, runtime_library_paths=libraries)
        budget.process = process
        files.write_new(output / "process.json", process)
        budget.check()
        runtime.validate_process_record(process, command=command, limits=limits, input_bytes=payload,
                                        success_codes=(0,), runtime_library_paths=libraries)
        after, after_record, _, _ = _snapshot(ref)
        require(before == after and record == after_record and sources == admission_sources(),
                "original source/model/input or current admission code changed during the worker")
        worker = bridge._decode(process["stdout"].encode(), MAX_METADATA, "historical admission worker")
        receipt = {"schema": RECEIPT_SCHEMA, "status": "passed-corrected-historical-admission",
            "request": request, "process": process, "worker_result": worker, "before": before, "after": after,
            "whole_call": budget.check(), "claim_boundary":
                "Completed original producer metadata plus saved artifact bytes; no model execution, proof, evaluation score or new training authority.",
            **NO_WORK}
        _validate_receipt(receipt, ref, after, record, sources)
        files.guard_output(output / "admission.json", protected=protected)
        receipt["whole_call"] = budget.check()
        raw = canonical(receipt) + b"\n"
        require(len(raw) <= MAX_METADATA, "corrected historical admission receipt exceeds its bound")
        files.write_new(output / "admission.json", raw, raw=True)
        budget.check()
        return {"path": str(output / "admission.json"), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    except BaseException as error:
        if created:
            # A failed attempt never publishes a usable new receipt after a
            # failure; any already written evidence stays immutable.
            files.write_new(output / "failure.json", {"schema": RECEIPT_SCHEMA + "-failure", "status": "failed",
                "error_type": type(error).__name__, "error": " ".join(str(error).split())[:2048],
                "whole_call": budget.measure(), "admission_result_must_not_be_used": True, **NO_WORK})
        raise
    finally:
        if parent is not None:
            os.close(parent)
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
