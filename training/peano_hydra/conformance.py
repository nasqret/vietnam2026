"""Deterministic semantic-conformance material for Peano Hydra H0.2.

The objects constructed here are inert inputs to checkers.  This module is
not a proof authority: every positive is checked again by the authoritative
Python kernel against its retained original target, and the campaign driver
also sends the same canonical artifact to independently built checkers.

The active profile has no decision claim.  Accordingly, a certificate checked
against an intentionally different target is called ``certificate_rejected``.
It is never evidence that the different target is not a theorem.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, fields
from hashlib import sha256
import json
from typing import Callable, Iterable, Iterator, Literal, Mapping

from peano_lab.engine.state import proof_metrics, proof_resource_metrics
from peano_lab.kernel import proofs as kernel_proofs
from peano_lab.kernel.artifact_codec import (
    encode_artifact,
    encode_formula,
    encode_proof,
)
from peano_lab.kernel.checker import check, check_classical
from peano_lab.kernel.formulas import (
    And,
    Bot,
    Eq,
    Exists,
    Forall,
    Formula,
    Imp,
    Or,
    pretty_formula,
)
from peano_lab.kernel.proofs import (
    Axiom,
    CongS,
    DNE,
    EqRefl,
    EqSubst,
    ForallElim,
    ForallIntro,
    Hyp,
    ImpIntro,
    Ind,
    Proof,
)
from peano_lab.kernel.terms import Add, Mul, Succ, Term, Var, Zero
from peano_lab.library import theorems as theorem_library

from .profile import (
    SemanticProfileError,
    canonical_profile_theorem,
    semantic_profile,
    semantic_profile_sha256,
    validate_semantic_profile,
)


CONFORMANCE_FORMAT = "peano-hydra-semantic-conformance"
CONFORMANCE_VERSION = 1
FULL_LIBRARY_COUNT = 384
GENERATED_COUNT = 640
GENERATED_REFLEXIVITY_COUNT = 256
GENERATED_FORALL_ADD_COUNT = 256
GENERATED_FORALL_MUL_COUNT = 128
FULL_POSITIVE_COUNT = FULL_LIBRARY_COUNT + GENERATED_COUNT
FUEL_MULTIPLIER = 8
FUEL_OFFSET = 16
WIRE_NAT_MAX = 0xFFFF_FFFF
WASM_PORTABLE_INDEX_MAX = WIRE_NAT_MAX - 256

Disposition = Literal["accept", "certificate_rejected", "input_rejected"]
PythonDisposition = Literal["accept", "certificate_rejected", "not_applicable"]


class ConformanceError(RuntimeError):
    """The deterministic H0.2 corpus or one of its invariants failed."""


@dataclass(frozen=True, slots=True)
class PositiveCase:
    """One closed formula paired with a proposed positive certificate."""

    case_id: str
    source: Literal[
        "public-library",
        "generated-refl",
        "generated-forall-add",
        "generated-forall-mul",
    ]
    name: str
    formula: Formula
    proof: Proof
    dependencies: tuple[str, ...] = ()
    statement_source: str | None = None
    script: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ArtifactCase:
    """One exact artifact and the safe disposition expected from a checker."""

    case_id: str
    category: str
    artifact: bytes
    expected: Disposition
    python_disposition: PythonDisposition
    formula_sha256: str | None
    positive_case_id: str | None = None
    decoder_nodes: int | None = None
    decoder_depth: int | None = None
    wire_nat_max: int | None = None
    portable_index_max: int | None = None


@dataclass(frozen=True, slots=True)
class SemanticMutation:
    """A well-formed target/certificate pair that HA must reject."""

    case_id: str
    category: str
    formula: Formula
    proof: Proof
    classical_control_accepts: bool = False


def canonical_json_bytes(value: object) -> bytes:
    """Return the campaign's small deterministic JSON representation."""

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as error:
        raise ConformanceError(f"conformance value is not strict JSON: {error}") from None


def digest_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def digest_json(value: object) -> str:
    return digest_bytes(canonical_json_bytes(value))


def default_fuel(proof: Proof) -> int:
    """Use the shared Lean/Rust path-fuel convention for one certificate."""

    nodes, _ = proof_metrics(proof)
    if nodes < 1:  # pragma: no cover - every exact Proof has one root
        raise ConformanceError("a proof certificate must contain at least one node")
    return FUEL_MULTIPLIER * nodes + FUEL_OFFSET


def formula_sha256(formula: Formula) -> str:
    return digest_bytes(encode_formula(formula))


def proof_sha256(proof: Proof) -> str:
    return digest_bytes(encode_proof(proof))


def _term_shape(term: Term) -> tuple[int, int]:
    constructor = type(term)
    if constructor in (Zero, Var):
        return 1, 1
    if constructor is Succ:
        nodes, depth = _term_shape(term.term)
        return nodes + 1, depth + 1
    if constructor in (Add, Mul):
        left_nodes, left_depth = _term_shape(term.left)
        right_nodes, right_depth = _term_shape(term.right)
        return left_nodes + right_nodes + 1, max(left_depth, right_depth) + 1
    raise ConformanceError("artifact shape saw a malformed term")


def _formula_shape(formula: Formula) -> tuple[int, int]:
    constructor = type(formula)
    if constructor is Eq:
        left_nodes, left_depth = _term_shape(formula.left)
        right_nodes, right_depth = _term_shape(formula.right)
        return left_nodes + right_nodes + 1, max(left_depth, right_depth) + 1
    if constructor is Bot:
        return 1, 1
    if constructor in (Imp, And, Or):
        left_nodes, left_depth = _formula_shape(formula.left)
        right_nodes, right_depth = _formula_shape(formula.right)
        return left_nodes + right_nodes + 1, max(left_depth, right_depth) + 1
    if constructor in (Forall, Exists):
        nodes, depth = _formula_shape(formula.body)
        return nodes + 1, depth + 1
    raise ConformanceError("artifact shape saw a malformed formula")


def _proof_shape(proof: Proof) -> tuple[int, int]:
    """Count every tagged syntax node nested below a proof root."""

    total = 1
    child_depths = [0]
    for field in fields(proof):
        value = getattr(proof, field.name)
        if isinstance(value, Proof):
            nodes, depth = _proof_shape(value)
        elif isinstance(value, Formula):
            nodes, depth = _formula_shape(value)
        elif isinstance(value, Term):
            nodes, depth = _term_shape(value)
        else:
            continue
        total += nodes
        child_depths.append(depth)
    return total, max(child_depths) + 1


def artifact_decoder_shape(target: Formula, proof: Proof) -> tuple[int, int]:
    """Match Rust's decoder node/depth accounting (artifact root uncharged)."""

    formula_nodes, formula_depth = _formula_shape(target)
    proof_nodes, proof_depth = _proof_shape(proof)
    return formula_nodes + proof_nodes, max(formula_depth, proof_depth)


def _syntax_index_max(value: Term | Formula | Proof) -> int:
    maximum = 0
    pending: list[Term | Formula | Proof] = [value]
    while pending:
        node = pending.pop()
        if type(node) is Var:
            maximum = max(maximum, node.index)
        elif type(node) is Hyp:
            maximum = max(maximum, node.i)
        for field in fields(node):
            child = getattr(node, field.name)
            if isinstance(child, (Term, Formula, Proof)):
                pending.append(child)
    return maximum


def artifact_wire_shape(
    fuel: int, target: Formula, proof: Proof
) -> tuple[int, int]:
    """Return largest wire natural and checker-side index in an artifact."""

    if type(fuel) is not int or fuel < 0:
        raise ConformanceError("artifact fuel must be a non-negative integer")
    maximum_index = max(_syntax_index_max(target), _syntax_index_max(proof))
    return max(fuel, maximum_index), maximum_index


def expected_intuitionistic_constructor_names() -> tuple[str, ...]:
    """Return the exact constructor inventory frozen by the active profile."""

    return tuple(
        name for name in kernel_proofs.__all__ if name not in {"Proof", "DNE"}
    )


def proof_constructor_names(proof: Proof) -> frozenset[str]:
    """Collect exact proof constructors, visiting a shared object only once."""

    if not isinstance(proof, Proof):
        raise TypeError("proof constructor coverage requires a Proof")
    found: set[str] = set()
    seen: set[int] = set()
    pending = [proof]
    while pending:
        node = pending.pop()
        identity = id(node)
        if identity in seen:
            continue
        seen.add(identity)
        found.add(type(node).__name__)
        for field in fields(node):
            child = getattr(node, field.name)
            if isinstance(child, Proof):
                pending.append(child)
    return frozenset(found)


def assert_public_constructor_coverage(observed: Iterable[str]) -> tuple[str, ...]:
    """Require public certificates to exercise every intuitionistic rule."""

    expected = expected_intuitionistic_constructor_names()
    observed_set = set(observed)
    missing = [name for name in expected if name not in observed_set]
    forbidden = sorted(observed_set - set(expected))
    if missing or forbidden:
        details: list[str] = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if forbidden:
            details.append("out-of-profile " + ", ".join(forbidden))
        raise ConformanceError(
            "public proof-constructor coverage failed: " + "; ".join(details)
        )
    return expected


def library_positive_cases(
    names: Iterable[str] | None = None,
) -> Iterator[PositiveCase]:
    """Replay public entries in the requested deterministic ladder order."""

    selected = theorem_library.names() if names is None else tuple(names)
    if not selected or len(set(selected)) != len(selected):
        raise ConformanceError("library selection must be non-empty and unique")
    for index, requested in enumerate(selected):
        spec = theorem_library.get(requested)
        if spec is None or spec.name != requested:
            raise ConformanceError(
                f"library selection contains non-canonical theorem {requested!r}"
            )
        checked = theorem_library.replay(requested)
        yield PositiveCase(
            case_id=f"library-{index:04d}-{spec.name}",
            source="public-library",
            name=spec.name,
            formula=checked.formula,
            proof=checked.certificate,
            dependencies=spec.dependencies,
            statement_source=spec.statement,
            script=spec.script,
        )


def _numeral(value: int) -> Term:
    if type(value) is not int or not 0 <= value <= 256:
        raise ConformanceError("synthetic numeral must remain in profile bounds")
    result: Term = Zero()
    for _ in range(value):
        result = Succ(result)
    return result


def generated_positive_cases(
    *,
    forbidden_formula_sha256: Iterable[str] = (),
    count: int = GENERATED_COUNT,
) -> tuple[PositiveCase, ...]:
    """Build the reviewed 256/256/128 small-reflexivity corpus.

    The complete order is ``n = n`` for 0..255, then
    ``forall x. x + n = x + n`` for 0..255, then the analogous multiplication
    formulas for 0..127.  A prefix is available solely for focused tests.
    """

    if type(count) is not int or not 1 <= count <= GENERATED_COUNT:
        raise ConformanceError(
            f"generated count must be an integer in 1..{GENERATED_COUNT}"
        )
    forbidden = set(forbidden_formula_sha256)
    selected_hashes: set[str] = set()
    all_cases: list[PositiveCase] = []

    def retain(case: PositiveCase) -> None:
        digest = formula_sha256(case.formula)
        if digest in forbidden:
            raise ConformanceError(
                f"reviewed generated formula overlaps the public corpus: {case.case_id}"
            )
        if digest in selected_hashes:
            raise ConformanceError(
                f"reviewed generated formula is duplicated: {case.case_id}"
            )
        selected_hashes.add(digest)
        all_cases.append(case)

    for number in range(GENERATED_REFLEXIVITY_COUNT):
        term = _numeral(number)
        retain(
            PositiveCase(
                case_id=f"generated-refl-{number:04d}",
                source="generated-refl",
                name=f"generated_refl_{number:04d}",
                formula=Eq(term, term),
                proof=EqRefl(term),
            )
        )
    for number in range(GENERATED_FORALL_ADD_COUNT):
        term = Add(Var(0), _numeral(number))
        retain(
            PositiveCase(
                case_id=f"generated-forall-add-{number:04d}",
                source="generated-forall-add",
                name=f"generated_forall_add_{number:04d}",
                formula=Forall(Eq(term, term)),
                proof=ForallIntro(EqRefl(term)),
            )
        )
    for number in range(GENERATED_FORALL_MUL_COUNT):
        term = Mul(Var(0), _numeral(number))
        retain(
            PositiveCase(
                case_id=f"generated-forall-mul-{number:04d}",
                source="generated-forall-mul",
                name=f"generated_forall_mul_{number:04d}",
                formula=Forall(Eq(term, term)),
                proof=ForallIntro(EqRefl(term)),
            )
        )
    result = tuple(all_cases[:count])
    if len(result) != count or len({formula_sha256(c.formula) for c in result}) != count:
        raise ConformanceError("synthetic conformance construction lost uniqueness")
    return result


def wrong_target(formula: Formula) -> Formula:
    """Return the exact retained wrong-target mutation used by H0.2."""

    return Imp(formula, formula)


def validate_positive_with_python(case: PositiveCase) -> tuple[ArtifactCase, ArtifactCase]:
    """Check one positive and its reused-certificate wrong-target mutation."""

    canonical = pretty_formula(case.formula, [])
    if canonical_profile_theorem(canonical) != canonical:
        raise ConformanceError(f"{case.case_id} is not a canonical profile theorem")
    if not check((), case.proof, case.formula):
        raise ConformanceError(
            f"authoritative Python rejected positive {case.case_id!r}"
        )
    mutated_target = wrong_target(case.formula)
    if check((), case.proof, mutated_target):
        raise ConformanceError(
            f"authoritative Python accepted wrong target for {case.case_id!r}"
        )
    fuel = default_fuel(case.proof)
    original = encode_artifact(fuel, case.formula, case.proof)
    wrong = encode_artifact(fuel, mutated_target, case.proof)
    original_nodes, original_depth = artifact_decoder_shape(case.formula, case.proof)
    wrong_nodes, wrong_depth = artifact_decoder_shape(mutated_target, case.proof)
    original_wire, original_index = artifact_wire_shape(
        fuel, case.formula, case.proof
    )
    wrong_wire, wrong_index = artifact_wire_shape(
        fuel, mutated_target, case.proof
    )
    return (
        ArtifactCase(
            case_id=f"{case.case_id}:original",
            category="positive",
            artifact=original,
            expected="accept",
            python_disposition="accept",
            formula_sha256=formula_sha256(case.formula),
            positive_case_id=case.case_id,
            decoder_nodes=original_nodes,
            decoder_depth=original_depth,
            wire_nat_max=original_wire,
            portable_index_max=original_index,
        ),
        ArtifactCase(
            case_id=f"{case.case_id}:wrong-target",
            category="wrong-target",
            artifact=wrong,
            expected="certificate_rejected",
            python_disposition="certificate_rejected",
            formula_sha256=formula_sha256(mutated_target),
            positive_case_id=case.case_id,
            decoder_nodes=wrong_nodes,
            decoder_depth=wrong_depth,
            wire_nat_max=wrong_wire,
            portable_index_max=wrong_index,
        ),
    )


def positive_row(
    case: PositiveCase,
    validated: tuple[ArtifactCase, ArtifactCase] | None = None,
) -> dict[str, object]:
    """Return the deterministic semantic row used by both cold replay roots."""

    original, wrong = (
        validate_positive_with_python(case) if validated is None else validated
    )
    if (
        original.positive_case_id != case.case_id
        or wrong.positive_case_id != case.case_id
        or original.expected != "accept"
        or wrong.expected != "certificate_rejected"
    ):
        raise ConformanceError("positive row received artifacts for a different case")
    nodes, depth, objects, edges, reused = proof_resource_metrics(case.proof)
    canonical_statement = pretty_formula(case.formula, [])
    statement_source = case.statement_source or canonical_statement
    script_bytes = ("\n".join(case.script) + ("\n" if case.script else "")).encode(
        "utf-8"
    )
    return {
        "artifact_sha256": digest_bytes(original.artifact),
        "canonical_statement": canonical_statement,
        "case_id": case.case_id,
        "dependencies": list(case.dependencies),
        "formula_sha256": formula_sha256(case.formula),
        "fuel": default_fuel(case.proof),
        "name": case.name,
        "proof_depth": depth,
        "proof_edges": edges,
        "proof_nodes": nodes,
        "proof_objects": objects,
        "proof_reused_references": reused,
        "proof_sha256": proof_sha256(case.proof),
        "script_sha256": digest_bytes(script_bytes),
        "source": case.source,
        "statement_source": statement_source,
        "statement_source_sha256": digest_bytes(statement_source.encode("utf-8")),
        "wrong_target_artifact_sha256": digest_bytes(wrong.artifact),
        "wrong_target_formula_sha256": wrong.formula_sha256,
    }


def targeted_semantic_mutations() -> tuple[SemanticMutation, ...]:
    """Return small reviewed semantic mutations for the H0.2 rule boundary."""

    zero = Zero()
    one = Succ(zero)
    reflexive = Eq(zero, zero)
    forall_reflexive = Forall(Eq(Var(0), Var(0)))

    pa3_zero = ForallElim(Axiom("PA3"), zero)
    valid_substitution = EqSubst(Eq(Var(0), zero), pa3_zero, pa3_zero)
    if not check((), valid_substitution, reflexive):  # construction invariant
        raise ConformanceError("reviewed EqSubst control certificate drifted")

    motive = Eq(Var(0), Var(0))
    valid_step = ForallIntro(ImpIntro(EqRefl(Succ(Var(0)))))
    valid_induction = Ind(motive, EqRefl(zero), valid_step)
    if not check((), valid_induction, forall_reflexive):  # construction invariant
        raise ConformanceError("reviewed induction control certificate drifted")

    proposition = Eq(zero, one)
    dne_target = Imp(Imp(Imp(proposition, Bot()), Bot()), proposition)
    mutations = (
        SemanticMutation(
            "mutation-proof-constructor",
            "proof-constructor",
            reflexive,
            CongS(EqRefl(zero)),
        ),
        SemanticMutation(
            "mutation-binder-scope",
            "binder-scope",
            forall_reflexive,
            ForallIntro(EqRefl(Var(1))),
        ),
        SemanticMutation(
            "mutation-eq-subst-motive",
            "substitution",
            reflexive,
            EqSubst(Eq(Succ(Var(0)), zero), pa3_zero, pa3_zero),
        ),
        SemanticMutation(
            "mutation-ind-motive",
            "induction-motive",
            forall_reflexive,
            Ind(Eq(Var(0), zero), EqRefl(zero), valid_step),
        ),
        SemanticMutation(
            "mutation-ind-step",
            "induction-step",
            forall_reflexive,
            Ind(motive, EqRefl(zero), ForallIntro(ImpIntro(EqRefl(Var(0))))),
        ),
        SemanticMutation(
            "mutation-dne-ha",
            "classical-gate",
            dne_target,
            DNE(proposition),
            classical_control_accepts=True,
        ),
    )
    return mutations


def mutation_artifact_cases() -> tuple[ArtifactCase, ...]:
    """Check and encode every reviewed semantic and strict-codec mutation."""

    result: list[ArtifactCase] = []
    for mutation in targeted_semantic_mutations():
        if check((), mutation.proof, mutation.formula):
            raise ConformanceError(
                f"authoritative Python accepted mutation {mutation.case_id!r}"
            )
        classical_accepted = check_classical((), mutation.proof, mutation.formula)
        if classical_accepted is not mutation.classical_control_accepts:
            raise ConformanceError(
                f"classical control drifted for mutation {mutation.case_id!r}"
            )
        decoder_nodes, decoder_depth = artifact_decoder_shape(
            mutation.formula, mutation.proof
        )
        fuel = default_fuel(mutation.proof)
        wire_nat, portable_index = artifact_wire_shape(
            fuel, mutation.formula, mutation.proof
        )
        result.append(
            ArtifactCase(
                case_id=mutation.case_id,
                category=mutation.category,
                artifact=encode_artifact(fuel, mutation.formula, mutation.proof),
                expected="certificate_rejected",
                python_disposition="certificate_rejected",
                formula_sha256=formula_sha256(mutation.formula),
                decoder_nodes=decoder_nodes,
                decoder_depth=decoder_depth,
                wire_nat_max=wire_nat,
                portable_index_max=portable_index,
            )
        )

    valid_formula = Eq(Zero(), Zero())
    valid_proof = EqRefl(Zero())
    valid_nodes, valid_depth = artifact_decoder_shape(valid_formula, valid_proof)
    valid_fuel = FUEL_OFFSET + FUEL_MULTIPLIER
    valid_wire, valid_index = artifact_wire_shape(
        valid_fuel, valid_formula, valid_proof
    )
    valid = encode_artifact(valid_fuel, valid_formula, valid_proof)
    if not valid.endswith(b"\n"):  # pragma: no cover - codec contract
        raise ConformanceError("canonical artifact lost its terminal newline")
    result.append(
        ArtifactCase(
            case_id="mutation-malformed-artifact",
            category="artifact-codec",
            artifact=valid[:-1],
            expected="input_rejected",
            python_disposition="not_applicable",
            formula_sha256=None,
            decoder_nodes=valid_nodes,
            decoder_depth=valid_depth,
            wire_nat_max=valid_wire,
            portable_index_max=valid_index,
        )
    )

    # These open targets are outside the theorem profile.  They are retained
    # only to prove that diagnostic implementation boundaries are classified
    # as resource exclusions rather than logical disagreements.
    for case_id, category, index in (
        (
            "mutation-wire-nat-envelope",
            "wire-nat-envelope",
            WIRE_NAT_MAX + 1,
        ),
        (
            "mutation-wasm-portable-index-envelope",
            "wasm-index-envelope",
            WASM_PORTABLE_INDEX_MAX + 1,
        ),
    ):
        target = Eq(Var(index), Var(index))
        proof = EqRefl(Var(index))
        fuel = default_fuel(proof)
        nodes, depth = artifact_decoder_shape(target, proof)
        wire_nat, portable_index = artifact_wire_shape(fuel, target, proof)
        result.append(
            ArtifactCase(
                case_id=case_id,
                category=category,
                artifact=encode_artifact(fuel, target, proof),
                expected="certificate_rejected",
                python_disposition="not_applicable",
                formula_sha256=formula_sha256(target),
                decoder_nodes=nodes,
                decoder_depth=depth,
                wire_nat_max=wire_nat,
                portable_index_max=portable_index,
            )
        )

    result.append(
        ArtifactCase(
            case_id="mutation-zero-checker-fuel",
            category="checker-fuel-envelope",
            artifact=encode_artifact(0, valid_formula, valid_proof),
            expected="certificate_rejected",
            python_disposition="not_applicable",
            formula_sha256=formula_sha256(valid_formula),
            decoder_nodes=valid_nodes,
            decoder_depth=valid_depth,
            wire_nat_max=0,
            portable_index_max=0,
        )
    )
    return tuple(result)


def validate_boundary_mutations(
    *,
    result_validator: Callable[[object], object] | None = None,
    valid_unknown_result: Mapping[str, object] | None = None,
) -> tuple[dict[str, str], ...]:
    """Require profile-translation and negative-evidence attempts to fail.

    ``result_validator`` and ``valid_unknown_result`` are injectable so H0.2
    tests do not couple to an H0.1b implementation detail.  In production the
    frozen result-schema implementation is loaded lazily.
    """

    mutated_profile = deepcopy(semantic_profile())
    translations = mutated_profile.get("translations")
    if type(translations) is not dict or type(translations.get("external")) is not list:
        raise ConformanceError("registered external-translation inventory drifted")
    translations["external"].append(
        {
            "from": "untrusted external formula",
            "name": "forged-external-translation",
            "to": "unregistered core formula",
        }
    )
    try:
        validate_semantic_profile(mutated_profile)
    except SemanticProfileError:
        profile_result = {
            "case_id": "mutation-profile-external-translation",
            "category": "translation",
            "disposition": "profile_rejected",
        }
    else:  # pragma: no cover - a false acceptance is a campaign-stopping bug
        raise ConformanceError("profile accepted an unregistered external translation")

    if result_validator is None or valid_unknown_result is None:
        try:
            from .result_schema import (  # type: ignore[import-not-found]
                build_unknown_result,
                validate_result,
            )
        except ImportError as error:  # pragma: no cover - transitional checkout
            raise ConformanceError(
                "H0.1b result validator is required for negative-evidence mutation"
            ) from error
        if result_validator is None:
            result_validator = validate_result
        if valid_unknown_result is None:
            valid_unknown_result = build_unknown_result(
                "0 = 0",
                reason="search-exhausted",
                run_id="peano-hydra-h0-boundary-control",
            )

    base = dict(valid_unknown_result)
    try:
        result_validator(base)
    except ValueError as error:
        raise ConformanceError(
            f"negative-evidence control is not a valid unknown result: {error}"
        ) from error

    attempts = []
    not_theorem = dict(base)
    not_theorem["kind"] = "not_theorem"
    attempts.append(("mutation-negative-kind", not_theorem))
    negative_field = dict(base)
    negative_field["negative_evidence_sha256"] = "0" * 64
    attempts.append(("mutation-negative-field", negative_field))

    negative_results: list[dict[str, str]] = []
    for case_id, attempted in attempts:
        try:
            result_validator(attempted)
        except ValueError:
            negative_results.append(
                {
                    "case_id": case_id,
                    "category": "negative-evidence",
                    "disposition": "schema_rejected",
                }
            )
        else:  # pragma: no cover - a false acceptance is a campaign-stopping bug
            raise ConformanceError(f"result schema accepted {case_id!r}")
    return (profile_result, *negative_results)


def artifact_case_row(case: ArtifactCase) -> dict[str, object]:
    """Strip inert bytes into the deterministic row retained in reports."""

    return {
        "artifact_bytes": len(case.artifact),
        "artifact_sha256": digest_bytes(case.artifact),
        "case_id": case.case_id,
        "category": case.category,
        "decoder_depth": case.decoder_depth,
        "decoder_nodes": case.decoder_nodes,
        "expected": case.expected,
        "formula_sha256": case.formula_sha256,
        "positive_case_id": case.positive_case_id,
        "portable_index_max": case.portable_index_max,
        "python_disposition": case.python_disposition,
        "wire_nat_max": case.wire_nat_max,
    }


def assert_full_positive_corpus(
    library_rows: Iterable[Mapping[str, object]],
    generated: Iterable[PositiveCase],
) -> tuple[str, ...]:
    """Enforce the exact 384 + 640 positive, distinct-formula contract."""

    library = tuple(library_rows)
    synthetic = tuple(generated)
    if len(library) != FULL_LIBRARY_COUNT:
        raise ConformanceError(
            f"full public corpus needs {FULL_LIBRARY_COUNT} rows, found {len(library)}"
        )
    if len(synthetic) != GENERATED_COUNT:
        raise ConformanceError(
            f"full generated corpus needs {GENERATED_COUNT} rows, found {len(synthetic)}"
        )
    source_counts = {
        source: sum(case.source == source for case in synthetic)
        for source in (
            "generated-refl",
            "generated-forall-add",
            "generated-forall-mul",
        )
    }
    if source_counts != {
        "generated-refl": GENERATED_REFLEXIVITY_COUNT,
        "generated-forall-add": GENERATED_FORALL_ADD_COUNT,
        "generated-forall-mul": GENERATED_FORALL_MUL_COUNT,
    }:
        raise ConformanceError("generated reflexivity strata have the wrong sizes")
    hashes = [str(row["formula_sha256"]) for row in library]
    hashes.extend(formula_sha256(case.formula) for case in synthetic)
    if len(hashes) != FULL_POSITIVE_COUNT or len(set(hashes)) != FULL_POSITIVE_COUNT:
        raise ConformanceError(
            "the full H0.2 positive corpus must contain 1,024 distinct formulas"
        )
    return tuple(hashes)


__all__ = [
    "ArtifactCase",
    "CONFORMANCE_FORMAT",
    "CONFORMANCE_VERSION",
    "ConformanceError",
    "Disposition",
    "FULL_LIBRARY_COUNT",
    "FULL_POSITIVE_COUNT",
    "FUEL_MULTIPLIER",
    "FUEL_OFFSET",
    "GENERATED_COUNT",
    "GENERATED_FORALL_ADD_COUNT",
    "GENERATED_FORALL_MUL_COUNT",
    "GENERATED_REFLEXIVITY_COUNT",
    "WASM_PORTABLE_INDEX_MAX",
    "WIRE_NAT_MAX",
    "PositiveCase",
    "PythonDisposition",
    "SemanticMutation",
    "artifact_case_row",
    "artifact_decoder_shape",
    "artifact_wire_shape",
    "assert_full_positive_corpus",
    "assert_public_constructor_coverage",
    "canonical_json_bytes",
    "default_fuel",
    "digest_bytes",
    "digest_json",
    "expected_intuitionistic_constructor_names",
    "formula_sha256",
    "generated_positive_cases",
    "library_positive_cases",
    "mutation_artifact_cases",
    "positive_row",
    "proof_constructor_names",
    "proof_sha256",
    "semantic_profile_sha256",
    "targeted_semantic_mutations",
    "validate_boundary_mutations",
    "validate_positive_with_python",
    "wrong_target",
]
