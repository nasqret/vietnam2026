"""Bounded, model-free engineering fixtures for opt-in search-state deduplication.

The parent hashes source and supervises fresh children using only stdlib code.
Native parsing/search/replay imports occur inside guarded workers. These are
authored policy fixtures, never replayed model proposals or a recovered model
benchmark. Generic search ``model_calls`` count authored proposal invocations.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import stat
import sys
from typing import Callable
import uuid

from training.peano_hydra.review_runtime import ProcessLimits, run_bounded, validate_process_record


ROOT = Path(__file__).absolute().parents[2]
SCRIPT = "scripts/check_peano_hydra_search_dedup.py"
PLAN_SCHEMA = "peano-hydra-search-dedup-fixtures-plan-v1"
REPORT_SCHEMA = "peano-hydra-search-dedup-fixtures-results-v1"
REQUEST_SCHEMA = "peano-hydra-search-dedup-worker-request-v1"
RESPONSE_SCHEMA = "peano-hydra-search-dedup-worker-result-v1"
POLICY_SCHEMA = "peano-hydra-authored-name-branching-policy-v1"
CONTEXT_ALPHA_PROFILE = "context-alpha-v1"
LANES = (("legacy", None), ("context-alpha", CONTEXT_ALPHA_PROFILE))
CASES = (
    ("nested_reflexivity", "forall n m. n = n"),
    ("implication_identity", "forall n m. n = m -> n = m"),
    ("disjunction_injection", "forall n. n = 0 -> (n = 0 \\/ n = 1)"),
    ("conjunction_duplication", "forall n m. n = m -> (n = m /\\ n = m)"),
)
LIMIT_ITEMS = (("max_depth", 16), ("beam_width", 4), ("candidates_per_state", 4),
               ("max_model_calls", 8), ("max_states", 64))
COMMANDS = ("assumption", "intro", "left", "refl", "split")
VARIABLE_NAMES = ("n", "a", "x", "z", "m", "b", "y", "w", "p", "c", "u", "v")
HYPOTHESIS_NAMES = ("h", "ha", "hx", "hz", "hm", "hb", "hy", "hw", "hp", "hc", "hu", "hv")
WORKER_LIMITS = ProcessLimits(wall_seconds=15, cpu_seconds=10, rss_bytes=512 * 1024**2,
                              output_bytes=512 * 1024)
MAX_REQUEST_BYTES = 256 * 1024
MAX_REPORT_BYTES = 24 * 1024**2
MAX_SOURCE_FILE_BYTES = 2 * 1024**2
MAX_SOURCE_TOTAL_BYTES = 16 * 1024**2
MAX_SOURCE_FILES = 128
SOURCE_FILES = (
    "training/peano_hydra/search_dedup.py", SCRIPT,
    "training/peano_hydra/__init__.py", "training/peano_hydra/policy.py", "training/peano_hydra/runner.py",
    "training/peano_hydra/review_runtime.py", "scripts/hydra_bounded_exec.py",
    "training/peano_policy/__init__.py", "training/peano_policy/prompt.py",
    "training/peano_policy/search.py", "training/peano_policy/state_identity.py",
    "peano-lab/py/peano_lab/__init__.py", "peano-lab/py/peano_lab/batch.py",
    "peano-lab/py/peano_lab/ui/__init__.py", "peano-lab/py/peano_lab/ui/prove.py",
    "peano-lab/py/peano_lab/ui/panels.py", "peano-lab/py/peano_lab/library/theorems.py",
)
SOURCE_DIRECTORIES = ("peano-lab/py/peano_lab/kernel", "peano-lab/py/peano_lab/engine")
CLAIM = ("Authored deterministic CPU engineering fixtures, not model inference, saved model-proposal replay, "
         "recovered PRIMARY32 results, unseen generalization or independent theorem discovery. "
         "Equivalent proof obligations do not imply identical outputs from a name-sensitive policy.")


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def decode(raw: bytes, maximum: int = MAX_REQUEST_BYTES) -> dict:
    require(type(raw) is bytes and 0 < len(raw) <= maximum, "JSON exceeds its byte bound")
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON field")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("invalid nonfinite JSON number: " + value)
    def integer(value):
        require(len(value) <= 32, "oversized JSON integer")
        return int(value)
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid, parse_int=integer)
    require(type(value) is dict, "JSON must be one object")
    canonical(value)
    return value


def _no_models() -> None:
    require(not any(name.split(".", 1)[0] in {"torch", "transformers", "peft", "tokenizers"}
                    for name in sys.modules), "fixture process must not import model frameworks or tokenizers")


def _directory(path: Path) -> int:
    path = path.absolute()
    require(".." not in path.parts and 1 < len(path.parts) <= 64 and len(str(path).encode()) <= 4096,
            "unsafe directory path")
    access = getattr(os, "O_PATH", os.O_RDONLY) if sys.platform == "linux" else os.O_RDONLY
    fd = os.open(path.anchor, access | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for index, part in enumerate(path.parts[1:], 1):
            flags = os.O_RDONLY if index == len(path.parts) - 1 else access
            child = os.open(part, flags | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        result, fd = fd, -1
        return result
    finally:
        if fd >= 0:
            os.close(fd)


def _read(path: Path, maximum: int) -> bytes:
    parent = _directory(path.parent)
    fd = -1
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= maximum,
                "unsafe or oversized input file")
        parts, size = [], 0
        while size <= maximum:
            part = os.read(fd, min(65536, maximum + 1 - size))
            if not part:
                break
            parts.append(part)
            size += len(part)
        after, named = os.fstat(fd), os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        require(size == before.st_size and size <= maximum and all(
            getattr(before, key) == getattr(after, key) == getattr(named, key)
            for key in ("st_dev", "st_ino", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns")),
            "input changed during bounded reading")
        return b"".join(parts)
    finally:
        if fd >= 0:
            os.close(fd)
        os.close(parent)


def _source_names(root: Path) -> tuple[str, ...]:
    names, pending, directories = set(SOURCE_FILES), list(SOURCE_DIRECTORIES), 0
    while pending:
        name = pending.pop()
        directories += 1
        require(directories <= 32, "source directory inventory exceeds its bound")
        fd = _directory(root / name)
        try:
            with os.scandir(fd) as entries:
                for index, entry in enumerate(entries):
                    require(index < 256, "source directory exceeds its entry bound")
                    if entry.name == "__pycache__":
                        continue
                    require(not entry.is_symlink(), "source tree contains a symlink")
                    child = name + "/" + entry.name
                    if entry.is_dir(follow_symlinks=False):
                        require(len(child.split("/")) <= 12, "source nesting exceeds its bound")
                        pending.append(child)
                        require(len(pending) + directories <= 32, "source directory queue exceeds its bound")
                    elif entry.name.endswith(".py"):
                        require(entry.is_file(follow_symlinks=False), "source is not regular")
                        names.add(child)
                        require(len(names) <= MAX_SOURCE_FILES, "source file inventory exceeds its bound")
        finally:
            os.close(fd)
    return tuple(sorted(names))


def source_inventory(root: Path = ROOT) -> dict:
    names = _source_names(root)
    result, total = {}, 0
    for name in names:
        raw = _read(root / name, MAX_SOURCE_FILE_BYTES)
        total += len(raw)
        require(total <= MAX_SOURCE_TOTAL_BYTES, "source bytes exceed their aggregate bound")
        result[name] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    require(names == _source_names(root), "source inventory changed during hashing")
    return result


def _policy_record() -> dict:
    return {"schema": POLICY_SCHEMA, "state_input": "first ordered rendered goal and its context",
            "intro_variable_names": list(VARIABLE_NAMES), "intro_hypothesis_names": list(HYPOTHESIS_NAMES),
            "non_intro_candidates": {"and": ["split"], "or": ["left"], "other": ["assumption", "refl"]},
            "maximum_candidates": 4, "target_specific_scripts": False,
            "saved_model_proposals": False, "real_model_generate_calls": 0, "external_solver_calls": 0}


def build_demo_plan(root: Path = ROOT) -> dict:
    """Hash a fixed fixture plan, without importing native or model modules."""
    _no_models()
    sources = source_inventory(root)
    record = {"schema": PLAN_SCHEMA, "cases": [{"id": name, "source": source} for name, source in CASES],
              "lanes": [{"name": name, "search_profile": profile} for name, profile in LANES],
              "limits": dict(LIMIT_ITEMS), "classical": False,
              "capabilities": {"label": "hydra-name-branch-fixtures-v1", "allowed_commands": list(COMMANDS),
                               "allowed_theorems": []}, "policy": _policy_record(),
              "source_files": sources, "source_files_sha256": digest(sources),
              "source_coverage": "Listed fixture/search/runner/supervisor sources and bounded native kernel/engine Python inventory; not whole-repository attestation.",
              "profile_contract_authority": {"module": "training/peano_policy/state_identity.py",
                  "function": "search_profile_contract", "sha256": sources["training/peano_policy/state_identity.py"]["sha256"]},
              "worker_limits": WORKER_LIMITS.to_dict(), "maximum_search_workers": 8, "maximum_replay_workers": 8,
              "native_goal_validation_performed": False, "real_model_generate_calls": 0,
              "research_claim_eligible": False, "claim_boundary": CLAIM}
    return {**record, "plan_sha256": digest(record)}


def validate_demo_plan(plan: dict, root: Path = ROOT) -> None:
    require(type(plan) is dict and len(canonical(plan)) <= MAX_REQUEST_BYTES
            and canonical(plan) == canonical(build_demo_plan(root)), "fixture plan, source or fixed authority changed")


@dataclass(frozen=True, slots=True)
class AuthoredNamePolicy:
    """One bounded shape-aware policy, identical for every case and search lane."""
    _environment_json: str
    source_sha256: str

    @property
    def policy_environment(self) -> dict:
        return json.loads(self._environment_json)

    @property
    def evaluation_identity(self) -> dict:
        return {"name": "authored-name-branching-fixture-v1", "kind": POLICY_SCHEMA,
                "policy": _policy_record(), "source_sha256": self.source_sha256,
                "environment": self.policy_environment, "research_claim_eligible": False}

    def propose(self, goals_before: tuple[str, ...], *, max_candidates: int) -> tuple[str, ...]:
        require(type(goals_before) is tuple and 1 <= len(goals_before) <= 64
                and all(type(goal) is str for goal in goals_before)
                and sum(len(goal.encode()) for goal in goals_before) <= 16384,
                "fixture observation exceeds its bound")
        require(type(max_candidates) is int and 1 <= max_candidates <= 4, "fixture candidate quota changed")
        from peano_lab.kernel.formulas import And, Forall, Imp, Or, parse_formula_with_names

        context, separator, body = goals_before[0].partition("⊢")
        require(bool(separator) and "⊢" not in body, "fixture requires one rendered sequent")
        formula, _ = parse_formula_with_names(body.strip())
        if isinstance(formula, (Forall, Imp)):
            used = set(re.findall(r"\b([A-Za-z][A-Za-z0-9_]*)\s*:", context))
            pool = VARIABLE_NAMES if isinstance(formula, Forall) else HYPOTHESIS_NAMES
            names = tuple(name for name in pool if name not in used)[:max_candidates]
            require(len(names) == max_candidates, "bounded fixture name pool was exhausted")
            return tuple("intro " + name for name in names)
        if isinstance(formula, And):
            return ("split",)
        if isinstance(formula, Or):
            return ("left",)
        return ("assumption", "refl")[:max_candidates]


def _worker_guard() -> None:
    _no_models()
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.pycache_prefix == "/dev/null",
            "native fixture workers require isolated uncached Python")
    soft, hard = resource.getrlimit(resource.RLIMIT_CPU)
    require(soft == WORKER_LIMITS.cpu_seconds and hard == soft + 1,
            "native fixture worker requires its inherited bounded CPU reservation")


def _request(plan: dict, case_id: str, lane: str, *, replay: dict | None = None) -> dict:
    record = {"schema": REQUEST_SCHEMA, "mode": "search" if replay is None else "replay",
              "plan": plan, "case_id": case_id, "lane": lane}
    if replay is not None:
        record["replay"] = replay
    return record


def worker(request: dict) -> dict:
    """Execute only fixed native fixtures, never arbitrary caller-selected goals."""
    _worker_guard()  # Must precede every native import, even for malformed requests.
    require(type(request) is dict, "worker request must be one object")
    mode = request.get("mode")
    expected = {"schema", "mode", "plan", "case_id", "lane"} | ({"replay"} if mode == "replay" else set())
    require(set(request) == expected and request["schema"] == REQUEST_SCHEMA and mode in {"search", "replay"},
            "worker request schema changed")
    plan = request["plan"]
    validate_demo_plan(plan)
    cases, profiles = dict(CASES), dict(LANES)
    require(request["case_id"] in cases and request["lane"] in profiles, "worker selected a foreign case/profile")
    source, profile = cases[request["case_id"]], profiles[request["lane"]]
    from peano_lab.ui.prove import SurfaceCapabilities
    from training.peano_policy.state_identity import CONTEXT_ALPHA_V1, search_profile_contract

    require(CONTEXT_ALPHA_V1 == CONTEXT_ALPHA_PROFILE, "native search profile name changed")
    contract = search_profile_contract(profile)
    capabilities = SurfaceCapabilities(label=plan["capabilities"]["label"], allowed_commands=frozenset(COMMANDS),
                                       allowed_theorems=frozenset())
    if mode == "search":
        from training.peano_hydra.policy import HydraCandidatePolicy, PolicyHead
        from training.peano_hydra.runner import policy_environment, run_hydra
        from training.peano_policy.search import SearchLimits

        child = AuthoredNamePolicy(canonical(policy_environment(capabilities)).decode(),
                                   plan["source_files"]["training/peano_hydra/search_dedup.py"]["sha256"])
        policy = HydraCandidatePolicy((PolicyHead("authored", "symbolic", 4, child),),
                                      name="hydra-name-branching-fixture-v1")
        result = run_hydra(source, policy, capabilities=capabilities, limits=SearchLimits(**dict(LIMIT_ITEMS)),
                           label="search-dedup-" + request["case_id"] + "-" + request["lane"], search_profile=profile)
        require(result.search.search_profile == profile, "search did not execute the requested profile")
        payload = result.to_dict(include_trace=True)
    else:
        from peano_lab.batch import run_proof

        replay = request["replay"]
        require(type(replay) is dict and set(replay) == {"commands", "id", "session"}
                and type(replay["commands"]) is list and 1 <= len(replay["commands"]) <= 16
                and all(type(command) is str and 0 < len(command.encode()) <= 4096 for command in replay["commands"])
                and all(type(replay[key]) is str and 0 < len(replay[key]) <= 256 for key in ("id", "session")),
                "fresh replay input exceeds the fixed proof boundary")
        result = run_proof(source, tuple(replay["commands"]), request_id=replay["id"], session_id=replay["session"],
                           classical=False, on_error="stop", capabilities=capabilities)
        payload = result.to_dict(include_trace=True)
        require(result.kernel_checked is True and result.status == "proved", "fresh original-goal replay failed")
    validate_demo_plan(plan)
    _no_models()
    response = {"schema": RESPONSE_SCHEMA, "mode": mode, "plan_sha256": plan["plan_sha256"],
                "source_files_sha256": plan["source_files_sha256"], "case_id": request["case_id"], "lane": request["lane"],
                "search_profile": profile, "profile_contract": contract, "result": payload,
                "real_model_generate_calls": 0, "external_solver_calls": 0}
    require(len(canonical(response)) < WORKER_LIMITS.output_bytes - 1024, "worker evidence exceeds output reservation")
    return {**response, "response_sha256": digest(response)}


def _invoke(request: dict, root: Path) -> tuple[dict | None, dict]:
    validate_demo_plan(request["plan"], root)
    command = (sys.executable, "-I", "-B", "-X", "pycache_prefix=/dev/null", str(root / SCRIPT), "--worker")
    payload = canonical(request)
    require(len(payload) <= MAX_REQUEST_BYTES, "worker request exceeds byte bound")
    process = run_bounded(command, cwd=root, limits=WORKER_LIMITS, input_bytes=payload)
    validate_process_record(process, command=command, limits=WORKER_LIMITS, input_bytes=payload)
    if process["reason"] != "exited" or process["returncode"] != 0:
        return None, process
    validate_process_record(process, command=command, limits=WORKER_LIMITS, input_bytes=payload, success_codes=(0,))
    response = decode(process["stdout"].encode(), WORKER_LIMITS.output_bytes)
    require(set(response) == {"schema", "mode", "plan_sha256", "source_files_sha256", "case_id", "lane",
                             "search_profile", "profile_contract", "result", "real_model_generate_calls",
                             "external_solver_calls", "response_sha256"}
            and response["response_sha256"] == digest({k: v for k, v in response.items() if k != "response_sha256"})
            and response["schema"] == RESPONSE_SCHEMA and response["mode"] == request["mode"]
            and response["plan_sha256"] == request["plan"]["plan_sha256"]
            and response["source_files_sha256"] == request["plan"]["source_files_sha256"]
            and response["case_id"] == request["case_id"] and response["lane"] == request["lane"]
            and response["search_profile"] == dict(LANES)[request["lane"]]
            and type(response["real_model_generate_calls"]) is int and response["real_model_generate_calls"] == 0
            and type(response["external_solver_calls"]) is int and response["external_solver_calls"] == 0,
            "worker response does not bind the exact request")
    require((response["profile_contract"] is None) if response["search_profile"] is None
            else type(response["profile_contract"]) is dict, "worker profile contract is missing")
    validate_demo_plan(request["plan"], root)
    return response, process


def _validate_search(response: dict, plan: dict) -> None:
    result = response["result"]
    profile = response["search_profile"]
    require(type(result) is dict and type(result.get("v")) is int and result["v"] == (1 if profile is None else 2)
            and result.get("status") in {"proof", "limit", "exhausted"}
            and result.get("degraded") is False and result.get("eligible_for_comparison") is False,
            "fixture run lost its exact profile/version or untrusted-policy boundary")
    require(result["limits"] == plan["limits"] and result["environment"]["classical"] is False
            and canonical(result["environment"]["capabilities"]) == canonical(plan["capabilities"]),
            "fixture authority or resource limits changed")
    search = result["search"]
    require(("state_identity" in search) is (profile is not None), "search profile evidence is missing or silently widened")
    for name, ceiling in (("model_calls", 8), ("states_expanded", 8), ("states_discovered", 64),
                          ("candidates_executed", 32), ("frontier_peak", 4), ("depth_reached", 16)):
        require(type(search[name]) is int and 0 <= search[name] <= ceiling, "fixture search exceeded " + name)
    require(search["status"] == result["status"] and search["model_calls"] == search["states_expanded"]
            == len(result["proposal_records"]), "authored proposal-call accounting differs")
    if profile is None:
        require("search_profile" not in result and response["profile_contract"] is None,
                "legacy fixture silently acquired profile evidence")
    else:
        identity = search["state_identity"]
        contract = result.get("search_profile")
        require(profile == CONTEXT_ALPHA_PROFILE and type(identity) is dict and set(identity) == {"contract", "counters"}
                and type(contract) is dict and canonical(contract) == canonical(identity["contract"])
                == canonical(response["profile_contract"]), "top-level, nested or worker search-profile contract differs")
        require(contract.get("schema") == "peano-search-state-identity-v1" and contract.get("name") == profile,
                "fixture search-profile contract name/schema changed")
        encoded_contract = json.dumps({k: v for k, v in contract.items() if k != "contract_sha256"},
                                      sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
        require(contract.get("contract_sha256") == hashlib.sha256(encoded_contract).hexdigest(),
                "fixture search-profile contract digest changed")
        for name, ceiling in (("max_key_nodes", 8192), ("max_key_bytes", 65536),
                              ("max_retained_key_bytes", 8 * 1024**2), ("max_name_bytes", 256)):
            require(type(contract.get(name)) is int and 1 <= contract[name] <= ceiling,
                    "fixture structural-key resource bound changed")
        counters = identity["counters"]
        require(type(counters) is dict and set(counters) == {"key_attempts", "keys_built", "keys_declined",
                "duplicate_states", "renamed_states", "retained_key_bytes", "key_budget_declines"}
                and all(type(value) is int and value >= 0 for value in counters.values()),
                "fixture state-identity counters are malformed")
        require(1 <= counters["key_attempts"] <= search["candidates_executed"] + 1
                and counters["keys_built"] + counters["keys_declined"] == counters["key_attempts"]
                and counters["renamed_states"] <= counters["duplicate_states"] <= counters["keys_built"]
                and counters["key_budget_declines"] <= counters["keys_declined"]
                and search["states_discovered"] <= counters["key_attempts"] - counters["duplicate_states"]
                and counters["retained_key_bytes"] <= min(contract["max_retained_key_bytes"],
                    search["states_discovered"] * contract["max_key_bytes"]),
                "fixture state-identity counters violate their actual-work bounds")
    require(type(search["commands"]) is list and len(search["commands"]) <= 16, "fixture proof exceeds depth bound")
    if result["status"] == "proof":
        require(result["proved"] is True and result["replay"]["kernel_checked"] is True
                and result["replay"]["status"] == "proved" and result["replay"]["theorem"] == result["theorem"]
                and result["replay"]["proof_nodes"] == search["certificate_nodes"]
                and result["commands_sha256"] == digest(search["commands"])
                and 1 <= len(search["commands"]) <= search["depth_reached"], "fixture proof lost its checked command binding")
    else:
        require(result["proved"] is False and result["replay"] is None and not search["commands"]
                and search["certificate_nodes"] is None and result["commands_sha256"] is None,
                "unsuccessful fixture invented proof data")


def _summary(rows: list[dict]) -> dict:
    result = {}
    for lane, _ in LANES:
        completed = [row for row in rows if row["lane"] == lane and row["status"] == "completed"]
        proofs = [row for row in completed if row["search"]["result"]["proved"]]
        result[lane] = {"completed_cases": len(completed), "declared_cases": len(CASES),
                        "independently_replayed_proofs": len(proofs),
                        "unproved_within_bounds": len(completed) - len(proofs),
                        "authored_proposal_calls": sum(row["search"]["result"]["search"]["model_calls"] for row in completed),
                        "native_candidate_executions": sum(row["search"]["result"]["search"]["candidates_executed"] for row in completed),
                        "successful_tactic_decisions": sum(len(row["search"]["result"]["search"]["commands"]) for row in proofs),
                        "real_model_generate_calls": 0}
    return result


def _paired(rows: list[dict]) -> list[dict]:
    indexed = {(row["case_id"], row["lane"]): row for row in rows if row["status"] == "completed"}
    result = []
    for case_id, _ in CASES:
        pair = {lane: indexed.get((case_id, lane)) for lane, _ in LANES}
        record = {"case_id": case_id, "both_lanes_completed": all(row is not None for row in pair.values())}
        for lane, row in pair.items():
            if row is None:
                record[lane] = None
            else:
                value = row["search"]["result"]
                record[lane] = {"proved": value["proved"], "authored_proposal_calls": value["search"]["model_calls"],
                                "states_discovered": value["search"]["states_discovered"],
                                "tactic_decisions": len(value["search"]["commands"]),
                                "commands": value["search"]["commands"]}
        result.append(record)
    return result


def execute_demo(plan: dict, *, root: Path = ROOT, progress: Callable[[dict], None] | None = None) -> dict:
    """At most eight search and eight fresh-replay children; never retry failure."""
    _no_models()
    validate_demo_plan(plan, root)
    rows, complete = [], True
    emit = progress if progress is not None else lambda event: None
    for case_id, _ in CASES:
        for lane, _ in LANES:
            emit({"phase": "search-start", "case_id": case_id, "lane": lane, "completed": len(rows), "total": 8})
            search, search_process = _invoke(_request(plan, case_id, lane), root)
            row = {"case_id": case_id, "lane": lane, "status": "worker-failed" if search is None else "completed",
                   "search": search, "search_process": search_process, "independent_replay": None, "replay_process": None}
            if search is None:
                rows.append(row)
                complete = False
                break
            _validate_search(search, plan)
            if search["result"]["proved"]:
                saved = search["result"]["replay"]
                payload = {"commands": search["result"]["search"]["commands"], "id": saved["id"], "session": saved["session"]}
                emit({"phase": "independent-replay-start", "case_id": case_id, "lane": lane})
                fresh, replay_process = _invoke(_request(plan, case_id, lane, replay=payload), root)
                row.update(independent_replay=fresh, replay_process=replay_process)
                if fresh is None:
                    row["status"] = "replay-worker-failed"
                    rows.append(row)
                    complete = False
                    break
                require(canonical(fresh["result"]) == canonical(saved)
                        and canonical(fresh["profile_contract"]) == canonical(search["profile_contract"]),
                        "fresh independent kernel replay differs from the original-goal proof")
            rows.append(row)
            emit({"phase": "case-completed", "case_id": case_id, "lane": lane,
                  "completed": len(rows), "total": 8, "proved": search["result"]["proved"],
                  "authored_proposal_calls": search["result"]["search"]["model_calls"]})
        if not complete:
            break
    validate_demo_plan(plan, root)
    _no_models()
    record = {"schema": REPORT_SCHEMA, "status": "complete" if complete and len(rows) == 8 else "incomplete",
              "plan": plan, "rows": rows, "summary": _summary(rows), "paired": _paired(rows),
              "real_model_generate_calls": 0,
              "historical_gpu_inference_attested": False, "model_outputs_regenerated": False,
              "saved_model_proposals_used": False, "recovered_model_panel_claimed": False,
              "research_claim_eligible": False, "automatic_retry": False, "claim_boundary": CLAIM,
              "call_accounting": "search.model_calls counts authored deterministic propose calls; actual model-generation calls are zero."}
    result = {**record, "report_sha256": digest(record)}
    require(len(canonical(result)) <= MAX_REPORT_BYTES, "fixture report exceeds its evidence byte bound")
    return result


def fresh_output(path: Path, value: dict | None = None) -> None:
    """Check or atomically publish one fresh artifact, without replacing inputs."""
    path = path.absolute()
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,159}\.json", path.name) is not None,
            "output must have one bounded JSON basename")
    parent = _directory(path.parent)
    try:
        try:
            os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ValueError("output already exists; refusing to overwrite evidence")
        if value is None:
            return
        raw = canonical(value) + b"\n"
        require(len(raw) <= MAX_REPORT_BYTES, "output exceeds artifact byte bound")
        temporary = ".search-dedup-" + uuid.uuid4().hex
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path.name, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
        os.unlink(temporary, dir_fd=parent)
        os.fsync(parent)
    finally:
        os.close(parent)


__all__ = ["AuthoredNamePolicy", "CASES", "LANES", "WORKER_LIMITS", "build_demo_plan", "execute_demo",
           "validate_demo_plan", "source_inventory", "worker"]
