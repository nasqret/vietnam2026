"""Derive bundle06 with two scheduler wrappers and three byte-identical plans; standard-library files only.

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
OLD = ROOT / "output/hydra-implementation-2026-09-04/p6-source-bundle-05"
OUT = ROOT / "output/hydra-implementation-2026-09-04/p6-source-bundle-06"
SOURCE = OUT / "source"
MANIFEST_SHA = "a4e1999f52837692fcb3dfa9fb092fe6557dc46808ce60d69e54a376d6dc3c34"
OLD_RECEIPT_SHA = "a8b4522ce8d5e59afd2b806ee9c9d798996549d414042f3e2982016f20338c99"
DATA_SHA = "e575970df58d046735f492acaf22e1cdea44445608a201c62d0644590b95ea77"
PROVIDER_SHA = "7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f"
SMOKE_SHA = "cc8dec7bcb2187568c1aed1eaa1b580435460e297573b655eac2b32b74a271b4"
TRAINER_SHA = "41b97e63f09571071a75e1f1b01c6df8ab173783f596bc6ee1c3f3b0fab3c617"
PROVIDER = "hydra-playground/experimental_model.py"
SMOKE = "output/p6-prototype/remote_provider_smoke.py"
TRAINER = "output/p6-prototype/remote_training_pilot.py"
CHANGES = {
    SMOKE: (ROOT / "output/p6-scheduler-v3/remote_provider_smoke.py", SMOKE_SHA),
    TRAINER: (ROOT / "output/p6-scheduler-v3/remote_training_pilot.py", TRAINER_SHA),
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


def source_contracts(files, old_scope):
    old_trainer = ast.parse((OLD / "source" / TRAINER).read_bytes())
    trainer = ast.parse((SOURCE / TRAINER).read_bytes())
    old_smoke = ast.parse((OLD / "source" / SMOKE).read_bytes())
    smoke = ast.parse((SOURCE / SMOKE).read_bytes())
    require(executable_bodies(trainer) == executable_bodies(old_trainer),
            "Trainer behavior changed beyond its adjacent-helper binding.")
    old_bodies, new_bodies = executable_bodies(old_smoke), executable_bodies(smoke)
    require(set(old_bodies) == set(new_bodies)
            and {key for key in old_bodies if old_bodies[key] != new_bodies[key]} == {"read_scontrol"},
            "Smoke behavior changed beyond the reviewed scheduler query.")
    require(literal(smoke, "PROVIDER_SHA") == PROVIDER_SHA
            and literal(smoke, "SCONTROL_WALL_SECONDS") == 15.0
            and literal(smoke, "MAX_SCONTROL_BYTES") == literal(old_smoke, "MAX_SCONTROL_BYTES")
            and literal(smoke, "MAX_SCONTROL_CALLS") == literal(old_smoke, "MAX_SCONTROL_CALLS")
            and literal(trainer, "SMOKE_SHA") == SMOKE_SHA,
            "The reviewed scheduler/provider limits or binding differ.")
    fixed = literal(trainer, "FIXED_SOURCES")
    require(fixed == literal(old_trainer, "FIXED_SOURCES")
            and literal(trainer, "MODELS") == literal(old_trainer, "MODELS"),
            "Training source or model identity changed.")
    names = {"hydra-playground/" + name for name in fixed} | {SMOKE, TRAINER}
    names.update(name for name in files if name.endswith(".py") and name.startswith(
        ("hydra-playground/native-v7/peano_lab/", "hydra-playground/training-v5/hydra_training_v5/")))
    require(names == set(old_scope) and len(names) == 585, "Controller scope changed.")
    scope = {name: files[name] for name in sorted(names)}
    require(sum(row["bytes"] for row in scope.values()) <= 32 * BLOCK
            and all(row["bytes"] <= 4 * BLOCK for row in scope.values()), "Controller scope exceeds bounds.")
    require(all(scope["hydra-playground/" + name]["sha256"] == expected for name, expected in fixed.items()),
            "Fixed controller source mismatch.")
    require({name for name in scope if scope[name] != old_scope[name]} == set(CHANGES),
            "Controller map changed beyond the two reviewed wrappers.")
    return scope, {"method": "static AST/literal validation and exact file-inventory reconstruction",
        "application_modules_imported": 0, "controller_function_executed": False,
        "trainer_function_class_bodies_unchanged": True, "only_changed_smoke_function": "read_scontrol",
        "scheduler_query_wall_seconds": 15.0, "scheduler_query_output_bytes": 65536,
        "scheduler_query_call_cap": 64, "controller_source_files": len(scope),
        "only_changed_paths": sorted(CHANGES)}


def preserve_plans(files, old_launch):
    # Preserve the old index as evidence too; its links deliberately still name bundle05.
    names = ["prepared-plans.json"] + ["prepared-" + key + ".json" for key in MODELS]
    models = copy.deepcopy(old_launch["models"])
    for name in names:
        raw = (OLD / name).read_bytes()
        require(len(raw) <= BLOCK, "Prepared plan metadata exceeds its bound.")
        with (OUT / name).open("xb") as stream:
            stream.write(raw)
        require(descriptor(OUT / name) == descriptor(OLD / name), "Prepared plan bytes changed.")
    for key in MODELS:
        name = "prepared-" + key + ".json"
        plan = json.loads((OUT / name).read_bytes())
        require(hashlib.sha256(canonical({k: v for k, v in plan.items() if k != "plan_sha256"})).hexdigest()
                == plan["plan_sha256"] == models[key]["plan_sha256"], "Prepared plan identity changed.")
        require(plan["schema"] == "hydra-decision-pilot-plan-v2"
                and plan["profile"] == "hydra-fresh-decision-pilot-v2"
                and plan["training_rows"] == 2047 and plan["validation_rows"] == 432
                and plan["expected_optimizer_steps"] == 256 and plan["epochs"] == 1
                and plan["model_trained"] is False and plan["resume"] is False
                and plan["automatic_retry"] is False
                and plan["data_attestation"]["manifest_sha256"] == DATA_SHA,
                "Training plan schema, data or exposure differs.")
        require(all(files[path]["sha256"] == value for path, value in plan["source_pins"].items())
                and not (set(plan["source_pins"]) & set(CHANGES)),
                "The wrapper change affected a prepared training plan's source scope.")
        require(files[models[key]["config"]]["sha256"] == plan["config_sha256"], "Training config changed.")
        models[key]["prepared_plan"] = descriptor(OUT / name, with_path=True)
    return models


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (60, 75))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_BYTES, MAX_BYTES))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.alarm(120)
    started = time.monotonic()
    require(not OUT.exists(), "Refusing to overwrite bundle06.")
    require(descriptor(OLD / "manifest.json")["sha256"] == MANIFEST_SHA
            and descriptor(OLD / "actual-completion.json")["sha256"] == OLD_RECEIPT_SHA
            and descriptor(OLD / "local-seal.json")["sha256"] ==
            "45283d1f3f6a81c625615be1143f5d2a00cb292fc3a3684368366450811db13d",
            "Sealed05 manifest, completion receipt or seal changed.")
    old = json.loads((OLD / "manifest.json").read_bytes())
    receipt = json.loads((OLD / "actual-completion.json").read_bytes())
    require(old["file_count"] == 1206 and old["expanded_bytes"] == 108047802
            and old["dataset_manifest_sha256"] == DATA_SHA
            and receipt["actual_exit_code"] == 0 and receipt["completed"] is True,
            "Original sealed05 identity/completion differs.")
    old_files = inventory(OLD / "source")
    require(old_files == old["files"] and set(CHANGES) <= set(old_files), "Original inventory changed.")
    require(descriptor(OLD / "source-data.tar.gz") ==
            {"bytes": old["archive_bytes"], "sha256": old["archive_sha256"]}, "Original archive changed.")
    old_scope = json.loads((OLD / "controller-source-pins.json").read_bytes())
    require(hashlib.sha256(canonical(old_scope)).hexdigest() == old["controller_source_pins_sha256"]
            and all(old_files[name] == value for name, value in old_scope.items()), "Original scope changed.")
    require(descriptor(OLD / "training-launch-inputs.json")["sha256"] ==
            "349780c430e3beaa6b3c3980dc5a3fe0f1a17458f467bce3e98904e574220811",
            "Original launch metadata changed.")
    old_launch = json.loads((OLD / "training-launch-inputs.json").read_bytes())
    replacements = {name: descriptor(path) for name, (path, _) in CHANGES.items()}
    require(all(replacements[name]["sha256"] == expected for name, (_, expected) in CHANGES.items()),
            "Reviewed scheduler replacement changed.")
    OUT.mkdir(mode=0o700)
    SOURCE.mkdir(mode=0o700)
    for name in old_files:
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
            and all(files[name] == row for name, row in replacements.items()), "Payload escaped two-file scope.")
    scope, source_check = source_contracts(files, old_scope)
    scope_sha = hashlib.sha256(canonical(scope)).hexdigest()
    save("controller-source-pins.json", scope)
    models = preserve_plans(files, old_launch)
    with (OUT / "source-data.tar.gz").open("xb") as stream:
        archive_record = archive(files, stream)
    require(archive_record == archive(files), "Deterministic archive regeneration differed.")
    verify_archive(files)
    zero_work = {"application_modules_imported": 0, "model_calls": 0,
        "native_parsing_for_exclusions": False, "native_proof_replays": 0,
        "tokenizers_loaded": 0, "training_performed": False,
        "automatic_launch": False, "automatic_retry": False, "gpu_allocations": 0, "uploads": 0}
    manifest = {"schema": "hydra-exact-source-data-bundle-v3", **archive_record,
        "file_count": len(files), "expanded_bytes": sum(row["bytes"] for row in files.values()), "files": files,
        "derived_from": {"path": OLD.relative_to(ROOT).as_posix(), "manifest_sha256": MANIFEST_SHA,
            "actual_completion_sha256": OLD_RECEIPT_SHA, "unchanged_files": len(files) - 2},
        "changed_files": {name: {"before": old_files[name], "after": files[name],
            "replacement_source": CHANGES[name][0].relative_to(ROOT).as_posix()} for name in sorted(CHANGES)},
        "added_files": {}, "removed_files": [], "provider_sha256": PROVIDER_SHA,
        "provider_profile": "hydra-experimental-torch-qwen3-v2", "runner_sha256": SMOKE_SHA,
        "training_controller_sha256": TRAINER_SHA, "controller_source_pins_sha256": scope_sha,
        "source_contract_check": source_check, "dataset_manifest_sha256": DATA_SHA,
        "prepared_plans": descriptor(OUT / "prepared-plans.json", with_path=True),
        "prepared_plan_files_byte_identical_to_bundle05": True,
        "preparation_mode": "unchanged_plans_with_scheduler_binding_revision", **zero_work,
        "bounds": {"cpu_soft_seconds": 60, "cpu_hard_seconds": 75, "wall_seconds": 120,
            "max_files": 1300, "max_expanded_bytes": MAX_BYTES},
        "reproducibility": {"archive_repeated_stream_matches": True, "member_order": "lexical",
            "tar_format": "PAX", "file_mode": "0444", "uid": 0, "gid": 0, "mtime": 0,
            "gzip_filename": "", "gzip_mtime": 0, "gzip_level": 9,
            "python": sys.version.split()[0], "zlib_runtime": zlib.ZLIB_RUNTIME_VERSION}}
    save("manifest.json", manifest)
    launch = copy.deepcopy(old_launch)
    launch.update(preparation_mode="unchanged_plans_with_scheduler_binding_revision",
        archive=descriptor(OUT / "source-data.tar.gz", with_path=True),
        bundle_manifest=descriptor(OUT / "manifest.json", with_path=True),
        scheduler_helper_sha256=SMOKE_SHA, training_controller_sha256=TRAINER_SHA,
        source_pins_sha256=scope_sha, models=models,
        derived_from_bundle_completion=descriptor(OLD / "actual-completion.json", with_path=True),
        prepared_plan_files_byte_identical_to_bundle05=True, scheduler_query_wall_seconds=15.0,
        scheduler_query_output_bytes=65536, scheduler_query_call_cap=64)
    save("training-launch-inputs.json", launch)
    require(inventory(OLD / "source") == old_files and inventory(SOURCE) == files,
            "Original or copied payload changed during build.")
    require(all(descriptor(path) == replacements[name] for name, (path, _) in CHANGES.items()),
            "Reviewed replacement changed during build.")
    build = {"schema": "hydra-derived-scheduler-v3-bundle-build-v1", "completed": True,
        "original_bundle05_unchanged": True, "only_two_payload_files_changed": True,
        "prepared_plan_files_byte_identical_to_bundle05": True,
        "verified_source_files": len(files), "verified_archive_members": len(files),
        "archive_repeated_stream_matches": True, "source_contract_check": source_check,
        "manifest": descriptor(OUT / "manifest.json", with_path=True), "archive": archive_record,
        "prepared_plans": descriptor(OUT / "prepared-plans.json", with_path=True),
        "controller_source_pins_sha256": scope_sha,
        "builder": descriptor(Path(__file__).resolve(), with_path=True),
        "elapsed_seconds": time.monotonic() - started,
        "cpu_seconds": resource.getrusage(resource.RUSAGE_SELF).ru_utime + resource.getrusage(resource.RUSAGE_SELF).ru_stime,
        "peak_rss_native_units": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "peak_rss_units": "bytes" if sys.platform == "darwin" else "KiB", **zero_work}
    save("build-result.json", build)
    for path in SOURCE.rglob("*"):
        if path.is_dir():
            path.chmod(0o555)
    SOURCE.chmod(0o555)
    signal.alarm(0)
    print(json.dumps({"completed": True, "sealed": False, "pending": "actual receipt and local seal",
        "file_count": len(files), "expanded_bytes": manifest["expanded_bytes"], **archive_record,
        "manifest_sha256": descriptor(OUT / "manifest.json")["sha256"],
        "launch_inputs_sha256": descriptor(OUT / "training-launch-inputs.json")["sha256"],
        "controller_source_pins_sha256": scope_sha, "elapsed_seconds": time.monotonic() - started}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
