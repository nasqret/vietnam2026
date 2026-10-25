"""Owned native-only child for teacher prefix checks and bounded continuations.

No model, external solver, network, library import, or new inference rule is
available here. A successful result replays the entire original theorem from
an empty proof state and retains that independent trace.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from itertools import islice
import json
import os
from pathlib import Path
import resource
import signal
import stat
import sys
import time


SCHEMA = "hydra-teacher-native-request-v1"
KERNEL_SHA = "ad88855528244707b1fe7bd142d8fea60883a23b429840e07dd1875f3499c45d"
MAX_REQUEST_BYTES = 256 * 1024
MAX_RESULT_BYTES = 2 * 1024**2
MAX_DEPTH = 96
MAX_STATES = 64
MAX_EXPANSIONS = 32
MAX_FRONTIER = 16
MAX_TACTIC_ATTEMPTS = 384
MAX_MACRO = 8
MAX_DIAGNOSTICS = 64


class NativeDeadline(BaseException):
    pass


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def bootstrap(app):
    root = app.parent
    frozen = root / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
    sys.path[:0] = [str(app), str(app / "native-v7"), str(app / "training-v5"), str(frozen)]
    pins = {p.name: digest(p) for p in sorted((app / "native-v7/peano_lab/kernel").glob("*.py"))}
    require(sha256(canonical({"logic": "intuitionistic", "files": pins})).hexdigest() == KERNEL_SHA,
            "Teacher child kernel differs from the original unchanged checker.")


def execute(request, *, app, deadline, audit):
    from export_decisions import Inputs, Reservation, NativeIdentity, HOLDOUT_SHA256
    from hybrid_search import _closure_candidates, heuristic_candidates
    from peano_lab.batch import MODEL_V1_COMMANDS, run_proof
    from peano_lab.engine.state import apply_formula_subst, proof_metrics, proof_identity_metrics
    from peano_lab.engine.trace import render_goals
    from peano_lab.kernel.formulas import parse_formula_with_names, pretty_formula
    from peano_lab.ui.prove import SurfaceCapabilities, checked_surface_final
    from training.peano_policy.search import _AlphaStateIndex, _PrefixSnapshot, _new_owner, _replay, _canonical_goals

    require(request.get("schema") == SCHEMA and request.get("kind") in {"snapshot", "continuation"},
            "Unknown native teacher request.")
    state = request["state"]
    require(state.get("split") == "train" and state.get("reference_continuation_in_teacher_input") is False,
            "Native continuation needs an explicitly selected training state.")
    theorem = state["theorem"]
    target, names = parse_formula_with_names(theorem)
    require(not names and len(theorem.encode()) <= 16384, "Expected one bounded closed original theorem.")
    holdout = request["holdout"]
    require(holdout["sha256"] == HOLDOUT_SHA256, "Wrong held-out theorem reservation.")
    reservation = Reservation(Inputs(app.parent).reference(holdout), NativeIdentity())
    require(reservation.reason(theorem, state["family"], state["template_family"], state["case_id"]) is None,
            "Reserved theorem/template cannot enter a teacher child.")
    authority = SurfaceCapabilities(label="hydra-authority-no-imports-v1",
        allowed_commands=MODEL_V1_COMMANDS, allowed_theorems=frozenset())
    counts = {"prefix_tactic_attempts": 0, "teacher_tactic_attempts": 0,
        "heuristic_tactic_attempts": 0, "independent_replay_commands_requested": 0,
        "independent_replay_transitions_recorded": 0,
        "retained_states": 1, "native_transitions_accepted": 0,
        "native_expansions": 0, "teacher_steps_accepted": 0,
        "model_calls": 0, "solver_calls": 0}
    diagnostics = []
    audit.update(counts=counts, diagnostics=diagnostics, state_id=state["id"], prefix_checked=False)
    tick = 0

    def check():
        if time.monotonic() >= deadline:
            raise NativeDeadline("Native continuation wall limit.")

    def note(command, error, source):
        if len(diagnostics) < MAX_DIAGNOSTICS:
            diagnostics.append({"command": command, "source": source,
                                "error_type": type(error).__name__, "error": str(error)[:512]})

    def validate_goals(owner):
        goals = _canonical_goals(owner)
        require(len(goals) <= 16 and len(canonical(goals)) <= 16384,
                "Whole native goal tuple exceeds the bounded continuation state.")
        if goals:
            require(reservation.goals_reason(list(goals)) is None,
                    "Reserved or unparseable intermediate goals are forbidden.")
        return goals

    owner = _new_owner(target, names, theorem, classical=False, replay_id=0)
    root_goals = validate_goals(owner)
    prefix = _PrefixSnapshot.capture(owner, commands=(), goals=root_goals, capabilities=authority)

    def edge(parent, command, source):
        nonlocal tick
        check()
        require(type(command) is str and command == command.strip() and command.isprintable()
                and len(command.encode()) <= 4096 and ";" not in command
                and command.split()[0] in MODEL_V1_COMMANDS - {"use"},
                "Only one bounded ordinary no-import native command is allowed.")
        if len(parent.commands) >= MAX_DEPTH:
            return None, ValueError("Native script depth limit.")
        if source != "prefix" and counts["teacher_tactic_attempts"] + counts["heuristic_tactic_attempts"] >= MAX_TACTIC_ATTEMPTS:
            return None, ValueError("Native tactic attempt limit.")
        counts[source + "_tactic_attempts"] += 1
        tick += 1
        child, _, error = _replay(target, names, theorem, parent.commands + (command,),
            classical=False, capabilities=authority, replay_id=tick,
            prefix=parent, expected_goals=parent.goals)
        if error is not None:
            if isinstance(error, (MemoryError, TimeoutError)):
                raise error
            note(command, error, source)
            return None, error
        counts["native_transitions_accepted"] += 1
        goals = validate_goals(child)
        snapshot = _PrefixSnapshot.capture(child, commands=parent.commands + (command,),
                                          goals=goals, capabilities=authority)
        return snapshot, None

    recorded_commands = state["commands_before"]
    require(type(recorded_commands) is list and 2 <= len(recorded_commands) <= 24,
            "Selected prefix exceeds the fixed preparation bound.")
    for command in recorded_commands:
        candidate, error = edge(prefix, command, "prefix")
        require(candidate is not None, "Fresh selected-prefix replay failed: " + str(error))
        prefix = candidate
    require(prefix.goals == tuple(state["all_goals_before"]) and prefix.goals,
            "Fresh replay did not recover the exact selected complete open state.")
    audit["prefix_checked"] = True
    nodes, proof_depth = proof_metrics(prefix.state.partial)
    objects, _, _ = proof_identity_metrics(prefix.state.partial)
    base = {"schema": "hydra-teacher-native-result-v1", "state_id": state["id"],
        "original_theorem": theorem, "prefix_checked": True, "prefix_commands": recorded_commands,
        "all_goals_before": prefix.goals, "kernel_identity": KERNEL_SHA,
        "capabilities": {"label": authority.label, "allowed_commands": sorted(MODEL_V1_COMMANDS),
                         "allowed_theorems": []},
        "partial_proof_cost": {"structural_occurrences": nodes, "distinct_objects": objects,
                               "depth": proof_depth}, "counts": counts,
        "kernel_checked": False, "independent_replay_checked": False,
        "positive_distillation_eligible": False, "diagnostics": diagnostics}
    if request["kind"] == "snapshot":
        goal_records = []
        for goal in prefix.state.goals:
            variables = list(goal.variables)
            goal_records.append({"variables": variables,
                "context": [[name, pretty_formula(apply_formula_subst(formula, prefix.state.subst), variables)]
                            for name, formula in goal.context],
                "target": pretty_formula(apply_formula_subst(goal.target, prefix.state.subst), variables)})
        return {**base, "status": "snapshot", "goals": goal_records}

    plan = request["plan"]
    require(plan.get("source") in {"planner_model", "manual_fixture"},
            "The supplied plan needs an explicit model/fixture provenance.")
    supplied_source = "teacher_model" if plan["source"] == "planner_model" else "manual_fixture"
    commands = plan.get("commands")
    require(type(commands) is list and 1 <= len(commands) <= 32 and len(canonical(commands)) <= 16384
            and len(recorded_commands) + len(commands) <= MAX_DEPTH,
            "Teacher plan exceeds its fixed whole-plan bound.")
    provenance = list(state["prefix_provenance"])
    require(len(provenance) == len(recorded_commands), "Missing recorded prefix provenance.")
    teacher_used = 0
    for command in commands:
        if not prefix.goals:
            break
        child, error = edge(prefix, command, "teacher")
        if child is None:
            return {**base, "status": "rejected", "rejected_teacher_command": command,
                    "teacher_plan_sha256": plan["plan_sha256"], "error": str(error)[:512]}
        prefix = child
        teacher_used += 1
        counts["teacher_steps_accepted"] += 1
        provenance.append({"source": supplied_source, "command": command,
            "plan_sha256": plan["plan_sha256"], "reason": plan.get("reason", "")[:512]})
    require(teacher_used > 0, "No teacher tactic was executed.")
    base["teacher_plan_sha256"] = plan["plan_sha256"]
    base["teacher_plan_fully_executed"] = teacher_used == len(commands)
    base["unexecuted_plan_commands"] = commands[teacher_used:]

    def finish(winner, origins):
        check()
        certificate = checked_surface_final(winner.state, target)
        check()
        counts["independent_replay_commands_requested"] += len(winner.commands)

        def replay_progress(line):
            row = json.loads(line)
            if type(row) is dict and type(row.get("step")) is int:
                counts["independent_replay_transitions_recorded"] += 1

        replay = run_proof(theorem, winner.commands, capabilities=authority,
                           request_id="teacher-" + state["id"][:16], trace_sink=replay_progress)
        require(replay.status == "proved" and replay.kernel_checked and not replay.goals,
                "Independent original-theorem replay rejected the purported proof.")
        trace = [dict(row) for row in replay.trace]
        require(len(trace) == len(winner.commands) + 1 and len(origins) == len(winner.commands),
                "Independent replay did not retain every actual proof step.")
        for index, row in enumerate(trace[:-1]):
            require(row.get("status") == "ok" and row.get("tactic") == winner.commands[index]
                    and reservation.goals_reason(row["goals_before"] + row["goals_after"]) is None,
                    "Replay changed a proof step or crossed a reserved state.")
            row["origin"] = origins[index]
        occurrences, depth = proof_metrics(certificate)
        distinct, _, _ = proof_identity_metrics(certificate)
        result = {**base, "status": "proved", "commands": winner.commands,
            "continuation_commands": winner.commands[len(recorded_commands):],
            "provenance": origins, "trace": trace, "final_goals": [],
            "kernel_checked": True, "independent_replay_checked": True,
            "positive_distillation_eligible": supplied_source == "teacher_model",
            "positive_planner_target_eligible": supplied_source == "teacher_model" and base["teacher_plan_fully_executed"],
            "model_inference_evidence_required": "matching_parent_proposal_receipt_with_actual_decode",
            "proof_cost": {"structural_occurrences": occurrences, "distinct_objects": distinct, "depth": depth},
            "replay": replay.to_dict(include_trace=False)}
        require(len(canonical(result)) <= MAX_RESULT_BYTES, "Complete proof evidence exceeds its retention ceiling.")
        return result

    if not prefix.goals:
        return finish(prefix, provenance)
    alpha = _AlphaStateIndex()
    seen = set()
    key = alpha.key(prefix.state)
    alpha.remember(key, prefix.goals)
    seen.add(key)
    frontier = [(prefix, provenance)]
    while frontier and counts["retained_states"] < MAX_STATES and counts["native_expansions"] < MAX_EXPANSIONS:
        check()
        if counts["teacher_tactic_attempts"] + counts["heuristic_tactic_attempts"] >= MAX_TACTIC_ATTEMPTS:
            break
        counts["native_expansions"] += 1
        # Every fourth expansion serves the oldest retained branch.
        index = 0 if counts["native_expansions"] % 4 == 0 else min(range(len(frontier)),
            key=lambda i: (len(frontier[i][0].goals), len(canonical(frontier[i][0].goals)), len(frontier[i][0].commands)))
        parent, origins = frontier.pop(index)
        proposals = list(islice(_closure_candidates(parent.state, max_macro_steps=MAX_MACRO), 12))
        proposals += list(heuristic_candidates(parent.state, max_candidates=12, max_macro_steps=MAX_MACRO))
        unique = set()
        for proposal in proposals:
            check()
            macro = proposal.commands
            if macro in unique or not 1 <= len(macro) <= MAX_MACRO or len(parent.commands) + len(macro) > MAX_DEPTH:
                continue
            unique.add(macro)
            child, child_origins = parent, list(origins)
            for command in macro:
                new, error = edge(child, command, "heuristic")
                if new is None:
                    child = None
                    break
                child = new
                child_origins.append({"source": "heuristic", "command": command, "reason": proposal.reason[:512]})
                if not child.goals:
                    return finish(child, child_origins)
            if child is None:
                continue
            key = alpha.key(child.state)
            if key in seen:
                continue
            seen.add(key)
            alpha.remember(key, child.goals)
            counts["retained_states"] += 1
            frontier.append((child, child_origins))
            if len(frontier) > MAX_FRONTIER:
                del frontier[1]
            if counts["retained_states"] >= MAX_STATES:
                break
    return {**base, "status": "unknown", "remaining_frontier": len(frontier),
            "reason": "Finite native continuation exhausted or reached its search ceiling."}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-root", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--request-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    info = args.request.lstat()
    require(stat.S_ISREG(info.st_mode) and 0 < info.st_size <= MAX_REQUEST_BYTES,
            "Native child request must be a bounded regular file.")
    with args.request.open("rb") as stream:
        raw = stream.read(MAX_REQUEST_BYTES + 1)
    require(0 < len(raw) <= MAX_REQUEST_BYTES and len(raw) == info.st_size
            and sha256(raw).hexdigest() == args.request_sha256,
            "Native child request is missing, oversized or changed.")
    request = json.loads(raw)
    seconds = 15 if request.get("kind") == "snapshot" else 35
    cpu = 10 if request.get("kind") == "snapshot" else 25
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 2))
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024**2, 8 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

    def alarm(signum, frame):
        raise NativeDeadline("Owned native child wall/CPU guard.")

    signal.signal(signal.SIGALRM, alarm)
    signal.signal(signal.SIGXCPU, alarm)
    signal.alarm(seconds)
    started = time.monotonic()
    result, exit_code, audit = None, 0, {}
    try:
        app = args.app_root.resolve(strict=True)
        bootstrap(app)
        result = execute(request, app=app, deadline=started + seconds, audit=audit)
    except (NativeDeadline, MemoryError, TimeoutError) as error:
        result = {**audit, "status": "resource_limit", "error_type": type(error).__name__, "error": str(error)[:512],
                  "kernel_checked": False, "positive_distillation_eligible": False}
    except Exception as error:
        result = {**audit, "status": "error", "error_type": type(error).__name__, "error": str(error)[:512],
                  "kernel_checked": False, "positive_distillation_eligible": False}
        exit_code = 1
    finally:
        signal.alarm(0)
    result["elapsed_seconds"] = time.monotonic() - started
    result["child_intended_exit_code"] = exit_code
    result["actual_exit_observed_by"] = "owning_teacher_runner"
    result["resource_limits"] = {"cpu_seconds": cpu, "wall_seconds": seconds, "address_space_bytes": 2 * 1024**3}
    encoded = canonical(result) + b"\n"
    require(len(encoded) <= MAX_RESULT_BYTES, "Native result exceeds its bounded retention capacity.")
    with args.output.open("xb") as stream:
        stream.write(encoded)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
