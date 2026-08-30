"""Human-readable Lean facades backed by complete independently checked proofs.

The small presentation module is never proof authority.  Its theorem is
obtained from a separately imported, fully reconstructed certificate theorem,
using only definitional unfolding of conservative arithmetic predicates.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from hashlib import sha256
import re
from typing import Any

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
)
from .defined_syntax import DEFINITIONS_BY_NAME, parse_defined_formula
from .lean import (
    _formula_to_lean,
    _fresh_binder,
    _script_lines,
    _term_to_lean,
    _validate_theorem_name,
    formula_to_lean,
)
from .lean_certified import export_checked_bundle_theorem, export_checked_theorem
from .proof_bundle import ProofBundle


PRESENTATION_SCHEMA = "peano-lab-lean-presentation-v1"
MAX_PREVIEW_BYTES = 24_576
MAX_SUMMARY_BYTES = 4_096
MAX_SOURCE_BYTES = 1_048_576
MAX_SCRIPT_BYTES = 1_048_576
MAX_SCRIPT_LINES = 4_096
MAX_DEPENDENCIES = 4_096

SUPPORTED_ALIASES = (
    "Le",
    "Lt",
    "Dvd",
    "Prime",
    "Coprime",
    "ModEq",
    "QRes",
    "Odd",
    "Mod4One",
    "Mod4Three",
    "BetaAt",
    "Product",
    "AllPrime",
    "Sorted",
)
_ALIAS_NAMES = frozenset(SUPPORTED_ALIASES)
_EDITION_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,31}\Z")
_BINDER_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_']*\Z")
_LEAN_KEYWORDS = frozenset(
    {
        "abbrev", "axiom", "by", "class", "def", "do", "else", "end",
        "example", "export", "extends", "for", "fun", "if", "import",
        "in", "inductive", "instance", "let", "match", "mutual",
        "namespace", "opaque", "open", "partial", "private", "protected",
        "section", "set_option", "structure", "syntax", "theorem", "then",
        "variable", "where", "with",
    }
)


class LeanPresentationError(ValueError):
    """A proposed readable facade cannot preserve its exact checked target."""


@dataclass(frozen=True, slots=True)
class LeanPresentation:
    """A deterministic three-module package and its non-authoritative receipt."""

    name: str
    exact_statement: str
    readable_statement: str
    certificate_module: str
    certificate_relative_path: str
    certificate_code: str
    presentation_module: str
    presentation_relative_path: str
    presentation_code: str
    notation_module: str
    notation_relative_path: str
    notation_code: str
    manifest: dict[str, Any]
    preview: str

    def files(self) -> list[tuple[str, str]]:
        """Return LF-complete Lean sources in import-dependency order."""

        return [
            (self.notation_relative_path, self.notation_code),
            (self.certificate_relative_path, self.certificate_code),
            (self.presentation_relative_path, self.presentation_code),
        ]


def _registry_notation_lines() -> tuple[str, ...]:
    """Render reviewed finite-coding templates without adding any primitive."""

    lines: list[str] = []
    for name in ("BetaAt", "Product", "AllPrime", "Sorted"):
        definition = DEFINITIONS_BY_NAME[name]
        if parse_formula_in_context(
            definition.template_source,
            list(definition.parameters),
        ) != definition.template_formula:
            raise LeanPresentationError("reviewed presentation definition changed its AST")
        parameters = " ".join(definition.parameters)
        body = _formula_to_lean(
            definition.template_formula,
            tuple(definition.parameters),
            0,
        )
        lines.extend((f"def {name} ({parameters} : Nat) : Prop :=", f"  {body}", ""))
    return tuple(lines)


_NOTATION_CODE = "\n".join(
    (
        "-- Conservative Peano presentation notation; no arithmetic axiom is added.",
        "import PeanoLab.Codec",
        "",
        "namespace PeanoLab.Presentation",
        "",
        "def Le (a b : Nat) : Prop :=",
        "  ∃ h : Nat, h + a = b",
        "",
        "def Lt (a b : Nat) : Prop :=",
        "  ∃ h : Nat, h + Nat.succ a = b",
        "",
        "def Dvd (d n : Nat) : Prop :=",
        "  ∃ k : Nat, n = d * k",
        "",
        "def Prime (p : Nat) : Prop :=",
        "  (p = 1 → False) ∧ ∀ a : Nat, ∀ b : Nat,",
        "    p = a * b → a = 1 ∨ b = 1",
        "",
        "def Coprime (a b : Nat) : Prop :=",
        "  ∀ d : Nat, (∃ x : Nat, a = d * x) →",
        "    (∃ y : Nat, b = d * y) → d = 1",
        "",
        "def ModEq (m a b : Nat) : Prop :=",
        "  ∃ u : Nat, ∃ v : Nat, a + m * u = b + m * v",
        "",
        "def QRes (m a : Nat) : Prop :=",
        "  ∃ x : Nat, ∃ u : Nat, ∃ v : Nat,",
        "    x * x + m * u = a + m * v",
        "",
        "def Odd (n : Nat) : Prop :=",
        "  ∃ h : Nat, n = 2 * h + 1",
        "",
        "def Mod4One (n : Nat) : Prop :=",
        "  ∃ h : Nat, n = 4 * h + 1",
        "",
        "def Mod4Three (n : Nat) : Prop :=",
        "  ∃ h : Nat, n = 4 * h + 3",
        "",
        "theorem lt_iff (n p : Nat) : Lt n p ↔ n < p := by",
        "  constructor",
        "  · rintro ⟨k, hk⟩",
        "    apply Nat.lt_iff_add_one_le.mpr",
        "    apply Nat.le.intro (k := k)",
        "    simpa [Nat.add_comm] using hk",
        "  · intro h",
        "    obtain ⟨k, hk⟩ := Nat.le.dest (Nat.lt_iff_add_one_le.mp h)",
        "    exact ⟨k, by simpa [Nat.add_comm] using hk⟩",
        "",
        "theorem dvd_iff (d n : Nat) : Dvd d n ↔ d ∣ n := by",
        "  constructor",
        "  · rintro ⟨k, hk⟩",
        "    exact ⟨k, hk⟩",
        "  · rintro ⟨k, hk⟩",
        "    exact ⟨k, hk⟩",
        "",
        *_registry_notation_lines(),
        "end PeanoLab.Presentation",
        "",
    )
)


def _utf8_size(value: str) -> int:
    return len(value.encode("utf-8"))


def _bounded_utf8(value: str, maximum: int) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= maximum:
        return value
    suffix = "\n-- [preview truncated; export the complete certified package]"
    available = maximum - _utf8_size(suffix)
    return encoded[:available].decode("utf-8", errors="ignore") + suffix


def _validated_metadata(
    name: str,
    *,
    script: Sequence[str] | str,
    dependencies: Sequence[str],
    summary: str,
    edition: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    _validate_theorem_name(name)
    if len(name) > 128:
        raise LeanPresentationError("theorem name exceeds its presentation limit")
    if type(edition) is not str or _EDITION_PATTERN.fullmatch(edition) is None:
        raise LeanPresentationError("edition must be a bounded safe ASCII identifier")
    if type(summary) is not str or _utf8_size(summary) > MAX_SUMMARY_BYTES:
        raise LeanPresentationError("summary must be bounded UTF-8 text")
    if (
        not isinstance(dependencies, Sequence)
        or isinstance(dependencies, (str, bytes, bytearray))
        or len(dependencies) > MAX_DEPENDENCIES
    ):
        raise TypeError("dependencies must be a bounded sequence of theorem names")
    checked_dependencies = tuple(dependencies)
    for dependency in checked_dependencies:
        _validate_theorem_name(dependency)
    if len(set(checked_dependencies)) != len(checked_dependencies):
        raise LeanPresentationError("dependencies must not contain duplicate names")
    if isinstance(script, str):
        if _utf8_size(script) > MAX_SCRIPT_BYTES:
            raise LeanPresentationError("tactic script exceeds its presentation byte limit")
    elif isinstance(script, Sequence):
        if len(script) > MAX_SCRIPT_LINES:
            raise LeanPresentationError("tactic script exceeds its presentation line limit")
        script_bytes = 0
        for entry in script:
            if not isinstance(entry, str):
                raise TypeError("script must be text or a sequence of text lines")
            script_bytes += _utf8_size(entry)
            if script_bytes > MAX_SCRIPT_BYTES:
                raise LeanPresentationError(
                    "tactic script exceeds its presentation byte limit"
                )
    lines = _script_lines(script)
    if len(lines) > MAX_SCRIPT_LINES:
        raise LeanPresentationError("tactic script exceeds its presentation line limit")
    return lines, checked_dependencies


def _render_readable_formula(
    formula: Formula,
    names: tuple[str, ...],
    parent_precedence: int,
    leading: list[tuple[type[Formula], str]] | None = None,
) -> str:
    matched = _definition_match(formula)
    if matched is not None:
        definition, arguments = matched
        if definition.name not in _ALIAS_NAMES:
            raise LeanPresentationError("a definition has no exact Lean presentation")
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
        text = "¬" + _render_readable_formula(formula.left, names, 4)
        precedence = 4
    elif type(formula) in (And, Or, Imp):
        if type(formula) is And:
            precedence, symbol = 3, "∧"
        elif type(formula) is Or:
            precedence, symbol = 2, "∨"
        else:
            precedence, symbol = 1, "→"
        left = _render_readable_formula(formula.left, names, precedence + 1)
        right = _render_readable_formula(formula.right, names, precedence)
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
        body = _render_readable_formula(
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


def _readable_details(
    formula: Formula,
    source_statement: str | None,
) -> tuple[str, tuple[str, ...], bool]:
    exact = formula_to_lean(formula)
    if source_statement is None:
        source = pretty_formula(formula, [])
    elif type(source_statement) is str:
        source = source_statement
    else:
        raise TypeError("source_statement must be text or None")
    if _utf8_size(source) > MAX_SOURCE_BYTES:
        raise LeanPresentationError("source statement exceeds its presentation limit")

    try:
        parsed, free_names = parse_formula_with_names(source)
    except (RecursionError, TypeError, ValueError) as error:
        raise LeanPresentationError("source statement is not an exact PA formula") from error
    if free_names or parsed != formula:
        raise LeanPresentationError("source statement differs from the checked formula")

    try:
        compacted = compact_formula_source(source)
        if not compacted.receipt.exact_ast_equivalence:
            raise LeanPresentationError("defined compaction lacks exact AST equivalence")
        expanded = parse_defined_formula(
            compacted.defined_source,
            expansion_budget=DEFINED_EDITION_EXPANSION_BUDGET,
        )
        if expanded != formula:
            raise LeanPresentationError("readable notation changes the checked formula")
        aliases = tuple(
            item.name for item in compacted.receipt.definition_uses
        )
        if any(alias not in _ALIAS_NAMES for alias in aliases):
            return exact, (), False
        readable = _render_readable_formula(
            formula,
            (),
            0,
            _leading_source_binders(source),
        )
        return readable, aliases, True
    except (DefinedEditionError, RecursionError, TypeError, ValueError):
        return exact, (), False


def readable_formula(
    formula: Formula,
    *,
    source_statement: str | None = None,
) -> str:
    """Render exact conservative Lean notation without building a certificate."""

    return _readable_details(formula, source_statement)[0]


def preview_checked_presentation(
    name: str,
    formula: Formula,
    *,
    source_statement: str | None = None,
    script: Sequence[str] | str = (),
    dependencies: Sequence[str] = (),
    summary: str = "",
    edition: str = "stable",
) -> str:
    """Return a bounded theorem-first view without replay or certificate emission."""

    authored, checked_dependencies = _validated_metadata(
        name,
        script=script,
        dependencies=dependencies,
        summary=summary,
        edition=edition,
    )
    readable, aliases, _ = _readable_details(formula, source_statement)
    lines = [
        f"theorem «{name}» : {readable}",
    ]
    if summary:
        lines.extend("-- " + line for line in summary.splitlines())
    if aliases:
        lines.append("-- Exact constructive notation: " + ", ".join(aliases))
    lines.extend(
        (
            "-- Certificate companion: import PeanoLab.Codec",
            "-- Independent soundness: PeanoLab.Artifact.check_sound",
            "-- Lean verification: NOT RUN; compile the complete certified package.",
            f"-- Edition: {edition}",
        )
    )
    if checked_dependencies:
        shown = checked_dependencies[:12]
        tail = (
            f" (+{len(checked_dependencies) - len(shown)} more)"
            if len(shown) != len(checked_dependencies)
            else ""
        )
        lines.append("-- Peano dependencies: " + ", ".join(shown) + tail)
    if authored:
        lines.append("-- Original Peano tactics (not executable Lean tactics):")
        lines.extend("--   " + line for line in authored[:12])
        if len(authored) > 12:
            lines.append(f"--   ... {len(authored) - 12} additional tactic lines")
    return _bounded_utf8("\n".join(lines), MAX_PREVIEW_BYTES)


def _family_name(name: str) -> str:
    family = "".join(
        fragment[0].upper() + fragment[1:]
        for fragment in name.split("_")
        if fragment
    )
    family = family.replace("'", "Prime")
    if not family or not family[0].isalpha():
        family = "Theorem" + family
    return family


def _certificate_namespace(source: str, namespace: str) -> str:
    lines = source.splitlines()
    try:
        beginning = lines.index("namespace PeanoLab")
    except ValueError as error:
        raise LeanPresentationError("certificate lacks its exact Peano namespace") from error
    if not lines or lines[-1] != "end PeanoLab":
        raise LeanPresentationError("certificate lacks its exact closing namespace")
    lines[beginning] = f"namespace {namespace}"
    lines[-1] = f"end {namespace}"
    return "\n".join(lines) + "\n"


def _file_record(module: str, path: str, source: str) -> dict[str, Any]:
    payload = source.encode("utf-8")
    return {
        "module": module,
        "relative_path": path,
        "sha256": sha256(payload).hexdigest(),
        "bytes": len(payload),
    }


def _structural_stats(certificate: str) -> dict[str, int]:
    result = {
        "term_nodes": 0,
        "formula_nodes": 0,
        "proof_nodes": 0,
        "bundle_nodes": 0,
        "private_declarations": 0,
    }
    for line in certificate.splitlines():
        if not line.startswith("private def "):
            continue
        result["private_declarations"] += 1
        for marker, key in (
            (" : PeanoLab.Term :=", "term_nodes"),
            (" : PeanoLab.Formula :=", "formula_nodes"),
            (" : PeanoLab.Proof :=", "proof_nodes"),
            (" : PeanoLab.BundleNode :=", "bundle_nodes"),
        ):
            if marker in line:
                result[key] += 1
                break
    return result


def build_checked_presentation(
    name: str,
    formula: Formula,
    proof: Proof | None,
    *,
    source_statement: str | None = None,
    script: Sequence[str] | str = (),
    dependencies: Sequence[str] = (),
    summary: str = "",
    bundle: ProofBundle | None = None,
    include_axiom_audit: bool = True,
    edition: str = "stable",
) -> LeanPresentation:
    """Build a compact exact theorem and its independently checkable companion."""

    authored, checked_dependencies = _validated_metadata(
        name,
        script=script,
        dependencies=dependencies,
        summary=summary,
        edition=edition,
    )
    if type(include_axiom_audit) is not bool:
        raise TypeError("include_axiom_audit must be a boolean")
    if bundle is None and not isinstance(proof, Proof):
        raise TypeError("an ordinary presentation requires an exact proof certificate")
    if bundle is not None and type(bundle) is not ProofBundle:
        raise TypeError("bundle must be an exact ProofBundle or None")

    exact_statement = formula_to_lean(formula)
    readable_statement, aliases, exact_aliases = _readable_details(
        formula,
        source_statement,
    )
    if bundle is None:
        assert isinstance(proof, Proof)
        exported = export_checked_theorem(
            name,
            formula,
            proof,
            authored,
            dependencies=checked_dependencies,
            include_axiom_audit=include_axiom_audit,
        )
    else:
        exported = export_checked_bundle_theorem(
            name,
            bundle,
            formula,
            authored,
            dependencies=checked_dependencies,
            include_axiom_audit=include_axiom_audit,
        )
    if exported.statement != exact_statement:
        raise LeanPresentationError("certificate statement differs from the checked target")

    identity = sha256()
    for part in (name, edition, exact_statement, exported.code):
        encoded = part.encode("utf-8")
        identity.update(len(encoded).to_bytes(8, "big"))
        identity.update(encoded)
    digest = identity.hexdigest()
    family = f"{_family_name(name)}_{digest[:16]}"
    package = f"PeanoLab.Generated.{family}"
    package_path = "PeanoLab/Generated/" + family
    notation_module = "PeanoLab.Presentation"
    notation_path = "PeanoLab/Presentation.lean"
    certificate_module = package + ".Certificate"
    certificate_path = package_path + "/Certificate.lean"
    presentation_module = package + ".Theorem"
    presentation_path = package_path + "/Theorem.lean"
    certificate_code = _certificate_namespace(exported.code, certificate_module)

    facade = [
        "-- Human-readable theorem; its proof is the imported checked certificate.",
        f"import {notation_module}",
        f"import {certificate_module}",
        "",
        f"namespace {presentation_module}",
        "",
        "open PeanoLab.Presentation",
        "",
    ]
    if summary:
        facade.extend("-- " + line for line in summary.splitlines())
    facade.append(f"theorem «{name}» : {readable_statement} := by")
    target = f"{certificate_module}.«{name}»"
    if aliases:
        facade.append(f"  simpa [{', '.join(aliases)}] using {target}")
    else:
        facade.append(f"  exact {target}")
    if include_axiom_audit:
        facade.extend(("", f"#print axioms «{name}»"))
    facade.extend(("", f"end {presentation_module}", ""))
    presentation_code = "\n".join(facade)

    records = (
        _file_record(notation_module, notation_path, _NOTATION_CODE),
        _file_record(certificate_module, certificate_path, certificate_code),
        _file_record(presentation_module, presentation_path, presentation_code),
    )
    manifest: dict[str, Any] = {
        "schema": PRESENTATION_SCHEMA,
        "name": name,
        "edition": edition,
        "identity_sha256": digest,
        "exact_statement_sha256": sha256(
            exact_statement.encode("utf-8")
        ).hexdigest(),
        "readable_statement_sha256": sha256(
            readable_statement.encode("utf-8")
        ).hexdigest(),
        "exact_ast_equivalence": True,
        "conservative_alias_compaction": exact_aliases,
        "aliases": list(aliases),
        "proof_mode": "bundle" if bundle is not None else "certificate",
        "structure": _structural_stats(certificate_code),
        "files": list(records),
        "authority": {
            "lean_compiler_verified": False,
            "public_admission": False,
            "publication": False,
            "training": False,
            "final_evaluation": False,
        },
    }
    preview = preview_checked_presentation(
        name,
        formula,
        source_statement=source_statement,
        script=authored,
        dependencies=checked_dependencies,
        summary=summary,
        edition=edition,
    )
    return LeanPresentation(
        name=name,
        exact_statement=exact_statement,
        readable_statement=readable_statement,
        certificate_module=certificate_module,
        certificate_relative_path=certificate_path,
        certificate_code=certificate_code,
        presentation_module=presentation_module,
        presentation_relative_path=presentation_path,
        presentation_code=presentation_code,
        notation_module=notation_module,
        notation_relative_path=notation_path,
        notation_code=_NOTATION_CODE,
        manifest=manifest,
        preview=preview,
    )


__all__ = [
    "LeanPresentation",
    "LeanPresentationError",
    "MAX_PREVIEW_BYTES",
    "PRESENTATION_SCHEMA",
    "SUPPORTED_ALIASES",
    "build_checked_presentation",
    "preview_checked_presentation",
    "readable_formula",
]
