"""A deliberately untrusted Vampire advisor for the native Peano proof search.

Only kernel ASTs are exported; no user text is interpreted as TPTP.  Vampire
uses classical first-order logic and its proof is NOT a Peano certificate.
We inspect the actual refutation dependency graph to prioritize a small set
of native tactic macros.  Every suggested step, and the final original
theorem, still require the native engine and independent kernel replay.

This module never starts a process.  Its runner is injected by the HTTP
owner's bounded, offline, single-process Vampire supervisor.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Callable

from vampire_limits import RUNTIME_POLICY, classify_termination, solver_args, solver_limits


MAX_INPUT_BYTES = 64 * 1024
MAX_OUTPUT_BYTES = 256 * 1024
MAX_AST_NODES = 4096
MAX_AST_DEPTH = 112
MAX_CONTEXT = 64
MAX_PROOF_RECORDS = 1024
MAX_CANDIDATES = 24
MAX_MACRO_STEPS = 4
PA_AXIOMS = ("PA1", "PA2", "PA3", "PA4", "PA5", "PA6")
TRUST = "Vampire output is advisory; only a native Peano certificate can close the theorem."


class UnsupportedFragment(ValueError):
    pass


class UnsupportedProof(ValueError):
    pass


@dataclass(frozen=True)
class Premise:
    tptp_name: str
    native_name: str
    formula: object
    kind: str


@dataclass(frozen=True)
class ExportedProblem:
    text: str
    sha256: str
    premises: tuple[Premise, ...]
    target: object
    variables: tuple[str, ...]
    goal_count: int


class _Exporter:
    def __init__(self, variables: tuple[str, ...]):
        from peano_lab.kernel import formulas as f, terms as t
        self.f, self.t = f, t
        self.variables = variables
        self.nodes = 0
        self.next_binder = 0

    def _tick(self, depth: int) -> None:
        self.nodes += 1
        if self.nodes > MAX_AST_NODES or depth > MAX_AST_DEPTH:
            raise UnsupportedFragment("The focused AST exceeds the bounded Vampire export size.")

    def term(self, value, binders: tuple[str, ...], depth: int) -> str:
        self._tick(depth)
        t = self.t
        if type(value) is t.Var:
            index = value.index
            if type(index) is not int or index < 0:
                raise UnsupportedFragment("Malformed native variable index.")
            if index < len(binders):
                return binders[index]
            index -= len(binders)
            if index >= len(self.variables):
                raise UnsupportedFragment("A native variable escaped its focused scope.")
            # Introduced eigenvariables are rigid constants, never implicitly
            # generalized independently in each hypothesis.
            return f"hydra_c{index}"
        if type(value) is t.Zero:
            return "hydra_zero"
        if type(value) is t.Succ:
            return f"hydra_s({self.term(value.term, binders, depth + 1)})"
        if type(value) in (t.Add, t.Mul):
            function = "hydra_add" if type(value) is t.Add else "hydra_mul"
            return f"{function}({self.term(value.left, binders, depth + 1)},{self.term(value.right, binders, depth + 1)})"
        raise UnsupportedFragment("Unresolved metavariables and non-kernel terms are not exported to Vampire.")

    def formula(self, value, binders: tuple[str, ...] = (), depth: int = 0) -> str:
        self._tick(depth)
        f = self.f
        if type(value) is f.Eq:
            return f"({self.term(value.left, binders, depth + 1)} = {self.term(value.right, binders, depth + 1)})"
        if type(value) is f.Bot:
            return "$false"
        if type(value) in (f.Imp, f.And, f.Or):
            operator = {f.Imp: "=>", f.And: "&", f.Or: "|"}[type(value)]
            return f"({self.formula(value.left, binders, depth + 1)} {operator} {self.formula(value.right, binders, depth + 1)})"
        if type(value) in (f.Forall, f.Exists):
            name = f"V{self.next_binder}"
            self.next_binder += 1
            quantifier = "!" if type(value) is f.Forall else "?"
            return f"({quantifier} [{name}] : {self.formula(value.body, (name,) + binders, depth + 1)})"
        raise UnsupportedFragment("Only native first-order Peano formulas can be exported.")


def export_state(state) -> ExportedProblem:
    """Encode the focused sequent plus the six exact kernel PA axioms.

    Addition/multiplication are uninterpreted functions constrained by those
    axioms.  No integer theory, induction schema, or extra library is assumed.
    """
    from peano_lab.engine.state import ProofState, apply_formula_subst
    from peano_lab.kernel.checker import axiom_formula
    if type(state) is not ProofState or not state.goals:
        raise UnsupportedFragment("Vampire needs a non-empty native proof state.")
    goal = state.current()
    if len(goal.context) > MAX_CONTEXT or len(goal.variables) > 32:
        raise UnsupportedFragment("The focused context exceeds the bounded Vampire export size.")
    exporter = _Exporter(goal.variables)
    premises = []
    rows = ["% Hydra focused sequent: advisory classical FOF only; no induction schema."]
    for index, (name, original) in enumerate(goal.context):
        formula = apply_formula_subst(original, state.subst)
        encoded = f"hydra_h{index}"
        rows.append(f"fof({encoded},hypothesis,{exporter.formula(formula)}).")
        premises.append(Premise(encoded, name, formula, "hypothesis"))
    for name in PA_AXIOMS:
        formula = axiom_formula(name)
        if formula is None:
            raise UnsupportedFragment("A pinned Peano axiom is unavailable.")
        encoded = f"hydra_{name.lower()}"
        rows.append(f"fof({encoded},axiom,{exporter.formula(formula)}).")
        premises.append(Premise(encoded, name, formula, "kernel_axiom"))
    target = apply_formula_subst(goal.target, state.subst)
    rows.append(f"fof(hydra_goal,conjecture,{exporter.formula(target)}).")
    text = "\n".join(rows) + "\n"
    raw = text.encode("utf-8")
    if len(raw) > MAX_INPUT_BYTES:
        raise UnsupportedFragment("The exported Vampire problem exceeds 64 KiB.")
    return ExportedProblem(text, hashlib.sha256(raw).hexdigest(), tuple(premises), target,
                           tuple(goal.variables), len(state.goals))


def _split_top(value: str, delimiter: str = ",") -> list[str]:
    """Split a bounded TSTP expression without executing or interpreting it."""
    result, start, stack = [], 0, []
    quote, escape = None, False
    for index, char in enumerate(value):
        if quote:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == quote:
                quote = None
            continue
        if char in "'\"":
            quote = char
        elif char in "([":
            stack.append(char)
            if len(stack) > 128:
                raise UnsupportedProof("TSTP nesting exceeds its limit.")
        elif char in ")]":
            if not stack or (stack.pop(), char) not in (("(", ")"), ("[", "]")):
                raise UnsupportedProof("Unbalanced TSTP expression.")
        elif char == delimiter and not stack:
            result.append(value[start:index].strip())
            start = index + 1
    if quote or stack:
        raise UnsupportedProof("Incomplete TSTP expression.")
    result.append(value[start:].strip())
    return result


def _name(value: str) -> str:
    value = value.strip()
    if re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*|[0-9]+", value):
        return value
    if len(value) >= 2 and value[0] == value[-1] == "'" and re.fullmatch(r"[A-Za-z_0-9]+", value[1:-1]):
        return value[1:-1]
    raise UnsupportedProof("Unsupported proof reference name.")


def _call(value: str) -> tuple[str, list[str]]:
    match = re.match(r"^([a-z][A-Za-z_0-9]*)\s*\(", value.strip())
    if not match or not value.rstrip().endswith(")"):
        raise UnsupportedProof("Unsupported TSTP source expression.")
    return match.group(1), _split_top(value.strip()[match.end():-1])


def _source(value: str, depth: int = 0) -> tuple[list[str], list[str]]:
    if depth > 64:
        raise UnsupportedProof("Nested proof source exceeds its limit.")
    try:
        return [_name(value)], []
    except UnsupportedProof:
        pass
    kind, args = _call(value)
    if kind == "file" and len(args) == 2:
        return [], [_name(args[1])]
    if kind in ("introduced", "theory"):
        return [], []
    if kind != "inference" or len(args) != 3 or not args[2].startswith("[") or not args[2].endswith("]"):
        raise UnsupportedProof("Unsupported TSTP inference source.")
    references, inputs = [], []
    parents = args[2][1:-1].strip()
    for parent in _split_top(parents) if parents else []:
        refs, files = _source(parent, depth + 1)
        references.extend(refs)
        inputs.extend(files)
    return references, inputs


def proof_used_inputs(stdout: str, allowed_inputs: set[str]) -> tuple[tuple[str, ...], int]:
    """Find only input assumptions reachable from the final false clause.

    This is dependency extraction, not proof checking.  Malformed, partial,
    cyclic, or unsupported output supplies no guidance to the search.
    """
    if len(stdout.encode("utf-8")) > MAX_OUTPUT_BYTES:
        raise UnsupportedProof("The Vampire proof exceeds the output limit.")
    begin = re.search(r"(?m)^%\s*SZS output start (?:Proof|Refutation)\b[^\n]*\n", stdout)
    end = re.search(r"(?m)^%\s*SZS output end (?:Proof|Refutation)\b", stdout)
    if not begin or not end or end.start() <= begin.end():
        raise UnsupportedProof("Vampire did not return a complete TSTP proof block.")
    block = stdout[begin.end():end.start()]
    # Generated names and formulas contain no percent signs.  Strip only
    # whole comment lines; a percent inside a quoted source is left intact.
    block = "\n".join(line for line in block.splitlines() if not line.lstrip().startswith("%"))
    statements = _split_top(block, ".")
    if statements[-1]:
        raise UnsupportedProof("The final TSTP statement is incomplete.")
    statements.pop()
    if not statements or len(statements) > MAX_PROOF_RECORDS:
        raise UnsupportedProof("The TSTP record count is outside its bound.")
    records = {}
    roots = []
    for statement in statements:
        kind, args = _call(statement)
        if kind not in ("fof", "cnf", "tff") or len(args) < 4:
            raise UnsupportedProof("Only sourced first-order proof records are supported.")
        label = _name(args[0])
        if label in records:
            raise UnsupportedProof("Duplicate TSTP record name.")
        records[label] = _source(args[3])
        if re.fullmatch(r"\(*\s*\$false\s*\)*", args[2]):
            roots.append(label)
    if not roots:
        raise UnsupportedProof("The TSTP block contains no final false clause.")
    used, visited, visiting = [], set(), set()

    def visit(label: str, depth: int = 0) -> None:
        if depth > 128 or label in visiting:
            raise UnsupportedProof("Cyclic or excessively deep proof dependency graph.")
        if label in visited:
            return
        if label not in records:
            raise UnsupportedProof("An inference parent is absent from the proof block.")
        visiting.add(label)
        references, inputs = records[label]
        for parent in references:
            visit(parent, depth + 1)
        for name in inputs:
            if name not in allowed_inputs:
                raise UnsupportedProof("The proof refers to an input that was not exported.")
            if name not in used:
                used.append(name)
        visiting.remove(label)
        visited.add(label)

    visit(roots[-1])
    return tuple(name for name in used if name != "hydra_goal"), len(visited)


def _native_hints(problem: ExportedProblem, used: tuple[str, ...], maximum: int) -> list[dict]:
    from peano_lab.kernel import formulas as f, terms as t
    from peano_lab.kernel.terms import pretty_term
    from peano_lab.engine.state import instantiate_formula
    available = {premise.tptp_name: premise for premise in problem.premises}
    premises = [available[name] for name in used if name in available]
    hypotheses = {premise.native_name for premise in problem.premises if premise.kind == "hypothesis"}
    suggestions, seen = [], set()

    def add(commands: tuple[str, ...], why: str, sources: list[str]) -> None:
        if commands in seen or len(suggestions) >= maximum or not 0 < len(commands) <= MAX_MACRO_STEPS:
            return
        if any(not line or len(line.encode("utf-8")) > 512 or "\n" in line or "\r" in line for line in commands):
            return
        seen.add(commands)
        suggestions.append({"commands": list(commands), "source": "vampire",
                            "reason": why, "assumptions": sources, "kernel_checked": False})

    # A refutation can use a negative fact even when the current target is an
    # unrelated equality.  Prioritize its constructive reconstruction before
    # ordinary equality suggestions consume the finite candidate budget.
    # Only inputs reached from the actual final false-clause DAG occur in
    # ``premises``; merely exporting PA1 never enables this shortcut.
    for premise in premises:
        name, conclusion = premise.native_name, premise.formula
        if premise.kind == "kernel_axiom" and name in hypotheses:
            continue
        while type(conclusion) is f.Forall:
            conclusion = conclusion.body
        antecedents = 0
        while type(conclusion) is f.Imp:
            antecedents += 1
            conclusion = conclusion.right
        if not antecedents or type(conclusion) is not f.Bot:
            continue
        prefix = () if type(problem.target) is f.Bot else ("exfalso",)
        add(prefix + (f"apply {name}", "assumption"),
            "Reconstruct contradiction from a proof-used negative input, then discharge a native premise.",
            [name])

    direct_equalities = [premise for premise in premises if type(premise.formula) is f.Eq
                         and premise.kind == "hypothesis"]
    # Chained rewrites are the fragment for which a small macro can materially
    # improve on isolated tactic ranking.  Native replay decides orientation
    # and whether every step actually remains applicable.
    if 2 <= len(direct_equalities) <= 3:
        for ordered in (direct_equalities, list(reversed(direct_equalities))):
            names = [item.native_name for item in ordered]
            add(tuple([f"rewrite {name}" for name in names] + ["refl"]),
                "Chain equalities used in the Vampire refutation, then try reflexivity.", names)
    for premise in premises:
        name, formula = premise.native_name, premise.formula
        if premise.kind == "kernel_axiom" and name in hypotheses:
            continue  # A visible local hypothesis shadows the PA tactic name.
        if formula == problem.target and premise.kind == "hypothesis":
            add((f"exact {name}",), "The proof-used hypothesis matches the current goal.", [name])
        if type(formula) is f.Eq and type(problem.target) is f.Eq and formula.left == problem.target.right and formula.right == problem.target.left:
            add(("symm", f"exact {name}"), "Use the proof-used equality in the opposite orientation.", [name])
        add((f"apply {name}",), "Try backward application of an input used in the Vampire refutation.", [name])
        if type(formula) is f.Eq or premise.kind == "kernel_axiom" and name in ("PA3", "PA4", "PA5", "PA6"):
            for reverse in (False, True):
                command = f"rewrite {'<- ' if reverse else ''}{name}"
                add((command, "refl"), "Try a proof-used equality orientation and native reflexivity.", [name])
                add((command,), "Expose the intermediate goal after a proof-used equality rewrite.", [name])
        if type(formula) in (f.And, f.Or, f.Exists) and premise.kind == "hypothesis":
            add((f"cases {name}",), "Decompose a hypothesis used in the external refutation.", [name])
        if type(formula) is f.Forall and premise.kind == "hypothesis":
            terms, known = [], set()

            def collect_term(term, depth=0):
                if depth > 16 or len(terms) >= 8:
                    return
                if type(term) not in (t.Var, t.Zero, t.Succ, t.Add, t.Mul):
                    return
                if term not in known:
                    text = pretty_term(term, list(problem.variables))
                    if len(text) <= 96 and "#" not in text:
                        terms.append((term, text))
                        known.add(term)
                if type(term) is t.Succ:
                    collect_term(term.term, depth + 1)
                elif type(term) in (t.Add, t.Mul):
                    collect_term(term.left, depth + 1)
                    collect_term(term.right, depth + 1)

            # Only free terms of an atomic focused goal are considered.  We
            # never lift a subterm out from under a binder to invent a witness.
            if type(problem.target) is f.Eq:
                collect_term(problem.target.left)
                collect_term(problem.target.right)
            instances = []
            goal_terms = {item[0] for item in terms}
            for term, text in terms:
                instance = instantiate_formula(formula.body, term)
                if type(instance) is not f.Eq:
                    continue
                if instance == problem.target:
                    priority = 0
                elif instance.left in goal_terms or instance.right in goal_terms:
                    priority = 1
                else:
                    continue
                instances.append((priority, text, instance))
            for _, text, instance in sorted(instances, key=lambda row: (row[0], len(row[1]))):
                prefix = (f"specialize {name} ({text})",)
                if instance == problem.target:
                    add(prefix + (f"exact {name}",), "Instantiate a proof-used universal hypothesis at a goal term.", [name])
                for reverse in (False, True):
                    add(prefix + (f"rewrite {'<- ' if reverse else ''}{name}", "refl"),
                        "Instantiate a proof-used universal equality and reconstruct a native rewrite.", [name])
    return suggestions


class VampireAdvisor:
    def __init__(self, runner: Callable[[str], dict] | None = None):
        self.runner = runner

    def __call__(self, state, *, max_candidates: int = 12) -> dict:
        return self.advise(state, max_candidates=max_candidates)

    def advise(self, state, *, max_candidates: int = 12) -> dict:
        if type(max_candidates) is not int or not 1 <= max_candidates <= MAX_CANDIDATES:
            raise ValueError("Vampire guidance is limited to 1–24 candidates.")
        result = {"status": "unavailable", "detail": TRUST, "candidates": (), "suggestions": [],
                  "solver": {"available": False, "invocations": 0, "szs_status": None},
                  "problem_sha256": None, "kernel_checked": False}
        if self.runner is None:
            result["detail"] = "No pinned local Vampire runner is available. " + TRUST
            return result
        try:
            problem = export_state(state)
        except UnsupportedFragment as error:
            result.update(status="unsupported_fragment", detail=str(error) + " " + TRUST)
            return result
        result.update(problem_sha256=problem.sha256, focused_goal_only=True,
                      goal_count=problem.goal_count, exported_axioms=list(PA_AXIOMS), induction_exported=False)
        # Exactly one call.  The owner must return invocation and actual exit
        # metadata after reaping the bounded process; no retry or fallback.
        run = self.runner(problem.text)
        if type(run) is not dict:
            raise ValueError("Vampire runner returned an invalid result.")
        invoked = run.get("executed", run.get("invoked"))
        if type(invoked) is not bool:
            raise ValueError("Vampire runner omitted actual invocation metadata.")
        if run.get("problem_sha256", problem.sha256) != problem.sha256:
            raise ValueError("Vampire runner result was bound to a different problem.")
        solver = {"available": run.get("available") is True, "invocations": int(invoked),
                  "exit_code": run.get("exit_code"), "szs_status": None,
                  "timed_out": run.get("timed_out") is True or run.get("status") == "timeout", "kernel_checked": False}
        for key in ("version", "elapsed_seconds", "stdout_bytes", "stderr_bytes", "binary_sha256",
                    "peak_sampled_rss_bytes", "rss_samples"):
            if key in run:
                solver[key] = run[key]
        if "profile" in run:
            profile = run["profile"]
            limits, arguments = solver_limits(profile), solver_args(profile)
            if (run.get("limits") != limits or run.get("solver_args") != arguments
                    or run.get("runtime_policy") != RUNTIME_POLICY):
                raise ValueError("Vampire runner profile metadata does not match the fixed runtime policy.")
            solver.update(profile=profile, limits=limits, solver_args=arguments, runtime_policy=RUNTIME_POLICY)
            smoke = run.get("package_smoke", {})
            ready_verified = type(smoke) is dict and smoke.get("profile") == "standard" and smoke.get("ready_record_verified") is True
            solver["package_smoke"] = {"profile": "standard", "ready_record_verified": ready_verified,
                                       "covers_selected_profile": ready_verified and profile == "standard"}
        result["solver"] = solver
        if not invoked:
            result.update(status="unavailable", detail="Vampire was not launched. " + TRUST)
            return result
        stdout, stderr = run.get("stdout", ""), run.get("stderr", "")
        if not isinstance(stdout, str) or not isinstance(stderr, str):
            raise ValueError("Vampire runner output must be bounded UTF-8 text.")
        if len(stdout.encode("utf-8")) + len(stderr.encode("utf-8")) > MAX_OUTPUT_BYTES:
            result.update(status="output_limit", detail="Vampire output exceeded its bound; no guidance accepted.")
            return result
        solver["stdout_sha256"] = hashlib.sha256(stdout.encode("utf-8")).hexdigest()
        observed = classify_termination(stdout, stderr, exit_code=solver["exit_code"],
                                        output_limited=run.get("output_limited") is True)
        solver.update(termination=observed["termination"], status=observed["status"],
                      resource_limited=observed["resource_limited"])
        statuses = re.findall(r"(?m)^%\s*SZS status ([A-Za-z]+)\b", stdout)
        if statuses and len(set(statuses)) == 1:
            solver["szs_status"] = statuses[0]
        if observed["status"] == "output_limit":
            result.update(status="output_limit", detail="Vampire output exceeded its bound; no guidance accepted.")
            return result
        if solver["timed_out"] and not observed["timed_out"]:
            # A watchdog can kill the helper before it emits a status line.
            reported = run.get("termination", {})
            solver["termination"]["reason"] = ("outer_wall_watchdog" if type(reported) is dict
                and reported.get("reason") == "outer_wall_watchdog" else "runner_reported_timeout")
        solver["timed_out"] = solver["timed_out"] or observed["timed_out"]
        if solver["timed_out"]:
            solver["status"] = "timeout"
            result.update(status="timeout", detail="The bounded Vampire attempt timed out. " + TRUST)
            return result
        if observed["resource_limited"] or run.get("status") == "resource_limit":
            solver.update(status="resource_limit", resource_limited=True)
            if not observed["resource_limited"]:
                reported = run.get("termination", {})
                solver["termination"]["reason"] = ("owned_child_rss_watchdog" if type(reported) is dict
                    and reported.get("reason") == "owned_child_rss_watchdog" else "runner_reported_resource_limit")
            result.update(status="resource_limit", detail="Vampire reported a resource limit. " + TRUST)
            return result
        if (observed["status"] == "failed" or run.get("status") == "failed"
                or type(solver["exit_code"]) is not int or solver["exit_code"] != 0):
            solver["status"] = "failed"
            if observed["status"] != "failed":
                solver["termination"]["reason"] = "runner_reported_error"
            result.update(status="solver_error", detail="Vampire did not return a usable successful result. " + TRUST)
            return result
        if solver["szs_status"] not in {"Theorem", "ContradictoryAxioms"}:
            result.update(status="no_refutation", detail="Vampire supplied no supported refutation. " + TRUST)
            return result
        try:
            used, proof_nodes = proof_used_inputs(stdout, {item.tptp_name for item in problem.premises} | {"hydra_goal"})
        except UnsupportedProof as error:
            result.update(status="unsupported_proof", detail=str(error) + " " + TRUST)
            return result
        suggestions = _native_hints(problem, used, max_candidates)
        contradictory = solver["szs_status"] == "ContradictoryAxioms"
        solver.update(reachable_proof_records=proof_nodes, proof_used_inputs=list(used),
                      advisory_refutation=True, advisory_theorem=not contradictory)
        detail = ("Vampire reported contradictory exported premises; try native contradiction reconstruction. "
                  if contradictory else "Vampire supplied a classical refutation; try native reconstruction from its used inputs. ")
        result.update(status="advisory_contradiction" if contradictory else "advisory_theorem",
                      candidates=tuple(tuple(item["commands"]) for item in suggestions),
                      suggestions=suggestions, detail=detail + TRUST)
        return result
