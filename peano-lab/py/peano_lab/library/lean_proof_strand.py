"""Bounded, source-grounded readable Lean proof strands.

Planning only inspects the immutable checked-use theorem ledger.  In
particular it never replays a theorem, imports an artifact provider, or opens
a proof bundle.  Materialization translates each dependency-curried authored
body separately.  If a body cannot yet be translated to readable Lean, only
that *local* body is independently kernel-checked and embedded as a small
certificate.  Earlier named Lean theorems discharge its premises; a recursive
closed theorem certificate is never reconstructed.

Both generated Lean modules remain ordinary, Mathlib-free source.  Neither a
plan, narrative, Python receipt, source digest, nor release label grants
logical authority: the Lean compiler remains the independent verifier.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import ipaddress
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any
from urllib.parse import quote, urlsplit

from ..engine.state import start
from ..engine.tactics import InvalidProof, TacticError, apply_tactic, checked_final
from ..kernel.formulas import (
    And,
    Bot,
    Eq,
    Exists,
    Forall,
    Formula,
    Imp,
    Or,
    parse_formula_in_context,
    parse_formula_with_names,
    pretty_formula,
)
from ..kernel.proofs import Proof
from .defined_edition import (
    DEFINED_EDITION_EXPANSION_BUDGET,
    DefinedEditionError,
    _definition_match,
    _leading_source_binders,
    compact_formula_source,
    compact_tactic_command,
)
from .defined_syntax import DEFINITIONS, parse_defined_formula
from .lean import (
    _formula_to_lean,
    _fresh_binder,
    _term_to_lean,
    _validate_theorem_name,
    formula_to_lean,
    live_lean_url,
)
from .lean_certified import _CertificateEmitter
from .lean_presentation import (
    SUPPORTED_ALIASES,
    _BINDER_PATTERN,
    _LEAN_KEYWORDS,
    _NOTATION_CODE,
    _family_name,
    readable_formula,
)
from .theorems import TheoremSpec, _closed_formula, _primitive


STRAND_SCHEMA = "peano-lab-lean-proof-strand-v1"
MAX_STRAND_NODES = 4_096
MAX_STRAND_EDGES = 65_536
MAX_STRAND_DEPTH = 256
MAX_SOURCE_FILE_BYTES = 8 * 1024 * 1024
MAX_STATEMENT_BYTES = 1_048_576
MAX_SCRIPT_BYTES = 1_048_576
MAX_TOTAL_SPECIFICATION_BYTES = 64 * 1024 * 1024
MAX_CLAIMS_PER_NODE = 24
DEFAULT_PREVIEW_BYTES = 15_360
DEFAULT_MAX_MODULE_BYTES = 64 * 1024 * 1024
DEFAULT_CHUNK_BYTES = 192 * 1024
DEFAULT_LIVE_SOURCE_BYTES = 1_048_576
DEFAULT_LIVE_URL_BYTES = 512 * 1024
MAX_LIVE_URL_BYTES = 1_048_576
MAX_LIVE_CODEC_SOURCE_BYTES = 4 * 1_048_576
LIVE_EXPORT_SCHEMA = "peano-lab-lean-live-v1"

_DEFINITION_NAMES = frozenset(definition.name for definition in DEFINITIONS)
_SOURCE_PREFIX = "peano-lab/py/peano_lab/library/"
_LIBRARY = Path(__file__).resolve().parent
_SAFE_MODULE_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\.py\Z")
_LIVE_LZ_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
_LIVE_LZ_INDEX = {character: index for index, character in enumerate(_LIVE_LZ_ALPHABET)}
_LIVE_LZ_PAYLOAD = re.compile(r"[A-Za-z0-9+/]+\Z")


class ProofStrandError(ValueError):
    """A proof strand lacks exact metadata, evidence, or safe source identity."""


class ProofStrandLimitError(ProofStrandError):
    """A selected strand exceeded its explicit metadata or generation budget."""


@dataclass(frozen=True, slots=True)
class ProofStrandClaim:
    """One authored local mathematical claim and its exact expansion receipt."""

    line_number: int
    tactic: str
    name: str
    proposition: str
    exact_sha256: str
    defined_sha256: str
    exact_ast_equivalence: bool


@dataclass(frozen=True, slots=True)
class ProofStrandNode:
    """One immutable checked-use theorem and its replay-free source metadata."""

    name: str
    statement: str
    readable_statement: str
    dependencies: tuple[str, ...]
    script: tuple[str, ...]
    summary: str
    evidence: str
    membership: str
    source_module: str
    source_path: str
    source_sha256: str
    specification_sha256: str
    depth: int
    lean_identifier: str
    aliases: tuple[str, ...]
    tactic_counts: tuple[tuple[str, int], ...]
    local_claims: tuple[ProofStrandClaim, ...]
    local_claim_count: int

    @property
    def script_lines(self) -> int:
        return len(self.script)


@dataclass(frozen=True, slots=True)
class ProofStrandPlan:
    """A dependency-topological, metadata-only checked-use proof lineage."""

    root: str
    edition: str
    edition_version: str
    edition_identity_sha256: str
    nodes: tuple[ProofStrandNode, ...]
    edge_count: int
    maximum_depth: int
    total_script_lines: int
    identity_sha256: str

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def root_node(self) -> ProofStrandNode:
        return self.nodes[-1]


@dataclass(frozen=True, slots=True)
class ProofStrandPackage:
    """One named readable proof strand and its separately verifiable prelude."""

    module_name: str
    relative_path: str
    code: str
    manifest: dict[str, Any]
    preview: str
    generated_files: tuple[tuple[str, str], ...] = ()

    def files(self) -> list[tuple[str, str]]:
        """Return exact source files in Lean import-dependency order."""

        modules = self.generated_files or ((self.relative_path, self.code),)
        return [("PeanoLab/Presentation.lean", _NOTATION_CODE), *modules]


@dataclass(frozen=True, slots=True)
class LeanLiveExport:
    """One standalone core-Lean source; remote compilation is never asserted."""

    source: str
    url: str | None
    url_status: str
    source_bytes: int
    url_bytes: int
    manifest: dict[str, Any]


def _progress(
    callback: Callable[[dict[str, Any]], None] | None,
    *,
    stage: str,
    completed: int,
    total: int,
    theorem: str | None = None,
    message: str | None = None,
) -> None:
    """Expose bounded factual node progress without changing proof authority."""

    if callback is None:
        return
    if not callable(callback):
        raise ProofStrandError("proof-strand progress callback must be callable")
    if (
        stage not in {"plan", "translate", "certificate", "package", "compile", "repair", "complete"}
        or type(completed) is not int
        or type(total) is not int
        or completed < 0
        or total < 0
        or (total and completed > total)
    ):
        raise ProofStrandError("proof-strand progress event is not exact and bounded")
    event: dict[str, Any] = {
        "kind": "lean_strand_progress",
        "stage": stage,
        "completed": completed,
        "total": total,
    }
    if theorem is not None:
        event["theorem"] = theorem
    if message is not None:
        event["message"] = message
    callback(event)


def _digest_bytes(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def _digest_text(text: str) -> str:
    return _digest_bytes(text.encode("utf-8"))


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _positive_limit(name: str, value: object, maximum: int) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ProofStrandError(f"{name} must be an integer between 1 and {maximum}")
    return value


def _edition_view(edition: str) -> tuple[Any, str]:
    """Import only the current sealed, artifact-free Alpha-v25 inventory."""

    if type(edition) is not str or edition not in {"stable", "alpha"}:
        raise ProofStrandError("edition must be exactly 'stable' or 'alpha'")
    from . import editions_v25

    if edition == "stable":
        return editions_v25.STABLE_EDITION, "stable"
    return editions_v25.ALPHA_EDITION, "v25"


@lru_cache(maxsize=512)
def _source_identity(source_module: str) -> tuple[str, str]:
    if (
        type(source_module) is not str
        or not source_module.startswith(_SOURCE_PREFIX)
        or "\\" in source_module
    ):
        raise ProofStrandError("theorem source is not an approved library module")
    relative = PurePosixPath(source_module)
    parts = source_module.split("/")
    if (
        relative.is_absolute()
        or any(part in {"", ".", ".."} for part in parts)
        or len(parts) != 5
        or _SAFE_MODULE_NAME.fullmatch(parts[-1]) is None
    ):
        raise ProofStrandError("theorem source path is not a canonical library module")
    # Browser Pyodide intentionally flattens the package beneath /lab; its
    # frozen provenance still uses canonical repository-relative source names.
    # Resolve only the already validated basename against the mounted library.
    candidate = (_LIBRARY / parts[-1]).resolve()
    if candidate.parent != _LIBRARY or not candidate.is_file():
        raise ProofStrandError("theorem source escaped its reviewed library directory")
    size = candidate.stat().st_size
    if size > MAX_SOURCE_FILE_BYTES:
        raise ProofStrandLimitError(
            f"theorem source exceeds the {MAX_SOURCE_FILE_BYTES}-byte provenance limit"
        )
    digest = sha256()
    with candidate.open("rb") as stream:
        while block := stream.read(65_536):
            digest.update(block)
    return source_module, digest.hexdigest()


def _render_all_definitions(
    formula: Formula,
    names: tuple[str, ...],
    parent_precedence: int,
    leading: list[tuple[type[Formula], str]] | None = None,
) -> str:
    matched = _definition_match(formula)
    if matched is not None:
        definition, arguments = matched
        if definition.name not in _DEFINITION_NAMES:
            raise ProofStrandError("the matched formula has no reviewed Lean definition")
        text = definition.name + " " + " ".join(
            _term_to_lean(argument, names, 4) for argument in arguments
        )
        precedence = 5
    elif type(formula) is Eq:
        text = (
            f"{_term_to_lean(formula.left, names, 0)} = "
            f"{_term_to_lean(formula.right, names, 0)}"
        )
        precedence = 5
    elif type(formula) is Bot:
        text, precedence = "False", 5
    elif type(formula) is Imp and type(formula.right) is Bot:
        text = "¬" + _render_all_definitions(formula.left, names, 4)
        precedence = 4
    elif type(formula) in (And, Or, Imp):
        if type(formula) is And:
            precedence, symbol = 3, "∧"
        elif type(formula) is Or:
            precedence, symbol = 2, "∨"
        else:
            precedence, symbol = 1, "→"
        left = _render_all_definitions(formula.left, names, precedence + 1)
        right = _render_all_definitions(formula.right, names, precedence)
        text = f"{left} {symbol} {right}"
    elif type(formula) in (Forall, Exists):
        binder = _fresh_binder(names)
        if leading and leading[0][0] is type(formula):
            _, candidate = leading.pop(0)
            if (
                candidate not in names
                and candidate not in _LEAN_KEYWORDS
                and _BINDER_PATTERN.fullmatch(candidate) is not None
            ):
                binder = candidate
        symbol = "∀" if type(formula) is Forall else "∃"
        body = _render_all_definitions(
            formula.body,
            (binder,) + names,
            0,
            leading,
        )
        text = f"{symbol} {binder} : Nat, {body}"
        precedence = 0
    else:
        raise TypeError("expected an exact Peano formula constructor")
    return f"({text})" if precedence < parent_precedence else text


def _readable_strand_details(
    formula: Formula,
    source_statement: str | None,
) -> tuple[str, tuple[str, ...]]:
    if not isinstance(formula, Formula):
        raise TypeError("formula must be an exact Peano Formula")
    if source_statement is None:
        source = pretty_formula(formula, [])
    elif type(source_statement) is str:
        source = source_statement
    else:
        raise TypeError("source_statement must be text or None")
    if len(source.encode("utf-8")) > MAX_STATEMENT_BYTES:
        raise ProofStrandLimitError("statement exceeds its proof-strand byte limit")
    try:
        actual, names = parse_formula_with_names(source)
    except (RecursionError, TypeError, ValueError) as error:
        raise ProofStrandError("source statement is not a valid closed PA formula") from error
    if names or actual != formula:
        raise ProofStrandError("source statement differs from its exact checked formula")
    try:
        compact = compact_formula_source(source)
        if not compact.receipt.exact_ast_equivalence:
            raise ProofStrandError("definition compaction lacks its exact-AST receipt")
        expanded = parse_defined_formula(
            compact.defined_source,
            expansion_budget=DEFINED_EDITION_EXPANSION_BUDGET,
        )
        if expanded != formula:
            raise ProofStrandError("readable proof notation changed its exact PA formula")
        aliases = tuple(item.name for item in compact.receipt.definition_uses)
        if any(name not in _DEFINITION_NAMES for name in aliases):
            raise ProofStrandError("the proof surface uses an unreviewed definition")
        return (
            _render_all_definitions(
                formula,
                (),
                0,
                _leading_source_binders(source),
            ),
            aliases,
        )
    except (DefinedEditionError, RecursionError, TypeError, ValueError):
        return formula_to_lean(formula), ()


def readable_strand_formula(
    formula: Formula,
    *,
    source_statement: str | None = None,
) -> str:
    """Render all 40 reviewed conservative definitions without replay."""

    return _readable_strand_details(formula, source_statement)[0]


def _specification_identity(spec: TheoremSpec) -> str:
    return _digest_text(
        _canonical(
            {
                "name": spec.name,
                "statement": spec.statement,
                "dependencies": list(spec.dependencies),
                "script": list(spec.script),
                "summary": spec.summary,
            }
        )
    )


def _local_claims(
    script: tuple[str, ...],
) -> tuple[tuple[ProofStrandClaim, ...], int]:
    claims: list[ProofStrandClaim] = []
    total = 0
    for number, command in enumerate(script, 1):
        tactic = command.split(maxsplit=1)[0]
        if tactic not in {"have", "suffices"}:
            continue
        total += 1
        if len(claims) >= MAX_CLAIMS_PER_NODE:
            continue
        try:
            compacted = compact_tactic_command(command, number)
        except (DefinedEditionError, RecursionError, TypeError, ValueError) as error:
            raise ProofStrandError(
                f"local claim on tactic line {number} lacks an exact expansion receipt"
            ) from error
        if compacted.proposition is None or compacted.local_name is None:
            raise ProofStrandError("local claim lacks its proposition or hypothesis name")
        receipt = compacted.proposition.receipt
        if not receipt.exact_ast_equivalence:
            raise ProofStrandError("local claim is not exactly AST-equivalent")
        claims.append(
            ProofStrandClaim(
                line_number=number,
                tactic=tactic,
                name=compacted.local_name,
                proposition=compacted.proposition.defined_source,
                exact_sha256=receipt.expanded_source_sha256,
                defined_sha256=receipt.defined_source_sha256,
                exact_ast_equivalence=True,
            )
        )
    return tuple(claims), total


def _strand_node(item: Any, depth: int) -> tuple[ProofStrandNode, int]:
    if type(item.spec) is not TheoremSpec:
        raise ProofStrandError("edition row does not contain an exact theorem specification")
    spec = item.spec
    try:
        _validate_theorem_name(spec.name)
        for dependency in spec.dependencies:
            _validate_theorem_name(dependency)
    except (TypeError, ValueError) as error:
        raise ProofStrandError("theorem or dependency has an unsafe Lean identifier") from error
    if len(set(spec.dependencies)) != len(spec.dependencies):
        raise ProofStrandError(f"theorem {spec.name!r} repeats a direct dependency")
    if type(spec.statement) is not str or type(spec.summary) is not str:
        raise ProofStrandError("theorem statements and summaries must be exact text")
    if type(spec.script) is not tuple or not spec.script:
        raise ProofStrandError("theorem proof script must be a nonempty tuple")
    script_bytes = 0
    for line in spec.script:
        if type(line) is not str or not line.strip() or "\x00" in line:
            raise ProofStrandError("theorem proof script contains an unsafe command")
        script_bytes += len(line.encode("utf-8"))
        if script_bytes > MAX_SCRIPT_BYTES:
            raise ProofStrandLimitError("theorem proof script exceeds its byte limit")
    statement_bytes = len(spec.statement.encode("utf-8"))
    if statement_bytes > MAX_STATEMENT_BYTES:
        raise ProofStrandLimitError("theorem statement exceeds its proof-strand byte limit")
    source_path, source_sha256 = _source_identity(item.source_module)
    formula = _closed_formula(spec.statement)
    readable, aliases = _readable_strand_details(formula, spec.statement)
    claims, claim_count = _local_claims(spec.script)
    counts = Counter(line.split(maxsplit=1)[0] for line in spec.script)
    evidence = item.evidence.value
    membership = item.membership.value
    if evidence not in {"stable_closed", "alpha_closed"}:
        raise ProofStrandError(f"theorem {spec.name!r} lacks checked-use evidence")
    return (
        ProofStrandNode(
            name=spec.name,
            statement=spec.statement,
            readable_statement=readable,
            dependencies=spec.dependencies,
            script=spec.script,
            summary=spec.summary,
            evidence=evidence,
            membership=membership,
            source_module=item.source_module,
            source_path=source_path,
            source_sha256=source_sha256,
            specification_sha256=_specification_identity(spec),
            depth=depth,
            lean_identifier=spec.name,
            aliases=aliases,
            tactic_counts=tuple(sorted(counts.items())),
            local_claims=claims,
            local_claim_count=claim_count,
        ),
        statement_bytes + script_bytes,
    )


def plan_proof_strand(
    name: str,
    *,
    edition: str = "stable",
    max_nodes: int = 2_048,
    max_edges: int = 8_192,
    max_depth: int = 128,
    progress: Callable[[dict[str, Any]], None] | None = None,
) -> ProofStrandPlan:
    """Inspect one complete checked-use dependency DAG without proof replay."""

    node_limit = _positive_limit("max_nodes", max_nodes, MAX_STRAND_NODES)
    edge_limit = _positive_limit("max_edges", max_edges, MAX_STRAND_EDGES)
    depth_limit = _positive_limit("max_depth", max_depth, MAX_STRAND_DEPTH)
    if progress is not None and not callable(progress):
        raise ProofStrandError("proof-strand progress callback must be callable")
    try:
        _validate_theorem_name(name)
    except (TypeError, ValueError) as error:
        raise ProofStrandError("proof-strand root must be a safe theorem name") from error
    _progress(progress, stage="plan", completed=0, total=0, theorem=name)
    view, version = _edition_view(edition)
    root = view.by_name.get(name)
    if root is None:
        raise ProofStrandError(f"unknown {edition} theorem {name!r}")
    if not root.checked_use:
        raise ProofStrandError(
            f"{edition} theorem {name!r} has evidence {root.evidence.value!r}; "
            "checked-use authority is required"
        )
    colors: dict[str, int] = {}
    ordered: list[Any] = []
    edges = 0
    stack: list[tuple[str, bool, int]] = [(name, False, 0)]
    while stack:
        current, leaving, path_depth = stack.pop()
        if leaving:
            colors[current] = 2
            item = view.by_name.get(current)
            if item is None:
                raise ProofStrandError("proof dependency vanished during strand planning")
            ordered.append(item)
            continue
        color = colors.get(current, 0)
        if color == 2:
            continue
        if color == 1:
            raise ProofStrandError(f"proof dependency graph has a cycle at {current!r}")
        if path_depth > depth_limit:
            raise ProofStrandLimitError(
                f"proof strand exceeds its {depth_limit}-layer dependency-depth limit"
            )
        item = view.by_name.get(current)
        if item is None:
            raise ProofStrandError(f"proof dependency {current!r} is unavailable")
        if not item.checked_use:
            raise ProofStrandError(
                f"proof dependency {current!r} has no checked-use authority"
            )
        if len(colors) >= node_limit:
            raise ProofStrandLimitError(
                f"proof strand exceeds its {node_limit}-theorem dependency limit"
            )
        colors[current] = 1
        edges += len(item.spec.dependencies)
        if edges > edge_limit:
            raise ProofStrandLimitError(
                f"proof strand exceeds its {edge_limit}-edge dependency limit"
            )
        stack.append((current, True, path_depth))
        for dependency in reversed(item.spec.dependencies):
            if colors.get(dependency) == 1:
                raise ProofStrandError(
                    f"proof dependency graph has a cycle at {dependency!r}"
                )
            if colors.get(dependency) != 2:
                stack.append((dependency, False, path_depth + 1))

    nodes: list[ProofStrandNode] = []
    seen: set[str] = set()
    specification_bytes = 0
    for item in ordered:
        spec = item.spec
        if any(dependency not in seen for dependency in spec.dependencies):
            raise ProofStrandError("proof strand is not in exact dependency order")
        depth = int(view.dependency_depth_by_name[spec.name])
        if depth > depth_limit:
            raise ProofStrandLimitError(
                f"proof strand exceeds its {depth_limit}-layer dependency-depth limit"
            )
        node, charged = _strand_node(item, depth)
        specification_bytes += charged
        if specification_bytes > MAX_TOTAL_SPECIFICATION_BYTES:
            raise ProofStrandLimitError("proof strand exceeds its total metadata byte limit")
        nodes.append(node)
        seen.add(node.name)
        _progress(
            progress,
            stage="plan",
            completed=len(nodes),
            total=len(ordered),
            theorem=node.name,
        )
    if not nodes or nodes[-1].name != name:
        raise ProofStrandError("proof strand failed to terminate at its exact root")
    identity = _digest_text(
        _canonical(
            {
                "root": name,
                "edition": edition,
                "edition_version": version,
                "edition_identity_sha256": view.identity_sha256,
                "nodes": [
                    {
                        "name": node.name,
                        "specification_sha256": node.specification_sha256,
                        "source_sha256": node.source_sha256,
                        "evidence": node.evidence,
                    }
                    for node in nodes
                ],
            }
        )
    )
    return ProofStrandPlan(
        root=name,
        edition=edition,
        edition_version=version,
        edition_identity_sha256=view.identity_sha256,
        nodes=tuple(nodes),
        edge_count=edges,
        maximum_depth=max(node.depth for node in nodes),
        total_script_lines=sum(len(node.script) for node in nodes),
        identity_sha256=identity,
    )


def _bounded_lines(lines: list[str], maximum: int, footer: str) -> str:
    footer_bytes = len(footer.encode("utf-8"))
    if footer_bytes + 1 > maximum:
        raise ProofStrandLimitError("proof-strand preview cannot fit its authority footer")
    available = maximum - footer_bytes - 1
    prefix = "\n".join(lines).encode("utf-8")
    if len(prefix) > available:
        suffix = "\n-- [proof strand preview truncated]"
        remaining = available - len(suffix.encode("utf-8"))
        if remaining < 0:
            raise ProofStrandLimitError("proof-strand preview budget is too small")
        prefix = prefix[:remaining].decode("utf-8", "ignore").encode("utf-8")
        prefix += suffix.encode("utf-8")
    return prefix.decode("utf-8") + "\n" + footer


def preview_proof_strand(
    plan: ProofStrandPlan,
    *,
    max_bytes: int = DEFAULT_PREVIEW_BYTES,
    max_rows: int = 24,
) -> str:
    """Explain an immutable strand without replaying any theorem or proof."""

    if type(plan) is not ProofStrandPlan:
        raise TypeError("proof-strand preview requires an exact ProofStrandPlan")
    budget = _positive_limit("max_bytes", max_bytes, MAX_STATEMENT_BYTES)
    rows = _positive_limit("max_rows", max_rows, MAX_STRAND_NODES)
    root = plan.root_node
    lines = [
        f"theorem «{root.name}» : {root.readable_statement}",
        f"-- {root.summary}",
        f"-- Edition: {plan.edition}" + (
            f" {plan.edition_version}" if plan.edition == "alpha" else ""
        ),
        f"-- Checked-use evidence: {root.evidence}; membership: {root.membership}",
        (
            "-- Complete named dependency strand: "
            f"{plan.node_count} theorem(s), {plan.edge_count} edge(s), "
            f"maximum depth {plan.maximum_depth}, "
            f"{plan.total_script_lines} authored proof line(s)"
        ),
        f"-- Exact source: {root.source_path}",
        f"-- Source SHA-256: {root.source_sha256}",
        f"-- Specification SHA-256: {root.specification_sha256}",
    ]
    if root.dependencies:
        lines.append("-- Direct named ingredients: " + ", ".join(root.dependencies))
    if root.local_claims:
        lines.append("-- Exact-AST-preserving local mathematical claims:")
        for claim in root.local_claims[: min(6, rows)]:
            lines.append(
                f"--   line {claim.line_number}: "
                f"{claim.tactic} {claim.name} : {claim.proposition}"
            )
        if root.local_claim_count > min(6, rows):
            lines.append(
                f"--   ... {root.local_claim_count - min(6, rows)} additional local claim(s)"
            )
    lines.append("-- Named dependency strand (foundation first):")
    selected = plan.nodes[:rows]
    if len(plan.nodes) > rows:
        selected = plan.nodes[: max(1, rows - 1)] + (root,)
    for node in selected:
        lines.append(
            f"--   [{node.depth:02d}] {node.name}: "
            f"{len(node.dependencies)} premise(s), {len(node.script)} proof line(s)"
        )
    if len(plan.nodes) > rows:
        lines.append(f"--   ... {len(plan.nodes) - rows} intermediate theorem(s) omitted")
    footer = (
        "-- Proof-body replay: NOT RUN; Lean verification: NOT RUN. "
        "Compile the complete proof-strand package."
    )
    return _bounded_lines(lines, budget, footer)


def _definition_lines() -> list[str]:
    rows: list[str] = []
    already = frozenset(SUPPORTED_ALIASES)
    for definition in DEFINITIONS:
        if definition.name in already:
            continue
        if parse_formula_in_context(
            definition.template_source,
            list(definition.parameters),
        ) != definition.template_formula:
            raise ProofStrandError(
                f"reviewed definition {definition.name!r} changed its exact formula"
            )
        parameters = " ".join(definition.parameters)
        body = _formula_to_lean(
            definition.template_formula,
            tuple(definition.parameters),
            0,
        )
        rows.extend(
            (
                f"-- {definition.stable_id}: {definition.summary}",
                f"def {definition.name} ({parameters} : Nat) : Prop :=",
                f"  {body}",
                "",
            )
        )
    return rows


def _arithmetic_foundations() -> tuple[list[str], dict[str, str]]:
    rows = [
        "-- The six Peano foundations are proved facts about Lean Nat, not axioms.",
        "theorem pa1_sound : ∀ n : Nat, Nat.succ n = 0 → False := by",
        "  intro n h",
        "  exact Nat.succ_ne_zero n h",
        "",
        (
            "theorem pa2_sound : "
            "∀ n m : Nat, Nat.succ n = Nat.succ m → n = m := by"
        ),
        "  intro n m h",
        "  exact Nat.succ.inj h",
        "",
        "theorem pa3_sound : ∀ n : Nat, n + 0 = n := by",
        "  intro n",
        "  exact Nat.add_zero n",
        "",
        (
            "theorem pa4_sound : "
            "∀ n m : Nat, n + Nat.succ m = Nat.succ (n + m) := by"
        ),
        "  intro n m",
        "  exact Nat.add_succ n m",
        "",
        "theorem pa5_sound : ∀ n : Nat, n * 0 = 0 := by",
        "  intro n",
        "  exact Nat.mul_zero n",
        "",
        (
            "theorem pa6_sound : "
            "∀ n m : Nat, n * Nat.succ m = n * m + n := by"
        ),
        "  intro n m",
        "  exact Nat.mul_succ n m",
        "",
    ]
    return rows, {f"PA{index}": f"pa{index}_sound" for index in range(1, 7)}


def _curried_formula(
    node: ProofStrandNode,
    formulas: Mapping[str, Formula],
) -> Formula:
    target = formulas[node.name]
    for dependency in reversed(node.dependencies):
        target = Imp(formulas[dependency], target)
    return target


def _checked_local_body(
    node: ProofStrandNode,
    formula: Formula,
) -> Proof:
    state = start(formula)
    try:
        for dependency in node.dependencies:
            state = apply_tactic(state, "intro", dependency)
        for command in node.script:
            tactic, arguments = _primitive(command)
            state = apply_tactic(state, tactic, arguments)
        return checked_final(state, formula)
    except (InvalidProof, RecursionError, TacticError, TypeError, ValueError) as error:
        raise ProofStrandError(
            f"independent checking rejected the local proof body {node.name!r}"
        ) from error


def _certificate_lines(
    node: ProofStrandNode,
    formula: Formula,
    proof: Proof,
) -> tuple[list[str], str]:
    emitter = _CertificateEmitter(f"{node.name}_proof_strand_local_body")
    target_identifier = emitter.formula(formula)
    proof_identifier = emitter.proof(proof)
    artifact_identifier = f"{emitter.prefix}_artifact"
    theorem_identifier = f"_checked_local_body_{node.name}"
    fuel = max(64, 8 * len(emitter.proof_keys) + 16)
    # A quantified target contains shared nested formula and term bindings.
    # Unfolding only its outermost identifier leaves an opaque `Formula.Holds`
    # obligation under quantifiers, so nontrivial local fallback certificates
    # fail even though the unchanged kernel accepted their exact bodies.
    # Dict insertion order is deterministic and already dependency-topological.
    unfold = (
        artifact_identifier,
        *emitter.formula_keys.values(),
        *emitter.term_keys.values(),
        "PeanoLab.Formula.Holds",
        "PeanoLab.Term.eval",
        "PeanoLab.Valuation.cons",
    )
    groups = tuple(unfold[index:index + 6] for index in range(0, len(unfold), 6))
    simp_lines = [
        ("  simpa [" if index == 0 else "    ")
        + ", ".join(group)
        + (
            "] using sound (fun _ => 0)"
            if index == len(groups) - 1
            else ","
        )
        for index, group in enumerate(groups)
    ]
    rows = [
        "-- Fallback: ONLY this dependency-curried local body is certificate-checked.",
        *emitter.declarations,
        f"private def {artifact_identifier} : PeanoLab.Artifact :=",
        f"  {{ fuel := {fuel}, target := {target_identifier}, proof := {proof_identifier} }}",
        "",
        (
            f"private theorem «{theorem_identifier}» : "
            f"{formula_to_lean(formula)} := by"
        ),
        f"  have accepted : {artifact_identifier}.check = true := by",
        "    decide",
        "  have sound := PeanoLab.Artifact.check_sound accepted",
        *simp_lines,
        "",
    ]
    return rows, theorem_identifier


def _file_record(module: str, path: str, source: str) -> dict[str, Any]:
    payload = source.encode("utf-8")
    return {
        "module": module,
        "relative_path": path,
        "sha256": _digest_bytes(payload),
        "bytes": len(payload),
    }


def _line_count(rows: list[str] | tuple[str, ...]) -> int:
    return sum(line.count("\n") + 1 for line in rows)


def _module_size(rows: list[str]) -> int:
    return len("\n".join(rows).encode("utf-8"))


def _chunk_header(
    namespace: str,
    previous_module: str,
    index: int,
) -> list[str]:
    return [
        f"-- Dependency-topological readable proof strand, chunk {index:03d}.",
        f"import {previous_module}",
        "",
        "set_option maxRecDepth 4096",
        "set_option maxHeartbeats 800000",
        "set_option linter.unusedSimpArgs false",
        "set_option linter.unnecessarySimpa false",
        "",
        f"namespace {namespace}",
        "",
        "open PeanoLab.Presentation",
        "",
    ]


def _segment_modules(
    *,
    namespace: str,
    token: str,
    final_path: str,
    initial_rows: list[str],
    node_blocks: list[tuple[str, list[str], dict[str, Any]]],
    root: str,
    include_axiom_audit: bool,
    maximum: int,
) -> tuple[tuple[tuple[str, str], ...], str]:
    """Split a large theorem DAG into independently bounded Lean modules."""

    footer = [f"end {namespace}", ""]
    modules: list[tuple[str, str]] = []
    chunk_index = 0
    header = initial_rows
    pending: list[tuple[str, list[str], dict[str, Any]]] = []

    def chunk_identity(index: int) -> tuple[str, str]:
        label = f"C{index:03d}"
        return (
            f"PeanoLab.Generated.{token}.Chunks.{label}",
            f"PeanoLab/Generated/{token}/Chunks/{label}.lean",
        )

    def candidate_rows(
        current_header: list[str],
        current: list[tuple[str, list[str], dict[str, Any]]],
    ) -> list[str]:
        result = list(current_header)
        for _, block, _ in current:
            result.extend(block)
        result.extend(footer)
        return result

    def publish(
        index: int,
        current_header: list[str],
        current: list[tuple[str, list[str], dict[str, Any]]],
    ) -> tuple[str, str]:
        if not current:
            raise ProofStrandError("a generated proof-strand chunk has no theorem")
        module, relative = chunk_identity(index)
        rendered = "\n".join(candidate_rows(current_header, current))
        if len(rendered.encode("utf-8")) > maximum:
            raise ProofStrandLimitError("generated proof-strand chunk exceeds its byte limit")
        cursor = _line_count(current_header)
        for name, block, record in current:
            record["generated_module"] = module
            record["generated_relative_path"] = relative
            record["source_line_start"] = cursor + 1
            cursor += _line_count(block)
            record["source_line_end"] = cursor
            if record["name"] != name:
                raise ProofStrandError("proof-strand source mapping lost its theorem name")
        modules.append((relative, rendered))
        return module, relative

    for block in node_blocks:
        proposed = pending + [block]
        if _module_size(candidate_rows(header, proposed)) <= maximum:
            pending = proposed
            continue
        if not pending:
            raise ProofStrandLimitError(
                f"the local proof node {block[0]!r} exceeds its "
                f"{maximum}-byte independent Lean chunk limit"
            )
        previous, _ = publish(chunk_index, header, pending)
        chunk_index += 1
        header = _chunk_header(namespace, previous, chunk_index)
        pending = [block]
        if _module_size(candidate_rows(header, pending)) > maximum:
            raise ProofStrandLimitError(
                f"the local proof node {block[0]!r} exceeds its "
                f"{maximum}-byte independent Lean chunk limit"
            )
    previous, _ = publish(chunk_index, header, pending)
    final = [
        "-- Final independently compiled theorem of the named proof strand.",
        f"import {previous}",
        "",
        f"namespace {namespace}",
        "",
    ]
    if include_axiom_audit:
        final.extend((f"#print axioms «{root}»", ""))
    final.extend((f"end {namespace}", ""))
    final_code = "\n".join(final)
    if len(final_code.encode("utf-8")) > maximum:
        raise ProofStrandLimitError("final proof-strand module exceeds its byte limit")
    modules.append((final_path, final_code))
    return tuple(modules), final_code


def build_proof_strand(
    plan: ProofStrandPlan,
    *,
    max_steps: int = 4_096,
    max_module_bytes: int = DEFAULT_MAX_MODULE_BYTES,
    chunk_max_bytes: int = DEFAULT_CHUNK_BYTES,
    include_axiom_audit: bool = True,
    strict_readable: bool = False,
    force_fallback_names: frozenset[str] | None = None,
    force_fallback: frozenset[str] | None = None,
    progress: Callable[[dict[str, Any]], None] | None = None,
) -> ProofStrandPackage:
    """Materialize one modular, independently Lean-checkable proof strand."""

    if type(plan) is not ProofStrandPlan:
        raise TypeError("proof-strand generation requires an exact ProofStrandPlan")
    if progress is not None and not callable(progress):
        raise ProofStrandError("proof-strand progress callback must be callable")
    step_limit = _positive_limit("max_steps", max_steps, 65_536)
    byte_limit = _positive_limit("max_module_bytes", max_module_bytes, 64 * 1024 * 1024)
    chunk_limit = _positive_limit("chunk_max_bytes", chunk_max_bytes, 64 * 1024 * 1024)
    if type(include_axiom_audit) is not bool or type(strict_readable) is not bool:
        raise ProofStrandError("proof-strand policy flags must be exact booleans")
    if force_fallback_names is not None and force_fallback is not None:
        raise ProofStrandError("use only one forced-fallback name set")
    requested_fallback = (
        force_fallback_names if force_fallback_names is not None else force_fallback
    )
    if requested_fallback is None:
        forced = frozenset()
    elif type(requested_fallback) is frozenset and all(
        type(item) is str for item in requested_fallback
    ):
        forced = requested_fallback
    else:
        raise ProofStrandError("forced fallback names must be an exact string frozenset")
    unknown_fallback = forced.difference(node.name for node in plan.nodes)
    if unknown_fallback:
        raise ProofStrandError(
            "forced fallback names are outside the selected proof strand: "
            + ", ".join(sorted(unknown_fallback))
        )
    from .lean_proof_reconstruction import (
        LeanProofReconstruction,
        reconstruct_theorem,
    )

    token = f"{_family_name(plan.root)}_{plan.identity_sha256[:16]}"
    module_name = f"PeanoLab.Generated.{token}.Strand"
    path = f"PeanoLab/Generated/{token}/Strand.lean"
    foundations, available_axioms = _arithmetic_foundations()
    rows = [
        "-- Source-grounded constructive proof strand; no recursive certificate replay.",
        f"-- Root: {plan.root}; edition: {plan.edition} {plan.edition_version}.",
        (
            f"-- {plan.node_count} named theorem(s), {plan.edge_count} edge(s), "
            f"{plan.total_script_lines} authored tactic line(s)."
        ),
        "import PeanoLab.Presentation",
        "import PeanoLab.Codec",
        "",
        "set_option maxRecDepth 4096",
        "set_option maxHeartbeats 800000",
        "set_option linter.unusedSimpArgs false",
        "set_option linter.unnecessarySimpa false",
        "",
        f"namespace {module_name}",
        "",
        "open PeanoLab.Presentation",
        "",
        "-- The other reviewed notation definitions are exact conservative abbreviations.",
        *_definition_lines(),
        *foundations,
    ]
    formulas: dict[str, Formula] = {}
    references: dict[str, str] = {}
    records: list[dict[str, Any]] = []
    node_blocks: list[tuple[str, list[str], dict[str, Any]]] = []
    translated = 0
    fallback = 0
    source_bytes = sum(len(line.encode("utf-8")) + 1 for line in rows)
    source_line_cursor = sum(line.count("\n") + 1 for line in rows)
    initial_rows = list(rows)
    _progress(
        progress,
        stage="translate",
        completed=0,
        total=plan.node_count,
        theorem=plan.root,
    )

    for index, node in enumerate(plan.nodes, 1):
        if len(node.script) > step_limit:
            raise ProofStrandLimitError(
                f"theorem {node.name!r} exceeds its {step_limit}-step local-body limit"
            )
        formulas[node.name] = _closed_formula(node.statement)
        dependency_formulas = {
            dependency: formulas[dependency] for dependency in node.dependencies
        }
        dependency_references = {
            dependency: references[dependency] for dependency in node.dependencies
        }
        spec = TheoremSpec(
            node.name,
            node.statement,
            node.dependencies,
            node.script,
            node.summary,
        )
        if _specification_identity(spec) != node.specification_sha256:
            raise ProofStrandError("proof-strand specification changed after planning")
        standard_statement = readable_formula(
            formulas[node.name],
            source_statement=node.statement,
        )
        if node.name in forced:
            result = LeanProofReconstruction(
                name=node.name,
                lean_statement=standard_statement,
                lean_body="",
                used_dependencies=(),
                used_axioms=(),
                translated_steps=0,
                unsupported_steps=("forced local certificate fallback",),
                status="fallback_required",
                diagnostics=("caller explicitly requested a local checked fallback",),
            )
        else:
            result = reconstruct_theorem(
                spec,
                dependency_references=dependency_references,
                dependency_formulas=dependency_formulas,
                available_axioms=available_axioms,
                max_steps=step_limit,
            )
        if result.name != node.name or result.lean_statement not in {
            standard_statement,
            formula_to_lean(formulas[node.name]),
        }:
            raise ProofStrandError("readable proof reconstruction changed its theorem target")
        source_line_start = source_line_cursor + 1
        node_lines = [
            f"-- PROOF NODE: {node.name}",
            f"-- {node.summary.replace(chr(10), ' ').replace(chr(13), ' ')}",
            f"-- Source: {node.source_path}; SHA-256: {node.source_sha256}",
        ]
        used_dependencies: tuple[str, ...]
        if result.status == "translated":
            if type(result.lean_body) is not str or not result.lean_body.startswith("by\n"):
                raise ProofStrandError("readable proof reconstruction returned unsafe Lean")
            lean_body = result.lean_body
            if result.lean_statement != node.readable_statement:
                # The strand exposes all reviewed conservative aliases, while
                # reconstruction may safely use only its smaller alias set or
                # the exact expanded formula. Preserve the compact declaration
                # and make Lean itself check their definitional equivalence
                # before executing the authored target-specific tactic body.
                lean_body = (
                    "by\n"
                    f"  change {result.lean_statement}\n"
                    + result.lean_body.removeprefix("by\n")
                )
            node_lines.append(
                f"theorem «{node.name}» : {node.readable_statement} := {lean_body}"
            )
            proof_status = "readable_lean"
            used_dependencies = tuple(result.used_dependencies)
            translated += 1
        elif result.status == "fallback_required":
            if strict_readable:
                raise ProofStrandError(
                    f"theorem {node.name!r} requires a local certificate fallback; "
                    "strict-readable mode forbids it"
                )
            _progress(
                progress,
                stage="certificate",
                completed=index - 1,
                total=plan.node_count,
                theorem=node.name,
                message="checking only this dependency-relative local body",
            )
            curried = _curried_formula(node, formulas)
            local = _checked_local_body(node, curried)
            certificate_rows, certificate_name = _certificate_lines(node, curried, local)
            node_lines.extend(certificate_rows)
            invocation = f"«{certificate_name}»"
            if node.dependencies:
                invocation += " " + " ".join(
                    f"«{dependency}»" for dependency in node.dependencies
                )
            node_lines.extend(
                (
                    f"theorem «{node.name}» : {node.readable_statement} := by",
                    f"  exact {invocation}",
                )
            )
            proof_status = "local_checked_certificate"
            used_dependencies = node.dependencies
            fallback += 1
            del local
        else:
            raise ProofStrandError("readable proof reconstruction has an unknown verdict")
        if not set(used_dependencies).issubset(node.dependencies):
            raise ProofStrandError("readable proof uses an undeclared theorem dependency")
        node_lines.append("")
        source_bytes += sum(len(line.encode("utf-8")) + 1 for line in node_lines)
        if source_bytes > byte_limit:
            raise ProofStrandLimitError(
                f"generated Lean proof strand exceeds its {byte_limit}-byte source limit"
            )
        rows.extend(node_lines)
        source_line_cursor += sum(line.count("\n") + 1 for line in node_lines)
        source_line_end = source_line_cursor
        references[node.name] = node.lean_identifier
        record = {
                "name": node.name,
                "evidence": node.evidence,
                "membership": node.membership,
                "source_module": node.source_module,
                "source_path": node.source_path,
                "source_sha256": node.source_sha256,
                "specification_sha256": node.specification_sha256,
                "depth": node.depth,
                "dependencies": list(node.dependencies),
                "lean_identifier": node.lean_identifier,
                "generated_module": module_name,
                "generated_relative_path": path,
                "source_line_start": source_line_start,
                "source_line_end": source_line_end,
                "statement_sha256": _digest_text(node.statement),
                "readable_statement_sha256": _digest_text(node.readable_statement),
                "aliases": list(node.aliases),
                "local_claim_count": node.local_claim_count,
                "proof_status": proof_status,
                "translated_steps": result.translated_steps,
                "unsupported_steps": list(result.unsupported_steps),
                "diagnostics": list(result.diagnostics),
                "used_dependencies": list(used_dependencies),
                "used_axioms": list(result.used_axioms),
        }
        records.append(record)
        node_blocks.append((node.name, node_lines, record))
        _progress(
            progress,
            stage="certificate" if proof_status == "local_checked_certificate" else "translate",
            completed=index,
            total=plan.node_count,
            theorem=node.name,
        )

    if include_axiom_audit:
        rows.extend((f"#print axioms «{plan.root}»", ""))
    rows.extend((f"end {module_name}", ""))
    code = "\n".join(rows)
    if len(code.encode("utf-8")) > byte_limit:
        raise ProofStrandLimitError("generated Lean proof strand exceeded its source limit")
    if len(code.encode("utf-8")) <= chunk_limit:
        generated_files = ((path, code),)
    else:
        generated_files, code = _segment_modules(
            namespace=module_name,
            token=token,
            final_path=path,
            initial_rows=initial_rows,
            node_blocks=node_blocks,
            root=plan.root,
            include_axiom_audit=include_axiom_audit,
            maximum=chunk_limit,
        )
    file_records = [
        _file_record("PeanoLab.Presentation", "PeanoLab/Presentation.lean", _NOTATION_CODE),
        *[
            _file_record(relative[:-5].replace("/", "."), relative, source)
            for relative, source in generated_files
        ],
    ]
    manifest: dict[str, Any] = {
        "schema": STRAND_SCHEMA,
        "name": plan.root,
        "edition": plan.edition,
        "edition_version": plan.edition_version,
        "edition_identity_sha256": plan.edition_identity_sha256,
        "identity_sha256": plan.identity_sha256,
        "module_name": module_name,
        "relative_path": path,
        "node_count": plan.node_count,
        "edge_count": plan.edge_count,
        "maximum_depth": plan.maximum_depth,
        "total_script_lines": plan.total_script_lines,
        "translated_node_count": translated,
        "fallback_node_count": fallback,
        "definition_count": len(DEFINITIONS),
        "chunk_count": max(0, len(generated_files) - 1),
        "maximum_chunk_bytes": chunk_limit,
        "nodes": records,
        "files": file_records,
        "authority": {
            "lean_compiler_verified": False,
            "public_admission": False,
            "publication": False,
            "training": False,
            "final_evaluation": False,
        },
    }
    metadata_preview = preview_proof_strand(plan)
    preview_prefix, _, _ = metadata_preview.rpartition("\n")
    generation_footer = (
        f"-- Proof-body replay: RUN ({translated} readable Lean candidate(s); "
        f"{fallback} locally checked certificate fallback(s)); "
        "Lean verification: NOT RUN. Compile the complete proof-strand package."
    )
    materialized_preview = _bounded_lines(
        preview_prefix.splitlines(),
        DEFAULT_PREVIEW_BYTES,
        generation_footer,
    )
    _progress(
        progress,
        stage="package",
        completed=plan.node_count,
        total=plan.node_count,
        theorem=plan.root,
    )
    return ProofStrandPackage(
        module_name=module_name,
        relative_path=path,
        code=code,
        manifest=manifest,
        preview=materialized_preview,
        generated_files=generated_files,
    )


def _live_node_blocks(
    plan: ProofStrandPlan,
    package: ProofStrandPackage,
) -> tuple[list[list[str]], set[str]]:
    """Extract only authenticated readable theorem blocks; never replay them."""

    manifest = package.manifest
    if (
        type(manifest) is not dict
        or manifest.get("schema") != STRAND_SCHEMA
        or manifest.get("name") != plan.root
        or manifest.get("identity_sha256") != plan.identity_sha256
        or type(manifest.get("fallback_node_count")) is not int
        or manifest["fallback_node_count"] != 0
    ):
        raise ProofStrandError(
            "Lean Live requires an exact readable-only proof strand; "
            "local certificate fallbacks require the separately installed Lean companion"
        )
    records = manifest.get("nodes")
    if type(records) is not list or len(records) != plan.node_count:
        raise ProofStrandError("Lean Live proof nodes do not match the selected exact strand")
    if type(package.generated_files) is not tuple or not package.generated_files:
        raise ProofStrandError("Lean Live requires exact dependency-topological Lean modules")
    files: dict[str, str] = {}
    for item in package.generated_files:
        if (
            type(item) is not tuple
            or len(item) != 2
            or type(item[0]) is not str
            or type(item[1]) is not str
            or item[0] in files
        ):
            raise ProofStrandError("Lean Live source modules contain an unsafe or duplicate entry")
        files[item[0]] = item[1]
    file_records = manifest.get("files")
    if type(file_records) is not list:
        raise ProofStrandError("Lean Live source module records are missing")
    authenticated = {
        record.get("relative_path"): record
        for record in file_records
        if type(record) is dict and type(record.get("relative_path")) is str
    }
    blocks: list[list[str]] = []
    used_foundations: set[str] = set()
    for expected, record in zip(plan.nodes, records, strict=True):
        if (
            type(record) is not dict
            or record.get("name") != expected.name
            or record.get("proof_status") != "readable_lean"
            or type(record.get("generated_relative_path")) is not str
            or type(record.get("source_line_start")) is not int
            or type(record.get("source_line_end")) is not int
            or record["source_line_start"] <= 0
            or record["source_line_end"] < record["source_line_start"]
        ):
            raise ProofStrandError("Lean Live source-to-theorem mapping is not exact")
        path = record["generated_relative_path"]
        module = files.get(path)
        receipt = authenticated.get(path)
        if (
            module is None
            or type(receipt) is not dict
            or receipt.get("bytes") != len(module.encode("utf-8"))
            or receipt.get("sha256") != _digest_text(module)
        ):
            raise ProofStrandError("Lean Live theorem module failed its exact source digest")
        physical = module.splitlines()
        if record["source_line_end"] > len(physical):
            raise ProofStrandError("Lean Live theorem source interval is outside its module")
        selected = physical[record["source_line_start"] - 1:record["source_line_end"]]
        if not selected or selected[0] != f"-- PROOF NODE: {expected.name}":
            raise ProofStrandError("Lean Live theorem interval lost its exact named boundary")
        theorem = f"theorem «{expected.name}» : "
        theorem_rows = [line for line in selected if not line.startswith("--")]
        if not theorem_rows or not theorem_rows[0].startswith(theorem):
            raise ProofStrandError("Lean Live theorem interval lacks its exact readable declaration")
        summary = expected.summary.replace("\n", " ").replace("\r", " ")
        blocks.append([f"-- {expected.name}: {summary}", *theorem_rows])
        for axiom in record.get("used_axioms", ()):
            if type(axiom) is not str or re.fullmatch(r"PA[1-6]", axiom) is None:
                raise ProofStrandError("Lean Live theorem records an unreviewed foundation")
            used_foundations.add(f"pa{axiom[2]}_sound")
    return blocks, used_foundations


def _live_definitions(identifiers: set[str]) -> list[str]:
    """Inline only exact reviewed definitions actually named by proof blocks."""

    rows: list[str] = []
    for definition in DEFINITIONS:
        if definition.name not in identifiers:
            continue
        if parse_formula_in_context(
            definition.template_source,
            list(definition.parameters),
        ) != definition.template_formula:
            raise ProofStrandError(
                f"Lean Live definition {definition.name!r} changed its exact formula"
            )
        body = _formula_to_lean(
            definition.template_formula,
            tuple(definition.parameters),
            0,
        )
        parameters = " ".join(definition.parameters)
        rows.extend((f"def {definition.name} ({parameters} : Nat) : Prop :=", f"  {body}", ""))
    return rows


def _live_foundations(required: set[str]) -> list[str]:
    rows, _ = _arithmetic_foundations()
    selected: list[str] = []
    current: list[str] = []
    current_name: str | None = None
    for line in [*rows, "theorem _live_foundation_sentinel : True := True.intro"]:
        match = re.match(r"theorem (pa[1-6]_sound)\b", line)
        sentinel = line.startswith("theorem _live_foundation_sentinel")
        if match is not None or sentinel:
            if current_name in required:
                selected.extend(current)
            current = []
            current_name = match.group(1) if match is not None else None
        if current_name is not None:
            current.append(line)
    return selected


def compress_lean_live_codez(
    source: str,
    *,
    max_input_bytes: int = DEFAULT_LIVE_SOURCE_BYTES,
) -> str:
    """Implement Lean Live's official unpadded LZString.compressToBase64 codec."""

    limit = _positive_limit("max_input_bytes", max_input_bytes, MAX_LIVE_CODEC_SOURCE_BYTES)
    if type(source) is not str:
        raise ProofStrandError("Lean Live compression requires exact Unicode source text")
    try:
        payload = source.encode("utf-8")
        utf16 = source.encode("utf-16-le")
    except UnicodeError as error:
        raise ProofStrandError("Lean Live source contains invalid Unicode surrogate data") from error
    if len(payload) > limit:
        raise ProofStrandLimitError("Lean Live compression exceeds its exact source byte limit")
    units = [chr(utf16[index] | (utf16[index + 1] << 8)) for index in range(0, len(utf16), 2)]
    dictionary: dict[str, int] = {}
    pending: set[str] = set()
    next_code = 3
    enlarge_in = 2
    code_bits = 2
    output: list[str] = []
    accumulated = 0
    position = 0

    def write_bits(value: int, count: int) -> None:
        nonlocal accumulated, position
        for _ in range(count):
            accumulated = (accumulated << 1) | (value & 1)
            if position == 5:
                output.append(_LIVE_LZ_ALPHABET[accumulated])
                accumulated = 0
                position = 0
            else:
                position += 1
            value >>= 1

    def consume_dictionary_slot() -> None:
        nonlocal enlarge_in, code_bits
        enlarge_in -= 1
        if enlarge_in == 0:
            enlarge_in = 1 << code_bits
            code_bits += 1

    def emit(word: str) -> None:
        if word in pending:
            value = ord(word[0])
            write_bits(0 if value < 256 else 1, code_bits)
            write_bits(value, 8 if value < 256 else 16)
            consume_dictionary_slot()
            pending.remove(word)
        else:
            write_bits(dictionary[word], code_bits)
        consume_dictionary_slot()

    current = ""
    for unit in units:
        if unit not in dictionary:
            dictionary[unit] = next_code
            next_code += 1
            pending.add(unit)
        candidate = current + unit
        if candidate in dictionary:
            current = candidate
            continue
        emit(current)
        dictionary[candidate] = next_code
        next_code += 1
        current = unit
    if current:
        emit(current)
    write_bits(2, code_bits)
    while True:
        accumulated <<= 1
        if position == 5:
            output.append(_LIVE_LZ_ALPHABET[accumulated])
            break
        position += 1
    return "".join(output)


def decompress_lean_live_codez(
    compressed: str,
    *,
    max_output_bytes: int = DEFAULT_LIVE_SOURCE_BYTES,
) -> str:
    """Decode one canonical bounded official Lean Live codez fragment exactly."""

    limit = _positive_limit("max_output_bytes", max_output_bytes, MAX_LIVE_CODEC_SOURCE_BYTES)
    if (
        type(compressed) is not str
        or not compressed
        or len(compressed) > MAX_LIVE_URL_BYTES
        or _LIVE_LZ_PAYLOAD.fullmatch(compressed) is None
    ):
        raise ProofStrandError("Lean Live compressed payload has a noncanonical unpadded Base64 alphabet")
    values = [_LIVE_LZ_INDEX[character] for character in compressed]
    offset = 0

    def read_bits(count: int) -> int:
        nonlocal offset
        value = 0
        for index in range(count):
            if offset >= 6 * len(values):
                raise ProofStrandError("Lean Live compressed payload is truncated")
            group, position = divmod(offset, 6)
            value |= ((values[group] >> (5 - position)) & 1) << index
            offset += 1
        return value

    first = read_bits(2)
    if first == 2:
        decoded = ""
    elif first not in {0, 1}:
        raise ProofStrandError("Lean Live compressed stream has an invalid first literal")
    else:
        initial = chr(read_bits(8 if first == 0 else 16))
        dictionary: list[str | None] = [None, None, None, initial]
        previous = initial
        entries = [initial]
        emitted_units = 1
        remaining_slots = 4
        code_bits = 3
        while True:
            code = read_bits(code_bits)
            if code in {0, 1}:
                dictionary.append(chr(read_bits(8 if code == 0 else 16)))
                code = len(dictionary) - 1
                remaining_slots -= 1
            elif code == 2:
                break
            if remaining_slots == 0:
                remaining_slots = 1 << code_bits
                code_bits += 1
            if code < len(dictionary) and dictionary[code] is not None:
                entry = dictionary[code]
                assert entry is not None
            elif code == len(dictionary):
                entry = previous + previous[0]
            else:
                raise ProofStrandError("Lean Live compressed stream references an invalid phrase")
            emitted_units += len(entry)
            if emitted_units > limit:
                raise ProofStrandLimitError("Lean Live decompression exceeds its exact output byte limit")
            entries.append(entry)
            dictionary.append(previous + entry[0])
            # A literal and its adjoining phrase can each consume a slot for
            # one emitted UTF-16 unit. The UTF-8 byte limit also bounds units.
            if len(dictionary) > 2 * limit + 4:
                raise ProofStrandLimitError("Lean Live decompression exceeds its phrase limit")
            remaining_slots -= 1
            previous = entry
            if remaining_slots == 0:
                remaining_slots = 1 << code_bits
                code_bits += 1
        units = "".join(entries)
        raw = bytearray()
        for unit in units:
            value = ord(unit)
            raw.extend((value & 255, value >> 8))
        try:
            decoded = raw.decode("utf-16-le")
            utf8 = decoded.encode("utf-8")
        except UnicodeError as error:
            raise ProofStrandError("Lean Live compressed source has invalid UTF-16 surrogates") from error
        if len(utf8) > limit:
            raise ProofStrandLimitError("Lean Live decompression exceeds its exact output byte limit")
    if compress_lean_live_codez(decoded, max_input_bytes=limit) != compressed:
        raise ProofStrandError("Lean Live compressed payload has noncanonical trailing data")
    return decoded


def select_live_share_url(
    source: str,
    *,
    max_url_bytes: int = DEFAULT_LIVE_URL_BYTES,
    max_source_bytes: int = DEFAULT_LIVE_SOURCE_BYTES,
) -> tuple[str | None, str | None, int]:
    """Select the shortest exact official code/codez URL within hard bounds."""

    url_limit = _positive_limit("max_url_bytes", max_url_bytes, MAX_LIVE_URL_BYTES)
    source_limit = _positive_limit(
        "max_source_bytes",
        max_source_bytes,
        MAX_LIVE_CODEC_SOURCE_BYTES,
    )
    if type(source) is not str:
        raise ProofStrandError("Lean Live share source must be exact Unicode text")
    try:
        actual_bytes = len(source.encode("utf-8"))
    except UnicodeError as error:
        raise ProofStrandError("Lean Live share source contains invalid Unicode") from error
    if actual_bytes > source_limit:
        raise ProofStrandLimitError("Lean Live share source exceeds its reviewed byte limit")
    direct = live_lean_url(source)
    compressed = (
        "https://live.lean-lang.org/#codez="
        + quote(
            compress_lean_live_codez(source, max_input_bytes=source_limit),
            safe="",
        )
    )
    candidates = ((direct, "code"), (compressed, "codez"))
    candidate, encoding = min(candidates, key=lambda item: len(item[0].encode("utf-8")))
    encoded_bytes = len(candidate.encode("utf-8"))
    if encoded_bytes > url_limit:
        return None, None, encoded_bytes
    return candidate, encoding, encoded_bytes


def build_live_export(
    plan: ProofStrandPlan,
    package: ProofStrandPackage,
    *,
    max_source_bytes: int = DEFAULT_LIVE_SOURCE_BYTES,
    max_url_bytes: int = DEFAULT_LIVE_URL_BYTES,
) -> LeanLiveExport:
    """Inline a readable-only exact strand for Lean Live without proof replay."""

    if type(plan) is not ProofStrandPlan or type(package) is not ProofStrandPackage:
        raise TypeError("Lean Live export requires one exact proof plan and generated package")
    source_limit = _positive_limit("max_source_bytes", max_source_bytes, DEFAULT_MAX_MODULE_BYTES)
    url_limit = _positive_limit("max_url_bytes", max_url_bytes, MAX_LIVE_URL_BYTES)
    blocks, foundations = _live_node_blocks(plan, package)
    combined = "\n".join(line for block in blocks for line in block)
    identifiers = set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", combined))
    foundations.update(name for name in identifiers if re.fullmatch(r"pa[1-6]_sound", name))
    rows = [
        "-- Standalone constructive Peano proof; remote Lean compilation has not run.",
        f"-- Root: {plan.root}; {plan.node_count} exact named theorem(s).",
        "",
        "set_option maxRecDepth 4096",
        "set_option maxHeartbeats 800000",
        "set_option linter.unusedSimpArgs false",
        "set_option linter.unnecessarySimpa false",
        "",
        "namespace PeanoLabLive",
        "",
        *_live_definitions(identifiers),
        *_live_foundations(foundations),
    ]
    for block in blocks:
        rows.extend(block)
        if _module_size(rows) > source_limit:
            raise ProofStrandLimitError(
                f"standalone Lean Live source exceeds its {source_limit}-byte bound"
            )
    rows.extend((f"#print axioms «{plan.root}»", "", "end PeanoLabLive", ""))
    source = "\n".join(rows)
    payload = source.encode("utf-8")
    if len(payload) > source_limit:
        raise ProofStrandLimitError("standalone Lean Live source exceeds its byte bound")
    if (
        re.search(r"(?m)^\s*import\b", source)
        or re.search(r"\b(?:sorry|sorryAx|native_decide)\b", source)
        or re.search(r"(?m)^\s*axiom\b", source)
        or "PeanoLab.Codec" in source
        or "PeanoLab.Artifact" in source
    ):
        raise ProofStrandError("standalone Lean Live source contains an unavailable or unsafe dependency")
    url, encoding, encoded_bytes = select_live_share_url(
        source,
        max_url_bytes=url_limit,
        max_source_bytes=min(source_limit, MAX_LIVE_CODEC_SOURCE_BYTES),
    )
    shareable = url is not None
    status = "ready" if shareable else "oversized"
    receipt: dict[str, Any] = {
        "schema": LIVE_EXPORT_SCHEMA,
        "theorem": plan.root,
        "edition": plan.edition,
        "edition_version": plan.edition_version,
        "source_sha256": _digest_bytes(payload),
        "source_bytes": len(payload),
        "self_contained": True,
        "core_imports": [],
        "external_import_count": 0,
        "share_url": url,
        "share_encoding": encoding,
        "share_status": status,
        "share_url_bytes": encoded_bytes,
        "share_url_max_bytes": url_limit,
        "remote_compilation": "not_run",
        "fallback_node_count": 0,
        "authority": {
            "lean_live_compiler_verified": False,
            "public_admission": False,
            "publication": False,
            "training": False,
            "final_evaluation": False,
        },
    }
    return LeanLiveExport(source, url, status, len(payload), encoded_bytes, receipt)


def live_hosted_url(source_url: str, *, max_url_bytes: int = DEFAULT_LIVE_URL_BYTES) -> str:
    """Hand off an already publicly reachable HTTPS Lean source; do not upload it."""

    limit = _positive_limit("max_url_bytes", max_url_bytes, MAX_LIVE_URL_BYTES)
    if type(source_url) is not str or len(source_url.encode("utf-8")) > limit:
        raise ProofStrandError("the hosted Lean source URL is not bounded exact text")
    try:
        parsed = urlsplit(source_url)
    except (TypeError, ValueError) as error:
        raise ProofStrandError("the hosted Lean source URL is malformed") from error
    hostname = parsed.hostname
    if (
        parsed.scheme != "https"
        or not hostname
        or hostname.lower() == "localhost"
        or hostname.lower().endswith((".localhost", ".local", ".internal", ".invalid", ".test"))
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or not parsed.path.endswith(".lean")
    ):
        raise ProofStrandError("Lean Live hosted handoff requires a public HTTPS .lean source")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        if "." not in hostname:
            raise ProofStrandError(
                "Lean Live hosted handoff requires an explicitly public HTTPS hostname"
            ) from None
    else:
        if not address.is_global:
            raise ProofStrandError(
                "Lean Live hosted handoff refuses private or non-routable source addresses"
            )
    result = "https://live.lean-lang.org/#url=" + quote(source_url, safe="")
    if len(result.encode("utf-8")) > limit:
        raise ProofStrandLimitError("Lean Live hosted handoff exceeds its URL byte bound")
    return result


__all__ = [
    "STRAND_SCHEMA",
    "MAX_STRAND_NODES",
    "MAX_STRAND_EDGES",
    "MAX_STRAND_DEPTH",
    "DEFAULT_CHUNK_BYTES",
    "DEFAULT_LIVE_SOURCE_BYTES",
    "DEFAULT_LIVE_URL_BYTES",
    "MAX_LIVE_URL_BYTES",
    "MAX_LIVE_CODEC_SOURCE_BYTES",
    "LIVE_EXPORT_SCHEMA",
    "ProofStrandError",
    "ProofStrandLimitError",
    "ProofStrandClaim",
    "ProofStrandNode",
    "ProofStrandPlan",
    "ProofStrandPackage",
    "LeanLiveExport",
    "readable_strand_formula",
    "plan_proof_strand",
    "preview_proof_strand",
    "build_proof_strand",
    "compress_lean_live_codez",
    "decompress_lean_live_codez",
    "select_live_share_url",
    "build_live_export",
    "live_hosted_url",
]
