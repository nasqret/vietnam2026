"""Derive one source bundle with only the diagnosed JSON comparison correction.

This is bounded file/AST work. It imports no application, tokenizer, model or
native engine; it cannot submit, upload, train, resume or recover an artifact.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import resource
import signal
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = HERE / "p6-source-bundle-06"
OUT = HERE / "p6-source-bundle-07"
REPLACEMENT = ROOT / "output/p6-serialization-v1/remote_training_pilot.py"
TRAINER = "output/p6-prototype/remote_training_pilot.py"
OLD_MANIFEST = "e1f5518231eaa04469d39c830bd480ec11ff4ed891907772d48aeab67da18f96"
OLD_COMPLETION = "510fd1e3f1871e59f98c16e362bac9a88dd77bb860e9a6c991b9d959e616cb9f"
OLD_SEAL = "fe2b602d75c6e2c9a3227bdfc7783717ea6cc546407b1614211322f17071e79b"
OLD_LAUNCH = "6ae22bd1075f7e83ad1ff427dbe468eeb5e38f30619e98ea7fcc71d48aae6e88"
HELPER_SHA = "1c22c1a48ab0f647da5565fd8776c383480be0381e4eb4a254c45862cfe72b99"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replacement-sha256", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{64}", args.replacement_sha256):
        raise ValueError("An exact reviewed replacement hash is required.")
    resource.setrlimit(resource.RLIMIT_CPU, (60, 75))
    resource.setrlimit(resource.RLIMIT_FSIZE, (128 * 1024**2, 128 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.alarm(120)
    started = time.monotonic()
    helper_path = HERE / "build_p6_bundle_06.py"
    if hashlib.sha256(helper_path.read_bytes()).hexdigest() != HELPER_SHA:
        raise ValueError("The preserved metadata/file helper changed.")
    spec = importlib.util.spec_from_file_location("_hydra_bundle_file_helpers", helper_path)
    b = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b)
    b.OLD, b.OUT, b.SOURCE = OLD, OUT, OUT / "source"
    b.CHANGES = {TRAINER: (REPLACEMENT, args.replacement_sha256)}
    require, canonical, descriptor = b.require, b.canonical, b.descriptor
    require(not OUT.exists(), "Refusing to overwrite this source revision.")
    for name, expected in (("manifest.json", OLD_MANIFEST), ("actual-completion.json", OLD_COMPLETION),
                           ("local-seal.json", OLD_SEAL), ("training-launch-inputs.json", OLD_LAUNCH)):
        require(descriptor(OLD / name)["sha256"] == expected, "Preserved bundle metadata changed: " + name)
    old = json.loads((OLD / "manifest.json").read_bytes())
    actual = json.loads((OLD / "actual-completion.json").read_bytes())
    require(actual["actual_exit_code"] == 0 and actual["completed"] is True,
            "The predecessor build did not complete.")
    old_files = b.inventory(OLD / "source")
    require(old_files == old["files"] and len(old_files) == 1206, "Original source inventory changed.")
    require(descriptor(OLD / "source-data.tar.gz") ==
            {"bytes": old["archive_bytes"], "sha256": old["archive_sha256"]}, "Original archive changed.")
    replacement_pin = descriptor(REPLACEMENT)
    require(replacement_pin["sha256"] == args.replacement_sha256, "Reviewed correction changed.")
    before = (OLD / "source" / TRAINER).read_text()
    after = REPLACEMENT.read_text()
    old_check = 'require(disk == artifact, "Returned training artifact differs from the saved manifest.")'
    new_check = 'require(canonical(disk) == canonical(artifact), "Returned training artifact differs from the saved manifest.")'
    require(before.count(old_check) == after.count(new_check) == 1, "Exact diagnosed comparison is missing.")
    reverted = after.replace(new_check, old_check)
    require(ast.dump(ast.parse(reverted), include_attributes=False) ==
            ast.dump(ast.parse(before), include_attributes=False), "Executable source differs beyond the one comparison.")
    old_scope = json.loads((OLD / "controller-source-pins.json").read_bytes())
    require(hashlib.sha256(canonical(old_scope)).hexdigest() == old["controller_source_pins_sha256"]
            and len(old_scope) == 585 and all(old_files[name] == value for name, value in old_scope.items()),
            "Original controller map changed.")
    OUT.mkdir(mode=0o700)
    b.SOURCE.mkdir(mode=0o700)
    for name in old_files:
        relative = Path(name)
        require(not relative.is_absolute() and ".." not in relative.parts and relative.as_posix() == name,
                "Noncanonical source path.")
        incoming = REPLACEMENT if name == TRAINER else OLD / "source" / name
        target = b.SOURCE / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with incoming.open("rb") as src, target.open("xb") as dst:
            while block := src.read(b.BLOCK):
                dst.write(block)
        target.chmod(0o444)
    files = b.inventory(b.SOURCE)
    require(set(files) == set(old_files) and
            {name for name in files if files[name] != old_files[name]} == {TRAINER}, "Unexpected payload change.")
    require(files[TRAINER] == replacement_pin, "Copied controller differs.")
    scope = {name: files[name] for name in old_scope}
    scope_sha = hashlib.sha256(canonical(scope)).hexdigest()
    b.save("controller-source-pins.json", scope)
    old_launch = json.loads((OLD / "training-launch-inputs.json").read_bytes())
    models = b.preserve_plans(files, old_launch)
    with (OUT / "source-data.tar.gz").open("xb") as stream:
        archive = b.archive(files, stream)
    require(archive == b.archive(files), "Deterministic archive regeneration differed.")
    b.verify_archive(files)
    zero_work = {"application_modules_imported": 0, "model_calls": 0, "tokenizers_loaded": 0,
                 "native_proof_replays": 0, "native_parsing_for_exclusions": False,
                 "training_performed": False, "automatic_launch": False,
                 "automatic_retry": False, "gpu_allocations": 0, "uploads": 0}
    source_check = {"method": "exact file inventory and complete AST equality after reverting one comparison",
                    "only_changed_paths": [TRAINER], "controller_source_files": 585,
                    "strict_json_decode_preserved": True, "post_save_validation_preserved": True,
                    "training_module_and_objective_unchanged": True}
    manifest = {"schema": "hydra-exact-source-data-bundle-v3", **archive,
        "file_count": len(files), "expanded_bytes": sum(row["bytes"] for row in files.values()), "files": files,
        "derived_from": {"path": OLD.relative_to(ROOT).as_posix(), "manifest_sha256": OLD_MANIFEST,
                         "actual_completion_sha256": OLD_COMPLETION, "unchanged_files": len(files) - 1},
        "changed_files": {TRAINER: {"before": old_files[TRAINER], "after": files[TRAINER],
                                    "replacement_source": REPLACEMENT.relative_to(ROOT).as_posix()}},
        "added_files": {}, "removed_files": [], "provider_sha256": b.PROVIDER_SHA,
        "provider_profile": "hydra-experimental-torch-qwen3-v2", "runner_sha256": b.SMOKE_SHA,
        "training_controller_sha256": args.replacement_sha256, "controller_source_pins_sha256": scope_sha,
        "source_contract_check": source_check, "dataset_manifest_sha256": b.DATA_SHA,
        "prepared_plans": descriptor(OUT / "prepared-plans.json", with_path=True),
        "prepared_plan_files_byte_identical_to_bundle06": True,
        "preparation_mode": "serialized_artifact_comparison_revision", **zero_work}
    b.save("manifest.json", manifest)
    launch = copy.deepcopy(old_launch)
    launch.update(preparation_mode="serialized_artifact_comparison_revision",
        archive=descriptor(OUT / "source-data.tar.gz", with_path=True),
        bundle_manifest=descriptor(OUT / "manifest.json", with_path=True),
        training_controller_sha256=args.replacement_sha256, source_pins_sha256=scope_sha, models=models,
        derived_from_bundle_completion=descriptor(OLD / "actual-completion.json", with_path=True),
        prepared_plan_files_byte_identical_to_bundle06=True)
    b.save("training-launch-inputs.json", launch)
    require(b.inventory(OLD / "source") == old_files and b.inventory(b.SOURCE) == files,
            "Original or derived source changed during build.")
    require(descriptor(REPLACEMENT) == replacement_pin, "Reviewed correction changed during build.")
    result = {"schema": "hydra-json-comparison-derived-bundle-build-v1", "completed": True,
        "original_bundle06_unchanged": True, "only_one_payload_file_changed": True,
        "prepared_plan_files_byte_identical_to_bundle06": True, "source_contract_check": source_check,
        "archive": archive, "manifest": descriptor(OUT / "manifest.json", with_path=True),
        "verified_source_files": len(files), "expanded_bytes": manifest["expanded_bytes"],
        "launch_inputs": descriptor(OUT / "training-launch-inputs.json", with_path=True),
        "controller_source_pins_sha256": scope_sha, "builder": descriptor(Path(__file__).resolve(), with_path=True),
        "elapsed_seconds": time.monotonic() - started, **zero_work}
    b.save("build-result.json", result)
    for path in b.SOURCE.rglob("*"):
        if path.is_dir():
            path.chmod(0o555)
    b.SOURCE.chmod(0o555)
    signal.alarm(0)
    print(json.dumps({"completed": True, "sealed": False, "pending": "actual tool completion and local seal",
                      "file_count": len(files), "expanded_bytes": manifest["expanded_bytes"], **archive,
                      "manifest_sha256": descriptor(OUT / "manifest.json")["sha256"],
                      "launch_inputs_sha256": descriptor(OUT / "training-launch-inputs.json")["sha256"],
                      "controller_source_pins_sha256": scope_sha,
                      "training_controller_sha256": args.replacement_sha256}), flush=True)


if __name__ == "__main__":
    main()
