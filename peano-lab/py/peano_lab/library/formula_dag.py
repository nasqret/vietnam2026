"""Audited formula sharing without extending the trusted Peano kernel.

The kernel still receives ordinary, frozen :class:`Formula` and :class:`Term`
objects.  This module only interns identical de Bruijn syntax, records a
self-contained topological DAG, and optionally shares repeated hygienic
definition expansions.  Neither an object identity nor a digest proves a
formula: every serialized edge resolves to an earlier node in the same DAG.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from ..kernel.formulas import And, Bot, Eq, Exists, Forall, Formula, Imp, Or
from ..kernel.terms import (
    Add,
    Mul,
    ParseError,
    Succ,
    Term,
    Var,
    Zero,
    _is_identifier,
    _parse_term_from,
)
from . import defined_syntax


FORMULA_DAG_FORMAT = "peano-lab-formula-dag-v1"
DEFAULT_MAX_UNIQUE_NODES = 100_000
DEFAULT_MAX_STRUCTURAL_OCCURRENCES = 5_000_000
DEFAULT_MAX_DEPTH = 512

_TERM_KINDS = frozenset({"var", "zero", "succ", "add", "mul"})
_FORMULA_KINDS = frozenset(
    {"eq", "bot", "imp", "and", "or", "forall", "exists"}
)


class FormulaDagError(ValueError):
    """A formula DAG or shared expansion violates its strict local contract."""


@dataclass(frozen=True, slots=True)
class FormulaDagNode:
    """One constructor and references to strictly earlier local nodes."""

    kind: str
    children: tuple[int, ...] = ()
    index: int | None = None


@dataclass(frozen=True, slots=True)
class FormulaDagMetrics:
    """Distinguish actual DAG size from its ordinary expanded tree size."""

    unique_nodes: int
    structural_occurrences: int
    maximum_depth: int
    reused_edges: int


@dataclass(frozen=True, slots=True)
class FormulaDag:
    """A complete, local, topologically ordered formula and term DAG."""

    nodes: tuple[FormulaDagNode, ...]
    root: int

    def expand(self) -> Formula:
        """Reconstruct exact ordinary core AST values with their sharing."""

        if type(self.nodes) is not tuple or not self.nodes:
            raise FormulaDagError("formula DAG requires a nonempty node tuple")
        if type(self.root) is not int or self.root != len(self.nodes) - 1:
            raise FormulaDagError("canonical formula DAG root must be its final node")

        values: list[Formula | Term] = []
        seen_keys: set[tuple[str, tuple[int, ...], int | None]] = set()
        for node_id, node in enumerate(self.nodes):
            if type(node) is not FormulaDagNode:
                raise FormulaDagError("DAG nodes must be exact FormulaDagNode values")
            if type(node.kind) is not str or type(node.children) is not tuple:
                raise FormulaDagError("DAG constructor and edges have invalid types")
            if not all(type(edge) is int and 0 <= edge < node_id for edge in node.children):
                raise FormulaDagError("DAG edges must point strictly backward")
            key = (node.kind, node.children, node.index)
            if key in seen_keys:
                raise FormulaDagError("duplicate structural DAG nodes are not canonical")
            seen_keys.add(key)
            children = tuple(values[edge] for edge in node.children)
            values.append(_construct_node(node.kind, children, node.index))

        result = values[self.root]
        if not isinstance(result, Formula):
            raise FormulaDagError("DAG root must be an ordinary core formula")
        reachable: set[int] = set()
        pending = [self.root]
        while pending:
            node_id = pending.pop()
            if node_id in reachable:
                continue
            reachable.add(node_id)
            pending.extend(self.nodes[node_id].children)
        if len(reachable) != len(self.nodes):
            raise FormulaDagError("canonical formula DAG contains unreachable nodes")
        return result

    def metrics(self) -> FormulaDagMetrics:
        """Compute tree metrics once per node, never by expanding all paths."""

        self.expand()
        occurrences: list[int] = []
        depths: list[int] = []
        indegrees = [0] * len(self.nodes)
        for node in self.nodes:
            occurrences.append(1 + sum(occurrences[edge] for edge in node.children))
            depths.append(1 + max((depths[edge] for edge in node.children), default=0))
            for edge in node.children:
                indegrees[edge] += 1
        return FormulaDagMetrics(
            unique_nodes=len(self.nodes),
            structural_occurrences=occurrences[self.root],
            maximum_depth=depths[self.root],
            reused_edges=sum(max(0, degree - 1) for degree in indegrees),
        )

    def to_record(self) -> list[Any]:
        """Return inert tagged arrays, never Python objects or trusted hashes."""

        self.expand()
        encoded: list[list[Any]] = []
        for node in self.nodes:
            if node.kind == "var":
                encoded.append(["var", node.index])
            else:
                encoded.append([node.kind, *node.children])
        return [FORMULA_DAG_FORMAT, self.root, encoded]

    def to_json(self) -> str:
        """Canonical exact-byte JSON, with exactly one trailing newline."""

        return json.dumps(
            self.to_record(),
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        ) + "\n"

    @classmethod
    def from_record(
        cls,
        record: object,
        *,
        max_unique_nodes: int = DEFAULT_MAX_UNIQUE_NODES,
    ) -> FormulaDag:
        """Decode exact-arity constructor arrays and validate every local edge."""

        if (
            type(record) is not list
            or len(record) != 3
            or record[0] != FORMULA_DAG_FORMAT
            or type(record[1]) is not int
            or type(record[2]) is not list
        ):
            raise FormulaDagError("invalid formula DAG envelope")
        if not record[2] or len(record[2]) > max_unique_nodes:
            raise FormulaDagError("formula DAG exceeds its unique-node limit")
        decoded: list[FormulaDagNode] = []
        for item in record[2]:
            if type(item) is not list or not item or type(item[0]) is not str:
                raise FormulaDagError("formula DAG nodes must be tagged arrays")
            if item[0] == "var":
                if len(item) != 2:
                    raise FormulaDagError("variable node has invalid arity")
                decoded.append(FormulaDagNode("var", (), item[1]))
            else:
                decoded.append(FormulaDagNode(item[0], tuple(item[1:])))
        dag = cls(tuple(decoded), record[1])
        dag.expand()
        return dag

    @classmethod
    def from_json(
        cls,
        payload: str,
        *,
        max_unique_nodes: int = DEFAULT_MAX_UNIQUE_NODES,
    ) -> FormulaDag:
        """Reject alternate spacing, number spellings, and trailing payload."""

        if type(payload) is not str:
            raise FormulaDagError("formula DAG payload must be text")
        try:
            record = json.loads(payload)
        except (TypeError, ValueError) as exc:
            raise FormulaDagError("invalid formula DAG JSON") from exc
        dag = cls.from_record(record, max_unique_nodes=max_unique_nodes)
        if dag.to_json() != payload:
            raise FormulaDagError("formula DAG JSON is not canonical")
        return dag


def _construct_node(
    kind: str,
    children: tuple[Formula | Term, ...],
    index: int | None,
) -> Formula | Term:
    if kind == "var":
        if children or type(index) is not int or index < 0:
            raise FormulaDagError("variable node needs one nonnegative index")
        return Var(index)
    if index is not None:
        raise FormulaDagError("only variable nodes carry an index")
    if kind == "zero":
        if children:
            raise FormulaDagError("zero node cannot have edges")
        return Zero()
    if kind == "bot":
        if children:
            raise FormulaDagError("falsity node cannot have edges")
        return Bot()
    if kind == "succ":
        if len(children) != 1 or not isinstance(children[0], Term):
            raise FormulaDagError("successor needs exactly one term")
        return Succ(children[0])
    if kind in {"add", "mul"}:
        if len(children) != 2 or not all(isinstance(child, Term) for child in children):
            raise FormulaDagError("arithmetic node needs exactly two terms")
        return (Add if kind == "add" else Mul)(children[0], children[1])
    if kind == "eq":
        if len(children) != 2 or not all(isinstance(child, Term) for child in children):
            raise FormulaDagError("equality node needs exactly two terms")
        return Eq(children[0], children[1])
    if kind in {"imp", "and", "or"}:
        if len(children) != 2 or not all(
            isinstance(child, Formula) for child in children
        ):
            raise FormulaDagError("logical connective needs exactly two formulas")
        return {"imp": Imp, "and": And, "or": Or}[kind](children[0], children[1])
    if kind in {"forall", "exists"}:
        if len(children) != 1 or not isinstance(children[0], Formula):
            raise FormulaDagError("quantifier needs exactly one formula")
        return (Forall if kind == "forall" else Exists)(children[0])
    raise FormulaDagError(f"unknown formula DAG constructor {kind!r}")


def _node_parts(value: object) -> tuple[str, tuple[object, ...], int | None]:
    if type(value) is Var:
        if type(value.index) is not int or value.index < 0:
            raise FormulaDagError("variable index must be a nonnegative integer")
        return "var", (), value.index
    if type(value) is Zero:
        return "zero", (), None
    if type(value) is Succ:
        return "succ", (value.term,), None
    if type(value) is Add:
        return "add", (value.left, value.right), None
    if type(value) is Mul:
        return "mul", (value.left, value.right), None
    if type(value) is Eq:
        return "eq", (value.left, value.right), None
    if type(value) is Bot:
        return "bot", (), None
    if type(value) is Imp:
        return "imp", (value.left, value.right), None
    if type(value) is And:
        return "and", (value.left, value.right), None
    if type(value) is Or:
        return "or", (value.left, value.right), None
    if type(value) is Forall:
        return "forall", (value.body,), None
    if type(value) is Exists:
        return "exists", (value.body,), None
    raise FormulaDagError("only exact Peano kernel constructors can be interned")


class FormulaArena:
    """Per-invocation structural hash-consing with strong identity references."""

    def __init__(
        self,
        *,
        max_unique_nodes: int = DEFAULT_MAX_UNIQUE_NODES,
        max_depth: int = DEFAULT_MAX_DEPTH,
    ):
        if type(max_unique_nodes) is not int or max_unique_nodes <= 0:
            raise FormulaDagError("unique-node limit must be a positive integer")
        if type(max_depth) is not int or max_depth <= 0:
            raise FormulaDagError("depth limit must be a positive integer")
        self.max_unique_nodes = max_unique_nodes
        self.max_depth = max_depth
        self._nodes: list[FormulaDagNode] = []
        self._values: list[Formula | Term] = []
        self._structural: dict[tuple[str, tuple[int, ...], int | None], int] = {}
        self._identity: dict[int, tuple[object, int]] = {}

    def _remember(self, original: object, node_id: int) -> None:
        self._identity[id(original)] = (original, node_id)

    def _existing(self, value: object) -> int | None:
        entry = self._identity.get(id(value))
        return entry[1] if entry is not None and entry[0] is value else None

    def _intern(self, root: object) -> int:
        pending: list[tuple[object, bool, int]] = [(root, False, 1)]
        active: set[int] = set()
        while pending:
            value, finished, depth = pending.pop()
            if depth > self.max_depth:
                raise FormulaDagError("formula DAG exceeds its nesting-depth limit")
            existing = self._existing(value)
            if existing is not None:
                continue
            identity = id(value)
            kind, children, index = _node_parts(value)
            if not finished:
                if identity in active:
                    raise FormulaDagError("cyclic Python syntax cannot form a DAG")
                active.add(identity)
                pending.append((value, True, depth))
                pending.extend((child, False, depth + 1) for child in reversed(children))
                continue
            active.remove(identity)
            child_ids: list[int] = []
            for child in children:
                child_id = self._existing(child)
                if child_id is None:
                    raise FormulaDagError("a child was not interned before its parent")
                child_ids.append(child_id)
            key = (kind, tuple(child_ids), index)
            node_id = self._structural.get(key)
            if node_id is None:
                if len(self._nodes) >= self.max_unique_nodes:
                    raise FormulaDagError("formula DAG exceeds its unique-node limit")
                node_id = len(self._nodes)
                shared_children = tuple(self._values[child] for child in child_ids)
                canonical = _construct_node(kind, shared_children, index)
                self._nodes.append(FormulaDagNode(kind, tuple(child_ids), index))
                self._values.append(canonical)
                self._structural[key] = node_id
                self._remember(canonical, node_id)
            self._remember(value, node_id)
        result = self._existing(root)
        if result is None:
            raise FormulaDagError("formula interning failed")
        return result

    def intern_term(self, term: Term) -> Term:
        node_id = self._intern(term)
        result = self._values[node_id]
        if not isinstance(result, Term):
            raise FormulaDagError("expected a core term")
        return result

    def intern_formula(self, formula: Formula) -> Formula:
        node_id = self._intern(formula)
        result = self._values[node_id]
        if not isinstance(result, Formula):
            raise FormulaDagError("expected a core formula")
        return result

    def term_id(self, term: Term) -> int:
        result = self._intern(term)
        if not isinstance(self._values[result], Term):
            raise FormulaDagError("expected a core term")
        return result

    def freeze(self, formula: Formula) -> FormulaDag:
        """Emit only nodes reachable from this root, preserving local order."""

        root = self._intern(formula)
        if not isinstance(self._values[root], Formula):
            raise FormulaDagError("formula DAG root must be a core formula")
        reachable: set[int] = set()
        pending = [root]
        while pending:
            node_id = pending.pop()
            if node_id in reachable:
                continue
            reachable.add(node_id)
            pending.extend(self._nodes[node_id].children)
        old_ids = sorted(reachable)
        remap = {old: new for new, old in enumerate(old_ids)}
        nodes = tuple(
            FormulaDagNode(
                self._nodes[old].kind,
                tuple(remap[child] for child in self._nodes[old].children),
                self._nodes[old].index,
            )
            for old in old_ids
        )
        return FormulaDag(nodes, remap[root])


@dataclass(frozen=True, slots=True)
class SharedDefinedFormula:
    """Exact expanded core formula plus auditable definition-sharing evidence."""

    formula: Formula
    free_names: tuple[str, ...]
    dag: FormulaDag
    definition_calls: int
    definition_cache_hits: int
    unique_expansion_nodes: int


class _SharedDefinedFormulaParser(defined_syntax._DefinedFormulaParser):
    def __init__(self, source: str, expansion_budget: int, arena: FormulaArena):
        super().__init__(source, expansion_budget)
        self.arena = arena
        self.cache: dict[tuple[str, tuple[int, ...]], Formula] = {}
        self.definition_calls = 0
        self.definition_cache_hits = 0

    def _atom(self) -> Formula:
        token = self.stream.peek()
        position = self.stream.position
        is_call = (
            position + 1 < len(self.stream.tokens)
            and self.stream.tokens[position + 1].text == "("
        )
        if not (_is_identifier(token) and token != "S" and is_call):
            return super(defined_syntax._DefinedFormulaParser, self)._atom()

        column = self.stream.column()
        name = self.stream.take()
        definition = defined_syntax.ALL_DEFINITIONS_BY_NAME.get(name)
        if definition is None:
            raise ParseError(f"unknown defined predicate {name!r} at column {column}")
        self.stream.expect("(")
        arguments: list[Term] = []
        if self.stream.accept(")") is None:
            while True:
                argument = _parse_term_from(self.stream, self.bound, self.free)
                arguments.append(self.arena.intern_term(argument))
                if self.stream.accept(")") is not None:
                    break
                self.stream.expect(",")
        if len(arguments) != definition.arity:
            suffix = "argument" if definition.arity == 1 else "arguments"
            raise ParseError(
                f"defined predicate {name!r} expects {definition.arity} {suffix}, "
                f"got {len(arguments)} at column {column}"
            )

        self.definition_calls += 1
        key = (
            definition.stable_id,
            tuple(self.arena.term_id(argument) for argument in arguments),
        )
        cached = self.cache.get(key)
        if cached is not None:
            # Reusing an exact call still consumes one bounded surface action.
            self.expansion_counter.node(definition, column)
            self.definition_cache_hits += 1
            return cached
        expanded = defined_syntax._instantiate_formula(
            definition.template_formula,
            tuple(arguments),
            0,
            self.expansion_counter,
            definition,
            column,
        )
        canonical = self.arena.intern_formula(expanded)
        self.cache[key] = canonical
        return canonical


def compile_shared_defined_formula(
    source: str,
    *,
    expansion_budget: int = defined_syntax.DEFAULT_EXPANSION_BUDGET,
    max_unique_nodes: int = DEFAULT_MAX_UNIQUE_NODES,
    max_structural_occurrences: int = DEFAULT_MAX_STRUCTURAL_OCCURRENCES,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> SharedDefinedFormula:
    """Expand definitions hygienically once and retain exactly equivalent AST."""

    if type(max_structural_occurrences) is not int or max_structural_occurrences <= 0:
        raise FormulaDagError("structural occurrence limit must be a positive integer")
    arena = FormulaArena(max_unique_nodes=max_unique_nodes, max_depth=max_depth)
    parser = _SharedDefinedFormulaParser(source, expansion_budget, arena)
    formula = arena.intern_formula(parser.parse())
    dag = arena.freeze(formula)
    metrics = dag.metrics()
    if metrics.structural_occurrences > max_structural_occurrences:
        raise FormulaDagError("expanded formula exceeds its structural occurrence limit")
    if metrics.maximum_depth > max_depth:
        raise FormulaDagError("expanded formula exceeds its nesting-depth limit")
    return SharedDefinedFormula(
        formula=formula,
        free_names=tuple(parser.free),
        dag=dag,
        definition_calls=parser.definition_calls,
        definition_cache_hits=parser.definition_cache_hits,
        unique_expansion_nodes=parser.expansion_counter.used,
    )


def parse_shared_defined_formula(source: str, **kwargs: Any) -> Formula:
    """Compatible opt-in parser returning only the exact ordinary core AST."""

    return compile_shared_defined_formula(source, **kwargs).formula


def parse_shared_defined_formula_with_names(
    source: str, **kwargs: Any
) -> tuple[Formula, tuple[str, ...]]:
    """Compatible opt-in parser retaining first-occurrence free names."""

    result = compile_shared_defined_formula(source, **kwargs)
    return result.formula, result.free_names


__all__ = [
    "DEFAULT_MAX_DEPTH",
    "DEFAULT_MAX_STRUCTURAL_OCCURRENCES",
    "DEFAULT_MAX_UNIQUE_NODES",
    "FORMULA_DAG_FORMAT",
    "FormulaArena",
    "FormulaDag",
    "FormulaDagError",
    "FormulaDagMetrics",
    "FormulaDagNode",
    "SharedDefinedFormula",
    "compile_shared_defined_formula",
    "parse_shared_defined_formula",
    "parse_shared_defined_formula_with_names",
]
