"""Bounded state-aware symbolic proposals for the existing Hydra runner.

This is an untrusted candidate generator, not another proof engine. It reads
only the canonical current goals and local hypotheses, proposes ordinary
single-step tactics through the development action protocol, and leaves all
execution and original-goal checking to Peano. It never loads a theorem
portfolio, recorded script, model, or external solver. Arithmetic used to rank
small witness candidates is not proof evidence.

The existing search counter named ``model_calls`` counts policy requests even
for symbolic providers. Consumers must label those as state expansions and
use ``workload`` below for the explicit zero model/solver-call accounting.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Iterator

from peano_lab.kernel.formulas import (
    And, Bot, Eq, Exists, Forall, Formula, Imp, Or, parse_formula_in_context,
)
from peano_lab.kernel.subst import subst_formula
from peano_lab.kernel.terms import Add, Mul, Succ, Term, Var, Zero, numeral_value, pretty_term
from peano_lab.ui.prove import SurfaceCapabilities
from training.peano_hydra.policy import HydraCandidatePolicy, PolicyHead, _validate_tactic_line
from training.peano_hydra.protocol import compile_action, development_profile
from training.peano_hydra.runner import policy_environment
from training.peano_policy.search import SearchLimits, state_sha256


SYMBOLIC_COMMANDS = frozenset({
    "apply", "assumption", "cases", "congr", "exists", "induction", "intro",
    "left", "norm_num", "refl", "rewrite", "right", "simp", "split",
})
SYMBOLIC_SCHEMA = "peano-hydra-bounded-symbolic-policy-v1"
MAX_TACTIC_BYTES = 4_096
MAX_SYMBOLIC_EVIDENCE_BYTES = 1_024 * 1_024
DEFAULT_SYMBOLIC_LIMITS = SearchLimits(
    max_depth=16, beam_width=4, candidates_per_state=8, max_model_calls=32, max_states=128,
)
_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_']{0,63}\Z")
_META = re.compile(r"\?t[0-9]+(?:@[0-9]+)?")


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class SymbolicConfig:
    """Frozen components and finite per-request enumeration limits.

    Components may be disabled independently. Their names describe proposal
    families; turning on induction alone does not supply a closing tactic.
    Search depth/beam/state limits remain separate host-owned SearchLimits.
    """

    closure: bool = True
    structural: bool = True
    witness: bool = True
    induction: bool = True
    candidates_per_state: int = 8
    max_proposals: int = 128
    max_witness_value: int = 8
    max_term_candidates: int = 32
    max_term_nodes: int = 16
    max_induction_hypotheses: int = 2
    max_induction_candidates: int = 2
    max_goal_bytes: int = 4_096
    max_state_bytes: int = 16_384
    max_goals: int = 16
    max_context: int = 16
    max_variables: int = 8
    max_formula_nodes: int = 2_048
    max_formula_depth: int = 96
    max_arithmetic_value: int = 128
    max_action_receipt_bytes: int = 512 * 1_024

    def __post_init__(self) -> None:
        for name in ("closure", "structural", "witness", "induction"):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"symbolic {name} must be a Boolean")
        if not any((self.closure, self.structural, self.witness, self.induction)):
            raise ValueError("symbolic configuration must enable at least one component")
        bounds = {
            "candidates_per_state": (1, 8), "max_proposals": (1, 256),
            "max_witness_value": (0, 16), "max_term_candidates": (1, 64),
            "max_term_nodes": (1, 64), "max_induction_hypotheses": (0, 3),
            "max_induction_candidates": (1, 4), "max_goal_bytes": (32, 4_096),
            "max_state_bytes": (32, 32_768), "max_goals": (1, 32),
            "max_context": (1, 16), "max_variables": (1, 16),
            "max_formula_nodes": (8, 4_096), "max_formula_depth": (4, 96),
            "max_arithmetic_value": (1, 128),
            "max_action_receipt_bytes": (1_024, 512 * 1_024),
        }
        for name, (minimum, maximum) in bounds.items():
            value = getattr(self, name)
            if type(value) is not int or not minimum <= value <= maximum:
                raise ValueError(f"symbolic {name} must lie in [{minimum}, {maximum}]")
        if self.max_state_bytes < self.max_goal_bytes:
            raise ValueError("symbolic state-byte limit cannot be smaller than one goal")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class _Observation:
    variables: tuple[str, ...]  # nearest binder first, as in the kernel printer
    hypotheses: tuple[tuple[str, Formula], ...]  # visible oldest first
    target: Formula
    has_metas: bool

    @property
    def used_names(self) -> frozenset[str]:
        return frozenset(self.variables) | frozenset(name for name, _ in self.hypotheses)


class _ObservationLimit(ValueError):
    pass


def _nodes(root: Formula | Term, maximum: int, depth_limit: int) -> int:
    pending = [(root, 1)]
    count = 0
    while pending:
        node, depth = pending.pop()
        count += 1
        if count > maximum or depth > depth_limit:
            raise _ObservationLimit("symbolic formula exceeds its AST boundary")
        if type(node) in (Eq, And, Or, Imp, Add, Mul):
            pending.extend(((node.left, depth + 1), (node.right, depth + 1)))
        elif type(node) in (Forall, Exists):
            pending.append((node.body, depth + 1))
        elif type(node) is Succ:
            pending.append((node.term, depth + 1))
        elif type(node) not in (Var, Zero, Bot):
            raise _ObservationLimit("symbolic formula contains an unsupported constructor")
    return count


def _observe(goals: tuple[str, ...], config: SymbolicConfig) -> tuple[_Observation, int]:
    if type(goals) is not tuple or not goals or not all(type(goal) is str and goal for goal in goals):
        raise TypeError("symbolic proposals require one nonempty exact tuple of canonical goals")
    if len(goals) > config.max_goals:
        raise _ObservationLimit("symbolic goal count exceeds its boundary")
    sizes = [len(goal.encode("utf-8")) for goal in goals]
    if max(sizes) > config.max_goal_bytes or sum(sizes) > config.max_state_bytes:
        raise _ObservationLimit("symbolic goal text exceeds its byte boundary")
    focused = goals[0]
    if focused.splitlines() != [focused] or focused.count("⊢") != 1:
        raise _ObservationLimit("symbolic goal is not a canonical single-line observation")
    # Keep the parser's own recursive descent well inside the public limits.
    if any(len(value) > 3 or int(value) > config.max_arithmetic_value for value in re.findall(r"(?<![\w'])\d+", _META.sub("m", focused))):
        raise _ObservationLimit("symbolic observation contains an oversized numeral")
    if focused.count("(") > config.max_formula_depth or focused.count("∀") + focused.count("∃") > config.max_formula_depth:
        raise _ObservationLimit("symbolic parser nesting exceeds its boundary")
    prefix, _, target_source = focused.partition("⊢")
    variables: list[str] = []
    hypothesis_sources: list[tuple[str, str]] = []
    used: set[str] = set()
    for declaration in prefix.strip().split(", ") if prefix.strip() else ():
        name, separator, source = declaration.partition(" : ")
        if not separator or _NAME.fullmatch(name) is None or name in used:
            raise _ObservationLimit("symbolic context declaration is malformed")
        used.add(name)
        if source == "ℕ":
            if hypothesis_sources:
                raise _ObservationLimit("rigid variables must precede displayed hypotheses")
            variables.append(name)
        else:
            hypothesis_sources.append((name, source))
    if len(variables) > config.max_variables or len(hypothesis_sources) > config.max_context:
        raise _ObservationLimit("symbolic context exceeds its boundary")
    index_names = list(reversed(variables))
    # Metavariables are opaque for scoring, never concrete witnesses. Their
    # actual identity/substitution remains wholly owned by the tactic engine.
    metas: dict[str, str] = {}
    for match in _META.finditer(focused):
        if match.group() not in metas:
            name = f"hydra_meta_{len(metas)}"
            while name in used:
                name += "_"
            used.add(name)
            metas[match.group()] = name
            index_names.append(name)
    def parse(source: str) -> Formula:
        return parse_formula_in_context(_META.sub(lambda match: metas[match.group()], source), index_names)
    try:
        target = parse(target_source.strip())
        hypotheses = tuple((name, parse(source)) for name, source in hypothesis_sources)
        total = _nodes(target, config.max_formula_nodes, config.max_formula_depth)
        for _, formula in hypotheses:
            total += _nodes(formula, config.max_formula_nodes, config.max_formula_depth)
            if total > config.max_formula_nodes:
                raise _ObservationLimit("symbolic whole-context AST exceeds its boundary")
    except (ValueError, RecursionError) as error:
        raise _ObservationLimit(str(error)) from error
    return _Observation(tuple(reversed(variables)), hypotheses, target, bool(metas)), total


def _fresh(base: str, observation: _Observation) -> str:
    used = observation.used_names
    if base not in used:
        return base
    for index in range(len(used) + 1):
        name = f"{base}{index}"
        if name not in used:
            return name
    raise _ObservationLimit("no bounded fresh symbolic name")


def _body(formula: Formula) -> Formula:
    while type(formula) is Forall:
        formula = formula.body
    return formula


def _value(term: Term, maximum: int) -> int | None:
    if type(term) is Zero:
        return 0
    if type(term) is Var:
        return None
    if type(term) is Succ:
        inner = _value(term.term, maximum)
        return inner + 1 if inner is not None and inner < maximum else None
    left, right = _value(term.left, maximum), _value(term.right, maximum)
    if left is None or right is None:
        return None
    value = left + right if type(term) is Add else left * right
    return value if value <= maximum else None


def _has_numerical_island(formula: Eq, maximum: int) -> bool:
    pending = [formula.left, formula.right]
    while pending:
        term = pending.pop()
        if type(term) in (Add, Mul):
            if _value(term, maximum) is not None:
                return True
            pending.extend((term.left, term.right))
        elif type(term) is Succ:
            pending.append(term.term)
    return False


def _lower_term(term: Term, depth: int, variable_count: int) -> Term | None:
    if type(term) is Var:
        return Var(term.index - depth) if depth <= term.index < depth + variable_count else None
    if type(term) is Zero:
        return term
    if type(term) is Succ:
        inner = _lower_term(term.term, depth, variable_count)
        return None if inner is None else Succ(inner)
    left = _lower_term(term.left, depth, variable_count)
    right = _lower_term(term.right, depth, variable_count)
    return None if left is None or right is None else type(term)(left, right)


def _visible_terms(formula: Formula, variable_count: int) -> Iterator[Term]:
    pending: list[tuple[Formula | Term, int]] = [(formula, 0)]
    while pending:
        node, depth = pending.pop()
        if isinstance(node, Term):
            term = _lower_term(node, depth, variable_count)
            if term is not None:
                yield term
        if type(node) in (Eq, And, Or, Imp, Add, Mul):
            pending.extend(((node.right, depth), (node.left, depth)))
        elif type(node) in (Forall, Exists):
            pending.append((node.body, depth + 1))
        elif type(node) is Succ:
            pending.append((node.term, depth))


def _mentions(formula: Formula, index: int) -> bool:
    return any(
        type(term) is Var and term.index == index
        for term in _visible_terms(formula, index + 1)
    )


def _action(operation: str, **fields: object) -> dict[str, object]:
    return {"v": 1, "op": operation, **fields}


def _dispatch(solver: str, premises: tuple[str, ...] = ()) -> dict[str, object]:
    return _action("Dispatch", solver=solver, premises=list(premises), bounds={"max_calls": 1})


@dataclass(frozen=True, slots=True)
class SymbolicCandidatePolicy:
    """An identified, finite symbolic child suitable for a Hydra portfolio."""

    capabilities: SurfaceCapabilities
    config: SymbolicConfig = SymbolicConfig()
    name: str = "hydra-bounded-symbolic-v1"
    _identity_json: str = field(init=False, repr=False)
    _environment_json: str = field(init=False, repr=False)
    _work: dict[str, int] = field(init=False, repr=False, compare=False)
    _action_records: list[dict[str, object]] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if type(self.capabilities) is not SurfaceCapabilities or type(self.config) is not SymbolicConfig:
            raise TypeError("symbolic policy requires exact capabilities and SymbolicConfig")
        if self.capabilities.allowed_commands is None or self.capabilities.allowed_theorems != frozenset():
            raise ValueError("symbolic development requires finite commands and an explicit empty theorem allowlist")
        if type(self.name) is not str or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,159}", self.name) is None:
            raise ValueError("symbolic policy name must be bounded nonempty text")
        environment = policy_environment(self.capabilities)
        identity = {
            "name": self.name, "kind": SYMBOLIC_SCHEMA, "config": self.config.to_dict(),
            "environment": environment, "profile_sha256": development_profile()["profile_sha256"],
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "candidate_semantics": "one-typed-action-one-public-tactic-no-hidden-search",
            "model_calls": 0, "solver_calls": 0, "recorded_scripts": False,
            "solver_call_semantics": "external providers only; native closures are ordinary tactic edges",
            "research_claim_eligible": False,
        }
        object.__setattr__(self, "_identity_json", _canonical(identity))
        object.__setattr__(self, "_environment_json", _canonical(environment))
        object.__setattr__(self, "_action_records", [])
        object.__setattr__(self, "_work", dict.fromkeys((
            "proposal_calls", "formula_nodes_scanned", "terms_considered",
            "witnesses_ranked", "arithmetic_comparisons", "candidate_lines_generated",
            "candidate_lines_returned", "observation_limit_hits", "proposal_limit_hits",
            "protocol_rejections", "model_calls", "solver_calls",
            "external_solver_calls", "native_dispatch_proposals",
            "retained_action_receipt_bytes", "receipt_limit_hits",
        ), 0))

    @property
    def evaluation_identity(self) -> dict[str, object]:
        return json.loads(self._identity_json)

    @property
    def policy_environment(self) -> dict[str, object]:
        return json.loads(self._environment_json)

    @property
    def workload(self) -> dict[str, int]:
        """Detached real proposal/enumeration counts; no ML calls are hidden."""
        return dict(self._work)

    @property
    def action_records(self) -> tuple[dict[str, object], ...]:
        """Bounded, detached typed transports bound to the runner's state ledger."""
        return tuple(json.loads(_canonical(record)) for record in self._action_records)

    def _record_action(self, action, commands, status, error, goals, index) -> bool:
        record = {
            "schema": "peano-hydra-symbolic-action-receipt-v1",
            "proposal_call": self._work["proposal_calls"], "candidate_index": index,
            "action": action, "compiled_commands": list(commands), "status": status,
            "error": error, "profile_sha256": self.evaluation_identity["profile_sha256"],
            "environment_sha256": self.policy_environment["environment_sha256"],
            "state_sha256": state_sha256(goals),
        }
        record["receipt_sha256"] = hashlib.sha256(_canonical(record).encode("utf-8")).hexdigest()
        size = len(_canonical(record).encode("utf-8"))
        if (
            len(self._action_records) >= self.config.max_proposals * self.config.candidates_per_state
            or self._work["retained_action_receipt_bytes"] + size > self.config.max_action_receipt_bytes
        ):
            self._work["receipt_limit_hits"] += 1
            return False
        self._action_records.append(record)
        self._work["retained_action_receipt_bytes"] += size
        return True

    def _terms(self, observation: _Observation) -> tuple[Term, ...]:
        cfg = self.config
        terms: list[Term] = []
        seen: set[Term] = set()
        def add(term: Term) -> None:
            if len(terms) >= cfg.max_term_candidates:
                return
            self._work["terms_considered"] += 1
            try:
                _nodes(term, cfg.max_term_nodes, cfg.max_formula_depth)
            except _ObservationLimit:
                return
            value = numeral_value(term)
            if value is not None and value > cfg.max_witness_value:
                return
            if term not in seen:
                seen.add(term)
                terms.append(term)
        # Prefer terms already in the goal, then available rigid variables.
        # Binder-local and unresolved meta variables never escape into terms.
        for term in _visible_terms(observation.target, len(observation.variables)):
            add(term)
            if len(terms) >= cfg.max_term_candidates:
                break
        for index in range(len(observation.variables)):
            add(Var(index))
        for _, formula in reversed(observation.hypotheses[-4:]):
            for term in _visible_terms(formula, len(observation.variables)):
                add(term)
                if len(terms) >= cfg.max_term_candidates:
                    break
        numeral: Term = Zero()
        for _ in range(cfg.max_witness_value + 1):
            add(numeral)
            numeral = Succ(numeral)
        # One finite constructor layer over a fixed tiny prefix, never an
        # open-ended recursive grammar or a materialized Cartesian explosion.
        atoms = tuple(terms[: min(6, cfg.max_term_candidates)])
        for term in atoms:
            add(Succ(term))
        for left in atoms:
            for right in atoms:
                add(Add(left, right))
                add(Mul(left, right))
        return tuple(terms)

    def _witness_rank(self, body: Formula, term: Term) -> int:
        self._work["witnesses_ranked"] += 1
        instance = subst_formula(body, 0, term)
        if type(instance) is Eq:
            if instance.left == instance.right:
                return 0
            self._work["arithmetic_comparisons"] += 1
            left = _value(instance.left, self.config.max_arithmetic_value)
            right = _value(instance.right, self.config.max_arithmetic_value)
            if left is not None and right is not None:
                return 0 if left == right else 2
        return 1

    def _actions(self, observation: _Observation) -> Iterator[dict[str, object]]:
        cfg, target = self.config, observation.target
        body = _body(target)
        hypotheses = tuple(reversed(observation.hypotheses))
        equations = tuple(name for name, formula in hypotheses if type(_body(formula)) is Eq)[:2]
        if cfg.closure:
            if any(formula == target for _, formula in hypotheses) or observation.has_metas:
                yield _dispatch("assumption")
            if type(target) is Eq and (target.left == target.right or observation.has_metas):
                yield _dispatch("refl")
            if not observation.has_metas and type(body) is Eq:
                left = _value(body.left, cfg.max_arithmetic_value)
                right = _value(body.right, cfg.max_arithmetic_value)
                self._work["arithmetic_comparisons"] += 1
                if (left is not None and right is not None and left == right) or _has_numerical_island(body, cfg.max_arithmetic_value):
                    yield _dispatch("norm_num")
                if equations:
                    yield _dispatch("simp", equations)
                yield _dispatch("simp")
        if cfg.structural:
            if type(target) in (Imp, Forall):
                yield _action("Split", kind="intro", name=_fresh("h" if type(target) is Imp else "n", observation))
            elif type(target) is And:
                yield _action("Split", kind="and", name=None)
            elif type(target) is Or:
                yield _action("Split", kind="left", name=None)
                yield _action("Split", kind="right", name=None)
            for name, formula in hypotheses:
                conclusion = _body(formula)
                while type(conclusion) is Imp:
                    conclusion = conclusion.right
                if conclusion == target or (type(formula) is Forall and type(conclusion) is type(target)):
                    yield _action("Use", name=name, specializations=[])
            for name, formula in hypotheses:
                if type(formula) in (And, Or, Exists, Bot):
                    eliminated = any(
                        other == f"{name}_{suffix}"
                        for other, _ in hypotheses for suffix in ("left", "right", "witness")
                    )
                    if not eliminated:
                        yield _action("Split", kind="cases", name=name)
            if type(target) is Bot:
                yield _action("Use", name="PA1", specializations=[])
            elif type(target) is Eq and any(
                type(formula) is Eq
                and type(formula.left) is Succ
                and type(formula.right) is Succ
                for _, formula in hypotheses
            ):
                yield _action("Use", name="PA2", specializations=[])
        if cfg.witness and type(target) is Exists and not observation.has_metas:
            terms = self._terms(observation)
            ranked = sorted(enumerate(terms), key=lambda item: (self._witness_rank(target.body, item[1]), item[0]))
            for _, term in ranked:
                yield _action("Witness", term=pretty_term(term, list(observation.variables)))
        if cfg.induction and not observation.has_metas:
            induction_hypotheses = sum(re.fullmatch(r"IH[0-9]*", name) is not None for name, _ in hypotheses)
            if induction_hypotheses < cfg.max_induction_hypotheses:
                # The typed development protocol requires an existing rigid
                # variable. A leading forall is introduced by the structural
                # component first, rather than inventing context authority.
                if type(target) is not Forall:
                    count = 0
                    for index, name in enumerate(observation.variables):
                        if _mentions(target, index):
                            yield _action("Induct", variable=name, motive="goal")
                            count += 1
                            if count >= cfg.max_induction_candidates:
                                break
        if cfg.closure and not observation.has_metas and type(body) is Eq:
            for name in equations:
                yield _dispatch("simp", (name,))
                yield _action("Rewrite", source=name, direction="forward", location="goal")
                yield _action("Rewrite", source=name, direction="backward", location="goal")

    def propose(self, goals_before: tuple[str, ...], *, max_candidates: int) -> tuple[str, ...]:
        if type(max_candidates) is not int or not 1 <= max_candidates <= self.config.candidates_per_state:
            raise ValueError("symbolic request exceeds its frozen candidate quota")
        if self._work["proposal_calls"] >= self.config.max_proposals:
            self._work["proposal_limit_hits"] += 1
            return ()
        self._work["proposal_calls"] += 1
        try:
            observation, nodes = _observe(goals_before, self.config)
        except _ObservationLimit:
            self._work["observation_limit_hits"] += 1
            return ()
        self._work["formula_nodes_scanned"] += nodes
        candidates: list[str] = []
        seen: set[str] = set()
        attempts = 0
        for action in self._actions(observation):
            operation = action["op"]
            head = {
                "Use": "apply", "Induct": "induction", "Witness": "exists", "Rewrite": "rewrite",
            }.get(operation)
            if operation == "Dispatch":
                head = action["solver"]
            elif operation == "Split":
                head = "split" if action["kind"] == "and" else action["kind"]
            if head not in self.capabilities.allowed_commands:
                continue
            attempts += 1
            if operation == "Dispatch":
                self._work["native_dispatch_proposals"] += 1
            try:
                commands = compile_action(
                    action, capabilities=self.capabilities, variables=observation.variables,
                    hypotheses=tuple(name for name, _ in observation.hypotheses),
                )
            except ValueError as error:
                self._work["protocol_rejections"] += 1
                recorded = self._record_action(action, (), "rejected", " ".join(str(error).split())[:256], goals_before, attempts)
                if not recorded or attempts >= max_candidates:
                    break
                continue
            if type(commands) is not tuple or len(commands) != 1:
                raise ValueError("symbolic candidates must contain exactly one public tactic")
            line = _validate_tactic_line(commands[0])
            if len(line.encode("utf-8")) > MAX_TACTIC_BYTES or line.split(" ", 1)[0] not in SYMBOLIC_COMMANDS:
                raise ValueError("compiled symbolic candidate escaped its tactic boundary")
            self._work["candidate_lines_generated"] += 1
            status = "duplicate" if line in seen else "accepted"
            if not self._record_action(action, commands, status, None, goals_before, attempts):
                break
            if line not in seen:
                seen.add(line)
                candidates.append(line)
            if attempts >= max_candidates:
                break
        self._work["candidate_lines_returned"] += len(candidates)
        return tuple(candidates)


def make_symbolic_policy(
    capabilities: SurfaceCapabilities,
    config: SymbolicConfig = SymbolicConfig(),
) -> HydraCandidatePolicy:
    """Create a fresh one-head portfolio; never reuse a proposal ledger."""
    child = SymbolicCandidatePolicy(capabilities, config)
    return HydraCandidatePolicy(
        (PolicyHead("bounded-symbolic", "symbolic", config.candidates_per_state, child),),
        name="hydra-bounded-symbolic-portfolio-v1",
    )


def _bounded_evidence_json(value: object) -> str:
    """Reject oversized/non-JSON/cyclic inputs before proposal regeneration."""
    pending = [(value, 0)]
    visited = text_bytes = 0
    while pending:
        item, depth = pending.pop()
        visited += 1
        if depth > 32 or visited + len(pending) > 131_072:
            raise ValueError("symbolic evidence exceeds its JSON structure boundary")
        if type(item) is dict:
            if len(item) > 4_096 or any(type(key) is not str for key in item):
                raise ValueError("symbolic evidence has malformed JSON fields")
            pending.extend((child, depth + 1) for pair in item.items() for child in pair)
        elif type(item) is list:
            if len(item) > 131_072:
                raise ValueError("symbolic evidence exceeds its JSON array boundary")
            pending.extend((child, depth + 1) for child in item)
        elif type(item) is str:
            if len(item) > MAX_SYMBOLIC_EVIDENCE_BYTES:
                raise ValueError("symbolic evidence exceeds its text boundary")
            try:
                text_bytes += len(item.encode("utf-8"))
            except UnicodeError:
                raise ValueError("symbolic evidence contains invalid Unicode") from None
            if text_bytes > MAX_SYMBOLIC_EVIDENCE_BYTES:
                raise ValueError("symbolic evidence exceeds its text boundary")
        elif type(item) is int:
            if item.bit_length() > 63:
                raise ValueError("symbolic evidence integer exceeds its boundary")
        elif type(item) is float:
            if not math.isfinite(item):
                raise ValueError("symbolic evidence contains a non-finite number")
        elif item is not None and type(item) is not bool:
            raise ValueError("symbolic evidence must contain only exact JSON values")
    encoded = _canonical(value)
    if len(encoded.encode("utf-8")) > MAX_SYMBOLIC_EVIDENCE_BYTES:
        raise ValueError("symbolic evidence exceeds its one-MiB reservation")
    return encoded


def _evidence_goals(value: object, *, allow_empty: bool = False) -> tuple[str, ...]:
    # Permit bounded observations which exceed the policy's smaller semantic
    # limits: regeneration must faithfully account for their limit-hit rows.
    if (type(value) is not list or not (0 if allow_empty else 1) <= len(value) <= 256
        or any(type(goal) is not str or not goal for goal in value)
        or sum(len(goal.encode("utf-8")) for goal in value) > MAX_SYMBOLIC_EVIDENCE_BYTES):
        raise ValueError("symbolic evidence has unbounded or malformed state observations")
    return tuple(value)


def _goal_alias_key(goals: tuple[str, ...]) -> tuple[str, ...]:
    """Compare complete states modulo presentation-only metavariable names.

    Search reassigns aliases independently at every state, whereas batch traces
    retain aliases along the whole successful path. A bijective first-occurrence
    renaming preserves repeated metavariables and any explicit scope suffixes;
    no formula, rigid name, goal order, or other text is normalized away.
    The caller still independently kernel-replays the exact, unmodified trace.
    """
    aliases: dict[str, str] = {}
    def replace(match: re.Match[str]) -> str:
        return aliases.setdefault(match.group(), f"?t{len(aliases) + 1}")
    return tuple(re.sub(r"\?t[0-9]+", replace, goal) for goal in goals)


def verify_symbolic_evidence(
    evidence: dict[str, object],
    action_records: list[dict[str, object]] | tuple[dict[str, object], ...],
    workload: dict[str, int],
    *,
    capabilities: SurfaceCapabilities,
    config: SymbolicConfig = SymbolicConfig(),
) -> None:
    """Authenticate deterministic proposal attribution without running search.

    Regenerate only the retained bounded observations, comparing the exact
    portfolio, complete proposal ledger, typed receipts, and workload. Bind a
    successful command path to those proposals and its original-goal trace.
    This does *not* validate certificates, reconstruct unexplored search edges,
    or authenticate measured wall/CPU/RSS; the host must independently replay
    every positive trace and validate its original goal, authority and limits.
    """
    if type(config) is not SymbolicConfig:
        raise ValueError("symbolic verification needs an exact frozen configuration")
    if type(evidence) is not dict or type(workload) is not dict or type(action_records) not in (tuple, list):
        raise ValueError("symbolic verification needs complete JSON evidence and action records")
    if len(action_records) > config.max_proposals * config.candidates_per_state:
        raise ValueError("symbolic action evidence exceeds its record reservation")
    actions = list(action_records)
    _bounded_evidence_json({"evidence": evidence, "action_records": actions, "workload": workload})
    if sum(len(_canonical(record).encode("utf-8")) for record in actions) > config.max_action_receipt_bytes:
        raise ValueError("symbolic action evidence exceeds its byte reservation")
    required = {"v", "label", "status", "proved", "theorem", "policy", "policy_identity",
                "environment", "limits", "commands_sha256", "proposal_records", "degraded",
                "eligible_for_comparison", "comparison_ineligibility_reasons", "degradation_reasons",
                "search", "replay"}
    if set(evidence) != required or type(evidence["v"]) is not int or evidence["v"] != 1:
        raise ValueError("symbolic runner evidence schema differs")
    limits = evidence["limits"]
    ceilings = {"max_depth": 16, "beam_width": 8, "candidates_per_state": config.candidates_per_state,
                "max_model_calls": config.max_proposals, "max_states": 256}
    if (type(limits) is not dict or set(limits) != set(ceilings)
        or any(type(limits[name]) is not int or not 1 <= limits[name] <= ceiling for name, ceiling in ceilings.items())
        or limits["candidates_per_state"] != config.candidates_per_state):
        raise ValueError("symbolic search evidence exceeds its frozen verification limits")
    records, search = evidence["proposal_records"], evidence["search"]
    if type(records) is not list or not 1 <= len(records) <= limits["max_model_calls"] or type(search) is not dict:
        raise ValueError("symbolic proposal evidence exceeds its call reservation")
    theorem = evidence["theorem"]
    if type(theorem) is not str or not theorem or len(theorem.encode("utf-8")) > MAX_TACTIC_BYTES:
        raise ValueError("symbolic evidence has an unbounded original theorem")
    states = []
    for index, record in enumerate(records, 1):
        if (type(record) is not dict or type(record.get("portfolio_call")) is not int
            or record["portfolio_call"] != index or record.get("outcome") != "ok"):
            raise ValueError("symbolic proposal calls are incomplete, reordered or degraded")
        states.append(_evidence_goals(record.get("goals")))
    if states[0] != (f"⊢ {theorem}",):
        raise ValueError("symbolic proposals do not start at the original closed goal")
    if (evidence["degraded"] is not False or evidence["degradation_reasons"] != []
        or type(evidence["proved"]) is not bool or evidence["status"] not in ("proof", "exhausted", "limit")
        or evidence["proved"] != (evidence["status"] == "proof")
        or search.get("status") != evidence["status"] or search.get("theorem") != theorem):
        raise ValueError("symbolic proof status or original-goal binding differs")
    for name in ("model_calls", "states_expanded"):
        if type(search.get(name)) is not int or search[name] != len(records):
            raise ValueError("symbolic search expansion count differs from its proposal ledger")
    for name, minimum, maximum in (
        ("states_discovered", 1, limits["max_states"]),
        ("candidates_executed", 0, len(records) * config.candidates_per_state),
        ("frontier_peak", 1, limits["beam_width"]),
        ("depth_reached", 0, limits["max_depth"]),
    ):
        if type(search.get(name)) is not int or not minimum <= search[name] <= maximum:
            raise ValueError("symbolic search counters exceed their reservations")

    fresh = make_symbolic_policy(capabilities, config=config)
    if (evidence["policy"] != fresh.name
        or _canonical(evidence["policy_identity"]) != _canonical(fresh.evaluation_identity)
        or _canonical(evidence["environment"]) != _canonical(fresh.policy_environment)):
        raise ValueError("symbolic policy identity, configuration or execution authority differs")
    for state in states:
        fresh.propose(state, max_candidates=limits["candidates_per_state"])
    if _canonical(records) != _canonical([record.to_dict() for record in fresh.records]):
        raise ValueError("symbolic proposal ledger differs from deterministic regeneration")
    child = fresh.heads[0].policy
    if _canonical(actions) != _canonical(list(child.action_records)):
        raise ValueError("symbolic typed action receipts differ from deterministic regeneration")
    if _canonical(workload) != _canonical(child.workload):
        raise ValueError("symbolic workload differs from deterministic regeneration")
    accepted_count = sum(len(record["accepted_candidates"]) for record in records)
    if search["candidates_executed"] > accepted_count:
        raise ValueError("symbolic search claims more candidate edges than proposals")
    commands = search.get("commands")
    if type(commands) is not list or len(commands) > limits["max_depth"]:
        raise ValueError("symbolic final command path exceeds its depth reservation")
    if not evidence["proved"]:
        if commands or search.get("certificate_nodes") is not None or evidence["replay"] is not None or evidence["commands_sha256"] is not None:
            raise ValueError("symbolic unknown result cannot contain positive proof evidence")
        return
    if not commands or any(type(line) is not str or not line or len(line.encode("utf-8")) > MAX_TACTIC_BYTES
                           or line.splitlines() != [line] or ";" in line or "<|>" in line for line in commands):
        raise ValueError("symbolic successful command path violates its single-action boundary")
    command_digest = hashlib.sha256(_canonical(commands).encode("utf-8")).hexdigest()
    if evidence["commands_sha256"] != command_digest:
        raise ValueError("symbolic successful command digest differs")
    replay = evidence["replay"]
    if (type(replay) is not dict or replay.get("kernel_checked") is not True
        or replay.get("status") != "proved" or replay.get("theorem") != theorem
        or replay.get("environment_sha256") != fresh.policy_environment["environment_sha256"]
        or replay.get("surface") != capabilities.label or replay.get("classical") is not False
        or replay.get("goals") != [] or type(replay.get("proof_nodes")) is not int
        or replay["proof_nodes"] < 1 or type(search.get("certificate_nodes")) is not int
        or search["certificate_nodes"] != replay["proof_nodes"]):
        raise ValueError("symbolic successful replay changed its original goal or authority")
    trace = replay.get("trace")
    if type(trace) is not list or len(trace) != len(commands) + 1:
        raise ValueError("symbolic successful replay needs one binding transition per command")
    expected_footer = {"qed": True, "theorem": theorem, "proof_size": replay["proof_nodes"], "tactic_count": len(commands)}
    if _canonical(trace[-1]) != _canonical(expected_footer):
        raise ValueError("symbolic successful replay footer differs")
    proposals: dict[tuple[tuple[str, ...], str], list[int]] = {}
    for index, (record, state) in enumerate(zip(records, states), 1):
        for command in record["accepted_candidates"]:
            proposals.setdefault((_goal_alias_key(state), command), []).append(index)
    before, previous_call = (f"⊢ {theorem}",), 0
    for index, (line, transition) in enumerate(zip(commands, trace[:-1]), 1):
        if (type(transition) is not dict or transition.get("tactic") != line
            or transition.get("status") != "ok" or transition.get("error") is not None
            or type(transition.get("step")) is not int or transition["step"] != index
            or transition.get("session") != replay.get("session")
            or type(transition.get("focus")) is not int or transition["focus"] != 0
            or _evidence_goals(transition.get("goals_before")) != before):
            raise ValueError("symbolic successful transitions differ from the exact command path")
        matches = proposals.get((_goal_alias_key(before), line), ())
        matched_call = next((call for call in matches if call > previous_call), None)
        if matched_call is None:
            raise ValueError("symbolic successful command/goal pair was not an ordered accepted proposal")
        previous_call = matched_call
        before = _evidence_goals(transition.get("goals_after"), allow_empty=True)
    if before:
        raise ValueError("symbolic successful trace leaves open goals")


__all__ = [
    "DEFAULT_SYMBOLIC_LIMITS", "MAX_SYMBOLIC_EVIDENCE_BYTES", "MAX_TACTIC_BYTES", "SYMBOLIC_COMMANDS", "SYMBOLIC_SCHEMA",
    "SymbolicCandidatePolicy", "SymbolicConfig", "make_symbolic_policy", "verify_symbolic_evidence",
]
