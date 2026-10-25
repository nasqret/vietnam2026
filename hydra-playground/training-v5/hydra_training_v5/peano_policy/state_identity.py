"""Bounded, conservative identity for opt-in context-renaming search pruning.

This is not a theorem checker or a proof transformer. Keys retain the whole
partial certificate and its DAG sharing, ordered obligations, de Bruijn slots,
and primitive-step count. Only unambiguous surface aliases and fresh hole IDs
are erased. The chosen original proof prefix must still be kernel checked and
independently replayed. Name-sensitive policies need not behave equivalently.

Version one deliberately declines all substitutions/metavariables, unknown
constructors, malformed states, and oversized keys. A declined key means NO
merging, never fallback to goal text. Caches belong to one search/authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from types import MappingProxyType

from peano_lab.engine.proof_reduction import LocalHave, LocalSuffices
from peano_lab.engine.state import Goal, Hole, ProofState, Step
from peano_lab.kernel import formulas as f, proofs as p, terms as t


CONTEXT_ALPHA_V1 = "context-alpha-v1"
MAX_KEY_NODES = 8192
MAX_KEY_BYTES = 64 * 1024
MAX_RETAINED_KEY_BYTES = 8 * 1024**2
MAX_NAME_BYTES = 256
_FORBIDDEN_NAMES = frozenset({"S", "forall", "exists", "bot", "false", "DNE"}
                             | {"PA" + str(i) for i in range(1, 7)})


def search_profile_contract(profile: str | None) -> dict[str, object] | None:
    """Return detached, versioned metadata; None is the untouched legacy mode."""
    if profile is None:
        return None
    if type(profile) is not str or profile != CONTEXT_ALPHA_V1:
        raise ValueError("unknown search profile; expected None or context-alpha-v1")
    record = {
        "schema": "peano-search-state-identity-v1",
        "name": CONTEXT_ALPHA_V1,
        "authority": "one-search; explicit finite commands; no theorem imports",
        "key": "exact native DAG bytes; closed target; ordered goals/context slots; full partial certificate; primitive-step count",
        "renaming": "surface variable/hypothesis aliases and unique proof-hole IDs only",
        "excluded": "nonempty substitutions; any metavariable; ambiguous/reserved names; malformed/unknown ASTs",
        "fallback": "fresh non-merging identity for every declined successor",
        "representative": "existing literal-goal priority; retain one original snapshot and command path verbatim",
        "priority": "goal count, literal goal-text length, proposal rank, parent rank, original commands",
        "transcript": "unchanged literal goals, state_sha256, proposals and commands",
        "max_key_nodes": MAX_KEY_NODES,
        "max_key_bytes": MAX_KEY_BYTES,
        "max_retained_key_bytes": MAX_RETAINED_KEY_BYTES,
        "max_name_bytes": MAX_NAME_BYTES,
        "model_behavior_equivalence_claimed": False,
        "proof_acceptance": "unchanged original-goal kernel check and Hydra fresh replay",
    }
    raw = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return {**record, "contract_sha256": hashlib.sha256(raw).hexdigest()}


@dataclass(frozen=True, slots=True)
class StateIdentityReport:
    key_attempts: int
    keys_built: int
    keys_declined: int
    duplicate_states: int
    renamed_states: int
    retained_key_bytes: int
    key_budget_declines: int = 0

    def __post_init__(self) -> None:
        counters = self.counters()
        if any(type(value) is not int or value < 0 for value in counters.values()):
            raise ValueError("state identity counters must be non-negative integers")
        if (self.keys_built + self.keys_declined != self.key_attempts
            or self.renamed_states > self.duplicate_states
            or self.duplicate_states > self.keys_built
            or self.key_budget_declines > self.keys_declined
            or self.retained_key_bytes > MAX_RETAINED_KEY_BYTES):
            raise ValueError("inconsistent state identity counters")

    @property
    def profile(self) -> str:
        return CONTEXT_ALPHA_V1

    def counters(self) -> dict[str, int]:
        return {name: getattr(self, name) for name in (
            "key_attempts", "keys_built", "keys_declined", "duplicate_states",
            "renamed_states", "retained_key_bytes", "key_budget_declines",
        )}

    def to_dict(self) -> dict[str, object]:
        return {"contract": search_profile_contract(self.profile), "counters": self.counters()}


# Explicit grammar, including the TWO distinct engine-local scheduling nodes.
# No dataclass reflection, subclass acceptance, AST __hash__, or recursive walk.
# Child domains: t=term, f=formula, p=proof; n=natural scalar, s=fixed axiom.
_GRAMMAR = {
    t.Var: ("t", (("index", "n"),)), t.Zero: ("t", ()),
    t.Succ: ("t", (("term", "t"),)),
    t.Add: ("t", (("left", "t"), ("right", "t"))),
    t.Mul: ("t", (("left", "t"), ("right", "t"))),
    f.Eq: ("f", (("left", "t"), ("right", "t"))), f.Bot: ("f", ()),
    f.Imp: ("f", (("antecedent", "f"), ("consequent", "f"))),
    f.And: ("f", (("left", "f"), ("right", "f"))),
    f.Or: ("f", (("left", "f"), ("right", "f"))),
    f.Forall: ("f", (("body", "f"),)), f.Exists: ("f", (("body", "f"),)),
    Hole: ("p", (("id", "n"),)), p.Hyp: ("p", (("i", "n"),)),
    p.ImpIntro: ("p", (("body", "p"),)),
    p.ImpElim: ("p", (("f", "p"), ("a", "p"))),
    p.Cut: ("p", (("proposition", "f"), ("conclusion", "f"), ("lemma", "p"), ("body", "p"))),
    p.AndIntro: ("p", (("left", "p"), ("right", "p"))),
    p.AndElimL: ("p", (("pair", "p"),)), p.AndElimR: ("p", (("pair", "p"),)),
    p.OrIntroL: ("p", (("proof", "p"),)), p.OrIntroR: ("p", (("proof", "p"),)),
    p.OrElim: ("p", (("disjunction", "p"), ("left_case", "p"), ("right_case", "p"))),
    p.BotElim: ("p", (("absurdity", "p"),)),
    p.ForallIntro: ("p", (("body", "p"),)),
    p.ForallElim: ("p", (("p", "p"), ("t", "t"))),
    p.ExistsIntro: ("p", (("t", "t"), ("p", "p"))),
    p.ExistsElim: ("p", (("p", "p"), ("body", "p"))),
    p.EqRefl: ("p", (("t", "t"),)), p.EqSym: ("p", (("proof", "p"),)),
    p.EqTrans: ("p", (("first", "p"), ("second", "p"))),
    p.CongS: ("p", (("proof", "p"),)),
    p.CongAdd: ("p", (("left", "p"), ("right", "p"))),
    p.CongMul: ("p", (("left", "p"), ("right", "p"))),
    p.EqSubst: ("p", (("motive", "f"), ("eq_proof", "p"), ("body_proof", "p"))),
    p.DNE: ("p", (("proposition", "f"),)), p.Axiom: ("p", (("name", "s"),)),
    p.Ind: ("p", (("motive", "f"), ("base", "p"), ("step", "p"))),
    LocalHave: ("p", (("proposition", "f"), ("proof", "p"), ("body", "p"))),
    LocalSuffices: ("p", (("proposition", "f"), ("body", "p"), ("proof", "p"))),
}
_GRAMMAR_IDENTITIES = {id(constructor): (constructor, grammar) for constructor, grammar in _GRAMMAR.items()}


class _Declined(ValueError):
    pass


def _need(condition: bool) -> None:
    if not condition:
        raise _Declined("state is outside the conservative identity profile")


class _Graph:
    def __init__(self, max_nodes: int, max_bytes: int):
        self.max_nodes, self.max_bytes = max_nodes, max_bytes
        self.work = self.encoded_bytes = 0
        self.records: list[list[object]] = []
        self.memo: dict[int, tuple[object, int, int, int]] = {}
        self.active: set[int] = set()
        self.holes: dict[int, int] = {}

    def charge(self, count: int = 1) -> None:
        self.work += count
        _need(self.work <= self.max_nodes)

    def add(self, root: object, domain: str) -> tuple[int, int, int]:
        # Memo values: original object (prevents ID reuse), record index,
        # expanded hole count, and minimum ambient term-variable slots needed.
        stack = [(root, domain, False)]
        while stack:
            node, expected, finishing = stack.pop()
            # ID lookup avoids invoking __hash__/__eq__ on an unknown class's
            # custom metaclass; the retained exact class prevents ID reuse.
            descriptor = _GRAMMAR_IDENTITIES.get(id(type(node)))
            _need(descriptor is not None and descriptor[0] is type(node))
            grammar = descriptor[1]
            _need(grammar[0] == expected)
            identity = id(node)
            if not finishing and identity in self.memo:
                _need(self.memo[identity][0] is node)
                continue
            fields = grammar[1]
            if not finishing:
                _need(identity not in self.active)
                self.charge()
                self.active.add(identity)
                stack.append((node, expected, True))
                for name, child_domain in reversed(fields):
                    child = getattr(node, name)
                    if child_domain in ("t", "f", "p"):
                        stack.append((child, child_domain, False))
                continue
            record: list[object] = [expected, type(node).__name__]
            hole_count = 1 if type(node) is Hole else 0
            required_slots = 0
            for name, child_domain in fields:
                child = getattr(node, name)
                if child_domain in ("t", "f", "p"):
                    retained, reference, holes, slots = self.memo[id(child)]
                    _need(retained is child)
                    record.append(["ref", reference])
                    hole_count += holes
                    required_slots = max(required_slots, slots)
                elif child_domain == "n":
                    _need(type(child) is int and 0 <= child < 2**63)
                    if type(node) is Hole:
                        _need(child not in self.holes)
                        self.holes[child] = len(self.holes)
                        child = self.holes[child]
                    elif type(node) is t.Var:
                        required_slots = child + 1
                    record.append(["int", child])
                else:
                    _need(type(child) is str and child in {"PA" + str(i) for i in range(1, 7)})
                    record.append(["axiom", child])
            if type(node) in (f.Forall, f.Exists):
                required_slots = max(0, required_slots - 1)
            _need(hole_count <= self.max_nodes)
            # Accounting the small fixed-arity records bounds allocation before
            # constructing the complete JSON key; no hash-only equality is used.
            self.encoded_bytes += len(json.dumps(record, separators=(",", ":"), ensure_ascii=True)) + 1
            _need(self.encoded_bytes <= self.max_bytes)
            self.memo[identity] = (node, len(self.records), hole_count, required_slots)
            self.records.append(record)
            self.active.remove(identity)
        _, reference, holes, slots = self.memo[id(root)]
        return reference, holes, slots


def _valid_names(names: tuple[str, ...]) -> bool:
    if any(type(name) is not str or not name or len(name) > MAX_NAME_BYTES for name in names):
        return False
    if len(set(names)) != len(names):
        return False
    return all(
        len(name.encode("utf-8")) <= MAX_NAME_BYTES
        and name not in _FORBIDDEN_NAMES
        and (name[0].isalpha() or name[0] == "_")
        and all(char.isalnum() or char in "_'" for char in name[1:])
        for name in names
    )


def context_alpha_key(
    state: ProofState, *, max_nodes: int = MAX_KEY_NODES, max_key_bytes: int = MAX_KEY_BYTES,
) -> bytes | None:
    """Exact bounded DAG key, or None to leave this state unmerged.

    Limits may be lowered for diagnostics, never raised beyond this profile.
    This key carries no proof authority and must only be used within a single
    search with a fixed original theorem, finite no-import surface and logic.
    """
    if (type(max_nodes) is not int or not 1 <= max_nodes <= MAX_KEY_NODES
        or type(max_key_bytes) is not int or not 1 <= max_key_bytes <= MAX_KEY_BYTES):
        raise ValueError("context-alpha key limits must be positive integers within the versioned bounds")
    try:
        _need(type(state) is ProofState and type(state.variables) is tuple and not state.variables)
        _need(type(state.subst) is MappingProxyType and not state.subst)
        _need(type(state.goals) is tuple and 0 < len(state.goals) <= max_nodes)
        _need(type(state.history) is tuple and len(state.history) <= max_nodes)
        _need(all(type(step) is Step for step in state.history))
        graph = _Graph(max_nodes, max_key_bytes)
        graph.charge(len(state.history) + len(state.goals))
        target, _, slots = graph.add(state.target, "f")
        _need(slots == 0)
        partial, hole_count, _ = graph.add(state.partial, "p")
        _need(hole_count == len(graph.holes) == len(state.goals))
        obligations = []
        for goal in state.goals:
            _need(type(goal) is Goal and type(goal.variables) is tuple and type(goal.context) is tuple)
            _need(len(goal.variables) + len(goal.context) <= max_nodes)
            graph.charge(len(goal.variables) + len(goal.context))
            _need(all(type(entry) is tuple and len(entry) == 2 for entry in goal.context))
            names = goal.variables + tuple(entry[0] for entry in goal.context)
            _need(_valid_names(names))
            formulas = []
            for formula in tuple(entry[1] for entry in goal.context) + (goal.target,):
                reference, holes, needed = graph.add(formula, "f")
                _need(holes == 0 and needed <= len(goal.variables))
                formulas.append(reference)
            obligations.append([len(goal.variables), formulas[:-1], formulas[-1]])
        value = [CONTEXT_ALPHA_V1, len(state.history), target, partial, obligations, graph.records]
        raw = json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("ascii")
        _need(len(raw) <= max_key_bytes)
        return raw
    except (_Declined, AttributeError, TypeError, ValueError, OverflowError):
        return None


__all__ = [
    "CONTEXT_ALPHA_V1", "MAX_KEY_NODES", "MAX_KEY_BYTES", "MAX_RETAINED_KEY_BYTES",
    "StateIdentityReport", "context_alpha_key", "search_profile_contract",
]
