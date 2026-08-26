"""Reconstruct readable Lean proofs from dependency-relative Peano scripts.

The generated text has no proof authority: Lean must elaborate the exact
theorem and all imported dependency theorems.  Reconstruction runs only the
small dependency-curried local script, never recursive theorem replay or a
complete transitive proof certificate.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass
import re
from typing import Any

from ..engine.state import Goal, ProofState, start
from ..engine.tactics import TacticError, apply_tactic
from ..kernel.formulas import (
    And,
    Bot,
    Eq,
    Exists,
    Forall,
    Formula,
    Imp,
    Or,
    parse_formula_with_names,
)
from ..kernel.terms import Add, Mul, Succ, Zero, numeral_value, parse_term_in_context
from .lean import _formula_to_lean, _term_to_lean, _validate_theorem_name, formula_to_lean
from .lean_presentation import (
    MAX_SCRIPT_BYTES,
    MAX_SCRIPT_LINES,
    _LEAN_KEYWORDS,
    _render_readable_formula,
    readable_formula,
)
from .theorems import TheoremSpec, get


MAX_RECONSTRUCTION_STEPS = 4_096
MAX_RECONSTRUCTION_GOALS = 1_024
MAX_RECONSTRUCTED_BYTES = 1_048_576
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_']*\Z")
_REFERENCE = re.compile(
    r"(?:[A-Za-z_][A-Za-z0-9_']*|«[A-Za-z_][A-Za-z0-9_']*»)"
    r"(?:\.(?:[A-Za-z_][A-Za-z0-9_']*|«[A-Za-z_][A-Za-z0-9_']*»))*\Z"
)

SUPPORTED_TACTICS = frozenset(
    {
        "intro",
        "have",
        "suffices",
        "specialize",
        "forall_elim",
        "induction",
        "apply",
        "split",
        "left",
        "right",
        "cases",
        "exfalso",
        "exists",
        "refl",
        "symm",
        "trans",
        "congr",
        "exact",
        "assumption",
        "rewrite",
        "simp",
        "norm_num",
    }
)

DEFAULT_AXIOM_REFERENCES: dict[str, str] = {
    "PA1": "Nat.succ_ne_zero",
    "PA2": "Nat.succ.inj",
    "PA3": "Nat.add_zero",
    "PA4": "Nat.add_succ",
    "PA5": "Nat.mul_zero",
    "PA6": "Nat.mul_succ",
}


class ReconstructionError(ValueError):
    """Unsafe metadata or an impossible exact proof-reconstruction contract."""


@dataclass(frozen=True, slots=True)
class LeanProofReconstruction:
    """One executable candidate or an honestly classified certificate fallback."""

    name: str
    lean_statement: str
    lean_body: str
    used_dependencies: tuple[str, ...]
    used_axioms: tuple[str, ...]
    translated_steps: int
    unsupported_steps: tuple[str, ...]
    status: str
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _GoalFrame:
    indent: int
    marker: str = ""


def _safe_identifier(value: object, label: str) -> str:
    if (
        type(value) is not str
        or len(value) > 128
        or _IDENTIFIER.fullmatch(value) is None
        or value in _LEAN_KEYWORDS
    ):
        raise ReconstructionError(f"{label} must be a safe Lean identifier")
    return value


def _safe_reference(value: object, label: str) -> str:
    if type(value) is not str or len(value) > 512 or _REFERENCE.fullmatch(value) is None:
        raise ReconstructionError(f"{label} must be a safe checked Lean theorem reference")
    return value


def _closed_formula(source: str, label: str) -> Formula:
    try:
        formula, names = parse_formula_with_names(source)
    except (RecursionError, TypeError, ValueError) as error:
        raise ReconstructionError(f"{label} is not an exact first-order formula") from error
    if names:
        raise ReconstructionError(f"{label} must not contain free variables")
    return formula


def _unsupported(
    name: str,
    statement: str,
    diagnostics: str,
    *,
    command: str = "",
    translated: int = 0,
) -> LeanProofReconstruction:
    return LeanProofReconstruction(
        name=name,
        lean_statement=statement,
        lean_body="",
        used_dependencies=(),
        used_axioms=(),
        translated_steps=translated,
        unsupported_steps=(command,) if command else (),
        status="fallback_required",
        diagnostics=(diagnostics,),
    )


def _goal_formula(formula: Formula, names: tuple[str, ...]) -> str:
    try:
        return _render_readable_formula(formula, names, 0)
    except (RecursionError, TypeError, ValueError):
        return _formula_to_lean(formula, names, 0)


def _goal_term(source: str, goal: Goal, *, application: bool = False) -> str:
    if source.strip() == "?":
        raise ReconstructionError("unresolved metavariable witnesses cannot become Lean terms")
    term = parse_term_in_context(source.strip(), list(goal.variables))
    return _term_to_lean(term, goal.variables, 4 if application else 0)


def _hypothesis(goal: Goal, name: str) -> Formula:
    return next(
        formula for candidate, formula in goal.context if candidate == name
    )


def _fresh_context_names(before: Goal, after: Goal) -> list[str]:
    previous = {name for name, _ in before.context}
    return [name for name, _ in after.context if name not in previous]


def _emit(lines: list[str], frame: _GoalFrame, commands: tuple[str, ...]) -> int:
    if not commands:
        raise ReconstructionError("a translated command cannot be empty")
    indent = frame.indent
    if frame.marker.startswith("|"):
        lines.append(" " * indent + frame.marker)
        indent += 2
        lines.extend(" " * indent + command for command in commands)
    elif frame.marker == "bullet":
        lines.append(" " * indent + "· " + commands[0])
        indent += 2
        lines.extend(" " * indent + command for command in commands[1:])
    else:
        lines.extend(" " * indent + command for command in commands)
    return indent


def _rewrite_command(
    args: str,
    before: Goal,
    after: Goal,
    axioms: Mapping[str, str],
    used_axioms: set[str],
) -> tuple[str, ...]:
    pieces = args.split()
    reverse = bool(pieces and pieces[0] in {"<-", "←"})
    if reverse:
        pieces = pieces[1:]
    if len(pieces) == 1:
        equation, target = pieces[0], None
    elif len(pieces) == 3 and pieces[1] == "at":
        equation, target = pieces[0], pieces[2]
    else:
        raise ReconstructionError("unsupported Peano rewrite argument structure")
    _safe_identifier(equation, "rewrite equation")
    reference = axioms.get(equation, equation)
    if equation in axioms:
        used_axioms.add(equation)
    direction = "← " if reverse else ""
    if target is not None:
        _safe_identifier(target, "rewritten hypothesis")
    suffix = "" if target is None else f" at {target}"
    if equation == "PA4":
        # Nat.add_succ is definitional in Lean. Its rewrite matcher can first
        # reduce nested additions, silently consuming several distinct Peano
        # occurrences and making the next authored rewrite impossible. `change`
        # asks Lean to kernel-check the *exact* independently computed successor
        # proof state instead, preserving every original occurrence transition.
        expected = after.target if target is None else _hypothesis(after, target)
        commands = (
            "change " + _formula_to_lean(expected, after.variables, 0) + suffix,
        )
    else:
        # Peano rewrites exactly one occurrence and deliberately leaves its
        # goal open. Lean `rw` rewrites every occurrence and then attempts
        # `rfl`; explicit first-occurrence `rewrite` preserves both contracts.
        command = f"rewrite (occs := .pos [1]) [{direction}{reference}]" + suffix
        if equation in axioms:
            commands = (command,)
        else:
            prior = before.target if target is None else _hypothesis(before, target)
            exact_prior = _formula_to_lean(prior, before.variables, 0)
            if _goal_formula(prior, before.variables) == exact_prior:
                commands = (command,)
            else:
                # A local conservative alias can compact several independently
                # authored occurrences into one Lean argument. Anchor both ends
                # to authenticated expanded states only when readable notation
                # actually differs; ordinary arithmetic stays concise.
                expected = after.target if target is None else _hypothesis(after, target)
                commands = (
                    "change " + exact_prior + suffix,
                    command,
                    "change " + _formula_to_lean(expected, after.variables, 0) + suffix,
                )
    if target is None:
        return commands
    fresh = _fresh_context_names(before, after)
    preserved = next((name for name in fresh if name.startswith(target + "_before")), None)
    if preserved is not None:
        _safe_identifier(preserved, "preserved hypothesis")
        return (f"have {preserved} := {target}", *commands)
    return commands


def _simp_command(
    args: str,
    axioms: Mapping[str, str],
    used_axioms: set[str],
) -> str:
    references = [axioms[name] for name in ("PA3", "PA4", "PA5", "PA6")]
    used_axioms.update(("PA3", "PA4", "PA5", "PA6"))
    text = args.strip()
    if text:
        if not text.startswith("[") or not text.endswith("]"):
            raise ReconstructionError("unsupported Peano simp argument structure")
        for item in text[1:-1].split(","):
            value = item.strip()
            if not value:
                continue
            reverse = value.startswith("<-") or value.startswith("←")
            if reverse:
                value = value[2:].strip() if value.startswith("<-") else value[1:].strip()
            name = _safe_identifier(value, "simp lemma")
            reference = axioms.get(name, name)
            if name in axioms:
                used_axioms.add(name)
            references.append(("← " if reverse else "") + reference)
    return "simp only [" + ", ".join(references) + "]"


def _norm_num_command(before: Goal, produced: int) -> str:
    if produced != 0 or type(before.target) is not Eq:
        raise ReconstructionError("open or residual norm_num goals require certificate fallback")
    def bounded_value(term: object, depth: int = 0) -> int | None:
        if depth > 128:
            return None
        if type(term) in (Zero, Succ, Mul):
            encoded = numeral_value(term)
            if encoded is not None:
                return encoded if encoded <= 100_000 else None
        if type(term) is Succ:
            child = bounded_value(term.term, depth + 1)
            return child + 1 if child is not None and child < 100_000 else None
        if type(term) in (Add, Mul):
            left = bounded_value(term.left, depth + 1)
            right = bounded_value(term.right, depth + 1)
            if left is None or right is None:
                return None
            value = left + right if type(term) is Add else left * right
            return value if value <= 100_000 else None
        return None

    left = bounded_value(before.target.left)
    right = bounded_value(before.target.right)
    if left is None or right is None or max(left, right) > 100_000:
        raise ReconstructionError("non-small numerical goals require certificate fallback")
    return "decide"


def _translate_command(
    tactic: str,
    args: str,
    before: Goal,
    after: ProofState,
    produced: int,
    frame: _GoalFrame,
    lines: list[str],
    axioms: Mapping[str, str],
    used_axioms: set[str],
) -> tuple[_GoalFrame, ...]:
    first_after = after.goals[0] if produced else None

    if tactic in {"intro", "exact", "apply"}:
        name = _safe_identifier(args.strip(), tactic + " argument")
        if tactic == "apply" and name == "DNE":
            raise ReconstructionError("classical DNE is unavailable in constructive Lean export")
        if tactic == "apply" and name in axioms:
            used_axioms.add(name)
            name = axioms[name]
        commands = (f"{tactic} {name}",)
    elif tactic in {"refl", "symm", "assumption", "exfalso", "left", "right"}:
        if args.strip():
            raise ReconstructionError(f"{tactic} does not accept arguments")
        commands = ("rfl" if tactic == "refl" else tactic,)
    elif tactic in {"specialize", "forall_elim"}:
        if first_after is None:
            raise ReconstructionError("specialization unexpectedly closed its goal")
        parts = args.split(maxsplit=1)
        if len(parts) != 2:
            raise ReconstructionError("specialization requires a hypothesis and exact term")
        hypothesis = _safe_identifier(parts[0], "specialized hypothesis")
        witness = _goal_term(parts[1], before, application=True)
        fresh = _fresh_context_names(before, first_after)
        previous = next(
            (name for name in fresh if name.startswith(hypothesis + "_before")),
            None,
        )
        commands = (
            (f"have {previous} := {hypothesis}", f"specialize {hypothesis} {witness}")
            if previous is not None
            else (f"specialize {hypothesis} {witness}",)
        )
    elif tactic == "exists":
        witness = _goal_term(args, before)
        commands = (f"refine ⟨{witness}, ?_⟩",)
    elif tactic == "trans":
        # `trans` is not a Lean-core tactic.  Applying its core equality
        # theorem preserves the exact two dependency-relative obligations.
        commands = (f"apply Eq.trans (b := {_goal_term(args, before)})",)
    elif tactic == "split":
        commands = ("constructor",)
    elif tactic == "congr":
        if type(before.target) is not Eq:
            raise ReconstructionError("congruence requires an exact equality goal")
        left, right = before.target.left, before.target.right
        if type(left) is Succ and type(right) is Succ:
            if produced != 1:
                raise ReconstructionError("successor congruence must preserve its exact obligation")
            commands = ("refine congrArg Nat.succ ?_",)
        elif type(left) is Add and type(right) is Add:
            if produced != 2:
                raise ReconstructionError("addition congruence must preserve both exact obligations")
            # `congrArg₂` is not in Lean core.  The primitive `congr` and
            # unary `congrArg` expose exactly the two authored subgoals.
            commands = ("refine congr (congrArg Nat.add ?_) ?_",)
        elif type(left) is Mul and type(right) is Mul:
            if produced != 2:
                raise ReconstructionError("multiplication congruence must preserve both exact obligations")
            commands = ("refine congr (congrArg Nat.mul ?_) ?_",)
        else:
            raise ReconstructionError("unsupported congruence constructor")
    elif tactic == "rewrite":
        if first_after is None:
            raise ReconstructionError("rewrite unexpectedly closed its goal")
        commands = _rewrite_command(args, before, first_after, axioms, used_axioms)
    elif tactic == "simp":
        commands = (_simp_command(args, axioms, used_axioms),)
    elif tactic == "norm_num":
        commands = (_norm_num_command(before, produced),)
    elif tactic == "cases":
        name = _safe_identifier(args.strip(), "case hypothesis")
        proposition = _hypothesis(before, name)
        if type(proposition) is And:
            if first_after is None or len(first_after.context) < 2:
                raise ReconstructionError("conjunction cases lost exact hypotheses")
            right_name = _safe_identifier(first_after.context[0][0], "right hypothesis")
            left_name = _safe_identifier(first_after.context[1][0], "left hypothesis")
            commands = (f"obtain ⟨{left_name}, {right_name}⟩ := {name}",)
        elif type(proposition) is Exists:
            if first_after is None or not first_after.variables or not first_after.context:
                raise ReconstructionError("existential cases lost their exact witness")
            witness = _safe_identifier(first_after.variables[0], "existential witness")
            evidence = _safe_identifier(first_after.context[0][0], "existential evidence")
            commands = (f"obtain ⟨{witness}, {evidence}⟩ := {name}",)
        elif type(proposition) is Or:
            if produced != 2 or len(after.goals) < 2:
                raise ReconstructionError("disjunction cases require exactly two branches")
            left_name = _safe_identifier(after.goals[0].context[0][0], "left hypothesis")
            right_name = _safe_identifier(after.goals[1].context[0][0], "right hypothesis")
            commands = (f"rcases {name} with {left_name} | {right_name}",)
        elif type(proposition) is Bot:
            commands = (f"exact False.elim {name}",)
        else:
            raise ReconstructionError("unsupported cases proposition")
    elif tactic in {"have", "suffices"}:
        if produced != 2 or first_after is None:
            raise ReconstructionError(f"{tactic} must produce its exact two obligations")
        name_source, separator, _formula = args.partition(":")
        if not separator:
            raise ReconstructionError(f"{tactic} requires an explicit local proposition")
        name = _safe_identifier(name_source.strip(), tactic + " hypothesis")
        proposition = (
            first_after.target
            if tactic == "have"
            else next(value for label, value in first_after.context if label == name)
        )
        rendered = _goal_formula(proposition, before.variables)
        suffix = ":= by" if tactic == "have" else "by"
        commands = (f"{tactic} {name} : {rendered} {suffix}",)
    elif tactic == "induction":
        if produced != 2 or len(after.goals) < 2:
            raise ReconstructionError("induction must produce exact base and successor goals")
        variable = _safe_identifier(args.strip(), "induction variable")
        step_goal = after.goals[1]
        if not step_goal.variables or not step_goal.context:
            raise ReconstructionError("induction lost its successor variable or hypothesis")
        step_name = _safe_identifier(step_goal.variables[0], "successor variable")
        ih_name = _safe_identifier(step_goal.context[0][0], "induction hypothesis")
        commands = (
            (f"intro {variable}", f"induction {variable} with")
            if type(before.target) is Forall and variable not in before.variables
            else (f"induction {variable} with",)
        )
        indent = _emit(lines, frame, commands)
        return (
            _GoalFrame(indent, "| zero =>"),
            _GoalFrame(indent, f"| succ {step_name} {ih_name} =>"),
        )
    else:
        raise ReconstructionError(f"unsupported Peano tactic {tactic!r}")

    indent = _emit(lines, frame, commands)
    if produced == 0:
        return ()
    if tactic in {"have", "suffices"}:
        return (_GoalFrame(indent + 2), _GoalFrame(indent))
    if produced == 1:
        return (_GoalFrame(indent),)
    return tuple(_GoalFrame(indent, "bullet") for _ in range(produced))


def reconstruct_theorem(
    spec: TheoremSpec,
    *,
    dependency_references: Mapping[str, str],
    dependency_formulas: Mapping[str, Formula] | None = None,
    statement: str | None = None,
    available_axioms: Mapping[str, str] | None = None,
    max_steps: int = MAX_RECONSTRUCTION_STEPS,
) -> LeanProofReconstruction:
    """Translate one local theorem body; unsupported commands fail transparently."""

    if type(spec) is not TheoremSpec:
        raise ReconstructionError("proof reconstruction needs an exact TheoremSpec")
    _validate_theorem_name(spec.name)
    _safe_identifier(spec.name, "theorem name")
    if type(max_steps) is not int or not 1 <= max_steps <= MAX_RECONSTRUCTION_STEPS:
        raise ReconstructionError("max_steps must be an exact bounded positive integer")
    if type(spec.dependencies) is not tuple or len(spec.dependencies) > max_steps:
        raise ReconstructionError("dependencies must be an exact bounded theorem tuple")
    if type(spec.script) is not tuple or len(spec.script) > min(max_steps, MAX_SCRIPT_LINES):
        raise ReconstructionError("script must be an exact bounded tactic tuple")
    if not all(type(line) is str and line.strip() for line in spec.script):
        raise ReconstructionError("script contains a blank or non-text command")
    if sum(len(line.encode("utf-8")) for line in spec.script) > MAX_SCRIPT_BYTES:
        raise ReconstructionError("script exceeds its bounded UTF-8 byte allowance")
    if not isinstance(dependency_references, Mapping):
        raise ReconstructionError("dependency_references must be an exact name mapping")
    if dependency_formulas is not None and not isinstance(dependency_formulas, Mapping):
        raise ReconstructionError("dependency_formulas must be an exact formula mapping")

    formula = _closed_formula(spec.statement, "theorem statement")
    readable = readable_formula(formula, source_statement=spec.statement)
    exact = formula_to_lean(formula)
    if statement is None:
        selected_statement = readable
    elif type(statement) is str and statement in {readable, exact}:
        selected_statement = statement
    else:
        raise ReconstructionError("the requested Lean statement differs from the exact theorem")

    dependencies = tuple(_safe_identifier(name, "dependency name") for name in spec.dependencies)
    if len(set(dependencies)) != len(dependencies):
        raise ReconstructionError("theorem dependencies must not contain duplicate names")
    unknown = set(dependency_references) - set(dependencies)
    if unknown:
        raise ReconstructionError("dependency reference contains undeclared theorem names")
    missing = tuple(name for name in dependencies if name not in dependency_references)
    if missing:
        return _unsupported(
            spec.name,
            selected_statement,
            "missing independently checked Lean dependency references: " + ", ".join(missing),
        )
    references = {
        name: _safe_reference(dependency_references[name], f"dependency {name!r}")
        for name in dependencies
    }

    if dependency_formulas is not None:
        unknown_formulas = set(dependency_formulas) - set(dependencies)
        if unknown_formulas:
            raise ReconstructionError("dependency formula contains undeclared theorem names")
    formulas: dict[str, Formula] = {}
    for name in dependencies:
        if dependency_formulas is not None and name in dependency_formulas:
            candidate = dependency_formulas[name]
            if not isinstance(candidate, Formula):
                raise ReconstructionError("dependency must carry an exact PA formula")
        else:
            dependency = get(name)
            if dependency is None:
                return _unsupported(
                    spec.name,
                    selected_statement,
                    f"no exact closed formula is available for dependency {name!r}",
                )
            candidate = _closed_formula(dependency.statement, f"dependency {name!r}")
        formulas[name] = candidate

    if available_axioms is not None and not isinstance(available_axioms, Mapping):
        raise ReconstructionError("available_axioms must be a mapping of actual PA names")
    axioms = dict(DEFAULT_AXIOM_REFERENCES)
    if available_axioms is not None:
        for name, reference in available_axioms.items():
            if name not in axioms:
                raise ReconstructionError("only actual arithmetic axioms PA1 through PA6 exist")
            axioms[name] = _safe_reference(reference, f"arithmetic lemma {name!r}")

    for command in spec.script:
        tactic = command.split(maxsplit=1)[0]
        if tactic not in SUPPORTED_TACTICS or (tactic == "apply" and command.strip() == "apply DNE"):
            return _unsupported(
                spec.name,
                selected_statement,
                f"the constructive Lean translator does not support {tactic!r}",
                command=command,
            )

    curried = formula
    for dependency in reversed(dependencies):
        curried = Imp(formulas[dependency], curried)
    try:
        state = start(curried)
        for dependency in dependencies:
            state = apply_tactic(state, "intro", dependency)
    except (TacticError, RecursionError, TypeError, ValueError) as error:
        return _unsupported(
            spec.name,
            selected_statement,
            "could not reconstruct the exact dependency-curried theorem body: " + str(error),
        )

    lines = ["by"]
    for dependency in dependencies:
        lines.append(f"  have {dependency} := {references[dependency]}")
    frames: deque[_GoalFrame] = deque((_GoalFrame(2),))
    used_axioms: set[str] = set()
    translated = 0

    for command in spec.script:
        if not frames or state.current() is None:
            return _unsupported(
                spec.name,
                selected_statement,
                "the authored script continues after its final goal",
                command=command,
                translated=translated,
            )
        parts = command.split(maxsplit=1)
        tactic, args = parts[0], parts[1] if len(parts) == 2 else ""
        before = state.current()
        assert before is not None
        try:
            next_state = apply_tactic(state, tactic, args)
            produced = len(next_state.goals) - len(state.goals) + 1
            if produced < 0 or len(next_state.goals) > MAX_RECONSTRUCTION_GOALS:
                raise ReconstructionError("local proof exceeds its safe open-goal boundary")
            frame = frames.popleft()
            children = _translate_command(
                tactic,
                args,
                before,
                next_state,
                produced,
                frame,
                lines,
                axioms,
                used_axioms,
            )
            if len(children) != produced:
                raise ReconstructionError("translated Lean branch count differs from Peano")
            frames.extendleft(reversed(children))
            if len(frames) != len(next_state.goals):
                raise ReconstructionError("translated Lean goal stack lost exact synchronization")
            state = next_state
            translated += 1
            if sum(len(line.encode("utf-8")) + 1 for line in lines) > MAX_RECONSTRUCTED_BYTES:
                raise ReconstructionError("readable Lean proof exceeds its safe source-byte boundary")
        except (
            ReconstructionError,
            TacticError,
            StopIteration,
            RecursionError,
            TypeError,
            ValueError,
        ) as error:
            return _unsupported(
                spec.name,
                selected_statement,
                f"cannot soundly reconstruct tactic {translated + 1}: {error}",
                command=command,
                translated=translated,
            )

    if frames or not state.is_done():
        return _unsupported(
            spec.name,
            selected_statement,
            "the authored script leaves unproved dependency-relative goals",
            translated=translated,
        )
    return LeanProofReconstruction(
        name=spec.name,
        lean_statement=selected_statement,
        lean_body="\n".join(lines),
        used_dependencies=dependencies,
        used_axioms=tuple(name for name in DEFAULT_AXIOM_REFERENCES if name in used_axioms),
        translated_steps=translated,
        unsupported_steps=(),
        status="translated",
        diagnostics=(),
    )


__all__ = [
    "DEFAULT_AXIOM_REFERENCES",
    "LeanProofReconstruction",
    "MAX_RECONSTRUCTION_GOALS",
    "MAX_RECONSTRUCTION_STEPS",
    "MAX_RECONSTRUCTED_BYTES",
    "ReconstructionError",
    "SUPPORTED_TACTICS",
    "reconstruct_theorem",
]
