"""Metadata/config CLI for the explicit teacher-data extension; no training.

Creating a spec pins existing actual run artifacts. Export requires separate
fresh native replay receipts. No operation here invokes a model or proof tactic.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

from teacher_data import (APP, ROOT, BASE_SHA, SELECTION_SHA, SPEC_SCHEMA, DATA_SCHEMA,
    Inputs, bootstrap, canonical, require, export_dataset, write_new)


def relative(path):
    path = Path(path)
    return path.relative_to(ROOT).as_posix() if path.is_absolute() else path.as_posix()


def exact_reference(inputs, path, maximum=2 * 1024**2):
    name = relative(path)
    inputs.read(name, maximum=maximum)
    return inputs.pins[name]


def make_spec(*, base_manifest, selection, campaign_directory, actual_exit, output):
    inputs = Inputs()
    base = exact_reference(inputs, base_manifest)
    cohort = exact_reference(inputs, selection)
    require(base["sha256"] == BASE_SHA and cohort["sha256"] == SELECTION_SHA,
            "Use the fixed v2 base and unchanged 32-state teacher selection.")
    directory = relative(campaign_directory)
    request = inputs.json(directory + "/request.json")
    campaign = {"directory": directory,
        "request_sha256": inputs.pins[directory + "/request.json"]["sha256"],
        "source_pins_sha256": request["source_pins_sha256"],
        "actual_process_exit": exact_reference(inputs, actual_exit, 32)}
    for filename, key in (("completion.json", "completion_sha256"),
                          ("model-admission.json", "model_admission_sha256"),
                          ("positive-continuations.json", "positives_sha256")):
        campaign[key] = exact_reference(inputs, directory + "/" + filename)["sha256"]
    record = {"schema": SPEC_SCHEMA, "base_dataset": base, "selection": cohort, "campaign": campaign}
    raw = canonical(record) + b"\n"
    write_new(output, raw)
    return {"path": relative(output), "sha256": sha256(raw).hexdigest(), "status": "pinned_not_admitted"}


def make_config(*, dataset_manifest, expected_sha256, model_key, output, artifact_directory):
    inputs = Inputs()
    manifest_name = relative(dataset_manifest)
    manifest = inputs.json(manifest_name, expected_sha256)
    require(manifest.get("schema") == DATA_SCHEMA and manifest.get("training_allowed") is True
            and manifest.get("status") == "complete" and manifest.get("teacher_rows_added", 0) > 0,
            "A zero/unadmitted teacher dataset cannot generate a student-update config.")
    bootstrap()
    from hydra_training_v5.pilot_config import load_pilot_config, validate_pilot_config
    from experimental_model import model_spec
    spec = model_spec(model_key)
    original = load_pilot_config(APP / "training-v5/configs/qwen3_4b_decisions_v2_pilot.toml")
    sections = asdict(original)
    sections.pop("path"); sections.pop("curriculum", None)
    require(set(sections) == {"run", "model", "data", "lora", "trainer", "generation"},
            "The fixed pilot's six-section configuration changed.")
    sections["model"]["model_id"] = spec["model_id"]
    sections["model"]["revision"] = spec["revision"]
    sections["run"]["name"] = model_key + "-teacher-augmented-v1"
    sections["run"]["output_dir"] = relative(artifact_directory)
    destination = inputs.path(sections["run"]["output_dir"])
    require(not destination.exists(), "The new student adapter must have a fresh output directory.")
    directory = str(Path(manifest_name).parent)
    sections["data"]["train_path"] = directory + "/primitive-train.jsonl"
    sections["data"]["eval_path"] = directory + "/primitive-val.jsonl"
    lines = ["# Prepared teacher augmentation; a new admitted manifest and allocation remain mandatory."]
    for section in ("run", "model", "data", "lora", "trainer", "generation"):
        lines.append("[" + section + "]")
        for key, value in sections[section].items():
            require(value is not None and type(value) in (str, int, float, bool, list, tuple),
                    "Unexpected pilot configuration type.")
            lines.append(key + " = " + json.dumps(value, ensure_ascii=False, allow_nan=False))
        lines.append("")
    raw = ("\n".join(lines) + "\n").encode()
    write_new(output, raw)
    validate_pilot_config(load_pilot_config(output))
    return {"path": relative(output), "sha256": sha256(raw).hexdigest(),
        "model_key": model_key, "dataset_manifest_sha256": expected_sha256,
        "status": "config_written_not_prepared_or_trained"}


def main(argv=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    spec = sub.add_parser("spec")
    for name in ("base-manifest", "selection", "campaign-directory", "actual-exit", "output"):
        spec.add_argument("--" + name, type=Path, required=True)
    export = sub.add_parser("export")
    export.add_argument("--input-spec", required=True)
    export.add_argument("--input-sha256", required=True)
    export.add_argument("--output", type=Path, required=True)
    export.add_argument("--replay-manifest", type=Path)
    export.add_argument("--replay-sha256")
    export.add_argument("--replay-actual-exit", type=Path)
    export.add_argument("--replay-exit-sha256")
    config = sub.add_parser("config")
    config.add_argument("--dataset-manifest", type=Path, required=True)
    config.add_argument("--dataset-sha256", required=True)
    config.add_argument("--model-key", choices=("qwen3-1.7b-base", "qwen3-4b-base", "qwen3-8b-base"), required=True)
    config.add_argument("--output", type=Path, required=True)
    config.add_argument("--artifact-directory", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "spec":
        record = make_spec(base_manifest=args.base_manifest, selection=args.selection,
            campaign_directory=args.campaign_directory, actual_exit=args.actual_exit, output=args.output)
    elif args.command == "config":
        record = make_config(dataset_manifest=args.dataset_manifest, expected_sha256=args.dataset_sha256,
            model_key=args.model_key, output=args.output, artifact_directory=args.artifact_directory)
    else:
        require((args.replay_manifest is None) == (args.replay_sha256 is None)
                and (args.replay_actual_exit is None) == (args.replay_exit_sha256 is None),
                "Every fresh replay input needs its exact explicit SHA.")
        replay = None if args.replay_manifest is None else {"path": relative(args.replay_manifest), "sha256": args.replay_sha256}
        replay_exit = None if args.replay_actual_exit is None else {"path": relative(args.replay_actual_exit), "sha256": args.replay_exit_sha256}
        record = export_dataset(args.input_spec, expected_sha256=args.input_sha256, output=args.output,
                                replay_manifest=replay, replay_exit=replay_exit)
    print(json.dumps({k: v for k, v in record.items() if k not in {"inputs", "files", "source_pins", "base_attestation"}}, sort_keys=True))
    return 0 if record.get("status", "").startswith(("pinned_", "config_", "complete")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
