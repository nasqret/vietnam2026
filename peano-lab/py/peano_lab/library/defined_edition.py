"""A conservative, definition-aware reading edition of the QR library.

The ordinary Peano Lab library deliberately stores only formulas in the
kernel's first-order language.  This module builds a second *surface* edition:
reviewed formula patterns are printed as calls such as ``Dvd(d,n)`` and
``Prime(p)``.  Every call is expanded again by :mod:`defined_syntax` before a
surface theorem is converted back to an ordinary :class:`TheoremSpec`.

Nothing in this module is trusted by the kernel.  In particular, it adds no
formula constructor, proof constructor, theorem-name environment, or axiom.
The equivalence receipts below compare the expanded and original de Bruijn
ASTs exactly.  The adapter is intentionally separate from the public theorem
registry so the frozen explicit library and model identities do not change.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import inspect
import json
from pathlib import Path
import re
from types import MappingProxyType

from peano_lab.kernel.formulas import (
    And,
    Bot,
    Eq,
    Exists,
    Forall,
    Formula,
    Imp,
    Or,
    _as_le,
    _fresh_binder,
    parse_formula_in_context,
    parse_formula_with_names,
    pretty_formula,
)
from peano_lab.kernel.terms import (
    Add,
    Mul,
    Succ,
    Term,
    Var,
    Zero,
    _TokenStream,
    _is_identifier,
    _pretty_term,
)

from .defined_syntax import (
    DEFINITIONS,
    DEFINED_SYNTAX_REGISTRY_SHA256,
    DefinitionSpec,
    parse_defined_formula_in_context,
    parse_defined_formula_with_names,
)
from .quadratic_reciprocity_stack_runtime import quadratic_reciprocity_stack
from .theorems import TheoremSpec


DEFINED_EDITION_SCHEMA = "peano-lab-defined-edition-v1"
# Large QR statements contain many independent surface calls.  This is a
# denial-of-service guard, not a proof-size or kernel limit.
DEFINED_EDITION_EXPANSION_BUDGET = 4_000_000

_SOURCE_PATH = Path(__file__).resolve()
_REPO_ROOT = _SOURCE_PATH.parents[4]
_SYNTAX_SOURCE = Path(inspect.getsourcefile(DefinitionSpec) or "").resolve()
_SYNTAX_SOURCE_RELATIVE = _SYNTAX_SOURCE.relative_to(_REPO_ROOT).as_posix()
_SYNTAX_SOURCE_SHA256 = sha256(_SYNTAX_SOURCE.read_bytes()).hexdigest()


class DefinedEditionError(ValueError):
    """A defined surface failed its exact conservative-expansion contract."""


@dataclass(frozen=True, slots=True)
class SurfacePart:
    """One plain-text or linked-definition span in a compact formula."""

    kind: str
    text: str
    definition_id: str | None = None

    def __post_init__(self) -> None:
        if self.kind not in {"text", "definition"} or not self.text:
            raise DefinedEditionError("surface parts need a valid kind and nonempty text")
        if (self.kind == "definition") != (self.definition_id is not None):
            raise DefinedEditionError("only definition parts carry a definition ID")

    def as_json(self) -> dict[str, str]:
        if self.kind == "text":
            return {"kind": "text", "text": self.text}
        assert self.definition_id is not None
        return {
            "kind": "definition",
            "definition": self.definition_id,
            "text": self.text,
        }


@dataclass(frozen=True, slots=True)
class DefinitionUse:
    """The number of syntactic calls to one definition in a surface."""

    definition_id: str
    name: str
    occurrences: int


@dataclass(frozen=True, slots=True)
class EquivalenceReceipt:
    """Content receipts for one exact AST-preserving compaction."""

    expanded_source_sha256: str
    defined_source_sha256: str
    canonical_expansion_sha256: str
    free_names: tuple[str, ...]
    definition_uses: tuple[DefinitionUse, ...]
    expanded_characters: int
    defined_characters: int
    exact_ast_equivalence: bool


@dataclass(frozen=True, slots=True)
class FormulaCompaction:
    """A compact formula plus its display spans and expansion receipt."""

    expanded_source: str
    defined_source: str
    parts: tuple[SurfacePart, ...]
    receipt: EquivalenceReceipt


@dataclass(frozen=True, slots=True)
class TacticCompaction:
    """One tactic command, compacting only a local proposition if present."""

    line_number: int
    tactic: str
    expanded_command: str
    defined_command: str
    parts: tuple[SurfacePart, ...]
    local_name: str | None
    proposition: FormulaCompaction | None


@dataclass(frozen=True, slots=True)
class DefinedTheoremSpec:
    """A theorem specification whose statement/local formulas use definitions."""

    name: str
    statement: str
    dependencies: tuple[str, ...]
    script: tuple[str, ...]
    summary: str


@dataclass(frozen=True, slots=True)
class DefinedTheoremRecord:
    """The two editions and all local equivalence receipts for one theorem."""

    scope: str
    expanded_spec: TheoremSpec
    defined_spec: DefinedTheoremSpec
    compiled_spec: TheoremSpec
    statement: FormulaCompaction
    tactics: tuple[TacticCompaction, ...]
    definition_uses: tuple[DefinitionUse, ...]


@dataclass(frozen=True, slots=True)
class DefinedEditionMetrics:
    """Aggregate size and coverage measurements for the exact QR closure."""

    theorem_count: int
    public_theorem_count: int
    candidate_theorem_count: int
    tactic_line_count: int
    local_statement_count: int
    changed_theorem_statement_count: int
    changed_local_statement_count: int
    expanded_statement_characters: int
    defined_statement_characters: int
    expanded_local_statement_characters: int
    defined_local_statement_characters: int
    definition_occurrences: tuple[DefinitionUse, ...]
    longest_expanded_statement: tuple[str, int]
    longest_defined_statement: tuple[str, int]
    longest_expanded_local_statement: tuple[str, int, int]
    longest_defined_local_statement: tuple[str, int, int]


@dataclass(frozen=True, slots=True)
class DefinedLibraryEdition:
    """Immutable defined edition of the exact 557-node QR dependency closure."""

    schema: str
    registry_sha256: str
    records: tuple[DefinedTheoremRecord, ...]
    by_name: Mapping[str, DefinedTheoremRecord]
    metrics: DefinedEditionMetrics


_PD_ID = re.compile(r"^PD[0-9A-Y]{4}$")


def _definition_id(definition: DefinitionSpec) -> str:
    if not _PD_ID.fullmatch(definition.stable_id):
        raise DefinedEditionError(
            f"definition {definition.name!r} has invalid persistent explorer ID "
            f"{definition.stable_id!r}"
        )
    return definition.stable_id


def _term_nodes(term: Term) -> int:
    if isinstance(term, (Var, Zero)):
        return 1
    if isinstance(term, Succ):
        return 1 + _term_nodes(term.term)
    if isinstance(term, (Add, Mul)):
        return 1 + _term_nodes(term.left) + _term_nodes(term.right)
    raise TypeError("expected a PA term")


def _formula_nodes(formula: Formula) -> int:
    if isinstance(formula, Eq):
        return 1 + _term_nodes(formula.left) + _term_nodes(formula.right)
    if isinstance(formula, Bot):
        return 1
    if isinstance(formula, (Imp, And, Or)):
        return 1 + _formula_nodes(formula.left) + _formula_nodes(formula.right)
    if isinstance(formula, (Forall, Exists)):
        return 1 + _formula_nodes(formula.body)
    raise TypeError("expected a PA formula")


# Prefer the largest reviewed abstraction at an overlapping root.  Registry
# order breaks equal-size ties and is itself covered by the registry digest.
_MATCH_ORDER = tuple(
    sorted(
        enumerate(DEFINITIONS),
        key=lambda item: (-_formula_nodes(item[1].template_formula), item[0]),
    )
)
_MATCH_BY_ROOT: Mapping[type[Formula], tuple[DefinitionSpec, ...]] = MappingProxyType(
    {
        root: tuple(
            definition
            for _, definition in _MATCH_ORDER
            if type(definition.template_formula) is root
        )
        for root in {type(item.template_formula) for item in DEFINITIONS}
    }
)


def _drop_template_binders(term: Term, depth: int) -> tuple[bool, Term | None]:
    """Lower a target argument out of binders introduced by a template."""

    if isinstance(term, Var):
        if term.index < depth:
            return False, None
        return True, Var(term.index - depth)
    if isinstance(term, Zero):
        return True, term
    if isinstance(term, Succ):
        valid, child = _drop_template_binders(term.term, depth)
        return (True, Succ(child)) if valid and child is not None else (False, None)
    if isinstance(term, (Add, Mul)):
        left_valid, left = _drop_template_binders(term.left, depth)
        right_valid, right = _drop_template_binders(term.right, depth)
        if not left_valid or not right_valid or left is None or right is None:
            return False, None
        return True, type(term)(left, right)
    raise TypeError("expected a PA term")


def _match_term(
    pattern: Term,
    target: Term,
    *,
    depth: int,
    arity: int,
    bindings: list[Term | None],
) -> bool:
    if isinstance(pattern, Var):
        if pattern.index < depth:
            return isinstance(target, Var) and target.index == pattern.index
        parameter = pattern.index - depth
        if parameter >= arity:
            return False
        valid, lowered = _drop_template_binders(target, depth)
        if not valid or lowered is None:
            return False
        previous = bindings[parameter]
        if previous is None:
            bindings[parameter] = lowered
            return True
        return previous == lowered
    if type(pattern) is not type(target):
        return False
    if isinstance(pattern, Zero):
        return True
    if isinstance(pattern, Succ):
        assert isinstance(target, Succ)
        return _match_term(
            pattern.term,
            target.term,
            depth=depth,
            arity=arity,
            bindings=bindings,
        )
    if isinstance(pattern, (Add, Mul)):
        assert isinstance(target, (Add, Mul))
        return _match_term(
            pattern.left,
            target.left,
            depth=depth,
            arity=arity,
            bindings=bindings,
        ) and _match_term(
            pattern.right,
            target.right,
            depth=depth,
            arity=arity,
            bindings=bindings,
        )
    raise TypeError("expected a PA term")


def _match_formula(
    pattern: Formula,
    target: Formula,
    *,
    depth: int,
    arity: int,
    bindings: list[Term | None],
) -> bool:
    if type(pattern) is not type(target):
        return False
    if isinstance(pattern, Eq):
        assert isinstance(target, Eq)
        return _match_term(
            pattern.left,
            target.left,
            depth=depth,
            arity=arity,
            bindings=bindings,
        ) and _match_term(
            pattern.right,
            target.right,
            depth=depth,
            arity=arity,
            bindings=bindings,
        )
    if isinstance(pattern, Bot):
        return True
    if isinstance(pattern, (Imp, And, Or)):
        assert isinstance(target, (Imp, And, Or))
        return _match_formula(
            pattern.left,
            target.left,
            depth=depth,
            arity=arity,
            bindings=bindings,
        ) and _match_formula(
            pattern.right,
            target.right,
            depth=depth,
            arity=arity,
            bindings=bindings,
        )
    if isinstance(pattern, (Forall, Exists)):
        assert isinstance(target, (Forall, Exists))
        return _match_formula(
            pattern.body,
            target.body,
            depth=depth + 1,
            arity=arity,
            bindings=bindings,
        )
    raise TypeError("expected a PA formula")


def _definition_match(
    formula: Formula,
) -> tuple[DefinitionSpec, tuple[Term, ...]] | None:
    for definition in _MATCH_BY_ROOT.get(type(formula), ()):
        bindings: list[Term | None] = [None] * definition.arity
        if _match_formula(
            definition.template_formula,
            formula,
            depth=0,
            arity=definition.arity,
            bindings=bindings,
        ) and all(binding is not None for binding in bindings):
            return definition, tuple(binding for binding in bindings if binding is not None)
    return None


def _append_part(
    parts: list[SurfacePart],
    text: str,
    definition_id: str | None = None,
) -> None:
    if not text:
        return
    kind = "definition" if definition_id is not None else "text"
    if kind == "text" and parts and parts[-1].kind == "text":
        previous = parts[-1]
        parts[-1] = SurfacePart("text", previous.text + text)
    else:
        parts.append(SurfacePart(kind, text, definition_id))


def _render_formula_parts(
    formula: Formula,
    names: list[str],
    parent_precedence: int,
    uses: Counter[str],
    leading_binders: list[tuple[type[Formula], str]] | None = None,
) -> list[SurfacePart]:
    match = _definition_match(formula)
    if match is not None:
        definition, arguments = match
        definition_id = _definition_id(definition)
        text = (
            f"{definition.name}("
            + ",".join(_pretty_term(argument, names, 0) for argument in arguments)
            + ")"
        )
        uses[definition.name] += 1
        parts = [SurfacePart("definition", text, definition_id)]
        level = 5
    else:
        le_terms = _as_le(formula)
        if le_terms is not None:
            lower, upper = le_terms
            parts = [
                SurfacePart(
                    "text",
                    f"{_pretty_term(lower, names, 0)} ≤ {_pretty_term(upper, names, 0)}",
                )
            ]
            level = 5
        elif isinstance(formula, Eq):
            parts = [
                SurfacePart(
                    "text",
                    f"{_pretty_term(formula.left, names, 0)} = "
                    f"{_pretty_term(formula.right, names, 0)}",
                )
            ]
            level = 5
        elif isinstance(formula, Bot):
            parts, level = [SurfacePart("text", "⊥")], 5
        elif isinstance(formula, Imp) and isinstance(formula.right, Bot):
            parts = [SurfacePart("text", "¬")]
            for part in _render_formula_parts(formula.left, names, 4, uses):
                _append_part(parts, part.text, part.definition_id)
            level = 4
        elif isinstance(formula, (And, Or, Imp)):
            if isinstance(formula, And):
                level, symbol = 3, "∧"
            elif isinstance(formula, Or):
                level, symbol = 2, "∨"
            else:
                level, symbol = 1, "→"
            parts = _render_formula_parts(
                formula.left,
                names,
                level + (1 if isinstance(formula, Imp) else 0),
                uses,
            )
            _append_part(parts, f" {symbol} ")
            right_level = level if isinstance(formula, Imp) else level + 1
            if isinstance(formula, Imp) and isinstance(formula.right, (Forall, Exists)):
                right_level = 0
            for part in _render_formula_parts(
                formula.right, names, right_level, uses
            ):
                _append_part(parts, part.text, part.definition_id)
        elif isinstance(formula, (Forall, Exists)):
            binder = _fresh_binder(names)
            if leading_binders and leading_binders[0][0] is type(formula):
                _, preferred = leading_binders.pop(0)
                if preferred not in names:
                    binder = preferred
            symbol = "∀" if isinstance(formula, Forall) else "∃"
            parts = [SurfacePart("text", f"{symbol} {binder}. ")]
            for part in _render_formula_parts(
                formula.body,
                [binder] + names,
                0,
                uses,
                leading_binders,
            ):
                _append_part(parts, part.text, part.definition_id)
            level = 0
        else:
            raise TypeError("expected a PA formula")

    if level < parent_precedence:
        wrapped: list[SurfacePart] = [SurfacePart("text", "(")]
        for part in parts:
            _append_part(wrapped, part.text, part.definition_id)
        _append_part(wrapped, ")")
        return wrapped
    return parts


def _uses(counter: Counter[str]) -> tuple[DefinitionUse, ...]:
    return tuple(
        DefinitionUse(_definition_id(definition), definition.name, counter[definition.name])
        for definition in DEFINITIONS
        if counter[definition.name]
    )


def _leading_source_binders(source: str) -> list[tuple[type[Formula], str]]:
    """Read only an unparenthesized leading quantifier chain from the surface."""

    stream = _TokenStream(source)
    result: list[tuple[type[Formula], str]] = []
    while stream.peek() in {"forall", "∀", "exists", "∃"}:
        quantifier = stream.take()
        constructor: type[Formula] = (
            Forall if quantifier in {"forall", "∀"} else Exists
        )
        names: list[str] = []
        while _is_identifier(stream.peek()) and stream.peek() not in {
            "forall",
            "exists",
            "bot",
            "false",
        }:
            names.append(stream.take())
        if not names or stream.accept(".") is None:
            return []
        result.extend((constructor, name) for name in names)
    return result


def compact_formula_source(source: str) -> FormulaCompaction:
    """Compact one explicit formula and prove exact expansion in its name scope."""

    if not isinstance(source, str) or not source.strip():
        raise DefinedEditionError("formula source must be nonempty text")
    expanded_formula, names = parse_formula_with_names(source)
    counter: Counter[str] = Counter()
    parts = tuple(
        _render_formula_parts(
            expanded_formula,
            list(names),
            0,
            counter,
            _leading_source_binders(source),
        )
    )
    if not parts:
        raise DefinedEditionError("formula renderer produced no surface parts")
    if counter:
        defined_source = "".join(part.text for part in parts)
    else:
        # The defined edition is a surgical notation layer, not a global
        # pretty-printing rewrite.  Byte-preserve formulas with no definition
        # use so unrelated theorem statements and tactic lines remain frozen.
        defined_source = source
        parts = (SurfacePart("text", source),)
    expanded_again = parse_defined_formula_in_context(
        defined_source,
        list(names),
        expansion_budget=DEFINED_EDITION_EXPANSION_BUDGET,
    )
    equivalent = expanded_again == expanded_formula
    if not equivalent:
        raise DefinedEditionError("defined formula did not re-expand to its original AST")
    canonical = pretty_formula(expanded_again, list(names))
    receipt = EquivalenceReceipt(
        expanded_source_sha256=sha256(source.encode("utf-8")).hexdigest(),
        defined_source_sha256=sha256(defined_source.encode("utf-8")).hexdigest(),
        canonical_expansion_sha256=sha256(canonical.encode("utf-8")).hexdigest(),
        free_names=names,
        definition_uses=_uses(counter),
        expanded_characters=len(source),
        defined_characters=len(defined_source),
        exact_ast_equivalence=True,
    )
    return FormulaCompaction(source, defined_source, parts, receipt)


def compact_tactic_command(command: str, line_number: int = 1) -> TacticCompaction:
    """Compact only the proposition of ``have``/``suffices`` commands."""

    if not isinstance(command, str) or not command.strip():
        raise DefinedEditionError("tactic command must be nonempty text")
    pieces = command.strip().split(maxsplit=1)
    tactic = pieces[0]
    if tactic not in {"have", "suffices"}:
        return TacticCompaction(
            line_number,
            tactic,
            command,
            command,
            (SurfacePart("text", command),),
            None,
            None,
        )
    args = pieces[1] if len(pieces) == 2 else ""
    name_source, separator, proposition_source = args.partition(":")
    if not separator or not name_source.strip() or not proposition_source.strip():
        raise DefinedEditionError(
            f"malformed {tactic} command on line {line_number}: expected name : proposition"
        )
    proposition = compact_formula_source(proposition_source.strip())
    local_name = name_source.strip()
    if not proposition.receipt.definition_uses:
        return TacticCompaction(
            line_number,
            tactic,
            command,
            command,
            (SurfacePart("text", command),),
            local_name,
            proposition,
        )
    prefix = f"{tactic} {local_name} : "
    parts: list[SurfacePart] = [SurfacePart("text", prefix)]
    for part in proposition.parts:
        _append_part(parts, part.text, part.definition_id)
    defined = "".join(part.text for part in parts)
    return TacticCompaction(
        line_number,
        tactic,
        command,
        defined,
        tuple(parts),
        local_name,
        proposition,
    )


def compile_defined_spec(spec: DefinedTheoremSpec) -> TheoremSpec:
    """Expand a defined theorem to the unchanged ordinary ``TheoremSpec`` type."""

    if type(spec) is not DefinedTheoremSpec:
        raise TypeError("defined theorem compiler needs DefinedTheoremSpec")
    statement_formula, statement_names = parse_defined_formula_with_names(
        spec.statement,
        expansion_budget=DEFINED_EDITION_EXPANSION_BUDGET,
    )
    if statement_names:
        raise DefinedEditionError(
            f"defined theorem {spec.name!r} is not closed: {statement_names!r}"
        )
    statement = pretty_formula(statement_formula, [])
    script: list[str] = []
    for line_number, command in enumerate(spec.script, 1):
        pieces = command.strip().split(maxsplit=1)
        tactic = pieces[0] if pieces else ""
        if tactic not in {"have", "suffices"}:
            script.append(command)
            continue
        args = pieces[1] if len(pieces) == 2 else ""
        name_source, separator, proposition_source = args.partition(":")
        if not separator or not name_source.strip() or not proposition_source.strip():
            raise DefinedEditionError(
                f"malformed {tactic} in {spec.name!r} line {line_number}"
            )
        proposition, names = parse_defined_formula_with_names(
            proposition_source.strip(),
            expansion_budget=DEFINED_EDITION_EXPANSION_BUDGET,
        )
        expanded = pretty_formula(proposition, list(names))
        script.append(f"{tactic} {name_source.strip()} : {expanded}")
    return TheoremSpec(
        spec.name,
        statement,
        spec.dependencies,
        tuple(script),
        spec.summary,
    )


def _same_open_formula(left: str, right: str) -> bool:
    """Compare open formulas by their shared surface-name environment."""

    left_formula, left_names = parse_formula_with_names(left)
    right_formula = parse_formula_in_context(right, list(left_names))
    return left_formula == right_formula


def compact_theorem_spec(spec: TheoremSpec, *, scope: str) -> DefinedTheoremRecord:
    """Build, compile, and verify one definition-aware theorem record."""

    if type(spec) is not TheoremSpec:
        raise TypeError("theorem compactor needs an ordinary TheoremSpec")
    if scope not in {"public", "candidate"}:
        raise DefinedEditionError("theorem scope must be public or candidate")
    statement = compact_formula_source(spec.statement)
    tactics = tuple(
        compact_tactic_command(command, line_number)
        for line_number, command in enumerate(spec.script, 1)
    )
    defined = DefinedTheoremSpec(
        spec.name,
        statement.defined_source,
        spec.dependencies,
        tuple(item.defined_command for item in tactics),
        spec.summary,
    )
    compiled = compile_defined_spec(defined)
    if parse_formula_with_names(compiled.statement)[0] != parse_formula_with_names(
        spec.statement
    )[0]:
        raise DefinedEditionError(
            f"compiled statement for {spec.name!r} differs from the explicit AST"
        )
    total: Counter[str] = Counter(
        {
            use.name: use.occurrences
            for use in statement.receipt.definition_uses
        }
    )
    for original_command, compiled_command, tactic_record in zip(
        spec.script, compiled.script, tactics, strict=True
    ):
        if tactic_record.proposition is None:
            if original_command != compiled_command:
                raise DefinedEditionError(
                    f"compiler changed nonlocal tactic in {spec.name!r}"
                )
            continue
        original_proposition = original_command.partition(":")[2].strip()
        compiled_proposition = compiled_command.partition(":")[2].strip()
        if not _same_open_formula(original_proposition, compiled_proposition):
            raise DefinedEditionError(
                f"compiled local proposition in {spec.name!r} line "
                f"{tactic_record.line_number} differs from the explicit AST"
            )
        total.update(
            {
                use.name: use.occurrences
                for use in tactic_record.proposition.receipt.definition_uses
            }
        )
    return DefinedTheoremRecord(
        scope,
        spec,
        defined,
        compiled,
        statement,
        tactics,
        _uses(total),
    )


def _longest_statement(
    records: Sequence[DefinedTheoremRecord], *, defined: bool
) -> tuple[str, int]:
    if not records:
        return "", 0
    return max(
        (
            (
                record.expanded_spec.name,
                len(record.defined_spec.statement if defined else record.expanded_spec.statement),
            )
            for record in records
        ),
        key=lambda item: (item[1], item[0]),
    )


def _longest_local(
    records: Sequence[DefinedTheoremRecord], *, defined: bool
) -> tuple[str, int, int]:
    candidates = [
        (
            record.expanded_spec.name,
            tactic.line_number,
            len(
                tactic.proposition.defined_source
                if defined
                else tactic.proposition.expanded_source
            ),
        )
        for record in records
        for tactic in record.tactics
        if tactic.proposition is not None
    ]
    if not candidates:
        return "", 0, 0
    name, line, length = max(candidates, key=lambda item: (item[2], item[0], item[1]))
    return name, line, length


def _edition_metrics(records: tuple[DefinedTheoremRecord, ...]) -> DefinedEditionMetrics:
    locals_ = tuple(
        tactic.proposition
        for record in records
        for tactic in record.tactics
        if tactic.proposition is not None
    )
    total: Counter[str] = Counter()
    for record in records:
        total.update(
            {use.name: use.occurrences for use in record.definition_uses}
        )
    return DefinedEditionMetrics(
        theorem_count=len(records),
        public_theorem_count=sum(record.scope == "public" for record in records),
        candidate_theorem_count=sum(record.scope == "candidate" for record in records),
        tactic_line_count=sum(len(record.tactics) for record in records),
        local_statement_count=len(locals_),
        changed_theorem_statement_count=sum(
            bool(record.statement.receipt.definition_uses)
            for record in records
        ),
        changed_local_statement_count=sum(
            bool(item.receipt.definition_uses) for item in locals_
        ),
        expanded_statement_characters=sum(
            len(record.expanded_spec.statement) for record in records
        ),
        defined_statement_characters=sum(
            len(record.defined_spec.statement) for record in records
        ),
        expanded_local_statement_characters=sum(
            len(item.expanded_source) for item in locals_
        ),
        defined_local_statement_characters=sum(
            len(item.defined_source) for item in locals_
        ),
        definition_occurrences=_uses(total),
        longest_expanded_statement=_longest_statement(records, defined=False),
        longest_defined_statement=_longest_statement(records, defined=True),
        longest_expanded_local_statement=_longest_local(records, defined=False),
        longest_defined_local_statement=_longest_local(records, defined=True),
    )


@lru_cache(maxsize=1)
def defined_library_edition() -> DefinedLibraryEdition:
    """Build the exact 557-theorem QR closure in definition-aware syntax."""

    stack = quadratic_reciprocity_stack()
    records = tuple(
        compact_theorem_spec(spec, scope=scope)
        for scope, spec in stack.combined_order
    )
    if len(records) != 557:
        raise DefinedEditionError(
            f"defined QR closure must contain 557 theorems, found {len(records)}"
        )
    by_name = {record.expanded_spec.name: record for record in records}
    if len(by_name) != len(records):
        raise DefinedEditionError("defined QR closure contains duplicate theorem names")
    return DefinedLibraryEdition(
        DEFINED_EDITION_SCHEMA,
        DEFINED_SYNTAX_REGISTRY_SHA256,
        records,
        MappingProxyType(by_name),
        _edition_metrics(records),
    )


def compile_defined_library() -> tuple[TheoremSpec, ...]:
    """Compile all 557 surface records to ordinary, kernel-language specs."""

    return tuple(record.compiled_spec for record in defined_library_edition().records)


def _definition_source_line(definition: DefinitionSpec) -> int:
    needle = f'name="{definition.name}"'
    for number, line in enumerate(
        _SYNTAX_SOURCE.read_text(encoding="utf-8").splitlines(), 1
    ):
        if needle in line:
            return number
    raise DefinedEditionError(f"cannot locate definition source for {definition.name!r}")


def _definition_json_records() -> list[dict[str, object]]:
    ids_by_name = {definition.name: _definition_id(definition) for definition in DEFINITIONS}
    records: list[dict[str, object]] = []
    seen: set[str] = set()
    for definition in DEFINITIONS:
        definition_id = _definition_id(definition)
        dependencies = [ids_by_name[name] for name in definition.conceptual_dependencies]
        if any(dependency not in seen for dependency in dependencies):
            raise DefinedEditionError(
                f"definition {definition.name!r} has a nonpreceding conceptual dependency"
            )
        records.append(
            {
                "id": definition_id,
                "name": definition.name,
                "signature": f"{definition.name}({','.join(definition.parameters)})",
                "summary": definition.summary,
                "expansion": definition.template_source,
                "expansion_sha256": sha256(
                    definition.template_source.encode("utf-8")
                ).hexdigest(),
                "dependencies": dependencies,
                "source": {
                    "path": _SYNTAX_SOURCE_RELATIVE,
                    "line": _definition_source_line(definition),
                    "sha256": _SYNTAX_SOURCE_SHA256,
                },
            }
        )
        seen.add(definition_id)
    return records


def _theorem_json_records(
    edition: DefinedLibraryEdition,
) -> list[dict[str, object]]:
    return [
        {
            "name": record.expanded_spec.name,
            "defined_statement": record.defined_spec.statement,
            "expanded_statement_sha256": sha256(
                record.expanded_spec.statement.encode("utf-8")
            ).hexdigest(),
            "statement_parts": [part.as_json() for part in record.statement.parts],
            "defined_script_lines": [
                {
                    "number": tactic.line_number,
                    "defined_command": tactic.defined_command,
                    "expanded_command_sha256": sha256(
                        tactic.expanded_command.encode("utf-8")
                    ).hexdigest(),
                    "command_parts": [part.as_json() for part in tactic.parts],
                }
                for tactic in record.tactics
            ],
        }
        for record in edition.records
    ]


def build_defined_edition() -> dict[str, object]:
    """Return the JSON-compatible adapter consumed by the defined explorer."""

    edition = defined_library_edition()
    definitions = _definition_json_records()
    theorems = _theorem_json_records(edition)
    # The explorer normalizes a derived use-count map into each theorem before
    # checking this identity.  Compute the same semantic payload here.
    normalized_theorems: list[dict[str, object]] = []
    for theorem in theorems:
        statement_counts: Counter[str] = Counter(
            part["definition"]
            for part in theorem["statement_parts"]  # type: ignore[index]
            if part["kind"] == "definition"  # type: ignore[index]
        )
        script_counts: Counter[str] = Counter(
            part["definition"]
            for line in theorem["defined_script_lines"]  # type: ignore[index]
            for part in line["command_parts"]
            if part["kind"] == "definition"
        )
        total_counts = statement_counts + script_counts
        normalized_theorems.append(
            {
                "name": theorem["name"],
                "defined_statement": theorem["defined_statement"],
                "expanded_statement_sha256": theorem["expanded_statement_sha256"],
                "statement_parts": theorem["statement_parts"],
                "defined_script_lines": theorem["defined_script_lines"],
                "statement_definition_uses": dict(sorted(statement_counts.items())),
                "script_definition_uses": dict(sorted(script_counts.items())),
                "definition_uses": dict(sorted(total_counts.items())),
            }
        )
    semantic = {
        "schema": DEFINED_EDITION_SCHEMA,
        "definitions": definitions,
        "theorems": normalized_theorems,
    }
    identity = sha256(
        json.dumps(
            semantic,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return {
        "schema": DEFINED_EDITION_SCHEMA,
        "identity_sha256": identity,
        "definitions": definitions,
        "theorems": theorems,
    }


__all__ = [
    "DEFINED_EDITION_SCHEMA",
    "DEFINED_EDITION_EXPANSION_BUDGET",
    "DefinedEditionError",
    "SurfacePart",
    "DefinitionUse",
    "EquivalenceReceipt",
    "FormulaCompaction",
    "TacticCompaction",
    "DefinedTheoremSpec",
    "DefinedTheoremRecord",
    "DefinedEditionMetrics",
    "DefinedLibraryEdition",
    "compact_formula_source",
    "compact_tactic_command",
    "compile_defined_spec",
    "compact_theorem_spec",
    "defined_library_edition",
    "compile_defined_library",
    "build_defined_edition",
]
