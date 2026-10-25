"""Pure admission of teacher exposure, distinct from the frozen tensor loader.

Importing this module never imports a native engine, model, tokenizer or trainer.
Only prepare_distilled_study.py may regenerate the sealed teacher dataset. Each
case rehashes that admission's complete evidence before using the unchanged P6
loader; its compatibility kind is not a claim about the training data.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import os
import re
import stat

from paired_common import (DATASET_SHA, EXPOSURE_FIELDS, HOLDOUT_SHA, PROVIDER_SHA,
    canonical, ordinary, require, strict_json, valid_sha, validate_exposure)

PROFILE = "hydra-fresh-teacher-augmented-pilot-v1"
PLAN_SCHEMA = "hydra-teacher-augmented-pilot-plan-v1"
DATA_SCHEMA = "hydra-teacher-augmented-primitive-dataset-v1"
ATTESTATION_SCHEMA = "hydra-teacher-augmented-data-attestation-v1"
ADMISSION_SCHEMA = "hydra-teacher-evaluation-admission-v1"
EXPOSURE_SCHEMA = "hydra-teacher-evaluation-exposure-v1"
PUBLIC_KIND = "teacher_augmented_pilot"
TENSOR_KIND = "fresh_decision_pilot"
MODEL = {"model_id": "Qwen/Qwen3-1.7B-Base", "revision": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"}
SELECTION_SHA = "26c09c2b28f54073f3964c4772113f7496eceb03107b356b892c619c9cc835d7"
FIXED_TEACHER = {
    "output/p7-prototype/distillation/teacher_data.py": "306b7d2aeee5d4599a9e880f9842cc3e3414cc69a2e80ed82dfd32f8b410d1bd",
    "output/p7-prototype/distillation/teacher_student_pilot.py": "0052f90448b163f6d87f89939459b09d2be88fc19b00c030f23cb4f53f38633d",
    "output/p7-prototype/distillation/remote_student_update.py": "11afed22a5635f21082678164dd81ac8e25fa4844d3898e9524dd2ce9faa6b82",
    "output/p7-prototype/distillation/teacher_replay.py": "24ae57e0548ec3b98369f7d14afc72d0ebafa6c5ad20d3c78a9c8c2fbcf43189",
    "hydra-playground/experimental_model.py": PROVIDER_SHA,
}
MAX_FILES = 2048
MAX_BYTES = 384 * 1024**2
MAX_FILE = 128 * 1024**2


def digest(value):
    return sha256(canonical(value)).hexdigest()


def descriptor(value):
    require(type(value) is dict and set(value) == {"path", "bytes", "sha256"}
            and type(value["path"]) is str and 0 < len(value["path"].encode()) <= 4096
            and not Path(value["path"]).is_absolute() and ".." not in Path(value["path"]).parts
            and Path(value["path"]).as_posix() == value["path"]
            and type(value["bytes"]) is int and 0 <= value["bytes"] <= MAX_FILE
            and valid_sha(value["sha256"]), "An exact ordinary project-relative input pin is required.")
    return value


class Evidence:
    """Bounded stable streaming hashes; no proof execution or deserialization."""
    def __init__(self, root, should_stop=None):
        self.root = Path(root).resolve(strict=True)
        self.should_stop, self.pins, self.total = should_stop, {}, 0

    def check(self):
        if self.should_stop is not None and self.should_stop():
            raise TimeoutError("Teacher evidence admission reached the unchanged load deadline.")

    def path(self, name):
        require(type(name) is str and name and not Path(name).is_absolute()
                and ".." not in Path(name).parts and Path(name).as_posix() == name,
                "Evidence paths must remain canonical and project relative.")
        path = self.root / name
        require(path.resolve(strict=True) == path, "Teacher evidence escaped through a symlink.")
        return path

    def read(self, value, *, keep=False):
        descriptor(value)
        self.check()
        name = value["path"]
        require(name not in self.pins or self.pins[name] == value, "Conflicting evidence pins.")
        fresh = name not in self.pins
        require(not fresh or (len(self.pins) < MAX_FILES and self.total + value["bytes"] <= MAX_BYTES),
                "Teacher evidence exceeds its file or total-byte ceiling.")
        path = self.path(name)
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        pieces = [] if keep else None
        h, size = sha256(), 0
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size == value["bytes"],
                    "Evidence must be a bounded single-link ordinary file.")
            while block := stream.read(1024**2):
                self.check()
                size += len(block)
                require(size <= value["bytes"], "Evidence grew while reading.")
                h.update(block)
                if keep:
                    pieces.append(block)
            held = os.fstat(stream.fileno())
        fields = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        require(fields(before) == fields(held) == fields(path.lstat()) and size == value["bytes"]
                and h.hexdigest() == value["sha256"], "Teacher evidence changed or has the wrong hash.")
        if fresh:
            self.pins[name], self.total = dict(value), self.total + size
        return None if not keep else b"".join(pieces)

    def json(self, value):
        require(value["bytes"] <= 4 * 1024**2, "Teacher JSON exceeds its finite metadata bound.")
        return strict_json(self.read(value, keep=True))


def teacher_training_exposure(record, fresh=None):
    require(type(record) is dict and record.get("schema") == "hydra-decision-pilot-artifact-v1"
            and record.get("profile") == PROFILE and record.get("model_trained") is True
            and record.get("resume") is False and record.get("automatic_retry") is False
            and record.get("saved_adapter_reload_admission") == "required_by_P6_before_inference",
            "Only a completed explicit teacher-augmented training artifact can enter this arm.")
    plan, data = record.get("plan", {}), record.get("plan", {}).get("data_attestation", {})
    require(plan.get("schema") == PLAN_SCHEMA and plan.get("profile") == PROFILE
            and plan.get("model") == record.get("model") == MODEL
            and plan.get("plan_sha256") == digest({k: v for k, v in plan.items() if k != "plan_sha256"})
            and plan.get("epochs") == 1 and plan.get("resume") is False and plan.get("automatic_retry") is False
            and plan.get("prompt_schema") == "primitive_v4" and plan.get("planner_rows_allowed") is False
            and plan.get("initialization") == "fresh_pinned_base_new_lora" and plan.get("model_trained") is False,
            "Teacher data must train the exact fresh 1.7B primitive student, not a renamed ordinary or resumed model.")
    require(data.get("schema") == ATTESTATION_SCHEMA and data.get("base_manifest_sha256") == DATASET_SHA
            and data.get("base_training_rows") == 2047 and data.get("holdout_sha256") == HOLDOUT_SHA
            and data.get("selection_sha256") == SELECTION_SHA
            and data.get("reserved_intermediate_check") == "exact_closed_AST_plus_declared_template_exclusions"
            and data.get("teacher_source_scope") == "complete_teacher_proposed_native_continuation"
            and all(data.get(k) is True for k in ("regenerated_byte_exact", "base_train_prefix_preserved", "validation_test_unchanged")),
            "Teacher selection, full replay, base-prefix preservation or reserved exclusions are not admitted.")
    added, continuations, calls = (data.get(k) for k in ("teacher_rows_added", "fresh_verified_continuations", "actual_teacher_model_calls"))
    require(type(added) is int and 1 <= added <= 2049 and plan.get("training_rows") == 2047 + added
            and data.get("training_rows") == plan["training_rows"]
            and data.get("validation_rows") == plan.get("validation_rows")
            and type(continuations) is int and 1 <= continuations <= 32
            and type(calls) is int and continuations <= calls <= 64
            and valid_sha(data.get("teacher_model_manifest_sha256"))
            and valid_sha(data.get("manifest_sha256")) and data["manifest_sha256"] != DATASET_SHA,
            "Empty/unknown teacher yield or incompatible exposure cannot authorize distillation evaluation.")
    require(type(record.get("actual_optimizer_steps")) is int
            and record["actual_optimizer_steps"] == plan.get("expected_optimizer_steps") == (plan["training_rows"] + 7) // 8,
            "The full augmented one-pass optimizer trace must be completed.")
    base = {name: plan[name] for name in EXPOSURE_FIELDS}
    base.update(dataset_sha256=data["manifest_sha256"], holdout_sha256=HOLDOUT_SHA, epochs=1,
        prompt_schema="primitive_v4", planner_rows_allowed=False, objective_sha256=digest(plan["objective"]))
    validate_exposure(base)
    extra = {"schema": EXPOSURE_SCHEMA, "model": MODEL, "plan_sha256": plan["plan_sha256"],
        "base_dataset_sha256": DATASET_SHA, "base_training_rows": 2047, "teacher_rows_added": added,
        "fresh_verified_continuations": continuations, "actual_teacher_model_calls": calls,
        "teacher_model_manifest_sha256": data["teacher_model_manifest_sha256"], "selection_sha256": SELECTION_SHA,
        "data_attestation_sha256": digest(data), "token_preflight_sha256": digest(record["token_preflight"]),
        "base_train_prefix_preserved": True, "validation_test_unchanged": True,
        "teacher_input_spec": data["teacher_input_spec"], "fresh_replay_manifest": data["fresh_replay_manifest"]}
    result = {**base, "teacher": extra}
    validate_teacher_exposure(result, fresh)
    return result


def validate_teacher_exposure(value, fresh=None):
    require(type(value) is dict and type(value.get("teacher")) is dict, "Explicit teacher exposure is required.")
    base = {k: v for k, v in value.items() if k != "teacher"}
    validate_exposure(base)
    t = value["teacher"]
    fields = {"schema", "model", "plan_sha256", "base_dataset_sha256", "base_training_rows", "teacher_rows_added",
        "fresh_verified_continuations", "actual_teacher_model_calls", "teacher_model_manifest_sha256", "selection_sha256",
        "data_attestation_sha256", "token_preflight_sha256", "base_train_prefix_preserved", "validation_test_unchanged",
        "teacher_input_spec", "fresh_replay_manifest"}
    require(set(t) == fields and t["schema"] == EXPOSURE_SCHEMA and t["model"] == MODEL
            and t["base_dataset_sha256"] == DATASET_SHA and t["selection_sha256"] == SELECTION_SHA
            and type(t["base_training_rows"]) is int and t["base_training_rows"] == 2047
            and type(t["teacher_rows_added"]) is int and 1 <= t["teacher_rows_added"] <= 2049
            and value["training_rows"] == 2047 + t["teacher_rows_added"]
            and type(t["fresh_verified_continuations"]) is int and 1 <= t["fresh_verified_continuations"] <= 32
            and type(t["actual_teacher_model_calls"]) is int
            and t["fresh_verified_continuations"] <= t["actual_teacher_model_calls"] <= 64
            and t["base_train_prefix_preserved"] is t["validation_test_unchanged"] is True
            and all(valid_sha(v) for k, v in t.items() if k.endswith("_sha256")),
            "Malformed or empty completed teacher exposure.")
    for key in ("teacher_input_spec", "fresh_replay_manifest"):
        ref = t[key]
        require(type(ref) is dict and {"path", "sha256"} <= set(ref) <= {"path", "sha256", "bytes"}
                and valid_sha(ref["sha256"]) and type(ref["path"]) is str and ref["path"],
                "Teacher source and fresh replay must retain their exact references.")
    if fresh is not None:
        validate_exposure(fresh)
        require(fresh["dataset_sha256"] == DATASET_SHA and fresh["training_rows"] == 2047
                and all(value[k] == fresh[k] for k in ("validation_rows", "validation_row_ids_sha256", "objective_sha256",
                    "holdout_sha256", "epochs", "prompt_schema", "planner_rows_allowed")),
                "The distilled student must share the baseline objective, validation and original data prefix.")


def validate_student_collection(observation, transport, raw_files, artifact):
    """Actual P6-style extracted collection, with P7's explicit completion schema."""
    exits = [transport[k] for k in ("actual_ssh_exit_code", "actual_exit_code") if k in transport]
    require(exits and all(type(v) is int and v == 0 for v in exits)
            and transport.get("owned_child_reaped") is True and transport.get("stop_reason") is None
            and transport.get("output_complete") is True and transport.get("automatic_retry") is False,
            "Actual successful reaped collection transport is required; unknown timeouts are not completion.")
    names = {"job/actual-process-exit.txt", "job/reservation.json", "job/reservation.json.claimed",
        "job/result/request.json", "job/result/completion.json", "job/result/prepared-plan.json",
        "job/result/token-preflight.json", "job/result/trained-artifact.json", "artifact/manifest.json"}
    require(set(raw_files) == names and observation.get("read_only") is True,
            "Complete ordinary P7 training collection files are required.")
    require("artifact/incomplete.json" not in observation.get("files", {}), "An incomplete student artifact cannot be admitted.")
    for name, raw in raw_files.items():
        row = observation.get("files", {}).get(name, {})
        require(type(raw) is bytes and row.get("stable") is True and row.get("complete_file") is True
                and row.get("bytes") == len(raw) and row.get("sha256") == sha256(raw).hexdigest(),
                "A training observation is partial, unstable or differs from its extracted bytes: " + name)
    require(raw_files["job/actual-process-exit.txt"].strip() == b"0", "Actual student process did not exit 0.")
    values = {name: strict_json(raw) for name, raw in raw_files.items() if name.endswith(".json") or name.endswith(".claimed")}
    r = values["job/reservation.json"]
    request, completion = values["job/result/request.json"], values["job/result/completion.json"]
    plan = artifact.get("plan", {})
    require(r.get("schema") == "hydra-p7-student-update-reservation-v1"
            and r.get("model_key") == "qwen3-1.7b-base" and r.get("uid") == 105923
            and r.get("account") == "plgccaiautore2026-gpu-gh200" and r.get("partition") == "plgrid-gpu-gh200"
            and all(type(r.get(k)) is int and r[k] == v for k, v in (("gpus", 1), ("nodes", 1), ("cpus", 8), ("memory_gib", 64)))
            and type(r.get("seconds")) is int and 300 <= r["seconds"] <= 7200 and r["seconds"] % 60 == 0
            and type(r.get("job_id")) is str and re.fullmatch(r"\d{1,20}", r["job_id"])
            and r.get("controller_sha256") == FIXED_TEACHER["output/p7-prototype/distillation/remote_student_update.py"],
            "Student completion is not the explicit owned P7 1.7B allocation.")
    query = observation.get("scheduler", {}).get("sacct", {})
    require(type(query.get("actual_exit_code")) is int and query["actual_exit_code"] == 0
            and query.get("stop_reason") is None and type(query.get("stdout_stderr")) is str
            and len(query["stdout_stderr"].encode()) <= 65536, "Successful raw terminal accounting is missing.")
    rows = [line.split("|") for line in query["stdout_stderr"].splitlines() if line.split("|", 1)[0] == r["job_id"]]
    require(len(rows) == 1 and len(rows[0]) == 14, "An exact allocation-level 14-column P6 sacct row is required.")
    row = rows[0]
    require(observation.get("job_id") == r["job_id"]
            and row[1:7] == [r["job_name"], "plgnasqret", r["account"], r["partition"], "COMPLETED", "0:0"]
            and row[7].isdigit() and row[8] == str(r["seconds"] // 60) and row[9] == "8",
            "Actual Slurm owner, limits or terminal completion differ from the student reservation.")
    allocated = {}
    for item in row[12].split(","):
        require("=" in item, "Malformed actual allocated resources.")
        key, value = item.split("=", 1)
        require(key not in allocated, "Duplicate actual allocated resource.")
        allocated[key] = value
    require(allocated.get("cpu") == "8" and allocated.get("node") == allocated.get("gres/gpu") == "1"
            and allocated.get("mem") in {"64G", "65536M"}, "Actual student resources differ.")
    require(request.get("schema") == "hydra-p7-student-update-request-v1" and request.get("profile") == PROFILE
            and request.get("reservation") == r
            and request.get("reservation_sha256") == sha256(raw_files["job/reservation.json"]).hexdigest()
            and digest(request.get("source_pins_before")) == r.get("source_pins_sha256")
            and request.get("source_pins_before") == completion.get("source_pins_after"),
            "Student request/source binding differs from the completed reservation.")
    claim = values["job/reservation.json.claimed"]
    require(claim.get("schema") == "hydra-p7-student-update-consumption-v1"
            and claim.get("job_id") == r["job_id"] and claim.get("nonce") == r.get("nonce")
            and claim.get("reservation_sha256") == request["reservation_sha256"]
            and claim.get("plan_sha256") == r.get("plan_sha256") and claim.get("dataset_sha256") == r.get("dataset_sha256")
            and claim.get("resume") is False and claim.get("automatic_retry") is False,
            "The actual one-use student reservation consumption is missing.")
    require(completion.get("schema") == "hydra-p7-student-update-completion-v1"
            and completion.get("profile") == PROFILE and completion.get("completed") is True
            and completion.get("error") is None and completion.get("sources_unchanged") is True
            and completion.get("actual_optimizer_steps") == completion.get("optimizer_callbacks_observed")
            == artifact.get("actual_optimizer_steps") == plan.get("expected_optimizer_steps")
            and completion.get("teacher_rows_added") == plan.get("data_attestation", {}).get("teacher_rows_added")
            and completion.get("base_rows_preserved") == 2047 and completion.get("resume") is False
            and completion.get("automatic_retry") is False, "Student completion is partial or inconsistent.")
    require(values["job/result/prepared-plan.json"] == plan
            and values["job/result/token-preflight.json"] == artifact.get("token_preflight")
            and values["job/result/trained-artifact.json"] == values["artifact/manifest.json"] == artifact
            and r.get("plan_sha256") == plan.get("plan_sha256")
            and r.get("config_sha256") == plan.get("config_sha256")
            and r.get("dataset_sha256") == plan.get("data_attestation", {}).get("manifest_sha256")
            and artifact.get("reservation", {}).get("job_id") == artifact.get("final_reservation", {}).get("job_id") == r["job_id"],
            "Saved artifact, actual token preflight and completed teacher plan disagree.")
    return {"job_id": r["job_id"], "actual_student_exit_code": 0, "actual_slurm_state": "COMPLETED",
        "actual_slurm_exit_code": "0:0", "allocated_seconds": r["seconds"], "elapsed_seconds": int(row[7]),
        "training_source_pins_sha256": r["source_pins_sha256"], "saved_tensor_reload_performed": False}


def validate_bound_dependencies(admission, dataset, record):
    """Require the full immutable evidence graph, not just an asserted admission flag."""
    inputs = {ref["path"]: ref for ref in admission["inputs"]}
    data_ref = descriptor(admission["teacher_dataset"])
    attestation = record["plan"]["data_attestation"]
    require(inputs.get(data_ref["path"]) == data_ref and data_ref["sha256"] == attestation["manifest_sha256"]
            and dataset.get("schema") == DATA_SCHEMA and dataset.get("status") == "complete"
            and dataset.get("training_allowed") is True and dataset.get("source_pins") == attestation.get("source_pins")
            and dataset.get("input_spec") == attestation["teacher_input_spec"]
            and dataset.get("fresh_replay_manifest") == attestation["fresh_replay_manifest"],
            "The complete teacher dataset is not bound to the actual regenerated training attestation.")
    dependencies = list(dataset["inputs"])
    parent = Path(data_ref["path"]).parent
    for name, item in dataset["files"].items():
        dependencies.append({"path": (parent / name).as_posix(), "bytes": item["bytes"], "sha256": item["sha256"]})
    for mapping in (record["plan"]["source_pins"], dataset["source_pins"]):
        for name, item in mapping.items():
            ref = inputs.get(name)
            require(ref is not None and ref["sha256"] == (item if type(item) is str else item["sha256"]),
                    "A teacher training/source dependency is absent from runtime admission.")
    require(dependencies and all(inputs.get(ref["path"]) == ref for ref in dependencies),
            "Teacher dataset input/replay/output dependencies were omitted or substituted.")


def verify_admission(root, reference, record, expected, *, should_stop=None):
    """Rehash a CPU-regenerated admission and every bound evidence file before load."""
    evidence = Evidence(root, should_stop)
    admission = evidence.json(reference)
    require(admission.get("schema") == ADMISSION_SCHEMA and admission.get("status") == "admitted_not_loaded"
            and admission.get("sealed_plan_regenerated_exactly") is True
            and admission.get("data_regenerated_byte_exact") is True
            and admission.get("native_proof_runs") == admission.get("model_calls") == 0
            and admission.get("tensor_reload_required") is True
            and admission.get("source_provider_sha256") == PROVIDER_SHA,
            "A complete separate teacher provenance admission is required before tensor loading.")
    exposure = teacher_training_exposure(record)
    require(exposure == expected == admission.get("teacher_exposure")
            and digest(record) == admission.get("artifact_canonical_sha256"),
            "The actual student manifest differs from its admitted teacher exposure.")
    inputs = admission.get("inputs")
    require(type(inputs) is list and 1 <= len(inputs) <= MAX_FILES
            and len({p["path"] for p in inputs}) == len(inputs), "Complete unique bounded teacher evidence is required.")
    for item in inputs:
        evidence.read(item)
    require(digest(inputs) == admission.get("inputs_sha256"), "Teacher input graph identity differs.")
    dataset = evidence.json(admission["teacher_dataset"])
    validate_bound_dependencies(admission, dataset, record)
    for name, expected_sha in FIXED_TEACHER.items():
        require(evidence.pins.get(name, {}).get("sha256") == expected_sha, "Sealed teacher/provider source pin is absent or changed.")
    require(admission.get("admission_source_sha256") == sha256(ordinary(__file__)).hexdigest(),
            "Teacher exposure admission implementation changed.")
    collection = admission.get("training_collection", {})
    observation, transport = evidence.json(collection["observation"]), evidence.json(collection["transport"])
    raw_files = {name: evidence.read(ref, keep=True) for name, ref in collection["files"].items()}
    require(validate_student_collection(observation, transport, raw_files, record) == admission.get("actual_training_completion"),
            "Bound actual student completion differs from the teacher admission.")
    return {"public_adapter_kind": PUBLIC_KIND, "tensor_loader_contract": TENSOR_KIND,
        "teacher_admission_sha256": reference["sha256"], "teacher_exposure": exposure,
        "rehash_files": len(evidence.pins), "rehash_bytes": evidence.total,
        "teacher_evidence_sent_to_search": False, "provider_identity_modified": False}
