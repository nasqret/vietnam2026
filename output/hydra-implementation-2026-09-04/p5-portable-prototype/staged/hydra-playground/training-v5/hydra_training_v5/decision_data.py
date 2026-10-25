"""Admission for new decision exports; preserved v1/v4 attestors stay intact.

The new export is not the old replay-compiler dataset. Admission rehashes every
source and regenerates the data from recorded full native replay evidence.
Regeneration parses formulas for exclusions; it performs no proof search or
model work and does not claim to have repeated the historical kernel checks.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
import tempfile

from .peano_policy.prompt import ProofExample, parse_prompt

PACKAGE = Path(__file__).resolve().parent
WORKING = PACKAGE.parent
APP = WORKING.parent
ROOT = APP.parent


class DecisionDataError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise DecisionDataError(message)


def _exporter():
    if str(APP) not in sys.path:
        sys.path.insert(0,str(APP))
    import export_decisions
    require(Path(export_decisions.__file__).resolve() == APP/"export_decisions.py",
            "Decision exporter came from an unexpected module path.")
    return export_decisions


def validate_primitive_row(row, *, split):
    require(type(row) is dict and row.get("schema") == "hydra-primitive-sft-v1"
            and row.get("split") == split and split in ("train","val","test")
            and row.get("prompt_version") == 4 and row.get("kernel_checked") is True
            and row.get("censored") is False,
            "Only explicitly checked primitive SFT rows are admissible.")
    require(row.get("verification_scope") in (
        "recorded_full_original_goal_independent_native_replay",
        "preserved_native_transition_and_actual_retention_training_origins"),
        "Unknown native evidence scope.")
    require(row.get("reserved_intermediate_check") == "exact_closed_AST_plus_declared_template_exclusions",
            "Row lacks reserved-state exclusion evidence.")
    parsed = parse_prompt(row["prompt"])
    require(parsed.prompt_version == 4 and parsed.classical is False
            and parsed.focus == 0 and tuple(parsed.goals) == tuple(row["goals_before"])
            and parsed.allowed_theorem_names == (), "Row changed its full state or primitive authority.")
    example = ProofExample(row["id"],row["prompt"],row["completion"],row["environment_sha256"])
    require(example.tactic == row["action"] and example.tactic != "qed"
            and not example.tactic.startswith("use "), "Completion is not a no-import primitive action.")
    return example


@dataclass(frozen=True)
class DecisionDataset:
    manifest_sha256: str
    manifest_path: str
    train: tuple[ProofExample,...]
    validation: tuple[ProofExample,...]
    test_count: int
    row_ids_sha256: str
    validation_ids_sha256: str
    attestation: dict


def verify_working_baseline():
    """Copied training files may only differ by the recorded namespace rewrite."""
    baseline = json.loads((WORKING/"BASELINE.json").read_bytes())
    require(baseline.get("schema") == "hydra-working-training-baseline-v1"
            and baseline.get("copied_files") == len(baseline.get("files", [])),
            "Malformed training baseline catalogue.")
    for record in baseline["files"]:
        path = WORKING/record["working"]
        require(path.is_file() and not path.is_symlink()
                and path.stat().st_size == record["initial_working_bytes"]
                and hashlib.sha256(path.read_bytes()).hexdigest() == record["initial_working_sha256"],
                "Inherited training source changed: "+record["working"])
    return {"sha256":hashlib.sha256((WORKING/"BASELINE.json").read_bytes()).hexdigest(),
            "copied_files_verified":len(baseline["files"]),"source_commit":baseline["source_commit"]}


def manifest_difference(expected, regenerated):
    """A bounded diagnostic, never a reason to accept mismatched evidence."""
    exporter = _exporter()
    keys = sorted(set(expected) | set(regenerated))
    changed = [key for key in keys if expected.get(key) != regenerated.get(key)]
    files = sorted(set(expected.get("files",{})) | set(regenerated.get("files",{})))
    def identity(value):return hashlib.sha256(exporter.canonical(value)).hexdigest()
    return {"schema":"hydra-decision-admission-diff-v1", "admitted":False,
        "expected_manifest_sha256":identity(expected),"regenerated_manifest_sha256":identity(regenerated),
        "different_top_level_fields":changed,
        "file_differences":{name:{"expected":expected.get("files",{}).get(name),
                                  "regenerated":regenerated.get("files",{}).get(name)}
            for name in files if expected.get("files",{}).get(name) != regenerated.get("files",{}).get(name)},
        "metadata_differences":{key:{"expected_sha256":identity(expected.get(key)),
                                     "regenerated_sha256":identity(regenerated.get(key))}
                                for key in changed if key != "files"}}


def retain_manifest_mismatch(expected_raw, regenerated_raw, expected, regenerated, *, failure_output=None):
    exporter = _exporter()
    difference = exporter.canonical(manifest_difference(expected,regenerated))+b"\n"
    require(all(len(raw) <= 1024*1024 for raw in (expected_raw,regenerated_raw,difference)),
            "Admission failure evidence exceeds its bound.")
    if failure_output is None:
        directory = ROOT/"output/admission-failures"
        directory.mkdir(parents=True,exist_ok=True)
        failure_output = Path(tempfile.mkdtemp(prefix="decision-v2-",dir=directory))
    else:
        failure_output = Path(failure_output)
        failure_output.mkdir(parents=True,exist_ok=False)
    for name,raw in (("expected-manifest.json",expected_raw),
                     ("regenerated-manifest.json",regenerated_raw),("diff.json",difference)):
        with (failure_output/name).open("xb") as stream:stream.write(raw)
    return str(failure_output)


def attest_decision_dataset(manifest_path, *, expected_sha256, workspace=ROOT, failure_output=None):
    """Fail closed on mutated sources, exclusion drift, or fabricated export rows."""
    exporter = _exporter()
    inputs = exporter.Inputs(workspace)
    path = Path(manifest_path)
    relative = path.relative_to(inputs.root).as_posix() if path.is_absolute() else path.as_posix()
    manifest = inputs.json(relative,expected_sha256)
    require(manifest.get("schema") == exporter.EXPORT_SCHEMA and manifest.get("status") == "complete"
            and manifest.get("schema_mode") == "primitive_v4" and manifest.get("max_train_rows",4097) <= 4096
            and manifest.get("holdout_sha256") == exporter.HOLDOUT_SHA256
            and manifest.get("ranking_feature_schema") == exporter.FEATURE_SCHEMA
            and manifest.get("ranking_numeric_encoding") == exporter.NUMERIC_ENCODING
            and manifest.get("resource_stops_are_censored") is True
            and manifest.get("missing_states_fabricated") is False,
            "Dataset is not a completed bounded primitive decision export.")
    root = str(Path(relative).parent)
    for record in manifest["inputs"]:
        inputs.read(record["path"],record,exporter.MAX_INPUT_BYTES)
    for name,pin in manifest["files"].items():
        inputs.read(root+"/"+name,pin,exporter.MAX_INPUT_BYTES)
    input_specs = []
    for record in manifest["inputs"]:
        if record["path"].endswith(".json") and record["bytes"] <= 512*1024:
            value = exporter.decode(inputs.read(record["path"],record,exporter.MAX_INPUT_BYTES))
            if type(value) is dict and value.get("schema") == exporter.INPUT_SCHEMA:
                input_specs.append(record)
    require(len(input_specs) == 1, "Expected one exact export input specification.")
    with tempfile.TemporaryDirectory(prefix="hydra-decision-admission-") as temporary:
        regenerated = exporter.export_dataset(input_specs[0]["path"],
            input_sha256=input_specs[0]["sha256"],output=Path(temporary)/"regenerated",
            root=inputs.root,website_opt_in=manifest["website_opt_in_enabled"])
        if exporter.canonical(regenerated) != exporter.canonical(manifest):
            retained = retain_manifest_mismatch(inputs.read(relative,expected_sha256,exporter.MAX_INPUT_BYTES),
                (Path(temporary)/"regenerated/manifest.json").read_bytes(),manifest,regenerated,
                failure_output=failure_output)
            raise DecisionDataError("Dataset cannot be regenerated exactly from its claimed evidence. "
                                    "Failure evidence retained at "+retained)
    groups,ids,rows = {},set(),{}
    for split in ("train","val","test"):
        values = []
        for line in inputs.read(root+"/primitive-"+split+".jsonl",
                manifest["files"]["primitive-"+split+".jsonl"],exporter.MAX_INPUT_BYTES).splitlines():
            row = exporter.decode(line)
            example = validate_primitive_row(row,split=split)
            require(example.example_id not in ids, "Duplicate row crosses exported splits.")
            ids.add(example.example_id)
            group = row.get("split_group")
            require(type(group) is str and (group not in groups or groups[group] == split),
                    "Whole theorem/template component crosses train/evaluation split.")
            groups[group] = split
            values.append(example)
        rows[split] = tuple(values)
    require(0 < len(rows["train"]) <= 4096 and len(rows["val"]) > 0,
            "Pilot requires a bounded nonempty training set and a family-separated validation set.")
    baseline = verify_working_baseline()
    def ids_digest(split):
        return hashlib.sha256(exporter.canonical([x.example_id for x in rows[split]])).hexdigest()
    attestation = {"schema":"hydra-decision-data-attestation-v2", "manifest_sha256":expected_sha256,
        "ranking_feature_schema":manifest["ranking_feature_schema"],
        "ranking_numeric_encoding":manifest["ranking_numeric_encoding"],
        "regenerated_byte_exact":True,"inputs_verified":len(manifest["inputs"]),
        "files_verified":len(manifest["files"]),"training_rows":len(rows["train"]),
        "validation_rows":len(rows["val"]),"test_rows_not_used":len(rows["test"]),
        "holdout_sha256":exporter.HOLDOUT_SHA256,"baseline":baseline,
        "native_replays_performed_by_admission":0,"source_scope":manifest["positive_source_scope"],
        "benchmark_claim":False}
    return DecisionDataset(expected_sha256,relative,rows["train"],rows["val"],len(rows["test"]),
                           ids_digest("train"),ids_digest("val"),attestation)
