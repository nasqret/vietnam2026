"""Prepare one explicit teacher study after actual teacher/student completion.

This command performs CPU dataset/plan regeneration using the sealed P7 code.
It must be run under the root's separately scheduled bounded metadata guard.
It never trains, loads a model, executes a proof, reads the reserved cases or
contacts a scheduler. Importing the module is pure; no admission happens here.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import importlib
from pathlib import Path
import sys

from paired_common import (FEATURES, HOLDOUT_SHA, MODEL_LIMITS, RESOURCE_LIMITS, WALL_PROFILES,
    canonical, ordinary, pin, require, save, search_settings, source_pins, strict_json,
    study_spec, training_exposure, validate_arm)
from paired_controller import SLICE_SHA
from teacher_exposure import (ADMISSION_SCHEMA, FIXED_TEACHER, MODEL, PUBLIC_KIND, Evidence,
    descriptor, digest, teacher_training_exposure, validate_student_collection)
import teacher_exposure


def add_path(evidence, relative, expected=None):
    path = evidence.path(relative)
    item = {"path": relative, **pin(path, 128 * 1024**2)}
    require(expected is None or item["sha256"] == (expected if type(expected) is str else expected["sha256"]),
            "An admitted source or data byte identity changed: " + relative)
    if type(expected) is dict and "bytes" in expected:
        require(item["bytes"] == expected["bytes"], "An admitted file size changed.")
    evidence.read(item)
    return item


def prepare(app, specification, specification_sha, output):
    app = Path(app).resolve(strict=True)
    root = app.parent
    require(Path(__file__).resolve().is_relative_to(root), "Preparation must run inside the new derived source root.")
    before = source_pins(app)
    spec_raw = ordinary(specification, 128 * 1024)
    require(sha256(spec_raw).hexdigest() == specification_sha, "Explicit teacher study choice changed.")
    choice = strict_json(spec_raw)
    fields = {"schema", "study_id", "wall_profile", "fresh_arm", "distilled_arm", "fresh_manifest",
        "student_manifest", "student_config", "teacher_dataset", "training_collection", "training_source_root"}
    require(set(choice) == fields and choice["schema"] == "hydra-teacher-paired-choice-v1"
            and choice["wall_profile"] in WALL_PROFILES, "Bind actual evidence and one explicit wall profile first.")
    validate_arm("fresh_1_7b", choice["fresh_arm"])
    validate_arm("distilled_1_7b", choice["distilled_arm"])
    evidence = Evidence(root)
    for ref in (choice["fresh_manifest"], choice["student_manifest"], choice["student_config"], choice["teacher_dataset"]):
        descriptor(ref)
    fresh_record = evidence.json(choice["fresh_manifest"])
    artifact = evidence.json(choice["student_manifest"])
    require(choice["fresh_manifest"]["sha256"] == choice["fresh_arm"]["adapter_manifest_sha256"]
            and choice["student_manifest"]["sha256"] == choice["distilled_arm"]["adapter_manifest_sha256"]
            and fresh_record.get("model") == fresh_record.get("plan", {}).get("model") == MODEL,
            "The saved manifests must be the declared matching 1.7B models.")
    fresh = training_exposure(fresh_record)
    exposure = teacher_training_exposure(artifact, fresh)
    collection = choice["training_collection"]
    require(type(collection) is dict and set(collection) == {"observation", "transport", "files"}
            and type(collection["files"]) is dict, "An exact extracted student collection is required.")
    observation, transport = evidence.json(collection["observation"]), evidence.json(collection["transport"])
    raw_files = {name: evidence.read(ref, keep=True) for name, ref in collection["files"].items()}
    actual = validate_student_collection(observation, transport, raw_files, artifact)
    require(observation["files"]["artifact/manifest.json"]["sha256"] == choice["student_manifest"]["sha256"],
            "The selected artifact is not the actual collected saved manifest.")
    request = strict_json(raw_files["job/result/request.json"])
    training_root = Path(choice["training_source_root"])
    require(training_root.is_absolute()
            and request["config"] == str(training_root / choice["student_config"]["path"])
            and request["dataset_manifest"] == str(training_root / choice["teacher_dataset"]["path"]),
            "Actual training did not consume the declared config and teacher dataset.")
    for name, expected in FIXED_TEACHER.items():
        add_path(evidence, name, expected)
    for name in ("teacher_data", "teacher_student_pilot", "remote_student_update"):
        loaded = sys.modules.get(name)
        expected = root / "output/p7-prototype/distillation" / (name + ".py")
        require(loaded is None or Path(loaded.__file__).resolve() == expected,
                "A different teacher admission module is already loaded.")
    sys.path.insert(0, str(root / "output/p7-prototype/distillation"))
    teacher_data = importlib.import_module("teacher_data")
    require(teacher_data.ROOT == root, "Sealed teacher admission selected the wrong workspace.")
    pilot = importlib.import_module("teacher_student_pilot")
    update = importlib.import_module("remote_student_update")
    evidence.read(choice["student_config"])
    dataset = evidence.json(choice["teacher_dataset"])
    plan = pilot.prepare(evidence.path(choice["student_config"]["path"]),
        dataset_manifest=evidence.path(choice["teacher_dataset"]["path"]),
        dataset_sha256=choice["teacher_dataset"]["sha256"])
    require(plan.record == artifact["plan"], "The actual teacher training plan does not regenerate exactly.")
    require(update.source_pins() == request["source_pins_before"],
            "Actual student source map differs from the unchanged sealed training implementation.")
    require(dataset["source_pins"] == teacher_data.source_pins()
            and dataset["base_rows_preserved"] == 2047 and dataset["teacher_rows_added"] > 0
            and dataset["schema"] == teacher_exposure.DATA_SCHEMA,
            "Regenerated teacher data lost its explicit nonempty base-preserving contract.")
    for item in dataset["inputs"]:
        evidence.read(item)
    directory = Path(choice["teacher_dataset"]["path"]).parent
    for name, item in dataset["files"].items():
        add_path(evidence, (directory / name).as_posix(), item)
    for mapping in (before, request["source_pins_before"], plan.record["source_pins"], dataset["source_pins"]):
        for name, item in mapping.items():
            add_path(evidence, name, item)
    require(source_pins(app) == before, "Executed metadata admission source changed.")
    output = Path(output).absolute()
    require(output.resolve() == output and output.is_relative_to(root) and not output.exists(),
            "Use a fresh ordinary output directory inside the new derived source root.")
    output.mkdir(parents=True, exist_ok=False)
    inputs = sorted(evidence.pins.values(), key=lambda v: v["path"])
    admission = {"schema": ADMISSION_SCHEMA, "status": "admitted_not_loaded",
        "artifact_canonical_sha256": digest(artifact), "artifact_manifest": choice["student_manifest"],
        "teacher_dataset": choice["teacher_dataset"],
        "teacher_exposure": exposure, "fresh_training_exposure": fresh,
        "sealed_plan_regenerated_exactly": True, "data_regenerated_byte_exact": True,
        "training_collection": collection, "actual_training_completion": actual,
        "inputs": inputs, "inputs_sha256": digest(inputs),
        "admission_source_sha256": sha256(ordinary(teacher_exposure.__file__)).hexdigest(),
        "source_provider_sha256": teacher_exposure.PROVIDER_SHA,
        "preparation_source_pins_sha256": digest(before), "choice_sha256": specification_sha,
        "tensor_reload_required": True, "native_proof_runs": 0, "model_calls": 0,
        "reserved_cases_parsed": False, "training_performed": False, "automatic_retry": False}
    save(output / "admission.json", admission)
    admission_ref = {"path": (output / "admission.json").relative_to(root).as_posix(), **pin(output / "admission.json")}
    study = {"schema": "hydra-p7-teacher-paired-study-v1", "study_id": choice["study_id"], "scope": "paired5",
        "comparison": "fixed_native_work_guarded" if choice["wall_profile"] == "guarded-work-60-v1" else "fixed_wall_slice",
        "wall_profile": choice["wall_profile"], "holdout_sha256": HOLDOUT_SHA, "slice_sha256": SLICE_SHA,
        "source_pins_sha256": digest(before), "arms": {"fresh_1_7b": choice["fresh_arm"], "distilled_1_7b": choice["distilled_arm"]},
        "features": FEATURES, "native_work": search_settings(choice["wall_profile"]), "model_limits": MODEL_LIMITS,
        "resource_limits": RESOURCE_LIMITS, "fresh_training_exposure": fresh, "distilled_training_exposure": exposure,
        "teacher_admission": admission_ref, "training_allowed": False, "retrieval_allowed": False,
        "automatic_retry": False, "resume": False}
    study_spec(study, SLICE_SHA)
    save(output / "study.json", study)
    save(output / "preparation.json", {"schema": "hydra-teacher-study-preparation-v1", "status": "prepared_not_executed",
        "study": {"path": (output / "study.json").relative_to(root).as_posix(), **pin(output / "study.json")},
        "admission": admission_ref, "source_pins_sha256": digest(before), "model_loaded": False,
        "guarded_baseline_reuse_requires_separate_complete_original_arm_audit": True})
    return study


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-root", type=Path, required=True)
    parser.add_argument("--choice", type=Path, required=True)
    parser.add_argument("--choice-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.app_root, args.choice, args.choice_sha256, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
