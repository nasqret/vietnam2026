"""Select exactly 32 training frontier states from admitted project evidence.

Preparation parses reservations but never runs a tactic or calls a model.
Archived future proof steps are used only to authenticate the source run; they
are not included in any selected state's teacher input or continuation budget.
The runner must freshly replay the exact recorded prefix before decoding.
"""
from __future__ import annotations

from collections import defaultdict, deque
from hashlib import sha256
import json
from pathlib import Path


SCHEMA = "hydra-teacher-training-frontier-selection-v1"
STRATEGY = "family_round_robin_exact_state_shortest_recorded_prefix_v1"
STATE_COUNT = 32
MAX_PREFIX = 24
MAX_STATE_BYTES = 16384
MAX_SELECTION_BYTES = 2 * 1024**2
MAX_INPUT_ROWS = 16384


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def identity(value):
    return sha256(canonical(value)).hexdigest()


def _goals(value):
    require(type(value) in (list, tuple) and 0 < len(value) <= 16
            and all(type(x) is str and x.count("⊢") == 1 and "?" not in x for x in value)
            and len(canonical(value)) <= MAX_STATE_BYTES,
            "A selected frontier needs all bounded, parseable open goals.")
    return tuple(value)


def _command(value):
    require(type(value) is str and value and value == value.strip() and value.isprintable()
            and len(value.encode()) <= 4096 and value.split()[0] not in {"qed", "use"},
            "Recorded prefix must be finite no-import native commands.")
    return value


def recorded_prefix(case, parent_id, *, verified_trace, graph_cache=None):
    """Reconstruct only actual accepted edges; missing links are never inferred."""
    theorem = case["canonical_theorem"]
    root_goals = ("⊢ " + theorem,)
    nodes = {0: {"parent_id": None, "command": None, "depth": 0,
                 "goals_after": root_goals, "source": "original_theorem"}}
    entry = None if graph_cache is None else graph_cache.get(id(case))
    require(entry is None or entry[0] is case, "Cached source graph identity changed.")
    cached = None if entry is None else entry[1]
    trace = [] if cached is not None else verified_trace(case)[0]

    def put(key, parent, command, depth, goals, source):
        require(type(key) is int and key > 0 and type(parent) is int and 0 <= parent < key
                and type(depth) is int and 1 <= depth <= 160, "Malformed recorded branch identity.")
        value = {"parent_id": parent, "command": _command(command), "depth": depth,
                 "goals_after": tuple(goals), "source": source}
        previous = nodes.get(key)
        require(previous is None or previous == value, "Recorded branch and replay prefix disagree.")
        nodes[key] = value

    for row in trace:
        origin = row["origin"]
        put(origin["branch_id"], origin["parent_id"], row["tactic"], row["step"],
            row["goals_after"], origin["source"])
    branches = [] if cached is not None else (case["last_job"]["result"].get("search") or {}).get("branches", [])
    require(type(branches) is list and len(branches) <= 20000, "Oversized source branch log.")
    for row in branches:
        if (row.get("status") in {"open", "proof"} and type(row.get("id")) is int
                and type(row.get("goals_after")) is list):
            put(row["id"], row["parent_id"], row["command"], row["depth"],
                row["goals_after"], row["source"])
    if cached is not None:
        nodes = cached
    elif graph_cache is not None:
        require(len(graph_cache) < 128, "Too many retained source branch graphs.")
        # Retain the source object as well as its graph: object IDs must not be
        # reused for a different source when callers supply short-lived dicts.
        graph_cache[id(case)] = (case, nodes)
    require(type(parent_id) is int and parent_id in nodes, "Frontier parent snapshot is missing.")
    chain, cursor = [], parent_id
    while cursor:
        require(len(chain) < MAX_PREFIX and cursor in nodes, "Prefix is missing or exceeds its depth bound.")
        node = nodes[cursor]
        chain.append((cursor, node))
        cursor = node["parent_id"]
    chain.reverse()
    require(2 <= len(chain) <= MAX_PREFIX, "Select introduced frontier states, not root examples.")
    goals_history = [root_goals]
    commands, provenance = [], []
    for index, (key, node) in enumerate(chain, 1):
        require(node["depth"] == index, "Recorded prefix depth is inconsistent.")
        commands.append(node["command"])
        provenance.append({"source": "recorded_prefix", "original_source": node["source"],
            "branch_id": key, "parent_id": node["parent_id"], "command": node["command"]})
        goals_history.append(_goals(node["goals_after"]))
    require(len(canonical(commands)) <= 32768, "Recorded prefix exceeds its byte ceiling.")
    return tuple(commands), tuple(provenance), tuple(goals_history)


def select_records(attempts, *, load_case, verified_trace, reservation, should_stop=None):
    """Pure finite selection with explicit evidence/reservation adapters."""
    require(type(attempts) is list and len(attempts) <= MAX_INPUT_ROWS, "Too many source frontier records.")
    candidates, skipped, graph_cache = {}, defaultdict(int), {}
    grouped_failures = defaultdict(list)
    for row in attempts:
        if should_stop is not None and should_stop():
            raise RuntimeError("Teacher frontier preparation cancelled.")
        if row.get("split") == "train" and row.get("native_rejected") is True and not row.get("censored"):
            key = (row.get("theorem_identity"), tuple(row.get("all_goals_before") or ()))
            error = row.get("error")
            if type(error) is str and len(grouped_failures[key]) < 4:
                grouped_failures[key].append((str(row.get("action", ""))[:128] + ": " + error)[:512])
    for row in attempts:
        if should_stop is not None and should_stop():
            raise RuntimeError("Teacher frontier preparation cancelled.")
        if (row.get("schema") != "hydra-native-action-attempt-v1" or row.get("split") != "train"
                or (row.get("source") or {}).get("owner") != "project"):
            skipped["not_project_training_frontier"] += 1
            continue
        # A changed source pin is fatal, not an excuse to silently select a
        # different set of training examples from the remaining files.
        case = load_case(row["source"])
        try:
            goals = _goals(row["all_goals_before"])
            require(case.get("outcome") == "proved" and case.get("expected") not in {"not_provable", "refutable"}
                    and case.get("case_id") == row["case_id"]
                    and case.get("canonical_theorem") == row["theorem"],
                    "Select only recorded completed positive project sources.")
            require(reservation.reason(row["theorem"], row["family"], row["template_family"], row["case_id"]) is None,
                    "Reserved theorem or template is forbidden.")
            commands, provenance, history = recorded_prefix(case, row["parent_id"],
                verified_trace=verified_trace, graph_cache=graph_cache)
            require(history[-1] == goals, "Recorded original prefix does not end at the selected exact state.")
            require(all(reservation.goals_reason(list(old)) is None for old in history),
                    "A reserved or unavailable intermediate state is forbidden.")
            key = (row["theorem_identity"], goals)
            record = {"id": identity([SCHEMA, row["theorem_identity"], goals]),
                "theorem": row["theorem"], "theorem_identity": row["theorem_identity"],
                "case_id": row["case_id"], "family": row["family"],
                "template_family": row["template_family"], "split": "train",
                "split_group": row["split_group"], "source": row["source"],
                "source_attempt_id": row["id"], "parent_id": row["parent_id"],
                "commands_before": commands, "prefix_provenance": provenance,
                "all_goals_before": goals, "recorded_failures": tuple(grouped_failures[key]),
                "recorded_prefix_goals_sha256": identity(history),
                "prefix_verification_required": "fresh_native_replay_before_teacher_decode",
                "reference_continuation_in_teacher_input": False,
                "kernel_checked_by_selection": False}
            previous = candidates.get(key)
            score = (len(commands), identity([record["source"], commands]))
            if previous is None or score < previous[0]:
                candidates[key] = (score, record)
        except (KeyError, TypeError, ValueError) as error:
            # These are source/fragment declines, not model or proof failures.
            skipped[type(error).__name__ + ": " + str(error)[:160]] += 1
    groups = defaultdict(list)
    for _, record in candidates.values():
        groups[record["template_family"]].append(record)
    for family in groups:
        groups[family].sort(key=lambda r: identity([STRATEGY, r["id"]]))
        groups[family] = deque(groups[family])
    selected = []
    while groups and len(selected) < STATE_COUNT:
        for family in sorted(tuple(groups)):
            if len(selected) == STATE_COUNT:
                break
            selected.append(groups[family].popleft())
            if not groups[family]:
                del groups[family]
    require(len(selected) == STATE_COUNT, "Fewer than 32 admissible distinct recoverable training frontiers.")
    return selected, {"candidate_states": len(candidates), "selected_states": len(selected),
        "skipped": dict(sorted(skipped.items())), "strategy": STRATEGY,
        "semantic_family_independence_certified": False}


def prepare_selection(dataset_manifest, *, dataset_sha256, app_root, output, should_stop=None):
    """Explicit metadata/parser admission. No model or native proof execution."""
    app = Path(app_root).resolve(strict=True)
    root = app.parent
    from hydra_training_v5.decision_data import attest_decision_dataset
    import export_decisions as exporter
    require(Path(exporter.__file__).resolve() == app / "export_decisions.py", "Wrong decision exporter path.")
    admitted = attest_decision_dataset(dataset_manifest, expected_sha256=dataset_sha256, workspace=root)
    inputs = exporter.Inputs(root)
    manifest = inputs.json(admitted.manifest_path, dataset_sha256)
    pins = {p["path"]: p for p in manifest["inputs"]}
    specs = []
    for pin in manifest["inputs"]:
        if pin["path"].endswith(".json") and pin["bytes"] <= 512 * 1024:
            record = exporter.decode(inputs.read(pin["path"], pin, exporter.MAX_INPUT_BYTES))
            if type(record) is dict and record.get("schema") == exporter.INPUT_SCHEMA:
                specs.append(record)
    require(len(specs) == 1, "Expected one admitted export specification.")
    holdout = specs[0]["holdout"]
    reservation = exporter.Reservation(inputs.reference(holdout), exporter.NativeIdentity())
    filename = str(Path(admitted.manifest_path).parent / "native-attempts.jsonl")
    attempts = [exporter.decode(line) for line in inputs.read(filename,
        manifest["files"]["native-attempts.jsonl"], exporter.MAX_INPUT_BYTES).splitlines()]
    cases = {}

    def load_case(source):
        require(type(source) is dict and source.get("path") in pins
                and source.get("sha256") == pins[source["path"]]["sha256"],
                "Frontier source is not an exact admitted dataset input.")
        key = source["path"]
        if key not in cases:
            require(len(cases) < 128, "Too many source cases.")
            cases[key] = inputs.json(key, pins[key], exporter.MAX_INPUT_BYTES)
        return cases[key]

    selected, selection_report = select_records(attempts, load_case=load_case,
        verified_trace=exporter.verified_trace, reservation=reservation, should_stop=should_stop)
    value = {"schema": SCHEMA, "strategy": STRATEGY,
        "dataset_manifest": admitted.manifest_path, "dataset_sha256": dataset_sha256,
        "dataset_attestation": admitted.attestation, "holdout": holdout,
        "states": selected, "selection": selection_report,
        "input_pins": sorted(inputs.pins.values(), key=lambda p: p["path"]),
        "model_calls": 0, "native_proof_runs": 0, "training_only": True,
        "teacher_reference_continuations": False, "positive_distillation_requires_fresh_full_replay": True,
        "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest()}
    raw = canonical(value) + b"\n"
    require(len(raw) <= MAX_SELECTION_BYTES, "Selection record exceeds its byte ceiling.")
    with Path(output).open("xb") as stream:
        stream.write(raw)
    return {"path": str(output), "bytes": len(raw), "sha256": sha256(raw).hexdigest(),
            "states": len(selected), "native_proof_runs": 0, "model_calls": 0}
