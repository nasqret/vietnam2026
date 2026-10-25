"""Metadata-only admission for exactly one recovered 1.7B and one normal 4B pilot.

No receipt is rewritten, no allocation is made and no model/native code runs.
The old failed job remains failed; every future inference must reload its own
saved tensors through the explicitly versioned inference provider. Callers supply real collected
file descriptors; this module contains no success receipt or allocation choice.
"""
from __future__ import annotations

import argparse
import base64
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import stat
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REL = "output/hydra-implementation-2026-09-04/"
RECOVERY = "p6-postsave-recovery-v4"
CPU_REPORT = "metadata-recovery-import4.json"
CPU_ACTUAL = "metadata-actual-completion-import4.json"
FRESH4 = "p6-training-launchers-v3"
UID = 105923
MAX_COLLECTION_BYTES = 16 * 1024**2
ORIGINAL = REL + "p6-training-launchers-v2/attempts/p6-training-fresh-1.7b-v2-01/observation-013"
KINDS = {"qwen3-1.7b-base": "saved_pilot_recovery_v2", "qwen3-4b-base": "fresh4b_source08_v3"}
PINNED = {
    RECOVERY + "/metadata_recovery.py": "aa2745a98bf56c54dc23d2393b0104bdf9a6ae0e14c6962dd4136c6d1f285e16",
    RECOVERY + "/gpu_saved_reload.py": "b50a2f9c54e977d13dd1f1830cb414701631bd5f46317fe1c8346ce5c49e43e6",
    RECOVERY + "/remote_recovery_control.py": "2aba491b719679e7f7b2418ce6c15d5a87d28f50d338f06f1f4e8fe950128b38",
    RECOVERY + "/recovery_launchers.py": "bd7bb619fb33a64c732dcd46a7e6f1e64d8f58fa27de40bc0bc4ed9eae7119c6",
    FRESH4 + "/remote_training_control.py": "c59c7343e08330d938ba7783827663354631b2a995ede1ee9172a9e86904e2b0",
    FRESH4 + "/training_launchers.py": "b62eeeecdcd42d071b11fd54884ab788c6c57c8b369cf6c4ffbebc34bddaf437",
    "paired-evaluation-v2/paired_common.py": "395849fde6e363a96a67aab3fbb7c8f5f82e2a8a6919eb123009ff108800a16d",
}
CHARGE_GLOBS = (
    "p6-training-launchers-v*/attempts/*/release/charge-intent.json",
    "p6-8b-smoke-launchers-v*/attempts/*/release/charge-intent.json",
    "p6-8b-training-launchers-v*/attempts/*/release/charge-intent.json",
    "paired-launchers-v*/prepared/arms/*/release/charge-intent.json",
    "p7-teacher-launchers-v*/attempts/*/release/charge-intent.json",
    "p7-student-launchers-v*/attempts/*/release/charge-intent.json",
    "p6-postsave-recovery-v*/attempts/*/release/charge-intent.json",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate metadata field.")
            result[key] = value
        return result
    def constant(value):
        raise ValueError("Non-finite JSON metadata: " + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


class Evidence:
    """A finite set of ordinary workspace files; no directory traversal or I/O hooks."""
    def __init__(self, root):
        self.root = Path(root).resolve(strict=True)
        self.inputs = {}
        self.total_bytes = 0

    def read(self, name, expected=None, maximum=2 * 1024**2):
        require(type(name) is str and 0 < len(name) <= 4096, "Invalid evidence path.")
        relative = Path(name)
        require(not relative.is_absolute() and relative.as_posix() == name and ".." not in relative.parts,
                "Evidence must stay at an ordinary workspace-relative path.")
        path = self.root / relative
        before = path.lstat()
        require(stat.S_ISREG(before.st_mode) and path.resolve(strict=True) == path and before.st_size <= maximum,
                "Evidence is not a bounded ordinary file.")
        with path.open("rb") as stream:
            raw = stream.read(maximum + 1)
        after = path.lstat()
        require(len(raw) == before.st_size and all(getattr(before, k) == getattr(after, k)
                for k in ("st_dev", "st_ino", "st_size", "st_mtime_ns")), "Evidence changed while read.")
        sha = digest(raw)
        require(expected is None or type(expected) is str and re.fullmatch(r"[0-9a-f]{64}", expected)
                and sha == expected, "Evidence SHA differs: " + name)
        self.total_bytes += len(raw)
        require(self.total_bytes <= 48 * 1024**2 and len(self.inputs) < 64, "Admission input budget exceeded.")
        pin = {"bytes": len(raw), "sha256": sha}
        require(name not in self.inputs or self.inputs[name] == pin, "Evidence changed between admission reads.")
        self.inputs[name] = pin
        return raw

    def descriptor(self, item, maximum=2 * 1024**2):
        require(type(item) is dict and set(item) == {"path", "sha256"}, "Expected exact evidence path and SHA.")
        return self.read(item["path"], item["sha256"], maximum)


@contextmanager
def readers(evidence, recovery=False):
    """Import only the exact reviewed metadata readers; their run methods are never called."""
    rows = ([
        ("gpu_saved_reload", RECOVERY + "/gpu_saved_reload.py"),
        ("_pilot_original_failure", RECOVERY + "/metadata_recovery.py"),
        ("remote_recovery_control", RECOVERY + "/remote_recovery_control.py"),
        ("_pilot_collection_reader", RECOVERY + "/recovery_launchers.py"),
    ] if recovery else [
        ("remote_training_control", FRESH4 + "/remote_training_control.py"),
        ("_pilot_collection_reader", FRESH4 + "/training_launchers.py"),
    ]) + [("_pilot_exposure_contract", "paired-evaluation-v2/paired_common.py")]
    previous, loaded = {}, {}
    try:
        for alias, relative in rows:
            path = evidence.root / REL / relative
            raw = evidence.read(REL + relative, PINNED[relative], 128 * 1024)
            previous[alias] = sys.modules.get(alias)
            spec = importlib.util.spec_from_file_location(alias, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[alias] = module
            exec(compile(raw, str(path), "exec"), module.__dict__)
            loaded[alias] = module
        yield loaded
    finally:
        for alias, old in previous.items():
            if old is None:
                sys.modules.pop(alias, None)
            else:
                sys.modules[alias] = old


def actual_outer(record):
    require(type(record) is dict, "Missing actual outer completion record.")
    codes = [record[k] for k in ("actual_exit_code", "actual_process_exit_code", "actual_outer_exit_code", "exit_code") if k in record]
    chunks = [record[k] for k in ("completion_chunk", "actual_completion_chunk", "actual_outer_completion_chunk") if k in record]
    require(codes and all(type(code) is int and code == 0 for code in codes)
            and chunks and all(type(chunk) is str and re.fullmatch(r"[0-9a-f]{6,64}", chunk) for chunk in chunks),
            "An actual successful, separately observed collection exit is required.")


def collection(evidence, descriptors, reader, family, attempt, response_schema):
    require(type(descriptors) is dict and set(descriptors) == {"response", "transport", "actual_completion"},
            "Missing real collection descriptors.")
    path = descriptors["response"].get("path", "")
    require(type(path) is str and re.fullmatch(re.escape(REL + family + "/attempts/" + attempt)
            + r"/observation-[0-9]{3}/response\.json", path), "Collection is not from the exact admitted attempt.")
    parent = str(Path(path).parent)
    require(descriptors["transport"].get("path") == parent + "/transport-completion.json"
            and descriptors["actual_completion"].get("path") in {
                parent + "/actual-tool-completion.json", parent + "/actual-completion.json"},
            "Collection transport and actual receipt must belong to the same observation.")
    actual_outer(strict_json(evidence.descriptor(descriptors["actual_completion"], 65536)))
    transport = strict_json(evidence.descriptor(descriptors["transport"], 65536))
    remote_name = "remote_recovery_control.py" if family == RECOVERY else "remote_training_control.py"
    require(type(transport.get("actual_ssh_exit_code")) is int and transport["actual_ssh_exit_code"] == 0
            and transport.get("owned_child_reaped") is True and transport.get("output_complete") is True
            and transport.get("stop_reason") is None and transport.get("automatic_retry") is False
            and transport.get("remote_script_sha256") == PINNED[family + "/" + remote_name],
            "Collection transport is unsuccessful or uses another helper.")
    response = strict_json(evidence.descriptor(descriptors["response"], MAX_COLLECTION_BYTES))
    require(response.get("schema") == response_schema and response.get("phase") == "collect"
            and response.get("completed") is True and response.get("error") is None, "Collection did not complete.")
    observation = response["result"]
    require(type(observation) is dict and observation.get("read_only") is True
            and type(observation.get("files")) is dict and set(observation["files"]) <= set(reader.control.FILES),
            "Unexpected collection inventory.")
    total = 0
    for row in observation["files"].values():
        require(type(row) is dict and type(row.get("bytes")) is int and 0 <= row["bytes"] <= 2 * 1024**2
                and type(row.get("base64")) is str and len(row["base64"]) <= 3 * 1024**2,
                "Unbounded collected file.")
        raw = base64.b64decode(row["base64"], validate=True)
        total += len(raw)
        require(len(raw) == row["bytes"] and digest(raw) == row["sha256"] and total <= reader.control.MAX_OBSERVATION,
                "Collected bytes differ from their hashes.")
    return observation


def complete_bytes(observation, name):
    row = observation["files"].get(name, {})
    require(row.get("stable") is True and row.get("complete_file") is True and row.get("offset") == 0,
            "Required evidence file is incomplete or unstable: " + name)
    raw = base64.b64decode(row["base64"], validate=True)
    require(row.get("bytes") == row.get("file_bytes_before") == row.get("file_bytes_after") == len(raw)
            and digest(raw) == row.get("sha256"), "Required evidence byte inventory differs.")
    return raw


def remote_rows(observation, names, job_directory):
    result = {}
    for name in names:
        raw = complete_bytes(observation, name)
        require(name.startswith("job/"), "Only fixed job metadata may be projected here.")
        result[job_directory + "/" + name[4:]] = {"bytes": len(raw), "sha256": digest(raw)}
    return result


def checked_reservation(observation, spec, reader):
    record = strict_json(complete_bytes(observation, "job/reservation.json"))
    require(type(record.get("uid")) is int and record["uid"] == UID
            and observation.get("job_id") == record.get("job_id")
            and canonical(record) == canonical(reader.control.reservation(spec, record.get("job_id"), UID)),
            "Pilot/recovery observation belongs to another owned reservation.")
    return record


def saved_population(artifact, before, after, manifest_pin):
    expected = {"manifest.json": manifest_pin["sha256"]}
    for group in ("adapter", "tokenizer"):
        files = artifact[group]["files"]
        require(type(files) is dict and 1 <= len(files) <= 16, "Invalid saved artifact population.")
        for name, sha in files.items():
            require(type(name) is str and name.startswith(group + "/") and name.count("/") == 1
                    and Path(name).name not in {".", ".."}, "Invalid saved artifact path.")
            expected[name] = sha
    require(type(before) is dict and before == after and set(before) == set(expected)
            and before["manifest.json"] == manifest_pin, "Saved artifact inventory changed or is partial.")
    for name, sha in expected.items():
        row = before[name]
        require(type(row) is dict and set(row) == {"bytes", "sha256"}
                and type(row["bytes"]) is int and 0 < row["bytes"] <= 256 * 1024**2
                and row["sha256"] == sha, "Saved tensor/tokenizer bytes changed: " + name)


def recovered(evidence, descriptor):
    require(set(descriptor) == {"kind", "cpu_metadata", "cpu_actual_completion", "gpu_collection"},
            "Saved recovery requires separate CPU and GPU receipts.")
    for key, filename in (("cpu_metadata", CPU_REPORT), ("cpu_actual_completion", CPU_ACTUAL)):
        require(descriptor[key].get("path") == REL + RECOVERY + "/" + filename, "Unexpected CPU recovery receipt path.")
    metadata_raw = evidence.descriptor(descriptor["cpu_metadata"])
    actual_raw = evidence.descriptor(descriptor["cpu_actual_completion"], 65536)
    metadata, actual = strict_json(metadata_raw), strict_json(actual_raw)
    with readers(evidence, recovery=True) as modules:
        reader, gpu = modules["_pilot_collection_reader"], modules["gpu_saved_reload"]
        gpu.validate_metadata(metadata, actual, digest(metadata_raw), reader.control.METADATA_VERIFIER_SHA)
        observation = collection(evidence, descriptor["gpu_collection"], reader, RECOVERY, gpu.ATTEMPT,
                                 "hydra-p6-saved-recovery-control-phase-v1")
        prepared_name = REL + RECOVERY + "/attempts/" + gpu.ATTEMPT + "/prepared.json"
        prepared_raw = evidence.read(prepared_name)
        _, prepared, spec, source_map = reader.load_prepared(digest(prepared_raw))
        require(spec["metadata_receipt_sha256"] == digest(metadata_raw)
                and spec["metadata_actual_sha256"] == digest(actual_raw), "Recovery used different CPU admission.")
        record = checked_reservation(observation, spec, reader)
        summary = reader.summarize(observation, spec, record, source_map)
        require(summary.get("status") == "saved_adapter_independent_reload_complete"
                and summary.get("saved_adapter_reload_admitted") is True and summary.get("errors") == [],
                "Independent saved reload is incomplete: " + str(summary.get("errors"))[:1200])
        original_obs = strict_json(evidence.read(ORIGINAL + "/observation.json",
            "a1d56e0e322a8b3f49d2ecd51da21309efe3ccc6cd091c3482edebef10375923", 65536))
        original_transport = strict_json(evidence.read(ORIGINAL + "/transport-completion.json",
            "ac2b0deec46aaac68a7fc0405b6d28acab8c8157b0b45c95a0b52ac55b388269", 65536))
        originals = {}
        for name in ("artifact/manifest.json", "job/result/request.json", "job/result/completion.json", "job/actual-process-exit.txt"):
            pin = original_obs["files"][name]
            raw = evidence.read(ORIGINAL + "/" + name, pin["sha256"])
            require(len(raw) == pin["bytes"] and all(metadata["inputs"][name][k] == pin[k] for k in ("bytes", "sha256")),
                    "CPU admission does not bind the preserved original evidence.")
            originals[name] = raw
        original_request = strict_json(originals["job/result/request.json"])
        modules["_pilot_original_failure"].validate_failed_job(original_obs, original_transport,
            strict_json(originals["job/result/completion.json"]), original_request,
            originals["job/actual-process-exit.txt"])
        manifest_raw = originals["artifact/manifest.json"]
        artifact = strict_json(manifest_raw)
        require(digest(manifest_raw) == gpu.MANIFEST_SHA and metadata.get("original_recorded_saved_plan_canonical_json_equal") is True
                and metadata.get("runtime_plan_matches_exact_provider_rebinding") is True
                and metadata.get("training_exposure_changed") is False
                and metadata.get("data_attestation") == artifact["plan"]["data_attestation"]
                and metadata.get("finite_gradient_boundaries") == 256 and metadata.get("changed_parameter_tensors") == 392,
                "Recovered artifact or independent CPU training admission differs.")
        before = strict_json(complete_bytes(observation, "job/result/artifact-before.json"))
        after = strict_json(complete_bytes(observation, "job/result/artifact-after.json"))
        manifest_pin = {"bytes": len(manifest_raw), "sha256": digest(manifest_raw)}
        saved_population(artifact, before, after, manifest_pin)
        remote = remote_rows(observation, (
            "job/actual-process-exit.txt", "job/reservation.json", "job/reservation.json.claimed",
            "job/result/request.json", "job/result/completion.json", "job/result/loaded-model.json",
            "job/result/artifact-before.json", "job/result/artifact-after.json"), spec["remote_job_directory"])
        remote[gpu.ARTIFACT + "/manifest.json"] = manifest_pin
        for key, raw in originals.items():
            if key.startswith("job/"):
                remote[gpu.CAMPAIGN + "/jobs/p6-training-fresh-1.7b-v2-01/" + key[4:]] = {"bytes": len(raw), "sha256": digest(raw)}
        for name, raw in ((CPU_REPORT, metadata_raw), (CPU_ACTUAL, actual_raw)):
            remote[gpu.PACKAGE + "/" + name] = {"bytes": len(raw), "sha256": digest(raw)}
        for key, path, expected_sha in (
            ("runtime_source_map", gpu.PACKAGE + "/runtime-source-pins-base3.json", None),
            ("runtime_manifest", str(Path(gpu.SOURCE).parent / "manifest.json"), gpu.RUNTIME_MANIFEST_SHA)):
            item = metadata["inputs"].get(key, {})
            require(item.get("path") == path and type(item.get("bytes")) is int
                    and 0 < item["bytes"] <= 2 * 1024**2 and gpu.sha(item.get("sha256"))
                    and (expected_sha is None or item["sha256"] == expected_sha),
                    "The separately authenticated inference input binding differs.")
            remote[path] = {"bytes": item["bytes"], "sha256": item["sha256"]}
        return {
            "job_id": gpu.ORIGINAL_JOB, "model_key": gpu.MODEL_KEY, "artifact_directory": gpu.ARTIFACT,
            "base_directory": gpu.BASE, "manifest_sha256": gpu.MANIFEST_SHA,
            "final_tensor_population_sha256": gpu.FINAL_TENSOR_SHA,
            "training_exposure": modules["_pilot_exposure_contract"].training_exposure(artifact),
            "original_training": {"job_id": gpu.ORIGINAL_JOB, "slurm_state": "FAILED", "slurm_exit_code": "1:0",
                "process_exit_code": 1, "controller_completed": False, "attempt": "p6-training-fresh-1.7b-v2-01",
                "seconds": original_request["reservation"]["seconds"], "reservation_sha256": original_request["reservation_sha256"],
                "source_root": gpu.TRAINING_SOURCE, "source_pins_sha256": gpu.TRAINING_SOURCE_MAP_SHA,
                "provider_sha256": gpu.TRAINING_PROVIDER_SHA},
            "recovery": {"job_id": record["job_id"], "slurm_state": "COMPLETED", "slurm_exit_code": "0:0",
                "process_exit_code": 0, "status": summary["status"], "cpu_metadata_sha256": digest(metadata_raw),
                "cpu_actual_sha256": digest(actual_raw), "attempt": gpu.ATTEMPT, "seconds": record["seconds"],
                "reservation_sha256": digest(canonical(record) + b"\n"), "selector": "import4",
                "runtime_source_root": gpu.SOURCE, "runtime_source_pins_sha256": gpu.SOURCE_MAP_SHA,
                "runtime_provider_sha256": gpu.PROVIDER_SHA, "runtime_manifest_sha256": gpu.RUNTIME_MANIFEST_SHA,
                "runtime_inference_only": True, "runtime_training_execution_allowed": False,
                "plan_derivation": metadata["plan_derivation"],
                "adapter_config_admission": metadata["adapter_config_admission"]},
            "normal_training_success": False, "original_failure_preserved": True,
            "prior_independent_reload_completed": True, "remote_files": remote,
        }


def normal4(evidence, descriptor):
    require(set(descriptor) == {"kind", "collection"}, "Normal 4B requires its real v3 collection.")
    with readers(evidence) as modules:
        reader = modules["_pilot_collection_reader"]
        model = reader.control.MODELS["qwen3-4b-base"]
        observation = collection(evidence, descriptor["collection"], reader, FRESH4, model["attempt"],
                                 "hydra-p6-training-control-phase-v1")
        prepared_name = REL + FRESH4 + "/attempts/" + model["attempt"] + "/prepared.json"
        prepared_raw = evidence.read(prepared_name)
        _, prepared, spec, _ = reader.load_prepared("qwen3-4b-base", digest(prepared_raw))
        require(spec["seconds"] == 2100 and spec["soft_limit_seconds"] == 2040, "The selected 4B allocation differs.")
        record = checked_reservation(observation, spec, reader)
        summary = reader.summarize(observation, spec, record, prepared["base_identity_sha256"])
        require(summary.get("status") == "complete_saved_artifact_metadata_requires_fresh_reload"
                and summary.get("saved_artifact_metadata_complete") is True and summary.get("errors") == [],
                "The actual 4B pilot is incomplete: " + str(summary.get("errors"))[:1200])
        manifest_raw = complete_bytes(observation, "artifact/manifest.json")
        artifact = strict_json(manifest_raw)
        artifact_directory = reader.control.SOURCE + "/" + model["artifact"]
        remote = remote_rows(observation, ("job/actual-process-exit.txt", "job/reservation.json",
            "job/reservation.json.claimed", "job/result/request.json", "job/result/completion.json",
            "job/result/artifact-receipt.json"), spec["remote_job_directory"])
        remote[artifact_directory + "/manifest.json"] = {"bytes": len(manifest_raw), "sha256": digest(manifest_raw)}
        return {
            "job_id": record["job_id"], "model_key": "qwen3-4b-base", "artifact_directory": artifact_directory,
            "base_directory": reader.control.CAMPAIGN + "/authenticated-bases-01/qwen3-4b-base",
            "manifest_sha256": digest(manifest_raw),
            "final_tensor_population_sha256": artifact["adapter_update"]["final_tensor_population_sha256"],
            "training_exposure": modules["_pilot_exposure_contract"].training_exposure(artifact),
            "original_training": {"job_id": record["job_id"], "slurm_state": "COMPLETED", "slurm_exit_code": "0:0",
                "process_exit_code": 0, "controller_completed": True, "attempt": model["attempt"], "seconds": record["seconds"],
                "reservation_sha256": digest(canonical(record) + b"\n"),
                "source_root": reader.control.SOURCE, "source_pins_sha256": spec["source_pins_sha256"],
                "controller_sha256": spec["controller_sha256"],
                "provider_sha256": "7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f"},
            "recovery": None, "normal_training_success": True, "original_failure_preserved": False,
            "prior_independent_reload_completed": False, "remote_files": remote,
        }


def admit_pilot(model_key, descriptor, *, root=ROOT):
    require(model_key in KINDS and type(descriptor) is dict and descriptor.get("kind") == KINDS[model_key],
            "Only the explicit recovered1.7/source08-4B admission routes are supported.")
    evidence = Evidence(root)
    own_name = Path(__file__).resolve().relative_to(evidence.root).as_posix()
    own_raw = evidence.read(own_name, maximum=128 * 1024)
    result = recovered(evidence, descriptor) if model_key == "qwen3-1.7b-base" else normal4(evidence, descriptor)
    result.update(schema="hydra-pilot-completion-admission-v2", kind=KINDS[model_key], evidence=descriptor,
        admission_source_sha256=digest(own_raw), input_pins=evidence.inputs,
        reload_required_in_each_paired_case=True, adapter_reload_admitted_for_future_inference=False,
        quality_evaluated=False, automatic_retry=False)
    return result


def admit_pair(descriptors, *, root=ROOT):
    require(type(descriptors) is dict and set(descriptors) == set(KINDS), "Both real pilot admission routes are required.")
    result = {model: admit_pilot(model, descriptors[model], root=root) for model in KINDS}
    require(result["qwen3-1.7b-base"]["training_exposure"] == result["qwen3-4b-base"]["training_exposure"],
            "Fresh sizes did not receive the exact same training exposure.")
    return result


def require_pilot_charges(ledger, admissions):
    """Recovery is an additional full charge; it never replaces the failed pilot."""
    require(type(ledger) is dict and type(ledger.get("gpu_reservations")) is list
            and len(ledger["gpu_reservations"]) <= 64, "Missing bounded campaign ledger.")
    for admission in admissions:
        require(admission.get("schema") == "hydra-pilot-completion-admission-v2", "Expected explicit pilot admission.")
        for allocation in (admission["original_training"], admission["recovery"]):
            if allocation is None:
                continue
            matches = [row for row in ledger["gpu_reservations"] if row.get("attempt") == allocation["attempt"]]
            require(len(matches) == 1, "An admitted pilot/recovery allocation has no unique full charge.")
            row = matches[0]
            require(row.get("job_id") == allocation["job_id"] and type(row.get("gpus")) is int and row["gpus"] == 1
                    and type(row.get("seconds")) is int and row["seconds"] == allocation["seconds"]
                    and type(row.get("allocated_seconds")) is int and row["allocated_seconds"] == allocation["seconds"]
                    and row.get("reservation_sha256") == allocation["reservation_sha256"],
                    "An admitted pilot/recovery charge was omitted, refunded or rebound.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--input-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    evidence = Evidence(ROOT)
    name = args.input.resolve(strict=True).relative_to(ROOT).as_posix()
    record = strict_json(evidence.read(name, args.input_sha256, 65536))
    require(type(record) is dict and set(record) == {"schema", "pilots"}
            and record["schema"] == "hydra-pilot-completion-admission-input-v2", "Explicit actual admission input required.")
    pilots = admit_pair(record["pilots"])
    output = args.output.absolute()
    require(output.parent.resolve(strict=True) == HERE and not output.exists(), "Write one new local admission record only.")
    raw = canonical({"schema": "hydra-pilot-pair-admission-v2", "pilots": pilots,
                     "input_sha256": args.input_sha256, "model_calls": 0, "native_calls": 0, "ssh_calls": 0}) + b"\n"
    require(len(raw) <= 2 * 1024**2, "Admission output exceeds its bound.")
    with output.open("xb") as stream:
        stream.write(raw)
    print(json.dumps({"path": str(output), "sha256": digest(raw), "bytes": len(raw), "metadata_only": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
