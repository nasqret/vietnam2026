"""Binder-free egg explanations reconstructed by ordinary native tactics.

Only the named unconditional natural-semiring rules below are understood.
Every rule instance and unchanged congruence context is checked as bounded
data before proposing trans/congr/ring/refl. No e-graph equality closes a goal.
"""
from dataclasses import dataclass
import re

from adviser_protocol import ProtocolError, checked_response, prepare_request
from p9_bridge_common import P9Advisor


RULE_SET = "peano-semiring-1"
MAX_TERM_NODES = 256
MAX_TERM_DEPTH = 32
MAX_STEPS = 16
RULES = {
    "add-zero": ("(+ ?a z)", "?a"),
    "zero-add": ("(+ z ?a)", "?a"),
    "mul-zero": ("(* ?a z)", "z"),
    "zero-mul": ("(* z ?a)", "z"),
    "mul-one": ("(* ?a (s z))", "?a"),
    "one-mul": ("(* (s z) ?a)", "?a"),
    "add-comm": ("(+ ?a ?b)", "(+ ?b ?a)"),
    "mul-comm": ("(* ?a ?b)", "(* ?b ?a)"),
    "add-assoc": ("(+ (+ ?a ?b) ?c)", "(+ ?a (+ ?b ?c))"),
    "mul-assoc": ("(* (* ?a ?b) ?c)", "(* ?a (* ?b ?c))"),
    "distrib-left": ("(* ?a (+ ?b ?c))", "(+ (* ?a ?b) (* ?a ?c))"),
    "distrib-right": ("(* (+ ?a ?b) ?c)", "(+ (* ?a ?c) (* ?b ?c))"),
    "factor-left": ("(+ (* ?a ?b) (* ?a ?c))", "(* ?a (+ ?b ?c))"),
    "factor-right": ("(+ (* ?a ?c) (* ?b ?c))", "(* (+ ?a ?b) ?c)"),
    "succ-add-one": ("(s ?a)", "(+ ?a (s z))"),
    "add-succ": ("(+ ?a (s ?b))", "(s (+ ?a ?b))"),
    "mul-succ": ("(* ?a (s ?b))", "(+ (* ?a ?b) ?a)"),
}


def _require(condition, message):
    if not condition:
        raise ProtocolError(message)


def parse_term(value, variables, *, pattern=False):
    _require(type(value) is str and 0 < len(value) <= 8192, "Oversized egg term string.")
    tokens = re.findall(r"\(|\)|[^\s()]+", value)
    _require(len(tokens) <= 4 * MAX_TERM_NODES, "Egg term token count exceeds its bound.")
    cursor = nodes = 0

    def take(depth):
        nonlocal cursor, nodes
        nodes += 1
        _require(nodes <= MAX_TERM_NODES and depth <= MAX_TERM_DEPTH and cursor < len(tokens),
                 "Incomplete or oversized egg term.")
        token = tokens[cursor]
        cursor += 1
        if token == "(":
            _require(cursor < len(tokens) and tokens[cursor] in {"s", "+", "*"}, "Unsupported egg operator.")
            operator = tokens[cursor]
            cursor += 1
            children = tuple(take(depth + 1) for _ in range(1 if operator == "s" else 2))
            _require(cursor < len(tokens) and tokens[cursor] == ")", "Wrong egg term arity.")
            cursor += 1
            return (operator,) + children
        _require(token == "z" or (re.fullmatch(r"v[0-3]", token) is not None and int(token[1:]) < variables)
                 or (pattern and token in {"?a", "?b", "?c"}), "Unscoped or unsupported egg atom.")
        return (token,)

    result = take(0)
    _require(cursor == len(tokens), "Trailing tokens in egg term.")
    return result


def sexpr(term):
    return term[0] if len(term) == 1 else "(" + term[0] + " " + " ".join(sexpr(child) for child in term[1:]) + ")"


def _export_term(term, variables, counter, depth=0):
    from peano_lab.kernel import terms as t
    counter[0] += 1
    _require(counter[0] <= MAX_TERM_NODES and depth <= MAX_TERM_DEPTH, "Focused egg AST exceeds its bound.")
    if type(term) is t.Var:
        _require(type(term.index) is int and 0 <= term.index < variables, "Variable escaped the egg scope.")
        return (f"v{term.index}",)
    if type(term) is t.Zero:
        return ("z",)
    if type(term) is t.Succ:
        return ("s", _export_term(term.term, variables, counter, depth + 1))
    if type(term) in (t.Add, t.Mul):
        return ("+" if type(term) is t.Add else "*", _export_term(term.left, variables, counter, depth + 1),
                _export_term(term.right, variables, counter, depth + 1))
    raise ProtocolError("Egg accepts only rigid, binder-free native natural terms.")


@dataclass(frozen=True)
class EGraphProblem:
    left: tuple
    right: tuple
    variables: tuple[str, ...]

    @property
    def payload(self):
        return {"fragment": "hydra-egg-semiring-v1", "rule_set": RULE_SET,
                "lhs": sexpr(self.left), "rhs": sexpr(self.right), "variables": len(self.variables),
                "max_nodes": 4096, "max_iterations": 8}


def focus_problem(state):
    from peano_lab.engine.state import ProofState
    from peano_lab.kernel.formulas import Eq
    _require(type(state) is ProofState and state.goals, "Egg requires an open native state.")
    goal = state.current()
    _require(type(goal.target) is Eq and len(goal.variables) <= 4, "Egg requires a focused equality with at most four variables.")
    left = _export_term(goal.target.left, len(goal.variables), [0])
    right = _export_term(goal.target.right, len(goal.variables), [0])
    _require(left != right, "Reflexivity does not need an external e-graph request.")
    return EGraphProblem(left, right, tuple(goal.variables))


def _match(pattern, term, bindings):
    if pattern[0].startswith("?"):
        existing = bindings.setdefault(pattern[0], term)
        return existing == term
    return (pattern[0] == term[0] and len(pattern) == len(term)
            and all(_match(left, right, bindings) for left, right in zip(pattern[1:], term[1:])))


def _at(term, path):
    for index in path:
        _require(type(index) is int and 0 <= index < len(term) - 1, "Egg congruence path escaped its term.")
        term = term[index + 1]
    return term


def _replace(term, path, replacement):
    if not path:
        return replacement
    children = list(term)
    children[path[0] + 1] = _replace(children[path[0] + 1], path[1:], replacement)
    return tuple(children)


def _native_term(term, variables):
    if term[0] == "z":
        return "0"
    if term[0].startswith("v"):
        return variables[int(term[0][1:])]
    if term[0] == "s":
        return "S (" + _native_term(term[1], variables) + ")"
    return "(" + _native_term(term[1], variables) + " " + term[0] + " " + _native_term(term[2], variables) + ")"


def _congruence_commands(term, path):
    if not path:
        return ("ring",)
    inner = _congruence_commands(term[path[0] + 1], path[1:])
    if term[0] == "s":
        return ("congr",) + inner
    return ("congr",) + (inner + ("refl",) if path[0] == 0 else ("refl",) + inner)


def cost_estimate(term):
    """Advisory expansion estimate, never certificate objects or timing."""
    if len(term) == 1:
        return (1, 1, 0 if term[0] == "z" else 1)
    children = [cost_estimate(child) for child in term[1:]]
    nodes = 1 + sum(child[1] for child in children)
    if term[0] == "s":
        monomials = min(256, children[0][2] + 1)
        work = children[0][0] + 2 * monomials + 4
    elif term[0] == "+":
        monomials = min(256, sum(child[2] for child in children))
        work = sum(child[0] for child in children) + monomials + 4
    else:
        monomials = min(256, children[0][2] * children[1][2])
        work = sum(child[0] for child in children) + 8 * monomials + 4
    return (min(10**9, work), nodes, monomials)


def reconstruct(problem, evidence):
    _require(type(evidence) is dict and evidence.get("schema") == "hydra-egg-explanation-v1"
             and evidence.get("rule_set") == RULE_SET, "Wrong egg explanation schema/rules.")
    steps = evidence.get("steps")
    _require(type(steps) is list and 0 < len(steps) <= MAX_STEPS, "Egg explanation exceeds sixteen rewrites.")
    current, validated = problem.left, []
    for record in steps:
        _require(type(record) is dict and set(record) == {"before", "after", "rule", "direction", "path"},
                 "Malformed named egg rewrite.")
        before, after = (parse_term(record[name], len(problem.variables)) for name in ("before", "after"))
        path, name, direction = record["path"], record["rule"], record["direction"]
        _require(before == current and before != after and name in RULES
                 and direction in {"forward", "backward"} and type(path) is list and len(path) <= MAX_TERM_DEPTH,
                 "Unknown, discontinuous or unbounded egg explanation.")
        old, new = _at(before, path), _at(after, path)
        first, second = RULES[name] if direction == "forward" else tuple(reversed(RULES[name]))
        bindings = {}
        _require(_match(parse_term(first, 4, pattern=True), old, bindings)
                 and _match(parse_term(second, 4, pattern=True), new, bindings)
                 and _replace(before, path, new) == after,
                 "Egg step is not one exact named semiring instance under unchanged congruence.")
        validated.append((before, after, tuple(path), name, direction))
        current = after
    _require(parse_term(evidence.get("end"), len(problem.variables)) == current, "Egg endpoint does not match its full explanation.")
    commands, used = [], []
    final = problem.left
    for before, after, path, name, direction in validated:
        next_commands = ("trans " + _native_term(after, problem.variables),) + _congruence_commands(before, path)
        close = after == problem.right
        if len(commands) + len(next_commands) + int(close) > 8 or any(len(line.encode("utf-8")) > 512 for line in next_commands):
            break
        commands.extend(next_commands)
        used.append({"rule": name, "direction": direction, "path": list(path)})
        final = after
        if close:
            commands.append("refl")
            break
    _require(commands and final != problem.left, "No bounded native congruence prefix can be reconstructed.")
    return {"commands": commands, "reason": "Replay named unconditional semiring rewrites through native trans/congr/ring.",
            "used_rewrites": used, "complete_explanation_reconstructed": len(used) == len(validated),
            "estimated_native_work_before": cost_estimate(problem.left)[0],
            "estimated_native_work_after": cost_estimate(final)[0],
            "cost_kind": "bounded AST polynomial-expansion estimate; not actual proof nodes"}


class EGraphAdvisor(P9Advisor):
    def __init__(self, session, runner, *, capabilities, authority_identity):
        super().__init__("egg", session, runner, capabilities=capabilities, authority_identity=authority_identity)

    def prepare(self, state, context):
        problem = focus_problem(state)
        return problem, prepare_request("egg", problem.payload, context, self.runner.identity)

    def decode(self, problem, request, execution):
        response = checked_response(request, execution)
        status = response.get("status")
        if status in {"no_candidate", "resource_limit"}:
            return status, [], {"reason": str(response.get("reason", "No bounded rewrite."))[:120],
                                "proof_checked": False}
        _require(status == "candidate", "Unknown egg response status.")
        evidence = response.get("evidence")
        _require(type(evidence) is dict and type(evidence.get("graph_nodes")) is int
                 and 0 < evidence["graph_nodes"] <= 4096 and type(evidence.get("iterations")) is int
                 and 0 <= evidence["iterations"] <= 8, "Egg graph or iteration bound was exceeded.")
        suggestion = reconstruct(problem, evidence)
        return "no_candidate", [suggestion], {"rule_set": RULE_SET, "graph_nodes": evidence["graph_nodes"],
            "iterations": evidence["iterations"], "explanation_steps": len(evidence["steps"]),
            "proof_checked": False, "native_reconstruction_required": True}
