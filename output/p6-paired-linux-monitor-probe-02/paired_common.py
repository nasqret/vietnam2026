# Scheduler v3 binding: one 15-second query, no retry or identity relaxation.
# Provider v2 revision: the reviewed 4.53.3 beam-slot accounting and scheduler pins.
# Study, reservation, resource, cleanup, and native proof rules are unchanged.
"""Pure, finite admission rules for a prospective Hydra model comparison.

Importing this module never imports a model, native engine, or scheduler client.
Wall-profile selection is a future root-reviewed decision after the load smoke.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat

HOLDOUT_SHA = "2a57f12ffe55f90c3c4ac896fba3c2bab47e795b6bb5ba5f15b2c6854cddb58e"
PROVIDER_SHA = "cc279710866146414c439e17935915f28d7dda7a44df20aa5d7e6bcd87994c44"
REGISTRY_SHA = "3303c4727052557a04bc2e33ea624ff7093703c68ae8fa95b12fb05adbc781c1"
NATIVE_MANIFEST_SHA = "5c2fa7aa6878c7730fe972e095f8e9312d0980de65c31767d385c27caf54046e"
KERNEL_SHA = "ad88855528244707b1fe7bd142d8fea60883a23b429840e07dd1875f3499c45d"
SCHEDULER_SHA = "cc8dec7bcb2187568c1aed1eaa1b580435460e297573b655eac2b32b74a271b4"
HISTORICAL_SHA = "cdacbda7777568120029b671374aaf16e994f2da2a54b867a00c81ece086d6ca"
DATASET_SHA = "e575970df58d046735f492acaf22e1cdea44445608a201c62d0644590b95ea77"
ORIGINAL = "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
ACCOUNT = "plgccaiautore2026-gpu-gh200"
PARTITION = "plgrid-gpu-gh200"
REQUIRED_ARMS = ("symbolic", "historical_1_7b", "fresh_1_7b", "fresh_4b")
OPTIONAL_ARMS = ("fresh_8b", "distilled_1_7b")
MODEL_KEYS = {"historical_1_7b": "qwen3-1.7b-base", "fresh_1_7b": "qwen3-1.7b-base",
              "fresh_4b": "qwen3-4b-base", "fresh_8b": "qwen3-8b-base",
              "distilled_1_7b": "qwen3-1.7b-base"}
SLICE_IDS = ("holdout_divisor_transitivity", "holdout_additive_left_cancellation",
             "holdout_four_residue_classes", "holdout_additive_totality",
             "holdout_negative_missing_divisor_premise")
FEATURES = {"engine": "sharing-v1", "library": False, "ranker": False,
            "planner": False, "external_advisers": [], "classical": False}
NATIVE_WORK = {"max_depth": 96, "max_states": 2048, "max_tactic_attempts": 6000,
               "max_expansions": 384, "max_frontier": 128, "candidates_per_state": 48,
               "max_macro_steps": 8, "closure_steps": 16, "heuristic_burst": 8,
               "max_model_calls": 16, "max_vampire_calls": 0}
# Both are alternatives awaiting the root's measured smoke decision, not allocations.
WALL_PROFILES = {
    "guarded-work-60-v1": {"load_seconds": 45, "search_seconds": 60,
                           "search_return_grace_seconds": 2, "replay_seconds": 13, "case_seconds": 120},
    "fixed-wall-30-v1": {"load_seconds": 45, "search_seconds": 30,
                         "search_return_grace_seconds": 2, "replay_seconds": 13, "case_seconds": 90},
}
MODEL_LIMITS = {"calls": 16, "candidate_width": 4, "input_tokens": 4096,
                "output_tokens_per_sequence": 64, "generated_token_slots": 4096,
                "seed": 0, "sampling": False}
RESOURCE_LIMITS = {"cpu_seconds": 300, "host_sampled_rss_bytes": 32 * 1024**3,
                   "gpu_observed_bytes": 32 * 1024**3, "sample_seconds": 0.05,
                   "stdout_stderr_bytes": 256 * 1024, "case_artifact_bytes": 16 * 1024**2,
                   "case_file_bytes": 4 * 1024**2, "cleanup_seconds": 3,
                   "parent_scheduler_calls": 64, "child_scheduler_calls": 32}
ADAPTER_FIELDS = {"model_key", "base_directory", "adapter_directory",
                  "adapter_manifest_sha256", "adapter_kind"}
EXPOSURE_FIELDS = ("training_rows", "validation_rows", "expected_optimizer_steps",
                   "training_row_ids_sha256", "validation_row_ids_sha256")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON field.")
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError("Nonfinite JSON number: " + value)
    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)
    require(type(result) is dict, "One JSON object is required.")
    return result


def valid_sha(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def ordinary(path, maximum=4 * 1024**2):
    path = Path(path)
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and not path.is_symlink() and info.st_nlink == 1
            and 0 <= info.st_size <= maximum, "A bounded ordinary single-link file is required: " + str(path))
    raw = path.read_bytes()
    after = path.lstat()
    require((info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
            and len(raw) == info.st_size, "File changed while reading.")
    return raw


def pin(path, maximum=4 * 1024**2):
    raw = ordinary(path, maximum)
    return {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}


def save(path, value, maximum=4 * 1024**2):
    raw = canonical(value) + b"\n"
    require(len(raw) <= maximum, "Output record exceeds its finite byte bound.")
    with Path(path).open("xb") as stream:
        stream.write(raw)


def search_settings(profile):
    require(profile in WALL_PROFILES, "Select a reviewed finite wall profile.")
    return {**NATIVE_WORK, "wall_seconds": WALL_PROFILES[profile]["search_seconds"]}


def scope_count(scope):
    require(scope in {"full16", "paired5"}, "Unknown predeclared evaluation scope.")
    return 16 if scope == "full16" else 5


def job_seconds(scope, profile):
    require(profile in WALL_PROFILES, "Unknown finite wall profile.")
    # Publish the whole-minute ceiling before authority is bound. In
    # particular paired5/fixed-wall is 600 seconds, not an implicit 570->600
    # change performed later by sbatch. Reservations must match this exactly.
    seconds = scope_count(scope) * WALL_PROFILES[profile]["case_seconds"] + 120
    return ((seconds + 59) // 60) * 60


def holdout_cases(path):
    raw = ordinary(path, 128 * 1024)
    require(sha256(raw).hexdigest() == HOLDOUT_SHA, "The exact prospective reservation changed.")
    value = strict_json(raw)
    rows = value.get("cases")
    require(value.get("frozen") is True and type(rows) is list and len(rows) == 16,
            "The fixed reservation must contain sixteen cases.")
    require(sum(row["category"] == "prospective_positive" for row in rows) == 12
            and sum(row["category"] == "negative_control" for row in rows) == 4,
            "The twelve positive/four control split changed.")
    require(len({row["id"] for row in rows}) == 16
            and len({row["family"] for row in rows if row["category"] == "prospective_positive"}) == 4,
            "The reserved IDs or four mathematical groups changed.")
    for row in rows:
        require(type(row["theorem"]) is str and 0 < len(row["theorem"].encode()) <= 4096
                and sha256(row["theorem"].encode()).hexdigest() == row["input_theorem_sha256"],
                "Reserved theorem bytes differ from their original input pin.")
    return rows


def case_payload(row, profile):
    # No case ID, family, expectation, counterexample, exposure note, or prior proof.
    return {"theorem": row["theorem"], "settings": {"features": FEATURES,
        "native_work": search_settings(profile), "model": MODEL_LIMITS}}


def validate_arm(name, value):
    require(name in REQUIRED_ARMS + OPTIONAL_ARMS, "Unknown evaluation arm.")
    if name == "symbolic":
        require(value is None, "Symbolic must not have a model or adapter.")
        return
    require(type(value) is dict and set(value) == ADAPTER_FIELDS
            and value["model_key"] == MODEL_KEYS[name], "Arm model fields differ from their fixed role.")
    require(value["adapter_kind"] == ("historical_retention" if name == "historical_1_7b" else "fresh_decision_pilot")
            and valid_sha(value["adapter_manifest_sha256"]), "Exact completed adapter identity is required.")
    if name == "historical_1_7b":
        require(value["adapter_manifest_sha256"] == HISTORICAL_SHA, "Historical control is not the preserved adapter.")
    for key in ("base_directory", "adapter_directory"):
        text = value[key]
        require(type(text) is str and 0 < len(text.encode()) <= 4096 and "\x00" not in text
                and Path(text).is_absolute(), "Model paths must be explicit absolute local paths.")


def training_exposure(record):
    require(type(record) is dict and record.get("schema") == "hydra-decision-pilot-artifact-v1"
            and record.get("model_trained") is True and record.get("resume") is False
            and record.get("automatic_retry") is False, "An incomplete/resumed artifact is not an evaluation arm.")
    plan = record["plan"]
    require(plan.get("schema") == "hydra-decision-pilot-plan-v2" and plan.get("epochs") == 1
            and plan.get("prompt_schema") == "primitive_v4" and plan.get("planner_rows_allowed") is False
            and record["actual_optimizer_steps"] == plan["expected_optimizer_steps"],
            "Fresh arms require the completed common one-pass primitive training contract.")
    attestation = plan["data_attestation"]
    require(attestation.get("holdout_sha256") == HOLDOUT_SHA
            and attestation.get("regenerated_byte_exact") is True
            and plan["resume"] is False and plan["automatic_retry"] is False,
            "Training has no bound evaluation-exclusion admission.")
    result = {name: plan[name] for name in EXPOSURE_FIELDS}
    result.update(dataset_sha256=attestation["manifest_sha256"], holdout_sha256=HOLDOUT_SHA,
                  epochs=1, prompt_schema="primitive_v4", planner_rows_allowed=False,
                  objective_sha256=sha256(canonical(plan["objective"])).hexdigest())
    validate_exposure(result)
    return result


def validate_exposure(value):
    fields = set(EXPOSURE_FIELDS) | {"dataset_sha256", "holdout_sha256", "epochs",
        "prompt_schema", "planner_rows_allowed", "objective_sha256"}
    require(type(value) is dict and set(value) == fields
            and type(value["training_rows"]) is int and 1 <= value["training_rows"] <= 4096
            and type(value["validation_rows"]) is int and 1 <= value["validation_rows"] <= 4096
            and type(value["expected_optimizer_steps"]) is int
            and value["expected_optimizer_steps"] == (value["training_rows"] + 7) // 8
            and type(value["epochs"]) is int and value["epochs"] == 1
            and value["prompt_schema"] == "primitive_v4" and value["planner_rows_allowed"] is False
            and value["holdout_sha256"] == HOLDOUT_SHA
            and all(valid_sha(value[key]) for key in fields if key.endswith("_sha256")),
            "Malformed, incomplete, or nonreserved finite training exposure.")


def study_spec(record, slice_sha):
    fields = {"schema", "study_id", "scope", "comparison", "wall_profile", "holdout_sha256",
              "slice_sha256", "source_pins_sha256", "arms", "features", "native_work", "model_limits",
              "resource_limits", "fresh_training_exposure", "distilled_training_exposure",
              "training_allowed", "retrieval_allowed", "automatic_retry", "resume"}
    require(type(record) is dict and set(record) == fields
            and record["schema"] == "hydra-p6-p10-paired-study-v1", "Unknown paired-study schema.")
    require(type(record["study_id"]) is str and re.fullmatch(r"[a-z0-9_-]{1,100}", record["study_id"]),
            "A bounded study identity is required.")
    require(record["scope"] in {"full16", "paired5"} and record["wall_profile"] in WALL_PROFILES,
            "Wall profile must be chosen after the smoke; unbound templates cannot execute.")
    require(record["comparison"] in {"fixed_native_work_guarded", "fixed_wall_slice"}
            and (record["comparison"] != "fixed_wall_slice" or record["scope"] == "paired5"),
            "Fixed-wall follow-up is restricted to the predeclared paired slice.")
    require(record["holdout_sha256"] == HOLDOUT_SHA and record["slice_sha256"] == slice_sha
            and valid_sha(record["source_pins_sha256"]), "Full exact source/input bindings are required.")
    require(canonical(record["features"]) == canonical(FEATURES)
            and canonical(record["native_work"]) == canonical(search_settings(record["wall_profile"]))
            and canonical(record["model_limits"]) == canonical(MODEL_LIMITS)
            and canonical(record["resource_limits"]) == canonical(RESOURCE_LIMITS),
            "Per-arm overrides or changed shared budgets are forbidden.")
    require(all(record[key] is False for key in ("training_allowed", "retrieval_allowed", "automatic_retry", "resume")),
            "Evaluation must not train, retrieve, resume, or retry.")
    arms = record["arms"]
    require(type(arms) is dict and 2 <= len(arms) <= 6, "Finite paired model arms are required.")
    if record["scope"] == "full16":
        require(set(arms) == set(REQUIRED_ARMS), "The first full comparison has exactly its four declared arms.")
    else:
        require("fresh_1_7b" in arms, "The optional paired slice retains the fresh 1.7B control.")
    for name, value in arms.items():
        validate_arm(name, value)
    require("distilled_1_7b" not in arms,
            "Distilled evaluation awaits explicit teacher-attested plan/provider admission; ordinary v2 training cannot impersonate it.")
    exposure = record["fresh_training_exposure"]
    validate_exposure(exposure)
    require(exposure["dataset_sha256"] == DATASET_SHA, "Fresh size arms must use the admitted common data.")
    require(("distilled_1_7b" in arms) == (type(record["distilled_training_exposure"]) is dict),
            "A distilled arm needs separately declared completed training exposure.")
    if "distilled_1_7b" in arms:
        validate_exposure(record["distilled_training_exposure"])
    else:
        require(record["distilled_training_exposure"] is None, "No undeclared distillation metadata.")
    return record


def source_pins(app):
    app = Path(app).resolve(strict=True)
    root = app.parent
    files = set(app.glob("*.py"))
    files.update((app / "native-v7/peano_lab").rglob("*.py"))
    files.update((app / "training-v5/hydra_training_v5").rglob("*.py"))
    files.update((root / ORIGINAL / "training").rglob("*.py"))
    files.update(Path(__file__).resolve().parent.glob("*.py"))
    fixed = {"experimental_model.py": PROVIDER_SHA,
             "experimental-models/qwen3-base-v1.json": REGISTRY_SHA,
             "native-v7/manifest.json": NATIVE_MANIFEST_SHA,
             "evaluation-holdout.json": HOLDOUT_SHA}
    files.update(app / name for name in fixed)
    files.add(app / "training-v5/BASELINE.json")
    require(600 <= len(files) <= 1200, "Missing or oversized executed source inventory.")
    result, total = {}, 0
    for path in sorted(files):
        relative = path.relative_to(root)
        require(path.resolve(strict=True) == root / relative, "Source escapes through a symlink.")
        item = pin(path)
        total += item["bytes"]
        require(total <= 48 * 1024**2, "Source inventory exceeds 48 MiB.")
        result[relative.as_posix()] = item
    for name, expected in fixed.items():
        require(result[(Path(app.name) / name).as_posix()]["sha256"] == expected,
                "Frozen provider/native/input pin changed: " + name)
    return result


def native_identity(app):
    native = Path(app) / "native-v7"
    raw = ordinary(native / "manifest.json", 256 * 1024)
    require(sha256(raw).hexdigest() == NATIVE_MANIFEST_SHA, "The executable native manifest changed.")
    manifest = strict_json(raw)
    files = manifest["files"]
    actual = {p.relative_to(native).as_posix() for p in (native / "peano_lab").rglob("*")
              if p.is_file() and "__pycache__" not in p.parts}
    require(actual == set(files), "The native executable inventory differs.")
    for name, expected in files.items():
        path = native / name
        require(path.resolve(strict=True).is_relative_to(native.resolve()) and pin(path) == expected,
                "An executable native source changed: " + name)
    kernel = {p.name: pin(p)["sha256"] for p in sorted((native / "peano_lab/kernel").glob("*.py"))}
    identity = sha256(canonical({"logic": "intuitionistic", "files": kernel})).hexdigest()
    require(identity == KERNEL_SHA, "The original proof checker identity changed.")
    return {"native_manifest_sha256": NATIVE_MANIFEST_SHA, "kernel_sha256": identity}


def validate_counts(search, session, policy):
    require(type(search) is dict, "A complete native search result is required.")
    for key in ("tactic_attempts", "states_expanded", "states_discovered", "depth_reached"):
        require(type(search.get(key)) is int and search[key] >= 0, "Missing actual native-work accounting.")
    for actual, cap in (("tactic_attempts", "max_tactic_attempts"), ("states_expanded", "max_expansions"),
                        ("states_discovered", "max_states"), ("depth_reached", "max_depth")):
        require(search[actual] <= NATIVE_WORK[cap], "Native work exceeded the shared bound.")
    for backend in ("vampire", "sympy", "cvc5", "egg", "e"):
        require(search.get(backend + "_calls") == 0 and search.get(backend + "_advisor_calls") == 0,
                "An undeclared external adviser ran.")
    planning = search.get("structured_planning", {})
    require(planning.get("enabled") is False and planning.get("requests") == 0
            and planning.get("provider") is None and search.get("lemma_library") is None
            and search.get("branch_ranker", {}).get("enabled") is False,
            "The fixed size comparison gained planning, retrieval, or ranking information.")
    if session is None:
        require(policy is None and search.get("model_calls") == 0 and search.get("model_advisor_calls") == 0,
                "Symbolic run has unexplained model activity.")
        return {"actual_model_calls": 0, "generated_token_slots": 0, "forward_passes": 0,
                "planner_calls": 0, "complete": True}
    calls, tokens = session.get("actual_model_calls"), session.get("generated_token_slots")
    require(type(calls) is int and 0 <= calls <= MODEL_LIMITS["calls"]
            and type(tokens) is int and 0 <= tokens <= MODEL_LIMITS["generated_token_slots"]
            and type(session.get("forward_passes")) is int and session["forward_passes"] >= 0,
            "Model counters are missing or exceed their finite shared limits.")
    require(calls == policy["calls"] == search.get("model_calls")
            and tokens == policy["generated_tokens"]
            and type(search.get("model_advisor_calls")) is int
            and calls <= search["model_advisor_calls"] <= MODEL_LIMITS["calls"],
            "Search/provider/session actual accounting differs; zero must not be inferred.")
    return {"actual_model_calls": calls, "generated_token_slots": tokens,
            "forward_passes": session["forward_passes"], "planner_calls": 0, "complete": True}


def proof_acceptance(search, replay, original):
    require(search.get("theorem") == original and search.get("classical") is False,
            "Search changed the original theorem or logic.")
    if search.get("status") != "proof":
        require(search.get("kernel_checked") is False and not search.get("commands"),
                "An incomplete search asserted a checked complete proof.")
        return False
    require(search.get("kernel_checked") is True and type(search.get("commands")) is list
            and 1 <= len(search["commands"]) <= NATIVE_WORK["max_depth"]
            and all(type(line) is str and 0 < len(line.encode()) <= 512 for line in search["commands"]),
            "Malformed complete native script.")
    inner = search.get("replay")
    for value in (inner, replay):
        require(type(value) is dict and value.get("kernel_checked") is True
                and value.get("status") == "proved" and value.get("theorem") == original
                and value.get("classical") is False and value.get("goals") == []
                and value.get("tactics_requested") == value.get("tactics_applied") == len(search["commands"])
                and value.get("proof_nodes") == search.get("certificate_nodes")
                and valid_sha(value.get("environment_sha256")),
                "Original-theorem independent native replay is missing or differs.")
    require(inner["environment_sha256"] == replay["environment_sha256"], "Independent replay changed native authority.")
    provenance = search.get("provenance")
    require(type(provenance) is list and len(provenance) == len(search["commands"])
            and all(type(row) is dict and row.get("source") in {"heuristic", "model"}
                    and row.get("command") == command for row, command in zip(provenance, search["commands"])),
            "Winning-step provenance does not match the executed native script.")
    return True
