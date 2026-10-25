"""Export explicitly pinned project search evidence; never execute a proof/model.

Successful full replay continuations supply primitive SFT and observed-distance
rows. Native rejections, action comparisons, and censored runs have separate
files. No unfinished branch is labelled mathematically false. The CLI performs
bounded native *parsing* for reservation checks, never tactic replay/checking.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys

from branch_ranker import (DISTANCE_SCHEMA, FEATURE_SCHEMA, NUMERIC_ENCODING,
                          canonical, extract_features, validate_goals)

APP = Path(__file__).resolve().parent
ROOT = APP.parent
TRAINING = APP / "training-v5"
INPUT_SCHEMA = "hydra-decision-export-inputs-v1"
EXPORT_SCHEMA = "hydra-decision-export-v2"
SFT_SCHEMA = "hydra-primitive-sft-v1"
HOLDOUT_SHA256 = "2a57f12ffe55f90c3c4ac896fba3c2bab47e795b6bb5ba5f15b2c6854cddb58e"
MAX_INPUT_BYTES = 128 * 1024 * 1024
MAX_RUNS = 16
MAX_CASES = 128
MAX_ROWS = 4096
MAX_RANKING_ROWS = 16384
PRIMITIVES = tuple(sorted(("apply", "assumption", "cases", "compact_arith", "congr",
    "exact", "exfalso", "exists", "forall_elim", "have", "induction", "intro", "left",
    "norm_num", "refl", "rewrite", "right", "ring", "simp", "specialize", "split",
    "suffices", "symm", "trans", "use")))
RESOURCE_RE = re.compile(r"resource|memory|(?:wall|cpu)[-_ ]?(?:time|limit)|timed? ?out|"
                         r"deadline|(?:work|node|proof|certificate|depth|size|fuel)[-_ ]?(?:budget|limit|cap)|"
                         r"too (?:large|deep)|exceed|100000|500000|25000", re.I)


class ExportError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ExportError(message)


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key.")
            result[key] = value
        return result
    def invalid(_):
        raise ExportError("Nonfinite JSON number.")
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    except (ValueError, RecursionError) as error:
        raise ExportError("Malformed bounded JSON: " + str(error)) from error


def safe_path(root, relative):
    require(type(relative) is str and relative and len(relative) <= 1024,
            "Expected a workspace-relative file path.")
    path = PurePosixPath(relative)
    require(not path.is_absolute() and path.as_posix() == relative
            and not set(path.parts) & {".", ".."}, "Noncanonical or escaping input path.")
    current = Path(root)
    require(not current.is_symlink(), "Input root must not be a symbolic link.")
    for part in path.parts:
        current /= part
        require(not current.is_symlink(), "Symbolic-link input paths are forbidden.")
    return current


class Inputs:
    """Stable, bounded, explicitly hashed input reader; no directory harvesting."""
    def __init__(self, root=ROOT):
        self.root = Path(root).absolute()
        self.pins = {}

    def read(self, relative, expected=None, maximum=8*1024*1024):
        path = safe_path(self.root, relative)
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb") as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode) and 0 <= before.st_size <= maximum,
                    "Input is not a bounded regular file: " + relative)
            raw = stream.read(maximum+1)
            after = os.fstat(stream.fileno())
            fields = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
            require(fields(before) == fields(after) == fields(path.lstat())
                    and len(raw) == before.st_size, "Input changed while reading: " + relative)
        pin = {"path": relative, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        if type(expected) is dict:
            require(pin["sha256"] == expected.get("sha256")
                    and ("bytes" not in expected or pin["bytes"] == expected["bytes"]),
                    "Pinned input mismatch: " + relative)
        elif expected is not None:
            require(pin["sha256"] == expected, "Pinned input mismatch: " + relative)
        require(relative not in self.pins or self.pins[relative] == pin, "Input changed within export.")
        self.pins[relative] = pin
        return raw

    def json(self, relative, expected=None, maximum=8*1024*1024):
        value = decode(self.read(relative, expected, maximum))
        require(type(value) is dict, "Expected a JSON object: " + relative)
        return value

    def reference(self, record, *, maximum=8*1024*1024):
        require(type(record) is dict and type(record.get("path")) is str
                and re.fullmatch(r"[0-9a-f]{64}", str(record.get("sha256"))) is not None,
                "An explicit path and SHA-256 input descriptor are required.")
        return self.json(record["path"], record, maximum)


class NativeIdentity:
    """Original AST identity only; lazy and separate from pure schema tests."""
    def __init__(self):
        frozen = ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831/peano-lab/py"
        if "peano_lab" not in sys.modules:
            sys.path.insert(0, str(frozen))
        from certificate_codec import formula_identity
        from peano_lab.kernel import formulas
        self.identity = formula_identity
        self.formulas = formulas
        from peano_lab.kernel import terms
        self.terms = terms
        self.cache = {}

    def __call__(self, statement):
        require(type(statement) is str and 0 < len(statement.encode("utf-8")) <= 16384,
                "Formula text exceeds the exclusion bound.")
        if statement not in self.cache:
            require(len(self.cache) < 100000, "Formula identity cache bound exceeded.")
            formula, names = self.formulas.parse_formula_with_names(statement)
            require(not names, "Reservation identity requires a closed formula.")
            pending = [(formula,0)]
            work = 0
            while pending:
                node,binders = pending.pop()
                work += 1
                require(work <= 50000 and binders <= 128, "Exclusion AST inspection bound exceeded.")
                if type(node) is self.terms.Var:
                    require(node.index < binders, "Unbound explicit de Bruijn index.")
                elif type(node) in (self.formulas.Forall,self.formulas.Exists):
                    pending.append((node.body,binders+1))
                else:
                    for name in getattr(type(node),"__dataclass_fields__",{}):
                        child = getattr(node,name)
                        if type(child) is not int:
                            pending.append((child,binders))
            self.cache[statement] = self.identity(formula)
        return self.cache[statement]

    def goal_identities(self, goal):
        context, target = goal.split("⊢", 1)
        names = []
        formulas = [target.strip()]
        for declaration in context.strip().split(", ") if context.strip() else ():
            name, separator, body = declaration.partition(" : ")
            require(separator and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_']*", name),
                    "Unrecognized native context declaration.")
            if body == "ℕ":
                names.append(name)
            else:
                formulas.append(body)
        # Bind exactly the native context variables. Unparsed metas are reported
        # as unavailable exclusion evidence, never silently discarded/truncated.
        prefix = "forall " + " ".join(names) + ". " if names else ""
        result = []
        for formula in formulas:
            result.append(self(prefix + "(" + formula + ")"))
            # A closed quantified target may have irrelevant context variables;
            # compare that exact closed formula independently as well.
            try:
                result.append(self(formula))
            except (ValueError, RecursionError):
                pass
        return result


class Reservation:
    def __init__(self, record, identity):
        require(record.get("frozen") is True and type(record.get("cases")) is list,
                "Reservation must be explicitly frozen.")
        rules = record.get("reservation", {})
        require(all(rules.get(key) is False for key in ("training_allowed", "retrieval_allowed",
                "teacher_labeling_for_training_allowed", "distillation_allowed")),
                "Reservation does not exclude all training/retrieval routes.")
        self.identity = identity
        self.identities = {identity(case["theorem"]) for case in record["cases"]}
        self.families = {case[key] for case in record["cases"]
                         for key in ("family", "template_subfamily") if case.get(key)}
        self.case_ids = {case["id"] for case in record["cases"]}

    def reason(self, theorem, family, template_family, case_id):
        if case_id in self.case_ids:
            return "reserved_case_id"
        if family in self.families or template_family in self.families:
            return "reserved_template_or_family"
        if self.identity(theorem) in self.identities:
            return "reserved_exact_ast_statement"
        return None

    def goals_reason(self, goals):
        try:
            for goal in validate_goals(goals):
                identities = self.identity.goal_identities(goal)
                if self.identities.intersection(identities):
                    return "reserved_intermediate_goal_or_assumption"
        except (ValueError, RecursionError) as error:
            return "intermediate_exclusion_unavailable:" + str(error)[:160]
        return None


def primitive(command):
    # This is a data-schema filter, not tactic parsing or command admission.
    return (type(command) is str and 0 < len(command.encode("utf-8")) <= 4096
            and command == command.strip() and "\n" not in command and "\r" not in command
            and not any(marker in command for marker in (";", "<|>", "<tactic>", "</tactic>"))
            and command.split(" ", 1)[0] in PRIMITIVES)


def primitive_prompt(goals, tactic):
    require(primitive(tactic) and not tactic.startswith("use "),
            "Primitive no-import data cannot grant new library authority.")
    if str(TRAINING) not in sys.path:
        sys.path.insert(0, str(TRAINING))
    from hydra_training_v5.peano_policy.prompt import (CapabilityIdentity,
        PromptEnvironment, render_prompt, ProofExample)
    capabilities = CapabilityIdentity("hydra-authority-no-imports-v1", PRIMITIVES, ())
    environment = PromptEnvironment(False, capabilities, prompt_version=4)
    prompt = render_prompt(goals=goals, focus=0, environment=environment)
    completion = tactic + "</tactic>"
    ProofExample(digest([prompt, completion]), prompt, completion, environment.sha256)
    return {"prompt_version": 4, "prompt": prompt, "completion": completion,
            "environment_sha256": environment.sha256,
            "capabilities": capabilities.to_record()}


def receipt_exit(record):
    values = [record[key] for key in ("actual_exit_code", "exit_code") if key in record]
    require(values and all(type(value) is int for value in values)
            and len(set(values)) == 1, "Missing/conflicting actual process exit receipt.")
    return values[0]


def verified_trace(case):
    """Validate an actual completed full replay, not just a success Boolean."""
    job = case.get("last_job", {})
    result = job.get("result") or {}
    execution = job.get("execution") or result.get("execution") or {}
    require(case.get("outcome") == "proved" and case.get("kernel_verified") is True
            and job.get("state") == "completed" and job.get("error") is None
            and result.get("status") == "proved" and result.get("kernel_checked") is True
            and result.get("goals") == [] and result.get("goals_scope") == "final-independent-replay"
            and execution.get("worker_exit_code") == 0 and execution.get("quiescent") is True,
            "Positive SFT requires a completed, quiescent native-replayed original theorem.")
    commands, trace = result.get("commands"), result.get("trace")
    require(type(commands) is list and 0 < len(commands) <= 512 and type(trace) is list
            and len(trace) == len(commands)+1, "Missing/incomplete winning replay trace.")
    require(result.get("theorem") == case.get("canonical_theorem"), "Original theorem/replay mismatch.")
    require(trace[0].get("goals_before") == ["⊢ " + case["canonical_theorem"]],
            "Replay does not start from the recorded original theorem.")
    search = result.get("search", {})
    provenance = search.get("provenance")
    require(type(provenance) is list and len(provenance) == len(commands)
            and search.get("commands") == commands and search.get("kernel_checked") is True,
            "Winning script and search provenance disagree.")
    for index, row in enumerate(trace[:-1]):
        require(type(row) is dict and row.get("step") == index+1
                and row.get("status") == "ok" and row.get("error") is None,
                "Replay contains an unsuccessful or missing transition.")
        validate_goals(row.get("goals_before")); validate_goals(row.get("goals_after"))
        if index:
            require(trace[index-1]["goals_after"] == row["goals_before"],
                    "Replay changed an outstanding goal between steps.")
        require(row.get("tactic") == commands[index] and row.get("focus") == 0
                and row.get("origin") == provenance[index]
                and provenance[index].get("command") == commands[index],
                "Replay command/provenance mismatch.")
    final = trace[-1]
    require(type(final) is dict and final.get("qed") is True
            and final.get("theorem") == case["canonical_theorem"]
            and final.get("tactic_count") == len(commands)
            and type(final.get("proof_size")) is int and final["proof_size"] > 0
            and final["proof_size"] == result.get("proof_nodes")
            and trace[-2]["goals_after"] == [], "Final independent qed is absent or inconsistent.")
    return trace[:-1], result


def family_splits(rows, seed, overrides=None):
    """Connect whole statement identities AND declared template families first."""
    parents = {}
    def find(value):
        parents.setdefault(value, value)
        while parents[value] != value:
            parents[value] = parents[parents[value]]
            value = parents[value]
        return value
    def union(a, b):
        x,y = find(a),find(b)
        parents[max(x,y)] = min(x,y)
    for row in rows:
        union("statement:"+row["theorem_identity"], "family:"+row["family"])
        union("family:"+row["family"], "template:"+row["template_family"])
    groups = defaultdict(list)
    for key in sorted(parents):
        groups[find(key)].append(key)
    keys = sorted(groups, key=lambda k: digest([seed, groups[k]]))
    overrides = overrides or {}
    require(type(overrides) is dict and all(type(key) is str and value in ("train","val","test")
            for key,value in overrides.items()), "Invalid whole-family split overrides.")
    assignments = {}
    for position,key in enumerate(keys):
        # Small pilot still needs nonempty validation/test families when possible.
        fraction = position/max(1,len(keys))
        split = "val" if position == 0 and len(keys) >= 3 else "test" if position == 1 and len(keys) >= 3 else "train"
        if len(keys) >= 10:
            split = "val" if fraction < 0.1 else "test" if fraction < 0.2 else "train"
        declared = {overrides[member.split(":",1)[1]] for member in groups[key]
                    if member.startswith(("family:","template:"))
                    and member.split(":",1)[1] in overrides}
        require(len(declared) <= 1, "Explicit family split conflicts with a connected theorem/template.")
        if declared:
            split = declared.pop()
        group = digest(groups[key])
        assignments[key] = (group,split)
    for row in rows:
        row["split_group"], row["split"] = assignments[find("statement:"+row["theorem_identity"])]
    return [{"group": assignments[key][0], "split": assignments[key][1], "members": groups[key]}
            for key in keys]


def extract_case(case, *, family, template_family, reservation, source):
    """Pure structural extraction given a supplied reservation identity adapter."""
    require(type(family) is str and re.fullmatch(r"[a-z][a-z0-9_]{0,119}", family),
            "Every case needs an explicit underscore family label.")
    require(type(template_family) is str and re.fullmatch(r"[a-z][a-z0-9_]{0,119}", template_family),
            "Every case needs a bounded template-family label.")
    theorem = case.get("canonical_theorem")
    require(type(theorem) is str and theorem, "Case has no original canonical theorem.")
    identity = reservation.identity(theorem)
    common = {"theorem": theorem, "theorem_identity": identity, "family": family,
              "template_family": template_family, "case_id": case["case_id"],
              "source": source, "benchmark_claim": False}
    reason = reservation.reason(theorem, family, template_family, case["case_id"])
    result = (case.get("last_job") or {}).get("result") or {}
    search = result.get("search") or {}
    outcome = {**common, "schema": "hydra-decision-outcome-v1", "outcome": case.get("outcome"),
        "search_status": search.get("status"), "limited_by": search.get("limited_by"),
        "error": (case.get("last_job") or {}).get("error"),
        "censored": case.get("outcome") != "proved", "mathematical_falsity_label": None,
        "model_calls": search.get("model_calls"), "vampire_calls": search.get("vampire_calls"),
        "branches_omitted": search.get("branches_omitted"),
        "diagnostics_omitted": search.get("diagnostics_omitted"),
        "proof_cost": search.get("proof_cost"), "excluded": reason,
        "unavailable_states": 0, "excluded_sft_steps": []}
    sft, distances, attempts, pairs = [],[],[],[]
    if reason:
        return sft, distances, attempts, pairs, outcome
    trace = []
    if case.get("outcome") == "proved":
        trace,result = verified_trace(case)
        require(case.get("expected") not in ("not_provable", "refutable"),
                "A supposedly false control was proved; halt export for review.")
    # Only retained exact parent snapshots are usable. Omitted states stay absent.
    states = {0: (["⊢ " + theorem], 0)}
    for row in trace:
        origin = row["origin"]
        states[origin["parent_id"]] = (row["goals_before"], row["step"]-1)
        states[origin["branch_id"]] = (row["goals_after"], row["step"])
    branches = search.get("branches", [])
    require(type(branches) is list and len(branches) <= 20000, "Invalid bounded branch log.")
    for branch in branches:
        if branch.get("id") is not None and type(branch.get("goals_after")) is list:
            goals = list(validate_goals(branch["goals_after"]))
            value = (goals, branch.get("depth"))
            if branch["id"] in states:
                require(states[branch["id"]] == value, "Branch and replay state snapshots disagree.")
            states[branch["id"]] = value
    winning_actions = defaultdict(list)
    for index,row in enumerate(trace):
        exclusion = reservation.goals_reason(row["goals_before"] + row["goals_after"])
        if exclusion or not primitive(row["tactic"]) or row["tactic"].startswith("use "):
            outcome["excluded_sft_steps"].append({"step": row["step"], "reason": exclusion or "not_no_import_primitive"})
            continue
        rendered = primitive_prompt(row["goals_before"], row["tactic"])
        rid = digest([SFT_SCHEMA, identity, rendered["prompt"], rendered["completion"]])
        sft.append({**common, "schema": SFT_SCHEMA, "id": rid, **rendered,
            "goals_before": row["goals_before"], "goals_after": row["goals_after"],
            "focus": 0, "action": row["tactic"], "step": row["step"],
            "remaining_steps": len(trace)-index, "kernel_checked": True,
            "verification_scope": "recorded_full_original_goal_independent_native_replay",
            "winning_source": row["origin"]["source"],
            "partial_proof_cost": None,
            "final_proof_cost": (search.get("proof_cost") or {}).get("final"),
            "runtime_profile": search.get("profile"), "censored": False,
            "reserved_intermediate_check": "exact_closed_AST_plus_declared_template_exclusions"})
        features = extract_features(row["goals_before"], depth=index)
        distances.append({**common, "schema": DISTANCE_SCHEMA, "feature_schema": FEATURE_SCHEMA,
            "id": digest(["distance", rid, len(trace)-index]), "sft_id": rid,
            "features": features, "all_goals": row["goals_before"], "branch_depth": index,
            "partial_proof_cost": None, "remaining_budget": None,
            "remaining_steps": len(trace)-index, "verified_continuation": True,
            "censored": False, "target_scope": "observed_winning_continuation_not_shortest_proof"})
        winning_actions[digest(row["goals_before"])].append(row["tactic"])
    for branch_index,branch in enumerate(branches):
        parent = states.get(branch.get("parent_id"))
        if parent is None:
            outcome["unavailable_states"] += 1
            continue
        before,depth = parent
        command = branch.get("command")
        if not primitive(command):
            continue
        exclusion = reservation.goals_reason(before + (branch.get("goals_after") or []))
        if exclusion:
            continue
        status = branch.get("status")
        rejected = status == "rejected"
        resource = bool(rejected and RESOURCE_RE.search(str(branch.get("reason", ""))))
        # Admission/authority errors are not native transition results.
        if status not in ("open", "proof", "rejected", "duplicate"):
            continue
        row = {**common, "schema": "hydra-native-action-attempt-v1",
            "id": digest([source, branch_index]), "parent_id": branch.get("parent_id"),
            "branch_id": branch.get("id"), "all_goals_before": before,
            "all_goals_after": branch.get("goals_after"), "action": command,
            "source_component": branch.get("source"), "status": status,
            "native_rejected": rejected, "error": branch.get("reason") if rejected else None,
            "censored": resource or not rejected,
            "outcome_label": "resource_censored" if resource else "native_rejected" if rejected else "accepted_outcome_unresolved",
            "proof_cost": None, "depth": depth, "mathematical_falsity_label": None}
        attempts.append(row)
        if rejected and not resource:
            for winner in sorted(set(winning_actions[digest(before)])):
                if winner == command:
                    continue
                pairs.append({**common, "schema": "hydra-action-preference-v1",
                    "id": digest([source, before, winner, command]),
                    "all_goals": before, "preferred_action": winner, "rejected_action": command,
                    "label": "checked_continuation_over_recorded_native_rejection",
                    "native_error": branch.get("reason"), "censored": False,
                    "branch_ranker_training_eligible": False,
                    "mathematical_impossibility_claim": False})
    return sft,distances,attempts,pairs,outcome


def load_run(inputs, specification, *, website_opt_in=False):
    owner = specification.get("owner")
    require(owner in ("project", "website"), "Explicit data ownership is required.")
    if owner == "website":
        require(website_opt_in and specification.get("training_opt_in") is True,
                "Website jobs are excluded without explicit per-bundle opt-in.")
    directory = specification.get("directory")
    safe_path(inputs.root, directory)
    summary = inputs.json(directory+"/summary.json", specification.get("summary_sha256"))
    plan = inputs.json(directory+"/plan.json", specification.get("plan_sha256"))
    receipt = inputs.reference(specification["receipt"])
    require(receipt_exit(receipt) == 0 and summary.get("status") == "complete"
            and summary.get("all_requested_cases_completed") is True
            and summary.get("source_pins_unchanged") is True,
            "Only finalized complete run bundles may enter this exporter.")
    require(plan.get("origin") == "live_http_search" and plan.get("automatic_retry") is False,
            "Unsupported run origin or automatic retry.")
    plan_sha = inputs.pins[directory+"/plan.json"]["sha256"]
    source = inputs.json(directory+"/source-pins.json", plan["source_pins"])
    after = inputs.json(directory+"/source-pins-after.json")
    require(source == after, "Run source pins changed before completion.")
    source_sha = inputs.pins[directory+"/source-pins.json"]["sha256"]
    curriculum_descriptor = plan["curriculum"]
    declared_curriculum = specification.get("curriculum")
    if declared_curriculum is not None:
        require(declared_curriculum.get("sha256") == curriculum_descriptor["sha256"],
                "Explicit portable curriculum differs from the original run pin.")
    curriculum_path = (declared_curriculum or curriculum_descriptor)["path"]
    if Path(curriculum_path).is_absolute():
        curriculum_path = Path(curriculum_path).relative_to(inputs.root).as_posix()
    curriculum = inputs.json(curriculum_path, curriculum_descriptor)
    cases_by_id = {case["id"]:case for case in curriculum["cases"]}
    selected = specification.get("case_ids")
    require(selected is None or type(selected) is list and len(set(selected)) == len(selected),
            "Invalid explicit case selection.")
    pins = summary.get("case_file_pins")
    require(type(pins) is dict and 1 <= len(pins) <= MAX_CASES, "Missing case-file pins.")
    records = []
    for filename,pin in sorted(pins.items()):
        case = inputs.json(directory+"/"+filename, pin)
        if selected is not None and case.get("case_id") not in selected:
            continue
        require(case.get("schema") == "hydra-advanced-http-case-v1"
                and case.get("origin") == "live_http_search"
                and case.get("reference_scripts_sent_to_server") is False
                and case.get("submission_count") == 1 and case.get("automatic_retry") is False
                and case.get("run_context") == {"plan_sha256": plan_sha, "source_pins_sha256": source_sha},
                "Case has an unsupported origin or broken plan/source binding.")
        require(case.get("case_id") in cases_by_id, "Case missing from pinned curriculum.")
        planned = [item for item in plan["jobs"] if item["case_id"] == case["case_id"]
                   and item["mode"] == case["search_mode"]]
        require(len(planned) == 1 and case["request"] == planned[0]["request"]
                and case["request"]["theorem"] == cases_by_id[case["case_id"]]["theorem"],
                "Case request differs from the pinned theorem-only plan.")
        metadata = dict(cases_by_id[case["case_id"]])
        assignment = specification.get("family_assignments", {}).get(case["case_id"], {})
        require(type(assignment) is dict and not set(assignment)-{"family", "template_family"},
                "Family overrides cannot change proofs or statements.")
        family = assignment.get("family", metadata.get("family"))
        template = assignment.get("template_family", metadata.get("template_subfamily", family))
        records.append((case, family, template, {"path": directory+"/"+filename,
            "sha256": pin["sha256"], "job_id": case.get("job_id"), "owner": owner,
            "source_pins_sha256": source_sha, "plan_sha256": plan_sha}))
    require(selected is None or set(selected) == {case[0]["case_id"] for case in records},
            "Requested case selection was not completely recorded.")
    return records


def retention_rows(inputs, spec, reservation):
    """Keep earlier TRAIN positives only, with their actual origin receipt pins.

    No DEV-to-TRAIN relabelling; old prompt/completion bytes are retained exactly.
    The historical training manifest is source evidence, not a new native replay.
    """
    preparation = inputs.reference(spec["manifest"])
    training = inputs.reference(spec["training_manifest"])
    require(training.get("model_trained") is True
            and training.get("training_inputs", {}).get("manifest_sha256") == spec["manifest"]["sha256"],
            "Retention data is not bound by the supplied actual training manifest.")
    origins = training["training_inputs"]["origins"]
    require(set(spec.get("origin_receipts", {})) == set(origins), "Missing preserved retention origins.")
    for name,reference in spec["origin_receipts"].items():
        require(reference["sha256"] == origins[name]["receipt_sha256"], "Origin receipt pin mismatch.")
        inputs.reference(reference)
    path = str(PurePosixPath(spec["manifest"]["path"]).parent / "train.jsonl")
    raw = inputs.read(path, preparation["files"]["train.jsonl"], MAX_INPUT_BYTES)
    selected_families = spec.get("families")
    require(type(selected_families) is list and selected_families and all(type(x) is str for x in selected_families),
            "Retention families must be explicitly selected.")
    rows, exclusions = [],Counter()
    for line_number,line in enumerate(raw.splitlines(),1):
        row = decode(line)
        if row.get("family") not in selected_families:
            continue
        transition = row.get("transition", {})
        require(row.get("schema") == "peano-hydra-posttrain-example-v2"
                and row.get("split") == "train" and row.get("source_split") == "train"
                and row.get("kernel_checked") is True and transition.get("kernel_checked") is True
                and transition.get("split") == "train", "Retention row lacks original checked TRAIN provenance.")
        theorem, family = transition.get("theorem"),row["family"]
        require(hashlib.sha256(theorem.encode()).hexdigest() == row["theorem_statement_sha256"],
                "Retention theorem bytes/hash disagree.")
        require(transition.get("action") == row.get("action")
                and transition.get("completion") == row.get("completion")
                and transition.get("prompt") == row.get("prompt"), "Retention transition changed.")
        reason = reservation.reason(theorem, family, family, row["theorem_name"])
        reason = reason or reservation.goals_reason(transition["goals_before"]+transition["goals_after"])
        if reason:
            exclusions[reason] += 1
            continue
        rendered = primitive_prompt(transition["goals_before"], row["action"])
        require(all(row.get(key) == rendered[key] for key in ("prompt", "completion", "environment_sha256")),
                "Retention v4 prompt/authority bytes changed.")
        identity = reservation.identity(theorem)
        rows.append({"schema": SFT_SCHEMA, "id": digest([SFT_SCHEMA,identity,row["prompt"],row["completion"]]),
            "theorem": theorem,"theorem_identity": identity,"family": family,"template_family": family,
            "case_id": row["theorem_name"], **rendered,
            "source": {"path": path,"sha256": inputs.pins[path]["sha256"], "line": line_number,"owner":"project"},
            "goals_before": transition["goals_before"], "goals_after": transition["goals_after"],
            "focus": transition["focus"], "action": row["action"],"step":transition["step"],
            "remaining_steps": None,"kernel_checked":True,
            "verification_scope":"preserved_native_transition_and_actual_retention_training_origins",
            "winning_source": transition.get("source"),"partial_proof_cost":None,"final_proof_cost":None,
            "runtime_profile":"preserved_primitive_v4","censored":False,"benchmark_claim":False,
            "reserved_intermediate_check":"exact_closed_AST_plus_declared_template_exclusions"})
    return rows,dict(exclusions)


def deduplicate(rows):
    unique = {}
    for row in rows:
        if row["id"] not in unique:
            unique[row["id"]] = {**row, "sources": [row["source"]]}
        elif row["source"] not in unique[row["id"]]["sources"]:
            require(unique[row["id"]]["split_group"] == row["split_group"], "Duplicate crossed family split.")
            unique[row["id"]]["sources"].append(row["source"])
    return [unique[key] for key in sorted(unique)]


def export_dataset(input_spec, *, input_sha256, output, root=ROOT, identity=None, website_opt_in=False):
    inputs = Inputs(root)
    relative = Path(input_spec).absolute().relative_to(inputs.root).as_posix() if Path(input_spec).is_absolute() else str(input_spec)
    spec = inputs.json(relative,input_sha256)
    require(spec.get("schema") == INPUT_SCHEMA and spec.get("schema_mode") == "primitive_v4",
            "Primitive and structured planner datasets must use separate export contracts.")
    require(spec["holdout"]["sha256"] == HOLDOUT_SHA256, "Reservation differs from the reviewed frozen pin.")
    reservation = Reservation(inputs.reference(spec["holdout"]), identity or NativeIdentity())
    runs = spec.get("runs")
    require(type(runs) is list and 1 <= len(runs) <= MAX_RUNS, "Invalid bounded run list.")
    seed = spec.get("seed", 20260904)
    require(type(seed) is int and 0 <= seed < 2**32, "Invalid split seed.")
    maximum = spec.get("max_train_rows", MAX_ROWS)
    require(type(maximum) is int and 1 <= maximum <= MAX_ROWS, "Training subset exceeds4096 rows.")
    output = Path(output)
    require(not output.exists() and not output.is_symlink(), "Export needs a fresh output directory.")
    collections = {name: [] for name in ("sft", "distance", "attempts", "preferences", "outcomes")}
    count = 0
    for run in runs:
        for case,family,template,source in load_run(inputs,run,website_opt_in=website_opt_in):
            count += 1
            require(count <= MAX_CASES, "Export case ceiling exceeded.")
            extracted = extract_case(case,family=family,template_family=template,
                                     reservation=reservation,source=source)
            for name,values in zip(collections,extracted):
                collections[name].extend(values if type(values) is list else [values])
    retention_report = None
    if spec.get("retention") is not None:
        retained,excluded = retention_rows(inputs,spec["retention"],reservation)
        collections["sft"].extend(retained)
        retention_report = {"eligible_rows_before_dedupe":len(retained),"exclusions":excluded}
    all_rows = [row for rows in collections.values() for row in rows]
    groups = family_splits(all_rows,seed,spec.get("split_overrides"))
    counts_before = {name:len(rows) for name,rows in collections.items()}
    for name in ("sft","distance","attempts","preferences"):
        collections[name] = deduplicate(collections[name])
    files,coverage = {},{}
    output.mkdir(parents=True,exist_ok=False)
    def write(name,rows):
        raw = b"".join(canonical(row)+b"\n" for row in rows)
        require(len(raw) <= MAX_INPUT_BYTES, "Export output byte ceiling exceeded.")
        with (output/name).open("xb") as stream:
            stream.write(raw)
        files[name] = {"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"rows":len(rows)}
    for split in ("train","val","test"):
        candidates = [row for row in collections["sft"] if row["split"] == split]
        # Stable stratification makes rare observed tactic heads survive a small
        # cap without duplicating rows; this is data selection, not reweighting.
        by_action = defaultdict(list)
        for row in sorted(candidates,key=lambda r:digest([seed,r["id"]])):
            by_action[row["action"].split()[0]].append(row)
        selected = []
        while by_action and len(selected) < maximum:
            for action in sorted(tuple(by_action)):
                if len(selected) >= maximum:break
                selected.append(by_action[action].pop(0))
                if not by_action[action]:del by_action[action]
        write("primitive-"+split+".jsonl",sorted(selected,key=lambda row:row["id"]))
        coverage[split] = {"eligible_before_cap":len(candidates),"selected":len(selected),
            "omitted_by_cap":len(candidates)-len(selected),
            "actions":dict(sorted(Counter(row["action"].split()[0]for row in selected).items()))}
        distances = [row for row in collections["distance"] if row["split"] == split]
        write("ranker-"+split+".jsonl",distances[:MAX_ROWS])
    write("native-attempts.jsonl",collections["attempts"][:MAX_RANKING_ROWS])
    write("action-preferences.jsonl",collections["preferences"][:MAX_RANKING_ROWS])
    write("outcomes.jsonl",collections["outcomes"])
    # Rehash every input after export without reading or authenticating current
    # app sources: archived source pins describe the run version, not today's app.
    for name,pin in list(inputs.pins.items()):
        inputs.read(name,pin,MAX_INPUT_BYTES)
    for source_path in (APP/"export_decisions.py",APP/"branch_ranker.py",TRAINING/"BASELINE.json"):
        inputs.read(source_path.relative_to(inputs.root).as_posix(),maximum=2*1024*1024)
    manifest = {"schema":EXPORT_SCHEMA,"schema_mode":"primitive_v4","status":"complete",
        "ranking_feature_schema":FEATURE_SCHEMA,"ranking_numeric_encoding":NUMERIC_ENCODING,
        "cases":count,"seed":seed,"max_train_rows":maximum,"files":files,
        "inputs":sorted(inputs.pins.values(),key=lambda p:p["path"]),"source_pins_unchanged":True,
        "groups":groups,"group_split_unit":"whole_AST_theorem_and_declared_template_family_components",
        "counts_before_dedupe":counts_before,"counts_after_dedupe":{k:len(v)for k,v in collections.items()},
        "omitted_by_output_cap":{"attempts":max(0,len(collections["attempts"])-MAX_RANKING_ROWS),
                                 "preferences":max(0,len(collections["preferences"])-MAX_RANKING_ROWS)},
        "primitive_coverage":coverage,"retention":retention_report,
        "holdout_sha256":HOLDOUT_SHA256,"exclusion_scope":"native_closed_AST_identity_and_explicit_family_labels",
        "semantic_family_independence_certified":False,"pretraining_independence_known":False,
        "website_opt_in_enabled":website_opt_in,"structured_planner_rows":0,
        "native_proof_replays_performed_by_exporter":0,"model_calls":0,"training_performed":False,
        "positive_source_scope":"recorded_native_checked_continuations_only",
        "missing_partial_costs_imputed":False,"missing_states_fabricated":False,
        "resource_stops_are_censored":True,"benchmark_claim":False,
        "training_admission_required":"rehash_and_regenerate_from_pinned_sources_before_model_loading"}
    with (output/"manifest.json").open("xb") as stream:
        stream.write(canonical(manifest)+b"\n")
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs",required=True)
    parser.add_argument("--inputs-sha256",required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--website-opt-in",action="store_true")
    args = parser.parse_args(argv)
    result = export_dataset(args.inputs,input_sha256=args.inputs_sha256,
                            output=args.output,website_opt_in=args.website_opt_in)
    print(json.dumps({"status":result["status"],"cases":result["cases"],
                      "primitive_coverage":result["primitive_coverage"],"output":str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
