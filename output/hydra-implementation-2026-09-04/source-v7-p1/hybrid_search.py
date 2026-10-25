"""Bounded symbolic / learned / ATP-guided search with native proof authority.

Advisors supply *untrusted tactic text*, never proofs.  Every physical line
extends an immutable, authority-bound native prefix in a fresh session.  A
closed branch must pass both the original finalizer and an independent batch
replay of the complete script before this module reports ``status='proof'``.

The frontier mixes best-first exploration with periodic oldest-first service.
Easy deterministic steps are closed locally; unresolved states enter a FIFO
advice queue, serviced after a finite symbolic burst.  Neither a stream of
rewrites nor an expensive model can consume another component's call budget.
This is exploratory bounded search, not a complete decision procedure.
"""
from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import time
from typing import Callable

from advice_memory import ModelAdviceMemory
from algebra_plan_cost import estimate_algebra_plan, rank_plan_indices
from atom_polynomial import atom_polynomial_chunk_plan
from arithmetic_search import (
    arithmetic_hints, arithmetic_priority, induction_hints, polynomial_identity,
)
from decomposition_memory import DecompositionAttemptMemory
from compact_dispatch import compact_arith_hint
from finite_difference import strengthening_hints
from polynomial_chunks import ChunkPlan, polynomial_chunk_plan
from proof_cost import measure_proof
from peano_lab.batch import MODEL_V1_COMMANDS, run_proof
from peano_lab.engine.state import (
    ProofState, apply_formula_subst, metas_in_formula,
    proof_size, shift_engine_term,
)
from peano_lab.kernel.formulas import (
    And, Bot, Eq, Exists, Forall, Imp, Or, parse_formula_with_names,
)
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero, pretty_term
from peano_lab.ui.prove import SurfaceCapabilities, checked_surface_final
from training.peano_hydra.protocol import validate_statement
from training.peano_policy.search import (
    _AlphaStateIndex, _PrefixSnapshot, _canonical_goals, _new_owner, _replay,
    _validate_candidate, state_sha256,
)


SEARCH_PROFILE = "hydra-playground-hybrid-v7"
MAX_TRACE_BYTES = 512 * 1024
MAX_BRANCH_LOG_BYTES = 128 * 1024
MAX_POLYNOMIAL_ATTEMPTS = 12
MAX_POLYNOMIAL_PLANS = 6
MAX_POLYNOMIAL_COMMANDS = 156
MAX_POLYNOMIAL_SCRIPT_BYTES = 64 * 1024
_SOURCES = frozenset({"heuristic", "model", "vampire"})


@dataclass(frozen=True, slots=True)
class HybridLimits:
    max_depth: int = 32
    max_states: int = 256
    max_tactic_attempts: int = 1024
    max_expansions: int = 128
    max_frontier: int = 64
    candidates_per_state: int = 24
    max_macro_steps: int = 4
    closure_steps: int = 8
    heuristic_burst: int = 4
    max_model_calls: int = 8
    max_vampire_calls: int = 4
    wall_seconds: float = 150.0

    def __post_init__(self):
        ceilings = {
            "max_depth": 160, "max_states": 8192, "max_tactic_attempts": 40000,
            "max_expansions": 4096, "max_frontier": 256,
            "candidates_per_state": 64, "max_macro_steps": 8,
            "closure_steps": 32, "heuristic_burst": 32,
            "max_model_calls": 128, "max_vampire_calls": 24,
        }
        for name, maximum in ceilings.items():
            value = getattr(self, name)
            minimum = 0 if name in {"max_model_calls", "max_vampire_calls"} else 1
            if type(value) is not int or not minimum <= value <= maximum:
                raise ValueError(f"{name} must be an integer in {minimum}..{maximum}")
        if type(self.wall_seconds) not in (int, float) or not math.isfinite(self.wall_seconds) \
                or not 0 < self.wall_seconds <= 600:
            raise ValueError("wall_seconds must be finite and in (0, 600]")


@dataclass(frozen=True, slots=True)
class _Proposal:
    commands: tuple[str, ...]
    source: str
    reason: str
    evidence: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class _Node:
    id: int
    parent_id: int | None
    prefix: _PrefixSnapshot
    provenance: tuple[dict, ...]
    arithmetic_rank: int = 1

    @property
    def commands(self):
        return self.prefix.commands

    @property
    def goals(self):
        return self.prefix.goals

    @property
    def state(self):
        return self.prefix.state

    @property
    def depth(self):
        return len(self.commands)


@dataclass(frozen=True, slots=True)
class _Continuation:
    """Only tactic text; its dictionary key owns the exact checked prefix."""
    plan_id: int
    commands: tuple[str, ...]
    offset: int = 0
    chunk: int = 1


def _one_line(value, maximum=256):
    return (" ".join(str(value).split()) or type(value).__name__)[:maximum]


def _proposal(*commands, reason):
    return _Proposal(tuple(commands), "heuristic", reason)


def _resolved(state):
    goal = state.current()
    if goal is None:
        raise ValueError("a closed state has no tactic choice")
    target = apply_formula_subst(goal.target, state.subst)
    context = tuple((name, apply_formula_subst(formula, state.subst))
                    for name, formula in goal.context)
    return goal, target, context


def _strip_foralls(formula):
    while type(formula) is Forall:
        formula = formula.body
    return formula


def _closure_candidates(state, *, max_macro_steps=4):
    """Equivalence-preserving steps and immediate native closing attempts."""
    goal, target, context = _resolved(state)
    for name, formula in context:
        if formula == target:
            yield _proposal(f"exact {name}", reason="The focused goal is a local hypothesis.")
    if type(target) is Eq and target.left == target.right:
        yield _proposal("refl", reason="Both equality terms are structurally identical.")
    for name, formula in context:
        if type(formula) is Bot:
            yield _proposal(f"cases {name}", reason="Eliminate an explicit contradiction in the local context.")
        if type(formula) is Forall and type(_strip_foralls(formula)) is not Imp:
            yield _proposal(f"apply {name}", reason="Try a universally quantified local hypothesis directly.")
    if type(target) in (Forall, Imp):
        yield _proposal("intro", reason="Introduce the next universal variable or implication hypothesis.")
        return
    if type(target) is And:
        yield _proposal("split", reason="Prove both conjuncts as separate native obligations.")
        return
    hint = compact_arith_hint(goal, target, context)
    if hint is not None:
        yield _Proposal(hint.commands, "heuristic", hint.reason,
            (("strategy", "compact_arith_dispatch"),
             ("schemas", ",".join(hint.schemas)),
             ("selected_assumptions", ",".join(hint.selected_assumptions))))
    if type(target) is Exists or _has_polynomial_structure(target):
        for hint in arithmetic_hints(goal, target, context):
            # Commit a synthesized witness as a closure only when its complete
            # native plan fits. Incomplete plans remain ordinary search branches.
            if hint.closes_goal and len(hint.commands) <= max_macro_steps:
                yield _proposal(*hint.commands, reason=hint.reason)
    if not metas_in_formula(target, state.subst):
        yield _proposal("simp", reason="Normalize by the native checked arithmetic simplifier.")
    formulas = tuple(formula for _, formula in context)
    for name, formula in context:
        if type(formula) is And and (formula.left not in formulas or formula.right not in formulas):
            yield _proposal(f"cases {name}", reason="Extract missing conjuncts from a local hypothesis.")
        if type(formula) is Exists and not _already_cased(name, formula, context):
            yield _proposal(f"cases {name}", reason="Unpack a local existential fact with a fresh native witness.")


def _lower_rigid_term(value, binders):
    """Lower a small term only when it does not depend on a removed binder."""
    stack, inspected = [value], 0
    while stack:
        term = stack.pop()
        inspected += 1
        if inspected > 64:
            return None
        if type(term) is Var:
            if term.index < binders:
                return None
        elif type(term) is Succ:
            stack.append(term.term)
        elif type(term) in (Add, Mul):
            stack.extend((term.left, term.right))
        elif type(term) is not Zero:
            return None
    return shift_engine_term(value, -binders)


def _successor_witnesses(goal, target, context):
    """Suggest small constructor witnesses; native replay proves every step.

    A predecessor of the right summand gives a predecessor of the sum by
    PA4. Local successor equalities supply additional predecessor terms.
    This is bounded term synthesis, not an imported arithmetic theorem.
    """
    if type(target) is not Exists or type(target.body) is not Eq:
        return ()
    body = target.body
    rigid = None
    for pattern, other in ((body.left, body.right), (body.right, body.left)):
        if type(pattern) is Succ and pattern.term == Var(0):
            rigid = _lower_rigid_term(other, 1)
            if rigid is not None:
                break
    if rigid is None:
        return ()

    def predecessors(term, depth=0):
        if type(term) is Succ:
            yield term.term, ()
        for name, formula in context[:16]:
            if type(formula) is not Eq:
                continue
            if type(formula.left) is Succ and formula.right == term:
                yield formula.left.term, (f"rewrite <- {name}",)
            if type(formula.right) is Succ and formula.left == term:
                yield formula.right.term, (f"rewrite {name}",)
        if type(term) is Add and depth < 3:
            for predecessor, rewrites in predecessors(term.right, depth + 1):
                yield Add(term.left, predecessor), rewrites

    proposals, seen = [], set()
    for term, rewrites in predecessors(rigid):
        if _lower_rigid_term(term, 0) is None:
            continue
        text = pretty_term(term, list(goal.variables))
        commands = (f"exists ({text})",) + rewrites + ("simp",)
        if len(text.encode("utf-8")) > 192 or commands in seen:
            continue
        seen.add(commands)
        proposals.append(_proposal(*commands, reason="Construct a successor witness from a local predecessor and the native addition recursion."))
        if len(proposals) == 8:
            break
    return tuple(proposals)


def _ground_terms(formula, *, limit=16):
    """Rigid subterms, lowered out of binders only if no local slot escapes."""
    result = []
    stack = [(formula, 0)]
    inspected = 0
    while stack and len(result) < limit and inspected < 512:
        value, depth = stack.pop()
        inspected += 1
        kind = type(value)
        if kind in (Forall, Exists):
            stack.append((value.body, depth + 1))
        elif kind in (Eq, And, Or, Imp):
            stack.extend(((value.right, depth), (value.left, depth)))
        elif kind in (Var, Zero, Succ, Add, Mul):
            term_stack = [value]
            rigid = True
            size = 0
            while term_stack and size <= 64:
                term = term_stack.pop()
                size += 1
                if type(term) is Var:
                    rigid = rigid and term.index >= depth
                elif type(term) is Succ:
                    term_stack.append(term.term)
                elif type(term) in (Add, Mul):
                    term_stack.extend((term.left, term.right))
                elif type(term) is not Zero:
                    rigid = False
            if rigid and not term_stack and size <= 64:
                lowered = shift_engine_term(value, -depth)
                if lowered not in result:
                    result.append(lowered)
            if kind is Succ:
                stack.append((value.term, depth))
            elif kind in (Add, Mul):
                stack.extend(((value.right, depth), (value.left, depth)))
    return tuple(result)


def _term_pool(goal, target, context):
    terms = list(_ground_terms(target))
    for _, formula in context[:8]:
        for term in _ground_terms(formula, limit=4):
            if term not in terms:
                terms.append(term)
    terms.extend(Var(index) for index in range(len(goal.variables)))
    terms.extend((Zero(), Succ(Zero())))
    result = []
    for term in terms:
        try:
            text = pretty_term(term, list(goal.variables))
        except (TypeError, ValueError, IndexError):
            continue
        if len(text.encode("utf-8")) <= 192 and text not in result:
            result.append(text)
        if len(result) == 12:
            break
    return result


def _already_cased(name, formula, context):
    # Native cases keeps the original hypothesis, so avoid reintroducing an
    # identical case assumption indefinitely in the same focused context.
    if type(formula) is Or:
        return any(other != name and item in (formula.left, formula.right)
                   for other, item in context)
    if type(formula) is Exists:
        return any(other.startswith(name + "_witness") for other, _ in context)
    return False


def _has_polynomial_structure(formula):
    stack = [formula]
    count = 0
    arithmetic = False
    while stack and count < 256:
        item = stack.pop()
        count += 1
        if type(item) in (Add, Mul):
            arithmetic = True
            stack.extend((item.left, item.right))
        elif type(item) is Eq:
            stack.extend((item.left, item.right))
        elif type(item) is Succ:
            stack.append(item.term)
        elif type(item) not in (Var, Zero):
            return False
    return not stack and arithmetic


def heuristic_candidates(state, *, max_candidates=24, max_macro_steps=4):
    """Generate short, inspectable tactics; no candidate is trusted to work."""
    goal, target, context = _resolved(state)
    groups = [[], [], [], [], [], []]
    arithmetic, immediate, logical, instantiation, induction, rewrites = groups
    for hint in arithmetic_hints(goal, target, context):
        arithmetic.append(_proposal(*hint.commands[:max_macro_steps], reason=hint.reason))
    # A strengthening connector must fit in full: its partial prefixes do not
    # yet justify replacing the original goal with the stronger invariant.
    if max_macro_steps >= 7:
        for hint in strengthening_hints(goal, target, context):
            if len(hint.commands) <= max_macro_steps:
                arithmetic.append(_Proposal(hint.commands, "heuristic", hint.reason,
                    (("strategy", "finite_difference_strengthening"),)))
    for hint in induction_hints(goal, target, context):
        arithmetic.append(_proposal(*hint.commands[:max_macro_steps], reason=hint.reason))
    # Unlike structural exact matching, native assumption can resolve a
    # metavariable created by backward application. Keep it as a branch so
    # alternative assignments remain available if later obligations fail.
    immediate.append(_proposal("assumption", reason="Try a unifying local hypothesis, including unresolved backward-application premises."))
    equations = [(name, formula) for name, formula in context[:16]
                 if type(_strip_foralls(formula)) is Eq]
    terms = _term_pool(goal, target, context)

    if type(target) is Eq:
        for name, formula in equations:
            if type(formula) is Eq and formula.left == target.right and formula.right == target.left:
                immediate.append(_proposal("symm", f"exact {name}", reason="Use the symmetric local equality."))
        for name, _ in equations[:6]:
            immediate.append(_proposal(f"simp [{name}]", reason="Normalize using one explicit local equality."))
        if len(equations) > 1:
            names = ", ".join(name for name, _ in equations[:4])
            immediate.insert(0, _proposal(f"simp [{names}]", reason="Normalize through a short chain of local equalities."))
        if type(target.left) is type(target.right) and type(target.left) in (Succ, Add, Mul):
            logical.append(_proposal("congr", reason="Reduce matching outer arithmetic symbols to component equalities."))
        immediate.append(_proposal("apply PA2", "assumption", reason="Recover an equality from equal successors using PA2."))
        if _has_polynomial_structure(target) and polynomial_identity(target) is not False:
            immediate.append(_proposal("ring", reason="Try native certificate-producing polynomial normalization."))
        logical.append(_proposal("norm_num", reason="Evaluate bounded closed numeral subexpressions with native certificates."))
        # The macro above keeps an unsuccessful symmetry branch transactional.
        # A bare symmetry is still useful before nontrivial specialization.
        if not state.history or state.history[-1].tactic != "symm":
            rewrites.append(_proposal("symm", reason="Explore the reverse orientation of the equality."))

    if type(target) is Or:
        logical.extend((_proposal("left", reason="Explore the left disjunct."),
                        _proposal("right", reason="Explore the right disjunct.")))
    if type(target) is Exists:
        logical.extend(_successor_witnesses(goal, target, context))
        logical.extend(_proposal(f"exists ({term})", reason="Try a rigid witness from this goal and its local context.")
                       for term in terms)

    for name, formula in context[:16]:
        if type(_strip_foralls(formula)) is Imp:
            logical.append(_proposal(f"apply {name}", reason="Backchain through a local implication."))
        if type(formula) in (Or, Exists) and not _already_cased(name, formula, context):
            logical.append(_proposal(f"cases {name}", reason="Explore the native cases of a local hypothesis."))
        if type(formula) is Forall:
            for term in terms[:4]:
                instantiation.append(_proposal(f"specialize {name} ({term})", reason="Instantiate a universal hypothesis at a relevant rigid term."))
                if type(formula.body) in (And, Or, Exists):
                    instantiation.append(_proposal(f"specialize {name} ({term})", f"cases {name}",
                        reason="Instantiate and decompose a quantified local fact."))

    if type(target) is Bot:
        immediate.append(_proposal("apply PA1", "assumption", reason="Use the Peano nonzero-successor axiom on a local contradiction."))
    elif any(type(_strip_foralls(formula)) is Imp and type(_strip_foralls(formula).right) is Bot
             for _, formula in context):
        logical.append(_proposal("exfalso", reason="Try deriving contradiction from the available negative hypotheses."))

    if not metas_in_formula(target, state.subst):
        for variable in goal.variables[:3]:
            # Do not recursively induct on a successor-case variable already
            # carrying this path's induction hypothesis. Other parameters can
            # still be considered in a later state.
            if any(name == "IH" or name.startswith("IH") for name, _ in context):
                break
            induction.append(_proposal(f"induction {variable}", "simp",
                reason="Try induction and discharge its base case by native simplification."))
            induction.append(_proposal(f"induction {variable}", reason="Open base and successor obligations for this parameter."))
        for name, _ in equations[:6]:
            for direction in ("", "<- "):
                command = f"rewrite {direction}{name}"
                rewrites.append(_proposal(command, "simp", reason="Rewrite an equality, then simplify the resulting obligation."))
                rewrites.append(_proposal(command, reason="Explore a locally justified equality rewrite."))
        if equations:
            names = ", ".join("<- " + name for name, _ in equations[:3])
            rewrites.append(_proposal(f"simp [{names}]", reason="Try the reverse orientations of selected local equalities."))

    # Interleave tactic families so numerous witnesses or specializations do
    # not suppress induction/cases under the finite candidate budget.
    seen = set()
    result = []
    for rank in range(max((len(group) for group in groups), default=0)):
        for group in groups:
            if rank < len(group):
                proposal = group[rank]
                if proposal.commands not in seen:
                    seen.add(proposal.commands)
                    result.append(proposal)
                    if len(result) == max_candidates:
                        return tuple(result)
    return tuple(result)


def search(theorem, *, capabilities=None, model_policy=None, vampire_advisor=None,
           limits=HybridLimits(), emit_progress: Callable[[dict], None] | None = None):
    """Search one theorem with optional lazy model and untrusted ATP advisors.

    ``model_policy.propose(goals_tuple, max_candidates=4)`` returns a bounded
    tuple of complete lines. ``vampire_advisor.advise(ProofState)`` returns a
    bounded dictionary with ``suggestions`` and ``solver.invocations`` (0/1).
    The callback owner must enforce the external solver's process limits.
    Neither callback is invoked for a goal closed by deterministic tactics.
    """
    if type(limits) is not HybridLimits:
        raise TypeError("limits must be an exact HybridLimits")
    if capabilities is None:
        capabilities = SurfaceCapabilities(label="hydra-playground-hybrid-no-imports-v1",
            allowed_commands=MODEL_V1_COMMANDS, allowed_theorems=frozenset())
    if type(capabilities) is not SurfaceCapabilities or capabilities.allowed_commands is None \
            or capabilities.allowed_theorems != frozenset():
        raise ValueError("Hybrid search requires finite native commands and no theorem imports.")
    if model_policy is not None and not callable(getattr(model_policy, "propose", None)):
        raise TypeError("model_policy must provide propose")
    if vampire_advisor is not None and not callable(getattr(vampire_advisor, "advise", None)):
        raise TypeError("vampire_advisor must provide advise")
    canonical = validate_statement(theorem)
    target, names = parse_formula_with_names(canonical)
    if names:
        raise ValueError("Quantify all free theorem variables explicitly.")
    started = time.monotonic()
    deadline = started + limits.wall_seconds
    owner = _new_owner(target, names, canonical, classical=False, replay_id=0)
    initial_goals = _canonical_goals(owner)
    root = _Node(0, None, _PrefixSnapshot.capture(owner, commands=(), goals=initial_goals,
                  capabilities=capabilities), ())
    alpha = _AlphaStateIndex()
    root_key = alpha.key(owner.state)
    seen = {root_key}
    alpha.remember(root_key, initial_goals)
    frontier = {0: root}
    deferred = deque()
    deferred_ids = set()
    counts = {"model_calls": 0, "model_advisor_calls": 0,
              "vampire_calls": 0, "vampire_advisor_calls": 0,
              "states_expanded": 0, "states_discovered": 1, "candidates_executed": 0,
              "tactic_attempts": 0, "frontier_peak": 1, "depth_reached": 0,
              "heuristic_candidates": 0, "model_candidates": 0, "vampire_candidates": 0,
              "branches_omitted": 0, "diagnostics_omitted": 0,
              "strengthening_candidates": 0, "strengthening_expansions": 0,
              "compact_arith_attempts": 0, "compact_arith_accepted": 0,
              "compact_arith_rejected": 0}
    native_timing = {"transition_seconds": 0.0, "finalization_seconds": 0.0,
                     "independent_replay_seconds": 0.0, "measurement_seconds": 0.0}
    final_proof_cost = None
    diagnostics, branches, advisor_results = [], [], []
    branch_bytes = 0
    limited_reasons = set()
    replay_id = 0
    next_id = 0
    macro_id = 0
    best = root
    proved = None
    stopped_vampire = False
    model_advice_memory = ModelAdviceMemory()
    decomposition_memory = DecompositionAttemptMemory()
    since_advice = 0
    frontier_turn = 0
    completed_macro_prefixes = set()
    strengthened_nodes = set()
    ring_failed_nodes = set()
    decomposition_considered = set()
    continuations = {}
    polynomial_fallbacks = {}
    polynomial_records = []
    polynomial_counts = {"planning_attempts": 0, "generated_plans": 0,
                         "planner_invocations": 0,
                         "cost_comparisons": 0, "fallbacks_activated": 0,
                         "repeated_decompositions_skipped": 0,
                         "chunks_attempted": 0, "native_steps_accepted": 0,
                         "local_sequences_completed": 0}
    vampire_cache_hits = 0

    def note(kind, message, node=None, command=None):
        if len(diagnostics) >= 64:
            counts["diagnostics_omitted"] += 1
            return
        diagnostics.append({"kind": kind, "message": _one_line(message),
            "branch_id": None if node is None else node.id, "command": command})

    def progress(phase, message, node=None):
        if emit_progress is not None:
            event = {"phase": phase, "message": message,
                     "model_calls": counts["model_calls"], "vampire_calls": counts["vampire_calls"],
                     "model_repeated_prompts_skipped": model_advice_memory.hits,
                     "vampire_advice_cache": {"cache_hits": vampire_cache_hits},
                     "polynomial_decomposition": {
                         "repeated_decompositions_skipped": polynomial_counts["repeated_decompositions_skipped"]},
                     "states_expanded": counts["states_expanded"],
                     "states_discovered": counts["states_discovered"],
                     "tactic_attempts": counts["tactic_attempts"], "frontier": len(frontier)}
            if node is not None:
                event.update(branch_id=node.id, depth=node.depth, open_goals=len(node.goals))
            emit_progress(event)

    def log_branch(record):
        nonlocal branch_bytes
        encoded = json.dumps(record, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if branch_bytes + len(encoded) > MAX_BRANCH_LOG_BYTES:
            counts["branches_omitted"] += 1
            return
        branch_bytes += len(encoded)
        branches.append(record)

    def expired():
        if time.monotonic() >= deadline:
            limited_reasons.add("wall_seconds")
            return True
        return False

    def priority(node):
        # Retain intermediate macro alternatives, but prefer their already
        # checked continuation. Otherwise a solved induction base can repeatedly
        # outrank the successor case merely because its formula is smaller.
        # One generated invariant gets a small, explicit exploration window;
        # oldest-first and deferred-advisor service still bound other waiting.
        preferred = node.id in strengthened_nodes and counts["strengthening_expansions"] < 8
        planned = node.id in continuations or node.id in ring_failed_nodes
        return (not planned, node.id in completed_macro_prefixes, not preferred, node.arithmetic_rank,
                len(node.goals), sum(len(goal) for goal in node.goals), node.depth, node.id)

    def consider_best(node):
        nonlocal best
        if priority(node) < priority(best) or best.id == 0:
            best = node

    def put(node):
        if node.id in frontier:
            return
        frontier[node.id] = node
        if len(frontier) > limits.max_frontier:
            # Keep the oldest pending branch as well as the best-scoring
            # branches; never mistake this lossy resource pruning for failure.
            oldest = min(frontier)
            worst = max((item for item in frontier.values() if item.id != oldest), key=priority)
            del frontier[worst.id]
            ring_failed_nodes.discard(worst.id)
            abandoned = continuations.pop(worst.id, None)
            if abandoned is not None:
                polynomial_records[abandoned.plan_id]["status"] = "frontier_pruned"
            limited_reasons.add("max_frontier")
        counts["frontier_peak"] = max(counts["frontier_peak"], len(frontier))

    def apply_script(parent, proposal):
        nonlocal replay_id, next_id, macro_id, proved, final_proof_cost
        if expired() or proved is not None:
            return None
        if type(proposal) is not _Proposal or proposal.source not in _SOURCES \
                or type(proposal.commands) is not tuple or not 1 <= len(proposal.commands) <= limits.max_macro_steps:
            note("invalid_candidate", "Advisor returned an invalid or oversized tactic macro.", parent)
            return None
        validated = []
        for raw in proposal.commands:
            command, error = _validate_candidate(raw, numeral_limit=64)
            if command is None or len(command.encode("utf-8")) > 512:
                note("invalid_candidate", error or "Candidate exceeded the tactic byte bound.", parent)
                return None
            if command.split(maxsplit=1)[0] not in capabilities.allowed_commands:
                note("authority_rejection", "Candidate command is outside the native search authority.", parent, command)
                return None
            validated.append(command)
        if parent.depth + len(validated) > limits.max_depth:
            limited_reasons.add("max_depth")
            return None
        strengthening = proposal.source == "heuristic" and (
            "strategy", "finite_difference_strengthening") in proposal.evidence
        decomposition = proposal.source == "heuristic" and (
            "strategy", "polynomial_decomposition") in proposal.evidence
        if strengthening:
            # Search-local state is separate from native alpha-state identity.
            # Never regenerate the same family on renamed or sibling branches.
            if counts["strengthening_candidates"] >= 1:
                return None
            counts["strengthening_candidates"] += 1
        macro_id += 1
        current_macro = macro_id
        counts["candidates_executed"] += 1
        counts[proposal.source + "_candidates"] += 1
        node = parent
        intermediate_ids = []
        for index, command in enumerate(validated):
            if expired():
                return None
            if counts["tactic_attempts"] >= limits.max_tactic_attempts:
                limited_reasons.add("max_tactic_attempts")
                return None
            counts["tactic_attempts"] += 1
            replay_id += 1
            path = node.commands + (command,)
            compact = command.split(maxsplit=1)[0] == "compact_arith"
            if compact:
                counts["compact_arith_attempts"] += 1
            step_started = time.monotonic()
            try:
                following, failed, error = _replay(target, names, canonical, path,
                    classical=False, capabilities=capabilities, replay_id=replay_id,
                    prefix=node.prefix, expected_goals=node.goals)
            finally:
                native_timing["transition_seconds"] += time.monotonic() - step_started
            if compact:
                counts["compact_arith_accepted" if following is not None else "compact_arith_rejected"] += 1
            if following is None:
                if isinstance(error, (TimeoutError, MemoryError)):
                    raise error
                if failed is not None and failed < len(path) - 1:
                    raise RuntimeError("An accepted immutable prefix failed its authority restoration.") from error
                log_branch({"id": None, "parent_id": node.id, "source": proposal.source,
                    "macro_id": current_macro, "macro_step": index + 1, "command": command,
                    "status": "rejected", "reason": _one_line(error)})
                if command == "ring" and not decomposition \
                        and node.id not in decomposition_considered \
                        and polynomial_counts["planning_attempts"] < MAX_POLYNOMIAL_ATTEMPTS \
                        and polynomial_counts["generated_plans"] < MAX_POLYNOMIAL_PLANS \
                        and polynomial_identity(_resolved(node.state)[1]) is True:
                    # Preserve the exact prefix that actually rejected ring,
                    # including a useful intermediate prefix of a failed macro.
                    # A planner result alone never creates a checked edge.
                    ring_failed_nodes.add(node.id)
                    put(node)
                return None
            counts["depth_reached"] = max(counts["depth_reached"], len(path))
            goals = _canonical_goals(following)
            terminal = following.state.is_done()
            if not terminal and following.state.goals == node.state.goals \
                    and dict(following.state.subst) == dict(node.state.subst):
                log_branch({"id": None, "parent_id": node.id, "source": proposal.source,
                    "macro_id": current_macro, "macro_step": index + 1, "command": command,
                    "status": "no_progress", "reason": "The native obligations and substitutions did not change."})
                return None
            key = None if terminal else alpha.key(following.state)
            if not terminal and key in seen:
                alpha.duplicate(key, goals)
                log_branch({"id": None, "parent_id": node.id, "source": proposal.source,
                    "macro_id": current_macro, "macro_step": index + 1, "command": command,
                    "status": "duplicate", "reason": "An identical conservative native alpha-state is already retained."})
                return None
            if not terminal and counts["states_discovered"] >= limits.max_states:
                limited_reasons.add("max_states")
                return None
            next_id += 1
            provenance = {"step": len(path), "branch_id": next_id, "parent_id": node.id,
                          "source": proposal.source, "macro_id": current_macro, "macro_step": index + 1,
                          "command": command, "reason": _one_line(proposal.reason)}
            if proposal.evidence:
                provenance["evidence"] = dict(proposal.evidence)
            new_node = _Node(next_id, node.id,
                _PrefixSnapshot.capture(following, commands=path, goals=goals, capabilities=capabilities),
                node.provenance + (provenance,),
                0 if terminal else arithmetic_priority(*_resolved(following.state)))
            if strengthening or node.id in strengthened_nodes:
                strengthened_nodes.add(new_node.id)
            branch_record = {"id": new_node.id, "parent_id": node.id, "source": proposal.source,
                "macro_id": current_macro, "macro_step": index + 1, "command": command,
                "status": "closed_pending_verification" if terminal else "open",
                "open_goals": len(goals), "depth": new_node.depth,
                "state_sha256": state_sha256(goals), "reason": _one_line(proposal.reason)}
            rendered_goals = list(goals)
            if len(json.dumps(rendered_goals, ensure_ascii=False).encode("utf-8")) <= 8192:
                branch_record["goals_after"] = rendered_goals
            else:
                branch_record["goals_omitted"] = "Native goal snapshot exceeded the 8 KiB per-node preview bound."
            log_branch(branch_record)
            if terminal:
                try:
                    final_started = time.monotonic()
                    try:
                        certificate = checked_surface_final(following.state, target, classical=False, trace=None)
                    finally:
                        native_timing["finalization_seconds"] += time.monotonic() - final_started
                    certificate_nodes = proof_size(certificate)
                    replay_started = time.monotonic()
                    try:
                        replay = run_proof(canonical, path, request_id="hybrid-independent-replay",
                            classical=False, on_error="stop", capabilities=capabilities,
                            trace_byte_limit=MAX_TRACE_BYTES)
                    finally:
                        native_timing["independent_replay_seconds"] += time.monotonic() - replay_started
                    if replay.status != "proved" or replay.kernel_checked is not True \
                            or replay.theorem != canonical or replay.goals != () \
                            or replay.proof_nodes != certificate_nodes:
                        raise RuntimeError("Independent replay did not agree with the original-theorem finalizer.")
                except (TimeoutError, MemoryError):
                    raise
                except Exception as error:
                    branch_record["status"] = "kernel_rejected"
                    note("kernel_rejection", error, new_node, command)
                    return None
                measurement_started = time.monotonic()
                measured = measure_proof(certificate, stage="final", should_stop=expired)
                native_timing["measurement_seconds"] += time.monotonic() - measurement_started
                if expired():
                    branch_record["status"] = "verified_after_search_deadline"
                    return None
                branch_record["status"] = "proved"
                final_proof_cost = measured
                proved = (new_node, certificate_nodes, replay.to_dict(include_trace=True))
                progress("verified", "The native kernel independently replayed and verified this proof.", new_node)
                return new_node
            seen.add(key)
            alpha.remember(key, goals)
            counts["states_discovered"] += 1
            consider_best(new_node)
            if index + 1 < len(validated):
                # A useful checked prefix remains explorable even when the
                # next line of an untrusted macro fails. Without this, marking
                # an intermediate state seen would silently lose that branch.
                put(new_node)
                intermediate_ids.append(new_node.id)
            node = new_node
        completed_macro_prefixes.update(intermediate_ids)
        return node

    def start_decomposition(node):
        ring_failed_nodes.discard(node.id)
        decomposition_considered.add(node.id)
        if polynomial_counts["planning_attempts"] >= MAX_POLYNOMIAL_ATTEMPTS \
                or polynomial_counts["generated_plans"] >= MAX_POLYNOMIAL_PLANS \
                or expired():
            return None
        previous = decomposition_memory.previously_attempted(node.goals, node.depth)
        if previous is not None:
            polynomial_counts["repeated_decompositions_skipped"] += 1
            note("polynomial_repeat_skipped",
                 f"An exact full-goals plan was already attempted at depth {previous.depth} "
                 f"(plan {previous.plan_id}); skipping this equal/deeper prefix.", node)
            return None
        polynomial_counts["planning_attempts"] += 1
        record = {"plan_id": len(polynomial_records), "branch_id": node.id,
                  "state_sha256": state_sha256(node.goals), "status": "no_plan",
                  "native_steps_accepted": 0, "chunks_attempted": 0,
                  "kernel_checked": False}
        polynomial_records.append(record)
        try:
            goal, equation, context = _resolved(node.state)
            if type(equation) is not Eq or polynomial_identity(equation) is not True:
                record["status"] = "not_a_rigid_polynomial_identity"
                return None
            alternatives = []
            for planner in (atom_polynomial_chunk_plan, polynomial_chunk_plan):
                if expired():
                    break
                polynomial_counts["planner_invocations"] += 1
                plan = planner(equation, goal.variables, context, should_stop=expired)
                if plan is not None:
                    alternatives.append(plan)
            if not alternatives:
                return None
            prepared, estimates = [], []
            for index, plan in enumerate(alternatives):
                candidate = record if index == 0 else {
                    "plan_id": len(polynomial_records), "branch_id": node.id,
                    "state_sha256": record["state_sha256"], "status": "no_plan",
                    "native_steps_accepted": 0, "chunks_attempted": 0, "kernel_checked": False}
                if index:
                    polynomial_records.append(candidate)
                try:
                    if type(plan) is not ChunkPlan or type(plan.commands) is not tuple \
                            or not 1 <= len(plan.commands) <= MAX_POLYNOMIAL_COMMANDS:
                        raise ValueError("The polynomial planner returned an invalid command sequence.")
                    validated = []
                    for raw in plan.commands:
                        command, error = _validate_candidate(raw, numeral_limit=64)
                        if command is None or len(command.encode("utf-8")) > 512:
                            raise ValueError(error or "A polynomial command exceeds its byte bound.")
                        if command.split(maxsplit=1)[0] not in capabilities.allowed_commands:
                            raise ValueError("A polynomial command is outside the native authority.")
                        validated.append(command)
                    script = ("\n".join(validated) + "\n").encode("utf-8")
                    if len(script) > MAX_POLYNOMIAL_SCRIPT_BYTES:
                        raise ValueError("A polynomial plan exceeds its total script-byte bound.")
                    candidate.update(commands=len(validated), script_bytes=len(script),
                        script_sha256=hashlib.sha256(script).hexdigest(),
                        obligations=len(plan.obligations), planner=_one_line(plan.strategy, 64))
                    if validated == ["ring"]:
                        candidate["status"] = "unchanged_ring_declined"
                        continue
                    if node.depth + len(validated) > limits.max_depth:
                        candidate["status"] = "remaining_depth_insufficient"
                        limited_reasons.add("max_depth")
                        continue
                    if any(item.commands == tuple(validated) for item in prepared):
                        candidate["status"] = "duplicate_plan"
                        continue
                    cost = estimate_algebra_plan(equation, tuple(validated),
                        obligations=plan.obligations, should_stop=expired)
                    # Report bounded aggregate features, not another copy of
                    # every obligation. The score cannot admit a native edge.
                    candidate["estimated_cost"] = {key: value for key, value in cost.items()
                        if key not in {"ring_obligations", "source_ast"}}
                    candidate["status"] = "retained_alternative"
                    prepared.append(_Continuation(candidate["plan_id"], tuple(validated)))
                    estimates.append(cost)
                except (ValueError, TypeError, RecursionError) as error:
                    candidate["status"] = "invalid_plan"
                    note("polynomial_plan_rejected", error, node)
            if not prepared:
                return None
            if expired():
                record["status"] = "search_deadline"
                return None
            order = rank_plan_indices(estimates, fallback_index=0)
            if len(order) > 1:
                polynomial_counts["cost_comparisons"] += 1
            chosen = prepared[order[0]]
            chosen_record = polynomial_records[chosen.plan_id]
            chosen_record["ranked_plan_ids"] = [prepared[item].plan_id for item in order]
            chosen_record["original_fallback_plan_id"] = prepared[0].plan_id
            if len(order) > 1:
                # At most two planners; retain the other plan at its original
                # immutable prefix, never at a partially executed child.
                polynomial_fallbacks[chosen.plan_id] = (node, prepared[order[1]])
            polynomial_counts["generated_plans"] += 1
            chosen_record["status"] = "proposed"
            chosen_record["attempt_memory_retained"] = decomposition_memory.remember_attempt(
                node.goals, node.depth, chosen.plan_id)
            return chosen
        except (TimeoutError, MemoryError):
            raise
        except (ValueError, TypeError, RecursionError) as error:
            record["status"] = "invalid_plan"
            note("polynomial_plan_rejected", error, node)
            return None

    def continue_decomposition(node, pending):
        """Run one ordinary bounded macro, then bind text to its exact child."""
        record = polynomial_records[pending.plan_id]
        size = min(8, limits.max_macro_steps)
        commands = pending.commands[pending.offset:pending.offset + size]
        record["chunks_attempted"] += 1
        polynomial_counts["chunks_attempted"] += 1
        before = counts["states_discovered"]
        child = apply_script(node, _Proposal(commands, "heuristic",
            "Prove smaller polynomial obligations through the unchanged native tactics.",
            (("strategy", "polynomial_decomposition"), ("plan_id", str(pending.plan_id)),
             ("chunk", str(pending.chunk)), ("planner", record["planner"]))))
        # Open states count only after native admission; a terminal state
        # counts only after both the finalizer and independent replay pass.
        accepted = counts["states_discovered"] - before + int(proved is not None)
        record["native_steps_accepted"] += accepted
        polynomial_counts["native_steps_accepted"] += accepted
        if child is None:
            # Partial checked prefixes already retained by apply_script remain
            # ordinary alternatives. Never attach this remainder to any of them.
            record["status"] = "sequence_stopped"
            fallback = polynomial_fallbacks.pop(pending.plan_id, None)
            if fallback is not None:
                origin, alternative = fallback
                alternative_record = polynomial_records[alternative.plan_id]
                if polynomial_counts["generated_plans"] < MAX_POLYNOMIAL_PLANS and not expired():
                    polynomial_counts["generated_plans"] += 1
                    polynomial_counts["fallbacks_activated"] += 1
                    alternative_record["status"] = "fallback_pending"
                    alternative_record["fallback_for_plan_id"] = pending.plan_id
                    continuations[origin.id] = alternative
                    put(origin)
                    return origin
                else:
                    alternative_record["status"] = "fallback_resource_stop"
            return None
        following = pending.offset + len(commands)
        if proved is not None:
            record["status"] = "original_theorem_verified"
        elif following == len(pending.commands):
            record["status"] = "local_sequence_completed"
            polynomial_counts["local_sequences_completed"] += 1
            polynomial_fallbacks.pop(pending.plan_id, None)
        else:
            record["status"] = "continuation_pending"
            continuations[child.id] = _Continuation(pending.plan_id, pending.commands,
                                                   following, pending.chunk + 1)
        if proved is None:
            put(child)
        progress("symbolic", "Checking a bounded sequence of smaller algebraic obligations.", child)
        return child

    def close(node):
        """Return (residual, saturated); every accepted closure edge is visible."""
        for _ in range(limits.closure_steps):
            if node.depth >= limits.max_depth or expired():
                if node.depth >= limits.max_depth:
                    limited_reasons.add("max_depth")
                return node, True
            successor = None
            for candidate in _closure_candidates(node.state, max_macro_steps=limits.max_macro_steps):
                successor = apply_script(node, candidate)
                if successor is not None or proved is not None:
                    break
                if counts["tactic_attempts"] >= limits.max_tactic_attempts:
                    return node, True
            if successor is None:
                return node, True
            node = successor
            if proved is not None:
                return node, True
        return node, False

    def assist(node):
        nonlocal stopped_vampire, vampire_cache_hits
        if vampire_advisor is not None and not stopped_vampire \
                and counts["vampire_advisor_calls"] < limits.max_vampire_calls:
            counts["vampire_advisor_calls"] += 1
            progress("vampire", "Consulting Vampire for untrusted local proof guidance.", node)
            try:
                advice = vampire_advisor.advise(node.state)
                if type(advice) is not dict or type(advice.get("solver")) is not dict:
                    raise ValueError("Vampire advisor returned malformed metadata.")
                solver = advice["solver"]
                invocations = solver.get("invocations", 0)
                if type(invocations) is not int or invocations not in (0, 1):
                    raise ValueError("One advisor request may run at most one Vampire process.")
                counts["vampire_calls"] += invocations
                # Unsupported focused states (for example unresolved metas)
                # do not make the installed solver unavailable to later ones.
                if solver.get("available") is False and (
                        advice.get("status") == "unavailable" or solver.get("status") == "unavailable"):
                    stopped_vampire = True
                suggestions = advice.get("suggestions", [])
                if type(suggestions) not in (list, tuple):
                    raise ValueError("Vampire suggestions must be a finite sequence.")
                if suggestions and (invocations != 1 or solver.get("available") is not True):
                    note("vampire_candidate_error", "Ignoring solver-attributed tactics without an actual available solver invocation.", node)
                    suggestions = []
                advice_record = {"branch_id": node.id,
                    "status": _one_line(advice.get("status", solver.get("status", "unknown"))),
                    "szs_status": _one_line(solver.get("szs_status", "unknown")),
                    "invocations": invocations, "available": solver.get("available") is True,
                    "problem_sha256": _one_line(advice.get("problem_sha256", "")),
                    "suggestions": min(len(suggestions), 12),
                    "kernel_checked": False}
                cache = advice.get("cache")
                if type(cache) is dict:
                    # Optional bounded metadata is diagnostic only. Cache hits
                    # never become fresh invocations or proof contributions.
                    kept_cache = {}
                    for key in ("policy", "request", "hit", "stored", "previous_request",
                                "previous_invocation", "previous_status", "previous_exit_code",
                                "previous_reason", "previous_profile", "previous_binary_sha256"):
                        value = cache.get(key)
                        if type(value) is str:
                            kept_cache[key] = _one_line(value)
                        elif value is None or type(value) in (bool, int):
                            kept_cache[key] = value
                    if cache.get("hit") is True:
                        if invocations != 0 or suggestions:
                            raise ValueError("A cached unsuccessful request cannot invoke Vampire or supply tactics.")
                        vampire_cache_hits += 1
                    advice_record["cache"] = kept_cache
                advisor_results.append(advice_record)
                for item in suggestions[:12]:
                    if type(item) is not dict or type(item.get("commands")) not in (list, tuple):
                        note("vampire_candidate_error", "Malformed solver suggestion.", node)
                        continue
                    evidence = (("problem_sha256", _one_line(advice.get("problem_sha256", ""))),)
                    assumptions = item.get("assumptions", [])
                    if type(assumptions) in (list, tuple) and all(type(name) is str for name in assumptions[:16]):
                        evidence += (("assumptions", _one_line(", ".join(assumptions[:16]))),)
                    proposal = _Proposal(tuple(item["commands"]), "vampire",
                        _one_line(item.get("reason", "Untrusted solver guidance, checked by the native surface.")), evidence)
                    child = apply_script(node, proposal)
                    if proved is not None:
                        return
                    if child is not None:
                        put(child)
            except (TimeoutError, MemoryError):
                raise
            except Exception as error:
                note("vampire_error", error, node)
        if expired() or counts["tactic_attempts"] >= limits.max_tactic_attempts:
            return
        if model_policy is not None and counts["model_advisor_calls"] < limits.max_model_calls:
            if model_advice_memory.previously_decoded(node.goals) is not None:
                progress("model_skipped", "This exact full proof state was already decoded; preserving the call budget for another choice.", node)
                return
            counts["model_advisor_calls"] += 1
            before_calls = getattr(model_policy, "calls", None)
            counted = False
            progress("model", "Asking the trained model to rank tactics at an unresolved choice point.", node)
            try:
                candidates = model_policy.propose(node.goals, max_candidates=4)
                after_calls = getattr(model_policy, "calls", None)
                if type(before_calls) is int and type(after_calls) is int:
                    if after_calls - before_calls not in (0, 1):
                        raise RuntimeError("One model advisor request may perform at most one candidate-batch decode.")
                    counts["model_calls"] += after_calls - before_calls
                else:
                    counts["model_calls"] += 1
                counted = True
                if type(candidates) is not tuple or len(candidates) > 4:
                    raise ValueError("Model proposals must be a tuple of at most four tactic lines.")
                if candidates and type(before_calls) is int and type(after_calls) is int \
                        and after_calls == before_calls:
                    raise ValueError("Ignoring model-attributed tactics without an actual candidate-batch decode.")
                if type(before_calls) is not int or type(after_calls) is not int or after_calls > before_calls:
                    # The ledger carries no tactics. A later exact prompt hit
                    # only suppresses another decode; it never adds a proof edge.
                    model_advice_memory.remember_decoded(node.goals, counts["model_calls"])
                local_seen = set()
                for line in candidates:
                    if type(line) is str and line in local_seen:
                        continue
                    if type(line) is str:
                        local_seen.add(line)
                    proposal = _Proposal((line,), "model", "The trained model proposed this tactic.",
                        (("model_call", str(counts["model_calls"])),
                         ("model_advisor_call", str(counts["model_advisor_calls"]))))
                    child = apply_script(node, proposal)
                    if proved is not None:
                        return
                    if child is not None:
                        put(child)
            except (TimeoutError, MemoryError):
                raise
            except Exception as error:
                note("model_error", error, node)
            finally:
                if not counted:
                    after_calls = getattr(model_policy, "calls", None)
                    if type(before_calls) is int and type(after_calls) is int:
                        delta = after_calls - before_calls
                        if delta not in (0, 1):
                            raise RuntimeError("Model advisor escaped its one-decode-per-request bound.")
                        counts["model_calls"] += delta

    progress("symbolic", "Closing deterministic proof steps before requesting model or solver advice.", root)
    while (frontier or deferred) and proved is None and not expired():
        if counts["tactic_attempts"] >= limits.max_tactic_attempts:
            limited_reasons.add("max_tactic_attempts")
            break
        if deferred and (not frontier or since_advice >= limits.heuristic_burst):
            node = deferred.popleft()
            assist(node)
            since_advice = 0
            continue
        if counts["states_expanded"] >= limits.max_expansions:
            limited_reasons.add("max_expansions")
            for pending in continuations.values():
                polynomial_records[pending.plan_id]["status"] = "expansion_budget"
            continuations.clear()
            ring_failed_nodes.clear()
            frontier.clear()
            continue
        frontier_turn += 1
        if frontier_turn % limits.heuristic_burst == 0:
            node = frontier.pop(min(frontier))
        else:
            node = min(frontier.values(), key=priority)
            del frontier[node.id]
        counts["states_expanded"] += 1
        if node.id in strengthened_nodes:
            counts["strengthening_expansions"] += 1
        since_advice += 1
        pending = continuations.pop(node.id, None)
        newly_planned = False
        if pending is None and node.id in ring_failed_nodes:
            pending = start_decomposition(node)
            newly_planned = pending is not None
        if pending is not None:
            child = continue_decomposition(node, pending)
            if proved is not None:
                break
            if child is not None:
                if newly_planned:
                    # Retain the starting alternative while giving the finite
                    # checked continuation its normal best-first priority.
                    put(node)
                continue
        node, saturated = close(node)
        if proved is not None:
            break
        if not saturated:
            put(node)
            continue
        if node.depth >= limits.max_depth:
            limited_reasons.add("max_depth")
            continue
        for proposal in heuristic_candidates(node.state, max_candidates=limits.candidates_per_state,
                                             max_macro_steps=limits.max_macro_steps):
            child = apply_script(node, proposal)
            if proved is not None:
                break
            if child is not None:
                put(child)
            if expired() or counts["tactic_attempts"] >= limits.max_tactic_attempts:
                break
        can_advise = (model_policy is not None and counts["model_advisor_calls"] < limits.max_model_calls) or (
            vampire_advisor is not None and not stopped_vampire and
            counts["vampire_advisor_calls"] < limits.max_vampire_calls)
        if proved is None and can_advise and node.id not in deferred_ids:
            deferred.append(node)
            deferred_ids.add(node.id)
        if counts["states_expanded"] % 4 == 0:
            progress("symbolic", "Exploring checked tactic branches and retaining alternatives.", node)

    if model_policy is not None and counts["model_advisor_calls"] >= limits.max_model_calls:
        limited_reasons.add("max_model_calls")
    if vampire_advisor is not None and counts["vampire_advisor_calls"] >= limits.max_vampire_calls \
            and not stopped_vampire:
        limited_reasons.add("max_vampire_calls")
    winning, certificate_nodes, replay = proved if proved is not None else (None, None, None)
    partial_proof_cost = None
    if winning is None:
        measurement_started = time.monotonic()
        partial_proof_cost = measure_proof(best.state.partial, stage="partial", should_stop=expired)
        native_timing["measurement_seconds"] += time.monotonic() - measurement_started
    return {
        "status": "proof" if winning is not None else ("limit" if limited_reasons else "exhausted"),
        "theorem": canonical, "commands": [] if winning is None else list(winning.commands),
        "certificate_nodes": certificate_nodes, "replay": replay,
        "initial_goals": list(initial_goals), "kernel_checked": winning is not None,
        "model_used": counts["model_calls"] > 0, "vampire_used": counts["vampire_calls"] > 0,
        "profile": SEARCH_PROFILE, "limits": asdict(limits), "limited_by": sorted(limited_reasons),
        "proof_cost": {"final": final_proof_cost, "best_partial": partial_proof_cost,
            "scope": "Only the winning final certificate or the retained best partial proof; not peak search memory",
            "partial_is_not_final_prediction": True},
        "native_timing": {**{key: round(value, 6) for key, value in native_timing.items()},
            "scope": "Transition time includes prefix restoration and tactic checking; finalization includes compilation and kernel checking. Measurements are diagnostic overhead."},
        **counts, "model_repeated_prompts_skipped": model_advice_memory.hits,
        "model_advice_memory": model_advice_memory.report(),
        "polynomial_decomposition": {"policy": "hydra-native-polynomial-continuations-v2",
            **polynomial_counts, "max_planning_attempts": MAX_POLYNOMIAL_ATTEMPTS,
            "attempt_memory": decomposition_memory.report(),
            "max_planner_variants_per_attempt": 2,
            "max_generated_plans": MAX_POLYNOMIAL_PLANS, "max_commands_per_plan": MAX_POLYNOMIAL_COMMANDS,
            "max_script_bytes": MAX_POLYNOMIAL_SCRIPT_BYTES,
            "chunk_steps": min(8, limits.max_macro_steps), "plans": polynomial_records,
            "pending_continuations": len(continuations), "trusted_as_proof": False},
        "state_identity": alpha.report().to_dict(), "diagnostics": diagnostics,
        "branches": branches, "advisor_results": advisor_results,
        "provenance": [] if winning is None else list(winning.provenance),
        "best_partial": None if winning is not None else {
            "commands": list(best.commands), "goals": list(best.goals), "branch_id": best.id,
            "kernel_checked": False, "scope": "open native prefix; not a proved theorem"},
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "model_call_unit": "candidate-batch decodes from provider.calls; successful callback calls when counter absent",
        "complete_decision_procedure": False, "classical": False,
    }


__all__ = ["HybridLimits", "SEARCH_PROFILE", "heuristic_candidates", "search"]
