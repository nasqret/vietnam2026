#!/usr/bin/env python3
"""Prepare a separately bounded, CPU-only scaled native Hydra experiment.

This is not the small composition pilot: it has its own source schema,
readiness record, and resource reservation. It cannot train, install a model,
submit a scheduler job, or turn exposed teacher families into a sealed test.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import prepare_peano_hydra_authority as pilot  # noqa: E402
from training.peano_hydra.review_runtime import (  # noqa: E402
    ProcessLimits, run_bounded, validate_process_record,
)

SCHEMA = "peano-hydra-authority-scale-readiness-v1"
PROFILE = "peano-hydra-authority-scale-v1"
SOURCE_SCHEMA = "peano-hydra-native-composition-scale-source-v1"
LIMITS = ProcessLimits(wall_seconds=180, cpu_seconds=120, rss_bytes=2 * 1024**3,
                       output_bytes=4 * 1024**2)
STAGES = ("source", "preparation", "preflight", "capacity-plan")


def _require_scaled_source(directory: Path) -> dict[str, object]:
    record = pilot._decode(pilot._read(directory / "manifest.json"))
    if record.get("schema") != SOURCE_SCHEMA:
        raise ValueError("scaled preparation requires its separately versioned native source")
    return record


def _require_scaled_preparation(directory: Path) -> None:
    record = pilot._decode(pilot._read(directory / "manifest.json"))
    source = record.get("source")
    if type(source) is not dict or type(source.get("directory")) is not str:
        raise ValueError("scaled preparation has no exact source directory")
    path = Path(source["directory"])
    _require_scaled_source(path if path.is_absolute() else ROOT / path)


def _worker(request: dict[str, object]) -> dict[str, object]:
    fields = {
        "plan": {"stage"}, "source": {"stage", "output"},
        "preparation": {"stage", "source", "output", "run_id"},
        "preflight": {"stage", "preparation"},
        "capacity-plan": {"stage", "preparation"},
        "token-audit": {"stage", "preparation", "tokenizer_manifest"},
    }
    stage = request.get("stage")
    if type(stage) is not str or stage not in fields or set(request) != fields[stage]:
        raise ValueError("invalid scaled authority worker stage or fields")
    if any(type(value) is not str or not value or len(value) > 4096 for value in request.values()):
        raise ValueError("invalid scaled authority worker text input")
    if stage == "plan":
        from training.peano_hydra.composition_scale import scaled_composition_profile_record

        return scaled_composition_profile_record()
    if stage == "source":
        from training.peano_hydra.composition_scale import (
            build_scaled_composition_source, publish_scaled_composition_source,
        )

        source = build_scaled_composition_source()
        directory = publish_scaled_composition_source(source, Path(request["output"]))
        return {
            "source_directory": str(directory), "source_schema": SOURCE_SCHEMA,
            "epoch_sha256": source.epoch.epoch_sha256,
            "manifest_sha256": hashlib.sha256(source.payloads["manifest.json"]).hexdigest(),
            "verified_routes": source.manifest["composition"]["verified_route_count"],
            "verified_transitions": len(source.curriculum.transitions),
            "model_generated": False,
        }
    if stage == "preparation":
        _require_scaled_source(Path(request["source"]))
    else:
        _require_scaled_preparation(Path(request["preparation"]))
    if stage == "token-audit":
        # The native-only CPU nodes and ARM GPU nodes use different Python
        # installations. Audit in the explicitly selected existing tokenizer
        # interpreter, before weights, with bounded single-threaded libraries.
        for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
            os.environ[name] = "1"
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
    return pilot._worker(request)


def _stage(request: dict[str, object], *, python: Path,
           output: Path | None = None, receipt_output: Path | None = None) -> dict[str, object]:
    if output is not None and receipt_output is not None:
        raise ValueError("choose one bounded receipt destination")
    command = (str(python), str(Path(__file__).absolute()), "--worker")
    payload = pilot._canonical(request)
    print(f"authority-scale: {request['stage']} (CPU only, wall<=180s, CPU<=120s, RSS<=2GiB)",
          file=sys.stderr, flush=True)
    library_paths = ()
    if os.environ.get("SLURM_JOB_ID") is not None:
        from training.peano_hydra.helios_runtime import reviewed_runtime_library_paths

        library_paths = reviewed_runtime_library_paths()
    runtime_options = {"runtime_library_paths": library_paths} if library_paths else {}
    receipt = run_bounded(command, cwd=ROOT, limits=LIMITS, input_bytes=payload, **runtime_options)
    if output is not None:
        pilot._write_new(output / f"{request['stage']}-process.json", receipt)
    elif receipt_output is not None:
        pilot._write_new(receipt_output, receipt)
    try:
        validate_process_record(receipt, command=command, limits=LIMITS,
                                input_bytes=payload, success_codes=(0,), **runtime_options)
    except ValueError as error:
        detail = " ".join(str(receipt.get("stderr", "")).split())[:1500]
        raise ValueError(f"{request['stage']} failed ({receipt.get('reason')}, exit "
                         f"{receipt.get('returncode')}): {detail or error}") from error
    result = pilot._decode(receipt["stdout"].encode())
    if output is not None:
        pilot._write_new(output / f"{request['stage']}.json", result)
    return result


def _readiness_record(output: Path, stages: dict[str, dict[str, object]],
                      files: dict[str, str]) -> dict[str, object]:
    if stages["source"].get("source_schema") != SOURCE_SCHEMA:
        raise ValueError("scaled readiness cannot relabel the small pilot source")
    result = pilot._readiness_record(output, stages, files)
    result.pop("readiness_sha256")
    result.update({
        "schema": SCHEMA, "profile": PROFILE, "source_schema": SOURCE_SCHEMA,
        "resource_limits_per_stage": LIMITS.to_dict(),
        "training_initialization": "fresh-pinned-base-with-new-lora",
        "training_schedule": "one-complete-epoch-no-resume-no-checkpoint-selection",
        "operational_authorization": "separate-explicit-user-request-and-launch-receipt",
        "next_boundary": "the separately authorized bounded Helios experiment; this data receipt grants no authority",
    })
    result["readiness_sha256"] = pilot._digest(result)
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
    pilot._bind_bundled_source(output, pilot._decode(pilot._read(output / "preparation/manifest.json")))
    if tokenizer_manifest is not None:
        stages["token-audit"] = _stage(
            {"stage": "token-audit", "preparation": str(output / "preparation"),
             "tokenizer_manifest": str(tokenizer_manifest)}, python=tokenizer_python, output=output,
        )
    files = {name: hashlib.sha256(pilot._read(output / name)).hexdigest()
             for stage in stages for name in (f"{stage}.json", f"{stage}-process.json")}
    result = _readiness_record(output, stages, files)
    pilot._write_new(output / "readiness.json", result)
    return result


def _verify(directory: Path, *, tokenizer_manifest: Path | None,
            tokenizer_python: Path) -> dict[str, object]:
    raw = pilot._read(directory / "readiness.json")
    saved = pilot._decode(raw)
    unsigned = dict(saved)
    signed = unsigned.pop("readiness_sha256", None)
    if (saved.get("schema") != SCHEMA or saved.get("profile") != PROFILE
        or saved.get("complete") is not True or signed != pilot._digest(unsigned)):
        raise ValueError("saved scaled readiness schema, completeness, or digest changed")
    if saved.get("output_directory") != str(directory) or saved.get("model_training_authorized") is not False:
        raise ValueError("saved scaled readiness changed its location or authorization boundary")
    if type(saved.get("token_budget_checked")) is not bool:
        raise ValueError("saved token-audit status is not a Boolean")
    if saved["token_budget_checked"] and tokenizer_manifest is None:
        raise ValueError("full verification requires the explicit saved --tokenizer-manifest")
    stages = STAGES + (("token-audit",) if saved["token_budget_checked"] else ())
    expected = {name for stage in stages for name in (f"{stage}.json", f"{stage}-process.json")}
    if type(saved.get("stage_files")) is not dict or set(saved["stage_files"]) != expected:
        raise ValueError("saved scaled readiness changed its exact stage inventory")
    pilot._bundle_inventory(directory, expected | {"readiness.json"})
    for name, digest in saved["stage_files"].items():
        if hashlib.sha256(pilot._read(directory / name)).hexdigest() != digest:
            raise ValueError(f"saved scaled stage changed: {name}")
    results = {stage: pilot._decode(pilot._read(directory / f"{stage}.json")) for stage in stages}
    source = _require_scaled_source(directory / "source")
    source_raw = pilot._read(directory / "source/manifest.json")
    preparation_raw = pilot._read(directory / "preparation/manifest.json")
    preparation = pilot._decode(preparation_raw)
    pilot._bind_bundled_source(directory, preparation)
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
        receipt = pilot._decode(pilot._read(directory / f"{stage}-process.json"))
        command = receipt.get("command")
        if (type(command) is not list or len(command) != 3 or type(command[0]) is not str
            or not Path(command[0]).is_absolute()
            or command[1:] != [str(Path(__file__).absolute()), "--worker"]):
            raise ValueError("saved receipt changed its scaled worker command")
        runtime_options = {}
        if "runtime_libraries" in receipt:
            from training.peano_hydra.review_runtime import validate_runtime_library_record

            # Historical central-module paths are data, never instructions to
            # load libraries on this verification machine. Fresh workers use
            # only the current explicitly checked execution environment.
            library_paths = validate_runtime_library_record(receipt["runtime_libraries"])
            runtime_options["runtime_library_paths"] = library_paths
        validate_process_record(receipt, command=tuple(command), limits=LIMITS,
                                input_bytes=pilot._canonical(requests[stage]), success_codes=(0,), **runtime_options)
        if not pilot._same(pilot._decode(receipt["stdout"].encode()), results[stage]):
            raise ValueError("saved scaled stage differs from its exact worker output")
    expected_source = {
        "source_directory": str(directory / "source"), "source_schema": SOURCE_SCHEMA,
        "epoch_sha256": source["epoch_sha256"],
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
    if not pilot._same(results["source"], expected_source) or not pilot._same(results["preparation"], expected_preparation):
        raise ValueError("saved scaled source/preparation changed its manifest identity")
    if not pilot._same(saved, _readiness_record(directory, results, saved["stage_files"])):
        raise ValueError("saved scaled readiness summary differs from its stage evidence")
    for stage in ("preflight", "capacity-plan"):
        fresh = _stage(requests[stage], python=Path(sys.executable))
        if not pilot._same(fresh, results[stage]):
            raise ValueError(f"independently regenerated scaled {stage} differs")
    if saved["token_budget_checked"]:
        fresh = _stage(requests["token-audit"], python=tokenizer_python)
        if not pilot._same(fresh, results["token-audit"]):
            raise ValueError("independently tokenized scaled inputs differ")
    if (pilot._read(directory / "readiness.json") != raw
        or pilot._read(directory / "source/manifest.json") != source_raw
        or pilot._read(directory / "preparation/manifest.json") != preparation_raw):
        raise ValueError("scaled inputs changed during independent verification")
    return {"schema": SCHEMA, "status": "verified", "readiness_sha256": signed,
            "verified_teacher_routes": saved["verified_teacher_routes"],
            "token_budget_checked": saved["token_budget_checked"],
            "model_training_authorized": False, "model_trained": False,
            "cuda_initialized": False, "research_claim_eligible": False}


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments == ["--worker"]:
        try:
            request = pilot._decode(sys.stdin.buffer.read(pilot.MAX_REQUEST_BYTES + 1),
                                    maximum=pilot.MAX_REQUEST_BYTES)
            sys.stdout.buffer.write(pilot._canonical(_worker(request)) + b"\n")
            return 0
        except (ValueError, TypeError, KeyError, OSError, RuntimeError, ImportError) as error:
            print(f"authority-scale-worker: {' '.join(str(error).split())[:3000]}", file=sys.stderr)
            return 2
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--plan", action="store_true", help="declare the scaled exercises without proof or writes (default)")
    modes.add_argument("--prepare", action="store_true", help="prepare one fresh CPU-only scaled experiment")
    modes.add_argument("--verify", type=Path, metavar="DIRECTORY", help="independently recheck a not-yet-trained bundle")
    modes.add_argument("--token-audit", type=Path, metavar="PREPARATION",
                       help="audit an existing scaled preparation in the selected tokenizer environment, without weights")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--audit-output", type=Path,
                        help="fresh standalone token-audit receipt; never changes the prepared bundle")
    parser.add_argument("--run-id", default="authority-scale-v1")
    parser.add_argument("--tokenizer-manifest", type=Path)
    parser.add_argument("--tokenizer-python", type=Path, default=Path(sys.executable))
    args = parser.parse_args(arguments)
    if args.prepare != (args.output_dir is not None):
        parser.error("--prepare requires a fresh --output-dir; planning and verification do not write")
    if not args.prepare and args.verify is None and args.token_audit is None and args.tokenizer_manifest is not None:
        parser.error("token audit belongs to --prepare or --verify, not planning")
    if (args.token_audit is None) != (args.audit_output is None):
        parser.error("standalone --token-audit requires one fresh --audit-output")
    if args.token_audit is not None and args.tokenizer_manifest is None:
        parser.error("standalone --token-audit requires the pinned --tokenizer-manifest")
    try:
        python = args.tokenizer_python.expanduser().absolute()
        if not python.is_file() or not os.access(python, os.X_OK):
            raise ValueError("select an existing executable --tokenizer-python")
        tokenizer = None if args.tokenizer_manifest is None else args.tokenizer_manifest.expanduser().absolute()
        if args.token_audit is not None:
            audit_output = args.audit_output.expanduser().absolute()
            process_output = audit_output.with_suffix(".process.json")
            if any(path.exists() or path.is_symlink() for path in (audit_output, process_output)):
                raise ValueError("standalone token audit requires a fresh output; existing evidence is preserved")
            if not audit_output.parent.is_dir() or audit_output.parent.is_symlink():
                raise ValueError("standalone audit output parent must be an existing real directory")
            result = _stage({"stage": "token-audit",
                             "preparation": str(args.token_audit.expanduser().absolute()),
                             "tokenizer_manifest": str(tokenizer)}, python=python,
                            receipt_output=process_output)
            pilot._write_new(audit_output, result)
        elif args.prepare:
            result = _prepare(args.output_dir.expanduser().absolute(), run_id=args.run_id,
                              tokenizer_manifest=tokenizer, tokenizer_python=python)
        elif args.verify is not None:
            result = _verify(args.verify.expanduser().absolute(), tokenizer_manifest=tokenizer,
                             tokenizer_python=python)
        else:
            result = _stage({"stage": "plan"}, python=Path(sys.executable))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2))
        return 0
    except (ValueError, TypeError, KeyError, OSError, RuntimeError) as error:
        print(f"hydra-authority-scale: {' '.join(str(error).split())[:3000]}", file=sys.stderr)
        if args.prepare:
            print("Partial output and receipts are retained; no automatic retry or limit increase.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
