"""Cheap, untrusted algebra-plan ranking; no tactics or polynomial expansion.

Scores are heuristic units, not predicted proof objects, memory or seconds.
They describe AST size, syntactic compound repetition, distribution pressure
and command growth. Repeated syntax is not credited as checked proof sharing:
local schedulers may be expanded during native finalization. Every alternative
still needs native execution and final replay, including plans with low scores.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from peano_lab.kernel.formulas import Eq, Forall, parse_formula_with_names
from peano_lab.kernel.terms import Add, Mul, ParseError, Succ, Var, Zero


POLICY = "hydra-algebra-plan-cost-v1"
MAX_ALTERNATIVES = 8
_PRESSURE_CAP = 1_000_000


@dataclass(frozen=True, slots=True)
class AlgebraCostLimits:
    max_ast_nodes: int = 4096
    max_ast_depth: int = 112
    max_work: int = 32768
    max_commands: int = 156
    max_line_bytes: int = 512
    max_script_bytes: int = 64 * 1024
    max_obligations: int = 156
    max_obligation_bytes: int = 64 * 1024

    def __post_init__(self):
        for name, maximum in (("max_ast_nodes", 4096), ("max_ast_depth", 112),
                ("max_work", 32768), ("max_commands", 156), ("max_line_bytes", 512),
                ("max_script_bytes", 64 * 1024), ("max_obligations", 156),
                ("max_obligation_bytes", 64 * 1024)):
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= maximum:
                raise ValueError(name + " must be a positive integer at most " + str(maximum))


DEFAULT_LIMITS = AlgebraCostLimits()


class _Unavailable(ValueError):
    pass


class _Budget:
    def __init__(self, limits, should_stop):
        self.limits = limits
        self.should_stop = should_stop
        self.work = 0

    def tick(self):
        if self.should_stop is not None and self.work % 64 == 0 and self.should_stop():
            raise _Unavailable("caller_stop")
        if self.work >= self.limits.max_work:
            raise _Unavailable("work_limit")
        self.work += 1


def _children(node):
    kind = type(node)
    if kind is Var:
        if type(node.index) is not int or not 0 <= node.index < 64:
            raise _Unavailable("variable_index")
        return ()
    if kind is Zero:
        return ()
    if kind is Succ:
        children = (node.term,)
    elif kind in (Add, Mul, Eq):
        children = (node.left, node.right)
    elif kind is Forall:
        if type(node.body) not in (Eq, Forall):
            raise _Unavailable("non_equational_obligation")
        return (node.body,)
    else:
        raise _Unavailable("unsupported_ast")
    if any(type(child) not in (Var, Zero, Succ, Add, Mul) for child in children):
        raise _Unavailable("non_rigid_term")
    return children


def _shape(equation, budget):
    if type(equation) not in (Eq, Forall):
        raise _Unavailable("non_equational_obligation")
    # This deliberately unfolds only up to max_ast_nodes occurrences. Unlike
    # proof observations, these small proposal ASTs do not justify a 100K memo.
    pending, results, active = [(equation, False, 1, ())], [], set()
    intern, frequencies, compounds = {}, {}, set()
    visited = maximum_depth = 0
    pressure_saturated = False
    while pending:
        budget.tick()
        node, leaving, depth, children = pending.pop()
        kind = type(node)
        if not leaving:
            visited += 1
            if visited > budget.limits.max_ast_nodes:
                raise _Unavailable("ast_node_limit")
            if depth > budget.limits.max_ast_depth:
                raise _Unavailable("ast_depth_limit")
            if id(node) in active:
                raise _Unavailable("ast_cycle")
            maximum_depth = max(maximum_depth, depth)
            children = _children(node)
            active.add(id(node))
            pending.append((node, True, depth, children))
            pending.extend((child, False, depth + 1, ()) for child in reversed(children))
            continue
        values = results[-len(children):] if children else []
        if children:
            del results[-len(children):]
        # A flat structural key avoids recursive dataclass hashing and also
        # recognizes equal compound syntax constructed as different objects.
        key = (kind.__name__, node.index) if kind is Var else (kind.__name__, *(v[0] for v in values))
        syntax = intern.setdefault(key, len(intern))
        frequencies[syntax] = frequencies.get(syntax, 0) + 1
        constant = False
        zero = False
        if kind is Zero:
            constant, zero, degree, pressure = True, True, 0, 0
        elif kind is Var:
            degree, pressure = 1, 1
        elif kind is Succ:
            constant, degree = values[0][1], values[0][3]
            pressure = 1 if constant else values[0][4] + 1
        elif kind in (Add, Mul):
            constant = all(v[1] for v in values)
            zero = all(v[2] for v in values) if kind is Add else any(v[2] for v in values)
            constant = constant or zero
            degree = (max(v[3] for v in values) if kind is Add else sum(v[3] for v in values))
            pressure = (sum(v[4] for v in values) if kind is Add else values[0][4] * values[1][4])
            if constant:
                degree, pressure = 0, int(not zero)
        else:
            degree = max(v[3] for v in values)
            pressure = sum(v[4] for v in values)
        if pressure > _PRESSURE_CAP:
            pressure_saturated = True
            pressure = _PRESSURE_CAP
        if kind in (Add, Mul, Succ) and not constant:
            compounds.add(syntax)
        results.append((syntax, constant, zero, degree, pressure))
        active.remove(id(node))
    result = results[0]
    return {"ast_occurrences": visited, "unique_syntax_nodes": len(intern),
            "depth": maximum_depth, "degree_bound": result[3],
            "repeated_compound_occurrences": sum(frequencies[key] - 1 for key in compounds),
            "distribution_pressure": result[4], "distribution_pressure_saturated": pressure_saturated}


def _obligation(value, budget):
    if type(value) in (Eq, Forall):
        return value, 0
    if type(value) is dict:
        value = value.get("theorem")  # Current ChunkPlan.obligations format.
    if type(value) is not str or not value or len(value) > budget.limits.max_line_bytes:
        raise _Unavailable("obligation_text")
    size = len(value.encode("utf-8"))
    if size > budget.limits.max_line_bytes:
        raise _Unavailable("obligation_text")
    # Cheap guards before the native *parser*, never a tactic or checker.
    # Decline elaborate text instead of trying to interpret arbitrary scripts.
    if value.count("=") != 1 or any(token in value for token in
            ("->", "→", "/\\", "\\/", "∧", "∨", "¬", "∃", "exists", "\x00", "\n", "\r")):
        raise _Unavailable("obligation_fragment")
    nesting = 0
    for character in value:
        if character == "(":
            nesting += 1
        elif character == ")":
            nesting -= 1
        if not 0 <= nesting <= 48:
            raise _Unavailable("obligation_nesting")
    if nesting or value.count("forall") + value.count("∀") > 32:
        raise _Unavailable("obligation_nesting")
    if any(len(match.group()) > 8 for match in re.finditer(r"(?<![\w'])\d+", value)):
        raise _Unavailable("obligation_numeral")
    budget.tick()
    parsed, _ = parse_formula_with_names(value)
    return parsed, size


def estimate_algebra_plan(equation, commands, *, obligations=(), limits=DEFAULT_LIMITS, should_stop=None):
    """Estimate a plan using its source Eq, command lines and optional ring goals.

    ``obligations`` accepts Eq/Forall ASTs, bounded theorem strings, or the
    dictionaries already emitted by ChunkPlan. When supplied, their number
    must match the plan's ``ring`` commands. Without them, the source equation
    is only a proxy for every ring invocation; no intermediate state is guessed.
    Unsupported/truncated inputs leave score=None so callers can retain their
    existing plan. Process resource errors (for example MemoryError) propagate.
    """
    if type(limits) is not AlgebraCostLimits:
        raise TypeError("limits must be AlgebraCostLimits")
    if should_stop is not None and not callable(should_stop):
        raise TypeError("should_stop must be callable")
    budget = _Budget(limits, should_stop)
    base = {"policy": POLICY, "kind": "heuristic_algebra_plan_cost", "score": None,
            "score_unit": "heuristic units; not proof objects, bytes of memory or seconds",
            "tactics_executed": 0, "proof_check_performed": False,
            "fallback_must_be_retained": True}
    try:
        budget.tick()
        if type(equation) is not Eq:
            raise _Unavailable("source_is_not_equality")
        if type(commands) not in (tuple, list) or not 1 <= len(commands) <= limits.max_commands:
            raise _Unavailable("command_count")
        if type(obligations) not in (tuple, list) or len(obligations) > limits.max_obligations:
            raise _Unavailable("obligation_count")
        script_bytes = rings = bindings = 0
        for command in commands:
            budget.tick()
            if type(command) is not str or len(command) > limits.max_line_bytes or not command.strip():
                raise _Unavailable("command_line")
            if any(character in command for character in ("\n", "\r", "\x00")):
                raise _Unavailable("command_line")
            size = len(command.encode("utf-8"))
            if size > limits.max_line_bytes:
                raise _Unavailable("command_line")
            script_bytes += size + 1
            if script_bytes > limits.max_script_bytes:
                raise _Unavailable("script_bytes")
            name = command.split(None, 1)[0]
            rings += name == "ring"
            bindings += name in ("have", "suffices")
        if obligations and len(obligations) != rings:
            raise _Unavailable("ring_obligation_count")
        source = _shape(equation, budget)
        goals, text_bytes = [], 0
        for value in obligations:
            budget.tick()
            target, size = _obligation(value, budget)
            text_bytes += size
            if text_bytes > limits.max_obligation_bytes:
                raise _Unavailable("obligation_bytes")
            goals.append(_shape(target, budget))
        basis = "declared_ring_obligations" if goals else "source_proxy"
        if not goals:
            goals = [source] * rings
        shape_score = sum(2 * goal["ast_occurrences"] + goal["unique_syntax_nodes"]
                          + goal["depth"] ** 2 + 4 * goal["distribution_pressure"]
                          + 2 * goal["repeated_compound_occurrences"] for goal in goals)
        # With no ring call, retain a small source-size term; we cannot observe
        # the proof a refl/rewrite/congruence command will actually construct.
        if not goals:
            shape_score = source["ast_occurrences"]
        growth = len(commands) - 1
        command_score = 8 * growth + (script_bytes + 63) // 64 + 16 * bindings
        return {**base, "status": "estimated", "reason": None,
                "score": shape_score + command_score, "source_ast": source,
                "ring_goal_basis": basis, "ring_obligations": goals,
                "components": {"shape_score": shape_score, "command_growth_score": command_score,
                    "commands": len(commands), "command_growth": growth,
                    "script_bytes": script_bytes, "ring_commands": rings,
                    "local_bindings": bindings}, "work_units": budget.work}
    except (_Unavailable, ParseError, UnicodeError, RecursionError, AttributeError) as error:
        reason = str(error) if type(error) is _Unavailable else "malformed_obligation"
        return {**base, "status": "cancelled" if reason == "caller_stop" else "unavailable",
                "reason": reason, "work_units": budget.work}


def rank_plan_indices(estimates, *, fallback_index):
    """Return every input index exactly once, retaining the specified fallback.

    With complete estimates, scores sort first and ties keep input order. If
    any estimate is unavailable, keep the existing fallback first and every
    other candidate in its original order. This helper never prunes, selects
    a proof, or turns estimation failure into a rejected branch.
    """
    if type(estimates) not in (tuple, list) or not 1 <= len(estimates) <= MAX_ALTERNATIVES:
        raise ValueError("ranking needs 1..8 materialized estimates")
    if type(fallback_index) is not int or not 0 <= fallback_index < len(estimates):
        raise ValueError("fallback_index must identify an existing alternative")

    scores = []
    for index in range(len(estimates)):
        value = estimates[index]
        if (type(value) is dict and value.get("policy") == POLICY and value.get("status") == "estimated"
                and type(value.get("score")) is int and 0 <= value["score"] <= 10**12):
            scores.append(value["score"])
        else:
            return (fallback_index, *(index for index in range(len(estimates)) if index != fallback_index))

    return tuple(sorted(range(len(estimates)), key=lambda index: (scores[index], index)))


__all__ = ["POLICY", "AlgebraCostLimits", "DEFAULT_LIMITS", "estimate_algebra_plan", "rank_plan_indices"]
