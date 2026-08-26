"""Authored, bounded certificate-conformance fixtures for a separate reference.

These are NOT autonomous Hydra discoveries, training examples, a sealed DEV
benchmark, or a decision procedure.  The production checker validates the
exact inert artifact bytes; an independently built Lean checker must judge
those same bytes separately.  No Lean process is launched by this module.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import stat

from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import (
    And, Bot, Eq, Exists, Forall, Formula, Imp, Or,
    parse_formula_in_context, pretty_formula,
)
from peano_lab.kernel.proofs import (
    AndElimL, AndElimR, AndIntro, Axiom, BotElim, CongAdd, CongMul, CongS,
    Cut, DNE, EqRefl, EqSubst, EqSym, EqTrans, ExistsElim, ExistsIntro,
    ForallElim, ForallIntro, Hyp, ImpElim, ImpIntro, Ind, OrElim,
    OrIntroL, OrIntroR, Proof,
)
from peano_lab.kernel.terms import Add, Mul, Succ, Term, Var, Zero
from peano_lab.library.proof_bundle import (
    decode_formula, decode_proof, encode_formula, encode_proof,
)
from training.peano_hydra.protocol import development_profile, validate_statement


SCHEMA = "hydra-native-lean-conformance-v1"
FUEL = 4096
SEEDS = 32
TEMPLATES = 32
MAX_CASES = 2048
MAX_CASE_BYTES = 128 * 1024
MAX_SUITE_BYTES = 32 * 1024 * 1024
_ROOT = Path(__file__).resolve().parents[2]
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_NAME = re.compile(r"[a-z][a-z0-9_-]{0,95}\Z")
_PROOF_TAGS = frozenset({
    "hyp", "imp_intro", "imp_elim", "cut", "and_intro", "and_elim_l", "and_elim_r",
    "or_intro_l", "or_intro_r", "or_elim", "bot_elim", "forall_intro", "forall_elim",
    "exists_intro", "exists_elim", "eq_refl", "eq_sym", "eq_trans", "cong_s",
    "cong_add", "cong_mul", "eq_subst", "axiom", "ind", "dne",
})


class ConformanceError(ValueError):
    """A fixture or its exact evidence binding is invalid, not a disproof."""


def _json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _wire(value: object) -> bytes:
    # The existing primitive v2 codec has ASCII tags/integers only and requires
    # one final LF.  This serialization is an untrusted adapter, not a checker.
    return json.dumps(value, ensure_ascii=True, allow_nan=False,
                      separators=(",", ":")).encode("ascii") + b"\n"


@dataclass(frozen=True, slots=True)
class ConformanceCase:
    case_id: str
    family: str
    seed: int
    kind: str
    statement: str | None
    expected_native: bool | None
    expected_lean: str
    artifact: bytes
    mutation: str | None = None
    parent_case_id: str | None = None

    def __post_init__(self) -> None:
        for value in (self.case_id, self.family):
            if type(value) is not str or _NAME.fullmatch(value) is None:
                raise ConformanceError("fixture identifiers must be safe bounded ASCII names")
        if type(self.seed) is not int or not 0 <= self.seed < SEEDS:
            raise ConformanceError("fixture seed is outside the fixed range")
        if type(self.kind) is not str or self.kind not in {"positive", "certificate_mutation", "wire_mutation"}:
            raise ConformanceError("unknown fixture kind")
        if type(self.artifact) is not bytes or not 0 < len(self.artifact) <= MAX_CASE_BYTES:
            raise ConformanceError("fixture artifact must be bounded exact bytes")
        if type(self.expected_lean) is not str or self.expected_lean not in {"ACCEPT", "REJECT", "DECODE_ERROR"}:
            raise ConformanceError("unknown Lean fixture expectation")
        for value in (self.mutation, self.parent_case_id):
            if value is not None and (type(value) is not str or _NAME.fullmatch(value) is None):
                raise ConformanceError("mutation/parent identifiers must be safe bounded ASCII names")
        if self.kind == "wire_mutation":
            if self.statement is not None or self.expected_native is not None or self.expected_lean == "ACCEPT":
                raise ConformanceError("wire-only fixtures have no native theorem-check expectation")
        else:
            if type(self.statement) is not str or validate_statement(self.statement) != self.statement:
                raise ConformanceError("fixture statement must be a canonical closed in-profile formula")
            positive = self.kind == "positive"
            if type(self.expected_native) is not bool or self.expected_native != positive:
                raise ConformanceError("fixture kind and native expectation disagree")
            if self.expected_lean != ("ACCEPT" if positive else "REJECT"):
                raise ConformanceError("fixture kind and Lean expectation disagree")

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id, "family": self.family, "seed": self.seed,
            "kind": self.kind, "statement": self.statement,
            "statement_sha256": None if self.statement is None else _sha(self.statement.encode("utf-8")),
            "expected_native": self.expected_native, "expected_lean": self.expected_lean,
            "artifact_bytes": len(self.artifact), "artifact_sha256": _sha(self.artifact),
            "mutation": self.mutation, "parent_case_id": self.parent_case_id,
            "claim": "candidate-certificate validity only; no theoremhood-negative conclusion",
        }


def _numeral(value: int, tail: Term | None = None) -> Term:
    result: Term = Zero() if tail is None else tail
    for _ in range(value):
        result = Succ(result)
    return result


def _at(name: str, *terms: Term) -> Proof:
    result: Proof = Axiom(name)
    for term in terms:
        result = ForallElim(result, term)
    return result


def _templates(seed: int) -> tuple[tuple[str, Formula, Proof], ...]:
    z, t, x, y = Zero(), _numeral(seed), Var(0), Var(1)
    a, b, r = Eq(t, z), Eq(z, Succ(z)), Eq(t, t)
    universal = Forall(Eq(Add(x, t), Add(x, t)))
    motive = Eq(Add(t, x), _numeral(seed, x))
    step = ForallIntro(ImpIntro(EqTrans(_at("PA4", t, x), CongS(Hyp(0)))))
    subst_motive = Eq(Add(t, t), Add(x, x))
    # Under two ambient binders [m,n], slot 0 in this motive is the equality
    # replacement, so m/n are slots 1/2.  This is deliberately hand-authored,
    # not computed with the production substitution routine being exercised.
    captured_motive = Eq(Add(Var(1), Var(2)), Add(Var(1), Var(0)))
    return (
        ("eq-refl", r, EqRefl(t)),
        ("eq-sym", Imp(a, Eq(z, t)), ImpIntro(EqSym(Hyp(0)))),
        ("eq-trans", Imp(a, Imp(Eq(z, Succ(t)), Eq(t, Succ(t)))),
         ImpIntro(ImpIntro(EqTrans(Hyp(1), Hyp(0))))),
        ("cong-s", Imp(a, Eq(Succ(t), Succ(z))), ImpIntro(CongS(Hyp(0)))),
        ("cong-add", Imp(a, Eq(Add(t, t), Add(z, z))), ImpIntro(CongAdd(Hyp(0), Hyp(0)))),
        ("cong-mul", Imp(a, Eq(Mul(t, t), Mul(z, z))), ImpIntro(CongMul(Hyp(0), Hyp(0)))),
        ("imp-identity", Imp(a, a), ImpIntro(Hyp(0))),
        ("imp-elim", Imp(Imp(a, b), Imp(a, b)), ImpIntro(ImpIntro(ImpElim(Hyp(1), Hyp(0))))),
        ("and-intro", Imp(a, And(a, a)), ImpIntro(AndIntro(Hyp(0), Hyp(0)))),
        ("and-elim-left", Imp(And(a, b), a), ImpIntro(AndElimL(Hyp(0)))),
        ("and-elim-right", Imp(And(a, b), b), ImpIntro(AndElimR(Hyp(0)))),
        ("or-intro-left", Imp(a, Or(a, b)), ImpIntro(OrIntroL(Hyp(0)))),
        ("or-intro-right", Imp(a, Or(b, a)), ImpIntro(OrIntroR(Hyp(0)))),
        ("or-elim", Imp(Or(a, a), a), ImpIntro(OrElim(Hyp(0), Hyp(0), Hyp(0)))),
        ("bot-elim", Imp(Bot(), a), ImpIntro(BotElim(Hyp(0)))),
        ("forall-intro", universal, ForallIntro(EqRefl(Add(x, t)))),
        ("forall-elim", Eq(Add(t, t), Add(t, t)),
         ForallElim(Cut(universal, universal, ForallIntro(EqRefl(Add(x, t))), Hyp(0)), t)),
        ("exists-intro", Exists(Eq(x, t)), ExistsIntro(t, EqRefl(t))),
        ("exists-elim", Imp(Exists(Eq(x, t)), Exists(Eq(t, x))),
         ImpIntro(ExistsElim(Hyp(0), ExistsIntro(x, EqSym(Hyp(0)))))),
        ("eq-subst", Imp(a, Eq(Add(t, t), Add(z, z))),
         ImpIntro(EqSubst(subst_motive, Hyp(0), EqRefl(Add(t, t))))),
        ("cut", r, Cut(r, r, EqRefl(t), Hyp(0))),
        ("induction", Forall(motive), Ind(motive, _at("PA3", t), step)),
        ("pa1", Imp(Eq(Succ(t), z), Bot()), _at("PA1", t)),
        ("pa2", Imp(Eq(Succ(t), Succ(z)), Eq(t, z)), _at("PA2", t, z)),
        ("pa3", Eq(Add(t, z), t), _at("PA3", t)),
        ("pa4", Eq(Add(t, Succ(z)), Succ(Add(t, z))), _at("PA4", t, z)),
        ("pa5", Eq(Mul(t, z), z), _at("PA5", t)),
        ("pa6", Eq(Mul(t, Succ(z)), Add(Mul(t, z), t)), _at("PA6", t, z)),
        ("nested-binder", Forall(Forall(Imp(Eq(y, t), Eq(y, t)))),
         ForallIntro(ForallIntro(ImpIntro(Hyp(0))))),
        ("forall-exists", Forall(Exists(Eq(Add(x, t), Add(y, t)))),
         ForallIntro(ExistsIntro(x, EqRefl(Add(x, t))))),
        ("forall-context", Imp(universal, universal),
         ImpIntro(ForallIntro(ForallElim(Hyp(0), x)))),
        ("subst-under-binder", Forall(Imp(Eq(x, t), Forall(Eq(Add(x, y), Add(x, t))))),
         ForallIntro(ImpIntro(ForallIntro(EqSubst(captured_motive, Hyp(0), EqRefl(Add(x, y))))))),
    )


def _case(case_id: str, family: str, seed: int, target: Formula, proof: Proof,
          *, mutation: str | None = None, parent: str | None = None) -> ConformanceCase:
    statement = validate_statement(pretty_formula(target, []))
    if parse_formula_in_context(statement, []) != target:
        raise ConformanceError("authored target lost its exact closed statement")
    positive = mutation is None
    return ConformanceCase(
        case_id, family, seed, "positive" if positive else "certificate_mutation",
        statement, positive, "ACCEPT" if positive else "REJECT",
        _wire(["peano-lab-v2", FUEL, encode_formula(target), encode_proof(proof)]), mutation, parent,
    )


def _replace_first(tree: object, tag: str, replace_node) -> object:
    if type(tree) is not list:
        return tree
    if tree and tree[0] == tag:
        return replace_node(tree)
    for index, child in enumerate(tree[1:], 1):
        if type(child) is list:
            replaced = _replace_first(child, tag, replace_node)
            if replaced is not child:
                return tree[:index] + [replaced] + tree[index + 1:]
    return tree


def _mutate(base: object, family: str) -> tuple[object, str]:
    changes = {
        "eq-refl": ("eq_refl", lambda p: ["eq_refl", ["succ", p[1]]], "wrong-reflexive-term"),
        "eq-sym": ("eq_sym", lambda p: p[1], "removed-symmetry"),
        "eq-trans": ("eq_trans", lambda p: [p[0], p[2], p[1]], "reversed-transitivity-premises"),
        "cong-s": ("cong_s", lambda p: ["eq_sym", p[1]], "wrong-congruence-constructor"),
        "cong-add": ("cong_add", lambda p: ["cong_mul", *p[1:]], "add-mul-constructor-swap"),
        "cong-mul": ("cong_mul", lambda p: ["cong_add", *p[1:]], "mul-add-constructor-swap"),
        "imp-identity": ("hyp", lambda p: ["hyp", 1], "wrong-hypothesis-slot"),
        "imp-elim": ("imp_elim", lambda p: [p[0], p[2], p[1]], "swapped-function-argument"),
        "and-intro": ("and_intro", lambda p: [p[0], p[1], ["hyp", 7]], "missing-conjunct-proof"),
        "and-elim-left": ("and_elim_l", lambda p: ["and_elim_r", p[1]], "wrong-conjunction-projection"),
        "and-elim-right": ("and_elim_r", lambda p: ["and_elim_l", p[1]], "wrong-conjunction-projection"),
        "or-intro-left": ("or_intro_l", lambda p: ["or_intro_r", p[1]], "wrong-disjunction-injection"),
        "or-intro-right": ("or_intro_r", lambda p: ["or_intro_l", p[1]], "wrong-disjunction-injection"),
        "or-elim": ("or_elim", lambda p: [p[0], p[1], ["hyp", 7], p[3]], "invalid-case-context"),
        "bot-elim": ("bot_elim", lambda p: p[1], "missing-bottom-elimination"),
        "forall-intro": ("forall_intro", lambda p: p[1], "missing-universal-binder"),
        "forall-elim": ("forall_elim", lambda p: [p[0], p[1], ["succ", p[2]]], "wrong-universal-instantiation"),
        "exists-intro": ("exists_intro", lambda p: [p[0], ["succ", p[1]], p[2]], "witness-proof-disagreement"),
        "exists-elim": ("exists_intro", lambda p: [p[0], ["var", 1], p[2]], "existential-eigenvariable-escape"),
        "eq-subst": ("eq_subst", lambda p: [p[0], ["eq", ["var", 0], ["zero"]], p[2], p[3]], "wrong-equality-motive"),
        "cut": ("cut", lambda p: [p[0], ["bot"], p[2], p[3], p[4]], "wrong-cut-proposition"),
        "induction": ("ind", lambda p: [p[0], ["eq", ["var", 0], ["zero"]], p[2], p[3]], "wrong-induction-motive"),
        "nested-binder": ("hyp", lambda p: ["eq_refl", ["var", 0]], "outer-inner-variable-confusion"),
        "forall-exists": ("exists_intro", lambda p: [p[0], ["var", 1], p[2]], "wrong-witness-binder-depth"),
        "forall-context": ("forall_elim", lambda p: [p[0], p[1], ["succ", p[2]]], "context-specialization-shift"),
        "subst-under-binder": ("eq_subst", lambda p: [p[0], ["eq", ["add", ["var", 0], ["var", 1]],
                                                                 ["add", ["var", 0], ["var", 2]]], p[2], p[3]], "capturing-substitution-motive"),
    }
    if family.startswith("pa"):
        tag, replacement, label = "axiom", lambda p: ["axiom", "PA5" if p[1] != "PA5" else "PA3"], "wrong-pa-axiom"
    else:
        tag, replacement, label = changes[family]
    mutated = _replace_first(base, tag, replacement)
    if mutated is base:
        raise ConformanceError(f"mutation did not reach its intended constructor: {family}")
    return mutated, label


def _wire_cases(sample: ConformanceCase) -> tuple[ConformanceCase, ...]:
    original = json.loads(sample.artifact)
    mutated: list[tuple[str, bytes, str]] = [
        ("truncated-json", sample.artifact[:-4], "DECODE_ERROR"),
        ("leading-whitespace", b" " + sample.artifact, "DECODE_ERROR"),
        ("missing-final-lf", sample.artifact[:-1], "DECODE_ERROR"),
        ("extra-final-lf", sample.artifact + b"\n", "DECODE_ERROR"),
        ("unknown-envelope", _wire(["peano-lab-v999", *original[1:]]), "DECODE_ERROR"),
        ("extra-envelope-field", _wire(original + [0]), "DECODE_ERROR"),
        ("boolean-fuel", _wire([original[0], True, *original[2:]]), "DECODE_ERROR"),
        ("negative-fuel", _wire([original[0], -1, *original[2:]]), "DECODE_ERROR"),
        ("fractional-fuel", _wire([original[0], 1.5, *original[2:]]), "DECODE_ERROR"),
        ("unknown-proof-tag", _wire(original[:3] + [["trusted_theorem", "not-a-proof"]]), "DECODE_ERROR"),
        ("unknown-axiom", _wire(original[:3] + [["axiom", "PA7"]]), "DECODE_ERROR"),
        ("wrong-proof-arity", _wire(original[:3] + [["eq_refl"]]), "DECODE_ERROR"),
        ("negative-variable", _wire(original[:3] + [["eq_refl", ["var", -1]]]), "DECODE_ERROR"),
        ("wrong-formula-arity", _wire(original[:2] + [["eq", ["zero"]], original[3]]), "DECODE_ERROR"),
        ("object-envelope", b'{"v":2,"v":2}\n', "DECODE_ERROR"),
        # Decoded but rejected by the Lean artifact gate, not parser errors or
        # Python/Lean certificate disagreements: native check has no fuel gate.
        ("zero-fuel", _wire([original[0], 0, *original[2:]]), "REJECT"),
        ("open-target", _wire([original[0], FUEL, ["eq", ["var", 0], ["var", 0]],
                               ["eq_refl", ["var", 0]]]), "REJECT"),
    ]
    return tuple(ConformanceCase(
        f"wire-{name}", name, 0, "wire_mutation", None, None, expected, artifact,
        name, sample.case_id,
    ) for name, artifact, expected in mutated)


def _bounded(cases: object) -> tuple[ConformanceCase, ...]:
    if type(cases) is not tuple or not cases or len(cases) > MAX_CASES:
        raise ConformanceError("suite must be a bounded non-empty exact tuple")
    if not all(type(case) is ConformanceCase for case in cases):
        raise ConformanceError("suite requires exact ConformanceCase values")
    if len({case.case_id for case in cases}) != len(cases):
        raise ConformanceError("duplicate conformance case IDs")
    if sum(len(case.artifact) for case in cases) > MAX_SUITE_BYTES:
        raise ConformanceError("suite exceeds its aggregate byte limit")
    return cases


@lru_cache(maxsize=1)
def build_conformance_cases() -> tuple[ConformanceCase, ...]:
    """Return 1,024 unique admitted positive formulas and separate mutations.

    Thirty-two authored rule templates receive thirty-two small numeral
    substitutions. An explicit reflexive tag conjunct encodes (template,
    seed), keeping same-goal/different-rule tests distinct without claiming
    distinct mathematical lineages or adding an assumption to the real rule
    fixture. The manifest reports this construction explicitly.
    """

    cases: list[ConformanceCase] = []
    positives: list[ConformanceCase] = []
    for seed in range(SEEDS):
        templates = _templates(seed)
        if len(templates) != TEMPLATES:
            raise ConformanceError("the fixed template inventory changed")
        for number, (family, formula, proof) in enumerate(templates):
            # A compact, ordinary arithmetic spelling saves AST space without
            # adding numeral syntax or changing the numeric admission ceiling.
            family_tag = Add(Mul(_numeral(number // 8), _numeral(8)), _numeral(number % 8))
            tag = Add(family_tag, _numeral(seed))
            marker = Eq(tag, tag)
            case = _case(f"positive-{family}-{seed:02d}", family, seed,
                         And(marker, formula), AndIntro(EqRefl(tag), proof))
            positives.append(case)
            cases.append(case)
    if len({case.statement for case in positives}) != TEMPLATES * SEEDS:
        raise ConformanceError("positive formulas must remain exactly 1,024 distinct canonical statements")
    for parent in positives:
        if not 1 <= parent.seed <= 8:
            continue
        data = json.loads(parent.artifact)
        body, label = _mutate(data[3][2], parent.family)
        data[3] = ["and_intro", data[3][1], body]
        cases.append(ConformanceCase(
            f"mutation-{parent.family}-{parent.seed:02d}", parent.family, parent.seed,
            "certificate_mutation", parent.statement, False, "REJECT", _wire(data), label, parent.case_id,
        ))
        if parent.family == "induction":
            for slot, label in ((2, "wrong-induction-base"), (3, "wrong-induction-step")):
                changed = json.loads(parent.artifact)
                changed[3][2][slot] = ["eq_refl", ["zero"]]
                cases.append(ConformanceCase(
                    f"mutation-{label}-{parent.seed:02d}", "induction", parent.seed,
                    "certificate_mutation", parent.statement, False, "REJECT", _wire(changed), label, parent.case_id,
                ))
    for seed in range(8):
        proposition = Eq(_numeral(seed), Zero())
        target = Imp(Imp(Imp(proposition, Bot()), Bot()), proposition)
        cases.append(_case(f"mutation-dne-{seed:02d}", "dne-boundary", seed, target,
                           DNE(proposition), mutation="classical-rule-in-intuitionistic-mode"))
    cases.extend(_wire_cases(positives[0]))
    return _bounded(tuple(cases))


def _decode_bound_case(case: ConformanceCase) -> tuple[Formula, Proof]:
    if case.kind == "wire_mutation":
        raise ConformanceError("wire-only fixtures have no native certificate endpoint")
    try:
        data = json.loads(case.artifact)
        if (type(data) is not list or len(data) != 4 or data[0] != "peano-lab-v2"
                or type(data[1]) is not int or data[1] != FUEL or _wire(data) != case.artifact):
            raise ConformanceError("native fixture bytes lost their exact canonical v2 envelope/fuel")
        target = decode_formula(data[2])
        proof = decode_proof(data[3])
        original = parse_formula_in_context(case.statement, [])
        if (target != original or validate_statement(case.statement) != case.statement
                or encode_formula(target) != data[2] or encode_proof(proof) != data[3]):
            raise ConformanceError("serialized target/certificate differs from its exact bound statement")
    except (UnicodeError, ValueError, TypeError, RecursionError) as exc:
        raise ConformanceError(f"invalid native fixture {case.case_id}: {exc}") from None
    return original, proof


def check_native_cases(cases: tuple[ConformanceCase, ...]) -> dict[str, object]:
    """Judge decoded artifact bytes against their original bound statements.

    A False result rejects this certificate, not its theorem. Wire mutations
    remain explicitly unmeasured on this endpoint; Lean must check their
    decoding, canonicality, fuel and closure behavior independently.
    """

    rows = []
    for case in _bounded(cases):
        if case.kind == "wire_mutation":
            result = None
        else:
            original, proof = _decode_bound_case(case)
            result = check((), proof, original)
        rows.append({"case_id": case.case_id, "kind": case.kind,
                     "artifact_sha256": _sha(case.artifact), "native_accepts": result,
                     "expected_native": case.expected_native, "matched": result == case.expected_native})
    mismatches = [row["case_id"] for row in rows if not row["matched"]]
    report = {
        "v": 1, "schema": SCHEMA, "endpoint": "production-intuitionistic-kernel",
        "checked_exact_artifact_bytes": True, "classical": False,
        "positive_certificates_checked": sum(row["kind"] == "positive" for row in rows),
        "positive_certificates_accepted": sum(row["kind"] == "positive" and row["native_accepts"] is True for row in rows),
        "certificate_mutations_rejected": sum(row["kind"] == "certificate_mutation" and row["native_accepts"] is False for row in rows),
        "wire_cases_skipped": sum(row["kind"] == "wire_mutation" for row in rows),
        "all_expected_results": not mismatches, "mismatches": mismatches, "rows": rows,
        "negative_theoremhood_claim": False, "independent_reference_checked": False,
    }
    report["report_sha256"] = _sha(_json(report))
    return report


def _proof_inventory(cases: tuple[ConformanceCase, ...], *, authored_body: bool = False) -> tuple[dict[str, int], dict[str, int]]:
    constructors: Counter[str] = Counter()
    axioms: Counter[str] = Counter()
    for case in cases:
        if case.kind != "positive":
            continue
        target, decoded_proof = _decode_bound_case(case)
        proof = encode_proof(decoded_proof)
        if authored_body and (type(target) is not And or type(decoded_proof) is not AndIntro):
            raise ConformanceError("authored templates require the declared reflexive tag conjunct")
        pending = [proof[2] if authored_body else proof]
        while pending:
            value = pending.pop()
            if type(value) is list and value:
                tag = value[0]
                if type(tag) is str and tag in _PROOF_TAGS:
                    constructors[tag] += 1
                    if tag == "axiom":
                        axioms[value[1]] += 1
                pending.extend(item for item in value[1:] if type(item) is list)
    return dict(sorted(constructors.items())), dict(sorted(axioms.items()))


def conformance_manifest(
    cases: tuple[ConformanceCase, ...], *, epoch_sha256: str | None = None,
) -> dict[str, object]:
    """Describe expected fixtures and provenance, never an executed Lean result."""

    cases = _bounded(cases)
    if epoch_sha256 is not None and (type(epoch_sha256) is not str or _DIGEST.fullmatch(epoch_sha256) is None):
        raise ConformanceError("epoch_sha256 must be a lowercase SHA-256 or None")
    sources = []
    for relative in ("training/peano_hydra/conformance.py", "peano-lab/py/peano_lab/library/proof_bundle.py"):
        path = _ROOT / relative
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_size > 2_000_000:
            raise ConformanceError("generator/serializer source must be a bounded regular file")
        raw = path.read_bytes()
        sources.append({"path": relative, "bytes": len(raw), "sha256": _sha(raw)})
    constructors, axioms = _proof_inventory(cases)
    authored_constructors, _ = _proof_inventory(cases, authored_body=True)
    positives = tuple(case for case in cases if case.kind == "positive")
    records = [case.to_dict() for case in cases]
    manifest = {
        "v": 1, "schema": SCHEMA, "status": "fixtures-planned-reference-not-run",
        "profile_sha256": development_profile()["profile_sha256"], "epoch_sha256": epoch_sha256,
        "epoch_role": "separate lineage metadata only; no catalog imports or replay",
        "authorship": "human/agent-authored deterministic conformance templates; not Hydra search",
        "generation": {"templates": TEMPLATES, "seeds_per_template": SEEDS,
                       "seed_range": [0, SEEDS - 1], "fuel": FUEL,
                       "uniqueness_marker": "explicit reflexive (template,seed) tag conjunct; no assumptions or independent-lineage claim"},
        "case_count": len(cases), "positive_certificate_count": len(positives),
        "distinct_positive_formula_count": len({case.statement for case in positives}),
        "positive_family_counts": dict(sorted(Counter(case.family for case in positives).items())),
        "certificate_mutation_count": sum(case.kind == "certificate_mutation" for case in cases),
        "mutation_coverage": dict(sorted(Counter(case.mutation for case in cases if case.kind == "certificate_mutation").items())),
        "wire_mutation_count": sum(case.kind == "wire_mutation" for case in cases),
        "wire_native_status": "not run; Lean artifact gate only",
        "expected_lean_counts": dict(sorted(Counter(case.expected_lean for case in cases).items())),
        "positive_proof_constructor_occurrences": constructors, "positive_axiom_occurrences": axioms,
        "authored_template_constructor_occurrences": authored_constructors,
        "artifact_total_bytes": sum(len(case.artifact) for case in cases),
        "limits": {"max_cases": MAX_CASES, "max_case_bytes": MAX_CASE_BYTES, "max_suite_bytes": MAX_SUITE_BYTES},
        "source_bindings": sources, "cases": records,
        "cases_sha256": _sha(_json(records)),
        "claims": {"h0_complete": False, "decision_procedure": False,
                   "negative_theoremhood": False, "autonomous_discoveries": False,
                   "training_or_sealed_evaluation_data": False,
                   "independent_reference_checked": False,
                   "parser_independently_verified": False,
                   "independent_python_reference": False,
                   "intuitionistic_completeness_from_nat_semantics": False},
    }
    manifest["manifest_sha256"] = _sha(_json(manifest))
    return manifest


__all__ = ["ConformanceCase", "ConformanceError", "build_conformance_cases",
           "conformance_manifest", "check_native_cases"]
