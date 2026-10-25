"""Bounded, untrusted proof plans compiled to ordinary native commands.

Nothing here runs a tactic, checks a certificate, imports a theorem, or calls a
model. Compilation validates structure, finite authority, names and budgets;
it does not promise that a command will succeed. The host must execute every
edge transactionally, retain every native goal, and independently replay QED.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
import re
from types import MappingProxyType
from typing import Mapping

from peano_lab.engine.state import Goal, MetaVar
from peano_lab.engine.trace import render_goals
from peano_lab.kernel.formulas import (
    And, Bot, Eq, Exists, Forall, Formula, Imp, Or,
    parse_formula_in_context, pretty_formula,
)
from peano_lab.kernel.terms import (
    Add, Mul, Succ, Term, Var, Zero, parse_term_in_context, pretty_term,
)


PLAN_VERSION = "hydra-structured-proof-plan-v1"
MAX_COMMANDS = 32
MAX_PLAN_BYTES = 16384
MAX_AST_NODES = 4096
MAX_CHUNK_COMMANDS = 8
MAX_ACTIONS = 32
MAX_COMPILE_WORK = 131072
MAX_DEPTH = 64
MAX_INPUT_AST_NODES = 32768
MAX_INPUT_BYTES = 131072
MAX_PROPOSALS = 2
_RESERVED = frozenset(("S", "forall", "exists", "bot", "false"))
_NO_ARGUMENT = frozenset(("refl", "assumption", "split", "left", "right",
                          "symm", "congr", "exfalso", "simp", "ring", "compact_arith"))
_NAMED = frozenset(("intro", "exact", "apply", "cases"))


class PlannerError(ValueError):
    """A proposal is invalid; it has no proof authority."""


class PlannerLimit(PlannerError):
    """A finite planning budget declined the proposal."""


class PlannerCancelled(PlannerLimit):
    pass


def _identifier(value):
    if (type(value) is not str or not value or len(value.encode("utf-8")) > 64
            or value in _RESERVED or not (value[0].isalpha() or value[0] == "_")
            or not all(c.isalnum() or c in "_'" for c in value[1:])):
        raise PlannerError("expected one bounded native identifier")
    return value


def _text(value, limit=4096):
    if (type(value) is not str or not value or not value.isprintable()
            or len(value.encode("utf-8")) > limit):
        raise PlannerError("expected bounded single-line text")
    return value


def _digest(value, *, allow_none=False):
    if allow_none and value == "none":
        return value
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise PlannerError("expected an exact lowercase SHA-256 identity")
    return value


def _metadata(value):
    if not isinstance(value, Mapping) or len(value) > 32:
        raise PlannerError("metadata must be a bounded flat mapping")
    result = {}
    for name, item in value.items():
        _text(name, 96)
        if type(item) not in (str, int, float, bool, type(None)):
            raise PlannerError("metadata values must be JSON scalars")
        if type(item) is str:
            _text(item, 512)
        if type(item) in (int, float) and (not -1e12 <= item <= 1e12):
            raise PlannerError("metadata number is not finite and bounded")
        result[name] = item
    return MappingProxyType(result)


@dataclass(frozen=True, slots=True)
class CapabilitySnapshot:
    label: str
    commands: tuple[str, ...]
    theorems: tuple[str, ...] = ()

    def __post_init__(self):
        _text(self.label, 160)
        for attr, maximum in (("commands", 64), ("theorems", 64)):
            values = getattr(self, attr)
            if type(values) not in (tuple, list, frozenset) or len(values) > maximum:
                raise PlannerError("planner capabilities must be finite")
            for value in values:
                _text(value, 96)
                if any(c.isspace() for c in value):
                    raise PlannerError("capability names must be individual tokens")
            object.__setattr__(self, attr, tuple(sorted(set(values))))

    @classmethod
    def from_native(cls, capabilities):
        return cls(capabilities.label, capabilities.allowed_commands, capabilities.allowed_theorems)

    def record(self):
        return {"label": self.label, "commands": list(self.commands), "theorems": list(self.theorems)}

    @property
    def identity(self):
        return sha256(_json(self.record()).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class LemmaCandidate:
    """Host-selected metadata only; actual `use` must recheck its certificate."""
    name: str
    formula: Formula
    certificate_sha256: str
    kernel_identity: str
    library_identity: str
    cost: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self):
        _text(self.name, 96)
        if any(c.isspace() for c in self.name):
            raise PlannerError("lemma name must be one capability token")
        _digest(self.certificate_sha256)
        _digest(self.kernel_identity)
        _digest(self.library_identity)
        object.__setattr__(self, "cost", _metadata(self.cost))


@dataclass(frozen=True, slots=True)
class PlannerContext:
    original_target: Formula
    original_variables: tuple[str, ...]
    goals: tuple[Goal, ...]
    capabilities: CapabilitySnapshot
    kernel_identity: str
    library_identity: str = "none"
    lemmas: tuple[LemmaCandidate, ...] = ()
    failures: tuple[str, ...] = ()
    remaining: Mapping[str, object] = field(default_factory=dict)
    certificate_cost: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self):
        for attr, maximum in (("original_variables", 64), ("goals", 64),
                              ("lemmas", 4), ("failures", 16)):
            value = getattr(self, attr)
            if type(value) not in (tuple, list) or len(value) > maximum:
                raise PlannerLimit("planner context exceeds its finite collection bound")
            object.__setattr__(self, attr, tuple(value))
        if type(self.capabilities) is not CapabilitySnapshot:
            raise PlannerError("planner needs an explicit finite capability snapshot")
        _digest(self.kernel_identity)
        _digest(self.library_identity, allow_none=True)
        for name in self.original_variables:
            _identifier(name)
        for failure in self.failures:
            _text(failure, 1024)
        object.__setattr__(self, "remaining", _metadata(self.remaining))
        object.__setattr__(self, "certificate_cost", _metadata(self.certificate_cost))


@dataclass(frozen=True, slots=True)
class InductionAction:
    variable: str
    generalize: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class GeneralizeAction:
    variables: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AuxiliaryAction:
    mode: str
    name: str
    statement: str


@dataclass(frozen=True, slots=True)
class WitnessTemplate:
    expression: str
    bindings: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class WitnessAction:
    template: WitnessTemplate


@dataclass(frozen=True, slots=True)
class InstantiateAction:
    lemma: str
    terms: tuple[str, ...] = ()
    alias: str | None = None
    finish: str = "none"


@dataclass(frozen=True, slots=True)
class StepAction:
    tactic: str
    name: str | None = None
    term: str | None = None
    reverse: bool = False


@dataclass(frozen=True, slots=True)
class RouteAction:
    goal: int
    actions: tuple[object, ...]
    adviser_hint: str = "native"


@dataclass(frozen=True, slots=True)
class StrengthenAction:
    parameter: str | None = None
    max_auxiliaries: int = 2
    generalize_parameters: bool = True


@dataclass(frozen=True, slots=True)
class PlanSpec:
    actions: tuple[object, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class CompiledPlan:
    commands: tuple[str, ...]
    provenance: tuple[tuple[tuple[str, object], ...], ...]
    starting_goals: tuple[Goal, ...]
    reason: str
    source: str
    plan_sha256: str
    context_sha256: str
    capability_identity: str
    library_identity: str
    ast_nodes: int
    analysis_work: int
    introduces_open_obligations: bool
    backend_hints: tuple[tuple[int, str], ...] = ()

    def chunks(self, maximum=MAX_CHUNK_COMMANDS):
        if type(maximum) is not int or not 1 <= maximum <= MAX_CHUNK_COMMANDS:
            raise PlannerLimit("native execution chunks must contain 1..8 commands")
        return tuple(self.commands[index:index + maximum] for index in range(0, len(self.commands), maximum))


class _Budget:
    def __init__(self, should_stop=None, *, max_nodes=MAX_AST_NODES):
        if should_stop is not None and not callable(should_stop):
            raise TypeError("should_stop must be callable or None")
        self.should_stop, self.work, self.ast_nodes, self.max_nodes = should_stop, 0, 0, max_nodes
        self.check()

    def check(self):
        if self.should_stop is not None and self.should_stop():
            raise PlannerCancelled("proof planning was cancelled")

    def tick(self, amount=1):
        previous = self.work
        self.work += amount
        if self.work > MAX_COMPILE_WORK:
            raise PlannerLimit("proof planner compilation work exceeded")
        if self.work // 64 != previous // 64:
            self.check()


def _scan(value, variables, budget, *, allow_meta=False):
    pending = [(value, 0, 0)]
    while pending:
        node, bound, depth = pending.pop()
        budget.tick()
        budget.ast_nodes += 1
        if budget.ast_nodes > budget.max_nodes or depth > MAX_DEPTH:
            raise PlannerLimit("proof planning AST bound exceeded")
        if type(node) is Var:
            if type(node.index) is not int or not 0 <= node.index < variables + bound:
                raise PlannerError("out-of-scope native variable in planner input")
        elif type(node) is MetaVar and allow_meta:
            if type(node.id) is not int or type(node.depth) is not int or min(node.id, node.depth) < 0:
                raise PlannerError("malformed native metavariable")
        elif type(node) in (Zero, Bot):
            continue
        elif type(node) is Succ:
            pending.append((node.term, bound, depth + 1))
        elif type(node) in (Add, Mul, Eq, And, Imp, Or):
            pending.extend(((node.left, bound, depth + 1), (node.right, bound, depth + 1)))
        elif type(node) in (Forall, Exists):
            pending.append((node.body, bound + 1, depth + 1))
        else:
            raise PlannerError("planner input is not supported native syntax")


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def context_record(context, *, should_stop=None):
    """Render all supplied goals and metadata, or reject the whole input."""
    if type(context) is not PlannerContext:
        raise PlannerError("expected a PlannerContext")
    budget = _Budget(should_stop, max_nodes=MAX_INPUT_AST_NODES)
    _scan(context.original_target, len(context.original_variables), budget)
    if len(set(context.original_variables)) != len(context.original_variables):
        raise PlannerError("original variable names must be unique")
    for goal in context.goals:
        if type(goal) is not Goal or len(goal.variables) > 64 or len(goal.context) > 128:
            raise PlannerError("expected a bounded exact native goal")
        if any(type(entry) is not tuple or len(entry) != 2 for entry in goal.context):
            raise PlannerError("native context entries must be name/formula pairs")
        names = tuple(goal.variables) + tuple(name for name, _ in goal.context)
        for name in names:
            _identifier(name)
        if len(set(names)) != len(names):
            raise PlannerError("native goal names must be unambiguous")
        _scan(goal.target, len(goal.variables), budget, allow_meta=True)
        for _, formula in goal.context:
            _scan(formula, len(goal.variables), budget, allow_meta=True)
    lemmas, seen = [], set()
    for lemma in context.lemmas:
        if (type(lemma) is not LemmaCandidate or lemma.name in seen
                or lemma.name not in context.capabilities.theorems
                or lemma.library_identity != context.library_identity
                or lemma.kernel_identity != context.kernel_identity):
            raise PlannerError("selected lemma identity or authority does not match the context")
        seen.add(lemma.name)
        _scan(lemma.formula, 0, budget)
        lemmas.append({"name": lemma.name, "statement": pretty_formula(lemma.formula, []),
                       "certificate_sha256": lemma.certificate_sha256,
                       "kernel_identity": lemma.kernel_identity,
                       "library_identity": lemma.library_identity, "cost": dict(lemma.cost)})
    record = {
        "plan_contract": PLAN_VERSION,
        "original_goal": pretty_formula(context.original_target, list(context.original_variables)),
        "original_variables": list(context.original_variables),
        "goals": render_goals(context.goals),
        "capabilities": context.capabilities.record(),
        "capability_identity": context.capabilities.identity,
        "kernel_identity": context.kernel_identity, "library_identity": context.library_identity,
        "selected_lemmas": lemmas, "recent_failures": list(context.failures),
        "remaining_budget": dict(context.remaining), "certificate_cost": dict(context.certificate_cost),
    }
    encoded = _json(record).encode("utf-8")
    if len(encoded) > MAX_INPUT_BYTES:
        raise PlannerLimit("full planner context exceeds its byte bound; no goals were truncated")
    budget.tick(len(encoded))
    budget.check()
    return record


def _parse(source, variables, budget, *, formula=False):
    _text(source)
    for numeral in re.findall(r"(?<![\w'])\d+", source):
        if len(numeral) > 7 or int(numeral) > 1_000_000:
            raise PlannerLimit("planner numeral exceeds the native surface limit")
    budget.tick(len(source.encode("utf-8")))
    try:
        value = (parse_formula_in_context(source, list(variables)) if formula
                 else parse_term_in_context(source, list(variables)))
    except (ValueError, TypeError, RecursionError) as error:
        raise PlannerError("invalid native formula or term in structured plan") from error
    _scan(value, len(variables), budget)
    return value


def _free_indices(formula, budget):
    found, pending = set(), [(formula, 0)]
    while pending:
        value, depth = pending.pop()
        budget.tick()
        if type(value) is MetaVar:
            raise PlannerError("generalization requires resolved native terms")
        if type(value) is Var and value.index >= depth:
            found.add(value.index - depth)
        elif type(value) is Succ:
            pending.append((value.term, depth))
        elif type(value) in (Eq, Add, Mul, And, Or, Imp):
            pending.extend(((value.left, depth), (value.right, depth)))
        elif type(value) in (Forall, Exists):
            pending.append((value.body, depth + 1))
    return found


def _quantify(formula, index, budget):
    def visit(value, depth):
        budget.tick()
        if type(value) is Var:
            return (value if value.index < depth else
                    Var(depth) if value.index - depth == index else Var(value.index + 1))
        if type(value) in (Zero, Bot):
            return value
        if type(value) is Succ:
            return Succ(visit(value.term, depth))
        if type(value) in (Eq, Add, Mul, And, Or, Imp):
            return type(value)(visit(value.left, depth), visit(value.right, depth))
        if type(value) in (Forall, Exists):
            return type(value)(visit(value.body, depth + 1))
        raise PlannerError("generalization requires resolved native syntax")
    return Forall(visit(formula, 0))


class _Compiler:
    def __init__(self, context, source, should_stop):
        self.context, self.source = context, source
        self.budget = _Budget(should_stop)
        self.goal = context.goals[0]
        self.variables = list(self.goal.variables)
        self.names = set(self.variables) | {name for name, _ in self.goal.context}
        self.commands, self.provenance, self.hints = [], [], []
        self.action_count = self.import_count = 0
        self.open_obligations = False

    def fresh(self, prefix):
        name, suffix = prefix, 1
        while name in self.names:
            self.budget.tick()
            name, suffix = prefix + str(suffix), suffix + 1
        self.names.add(name)
        return name

    def emit(self, command, action, **evidence):
        self.budget.tick(len(command.encode("utf-8")))
        _text(command, 8192)
        if any(c in command for c in ";\n\r"):
            raise PlannerError("compiled plans contain only individual native commands")
        if command.partition(" ")[0] not in self.context.capabilities.commands:
            raise PlannerError("a compiled command is outside the selected native authority")
        self.commands.append(command)
        self.provenance.append(tuple(sorted({"action": action, "source": self.source,
                                            "kernel_checked": False, **evidence}.items())))
        if (len(self.commands) > MAX_COMMANDS
                or sum(len(line.encode("utf-8")) + 1 for line in self.commands) > MAX_PLAN_BYTES):
            raise PlannerLimit("whole plan exceeds its command or byte bound")

    def generalize(self, variables):
        if self.commands:
            raise PlannerError("goal generalization must be the first plan action")
        if type(variables) not in (tuple, list) or not 1 <= len(variables) <= 4:
            raise PlannerError("generalization selects one to four original parameters")
        for name in variables:
            _identifier(name)
            if name not in self.goal.variables:
                raise PlannerError("generalization selected an unknown parameter")
        if len(set(variables)) != len(variables):
            raise PlannerError("generalized parameters must be distinct")
        indices = tuple(self.goal.variables.index(name) for name in variables)
        dependent = tuple((name, formula) for name, formula in self.goal.context
                          if set(indices) & _free_indices(formula, self.budget))
        proposition = self.goal.target
        for _, formula in reversed(dependent):
            proposition = Imp(formula, proposition)
        for index in reversed(indices):
            proposition = _quantify(proposition, index, self.budget)
        _scan(proposition, len(self.goal.variables), self.budget)
        name = self.fresh("hydra_generalized")
        self.emit(f"suffices {name} : {pretty_formula(proposition, list(self.goal.variables))}",
                  "generalize", generalized_parameters=",".join(variables), open_auxiliary=True)
        for variable in variables:
            self.emit(f"specialize {name} {variable}", "generalize_projection")
        self.emit(f"{'apply' if dependent else 'exact'} {name}", "generalize_projection")
        for hypothesis, _ in dependent:
            self.emit(f"exact {hypothesis}", "generalize_projection")
        self.open_obligations = True

    def compile(self, action, depth=0):
        self.budget.tick()
        self.budget.ast_nodes += 1
        self.action_count += 1
        if self.action_count > MAX_ACTIONS or depth > 4:
            raise PlannerLimit("structured action count or nesting exceeded")
        if type(action) is GeneralizeAction:
            self.generalize(action.variables)
        elif type(action) is InductionAction:
            _identifier(action.variable)
            if type(action.generalize) not in (tuple, list) or len(action.generalize) > 4:
                raise PlannerError("induction generalization must be a bounded parameter array")
            for name in action.generalize:
                _identifier(name)
            if action.variable not in self.variables or action.variable in action.generalize:
                raise PlannerError("induction needs one current, non-generalized parameter")
            if action.generalize:
                self.generalize(action.generalize)
            self.emit(f"induction {action.variable}", "induction")
            self.open_obligations = True
        elif type(action) is AuxiliaryAction:
            if action.mode not in ("have", "suffices"):
                raise PlannerError("auxiliary mode must be have or suffices")
            name = _identifier(action.name)
            if name in self.names:
                raise PlannerError("auxiliary name is not fresh")
            formula = _parse(action.statement, self.variables, self.budget, formula=True)
            self.names.add(name)
            self.emit(f"{action.mode} {name} : {pretty_formula(formula, self.variables)}",
                      "auxiliary", scheduling=action.mode, open_auxiliary=True)
            self.open_obligations = True
        elif type(action) is WitnessAction:
            template = action.template
            if type(template) is not WitnessTemplate or type(template.bindings) not in (tuple, list) or len(template.bindings) > 8:
                raise PlannerError("witness needs a bounded expression template")
            slots, terms = [], []
            for entry in template.bindings:
                if type(entry) not in (tuple, list) or len(entry) != 2:
                    raise PlannerError("witness binding must be a name/expression pair")
                name, expression = entry
                _identifier(name)
                if name in self.names or name in slots:
                    raise PlannerError("witness placeholder shadows a native name")
                slots.append(name)
                terms.append(_parse(expression, self.variables, self.budget))
            expression = _parse(template.expression, self.variables + slots, self.budget)
            def substitute(term):
                self.budget.tick()
                if type(term) is Var:
                    return term if term.index < len(self.variables) else terms[term.index - len(self.variables)]
                if type(term) is Zero:
                    return term
                if type(term) is Succ:
                    return Succ(substitute(term.term))
                return type(term)(substitute(term.left), substitute(term.right))
            expression = substitute(expression)
            _scan(expression, len(self.variables), self.budget)
            self.emit(f"exists {pretty_term(expression, self.variables)}", "witness")
        elif type(action) is InstantiateAction:
            matches = [lemma for lemma in self.context.lemmas if lemma.name == action.lemma]
            if len(matches) != 1 or action.lemma not in self.context.capabilities.theorems:
                raise PlannerError("lemma was not explicitly selected under this authority")
            if type(action.terms) not in (tuple, list) or len(action.terms) > 8:
                raise PlannerLimit("lemma instantiation has too many explicit terms")
            if action.finish not in ("none", "exact", "apply"):
                raise PlannerError("lemma finish must be none, exact or apply")
            lemma = matches[0]
            alias = self.fresh("hydra_import") if action.alias is None else _identifier(action.alias)
            if action.alias is not None:
                if alias in self.names:
                    raise PlannerError("lemma alias must be fresh")
                self.names.add(alias)
            formula = lemma.formula
            rendered = []
            for term in action.terms:
                if type(formula) is not Forall:
                    raise PlannerError("too many terms for the selected lemma's universal prefix")
                rendered.append(pretty_term(_parse(term, self.variables, self.budget), self.variables))
                formula = formula.body
            self.import_count += 1
            imports_remaining = self.context.remaining.get("imports", 8)
            if type(imports_remaining) is not int or not 0 <= self.import_count <= min(8, imports_remaining):
                raise PlannerLimit("plan exceeds the host's remaining checked-import allowance")
            self.emit(f"use {lemma.name} as {alias}", "instantiate",
                      lemma=lemma.name, certificate_sha256=lemma.certificate_sha256)
            for term in rendered:
                self.emit(f"specialize {alias} {term}", "instantiate", lemma=lemma.name)
            if action.finish != "none":
                self.emit(f"{action.finish} {alias}", "instantiate", lemma=lemma.name)
        elif type(action) is StepAction:
            _text(action.tactic, 64)
            if type(action.reverse) is not bool:
                raise PlannerError("rewrite orientation must be Boolean")
            if action.tactic in _NO_ARGUMENT:
                if action.name is not None or action.term is not None or action.reverse:
                    raise PlannerError("this native step takes no arguments")
                command = action.tactic
            elif action.tactic in _NAMED:
                name = _identifier(action.name)
                if action.term is not None or action.reverse:
                    raise PlannerError("this native step takes only a name")
                if action.tactic == "intro":
                    if name in self.names:
                        raise PlannerError("intro name must be fresh")
                    self.names.add(name)
                    # Declared names allow later typed expressions. This is a
                    # syntactic scope, never a claim the native intro succeeded.
                    self.variables.insert(0, name)
                command = f"{action.tactic} {name}"
            elif action.tactic == "rewrite":
                name = _identifier(action.name)
                if action.term is not None:
                    raise PlannerError("structured rewrite accepts only a named equation")
                command = f"rewrite {'<- ' if action.reverse else ''}{name}"
            elif action.tactic in ("specialize", "forall_elim", "trans"):
                if action.reverse or (action.tactic == "trans" and action.name is not None):
                    raise PlannerError("unexpected structured step argument")
                term = pretty_term(_parse(action.term, self.variables, self.budget), self.variables)
                name = "" if action.tactic == "trans" else _identifier(action.name) + " "
                command = f"{action.tactic} {name}{term}"
            else:
                raise PlannerError("unknown or unsupported native step kind")
            self.emit(command, "native_step", tactic=action.tactic)
        elif type(action) is RouteAction:
            if type(action.goal) is not int or action.goal != 0:
                raise PlannerError("only the current focused goal can be routed; focus tacticals are not admitted")
            if action.adviser_hint not in ("native", "model", "vampire"):
                raise PlannerError("unknown subgoal adviser hint")
            if type(action.actions) not in (tuple, list) or not 1 <= len(action.actions) <= MAX_ACTIONS:
                raise PlannerError("a route needs explicit native child actions")
            self.hints.append((len(self.commands), action.adviser_hint))
            for child in action.actions:
                self.compile(child, depth + 1)
        elif type(action) is StrengthenAction:
            if self.commands:
                raise PlannerError("finite-difference strengthening must begin a plan")
            if (type(action.max_auxiliaries) is not int or not 1 <= action.max_auxiliaries <= 2
                    or type(action.generalize_parameters) is not bool):
                raise PlannerError("strengthening needs one or two auxiliaries and a Boolean generalization flag")
            from finite_difference import propose_coupled_strengthening, StrengtheningCancelled
            parameter = None
            if action.parameter is not None:
                _identifier(action.parameter)
                if action.parameter not in self.goal.variables:
                    raise PlannerError("strengthening selected an unknown parameter")
                parameter = self.goal.variables.index(action.parameter)
            try:
                proposal = propose_coupled_strengthening(
                    self.goal, self.goal.target, self.goal.context, parameter_index=parameter,
                    max_auxiliaries=action.max_auxiliaries,
                    generalize_parameters=action.generalize_parameters,
                    should_stop=self.budget.should_stop)
            except StrengtheningCancelled as error:
                raise PlannerCancelled(str(error)) from error
            if proposal is None:
                raise PlannerError("no supported coupled finite-difference invariant was found")
            self.budget.tick(proposal.analysis_work)
            _scan(proposal.strengthened, len(self.goal.variables), self.budget)
            for command in proposal.commands:
                self.emit(command, "finite_difference_projection", auxiliaries=proposal.auxiliary_count)
            induction_name = self.fresh("hydra_induction")
            self.emit(f"intro {induction_name}", "finite_difference_induction")
            self.emit(f"induction {induction_name}", "finite_difference_induction")
            self.open_obligations = True
        else:
            raise PlannerError("unknown structured proof action")


def compile_plan(spec, context, *, source="heuristic", should_stop=None):
    if source not in ("heuristic", "planner_model", "test_backend"):
        raise PlannerError("unknown actual proposal source")
    record = context_record(context, should_stop=should_stop)
    if not context.goals:
        raise PlannerError("there is no open goal to plan")
    if (type(spec) is not PlanSpec or type(spec.actions) not in (tuple, list)
            or not 1 <= len(spec.actions) <= MAX_ACTIONS):
        raise PlannerError("expected a nonempty bounded typed plan")
    _text(spec.reason, 1024)
    compiler = _Compiler(context, source, should_stop)
    for action in spec.actions:
        compiler.compile(action)
    if not compiler.commands or compiler.budget.ast_nodes > MAX_AST_NODES:
        raise PlannerLimit("empty or oversized structured plan")
    remaining_depth = context.remaining.get("depth", MAX_COMMANDS)
    remaining_attempts = context.remaining.get("tactic_attempts", MAX_COMMANDS)
    if (type(remaining_depth) is not int or type(remaining_attempts) is not int
            or len(compiler.commands) > min(remaining_depth, remaining_attempts)):
        raise PlannerLimit("complete plan does not fit the remaining native depth/attempt allowance")
    compiler.budget.check()
    commands = tuple(compiler.commands)
    return CompiledPlan(
        commands, tuple(compiler.provenance), context.goals, spec.reason, source,
        sha256(("\n".join(commands) + "\n").encode("utf-8")).hexdigest(),
        sha256(_json(record).encode("utf-8")).hexdigest(), context.capabilities.identity,
        context.library_identity, compiler.budget.ast_nodes, compiler.budget.work,
        compiler.open_obligations, tuple(compiler.hints),
    )


def deterministic_plans(context, *, max_proposals=2, should_stop=None):
    """Small deterministic candidates first; every result remains untrusted."""
    if type(max_proposals) is not int or not 0 <= max_proposals <= MAX_PROPOSALS:
        raise PlannerLimit("at most two plans may be proposed at one decision")
    context_record(context, should_stop=should_stop)
    if not context.goals or not max_proposals:
        return ()
    goal = context.goals[0]
    candidates = [PlanSpec((StrengthenAction(),), "Try a bounded coupled induction invariant.")]
    if goal.variables and not any(name.startswith("IH") for name, _ in goal.context):
        # Generalize one other parameter rather than multiplying the branching
        # space. More ambitious selections are available as explicit actions.
        candidates.append(PlanSpec((InductionAction(goal.variables[-1], tuple(goal.variables[:1])
            if len(goal.variables) > 1 else ()),), "Try induction with an explicitly generalized parameter."))
    result, seen = [], set()
    for spec in candidates:
        try:
            compiled = compile_plan(spec, context, source="heuristic", should_stop=should_stop)
        except PlannerCancelled:
            raise
        except PlannerError:
            continue
        if compiled.commands not in seen:
            seen.add(compiled.commands)
            result.append(compiled)
        if len(result) == max_proposals:
            break
    return tuple(result)


def decode_plan_document(text):
    """Strict JSON envelope; reject duplicate keys, unknown fields and kinds."""
    if type(text) is not str or len(text.encode("utf-8")) > MAX_PLAN_BYTES:
        raise PlannerLimit("planner output byte bound exceeded")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise PlannerError("duplicate key in planner JSON")
            result[key] = value
        return result
    def constant(_):
        raise PlannerError("non-finite JSON number in planner output")
    try:
        raw = json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    except PlannerError:
        raise
    except (ValueError, TypeError, RecursionError) as error:
        raise PlannerError("planner output is not one valid JSON document") from error
    def fields(record, required, optional=()):
        if (type(record) is not dict or not set(required) <= record.keys()
                or set(record) - set(required) - set(optional)):
            raise PlannerError("missing or unknown structured-plan field")
    fields(raw, ("v", "plans"))
    if type(raw["v"]) is not int or raw["v"] != 1 or type(raw["plans"]) is not list or not 1 <= len(raw["plans"]) <= 2:
        raise PlannerError("planner document must contain version 1 and one or two plans")
    count = 0
    def action(record, depth=0):
        nonlocal count
        count += 1
        if count > MAX_ACTIONS * MAX_PROPOSALS or depth > 4:
            raise PlannerLimit("decoded planner action bound exceeded")
        fields(record, ("kind",), ("variable", "generalize", "variables", "mode", "name", "statement",
               "template", "bindings", "lemma", "terms", "alias", "finish", "tactic", "term",
               "reverse", "goal", "actions", "adviser_hint", "parameter", "max_auxiliaries", "generalize_parameters"))
        kind = record["kind"]
        if kind == "induct":
            fields(record, ("kind", "variable"), ("generalize",))
            generalized = record.get("generalize", [])
            if type(generalized) is not list:
                raise PlannerError("generalize must be an array")
            return InductionAction(record["variable"], tuple(generalized))
        if kind == "generalize":
            fields(record, ("kind", "variables"))
            if type(record["variables"]) is not list:
                raise PlannerError("variables must be an array")
            return GeneralizeAction(tuple(record["variables"]))
        if kind == "auxiliary":
            fields(record, ("kind", "mode", "name", "statement"))
            return AuxiliaryAction(record["mode"], record["name"], record["statement"])
        if kind == "witness":
            fields(record, ("kind", "template"), ("bindings",))
            bindings = record.get("bindings", {})
            if type(bindings) is not dict:
                raise PlannerError("witness bindings must be an object")
            return WitnessAction(WitnessTemplate(record["template"], tuple(bindings.items())))
        if kind == "instantiate":
            fields(record, ("kind", "lemma"), ("terms", "alias", "finish"))
            terms = record.get("terms", [])
            if type(terms) is not list:
                raise PlannerError("lemma terms must be an array")
            return InstantiateAction(record["lemma"], tuple(terms), record.get("alias"), record.get("finish", "none"))
        if kind == "step":
            fields(record, ("kind", "tactic"), ("name", "term", "reverse"))
            return StepAction(record["tactic"], record.get("name"), record.get("term"), record.get("reverse", False))
        if kind == "route":
            fields(record, ("kind", "goal", "actions"), ("adviser_hint",))
            if type(record["actions"]) is not list or len(record["actions"]) > MAX_ACTIONS:
                raise PlannerError("route actions must be a bounded array")
            return RouteAction(record["goal"], tuple(action(child, depth + 1) for child in record["actions"]),
                               record.get("adviser_hint", "native"))
        if kind == "strengthen":
            fields(record, ("kind",), ("parameter", "max_auxiliaries", "generalize_parameters"))
            return StrengthenAction(record.get("parameter"), record.get("max_auxiliaries", 2),
                                    record.get("generalize_parameters", True))
        raise PlannerError("unknown structured action kind")
    result = []
    for record in raw["plans"]:
        fields(record, ("reason", "actions"))
        if type(record["actions"]) is not list or not 1 <= len(record["actions"]) <= MAX_ACTIONS:
            raise PlannerError("plan actions must be a bounded nonempty array")
        result.append(PlanSpec(tuple(action(item) for item in record["actions"]), record["reason"]))
    return tuple(result)
