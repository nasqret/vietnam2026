#!/usr/bin/env python3
"""Prepare the explicitly authorized, resource-fit small-model experiment.

Default/--check authenticates the fixed selection and original input bytes;
it does not replay proofs, load a tokenizer/model, or publish data. --prepare
regenerates every retained complete proof route through the existing kernel
pipeline and publishes a separate immutable handoff. The original catalog-460
data, historical quarantine, model configuration, and token guards do not change.
The production training runner must still tokenize and check its exact inputs.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / "peano-lab/py", ROOT / "scripts"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from training.peano_hydra.epoch import freeze_epoch  # noqa: E402
from training.peano_hydra.frontier import decode, digest, read_bytes  # noqa: E402
from training.peano_hydra.posttrain import prepare_posttraining  # noqa: E402
from training.peano_policy.manifest import publish_staged_directory_noreplace  # noqa: E402

AUDIT_RELATIVE = "artifacts/peano-hydra/capacity-2026-08-27/token-fit-precheck.json"
AUDIT_FILE_SHA256 = "42ec036d7ad518ed98ebe185649adb5dbd56700f1d60f5e4e3cc5a2af0c8f140"
ORIGINAL_REFERENCE = "artifacts/peano-hydra/alpha-v25-posttrain-2026-08-26"
ORIGINAL_DIRECTORY = "_deploy/hydra-posttrain-next"
SOURCE_DIRECTORY = "_deploy/hydra-capacity-fit-source"
PREPARATION_DIRECTORY = "_deploy/hydra-posttrain-capacity-fit"
RUN_ID = "capacity-fit-v1"
MAX_BYTES = 64 * 1024**2


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _row_key(row: dict[str, object]) -> str:
    # The existing curriculum's exact authority-preserving deduplication key.
    return digest([row[name] for name in (
        "epoch_sha256", "lineage_sha256", "state_sha256", "action", "environment_sha256"
    )])


def _row_text(row: dict[str, object]) -> tuple[str, str]:
    return _sha(row["prompt"].encode("utf-8")), _sha(row["completion"].encode("utf-8"))


@dataclass(frozen=True)
class FitInputs:
    plan: dict[str, object]
    rows: dict[str, tuple[dict[str, object], ...]]
    census: dict[str, list[dict[str, object]]]


def load_fit_inputs(root: Path = ROOT) -> FitInputs:
    """Authenticate a fixed pre-model resource selection, not an unseen split."""
    audit_raw = read_bytes(root / AUDIT_RELATIVE, limit=8 * 1024**2)
    _require(_sha(audit_raw) == AUDIT_FILE_SHA256, "frozen local token precheck bytes changed")
    audit = decode(audit_raw, limit=8 * 1024**2)
    unsigned = dict(audit)
    signed = unsigned.pop("audit_sha256")
    _require(digest(unsigned) == signed, "token precheck digest differs")
    _require(audit["limits"] == {"max_sequence_tokens": 4096, "max_supervised_tokens": 256},
             "resource-fit selection changed the training token limits")
    _require(audit["model_training_executed"] is False and audit["research_claim_eligible"] is False
             and audit["tokenizer"]["production_runtime_attestation"] is False,
             "local token precheck must not claim a production model run")
    reference_raw = read_bytes(root / ORIGINAL_REFERENCE / "next-preparation-manifest.json")
    _require(_sha(reference_raw) == audit["original_preparation_manifest_sha256"],
             "original preparation reference changed")
    reference = decode(reference_raw)
    original = root / ORIGINAL_DIRECTORY
    _require(not (root / "_deploy").is_symlink() and original.is_dir() and not original.is_symlink(),
             "original preparation must be a regular dedicated directory")
    _require(read_bytes(original / "manifest.json") == reference_raw,
             "original catalog-460 preparation manifest changed")
    _require({path.name for path in original.iterdir()} == set(reference["files"]) | {"manifest.json"},
             "original preparation inventory changed")
    payloads = {}
    for name, descriptor in reference["files"].items():
        raw = read_bytes(original / name, limit=MAX_BYTES)
        _require(len(raw) == descriptor["bytes"] and _sha(raw) == descriptor["sha256"],
                 f"original preparation file changed: {name}")
        payloads[name] = raw
    source_raw = read_bytes(root / ORIGINAL_REFERENCE / "next-source-manifest.json")
    _require(_sha(source_raw) == reference["source"]["manifest_sha256"], "source reference changed")
    source = decode(source_raw)
    names = source["catalog_training"]["theorem_names"]
    exclusions = audit["excluded_theorem_names"]
    selected = [name for name in names if name not in exclusions]
    _require(len(names) == len(set(names)) == 460 and len(set(exclusions)) == len(exclusions) == 5,
             "original route inventory or fixed whole-route exclusion count changed")
    _require(set(exclusions) <= set(names) and selected == audit["kept_catalog_theorem_names"],
             "retained catalog routes differ from the fixed resource selection")
    _require(len(selected) == 455, "resource-fit selection must retain exactly 455 complete routes")
    rows = {}
    observed_exclusions = set()
    for split in ("train", "dev"):
        records = tuple(decode(line) for line in payloads[f"{split}.jsonl"].splitlines())
        census = audit["rows"][split]
        _require(len(records) == len(census) == reference["files"][f"{split}.jsonl"]["rows"],
                 f"local precheck lost {split} rows")
        for row, observed in zip(records, census):
            _require(row["source_transition_sha256"] == observed["source_transition_sha256"]
                     and row["theorem_name"] == observed["theorem_name"],
                     "token precheck changed its exact row order or theorem identity")
            _require(type(observed["sequence_tokens"]) is int and observed["sequence_tokens"] >= 2
                     and type(observed["supervised_tokens"]) is int and observed["supervised_tokens"] >= 1,
                     "token precheck contains invalid lengths")
            if observed["sequence_tokens"] > 4096 or observed["supervised_tokens"] > 256:
                observed_exclusions.add(row["theorem_name"])
        rows[split] = records
    _require(observed_exclusions == set(exclusions), "exclusions are not exactly the oversized routes")
    plan = {
        "schema": "peano-hydra-capacity-fit-plan-v1", "run_id": RUN_ID,
        "required_epoch_sha256": reference["epoch_sha256"], "required_version": reference["version"],
        "original_preparation_directory": ORIGINAL_DIRECTORY,
        "original_preparation_manifest_sha256": _sha(reference_raw),
        "local_token_precheck": {"path": AUDIT_RELATIVE, "file_sha256": AUDIT_FILE_SHA256,
                                 "audit_sha256": signed, "tokenizer": audit["tokenizer"]},
        "selection_policy": audit["selection_policy"],
        "excluded_theorem_names": exclusions, "selected_theorem_names": selected,
        "selected_catalog_routes": len(selected), "token_limits": audit["limits"],
        "projected_counts": audit["projected_fit_counts"],
        "source_directory": SOURCE_DIRECTORY, "preparation_directory": PREPARATION_DIRECTORY,
        "production_token_recheck_required": True, "unseen_evaluation_eligible": False,
        "development_only": True, "research_claim_eligible": False, "model_trained": False,
    }
    plan["plan_sha256"] = digest(plan)
    return FitInputs(plan, rows, audit["rows"])


def validate_fit_rows(inputs: FitInputs, prepared) -> dict[str, object]:
    """New rows must have the exact safe old prompt/action/authority and split."""
    totals = {}
    for split, current in (("train", prepared.train_rows), ("dev", prepared.development_rows)):
        known = {}
        for original, tokens in zip(inputs.rows[split], inputs.census[split]):
            key = _row_key(original)
            value = (_row_text(original), tokens["sequence_tokens"], tokens["supervised_tokens"])
            _require(key not in known or known[key] == value, "original token-key collision")
            known[key] = value
        expected_keys = {_row_key(row) for row in inputs.rows[split]
                         if row["theorem_name"] not in inputs.plan["excluded_theorem_names"]}
        observed_keys = set()
        lengths, completions = [], []
        for row in current:
            _require(row["theorem_name"] not in inputs.plan["excluded_theorem_names"],
                     "an excluded proof route returned in the resource-fit handoff")
            key = _row_key(row)
            _require(key not in observed_keys, "duplicate regenerated resource-fit transition")
            observed_keys.add(key)
            value = known.get(key)
            _require(value is not None and value[0] == _row_text(row),
                     "regenerated row needs a new token audit; old counts cannot be reused")
            _require(value[1] <= 4096 and value[2] <= 256, "regenerated row exceeds unchanged token limits")
            lengths.append(value[1])
            completions.append(value[2])
        _require(observed_keys == expected_keys, "regenerated resource-fit transition inventory differs")
        _require(bool(lengths), "resource-fit split is empty")
        totals[split] = {
            "rows_under_original_split": len(lengths), "sequence_total": sum(lengths),
            "sequence_sum_squared": sum(length * length for length in lengths),
            "sequence_maximum": max(lengths), "supervised_total": sum(completions),
            "supervised_maximum": max(completions),
        }
    _require(totals == inputs.plan["projected_counts"],
             "independent regeneration changed the projected resource-fit corpus; review before training")
    return totals


def _publish_source(directory: Path, payloads: dict[str, bytes]) -> None:
    _require(not directory.parent.is_symlink(), "resource-fit output parent must not be a symlink")
    if directory.exists() or directory.is_symlink():
        _require(directory.is_dir() and not directory.is_symlink(), "unsafe existing resource-fit source")
        _require({path.name for path in directory.iterdir()} == set(payloads), "existing source inventory differs")
        for name, raw in payloads.items():
            _require(read_bytes(directory / name, limit=MAX_BYTES) == raw,
                     f"refusing to replace existing resource-fit source: {name}")
        return
    directory.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{directory.name}.partial-", dir=directory.parent))
    for name, raw in payloads.items():
        with (staging / name).open("xb") as stream:
            stream.write(raw)
    # Existing nonempty AND empty destinations are protected by this shared
    # no-replace primitive. Interrupted staging is retained for inspection.
    publish_staged_directory_noreplace(staging, directory)


def prepare_fit(root: Path = ROOT) -> dict[str, object]:
    inputs = load_fit_inputs(root)
    expected = inputs.plan["required_epoch_sha256"]
    _require(freeze_epoch(root).epoch_sha256 == expected,
             "capacity fit requires the frozen Alpha-v25 source checkout, not a moving newer release")
    from prepare_peano_hydra import _strict_json, encode_jsonl, prepare
    epoch, curriculum, manifest = prepare(catalog_limit=0, catalog_theorems=tuple(inputs.plan["selected_theorem_names"]))
    _require(epoch.epoch_sha256 == expected and manifest["catalog_training"]["theorem_names"] == inputs.plan["selected_theorem_names"],
             "resource-fit replay changed its frozen epoch or complete selected routes")
    manifest["capacity_fit"] = inputs.plan
    source = root / SOURCE_DIRECTORY
    _publish_source(source, {
        "epoch.json": _strict_json(epoch.to_dict(include_graphs=True), pretty=True),
        "manifest.json": _strict_json(manifest, pretty=True),
        "sft.jsonl": encode_jsonl(curriculum.transitions),
        "preferences.jsonl": encode_jsonl(curriculum.preferences),
        "discovery.jsonl": encode_jsonl(curriculum.discoveries),
    })
    prepared = prepare_posttraining(source, root / PREPARATION_DIRECTORY, run_id=RUN_ID)
    counts = validate_fit_rows(inputs, prepared)
    _require(prepared.manifest["held_out"]["quarantine_rows"] == 13,
             "resource-fit preparation changed the historical quarantined rows")
    _publish_source(root / PREPARATION_DIRECTORY, prepared.payloads)
    _require(load_fit_inputs(root).plan == inputs.plan, "original inputs changed while preparing resource fit")
    return {
        "schema": "peano-hydra-capacity-fit-preparation-v1", "status": "prepared",
        "plan_sha256": inputs.plan["plan_sha256"], "run_id": RUN_ID,
        "epoch_sha256": epoch.epoch_sha256, "checked_catalog_routes": 455,
        "training_rows": len(prepared.train_rows), "development_rows": len(prepared.development_rows),
        "quarantined_rows": 13, "local_token_projection": counts,
        "preparation_directory": PREPARATION_DIRECTORY,
        "preparation_manifest_sha256": _sha(prepared.payloads["manifest.json"]),
        "adapter_output_dir": prepared.config.run.output_dir,
        "production_token_recheck_required": True, "model_trained": False,
        "research_claim_eligible": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true", help="authenticate selection and original bytes, without proof replay or writes")
    modes.add_argument("--prepare", action="store_true", help="replay complete retained proof routes and publish a separate checked handoff")
    args = parser.parse_args(argv)
    try:
        result = prepare_fit() if args.prepare else load_fit_inputs().plan
    except (KeyError, OSError, TypeError, ValueError, RuntimeError) as error:
        print(f"prepare-peano-hydra-capacity: {' '.join(str(error).split())}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
