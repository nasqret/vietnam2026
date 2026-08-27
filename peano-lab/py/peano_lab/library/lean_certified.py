"""Translate checked first-order Peano certificates into completed Lean theorems.

The generated module imports the independently verified, Mathlib-free
PeanoLab.Codec companion. It reconstructs the exact target and certificate
as Lean syntax, checks the certificate again inside Lean, and applies the
companion's proved semantic soundness theorem. Neither Python's certificate
acceptance nor a tactic script is treated as an axiom.

The self-contained certificate format remains available for complete audits;
human-facing presentation and reusable checked modules are layered separately.
"""

from __future__ import annotations

from collections.abc import Sequence
from hashlib import sha256

from ..kernel.checker import check
from ..kernel.formulas import And, Bot, Eq, Exists, Forall, Formula, Imp, Or
from ..kernel.proofs import (
    AndElimL,
    AndElimR,
    AndIntro,
    Axiom,
    BotElim,
    CongAdd,
    CongMul,
    CongS,
    Cut,
    DNE,
    EqRefl,
    EqSubst,
    EqSym,
    EqTrans,
    ExistsElim,
    ExistsIntro,
    ForallElim,
    ForallIntro,
    Hyp,
    ImpElim,
    ImpIntro,
    Ind,
    OrElim,
    OrIntroL,
    OrIntroR,
    Proof,
)
from ..kernel.terms import Add, Mul, Succ, Term, Var, Zero
from .lean import (
    LeanExport,
    _script_lines,
    _validate_theorem_name,
    formula_to_lean,
)
from .proof_bundle import (
    ProofBundle,
    ProofBundleError,
    check_proof_bundle,
    decode_proof_bundle,
    encode_proof_bundle,
)


class LeanCertificateError(ValueError):
    """A certificate cannot safely become a closed intuitionistic Lean theorem."""


class _CertificateEmitter:
    """Build deterministic, structurally shared topological Lean AST bindings."""

    def __init__(self, name: str) -> None:
        self.prefix = "_pl_" + sha256(name.encode("utf-8")).hexdigest()[:12]
        self.declarations: list[str] = []
        self.term_keys: dict[tuple[object, ...], str] = {}
        self.formula_keys: dict[tuple[object, ...], str] = {}
        self.proof_keys: dict[tuple[object, ...], str] = {}
        self.term_objects: dict[int, str] = {}
        self.formula_objects: dict[int, str] = {}
        self.proof_objects: dict[int, str] = {}
        self.retained_objects: list[object] = []

    def _bind(
        self,
        kind: str,
        key: tuple[object, ...],
        expression: str,
        keys: dict[tuple[object, ...], str],
    ) -> str:
        existing = keys.get(key)
        if existing is not None:
            return existing
        identifier = f"{self.prefix}_{kind}{len(keys)}"
        lean_type = {"t": "Term", "f": "Formula", "p": "Proof"}[kind]
        self.declarations.append(
            f"private def {identifier} : PeanoLab.{lean_type} := {expression}"
        )
        keys[key] = identifier
        return identifier

    @staticmethod
    def _exact_nat(value: object, label: str) -> int:
        if type(value) is not int or value < 0:
            raise LeanCertificateError(f"{label} must be a non-negative integer")
        return value

    def term(self, term: Term) -> str:
        cached = self.term_objects.get(id(term))
        if cached is not None:
            return cached
        self.retained_objects.append(term)
        if type(term) is Var:
            index = self._exact_nat(term.index, "de Bruijn variable")
            key, expression = ("var", index), f".var {index}"
        elif type(term) is Zero:
            key, expression = ("zero",), ".zero"
        elif type(term) is Succ:
            child = self.term(term.term)
            key, expression = ("succ", child), f".succ {child}"
        elif type(term) in {Add, Mul}:
            left, right = self.term(term.left), self.term(term.right)
            tag = "add" if type(term) is Add else "mul"
            key, expression = (tag, left, right), f".{tag} {left} {right}"
        else:
            raise LeanCertificateError("expected an exact Peano term constructor")
        identifier = self._bind("t", key, expression, self.term_keys)
        self.term_objects[id(term)] = identifier
        return identifier

    def formula(self, formula: Formula) -> str:
        cached = self.formula_objects.get(id(formula))
        if cached is not None:
            return cached
        self.retained_objects.append(formula)
        if type(formula) is Eq:
            left, right = self.term(formula.left), self.term(formula.right)
            key, expression = ("eq", left, right), f".eq {left} {right}"
        elif type(formula) is Bot:
            key, expression = ("bot",), ".bot"
        elif type(formula) in {Imp, And, Or}:
            left, right = self.formula(formula.left), self.formula(formula.right)
            tag = {Imp: "imp", And: "conj", Or: "disj"}[type(formula)]
            key, expression = (tag, left, right), f".{tag} {left} {right}"
        elif type(formula) in {Forall, Exists}:
            body = self.formula(formula.body)
            tag = "forallE" if type(formula) is Forall else "existsE"
            key, expression = (tag, body), f".{tag} {body}"
        else:
            raise LeanCertificateError("expected an exact Peano formula constructor")
        identifier = self._bind("f", key, expression, self.formula_keys)
        self.formula_objects[id(formula)] = identifier
        return identifier

    def proof(self, proof: Proof) -> str:
        cached = self.proof_objects.get(id(proof))
        if cached is not None:
            return cached
        self.retained_objects.append(proof)

        unary = {
            ImpIntro: ("impIntro", "body"),
            AndElimL: ("andElimL", "pair"),
            AndElimR: ("andElimR", "pair"),
            OrIntroL: ("orIntroL", "proof"),
            OrIntroR: ("orIntroR", "proof"),
            BotElim: ("botElim", "absurdity"),
            ForallIntro: ("forallIntro", "body"),
            EqSym: ("eqSym", "proof"),
            CongS: ("congS", "proof"),
        }
        binary = {
            ImpElim: ("impElim", "function", "argument"),
            AndIntro: ("andIntro", "left", "right"),
            ExistsElim: ("existsElim", "existential", "body"),
            EqTrans: ("eqTrans", "first", "second"),
            CongAdd: ("congAdd", "left", "right"),
            CongMul: ("congMul", "left", "right"),
        }

        constructor = type(proof)
        if constructor is Hyp:
            index = self._exact_nat(proof.index, "hypothesis index")
            key, expression = ("hyp", index), f".hyp {index}"
        elif constructor in unary:
            tag, attribute = unary[constructor]
            child = self.proof(getattr(proof, attribute))
            key, expression = (tag, child), f".{tag} {child}"
        elif constructor in binary:
            tag, first_name, second_name = binary[constructor]
            first = self.proof(getattr(proof, first_name))
            second = self.proof(getattr(proof, second_name))
            key, expression = (tag, first, second), f".{tag} {first} {second}"
        elif constructor is Cut:
            proposition = self.formula(proof.proposition)
            conclusion = self.formula(proof.conclusion)
            lemma, body = self.proof(proof.lemma), self.proof(proof.body)
            key = ("cut", proposition, conclusion, lemma, body)
            expression = f".cut {proposition} {conclusion} {lemma} {body}"
        elif constructor is OrElim:
            source = self.proof(proof.disjunction)
            left, right = self.proof(proof.left_case), self.proof(proof.right_case)
            key, expression = ("orElim", source, left, right), (
                f".orElim {source} {left} {right}"
            )
        elif constructor is ForallElim:
            source, term = self.proof(proof.universal), self.term(proof.term)
            key, expression = ("forallElim", source, term), (
                f".forallElim {source} {term}"
            )
        elif constructor is ExistsIntro:
            term, source = self.term(proof.term), self.proof(proof.proof)
            key, expression = ("existsIntro", term, source), (
                f".existsIntro {term} {source}"
            )
        elif constructor is EqRefl:
            term = self.term(proof.term)
            key, expression = ("eqRefl", term), f".eqRefl {term}"
        elif constructor is EqSubst:
            motive = self.formula(proof.motive)
            equation, body = self.proof(proof.equation), self.proof(proof.body)
            key, expression = ("eqSubst", motive, equation, body), (
                f".eqSubst {motive} {equation} {body}"
            )
        elif constructor is Axiom:
            names = {
                "PA1": "pa1",
                "PA2": "pa2",
                "PA3": "pa3",
                "PA4": "pa4",
                "PA5": "pa5",
                "PA6": "pa6",
            }
            tag = names.get(proof.name)
            if tag is None:
                raise LeanCertificateError(
                    "the only allowed arithmetic axioms are PA1 through PA6"
                )
            key, expression = ("axiom", tag), f".axiom .{tag}"
        elif constructor is Ind:
            motive = self.formula(proof.motive)
            base, step = self.proof(proof.base), self.proof(proof.step)
            key, expression = ("ind", motive, base, step), (
                f".ind {motive} {base} {step}"
            )
        elif constructor is DNE:
            raise LeanCertificateError(
                "classical double-negation elimination is not an intuitionistic certificate"
            )
        else:
            raise LeanCertificateError("expected an exact Peano proof constructor")

        identifier = self._bind("p", key, expression, self.proof_keys)
        self.proof_objects[id(proof)] = identifier
        return identifier


def export_checked_theorem(
    name: str,
    formula: Formula,
    proof: Proof,
    script: Sequence[str] | str = (),
    *,
    dependencies: Sequence[str] = (),
    include_axiom_audit: bool = True,
) -> LeanExport:
    """Return a completed Lean theorem reconstructed from a checked PA proof.

    The result contains no placeholders, custom axioms, trusted Python status,
    compiler-reflection shortcuts, or unchecked imported theorem claims.
    The generated axiom audit exposes the companion soundness assumptions.
    """

    _validate_theorem_name(name)
    if (
        not isinstance(dependencies, Sequence)
        or isinstance(dependencies, (str, bytes, bytearray))
        or not all(isinstance(item, str) for item in dependencies)
    ):
        raise TypeError("dependencies must be a sequence of theorem names")
    for dependency in dependencies:
        _validate_theorem_name(dependency)
    if type(include_axiom_audit) is not bool:
        raise TypeError("include_axiom_audit must be a boolean")
    if not check((), proof, formula):
        raise LeanCertificateError(
            "the independent Peano kernel rejected the original closed theorem"
        )

    statement = formula_to_lean(formula)
    authored = _script_lines(script)
    emitter = _CertificateEmitter(name)
    target_identifier = emitter.formula(formula)
    proof_identifier = emitter.proof(proof)
    artifact_identifier = f"{emitter.prefix}_artifact"
    fuel = max(64, 8 * len(emitter.proof_keys) + 16)

    lines = [
        "-- Automatically translated from a checked constructive Peano certificate.",
        "-- Build inside the Mathlib-free sibling peano-lab-lean project.",
        "import PeanoLab.Codec",
        "",
        "set_option maxRecDepth 4096",
        "set_option maxHeartbeats 800000",
        "",
        "namespace PeanoLab",
        "",
        *emitter.declarations,
        "",
        f"private def {artifact_identifier} : PeanoLab.Artifact :=",
        f"  {{ fuel := {fuel}, target := {target_identifier}, proof := {proof_identifier} }}",
        "",
    ]
    if dependencies:
        lines.append(
            "-- Independently replayed Peano dependencies: " + ", ".join(dependencies)
        )
    if authored:
        lines.append("-- Original Peano tactic script:")
        lines.extend(f"--   {line}" for line in authored)
    lines.extend(
        (
            f"theorem «{name}» : {statement} := by",
            f"  have accepted : {artifact_identifier}.check = true := by",
            "    decide",
            "  have sound := PeanoLab.Artifact.check_sound accepted",
            # The rendered proposition is definitionally the interpretation
            # of the closed target. Conversion unfolds every shared private
            # AST binding, including children below quantifiers; a root-only
            # simplifier list does not explicitly unfold those children.
            "  exact sound (fun _ => 0)",
            "",
        )
    )
    if include_axiom_audit:
        lines.extend((f"#print axioms «{name}»", ""))
    lines.append("end PeanoLab")
    code = "\n".join(lines)
    # Certified modules import the local, independently verified companion.
    # Live Lean cannot resolve that import, and percent-encoding a complete
    # certificate can allocate multiple additional megabytes for no usable
    # result. Statement-only exports retain their separate Live Lean link.
    return LeanExport(name, statement, code, "")


def export_checked_bundle_theorem(
    name: str,
    bundle: ProofBundle,
    formula: Formula,
    script: Sequence[str] | str = (),
    *,
    dependencies: Sequence[str] = (),
    include_axiom_audit: bool = True,
) -> LeanExport:
    """Translate an independently checked shared proof DAG into a Lean theorem.

    The resulting ordinary proposition uses the sibling Lean proof-bundle
    soundness theorem. Dense local indices and every dependency-curried proof
    body are reconstructed explicitly; theorem names, Python status, and
    artifact hashes carry no proof authority.
    """

    _validate_theorem_name(name)
    if (
        not isinstance(dependencies, Sequence)
        or isinstance(dependencies, (str, bytes, bytearray))
        or not all(isinstance(item, str) for item in dependencies)
    ):
        raise TypeError("dependencies must be a sequence of theorem names")
    for dependency in dependencies:
        _validate_theorem_name(dependency)
    if type(include_axiom_audit) is not bool:
        raise TypeError("include_axiom_audit must be a boolean")

    try:
        check_proof_bundle(bundle, formula)
        canonical_bundle, canonical_formula = decode_proof_bundle(
            encode_proof_bundle(bundle, formula)
        )
    except (ProofBundleError, RecursionError, TypeError, ValueError) as error:
        raise LeanCertificateError(
            "the independent Peano kernel rejected the complete proof bundle"
        ) from error

    statement = formula_to_lean(canonical_formula)
    authored = _script_lines(script)
    emitter = _CertificateEmitter(name)
    target_identifier = emitter.formula(canonical_formula)
    rows: list[tuple[str, str, str, tuple[int, ...], int]] = []
    for node in canonical_bundle.nodes:
        if node.fuel is None:
            raise LeanCertificateError("canonical proof bundle requires explicit fuel")
        node_identifier = f"{emitter.prefix}_n{node.node_id}"
        row_target = emitter.formula(node.target)
        row_body = emitter.proof(node.body)
        rows.append((node_identifier, row_target, row_body, node.dependencies, node.fuel))

    node_declarations: list[str] = []
    for identifier, target, body, row_dependencies, fuel in rows:
        encoded_dependencies = ", ".join(map(str, row_dependencies))
        node_declarations.extend(
            (
                f"private def {identifier} : PeanoLab.BundleNode :=",
                f"  {{ fuel := {fuel}, target := {target},",
                f"    dependencies := [{encoded_dependencies}], body := {body} }}",
            )
        )
    bundle_identifier = f"{emitter.prefix}_bundle"
    encoded_nodes = ", ".join(identifier for identifier, *_ in rows)

    lines = [
        "-- Automatically translated from a complete checked Peano proof DAG.",
        "-- Every local proof and dependency is independently rechecked in Lean.",
        "import PeanoLab.ProofBundle",
        "",
        "set_option maxRecDepth 4096",
        "set_option maxHeartbeats 800000",
        "",
        "namespace PeanoLab",
        "",
        *emitter.declarations,
        "",
        *node_declarations,
        "",
        f"private def {bundle_identifier} : PeanoLab.ProofBundle :=",
        f"  {{ nodes := [{encoded_nodes}], root := {canonical_bundle.root} }}",
        "",
    ]
    if dependencies:
        lines.append(
            "-- Independently replayed Peano dependencies: " + ", ".join(dependencies)
        )
    if authored:
        lines.append("-- Original Peano tactic script:")
        lines.extend(f"--   {line}" for line in authored)
    lines.extend(
        (
            f"theorem «{name}» : {statement} := by",
            f"  have accepted : PeanoLab.checkBundle {bundle_identifier} "
            f"{target_identifier} = true := by",
            "    decide",
            "  have sound := PeanoLab.checkBundle_sound accepted",
            # As above, use kernel conversion through the whole shared
            # target DAG, not a tactic-dependent partial unfolding.
            "  exact sound (fun _ => 0)",
            "",
        )
    )
    if include_axiom_audit:
        lines.extend((f"#print axioms «{name}»", ""))
    lines.append("end PeanoLab")
    code = "\n".join(lines)
    # Bundle proofs are local-only for the same reason as single certificates.
    return LeanExport(name, statement, code, "")


__all__ = [
    "LeanCertificateError",
    "export_checked_bundle_theorem",
    "export_checked_theorem",
]
