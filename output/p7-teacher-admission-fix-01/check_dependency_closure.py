"""Prepare only missing baseline dependencies; check the unchanged hash verifier.

No dataset regeneration, theorem parsing, proof, model, network, or subprocess.
The authoritative baseline function is AST-extracted for an isolated file test;
no module or runtime global is patched or imported.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / "output/hydra-implementation-2026-09-04"
DEST = BASE / "combined-source-bundle-03"
FAILED = BASE / "combined-source-bundle-02"
P6 = BASE / "p6-source-bundle-07"
RELATIVE = "hydra-playground/training-v5"
BASELINE_SHA = "fa0f560dfd2310557ad31271786dd89abd4878f4f074be98da74e3301558db8d"
ATTESTOR_SHA = "b3a6fb79fee07c6b5fdc61988a56e598bb57cea0b7e5501df80519422cbddb53"
MANIFESTS = {
    FAILED: "ae47bb1f0b6939c3f1ca8ac406024f832fc95b50ff505cf66648e94df0e578a7",
    DEST: "bff0239d9e0c74e088118a271907da887d009acad3e3b21eca4534c1da855c08",
    P6: "0cf4cce57f8e4793d09c6283b33dfe81400a3d9653e994116c9899f23da737a3",
}
DENIED = []


def guard(event, args):
    if event in {"subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect", "socket.bind"}:
        DENIED.append(event)
        raise AssertionError("File-only gate prohibits process/network activity.")
    if event == "import" and args[0].split(".")[0] in {
        "peano_lab", "torch", "transformers", "mlx", "numpy", "sympy", "cvc5", "z3", "export_decisions"
    }:
        DENIED.append(args[0])
        raise AssertionError("File-only gate prohibits native/model/dataset runtime imports.")


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path, expected=None):
    require(path.resolve() == path and path.is_file() and not path.is_symlink(), "Ordinary fixed file required.")
    before = path.stat()
    require(before.st_size <= 32 * 1024**2, "File exceeds metadata gate bound.")
    raw = path.read_bytes()
    after = path.stat()
    fields = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    require(fields(before) == fields(after) and len(raw) == before.st_size, "Input changed during read.")
    descriptor = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    if expected is not None:
        require(descriptor == expected if isinstance(expected, dict) else descriptor["sha256"] == expected,
                "Exact input pin differs: " + str(path.relative_to(ROOT)))
    return raw, descriptor


def write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(raw)


def save(path, value):
    write(path, json.dumps(value, sort_keys=True, indent=2, allow_nan=False).encode() + b"\n")


def main():
    sys.addaudithook(guard)
    manifests, watched = {}, {}
    for bundle, expected in MANIFESTS.items():
        raw, pin = read(bundle / "manifest.json", expected)
        manifests[bundle] = json.loads(raw)
        watched[bundle / "manifest.json"] = pin
    baseline_path = DEST / "source" / RELATIVE / "BASELINE.json"
    baseline_raw, baseline_pin = read(baseline_path, BASELINE_SHA)
    baseline = json.loads(baseline_raw)
    require(baseline["copied_files"] == len(baseline["files"]) == 122, "Baseline scope changed.")
    attestor_path = DEST / "source" / RELATIVE / "hydra_training_v5/decision_data.py"
    attestor_raw, attestor_pin = read(attestor_path, ATTESTOR_SHA)
    watched.update({baseline_path: baseline_pin, attestor_path: attestor_pin})
    for bundle in (FAILED, P6):
        read(bundle / "source" / RELATIVE / "BASELINE.json", baseline_pin)
        read(bundle / "source" / RELATIVE / "hydra_training_v5/decision_data.py", attestor_pin)
    node = next(n for n in ast.parse(attestor_raw).body if isinstance(n, ast.FunctionDef) and n.name == "verify_working_baseline")
    function_code = compile(ast.Module(body=[node], type_ignores=[]), str(attestor_path), "exec")
    additions, payloads = [], {}
    missing = []
    for record in baseline["files"]:
        relative = (Path(RELATIVE) / record["working"]).as_posix()
        require(".." not in Path(relative).parts and not Path(relative).is_absolute(), "Unsafe baseline path.")
        expected = {"bytes": record["initial_working_bytes"], "sha256": record["initial_working_sha256"]}
        existing = DEST / "source" / relative
        if relative in manifests[DEST]["files"]:
            require(manifests[DEST]["files"][relative] == expected, "Parent manifest differs from inherited baseline.")
            raw, pin = read(existing, expected)
            watched[existing] = pin
        else:
            require(not existing.exists() and not existing.is_symlink()
                    and relative not in manifests[FAILED]["files"] and Path(relative).suffix != ".py",
                    "A dependency is not an absent non-Python inherited file.")
            require(manifests[P6]["files"].get(relative) == expected, "Dependency absent from original P6 manifest.")
            source = P6 / "source" / relative
            raw, pin = read(source, expected)
            watched[source] = pin
            missing.append(record["working"])
            additions.append({"destination": relative, "remote_source": "bundles/source-data-07/source/" + relative,
                "local_source": source.relative_to(ROOT).as_posix(), "payload": "payload/" + relative,
                "before": "absent", **expected})
        payloads[record["working"]] = raw
    require(len(additions) == 20 and sum(a["bytes"] for a in additions) == 128574, "Unexpected dependency delta.")

    def checker(directory):
        namespace = {"WORKING": directory, "json": json, "hashlib": hashlib, "require": require}
        exec(function_code, namespace)
        return namespace["verify_working_baseline"]()

    failure = None
    try:
        checker(DEST / "source" / RELATIVE)
    except ValueError as error:
        failure = str(error)
    require(failure == "Inherited training source changed: " + missing[0], "Original missing-file failure did not reproduce.")
    with tempfile.TemporaryDirectory(prefix="hydra-p7-baseline-files-") as directory:
        working = Path(directory).resolve()
        write(working / "BASELINE.json", baseline_raw)
        for relative, raw in payloads.items():
            write(working / relative, raw)
        restored = checker(working)
        require(restored == {"sha256": BASELINE_SHA, "copied_files_verified": 122,
                            "source_commit": baseline["source_commit"]}, "Restored baseline differs.")
        tampered = working / missing[0]
        with tampered.open("ab") as handle:
            handle.write(b"\n")
        try:
            checker(working)
        except ValueError as error:
            require(str(error) == failure, "Wrong tamper rejection.")
        else:
            raise AssertionError("Altered dependency was accepted.")
    for row in additions:
        write(HERE / row["payload"], payloads[str(Path(row["destination"]).relative_to(RELATIVE))])
    for path, expected in watched.items():
        read(path, expected)
    require(not DENIED, "Prohibited activity was attempted.")
    packaging = {"schema": "hydra-p7-baseline-dependency-delta-v1", "status": "prepared_not_deployed",
        "parent_bundle": "combined-source-bundle-03", "parent_manifest_sha256": MANIFESTS[DEST],
        "original_dependency_bundle": "p6-source-bundle-07", "original_dependency_manifest_sha256": MANIFESTS[P6],
        "baseline_sha256": BASELINE_SHA, "attestor_sha256": ATTESTOR_SHA,
        "additions": additions, "added_files": 20, "added_bytes": 128574,
        "existing_file_replacements": 0, "code_changes": 0, "selection_changes": 0,
        "teacher_code_source_map_change_required": False, "new_bundle_manifest_required": True,
        "upload_document_payload_required": False, "remote_actions_performed": False,
        "allocation_seconds_selected": None, "new_teacher_attempt_required": True}
    save(HERE / "PACKAGING.json", packaging)
    report = {"schema": "hydra-p7-baseline-closure-pure-check-v1", "passed": True,
        "checks": 3, "original_missing_dependency_rejection": failure,
        "restored_baseline": restored, "altered_dependency_rejected": True,
        "baseline_callable_ast_sha256": hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest(),
        "inputs_unchanged": True, "inputs": {str(p.relative_to(ROOT)): v for p, v in watched.items()},
        "native_model_dataset_runtime_imports": False, "dataset_or_selection_regenerated": False,
        "model_proof_scheduler_calls": 0, "prohibited_activity_attempts": DENIED}
    save(HERE / "closure-check-01.json", report)
    print(json.dumps({"passed": True, "checks": 3, "added_files": 20, "added_bytes": 128574,
        "packaging": read(HERE / "PACKAGING.json")[1], "report": read(HERE / "closure-check-01.json")[1]}, sort_keys=True))


if __name__ == "__main__":
    main()
