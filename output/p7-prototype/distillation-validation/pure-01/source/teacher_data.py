"""Explicit P7 teacher-continuation extension to the immutable P5 v2 dataset.

Metadata admission never executes a proof or model. New rows require both a
real P7 campaign receipt and a separately scheduled full native replay receipt.
The original 2047 train lines and all validation/test files remain byte exact.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat
import sys

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "hydra-playground"
WORKING = APP / "training-v5"
HERE = Path(__file__).resolve().parent
P7 = HERE.parent
STAGED = P7 / "staged"
SPEC_SCHEMA = "hydra-teacher-distillation-input-v1"
DATA_SCHEMA = "hydra-teacher-augmented-primitive-dataset-v1"
BASE_SHA = "e575970df58d046735f492acaf22e1cdea44445608a201c62d0644590b95ea77"
SELECTION_SHA = "26c09c2b28f54073f3964c4772113f7496eceb03107b356b892c619c9cc835d7"
HOLDOUT_SHA = "2a57f12ffe55f90c3c4ac896fba3c2bab47e795b6bb5ba5f15b2c6854cddb58e"
REGISTRY_SHA = "a56dad7ac6368964c039c9ddabab5ac6174939f9684ae23bf6872080cf38c105"
KERNEL_SHA = "ad88855528244707b1fe7bd142d8fea60883a23b429840e07dd1875f3499c45d"
MODEL_ID = "deepseek-ai/DeepSeek-Prover-V2-7B"
REVISION = "a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b"
MODEL_KEY = "deepseek-prover-v2-7b-teacher"
MODEL_PROFILE = "hydra-remote-deepseek-teacher-v1"
CAMPAIGN_PROFILE = "hydra-teacher-continuation-campaign-v1"
PROMPT_CONTRACT = "hydra-deepseek-native-json-teacher-input-v1"
MAX_ROWS = 4096
BASE_ROWS = 2047
MAX_FILES = 1024
MAX_TOTAL_BYTES = 320 * 1024**2
MAX_JSON = 2 * 1024**2
FIXED_P7 = {
    "experimental_teacher.py": "944524ec52ac0166dffa10bda13143357f6c6daad5d7354b820a422158ac45e2",
    "teacher_campaign.py": "53fe5cff56fdb8c7a52bd52cf421d133ede544b03816abfb32c0710f7ad8767e",
    "teacher_native.py": "e1356c7b094341044edf2a4e25fa006cd50250775e6ccb2fb3e331ebdb7fe1af",
    "teacher_states.py": "3b1fe039166a541bc914746bc0fe0723110a17dfe5a6edcdb581b87d585191ab",
}
FROZEN_PILOT_SHA = "284d4bc74b2379dd08ffc4ecc5cb029d9593504e71d53f86761d4d5542b281e8"


class TeacherDataError(ValueError):
    pass


def require(value, message):
    if not value:
        raise TeacherDataError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def digest(value):
    return sha256(canonical(value)).hexdigest()


def strict_json(raw):
    def pairs(values):
        result = {}
        for key, value in values:
            require(key not in result, "Duplicate JSON field.")
            result[key] = value
        return result
    def invalid(value):
        raise TeacherDataError("Nonfinite JSON value: " + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def bootstrap():
    frozen = ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
    sys.path[:0] = [str(APP), str(APP / "native-v7"), str(WORKING), str(STAGED), str(frozen)]
    import peano_lab
    require(Path(peano_lab.__file__).resolve() == APP / "native-v7/peano_lab/__init__.py",
            "Teacher admission selected the wrong native working copy.")


def frozen_data():
    bootstrap()
    from hydra_training_v5 import decision_data
    require(Path(decision_data.__file__).resolve() == WORKING / "hydra_training_v5/decision_data.py",
            "Unexpected frozen decision-data implementation.")
    return decision_data


def verify_working_baseline():
    return frozen_data().verify_working_baseline()


def __getattr__(name):
    if name == "DecisionDataset":
        return frozen_data().DecisionDataset
    raise AttributeError(name)


class Inputs:
    """Finite regular-file input graph. No symlink escape or hash-only trust."""
    def __init__(self, root=ROOT, should_stop=None):
        self.root = Path(root).resolve(strict=True)
        self.should_stop = should_stop
        self.pins, self.raw = {}, {}
        self.total_bytes = 0

    def check(self):
        if self.should_stop and self.should_stop():
            raise TeacherDataError("Teacher data operation cancelled.")

    def path(self, relative):
        require(type(relative) is str and relative and not Path(relative).is_absolute()
                and Path(relative).as_posix() == relative and ".." not in Path(relative).parts,
                "Expected a canonical project-relative evidence path.")
        path = self.root / relative
        require(path.resolve() == path, "Evidence path escapes through a symlink.")
        return path

    def read(self, relative, expected=None, maximum=MAX_JSON):
        self.check()
        path = self.path(relative)
        if relative not in self.raw:
            require(len(self.raw) < MAX_FILES, "Teacher evidence file count exceeds its bound.")
            before = path.lstat()
            require(stat.S_ISREG(before.st_mode) and 0 <= before.st_size <= maximum
                    and self.total_bytes + before.st_size <= MAX_TOTAL_BYTES,
                    "Teacher evidence file/total bytes exceed their bounds.")
            with path.open("rb") as stream:
                raw = stream.read(maximum + 1)
            after = path.lstat()
            require(len(raw) == before.st_size and len(raw) <= maximum
                    and (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
                    == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns),
                    "Evidence changed during its bounded read.")
            self.raw[relative] = raw
            self.total_bytes += len(raw)
            self.pins[relative] = {"path": relative, "bytes": len(raw), "sha256": sha256(raw).hexdigest()}
        raw, pin = self.raw[relative], self.pins[relative]
        require(len(raw) <= maximum, "Cached evidence exceeds this input's bound.")
        if expected is not None:
            value = expected if type(expected) is str else expected.get("sha256")
            require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value)
                    and pin["sha256"] == value, "Pinned teacher evidence changed: " + relative)
            if type(expected) is dict and "bytes" in expected:
                require(pin["bytes"] == expected["bytes"], "Pinned evidence size changed.")
        return raw

    def json(self, relative, expected=None, maximum=MAX_JSON):
        result = strict_json(self.read(relative, expected, maximum))
        require(type(result) is dict, "Expected a JSON evidence object.")
        return result

    def reference(self, record, maximum=MAX_JSON):
        require(type(record) is dict and set(record) <= {"path", "sha256", "bytes"}
                and {"path", "sha256"} <= set(record), "Missing exact evidence reference.")
        return self.json(record["path"], record, maximum)


def source_pins():
    paths = sorted(HERE.glob("*.py")) + [HERE / "DERIVATION.json",
        WORKING / "hydra_training_v5/decision_pilot.py", WORKING / "hydra_training_v5/decision_data.py",
        APP / "export_decisions.py", APP / "planner_provider.py", APP / "proof_planner.py",
        APP / "experimental_model.py", STAGED / "experimental-models/deepseek-teacher-v1.json"]
    result = {}
    for path in paths:
        raw = path.read_bytes()
        require(path.is_file() and not path.is_symlink() and len(raw) <= MAX_JSON,
                "Missing/oversized teacher extension source.")
        result[path.relative_to(ROOT).as_posix()] = sha256(raw).hexdigest()
    require(result[(WORKING / "hydra_training_v5/decision_pilot.py").relative_to(ROOT).as_posix()]
            == FROZEN_PILOT_SHA, "The original frozen pilot changed.")
    return result


def validate_native_trace(result, state):
    """Validate complete recorded transitions; this function never runs them."""
    commands, trace, origins = result.get("commands"), result.get("trace"), result.get("provenance")
    require(result.get("schema") == "hydra-teacher-native-result-v1"
            and result.get("status") == "proved" and result.get("kernel_checked") is True
            and result.get("independent_replay_checked") is True
            and result.get("positive_distillation_eligible") is True
            and result.get("original_theorem") == state["theorem"]
            and result.get("state_id") == state["id"] and result.get("kernel_identity") == KERNEL_SHA
            and result.get("final_goals") == [], "Only complete original-theorem teacher continuations are admissible.")
    prefix = state["commands_before"]
    require(type(commands) is list and 2 <= len(prefix) <= 24 and len(prefix) < len(commands) <= 96
            and commands[:len(prefix)] == prefix and result.get("prefix_commands") == prefix
            and type(trace) is list and len(trace) == len(commands) + 1
            and type(origins) is list and len(origins) == len(commands), "Missing exact prefix/full continuation.")
    require(trace[0].get("goals_before") == ["⊢ " + state["theorem"]]
            and trace[len(prefix)].get("goals_before") == state["all_goals_before"],
            "Complete replay changed its original theorem or selected full state.")
    teacher_steps = 0
    for index, (command, row, origin) in enumerate(zip(commands, trace[:-1], origins)):
        require(type(command) is str and 0 < len(command.encode()) <= 4096 and command.isprintable()
                and ";" not in command and command.split()[0] not in {"qed", "use"},
                "Only bounded ordinary no-import native actions are admitted.")
        require(row.get("step") == index + 1 and row.get("status") == "ok" and row.get("error") is None
                and row.get("focus") == 0 and row.get("tactic") == command
                and row.get("origin") == origin and origin.get("command") == command,
                "Native replay step/provenance is missing or changed.")
        for goals in (row.get("goals_before"), row.get("goals_after")):
            require(type(goals) is list and len(goals) <= 16 and len(canonical(goals)) <= 16384
                    and all(type(g) is str and g.count("⊢") == 1 and "?" not in g for g in goals),
                    "Native replay omitted or changed its bounded complete goal tuple.")
        if index:
            require(trace[index-1]["goals_after"] == row["goals_before"], "Replay goal chain is discontinuous.")
        if index < len(prefix):
            require(origin == state["prefix_provenance"][index] and origin.get("source") == "recorded_prefix",
                    "The teacher cannot claim previously recorded prefix work.")
        else:
            require(origin.get("source") in {"teacher_model", "heuristic"},
                    "Manual/test/backend or unrelated proof steps cannot become teacher data.")
            teacher_steps += origin["source"] == "teacher_model"
    final = trace[-1]
    replay = result.get("replay") or {}
    require(teacher_steps >= 1 and type(result["counts"].get("teacher_steps_accepted")) is int
            and result["counts"]["teacher_steps_accepted"] == teacher_steps
            and final.get("qed") is True and final.get("theorem") == state["theorem"]
            and final.get("tactic_count") == len(commands)
            and type(final.get("proof_size")) is int and final["proof_size"] > 0
            and trace[-2]["goals_after"] == []
            and replay.get("status") == "proved" and replay.get("kernel_checked") is True
            and replay.get("goals") == [] and replay.get("proof_nodes") == final["proof_size"],
            "A full independent original-goal qed with actual teacher steps is required.")
    return trace[:-1]


def validate_owned_execution(record, *, result_sha):
    require(record.get("actual_exit_code") == 0 and type(record.get("actual_exit_code")) is int
            and record.get("quiescent") is True and record.get("launched") is True
            and record.get("stopped_for") is None and record.get("child_result_sha256") == result_sha
            and record.get("automatic_retry") is False,
            "A resource-stopped/unreaped/nonzero child cannot provide positive evidence.")


def validate_teacher_identity(identity, registry):
    require(identity.get("schema") == "hydra-loaded-remote-teacher-v1"
            and identity.get("profile") == MODEL_PROFILE and identity.get("model_key") == MODEL_KEY
            and identity.get("model_id") == MODEL_ID and identity.get("revision") == REVISION
            and identity.get("registry_sha256") == REGISTRY_SHA
            and identity.get("model_loaded") is True and identity.get("adapter_present") is False
            and identity.get("automatic_download") is False and identity.get("automatic_retry") is False
            and identity.get("prompt_contract") == PROMPT_CONTRACT
            and identity.get("source_sha256") == FIXED_P7["experimental_teacher.py"],
            "The producer was not the admitted actual teacher implementation.")
    require(digest({k: v for k, v in identity.items() if k != "model_manifest_sha256"})
            == identity.get("model_manifest_sha256"), "Loaded teacher identity changed.")
    base = identity.get("base") or {}
    require(base.get("files") == {**registry["metadata_files"], **registry["weight_files"]}
            and base.get("weight_bytes_fully_hashed") is True
            and base.get("model_id") == MODEL_ID and base.get("revision") == REVISION
            and base.get("registry_sha256") == REGISTRY_SHA
            and digest({k: v for k, v in base.items() if k != "base_identity_sha256"})
                == base.get("base_identity_sha256"), "Teacher base-byte authentication differs.")


def validate_proposal(record, state, identity, selected_index):
    require(record.get("schema") == "hydra-teacher-proposal-batch-v1"
            and record.get("state_id") == state["id"] and record.get("status") == "proposals"
            and type(record.get("actual_model_calls")) is int and record["actual_model_calls"] == 1
            and type(record.get("generated_tokens")) is int and 1 <= record["generated_tokens"] <= 512,
            "A checked tactic without an actual teacher decode is not a teacher example.")
    provider = record.get("provider") or {}
    backend = provider.get("provider") or {}
    require(provider.get("available") is True and provider.get("test_backend") is False
            and backend.get("kind") == "local_model" and backend.get("name") == MODEL_KEY
            and backend.get("model_manifest_sha256") == identity["model_manifest_sha256"]
            and backend.get("tokenizer_sha256") == identity["tokenizer_sha256"],
            "Test providers or changed model/tokenizer identities are forbidden.")
    model_input, output = record.get("input") or {}, record.get("output") or {}
    input_ids, output_ids = model_input.get("input_token_ids"), output.get("output_token_ids")
    require(type(input_ids) is list and 0 < len(input_ids) <= 4096
            and model_input.get("input_tokens") == len(input_ids)
            and model_input.get("prompt_contract") == PROMPT_CONTRACT
            and model_input.get("chat_template_sha256") == identity["chat_template_sha256"]
            and type(output_ids) is list and len(output_ids) == record["generated_tokens"]
            and all(type(t) is int and 0 <= t < 102400 for t in input_ids + output_ids)
            and type(model_input.get("p4_prompt")) is str
            and sha256(model_input["p4_prompt"].encode()).hexdigest() == record.get("prompt_sha256")
            and type(output.get("decoded_text")) is str and len(output["decoded_text"].encode()) <= 32768,
            "Missing actual bounded teacher prompt/token/output evidence.")
    plans = record.get("plans")
    require(type(plans) is list and 1 <= len(plans) <= 2 and type(selected_index) is int
            and 0 <= selected_index < len(plans), "Missing selected teacher plan.")
    plan = plans[selected_index]
    require(plan.get("source") == "planner_model" and type(plan.get("commands")) is list
            and 1 <= len(plan["commands"]) <= 32 and len(canonical(plan["commands"])) <= 16384,
            "The selected plan is not a bounded actual model proposal.")
    return plan


def verify_compiled_output(record, state, snapshot):
    """Recompile recorded JSON with the same P4 parser; never run a tactic."""
    bootstrap()
    from teacher_campaign import planner_context
    from planner_provider import PlannerBackendIdentity, render_planner_prompt, _INSTRUCTIONS
    from proof_planner import compile_plan, decode_plan_document
    from experimental_teacher import _PREFIX
    prompt = record["input"]["p4_prompt"]
    require(prompt.startswith(_INSTRUCTIONS) and record["input"].get("teacher_message") == _PREFIX + prompt,
            "The recorded full teacher/P4 prompt contract differs.")
    context_data = strict_json(prompt[len(_INSTRUCTIONS):])
    identity_data = dict(record["provider"]["provider"])
    identity_data.pop("prompt_contract", None)
    identity = PlannerBackendIdentity(**identity_data)
    context = planner_context(state, snapshot, failures=context_data["recent_failures"],
                              remaining=context_data["remaining_budget"])
    require(render_planner_prompt(context, identity) == prompt, "Recorded teacher input is not this complete native state.")
    specs = decode_plan_document(record["output"]["decoded_text"])
    plans, seen = [], set()
    for spec in specs:
        plan = compile_plan(spec, context, source="planner_model")
        if plan.commands in seen:
            continue
        seen.add(plan.commands)
        plans.append({"commands": list(plan.commands), "reason": plan.reason, "source": plan.source,
                      "plan_sha256": plan.plan_sha256, "ast_nodes": plan.ast_nodes})
    require(plans == record["plans"], "Recorded commands do not follow from the actual teacher JSON output.")


def load_campaign(inputs, spec):
    selection = inputs.reference(spec["selection"])
    require(spec["selection"]["sha256"] == SELECTION_SHA and selection.get("training_only") is True
            and selection.get("dataset_sha256") == BASE_SHA and len(selection.get("states", [])) == 32,
            "The teacher cohort must be the exact frozen 32 training states.")
    require(selection.get("holdout", {}).get("sha256") == HOLDOUT_SHA,
            "The fixed theorem/template/intermediate-state reservation changed.")
    cohort = selection["states"]
    require(len({s["id"] for s in cohort}) == 32 and all(s.get("split") == "train" for s in cohort),
            "Selection IDs/splits changed.")
    campaign = spec["campaign"]
    directory = campaign["directory"]
    inputs.path(directory)
    request = inputs.json(directory + "/request.json", campaign["request_sha256"])
    completion = inputs.json(directory + "/completion.json", campaign["completion_sha256"])
    admission = inputs.json(directory + "/model-admission.json", campaign["model_admission_sha256"])
    positive = inputs.json(directory + "/positive-continuations.json", campaign["positives_sha256"])
    exit_raw = inputs.read(campaign["actual_process_exit"]["path"], campaign["actual_process_exit"], 32)
    require(exit_raw.strip() == b"0", "Teacher campaign has no successful actual outer process exit.")
    require(request.get("profile") == completion.get("profile") == CAMPAIGN_PROFILE
            and request.get("selection_sha256") == SELECTION_SHA
            and request.get("selected_ids") == [s["id"] for s in cohort]
            and request.get("states") == 32 and request.get("max_calls") == 64
            and request.get("max_proposals") == 128 and request.get("automatic_retry") is False
            and completion.get("completed") is True and completion.get("error") is None
            and completion.get("states_completed") == completion.get("selected_states") == 32
            and completion.get("sources_unchanged") is True
            and completion.get("source_pins_after") == request.get("source_pins_before")
            and digest(request["source_pins_before"]) == request.get("source_pins_sha256")
            == campaign["source_pins_sha256"], "The complete bounded teacher campaign/source receipt differs.")
    for name, expected in FIXED_P7.items():
        relative = "output/p7-prototype/staged/" + name
        require(request["source_pins_before"].get(relative) == expected, "Teacher controller source is not the frozen P7 version.")
        inputs.read(relative, expected)
    for name in ("proof_planner.py", "planner_provider.py"):
        relative = "hydra-playground/" + name
        inputs.read(relative, request["source_pins_before"][relative])
    registry_path = "output/p7-prototype/staged/experimental-models/deepseek-teacher-v1.json"
    registry = inputs.json(registry_path, REGISTRY_SHA)
    identity = admission["identity"]
    validate_teacher_identity(identity, registry)
    session = completion.get("session") or {}
    require(session.get("identity") == identity and type(session.get("actual_model_calls")) is int
            and 0 <= session["actual_model_calls"] <= 64
            and type(session.get("generated_tokens")) is int and 0 <= session["generated_tokens"] <= 32768
            and completion.get("optimizer_updates") == completion.get("student_model_calls") == completion.get("solver_calls") == 0,
            "Teacher campaign counters do not establish the declared inference scope.")
    records = positive.get("records")
    require(positive.get("schema") == "hydra-teacher-positive-continuations-v1"
            and positive.get("training_performed") is False and type(records) is list
            and 0 <= len(records) <= 32 and positive.get("positive_count") == len(records)
            and completion.get("positive_continuations") == len(records)
            and session["actual_model_calls"] >= len(records), "Malformed bounded positive continuation index.")
    summaries = completion.get("summaries")
    require(type(summaries) is list and len(summaries) == 32
            and {r["state_id"] for r in summaries} == {s["id"] for s in cohort}, "Missing completed state accounting.")
    selected, seen = [], set()
    for item in sorted(records, key=lambda r: r["index"]):
        index = item["index"]
        require(type(index) is int and 0 <= index < 32 and index not in seen, "Duplicate or invalid positive state index.")
        seen.add(index)
        state = cohort[index]
        summary = next(r for r in summaries if r["state_id"] == state["id"])
        require(item.get("state_id") == state["id"] and item.get("split") == "train"
                and item.get("outcome") == "proved" and item.get("positive_distillation_eligible") is True
                and item.get("selection_sha256") == SELECTION_SHA
                and item.get("teacher_model_manifest_sha256") == identity["model_manifest_sha256"]
                and all(item.get(k) == summary.get(k) for k in summary), "Positive index does not match its completed state.")
        state_directory = f"{index:03d}-" + state["id"][:16]
        native_name = item["successful_native_record"]
        execution_name = item["native_execution_record"]
        proposal_name = item["teacher_proposal_record"]
        require(all(type(name) is str and name.startswith(state_directory + "/") for name in
                    (native_name, execution_name, proposal_name)), "Positive paths point at another state.")
        native = inputs.json(directory + "/" + native_name, item["successful_native_sha256"])
        execution = inputs.json(directory + "/" + execution_name, item["native_execution_sha256"])
        validate_owned_execution(execution, result_sha=item["successful_native_sha256"])
        trace = validate_native_trace(native, state)
        proposal = inputs.json(directory + "/" + proposal_name, item["teacher_proposal_sha256"])
        plan = validate_proposal(proposal, state, identity, item["teacher_plan_index"])
        require(plan["plan_sha256"] == item["teacher_plan_sha256"] == native.get("teacher_plan_sha256"),
                "Teacher proposal and native continuation refer to different plans.")
        prefix_name = directory + "/" + state_directory + "/prefix/result.json"
        snapshot = inputs.json(prefix_name)
        prefix_exec = inputs.json(directory + "/" + state_directory + "/prefix/execution.json")
        validate_owned_execution(prefix_exec, result_sha=inputs.pins[prefix_name]["sha256"])
        require(snapshot.get("state_id") == state["id"] and snapshot.get("prefix_commands") == state["commands_before"]
                and snapshot.get("all_goals_before") == state["all_goals_before"], "Fresh prefix receipt changed.")
        verify_compiled_output(proposal, state, snapshot)
        used = [o["command"] for o in native["provenance"] if o["source"] == "teacher_model"]
        require(used == plan["commands"][:len(used)] and used,
                "Accepted teacher commands do not belong to the actual proposed plan.")
        selected.append({"state": state, "native": native, "trace": trace,
            "source": inputs.pins[directory + "/" + native_name],
            "teacher_proposal": inputs.pins[directory + "/" + proposal_name],
            "teacher_model_manifest_sha256": identity["model_manifest_sha256"]})
    return selection, selected, {"campaign_completion": inputs.pins[directory + "/completion.json"],
        "positive_teacher_continuations": len(selected), "actual_teacher_model_calls": session["actual_model_calls"],
        "actual_teacher_generated_tokens": session["generated_tokens"],
        "teacher_model_manifest_sha256": identity["model_manifest_sha256"]}


def merge_rows(base_raw, additions, *, maximum=MAX_ROWS):
    """Keep all original line bytes; no sampling, row dropping or relabeling."""
    require(type(base_raw) is bytes and base_raw.endswith(b"\n"), "Base training rows must retain their exact line encoding.")
    lines = base_raw.splitlines()
    require(len(lines) == BASE_ROWS, "The entire fixed 2047-row base must be preserved.")
    base = [strict_json(line) for line in lines]
    ids = {row["id"] for row in base}
    require(len(ids) == BASE_ROWS, "Base IDs are not unique.")
    seen = {(row["prompt"], row["completion"]) for row in base}
    appended, duplicate = [], 0
    for row in additions:
        require(row.get("split") == "train", "Teacher rows cannot change validation or test exposure.")
        key = (row["prompt"], row["completion"])
        if key in seen:
            duplicate += 1
            continue
        require(row["id"] not in ids, "Different content reused a training example ID.")
        seen.add(key); ids.add(row["id"]); appended.append(row)
    require(BASE_ROWS + len(appended) <= maximum <= MAX_ROWS,
            "Teacher augmentation exceeds 4096 rows; it must not silently drop the base or teacher rows.")
    raw = base_raw + b"".join(canonical(row) + b"\n" for row in appended)
    return raw, appended, {"base_rows_preserved": BASE_ROWS, "teacher_rows_added": len(appended),
        "duplicate_teacher_rows_omitted": duplicate, "rows_dropped_for_budget": 0,
        "base_train_prefix_sha256": sha256(base_raw).hexdigest()}


def load_inputs(spec_path, *, expected_sha256, root=ROOT, should_stop=None):
    inputs = Inputs(root, should_stop)
    spec = inputs.json(spec_path, expected_sha256)
    require(set(spec) == {"schema", "base_dataset", "selection", "campaign"}
            and spec["schema"] == SPEC_SCHEMA and spec["base_dataset"]["sha256"] == BASE_SHA,
            "Expected the explicit teacher extension of the fixed v2 base dataset.")
    base = frozen_data().attest_decision_dataset(spec["base_dataset"]["path"],
        expected_sha256=BASE_SHA, workspace=inputs.root)
    require(len(base.train) == BASE_ROWS, "The admitted v2 base must have all 2047 original training rows.")
    base_manifest = inputs.reference(spec["base_dataset"])
    for pin in base_manifest["inputs"]:
        inputs.read(pin["path"], pin, 128 * 1024**2)
    directory = Path(spec["base_dataset"]["path"]).parent
    files = {name: inputs.read((directory / name).as_posix(), pin, 128 * 1024**2)
             for name, pin in base_manifest["files"].items()}
    selection, candidates, campaign = load_campaign(inputs, spec)
    return inputs, spec, base, base_manifest, files, selection, candidates, campaign


def validate_fresh_replay(record, candidate):
    state, native = candidate["state"], candidate["native"]
    require(record.get("schema") == "hydra-teacher-fresh-replay-result-v1"
            and record.get("status") == "verified" and record.get("kernel_checked") is True
            and record.get("state_id") == state["id"] and record.get("kernel_identity") == KERNEL_SHA
            and record.get("native_source_sha256") == candidate["source"]["sha256"]
            and record.get("commands_sha256") == digest(native["commands"])
            and record.get("model_calls") == record.get("solver_calls") == 0,
            "A newly checked original-theorem replay must support every teacher continuation.")
    replay = record.get("replay") or {}
    trace = replay.get("trace")
    require(replay.get("status") == "proved" and replay.get("kernel_checked") is True
            and replay.get("theorem") == state["theorem"] and replay.get("goals") == []
            and replay.get("commands") == native["commands"] and type(trace) is list
            and len(trace) == len(native["trace"]), "The fresh replay is incomplete or proves another statement.")
    for expected, row in zip(native["trace"][:-1], trace[:-1]):
        require(all(row.get(key) == expected.get(key) for key in
                    ("step", "tactic", "focus", "status", "error", "goals_before", "goals_after")),
                "The fresh replay did not reproduce every full native state transition.")
    final = trace[-1]
    require(final.get("qed") is True and final.get("theorem") == state["theorem"]
            and final.get("tactic_count") == len(native["commands"])
            and type(final.get("proof_size")) is int and final["proof_size"] > 0
            and final["proof_size"] == replay.get("proof_nodes") and trace[-2]["goals_after"] == [],
            "Fresh original-theorem replay has no complete final certificate.")


def load_replays(inputs, reference, actual_exit, *, spec_sha, candidates):
    from teacher_replay import replay_sources
    batch = inputs.reference(reference)
    require(inputs.read(actual_exit["path"], actual_exit, 32).strip() == b"0",
            "The fresh replay batch has no successful actual owning-process exit.")
    require(batch.get("schema") == "hydra-teacher-fresh-replay-batch-v1"
            and batch.get("completed") is True and batch.get("input_spec_sha256") == spec_sha
            and batch.get("selection_sha256") == SELECTION_SHA
            and batch.get("sources_unchanged") is True
            and batch.get("source_pins_before") == batch.get("source_pins_after")
            == replay_sources()
            and batch.get("model_calls") == batch.get("solver_calls") == 0,
            "Fresh replay batch is incomplete, changed, or refers to another teacher cohort.")
    records = batch.get("records")
    require(type(records) is list and len(records) == len(candidates)
            and {row["state_id"] for row in records} == {row["state"]["id"] for row in candidates},
            "Fresh replay batch omitted or substituted a teacher continuation.")
    eligible, failures = [], []
    for candidate in candidates:
        item = next(row for row in records if row["state_id"] == candidate["state"]["id"])
        execution = inputs.reference(item["execution"])
        if item.get("status") != "verified":
            require(execution.get("quiescent") is True, "An unreaped replay child blocks all admission.")
            failures.append({"state_id": item["state_id"], "status": item.get("status"),
                             "censored": True, "positive_rows": 0})
            continue
        value = inputs.reference(item["result"])
        validate_owned_execution(execution, result_sha=item["result"]["sha256"])
        validate_fresh_replay(value, candidate)
        eligible.append({**candidate, "fresh_replay": item["result"],
                         "fresh_execution": item["execution"]})
    return eligible, failures


def require_training_component(state, group, theorem_identity):
    require(group is not None and group.get("split") == "train" and state.get("split") == "train"
            and theorem_identity == state.get("theorem_identity")
            and {"statement:" + theorem_identity, "family:" + state["family"],
                 "template:" + state["template_family"]} <= set(group.get("members", ())),
            "Teacher theorem/template belongs outside the admitted training component.")


def continuation_rows(candidates, *, selection, base_manifest, inputs):
    """Render v4 primitive targets only from fully replayed continuation suffixes."""
    exporter = frozen_data()._exporter()
    reservation = exporter.Reservation(inputs.reference(selection["holdout"]), exporter.NativeIdentity())
    groups = {group["group"]: group for group in base_manifest["groups"]}
    rows = []
    continuations = []
    for candidate in candidates:
        inputs.check()
        state, native = candidate["state"], candidate["native"]
        group = groups.get(state["split_group"])
        identity = reservation.identity(state["theorem"])
        require_training_component(state, group, identity)
        require(reservation.reason(state["theorem"], state["family"], state["template_family"], state["case_id"]) is None,
                "Reserved theorem/template is forbidden in teacher distillation.")
        for row in candidate["trace"]:
            require(reservation.goals_reason(row["goals_before"] + row["goals_after"]) is None,
                    "A teacher proof crossed a reserved or unparseable intermediate state.")
        prefix = len(state["commands_before"])
        for index, row in enumerate(candidate["trace"]):
            if index < prefix:
                continue
            require(exporter.primitive(row["tactic"]) and not row["tactic"].startswith("use "),
                    "A teacher continuation cannot introduce another primitive authority.")
            rendered = exporter.primitive_prompt(row["goals_before"], row["tactic"])
            rid = exporter.digest([exporter.SFT_SCHEMA, identity, rendered["prompt"], rendered["completion"]])
            value = {"schema": exporter.SFT_SCHEMA, "id": rid, **rendered,
                "theorem": state["theorem"], "theorem_identity": identity, "case_id": state["case_id"],
                "family": state["family"], "template_family": state["template_family"],
                "split_group": state["split_group"], "split": "train", "focus": 0,
                "goals_before": row["goals_before"], "goals_after": row["goals_after"],
                "action": row["tactic"], "step": row["step"], "remaining_steps": len(candidate["trace"]) - index,
                "kernel_checked": True, "censored": False, "benchmark_claim": False,
                "verification_scope": "recorded_full_original_goal_independent_native_replay",
                "reserved_intermediate_check": "exact_closed_AST_plus_declared_template_exclusions",
                "winning_source": row["origin"]["source"], "partial_proof_cost": None,
                "final_proof_cost": native["proof_cost"], "runtime_profile": CAMPAIGN_PROFILE,
                "source": {**candidate["source"], "owner": "project"},
                "teacher_evidence": {"state_id": state["id"], "selection_sha256": SELECTION_SHA,
                    "teacher_model_manifest_sha256": candidate["teacher_model_manifest_sha256"],
                    "actual_teacher_proposal": candidate["teacher_proposal"],
                    "fresh_original_theorem_replay": candidate["fresh_replay"],
                    "fresh_replay_execution": candidate["fresh_execution"],
                    "source_scope": "complete_teacher_proposed_native_continuation",
                    "teacher_step": row["origin"]["source"] == "teacher_model"}}
            frozen_data().validate_primitive_row(value, split="train")
            rows.append(value)
        continuations.append({"state_id": state["id"], "theorem": state["theorem"],
            "commands_sha256": digest(native["commands"]), "complete_commands": native["commands"],
            "prefix_steps_excluded_from_new_rows": prefix, "fresh_replay": candidate["fresh_replay"],
            "native_source": candidate["source"], "teacher_proposal": candidate["teacher_proposal"]})
    return rows, continuations


def write_new(path, raw):
    require(type(raw) is bytes and len(raw) <= 128 * 1024**2, "Generated data exceeds its byte bound.")
    with Path(path).open("xb") as stream:
        stream.write(raw)


def export_dataset(spec_path, *, expected_sha256, output, replay_manifest=None, replay_exit=None,
                   root=ROOT, should_stop=None):
    before = source_pins()
    loaded = load_inputs(spec_path, expected_sha256=expected_sha256, root=root, should_stop=should_stop)
    inputs, spec, base, base_manifest, files, selection, candidates, campaign = loaded
    output = Path(output)
    require(not output.exists() and not output.is_symlink(), "A new teacher dataset directory is required.")
    output.mkdir(parents=True, exist_ok=False)
    failure_base = {"schema": DATA_SCHEMA, "training_allowed": False, "model_trained": False,
        "input_spec": inputs.pins[spec_path], "base_dataset": spec["base_dataset"],
        "base_rows_preserved": BASE_ROWS, "teacher_rows_added": 0, **campaign,
        "native_proof_runs_by_exporter": 0, "student_model_calls": 0, "automatic_retry": False}
    if not candidates:
        blocked = {**failure_base, "status": "blocked_zero_teacher_continuations"}
        write_new(output / "blocked.json", canonical(blocked) + b"\n")
        return blocked
    require(replay_manifest is not None and replay_exit is not None,
            "Actual complete teacher proofs need separately scheduled fresh native replay admission.")
    eligible, failures = load_replays(inputs, replay_manifest, replay_exit,
                                      spec_sha=expected_sha256, candidates=candidates)
    additions, continuations = continuation_rows(eligible, selection=selection, base_manifest=base_manifest, inputs=inputs)
    train, new_rows, merge = merge_rows(files["primitive-train.jsonl"], additions)
    if not new_rows:
        blocked = {**failure_base, **merge, "status": "blocked_no_new_fully_replayed_rows",
            "fresh_verified_continuations": len(eligible), "replay_failures": failures}
        write_new(output / "blocked.json", canonical(blocked) + b"\n")
        return blocked
    files["primitive-train.jsonl"] = train
    files["teacher-continuations.jsonl"] = b"".join(canonical(row) + b"\n" for row in continuations)
    file_pins = {}
    for name, raw in sorted(files.items()):
        write_new(output / name, raw)
        file_pins[name] = {"bytes": len(raw), "sha256": sha256(raw).hexdigest(), "rows": len(raw.splitlines())}
    require(source_pins() == before, "Teacher dataset source changed during export.")
    manifest = {"schema": DATA_SCHEMA, "status": "complete", "training_allowed": True,
        "input_spec": inputs.pins[spec_path], "base_dataset": spec["base_dataset"],
        "selection_sha256": SELECTION_SHA, "base_attestation": base.attestation,
        "fresh_replay_manifest": replay_manifest, "fresh_replay_actual_exit": replay_exit,
        "source_pins": before, "sources_unchanged": True,
        "inputs": sorted(inputs.pins.values(), key=lambda p: p["path"]), "files": file_pins,
        "schema_mode": "primitive_v4", "structured_planner_rows": 0,
        "max_train_rows": MAX_ROWS, "training_rows": BASE_ROWS + len(new_rows), **merge, **campaign,
        "fresh_verified_continuations": len(eligible), "replay_failures": failures,
        "validation_bytes_unchanged": True, "test_bytes_unchanged": True,
        "ranker_files_unchanged": True, "website_data_allowed": False,
        "holdout_sha256": selection["holdout"]["sha256"], "reserved_cohort_states": 32,
        "reserved_intermediate_check": "exact_closed_AST_plus_declared_template_exclusions",
        "teacher_source_scope": "complete_teacher_proposed_native_continuation",
        "native_proof_runs_by_exporter": 0, "model_calls_by_exporter": 0,
        "training_performed": False, "automatic_retry": False, "benchmark_claim": False}
    write_new(output / "manifest.json", canonical(manifest) + b"\n")
    return manifest


def attest_teacher_dataset(manifest_path, *, expected_sha256, workspace=ROOT, failure_output=None):
    """Reproduce the extension exactly. This is not another native proof run."""
    import tempfile
    inputs = Inputs(workspace)
    path = Path(manifest_path)
    relative = path.relative_to(inputs.root).as_posix() if path.is_absolute() else path.as_posix()
    manifest = inputs.json(relative, expected_sha256)
    require(manifest.get("schema") == DATA_SCHEMA and manifest.get("status") == "complete"
            and manifest.get("training_allowed") is True and type(manifest.get("teacher_rows_added")) is int
            and manifest["teacher_rows_added"] > 0 and manifest.get("base_rows_preserved") == BASE_ROWS
            and type(manifest.get("training_rows")) is int
            and manifest["training_rows"] == BASE_ROWS + manifest["teacher_rows_added"] <= MAX_ROWS,
            "Zero, partial or unverified teacher output cannot authorize a student update.")
    require(manifest.get("source_pins") == source_pins(), "Teacher dataset extension code changed.")
    directory = Path(relative).parent
    actual = {name: inputs.read((directory / name).as_posix(), pin, 128 * 1024**2)
              for name, pin in manifest["files"].items()}
    with tempfile.TemporaryDirectory(prefix="hydra-teacher-data-admission-") as temporary:
        destination = Path(temporary) / "regenerated"
        regenerated = export_dataset(manifest["input_spec"]["path"],
            expected_sha256=manifest["input_spec"]["sha256"], output=destination,
            replay_manifest=manifest["fresh_replay_manifest"], replay_exit=manifest["fresh_replay_actual_exit"], root=inputs.root)
        require(canonical(regenerated) == canonical(manifest), "Teacher data manifest does not reproduce byte exactly.")
        require(all((destination / name).read_bytes() == raw for name, raw in actual.items()),
                "Teacher data row bytes differ from full evidence regeneration.")
    frozen = frozen_data()
    rows, ids, groups = {}, set(), {}
    for split in ("train", "val", "test"):
        parsed = []
        for line in actual["primitive-" + split + ".jsonl"].splitlines():
            row = strict_json(line)
            example = frozen.validate_primitive_row(row, split=split)
            require(example.example_id not in ids, "Duplicate teacher/base ID crosses splits.")
            ids.add(example.example_id)
            group = row["split_group"]
            require(group not in groups or groups[group] == split, "Teacher augmentation crossed an evaluation family.")
            groups[group] = split
            parsed.append(example)
        rows[split] = tuple(parsed)
    require(len(rows["train"]) == manifest["training_rows"] and rows["val"], "Augmented train/validation count differs.")
    attestation = {"schema": "hydra-teacher-augmented-data-attestation-v1", "manifest_sha256": expected_sha256,
        "base_manifest_sha256": BASE_SHA, "base_training_rows": BASE_ROWS,
        "teacher_rows_added": manifest["teacher_rows_added"], "training_rows": len(rows["train"]),
        "validation_rows": len(rows["val"]), "test_rows_not_used": len(rows["test"]),
        "selection_sha256": SELECTION_SHA, "source_pins": manifest["source_pins"],
        "holdout_sha256": HOLDOUT_SHA,
        "reserved_intermediate_check": manifest["reserved_intermediate_check"],
        "teacher_source_scope": manifest["teacher_source_scope"],
        "fresh_verified_continuations": manifest["fresh_verified_continuations"],
        "teacher_model_manifest_sha256": manifest["teacher_model_manifest_sha256"],
        "actual_teacher_model_calls": manifest["actual_teacher_model_calls"],
        "teacher_input_spec": manifest["input_spec"],
        "base_attestation_sha256": digest(manifest["base_attestation"]),
        "fresh_replay_manifest": manifest["fresh_replay_manifest"], "regenerated_byte_exact": True,
        "base_train_prefix_preserved": True, "validation_test_unchanged": True,
        "native_replays_performed_by_admission": 0, "benchmark_claim": False}
    return frozen.DecisionDataset(expected_sha256, relative, rows["train"], rows["val"], len(rows["test"]),
        digest([x.example_id for x in rows["train"]]), digest([x.example_id for x in rows["val"]]), attestation)
