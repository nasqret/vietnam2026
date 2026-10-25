"""Derive bundle05 and three source-rebound plans; standard-library files only.

No app/native imports, source execution, data admission, tokenization, model,
solver, scheduler, upload, or training operation is performed by this builder.
"""
from __future__ import annotations

import ast
import copy
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import resource
import signal
import stat
import sys
import tarfile
import time
import zlib

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / "output/hydra-implementation-2026-09-04/p6-source-bundle-04"
OUT = ROOT / "output/hydra-implementation-2026-09-04/p6-source-bundle-05"
SOURCE = OUT / "source"
MANIFEST_SHA = "613a32e58b41e4ff1047b7da89b576fcc5c9afcb31137011de980f2f93e207f9"
OLD_RECEIPT_SHA = "a216026780bce63edb80f72fa618dac2858ed0936c76476de89ce709088a80a2"
DATA_SHA = "e575970df58d046735f492acaf22e1cdea44445608a201c62d0644590b95ea77"
OLD_PROVIDER_SHA = "b5b85ed8bba6b0e6cdda4c7772443c5fec630a5643deba7d53598bcdd0cf9598"
PROVIDER_SHA = "7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f"
SMOKE_SHA = "267e150ec3f1a432cb5c36a1864bbf1735d2866a04224cd654ae6c533f469bb4"
TRAINER_SHA = "f4d04c01037d50bf90fc356706fc525bc6f1ee800b84ffc80db4a0d693dc65ed"
PROVIDER = "hydra-playground/experimental_model.py"
SMOKE = "output/p6-prototype/remote_provider_smoke.py"
TRAINER = "output/p6-prototype/remote_training_pilot.py"
CHANGES = {
    PROVIDER: (ROOT / PROVIDER, PROVIDER_SHA),
    SMOKE: (ROOT / "output/p6-provider-v2/remote_provider_smoke.py", SMOKE_SHA),
    TRAINER: (ROOT / "output/p6-provider-v2/remote_training_pilot.py", TRAINER_SHA),
}
BLOCK = 1024**2
MAX_BYTES = 128 * BLOCK
MODELS = ("qwen3-1.7b-base", "qwen3-4b-base", "qwen3-8b-base")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def descriptor(path, *, with_path=False):
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= MAX_BYTES
            and path.resolve(strict=True) == path, "Nonordinary/oversized source: " + str(path))
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(BLOCK):
            size += len(chunk)
            require(size <= MAX_BYTES, "File exceeded its byte ceiling while read.")
            digest.update(chunk)
    after = path.lstat()
    require(all(getattr(before, key) == getattr(after, key)
                for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns")) and size == before.st_size,
            "File changed while read: " + str(path))
    result = {"bytes": size, "sha256": digest.hexdigest()}
    if with_path:
        result["path"] = path.relative_to(ROOT).as_posix()
    return result


def save(name, value):
    raw = canonical(value) + b"\n"
    require(len(raw) <= 4 * BLOCK, "Metadata exceeded its byte ceiling.")
    with (OUT / name).open("xb") as stream:
        stream.write(raw)


def inventory(root):
    result = {}
    total = 0
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), "Symlink appeared in frozen payload.")
        if path.is_dir():
            continue
        result[path.relative_to(root).as_posix()] = value = descriptor(path)
        total += value["bytes"]
        require(len(result) <= 1300 and total <= MAX_BYTES, "Payload exceeded its finite scope.")
    return result


def literal(tree, name):
    values = [node.value for node in tree.body if isinstance(node, ast.Assign)
              and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
              and node.targets[0].id == name]
    require(len(values) == 1, "Missing/ambiguous source literal: " + name)
    return ast.literal_eval(values[0])


def executable_bodies(tree):
    return {node.name: ast.dump(node, include_attributes=False) for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}


def source_contracts(files, old_files, old_scope):
    old_trainer = ast.parse((OLD / "source" / TRAINER).read_bytes())
    trainer = ast.parse((SOURCE / TRAINER).read_bytes())
    old_smoke = ast.parse((OLD / "source" / SMOKE).read_bytes())
    smoke = ast.parse((SOURCE / SMOKE).read_bytes())
    require(executable_bodies(trainer) == executable_bodies(old_trainer)
            and executable_bodies(smoke) == executable_bodies(old_smoke),
            "A wrapper function/class changed beyond the approved source-binding revision.")
    require(literal(smoke, "PROVIDER_SHA") == PROVIDER_SHA
            and literal(trainer, "SMOKE_SHA") == SMOKE_SHA, "Adjacent helper/provider pins disagree.")
    fixed = literal(trainer, "FIXED_SOURCES")
    expected_fixed = literal(old_trainer, "FIXED_SOURCES")
    expected_fixed["experimental_model.py"] = PROVIDER_SHA
    require(fixed == expected_fixed and literal(trainer, "MODELS") == literal(old_trainer, "MODELS"),
            "Training fixed scope or model revision changed.")
    names = {"hydra-playground/" + name for name in fixed} | {SMOKE, TRAINER}
    names.update(name for name in files if name.endswith(".py") and name.startswith(
        ("hydra-playground/native-v7/peano_lab/", "hydra-playground/training-v5/hydra_training_v5/")))
    require(names == set(old_scope) and 100 <= len(names) <= 1024,
            "Source inventory escaped the preserved controller scope.")
    scope = {name: files[name] for name in sorted(names)}
    require(sum(row["bytes"] for row in scope.values()) <= 32 * BLOCK
            and all(row["bytes"] <= 4 * BLOCK for row in scope.values()), "Controller source scope is oversized.")
    for name, expected in fixed.items():
        require(scope["hydra-playground/" + name]["sha256"] == expected, "Fixed controller source mismatch: " + name)
    require({name for name in scope if scope[name] != old_scope[name]} == set(CHANGES),
            "Controller source map changed beyond the three reviewed files.")
    return scope, {"method": "static AST/literal validation and exact file-inventory reconstruction",
                   "application_modules_imported": 0, "controller_function_executed": False,
                   "all_wrapper_function_class_bodies_unchanged": True,
                   "controller_source_files": len(scope), "only_changed_paths": sorted(CHANGES)}


class HashWriter:
    def __init__(self, target=None):
        self.target, self.hash, self.bytes = target, hashlib.sha256(), 0

    def write(self, raw):
        self.bytes += len(raw)
        require(self.bytes <= MAX_BYTES, "Archive stream exceeded its byte bound.")
        self.hash.update(raw)
        if self.target is not None:
            self.target.write(raw)
        return len(raw)

    def flush(self):
        if self.target is not None:
            self.target.flush()


def archive(files, destination=None):
    compressed = HashWriter(destination)
    with gzip.GzipFile(filename="", mode="wb", fileobj=compressed, mtime=0, compresslevel=9) as gz:
        uncompressed = HashWriter(gz)
        with tarfile.open(fileobj=uncompressed, mode="w|", format=tarfile.PAX_FORMAT) as tar:
            for name, value in files.items():
                item = tarfile.TarInfo(name)
                item.size, item.mode, item.mtime = value["bytes"], 0o444, 0
                item.uid = item.gid = 0
                item.uname = item.gname = ""
                with (SOURCE / name).open("rb") as incoming:
                    tar.addfile(item, incoming)
    return {"archive_bytes": compressed.bytes, "archive_sha256": compressed.hash.hexdigest(),
            "tar_bytes": uncompressed.bytes, "tar_sha256": uncompressed.hash.hexdigest()}


def verify_archive(files):
    seen = {}
    with tarfile.open(OUT / "source-data.tar.gz", "r|gz") as tar:
        for item in tar:
            require(item.isfile() and item.name in files and item.name not in seen
                    and item.mode == 0o444 and item.uid == item.gid == item.mtime == 0
                    and item.uname == item.gname == "", "Archive type, path or metadata mismatch.")
            require(item.size == files[item.name]["bytes"], "Archive member size mismatch.")
            digest = hashlib.sha256()
            size = 0
            with tar.extractfile(item) as stream:
                while chunk := stream.read(BLOCK):
                    size += len(chunk)
                    digest.update(chunk)
            seen[item.name] = {"bytes": size, "sha256": digest.hexdigest()}
    require(seen == files, "Archive omitted or changed a payload file.")


def rebind_plans(files, old_files):
    old_plans_raw = (OLD / "prepared-plans.json").read_bytes()
    old_plans = json.loads(old_plans_raw)
    require(old_plans.get("completed") is True and old_plans.get("payload_unchanged") is True
            and old_plans["dataset_manifest_sha256"] == DATA_SHA, "Original native data-admission gate was incomplete.")
    result = {}
    for key in MODELS:
        filename = "prepared-" + key + ".json"
        old_descriptor = old_plans["plans"][key]["prepared_plan"]
        require(descriptor(OLD / filename) == {name: old_descriptor[name] for name in ("bytes", "sha256")},
                "An original prepared-plan pin changed.")
        plan = json.loads((OLD / filename).read_bytes())
        old_plan = copy.deepcopy(plan)
        require(hashlib.sha256(canonical({k: v for k, v in plan.items() if k != "plan_sha256"})).hexdigest()
                == plan["plan_sha256"], "Original plan does not match its canonical content hash.")
        require(plan["schema"] == "hydra-decision-pilot-plan-v2" and plan["profile"] == "hydra-fresh-decision-pilot-v2"
                and plan["training_rows"] == 2047 and plan["validation_rows"] == 432
                and plan["expected_optimizer_steps"] == 256 and plan["epochs"] == 1
                and plan["model_trained"] is False and plan["resume"] is False
                and plan["automatic_retry"] is False
                and plan["data_attestation"]["manifest_sha256"] == DATA_SHA,
                "Original exposure/schema/data identity differs.")
        old_source_pins = plan["source_pins"]
        require(PROVIDER in old_source_pins and old_source_pins[PROVIDER] == OLD_PROVIDER_SHA
                and all(old_files[name]["sha256"] == value for name, value in old_source_pins.items()),
                "Original training-plan source scope differs from its sealed payload.")
        plan["source_pins"] = {name: files[name]["sha256"] for name in old_source_pins}
        require({name for name in old_source_pins if old_source_pins[name] != plan["source_pins"][name]} == {PROVIDER},
                "Training-plan source rebinding changed more than the provider.")
        plan["plan_sha256"] = hashlib.sha256(canonical({k: v for k, v in plan.items() if k != "plan_sha256"})).hexdigest()
        require(all(plan[name] == value for name, value in old_plan.items() if name not in {"source_pins", "plan_sha256"}),
                "Source rebinding changed original data/config/exposure.")
        config = old_plans["plans"][key]["config"]
        require(files[config]["sha256"] == plan["config_sha256"] == old_files[config]["sha256"], "Original config changed.")
        save(filename, plan)
        result[key] = {"model": plan["model"], "config": config, "config_sha256": plan["config_sha256"],
            "prepared_plan": descriptor(OUT / filename, with_path=True), "plan_sha256": plan["plan_sha256"],
            "training_rows": plan["training_rows"], "validation_rows": plan["validation_rows"],
            "expected_optimizer_steps": plan["expected_optimizer_steps"],
            "training_row_ids_sha256": plan["training_row_ids_sha256"],
            "validation_row_ids_sha256": plan["validation_row_ids_sha256"],
            "future_artifact_directory": old_plans["plans"][key]["future_artifact_directory"],
            "inherited_plan": descriptor(OLD / filename, with_path=True), "inherited_plan_sha256": old_plan["plan_sha256"],
            "native_admission_rerun": False, "model_trained": False}
    require(len({row["training_row_ids_sha256"] for row in result.values()}) == 1
            and len({row["validation_row_ids_sha256"] for row in result.values()}) == 1,
            "Model-size plans no longer share exact row identity.")
    return result


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (60, 75))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_BYTES, MAX_BYTES))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.alarm(120)
    started = time.monotonic()
    require(not OUT.exists(), "Refusing to overwrite an existing bundle05 attempt.")
    require(all(len(value[1]) == 64 and set(value[1]) <= set("0123456789abcdef") for value in CHANGES.values()),
            "All three reviewed replacement hashes must be pinned before building.")
    require(descriptor(OLD / "manifest.json")["sha256"] == MANIFEST_SHA
            and descriptor(OLD / "actual-completion.json")["sha256"] == OLD_RECEIPT_SHA,
            "Sealed04 source/admission receipt changed.")
    old = json.loads((OLD / "manifest.json").read_bytes())
    receipt = json.loads((OLD / "actual-completion.json").read_bytes())
    require(old["file_count"] == 1206 and old["expanded_bytes"] == 108045238
            and old["dataset_manifest_sha256"] == DATA_SHA
            and receipt["actual_exit_code"] == receipt["admission"]["actual_exit_code"] == 0
            and receipt["admission"]["owned_child_reaped"] is True, "Original payload/admission identity differs.")
    old_files = inventory(OLD / "source")
    require(old_files == old["files"] and set(CHANGES) <= set(old_files), "Original source inventory changed.")
    require(descriptor(OLD / "source-data.tar.gz") == {"bytes": old["archive_bytes"], "sha256": old["archive_sha256"]},
            "Original compressed archive pin changed.")
    old_scope = json.loads((OLD / "controller-source-pins.json").read_bytes())
    require(hashlib.sha256(canonical(old_scope)).hexdigest() == old["controller_source_pins_sha256"]
            and all(old_files[name] == value for name, value in old_scope.items()), "Original controller map changed.")
    replacements = {name: descriptor(path) for name, (path, _) in CHANGES.items()}
    require(all(replacements[name]["sha256"] == expected for name, (_, expected) in CHANGES.items()),
            "A reviewed replacement source changed.")
    OUT.mkdir(mode=0o700)
    SOURCE.mkdir(mode=0o700)
    for name, expected in old_files.items():
        relative = PurePosixPath(name)
        require(not relative.is_absolute() and str(relative) == name and ".." not in relative.parts
                and "\\" not in name and "\x00" not in name, "Noncanonical archive path.")
        incoming = CHANGES[name][0] if name in CHANGES else OLD / "source" / name
        target = SOURCE / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with incoming.open("rb") as src, target.open("xb") as dst:
            while chunk := src.read(BLOCK):
                dst.write(chunk)
        target.chmod(0o444)
    files = inventory(SOURCE)
    require(set(files) == set(old_files)
            and {name for name in files if files[name] != old_files[name]} == set(CHANGES)
            and all(files[name] == value for name, value in replacements.items()), "Payload scope changed beyond three files.")
    scope, source_check = source_contracts(files, old_files, old_scope)
    scope_sha = hashlib.sha256(canonical(scope)).hexdigest()
    save("controller-source-pins.json", scope)
    plans = rebind_plans(files, old_files)
    save("prepared-plans.json", {"schema": "hydra-source-rebound-three-model-plans-v1", "completed": True,
        "preparation_mode": "metadata_rebinding_of_preserved_native_data_admission", "plans": plans,
        "inherited_admission": descriptor(OLD / "actual-completion.json", with_path=True),
        "inherited_prepared_plans": descriptor(OLD / "prepared-plans.json", with_path=True),
        "dataset_manifest_sha256": DATA_SHA, "exact_row_identity_shared": True,
        "native_parsing_for_exclusions": False, "native_proof_replays": 0,
        "model_calls": 0, "tokenizers_loaded": 0, "training_performed": False,
        "application_modules_imported": 0, "gpu_allocations": 0, "automatic_retry": False})
    with (OUT / "source-data.tar.gz").open("xb") as stream:
        first = archive(files, stream)
    require(first == archive(files), "Deterministic second archive stream differed.")
    verify_archive(files)
    manifest = {"schema": "hydra-exact-source-data-bundle-v3", **first, "file_count": len(files),
        "expanded_bytes": sum(row["bytes"] for row in files.values()), "files": files,
        "derived_from": {"path": OLD.relative_to(ROOT).as_posix(), "manifest_sha256": MANIFEST_SHA,
            "actual_completion_sha256": OLD_RECEIPT_SHA, "unchanged_files": len(files) - 3},
        "changed_files": {name: {"before": old_files[name], "after": files[name],
            "replacement_source": CHANGES[name][0].relative_to(ROOT).as_posix()} for name in sorted(CHANGES)},
        "added_files": {}, "removed_files": [], "provider_sha256": PROVIDER_SHA,
        "provider_profile": "hydra-experimental-torch-qwen3-v2", "runner_sha256": SMOKE_SHA,
        "training_controller_sha256": TRAINER_SHA, "controller_source_pins_sha256": scope_sha,
        "source_contract_check": source_check, "dataset_manifest_sha256": DATA_SHA,
        "prepared_plans": descriptor(OUT / "prepared-plans.json", with_path=True),
        "preparation_mode": "metadata_rebinding_of_preserved_native_data_admission",
        "application_modules_imported": 0, "model_calls": 0, "native_parsing_for_exclusions": False,
        "native_proof_replays": 0, "tokenizers_loaded": 0, "training_performed": False,
        "automatic_launch": False, "automatic_retry": False, "gpu_allocations": 0, "uploads": 0,
        "bounds": {"cpu_soft_seconds": 60, "cpu_hard_seconds": 75, "wall_seconds": 120,
            "max_files": 1300, "max_expanded_bytes": MAX_BYTES},
        "reproducibility": {"archive_repeated_stream_matches": True, "member_order": "lexical",
            "tar_format": "PAX", "file_mode": "0444", "uid": 0, "gid": 0, "mtime": 0,
            "gzip_filename": "", "gzip_mtime": 0, "gzip_level": 9,
            "python": sys.version.split()[0], "zlib_runtime": zlib.ZLIB_RUNTIME_VERSION}}
    save("manifest.json", manifest)
    launch = json.loads((OLD / "training-launch-inputs.json").read_bytes())
    launch.update(schema="hydra-frozen-training-launch-inputs-v2",
        preparation_mode="metadata_rebinding_of_preserved_native_data_admission",
        archive=descriptor(OUT / "source-data.tar.gz", with_path=True),
        bundle_manifest=descriptor(OUT / "manifest.json", with_path=True),
        scheduler_helper_sha256=SMOKE_SHA, training_controller_sha256=TRAINER_SHA,
        source_pins_sha256=scope_sha, provider_sha256=PROVIDER_SHA, models=plans,
        inherited_admission=descriptor(OLD / "actual-completion.json", with_path=True),
        native_parsing_for_exclusions=False, application_modules_imported=0)
    save("training-launch-inputs.json", launch)
    require(inventory(OLD / "source") == old_files and inventory(SOURCE) == files,
            "Original or copied source changed during the build.")
    require(all(descriptor(path) == replacements[name] for name, (path, _) in CHANGES.items()),
            "Replacement source changed during the build.")
    save("build-result.json", {"schema": "hydra-derived-provider-v2-bundle-build-v1", "completed": True,
        "original_bundle04_unchanged": True, "only_three_payload_files_changed": True,
        "verified_source_files": len(files), "verified_archive_members": len(files),
        "archive_repeated_stream_matches": True, "source_contract_check": source_check,
        "manifest": descriptor(OUT / "manifest.json", with_path=True), "archive": first,
        "prepared_plans": descriptor(OUT / "prepared-plans.json", with_path=True),
        "controller_source_pins_sha256": scope_sha, "builder": descriptor(Path(__file__).resolve(), with_path=True),
        "elapsed_seconds": time.monotonic() - started,
        "cpu_seconds": resource.getrusage(resource.RUSAGE_SELF).ru_utime + resource.getrusage(resource.RUSAGE_SELF).ru_stime,
        "peak_rss_native_units": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "peak_rss_units": "bytes" if sys.platform == "darwin" else "KiB",
        "application_modules_imported": 0, "native_parsing_for_exclusions": False,
        "model_calls": 0, "native_proof_replays": 0, "tokenizers_loaded": 0,
        "gpu_allocations": 0, "uploads": 0, "automatic_retry": False})
    for path in SOURCE.rglob("*"):
        if path.is_dir():
            path.chmod(0o555)
    SOURCE.chmod(0o555)
    signal.alarm(0)
    print(json.dumps({"completed": True, "sealed": False, "pending": "actual receipt and local seal",
        "file_count": len(files), "expanded_bytes": manifest["expanded_bytes"], **first,
        "manifest_sha256": descriptor(OUT / "manifest.json")["sha256"],
        "controller_source_pins_sha256": scope_sha,
        "plan_sha256": {key: value["plan_sha256"] for key, value in plans.items()},
        "elapsed_seconds": time.monotonic() - started}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
