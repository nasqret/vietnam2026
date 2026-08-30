#!/usr/bin/env python3
"""Bounded training-only admission/exclusion check; no comparison admission.

This reader reuses the native candidate/audit byte validator without calling
BenchmarkReference.load or the reference-readiness/human-benchmark gate. It
joins all admitted compact rows to the exact native first-occurrence projection
and checks all64 reserved roots/families/lineages/templates and before/after
states. No proof, model, Lean, approval or data publication is performed.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
import hashlib
import io
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).absolute().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "peano-lab/py")]
SOURCES = (
    "scripts/check_peano_hydra_frontier_training_inputs.py",
    "training/peano_hydra/frontier_training_launch.py",
    "training/peano_hydra/frontier_pilot_launch.py",
    "training/peano_hydra/frontier_benchmark_protocol.py",
    "training/peano_hydra/frontier_benchmark_candidates.py",
    "training/peano_hydra/frontier_benchmark_audit.py",
    "training/peano_hydra/scaling_admission.py",
    "training/peano_hydra/scaling_lineage.py",
    "training/peano_hydra/scaling_workflow.py",
    "training/peano_hydra/corrective_workflow.py",
    "training/peano_hydra/review_runtime.py",
    "training/peano_hydra/helios_runtime.py",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def digest(value):
    return sha(canonical(value))


def candidate_exclusions(bundle):
    """Exact reserved metadata/state set, after the independent byte validator."""
    from training.peano_hydra.frontier_benchmark_audit import formula_features
    routes, proofs = bundle["plan"]["routes"], bundle["proofs"]
    require(len(routes) == len(proofs) == 64, "all64 candidate routes and proofs are required")
    result = {"roots": set(), "families": set(), "lineages": set(), "names": set(),
              "templates": set(), "skeletons": set(), "states": set()}
    for route in routes:
        features = formula_features(route["statement"])
        require(features["closed"] and features["canonical_sha256"] == route["statement_sha256"],
                "candidate statement is not its exact closed canonical root")
        result["roots"].add(route["statement_sha256"])
        result["skeletons"].add(features["skeleton_sha256"])
        for key, field in (("families", "family"), ("lineages", "lineage_sha256"),
                           ("names", "name"), ("templates", "template_sha256")):
            result[key].add(route[field])
    for proof in proofs:
        require(proof["name"] in result["names"], "candidate proof is outside the reserved inventory")
        trace = proof["native_result"]["trace"]
        for index, step in enumerate(trace):
            if "qed" in step:
                require(index == len(trace) - 1 and set(step) == {"proof_size", "qed", "tactic_count", "theorem"}
                        and step["qed"] is True and step["proof_size"] == proof["proof_nodes"]
                        and step["tactic_count"] == proof["engine_steps"]
                        and step["theorem"] == proof["native_result"]["theorem"],
                        "candidate terminal QED trace record differs from its native proof")
                continue
            for field in ("goals_before", "goals_after"):
                goals = step[field]
                require(type(goals) is list and len(goals) <= 128
                        and all(type(goal) is str and len(goal.encode()) <= 65536 for goal in goals),
                        "candidate before/after state exceeds its declared bound")
                if goals:
                    result["states"].add(digest(goals))
    require(len(result["roots"]) == len(result["names"]) == 64 and len(result["families"]) == 8,
            "candidate root/name/family reservation is incomplete")
    return result


def project_and_exclude(rows, routes, exclusions, *, epoch_sha256, maximum_rows=16384):
    """Stream native rows; no model data or proof results are manufactured."""
    from training.peano_hydra.frontier_benchmark_audit import formula_features
    by_name = {row["name"]: row for row in routes}
    require(len(by_name) == len(routes) and 0 < len(routes) <= 2048,
            "native route inventory is missing or duplicated")

    @lru_cache(maxsize=32768)
    def features(source):
        return formula_features(source)

    for route in routes:
        root = features(route["statement"])
        require(root["closed"] and root["canonical_sha256"] == route["statement_sha256"],
                "native route root is not its canonical statement")
        require(route["statement_sha256"] not in exclusions["roots"]
                and route["family"] not in exclusions["families"]
                and route["lineage_sha256"] not in exclusions["lineages"]
                and route["name"] not in exclusions["names"]
                and route.get("template_sha256") not in exclusions["templates"]
                and root["skeleton_sha256"] not in exclusions["skeletons"],
                "admitted source contains a reserved root/family/lineage/template")
    first = {"train": [], "dev": []}
    duplicates = {"train": 0, "dev": 0}
    seen, route_names, count, state_observations = {}, set(), 0, 0
    for row in rows:
        count += 1
        require(count <= maximum_rows and type(row) is dict and row.get("split") in first,
                "native rows exceed the complete reviewed TRAIN/DEV boundary")
        split, name = row["split"], row.get("theorem_name")
        require(name in by_name, "native transition has no declared route")
        route = by_name[name]
        require(row.get("epoch_sha256") == epoch_sha256 == route["epoch_sha256"]
                and row.get("family") == route["family"] and row.get("lineage_sha256") == route["lineage_sha256"]
                and row.get("theorem") == route["statement"] and row["split"] == route["split"],
                "native transition changed its declared epoch/route/split")
        route_names.add(name)
        require(row.get("state_sha256") == digest(row.get("goals_before")),
                "native row before-state hash differs")
        for field in ("goals_before", "goals_after"):
            goals = row.get(field)
            require(type(goals) is list and len(goals) <= 128
                    and all(type(goal) is str and len(goal.encode()) <= 65536 for goal in goals),
                    "native before/after state exceeds its declared bound")
            if goals:
                state_observations += 1
                require(digest(goals) not in exclusions["states"],
                        "admitted native transition contains a reserved candidate before/after state")
            for goal in goals:
                _, marker, target = goal.rpartition("⊢")
                require(marker and target.strip(), "native displayed goal lacks its exact target")
                target = target.strip()
                if "?" in target:
                    continue  # An open metavariable is not a closed target; full state was still checked.
                target_features = features(target)
                require(not target_features["closed"]
                        or target_features["canonical_sha256"] not in exclusions["roots"],
                        "admitted intermediate target is a reserved candidate root")
        identity = digest([row["epoch_sha256"], row["environment_sha256"],
                           row["lineage_sha256"], row["state_sha256"], row["action"]])
        if identity in seen:
            require(seen[identity] == split, "same native state/action identity crosses TRAIN/DEV")
            duplicates[split] += 1
        else:
            seen[identity] = split
            first[split].append(digest(row))
    require(route_names == set(by_name) and count > 0, "native source did not cover every declared route")
    return first, {"native_rows": count, "routes": len(route_names), "duplicate_split_rows": duplicates,
                   "first_occurrence_split_rows": {key: len(value) for key, value in first.items()},
                   "nonempty_before_after_state_observations": state_observations,
                   "ordered_projection_sha256": {key: digest(value) for key, value in first.items()},
                   "reserved_candidate_count": 64, "reserved_family_count": 8,
                   "reserved_nonempty_states": len(exclusions["states"]),
                   "exact_reserved_overlap_count": 0,
                   "claim": "exact declared roots/templates/lineages/states only; not semantic novelty or benchmark admission"}


def check_compact_rows(raw, expected, *, split, source_manifest_sha256):
    from training.peano_hydra.scaling_workflow import decode
    from training.peano_hydra.scaling_admission import MAX_ROW_BYTES
    require(type(raw) is bytes and len(raw) <= 64 * 1024**2, "prepared split exceeds its byte cap")
    stream, count = io.BytesIO(raw), 0
    while True:
        line = stream.readline(MAX_ROW_BYTES + 1)
        if not line:
            break
        require(count < len(expected) and len(line) <= MAX_ROW_BYTES and line.endswith(b"\n"),
                "prepared split has extra/truncated/oversized rows")
        row = decode(line)
        require(type(row) is dict and row.get("split") == split
                and row.get("source_manifest_sha256") == source_manifest_sha256
                and row.get("source_transition_sha256") == expected[count],
                "prepared rows changed the native first-occurrence order or membership")
        count += 1
    require(count == len(expected), "prepared split omits admitted native transitions")
    return count


def check_request(path, expected_request_sha256):
    from training.peano_hydra import frontier_training_launch as gate
    from training.peano_hydra import frontier_benchmark_protocol as protocol
    from training.peano_hydra import scaling_admission, scaling_workflow
    path = path.absolute()
    require(path == ROOT / gate.INPUTS["training_inputs"], "training input request must use its fixed package path")
    with protocol._Inputs() as inputs:
        request, request_file = inputs.json(path, expected=expected_request_sha256, maximum=4 * 1024**2)
        require(type(request) is dict and set(request) == {
            "schema", "run_id", "preparation_manifest", "training_admission", "review_sha256",
            "benchmark_manifest", "benchmark_audit", "claim_boundary"}, "training input request fields differ")
        require(request["schema"] == gate.TRAINING_INPUTS_SCHEMA and request["run_id"] == gate.RUN_ID
                and canonical(request["claim_boundary"]) == canonical(gate.CLAIM_BOUNDARY),
                "training input request claims a different scope or benchmark authority")
        records = {}
        for name in ("preparation_manifest", "training_admission", "benchmark_manifest", "benchmark_audit"):
            desc = protocol._descriptor(request[name], name)
            require(desc["path"].startswith(gate.PACKAGE + "/"), "input descriptor is outside the fixed package")
            if name in ("preparation_manifest", "training_admission"):
                require(desc["path"] == gate.INPUTS[name], "input descriptor points to another preparation")
            records[name], observed = inputs.json(ROOT / desc["path"], expected=desc["sha256"], maximum=desc["bytes"])
            require(observed["bytes"] == desc["bytes"], "input descriptor byte count changed")
        checked = protocol._check_candidate(inputs,
            ROOT / request["benchmark_manifest"]["path"], request["benchmark_manifest"]["sha256"],
            ROOT / request["benchmark_audit"]["path"], request["benchmark_audit"]["sha256"])
        source_root = ROOT / gate.ADMITTED / "source"
        identity = scaling_admission.admission_identity(source_root)
        require(identity["review_sha256"] == request["review_sha256"]
                and identity["admission_file_sha256"] == request["training_admission"]["sha256"],
                "accepted lineage review/admission does not bind this exact training input request")
        admitted, prep = records["training_admission"], records["preparation_manifest"]
        require(admitted["run_id"] == prep["run_id"] == gate.RUN_ID
                and prep["curriculum_identity"]["review_admission"] == identity
                and prep["model"] == gate.MODEL and prep["epoch_sha256"] == gate.PINS["epoch_sha256"]
                and prep["training"]["adapter_output_dir"] == gate.ADAPTER_OUTPUT
                and checked["binding"]["epoch_sha256"] == gate.PINS["epoch_sha256"],
                "training data or candidate audit changed epoch/base/admission/output")
        source, source_file = inputs.json(source_root / "manifest.json",
                                         expected=admitted["source_manifest_sha256"], maximum=4 * 1024**2)
        audited = {(row["sha256"], row["bytes"]) for row in checked["audit"]["source_inventory"]}
        require((source_file["sha256"], source_file["bytes"]) in audited
                and (source["files"]["sft.jsonl"]["sha256"], source["files"]["sft.jsonl"]["bytes"]) in audited,
                "declared benchmark exposure audit did not inspect the complete admitted native source")
        bundle_path = (ROOT / request["benchmark_manifest"]["path"]).parent / "bundle.json"
        bundle, _ = inputs.json(bundle_path, expected=checked["binding"]["bundle_file_sha256"], maximum=16 * 1024**2)
        exclusions = candidate_exclusions(bundle)
        first, result = project_and_exclude(
            scaling_workflow.source_rows(source_root, expected_manifest_sha256=admitted["source_manifest_sha256"]),
            source["composition"]["plan"]["routes"], exclusions, epoch_sha256=gate.PINS["epoch_sha256"])
        counts = admitted["counts"]
        require(result["native_rows"] == counts["native_transition_rows"] == 15264
                and result["routes"] == counts["native_routes"] == 1152
                and result["duplicate_split_rows"] == counts["duplicate_split_rows"]
                and result["first_occurrence_split_rows"] == {"train": 12772, "dev": 2096},
                "admitted projection accounting differs from the complete native source")
        preparation_root = ROOT / gate.PREPARATION
        require(set(prep["files"]) | {"manifest.json"} == scaling_admission.PREPARATION_FILES,
                "preparation file inventory differs from the admitted complete projection")
        total_bytes = request["preparation_manifest"]["bytes"]
        for name, desc in prep["files"].items():
            require(Path(name).name == name, "prepared payload path is not one exact file")
            total_bytes += desc["bytes"]
            require(total_bytes <= scaling_admission.MAX_PREPARATION_BYTES,
                    "complete admitted preparation exceeds its original byte bound")
            observed, raw = inputs.read(preparation_root / name, expected=desc["sha256"],
                                        maximum=desc["bytes"], retain=name in ("train.jsonl", "dev.jsonl"))
            require(observed["bytes"] == desc["bytes"], "prepared payload bytes changed")
            if name in ("train.jsonl", "dev.jsonl"):
                split = name[:-6]
                checked_count = check_compact_rows(raw, first[split], split=split,
                                                  source_manifest_sha256=admitted["source_manifest_sha256"])
                require(desc["rows"] == checked_count, "prepared split descriptor row count changed")
            elif name.endswith(".jsonl"):
                require(desc["bytes"] == 0 and desc["rows"] == 0,
                        "training-only preparation unexpectedly carries preferences/discovery/quarantine rows")
        inputs.assert_unchanged()
        require(not {"torch", "transformers", "peft", "tokenizers"} & set(sys.modules),
                "training-only input checking imported a model framework")
        return {"schema": "peano-hydra-frontier-training-input-check-v1", "status": "passed",
                "request_file_sha256": request_file["sha256"], "run_id": gate.RUN_ID,
                "preparation_manifest_sha256": request["preparation_manifest"]["sha256"],
                "admission": identity, "candidate_binding": checked["binding"], "exclusions": result,
                "preparation_bytes": total_bytes, "claim_boundary": dict(gate.CLAIM_BOUNDARY),
                "model_weights_loaded": False, "cuda_initialized": False,
                "native_proofs_replayed_by_this_check": False, "benchmark_or_reference_admission": False}


def main():
    from training.peano_hydra import frontier_training_launch as gate
    from training.peano_hydra import review_runtime, corrective_workflow
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--request", type=Path)
    parser.add_argument("--expected-request-sha256")
    parser.add_argument("--output", type=Path, help="optional fresh CPU-check receipt; never an approval")
    args = parser.parse_args()
    try:
        if args.worker:
            require(sys.argv[1:] == ["--worker"], "internal worker accepts only its bounded stdin request")
            value = gate.decode(sys.stdin.buffer.read(8193))
            require(set(value) == {"request", "expected_request_sha256"}, "worker request fields differ")
            result = check_request(Path(value["request"]), value["expected_request_sha256"])
        else:
            require(args.request is not None and type(args.expected_request_sha256) is str
                    and gate.HEX.fullmatch(args.expected_request_sha256), "exact input request and external raw SHA required")
            before = {name: sha((ROOT / name).read_bytes()) for name in SOURCES}
            limits = review_runtime.ProcessLimits(wall_seconds=180, cpu_seconds=120,
                                                  rss_bytes=1024**3, output_bytes=256 * 1024)
            process = review_runtime.run_bounded(
                (sys.executable, "-I", "-B", "-X", "pycache_prefix=/dev/null", str(Path(__file__).absolute()), "--worker"),
                cwd=ROOT, limits=limits, input_bytes=canonical({"request": str(args.request.absolute()),
                                                        "expected_request_sha256": args.expected_request_sha256}),
                runtime_library_paths=corrective_workflow.runtime_libraries())
            after = {name: sha((ROOT / name).read_bytes()) for name in SOURCES}
            passed = before == after and process["reason"] == "exited" and process["returncode"] == 0
            result = {"schema": "peano-hydra-frontier-training-input-process-v1",
                      "status": "passed" if passed else "failed",
                      "source_files": before, "source_files_after": after, "sources_unchanged": before == after,
                      "result": gate.decode(process["stdout"].encode()) if passed else None, "process": process,
                      "allocation_performed": False, "approval_created": False}
            if args.output is not None:
                output = args.output.absolute()
                require(output not in (ROOT / gate.REQUEST, ROOT / gate.APPROVAL),
                        "the input checker never writes resource request or approval")
                fd = gate.directory(output.parent)
                try:
                    child = os.open(output.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
                    with os.fdopen(child, "wb") as stream:
                        stream.write(canonical(result) + b"\n")
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.fsync(fd)
                finally:
                    os.close(fd)
            require(passed, "bounded training input check failed: " + process["reason"] + "; " + process["stderr"][:2000])
            require(result["result"]["status"] == "passed", "training input worker did not pass")
        print(canonical(result).decode(), flush=True)
        return 0
    except (ValueError, TypeError, KeyError, OSError, RuntimeError) as error:
        print("frontier-training-inputs: " + " ".join(str(error).split())[:3000], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
