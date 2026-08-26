"""Bounded HA development syntax and untrusted, typed public-tactic actions.

This is an opt-in development profile, not the completed H0 fragment contract
or a decision procedure.  A compiled action or its receipt is never a proof:
the ordinary public surface and original-goal kernel check remain mandatory.
Existing ``surface-macro-v0`` artifacts are deliberately unaffected.
"""

from __future__ import annotations

from dataclasses import asdict
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import stat
import unicodedata

from peano_lab.batch import capability_sha256
from peano_lab.engine.compact_arith import DEFAULT_COMPACT_ARITH_LIMITS
from peano_lab.engine.norm_num import DEFAULT_NORM_NUM_LIMITS
from peano_lab.engine.trace import render_goals
from peano_lab.engine.tactics import (
    MAX_LIVE_PROOF_DEPTH,
    MAX_LIVE_PROOF_NODES,
    MAX_LIVE_PROOF_OBJECTS,
    TacticError,
)
from peano_lab.kernel.checker import axiom_formula
from peano_lab.kernel.formulas import (
    And, Bot, Eq, Exists, Forall, Formula, Imp, Or,
    parse_formula_in_context, pretty_formula,
)
from peano_lab.kernel.terms import (
    Add, Mul, ParseError, Succ, Term, Var, Zero, _TokenStream,
    parse_term_in_context, pretty_term,
)
from peano_lab.ui.prove import ProofSession, SurfaceCapabilities, run_surface
from training.peano_policy.search import state_sha256


PROFILE_VERSION = 1
PROFILE_ID = "hydra-ha-development-v1"
ACTION_VERSION = 1
MAX_SOURCE_BYTES = 4096
MAX_JSON_BYTES = 16384
MAX_AST_NODES = 256
MAX_AST_DEPTH = 96
MAX_BINDERS = 16
MAX_HYPOTHESES = 16
MAX_NUMERAL = 64
MAX_IDENTIFIER_CHARS = 64
MAX_TOKENS = 512
MAX_PAREN_DEPTH = 48
MAX_SPECIALIZATIONS = 16
MAX_RECEIPT_GOALS = 64
MAX_RECEIPT_STATE_BYTES = 65536

_ROOT = Path(__file__).resolve().parents[2]
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_']{0,63}\Z")
_AXIOMS = tuple(f"PA{index}" for index in range(1, 7))
_RESERVED = frozenset({"S", "forall", "exists", "bot", "false", "DNE", "goal"})
_SYNTAX_TOKENS = frozenset(
    {"(", ")", ",", "+", "*", "·", "=", ".", "~", "¬", "⊥",
     "->", "→", "/\\", "∧", "\\/", "∨", "forall", "∀", "exists", "∃", "<=", "≤"}
)
_DISPATCH = frozenset({"refl", "assumption", "simp", "norm_num", "compact_arith"})
_FIELDS = {
    "Use": frozenset({"v", "op", "name", "specializations"}),
    "Cut": frozenset({"v", "op", "kind", "name", "formula"}),
    "Witness": frozenset({"v", "op", "term"}),
    "Induct": frozenset({"v", "op", "variable", "motive"}),
    "Rewrite": frozenset({"v", "op", "source", "direction", "location"}),
    "Split": frozenset({"v", "op", "kind", "name"}),
    "Dispatch": frozenset({"v", "op", "solver", "premises", "bounds"}),
}
_SOURCE_PATHS = (
    "training/peano_hydra/protocol.py",
    "peano-lab/py/peano_lab/kernel/terms.py",
    "peano-lab/py/peano_lab/kernel/formulas.py",
    "peano-lab/py/peano_lab/kernel/subst.py",
    "peano-lab/py/peano_lab/kernel/proofs.py",
    "peano-lab/py/peano_lab/kernel/checker.py",
    "peano-lab/py/peano_lab/engine/state.py",
    "peano-lab/py/peano_lab/engine/tactics.py",
    "peano-lab/py/peano_lab/engine/tacticals.py",
    "peano-lab/py/peano_lab/engine/trace.py",
    "peano-lab/py/peano_lab/engine/induction.py",
    "peano-lab/py/peano_lab/engine/rewrite.py",
    "peano-lab/py/peano_lab/engine/proof_reduction.py",
    "peano-lab/py/peano_lab/engine/norm_num.py",
    "peano-lab/py/peano_lab/engine/compact_arith.py",
    "peano-lab/py/peano_lab/ui/prove.py",
    "peano-lab/py/peano_lab/batch.py",
    "training/peano_policy/search.py",
)


class ProtocolError(ValueError):
    """An input is outside the explicit development protocol; no proof claim."""


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _text_bytes(value: object, label: str, limit: int) -> bytes:
    if type(value) is not str or not value:
        raise ProtocolError(f"{label} must be non-empty text")
    try:
        raw = value.encode("utf-8")
    except UnicodeError:
        raise ProtocolError(f"{label} must be valid UTF-8 text") from None
    if len(raw) > limit:
        raise ProtocolError(f"{label} exceeds its {limit}-byte limit")
    return raw


def _identifier(value: object, label: str, *, reference: bool = False) -> str:
    if type(value) is not str or _IDENTIFIER.fullmatch(value) is None:
        raise ProtocolError(f"{label} must be a safe ASCII identifier")
    if value in _RESERVED or (not reference and value in _AXIOMS):
        raise ProtocolError(f"{label} uses a reserved identifier")
    return value


def _names(values: object, label: str, limit: int) -> tuple[str, ...]:
    if type(values) not in (tuple, list) or len(values) > limit:
        raise ProtocolError(f"{label} must be a finite list/tuple of at most {limit} names")
    result = tuple(_identifier(value, label) for value in values)
    if len(result) != len(set(result)):
        raise ProtocolError(f"{label} must not contain duplicate names")
    return result


def _syntax_preflight(source: object) -> str:
    _text_bytes(source, "formula/term source", MAX_SOURCE_BYTES)
    assert type(source) is str
    # No escaped names, explicit de Bruijn indices, engine metavariables,
    # comments, line breaks, or Unicode identifier lookalikes enter the parser.
    if any(char.isspace() and char != " " for char in source):
        raise ProtocolError("formula/term source must be a single line using ASCII spaces")
    try:
        tokens = _TokenStream(source).tokens
    except (ParseError, RecursionError) as exc:
        raise ProtocolError(f"invalid formula/term syntax: {exc}") from None
    if not tokens or len(tokens) > MAX_TOKENS:
        raise ProtocolError(f"formula/term source exceeds the {MAX_TOKENS}-token limit")
    nesting = 0
    in_binders = False
    for token in tokens:
        text = token.text
        if in_binders:
            if text == ".":
                in_binders = False
            else:
                _identifier(text, "bound variable")
        elif text in {"forall", "∀", "exists", "∃"}:
            in_binders = True
        if text == "(":
            nesting += 1
            if nesting > MAX_PAREN_DEPTH:
                raise ProtocolError("formula/term source exceeds the parenthesis-depth limit")
        elif text == ")":
            nesting -= 1
            if nesting < 0:
                raise ProtocolError("unbalanced formula/term parentheses")
        if text in _SYNTAX_TOKENS or text in {"S", "bot", "false"}:
            continue
        if text.isascii() and text.isdecimal():
            significant = text.lstrip("0") or "0"
            if len(significant) > 2 or int(significant) > MAX_NUMERAL:
                raise ProtocolError(f"numerals must not exceed {MAX_NUMERAL}")
            continue
        _identifier(text, "formula/term identifier")
    if nesting:
        raise ProtocolError("unbalanced formula/term parentheses")
    return source


def _audit_ast(root: Formula | Term, *, variables: int) -> None:
    # Occurrences, rather than Python object identities, are charged.  Input
    # ASTs use only the original kernel constructors, never engine MetaVar.
    stack: list[tuple[Formula | Term, int, int]] = [(root, 1, 0)]
    count = 0
    while stack:
        node, depth, binders = stack.pop()
        count += 1
        if count > MAX_AST_NODES or depth > MAX_AST_DEPTH:
            raise ProtocolError("formula/term exceeds the AST node/depth limits")
        kind = type(node)
        if kind is Var:
            if type(node.index) is not int or not 0 <= node.index < variables + binders:
                raise ProtocolError("formula/term has an out-of-scope variable")
            children = ()
        elif kind in (Zero, Bot):
            children = ()
        elif kind is Succ:
            children = (node.term,)
        elif kind in (Add, Mul, Eq, And, Or, Imp):
            children = (node.left, node.right)
        elif kind in (Forall, Exists):
            binders += 1
            if binders + variables > MAX_BINDERS:
                raise ProtocolError("formula exceeds the bound/context-variable limit")
            children = (node.body,)
        else:
            raise ProtocolError("formula/term uses an out-of-profile AST constructor")
        stack.extend((child, depth + 1, binders) for child in children)


def _formula(source: object, variables: tuple[str, ...]) -> str:
    text = _syntax_preflight(source)
    try:
        parsed = parse_formula_in_context(text, list(variables))
        _audit_ast(parsed, variables=len(variables))
        canonical = pretty_formula(parsed, list(variables))
        # Canonicalization must not escape the admission grammar/bounds, e.g.
        # a long explicit S-chain becoming a forbidden decimal literal.
        _syntax_preflight(canonical)
        return canonical
    except (ParseError, RecursionError) as exc:
        raise ProtocolError(f"invalid or open development formula: {exc}") from None


def _term(source: object, variables: tuple[str, ...]) -> str:
    text = _syntax_preflight(source)
    try:
        parsed = parse_term_in_context(text, list(variables))
        _audit_ast(parsed, variables=len(variables))
        canonical = pretty_term(parsed, list(variables))
        _syntax_preflight(canonical)
        return canonical
    except (ParseError, RecursionError) as exc:
        raise ProtocolError(f"invalid or open development term: {exc}") from None


def validate_statement(source: str) -> str:
    """Return the canonical, closed native formula or reject outside the profile.

    Acceptance checks syntax/scope/resources only.  Even ``0 = 1`` is a valid
    input statement, and this function does not assert it or its negation.
    """

    return _formula(source, ())


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for name, value in pairs:
        if name in result:
            raise ProtocolError(f"duplicate JSON field {name!r}")
        result[name] = value
    return result


def _reject_number(value: str) -> None:
    raise ProtocolError(f"non-integer JSON number {value!r} is not an action value")


def _record(record: object) -> dict[str, object]:
    if type(record) in (str, bytes):
        if type(record) is bytes:
            if len(record) > MAX_JSON_BYTES:
                raise ProtocolError("action JSON exceeds its byte limit")
            try:
                record = record.decode("utf-8")
            except UnicodeError:
                raise ProtocolError("action JSON must be valid UTF-8") from None
        _text_bytes(record, "action JSON", MAX_JSON_BYTES)
        try:
            record = json.loads(
                record, object_pairs_hook=_pairs, parse_constant=_reject_number,
                parse_float=_reject_number,
            )
        except (ValueError, RecursionError) as exc:
            raise ProtocolError(f"invalid action JSON: {exc}") from None
    if type(record) is not dict:
        raise ProtocolError("an action must be an exact JSON object")
    # Also bound already-decoded objects: generators, custom objects, cycles,
    # huge collections, and deep nested programs are not JSON action fields.
    stack = [(record, 0)]
    count = 0
    while stack:
        value, depth = stack.pop()
        count += 1
        if count > 256 or depth > 4:
            raise ProtocolError("action JSON exceeds structural limits")
        if type(value) is dict:
            if len(value) > 8:
                raise ProtocolError("action object has too many fields")
            for key, child in value.items():
                if type(key) is not str or len(key) > MAX_IDENTIFIER_CHARS:
                    raise ProtocolError("action field names must be short text")
                stack.append((child, depth + 1))
        elif type(value) is list:
            if len(value) > MAX_SPECIALIZATIONS:
                raise ProtocolError("action list exceeds its item limit")
            stack.extend((child, depth + 1) for child in value)
        elif type(value) is str:
            _text_bytes(value, "action field", MAX_SOURCE_BYTES)
        elif value is None or type(value) is bool:
            pass
        elif type(value) is int:
            if not 0 <= value <= MAX_NUMERAL:
                raise ProtocolError("action integer exceeds its limit")
        else:
            raise ProtocolError("action fields must contain only exact JSON values")
    if len(_canonical(record)) > MAX_JSON_BYTES:
        raise ProtocolError("action JSON exceeds its byte limit")
    if type(record.get("v")) is not int or record["v"] != ACTION_VERSION:
        raise ProtocolError(f"action v must be exactly {ACTION_VERSION}")
    operation = record.get("op")
    if type(operation) is not str or operation not in _FIELDS:
        raise ProtocolError("unknown action operation")
    if set(record) != _FIELDS[operation]:
        raise ProtocolError(f"{operation} has missing or unknown fields")
    return json.loads(_canonical(record))


def _authority(capabilities: object) -> SurfaceCapabilities:
    if type(capabilities) is not SurfaceCapabilities:
        raise ProtocolError("capabilities must be an exact SurfaceCapabilities value")
    if capabilities.allowed_commands is None or capabilities.allowed_theorems is None:
        raise ProtocolError("development actions require finite command and theorem authority")
    return capabilities


def _enum(value: object, choices: set[str] | frozenset[str], label: str) -> str:
    if type(value) is not str or value not in choices:
        raise ProtocolError(f"unsupported {label}")
    return value


def _compile_action(
    record: object, *, capabilities: SurfaceCapabilities,
    variables: object, hypotheses: object,
) -> tuple[dict[str, object], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    authority = _authority(capabilities)
    variables = _names(variables, "variables", MAX_BINDERS)
    hypotheses = _names(hypotheses, "hypotheses", MAX_HYPOTHESES)
    if set(variables) & set(hypotheses):
        raise ProtocolError("variables and hypotheses must have distinct names")
    action = _record(record)
    operation = action["op"]
    commands: list[str] = []

    def local(value: object, label: str) -> str:
        name = _identifier(value, label)
        if name not in hypotheses:
            raise ProtocolError(f"{label} is not an available local hypothesis")
        return name

    def fresh(value: object, label: str) -> str:
        name = _identifier(value, label)
        if name in variables or name in hypotheses:
            raise ProtocolError(f"{label} collides with the current context")
        return name

    if operation == "Use":
        name = _identifier(action["name"], "Use.name", reference=True)
        terms = action["specializations"]
        if type(terms) is not list:
            raise ProtocolError("Use.specializations must be a JSON array")
        action["specializations"] = [_term(term, variables) for term in terms]
        if name in _AXIOMS:
            if terms:
                raise ProtocolError("native PA constants do not accept explicit specializations")
        elif name not in hypotheses:
            fresh(name, "Use.name")
            try:
                authority.require_theorem(name)
            except TacticError as exc:
                raise ProtocolError(str(exc)) from None
            commands.append(f"use {name}")
        commands.extend(f"specialize {name} {term}" for term in action["specializations"])
        commands.append(f"apply {name}")
    elif operation == "Cut":
        kind = _enum(action["kind"], {"have", "suffices"}, "Cut.kind")
        name = fresh(action["name"], "Cut.name")
        action["formula"] = _formula(action["formula"], variables)
        commands.append(f"{kind} {name} : {action['formula']}")
    elif operation == "Witness":
        action["term"] = _term(action["term"], variables)
        commands.append(f"exists {action['term']}")
    elif operation == "Induct":
        name = _identifier(action["variable"], "Induct.variable")
        if name not in variables:
            raise ProtocolError("Induct.variable is not in the current context")
        _enum(action["motive"], {"goal"}, "Induct.motive (only the current goal is supported)")
        commands.append(f"induction {name}")
    elif operation == "Rewrite":
        source = local(action["source"], "Rewrite.source")
        direction = _enum(action["direction"], {"forward", "backward"}, "Rewrite.direction")
        location = action["location"]
        suffix = "" if location == "goal" else f" at {local(location, 'Rewrite.location')}"
        commands.append(f"rewrite {'<- ' if direction == 'backward' else ''}{source}{suffix}")
    elif operation == "Split":
        kind = _enum(action["kind"], {"intro", "and", "left", "right", "cases"}, "Split.kind")
        name = action["name"]
        if kind == "intro":
            commands.append("intro" if name is None else f"intro {fresh(name, 'Split.name')}")
        elif kind == "cases":
            commands.append(f"cases {local(name, 'Split.name')}")
        else:
            if name is not None:
                raise ProtocolError("Split.name must be null for and/left/right")
            commands.append("split" if kind == "and" else kind)
    else:
        solver = _enum(action["solver"], _DISPATCH, "Dispatch.solver")
        premises = action["premises"]
        if type(premises) is not list:
            raise ProtocolError("Dispatch.premises must be a JSON array")
        names = tuple(local(name, "Dispatch.premise") for name in premises)
        if len(set(names)) != len(names):
            raise ProtocolError("Dispatch premises must not contain duplicates")
        bounds = action["bounds"]
        if (type(bounds) is not dict or set(bounds) != {"max_calls"}
                or type(bounds["max_calls"]) is not int or bounds["max_calls"] != 1):
            raise ProtocolError("Dispatch.bounds must be exactly {max_calls: 1}")
        if premises and solver not in {"simp", "compact_arith"}:
            raise ProtocolError("this native Dispatch solver does not accept named premises")
        suffix = " [" + ", ".join(names) + "]" if names else ""
        commands.append(solver + suffix)

    try:
        for command in commands:
            authority.require_command(command.split(" ", 1)[0])
    except TacticError as exc:
        raise ProtocolError(str(exc)) from None
    return action, tuple(commands), variables, hypotheses


def compile_action(
    record: object, *, capabilities: SurfaceCapabilities,
    variables: tuple[str, ...] = (), hypotheses: tuple[str, ...] = (),
) -> tuple[str, ...]:
    """Compile exact typed JSON to public primitives, without running a proof.

    Context names are index-to-name order (innermost variable first). ``Use``
    may emit several primitives. Execute the generated ``'; '.join(commands)``
    as ONE ``run_surface`` transaction to avoid publishing a partial macro.
    All success/failure tracing and original-goal verification remain the
    responsibility of the existing runner; never treat compilation as QED.
    """

    return _compile_action(
        record, capabilities=capabilities, variables=variables, hypotheses=hypotheses,
    )[1]


def action_receipt(
    record: object, *, capabilities: SurfaceCapabilities, goals: tuple[str, ...],
    focus: int = 0, variables: tuple[str, ...] = (), hypotheses: tuple[str, ...] = (),
) -> dict[str, object]:
    """Bind a proposal to caller-rendered state, authority and source profile.

    This is detached provenance, not a signature or execution/QED certificate.
    ``goals`` must come from the runner's complete canonical goal observation;
    a consumer must compare it to the actual state before executing commands.
    """

    if type(goals) is not tuple or not 1 <= len(goals) <= MAX_RECEIPT_GOALS:
        raise ProtocolError("receipt goals must be a non-empty bounded tuple")
    if type(focus) is not int or not 0 <= focus < len(goals):
        raise ProtocolError("receipt focus is outside the goal tuple")
    total = 0
    for goal in goals:
        total += len(_text_bytes(goal, "receipt goal", MAX_RECEIPT_STATE_BYTES))
        if any(unicodedata.category(char) in {"Cc", "Cf", "Cs", "Zl", "Zp"} for char in goal):
            raise ProtocolError("receipt goals must be single-line canonical observations")
    if total > MAX_RECEIPT_STATE_BYTES:
        raise ProtocolError("receipt state exceeds its byte limit")
    action, commands, variables, hypotheses = _compile_action(
        record, capabilities=capabilities, variables=variables, hypotheses=hypotheses,
    )
    authority = {
        "label": capabilities.label,
        "allowed_commands": sorted(capabilities.allowed_commands),
        "allowed_theorems": sorted(capabilities.allowed_theorems),
    }
    result = {
        "v": 1,
        "kind": "hydra-development-action-proposal",
        "profile_sha256": development_profile()["profile_sha256"],
        "action": action,
        "action_sha256": _sha256(action),
        "commands": list(commands),
        "commands_sha256": _sha256(list(commands)),
        "goals": list(goals),
        "state_sha256": state_sha256(goals),
        "focus": focus,
        "variables": list(variables),
        "hypotheses": list(hypotheses),
        "authority": authority,
        "environment_sha256": capability_sha256(capabilities),
        "kernel_checked": False,
    }
    result["receipt_sha256"] = _sha256(result)
    return result


def execute_action(
    owner: ProofSession, record: object, *, capabilities: SurfaceCapabilities,
) -> tuple[ProofSession, dict[str, object]]:
    """Execute one typed action atomically through the existing public surface.

    Only the first goal is focused.  The supplied immutable state/history and
    replay program are never changed, including if a later ``Use`` primitive
    fails.  The supplied append-only trace records the one successful or
    failed transaction.  No QED is performed here, even when all goals close.

    Admission bounds constrain the original statement and action payloads;
    generated intermediate certificates retain the existing native bounds.
    """

    if type(owner) is not ProofSession or owner.classical is not False:
        raise ProtocolError("action execution needs an intuitionistic ProofSession")
    if owner.original_names:
        raise ProtocolError("development action execution requires a closed original goal")
    canonical = validate_statement(owner.target_source)
    if canonical != pretty_formula(owner.original_target, []):
        raise ProtocolError("session source does not match its original target")
    goal = owner.state.current()
    if goal is None:
        raise ProtocolError("there is no open goal for an action")
    proposal = action_receipt(
        record, capabilities=capabilities, goals=tuple(render_goals(owner.state)),
        variables=goal.variables, hypotheses=tuple(name for name, _ in goal.context),
    )
    line = "; ".join(proposal["commands"])
    # The only multi-command action is Use.  Its import/specialization prefix
    # preserves exactly one focused goal, so native semicolon sequencing is
    # linear here and cannot accidentally apply a suffix to unrelated goals.
    after = run_surface(owner, line, capabilities=capabilities)
    if development_profile()["profile_sha256"] != proposal["profile_sha256"]:
        raise ProtocolError("development profile changed during action execution")
    goals_after = tuple(render_goals(after.state))
    receipt = {
        "v": 1, "kind": "hydra-development-action-execution", "status": "applied",
        "proposal": proposal, "surface_transaction": line,
        "goals_after": list(goals_after), "state_after_sha256": state_sha256(goals_after),
        "history_before": len(owner.state.history), "history_after": len(after.state.history),
        "kernel_checked": False,
    }
    receipt["receipt_sha256"] = _sha256(receipt)
    return after, receipt


def _source_key() -> tuple[tuple[str, int, int, int, int], ...]:
    rows = []
    for relative in _SOURCE_PATHS:
        path = _ROOT / relative
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_size > 2_000_000:
            raise ProtocolError(f"profile source is not a bounded regular file: {relative}")
        rows.append((relative, info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_ino))
    return tuple(rows)


@lru_cache(maxsize=1)
def _profile_json(key: tuple[tuple[str, int, int, int, int], ...]) -> bytes:
    sources = []
    for relative, size, _, _, _ in key:
        raw = (_ROOT / relative).read_bytes()
        if len(raw) != size:
            raise ProtocolError("profile source changed while hashing")
        sources.append({"path": relative, "bytes": size, "sha256": hashlib.sha256(raw).hexdigest()})
    if _source_key() != key:
        raise ProtocolError("profile source changed while hashing")
    profile = {
        "v": PROFILE_VERSION,
        "profile_id": PROFILE_ID,
        "status": "bounded-development-only",
        "h0_complete": False,
        "research_claim_eligible": False,
        "legacy_surface": "surface-macro-v0 remains separate and unchanged",
        "logic": "intuitionistic first-order arithmetic with equality",
        "classical": False,
        "grammar": {
            "sorts": ["Nat"],
            "terms": {"Var": ["de_bruijn_index"], "Zero": [], "Succ": ["term"],
                      "Add": ["term", "term"], "Mul": ["term", "term"]},
            "formulas": {"Eq": ["term", "term"], "Bot": [], "Imp": ["formula", "formula"],
                         "And": ["formula", "formula"], "Or": ["formula", "formula"],
                         "Forall": ["formula"], "Exists": ["formula"]},
            "statements": "closed formulas only; no implicit universal closure",
            "binders": "de Bruijn, nearest binder index 0; context index-to-name order",
            "alpha_equivalence": "native AST equality; canonical fresh binder pretty-printing",
            "substitution": "native capture-avoiding lifting/substitution",
            "identifier_pattern": _IDENTIFIER.pattern,
            "reserved_identifiers": sorted(_RESERVED | set(_AXIOMS)),
            "surface_sugar": {
                "numerals": "unary successor ASTs through 64",
                "negation": "A -> Bot",
                "le": "a <= b becomes exists k. k + a = b (capture-avoiding)",
                "ascii_unicode": ["forall/∀", "exists/∃", "->/→", "/\\/∧", "\\//∨",
                                  "*/·", "<=/≤", "~/¬", "bot/false/⊥"],
            },
            "translations": [],
            "extensions": [],
            "explicit_indices_and_metavariables": False,
        },
        "axioms": [{"name": name, "formula": pretty_formula(axiom_formula(name), [])}
                   for name in _AXIOMS],
        "proof_rules": ["Hyp", "Axiom", "EqRefl", "EqSym", "EqTrans", "CongS", "CongAdd", "CongMul",
                        "EqSubst", "ImpIntro", "ImpElim", "AndIntro", "AndElimL", "AndElimR",
                        "OrIntroL", "OrIntroR", "OrElim", "BotElim", "ForallIntro", "ForallElim",
                        "ExistsIntro", "ExistsElim", "Cut", "Ind"],
        "induction": {
            "domain": "Nat", "motive": "current focused goal only",
            "context": "native dependent-context generalization and eigenvariable checks",
            "formula_restriction": "profile grammar and resource ceilings; not a decision fragment",
            "arbitrary_explicit_motive_supported": False,
        },
        "limits": {
            "source_utf8_bytes": MAX_SOURCE_BYTES, "action_json_bytes": MAX_JSON_BYTES,
            "ast_nodes": MAX_AST_NODES, "ast_depth": MAX_AST_DEPTH,
            "bound_plus_context_variables": MAX_BINDERS, "local_hypotheses": MAX_HYPOTHESES,
            "numeral": MAX_NUMERAL, "identifier_chars": MAX_IDENTIFIER_CHARS,
            "tokens": MAX_TOKENS, "parenthesis_depth": MAX_PAREN_DEPTH,
            "specializations": MAX_SPECIALIZATIONS,
            "receipt_goals": MAX_RECEIPT_GOALS, "receipt_state_bytes": MAX_RECEIPT_STATE_BYTES,
            "live_proof_nodes": MAX_LIVE_PROOF_NODES, "live_proof_objects": MAX_LIVE_PROOF_OBJECTS,
            "live_proof_depth": MAX_LIVE_PROOF_DEPTH,
            "scope": "statement/action admission; derived states retain source-bound native proof ceilings",
        },
        "actions": {
            "version": ACTION_VERSION, "required_fields": {op: sorted(fields) for op, fields in _FIELDS.items()},
            "json_value_types": {
                "v": "integer exactly 1 (not Boolean)", "op": "case-sensitive string tag",
                "name_variable_source_direction_location_kind_motive_solver": "strings, except Split.name may be null",
                "formula_term": "single-line source strings",
                "specializations_premises": "JSON arrays of strings",
                "bounds": "exact object with integer max_calls=1 (not Boolean)",
            },
            "duplicate_unknown_fields": "reject", "arbitrary_tactical_programs": False,
            "Use": {"name": "local hypothesis, PA1..PA6, or finite allowed checked theorem",
                    "specializations": "bounded term array; PA constants require empty array",
                    "compile": "[use name if imported]; [specialize name term]*; apply name"},
            "Cut": {"kind": ["have", "suffices"], "name": "fresh identifier", "formula": "scoped formula"},
            "Witness": {"term": "scoped term", "compile": "exists term"},
            "Induct": {"variable": "existing variable", "motive": ["goal"], "compile": "induction variable"},
            "Rewrite": {"source": "local hypothesis", "direction": ["forward", "backward"],
                        "location": "goal or local hypothesis"},
            "Split": {"kind": ["intro", "and", "left", "right", "cases"],
                      "name": "fresh intro name or null; local cases name; null otherwise"},
            "Dispatch": {"solver": sorted(_DISPATCH), "premises": "distinct local names for simp/compact_arith only",
                         "bounds": {"max_calls": 1}, "external_solvers": False},
            "transaction": "one generated semicolon sequence through run_surface; failed state/history unchanged",
        },
        "native_dispatch_limits": {
            "norm_num": asdict(DEFAULT_NORM_NUM_LIMITS),
            "compact_arith": asdict(DEFAULT_COMPACT_ARITH_LIMITS),
            "simp": {"max_steps": 4096, "builtin_rules": ["PA3", "PA4", "PA5", "PA6"]},
            "refl_assumption": "one public primitive under live-certificate ceilings",
            "caller_overrides": False,
        },
        "authority": {
            "commands_and_imports": "finite caller-owned SurfaceCapabilities, bound in each receipt",
            "import_check": "public use independently checks the imported certificate",
            "catalog_identity": "separate caller-owned epoch; not frozen by this syntax profile",
            "external_solver_status_is_evidence": False,
        },
        "evidence": {
            "positive": "independent native kernel replay against the original closed goal",
            "proposal_receipt": "provenance only, never an execution or QED certificate",
            "failure_or_budget_exhaustion": "unknown; not unprovability or falsity",
            "negative_result_supported": False, "decision_procedure_claim": False,
            "h0_remaining": "independent semantic/reference conformance, cold replay and protocol gate reviews",
        },
        "source_bindings": sources,
        "canonical_encoding": "UTF-8 JSON, sorted keys, compact separators, no nonfinite values",
    }
    profile["profile_sha256"] = _sha256(profile)
    return _canonical(profile)


def development_profile() -> dict[str, object]:
    """Return a detached canonical profile, source-bound without corpus replay.

    ``profile_sha256`` hashes the canonical object with that one field omitted.
    File identity changes invalidate the small in-process source-hash cache.
    """

    return json.loads(_profile_json(_source_key()))


__all__ = [
    "PROFILE_VERSION", "PROFILE_ID", "ACTION_VERSION", "ProtocolError",
    "development_profile", "validate_statement", "compile_action", "action_receipt", "execute_action",
]
