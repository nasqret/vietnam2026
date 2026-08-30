#!/usr/bin/env python3
"""Prepare or recheck a bounded, CPU-only authority-aware Hydra experiment.

No mode loads model weights, starts training, transfers data, submits jobs, or
approves a research benchmark. Each native/tokenizer stage runs in a separate
owned process with fixed limits. Interrupted output is retained, never repaired
in place or presented as a complete readiness bundle.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import stat
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.peano_hydra.review_runtime import (  # noqa: E402
    ProcessLimits, run_bounded, validate_process_record,
)

SCHEMA = "peano-hydra-authority-readiness-v1"
LIMITS = ProcessLimits(wall_seconds=45, cpu_seconds=30, rss_bytes=1024**3,
                       output_bytes=4 * 1024**2)
MAX_JSON_BYTES = 4 * 1024**2
MAX_REQUEST_BYTES = 64 * 1024
PINNED_TOKENIZER_REFERENCE = ROOT / "artifacts/peano-hydra/capacity-2026-08-27/training-manifest.json"
PINNED_TOKENIZER_REFERENCE_SHA256 = "723d0f8109c0272774f445c552d781c8e64cadfa50d0516246eb0fa2fd31a955"


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _same(left: object, right: object) -> bool:
    """Strict JSON equality: booleans, integers, and floats are not aliases."""
    return _canonical(left) == _canonical(right)


def _decode(raw: bytes, *, maximum: int = MAX_JSON_BYTES) -> dict[str, object]:
    if len(raw) > maximum:
        raise ValueError("authority workflow JSON exceeds its byte reservation")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate authority workflow JSON field")
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError(f"non-finite authority workflow JSON: {value}")

    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)
    if type(value) is not dict:
        raise ValueError("authority workflow JSON must be one object")
    return value


def _read(path: Path) -> bytes:
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_JSON_BYTES:
            raise ValueError("authority workflow input is not a bounded regular JSON file")
        raw = stream.read(MAX_JSON_BYTES + 1)
        after = os.fstat(stream.fileno())
    if len(raw) != before.st_size or (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
        after.st_size, after.st_mtime_ns, after.st_ctime_ns
    ):
        raise ValueError("authority workflow input changed while reading")
    return raw


def _write_new(path: Path, value: dict[str, object]) -> None:
    raw = (json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2) + "\n").encode()
    if len(raw) > MAX_JSON_BYTES:
        raise ValueError("authority workflow output exceeds its byte reservation")
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def _pinned_tokenizer_descriptor(saved: dict[str, object]) -> dict[str, object]:
    """Use a repository-pinned production receipt, not a caller's model label."""
    raw = _read(PINNED_TOKENIZER_REFERENCE)
    if hashlib.sha256(raw).hexdigest() != PINNED_TOKENIZER_REFERENCE_SHA256:
        raise ValueError("trusted pinned-tokenizer reference bytes changed")
    reference = _decode(raw)
    descriptor = reference.get("tokenizer")
    if (type(descriptor) is not dict or not _same(saved.get("model"), reference.get("model"))
        or not _same(saved.get("tokenizer"), descriptor)):
        raise ValueError("tokenizer differs from the trusted pinned-Qwen artifact inventory")
    return descriptor


def _bind_bundled_source(directory: Path, preparation: dict[str, object]) -> None:
    """Join the exact source that was replayed to the source shown to the user."""
    identity = preparation.get("source")
    if type(identity) is not dict or type(identity.get("directory")) is not str:
        raise ValueError("preparation has no exact bundled-source identity")
    declared = Path(identity["directory"])
    if not declared.is_absolute():
        declared = ROOT / declared
    if declared.absolute() != directory / "source":
        raise ValueError("preparation redirects verification away from the bundled source")
    names = {"manifest.json": "manifest_sha256", "epoch.json": "epoch_file_sha256",
             "sft.jsonl": "sft_sha256", "preferences.jsonl": "preferences_sha256",
             "discovery.jsonl": "discovery_sha256"}
    for name, field in names.items():
        path = directory / "source" / name
        from training.peano_hydra.review_runtime import hash_file

        if hash_file(path, maximum=64 * 1024**2)["sha256"] != identity.get(field):
            raise ValueError(f"preparation changed its bundled source file: {name}")
    curriculum = preparation.get("curriculum_identity")
    if type(curriculum) is not dict or curriculum.get("source_manifest_sha256") != identity["manifest_sha256"]:
        raise ValueError("curriculum identity differs from the exact bundled source")


def _bundle_inventory(directory: Path, expected_files: set[str]) -> None:
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("authority bundle must be one real directory")
    allowed = expected_files | {"source", "preparation"}
    seen = set()
    with os.scandir(directory) as entries:
        for entry in entries:
            if entry.name not in allowed or entry.is_symlink() or len(seen) >= len(allowed):
                raise ValueError("authority bundle inventory changed or exceeds its entry bound")
            regular = (entry.is_file(follow_symlinks=False) if entry.name in expected_files
                       else entry.is_dir(follow_symlinks=False))
            if not regular:
                raise ValueError("authority bundle contains a non-regular entry")
            seen.add(entry.name)
    if seen != allowed:
        raise ValueError("authority bundle inventory is incomplete")


def _token_audit(preparation: Path, tokenizer_manifest: Path) -> dict[str, object]:
    # Transformers is used solely as the pinned tokenizer implementation.
    # Disable framework discovery before its first import; never initialize CUDA.
    for name in ("USE_TORCH", "USE_TF", "USE_FLAX"):
        os.environ[name] = "0"
    if "torch" in sys.modules:
        raise ValueError("token audit must start without an imported model framework")
    from training.peano_hydra import posttrain
    from training.peano_policy.authority import AUTHORITY_PRIMITIVE_PROFILE, AuthorityTokenConstraint
    from training.peano_policy.budget import enforce_token_budget, tokenize_split, tokenizer_identity_record
    from training.peano_policy.manifest import verify_artifact_directory

    prepared = posttrain.load_preparation(preparation)
    if prepared.manifest.get("authority_profile") != AUTHORITY_PRIMITIVE_PROFILE:
        raise ValueError("token audit requires the separately replayed authority preparation")
    raw = _read(tokenizer_manifest)
    saved = _decode(raw)
    if saved.get("model") != {"model_id": posttrain.BASE_MODEL_ID, "revision": posttrain.BASE_MODEL_REVISION}:
        raise ValueError("tokenizer manifest does not bind the exact reviewed Qwen revision")
    descriptor = _pinned_tokenizer_descriptor(saved)
    directory = verify_artifact_directory(tokenizer_manifest.parent, descriptor, "tokenizer")
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(str(directory), use_fast=True, trust_remote_code=False,
                                               local_files_only=True)
    if tokenizer.eos_token_id is None:
        raise ValueError("the saved tokenizer has no EOS token")
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    identity = tokenizer_identity_record(tokenizer, model_id=posttrain.BASE_MODEL_ID,
                                         revision=posttrain.BASE_MODEL_REVISION)
    constraint = AuthorityTokenConstraint(tokenizer, posttrain._source_authority_environment(prepared.source),
                                          prompt_length=0, max_new_tokens=prepared.config.generation.max_new_tokens)

    class Prefix(list):
        def tolist(self):
            return list(self)

    exposure = {}
    reachable_rows = 0
    maximum_target_tokens = 0
    for split, rows, maximum, squared in (
        ("train", prepared.train_rows, posttrain.MAX_TRAIN_TOKENS, posttrain.MAX_TRAIN_SQUARED_TOKENS),
        ("dev", prepared.development_rows, posttrain.MAX_DEV_TOKENS, posttrain.MAX_DEV_SQUARED_TOKENS),
    ):
        examples = posttrain._proof_examples(prepared, rows, split=split)
        features, counts = tokenize_split(examples, tokenizer, role=split,
                                         max_length=prepared.config.data.max_length,
                                         tokenizer_identity=identity)
        enforce_token_budget(counts, max_total_tokens=maximum, max_sum_squared_tokens=squared,
                             max_supervised_tokens=prepared.config.generation.max_new_tokens)
        for feature in features:
            targets = [token for token in feature["labels"] if token != -100]
            prefix = Prefix()
            for token in targets:
                if token not in constraint(0, prefix):
                    raise ValueError("a supervised target token is unreachable under the exact authority decoder")
                prefix.append(token)
            reachable_rows += 1
            maximum_target_tokens = max(maximum_target_tokens, len(targets))
        del features
        exposure[split] = counts
    verify_artifact_directory(tokenizer_manifest.parent, saved["tokenizer"], "tokenizer")
    if _read(tokenizer_manifest) != raw or "torch" in sys.modules:
        raise ValueError("tokenizer identity changed or a model framework entered the audit")
    report = {
        "schema": "peano-hydra-authority-token-audit-v1", "status": "passed",
        "preparation_manifest_sha256": hashlib.sha256(prepared.payloads["manifest.json"]).hexdigest(),
        "tokenizer_manifest_path": str(tokenizer_manifest),
        "tokenizer_manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "trusted_tokenizer_reference_sha256": PINNED_TOKENIZER_REFERENCE_SHA256,
        "tokenizer_artifacts": saved["tokenizer"], "tokenizer": identity,
        "local_runtime": {"python": sys.version.split()[0],
                          "transformers": importlib.metadata.version("transformers"),
                          "tokenizers": importlib.metadata.version("tokenizers")},
        "limits": {"max_sequence_tokens": prepared.config.data.max_length,
                   "max_supervised_tokens": prepared.config.generation.max_new_tokens},
        "token_exposure": exposure, "production_runtime_attestation": False,
        "decoder_target_reachability": {"rows": reachable_rows, "all_target_tokens_and_eos_reachable": True,
                                        "max_supervised_tokens": maximum_target_tokens,
                                        "all_targets_within_capacity_64_token_bound": maximum_target_tokens <= 64},
        "model_weights_loaded": False, "cuda_initialized": False, "research_claim_eligible": False,
    }
    report["audit_sha256"] = _digest(report)
    return report


def _worker(request: dict[str, object]) -> dict[str, object]:
    stage = request.get("stage")
    fields = {
        "plan": {"stage"}, "source": {"stage", "output"},
        "preparation": {"stage", "source", "output", "run_id"},
        "preflight": {"stage", "preparation"}, "capacity-plan": {"stage", "preparation"},
        "token-audit": {"stage", "preparation", "tokenizer_manifest"},
    }
    if stage not in fields or set(request) != fields[stage]:
        raise ValueError("invalid authority worker stage or fields")
    if any(type(value) is not str or not value or len(value) > 4096 for value in request.values()):
        raise ValueError("invalid authority worker text input")
    if stage == "plan":
        from training.peano_hydra.composition import composition_profile_record

        return composition_profile_record()
    if stage == "source":
        from training.peano_hydra.composition import build_composition_source, publish_composition_source

        source = build_composition_source()
        directory = publish_composition_source(source, Path(request["output"]))
        return {"source_directory": str(directory), "epoch_sha256": source.epoch.epoch_sha256,
                "manifest_sha256": hashlib.sha256(source.payloads["manifest.json"]).hexdigest(),
                "verified_routes": source.manifest["composition"]["verified_route_count"],
                "verified_transitions": len(source.curriculum.transitions), "model_generated": False}
    from training.peano_hydra import posttrain

    if stage == "preparation":
        prepared = posttrain.prepare_posttraining(Path(request["source"]), Path(request["output"]),
                                                 run_id=request["run_id"])
        posttrain.publish_preparation(prepared)
        return {"preparation_directory": str(prepared.output_directory),
                "manifest_sha256": hashlib.sha256(prepared.payloads["manifest.json"]).hexdigest(),
                "training_rows": len(prepared.train_rows), "development_rows": len(prepared.development_rows),
                "quarantine_rows": prepared.manifest["held_out"]["quarantine_rows"],
                "adapter_output_dir": prepared.config.run.output_dir}
    if stage == "preflight":
        return posttrain.preflight(Path(request["preparation"]))
    if stage == "capacity-plan":
        from training.peano_hydra.capacity import build_capacity_plan
        from training.peano_policy.authority import AUTHORITY_PRIMITIVE_PROFILE

        return build_capacity_plan(Path(request["preparation"]),
                                   authority_profile=AUTHORITY_PRIMITIVE_PROFILE).to_dict()
    return _token_audit(Path(request["preparation"]), Path(request["tokenizer_manifest"]))


def _stage(request: dict[str, object], *, python: Path, output: Path | None = None) -> dict[str, object]:
    command = (str(python), str(Path(__file__).absolute()), "--worker")
    payload = _canonical(request)
    print(f"authority: {request['stage']} (CPU only, wall<=45s, CPU<=30s, RSS<=1GiB)",
          file=sys.stderr, flush=True)
    receipt = run_bounded(command, cwd=ROOT, limits=LIMITS, input_bytes=payload)
    if output is not None:
        _write_new(output / f"{request['stage']}-process.json", receipt)
    try:
        validate_process_record(receipt, command=command, limits=LIMITS, input_bytes=payload, success_codes=(0,))
    except ValueError as error:
        detail = " ".join(str(receipt.get("stderr", "")).split())[:1500]
        raise ValueError(f"{request['stage']} failed ({receipt.get('reason')}, exit {receipt.get('returncode')}): {detail or error}") from error
    result = _decode(receipt["stdout"].encode())
    if output is not None:
        _write_new(output / f"{request['stage']}.json", result)
    return result


def _readiness_record(output: Path, stages: dict[str, dict[str, object]],
                      files: dict[str, str]) -> dict[str, object]:
    source, preparation, preflight, plan = (stages[name] for name in (
        "source", "preparation", "preflight", "capacity-plan"
    ))
    if (source["epoch_sha256"] != preflight["epoch_sha256"]
        or source["epoch_sha256"] != plan["epoch_sha256"]
        or preparation["manifest_sha256"] != plan["preparation_manifest_sha256"]
        or preparation["training_rows"] != preflight["training_rows"]
        or preparation["development_rows"] != preflight["development_rows"]
        or preparation["adapter_output_dir"] != preflight["adapter_output_dir"]):
        raise ValueError("authority stages disagree about their exact data or epoch")
    if "token-audit" in stages and stages["token-audit"]["preparation_manifest_sha256"] != preparation["manifest_sha256"]:
        raise ValueError("token audit changed its exact preparation")
    curriculum = preflight.get("curriculum_identity")
    if type(curriculum) is not dict or curriculum.get("source_manifest_sha256") != source["manifest_sha256"]:
        raise ValueError("preflight verified a different source from the displayed teacher source")
    result = {
        "schema": SCHEMA, "status": "prepared", "complete": True,
        "output_directory": str(output), "stage_files": files,
        "source_manifest_sha256": source["manifest_sha256"],
        "preparation_manifest_sha256": preparation["manifest_sha256"],
        "capacity_plan_sha256": plan["plan_sha256"],
        "verified_teacher_routes": source["verified_routes"],
        "training_rows": preparation["training_rows"],
        "development_rows": preparation["development_rows"],
        "expected_optimizer_steps": preflight["expected_optimizer_steps"],
        "token_budget_checked": "token-audit" in stages,
        "training_readiness": "cpu-token-budget-passed" if "token-audit" in stages else "token-audit-required",
        "resource_limits_per_stage": LIMITS.to_dict(), "maximum_concurrent_workers": 1,
        "model_training_authorized": False, "model_trained": False, "cuda_initialized": False,
        "human_review_complete": False, "sealed_benchmark": False, "research_claim_eligible": False,
        "public_correlated_exposed_data": True,
        "next_boundary": "review this exposed-data profile and authorize a separately bounded GPU run",
    }
    result["readiness_sha256"] = _digest(result)
    return result


def _prepare(output: Path, *, run_id: str, tokenizer_manifest: Path | None,
             tokenizer_python: Path) -> dict[str, object]:
    if output.exists() or output.is_symlink() or output == ROOT or output in ROOT.parents:
        raise ValueError("choose a fresh dedicated output directory; existing data is never replaced")
    if not output.parent.is_dir() or output.parent.is_symlink():
        raise ValueError("output parent must be an existing real directory")
    output.mkdir()
    native_python = Path(sys.executable)
    stages = {}
    requests = (
        {"stage": "source", "output": str(output / "source")},
        {"stage": "preparation", "source": str(output / "source"),
         "output": str(output / "preparation"), "run_id": run_id},
        {"stage": "preflight", "preparation": str(output / "preparation")},
        {"stage": "capacity-plan", "preparation": str(output / "preparation")},
    )
    for request in requests:
        stages[request["stage"]] = _stage(request, python=native_python, output=output)
    _bind_bundled_source(output, _decode(_read(output / "preparation/manifest.json")))
    if tokenizer_manifest is not None:
        stages["token-audit"] = _stage(
            {"stage": "token-audit", "preparation": str(output / "preparation"),
             "tokenizer_manifest": str(tokenizer_manifest)}, python=tokenizer_python, output=output,
        )
    files = {name: hashlib.sha256(_read(output / name)).hexdigest()
             for stage in stages for name in (f"{stage}.json", f"{stage}-process.json")}
    result = _readiness_record(output, stages, files)
    _write_new(output / "readiness.json", result)
    return result


def _verify(directory: Path, *, tokenizer_manifest: Path | None,
            tokenizer_python: Path) -> dict[str, object]:
    raw = _read(directory / "readiness.json")
    saved = _decode(raw)
    unsigned = dict(saved)
    signed = unsigned.pop("readiness_sha256", None)
    if saved.get("schema") != SCHEMA or saved.get("complete") is not True or signed != _digest(unsigned):
        raise ValueError("saved authority readiness schema, completeness, or digest changed")
    if saved.get("output_directory") != str(directory) or saved.get("model_training_authorized") is not False:
        raise ValueError("saved readiness changed its location or approval boundary")
    if type(saved.get("token_budget_checked")) is not bool:
        raise ValueError("saved token-audit status is not a Boolean")
    if saved["token_budget_checked"] and tokenizer_manifest is None:
        raise ValueError("full verification requires explicit --tokenizer-manifest used by the saved token audit")
    stages = ("source", "preparation", "preflight", "capacity-plan") + (
        ("token-audit",) if saved.get("token_budget_checked") is True else ()
    )
    expected = {name for stage in stages for name in (f"{stage}.json", f"{stage}-process.json")}
    if type(saved.get("stage_files")) is not dict or set(saved["stage_files"]) != expected:
        raise ValueError("saved authority readiness changed its exact stage inventory")
    _bundle_inventory(directory, expected | {"readiness.json"})
    for name, digest in saved["stage_files"].items():
        if hashlib.sha256(_read(directory / name)).hexdigest() != digest:
            raise ValueError(f"saved authority stage changed: {name}")
    results = {stage: _decode(_read(directory / f"{stage}.json")) for stage in stages}
    source_raw = _read(directory / "source/manifest.json")
    source = _decode(source_raw)
    preparation_raw = _read(directory / "preparation/manifest.json")
    preparation = _decode(preparation_raw)
    _bind_bundled_source(directory, preparation)
    requests = {
        "source": {"stage": "source", "output": str(directory / "source")},
        "preparation": {"stage": "preparation", "source": str(directory / "source"),
                        "output": str(directory / "preparation"), "run_id": preparation["run_id"]},
        "preflight": {"stage": "preflight", "preparation": str(directory / "preparation")},
        "capacity-plan": {"stage": "capacity-plan", "preparation": str(directory / "preparation")},
        "token-audit": {"stage": "token-audit", "preparation": str(directory / "preparation"),
                        "tokenizer_manifest": str(tokenizer_manifest)},
    }
    for stage in stages:
        receipt = _decode(_read(directory / f"{stage}-process.json"))
        command = receipt.get("command")
        if (type(command) is not list or len(command) != 3 or type(command[0]) is not str
            or not Path(command[0]).is_absolute()
            or command[1:] != [str(Path(__file__).absolute()), "--worker"]):
            raise ValueError("saved receipt changed its authority worker command")
        # The historical executable is inspected as text, never executed.
        # Fresh workers use only the current or explicitly selected Python.
        validate_process_record(receipt, command=tuple(command), limits=LIMITS,
                                input_bytes=_canonical(requests[stage]), success_codes=(0,))
        if not _same(_decode(receipt["stdout"].encode()), results[stage]):
            raise ValueError("saved stage differs from its exact worker output")
    expected_source = {
        "source_directory": str(directory / "source"), "epoch_sha256": source["epoch_sha256"],
        "manifest_sha256": hashlib.sha256(source_raw).hexdigest(),
        "verified_routes": source["composition"]["verified_route_count"],
        "verified_transitions": source["transition_count"], "model_generated": False,
    }
    expected_preparation = {
        "preparation_directory": str(directory / "preparation"),
        "manifest_sha256": hashlib.sha256(preparation_raw).hexdigest(),
        "training_rows": preparation["splits"]["train"]["rows"],
        "development_rows": preparation["splits"]["dev"]["rows"],
        "quarantine_rows": preparation["held_out"]["quarantine_rows"],
        "adapter_output_dir": preparation["training"]["adapter_output_dir"],
    }
    if not _same(results["source"], expected_source) or not _same(results["preparation"], expected_preparation):
        raise ValueError("saved source/preparation stage changed its exact manifest identity")
    if not _same(saved, _readiness_record(directory, results, saved["stage_files"])):
        raise ValueError("saved readiness summary differs from its exact stage evidence")
    native_python = Path(sys.executable)
    for stage in ("preflight", "capacity-plan"):
        fresh = _stage({"stage": stage, "preparation": str(directory / "preparation")}, python=native_python)
        if not _same(fresh, results[stage]):
            raise ValueError(f"independently regenerated {stage} differs from saved evidence")
    if saved["token_budget_checked"]:
        fresh = _stage({"stage": "token-audit", "preparation": str(directory / "preparation"),
                        "tokenizer_manifest": str(tokenizer_manifest)}, python=tokenizer_python)
        if not _same(fresh, results["token-audit"]):
            raise ValueError("independently tokenized training inputs differ from saved evidence")
    if (_read(directory / "readiness.json") != raw
        or _read(directory / "source/manifest.json") != source_raw
        or _read(directory / "preparation/manifest.json") != preparation_raw):
        raise ValueError("saved readiness changed during independent verification")
    return {"schema": SCHEMA, "status": "verified", "readiness_sha256": signed,
            "verified_teacher_routes": saved["verified_teacher_routes"],
            "token_budget_checked": saved["token_budget_checked"],
            "model_training_authorized": False, "model_trained": False,
            "cuda_initialized": False, "research_claim_eligible": False}


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments == ["--worker"]:
        try:
            result = _worker(_decode(sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1), maximum=MAX_REQUEST_BYTES))
            sys.stdout.buffer.write(_canonical(result) + b"\n")
            return 0
        except (ValueError, TypeError, KeyError, OSError, RuntimeError, ImportError) as error:
            print(f"authority-worker: {' '.join(str(error).split())[:3000]}", file=sys.stderr)
            return 2
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--plan", action="store_true", help="show fixed authored exercises without proving or writing (default)")
    modes.add_argument("--prepare", action="store_true", help="publish one fresh CPU-verified experiment bundle")
    modes.add_argument("--verify", type=Path, metavar="DIRECTORY", help="read-only independent replay of a completed bundle")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--run-id", default="authority-composition-v1")
    parser.add_argument("--tokenizer-manifest", type=Path,
                        help="saved manifest binding tokenizer files and the exact pinned Qwen revision; weights are not read")
    parser.add_argument("--tokenizer-python", type=Path, default=Path(sys.executable),
                        help="explicit existing Python with transformers/tokenizers; never installed automatically")
    args = parser.parse_args(arguments)
    if args.prepare != (args.output_dir is not None):
        parser.error("--prepare requires a fresh --output-dir; planning and verification do not write")
    if not args.prepare and args.verify is None and args.tokenizer_manifest is not None:
        parser.error("token audit belongs to --prepare or --verify, not planning")
    try:
        python = args.tokenizer_python.expanduser().absolute()
        if not python.is_file() or not os.access(python, os.X_OK):
            raise ValueError("select an existing executable --tokenizer-python")
        tokenizer = None if args.tokenizer_manifest is None else args.tokenizer_manifest.expanduser().absolute()
        if args.prepare:
            result = _prepare(args.output_dir.expanduser().absolute(), run_id=args.run_id,
                              tokenizer_manifest=tokenizer, tokenizer_python=python)
        elif args.verify is not None:
            result = _verify(args.verify.expanduser().absolute(), tokenizer_manifest=tokenizer, tokenizer_python=python)
        else:
            result = _stage({"stage": "plan"}, python=Path(sys.executable))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2))
        return 0
    except (ValueError, TypeError, KeyError, OSError, RuntimeError) as error:
        print(f"hydra-authority: {' '.join(str(error).split())[:3000]}", file=sys.stderr)
        if args.prepare:
            print("Any partial output and process receipts are retained; choose a new directory after fixing the failure.",
                  file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
